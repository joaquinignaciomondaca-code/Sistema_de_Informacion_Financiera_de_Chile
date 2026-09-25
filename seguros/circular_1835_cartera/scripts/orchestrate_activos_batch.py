"""
Orquestador de Ingesta por Lotes (Batch Streaming): Carteras Circular 1835 CMF
================================================================================
Optimizacion de alto rendimiento:
- Descarga en streaming a RAM (io.BytesIO).
- Acumula DataFrames mensuales en memoria y consolida en Parquet por lotes.
- Reduce el costo de I/O y drop_duplicates de N lecturas a 1 consolidacion por lote.
- Actualiza control_descargas_activos.csv de forma transaccional.
"""

import os
import sys
import io
import time
import argparse
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUTS_DIR = os.path.join(MODULE_DIR, "outputs")
CONTROL_FILE = os.path.join(MODULE_DIR, "control_descargas_activos.csv")

sys.path.insert(0, SCRIPT_DIR)
from process_cartera_activos import extract_all_assets_from_zip, DEDUP_KEYS

BASE_URL = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php"
ENTITIES = {
    "generales": "CSGEN",
    "vida": "CSVID"
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})


def load_control():
    if os.path.exists(CONTROL_FILE):
        try:
            return pd.read_csv(CONTROL_FILE, dtype=str)
        except Exception:
            pass
    return pd.DataFrame(columns=[
        "periodo", "sector", "estado", "acciones", "fondos", "extranjeros", "bonos", "bienes_raices", "solvencia", "fecha_proceso"
    ])


def save_control(df):
    df.sort_values(by=["periodo", "sector"]).to_csv(CONTROL_FILE, index=False, encoding="utf-8")


def is_processed(ctrl_df, periodo, sector, forzar=False):
    if forzar or ctrl_df.empty:
        return False
    match = ctrl_df[(ctrl_df["periodo"] == periodo) & (ctrl_df["sector"] == sector)]
    if not match.empty:
        return match.iloc[0]["estado"] == "COMPLETO"
    return False


def record_status(periodo, sector, estado, counts=None):
    counts = counts or {"acciones": 0, "fondos": 0, "extranjeros": 0, "bonos": 0, "bienes_raices": 0, "solvencia": 0}
    ctrl_df = load_control()
    ctrl_df = ctrl_df[~((ctrl_df["periodo"] == periodo) & (ctrl_df["sector"] == sector))]
    nueva_fila = {
        "periodo": periodo,
        "sector": sector,
        "estado": estado,
        "acciones": counts.get("acciones", 0),
        "fondos": counts.get("fondos", 0),
        "extranjeros": counts.get("extranjeros", 0),
        "bonos": counts.get("bonos", 0),
        "bienes_raices": counts.get("bienes_raices", 0),
        "solvencia": counts.get("solvencia", 0),
        "fecha_proceso": datetime.now().isoformat()
    }
    ctrl_df = pd.concat([ctrl_df, pd.DataFrame([nueva_fila])], ignore_index=True)
    save_control(ctrl_df)


def get_periods_range(start_str, end_str):
    y_start, m_start = int(start_str[:4]), int(start_str[5:7])
    y_end, m_end = int(end_str[:4]), int(end_str[5:7])
    periods = []
    y, m = y_start, m_start
    while (y, m) <= (y_end, m_end):
        periods.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return periods


def check_availability(entity_code, yyyymm):
    url = f"{BASE_URL}?tipoentidad={entity_code}&fnAjax=archi&peri={yyyymm}"
    try:
        resp = SESSION.get(url, timeout=(8, 15))
        return resp.text.strip() == "1"
    except Exception as e:
        print(f"  [WARN] Error verificando disponibilidad para {entity_code} {yyyymm}: {e}")
        return False


def download_and_extract_month(sector, periodo):
    entity_code = ENTITIES[sector]
    yyyymm = periodo.replace("-", "")
    download_url = f"{BASE_URL}?tipoentidad={entity_code}&fnAjax=descarga&peri={yyyymm}"
    filename_hint = f"{yyyymm}_{sector}.zip"

    resp = SESSION.get(download_url, timeout=(12, 60))
    if resp.status_code != 200:
        raise ValueError(f"HTTP {resp.status_code} al descargar {download_url}")

    data = resp.content
    if not data.startswith(b"PK"):
        raise ValueError(f"Descarga incompleta o no es un ZIP valido ({len(data)} bytes).")

    size_mb = len(data) / (1024 * 1024)
    buffer = io.BytesIO(data)
    assets, detected_sector = extract_all_assets_from_zip(buffer, filename_hint=filename_hint, sector_override=sector)

    month_counts = {}
    for asset_name, rows in assets.items():
        month_counts[asset_name] = len(rows)

    return assets, month_counts, size_mb


def consolidate_batch(batch_accumulator, sector):
    target_dir = os.path.join(OUTPUTS_DIR, sector.lower())
    os.makedirs(target_dir, exist_ok=True)

    print(f"\n[CONSOLIDANDO EN PARQUET] Guardando lote acumulado para sector {sector.upper()}...")
    t0 = time.time()

    for asset_name, list_of_dfs in batch_accumulator.items():
        if not list_of_dfs:
            continue

        parquet_path = os.path.join(target_dir, f"cartera_{asset_name}.parquet")
        df_new_batch = pd.concat(list_of_dfs, ignore_index=True)

        if os.path.exists(parquet_path):
            try:
                df_old = pd.read_parquet(parquet_path)
                old_rows = len(df_old)
                df_combined = pd.concat([df_old, df_new_batch], ignore_index=True)
                subset = [c for c in DEDUP_KEYS.get(asset_name, []) if c in df_combined.columns]
                if subset:
                    df_combined = df_combined.drop_duplicates(subset=subset, keep="last")
            except Exception as e:
                print(f"  [ERROR READ] {asset_name}: {e}")
                df_combined = df_new_batch
                old_rows = 0
        else:
            df_combined = df_new_batch
            old_rows = 0

        df_combined.to_parquet(parquet_path, index=False, engine="pyarrow", compression="snappy")
        print(f"  - {asset_name:<15}: {old_rows:>9,} -> {len(df_combined):>9,} filas (+{len(df_combined)-old_rows:,})")

    t_elapsed = time.time() - t0
    print(f"[CONSOLIDADO FINALIZADO] Parquet actualizado exitosamente en {t_elapsed:.1f}s\n")


def run_batch_orchestrator(start_period="2024-09", end_period="2026-08", sector_choice="ambos", forzar=False):
    sectors = ["generales", "vida"] if sector_choice == "ambos" else [sector_choice]
    periods = get_periods_range(start_period, end_period)

    print("=" * 85)
    print("ORQUESTADOR BATCH DE CARTERAS CMF (CIRCULAR 1835)")
    print(f"Rango a procesar: {start_period} a {end_period} ({len(periods)} meses)")
    print(f"Sectores: {', '.join(s.upper() for s in sectors)}")
    print("Modo: Descarga RAM + Consolidacion Inteligente por Lote")
    print("=" * 85)

    for sector in sectors:
        entity_code = ENTITIES[sector]
        print(f"\n>>> INICIANDO PROCESAMIENTO SECTOR: {sector.upper()} <<<")

        ctrl_df = load_control()
        pending_periods = [p for p in periods if not is_processed(ctrl_df, p, sector, forzar=forzar)]

        if not pending_periods:
            print(f"Sector {sector.upper()} ya esta 100% al dia para el rango {start_period} a {end_period}.")
            continue

        print(f"Periodos pendientes para {sector.upper()}: {len(pending_periods)} meses")

        batch_accumulator = {
            "acciones": [],
            "fondos": [],
            "extranjeros": [],
            "bonos": [],
            "bienes_raices": [],
            "solvencia": []
        }

        months_in_batch = 0

        for idx, periodo in enumerate(pending_periods, start=1):
            yyyymm = periodo.replace("-", "")
            print(f"[{idx}/{len(pending_periods)}] {sector.upper()} {periodo}...", end=" ", flush=True)

            disponible = check_availability(entity_code, yyyymm)
            if not disponible:
                print("NO PUBLICADO EN CMF")
                record_status(periodo, sector, "NO_PUBLICADO")
                continue

            exito = False
            for intento in range(1, 4):
                try:
                    t_start = time.time()
                    assets, month_counts, size_mb = download_and_extract_month(sector, periodo)
                    t_sec = time.time() - t_start

                    for asset_name, rows in assets.items():
                        if rows:
                            batch_accumulator[asset_name].append(pd.DataFrame(rows))

                    record_status(periodo, sector, "COMPLETO", month_counts)
                    print(f"OK ({size_mb:.1f} MB en {t_sec:.1f}s) -> Bonos: {month_counts.get('bonos', 0):,}, Solv: {month_counts.get('solvencia', 0):,}")
                    exito = True
                    months_in_batch += 1
                    break
                except Exception as e:
                    print(f"[REINTENTO {intento}] {e}...", end=" ", flush=True)
                    time.sleep(2)

            if not exito:
                print("ERROR DE DESCARGA")
                record_status(periodo, sector, "ERROR")

            # Consolidar cada 12 meses o al final para asegurar persistencia
            if months_in_batch >= 12:
                consolidate_batch(batch_accumulator, sector)
                batch_accumulator = {k: [] for k in batch_accumulator}
                months_in_batch = 0

        # Consolidacion final del sector si quedaron datos en buffer
        if months_in_batch > 0:
            consolidate_batch(batch_accumulator, sector)

    print("\n" + "=" * 85)
    print("PROCESO BATCH CONCLUIDO CON EXITO.")
    print("=" * 85)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador Batch de Carteras CMF")
    parser.add_argument("--desde", default="2024-09", help="Periodo inicial YYYY-MM")
    parser.add_argument("--hasta", default="2026-08", help="Periodo final YYYY-MM")
    parser.add_argument("--sector", choices=["ambos", "generales", "vida"], default="ambos")
    parser.add_argument("--forzar", action="store_true", help="Forzar re-descarga")
    args = parser.parse_args()

    run_batch_orchestrator(start_period=args.desde, end_period=args.hasta, sector_choice=args.sector, forzar=args.forzar)

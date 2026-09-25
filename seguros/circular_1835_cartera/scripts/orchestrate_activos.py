"""
Orquestador Histórico de Ingesta y Streaming: Todas las Carteras de Inversión (Circular 1835 CMF)
================================================================================================
Módulo: seguros / circular_1835_cartera / scripts / orchestrate_activos.py

Descarga en streaming directo a RAM (io.BytesIO) y consolida en Parquet y CSV:
  - Acciones Locales (A)
  - Fondos Nacionales (F)
  - Activos Extranjeros (X)
  - Bonos y Renta Fija (I)
  - Bienes Raíces (B)
  - Carátula de Balance y Solvencia (C)

Características:
  - Zero Disk Footprint: 0 bytes temporales en disco durante la ejecución.
  - Registro de Checkpoints persistente en control_descargas_activos.csv.
  - Reanudación inteligente: no re-descarga períodos completados salvo flag --forzar.
  - Verificación previa de disponibilidad contra el servidor CMF.
"""

import os
import sys
import io
import time
import argparse
import urllib.request
from datetime import datetime
from pathlib import Path
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUTS_DIR = os.path.join(MODULE_DIR, "outputs")
CONTROL_FILE = os.path.join(MODULE_DIR, "control_descargas_activos.csv")

sys.path.insert(0, SCRIPT_DIR)
from process_cartera_activos import extract_all_assets_from_zip, consolidate_assets

BASE_URL = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php"
ENTITIES = {
    "generales": "CSGEN",
    "vida": "CSVID"
}


# =============================================================================
# GESTIÓN DE CHECKPOINTS
# =============================================================================
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


# =============================================================================
# RANGO DE PERÍODOS
# =============================================================================
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


# =============================================================================
# STREAMING Y CONEXIÓN CMF
# =============================================================================
import requests

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})


def check_availability(entity_code, yyyymm):
    url = f"{BASE_URL}?tipoentidad={entity_code}&fnAjax=archi&peri={yyyymm}"
    try:
        resp = SESSION.get(url, timeout=(8, 15))
        return resp.text.strip() == "1"
    except Exception as e:
        print(f"  [WARN] Error verificando disponibilidad para {entity_code} {yyyymm}: {e}")
        return False


def stream_and_process_month(sector, periodo):
    entity_code = ENTITIES[sector]
    yyyymm = periodo.replace("-", "")
    download_url = f"{BASE_URL}?tipoentidad={entity_code}&fnAjax=descarga&peri={yyyymm}"
    filename_hint = f"{yyyymm}_{sector}.zip"

    resp = SESSION.get(download_url, timeout=(10, 45))
    if resp.status_code != 200:
        raise ValueError(f"HTTP {resp.status_code} al descargar {download_url}")

    data = resp.content
    if not data.startswith(b"PK"):
        raise ValueError(f"Descarga incompleta o no es un ZIP válido ({len(data)} bytes).")

    size_mb = len(data) / (1024 * 1024)
    print(f"  -> Descargado en RAM: {size_mb:.2f} MB. Extrayendo todas las clases de activos...")

    buffer = io.BytesIO(data)
    assets, detected_sector = extract_all_assets_from_zip(buffer, filename_hint=filename_hint, sector_override=sector)
    counts = consolidate_assets(assets, sector=sector)
    return counts


# =============================================================================
# EJECUTOR PRINCIPAL
# =============================================================================
def run_orchestrator(start_period="2024-01", end_period="2024-06", sector_choice="ambos", forzar=False):
    sectors = ["generales", "vida"] if sector_choice == "ambos" else [sector_choice]
    periods = get_periods_range(start_period, end_period)
    total_tasks = len(periods) * len(sectors)

    print("=" * 85)
    print("ORQUESTADOR HISTÓRICO INTEGRAL: TODAS LAS CARTERAS CIRCULAR 1835 CMF")
    print(f"Rango: {start_period} a {end_period} ({len(periods)} meses)")
    print(f"Sectores: {', '.join(s.upper() for s in sectors)}")
    print(f"Total tareas: {total_tasks}")
    print(f"Modo: Streaming 100% In-Memory (Zero Disk Footprint)")
    print(f"Control de estado: {CONTROL_FILE}")
    print("=" * 85)

    procesados_ok = 0
    omitidos = 0
    no_publicados = 0
    errores = 0

    for periodo in periods:
        yyyymm = periodo.replace("-", "")

        for sector in sectors:
            ctrl_df = load_control()
            if is_processed(ctrl_df, periodo, sector, forzar=forzar):
                print(f"[SKIP] {sector.upper():<9} {periodo} -> Ya procesado previamente.")
                omitidos += 1
                continue

            entity_code = ENTITIES[sector]
            print(f"\n[EVALUANDO] {sector.upper()} {periodo}...")

            disponible = check_availability(entity_code, yyyymm)
            if not disponible:
                print(f"  [CMF] Período aún no disponible. Registrando NO_PUBLICADO.")
                record_status(periodo, sector, "NO_PUBLICADO")
                no_publicados += 1
                continue

            exito = False
            intentos = 3
            for intento in range(1, intentos + 1):
                try:
                    t0 = time.time()
                    counts = stream_and_process_month(sector, periodo)
                    t_elapsed = time.time() - t0
                    record_status(periodo, sector, "COMPLETO", counts)
                    print(f"  [OK {t_elapsed:.1f}s] {sector.upper()} {periodo} -> Acc: {counts.get('acciones',0):,}, Fnd: {counts.get('fondos',0):,}, Ext: {counts.get('extranjeros',0):,}, Bon: {counts.get('bonos',0):,}, BR: {counts.get('bienes_raices',0):,}")
                    exito = True
                    procesados_ok += 1
                    break
                except Exception as e:
                    print(f"  [REINTENTO {intento}/{intentos}] Falló {sector} {periodo}: {e}")
                    time.sleep(2)

            if not exito:
                print(f"  [ERROR] No se pudo procesar {sector} {periodo} tras {intentos} intentos.")
                record_status(periodo, sector, "ERROR")
                errores += 1

    print("\n" + "=" * 85)
    print("RESUMEN DE EJECUCIÓN DEL ORQUESTADOR INTEGRAL")
    print("=" * 85)
    print(f"Procesados exitosamente: {procesados_ok}")
    print(f"Omitidos (ya al día):    {omitidos}")
    print(f"No publicados en CMF:    {no_publicados}")
    print(f"Errores:                 {errores}")
    print("=" * 85)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador Integral de Carteras CMF (Streaming)")
    parser.add_argument("--desde", default="2024-01", help="Período inicial YYYY-MM (default: 2024-01)")
    parser.add_argument("--hasta", default="2024-06", help="Período final YYYY-MM (default: 2024-06)")
    parser.add_argument("--sector", choices=["ambos", "generales", "vida"], default="ambos", help="Sector a procesar")
    parser.add_argument("--forzar", action="store_true", help="Forzar re-descarga")
    args = parser.parse_args()

    run_orchestrator(start_period=args.desde, end_period=args.hasta, sector_choice=args.sector, forzar=args.forzar)

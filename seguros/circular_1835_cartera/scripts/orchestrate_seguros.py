import os
import sys
import io
import time
import argparse
import urllib.request
from datetime import datetime
from pathlib import Path
import pandas as pd

# Rutas del módulo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUTS_DIR = os.path.join(MODULE_DIR, "outputs")
CONTROL_FILE = os.path.join(MODULE_DIR, "control_descargas.csv")

# Asegurar importación del parser B.7
sys.path.insert(0, SCRIPT_DIR)
from process_b7_derivatives import process_single_zip

BASE_URL = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php"
ENTITIES = {
    "generales": "CSGEN",
    "vida": "CSVID"
}

# =============================================================================
# GESTIÓN DEL REGISTRO DE CONTROL (CHECKPOINTS)
# =============================================================================
def load_control():
    if os.path.exists(CONTROL_FILE):
        try:
            return pd.read_csv(CONTROL_FILE, dtype=str)
        except Exception:
            pass
    return pd.DataFrame(columns=["periodo", "sector", "estado", "forwards", "swaps", "repos", "opciones", "fecha_proceso"])

def save_control(df):
    df.sort_values(by=["periodo", "sector"]).to_csv(CONTROL_FILE, index=False, encoding="utf-8")

def is_processed(ctrl_df, periodo, sector, forzar=False):
    if forzar or ctrl_df.empty:
        return False
    match = ctrl_df[(ctrl_df["periodo"] == periodo) & (ctrl_df["sector"] == sector)]
    if not match.empty:
        estado = match.iloc[0]["estado"]
        return estado == "COMPLETO"
    return False

def record_status(periodo, sector, estado, counts=None):
    counts = counts or {"forwards": 0, "swaps": 0, "repos": 0, "opciones": 0}
    ctrl_df = load_control()
    ctrl_df = ctrl_df[~((ctrl_df["periodo"] == periodo) & (ctrl_df["sector"] == sector))]
    nueva_fila = {
        "periodo": periodo,
        "sector": sector,
        "estado": estado,
        "forwards": counts.get("forwards", 0),
        "swaps": counts.get("swaps", 0),
        "repos": counts.get("repos", 0),
        "opciones": counts.get("opciones", 0),
        "fecha_proceso": datetime.now().isoformat()
    }
    ctrl_df = pd.concat([ctrl_df, pd.DataFrame([nueva_fila])], ignore_index=True)
    save_control(ctrl_df)

# =============================================================================
# GENERADOR DE PERÍODOS
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
# INGESTA POR STREAMING DIRECTO EN MEMORIA (ZERO DISK BLOAT)
# =============================================================================
def check_availability(entity_code, yyyymm):
    url = f"{BASE_URL}?tipoentidad={entity_code}&fnAjax=archi&peri={yyyymm}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8", errors="ignore").strip()
            return data == "1"
    except Exception as e:
        print(f"  [WARN] Error verificando disponibilidad para {entity_code} {yyyymm}: {e}")
        return False

def stream_and_process_month(sector, periodo):
    entity_code = ENTITIES[sector]
    yyyymm = periodo.replace("-", "")
    download_url = f"{BASE_URL}?tipoentidad={entity_code}&fnAjax=descarga&peri={yyyymm}"
    filename_hint = f"{yyyymm}_{sector}.zip"

    req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read()

        if not data.startswith(b"PK"):
            raise ValueError(f"Descarga incompleta o no es un archivo ZIP válido ({len(data)} bytes).")

        size_mb = len(data) / (1024 * 1024)
        print(f"  -> Descargado en RAM: {size_mb:.2f} MB (0 bytes en disco). Parseando B.7...")

        buffer = io.BytesIO(data)
        counts = process_single_zip(buffer, filename_hint=filename_hint, delete_zip=False)
        return counts

def run_orchestrator(start_period="2023-01", end_period="2026-08", sector_choice="ambos", forzar=False):
    sectors = ["generales", "vida"] if sector_choice == "ambos" else [sector_choice]
    periods = get_periods_range(start_period, end_period)
    total_tasks = len(periods) * len(sectors)

    print("=" * 85)
    print("ORQUESTADOR HISTÓRICO - CARTERAS B.7 CIRCULAR 1835 CMF (STREAMING DIRECTO)")
    print(f"Rango: {start_period} a {end_period} ({len(periods)} meses)")
    print(f"Sectores: {', '.join(s.upper() for s in sectors)}")
    print(f"Total combinaciones mes/sector: {total_tasks}")
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

            # 1. Comprobar si está publicado en el servidor CMF
            disponible = check_availability(entity_code, yyyymm)
            if not disponible:
                print(f"  [CMF] Período aún no disponible o no publicado. Registrando NO_PUBLICADO.")
                record_status(periodo, sector, "NO_PUBLICADO")
                no_publicados += 1
                continue

            # 2. Descargar y procesar en streaming (RAM -> Parquet)
            exito = False
            intentos = 3
            for intento in range(1, intentos + 1):
                try:
                    t0 = time.time()
                    counts = stream_and_process_month(sector, periodo)
                    t_elapsed = time.time() - t0
                    record_status(periodo, sector, "COMPLETO", counts)
                    print(f"  [OK {t_elapsed:.1f}s] {sector.upper()} {periodo} -> Fwd: {counts['forwards']}, Swp: {counts['swaps']}, Rep: {counts['repos']}, Opc: {counts['opciones']}")
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
    print("RESUMEN DE EJECUCIÓN DEL ORQUESTADOR")
    print("=" * 85)
    print(f"Procesados exitosamente: {procesados_ok}")
    print(f"Omitidos (ya al día):    {omitidos}")
    print(f"No publicados en CMF:    {no_publicados}")
    print(f"Errores:                 {errores}")
    print("=" * 85)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador Histórico de Seguros CMF (Streaming)")
    parser.add_argument("--desde", default="2023-01", help="Período inicial YYYY-MM (default: 2023-01)")
    parser.add_argument("--hasta", default="2026-08", help="Período final YYYY-MM (default: 2026-08)")
    parser.add_argument("--sector", choices=["ambos", "generales", "vida"], default="ambos", help="Sector a procesar")
    parser.add_argument("--forzar", action="store_true", help="Re-descargar incluso si ya figura como COMPLETO")
    args = parser.parse_args()

    run_orchestrator(start_period=args.desde, end_period=args.hasta, sector_choice=args.sector, forzar=args.forzar)

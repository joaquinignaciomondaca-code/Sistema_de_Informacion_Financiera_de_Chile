"""
Pipeline Incremental de Descarga y Normalización - Derivados FFMM (Circular 1333 CMF)
=====================================================================================
- Módulo: ffmm / circular_1333_cartera
- Descarga inteligente: omite archivos consolidados históricos (> 2 meses con tamaño válido).
- Revisa automáticamente la ventana reciente móvil (últimos N meses).
- Detecta meses no publicados ("Sin información") sin fallar.
- Normaliza y actualiza los archivos maestros (Parquet y CSV con UTF-8 BOM).
- Diseñado para correr periódicamente (días 1, 8, 18 y fin de mes).
"""

import os
import re
import sys
import glob
import logging
from datetime import datetime, date
import requests
import urllib3
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Rutas autocontenidas del módulo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(MODULE_DIR, "inputs")
NORM_DIR = os.path.join(MODULE_DIR, "outputs")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(NORM_DIR, exist_ok=True)

FUTU_PARQUET = os.path.join(NORM_DIR, "ffmm_futu_normalizado.parquet")
FUTU_CSV = os.path.join(NORM_DIR, "ffmm_futu_normalizado.csv")
OPCI_PARQUET = os.path.join(NORM_DIR, "ffmm_opci_normalizado.parquet")
OPCI_CSV = os.path.join(NORM_DIR, "ffmm_opci_normalizado.csv")

CMF_URL = "https://www.cmfchile.cl/institucional/estadisticas/ffm_download.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php"
}


# =============================================================================
# 1. NORMALIZADORES ESTRICTOS (Circ. 1333)
# =============================================================================
def normalize_futu_file(filepath):
    fname = os.path.basename(filepath)
    m = re.search(r'FUTU_(\d{4})(\d{2})\.txt', fname)
    if not m:
        return pd.DataFrame()
    periodo = f"{m.group(1)}-{m.group(2)}"

    try:
        df = pd.read_csv(filepath, sep=";", encoding="utf-8", dtype=str)
    except Exception:
        df = pd.read_csv(filepath, sep=";", encoding="latin-1", dtype=str, on_bad_lines="skip")

    if df.empty or 'Run Fondo' not in df.columns:
        return pd.DataFrame()

    out = pd.DataFrame(index=df.index)
    out["periodo"] = periodo
    out["run_fondo"] = df["Run Fondo"].str.strip()
    out["nombre_fondo"] = df["Nombre Fondo"].str.strip()
    out["moneda_subyacente"] = df["FFM_6040111"].str.strip()
    out["tipo_instrumento"] = df["FFM_6040112"].str.strip()
    out["nemotecnico"] = df["FFM_6040113"].str.strip()
    out["fecha_vencimiento"] = df["FFM_6040114"].str.strip()
    out["mercado"] = df["FFM_6040115"].str.strip()
    out["pais"] = df["FFM_6040116"].str.strip()
    out["posicion"] = df["FFM_6040200"].str.strip().str.upper()

    out["nocional"] = pd.to_numeric(df["FFM_6040300"].str.replace(",", "."), errors="coerce").fillna(0)
    out["precio_pactado"] = pd.to_numeric(df["FFM_6040400"].str.replace(",", "."), errors="coerce").fillna(0)
    out["monto_contratado_m_clp"] = pd.to_numeric(df["FFM_6040500"].str.replace(",", "."), errors="coerce").fillna(0)
    out["valor_mercado_m_clp"] = pd.to_numeric(df["FFM_6040600"].str.replace(",", "."), errors="coerce").fillna(0)
    out["archivo_fuente"] = fname
    return out


def normalize_opci_file(filepath):
    fname = os.path.basename(filepath)
    m = re.search(r'OPCI_(\d{4})(\d{2})\.txt', fname)
    if not m:
        return pd.DataFrame()
    periodo = f"{m.group(1)}-{m.group(2)}"

    try:
        df = pd.read_csv(filepath, sep=";", encoding="utf-8", dtype=str)
    except Exception:
        df = pd.read_csv(filepath, sep=";", encoding="latin-1", dtype=str, on_bad_lines="skip")

    if df.empty or 'Run Fondo' not in df.columns:
        return pd.DataFrame()

    out = pd.DataFrame(index=df.index)
    out["periodo"] = periodo
    out["run_fondo"] = df["Run Fondo"].str.strip()
    out["nombre_fondo"] = df["Nombre Fondo"].str.strip()
    out["moneda_subyacente"] = df["FFM_6030111"].str.strip()
    out["nemotecnico"] = df["FFM_6030112"].str.strip()
    out["tipo_opcion"] = df["FFM_6030113"].str.strip().str.upper()
    out["fecha_vencimiento"] = df["FFM_6030114"].str.strip()
    out["mercado"] = df["FFM_6030115"].str.strip()
    out["pais"] = df["FFM_6030116"].str.strip()
    out["posicion"] = df["FFM_6030200"].str.strip().str.upper()

    out["strike"] = pd.to_numeric(df["FFM_6030300"].str.replace(",", "."), errors="coerce").fillna(0)
    out["numero_contratos"] = pd.to_numeric(df["FFM_6030400"].str.replace(",", "."), errors="coerce").fillna(0)
    out["prima_m_clp"] = pd.to_numeric(df["FFM_6030500"].str.replace(",", "."), errors="coerce").fillna(0)

    val_col = "FFM_6030900" if "FFM_6030900" in df.columns else "FFM_6030800"
    out["valor_mercado_m_clp"] = pd.to_numeric(df[val_col].str.replace(",", "."), errors="coerce").fillna(0)
    out["archivo_fuente"] = fname
    return out


# =============================================================================
# 2. GESTOR DE PERIODOS A REVISAR
# =============================================================================
def get_periods_to_check(months_back=3, full_scan=False):
    """
    Genera la lista de periodos (año, mes) a inspeccionar.
    Por defecto revisa la ventana móvil de los últimos `months_back` meses (~2 seg).
    Si full_scan=True, busca meses faltantes en toda la serie histórica desde 2001-01.
    """
    now = datetime.now()
    periods_set = set()

    y, m = now.year, now.month
    for _ in range(months_back + 1):
        periods_set.add((str(y), f"{m:02d}"))
        m -= 1
        if m == 0:
            m = 12
            y -= 1

    if full_scan:
        cur_y, cur_m = 2001, 1
        end_y, end_m = now.year, now.month
        while (cur_y < end_y) or (cur_y == end_y and cur_m <= end_m):
            sy = str(cur_y)
            sm = f"{cur_m:02d}"
            f_futu = os.path.join(RAW_DIR, f"FUTU_{sy}{sm}.txt")
            f_opci = os.path.join(RAW_DIR, f"OPCI_{sy}{sm}.txt")
            if not (os.path.exists(f_futu) and os.path.exists(f_opci)):
                periods_set.add((sy, sm))
            cur_m += 1
            if cur_m > 12:
                cur_m = 1
                cur_y += 1

    return sorted(list(periods_set))


# =============================================================================
# 3. DESCARGA INCREMENTAL INTELIGENTE
# =============================================================================
def download_file_if_needed(year, month, cartera):
    fname = f"{cartera}_{year}{month}.txt"
    fpath = os.path.join(RAW_DIR, fname)
    
    now = datetime.now()
    diff_months = (now.year - int(year)) * 12 + (now.month - int(month))

    # Histórico cerrado: si existe, tiene tamaño válido y es de más de 2 meses atrás, omitir
    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000 and diff_months > 2:
        return False

    data = {"aa": year, "mm": month, "cartera": cartera, "btnConsulta": "GENERAR ARCHIVO"}
    try:
        r = requests.post(CMF_URL, data=data, headers=HEADERS, verify=False, timeout=30)
        content = r.content

        if b"Sin informaci" in content or len(content) < 500:
            return False

        if os.path.exists(fpath):
            existing_size = os.path.getsize(fpath)
            if existing_size == len(content):
                return False
            else:
                print(f"[ACTUALIZACIÓN] {fname}: tamaño cambió de {existing_size:,} a {len(content):,} bytes.")
        else:
            print(f"[NUEVO] Descargado {fname} ({len(content):,} bytes).")

        with open(fpath, "wb") as f:
            f.write(content)
        return True

    except Exception as e:
        print(f"[ERROR] Fallo al consultar {fname}: {e}")
        return False


# =============================================================================
# 4. EJECUCIÓN
# =============================================================================
def run_pipeline(months_back=3, full_scan=False):
    print("=" * 75)
    print(f"PIPELINE DERIVADOS FFMM (CIRCULAR 1333 CMF) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    periods_to_check = get_periods_to_check(months_back=months_back, full_scan=full_scan)
    print(f"Periodos en revisión ({len(periods_to_check)}): {periods_to_check}")

    files_modified = False
    for y, m in periods_to_check:
        for cartera in ["FUTU", "OPCI"]:
            updated = download_file_if_needed(y, m, cartera)
            if updated:
                files_modified = True

    if not files_modified and os.path.exists(FUTU_PARQUET) and os.path.exists(OPCI_PARQUET):
        print("\n-> Todos los datos están al día. No se requirió re-procesar.")
        return

    print("\n-> Actualizando bases normalizadas Parquet y CSV...")
    futu_files = sorted(glob.glob(os.path.join(RAW_DIR, "FUTU_*.txt")))
    futu_dfs = [normalize_futu_file(fp) for fp in futu_files]
    df_futu = pd.concat([d for d in futu_dfs if not d.empty], ignore_index=True)
    df_futu.to_parquet(FUTU_PARQUET, index=False, engine="pyarrow")
    try:
        df_futu.to_csv(FUTU_CSV, index=False, encoding="utf-8-sig")
    except PermissionError:
        print(f"[AVISO] No se pudo sobrescribir {FUTU_CSV} (archivo abierto en Excel).")

    opci_files = sorted(glob.glob(os.path.join(RAW_DIR, "OPCI_*.txt")))
    opci_dfs = [normalize_opci_file(fp) for fp in opci_files]
    df_opci = pd.concat([d for d in opci_dfs if not d.empty], ignore_index=True)
    df_opci.to_parquet(OPCI_PARQUET, index=False, engine="pyarrow")
    try:
        df_opci.to_csv(OPCI_CSV, index=False, encoding="utf-8-sig")
    except PermissionError:
        print(f"[AVISO] No se pudo sobrescribir {OPCI_CSV} (archivo abierto en Excel).")

    print(f"FUTU consolidado: {len(df_futu):,} registros ({df_futu['periodo'].min()} a {df_futu['periodo'].max()})")
    print(f"OPCI consolidado: {len(df_opci):,} registros ({df_opci['periodo'].min()} a {df_opci['periodo'].max()})")
    print("Pipeline completado exitosamente.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline incremental de derivados FFMM (Circular 1333)")
    parser.add_argument("--months-back", type=int, default=3, help="Meses hacia atrás a revisar (default: 3)")
    parser.add_argument("--full-scan", action="store_true", help="Escanear toda la historia desde 2001")
    args = parser.parse_args()

    run_pipeline(months_back=args.months_back, full_scan=args.full_scan)

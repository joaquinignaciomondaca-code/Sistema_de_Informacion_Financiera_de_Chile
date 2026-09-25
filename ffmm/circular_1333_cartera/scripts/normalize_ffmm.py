"""
Normalizador Estricto de Derivados (Circular 1333 CMF - Fondos Mutuos)
=====================================================================
- Procesa todos los archivos en inputs/ (FUTU_*.txt y OPCI_*.txt).
- Genera archivos maestros en outputs/: Parquet y CSV (UTF-8 con BOM).
- Mantiene estrictamente las columnas oficiales de la normativa CMF.
"""

import os
import glob
import re
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(MODULE_DIR, "inputs")
NORM_DIR = os.path.join(MODULE_DIR, "outputs")
os.makedirs(NORM_DIR, exist_ok=True)


def normalize_futu_strict(filepath):
    filename = os.path.basename(filepath)
    m = re.search(r'FUTU_(\d{4})(\d{2})\.txt', filename)
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
    out["archivo_fuente"] = filename
    return out


def normalize_opci_strict(filepath):
    filename = os.path.basename(filepath)
    m = re.search(r'OPCI_(\d{4})(\d{2})\.txt', filename)
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
    out["archivo_fuente"] = filename
    return out


def main():
    print("Normalizando derivados FUTU...")
    futu_files = sorted(glob.glob(os.path.join(RAW_DIR, "FUTU_*.txt")))
    futu_dfs = [normalize_futu_strict(p) for p in futu_files]
    df_futu = pd.concat([d for d in futu_dfs if not d.empty], ignore_index=True)
    df_futu.to_parquet(os.path.join(NORM_DIR, "ffmm_futu_normalizado.parquet"), index=False, engine="pyarrow")
    df_futu.to_csv(os.path.join(NORM_DIR, "ffmm_futu_normalizado.csv"), index=False, encoding="utf-8-sig")
    print(f"FUTU OK: {len(df_futu):,} filas ({df_futu['periodo'].min()} a {df_futu['periodo'].max()})")

    print("Normalizando derivados OPCI...")
    opci_files = sorted(glob.glob(os.path.join(RAW_DIR, "OPCI_*.txt")))
    opci_dfs = [normalize_opci_strict(p) for p in opci_files]
    df_opci = pd.concat([d for d in opci_dfs if not d.empty], ignore_index=True)
    df_opci.to_parquet(os.path.join(NORM_DIR, "ffmm_opci_normalizado.parquet"), index=False, engine="pyarrow")
    df_opci.to_csv(os.path.join(NORM_DIR, "ffmm_opci_normalizado.csv"), index=False, encoding="utf-8-sig")
    print(f"OPCI OK: {len(df_opci):,} filas ({df_opci['periodo'].min()} a {df_opci['periodo'].max()})")


if __name__ == "__main__":
    main()

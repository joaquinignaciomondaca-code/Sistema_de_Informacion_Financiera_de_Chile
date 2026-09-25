"""
Exportador de Operaciones Repo / Pactos (VRC y CRV) para Fondos de Inversion.
Convierte la base historica oficial CMF a formato Parquet de alto rendimiento.
"""

import os
import re
import unicodedata
from pathlib import Path
import pandas as pd

def clean_col(col):
    c = unicodedata.normalize("NFKD", str(col)).encode("ASCII", "ignore").decode("utf-8").lower()
    c = re.sub(r"[^a-z0-9]+", "_", c).strip("_")
    return c

def main():
    excel_path = Path(r"C:\Users\joaqu\Desktop\Respaldo_BCCH\Fondos_Inversion\01_estados_financieros\outputs\5_Repos_CMF_Completo.xlsx")
    if not excel_path.exists():
        print(f"ERROR: Archivo no encontrado en {excel_path}")
        return

    out_dir = Path("fi/repos/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_parquet = out_dir / "fi_repos_vrc_crv.parquet"

    print(f"Cargando {excel_path.name}...")
    df = pd.read_excel(excel_path, sheet_name="Repos_CMF")
    df.columns = [clean_col(c) for c in df.columns]

    col_rename = {
        "run": "run_fondo",
        "ano": "anio",
        "mes": "mes",
        "codigo_de_operacion": "codigo_operacion",
        "fecha_de_inicio": "fecha_inicio",
        "fecha_de_termino": "fecha_termino",
        "nombre_contraparte": "nombre_contraparte",
        "subcategoria": "subcategoria_contraparte",
        "rut_contraparte": "rut_contraparte",
        "valor_inicial": "valor_inicial",
        "tasa": "tasa_pct",
        "valor_final": "valor_final",
        "valorizacion_al_cierre": "valorizacion_cierre",
        "codigo_isin_o_cusip": "isin",
        "nemotecnico_del_instrumento": "nemotecnico",
        "nombre_del_emisor": "emisor_garantia",
        "tipo_de_instrumento": "tipo_instrumento_garantia",
        "clasificacion_por_instrumento": "clasificacion_garantia",
        "valor_de_mercado": "valor_mercado_garantia",
    }

    df = df.rename(columns=col_rename)
    df["periodo"] = df["anio"].astype(str) + df["mes"].astype(str).str.zfill(2)
    df["tipo_operacion_desc"] = df["codigo_operacion"].map({
        "CRV": "Compra con Pacto de Retroventa (Activo)",
        "VRC": "Venta con Pacto de Retrocompra (Pasivo)"
    }).fillna(df["codigo_operacion"])

    # Normalización integral canónica
    try:
        from normalize_repos_fi import normalize_repos_dataframe, export_clean_outputs
    except ImportError:
        from fi.repos.scripts.normalize_repos_fi import normalize_repos_dataframe, export_clean_outputs

    df_clean = normalize_repos_dataframe(df)
    export_clean_outputs(df_clean)

    print(f"Exportación y normalización exitosa.")
    print(f"Total registros limpios: {len(df_clean):,}")
    print(f"Rango temporal ISO: {df_clean['periodo'].min()} a {df_clean['periodo'].max()}")
    print(f"Fondos unicos: {df_clean['run_fondo'].nunique()}")
    print(f"Contrapartes reconciliadas: {df_clean['rut_contraparte'].nunique()}")

if __name__ == "__main__":
    main()

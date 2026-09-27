"""
Extractor LEGACY deshabilitado: no usar como pipeline de publicación.
Lee un Excel ausente del PC, mezcla bancos y agregados, copia RUT actuales
al pasado y confunde suma de saldos con volumen transado. Ver auditoría REPO.
La preparación no publicadora está en prepare_repo_corrections.py.
"""

import os
import json

def extract_bancos_repos_series():
    raise RuntimeError(
        "Extractor legacy bloqueado: identidad histórica y 'total_transado' "
        "no verificados. Usar prepare_repo_corrections.py sólo para revisión; "
        "ningún script está autorizado todavía a publicar REPO."
    )
    import pandas as pd  # sólo para conservar referencia histórica; inalcanzable
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    excel_path = r"C:\Users\joaqu\Desktop\Respaldo_BCCH\Bancos\REPO_BANCO\REPO_BANCOS_CMF\repo_banco.xlsx"
    maestro_path = os.path.join(base_dir, "docs", "outputs", "bancos", "bancos_maestro.parquet")
    out_dir = os.path.join(base_dir, "docs", "outputs", "bancos")
    os.makedirs(out_dir, exist_ok=True)

    print("Cargando maestro de bancos...")
    df_maestro = pd.read_parquet(maestro_path)[["codigo_institucion", "rut", "razon_social", "nombre_fantasia"]]

    print(f"Leyendo archivo Excel de repos: {excel_path}...")
    df_excel = pd.read_excel(excel_path, sheet_name="Detalle por Banco", header=2)
    df_resumen = pd.read_excel(excel_path, sheet_name=0, header=2)

    # Mapa oficial de Tipo de Cambio Cierre mensual CMF / BCCh
    tc_map = dict(zip(df_resumen["Periodo"].astype(str).str.strip(), df_resumen["TC_dolar_CLP"]))

    # Limpieza y formateo
    df_excel["codigo_institucion"] = df_excel["Codigo_Banco"].astype(int).apply(lambda x: f"{x:03d}")
    df_excel["periodo"] = df_excel["Periodo"].astype(str).str.strip()
    df_excel["fecha_corte"] = (pd.to_datetime(df_excel["periodo"] + "-01") + pd.offsets.MonthEnd(1)).dt.strftime("%Y-%m-%d")
    df_excel["id_repo"] = df_excel["codigo_institucion"] + "_" + df_excel["periodo"]

    # Cruzar con maestro
    merged = pd.merge(df_excel, df_maestro, on="codigo_institucion", how="left")

    if merged["rut"].isna().any():
        missing_banks = merged[merged["rut"].isna()]["codigo_institucion"].unique()
        raise ValueError(f"Instituciones no encontradas en bancos_maestro: {missing_banks}")

    # Tipos de cambio y valores monetarios
    merged["tc_usd_cierre"] = merged["periodo"].map(tc_map).round(4)
    if merged["tc_usd_cierre"].isna().any():
        raise ValueError("Hay periodos sin tipo de cambio oficial en el mapa.")

    merged["repo_activo_mm_clp"] = merged["Repo_Activo_MMCLP"].fillna(0.0).round(2)
    merged["repo_pasivo_mm_clp"] = merged["Repo_Pasivo_MMCLP"].fillna(0.0).round(2)
    merged["repo_neto_mm_clp"] = (merged["repo_activo_mm_clp"] - merged["repo_pasivo_mm_clp"]).round(2)

    merged["repo_activo_mm_usd"] = merged["Repo_Activo_MMUSD"].fillna(0.0).round(2)
    merged["repo_pasivo_mm_usd"] = merged["Repo_Pasivo_MMUSD"].fillna(0.0).round(2)
    merged["repo_neto_mm_usd"] = (merged["repo_activo_mm_usd"] - merged["repo_pasivo_mm_usd"]).round(2)
    merged["total_transado_mm_usd"] = (merged["repo_activo_mm_usd"] + merged["repo_pasivo_mm_usd"]).round(2)

    merged["posicion_relativa"] = "Neutro"
    merged.loc[merged["repo_neto_mm_clp"] > 0, "posicion_relativa"] = "Prestamista Neto de Liquidez"
    merged.loc[merged["repo_neto_mm_clp"] < 0, "posicion_relativa"] = "Tomador Neto de Fondeo"

    cols = [
        "id_repo",
        "periodo",
        "fecha_corte",
        "codigo_institucion",
        "rut",
        "razon_social",
        "nombre_fantasia",
        "repo_activo_mm_clp",
        "repo_pasivo_mm_clp",
        "repo_neto_mm_clp",
        "tc_usd_cierre",
        "repo_activo_mm_usd",
        "repo_pasivo_mm_usd",
        "repo_neto_mm_usd",
        "total_transado_mm_usd",
        "posicion_relativa"
    ]

    out_df = merged[cols].sort_values(["periodo", "codigo_institucion"]).reset_index(drop=True)

    parquet_file = os.path.join(out_dir, "bancos_repos_saldos_series.parquet")
    json_file = os.path.join(out_dir, "bancos_repos_saldos_series.json")

    print(f"Exportando Parquet a {parquet_file} ({len(out_df):,} registros)...")
    out_df.to_parquet(parquet_file, index=False)

    print(f"Exportando JSON a {json_file}...")
    out_df.to_json(json_file, orient="records", date_format="iso", indent=2)

    print("Proceso completado exitosamente con 0 residuos temporales.")

if __name__ == "__main__":
    extract_bancos_repos_series()

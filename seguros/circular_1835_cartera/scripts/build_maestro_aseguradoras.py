"""
Generador de Catalogos Maestros de Entidades Aseguradoras (Circular 1835 CMF).
Genera tablas de dimensiones institucionales para Seguros de Vida y Seguros Generales.
"""

import re
import unicodedata
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = ROOT_DIR / "outputs"

def clean_entity_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    # Corregir artefactos tipicos de codificacion CMF
    name = name.replace("#", "Ñ").replace("COMPA IA", "COMPAÑIA").replace("COMPA  IA", "COMPAÑIA")
    name = re.sub(r"\s+", " ", name).strip()
    return name.upper()

def extract_rut_numerico(rut_str: str) -> int:
    digits = re.sub(r"[^\d]", "", rut_str.split("-")[0])
    return int(digits) if digits else 0

def build_catalog(solvencia_parquet: Path, sector_code: str, sector_label: str) -> pd.DataFrame:
    if not solvencia_parquet.exists():
        print(f"Advertencia: No se encontro {solvencia_parquet}")
        return pd.DataFrame()

    df = pd.read_parquet(solvencia_parquet)
    df["nombre_limpio"] = df["nombre_aseguradora"].apply(clean_entity_name)
    df["periodo_clean"] = df["periodo"].astype(str)

    max_period_global = df["periodo_clean"].max()
    threshold_active = "2024-01"

    records = []
    for rut, group in df.groupby("rut_aseguradora"):
        group_sorted = group.sort_values(by="periodo_clean", ascending=False)
        valid_names = group_sorted[group_sorted["nombre_limpio"] != ""]["nombre_limpio"]
        best_name = valid_names.iloc[0] if len(valid_names) > 0 else rut

        min_p = group["periodo_clean"].min()
        max_p = group["periodo_clean"].max()
        n_periods = group["periodo_clean"].nunique()

        latest_rows = group[group["periodo_clean"] == max_p]
        inv_vigente = float(latest_rows["total_inversion_m_clp"].max()) if "total_inversion_m_clp" in latest_rows else 0.0
        pat_vigente = float(latest_rows["patrimonio_comprometido"].max()) if "patrimonio_comprometido" in latest_rows else 0.0

        estado = "Activa" if max_p >= threshold_active else "Inactiva / Historica"

        records.append({
            "rut_aseguradora": str(rut).strip(),
            "rut_numerico": extract_rut_numerico(str(rut)),
            "nombre_aseguradora": best_name,
            "sector": sector_code,
            "clasificacion": sector_label,
            "estado": estado,
            "primer_periodo": min_p,
            "ultimo_periodo": max_p,
            "periodos_reportados": int(n_periods),
            "inversion_ultimo_reporte_m_clp": round(inv_vigente, 2),
            "patrimonio_ultimo_reporte_m_clp": round(pat_vigente, 2)
        })

    df_out = pd.DataFrame(records)
    df_out = df_out.sort_values(by=["estado", "inversion_ultimo_reporte_m_clp"], ascending=[True, False]).reset_index(drop=True)
    return df_out

def main():
    vida_solvencia = OUTPUTS_DIR / "vida" / "cartera_solvencia.parquet"
    gen_solvencia = OUTPUTS_DIR / "generales" / "cartera_solvencia.parquet"

    print("Generando catalogo maestro de entidades para Seguros de Vida...")
    df_vida = build_catalog(vida_solvencia, "VIDA", "Seguros de Vida")
    out_vida = OUTPUTS_DIR / "vida" / "maestro_aseguradoras_vida.parquet"
    df_vida.to_parquet(out_vida, index=False)
    print(f"Exito Vida: {out_vida} ({len(df_vida)} entidades registradas)")

    print("Generando catalogo maestro de entidades para Seguros Generales...")
    df_gen = build_catalog(gen_solvencia, "GENERALES", "Seguros Generales")
    out_gen = OUTPUTS_DIR / "generales" / "maestro_aseguradoras_generales.parquet"
    df_gen.to_parquet(out_gen, index=False)
    print(f"Exito Generales: {out_gen} ({len(df_gen)} entidades registradas)")

if __name__ == "__main__":
    main()

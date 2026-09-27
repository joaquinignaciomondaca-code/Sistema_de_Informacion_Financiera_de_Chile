"""Audita la Lista de Entidades de Factoring y Leasing.

El backfill IFRS de cuentas ESF/ER se publica por otro proceso y conserva
advertencias de alcance; este auditor no coteja ni certifica esa serie.
La validez del dígito verificador no certifica identidad ni vigencia CMF.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/outputs/factoring_leasing"
RETIRED = (
    "factoring_leasing_balance_resumen",
    "factoring_leasing_nota_efectivo_detalle",
    "factoring_leasing_cartera_morosidad_detalle",
)


def dv_m11(body):
    digits = str(body).replace(".", "")
    if not digits.isdigit():
        raise ValueError("RUT contiene caracteres no numéricos")
    remainder = 11 - sum(int(ch) * (i % 6 + 2) for i, ch in enumerate(reversed(digits))) % 11
    return "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)


def run_audit(output_dir=OUTPUT):
    output_dir = Path(output_dir)
    parquet = output_dir / "factoring_leasing_maestro.parquet"
    json_path = output_dir / "factoring_leasing_maestro.json"
    if not parquet.is_file() or not json_path.is_file():
        raise ValueError("Falta Parquet o JSON de la lista de entidades")
    retired_files = [str(output_dir / f"{name}.{ext}") for name in RETIRED for ext in ("json", "parquet")
                     if (output_dir / f"{name}.{ext}").exists()]
    if retired_files:
        raise ValueError(f"Archivos retirados aún publicados: {retired_files}")
    df = pd.read_parquet(parquet)
    rows = json.loads(json_path.read_text(encoding="utf-8"))
    required = {"rut", "razon_social"}
    if df.empty or not required <= set(df.columns) or not isinstance(rows, list) or len(rows) != len(df):
        raise ValueError("Lista vacía, esquema incompleto o cantidad JSON/Parquet distinta")
    if df["rut"].isna().any() or df["razon_social"].isna().any() or df["rut"].duplicated().any():
        raise ValueError("RUT/nombre faltante o RUT duplicado")
    for rut in df["rut"]:
        parts = str(rut).split("-")
        if len(parts) != 2 or dv_m11(parts[0]) != parts[1].upper():
            raise ValueError(f"Dígito verificador inválido: {rut}")
    if any(not isinstance(row, dict) or set(row) != set(df.columns) for row in rows):
        raise ValueError("Columnas JSON/Parquet distintas")
    # El JSON publicado debe representar los mismos registros, no sólo igual cantidad.
    expected = json.loads(df.to_json(orient="records", force_ascii=False))
    if expected != rows:
        raise ValueError("Valores JSON/Parquet distintos en lista de entidades")
    print(f"Lista de Entidades: {len(df)} RUT únicos con DV válido; JSON/Parquet consistentes."
          " La identidad y vigencia registral requieren fuentes oficiales independientes.")
    return len(df)


if __name__ == "__main__":
    run_audit()

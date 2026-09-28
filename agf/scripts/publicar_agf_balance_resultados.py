"""Separa los EEFF IFRS de las AGF en dos tablas publicadas: balance y estado de resultados.

Fuente: agf/fuentes/agf_eeff_cmf.parquet
    Lo escribe stream_cmf_agf.py (se corre a mano, no hay workflow de Actions) leyendo la pestaña
    "Información Financiera" de cada AGF vigente en cmfchile.cl (entidad.php, pestania=3, IFRS
    individual), un trimestre a la vez. La CMF publica en miles de pesos; la fuente guarda millones
    (MM$), por eso las columnas publicadas terminan en _mm_clp.
    El archivo actual es la corrida del 2026-09-23 (publicada antes como agf_balance_resumen).

Salida (docs/outputs/agf/):
    agf_balance.parquet     activos, pasivos, patrimonio, efectivo, otros activos financieros (+ USD)
    agf_resultados.parquet  ingresos de actividades ordinarias acumulados en el año y del trimestre;
                            gastos de administración y ganancia (pérdida) acumulados

Columnas que la fuente no capturó:
    En la corrida del 2026-09-23 "Gastos de administración" y "Ganancia (pérdida)" quedaron en 0 en
    el 100% de las filas, aunque la CMF sí los publica (cotejado: Banchile AGF dic-2025 muestra gastos
    109.451 MM$ y ganancia 47.377 MM$). Las dos únicas etiquetas con tilde fallaron, así que se trata
    de un problema de codificación en el scraper, ya corregido en stream_cmf_agf.py. Si una columna
    viene toda en 0 se publica como NULL (no capturado), no como cero.

Validaciones que detienen la publicación: columnas esperadas; sin (rut, periodo) repetidos; periodo
AAAA-MM trimestral; activos = pasivos + patrimonio (±0,01 MM$) en todas las filas; RUT presente en
agf_maestro.

Uso:  python -m agf.scripts.publicar_agf_balance_resultados [--fuente RUTA] [--seco]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
FUENTE = ROOT / "agf" / "fuentes" / "agf_eeff_cmf.parquet"
OUT = ROOT / "docs" / "outputs" / "agf"
MAESTRO = OUT / "agf_maestro.parquet"
TOL = 0.01  # MM$

ESPERADAS = [
    "rut", "periodo", "razon_social", "total_activos_m_clp", "total_pasivos_m_clp", "patrimonio_neto_m_clp",
    "efectivo_y_equivalentes_m_clp", "cartera_propia_inversiones_m_clp", "ingresos_comisiones_m_clp",
    "gastos_administracion_m_clp", "ganancia_perdida_ejercicio_m_clp", "total_activos_m_usd", "patrimonio_neto_m_usd",
]
RESULTADOS_ACUM = {
    "ingresos_comisiones_m_clp": "ingresos_ordinarios_acum_mm_clp",
    "gastos_administracion_m_clp": "gastos_administracion_acum_mm_clp",
    "ganancia_perdida_ejercicio_m_clp": "ganancia_perdida_acum_mm_clp",
}


def fallar(msg: str) -> None:
    raise SystemExit(f"✗ {msg}")


def leer(fuente: Path) -> pd.DataFrame:
    df = pd.read_parquet(fuente)
    faltan = set(ESPERADAS) - set(df.columns)
    if faltan:
        fallar(f"Faltan columnas en la fuente: {sorted(faltan)}")
    df = df[ESPERADAS].copy()
    df["periodo"] = df["periodo"].astype(str)
    if not df["periodo"].str.fullmatch(r"20\d{2}-(03|06|09|12)").all():
        fallar("Hay periodos que no son cierres trimestrales AAAA-MM")
    if df.duplicated(["rut", "periodo"]).any():
        fallar("Hay (rut, periodo) repetidos")
    gap = (df["total_activos_m_clp"] - df["total_pasivos_m_clp"] - df["patrimonio_neto_m_clp"]).abs()
    if (gap > TOL).any():
        fallar(f"{int((gap > TOL).sum())} balances no cuadran activos = pasivos + patrimonio")
    if MAESTRO.exists():
        sin_maestro = set(df["rut"]) - set(pd.read_parquet(MAESTRO, columns=["rut"])["rut"])
        if sin_maestro:
            fallar(f"RUT sin fila en agf_maestro: {sorted(sin_maestro)}")
    return df


def no_capturadas(df: pd.DataFrame) -> list[str]:
    return [c for c in RESULTADOS_ACUM if (df[c].fillna(0) == 0).all()]


def construir(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    df = df.sort_values(["rut", "periodo"]).reset_index(drop=True)
    base = df[["rut", "periodo", "razon_social"]].copy()
    base["razon_social"] = base["razon_social"].str.replace(r"\s+", " ", regex=True).str.strip()
    base["anio"] = base["periodo"].str[:4].astype(int)
    base["mes"] = base["periodo"].str[5:].astype(int)

    balance = base[["rut", "periodo", "razon_social"]].copy()
    balance["total_activos_mm_clp"] = df["total_activos_m_clp"]
    balance["total_pasivos_mm_clp"] = df["total_pasivos_m_clp"]
    balance["patrimonio_mm_clp"] = df["patrimonio_neto_m_clp"]
    balance["efectivo_equivalentes_mm_clp"] = df["efectivo_y_equivalentes_m_clp"]
    balance["otros_activos_financieros_mm_clp"] = df["cartera_propia_inversiones_m_clp"]
    balance["total_activos_mm_usd"] = df["total_activos_m_usd"]
    balance["patrimonio_mm_usd"] = df["patrimonio_neto_m_usd"]

    vacias = no_capturadas(df)
    res = base[["rut", "periodo", "razon_social"]].copy()
    res["meses_acumulados"] = base["mes"]
    for origen, destino in RESULTADOS_ACUM.items():
        res[destino] = np.nan if origen in vacias else df[origen]
    # Trimestre = acumulado del año menos el acumulado del trimestre anterior del mismo año y AGF.
    # Marzo es el propio acumulado; si falta el trimestre anterior, queda NULL.
    acum = res["ingresos_ordinarios_acum_mm_clp"]
    previo = res.assign(_mes=base["mes"] + 3, _anio=base["anio"])[["rut", "_anio", "_mes", "ingresos_ordinarios_acum_mm_clp"]]
    previo.columns = ["rut", "anio", "mes", "_acum_previo"]
    unido = base[["rut", "anio", "mes"]].merge(previo, on=["rut", "anio", "mes"], how="left")
    res["ingresos_ordinarios_trimestre_mm_clp"] = np.where(
        base["mes"] == 3, acum, (acum - unido["_acum_previo"].values).round(3))
    res = res[["rut", "periodo", "razon_social", "meses_acumulados", "ingresos_ordinarios_acum_mm_clp",
               "ingresos_ordinarios_trimestre_mm_clp", "gastos_administracion_acum_mm_clp", "ganancia_perdida_acum_mm_clp"]]
    orden = ["periodo", "rut"]
    return balance.sort_values(orden).reset_index(drop=True), res.sort_values(orden).reset_index(drop=True), vacias


def escribir(df: pd.DataFrame, nombre: str) -> Path:
    destino = OUT / f"{nombre}.parquet"
    tmp = destino.with_suffix(".parquet.tmp")
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), tmp, compression="zstd")
    if pq.read_table(tmp).num_rows != len(df):
        tmp.unlink()
        fallar(f"Relectura de {nombre} no coincide")
    tmp.replace(destino)
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuente", type=Path, default=FUENTE)
    ap.add_argument("--seco", action="store_true", help="valida sin escribir")
    args = ap.parse_args()
    balance, resultados, vacias = construir(leer(args.fuente))
    trim = resultados["ingresos_ordinarios_trimestre_mm_clp"]
    print(f"{len(balance)} balances de {balance['rut'].nunique()} AGF, {balance['periodo'].min()}–{balance['periodo'].max()}. "
          f"Ingresos del trimestre: {int(trim.notna().sum())} calculados, {int(trim.isna().sum())} sin trimestre previo, "
          f"{int((trim < 0).sum())} negativos (reexpresiones).")
    if vacias:
        print(f"⚠ No capturadas en la fuente (todo 0 → NULL): {', '.join(vacias)}")
    if args.seco:
        return
    for df, nombre in ((balance, "agf_balance"), (resultados, "agf_resultados")):
        print("→", escribir(df, nombre).relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())

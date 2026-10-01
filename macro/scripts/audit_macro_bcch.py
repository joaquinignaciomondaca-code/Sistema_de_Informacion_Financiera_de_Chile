#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría de integridad de las tablas temáticas macro (BCCh SIETE).

Valida, sobre docs/outputs/macro/ (o el directorio indicado):
1. Que exista un Parquet por cada tabla temática declarada en build_tablas_tematicas.TABLAS
   y que tenga exactamente las columnas declaradas (fecha, periodo + indicadores).
2. Unicidad y orden cronológico de `fecha`; sin fechas futuras; `periodo` = fecha[:7].
3. Que cada columna sea numérica y no esté completamente vacía.
4. Que ninguna observación de las series nativas se haya perdido al pivotar.
5. Rangos económicos plausibles en indicadores clave (TPM, dólar, UF, IPC, cobre).
6. Que las 51 series del catálogo estén cubiertas por alguna tabla temática.

Uso: python -m macro.scripts.audit_macro_bcch [--input-dir docs/outputs/macro]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from macro.scripts.build_tablas_tematicas import (
    CARPETA_SERIES, CATALOGO_PQ, SALIDA, TABLAS, cargar_series, verificar,
)

RANGOS = {  # columna -> (mínimo, máximo) plausibles
    "tpm_pct": (0.0, 15.0),
    "tib_promedio_pct": (0.0, 15.0),
    "dolar_observado_clp_por_usd": (400.0, 1400.0),
    "euro_observado_clp_por_eur": (500.0, 1500.0),
    "uf_valor_clp": (20000.0, 60000.0),
    "utm_valor_clp": (40000.0, 100000.0),
    "ipc_var_anual_pct": (-5.0, 20.0),
    "cobre_refinado_usd_por_libra": (1.0, 10.0),
    "oro_usd_por_onza_troy": (800.0, 8000.0),
    "desocupacion_pct": (3.0, 20.0),
    "tasa_fed_funds_pct": (0.0, 10.0),
}


def run_audit(macro_dir: Path | None = None) -> int:
    macro_dir = Path(macro_dir or SALIDA).resolve()
    errores: list[str] = []
    hoy = date.today().isoformat()
    print("=" * 70)
    print("Auditoría de integridad: tablas temáticas macro (BCCh SIETE)")
    print(f"Directorio: {macro_dir}")
    print("=" * 70)

    series = cargar_series() if CARPETA_SERIES.exists() else None
    claves_cubiertas: set[str] = set()

    for spec in TABLAS:
        ruta = macro_dir / f"{spec['id']}.parquet"
        if not ruta.exists():
            errores.append(f"{spec['id']}: falta el Parquet")
            continue
        df = pq.read_table(ruta).to_pandas()
        esperadas = ["fecha", "periodo"] + [c for _, c in spec.get("columnas", [])] \
            + [c for c, _, _ in spec.get("derivadas", [])]
        if list(df.columns) != esperadas:
            errores.append(f"{spec['id']}: columnas {list(df.columns)} ≠ {esperadas}")
            continue
        if df["fecha"].duplicated().any() or not df["fecha"].is_monotonic_increasing:
            errores.append(f"{spec['id']}: fechas duplicadas o desordenadas")
        if (df["fecha"] > hoy).any():
            errores.append(f"{spec['id']}: fechas futuras")
        if not (df["periodo"] == df["fecha"].str[:7]).all():
            errores.append(f"{spec['id']}: periodo incoherente con fecha")
        for col in esperadas[2:]:
            if not pd.api.types.is_numeric_dtype(df[col]):
                errores.append(f"{spec['id']}.{col}: no numérica")
            elif df[col].notna().sum() == 0:
                errores.append(f"{spec['id']}.{col}: sin ningún valor")
            elif col in RANGOS:
                lo, hi = RANGOS[col]
                fuera = df[(df[col] < lo) | (df[col] > hi)]
                if not fuera.empty:
                    errores.append(f"{spec['id']}.{col}: {len(fuera)} valores fuera de [{lo}, {hi}] "
                                   f"(ej. {fuera['fecha'].iloc[0]} = {fuera[col].iloc[0]})")
        if series is not None:
            try:
                verificar(spec, df, series)
            except ValueError as e:
                errores.append(str(e))
        claves_cubiertas.update(c for c, _ in spec.get("columnas", []))
        for _, a, b in spec.get("derivadas", []):
            claves_cubiertas.update((a, b))
        print(f"  OK  {spec['id']:38s} {len(df):6d} filas  {df['fecha'].iloc[0]} → {df['fecha'].iloc[-1]}")

    if CATALOGO_PQ.exists():
        cat = pq.read_table(CATALOGO_PQ, columns=["clave"]).column(0).to_pylist()
        faltan = sorted(set(cat) - claves_cubiertas)
        if faltan:
            errores.append(f"series del catálogo sin tabla temática: {faltan}")
        else:
            print(f"  OK  las {len(cat)} series del catálogo están cubiertas por las {len(TABLAS)} tablas")

    print("=" * 70)
    if errores:
        for e in errores:
            print(f"  ERROR  {e}")
        print(f"Auditoría FALLIDA: {len(errores)} problema(s).")
        return 1
    print("Auditoría OK.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", default=None)
    a = ap.parse_args()
    sys.exit(run_audit(a.input_dir))

#!/usr/bin/env python3
"""Consolida los resultados de varias ramas `actions/ps-extraccion-<desde>-<hasta>-<run_id>` (tramos de años corridos en
paralelo) en una sola carpeta de salida, sin duplicados y con las mismas claves que usa el pipeline.

Uso:
    python securitizadoras/scripts/consolidar_tramos.py /tmp/full_2010-2013 /tmp/full_2014-2017 ... [--out docs/outputs/securitizadoras]

Cada argumento es una carpeta que contiene `docs/outputs/securitizadoras/` (o directamente los Parquet). Las tablas de
período (balances, líneas, notas, cobertura) se concatenan y se deduplican por su clave conservando la fila del tramo
más reciente (último argumento gana); las tablas maestras (que cada tramo genera completas) se toman del último tramo.
No modifica ningún valor: sólo une y ordena.
"""
import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_securitizadoras as P  # noqa: E402

# clave de "unidad de extracción": si dos tramos traen la misma unidad, se conservan TODAS las filas del último tramo
# (y ninguna del anterior), así no se mezclan lecturas distintas del mismo PDF.
CLAVES = {
    "patrimonios_separados_balance_resumen": ["id_patrimonio", "periodo"],
    "patrimonios_separados_eeff_lineas": ["id_patrimonio", "periodo"],
    "patrimonios_separados_notas_detalle": ["id_patrimonio", "periodo"],
    "patrimonios_separados_cobertura": ["rut_administradora", "periodo", "etiqueta_web"],
    "securitizadoras_balance_resumen": ["rut", "periodo"],
}
MAESTROS = ["securitizadoras_maestro", "patrimonios_separados_maestro"]


def _dir_tablas(raiz):
    cand = os.path.join(raiz, "docs", "outputs", "securitizadoras")
    return cand if os.path.isdir(cand) else raiz


def _leer(raiz, nombre):
    f = os.path.join(_dir_tablas(raiz), f"{nombre}.parquet")
    return pd.read_parquet(f) if os.path.exists(f) else None


def consolidar(tramos, out_dir):
    P.OUT_DIR = out_dir
    resumen = {}
    for nombre, clave in CLAVES.items():
        partes = []
        for k, t in enumerate(tramos):
            d = _leer(t, nombre)
            if d is not None and not d.empty:
                d = d.copy(); d["_tramo"] = k; partes.append(d)
        if not partes:
            continue
        df = pd.concat(partes, ignore_index=True)
        clave_ok = [c for c in clave if c in df.columns]
        antes = len(df)
        ultimo = df.groupby(clave_ok, dropna=False)["_tramo"].transform("max")
        df = df[df["_tramo"] == ultimo].drop(columns="_tramo").reset_index(drop=True)
        orden = clave_ok[:2]
        P.guardar(nombre, df, orden or None)
        resumen[nombre] = (antes, len(df))
    for nombre in MAESTROS:
        for t in reversed(tramos):
            df = _leer(t, nombre)
            if df is not None:
                P.guardar(nombre, df)
                resumen[nombre] = (len(df), len(df))
                break
    return resumen


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tramos", nargs="+")
    ap.add_argument("--out", default=P.OUT_DIR)
    a = ap.parse_args()
    r = consolidar(a.tramos, a.out)
    for k, (antes, despues) in r.items():
        print(f"{k}: {antes} filas leídas → {despues} únicas")

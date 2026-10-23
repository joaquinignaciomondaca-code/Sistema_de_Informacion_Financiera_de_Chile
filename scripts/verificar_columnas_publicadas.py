#!/usr/bin/env python3
"""Ningún Parquet publicado trae columnas fuera del esquema declarado.

`pipelines/esquema_publicado.py` decide qué columnas viajan en el archivo que se
descarga; el resto son columnas de control que se calculan para validar y no se
publican. Esta compuerta contrasta esa lista con los Parquet servidos: falla si una
partición trae una columna de más, si le falta una declarada o si el orden cambió.

    python3 scripts/verificar_columnas_publicadas.py           # informa
    python3 scripts/verificar_columnas_publicadas.py --check   # exit 1 si hay desvío
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pipelines.esquema_publicado import COLUMNAS_PUBLICADAS  # noqa: E402

MANIFIESTO = RAIZ / "data_manifest.json"
DOCS = RAIZ / "docs"


def particiones(tabla: dict) -> list[Path]:
    """Archivos Parquet del conjunto, según su manifiesto de particiones.

    En `data_manifest.json` el manifiesto del conjunto puede venir en `files_manifest`
    o, para las series por año o por mes, en `file_parquet` apuntando a un JSON.
    """
    archivos: list[Path] = []
    candidatos = [tabla.get("files_manifest"), tabla.get("file_parquet")]
    for candidato in candidatos:
        if not candidato:
            continue
        ruta = DOCS / candidato
        if ruta.suffix == ".json" and ruta.is_file():
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            archivos = [DOCS / f for f in datos.get("files", [])]
        elif ruta.suffix == ".parquet":
            archivos = [ruta]
        if archivos:
            break
    return [a for a in archivos if a.is_file()]


def main() -> int:
    import pyarrow.parquet as pq

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="falla si alguna partición se desvía")
    args = ap.parse_args()

    tablas = {t["id"]: t for t in json.loads(MANIFIESTO.read_text(encoding="utf-8"))["tables"]}
    problemas: list[str] = []
    revisadas = 0
    for conjunto, esperadas in COLUMNAS_PUBLICADAS.items():
        tabla = tablas.get(conjunto)
        if not tabla:
            problemas.append(f"{conjunto}: no está en data_manifest.json")
            continue
        archivos = particiones(tabla)
        if not archivos:
            problemas.append(f"{conjunto}: no se encontró ningún Parquet publicado")
            continue
        for archivo in archivos:
            columnas = pq.read_schema(archivo).names
            revisadas += 1
            if columnas == esperadas:
                continue
            de_mas = [c for c in columnas if c not in esperadas]
            de_menos = [c for c in esperadas if c not in columnas]
            detalle = []
            if de_mas:
                detalle.append("columnas de más: " + ", ".join(de_mas))
            if de_menos:
                detalle.append("columnas declaradas que faltan: " + ", ".join(de_menos))
            if not detalle:
                detalle.append("mismas columnas en otro orden")
            problemas.append(f"{archivo.relative_to(RAIZ)}: " + "; ".join(detalle))

    for problema in problemas[:12]:
        print("  [FALLA] " + problema)
    if len(problemas) > 12:
        print(f"  … y {len(problemas) - 12} más")
    print(
        f"COLUMNAS PUBLICADAS: {revisadas} partición(es) de {len(COLUMNAS_PUBLICADAS)} conjunto(s) "
        f"revisadas · {len(problemas)} problema(s)"
    )
    return 1 if (problemas and args.check) else (1 if problemas else 0)


if __name__ == "__main__":
    raise SystemExit(main())

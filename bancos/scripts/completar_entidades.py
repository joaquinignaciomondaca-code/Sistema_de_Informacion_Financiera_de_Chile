#!/usr/bin/env python3
"""Completa `rut` y `razon_social` en las particiones de banca ya publicadas.

Hallazgo 16 de `docs/notas/ruta_api_v1_2026-10-22.md`: el extractor escribía las
dos columnas a `None` en todas las filas desde 2022-01. Las columnas existían, el
esquema las declaraba VARCHAR y la base las tipaba `NULL`, así que un
`WHERE rut = '97004000'` devolvía **0 filas sin error** habiendo 1.945 líneas de
ese banco en el período.

Este script repara lo publicado sin volver a descargar la CMF: el cruce
`codigo_institucion -> rut, razon_social` ya está en `bancos_maestro.parquet`. Es
idempotente (si una partición ya tiene los valores, no se reescribe) y escribe
cada archivo en un temporal antes de reemplazarlo.

El arreglo de origen (para las particiones futuras) está en
`extract_cmf_bank_lines.extract_archive(..., entidades=…)` y lo usa
`publish_cmf_bank_period.py`.

    python3 bancos/scripts/completar_entidades.py            # repara
    python3 bancos/scripts/completar_entidades.py --check    # exit 1 si queda algo a NULL
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SALIDA = ROOT / "docs" / "outputs" / "bancos" / "cmf_b1_b2_r1"
MAESTRO = ROOT / "docs" / "outputs" / "bancos" / "bancos_maestro.parquet"
COLUMNAS = ("rut", "razon_social")


def cargar_entidades() -> dict[str, dict[str, str]]:
    import pyarrow.parquet as pq

    if not MAESTRO.exists():
        raise SystemExit(f"Falta el maestro de bancos: {MAESTRO.relative_to(ROOT)}")
    filas = pq.read_table(MAESTRO, columns=["codigo_institucion", "rut", "razon_social"]).to_pylist()
    return {
        f["codigo_institucion"]: {"rut": f["rut"], "razon_social": f["razon_social"]}
        for f in filas
        if f["codigo_institucion"] and f["rut"]
    }


def particiones() -> list[Path]:
    return sorted(SALIDA.glob("*/lineas.parquet"))


def completar(archivo: Path, entidades: dict[str, dict[str, str]]) -> tuple[bool, int, int]:
    """Devuelve (cambió, filas, filas_sin_entidad)."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    tabla = pq.read_table(archivo)
    codigos = tabla.column("codigo_institucion").to_pylist()
    rut = [entidades.get(c, {}).get("rut") for c in codigos]
    razon = [entidades.get(c, {}).get("razon_social") for c in codigos]
    sin_entidad = sum(1 for c in codigos if c not in entidades)

    if tabla.column("rut").to_pylist() == rut and tabla.column("razon_social").to_pylist() == razon:
        return False, tabla.num_rows, sin_entidad

    # El Parquet publicado tipa las dos columnas como `null` (todas las filas
    # venían en NULL). Se reconstruyen como string, que es lo que declara el
    # esquema del contrato.
    indice_rut = tabla.schema.get_field_index("rut")
    indice_razon = tabla.schema.get_field_index("razon_social")
    nueva = tabla.set_column(indice_rut, pa.field("rut", pa.string(), nullable=True),
                             pa.array(rut, type=pa.string()))
    nueva = nueva.set_column(indice_razon, pa.field("razon_social", pa.string(), nullable=True),
                             pa.array(razon, type=pa.string()))

    temporal = archivo.with_suffix(".parquet.tmp")
    pq.write_table(nueva, temporal, compression="zstd", version="2.6")
    comprobada = pq.read_table(temporal)
    if comprobada.num_rows != tabla.num_rows or comprobada.column_names != tabla.column_names:
        temporal.unlink(missing_ok=True)
        raise RuntimeError(f"{archivo}: el Parquet temporal no conserva filas ni columnas")
    os.replace(temporal, archivo)
    return True, tabla.num_rows, sin_entidad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="no escribe: falla si queda alguna fila sin entidad")
    args = ap.parse_args()

    entidades = cargar_entidades()
    print(f"Maestro de bancos: {len(entidades)} instituciones con RUT")

    cambiadas = 0
    incorrectas = 0
    filas = 0
    sin_entidad = 0
    pendientes: list[str] = []
    for archivo in particiones():
        if args.check:
            malas, n, huerfanas = _inspeccionar(archivo, entidades)
            incorrectas += malas
        else:
            cambio, n, huerfanas = completar(archivo, entidades)
            cambiadas += int(cambio)
        filas += n
        sin_entidad += huerfanas
        if huerfanas:
            pendientes.append(f"{archivo.parent.name}: {huerfanas} filas con un código que no está en el maestro")
        if args.check and malas:
            pendientes.append(f"{archivo.parent.name}: {malas} filas sin el RUT del maestro")

    if args.check:
        print(json.dumps({"particiones": len(particiones()), "filas": filas,
                          "filas_incorrectas": incorrectas, "filas_sin_entidad": sin_entidad,
                          "pendientes": pendientes[:5]}, ensure_ascii=False, indent=1))
        if pendientes:
            print("BANCA: quedan filas sin RUT o con un RUT que no es el del maestro")
            return 1
        print("BANCA: todas las filas tienen el RUT y la razón social del maestro")
        return 0

    print(json.dumps({"particiones": len(particiones()), "reescritas": cambiadas,
                      "filas": filas, "filas_sin_entidad": sin_entidad,
                      "pendientes": pendientes[:5]}, ensure_ascii=False, indent=1))
    return 1 if pendientes else 0


def _inspeccionar(archivo: Path, entidades: dict[str, dict[str, str]]) -> tuple[bool, int, int]:
    import pyarrow.parquet as pq

    tabla = pq.read_table(archivo, columns=["codigo_institucion", "rut", "razon_social"])
    codigos = tabla.column("codigo_institucion").to_pylist()
    ruts = tabla.column("rut").to_pylist()
    razones = tabla.column("razon_social").to_pylist()
    esperado_rut = [entidades.get(c, {}).get("rut") for c in codigos]
    sin_entidad = sum(1 for c in codigos if c not in entidades)
    esperado_razon = [entidades.get(c, {}).get("razon_social") for c in codigos]
    malas = sum(1 for a, b, c, d in zip(ruts, esperado_rut, razones, esperado_razon) if a != b or c != d)
    return malas, tabla.num_rows, sin_entidad


if __name__ == "__main__":
    raise SystemExit(main())

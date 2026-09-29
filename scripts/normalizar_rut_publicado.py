#!/usr/bin/env python3
"""Backfill: aplica la convención de RUT (pipelines/auto/rut.py) a lo ya publicado.

Reescribe los Parquet (conservando límites de row group y codec) y los JSON
(conservando estilo de indentación) de docs/outputs/ que lleven columnas
RUT en formato no canónico. Idempotente: en una segunda corrida no escribe nada.

Uso:
    python3 scripts/normalizar_rut_publicado.py             # dry-run (plan)
    python3 scripts/normalizar_rut_publicado.py --apply     # escribe
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pyarrow as pa
import pyarrow.parquet as pq

from pipelines.auto.rut import normalizar_registros, normalizar_tabla, _op_de

DOCS = Path(__file__).resolve().parents[1] / "docs" / "outputs"


def transformar_parquet(ruta: Path, apply: bool = False) -> tuple[bool, str]:
    pf = pq.ParquetFile(ruta)
    nombres0 = list(pf.schema_arrow.names)
    if not any(n in ("rut", "rut_cuerpo", "rut_formateado") or _op_de(n)[0] for n in nombres0):
        return False, "sin columnas afectadas"
    md = pf.metadata
    codecs = {md.row_group(0).column(j).compression for j in range(md.row_group(0).num_columns)}
    codec = (sorted(codecs)[0] or "snappy").lower()
    transformados, cambios = [], set()
    try:
        for i in range(pf.num_row_groups):
            t2, cam = normalizar_tabla(pf.read_row_group(i))
            transformados.append(t2)
            cambios.update(cam)
    except ValueError as e:
        return False, f"OMITIDO ({e})"
    if not cambios:
        return False, "sin cambios"
    if not apply:
        return True, ", ".join(sorted(cambios))
    final: list[str] = []
    for t in transformados:
        for n in t.column_names:
            if n not in final:
                final.append(n)
    base = transformados[0]
    for t in transformados[1:]:
        for n in t.column_names:
            if n not in base.column_names and n not in final:
                final.append(n)
    tipos = {n: transformados[0].field(n).type for n in final if n in transformados[0].column_names}
    for t in transformados:
        for n in final:
            if n in t.column_names and n not in tipos:
                tipos[n] = t.field(n).type
    alineados = [_alinear(t, final, tipos) for t in transformados]
    tmp = ruta.with_suffix(".parquet.tmp")
    # Sin metadata key-value (pandas/ARROW:schema): el esquema físico es la
    # fuente de verdad y la metadata heredada quedaría obsoleta.
    w = pq.ParquetWriter(tmp, alineados[0].schema.remove_metadata(), compression=codec)
    for t in alineados:
        w.write_table(t)
    w.close()
    tmp.replace(ruta)
    return True, ", ".join(sorted(cambios))


def _alinear(t: "pa.Table", nombres: list[str], tipos: dict) -> "pa.Table":
    for n in nombres:
        if n not in t.column_names:
            t = t.append_column(n, pa.null_array(t.num_rows, type=tipos.get(n, pa.string())))
    if list(t.column_names) != nombres:
        t = t.select(nombres)
    return t


def _estilo_json(raw: str) -> tuple[int, tuple[str, str]]:
    m = re.search(r'\n(\s+)"', raw)
    indent = len(m.group(1)) if m else 2
    sep = ": " if re.search(r": \"", raw) else ":"
    return indent, (",", sep)


def transformar_json(ruta: Path, apply: bool = False) -> tuple[bool, str]:
    raw = ruta.read_text(encoding="utf-8")
    try:
        datos = json.loads(raw)
    except Exception:
        return False, "no JSON"
    if not isinstance(datos, list) or not datos or not isinstance(datos[0], dict):
        return False, "no lista de objetos"
    if not any(str(k).startswith(("rut", "run")) for r in datos[:50] for k in r):
        return False, "sin columnas RUT"
    nuevo, cambios = normalizar_registros(datos)
    if not cambios:
        return False, "sin cambios"
    if not apply:
        return True, ", ".join(sorted(cambios))
    indent, sep = _estilo_json(raw)
    texto = json.dumps(nuevo, ensure_ascii=False, indent=indent, separators=sep)
    if raw.endswith("\n"):
        texto += "\n"
    ruta.write_text(texto, encoding="utf-8")
    return True, ", ".join(sorted(cambios))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="escribe (por defecto solo dry-run)")
    args = ap.parse_args()

    n_pq = n_js = 0
    for ruta in sorted(DOCS.rglob("*.parquet")):
        ok, detalle = transformar_parquet(ruta, args.apply)
        if ok:
            n_pq += 1
            if not args.apply:
                print(f"  {ruta.relative_to(DOCS.parent.parent)}: {detalle}")
    for ruta in sorted(DOCS.rglob("*.json")):
        if "manifest" in ruta.stem:
            continue
        ok, detalle = transformar_json(ruta, args.apply)
        if ok:
            n_js += 1
            if not args.apply:
                print(f"  {ruta.relative_to(DOCS.parent.parent)}: {detalle}")
    verbo = "escritos" if args.apply else "planificados (dry-run; --apply para escribir)"
    print(f"\nParquet {verbo}: {n_pq} · JSON {verbo}: {n_js}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

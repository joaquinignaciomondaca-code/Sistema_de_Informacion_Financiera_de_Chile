#!/usr/bin/env python3
"""Aplica al Parquet ya publicado de pactos FI las reparaciones de texto del extractor.

Los Parquet de `docs/outputs/fi/pactos/` se publicaron antes de que el extractor reparara el
texto dañado de la CMF. Este script los deja consistentes con las reglas vigentes sin volver a
consultar la fuente y sin agregar ni quitar filas, ni cambiar ningún importe:

  * `rut_contraparte`: descarta el dígito verificador pegado al cuerpo (805370009 → 80537000),
    que es la convención publicada («cuerpo del RUT, sin DV»).
  * `contraparte`: normaliza por RUT con el padrón de contrapartes (nombre canónico, grafías
    alternativas conocidas del mismo RUT —abreviaturas, siglas y plurales— y reparación del
    carácter de reemplazo (�) cuando hay reconstrucción verificada). También completa la
    contraparte vacía de una fila cuyo RUT sí está en el padrón.
  * `isin`, `nemotecnico`, `nombre_emisor`: los centinelas «NA»/«N/A»/«S/I» se publican como
    vacío (la convención de la casa para «sin dato») y se aplican las reconstrucciones
    verificadas de `TEXTOS_REPARADOS`.

Idempotente: una segunda corrida no escribe nada.

Uso:
    python3 scripts/reparar_pactos_fi.py             # dry-run (plan)
    python3 scripts/reparar_pactos_fi.py --apply     # escribe
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from fi.scripts.actualizar_carteras import (  # noqa: E402
    CENTINELAS_TEXTO,
    TEXTOS_REPARADOS,
    TEXTO_VACIO,
    cuerpo_contraparte,
    normalizar_contraparte,
)

RAIZ = Path(__file__).resolve().parents[1]
DIR_PACTOS = RAIZ / "docs" / "outputs" / "fi" / "pactos"
COLUMNAS = ("rut_contraparte", "contraparte") + tuple(sorted(CENTINELAS_TEXTO))


def reparar_tabla(tabla: "pa.Table") -> tuple["pa.Table", dict[str, int]]:
    """Devuelve la tabla reparada y las celdas cambiadas por columna."""
    nombres = tabla.column_names
    presentes = [c for c in COLUMNAS if c in nombres]
    originales = {c: tabla.column(c).to_pylist() for c in presentes}
    nuevos = {c: list(originales[c]) for c in presentes}

    if "rut_contraparte" in nombres:
        nuevos["rut_contraparte"] = [cuerpo_contraparte(v) for v in originales["rut_contraparte"]]
    if "contraparte" in nombres:
        ruts = nuevos.get("rut_contraparte", originales.get("rut_contraparte", [None] * tabla.num_rows))
        nuevos["contraparte"] = [normalizar_contraparte(r, n) for r, n in zip(ruts, originales["contraparte"])]
    for col in sorted(CENTINELAS_TEXTO):
        if col not in nombres:
            continue
        valores = []
        for v in originales[col]:
            if isinstance(v, str):
                s = v.strip()
                if s.upper() in TEXTO_VACIO:
                    valores.append(None)
                    continue
                if s in TEXTOS_REPARADOS:
                    valores.append(TEXTOS_REPARADOS[s])
                    continue
            valores.append(v)
        nuevos[col] = valores

    cambios = {c: sum(1 for a, b in zip(originales[c], nuevos[c]) if a != b) for c in presentes}
    for col, cambiadas in cambios.items():
        if cambiadas:
            tabla = tabla.set_column(nombres.index(col), col, pa.array(nuevos[col], type=tabla.schema.field(col).type))
    return tabla, cambios


def reparar_archivo(ruta: Path, apply: bool = False) -> tuple[int, dict[str, int]]:
    pf = pq.ParquetFile(ruta)
    tabla = pq.read_table(ruta)
    nueva, cambios = reparar_tabla(tabla)
    total = sum(cambios.values())
    if not total or not apply:
        return total, cambios
    codec = (pf.metadata.row_group(0).column(0).compression or "snappy").lower()
    opciones = {"compression": codec}
    if codec == "zstd":  # el extractor escribe zstd nivel 9
        opciones["compression_level"] = 9
    tmp = ruta.with_suffix(".parquet.tmp")
    pq.write_table(nueva, tmp, **opciones)
    tmp.replace(ruta)
    return total, cambios


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="escribe los Parquet (sin esto sólo informa el plan)")
    a = ap.parse_args(argv)
    rutas = [r for r in sorted(DIR_PACTOS.glob("*.parquet")) if r.name != "_vacio.parquet"]
    if not rutas:
        print(f"No hay Parquet de pactos en {DIR_PACTOS.relative_to(RAIZ)}.")
        return 0
    total, por_columna, tocados = 0, {c: 0 for c in COLUMNAS}, []
    for ruta in rutas:
        cambiadas, cambios = reparar_archivo(ruta, a.apply)
        if not cambiadas:
            continue
        tocados.append(ruta.name)
        total += cambiadas
        for col, n in cambios.items():
            por_columna[col] += n
        detalle = ", ".join(f"{col}: {n}" for col, n in sorted(cambios.items()) if n)
        print(f"{ruta.name}: {cambiadas} celdas ({detalle})")
    if not total:
        print("Nada que reparar: los Parquet ya siguen las reglas del extractor.")
        return 0
    resumen = ", ".join(f"{col}: {n}" for col, n in sorted(por_columna.items()) if n)
    accion = "reparadas" if a.apply else "a reparar (dry-run)"
    print(f"\n{total} celdas {accion} en {len(tocados)} archivos ({resumen}).")
    if not a.apply:
        print("Dry-run: vuelve a correrlo con --apply para escribir. Al aplicar cambian los pesos,")
        print("así que después hay que regenerar el catálogo: python3 scripts/build_download_catalog.py")
    else:
        print("Regenera el catálogo de descargas: python3 scripts/build_download_catalog.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

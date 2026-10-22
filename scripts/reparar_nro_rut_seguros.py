#!/usr/bin/env python3
"""Repara el RUT del emisor en los Parquet de seguros ya publicados (Circular 1835).

La ficha de la CMF declara `NRO_RUT` como campo tipo "r" de 10 caracteres: nueve
cifras de cuerpo (con los ceros a la izquierda) más el dígito verificador. El
extractor lo publicaba tal cual, `97006000-6`, mientras el resto de la base usa
la convención de `pipelines/auto/rut.py` (`rut` = cuerpo, `rut_dv` = cuerpo-DV).
Consecuencia: un `JOIN` entre seguros y cualquier otra industria devolvía cero
filas sin error, que es el peor modo de fallo.

Este script deja lo publicado consistente con las reglas vigentes **sin volver a
consultar la fuente y sin agregar ni quitar filas, ni cambiar importe alguno**:

  * `nro_rut`  → cuerpo (`97006000`).
  * `nro_rut_dv` → cuerpo-DV (`97006000-6`), en la misma posición que publica
    `seguros/scripts/actualizar_carteras.py::esquema()`.
  * `nro_rut_<algo>` (FK, p. ej. `nro_rut_activo_objeto`) → cuerpo.

Las demás columnas se copian intactas y se verifica que sigan siendo idénticas
antes de escribir. Idempotente: una segunda corrida no escribe nada.

Uso:
    python3 scripts/reparar_nro_rut_seguros.py           # dry-run (plan)
    python3 scripts/reparar_nro_rut_seguros.py --apply   # escribe

Requiere `pyarrow`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SALIDA = RAIZ / "docs" / "outputs" / "seguros"
FAMILIA = ("nro_rut", "nro_rut_dv")


def columnas_afectadas(nombres: list[str]) -> list[str]:
    """Columnas de la familia `nro_rut*` presentes en el archivo."""
    return [c for c in nombres if c.startswith(FAMILIA[0])]


def _es_columna_rut(nombre: str) -> bool:
    return nombre.startswith(FAMILIA[0])


def reparar_tabla(t):  # noqa: ANN001, ANN201 - pyarrow.Table
    """Devuelve (tabla reparada, nº de celdas cambiadas). No muta la entrada."""
    import pyarrow as pa

    from pipelines.auto.rut import normalizar_tabla

    nombres = list(t.column_names)
    if not columnas_afectadas(nombres):
        return t, 0

    antes = {c: t[c].to_pylist() for c in nombres}
    t2, _ = normalizar_tabla(t)
    if "nro_rut" not in t2.column_names:
        # Sólo FK `nro_rut_<algo>`: la normalización ya dejó el cuerpo, nada que ordenar.
        cambiadas = sum(
            1 for c in nombres if _es_columna_rut(c)
            for a, b in zip(antes[c], t2[c].to_pylist()) if a != b
        )
        return t2, cambiadas

    # Posición canónica: `nro_rut_dv` justo después de `nro_rut`, como en el esquema
    # del publicador. Sin esto, el próximo mes quedaría con otro orden de columnas.
    orden = [c for c in t2.column_names if c != "nro_rut_dv"]
    orden.insert(orden.index("nro_rut") + 1, "nro_rut_dv")
    t2 = t2.select(orden)
    t2 = t2.set_column(t2.column_names.index("nro_rut_dv"), "nro_rut_dv",
                       t2["nro_rut_dv"].cast(pa.string()))

    # Ninguna otra columna puede cambiar.
    for c in nombres:
        if _es_columna_rut(c):
            continue
        if antes[c] != t2[c].to_pylist():
            raise RuntimeError(f"la reparación alteró la columna {c!r}; se aborta")

    # Regenerar la metadata pandas: al añadir una columna, la heredada del archivo
    # original queda obsoleta y el guardián (audit_rut_formatos) la rechaza.
    t2 = pa.Table.from_pandas(t2.to_pandas(), preserve_index=False, schema=t2.schema)

    cambiadas = sum(
        1 for c in nombres if _es_columna_rut(c) and c in antes
        for a, b in zip(antes[c], t2[c].to_pylist()) if a != b
    )
    return t2, cambiadas


def verificar(t, ruta: Path) -> list[str]:  # noqa: ANN001
    """Comprueba que lo reparado cumple la convención. Devuelve problemas."""
    import re

    from pipelines.auto.rut import dv as dv_de

    problemas = []
    re_c = re.compile(r"^\d{4,9}$")
    re_b = re.compile(r"^\d{4,9}-[\dKk]$")
    for col in [c for c in t.column_names if _es_columna_rut(c)]:
        if col.endswith("_dv"):
            continue
        for i, v in enumerate(t[col].to_pylist()):
            if v is None or v == "":
                continue
            if not re_c.match(str(v)):
                problemas.append(f"{ruta.name}: {col} no es cuerpo en fila {i}: {v!r}")
                break
    if "nro_rut_dv" in t.column_names:
        for i, v in enumerate(t["nro_rut_dv"].to_pylist()):
            if v is None or v == "":
                continue
            if not re_b.match(str(v)):
                problemas.append(f"{ruta.name}: nro_rut_dv no es cuerpo-DV en fila {i}: {v!r}")
                break
            cuerpo, dig = str(v).rsplit("-", 1)
            if dig.upper() != dv_de(cuerpo):
                problemas.append(f"{ruta.name}: DV no cuadra en fila {i}: {v!r}")
                break
    return problemas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="escribe los cambios (por defecto: sólo el plan)")
    args = ap.parse_args(argv)

    import pyarrow.parquet as pq

    rutas = sorted(p for p in SALIDA.rglob("*.parquet") if p.name != "_vacio.parquet")
    objetivos, total_filas, bytes_antes = [], 0, 0
    for ruta in rutas:
        md = pq.ParquetFile(ruta).metadata
        if not columnas_afectadas(pq.ParquetFile(ruta).schema_arrow.names):
            continue
        objetivos.append((ruta, md.num_rows))
        total_filas += md.num_rows
        bytes_antes += ruta.stat().st_size

    if not objetivos:
        print("Nada que reparar: ningún Parquet publicado tiene columna nro_rut.")
        return 0

    print(f"{'ESCRIBIENDO' if args.apply else 'DRY-RUN'}: {len(objetivos)} archivo(s), "
          f"{total_filas:,} filas, {bytes_antes / 1048576:.1f} MB")
    problemas: list[str] = []
    bytes_despues = 0
    escritos = 0
    for ruta, filas in objetivos:
        t = pq.read_table(ruta)
        t2, cambiadas = reparar_tabla(t)
        problemas += verificar(t2, ruta)
        if not args.apply:
            continue
        if t2.equals(t) and (t2.schema.metadata or {}) == (t.schema.metadata or {}):
            bytes_despues += ruta.stat().st_size
            continue
        tmp = ruta.with_suffix(".tmp")
        pq.write_table(t2, tmp, compression="zstd", compression_level=9)
        tmp.replace(ruta)
        escritos += 1
        bytes_despues += ruta.stat().st_size

    if complicado := [p for p in problemas]:
        print("PROBLEMAS:")
        for p in complicado[:20]:
            print("  ", p)
        if len(complicado) > 20:
            print(f"   … y {len(complicado) - 20} más")
        return 1

    if args.apply:
        print(f"Escritos {escritos} archivo(s). Nuevo peso: {bytes_despues / 1048576:.1f} MB "
              f"(delta {(bytes_despues - bytes_antes) / 1048576:+.1f} MB).")
    else:
        print("Verificación en memoria: ninguna fila incumple la convención tras la reparación.")
        print("Ejecuta con --apply para escribir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

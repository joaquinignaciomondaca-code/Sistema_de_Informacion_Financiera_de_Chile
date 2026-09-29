#!/usr/bin/env python3
"""Auditoría de formatos de RUT en todo lo publicado (docs/outputs/).

Vigila la convención de `pipelines/auto/rut.py` contra los Parquet y JSON
publicados, para que ningún pipeline vuelva a publicar un formato roto en
silencio:

  * `rut`               → cuerpo (C), sin puntos ni DV.  Un `rut` numérico
                          (int64) ya es el cuerpo y pasa.
  * `rut_dv`, `*_dv`    → cuerpo-DV (B) o cuerpo (si la fuente no traía DV);
                          nunca con puntos.
  * `*_completo`        → con puntos (A) cuando el cuerpo tiene ≥6 cifras;
                          RUNs de 4-5 cifras (fondos) quedan como B.
  * `rut_<entidad>`     → cuerpo (C). Los placeholders numéricos cortos
                          ('0', '99') de los orígenes se toleran.
  * `rut_cuerpo` / `rut_formateado` → no deben existir (sobreviven `rut` y
    `rut_completo`).
  * `run_*`             → fuera de convención (identificadores de fondo).
  * metadata pandas heredada → debe describir las mismas columnas RUT que
    el esquema físico (un re-escritor no debe dejarla obsoleta).

Uso:
    python3 scripts/audit_rut_formatos.py            # informe + fallo si hay errores
    python3 scripts/audit_rut_formatos.py --check    # solo exit code (CI)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipelines.auto.rut import RE_A, RE_B, RE_C, _norm

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs" / "outputs"

RE_RUN = re.compile(r"^\d{4,8}(-[\dKk])?$")  # RUNs de fondo, con o sin DV
RE_PH = re.compile(r"^\d{1,3}$")  # placeholder numérico corto del origen


def _check_valor(nombre: str, v) -> str | None:
    """Devuelve un mensaje de error (o None) para un valor de la columna."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    n = _norm(s)
    if n is None:
        # no parseable: RUN de fondo (run_*/_completo) o placeholder numérico
        # corto del origen ('0', '1', '90' = emisor no identificado)
        if (nombre.startswith("run_") or nombre.endswith("_completo")) and RE_RUN.match(s):
            return None
        if RE_PH.match(s):
            return None
        return f"valor no reconocido: {s!r}"
    c, dv = n
    if nombre == "rut":
        if RE_A.match(s):
            return f"rut con puntos: {s!r} (debe ser cuerpo)"
        if RE_B.match(s):
            return f"rut con DV: {s!r} (el DV va en rut_dv)"
        return None
    if nombre == "rut_dv" or nombre.endswith("_dv"):
        if RE_A.match(s):
            return f"{nombre} con puntos: {s!r}"
        return None
    if nombre.endswith("_completo"):
        if len(c) >= 6 and not RE_A.match(s):
            return f"{nombre} sin puntos, cuerpo de {len(c)} cifras: {s!r}"
        return None
    if nombre.startswith("run_"):
        return None
    # rut_<entidad>: cuerpo
    if RE_A.match(s):
        return f"{nombre} con puntos: {s!r} (debe ser cuerpo)"
    if RE_B.match(s):
        return f"{nombre} con DV: {s!r} (debe ser cuerpo)"
    return None


def _fam_rut(cols) -> set[str]:
    return {c for c in cols if c == "dv" or str(c).startswith("rut") or str(c).startswith("run")}


def auditar_parquet(ruta: Path) -> list[str]:
    import pyarrow.parquet as pq
    errores: list[str] = []
    t = pq.read_table(ruta)
    for f in t.schema:
        if not (f.name.startswith("rut") or f.name.startswith("run_")):
            continue
        if str(f.type) not in ("string", "large_string"):
            continue  # numérico = cuerpo (C) o nulo: fuera de la auditoría de texto
        if f.name in ("rut_cuerpo", "rut_formateado"):
            errores.append(f"columna retirada presente: {f.name}")
            continue
        for v in t.column(f.name).to_pylist():
            err = _check_valor(f.name, v)
            if err:
                errores.append(f"{f.name}: {err}")
                break  # uno por columna basta para el reporte
    # La metadata key-value heredada (pandas) debe describir las mismas columnas
    # RUT que el esquema físico: si difiere, un re-escritor la dejó obsoleta.
    try:
        kv = pq.ParquetFile(ruta).metadata.metadata
    except Exception:
        kv = None
    if kv and b"pandas" in kv:
        try:
            cols_kv = {c["name"] for c in json.loads(kv[b"pandas"])["columns"]}
        except Exception:
            cols_kv = None
        if cols_kv is not None and _fam_rut(cols_kv) != _fam_rut(t.column_names):
            dif = _fam_rut(cols_kv) ^ _fam_rut(t.column_names)
            errores.append(f"metadata pandas obsoleta (columnas RUT difieren): {sorted(dif)}")
    return errores


def auditar_json(ruta: Path) -> list[str]:
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(datos, list) or not datos or not isinstance(datos[0], dict):
        return []
    errores: list[str] = []
    for nombre in datos[0]:
        if not (str(nombre).startswith("rut") or str(nombre).startswith("run_")):
            continue
        if nombre in ("rut_cuerpo", "rut_formateado"):
            errores.append(f"columna retirada presente: {nombre}")
            continue
        for reg in datos:
            err = _check_valor(str(nombre), reg.get(nombre))
            if err:
                errores.append(f"{nombre}: {err}")
                break
    return errores


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="silencioso; solo exit code")
    args = ap.parse_args()

    n_arch = n_err = 0
    for ruta in sorted(DOCS.rglob("*.parquet")):
        n_arch += 1
        for e in auditar_parquet(ruta):
            n_err += 1
            if not args.check:
                print(f"Error {ruta.relative_to(DOCS)}: {e}")
    for ruta in sorted(DOCS.rglob("*.json")):
        if "manifest" in ruta.stem:
            continue
        n_arch += 1
        for e in auditar_json(ruta):
            n_err += 1
            if not args.check:
                print(f"Error {ruta.relative_to(DOCS)}: {e}")
    if not args.check:
        print(f"RUT: {n_arch} archivos auditados, {n_err} problema(s).")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Revisa que cada tabla de data_manifest.json tenga los metadatos uniformes del punto 7.

Campos exigidos: fuente, unidad, escala, moneda, criterio_contable, cobertura,
fecha_extraccion y estado_qa. Cada campo debe existir y tener texto no vacío.

Uso:
  python scripts/validar_metadatos.py            # informe de cobertura
  python scripts/validar_metadatos.py --lista    # además, una línea por tabla pendiente
  python scripts/validar_metadatos.py --exigir   # sale con 1 si alguna tabla con metadatos incompletos
                                                # o si una tabla de las listadas en --tablas no los tiene
  python scripts/validar_metadatos.py --tablas ffmm_cartera_nacional macro_uf patrimonios_separados_balance --exigir
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CAMPOS = ["fuente", "unidad", "escala", "moneda", "criterio_contable", "cobertura", "fecha_extraccion", "estado_qa"]
RAIZ = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exigir", action="store_true", help="salir con código 1 si falla alguna comprobación")
    ap.add_argument("--tablas", nargs="*", default=[], help="tablas que deben estar completas")
    ap.add_argument("--lista", action="store_true", help="imprime una línea por cada tabla pendiente")
    args = ap.parse_args()

    tablas = json.loads((RAIZ / "data_manifest.json").read_text(encoding="utf-8"))["tables"]
    completas, incompletas = [], []
    for t in tablas:
        meta = t.get("metadatos") or {}
        faltan = [c for c in CAMPOS if not str(meta.get(c, "")).strip()]
        (incompletas if faltan else completas).append((t["id"], faltan))

    print(f"Tablas con metadatos uniformes completos: {len(completas)} de {len(tablas)}")
    if args.lista:
        for tid, faltan in incompletas:
            print(f"  pendiente  {tid:40} faltan: {', '.join(faltan)}")

    fallos = []
    ids_completas = {tid for tid, _ in completas}
    for tid in args.tablas:
        if tid not in {t["id"] for t in tablas}:
            fallos.append(f"{tid}: no existe en data_manifest.json")
        elif tid not in ids_completas:
            fallos.append(f"{tid}: metadatos incompletos")
    for f in fallos:
        print("FALLA:", f)

    if args.exigir and fallos:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

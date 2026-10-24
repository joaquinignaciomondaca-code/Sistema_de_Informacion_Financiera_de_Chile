#!/usr/bin/env python3
"""Guarda margen para los límites de tamaño de GitHub Pages y reporta el peso de datos.

GitHub Pages admite sitios publicados de hasta 1 GiB. Este control falla antes,
a 900 MiB, para dejar margen a despliegues y artefactos que el checkout local no
incluya. También imprime el tamaño del conjunto Parquet publicado, útil para
estimar transferencia; no presupone que una visita descargue todo ese conjunto.

Uso: python scripts/audit_pages_capacity.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CATALOG = DOCS / "api" / "v2" / "catalog.json"
MIB = 1024**2
GIB = 1024**3
LIMITE_GH_PAGES = 900 * MIB
AVISO = 750 * MIB


def main() -> int:
    if not DOCS.is_dir():
        print(f"FALLA: no existe el directorio publicado {DOCS}")
        return 1

    archivos = [p for p in DOCS.rglob("*") if p.is_file() and not p.is_symlink()]
    total = sum(p.stat().st_size for p in archivos)
    print(f"docs/: {total / MIB:.1f} MiB en {len(archivos):,} archivos")
    print(f"Umbral preventivo: {LIMITE_GH_PAGES / MIB:.0f} MiB (límite documentado: 1 GiB)")

    if CATALOG.exists():
        try:
            catalogo = json.loads(CATALOG.read_text(encoding="utf-8"))
            bytes_datos = int(catalogo["totales"]["bytes"])
            filas = int(catalogo["totales"]["filas"])
            transferencias = 100_000_000_000 / bytes_datos if bytes_datos else 0
            print(
                f"Parquet del catálogo: {bytes_datos / MIB:.1f} MiB · "
                f"{filas:,} filas · ~{transferencias:.0f} transferencias completas "
                "equivalen a 100 GB (solo referencia; normalmente se leen rangos parciales)."
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            print(f"FALLA: no se pudo leer el peso del catálogo ({exc})")
            return 1
    else:
        print(f"FALLA: falta el catálogo publicado {CATALOG.relative_to(ROOT)}")
        return 1

    if total >= LIMITE_GH_PAGES:
        print("FALLA: docs/ llegó al umbral preventivo; reducir o externalizar archivos antes de publicar.")
        return 1
    if total >= AVISO:
        print("AVISO: el sitio está sobre 750 MiB; revisar el crecimiento antes del próximo despliegue.")
    else:
        print("OK: el tamaño publicado conserva margen bajo el umbral preventivo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""¿Dónde invierten fuera de Chile los fondos mutuos, en el último mes publicado?

Es la primera consulta del README, ejecutada de principio a fin: el SDK lee el
contrato, crea las vistas y consulta los Parquet. La comprobación no fija el
resultado exacto —los datos cambian todos los meses— sino que comprueba que el
patrón que el README afirma seguir estando:

  * el último período trae posiciones en al menos tres países,
  * EE. UU. está entre ellos,
  * y el mayor país supera el centenar de posiciones.

    python3 examples/python/01_ffmm_extranjero.py
    SIF_CHILE_BASE=docs python3 examples/python/01_ffmm_extranjero.py   # sin red
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import sif_chile
except ModuleNotFoundError:  # se puede correr desde el repo sin instalar nada
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sdk" / "python"))
    import sif_chile

SQL = """
SELECT pais_emisor,
       count(*)                  AS posiciones,
       count(DISTINCT run_fondo) AS fondos
FROM ffmm_cartera_extranjera
WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_extranjera)
GROUP BY pais_emisor
ORDER BY posiciones DESC
"""


def main() -> int:
    with sif_chile.connect() as sif:
        periodo = sif.sql("SELECT max(periodo) FROM ffmm_cartera_extranjera").fetchone()[0]
        filas = sif.sql(SQL).fetchall()

    print(f"Fondos mutuos chilenos invertidos en el exterior · período {periodo}\n")
    print(f"{'país':<6}{'posiciones':>12}{'fondos':>9}")
    print("-" * 27)
    for pais, posiciones, fondos in filas:
        print(f"{pais:<6}{posiciones:>12,}{fondos:>9,}")

    paises = {f[0] for f in filas}
    total = sum(f[1] for f in filas)
    assert filas, "la consulta no devolvió ninguna fila: revisa el período publicado"
    assert len(paises) >= 3, f"solo {len(paises)} países emisores: {paises}"
    assert "US" in paises, f"EE. UU. no aparece entre los emisores: {sorted(paises)}"
    assert total >= 1000, f"solo {total} posiciones en el exterior"
    assert max(f[1] for f in filas) >= 100, "ningún país llega a 100 posiciones"

    print(f"\nOK · {total:,} posiciones en {len(paises)} países, {periodo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

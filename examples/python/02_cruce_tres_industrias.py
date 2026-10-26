#!/usr/bin/env python3
"""El caso que motiva el proyecto: un emisor visto desde tres industrias a la vez.

Bancos, aseguradoras y fondos mutuos publican por separado. Este ejemplo cruza
`bancos_lista_entidades.rut`, `seguros_renta_fija.nro_rut` y
`ffmm_cartera_nacional.rut_emisor`, que se publican en formato de cuerpo para
este JOIN; eso no vuelve intercambiables todos los identificadores del catálogo
ni verifica los DV preexistentes. Lo que se comprueba aquí es **de conjunto y de
umbral**, no un número exacto: las carteras cambian cada mes y fijar «15
emisores» convertiría el ejemplo en una prueba que falla sola.

    python3 examples/python/02_cruce_tres_industrias.py
    SIF_CHILE_BASE=docs python3 examples/python/02_cruce_tres_industrias.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import sif_chile
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sdk" / "python"))
    import sif_chile

SQL = """
WITH bancos AS (
  SELECT rut, razon_social
  FROM bancos_lista_entidades
),
seguros AS (
  SELECT nro_rut AS rut, count(DISTINCT rut_aseguradora) AS aseguradoras
  FROM seguros_renta_fija
  WHERE periodo = (SELECT max(periodo) FROM seguros_renta_fija)
  GROUP BY 1
),
fondos AS (
  SELECT rut_emisor AS rut, count(DISTINCT run_fondo) AS fondos_mutuos
  FROM ffmm_cartera_nacional
  WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_nacional)
  GROUP BY 1
)
SELECT b.razon_social AS emisor, s.aseguradoras, f.fondos_mutuos
FROM bancos b
JOIN seguros s USING (rut)
JOIN fondos f USING (rut)
ORDER BY s.aseguradoras + f.fondos_mutuos DESC
"""


def main() -> int:
    with sif_chile.connect() as sif:
        filas = sif.sql(SQL).fetchall()
        bancos = {b[0] for b in sif.sql("SELECT razon_social FROM bancos_lista_entidades").fetchall()}
        periodos = sif.sql(
            "SELECT (SELECT max(periodo) FROM seguros_renta_fija),"
            "       (SELECT max(periodo) FROM ffmm_cartera_nacional)"
        ).fetchone()

    print(f"Emisores con exposición simultánea · seguros {periodos[0]} · fondos {periodos[1]}\n")
    print(f"{'emisor':<34}{'aseguradoras':>14}{'fondos':>8}")
    print("-" * 56)
    for emisor, aseguradoras, fondos in filas:
        print(f"{emisor:<34}{aseguradoras:>14}{fondos:>8}")

    emisores = {f[0] for f in filas}
    # Conjunto: todo lo que salió del cruce es un banco del catálogo.
    assert emisores, "el cruce no devolvió ningún emisor"
    assert emisores <= bancos, f"emisores fuera del catálogo: {sorted(emisores - bancos)[:5]}"
    # Umbral: el cruce no puede quedarse en un caso anecdótico.
    assert len(emisores) >= 5, f"solo {len(emisores)} emisores cruzados"
    assert all(a >= 1 and f >= 1 for _, a, f in filas), "hay filas con cero en alguna industria"
    concentrado = [f for f in filas if f[1] + f[2] >= 200]
    assert concentrado, "ningún emisor llega a 200 relaciones entre las dos industrias"

    emisor, aseguradoras, fondos = filas[0]
    print(f"\nOK · {len(emisores)} emisores cruzan las tres fuentes; el primero es")
    print(f"     {emisor}: {aseguradoras} aseguradoras y {fondos} fondos mutuos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

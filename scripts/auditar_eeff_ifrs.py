#!/usr/bin/env python3
"""Cuadra, trimestre por trimestre, todos los estados financieros IFRS ya publicados.

El extractor valida «activos = pasivos + patrimonio» al momento de leer un trimestre, pero
solo de los trimestres que lee: los cerrados (más de 150 días) no se vuelven a descargar
nunca, así que de los 69 trimestres publicados únicamente el último pasó por la compuerta.
Este script hace el trabajo que faltaba: recorre **todo lo publicado** (AGF, securitizadoras,
CCAF, factoring y leasing, corredores y agentes de valores, y fondos mutuos) y comprueba

  * el cuadre del balance de cada sociedad y trimestre (activos = pasivos + patrimonio);
  * que la compuerta no se haya quedado ciega: si de pronto casi ningún balance trae los
    tres totales reconocibles, cambiaron las glosas y la validación dejó de proteger;
  * dos identidades del estado de resultados: el resultado integral (`ERI`) arrastra la
    misma ganancia del ejercicio que el `ERFG`/`ERNG`, y ganancia bruta = ingresos − costo
    de ventas.

No descarga nada y no escribe en docs/: lee los Parquet publicados y termina con código 1
si algo no cuadra. Corre en `web_audit.yml` (push, PR y a mano), de modo que la promesa del
README —«se verifica antes de publicar»— queda respaldada por una comprobación ejecutable
sobre la historia completa, no solo por el extractor de turno.

Uso:
    python scripts/auditar_eeff_ifrs.py                # falla si algo no cuadra
    python scripts/auditar_eeff_ifrs.py --detalle      # lista cada hallazgo
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import cuadratura  # noqa: E402

DOCS = RAIZ / "docs" / "outputs"

# Series publicadas a partir del TXT IFRS de la CMF. Las tres primeras salen de
# pipelines/ifrs_sectores (particiones por año); factoring y leasing, de
# factoring_leasing/scripts (un Parquet plano por tabla, mismo archivo de origen). Corredores y
# agentes de valores salen del Excel FECU (corredoras_bolsa/scripts, miles de pesos): su balance
# se cuadra con los códigos 10 = 21 + 22; su estado de resultados no tiene identidades definidas.
# Los fondos mutuos salen del XML IFRS de la ficha de cada fondo (ffmm/scripts, miles de la moneda del
# fondo): activo − pasivo = activo neto atribuible a los partícipes y seis identidades de resultados.
SERIES = [
    # (etiqueta, carpeta de balance, carpeta de resultados, claves, campo valor, verificar_balance, verificar_resultados)
    ("AGF", "agf/agf_balance", "agf/agf_resultados",
     cuadratura.CLAVES_IFRS, "valor", cuadratura.verificar_ifrs, cuadratura.verificar_resultados_ifrs),
    ("Securitizadoras", "securitizadoras/securitizadoras_balance", "securitizadoras/securitizadoras_resultados",
     cuadratura.CLAVES_IFRS, "valor", cuadratura.verificar_ifrs, cuadratura.verificar_resultados_ifrs),
    ("CCAF", "cajas_compensacion/ccaf_balance", "cajas_compensacion/ccaf_resultados",
     cuadratura.CLAVES_IFRS, "valor", cuadratura.verificar_ifrs, cuadratura.verificar_resultados_ifrs),
    ("Factoring y leasing", "factoring_leasing/factoring_leasing_balance_serie_ifrs_cmf.parquet",
     "factoring_leasing/factoring_leasing_resultados_serie_ifrs_cmf.parquet",
     cuadratura.CLAVES_FL, "valor_archivo", cuadratura.verificar_fl, cuadratura.verificar_resultados_fl),
    ("Corredores y agentes", "corredoras_bolsa/corredoras_bolsa_balance", "corredoras_bolsa/corredoras_bolsa_resultados",
     cuadratura.CLAVES_FECU, "valor_miles_clp", cuadratura.verificar_fecu, lambda filas: (0, [])),
    ("Fondos mutuos", "ffmm/ffmm_balance", "ffmm/ffmm_resultados",
     cuadratura.CLAVES_FFMM, "valor_miles_mf", cuadratura.verificar_ffmm, cuadratura.verificar_resultados_ffmm),
]

CAMPO_PERIODO = "periodo"


def leer(ruta_relativa: str):
    """Filas de una serie publicada (carpeta con particiones por año o Parquet plano)."""
    ruta = DOCS / ruta_relativa
    if ruta.is_file():
        return pq.read_table(ruta).to_pylist()
    filas = []
    for p in sorted(ruta.glob("*.parquet")):
        filas.extend(pq.read_table(p).to_pylist())
    return filas


def por_periodo(filas):
    grupos: dict[str, list] = {}
    for f in filas:
        grupos.setdefault(str(f.get(CAMPO_PERIODO)), []).append(f)
    return grupos


def auditar(detalle: bool) -> int:
    fallas: list[str] = []
    resumen = []

    for etiqueta, bal, res, claves, _valor, verificar_balance, verificar_resultados in SERIES:
        filas_bal = leer(bal)
        filas_res = leer(res)
        if not filas_bal:
            fallas.append(f"{etiqueta}: no se encontraron balances publicados en {bal}")
            continue

        totales = verificados = descuadrados = 0
        verificaciones = divergencias = 0
        hallazgos: list[str] = []

        for periodo, grupo in sorted(por_periodo(filas_bal).items()):
            n = cuadratura.contar_grupos(grupo, claves)
            v, malos = verificar_balance(grupo)
            totales += n
            verificados += v
            descuadrados += len(malos)
            for m in malos:
                hallazgos.append(f"{etiqueta} {periodo} · balance · {m}")

        for periodo, grupo in sorted(por_periodo(filas_res).items()):
            v, malos = verificar_resultados(grupo)
            verificaciones += v
            divergencias += len(malos)
            for m in malos:
                hallazgos.append(f"{etiqueta} {periodo} · resultados · {m}")

        cobertura = verificados / totales if totales else 0.0
        resumen.append((etiqueta, totales, verificados, cobertura, descuadrados,
                        verificaciones, divergencias))

        if descuadrados:
            fallas.append(f"{etiqueta}: {descuadrados} balances no cuadran "
                          f"(activos ≠ pasivos + patrimonio)")
        if divergencias:
            fallas.append(f"{etiqueta}: {divergencias} identidades del estado de resultados no se cumplen")
        # La compuerta del extractor se apaga si casi ningún balance es verificable: aquí se
        # detecta lo mismo sobre la historia, con el mismo umbral.
        if cuadratura.debe_detener(verificados, [], balances_totales=totales):
            fallas.append(f"{etiqueta}: solo {verificados} de {totales} balances son verificables "
                          f"({cobertura:.0%} < {cuadratura.COBERTURA_MINIMA:.0%}): "
                          "las glosas de los totales cambiaron y la cuadratura no alcanza a leerlas")

        if detalle:
            for h in hallazgos[:40]:
                print(f"  · {h}")
            if len(hallazgos) > 40:
                print(f"  · … y {len(hallazgos) - 40} más")

    print()
    print(f"{'Sector':<22}{'Balances':>9}{'Verificados':>13}{'Cobertura':>11}"
          f"{'Descuadres':>12}{'Identidades':>13}{'Divergencias':>14}")
    for etiqueta, totales, verificados, cobertura, desc, verif_res, div in resumen:
        print(f"{etiqueta:<22}{totales:>9}{verificados:>13}{cobertura:>10.1%}{desc:>12}"
              f"{verif_res:>13}{div:>14}")

    bal_t = sum(r[1] for r in resumen)
    bal_v = sum(r[2] for r in resumen)
    res_v = sum(r[5] for r in resumen)
    print()
    print(f"Total: {bal_v}/{bal_t} balances verificados ({bal_v / bal_t:.1%} · los que faltan no "
          f"traen los tres totales en la glosa de la fuente) · "
          f"{res_v} identidades de resultados comprobadas")

    if fallas:
        print()
        for f in fallas:
            print(f"FALLA {f}")
        return 1
    print("\nCuadratura IFRS: toda la historia publicada cuadra.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--detalle", action="store_true", help="lista cada balance o identidad que falla")
    a = ap.parse_args()
    return auditar(a.detalle)


if __name__ == "__main__":
    sys.exit(main())

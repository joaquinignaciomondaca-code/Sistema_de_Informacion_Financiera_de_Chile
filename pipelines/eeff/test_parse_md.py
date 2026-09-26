"""Prueba el parser con la Nota 4 real de Factoring Security (PDF marzo 2026)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff.parse_md import parse_documento
from pipelines.eeff.validate_api import cuadratura_balance

FIXTURE = """
rut: 96655860-1
razon_social: FACTORING SECURITY S.A.
periodo: 2026-03
fecha_corte: 2026-03-31
tipo_eeff: Individual
fuente: CMF PDF Estados financieros

## BALANCE
nombre|nota|monto_miles|comparativo_miles|clase
Efectivo y equivalentes al efectivo|4|11283111|29479668|Activo
Deudores comerciales y otras cuentas por cobrar|5|648223161|648194399|Activo
Total de activos||672356418|689514566|Total
Total de pasivos||551969169|570967223|Total
Patrimonio total||120387249|118547343|Total

## RESULTADOS
nombre|nota|monto_miles|comparativo_miles|clase
Ingresos de actividades ordinarias|18|16626587|13522787|Ingreso

## NOTAS_INDICE
4|Efectivo y Equivalentes al Efectivo|24
5|Deudores Comerciales y Otras Cuentas por Cobrar|26

## NOTA 4 Efectivo y equivalentes al efectivo
| | Saldo 31/03/2026 M$ | Saldo 31/12/2025 M$ |
| --- | --- | --- |
| Efectivo en caja | 4.240 | 4.240 |
| Fondos Mutuos | - | 15.003.881 |
| Saldos en bancos | 11.278.871 | 14.471.547 |
| Totales | 11.283.111 | 29.479.668 |
"""


def test_nota_efectivo_cuadra_con_balance():
    parsed = parse_documento(FIXTURE, {
        "rut": "96655860-1",
        "razon_social": "FACTORING SECURITY S.A.",
        "periodo": "2026-03",
        "fecha_corte": "2026-03-31",
        "tipo_eeff": "Individual",
        "fuente": "CMF PDF",
    })
    assert parsed["balance"], "el balance del MD no se leyó"
    efectivo = [r for r in parsed["balance"] if "efectivo" in r["nombre_cuenta"].lower()][0]
    assert efectivo["monto_miles_clp"] == 11283111
    notas = [r for r in parsed["notas"] if r["numero_nota"] == 4 and r["concepto"].lower() != "totales"]
    assert notas, "la tabla de la Nota 4 no se leyó"
    suma = round(sum(r["monto_miles_clp"] for r in notas), 2)
    assert suma == efectivo["monto_miles_clp"]
    cuadre = cuadratura_balance(parsed["balance"])
    assert cuadre["estado"] == "OK", cuadre
    print("OK nota 4 cuadra con el efectivo del PDF")
    security = (ROOT / "factoring_leasing" / "eeff_fuentes" / "96655860-1_2026-03.md").read_text(encoding="utf-8")
    parsed_sec = parse_documento(security, {
        "rut": "96655860-1",
        "razon_social": "FACTORING SECURITY S.A.",
        "periodo": "2026-03",
        "fecha_corte": "2026-03-31",
        "tipo_eeff": "Individual",
        "fuente": "CMF PDF",
    })
    nota5 = [r for r in parsed_sec["notas"] if r["numero_nota"] == 5 and r["concepto"].lower() != "totales"]
    assert nota5, "la Nota 5 no se leyó"
    neto = round(sum(r["monto_miles_clp"] for r in nota5), 2)
    deudores = [r for r in parsed_sec["balance"] if "deudores comerciales" in r["nombre_cuenta"].lower()][0]
    assert neto == deudores["monto_miles_clp"] == 648223161
    assert any("Colocación" in r["detalle"] for r in nota5)
    print("OK nota 5 neto cuadra con deudores del PDF")


if __name__ == "__main__":
    test_nota_efectivo_cuadra_con_balance()

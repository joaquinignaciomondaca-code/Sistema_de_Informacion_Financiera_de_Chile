"""Parser: la nota cuadra con la carátula y no vuelve a una bolsa."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff.parse_md import cargar_md, parse_documento
from pipelines.eeff.validate_api import cuadratura_balance, validar_documento

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
| | Saldo 31/12/2025 M$ | Saldo 31/03/2026 M$ |
| --- | --- | --- |
| Efectivo en caja | 4.240 | 4.240 |
| Fondos Mutuos | 15.003.881 | - |
| Saldos en bancos | 14.471.547 | 11.278.871 |
| Totales | 29.479.668 | 11.283.111 |
"""

META = {
    "rut": "96655860-1",
    "razon_social": "FACTORING SECURITY S.A.",
    "periodo": "2026-03",
    "fecha_corte": "2026-03-31",
    "tipo_eeff": "Individual",
    "fuente": "CMF PDF",
}


def test_nota_efectivo_cuadra_con_balance():
    parsed = parse_documento(FIXTURE, META)
    assert "notas" not in parsed
    assert parsed["balance"]
    efectivo = [r for r in parsed["balance"] if r["cuenta_canonica"] == "efectivo"][0]
    assert efectivo["monto_miles_clp"] == 11283111
    notas = [r for r in parsed["tablas"]["efectivo"] if not r["es_total"]]
    assert notas, "la tabla de la Nota 4 no se leyó"
    assert round(sum(r["saldo_miles"] for r in notas), 2) == efectivo["monto_miles_clp"]
    # La columna vieja va primera. El corte es marzo 2026, no la primera columna.
    assert notas[0]["saldo_miles"] == 4240
    assert notas[0]["saldo_comparativo_miles"] == 4240
    fondos = [r for r in notas if "fondos" in r["concepto"].lower()][0]
    assert fondos["saldo_miles"] == 0
    assert fondos["saldo_comparativo_miles"] == 15003881
    assert cuadratura_balance(parsed["balance"])["estado"] == "OK"
    vals = validar_documento(parsed["balance"], {
        "activos_liquidos_m_clp": 11283.11,
        "cartera_credito_m_clp": 648223.16,
        "total_activos_m_clp": 672356.42,
        "patrimonio_neto_m_clp": 120387.25,
    })
    assert {v["concepto"]: v["estado"] for v in vals}["efectivo"] == "OK"
    print("OK nota 4 cuadra con el efectivo del PDF, con las fechas en orden inverso")

    security = (ROOT / "factoring_leasing" / "eeff_fuentes" / "96655860-1_2026-03.md").read_text(encoding="utf-8")
    parsed_sec = parse_documento(security, META)
    nota5 = [r for r in parsed_sec["tablas"]["deudores"] if not r["es_total"]]
    assert nota5, "la Nota 5 no se leyó"
    neto = round(sum(r["neto_miles"] for r in nota5), 2)
    deudores = [r for r in parsed_sec["balance"] if r["cuenta_canonica"] == "deudores"][0]
    assert neto == deudores["monto_miles_clp"] == 648223161
    factura = nota5[0]
    assert factura["colocacion_miles"] == 519162626
    assert factura["provision_miles"] == 1166520
    assert factura["neto_miles"] == 517996106
    assert parsed_sec["tablas"]["deudores"][-1]["es_total"] == 1
    print("OK nota 5 neto cuadra con deudores del PDF")


def test_eurocapital_no_inventa_la_nota():
    path = ROOT / "factoring_leasing" / "eeff_fuentes" / "96861280-8_2026-03.md"
    meta, text = cargar_md(path)
    parsed = parse_documento(text, meta)
    assert parsed["tablas"]["efectivo"] == []
    assert parsed["tablas"]["deudores"] == []
    assert parsed["pendientes"] == []
    deudores = [r for r in parsed["balance"] if r["cuenta_canonica"] == "deudores"][0]
    assert deudores["monto_miles_clp"] == 232162009
    vals = validar_documento(parsed["balance"], {
        "cartera_credito_m_clp": 232162.01,
        "activos_liquidos_m_clp": 6117.08,
        "total_activos_m_clp": 290187.61,
        "pasivos_corrientes_m_clp": 1,
        "pasivos_no_corrientes_m_clp": 1,
        "patrimonio_neto_m_clp": 52213.93,
    })
    por_concepto = {v["concepto"]: v for v in vals}
    assert por_concepto["deudores_corrientes"]["estado"] == "OK", por_concepto["deudores_corrientes"]
    assert por_concepto["pasivos_corrientes"]["estado"] == "SOLO_API"
    print("OK Eurocapital no inventa la nota y la carátula con «corrientes» sí se lee")


if __name__ == "__main__":
    test_nota_efectivo_cuadra_con_balance()
    test_eurocapital_no_inventa_la_nota()

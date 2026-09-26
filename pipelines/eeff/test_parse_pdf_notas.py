"""Notas: el total que se guarda es el de la cara. Sin red."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipelines.eeff.parse_pdf_notas import (
    composicion_en_tablas,
    composicion_que_calza,
    extraer_notas,
    indice_notas,
)

PAGINA = """
NOTA 4 – EFECTIVO Y EQUIVALENTES AL EFECTIVO
La composición es la siguiente:
Efectivo en caja 4.240 4.240
Fondos Mutuos - 15.003.881
Saldos en bancos 11.278.871 14.471.547
Totales 11.283.111 29.479.668
a) Otra apertura que no es la cara
Totales 99.999 1
"""

PPE = """
NOTA 11 – PROPIEDADES, PLANTA Y EQUIPO
Muebles 87.785 (39.562) 48.223
Instalaciones 26.001 (24.842) 1.159
Totales 113.786 (64.404) 49.382
"""

TABLA = [
    ["", "31-03-2026", "31-12-2025"],
    ["Facturas por pagar", "116.588", "182.905"],
    ["Cuentas por pagar a clientes", "4.584.892", "4.310.247"],
    ["Totales", "4.701.480", "4.493.152"],
]


def test_indice_no_usa_el_numero_como_nombre():
    indice = indice_notas([
        "Nota 13 – Préstamos que devengan intereses 37\nNota 14 – Cuentas por pagar comerciales 38\n"
        "Nota 4 – Efectivo y equivalentes al efectivo 22\nNota 5 – Deudores comerciales 22\n",
        "NOTA 13 – OTROS PASIVOS FINANCIEROS\nEl detalle\n",
    ])
    por_numero = {fila["numero"]: fila for fila in indice}
    assert por_numero[13]["familia"] == "pasivos_financieros"
    assert por_numero[13]["en_indice"] is True
    assert por_numero[4]["familia"] == "efectivo"


def test_efectivo_calza_y_no_toma_el_total_posterior():
    comp = composicion_que_calza(PAGINA, 11283111)
    assert comp is not None
    assert comp["total"] == 11283111
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 11283111
    assert all(f["monto_miles"] != 99999 for f in comp["filas"])


def test_ppe_usa_la_columna_neto():
    comp = composicion_que_calza(PPE, 49382)
    assert comp is not None
    assert comp["total"] == 49382
    assert comp["filas"][0]["concepto"] == "Muebles"
    assert comp["filas"][0]["monto_miles"] == 48223


def test_montos_apilados_calzan():
    texto = """
NOTA 4 – EFECTIVO Y EQUIVALENTES AL EFECTIVO
Efectivo en caja
4.240
4.240
Fondos Mutuos
-
15.003.881
Saldos en bancos
11.278.871
14.471.547
Totales
11.283.111
29.479.668
"""
    comp = composicion_que_calza(texto, 11283111)
    assert comp is not None
    assert [f["concepto"] for f in comp["filas"] if not f["es_total"]] == [
        "Efectivo en caja", "Fondos Mutuos", "Saldos en bancos",
    ]
    assert comp["filas"][1]["monto_miles"] == 0


def test_no_inventa_si_no_calza():
    assert composicion_que_calza(PAGINA, 1) is None


def test_tabla_pdf():
    comp = composicion_en_tablas([TABLA], 4701480)
    assert comp is not None
    assert comp["total"] == 4701480
    assert len([f for f in comp["filas"] if not f["es_total"]]) == 2


def test_extraer_marca_lo_que_no_lee():
    balance = [
        {"nombre_cuenta": "Efectivo y equivalentes al efectivo", "nota_ref": "4", "monto_miles_clp": 11283111},
        {"nombre_cuenta": "Deudores comerciales y otras cuentas por cobrar", "nota_ref": "5", "monto_miles_clp": 100},
    ]
    salida = extraer_notas([PAGINA], None, balance, {"rut": "1", "periodo": "2026-03"})
    estados = {fila["cuenta"]: fila["estado"] for fila in salida["cuadre"]}
    assert estados["efectivo"] == "OK"
    assert estados["deudores"] == "NO_LEIDA"
    conceptos = [f["concepto"] for f in salida["tablas"]["efectivo"]]
    assert conceptos[0] == "Efectivo en caja"
    assert "NOTA 4" not in conceptos[0]

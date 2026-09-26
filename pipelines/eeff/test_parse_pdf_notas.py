"""Notas: el total que se guarda es el de la cara. Sin red."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipelines.eeff.parse_pdf_notas import (
    _montos,
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


def test_nota_partida_en_dos_lineas():
    indice = indice_notas([
        "NOTA 5\nEFECTIVO Y EQUIVALENTES AL EFECTIVO\n"
        "NOTA 6\nDEUDORES COMERCIALES Y OTRAS CUENTAS POR COBRAR\n"
        "NOTA 7\nCUENTAS POR COBRAR A ENTIDADES RELACIONADAS\n"
        "NOTA 8\nOTROS ACTIVOS NO FINANCIEROS\n"
    ])
    por_numero = {fila["numero"]: fila for fila in indice}
    assert por_numero[5]["familia"] == "efectivo"
    assert por_numero[6]["familia"] == "deudores"


def test_una_oracion_no_es_titulo_de_nota():
    indice = indice_notas([
        "5. Con fecha 27 de noviembre de 2025 se celebró sesión Extraordinaria de Directorio\n"
    ])
    assert indice == []


def test_no_toma_un_miles_como_nota():
    indice = indice_notas([
        "3.300 nuevas acciones de Factotal S.A. provenientes de la fusión por cada una\n"
    ])
    assert indice == []


def test_subtotales_calzan_cuando_el_detalle_esta_anidado():
    texto = """
NOTA 3 - Efectivo y Equivalentes al Efectivo
Efectivo en caja
Factotal S.A.
Pesos
1.770
1.770
Efectivo en caja
Procesos y Servicios Ltda.
Pesos
1.000
1.000
Subtotal Efectivo en Caja
2.770
2.770
Bancos
Factotal S.A.
Pesos
3.000
3.000
Subtotal Bancos
3.000
3.000
Total
5.770
5.770
"""
    comp = composicion_que_calza(texto, 5770)
    assert comp is not None
    assert comp["total"] == 5770
    conceptos = [f["concepto"] for f in comp["filas"] if not f["es_total"]]
    assert conceptos == [
        "Efectivo en caja — Factotal S.A.",
        "Efectivo en caja — Procesos y Servicios Ltda.",
        "Bancos — Factotal S.A.",
    ]
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 5770


def test_puente_bruto_neto_usa_los_subtotales():
    texto = """
NOTA 4 - Deudores Comerciales y otras Cuentas por Cobrar
Deudores por operaciones de Factoring (bruto)
78.451.176
91.360.046
Provisión por deterioro
(5.850.051)
(5.942.231)
Deudores por operaciones de Factoring (neto)
72.601.125
85.417.815
Total Deudores comerciales, Neto, Corriente
72.601.125
85.417.815
Cuentas por cobrar comerciales
2.205.914
1.747.354
Total Cuentas por cobrar comerciales
2.205.914
1.747.354
Total Deudores y Cuentas por cobrar, Neto, Corriente
74.807.039
87.165.169
"""
    comp = composicion_que_calza(texto, 74807039)
    assert comp is not None
    assert [f["concepto"] for f in comp["filas"] if not f["es_total"]] == [
        "Total Deudores comerciales, Neto, Corriente",
        "Total Cuentas por cobrar comerciales",
    ]


def test_signo_peso_no_parte_la_fila():
    texto = """
(8) Efectivo y equivalentes al efectivo
Bancos
$
36.070
40.983
Fondos Mutuos (a)
$
-
7.023
Total efectivo y equivalentes al efectivo
36.070
48.006
"""
    comp = composicion_que_calza(texto, 36070)
    assert comp is not None
    assert [f["concepto"] for f in comp["filas"] if not f["es_total"]] == ["Bancos", "Fondos Mutuos (a)"]
    assert comp["filas"][0]["monto_miles"] == 36070


def test_un_rut_no_es_un_miles():
    assert _montos("77.124.030-5 Inversiones Lauca Ltda. 2.632.619") == [2632619.0]
    assert 15642382.0 not in _montos("15.642.382-K")


def test_una_frase_con_monto_no_ensucia_la_composicion():
    texto = """
NOTA 5 - EFECTIVO Y EQUIVALENTES AL EFECTIVO
El flujo alcanzó a M$41.636.806, en comparación con M$20.580.904 en igual período del año anterior.
Saldos en bancos
1.730.440
2.817.192
Fondos fijos
3.082
2.519
Fondos mutuos
10.478
47.321
Totales
1.744.000
2.867.032
"""
    comp = composicion_que_calza(texto, 1744000)
    assert comp is not None
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 1744000
    assert all("comparaci" not in f["concepto"].lower() for f in comp["filas"])


def test_una_fecha_no_es_un_miles():
    texto = """
NOTA 6 - Efectivo y Equivalente al Efectivo
Conceptos
31.03.2026
31.12.2025
M$
M$
Cuentas Corrientes Bancarias
938.680
2.149.523
Inversión en Fondos Mutuos
4.940.977
-
Total
5.879.657
2.149.523
"""
    comp = composicion_que_calza(texto, 5879657)
    assert comp is not None
    assert [f["concepto"] for f in comp["filas"] if not f["es_total"]] == [
        "Cuentas Corrientes Bancarias", "Inversión en Fondos Mutuos",
    ]


def test_monto_menor_a_mil_no_se_pierde():
    texto = """
NOTA 7 - Efectivo y equivalentes al efectivo
Efectivo en caja
350
350
Cuentas corrientes bancarias
1.118.003
1.271.026
Fondos Mutuos
50.932
50.932
Total, efectivo y equivalentes al efectivo
1.169.285
1.322.308
"""
    comp = composicion_que_calza(texto, 1169285)
    assert comp is not None
    assert [f["concepto"] for f in comp["filas"] if not f["es_total"]] == [
        "Efectivo en caja", "Cuentas corrientes bancarias", "Fondos Mutuos",
    ]
    assert comp["filas"][0]["monto_miles"] == 350


def test_parentesis_con_espacio_es_negativo():
    texto = """
NOTA 6 - Deudores Comerciales y otras Cuentas por Cobrar
Documentos y otras cuentas por cobrar
3.433.090
3.355.211
Provision Incobrable
(203.199 )
(203.199 )
Total
3.229.891
3.152.012
"""
    comp = composicion_que_calza(texto, 3229891)
    assert comp is not None
    assert comp["filas"][1]["monto_miles"] == -203199
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 3229891


def test_una_sola_clase_de_activo_calza():
    texto = """
NOTA 12 - Activos intangibles
Programas informáticos
30.482
29.008
28.348
27.870
2.134
1.138
Total activos intangibles
30.482
29.008
28.348
27.870
2.134
1.138
"""
    comp = composicion_que_calza(texto, 2134)
    assert comp is not None
    assert comp["filas"][0]["concepto"] == "Programas informáticos"
    assert comp["filas"][0]["monto_miles"] == 2134


def test_no_acepta_el_encabezado_como_unica_partida():
    texto = """
Concepto
47.392
47.392
Total
47.392
47.392
"""
    assert composicion_que_calza(texto, 47392) is None


def test_el_guion_del_nombre_no_borra_el_monto():
    texto = """
NOTA 15 PASIVOS FINANCIEROS
Préstamos bancarios
66.724.259
Emisión de Notas - Gramercy (*)
39.485.866
Obligaciones con el publico
4.504.784
Total
110.714.909
"""
    comp = composicion_que_calza(texto, 110714909)
    assert comp is not None
    assert any("Gramercy" in f["concepto"] for f in comp["filas"])
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 110714909


def test_la_sociedad_es_la_partida_de_relacionadas():
    texto = """
NOTA 7 CUENTAS POR COBRAR Y POR PAGAR A ENTIDADES RELACIONADAS
Corrientes
No corrientes
Recfin SpA.
1.689.086
-
Inmobiliaria IV Centenario S.A.
440
-
Klym S.A.S (1)
3.524.986
-
Otros (2)
32.482
-
Total
5.246.994
12.249
"""
    comp = composicion_que_calza(texto, 5246994)
    assert comp is not None
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 5246994


def test_una_llamada_no_corta_la_nota_antes_de_la_tabla():
    from pipelines.eeff.parse_pdf_notas import secciones

    secs = secciones([
        "19.- Otros pasivos no financieros y Provisiones por beneficio a los empleados\nEl detalle.\n(2) Dividendos mínimos\n",
        "20.- Arrendamiento\nProvisión Total, Saldo Inicial 01-01-2026\n574.657\nProvisiones nuevas\n87.864\nProvisión Utilizada\n(144.703)\nProvisión Total, Saldo Final 31-03-2026\n517.818\n",
    ])
    assert all(sec["numero"] != 2 for sec in secs)
    nota = next(sec for sec in secs if sec["numero"] == 19)
    assert "517.818" in nota["texto"]
    comp = composicion_que_calza(nota["texto"], 517818)
    assert comp is not None
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 517818


def test_la_nota_al_pie_no_abre_otra_nota():
    from pipelines.eeff.parse_pdf_notas import secciones

    secs = secciones([
        "NOTA 7 CUENTAS POR COBRAR Y POR PAGAR A ENTIDADES RELACIONADAS\nEl detalle.\n",
        "Recfin SpA.\n5.790.928\nTotal\n5.790.928\n(2) Corresponde a cuentas por cobrar a ejecutivos principales de la compañía.\n",
    ])
    assert all(sec["numero"] != 2 for sec in secs)
    nota = next(sec for sec in secs if sec["numero"] == 7)
    assert "5.790.928" in nota["texto"]


def test_el_numero_de_pagina_no_es_otra_columna():
    texto = """
NOTA 14 ACTIVOS INTANGIBLES
Importe neto al 31/03/2026
968.758
152.895
1.121.653
67
"""
    comp = composicion_que_calza(texto, 1121653)
    assert comp is not None
    partes = [f for f in comp["filas"] if not f["es_total"]]
    assert [f["monto_miles"] for f in partes] == [968758, 152895]


def test_las_clases_de_la_misma_fila_suman_el_neto():
    texto = """
NOTA 14 ACTIVOS INTANGIBLES
Importe neto al 31/03/2026
968.758
152.895
1.121.653
"""
    comp = composicion_que_calza(texto, 1121653)
    assert comp is not None
    partes = [f for f in comp["filas"] if not f["es_total"]]
    assert len(partes) == 2
    assert sum(f["monto_miles"] for f in partes) == 1121653


def test_la_linea_de_la_cuenta_cierra_aunque_no_diga_total():
    texto = """
NOTA 13 - Impuesto a las ganancias
Otros impuestos
197.722
Impuesto AT ejercicio anterior
7.053
Remanente
896.052
Activo por impuestos corrientes
1.100.827
"""
    comp = composicion_que_calza(texto, 1100827)
    assert comp is not None
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 1100827


def test_el_ultimo_saldo_chico_antes_del_total_no_se_pierde():
    texto = """
NOTA 17 - Cuentas por pagar a entidades relacionadas
Inversiones Lauca Ltda.
Chile
7.160.848
Matías Bonet Cabrera
Chile
104
Total
7.160.952
"""
    comp = composicion_que_calza(texto, 7160952)
    assert comp is not None, "el 104 de la última fila tiene que entrar"
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 7160952


def test_un_miles_chico_en_la_misma_linea_no_se_pierde():
    texto = """
NOTA 17 - Saldos con partes relacionadas
Inversiones Lauca Ltda. Chile 2.632.619
Matías Bonet Cabrera Chile 104
Total 7.160.952
"""
    assert _montos("Matías Bonet Cabrera Chile 104") == [104.0]
    assert _montos("77.124.030-5 Inversiones Lauca Ltda. 2.632.619") == [2632619.0]
    comp = composicion_que_calza(
        """
NOTA 17 - Cuentas por pagar a entidades relacionadas
Inversiones Lauca Ltda. Chile 7.160.848
Matías Bonet Cabrera Chile 104
Total 7.160.952
""",
        7160952,
    )
    assert comp is not None
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 7160952


def test_dos_lineas_de_la_cara_no_se_suman():
    from pipelines.eeff.parse_pdf_notas import objetivos_cara

    balance = [
        {"nombre_cuenta": "Deudores comerciales y otras cuentas por cobrar", "nota_ref": "11", "monto_miles_clp": 67134136, "clase": "Activo"},
        {"nombre_cuenta": "Deudores comerciales y otras cuentas por cobrar", "nota_ref": "11", "monto_miles_clp": 98804906, "clase": "Activo"},
    ]
    objetivos = objetivos_cara(balance)
    assert [fila["monto_miles"] for fila in objetivos] == [67134136, 98804906]


def test_el_subtotal_toma_solo_las_partidas_de_arriba():
    texto = """
NOTA 18 - Impuestos
Saldo final de otra tabla
2.148.441
Impuesto a la renta
(167.516)
Pagos provisionales mensuales
890.913
Subtotal activos corrientes
723.397
"""
    comp = composicion_que_calza(texto, 723397)
    assert comp is not None
    assert [f["concepto"] for f in comp["filas"] if not f["es_total"]] == [
        "Impuesto a la renta",
        "Pagos provisionales mensuales",
    ]


def test_el_saldo_final_suma_el_movimiento_no_el_subtotal_dos_veces():
    texto = """
NOTA 19 - Provisiones por beneficios a los empleados
Provisión Vacaciones personal
517.817
574.657
Provisión Total, Saldo Inicial 01-01-2026
574.657
593.703
Provisiones nuevas
87.864
366.888
Provisión Utilizada
(144.703)
(385.934)
Cambios en Provisiones , Total
(56.839)
(19.046)
Provisión Total, Saldo Final 31-03-2026
517.818
574.657
"""
    comp = composicion_que_calza(texto, 517818)
    assert comp is not None
    partes = [f for f in comp["filas"] if not f["es_total"]]
    assert [f["monto_miles"] for f in partes] == [574657, 87864, -144703]
    assert sum(f["monto_miles"] for f in partes) == 517818


def test_las_columnas_antes_del_total_suman_la_linea():
    texto = """
Nota 25 - Segmentos Operativos
Factoring
Leasing
Créditos
Eliminaciones
/Otros
Total
Al 31 de marzo de 2026 y 31 de diciembre de 2025
Otros pasivos financieros no corrientes
55.477.352
-
1.751.870
-
57.229.222
59.863.645
"""
    comp = composicion_que_calza(texto, 57229222)
    assert comp is not None
    partes = [f for f in comp["filas"] if not f["es_total"]]
    assert [f["concepto"] for f in partes] == ["Factoring", "Leasing", "Créditos", "Eliminaciones/Otros"]
    assert sum(f["monto_miles"] for f in partes) == 57229222


def test_la_columna_corrida_por_un_cero_sigue_sumando():
    texto = """
NOTA 16 - Otros pasivos no financieros
Fondo III cuota R
-
20.525.825
20.528.176
Fondo III cuota C
-
(811.095)
(828.868)
Fondo III cuota I
-
9.571.081
9.572.272
Provision Riesgo
40.575
33.119
EF Securitizadora
1.249.956
887.168
Total
30.576.342
30.065.113
"""
    comp = composicion_que_calza(texto, 30576342)
    assert comp is not None
    assert sum(f["monto_miles"] for f in comp["filas"] if not f["es_total"]) == 30576342
    assert any(f["monto_miles"] == -811095 for f in comp["filas"])


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

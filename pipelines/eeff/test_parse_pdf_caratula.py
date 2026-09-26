"""Parser de carátula, sin red. Una tabla sintética y una página en texto."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipelines.eeff.parse_pdf_caratula import (
    clasificar_pagina,
    fold,
    lineas_apiladas,
    lineas_caidas,
    lineas_de_tabla,
    lineas_de_texto,
    orden_montos,
)
from pipelines.eeff.validate_api import cuadratura_balance, cuadratura_resultados

META = {"rut": "99501480-7", "razon_social": "PENTA", "periodo": "2026-03", "tipo_eeff": "Consolidado"}

TABLA = [
    ["", "Nota", "31.03.2026 M$", "31.12.2025 M$"],
    ["Activos", "", "", ""],
    ["Efectivo y equivalentes al efectivo", "6", "1.164.717", "925.415"],
    ["Deudores comerciales y otras cuentas por cobrar corrientes", "7", "189.005.473", "193.000.377"],
    ["Total activos corrientes", "", "199.551.164", "202.841.842"],
    ["Total activos no corrientes", "", "53.361.684", "50.219.345"],
    ["Total activos", "", "252.912.848", "253.061.187"],
    ["Total pasivos corrientes", "", "191.485.053", "193.160.693"],
    ["Total pasivos no corrientes", "", "7.308.352", "7.340.322"],
    ["Total pasivos", "", "198.793.405", "200.501.015"],
    ["Capital pagado", "20", "11.874.585", "11.874.586"],
    ["Total patrimonio", "", "54.119.443", "52.560.172"],
]


def test_el_salto_despues_del_monto_no_abre_otra_cuenta():
    texto = """
Estados de Situación Financiera
Total de activos corrientes distintos de los activos o grupos
133.642.225
141.017.468
de activos para su disposición clasificados como mantenidos para
la venta o como mantenidos para distribuir a los propietarios
Activos corrientes o grupos de activos para su disposición
(10)
293.797
834.139
clasificados como mantenidos para la venta
Total activo corriente
133.936.022
141.851.607
Patrimonio atribuible a los propietarios
48.808.633
47.530.732
de la controladora
Interés no controlador
(16)
377.704
393.542
"""
    lineas = lineas_apiladas(texto, "balance", META)
    nombres = [row["nombre_cuenta"] for row in lineas]
    assert not any(nombre[:1].islower() for nombre in nombres), nombres
    assert any(
        nombre.startswith("Total de activos corrientes") and nombre.endswith("propietarios")
        for nombre in nombres
    )
    venta = next(row for row in lineas if row["nombre_cuenta"].startswith("Activos corrientes o grupos"))
    assert venta["nombre_cuenta"].endswith("venta")
    assert venta["monto_miles_clp"] == 293797
    assert venta["nota_ref"] == "10"
    assert "Total activo corriente" in nombres
    assert any(nombre.startswith("Patrimonio atribuible") and nombre.endswith("controladora") for nombre in nombres)
    assert "Interés no controlador" in nombres


def test_plusvalia_con_nota_en_el_nombre_no_es_caida():
    elegidas = [{"nombre_cuenta": "Plusvalía", "monto_miles_clp": 1629466.0}]
    otras = [{"nombre_cuenta": "Plusvalía (12)", "monto_miles_clp": 1629466.0}]
    assert lineas_caidas(elegidas, otras) == []


def test_la_nota_pegada_al_nombre_no_es_parte_de_la_cuenta():
    lineas = lineas_de_tabla(
        [["Activos por impuestos diferidos 17.1", "405.805", "468.707"]],
        "balance",
        META,
        "corte_primero",
    )
    assert lineas[0]["nombre_cuenta"] == "Activos por impuestos diferidos"
    assert lineas[0]["nota_ref"] == "17"
    assert lineas[0]["monto_miles_clp"] == 405805


def test_una_linea_de_indice_no_es_cara_caida():
    elegidas = [{"nombre_cuenta": "Efectivo y equivalentes al efectivo", "monto_miles_clp": 36.0}]
    otras = elegidas + [
        {"nombre_cuenta": "Ingresos financieros", "monto_miles_clp": 21.0},
        {"nombre_cuenta": "Nota 2 - Criterios contables aplicados", "monto_miles_clp": 3.0},
        {"nombre_cuenta": "Índice Página", "monto_miles_clp": 1.0},
    ]
    caidas = lineas_caidas(elegidas, otras)
    assert [fila["nombre_cuenta"] for fila in caidas] == ["Ingresos financieros"]


def test_tabla_cierra_y_no_inventa():
    assert orden_montos(TABLA, "2026-03") == "corte_primero"
    lineas = lineas_de_tabla(TABLA, "balance", META, "corte_primero")
    nombres = [row["nombre_cuenta"] for row in lineas]
    assert "Activos" not in nombres
    assert any(row["nombre_cuenta"].startswith("Efectivo") and row["monto_miles_clp"] == 1164717 for row in lineas)
    cuadre = cuadratura_balance(lineas)
    assert cuadre["estado"] == "OK", cuadre
    assert abs(cuadre["diff_m_clp"]) <= 1


def test_comparativo_primero_no_se_deja_al_reves():
    tabla = [
        ["", "31.12.2025", "31.03.2026"],
        ["Total activos", "253.061.187", "252.912.848"],
        ["Total pasivos", "200.501.015", "198.793.405"],
        ["Total patrimonio", "52.560.172", "54.119.443"],
    ]
    assert orden_montos(tabla, "2026-03") == "comparativo_primero"
    lineas = lineas_de_tabla(tabla, "balance", META, "comparativo_primero")
    activos = next(row for row in lineas if row["nombre_cuenta"] == "Total activos")
    assert activos["monto_miles_clp"] == 252912848
    assert activos["monto_comparativo_miles_clp"] == 253061187


def test_apilado_como_sale_el_pdf():
    texto = """
PENTA FINANCIERO S.A. Y FILIALES
Estados de Situación Financiera Consolidados
31 de marzo de 2026 y 31 de diciembre de 2025
(Expresado en miles de pesos - M$)
Efectivo y equivalentes al efectivo
(6)
 1.164.717
 925.415
Deudores comerciales y otras cuentas por cobrar
(7)
 189.005.473  193.000.377
Total, activos corrientes
199.551.164
202.841.842
Total, activos no corrientes
53.361.684
50.219.345
Total, Activos
252.912.848
253.061.187
Total, pasivos corrientes
191.485.053
193.160.693
Total, pasivos no corrientes
7.308.352
7.340.322
Total, Pasivos
198.793.405
200.501.015
Total patrimonio
54.119.443
52.560.172
"""
    assert clasificar_pagina(texto) == "balance"
    lineas = lineas_apiladas(texto, "balance", META)
    efectivo = next(row for row in lineas if row["nombre_cuenta"].startswith("Efectivo"))
    assert efectivo["nota_ref"] == "6"
    assert efectivo["monto_miles_clp"] == 1164717
    assert cuadratura_balance(lineas)["estado"] == "OK"


def test_encabezado_notas_y_anio_no_es_linea():
    texto = """
Estados Intermedios de Situación Financiera Consolidados
Activos
Notas
2026
2025
M$
M$
Activos corrientes:
Efectivo y equivalentes al efectivo
7
1.169.285
1.322.308
Total activos corrientes
48.332.431
48.932.458
"""
    lineas = lineas_apiladas(texto, "balance", META)
    assert [row["nombre_cuenta"] for row in lineas] == [
        "Efectivo y equivalentes al efectivo",
        "Total activos corrientes",
    ]
    assert lineas[0]["monto_miles_clp"] == 1169285


def test_api_con_monto_vacio_no_revienta():
    from pipelines.eeff.validate_api import validar_documento
    lineas = lineas_apiladas("""
Estados de Situación Financiera
Total activos
10.000
9.000
""", "balance", META)
    vals = validar_documento(lineas, {"total_activos_m_clp": None, "rut": "1-9"})
    assert any(row["concepto"] == "total_activos" and row["estado"] == "SIN_API" for row in vals)


def test_dos_montos_pegados_no_son_un_numero():
    from pipelines.eeff.parse_pdf_caratula import _montos_de_linea
    from pipelines.eeff.canon import parse_monto_chileno

    assert parse_monto_chileno("324.875.184542.645") is None
    assert _montos_de_linea("324.875.184542.645") == [324875184.0, 542645.0]


def test_nota_con_punto_y_parentesis_no_es_monto():
    comercial = """
Estados de Resultados Integrales
Ingresos de actividades ordinarias
20.1
8.169.520
6.209.315
Costo de ventas
20.2
(2.931.088)
(2.804.271)
Ganancia bruta
5.238.432
3.405.044
"""
    lineas = lineas_apiladas(comercial, "resultado", META)
    assert lineas[0]["monto_miles_clp"] == 8169520
    assert lineas[0]["nota_ref"] == "20"
    assert cuadratura_resultados(lineas)["estado"] == "OK"

    unidad = """
Estados de Resultados Integrales
Ingresos de actividades ordinarias
21.062.625
10.246.766
Costo de ventas
(18) (19.824.881)
(9.115.872)
Margen bruto
1.237.744
1.130.894
"""
    lineas = lineas_apiladas(unidad, "resultado", META)
    assert lineas[1]["monto_miles_clp"] == -19824881
    assert cuadratura_resultados(lineas)["estado"] == "OK"

    progreso = """
Estados de resultados
Ingresos de actividades ordinarias
23
7.053.707
7.135.080
Costo de ventas
( 1.948.722)
( 2.053.239)
Ganancia bruta
5.104.985
5.081.841
"""
    lineas = lineas_apiladas(progreso, "resultado", META)
    assert lineas[0]["monto_miles_clp"] == 7053707
    assert lineas[1]["monto_miles_clp"] == -1948722
    assert cuadratura_resultados(lineas)["estado"] == "OK"


def test_desglose_de_la_linea_padre_no_se_suma_dos_veces():
    hlc = """
Estados de Resultados Integrales
Ingresos de actividades ordinarias
9.091
8.758
Otros ingresos
9.091
8.758
Costo de Ventas
(35.702)
(36.036)
Remuneraciones
(35.702)
(33.602)
Gastos por recaudación de arriendos
0
(2.434)
Ganancia bruta
(26.611)
(27.278)
"""
    lineas = lineas_apiladas(hlc, "resultado", META)
    assert cuadratura_resultados(lineas)["estado"] == "OK"


def test_resultado_no_suma_dos_veces_ni_se_come_el_cero():
    autofin = """
Estados de Resultados Integrales
Utilidad (Pérdida)
Ingresos
20.a
25.304.795
20.706.428
Gastos por intereses
20.b
(5.374.884)
(4.366.281)
Ingreso neto
19.929.911
16.340.147
"""
    lineas = lineas_apiladas(autofin, "resultado", META)
    assert lineas[0]["nombre_cuenta"] == "Ingresos"

    forum = """
Estados de Resultados Integrales
Ganancias que surgen de la baja en cuentas de activos financieros
0
0
Gasto de administración
21
(19.788.099)
(18.045.200)
"""
    forum_lineas = lineas_apiladas(forum, "resultado", META)
    assert forum_lineas[0]["monto_miles_clp"] == 0
    assert forum_lineas[1]["nombre_cuenta"] == "Gasto de administración"

    tanner = """
Estados de Resultados
Pérdidas por deterioro
29
(5.635.331)
(7.394.496)
Costos financieros
-
(92.657)
(89.839)
Resultado por unidades de reajuste
-
723
803
Utilidad antes de Impuesto
(5.727.265)
(7.483.532)
"""
    tanner_lineas = lineas_apiladas(tanner, "resultado", META)
    costos = next(row for row in tanner_lineas if row["nombre_cuenta"] == "Costos financieros")
    assert costos["monto_miles_clp"] == -92657
    assert costos["monto_comparativo_miles_clp"] == -89839
    assert cuadratura_resultados(tanner_lineas)["estado"] == "OK"

    security = lineas_apiladas(
        """
Estados de Resultados
Ingresos de actividades ordinarias
10.000
8.000
Costo de ventas
(4.000)
(3.000)
Ganancia bruta
6.000
5.000
Ganancia procedente de operaciones continuadas
6.000
5.000
Ganancia del periodo
6.000
5.000
""",
        "resultado",
        META,
    )
    assert cuadratura_resultados(security)["estado"] == "OK"


def test_el_resultado_integral_se_guarda_y_no_rompe_la_utilidad():
    texto = """
Estados de Resultados Integrales
Ingresos de actividades ordinarias
10.000
8.000
Costo de ventas
(4.000)
(3.000)
Ganancia bruta
6.000
5.000
Ganancia del periodo
6.000
5.000
Ganancias por acción
1.500
1.200
Coberturas de flujo de efectivo
100
80
Otro resultado integral
100
80
Resultado integral total
6.100
5.080
"""
    lineas = lineas_apiladas(texto, "resultado", META)
    nombres = [fold(row["nombre_cuenta"]) for row in lineas]
    assert any("por accion" in nombre for nombre in nombres)
    assert any("cobertura" in nombre for nombre in nombres)
    assert any("resultado integral" in nombre for nombre in nombres)
    assert cuadratura_resultados(lineas)["estado"] == "OK"


def test_security_no_suma_el_subtotal_ni_toma_el_tramo_como_total():
    from pipelines.eeff.validate_api import cuadratura_detalle

    def fila(nombre, miles, clase="Cuenta"):
        return {
            "nombre_cuenta": nombre,
            "clase": clase,
            "monto_miles_clp": miles,
            "monto_m_clp": miles / 1000.0,
        }

    lineas = [
        fila("Efectivo y equivalentes al efectivo", 5200231, "Activo"),
        fila("Otros activos no financieros", 355636),
        fila("Deudores comerciales y otras cuentas por cobrar", 358043835, "Activo"),
        fila("Cuentas por cobrar a entidades relacionadas", 5190984),
        fila("Activos por impuestos", 592563),
        fila("Activos distintos de los activos o grupos de activos para su disposición", 369383249),
        fila("Activos no corrientes o grupos de activos para su disposición clasificados como mantenidos para la venta", 280961, "Activo no corriente"),
        fila("Total activos corrientes", 369664210, "Activo"),
        fila("Otros activos no financieros", 529255),
        fila("Inversiones contabilizadas utilizando el método de la participación", 42),
        fila("Activos intangibles distintos de la plusvalía", 1197853),
        fila("Propiedades, planta y equipo", 246595),
        fila("Activos por derecho de uso", 74821),
        fila("Activos por impuestos diferidos", 2735441),
        fila("Total activos no corrientes", 4784007, "Activo no corriente"),
        fila("TOTAL ACTIVOS", 374448217, "Total"),
        fila("Otros pasivos financieros", 221191991, "Pasivo"),
        fila("Pasivos por arrendamientos corrientes", 77811, "Pasivo"),
        fila("Cuentas por pagar comerciales y otras cuentas por pagar", 4811212),
        fila("Otras provisiones", 1342058),
        fila("Pasivos por impuestos corrientes", 0, "Pasivo"),
        fila("Provisiones por beneficios a los empleados", 341995),
        fila("Otros pasivos no financieros", 4026273, "Pasivo"),
        fila("Total pasivos corrientes", 231791340, "Pasivo"),
        fila("Otros pasivos financieros no corrientes", 84518970, "Pasivo"),
        fila("Total pasivos", 84518970, "Total"),
        fila("Capital emitido", 15217695, "Patrimonio"),
        fila("Ganancias acumuladas", 42920212, "Patrimonio"),
        fila("Otras reservas", 0, "Patrimonio"),
        fila("Patrimonio neto total", 58137907, "Patrimonio"),
        fila("TOTAL PATRIMONIO Y PASIVOS", 374448217, "Total"),
    ]
    assert cuadratura_detalle(lineas)["estado"] == "OK"
    assert cuadratura_balance(lineas)["estado"] == "OK"


def test_texto_y_titulo():
    assert clasificar_pagina("Nota 6 - Efectivo\nEstado de situación financiera\n1.164.717\n925.415\n252.912.848") == ""
    assert clasificar_pagina("Estado de Situación Financiera\nAl 31 de marzo de 2026") == ""
    texto = "\n".join([
        "Estado de Resultados",
        "Ingreso de actividades ordinarias 21 6.866.723 7.008.242",
        "Costo de ventas 22 (2.702.777) (3.114.462)",
        "Ganancia bruta 4.163.946 3.893.780",
    ])
    lineas = lineas_de_texto(texto, "resultado", META)
    assert len(lineas) == 3
    assert lineas[1]["monto_miles_clp"] == -2702777
    assert cuadratura_resultados(lineas)["estado"] == "OK"


if __name__ == "__main__":
    test_tabla_cierra_y_no_inventa()
    test_comparativo_primero_no_se_deja_al_reves()
    test_apilado_como_sale_el_pdf()
    test_encabezado_notas_y_anio_no_es_linea()
    test_api_con_monto_vacio_no_revienta()
    test_nota_con_punto_y_parentesis_no_es_monto()
    test_desglose_de_la_linea_padre_no_se_suma_dos_veces()
    test_resultado_no_suma_dos_veces_ni_se_come_el_cero()
    test_texto_y_titulo()
    print("ok")

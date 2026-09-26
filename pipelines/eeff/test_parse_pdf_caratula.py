"""Parser de carátula, sin red. Una tabla sintética y una página en texto."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipelines.eeff.parse_pdf_caratula import (
    clasificar_pagina,
    lineas_apiladas,
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
    test_texto_y_titulo()
    print("ok")

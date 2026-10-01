"""Pruebas del sondeo de industrias del TXT IFRS (scripts/sondear_ifrs_sectores.py).

El sondeo decide a qué industria vale la pena extenderse, así que su clasificación
tiene que ser estable y su lectura del archivo, la misma que la del extractor.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
RUTA = RAIZ / "scripts" / "sondear_ifrs_sectores.py"


def cargar():
    spec = importlib.util.spec_from_file_location("sondear_ifrs_sectores", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["sondear_ifrs_sectores"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


sondeo = cargar()


def fila(rut, nombre, tax="TAX CI", estado="ESF C/NC", cuenta="Total de activos", valor="1"):
    return f"202606;{rut};{nombre};I;CLP;{cuenta};{valor};{tax};{estado}"


class GiroTest(unittest.TestCase):
    def test_reconoce_los_giros_conocidos(self):
        casos = {
            "BANCO DE CHILE": "banca",
            "COMPAÑIA DE SEGUROS GENERALES CONSORCIO NACIONAL": "seguros",
            "HMC S.A. ADMINISTRADORA GENERAL DE FONDOS": "agf",
            "BCI SECURITIZADORA S.A.": "securitizadora",
            "CAJA DE COMPENSACION DE ASIGNACION FAMILIAR LOS ANDES": "caja_compensacion",
            "FACTORING SECURITY S.A.": "factoring_leasing",
            "BANCHILE CORREDORES DE BOLSA S.A.": "corredora_bolsa",
            "AFP HABITAT S.A.": "afp",
            "EMPRESA QUE NO CALZA CON NADA SPA": "sin clasificar",
        }
        for nombre, esperado in casos.items():
            self.assertEqual(sondeo.giro(nombre), esperado, nombre)

    def test_normaliza_acentos_y_mayusculas(self):
        self.assertEqual(sondeo.giro("caja de compensación los héroes"), "caja_compensacion")


class SondearTest(unittest.TestCase):
    def test_cuenta_sociedades_taxonomias_y_novedad(self):
        lineas = [
            fila("76034728", "HMC S.A. ADMINISTRADORA GENERAL DE FONDOS"),          # cubierta
            fila("97004000", "BANCO DE CHILE"),                                      # cubierta
            fila("76123456", "EMPRESA NUEVA SPA"),                                   # nueva
            fila("76123456", "EMPRESA NUEVA SPA", estado="ERFG", cuenta="Ingresos"),
            fila("99501480", "LEASING ANDINO S.A.", tax="TAX HB"),
        ]
        informe = sondeo.sondear([(i + 1, l.split(";")) for i, l in enumerate(lineas)],
                                 {"76034728": "agf", "97004000": "bancos"})
        self.assertEqual(informe["sociedades"], 4)
        self.assertEqual(informe["ya_en_el_sistema"], 2)
        self.assertEqual(informe["nuevas_para_el_sistema"], 2)
        self.assertEqual(informe["por_taxonomia"], {"TAX CI": 3, "TAX HB": 1})
        # sociedades por estado (no filas): 4 traen balance y 1 además resultados
        self.assertEqual(informe["por_estado"], {"ESF C/NC": 4, "ERFG": 1})
        giros = {g["giro"]: g for g in informe["por_giro"]}
        self.assertEqual(giros["agf"]["sociedades"], 1)
        self.assertEqual(giros["agf"]["nuevas"], 0)
        self.assertEqual(giros["banca"]["nuevas"], 0)
        self.assertEqual(giros["factoring_leasing"]["nuevas"], 1)
        self.assertEqual(giros["sin clasificar"]["nuevas"], 1)

    def test_ignora_lineas_incompletas_y_rut_no_numericos(self):
        lineas = [fila("76034728", "HMC AGF"), "202606;;SIN RUT;I;CLP;cuenta;1;TAX CI;ESF C/NC"]
        informe = sondeo.sondear([(1, l.split(";")) for l in lineas], {})
        self.assertEqual(informe["sociedades"], 1)

    def test_ejemplos_se_ordenan_por_tamano_del_estado(self):
        lineas = [fila("76111111", "EMPRESA CHICA SPA")]
        lineas += [fila("76222222", "EMPRESA GRANDE SPA", cuenta=f"Cuenta {i}") for i in range(5)]
        informe = sondeo.sondear([(i + 1, l.split(";")) for i, l in enumerate(lineas)], {}, ejemplos=3)
        nuevo = [g for g in informe["por_giro"] if g["giro"] == "sin clasificar"][0]
        self.assertEqual([e["rut"] for e in nuevo["ejemplos_nuevas"]], ["76222222", "76111111"])


if __name__ == "__main__":
    unittest.main()

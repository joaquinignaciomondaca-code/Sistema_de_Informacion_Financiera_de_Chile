"""Pruebas del parseo compartido del TXT IFRS de la CMF (`pipelines/auto/ifrs_txt.py`).

Dos extractores publican a partir del mismo archivo; si lo interpretan distinto, las dos
tablas se ven iguales y no lo son. Estas pruebas fijan la interpretación.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

from pipelines.auto import ifrs_txt  # noqa: E402


class ArchivoTest(unittest.TestCase):
    def test_rechaza_html_y_vacios(self):
        self.assertFalse(ifrs_txt.es_txt(b""))
        self.assertFalse(ifrs_txt.es_txt(b"<html><body>error</body></html>"))
        self.assertFalse(ifrs_txt.es_txt(b"<!DOCTYPE html><p>no</p>"))
        self.assertFalse(ifrs_txt.es_txt(b"ACCION NO PERMITIDA"))

    def test_acepta_el_txt(self):
        self.assertTrue(ifrs_txt.es_txt(b"202503;76034728;EMPRESA;I;CLP;Total de activos;1;TAX CI;ESF C/NC\n"))

    def test_decodifica_latin1_si_utf8_falla(self):
        self.assertEqual(ifrs_txt.decodificar("SECURITIZADORA".encode("latin-1")), "SECURITIZADORA")
        self.assertEqual(ifrs_txt.decodificar("CAJA DE COMPENSACI\xd3N".encode("latin-1")),
                         "CAJA DE COMPENSACIÓN")

    def test_lineas_descarta_vacias_y_quita_espacios(self):
        brute = b"202503; A ;I;CLP;cuenta;1;TAX CI;ESF C/NC\n\n   \n"
        lineas = list(ifrs_txt.lineas(brute))
        self.assertEqual(len(lineas), 1)
        self.assertEqual(lineas[0][1][1], "A")


class RepartoTest(unittest.TestCase):
    def test_esf_es_balance_y_er_es_resultados(self):
        self.assertEqual(ifrs_txt.tabla_de("ESF C/NC"), "balance")
        self.assertEqual(ifrs_txt.tabla_de("ESF OL"), "balance")
        self.assertEqual(ifrs_txt.tabla_de("ERFG"), "resultados")
        self.assertEqual(ifrs_txt.tabla_de("ERNG"), "resultados")
        self.assertEqual(ifrs_txt.tabla_de("ERI"), "resultados")

    def test_fluir_de_efectivo_no_se_publica(self):
        self.assertIsNone(ifrs_txt.tabla_de("EFMD"))
        self.assertIsNone(ifrs_txt.tabla_de("EFMI"))
        self.assertIsNone(ifrs_txt.tabla_de(""))


class ImporteTest(unittest.TestCase):
    def test_enteros(self):
        self.assertEqual(ifrs_txt.valor_y_texto("1000"), (1000, None))
        self.assertEqual(ifrs_txt.valor_y_texto("-281398000"), (-281398000, None))
        self.assertEqual(ifrs_txt.valor_y_texto("0"), (0, None))

    def test_no_entero_queda_nulo_y_el_texto_se_conserva(self):
        self.assertEqual(ifrs_txt.valor_y_texto("14.5821"), (None, "14.5821"))
        self.assertEqual(ifrs_txt.valor_y_texto("1.234,56"), (None, "1.234,56"))
        self.assertEqual(ifrs_txt.valor_y_texto(""), (None, ""))

    def test_nunca_se_adivina_un_cero_ni_un_separador_decimal(self):
        valor, texto = ifrs_txt.valor_y_texto("0,00")
        self.assertIsNone(valor)   # no es un entero literal: no se redondea a 0
        self.assertEqual(texto, "0,00")


class ContextosTest(unittest.TestCase):
    def test_orden_y_repeticion(self):
        ctx = ifrs_txt.Contextos()
        clave = ctx.clave_estado("202503", "76034728", "I", "CLP", "TAX CI", "ERFG")
        self.assertEqual(ctx.agregar(clave, "Ingresos"), (1, 1))
        self.assertEqual(ctx.agregar(clave, "Ganancia (pérdida)"), (2, 1))
        # La misma cuenta por segunda vez: sube la repetición, no el orden.
        self.assertEqual(ctx.agregar(clave, "Ganancia (pérdida)"), (3, 2))

    def test_la_taxonomia_separa_los_estados(self):
        ctx = ifrs_txt.Contextos()
        a = ctx.clave_estado("202503", "1", "I", "CLP", "TAX CI", "ESF C/NC")
        b = ctx.clave_estado("202503", "1", "I", "CLP", "TAX HB", "ESF C/NC")
        self.assertEqual(ctx.agregar(a, "Efectivo"), (1, 1))
        self.assertEqual(ctx.agregar(b, "Efectivo"), (1, 1))

    def test_estados_distintos_no_comparten_orden(self):
        ctx = ifrs_txt.Contextos()
        self.assertEqual(ctx.agregar(ctx.clave_estado("202503", "1", "I", "CLP", "TAX CI", "ERFG"), "A"), (1, 1))
        self.assertEqual(ctx.agregar(ctx.clave_estado("202503", "1", "I", "CLP", "TAX CI", "ERI"), "A"), (1, 1))


if __name__ == "__main__":
    unittest.main()

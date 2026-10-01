"""Pruebas del parseo compartido del TXT IFRS de la CMF (`pipelines/auto/ifrs_txt.py`).

Dos extractores publican a partir del mismo archivo; si lo interpretan distinto, las dos
tablas se ven iguales y no lo son. Estas pruebas fijan la interpretación.
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
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


def _indice(entradas, forma="parrafos") -> bytes:
    """Índice sintético con la forma de la página: un enlace por archivo y su «actualizado»."""
    html = ""
    for inicio, fin, texto in entradas:
        href = f"https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={inicio}&amp;termino={fin}"
        fecha = f"(actualizado: {texto})" if texto else ""
        if forma == "parrafos":
            html += f'<p><a href="{href}">x</a></p><p>{fecha}</p>'
        elif forma == "br":
            html += f'<a href="{href}">x</a><br/><small>{fecha}</small><br/>'
        elif forma == "dentro_del_enlace":
            html += f'<li><a href="{href}">x {fecha}</a></li>'
        elif forma == "dos_enlaces":
            html += f'<div><a href="{href}">x</a><a href="{href}"><img/></a><span>{fecha}</span></div>'
    return f"<html><body>{html}</body></html>".encode("utf-8")


class ActualizacionesIndiceTest(unittest.TestCase):
    """La CMF reedita cierres viejos: el índice dice cuándo, y de ahí se decide releer."""

    ENTRADAS = [("202606", "202606", "30/09/2026 23:59"), ("202512", "202512", "26/08/2026 22:01"),
                ("202403", "202412", "31/03/2025")]

    def test_fecha_con_hora_se_convierte_de_hora_de_chile_a_utc(self):
        # Septiembre ya está en horario de verano (UTC-3); agosto no (UTC-4).
        self.assertEqual(ifrs_txt.fecha_actualizado("(actualizado: 30/09/2026 23:59)"),
                         datetime(2026, 10, 1, 2, 59, tzinfo=timezone.utc))
        self.assertEqual(ifrs_txt.fecha_actualizado("(actualizado: 26/08/2026 22:01)"),
                         datetime(2026, 8, 27, 2, 1, tzinfo=timezone.utc))

    def test_fecha_sin_hora_es_el_final_del_dia(self):
        # Prudente: si la CMF tocó el archivo ese día después de nuestra lectura, se baja otra vez.
        f = ifrs_txt.fecha_actualizado("(actualizado: 31/03/2025)")
        self.assertEqual(f, datetime(2025, 4, 1, 2, 59, 59, tzinfo=timezone.utc))

    def test_texto_sin_fecha_o_fecha_imposible(self):
        self.assertIsNone(ifrs_txt.fecha_actualizado(""))
        self.assertIsNone(ifrs_txt.fecha_actualizado("Junio 2026"))
        self.assertIsNone(ifrs_txt.fecha_actualizado("(actualizado: 31/02/2026)"))
        self.assertIsNone(ifrs_txt.fecha_actualizado("(actualizado: 12/13/2026)"))

    def test_funciona_con_las_formas_plausibles_del_html(self):
        for forma in ("parrafos", "br", "dentro_del_enlace", "dos_enlaces"):
            with self.subTest(forma=forma):
                r = ifrs_txt.actualizaciones_indice(_indice(self.ENTRADAS, forma))
                self.assertEqual(r["202606"], datetime(2026, 10, 1, 2, 59, tzinfo=timezone.utc))
                self.assertEqual(r["202512"], datetime(2026, 8, 27, 2, 1, tzinfo=timezone.utc))

    def test_un_enlace_anual_vale_para_sus_cuatro_trimestres(self):
        r = ifrs_txt.actualizaciones_indice(_indice(self.ENTRADAS))
        trimestres = {k for k in r if k.startswith("2024")}
        self.assertEqual(trimestres, {"202403", "202406", "202409", "202412"})
        self.assertEqual(len({r[k] for k in trimestres}), 1)

    def test_cada_enlace_recibe_su_propia_fecha(self):
        """Un enlace sin fecha no hereda la del vecino (no hay cierre falso ni relectura falsa)."""
        r = ifrs_txt.actualizaciones_indice(_indice([("202606", "202606", None),
                                                     ("202603", "202603", "27/08/2026 12:00")]))
        self.assertNotIn("202606", r)
        self.assertIn("202603", r)

    def test_si_hay_dos_fechas_para_un_trimestre_gana_la_mas_reciente(self):
        r = ifrs_txt.actualizaciones_indice(_indice([("202403", "202412", "31/03/2025"),
                                                     ("202409", "202409", "10/01/2026 08:00")]))
        self.assertEqual(r["202409"], datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc))
        self.assertEqual(r["202406"], datetime(2025, 4, 1, 2, 59, 59, tzinfo=timezone.utc))

    def test_sin_fechas_o_con_html_roto_no_devuelve_nada(self):
        self.assertEqual(ifrs_txt.actualizaciones_indice(b""), {})
        self.assertEqual(ifrs_txt.actualizaciones_indice(_indice([("202606", "202606", None)])), {})
        self.assertEqual(ifrs_txt.actualizaciones_indice(b"<html><a href='ver_archivo.php?inicio=2"), {})

    def test_ignora_intervalos_que_no_son_trimestrales(self):
        r = ifrs_txt.actualizaciones_indice(_indice([("202401", "202412", "31/03/2025"),
                                                     ("202412", "202403", "31/03/2025")]))
        self.assertEqual(r, {})

    def test_reeditado_despues_de_la_ultima_lectura(self):
        leido = "2026-09-28T08:02:39+00:00"
        self.assertTrue(ifrs_txt.reeditado_despues(leido, datetime(2026, 9, 29, tzinfo=timezone.utc)))
        self.assertFalse(ifrs_txt.reeditado_despues(leido, datetime(2026, 8, 27, tzinfo=timezone.utc)))
        # Sin fecha de la CMF o sin lectura previa: no hay por qué releer.
        self.assertFalse(ifrs_txt.reeditado_despues(leido, None))
        self.assertFalse(ifrs_txt.reeditado_despues(None, datetime(2026, 9, 29, tzinfo=timezone.utc)))
        self.assertFalse(ifrs_txt.reeditado_despues("no es una fecha", datetime(2026, 9, 29, tzinfo=timezone.utc)))

    def test_lectura_sin_zona_se_toma_como_utc(self):
        self.assertTrue(ifrs_txt.reeditado_despues("2026-09-28T08:02:39", datetime(2026, 9, 28, 9, tzinfo=timezone.utc)))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de scripts/build_privacidad_cifras.py.

No usan los Parquet del repositorio: la parte que se prueba es la reescritura del
texto, que es donde puede romperse en silencio (un patrón que deja de coincidir
haría que el script no encontrara el total y saliera con 1, o —peor— que
escribiera en el sitio equivocado).

Uso: python -m unittest scripts.test_build_privacidad_cifras -v
"""
from __future__ import annotations

import unittest

from scripts import build_privacidad_cifras as b


FILA_MD = (
    "| `fintech_rpsf_lista_entidades` | 36 personas naturales (de 267 prestadores) "
    "| RUT, nombre o razón social | Registro de Prestadores |\n"
    "| `corredoras_bolsa_lista_entidades` | 11 corredores inscritos a nombre de persona "
    "natural (de 120) | RUT, nombre | Registro de corredores |\n"
)

FILA_HTML = (
    "          <td>36 personas naturales, de 267 prestadores</td>\n"
    "          <td>11 corredores inscritos a nombre de persona natural, de 120</td>\n"
)


class AvisoTest(unittest.TestCase):
    def test_actualiza_los_dos_totales_en_markdown(self):
        texto, cambios = b.sincronizar(FILA_MD, 268, 121, "PRIVACIDAD.md")
        self.assertIn("de 268 prestadores", texto)
        self.assertIn("natural (de 121)", texto)
        self.assertEqual(len(cambios), 2)

    def test_actualiza_los_dos_totales_en_html(self):
        texto, cambios = b.sincronizar(FILA_HTML, 268, 121, "docs/privacidad.html")
        self.assertIn("de 268 prestadores", texto)
        self.assertIn("natural, de 121", texto)
        self.assertEqual(len(cambios), 2)

    def test_no_toca_los_conteos_que_expresan_el_criterio(self):
        """36 personas naturales y 11 corredores son el criterio, no la fuente.

        Si cambian, la compuerta de privacidad tiene que fallar para que alguien
        revise si el riesgo cambió; este script no debe taparlo.
        """
        texto, _ = b.sincronizar(FILA_MD, 300, 150, "PRIVACIDAD.md")
        self.assertIn("36 personas naturales", texto)
        self.assertIn("11 corredores", texto)

    def test_texto_sin_el_total_falla_en_vez_de_pasar_en_silencio(self):
        with self.assertRaises(SystemExit):
            b.sincronizar("No hay tabla de privacidad.\n", 268, 121, "PRIVACIDAD.md")

    def test_es_idempotente(self):
        una, _ = b.sincronizar(FILA_MD, 268, 121, "PRIVACIDAD.md")
        dos, cambios = b.sincronizar(una, 268, 121, "PRIVACIDAD.md")
        self.assertEqual(una, dos)
        self.assertEqual(cambios, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

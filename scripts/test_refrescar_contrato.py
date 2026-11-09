"""Pruebas del refresco unificado del contrato derivado.

La condición de carrera que motivó el script no se puede reproducir aquí con git real, pero
sí sus dos invariantes: la cadena se corre completa y en orden, y una cabeza que se mueve a
mitad de camino descarta el intento en vez de publicar una mezcla.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from scripts import refrescar_contrato as r  # noqa: E402
from scripts.cadena_contrato import CADENA  # noqa: E402


class RefrescoTest(unittest.TestCase):
    def test_la_cadena_lleva_las_metricas_y_termina_auditando(self):
        """`build_metricas_publicadas` debe ir antes de publicar, no después del commit."""
        self.assertIn("build_metricas_publicadas.py", CADENA)
        self.assertLess(CADENA.index("build_download_catalog.py"),
                        CADENA.index("build_metricas_publicadas.py"))
        self.assertLess(CADENA.index("build_metricas_publicadas.py"),
                        CADENA.index("auditar_contrato.py"))
        self.assertEqual(CADENA[-1], "auditar_contrato.py")

    def test_el_aviso_de_privacidad_se_sincroniza_antes_de_sellar_el_html(self):
        """Los totales de la fuente se escriben antes de que `build_metadatos` selle el HTML.

        El 2026-11-09 el registro FinTech de la CMF pasó de 267 a 268 prestadores y
        `web_audit` se puso en rojo en `main`: el aviso declaraba la cifra vieja. Si
        el paso va después de `build_metadatos`, el HTML publicado queda una alta
        atrás aunque el Markdown esté al día.
        """
        self.assertIn("build_privacidad_cifras.py", CADENA)
        self.assertLess(CADENA.index("build_privacidad_cifras.py"),
                        CADENA.index("build_metadatos.py"))

    def test_corre_todos_los_generadores_y_verifica_cada_uno(self):
        llamadas = []

        def correr(script, *args):
            llamadas.append((script, args))

        with mock.patch.object(r, "correr", correr), \
             mock.patch.object(r, "cpu", return_value="abc"):
            self.assertTrue(r.intento(verificar=True))
        # `auditar_contrato.py` se invoca siempre con `--check`: no genera, audita.
        generadores = [s for s, args in llamadas if not args]
        self.assertEqual(generadores, [s for s in CADENA if s != "auditar_contrato.py"])
        self.assertIn(("auditar_contrato.py", ("--check",)), llamadas)
        verificados = [s for s, args in llamadas if args == ("--check",)]
        self.assertIn("build_metricas_publicadas.py", verificados)
        self.assertIn("build_api.py", verificados)
        # `verificar_claves.py` no genera artefactos: no tiene `--check` que correr.
        self.assertNotIn("verificar_claves.py", verificados)

    def test_si_la_cabeza_se_mueve_se_descarta_el_intento(self):
        """Publicar medio contrato es peor que no publicar: se rehace desde cero."""
        cabezas = iter(["aaa", "bbb"])

        def correr(script, *args):
            del script, args

        with mock.patch.object(r, "correr", correr), \
             mock.patch.object(r, "cpu", lambda: next(cabezas, "bbb")):
            self.assertFalse(r.intento(verificar=False))

    def test_reintenta_y_termina_fallando_si_la_rama_no_deja_de_moverse(self):
        with mock.patch.object(r, "intento", lambda verificar: False), \
             mock.patch.object(r.time, "sleep", lambda s: None), \
             mock.patch("builtins.print"):
            self.assertEqual(r.main(["--intentos", "3"]), 1)
        with mock.patch.object(r, "intento", lambda verificar: True), \
             mock.patch("builtins.print"):
            self.assertEqual(r.main([]), 0)

    def test_sin_verificar_omite_la_pasada_de_check(self):
        vistos = []

        def correr(script, *args):
            vistos.append(args)

        with mock.patch.object(r, "correr", correr), \
             mock.patch.object(r, "cpu", return_value="abc"):
            r.intento(verificar=False)
        # El único `--check` permitido es el del auditor, que siempre audita.
        self.assertEqual(len(vistos), len(CADENA))
        self.assertEqual(vistos.count(("--check",)), 1)


if __name__ == "__main__":
    unittest.main()

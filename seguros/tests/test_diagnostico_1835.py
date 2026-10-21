"""Regresión: el resumen del diagnóstico diferencia exclusiones de errores fatales."""
import contextlib
import io
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from seguros.scripts import actualizar_carteras as ac


class Diagnostico1835Test(unittest.TestCase):
    def test_reporta_archivos_excluidos_sin_declarar_periodo_fallido(self):
        salida = io.StringIO()
        args = SimpleNamespace(zip_dir=None, cache=None)
        resultado_lectura = ({}, {}, [], ["e202412g.76598625: tipo de registro '6' desconocido"])
        with patch.dict(os.environ, {"GITHUB_ACTIONS": ""}, clear=False):
            with patch.object(ac, "descargar", return_value=b"zip"):
                with patch.object(ac, "leer_zip", side_effect=[resultado_lectura, ({}, {}, [], [])]):
                    with contextlib.redirect_stdout(salida):
                        rc = ac.diagnostico(["2024-12"], args)
        self.assertEqual(rc, 0)
        texto = salida.getvalue()
        self.assertIn("1 archivos excluidos", texto)
        self.assertIn("0 sectores con error fatal", texto)
        self.assertIn("1 archivos excluidos con advertencia", texto)


if __name__ == "__main__":
    unittest.main()

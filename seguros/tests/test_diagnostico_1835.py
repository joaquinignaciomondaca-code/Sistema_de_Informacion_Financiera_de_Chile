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
        vacias = {tabla: [] for tabla in ac.TABLAS}
        resultado_lectura = (vacias, {}, [], ["e202412g.76598625: tipo de registro '6' desconocido"])
        sin_exclusiones = ({tabla: [] for tabla in ac.TABLAS}, {}, [], [])
        with patch.dict(os.environ, {"GITHUB_ACTIONS": ""}, clear=False):
            with patch.object(ac, "descargar", return_value=b"zip"):
                with patch.object(ac, "contar_archivos_por_tipo", return_value={"e": 0, "r": 1, "v": 2, "g": 0}):
                    with patch.object(ac, "leer_zip", side_effect=[resultado_lectura, sin_exclusiones]):
                        with contextlib.redirect_stdout(salida):
                            rc = ac.diagnostico(["2024-12"], args)
        self.assertEqual(rc, 0)
        texto = salida.getvalue()
        self.assertIn("1 archivos excluidos", texto)
        self.assertIn("0 sectores con error fatal", texto)
        self.assertIn("1 archivos excluidos con advertencia", texto)
        self.assertIn("B.12/r 1 archivos, 0 filas", texto)
        self.assertIn("B.13/v 2 archivos, 0 filas", texto)


if __name__ == "__main__":
    unittest.main()

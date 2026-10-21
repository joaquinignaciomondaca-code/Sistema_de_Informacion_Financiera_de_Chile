"""Pruebas de auditoría de archivos fuente y de diagnóstico 1835."""
import contextlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from seguros.scripts import actualizar_carteras as ac


class Diagnostico1835Test(unittest.TestCase):
    def test_audita_prefijos_fuente_y_persiste_solo_conteos(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for nombre in ("e202412.empresa", "e202412.empresa2", "v202412.arriendo", "g202412.garantia"):
                z.writestr(nombre, b"")
        args = SimpleNamespace(zip_dir=None, cache=None)
        control = {"aseguradoras": {}, "periodos": {"2024-12": {"registros": {}}}}
        original_salida = ac.SALIDA
        with tempfile.TemporaryDirectory() as tmp:
            ac.SALIDA = Path(tmp)
            try:
                with patch.object(ac, "descargar", return_value=buf.getvalue()):
                    with contextlib.redirect_stdout(io.StringIO()):
                        rc = ac.auditar_archivos_fuente(control, ["2024-12"], args)
                guardado = json.loads((Path(tmp) / "manifest.json").read_text())
            finally:
                ac.SALIDA = original_salida
        self.assertEqual(rc, 0)
        for sector in ("vida", "generales"):
            self.assertEqual(guardado["periodos"]["2024-12"]["archivos_fuente_por_prefijo"][sector],
                             {"e": 2, "r": 0, "v": 1, "g": 1})

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

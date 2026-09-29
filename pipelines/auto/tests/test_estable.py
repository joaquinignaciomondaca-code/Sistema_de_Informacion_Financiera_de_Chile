import json
import tempfile
import unittest
from pathlib import Path

from pipelines.auto import estable


class EstableTest(unittest.TestCase):
    def setUp(self):
        self.ruta = Path(tempfile.mkdtemp()) / "manifest.json"

    def test_primera_escritura(self):
        self.assertTrue(estable.escribir_json(self.ruta, {"a": 1, "updated_at": "2026-01-01"}))
        self.assertEqual(json.loads(self.ruta.read_text())["a"], 1)

    def test_solo_cambia_la_hora_no_reescribe(self):
        estable.escribir_json(self.ruta, {"a": 1, "updated_at": "2026-01-01", "p": {"leido_utc": "x", "n": 2}})
        antes = self.ruta.read_text()
        self.assertFalse(estable.escribir_json(self.ruta, {"a": 1, "updated_at": "2026-09-29", "p": {"leido_utc": "y", "n": 2}}))
        self.assertEqual(self.ruta.read_text(), antes)

    def test_cambio_real_escribe_con_marcas_nuevas(self):
        estable.escribir_json(self.ruta, {"a": 1, "updated_at": "2026-01-01"})
        self.assertTrue(estable.escribir_json(self.ruta, {"a": 2, "updated_at": "2026-09-29"}))
        self.assertEqual(json.loads(self.ruta.read_text()), {"a": 2, "updated_at": "2026-09-29"})

    def test_listas_y_claves_nuevas_cuentan_como_cambio(self):
        estable.escribir_json(self.ruta, {"t": [{"id": 1, "ultima_actualizacion": "a"}]})
        self.assertTrue(estable.escribir_json(self.ruta, {"t": [{"id": 1, "ultima_actualizacion": "b"}, {"id": 2}]}))
        self.assertTrue(estable.escribir_json(self.ruta, {"t": [{"id": 1}, {"id": 2}], "nueva": 1}))

    def test_archivo_previo_corrupto_se_reescribe(self):
        self.ruta.write_text("{roto")
        self.assertTrue(estable.escribir_json(self.ruta, {"a": 1}))


if __name__ == "__main__":
    unittest.main()

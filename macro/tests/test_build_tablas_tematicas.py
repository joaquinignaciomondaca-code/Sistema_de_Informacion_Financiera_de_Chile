"""El constructor macro no descarta observaciones duplicadas sin revisión."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from macro.scripts import build_tablas_tematicas as builder
from scripts import build_macro_web as web_builder


class CargaSeries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.tmp.name)
        self.patch = patch.object(builder, "CARPETA_SERIES", self.carpeta)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def escribir(self, nombre: str, filas: list[dict]) -> None:
        pd.DataFrame(filas).to_parquet(self.carpeta / nombre, index=False)

    def test_conserva_observaciones_no_solapadas_entre_archivos(self):
        self.escribir("2024.parquet", [{
            "fecha": "2024-01-01", "periodo": "2024-01", "clave": "uf",
            "serie_id": "F000", "valor": 36000.0,
        }])
        self.escribir("2025.parquet", [{
            "fecha": "2025-01-01", "periodo": "2025-01", "clave": "uf",
            "serie_id": "F000", "valor": 38000.0,
        }])

        resultado = builder.cargar_series()

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado["valor"].tolist(), [36000.0, 38000.0])

    def test_rechaza_repeticion_exacta_en_vez_de_deduplicar(self):
        fila = {
            "fecha": "2025-01-01", "periodo": "2025-01", "clave": "uf",
            "serie_id": "F000", "valor": 38000.0,
        }
        self.escribir("2025.parquet", [fila, fila.copy()])

        with self.assertRaisesRegex(ValueError, "no se deduplican automáticamente"):
            builder.cargar_series()

    def test_rechaza_valores_conflictivos_para_la_misma_clave(self):
        filas = [
            {"fecha": "2025-01-01", "periodo": "2025-01", "clave": "uf",
             "serie_id": "F000", "valor": 38000.0},
            {"fecha": "2025-01-01", "periodo": "2025-01", "clave": "uf",
             "serie_id": "F000", "valor": 38100.0},
        ]
        self.escribir("2025.parquet", filas)

        with self.assertRaisesRegex(ValueError, "no se deduplican automáticamente"):
            builder.cargar_series()

    def test_detecta_duplicados_entre_archivos(self):
        fila = {
            "fecha": "2025-01-01", "periodo": "2025-01", "clave": "uf",
            "serie_id": "F000", "valor": 38000.0,
        }
        self.escribir("2025-a.parquet", [fila])
        self.escribir("2025-b.parquet", [fila.copy()])

        with self.assertRaisesRegex(ValueError, "Hay 2 filas"):
            builder.cargar_series()


class MetadatosWeb(unittest.TestCase):
    def test_fecha_diaria_no_se_declara_como_dia_habil(self):
        spec = next(t for t in web_builder.TABLAS if t["id"] == "macro_uf")
        ficha = web_builder.ficha(spec, {
            "filas": 4682,
            "desde": "2014-01-01",
            "hasta": "2026-10-26",
            "ultima_actualizacion": "2026-10-26",
        })
        self.assertIn("Fecha de la observación diaria (AAAA-MM-DD) publicada por el BCCh.", ficha)
        self.assertNotIn("día hábil publicado por el BCCh", ficha)


if __name__ == "__main__":
    unittest.main()

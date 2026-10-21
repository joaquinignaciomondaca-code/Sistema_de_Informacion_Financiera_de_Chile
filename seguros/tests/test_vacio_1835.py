"""Prueba que las tablas sin filas publiquen un Parquet vacío con su esquema completo.

Sin este archivo, una tabla que la CMF no entrega (B.12 y B.13 en los 22 cierres auditados) queda
con `files: []` en su manifiesto, y la vista web falla con "No hay particiones publicadas".

Todo se escribe en un directorio temporal: no se toca docs/outputs ni data_manifest.json.

  python -m unittest seguros.tests.test_vacio_1835
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from seguros.scripts import actualizar_carteras as ac


class TablasVaciasTest(unittest.TestCase):
    def setUp(self):
        self._salida = ac.SALIDA
        self._tmp = tempfile.TemporaryDirectory()
        ac.SALIDA = Path(self._tmp.name)

    def tearDown(self):
        ac.SALIDA = self._salida
        self._tmp.cleanup()

    def test_tablas_sin_filas_publican_parquet_vacio_con_esquema(self):
        ac.escribir_manifiestos({"periodos": {}, "aseguradoras": {}})
        for tabla in ac.TABLAS:
            with self.subTest(tabla=tabla):
                vacio = ac.SALIDA / tabla / "_vacio.parquet"
                self.assertTrue(vacio.exists(), "falta _vacio.parquet")
                archivo = pq.ParquetFile(vacio)
                self.assertEqual(archivo.metadata.num_rows, 0)
                self.assertEqual(archivo.schema_arrow.names, ac.esquema(tabla).names)
                man = ac.SALIDA / tabla / "manifest.json"
                self.assertIn(f"outputs/seguros/{tabla}/_vacio.parquet",
                              man.read_text(encoding="utf-8"))
                self.assertIn('"total_records": 0', man.read_text(encoding="utf-8"))

    def test_datos_reales_retiran_el_vacio_y_no_se_mezclan(self):
        ac.escribir_manifiestos({"periodos": {}, "aseguradoras": {}})
        tabla = "prestamos"
        esquema = ac.esquema(tabla)
        ruta = ac.ruta_particion(tabla, "2025-01")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        fila = {nombre: None for nombre in esquema.names}
        fila.update({"periodo": "2025-01", "sector": "vida", "rut_aseguradora": "076543210"})
        pq.write_table(pa.Table.from_pylist([fila], schema=esquema), ruta)

        ac.escribir_manifiestos({"periodos": {}, "aseguradoras": {}})

        self.assertFalse((ac.SALIDA / tabla / "_vacio.parquet").exists(),
                         "el vacío debe retirarse cuando hay particiones reales")
        man = (ac.SALIDA / tabla / "manifest.json").read_text(encoding="utf-8")
        self.assertIn(f"outputs/seguros/{tabla}/{ruta.name}", man)
        self.assertNotIn("_vacio", man)
        self.assertIn('"total_records": 1', man)



if __name__ == "__main__":
    unittest.main()

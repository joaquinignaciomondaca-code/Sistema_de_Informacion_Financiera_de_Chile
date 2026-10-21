"""Prueba el backfill de vistas analíticas desde Parquet completos ya publicados."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from seguros.scripts import actualizar_carteras as ac
from seguros.scripts.vistas_1835 import RESUMENES_RELEVANTES


class BackfillVistasTest(unittest.TestCase):
    def test_deriva_por_periodo_sin_descargar_zip_y_conserva_filas(self):
        anterior_salida = ac.SALIDA
        anterior_manifiestos = ac.escribir_manifiestos
        anterior_data_manifest = ac.actualizar_data_manifest
        try:
            with tempfile.TemporaryDirectory() as tmp:
                ac.SALIDA = Path(tmp)
                ac._ESQUEMAS.clear()
                schema = ac.esquema("acciones")
                rows = []
                for periodo, nemotecnico in (("2016-11", "AAA"), ("2016-12", "BBB")):
                    row = {name: None for name in schema.names}
                    row.update({
                        "periodo": periodo,
                        "sector": "vida",
                        "rut_aseguradora": "76015592-1",
                        "nombre_aseguradora": "ASEGURADORA DE PRUEBA",
                        "tipo_instrumento": "ACC",
                        "nemotecnico": nemotecnico,
                        "serie": "A",
                        "unidad_monetaria": "CLP",
                        "unidades": 10.0,
                        "valor_costo_clp": 1000.0,
                        "valor_libro_clp": 1000.0,
                        "valor_bolsa_clp": 1100.0,
                        "valor_razonable_m_clp": 1,
                        "deterioro_m_clp": 0,
                        "valor_final_m_clp": 1,
                        "clasificacion_de_riesgo": "AA",
                        "relacionado": "NR",
                    })
                    rows.append(row)
                origen = ac.ruta_particion("acciones", "2016-11")
                origen.parent.mkdir(parents=True)
                df = pd.DataFrame(rows).reindex(columns=schema.names)
                pq.write_table(pa.Table.from_pandas(df, schema=schema, preserve_index=False), origen)
                control = {
                    "periodos": {
                        periodo: {"registros": {"acciones": 1}}
                        for periodo in ("2016-11", "2016-12")
                    },
                    "aseguradoras": {},
                }
                derivables = ac.backfill_vistas_existentes(control, escribir=False)
                self.assertEqual(derivables, {
                    ("2016-11", "acciones_relevantes"),
                    ("2016-12", "acciones_relevantes"),
                })
                # Evita tocar los manifiestos del repo: la prueba coteja el Parquet derivado.
                ac.escribir_manifiestos = lambda _control: None
                ac.actualizar_data_manifest = lambda _control: None
                self.assertEqual(ac.backfill_vistas_existentes(control, escribir=True), derivables)
                resumen = pq.read_table(ac.ruta_particion("acciones_relevantes", "2016-11")).to_pandas()
                self.assertEqual(len(resumen), 2)
                self.assertEqual(resumen["nemotecnico"].tolist(), ["AAA", "BBB"])
                resumen_slug = next(cfg[0] for cfg in RESUMENES_RELEVANTES.values()
                                    if cfg[0] == "acciones_relevantes")
                self.assertEqual(list(resumen.columns), ac.esquema(resumen_slug).names)
        finally:
            ac.SALIDA = anterior_salida
            ac.escribir_manifiestos = anterior_manifiestos
            ac.actualizar_data_manifest = anterior_data_manifest
            ac._ESQUEMAS.clear()


if __name__ == "__main__":
    unittest.main()

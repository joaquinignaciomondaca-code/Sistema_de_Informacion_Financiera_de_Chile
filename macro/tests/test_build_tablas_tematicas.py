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

    def test_fecha_mensual_se_rotula_como_inicio_del_mes(self):
        spec = next(t for t in web_builder.TABLAS if t["id"] == "macro_utm")
        ficha = web_builder.ficha(spec, {
            "filas": 154,
            "desde": "2014-01-01",
            "hasta": "2026-10-01",
            "ultima_actualizacion": "2026-10-26",
        })
        self.assertIn("Primer día del mes al que corresponde el dato (AAAA-MM-01).", ficha)

    def test_fecha_trimestral_se_rotula_como_inicio_del_trimestre(self):
        spec = next(t for t in web_builder.TABLAS if t["id"] == "macro_pib_trimestral")
        ficha = web_builder.ficha(spec, {
            "filas": 50,
            "desde": "2014-01-01",
            "hasta": "2026-04-01",
            "ultima_actualizacion": "2026-10-26",
        })
        self.assertIn("Primer día del trimestre al que corresponde el dato (AAAA-MM-01).", ficha)

    def test_pib_trimestral_conserva_observacion_de_cada_trimestre(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_pib_trimestral")
        series = pd.DataFrame([
            {"fecha": "2026-01-01", "periodo": "2026-01", "clave": "pib",
             "serie_id": "F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T", "valor": 3200.0},
            {"fecha": "2026-04-01", "periodo": "2026-04", "clave": "pib",
             "serie_id": "F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T", "valor": 3300.0},
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-01-01", "2026-04-01"])
        self.assertEqual(tabla["periodo"].tolist(), ["2026-01", "2026-04"])
        self.assertEqual(tabla["pib_encadenado_miles_mm_clp"].tolist(), [3200.0, 3300.0])

    def test_imacec_es_una_fila_mensual_con_todas_sus_series(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_imacec")
        keys = [key for key, _ in spec["columnas"]]
        series = pd.DataFrame([
            {"fecha": fecha, "periodo": fecha[:7], "clave": key,
             "serie_id": f"source-{key}", "valor": base + indice}
            for indice, key in enumerate(keys, start=1)
            for fecha, base in (("2026-07-01", 100.0), ("2026-08-01", 110.0))
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-07-01", "2026-08-01"])
        self.assertEqual(tabla["periodo"].tolist(), ["2026-07", "2026-08"])
        self.assertEqual(len(tabla), 2)
        for indice, (_key, columna) in enumerate(spec["columnas"], start=1):
            self.assertEqual(tabla[columna].tolist(), [100.0 + indice, 110.0 + indice])

    def test_ipc_alinea_indice_y_variaciones_mensuales(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_inflacion_ipc")
        keys = [key for key, _ in spec["columnas"]]
        series = pd.DataFrame([
            {"fecha": fecha, "periodo": fecha[:7], "clave": key,
             "serie_id": f"source-{key}", "valor": base + indice}
            for indice, key in enumerate(keys, start=1)
            for fecha, base in (("2026-08-01", 100.0), ("2026-09-01", 101.0))
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-08-01", "2026-09-01"])
        self.assertEqual(tabla["periodo"].tolist(), ["2026-08", "2026-09"])
        self.assertEqual(len(tabla), 2)
        for indice, (_key, columna) in enumerate(spec["columnas"], start=1):
            self.assertEqual(tabla[columna].tolist(), [100.0 + indice, 101.0 + indice])

    def test_tasas_corto_plazo_conserva_huecos_de_cada_serie(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_tasas_corto_plazo")
        series = pd.DataFrame([
            {"fecha": "2026-08-03", "periodo": "2026-08", "clave": "tpm",
             "serie_id": "source-tpm", "valor": 4.75},
            {"fecha": "2026-08-04", "periodo": "2026-08", "clave": "tpm",
             "serie_id": "source-tpm", "valor": 4.75},
            {"fecha": "2026-08-03", "periodo": "2026-08", "clave": "tib",
             "serie_id": "source-tib", "valor": 4.61},
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-08-03", "2026-08-04"])
        self.assertEqual(tabla["tpm_pct"].tolist(), [4.75, 4.75])
        self.assertEqual(tabla.loc[0, "tib_promedio_pct"], 4.61)
        self.assertTrue(pd.isna(tabla.loc[1, "tib_promedio_pct"]))

    def test_curva_bonos_pesos_alinea_plazos_y_preserva_huecos(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_curva_bonos_pesos")
        series = pd.DataFrame([
            {"fecha": "2026-10-21", "periodo": "2026-10", "clave": key,
             "serie_id": f"source-{key}", "valor": valor}
            for (key, _columna), valor in zip(spec["columnas"], (3.0, 3.2, 3.5))
        ] + [
            {"fecha": "2026-10-22", "periodo": "2026-10", "clave": "bcp_5y",
             "serie_id": "source-bcp_5y", "valor": 3.25},
            {"fecha": "2026-10-22", "periodo": "2026-10", "clave": "bcp_10y",
             "serie_id": "source-bcp_10y", "valor": 3.55},
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-10-21", "2026-10-22"])
        self.assertEqual(tabla.loc[0, "rendimiento_bono_pesos_2_anos_pct"], 3.0)
        self.assertTrue(pd.isna(tabla.loc[1, "rendimiento_bono_pesos_2_anos_pct"]))
        self.assertEqual(tabla["rendimiento_bono_pesos_5_anos_pct"].tolist(), [3.2, 3.25])
        self.assertEqual(tabla["rendimiento_bono_pesos_10_anos_pct"].tolist(), [3.5, 3.55])

    def test_swaps_camara_usa_union_de_fechas_sin_rellenar_series(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_swaps_camara")
        series = pd.DataFrame([
            {"fecha": "2026-08-03", "periodo": "2026-08", "clave": key,
             "serie_id": f"source-{key}", "valor": 4.0 + indice}
            for indice, (key, _columna) in enumerate(spec["columnas"], start=1)
        ] + [{
            "fecha": "2026-08-04", "periodo": "2026-08", "clave": "spc_clp_90d",
            "serie_id": "source-spc_clp_90d", "valor": 4.25,
        }])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-08-03", "2026-08-04"])
        self.assertEqual(tabla["swap_camara_pesos_90_dias_pct"].tolist(), [5.0, 4.25])
        for _key, columna in spec["columnas"][1:]:
            self.assertTrue(pd.isna(tabla.loc[1, columna]))

    def test_mercado_laboral_alinea_las_cuatro_metricas_mensuales(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_mercado_laboral")
        keys = [key for key, _ in spec["columnas"]]
        series = pd.DataFrame([
            {"fecha": fecha, "periodo": fecha[:7], "clave": key,
             "serie_id": f"source-{key}", "valor": base + indice}
            for indice, key in enumerate(keys, start=1)
            for fecha, base in (("2026-07-01", 100.0), ("2026-08-01", 110.0))
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-07-01", "2026-08-01"])
        self.assertEqual(tabla["periodo"].tolist(), ["2026-07", "2026-08"])
        self.assertEqual(len(tabla), 2)
        for indice, (_key, columna) in enumerate(spec["columnas"], start=1):
            self.assertEqual(tabla[columna].tolist(), [100.0 + indice, 110.0 + indice])

    def test_macro_cobre_une_observaciones_nativas_sin_rellenar_frecuencias(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_cobre")
        series = pd.DataFrame([
            {"fecha": "2026-01-01", "periodo": "2026-01", "clave": "cobre_mensual",
             "serie_id": "F019.PPB.PRE.40.M", "valor": 4.25},
            {"fecha": "2026-01-02", "periodo": "2026-01", "clave": "cobre_diario",
             "serie_id": "F019.PPB.PRE.100.D", "valor": 4.50},
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-01-01", "2026-01-02"])
        self.assertTrue(pd.isna(tabla.loc[0, "cobre_refinado_usd_por_libra"]))
        self.assertEqual(tabla.loc[0, "cobre_referencial_mensual_usd_por_libra"], 4.25)
        self.assertEqual(tabla.loc[1, "cobre_refinado_usd_por_libra"], 4.50)
        self.assertTrue(pd.isna(tabla.loc[1, "cobre_referencial_mensual_usd_por_libra"]))

    def test_inflacion_implicita_usa_pares_en_la_misma_fecha(self):
        spec = next(t for t in builder.TABLAS if t["id"] == "macro_inflacion_implicita")
        series = pd.DataFrame([
            {"fecha": "2026-01-02", "periodo": "2026-01", "clave": "bcp_5y",
             "serie_id": "F022.BCLP.TIS.AN05.NO.Z.D", "valor": 3.81},
            {"fecha": "2026-01-02", "periodo": "2026-01", "clave": "bcu_5y",
             "serie_id": "F022.BUF.TIS.AN05.UF.Z.D", "valor": 1.806},
            {"fecha": "2026-01-03", "periodo": "2026-01", "clave": "bcp_5y",
             "serie_id": "F022.BCLP.TIS.AN05.NO.Z.D", "valor": 3.82},
            {"fecha": "2026-01-04", "periodo": "2026-01", "clave": "bcp_10y",
             "serie_id": "F022.BCLP.TIS.AN10.NO.Z.D", "valor": 4.20},
            {"fecha": "2026-01-04", "periodo": "2026-01", "clave": "bcu_10y",
             "serie_id": "F022.BUF.TIS.AN10.UF.Z.D", "valor": 1.7545},
        ])

        tabla = builder.construir_tabla(spec, series)

        self.assertEqual(tabla["fecha"].tolist(), ["2026-01-02", "2026-01-04"])
        self.assertEqual(tabla.loc[0, "inflacion_implicita_5_anos_pct"], 2.004)
        self.assertTrue(pd.isna(tabla.loc[0, "inflacion_implicita_10_anos_pct"]))
        self.assertTrue(pd.isna(tabla.loc[1, "inflacion_implicita_5_anos_pct"]))
        self.assertEqual(tabla.loc[1, "inflacion_implicita_10_anos_pct"], 2.4455)


if __name__ == "__main__":
    unittest.main()

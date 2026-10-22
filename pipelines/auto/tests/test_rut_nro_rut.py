"""El RUT del emisor que la ficha de la CMF llama `nro_rut` (Circular 1835).

La ficha lo declara como campo tipo "r": nueve cifras de cuerpo (con ceros a la
izquierda) más el dígito verificador. Al publicarse tal cual, `JOIN`s entre
seguros y cualquier otra industria devolvían cero filas sin error, porque el
resto de la base publica `rut` = cuerpo y `rut_dv` = cuerpo-DV.

Estas pruebas fijan la regla en las tres rutas de normalización (registro,
tabla Arrow y DataFrame) y comprueban que no toca nada más.
"""
from __future__ import annotations

import unittest

import pandas as pd

from pipelines.auto.rut import normalizar_dataframe, normalizar_registro, normalizar_tabla


class NroRutRegistroTest(unittest.TestCase):
    def test_cuerpo_dv_pasa_a_cuerpo_mas_dv(self):
        r, cambios = normalizar_registro({"nro_rut": "97006000-6"})
        self.assertEqual(r, {"nro_rut": "97006000", "nro_rut_dv": "97006000-6"})
        self.assertIn("nro_rut→C (+nro_rut_dv)", cambios)

    def test_con_puntos(self):
        r, _ = normalizar_registro({"nro_rut": "97.006.000-6"})
        self.assertEqual(r, {"nro_rut": "97006000", "nro_rut_dv": "97006000-6"})

    def test_conserva_ceros_a_la_izquierda(self):
        r, _ = normalizar_registro({"nro_rut": "097029000-1"})
        self.assertEqual(r["nro_rut"], "097029000")
        self.assertEqual(r["nro_rut_dv"], "097029000-1")

    def test_digito_k(self):
        r, _ = normalizar_registro({"nro_rut": "76015592-K"})
        self.assertEqual(r, {"nro_rut": "76015592", "nro_rut_dv": "76015592-K"})

    def test_cuerpo_solo_no_inventa_dv(self):
        r, cambios = normalizar_registro({"nro_rut": "97006000"})
        self.assertEqual(r, {"nro_rut": "97006000"})
        self.assertEqual(cambios, [])

    def test_nulo(self):
        r, cambios = normalizar_registro({"nro_rut": None})
        self.assertIsNone(r["nro_rut"])
        self.assertEqual(cambios, [])

    def test_fk_se_publica_como_cuerpo(self):
        r, _ = normalizar_registro({"nro_rut_activo_objeto": "81826800-9"})
        self.assertEqual(r, {"nro_rut_activo_objeto": "81826800"})

    def test_idempotente(self):
        r1, _ = normalizar_registro({"nro_rut": "97006000-6"})
        r2, cambios = normalizar_registro(r1)
        self.assertEqual(r1, r2)
        self.assertEqual(cambios, [])

    def test_no_toca_otras_columnas(self):
        reg = {"nro_rut": "97006000-6", "rut_aseguradora": "97006000", "valor_final_m_clp": 5}
        r, _ = normalizar_registro(reg)
        self.assertEqual(r["rut_aseguradora"], "97006000")
        self.assertEqual(r["valor_final_m_clp"], 5)


class NroRutTablaTest(unittest.TestCase):
    def _tabla(self, df):
        import pyarrow as pa
        return pa.Table.from_pandas(df, preserve_index=False)

    def test_sin_columna_dv_la_agrega(self):
        t, _ = normalizar_tabla(self._tabla(pd.DataFrame({"nro_rut": ["97006000-6"]})))
        self.assertEqual(t.column("nro_rut").to_pylist(), ["97006000"])
        self.assertEqual(t.column("nro_rut_dv").to_pylist(), ["97006000-6"])

    def test_columna_dv_toda_nula(self):
        """Un `nro_rut_dv` vacío creado por el esquema del publicador debe rellenarse."""
        df = pd.DataFrame({"nro_rut": ["97006000-6"], "nro_rut_dv": [None]})
        t, _ = normalizar_tabla(self._tabla(df))
        self.assertEqual(t.column_names.count("nro_rut_dv"), 1)
        self.assertEqual(t.column("nro_rut_dv").to_pylist(), ["97006000-6"])

    def test_posicion_de_la_columna_nueva(self):
        """El publicador inserta nro_rut_dv tras nro_rut; la normalización no debe
        crear una segunda columna al final."""
        df = pd.DataFrame({"nro_rut": ["97006000-6"], "otra": [1]})
        t, _ = normalizar_tabla(self._tabla(df))
        self.assertEqual(len([c for c in t.column_names if c == "nro_rut_dv"]), 1)
        self.assertEqual(t.column("otra").to_pylist(), [1])

    def test_dataframe_idempotente(self):
        df = pd.DataFrame({"nro_rut": ["97006000-6", "76015592-K", None]})
        una = normalizar_dataframe(df)
        dos = normalizar_dataframe(una)
        self.assertTrue(una.equals(dos))
        self.assertEqual(una["nro_rut"].tolist()[0], "97006000")
        self.assertEqual(una["nro_rut_dv"].tolist()[1], "76015592-K")


if __name__ == "__main__":
    unittest.main()

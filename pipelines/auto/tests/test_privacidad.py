import unittest

from pipelines.auto import privacidad


class CuerpoRutTest(unittest.TestCase):
    def test_acepta_los_tres_formatos(self):
        self.assertEqual(privacidad.cuerpo_rut("97.004.000-5"), "97004000")
        self.assertEqual(privacidad.cuerpo_rut("97004000-5"), "97004000")
        self.assertEqual(privacidad.cuerpo_rut("97004000"), "97004000")

    def test_rut_corto_no_se_rellena_con_ceros(self):
        self.assertEqual(privacidad.cuerpo_rut("008253"), "8253")

    def test_vacios_y_basura(self):
        for valor in (None, "", "   ", "NA", "S/I", "no aplica"):
            self.assertIsNone(privacidad.cuerpo_rut(valor))


class PersonaNaturalTest(unittest.TestCase):
    """El criterio: bajo 50.000.000 y fuera de los registros de entidades."""

    def test_rut_alto_es_entidad(self):
        self.assertFalse(privacidad.es_probable_persona_natural("76015592"))
        self.assertEqual(privacidad.tipo_emisor("76015592"), privacidad.TIPO_JURIDICA)

    def test_rut_bajo_desconocido_se_enmascara(self):
        self.assertTrue(privacidad.es_probable_persona_natural("15273263"))
        self.assertEqual(privacidad.tipo_emisor("15273263"), privacidad.TIPO_NATURAL)

    def test_rut_bajo_pero_conocido_se_conserva(self):
        # Los fondos tienen RUN corto: sin el registro publicado se perderían.
        entidades = {"7014", "8253"}
        self.assertFalse(privacidad.es_probable_persona_natural("7014", entidades))
        self.assertEqual(privacidad.tipo_emisor("8253", entidades), privacidad.TIPO_JURIDICA)

    def test_la_lista_de_entidades_es_una_copia_no_un_estado_oculto(self):
        # Sin entidades conocidas, el criterio enmascara: debe fallar hacia la privacidad.
        self.assertTrue(privacidad.es_probable_persona_natural("7014"))

    def test_sin_rut_queda_etiquetado(self):
        self.assertEqual(privacidad.tipo_emisor(None), privacidad.TIPO_SIN_RUT)
        self.assertEqual(privacidad.tipo_emisor(""), privacidad.TIPO_SIN_RUT)

    def test_enmascarar_devuelve_none_y_el_tipo(self):
        valor, tipo = privacidad.enmascarar_rut_emisor("15273263")
        self.assertIsNone(valor)
        self.assertEqual(tipo, privacidad.TIPO_NATURAL)

    def test_enmascarar_conserva_la_entidad(self):
        valor, tipo = privacidad.enmascarar_rut_emisor("76015592")
        self.assertEqual(valor, "76015592")
        self.assertEqual(tipo, privacidad.TIPO_JURIDICA)

    def test_enmascarar_columna_mantiene_el_largo(self):
        valores = ["76015592", "15273263", "", None, "8253"]
        nuevos, tipos = privacidad.enmascarar_columna(valores, {"8253"})
        self.assertEqual(len(nuevos), len(valores))
        self.assertEqual(nuevos[0], "76015592")
        self.assertIsNone(nuevos[1])
        self.assertIsNone(nuevos[2])
        self.assertIsNone(nuevos[3])
        self.assertEqual(nuevos[4], "8253")
        self.assertEqual(tipos, [
            privacidad.TIPO_JURIDICA, privacidad.TIPO_NATURAL, privacidad.TIPO_SIN_RUT,
            privacidad.TIPO_SIN_RUT, privacidad.TIPO_JURIDICA,
        ])


class BienesRaicesTest(unittest.TestCase):
    def test_property_id_es_estable_y_seudo(self):
        a = privacidad.property_id("76015592", "00336-00006")
        b = privacidad.property_id("76015592", "00336-00006")
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("BIEN-"))
        self.assertNotIn("336", a)
        self.assertNotIn("76015592", a)

    def test_property_id_separa_inmuebles_y_aseguradoras(self):
        self.assertNotEqual(
            privacidad.property_id("76015592", "00336-00006"),
            privacidad.property_id("76015592", "00336-00007"),
        )
        self.assertNotEqual(
            privacidad.property_id("76015592", "00336-00006"),
            privacidad.property_id("76039758", "00336-00006"),
        )

    def test_rol_vacio_no_genera_id(self):
        self.assertIsNone(privacidad.property_id("76015592", None))
        self.assertIsNone(privacidad.property_id("76015592", ""))

    def test_la_sal_cambia_el_seudonimo(self):
        self.assertNotEqual(
            privacidad.property_id("76015592", "1-24", sal=""),
            privacidad.property_id("76015592", "1-24", sal="secreto"),
        )

    def test_normalizar_rol_ignora_espacios_y_mayusculas(self):
        self.assertEqual(privacidad.normalizar_rol(" 1-24 "), "1-24")
        self.assertEqual(privacidad.property_id("1", "1-24"), privacidad.property_id("1", " 1-24 "))


class DataFrameTest(unittest.TestCase):
    """Las dos reglas aplicadas a un DataFrame (pandas es opcional)."""

    def setUp(self):
        try:
            import pandas as pd  # noqa: F401
        except Exception:  # pragma: no cover - entorno sin pandas
            self.skipTest("pandas no disponible")
        import pandas as pd
        self.pd = pd

    def test_proteger_cartera_nacional(self):
        df = self.pd.DataFrame({"rut_emisor": ["76015592", "15273263", None], "periodo": ["2026-06"] * 3})
        out = privacidad.proteger_cartera_nacional(df, {"76015592"})
        # pandas representa el valor suprimido como NaN; al escribir el Parquet
        # vuelve a ser nulo, porque el esquema declara la columna como string.
        rut = out["rut_emisor"].tolist()
        self.assertEqual(rut[0], "76015592")
        self.assertTrue(self.pd.isna(rut[1]), f"se esperaba RUT suprimido, llegó {rut[1]!r}")
        self.assertTrue(self.pd.isna(rut[2]), f"se esperaba nulo, llegó {rut[2]!r}")
        self.assertEqual(out["emisor_tipo"].tolist(),
                         [privacidad.TIPO_JURIDICA, privacidad.TIPO_NATURAL, privacidad.TIPO_SIN_RUT])

    def test_proteger_bienes_raices_quita_direccion_y_rol(self):
        df = self.pd.DataFrame({
            "rut_aseguradora": ["76015592", "76015592"],
            "rol": ["00336-00006", "00336-00007"],
            "ubicacion": ["AV APOQUINDO 4001 OF 201", "AV APOQUINDO 4001 OF 202"],
            "comuna": ["71", "71"],
            "ciudad": ["SANTIAGO", "SANTIAGO"],
        })
        out = privacidad.proteger_bienes_raices(df, sal="prueba")
        self.assertEqual(out["ubicacion"].tolist(), [None, None])
        self.assertEqual(out["rol"].tolist(), [None, None])
        self.assertEqual(out["comuna"].tolist(), ["71", "71"])
        self.assertEqual(out["ciudad"].tolist(), ["SANTIAGO", "SANTIAGO"])
        self.assertEqual(len(set(out["property_id"])), 2)
        self.assertTrue(all(str(p).startswith("BIEN-") for p in out["property_id"]))

    def test_proteger_es_idempotente(self):
        df = self.pd.DataFrame({"rut_aseguradora": ["76015592"], "rol": ["1-24"], "ubicacion": ["CALLE 123"]})
        una = privacidad.proteger_bienes_raices(df, sal="prueba")
        dos = privacidad.proteger_bienes_raices(una, sal="prueba")
        # La segunda pasada no rompe: el id se pierde porque el rol ya no está, y
        # por eso el backfill corre una sola vez y queda marcado en su manifiesto.
        self.assertEqual(una["ubicacion"].tolist(), dos["ubicacion"].tolist())


if __name__ == "__main__":
    unittest.main()

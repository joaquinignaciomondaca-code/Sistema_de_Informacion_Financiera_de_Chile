"""Importes legibles en la sección de Banca (B1/B2/R1).

Cubre las tres piezas que se agregaron para que el Visor muestre un monto y no
el campo crudo del archivo CMF:

  * `importe_normalizado` del extractor y `calcular` del normalizador tienen que
    dar el mismo número y el mismo marcador de formato;
  * el maestro publica un único formato de RUT (`rut_dv` = `rut`-DV, sin puntos);
  * el cotejo publicado no deja ninguna fila fuera del registro de la CMF.
"""
import json
import unittest
from pathlib import Path

from bancos.scripts.extract_cmf_bank_lines import importe_normalizado
from bancos.scripts.normalizar_importes import calcular
from bancos.scripts.corregir_identidades import con_dv

ROOT = Path(__file__).resolve().parents[2]
BANCOS = ROOT / "docs" / "outputs" / "bancos"
MAESTRO = BANCOS / "bancos_maestro.json"
COTEJO = BANCOS / "identidades_cmf.json"

# Una fila de cada mitad de la serie, con el valor ya verificado contra el XLSX
# de la CMF en `bancos/ESQUEMA_CMF_B1_B2_R1.md`.
CASOS = [
    # (exactos, raw, importe esperado, formato esperado)
    (["1542552118136"], ["001542552118136"], 1542552118136, "entero_15"),
    (["26458735676131"], ["26458735676131,00"], 26458735676131, "decimal_coma"),
    (["-1"], ["-0000000000001"], -1, "entero_15"),
    (["0", "0", "0", "0"], ["000000000000000"] * 4, 0, "entero_15"),
    (
        ["26458735676131", "18194231752989", "86353276604", "5425082730722"],
        ["26458735676131,00", "18194231752989,00", "0086353276604,00", "5425082730722,00"],
        50164403436446,
        "decimal_coma",
    ),
]


class ImporteNormalizadoTests(unittest.TestCase):
    def test_extractor_y_normalizador_coinciden(self):
        for exactos, raw, importe, formato in CASOS:
            with self.subTest(raw=raw):
                self.assertEqual(
                    importe_normalizado(exactos, raw),
                    {"importe_clp": importe, "formato_monto_fuente": formato},
                )
                self.assertEqual(calcular(exactos, raw), (importe, formato))

    def test_los_ceros_a_la_izquierda_no_cambian_el_monto(self):
        # `001542552118136` es $1.542.552.118.136, no 154.255.211.813.600.
        self.assertEqual(importe_normalizado(["1542552118136"], ["001542552118136"])["importe_clp"],
                         1542552118136)

    def test_la_suma_de_las_cuatro_monedas_es_el_total_de_la_cuenta(self):
        exactos, raw = CASOS[-1][0], CASOS[-1][1]
        self.assertEqual(importe_normalizado(exactos, raw)["importe_clp"], sum(int(v) for v in exactos))


class FormatoRutDelMaestroTests(unittest.TestCase):
    def test_rut_dv_sin_puntos_y_igual_a_rut_mas_dv(self):
        for fila in json.loads(MAESTRO.read_text(encoding="utf-8")):
            with self.subTest(codigo=fila["codigo_institucion"]):
                self.assertNotIn(".", fila["rut"])
                self.assertNotIn(".", fila["rut_dv"])
                self.assertTrue(fila["rut_dv"].startswith(fila["rut"] + "-"))

    def test_con_dv_no_reintroduce_puntos(self):
        self.assertEqual(con_dv("97003000", "K"), "97003000-K")


class CotejoPublicadoTests(unittest.TestCase):
    def setUp(self):
        self.cotejo = json.loads(COTEJO.read_text(encoding="utf-8"))

    def test_ninguna_fila_queda_fuera_del_registro(self):
        self.assertEqual(self.cotejo["resumen"]["por_cotejo"].get("no_en_registro", 0), 0)

    def test_el_resumen_cuadra_con_las_filas(self):
        resumen = self.cotejo["resumen"]
        self.assertEqual(resumen["filas"], len(self.cotejo["filas"]))
        self.assertEqual(sum(resumen["por_cotejo"].values()), resumen["filas"])
        self.assertEqual(resumen["por_cotejo"], {"agregado_sectorial": 7, "cotejado": 30, "declarado": 4})


if __name__ == "__main__":
    unittest.main()

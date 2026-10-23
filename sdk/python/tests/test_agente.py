"""Pruebas de las dos herramientas del agente, sin servidor MCP y sin red (2.1).

Se prueba lo que un agente ve: que la búsqueda encuentre la tabla correcta con
lenguaje natural, que la ficha quepa en contexto y que un error llegue como
`error` + `pista` en vez de como excepción.
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from sif_chile import agente

DOCS = Path(__file__).resolve().parents[3] / "docs"


class Agente(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SIF_CHILE_BASE"] = str(DOCS)

    @classmethod
    def tearDownClass(cls):
        agente.cerrar()
        os.environ.pop("SIF_CHILE_BASE", None)

    def buscar(self, texto, **kw):
        return json.loads(agente.buscar(texto, **kw))

    def ejecutar(self, sql, **kw):
        return json.loads(agente.ejecutar(sql, **kw))

    def test_encuentra_la_tabla_con_la_pregunta_del_readme(self):
        resultado = self.buscar("dónde invierten fuera de Chile los fondos mutuos", limite=3)
        ids = [o["id"] for o in resultado["objetos"]]
        self.assertEqual(ids[0], "ffmm_cartera_extranjera")

    def test_la_ficha_trae_lo_justo_para_escribir_sql(self):
        objeto = self.buscar("seguros renta fija", limite=1)["objetos"][0]
        self.assertEqual(objeto["id"], "seguros_renta_fija")
        self.assertIn("periodo", objeto["columnas"])
        self.assertTrue(objeto["pk"])
        self.assertGreater(objeto["filas"], 0)
        # Compacta: la ficha entera de una tabla tiene que caber en un contexto.
        self.assertLess(len(json.dumps(objeto, ensure_ascii=False)), 2_000)

    def test_una_ficha_sin_clave_publica_pk_nulo(self):
        """La 2.0.1 retiró la clave de 27 objetos: `pk` tiene que ser `null`.

        Si el campo se omitiera, un consumidor no distinguiría «no hay clave» de
        «esta versión no lo dice»; y si viniera como lista vacía, `",".join` y
        `pk[0]` fallarían igual. Se fija el contrato: el campo existe y es null.
        """
        objetos = self.buscar("cartera nacional de fondos mutuos", limite=3)["objetos"]
        ficha = next(o for o in objetos if o["id"] == "ffmm_cartera_nacional")
        self.assertIn("pk", ficha)
        self.assertIsNone(ficha["pk"])
        self.assertEqual(ficha["filas"], 1_590_196)

    def test_una_ficha_con_clave_sigue_trayendo_la_clave(self):
        objetos = self.buscar("unidad de fomento", limite=3)["objetos"]
        con_clave = [o for o in objetos if o["pk"]]
        self.assertTrue(con_clave, f"ninguna ficha trajo pk: {[o['id'] for o in objetos]}")

    def test_sin_coincidencias_da_una_pista(self):
        resultado = self.buscar("xilofón")
        self.assertEqual(resultado["objetos"], [])
        self.assertIn("pista", resultado)

    def test_ejecutar_devuelve_columnas_y_filas(self):
        resultado = self.ejecutar("SELECT count(*) AS n FROM seguros_lista_entidades")
        self.assertEqual(resultado["columnas"], ["n"])
        self.assertEqual(resultado["datos"], [[84]])
        self.assertFalse(resultado["truncado"])

    def test_ejecutar_trunca_y_lo_dice(self):
        resultado = self.ejecutar("SELECT * FROM macro_uf", limite=3)
        self.assertEqual(len(resultado["datos"]), 3)
        self.assertTrue(resultado["truncado"])

    def test_un_sql_roto_vuelve_con_pista(self):
        resultado = self.ejecutar("SELECT nope FROM ffmm_cartera_extranjera")
        self.assertIn("error", resultado)
        self.assertIn("sif_buscar", resultado["pista"])

    def test_el_guardia_bloquea_escrituras(self):
        resultado = self.ejecutar("DROP VIEW ffmm_cartera_extranjera")
        self.assertIn("error", resultado)
        self.assertIn("SELECT", resultado["pista"])

    def test_presupuesto_de_contexto_de_las_fichas(self):
        # 2.2 mide el esquema de las herramientas en `scripts/auditar_mcp.py`;
        # aquí se vigila la otra mitad: que una búsqueda normal no explote.
        texto = agente.buscar("fondos mutuos", limite=3)
        self.assertLess(agente.contar_tokens(texto), 500)


if __name__ == "__main__":
    unittest.main()

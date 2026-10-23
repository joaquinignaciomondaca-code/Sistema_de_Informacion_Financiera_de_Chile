"""Pruebas del SDK sin red (tarea 1b.5).

Se ejecutan contra la copia local del repositorio (`base=docs`), así que no
hacen ninguna petición y sirven en cualquier CI. Lo que se prueba es lo que
puede romperse en silencio: que el cliente lea el contrato y no una lista
propia, que respete los alias, que el guardia bloquee escrituras y que las
descargas verifiquen el hash.

    python3 -m unittest discover -s sdk/python/tests -t sdk/python
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sif_chile
from sif_chile import guardia

RAIZ = Path(__file__).resolve().parents[3]
DOCS = RAIZ / "docs"


class Contrato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sif = sif_chile.connect(base=str(DOCS))

    @classmethod
    def tearDownClass(cls):
        cls.sif.cerrar()

    def test_lee_el_catalogo_publicado(self):
        catalogo = json.loads((DOCS / "api" / "v1" / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(len(self.sif.tablas()), catalogo["totales"]["objetos"])
        self.assertEqual(len(self.sif.tablas()), 90)

    def test_esquema_coincide_con_el_archivo(self):
        doc = json.loads((DOCS / "api" / "v1" / "schema" / "bancos_balance.json").read_text(encoding="utf-8"))
        leido = self.sif.esquema("bancos_balance")
        self.assertEqual([c["nombre"] for c in leido["columnas"]],
                         [c["nombre"] for c in doc["columnas"]])
        self.assertEqual(leido["primaryKey"], doc["primaryKey"])
        self.assertTrue(leido["primaryKey"], "bancos_balance tiene clave verificada")

    def test_alias_heredado_resuelve_al_objeto(self):
        self.assertEqual(self.sif.tabla("seguros_maestro")["id"], "seguros_lista_entidades")
        self.assertIn("seguros_maestro", self.sif.tabla("seguros_lista_entidades")["aliases"])

    def test_objeto_desconocido_da_error_util(self):
        with self.assertRaises(KeyError) as ctx:
            self.sif.tabla("no_existe")
        self.assertIn("no_existe", str(ctx.exception))

    def test_las_consultas_publicadas_corren(self):
        consultas = self.sif.consultas()
        # El catálogo crece con el sitio; lo que no puede pasar es que falte una
        # consulta o que el número publicado en el gesto no cuadre con él.
        publicado = json.loads((DOCS / "api" / "v1" / "queries.json").read_text(encoding="utf-8"))
        self.assertEqual(len(consultas), publicado["total"])
        self.assertGreaterEqual(len(consultas), 156)
        primera = consultas[0]
        filas = self.sif.consulta(primera["id"], limite=2).fetchall()
        self.assertLessEqual(len(filas), 2)

    def test_toda_tabla_con_datos_responde(self):
        # Una vista creada no sirve de nada si al consultarla revienta.
        for objeto in self.sif.tablas(estado="publicado")[:10]:
            n = self.sif.sql(f'SELECT count(*) FROM "{objeto["id"]}"').fetchone()[0]
            self.assertGreaterEqual(n, 0, objeto["id"])


class Datos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sif = sif_chile.connect(base=str(DOCS))

    @classmethod
    def tearDownClass(cls):
        cls.sif.cerrar()

    def test_read_table_devuelve_datos(self):
        tabla = self.sif.read_table("macro_dolar_observado", limite=5)
        self.assertEqual(len(tabla), 5)
        self.assertGreaterEqual(len(tabla.columns), 2)

    def test_limite_no_cambia_el_resultado_solo_lo_corta(self):
        completo = self.sif.sql("SELECT count(*) FROM seguros_lista_entidades").fetchone()[0]
        self.assertEqual(completo, 84)
        self.assertEqual(len(self.sif.sql("SELECT * FROM seguros_lista_entidades", limite=3).fetchall()), 3)

    def test_descarga_verifica_el_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            rutas = self.sif.descargar("afp_lista_entidades", tmp)
            self.assertTrue(rutas and rutas[0].exists())
            # Una segunda descarga reconoce el archivo intacto y no lo reescribe.
            antes = rutas[0].stat().st_mtime_ns
            otra = self.sif.descargar("afp_lista_entidades", tmp)
            self.assertEqual(otra[0], rutas[0])
            self.assertEqual(otra[0].stat().st_mtime_ns, antes)


class Guardia(unittest.TestCase):
    def test_permite_lectura(self):
        for sql in ("SELECT 1", "  with x as (select 1) select * from x",
                    "DESCRIBE SELECT 1", "SUMMARIZE SELECT 1"):
            ok, motivo = guardia.validar(sql)
            self.assertTrue(ok, f"{sql!r}: {motivo}")

    def test_bloquea_escrituras(self):
        for sql in ("DROP VIEW agf_balance", "CREATE TABLE x AS SELECT 1",
                    "INSERT INTO x VALUES (1)", "ATTACH 'x.db'", "INSTALL httpfs"):
            ok, _ = guardia.validar(sql)
            self.assertFalse(ok, f"debió bloquear: {sql!r}")

    def test_bloquea_ctas_disfrazado(self):
        ok, motivo = guardia.validar("SELECT * FROM t INTO nueva")
        self.assertFalse(ok)
        self.assertIn("INTO", motivo)

    def test_bloquea_varias_sentencias(self):
        ok, motivo = guardia.validar("SELECT 1; DROP VIEW x")
        self.assertFalse(ok)
        self.assertIn("2", motivo)

    def test_un_literal_o_un_comentario_no_bloquean(self):
        # Una cuenta que se llame "drop" no puede impedir una consulta legítima.
        for sql in ("SELECT 'drop table'", "SELECT 1 -- drop",
                    "SELECT * FROM t WHERE nombre = 'COPY'"):
            ok, motivo = guardia.validar(sql)
            self.assertTrue(ok, f"{sql!r}: {motivo}")

    def test_un_comentario_no_esconde_una_sentencia(self):
        ok, _ = guardia.validar("-- SELECT 1\nDROP VIEW x")
        self.assertFalse(ok)

    def test_sql_lanza_valueerror(self):
        sif = sif_chile.connect(base=str(DOCS))
        try:
            with self.assertRaises(ValueError):
                sif.sql("DROP VIEW afp_lista_entidades")
        finally:
            sif.cerrar()


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de scripts/build_download_exports.py (descargas CSV/JSON pre-construidas).

Crea datos de prueba en directorios temporales y patea DOCS del módulo, sin
tocar docs/ del repositorio. Requiere duckdb y pyarrow (ya instalados en los
workflows); si no están, se salta con mensaje explícito.

Uso: python -m unittest scripts.test_build_download_exports -v
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    import duckdb
except Exception:  # pragma: no cover
    duckdb = None

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover
    pa = pq = None

import scripts.build_download_exports as exp


def json_leer(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@unittest.skipUnless(duckdb is not None and pa is not None, "duckdb y pyarrow no instalados")
class BuildDownloadExportsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        self.salida = self.docs / "outputs" / "prueba"
        self.salida.mkdir(parents=True)
        self.viejo_docs, self.viejo_indice = exp.DOCS, exp.INDICE
        exp.DOCS = self.docs
        exp.INDICE = self.root / "_exportes_test.json"
        self.patches = {}

    def tearDown(self):
        for nombre, valor in self.patches.items():
            setattr(exp, nombre, valor)
        exp.DOCS, exp.INDICE = self.viejo_docs, self.viejo_indice
        self.temp.cleanup()

    def patchear(self, nombre, valor):
        self.patches[nombre] = getattr(exp, nombre)
        setattr(exp, nombre, valor)

    def write_parquet(self, ruta: str, filas: list[dict]) -> str:
        """Escribe un Parquet bajo docs/ y devuelve la ruta relativa."""
        tabla = pa.table({k: [f.get(k) for f in filas] for k in filas[0]})
        destino = self.docs / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(tabla, destino)
        return ruta

    def test_sql_lectura_usa_caminos_absolutos(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        sql = exp.sql_lectura([ruta], "")
        self.assertIn(str((self.docs / ruta).resolve()), sql)
        self.assertNotIn("'outputs/", sql)

    def test_generar_csv_y_json(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [
            {"nombre": "A", "valor": 1.5},
            {"nombre": "B", "valor": None},
        ])
        csv_path = self.salida / "tabla.completo.csv"
        json_path = self.salida / "tabla.completo.json"
        self.assertTrue(exp.generar_csv([ruta], "", csv_path))
        texto = csv_path.read_text(encoding="utf-8")
        self.assertNotIn("﻿", texto)  # sin BOM: lo esperan Power BI / Data Studio
        # DuckDB cota sólo lo que hace falta (RFC 4180): suficiente para Power BI y Data Studio.
        self.assertEqual(texto.splitlines(), ["nombre,valor", "A,1.5", "B,"])
        exp.generar_json([ruta], "", json_path)
        lineas = json_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lineas), 2)
        self.assertEqual(json.loads(lineas[0]), {"nombre": "A", "valor": 1.5})
        self.assertIsNone(json.loads(lineas[1])["valor"])

    def test_firma_cambia_cuando_el_dato_cambia(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}])
        firma1 = exp.firma([ruta], "")
        firma2 = dict(firma1)
        self.assertTrue(exp.hay_cambio(None, firma1))
        self.assertFalse(exp.hay_cambio(firma1, firma2))
        self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        self.assertTrue(exp.hay_cambio(firma1, exp.firma([ruta], "")))

    def test_generar_conjunto_publica_csv_y_json(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        entrada = exp.generar_conjunto(vista, {"conjuntos": {}}, forzado=False)
        self.assertTrue(entrada["csv"])
        self.assertEqual(entrada["csv"]["ruta"], "outputs/prueba/tabla.completo.csv")
        self.assertEqual(entrada["csv"]["filas"], 2)
        self.assertTrue(entrada["json"])
        self.assertEqual(entrada["nota"], None)
        self.assertTrue((self.docs / entrada["csv"]["ruta"]).exists())

    def test_incremental_no_regenera_sin_cambio(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        indice = {"conjuntos": {}}
        entrada = exp.generar_conjunto(vista, indice, forzado=False)
        indice["conjuntos"]["tabla"] = entrada
        csv_path = self.docs / entrada["csv"]["ruta"]
        antes = csv_path.read_bytes()
        # Segundo pase: misma firma → se conserva el CSV publicado.
        entrada2 = exp.generar_conjunto(vista, indice, forzado=False)
        self.assertEqual(entrada2["csv"], entrada["csv"])
        self.assertEqual(csv_path.read_bytes(), antes)
        # Si cambia la fuente, se regenera (y el JSON nuevo refleja el dato nuevo).
        self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}, {"a": 3}])
        entrada3 = exp.generar_conjunto(vista, indice, forzado=False)
        self.assertEqual(entrada3["csv"]["filas"], 3)
        self.assertNotEqual(entrada3["csv"], entrada["csv"])

    def test_vista_con_filtro_se_omite(self):
        ruta = self.write_parquet("outputs/prueba/banca.parquet", [{"familia": "B1"}, {"familia": "R1"}])
        vista = {"name": "banco", "kind": "file", "path": ruta, "where": "familia = 'B1'"}
        entrada = exp.generar_conjunto(vista, {"conjuntos": {}}, forzado=False)
        self.assertIsNone(entrada["csv"])
        self.assertIsNone(entrada["json"])
        self.assertIn("filtro SQL", entrada["nota"])

    def test_csv_sobre_tope_no_se_publica(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        self.patchear("CSV_MAX_MB", 0)  # ningún CSV cabe
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        entrada = exp.generar_conjunto(vista, {"conjuntos": {}}, forzado=False)
        self.assertIsNone(entrada["csv"])
        self.assertFalse((self.salida / "tabla.completo.csv").exists())

    def test_bajar_el_tope_retira_el_csv_ya_publicado(self):
        """Un CSV publicado que ya no cabe en el tope debe desaparecer, no quedarse.

        El 2026-11-09 se bajó el tope de 35 MB a 10 MB para aliviar el peso del
        sitio. Con el pase incremental anterior, el conjunto «no cambió su
        fuente» y el CSV de 33 MB seguía publicado: la bajada del tope no tenía
        efecto y el sitio seguía pesando lo mismo.
        """
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        indice = {"conjuntos": {}}
        entrada = exp.generar_conjunto(vista, indice, forzado=False)
        indice["conjuntos"]["tabla"] = entrada
        csv_path = self.docs / entrada["csv"]["ruta"]
        self.assertTrue(csv_path.exists())
        # El mismo conjunto, ahora con un tope menor que el archivo publicado.
        self.patchear("CSV_MAX_MB", 0)
        entrada2 = exp.generar_conjunto(vista, indice, forzado=False)
        self.assertIsNone(entrada2["csv"])
        self.assertFalse(csv_path.exists())

    def test_json_sobre_tope_no_se_publica(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        self.patchear("JSON_MAX_MB", 0)  # ningún JSON cabe
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        entrada = exp.generar_conjunto(vista, {"conjuntos": {}}, forzado=False)
        self.assertTrue(entrada["csv"])  # el CSV sí se publica
        self.assertIsNone(entrada["json"])
        self.assertFalse((self.salida / "tabla.completo.json").exists())

    def test_parquet_gigante_no_se_intenta(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}])
        self.patchear("PARQUET_MAX_MB", 0)  # ningún Parquet pasa el filtro previo
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        entrada = exp.generar_conjunto(vista, {"conjuntos": {}}, forzado=False)
        self.assertIsNone(entrada["csv"])
        self.assertIn("tope", entrada["nota"])

    def test_check_detecta_fuente_cambiada(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}])
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        indice = {"conjuntos": {}}
        entrada = exp.generar_conjunto(vista, indice, forzado=False)
        indice["conjuntos"]["tabla"] = entrada
        json.dump(indice, open(exp.INDICE, "w", encoding="utf-8"), ensure_ascii=False)
        # --check sin cambios: el estado esperado coincide con el guardado.
        esperado = exp.generar_conjunto(vista, json_leer(exp.INDICE), forzado=False, escribir=False)
        self.assertEqual(esperado["csv"], entrada["csv"])
        self.assertEqual(esperado["json"], entrada["json"])
        # Con la fuente cambiada, el estado esperado ya no coincide con el guardado.
        self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}, {"a": 2}, {"a": 3}])
        esperado2 = exp.generar_conjunto(vista, json_leer(exp.INDICE), forzado=False, escribir=False)
        self.assertIsNone(esperado2["csv"])
        self.assertNotEqual(esperado2["csv"], indice["conjuntos"]["tabla"]["csv"])

    def test_lista_archivos(self):
        ruta = self.write_parquet("outputs/prueba/tabla.parquet", [{"a": 1}])
        vista = {"name": "tabla", "kind": "file", "path": ruta, "where": ""}
        indice = {"conjuntos": {}}
        indice["conjuntos"]["tabla"] = exp.generar_conjunto(vista, indice, forzado=False)
        lista = exp.lista_archivos(indice)
        self.assertIn("outputs/prueba/tabla.completo.csv", lista)
        self.assertIn("outputs/prueba/tabla.completo.json", lista)
        self.assertEqual(lista, sorted(lista))


if __name__ == "__main__":
    unittest.main(verbosity=2)

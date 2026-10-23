"""La búsqueda de claves no puede inventar una clave única.

El 2026-10-23 se descubrió que `docs/api/claves.csv` declaraba una clave
primaria única para 13 objetos que tienen filas idénticas publicadas —entre
ellos `ffmm_cartera_nacional`, con 160.564 filas repetidas—. La causa estaba en
`scripts/verificar_claves.py`: marcaba las filas repetidas con

    WHERE (a, b, c) IN (SELECT a, b, c FROM … GROUP BY … HAVING count(*) > 1)

y en DuckDB esa tupla **no** se compara fila a fila: se lee como un valor
compuesto y devuelve un conjunto que no es el de las repetidas. Cuando salía
vacío se interpretaba como «no hay duplicados» y la clave se daba por buena.
El CSV, además, copiaba `filas` en la columna `distintas`, así que ni siquiera
podía contradecirse.

Estas pruebas fijan las dos cosas: la búsqueda sólo declara única una
combinación medida sobre todas las filas, y el informe publica esa medición.
"""
from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("verificar_claves", RAIZ / "scripts" / "verificar_claves.py")
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)


class BuscarClaveTests(unittest.TestCase):
    def setUp(self):
        import duckdb

        self.con = duckdb.connect()

    def tearDown(self):
        self.con.close()

    def _tabla(self, filas):
        """Tabla de prueba con las columnas que usan los casos."""
        columnas = list(filas[0])
        valores = ", ".join(
            "(" + ", ".join("NULL" if f[c] is None else repr(f[c]) for c in columnas) + ")"
            for f in filas
        )
        self.con.execute(f"CREATE OR REPLACE TABLE t AS SELECT * FROM (VALUES {valores}) v("
                         + ", ".join(f'"{c}"' for c in columnas) + ")")
        return columnas

    def test_no_declara_unica_una_clave_con_filas_repetidas(self):
        """El caso que falló: la fila completa se repite y la clave corta no alcanza.

        `buscar_clave` recibe `limite` menor que el número de columnas para
        forzar la segunda fase, que es donde estaba el error.
        """
        columnas = self._tabla([
            {"a": "1", "b": "x", "c": "p"},
            {"a": "1", "b": "x", "c": "p"},   # idéntica a la anterior
            {"a": "2", "b": "y", "c": "q"},
        ])
        clave, unica = vc.buscar_clave(self.con, "t", columnas, 3, limite=1)
        self.assertFalse(unica, f"declaró única una clave falsa: {clave}")
        self.assertFalse(vc.es_unica(self.con, "t", clave, 3))

    def test_un_nulo_en_la_clave_no_esconde_las_filas_repetidas(self):
        """La trampa exacta de `ffmm_cartera_nacional`.

        Su clave propuesta incluía columnas que llegan nulas (`fecha_vencimiento`,
        `tir_pct`). Con un NULL en la tupla, `(a, b) IN (SELECT a, b …)` devuelve
        el conjunto vacío —DuckDB compara la tupla como un valor compuesto— y el
        vacío se leía como «no hay repetidas»: así se publicó una clave que no lo
        era en 13 objetos. Esta prueba fija que un NULL no cambia la respuesta.
        """
        columnas = self._tabla([
            {"a": "1", "b": None, "c": "p"},
            {"a": "1", "b": None, "c": "p"},   # idéntica a la anterior
            {"a": "2", "b": "y", "c": "q"},
        ])
        self.assertFalse(vc.es_unica(self.con, "t", columnas, 3))
        # limite=2 para llegar a la segunda fase con una tupla de dos columnas
        # —la forma exacta que fallaba— y no con una sola.
        clave, unica = vc.buscar_clave(self.con, "t", columnas, 3, limite=2)
        self.assertFalse(unica, f"declaró única una clave falsa con NULL: {clave}")

    def test_una_clave_real_se_encuentra(self):
        columnas = self._tabla([
            {"a": "1", "b": "x", "c": "p"},
            {"a": "2", "b": "x", "c": "p"},
            {"a": "3", "b": "y", "c": "q"},
        ])
        clave, unica = vc.buscar_clave(self.con, "t", columnas, 3, limite=1)
        self.assertTrue(unica)
        self.assertTrue(vc.es_unica(self.con, "t", clave, 3))
        self.assertEqual(len(clave), 1, "la clave mínima era una sola columna")

    def test_la_fila_completa_repetida_no_es_clave(self):
        columnas = self._tabla([
            {"a": "1", "b": "x"},
            {"a": "1", "b": "x"},
        ])
        clave, unica = vc.buscar_clave(self.con, "t", columnas, 2)
        self.assertFalse(unica)
        self.assertFalse(vc.es_unica(self.con, "t", columnas, 2))

    def test_es_unica_cuenta_las_filas_y_no_las_columnas(self):
        columnas = self._tabla([
            {"a": "1", "b": None},
            {"a": "1", "b": None},
            {"a": "2", "b": None},
        ])
        self.assertFalse(vc.es_unica(self.con, "t", columnas, 3))
        self.assertTrue(vc.es_unica(self.con, "t", columnas, 2))


class InformeTests(unittest.TestCase):
    """El CSV no puede afirmar una unicidad que no midió."""

    def test_las_propuestas_llevan_la_medicion_y_no_el_total(self):
        csv_path = RAIZ / "docs" / "api" / "claves.csv"
        if not csv_path.exists():
            self.skipTest("sin claves.csv")
        with csv_path.open(encoding="utf-8", newline="") as fh:
            filas = [f for f in csv.DictReader(fh) if f["tipo"] == "pk"]
        for fila in filas:
            if fila["estado"] in ("propuesta", "ok"):
                self.assertEqual(
                    int(fila["filas"]) - int(fila["distintas"]), int(fila["sobrantes"]),
                    f"{fila['objeto']}: el informe no cuadra consigo mismo",
                )
                if fila["estado"] == "propuesta":
                    self.assertEqual(int(fila["sobrantes"]), 0,
                                     f"{fila['objeto']}: una clave propuesta no puede tener sobrantes")


if __name__ == "__main__":
    unittest.main()

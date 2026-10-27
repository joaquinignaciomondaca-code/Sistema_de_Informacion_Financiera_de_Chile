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


class ContraLaMedicionIndependienteTests(unittest.TestCase):
    """`buscar_clave` contra la verdad medida por otro camino.

    La prueba de mutación del 2026-10-23 mostró que reponer la búsqueda rota
    dejaba en verde cinco de las seis pruebas: cubrían el caso escrito a mano,
    no el comportamiento. Estas pruebas generan tablas con repetición y nulos y
    comparan la respuesta con un `SELECT DISTINCT` —que no usa ventanas ni la
    lógica del módulo—, así que cualquier atajo que vuelva a declarar única una
    combinación con repetidas falla aquí.
    """

    def setUp(self):
        import duckdb

        self.con = duckdb.connect()

    def tearDown(self):
        self.con.close()

    def _aleatoria(self, semilla, columnas=3, filas=120, dominio=6, nulos=0.2):
        """Tabla con repetición y NULL, para que la clave corta no sea trivial."""
        import random

        rnd = random.Random(semilla)
        nombres = [f"c{i}" for i in range(columnas)]
        datos = [
            [None if rnd.random() < nulos else f"v{rnd.randrange(dominio)}" for _ in nombres]
            for _ in range(filas)
        ]
        # La fila completa repetida dos veces garantiza que la tabla no tenga
        # clave natural: el módulo debe decir «no única», no inventar una.
        datos.append(list(datos[0]))
        valores = ", ".join(
            "(" + ", ".join("NULL" if v is None else repr(v) for v in fila) + ")" for fila in datos
        )
        self.con.execute(
            "CREATE OR REPLACE TABLE t AS SELECT * FROM (VALUES " + valores + ") v("
            + ", ".join(f'"{c}"' for c in nombres) + ")"
        )
        return nombres

    def _distintas(self, columnas):
        """Verdad medida sin ventanas: `SELECT DISTINCT`, el camino corto."""
        lista = ", ".join(f'"{c}"' for c in columnas)
        return self.con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {lista} FROM t)").fetchone()[0]

    def _filas(self):
        return self.con.execute("SELECT count(*) FROM t").fetchone()[0]

    def test_treinta_tablas_al_azar_sin_una_sola_clave_falsa(self):
        for semilla in range(30):
            with self.subTest(semilla=semilla):
                columnas = self._aleatoria(semilla)
                filas = self._filas()
                clave, unica = vc.buscar_clave(self.con, "t", columnas, filas, limite=2)
                if unica:
                    self.assertEqual(
                        self._distintas(clave), filas,
                        f"declaró única {clave} con {filas - self._distintas(clave)} filas repetidas",
                    )
                else:
                    # Si dice que no hay clave, la fila completa tiene que repetirse.
                    self.assertLess(self._distintas(columnas), filas,
                                    "dijo «sin clave» en una tabla sin filas repetidas")
                self.assertEqual(vc.es_unica(self.con, "t", clave, filas), unica)

    def test_un_nulo_en_cualquier_columna_de_la_clave_no_la_salva(self):
        """El NULL puede caer en la primera, en la última o en las dos."""
        for posicion in (0, 1, 2):
            with self.subTest(posicion=posicion):
                nombres = [f"c{i}" for i in range(3)]
                base = ["v0", "v0", "v0"]
                base[posicion] = None
                fila = dict(zip(nombres, base))
                self.con.execute(
                    "CREATE OR REPLACE TABLE t AS SELECT * FROM (VALUES (?, ?, ?), (?, ?, ?), (?, ?, ?)) "
                    "v(c0, c1, c2)",
                    [fila["c0"], fila["c1"], fila["c2"]] * 2 + ["v9", "v9", "v9"],
                )
                for limite in (1, 2, 3):
                    clave, unica = vc.buscar_clave(self.con, "t", nombres, 3, limite=limite)
                    self.assertFalse(unica, f"clave falsa {clave} con NULL en {nombres[posicion]}")
                self.assertFalse(vc.es_unica(self.con, "t", nombres, 3))

    def test_el_informe_no_puede_contradecir_al_catalogo(self):
        """Todo objeto con filas publicadas tiene fila de clave primaria medida."""
        import json

        csv_path = RAIZ / "docs" / "api" / "claves.csv"
        cat_path = RAIZ / "docs" / "api" / "v2" / "catalog.json"
        if not csv_path.exists() or not cat_path.exists():
            self.skipTest("sin contrato generado")
        catalogo = {o["id"]: o for o in json.loads(cat_path.read_text(encoding="utf-8"))["objetos"]}
        with csv_path.open(encoding="utf-8", newline="") as fh:
            medidas = {f["objeto"] for f in csv.DictReader(fh) if f["tipo"] == "pk"}
        con_filas = {k for k, o in catalogo.items() if int(o.get("filas") or 0) > 0}
        self.assertEqual(con_filas - medidas, set(),
                         "objetos publicados con filas y sin clave medida en claves.csv")


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


class ArtefactoClavesTests(unittest.TestCase):
    """El modo --check compara el informe y nunca modifica el checkout."""

    def test_check_detecta_deriva_sin_sobrescribir_el_csv(self):
        with tempfile.TemporaryDirectory() as temporal:
            destino = Path(temporal) / "claves.csv"
            anterior = b"informe versionado antiguo\r\n"
            destino.write_bytes(anterior)
            generado = vc.serializar_csv([{"objeto": "demo", "tipo": "fk"}])

            self.assertFalse(vc.guardar_o_comprobar_csv(destino, generado, check=True))
            self.assertEqual(destino.read_bytes(), anterior)

    def test_check_de_archivo_ausente_falla_sin_crearlo(self):
        with tempfile.TemporaryDirectory() as temporal:
            destino = Path(temporal) / "no-existe.csv"
            generado = vc.serializar_csv([])

            self.assertFalse(vc.guardar_o_comprobar_csv(destino, generado, check=True))
            self.assertFalse(destino.exists())

    def test_modo_generacion_escribe_el_csv_serializado(self):
        with tempfile.TemporaryDirectory() as temporal:
            destino = Path(temporal) / "claves.csv"
            generado = vc.serializar_csv([{"objeto": "demo", "tipo": "fk"}])

            self.assertTrue(vc.guardar_o_comprobar_csv(destino, generado, check=False))
            self.assertEqual(destino.read_bytes(), generado)


if __name__ == "__main__":
    unittest.main()

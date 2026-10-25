#!/usr/bin/env python3
"""Ejecuta con DuckDB nativo las consultas SQL que ofrece la ficha candidata.

Trabaja solo con Parquet locales y el DDL de views.sql; no prueba DuckDB-Wasm
ni solicita datos a Pages/Vercel.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote

import duckdb

from ficha_renderer import DOCS, VISTAS_SQL, construir_ficha

CANDIDATAS = (
    "seguros_renta_fija",
    "ffmm_cartera_nacional",
    "fi_cartera_nacional",
    "macro_uf",
    "bancos_balance",
    "patrimonios_separados_balance",
)


class Enlaces(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(str(href))


def sql_de_ficha(id_api: str) -> tuple[str, str]:
    html = construir_ficha(id_api, verificar_hash=False)
    parser = Enlaces()
    parser.feed(html)
    encontrados = [unquote(href.split("#sql=", 1)[1]) for href in parser.hrefs if "#sql=" in href]
    if len(encontrados) != 1:
        raise SystemExit(f"Se esperaba una consulta SQL en la ficha {id_api}; hay {len(encontrados)}")
    objeto = next(o for o in json.loads((DOCS / "api" / "v2" / "catalog.json").read_text(encoding="utf-8"))["objetos"] if o["id"] == id_api)
    return str(objeto.get("sql_view") or ""), encontrados[0]


def ddl_de_vista(ddl: str, nombre: str) -> str:
    patron = re.compile(
        r"CREATE\s+OR\s+REPLACE\s+VIEW\s+[\"`]?" + re.escape(nombre)
        + r"[\"`]?\s+AS\b.*?;",
        re.IGNORECASE | re.DOTALL,
    )
    coincidencias = patron.findall(ddl)
    if len(coincidencias) != 1:
        raise SystemExit(f"views.sql debe definir exactamente una vista {nombre}; hay {len(coincidencias)}")
    return coincidencias[0]


def main() -> int:
    archivo_ddl = VISTAS_SQL.read_text(encoding="utf-8")
    conn = duckdb.connect()
    conn.execute("SET VARIABLE sif_base = '" + DOCS.as_posix().replace("'", "''") + "'")
    pruebas: list[tuple[str, str]] = []

    for id_api in CANDIDATAS:
        view, query = sql_de_ficha(id_api)
        if not view or query != f"SELECT * FROM {view} LIMIT 20;":
            raise SystemExit(f"SQL de ficha no conserva vista/consulta canónica: {id_api} → {query}")
        conn.execute(ddl_de_vista(archivo_ddl, view))
        pruebas.append((id_api, query))

    # Control cruzado adicional de los dos contratos bancarios: que el SQL
    # ejecutado confirme el mismo perímetro que las descripciones y los archivos.
    for view in ("bancos_balance", "bancos_resultados"):
        conn.execute(ddl_de_vista(archivo_ddl, view))

    for id_api, query in pruebas:
        filas = conn.execute(query).fetchall()
        if not filas or len(filas) > 20:
            raise SystemExit(f"Consulta de ficha {id_api} no devuelve entre 1 y 20 filas: {len(filas)}")
        print(f"OK {id_api}: {len(filas)} filas de vista local para {query}")

    for view, esperadas in (("bancos_balance", {"B1", "B2"}), ("bancos_resultados", {"R1"})):
        columnas = [c[0] for c in conn.execute(f"SELECT * FROM {view} LIMIT 0").description]
        if "familia_archivo_fuente" not in columnas:
            raise SystemExit(f"La vista {view} no expone la columna de filtro esperada")
        familias = {r[0] for r in conn.execute(f"SELECT DISTINCT familia_archivo_fuente FROM {view}").fetchall()}
        if not familias or not familias <= esperadas:
            raise SystemExit(f"Filtro bancario inesperado en {view}: {sorted(familias)}")
        print(f"OK {view}: familias {', '.join(sorted(familias))}")

    conn.close()
    print(f"SQL LOCAL: {len(pruebas)} consultas de fichas más 2 filtros bancarios; DuckDB nativo, sin navegador/red")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

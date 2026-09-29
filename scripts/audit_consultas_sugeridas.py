#!/usr/bin/env python3
"""Ejecuta todas las consultas sugeridas de la interfaz contra los Parquet publicados.

La web ofrece consultas sugeridas por industria (docs/js/sidebar.js). Si una de ellas
devuelve una tabla vacía o revienta, el visitante se lleva la peor primera impresión
posible. Esta auditoría registra las mismas vistas semánticas que registra el navegador
(docs/js/duckdb_client.js) y ejecuta cada consulta, informando de tres estados:

    OK      la consulta devuelve filas
    VACIA   la consulta es válida pero no devuelve ninguna fila
    ERROR   la consulta no se puede ejecutar

Uso:
    python3 scripts/audit_consultas_sugeridas.py            # informe completo
    python3 scripts/audit_consultas_sugeridas.py --check    # falla si hay ERROR o VACIA

Requiere el paquete `duckdb`. Si no está instalado, la auditoría se salta con éxito
para no romper entornos que no lo tengan.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
CLIENTE = DOCS / "js" / "duckdb_client.js"
SIDEBAR = DOCS / "js" / "sidebar.js"


def _bloque(texto: str, marcador: str) -> str:
    """Devuelve el cuerpo del array/objeto que sigue a `marcador`, equilibrando corchetes."""
    i = texto.index(marcador)
    i = texto.index("[", i) if "[" in texto[i : i + 200] else texto.index("{", i)
    apertura = texto[i]
    cierre = "]" if apertura == "[" else "}"
    nivel, j = 0, i
    while j < len(texto):
        if texto[j] == apertura:
            nivel += 1
        elif texto[j] == cierre:
            nivel -= 1
            if nivel == 0:
                return texto[i : j + 1]
        j += 1
    raise ValueError(f"bloque no equilibrado para {marcador}")


def vistas_semanticas() -> list[dict]:
    """Extrae SEMANTIC_VIEWS de duckdb_client.js."""
    txt = CLIENTE.read_text(encoding="utf-8")
    bloque = _bloque(txt, "const SEMANTIC_VIEWS")
    vistas = []
    for m in re.finditer(r"\{([^{}]*)\}", bloque):
        cuerpo = m.group(1)
        nombre = re.search(r'name:\s*"([^"]+)"', cuerpo)
        if not nombre:
            continue
        v = {"name": nombre.group(1)}
        for clave in ("file", "manifest", "where"):
            hit = re.search(rf'{clave}:\s*"([^"]+)"', cuerpo)
            if hit:
                v[clave] = hit.group(1)
        vistas.append(v)
    return vistas


def alias_heredados() -> dict[str, list[str]]:
    txt = CLIENTE.read_text(encoding="utf-8")
    bloque = _bloque(txt, "const LEGACY_VIEW_ALIASES")
    alias = {}
    for m in re.finditer(r"(\w+):\s*\[([^\]]*)\]", bloque):
        alias[m.group(1)] = re.findall(r'"([^"]+)"', m.group(2))
    return alias


def _desescapar(s: str) -> str:
    """Deshace los escapes de cadena JS sin romper los caracteres UTF-8."""
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def consultas_sugeridas() -> list[tuple[str, str]]:
    """Extrae los pares (etiqueta, consulta) de sidebar.js."""
    txt = SIDEBAR.read_text(encoding="utf-8")
    patron = re.compile(
        r'\{\s*label:\s*"((?:[^"\\]|\\.)*)"\s*,\s*query:\s*"((?:[^"\\]|\\.)*)"\s*\}', re.S
    )
    fuera = []
    for m in patron.finditer(txt):
        etiqueta = _desescapar(m.group(1))
        consulta = _desescapar(m.group(2))
        fuera.append((etiqueta, consulta))
    return fuera


def ficheros_de(vista: dict) -> list[str]:
    if "file" in vista:
        ruta = DOCS / vista["file"]
        return [str(ruta)] if ruta.exists() else []
    if "manifest" in vista:
        man = DOCS / vista["manifest"]
        if not man.exists():
            return []
        datos = json.loads(man.read_text(encoding="utf-8"))
        rutas = [DOCS / f for f in datos.get("files", [])]
        return [str(p) for p in rutas if p.exists()]
    return []


def registrar(con, vistas: list[dict], alias: dict[str, list[str]]) -> list[str]:
    sin_datos = []
    for v in vistas:
        ficheros = ficheros_de(v)
        if not ficheros:
            sin_datos.append(v["name"])
            continue
        filtro = f" WHERE {v['where']}" if "where" in v else ""
        con.execute(
            f'CREATE OR REPLACE VIEW "{v["name"]}" AS '
            f"SELECT * FROM read_parquet({ficheros!r}, union_by_name=true){filtro}"
        )
        for viejo in alias.get(v["name"], []):
            con.execute(f'CREATE OR REPLACE VIEW "{viejo}" AS SELECT * FROM "{v["name"]}"')
    return sin_datos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="salir con error si algo falla")
    args = ap.parse_args()

    try:
        import duckdb
    except ImportError:
        print("duckdb no instalado: auditoría omitida")
        return 0

    con = duckdb.connect()
    vistas = vistas_semanticas()
    alias = alias_heredados()
    sin_datos = registrar(con, vistas, alias)

    print(f"Vistas declaradas : {len(vistas)}")
    print(f"Vistas registradas: {len(vistas) - len(sin_datos)}")
    if sin_datos:
        print(f"Vistas sin fichero: {len(sin_datos)} -> {', '.join(sorted(sin_datos))}")

    filas_por_vista = {}
    for v in vistas:
        if v["name"] in sin_datos:
            continue
        filas_por_vista[v["name"]] = con.execute(
            'SELECT count(*) FROM "%s"' % v["name"]
        ).fetchone()[0]
    vistas_vacias = sorted(n for n, c in filas_por_vista.items() if c == 0)
    total_filas = sum(filas_por_vista.values())
    print(f"Filas publicadas  : {total_filas:,}".replace(",", "."))
    if vistas_vacias:
        print(f"Vistas con 0 filas: {len(vistas_vacias)} -> {', '.join(vistas_vacias)}")
    print()

    consultas = consultas_sugeridas()
    print(f"Consultas sugeridas: {len(consultas)}\n")

    errores, vacias = [], []
    for etiqueta, sql in consultas:
        try:
            filas = con.execute(sql).fetchall()
        except Exception as exc:  # noqa: BLE001
            errores.append((etiqueta, sql, str(exc).splitlines()[0][:160]))
            continue
        if not filas:
            vacias.append((etiqueta, sql))

    ok = len(consultas) - len(errores) - len(vacias)
    print(f"  OK    : {ok}")
    print(f"  VACIA : {len(vacias)}")
    print(f"  ERROR : {len(errores)}")

    if vacias:
        print("\n--- devuelven tabla vacía ---")
        for etiqueta, sql in vacias:
            print(f"  · {etiqueta}\n      {sql[:150]}")
    if errores:
        print("\n--- no ejecutan ---")
        for etiqueta, _sql, msg in errores:
            print(f"  · {etiqueta}\n      {msg}")

    if args.check and (errores or vacias or vistas_vacias):
        print("\nFALLA: hay consultas sugeridas rotas o vacías, o vistas sin filas.")
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

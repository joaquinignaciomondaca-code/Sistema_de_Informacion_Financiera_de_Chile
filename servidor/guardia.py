"""Guardia de solo lectura del servidor HTTP: AST, no expresiones regulares.

El guardia del SDK (`sif_chile.guardia`) protege la sesión de quien ejecuta una
consulta en su propia máquina. Un servidor público necesita además proteger los
archivos del proceso: DuckDB puede leer el disco con funciones de tabla
(`read_text`, `glob`, `read_parquet`, …), con *replacement scans*
(`SELECT * FROM '/etc/passwd'`) y puede ejecutar SQL escondido en `query('…')`.

Las expresiones regulares no alcanzan: se probó que `main.read_text(…)`,
`SELECT * FROM (SELECT * FROM '…')` y `FROM (VALUES …) t, '…'` las burlan. Por
eso este guardia parsea con el propio DuckDB (`json_serialize_sql`) y recorre el
AST con una política **fail-closed**:

  1. Una sola sentencia, y que el parser la serialice (SELECT/WITH/VALUES/TABLE/
     DESCRIBE/SHOW/SUMMARIZE). EXPLAIN/PIVOT/UNPIVOT no se serializan en DuckDB
     2.0 y se rechazan; cualquier escritura tampoco.
  2. Toda relación (`BASE_TABLE`) tiene que ser una vista del contrato o una CTE
     definida en la propia consulta. Un literal usado como tabla (*replacement
     scan*) no es ninguna de las dos y se rechaza, esté anidado o tras coma.
  3. Toda función de tabla (`TABLE_FUNCTION`) se rechaza: el servidor no abre
     archivos, ni red, ni otras bases. Las vistas del contrato ya encapsulan los
     `read_parquet` publicados.
  4. Toda función escalar/aggregate/window tiene que estar en la lista blanca del
     núcleo DuckDB, menos las que tienen efectos o leen configuración
     (`setseed`, `nextval`, `current_setting`, `getvariable`, `json_serialize_sql`,
     …). Se comparan por nombre, así que `main.read_text` o `pg_catalog.abs` no
     añaden una vía nueva.

No es una frontera de seguridad por sí solo —la defensa en profundidad del
servidor añade `lock_configuration`, modo local sin red o `LocalFileSystem`
deshabilitado en modo remoto, usuario sin privilegios y montaje de solo lectura—
pero cierra los vectores que el guardia del SDK, pensado para uso local, no
cubría. Ver `servidor/README.md` y `servidor/tests/test_guardia.py`.
"""
from __future__ import annotations

import json
import threading
from typing import Any, Iterable

import duckdb

# Funciones que nunca se permiten, aunque el núcleo las traiga como escalares.
# Unas tienen efectos (setseed, nextval), otras leen configuración o el propio
# SQL (current_setting, getvariable, json_serialize_sql), y otras ejecutan SQL o
# tocan archivos/red. Las de tabla ya se rechazan por tipo de nodo; se listan
# igual para que el mensaje sea claro y la defensa no dependa de una sola capa.
PROHIBIDAS = frozenset({
    "read_text", "read_blob", "read_parquet", "read_csv", "read_csv_auto",
    "read_json", "read_json_auto", "read_ndjson", "read_ndjson_auto",
    "read_avro", "read_arrow", "glob", "parquet_scan", "csv_scan", "json_scan",
    "ndjson_scan", "avro_scan", "arrow_scan", "sniff_csv", "parquet_metadata",
    "parquet_schema", "parquet_file_metadata", "csv_metadata",
    "sqlite_scan", "sqlite_attach", "postgres_scan", "postgres_attach",
    "mysql_scan", "mysql_attach", "odbc_scan", "delta_scan", "iceberg_scan",
    "iceberg_metadata", "query", "query_table", "from_text",
    "load_extension", "install_extension", "force_install", "attach",
    "detach", "copy", "export", "import", "ingest",
    "setseed", "nextval", "currval", "setvariable", "getvariable",
    "current_setting", "json_serialize_sql", "pg_sleep",
    "inet_client_addr", "inet_client_port", "inet_server_addr", "inet_server_port",
})

# Operadores que el AST marca como función pero no son nombres de catálogo.
OPERADORES = frozenset({
    "+", "-", "*", "/", "%", "||", "~~", "!~~", "~~*", "!~~*", "^", "&", "|",
    "<<", ">>", "=", "!=", "<>", "<", ">", "<=", ">=", "!", "NOT", "AND", "OR",
    "IS", "ISNULL", "NOTNULL", "~", "!~", "~*", "!~*",
})

# SHOW sin subconsulta que se permite (no revela variables ni configuración).
SHOW_PERMITIDOS = frozenset({"tables", "views", "databases", "schemas"})

# Catálogos/esquemas desde los que se puede leer una vista del contrato.
CATALOGOS = frozenset({"", "memory", "temp"})
ESQUEMAS = frozenset({"", "main", "temp"})


def _ctes(nodo: Any) -> set[str]:
    """Nombres de CTE definidos en la consulta (incluidas las recursivas)."""
    nombres: set[str] = set()

    def walk(n: Any) -> None:
        if isinstance(n, dict):
            if n.get("type") == "RECURSIVE_CTE_NODE" and n.get("cte_name"):
                nombres.add(str(n["cte_name"]).lower())
            mapa = n.get("cte_map")
            if isinstance(mapa, dict):
                for entrada in mapa.get("map") or []:
                    if isinstance(entrada, dict) and entrada.get("key"):
                        nombres.add(str(entrada["key"]).lower())
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(nodo)
    return nombres


class GuardiaAST:
    """Guardia fail-closed sobre el AST de DuckDB.

    `relaciones` son los nombres de las vistas que el contrato registró (las de
    `SHOW TABLES` tras ejecutar `views.sql`). `funciones` permite inyectar la
    lista blanca en pruebas; por defecto se toma del núcleo DuckDB.
    """

    def __init__(self, relaciones: Iterable[str],
                 funciones: Iterable[str] | None = None) -> None:
        self.relaciones = {str(r).lower() for r in relaciones}
        self._con = duckdb.connect()
        self._lock = threading.Lock()
        self._cerrado = False
        if funciones is None:
            filas = self._con.execute(
                "SELECT DISTINCT function_name FROM duckdb_functions() "
                "WHERE function_type IN ('scalar', 'aggregate', 'window')"
            ).fetchall()
            funciones = [f[0] for f in filas]
        self.funciones = ({str(f).lower() for f in funciones} | OPERADORES
                          | {"unnest"}) - PROHIBIDAS

    def validar(self, sql: str) -> tuple[bool, str]:
        """Devuelve (permitida, motivo). El motivo está escrito para mostrarse."""
        original = "" if sql is None else str(sql)
        if not original.strip():
            return False, "La consulta está vacía."
        try:
            with self._lock:
                crudo = self._con.execute(
                    "SELECT json_serialize_sql(?)", [original]
                ).fetchone()[0]
            ast = json.loads(crudo)
        except duckdb.Error as exc:
            return False, f"No se pudo parsear la consulta: {str(exc).splitlines()[0][:200]}"
        if ast.get("error"):
            tipo = ast.get("error_type", "")
            mensaje = ast.get("error_message", "")
            if tipo == "not implemented":
                return False, (
                    "El servidor solo acepta SELECT/WITH/VALUES/TABLE/DESCRIBE/SHOW/"
                    "SUMMARIZE de una sola sentencia. EXPLAIN/PIVOT/UNPIVOT no se "
                    "pueden validar y se rechazan."
                )
            return False, f"Consulta inválida: {mensaje[:200]}"
        sentencias = ast.get("statements") or []
        if len(sentencias) != 1:
            return False, (
                f"Solo se ejecuta una sentencia por vez y esta trae {len(sentencias)}. "
                "No se permite encadenar sentencias con «;»."
            )
        ctes = _ctes(ast)
        motivo = self._revisar(ast, ctes)
        if motivo:
            return False, motivo
        return True, ""

    def exigir(self, sql: str) -> str:
        ok, motivo = self.validar(sql)
        if not ok:
            raise ValueError(motivo)
        return sql

    def _revisar(self, nodo: Any, ctes: set[str]) -> str:
        if isinstance(nodo, dict):
            tipo = nodo.get("type")
            if tipo == "BASE_TABLE":
                nombre = str(nodo.get("table_name") or "").lower()
                catalogo = str(nodo.get("catalog_name") or "").lower()
                esquema = str(nodo.get("schema_name") or "").lower()
                if nodo.get("at_clause") is not None:
                    return "No se acepta AT/VERSION sobre una relación."
                if nombre in ctes:
                    if catalogo or esquema not in ESQUEMAS:
                        return f"La CTE «{nodo.get('table_name')}» no se puede calificar así."
                elif nombre in self.relaciones:
                    if catalogo not in CATALOGOS or esquema not in ESQUEMAS:
                        return (
                            f"«{nodo.get('table_name')}» solo se lee desde el contrato "
                            "(memory/main o temp/main), no desde otro catálogo o esquema."
                        )
                else:
                    return (
                        f"«{nodo.get('table_name')}» no es una vista del contrato ni una "
                        "CTE de la consulta. El servidor no lee archivos ni otras bases: "
                        "descubre los objetos en /v2/catalog."
                    )
            elif tipo == "TABLE_FUNCTION":
                fn = (nodo.get("function") or {}).get("function_name") or "tabla"
                return (
                    f"La función de tabla «{fn}» no está permitida: el servidor no abre "
                    "archivos, red ni otras bases. Consulta las vistas del contrato."
                )
            elif tipo == "FUNCTION":
                nombre = str(nodo.get("function_name") or "").lower()
                if nombre in PROHIBIDAS or nombre not in self.funciones:
                    return (
                        f"La función «{nombre}» no está permitida: tiene efectos, lee "
                        "configuración o no es del núcleo de lectura del servidor."
                    )
            elif tipo == "SHOW_REF":
                if nodo.get("query") is None:
                    tabla = str(nodo.get("table_name") or "").strip('"').lower()
                    if tabla not in SHOW_PERMITIDOS:
                        return f"SHOW «{tabla}» no está permitido en el servidor."
            for v in nodo.values():
                motivo = self._revisar(v, ctes)
                if motivo:
                    return motivo
        elif isinstance(nodo, list):
            for v in nodo:
                motivo = self._revisar(v, ctes)
                if motivo:
                    return motivo
        return ""

    def cerrar(self) -> None:
        if not self._cerrado:
            self._cerrado = True
            self._con.close()

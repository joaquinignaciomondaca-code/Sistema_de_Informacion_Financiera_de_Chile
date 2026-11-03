"""Pruebas del guardia AST: lo que deja pasar y lo que rebota, sobre DuckDB real."""
from __future__ import annotations

import pytest

LEGITIMAS = [
    "SELECT count(*) FROM seguros_lista_entidades",
    'SELECT * FROM "bancos_balance" LIMIT 3',
    "WITH x AS (SELECT 1 a) SELECT * FROM x",
    "WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t WHERE n<5) SELECT * FROM t",
    "DESCRIBE macro_uf",
    "SHOW TABLES",
    "SHOW VIEWS",
    "SUMMARIZE SELECT 1 AS x",
    "VALUES (1), (2)",
    "TABLE bancos_balance",
    "SELECT * FROM memory.main.bancos_balance LIMIT 1",
    "SELECT 'hola drop' AS t",
    "SELECT /* read_text('/etc/passwd') */ 1",
    "SELECT $foo$;DROP$foo$ AS t",
    "SELECT abs(-1), pg_catalog.abs(-2), main.abs(-3)",
    "SELECT list_transform([1,2,3], x -> x+1)",
    "SELECT struct_pack(a := 1)",
    "SELECT unnest([1,2,3])",
    "SELECT count(*) FILTER (WHERE 1=1) FROM (SELECT 1)",
    "SELECT CAST(1 AS VARCHAR), coalesce(NULL, 1)",
    "WITH read_text AS (SELECT 1 AS x) SELECT * FROM read_text",
]

ATAQUES = [
    "SELECT * FROM read_text('/etc/passwd')",
    'SELECT * FROM "read_text"(\'/etc/passwd\')',
    "SELECT * FROM main.read_text('/etc/passwd')",
    "SELECT * FROM pg_catalog.read_text('/etc/passwd')",
    "SELECT * FROM glob('/etc/*')",
    "SELECT * FROM 'docs/api/v2/catalog.json'",
    "SELECT * FROM (SELECT * FROM 'docs/api/v2/catalog.json')",
    "SELECT * FROM (VALUES (1)) t(x) JOIN 'docs/api/v2/catalog.json' ON true",
    "SELECT * FROM (VALUES (1)) t(x), 'docs/api/v2/catalog.json'",
    "SELECT * FROM read_parquet('/etc/passwd')",
    "SELECT query('DROP VIEW x')",
    "SELECT * FROM query('SELECT 1')",
    "SELECT * FROM query_table('bancos_balance')",
    "SELECT json_serialize_sql('SELECT 1')",
    "SELECT current_setting('threads')",
    "SELECT getvariable('sif_base')",
    "SELECT setseed(0.5)",
    "SELECT nextval('x')",
    "PRAGMA threads=1",
    "SET threads=1",
    "DROP VIEW bancos_balance",
    "SELECT 1; DROP VIEW x",
    "SELECT 1; SELECT 2",
    "SELECT * INTO falsa FROM bancos_balance",
    "ATTACH '/tmp/x.db'",
    "SELECT * FROM sqlite_scan('/tmp/x.db','t')",
    "COPY bancos_balance TO '/tmp/x.csv'",
    "EXPLAIN SELECT 1",
    "PIVOT (SELECT 1 AS a, 2 AS b) ON a USING sum(b)",
    "SELECT * FROM range(10)",
    "SELECT * FROM generate_series(1,10)",
    "SELECT * FROM unnest([1,2,3])",
    "SELECT * FROM duckdb_functions()",
    "SELECT * FROM duckdb_tables()",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM system.main.bancos_balance",
    "SELECT * FROM pg_catalog.pg_tables",
    "SELECT * FROM bancos_balance AT (VERSION => 1)",
    "",
    "   ",
]


@pytest.mark.parametrize("sql", LEGITIMAS)
def test_legitimas(motor, sql):
    ok, motivo = motor.guardia.validar(sql)
    assert ok, motivo


@pytest.mark.parametrize("sql", ATAQUES)
def test_ataques(motor, sql):
    ok, motivo = motor.guardia.validar(sql)
    assert not ok, f"debía rechazar: {sql}"
    assert motivo


def test_mensaje_de_reemplazo(motor):
    ok, motivo = motor.guardia.validar("SELECT * FROM '/etc/passwd'")
    assert not ok
    assert "vista del contrato" in motivo


def test_mensaje_de_funcion(motor):
    ok, motivo = motor.guardia.validar("SELECT * FROM glob('/etc/*')")
    assert not ok
    assert "función de tabla" in motivo

"""Pruebas del Motor sobre los Parquet reales del contrato (modo local)."""
from __future__ import annotations

import threading

import pytest

from servidor.app import Limites, Motor, Ocupado, Timeout


def test_consulta_real(motor):
    r = motor.consultar("SELECT count(*) AS n FROM seguros_lista_entidades", 10)
    assert r["ok"] and r["class"] == "ok"
    assert r["columnas"] == ["n"]
    assert r["datos"] == [[84]]
    assert r["data_release"]


def test_truncado(motor):
    r = motor.consultar("SELECT * FROM macro_uf", 3)
    assert r["filas"] == 3
    assert r["truncado"] is True
    assert len(r["datos"]) == 3


def test_no_truncado(motor):
    r = motor.consultar("SELECT 1 AS x", 10)
    assert r["filas"] == 1
    assert r["truncado"] is False


def test_describe_show(motor):
    r = motor.consultar("DESCRIBE bancos_balance", 200)
    assert r["filas"] > 0
    r = motor.consultar("SHOW TABLES", 200)
    # SHOW TABLES desde un cursor no lista las 4 vistas temporales auxiliares.
    assert r["filas"] >= 105


def test_serializacion(motor):
    r = motor.consultar(
        "SELECT DATE '2026-01-02' AS f, TIMESTAMP '2026-01-02 03:04:05' AS t, "
        "CAST('1234.56' AS DECIMAL(10,2)) AS d, INTERVAL 90 SECOND AS i, 'x' AS s", 1)
    fila = r["datos"][0]
    assert fila[0] == "2026-01-02"
    assert fila[1].startswith("2026-01-02T03:04:05")
    assert fila[2] == "1234.56"
    assert fila[3] == 90.0


def test_no_finitos(motor):
    r = motor.consultar("SELECT 'nan'::DOUBLE AS n, 'inf'::DOUBLE AS i", 1)
    assert r["datos"] == [[None, None]]


def test_timeout_y_reuso(motor):
    limites = Limites(pool=1, timeout_s=0.3)
    m = Motor(base=motor.base, limites=limites)
    try:
        with pytest.raises(Timeout):
            m.consultar("SELECT count(*) FROM ffmm_cartera_nacional a CROSS JOIN ffmm_cartera_nacional b", 1)
        # El cursor interrumpido vuelve al pool y sirve otra consulta.
        r = m.consultar("SELECT 42 AS respuesta", 1)
        assert r["datos"] == [[42]]
    finally:
        m.cerrar()


def test_pool_ocupado():
    m = Motor(base="docs", limites=Limites(pool=1, timeout_s=0.2))
    try:
        cur = m._pool.get_nowait()
        with pytest.raises(Ocupado):
            m.consultar("SELECT 1", 1)
        m._pool.put(cur)
    finally:
        m.cerrar()


def test_limite_invalido(motor):
    with pytest.raises(ValueError):
        motor.consultar("SELECT 1", 0)
    with pytest.raises(ValueError):
        motor.consultar("SELECT 1", motor.limites.max_filas + 1)


def test_sql_vacio(motor):
    with pytest.raises(ValueError):
        motor.consultar("", 1)


def test_lock_configuration(motor):
    import duckdb
    cur = motor._con.cursor()
    with pytest.raises(duckdb.Error):
        cur.execute("SET threads=1")
    cur.close()

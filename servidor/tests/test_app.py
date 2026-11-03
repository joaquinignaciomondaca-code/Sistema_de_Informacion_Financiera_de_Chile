"""Pruebas HTTP de la app FastAPI contra los Parquet reales (modo local)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from servidor.app import Limites, crear_app


def test_health(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    c = r.json()
    assert c["ok"] and c["class"] == "ok"
    assert c["objetos"] == 90
    assert c["vistas"] == 109
    assert c["modo"] == "local"


def test_raiz(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    c = r.json()
    assert c["contrato"] == "v2"
    assert "/v2/query" in c["rutas"].values()
    assert c["auth_requerida"] is False


def test_catalog(cliente):
    r = cliente.get("/v2/catalog")
    assert r.status_code == 200
    c = r.json()
    assert c["totales"]["objetos"] == 90
    assert c["totales"]["consultas"] == 159


def test_schema(cliente):
    r = cliente.get("/v2/schema/bancos_balance")
    assert r.status_code == 200
    c = r.json()
    assert c["id"] == "bancos_balance"
    assert c["columnas"]


def test_schema_alias(cliente):
    r = cliente.get("/v2/schema/afp_maestro")
    assert r.status_code == 200


def test_schema_invalido(cliente):
    r = cliente.get("/v2/schema/../../etc")
    assert r.status_code in (400, 404)


def test_schema_desconocido(cliente):
    r = cliente.get("/v2/schema/no_existe")
    assert r.status_code == 404
    assert r.json()["class"] == "input"


def test_partitions(cliente):
    r = cliente.get("/v2/partitions/bancos_balance")
    assert r.status_code == 200
    assert r.json()["particiones"]


def test_queries(cliente):
    r = cliente.get("/v2/queries")
    assert r.status_code == 200
    assert len(r.json()["consultas"]) == 159


def test_resultados(cliente):
    r = cliente.get("/v2/resultados")
    assert r.status_code == 200
    assert r.json()["consultas"]


def test_resultado(cliente):
    r = cliente.get("/v2/resultado/companias-que-reportan-en-el-ultimo-mes-7ece34")
    assert r.status_code == 200
    c = r.json()
    assert c["filas"] == 66


def test_resultado_desconocido(cliente):
    r = cliente.get("/v2/resultado/no-existe")
    assert r.status_code == 404


def test_query_post(cliente):
    r = cliente.post("/v2/query", json={"sql": "SELECT count(*) AS n FROM seguros_lista_entidades"})
    assert r.status_code == 200
    c = r.json()
    assert c["ok"] and c["datos"] == [[84]]
    assert r.headers["cache-control"] == "no-store"


def test_query_get(cliente):
    r = cliente.get("/v2/query", params={"sql": "SELECT 1 AS x", "limite": 1})
    assert r.status_code == 200
    assert r.json()["datos"] == [[1]]


def test_query_truncado(cliente):
    r = cliente.post("/v2/query", json={"sql": "SELECT * FROM macro_uf", "limite": 3})
    assert r.status_code == 200
    assert r.json()["truncado"] is True


def test_query_guardia(cliente):
    r = cliente.post("/v2/query", json={"sql": "SELECT * FROM read_text('/etc/passwd')"})
    assert r.status_code == 403
    c = r.json()
    assert c["class"] == "refused" and c["retry"] == "no"


def test_query_replacement(cliente):
    r = cliente.post("/v2/query", json={"sql": "SELECT * FROM 'docs/api/v2/catalog.json'"})
    assert r.status_code == 403


def test_query_columna_inexistente(cliente):
    r = cliente.post("/v2/query", json={"sql": "SELECT nope FROM bancos_balance"})
    assert r.status_code == 400
    assert r.json()["class"] == "input"


def test_query_vacia(cliente):
    r = cliente.post("/v2/query", json={"sql": ""})
    assert r.status_code == 400


def test_query_limite_invalido(cliente):
    r = cliente.post("/v2/query", json={"sql": "SELECT 1", "limite": 0})
    assert r.status_code == 400


def test_openapi(cliente):
    r = cliente.get("/openapi.json")
    assert r.status_code == 200
    c = r.json()
    assert "/v2/query" in c["paths"]
    assert "/health" in c["paths"]


def test_docs(cliente):
    r = cliente.get("/docs")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_sin_x_frame_options(cliente):
    r = cliente.get("/health")
    assert "x-frame-options" not in {k.lower() for k in r.headers}


def test_cors(cliente):
    r = cliente.options("/v2/query", headers={
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"


def test_auth():
    app = crear_app(base="docs", token="secreto", limites=Limites(pool=1, rate_burst=100, rate_min=600))
    with TestClient(app) as c:
        r = c.post("/v2/query", json={"sql": "SELECT 1"})
        assert r.status_code == 401
        assert r.json()["class"] == "auth"
        r = c.post("/v2/query", json={"sql": "SELECT 1"}, headers={"Authorization": "Bearer mal"})
        assert r.status_code == 401
        r = c.post("/v2/query", json={"sql": "SELECT 1"}, headers={"Authorization": "Bearer secreto"})
        assert r.status_code == 200
    app.state.motor.cerrar()


def test_rate_limit():
    app = crear_app(base="docs", limites=Limites(pool=1, rate_burst=1, rate_min=1))
    with TestClient(app) as c:
        r = c.post("/v2/query", json={"sql": "SELECT 1"})
        assert r.status_code == 200
        r = c.post("/v2/query", json={"sql": "SELECT 1"})
        assert r.status_code == 429
        c = r.json()
        assert c["class"] == "rate" and c["retry"] == "after_wait"
        assert "retry-after" in {k.lower() for k in r.headers}
        assert c["retryAfterMs"] >= 1000
    app.state.motor.cerrar()


def test_timeout_http():
    app = crear_app(base="docs", limites=Limites(pool=1, timeout_s=0.3, rate_burst=100, rate_min=600))
    with TestClient(app) as c:
        r = c.post("/v2/query", json={"sql": "SELECT count(*) FROM ffmm_cartera_nacional a CROSS JOIN ffmm_cartera_nacional b"})
        assert r.status_code == 504
        assert r.json()["class"] == "timeout"
        r = c.post("/v2/query", json={"sql": "SELECT 1"})
        assert r.status_code == 200
    app.state.motor.cerrar()

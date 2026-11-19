"""Configuración de pytest del servidor: SDK en el path y copia local de docs/."""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "sdk" / "python"))
os.environ.setdefault("SIF_CHILE_BASE", str(RAIZ / "docs"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from servidor.app import Limites, Motor, crear_app  # noqa: E402


@pytest.fixture(scope="session")
def motor():
    m = Motor(base=str(RAIZ / "docs"), limites=Limites(pool=2, timeout_s=5))
    yield m
    m.cerrar()


@pytest.fixture(scope="session")
def entidades_esperadas():
    """Filas reales de `seguros_lista_entidades` en el Parquet publicado.

    Antes las pruebas fijaban 84 a mano. El 2026-11-17 la cartera de seguros
    publicó una aseguradora más y el job `servidor` quedó en rojo por un número,
    no por una regresión: el Parquet tenía 85 filas y el motor respondía 85.
    Leer el conteo del propio Parquet mantiene la prueba sobre lo que importa
    (el motor devuelve lo que hay publicado) sin acoplarla a cada alta.
    """
    import pyarrow.parquet as pq

    ruta = RAIZ / "docs" / "outputs" / "seguros" / "aseguradoras.parquet"
    return pq.ParquetFile(ruta).metadata.num_rows


@pytest.fixture(scope="session")
def app():
    aplicacion = crear_app(base=str(RAIZ / "docs"),
                           limites=Limites(pool=2, timeout_s=5, rate_burst=1000, rate_min=6000))
    yield aplicacion


@pytest.fixture(scope="session")
def cliente(app):
    # Un solo TestClient de sesión: el lifespan arranca/cierra el motor una vez.
    with TestClient(app) as c:
        yield c

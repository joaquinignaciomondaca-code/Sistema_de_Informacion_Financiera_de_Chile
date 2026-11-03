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
def app():
    aplicacion = crear_app(base=str(RAIZ / "docs"),
                           limites=Limites(pool=2, timeout_s=5, rate_burst=1000, rate_min=6000))
    yield aplicacion


@pytest.fixture(scope="session")
def cliente(app):
    # Un solo TestClient de sesión: el lifespan arranca/cierra el motor una vez.
    with TestClient(app) as c:
        yield c

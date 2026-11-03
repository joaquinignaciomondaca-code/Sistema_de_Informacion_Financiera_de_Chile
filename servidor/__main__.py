"""Punto de entrada: `python -m servidor`.

Lee `SIF_CHILE_BASE` (carpeta local o URL remota) y sirve la app con uvicorn.
Por defecto escucha en 0.0.0.0:8000 para que el preview del entorno funcione;
en producción se pone un proxy TLS delante (ver `compose.yaml` y `Caddyfile`).
"""
from __future__ import annotations

import logging
import os

import uvicorn

from .app import crear_app


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("SIF_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    host = os.environ.get("SIF_API_HOST", "0.0.0.0")
    port = int(os.environ.get("SIF_API_PORT", "8000"))
    uvicorn.run(crear_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

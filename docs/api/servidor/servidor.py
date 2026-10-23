"""Arranca un DuckDB que sirve los datos de SIF Chile por el protocolo Quack.

Borrador del servicio de la fase 3: **no desplegado y no verificado** dentro del
repositorio (ver `README.md`). La idea es una sola: abrir la base en modo
lectura, cargar las vistas publicadas y atender en localhost para que un proxy
termine TLS por delante.

Variables:
    SIF_CHILE_BASE      base del sitio o carpeta local con los Parquet (por defecto, el sitio)
    SIF_QUACK_TOKEN     token que piden los clientes; si falta, se genera y se imprime
    SIF_QUACK_BIND      dónde escuchar (por defecto 127.0.0.1:9494)
"""
from __future__ import annotations

import os
import secrets
import sys
import time
import urllib.request
from pathlib import Path

import duckdb

BASE = os.environ.get(
    "SIF_CHILE_BASE",
    "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile",
).rstrip("/")
BIND = os.environ.get("SIF_QUACK_BIND", "127.0.0.1:9494")
TOKEN = os.environ.get("SIF_QUACK_TOKEN") or secrets.token_urlsafe(32)
VISTAS = f"{BASE}/api/v2/views.sql"


def main() -> int:
    con = duckdb.connect()                     # sin archivo: sólo vistas, nunca datos del cliente
    con.execute("INSTALL quack; LOAD quack;")
    # El DDL se baja por HTTP normal (no hace falta httpfs para leer un .sql); las
    # vistas que crea sí leen Parquet remoto, y eso lo resuelve httpfs al vuelo.
    if BASE.startswith("http"):
        ddl = urllib.request.urlopen(VISTAS, timeout=30).read().decode("utf-8")
    else:
        ddl = Path(VISTAS.replace(BASE, BASE)).read_text(encoding="utf-8")
    con.execute(ddl)
    con.execute("CALL quack_serve('quack:" + BIND + "', token = ?)", [TOKEN])
    print(f"Quack escuchando en quack:{BIND} · {len(con.execute('SHOW TABLES').fetchall())} vistas",
          flush=True)
    print("Token:", TOKEN, flush=True)
    try:
        while True:                            # el proceso tiene que seguir vivo
            time.sleep(3600)
    except KeyboardInterrupt:
        con.execute("CALL quack_stop('quack:" + BIND + "')")
    return 0


if __name__ == "__main__":
    sys.exit(main())

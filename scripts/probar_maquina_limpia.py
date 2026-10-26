#!/usr/bin/env python3
"""Prueba de máquina limpia (Fase 1a, tarea 1a.8) — versión local.

La prueba original es «un contenedor sin el repo descubre un conjunto, lee su
esquema y consulta datos». El sandbox no tiene salida al sitio publicado, así
que se simula lo que de verdad se prueba: **un consumidor que no tiene el repo**
y que sólo dispone de HTTP.

Cómo se simula, sin trampa:

  * El servidor sirve `docs/` con `http.server`, en un puerto efímero de
    localhost. Para el cliente es un sitio cualquiera.
  * El cliente corre en un **venv aparte**, con su propio intérprete y paquetes
    (sólo `duckdb`), desde un directorio temporal **fuera del repo** y sin
    `PYTHONPATH`. No puede importar nada del proyecto.
  * El cliente no ve el filesystem del repo: descarga el descriptor por HTTP,
    elige un recurso, se baja su Parquet y lo consulta.

Lo único que no se reproduce es el CDN de GitHub Pages; el protocolo, el
formato y el contenido son los mismos archivos que sirve el sitio.

Pasos (uno por línea, reproducibles a mano):

    python3 scripts/probar_maquina_limpia.py

Deja la evidencia en `docs/api/prueba_maquina_limpia.log`.

Uso:
    python3 scripts/probar_maquina_limpia.py            # crea venv e instala duckdb
    python3 scripts/probar_maquina_limpia.py --sin-instalar   # reusa un venv ya creado
    python3 scripts/probar_maquina_limpia.py --check           # exit 1 si algo falla
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
LOG = RAIZ / "docs" / "api" / "prueba_maquina_limpia.log"
BASE_TMP = Path(tempfile.gettempdir()) / "sif-maquina-limpia"

CLIENTE = r'''
"""Consumidor limpio: no conoce el repo, sólo una URL."""
import json, sys, urllib.request
from pathlib import Path

import duckdb

base = sys.argv[1]
salida = Path(sys.argv[2])
pasos = []

def paso(nombre, ok, detalle):
    pasos.append({"paso": nombre, "ok": ok, "detalle": detalle})
    print(f"{'OK  ' if ok else 'FALLA'} {nombre}: {detalle}")

# 0. Ni rastro del proyecto en el path de importación.
proyecto = [p for p in sys.path if "Sistema_de_Informacion_Financiera" in p]
paso("sin el repo en sys.path", not proyecto, f"{proyecto or 'ninguno'}")

# 1. Descubrir el catálogo por HTTP.
with urllib.request.urlopen(base + "/api/v2/datapackage.json", timeout=30) as r:
    paquete = json.load(r)
recursos = {x["name"]: x for x in paquete["resources"]}
paso("descubrir el Data Package", len(recursos) == 86, f"{len(recursos)} recursos")

# 2. Leer el esquema de un conjunto, sin haber visto el repo.
elegido = recursos["seguros_lista_entidades"]
campos = [c["name"] for c in elegido["schema"]["fields"]]
paso("leer el esquema", "rut_aseguradora" in campos and "sector" in campos, f"{len(campos)} columnas")
paso("clave declarada", elegido["schema"].get("primaryKey") == ["sector", "rut_aseguradora"],
     str(elegido["schema"].get("primaryKey")))

# 3. Descargar el Parquet y consultarlo.
#    El descriptor publica URLs del sitio; aqui ese sitio es el que sirve
#    localhost, asi que se reescribe solo el prefijo.
sitio = paquete["sif"]["base_url"]
url = elegido["path"][0]
local = base + url[len(sitio.rstrip("/")):] if url.startswith(sitio.rstrip("/")) else url
paso("resolver la URL publica", local.startswith(base), local.replace(base, "<sitio local>"))
destino = salida / "aseguradoras.parquet"
urllib.request.urlretrieve(local, destino)
con = duckdb.connect()
filas = con.execute(f"SELECT count(*) FROM read_parquet('{destino}')").fetchone()[0]
paso("consultar los datos", filas == elegido["sif"]["filas"], f"{filas} filas (declara 84)")

# 4. Una consulta de negocio, tal como la escribiría un tercero.
por_sector = con.execute(
    f"SELECT sector, count(*) FROM read_parquet('{destino}') GROUP BY 1 ORDER BY 2 DESC"
).fetchall()
paso("consulta de negocio", sum(n for _, n in por_sector) == 84, str(por_sector))

# 5. El contrato estático: catálogo y vista SQL, sin haber visto el repo.
with urllib.request.urlopen(base + "/api/v2/catalog.json", timeout=30) as r:
    catalogo = json.load(r)
paso("descubrir el catalogo", catalogo["totales"]["objetos"] == 90,
     f"{catalogo['totales']['objetos']} objetos, {catalogo['totales']['consultas']} consultas")
with urllib.request.urlopen(base + "/api/v2/schema/seguros_lista_entidades.json", timeout=30) as r:
    esquema = json.load(r)
paso("leer el esquema por contrato", len(esquema["columnas"]) == 7,
     f"{len(esquema['columnas'])} columnas, pk {esquema['primaryKey']}")
with urllib.request.urlopen(base + "/api/v2/views.sql", timeout=30) as r:
    ddl = r.read().decode()
vistas = [l for l in ddl.splitlines() if l.startswith("CREATE OR REPLACE VIEW")]
paso("bajar las vistas", len(vistas) == 105, f"{len(vistas)} CREATE VIEW")

# 6. Que el esquema declarado sea el que devuelve la base.
descrito = {r[0]: r[1] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{destino}')").fetchall()}
esperado = {c["name"]: {"string": "VARCHAR", "integer": "BIGINT", "boolean": "BOOLEAN"}[c["type"]]
            for c in elegido["schema"]["fields"]}
coinciden = all(descrito.get(k) == v for k, v in esperado.items())
paso("esquema declarado = esquema real", coinciden, "sin discrepancias" if coinciden else str(esperado))

print(json.dumps(pasos))
'''


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def servidor(puerto: int) -> http.server.ThreadingHTTPServer:
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", puerto), manejador)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sin-instalar", action="store_true", help="no crea el venv; usa el de la corrida anterior")
    ap.add_argument("--check", action="store_true", help="exit 1 si algún paso falla")
    args = ap.parse_args()

    if BASE_TMP.exists() and not args.sin_instalar:
        shutil.rmtree(BASE_TMP)
    BASE_TMP.mkdir(parents=True, exist_ok=True)
    venv = BASE_TMP / "venv"
    python = venv / "bin" / "python"
    lineas: list[str] = [f"# Prueba de máquina limpia · {datetime.now().isoformat(timespec='seconds')}", ""]

    def anotar(texto: str) -> None:
        print(texto)
        lineas.append(texto)

    if not python.exists():
        anotar(f"$ python3 -m venv {venv}")
        r = subprocess.run([sys.executable, "-m", "venv", str(venv)], capture_output=True, text=True)
        if r.returncode != 0:
            anotar(f"  [FALLA] no se pudo crear el venv: {r.stderr.strip()[:200]}")
            return 1
        anotar(f"$ {venv}/bin/pip install --quiet duckdb   # el cliente sólo necesita un motor")
        r = subprocess.run([str(venv / "bin" / "pip"), "install", "--quiet", "--disable-pip-version-check", "duckdb"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            anotar(f"  [FALLA] pip no pudo instalar duckdb (¿sin red?): {r.stderr.strip()[:200]}")
            return 1

    # El cliente vive fuera del repo: su cwd es un directorio temporal.
    trabajo = BASE_TMP / "cliente"
    trabajo.mkdir(exist_ok=True)
    guion = BASE_TMP / "cliente.py"
    guion.write_text(CLIENTE, encoding="utf-8")

    puerto = puerto_libre()
    httpd = servidor(puerto)
    base = f"http://127.0.0.1:{puerto}"
    anotar("$ python3 -m http.server <puerto efímero> --directory docs   # sirve el sitio, como en producción")
    anotar("$ cd <cliente externo> && <venv externo>/bin/python <cliente.py> "
           "http://127.0.0.1:<puerto efímero> <cliente externo>   # sin el repo")
    anotar("")

    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    t0 = time.time()
    r = subprocess.run([str(python), str(guion), base, str(trabajo)],
                       cwd=str(trabajo), env=entorno, capture_output=True, text=True)
    httpd.shutdown()
    duracion = time.time() - t0

    for linea in r.stdout.strip().splitlines():
        if linea.startswith("{"):
            continue
        anotar(linea)
    if r.returncode != 0:
        anotar(f"  [FALLA] el cliente terminó con {r.returncode}")
        anotar((r.stderr or "").strip()[-600:])
        LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
        return 1

    try:
        pasos = json.loads(r.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        anotar("  [FALLA] el cliente no devolvió el informe")
        return 1

    fallidos = [p for p in pasos if not p["ok"]]
    anotar("")
    anotar(f"Duración: {duracion:.1f} s · pasos: {len(pasos)} · fallos: {len(fallidos)}")
    anotar("MÁQUINA LIMPIA: " + ("el consumidor descubre, lee el esquema y consulta sin tener el repo"
                                 if not fallidos else f"{len(fallidos)} paso(s) fallaron"))
    LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Evidencia: {LOG.relative_to(RAIZ)}")
    return 1 if (fallidos and args.check) else 0


if __name__ == "__main__":
    raise SystemExit(main())

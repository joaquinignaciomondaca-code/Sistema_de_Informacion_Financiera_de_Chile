#!/usr/bin/env python3
"""Ejecuta los ejemplos reproducibles y comprueba que hacen lo que dicen (1c).

Esto no es un lint: se lanzan los programas de verdad. Los de Python corren
contra la copia local de `docs/` (sin red); el de JavaScript, contra un
`http.server` efímero, porque su gracia es `fetch`. El de R no se puede probar
aquí —no hay intérprete de R en este entorno— y tiene su propio trabajo en
`web_audit.yml`: si esa compuerta falla, el ejemplo de R no se anuncia.

    python3 scripts/probar_ejemplos.py            # informe
    python3 scripts/probar_ejemplos.py --check    # exit 1 si algún ejemplo falla

Deja la evidencia en `docs/api/ejemplos.log`.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import os
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
LOG = DOCS / "api" / "ejemplos.log"
SDK = RAIZ / "sdk" / "python"


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def ejecutar(nombre: str, comando: list[str], entorno: dict[str, str]) -> tuple[bool, str, str]:
    t0 = time.time()
    r = subprocess.run(comando, cwd=str(RAIZ), env=entorno, capture_output=True, text=True)
    duracion = time.time() - t0
    ok = r.returncode == 0
    detalle = (r.stdout.strip().splitlines() or [""])[-1]
    if not ok:
        detalle = (r.stderr.strip() or r.stdout.strip()).splitlines()[-1] if (r.stderr or r.stdout) else "sin salida"
    return ok, f"{duracion:.1f} s · {detalle[:110]}", r.stdout + r.stderr


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 si algún ejemplo falla")
    args = ap.parse_args()

    lineas: list[str] = [f"# Ejemplos reproducibles · {datetime.now().isoformat(timespec='seconds')}", ""]

    def anotar(texto: str) -> None:
        print(texto)
        lineas.append(texto)

    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    entorno["PYTHONPATH"] = str(SDK)
    entorno["SIF_CHILE_BASE"] = str(DOCS)

    pruebas = [
        ("python/01_ffmm_extranjero.py", [sys.executable, "examples/python/01_ffmm_extranjero.py"]),
        ("python/02_cruce_tres_industrias.py", [sys.executable, "examples/python/02_cruce_tres_industrias.py"]),
    ]

    puerto = puerto_libre()
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", puerto), manejador)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    entorno_js = dict(entorno, SIF_CHILE_BASE=f"http://127.0.0.1:{puerto}")
    pruebas.append(("javascript/catalogo.mjs", ["node", "examples/javascript/catalogo.mjs"]))
    anotar(f"$ python3 -m http.server {puerto} --directory docs   # para el ejemplo de JavaScript")

    fallos = 0
    for i, (nombre, comando) in enumerate(pruebas):
        anotar(f"$ {' '.join(comando)}")
        ok, detalle, salida = ejecutar(nombre, comando, entorno_js if nombre.endswith(".mjs") else entorno)
        anotar(f"{'OK   ' if ok else 'FALLA'} {nombre} · {detalle}")
        if not ok:
            fallos += 1
            for linea in salida.strip().splitlines()[-6:]:
                anotar(f"      {linea}")
    httpd.shutdown()

    anotar("")
    anotar(f"EJEMPLOS: {len(pruebas) - fallos}/{len(pruebas)} reproducibles"
           if not fallos else f"EJEMPLOS: {fallos} de {len(pruebas)} fallaron")
    LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Evidencia: {LOG.relative_to(RAIZ)}")
    return 1 if (fallos and args.check) else 0


if __name__ == "__main__":
    raise SystemExit(main())

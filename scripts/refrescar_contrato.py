#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenera, desde cero y en un solo camino, el contrato derivado de lo publicado.

Existe por una condición de carrera real: `macro.yml` publica filas nuevas y corre
`build_macro_web.py` + `build_metricas_publicadas.py` en su propio commit, mientras
`contrato_publicado.yml` regenera la cadena completa cada dos horas. Si la cadena vieja
empieza antes de que llegue el commit macro y termina después, cada script lee un estado
distinto: `build_macro_web` vio las filas nuevas y `build_api` no. Así apareció en `main`
el 2026-11-04 un catálogo con 19.814.981 filas y descargas con 19.814.992, `catalog.json`
una fila atrás de su Parquet y `web_audit` en rojo sin que nadie hubiera tocado el código.

Dos defensas, en este orden:

  1. cabeza estable: si `HEAD` cambió mientras corría la cadena, otro publicador acaba de
     escribir y el resultado mezcla dos estados. Se reintenta completo sobre la cabeza nueva.
  2. verificación completa: al final se corre cada generador con `--check`, que falla si el
     artefacto no coincide con lo que producen los datos publicados. Sin esa compuerta, un
     valor a medio generar se publica y lo descubre el siguiente `web_audit`.

Uso (lo llama `.github/workflows/contrato_publicado.yml`):
    python3 scripts/refrescar_contrato.py
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from scripts.build_macro_web import CADENA  # noqa: E402

GIT = ["git", "-C", str(RAIZ)]


def cpu() -> str:
    """`HEAD` actual, para detectar que la rama se movió mientras corría la cadena."""
    return subprocess.run(
        [*GIT, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()


def correr(script: str, *args: str) -> None:
    print(f"::group::{script} {' '.join(args)}".rstrip(), flush=True)
    try:
        subprocess.run(
            [sys.executable, str(RAIZ / "scripts" / script), *args],
            cwd=RAIZ,
            check=True,
        )
    finally:
        print("::endgroup::", flush=True)


def intento(verificar: bool) -> bool:
    """Una pasada completa. Devuelve False si la cabeza se movió a mitad de camino."""
    inicial = cpu()
    for script in CADENA:
        if script == "auditar_contrato.py":
            # `auditar_contrato.py` ya termina con `--check`; sin la bandera enumera y audita.
            correr(script, "--check")
            continue
        correr(script)
        if cpu() != inicial:
            print(f"La cabeza cambió durante {script}: otra publicación entró en la rama.")
            return False
    if verificar:
        for script in CADENA:
            if script in {"verificar_claves.py", "auditar_contrato.py"}:
                continue  # no generan artefactos: solo miden y auditan
            correr(script, "--check")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--intentos", type=int, default=3, help="pasadas completas si la cabeza se mueve")
    ap.add_argument("--sin-verificar", action="store_true", help="omite la pasada final de --check")
    a = ap.parse_args(argv)
    for n in range(1, a.intentos + 1):
        if intento(not a.sin_verificar):
            print(f"Contrato derivado regenerado y verificado (intento {n}/{a.intentos}).")
            return 0
        if n < a.intentos:
            time.sleep(15)
    print("::error title=Contrato derivado::la rama no dejó de moverse; no se publica un contrato a medias")
    return 1


if __name__ == "__main__":
    sys.exit(main())

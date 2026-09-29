"""Lectura y escritura segura de docs/js/data_bundles.js.

El archivo es `window.DATA_BUNDLES = {<clave>: [<filas>], ...};` (JSON en una sola línea).
Varios scripts lo editaban por texto (regex, o agregando `window.DATA_BUNDLES.x = ...;` al
final). Eso no funciona: la búsqueda de la clave nunca coincidía con la forma real del archivo,
así que cada corrida agregaba una asignación duplicada, y cualquier lector que esperara JSON
puro se rompía. Aquí se lee el objeto con `raw_decode` (ignora lo que venga después), se
cambia la clave y se reescribe siempre en forma canónica.
"""
from __future__ import annotations

import json
from pathlib import Path

PREFIJO = "window.DATA_BUNDLES = "


def leer(ruta: Path) -> dict:
    texto = Path(ruta).read_text(encoding="utf-8")
    inicio = texto.index("=") + 1
    objeto, _ = json.JSONDecoder().raw_decode(texto[inicio:].lstrip())
    return objeto


def guardar_claves(ruta: Path, claves: dict) -> bool:
    """Actualiza `claves` en el bundle. Devuelve True si el archivo cambió."""
    ruta = Path(ruta)
    actual = ruta.read_text(encoding="utf-8")
    bundles = leer(ruta)
    bundles.update(claves)
    nuevo = f"{PREFIJO}{json.dumps(bundles, ensure_ascii=False)};\n"
    if nuevo == actual:
        return False
    ruta.write_text(nuevo, encoding="utf-8")
    return True

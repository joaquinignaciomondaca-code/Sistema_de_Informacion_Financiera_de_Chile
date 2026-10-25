#!/usr/bin/env python3
"""Evita enlaces anidados y destinos rotos en el índice Markdown de notas."""
from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

from build_indice_notas import INDICE, limpiar_resumen


def main() -> int:
    casos = {
        "**Documento base:** [`api_publica_factibilidad_2026-10-22.md`](api_publica_factibilidad_2026-10-22.md)": "api_publica_factibilidad_2026-10-22.md",
        "Consulta [el contrato](../api/README.md) para más detalles.": "Consulta el contrato para más detalles.",
        "**Estado:** listo; usa `--check`.": "listo; usa --check.",
        "Una _nota importante_ y el código `a_b`.": "Una nota importante y el código a_b.",
        "Objeto: ahora **un título que se cierra en la línea siguiente": "Objeto: ahora un título que se cierra en la línea siguiente",
    }
    for entrada, esperado in casos.items():
        obtenido = limpiar_resumen(entrada)
        if obtenido != esperado:
            raise SystemExit(f"FALLA: {entrada!r} → {obtenido!r}; esperado {esperado!r}")
        if "](" in obtenido:
            raise SystemExit(f"FALLA: sobrevivió sintaxis de enlace en {obtenido!r}")
        print(f"OK resumen plano: {obtenido}")

    contenido = INDICE.read_text(encoding="utf-8")
    faltantes: list[str] = []
    enlaces_locales = 0
    for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", contenido):
        destino = raw.strip().strip("<>")
        url = urlparse(destino)
        if url.scheme or not url.path:
            continue
        enlaces_locales += 1
        ruta = (INDICE.parent / unquote(url.path)).resolve()
        if not ruta.exists():
            faltantes.append(destino)
    if faltantes:
        raise SystemExit(f"FALLA: destinos locales ausentes en índice: {faltantes}")
    print(f"OK destinos locales del índice: {enlaces_locales}, ninguno ausente")
    print(f"ÍNDICE DE NOTAS: {len(casos)} casos OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

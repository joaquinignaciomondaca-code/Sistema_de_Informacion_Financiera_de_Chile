#!/usr/bin/env python3
"""Genera docs/outputs/indice_busqueda.json para la búsqueda por pregunta o concepto.

Fuentes:
  - docs/reproducibilidad/diccionario.json   (tablas, descripciones y columnas)
  - docs/busqueda_sinonimos.json             (conceptos y preguntas curados a mano)

Falla si un sinónimo apunta a una tabla que no existe en el diccionario, para que un
renombrado no deje la búsqueda apuntando a nada.

Uso:
  python scripts/generar_indice_busqueda.py          # escribe el índice
  python scripts/generar_indice_busqueda.py --check  # solo valida, no escribe
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DICCIONARIO = RAIZ / "docs" / "reproducibilidad" / "diccionario.json"
SINONIMOS = RAIZ / "docs" / "busqueda_sinonimos.json"
SALIDA = RAIZ / "docs" / "outputs" / "indice_busqueda.json"
MAX_SIGNIFICADO = 160


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar términos de forma estable."""
    t = unicodedata.normalize("NFD", str(texto).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip()


def construir(diccionario: dict, sinonimos: dict) -> tuple[dict, list[str]]:
    tablas = {t["id"]: t for t in diccionario["datos"]}
    errores: list[str] = []
    terminos_por_tabla: dict[str, list[str]] = {tid: [] for tid in tablas}

    for concepto in sinonimos["conceptos"]:
        etiquetas = [concepto["termino"], *concepto.get("alias", [])]
        for tid in concepto["tablas"]:
            if tid not in tablas:
                errores.append(f"«{concepto['termino']}» apunta a una tabla inexistente: {tid}")
                continue
            for e in etiquetas:
                if e not in terminos_por_tabla[tid]:
                    terminos_por_tabla[tid].append(e)

    if errores:
        return {}, errores

    entradas = []
    for tid, t in tablas.items():
        entradas.append({
            "id": tid,
            "nombre": t["name"],
            "vista": t["viewName"],
            "sector": t["sector"],
            "sectorLabel": t["sectorLabel"],
            "descripcion": t.get("descripcion", ""),
            "terminos": terminos_por_tabla[tid],
            "columnas": [
                {"nombre": c["name"], "significado": (c.get("significado") or "")[:MAX_SIGNIFICADO]}
                for c in t.get("columnas", [])
            ],
        })

    indice = {
        "generado": diccionario.get("generado"),
        "nota": "Índice para la búsqueda por pregunta. Generado por scripts/generar_indice_busqueda.py; no editar a mano.",
        "tablas": entradas,
    }
    return indice, []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="solo valida los sinónimos")
    args = ap.parse_args()

    diccionario = json.loads(DICCIONARIO.read_text(encoding="utf-8"))
    sinonimos = json.loads(SINONIMOS.read_text(encoding="utf-8"))
    indice, errores = construir(diccionario, sinonimos)
    if errores:
        for e in errores:
            print("ERROR", e, file=sys.stderr)
        return 1

    con_termino = sum(1 for t in indice["tablas"] if t["terminos"])
    print(f"Tablas: {len(indice['tablas'])}; con al menos un término: {con_termino}; "
          f"conceptos: {len(sinonimos['conceptos'])}")
    if args.check:
        return 0
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(indice, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("→", SALIDA.relative_to(RAIZ), f"({SALIDA.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

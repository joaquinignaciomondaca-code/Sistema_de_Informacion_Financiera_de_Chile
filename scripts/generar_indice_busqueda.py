#!/usr/bin/env python3
"""Genera docs/outputs/indice_busqueda.json para la búsqueda por pregunta o concepto.

Fuentes:
  - docs/reproducibilidad/diccionario.json   (tablas, descripciones y columnas)
  - docs/busqueda_sinonimos.json             (conceptos y preguntas curados a mano)
  - docs/api/v2/catalog.json                 (ID, fuente primaria y corte)
  - docs/js/download_catalog.js              (formatos de archivos descargables)

Falla si un sinónimo apunta a una tabla que no existe en el diccionario, para que un
renombrado no deje la búsqueda apuntando a nada.

Uso:
  python scripts/generar_indice_busqueda.py          # escribe el índice
  python scripts/generar_indice_busqueda.py --check  # valida fuentes e índice, no escribe
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
CATALOGO_API = RAIZ / "docs" / "api" / "v2" / "catalog.json"
CATALOGO_DESCARGAS = RAIZ / "docs" / "js" / "download_catalog.js"
MAX_SIGNIFICADO = 160


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar términos de forma estable."""
    t = unicodedata.normalize("NFD", str(texto).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip()


def construir(
    diccionario: dict,
    sinonimos: dict,
    catalogo_api: dict,
    catalogo_descargas: dict,
) -> tuple[dict, list[str]]:
    tablas = {t["id"]: t for t in diccionario["datos"]}
    errores: list[str] = []
    terminos_por_tabla: dict[str, list[str]] = {tid: [] for tid in tablas}
    objetos_api = catalogo_api.get("objetos", [])
    api_por_id = {o["id"]: o for o in objetos_api if o.get("id")}
    items_descarga = [
        item for grupo in catalogo_descargas.get("grupos", [])
        for item in grupo.get("items", [])
    ]
    descargas_por_id = {item["id"]: item for item in items_descarga if item.get("id")}
    ids_tablas = set(tablas)
    if len(tablas) != len(diccionario.get("datos", [])):
        errores.append("IDs duplicados en docs/reproducibilidad/diccionario.json")
    if len(api_por_id) != len(objetos_api):
        errores.append("IDs faltantes o duplicados en catalog.json")
    if len(descargas_por_id) != len(items_descarga):
        errores.append("IDs faltantes o duplicados en DOWNLOAD_CATALOG")
    if ids_tablas != set(api_por_id):
        errores.append(
            "IDs del diccionario/API distintos: "
            f"faltan_en_api={sorted(ids_tablas - set(api_por_id))}, "
            f"sobran_en_api={sorted(set(api_por_id) - ids_tablas)}"
        )
    if ids_tablas != set(descargas_por_id):
        errores.append(
            "IDs del diccionario/Descargas distintos: "
            f"faltan_en_descargas={sorted(ids_tablas - set(descargas_por_id))}, "
            f"sobran_en_descargas={sorted(set(descargas_por_id) - ids_tablas)}"
        )

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
        api = api_por_id[tid]
        descarga = descargas_por_id[tid]
        fuente = api.get("fuente")
        corte = api.get("corte")
        if not fuente or not corte:
            errores.append(f"{tid} no tiene fuente y/o corte declarados en catalog.json")
            continue
        archivos = descarga.get("archivos", [])
        formatos = sorted({
            Path(a.get("ruta", "")).suffix.lstrip(".").upper()
            for a in archivos if Path(a.get("ruta", "")).suffix
        })
        entradas.append({
            "id": tid,
            "fuente": fuente,
            "corte": corte,
            "formatos": formatos,
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
    return indice, errores


def cargar_catalogo_descargas() -> dict:
    texto = CATALOGO_DESCARGAS.read_text(encoding="utf-8")
    prefijo = "window.DOWNLOAD_CATALOG ="
    try:
        payload = texto.split(prefijo, 1)[1].strip()
    except IndexError as exc:
        raise ValueError("download_catalog.js no expone window.DOWNLOAD_CATALOG") from exc
    if not payload.endswith(";"):
        raise ValueError("download_catalog.js no termina con un objeto JSON generado")
    return json.loads(payload[:-1].strip())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="valida fuentes e índice generado, sin escribir")
    args = ap.parse_args()

    diccionario = json.loads(DICCIONARIO.read_text(encoding="utf-8"))
    sinonimos = json.loads(SINONIMOS.read_text(encoding="utf-8"))
    catalogo_api = json.loads(CATALOGO_API.read_text(encoding="utf-8"))
    try:
        catalogo_descargas = cargar_catalogo_descargas()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR no se pudo leer el catálogo de descargas: {exc}", file=sys.stderr)
        return 1
    indice, errores = construir(diccionario, sinonimos, catalogo_api, catalogo_descargas)
    if errores:
        for e in errores:
            print("ERROR", e, file=sys.stderr)
        return 1

    con_termino = sum(1 for t in indice["tablas"] if t["terminos"])
    print(f"Tablas: {len(indice['tablas'])}; con al menos un término: {con_termino}; "
          f"conceptos: {len(sinonimos['conceptos'])}")
    if args.check:
        if not SALIDA.exists():
            print(f"ERROR falta {SALIDA.relative_to(RAIZ)}; regenera el índice", file=sys.stderr)
            return 1
        publicado = json.loads(SALIDA.read_text(encoding="utf-8"))
        if publicado != indice:
            print(f"ERROR {SALIDA.relative_to(RAIZ)} está desactualizado; ejecuta python scripts/generar_indice_busqueda.py", file=sys.stderr)
            return 1
        print(f"ÍNDICE OK: {SALIDA.relative_to(RAIZ)} coincide con sus fuentes")
        return 0
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(indice, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("→", SALIDA.relative_to(RAIZ), f"({SALIDA.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

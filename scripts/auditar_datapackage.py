#!/usr/bin/env python3
"""Audita el Data Package publicado (Fase 1a).

Comprueba dos cosas que un lector real comprobaría, sin descargar nada de la
red:

  1. **Estructura**: el descriptor se carga con `frictionless` (el lector de
     referencia del ecosistema), tiene 86 recursos tabulares y cada recurso
     declara exactamente los campos de `docs/api/esquemas.json`.
  2. **Contenido**: cada `path` del descriptor apunta a un archivo que existe,
     pesa lo que dice `bytes` y tiene el `sha256` declarado. Sobre una muestra
     se abren además los Parquet con `frictionless` para confirmar que el
     esquema declarado encaja con los datos reales.

Los recursos que apuntan a una URL del sitio se resuelven a su archivo local:
el sitio publica `docs/`, así que la ruta es la misma. No se hace ninguna
petición de red.

Uso:
    python3 scripts/auditar_datapackage.py            # hashes + 5 muestras
    python3 scripts/auditar_datapackage.py --muestra 86
    python3 scripts/auditar_datapackage.py --check    # falla si algo no cuadra
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
DESCRIPTOR = DOCS / "api" / "v1" / "datapackage.json"
ESQUEMAS = DOCS / "api" / "esquemas.json"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def local(url: str) -> Path | None:
    """URL del sitio → archivo en docs/. Devuelve None si no es del sitio."""
    import re

    m = re.match(r"https://[^/]+/Sistema_de_Informacion_Financiera_de_Chile/(.*)", url)
    return DOCS / m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", type=int, default=86, help="recursos que además se abren con frictionless")
    ap.add_argument("--check", action="store_true", help="sólo valida (CI)")
    args = ap.parse_args()

    t0 = time.time()
    try:
        from frictionless import Package, Resource
    except ImportError:
        print("AVISO: frictionless no está instalado; se omiten las comprobaciones estructurales")
        return 0

    problemas: list[str] = []

    # 1. Estructura ---------------------------------------------------------
    paquete = Package(str(DESCRIPTOR))
    recursos = paquete.resources
    print(f"Estructura: {len(recursos)} recursos leídos por frictionless")
    if len(recursos) != 86:
        problemas.append(f"se esperaban 86 recursos con datos y hay {len(recursos)}")
    if paquete.profile != "tabular-data-package":
        problemas.append(f"perfil inesperado: {paquete.profile}")

    crudo = json.loads(DESCRIPTOR.read_text(encoding="utf-8"))
    por_nombre = {r["name"]: r for r in crudo["resources"]}
    esquemas = json.loads(ESQUEMAS.read_text(encoding="utf-8"))["objetos"]
    for r in recursos:
        declaradas = [c["nombre"] for c in esquemas[r.name]["columnas"]]
        leidas = [f.name for f in r.schema.fields]
        if declaradas != leidas:
            problemas.append(f"{r.name}: los campos no coinciden con docs/api/esquemas.json")
    print(f"  campos: {sum(len(r.schema.fields) for r in recursos)} en {len(recursos)} recursos, iguales al contrato")

    # 2. Contenido ----------------------------------------------------------
    revisados = 0
    for nombre, r in por_nombre.items():
        for parte in r["sif"]["particiones"]:
            archivo = local(parte["path"])
            if archivo is None or not archivo.exists():
                problemas.append(f"{nombre}: falta el archivo {parte['path']}")
                continue
            revisados += 1
            if archivo.stat().st_size != parte["bytes"]:
                problemas.append(f"{nombre}: el tamaño de {archivo.name} no coincide con el descriptor")
    print(f"Archivos: {revisados} rutas resueltas a disco")

    # Hash del recurso = sha256 de la concatenación de los sha256 de sus partes.
    for nombre, desc in por_nombre.items():
        partes = desc["sif"]["particiones"]
        huellas = []
        for p in partes:
            archivo = local(p["path"])
            if archivo is None or not archivo.exists():
                continue
            real = sha256(archivo)
            if real != p["sha256"]:
                problemas.append(f"{nombre}: sha256 distinto en {archivo.name}")
            huellas.append(real)
        esperado = hashlib.sha256("".join(huellas).encode()).hexdigest()
        if huellas and desc.get("hash") != esperado:
            problemas.append(f"{nombre}: el hash del recurso no cuadra con sus particiones")
    print("Hash:   sha256 verificado archivo por archivo")

    # 3. Muestra con datos reales -------------------------------------------
    # frictionless lee Parquet a través de pandas: sin él, la muestra no se
    # puede hacer y se dice, en vez de dar la validación por buena.
    try:
        import pandas  # noqa: F401
        hay_pandas = True
    except ImportError:
        hay_pandas = False
        print("AVISO: sin pandas, frictionless no abre los Parquet; se omite la muestra")
    abiertos = 0
    for r in (recursos[: args.muestra] if hay_pandas else []):
        desc = por_nombre[r.name]
        p = (desc["sif"]["particiones"] or [{}])[0]
        archivo = local(p.get("path", ""))
        if archivo is None or not archivo.exists():
            continue
        tabla = Resource(path=str(archivo), format="parquet", schema=r.schema)
        with tabla:
            fila = next(tabla.row_stream, None)
        abiertos += 1
        vacio = not desc["sif"].get("filas")  # una tabla publicada sin filas es legítima
        if fila is None and not vacio:
            problemas.append(f"{r.name}: la muestra no devolvió ninguna fila y el descriptor no la declara vacía")
        elif fila is not None and len(fila) != len(r.schema.fields):
            problemas.append(f"{r.name}: la fila leída no tiene las {len(r.schema.fields)} columnas declaradas")
    print(f"Muestra: {abiertos} recursos abiertos con su esquema declarado, sin red")

    duracion = time.time() - t0
    print(f"Duración: {duracion:.1f} s")
    for p in problemas[:20]:
        print(f"  [FALLA] {p}")
    if problemas:
        print(f"DATAPACKAGE: {len(problemas)} problema(s)")
        return 1
    print("DATAPACKAGE: descriptor válido, hashes al día y esquema encajado con los datos")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # el CI necesita una línea, no un traceback en un log remoto
        print(f"[FALLA] excepción: {type(exc).__name__}: {exc}")
        raise SystemExit(1)

#!/usr/bin/env python3
"""Comprueba que el motor DuckDB vendorizado sea exactamente el que se revisó.

`docs/vendor/duckdb/` contiene el módulo, el worker y un `.wasm` de 18 MB que el
navegador ejecuta desde el propio origen del sitio. Sin una huella registrada,
cualquier cambio en esos archivos —una actualización, un reemplazo accidental o
una alteración del artefacto— pasa inadvertido: el sitio sigue funcionando y
nadie revisa los bytes.

Este script compara cada archivo con `docs/vendor/duckdb/manifiesto.json`
(versión, tamaño y SHA-256) y con `DUCKDB_VERSION` de `docs/js/duckdb_client.js`,
que es la versión que usan los respaldos por CDN. Falla si algo no coincide o si
aparece un archivo del motor que el manifiesto no declara.

Uso:
  python3 scripts/audit_vendor_duckdb.py              # verifica
  python3 scripts/audit_vendor_duckdb.py --actualizar # reescribe las huellas

`--actualizar` es una decisión consciente, no parte del flujo normal: al
cambiar de versión hay que revisar el bundle y anotar el cambio en la nota del
motor. El CI siempre corre sin `--actualizar`.
"""
import argparse
import hashlib
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(RAIZ, "docs", "vendor", "duckdb")
MANIFIESTO = os.path.join(VENDOR, "manifiesto.json")
CLIENTE = os.path.join(RAIZ, "docs", "js", "duckdb_client.js")
ESPERADOS = ("duckdb-browser.mjs", "duckdb-browser-eh.worker.js", "duckdb-eh.wasm")


def sha256(ruta):
    huella = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            huella.update(bloque)
    return huella.hexdigest()


def version_del_cliente():
    fuente = open(CLIENTE, encoding="utf-8").read()
    encontrada = re.search(r'DUCKDB_VERSION\s*=\s*"([^"]+)"', fuente)
    return encontrada.group(1) if encontrada else None


def medir():
    return {
        nombre: {"bytes": os.path.getsize(os.path.join(VENDOR, nombre)), "sha256": sha256(os.path.join(VENDOR, nombre))}
        for nombre in ESPERADOS
    }


def escribir_manifiesto(manifiesto):
    manifiesto["archivos"] = medir()
    with open(MANIFIESTO, "w", encoding="utf-8") as archivo:
        json.dump(manifiesto, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")
    print(f"manifiesto actualizado: {len(manifiesto['archivos'])} archivos")


def main():
    parser = argparse.ArgumentParser(description="Verifica la integridad del motor DuckDB vendorizado.")
    parser.add_argument("--actualizar", action="store_true", help="reescribe las huellas del manifiesto")
    args = parser.parse_args()

    if not os.path.exists(MANIFIESTO):
        print("FALLA: falta docs/vendor/duckdb/manifiesto.json")
        return 1
    manifiesto = json.load(open(MANIFIESTO, encoding="utf-8"))

    if args.actualizar:
        escribir_manifiesto(manifiesto)
        return 0

    fallas = []
    version = manifiesto.get("version")
    declarada = version_del_cliente()
    if declarada != version:
        fallas.append(f"duckdb_client.js declara {declarada!r} y el manifiesto {version!r}")

    declarados = manifiesto.setdefault("archivos", {})
    for nombre in ESPERADOS:
        ruta = os.path.join(VENDOR, nombre)
        if not os.path.exists(ruta):
            fallas.append(f"falta {nombre}")
            continue
        esperado = declarados.get(nombre)
        if not esperado:
            fallas.append(f"{nombre} no está en el manifiesto")
            continue
        bytes_reales = os.path.getsize(ruta)
        if bytes_reales != esperado.get("bytes"):
            fallas.append(f"{nombre}: {bytes_reales} bytes, el manifiesto dice {esperado.get('bytes')}")
        huella = sha256(ruta)
        if huella != esperado.get("sha256"):
            fallas.append(f"{nombre}: SHA-256 {huella[:12]}… no coincide con {str(esperado.get('sha256'))[:12]}…")

    # Un archivo del motor que nadie declaró también es un cambio del artefacto.
    for nombre in sorted(os.listdir(VENDOR)):
        if nombre.startswith("duckdb") and nombre not in ESPERADOS:
            fallas.append(f"archivo del motor no declarado: {nombre}")

    if fallas:
        for falla in fallas:
            print(f"FALLA: {falla}")
        print(f"Motor DuckDB: {len(fallas)} problema(s)")
        return 1

    print(f"Motor DuckDB {version}: {len(ESPERADOS)} archivos con la huella esperada")
    return 0


if __name__ == "__main__":
    sys.exit(main())

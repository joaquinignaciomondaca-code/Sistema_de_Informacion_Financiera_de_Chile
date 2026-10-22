#!/usr/bin/env python3
"""Genera el Data Package de la API (Fase 1a de la ruta).

Un Data Package es un descriptor JSON que cualquier herramienta del ecosistema
Frictionless puede leer: dice qué recursos hay, dónde están, qué columnas
tienen, cuánto pesan y qué hash tienen. Este script lo construye desde lo ya
verificado —manifiesto, esquemas, reconciliación y claves—, no desde una lista
escrita a mano, y valida que no invente nada.

Reglas:

  * **Un recurso por objeto del contrato**, no por archivo. Los objetos con
    varias particiones las publican en `path` (multipart, admitido por la
    especificación) y el detalle en `sif.particiones`.
  * **Los campos salen de `docs/api/esquemas.json`**, y los tipos se traducen a
    los de Table Schema (`VARCHAR` → `string`, `BIGINT` → `integer`…). Si un
    campo no está en el esquema, no se publica.
  * **`primaryKey` sólo cuando está probada** en `docs/api/claves.csv` sobre
    todas las filas. Los objetos con PK declarada que no es única, o con filas
    repetidas, **no** llevan clave: prometer una clave falsa es peor que no
    tener ninguna.
  * **Cada hash se calcula del archivo**, y su conjunto produce el
    `data_release`. Nada de fechas inventadas.
  * **Ningún recurso declara una licencia que no esté comprobada**: los datos
    son de terceros y `DATA_LICENSE.md` los deja en `pendiente`.

Genera `docs/api/v1/datapackage.json`.

Uso:
    python3 scripts/build_api.py                 # escribe el descriptor
    python3 scripts/build_api.py --check         # falla si está desactualizado
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
API = DOCS / "api"
V1 = API / "v1"
sys.path.insert(0, str(RAIZ / "scripts"))

import audit_consultas_sugeridas as ac  # noqa: E402

DESTINO = V1 / "datapackage.json"
ESQUEMAS = API / "esquemas.json"
CLAVES = API / "claves.csv"
RECONCILIACION = API / "reconciliacion.csv"

# URL del sitio, la que ya usa el README. La decisión de si es la canónica
# (tarea 0.1) sigue abierta: hasta entonces el descriptor la marca provisional.
SITIO = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/"
REPO = "https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile"

API_VERSION = "v1"
VERSION_CONTRATO = "1.0.0"  # semver del descriptor; la regla está en la ruta (0.3)

TIPOS = {
    "VARCHAR": "string",
    "VARCHAR[]": "array",
    "BIGINT": "integer",
    "INTEGER": "integer",
    "SMALLINT": "integer",
    "TINYINT": "integer",
    "DOUBLE": "number",
    "REAL": "number",
    "BOOLEAN": "boolean",
    "DATE": "date",
    "TIMESTAMP": "datetime",
    "TIMESTAMPTZ": "datetime",
}

FUENTES = {
    "CMF": ("CMF — Comisión para el Mercado Financiero", "https://www.cmfchile.cl"),
    "BCCh": ("BCCh — Banco Central de Chile", "https://si3.bcentral.cl"),
    "SPensiones": ("SPensiones — Superintendencia de Pensiones", "https://www.spensiones.cl"),
    "SUSESO": ("SUSESO — Superintendencia de Seguridad Social", "https://www.suseso.cl"),
}


def _url(ruta: Path) -> str:
    """URL pública de un archivo de `docs/`.

    Frictionless rechaza rutas con `..` («path is not safe»), así que el
    descriptor no puede usar rutas relativas al propio archivo: publica URLs
    del sitio. Se comprueba que el archivo exista en `docs/`.
    """
    rel = ruta.resolve().relative_to(DOCS.resolve()).as_posix()
    if not (DOCS / rel).exists():
        raise SystemExit(f"ERROR: {rel} no existe en docs/")
    return SITIO + rel


def _licencia() -> str:
    return f"{REPO}/blob/main/DATA_LICENSE.md"


def agencias(origen: str) -> list[str]:
    """Las fuentes que menciona el campo `origen` del manifiesto."""
    dicho = origen.lower()
    fuera = []
    if "cmf" in dicho or "mercado financiero" in dicho:
        fuera.append("CMF")
    if "banco central" in dicho or "bcentral" in dicho:
        fuera.append("BCCh")
    if "pensiones" in dicho:
        fuera.append("SPensiones")
    if "suseso" in dicho or "seguridad social" in dicho:
        fuera.append("SUSESO")
    return fuera


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_csv(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def campos_de(columnas: list[dict]) -> list[dict]:
    """Columnas del contrato → `fields` de Table Schema."""
    campos = []
    for col in columnas:
        tipo = TIPOS.get(col["tipo"])
        if tipo is None:
            raise SystemExit(f"ERROR: tipo sin traducción a Table Schema: {col['tipo']} ({col['nombre']})")
        campo = {"name": col["nombre"], "type": tipo}
        if col.get("significado"):
            campo["description"] = col["significado"]
        if col.get("rol"):
            campo["sif_rol"] = col["rol"]
        if col.get("sin_valores"):
            campo["sif_sin_valores"] = True
        campos.append(campo)
    return campos


def construir() -> dict:
    esquemas = json.loads(ESQUEMAS.read_text(encoding="utf-8"))
    objetos = esquemas["objetos"]
    manifiesto = {t["id"]: t for t in json.loads((RAIZ / "data_manifest.json").read_text(encoding="utf-8"))["tables"]}
    reconciliacion = {f["objeto"]: f for f in cargar_csv(RECONCILIACION)}

    claves: dict[str, dict] = {}
    for fila in cargar_csv(CLAVES):
        if fila["tipo"] == "pk":
            claves[fila["objeto"]] = fila

    recursos = []
    hashes: list[str] = []
    for nombre in sorted(objetos):
        info = objetos[nombre]
        if not info["columnas"]:
            continue  # los 4 vacíos se publican en el catálogo, sin archivo que describir

        datos = next(v for v in ac.vistas_semanticas() if v["name"] == nombre)
        ficheros = [Path(p) for p in ac.ficheros_de(datos)]
        particiones = []
        for f in ficheros:
            h = sha256(f)
            hashes.append(h)
            particiones.append({
                "path": _url(f),
                "bytes": f.stat().st_size,
                "sha256": h,
                "filas": _filas(f),
            })

        recon = reconciliacion.get(nombre, {})
        tabla = manifiesto.get(info.get("manifest_id") or "", {})
        origen = tabla.get("origen", "")
        urls = re.findall(r"https?://[^\s,)»]+", origen)
        fuentes = [
            {"title": FUENTES[a][0], "path": urls[0] if urls else FUENTES[a][1], "sif_estado": "pendiente"}
            for a in agencias(origen)
        ] or [{"title": "Origen no declarado", "sif_estado": "pendiente"}]

        recurso = {
            "profile": "tabular-data-resource",
            "name": nombre,
            "title": recon.get("nombre_visible") or info.get("nombre_visible") or nombre,
            "description": tabla.get("descripcion") or "",
            "path": [p["path"] for p in particiones],
            "scheme": "file",
            "format": "parquet",
            "mediatype": "application/vnd.apache.parquet",
            "bytes": sum(p["bytes"] for p in particiones),
            "hash": hashlib.sha256("".join(p["sha256"] for p in particiones).encode()).hexdigest(),
            "schema": {"fields": campos_de(info["columnas"])},
            "sources": fuentes,
            "licenses": [{"name": "Uso condicionado por la fuente", "path": _licencia()}],
            "sif": {
                "manifest_id": info.get("manifest_id"),
                "sector": info.get("sector"),
                "nivel": recon.get("nivel"),
                "estado": recon.get("estado"),
                "deriva_de": recon.get("deriva_de") or None,
                "puente": recon.get("puente"),
                "filtro": info.get("filtro"),
                "particiones": particiones,
                "filas": info.get("filas"),
                "corte": tabla.get("corte"),
                "ultima_actualizacion": tabla.get("ultima_actualizacion"),
                "extracted_at": (tabla.get("metadatos") or {}).get("fecha_extraccion"),
                "licencia_estado": "pendiente",
                "api_version": API_VERSION,
            },
        }

        clave = claves.get(nombre)
        if clave and clave["estado"] in ("ok", "propuesta") and clave["columnas"]:
            columnas = [c.strip() for c in clave["columnas"].split("+")]
            recurso["schema"]["primaryKey"] = columnas
            recurso["sif"]["clave_origen"] = "declarada" if clave["declarada"] == "si" else "propuesta"
        else:
            recurso["sif"]["clave_origen"] = None
            recurso["sif"]["sin_clave"] = clave["estado"] if clave else "no_verificada"

        recursos.append(recurso)

    # El `data_release` no es una fecha elegida a mano: es el contenido.
    huella = hashlib.sha256("".join(sorted(hashes)).encode()).hexdigest()[:12]
    fechas = [t.get("ultima_actualizacion", "") for t in manifiesto.values() if t.get("ultima_actualizacion")]
    fecha_datos = max(fechas) if fechas else ""
    data_release = f"{fecha_datos}.{huella}"

    return {
        "profile": "tabular-data-package",
        "name": "sif-chile",
        "title": "Sistema de Información Financiera de Chile",
        "description": (
            "Datos financieros chilenos normalizados a Parquet desde fuentes públicas "
            "(CMF y Banco Central de Chile, entre otras), con esquema verificado y claves "
            "comprobadas sobre todas las filas publicadas."
        ),
        "version": VERSION_CONTRATO,
        "created": f"{fecha_datos}T00:00:00",
        "homepage": "https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile",
        "licenses": [{"name": "Datos: uso condicionado por la fuente · Código: MIT", "path": _licencia()}],
        "sources": [{"title": t, "path": u} for t, u in FUENTES.values()],
        "sif": {
            "api_version": API_VERSION,
            "data_release": data_release,
            "versionado": {
                "regla": "semver; un dato nuevo NO sube la versión (eso es data_release)",
                "mayor": "se rompe un cliente: quitar o renombrar recurso o columna, cambiar un tipo",
                "menor": "se puede ignorar: añadir recurso, columna al final o campo sif.*",
                "parche": "sólo datos: corrige valores sin tocar el esquema",
            },
            "contrato": {
                "reconciliacion": SITIO + "api/reconciliacion.csv",
                "esquemas": SITIO + "api/esquemas.json",
                "claves": SITIO + "api/claves.csv",
                "datapackage": SITIO + "api/v1/datapackage.json",
                "licencia": _licencia(),
            },
            "objetos_sin_archivo": esquemas["resumen"]["sin_esquema"],
            "filas_unicas": esquemas["resumen"]["filas_unicas"],
            "base_url": SITIO,
            "base_url_estado": "decidida (D1): Pages publica la API; Vercel redirige /api/* aquí con un 307",
            "espejo": "https://sistema-de-informacion-financiera-de-chile-docs.vercel.app",
        },
        "resources": recursos,
    }


_CACHE_FILAS: dict[Path, int] = {}


def _filas(ruta: Path) -> int:
    if ruta not in _CACHE_FILAS:
        import pyarrow.parquet as pq

        _CACHE_FILAS[ruta] = pq.ParquetFile(ruta).metadata.num_rows
    return _CACHE_FILAS[ruta]


def comparable(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="falla si el descriptor versionado está desactualizado")
    args = ap.parse_args()

    doc = construir()
    recursos = doc["resources"]
    con_clave = [r for r in recursos if "primaryKey" in r["schema"]]
    sin_clave = [r for r in recursos if "primaryKey" not in r["schema"]]

    print(f"Recursos: {len(recursos)} · con primaryKey: {len(con_clave)} · sin clave: {len(sin_clave)}")
    print(f"Campos: {sum(len(r['schema']['fields']) for r in recursos)} · particiones: {sum(len(r['path']) for r in recursos)}")
    print(f"Bytes: {sum(r['bytes'] for r in recursos):,}".replace(",", ".") + f" · data_release: {doc['sif']['data_release']}")

    if args.check:
        if not DESTINO.exists():
            print(f"ERROR: falta {DESTINO.relative_to(RAIZ)}; ejecuta scripts/build_api.py")
            return 1
        actual = json.loads(DESTINO.read_text(encoding="utf-8"))
        if comparable(actual) != comparable(doc):
            print("ERROR: docs/api/v1/datapackage.json está desactualizado; ejecuta scripts/build_api.py")
            antes = {r["name"]: r for r in actual["resources"]}
            ahora = {r["name"]: r for r in recursos}
            for nombre in sorted(set(antes) | set(ahora)):
                if nombre not in antes or nombre not in ahora:
                    print(f"  · recurso {'nuevo' if nombre not in antes else 'retirado'}: {nombre}")
                    continue
                a, b = antes[nombre], ahora[nombre]
                if a.get("hash") != b.get("hash"):
                    print(f"  · {nombre}: cambió el contenido (hash)")
                elif [c["name"] for c in a["schema"]["fields"]] != [c["name"] for c in b["schema"]["fields"]]:
                    print(f"  · {nombre}: cambiaron las columnas")
            return 1
        print("DATAPACKAGE: descriptor al día")
        return 0

    V1.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Escrito en {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

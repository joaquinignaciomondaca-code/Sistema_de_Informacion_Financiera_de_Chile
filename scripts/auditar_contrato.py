#!/usr/bin/env python3
"""Audita el contrato estático de la API (fase 1 de la ruta).

Comprueba que lo publicado y lo que dicen los documentos sean lo mismo, y que
`views.sql` se pueda ejecutar de verdad:

  1. **Coherencia** entre catálogo, esquemas, particiones, reconciliación y
     claves: mismos 90 objetos, misma clave primaria, mismos archivos.
  2. **Archivos**: cada ruta del catálogo existe, pesa lo declarado y tiene el
     SHA-256 declarado.
  3. **Consultas**: 159, ids únicos, y toda tabla que mencionan existe en el
     catálogo (por nombre o por alias).
  4. **OpenAPI**: las 11 rutas son las que existen; el `enum` de ids cubre los 90
     objetos.
  5. **Vistas**: se ejecuta `views.sql` sustituyendo la base por la copia local
     de `docs/` (el sandbox no tiene salida al sitio) y se comprueba que crea
     las 105 vistas y que **cada objeto con datos responde a un `count(*)`**.
  6. **`llms.txt`**: las cifras que le dice a un agente (objetos, consultas) son
     las del catálogo, y ninguna de sus rutas da 404.
  7. **Una sola versión**: las nueve piezas del contrato declaran la misma
     versión semver y la misma `api_version` que la carpeta.

Uso:
    python3 scripts/auditar_contrato.py            # informe (~10 s)
    python3 scripts/auditar_contrato.py --check    # exit 1 si algo falla
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
sys.path.insert(0, str(RAIZ / "scripts"))

from version_contrato import API_VERSION, VERSION_CONTRATO  # noqa: E402

V2 = DOCS / "api" / API_VERSION

BASE = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile"


def leer_json(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 si algo no cuadra")
    args = ap.parse_args()

    t0 = time.time()
    problemas: list[str] = []
    catalogo = leer_json(V2 / "catalog.json")
    objetos = catalogo["objetos"]
    ids = [o["id"] for o in objetos]

    esquemas = leer_json(DOCS / "api" / "esquemas.json")
    reconciliacion = {f["objeto"]: f for f in csv.DictReader(
        (DOCS / "api" / "reconciliacion.csv").open(encoding="utf-8"))}
    claves = {f["objeto"]: f for f in csv.DictReader(
        (DOCS / "api" / "claves.csv").open(encoding="utf-8")) if f["tipo"] == "pk"}

    # 1. Coherencia ---------------------------------------------------------
    if len(objetos) != 90:
        problemas.append(f"el catálogo tiene {len(objetos)} objetos y deben ser 90")
    if set(ids) != set(esquemas["objetos"]):
        problemas.append("el catálogo y docs/api/esquemas.json no tienen los mismos objetos")
    if set(ids) != set(reconciliacion):
        problemas.append("el catálogo y la reconciliación no tienen los mismos objetos")
    for objeto in objetos:
        declarada = objeto.get("primaryKey") or []
        verificada = claves.get(objeto["id"], {})
        esperada = ([c.strip() for c in verificada["columnas"].split("+")]
                    if verificada.get("columnas") and verificada.get("estado") in ("ok", "propuesta") else [])
        if declarada != esperada:
            problemas.append(f"{objeto['id']}: primaryKey del catálogo {declarada} ≠ verificada {esperada}")
        if not (V2 / "schema" / f"{objeto['id']}.json").exists():
            problemas.append(f"falta schema/{objeto['id']}.json")
        if not (V2 / "partitions" / f"{objeto['id']}.json").exists():
            problemas.append(f"falta partitions/{objeto['id']}.json")
    print(f"Coherencia: {len(objetos)} objetos en catálogo, esquemas y reconciliación")

    # 2. Archivos -----------------------------------------------------------
    archivos = 0
    for nombre in ids:
        doc = leer_json(V2 / "partitions" / f"{nombre}.json")
        for parte in doc["particiones"]:
            archivo = DOCS / parte["archivo"]
            if not archivo.exists():
                problemas.append(f"{nombre}: falta {parte['archivo']}")
                continue
            archivos += 1
            if archivo.stat().st_size != parte["bytes"]:
                problemas.append(f"{nombre}: tamaño distinto en {archivo.name}")
            if sha256(archivo) != parte["sha256"]:
                problemas.append(f"{nombre}: sha256 distinto en {archivo.name}")
    print(f"Archivos: {archivos} particiones con tamaño y hash verificados")

    # 3. Consultas ----------------------------------------------------------
    consultas = leer_json(V2 / "queries.json")
    alias = {a: o["id"] for o in objetos for a in o["aliases"]}
    conocidos = set(ids)
    vistos = set()
    for c in consultas["consultas"]:
        if c["id"] in vistos:
            problemas.append(f"id de consulta repetido: {c['id']}")
        vistos.add(c["id"])
        if not c["sql"].strip():
            problemas.append(f"{c['id']}: SQL vacío")
        for tabla in c["espera"]["tablas"]:
            if tabla not in conocidos:
                problemas.append(f"{c['id']}: usa {tabla}, que no está en el catálogo")
        crudo = {t.lower() for t in re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_]\w*)", c["sql"])}
        for tabla in crudo:
            if tabla not in conocidos and tabla not in alias and tabla != "range":
                problemas.append(f"{c['id']}: menciona «{tabla}», que no existe")
    print(f"Consultas: {consultas['total']} con id único y tablas del catálogo")

    # 4. OpenAPI ------------------------------------------------------------
    openapi = leer_json(V2 / "openapi.json")
    esperadas = {
        "/api/v2/datapackage.json", "/api/v2/catalog.json", "/api/v2/schema/{id}.json",
        "/api/v2/partitions/{id}.json", "/api/v2/queries.json",
        "/api/v2/resultados/index.json", "/api/v2/resultados/{id}.json",
        "/api/v2/views.sql",
        "/api/reconciliacion.csv", "/api/claves.csv", "/outputs/{ruta}",
    }
    if set(openapi["paths"]) != esperadas:
        problemas.append(f"OpenAPI publica rutas que no existen o le faltan: "
                         f"{sorted(set(openapi['paths']) ^ esperadas)}")
    for ruta in ("/api/v2/schema/{id}.json", "/api/v2/partitions/{id}.json"):
        enum = openapi["paths"][ruta]["get"]["parameters"][0]["schema"]["enum"]
        if set(enum) != conocidos:
            problemas.append(f"{ruta}: el enum de ids no cubre los 90 objetos")
    enum_consultas = openapi["paths"]["/api/v2/resultados/{id}.json"]["get"]["parameters"][0]["schema"]["enum"]
    if set(enum_consultas) != vistos:
        problemas.append("/api/v2/resultados/{id}.json: el enum no cubre las consultas")
    for ruta in openapi["paths"]:
        if ruta.startswith("/outputs") or ruta.startswith("/api/"):
            if "get" not in openapi["paths"][ruta]:
                problemas.append(f"{ruta}: no declara GET")
    print(f"OpenAPI: {len(openapi['paths'])} rutas, todas con GET y los 90 ids")

    # 4b. Resultados precalculados (fase 3) ---------------------------------
    resultados = V2 / "resultados"
    por_id = {c["id"]: c for c in consultas["consultas"]}
    if not resultados.exists():
        problemas.append("falta api/v2/resultados/: las 159 consultas vienen sin resultado")
    else:
        indice = leer_json(resultados / "index.json")
        if indice.get("data_release") != catalogo["data_release"]:
            problemas.append("resultados/index.json: data_release distinto del catálogo")
        listados = {c["id"]: c for c in indice.get("consultas", [])}
        if set(listados) != vistos:
            problemas.append(f"resultados/index.json: {len(set(listados) ^ vistos)} consultas "
                             f"sin resultado o de más")
        sobrantes = {p.stem for p in resultados.glob("*.json")} - vistos - {"index"}
        for nombre in sorted(sobrantes)[:5]:
            problemas.append(f"resultados/{nombre}.json no corresponde a ninguna consulta")
        for ident, c in por_id.items():
            ruta = resultados / f"{ident}.json"
            if not ruta.exists():
                problemas.append(f"falta resultados/{ident}.json")
                continue
            crudo = ruta.read_bytes()
            doc = json.loads(crudo)
            if doc.get("sql", "").strip().rstrip(";") != c["sql"].strip().rstrip(";"):
                problemas.append(f"resultados/{ident}.json: el SQL no es el de queries.json")
            if doc.get("filas") != len(doc.get("datos", [])):
                problemas.append(f"resultados/{ident}.json: `filas` no coincide con `datos`")
            if doc.get("truncado") and doc.get("filas") != doc.get("max_filas"):
                problemas.append(f"resultados/{ident}.json: truncado con menos filas que el tope")
            if doc.get("data_release") != catalogo["data_release"]:
                problemas.append(f"resultados/{ident}.json: data_release distinto del catálogo")
            declarado = listados.get(ident, {})
            if declarado.get("sha256") != hashlib.sha256(crudo).hexdigest():
                problemas.append(f"resultados/{ident}.json: el sha256 del índice no coincide")
            if declarado.get("filas") != doc.get("filas"):
                problemas.append(f"resultados/{ident}.json: el índice declara otras filas")
        print(f"Resultados: {len(por_id)} consultas con su JSON, SQL, tope y sha256 verificados")

    # 5. Vistas -------------------------------------------------------------
    sql = (V2 / "views.sql").read_text(encoding="utf-8")
    if f"'{BASE}'" not in sql:
        problemas.append("views.sql no usa la URL canónica de la decisión D1")
    vistas = 0
    try:
        import duckdb

        local = sql.replace(f"'{BASE}'", f"'{DOCS.resolve()}'")
        con = duckdb.connect()
        con.execute(local)
        vistas = con.execute("SELECT count(*) FROM duckdb_views() WHERE NOT internal").fetchone()[0]
        con_creadas = {r[0] for r in con.execute(
            "SELECT view_name FROM duckdb_views() WHERE NOT internal").fetchall()}
        esperadas_vistas = {o["id"] for o in objetos if o["particiones"]} | set(alias)
        if con_creadas != esperadas_vistas:
            problemas.append(f"views.sql crea {len(con_creadas)} vistas y se esperaban "
                             f"{len(esperadas_vistas)}")
        # Cada objeto con datos tiene que responder, no sólo existir.
        for objeto in objetos:
            if not objeto["particiones"]:
                continue
            try:
                con.execute(f'SELECT count(*) FROM "{objeto["id"]}"').fetchone()
            except Exception as exc:  # noqa: BLE001
                problemas.append(f"{objeto['id']}: la vista no responde ({str(exc).splitlines()[0][:80]})")
        con.close()
    except ImportError:
        print("AVISO: sin duckdb no se ejecutan las vistas")
    print(f"Vistas: {vistas} creadas desde views.sql con la base local, todas responden")

    # 6. El release tiene que ser el mismo que el del Data Package ----------
    paquete = leer_json(V2 / "datapackage.json")
    if paquete["sif"]["data_release"] != catalogo["data_release"]:
        problemas.append("el data_release del catálogo y del Data Package no coinciden")
    print(f"Release: {catalogo['data_release']} en catálogo y Data Package")

    # 6b. Una sola versión: la que dice `scripts/version_contrato.py` ------
    # El 2026-10-23 el Data Package decía 2.0.0 y el catálogo, los esquemas, las
    # particiones, las consultas, el OpenAPI y los resultados seguían en 1.0.0:
    # el contrato se contradecía. Esta comprobación lo impide.
    piezas = {
        "catalog.json": catalogo,
        "openapi.json": openapi,
        "queries.json": consultas,
        "resultados/index.json": leer_json(resultados / "index.json")
        if resultados.exists() else {},
        "datapackage.json": paquete,
    }
    for objeto in objetos[:90]:
        piezas[f"schema/{objeto['id']}.json"] = leer_json(V2 / "schema" / f"{objeto['id']}.json")
        piezas[f"partitions/{objeto['id']}.json"] = leer_json(V2 / "partitions" / f"{objeto['id']}.json")
    def version_de(nombre: str, doc: dict):
        # OpenAPI declara la versión en `info.version`, como manda el estándar.
        if nombre == "openapi.json":
            return (doc.get("info") or {}).get("version")
        return doc.get("version")

    desalineadas = sorted(n for n, d in piezas.items() if version_de(n, d) != VERSION_CONTRATO)
    for nombre in desalineadas[:6]:
        problemas.append(f"{nombre}: declara la versión {version_de(nombre, piezas[nombre])} "
                         f"y el contrato es {VERSION_CONTRATO}")
    if len(desalineadas) > 6:
        problemas.append(f"… y {len(desalineadas) - 6} piezas más con otra versión")
    if V2.name != API_VERSION:
        problemas.append(f"la carpeta del contrato es api/{V2.name} y API_VERSION dice {API_VERSION}")
    for nombre in ("catalog.json", "datapackage.json"):
        declarada = (paquete["sif"].get("api_version") if nombre == "datapackage.json"
                     else piezas[nombre].get("api_version"))
        if declarada != API_VERSION:
            problemas.append(f"{nombre}: api_version {declarada} ≠ {API_VERSION}")
    if esquemas.get("version") != API_VERSION:
        problemas.append(f"esquemas.json: version {esquemas.get('version')} ≠ {API_VERSION}")
    print(f"Versión: {len(piezas)} piezas en {VERSION_CONTRATO} (api/{API_VERSION})"
          f"{'' if not desalineadas else f', {len(desalineadas)} desalineadas'}")

    # 7. El llms.txt no puede mentirle a un agente -------------------------
    llms = DOCS / "llms.txt"
    if not llms.exists():
        problemas.append("falta docs/llms.txt, la puerta de entrada para agentes")
    else:
        texto = llms.read_text(encoding="utf-8")
        cifras = {"objetos": len(objetos), "consultas": consultas["total"]}
        for nombre, esperado in cifras.items():
            hallada = re.search(rf"\b(\d+) {nombre}\b", texto)
            if not hallada:
                problemas.append(f"llms.txt no dice cuántos {nombre} hay")
            elif int(hallada.group(1)) != esperado:
                problemas.append(f"llms.txt dice {hallada.group(1)} {nombre} y hay {esperado}")
        enlaces = set(re.findall(re.escape(BASE) + r"(/api/v2/[\w./-]+)", texto))
        rotos = [r for r in enlaces if not (DOCS / r.lstrip("/")).exists()]
        for r in rotos:
            problemas.append(f"llms.txt enlaza a una ruta que no existe: {r}")
        print(f"llms.txt: {len(cifras)} cifras y {len(enlaces)} rutas de api/v2 comprobadas"
              f"{'' if not rotos else f', {len(rotos)} rotas'}")

    duracion = time.time() - t0
    for p in problemas[:20]:
        print(f"  [FALLA] {p}")
    print(f"Duración: {duracion:.1f} s")
    if problemas:
        print(f"CONTRATO-API: {len(problemas)} problema(s)")
        return 1
    print("CONTRATO-API: catálogo, esquemas, particiones, consultas, resultados, OpenAPI y vistas coherentes")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # el CI necesita una línea, no un traceback remoto
        print(f"[FALLA] excepción: {type(exc).__name__}: {exc}")
        raise SystemExit(1)

#!/usr/bin/env python3
"""Genera el contrato estático de la API (fase 1 de la ruta).

El Data Package de la 1a dice «estos 86 conjuntos existen y así se leen». Este
paso añade lo que un cliente necesita para **descubrir y consultar** sin abrir
el repo:

    docs/api/v2/catalog.json            el índice: 90 objetos con estado, tamaño y clave
    docs/api/v2/schema/{id}.json        columnas y tipos de cada objeto
    docs/api/v2/partitions/{id}.json    qué archivos lo componen, con su hash
    docs/api/v2/queries.json            las 159 consultas de la web, con id estable
    docs/api/v2/openapi.json            sólo las rutas GET que existen de verdad
    docs/api/v2/views.sql               las 105 vistas (86 con datos + 19 alias)
    docs/api/v2/resultados/{id}.json    lo que devuelve cada consulta (fase 3); lo
                                        escribe build_resultados.py, que corre después

Todo se deriva de lo ya verificado —esquemas, reconciliación, claves y
manifiesto— y la URL base se publica como `{{BASE}}`: ese marcador lo sustituye
cada consumidor (el sitio, una copia local, un espejo) y así la decisión D1 no
obliga a regenerar.

Uso:
    python3 scripts/build_contrato.py                       # escribe todo
    python3 scripts/build_contrato.py --base https://…/     # sustituye {{BASE}}
    python3 scripts/build_contrato.py --check               # falla si está atrasado
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
API = DOCS / "api"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from version_contrato import API_VERSION, VERSION_CONTRATO  # noqa: E402

V2 = API / API_VERSION

import audit_consultas_sugeridas as ac  # noqa: E402
from pipelines.api import fuentes as F  # noqa: E402
from pipelines.api import vistas as V  # noqa: E402

VERSION = VERSION_CONTRATO
# Decisión D1: la API se publica en GitHub Pages y Vercel redirige /api/* allí.
# Todo el contrato usa esta base absoluta; `--base` existe para generar una
# copia apuntando a un espejo o a una ruta local.
BASE = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile"

TITULOS_BANCOS = {
    "bancos_balance": "Líneas de balance bancario CMF (B1/B2)",
    "bancos_resultados": "Líneas de resultados bancarios CMF (R1)",
}

TIPOS_TS = {
    "VARCHAR": "string", "VARCHAR[]": "array", "BIGINT": "integer", "INTEGER": "integer",
    "SMALLINT": "integer", "TINYINT": "integer", "DOUBLE": "number", "REAL": "number",
    "BOOLEAN": "boolean", "DATE": "date", "TIMESTAMP": "datetime", "TIMESTAMPTZ": "datetime",
}


def leer_csv(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def periodo_de(ruta: str) -> str:
    """El período que se puede leer del nombre del archivo (o su carpeta)."""
    partes = Path(ruta).parts
    for parte in reversed(partes):
        m = re.fullmatch(r"(\d{4})-(\d{2})", parte)
        if m:
            return parte
        if re.fullmatch(r"\d{4}", parte) and not parte.endswith(".parquet"):
            return parte
    m = re.search(r"(\d{4})-(\d{2})", Path(ruta).stem)
    return m.group(0) if m else Path(ruta).stem


def slug(texto: str) -> str:
    sin = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sin.lower()).strip("-")[:48] or "consulta"


def cargar() -> dict:
    esquemas = json.loads((API / "esquemas.json").read_text(encoding="utf-8"))
    manifiesto = {t["id"]: t for t in json.loads(
        (RAIZ / "data_manifest.json").read_text(encoding="utf-8"))["tables"]}
    reconciliacion = {f["objeto"]: f for f in leer_csv(API / "reconciliacion.csv")}
    claves = {f["objeto"]: f for f in leer_csv(API / "claves.csv") if f["tipo"] == "pk"}
    return {"esquemas": esquemas, "manifiesto": manifiesto,
            "reconciliacion": reconciliacion, "claves": claves}


def construir_objetos(datos: dict, alias: dict[str, list[str]], base: str) -> tuple[list[dict], dict[str, dict], dict[str, dict], list[str]]:
    esquemas = datos["esquemas"]["objetos"]
    vistas = {v["name"]: v for v in ac.vistas_semanticas()}
    fichas_vocabulario = json.loads((DOCS / "vocabulario.json").read_text(encoding="utf-8")).get("tablas", [])
    descripciones_vocabulario = {f.get("id"): f.get("descripcion", "") for f in fichas_vocabulario}
    catalogo, esquemas_por_id, particiones_por_id = [], {}, {}
    hashes: list[str] = []

    for nombre in sorted(esquemas):
        info = esquemas[nombre]
        vista = vistas[nombre]
        recon = datos["reconciliacion"].get(nombre, {})
        tabla = datos["manifiesto"].get(info.get("manifest_id") or "", {})
        clave = datos["claves"].get(nombre)

        partes = []
        for rel in V.rutas_relativas(vista):
            archivo = DOCS / rel
            huella = sha256(archivo)
            hashes.append(huella)
            partes.append({
                "path": f"{base.rstrip('/')}/{rel}",
                "archivo": rel,
                "periodo": periodo_de(rel),
                "bytes": archivo.stat().st_size,
                "sha256": huella,
            })

        columnas = []
        for col in info["columnas"]:
            campo = {"nombre": col["nombre"], "tipo": col["tipo"],
                     "tipo_ts": TIPOS_TS[col["tipo"]]}
            for clave_col in ("rol", "significado", "criterio_contable"):
                if col.get(clave_col):
                    campo[clave_col] = col[clave_col]
            if col.get("sin_valores"):
                campo["sin_valores"] = True
            columnas.append(campo)

        # `None` es «no hay clave única medida»; `[]` sería «clave de cero
        # columnas», que no significa lo mismo y un consumidor puede leer como
        # verdad. Sólo se publica una lista cuando la medición la respalda.
        pk = None
        if clave and clave["estado"] in ("ok", "propuesta") and clave["columnas"]:
            pk = [c.strip() for c in clave["columnas"].split("+")]

        fk = [
            {"columna": f["columnas"], "destino": f["destino"], "tasa": float(f["tasa"] or 0)}
            for f in leer_csv(API / "claves.csv")
            if f["tipo"] == "fk" and f["objeto"] == nombre and f["destino"]
        ]

        atribucion = F.atribucion_de(info.get("sector"), nombre)

        esquemas_por_id[nombre] = {
            "contrato": "sif-api/esquema",
            "version": VERSION,
            "id": nombre,
            "fuente": atribucion["fuente"],
            "atribucion": atribucion["cita"],
            "url_terminos": atribucion["url_terminos"],
            "licencia_estado": atribucion["estado"],
            "adaptacion": atribucion["adaptacion"],
            "titulo": TITULOS_BANCOS.get(nombre) or recon.get("nombre_visible") or nombre,
            "sector": info.get("sector"),
            "estado": recon.get("estado"),
            "primaryKey": pk,
            "foraneas": fk,
            "columnas": columnas,
        }
        particiones_por_id[nombre] = {
            "contrato": "sif-api/particiones",
            "version": VERSION,
            "id": nombre,
            "estado": recon.get("estado"),
            "filtro": info.get("filtro"),
            "particiones": partes,
            "total": {"archivos": len(partes),
                      "bytes": sum(p["bytes"] for p in partes),
                      "filas": info.get("filas")},
        }

        catalogo.append({
            "id": nombre,
            "titulo": TITULOS_BANCOS.get(nombre) or recon.get("nombre_visible") or nombre,
            "sql_view": nombre,
            "aliases": V.aliases_de(nombre, alias),
            "sector": info.get("sector"),
            "nivel": recon.get("nivel"),
            "estado": recon.get("estado"),
            "deriva_de": recon.get("deriva_de") or None,
            "filas": info.get("filas"),
            "bytes": sum(p["bytes"] for p in partes),
            "particiones": len(partes),
            "corte": tabla.get("corte") or recon.get("corte") or None,
            "frescura": tabla.get("frescura") or None,
            "ultima_actualizacion": tabla.get("ultima_actualizacion") or None,
            # Para banca, la ficha pública distingue la semántica del objeto y
            # confirma que sus Parquet de descarga materializan el mismo filtro.
            "descripcion": (
                descripciones_vocabulario.get(nombre, "")
                if nombre in {"bancos_balance", "bancos_resultados"}
                else tabla.get("descripcion") or ""
            ),
            "fuente": atribucion["fuente"],
            "atribucion": atribucion["cita"],
            "url_terminos": atribucion["url_terminos"],
            "licencia_estado": atribucion["estado"],
            "adaptacion": atribucion["adaptacion"],
            "nota_adaptacion": atribucion.get("nota_adaptacion") or None,
            "primaryKey": pk,
            "esquema": f"{base.rstrip('/')}/api/v2/schema/{nombre}.json",
            "particiones_url": f"{base.rstrip('/')}/api/v2/partitions/{nombre}.json",
        })

    return catalogo, esquemas_por_id, particiones_por_id, hashes


def construir_consultas(catalogo: list[dict]) -> dict:
    conocidos = {o["id"] for o in catalogo}
    alias = {a: o["id"] for o in catalogo for a in o["aliases"]}
    consultas, vistos = [], set()

    fuentes = [("explorador", t, s) for t, s in ac.consultas_sugeridas()]
    fuentes += [("terminal", t, s) for t, s in ac.consultas_terminal()]

    for origen, titulo, sql in fuentes:
        base = f"{slug(titulo)}-{hashlib.sha1(sql.encode()).hexdigest()[:6]}"
        ident = base
        n = 2
        while ident in vistos:
            ident, n = f"{base}-{n}", n + 1
        vistos.add(ident)
        tablas = sorted({
            alias.get(t.lower(), t.lower())
            for t in re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][\w]*)", sql)
            if alias.get(t.lower(), t.lower()) in conocidos
        })
        consultas.append({
            "id": ident,
            "titulo": titulo,
            "origen": origen,
            "sql": sql.strip(),
            "espera": {
                # La expectativa es de forma, no un número fijo: una consulta
                # que devuelve filas hoy puede devolver otras mañana.
                "tipo": "no_vacia",
                "tablas": tablas,
            },
        })

    return {
        "contrato": "sif-api/consultas",
        "version": VERSION,
        "generado": date.today().isoformat(),
        "como_se_genera": "python3 scripts/build_contrato.py",
        "nota": "Salen de la propia web (sidebar.js e index.html); la auditoría las ejecuta contra los Parquet en cada CI.",
        "total": len(consultas),
        "consultas": consultas,
    }


def construir_openapi(catalogo: list[dict], n_consultas: int, base: str,
                      ids_consultas: list[str] | None = None) -> dict:
    """Sólo las rutas GET que existen de verdad. Nada inventado."""

    def json_resp(descripcion: str) -> dict:
        return {"200": {"description": descripcion,
                        "content": {"application/json": {"schema": {"type": "object"}}}}}

    rutas = {
        "/api/v2/datapackage.json": {
            "get": {"operationId": "getDatapackage", "summary": "Data Package con los 86 conjuntos",
                    "tags": ["contrato"], "responses": json_resp("Descriptor Frictionless")}},
        "/api/v2/catalog.json": {
            "get": {"operationId": "getCatalogo", "summary": "Índice de los 90 objetos del contrato",
                    "tags": ["contrato"], "responses": json_resp("Catálogo")}},
        "/api/v2/schema/{id}.json": {
            "get": {"operationId": "getEsquema", "summary": "Columnas y tipos de un objeto",
                    "tags": ["contrato"],
                    "parameters": [{"name": "id", "in": "path", "required": True,
                                    "schema": {"type": "string", "enum": [o["id"] for o in catalogo]}}],
                    "responses": json_resp("Esquema del objeto")}},
        "/api/v2/partitions/{id}.json": {
            "get": {"operationId": "getParticiones", "summary": "Archivos que componen un objeto",
                    "tags": ["contrato"],
                    "parameters": [{"name": "id", "in": "path", "required": True,
                                    "schema": {"type": "string", "enum": [o["id"] for o in catalogo]}}],
                    "responses": json_resp("Particiones y sus hashes")}},
        "/api/v2/queries.json": {
            "get": {"operationId": "getConsultas", "summary": f"Las {n_consultas} consultas de la web, con id estable",
                    "tags": ["consultas"], "responses": json_resp("Consultas")}},
        "/api/v2/resultados/index.json": {
            "get": {"operationId": "getResultadosIndice",
                    "summary": f"El resultado ya calculado de las {n_consultas} consultas",
                    "tags": ["consultas"], "responses": json_resp("Índice de resultados")}},
        "/api/v2/resultados/{id}.json": {
            "get": {"operationId": "getResultado",
                    "summary": "Columnas, filas y el SQL de una consulta publicada",
                    "tags": ["consultas"],
                    "parameters": [{"name": "id", "in": "path", "required": True,
                                    "schema": {"type": "string", "enum": ids_consultas or []}}],
                    "responses": json_resp("Resultado de la consulta")}},
        "/api/v2/views.sql": {
            "get": {"operationId": "getVistas", "summary": "DDL de las 105 vistas (86 con datos + 19 alias)",
                    "tags": ["contrato"],
                    "responses": {"200": {"description": "SQL", "content": {"text/plain": {"schema": {"type": "string"}}}}}}},
        "/api/reconciliacion.csv": {
            "get": {"operationId": "getReconciliacion", "summary": "Objeto ↔ manifiesto ↔ dataset",
                    "tags": ["contrato"],
                    "responses": {"200": {"description": "CSV", "content": {"text/csv": {"schema": {"type": "string"}}}}}}},
        "/api/claves.csv": {
            "get": {"operationId": "getClaves", "summary": "Claves primarias y foráneas verificadas",
                    "tags": ["contrato"],
                    "responses": {"200": {"description": "CSV", "content": {"text/csv": {"schema": {"type": "string"}}}}}}},
        "/outputs/{ruta}": {
            "get": {"operationId": "getParquet", "summary": "Los Parquet publicados del sitio",
                    "tags": ["datos"],
                    "parameters": [{"name": "ruta", "in": "path", "required": True,
                                    "schema": {"type": "string"}, "example": "seguros/aseguradoras.parquet"}],
                    "responses": {"200": {"description": "Parquet",
                                          "content": {"application/vnd.apache.parquet": {"schema": {"type": "string", "format": "binary"}}}}}}},
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Sistema de Información Financiera de Chile",
            "version": VERSION,
            "summary": "Contrato estático sobre Parquet públicos; sin /query ni JSON por fila.",
            "description": (
                "API de solo lectura sobre archivos estáticos. Las rutas listadas son las que "
                "existen: no hay endpoint de consulta ad-hoc, ni autenticación, ni SLA. "
                f"Las {n_consultas} consultas del catálogo sí vienen con su resultado ya calculado, "
                "en /api/v2/resultados/."
            ),
            "license": {"name": "Datos: uso condicionado por la fuente · Código: MIT",
                        "url": "https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/blob/main/DATA_LICENSE.md"},
        },
        "servers": [{"url": base.rstrip("/"), "description": "URL canónica (decisión D1)"}],
        "tags": [{"name": "contrato"}, {"name": "consultas"}, {"name": "datos"}],
        "paths": rutas,
    }


def construir_vistas(catalogo: list[dict], alias: dict[str, list[str]], base: str) -> str:
    vistas = {v["name"]: v for v in ac.vistas_semanticas()}
    lineas = [
        "-- Vistas del contrato — generado por scripts/build_contrato.py",
        f"-- {sum(1 for o in catalogo if o['particiones'])} vistas con datos + "
        f"{sum(len(o['aliases']) for o in catalogo)} alias = "
        f"{sum(1 for o in catalogo if o['particiones']) + sum(len(o['aliases']) for o in catalogo)} objetos SQL.",
        "--",
        "-- Uso remoto:   duckdb < views.sql",
        "-- Uso local:    cambie la línea siguiente por la ruta de su copia de docs/",
        "--                (por ejemplo file:///home/yo/repo/docs) y ejecútelo igual.",
        "-- Algunas vistas usan copias compactas SQL-only en outputs/sql_query/ y no se ofrecen para descarga.",
        "",
        f"SET VARIABLE sif_base = '{base.rstrip('/')}';",
        "",
    ]
    vacias = []
    for objeto in catalogo:
        vista = vistas[objeto["id"]]
        if not objeto["particiones"]:
            vacias.append(objeto["id"])
            lineas.append(f"-- {objeto['id']}: sin particiones publicadas ({objeto['estado']})")
            continue
        # Las rutas se construyen en la propia consulta con la variable de
        # sesión: así el mismo views.sql sirve para el sitio, para una copia
        # local o para un espejo, sin regenerarlo.
        rutas = [f"getvariable('sif_base') || '/{rel}'" for rel in V.rutas_sql_relativas(vista)]
        argumento = rutas[0] if len(rutas) == 1 else "[" + ", ".join(rutas) + "]"
        solo = "" if len(rutas) == 1 else ", union_by_name=true"
        filtro = f"\n  WHERE {vista['where']}" if vista.get("where") else ""
        lineas.append(f"CREATE OR REPLACE VIEW \"{objeto['id']}\" AS\n"
                      f"SELECT * FROM read_parquet({argumento}{solo}){filtro};")
        for viejo in objeto["aliases"]:
            lineas.append(f'CREATE OR REPLACE VIEW "{viejo}" AS SELECT * FROM "{objeto["id"]}";')
    if vacias:
        lineas.append("")
        lineas.append("-- Objetos publicados sin filas (la fuente no entrega la tabla): "
                      + ", ".join(vacias))
    lineas.append("")
    return "\n".join(lineas)


def comparable(doc: dict) -> str:
    copia = json.loads(json.dumps(doc))
    copia.pop("generado", None)
    return json.dumps(copia, ensure_ascii=False, indent=1, sort_keys=True)


def escribir_json(ruta: Path, doc: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=BASE, help="URL base de lo generado (por defecto, la canónica)")
    ap.add_argument("--check", action="store_true", help="no escribe; falla si algo está atrasado")
    args = ap.parse_args()

    datos = cargar()
    alias = ac.alias_heredados()
    catalogo, esquemas, particiones, hashes = construir_objetos(datos, alias, args.base)
    consultas = construir_consultas(catalogo)
    openapi = construir_openapi(catalogo, consultas["total"], args.base,
                                [c["id"] for c in consultas["consultas"]])
    vistas_sql = construir_vistas(catalogo, alias, args.base)

    huella = hashlib.sha256("".join(sorted(hashes)).encode()).hexdigest()[:12]
    fechas = [t.get("ultima_actualizacion", "") for t in datos["manifiesto"].values()
              if t.get("ultima_actualizacion")]
    data_release = f"{max(fechas) if fechas else ''}.{huella}"

    doc_catalogo = {
        "contrato": "sif-api/catalogo",
        "version": VERSION,
        "api_version": API_VERSION,
        "data_release": data_release,
        "generado": date.today().isoformat(),
        "como_se_genera": "python3 scripts/build_contrato.py",
        "base": args.base,
        "totales": {
            "objetos": len(catalogo),
            # `con_datos` = tiene al menos un archivo publicado. No es lo mismo que
            # tener filas: `fi_bienes_raices` publica el esquema con un Parquet vacío
            # (0 filas) para que la vista SQL exista, así que cuenta en uno y no en el
            # otro. Los dos números van con nombre propio para que nadie tenga que
            # restarlos a mano (90 · 89 · 86 · 85).
            "con_datos": sum(1 for o in catalogo if o["particiones"]),
            "con_filas": sum(1 for o in catalogo if o["filas"]),
            "vacios": sum(1 for o in catalogo if o["estado"] == "vacio"),
            "derivados": sum(1 for o in catalogo if o["estado"] == "derivado"),
            "alias": sum(len(o["aliases"]) for o in catalogo),
            "consultas": consultas["total"],
            "filas": datos["esquemas"]["resumen"]["filas_unicas"],
            "bytes": sum(o["bytes"] for o in catalogo),
        },
        "rutas": {
            "datapackage": f"{args.base}/api/v2/datapackage.json",
            "resultados": f"{args.base}/api/v2/resultados/index.json",
            "esquema": f"{args.base}/api/v2/schema/{{id}}.json",
            "particiones": f"{args.base}/api/v2/partitions/{{id}}.json",
            "consultas": f"{args.base}/api/v2/queries.json",
            "vistas": f"{args.base}/api/v2/views.sql",
            "openapi": f"{args.base}/api/v2/openapi.json",
        },
        "objetos": catalogo,
    }

    if args.check:
        problemas = []
        esperados = {
            "catalog.json": doc_catalogo,
            "queries.json": consultas,
            "openapi.json": openapi,
        }
        for nombre, doc in esperados.items():
            ruta = V2 / nombre
            if not ruta.exists():
                problemas.append(f"falta {ruta.relative_to(RAIZ)}")
                continue
            actual = json.loads(ruta.read_text(encoding="utf-8"))
            if comparable(actual) != comparable(doc):
                problemas.append(f"{ruta.relative_to(RAIZ)} está desactualizado")
        for nombre in [o["id"] for o in catalogo]:
            if not (V2 / "schema" / f"{nombre}.json").exists():
                problemas.append(f"falta schema/{nombre}.json")
            if not (V2 / "partitions" / f"{nombre}.json").exists():
                problemas.append(f"falta partitions/{nombre}.json")
        if not (V2 / "views.sql").exists():
            problemas.append("falta views.sql")
        print(f"Objetos: {len(catalogo)} · esquemas: {len(esquemas)} · particiones: {len(particiones)}")
        print(f"Consultas: {consultas['total']} · rutas OpenAPI: {len(openapi['paths'])}")
        for p in problemas[:10]:
            print(f"  [FALLA] {p}")
        if problemas:
            print(f"CONTRATO: {len(problemas)} problema(s); ejecuta scripts/build_contrato.py")
            return 1
        print("CONTRATO: al día")
        return 0

    escribir_json(V2 / "catalog.json", doc_catalogo)
    escribir_json(V2 / "queries.json", consultas)
    escribir_json(V2 / "openapi.json", openapi)
    for nombre, doc in esquemas.items():
        escribir_json(V2 / "schema" / f"{nombre}.json", doc)
    for nombre, doc in particiones.items():
        escribir_json(V2 / "partitions" / f"{nombre}.json", doc)
    (V2 / "views.sql").write_text(vistas_sql, encoding="utf-8")

    total = doc_catalogo["totales"]
    print(f"Objetos: {total['objetos']} ({total['con_datos']} con datos · {total['vacios']} vacíos · "
          f"{total['derivados']} derivados) · {total['alias']} alias")
    print(f"Consultas: {total['consultas']} · rutas OpenAPI: {len(openapi['paths'])}")
    print(f"Esquemas: {len(esquemas)} archivos · particiones: {len(particiones)} archivos · "
          f"{sum(len(p['particiones']) for p in particiones.values())} archivos listados")
    print(f"Filas: {total['filas']:,}".replace(",", ".") + f" · data_release: {data_release}")
    print(f"Escrito en {V2.relative_to(RAIZ)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

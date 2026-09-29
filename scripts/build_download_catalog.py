#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el catálogo de descargas de la web (docs/js/download_catalog.js).

Fuentes de verdad:
  * docs/vocabulario.json     -> nombre canónico, tipo, sector y descripción.
  * docs/js/duckdb_client.js  -> SEMANTIC_VIEWS (qué vista cubre qué archivos).
  * docs/outputs/**/manifest.json + Parquet en disco (filas y bytes reales).

El resultado alimenta la pestaña «Descargas»: filas, periodo, peso y archivos de
cada conjunto publicado, agrupados por sector con su nombre canónico.

Uso:
    python3 scripts/build_download_catalog.py            # escribe el catálogo
    python3 scripts/build_download_catalog.py --check    # falla si está desactualizado
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date

try:  # pyarrow es opcional: sin él sólo se pierden los conteos de filas sueltos
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - entorno sin pyarrow
    pq = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DUCKDB_JS = os.path.join(DOCS, "js", "duckdb_client.js")
VOCAB_JSON = os.path.join(DOCS, "vocabulario.json")
OUT_JS = os.path.join(DOCS, "js", "download_catalog.js")

VIEW_RE = re.compile(
    r"\{\s*name:\s*\"(?P<name>[a-z0-9_]+)\"\s*,\s*"
    r"(?:(?P<kind>file|manifest):\s*\"(?P<path>[^\"]+)\")"
    r"(?:\s*,\s*where:\s*\"(?P<where>[^\"]*)\")?\s*\}",
)


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_vocabulario() -> dict:
    with open(VOCAB_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sector_corto(vocab: dict, clave: str) -> str:
    """Etiqueta corta para el filtro de la pestaña (sin el paréntesis final)."""
    return re.sub(r"\s*\(.*\)$", "", vocab["sectores"].get(clave, clave))


def parse_views() -> list[dict]:
    src = read(DUCKDB_JS)
    bloque = src[src.index("const SEMANTIC_VIEWS"):src.index("class DuckDBClient")]
    vistas = []
    for match in VIEW_RE.finditer(bloque):
        item = match.groupdict()
        vistas.append({
            "name": item["name"],
            "kind": item["kind"],
            "path": item["path"],
            "where": item.get("where") or "",
        })
    if not vistas:
        raise SystemExit("No se pudieron leer las vistas de duckdb_client.js")
    return vistas


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def periodos_de(manifest: dict) -> list[str]:
    """Los manifiestos publican los periodos como lista de textos o de objetos."""
    bruto = manifest.get("periodos") or manifest.get("periods") or []
    valores = []
    for item in bruto:
        if isinstance(item, dict):
            valor = item.get("period") or item.get("periodo")
            if valor:
                valores.append(str(valor))
        else:
            valores.append(str(item))
    return sorted(valores)


def periodo_de_ruta(path: str) -> str | None:
    match = re.search(r"(\d{4})-(\d{2})", path)
    return f"{match.group(1)}-{match.group(2)}" if match else None


def file_size(rel_path: str) -> int:
    full = os.path.join(DOCS, rel_path)
    return os.path.getsize(full) if os.path.exists(full) else 0


def filas_parquet(rel_path: str) -> int | None:
    """Cuenta las filas leyendo sólo el pie del Parquet (con pyarrow disponible)."""
    if pq is None:
        return None
    full = os.path.join(DOCS, rel_path)
    if not os.path.exists(full):
        return None
    try:
        return int(pq.ParquetFile(full).metadata.num_rows)
    except Exception:
        return None


def catalogo_vigente() -> dict:
    """Catálogo ya escrito, para heredar los conteos cuando no hay pyarrow."""
    if not os.path.exists(OUT_JS):
        return {}
    try:
        texto = read(OUT_JS)
        return json.loads(texto[texto.index("{"):texto.rindex(";")])
    except Exception:
        return {}


def filas_heredadas(vigente: dict, vid: str) -> int | None:
    for grupo in vigente.get("grupos", []):
        for item in grupo.get("items", []):
            if item.get("id") == vid:
                return item.get("filas")
    return None


def build() -> dict:
    views = parse_views()
    vocab = load_vocabulario()
    previo = catalogo_vigente() if pq is None else {}
    fichas = {t["id"]: t for t in vocab["tablas"]}
    sectores = vocab["sectores"]

    por_sector: dict[str, list] = {}
    total_filas = 0
    total_bytes = 0

    for view in views:
        vid = view["name"]
        ficha = fichas.get(vid)
        if ficha is None:
            raise SystemExit(f"La vista {vid} no está en docs/vocabulario.json: el vocabulario quedó atrás.")
        sector_clave = ficha["sector"]
        grupo = sectores[sector_clave]

        if view["kind"] == "file":
            files = [view["path"]]
            manifest_total = None
            periodos: list[str] = []
            updated = None
        else:
            manifest_path = os.path.join(DOCS, view["path"])
            if not os.path.exists(manifest_path):
                continue
            manifest = load_manifest(manifest_path)
            files = list(manifest.get("files", []))
            manifest_total = manifest.get("total_records")
            periodos = periodos_de(manifest)
            updated = manifest.get("updated_at")

        archivos = []
        for rel in files:
            entrada = {"ruta": rel, "bytes": file_size(rel)}
            periodo = periodo_de_ruta(rel)
            if periodo:
                entrada["periodo"] = periodo
            archivos.append(entrada)

        if not periodos:
            periodos = sorted({a["periodo"] for a in archivos if a.get("periodo")})

        if view["where"]:
            # Vista unificada: el manifiesto cuenta las filas de todos los archivos
            # fuente, no las de la vista (que aplica un filtro). Preferimos decir
            # "se cuentan al consultar" antes que mostrar un número equivocado.
            filas = None
        elif manifest_total is not None:
            filas = int(manifest_total)
        else:
            # Manifiestos antiguos sin total, catálogos de una sola tabla y series
            # que se publican año a año: el conteo sale del pie de cada Parquet.
            conteos = [filas_parquet(a["ruta"]) for a in archivos]
            filas = sum(conteos) if conteos and all(c is not None for c in conteos) else None
            if filas is None and previo:
                # Sin pyarrow: se hereda el conteo del catálogo vigente para que
                # --check siga siendo útil (detecta cambios de rutas, pesos y nombres).
                filas = filas_heredadas(previo, vid)
        item = {
            "id": vid,
            "nombre": ficha["nombre"],
            "detalle": vocab["tipos"].get(ficha["tipo"], ficha["tipo"]),
            "descripcion": ficha.get("descripcion", ""),
            "cobertura": ficha.get("cobertura", ""),
            "grupo": grupo,
            "sector": sector_corto(vocab, sector_clave),
            "filas": filas,
            "filasReales": filas is not None,
            "bytes": sum(a["bytes"] for a in archivos),
            "archivos": archivos,
            "archivosN": len(archivos),
            "periodo": {"desde": periodos[0], "hasta": periodos[-1]} if periodos else None,
            "unificado": bool(view["where"]),
            "filasFuente": int(manifest_total) if manifest_total is not None else None,
            "actualizado": updated,
        }
        por_sector.setdefault(grupo, []).append(item)
        total_filas += int(filas or 0)
        total_bytes += item["bytes"]

    bloques = [
        {"grupo": grupo, "sector": items[0]["sector"], "items": items}
        for grupo, items in sorted(por_sector.items())
    ]

    return {
        "generado": date.today().isoformat(),
        "conjuntos": sum(len(b["items"]) for b in bloques),
        "filas": total_filas,
        "bytes": total_bytes,
        "grupos": bloques,
    }


def render(catalogo: dict) -> str:
    payload = json.dumps(catalogo, ensure_ascii=False, separators=(",", ":"))
    return (
        "/**\n"
        " * Catálogo de descargas del Sistema de Información Financiera de Chile.\n"
        " * Archivo GENERADO por scripts/build_download_catalog.py — no editar a mano.\n"
        " * Nombres, tipos y sectores salen de docs/vocabulario.json; filas, peso y\n"
        " * periodos, de los manifiestos publicados en docs/outputs.\n"
        " */\n"
        f"window.DOWNLOAD_CATALOG = {payload};\n"
    )


def main() -> int:
    catalogo = build()
    contenido = render(catalogo)
    resumen = (
        f"{catalogo['conjuntos']} conjuntos · {catalogo['filas']:,} filas · "
        f"{catalogo['bytes'] / 1e6:,.1f} MB"
    ).replace(",", ".")

    if "--check" in sys.argv:
        actual = read(OUT_JS) if os.path.exists(OUT_JS) else ""
        if actual != contenido:
            extra = ""
            if pq is None:
                extra = "\n  (sin pyarrow: instala las dependencias con `pip install -r requirements.txt`" \
                        " para contar filas reales)"
            print("CATÁLOGO DESACTUALIZADO: ejecuta scripts/build_download_catalog.py" + extra)
            return 1
        print(f"Catálogo al día: {resumen}")
        return 0

    with open(OUT_JS, "w", encoding="utf-8") as fh:
        fh.write(contenido)
    print(f"Catálogo escrito en {os.path.relpath(OUT_JS, ROOT)}: {resumen}")
    sin_filas = [i["id"] for b in catalogo["grupos"] for i in b["items"] if i["filas"] is None]
    if sin_filas and pq is None:
        print(f"  Aviso: {len(sin_filas)} conjuntos quedaron sin conteo de filas "
              "(instala pyarrow para leerlas del Parquet).")
    elif sin_filas:
        print(f"  Aviso: {len(sin_filas)} conjuntos sin conteo disponible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Genera la spec de api-anything para el contrato estático de SIF Chile.

api-anything (https://github.com/anthropics/api-anything) aprende sitios web y
los expone como operaciones verificables. Aquí no hace falta aprender nada: el
contrato ya es un conjunto de GET estáticos con ids estables, así que la spec se
**genera** desde `docs/api/v2/catalog.json` y se verifica con `verify --strict`.

Genera:
  * `integraciones/api-anything/sif-chile.json` — la spec (6 operaciones de lectura).
  * `integraciones/api-anything/sif-chile.md`   — notas para quien la llama.

Uso:
    python3 scripts/build_api_anything.py            # escribe
    python3 scripts/build_api_anything.py --check    # exit 1 si está desactualizada
    python3 scripts/build_api_anything.py --base URL # otra base (espejo local)

La spec es determinista: sin fechas ni rutas absolutas, para que `--check` no
falle por el reloj. La base canónica es el sitio publicado; para probar contra
un espejo local se usa `--base` (lo hace `scripts/probar_api_anything.py`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
V2 = DOCS / "api" / "v2"
DEST = RAIZ / "integraciones" / "api-anything"
BASE_CANONICA = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile"
PREFIJO = "/Sistema_de_Informacion_Financiera_de_Chile"


def _op(nombre: str, descripcion: str, ruta: str, *, id_param: bool = False,
        extract: str | None = None, pick: list[str] | None = None,
        checks: list[dict] | None = None, ejemplo_id: str | None = None) -> dict:
    url = "{base}" + ruta
    op = {
        "name": nombre,
        "description": descripcion,
        "request": {"method": "GET", "url": url, "headers": {}},
        "slots": [],
        "trigger": {"url": url},
        "match": {"method": "GET", "path": PREFIJO + ruta.replace("{id}", "*")},
        "response": {"format": "json"},
        "params": [],
        "readOnly": True,
        "minTier": 1,
        "learnedLoggedIn": False,
    }
    if extract:
        op["response"]["extract"] = extract
    if pick:
        op["response"]["pick"] = pick
    if id_param:
        op["params"] = [{
            "name": "id", "type": "string", "required": True,
            "description": "Id estable del objeto o consulta del contrato.",
            "example": ejemplo_id,
            "pattern": "^[a-z0-9][a-z0-9_-]*$",
            "hint": "id del catálogo (p. ej. bancos_balance) o de consultas (slug-6hex)",
        }]
        op["slots"] = [{"param": "id", "at": ["path:4"], "template": "{id}.json"}]
    if checks:
        op["checks"] = checks
    return op


def construir(base: str) -> dict:
    catalogo = json.loads((V2 / "catalog.json").read_text(encoding="utf-8"))
    consultas = json.loads((V2 / "queries.json").read_text(encoding="utf-8"))
    objetos = catalogo["objetos"]
    con_datos = [o for o in objetos if o.get("estado") == "publicado" and o.get("filas", 0) > 0]
    ejemplo_obj = next((o["id"] for o in con_datos if o["id"] == "bancos_balance"), con_datos[0]["id"])
    ejemplo_consulta = consultas["consultas"][0]["id"]
    ops = [
        _op("catalog", "Índice de los objetos del contrato: id, sector, estado, filas, bytes, clave, corte y rutas.",
            "/api/v2/catalog.json", extract="objetos",
            pick=["id", "sector", "estado", "filas", "bytes", "primaryKey", "corte"],
            checks=[{"args": {}, "expect": "result", "purpose": "el catálogo siempre trae objetos"}]),
        _op("schema", "Columnas, tipos, significado y clave de un objeto.",
            "/api/v2/schema/{id}.json", id_param=True, ejemplo_id=ejemplo_obj,
            pick=["id", "titulo", "primaryKey", "columnas"],
            checks=[
                {"args": {"id": ejemplo_obj}, "expect": "result", "purpose": "un objeto con datos tiene esquema"},
                {"args": {"id": "no_existe_este_objeto"}, "expect": "input", "purpose": "un id inventado es 404, no datos"},
            ]),
        _op("partitions", "Archivos Parquet que componen un objeto, con período, filas, bytes y SHA-256.",
            "/api/v2/partitions/{id}.json", id_param=True, ejemplo_id=ejemplo_obj,
            extract="particiones", pick=["path", "periodo", "filas", "bytes", "sha256"],
            checks=[
                {"args": {"id": ejemplo_obj}, "expect": "result", "purpose": "un objeto publicado tiene particiones"},
                {"args": {"id": "no_existe_este_objeto"}, "expect": "input", "purpose": "un id inventado es 404"},
            ]),
        _op("queries", "Las consultas sugeridas del sitio, con id estable, título, SQL y expectativa.",
            "/api/v2/queries.json", extract="consultas",
            pick=["id", "titulo", "sql", "espera"],
            checks=[{"args": {}, "expect": "result", "purpose": "el catálogo de consultas no está vacío"}]),
        _op("resultados", "Índice de los resultados ya calculados: filas, columnas, tope, sha256 y URL.",
            "/api/v2/resultados/index.json", extract="consultas",
            pick=["id", "titulo", "filas", "columnas", "truncado", "url"],
            checks=[{"args": {}, "expect": "result", "purpose": "hay resultados precalculados"}]),
        _op("resultado", "El resultado ya calculado de una consulta: datos, SQL que los produjo y data_release.",
            "/api/v2/resultados/{id}.json", id_param=True, ejemplo_id=ejemplo_consulta,
            pick=["id", "sql", "data_release", "columnas", "filas", "datos"],
            checks=[
                {"args": {"id": ejemplo_consulta}, "expect": "result", "purpose": "una consulta publicada tiene resultado"},
                {"args": {"id": "no-existe-esta-consulta-000000"}, "expect": "input", "purpose": "un id inventado es 404"},
            ]),
    ]
    return {
        "name": "sif-chile",
        "displayName": "SIF Chile · contrato estático",
        "baseUrl": base,
        "description": ("Contrato estático de datos financieros chilenos (CMF, BCCh, SPensiones): "
                        "catálogo, esquemas, particiones, consultas y resultados precalculados. "
                        "Solo GET, sin autenticación. No es SQL arbitrario."),
        "operations": ops,
    }


def notas(base: str) -> str:
    return f"""# sif-chile · notas para quien llama

Contrato estático de SIF Chile. Base: `{base}`.

- Todo es GET y de solo lectura (`readOnly: true`, `minTier: 1`): no hay cookies,
  ni login, ni escrituras. No hace falta navegador.
- `catalog` es el punto de partida: devuelve los objetos con `id`. Usa ese `id`
  en `schema` y `partitions`.
- `queries` devuelve las consultas sugeridas con `id` estable; `resultados` es su
  índice ya calculado y `resultado` trae los datos de una. Si solo necesitas el
  número, pide `resultado` y no descargues los Parquet.
- Un `id` que no existe responde 404 y api-anything lo clasifica como `input`
  (no como sitio caído): corrige el id, no reintentes a ciegas.
- Los Parquet no están en esta spec: se leen con DuckDB desde `views.sql` o con
  el SDK `sif-chile`. Esta spec cubre el contrato JSON, no la descarga masiva.

## Maintainer notes

Spec generada por `scripts/build_api_anything.py` desde `docs/api/v2/`. No editar
a mano: `python3 scripts/build_api_anything.py --check` falla si se desactualiza.
La prueba real contra un espejo local es `scripts/probar_api_anything.py`.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--base", default=BASE_CANONICA)
    args = ap.parse_args()
    spec = construir(args.base)
    # La URL de la request lleva la base completa; el slot usa el índice de segmento.
    for op in spec["operations"]:
        op["request"]["url"] = op["request"]["url"].replace("{base}", args.base)
        op["trigger"]["url"] = op["trigger"]["url"].replace("{base}", args.base)
    texto = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    md = notas(args.base)
    if args.check:
        ok = True
        for ruta, contenido in ((DEST / "sif-chile.json", texto), (DEST / "sif-chile.md", md)):
            if not ruta.exists() or ruta.read_text(encoding="utf-8") != contenido:
                print(f"FALLA {ruta.relative_to(RAIZ)} desactualizado")
                ok = False
        print("OK spec api-anything al día" if ok else "Regenera con: python3 scripts/build_api_anything.py")
        return 0 if ok else 1
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "sif-chile.json").write_text(texto, encoding="utf-8")
    (DEST / "sif-chile.md").write_text(md, encoding="utf-8")
    print(f"Escrito {DEST.relative_to(RAIZ)}/sif-chile.json y .md ({len(spec['operations'])} operaciones)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

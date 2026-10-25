#!/usr/bin/env python3
"""Renderizador estático genérico para previsualizar fichas sin publicarlas.

Las páginas de candidatos se generan en memoria durante las pruebas. Solo el
constructor aprobado de `ccaf_lista_entidades` escribe una ruta bajo docs/.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CATALOGO = DOCS / "api" / "v2" / "catalog.json"
DATAPACKAGE = DOCS / "api" / "v2" / "datapackage.json"
MANIFIESTO = ROOT / "data_manifest.json"
VISTAS_SQL = DOCS / "api" / "v2" / "views.sql"
CONSULTAS_JS = DOCS / "js" / "download_catalog.js"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _numero(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def _enlace(ruta_doc: str, ruta_ficha: Path) -> str:
    destino = (DOCS / ruta_doc).resolve()
    if not destino.is_relative_to(DOCS.resolve()) or not destino.is_file():
        raise SystemExit(f"Destino de ficha ausente o fuera de docs/: {ruta_doc}")
    return os.path.relpath(destino, (DOCS / ruta_ficha).resolve()).replace(os.sep, "/")


def _labels_descargas() -> dict[str, dict[str, str]]:
    texto = CONSULTAS_JS.read_text(encoding="utf-8")
    prefijo = "window.DOWNLOAD_CATALOG ="
    payload = texto.split(prefijo, 1)[1].strip()
    if not payload.endswith(";"):
        raise SystemExit("download_catalog.js no contiene un artefacto JSON reconocible")
    data = json.loads(payload[:-1].strip())
    labels: dict[str, dict[str, str]] = {}
    for grupo in data.get("grupos", []):
        for item in grupo.get("items", []):
            if item.get("id"):
                labels[item["id"]] = {
                    "detalle": str(item.get("detalle") or ""),
                    "nombre": str(item.get("nombre") or ""),
                    "grupo": str(grupo.get("grupo") or ""),
                }
    return labels


def construir_ficha(id_api: str, verificar_hash: bool = True) -> str:
    """Construye HTML genérico en memoria; no escribe archivos.

    `verificar_hash=False` sirve para probar estados de interfaz rápidamente; el
    contrato publicado verifica los hashes de todas las particiones por separado.
    """
    catalogo = _json(CATALOGO)
    paquete = _json(DATAPACKAGE)
    manifiesto = _json(MANIFIESTO)
    version = str(catalogo.get("version") or "")
    release = str(catalogo.get("data_release") or "")
    if not version or paquete.get("version") != version or not release:
        raise SystemExit("Catálogo/Data Package sin versión o data_release coherentes")

    objeto = next((o for o in catalogo.get("objetos", []) if o.get("id") == id_api), None)
    if not objeto:
        raise SystemExit(f"ID no publicado en catalog.json: {id_api}")
    if objeto.get("procedencia"):
        raise SystemExit(f"{id_api} tiene procedencia estructurada y requiere su ficha especializada")
    recurso = next((r for r in paquete.get("resources", []) if r.get("name") == id_api), None)
    manifest_id = str(((recurso or {}).get("sif") or {}).get("manifest_id") or id_api)
    tabla = next((t for t in manifiesto.get("tables", []) if t.get("id") == manifest_id), None)
    meta = (tabla or {}).get("metadatos") or {}

    schema_path = DOCS / "api" / "v2" / "schema" / f"{id_api}.json"
    partition_path = DOCS / "api" / "v2" / "partitions" / f"{id_api}.json"
    schema = _json(schema_path)
    descriptor = _json(partition_path)
    if descriptor.get("id") != id_api:
        raise SystemExit(f"ID incorrecto en descriptor de particiones para {id_api}")
    parts = descriptor.get("particiones") or []
    total = descriptor.get("total") or {}
    rows = int(objeto.get("filas") or 0)
    byte_count = int(objeto.get("bytes") or 0)
    if len(parts) != int(objeto.get("particiones") or 0):
        raise SystemExit(f"Conteo de particiones inconsistente para {id_api}")
    if (int(total.get("archivos") or 0), int(total.get("filas") or 0), int(total.get("bytes") or 0)) != (len(parts), rows, byte_count):
        raise SystemExit(f"Totales de particiones inconsistentes para {id_api}")
    if schema.get("primaryKey") != objeto.get("primaryKey"):
        raise SystemExit(f"primaryKey no coincide entre catálogo y esquema para {id_api}")
    if recurso:
        if int(recurso.get("bytes") or 0) != byte_count:
            raise SystemExit(f"Bytes del recurso Data Package no coinciden para {id_api}")
    elif parts or rows or byte_count:
        raise SystemExit(f"{id_api} tiene datos publicados pero falta en Data Package")

    ficha_dir = Path("datos") / id_api
    rutas_archivo: list[tuple[dict[str, Any], str]] = []
    for part in parts:
        archivo = str(part.get("archivo") or "")
        if not archivo.startswith("outputs/"):
            raise SystemExit(f"Ruta de partición no segura para {id_api}: {archivo}")
        local = DOCS / archivo
        if not local.is_file() or local.stat().st_size != int(part.get("bytes") or 0):
            raise SystemExit(f"Archivo físico ausente o con tamaño distinto: {archivo}")
        sha = str(part.get("sha256") or "")
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise SystemExit(f"SHA-256 ausente o inválido en {archivo}")
        if verificar_hash and _sha256(local) != sha:
            raise SystemExit(f"SHA-256 físico no coincide: {archivo}")
        rutas_archivo.append((part, _enlace(archivo, ficha_dir)))

    rutas = {
        "inicio": _enlace("index.html", ficha_dir),
        "esquema": _enlace(f"api/v2/schema/{id_api}.json", ficha_dir),
        "particiones": _enlace(f"api/v2/partitions/{id_api}.json", ficha_dir),
        "datapackage": _enlace("api/v2/datapackage.json", ficha_dir) if recurso else None,
    }
    sql_view = str(objeto.get("sql_view") or "")
    views_sql = VISTAS_SQL.read_text(encoding="utf-8")
    ddl_view = bool(sql_view and re.search(
        r"CREATE\s+OR\s+REPLACE\s+VIEW\s+[\"`]?" + re.escape(sql_view) + r"[\"`]?\s+AS\b",
        views_sql,
        re.IGNORECASE,
    ))
    sql_disponible = bool(rows > 0 and parts and ddl_view)
    consulta = f"SELECT * FROM {sql_view} LIMIT 20;" if sql_disponible else ""
    sql_url = f"{rutas['inicio']}#sql={quote(consulta, safe='')}" if consulta else ""

    labels = _labels_descargas().get(id_api, {})
    grupo = labels.get("grupo") or str(objeto.get("sector") or "")
    nombre = labels.get("detalle") or labels.get("nombre") or str(objeto.get("titulo") or id_api)
    titulo = f"{nombre} · {grupo}" if grupo else nombre
    descripcion = str(objeto.get("descripcion") or "")
    fuente = str(objeto.get("fuente") or meta.get("fuente") or "")
    atribucion = str(objeto.get("atribucion") or "")
    terms = str(objeto.get("url_terminos") or "")
    estado_licencia = str(objeto.get("licencia_estado") or "")
    primary = schema.get("primaryKey") or []
    primary_text = ", ".join(str(k) for k in primary) if primary else "No declarada"
    columns = schema.get("columnas") or []
    period = str(objeto.get("corte") or meta.get("cobertura") or "")
    extraction = str(meta.get("fecha_extraccion") or ((recurso or {}).get("sif") or {}).get("extracted_at") or "")
    freshness = str(objeto.get("frescura") or "")
    unit = str(meta.get("unidad") or "")
    qa = str(meta.get("estado_qa") or "")

    stats = [
        ("Registros", _numero(rows)),
        ("Archivos Parquet", _numero(len(parts))),
        ("Tamaño publicado", f"{_numero(byte_count)} bytes"),
        ("Columnas", _numero(len(columns))),
        ("Estado", "Sin filas declaradas" if rows == 0 else "Publicado"),
    ]
    if period:
        stats.append(("Cobertura declarada", period))
    if extraction:
        stats.append(("Extracción declarada", extraction))
    if freshness:
        stats.append(("Frescura declarada", freshness))
    if unit:
        stats.append(("Unidad", unit))
    stats.extend([
        ("Versión API", version),
        ("Identificador de publicación", release),
        ("Clave primaria", primary_text),
    ])
    stats_html = "\n".join(
        f"<div><dt>{_esc(label)}</dt><dd>{'<code>' + _esc(value) + '</code>' if label in {'Clave primaria', 'Identificador de publicación'} else _esc(value)}</dd></div>"
        for label, value in stats
    )

    if len(rutas_archivo) == 1:
        part, href = rutas_archivo[0]
        acciones_archivo = f'<a class="boton" href="{_esc(href)}" download>Descargar Parquet ({_numero(int(part.get("bytes") or 0))} bytes)</a>'
    elif rutas_archivo:
        items_archivo = "\n".join(
            "<li>"
            f"<a href=\"{_esc(href)}\" download>{_esc(part.get('periodo') or Path(str(part.get('archivo'))).name)}</a>"
            f" <span>· {_numero(int(part.get('bytes') or 0))} bytes</span>"
            "</li>"
            for part, href in rutas_archivo
        )
        acciones_archivo = (
            f'<details class="archivos"><summary>Descargar archivos Parquet ({_numero(len(parts))})</summary>'
            f'<ol>{items_archivo}</ol></details>'
        )
    else:
        acciones_archivo = '<p class="nota">No hay archivos Parquet publicados para este objeto; no se ofrece una descarga.</p>'

    acciones = [acciones_archivo]
    acciones.append(f'<a class="boton secundario" href="{_esc(rutas["esquema"])}">Ver esquema JSON</a>')
    acciones.append(f'<a class="boton secundario" href="{_esc(rutas["particiones"])}">Ver descriptor de particiones</a>')
    if recurso:
        acciones.append(f'<a class="boton secundario" href="{_esc(rutas["datapackage"])}">Ver Data Package (recurso { _esc(id_api) })</a>')
    actions_html = "\n".join(acciones)

    filas_columnas = "\n".join(
        "<tr>"
        f"<th scope=\"row\"><code>{_esc(col.get('nombre'))}</code></th>"
        f"<td><code>{_esc(col.get('tipo'))}</code></td>"
        f"<td>{_esc(col.get('significado') or col.get('descripcion') or 'No declarado en el esquema.')}</td>"
        "</tr>"
        for col in columns
    )
    rows_table = "\n".join(
        "<tr>"
        f"<th scope=\"row\">{_esc(part.get('periodo') or part.get('archivo'))}</th>"
        f"<td>{_numero(int(part.get('bytes') or 0))}</td>"
        f"<td><code>{_esc(part.get('sha256'))}</code></td>"
        "</tr>"
        for part, _href in rutas_archivo
    )
    source_html = ""
    if fuente or atribucion or terms or estado_licencia:
        term_link = f' <a href="{_esc(terms)}" target="_blank" rel="noopener noreferrer">Ver condiciones declaradas</a>' if terms.startswith("https://") else ""
        state_label = {"verificada": "Verificada según el contrato", "pendiente_verificacion": "Pendiente de verificación"}.get(estado_licencia, estado_licencia)
        state_html = f"<p><strong>Estado de condiciones en el catálogo:</strong> {_esc(state_label)}.{term_link}</p>" if state_label else term_link
        source_html = (
            '<h2>Fuente y condiciones</h2>'
            + (f'<p><strong>Fuente declarada:</strong> {_esc(fuente)}</p>' if fuente else "")
            + (f'<p>{_esc(atribucion)}</p>' if atribucion else "")
            + state_html
        )
    qa_html = f'<aside class="nota"><strong>Observación QA declarada en el manifest:</strong> {_esc(qa)}</aside>' if qa else ""
    zero_note = ""
    if rows == 0:
        if parts:
            zero_note = '<aside class="nota"><strong>El contrato declara 0 filas.</strong> El archivo se ofrece para inspeccionar su estado; el cero no acredita que el período esté completo ni que no existan datos en la fuente.</aside>'
        else:
            zero_note = '<aside class="nota"><strong>El contrato declara 0 filas y 0 archivos.</strong> Por eso esta ficha no ofrece descarga ni SQL.</aside>'
    if sql_disponible:
        query_html = (
            '<h2>Consulta SQL</h2>'
            '<p>Esta consulta se ejecuta localmente en el navegador; no hay SQL remoto.</p>'
            f'<pre><code>{_esc(consulta)}</code></pre>'
            f'<p><a href="{_esc(sql_url)}">Abrir la consulta en el explorador del sitio</a></p>'
        )
    else:
        query_html = ""

    if not columns:
        schema_html = '<p>No hay columnas declaradas en el esquema disponible.</p>'
    else:
        schema_html = (
            f'<details><summary>Ver definición de las {_numero(len(columns))} columnas</summary>'
            '<div class="tabla-wrap"><table><thead><tr><th scope="col">Columna</th><th scope="col">Tipo</th><th scope="col">Significado declarado</th></tr></thead>'
            f'<tbody>{filas_columnas}</tbody></table></div></details>'
        )
    integrity_html = (
        '<h2>Integridad de archivos</h2>'
        + ('<p>SHA-256 publicado por archivo:</p><div class="tabla-wrap"><table><thead><tr><th scope="col">Período/archivo</th><th scope="col">Bytes</th><th scope="col">SHA-256</th></tr></thead>'
           f'<tbody>{rows_table}</tbody></table></div>' if rows_table else '<p>No hay huellas SHA-256 de archivos porque el contrato no publica particiones.</p>')
        + '<p>Hashes e identificador de publicación distinguen bytes publicados; no garantizan recuperar versiones históricas.</p>'
    )
    documento = f'''<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,follow">
<meta name="description" content="Ficha piloto de {_esc(titulo)}: metadatos declarados, disponibilidad y acciones que existen para este objeto.">
<title>{_esc(titulo)} · SIF Chile</title>
<style>
:root {{ color-scheme:light; --tinta:#17212b; --secundario:#4b5967; --fondo:#f4f6f8; --papel:#fff; --borde:#cbd3db; --enlace:#075a84; --aviso-fondo:#fff4d6; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--fondo); color:var(--tinta); font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
a {{ color:var(--enlace); text-underline-offset:.18em; }} a:focus-visible,summary:focus-visible {{ outline:3px solid #a44900; outline-offset:3px; border-radius:2px; }}
.marco {{ width:min(100% - 2rem,72rem); margin-inline:auto; }} header {{ padding:1rem 0; border-bottom:1px solid var(--borde); background:var(--papel); }} main {{ padding:2rem 0 4rem; }}
.sobrelinea {{ color:var(--secundario); font-size:.95rem; }} h1 {{ font-size:clamp(1.8rem,4vw,2.6rem); line-height:1.15; }} h2 {{ margin-top:2rem; font-size:1.35rem; }} code {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; overflow-wrap:anywhere; }}
.resumen {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(9rem,1fr)); gap:.7rem 1.25rem; padding:1rem 0; border-block:1px solid var(--borde); }} .resumen div {{ min-width:0; }} dt {{ color:var(--secundario); font-size:.88rem; }} dd {{ margin:.1rem 0 0; font-weight:650; }}
.acciones {{ display:flex; flex-wrap:wrap; align-items:start; gap:.65rem; margin:1.25rem 0; }} .boton {{ display:inline-block; min-height:2.75rem; padding:.6rem .9rem; border:1px solid var(--enlace); border-radius:.35rem; background:var(--enlace); color:#fff; font-weight:650; text-decoration:none; }} .boton.secundario {{ background:var(--papel); color:var(--enlace); }}
.nota {{ padding:.85rem 1rem; border-left:4px solid #a46a00; background:var(--aviso-fondo); color:#3b2b12; }} .tabla-wrap {{ overflow-x:auto; border:1px solid var(--borde); background:var(--papel); }} table {{ width:100%; border-collapse:collapse; }} th,td {{ padding:.6rem .7rem; border-bottom:1px solid #dce2e7; text-align:left; vertical-align:top; }} thead th {{ background:#edf1f4; }} details {{ margin:1rem 0; }} summary {{ cursor:pointer; font-weight:650; }} ol {{ padding-left:1.5rem; }}
footer {{ border-top:1px solid var(--borde); padding:1rem 0 2rem; color:var(--secundario); font-size:.9rem; }} @media (max-width:38rem) {{ .marco {{ width:min(100% - 1.25rem,72rem); }} main {{ padding-top:1.25rem; }} .acciones {{ display:grid; }} .boton {{ text-align:center; }} th,td {{ padding:.5rem; }} }} @media(prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ scroll-behavior:auto !important; }} }}
</style></head><body>
<header><div class="marco"><nav aria-label="Navegación de la ficha"><a href="{_esc(rutas['inicio'])}">Volver al sitio SIF Chile</a> › Ficha piloto</nav></div></header>
<main class="marco"><p class="sobrelinea">{_esc(grupo)} · Ficha técnica piloto</p><h1>{_esc(titulo)}</h1><p class="id">ID de API: <code>{_esc(id_api)}</code></p>
{f'<p>{_esc(descripcion)}</p>' if descripcion else ''}
<dl class="resumen">{stats_html}</dl>
<section class="acciones" aria-label="Acciones disponibles">{actions_html}</section>
{zero_note}
{f'<p class="sobrelinea">Frescura declarada: {_esc(freshness)}</p>' if freshness else ''}
{source_html}
{qa_html}
<h2>Esquema</h2><p>El descriptor enlazado arriba contiene la definición oficial del objeto.</p>{schema_html}
{query_html}
{integrity_html}
</main><footer><div class="marco">Ficha piloto no indexable. La licencia MIT cubre el código, no los datos de terceros; verifica las condiciones de cada fuente antes de reutilizar.</div></footer>
</body></html>'''
    if "<script" in documento.lower():
        raise SystemExit(f"La ficha de {id_api} requiere JavaScript para su contenido esencial")
    return documento

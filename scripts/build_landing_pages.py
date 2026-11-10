#!/usr/bin/env python3
"""Genera páginas HTML temáticas e indexables desde la API publicada.

Las páginas combinan contenido editorial curado en docs/seo_landing_pages.json
con periodos, recuentos, tablas, enlaces de API y consultas actuales del catálogo.
Así cada URL ofrece contenido útil sin duplicar cifras que envejecen con los datos.

Uso:
  python scripts/build_landing_pages.py
  python scripts/build_landing_pages.py --check
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = DOCS / "seo_landing_pages.json"
CATALOG = DOCS / "api" / "v2" / "catalog.json"
QUERIES = DOCS / "api" / "v2" / "queries.json"
INDEX = DOCS / "index.html"
BEGIN = "<!-- SEO-TEMAS:INICIO -->"
END = "<!-- SEO-TEMAS:FIN -->"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def thousands(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def replace_block(source: str, block: str) -> str:
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise SystemExit(f"index.html debe contener una pareja de marcas {BEGIN} / {END}")
    start = source.index(BEGIN)
    finish = source.index(END) + len(END)
    if finish < start:
        raise SystemExit("las marcas SEO-TEMAS están invertidas")
    return source[:start] + block + source[finish:]


def query_url(base: str, sql: str) -> str:
    return f"{base}/#sql={quote(sql, safe='')}"


def render_index_nav(base: str, pages: list[dict]) -> str:
    links = "\n".join(
        f'                  <a href="{esc(base)}/temas/{esc(p["slug"])}/">{esc(p["nav_label"])}</a>'
        for p in pages
    )
    return (
        f"{BEGIN}\n"
        '              <nav class="seo-topic-nav" aria-label="Guías de datos financieros por mercado">\n'
        '                <span>Guías de datos</span>\n'
        f"{links}\n"
        "              </nav>\n"
        f"{END}"
    )


def render_page(base: str, page: dict, objects: list[dict], queries: list[dict], generated: str) -> str:
    url = f"{base}/temas/{page['slug']}/"
    periods = [o.get("corte", "") for o in objects if o.get("corte")]
    date_ranges = sorted({p for p in periods})
    newest = max((o.get("ultima_actualizacion", "") for o in objects), default="")
    rows = []
    for item in objects:
        detail_links = []
        if item.get("particiones_url"):
            detail_links.append(f'<a href="{esc(item["particiones_url"])}">Descargas</a>')
        if item.get("esquema"):
            detail_links.append(f'<a href="{esc(item["esquema"])}">Esquema</a>')
        if item.get("url_terminos"):
            detail_links.append(f'<a href="{esc(item["url_terminos"])}" rel="external">Condiciones de uso</a>')
        rows.append(
            "<tr>"
            f'<td><strong>{esc(item.get("titulo", item["id"]))}</strong>'
            f'<span class="seo-description">{esc(item.get("descripcion", ""))}</span></td>'
            f'<td>{esc(item.get("corte", "Sin periodo declarado"))}</td>'
            f'<td>{thousands(item.get("filas", 0))}</td>'
            f'<td>{" · ".join(detail_links)}</td>'
            "</tr>"
        )
    tables = "\n".join(rows)
    query_cards = "\n".join(
        f'<li><a href="{esc(query_url(base, q["sql"]))}">{esc(q["titulo"])}'
        '<small>Abre la consulta SQL en SIF Chile.</small></a></li>'
        for q in queries
    )
    sections = []
    for section in page["secciones"]:
        paragraphs = "\n".join(f"<p>{esc(text)}</p>" for text in section["parrafos"])
        sections.append(f'<section class="seo-section"><h2>{esc(section["titulo"])}</h2>{paragraphs}</section>')
    related = [p for p in CONFIG_DATA["paginas"] if p["slug"] != page["slug"]]
    related_links = "\n".join(
        f'<li><a href="{esc(base)}/temas/{esc(p["slug"])}/">{esc(p["nav_label"])}</a></li>'
        for p in related
    )
    json_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": page["titulo"],
        "description": page["descripcion"],
        "url": url,
        "inLanguage": "es-CL",
        "dateModified": generated,
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(objects),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "item": {
                        "@type": "Dataset",
                        "name": item.get("titulo", item["id"]),
                        "description": item.get("descripcion", ""),
                        "temporalCoverage": item.get("corte", ""),
                        "url": item.get("particiones_url", ""),
                    },
                }
                for index, item in enumerate(objects, 1)
            ],
        },
        "publisher": {
            "@type": "Organization",
            "name": "Sistema de Información Financiera de Chile",
            "url": f"{base}/",
        },
    }
    ld = json.dumps(json_ld, ensure_ascii=False, indent=2).replace("</", "<\\/")
    periods_html = " · ".join(esc(p) for p in date_ranges)
    return f'''<!doctype html>
<html lang="es-CL">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page["titulo"])}</title>
  <meta name="description" content="{esc(page["descripcion"])}">
  <link rel="canonical" href="{esc(url)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="es_CL">
  <meta property="og:site_name" content="Sistema de Información Financiera de Chile">
  <meta property="og:title" content="{esc(page["titulo"])}">
  <meta property="og:description" content="{esc(page["descripcion"])}">
  <meta property="og:url" content="{esc(url)}">
  <meta property="og:image" content="{esc(base)}/assets/og_sif_1200x630.png">
  <meta property="og:image:alt" content="SIF Chile: datos financieros públicos organizados por mercado">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{esc(base)}/assets/og_sif_1200x630.png">
  <link rel="stylesheet" href="../../css/seo-content.css">
  <script type="application/ld+json">{ld}</script>
</head>
<body>
  <main class="seo-page">
    <nav class="seo-breadcrumbs" aria-label="Ruta de navegación"><a href="{esc(base)}/">SIF Chile</a> › Datos por mercado</nav>
    <header class="seo-hero">
      <p class="seo-kicker">Datos públicos · Chile · CMF</p>
      <h1>{esc(page["h1"])}</h1>
      <p class="seo-lead">{esc(page["bajada"])}</p>
      <p class="seo-meta">Coberturas declaradas: {periods_html}. Última actualización de estos conjuntos: {esc(newest or generated)}.</p>
      <div class="seo-actions">
        <a class="seo-button seo-button-primary" href="{esc(query_url(base, queries[0]["sql"]))}">Probar una consulta SQL</a>
        <a class="seo-button" href="{esc(base)}/">Abrir el explorador completo</a>
      </div>
    </header>
    <section class="seo-section" aria-labelledby="conjuntos-title">
      <h2 id="conjuntos-title">Conjuntos de datos disponibles</h2>
      <p>Los periodos y recuentos se leen del catálogo publicado. Abre el manifiesto para descargar por periodo o el esquema para revisar campos y definiciones.</p>
      <div class="seo-table-wrap"><table class="seo-table">
        <thead><tr><th>Conjunto y descripción</th><th>Periodo disponible</th><th>Filas</th><th>Recursos</th></tr></thead>
        <tbody>{tables}</tbody>
      </table></div>
    </section>
    {''.join(sections)}
    <section class="seo-section" aria-labelledby="consultas-title">
      <h2 id="consultas-title">Consultas listas para usar</h2>
      <p>Cada ejemplo abre el explorador SQL con una consulta preparada sobre el último periodo que contiene el catálogo.</p>
      <ul class="seo-query-list">{query_cards}</ul>
    </section>
    <section class="seo-section" aria-labelledby="api-title">
      <h2 id="api-title">API y descargas</h2>
      <p>Los datos están disponibles como archivos estáticos y pueden utilizarse desde Python, DuckDB u otras herramientas compatibles con Parquet. El catálogo API describe los objetos y sus recursos; los manifiestos de cada conjunto enumeran los archivos y periodos.</p>
      <ul>
        <li><a href="{esc(base)}/api/v2/catalog.json">Catálogo API completo (JSON)</a></li>
        <li><a href="{esc(base)}/api/v2/datapackage.json">Data Package</a></li>
        <li><a href="https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile">Código fuente y documentación en GitHub</a></li>
      </ul>
    </section>
    <section class="seo-section" aria-labelledby="relacionados-title">
      <h2 id="relacionados-title">Más datos financieros de Chile</h2>
      <ul class="seo-related-list">{related_links}</ul>
    </section>
    <footer class="seo-footer">
      <p>Proyecto independiente de consulta y distribución de datos públicos. No representa a la CMF ni a los organismos fuente. Las cifras y definiciones originales se deben verificar en sus publicaciones.</p>
      <p><a href="{esc(base)}/privacidad.html">Privacidad</a> · <a href="https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/blob/main/DATA_LICENSE.md">Licencia y atribución de datos</a></p>
    </footer>
  </main>
</body>
</html>
'''


def construir() -> dict[Path, str]:
    global CONFIG_DATA
    CONFIG_DATA = read_json(CONFIG)
    catalog = read_json(CATALOG)
    query_catalog = read_json(QUERIES)
    base = str(catalog["base"]).rstrip("/")
    objects = {item["id"]: item for item in catalog.get("objetos", [])}
    queries = query_catalog.get("consultas", [])
    outputs: dict[Path, str] = {}
    nav_pages = []
    seen_slugs = set()
    for page in CONFIG_DATA.get("paginas", []):
        slug = str(page.get("slug", ""))
        if not slug or slug in seen_slugs or "/" in slug or ".." in slug:
            raise SystemExit(f"slug vacío, duplicado o inseguro: {slug!r}")
        seen_slugs.add(slug)
        selected = []
        for item_id in page.get("ids", []):
            if item_id not in objects:
                raise SystemExit(f"{slug}: ID no publicado en catalog.json: {item_id}")
            item = objects[item_id]
            if int(item.get("filas", 0)) > 0:
                selected.append(item)
        if not selected:
            raise SystemExit(f"{slug}: no hay conjuntos publicados con filas")
        selected_queries = []
        for title in page.get("consultas", []):
            match = next((q for q in queries if q.get("titulo") == title), None)
            if not match or not match.get("sql"):
                raise SystemExit(f"{slug}: falta la consulta publicada «{title}»")
            selected_queries.append(match)
        if not selected_queries:
            raise SystemExit(f"{slug}: falta al menos una consulta de ejemplo")
        target = DOCS / "temas" / slug / "index.html"
        outputs[target] = render_page(base, page, selected, selected_queries, str(catalog.get("generado", "")))
        nav_pages.append(page)

    index = INDEX.read_text(encoding="utf-8")
    outputs[INDEX] = replace_block(index, render_index_nav(base, nav_pages))
    return outputs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = construir()
    stale = []
    for path, expected in outputs.items():
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual != expected:
            if args.check:
                stale.append(path.relative_to(ROOT).as_posix())
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8")
    if stale:
        print("Páginas temáticas atrasadas:")
        print("\n".join(f"  - {path}" for path in stale))
        print("Ejecuta scripts/build_landing_pages.py")
        return 1
    estado = "al día" if args.check else "generadas"
    print(f"Páginas temáticas {estado}: {len(outputs) - 1} páginas y enlaces de portada")
    return 0


if __name__ == "__main__":
    sys.exit(main())

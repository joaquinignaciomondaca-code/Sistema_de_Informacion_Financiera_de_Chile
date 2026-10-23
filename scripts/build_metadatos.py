#!/usr/bin/env python3
"""Genera el `<head>` social de la portada, `robots.txt` y `sitemap.xml`.

Tres piezas que se desfasan solas si se escriben a mano: la descripción que ve
un buscador, las etiquetas que arma la tarjeta al compartir el enlace y el
mapa del sitio. Aquí se calculan desde el contrato publicado
(`docs/api/v2/catalog.json`), así que las cifras no pueden quedar viejas.

Qué escribe:

  * un bloque entre `<!-- SEO:INICIO -->` y `<!-- SEO:FIN -->` en
    `docs/index.html` (meta description, Open Graph, Twitter, canonical y las
    huellas de la imagen social);
  * el canonical de `docs/privacidad.html` (la otra página del sitemap);
  * `docs/robots.txt`, que permite todo y apunta al sitemap;
  * `docs/sitemap.xml` con las dos páginas del sitio.

`--check` falla si algo quedó atrás, igual que el resto del contrato.
La imagen social la produce `scripts/build_og_image.py`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
INDICE = DOCS / "index.html"
CATALOGO = DOCS / "api" / "v2" / "catalog.json"
IMAGEN = DOCS / "assets" / "og_sif_1200x630.png"
PRIVACIDAD = DOCS / "privacidad.html"

BASE = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile"
INICIO = "<!-- SEO:INICIO -->"
FIN = "<!-- SEO:FIN -->"

TITULO = "Sistema de Información Financiera de Chile — Inversiones institucionales y mercados"


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def datos() -> dict:
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    t = cat["totales"]
    return {
        "objetos": t["objetos"],
        "con_datos": t["con_datos"],
        "filas": t["filas"],
        "consultas": t["consultas"],
        "release": cat["data_release"],
    }


def descripcion(d: dict) -> str:
    """La frase que se lee en un resultado de búsqueda (≤ 160 caracteres)."""
    texto = (f"{d['con_datos']} conjuntos de datos financieros públicos de Chile "
             f"—bancos, seguros, fondos, cooperativas, fintech y macro—, "
             f"{miles(d['filas'])} filas en Parquet, sin registro.")
    if len(texto) > 160:
        raise SystemExit(f"la meta description tiene {len(texto)} caracteres; el tope es 160")
    return texto


def bloque(d: dict, imagen_sha: str) -> str:
    desc = descripcion(d)
    img = f"{BASE}/assets/{IMAGEN.name}"
    lineas = [
        INICIO,
        "  <!-- Generado por scripts/build_metadatos.py desde el catálogo publicado.",
        "       No editar a mano: --check falla si no coincide. -->",
        f'  <meta name="description" content="{desc}">',
        f'  <link rel="canonical" href="{BASE}/">',
        "",
        '  <meta property="og:type" content="website">',
        '  <meta property="og:site_name" content="Sistema de Información Financiera de Chile">',
        '  <meta property="og:locale" content="es_CL">',
        f'  <meta property="og:title" content="{TITULO}">',
        f'  <meta property="og:description" content="{desc}">',
        f'  <meta property="og:url" content="{BASE}/">',
        f'  <meta property="og:image" content="{img}">',
        '  <meta property="og:image:type" content="image/png">',
        '  <meta property="og:image:width" content="1200">',
        '  <meta property="og:image:height" content="630">',
        '  <meta property="og:image:alt" content="SIF — Sistema de Información Financiera de Chile: '
        f'{d["objetos"]} objetos y {miles(d["filas"])} filas de datos financieros públicos.">',
        f'  <meta property="og:image:secure_url" content="{img}">',
        # Huella del archivo: si la imagen cambia y no se regenera esto, --check lo dice.
        f'  <meta name="sif:og-image-sha256" content="{imagen_sha}">',
        "",
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="twitter:title" content="{TITULO}">',
        f'  <meta name="twitter:description" content="{desc}">',
        f'  <meta name="twitter:image" content="{img}">',
        '  <meta name="twitter:image:alt" content="SIF — Sistema de Información Financiera de Chile">',
        "",
        f'  <meta name="sif:data-release" content="{d["release"]}">',
        FIN,
    ]
    return "\n".join(lineas)


def canonical_privacidad() -> str:
    """Sólo el canonical: esa página ya tiene su descripción escrita a mano."""
    return (INICIO + "\n"
            f'  <link rel="canonical" href="{BASE}/privacidad.html">\n'
            + FIN)


def robots() -> str:
    return (
        "# SIF — Sistema de Información Financiera de Chile\n"
        "# Todo el sitio es público y se puede rastrear; no hay áreas privadas.\n"
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n"
    )


def sitemap() -> str:
    paginas = [
        (f"{BASE}/", "1.0", "daily"),
        (f"{BASE}/privacidad.html", "0.3", "monthly"),
    ]
    filas = "\n".join(
        f'  <url>\n    <loc>{url}</loc>\n    <changefreq>{freq}</changefreq>\n'
        f'    <priority>{prio}</priority>\n  </url>'
        for url, prio, freq in paginas
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{filas}\n</urlset>\n")


def con_bloque(html: str, nuevo: str) -> str:
    if INICIO in html and FIN in html:
        antes = html[: html.index(INICIO)]
        despues = html[html.index(FIN) + len(FIN):]
        return antes + nuevo + despues
    # Primera vez: el bloque entra después de <title>, que es donde lo leen
    # los rastreadores que cortan el <head> temprano.
    marca = "</title>"
    if marca not in html:
        raise SystemExit("index.html no tiene <title>: no se puede insertar el bloque")
    corte = html.index(marca) + len(marca)
    return html[:corte] + "\n\n" + nuevo + html[corte:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not IMAGEN.exists():
        print(f"METADATOS: falta {IMAGEN.relative_to(RAIZ)}; ejecuta scripts/build_og_image.py")
        return 1
    sha = hashlib.sha256(IMAGEN.read_bytes()).hexdigest()

    d = datos()
    actual = INDICE.read_text(encoding="utf-8")
    nuevo_html = con_bloque(actual, bloque(d, sha))
    privacidad = PRIVACIDAD.read_text(encoding="utf-8")
    nuevos = {
        INDICE: nuevo_html,
        PRIVACIDAD: con_bloque(privacidad, canonical_privacidad()),
        DOCS / "robots.txt": robots(),
        DOCS / "sitemap.xml": sitemap(),
    }

    if args.check:
        fallos = []
        for ruta, contenido in nuevos.items():
            if not ruta.exists():
                fallos.append(f"falta {ruta.relative_to(RAIZ)}")
            elif ruta.read_text(encoding="utf-8") != contenido:
                fallos.append(f"{ruta.relative_to(RAIZ)} está desactualizado")
        if fallos:
            for f in fallos:
                print(f"METADATOS: {f}")
            print("METADATOS: ejecuta scripts/build_metadatos.py")
            return 1
        print(f"METADATOS: al día (description de {len(descripcion(d))} caracteres, "
              f"og:image {IMAGEN.name}, robots.txt y sitemap.xml)")
        return 0

    for ruta, contenido in nuevos.items():
        ruta.write_text(contenido, encoding="utf-8")
    print(f"Escrito el bloque social de index.html, robots.txt y sitemap.xml · "
          f"{d['objetos']} objetos, {miles(d['filas'])} filas, {d['consultas']} consultas · "
          f"data_release {d['release']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

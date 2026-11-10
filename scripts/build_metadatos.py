#!/usr/bin/env python3
"""Genera el `<head>` social de la portada, `robots.txt` y `sitemap.xml`.

Tres piezas que se desfasan solas si se escriben a mano: la descripción que ve
un buscador, las etiquetas que arma la tarjeta al compartir el enlace y el
mapa del sitio. Aquí se calculan desde el contrato publicado
(`docs/api/v2/catalog.json`), así que las cifras no pueden quedar viejas.

Qué escribe:

  * un bloque entre `<!-- SEO:INICIO -->` y `<!-- SEO:FIN -->` en
    `docs/index.html` (meta description, Open Graph, Twitter, canonical,
    JSON-LD Dataset y las huellas de la imagen social);
 * el canonical de `docs/privacidad.html`;
 * `docs/robots.txt`, que permite todo y apunta al sitemap;
 * `docs/sitemap.xml`, generado escaneando páginas HTML indexables bajo `docs/`
   (excluye `noindex` y archivos de verificación), con URLs canónicas y `lastmod`;
 * `docs/opensearch.xml`, descriptor para que los navegadores busquen dentro
   del sitio desde la barra de direcciones.

`--check` falla si algo quedó atrás, igual que el resto del contrato.
La imagen social la produce `scripts/build_og_image.py`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
        "generado": cat.get("generado", ""),
    }


def descripcion(d: dict) -> str:
    """La frase que se lee en un resultado de búsqueda (≤ 160 caracteres)."""
    # Sin contar conjuntos a propósito: la portada publica «74 conjuntos
    # visibles» y el contrato 86 con datos, y las dos cifras son ciertas pero
    # juntas se leen como una contradicción en un resultado de búsqueda.
    # La cifra se trunca hacia abajo y se declara aproximada: «19,8 millones»
    # prometía 19.800.000 filas cuando hay 19.777.517. Misma regla que
    # docs/js/alcance.js (dos cifras significativas, nunca al alza).
    millones = d["filas"] / 1_000_000
    cifra = math.floor(millones) if millones >= 10 else math.floor(millones * 10) / 10
    if millones >= 10:
        legible = f"{cifra}"
    else:
        legible = f"{cifra:.1f}".replace(".", ",")
    aproximada = "más de " if d["filas"] > cifra * 1_000_000 else ""
    texto = ("Datos financieros públicos de Chile —bancos, seguros, fondos, "
             f"cooperativas, fintech y macro—: {aproximada}{legible} millones de filas en "
             "Parquet y SQL.")
    if len(texto) > 160:
        raise SystemExit(f"la meta description tiene {len(texto)} caracteres; el tope es 160")
    return texto


def json_ld_dataset(cat: dict, d: dict) -> str:
    """Marcado estructurado schema.org/Dataset para la portada."""
    objetos = cat.get("objetos", [])
    fuentes = sorted({o.get("fuente", "") for o in objetos if o.get("fuente")})
    sectores = sorted({o.get("sector", "") for o in objetos if o.get("sector")})
    distribucion = [
        {
            "@type": "DataDownload",
            "name": "Catálogo API (JSON)",
            "encodingFormat": "application/json",
            "contentUrl": f"{BASE}/api/v2/catalog.json",
        },
        {
            "@type": "DataDownload",
            "name": "Data Package (Frictionless)",
            "encodingFormat": "application/json",
            "contentUrl": f"{BASE}/api/v2/datapackage.json",
        },
        {
            "@type": "DataDownload",
            "name": "Consultas SQL precálculadas",
            "encodingFormat": "application/json",
            "contentUrl": f"{BASE}/api/v2/queries.json",
        },
    ]
    dataset = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": TITULO,
        "description": descripcion(d),
        "url": f"{BASE}/",
        "datePublished": cat.get("generado", ""),
        "dateModified": cat.get("generado", ""),
        "version": cat.get("data_release", ""),
        "publisher": {
            "@type": "Organization",
            "name": "Sistema de Información Financiera de Chile",
            "url": f"{BASE}/",
        },
        "provider": {
            "@type": "Organization",
            "name": "Sistema de Información Financiera de Chile",
            "url": f"{BASE}/",
        },
        "keywords": ", ".join(sectores),
        "measurementTechnique": "Parquet y SQL en el navegador (DuckDB-Wasm)",
        "distribution": distribucion,
        "includes": [
            {
                "@type": "Dataset",
                "name": f"{len(objetos)} objetos de datos financieros públicos de Chile",
                "description": (
                    f"{miles(d['filas'])} filas, {d['objetos']} objetos, "
                    f"{d['consultas']} consultas SQL precálculadas"
                ),
            }
        ],
        "isAccessibleForFree": True,
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
    }
    # Fuentes como "about" (categorías del dataset)
    if fuentes:
        dataset["about"] = [{"@type": "Thing", "name": f} for f in fuentes]
    return (
        '  <script type="application/ld+json">\n'
        + json.dumps(dataset, ensure_ascii=False, indent=2)
        + "\n  </script>"
    )


def bloque(d: dict, imagen_sha: str, json_ld: str) -> str:
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
        f'{d["objetos"]} objetos con datos financieros públicos de Chile.">',
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
        "",
        json_ld,
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


def opensearch() -> str:
    """Descriptor OpenSearch para búsqueda desde la barra de direcciones del navegador."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">\n'
        '  <ShortName>SIF Chile</ShortName>\n'
        f'  <Description>Buscar en {TITULO}</Description>\n'
        '  <InputEncoding>UTF-8</InputEncoding>\n'
        f'  <Image width="16" height="16">{BASE}/assets/logo_sif_isotipo.svg</Image>\n'
        f'  <Url type="text/html" template="{BASE}/#q={{searchTerms}}"/>\n'
        f'  <Url type="application/opensearchdescription+xml" template="{BASE}/opensearch.xml"/>\n'
        '</OpenSearchDescription>\n'
    )


def _pagina_prioridad(ruta_relativa: Path) -> tuple[str, str, str]:
    """Devuelve (url, prioridad, changefreq) para una página HTML de docs/."""
    if ruta_relativa == Path("index.html"):
        return f"{BASE}/", "1.0", "daily"
    if ruta_relativa == Path("privacidad.html"):
        return f"{BASE}/privacidad.html", "0.3", "monthly"
    if ruta_relativa.name == "index.html" and ruta_relativa.parts[:1] == ("temas",):
        ruta = "/".join(ruta_relativa.parts[:-1])
        return f"{BASE}/{ruta}/", "0.8", "weekly"
    # Páginas de detalle bajo subdirectorios (ej. docs/datos/.../index.html).
    return f"{BASE}/{ruta_relativa.as_posix()}", "0.5", "monthly"


def sitemap(d: dict) -> str:
    paginas: list[tuple[str, str, str]] = []
    for html in sorted(DOCS.rglob("*.html")):
        ruta_relativa = html.relative_to(DOCS)
        # Ignora páginas parciales o de plantilla que no son destino de navegación.
        nombre = html.name.lower()
        if nombre.startswith("_") or nombre.endswith("_fragment.html"):
            continue
        contenido = html.read_text(encoding="utf-8", errors="replace")
        if 'name="robots" content="noindex' in contenido.lower():
            continue
        # El archivo de propiedad de Search Console verifica el sitio; no es una
        # página para resultados de búsqueda ni un destino editorial.
        if ruta_relativa.parent == Path(".") and contenido.lstrip().startswith("google-site-verification:"):
            continue
        paginas.append(_pagina_prioridad(ruta_relativa))

    filas = "\n".join(
        f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{d["generado"]}</lastmod>\n'
        f'    <changefreq>{freq}</changefreq>\n'
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

    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    d = datos()
    json_ld = json_ld_dataset(cat, d)
    actual = INDICE.read_text(encoding="utf-8")
    nuevo_html = con_bloque(actual, bloque(d, sha, json_ld))
    privacidad = PRIVACIDAD.read_text(encoding="utf-8")
    nuevos = {
        INDICE: nuevo_html,
        PRIVACIDAD: con_bloque(privacidad, canonical_privacidad()),
        DOCS / "robots.txt": robots(),
        DOCS / "sitemap.xml": sitemap(d),
        DOCS / "opensearch.xml": opensearch(),
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
              f"og:image {IMAGEN.name}, robots.txt, sitemap.xml y opensearch.xml)")
        return 0

    for ruta, contenido in nuevos.items():
        ruta.write_text(contenido, encoding="utf-8")
    print(f"Escrito el bloque social de index.html, robots.txt, sitemap.xml y opensearch.xml · "
          f"{d['objetos']} objetos, {miles(d['filas'])} filas, {d['consultas']} consultas · "
          f"data_release {d['release']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

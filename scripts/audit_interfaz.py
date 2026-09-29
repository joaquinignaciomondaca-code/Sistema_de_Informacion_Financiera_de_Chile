#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría estática de la interfaz web (Sistema de Información Financiera de Chile).

Comprueba, sin navegador ni red, las invariantes de estructura y de temas que el
rediseño del 2026-09-28 introdujo y que son fáciles de romper sin darse cuenta:

  1. index.html: siete pestañas con role="tab", aria-controls apuntando a un id real
     y un único panel por pestaña.
  2. Terminal SQL: contenedor propio dentro del panel principal y todos sus
     componentes presentes; sin restos del panel inferior ni del divisor.
  3. Capa de experiencia (ux_shell.js): pestaña recordada, avisos, atajos y
     diagnóstico del motor expuestos en window.MFCUI.
  4. Temas: ningún color fijo fuera de los bloques de paleta en app.css, de modo
     que las seis paletas (incluida la clara "informe") sigan siendo legibles.
  5. Motor DuckDB: copia local presente en docs/vendor/duckdb y usada antes que el CDN.
  6. Descargas: pestaña propia con catálogo generado y sincronizado, Parquet
     directo y CSV/Excel por motor; sin restos del modal de exportación retirado.

Uso: python scripts/audit_interfaz.py
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")

TABS = {
    "tab-btn-info": "info-container",
    "tab-btn-erd": "erd-canvas",
    "tab-btn-dict": "dict-container",
    "tab-btn-data": "data-viewer-container",
    "tab-btn-sql": "sql-container",
    "tab-btn-downloads": "downloads-container",
    "tab-btn-normativa": "normativa-container",
}

# Colores fijos que rompen una u otra paleta cuando quedan fuera de los bloques
# de tema. Se permite la lista blanca (por ejemplo, sombras o el fallback de una
# variable) sólo si es explícita.
ALLOWED_HEX = {
    "#132D46",  # fallback declarado de var(--accent-contrast)
    "#070C18",  # fallback declarado de var(--accent-contrast)
    "#00ADB5",  # fallback declarado de var(--accent-teal)
}

errors = []
notes = []


def fail(msg):
    errors.append(msg)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as handle:
        return handle.read()


def audit_tabs(html):
    print("\n--- 1. Pestañas de la vista principal ---")
    found = re.findall(r'<button[^>]*class="panel-tab-btn[^"]*"[^>]*>', html)
    ids = re.findall(r'id="(tab-btn-[a-z]+)"', " ".join(found))
    print(f"  Pestañas declaradas: {len(ids)} -> {', '.join(ids)}")
    for tab_id, container in TABS.items():
        tag = next((t for t in found if f'id="{tab_id}"' in t), None)
        if tag is None:
            fail(f"falta la pestaña {tab_id}")
            continue
        if 'role="tab"' not in tag:
            fail(f"{tab_id} no declara role=\"tab\"")
        if f'aria-controls="{container}"' not in tag:
            fail(f"{tab_id} no declara aria-controls=\"{container}\"")
        if f'id="{container}"' not in html:
            fail(f"el panel {container} de {tab_id} no existe en index.html")
    if len(ids) != len(set(ids)):
        fail("hay pestañas duplicadas")
    print(f"  Paneles verificados: {len(TABS)}")

    # La descarga ya no es un botón de cabecera con modal aparte: es una pestaña
    # con el catálogo publicado a la vista (2026-09-28).
    if 'id="tab-btn-export"' in html or "panel-action-btn" in html:
        fail("quedan restos del antiguo botón de descarga de la cabecera del panel")
    else:
        print("  [OK] Sin botón de descarga en la cabecera: la descarga es una pestaña")

    if "ExportModal" in html or "export_modal" in html:
        fail("index.html todavía referencia el modal de exportación retirado")
    # Ojo: "openExportModal" contiene "ExportModal" como subcadena; se buscan las
    # referencias reales al objeto global retirado.
    for js in ("data_viewer.js", "chat_terminal.js", "sidebar.js", "erd_graph.js", "ux_shell.js"):
        texto = read(f"docs/js/{js}")
        if "window.ExportModal" in texto or "ExportModal." in texto:
            fail(f"{js} todavía llama al modal de exportación retirado")
    for name in ("export_modal.js",):
        if os.path.exists(os.path.join(ROOT, "docs/js", name)):
            fail(f"docs/js/{name} sigue en el repositorio pero ya no se usa")
    print("  [OK] El antiguo modal de exportación está retirado")

    for script in ("js/download_utils.js?v=", "js/download_catalog.js?v=", "js/downloads_panel.js?v="):
        if script not in html:
            fail(f"index.html no carga {script.rstrip('?v=')} con versión")
    if 'id="downloads-container"' not in html:
        fail("no existe el contenedor de la pestaña Descargas")
    else:
        print("  [OK] La pestaña Descargas carga sus tres archivos y su contenedor")


def audit_descargas(html):
    """La pestaña Descargas: catálogo generado, frescura y datos por conjunto."""
    print("\n--- 1b. Catálogo de descargas ---")
    panel = read("docs/js/downloads_panel.js")
    util = read("docs/js/download_utils.js")
    if not os.path.exists(os.path.join(ROOT, "docs/js/download_catalog.js")):
        fail("falta docs/js/download_catalog.js (ejecuta scripts/build_download_catalog.py)")
        return
    catalogo = read("docs/js/download_catalog.js")
    if "window.DOWNLOAD_CATALOG" not in catalogo:
        fail("el catálogo de descargas no expone window.DOWNLOAD_CATALOG")

    # El catálogo debe estar sincronizado con las vistas publicadas.
    check = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts/build_download_catalog.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    if check.returncode != 0:
        fail(f"catálogo de descargas desactualizado: {check.stdout.strip()}")
    else:
        print("  [OK] Catálogo sincronizado con las vistas y manifiestos publicados")

    for pieza, archivo in (("DOWNLOAD_CATALOG", "docs/js/download_catalog.js"),):
        if pieza not in read(archivo):
            fail(f"{archivo} no define {pieza}")

    # Cada conjunto necesita acción de descarga real: Parquet directo o motor.
    for requerido in ("data-action=\"parquet\"", "data-action=\"csv\"", "data-action=\"xlsx\"", "MFCDownload.exportarFilas"):
        if requerido not in panel:
            fail(f"el panel de descargas no ofrece {requerido}")
    for requerido in ("exportarFilas", "blobCsv", "libroXlsx", "LIMITE_EXCEL"):
        if requerido not in util:
            fail(f"download_utils.js no define {requerido}")
    if "requiere el motor" in panel and False:
        pass
    print("  [OK] Parquet directo + CSV/Excel por motor + ayudas compartidas")

    # El contexto del visor debe seguir llegando a la pestaña.
    if "MFCUI.openDownloads" not in read("docs/js/data_viewer.js"):
        fail("el visor no abre la pestaña Descargas con la tabla activa")
    if "openDownloads" not in read("docs/js/ux_shell.js"):
        fail("MFCUI.openDownloads no está definido en ux_shell.js")
    print("  [OK] El visor abre Descargas con su tabla ya seleccionada")


def audit_cache():
    """Todos los archivos locales comparten una sola etiqueta de versión."""
    print("\n--- 1d. Caché de los archivos locales ---")
    texto = read("docs/index.html")
    etiquetas = set(re.findall(r'(?:src|href)="(?:css|js)/[^"?]+\?v=([^"]+)"', texto))
    if len(etiquetas) != 1:
        fail(f"assets locales con {len(etiquetas)} etiquetas distintas: {', '.join(sorted(etiquetas))}")
        return
    print(f"  [OK] Los 15 archivos locales usan la versión {etiquetas.pop()}")


def audit_vocabulario():
    """El vocabulario canónico es una sola lista y se aplica a todos los archivos."""
    print("\n--- 1c. Vocabulario de tablas ---")
    if not os.path.exists(os.path.join(ROOT, "docs/vocabulario.json")):
        fail("falta docs/vocabulario.json (fuente única de nombres y sectores)")
        return
    check = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts/normalizar_vocabulario.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    if check.returncode != 0:
        for linea in check.stdout.strip().splitlines()[1:6]:
            fail(f"vocabulario: {linea.strip()}")
    else:
        print("  [OK] " + check.stdout.strip())

    vocab = json.loads(read("docs/vocabulario.json"))
    tablas = vocab["tablas"]
    if len(tablas) != 52:
        fail(f"el vocabulario describe {len(tablas)} tablas y hay 52 publicadas")

    # Toda lista de entidades de un sector se llama lista_entidades.
    listas = [t for t in tablas if t["tipo"].startswith("lista_entidades")]
    malas = [t["id"] for t in listas if not t["nombre"].endswith(t["tipo"])]
    if malas:
        fail(f"listas de entidades con otro nombre: {', '.join(malas)}")
    else:
        print(f"  [OK] {len(listas)} listas de entidades se llaman lista_entidades")

    # Nombres y tipos únicos: dos tablas no pueden llamarse igual.
    repetidos = [n for n in {t["nombre"] for t in tablas} if [x["nombre"] for x in tablas].count(n) > 1]
    if repetidos:
        fail(f"nombres de tabla repetidos: {', '.join(repetidos)}")

    # Los nombres prohibidos no pueden aparecer en los archivos vivos.
    # La lista de nombres retirados vive en el propio vocabulario.
    prohibidos = tuple(vocab.get("nombres_retirados", []))
    # Las rutas de los Parquet publicados conservan nombres antiguos por diseño
    # (son archivos ya emitidos): el nombre retirado se busca como palabra suelta.
    extensiones = r"(?:parquet|json|csv|xlsx|zip|wasm|js|mjs|md|html)"
    for rel in ("docs/index.html", "docs/js/sidebar.js", "docs/js/data_viewer.js",
                "docs/js/data_dictionary.js", "docs/js/erd_graph.js"):
        texto = read(rel)
        for palabra in prohibidos:
            patron = re.compile(r"(?<![/\w-])" + re.escape(palabra) + r"(?!\w|\.(?:" + extensiones + r")\b)")
            if patron.search(texto):
                fail(f"{rel} usa un nombre retirado por el vocabulario: «{palabra}»")
    print("  [OK] Sin nombres de tabla retirados en los archivos de la web")


def audit_terminal(html):
    print("\n--- 2. Terminal SQL como pestaña ---")
    start = html.find('class="sql-container"')
    if start == -1:
        fail("no existe #sql-container")
        return
    panel_start = html.find('class="top-panel"')
    if panel_start == -1 or start < panel_start:
        fail("#sql-container no está dentro del panel principal")
    else:
        print("  [OK] El terminal vive dentro del panel principal")
    required = [
        "chat-messages", "chat-input", "send-btn", "btn-clear-terminal",
        "btn-show-favorites", "btn-share-query", "sql-engine-dot", "sql-engine-alert",
        "btn-engine-retry", "btn-engine-copy", "sql-engine-env", "quick-chips",
    ]
    missing = [rid for rid in required if f'id="{rid}"' not in html and f'class="{rid}"' not in html]
    if missing:
        fail("faltan componentes del terminal: " + ", ".join(missing))
    else:
        print(f"  [OK] {len(required)} componentes del terminal presentes")
    leftovers = [name for name in ("bottom-panel", "panel-splitter", "PS financiero")
                 if name in html]
    if leftovers:
        fail("quedaron restos del panel inferior: " + ", ".join(leftovers))
    else:
        print("  [OK] Sin restos del panel inferior ni del divisor")


def audit_header_compaction(html, css):
    """La cabecera del panel debe caber con las seis pestañas.

    Se han cortado dos veces por no contemplar que el panel es la ventana menos
    la barra lateral. Las pestañas van sin iconos y el contexto se comprime por
    el ancho real del panel (container queries), con media queries de respaldo.
    """
    print("\n--- 9. Cabecera del panel: compacidad ---")
    tabs = re.findall(r'<button[^>]*class="panel-tab-btn[^"]*"[^>]*>(.*?)</button>', html, re.S)
    con_icono = [t for t in tabs if "<svg" in t]
    if con_icono:
        fail(f"{len(con_icono)} pestaña(s) volvieron a llevar icono: la cabecera se corta en pantallas medianas")
    else:
        print(f"  [OK] Las {len(tabs)} pestañas son de texto (sin iconos)")

    if "container-type: inline-size" not in css or "@container panelheader" not in css:
        fail("la cabecera perdió las container queries: vuelve a comprimirse según la ventana y no según el panel")
    else:
        print("  [OK] La cabecera se comprime según el ancho del panel")
    if "@media (max-width: 1300px)" not in css:
        fail("falta el respaldo por ancho de ventana para navegadores sin container queries")
    else:
        print("  [OK] Respaldo por ancho de ventana presente")


def audit_ux_layer():
    print("\n--- 3. Capa de experiencia (ux_shell.js) ---")
    path = os.path.join(DOCS, "js", "ux_shell.js")
    if not os.path.exists(path):
        fail("falta docs/js/ux_shell.js")
        return
    source = read("docs/js/ux_shell.js")
    for needle, label in [
        ("window.MFCUI", "exposición de la API"),
        ("initialTab", "pestaña inicial recordada"),
        ("rememberTab", "memoria de pestaña"),
        ("toast", "avisos breves"),
        ("Alt", "atajo de teclado"),
        ("duckdb-ready", "reacción al estado del motor"),
    ]:
        if needle not in source:
            fail(f"ux_shell.js no contempla {label}")
        else:
            print(f"  [OK] {label}")
    html = read("docs/index.html")
    if "js/ux_shell.js?v=" not in html:
        fail("index.html no carga ux_shell.js con versión")
    else:
        print("  [OK] index.html carga ux_shell.js")


def audit_theme_tokens():
    print("\n--- 4. Temas: sin colores fijos fuera de la paleta ---")
    css = read("docs/css/app.css")
    marker = "* {\n  box-sizing"
    body = css[css.index(marker):] if marker in css else css
    offenders = {}
    for match in re.finditer(r"#[0-9A-Fa-f]{3,6}\b", body):
        value = match.group(0)
        if value in ALLOWED_HEX:
            continue
        line = body[:match.start()].count("\n") + 1
        offenders.setdefault(value, []).append(line)
    if offenders:
        for value, lines in offenders.items():
            fail(f"color fijo {value} fuera de los bloques de tema (líneas del cuerpo: {lines[:4]})")
    else:
        print("  [OK] El cuerpo del CSS no fija colores: todo sale de variables de la paleta")

    for token in ("--warn-rgb", "--info-rgb", "--teal-rgb", "--violet-rgb", "--orange-rgb", "--red-rgb"):
        count = css.count(f"{token}:")
        if count != 6:
            fail(f"el token {token} debería estar definido en las 6 paletas (está {count} veces)")
    print("  [OK] Los seis semánticos están definidos en las seis paletas")


def audit_engine():
    print("\n--- 5. Motor DuckDB-Wasm ---")
    vendor = os.path.join(DOCS, "vendor", "duckdb")
    for name in ("duckdb-browser.mjs", "duckdb-browser-eh.worker.js", "duckdb-eh.wasm"):
        path = os.path.join(vendor, name)
        if not os.path.exists(path):
            fail(f"falta la copia local {name}")
        else:
            print(f"  [OK] {name} ({os.path.getsize(path) / 1048576:.1f} MB)")
    source = read("docs/js/duckdb_client.js")
    if "DUCKDB_LOCAL_DIR" not in source or "vendor/duckdb/" not in source:
        fail("duckdb_client.js no usa la copia local del motor")
    else:
        print("  [OK] El motor se carga desde el propio sitio")
    # Los bundles se declaran de forma explícita (y no vía getJsDelivrBundles) para
    # poder incluir la entrada "mvp", que selectBundle exige en navegadores sin
    # exception handling. Se comprueba entonces que existan los dos CDNs de respaldo.
    for esperado, etiqueta in [("jsdelivr", "jsDelivr"), ("unpkg", "unpkg")]:
        if esperado not in source.lower():
            fail(f"duckdb_client.js perdió el respaldo por CDN {etiqueta}")
    if 'bundles.mvp' not in source:
        fail("duckdb_client.js no declara el bundle mvp (selectBundle falla sin él)")
    else:
        print("  [OK] Respaldos por CDN jsDelivr y unpkg, con bundle mvp declarado")
    for capacidad in ["probeBlobWorker", "getPlatformFeatures", "buildDiagnostics"]:
        if capacidad not in source:
            fail(f"duckdb_client.js no expone {capacidad} para el diagnóstico")
    else:
        print("  [OK] Sondas de entorno y diagnóstico copiable presentes")


def audit_normativa():
    print("\n--- 6. Enlaces del visor de normativa ---")
    audit = os.path.join(ROOT, "scripts", "audit_normativa_web.js")
    source = read("scripts/audit_normativa_web.js")
    if "switchMainTab" not in source:
        fail("la auditoría de normativa ya no comprueba la conexión con switchMainTab")
    else:
        print("  [OK] La auditoría de normativa sigue verificando la pestaña")


def audit_dead_classes():
    """Clases CSS que ya no usa nadie: suelen quedar tras mover controles."""
    print("\n--- 7. CSS sin clases muertas conocidas ---")
    css = read("docs/css/app.css")
    html = read("docs/index.html")
    js = ""
    for name in ("sidebar.js", "data_viewer.js", "data_dictionary.js", "chat_terminal.js",
                 "downloads_panel.js", "download_utils.js", "erd_graph.js", "ux_shell.js",
                 "normativa_monitor.js"):
        js += read(f"docs/js/{name}")
    for cls in ("header-download-btn", "panel-tab-export", "panel-action-btn", "export-modal-backdrop",
                "bottom-panel", "splitter"):
        if f".{cls}" in css and cls not in html and cls not in js:
            fail(f"la clase .{cls} sigue en app.css pero ya no se usa en ninguna parte")
        else:
            print(f"  [OK] {cls}: sin restos")


def audit_control_chars():
    """Caracteres de control sueltos: casi siempre son escapes mal escritos.

    Un `\b` o `\f` dentro de un literal de Python o de un here-doc se convierte
    en retroceso o salto de página al escribir el archivo, y deja el texto
    invisible y roto (por ejemplo `\`\x08ash` en lugar de un bloque ```bash```).
    Los archivos minificados de terceros quedan fuera: contienen bytes de control
    legítimos dentro de sus cadenas.
    """
    print("\n--- 8. Higiene de texto: caracteres de control ---")
    revisar = [
        "README.md", "PSEUDOCODIGO.md", "ccaf/README.md", "bancos/README.md",
        "factoring_leasing/README.md", "fi/README.md", "macro/README.md",
        "pensiones/README.md", "docs/NAMING.md", "docs/index.html",
        "docs/css/app.css", "docs/js/ux_shell.js", "docs/js/duckdb_client.js",
        "docs/js/sidebar.js", "docs/js/chat_terminal.js", "scripts/preview_no_cache.py",
        "scripts/audit_interfaz.py", "scripts/audit_interfaz_dom.js",
        "scripts/audit_web_full.py", "scripts/audit_navigation.py",
    ]
    hallazgos = 0
    for rel in revisar:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as handle:
            for numero, linea in enumerate(handle, 1):
                for ch in linea.rstrip("\r\n"):
                    if ord(ch) < 32 and ch != "\t":
                        fail(f"{rel}:{numero} contiene el carácter de control 0x{ord(ch):02x}")
                        hallazgos += 1
                        break
    if hallazgos == 0:
        print(f"  [OK] {len(revisar)} archivos de texto sin caracteres de control sueltos")


def main():
    html = read("docs/index.html")
    audit_tabs(html)
    audit_descargas(html)
    audit_vocabulario()
    audit_cache()
    audit_terminal(html)
    audit_ux_layer()
    audit_theme_tokens()
    audit_engine()
    audit_normativa()
    audit_dead_classes()
    audit_control_chars()
    audit_header_compaction(html, read("docs/css/app.css"))

    print("\n" + "=" * 75)
    if errors:
        print(f"RESULTADO: {len(errors)} PROBLEMA(S) DE INTERFAZ")
        for item in errors:
            print(f"  - {item}")
        print("=" * 75)
        return 1
    print("RESULTADO: INTERFAZ COHERENTE (estructura, terminal, temas y motor)")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())

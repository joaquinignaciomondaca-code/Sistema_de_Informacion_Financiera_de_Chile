#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría estática de la interfaz web (Sistema de Información Financiera de Chile).

Comprueba, sin navegador ni red, las invariantes de estructura y de temas que el
rediseño del 2026-09-28 introdujo y que son fáciles de romper sin darse cuenta:

  1. index.html: siete pestañas con role="tab" —Información, Mapa, Diccionario, Visor,
     Consultas SQL, Descargas y Guía—, aria-controls apuntando a un id real y un
     único panel por pestaña.
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
import csv
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
    "tab-btn-guia": "guia-container",
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
    """Todos los archivos locales comparten una sola etiqueta de versión.

    Subirla es un paso manual y se olvidó una vez (2026-10-23: el mapa y las
    cifras nuevos quedaron publicados detrás de la etiqueta anterior, y quien
    hubiera entrado antes seguía viendo el JavaScript viejo). El chequeo vive en
    `scripts/subir_etiqueta.py --check`, que además dice cuál es la etiqueta y
    cuántos activos la llevan.
    """
    print("\n--- 1d. Caché de los archivos locales ---")
    check = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts/subir_etiqueta.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    salida = check.stdout.strip().splitlines()
    if check.returncode == 0:
        print(f"  [OK] {salida[-1]}")
        return
    for linea in salida:
        if "[FALLA]" in linea:
            fail(linea.strip())
    if not any("[FALLA]" in linea for linea in salida):
        fail("no se pudo comprobar la etiqueta de los activos")


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
    publicadas = len(re.findall(r'\{\s*name:\s*"[a-z0-9_]+"\s*,\s*(?:file|manifest):', read("docs/js/duckdb_client.js")))
    if len(tablas) != publicadas:
        fail(f"el vocabulario describe {len(tablas)} tablas y hay {publicadas} publicadas")

    # Toda lista de entidades de un sector se llama lista_entidades.
    listas = [t for t in tablas if t["tipo"].startswith("lista_entidades")]
    malas = [t["id"] for t in listas if not t["nombre"].endswith(t["tipo"])]
    if malas:
        fail(f"listas de entidades con otro nombre: {', '.join(malas)}")
    else:
        print(f"  [OK] {len(listas)} listas de entidades se llaman lista_entidades")

    # El título oficial puede repetirse cuando el registro tiene dos representaciones
    # deliberadas (completa y campos relevantes); la combinación título/tipo sí es única.
    claves = [(t["nombre"], t["tipo"]) for t in tablas]
    repetidos = sorted({clave for clave in claves if claves.count(clave) > 1})
    if repetidos:
        fail("tablas repetidas con el mismo título y tipo: " + ", ".join(f"{n} ({tipo})" for n, tipo in repetidos))

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
    """La cabecera del panel debe caber con las siete pestañas.

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


def audit_accesibilidad(html, css):
    print("\n--- 10. Teclado y movimiento: salto, foco y prefers-reduced-motion ---")
    if 'class="skip-link"' in html and 'href="#main-content"' in html:
        print("  [OK] enlace «Saltar al contenido principal»")
    else:
        fail("index.html no tiene el enlace de salto al contenido")
    destino = re.search(r'<main[^>]*id="main-content"[^>]*>', html)
    if destino and 'tabindex="-1"' in destino.group(0):
        print("  [OK] el destino del salto es enfocable (tabindex=-1)")
    else:
        fail("el <main> no tiene id=main-content con tabindex=-1")
    malas = []
    for m in re.finditer(r'([^{}]*:focus-visible[^{}]*)\{([^{}]*)\}', css):
        if re.search(r'outline:\s*none', m.group(2)):
            malas.append(" ".join(m.group(1).split()))
    if malas:
        fail("reglas :focus-visible que anulan el anillo de foco: " + "; ".join(malas))
    else:
        print("  [OK] ninguna regla :focus-visible anula el anillo de foco")
    if "prefers-reduced-motion: reduce" in css:
        print("  [OK] prefers-reduced-motion respetado")
    else:
        fail("app.css no respeta prefers-reduced-motion")
    if re.search(r"transition:\s*all\b", css):
        fail("app.css usa transition: all; hay que declarar qué propiedades cambian")
    else:
        print("  [OK] ninguna transición anima «all»")
    # Tablas ordenables: el control debe ser un botón dentro del <th>, con scope
    # y aria-sort, no un onclick sobre la celda de encabezado.
    for archivo in ("docs/js/data_viewer.js", "docs/js/chat_terminal.js"):
        fuente = read(archivo)
        if 'scope="col"' in fuente and "th-sort-btn" in fuente and "aria-sort" in fuente:
            print(f"  [OK] {archivo.split('/')[-1]}: encabezados ordenables con botón y aria-sort")
        else:
            fail(f"{archivo} no expone encabezados ordenables accesibles")
    # El esquema del mapa es un diálogo con nombre, cierre por Escape y retorno de foco.
    modal = re.search(r'<div class="schema-modal"[^>]*>', html)
    if modal and 'role="dialog"' in modal.group(0) and 'aria-labelledby="modal-table-name"' in modal.group(0):
        print("  [OK] el esquema del mapa es un diálogo con nombre")
    else:
        fail("el esquema del mapa no tiene role=dialog ni aria-labelledby")
    terminal = read("docs/js/chat_terminal.js")
    if "cerrarEsquema" in terminal and '"Escape"' in terminal and "__focoAntesDelEsquema" in terminal:
        print("  [OK] el esquema se cierra con Escape y devuelve el foco")
    else:
        fail("el esquema no cierra con Escape ni devuelve el foco")


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
    for esperado, etiqueta in [("jsdelivr", "jsDelivr"), ("esm.sh", "esm.sh")]:
        if esperado not in source.lower():
            fail(f"duckdb_client.js perdió el respaldo por CDN {etiqueta}")
    if 'bundles.mvp' not in source:
        fail("duckdb_client.js no declara el bundle mvp (selectBundle falla sin él)")
    else:
        print("  [OK] Respaldos por CDN jsDelivr y esm.sh, con bundle mvp declarado")
    # Los .mjs que upstream publica en dist/ importan "apache-arrow" como
    # especificador desnudo. Un navegador no lo resuelve sin import map, así que
    # un bundle vendorizado con imports desnudos deja la terminal SQL muerta en
    # producción aunque todos los archivos existan y se sirvan con HTTP 200.
    bundle_local = os.path.join(vendor, "duckdb-browser.mjs")
    if os.path.exists(bundle_local):
        desnudos = sorted(set(re.findall(r'from\s*["\']([^"\'./][^"\']*)["\']', read(bundle_local))))
        if desnudos:
            fail(
                "el bundle local del motor tiene imports sin resolver "
                f"({', '.join(desnudos)}): el navegador no puede cargarlo"
            )
        else:
            print("  [OK] El bundle local del motor es autocontenido (sin imports desnudos)")
    if "importmap" not in read("docs/index.html") and not os.path.exists(bundle_local):
        fail("sin bundle autocontenido ni import map, el motor no puede arrancar")
    for capacidad in ["probeBlobWorker", "getPlatformFeatures", "buildDiagnostics"]:
        if capacidad not in source:
            fail(f"duckdb_client.js no expone {capacidad} para el diagnóstico")
    else:
        print("  [OK] Sondas de entorno y diagnóstico copiable presentes")


def audit_normativa_retirada():
    """El monitor normativo salió de la navegación, pero su código se conserva.

    Se retiró de la interfaz (era otro producto: exigía revisión periódica y
    resúmenes que envejecen) sin borrar el módulo ni los datos, por si algún día
    vuelve como proyecto aparte. Esta auditoría cuida justamente esa frontera:
    que la pestaña no esté en la web, pero que el código siga en el repo.
    """
    print("\n--- 6. Monitor normativo fuera de la interfaz, código conservado ---")
    html = read("docs/index.html")
    shell = read("docs/js/ux_shell.js")
    if "tab-btn-normativa" in html or "normativa-container" in html:
        fail("la pestaña de normativa volvió al index.html")
    elif "normativa_monitor.js" in html:
        fail("index.html volvió a cargar normativa_monitor.js")
    elif '"normativa"' in shell:
        fail('ux_shell.js volvió a incluir "normativa" en sus pestañas válidas')
    else:
        print("  [OK] Ni la pestaña ni su script se cargan en la web")
    for pieza in ("docs/js/normativa_monitor.js", "scripts/audit_normativa_web.js"):
        if not os.path.exists(os.path.join(ROOT, pieza)):
            fail(f"se borró {pieza}: el monitor estaba retirado de la interfaz, no del repo")
        else:
            print(f"  [OK] {pieza} sigue en el repo")


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


def audit_cabeceras():
    """El despliegue declara cabeceras de seguridad y las dos copias coinciden."""
    print("\n--- 11. Cabeceras de seguridad del despliegue ---")
    try:
        raiz = read("vercel.json")
        docs = read("docs/vercel.json")
    except FileNotFoundError:
        fail("falta vercel.json (o su copia en docs/): el despliegue no declara cabeceras")
        return
    if raiz != docs:
        fail("vercel.json y docs/vercel.json difieren; el despliegue no es el mismo según la raíz")
    config = json.loads(raiz)
    reglas = config.get("headers", [])
    if not any(regla.get("source") == "/outputs/(.*).parquet" for regla in reglas):
        fail("vercel.json perdió la regla de caché de los Parquet")
    generales = {}
    for regla in reglas:
        if regla.get("source") == "/(.*)":
            for cabecera in regla.get("headers", []):
                generales[cabecera.get("key")] = cabecera.get("value")
    esperadas = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        "Cross-Origin-Opener-Policy": "same-origin",
    }
    for clave, valor in esperadas.items():
        if generales.get(clave) != valor:
            fail(f"vercel.json no declara {clave}: {valor}")
    politica = generales.get("Content-Security-Policy", "")
    for directiva in ("frame-ancestors 'none'", "object-src 'none'", "base-uri 'self'"):
        if directiva not in politica:
            fail(f"la CSP del despliegue no incluye {directiva}")
    if not any(clave not in generales for clave in esperadas) and all(d in politica for d in ("frame-ancestors 'none'", "object-src 'none'", "base-uri 'self'")):
        print(f"  [OK] {len(esperadas) + 1} cabeceras en las dos copias de vercel.json, con CSP mínima")
    # Decisión D1: GitHub Pages publica la API y Vercel la redirige. Si alguien
    # quita el redirect, Vercel serviría una copia con otro origen y la URL
    # canónica dejaría de ser única.
    API_CANONICA = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/api/"
    redirecciones = config.get("redirects") or []
    api = next((r for r in redirecciones if r.get("source") == "/api/(.*)"), None)
    if api is None:
        fail("vercel.json no redirige /api/* a la URL canónica (decisión D1)")
    elif not str(api.get("destination", "")).startswith(API_CANONICA):
        fail(f"el redirect de /api/* no apunta a Pages: {api.get('destination')}")
    elif api.get("permanent"):
        fail("el redirect de /api/* es permanente: quedaría cacheado en los clientes y no se podría revertir")
    else:
        print("  [OK] /api/* en Vercel redirige (307) a la URL canónica de Pages")


def audit_como_usar(html, css):
    """La sección «Cómo usar»: dos pestañas, dos audiencias, cero enlaces muertos."""
    print("\n--- 12. Cómo usar: pestañas de personas y de agentes ---")
    if 'id="guia-como-usar"' not in html:
        fail("index.html no tiene la sección «Cómo usar» (id=guia-como-usar)")
        return
    # El panel se delimita por el comentario que abre el siguiente, no por una
    # cuenta de </div>: el contenido tiene paneles anidados y la primera versión
    # de esta comprobación se cortaba a la mitad.
    inicio = html.find('id="guia-container"')
    fin = html.find("<!-- Descargas:", inicio)
    panel = html[inicio:fin] if (inicio != -1 and fin != -1) else ""
    faltan = [m for m in ('id="guia-como-usar"', 'id="creditos-guia"') if m not in panel]
    if faltan:
        fail(f"la pestaña Guía no contiene {', '.join(faltan)}")
    else:
        print("  [OK] la pestaña Guía contiene las instrucciones y los manuales")
    botones = []
    for etiqueta in re.findall(r'<button[^>]*data-uso-tab="([\w-]+)"[^>]*>', html):
        bloque = re.search(r'<button[^>]*data-uso-tab="' + re.escape(etiqueta) + r'"[^>]*>', html)
        controles = re.search(r'aria-controls="([\w-]+)"', bloque.group(0)) if bloque else None
        if controles:
            botones.append((etiqueta, controles.group(1)))
    if len(botones) != 2:
        fail(f"«Cómo usar» tiene {len(botones)} pestañas y se esperaban 2")
        return
    for etiqueta, panel in botones:
        if f'id="{panel}"' not in html:
            fail(f"la pestaña {etiqueta} apunta a un panel que no existe: {panel}")
        else:
            print(f"  [OK] pestaña {etiqueta} → {panel}")
    if "js/como_usar.js?v=" not in html:
        fail("index.html no carga js/como_usar.js con versión")
    else:
        print("  [OK] index.html carga como_usar.js con versión")
    for clave in ("191 tokens", "159", "sif-mcp"):
        if clave not in html:
            fail(f"«Cómo usar» no menciona «{clave}», que es lo que promete la entrega")
    for clase in (".uso-tabs", ".uso-tab", ".uso-panel", ".uso-code"):
        if clase not in css:
            fail(f"app.css no define {clase}, que usa la sección «Cómo usar»")
    print("  [OK] las clases de la sección existen en app.css")

    # El enlace directo (#como-usar-agentes) tiene que abrir la pestaña Guía, y
    # hacerlo en `load`: `switchMainTab` lo define un script en línea y el orden
    # respecto a los diferidos no está garantizado.
    guion = read("docs/js/como_usar.js")
    if 'window.addEventListener("load", entrar)' not in guion:
        fail("como_usar.js no espera a `load` para cambiar de pestaña: el enlace directo puede fallar")
    else:
        print("  [OK] el enlace directo abre la Guía al terminar la carga")


def audit_privacidad(html, css):
    """El aviso de privacidad se lee completo y habla de lo que sí se publica."""
    print("\n--- 13. Aviso de privacidad: desplazamiento y contenido ---")
    try:
        pagina = read("docs/privacidad.html")
    except FileNotFoundError:
        fail("falta docs/privacidad.html y el sitio lo enlaza desde index.html")
        return
    if 'href="privacidad.html"' not in html:
        fail("index.html no enlaza el aviso de privacidad")
    # app.css fija body{height:100vh;overflow:hidden} para la aplicación de una
    # sola pantalla. Si el aviso hereda esas dos reglas, la rueda del ratón no
    # desplaza y el documento queda cortado: tiene que revertirlas explícitamente.
    estilo = pagina.split("</style>")[0]
    if "overflow-y: auto" not in estilo or re.search(r"body\s*\{[^}]*(?<![\w-])height:\s*100vh", estilo):
        fail("privacidad.html no revierte el alto fijo y el desborde oculto de app.css: la página no se desplaza")
    elif "overflow: hidden" not in css:
        fail("app.css ya no esconde el desborde; revisar la regla de privacidad.html")
    else:
        print("  [OK] el aviso revierte el alto fijo del cuerpo y se puede desplazar")
    # El aviso describe lo publicado: los tres conjuntos con personas y el
    # tratamiento de identificadores, no una lista de lo que falta.
    for termino in ("fintech_rpsf_lista_entidades", "corredoras_bolsa_lista_entidades",
                    "seguros_bienes_raices", "rut_omitido_por_ley", "property_id"):
        if termino not in pagina:
            fail(f"el aviso de privacidad no menciona {termino}, que sí se publica")
    titulos = re.findall(r"<h2>(.*?)</h2>", pagina, re.S)
    negativos = [t for t in titulos if re.search(r"\bno\b", t, re.I)]
    if negativos:
        fail("el aviso de privacidad tiene secciones enunciadas por lo que no se publica: "
             + " · ".join(x.strip() for x in negativos))
    else:
        print(f"  [OK] el aviso enuncia sus {len(titulos)} secciones por el tratamiento que aplica")


def audit_alcance_publicado(html):
    """El alcance de la edición se cuenta por lo publicado, no por lo ausente."""
    print("\n--- 14. Alcance de la edición: sólo lo publicado ---")
    if 'id="info-alcance"' not in html:
        fail("index.html no tiene el bloque de alcance (id=info-alcance)")
        return
    inicio = html.find('id="info-alcance"')
    fin = html.find("</section>", inicio)
    bloque = html[inicio:fin] if inicio != -1 and fin != -1 else ""
    if not bloque:
        fail("el bloque de alcance no se pudo delimitar")
        return
    for frase in ("No incluye", "no se publica", "no se publicó", "queda fuera de esta edición"):
        if frase in bloque:
            fail(f"el alcance de la edición se enuncia por lo ausente («{frase}»)")
    h2 = re.search(r"<h2>(.*?)</h2>", bloque, re.S)
    if h2 and re.search(r"qué no|lo que no", h2.group(1), re.I):
        fail(f"el título del alcance habla de lo que no se publica: {h2.group(1).strip()}")
    sectores = set(re.findall(r"sector\.([a-z_]+)\.", bloque))
    incluye = set(re.findall(r"<strong>([^<]{3,60})</strong>", bloque))
    if len(incluye) < 5:
        fail("el alcance enumera menos de cinco grupos publicados")
    else:
        print(f"  [OK] el alcance describe {len(incluye)} grupos publicados y no nombra ausencias")


def audit_estado_claves(html, css):
    """El estado de clave llega a la web desde claves.csv, y cubre todo el catálogo."""
    print("\n--- 15. Estado de las claves en el Diccionario y el visor ---")
    if "js/estado_claves.js?v=" not in html:
        fail("index.html no carga js/estado_claves.js con versión")
        return
    ruta = os.path.join(ROOT, "docs/js/estado_claves.js")
    if not os.path.exists(ruta):
        fail("falta docs/js/estado_claves.js (genéralo con scripts/build_estado_claves.py)")
        return
    texto = open(ruta, encoding="utf-8").read()
    if "GENERADO por scripts/build_estado_claves.py" not in texto:
        fail("estado_claves.js no declara su origen; ¿se editó a mano?")
        return
    doc = json.loads(texto[texto.index("{"):texto.rindex(";")])
    objetos = doc["objetos"]
    resumen = doc["resumen"]
    if resumen["sin_verificar"]:
        fail(f"{resumen['sin_verificar']} objetos publicados sin verificación de clave")
    catalogo = json.loads(read("docs/api/v2/catalog.json"))
    ids = {o["id"] for o in catalogo["objetos"]}
    faltan = sorted(ids - set(objetos))
    if faltan:
        fail(f"el estado de claves no cubre {len(faltan)} objetos del catálogo: {', '.join(faltan[:5])}")
        return
    # De claves.csv se toman las claves primarias medidas; las tablas vacías no
    # tienen fila que medir y el catálogo las aporta como "sin datos".
    medidas = {
        f["objeto"]
        for f in csv.DictReader(open(os.path.join(ROOT, "docs/api/claves.csv"), encoding="utf-8"))
        if f["tipo"] == "pk" and f["estado"] != "sin_datos"
    }
    con_datos = {o for o, d in objetos.items() if d["estado"] != "sin_datos"}
    if medidas != con_datos:
        fail("los objetos de estado_claves.js no coinciden con las claves primarias de claves.csv")
        return
    print(f"  [OK] {len(objetos)} objetos con estado de clave, todos derivados de claves.csv")
    print(f"  [OK] {resumen['verificadas']} verificadas · {resumen['propuestas']} propuestas · "
          f"{resumen['sin_clave']} sin clave · {resumen['sin_datos']} sin datos")
    for clase in (".dict-key-box", ".dict-key-badge", ".scope-banner-claves"):
        if clase not in css:
            fail(f"falta el estilo {clase} en app.css")
    if 'avisoClaves' not in read("docs/js/data_dictionary.js"):
        fail("el Diccionario no pinta el estado de la clave")
    if 'avisoClaves' not in read("docs/js/data_viewer.js"):
        fail("el visor no avisa de las filas repetidas")
    print("  [OK] Diccionario y visor muestran el estado con sus estilos")


def audit_vitrina(html):
    """La portada se puede compartir y rastrear: metadatos, robots y sitemap."""
    print("\n--- 16. Vitrina: metadatos sociales, robots y sitemap ---")
    requeridas = {
        'name="description"': "falta la meta description",
        'rel="canonical"': "falta el canonical",
        'property="og:title"': "falta og:title",
        'property="og:description"': "falta og:description",
        'property="og:url"': "falta og:url",
        'property="og:image"': "falta og:image",
        'property="og:image:width" content="1200"': "el og:image no declara 1200 de ancho",
        'property="og:image:height" content="630"': "el og:image no declara 630 de alto",
        'property="og:image:alt"': "falta el texto alternativo del og:image",
        'name="twitter:card" content="summary_large_image"': "falta twitter:card",
        'name="twitter:image"': "falta twitter:image",
    }
    for marca, error in requeridas.items():
        if marca not in html:
            fail(error)
    if "SEO:INICIO" not in html:
        fail("el bloque de metadatos no lleva la marca de generado (SEO:INICIO)")
    # Una sola descripción y un solo canonical: duplicarlos los vuelve ambiguos.
    for etiqueta in ("name=\"description\"", 'rel="canonical"'):
        if html.count(etiqueta) != 1:
            fail(f"{etiqueta} aparece {html.count(etiqueta)} veces y debe aparecer una")

    imagen = os.path.join(ROOT, "docs/assets/og_sif_1200x630.png")
    if not os.path.exists(imagen):
        fail("falta assets/og_sif_1200x630.png (genérala con scripts/build_og_image.py)")
    else:
        with open(imagen, "rb") as fh:
            cabecera = fh.read(33)
        if cabecera[:8] != b"\x89PNG\r\n\x1a\n":
            fail("og:image no es un PNG")
        else:
            ancho = int.from_bytes(cabecera[16:20], "big")
            alto = int.from_bytes(cabecera[20:24], "big")
            if (ancho, alto) != (1200, 630):
                fail(f"og:image mide {ancho}×{alto} y debe medir 1200×630")
            else:
                peso = os.path.getsize(imagen) // 1024
                print(f"  [OK] og:image es un PNG de {ancho}×{alto} ({peso} KB)")

    for nombre in ("robots.txt", "sitemap.xml"):
        ruta = os.path.join(ROOT, "docs", nombre)
        if not os.path.exists(ruta):
            fail(f"falta docs/{nombre}")
    robots = read("docs/robots.txt") if os.path.exists(os.path.join(ROOT, "docs/robots.txt")) else ""
    if "Sitemap:" not in robots:
        fail("robots.txt no apunta al sitemap")
    sitemap = read("docs/sitemap.xml") if os.path.exists(os.path.join(ROOT, "docs/sitemap.xml")) else ""
    if "<urlset" not in sitemap or "/privacidad.html" not in sitemap:
        fail("sitemap.xml no declara las dos páginas del sitio")
    if not errors:
        print("  [OK] metadatos sociales completos, robots.txt y sitemap.xml con las dos páginas")


def main():
    html = read("docs/index.html")
    audit_tabs(html)
    audit_descargas(html)
    audit_vocabulario()
    audit_cache()
    audit_terminal(html)
    audit_ux_layer()
    audit_theme_tokens()
    audit_accesibilidad(html, read("docs/css/app.css"))
    audit_engine()
    audit_normativa_retirada()
    audit_dead_classes()
    audit_control_chars()
    audit_header_compaction(html, read("docs/css/app.css"))
    audit_cabeceras()
    audit_como_usar(html, read("docs/css/app.css"))
    audit_privacidad(html, read("docs/css/app.css"))
    audit_alcance_publicado(html)
    audit_estado_claves(html, read("docs/css/app.css"))
    audit_vitrina(html)

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

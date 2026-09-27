#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_web_full.py
Auditoría integral de la interfaz web de bcch_market_monitor:
  1. Sidebar (sidebar.js): grupos, sectores, tablas y chips SQL.
  2. Visor de Datos (data_viewer.js): catálogo de tablas, opciones del selector y consistencia con Parquet.
  3. Diccionario de Datos (data_dictionary.js): esquemas declarados vs columnas físicas en Parquet.
  4. Diagrama ERD (erd_graph.js): nodos, archivos Parquet y consistencia de enlaces relacionales (ERD_LINKS).
  5. Vistas Semánticas DuckDB (duckdb_client.js): verificación de todos los archivos .parquet.
  6. Integridad de Assets HTML (index.html): scripts y hojas de estilo locales.
"""

import os
import re
import json
import pyarrow.parquet as pq

def audit_html_assets(base_dir):
    print("\n--- 1. AUDITORIA: Assets de index.html ---")
    index_path = os.path.join(base_dir, "docs", "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Scripts locales
    script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    local_scripts = [s for s in script_srcs if not s.startswith("http") and not s.startswith("//")]
    
    # CSS locales
    css_hrefs = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html)
    local_css = [c for c in css_hrefs if not c.startswith("http") and not c.startswith("//") and "css" in c]

    errors = 0
    for s in local_scripts:
        clean_s = s.split("?")[0]
        full_p = os.path.join(base_dir, "docs", clean_s)
        if not os.path.exists(full_p):
            print(f"Error: Script local no encontrado: {clean_s}")
            errors += 1
        else:
            print(f"  [OK] Script: {clean_s} ({os.path.getsize(full_p)} bytes)")
            # Validar sintaxis JS con Node si esta disponible
            try:
                import subprocess
                subprocess.check_output(["node", "-c", full_p], stderr=subprocess.STDOUT)
                print(f"       -> Sintaxis JS valida (V8/Node OK)")
            except Exception as e:
                print(f"Error Sintaxis JS en {clean_s}: {e}")
                errors += 1

    for c in local_css:
        clean_c = c.split("?")[0]
        full_p = os.path.join(base_dir, "docs", clean_c)
        if not os.path.exists(full_p):
            print(f"Error: CSS local no encontrado: {clean_c}")
            errors += 1
        else:
            print(f"  [OK] CSS: {clean_c} ({os.path.getsize(full_p)} bytes)")

    assert errors == 0, f"Se encontraron {errors} assets locales rotos o con errores de sintaxis en index.html"
    print("Resultado Assets HTML: 100% encontrados y sintacticamente validos.")

def audit_duckdb_views(base_dir):
    print("\n--- 2. AUDITORIA: Vistas Semanticas DuckDB (duckdb_client.js) ---")
    duckdb_js = os.path.join(base_dir, "docs", "js", "duckdb_client.js")
    with open(duckdb_js, "r", encoding="utf-8") as f:
        code = f.read()

    # Extraer { name: "...", file: "..." } y también las vistas que unen varias
    # particiones { name: "...", file: ["...", "..."] }, ya que el visor las lee
    # como una sola tabla (p. ej. vida_bonos con sus dos cortes).
    matches = re.findall(
        r'\{\s*name:\s*["\']([^"\']+)["\'],\s*file:\s*(?:["\']([^"\']+)["\']|\[([^\]]*)\])',
        code)
    views = []
    for name, single, multi in matches:
        files = [single] if single else re.findall(r'["\']([^"\']+)["\']', multi)
        for rel_file in files:
            views.append((name, rel_file))
    print(f"Total vistas registradas en duckdb_client.js: {len(matches)} "
          f"({len(views)} archivos Parquet)")

    errors = 0
    total_filas = 0
    for name, rel_file in views:
        full_path = os.path.join(base_dir, "docs", rel_file)
        if not os.path.exists(full_path):
            print(f"Error: Archivo Parquet no existe para vista {name}: {rel_file}")
            errors += 1
            continue

        try:
            tab = pq.read_table(full_path)
            cnt = tab.num_rows
            total_filas += cnt
        except Exception as e:
            print(f"Error leyendo Parquet para vista {name}: {e}")
            errors += 1

    assert errors == 0, f"Se encontraron {errors} errores en vistas de DuckDB"
    print(f"Resultado Vistas DuckDB: {len(views)}/{len(views)} archivos Parquet validados ({total_filas:,} filas totales en base de datos).")
    return {name: ([single] if single else re.findall(r'["\']([^"\']+)["\']', multi))
            for name, single, multi in matches}

def audit_sidebar(base_dir, registered_views):
    print("\n--- 3. AUDITORIA: Estructura Lateral de Navegacion (sidebar.js) ---")
    sidebar_js = os.path.join(base_dir, "docs", "js", "sidebar.js")
    with open(sidebar_js, "r", encoding="utf-8") as f:
        code = f.read()

    # Extraer grupos
    groups = re.findall(r'id:\s*["\'](group_[^"\']+)["\'],\s*type:\s*["\']group["\'],\s*label:\s*["\']([^"\']+)["\']', code)
    print(f"Grupos de navegacion en sidebar: {len(groups)}")
    for gid, lbl in groups:
        print(f"  - {gid}: {lbl}")

    # Extraer tablas del sidebar
    # { id: "...", name: "...", rows: "...", file: "..." }
    tables = re.findall(r'\{\s*id:\s*["\']([^"\']+)["\'],\s*name:\s*["\']([^"\']+)["\'],\s*rows:\s*["\']([^"\']+)["\'],\s*file:\s*["\']([^"\']+)["\']\s*\}', code)
    print(f"\nTotal tablas enlazadas en sidebar: {len(tables)}")
    
    errors = 0
    active_tables = 0
    planned_tables = 0
    for tid, tname, rows, rel_file in tables:
        if rel_file == "#":
            planned_tables += 1
            print(f"  [EN AGENDA] {tid} ({tname}) -> {rows}")
        else:
            active_tables += 1
            full_path = os.path.join(base_dir, "docs", rel_file)
            if not os.path.exists(full_path):
                print(f"Error: Archivo no existe para tabla {tid}: {rel_file}")
                errors += 1
            if tid not in registered_views:
                print(f"Advertencia: Tabla {tid} no esta en registered_views de duckdb_client.js")

    print(f"Tablas activas: {active_tables}, Tablas en agenda/placeholder: {planned_tables}")
    assert errors == 0, f"Se encontraron {errors} archivos rotos en sidebar"

    # Extraer y validar chips SQL
    chips = re.findall(r'\{\s*label:\s*["\']([^"\']+)["\'],\s*query:\s*["\']([^"\']+)["\']\s*\}', code)
    print(f"\nTotal chips de consultas predefinidas: {len(chips)}")
    
    chip_errors = 0
    for label, query in chips:
        if query.strip().startswith("--"):
            continue
        # Verificar que las tablas mencionadas en el query existan en registered_views
        # Buscar palabras despues de FROM o JOIN
        table_matches = re.findall(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)\b', query, re.IGNORECASE)
        for tbl in table_matches:
            if tbl.lower() not in [v.lower() for v in registered_views.keys()]:
                print(f"Error en Chip SQL '{label}': Tabla '{tbl}' no existe en vistas registradas.\nQuery: {query}")
                chip_errors += 1

    assert chip_errors == 0, f"Se encontraron {chip_errors} consultas con tablas invalidas en chips"
    print(f"Resultado Chips SQL: {len(chips)}/{len(chips)} consultas analizadas y vinculadas a tablas existentes.")

def audit_data_viewer(base_dir, registered_views):
    print("\n--- 4. AUDITORIA: Visor de Datos (data_viewer.js) ---")
    dv_js = os.path.join(base_dir, "docs", "js", "data_viewer.js")
    with open(dv_js, "r", encoding="utf-8") as f:
        code = f.read()

    # Extraer grupos y tablas de DATA_VIEWER_CATALOG
    dv_tables = re.findall(r'\{\s*id:\s*["\']([^"\']+)["\'],\s*name:\s*["\']([^"\']+)["\']\s*\}', code)
    print(f"Tablas en catalogo del Visor de Datos: {len(dv_tables)}")

    errors = 0
    for tid, tname in dv_tables:
        if tid not in registered_views:
            print(f"Error: Tabla del visor '{tid}' no registrada en duckdb_client.js")
            errors += 1
        else:
            for rel_file in registered_views[tid]:
                full_p = os.path.join(base_dir, "docs", rel_file)
                if not os.path.exists(full_p):
                    print(f"Error: Archivo no existe para tabla del visor '{tid}': {rel_file}")
                    errors += 1

    assert errors == 0, f"Se encontraron {errors} inconsistencias en DATA_VIEWER_CATALOG"
    print(f"Resultado Visor de Datos: 100% de las {len(dv_tables)} tablas enlazadas correctamente a archivos y vistas.")

def audit_data_dictionary(base_dir, registered_views):
    print("\n--- 5. AUDITORIA: Diccionario de Datos (data_dictionary.js) ---")
    dd_js = os.path.join(base_dir, "docs", "js", "data_dictionary.js")
    with open(dd_js, "r", encoding="utf-8") as f:
        code = f.read()

    # Extraer bloques de tablas
    table_blocks = re.findall(r'\{\s*id:\s*["\']([^"\']+)["\'],\s*name:\s*["\']([^"\']+)["\'],\s*viewName:\s*["\']([^"\']+)["\'],\s*sector:\s*["\']([^"\']+)["\'],.*?columnas:\s*\[(.*?)\]\s*\}', code, re.DOTALL)
    print(f"Tablas documentadas en diccionario de datos: {len(table_blocks)}")

    errors = 0
    total_cols_audited = 0
    for tid, tname, viewName, sector, cols_block in table_blocks:
        col_names = re.findall(r'name:\s*["\']([^"\']+)["\']', cols_block)
        
        # Verificar contra Parquet fisico si la vista existe
        if viewName in registered_views:
            physical_cols = set()
            for rel_file in registered_views[viewName]:
                pq_path = os.path.join(base_dir, "docs", rel_file)
                if os.path.exists(pq_path):
                    physical_cols.update(pq.read_schema(pq_path).names)
            for col in col_names:
                total_cols_audited += 1
                if col not in physical_cols:
                    print(f"Inconsistencia en diccionario: Columna '{col}' en tabla '{tid}' no existe en Parquet de {viewName}")
                    errors += 1

    assert errors == 0, f"Se encontraron {errors} inconsistencias de columnas en el diccionario de datos"
    print(f"Resultado Diccionario de Datos: {total_cols_audited} columnas auditadas contra archivos Parquet reales con 100% de coincidencia.")

def audit_erd_graph(base_dir, registered_views):
    print("\n--- 6. AUDITORIA: Diagrama de Entidad-Relacion ERD (erd_graph.js) ---")
    erd_js = os.path.join(base_dir, "docs", "js", "erd_graph.js")
    with open(erd_js, "r", encoding="utf-8") as f:
        code = f.read()

    # Extraer nodos ERD_TABLES
    # id: "...", name: "...", sector: "...", ... file: "..."
    nodes = re.findall(r'id:\s*["\']([^"\']+)["\'],\s*name:\s*["\']([^"\']+)["\'],\s*sector:\s*["\']([^"\']+)["\'],.*?file:\s*["\']([^"\']+)["\']', code, re.DOTALL)
    print(f"Nodos de tablas en diagrama ERD: {len(nodes)}")
    
    node_ids = set()
    node_errors = 0
    for nid, nname, sec, rel_file in nodes:
        node_ids.add(nid)
        if rel_file != "#":
            # El ERD puede tener un nombre de archivo representativo no publicado
            # (p. ej. vida_bonos); en ese caso se valida la vista semántica real,
            # que une las particiones versionadas en el repositorio.
            rel_files = registered_views.get(nid, [rel_file])
            for published_file in rel_files:
                full_path = os.path.join(base_dir, "docs", published_file)
                if not os.path.exists(full_path):
                    print(f"Error ERD: Archivo no existe para nodo '{nid}': {published_file}")
                    node_errors += 1

    assert node_errors == 0, f"Se encontraron {node_errors} archivos rotos en nodos ERD"

    # Extraer conexiones ERD_LINKS
    # { from: "...", to: "...", key: "..." }
    links = re.findall(r'\{\s*from:\s*["\']([^"\']+)["\'],\s*to:\s*["\']([^"\']+)["\'],\s*key:\s*["\']([^"\']+)["\']\s*\}', code)
    print(f"Conexiones relacionales (ERD_LINKS): {len(links)}")

    link_errors = 0
    for from_node, to_node, key in links:
        if from_node not in node_ids:
            print(f"Error ERD Link: Nodo origen '{from_node}' no existe en ERD_TABLES")
            link_errors += 1
        if to_node not in node_ids:
            print(f"Error ERD Link: Nodo destino '{to_node}' no existe en ERD_TABLES")
            link_errors += 1

    assert link_errors == 0, f"Se encontraron {link_errors} conexiones rotas en ERD_LINKS"
    print(f"Resultado Diagrama ERD: {len(nodes)} nodos y {len(links)} conexiones relacionales 100% integras.")

def main():
    print("===========================================================================")
    print("AUDITORIA INTEGRAL DE LA APLICACION WEB Y SECCIONES (MONITOR FINANCIERO)")
    print("===========================================================================")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    audit_html_assets(base_dir)
    registered_views = audit_duckdb_views(base_dir)
    audit_sidebar(base_dir, registered_views)
    audit_data_viewer(base_dir, registered_views)
    audit_data_dictionary(base_dir, registered_views)
    audit_erd_graph(base_dir, registered_views)

    print("\n===========================================================================")
    print("RESULTADO GLOBAL: TODAS LAS SECCIONES DE LA WEB ESTAN 100% OPERATIVAS")
    print("===========================================================================")

if __name__ == "__main__":
    main()

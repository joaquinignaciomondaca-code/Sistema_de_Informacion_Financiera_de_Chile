#!/usr/bin/env python3
"""Publica en docs/ la serie IFRS FL solo cuando el índice completo está local.

El workflow primero completa el backfill en .local-data, luego este script arma
Parquets únicos de balance y resultados y actualiza los catálogos de la web.
Nunca resume/suma cuentas, convierte unidades, elimina repeticiones ni rellena
importes no enteros. El commit/push lo realiza el workflow a la misma rama.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipelines.auto.rut import normalizar_dataframe  # noqa: E402

DATA = ROOT / '.local-data' / 'factoring_leasing_serie'
DOCS = ROOT / 'docs'
OUT = DOCS / 'outputs' / 'factoring_leasing'
BALANCE = 'factoring_leasing_balance_serie_ifrs_cmf'
RESULTS = 'factoring_leasing_resultados_serie_ifrs_cmf'
MARKERS = {
    'docs/js/duckdb_client.js': ('// BEGIN AUTO FL IFRS SERIES VIEWS', '// END AUTO FL IFRS SERIES VIEWS'),
    'docs/js/sidebar.js': ('// BEGIN AUTO FL IFRS SERIES NAVIGATION', '// END AUTO FL IFRS SERIES NAVIGATION'),
    'docs/js/data_viewer.js': ('// BEGIN AUTO FL IFRS SERIES VIEWER', '// END AUTO FL IFRS SERIES VIEWER'),
    'docs/js/data_dictionary.js': ('// BEGIN AUTO FL IFRS SERIES DICTIONARY', '// END AUTO FL IFRS SERIES DICTIONARY'),
}
# Esquema del STAGING (igual a COLUMNS de backfill_ifrs.py); la publicación
# aplica la convención de RUT en atomic_parquet y queda documentada en DOC_COLUMNS.
TABLE_COLUMNS = [
    ('periodo', 'VARCHAR', 'Cierre informado por CMF, AAAA-MM.'),
    ('rut_cuerpo', 'VARCHAR', 'Cuerpo del RUT que aparece en el TXT; el archivo no trae dígito verificador.'),
    ('rut', 'VARCHAR', 'RUT actual del catálogo asociado al cuerpo; el vínculo histórico requiere auditoría independiente.'),
    ('nombre_reportado', 'VARCHAR', 'Razón social declarada en la fila fuente de este período.'),
    ('segmento_catalogo', 'VARCHAR', 'Segmento consignado en el catálogo actual; puede incluir entidades mixtas/automotrices.'),
    ('nombre_catalogo', 'VARCHAR', 'Razón social del catálogo local actual; no reemplaza al nombre reportado históricamente.'),
    ('tipo_balance', 'VARCHAR', 'I individual o C consolidado, literal del archivo CMF; no sumar contextos.'),
    ('moneda_archivo', 'VARCHAR', 'Moneda literal CMF; sin conversión FX ni homogeneización.'),
    ('cuenta', 'VARCHAR', 'Etiqueta literal de la cuenta en el TXT IFRS CMF.'),
    ('valor_archivo', 'BIGINT', 'Importe entero literal del TXT cuando es entero; NULL si el original no se interpreta como entero.'),
    ('valor_texto_original', 'VARCHAR', 'Valor literal del TXT, preservado incluso si valor_archivo es NULL.'),
    ('valor_es_entero', 'BOOLEAN', 'Indica si el valor original se pudo interpretar como entero sin transformación.'),
    ('taxonomia', 'VARCHAR', 'Taxonomía literal CMF, por ejemplo TAX CI/HB/HS.'),
    ('estado_financiero', 'VARCHAR', 'Tipo de estado CMF: ESF* para balance; ER* para resultados.'),
    ('repeticion_contexto', 'BIGINT', 'Ordinal de repetición dentro de la misma clave/contexto. No se deduplican ni suman.'),
    ('fuente_archivo', 'VARCHAR', 'URL de descarga; 2009-03 usa archivo anual CMF filtrado al trimestre.'),
    ('sha256_archivo', 'VARCHAR', 'SHA-256 de la respuesta de descarga o del subconjunto anual filtrado.'),
    ('identidad_nombre_coincide_catalogo', 'BOOLEAN', 'Coincidencia textual normalizada entre nombre fuente y nombre actual; no certifica identidad histórica.'),
]
# Esquema publicado tras normalizar (convención de RUT, pipelines/auto/rut.py):
# `rut` = cuerpo, `rut_dv` = con DV, sin `rut_cuerpo`.
DOC_COLUMNS = [
    ('periodo', 'VARCHAR'),
    ('rut', 'VARCHAR'),
    ('nombre_reportado', 'VARCHAR'),
    ('segmento_catalogo', 'VARCHAR'),
    ('nombre_catalogo', 'VARCHAR'),
    ('tipo_balance', 'VARCHAR'),
    ('moneda_archivo', 'VARCHAR'),
    ('cuenta', 'VARCHAR'),
    ('valor_archivo', 'BIGINT'),
    ('valor_texto_original', 'VARCHAR'),
    ('valor_es_entero', 'BOOLEAN'),
    ('taxonomia', 'VARCHAR'),
    ('estado_financiero', 'VARCHAR'),
    ('repeticion_contexto', 'BIGINT'),
    ('fuente_archivo', 'VARCHAR'),
    ('sha256_archivo', 'VARCHAR'),
    ('identidad_nombre_coincide_catalogo', 'BOOLEAN'),
    ('rut_dv', 'VARCHAR'),
]


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_parquet(frame, path):
    # Convención de RUT (pipelines/auto/rut.py): `rut` = cuerpo, `rut_dv` = con DV.
    frame = normalizar_dataframe(frame)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.parquet', delete=False) as tmp:
        temp = Path(tmp.name)
    try:
        frame.to_parquet(temp, index=False)
        check = pd.read_parquet(temp)
        if len(check) != len(frame) or list(check.columns) != list(frame.columns):
            raise ValueError(f'Roundtrip Parquet/schema no coincide: {path.name}')
        if len(frame) and check['valor_texto_original'].tolist() != frame['valor_texto_original'].tolist():
            raise ValueError(f'Roundtrip no conserva el importe literal: {path.name}')
        if path.is_file() and file_sha256(path) == file_sha256(temp):
            temp.unlink()
        else:
            temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def replace_block(text, start, end, content, path):
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f'Markers ausentes/duplicados en {path}')
    a = text.index(start) + len(start)
    b = text.index(end)
    if b < a:
        raise ValueError(f'Markers invertidos en {path}')
    return text[:a] + '\n' + content.rstrip() + '\n  ' + text[b:]


def js(value):
    return json.dumps(value, ensure_ascii=False).replace('</', '<\\/')


def query(name):
    return (f'SELECT periodo, rut, nombre_reportado, tipo_balance, moneda_archivo, cuenta, '
            f'valor_archivo, valor_texto_original, valor_es_entero, taxonomia, '
            f'estado_financiero, repeticion_contexto FROM {name} '
            'ORDER BY periodo DESC, rut, tipo_balance, estado_financiero, cuenta LIMIT 500;')


# En los resultados IFRS la etiqueta "Ganancia (pérdida)" aparece hasta 3 veces por estado, siempre
# con el mismo valor: en ERFG/ERNG tras operaciones continuadas (repeticion_contexto = 1) y otra vez
# como total de la atribución controladora/no controladora (= 2); y en ERI como línea inicial del
# resultado integral. Sumarla sin filtrar triplica la utilidad. Se conserva literal (no se deduplica)
# y se entregan consultas que eligen una sola fila por estado.
PROFIT_LABEL = 'ganancia (pérdida)'


def profit_queries(name):
    return [
        ('Utilidad del período · 1 fila por estado',
         f"SELECT periodo, rut, nombre_reportado, tipo_balance, estado_financiero, valor_archivo AS ganancia_perdida "
         f"FROM {name} WHERE lower(cuenta) = '{PROFIT_LABEL}' AND estado_financiero IN ('ERFG', 'ERNG') "
         "AND repeticion_contexto = 1 ORDER BY periodo DESC, rut;"),
        ("Dónde se repite 'Ganancia (pérdida)'",
         f"SELECT estado_financiero, repeticion_contexto, count(*) AS filas, count(DISTINCT (periodo, rut, tipo_balance)) AS estados "
         f"FROM {name} WHERE lower(cuenta) = '{PROFIT_LABEL}' GROUP BY ALL ORDER BY estado_financiero, repeticion_contexto;"),
    ]


def sidebar_block(meta):
    period = f"{meta['primer_periodo'][:4]}-{meta['primer_periodo'][4:]}–{meta['ultimo_periodo'][:4]}-{meta['ultimo_periodo'][4:]}"
    badge = f"{meta['periodos_indice']} cierres · {len(meta['ruts_con_datos_total'])} RUT"
    entries = []
    for cid, label, table_id, table_name, rows, file, sql_label in [
        ('fl_balance_serie_ifrs_cmf_folder', f'Balance · Serie CMF ({period})', BALANCE,
         'factoring_leasing.balance_serie_ifrs_cmf', meta['filas_balance_total'],
         f'outputs/factoring_leasing/{BALANCE}.parquet', 'Cuentas de balance CMF'),
        ('fl_resultados_serie_ifrs_cmf_folder', f'Resultados · Serie CMF ({period})', RESULTS,
         'factoring_leasing.resultados_serie_ifrs_cmf', meta['filas_resultados_total'],
         f'outputs/factoring_leasing/{RESULTS}.parquet', 'Cuentas de resultados CMF')]:
        chip_list = [(sql_label + ' · primeros 500', query(table_id))]
        if table_id == RESULTS:
            chip_list += profit_queries(table_id)
        chips = ',\n                    '.join(f'{{ label: {js(lbl)}, query: {js(sql)} }}' for lbl, sql in chip_list)
        entries.append(f'''          {{
            id: "{cid}", type: "circular",
            label: {js(label)}, badge: {js(badge)}, badgeType: "data", status: "active",
            sector: "factoring_leasing",
            chips: [{chips}],
            tables: [{{ id: "{table_id}", name: {js(f'{table_name} ({rows:,} cuentas; no cotejo integral)')},
                       rows: {js(f'{rows:,} cuentas · {meta["periodos_indice"]} cierres · extracción sin cotejo integral')},
                       file: {js(file)} }}]
          }},''')
    return '\n'.join(entries)


def viewer_block(meta):
    balance_name = f"factoring_leasing.balance_serie_ifrs_cmf ({meta['filas_balance_total']:,} cuentas; no cotejo integral)"
    results_name = f"factoring_leasing.resultados_serie_ifrs_cmf ({meta['filas_resultados_total']:,} cuentas; no cotejo integral)"
    return '\n'.join([
        f'      {{ id: "{BALANCE}", name: {js(balance_name)} }},',
        f'      {{ id: "{RESULTS}", name: {js(results_name)} }},',
    ])


def duckdb_block():
    return '\n'.join([
        f'  {{ name: "{BALANCE}", file: "outputs/factoring_leasing/{BALANCE}.parquet" }},',
        f'  {{ name: "{RESULTS}", file: "outputs/factoring_leasing/{RESULTS}.parquet" }},',
    ])


def dictionary_block(meta, run_id):
    descriptions = {
        'rut': 'Cuerpo del RUT actual del catálogo (sin DV); la unión es por cuerpo y no certifica vigencia ni identidad histórica.',
        'rut_dv': 'RUT del catálogo con dígito verificador (cuerpo-DV).',
        'nombre_reportado': 'Nombre reportado por CMF en ese período.',
        'nombre_catalogo': 'Nombre del catálogo actual; puede diferir del nombre histórico.',
        'tipo_balance': 'I individual / C consolidado. Se preservan separados; no sumar.',
        'moneda_archivo': 'Moneda original, sin conversión.',
        'cuenta': 'Etiqueta literal de cuenta reportada.',
        'valor_archivo': 'Entero original cuando pudo leerse como entero; NULL para valores no enteros.',
        'valor_texto_original': 'Texto literal de la cifra, preservado siempre.',
        'valor_es_entero': 'Control de interpretación numérica; false no significa cero.',
        'taxonomia': 'Código literal de taxonomía CMF.',
        'estado_financiero': ('Código CMF del estado: ESF C/NC = situación financiera; ERFG = resultados por función; '
                              'ERNG = resultados por naturaleza; ERI = resultado integral.'),
        'repeticion_contexto': ('Ordinal de la misma etiqueta dentro del estado; se conserva sin sumar. En resultados, '
                                '"Ganancia (pérdida)" aparece en ERFG/ERNG con ordinal 1 y 2 y otra vez al inicio de ERI, '
                                'con el mismo valor: para la utilidad del período usar estado ERFG/ERNG y ordinal 1.'),
        'fuente_archivo': 'URL pública CMF que originó la fila.',
        'sha256_archivo': 'Huella de la descarga usada.',
        'identidad_nombre_coincide_catalogo': 'Coincidencia de nombre normalizada; señal, no auditoría histórica.',
    }
    stage_desc = {name: desc for name, _typ, desc in TABLE_COLUMNS}
    columns = []
    for name, typ in DOC_COLUMNS:
        columns.append({'name': name, 'type': typ, 'role': 'Métrica' if name in ('valor_archivo', 'valor_texto_original') else 'Dimensión',
                        'significado': descriptions.get(name, stage_desc.get(name, '')), 'contable': 'No aplica'})
    created = meta['fecha_actualizacion_utc'][:10]
    period_range = f"{meta['primer_periodo'][:4]}-{meta['primer_periodo'][4:]} a {meta['ultimo_periodo'][:4]}-{meta['ultimo_periodo'][4:]}"
    common = {
        'sector': 'factoring_leasing', 'sectorLabel': 'Factoring & Leasing',
        'norma': 'CMF IFRS TXT · extracción automática de cuentas ESF/ER',
        'corte': f"{period_range} · {meta['periodos_indice']} cierres",
        'frescura': 'Serie de la fuente CMF; valores crudos, no validación integral',
        'modo': 'Actions: descarga histórica incremental y publicación automática al completarse',
        'ultimaActualizacion': created,
        'origen': f"CMF {meta['fuente_indice']}; corrida Actions {run_id}. 24/28 RUT de catálogo presentes. Incluye cuentas repetidas y valores no enteros; no convertir, deduplicar ni sumar sin criterio. No cotejo integral de estados.",
        'columnas': columns,
    }
    objects = []
    for table_id, view_name, title, rows, statement in [
        (BALANCE, BALANCE, 'Balance IFRS CMF · serie histórica', meta['filas_balance_total'], 'ESF'),
        (RESULTS, RESULTS, 'Resultados IFRS CMF · serie histórica', meta['filas_resultados_total'], 'ER'),
    ]:
        item = dict(common)
        item.update({
            'id': table_id, 'name': 'factoring_leasing.' + table_id.removeprefix('factoring_leasing_'), 'viewName': view_name,
            'registros': f"{rows:,} cuentas · {len(meta['ruts_con_datos_total'])}/28 RUT con datos",
            'descripcion': (f"{title}. {rows:,} filas de cuentas de estados {statement} entre "
                            f"{period_range}; no son estados agregados. "
                            f"Incluye {meta['importes_no_enteros_total']:,} importes no enteros preservados como texto/null y "
                            f"{meta['cuentas_contexto_repetidas_total']:,} repeticiones de contexto conservadas. "
                            'Monedas, taxonomías y tipos I/C permanecen separados; sin conversión, deduplicación ni suma. Cifras no cotejadas en su totalidad.'),
        })
        objects.append('  ' + json.dumps(item, ensure_ascii=False, separators=(',', ':')) + ',')
    return '\n'.join(objects)


def apply_catalogs(meta, run_id, root=DOCS):
    files = {
        'docs/js/duckdb_client.js': duckdb_block(),
        'docs/js/sidebar.js': sidebar_block(meta),
        'docs/js/data_viewer.js': viewer_block(meta),
        'docs/js/data_dictionary.js': dictionary_block(meta, run_id),
    }
    for rel, block in files.items():
        path = root.parent / rel
        text = path.read_text(encoding='utf-8')
        start, end = MARKERS[rel]
        path.write_text(replace_block(text, start, end, block, rel), encoding='utf-8')
    # Cache busting: la web descarga los catálogos recién generados y los Parquets.
    version = f"fl-{meta['ultimo_periodo']}-{meta['filas_balance_total']}-{meta['filas_resultados_total']}"
    index = root / 'index.html'
    text = index.read_text(encoding='utf-8')
    for file in ('duckdb_client.js', 'sidebar.js', 'data_dictionary.js', 'data_viewer.js'):
        pattern = rf'(src="js/{re.escape(file)}\?v=)[^"]*(")'
        text, count = re.subn(pattern, rf'\g<1>{version}\2', text)
        if count != 1:
            raise ValueError(f'No se pudo renovar cache busting de {file}: {count}')
    index.write_text(text, encoding='utf-8')


def load_complete(out=DATA):
    summary_path = out / 'resumen.json'
    if not summary_path.is_file():
        return None, 'No existe resumen de extracción.'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    periods = summary.get('periodos_indice_lista', [])
    if summary.get('estado_global') not in ('completo_sin_publicar', 'completo_publicado', 'completo_incluido_en_docs'):
        return None, f"Extracción no completa: estado={summary.get('estado_global')}"
    if (not periods or len(periods) != summary.get('periodos_indice') or
            len(set(periods)) != len(periods) or summary.get('pendientes') or summary.get('errores')):
        return None, 'La lista de períodos del índice está incompleta o tiene errores.'
    catalog_hash = summary.get('sha256_catalogo')
    balance_frames, result_frames = [], []
    for period in periods:
        folder = out / 'periodos' / period
        marker = folder / '_complete.json'
        if not marker.is_file():
            return None, f'Falta marca de período completo: {period}'
        meta = json.loads(marker.read_text(encoding='utf-8'))
        if meta.get('periodo') != period or meta.get('sha256_catalogo') != catalog_hash:
            return None, f'Metadata de período incompatible: {period}'
        for table, frames in [('balance', balance_frames), ('resultados', result_frames)]:
            file = folder / f'{table}.parquet'
            if not file.is_file():
                return None, f'Parquet ausente: {period}/{table}'
            frame = pd.read_parquet(file)
            if len(frame) != meta.get(f'filas_{table}'):
                return None, f'Cantidad de filas incoherente: {period}/{table}'
            if len(frame) and set(frame['periodo'].unique()) != {f'{period[:4]}-{period[4:]}'}:
                return None, f'Período de fila distinto al particionado: {period}/{table}'
            if list(frame.columns) != [c[0] for c in TABLE_COLUMNS]:
                return None, f'Esquema inesperado: {period}/{table}'
            frames.append(frame)
    balance = pd.concat(balance_frames, ignore_index=True)
    results = pd.concat(result_frames, ignore_index=True)
    for frame in (balance, results):
        numeric = pd.to_numeric(frame['valor_archivo'], errors='coerce')
        mask = frame['valor_es_entero'].fillna(False).astype(bool)
        if numeric[mask].isna().any() or (numeric[mask] % 1 != 0).any():
            return None, 'El valor_archivo contiene decimales o falta para un entero marcado.'
        if numeric[~mask].notna().any():
            return None, 'Un importe marcado no entero fue convertido a número.'
        frame['valor_archivo'] = pd.array(numeric, dtype='Int64')
        frame['repeticion_contexto'] = pd.array(frame['repeticion_contexto'], dtype='Int64')
    if len(balance) != summary.get('filas_balance_total') or len(results) != summary.get('filas_resultados_total'):
        return None, 'Totales de filas no coinciden con el resumen.'
    summary = dict(summary)
    summary['ruts_con_datos_total'] = sorted(set(balance['rut'].dropna()) | set(results['rut'].dropna()))
    summary['periodos_indice_lista'] = periods
    return (summary, balance, results), None


def update_root_manifest(meta, run_id, docs=DOCS):
    """Mantiene el inventario JSON del repo sincronizado con los Parquets públicos."""
    path = docs.parent / 'data_manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    tables = manifest.get('tables')
    if not isinstance(tables, list):
        raise ValueError('data_manifest.json no tiene una lista tables')
    ids = {BALANCE, RESULTS}
    tables = [item for item in tables if item.get('id') not in ids]
    generated = []
    for table_id, suffix, rows, statement in [
        (BALANCE, 'balance', meta['filas_balance_total'], 'ESF'),
        (RESULTS, 'resultados', meta['filas_resultados_total'], 'ER'),
    ]:
        generated.append({
            'id': table_id,
            'name': 'factoring_leasing.' + suffix + '_serie_ifrs_cmf',
            'view_name': table_id,
            'sector': 'factoring_leasing',
            'sector_label': 'Factoring & Leasing',
            'norma': 'CMF IFRS TXT · extracción de cuentas ESF/ER',
            'corte': f"{meta['primer_periodo'][:4]}-{meta['primer_periodo'][4:]} a {meta['ultimo_periodo'][:4]}-{meta['ultimo_periodo'][4:]}",
            'frescura': 'Serie completa del índice consultado; extracción literal, no cotejo integral',
            'modo': 'Automático · Actions publica solo al completar todos los cierres CMF',
            'ultima_actualizacion': meta['fecha_actualizacion_utc'][:10],
            'file_parquet': f'outputs/factoring_leasing/{table_id}.parquet',
            'registros_reales': int(rows),
            'descripcion': (f"{rows:,} filas de cuentas {statement}; no son estados agregados. "
                            'Monedas, taxonomías y tipo I/C separados; importes no enteros y repeticiones preservados. Sin conversión, deduplicación ni suma; cifras no cotejadas en su totalidad.'),
            'origen': (f"CMF {meta['fuente_indice']}; corrida Actions {run_id}. "
                       f"{len(meta['ruts_con_datos_total'])}/28 RUT del catálogo con datos; "
                       'revisar metadata JSON acompañante para faltantes y advertencias.'),
        })
    tables.extend(generated)
    manifest['tables'] = tables
    manifest['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    manifest['total_tables'] = len(tables)
    manifest['total_records'] = sum(int(item.get('registros_reales', 0)) for item in tables)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def publish(out=DATA, docs=DOCS, run_id='local'):
    loaded, reason = load_complete(out)
    if loaded is None:
        print(f'PUBLICACION_OMITIDA: {reason}', flush=True)
        return False
    summary, balance, results = loaded
    summary['filas_balance_total'] = len(balance)
    summary['filas_resultados_total'] = len(results)
    summary['fuente_indice'] = summary.get('fuente_indice', 'https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php')
    balance_path = docs / 'outputs' / 'factoring_leasing' / f'{BALANCE}.parquet'
    results_path = docs / 'outputs' / 'factoring_leasing' / f'{RESULTS}.parquet'
    atomic_parquet(balance, balance_path)
    atomic_parquet(results, results_path)
    meta = {
        'estado': 'serie_completa_del_indice_no_cotejo_integral',
        'fuente_indice': summary['fuente_indice'], 'run_actions': str(run_id),
        'fecha_actualizacion_utc': datetime.now(timezone.utc).isoformat(),
        'publicado_en_docs': True,
        'primer_periodo': summary['primer_periodo'], 'ultimo_periodo': summary['ultimo_periodo'],
        'periodos_indice': summary['periodos_indice'],
        'rut_catalogo': summary['rut_catalogo'],
        'ruts_con_datos': summary['ruts_con_datos_total'],
        'ruts_sin_filas_en_fuente': summary.get('ruts_sin_datos_hasta_ahora', []),
        'filas_balance': len(balance), 'filas_resultados': len(results),
        'filas_balance_total': len(balance), 'filas_resultados_total': len(results),
        'ruts_con_datos_total': summary['ruts_con_datos_total'],
        'importes_no_enteros': summary.get('importes_no_enteros_total', 0),
        'importes_no_enteros_total': summary.get('importes_no_enteros_total', 0),
        'cuentas_contexto_repetidas': summary.get('cuentas_contexto_repetidas_total', 0),
        'cuentas_contexto_repetidas_total': summary.get('cuentas_contexto_repetidas_total', 0),
        'advertencia': ('Extracción literal del TXT IFRS CMF. No es un cotejo integral de estados; '
                        'no convertir monedas, sumar balances individual/consolidado, deduplicar etiquetas, '
                        'ni interpretar valores no enteros como cero. Filas y faltantes según fuente disponible.'),
    }
    meta['sha256_balance_parquet'] = file_sha256(balance_path)
    meta['sha256_resultados_parquet'] = file_sha256(results_path)
    meta_path = docs / 'outputs' / 'factoring_leasing' / f'{BALANCE}_metadata.json'
    if meta_path.is_file():
        previous = json.loads(meta_path.read_text(encoding='utf-8'))
        stable_fields = ('sha256_balance_parquet', 'sha256_resultados_parquet',
                         'primer_periodo', 'ultimo_periodo', 'periodos_indice',
                         'ruts_con_datos', 'ruts_sin_filas_en_fuente',
                         'filas_balance', 'filas_resultados',
                         'importes_no_enteros', 'cuentas_contexto_repetidas')
        unchanged = all(previous.get(key) == meta.get(key) for key in stable_fields)
        if unchanged:
            # No crear un commit diario solo por cambiar timestamp/corrida cuando
            # los datos públicos no cambiaron.
            meta['run_actions'] = previous['run_actions']
            meta['fecha_actualizacion_utc'] = previous['fecha_actualizacion_utc']
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    effective_run_id = meta['run_actions']
    apply_catalogs(meta, effective_run_id, docs)
    update_root_manifest(meta, effective_run_id, docs)
    summary['publicado_en_docs'] = True
    summary['estado_global'] = 'completo_incluido_en_docs'
    summary['parquets_docs'] = [balance_path.relative_to(docs).as_posix(), results_path.relative_to(docs).as_posix()]
    (out / 'resumen.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"PUBLICACION_PREPARADA: balance={len(balance):,}, resultados={len(results):,}, "
          f"periodos={summary['periodos_indice']}, RUT={len(summary['ruts_con_datos_total'])}, run={run_id}", flush=True)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--docs', type=Path, default=DOCS)
    parser.add_argument('--run-id', default=os.environ.get('GITHUB_RUN_ID', 'local'))
    args = parser.parse_args()
    try:
        publish(args.data, args.docs, args.run_id)
    except Exception as exc:
        print(f'::error::Publicación no realizada: {type(exc).__name__}: {exc}', flush=True)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

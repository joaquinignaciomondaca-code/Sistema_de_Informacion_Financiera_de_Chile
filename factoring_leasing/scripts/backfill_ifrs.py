#!/usr/bin/env python3
"""Serie completa de cuentas IFRS CMF para los 28 RUT del catálogo FL.

Un pedido por trimestre disponible del índice CMF (2009-03..último cierre
publicado); cada respuesta contiene muchas sociedades. Retiene TODAS las
cuentas ESF*/ER* y ambos tipos de balance (I/C) en dos tablas detalladas,
sin inventar pasivos, ceros, conversiones o tipo de cambio. No escribe en docs/.

Persistencia: un par de Parquets por trimestre + estado atómico; Actions restaura
esta carpeta desde cache y vuelve a intentar períodos fallidos. El índice se
consulta de nuevo cada día, pero los períodos ya guardados no se descargan.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.local-data' / 'factoring_leasing_serie'
INDEX = 'https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php'
ARCHIVE = 'https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={0}&termino={0}'
CATALOG = ROOT / 'docs/outputs/factoring_leasing/factoring_leasing_maestro.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)', 'Accept': 'text/plain,text/html,*/*'}
# No asignar un tipo de balance o unidad no informada por el archivo.
COLUMNS = ['periodo', 'rut_cuerpo', 'rut', 'nombre_reportado', 'segmento_catalogo',
           'nombre_catalogo', 'tipo_balance', 'moneda_archivo', 'cuenta',
           'valor_archivo', 'valor_texto_original', 'valor_es_entero',
           'taxonomia', 'estado_financiero', 'repeticion_contexto', 'fuente_archivo',
           'sha256_archivo', 'identidad_nombre_coincide_catalogo']


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=90) as response:
        data = response.read(50_000_001)
        if len(data) > 50_000_000:
            raise ValueError('Respuesta de la CMF supera límite de 50 MB')
        if response.status != 200:
            raise ValueError(f'HTTP {response.status}')
        return data


def periods_from_index(raw):
    if not raw or b'<html' not in raw[:1000].lower():
        raise ValueError('Índice CMF no es HTML')
    parser = Links()
    parser.feed(raw.decode('utf-8', errors='replace'))
    intervals = []
    for link in parser.links:
        if 'ver_archivo.php?' not in link:
            continue
        m = re.search(r'[?&]inicio=(\d{6})&termino=(\d{6})', link.replace('&amp;', '&'))
        if not m:
            continue
        first, last = m.groups()
        if first > last or first[4:] not in ('03', '06', '09', '12') or last[4:] not in ('03', '06', '09', '12'):
            continue
        intervals.append((first, last))
    if not intervals:
        raise ValueError('Índice CMF sin intervalos de reportes trimestrales')
    # Si la página enlaza un año completo, se consulta cada cierre por separado
    # para guardar progreso y detectar ausencias sin contar páginas HTML como datos.
    periods = set()
    for first, last in intervals:
        year, month = int(first[:4]), int(first[4:])
        while f'{year:04d}{month:02d}' <= last:
            periods.add(f'{year:04d}{month:02d}')
            month += 3
            if month > 12:
                year += 1
                month = 3
    return sorted(periods)


def annual_fallback(raw_index, period, fetcher):
    """Si un corte aislado falla, usar SOLO el enlace anual anunciado por CMF.

    Preservar exclusivamente las líneas del trimestre solicitado. No aceptar
    otro año, HTML de error, archivo vacío ni períodos de otros trimestres como
    si fueran datos de ese corte.
    """
    parser = Links()
    parser.feed(decode(raw_index))
    year = period[:4]
    annual = f'{year}03'
    end = f'{year}12'
    if not any(re.search(rf'[?&]inicio={annual}&(?:amp;)?termino={end}(?:\D|$)',
                         link.replace('&amp;', '&')) for link in parser.links):
        raise ValueError(f'No existe enlace anual CMF para {year}')
    url = f'https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={annual}&termino={end}'
    raw = fetcher(url)
    if not raw or b'<html' in raw[:500].lower() or b'ACCION NO PERMITIDA' in raw[:1000].upper():
        raise ValueError('Archivo anual CMF no es TXT')
    lines = [line for line in raw.splitlines(keepends=True)
             if line.split(b';', 1)[0].strip() == period.encode('ascii')]
    if not lines:
        raise ValueError(f'Archivo anual CMF sin filas para {period}')
    return b''.join(line.rstrip(b'\r\n') + b'\n' for line in lines), url


def load_catalog(path=CATALOG):
    rows = json.loads(Path(path).read_text(encoding='utf-8'))
    catalog = {}
    for row in rows:
        rut = str(row['rut']).replace('.', '').upper()
        body, dv = rut.split('-')
        if body in catalog or not body.isdigit() or not dv:
            raise ValueError('RUT duplicado o inválido en catálogo: ' + rut)
        # Los 28 registros del catálogo incluyen segmento Automotriz. Se incluyen
        # expresamente para no omitir silenciosamente entidades de la carpeta FL.
        catalog[body] = {'rut': body + '-' + dv, 'segmento': row['segmento'],
                         'nombre': row['razon_social'].strip()}
    if not catalog:
        raise ValueError('Catálogo de entidades vacío')
    return catalog


def decode(raw):
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('latin-1')


def normalize_name(s):
    import unicodedata
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', s.upper())
                            if not unicodedata.combining(c)).split())


def parse_period(raw, period, catalog, url=None):
    """Una fila por cuenta/contexto. No sumar duplicados ni redondear a millones.

    valor_archivo es un entero literal del TXT: no se afirma que todos los
    reportes y monedas compartan una escala. La unidad se validará antes de
    publicar; por ahora permanece en cuarentena sin conversión.
    """
    if not raw or b'<html' in raw[:500].lower() or b'ACCION NO PERMITIDA' in raw[:1000].upper():
        raise ValueError('La descarga no es el archivo TXT CMF')
    if not re.fullmatch(r'\d{4}(03|06|09|12)', period):
        raise ValueError('Período inválido')
    url = url or ARCHIVE.format(period)
    digest = hashlib.sha256(raw).hexdigest()
    balance, income = [], []
    selected = 0
    noninteger = []
    repetitions = {}
    duplicates = []
    for number, cells in enumerate(csv.reader(io.StringIO(decode(raw)), delimiter=';', strict=True), start=1):
        if not cells or all(not c.strip() for c in cells):
            continue
        if len(cells) < 9:
            # No ignorar líneas corruptas de las entidades seleccionadas.
            if len(cells) > 1 and cells[1].strip() in catalog:
                raise ValueError(f'Línea {number} incompleta de RUT objetivo')
            continue
        p, body, name, kind, currency, account, amount, tax, state = (c.strip() for c in cells[:9])
        if body not in catalog:
            continue
        selected += 1
        if p != period:
            raise ValueError(f'Línea {number}: período {p} distinto al solicitado {period}')
        if len(cells) != 9 or not account or not name or not currency or not tax or not state or kind not in ('I', 'C'):
            raise ValueError(f'Línea {number}: esquema/identidad/tipo incompleto')
        integer = bool(re.fullmatch(r'-?\d+', amount))
        if not integer and len(noninteger) < 20:
            # Nunca convertir silenciosamente a 0, ni inferir separador decimal.
            noninteger.append({'linea': number, 'rut': body, 'cuenta': account,
                               'valor_original': amount[:120]})
        if not state.startswith(('ESF', 'ER')):
            continue
        key = (p, body, kind, currency, tax, state, account)
        repetitions[key] = repetitions.get(key, 0) + 1
        if repetitions[key] > 1 and len(duplicates) < 20:
            duplicates.append({'linea': number, 'rut': body, 'cuenta': account,
                               'tipo_balance': kind, 'moneda': currency, 'estado': state,
                               'valor_original': amount[:120]})
        row = dict(zip(COLUMNS, [f'{p[:4]}-{p[4:]}', body, catalog[body]['rut'], name,
                                 catalog[body]['segmento'], catalog[body]['nombre'], kind,
                                 currency, account, int(amount) if integer else None,
                                 amount, integer, tax, state, repetitions[key], url, digest,
                                 normalize_name(name) == normalize_name(catalog[body]['nombre'])]))
        if state.startswith('ESF'):
            balance.append(row)
        else:
            income.append(row)
        # Otros estados en el TXT no se confunden con balance/resultados.
    if selected == 0:
        return balance, income, {'estado': 'sin_rut_catalogo', 'filas_objetivo': 0}
    if not balance and not income:
        raise ValueError('Archivo contiene RUT objetivo pero no estados ESF/ER')
    # Contextos repetidos conservados con ordinal; su semántica no es evidente
    # (acumulado vs trimestre, reexpresiones, taxonomías) y NO se suman.
    by_rut = {r['rut'] for r in balance + income}
    return balance, income, {'estado': 'extraido', 'filas_objetivo': selected,
        'entidades': len(by_rut), 'ruts_con_datos': sorted(by_rut),
        'filas_balance': len(balance), 'filas_resultados': len(income),
        'nombres_distintos_catalogo': len({r['rut'] for r in balance + income if not r['identidad_nombre_coincide_catalogo']}),
        'importes_no_enteros': sum(not r['valor_es_entero'] for r in balance + income),
        'ejemplos_importes_no_enteros': noninteger,
        'cuentas_contexto_repetidas': sum(v - 1 for v in repetitions.values()),
        'ejemplos_repeticiones': duplicates,
        'monedas': sorted({r['moneda_archivo'] for r in balance + income}),
        'tipos_balance': sorted({r['tipo_balance'] for r in balance + income})}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as tmp:
        json.dump(value, tmp, ensure_ascii=False, indent=2)
        tmp.write('\n')
        temp = Path(tmp.name)
    temp.replace(path)


def valid_cached(out, period, catalog_digest):
    folder = out / 'periodos' / period
    marker = folder / '_complete.json'
    if not marker.is_file():
        return False
    try:
        meta = json.loads(marker.read_text(encoding='utf-8'))
        if meta.get('sha256_catalogo') != catalog_digest or meta.get('periodo') != period:
            return False
        for name in ('balance', 'resultados'):
            file = folder / f'{name}.parquet'
            if not file.is_file() or len(pd.read_parquet(file)) != meta.get('filas_' + name, 0):
                return False
        return True
    except (OSError, ValueError, KeyError):
        return False


def save_period(out, period, balance, income, stats):
    folder = out / 'periodos' / period
    folder.mkdir(parents=True, exist_ok=True)
    for name, rows in [('balance', balance), ('resultados', income)]:
        path = folder / f'{name}.parquet'
        with tempfile.NamedTemporaryFile(dir=folder, suffix='.parquet', delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            pd.DataFrame.from_records(rows, columns=COLUMNS).to_parquet(temporary, index=False)
            back = pd.read_parquet(temporary)
            if len(back) != len(rows) or (len(rows) and back['valor_texto_original'].tolist() != [r['valor_texto_original'] for r in rows]):
                raise ValueError('Roundtrip Parquet distinto al TXT')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    # _complete.json se escribe al final; si hubo interrupción, el período se reintenta.
    atomic_json(folder / '_complete.json', stats)


def run(args, fetcher=fetch):
    out = args.out
    catalog = load_catalog(args.catalog)
    catalog_digest = hashlib.sha256(Path(args.catalog).read_bytes()).hexdigest()
    index_data = fetcher(INDEX)
    periods = periods_from_index(index_data)
    out.mkdir(parents=True, exist_ok=True)
    summary = {'fuente_indice': INDEX, 'generado_utc': datetime.now(timezone.utc).isoformat(),
               'publicado_en_web': False, 'rut_catalogo': len(catalog), 'periodos_indice': len(periods),
               'primer_periodo': periods[0], 'ultimo_periodo': periods[-1],
               'procesados_esta_corrida': [], 'pendientes': [], 'errores': [],
               'nota': 'Cuarentena: cuentas ESF/ER literales por RUT; escala, cobertura y nombres históricos por auditar'}
    # Después de un barrido, no reconsultar toda la historia en cada corrida.
    # El backlog histórico avanza por índice; el ciclo siguiente reintenta errores.
    # Si el índice añade cortes, éstos se toman antes del backlog.
    progress_path = out / 'progreso.json'
    progress = json.loads(progress_path.read_text(encoding='utf-8')) if progress_path.is_file() else {}
    if progress.get('sha256_catalogo') != catalog_digest:
        progress = {'sha256_catalogo': catalog_digest, 'fallidos': []}
    pending = [p for p in reversed(periods) if not valid_cached(out, p, catalog_digest)]
    # Evitar que un solo corte que falla persistentemente monopolice el batch.
    failures = set(progress.get('fallidos', []))
    fresh = [p for p in pending if p not in failures]
    retry = [p for p in pending if p in failures]
    planned = (fresh + retry)[:args.batch]
    for period in planned:
        try:
            url = ARCHIVE.format(period)
            try:
                raw = fetcher(url)
                balance, income, stats = parse_period(raw, period, catalog, url)
            except (ValueError, OSError) as direct_error:
                try:
                    raw, url = annual_fallback(index_data, period, fetcher)
                    balance, income, stats = parse_period(raw, period, catalog, url)
                    stats['respaldo_anual'] = True
                    stats['error_consulta_trimestre'] = f'{type(direct_error).__name__}: {direct_error}'
                except (ValueError, OSError) as annual_error:
                    raise ValueError(f'corte individual: {direct_error}; respaldo anual: {annual_error}') from annual_error
            stats.update(periodo=period, sha256_archivo=hashlib.sha256(raw).hexdigest(),
                         sha256_catalogo=catalog_digest, filas_balance=len(balance),
                         filas_resultados=len(income),
                         fuente_archivo=url, fecha_descarga_utc=datetime.now(timezone.utc).isoformat())
            save_period(out, period, balance, income, stats)
            failures.discard(period)
            summary['procesados_esta_corrida'].append({'periodo': period, **stats})
            print(f"[{period}] {stats['estado']}: entidades={stats.get('entidades', 0)} "
                  f"balance={len(balance)} resultado={len(income)}", flush=True)
        except Exception as exc:
            summary['errores'].append({'periodo': period, 'error': f'{type(exc).__name__}: {exc}'})
            failures.add(period)
            print(f'::warning::[{period}] {type(exc).__name__}: {exc}', flush=True)
            # No marcar el período como completo; continuar otros trimestres.
            # Un corte antiguo puede devolver 500/HTML aunque los demás funcionen.
            # Se reintentará en la próxima corrida sin bloquear el backfill.
            continue
    summary['pendientes'] = [p for p in reversed(periods) if not valid_cached(out, p, catalog_digest)]
    atomic_json(progress_path, {'sha256_catalogo': catalog_digest,
                                'fallidos': sorted(failures & set(summary['pendientes']))})
    summary['completados_total'] = len(periods) - len(summary['pendientes'])
    completed = [json.loads((out / 'periodos' / p / '_complete.json').read_text(encoding='utf-8'))
                 for p in periods if valid_cached(out, p, catalog_digest)]
    summary['ruts_con_datos_total'] = sorted({rut for item in completed for rut in item.get('ruts_con_datos', [])})
    summary['ruts_sin_datos_hasta_ahora'] = sorted({meta['rut'] for meta in catalog.values()} - set(summary['ruts_con_datos_total']))
    summary['filas_balance_total'] = sum(item['filas_balance'] for item in completed)
    summary['filas_resultados_total'] = sum(item['filas_resultados'] for item in completed)
    summary['importes_no_enteros_total'] = sum(item.get('importes_no_enteros', 0) for item in completed)
    summary['cuentas_contexto_repetidas_total'] = sum(item.get('cuentas_contexto_repetidas', 0) for item in completed)
    summary['periodos_sin_rut_catalogo'] = [item['periodo'] for item in completed if item['estado'] == 'sin_rut_catalogo']
    summary['estado_global'] = ('completo_sin_publicar' if not summary['pendientes'] else
                               'parcial_con_errores_sin_publicar' if summary['errores'] else
                               'en_progreso_sin_publicar')
    atomic_json(out / 'resumen.json', summary)
    print(f"PROGRESO {summary['completados_total']}/{len(periods)} períodos; "
          f"pendientes={len(summary['pendientes'])}; estado={summary['estado_global']}", flush=True)
    # Incompleto o con errores se comunica en resumen, pero no se simula
    # completitud: el job conserva progreso y el próximo disparo continúa.
    return 0 if summary['completados_total'] > 0 else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--catalog', type=Path, default=CATALOG)
    p.add_argument('--out', type=Path, default=OUT)
    p.add_argument('--batch', type=int, default=100, help='máximo de trimestres por corrida')
    args = p.parse_args()
    if args.batch < 1:
        p.error('--batch debe ser positivo')
    return run(args)


if __name__ == '__main__':
    sys.exit(main())

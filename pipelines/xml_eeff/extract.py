#!/usr/bin/env python3
"""Ingesta CMF IFRS XML / XBRL en cuarentena; nunca modifica docs/outputs.

Por defecto: revisa los dos últimos cierres y un lote acotado de entidades por día.
El cursor + histórico se conservan en cache de Actions; para reiniciar, --reset.
Las salidas son JSONL y manifiesto en .local-data/xml_eeff/, para artifact privado.
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.local-data/xml_eeff'
BASE = 'https://www.cmfchile.cl'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0; financial-research)', 'Accept': 'text/html,application/xml,*/*'}
CONFIG = {
    'corredoras': ('docs/outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.json', 'COBOL', '3', 'IVEF', 'rut_cuerpo', 'nombre_empresa'),
    'ffmm': ('docs/outputs/ffmm/ffmm_registro_fondos_universo.json', 'RGFMU', '3', 'FMEF', 'run_fondo', 'nombre_fondo'),
    'fi': ('docs/outputs/fi/fi_registro_fondos_universo.json', None, '29', 'FIEF', 'run_fondo', 'nombre_fondo'),
    'agf': ('docs/outputs/agf/agf_maestro.json', 'RGAGF', '3', 'XBRL', 'rut', 'razon_social'),
    'retail': ('docs/outputs/retail_financiero/retail_financiero_maestro.json', 'RVEMI', '3', 'XBRL', 'rut', 'razon_social'),
}
BALANCE = {'corredoras': ('TotalActivos', 'TotalPasivos', 'TotalPatrimonio'),
           'ffmm': ('TotalActivo', 'TotalPasivo', 'ActivoNetoAtribuibleALosParticipes'),
           'fi': ('TotalActivo', 'TotalPasivo', 'TotalPatrimonioNeto')}
RESULT = {'corredoras': ('UtilidadPerdidaDelEjercicio', 'ResultadoDelEjercicioPatrimonio', 'ResultadoAntesDeImpuestoALaRenta'),
          'ffmm': ('UtilidadPerdidaDeLaOperacionDespuesDeImpuesto',),
          'fi': ('ResultadoDelEjercicio',)}


def read_url(url, limit=12_000_000):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Respuesta demasiado grande')
    return raw


def periodos_ultimo(anios=2):
    hoy = date.today()
    # Ventana pequeña con solapamiento para declaraciones tardías o correcciones.
    cierre = ((hoy.month - 1) // 3) * 3 or 12
    anio = hoy.year if cierre != 12 or hoy.month != 1 else hoy.year - 1
    meses = []
    for _ in range(anios * 4):
        meses.append(f'{anio:04d}-{cierre:02d}')
        cierre -= 3
        if cierre == 0:
            anio -= 1
            cierre = 12
    return meses


def plan(sector, include_historical=False):
    file, entity, tab, marker, idcol, namecol = CONFIG[sector]
    rows = json.loads((ROOT / file).read_text(encoding='utf8'))
    seen = set()
    for row in rows:
        rut = str(row[idcol]).strip().replace('.', '').split('-')[0]
        tipo = row.get('tipo_entidad', entity) if sector == 'fi' else entity
        if tipo not in (entity, 'FINRE', 'FIRES') or not rut.isdigit() or (rut, tipo) in seen:
            continue
        seen.add((rut, tipo))
        # En el barrido cotidiano, no pedir reportes futuros de entidades históricas.
        if not include_historical and str(row.get('estado_vigencia', row.get('estado_cmf', 'vigente'))).lower().startswith('no vigente'):
            continue
        yield {'sector': sector, 'rut': rut, 'tipo': tipo, 'nombre_registro': str(row[namecol]), 'tab': tab, 'marker': marker}


def ficha_url(item, per):
    year, month = per.split('-')
    params = {'mercado': 'V', 'rut': item['rut'], 'tipoentidad': item['tipo'], 'vig': 'VI', 'control': 'svs',
              'pestania': item['tab'], 'mm': month, 'aa': year}
    if item['sector'] not in ('corredoras',):
        params.update(tipo='I', tipo_norma='IFRS')
    return BASE + '/institucional/mercados/entidad.php?' + urllib.parse.urlencode(params)


def link_from_html(raw, item):
    page = raw.decode('latin-1', errors='replace')
    marker = item['marker']
    if marker != 'XBRL':
        for href in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', page, re.I):
            href = html.unescape(href)
            if 'ifrs_xml_verarchivo.php' in href and 'archivo=' + marker in href:
                return urllib.parse.urljoin(BASE + '/institucional/mercados/', href)
    else:
        for m in re.finditer(r'<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', page, re.I | re.S):
            if 'XBRL' in re.sub(r'<[^>]+>', '', m[2]).upper():
                return urllib.parse.urljoin(BASE + '/institucional/mercados/', html.unescape(m[1]))
    return None


def signed_rut_ok(body, dv):
    nums = [int(x) for x in str(body) if x.isdigit()]
    if not nums: return False
    n = 11 - sum(x * (2 + i % 6) for i, x in enumerate(reversed(nums))) % 11
    return ('0' if n == 11 else 'K' if n == 10 else str(n)) == str(dv).upper()


def parse_ifrs(raw, item, per, url):
    root = ET.fromstring(raw)
    if root.tag != 'IFRS': raise ValueError(f'Raiz no IFRS: {root.tag}')
    ident = root.find('Identificacion')
    datos = root.find('DatosPeriodo')
    if ident is None or datos is None: raise ValueError('Sin Identificacion/DatosPeriodo')
    fondo = item['sector'] in ('ffmm', 'fi')
    body_key = 'RUTFondoInforma' if fondo else 'RUTEntidadInforma'
    dv_key = 'DVFondoInforma' if fondo else 'DVEntidadInforma'
    rut_xml = ident.findtext(body_key)
    dv_xml = ident.findtext(dv_key)
    if rut_xml and rut_xml != item['rut']: raise ValueError('RUT XML no corresponde al registro')
    if rut_xml and dv_xml and not signed_rut_ok(rut_xml, dv_xml): raise ValueError('DV XML invalido')
    fecha = datos.find('PeriodoPresentacionEstadosFinancieros')
    if fecha is None: raise ValueError('Periodo no declarado')
    informado = f"{int(fecha.findtext('Anio')):04d}-{int(fecha.findtext('Mes')):02d}"
    if informado != per: raise ValueError(f'Periodo XML {informado} != consulta {per}')
    moneda = datos.findtext('MonedaPresentacionEstadosFinancieros')
    if not moneda: raise ValueError('Moneda no declarada')
    facts = {}
    for node in root.iter('Cuenta'):
        if node.get('Context') != 'PeriodoActual' or not node.get('CodigoCuenta'): continue
        code = node.get('CodigoCuenta')
        text = (node.text or '').strip()
        if not re.fullmatch(r'-?\d+(?:\.\d+)?', text): raise ValueError(f'Cuenta no numerica: {code}')
        number = float(text)
        # Repeated codes are acceptable only if their value is identical.
        if code in facts and facts[code] != number: raise ValueError(f'Codigo duplicado con valores distintos: {code}')
        facts[code] = number
    codes = BALANCE[item['sector']]
    if not all(k in facts for k in codes): raise ValueError('Faltan totales de balance')
    activo, pasivo, patrimonio = (facts[k] for k in codes)
    # FFMM: el pasivo excluye el activo neto; FI TotalPasivo incluye patrimonio.
    check = pasivo + patrimonio if item['sector'] != 'fi' else pasivo
    if abs(activo - check) > max(1.0, abs(activo) * 0.000001):
        raise ValueError('Balance no cuadra (segun estructura sectorial)')
    result_code = next((k for k in RESULT[item['sector']] if k in facts), None)
    if not result_code: raise ValueError('Falta resultado del ejercicio (no inventar cero)')
    return {'sector': item['sector'], 'rut': item['rut'], 'tipo_entidad': item['tipo'], 'nombre_registro': item['nombre_registro'],
            'periodo': per, 'moneda_original': moneda, 'escala': 'miles',
            'total_activo': activo, 'total_pasivo_reportado': pasivo, 'patrimonio_o_activo_neto': patrimonio,
            'definicion_total_pasivo': 'incluye_patrimonio' if item['sector'] == 'fi' else 'excluye_patrimonio',
            'resultado_ejercicio': facts[result_code], 'codigo_resultado': result_code,
            'balance_cuadra': True, 'cuentas': len(facts), 'fuente_url': url,
            'sha256_xml': hashlib.sha256(raw).hexdigest(), 'calidad': 'revisar_antes_de_publicar'}


def parse_xbrl(raw, item, per, url):
    """XBRL: no homologar conceptos IFRS arbitrariamente. Guardar métricas solo si inequívocas."""
    root = ET.fromstring(raw)
    if not root.tag.lower().endswith('xbrl'):
        raise ValueError(f'No es una instancia XBRL: {root.tag}')
    # XBRL permite múltiples dimensiones, segmentos, contextos y unidades; no inferir
    # totales en masa sin resolver moneda, base de consolidación y contexto del período.
    contexts = sum(1 for el in root if el.tag.rsplit('}', 1)[-1] == 'context')
    units = sum(1 for el in root if el.tag.rsplit('}', 1)[-1] == 'unit')
    if not contexts or not units: raise ValueError('XBRL sin contextos o unidades')
    return {'sector': item['sector'], 'rut': item['rut'], 'periodo': per,
            'tipo_entidad': item['tipo'], 'nombre_registro': item['nombre_registro'],
            'xbrl_contextos': contexts, 'xbrl_unidades': units, 'fuente_url': url,
            'sha256_xbrl': hashlib.sha256(raw).hexdigest(), 'calidad': 'xbrl_pendiente_mapeo_taxonomia',
            'total_activo': None, 'resultado_ejercicio': None}


def process(item, per):
    url = ficha_url(item, per)
    raw_ficha = read_url(url)
    link = link_from_html(raw_ficha, item)
    if not link: return 'sin_fuente', None
    raw = read_url(link)
    if item['marker'] == 'XBRL':
        return 'pendiente_taxonomia', parse_xbrl(raw, item, per, link)
    return 'ok_xml', parse_ifrs(raw, item, per, link)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sector', choices=list(CONFIG), action='append', help='repetible; sin argumento: todos')
    ap.add_argument('--start', help='AAAA-MM; sólo para backfill manual')
    ap.add_argument('--end', help='AAAA-MM; sólo para backfill manual')
    ap.add_argument('--batch', type=int, default=90, help='máximo de combinaciones por corrida y sector')
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--shards', type=int, default=1)
    ap.add_argument('--reset', action='store_true', help='descartar cursor y estado de una ventana nueva')
    ap.add_argument('--historical', action='store_true', help='incluye entidades no vigentes; para backfill manual')
    ap.add_argument('--all-periods', action='store_true', help='backfill trimestral desde 2011, en lotes')
    args = ap.parse_args()
    if args.batch < 1: ap.error('--batch debe ser positivo')
    if args.shards < 1 or not 0 <= args.shard < args.shards: ap.error('shard fuera de rango')
    OUT.mkdir(parents=True, exist_ok=True)
    sectors = args.sector or list(CONFIG)
    if args.start and not re.fullmatch(r'\d{4}-(03|06|09|12)', args.start): ap.error('--start inválido')
    if args.end and not re.fullmatch(r'\d{4}-(03|06|09|12)', args.end): ap.error('--end inválido')
    if args.all_periods or args.start or args.end:
        periods = [f'{y}-{m:02d}' for y in range(2011, date.today().year + 1) for m in (3, 6, 9, 12)]
        periods = [p for p in periods if p <= periodos_ultimo(1)[0]]
    else:
        periods = periodos_ultimo(1)[:2]  # último cierre y previo; fechas pasadas sin repasar toda la historia
    if args.start: periods = [p for p in periods if p >= args.start]
    if args.end: periods = [p for p in periods if p <= args.end]
    if not periods: ap.error('ventana vacía')
    periods.sort()
    results = {}
    for sector in sectors:
        pending = [(item, period) for item in plan(sector, args.historical or args.all_periods)
                   if int(hashlib.sha256((item['rut'] + item['tipo']).encode()).hexdigest(), 16) % args.shards == args.shard
                   for period in periods]
        fingerprint = hashlib.sha256(json.dumps([(i['rut'], i['tipo'], p) for i, p in pending]).encode()).hexdigest()[:12]
        statepath = OUT / f'{sector}_shard{args.shard}of{args.shards}_state.json'
        ledgerpath = OUT / f'{sector}_shard{args.shard}of{args.shards}_ledger.jsonl'
        if args.reset or not statepath.exists():
            state = {'fingerprint': fingerprint, 'cursor': 0, 'pass': 0}
        else:
            state = json.loads(statepath.read_text())
            if state['fingerprint'] != fingerprint: state = {'fingerprint': fingerprint, 'cursor': 0, 'pass': state.get('pass', 0) + 1}
        if not pending:
            results[sector] = {'total': 0, 'procesadas': 0, 'estado': 'sin_entidades'}
            continue
        start = state['cursor'] % len(pending)
        done = 0
        stats = {}
        with ledgerpath.open('a', encoding='utf8') as ledger:
            for offset in range(min(args.batch, len(pending))):
                ix = (start + offset) % len(pending)
                item, per = pending[ix]
                try:
                    status, data = process(item, per)
                    error = None
                except Exception as exc:
                    status, data, error = 'error', None, f'{type(exc).__name__}: {exc}'
                stats[status] = stats.get(status, 0) + 1
                row = {'sector': sector, 'rut': item['rut'], 'periodo': per, 'status': status,
                       'consulta': ficha_url(item, per), 'error': error, 'registro': data,
                       'consultado_utc': datetime.now(timezone.utc).isoformat()}
                ledger.write(json.dumps(row, ensure_ascii=False) + '\n')
                ledger.flush()
                state['cursor'] = (ix + 1) % len(pending)
                # Persistencia para recuperación de fallos del job.
                statepath.write_text(json.dumps(state, indent=2))
                done += 1
                time.sleep(.15)
        results[sector] = {'total': len(pending), 'procesadas': done, 'cursor': state['cursor'], 'por_estado': stats}
        print(f'{sector}: {json.dumps(results[sector], ensure_ascii=False)}', flush=True)
    (OUT / f'resumen_shard{args.shard}of{args.shards}.json').write_text(json.dumps({'generado_utc': datetime.now(timezone.utc).isoformat(),
                                                    'solo_revision': True, 'sectores': results}, indent=2, ensure_ascii=False))
    # Fail closed if *every* attempt is a transport/parse error. An empty result is NOT success.
    attempts = sum(sum(v.get('por_estado', {}).values()) for v in results.values())
    errors = sum(v.get('por_estado', {}).get('error', 0) for v in results.values())
    if attempts == 0 or attempts == errors: return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())

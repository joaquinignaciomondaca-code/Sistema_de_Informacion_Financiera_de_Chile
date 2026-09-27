#!/usr/bin/env python3
"""Coteja dos estados de situación financiera CMF: archivo plano vs ficha HTML.

Solo genera evidencia en .local-data; NUNCA escribe docs/outputs. No reutiliza
el extractor antiguo, que redondea, rellena faltantes con cero y publica.
"""
import base64
import csv
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.local-data' / 'factoring_leasing_muestra'
BASE = 'https://www.cmfchile.cl/institucional'
SAMPLES = [
    {'segmento': 'Factoring', 'rut': '96655860', 'dv': '1', 'periodo': '202206',
     'nombre': 'FACTORING SECURITY S.A.', 'tipo_entidad': 'RVEMI'},
    {'segmento': 'Leasing', 'rut': '96809970', 'dv': '1', 'periodo': '202209',
     'nombre': 'UNIDAD LEASING HABITACIONAL S.A.', 'tipo_entidad': 'RGEIN'},
]
FIELDS = {
    'total_activos_miles_clp': 'Total de activos',
    'total_pasivos_miles_clp': 'Total de pasivos',
    'patrimonio_miles_clp': 'Patrimonio total',
    'efectivo_miles_clp': 'Efectivo y equivalentes al efectivo',
}


def fetch(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html,text/plain,*/*'})
    with urlopen(req, timeout=90) as response:
        return response.read()


def urls(sample):
    period = sample['periodo']
    ficha = (f"{BASE}/mercados/entidad.php?mercado=V&rut={sample['rut']}"
             f"&tipoentidad={sample['tipo_entidad']}&vig=VI&control=svs&pestania=3"
             f"&mm={period[4:]}&aa={period[:4]}&tipo=I&tipo_norma=IFRS")
    archivo = f'{BASE}/estadisticas/ver_archivo.php?inicio={period}&termino={period}'
    return ficha, archivo


class Rows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.depth = 0
        self.cell = None
        self.cells = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.depth += 1
            if self.depth == 1:
                self.cells = []
        elif tag in ('td', 'th') and self.depth == 1:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.cells.append(' '.join(' '.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr':
            if self.depth == 1 and self.cells:
                self.rows.append(self.cells)
            self.depth = max(0, self.depth - 1)


def html_amounts(data, sample):
    page = data.decode('utf-8', errors='replace')
    if '\ufffd' in page:
        page = data.decode('latin-1')
    if sample['nombre'] not in page.upper() or not re.search(r'RUT\s*:?\s*' + sample['rut'] + r'\s*-\s*' + sample['dv'], page, re.I):
        raise ValueError('Identidad (nombre/RUT/DV) no coincide con ficha CMF')
    if not re.search(r'Tipo de Balance\s*:?\s*<[^>]*>\s*INDIVIDUAL', page, re.I):
        raise ValueError('Ficha no declara balance individual')
    if not re.search(r'CLP\s*-\s*Peso chileno\s*\(Miles\)', page, re.I):
        raise ValueError('Ficha sin unidad CLP (miles)')
    if f'{sample["periodo"][:4]}-{sample["periodo"][4:]}-' not in page:
        raise ValueError('Cierre no encontrado en visualización de ficha')
    parser = Rows()
    parser.feed(page)
    # Aislar el estado de situación: la etiqueta Efectivo también aparece en flujos.
    active = False
    found = {v: [] for v in FIELDS.values()}
    for cells in parser.rows:
        text = ' '.join(cells)
        if '[210000]' in text or 'Estado de situación financiera, corriente/no corriente' in text:
            active = True
        if active and ('[310000]' in text or 'Estado del resultado' in text):
            break
        if not active:
            continue
        if cells and cells[0].strip() in found:
            vals = [c for c in cells[1:] if re.fullmatch(r'-?\d[\d.]*', c.strip())]
            if not vals:
                raise ValueError('No hay importe actual para ' + cells[0])
            found[cells[0]].append(int(vals[0].replace('.', '')))
    if any(len(v) != 1 for v in found.values()):
        raise ValueError(f'Etiquetas HTML ausentes/duplicadas: { {k: len(v) for k, v in found.items()} }')
    return {col: found[label][0] for col, label in FIELDS.items()}


def stream_amounts(data, sample):
    if b'<html' in data[:500].lower():
        raise ValueError('Archivo estructurado devolvió HTML')
    text = data.decode('utf-8', errors='replace')
    if '\ufffd' in text:
        text = data.decode('latin-1')
    found = {v: [] for v in FIELDS.values()}
    names = set()
    rows = 0
    for cells in csv.reader(text.splitlines(), delimiter=';'):
        if len(cells) < 9 or cells[0] != sample['periodo'] or cells[1] != sample['rut'] or cells[3] != 'I' or cells[4] != 'CLP':
            continue
        names.add(cells[2].strip().upper())
        if cells[5] not in found or not cells[8].startswith('ESF'):
            continue
        if not re.fullmatch(r'-?\d+', cells[6].strip()):
            raise ValueError('Importe estructurado no entero: ' + cells[5])
        value = int(cells[6])
        if value % 1000:
            raise ValueError('Importe no convertible exactamente a miles: ' + cells[5])
        found[cells[5]].append(value // 1000)
        rows += 1
    if names != {sample['nombre']}:
        raise ValueError(f'Nombre del archivo no coincide con identidad esperada: {names}')
    if any(len(v) != 1 for v in found.values()):
        raise ValueError(f'Cuentas ausentes/duplicadas en archivo: { {k: len(v) for k, v in found.items()} }')
    if rows != 4:
        raise ValueError('No hay exactamente cuatro cuentas para muestra')
    return {col: found[label][0] for col, label in FIELDS.items()}


def audit_one(sample, ficha_data, archivo_data):
    ficha, archivo = urls(sample)
    html = html_amounts(ficha_data, sample)
    stream = stream_amounts(archivo_data, sample)
    if stream != html:
        raise ValueError(f'Diferencias fuente estructurada vs ficha CMF: { {k: (stream[k], html[k]) for k in FIELDS if stream[k] != html[k]} }')
    if stream['total_activos_miles_clp'] <= 0 or stream['total_activos_miles_clp'] != stream['total_pasivos_miles_clp'] + stream['patrimonio_miles_clp']:
        raise ValueError('Balance no cuadra: activo != pasivo + patrimonio')
    return {'segmento': sample['segmento'], 'rut': sample['rut'] + '-' + sample['dv'],
            'nombre_en_archivo_y_ficha': sample['nombre'], 'tipo_entidad': sample['tipo_entidad'],
            'tipo_balance': 'I', 'periodo': sample['periodo'][:4] + '-' + sample['periodo'][4:],
            'unidad': 'miles de pesos chilenos (CLP)', **stream, 'fuente_ficha_cmf': ficha,
            'fuente_archivo_cmf': archivo, 'sha256_ficha': hashlib.sha256(ficha_data).hexdigest(),
            'sha256_archivo': hashlib.sha256(archivo_data).hexdigest(),
            'alcance_validacion': 'cuatro cuentas del balance, esta entidad y este período solamente; PDF/XBRL no cotejados'}


def main():
    records, errors = [], []
    for sample in SAMPLES:
        try:
            ficha, archivo = urls(sample)
            record = audit_one(sample, fetch(ficha), fetch(archivo))
            records.append(record)
            print(f'COINCIDE {record["segmento"]} {record["rut"]} {record["periodo"]}: {record["total_activos_miles_clp"]} miles CLP', flush=True)
            # Evidencia recuperable si el sandbox no puede bajar artifacts/logs. Nunca tokens.
            print('::notice::FL_SAMPLE_B64=' + base64.b64encode(json.dumps(record, ensure_ascii=False).encode()).decode(), flush=True)
        except Exception as exc:
            error = {'segmento': sample['segmento'], 'rut': sample['rut'], 'periodo': sample['periodo'], 'error': f'{type(exc).__name__}: {exc}'}
            errors.append(error)
            print(f'::error::{json.dumps(error, ensure_ascii=False)}', flush=True)
    report = {'aprobada_muestra': len(records) == len(SAMPLES) and not errors,
              'criterio': 'cuatro cuentas del balance, identidad, período, I, CLP miles y cuadre; no valida resultados ni PDF/XBRL',
              'registros': records, 'errores': errors}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'cotejo.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Muestra aprobada={report["aprobada_muestra"]}; filas={len(records)}; errores={len(errors)}', flush=True)
    return 0 if report['aprobada_muestra'] else 1


if __name__ == '__main__':
    sys.exit(main())

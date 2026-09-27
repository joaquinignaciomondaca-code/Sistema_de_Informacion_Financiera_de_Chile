#!/usr/bin/env python3
"""Cotejo acotado XML vs tabla HTML CMF; Parquet solo de revisión.

NUNCA escribe docs/outputs. En Actions descarga las fichas y los XML; el reporte
incluye cifras reales y se puede reconstruir localmente sin descargar artifacts.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata

import pandas as pd

import extract

OUT = extract.ROOT / '.local-data/xml_eeff_muestra'
# Entidades/períodos seleccionados antes del cotejo. La tabla HTML y el XML se
# obtienen independientemente de la misma ficha CMF durante la corrida.
SAMPLE = [
    ('ffmm', '8490', '2014-12'),
    ('fi', '7064', '2021-12'),
]
LABELS = {
    'ffmm': {
        'total_activo': 'total activo',
        'total_pasivo_reportado': 'total pasivo (excluido el activo neto',
        'patrimonio_o_activo_neto': 'activo neto atribuible a los participes',
        'resultado_ejercicio': 'utilidad/',
    },
    'fi': {
        'total_activo': 'total activo',
        'total_pasivo_reportado': 'total pasivo',
        'patrimonio_o_activo_neto': 'total patrimonio neto',
        'resultado_ejercicio': 'resultado del ejercicio',
    },
}


def plain(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return ' '.join(text.casefold().split())


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.cells = []
        self.cell = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.depth += 1
            if self.depth == 1: self.cells = []
        elif tag in ('td', 'th') and self.depth == 1:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.cells.append(' '.join(' '.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr':
            if self.depth == 1 and self.cells: self.rows.append(self.cells)
            self.depth = max(0, self.depth - 1)


def html_values(page, sector):
    parser = Tables()
    parser.feed(page.decode('latin-1', errors='replace'))
    found = {}
    for field, label in LABELS[sector].items():
        candidates = []
        start = False
        for cells in parser.rows:
            if sector == 'fi' and field == 'resultado_ejercicio':
                title = ' '.join(plain(c) for c in cells)
                if 'estado de resultados integrales' in title: start = True
                elif start and ('estado de cambios en el patrimonio' in title or
                                'estado de flujos de efectivo' in title): break
                if not start: continue
            # Etiqueta en celda propia; descartar subtotales que solo contienen el texto.
            def matches(cell):
                value = plain(cell)
                if field == 'resultado_ejercicio' and sector == 'ffmm':
                    # La etiqueta usa barra: Utilidad/(pérdida) de la operación después de impuesto.
                    return ('de la operacion despues de impuesto' in value and
                            ('utilidad' in value or 'perdida' in value))
                if field == 'resultado_ejercicio' and sector == 'fi':
                    # En cambios patrimoniales también aparece "Resultado del ejercicio":
                    # cotejar solo contra el estado de resultados integrales.
                    return value.startswith('resultado del ejercicio')
                # No confundir Total Activo Corriente/No Corriente ni
                # Total Pasivo Corriente con el total del balance.
                if field == 'total_activo':
                    return value == label or bool(re.fullmatch(re.escape(label) + r' \([^)]*\)', value))
                if field == 'total_pasivo_reportado':
                    if sector == 'ffmm': return value.startswith(label)
                    return value == label or bool(re.fullmatch(re.escape(label) + r' \([^)]*\)', value))
                return value.startswith(label)
            if not any(matches(cell) for cell in cells): continue
            # La ficha presenta Nota, período actual y período anterior. Los dos
            # últimos valores numéricos de la fila son los importes de ambos períodos.
            nums = []
            for cell in cells:
                if re.fullmatch(r'\(?-?\d[\d.]*\)?', cell):
                    nums.append(int(cell.replace('.', '').strip('()')) * (-1 if cell.startswith('(') else 1))
            if len(nums) >= 2:
                candidates.append(nums[-2])
        if not candidates:
            raise ValueError(f'Fila HTML sin dos períodos: {sector}.{field} ({label}); candidatas={[[c[:65] for c in row] for row in parser.rows if any(label in plain(c) for c in row)][:4]}')
        if len(set(candidates)) != 1:
            raise ValueError(f'Fila HTML ambigua: {sector}.{field}: {candidates}')
        found[field] = candidates[0]
    return found


def sample_once(sector, rut, period):
    item = next(i for i in extract.plan(sector, include_historical=True) if i['rut'] == rut)
    ficha = extract.ficha_url(item, period)
    raw_html = extract.read_url(ficha)
    link = extract.link_from_html(raw_html, item)
    if not link: raise ValueError('La ficha no enlaza el XML correspondiente')
    cmf = html_values(raw_html, sector)
    raw_xml = extract.read_url(link, referer=ficha)
    parsed = extract.parse_ifrs(raw_xml, item, period, link)
    # No aprobar XML saneado o DV discordante aunque los importes coincidan.
    if parsed['parseo_reparado'] or parsed['dv_xml_coincide'] is False:
        raise ValueError('XML reparado o DV discordante: requiere revisión manual')
    diffs = {field: {'cmf_html': amount, 'xml': parsed[field]}
             for field, amount in cmf.items() if amount != parsed[field]}
    if diffs: raise ValueError(f'Cifras XML vs HTML distintas: {diffs}')
    record = {k: parsed[k] for k in ('sector', 'rut', 'tipo_entidad', 'nombre_registro', 'periodo',
        'moneda_original', 'escala', 'total_activo', 'total_pasivo_reportado',
        'definicion_total_pasivo', 'patrimonio_o_activo_neto', 'resultado_ejercicio',
        'codigo_resultado', 'dv_xml_coincide', 'parseo_reparado', 'sha256_xml')}
    record.update(fuente_ficha=ficha, fuente_xml=extract.url_fuente_segura(link),
                  sha256_html=hashlib.sha256(raw_html).hexdigest(),
                  calidad='muestra_cotejada_xml_vs_html_cmf')
    return record


def save(records, directory):
    directory.mkdir(parents=True, exist_ok=True)
    # Mantener datos y resultado de la auditoría juntos, NO bajo docs/outputs.
    path = directory / 'eeff_muestra_cmf.parquet'
    pd.DataFrame.from_records(records).to_parquet(path, index=False)
    verify = pd.read_parquet(path).to_dict(orient='records')
    for source, roundtrip in zip(records, verify):
        for key in ('rut', 'periodo', 'total_activo', 'total_pasivo_reportado',
                    'patrimonio_o_activo_neto', 'resultado_ejercicio', 'moneda_original', 'sha256_xml'):
            if source[key] != roundtrip[key]: raise ValueError(f'Parquet no coincide tras lectura: {key}')
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-report', type=Path, help='reconstruir Parquet desde reporte Actions verificado')
    parser.add_argument('--output-dir', type=Path, default=OUT)
    args = parser.parse_args()
    records, errors = [], []
    if args.from_report:
        report = json.loads(args.from_report.read_text(encoding='utf8'))
        if not report.get('aprobada_muestra') or len(report.get('registros', [])) != len(SAMPLE):
            parser.error('Reporte incompleto o no aprobado: no crear Parquet')
        if {(r['sector'], r['rut'], r['periodo']) for r in report['registros']} != set(SAMPLE):
            parser.error('El reporte no corresponde a la muestra predefinida')
        records = report['registros']
    else:
        for sector, rut, period in SAMPLE:
            try:
                row = sample_once(sector, rut, period)
                records.append(row)
                print(f'COINCIDE: {sector} {rut} {period}: activo={row["total_activo"]} '
                      f'pasivo_reportado={row["total_pasivo_reportado"]} '
                      f'patrimonio={row["patrimonio_o_activo_neto"]} '
                      f'resultado={row["resultado_ejercicio"]} moneda_xml={row["moneda_original"]}', flush=True)
            except Exception as exc:
                errors.append({'sector': sector, 'rut': rut, 'periodo': period,
                               'error': f'{type(exc).__name__}: {exc}'})
                print(f'NO APROBADO: {sector} {rut} {period}: {exc}', flush=True)
    approved = len(records) == len(SAMPLE) and not errors
    report = {'aprobada_muestra': approved, 'criterio': 'cuatro campos XML contra tabla HTML CMF; RUT, período y DV',
              'alcance': 'dos entidad/período; no valida el universo ni la moneda de otros registros',
              'registros': records, 'errores': errors}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'cotejo_muestra.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf8')
    if approved:
        path = save(records, args.output_dir)
        print(f'PARQUET MUESTRA: {path} ({len(records)} filas)', flush=True)
    else:
        print('Muestra NO aprobada; no se genera Parquet.', flush=True)
    return 0 if approved else 1


if __name__ == '__main__':
    raise SystemExit(main())

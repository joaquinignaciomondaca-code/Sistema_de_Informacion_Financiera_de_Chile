"""Coteja FX REPO 2008–2026 con tablas diarias oficiales del SII (NO publica).

El HTML viejo del SII lista observaciones diarias; para cada mes se usa la
última cotización diaria publicada, que puede ser anterior al fin calendario.
No se interpreta un blanco como cero ni se sustituye por un promedio mensual.
Páginas nuevas sin la tabla antigua se reportan como SIN_VERIFICAR, no como OK.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from decimal import Decimal
from pathlib import Path

from bancos.scripts import probe_repos_zip_cmf as probe
from bancos.scripts.probe_repo_fx_sii import Tables, URL

OUT = probe.ROOT / '.local-data/review/bancos/fx_sii_historico.json'
HEADER = ['Día', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
NUMBER = re.compile(r'\d+(?:[.,]\d{1,2})?\Z')


def parse_old_table(html: str, year: int) -> dict[str, Decimal]:
    parser = Tables()
    parser.feed(html)
    candidates = [t for t in parser.tables if t and t[0] == HEADER]
    # La versión nueva del SII incluye la misma tabla anual más 12 tablas
    # mensuales; seleccionar la única tabla con encabezado de 13 columnas.
    if len(candidates) != 1:
        raise ValueError(f'{year}: no hay exactamente una tabla anual completa SII')
    table = candidates[0]
    if len(table) != 33 or any(len(row) != 13 for row in table):
        raise ValueError(f'{year}: tabla SII truncada o alterada')
    if [r[0] for r in table[1:32]] != [str(i) for i in range(1, 32)]:
        raise ValueError(f'{year}: días SII no secuenciales')
    if table[32][0] != 'Promedio':
        raise ValueError(f'{year}: fila final no reconocida')
    latest = {}
    for month in range(1, 13):
        values = [r[month] for r in table[1:32] if r[month]]
        if not values or any(not NUMBER.fullmatch(v) for v in values):
            raise ValueError(f'{year}-{month:02d}: sin última observación SII o monto inválido')
        latest[f'{year}-{month:02d}'] = Decimal(values[-1].replace(',', '.'))
    return latest


def compare_year(year: int, html: str, published: dict[str, Decimal]) -> dict:
    try:
        values = parse_old_table(html, year)
    except ValueError as exc:
        return {'anio': year, 'estado': 'SIN_VERIFICAR', 'motivo': str(exc)}
    if set(values) != {f'{year}-{m:02d}' for m in range(1, 13)}:
        raise ValueError('Cobertura anual incompleta')
    relevant = {p: v for p, v in values.items() if p in published}
    if not relevant:
        return {'anio': year, 'estado': 'SIN_VERIFICAR', 'motivo': 'Año sin meses publicados en REPO'}
    diffs = [{'mes': p, 'sii': str(value), 'repo': str(published[p])}
             for p, value in sorted(relevant.items()) if value != published[p]]
    return {'anio': year, 'estado': 'DIFERENCIA' if diffs else 'COINCIDE',
            'meses': len(relevant), 'discrepancias': diffs,
            'ultimas_cotizaciones': {p: str(v) for p, v in sorted(relevant.items())}}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--from-year', type=int, default=2008)
    cli.add_argument('--through-year', type=int, default=2026)
    args = cli.parse_args()
    if not (2008 <= args.from_year <= args.through_year <= 2026):
        raise ValueError('Rango anual inválido')
    legacy = json.loads(probe.LEGACY.read_text(encoding='utf-8'))
    by_month: dict[str, Decimal] = {}
    for row in legacy:
        p, value = row['periodo'], Decimal(str(row['tc_usd_cierre']))
        if p in by_month and by_month[p] != value:
            raise ValueError(f'FX legacy diferente entre bancos para {p}')
        by_month[p] = value
    reports = []
    for year in range(args.from_year, args.through_year + 1):
        # 2013+ usa la vista SII actual: la URL histórica entrega solo un JS
        # de redirección; ir directamente a la URL institucional conocida.
        url = (f'https://www.sii.cl/valores_y_fechas/dolar/dolar{year}.htm'
               if year >= 2013 else URL.format(year))
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=25) as res:
                final = res.url
                raw = res.read(1_000_001)
            if len(raw) > 1_000_000 or not final.startswith('https://www.sii.cl/'):
                raise ValueError('Respuesta fuera de SII o mayor al límite')
            result = compare_year(year, raw.decode('utf-8', errors='replace'), by_month)
            result.update({'url': final, 'sha256_html': hashlib.sha256(raw).hexdigest()})
        except (OSError, ValueError) as exc:
            result = {'anio': year, 'estado': 'SIN_VERIFICAR', 'motivo': str(exc), 'url': url}
        reports.append(result)
        print('::notice title=SII-FX-' + str(year) + '::' + json.dumps(result, ensure_ascii=False))
    summary = {'estado': 'BORRADOR_NO_PUBLICAR', 'informes': reports}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

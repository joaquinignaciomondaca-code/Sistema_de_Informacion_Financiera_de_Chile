"""Reextracción de saldos B1 CMF a informe de revisión, NUNCA publica.

B1 distribuido en ZIP estadísticos tiene 4 campos por moneda (sin total).
MB1 regulatorio tiene además un total: NO se debe aplicar su layout fijo a B1.
Pactos *y préstamos de valores*, saldo consolidado a fecha de corte, NO flujo.
El código del TXT no constituye un RUT ni certifica domicilio de entidad.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from bancos.scripts import probe_repos_zip_cmf as probe
from bancos.scripts.audit_repo_release_gate import AGGREGATES, FOREIGN_AFFILIATES

OUT = probe.ROOT / '.local-data/review/bancos/reconstruccion_cmf'
ACCOUNTS = {'2021': ('1160000', '2160000'), '2022': ('141000000', '243000000')}
CELL = re.compile(r'\s*([+-]?)(\d{1,15})(?:,(\d{2}))?\s*\Z')
QUANT = Decimal('0.01')


def amount(cell: str, old: bool) -> Decimal:
    match = CELL.fullmatch(cell)
    if not match or (old and match[3] is None) or (not old and match[3] not in (None, '00')):
        raise ValueError(f'Celda B1 ilegible o unidad ambigua: {cell!r}')
    value = Decimal(match[2]) + Decimal(match[3] or '0') / 100
    return -value if match[1] == '-' else value


def read_b1(content: bytes, period: str, bank: str) -> dict:
    """Valida encabezado y exige una cuenta raíz por lado y 4 columnas por cuenta."""
    try:
        lines = content.decode('latin-1').splitlines()
    except UnicodeError as exc:
        raise ValueError('B1 no decodificable') from exc
    if not lines or not re.fullmatch(r'\d{1,3}\t[^\t\r\n]+', lines[0]) or int(lines[0].split('\t', 1)[0]) != int(bank):
        raise ValueError(f'Encabezado B1 distinto del código {bank}')
    old = period < '2022-01'
    accounts = ACCOUNTS['2021' if old else '2022']
    found: dict[str, list[str]] = {}
    for line in lines[1:]:
        cells = line.split('\t')
        if cells[0] not in accounts:
            continue
        if cells[0] in found:
            raise ValueError(f'Cuenta duplicada {cells[0]} en {bank}/{period}')
        if len(cells) != 5:
            raise ValueError(f'Cuenta {cells[0]}: se esperan cuatro monedas, hay {len(cells)-1}')
        found[cells[0]] = cells[1:]
    if set(found) != set(accounts):
        raise ValueError(f'Cuentas faltantes {set(accounts) - set(found)} en {bank}/{period}')
    values = {}
    nonzero_raw = {}
    for side, account in zip(('activo', 'pasivo'), accounts):
        components = [amount(c, old) for c in found[account]]
        value = sum(components, Decimal(0)) / (1 if old else 1_000_000)
        nonzero_raw[side] = any(c != 0 for c in components)
        values[side] = str(value.quantize(QUANT, rounding=ROUND_HALF_UP))
    return {'codigo_institucion': bank, 'periodo': period,
            'nombre_encabezado_b1': lines[0].split('\t', 1)[1].strip(),
            'cuenta_activo': accounts[0],
            'cuenta_pasivo': accounts[1], 'repo_activo_mm_clp': values['activo'],
            'repo_pasivo_mm_clp': values['pasivo'], 'importe_crudo_no_cero': nonzero_raw,
            'sha256_b1': hashlib.sha256(content).hexdigest(),
            'clase_para_revision': ('agregado' if bank in AGGREGATES else
                                   'filial_extranjera' if bank in FOREIGN_AFFILIATES else
                                   'codigo_sin_identidad_certificada')}


def extract(blob: bytes, period: str, url: str) -> dict:
    if not probe.trusted_zip(url) or len(blob) > probe.MAX_ZIP or not probe.PERIOD.fullmatch(period):
        raise ValueError('ZIP/período no confiable')
    banks = []
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for info in z.infolist():
            m = probe.BALANCE_TXT.fullmatch(Path(info.filename).name)
            if not m or m[1].lower() != 'b1':
                continue
            if f'{m[2]}-{m[3]}' != period or info.file_size == 0 or info.file_size > probe.MAX_TXT:
                raise ValueError(f'TXT B1 de mes/tamaño incorrecto: {info.filename}')
            banks.append(read_b1(z.read(info), period, m[4]))
    if not banks:
        raise ValueError(f'Sin B1 en ZIP {period}')
    codes = [r['codigo_institucion'] for r in banks]
    if len(codes) != len(set(codes)):
        raise ValueError(f'B1 duplicados en ZIP {period}')
    return {'periodo': period, 'url_zip': url, 'sha256_zip': hashlib.sha256(blob).hexdigest(),
            'filas': sorted(banks, key=lambda r: r['codigo_institucion'])}


def reconcile_system_total(month: dict) -> dict:
    """Control exploratorio: no presuponer que B1 individual suma el total consolidado."""
    rows = month['filas']
    system = [r for r in rows if r['codigo_institucion'] == '999']
    if len(system) != 1:
        raise ValueError(f"Total sistema 999 ausente/duplicado en {month['periodo']}")
    individuals = [r for r in rows if r['codigo_institucion'] not in AGGREGATES |
                   FOREIGN_AFFILIATES and r['codigo_institucion'] != '999']
    result = {'periodo': month['periodo'], 'instituciones': len(individuals)}
    for side in ('activo', 'pasivo'):
        key = f'repo_{side}_mm_clp'
        total = Decimal(system[0][key])
        added = sum((Decimal(r[key]) for r in individuals), Decimal(0))
        result[side] = {'sistema': str(total), 'individuales': str(added),
                        'diferencia_mm_clp': str(total - added)}
    return result


def compare(month: dict, old: dict) -> dict:
    period = month['periodo']
    actual = {r['codigo_institucion']: r for r in month['filas']}
    baseline = {code: r for (p, code), r in old.items() if p == period}
    diffs = []
    for code in sorted(actual.keys() & baseline.keys()):
        for key in ('repo_activo_mm_clp', 'repo_pasivo_mm_clp'):
            source, legacy = Decimal(actual[code][key]), Decimal(str(baseline[code][key]))
            if source != legacy:
                diffs.append({'codigo': code, 'campo': key, 'cmf': str(source), 'legacy': str(legacy)})
    return {'periodo': period, 'comparados': len(actual.keys() & baseline.keys()),
            'diferencias': diffs, 'solo_cmf': sorted(actual.keys() - baseline.keys()),
            'solo_legacy': sorted(baseline.keys() - actual.keys()),
            'filas_cmf': len(actual), 'filas_legacy': len(baseline)}


def run(out: Path = OUT, periods: list[str] | None = None) -> dict:
    found, ambiguous = probe.resolve_links()
    legacy = json.loads(probe.LEGACY.read_text(encoding='utf-8'))
    old = {(r['periodo'], r['codigo_institucion']): r for r in legacy}
    if len(old) != len(legacy):
        raise ValueError('Referencias legacy repetidas')
    requested = sorted(set(periods if periods is not None else (r['periodo'] for r in legacy)))
    if not requested or any(not probe.PERIOD.fullmatch(p) or p not in found or p in ambiguous for p in requested):
        raise ValueError('Mes requerido sin ZIP inequívoco')
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    extra_codes = Counter()
    extra_nonzero = Counter()
    names_by_code: dict[str, set[str]] = {}
    total_checks = []
    for p in requested:
        # Siempre se deja constancia del error, sin confundirlo con un mes sin datos.
        try:
            doc = extract(probe.read_public(found[p], probe.MAX_ZIP), p, found[p])
            comparison = compare(doc, old)
            total_checks.append(reconcile_system_total(doc))
            for row in doc['filas']:
                code = row['codigo_institucion']
                names_by_code.setdefault(code, set()).add(row['nombre_encabezado_b1'])
                if code in comparison['solo_cmf']:
                    extra_codes[code] += 1
                    if any(row['importe_crudo_no_cero'].values()):
                        extra_nonzero[code] += 1
            (out / f'{p}.json').write_text(json.dumps(doc, ensure_ascii=False) + '\n', encoding='utf-8')
            reports.append(comparison)
            print(f'{p}: B1={comparison["filas_cmf"]} legacy={comparison["filas_legacy"]} '
                  f'diferencias={len(comparison["diferencias"])} solo_CMF={len(comparison["solo_cmf"])}', flush=True)
        except (RuntimeError, ValueError, OSError, zipfile.BadZipFile) as exc:
            reports.append({'periodo': p, 'error': str(exc)})
            print(f'{p}: ERROR {exc}', flush=True)
    errors = [r for r in reports if r.get('error')]
    totals = Counter()
    for r in reports:
        for key in ('comparados', 'filas_cmf', 'filas_legacy'):
            totals[key] += r.get(key, 0)
        totals['diferencias'] += len(r.get('diferencias', []))
        totals['solo_cmf'] += len(r.get('solo_cmf', []))
        totals['solo_legacy'] += len(r.get('solo_legacy', []))
    summary = {'estado': 'BORRADOR_NO_PUBLICAR',
               'conciliacion_total_sistema': total_checks,
               'codigos_cmf_fuera_legacy': {code: {'meses': count, 'meses_no_cero': extra_nonzero[code],
                                                   'nombres_b1': sorted(names_by_code[code])}
                                             for code, count in sorted(extra_codes.items())},
               'codigos_cmf_todos': {code: sorted(names) for code, names in sorted(names_by_code.items())},
               'meses_solicitados': requested,
               'meses_descargados': len(reports) - len(errors), 'totales': dict(totals),
               'errores': errors, 'comparaciones': reports,
               'pendiente': ['identidad legal y vigencia por código-mes',
                             'cobertura y propósito de códigos sin fila legacy',
                             'confirmación contable por vigencia y fuente FX independiente']}
    (out / 'resumen.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('periods', nargs='*', help='Meses para calibración; sin argumento recorre todos los legacy')
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    result = run(out=args.output, periods=args.periods or None)
    print('::notice title=Reextracción B1 NO PUBLICADA::' + json.dumps({
        'meses': result['meses_descargados'], 'solicitados': len(result['meses_solicitados']),
        'totales': result['totales'], 'errores': result['errores'][:3]}, ensure_ascii=False))
    return 1 if result['errores'] or result['totales'].get('diferencias') or result['totales'].get('solo_legacy') else 0


if __name__ == '__main__':
    sys.exit(main())

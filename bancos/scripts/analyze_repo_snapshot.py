"""Conciliación local de una copia de revisión B1; solo lectura, NUNCA publica.

Las fuentes son el snapshot temporal transportado desde Actions y el JSON legacy.
El hash de cada ZIP es trazabilidad, NO una prueba criptográfica del contenido
transportado contra la fuente hasta recuperar/verificar los ZIP originales.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

from bancos.scripts import probe_repos_zip_cmf as probe
from bancos.scripts.audit_repo_release_gate import AGGREGATES, FOREIGN_AFFILIATES

DEFAULT = probe.ROOT / '.local-data/review/bancos/reconstruccion_cmf/snapshot_local.json'
MONEY = re.compile(r'-?\d+(?:\.\d+)?\Z')


def analyze(snapshot: dict, legacy: list[dict]) -> dict:
    if snapshot.get('estado') != 'BORRADOR_NO_PUBLICAR' or not isinstance(snapshot.get('meses'), list):
        raise ValueError('Snapshot no validado o incompleto')
    old = {(r['periodo'], r['codigo_institucion']): r for r in legacy}
    if len(old) != len(legacy):
        raise ValueError('Duplicados legacy')
    expected = {r['periodo'] for r in legacy}
    months = snapshot['meses']
    if len(months) != len(expected) or {m[0] for m in months} != expected:
        raise ValueError('Meses faltantes o duplicados en snapshot')
    diffs = []
    unpaired = []
    classes = Counter()
    details = []
    zero_extras = 0
    for month, digest, records in months:
        if not probe.PERIOD.fullmatch(month) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError(f'Mes o SHA inválido: {month}')
        rows = {}
        exact_rows = {}
        for entry in records:
            if len(entry) not in (3, 5) or not re.fullmatch(r'\d{3}', entry[0]) or entry[0] in rows:
                raise ValueError(f'Código inválido/repetido: {month}')
            if any(not isinstance(value, str) or not MONEY.fullmatch(value) for value in entry[1:3]):
                raise ValueError(f'Importe inválido: {month}/{entry[0]}')
            if len(entry) == 5 and any(not isinstance(v, str) or not MONEY.fullmatch(v) for v in entry[3:]):
                raise ValueError(f'Importe exacto inválido: {month}/{entry[0]}')
            rows[entry[0]] = tuple(Decimal(v) for v in entry[1:3])
            if len(entry) == 5:
                exact_rows[entry[0]] = tuple(Decimal(v) for v in entry[3:5])
        if exact_rows and len(exact_rows) != len(rows):
            raise ValueError(f'Precisión mixta: {month}')
        if '999' not in rows:
            raise ValueError(f'Total del sistema ausente: {month}')
        comparable = {code for (p, code) in old if p == month}
        for code in comparable - rows.keys():
            unpaired.append([month, code])
        for code in comparable & rows.keys():
            for side, field in enumerate(('repo_activo_mm_clp', 'repo_pasivo_mm_clp')):
                if rows[code][side] != Decimal(str(old[(month, code)][field])):
                    diffs.append([month, code, field])
        extras = rows.keys() - comparable
        zero_extras += sum(rows[c] == (0, 0) for c in extras if c != '999')
        individuals = [v for code, v in rows.items() if code not in AGGREGATES | FOREIGN_AFFILIATES]
        delta = tuple(rows['999'][i] - sum((v[i] for v in individuals), Decimal(0)) for i in (0, 1))
        excluded = rows.get('507', (Decimal(0), Decimal(0))) if month < '2009-11' else (Decimal(0), Decimal(0))
        residual = tuple(delta[i] + excluded[i] for i in (0, 1))
        exact_delta = None
        if exact_rows:
            exact_individuals = [v for code, v in exact_rows.items()
                                 if code not in AGGREGATES | FOREIGN_AFFILIATES]
            exact_delta = tuple(exact_rows['999'][i] - sum((v[i] for v in exact_individuals), Decimal(0))
                                for i in (0, 1))
        exact_residual = (tuple(exact_delta[i] + exact_rows.get('507', (Decimal(0), Decimal(0)))[i]
                                for i in (0, 1)) if exact_delta is not None else None)
        if exact_delta is not None and all(d == 0 for d in exact_delta):
            category = 'conciliado_exacto_en_fuente'
        elif exact_delta is not None and month < '2009-11' and exact_residual == (0, 0):
            category = 'igual_saldo_507_pre_fusion_en_fuente'
        elif delta == (0, 0):
            category = 'conciliado_exacto_redondeado'
        elif month < '2009-11' and residual == (0, 0):
            category = 'igual_saldo_507_pre_fusion_redondeado'
        elif month >= '2022-01' and all(abs(d) <= Decimal('0.02') for d in delta):
            category = 'diferencia_centésimas_mm_por_investigar'
        else:
            category = 'diferencia_material_sin_explicacion'
        classes[category] += 1
        if category not in ('conciliado_exacto_en_fuente', 'conciliado_exacto_redondeado'):
            details.append({'periodo': month, 'tipo': category,
                            'delta_mm_clp': [str(d) for d in delta],
                            'delta_exact_mm_clp': [str(d) for d in exact_delta] if exact_delta else None,
                            'residuo_si_se_excluye_507': [str(v) for v in residual]})
    return {'estado': 'NO_APROBADO', 'meses': len(months),
            'filas_b1': sum(len(m[2]) for m in months), 'filas_legacy': len(legacy),
            'diferencias_legacy': diffs, 'legacy_sin_b1': unpaired,
            'extras_sin_saldo_redondeado_excluido_999': zero_extras,
            'categorias_total_sistema': dict(classes), 'meses_no_conciliados': details,
            'nota': 'La coincidencia y la tolerancia no acreditan perímetro, identidad, glosa ni FX; no publicable.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=DEFAULT)
    parser.add_argument('--legacy', type=Path, default=probe.LEGACY)
    args = parser.parse_args()
    report = analyze(json.loads(args.snapshot.read_text(encoding='utf-8')),
                     json.loads(args.legacy.read_text(encoding='utf-8')))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

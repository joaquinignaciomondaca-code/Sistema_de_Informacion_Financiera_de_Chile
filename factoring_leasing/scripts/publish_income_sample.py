#!/usr/bin/env python3
"""Publica solo dos resultados acumulados cotejados; no incluye el balance.

El balance previo conserva su archivo y corrida de evidencia independientes.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from publish_structured_sample import FIXED as BALANCE_APPROVED

ROOT = Path(__file__).resolve().parents[2]
RUN = 36337715177
SHA = '1b80e2be68a61885d65cf341210eb84895c1db1e'
APPROVED = {
    ('Factoring', '96655860-1', '2022-06'): (8148312, 7204369),
    ('Leasing', '96809970-1', '2022-09'): (665671, 408471),
}
RESULT_COLUMNS = ('resultado_antes_impuestos_miles_clp',
                  'resultado_operaciones_continuadas_miles_clp')
BASE_COLUMNS = ('segmento', 'rut', 'nombre_en_archivo_y_ficha', 'tipo_entidad',
                'tipo_balance', 'periodo', 'unidad', 'fuente_ficha_cmf',
                'fuente_archivo_cmf', 'sha256_ficha', 'sha256_archivo',
                'alcance_validacion')
WARNING = ('cuatro cuentas de balance y dos de resultado acumulado, esta entidad y este período '
           'solamente; PDF/XBRL no cotejados')
OUTPUT_NAME = 'factoring_leasing_resultados_muestra_cmf.parquet'


def validate(report):
    if report.get('aprobada_muestra') is not True or report.get('errores') or report.get('acciones_run') != RUN or report.get('head_sha') != SHA:
        raise ValueError('Cotejo del resultado no aprobado o procedencia distinta')
    rows = report.get('registros', [])
    if len(rows) != 2 or {(r['segmento'], r['rut'], r['periodo']) for r in rows} != set(APPROVED):
        raise ValueError('Deben ser exactamente dos resultados cotejados')
    for row in rows:
        key = (row['segmento'], row['rut'], row['periodo'])
        if tuple(row.get(c) for c in RESULT_COLUMNS) != APPROVED[key]:
            raise ValueError('Resultado no corresponde a la muestra aprobada')
        if tuple(row.get(c) for c in ('total_activos_miles_clp', 'total_pasivos_miles_clp',
                                      'patrimonio_miles_clp', 'efectivo_miles_clp',
                                      'nombre_en_archivo_y_ficha', 'tipo_entidad', 'sha256_archivo')) != BALANCE_APPROVED[key]:
            raise ValueError('Balance del nuevo cotejo no coincide con el previamente aprobado')
        if row.get('tipo_balance') != 'I' or row.get('unidad') != 'miles de pesos chilenos (CLP)':
            raise ValueError('Moneda o tipo de balance incorrecto')
        if row.get('alcance_validacion') != WARNING:
            raise ValueError('Alcance de validación no aprobado')
        if any(not str(row.get(field, '')).startswith('https://www.cmfchile.cl/institucional/')
               for field in ('fuente_ficha_cmf', 'fuente_archivo_cmf')):
            raise ValueError('Falta fuente oficial')
        if any(token in row['fuente_ficha_cmf'] for token in ('auth=', 'send=')):
            raise ValueError('URL contiene token efímero')
    return rows


def publish(report, output):
    rows = validate(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    records = [{**{c: row[c] for c in BASE_COLUMNS + RESULT_COLUMNS},
                'run_cotejo_actions': RUN,
                'definicion_periodo_resultado': 'acumulado desde 1 de enero hasta cierre indicado'}
               for row in rows]
    pd.DataFrame(records).to_parquet(output, index=False)
    check = pd.read_parquet(output)
    if len(check) != 2 or any(tuple(r[c] for c in RESULT_COLUMNS) != APPROVED[(r['segmento'], r['rut'], r['periodo'])]
                              for r in check.to_dict('records')):
        raise ValueError('Lectura de Parquet no coincide con cotejo aprobado')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/outputs/factoring_leasing' / OUTPUT_NAME)
    args = parser.parse_args()
    print(publish(json.loads(args.report.read_text()), args.output))

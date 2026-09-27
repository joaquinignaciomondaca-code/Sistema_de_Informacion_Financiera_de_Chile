#!/usr/bin/env python3
"""Publica solamente las 2 filas cotejadas del run Actions 36337279448.

No publica balances masivos ni toma cualquier reporte local como aprobación.
La entrada se reconstruye de las anotaciones del job exitoso; la comprobación
fija los campos de auditoría y las cuatro cifras de cada fila.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN = 36337279448
FIXED = {
    ('Factoring', '96655860-1', '2022-06'): (435359519, 376903204, 58456315, 6110582,
        'FACTORING SECURITY S.A.', 'RVEMI', '97b6d8ba7000b31ffbca8ee6195726be7eb2e3c24fae74095205442fa29652fc'),
    ('Leasing', '96809970-1', '2022-09'): (28116046, 21817177, 6298869, 66021,
        'UNIDAD LEASING HABITACIONAL S.A.', 'RGEIN', 'b20cd84591fe9764aa0412812e593369b4178e1568750b4cafadf0000bc431e3'),
}
COLUMNS = ('total_activos_miles_clp', 'total_pasivos_miles_clp', 'patrimonio_miles_clp',
           'efectivo_miles_clp', 'nombre_en_archivo_y_ficha', 'tipo_entidad', 'sha256_archivo')
OUTPUT_NAME = 'factoring_leasing_eeff_muestra_cmf.parquet'


def validate(report):
    if report.get('aprobada_muestra') is not True or report.get('errores') or report.get('acciones_run') != RUN:
        raise ValueError('El cotejo no está aprobado o no corresponde al run aprobado')
    if report.get('head_sha') != '4355226841609feb94e84cd2e30d0977c9decd41':
        raise ValueError('El commit del cotejo no corresponde al run aprobado')
    rows = report.get('registros', [])
    if len(rows) != 2 or {(r['segmento'], r['rut'], r['periodo']) for r in rows} != set(FIXED):
        raise ValueError('Deben ser exactamente las dos filas aprobadas')
    for r in rows:
        key = (r['segmento'], r['rut'], r['periodo'])
        if tuple(r.get(k) for k in COLUMNS) != FIXED[key]:
            raise ValueError(f'Valores de muestra no coinciden: {key}')
        if r.get('tipo_balance') != 'I' or r.get('unidad') != 'miles de pesos chilenos (CLP)':
            raise ValueError('Tipo de balance o moneda no aprobada')
        if r.get('total_activos_miles_clp') != r.get('total_pasivos_miles_clp') + r.get('patrimonio_miles_clp'):
            raise ValueError('Balance no cuadra')
        if any(not r.get(k, '').startswith('https://www.cmfchile.cl/institucional/') for k in ('fuente_ficha_cmf', 'fuente_archivo_cmf')):
            raise ValueError('Falta fuente oficial')
        if 'auth=' in r['fuente_ficha_cmf'] or 'send=' in r['fuente_ficha_cmf']:
            raise ValueError('Token efímero no publicable')
        if r.get('alcance_validacion') != 'cuatro cuentas del balance, esta entidad y este período solamente; PDF/XBRL no cotejados':
            raise ValueError('Advertencia de alcance ausente')
    return rows


def publish(report, output):
    rows = validate(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([{**r, 'run_cotejo_actions': RUN} for r in rows])
    frame.to_parquet(output, index=False)
    back = pd.read_parquet(output)
    assert len(back) == 2
    for r in back.to_dict('records'):
        key = (r['segmento'], r['rut'], r['periodo'])
        assert tuple(r[k] for k in COLUMNS) == FIXED[key]
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/outputs/factoring_leasing' / OUTPUT_NAME)
    args = parser.parse_args()
    print(publish(json.loads(args.report.read_text()), args.output))

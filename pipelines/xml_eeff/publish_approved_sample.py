#!/usr/bin/env python3
"""Publica ÚNICAMENTE las dos filas cotejadas XML vs HTML CMF en el sitio estático.

Entrada: reporte del run 36332905593 reconstruido de sus anotaciones (ver
`docs/notas/cotejo_muestra_xml_ffmm_fi_2026-09-27.md`). El guardarraíl impide
que un reporte posterior, una fila adicional o un valor no cotejado se publique
accidentalmente como si tuviera el mismo nivel de revisión.

Uso: python pipelines/xml_eeff/publish_approved_sample.py \
  --report .local-data/xml_eeff_muestra/cotejo_muestra.json
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN = 36332905593
SAMPLE = {
    ('ffmm', '8490', '2014-12'): {
        'sha256_xml': 'c28c932611b975990c6d5ca88e56d15d7ab24de63f3e07ce9d6aca6e8701f43d',
        'moneda_original': '$$', 'total_activo': 2957448, 'total_pasivo_reportado': 5947,
        'patrimonio_o_activo_neto': 2951501, 'resultado_ejercicio': 3470,
        'definicion_total_pasivo': 'excluye_patrimonio', 'tipo_entidad': 'RGFMU',
        'nombre_xml_historico': 'Fondo Mutuo Cruz del Sur Selectivo',
    },
    ('fi', '7064', '2021-12'): {
        'sha256_xml': '235d5ae96807f189cd2df6fb5e719ab01a26552caf2b576f9b4deced172e742e',
        'moneda_original': 'PROM', 'total_activo': 24887, 'total_pasivo_reportado': 24887,
        'patrimonio_o_activo_neto': 24826, 'resultado_ejercicio': -122,
        'definicion_total_pasivo': 'incluye_patrimonio', 'tipo_entidad': 'FIRES',
        'nombre_xml_historico': 'FONDO DE INVERSION DEUDA LATAM HIGH YIELD',
    },
}
TABLES = {
    'ffmm': 'ffmm_eeff_xml_muestra_cmf',
    'fi': 'fi_eeff_xml_muestra_cmf',
}


def validate(report):
    if report.get('aprobada_muestra') is not True or report.get('errores'):
        raise ValueError('Reporte no aprobado o con errores')
    if report.get('acciones_run') != RUN or not str(report.get('head_sha', '')).startswith('0b93e0f'):
        raise ValueError('El reporte no procede del run de cotejo aprobado')
    rows = report.get('registros', [])
    if len(rows) != 2 or {(r['sector'], r['rut'], r['periodo']) for r in rows} != SAMPLE.keys():
        raise ValueError('Deben ser exactamente las dos filas cotejadas')
    for row in rows:
        key = (row['sector'], row['rut'], row['periodo'])
        for field, expected in SAMPLE[key].items():
            if row.get(field) != expected:
                raise ValueError(f'Dato no cotejado: {key} / {field}: {row.get(field)!r}')
        if row.get('parseo_reparado') is not False or row.get('dv_xml_coincide') is not True:
            raise ValueError('XML reparado o DV discordante: no publicar')
        if row.get('escala') != 'miles' or row.get('calidad') != 'muestra_cotejada_xml_vs_html_cmf':
            raise ValueError('Escala/calidad no cotejada')
        if not row.get('fuente_ficha', '').startswith('https://www.cmfchile.cl/'):
            raise ValueError('Fuente HTML no oficial')
        if not row.get('fuente_xml', '').startswith('https://www.cmfchile.cl/'):
            raise ValueError('Fuente XML no oficial')
        if 'auth=' in row['fuente_xml'] or 'send=' in row['fuente_xml']:
            raise ValueError('URL incluye token efímero')
        if not row.get('nombre_registro_actual') or not row.get('nombre_xml_historico'):
            raise ValueError('Falta el nombre actual o histórico')
    return rows


def publish(report, outdir):
    rows = validate(report)
    outdir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for sector in ('ffmm', 'fi'):
        r = next(r for r in rows if r['sector'] == sector)
        # No renombrar PROM a CLP: la ficha indica miles de dólares.
        unidad = 'miles de pesos (CMF)' if sector == 'ffmm' else 'miles de dólares (CMF)'
        pasivo_sin_patrimonio = (r['total_pasivo_reportado'] if sector == 'ffmm'
                                 else r['total_activo'] - r['patrimonio_o_activo_neto'])
        record = {
            'run_fondo': r['rut'], 'tipo_entidad': r['tipo_entidad'], 'periodo': r['periodo'],
            'nombre_xml_historico': r['nombre_xml_historico'],
            'nombre_registro_actual': r['nombre_registro_actual'],
            'moneda_original_xml': r['moneda_original'], 'unidad_segun_ficha_cmf': unidad,
            'total_activo': float(r['total_activo']),
            'total_pasivo_reportado': float(r['total_pasivo_reportado']),
            'definicion_total_pasivo': r['definicion_total_pasivo'],
            'pasivo_sin_patrimonio': float(pasivo_sin_patrimonio),
            'patrimonio_o_activo_neto': float(r['patrimonio_o_activo_neto']),
            'resultado_ejercicio': float(r['resultado_ejercicio']),
            'codigo_resultado_xml': r['codigo_resultado'],
            'dv_xml_coincide': True, 'parseo_reparado': False,
            'fuente_ficha_cmf': r['fuente_ficha'], 'fuente_xml_cmf': r['fuente_xml'],
            'sha256_xml': r['sha256_xml'], 'run_cotejo_actions': RUN,
            'alcance_validacion': 'solo esta fila: cuatro importes XML vs HTML CMF',
        }
        path = outdir / sector / (TABLES[sector] + '.parquet')
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([record]).to_parquet(path, index=False)
        readback = pd.read_parquet(path)
        assert len(readback) == 1
        assert readback.loc[0, 'total_activo'] == SAMPLE[(sector, r['rut'], r['periodo'])]['total_activo']
        assert readback.loc[0, 'pasivo_sin_patrimonio'] + readback.loc[0, 'patrimonio_o_activo_neto'] == readback.loc[0, 'total_activo']
        outputs.append(path)
    return outputs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--outdir', type=Path, default=ROOT / 'docs' / 'outputs')
    args = p.parse_args()
    for path in publish(json.loads(args.report.read_text(encoding='utf-8')), args.outdir):
        print(f'{path}: 1 fila cotejada')


if __name__ == '__main__':
    main()

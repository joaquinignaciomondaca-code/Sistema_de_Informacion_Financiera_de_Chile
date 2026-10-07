"""CSV originales BDP o ZIP locales -> staging privado, nunca docs/outputs.

Conserva los 18 campos como texto: no adivina escalas ni tipos numéricos.
Un directorio nuevo por corrida evita mezclar revisiones de un mismo período.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLUMNS = ('fecha afp tipo_de_fondo tipo_de_instrumento nemotecnico_del_instrumento '
           'nombre_del_emisor nacionalidad_del_emisor unidad_de_reajuste_de_moneda '
           'unidades precio inversion grupo_economico moneda_contrato_forward '
           'moneda_objeto_forward precio_ejercicio_forward plazo_economico '
           'tasa_pactada_del_fondo_swap tasa_pactada_de_la_contraparte_swap').split()
LINEAGE = ['archivo_fuente', 'sha256_archivo_fuente', 'numero_fila_fuente',
           'id_registro_fuente', 'fecha_ingestion', 'version_esquema']


def mapping():
    config = json.loads((ROOT / 'pensiones/config/familias_bdp.json').read_text())
    result = {}
    for family, codes in config['familias'].items():
        for code in codes.split():
            if code in result:
                raise ValueError('Código en dos familias: ' + code)
            result[code] = ('afp_' if family.startswith('derivados_') else 'afp_cartera_') + family
    return result


def sha256(stream, deadline=None):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        if deadline is not None and time.monotonic() > deadline:
            raise TimeoutError("Tiempo agotado durante lectura de fuente")
        h.update(block)
    return h.hexdigest()


def extract(inputs, output, encoding='utf-8-sig', max_archivos=50, minutos=60):
    import pyarrow as pa
    import pyarrow.parquet as pq
    output = Path(output).resolve()
    private = (ROOT / '.local-data').resolve()
    if private not in output.parents:
        raise ValueError('El staging debe estar dentro de .local-data/')
    if output.exists():
        raise ValueError('Use un directorio nuevo por corrida')
    if max_archivos < 1 or not math.isfinite(minutos) or minutos <= 0:
        raise ValueError('Límites deben ser positivos')
    output.mkdir(parents=True)
    deadline = time.monotonic() + minutos * 60
    codes = mapping()
    schema = pa.schema([(c, pa.string()) for c in COLUMNS + LINEAGE])
    report = {'version': 1, 'estado': 'incompleto', 'publicable': False,
              'motivo': 'Pendientes cotejo SP, formatos numéricos y permiso de redistribución',
              'fuentes': [], 'filas': 0, 'familias': {}, 'cobertura': {}, 'particiones': []}
    counts, coverage = Counter(), Counter()
    seen = set()
    processed = 0
    stamp = datetime.now(timezone.utc).isoformat()

    def consume(opener, label):
        nonlocal processed
        if processed >= max_archivos:
            raise ValueError('Límite de archivos excedido; corrida incompleta')
        processed += 1
        with opener() as raw:
            digest = sha256(raw, deadline)
        if digest in seen:
            raise ValueError('CSV repetido (mismo SHA256)')
        seen.add(digest)
        buffers = defaultdict(list)
        source_rows = 0
        def flush(family):
            rows = buffers[family]
            if not rows:
                return
            dest = output / family / f'part-{len(report["particiones"]):06d}.parquet'
            dest.parent.mkdir(exist_ok=True)
            pq.write_table(pa.Table.from_pylist(rows, schema=schema), dest, compression='zstd')
            with dest.open('rb') as saved:
                part_hash = sha256(saved, deadline)
            report['particiones'].append({'path': str(dest.relative_to(output)), 'filas': len(rows),
                                          'familia': family, 'sha256': part_hash})
            rows.clear()
        with opener() as raw, io.TextIOWrapper(raw, encoding=encoding, newline='') as text:
            reader = csv.reader(text, delimiter=';', strict=True)
            header = next(reader, [])
            header = [s.strip().lower() for s in header]
            header = ['tasa_pactada_de_la_contraparte_swap' if s == 'tasa_pactada_de_la_contraparte_s' else s for s in header]
            if header != COLUMNS:
                raise ValueError('Cabecera BDP inesperada: ' + label)
            for number, values in enumerate(reader, 2):
                if time.monotonic() > deadline:
                    raise TimeoutError('Tiempo agotado; corrida incompleta')
                if len(values) != len(COLUMNS):
                    raise ValueError(f'Cantidad de campos inválida: {label}:{number}')
                row = dict(zip(COLUMNS, values))
                if not all(row[c].strip() for c in COLUMNS[:4]):
                    raise ValueError(f'Clave de cobertura vacía: {label}:{number}')
                family = codes.get(row['tipo_de_instrumento'].strip(), 'otros_no_clasificados')
                row.update(archivo_fuente=label, sha256_archivo_fuente=digest,
                           numero_fila_fuente=str(number), id_registro_fuente=f'{digest}:{number}',
                           fecha_ingestion=stamp, version_esquema='bdp-texto-v1')
                buffers[family].append(row)
                counts[family] += 1
                coverage[json.dumps(values[:4], ensure_ascii=False)] += 1
                source_rows += 1
                if len(buffers[family]) >= 10000:
                    flush(family)
        for family in buffers:
            flush(family)
        if not source_rows:
            raise ValueError('CSV sin observaciones: ' + label)
        with opener() as raw:
            if sha256(raw, deadline) != digest:
                raise ValueError('La fuente cambió durante la lectura')
        report['fuentes'].append({'archivo': label, 'sha256': digest, 'filas': source_rows})

    try:
        for source in map(Path, inputs):
            if source.suffix.lower() == '.zip':
                with zipfile.ZipFile(source) as archive:
                    members = [m for m in archive.infolist() if m.filename.lower().endswith('.csv')]
                    if not members:
                        raise ValueError('ZIP sin CSV')
                    for member in members:
                        if member.file_size > 2_000_000_000:
                            raise ValueError('Miembro ZIP demasiado grande')
                        consume(lambda m=member: archive.open(m), f'{source.name}!{member.filename}')
            elif source.suffix.lower() == '.csv':
                consume(lambda s=source: s.open('rb'), source.name)
            else:
                raise ValueError('Sólo CSV/ZIP originales; no XLSX del espejo')
        if not processed:
            raise ValueError('No hay fuentes')
        report['estado'] = 'cuarentena' if counts['otros_no_clasificados'] else 'staging_completo'
    finally:
        report.update(filas=sum(counts.values()), familias=dict(counts), cobertura=dict(coverage))
        (output / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inputs', nargs='+', type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--encoding', choices=['utf-8-sig', 'cp1252'], default='utf-8-sig')
    p.add_argument('--max-archivos', type=int, default=50)
    p.add_argument('--minutos', type=float, default=60)
    a = p.parse_args()
    extract(a.inputs, a.output, a.encoding, a.max_archivos, a.minutos)

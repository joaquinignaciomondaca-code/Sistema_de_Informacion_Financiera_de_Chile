"""Auditoría sin red del staging; no concede autorización para publicar."""
import argparse
import json
from collections import Counter
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from extraer_carteras_afp import COLUMNS, LINEAGE, mapping, sha256


def audit(directory):
    directory = Path(directory).resolve()
    report = json.loads((directory / 'audit.json').read_text())
    if report['estado'] != 'staging_completo' or report.get('publicable') is not False:
        raise ValueError('Corrida incompleta o con códigos en cuarentena')
    counts, coverage, sources = Counter(), Counter(), Counter()
    ids, paths = set(), set()
    codes = mapping()
    expected = {s['sha256']: s for s in report['fuentes']}
    if len(expected) != len(report['fuentes']):
        raise ValueError('Fuentes duplicadas en inventario')
    for part in report['particiones']:
        path = (directory / part['path']).resolve()
        if directory not in path.parents or path in paths:
            raise ValueError('Ruta de partición inválida o repetida')
        paths.add(path)
        with path.open('rb') as raw:
            if sha256(raw) != part['sha256']:
                raise ValueError('Hash de partición incorrecto')
        parquet = pq.ParquetFile(path)
        if parquet.schema_arrow != pa.schema([(c, pa.string()) for c in COLUMNS + LINEAGE]):
            raise ValueError('Esquema inesperado')
        n = 0
        for batch in parquet.iter_batches(batch_size=10000):
            for row in batch.to_pylist():
                source = expected.get(row['sha256_archivo_fuente'])
                if (source is None or row['archivo_fuente'] != source['archivo']
                        or not str(row['numero_fila_fuente']).isdigit()
                        or not 2 <= int(row['numero_fila_fuente']) <= source['filas'] + 1
                        or row['version_esquema'] != 'bdp-texto-v1'
                        or not row['fecha_ingestion']
                        or not all(row[c] and row[c].strip() for c in COLUMNS[:4])):
                    raise ValueError('Metadatos de fuente inválidos')
                rid = row['id_registro_fuente']
                if rid in ids or rid != f"{row['sha256_archivo_fuente']}:{row['numero_fila_fuente']}":
                    raise ValueError('Linaje duplicado o inválido')
                ids.add(rid)
                if codes.get(row['tipo_de_instrumento'].strip()) != part['familia']:
                    raise ValueError('Familia incorrecta')
                sources[row['sha256_archivo_fuente']] += 1
                counts[part['familia']] += 1
                coverage[json.dumps([row[c] for c in COLUMNS[:4]], ensure_ascii=False)] += 1
                n += 1
        if n != part['filas']:
            raise ValueError('Conteo de partición incorrecto')
    expected_sources = {s['sha256']: s['filas'] for s in report['fuentes']}
    if (set(directory.rglob('*.parquet')) != paths or dict(sources) != expected_sources
            or dict(counts) != report['familias'] or dict(coverage) != report['cobertura']
            or sum(counts.values()) != report['filas'] or not counts):
        raise ValueError('Falla conservación/cobertura/inventario')
    return {'filas': sum(counts.values()), 'familias': len(counts), 'publicable': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(audit(parser.parse_args().directory)))

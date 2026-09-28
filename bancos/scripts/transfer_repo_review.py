"""Transporta una revisión B1 comprimida por anotaciones Actions, NUNCA publica datos.

Usar sólo para análisis local cuando la descarga de artefactos Actions falla.
Las anotaciones no son fuente primaria: conservan hashes ZIP de la corrida CMF.
El límite práctico de 10 anotaciones por job exige ejecutar tres lotes; el lector
local rechaza partes faltantes, duplicadas o mezcladas. Se conservan hashes ZIP,
pero el transporte no verifica por sí solo el ZIP original.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
import re
import sys
from pathlib import Path

from bancos.scripts.rebuild_repo_from_cmf import OUT

PREFIX = 'REPO-REV-V3'
CHUNK_SIZE = 2900
MAX_CHUNKS = 10


def encode_review(folder: Path) -> list[str]:
    summary = json.loads((folder / 'resumen.json').read_text(encoding='utf-8'))
    requested = summary['meses_solicitados']
    if (summary['errores'] or summary['meses_descargados'] != len(requested)
            or summary['totales']['diferencias'] or summary['totales']['solo_legacy']):
        raise ValueError('Revisión incompleta: no transferir como serie cerrada')
    docs = []
    for month in requested:
        doc = json.loads((folder / f'{month}.json').read_text(encoding='utf-8'))
        if doc['periodo'] != month or len(doc['filas']) == 0:
            raise ValueError(f'Mes inválido {month}')
        docs.append([month, doc['sha256_zip'], [
            [r['codigo_institucion'], r['repo_activo_mm_clp'], r['repo_pasivo_mm_clp'],
             r['importe_exact_mm_clp']['activo'], r['importe_exact_mm_clp']['pasivo']]
            for r in doc['filas']
        ]])
    payload = {'estado': 'BORRADOR_NO_PUBLICAR', 'meses': docs}
    compressed = lzma.compress(json.dumps(payload, ensure_ascii=False,
                                          separators=(',', ':')).encode('utf-8'), preset=9)
    digest = hashlib.sha256(compressed).hexdigest()
    encoded = base64.b64encode(compressed).decode('ascii')
    pieces = [encoded[i:i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]
    if not pieces or len(pieces) > MAX_CHUNKS:
        raise ValueError(f'{len(pieces)} anotaciones: supera tope; usar transporte por lotes')
    return [f'{PREFIX}:{digest}:{i + 1}/{len(pieces)}:{piece}'
            for i, piece in enumerate(pieces)]


def decode_review(messages: list[str]) -> dict:
    items = {}
    digest = None
    count = None
    pattern = re.compile(rf'^{PREFIX}:([0-9a-f]{{64}}):(\d+)/(\d+):([A-Za-z0-9+/=]+)$')
    for message in messages:
        match = pattern.fullmatch(message)
        if not match:
            raise ValueError('Parte de revisión ilegible')
        sha, index, total, fragment = match.groups()
        index, total = int(index), int(total)
        if (digest is not None and sha != digest) or (count is not None and total != count):
            raise ValueError('Se mezclaron revisiones distintas')
        if not (1 <= index <= total <= MAX_CHUNKS) or index in items:
            raise ValueError('Parte de revisión duplicada o fuera de rango')
        digest, count = sha, total
        items[index] = fragment
    if not count or len(items) != count:
        raise ValueError('Revisión truncada o sin anotaciones')
    blob = base64.b64decode(''.join(items[i] for i in range(1, count + 1)), validate=True)
    if hashlib.sha256(blob).hexdigest() != digest:
        raise ValueError('SHA-256 de revisión no coincide')
    doc = json.loads(lzma.decompress(blob))
    if doc.get('estado') != 'BORRADOR_NO_PUBLICAR' or not isinstance(doc.get('meses'), list):
        raise ValueError('Revisión incompleta o no segregada')
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=OUT)
    parser.add_argument('--decode-annotations', type=Path,
                        help='JSON de endpoint /check-runs/{id}/annotations (no descargar ZIP)')
    parser.add_argument('--output', type=Path, default=OUT / 'snapshot_local.json')
    args = parser.parse_args()
    if args.decode_annotations:
        annotations = json.loads(args.decode_annotations.read_text(encoding='utf-8'))
        messages = [a['message'] for a in annotations if str(a.get('title', '')).startswith(PREFIX)]
        doc = decode_review(messages)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(doc, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'Revisión local NO PUBLICADA: {len(doc["meses"])} meses en {args.output}')
    else:
        for i, message in enumerate(encode_review(args.folder), start=1):
            print(f'::notice title={PREFIX}-{i:02d}::{message}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f'Transferencia de revisión incompleta: {exc}', file=sys.stderr)
        sys.exit(1)

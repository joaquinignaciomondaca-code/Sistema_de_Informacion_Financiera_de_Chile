"""Reconstruye en el laboratorio un snapshot B1 desde un run Actions existente.

Usa gh para descargar SOLO metadatos/anotaciones de tres jobs; NO descarga ZIP,
NO consulta CMF, NO modifica datos publicados ni obtiene credenciales del usuario.
Rechaza meses, jobs o fragmentos incompletos; salida .local-data/ ignorada por git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from bancos.scripts import probe_repos_zip_cmf as probe
from bancos.scripts.transfer_repo_review import PREFIX, decode_review

OUT = probe.ROOT / '.local-data/review/bancos/reconstruccion_cmf/snapshot_hidratado.json'
JOB = re.compile(r'^transfer_review \(([012])\)$')


def fetch_json(endpoint: str) -> object:
    # gh usa la autenticación del sandbox; no copiarla al repo ni a anotaciones.
    result = subprocess.run(['gh', 'api', endpoint], check=True, text=True,
                            capture_output=True, timeout=45)
    return json.loads(result.stdout)


def assemble_jobs(jobs: list[dict], annotations: dict[int, list[dict]],
                  expected: set[str]) -> dict:
    shards = {}
    for job in jobs:
        match = JOB.fullmatch(job['name'])
        if not match:
            continue
        index = int(match[1])
        if index in shards or job['conclusion'] != 'success':
            raise ValueError(f'Lote repetido o fallido: {index}')
        messages = [a['message'] for a in annotations[job['id']]
                    if a.get('title', '').startswith(PREFIX)]
        shards[index] = decode_review(messages)
    if set(shards) != {0, 1, 2}:
        raise ValueError(f'Faltan lotes B1: {sorted(set(range(3)) - shards.keys())}')
    months = {}
    for shard, doc in shards.items():
        for month in doc['meses']:
            p, digest, rows = month
            if (not probe.PERIOD.fullmatch(p) or not re.fullmatch(r'[0-9a-f]{64}', digest)
                    or p in months or not isinstance(rows, list) or not rows):
                raise ValueError(f'Mes/ZIP duplicado o inválido: {p}')
            if p not in expected:
                raise ValueError(f'Mes inesperado: {p}')
            months[p] = month
    if set(months) != expected:
        raise ValueError(f'Cobertura incompleta: faltan {sorted(expected - months.keys())}')
    return {'estado': 'BORRADOR_NO_PUBLICAR', 'meses': [months[k] for k in sorted(months)]}


def hydrate(run_id: int, output: Path = OUT) -> dict:
    if run_id <= 0:
        raise ValueError('run_id inválido')
    root = 'repos/joaquinignaciomondaca-code/monitor-financiero-chile'
    run = fetch_json(f'{root}/actions/runs/{run_id}')
    if run.get('conclusion') != 'success' or run.get('head_branch') != 'arena/01a0e08b-monitor-financiero-chile':
        raise ValueError('Run incompleto o de otra rama')
    jobs = fetch_json(f'{root}/actions/runs/{run_id}/jobs?per_page=100')['jobs']
    relevant = [j for j in jobs if JOB.fullmatch(j['name'])]
    if len(jobs) >= 100 or len(relevant) != 3:
        raise ValueError('Jobs paginados, duplicados o faltantes')
    annotations = {j['id']: fetch_json(f'{root}/check-runs/{j["id"]}/annotations?per_page=50')
                   for j in relevant}
    legacy = json.loads(probe.LEGACY.read_text(encoding='utf-8'))
    snapshot = assemble_jobs(jobs, annotations, {r['periodo'] for r in legacy})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'NO PUBLICADO: {len(snapshot["meses"])} meses; copia {output}; '
          f'SHA256 {hashlib.sha256(output.read_bytes()).hexdigest()}')
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id', type=int)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    hydrate(args.run_id, args.output)


if __name__ == '__main__':
    main()

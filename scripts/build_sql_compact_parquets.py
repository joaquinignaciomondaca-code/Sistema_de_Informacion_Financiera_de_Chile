#!/usr/bin/env python3
"""Genera Parquet compactos de uso exclusivo para las vistas SQL de DuckDB-Wasm.

Los artefactos de ``docs/outputs/sql_query/`` reducen el número de archivos
remotos que DuckDB debe abrir al preparar una vista. No son archivos de descarga:
los manifiestos públicos y el catálogo de Descargas siguen apuntando a las
particiones originales, con sus períodos, filtros y conteos.

Uso:
    python scripts/build_sql_compact_parquets.py
    python scripts/build_sql_compact_parquets.py --only bancos_balance ffmm_cartera_nacional
    python scripts/build_sql_compact_parquets.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Iterable

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DATASETS: dict[str, dict[str, str]] = {
    "bancos_balance": {
        "source_manifest": "docs/outputs/bancos/balance_b1_b2/manifest.json",
        "file": "docs/outputs/sql_query/bancos_balance.parquet",
        "description": "Copia compacta SQL de bancos_balance: solo familias CMF B1 y B2; no es un archivo de descarga.",
    },
    "bancos_resultados": {
        "source_manifest": "docs/outputs/bancos/resultados_r1/manifest.json",
        "file": "docs/outputs/sql_query/bancos_resultados.parquet",
        "description": "Copia compacta SQL de bancos_resultados: solo familia CMF R1; no es un archivo de descarga.",
    },
    "ffmm_cartera_nacional": {
        "source_manifest": "docs/outputs/ffmm/cartera_nacional/manifest.json",
        "file": "docs/outputs/sql_query/ffmm_cartera_nacional.parquet",
        "description": "Copia compacta SQL de la cartera nacional de fondos mutuos; no es un archivo de descarga.",
    },
    "seguros_acciones": {
        "source_manifest": "docs/outputs/seguros/acciones/manifest.json",
        "file": "docs/outputs/sql_query/seguros_acciones.parquet",
        "description": "Copia compacta SQL de acciones de aseguradoras; no es un archivo de descarga.",
    },
}
FORMAT_VERSION = 1
BATCH_ROWS = 131_072


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_repo_path(value: object, root: Path) -> Path:
    if not isinstance(value, str) or not value or value.startswith("/"):
        raise ValueError(f"Ruta no relativa en manifiesto: {value!r}")
    rel = Path(value)
    if ".." in rel.parts:
        raise ValueError(f"Ruta fuera de docs/ en manifiesto: {value!r}")
    path = (root / "docs" / rel).resolve()
    docs = (root / "docs").resolve()
    if path != docs and docs not in path.parents:
        raise ValueError(f"Ruta fuera de docs/ en manifiesto: {value!r}")
    return path


def load_inputs(root: Path, name: str, spec: dict[str, str]) -> tuple[dict, list[tuple[str, Path, int, str]], object]:
    source_manifest_path = root / spec["source_manifest"]
    if not source_manifest_path.is_file():
        raise FileNotFoundError(f"Falta manifiesto de origen: {source_manifest_path.relative_to(root)}")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    file_entries = source_manifest.get("files")
    if not isinstance(file_entries, list) or not file_entries:
        raise ValueError(f"{name}: el manifiesto no contiene archivos")

    source_files: list[tuple[str, Path, int, str]] = []
    schema = None
    total_rows = 0
    for entry in file_entries:
        rel = entry.get("file") if isinstance(entry, dict) else entry
        path = safe_repo_path(rel, root)
        if not path.is_file():
            raise FileNotFoundError(f"{name}: falta la partición {path.relative_to(root)}")
        parquet = pq.ParquetFile(path)
        current_schema = parquet.schema_arrow
        if schema is None:
            schema = current_schema
        elif not schema.remove_metadata().equals(current_schema.remove_metadata(), check_metadata=False):
            raise ValueError(f"{name}: esquema incompatible en {rel}; no se compactan columnas distintas")
        rows = int(parquet.metadata.num_rows)
        total_rows += rows
        source_files.append((Path(rel).as_posix(), path, rows, sha256(path)))

    declared_rows = source_manifest.get("total_records")
    if declared_rows is not None and int(declared_rows) != total_rows:
        raise ValueError(f"{name}: manifiesto declara {declared_rows:,} filas, pero sus Parquet suman {total_rows:,}")
    return source_manifest, source_files, schema


def sidecar_for(
    root: Path,
    name: str,
    spec: dict[str, str],
    source_manifest: dict,
    source_files: list[tuple[str, Path, int, str]],
    schema,
    output_path: Path,
) -> dict:
    return {
        "format_version": FORMAT_VERSION,
        "dataset": name,
        "description": spec["description"],
        "purpose": "SQL-only; no forma parte del catálogo de descargas",
        "source_manifest": Path(spec["source_manifest"]).relative_to("docs").as_posix(),
        "source_updated_at": source_manifest.get("updated_at"),
        "source_files": [
            {"path": rel, "records": rows, "sha256": digest}
            for rel, _path, rows, digest in source_files
        ],
        "file": Path(spec["file"]).relative_to("docs").as_posix(),
        "records": sum(item[2] for item in source_files),
        "bytes": output_path.stat().st_size,
        "sha256": sha256(output_path),
        "schema": [
            {"name": field.name, "type": str(field.type)}
            for field in schema
        ],
    }


def write_compact(root: Path, name: str, spec: dict[str, str]) -> dict:
    source_manifest, source_files, schema = load_inputs(root, name, spec)
    target = root / spec["file"]
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix=target.name + ".", suffix=".tmp")
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with pq.ParquetWriter(
            temporary,
            schema,
            compression="zstd",
            version="2.6",
            write_statistics=True,
        ) as writer:
            for _rel, source_path, _rows, _digest in source_files:
                parquet = pq.ParquetFile(source_path)
                for batch in parquet.iter_batches(batch_size=BATCH_ROWS):
                    writer.write_batch(batch, row_group_size=BATCH_ROWS)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)

    sidecar_path = target.with_suffix(".manifest.json")
    sidecar = sidecar_for(root, name, spec, source_manifest, source_files, schema, target)
    atomic_json(sidecar_path, sidecar)
    return sidecar


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def check_compact(root: Path, name: str, spec: dict[str, str]) -> list[str]:
    problems = []
    target = root / spec["file"]
    sidecar_path = target.with_suffix(".manifest.json")
    if not target.is_file():
        return [f"falta {spec['file']}"]
    if not sidecar_path.is_file():
        return [f"falta {sidecar_path.relative_to(root)}"]
    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        source_manifest, source_files, schema = load_inputs(root, name, spec)
        expected_paths = [
            {"path": rel, "records": rows, "sha256": digest}
            for rel, _path, rows, digest in source_files
        ]
        expected_schema = [{"name": field.name, "type": str(field.type)} for field in schema]
        parquet = pq.ParquetFile(target)
        output_schema = parquet.schema_arrow
        checks = {
            "format_version": FORMAT_VERSION,
            "dataset": name,
            "description": spec["description"],
            "purpose": "SQL-only; no forma parte del catálogo de descargas",
            "source_manifest": Path(spec["source_manifest"]).relative_to("docs").as_posix(),
            "source_updated_at": source_manifest.get("updated_at"),
            "source_files": expected_paths,
            "file": Path(spec["file"]).relative_to("docs").as_posix(),
            "records": sum(item[2] for item in source_files),
            "bytes": target.stat().st_size,
            "sha256": sha256(target),
            "schema": expected_schema,
        }
        for key, expected in checks.items():
            if sidecar.get(key) != expected:
                problems.append(f"{name}: sidecar {key} desactualizado")
        if int(parquet.metadata.num_rows) != checks["records"]:
            problems.append(f"{name}: filas del compacto no coinciden con las particiones")
        if not schema.remove_metadata().equals(output_schema.remove_metadata(), check_metadata=False):
            problems.append(f"{name}: esquema del compacto no coincide con las particiones")
    except Exception as exc:
        problems.append(f"{name}: {exc}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=sorted(DATASETS), help="construir o revisar solo estos objetos")
    parser.add_argument("--check", action="store_true", help="no escribe; falla si el compacto o su huella están desactualizados")
    args = parser.parse_args()
    selected: Iterable[str] = args.only or DATASETS.keys()
    errors: list[str] = []
    summaries = []
    for name in selected:
        spec = DATASETS[name]
        if args.check:
            problems = check_compact(ROOT, name, spec)
            errors.extend(problems)
            if not problems:
                sidecar = json.loads((ROOT / spec["file"]).with_suffix(".manifest.json").read_text(encoding="utf-8"))
                summaries.append(f"{name}: {sidecar['records']:,} filas, {sidecar['bytes']:,} bytes")
        else:
            sidecar = write_compact(ROOT, name, spec)
            summaries.append(f"{name}: {sidecar['records']:,} filas, {sidecar['bytes']:,} bytes")
    if errors:
        print("PARQUET SQL COMPACTOS: " + "; ".join(errors[:20]))
        print("Ejecuta python scripts/build_sql_compact_parquets.py")
        return 1
    print("PARQUET SQL COMPACTOS: " + " · ".join(summaries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

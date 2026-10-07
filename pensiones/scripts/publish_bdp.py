"""Publica Parquet BDP sólo si pasan evidencia, auditoría y política versionada.

El contenido publicado es el CSV fuente preservado como VARCHAR. No infiere fecha,
escala o unidad. La configuración del repositorio mantiene el gate cerrado; una
variable/secreto/entrada de Actions no puede sustituir la evidencia requerida.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

try:
    from .bdp_common import (
        PRIVATE_ROOT,
        ROOT,
        atomic_json,
        load_family_mapping,
        sha256_file,
    )
    from .check_publicacion_bdp import DEFAULT_POLICY, evaluate
except ImportError:  # ejecución directa desde pensiones/scripts/
    from bdp_common import PRIVATE_ROOT, ROOT, atomic_json, load_family_mapping, sha256_file  # type: ignore
    from check_publicacion_bdp import DEFAULT_POLICY, evaluate  # type: ignore

DEFAULT_STAGING = PRIVATE_ROOT / "pensiones/bdp/staging"
DEFAULT_PUBLIC_ROOT = ROOT / "docs/outputs/pensiones/bdp"
PUBLISHER_MARKER = ".bdp_publication.json"


def _check_output_root(output_root: Path) -> Path:
    resolved = Path(output_root).resolve()
    public_parent = (ROOT / "docs/outputs/pensiones").resolve()
    if public_parent not in resolved.parents and PRIVATE_ROOT not in resolved.parents:
        raise ValueError("Destino permitido sólo en docs/outputs/pensiones/ o en .local-data/ para pruebas")
    if resolved == public_parent or resolved == ROOT / "docs/outputs":
        raise ValueError("Destino debe ser el subdirectorio bdp, no sobrescribir el sector")
    return resolved


def _publish_tree(staging: Path, output_root: Path, audit_result: dict[str, Any]) -> dict[str, Any]:
    staging = Path(staging).resolve()
    output_root = _check_output_root(output_root)
    stage_manifest = json.loads((staging / "manifest.json").read_text(encoding="utf-8"))
    mapping = load_family_mapping()
    table_parts: dict[str, list[dict[str, Any]]] = {}
    totals: Counter[str] = Counter()
    for source_key, revision_id in sorted(stage_manifest["active_sources"].items()):
        revision = stage_manifest["revisions"][revision_id]
        if not revision.get("complete") or revision.get("source_key") != source_key:
            raise ValueError(f"Revisión activa inválida: {source_key}")
        for part in revision["parts"]:
            family = part["family"]
            if family not in set(mapping.values()):
                raise ValueError(f"Familia fuera del catálogo: {family}")
            source_part = (staging / part["path"]).resolve()
            if staging not in source_part.parents or not source_part.is_file():
                raise ValueError(f"Partición staging inválida: {part['path']}")
            if sha256_file(source_part) != part["sha256"]:
                raise ValueError(f"Hash cambió antes de publicar: {part['path']}")
            table_parts.setdefault(family, []).append(
                {
                    "source_path": source_part,
                    "source_key": source_key,
                    "revision_id": revision_id,
                    "name": source_part.name,
                    "rows": int(part["rows"]),
                    "sha256": part["sha256"],
                }
            )
            totals[family] += int(part["rows"])

    if not table_parts or sum(totals.values()) != audit_result["filas"]:
        raise ValueError("El plan de publicación no conserva todas las filas activas")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    temp_root = output_root.parent / f".bdp-publish-tmp-{uuid.uuid4().hex}"
    backup_root = output_root.parent / f".bdp-publish-old-{uuid.uuid4().hex}"
    temp_root.mkdir()
    stamp = datetime.now(timezone.utc).isoformat()
    tables = []
    try:
        for family, parts in sorted(table_parts.items()):
            table_dir = temp_root / family
            table_dir.mkdir(parents=True)
            file_records = []
            for part in parts:
                destination = table_dir / f"{part['revision_id']}-{part['name']}"
                shutil.copyfile(part["source_path"], destination)
                digest = sha256_file(destination)
                if digest != part["sha256"]:
                    raise ValueError(f"Hash de publicación distinto: {destination.name}")
                metadata = pq.ParquetFile(destination).metadata
                if metadata.num_rows != part["rows"]:
                    raise ValueError(f"Conteo Parquet distinto en destino: {destination.name}")
                # El path público es estable también en pruebas con output_root
                # privado; el publicador real siempre instala bajo docs/outputs/.
                relative_to_docs = Path("outputs/pensiones/bdp") / family / destination.name
                file_records.append(
                    {
                        "path": relative_to_docs.as_posix(),
                        "rows": part["rows"],
                        "bytes": destination.stat().st_size,
                        "sha256": digest,
                        "source_key": part["source_key"],
                        "source_revision": part["revision_id"],
                    }
                )
            table_manifest = {
                "version": 1,
                "table": family,
                "total_records": sum(item["rows"] for item in file_records),
                "updated_at": stamp,
                "files": [item["path"] for item in file_records],
                "files_detail": file_records,
                "schema": "bdp-texto-v2; los 18 campos y el linaje son VARCHAR",
                "numeric_normalization": "none; texto fuente preservado",
                "publication_gate": "approved",
            }
            atomic_json(table_dir / "manifest.json", table_manifest)
            tables.append(
                {
                    "id": family,
                    "records": table_manifest["total_records"],
                    "manifest": f"outputs/pensiones/bdp/{family}/manifest.json",
                    "files": file_records,
                }
            )
        root_manifest = {
            "version": 1,
            "source": "Superintendencia de Pensiones · Base de Datos Pública (BDP)",
            "generated_at": stamp,
            "rows": sum(totals.values()),
            "tables": tables,
            "active_source_packages": {
                package_id: {
                    "sha256": package["archive_sha256"],
                    "official_origin_verified": package["official_origin_verified"],
                }
                for package_id, package in sorted(stage_manifest["packages"].items())
            },
            "audit_summary": {
                "families": audit_result["familias"],
                "unknown_codes": audit_result["codigos_no_clasificados"],
                "coverage_certified": False,
            },
            "notice": "Distribución autorizada por la política de publicación versionada; cifras literales sin normalización adicional.",
            "publisher": "pensiones/scripts/publish_bdp.py",
        }
        atomic_json(temp_root / "manifest.json", root_manifest)
        atomic_json(
            temp_root / PUBLISHER_MARKER,
            {"managed_by": "publish_bdp.py", "version": 1, "generated_at": stamp},
        )
        if output_root.exists():
            if not (output_root / PUBLISHER_MARKER).is_file():
                raise ValueError("El destino existente no está marcado como gestionado por este publicador")
            os.replace(output_root, backup_root)
        try:
            os.replace(temp_root, output_root)
        except Exception:
            if backup_root.exists() and not output_root.exists():
                os.replace(backup_root, output_root)
            raise
        if backup_root.exists():
            shutil.rmtree(backup_root)
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)
    return root_manifest


def publish(
    staging: Path = DEFAULT_STAGING,
    output_root: Path = DEFAULT_PUBLIC_ROOT,
    policy_path: Path = DEFAULT_POLICY,
) -> dict[str, Any]:
    decision = evaluate(policy_path, staging)
    if not decision.get("ready"):
        raise PermissionError("Publicación BDP bloqueada: " + "; ".join(decision.get("razones", [])))
    result = _publish_tree(Path(staging), Path(output_root), decision["staging_audit"])
    return {"published": True, "output": str(output_root), "rows": result["rows"], "tables": len(result["tables"])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, default=DEFAULT_STAGING)
    parser.add_argument("--output", type=Path, default=DEFAULT_PUBLIC_ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)
    try:
        result = publish(args.staging, args.output, args.policy)
    except PermissionError as exc:
        print(str(exc))
        return 2
    except Exception as exc:
        print(f"Publicación BDP abortada sin modificar archivos: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

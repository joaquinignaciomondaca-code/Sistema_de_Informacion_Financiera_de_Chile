"""Auditoría independiente de particiones/checkpoints BDP en staging privado.

La auditoría no valida semántica numérica, exactitud frente a SP ni derechos de
redistribución. Nunca devuelve publicable=true.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

try:
    from .bdp_common import (
        COLUMNS,
        LINEAGE,
        PRIVATE_ROOT,
        REQUIRED_PACKAGE_IDS,
        SCHEMA_VERSION,
        assert_private_path,
        atomic_json,
        load_family_mapping,
        sha256_file,
        validate_sha256,
    )
except ImportError:  # ejecución directa desde pensiones/scripts/
    from bdp_common import (  # type: ignore
        COLUMNS,
        LINEAGE,
        PRIVATE_ROOT,
        REQUIRED_PACKAGE_IDS,
        SCHEMA_VERSION,
        assert_private_path,
        atomic_json,
        load_family_mapping,
        sha256_file,
        validate_sha256,
    )

MANIFEST_VERSION = 2


def _schema() -> pa.Schema:
    return pa.schema([(column, pa.string()) for column in COLUMNS + LINEAGE])


def _date_ingested(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (TypeError, ValueError):
        return False


def audit(
    directory: Path,
    *,
    allow_incomplete: bool = False,
    allow_quarantine: bool = False,
    require_full_history: bool = False,
) -> dict[str, Any]:
    directory = assert_private_path(Path(directory), label="El staging a auditar")
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Falta manifest.json de staging")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != MANIFEST_VERSION:
        raise ValueError("Versión de manifest.json no soportada")
    for key in ("packages", "pending_packages", "revisions", "active_sources"):
        if not isinstance(manifest.get(key), dict):
            raise ValueError(f"Campo inválido en manifest.json: {key}")
    if manifest.get("publication", {}).get("blocked") is not True:
        raise ValueError("El staging perdió la marca de bloqueo de publicación")
    manifest_incomplete = manifest.get("status") != "staging_complete"

    package_ids = set(manifest["packages"])
    active_sources = manifest["active_sources"]
    revisions = manifest["revisions"]
    codes = load_family_mapping()
    expected_schema = _schema()
    paths_referenced: set[Path] = set()
    active_revision_ids: set[str] = set()
    for package_id, package in manifest["packages"].items():
        if package.get("status") != "complete" or package.get("package_id") != package_id:
            raise ValueError(f"Registro de paquete incompleto o inconsistente: {package_id}")
        validate_sha256(str(package.get("archive_sha256", "")), label="SHA-256 de archivo fuente")
        source_keys = package.get("source_keys")
        if not isinstance(source_keys, list) or not source_keys:
            raise ValueError(f"Paquete sin miembros CSV: {package_id}")
        if len(source_keys) != len(set(source_keys)):
            raise ValueError(f"Miembros CSV duplicados en {package_id}")
        for source_key in source_keys:
            revision_id = active_sources.get(source_key)
            if not revision_id or revision_id not in revisions:
                raise ValueError(f"Miembro activo sin revisión: {source_key}")
            revision = revisions[revision_id]
            if (
                not revision.get("complete")
                or revision.get("source_key") != source_key
                or revision.get("package_id") != package_id
            ):
                raise ValueError(f"Revisión activa incompleta o mal asociada: {source_key}")
            active_revision_ids.add(revision_id)
    for source_key, revision_id in active_sources.items():
        if revision_id not in revisions or revisions[revision_id].get("source_key") != source_key:
            raise ValueError(f"Índice active_sources inconsistente: {source_key}")
        revision = revisions[revision_id]
        package = manifest["packages"].get(revision.get("package_id"), {})
        if source_key not in package.get("source_keys", []):
            raise ValueError(f"Fuente activa no está en el inventario de su paquete: {source_key}")

    pending = manifest["pending_packages"]
    if pending and not allow_incomplete:
        raise ValueError("Hay paquetes en curso; use --allow-incomplete sólo para inspeccionar checkpoints")
    for package_id, record in pending.items():
        if record.get("package_id") != package_id or not record.get("source_keys"):
            raise ValueError(f"Checkpoint de paquete inválido: {package_id}")
        for source_key, revision_id in record.get("source_revisions", {}).items():
            if source_key not in record["source_keys"] or revision_id not in revisions:
                raise ValueError(f"Checkpoint de miembro inválido: {source_key}")

    with tempfile.TemporaryDirectory(prefix="bdp-audit-", dir=PRIVATE_ROOT) as temp_dir:
        db_path = Path(temp_dir) / "audit.sqlite"
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("CREATE TABLE ids (id TEXT PRIMARY KEY)")
        connection.execute(
            "CREATE TABLE coverage (fecha TEXT, afp TEXT, fondo TEXT, instrumento TEXT, n INTEGER, "
            "PRIMARY KEY(fecha, afp, fondo, instrumento))"
        )
        connection.execute("CREATE TABLE instrument_codes (code TEXT PRIMARY KEY, n INTEGER)")

        all_rows_by_revision: dict[str, Counter[str]] = {}
        active_rows_by_family: Counter[str] = Counter()
        active_rows_by_source: Counter[str] = Counter()
        coverage_rows = 0
        unknown_codes: Counter[str] = Counter()
        referenced_count = 0

        for revision_id, revision in revisions.items():
            validate_sha256(str(revision_id), label="ID de revisión")
            if not isinstance(revision, dict) or not isinstance(revision.get("parts"), list):
                raise ValueError(f"Revisión mal formada: {revision_id}")
            source_key = str(revision.get("source_key", ""))
            if not source_key or source_key.count("!") < 1:
                raise ValueError(f"Identificador de fuente inválido: {revision_id}")
            member_hash = validate_sha256(
                str(revision.get("member_sha256", "")), label="SHA-256 CSV"
            )
            if not isinstance(revision.get("complete"), bool):
                raise ValueError(f"Estado de revisión inválido: {revision_id}")
            if revision.get("complete"):
                validate_sha256(str(revision_id), label="ID de revisión")
                if revision.get("schema_version") != SCHEMA_VERSION:
                    raise ValueError(f"Versión de esquema inválida: {revision_id}")
                if revision.get("encoding") not in {"utf-8-sig", "cp1252"}:
                    raise ValueError(f"Codificación inválida: {revision_id}")
                if not _date_ingested(revision.get("fecha_ingestion", "")):
                    raise ValueError(f"Fecha de ingestión inválida: {revision_id}")
            family_counts: Counter[str] = Counter()
            source_rows_seen: Counter[str] = Counter()
            for part in revision["parts"]:
                relative = Path(str(part.get("path", "")))
                path = (directory / relative).resolve()
                if directory not in path.parents or path in paths_referenced or not path.is_file():
                    raise ValueError(f"Ruta faltante, repetida o fuera del staging: {relative}")
                paths_referenced.add(path)
                referenced_count += 1
                if sha256_file(path) != part.get("sha256"):
                    raise ValueError(f"Hash de partición incorrecto: {relative}")
                parquet = pq.ParquetFile(path)
                if parquet.schema_arrow != expected_schema:
                    raise ValueError(f"Esquema Parquet inesperado: {relative}")
                family = str(part.get("family", ""))
                if relative.parts[:3] != ("revisions", revision_id, family):
                    raise ValueError(f"Ruta no corresponde a la familia/revisión: {relative}")
                count = 0
                for batch in parquet.iter_batches(batch_size=10_000):
                    for row in batch.to_pylist():
                        record_no = row.get("numero_fila_fuente", "")
                        code = (row.get("tipo_de_instrumento") or "").strip()
                        expected_family = codes.get(code, "otros_no_clasificados")
                        if (
                            row.get("archivo_fuente") != source_key
                            or row.get("sha256_archivo_fuente") != member_hash
                            or not record_no.isdigit()
                            or int(record_no) < 2
                            or row.get("id_registro_fuente")
                            != f"{source_key}:{member_hash}:{record_no}"
                            or row.get("fecha_ingestion") != revision.get("fecha_ingestion")
                            or row.get("version_esquema") != SCHEMA_VERSION
                            or not all((row.get(column) or "").strip() for column in COLUMNS[:4])
                            or family != expected_family
                        ):
                            raise ValueError(f"Linaje, clave o familia incorrecta: {relative}")
                        if revision.get("complete") and int(record_no) > int(revision.get("source_rows", 0)) + 1:
                            raise ValueError(f"Número de registro fuera del rango fuente: {relative}")
                        if revision_id in active_revision_ids:
                            try:
                                connection.execute(
                                    "INSERT INTO ids(id) VALUES (?)",
                                    (row["id_registro_fuente"],),
                                )
                            except sqlite3.IntegrityError as exc:
                                raise ValueError("ID de linaje repetido entre particiones activas") from exc
                            connection.execute(
                                "INSERT INTO coverage VALUES (?,?,?,?,1) "
                                "ON CONFLICT(fecha,afp,fondo,instrumento) DO UPDATE SET n=n+1",
                                tuple(row[column] for column in COLUMNS[:4]),
                            )
                            connection.execute(
                                "INSERT INTO instrument_codes VALUES (?,1) "
                                "ON CONFLICT(code) DO UPDATE SET n=n+1",
                                (code,),
                            )
                            active_rows_by_family[family] += 1
                            active_rows_by_source[source_key] += 1
                            if expected_family == "otros_no_clasificados":
                                unknown_codes[code] += 1
                        family_counts[family] += 1
                        source_rows_seen[source_key] += 1
                        count += 1
                if count != int(part.get("rows", -1)):
                    raise ValueError(f"Conteo de partición incorrecto: {relative}")
            expected_rows_by_family = Counter(revision.get("rows_by_family", {}))
            if dict(family_counts) != dict(expected_rows_by_family):
                # Las revisiones parciales conservan sólo lotes completos; sus
                # contadores describen exactamente las filas ya confirmadas.
                raise ValueError(f"Conservación por familia incorrecta: {source_key}")
            revision_rows = sum(family_counts.values())
            if revision_rows != int(revision.get("rows", -1)):
                raise ValueError(f"Conteo total de revisión incorrecto: {source_key}")
            if revision.get("complete") and revision_rows != int(revision.get("source_rows", -1)):
                raise ValueError(f"Conservación de registros de fuente incorrecta: {source_key}")
            all_rows_by_revision[revision_id] = family_counts

        connection.commit()
        expected_paths = {path.resolve() for path in directory.rglob("*.parquet")}
        if expected_paths != paths_referenced:
            raise ValueError("Inventario de Parquet tiene archivos huérfanos o entradas faltantes")
        if active_rows_by_source != Counter(
            {
                source_key: int(revisions[revision_id].get("rows", 0))
                for source_key, revision_id in active_sources.items()
            }
        ):
            raise ValueError("Conservación por fuente activa incorrecta")
        coverage_summary = connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(n),0) FROM coverage"
        ).fetchone()
        coverage_rows = int(coverage_summary[1])
        coverage_dimensions = {
            "combinaciones_fecha_afp_fondo_instrumento": int(coverage_summary[0]),
            "cortes_fuente_distintos": int(
                connection.execute("SELECT COUNT(DISTINCT fecha) FROM coverage").fetchone()[0]
            ),
            "afp_distintas": int(
                connection.execute("SELECT COUNT(DISTINCT afp) FROM coverage").fetchone()[0]
            ),
            "fondos_distintos": int(
                connection.execute("SELECT COUNT(DISTINCT fondo) FROM coverage").fetchone()[0]
            ),
            "codigos_instrumento_distintos": int(
                connection.execute("SELECT COUNT(*) FROM instrument_codes").fetchone()[0]
            ),
        }
        connection.close()

    missing_packages = sorted(set(REQUIRED_PACKAGE_IDS) - package_ids)
    incomplete = bool(pending or manifest_incomplete)
    full_history = bool(not missing_packages and not incomplete)
    result = {
        "version": 2,
        "estado": (
            "incompleto" if incomplete else "cuarentena" if unknown_codes else "staging_completo"
        ),
        "publicable": False,
        "publicacion_bloqueada": True,
        "historico_completo_por_paquetes": full_history,
        "cobertura_historica_certificada": False,
        "paquetes_activos": sorted(package_ids),
        "paquetes_faltantes": missing_packages,
        "miembros_activos": len(active_sources),
        "revisiones_auditadas": len(revisions),
        "particiones_auditadas": referenced_count,
        "filas": sum(active_rows_by_family.values()),
        "familias": dict(sorted(active_rows_by_family.items())),
        "filas_por_fuente": dict(sorted(active_rows_by_source.items())),
        "codigos_no_clasificados": dict(sorted(unknown_codes.items())),
        "cobertura": {**coverage_dimensions, "filas_en_matriz": coverage_rows},
        "paquetes_oficiales_verificados": sorted(
            package_id
            for package_id, package in manifest["packages"].items()
            if package.get("official_origin_verified") is True
        ),
        "nota": "Cobertura por paquetes no certifica fechas/valores ni exactitud contra los originales SP.",
    }
    if result["estado"] == "incompleto" and not allow_incomplete:
        raise ValueError("Staging incompleto: estado de corrida, checkpoints o paquetes pendientes")
    if unknown_codes and not allow_quarantine:
        raise ValueError("Hay códigos sin clasificar; se conservan en cuarentena y bloquean la auditoría")
    if require_full_history and not full_history:
        raise ValueError("Faltan paquetes requeridos para el histórico completo: " + ", ".join(missing_packages))
    atomic_json(directory / "audit.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--allow-quarantine", action="store_true")
    parser.add_argument("--require-full-history", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = audit(
            args.directory,
            allow_incomplete=args.allow_incomplete,
            allow_quarantine=args.allow_quarantine,
            require_full_history=args.require_full_history,
        )
    except Exception as exc:
        print(f"AUDITORÍA BDP FALLIDA: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

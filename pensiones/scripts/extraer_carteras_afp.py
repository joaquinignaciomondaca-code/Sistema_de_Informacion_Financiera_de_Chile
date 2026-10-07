"""Ingesta reanudable e incremental de originales CSV/ZIP de la BDP.

- Staging y originales sólo se admiten bajo .local-data/.
- Se preservan literalmente los 18 campos originales como texto.
- Cada CSV se procesa en lotes con checkpoint atómico y linaje por registro lógico.
- Las revisiones se conservan por hash; la revisión activa cambia sólo al terminar
  el paquete completo, para no mezclar versiones ni perder una corrida válida.
- La descarga oficial, el cotejo SP y la autorización de redistribución son gates
  separados: este extractor nunca publica en docs/outputs/.

Códigos de salida de ``main``: 0 = staging completo; 2 = límite alcanzado con
checkpoint íntegro (repita la misma orden para reanudar); 3 = uso incorrecto o
ausencia de originales (no hay nada que reanudar); 1 = error de ingesta.
"""
from __future__ import annotations

import argparse
import csv
import errno
import hashlib
import io
import json
import math
import os
import re
import socket
import sys
import time
import zipfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Callable

try:
    from .bdp_common import (
        COLUMNS,
        LINEAGE,
        OFFICIAL_LANDING_PAGE,
        PRIVATE_ROOT,
        ROOT,
        SCHEMA_VERSION,
        atomic_json,
        assert_private_path,
        load_family_mapping,
        safe_archive_member,
        sha256_file,
        sha256_stream,
        validate_package_id,
        validate_sha256,
    )
except ImportError:  # ejecución directa desde pensiones/scripts/
    from bdp_common import (  # type: ignore
        COLUMNS,
        LINEAGE,
        OFFICIAL_LANDING_PAGE,
        PRIVATE_ROOT,
        ROOT,
        SCHEMA_VERSION,
        atomic_json,
        assert_private_path,
        load_family_mapping,
        safe_archive_member,
        sha256_file,
        sha256_stream,
        validate_package_id,
        validate_sha256,
    )

DEFAULT_OUTPUT = PRIVATE_ROOT / "pensiones/bdp/staging"
DEFAULT_INPUTS = PRIVATE_ROOT / "pensiones/bdp/originales"
MAX_CSV_BYTES = 4_000_000_000
MAX_TOTAL_CSV_BYTES = 20_000_000_000
MAX_CSV_MEMBERS = 20_000
MAX_CSV_FIELD_BYTES = 16_000_000
MANIFEST_VERSION = 2


class StopAfterCheckpoint(Exception):
    """Se alcanzó un límite entre lotes; el checkpoint quedó consistente."""


class HashingRaw(io.RawIOBase):
    """Envoltorio que calcula SHA-256 de bytes CSV al leer sin materializarlos."""

    def __init__(self, raw: BinaryIO):
        super().__init__()
        self.raw = raw
        self.digest = hashlib.sha256()

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        block = self.raw.read(len(buffer))
        if not block:
            return 0
        self.digest.update(block)
        buffer[: len(block)] = block
        return len(block)

    def close(self) -> None:
        if not self.closed:
            try:
                self.raw.close()
            finally:
                super().close()


@contextmanager
def _csv_field_limit(limit: int):
    previous = csv.field_size_limit()
    csv.field_size_limit(limit)
    try:
        yield
    finally:
        csv.field_size_limit(previous)


def mapping() -> dict[str, str]:
    """Compatibilidad con los scripts y pruebas anteriores del PR #28."""
    return load_family_mapping()


def _normalize_header(values: list[str]) -> list[str]:
    header = [item.strip().lower() for item in values]
    # El manual/CSV histórico puede truncar este único encabezado; se acepta sólo
    # ese alias exacto y se documenta sin alterar los valores de las filas.
    return [
        "tasa_pactada_de_la_contraparte_swap"
        if item == "tasa_pactada_de_la_contraparte_s"
        else item
        for item in header
    ]


def _atomic_write_parquet(table: Any, destination: Path) -> None:
    import pyarrow.parquet as pq

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    pq.write_table(table, temporary, compression="zstd")
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, destination)


def _revision_id(package_id: str, member: str, digest: str, encoding: str) -> str:
    token = "\0".join((package_id, member, digest, encoding, SCHEMA_VERSION))
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _load_source_package(path: Path, explicit_package_id: str | None = None) -> dict[str, Any]:
    path = assert_private_path(Path(path), label="Los originales CSV/ZIP")
    if not path.is_file():
        raise ValueError(f"No existe el original: {path}")
    sidecar = path.with_suffix(path.suffix + ".source.json")
    record: dict[str, Any] = {}
    if sidecar.exists():
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        if record.get("version") != 2 or record.get("download_status") != "verified":
            raise ValueError(f"Sidecar de descarga no verificado/actualizado: {sidecar.name}")
        capture_sha = validate_sha256(str(record.get("capture_evidence_sha256", "")), label="SHA-256 de captura UI")
        capture_path = Path(str(record.get("capture_evidence_path", "")))
        if not capture_path.is_absolute():
            capture_path = ROOT / capture_path
        capture_path = assert_private_path(capture_path, label="La evidencia de captura")
        evidence_root = (PRIVATE_ROOT / "pensiones/bdp/evidencia").resolve()
        if evidence_root not in capture_path.parents or not capture_path.is_file():
            raise ValueError(f"No está disponible la evidencia privada de captura: {sidecar.name}")
        if sha256_file(capture_path) != capture_sha:
            raise ValueError(f"La evidencia de captura difiere de su SHA-256: {sidecar.name}")
        if record.get("capture_method") != "GET" or int(record.get("capture_response_status", 0)) != 200:
            raise ValueError(f"Sidecar sin captura GET/HTTP 200 de la UI oficial: {sidecar.name}")
        if record.get("filename") != path.name:
            raise ValueError(f"El nombre del sidecar no corresponde a {path.name}")
        if record.get("source_page") != OFFICIAL_LANDING_PAGE or record.get("captured_from") != OFFICIAL_LANDING_PAGE:
            raise ValueError(f"La procedencia del sidecar no es la página BDP oficial: {path.name}")
        verification = record.get("verification", [])
        if "HTTPS" not in verification or not any("spensiones.cl" in str(item) for item in verification):
            raise ValueError(f"Sidecar sin controles de transporte oficiales: {path.name}")
        if path.suffix.lower() != ".zip":
            raise ValueError("El sidecar oficial sólo puede verificar paquetes ZIP")
        if sha256_file(path) != validate_sha256(str(record.get("sha256", ""))):
            raise ValueError(f"SHA-256 del original difiere del sidecar: {path.name}")
        final_host = str(record.get("final_host", "")).lower().rstrip(".")
        if not (final_host == "spensiones.cl" or final_host.endswith(".spensiones.cl")):
            raise ValueError(f"Origen del sidecar no es la Superintendencia: {path.name}")
        package_id = validate_package_id(str(record.get("package_id", "")))
        if explicit_package_id and explicit_package_id != package_id:
            raise ValueError("--package-id contradice el ID de paquete del sidecar")
        official_verified = True
        archive_sha256 = str(record["sha256"])
    else:
        package_id = validate_package_id(explicit_package_id or path.stem.lower())
        archive_sha256 = sha256_file(path)
        official_verified = False
    if path.suffix.lower() not in {".zip", ".csv"}:
        raise ValueError("Sólo se aceptan originales CSV o ZIP; no espejos XLSX")
    if path.stat().st_size <= 0:
        raise ValueError(f"Original vacío: {path.name}")
    return {
        "path": path,
        "package_id": package_id,
        "archive_sha256": archive_sha256,
        "official_verified": official_verified,
        "download_record": record,
    }


def _manifest_template() -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).isoformat()
    return {
        "version": MANIFEST_VERSION,
        "created_at": stamp,
        "updated_at": stamp,
        "status": "incomplete",
        "publication": {"blocked": True, "reason": "Cotejo SP y redistribución pendientes"},
        "packages": {},
        "pending_packages": {},
        "revisions": {},
        "active_sources": {},
    }


def _load_manifest(output: Path) -> dict[str, Any]:
    path = output / "manifest.json"
    if not path.exists():
        return _manifest_template()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("version") != MANIFEST_VERSION:
        raise ValueError("Manifiesto de staging incompatible; exporte copia y migre explícitamente")
    for key in ("packages", "pending_packages", "revisions", "active_sources"):
        if not isinstance(manifest.get(key), dict):
            raise ValueError(f"Manifiesto inválido: {key}")
    return manifest


def _save_manifest(output: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_json(output / "manifest.json", manifest)


def _part_paths(output: Path, revision: dict[str, Any]) -> set[Path]:
    paths: set[Path] = set()
    for part in revision.get("parts", []):
        path = (output / part["path"]).resolve()
        if output not in path.parents:
            raise ValueError("Ruta de partición fuera del staging")
        paths.add(path)
    return paths


def _verify_revision_parts(output: Path, revision: dict[str, Any]) -> None:
    for part in revision.get("parts", []):
        path = (output / part["path"]).resolve()
        if output not in path.parents or not path.is_file():
            raise ValueError("Falta una partición checkpoint: " + str(part.get("path")))
        if sha256_file(path) != part.get("sha256"):
            raise ValueError("Hash de checkpoint incorrecto: " + str(part["path"]))


def _clean_uncommitted_parts(output: Path, revision_id: str, revision: dict[str, Any]) -> None:
    revision_dir = output / "revisions" / revision_id
    if not revision_dir.exists():
        return
    committed = _part_paths(output, revision)
    for path in revision_dir.rglob("*"):
        if path.is_file() and (path.name.endswith(".tmp") or path.suffix == ".parquet"):
            if path.resolve() not in committed:
                path.unlink()


def _open_member(source: dict[str, Any], member_name: str, archive: zipfile.ZipFile | None = None) -> Callable[[], Any]:
    path: Path = source["path"]
    if path.suffix.lower() == ".csv":
        return lambda: path.open("rb")
    if archive is None:
        raise ValueError("ZIP member requires an open archive")
    return lambda: archive.open(member_name, "r")


def _csv_members(source: dict[str, Any], archive: zipfile.ZipFile | None) -> list[tuple[str, int]]:
    path: Path = source["path"]
    if path.suffix.lower() == ".csv":
        if path.stat().st_size > MAX_CSV_BYTES:
            raise ValueError("CSV supera el límite de tamaño")
        return [(path.name, path.stat().st_size)]
    assert archive is not None
    names: set[str] = set()
    result = []
    total_csv_bytes = 0
    for info in archive.infolist():
        if info.is_dir():
            safe_archive_member(info.filename.rstrip("/\\\\"))
            continue
        member = safe_archive_member(info.filename)
        if member in names:
            raise ValueError(f"Miembro ZIP duplicado: {member}")
        names.add(member)
        if info.flag_bits & 0x1:
            raise ValueError(f"Miembro ZIP cifrado: {member}")
        if member.lower().endswith(".csv"):
            if info.file_size > MAX_CSV_BYTES:
                raise ValueError(f"CSV ZIP supera el límite de tamaño: {member}")
            if info.file_size and info.compress_size == 0:
                raise ValueError(f"Tamaño ZIP inconsistente: {member}")
            if info.compress_size and info.file_size / info.compress_size > 10_000:
                raise ValueError(f"Ratio de compresión sospechoso: {member}")
            total_csv_bytes += info.file_size
            if total_csv_bytes > MAX_TOTAL_CSV_BYTES:
                raise ValueError("Tamaño total de CSV en ZIP supera el límite permitido")
            result.append((member, info.file_size))
    if not result:
        raise ValueError("ZIP sin miembros CSV")
    if len(result) > MAX_CSV_MEMBERS:
        raise ValueError("ZIP excede el máximo de CSV permitidos")
    return sorted(result)


def _check_sidecar_inventory(source: dict[str, Any], members: list[tuple[str, int]], archive: zipfile.ZipFile | None) -> None:
    expected = source["download_record"].get("zip_csv_members") if source["download_record"] else None
    if expected is None or archive is None:
        return
    actual = {name: (size, f"{info.CRC:08x}") for name, size in members for info in [archive.getinfo(name)]}
    stated = {
        item.get("name"): (item.get("bytes_uncompressed"), item.get("crc32"))
        for item in expected
    }
    if actual != stated:
        raise ValueError("Inventario CSV/CRC del ZIP no coincide con el sidecar de descarga")


def _stream_member_hash(opener: Callable[[], Any], deadline: float) -> str:
    with opener() as stream:
        return sha256_stream(stream, deadline)


def _consume_member(
    *,
    source: dict[str, Any],
    member_name: str,
    member_size: int,
    opener: Callable[[], Any],
    member_hash: str,
    output: Path,
    manifest: dict[str, Any],
    encoding: str,
    batch_rows: int,
    max_batches: int,
    deadline: float,
    global_batches: list[int],
) -> tuple[str, bool]:
    import pyarrow as pa

    package_id = source["package_id"]
    source_key = f"{package_id}!{member_name}"
    revision_id = _revision_id(package_id, member_name, member_hash, encoding)
    revisions = manifest["revisions"]
    revision = revisions.get(revision_id)
    if revision and revision.get("complete"):
        if revision.get("source_key") != source_key or revision.get("member_sha256") != member_hash:
            raise ValueError("Colisión de identificador de revisión")
        _verify_revision_parts(output, revision)
        revision.setdefault("archive_sha256s", [])
        if source["archive_sha256"] not in revision["archive_sha256s"]:
            revision["archive_sha256s"].append(source["archive_sha256"])
            _save_manifest(output, manifest)
        return revision_id, True

    if revision is None:
        revision = {
            "source_key": source_key,
            "package_id": package_id,
            "member": member_name,
            "member_sha256": member_hash,
            "archive_sha256s": [source["archive_sha256"]],
            "encoding": encoding,
            "schema_version": SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "fecha_ingestion": datetime.now(timezone.utc).isoformat(),
            "complete": False,
            "last_source_row": 1,
            "next_batch": 0,
            "rows": 0,
            "rows_by_family": {},
            "parts": [],
            "source_bytes_uncompressed": member_size,
        }
        revisions[revision_id] = revision
        _save_manifest(output, manifest)
    else:
        if (
            revision.get("source_key") != source_key
            or revision.get("member_sha256") != member_hash
            or revision.get("encoding") != encoding
        ):
            raise ValueError("Checkpoint no corresponde al CSV/codificación de la entrada")
        revision.setdefault("archive_sha256s", [])
        if source["archive_sha256"] not in revision["archive_sha256s"]:
            revision["archive_sha256s"].append(source["archive_sha256"])
    _verify_revision_parts(output, revision)
    _clean_uncommitted_parts(output, revision_id, revision)

    expected_schema = pa.schema([(column, pa.string()) for column in COLUMNS + LINEAGE])
    buffers: dict[str, list[dict[str, str]]] = defaultdict(list)
    batch_counts: Counter[str] = Counter()
    batch_count = 0
    batch_last_row = int(revision.get("last_source_row", 1))
    total_rows_seen = 0
    source_row_number = 1  # el encabezado ocupa el registro lógico 1
    codes = mapping()
    stop_after_batch = False

    def commit_batch() -> None:
        nonlocal batch_count, batch_last_row
        if not batch_count:
            return
        batch_no = int(revision["next_batch"])
        new_parts = []
        for family in sorted(buffers):
            records = buffers[family]
            if not records:
                continue
            table = pa.Table.from_pylist(records, schema=expected_schema)
            relative = Path("revisions") / revision_id / family / f"batch-{batch_no:06d}.parquet"
            destination = output / relative
            _atomic_write_parquet(table, destination)
            new_parts.append(
                {
                    "path": relative.as_posix(),
                    "family": family,
                    "rows": len(records),
                    "sha256": sha256_file(destination),
                }
            )
        revision["parts"].extend(new_parts)
        revision["rows"] = int(revision.get("rows", 0)) + batch_count
        family_counts = Counter(revision.get("rows_by_family", {}))
        family_counts.update(batch_counts)
        revision["rows_by_family"] = dict(family_counts)
        revision["last_source_row"] = batch_last_row
        revision["next_batch"] = batch_no + 1
        _save_manifest(output, manifest)
        for records in buffers.values():
            records.clear()
        batch_counts.clear()
        batch_count = 0
        global_batches[0] += 1

    try:
        with opener() as raw:
            hashing_raw = HashingRaw(raw)
            buffered = io.BufferedReader(hashing_raw, buffer_size=1024 * 1024)
            with io.TextIOWrapper(buffered, encoding=encoding, newline="") as text, _csv_field_limit(MAX_CSV_FIELD_BYTES):
                reader = csv.reader(text, delimiter=";", strict=True)
                header = _normalize_header(next(reader, []))
                if header != list(COLUMNS):
                    raise ValueError("Cabecera BDP inesperada: " + source_key)
                for source_row_number, values in enumerate(reader, start=2):
                    if source_row_number <= int(revision["last_source_row"]):
                        continue
                    if time.monotonic() >= deadline:
                        stop_after_batch = True
                        break
                    if len(values) != len(COLUMNS):
                        raise ValueError(
                            f"Cantidad de campos inválida: {source_key}:{source_row_number}"
                        )
                    row = dict(zip(COLUMNS, values))
                    if not all(row[column].strip() for column in COLUMNS[:4]):
                        raise ValueError(f"Clave de cobertura vacía: {source_key}:{source_row_number}")
                    code = row["tipo_de_instrumento"].strip()
                    family = codes.get(code, "otros_no_clasificados")
                    row.update(
                        archivo_fuente=source_key,
                        sha256_archivo_fuente=member_hash,
                        numero_fila_fuente=str(source_row_number),
                        id_registro_fuente=f"{source_key}:{member_hash}:{source_row_number}",
                        fecha_ingestion=revision["fecha_ingestion"],
                        version_esquema=SCHEMA_VERSION,
                    )
                    buffers[family].append(row)
                    batch_counts[family] += 1
                    batch_count += 1
                    total_rows_seen += 1
                    batch_last_row = source_row_number
                    if batch_count >= batch_rows:
                        commit_batch()
                        if max_batches and global_batches[0] >= max_batches:
                            stop_after_batch = True
                            break
                if not stop_after_batch:
                    commit_batch()
                # Si se interrumpe por límite, el batch en memoria se descarta y
                # el siguiente intento relee desde el último registro confirmado.
                if not stop_after_batch and hashing_raw.digest.hexdigest() != member_hash:
                    raise ValueError("El CSV cambió entre el cálculo de hash y el parseo")
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError(f"CSV no decodificable o mal formado ({source_key}): {exc}") from exc

    if stop_after_batch:
        if time.monotonic() >= deadline:
            raise StopAfterCheckpoint("Tiempo agotado entre lotes; checkpoint conservado")
        raise StopAfterCheckpoint("Límite de lotes alcanzado; checkpoint conservado")
    if int(revision.get("rows", 0)) == 0:
        raise ValueError("CSV sin observaciones: " + source_key)
    if int(revision.get("last_source_row", 1)) < 2:
        raise ValueError("CSV sin registros después de su encabezado: " + source_key)
    revision["complete"] = True
    revision["completed_at"] = datetime.now(timezone.utc).isoformat()
    revision["source_rows"] = int(revision["last_source_row"]) - 1
    _save_manifest(output, manifest)
    return revision_id, False


def _activate_package(
    manifest: dict[str, Any],
    source: dict[str, Any],
    archive_sha256: str,
    source_keys: list[str],
) -> None:
    package_id = source["package_id"]
    previous = manifest["packages"].get(package_id, {})
    new_set = set(source_keys)
    for old_key in previous.get("source_keys", []):
        if old_key not in new_set:
            manifest["active_sources"].pop(old_key, None)
    for source_key in source_keys:
        revision_id = manifest["pending_packages"][package_id]["source_revisions"][source_key]
        revision = manifest["revisions"][revision_id]
        if not revision.get("complete"):
            raise ValueError("No se activa un paquete con miembros incompletos")
        manifest["active_sources"][source_key] = revision_id
    manifest["packages"][package_id] = {
        "package_id": package_id,
        "archive_sha256": archive_sha256,
        "filename": source["path"].name,
        "bytes": source["path"].stat().st_size,
        "official_origin_verified": bool(source["official_verified"]),
        "downloaded_at": source["download_record"].get("downloaded_at") if source["download_record"] else None,
        "source_keys": source_keys,
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete",
    }
    manifest["pending_packages"].pop(package_id, None)


def _acquire_lock(lock: Path) -> int:
    """Crea lock exclusivo y recupera uno obsoleto sólo si el PID local murió."""
    for _ in range(2):
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            payload = {
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            os.write(descriptor, json.dumps(payload).encode("utf-8"))
            os.fsync(descriptor)
            return descriptor
        except FileExistsError as exc:
            try:
                owner = json.loads(lock.read_text(encoding="utf-8"))
                same_host = owner.get("hostname") == socket.gethostname()
                pid = int(owner.get("pid", 0))
            except Exception:
                raise ValueError("Lock de ingesta ilegible; verifique procesos antes de retirarlo") from exc
            if not same_host or pid <= 0:
                raise ValueError("Lock de otro host/PID; no se elimina automáticamente") from exc
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                lock.unlink(missing_ok=True)
                continue
            except PermissionError:
                raise ValueError("Hay un proceso de ingesta activo con permisos distintos") from exc
            except OSError as process_error:
                if process_error.errno == errno.ESRCH:
                    lock.unlink(missing_ok=True)
                    continue
                raise ValueError("No se pudo comprobar si el proceso de ingesta sigue activo") from process_error
            raise ValueError("Ya existe una ingesta activa; no se puede reanudar en paralelo") from exc
    raise ValueError("No se pudo adquirir el lock de ingesta")


def extract(
    inputs: list[Path],
    output: Path = DEFAULT_OUTPUT,
    encoding: str = "utf-8-sig",
    max_archivos: int = 50,
    minutos: float = 60,
    *,
    package_ids: list[str] | None = None,
    filas_por_lote: int = 10_000,
    max_lotes: int = 0,
    incremental: bool = False,
) -> dict[str, Any]:
    import pyarrow as pa  # noqa: F401 -- dependency checked before touching state

    output = assert_private_path(Path(output), label="El staging")
    if not math.isfinite(minutos) or minutos <= 0 or max_archivos < 1 or filas_por_lote < 1 or max_lotes < 0:
        raise ValueError("Límites de tiempo, archivos, lotes y filas deben ser válidos")
    if encoding not in {"utf-8-sig", "cp1252"}:
        raise ValueError("Codificación no admitida; use utf-8-sig o cp1252")
    if output.exists() and not output.is_dir():
        raise ValueError("La ruta de staging existe y no es directorio")
    if package_ids and len(package_ids) != len(inputs):
        raise ValueError("--package-id debe aparecer una vez por cada archivo de entrada")
    explicit = package_ids or [None] * len(inputs)
    sources = [_load_source_package(path, package_id) for path, package_id in zip(inputs, explicit)]
    package_id_list = [source["package_id"] for source in sources]
    if len(set(package_id_list)) != len(package_id_list):
        raise ValueError("No procese dos archivos del mismo paquete en una corrida")
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".ingest.lock"
    lock_fd = _acquire_lock(lock)
    os.close(lock_fd)

    try:
        manifest = _load_manifest(output)
    except Exception:
        lock.unlink(missing_ok=True)
        raise
    if incremental and not manifest["packages"]:
        lock.unlink(missing_ok=True)
        raise ValueError("--incremental requiere un staging previo con paquetes completos")
    deadline = time.monotonic() + minutos * 60
    global_batches = [0]
    processed_members = 0
    stopped = False
    error: Exception | None = None
    try:
        for source in sources:
            package_id = source["package_id"]
            archive_sha = source["archive_sha256"]
            current_package = manifest["packages"].get(package_id, {})
            if current_package.get("archive_sha256") == archive_sha and current_package.get("status") == "complete":
                # Un paquete idéntico ya auditado no se vuelve a leer ni se duplica.
                continue
            if time.monotonic() >= deadline:
                stopped = True
                break
            archive_context = zipfile.ZipFile(source["path"]) if source["path"].suffix.lower() == ".zip" else None
            try:
                members = _csv_members(source, archive_context)
                _check_sidecar_inventory(source, members, archive_context)
                source_keys = [f"{package_id}!{name}" for name, _ in members]
                pending = manifest["pending_packages"].get(package_id)
                if pending and (
                    pending.get("archive_sha256") != archive_sha
                    or pending.get("source_keys") != source_keys
                ):
                    raise ValueError(
                        "El paquete cambió mientras había un checkpoint incompleto; "
                        "termine la versión pendiente o use un staging nuevo para la revisión"
                    )
                if pending is None:
                    pending = {
                        "package_id": package_id,
                        "archive_sha256": archive_sha,
                        "filename": source["path"].name,
                        "source_keys": source_keys,
                        "source_revisions": {},
                        "started_at": datetime.now(timezone.utc).isoformat(),
                    }
                    manifest["pending_packages"][package_id] = pending
                    _save_manifest(output, manifest)
                for member_name, member_size in members:
                    if processed_members >= max_archivos:
                        stopped = True
                        break
                    if time.monotonic() >= deadline:
                        stopped = True
                        break
                    processed_members += 1
                    opener = _open_member(source, member_name, archive_context)
                    member_hash = _stream_member_hash(opener, deadline)
                    source_key = f"{package_id}!{member_name}"
                    revision_id, was_complete = _consume_member(
                        source=source,
                        member_name=member_name,
                        member_size=member_size,
                        opener=opener,
                        member_hash=member_hash,
                        output=output,
                        manifest=manifest,
                        encoding=encoding,
                        batch_rows=filas_por_lote,
                        max_batches=max_lotes,
                        deadline=deadline,
                        global_batches=global_batches,
                    )
                    pending["source_revisions"][source_key] = revision_id
                    if source_key not in pending["source_keys"]:
                        raise ValueError("Miembro CSV no declarado en inventario del paquete")
                    _save_manifest(output, manifest)
                    if max_lotes and global_batches[0] >= max_lotes:
                        stopped = True
                        break
                if stopped:
                    break
                if len(pending["source_revisions"]) != len(source_keys):
                    raise ValueError("Inventario del paquete quedó incompleto")
                _activate_package(manifest, source, archive_sha, source_keys)
                _save_manifest(output, manifest)
            finally:
                if archive_context is not None:
                    archive_context.close()
    except StopAfterCheckpoint:
        stopped = True
    except Exception as exc:
        error = exc

    manifest["status"] = "incomplete" if stopped or error or manifest["pending_packages"] else "staging_complete"
    manifest["publication"] = {
        "blocked": True,
        "reason": "Cotejo contra originales SP y condiciones de redistribución pendientes",
    }
    _save_manifest(output, manifest)
    summary = {
        "version": 1,
        "status": manifest["status"],
        "publicable": False,
        "filas_activas": sum(
            int(manifest["revisions"][revision_id].get("rows", 0))
            for revision_id in manifest["active_sources"].values()
        ),
        "paquetes_procesados": sorted(manifest["packages"]),
        "paquetes_pendientes": sorted(manifest["pending_packages"]),
        "miembros_procesados_en_corrida": processed_members,
        "lotes_confirmados_en_corrida": global_batches[0],
        "motivo": (
            "La extracción sólo crea staging privado; publicación bloqueada por diseño."
            if not error
            else f"Ingesta incompleta: {type(error).__name__}: {error}"
        ),
    }
    atomic_json(output / "audit.json", summary)
    lock.unlink(missing_ok=True)
    if error:
        raise error
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, help="ZIP/CSV oficial descargado; puede omitirse con --scan")
    parser.add_argument("--scan", type=Path, default=None, help="Procesa ZIPs en una carpeta privada")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--package-id", action="append", default=[], help="ID del paquete para un CSV/ZIP sin sidecar; repetir por archivo")
    parser.add_argument("--encoding", choices=["utf-8-sig", "cp1252"], default="utf-8-sig")
    parser.add_argument("--max-archivos", type=int, default=50, help="Máximo de miembros CSV por corrida")
    parser.add_argument("--filas-por-lote", type=int, default=10_000)
    parser.add_argument("--max-lotes", type=int, default=0, help="0 = sin límite; checkpoint al completar cada lote")
    parser.add_argument("--minutos", type=float, default=60)
    parser.add_argument("--incremental", action="store_true", help="Exige staging existente; lo no entregado permanece activo")
    args = parser.parse_args(argv)
    inputs = list(args.inputs)
    if args.scan:
        folder = assert_private_path(args.scan, label="La carpeta de originales")
        inputs.extend(sorted([*folder.glob("*.zip"), *folder.glob("*.csv")]))
    if not inputs:
        # argparse.error() también sale con código 2, que en este extractor
        # significa "límite/checkpoint reanudable: repita la misma orden". Sin
        # originales no hay nada que reanudar, así que se usa un código distinto
        # para que el operador no repita la orden en bucle sin efecto.
        parser.print_usage(sys.stderr)
        print(
            "No se encontraron originales CSV/ZIP en la ruta indicada; no hay "
            "checkpoint que reanudar. Código 3 = uso/ausencia de originales; el "
            "código 2 queda reservado a límite/checkpoint incompleto.",
            file=sys.stderr,
        )
        return 3
    try:
        result = extract(
            inputs,
            args.output,
            args.encoding,
            args.max_archivos,
            args.minutos,
            package_ids=args.package_id or None,
            filas_por_lote=args.filas_por_lote,
            max_lotes=args.max_lotes,
            incremental=args.incremental,
        )
    except Exception as exc:
        print(f"Ingesta BDP no completada: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "staging_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())

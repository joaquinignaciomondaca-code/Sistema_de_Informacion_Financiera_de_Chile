"""Descarga paquetes BDP desde enlaces HTTPS capturados en el portal oficial.

No descubre endpoints, no envía formularios y no elude WAF/CAPTCHA. Cada URL debe
haber sido capturada por una persona desde la página BDP oficial, respaldada por
un registro de captura saneado bajo .local-data/, y permanecer bajo spensiones.cl.
Las descargas y sus hashes se guardan sólo en .local-data/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import urllib.error
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

try:
    from .bdp_common import (
        OFFICIAL_LANDING_PAGE,
        PRIVATE_ROOT,
        REQUIRED_PACKAGE_IDS,
        ROOT,
        atomic_json,
        assert_private_path,
        public_url_without_query,
        safe_archive_member,
        sha256_file,
        validate_official_https_url,
        validate_package_id,
        validate_sha256,
    )
except ImportError:  # ejecución directa desde pensiones/scripts/
    from bdp_common import (  # type: ignore
        OFFICIAL_LANDING_PAGE,
        PRIVATE_ROOT,
        REQUIRED_PACKAGE_IDS,
        ROOT,
        atomic_json,
        assert_private_path,
        public_url_without_query,
        safe_archive_member,
        sha256_file,
        validate_official_https_url,
        validate_package_id,
        validate_sha256,
    )

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "config/paquetes_bdp.json"
DEFAULT_OUTPUT = PRIVATE_ROOT / "pensiones/bdp/originales"
MAX_PACKAGE_BYTES = 2_000_000_000
MAX_MEMBER_BYTES = 4_000_000_000
MAX_TOTAL_UNCOMPRESSED = 20_000_000_000
MAX_MEMBERS = 20_000
BLOCK_SIZE = 1024 * 1024
USER_AGENT = "SIF-BDP-Downloader/1.0 (official-source archival; no browser impersonation)"
CAPTURE_KEYS = {
    "source_page",
    "captured_at",
    "request_method",
    "request_url",
    "referer",
    "response_status",
    "content_type",
    "response_filename",
}
ALLOWED_ZIP_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


class CatalogNotReady(ValueError):
    """El catálogo no contiene una captura verificable del portal BDP."""


class OfficialRedirectHandler(urllib.request.HTTPRedirectHandler):
    """No permite que una respuesta oficial redirija fuera de spensiones.cl."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        validate_official_https_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_opener():
    return urllib.request.build_opener(OfficialRedirectHandler())


def _safe_filename(value: str) -> str:
    decoded = unquote(value or "")
    if any(char in decoded for char in ("/", "\\", "\x00")):
        raise ValueError("Nombre de paquete inseguro")
    name = Path(decoded).name
    if not name or name in {".", ".."} or not name.lower().endswith(".zip"):
        raise ValueError("El nombre esperado debe ser un nombre de archivo .zip")
    return name


def _validate_capture(package: dict[str, Any], source_page: str) -> dict[str, Any]:
    """Valida el registro mínimo de una descarga observada en la UI oficial.

    El registro saneado no contiene cookies, headers ni cuerpo POST. Su SHA-256
    queda fijado en el catálogo versionado; la auditoría humana del PR sigue
    siendo necesaria para confiar en la captura.
    """
    capture_ref = package.get("capture_evidence")
    capture_sha = package.get("capture_sha256")
    if not capture_ref or not capture_sha:
        raise CatalogNotReady(f"Falta evidencia saneada de captura UI para {package.get('id')}")
    capture_path = Path(str(capture_ref))
    if not capture_path.is_absolute():
        capture_path = ROOT / capture_path
    capture_path = assert_private_path(capture_path, label="La evidencia de captura")
    evidence_root = (PRIVATE_ROOT / "pensiones/bdp/evidencia").resolve()
    if evidence_root not in capture_path.parents:
        raise ValueError("La evidencia debe residir bajo .local-data/pensiones/bdp/evidencia/")
    if not capture_path.is_file():
        raise CatalogNotReady(f"No está disponible la evidencia privada de captura: {capture_ref}")
    capture_sha = validate_sha256(str(capture_sha), label="SHA-256 de evidencia de captura")
    if sha256_file(capture_path) != capture_sha:
        raise ValueError(f"SHA-256 de captura no coincide: {capture_ref}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if not isinstance(capture, dict) or set(capture) != CAPTURE_KEYS:
        raise ValueError("Registro de captura no cumple el esquema saneado requerido")
    if capture.get("source_page") != source_page:
        raise ValueError("La captura no identifica la página BDP declarada")
    request_url = validate_official_https_url(str(capture.get("request_url", "")))
    if request_url != validate_official_https_url(str(package.get("download_url", ""))):
        raise ValueError("La URL de descarga no coincide con la solicitud capturada")
    referer = validate_official_https_url(str(capture.get("referer", "")))
    if referer.rstrip("/") != source_page.rstrip("/"):
        raise ValueError("El referer de la petición capturada no es la página BDP")
    if str(capture.get("request_method", "")).upper() != "GET":
        raise ValueError("Sólo se automatiza GET observado; un flujo POST requiere implementación revisada aparte")
    if int(capture.get("response_status", 0)) != 200:
        raise ValueError("La captura de descarga no terminó en HTTP 200")
    content_type = str(capture.get("content_type", "")).split(";", 1)[0].strip().lower()
    if content_type not in ALLOWED_ZIP_CONTENT_TYPES:
        raise ValueError("El Content-Type observado no identifica un ZIP/descarga binaria")
    filename = _safe_filename(str(package.get("expected_filename", "")))
    if str(capture.get("response_filename", "")) != filename:
        raise ValueError("El nombre de descarga capturado difiere del catálogo")
    try:
        captured_at = datetime.fromisoformat(str(capture.get("captured_at", "")).replace("Z", "+00:00"))
        catalog_at = datetime.fromisoformat(str(package.get("captured_at", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Fecha inválida en captura o catálogo") from exc
    if captured_at.tzinfo is None or catalog_at.tzinfo is None:
        raise ValueError("Las fechas de captura deben declarar zona horaria")
    if captured_at != catalog_at:
        raise ValueError("La fecha de captura no coincide con el catálogo")
    return {
        "sha256": capture_sha,
        "path": capture_path.relative_to(ROOT).as_posix(),
        **capture,
    }


def load_catalog(path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if catalog.get("version") != 1:
        raise ValueError("Versión de catálogo BDP no soportada")
    source_page = catalog.get("source_page", "")
    validate_official_https_url(source_page)
    if source_page.rstrip("/") != OFFICIAL_LANDING_PAGE.rstrip("/"):
        raise ValueError("La fuente debe ser la página oficial BDP documentada")
    packages = catalog.get("packages")
    if not isinstance(packages, list) or not packages:
        raise CatalogNotReady("No hay paquetes oficiales registrados")
    ids = [validate_package_id(str(item.get("id", ""))) for item in packages]
    if len(set(ids)) != len(ids):
        raise ValueError("Hay IDs de paquetes duplicados")
    if set(ids) != set(REQUIRED_PACKAGE_IDS):
        raise CatalogNotReady("El catálogo debe declarar exactamente los tres paquetes históricos BDP esperados")
    missing = []
    for item in packages:
        package_id = item["id"]
        url = item.get("download_url")
        filename = item.get("expected_filename")
        captured_from = item.get("captured_from")
        captured_at = item.get("captured_at")
        if not url or not filename or captured_from != source_page or not captured_at:
            missing.append(package_id)
            continue
        validate_official_https_url(url)
        _safe_filename(filename)
        try:
            datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"captured_at inválida en {package_id}") from exc
        if item.get("expected_sha256"):
            validate_sha256(str(item["expected_sha256"]), label=f"SHA-256 esperado de {package_id}")
        try:
            _validate_capture(item, source_page)
        except CatalogNotReady:
            missing.append(package_id)
    if missing:
        raise CatalogNotReady(
            "Faltan URL/nombre/fecha o evidencia saneada capturada desde la interfaz oficial para: "
            + ", ".join(missing)
        )
    if catalog.get("estado") != "listo":
        raise CatalogNotReady(
            "El catálogo no está marcado como listo tras una revisión de la captura oficial"
        )
    return catalog


def catalog_status(path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    try:
        catalog = load_catalog(path)
    except CatalogNotReady as exc:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            package_ids = [item.get("id") for item in data.get("packages", [])]
        except Exception:
            package_ids = []
        return {
            "ready": False,
            "estado": "bloqueado_sin_captura_oficial",
            "paquetes": package_ids,
            "motivo": str(exc),
        }
    return {
        "ready": True,
        "estado": "catalogo_capturado",
        "paquetes": [item["id"] for item in catalog["packages"]],
        "motivo": "URLs y registros saneados capturados; respuestas se validan en cada descarga",
    }


def _archive_inventory(path: Path) -> list[dict[str, Any]]:
    if not zipfile.is_zipfile(path):
        raise ValueError("La respuesta no es un ZIP válido (posible HTML/error del portal)")
    total = 0
    csvs: list[dict[str, Any]] = []
    names: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_MEMBERS:
            raise ValueError("El ZIP excede el máximo de miembros permitido")
        for info in infos:
            if info.is_dir():
                safe_archive_member(info.filename.rstrip("/\\"))
                continue
            normalized = safe_archive_member(info.filename)
            if normalized in names:
                raise ValueError(f"Miembro duplicado en ZIP: {normalized}")
            names.add(normalized)
            if info.flag_bits & 0x1:
                raise ValueError(f"Miembro ZIP cifrado no admitido: {normalized}")
            if info.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f"Miembro ZIP demasiado grande: {normalized}")
            total += info.file_size
            if total > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError("El tamaño descomprimido del ZIP excede el límite")
            if info.file_size and info.compress_size == 0:
                raise ValueError(f"Tamaño comprimido inconsistente: {normalized}")
            if info.compress_size and info.file_size / info.compress_size > 10_000:
                raise ValueError(f"Ratio de compresión sospechoso: {normalized}")
            if normalized.lower().endswith(".csv"):
                csvs.append(
                    {
                        "name": normalized,
                        "bytes_compressed": info.compress_size,
                        "bytes_uncompressed": info.file_size,
                        "crc32": f"{info.CRC:08x}",
                    }
                )
        if not csvs:
            raise ValueError("El ZIP no contiene miembros CSV")
        # Lee todos los miembros para verificar CRC; nunca los extrae al disco.
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"CRC incorrecto en miembro ZIP: {bad_member}")
    return csvs


def _preserve_previous_revision(
    target: Path,
    sidecar: Path,
    output_dir: Path,
    package_id: str,
) -> str | None:
    """Conserva el ZIP/sidecar activos antes de sustituirlos por una revisión nueva."""
    if not target.exists():
        return None
    if not sidecar.is_file():
        raise ValueError("No se reemplaza un original existente sin sidecar de procedencia")
    previous = json.loads(sidecar.read_text(encoding="utf-8"))
    previous_sha = sha256_file(target)
    if (
        previous.get("version") != 2
        or previous.get("download_status") != "verified"
        or previous.get("sha256") != previous_sha
    ):
        raise ValueError("No se reemplaza un original cuyo sidecar/hash no sea verificable")
    history_dir = output_dir / "revisions" / package_id
    history_dir.mkdir(parents=True, exist_ok=True)
    archive_copy = history_dir / f"{previous_sha}.zip"
    sidecar_copy = archive_copy.with_suffix(archive_copy.suffix + ".source.json")
    if archive_copy.exists() and sha256_file(archive_copy) != previous_sha:
        archive_copy.unlink()
    if not archive_copy.exists():
        temporary = archive_copy.with_name(f".{archive_copy.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copy2(target, temporary)
            with temporary.open("rb") as stream:
                os.fsync(stream.fileno())
            if sha256_file(temporary) != previous_sha:
                raise ValueError("La copia de resguardo del ZIP no conserva su SHA-256")
            os.replace(temporary, archive_copy)
        finally:
            temporary.unlink(missing_ok=True)
    if sidecar_copy.exists():
        prior_sidecar = json.loads(sidecar_copy.read_text(encoding="utf-8"))
        if prior_sidecar.get("sha256") != previous_sha:
            raise ValueError("Sidecar de una revisión previa no corresponde a su ZIP")
    else:
        temporary = sidecar_copy.with_name(f".{sidecar_copy.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copy2(sidecar, temporary)
            with temporary.open("rb") as stream:
                os.fsync(stream.fileno())
            os.replace(temporary, sidecar_copy)
        finally:
            temporary.unlink(missing_ok=True)
    return archive_copy.relative_to(output_dir).as_posix()


def _recover_pending_download(target: Path, sidecar: Path, pending_sidecar: Path) -> None:
    """Finaliza o descarta un sidecar pendiente tras una interrupción atómica."""
    if not pending_sidecar.exists():
        return
    if not target.is_file():
        raise ValueError("Hay sidecar pendiente pero falta el ZIP activo; revise el estado privado")
    current_sha = sha256_file(target)
    try:
        pending = json.loads(pending_sidecar.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("Sidecar pendiente ilegible; no se modifica el ZIP activo") from exc
    if (
        pending.get("version") == 2
        and pending.get("download_status") == "verified"
        and pending.get("sha256") == current_sha
    ):
        _archive_inventory(target)
        os.replace(pending_sidecar, sidecar)
        return
    if sidecar.is_file():
        current = json.loads(sidecar.read_text(encoding="utf-8"))
        if current.get("sha256") == current_sha:
            pending_sidecar.unlink()
            return
    raise ValueError("Sidecar pendiente no corresponde al ZIP ni a un estado anterior verificable")


def _response_header(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    return headers.get(name)


def _request(opener: Any, url: str, headers: dict[str, str], timeout: int):
    validate_official_https_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    try:
        if hasattr(opener, "open"):
            return opener.open(request, timeout=timeout)
        return opener(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        raise ValueError(f"GET HTTP {status} desde la fuente oficial") from None
    except urllib.error.URLError:
        raise ValueError("Falla de transporte/timeout al acceder a la fuente oficial") from None


def _content_range_start(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+|\*)", value.strip())
    return int(match.group(1)) if match else None


def _head_unchanged(url: str, old: dict[str, Any], *, opener: Any, timeout: int) -> bool:
    """Consulta validadores remotos para omitir paquetes sin cambios.

    Si SP no implementa HEAD/ETag/Last-Modified, se vuelve a descargar y validar;
    nunca se conserva un ZIP sólo porque su URL no cambió.
    """
    headers = {"User-Agent": USER_AGENT}
    if old.get("etag"):
        headers["If-None-Match"] = str(old["etag"])
    if old.get("last_modified"):
        headers["If-Modified-Since"] = str(old["last_modified"])
    request = urllib.request.Request(url, headers=headers, method="HEAD")
    try:
        response = opener.open(request, timeout=timeout) if hasattr(opener, "open") else opener(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        if status == 304:
            return True
        if 400 <= status < 600:
            return False
        raise ValueError(f"HEAD HTTP {status} desde la fuente oficial") from None
    except urllib.error.URLError:
        # HEAD puede estar bloqueado aunque GET sea válido; fuerza una nueva
        # descarga y validación en vez de confiar en la caché local.
        return False
    try:
        final_url = response.geturl() if hasattr(response, "geturl") else url
        validate_official_https_url(final_url)
        status = getattr(response, "status", None) or getattr(response, "code", None)
        if status == 304:
            return True
        if status != 200:
            return False
        content_type = _response_header(response, "Content-Type")
        if content_type and content_type.split(";", 1)[0].strip().lower() not in ALLOWED_ZIP_CONTENT_TYPES:
            return False
        etag = _response_header(response, "ETag")
        modified = _response_header(response, "Last-Modified")
        length = _response_header(response, "Content-Length")
        length_matches = length is not None and int(length) == int(old.get("bytes", -1))
        if old.get("etag") and etag:
            return etag == old.get("etag") and length_matches
        return bool(
            old.get("last_modified")
            and modified == old.get("last_modified")
            and length_matches
        )
    finally:
        response.close()


def _download_to_part(
    package: dict[str, Any],
    part_path: Path,
    partial_meta_path: Path,
    *,
    opener: Any,
    timeout: int,
    max_bytes: int,
) -> dict[str, Any]:
    url = str(package["download_url"])
    url_fingerprint = hashlib.sha256(url.encode("utf-8")).hexdigest()
    current_size = part_path.stat().st_size if part_path.exists() else 0
    old_meta = {}
    if partial_meta_path.exists():
        try:
            old_meta = json.loads(partial_meta_path.read_text(encoding="utf-8"))
        except Exception:
            old_meta = {}
    resume = bool(
        current_size
        and old_meta.get("url_fingerprint") == url_fingerprint
        and old_meta.get("etag")
        and not str(old_meta.get("etag", "")).strip().lower().startswith("w/")
    )
    request_headers: dict[str, str] = {}
    if resume:
        request_headers["Range"] = f"bytes={current_size}-"
        request_headers["If-Range"] = str(old_meta["etag"])

    response = _request(opener, url, request_headers, timeout)
    try:
        final_url = response.geturl() if hasattr(response, "geturl") else url
        validate_official_https_url(final_url)
        status = getattr(response, "status", None) or getattr(response, "code", None)
        etag = _response_header(response, "ETag")
        last_modified = _response_header(response, "Last-Modified")
        response_start = _content_range_start(_response_header(response, "Content-Range"))
        append = bool(resume and status == 206 and response_start == current_size and etag == old_meta.get("etag"))
        if resume and not append:
            # Si el servidor ignoró Range o cambió el objeto, descarta el parcial y
            # repite una solicitud completa; jamás concatena respuestas incompatibles.
            part_path.unlink(missing_ok=True)
            request_headers = {}
            response.close()
            response = _request(opener, url, request_headers, timeout)
            final_url = response.geturl() if hasattr(response, "geturl") else url
            validate_official_https_url(final_url)
            status = getattr(response, "status", None) or getattr(response, "code", None)
            etag = _response_header(response, "ETag")
            last_modified = _response_header(response, "Last-Modified")
            append = False
        if status not in (200, 206):
            raise ValueError(f"Respuesta HTTP inesperada: {status}")
        response_type = _response_header(response, "Content-Type")
        if response_type and response_type.split(";", 1)[0].strip().lower() not in ALLOWED_ZIP_CONTENT_TYPES:
            raise ValueError("La respuesta HTTP no declara tipo ZIP/binario")
        if status == 206 and not append:
            part_path.unlink(missing_ok=True)
            partial_meta_path.unlink(missing_ok=True)
            raise ValueError("Respuesta parcial inesperada sin una descarga reanudable")
        length = _response_header(response, "Content-Length")
        base_size = current_size if append else 0
        range_end = range_total = None
        if status == 206:
            content_range = _response_header(response, "Content-Range") or ""
            range_match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range.strip())
            if range_match is None:
                part_path.unlink(missing_ok=True)
                partial_meta_path.unlink(missing_ok=True)
                raise ValueError("Content-Range inválido para reanudar")
            range_start, range_end, range_total = map(int, range_match.groups())
            if (
                range_start != base_size
                or range_end < range_start
                or range_end != range_total - 1
                or (length and int(length) != range_end - range_start + 1)
            ):
                part_path.unlink(missing_ok=True)
                partial_meta_path.unlink(missing_ok=True)
                raise ValueError("Content-Range no corresponde al parcial/tamaño anunciado")
        if length and base_size + int(length) > max_bytes:
            raise ValueError("El paquete excede el límite de bytes configurado")
        if base_size > max_bytes:
            raise ValueError("El parcial supera el límite de bytes configurado")
        mode = "ab" if append else "wb"
        downloaded = base_size
        chunks_since_checkpoint = 0

        def save_partial_state(byte_count: int) -> None:
            if etag:
                atomic_json(
                    partial_meta_path,
                    {
                        "url_fingerprint": url_fingerprint,
                        "etag": etag,
                        "last_modified": last_modified,
                        "bytes": byte_count,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

        if etag:
            save_partial_state(downloaded)
        try:
            with part_path.open(mode) as destination:
                while True:
                    block = response.read(BLOCK_SIZE)
                    if not block:
                        break
                    downloaded += len(block)
                    if downloaded > max_bytes:
                        part_path.unlink(missing_ok=True)
                        partial_meta_path.unlink(missing_ok=True)
                        raise ValueError("El paquete excede el límite de bytes configurado")
                    destination.write(block)
                    chunks_since_checkpoint += 1
                    if chunks_since_checkpoint >= 8:
                        destination.flush()
                        os.fsync(destination.fileno())
                        save_partial_state(downloaded)
                        chunks_since_checkpoint = 0
                destination.flush()
                os.fsync(destination.fileno())
        except Exception:
            if part_path.exists():
                save_partial_state(part_path.stat().st_size)
            else:
                partial_meta_path.unlink(missing_ok=True)
            raise
        if status == 206:
            if range_end is None or range_total is None or downloaded != range_end + 1 or downloaded != range_total:
                part_path.unlink(missing_ok=True)
                partial_meta_path.unlink(missing_ok=True)
                raise ValueError("La descarga Range no coincide con los límites/tamaño anunciados")
        elif length and downloaded - base_size != int(length):
            save_partial_state(downloaded)
            raise ValueError("La respuesta HTTP terminó antes del Content-Length anunciado")
        atomic_json(
            partial_meta_path,
            {
                "url_fingerprint": url_fingerprint,
                "etag": etag,
                "last_modified": last_modified,
                "bytes": downloaded,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        return {
            "url_fingerprint": url_fingerprint,
            "final_url": public_url_without_query(final_url),
            "final_host": urlsplit(final_url).hostname,
            "etag": etag,
            "last_modified": last_modified,
            "bytes": downloaded,
        }
    finally:
        response.close()


def download_package(
    package: dict[str, Any],
    source_page: str,
    output_dir: Path = DEFAULT_OUTPUT,
    *,
    opener: Any | None = None,
    timeout: int = 60,
    max_bytes: int = MAX_PACKAGE_BYTES,
    refresh: bool = True,
) -> dict[str, Any]:
    if timeout <= 0 or max_bytes <= 0:
        raise ValueError("Timeout y max_bytes deben ser positivos")
    output_dir = assert_private_path(Path(output_dir), label="La carpeta de originales")
    output_dir.mkdir(parents=True, exist_ok=True)
    package_id = validate_package_id(str(package["id"]))
    source_page = validate_official_https_url(source_page)
    if source_page.rstrip("/") != OFFICIAL_LANDING_PAGE.rstrip("/"):
        raise ValueError("Página de origen BDP inesperada")
    url = validate_official_https_url(str(package["download_url"]))
    if package.get("captured_from") != source_page:
        raise ValueError("La URL no declara haber sido capturada desde la página BDP oficial")
    if not package.get("captured_at"):
        raise ValueError("Falta fecha de captura manual del enlace oficial")
    filename = _safe_filename(str(package["expected_filename"]))
    capture = _validate_capture(package, source_page)
    expected_sha = package.get("expected_sha256")
    if expected_sha:
        expected_sha = validate_sha256(str(expected_sha), label="SHA-256 esperado")

    target = output_dir / f"{package_id}.zip"
    sidecar = target.with_suffix(target.suffix + ".source.json")
    pending_sidecar = sidecar.with_suffix(sidecar.suffix + ".pending")
    partial = target.with_suffix(target.suffix + ".part")
    partial_meta = target.with_suffix(target.suffix + ".part.json")
    _recover_pending_download(target, sidecar, pending_sidecar)
    url_fingerprint = hashlib.sha256(url.encode("utf-8")).hexdigest()
    http_opener = opener or build_opener()
    if target.exists() and sidecar.exists():
        old = json.loads(sidecar.read_text(encoding="utf-8"))
        digest = sha256_file(target)
        old_is_valid = (
            old.get("version") == 2
            and old.get("capture_evidence_sha256") == capture["sha256"]
            and old.get("source_filename") == filename
            and old.get("package_id") == package_id
            and old.get("url_fingerprint") == url_fingerprint
            and old.get("sha256") == digest
            and old.get("download_status") == "verified"
            and (expected_sha is None or digest == expected_sha)
        )
        if old_is_valid and not refresh:
            return old
        if old_is_valid and _head_unchanged(url, old, opener=http_opener, timeout=timeout):
            partial.unlink(missing_ok=True)
            partial_meta.unlink(missing_ok=True)
            return old
    if target.exists() and not sidecar.exists():
        raise ValueError("Existe un ZIP sin sidecar de procedencia; no se acepta como descarga verificada")

    response_meta = _download_to_part(
        package,
        partial,
        partial_meta,
        opener=http_opener,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    digest = sha256_file(partial)
    if expected_sha and digest != expected_sha:
        partial.unlink(missing_ok=True)
        partial_meta.unlink(missing_ok=True)
        raise ValueError("SHA-256 descargado no coincide con el valor fijado en el catálogo")
    try:
        inventory = _archive_inventory(partial)
    except Exception:
        # Una respuesta completa pero inválida no es un checkpoint reanudable;
        # evita que el siguiente intento solicite Range desde EOF.
        partial.unlink(missing_ok=True)
        partial_meta.unlink(missing_ok=True)
        raise
    previous_archive = _preserve_previous_revision(target, sidecar, output_dir, package_id)
    record = {
        "version": 2,
        "package_id": package_id,
        "filename": target.name,
        "source_filename": filename,
        "bytes": partial.stat().st_size,
        "sha256": digest,
        "source_page": source_page,
        "captured_from": source_page,
        "captured_at": package["captured_at"],
        "capture_evidence_path": capture["path"],
        "capture_evidence_sha256": capture["sha256"],
        "capture_method": str(capture["request_method"]).upper(),
        "capture_response_status": capture["response_status"],
        "capture_content_type": capture["content_type"],
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "url_fingerprint": response_meta["url_fingerprint"],
        "final_url": response_meta["final_url"],
        "final_host": response_meta["final_host"],
        "etag": response_meta["etag"],
        "last_modified": response_meta["last_modified"],
        "expected_sha256": expected_sha,
        "previous_archive": previous_archive,
        "zip_csv_members": inventory,
        "download_status": "verified",
        "verification": [
            "HTTPS",
            "origen y redirecciones bajo spensiones.cl",
            "ZIP legible y CRC de todos sus miembros",
            "SHA-256 local registrado" + (" y cotejado con catálogo" if expected_sha else "; SP no aportó hash previo"),
        ],
        "redistribution_status": "not_reviewed",
    }
    atomic_json(pending_sidecar, record)
    os.replace(partial, target)
    os.replace(pending_sidecar, sidecar)
    partial_meta.unlink(missing_ok=True)
    return record


def download_catalog(
    catalog_path: Path = DEFAULT_CATALOG,
    output_dir: Path = DEFAULT_OUTPUT,
    *,
    opener: Any | None = None,
    timeout: int = 60,
    max_bytes: int = MAX_PACKAGE_BYTES,
    refresh: bool = True,
) -> list[dict[str, Any]]:
    catalog = load_catalog(catalog_path)
    records = []
    for package in catalog["packages"]:
        records.append(
            download_package(
                package,
                catalog["source_page"],
                output_dir,
                opener=opener,
                timeout=timeout,
                max_bytes=max_bytes,
                refresh=refresh,
            )
        )
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-bytes", type=int, default=MAX_PACKAGE_BYTES)
    parser.add_argument("--check-only", action="store_true", help="Informa el bloqueo sin intentar acceder a SP")
    args = parser.parse_args(argv)
    status = catalog_status(args.catalog)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if args.check_only or not status["ready"]:
        return 0
    try:
        records = download_catalog(
            args.catalog,
            args.output,
            timeout=args.timeout,
            max_bytes=args.max_bytes,
        )
    except Exception as exc:
        print(f"Descarga BDP no verificada: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps({"descargados": records}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

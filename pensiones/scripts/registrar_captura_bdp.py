"""Construye el registro saneado de una captura UI del portal BDP de la SP.

Este script **no descarga nada y no modifica el catálogo versionado**. Sólo
materializa, bajo `.local-data/pensiones/bdp/evidencia/`, el archivo JSON de ocho
campos que `download_bdp_packages._validate_capture` exige, e imprime el bloque
exacto que una persona debe pegar en `config/paquetes_bdp.json` y revisar en un
pull request.

Los ocho campos provienen de lo observado en el navegador (pestaña Network de la
descarga real). No se aceptan cookies, headers, cuerpo POST ni valores con
apariencia de credencial: si la SP entregara un token de sesión, este script lo
rechaza en vez de persistirlo en un repositorio público.

Uso:

    python -m pensiones.scripts.registrar_captura_bdp \\
        --package-id historico_1996_2005 \\
        --request-url https://www.spensiones.cl/ruta/observada.zip \\
        --response-filename nombre_observado.zip \\
        --captured-at 2026-10-07T12:00:00Z \\
        [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .bdp_common import (
        OFFICIAL_LANDING_PAGE,
        PRIVATE_ROOT,
        REQUIRED_PACKAGE_IDS,
        ROOT,
        atomic_json,
        sha256_file,
        validate_official_https_url,
        validate_package_id,
    )
    from .download_bdp_packages import ALLOWED_ZIP_CONTENT_TYPES, CAPTURE_KEYS, _safe_filename
except ImportError:  # ejecución directa desde pensiones/scripts/
    from bdp_common import (  # type: ignore
        OFFICIAL_LANDING_PAGE,
        PRIVATE_ROOT,
        REQUIRED_PACKAGE_IDS,
        ROOT,
        atomic_json,
        sha256_file,
        validate_official_https_url,
        validate_package_id,
    )
    from download_bdp_packages import (  # type: ignore
        ALLOWED_ZIP_CONTENT_TYPES,
        CAPTURE_KEYS,
        _safe_filename,
    )

EVIDENCE_ROOT = PRIVATE_ROOT / "pensiones/bdp/evidencia"
DEFAULT_CATALOG = ROOT / "pensiones/config/paquetes_bdp.json"
# Señales de que un valor observado es una credencial y no un dato de captura.
SECRET_HINTS = ("cookie", "authorization", "bearer", "set-cookie", "phpsessid", "jsessionid")
JWT_RE = re.compile(r"^eyJ[\w-]*\.[\w-]*\.[\w-]*$")


class CaptureRejected(ValueError):
    """El valor observado parece una credencial o no cumple el esquema saneado."""


def _reject_secrets(value: str, label: str) -> str:
    lowered = (value or "").lower()
    if any(hint in lowered for hint in SECRET_HINTS):
        raise CaptureRejected(f"{label} parece contener una credencial de sesión; no se persiste")
    for token in re.split(r"[;&\s]+", value or ""):
        if JWT_RE.match(token.strip()):
            raise CaptureRejected(f"{label} contiene un token firmado (JWT); no se persiste")
    return value


def _validated_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaptureRejected("captured-at no es una fecha ISO-8601 válida") from exc
    if parsed.tzinfo is None:
        raise CaptureRejected("captured-at debe declarar zona horaria (p. ej. 2026-10-07T12:00:00Z)")
    return parsed.isoformat().replace("+00:00", "Z") if parsed.utcoffset().total_seconds() == 0 else parsed.isoformat()


def build_capture(
    *,
    package_id: str,
    request_url: str,
    response_filename: str,
    captured_at: str,
    source_page: str = OFFICIAL_LANDING_PAGE,
    referer: str | None = None,
    request_method: str = "GET",
    response_status: int = 200,
    content_type: str = "application/zip",
) -> dict[str, Any]:
    """Valida y devuelve el registro de ocho campos; no escribe en disco."""
    validate_package_id(package_id)
    if package_id not in REQUIRED_PACKAGE_IDS:
        raise CaptureRejected(
            f"{package_id} no es uno de los paquetes requeridos: {', '.join(REQUIRED_PACKAGE_IDS)}"
        )
    referer = referer or source_page
    # Cualquier rechazo de los validadores se expresa como CaptureRejected para que
    # el asistente tenga una única señal de "no se persiste esta captura".
    def _official_url(value: str, label: str) -> str:
        try:
            return validate_official_https_url(_reject_secrets(value, label))
        except ValueError as exc:
            raise CaptureRejected(f"{label}: {exc}") from exc

    try:
        filename = _safe_filename(_reject_secrets(response_filename, "response-filename"))
    except ValueError as exc:
        raise CaptureRejected(f"response-filename: {exc}") from exc

    capture = {
        "source_page": _official_url(source_page, "source-page"),
        "captured_at": _validated_timestamp(captured_at),
        "request_method": str(request_method).upper(),
        "request_url": _official_url(request_url, "request-url"),
        "referer": _official_url(referer, "referer"),
        "response_status": int(response_status),
        "content_type": str(content_type).split(";", 1)[0].strip().lower(),
        "response_filename": filename,
    }
    if set(capture) != CAPTURE_KEYS:
        raise CaptureRejected("El registro no coincide con el esquema saneado exigido")
    if capture["request_method"] != "GET":
        raise CaptureRejected(
            "Sólo se registra un GET observado. Si el portal descarga por POST o exige "
            "sesión, hay que implementar ese flujo aparte tras revisarlo; no se automatiza aquí."
        )
    if capture["response_status"] != 200:
        raise CaptureRejected("La descarga observada debe haber terminado en HTTP 200")
    if capture["content_type"] not in ALLOWED_ZIP_CONTENT_TYPES:
        raise CaptureRejected(
            f"Content-Type {capture['content_type']!r} no identifica un ZIP/binario"
        )
    if capture["referer"].rstrip("/") != capture["source_page"].rstrip("/"):
        raise CaptureRejected("El referer observado debe ser la página BDP declarada")
    return capture


def catalog_block(package_id: str, capture: dict[str, Any], evidence_ref: str, capture_sha: str, description: str) -> dict[str, Any]:
    """Bloque listo para pegar en `packages[]` del catálogo versionado."""
    return {
        "id": package_id,
        "descripcion": description,
        "download_url": capture["request_url"],
        "expected_filename": capture["response_filename"],
        # Se fija después de la primera descarga verificada; el descargador lo compara.
        "expected_sha256": None,
        "captured_from": capture["source_page"],
        "captured_at": capture["captured_at"],
        "capture_evidence": evidence_ref,
        "capture_sha256": capture_sha,
    }


def _description_from_catalog(package_id: str, catalog_path: Path) -> str:
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception:
        return package_id
    for item in catalog.get("packages", []):
        if item.get("id") == package_id:
            return str(item.get("descripcion") or package_id)
    return package_id


def register(args: argparse.Namespace) -> int:
    try:
        capture = build_capture(
            package_id=args.package_id,
            request_url=args.request_url,
            response_filename=args.response_filename,
            captured_at=args.captured_at,
            source_page=args.source_page,
            referer=args.referer,
            request_method=args.request_method,
            response_status=args.response_status,
            content_type=args.content_type,
        )
    except (CaptureRejected, ValueError) as exc:
        print(f"Captura rechazada: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    target = EVIDENCE_ROOT / f"{args.package_id}.json"
    if args.dry_run:
        print(json.dumps(capture, ensure_ascii=False, indent=2, sort_keys=True))
        print(f"[dry-run] no se escribió {target}", file=sys.stderr)
        evidence_ref = str(target.relative_to(ROOT))
        capture_sha = "<se calcula al escribir el archivo>"
    else:
        atomic_json(target, capture)
        capture_sha = sha256_file(target)
        evidence_ref = str(target.relative_to(ROOT))

    description = _description_from_catalog(args.package_id, args.catalog)
    payload = {
        "registro_escrito": None if args.dry_run else evidence_ref,
        "capture_sha256": capture_sha,
        "bloque_para_paquetes_bdp_json": catalog_block(
            args.package_id, capture, evidence_ref, capture_sha, description
        ),
        "pasos_siguientes": [
            "1. Pegar el bloque en config/paquetes_bdp.json y revisarlo en un pull request.",
            "2. Descargar con: python -m pensiones.scripts.download_bdp_packages --output .local-data/pensiones/bdp/originales",
            "3. Fijar expected_sha256 con el hash del ZIP descargado y volver a revisar.",
            "4. El gate de publicación NO se abre con esto: siguen faltando cotejo, cobertura y condiciones de redistribución.",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package-id", required=True, choices=list(REQUIRED_PACKAGE_IDS))
    parser.add_argument("--request-url", required=True, help="URL exacta de la descarga observada en el navegador")
    parser.add_argument("--response-filename", required=True, help="Nombre de archivo con que respondió el servidor")
    parser.add_argument("--captured-at", required=True, help="Fecha/hora de la observación, ISO-8601 con zona")
    parser.add_argument("--source-page", default=OFFICIAL_LANDING_PAGE)
    parser.add_argument("--referer", default=None, help="Por defecto, la página BDP")
    parser.add_argument("--request-method", default="GET")
    parser.add_argument("--response-status", type=int, default=200)
    parser.add_argument("--content-type", default="application/zip")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--dry-run", action="store_true", help="Valida e imprime sin escribir el registro")
    args = parser.parse_args(argv)
    return register(args)


if __name__ == "__main__":
    raise SystemExit(main())

"""Auditoría estructural del feed CMF antes de publicarlo en GitHub Pages."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .config import EFFECTIVE_DATE_PRECISIONS, EVENT_TYPES, SCHEMA_VERSION, SECTOR_LABELS
from .pipeline import FEED_PATH, STATE_PATH, _date_value_valid, _effective_date_matches_evidence


class AuditFailure(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditFailure(f"No se puede leer JSON válido en {path}: {type(exc).__name__}") from None
    if not isinstance(value, dict):
        raise AuditFailure(f"La raíz de {path} debe ser un objeto JSON.")
    return value


def _is_official_url(value: str) -> bool:
    try:
        parts = urlsplit(value)
        return parts.scheme == "https" and (parts.hostname or "").lower() == "www.cmfchile.cl"
    except ValueError:
        return False


def _evidence_key(value: Any) -> str:
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    unaccented = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in unaccented.casefold() if char.isalnum())


def _valid_evidence_item(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("quote"), str)
        and bool(value["quote"].strip())
        and isinstance(value.get("page"), int)
        and not isinstance(value.get("page"), bool)
        and value["page"] >= 0
    )


def validate_feed(feed: dict[str, Any], *, require_run: bool = False) -> list[str]:
    errors: list[str] = []
    if feed.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version debe ser {SCHEMA_VERSION}.")
    if not _is_official_url(str(feed.get("source_url", ""))):
        errors.append("source_url no corresponde al dominio HTTPS oficial de la CMF.")
    events = feed.get("events")
    if not isinstance(events, list):
        errors.append("events debe ser una lista.")
        events = []
    if require_run and not feed.get("last_checked_at"):
        errors.append("La ejecución no dejó last_checked_at.")
    checked_at = feed.get("last_checked_at")
    if checked_at:
        try:
            parsed_checked_at = datetime.fromisoformat(str(checked_at).replace("Z", "+00:00"))
            if parsed_checked_at.tzinfo is None:
                errors.append("last_checked_at debe incluir zona horaria.")
        except ValueError:
            errors.append("last_checked_at no es una fecha ISO válida.")
    if require_run and feed.get("status") != "ok":
        errors.append("status debe ser 'ok' luego de una consulta exitosa.")
    last_detected_at = feed.get("last_detected_at")
    if last_detected_at:
        try:
            detected_moment = datetime.fromisoformat(str(last_detected_at).replace("Z", "+00:00"))
            if detected_moment.tzinfo is None:
                errors.append("last_detected_at debe incluir zona horaria.")
        except ValueError:
            errors.append("last_detected_at no es una fecha ISO válida.")

    seen_ids: set[str] = set()
    for index, event in enumerate(events):
        prefix = f"events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} debe ser un objeto.")
            continue
        event_id = str(event.get("id", ""))
        if not event_id or event_id in seen_ids:
            errors.append(f"{prefix}.id vacío o duplicado: {event_id!r}.")
        seen_ids.add(event_id)
        publication_date = event.get("publication_date")
        if publication_date:
            try:
                date.fromisoformat(str(publication_date))
            except ValueError:
                errors.append(f"{prefix}.publication_date no es YYYY-MM-DD.")
        elif event.get("date_precision") != "sin_fecha":
            errors.append(f"{prefix} sin fecha debe marcar date_precision='sin_fecha'.")
        if not _is_official_url(str(event.get("document_url", ""))):
            errors.append(f"{prefix}.document_url no es HTTPS del dominio CMF.")
        if event.get("source_url") and not _is_official_url(str(event["source_url"])):
            errors.append(f"{prefix}.source_url no es HTTPS del dominio CMF.")
        event_detected_at = event.get("last_detected_at")
        if event_detected_at:
            try:
                parsed_event_detection = datetime.fromisoformat(str(event_detected_at).replace("Z", "+00:00"))
                if parsed_event_detection.tzinfo is None:
                    errors.append(f"{prefix}.last_detected_at debe incluir zona horaria.")
            except ValueError:
                errors.append(f"{prefix}.last_detected_at no es una fecha ISO válida.")
        raw_sectors = event.get("sectors", [])
        if not isinstance(raw_sectors, list):
            errors.append(f"{prefix}.sectors debe ser una lista.")
            sectors: list[str] = []
        else:
            sectors = [sector for sector in raw_sectors if isinstance(sector, str)]
            if len(sectors) != len(raw_sectors):
                errors.append(f"{prefix}.sectors solo puede contener códigos de texto.")
        if len(set(sectors)) != len(sectors):
            errors.append(f"{prefix}.sectors contiene códigos duplicados.")
        unknown = set(sectors) - set(SECTOR_LABELS)
        if unknown:
            errors.append(f"{prefix} contiene industrias no reconocidas: {sorted(unknown)}.")

        sector_evidence = event.get("sector_evidence", [])
        if not isinstance(sector_evidence, list):
            errors.append(f"{prefix}.sector_evidence debe ser una lista.")
            sector_evidence = []
        evidence_sectors: set[str] = set()
        for evidence in sector_evidence:
            if not _valid_evidence_item(evidence) or not isinstance(evidence.get("sector"), str):
                errors.append(f"{prefix} tiene evidencia de industria mal formada.")
                continue
            evidence_sectors.add(evidence["sector"])
        if not set(sectors).issubset(evidence_sectors):
            errors.append(f"{prefix} asigna una industria sin una cita asociada.")
        if evidence_sectors - set(sectors):
            errors.append(f"{prefix} conserva citas de industrias no asignadas.")

        raw_norms = event.get("affected_norms", [])
        if not isinstance(raw_norms, list) or any(not isinstance(norm, str) or not norm.strip() for norm in raw_norms):
            errors.append(f"{prefix}.affected_norms debe ser una lista de textos no vacíos.")
            norms: list[str] = []
        else:
            norms = raw_norms
        norm_evidence = event.get("norm_evidence", [])
        if not isinstance(norm_evidence, list):
            errors.append(f"{prefix}.norm_evidence debe ser una lista.")
            norm_evidence = []
        valid_norm_evidence = [
            evidence for evidence in norm_evidence
            if _valid_evidence_item(evidence)
            and isinstance(evidence.get("norm"), str)
            and evidence["norm"].strip()
        ]
        if len(valid_norm_evidence) != len(norm_evidence):
            errors.append(f"{prefix} tiene evidencia de norma relacionada mal formada.")
        evidence_norm_keys = [_evidence_key(evidence["norm"]) for evidence in valid_norm_evidence]
        for norm in norms:
            norm_key = _evidence_key(norm)
            if not norm_key or not any(norm_key in key or key in norm_key for key in evidence_norm_keys):
                errors.append(f"{prefix} relaciona una norma sin evidencia asociada.")
                break

        precision = event.get("effective_date_precision", "sin_fecha")
        effective_date = event.get("effective_date", "")
        if precision not in EFFECTIVE_DATE_PRECISIONS:
            errors.append(f"{prefix}.effective_date_precision inválida.")
        elif precision == "sin_fecha":
            if effective_date:
                errors.append(f"{prefix} publica fecha pero la marca sin_fecha.")
            if event.get("effective_date_evidence"):
                errors.append(f"{prefix} conserva una cita de vigencia no identificada.")
        elif not _date_value_valid(str(effective_date), precision):
            errors.append(f"{prefix}.effective_date no coincide con su precisión.")
        elif not isinstance(event.get("effective_date_evidence"), str) or not event["effective_date_evidence"].strip():
            errors.append(f"{prefix} publica vigencia sin cita de respaldo.")
        elif not _effective_date_matches_evidence(str(effective_date), str(precision), event["effective_date_evidence"]):
            errors.append(f"{prefix} publica vigencia incompatible con la cita.")
        elif not isinstance(event.get("effective_date_page"), int) or isinstance(event.get("effective_date_page"), bool) or event["effective_date_page"] < 0:
            errors.append(f"{prefix}.effective_date_page debe ser un entero no negativo.")

        if event.get("document_sha256") and not re.fullmatch(r"[a-f0-9]{64}", str(event["document_sha256"])):
            errors.append(f"{prefix}.document_sha256 no es SHA-256 hexadecimal.")
        analysis_status = event.get("analysis_status")
        if analysis_status not in (None, "complete", "pendiente"):
            errors.append(f"{prefix}.analysis_status debe ser complete o pendiente.")
        if analysis_status == "complete":
            if not isinstance(event.get("event_type"), str) or event["event_type"] not in EVENT_TYPES:
                errors.append(f"{prefix}.event_type no está en la taxonomía.")
            if not isinstance(event.get("summary"), str) or not event["summary"].strip():
                errors.append(f"{prefix} figura analizado pero carece de resumen.")
            if not isinstance(event.get("summary_evidence"), str) or not event["summary_evidence"].strip():
                errors.append(f"{prefix} figura analizado pero carece de evidencia del resumen.")
            page = event.get("summary_evidence_page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 0:
                errors.append(f"{prefix}.summary_evidence_page debe ser un entero no negativo.")
            elif page == 0:
                quote_key = _evidence_key(event.get("summary_evidence"))
                description_key = _evidence_key(event.get("description_cmf"))
                if len(quote_key) < 12 or quote_key not in description_key:
                    errors.append(f"{prefix} usa página 0 para el resumen sin cita literal del listado CMF.")
            confidence = event.get("confidence")
            if not isinstance(confidence, str) or confidence not in {"alta", "media", "baja"}:
                errors.append(f"{prefix}.confidence no es una categoría válida.")
            if not isinstance(event.get("needs_human_review"), bool):
                errors.append(f"{prefix}.needs_human_review debe ser booleano.")
        if analysis_status == "pendiente" and event.get("needs_human_review") is not True:
            errors.append(f"{prefix} tiene análisis pendiente sin revisión humana marcada.")
        if not sectors and event.get("needs_human_review") is not True:
            errors.append(f"{prefix} carece de industria y no está marcada para revisión.")
        review_flags = event.get("review_flags", [])
        if not isinstance(review_flags, list) or any(not isinstance(flag, str) for flag in review_flags):
            errors.append(f"{prefix}.review_flags debe ser una lista de textos.")
        elif review_flags and event.get("needs_human_review") is not True:
            errors.append(f"{prefix} tiene alertas de revisión sin marcar revisión humana.")
        if len(str(event.get("summary", ""))) > 650:
            errors.append(f"{prefix}.summary supera el límite de interfaz.")

    summary = feed.get("run_summary")
    if not isinstance(summary, dict):
        errors.append("run_summary debe ser un objeto.")
    else:
        actual_unassigned = sum(1 for event in events if isinstance(event, dict) and not event.get("sectors"))
        actual_pending = sum(
            1 for event in events
            if isinstance(event, dict) and event.get("analysis_status") != "complete"
        )
        if summary.get("unassigned_records") != actual_unassigned:
            errors.append("run_summary.unassigned_records no coincide con el feed.")
        if summary.get("pending_analysis") != actual_pending:
            errors.append("run_summary.pending_analysis no coincide con el feed.")
        for field in ("listed_records", "new_or_changed_records", "pdf_checks", "gemini_calls"):
            value = summary.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"run_summary.{field} debe ser un entero no negativo.")
    if require_run and not events:
        # Puede ser legítimo no encontrar una publicación reciente, pero un
        # feed vacío inicial o una respuesta de error no debe llegar a main.
        if not feed.get("last_checked_at"):
            errors.append("Feed vacío sin marca de consulta exitosa.")
    return errors


def audit(feed_path: Path = FEED_PATH, state_path: Path = STATE_PATH, *, require_run: bool = False) -> dict[str, Any]:
    feed = _load(feed_path)
    state = _load(state_path)
    errors = validate_feed(feed, require_run=require_run)
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"state.schema_version debe ser {SCHEMA_VERSION}.")
    state_items = state.get("items")
    if not isinstance(state_items, dict):
        errors.append("state.items debe ser un objeto.")
        state_items = {}
    if require_run and state.get("last_checked_at") != feed.get("last_checked_at"):
        errors.append("La fecha de consulta del estado y del feed no coincide.")
    if require_run and state.get("last_detected_at") != feed.get("last_detected_at"):
        errors.append("La fecha de última novedad detectada del estado y del feed no coincide.")
    feed_ids = {item.get("id") for item in feed.get("events", []) if isinstance(item, dict)}
    state_ids = set(state_items)
    missing = feed_ids - state_ids
    if missing:
        errors.append(f"Hay {len(missing)} registros publicados que faltan del índice incremental.")
    # Cinturón de seguridad: el feed no debe contener accidentalmente claves o
    # nombres de variables secretas. No se inspeccionan ni muestran sus valores.
    serialized = json.dumps(feed, ensure_ascii=False).lower()
    if "api_google_ai_studio" in serialized or "gemini_api_key" in serialized or "do-not-store-this-key" in serialized:
        errors.append("El feed contiene un nombre o marcador de secreto.")
    if errors:
        raise AuditFailure("\n".join(errors))
    return {
        "feed_path": str(feed_path),
        "events": len(feed.get("events", [])),
        "state_items": len(state_items),
        "last_checked_at": feed.get("last_checked_at"),
        "status": feed.get("status", "sin_ejecucion"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audita el feed público de novedades normativas CMF")
    parser.add_argument("--feed", type=Path, default=FEED_PATH)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--require-run", action="store_true", help="exige una consulta exitosa de CMF")
    args = parser.parse_args(argv)
    try:
        report = audit(args.feed, args.state, require_run=args.require_run)
    except AuditFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        "AUDITORÍA CMF OK: "
        f"{report['events']} publicaciones · {report['state_items']} claves incrementales · "
        f"última consulta {report['last_checked_at'] or 'pendiente de primera ejecución'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

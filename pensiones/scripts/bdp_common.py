"""Helpers comunes para descarga, staging y auditoría de la BDP de la SP."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import BinaryIO, Iterable
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = (ROOT / ".local-data").resolve()
OFFICIAL_LANDING_PAGE = "https://www.spensiones.cl/apps/bdp/index.php"
OFFICIAL_HOST = "spensiones.cl"
REQUIRED_PACKAGE_IDS = (
    "historico_1996_2005",
    "historico_2006_2015",
    "historico_2016_actualidad",
)

COLUMNS = tuple(
    "fecha afp tipo_de_fondo tipo_de_instrumento nemotecnico_del_instrumento "
    "nombre_del_emisor nacionalidad_del_emisor unidad_de_reajuste_de_moneda "
    "unidades precio inversion grupo_economico moneda_contrato_forward "
    "moneda_objeto_forward precio_ejercicio_forward plazo_economico "
    "tasa_pactada_del_fondo_swap tasa_pactada_de_la_contraparte_swap".split()
)
LINEAGE = (
    "archivo_fuente",
    "sha256_archivo_fuente",
    "numero_fila_fuente",
    "id_registro_fuente",
    "fecha_ingestion",
    "version_esquema",
)
SCHEMA_VERSION = "bdp-texto-v2"


def load_family_mapping() -> dict[str, str]:
    config_path = ROOT / "pensiones/config/familias_bdp.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for family, codes in config["familias"].items():
        for code in codes.split():
            if code in result:
                raise ValueError("Código en dos familias: " + code)
            result[code] = (
                "afp_" if family.startswith("derivados_") else "afp_cartera_"
            ) + family
    return result


def sha256_stream(stream: BinaryIO, deadline: float | None = None) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        if deadline is not None and time.monotonic() > deadline:
            raise TimeoutError("Tiempo máximo alcanzado mientras se calculaba SHA-256")
        digest.update(block)
    return digest.hexdigest()


def sha256_file(path: Path, deadline: float | None = None) -> str:
    with path.open("rb") as stream:
        return sha256_stream(stream, deadline)


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def assert_private_path(path: Path, *, label: str = "staging") -> Path:
    resolved = path.expanduser().resolve()
    if PRIVATE_ROOT not in resolved.parents:
        raise ValueError(f"{label} debe permanecer dentro de {PRIVATE_ROOT}")
    return resolved


def validate_package_id(package_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,79}", package_id):
        raise ValueError(f"Identificador de paquete inválido: {package_id!r}")
    return package_id


def validate_sha256(value: str, *, label: str = "SHA-256") -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{64}", value or ""):
        raise ValueError(f"{label} inválido: se esperaban 64 caracteres hexadecimales")
    return value.lower()


def validate_official_https_url(url: str) -> str:
    """Acepta sólo HTTPS en spensiones.cl o un subdominio suyo.

    La validación de host se repite en cada redirección del descargador. No se
    permiten credenciales embebidas, puertos alternativos ni fragmentos.
    """
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme.lower() != "https"
        or not host
        or not (host == OFFICIAL_HOST or host.endswith("." + OFFICIAL_HOST))
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.fragment
    ):
        raise ValueError("La URL debe ser HTTPS y pertenecer al dominio oficial spensiones.cl")
    sensitive = {
        "auth", "token", "access_token", "refresh_token", "api_key", "key",
        "signature", "sig", "expires", "session", "sessionid", "csrf", "nonce", "ticket",
    }
    if any(key.lower() in sensitive for key, _ in parse_qsl(parsed.query, keep_blank_values=True)):
        raise ValueError("La URL contiene parámetros de sesión/credenciales; no se guardan en el catálogo")
    if any(value.startswith("eyJ") and value.count(".") == 2 for _, value in parse_qsl(parsed.query)):
        raise ValueError("La URL parece contener un token firmado; no se guarda en el catálogo")
    return url


def public_url_without_query(url: str) -> str:
    """Forma segura para registrar procedencia sin persistir tokens de consulta."""
    parsed = urlsplit(url)
    return parsed._replace(query="", fragment="").geturl()


def safe_archive_member(name: str) -> str:
    """Rechaza rutas ZIP peligrosas; los miembros nunca se extraen al filesystem."""
    normalized = name.replace("\\", "/")
    parts = normalized.split("/")
    if (
        not normalized
        or normalized.startswith("/")
        or any(part in ("", ".", "..") for part in parts)
        or "\x00" in normalized
        or len(normalized) > 512
    ):
        raise ValueError(f"Ruta de miembro ZIP insegura: {name!r}")
    return normalized


def ensure_unique(items: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for item in items:
        if item in seen:
            raise ValueError(f"{label} duplicado: {item}")
        seen.add(item)

#!/usr/bin/env python3
"""Envía URLs a IndexNow (Bing, Yandex, Naver, Seznam) para indexación instantánea.

Lee docs/sitemap.xml y hace POST a https://api.indexnow.org/IndexNow con la lista de URLs.
Requiere la variable de entorno INDEXNOW_KEY (la clave que se genera en IndexNow).

Uso:
  INDEXNOW_KEY=<tu_clave> python scripts/seo_indexnow_push.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
SITEMAP = RAIZ / "docs" / "sitemap.xml"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/IndexNow"


def extraer_urls(ruta: Path) -> list[str]:
    """Extrae todas las <loc> de un sitemap XML."""
    texto = ruta.read_text(encoding="utf-8")
    urls = re.findall(r"<loc>(https?://[^<]+)</loc>", texto)
    return urls


def enviar_indexnow(key: str, urls: list[str], host: str) -> dict:
    """Envía la lista de URLs a IndexNow. Devuelve el JSON de respuesta."""
    # En un sitio de proyecto de GitHub Pages, el sitemap y el archivo de
    # verificación viven bajo /<repositorio>/. Conserva ese prefijo; usar la
    # raíz de github.io hace que IndexNow no encuentre la clave y responda 403.
    primera_url = urlparse(urls[0])
    prefijo_sitio = primera_url.path.rsplit("/", 1)[0].rstrip("/")
    key_location = f"{primera_url.scheme}://{host}{prefijo_sitio}/{key}.txt"
    payload = {
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    datos = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=datos,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            cuerpo = resp.read().decode("utf-8")
            return {"status": resp.status, "body": cuerpo}
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", errors="replace")
        return {"status": e.code, "body": cuerpo, "error": True}
    except Exception as e:  # noqa: BLE001
        return {"status": None, "body": str(e), "error": True}


def main() -> int:
    key = os.environ.get("INDEXNOW_KEY")
    if not key:
        print("ERROR: falta la variable de entorno INDEXNOW_KEY")
        return 1

    if not SITEMAP.exists():
        print(f"ERROR: no existe {SITEMAP}")
        return 1

    urls = extraer_urls(SITEMAP)
    if not urls:
        print("No se encontraron URLs en el sitemap")
        return 0

    # Extrae el host de la primera URL (debe coincidir con el sitio verificado)
    host = urlparse(urls[0]).netloc

    print(f"Enviando {len(urls)} URL(s) a IndexNow desde {host}...")
    resultado = enviar_indexnow(key, urls, host)

    if resultado.get("error"):
        print(f"ERROR IndexNow (HTTP {resultado.get('status')}): {resultado.get('body')}")
        return 1

    print(f"IndexNow OK (HTTP {resultado.get('status')}): {resultado.get('body')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

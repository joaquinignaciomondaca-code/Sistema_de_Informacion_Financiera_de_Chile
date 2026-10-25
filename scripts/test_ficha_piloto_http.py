#!/usr/bin/env python3
"""Prueba la ruta estática piloto y todas sus acciones bajo un prefijo local.

No sustituye una prueba en navegador ni una verificación del hosting público.
"""
from __future__ import annotations

from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from threading import Thread
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RUTA = "/datos/ccaf_lista_entidades/"
PREFIJO_PAGES = "/Sistema_de_Informacion_Financiera_de_Chile/"


class Recolector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.enlaces: list[str] = []
        self.scripts = 0
        self.h1 = 0
        self.th_sin_scope = 0
        self.viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        atributos = dict(attrs)
        if tag == "a" and atributos.get("href"):
            self.enlaces.append(str(atributos["href"]))
        if tag == "script":
            self.scripts += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "th" and atributos.get("scope") not in {"col", "row", "colgroup", "rowgroup"}:
            self.th_sin_scope += 1
        if tag == "meta" and atributos.get("name") == "viewport":
            self.viewport = True


def luminancia(color: str) -> float:
    color = color.removeprefix("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    canales = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lineales = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return sum(peso * canal for peso, canal in zip((0.2126, 0.7152, 0.0722), lineales))


def contraste(a: str, b: str) -> float:
    claro, oscuro = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def comprobar_accesibilidad_estatica(documento: str, parser: Recolector) -> float:
    if parser.h1 != 1 or parser.th_sin_scope:
        raise SystemExit("La ficha necesita un H1 y encabezados de tabla con scope explícito")
    if not parser.viewport:
        raise SystemExit("Falta la meta viewport para diseño adaptable")
    for regla in (":focus-visible", "@media (max-width:", "prefers-reduced-motion:reduce", "aria-label="):
        if regla not in documento:
            raise SystemExit(f"Falta una salvaguarda estática de accesibilidad/adaptación: {regla}")

    raiz = re.search(r":root\s*\{([^}]+)\}", documento)
    if not raiz:
        raise SystemExit("No se encontró la paleta CSS para medir contraste")
    colores = dict(re.findall(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})", raiz.group(1)))
    pares = [
        (colores.get("tinta"), colores.get("fondo"), 4.5, "texto principal"),
        (colores.get("secundario"), colores.get("fondo"), 4.5, "texto secundario"),
        (colores.get("enlace"), colores.get("fondo"), 4.5, "enlaces"),
        (colores.get("enlace"), colores.get("papel"), 4.5, "enlaces en tarjetas"),
        ("#ffffff", colores.get("enlace"), 4.5, "texto de botones"),
        ("#a44900", colores.get("fondo"), 3.0, "indicador de foco"),
        ("#a44900", colores.get("papel"), 3.0, "indicador de foco en tarjetas"),
        ("#3b2b12", colores.get("aviso-fondo"), 4.5, "aviso de condiciones pendientes"),
    ]
    valores = []
    for primer_plano, fondo, minimo, nombre in pares:
        if not primer_plano or not fondo:
            raise SystemExit(f"Falta un color necesario para comprobar {nombre}")
        valor = contraste(primer_plano, fondo)
        if valor < minimo:
            raise SystemExit(f"Contraste insuficiente en {nombre}: {valor:.2f}:1 (mínimo {minimo}:1)")
        valores.append(valor)
    return min(valores)


class Silencioso(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        # Simula el prefijo de proyecto de GitHub Pages, manteniendo `docs/` como
        # raíz física. Así se prueban los mismos enlaces relativos en ambas rutas.
        if path.startswith(PREFIJO_PAGES):
            path = "/" + path[len(PREFIJO_PAGES):]
        return super().translate_path(path)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    handler = partial(Silencioso, directory=str(DOCS))
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    hilo = Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    host = f"http://127.0.0.1:{servidor.server_port}"
    rutas = (RUTA, PREFIJO_PAGES + RUTA.lstrip("/"))
    try:
        for ruta in rutas:
            base = host + ruta
            with urlopen(base, timeout=10) as respuesta:
                if respuesta.status != 200 or respuesta.headers.get_content_type() != "text/html":
                    raise SystemExit(f"La ficha respondió {respuesta.status} {respuesta.headers.get_content_type()} en {ruta}")
                documento = respuesta.read().decode("utf-8")
            parser = Recolector()
            parser.feed(documento)
            if parser.scripts:
                raise SystemExit(f"La ficha requiere {parser.scripts} etiqueta(s) script")
            if "noindex,follow" not in documento:
                raise SystemExit("La ficha piloto debe permanecer fuera del índice hasta su aprobación")
            contraste_minimo = comprobar_accesibilidad_estatica(documento, parser)

            internos = []
            externos = []
            for href in parser.enlaces:
                url = urljoin(base, href)
                partes = urlsplit(url)
                if partes.scheme in {"http", "https"} and partes.netloc != urlsplit(base).netloc:
                    externos.append(url)
                    continue
                if partes.scheme not in {"http", "https"} or partes.netloc != urlsplit(base).netloc:
                    continue
                with urlopen(url, timeout=15) as respuesta:
                    if respuesta.status != 200:
                        raise SystemExit(f"Acción sin respuesta 200: {href} → {respuesta.status}")
                    respuesta.read()
                internos.append(href)

            if len(internos) != 6:
                raise SystemExit(f"Se esperaban 6 acciones internas verificables; obtenidas {len(internos)} en {ruta}")
            if len(externos) != 1 or "cmfchile.cl" not in externos[0]:
                raise SystemExit("El enlace externo de condiciones CMF falta o es inesperado")
            etiqueta = "prefijo Pages" if ruta.startswith(PREFIJO_PAGES) else "raíz Vercel asumida"
            print(f"FICHA PILOTO HTTP OK ({etiqueta}): {ruta} 200 · {len(internos)} enlaces internos 200 · sin JavaScript · contraste mínimo {contraste_minimo:.2f}:1")
        return 0
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())

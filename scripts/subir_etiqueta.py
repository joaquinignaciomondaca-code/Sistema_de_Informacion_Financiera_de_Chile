#!/usr/bin/env python3
"""Sube la etiqueta de versión de los activos locales de la web.

`docs/index.html` carga 22 archivos propios (`css/app.css` y `js/*.js`) con una
etiqueta `?v=…`. La etiqueta no es decorativa: GitHub Pages sirve los activos con
`Cache-Control: max-age=600`, así que un navegador que ya visitó el sitio sigue
usando el JavaScript viejo —hasta diez minutos— aunque el archivo nuevo ya esté
publicado. Cambiar el `?v` obliga a pedirlo de nuevo.

El 2026-10-23 se cambió `alcance.js`, `erd_graph.js`, `data_viewer.js` y
`data_dictionary.js` y **no** se subió la etiqueta: el código nuevo estaba
publicado, pero quien hubiera entrado antes podía seguir viendo el mapa con los
títulos encimados. Por eso la etiqueta ahora se cambia con un comando y no de
memoria:

    python3 scripts/subir_etiqueta.py mapa-y-cifras

Escribe la misma etiqueta en las 22 referencias, con la forma

    fl-AAAAMMDD-HHMM-<motivo>

donde la fecha y la hora son las del momento de la subida y el motivo es el
argumento (con guiones, sin espacios), para que el despliegue quede rastreable
desde el navegador —las notas de rendimiento citan la etiqueta para comparar
mediciones—.

`--check` no cambia nada: falla si las referencias no comparten una sola etiqueta
o si alguna se quedó sin ella. Lo usa `scripts/audit_interfaz.py`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INDICE = RAIZ / "docs" / "index.html"

# Sólo los activos locales: `/api/…`, enlaces externos y descargas no se tocan.
PATRON = re.compile(r'(?P<pre>(?:src|href)=")(?P<ruta>(?:css|js)/[^"?]+)(?:\?v=[^"]*)?(?P<post>")')


def motivo_valido(motivo: str) -> str:
    limpio = re.sub(r"[^a-z0-9-]+", "-", motivo.strip().lower()).strip("-")
    return limpio or "cambios"


def referencias(texto: str) -> list[str]:
    return [m.group("ruta") for m in PATRON.finditer(texto)]


def etiquetas(texto: str) -> list[str]:
    return re.findall(r'(?:src|href)="(?:css|js)/[^"?]+\?v=([^"]*)"', texto)


def revisar(texto: str) -> list[str]:
    """Lo que `--check` considera un fallo, en texto."""
    fallos = []
    rutas = referencias(texto)
    if not rutas:
        fallos.append("index.html no carga ningún activo local")
    sin_etiqueta = re.findall(r'(?:src|href)="(?:css|js)/[^"?]+"', texto)
    if sin_etiqueta:
        fallos.append(f"{len(sin_etiqueta)} activo(s) sin etiqueta de versión: "
                      + ", ".join(sin_etiqueta[:3]))
    vistas = set(etiquetas(texto))
    if len(vistas) > 1:
        fallos.append("etiquetas distintas: " + ", ".join(sorted(vistas)))
    vacias = [e for e in vistas if not e.strip()]
    if vacias:
        fallos.append("hay una etiqueta vacía (?v=)")
    return fallos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("motivo", nargs="?", default="",
                    help="texto corto que describe el cambio (se escribe en la etiqueta)")
    ap.add_argument("--check", action="store_true", help="no escribe; falla si la etiqueta no es única")
    ap.add_argument("--ahora", help=argparse.SUPPRESS)  # para pruebas: fl-AAAAMMDD-HHMM
    args = ap.parse_args()

    texto = INDICE.read_text(encoding="utf-8")
    fallos = revisar(texto)
    actual = (etiquetas(texto) or ["(ninguna)"])[0]

    if args.check:
        if fallos:
            for fallo in fallos:
                print(f"  [FALLA] {fallo}")
            print("ETIQUETA: revisa docs/index.html con scripts/subir_etiqueta.py")
            return 1
        print(f"ETIQUETA: los {len(referencias(texto))} activos locales usan «{actual}»")
        return 0

    motivo = motivo_valido(args.motivo)
    ahora = args.ahora or dt.datetime.now().strftime("%Y%m%d-%H%M")
    nueva = f"fl-{ahora}-{motivo}"

    def sustituir(m: re.Match) -> str:
        return f"{m.group('pre')}{m.group('ruta')}?v={nueva}{m.group('post')}"

    nuevo_texto, cuantos = PATRON.subn(sustituir, texto)
    if not cuantos:
        print("ETIQUETA: no se encontró ningún activo local en index.html")
        return 1
    if nuevo_texto == texto:
        print(f"ETIQUETA: ya estaba en «{nueva}» ({cuantos} activos)")
        return 0
    INDICE.write_text(nuevo_texto, encoding="utf-8")
    print(f"ETIQUETA: «{actual}» → «{nueva}» en {cuantos} activos locales")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Genera `docs/assets/og_sif_1200x630.png`, la imagen de las tarjetas sociales.

Requisito de las redes: 1200×630 PNG. El logo del sitio es un SVG de 820×180,
que no sirve como `og:image` (ni tamaño ni formato). Aquí se compone la misma
identidad —azul marino, turquesa, nodos conectados— sin depender del navegador:
sólo Pillow y las tipografías DejaVu del sistema.

Se regenera con `python3 scripts/build_og_image.py`; `--check` falla si el PNG
publicado no coincide con lo que produce este script (misma idea que el resto
del contrato: nada que se pueda desfasar en silencio).
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "docs" / "assets" / "og_sif_1200x630.png"

ANCHO, ALTO = 1200, 630
NAVY = (18, 54, 106)
TURQUESA = (0, 166, 166)
HUESO = (250, 251, 252)

FUENTES = Path("/usr/share/fonts/truetype/dejavu")


def fuente(nombre: str, tamano: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FUENTES / nombre), tamano)


# Nodos del isotipo, tomados del SVG del sitio (820×180 → se escalan aquí).
NODOS = [
    (48, 18, 10), (30, 61, 9), (56, 79, 10), (36, 102, 10), (55, 122, 8),
    (40, 143, 9), (61, 158, 9), (82, 42, 10), (20, 88, 8), (75, 91, 8),
    (67, 112, 8), (80, 128, 7), (28, 158, 7),
]
ENLACES = [
    ((48, 25), (48, 48)), ((48, 48), (30, 61)), ((30, 61), (56, 79)),
    ((56, 79), (36, 102)), ((36, 102), (55, 122)), ((55, 122), (40, 143)),
    ((40, 143), (61, 158)), ((48, 48), (78, 43)), ((30, 61), (20, 88)),
    ((56, 79), (75, 91)), ((36, 102), (67, 112)), ((55, 122), (80, 128)),
    ((40, 143), (28, 158)),
]
TURQUESA_EN = {6, 7, 10, 12}


def dibujar() -> Image.Image:
    img = Image.new("RGB", (ANCHO, ALTO), NAVY)
    d = ImageDraw.Draw(img)

    # Banda inferior más oscura: da profundidad sin competir con el texto.
    d.rectangle([0, ALTO - 132, ANCHO, ALTO], fill=(13, 40, 80))

    # Isotipo a la izquierda, escalado 3,4× desde su caja de 100×180.
    escala, ox, oy = 2.2, 100, 92
    def p(x, y):
        return (ox + x * escala, oy + y * escala)
    for (x1, y1), (x2, y2) in ENLACES:
        d.line([p(x1, y1), p(x2, y2)], fill=HUESO, width=14)
    for i, (cx, cy, r) in enumerate(NODOS):
        color = TURQUESA if i in TURQUESA_EN else HUESO
        x, y = p(cx, cy)
        d.ellipse([x - r * escala, y - r * escala, x + r * escala, y + r * escala], fill=color)

    # Texto.
    x = 420
    d.text((x, 78), "SIF", font=fuente("DejaVuSans-Bold.ttf", 88), fill=HUESO)
    d.text((x, 194), "Sistema de Información", font=fuente("DejaVuSans.ttf", 44), fill=HUESO)
    d.text((x, 248), "Financiera de Chile", font=fuente("DejaVuSans.ttf", 44), fill=HUESO)

    # Cifras: las del contrato publicado, sin adornos.
    d.line([x, 322, x + 660, 322], fill=(58, 92, 140), width=3)
    d.text((x, 344), "90 objetos · 19,8 millones de filas", font=fuente("DejaVuSans-Bold.ttf", 32), fill=TURQUESA)
    d.text((x, 394), "Bancos, seguros, fondos, cooperativas,", font=fuente("DejaVuSans.ttf", 27), fill=(200, 212, 226))
    d.text((x, 430), "fintech y macro, en Parquet y SQL", font=fuente("DejaVuSans.ttf", 27), fill=(200, 212, 226))

    # Pie: de dónde salen los datos y con qué condición. Los datos NO son CC BY:
    # son de la CMF, el BCCh y SPensiones, que autorizan republicarlos citando
    # la fuente (DATA_LICENSE.md). Decir otra cosa en una tarjeta social sería
    # publicar una licencia falsa.
    d.text((96, ALTO - 100), "Datos de la CMF, el Banco Central y la Superintendencia de Pensiones,",
           font=fuente("DejaVuSans.ttf", 23), fill=(176, 190, 208))
    d.text((96, ALTO - 68), "reproducidos citando la fuente. Código del repositorio: MIT.",
           font=fuente("DejaVuSans.ttf", 21), fill=(150, 166, 188))
    # El dominio va en la esquina inferior derecha, medido: escribirlo a ojo lo
    # sacaba del lienzo, y alinearlo con el pie lo montaba sobre la licencia.
    dominio = "joaquinignaciomondaca-code.github.io"
    f_dom = fuente("DejaVuSans.ttf", 22)
    ancho = d.textbbox((0, 0), dominio, font=f_dom)[2]
    d.text((ANCHO - 96 - ancho, ALTO - 34), dominio, font=f_dom, fill=TURQUESA)
    return img


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    img = dibujar()
    if img.size != (ANCHO, ALTO):
        print("OG-IMAGE: tamaño inesperado", img.size)
        return 1
    if args.check:
        if not DESTINO.exists():
            print(f"OG-IMAGE: falta {DESTINO.relative_to(RAIZ)}; ejecuta scripts/build_og_image.py")
            return 1
        actual = Image.open(DESTINO).convert("RGB")
        if actual.size != img.size or list(actual.getdata()) != list(img.getdata()):
            print(f"OG-IMAGE: {DESTINO.relative_to(RAIZ)} no coincide; ejecuta scripts/build_og_image.py")
            return 1
        print(f"OG-IMAGE: al día ({ANCHO}×{ALTO}, {DESTINO.stat().st_size // 1024} KB, "
              f"sha256 {hashlib.sha256(DESTINO.read_bytes()).hexdigest()[:12]})")
        return 0

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    img.save(DESTINO, "PNG", optimize=True)
    print(f"Escrito {DESTINO.relative_to(RAIZ)}: {ANCHO}×{ALTO}, "
          f"{DESTINO.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Baja tres cortes de una misma sociedad para mirar las notas antes de extraerlas.

No escribe carátula ni montos. Guarda el texto y borra el PDF.
Si una página no trae texto seleccionable, la lee con Tesseract.
El PDF se borra después de guardar el texto.
"""

from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff.cmf_pdf import descargar_pdf, ultimo_error

DEST = ROOT / "factoring_leasing" / "eeff_prueba" / "muestra_periodos"
CORTES = (
    ("96655860", "96655860-1", 2013, 12, "I"),
    ("96655860", "96655860-1", 2018, 12, "I"),
    ("96655860", "96655860-1", 2026, 3, "I"),
)
# Una carátula escaneada no llega a esto. Un pie de página sí.
_MIN_ALFANUM = 80


def _alfanum(texto: str) -> int:
    return sum(ch.isalnum() for ch in texto)


def _ocr_png(job: tuple[int, bytes]) -> tuple[int, str]:
    indice, png = job
    proc = subprocess.run(
        [
            "tesseract",
            "stdin",
            "stdout",
            "-l",
            "spa",
            "--oem",
            "1",
            "--psm",
            "6",
            "-c",
            "preserve_interword_spaces=1",
        ],
        input=png,
        capture_output=True,
        check=False,
        timeout=90,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")[:240]
        return indice, f"[ocr fallo] {err}"
    return indice, proc.stdout.decode("utf-8", errors="replace")


def _texto(blob: bytes) -> tuple[str, int]:
    import fitz

    doc = fitz.open(stream=blob, filetype="pdf")
    directos: dict[int, str] = {}
    ocr_idx: list[int] = []
    for i, page in enumerate(doc):
        texto = page.get_text("text") or ""
        if _alfanum(texto) >= _MIN_ALFANUM:
            directos[i] = texto
        else:
            ocr_idx.append(i)
    n = doc.page_count
    zoom = fitz.Matrix(200 / 72, 200 / 72)
    pngs: list[tuple[int, bytes]] = []
    for i in ocr_idx:
        pix = doc[i].get_pixmap(matrix=zoom, colorspace=fitz.csGRAY, alpha=False)
        pix.set_dpi(200, 200)
        pngs.append((i, pix.tobytes("png")))
    doc.close()
    print(f"[muestra] paginas={n} a_ocr={len(pngs)}", flush=True)
    ocr: dict[int, str] = {}
    if pngs:
        workers = min(2, os.cpu_count() or 2, len(pngs))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futuros = [pool.submit(_ocr_png, job) for job in pngs]
            for fut in as_completed(futuros):
                indice, texto = fut.result()
                ocr[indice] = texto
                print(
                    f"[muestra] ocr pagina {indice + 1}/{n} chars={_alfanum(texto)}",
                    flush=True,
                )
    partes = [
        f"--- pagina {i + 1} ---\n{ocr.get(i, directos.get(i, ''))}"
        for i in range(n)
    ]
    return "\n\n".join(partes), len(ocr_idx)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    solo = os.environ.get("MUESTRA_SOLO", "").strip()
    ok = 0
    for cuerpo, rut, year, month, preferir in CORTES:
        periodo = f"{year}-{month:02d}"
        if solo and periodo != solo:
            continue
        print(f"[muestra] {rut} {periodo} {preferir}", flush=True)
        blob, tipo, url = descargar_pdf(cuerpo, year, month, preferir=preferir)
        if not blob:
            print(f"[muestra] {rut} {periodo} sin PDF: {ultimo_error}")
            continue
        texto, ocr_paginas = _texto(blob)
        del blob
        path = DEST / f"{rut}_{periodo}.txt"
        path.write_text(
            f"rut: {rut}\nperiodo: {periodo}\ntipo_eeff: {tipo}\nocr_paginas: {ocr_paginas}\nurl_pdf: {url}\n\n{texto}",
            encoding="utf-8",
        )
        print(
            f"[muestra] {rut} {periodo} paginas={texto.count('--- pagina')} ocr={ocr_paginas} PDF borrado",
            flush=True,
        )
        ok += 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

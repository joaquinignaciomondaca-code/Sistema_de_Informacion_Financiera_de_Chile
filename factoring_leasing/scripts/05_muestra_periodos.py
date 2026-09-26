"""Baja tres cortes de una misma sociedad para mirar las notas antes de extraerlas.

No escribe carátula ni montos. Guarda el texto y borra el PDF.
"""

from __future__ import annotations

import sys
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


def _texto(blob: bytes) -> str:
    import fitz

    doc = fitz.open(stream=blob, filetype="pdf")
    partes = []
    for i, page in enumerate(doc):
        partes.append(f"--- pagina {i + 1} ---\n{page.get_text('text') or ''}")
    doc.close()
    return "\n\n".join(partes)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    ok = 0
    for cuerpo, rut, year, month, preferir in CORTES:
        periodo = f"{year}-{month:02d}"
        print(f"[muestra] {rut} {periodo} {preferir}")
        blob, tipo, url = descargar_pdf(cuerpo, year, month, preferir=preferir)
        if not blob:
            print(f"[muestra] {rut} {periodo} sin PDF: {ultimo_error}")
            continue
        texto = _texto(blob)
        del blob
        path = DEST / f"{rut}_{periodo}.txt"
        path.write_text(
            f"rut: {rut}\nperiodo: {periodo}\ntipo_eeff: {tipo}\nurl_pdf: {url}\n\n{texto}",
            encoding="utf-8",
        )
        print(f"[muestra] {rut} {periodo} paginas={texto.count('--- pagina')} PDF borrado")
        ok += 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

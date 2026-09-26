#!/usr/bin/env python3
"""EEFF de factoring y leasing desde el PDF de Información Financiera.

No parte de cero. Si el Markdown no cambió y el checkpoint está ok, no se
relee. Si un documento falla, se anota y se sigue. El checkpoint se escribe
después de cada sociedad.

La API solo valida totales. No escribe cifras en el estado. Las notas no
van a una bolsa: efectivo y deudores tienen tabla propia; las otras seis
comunes quedan marcadas como no leídas hasta que un PDF muestre la tabla.

No reintenta el TLS de CMF salvo --descargar, y solo para un Markdown que
todavía no existe (o --forzar).
"""

from __future__ import annotations

import argparse
import calendar
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff.correr import correr, listar_fuentes
from pipelines.eeff.estado import Store
from pipelines.eeff.parse_md import cargar_md

FUENTES = ROOT / "factoring_leasing" / "eeff_fuentes"
ESTADO = ROOT / "factoring_leasing" / "eeff_estado"
OUT = ROOT / "docs" / "outputs" / "factoring_leasing"
API_JSON = OUT / "factoring_leasing_balance_resumen.json"


def _objetivos_descarga(periodo: str) -> list[dict]:
    try:
        from factoring_leasing.eeff_fuentes.piloto_2026_03 import PILOTO
    except Exception:
        PILOTO = []
    if PILOTO:
        return PILOTO
    objetivos = []
    for path in listar_fuentes(FUENTES, periodo):
        meta, _ = cargar_md(path)
        if meta.get("rut"):
            objetivos.append(meta)
    return objetivos


def descargar(periodo: str, forzar: bool) -> None:
    """POST al buscador de Información Financiera. No borra un Markdown si la red falla."""
    from pipelines.eeff.cmf_pdf import descargar_pdf, pdf_a_markdown

    FUENTES.mkdir(parents=True, exist_ok=True)
    objetivos = _objetivos_descarga(periodo)
    print(f"[loop] {len(objetivos)} sociedades. Si el Markdown ya está, no se vuelve a bajar.")
    year, month = int(periodo[:4]), int(periodo[5:7])
    for doc in objetivos:
        path = FUENTES / f"{doc['rut']}_{periodo}.md"
        if path.exists() and not forzar:
            print(f"[loop] {path.name} ya está. No se redescarga.")
            continue
        cuerpo = doc["rut"].split("-")[0]
        print(f"[loop] {doc['rut']} {doc.get('razon_social', '')}")
        blob, tipo, url = descargar_pdf(cuerpo, year, month)
        if not blob:
            print(f"[loop] sin PDF {doc['rut']}. Se sigue. La fuente ya guardada no se toca.")
            continue
        md = pdf_a_markdown(blob)
        del blob
        header = (
            f"rut: {doc['rut']}\nrazon_social: {doc.get('razon_social', '')}\n"
            f"periodo: {periodo}\nfecha_corte: {year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}\n"
            f"tipo_eeff: {tipo}\nfuente: CMF PDF Estados financieros\nurl_pdf: {url}\n\n"
        )
        path.write_text(header + md, encoding="utf-8")
        del md
        print(f"[loop] {path.name} tipo={tipo}. PDF borrado de memoria.")


def main() -> None:
    parser = argparse.ArgumentParser(description="EEFF factoring y leasing, incremental")
    parser.add_argument("--periodo", default="", help="YYYY-MM. Vacío procesa todos los Markdown guardados.")
    parser.add_argument("--rut", default="", help="Un RUT. El resto no se toca.")
    parser.add_argument("--descargar", action="store_true", help="POST al buscador CMF solo si falta el Markdown")
    parser.add_argument("--forzar", action="store_true", help="Relee aunque el hash coincida. Con --descargar, vuelve a bajar.")
    parser.add_argument("--olvidar-ausentes", action="store_true", help="Quita del estado los documentos cuyo Markdown ya no está")
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.descargar:
        if not args.periodo:
            parser.error("--descargar necesita --periodo")
        descargar(args.periodo, args.forzar)
    store = Store(ESTADO)
    correr(
        FUENTES,
        store,
        OUT,
        periodo=args.periodo,
        rut=args.rut,
        forzar=args.forzar,
        api_json=API_JSON,
        olvidar_ausentes=args.olvidar_ausentes,
    )


if __name__ == "__main__":
    main()

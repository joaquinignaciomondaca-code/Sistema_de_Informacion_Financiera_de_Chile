#!/usr/bin/env python3
"""EEFF de factoring desde el PDF de Información Financiera.

Usa el buscador que ya estaba en fetch_cmf_pdf_stream (POST pestania=3).
Si CMF no responde desde esta red, lee los Markdown ya guardados en
factoring_leasing/eeff_fuentes/ (transcripción del mismo PDF / de la
visualización que publica esa ficha, no de ver_archivo.php).

La API solo valida totales.
"""

from __future__ import annotations

import argparse
import calendar
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff.canon import familia_nota
from pipelines.eeff.parse_md import cargar_md, parse_documento
from pipelines.eeff.validate_api import cuadratura_balance, validar_documento

FUENTES = ROOT / "factoring_leasing" / "eeff_fuentes"
OUT = ROOT / "docs" / "outputs" / "factoring_leasing"
API_PQ = OUT / "factoring_leasing_balance_resumen.parquet"


def _id(rut, periodo, *parts):
    slug = "_".join(str(p) for p in parts if p != "")
    return f"{rut}_{periodo.replace('-', '')}_{slug}"[:180]


def emitir_md(meta: dict, balance, resultados, indice, notas_md: str) -> str:
    lineas = [
        f"rut: {meta['rut']}",
        f"razon_social: {meta['razon_social']}",
        f"periodo: {meta['periodo']}",
        f"fecha_corte: {meta['fecha_corte']}",
        f"tipo_eeff: {meta['tipo_eeff']}",
        f"fuente: {meta['fuente']}",
        f"url_pdf: {meta.get('url_pdf', '')}",
        f"url_visualizacion: {meta.get('url_visualizacion', '')}",
        "",
        "## BALANCE",
        "nombre|nota|monto_miles|comparativo_miles|clase",
    ]
    for nombre, nota, monto, comp, clase in balance:
        lineas.append(f"{nombre}|{nota}|{monto}|{comp}|{clase}")
    lineas += ["", "## RESULTADOS", "nombre|nota|monto_miles|comparativo_miles|clase"]
    for nombre, nota, monto, comp, clase in resultados:
        lineas.append(f"{nombre}|{nota}|{monto}|{comp}|{clase}")
    lineas += ["", "## NOTAS_INDICE", "numero|titulo|pagina"]
    for numero, titulo, pagina in indice:
        lineas.append(f"{numero}|{titulo}|{pagina}")
    if notas_md:
        lineas += ["", notas_md.strip(), ""]
    return "\n".join(lineas) + "\n"


def cargar_api(periodo: str) -> dict:
    import pandas as pd
    if not API_PQ.exists():
        return {}
    df = pd.read_parquet(API_PQ)
    df = df[df["periodo"] == periodo]
    return {r["rut"]: r.to_dict() for _, r in df.iterrows()}


def construir(periodo: str = "2026-03", descargar: bool = False) -> None:
    import pandas as pd

    FUENTES.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    if descargar:
        from pipelines.eeff.cmf_pdf import descargar_pdf, pdf_a_markdown
        from factoring_leasing.eeff_fuentes.piloto_2026_03 import PILOTO
        for doc in PILOTO:
            cuerpo = doc["rut"].split("-")[0]
            year, month = int(periodo[:4]), int(periodo[5:7])
            blob, tipo, url = descargar_pdf(cuerpo, year, month)
            if not blob:
                print(f"[descarga] sin PDF {doc['rut']} {periodo} (red o periodo)")
                continue
            md = pdf_a_markdown(blob)
            header = (
                f"rut: {doc['rut']}\nrazon_social: {doc['razon_social']}\n"
                f"periodo: {periodo}\nfecha_corte: {year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}\n"
                f"tipo_eeff: {tipo}\nfuente: CMF PDF Estados financieros\nurl_pdf: {url}\n\n"
            )
            path = FUENTES / f"{doc['rut']}_{periodo}.md"
            path.write_text(header + md, encoding="utf-8")
            print(f"[descarga] {path.name} tipo={tipo} bytes={len(blob)}")

    if not any(FUENTES.glob("*.md")):
        from factoring_leasing.eeff_fuentes.piloto_2026_03 import escribir_fuentes
        escribir_fuentes(FUENTES)

    api = cargar_api(periodo)
    docs, balances, resultados, indices, notas, validaciones = [], [], [], [], [], []

    for path in sorted(FUENTES.glob("*.md")):
        meta, text = cargar_md(path)
        if meta.get("periodo") and meta["periodo"] != periodo:
            continue
        parsed = parse_documento(text, meta)
        if not parsed["balance"]:
            print(f"[parse] sin balance {path.name}")
            continue
        extraidas = {(r["numero_nota"]) for r in parsed["notas"]}
        for row in parsed["indice"]:
            row["extraida"] = 1 if row["numero_nota"] in extraidas else 0
            row["id_nota"] = _id(meta["rut"], meta["periodo"], "N", row["numero_nota"])
            indices.append(row)
        for i, row in enumerate(parsed["balance"], 1):
            row["id_linea"] = _id(meta["rut"], meta["periodo"], "B", i)
            balances.append(row)
        for i, row in enumerate(parsed["resultados"], 1):
            row["id_linea"] = _id(meta["rut"], meta["periodo"], "R", i)
            resultados.append(row)
        for i, row in enumerate(parsed["notas"], 1):
            row["id_linea"] = _id(meta["rut"], meta["periodo"], "L", row["numero_nota"], i)
            row["nota_canonica"] = row.get("nota_canonica") or familia_nota(row.get("titulo_nota", ""))
            notas.append(row)
        fila_api = api.get(meta["rut"])
        vals = validar_documento(parsed["balance"], fila_api)
        for v in vals:
            v["id_validacion"] = _id(meta["rut"], meta["periodo"], "V", v["concepto"])
            validaciones.append(v)
        cuadre = cuadratura_balance(parsed["balance"])
        estados_val = {v["estado"] for v in vals}
        if "DIFIERE" in estados_val:
            estado = "DIFIERE_API"
        elif parsed["notas"] and cuadre["estado"] == "OK":
            estado = "PDF_CON_NOTAS"
        elif parsed["notas"]:
            estado = "PDF_PARCIAL_CON_NOTAS"
        elif cuadre["estado"] == "OK":
            estado = "PDF_CARATULA"
        else:
            estado = "PDF_PARCIAL"
        docs.append({
            "id_documento": _id(meta["rut"], meta["periodo"], "DOC"),
            "rut": meta["rut"],
            "razon_social": meta.get("razon_social", ""),
            "periodo": meta["periodo"],
            "tipo_eeff": meta.get("tipo_eeff", ""),
            "url_pdf": meta.get("url_pdf", ""),
            "url_visualizacion": meta.get("url_visualizacion", ""),
            "unidad": "M$ miles CLP",
            "fuente": meta.get("fuente", "CMF PDF"),
            "notas_en_indice": len(parsed["indice"]),
            "lineas_balance": len(parsed["balance"]),
            "lineas_resultados": len(parsed["resultados"]),
            "lineas_notas": len(parsed["notas"]),
            "estado_extraccion": estado,
        })
        print(f"[ok] {meta['rut']} {meta.get('tipo_eeff','')} balance={len(parsed['balance'])} notas={len(parsed['notas'])} {estado} cuadre={cuadre}")

    tablas = {
        "factoring_leasing_eeff_documentos": docs,
        "factoring_leasing_balance_lineas": balances,
        "factoring_leasing_resultados_lineas": resultados,
        "factoring_leasing_notas_indice": indices,
        "factoring_leasing_nota_lineas": notas,
        "factoring_leasing_validacion_api": validaciones,
    }
    for nombre, filas in tablas.items():
        df = pd.DataFrame(filas)
        pq = OUT / f"{nombre}.parquet"
        js = OUT / f"{nombre}.json"
        df.to_parquet(pq, index=False)
        df.to_json(js, orient="records", force_ascii=False, indent=2)
        print(f"  {nombre}: {len(df)} filas")
    resumen = {
        "periodo": periodo,
        "documentos": len(docs),
        "validacion": {
            estado: sum(1 for v in validaciones if v["estado"] == estado)
            for estado in sorted({v["estado"] for v in validaciones})
        },
    }
    (OUT / "factoring_leasing_eeff_resumen_validacion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--periodo", default="2026-03")
    parser.add_argument("--descargar", action="store_true", help="POST al buscador CMF y baja el PDF")
    args = parser.parse_args()
    os.chdir(ROOT)
    construir(args.periodo, args.descargar)

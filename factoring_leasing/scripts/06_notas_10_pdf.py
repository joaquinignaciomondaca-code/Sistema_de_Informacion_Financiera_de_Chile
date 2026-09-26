#!/usr/bin/env python3
"""Diez PDF: cada línea de la cara, y la nota solo si suma esa línea.

No publica al monitor. No inventa la diferencia. No es el masivo. El PDF se borra.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff import cmf_pdf
from pipelines.eeff.parse_pdf_notas import extraer_notas
from pipelines.eeff.validate_api import cuadratura_balance, cuadratura_detalle, cuadratura_resultados

PRUEBA = ROOT / "factoring_leasing" / "eeff_prueba"


def _leer_pdf(blob: bytes) -> dict:
    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(blob)
        import fitz

        doc = fitz.open(path)
        paginas = [page.get_text("text") or "" for page in doc]
        doc.close()
        tablas = []
        try:
            import pdfplumber

            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    tablas.append(page.extract_tables() or [])
        except Exception as exc:
            print(f"[notas] pdfplumber no leyó tablas: {exc}")
            tablas = [[] for _ in paginas]
        return {"paginas": paginas, "tablas": tablas}
    finally:
        if os.path.exists(path):
            os.remove(path)


def _desde_04(extraido: dict, meta: dict) -> dict:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "prueba10", ROOT / "factoring_leasing" / "scripts" / "04_prueba_10_pdf.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._caratula(extraido, meta)


def _resumen(salida: dict, caratula: dict) -> dict:
    balance = caratula.get("balance", {}).get("lineas", [])
    resultados = caratula.get("resultado", {}).get("lineas", [])
    cuadre = salida["cuadre"]
    ok = sum(1 for fila in cuadre if fila["estado"] == "OK")
    no = sum(1 for fila in cuadre if fila["estado"] == "NO_LEIDA")
    eq = cuadratura_balance(balance) if balance else {"estado": "SIN_PDF"}
    det = cuadratura_detalle(balance) if balance else {"estado": "SIN_PDF", "hueco": ""}
    res = cuadratura_resultados(resultados) if resultados else {"estado": "SIN_PDF", "hueco": ""}
    caidas_b = caratula.get("balance", {}).get("caidas") or []
    caidas_r = caratula.get("resultado", {}).get("caidas") or []
    return {
        "indice": len(salida["indice"]),
        "ok": ok,
        "no_leida": no,
        "lineas_balance": len(balance),
        "lineas_resultados": len(resultados),
        "cuadre_balance": eq.get("estado"),
        "cuadre_detalle": det.get("estado"),
        "hueco_detalle": det.get("hueco", ""),
        "cuadre_resultados": res.get("estado"),
        "hueco_resultados": res.get("hueco", ""),
        "caidas_balance": [fila.get("nombre_cuenta", "") for fila in caidas_b],
        "caidas_resultados": [fila.get("nombre_cuenta", "") for fila in caidas_r],
        "cuentas": [
            {
                "cuenta": fila["cuenta"],
                "estado": fila["estado"],
                "cara_miles": fila["cara_miles"],
                "nota_miles": fila.get("nota_miles"),
                "titulo_nota": fila.get("titulo_nota", ""),
            }
            for fila in cuadre
        ],
    }


def correr(lote: list[dict], periodo: str, dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    year, month = (int(p) for p in periodo.split("-"))
    filas = []
    for item in lote:
        rut = item["rut"]
        cuerpo = rut.split("-")[0]
        meta = {
            "rut": rut,
            "razon_social": item.get("razon_social", ""),
            "periodo": periodo,
            "tipo_eeff": item.get("tipo_eeff", ""),
        }
        print(f"[notas] {rut} {periodo}", flush=True)
        blob, tipo, url = b"", "", ""
        for intento in range(4):
            blob, tipo, url = cmf_pdf.descargar_pdf(cuerpo, year, month, preferir="C")
            if blob:
                break
            print(f"[notas] {rut} intento {intento + 1}: {cmf_pdf.ultimo_error}", flush=True)
            time.sleep(8 * (intento + 1))
        if not blob:
            print(f"[notas] {rut} sin PDF")
            filas.append({"rut": rut, "error": "sin PDF", "ok": 0, "no_leida": 0})
            continue
        meta["tipo_eeff"] = tipo
        extraido = _leer_pdf(blob)
        del blob
        texto = "\n\n".join(
            f"--- pagina {i + 1} ---\n{pagina}" for i, pagina in enumerate(extraido["paginas"])
        )
        (dest / f"{rut}.txt").write_text(
            f"rut: {rut}\nperiodo: {periodo}\ntipo_eeff: {tipo}\nurl_pdf: {url}\n\n{texto}",
            encoding="utf-8",
        )
        caratula = _desde_04(extraido, meta)
        notas = extraer_notas(extraido["paginas"], extraido["tablas"], caratula["balance"]["lineas"], meta)
        (dest / f"{rut}_notas.json").write_text(
            json.dumps(notas, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (dest / f"{rut}_balance.json").write_text(
            json.dumps(caratula["balance"]["lineas"], ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (dest / f"{rut}_resultados.json").write_text(
            json.dumps(caratula["resultado"]["lineas"], ensure_ascii=False, indent=2), encoding="utf-8"
        )
        fila = {"rut": rut, "razon_social": meta["razon_social"], "tipo_eeff": tipo, "error": ""}
        fila.update(_resumen(notas, caratula))
        filas.append(fila)
        print(
            f"[notas] {rut} indice={fila['indice']} ok={fila['ok']} no_leida={fila['no_leida']} "
            f"balance={fila['lineas_balance']} {fila['cuadre_balance']} "
            f"caidas={len(fila['caidas_balance'])}+{len(fila['caidas_resultados'])} "
            f"resultados={fila['lineas_resultados']} {fila['cuadre_resultados']} PDF borrado",
            flush=True,
        )
    (dest / "resumen.json").write_text(json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")
    lineas = ["# Diez PDF: cada línea de la cara, y la nota si suma", ""]
    caidas = 0
    for fila in filas:
        caidas += len(fila.get("caidas_balance") or []) + len(fila.get("caidas_resultados") or [])
        lineas.append(
            f"- {fila.get('razon_social', '')} ({fila['rut']}): "
            f"balance={fila.get('lineas_balance', 0)} {fila.get('cuadre_balance', '')} "
            f"resultados={fila.get('lineas_resultados', 0)} {fila.get('cuadre_resultados', '')} "
            f"notas ok={fila.get('ok', 0)} no_leida={fila.get('no_leida', 0)} "
            f"caidas={len(fila.get('caidas_balance') or [])}+{len(fila.get('caidas_resultados') or [])}"
            + (f" error={fila['error']}" if fila.get("error") else "")
        )
        for nombre in (fila.get("caidas_balance") or [])[:8]:
            lineas.append(f"  - cara no guardada (balance): {nombre}")
        for nombre in (fila.get("caidas_resultados") or [])[:8]:
            lineas.append(f"  - cara no guardada (resultado): {nombre}")
    ok = sum(fila.get("ok", 0) for fila in filas)
    no = sum(fila.get("no_leida", 0) for fila in filas)
    lineas.append("")
    lineas.append(
        f"CALIDAD: {ok} notas calzan, {no} no leídas, {caidas} líneas de cara vistas por otra lectura y no guardadas. "
        "No se inventa la que falta. No es el masivo."
    )
    (dest / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    if any(fila.get("error") for fila in filas) or not filas:
        return 1
    return 0 if no == 0 and caidas == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lote", default=str(PRUEBA / "notas10.json"))
    parser.add_argument("--periodo", default="2026-03")
    parser.add_argument("--dest", default=str(PRUEBA / "notas10"))
    args = parser.parse_args()
    lote = json.loads(Path(args.lote).read_text(encoding="utf-8"))
    if isinstance(lote, dict):
        lote = lote["sociedades"]
    raise SystemExit(correr(lote, args.periodo, Path(args.dest)))


if __name__ == "__main__":
    main()

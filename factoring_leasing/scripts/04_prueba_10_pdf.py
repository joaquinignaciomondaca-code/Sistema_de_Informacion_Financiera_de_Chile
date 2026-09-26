#!/usr/bin/env python3
"""Prueba: diez PDF de marzo 2026. No publica y no pisa la fuente ya leída.

Baja el PDF por el buscador de Información Financiera, lo convierte, lo borra
y deja el texto en factoring_leasing/eeff_prueba/. La API se consulta en el
momento, solo para el chequeo. Si un PDF falla, se anota y se sigue.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipelines.eeff import cmf_pdf
from pipelines.eeff.cmf_pdf import descargar_pdf
from pipelines.eeff.parse_md import cargar_md
from pipelines.eeff.parse_pdf_caratula import (
    elegir,
    fold,
    lineas_apiladas,
    lineas_de_tabla,
    lineas_de_texto,
    orden_montos,
    paginas_caratula,
)
from pipelines.eeff.validate_api import (
    cuadratura_balance,
    cuadratura_detalle,
    cuadratura_resultados,
    validar_documento,
)

FUENTES = ROOT / "factoring_leasing" / "eeff_fuentes"
PRUEBA = ROOT / "factoring_leasing" / "eeff_prueba"
API_URL = "https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php"


def _objetivos(periodo: str) -> list[dict]:
    salida = []
    for path in sorted(FUENTES.glob(f"*_{periodo}.md")):
        meta, _ = cargar_md(path)
        if meta.get("rut"):
            meta["fuente_previa"] = str(path)
            salida.append(meta)
    return salida


def _extraer(blob: bytes) -> dict:
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
            tablas = [[] for _ in paginas]
            print(f"[prueba] pdfplumber no leyó tablas: {exc}")
        return {"paginas": paginas, "tablas": tablas}
    finally:
        if os.path.exists(path):
            os.remove(path)


def _puntaje_balance(lineas: list[dict]) -> int:
    if len(lineas) < 8:
        return 0
    cuadre = cuadratura_balance(lineas)
    detalle = cuadratura_detalle(lineas)
    return (4 if cuadre.get("estado") == "OK" else 0) + (1 if detalle.get("estado") == "OK" else 0)


def _puntaje_resultado(lineas: list[dict]) -> int:
    if not lineas:
        return 0
    return 1 if cuadratura_resultados(lineas).get("estado") == "OK" else 0


def _caratula(extraido: dict, meta: dict) -> dict:
    # La carátula está en las primeras páginas. Más atrás son notas que citan el estado.
    paginas = extraido["paginas"][:12]
    tablas_pdf = extraido["tablas"][:12]
    indices = paginas_caratula(paginas)
    salida = {}
    for estado, puntaje in (("balance", _puntaje_balance), ("resultado", _puntaje_resultado)):
        candidatos = []
        tablas = []
        for idx in indices.get(estado, []):
            if idx < len(tablas_pdf):
                tablas.extend(tablas_pdf[idx])
        if tablas:
            orden = orden_montos(tablas[0], meta["periodo"])
            por_tabla = []
            for tabla in tablas:
                por_tabla.extend(lineas_de_tabla(tabla, estado, meta, orden_montos(tabla, meta["periodo"])))
            candidatos.append((f"tabla:{orden}", por_tabla))
        texto = "\n".join(extraido["paginas"][idx] for idx in indices.get(estado, []) if idx < len(extraido["paginas"]))
        if texto:
            candidatos.append(("texto", lineas_de_texto(texto, estado, meta)))
            candidatos.append(("apilado", lineas_apiladas(texto, estado, meta)))
        metodo, lineas = elegir(candidatos, puntaje)
        salida[estado] = {"metodo": metodo, "lineas": lineas, "paginas": indices.get(estado, [])}
    return salida


def _api_periodo(periodo: str) -> dict:
    """Una descarga del trimestre. La llave es rut|tipo. No elige C si el PDF es I."""
    import ssl
    import urllib.request

    yyyymm = periodo.replace("-", "")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        f"{API_URL}?inicio={yyyymm}&termino={yyyymm}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, context=ctx, timeout=90) as resp:
        raw = resp.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="ignore")
    por = {}
    for line in text.splitlines():
        partes = line.rstrip("\r\n").split(";")
        if len(partes) < 7 or partes[4].strip() != "CLP":
            continue
        cuerpo, tipo, cuenta = partes[1].strip(), partes[3].strip(), partes[5].strip()
        try:
            valor = float(partes[6].strip())
        except ValueError:
            continue
        slot = por.setdefault(f"{cuerpo}|{tipo}", {"cuentas": {}})
        slot["cuentas"][cuenta] = slot["cuentas"].get(cuenta, 0.0) + valor
    return por


def _fila_api(slot: dict | None) -> dict | None:
    if not slot:
        return None
    cuentas = slot["cuentas"]

    def m(nombre: str):
        if nombre not in cuentas:
            return None
        return round(cuentas[nombre] / 1_000_000.0, 2)

    pasivo_nc = m("Total de pasivos no corrientes")
    if pasivo_nc is None:
        pasivo_nc = m("Pasivos no corrientes totales")
    cartera = 0.0
    vio = False
    for nombre in (
        "Deudores comerciales y otras cuentas por cobrar corrientes",
        "Deudores comerciales y otras cuentas por cobrar no corrientes",
        "Deudores comerciales y otras cuentas por cobrar",
    ):
        if nombre in cuentas:
            cartera += cuentas[nombre]
            vio = True
    return {
        "total_activos_m_clp": m("Total de activos"),
        "activos_liquidos_m_clp": m("Efectivo y equivalentes al efectivo"),
        "cartera_credito_m_clp": round(cartera / 1_000_000.0, 2) if vio else None,
        "pasivos_corrientes_m_clp": m("Pasivos corrientes totales"),
        "pasivos_no_corrientes_m_clp": pasivo_nc,
        "patrimonio_neto_m_clp": m("Patrimonio total"),
    }


def _total_previo(path: str) -> float | None:
    if not path or not Path(path).exists():
        return None
    _, texto = cargar_md(path)
    from pipelines.eeff.parse_md import parse_documento
    meta, _ = cargar_md(path)
    doc = parse_documento(texto, meta)
    for row in doc.get("balance") or []:
        if fold(row["nombre_cuenta"]) in {"total activos", "total de activos"}:
            return row["monto_miles_clp"]
    return None


def _resumen_fila(meta, caratula, api_fila, error: str) -> dict:
    balance = caratula.get("balance", {}).get("lineas", [])
    resultados = caratula.get("resultado", {}).get("lineas", [])
    eq = cuadratura_balance(balance) if balance else {"estado": "SIN_PDF" if error else "INCOMPLETO", "diff_m_clp": None}
    detalle = cuadratura_detalle(balance) if balance else {"estado": "SIN_PDF" if error else "INCOMPLETO", "hueco": error}
    res = cuadratura_resultados(resultados) if resultados else {"estado": "SIN_PDF" if error else "INCOMPLETO", "hueco": error}
    chequeos = validar_documento(balance, api_fila) if balance else []
    previo = _total_previo(meta.get("fuente_previa", ""))
    def _clave(nombre: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", fold(nombre))

    nuevo = next((
        row["monto_miles_clp"] for row in balance
        if _clave(row["nombre_cuenta"]) in {"total activos", "total de activos", "totales de activos"}
    ), None)
    return {
        "rut": meta["rut"],
        "razon_social": meta.get("razon_social", ""),
        "tipo_eeff": meta.get("tipo_eeff", ""),
        "error": error,
        "paginas_balance": caratula.get("balance", {}).get("paginas", []),
        "paginas_resultados": caratula.get("resultado", {}).get("paginas", []),
        "metodo_balance": caratula.get("balance", {}).get("metodo", ""),
        "metodo_resultados": caratula.get("resultado", {}).get("metodo", ""),
        "lineas_balance": len(balance),
        "lineas_resultados": len(resultados),
        "cuadre_balance": eq.get("estado"),
        "diff_balance_m_clp": eq.get("diff_m_clp"),
        "cuadre_detalle": detalle.get("estado"),
        "hueco_detalle": detalle.get("hueco", ""),
        "cuadre_resultados": res.get("estado"),
        "hueco_resultados": res.get("hueco", ""),
        "total_activos_miles": nuevo,
        "total_activos_fuente_previa": previo,
        "cruce_previo": (
            "SIN_TOTAL" if nuevo is None or previo is None
            else "IGUAL" if abs(nuevo - previo) <= 1 else "DISTINTO"
        ),
        "api": "SIN_API" if api_fila is None else "CONSULTADA",
        "chequeos_ok": sum(1 for row in chequeos if row.get("estado") == "OK"),
        "chequeos": [
            {"concepto": row["concepto"], "estado": row["estado"], "diff_m_clp": row.get("diff_m_clp")}
            for row in chequeos
        ],
    }


def reparsear(periodo: str) -> int:
    """Lee el texto ya guardado. No vuelve a bajar el PDF."""
    dest = PRUEBA / periodo
    resumen = []
    for path in sorted((dest / "texto").glob("*.txt")):
        texto = path.read_text(encoding="utf-8")
        meta = {"rut": path.stem, "periodo": periodo, "fuente": "CMF PDF Estados financieros"}
        for linea in texto.splitlines()[:6]:
            if linea.startswith("tipo_eeff:"):
                meta["tipo_eeff"] = linea.split(":", 1)[1].strip()
        paginas = re_split_paginas(texto)
        caratula = _caratula({"paginas": paginas, "tablas": [[] for _ in paginas]}, meta)
        previo = FUENTES / f"{meta['rut']}_{periodo}.md"
        if previo.exists():
            cab, _ = cargar_md(previo)
            meta["razon_social"] = cab.get("razon_social", "")
            meta["fuente_previa"] = str(previo)
        (dest / f"{meta['rut']}_balance.json").write_text(
            json.dumps(caratula["balance"]["lineas"], ensure_ascii=False, indent=2), encoding="utf-8")
        (dest / f"{meta['rut']}_resultados.json").write_text(
            json.dumps(caratula["resultado"]["lineas"], ensure_ascii=False, indent=2), encoding="utf-8")
        fila = _resumen_fila(meta, caratula, None, "")
        fila["api"] = "NO_REPETIDA"
        resumen.append(fila)
        print(
            f"[reparse] {meta['rut']} balance={fila['lineas_balance']} {fila['cuadre_balance']}/{fila['cuadre_detalle']} "
            f"resultados={fila['lineas_resultados']} {fila['cuadre_resultados']} previo={fila['cruce_previo']}"
        )
    (dest / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if resumen else 1


def re_split_paginas(texto: str) -> list[str]:
    partes = re.split(r"--- pagina \d+ ---", texto)
    return [parte for parte in partes if parte.strip()]


def _objetivos_lote(path: str, periodo: str) -> list[dict]:
    filas = json.loads(Path(path).read_text(encoding="utf-8"))
    for fila in filas:
        fila.setdefault("periodo", periodo)
        fila.setdefault("tipo_eeff", "")
    return filas


def correr(periodo: str, lote: str = "", dest_name: str = "") -> int:
    dest = PRUEBA / (dest_name or periodo)
    (dest / "texto").mkdir(parents=True, exist_ok=True)
    objetivos = _objetivos_lote(lote, periodo) if lote else _objetivos(periodo)
    print(f"[prueba] {len(objetivos)} sociedades de {periodo}")
    try:
        api = _api_periodo(periodo)
        print(f"[prueba] API del trimestre: {len(api)} rut|tipo")
    except Exception as exc:
        api = {}
        print(f"[prueba] API no respondió: {exc}. El PDF se lee igual.")
    resumen = []
    year, month = int(periodo[:4]), int(periodo[5:7])
    for meta in objetivos:
        cuerpo = meta["rut"].split("-")[0]
        print(f"[prueba] {meta['rut']} {meta.get('razon_social', '')}")
        error = ""
        caratula = {"balance": {"lineas": [], "paginas": [], "metodo": ""}, "resultado": {"lineas": [], "paginas": [], "metodo": ""}}
        tipo_pdf = meta.get("tipo_eeff", "")
        try:
            preferir = "I" if meta.get("tipo_eeff") == "Individual" else "C"
            blob, tipo, url = descargar_pdf(cuerpo, year, month, preferir=preferir)
            if not blob:
                error = cmf_pdf.ultimo_error or "sin PDF"
                print(f"[prueba] {meta['rut']} {error}")
            else:
                extraido = _extraer(blob)
                del blob
                meta = {**meta, "tipo_eeff": tipo or tipo_pdf, "fuente": "CMF PDF Estados financieros", "url_pdf": url}
                texto = "\n\n".join(f"--- pagina {i + 1} ---\n{pagina}" for i, pagina in enumerate(extraido["paginas"]))
                (dest / "texto" / f"{meta['rut']}.txt").write_text(
                    f"rut: {meta['rut']}\ntipo_eeff: {meta['tipo_eeff']}\nurl_pdf: {url}\n\n{texto}",
                    encoding="utf-8",
                )
                caratula = _caratula(extraido, meta)
                tipo_pdf = meta["tipo_eeff"]
                (dest / f"{meta['rut']}_balance.json").write_text(
                    json.dumps(caratula["balance"]["lineas"], ensure_ascii=False, indent=2), encoding="utf-8")
                (dest / f"{meta['rut']}_resultados.json").write_text(
                    json.dumps(caratula["resultado"]["lineas"], ensure_ascii=False, indent=2), encoding="utf-8")
                print(
                    f"[prueba] {meta['rut']} tipo={tipo_pdf} "
                    f"balance={len(caratula['balance']['lineas'])} "
                    f"resultados={len(caratula['resultado']['lineas'])} PDF borrado"
                )
        except Exception as exc:
            error = str(exc)
            print(f"[prueba] {meta['rut']} falló: {exc}")
        tipo_api = "C" if tipo_pdf == "Consolidado" else "I" if tipo_pdf == "Individual" else ""
        fila = _fila_api(api.get(f"{cuerpo}|{tipo_api}")) if tipo_api else None
        try:
            resumen.append(_resumen_fila(meta, caratula, fila, error))
        except Exception as exc:
            print(f"[prueba] {meta['rut']} el resumen falló: {exc}")
            resumen.append({
                "rut": meta["rut"],
                "razon_social": meta.get("razon_social", ""),
                "tipo_eeff": tipo_pdf,
                "error": error or str(exc),
                "lineas_balance": len(caratula.get("balance", {}).get("lineas", [])),
                "lineas_resultados": len(caratula.get("resultado", {}).get("lineas", [])),
                "cuadre_balance": "ERROR",
                "cuadre_detalle": "ERROR",
                "cuadre_resultados": "ERROR",
                "cruce_previo": "SIN_TOTAL",
                "api": "ERROR",
                "chequeos_ok": 0,
            })
    (dest / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    lineas = ["# Prueba 10 PDF " + periodo, ""]
    for row in resumen:
        lineas.append(
            f"- {row['razon_social']} ({row['rut']}, {row['tipo_eeff']}): "
            f"balance {row['lineas_balance']} {row['cuadre_balance']}/{row['cuadre_detalle']}, "
            f"resultados {row['lineas_resultados']} {row['cuadre_resultados']}, "
            f"previo {row['cruce_previo']}, API {row['api']} ok={row['chequeos_ok']}"
            + (f", error {row['error']}" if row["error"] else "")
        )
    (dest / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    return 0 if any(not row["error"] for row in resumen) else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba de 10 PDF de factoring")
    parser.add_argument("--periodo", default="2026-03")
    parser.add_argument("--lote", default="", help="JSON con rut y razon_social. No usa los Markdown ya leídos.")
    parser.add_argument("--dest", default="", help="Carpeta bajo eeff_prueba. Vacío usa el periodo.")
    parser.add_argument("--reparse", action="store_true", help="Lee el texto ya guardado. No baja el PDF.")
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.reparse:
        raise SystemExit(reparsear(args.periodo))
    raise SystemExit(correr(args.periodo, args.lote, args.dest))


if __name__ == "__main__":
    main()

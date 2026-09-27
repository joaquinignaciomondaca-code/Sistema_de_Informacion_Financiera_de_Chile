#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_xml_sources.py — Sonda automática de fuentes XML/XBRL oficiales por industria.

Objetivo: detectar, sin publicar ni escribir datos del sitio, si cada industria tiene
un archivo estructurado (XML IFRS o XBRL) que podamos usar en lugar de PDF/HTML.

- Solo biblioteca estándar (sin dependencias): pensado para correr en GitHub Actions.
- Salida: informe JSON + Markdown en .local-data/xml_probe/ (carpeta ignorada por git).
- No escribe Parquet, no modifica el sitio, no hace commit.

Uso:
    python scripts/probe_xml_sources.py                    # todas las sondas
    python scripts/probe_xml_sources.py --sector ffmm      # una industria
    python scripts/probe_xml_sources.py --muestras 3       # repite la sonda con ruts extra
    python scripts/probe_xml_sources.py --fail-on-missing  # falla en CI si desaparece una fuente
"""

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(BASE_DIR, ".local-data", "xml_probe")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml,text/plain,*/*",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

ENTIDAD = "https://www.cmfchile.cl/institucional/mercados/entidad.php"
IFRS_XML = "https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php"

UNIDAD_RE = re.compile(r"Expresado en (miles de [A-Za-z]+)", re.IGNORECASE)

# Cada sonda declara la industria, el tipo de entidad CMF y qué formato esperamos.
# Los ruts son muestras estables (no es un barrido del universo).
PROBES = [
    {
        "id": "corredoras_bolsa",
        "sector": "Corredoras de bolsa",
        "entidad": "COBOL",
        "pestania": "3",
        "mercado": "V",
        "formato": "xml_ifrs",
        "marcador_xml": "archivo=IVEF",
        "muestras": [("96571220", "2024-12"), ("96564330", "2024-12")],
    },
    {
        "id": "ffmm",
        "sector": "Fondos mutuos",
        "entidad": "RGFMU",
        "pestania": "3",
        "mercado": "V",
        "formato": "xml_ifrs",
        "marcador_xml": "archivo=FMEF",
        "extra": "&tipo=I&tipo_norma=IFRS",
        "muestras": [("8490", "2014-12")],
    },
    {
        "id": "fi_rescatables",
        "sector": "Fondos de inversion rescatables (FIRES)",
        "entidad": "FIRES",
        "pestania": "29",
        "mercado": "V",
        "formato": "xml_ifrs",
        "marcador_xml": "archivo=FIEF",
        "extra": "&tipo=I&tipo_norma=IFRS",
        "muestras": [("7064", "2021-12")],
    },
    {
        "id": "fi_no_rescatables",
        "sector": "Fondos de inversion no rescatables (FINRE)",
        "entidad": "FINRE",
        "pestania": "29",
        "mercado": "V",
        "formato": "xml_ifrs",
        "marcador_xml": "archivo=FIEF",
        "extra": "&tipo=I&tipo_norma=IFRS",
        "muestras": [("10001", "2021-12")],
    },
    {
        "id": "agf",
        "sector": "Administradoras generales de fondos",
        "entidad": "RGAGF",
        "pestania": "3",
        "mercado": "V",
        "formato": "xbrl",
        "extra": "&tipo=I&tipo_norma=IFRS",
        "muestras": [("96639280", "2014-12")],
    },
    {
        "id": "emisores_valores",
        "sector": "Emisores de valores (incluye CCAF y retail financiero)",
        "entidad": "RVEMI",
        "pestania": "3",
        "mercado": "V",
        "formato": "xbrl",
        "extra": "&tipo=I&tipo_norma=IFRS",
        "muestras": [("90749000", "2014-12"), ("81826800", "2016-12")],
    },
    # Pendientes: requieren definir el tipoentidad/módulo correcto antes de sondear.
    {"id": "seguros", "sector": "Companias de seguros", "formato": "xbrl", "pendiente": True,
     "nota": "CMF publica modulos 'IFRS/XBRL Mercado de Seguros' (taxonomias CL-HS y CL-BS); "
             "falta identificar el tipoentidad de la ficha por compania."},
    {"id": "cooperativas", "sector": "Cooperativas de ahorro y credito", "formato": "xbrl", "pendiente": True,
     "nota": "Sin IFRS XML identificado; revisar si existe envio XBRL como en CCAF."},
    {"id": "bancos", "sector": "Bancos", "formato": "xml_ifrs", "pendiente": True,
     "nota": "CMF entrega PDF/ZIP y reportes mensuales; no se identifico XML IFRS por entidad."},
]


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return resp.read()


def url_ficha(probe, rut, periodo):
    aa, mm = periodo.split("-")
    extra = probe.get("extra", "")
    return (f"{ENTIDAD}?mercado={probe.get('mercado', 'V')}&rut={rut}&tipoentidad={probe['entidad']}"
            f"&vig=VI&control=svs&pestania={probe['pestania']}&mm={mm}&aa={aa}{extra}")


def probe_one(probe, rut, periodo):
    resultado = {"industria": probe["id"], "sector": probe["sector"], "rut": rut,
                 "periodo": periodo, "formato_esperado": probe["formato"]}
    try:
        html = fetch(url_ficha(probe, rut, periodo)).decode("latin1", errors="ignore")
    except Exception as exc:  # red, TLS o 4xx/5xx
        resultado.update(estado="error_ficha", detalle=f"{type(exc).__name__}: {exc}")
        return resultado

    unidad = UNIDAD_RE.search(html)
    resultado["unidad_detectada"] = unidad.group(1) if unidad else None
    resultado["sin_informacion"] = "No existe informacion" in html or "No existe información" in html

    if probe["formato"] == "xml_ifrs":
        hrefs = re.findall(r'href="([^"]*ifrs_xml_verarchivo\.php[^"]*)"', html)
        objetivo = [h for h in hrefs if probe["marcador_xml"] in h]
        if not objetivo:
            resultado.update(estado="sin_xml", detalle=f"enlaces XML en pagina: {len(hrefs)}")
            return resultado
        url_xml = objetivo[0]
        if url_xml.startswith("/"):
            url_xml = "https://www.cmfchile.cl" + url_xml
        elif not url_xml.startswith("http"):
            url_xml = "https://www.cmfchile.cl/institucional/" + url_xml.replace("../", "")
        resultado["url_xml"] = url_xml
        resultado["archivo_xml"] = url_xml.split("archivo=")[-1].split("&")[0]
        try:
            crudo = fetch(url_xml)
            raiz = ET.fromstring(crudo)
            cuentas = raiz.findall(".//Cuenta")
            codigos = {c.attrib.get("CodigoCuenta") for c in cuentas if c.attrib.get("Context") == "PeriodoActual"}
            total = next((c.text for c in cuentas
                          if c.attrib.get("CodigoCuenta") in ("TotalActivos", "TotalActivo")
                          and c.attrib.get("Context") == "PeriodoActual"), None)
            resultado.update(
                estado="ok_disponible",
                bytes=len(crudo),
                raiz=raiz.tag,
                cuentas=len(cuentas),
                tiene_total_activos=bool(total),
                total_activos_muestra=total,
                codigos_clave=sorted([c for c in codigos if c.lower().startswith("total")]),
            )
        except Exception as exc:
            resultado.update(estado="xml_ilegible", detalle=f"{type(exc).__name__}: {exc}")
        return resultado

    if probe["formato"] == "xbrl":
        xbrl = re.findall(r"Estados financieros \(XBRL\)", html)
        pdf = re.findall(r"Estados financieros \(PDF\)", html)
        resultado["enlaces_xbrl"] = len(find_xbrl_hrefs(html))
        resultado["enlaces_pdf"] = len(re.findall(r'href="([^"]*safec_ifrs_verarchivo\.php[^"]*)"[^>]*>[^<]*PDF',
                                                  html, re.IGNORECASE)) or len(pdf)
        if resultado["enlaces_xbrl"]:
            resultado.update(estado="ok_disponible", detalle="XBRL disponible (revisar contra PDF)")
        elif pdf or re.search(r"Estados financieros", html):
            resultado.update(estado="solo_pdf", detalle="sin enlace XBRL en este periodo")
        else:
            resultado.update(estado="sin_xbrl", detalle="sin enlaces de estados financieros")
        return resultado

    resultado.update(estado="formato_desconocido")
    return resultado


def find_xbrl_hrefs(html):
    salida = []
    for m in re.finditer(r'href="([^"]*safec_ifrs_verarchivo\.php[^"]*)"', html):
        etiqueta = html[m.end():m.end() + 120]
        if "XBRL" in etiqueta.upper():
            salida.append(m.group(1))
    return salida


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", action="append", help="id de industria a sondear (repetible)")
    parser.add_argument("--muestras", type=int, default=1, help="cuantas muestras por industria")
    parser.add_argument("--fail-on-missing", action="store_true",
                        help="terminar con error si una fuente antes disponible no aparece")
    args = parser.parse_args()

    seleccion = [p for p in PROBES if not args.sector or p["id"] in args.sector]
    filas, pendientes = [], []

    for probe in seleccion:
        if probe.get("pendiente"):
            pendientes.append({"industria": probe["id"], "sector": probe["sector"],
                               "nota": probe["nota"]})
            continue
        for rut, periodo in probe["muestras"][: max(1, args.muestras)]:
            fila = probe_one(probe, rut, periodo)
            filas.append(fila)
            print(f"[{fila['estado']:>14}] {fila['sector']} · rut {rut} · {periodo} · "
                  f"{fila.get('detalle', fila.get('codigos_clave', ''))}")

    os.makedirs(OUT_DIR, exist_ok=True)
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    informe = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": "CMF Chile (consultas publicas) + Superintendencia de Pensiones",
        "publica_datos": False,
        "resultados": filas,
        "pendientes": pendientes,
    }
    ruta_json = os.path.join(OUT_DIR, f"xml_sources_{sello}.json")
    with open(ruta_json, "w", encoding="utf-8") as fh:
        json.dump(informe, fh, ensure_ascii=False, indent=2)

    lineas = [f"# Sonda XML/XBRL por industria — {sello}", "",
              "Sin publicación de datos: solo detección de fuentes oficiales.", "",
              "| Industria | RUT | Periodo | Formato | Estado | Detalle |", "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    for f in filas:
        detalle = f.get("detalle") or (f"cuentas={f.get('cuentas')} unidad={f.get('unidad_detectada')}")
        lineas.append(f"| {f['sector']} | {f['rut']} | {f['periodo']} | {f['formato_esperado']} "
                      f"| {f['estado']} | {detalle} |")
    if pendientes:
        lineas += ["", "## Pendientes de identificar", ""]
        lineas += [f"* **{p['sector']}**: {p['nota']}" for p in pendientes]
    ruta_md = os.path.join(OUT_DIR, f"xml_sources_{sello}.md")
    with open(ruta_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")

    print(f"\nInforme JSON: {ruta_json}")
    print(f"Informe MD:   {ruta_md}")

    faltantes = [f for f in filas if f["estado"] != "ok_disponible"]
    if args.fail_on_missing and faltantes:
        print(f"ATENCION: {len(faltantes)} sondas sin fuente estructurada disponible", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

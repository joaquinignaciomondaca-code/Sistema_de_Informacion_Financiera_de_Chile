#!/usr/bin/env python3
"""Sondeo de las industrias que viajan en el TXT IFRS de la CMF y hoy se descartan.

El archivo trimestral de la CMF trae todas las sociedades que envían estados financieros
XBRL: 368 en el cierre de 2026-06 (más de 580 en los cierres de diciembre). El extractor
`pipelines/ifrs_sectores/actualizar.py` publica 66 (AGF, securitizadoras y CCAF) y el
backfill de factoring y leasing añade los RUT de su catálogo. Todo lo demás se tira.

Antes de sumar industrias nuevas hay que saber qué hay ahí: cuántas sociedades son, de qué
giro, con qué taxonomía y —lo que decide el esfuerzo— cuántas ya están en otra tabla del
sistema y cuántas serían efectivamente nuevas. Eso es lo que responde este sondeo.

No publica nada, no escribe en docs/ y no hace commit: deja un JSON y un resumen en
`.local-data/ifrs_sectores/` (carpeta ignorada por git) y, en Actions, el resumen en el log.

Uso:
    python scripts/sondear_ifrs_sectores.py                 # baja el último trimestre
    python scripts/sondear_ifrs_sectores.py --txt archivo.txt --periodo 202606
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import ifrs_txt  # noqa: E402

INDICE = "https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php"
ARCHIVO = "https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={0}&termino={0}"
UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)", "Accept": "text/plain,text/html,*/*"}
SALIDA = RAIZ / ".local-data" / "ifrs_sectores"

# Giros reconocibles en el nombre. Es una aproximación para ordenar el sondeo, no una
# clasificación: para publicar una industria hay que cotejar contra la fuente, como ya se
# hizo con la muestra de dos filas de factoring y leasing.
GIROS = [
    ("banca", re.compile(r"\bBANCO\b|BANCARI")),
    ("seguros", re.compile(r"\bSEGUROS\b|\bCOMPAÑIA DE SEGUROS|\bASEGURADORA")),
    ("agf", re.compile(r"ADMINISTRADORA GENERAL DE FONDOS|\bA\.?\s?G\.?\s?F\.?(\s|$)")),
    ("securitizadora", re.compile(r"SECURITIZADORA")),
    ("caja_compensacion", re.compile(r"CAJA\s+DE\s+COMPENSACI")),
    ("factoring_leasing", re.compile(r"\bFACTORING\b|\bLEASING\b")),
    ("corredora_bolsa", re.compile(r"CORREDOR(?:A|ES)? DE BOLSA|AGENTE DE VALORES")),
    ("afp", re.compile(r"\bAFP\b|ADMINISTRADORA DE FONDOS DE PENSIONES")),
    ("cooperativa", re.compile(r"COOPERATIVA")),
    ("inmobiliaria", re.compile(r"INMOBILIARIA|\bINMOB\b")),
    ("holding", re.compile(r"\bHOLDING\b|\bMATRIZ\b|\bINVERSIONES\b")),
    ("salud", re.compile(r"\bISAPRE\b|\bCLINICA\b|\bSALUD\b")),
    ("energia", re.compile(r"\bENERGIA\b|\bELECTRICA\b|\bGAS\b|\bPETROL")),
    ("retail", re.compile(r"\bRETAIL\b|\bSUPERMERCADO|\bTIENDAS\b|\bCOMERCIAL\b")),
]


def giro(nombre: str) -> str:
    """Giro más probable según el nombre declarado en el archivo."""
    n = ifrs_txt.normalizar(nombre)
    return next((g for g, patron in GIROS if patron.search(n)), "sin clasificar")


def listas_del_sistema() -> dict[str, str]:
    """RUT -> industria, según los maestros ya publicados en docs/outputs.

    Sirve para distinguir «sociedad nueva para el sistema» de «sociedad que el sistema
    ya publica por otra vía» (por ejemplo un banco, cuya banca se publica con B1/B2/R1).
    """
    ruts: dict[str, str] = {}
    for ruta in sorted((RAIZ / "docs" / "outputs").glob("*/*maestro*.json")):
        try:
            filas = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(filas, list):
            continue
        industria = ruta.parent.name
        for f in filas:
            if not isinstance(f, dict):
                continue
            cuerpo = re.sub(r"\D", "", str(f.get("rut") or f.get("run_fondo") or "").split("-")[0])
            if cuerpo.isdigit():
                ruts.setdefault(cuerpo, industria)
    return ruts


def sondear(lineas, ruts_sistema: dict[str, str], ejemplos: int = 15) -> dict:
    """Resume el archivo: quién viene, con qué taxonomía y qué se está desperdiciando."""
    sociedades: dict[str, dict] = {}
    for _n, c in lineas:
        if len(c) < 9:
            continue
        per, rut, nombre, tipo, moneda, cuenta, _valor, tax, estado = c[:9]
        if not rut.isdigit():
            continue
        s = sociedades.setdefault(rut, {"rut": rut, "nombre": nombre, "periodo": per,
                                        "taxonomias": set(), "monedas": set(), "estados": set(),
                                        "tipos": set(), "cuentas": 0})
        s["taxonomias"].add(tax)
        s["monedas"].add(moneda)
        s["estados"].add(estado)
        s["tipos"].add(tipo)
        s["cuentas"] += 1

    por_giro: dict[str, list] = {}
    por_taxonomia: dict[str, int] = {}
    por_estado: dict[str, int] = {}
    cubiertas = 0
    for s in sociedades.values():
        g = giro(s["nombre"])
        industria = ruts_sistema.get(s["rut"])
        por_giro.setdefault(g, []).append({"rut": s["rut"], "nombre": s["nombre"],
                                           "en_el_sistema": industria,
                                           "taxonomia": "/".join(sorted(s["taxonomias"])),
                                           "cuentas": s["cuentas"]})
        if industria:
            cubiertas += 1
        for t in s["taxonomias"]:
            por_taxonomia[t] = por_taxonomia.get(t, 0) + 1
        for e in s["estados"]:
            por_estado[e] = por_estado.get(e, 0) + 1

    resumen_giros = []
    for g, filas_g in sorted(por_giro.items(), key=lambda kv: -len(kv[1])):
        nuevas = [f for f in filas_g if not f["en_el_sistema"]]
        resumen_giros.append({
            "giro": g, "sociedades": len(filas_g),
            "ya_en_el_sistema": len(filas_g) - len(nuevas),
            "nuevas": len(nuevas),
            "ejemplos_nuevas": sorted(nuevas, key=lambda f: -f["cuentas"])[:ejemplos],
        })
    periodos = sorted({s["periodo"] for s in sociedades.values()})
    return {
        "periodos_en_archivo": periodos,
        "sociedades": len(sociedades),
        "ya_en_el_sistema": cubiertas,
        "nuevas_para_el_sistema": len(sociedades) - cubiertas,
        "por_taxonomia": dict(sorted(por_taxonomia.items(), key=lambda kv: -kv[1])),
        "por_estado": dict(sorted(por_estado.items(), key=lambda kv: -kv[1])),
        "por_giro": resumen_giros,
    }


def descargar(url: str, timeout: int = 180) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--txt", type=Path, help="archivo ya descargado (para pruebas sin red)")
    ap.add_argument("--periodo", help="AAAAMM del trimestre (por defecto, el último del índice)")
    ap.add_argument("--ejemplos", type=int, default=15)
    a = ap.parse_args()

    if a.txt:
        raw = a.txt.read_bytes()
        periodo = a.periodo or "LOCAL"
    else:
        from html.parser import HTMLParser

        class Enlaces(HTMLParser):
            def __init__(self):
                super().__init__()
                self.enlaces: list[str] = []

            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    self.enlaces.append(dict(attrs).get("href") or "")

        indice = descargar(INDICE)
        p = Enlaces()
        p.feed(indice.decode("utf-8", errors="replace"))
        trimestres = sorted({m.group(1) for e in p.enlaces
                             for m in [re.search(r"inicio=(\d{6})&(?:amp;)?termino=\1", e)] if m})
        if not trimestres:
            print("::error::el índice de la CMF no trae trimestres")
            return 1
        periodo = a.periodo or trimestres[-1]
        raw = descargar(ARCHIVO.format(periodo))
    if not ifrs_txt.es_txt(raw):
        print("::error::la descarga no es el TXT de la CMF (¿HTML de error?)")
        return 1

    informe = sondear(ifrs_txt.lineas(raw), listas_del_sistema(), a.ejemplos)
    informe["periodo"] = periodo
    informe["generado_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    informe["fuente"] = str(a.txt) if a.txt else ARCHIVO.format(periodo)

    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"sondeo_{periodo}.json"
    ruta.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Sondeo {periodo}: {informe['sociedades']} sociedades · "
          f"{informe['ya_en_el_sistema']} ya cubiertas por el sistema · "
          f"{informe['nuevas_para_el_sistema']} nuevas")
    print(f"  Taxonomías: {informe['por_taxonomia']}")
    print(f"  Estados:    {informe['por_estado']}")
    print(f"  {'giro':<22}{'soc.':>6}{'cubiertas':>11}{'nuevas':>9}")
    for g in informe["por_giro"]:
        print(f"  {g['giro']:<22}{g['sociedades']:>6}{g['ya_en_el_sistema']:>11}{g['nuevas']:>9}")
    print(f"\nInforme: {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

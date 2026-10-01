"""Muestras reales de FIEF y su ficha CMF; solo staging, nunca publicación.

El runner de Actions alcanza la CMF aunque algunos sandbox no lo hagan. Conserva
el XML original y la ficha para pruebas/cotejo, con URL y SHA-256. No calcula ni
publica cifras de industria. Una vez disponible eeff_xml, valida también sus reglas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MUESTRAS = [
    ("7002", "FINRE", "2010-12"),
    ("7002", "FINRE", "2011-03"),
    ("7002", "FINRE", "2026-06"),
    ("7064", "FIRES", "2021-12"),
    ("9919", "FIRES", "2026-06"),
    ("9383", "FIRES", "2026-06"),
    ("7008", "FINRE", "2025-12"),
    ("7173", "FIRES", "2026-06"),
]
FICHA = (
    "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={run}&tipoentidad={tipo}"
    "&vig=VI&control=svs&pestania=29&mm={mes}&aa={anio}&tipo=I&tipo_norma=IFRS"
)
XML = (
    "https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php?archivo={archivo}"
    "&&rut={run}&&periodo={periodo}&&path=/web/ifrs_xml/fiifr/xml/&&desc_archivo=Estados_financieros_"
)


def descargar(url: str) -> bytes:
    ultimo = None
    for intento in range(3):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (SIFChile/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read(10_000_001)
            if len(raw) > 10_000_000:
                raise ValueError("respuesta mayor de 10 MB")
            return raw
        except (OSError, ValueError) as e:
            ultimo = e
            if intento < 2:
                time.sleep(3 * (intento + 1))
    raise RuntimeError(str(ultimo))


def leer(raw: bytes) -> ET.Element:
    txt = (
        raw.decode("utf-8-sig", errors="strict")
        if _utf8(raw)
        else raw.decode("latin-1")
    )
    txt = re.sub(r"^\s*<\?xml[^>]*\?>", "", txt)
    raiz = ET.fromstring(txt)
    if raiz.tag != "IFRS":
        raise ValueError("la respuesta no es XML IFRS")
    return raiz


def _utf8(raw):
    try:
        raw.decode("utf-8-sig")
        return True
    except UnicodeDecodeError:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", type=Path, default=ROOT / ".local-data" / "fi_eeff_muestra"
    )
    ap.add_argument(
        "--solo-descargar",
        action="store_true",
        help="descubrir el formato antes de validar el catálogo",
    )
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    resultados = []
    for run, tipo, periodo in MUESTRAS:
        nombre = f"{run}_{periodo}"
        r = {"run": run, "tipo_entidad": tipo, "periodo": periodo}
        try:
            url = FICHA.format(run=run, tipo=tipo, anio=periodo[:4], mes=periodo[5:])
            ficha = descargar(url)
            (args.out / f"{nombre}.html").write_bytes(ficha)
            r.update(fuente_ficha=url, sha256_ficha=hashlib.sha256(ficha).hexdigest())
            archivos = re.findall(rb"archivo=(FIEF[A-Za-z0-9_-]+\.xml)", ficha)
            if not archivos:
                r.update(estado="sin_enlace", bytes_ficha=len(ficha))
                raise ValueError("la ficha no enlaza un FIEF")
            archivo = max(archivos).decode("ascii")
            xml_url = XML.format(
                archivo=archivo, run=run, periodo=periodo.replace("-", "")
            )
            raw = descargar(xml_url)
            (args.out / f"{nombre}.xml").write_bytes(raw)
            raiz = leer(raw)
            if raiz.findtext("Identificacion/RUTFondoInforma") != run:
                raise ValueError("el XML informa otro fondo")
            cuentas = [c for c in raiz.findall("Cuenta") if not c.get("Serie")]
            r.update(
                estado="xml_descargado",
                fuente_archivo=xml_url,
                archivo=archivo,
                sha256_xml=hashlib.sha256(raw).hexdigest(),
                bytes_xml=len(raw),
                moneda=raiz.findtext(
                    "DatosPeriodo/MonedaPresentacionEstadosFinancieros"
                ),
                contextos={
                    c.tag: {e.tag: e.text for e in c} for c in raiz.find("Contextos")
                },
                cuentas_por_contexto=dict(Counter(c.get("Context") for c in cuentas)),
                codigos_por_contexto={
                    ctx: sorted(
                        {
                            (c.get("CodigoCuenta") or "").strip()
                            for c in cuentas
                            if c.get("Context") == ctx
                        }
                    )
                    for ctx in sorted({c.get("Context") for c in cuentas})
                },
            )
            if not args.solo_descargar:
                from fi.scripts import eeff_xml
                from fi.scripts.cotejo_eeff import cotejar

                registro = eeff_xml.extraer(raw, run, periodo)
                r["cotejo"] = cotejar(ficha, registro)
                r["validacion"] = registro["validacion"]
                r["estado"] = "validado"
        except (
            OSError,
            ValueError,
            RuntimeError,
            LookupError,
            TypeError,
            ET.ParseError,
        ) as e:
            r.update(error=f"{type(e).__name__}: {e}")
        resultados.append(r)
        print(
            "::notice title=FI XML muestra::"
            + json.dumps(
                {
                    k: v
                    for k, v in r.items()
                    if k not in ("contextos", "codigos_por_contexto")
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        time.sleep(0.2)
    (args.out / "muestras.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 1 if any(r.get("error") for r in resultados) else 0


if __name__ == "__main__":
    sys.exit(main())

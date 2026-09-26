"""Taxonomía de notas que comparten los EEFF IFRS chilenos.

La misma familia se usa en factoring, bancos, corredoras, cooperativas, CCAF,
AGF y securitizadoras. Si una industria no publica una nota, no se inventa
la fila: simplemente no aparece.
"""

from __future__ import annotations

import re
import unicodedata

def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return raw.lower()


def familia_nota(titulo: str) -> str:
    """Compatibilidad. El diccionario vive en alias.py: la llave no es el número."""
    from pipelines.eeff.alias import familia_nota as _familia

    return _familia(titulo)


def clase_cuenta(nombre: str, estado: str) -> str:
    blob = _fold(nombre)
    if estado == "resultado":
        if "ingreso" in blob and "gasto" not in blob and "costo" not in blob:
            return "Ingreso"
        if "costo" in blob:
            return "Costo"
        if "gasto" in blob or "deterioro" in blob:
            return "Gasto"
        return "Resultado"
    if "total de activos" == blob or blob == "total activos":
        return "Total"
    if "total de pasivos" == blob or blob == "total pasivos":
        return "Total"
    if "patrimonio total" in blob or "total patrimonio" in blob or "total de patrimonio y pasivos" in blob:
        return "Total"
    if "patrimonio" in blob or "capital" in blob or "ganancia" in blob or "reserva" in blob:
        return "Patrimonio"
    if "pasivo" in blob:
        return "Pasivo"
    if "no corriente" in blob:
        return "Activo no corriente" if "pasivo" not in blob else "Pasivo"
    if "corriente" in blob or "efectivo" in blob or "deudor" in blob:
        return "Activo"
    return "Cuenta"


_NUM = re.compile(r"^-?\(?\d{1,3}(?:\.\d{3})+(?:,\d+)?\)?$|^-?\(?\d+(?:,\d+)?\)?$")


def parse_monto_chileno(token: str):
    """Miles de pesos como vienen en el EEFF: 11.283.111 o (4.876.622) o '-'."""
    if token is None:
        return None
    raw = str(token).strip().replace("\\-", "-").replace("−", "-").replace("–", "-")
    raw = raw.replace("M$", "").replace("$", "").replace(" ", "")
    if raw == "" or raw.lower() in {"none", "nan"}:
        return None
    if raw in {"-", "—", "–", "n/a", "na"}:
        return 0.0
    negativo = raw.startswith("(") and raw.endswith(")")
    raw = raw.strip("()")
    if not _NUM.match(raw) and not re.fullmatch(r"-?\d[\d.]*(?:,\d+)?", raw):
        return None
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    else:
        # 11.283.111 es miles, no decimal. 324.875.184542.645 son dos montos pegados.
        grupos = raw.lstrip("-").split(".")
        miles_ok = len(grupos) >= 2 and 1 <= len(grupos[0]) <= 3 and all(len(g) == 3 for g in grupos[1:])
        if "." in raw and not miles_ok:
            return None
        if raw.count(".") > 1 or (raw.count(".") == 1 and len(raw.split(".")[-1]) == 3):
            raw = raw.replace(".", "")
    try:
        value = float(raw)
    except ValueError:
        return None
    return -value if negativo else value

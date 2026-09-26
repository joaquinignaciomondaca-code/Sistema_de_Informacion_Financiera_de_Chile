"""La API CMF (ver_archivo.php) no es fuente. Solo chequea totales del documento."""

from __future__ import annotations

import re

TOLERANCIA_M_CLP = 1.0

_MAPA = (
    ("total_activos", ("total de activos", "total activos", "totales de activos"), "total_activos_m_clp"),
    ("efectivo", ("efectivo y equivalentes", "efectivo y equivalente"), "activos_liquidos_m_clp"),
    ("deudores_corrientes", (
        "deudores comerciales y otras cuentas por cobrar corrientes",
        "deudores comerciales y otras cuentas por cobrar",
        "cuentas comerciales por cobrar y otras cuentas por cobrar corrientes",
        "cuentas comerciales por cobrar corrientes",
    ), "cartera_credito_m_clp"),
    ("pasivos_corrientes", (
        "pasivos corrientes totales",
        "total pasivos corrientes",
        "total de pasivos corrientes",
        "totales de pasivos corrientes",
        "total pasivo corriente",
    ), "pasivos_corrientes_m_clp"),
    ("pasivos_no_corrientes", (
        "total de pasivos no corrientes",
        "pasivos no corrientes totales",
        "total pasivos no corrientes",
        "totales de pasivos no corrientes",
        "total pasivo no corriente",
    ), "pasivos_no_corrientes_m_clp"),
    ("patrimonio", ("patrimonio total", "patrimonio neto total", "total patrimonio", "totales de patrimonio"), "patrimonio_neto_m_clp"),
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(text or "").lower())).strip()


def _buscar(lineas: list[dict], aliases: tuple[str, ...]) -> float | None:
    """El sufijo «corrientes» no esconde la línea. Un total genérico no se traga el corriente."""
    normas = [_norm(a) for a in aliases]
    for alias in normas:
        for row in lineas:
            if row.get("monto_m_clp") is None:
                continue
            if _norm(row["nombre_cuenta"]) == alias:
                return float(row["monto_m_clp"])
    candidatos = []
    vistos = set()
    for alias in normas:
        for row in lineas:
            if row.get("monto_m_clp") is None:
                continue
            nombre = _norm(row["nombre_cuenta"])
            if alias not in nombre:
                continue
            extra = nombre.replace(alias, " ", 1)
            if alias.startswith("total") and "corriente" in extra:
                continue
            clave = row.get("id_linea") or (nombre, row.get("monto_m_clp"))
            if clave in vistos:
                continue
            vistos.add(clave)
            candidatos.append(row)
    preferidos = [row for row in candidatos if "no corriente" not in _norm(row["nombre_cuenta"])]
    if len(preferidos) == 1:
        return float(preferidos[0]["monto_m_clp"])
    if len(candidatos) == 1 and "no corriente" not in _norm(candidatos[0]["nombre_cuenta"]):
        return float(candidatos[0]["monto_m_clp"])
    return None


def validar_documento(lineas_balance: list[dict], fila_api: dict | None) -> list[dict]:
    base = lineas_balance[0] if lineas_balance else {}
    salida = []
    for concepto, aliases, col_api in _MAPA:
        doc = _buscar(lineas_balance, aliases)
        api = None if fila_api is None or col_api not in fila_api else float(fila_api[col_api])
        if doc is None and api is None:
            estado = "SIN_DATO"
            diff = None
        elif doc is None:
            estado = "SOLO_API"
            diff = None
        elif api is None:
            estado = "SIN_API"
            diff = None
        else:
            diff = round(doc - api, 2)
            estado = "OK" if abs(diff) <= TOLERANCIA_M_CLP else "DIFIERE"
        salida.append({
            "rut": base.get("rut", ""),
            "razon_social": base.get("razon_social", ""),
            "periodo": base.get("periodo", ""),
            "concepto": concepto,
            "monto_documento_m_clp": doc,
            "monto_api_m_clp": api,
            "diff_m_clp": diff,
            "estado": estado,
            "fuente_documento": base.get("fuente", "EEFF PDF/MD"),
            "fuente_api": "CMF ver_archivo.php (solo validacion)",
        })
    return salida


def cuadratura_balance(lineas: list[dict]) -> dict:
    activos = _buscar(lineas, ("total de activos", "total activos", "totales de activos"))
    pasivos = _buscar(lineas, ("total de pasivos", "total pasivos", "totales de pasivos"))
    if pasivos is None:
        corrientes = _buscar(lineas, ("total pasivos corrientes", "total de pasivos corrientes", "totales de pasivos corrientes", "total pasivo corriente"))
        no_corrientes = _buscar(lineas, ("total pasivos no corrientes", "total de pasivos no corrientes", "totales de pasivos no corrientes", "total pasivo no corriente"))
        if corrientes is not None and no_corrientes is not None:
            pasivos = round(corrientes + no_corrientes, 2)
        elif corrientes is not None and no_corrientes is None and not any(
            "pasivo" in _norm(r["nombre_cuenta"]) and "no corriente" in _norm(r["nombre_cuenta"])
            for r in lineas
        ):
            pasivos = corrientes
    patrimonio = _buscar(lineas, ("patrimonio total", "patrimonio neto total", "total patrimonio", "totales de patrimonio"))
    if activos is None or pasivos is None or patrimonio is None:
        return {"estado": "INCOMPLETO", "diff_m_clp": None}
    diff = round(activos - (pasivos + patrimonio), 2)
    return {"estado": "OK" if abs(diff) <= TOLERANCIA_M_CLP else "DIFIERE", "diff_m_clp": diff, "activos": activos, "pasivos": pasivos, "patrimonio": patrimonio}

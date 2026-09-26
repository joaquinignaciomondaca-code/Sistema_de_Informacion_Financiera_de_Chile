"""La API CMF (ver_archivo.php) no es fuente. Solo chequea totales del documento."""

from __future__ import annotations

import re
import unicodedata

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
            if alias in {"total pasivos", "total de pasivos", "totales de pasivos", "total pasivo"} and "patrimonio" in nombre:
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
        crudo = None if fila_api is None else fila_api.get(col_api)
        try:
            api = None if crudo is None or crudo == "" else float(crudo)
        except (TypeError, ValueError):
            api = None
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


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", raw.lower())).strip()


def _fmt_miles(valor: float) -> str:
    entero = int(round(valor))
    signo = "-" if entero < 0 else ""
    return signo + f"{abs(entero):,}".replace(",", ".")


def _lado(nombre: str, clase: str) -> str:
    n = _fold(nombre)
    if "patrimonio" in n:
        return "Patrimonio"
    if "pasivo" in n:
        return "Pasivo"
    if "activo" in n:
        return "Activo"
    if clase in {"Activo", "Pasivo", "Patrimonio"}:
        return clase
    return ""


def _es_total_caratula(nombre: str, clase: str) -> bool:
    n = _fold(nombre)
    if clase == "Total":
        return True
    if n.startswith("total ") or n.startswith("totales "):
        return True
    return n in {"patrimonio total", "patrimonio neto total"}


def cuadratura_detalle(lineas: list[dict]) -> dict:
    """El detalle publicado tiene que sumar el subtotal que el PDF sí trae.

    No inventa la línea que falta. Una línea «atribuible» que ya es la suma
    de las anteriores no se vuelve a sumar. Un total sin ninguna línea de
    detalle no se denuncia aquí: eso lo ve la ecuación del balance.
    """
    huecos = []
    estado_lado = {
        "Activo": {"bucket": [], "stack": []},
        "Pasivo": {"bucket": [], "stack": []},
        "Patrimonio": {"bucket": [], "stack": []},
    }
    for row in lineas:
        if row.get("monto_miles_clp") is None:
            continue
        nombre_fila = row.get("nombre_cuenta", "")
        # El total combinado lo cierra la ecuación, no el rollo de un solo lado.
        if "pasivo" in _fold(nombre_fila) and "patrimonio" in _fold(nombre_fila) and _es_total_caratula(nombre_fila, row.get("clase", "")):
            continue
        lado = _lado(nombre_fila, row.get("clase", ""))
        if not lado:
            continue
        monto = float(row["monto_miles_clp"])
        nombre = row.get("nombre_cuenta", "")
        st = estado_lado[lado]
        if not _es_total_caratula(nombre, row.get("clase", "")):
            if (
                "atribuible" in _fold(nombre)
                and len(st["bucket"]) >= 2
                and abs(round(sum(st["bucket"]), 2) - monto) <= 1
            ):
                continue
            st["bucket"].append(monto)
            continue
        if st["bucket"]:
            suma = round(sum(st["bucket"]), 2)
            if abs(suma - monto) > 1:
                huecos.append(
                    f"{nombre}: detalle {_fmt_miles(suma)}, total {_fmt_miles(monto)}"
                )
            st["bucket"] = []
            st["stack"].append(monto)
            continue
        if st["stack"]:
            suma = round(sum(st["stack"]), 2)
            if abs(suma - monto) > 1:
                huecos.append(
                    f"{nombre}: faltan líneas por {_fmt_miles(monto - suma)} entre el subtotal y el total"
                )
            st["stack"] = []
    if not huecos:
        return {"estado": "OK", "hueco": ""}
    return {"estado": "FALTAN_LINEAS", "hueco": " | ".join(huecos[:4])}


def _es_atribucion(nombre: str) -> bool:
    n = _fold(nombre)
    return (
        "atribuible" in n
        or "no controlad" in n
        or n.startswith("propietarios")
        or "participaciones no" in n
    )


def _es_subtotal_resultado(nombre: str) -> bool:
    n = _fold(nombre)
    if _es_atribucion(nombre):
        return False
    # La discontinuada es un componente, aunque el nombre diga ganancia (pérdida).
    if "discontinuad" in n:
        return False
    limpio = re.sub(r"[^a-z ]", "", n).strip()
    if limpio in {"ganancia", "utilidad", "resultado", "ganancia perdida", "utilidad perdida", "ganancias perdidas"}:
        return True
    if ("operaciones continuadas" in n or "operaciones continuas" in n) and (
        "procedente" in n or "despues de impuesto" in n
    ):
        return True
    claves = (
        "ganancia bruta",
        "margen bruto",
        "ingreso neto",
        "antes de impuesto",
        "del periodo",
        "del ejercicio",
        "del ano",
        "actividades operacionales",
        "actividades de operacion",
        "resultado de operaciones",
    )
    return any(clave in n for clave in claves)


def _indices_desglose(lineas: list[dict]) -> set[int]:
    """El detalle que suma exactamente la línea anterior no se vuelve a sumar."""
    skip: set[int] = set()
    i = 0
    while i < len(lineas):
        nombre = lineas[i].get("nombre_cuenta", "")
        if _es_subtotal_resultado(nombre) or _es_atribucion(nombre):
            i += 1
            continue
        padre_c = lineas[i].get("monto_miles_clp")
        padre_k = lineas[i].get("monto_comparativo_miles_clp")
        if padre_c is None or padre_k is None:
            i += 1
            continue
        acc_c = 0.0
        acc_k = 0.0
        found = 0
        j = i + 1
        while j < len(lineas):
            hijo = lineas[j].get("nombre_cuenta", "")
            if _es_subtotal_resultado(hijo) or _es_atribucion(hijo):
                break
            c = lineas[j].get("monto_miles_clp")
            k = lineas[j].get("monto_comparativo_miles_clp")
            if c is None or k is None:
                break
            acc_c += c
            acc_k += k
            if abs(acc_c - padre_c) <= 1 and abs(acc_k - padre_k) <= 1:
                found = j
                break
            if abs(acc_c) > abs(padre_c) + 1 and abs(acc_k) > abs(padre_k) + 1:
                break
            j += 1
        if found:
            skip.update(range(i + 1, found + 1))
            i = found + 1
        else:
            i += 1
    return skip


def _roll_resultado(lineas: list[dict], campo: str, etiqueta: str) -> str:
    if not any(row.get(campo) is not None for row in lineas):
        return ""
    relevantes = [row for row in lineas if not _es_atribucion(row.get("nombre_cuenta", ""))]
    if relevantes and any(row.get(campo) is None for row in relevantes):
        return ""
    running = 0.0
    componentes = 0
    vio_subtotal = False
    neto = None
    desglose = _indices_desglose(lineas)
    for idx, row in enumerate(lineas):
        if idx in desglose:
            continue
        nombre = row.get("nombre_cuenta", "")
        if _es_atribucion(nombre):
            continue
        monto = float(row[campo])
        if _es_subtotal_resultado(nombre):
            vio_subtotal = True
            neto = monto
            if componentes == 0:
                return f"{etiqueta}: el resultado no trae las líneas que lo componen"
            if abs(round(running - monto, 2)) > 1:
                return (
                    f"{etiqueta} {nombre}: suma {_fmt_miles(running)}, "
                    f"línea {_fmt_miles(monto)}"
                )
            continue
        running += monto
        componentes += 1
    if not vio_subtotal and componentes:
        return f"{etiqueta}: no hay una línea de resultado para cerrar la suma"
    atrib = [
        float(row[campo])
        for row in lineas
        if _es_atribucion(row.get("nombre_cuenta", "")) and row.get(campo) is not None
    ]
    if atrib and neto is not None and abs(round(sum(atrib) - neto, 2)) > 1:
        return (
            f"{etiqueta}: la atribución suma {_fmt_miles(sum(atrib))} "
            f"y el resultado es {_fmt_miles(neto)}"
        )
    return ""


def cuadratura_resultados(lineas: list[dict]) -> dict:
    """Suma las líneas que no son subtotal. No completa la que falta."""
    if not lineas:
        return {"estado": "INCOMPLETO", "hueco": "sin estado de resultados"}
    corte = _roll_resultado(lineas, "monto_miles_clp", "corte")
    comp = _roll_resultado(lineas, "monto_comparativo_miles_clp", "comparativo")
    huecos = [texto for texto in (corte, comp) if texto]
    if not huecos:
        return {"estado": "OK", "hueco": ""}
    incompleto = all("no trae las líneas" in texto or texto.startswith("sin ") for texto in huecos)
    return {
        "estado": "INCOMPLETO" if incompleto else "FALTAN_LINEAS",
        "hueco": " | ".join(huecos),
    }


def cuadratura_balance(lineas: list[dict]) -> dict:
    activos = _buscar(lineas, ("total de activos", "total activos", "totales de activos"))
    pasivos = _buscar(lineas, ("total de pasivos", "total pasivos", "totales de pasivos", "total pasivo"))
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

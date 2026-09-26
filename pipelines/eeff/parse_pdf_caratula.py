"""Carátula de un PDF IFRS chileno, sin inventar líneas.

Solo lee páginas cuyo título es el estado de situación financiera o el estado
de resultados. Una fila entra si trae nombre y al menos un monto. Si la tabla
no se deja leer, no se completa con la página de al lado ni con la API.
"""

from __future__ import annotations

import re
import unicodedata

from pipelines.eeff.canon import clase_cuenta, parse_monto_chileno

_FECHA = re.compile(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}")
_NOTA = re.compile(r"^\d{1,2}$")
_ANIO = re.compile(r"20\d{2}")


def fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", raw.lower()).strip()


def _limpiar_celda(value) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u00a0", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def _es_fecha(token: str) -> bool:
    if _FECHA.search(token):
        return True
    bajo = fold(token)
    return any(mes in bajo for mes in ("enero", "marzo", "junio", "septiembre", "diciembre"))


def _monto(token: str):
    token = _limpiar_celda(token).replace("−", "-").replace("–", "-")
    if not token or _es_fecha(token):
        return None
    if not re.search(r"\d", token):
        return None
    # 6 es el número de la nota, no un saldo de 6 miles.
    if re.fullmatch(r"[1-9]\d?", token):
        return None
    return parse_monto_chileno(token)


def clasificar_pagina(texto: str) -> str:
    """El título manda. Una nota que cita el estado no abre la carátula."""
    cabeza = fold("\n".join((texto or "").splitlines()[:8]))
    if "nota " in cabeza[:40] or cabeza.startswith("notas "):
        return ""
    if "estado de situacion financiera" in cabeza or "estado de situacion" in cabeza:
        return "balance"
    if "estado de resultados" in cabeza or "estado del resultado" in cabeza:
        return "resultado"
    return ""


def paginas_caratula(textos: list[str]) -> dict[str, list[int]]:
    """Índices de las páginas de cada estado. La continuación entra; la nota no."""
    marcas = [clasificar_pagina(texto) for texto in textos]
    salida = {"balance": [], "resultado": []}
    for idx, marca in enumerate(marcas):
        if not marca:
            continue
        salida[marca].append(idx)
        if idx + 1 < len(textos) and not marcas[idx + 1]:
            siguiente = fold(textos[idx + 1][:400])
            if "continuacion" in siguiente or "continuación" in textos[idx + 1][:400].lower():
                salida[marca].append(idx + 1)
    return salida


def _montos_en_celda(celda: str) -> list[float]:
    celda = _limpiar_celda(celda)
    if not celda:
        return []
    uno = _monto(celda)
    if uno is not None:
        return [uno]
    partes = celda.split()
    if len(partes) >= 2 and all(_monto(parte) is not None for parte in partes):
        return [_monto(parte) for parte in partes]
    return []


def _fila(celdas: list[str]) -> dict | None:
    celdas = [_limpiar_celda(c) for c in celdas]
    while celdas and not celdas[-1]:
        celdas.pop()
    if not celdas:
        return None
    montos = []
    for idx, celda in enumerate(celdas):
        for monto in _montos_en_celda(celda):
            montos.append((idx, monto))
    if not montos:
        return None
    corte = montos[0][0]
    previos = celdas[:corte]
    nota = ""
    if previos and _NOTA.fullmatch(previos[-1]):
        nota = previos[-1]
        previos = previos[:-1]
    nombre = " ".join(parte for parte in previos if parte).strip(" .:-")
    if len(nombre) < 3 or fold(nombre) in {"activos", "pasivos", "patrimonio", "nota", "notas"}:
        return None
    if _es_fecha(nombre) or fold(nombre) in {"m$", "miles de pesos", "nota"}:
        return None
    return {
        "nombre": nombre,
        "nota": nota,
        "monto": montos[0][1],
        "comparativo": montos[1][1] if len(montos) > 1 else None,
        "columna": corte,
    }


def orden_montos(tabla: list[list], periodo: str) -> str:
    """corte_primero si la primera columna de montos es el periodo pedido."""
    anio, mes = periodo.split("-")
    corte_anio = anio
    for fila in tabla[:3]:
        anos = []
        for idx, celda in enumerate(fila or []):
            texto = _limpiar_celda(celda)
            hallados = _ANIO.findall(texto)
            if hallados and (_monto(texto) is None or _es_fecha(texto)):
                anos.append((idx, hallados[-1], texto))
        if len(anos) >= 2:
            primero, segundo = anos[0][1], anos[1][1]
            if primero == corte_anio and segundo != corte_anio:
                return "corte_primero"
            if segundo == corte_anio and primero != corte_anio:
                return "comparativo_primero"
            if mes == "03" and "marzo" in fold(anos[0][2]) and "diciembre" in fold(anos[1][2]):
                return "corte_primero"
    return "corte_primero"


def lineas_de_tabla(tabla: list[list], estado: str, meta: dict, orden: str) -> list[dict]:
    filas = []
    vistos = set()
    for cruda in tabla or []:
        if not cruda:
            continue
        parsed = _fila(cruda)
        if not parsed:
            continue
        monto = parsed["monto"]
        comp = parsed["comparativo"]
        if orden == "comparativo_primero":
            monto, comp = comp, monto
            if monto is None:
                continue
        clave = (fold(parsed["nombre"]), monto, comp)
        if clave in vistos:
            continue
        vistos.add(clave)
        filas.append(_linea(meta, estado, parsed["nombre"], parsed["nota"], monto, comp))
    return filas


def lineas_de_texto(texto: str, estado: str, meta: dict) -> list[dict]:
    """Respaldo cuando el PDF no trae tabla, solo texto posicionado."""
    filas = []
    vistos = set()
    pendiente = ""
    for cruda in (texto or "").splitlines():
        linea = _limpiar_celda(cruda)
        if not linea:
            continue
        parsed = _fila_texto(pendiente + " " + linea if pendiente else linea)
        if parsed is None and pendiente:
            parsed = _fila_texto(linea)
        if parsed is None:
            if _parece_nombre(linea):
                pendiente = linea
            else:
                pendiente = ""
            continue
        pendiente = ""
        clave = (fold(parsed["nombre"]), parsed["monto"], parsed["comparativo"])
        if clave in vistos:
            continue
        vistos.add(clave)
        filas.append(_linea(meta, estado, parsed["nombre"], parsed["nota"], parsed["monto"], parsed["comparativo"]))
    return filas


def _parece_nombre(linea: str) -> bool:
    if len(linea) < 4 or _monto(linea) is not None:
        return False
    if _es_fecha(linea) or fold(linea).startswith("estado de"):
        return False
    return bool(re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]", linea))


def _fila_texto(linea: str) -> dict | None:
    tokens = linea.split()
    if len(tokens) < 3:
        return None
    montos = []
    for idx in range(len(tokens) - 1, -1, -1):
        monto = _monto(tokens[idx])
        if monto is None or not re.search(r"\d", tokens[idx]):
            break
        montos.append((idx, monto))
        if len(montos) == 2:
            break
    if len(montos) < 2:
        return None
    montos.reverse()
    corte = montos[0][0]
    nota = ""
    nombre_tokens = tokens[:corte]
    if nombre_tokens and _NOTA.fullmatch(nombre_tokens[-1]):
        nota = nombre_tokens[-1]
        nombre_tokens = nombre_tokens[:-1]
    nombre = " ".join(nombre_tokens).strip(" .:-")
    if len(nombre) < 3:
        return None
    return {
        "nombre": nombre,
        "nota": nota,
        "monto": montos[0][1],
        "comparativo": montos[1][1],
    }


def _linea(meta, estado, nombre, nota, monto, comp) -> dict:
    return {
        "rut": meta.get("rut", ""),
        "razon_social": meta.get("razon_social", ""),
        "periodo": meta.get("periodo", ""),
        "fecha_corte": meta.get("fecha_corte", ""),
        "tipo_eeff": meta.get("tipo_eeff", ""),
        "estado": estado,
        "nombre_cuenta": nombre,
        "cuenta_canonica": "",
        "nota_ref": nota,
        "clase": clase_cuenta(nombre, estado),
        "monto_miles_clp": round(float(monto), 2),
        "monto_m_clp": round(float(monto) / 1000.0, 2),
        "monto_comparativo_miles_clp": None if comp is None else round(float(comp), 2),
        "fuente": "CMF PDF Estados financieros",
    }


def elegir(candidatos: list[tuple[str, list[dict]]], puntaje) -> tuple[str, list[dict]]:
    """El que cierra gana. Si ninguno cierra, el que tiene más líneas. No se mezclan."""
    if not candidatos:
        return "", []
    ordenados = sorted(candidatos, key=lambda item: (puntaje(item[1]), len(item[1])), reverse=True)
    return ordenados[0]

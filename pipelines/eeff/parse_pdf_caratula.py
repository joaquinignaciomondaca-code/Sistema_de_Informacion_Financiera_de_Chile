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


def _es_indice_o_nota(crudo: str, cabeza: str) -> bool:
    # «Notas» a secas es el encabezado de la columna, no una nota.
    if "notas a los estados" in cabeza or re.match(r"nota \d", cabeza):
        return True
    return "...." in crudo[:900]


def clasificar_pagina(texto: str) -> str:
    """El título manda. Si el PDF no lo repite, manda el contenido de la carátula."""
    crudo = texto or ""
    utiles = [linea.strip() for linea in crudo.splitlines() if linea.strip()]
    cabeza = fold("\n".join(utiles[:28]))
    if _es_indice_o_nota(crudo, cabeza):
        return ""
    montos = len(re.findall(r"\d{1,3}(?:\.\d{3})+", crudo))
    if montos < 3:
        return ""
    if "flujo de efectivo" in cabeza or "flujos de efectivo" in cabeza or "cambios en el patrimonio" in cabeza:
        return ""
    if "situacion financiera" in cabeza:
        return "balance"
    if (
        "estado de resultados" in cabeza
        or "estados de resultados" in cabeza
        or "resultados integrales" in cabeza
        or "resultados consolidados por funcion" in cabeza
        or "resultados por funcion" in cabeza
    ) and "otros resultados integrales" not in cabeza[:80]:
        return "resultado"
    if montos < 8:
        return ""
    if "efectivo y equivalentes" in cabeza and "activo" in cabeza:
        return "balance"
    if "pasivos corrientes" in cabeza and "ingresos de actividades" not in cabeza:
        return "balance"
    if "ingresos de actividades ordinarias" in cabeza or "ingreso de actividades ordinarias" in cabeza:
        return "resultado"
    if "ganancia bruta" in cabeza and "costo de ventas" in cabeza:
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


_SECCION = {
    "activos", "pasivos", "patrimonio", "patrimonio neto", "pasivos y patrimonio",
    "activo corriente", "activos corrientes", "activo no corriente", "activos no corrientes",
    "pasivo corriente", "pasivos corrientes", "pasivo no corriente", "pasivos no corrientes",
}
_NOTA_LINEA = re.compile(r"^\(?[1-9]\d?(?:[.\s]?[a-z])?\)?$")
_CORTE_ESTADO = {
    "balance": ("estado de resultados", "estados de resultados", "estado de flujos", "estados de flujos"),
    "resultado": (
        "otro resultado integral",
        "otros resultados integrales",
        "ganancia por accion",
        "estado de cambios",
        "estados de cambios",
        "estado de flujos",
        "estados de flujos",
    ),
}
_ENCABEZADO = {"ganancia", "perdida", "utilidad", "ganancia perdida", "utilidad perdida", "al", "acumulado"}


def _es_ruido(linea: str) -> bool:
    bajo = fold(linea)
    if not bajo or bajo in {"nota", "notas", "m$", "ms", "n", "activ", "numero"}:
        return True
    if any(marca in bajo for marca in ("s.a.", "s.a ", " spa", "limitada", "subsidiaria", "y filiales", "y filial")):
        return True
    if bajo.startswith("estado") or "expresado en" in bajo or "notas adjuntas" in bajo or "miles de pesos" in bajo:
        return True
    if _es_fecha(linea) or re.fullmatch(r"(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s+20\d{2}", bajo):
        return True
    if re.fullmatch(r"0?[1-9]\d?\.\d{2}\.20\d{2}", linea.replace(" ", "")):
        return True
    if re.search(r"\d{1,2}[-/](ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[-/]\d{2,4}", bajo):
        return True
    if bajo in {"n", "no", "nº", "no."}:
        return True
    if linea.isupper() and len(linea) > 4 and not bajo.startswith("total"):
        return True
    return False


def _es_encabezado_columna(linea: str) -> bool:
    limpio = re.sub(r"[^a-z ]", "", fold(linea)).strip()
    return limpio in _ENCABEZADO


def _es_guion(linea: str) -> bool:
    return linea.strip() in {"-", "—", "–"}


def _montos_de_linea(linea: str) -> list[float] | None:
    if _NOTA_LINEA.fullmatch(linea.strip()):
        return None
    partes = linea.split()
    if not partes:
        return None
    montos = []
    for parte in partes:
        limpio = parte.strip().replace("−", "-").replace("–", "-")
        if limpio in {"-", "—"}:
            montos.append(0.0)
            continue
        monto = _monto(limpio)
        if monto is None:
            return None
        montos.append(monto)
    return montos or None


def lineas_apiladas(texto: str, estado: str, meta: dict, orden: str = "corte_primero") -> list[dict]:
    """El PDF de la CMF deja el nombre, la nota y cada monto en su propia línea."""
    filas = []
    vistos = set()
    nombre: list[str] = []
    nota = ""
    montos: list[float] = []
    lado = ""
    cortes = _CORTE_ESTADO.get(estado, ())

    def emitir():
        nonlocal nombre, nota, montos
        titulo = re.sub(r"\s+", " ", " ".join(nombre)).strip(" .:-")
        nota_emit = nota
        monto = montos[0] if montos else None
        comp = montos[1] if len(montos) > 1 else None
        nombre, nota, montos = [], "", []
        if not titulo or monto is None or len(titulo) < 3 or fold(titulo) in _SECCION:
            return
        if "por accion" in fold(titulo) or "numero de acciones" in fold(titulo):
            return
        if orden == "comparativo_primero" and comp is not None:
            monto, comp = comp, monto
        clave = (fold(titulo), monto, comp)
        if clave in vistos:
            return
        vistos.add(clave)
        filas.append(_linea(meta, estado, titulo, nota_emit, monto, comp, lado))

    utiles = [linea for cruda in (texto or "").splitlines() if (linea := _limpiar_celda(cruda)) and not _es_ruido(linea)]
    limpias = []
    for idx, linea in enumerate(utiles):
        if _es_encabezado_columna(linea):
            siguiente = utiles[idx + 1] if idx + 1 < len(utiles) else ""
            if siguiente and _montos_de_linea(siguiente) is None and not _es_guion(siguiente):
                continue
        limpias.append(linea)
    guion = False
    for linea in limpias:
        bajo = fold(linea)
        if any(marca in bajo for marca in cortes) and filas:
            break
        if _es_guion(linea):
            if guion and not montos:
                montos = [0.0, 0.0]
                guion = False
                emitir()
                continue
            if montos:
                montos.append(0.0)
                if len(montos) >= 2:
                    emitir()
                continue
            guion = True
            continue
        if re.fullmatch(r"[1-9]\d?", linea) and not nombre and not montos and not nota:
            continue
        # 2026 y 2025 sueltos son el encabezado de columna, no un saldo.
        if re.fullmatch(r"(19|20)\d{2}", linea) and not nombre and not montos and not nota:
            continue
        if _NOTA_LINEA.fullmatch(linea) and nombre and not nota and not montos:
            guion = False
            nota = re.sub(r"\D", "", linea.split(".")[0])
            continue
        if re.fullmatch(r"[1-9]\d?", linea) and (nota or montos):
            montos.append(float(linea))
            if len(montos) >= 2:
                guion = False
                emitir()
            continue
        encontrados = _montos_de_linea(linea)
        if encontrados is not None:
            if guion and not montos and len(encontrados) >= 2:
                guion = False
                montos = list(encontrados[:2])
                emitir()
                continue
            montos.extend(encontrados)
            if len(montos) >= 2:
                guion = False
                emitir()
            continue
        if guion and len(montos) == 1:
            montos = [0.0] + montos
            guion = False
            emitir()
        elif montos:
            emitir()
        guion = False
        seccion = _lado_seccion(linea)
        if seccion or fold(linea).strip(" .:-") in _SECCION:
            if seccion:
                lado = seccion
            nombre = []
            nota = ""
            continue
        nombre.append(linea)
    if montos:
        emitir()
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


def _lado_seccion(linea: str) -> str:
    """El encabezado «Pasivos corrientes:» fija el lado. No es una cuenta."""
    bajo = fold(linea).strip(" .:-")
    if bajo not in _SECCION:
        return ""
    if "pasivo" in bajo and "patrimonio" in bajo:
        return ""
    if "pasivo" in bajo:
        return "Pasivo"
    if "patrimonio" in bajo:
        return "Patrimonio"
    if "activo" in bajo:
        return "Activo"
    return ""


def _linea(meta, estado, nombre, nota, monto, comp, lado: str = "") -> dict:
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
        "clase": lado if lado and estado != "resultado" and not fold(nombre).startswith("total") else clase_cuenta(nombre, estado),
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

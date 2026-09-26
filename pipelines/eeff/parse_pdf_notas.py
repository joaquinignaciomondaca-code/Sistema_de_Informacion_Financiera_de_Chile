"""Notas del PDF, por nombre. El total entra solo si es la línea de la cara.

No se inventa la diferencia. Si el total no está o no calza, la nota queda
marcada y no se rellena. El número de la nota no es la llave.
"""

from __future__ import annotations

import re

from pipelines.eeff.alias import clasificar_nota, fold
from pipelines.eeff.canon import parse_monto_chileno

# El punto de un miles (3.300) no es el punto de una nota.
_HEAD = re.compile(
    r"^(?:nota\s+)?(?:n[°ºo]\s*)?(\d{1,2})\s*[\.\)\-–—:]+\s+(.{4,160})$",
    re.IGNORECASE,
)
_HEAD_PAREN = re.compile(r"^\((\d{1,2})\)\s+(.{4,160})$")
# "NOTA 5" en una línea y el título en la siguiente no trae guion.
_HEAD_NOTA = re.compile(r"^nota\s+(\d{1,2})\s+(.{4,160})$", re.IGNORECASE)
_MONTO = re.compile(r"\(?-?\d{1,3}(?:\.\d{3})+(?:,\d+)?\)?")
_CONTINUA = re.compile(r"continuaci[oó]n", re.IGNORECASE)

# Líneas de la cara que una nota puede desagregar. El orden importa.
_OBJETIVOS = (
    ("impuestos_diferidos_activo", ("activos por impuestos diferidos",)),
    ("impuestos_diferidos_pasivo", ("pasivos por impuestos diferidos", "pasivo por impuestos diferidos")),
    ("impuestos_corrientes_activo", ("activos por impuestos corrientes", "activos por impuestos")),
    ("impuestos_corrientes_pasivo", ("pasivos por impuestos corrientes",)),
    ("intangibles", ("activos intangibles", "intangibles distintos")),
    ("provisiones_empleados", ("provisiones por beneficios", "provisiones corrientes por beneficios")),
    ("provisiones", ("otras provisiones",)),
    ("efectivo", ("efectivo y equivalente",)),
    ("deudores", ("deudores comerciales", "cuentas comerciales por cobrar")),
    ("pasivos_financieros", ("otros pasivos financieros", "prestamos que devengan interes")),
    ("cuentas_por_pagar", ("cuentas por pagar comerciales", "cuentas comerciales y otras cuentas por pagar")),
    ("relacionadas_por_cobrar", ("cuentas por cobrar a entidades relacionadas", "cuentas por cobrar a empresas relacionadas")),
    ("relacionadas_por_pagar", ("cuentas por pagar a entidades relacionadas", "cuentas por pagar a empresas relacionadas")),
    ("ppe", ("propiedades planta", "propiedad planta", "planta y equipo")),
    ("otros_activos_no_financieros", ("otros activos no financieros",)),
    ("otros_pasivos_no_financieros", ("otros pasivos no financieros",)),
)

_FAMILIA_OBJETIVO = {
    "efectivo": ("efectivo",),
    "deudores": ("deudores",),
    "pasivos_financieros": ("pasivos_financieros",),
    "cuentas_por_pagar": ("cuentas_por_pagar",),
    "relacionadas": ("relacionadas_por_cobrar", "relacionadas_por_pagar"),
    "impuestos": (
        "impuestos_corrientes_activo",
        "impuestos_corrientes_pasivo",
        "impuestos_diferidos_activo",
        "impuestos_diferidos_pasivo",
    ),
    "ppe": ("ppe",),
    "intangibles": ("intangibles",),
    "provisiones": ("provisiones", "provisiones_empleados"),
    "otros_activos": ("otros_activos_no_financieros",),
    "otros_pasivos": ("otros_pasivos_no_financieros",),
}


def cuenta_objetivo(nombre: str) -> str:
    blob = fold(nombre)
    if not blob or blob.startswith("total"):
        return ""
    for canon, frases in _OBJETIVOS:
        if any(frase in blob for frase in frases):
            if canon in {
                "deudores", "pasivos_financieros", "cuentas_por_pagar", "ppe",
                "relacionadas_por_cobrar", "relacionadas_por_pagar",
                "otros_activos_no_financieros", "efectivo",
            } and "no corriente" in blob:
                return f"{canon}_no_corriente"
            return canon
    return ""


def _titulo_limpio(titulo: str) -> str:
    titulo = re.sub(r"\s+", " ", titulo).strip(" .-\t")
    titulo = re.sub(r"\.{2,}.*$", "", titulo).strip(" .")
    titulo = re.sub(r"\s+\d{1,3}$", "", titulo).strip()
    return titulo


def _es_encabezado(line: str) -> tuple[int, str] | None:
    s = re.sub(r"\s+", " ", line.strip())
    if not s or len(s) > 180:
        return None
    if s.lower().startswith("nota a los") or "forman parte" in s.lower():
        return None
    match = _HEAD.match(s) or _HEAD_NOTA.match(s) or _HEAD_PAREN.match(s)
    if not match:
        return None
    titulo = _titulo_limpio(match.group(2))
    if len(titulo) < 4 or sum(ch.isalpha() for ch in titulo) < 4 or titulo[0].isdigit():
        return None
    blob = fold(titulo)
    if blob.startswith("a los estados"):
        return None
    # Una oración de política o una llamada no es el título de la nota.
    if blob.startswith(("con fecha", "al 31", "corresponde", "durante el", "incluye ", "esta partida", "se detalla")):
        return None
    # (2) Corresponde a... termina en punto: es nota al pie, no el título de la nota 2.
    if match.re is _HEAD_PAREN and (titulo.endswith(".") or len(titulo.split()) > 12):
        return None
    return int(match.group(1)), titulo


def _unir_titulos(texto: str) -> str:
    """`6)` en una línea y el título en la siguiente es un encabezado."""
    lineas = texto.splitlines()
    salida = []
    i = 0
    # Un "3" suelto es un miles o un año, no una nota. Hace falta el marcador.
    solo = re.compile(
        r"^(?:nota\s+\d{1,2}|n[°ºo]\s*\d{1,2}|\(\d{1,2}\)|\d{1,2}\))$",
        re.IGNORECASE,
    )
    while i < len(lineas):
        actual = lineas[i].strip()
        if solo.fullmatch(actual) and i + 1 < len(lineas):
            siguiente = lineas[i + 1].strip()
            if sum(ch.isalpha() for ch in siguiente) >= 4 and not _es_encabezado(siguiente):
                salida.append(f"{actual} {siguiente}")
                i += 2
                continue
        salida.append(lineas[i])
        i += 1
    return "\n".join(salida)


def indice_notas(paginas: list[str]) -> list[dict]:
    """Un título por número. El índice, si existe, gana al encabezado del cuerpo."""
    por_numero: dict[int, dict] = {}
    for n_pag, texto in enumerate(paginas):
        texto = _unir_titulos(texto)
        vistos = []
        for line in texto.splitlines():
            enc = _es_encabezado(line)
            if enc:
                vistos.append(enc)
        es_indice = len(vistos) >= 4
        for numero, titulo in vistos:
            if _CONTINUA.search(titulo):
                continue
            actual = por_numero.get(numero)
            fila = {
                "numero": numero,
                "titulo": titulo,
                "pagina": n_pag + 1,
                "en_indice": es_indice,
                "familia": _familia(titulo),
            }
            if actual is None or (es_indice and not actual["en_indice"]):
                por_numero[numero] = fila
    return [por_numero[n] for n in sorted(por_numero)]


def _familia(titulo: str) -> str:
    clas = clasificar_nota(titulo)
    return clas["tabla"] or clas["familia"]


def secciones(paginas: list[str]) -> list[dict]:
    marcas = []
    for n_pag, texto in enumerate(paginas):
        texto = _unir_titulos(texto)
        encabezados = []
        for i, line in enumerate(texto.splitlines()):
            enc = _es_encabezado(line)
            if enc:
                encabezados.append((i, enc[0], enc[1]))
        # El índice trae muchas notas en una página. Una nota con tres llamadas no.
        if len(encabezados) >= 8:
            continue
        for pos, numero, titulo in encabezados:
            if _CONTINUA.search(titulo):
                continue
            marcas.append((n_pag, pos, numero, titulo, texto))
    salida = []
    for i, (n_pag, pos, numero, titulo, texto) in enumerate(marcas):
        if i + 1 < len(marcas):
            fin_pag, fin_pos, _, _, fin_texto = marcas[i + 1]
        else:
            fin_pag, fin_pos, fin_texto = len(paginas), 0, ""
        trozos = [texto.splitlines()[pos:]]
        for siguiente in range(n_pag + 1, fin_pag):
            trozos.append(paginas[siguiente].splitlines())
        # La tabla puede quedar arriba del próximo título, en esa misma página.
        # No se corta lo que ya estaba en la página de esta nota.
        if fin_pag > n_pag and fin_texto and fin_pos:
            trozos.append(fin_texto.splitlines()[:fin_pos])
        salida.append({
            "numero": numero,
            "titulo": titulo,
            "pagina": n_pag + 1,
            "familia": _familia(titulo),
            "texto": "\n".join("\n".join(t) for t in trozos),
            # La página del próximo título entra: en dos columnas la tabla de esta
            # nota queda ahí. El texto de esa nota no se mezcla.
            "paginas": list(range(n_pag, min(fin_pag, len(paginas) - 1) + 1)),
        })
    return salida


def _montos(line: str) -> list[float]:
    line = line.replace("−", "-").replace("–", "-")
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+\)", ")", line)
    # El guion suelto es cero y va en su columna. (39.562) es negativo.
    # 31.03.2026 no es un miles: el monto no puede partir ni seguir en un dígito.
    # 77.124.030-5 es un RUT, no un monto.
    patron = re.compile(
        r"(?<![\d.])\(?-?\d{1,3}(?:\.\d{3})+(?:,\d+)?\)?(?![\d.])|(?<![\w\d])-(?![\w\d])"
    )
    valores = []
    for match in patron.finditer(line):
        token = match.group()
        resto = line[match.end():]
        if re.match(r"-[0-9kK]", resto):
            continue
        valor = parse_monto_chileno(token)
        if valor is not None:
            valores.append(valor)
    # «Chile 104» es un miles. 2026 y 77.124.030-5 no: el número chico va solo al final.
    if not valores and sum(ch.isalpha() for ch in line) >= 3:
        cola = re.search(r"(?<![\d./-])(\d{1,3})\s*$", line)
        blob = fold(line)
        if cola and not blob.startswith(("nota ", "notas ", "pagina ", "indice ")):
            valores.append(float(cola.group(1)))
    return valores


def _concepto(line: str) -> str:
    sin = _MONTO.sub(" ", line.replace("−", "-").replace("–", "-"))
    sin = re.sub(r"(?<![\w\d])-(?![\w\d])", " ", sin)
    return re.sub(r"\s+", " ", sin).strip(" .:-")


def _es_total(concepto: str) -> bool:
    blob = fold(concepto)
    return blob.startswith("total") or blob.startswith("subtotal")


def _es_cierre(concepto: str) -> bool:
    """El neto o el saldo final cierran la composición aunque no digan «total»."""
    blob = fold(concepto)
    if _es_total(concepto):
        return True
    if blob.endswith((" neto", "(neto)", " netos")):
        return True
    return blob == "saldo final" or blob.startswith("saldo final")


def _partes_utiles(filas: list[tuple], col: int) -> list[tuple]:
    partes = []
    for concepto, montos in filas:
        if _es_total(concepto) or not _concepto_util(concepto):
            continue
        if col >= len(montos) or montos[col] is None:
            continue
        comp = montos[col + 1] if col + 1 < len(montos) else None
        partes.append((concepto, montos[col], comp))
    return partes


def _suma(partes: list[tuple], objetivo: float) -> bool:
    return len(partes) >= 1 and abs(sum(monto for _, monto, _ in partes) - objetivo) <= 1


def _es_desglose(partes: list[tuple], objetivo: float) -> bool:
    """Dos partidas con monto, o una sola clase que es toda la línea. No un cero más la copia."""
    if not _suma(partes, objetivo):
        return False
    con_monto = [parte for parte in partes if abs(parte[1]) > 1]
    if len(con_monto) >= 2:
        return True
    return len(partes) == 1 and abs(partes[0][1] - objetivo) <= 1


def _sufijo(filas: list[tuple], col: int, objetivo: float) -> list[tuple] | None:
    """Las partidas pegadas al total, no toda la nota anterior."""
    utiles = _partes_utiles(filas, col)
    for inicio in range(len(utiles)):
        trozo = utiles[inicio:]
        if len(trozo) >= 2 and _es_desglose(trozo, objetivo):
            return trozo
    return None


def _rollup(filas: list[tuple], corte: int, col: int, objetivo: float) -> list[tuple] | None:
    """El subtotal reemplaza a sus hijas. El detalle suelto entre subtotales se suma."""
    j = corte - 1
    acc = 0.0
    partes = []
    while j >= 0 and len(partes) <= 16:
        concepto, montos = filas[j]
        if col >= len(montos) or montos[col] is None or not _concepto_util(concepto):
            j -= 1
            continue
        valor = montos[col]
        comp = montos[col + 1] if col + 1 < len(montos) else None
        acc += valor
        partes.append((concepto, valor, comp))
        j -= 1
        if _es_total(concepto):
            while j >= 0 and not _es_total(filas[j][0]):
                j -= 1
        if _es_desglose(partes, objetivo):
            return list(reversed(partes))
    return None


def _prefijo(filas: list[tuple], col: int, objetivo: float) -> list[tuple] | None:
    """El total impreso arriba y las clases debajo, hasta que suman."""
    acc = 0.0
    partes = []
    for concepto, montos in filas:
        if _es_total(concepto):
            break
        if col >= len(montos) or montos[col] is None or not _concepto_util(concepto):
            continue
        comp = montos[col + 1] if col + 1 < len(montos) else None
        acc += montos[col]
        partes.append((concepto, montos[col], comp))
        if len(partes) >= 2 and abs(acc - objetivo) <= 1:
            return partes
        if len(partes) > 12:
            break
    return None


def _monto_menor(line: str) -> float | None:
    """350 y (350) no traen punto de miles. Un 40 de número de página no entra aquí."""
    s = line.strip().replace("(", "-").replace(")", "")
    if re.fullmatch(r"-?\d{1,3}", s):
        return float(s)
    return None


def _es_linea_monto(line: str, siguiente: str = "", juntando: bool = False) -> bool:
    if sum(ch.isalpha() for ch in line) > 1 or len(line) > 80:
        return False
    if _montos(line):
        return True
    if _monto_menor(line) is None:
        return False
    if juntando:
        return True
    sig = siguiente.strip()
    if _monto_menor(sig) is not None or bool(_montos(sig)) or sig in {"-", "–", "—"}:
        return True
    # El último saldo chico queda justo antes del total, no antes de otro monto.
    return fold(sig).startswith(("total", "subtotal"))


def _concepto_util(concepto: str) -> bool:
    """Una partida, no un párrafo ni el encabezado de la tabla."""
    if not concepto or sum(ch.isalpha() for ch in concepto) < 3:
        return False
    if _es_total(concepto):
        return True
    if len(concepto) > 90:
        return False
    blob = fold(concepto)
    if len(blob.split()) > 10:
        return False
    if "$" in concepto or blob in {"concepto", "sociedad", "m", "ms", "nota", "al efectivo"}:
        return False
    return not any(
        frase in blob
        for frase in (
            "se detalla", "a continuacion", "estados financieros", "notas a los",
            "comparacion con", "igual periodo", "se explica", "alcanzo a",
        )
    )


def _es_moneda(line: str) -> bool:
    return fold(line) in {
        "pesos", "peso", "dolares", "dolar", "usd", "clp", "uf", "euro", "euros",
        "guarani", "nuevo sol", "soles", "pesos colombianos", "pesos mexicanos",
    }


def _es_ruido_etiqueta(line: str) -> bool:
    """Moneda, signo peso o sociedad entre el concepto y sus montos. No es una partida."""
    if _montos(line):
        return False
    if line.strip() in {"$", "US$", "USD", "UF"}:
        return True
    blob = fold(line)
    if not blob or _es_moneda(line) or blob in {"m", "ms", "sociedad", "concepto"}:
        return True
    return blob.endswith((" s a", " s a s", " ltda", " corp", " spa", " s a c v"))


def _filas_texto(texto: str) -> list[tuple[str, list[float]]]:
    """Acepta la fila en una línea, o el concepto y debajo la sociedad, la moneda y los montos."""
    lineas = [raw.strip() for raw in texto.splitlines() if raw.strip()]
    filas = []
    i = 0
    while i < len(lineas):
        line = lineas[i]
        if _es_encabezado(line) or line.endswith(":") or fold(line) in {
            "tipo de activo", "concepto", "conceptos", "detalle",
        }:
            i += 1
            continue
        montos = _montos(line)
        concepto = _concepto(line)
        letras = sum(ch.isalpha() for ch in concepto)
        if letras >= 3 and not montos and len(line) <= 80 and not _es_ruido_etiqueta(line):
            j = i + 1
            while j < len(lineas) and j <= i + 4 and _es_ruido_etiqueta(lineas[j]):
                # La sociedad identifica la partida. El signo, M$ y la moneda no.
                blob = fold(lineas[j])
                if blob and not _es_moneda(lineas[j]) and blob not in {"m", "ms", "sociedad", "concepto", "uf"}:
                    concepto = f"{concepto} — {lineas[j]}"
                j += 1
            if (
                j < len(lineas)
                and not _montos(lineas[j])
                and _monto_menor(lineas[j]) is None
                and not _es_encabezado(lineas[j])
                and len(lineas[j]) <= 40
                and j + 1 < len(lineas)
                and _es_linea_monto(lineas[j + 1])
            ):
                concepto = f"{concepto} {lineas[j]}"
                j += 1
            juntados = []
            k = j
            while k < len(lineas) and len(juntados) < 8 and _es_linea_monto(
                lineas[k], lineas[k + 1] if k + 1 < len(lineas) else "", bool(juntados)
            ):
                juntados.extend(_montos(lineas[k]) or [(_monto_menor(lineas[k]) or 0)])
                k += 1
            if juntados and _concepto_util(concepto.split(" — ")[0]):
                filas.append((concepto, juntados))
                i = k
                continue
        if montos and letras >= 3 and _concepto_util(concepto):
            filas.append((concepto, montos))
        i += 1
    return filas


def _armar(partes: list[tuple], valor: float, comparativo, col: int) -> dict:
    rows = [
        {
            "concepto": concepto,
            "monto_miles": monto,
            "monto_comparativo_miles": comp,
            "es_total": 0,
        }
        for concepto, monto, comp in partes
    ]
    rows.append({
        "concepto": "Totales",
        "monto_miles": valor,
        "monto_comparativo_miles": comparativo,
        "es_total": 1,
    })
    return {"filas": rows, "total": valor, "columna": col}


def _reconstruir(filas: list[tuple], objetivo: float) -> dict | None:
    """Partidas que suman la cara, o los subtotales si el puente bruto/neto no suma."""
    if objetivo is None:
        return None
    candidatos = []
    for i, (concepto, montos) in enumerate(filas):
        if not _es_total(concepto):
            continue
        for col, valor in enumerate(montos):
            if valor is None or abs(valor - objetivo) > 1:
                continue
            prev = 0
            for k in range(i - 1, -1, -1):
                if _es_total(filas[k][0]):
                    prev = k + 1
                    break
            detalles = []
            for concepto_p, montos_p in filas[prev:i]:
                if _es_total(concepto_p) or not _concepto_util(concepto_p):
                    continue
                if col >= len(montos_p) or montos_p[col] is None:
                    continue
                comp = montos_p[col + 1] if col + 1 < len(montos_p) else None
                detalles.append((concepto_p, montos_p[col], comp))
            comparativo = montos[col + 1] if col + 1 < len(montos) else None
            hojas = []
            for concepto_p, montos_p in filas[:i]:
                if _es_total(concepto_p) or not _concepto_util(concepto_p):
                    continue
                if col >= len(montos_p) or montos_p[col] is None:
                    continue
                comp = montos_p[col + 1] if col + 1 < len(montos_p) else None
                hojas.append((concepto_p, montos_p[col], comp))
            if len(hojas) >= 1 and abs(sum(m for _, m, _ in hojas) - objetivo) <= 1:
                candidatos.append((i, len(hojas), hojas, valor, comparativo, col))
                continue
            if len(detalles) >= 1 and abs(sum(m for _, m, _ in detalles) - objetivo) <= 1:
                candidatos.append((i, len(detalles), detalles, valor, comparativo, col))
                continue
            acc = 0.0
            subs = []
            calzo = False
            for concepto_p, montos_p in reversed(filas[:i]):
                if not _es_total(concepto_p) or col >= len(montos_p) or montos_p[col] is None:
                    continue
                acc += montos_p[col]
                comp = montos_p[col + 1] if col + 1 < len(montos_p) else None
                subs.append((concepto_p, montos_p[col], comp))
                if abs(acc - objetivo) <= 1 and len(subs) >= 2:
                    candidatos.append((i, len(subs), list(reversed(subs)), valor, comparativo, col))
                    calzo = True
                    break
                if objetivo > 0 and acc > objetivo + 1:
                    break
            if calzo:
                continue
            sufijo = _sufijo(filas[prev:i], col, objetivo)
            if sufijo:
                candidatos.append((i, len(sufijo), sufijo, valor, comparativo, col))
                continue
            rollo = _rollup(filas, i, col, objetivo)
            if rollo:
                candidatos.append((i, len(rollo), rollo, valor, comparativo, col))
                continue
            if i == 0 or not any(not _es_total(fila[0]) for fila in filas[:i]):
                adelante = _prefijo(filas[i + 1:], col, objetivo)
                if adelante:
                    candidatos.append((i, len(adelante), adelante, valor, comparativo, col))
    for i, (concepto, montos) in enumerate(filas):
        if _es_total(concepto) or not _es_cierre(concepto):
            continue
        for col, valor in enumerate(montos):
            if valor is None or abs(valor - objetivo) > 1:
                continue
            prev = 0
            for k in range(i - 1, -1, -1):
                if _es_total(filas[k][0]) or _es_cierre(filas[k][0]):
                    prev = k + 1
                    break
            sufijo = _sufijo(filas[prev:i], col, objetivo)
            if not sufijo:
                continue
            comparativo = montos[col + 1] if col + 1 < len(montos) else None
            candidatos.append((i, len(sufijo), sufijo, valor, comparativo, col))
    # «Activo por impuestos corrientes» cierra la composición aunque no diga total.
    for i, (concepto, montos) in enumerate(filas):
        if _es_total(concepto) or _es_cierre(concepto):
            continue
        for col, valor in enumerate(montos):
            if valor is None or abs(valor - objetivo) > 1:
                continue
            prev = 0
            for k in range(i - 1, -1, -1):
                if _es_total(filas[k][0]) or _es_cierre(filas[k][0]):
                    prev = k + 1
                    break
            sufijo = _sufijo(filas[prev:i], col, objetivo)
            if not sufijo:
                continue
            con_monto = [parte for parte in sufijo if abs(parte[1]) > 1]
            if len(con_monto) < 2:
                continue
            comparativo = montos[col + 1] if col + 1 < len(montos) else None
            candidatos.append((i, len(sufijo), sufijo, valor, comparativo, col))
    if not candidatos:
        # 968.758 + 152.895 = 1.121.653 en la misma fila: las clases son columnas.
        for i, (concepto, montos) in enumerate(filas):
            for col, valor in enumerate(montos):
                if valor is None or abs(valor - objetivo) > 1:
                    continue
                otros = [
                    (k, monto)
                    for k, monto in enumerate(montos)
                    if k != col and monto is not None and abs(monto) > 1
                ]
                if len(otros) < 2 or abs(sum(monto for _, monto in otros) - objetivo) > 1:
                    continue
                partes = [(f"{concepto} — columna {k + 1}", monto, None) for k, monto in otros]
                comparativo = montos[col + 1] if col + 1 < len(montos) else None
                return _armar(partes, valor, comparativo, col)
        return None
    _i, _n, partes, valor, comparativo, col = min(candidatos, key=lambda item: (item[0], -item[1]))
    return _armar(partes, valor, comparativo, col)


def composicion_que_calza(texto: str, objetivo: float) -> dict | None:
    """La composición cuya fila total es el objetivo y cuyas partes suman eso."""
    return _reconstruir(_filas_texto(texto), objetivo)


def _fila_tabla(row: list) -> tuple[str, list] | None:
    celdas = ["" if c is None else str(c).replace("\n", " ").strip() for c in row]
    if not any(celdas):
        return None
    idx = next((i for i, celda in enumerate(celdas) if sum(ch.isalpha() for ch in celda) >= 3), None)
    if idx is None:
        return None
    montos = [parse_monto_chileno(celda) if celda else None for celda in celdas[idx + 1:]]
    if not any(valor is not None for valor in montos):
        return None
    return celdas[idx], montos


def composicion_en_tablas(tablas: list[list[list]], objetivo: float) -> dict | None:
    if objetivo is None:
        return None
    mejor = None
    for tabla in tablas:
        filas = []
        for row in tabla or []:
            fila = _fila_tabla(row)
            if fila and _concepto_util(fila[0]):
                filas.append(fila)
        tomado = _reconstruir(filas, objetivo)
        if tomado and (mejor is None or len(tomado["filas"]) > len(mejor["filas"])):
            mejor = tomado
    return mejor


def _lado(titulo: str) -> str:
    blob = fold(titulo)
    if "no corriente" in blob:
        return "no_corriente"
    if "corriente" in blob:
        return "corriente"
    return ""


def _sirve(titulo: str, cuenta: str) -> bool:
    lado = _lado(titulo)
    es_no = cuenta.endswith("_no_corriente")
    if lado == "no_corriente":
        return es_no
    if lado == "corriente":
        return not es_no
    return True


def _cuenta_de_linea(row: dict) -> str:
    """Una línea impresa, no la suma de corriente y no corriente."""
    cuenta = cuenta_objetivo(row.get("nombre_cuenta") or "")
    if not cuenta:
        return ""
    clase = fold(row.get("clase") or "")
    if not cuenta.endswith("_no_corriente") and "no corriente" in clase:
        return f"{cuenta}_no_corriente"
    return cuenta


def objetivos_cara(balance: list[dict]) -> list[dict]:
    salida = []
    for row in balance:
        cuenta = _cuenta_de_linea(row)
        monto = row.get("monto_miles_clp")
        if not cuenta or monto is None or abs(float(monto)) < 1:
            continue
        nombre = row.get("nombre_cuenta") or ""
        nota_ref = str(row.get("nota_ref") or "")
        if not nota_ref:
            pegada = re.search(r"(?:^|\s)(\d{1,2})(?:\.\d{1,2}|\s*\([a-z]\))?\s*$", nombre, re.I)
            if pegada:
                nota_ref = pegada.group(1)
        salida.append({
            "cuenta": cuenta,
            "monto_miles": float(monto),
            "nota_ref": nota_ref,
            "nombre": nombre,
        })
    return salida


def _candidatas(secs: list[dict], objetivo: dict) -> list[dict]:
    """Primero la nota que cita la cara, en este PDF. Después la familia, sin mezclar lados."""
    cuenta = objetivo["cuenta"]
    base = cuenta.replace("_no_corriente", "")
    familia = [
        sec for sec in secs
        if cuenta in _FAMILIA_OBJETIVO.get(sec["familia"], ())
        or base in _FAMILIA_OBJETIVO.get(sec["familia"], ())
    ]
    preferidas = [sec for sec in familia if _sirve(sec["titulo"], cuenta)]
    otras = [sec for sec in familia if sec not in preferidas]
    por_numero = []
    ref = re.match(r"(\d{1,2})", str(objetivo.get("nota_ref") or ""))
    if ref:
        nref = int(ref.group(1))
        por_numero = [sec for sec in secs if sec["numero"] == nref]
    orden = []
    vistos = set()
    for sec in por_numero + preferidas + otras:
        clave = (sec["numero"], sec["pagina"], sec["titulo"])
        if clave in vistos:
            continue
        vistos.add(clave)
        orden.append(sec)
    return orden


def extraer_notas(
    paginas: list[str],
    tablas_por_pagina: list[list] | None,
    balance: list[dict],
    meta: dict | None = None,
) -> dict:
    """Índice completo y solo las composiciones que calzan con su línea."""
    meta = meta or {}
    indice = indice_notas(paginas)
    secs = secciones(paginas)
    tablas_por_pagina = tablas_por_pagina or []
    objetivos = objetivos_cara(balance)
    tablas: dict[str, list[dict]] = {}
    cuadre = []
    for objetivo in objetivos:
        cuenta = objetivo["cuenta"]
        # El número vale dentro de este PDF. No se usa para cruzar periodos.
        candidatas = _candidatas(secs, objetivo)
        mejor = None
        for sec in candidatas:
            tomado = composicion_que_calza(sec["texto"], objetivo["monto_miles"])
            if tomado is None:
                tablas_sec = []
                for n_pag in sec["paginas"]:
                    if n_pag < len(tablas_por_pagina):
                        tablas_sec.extend(tablas_por_pagina[n_pag] or [])
                tomado = composicion_en_tablas(tablas_sec, objetivo["monto_miles"])
            if tomado is None:
                continue
            tomado["numero_nota"] = sec["numero"]
            tomado["titulo_nota"] = sec["titulo"]
            if mejor is None or (
                sec["numero"] == mejor["numero_nota"] and len(tomado["filas"]) > len(mejor["filas"])
            ):
                mejor = tomado
            # La nota que cita esta línea ya sumó. No se cambia por otra más larga.
            citado = re.match(r"(\d{1,2})", str(objetivo.get("nota_ref") or ""))
            if citado and sec["numero"] == int(citado.group(1)):
                break
        if mejor is None:
            cuadre.append({
                "cuenta": cuenta,
                "nombre_cara": objetivo["nombre"],
                "nota_ref": objetivo["nota_ref"],
                "cara_miles": objetivo["monto_miles"],
                "nota_miles": None,
                "estado": "NO_LEIDA",
                "diff_miles": None,
            })
            continue
        for fila in mejor["filas"]:
            fila.update({
                "rut": meta.get("rut", ""),
                "periodo": meta.get("periodo", ""),
                "tipo_eeff": meta.get("tipo_eeff", ""),
                "cuenta": cuenta,
                "numero_nota": mejor["numero_nota"],
                "titulo_nota": mejor["titulo_nota"],
                "cara_miles": objetivo["monto_miles"],
            })
        tablas.setdefault(cuenta, []).extend(mejor["filas"])
        cuadre.append({
            "cuenta": cuenta,
            "nombre_cara": objetivo["nombre"],
            "nota_ref": objetivo["nota_ref"],
            "numero_nota": mejor["numero_nota"],
            "titulo_nota": mejor["titulo_nota"],
            "cara_miles": objetivo["monto_miles"],
            "nota_miles": mejor["total"],
            "estado": "OK",
            "diff_miles": round(mejor["total"] - objetivo["monto_miles"], 2),
        })
    return {"indice": indice, "tablas": tablas, "cuadre": cuadre}

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
    if blob.startswith(("con fecha", "al 31", "corresponden", "durante el", "incluye ", "esta partida")):
        return None
    if match.re is _HEAD_PAREN and len(titulo.split()) > 12:
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
        fin_pag = marcas[i + 1][0] if i + 1 < len(marcas) else len(paginas)
        trozos = [texto.splitlines()[pos:]]
        for siguiente in range(n_pag + 1, fin_pag):
            trozos.append(paginas[siguiente].splitlines())
        salida.append({
            "numero": numero,
            "titulo": titulo,
            "pagina": n_pag + 1,
            "familia": _familia(titulo),
            "texto": "\n".join("\n".join(t) for t in trozos),
            "paginas": list(range(n_pag, fin_pag)),
        })
    return salida


def _montos(line: str) -> list[float]:
    line = line.replace("−", "-").replace("–", "-")
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+\)", ")", line)
    # El guion suelto es cero y va en su columna. (39.562) es negativo.
    # 31.03.2026 no es un miles: el monto no puede partir ni seguir en un dígito.
    patron = re.compile(
        r"(?<![\d.])\(?-?\d{1,3}(?:\.\d{3})+(?:,\d+)?\)?(?![\d.])|(?<![\w\d])-(?![\w\d])"
    )
    valores = []
    for token in patron.findall(line):
        valor = parse_monto_chileno(token)
        if valor is not None:
            valores.append(valor)
    return valores


def _concepto(line: str) -> str:
    sin = _MONTO.sub(" ", line.replace("−", "-").replace("–", "-"))
    sin = re.sub(r"(?<![\w\d])-(?![\w\d])", " ", sin)
    return re.sub(r"\s+", " ", sin).strip(" .:-")


def _es_total(concepto: str) -> bool:
    blob = fold(concepto)
    return blob.startswith("total") or blob.startswith("subtotal")


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
    return _monto_menor(sig) is not None or bool(_montos(sig)) or sig in {"-", "–", "—"}


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
    if blob in {"concepto", "sociedad", "m", "ms", "nota", "al efectivo"}:
        return False
    return not any(
        frase in blob
        for frase in ("se detalla", "a continuacion", "estados financieros", "notas a los")
    )


def _es_moneda(line: str) -> bool:
    return fold(line) in {
        "pesos", "peso", "dolares", "dolar", "usd", "clp", "uf", "euro", "euros",
        "guarani", "nuevo sol", "soles", "pesos colombianos", "pesos mexicanos",
    }


def _es_ruido_etiqueta(line: str) -> bool:
    """Moneda o sociedad entre el concepto y sus montos. No es una partida."""
    if _montos(line):
        return False
    blob = fold(line)
    if _es_moneda(line) or blob in {"m", "ms", "sociedad", "concepto"}:
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
                # La sociedad identifica la partida. M$, Sociedad y la moneda no.
                if not _es_moneda(lineas[j]) and fold(lineas[j]) not in {"m", "ms", "sociedad", "concepto"}:
                    concepto = f"{concepto} — {lineas[j]}"
                j += 1
            if (
                j < len(lineas)
                and not _montos(lineas[j])
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
            for concepto_p, montos_p in reversed(filas[:i]):
                if not _es_total(concepto_p) or col >= len(montos_p) or montos_p[col] is None:
                    continue
                acc += montos_p[col]
                comp = montos_p[col + 1] if col + 1 < len(montos_p) else None
                subs.append((concepto_p, montos_p[col], comp))
                if abs(acc - objetivo) <= 1 and len(subs) >= 2:
                    candidatos.append((i, len(subs), list(reversed(subs)), valor, comparativo, col))
                    break
                if objetivo > 0 and acc > objetivo + 1:
                    break
    if not candidatos:
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


def objetivos_cara(balance: list[dict]) -> list[dict]:
    grupos: dict[str, dict] = {}
    for row in balance:
        cuenta = cuenta_objetivo(row.get("nombre_cuenta") or "")
        monto = row.get("monto_miles_clp")
        if not cuenta or monto is None or abs(float(monto)) < 1:
            continue
        slot = grupos.setdefault(cuenta, {
            "cuenta": cuenta,
            "monto_miles": 0.0,
            "nota_ref": str(row.get("nota_ref") or ""),
            "nombre": row.get("nombre_cuenta") or "",
        })
        slot["monto_miles"] += float(monto)
        if row.get("nota_ref"):
            slot["nota_ref"] = str(row.get("nota_ref"))
            slot["nombre"] = row.get("nombre_cuenta") or slot["nombre"]
    return list(grupos.values())


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
        base = cuenta.replace("_no_corriente", "")
        candidatas = [
            sec for sec in secs
            if cuenta in _FAMILIA_OBJETIVO.get(sec["familia"], ())
            or base in _FAMILIA_OBJETIVO.get(sec["familia"], ())
        ]
        candidatas = [sec for sec in candidatas if _sirve(sec["titulo"], cuenta)] or candidatas
        if not candidatas:
            # Dentro de este PDF el número de la cara sí apunta a su nota.
            # No se usa ese número para cruzar periodos.
            ref = re.match(r"(\d{1,2})", str(objetivo.get("nota_ref") or ""))
            if ref:
                nref = int(ref.group(1))
                candidatas = [
                    sec for sec in secs
                    if sec["numero"] == nref and sec["familia"] in {"otra", ""}
                    and _sirve(sec["titulo"], cuenta)
                ]
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
            if mejor is None or len(tomado["filas"]) > len(mejor["filas"]):
                mejor = tomado
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

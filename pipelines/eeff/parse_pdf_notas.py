"""Notas del PDF, por nombre. El total entra solo si es la línea de la cara.

No se inventa la diferencia. Si el total no está o no calza, la nota queda
marcada y no se rellena. El número de la nota no es la llave.
"""

from __future__ import annotations

import re

from pipelines.eeff.alias import clasificar_nota, fold
from pipelines.eeff.canon import parse_monto_chileno

_HEAD = re.compile(
    r"^(?:nota\s+)?(?:n[°ºo]\s*)?(\d{1,2})\s*[\.\)\-–—:]+\s*(.{4,160})$",
    re.IGNORECASE,
)
_HEAD_PAREN = re.compile(r"^\((\d{1,2})\)\s+(.{4,160})$")
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
    match = _HEAD.match(s) or _HEAD_PAREN.match(s)
    if not match:
        return None
    titulo = _titulo_limpio(match.group(2))
    if len(titulo) < 4 or sum(ch.isalpha() for ch in titulo) < 4:
        return None
    if fold(titulo).startswith("a los estados"):
        return None
    return int(match.group(1)), titulo


def _unir_titulos(texto: str) -> str:
    """`6)` en una línea y el título en la siguiente es un encabezado."""
    lineas = texto.splitlines()
    salida = []
    i = 0
    solo = re.compile(r"^(?:nota\s+)?(?:n[°ºo]\s*)?\(?\d{1,2}\)?$", re.IGNORECASE)
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
        if len(encabezados) >= 4:
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
    # El guion suelto es cero y va en su columna. (39.562) es negativo.
    patron = re.compile(r"\(?-?\d{1,3}(?:\.\d{3})+(?:,\d+)?\)?|(?<![\w\d])-(?![\w\d])")
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


def _es_linea_monto(line: str) -> bool:
    if len(line) > 24 or sum(ch.isalpha() for ch in line) > 1:
        return False
    return bool(_montos(line))


def _filas_texto(texto: str) -> list[tuple[str, list[float]]]:
    """Acepta la fila en una línea o el concepto y, debajo, sus montos."""
    lineas = [raw.strip() for raw in texto.splitlines() if raw.strip()]
    filas = []
    i = 0
    while i < len(lineas):
        line = lineas[i]
        if _es_encabezado(line):
            i += 1
            continue
        montos = _montos(line)
        concepto = _concepto(line)
        letras = sum(ch.isalpha() for ch in concepto)
        if letras >= 3 and not montos and len(line) <= 80:
            juntados = []
            j = i + 1
            while j < len(lineas) and len(juntados) < 4 and _es_linea_monto(lineas[j]):
                juntados.extend(_montos(lineas[j]))
                j += 1
            if juntados:
                filas.append((concepto, juntados))
                i = j
                continue
        if montos and letras >= 3 and fold(concepto) not in {"m", "ms", "nota"}:
            filas.append((concepto, montos))
        i += 1
    return filas


def composicion_que_calza(texto: str, objetivo: float) -> dict | None:
    """La composición cuya fila total es el objetivo y cuyas partes suman eso."""
    if objetivo is None:
        return None
    filas = _filas_texto(texto)
    candidatos = []
    for i, (concepto, montos) in enumerate(filas):
        if not _es_total(concepto):
            continue
        for col, valor in enumerate(montos):
            if abs(valor - objetivo) > 1:
                continue
            partes = []
            for concepto_p, montos_p in reversed(filas[max(0, i - 30):i]):
                if _es_total(concepto_p):
                    break
                if col >= len(montos_p):
                    break
                comp = montos_p[col + 1] if col + 1 < len(montos_p) else None
                partes.append((concepto_p, montos_p[col], comp))
            partes.reverse()
            if not partes:
                continue
            suma = sum(monto for _, monto, _ in partes)
            if abs(suma - objetivo) > 1:
                continue
            candidatos.append((i, col, partes, valor, montos[col + 1] if col + 1 < len(montos) else None))
    if not candidatos:
        return None
    i, col, partes, valor, comparativo = min(candidatos, key=lambda item: (item[0], -len(item[2])))
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


def composicion_en_tablas(tablas: list[list[list]], objetivo: float) -> dict | None:
    if objetivo is None:
        return None
    candidatos = []
    for tabla in tablas:
        filas = []
        for row in tabla or []:
            celdas = ["" if c is None else str(c).replace("\n", " ").strip() for c in row]
            if not any(celdas):
                continue
            montos = []
            for celda in celdas[1:]:
                valor = parse_monto_chileno(celda)
                montos.append(valor)
            concepto = celdas[0]
            if sum(ch.isalpha() for ch in concepto) < 3:
                continue
            if not any(v is not None for v in montos):
                continue
            filas.append((concepto, montos))
        for i, (concepto, montos) in enumerate(filas):
            if not _es_total(concepto):
                continue
            for col, valor in enumerate(montos):
                if valor is None or abs(valor - objetivo) > 1:
                    continue
                partes = []
                for concepto_p, montos_p in reversed(filas[:i]):
                    if _es_total(concepto_p):
                        break
                    if col >= len(montos_p) or montos_p[col] is None:
                        break
                    comp = montos_p[col + 1] if col + 1 < len(montos_p) else None
                    partes.append((concepto_p, montos_p[col], comp))
                partes.reverse()
                if not partes or abs(sum(m for _, m, _ in partes) - objetivo) > 1:
                    continue
                candidatos.append((len(partes), partes, valor, montos[col + 1] if col + 1 < len(montos) else None))
    if not candidatos:
        return None
    _, partes, valor, comparativo = max(candidatos, key=lambda item: item[0])
    rows = [
        {"concepto": c, "monto_miles": m, "monto_comparativo_miles": comp, "es_total": 0}
        for c, m, comp in partes
    ]
    rows.append({
        "concepto": "Totales",
        "monto_miles": valor,
        "monto_comparativo_miles": comparativo,
        "es_total": 1,
    })
    return {"filas": rows, "total": valor}


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

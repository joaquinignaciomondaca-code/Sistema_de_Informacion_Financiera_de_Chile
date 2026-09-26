"""Diccionario de alias de los EEFF de factoring y leasing.

La llave es el nombre económico, no el número de nota. El mismo préstamo
es la nota 13 en 2013 («Préstamos que devengan intereses») y otra nota 13
en 2026 («Otros pasivos financieros corrientes»). Si el título de un año
no aparece, no es que la nota no exista.

PARSER_VERSION sube cuando cambia este diccionario, el lector de tablas o el
cuadre que se publica. Una corrida no relee un archivo cuyo hash ya está ok
con la misma versión.
"""

from __future__ import annotations

import re
import unicodedata

PARSER_VERSION = 3

TABLAS_COMUNES = (
    "efectivo",
    "deudores",
    "pasivos_financieros",
    "cuentas_por_pagar",
    "relacionadas",
    "impuestos",
    "patrimonio",
    "ppe",
)

# Solo estas tienen columnas leídas de un PDF. El resto de las comunes
# queda en el índice con extraida=0. No se inventa la columna.
ESQUEMAS_CERRADOS = {
    "efectivo": ("concepto", "saldo_miles", "saldo_comparativo_miles"),
    "deudores": ("concepto", "colocacion_miles", "provision_miles", "neto_miles"),
}

_NO_COMUN = (
    ("politica", (
        "politica de", "politicas de", "politicas contables", "principales politicas",
        "principales criterios", "criterios contables", "bases de preparacion",
        "bases de presentacion", "nuevos pronunciamiento", "cambio en la politica",
        "cambios en politicas", "cambios contables",
    )),
    ("antecedentes", (
        "antecedentes de la", "informacion general", "informacion de la sociedad",
        "entidad que reporta", "aprobacion de los estados",
    )),
    ("segmentos", ("segmento",)),
    ("medio_ambiente", ("medio ambiente",)),
    ("contingencias", ("contingenc",)),
    ("sanciones", ("sancion",)),
    ("cauciones", ("caucion",)),
    ("hechos_posteriores", ("hechos posterior",)),
    ("hechos_relevantes", ("hechos relevante", "hechos esencial")),
    ("riesgos", (
        "factores de riesgo", "gestion del riesgo", "gestion de riesgo",
        "administracion del riesgo", "administracion de riesgo", "riesgo financiero",
    )),
    ("arrendamientos", ("arrendamiento", "derecho de uso", "derechos de uso", "derecho a usar")),
    ("deterioro", (
        "perdida de deterioro", "perdidas de deterioro", "perdidas por deterioro",
        "deterioro de valor", "deterioro niif", "perdidas crediticias",
    )),
    ("ingresos", (
        "ingresos y costos", "ingresos de actividades", "ingreso de actividades",
        "ingresos ordinarios", "ingresos por intereses", "composicion de resultados",
        "composicion de resultado",
    )),
    ("costos", ("costos de ventas", "costo de ventas", "costo de venta")),
    ("gastos", (
        "gastos de administracion", "gasto de administracion", "remuneracion del personal",
        "remuneraciones del directorio", "gastos del personal",
    )),
    ("asociadas", (
        "metodo de la participacion", "metodo de participacion",
        "inversiones en asociadas", "inversiones contabilizadas",
    )),
    ("intangibles", ("intangible", "plusvalia")),
    ("inventario", ("inventario",)),
    ("mantenidos_venta", ("mantenidos para la venta", "mantenido para la venta")),
    ("provisiones", (
        "provisiones", "provision por beneficio", "beneficios a los empleados",
        "beneficio a los empleados", "beneficios del personal",
    )),
    ("instrumentos", (
        "valor razonable", "valores razonables", "instrumento financiero",
        "instrumentos de deuda", "derivado", "forward", "swap",
    )),
    ("otros_activos", ("otros activos no financieros", "otros activos financieros", "activos financieros")),
    ("otros_pasivos", ("otros pasivos no financieros",)),
    ("reajuste", ("moneda extranjera", "unidades de reajuste", "diferencia de cambio")),
    ("dividendos", ("dividendo",)),
    ("personal", ("personal clave",)),
)

# Orden: relacionadas antes que cuentas por pagar, para que
# «cuentas por pagar a entidades relacionadas» no caiga en acreedores.
# «pasivos financieros» a secas no entra: «vencimiento de activos y pasivos
# financieros» no es la nota de deuda.
_COMUNES = (
    ("relacionadas", (
        "entidades relacionadas", "entidad relacionada",
        "empresas relacionadas", "empresa relacionada",
        "partes relacionadas", "parte relacionada",
    )),
    ("efectivo", ("efectivo y equivalente",)),
    ("deudores", (
        "deudores comerciales", "deudor comercial",
        "cuentas comerciales por cobrar",
        "cuentas por cobrar y otras cuentas por cobrar",
    )),
    ("pasivos_financieros", (
        "otros pasivos financieros",
        "prestamos que devengan interes",
        "prestamo que devenga interes",
    )),
    ("cuentas_por_pagar", (
        "cuentas por pagar comerciales",
        "cuentas comerciales y otras cuentas por pagar",
        "acreedores comerciales",
    )),
    ("impuestos", ("impuesto",)),
    ("ppe", (
        "propiedades planta", "propiedad planta",
        "plantas y equipos", "planta y equipo",
    )),
    ("patrimonio", (
        "movimientos de patrimonio", "capital y reservas",
        "patrimonio y reservas", "capital emitido", "patrimonio",
    )),
)

_CARA = (
    ("total_pasivo_patrimonio", ("total de patrimonio y pasivos", "total patrimonio y pasivos"), ()),
    ("total_activos_corrientes", (
        "activos corrientes totales", "total de activos corrientes",
        "total activos corrientes", "totales de activos corrientes",
    ), ()),
    ("total_activos_no_corrientes", (
        "total de activos no corrientes", "total activos no corrientes",
        "totales de activos no corrientes", "total activo no corriente",
    ), ()),
    ("total_activos", ("total de activos", "totales de activos", "total activos"), ("corriente",)),
    ("total_pasivos_corrientes", (
        "pasivos corrientes totales", "total de pasivos corrientes",
        "total pasivos corrientes", "totales de pasivos corrientes", "total pasivo corriente",
    ), ()),
    ("total_pasivos_no_corrientes", (
        "total de pasivos no corrientes", "total pasivos no corrientes",
        "totales de pasivos no corrientes", "total pasivo no corriente",
    ), ()),
    ("total_pasivos", ("total de pasivos", "totales de pasivos", "total pasivos"), ("corriente",)),
    ("total_patrimonio", (
        "patrimonio neto total", "patrimonio total", "total de patrimonio",
        "totales de patrimonio", "total patrimonio",
    ), ("pasivo",)),
    ("efectivo", ("efectivo y equivalente",), ()),
    ("deudores", ("deudores comerciales", "cuentas comerciales por cobrar"), ()),
    ("otros_activos_no_financieros", ("otros activos no financieros",), ()),
    ("ppe", ("propiedades planta", "propiedad planta", "plantas y equipos", "planta y equipo"), ()),
    ("cuentas_por_pagar", (
        "cuentas por pagar comerciales", "cuentas comerciales y otras cuentas por pagar",
    ), ()),
    ("relacionadas_por_cobrar", (
        "cuentas por cobrar a entidades relacionadas",
        "cuentas por cobrar a empresas relacionadas",
    ), ()),
    ("relacionadas_por_pagar", (
        "cuentas por pagar a entidades relacionadas",
        "cuentas por pagar a empresas relacionadas",
    ), ()),
    ("pasivos_financieros", ("otros pasivos financieros",), ()),
    ("capital", ("capital emitido", "capital pagado", "capital en acciones"), ()),
    ("ganancias_acumuladas", (
        "ganancias acumuladas", "ganancias perdidas acumuladas",
        "resultados acumulados", "resultado acumulado", "resultados retenidos",
    ), ()),
    ("ingresos", (
        "ingresos de actividades ordinarias", "ingreso de actividades ordinarias",
        "ingresos ordinarios",
    ), ()),
    ("costo_ventas", ("costos de ventas", "costo de ventas", "costo de venta"), ()),
    ("ganancia_bruta", ("ganancia bruta", "margen bruto"), ()),
    ("gasto_administracion", ("gastos de administracion", "gasto de administracion"), ()),
    ("unidades_reajuste", ("unidades de reajuste",), ()),
    ("impuesto", (
        "gastos por impuestos", "gasto por impuestos", "gasto por impuesto",
        "impuesto a las ganancias",
    ), ()),
    ("ganancia_periodo", (
        "ganancia perdida del periodo", "ganancia del periodo",
        "resultado del periodo", "utilidad perdida del periodo", "utilidad del periodo",
        "utilidad perdida del ejercicio", "utilidad del ejercicio", "resultado del ejercicio",
    ), ()),
)

_SUFIJO_NO_CORRIENTE = {
    "deudores", "pasivos_financieros", "relacionadas_por_cobrar",
    "relacionadas_por_pagar", "cuentas_por_pagar", "ppe",
    "otros_activos_no_financieros", "efectivo",
}


def fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = raw.lower()
    raw = re.sub(r"[^a-z0-9]+", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def clasificar_nota(titulo: str) -> dict:
    """tabla es una de las ocho comunes, o vacío. familia nunca usa el número."""
    blob = fold(titulo)
    if not blob:
        return {"tabla": "", "familia": "otra"}
    for familia, frases in _NO_COMUN:
        if any(frase in blob for frase in frases):
            return {"tabla": "", "familia": familia}
    if "cambios en patrimonio" in blob and "movimientos de patrimonio" not in blob:
        return {"tabla": "", "familia": "instrumentos"}
    for tabla, frases in _COMUNES:
        if tabla == "pasivos_financieros" and "vencimiento" in blob:
            continue
        if any(frase in blob for frase in frases):
            return {"tabla": tabla, "familia": tabla}
    return {"tabla": "", "familia": "otra"}


def familia_nota(titulo: str) -> str:
    clas = clasificar_nota(titulo)
    return clas["tabla"] or clas["familia"]


def _contiene(blob: str, frase: str, bloquear: tuple[str, ...]) -> bool:
    if frase not in blob:
        return False
    resto = blob.replace(frase, " ", 1)
    return not any(token in resto for token in bloquear)


def cuenta_cara(nombre: str, estado: str = "") -> str:
    """Cuenta canónica de la carátula. Vacío si el alias no calza. No renombra el PDF."""
    blob = fold(nombre)
    if not blob:
        return ""
    if estado == "resultado" and blob == "ingresos":
        return "ingresos"
    for canon, frases, bloquear in _CARA:
        if any(_contiene(blob, frase, bloquear) for frase in frases):
            if canon in _SUFIJO_NO_CORRIENTE and "no corriente" in blob:
                return f"{canon}_no_corriente"
            return canon
    return ""

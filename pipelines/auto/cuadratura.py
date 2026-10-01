"""Cuadratura contable de los balances y del estado de resultados antes de publicarlos.

El README promete que «un balance que no cuadra detiene la publicación». Este módulo es esa
compuerta para los extractores de estados financieros IFRS (AGF, securitizadoras, cajas de
compensación y corredoras) y para la auditoría de la serie de factoring y leasing. Sigue la
política de fondos de inversión (fi/scripts), ajustada a que aquí hay ~50 balances por
trimestre y no ~900:

  * un balance aislado que no cuadra no se descarta: queda como aviso en el manifiesto
    (a veces es la propia sociedad la que presentó mal su XBRL y la fuente nunca lo corrige;
    detener el trimestre por eso lo dejaría sin publicar para siempre);
  * si descuadran al menos MIN_MALOS balances y más de MAX_DESCUADRE de los verificados, es un
    problema de lectura (columnas corridas, glosas nuevas), no de una sociedad: el trimestre no
    se publica y se reintenta en la próxima corrida (fail-closed);
  * y si de pronto casi ningún balance se puede verificar, también se detiene: significa que
    cambió la forma de informar los totales y la compuerta se quedó ciega (ver más abajo).

Tolerancia: los totales vienen redondeados (a miles de pesos), así que se acepta una diferencia
de hasta `tol_abs` (una unidad del redondeo) o de 1 millonésima del activo, lo que sea mayor.
Con la historia publicada (2009-2026) cuadran los 3.793 balances IFRS de AGF, securitizadoras y
CCAF (uno de ellos con 1 mil pesos de redondeo) y los 2.861 de corredores y agentes de valores.

Por qué la compuerta mira también la cobertura
----------------------------------------------
Los totales se reconocen por su glosa («Total de activos»), comparada de forma normalizada
(minúsculas, sin acentos, sin comas, espacios colapsados). Es una lista blanca, y una lista
blanca tiene un modo de fallar traicionero: si la CMF renombra un total, `verificados` cae a
cero, `verificados >= MIN_PARA_COMPUERTA` deja de cumplirse y **la compuerta se apaga en
silencio** — el trimestre se publica sin ningún control, justo cuando más falta hacía. No es un
riesgo teórico: dentro del propio archivo conviven hoy dos convenciones («Total de activos» y
«Activos, Total», esta última en una securitizadora de 2009).

Por eso `debe_detener()` acepta `balances_totales`: si la fracción de balances que se pudo
verificar baja de `cobertura_minima`, se detiene igual. Una compuerta que no puede verificar no
es una compuerta abierta: es una compuerta rota, y se trata como tal.

Estado de resultados
--------------------
`verificar_resultados()` aplica dos identidades que se cumplen en el 100 % de la historia
publicada y que hasta ahora nadie comprobaba:

  * la primera línea del estado de resultados integral (`ERI`) es la misma ganancia del
    ejercicio que cierra el `ERFG`/`ERNG`: si difieren, algo se leyó mal (o el `ERI` dejó de
    arrastrar el resultado);
  * ganancia bruta = ingresos ordinarios − costo de ventas.

Tolerancia de 1 peso: son identidades exactas en la fuente, no agregados redondeados.
"""
from __future__ import annotations

import unicodedata

MAX_DESCUADRE = 0.05
MIN_MALOS = 3
MIN_PARA_COMPUERTA = 20  # con menos balances verificados no se puede hablar de «porcentaje»
COBERTURA_MINIMA = 0.90  # fracción mínima de balances que debe poder verificarse

# Glosas de los totales en los TXT IFRS de la CMF (comparadas normalizadas: ver `_glosa`).
# La lista se amplió con las variantes que aparecen en la historia publicada, incluida la
# nomenclatura antigua con comas («Activos, Total»).
ACTIVOS = {"total de activos", "total activos", "activos totales", "activos total", "total activo"}
PASIVOS = {"total de pasivos", "total pasivos", "pasivos totales", "pasivos total", "total pasivo"}
PATRIMONIO = {"patrimonio total", "total patrimonio", "total de patrimonio", "patrimonio neto",
              "total patrimonio neto", "patrimonio neto total"}

# Cuentas del estado de resultados usadas en las identidades.
GANANCIA = {"ganancia (pérdida)", "ganancia (perdida)"}
INGRESOS = {"ingresos de actividades ordinarias", "ingresos ordinarios", "ingresos ordinarios total",
            "ingresos de operacion", "ingresos de explotacion"}
COSTO_VENTAS = {"costo de ventas", "costos de ventas", "costo de venta"}
GANANCIA_BRUTA = {"ganancia bruta", "margen bruto", "ganancia bruta total"}


def _glosa(f: dict) -> str:
    """Glosa normalizada: minúsculas, sin acentos, sin comas ni puntos, espacios colapsados."""
    s = str(f.get("cuenta") or "")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = s.lower().replace(",", " ").replace(".", " ")
    return " ".join(s.split())


def contar_grupos(filas, claves) -> int:
    """Cuántos balances (o estados) distintos hay en estas filas, verificables o no."""
    return len({tuple(f.get(c) for c in claves) for f in filas})


def verificar(filas, claves, valor, clasificar, tol_abs=1000):
    """Verifica activos = pasivos + patrimonio por balance.

    filas       iterable de dicts (filas del balance de un trimestre)
    claves      campos que identifican un balance (p. ej. rut, tipo, moneda, estado, repetición)
    valor       campo numérico
    clasificar  f(fila) -> 'A' | 'P' | 'E' | None (activos, pasivos, patrimonio)
    Devuelve (balances_verificados, [descripción de cada descuadre]).
    Un balance solo se verifica si trae los tres totales con valor numérico.
    """
    tot: dict[tuple, dict[str, float]] = {}
    for f in filas:
        k = clasificar(f)
        v = f.get(valor)
        if k is None or v is None:
            continue
        tot.setdefault(tuple(f.get(c) for c in claves), {}).setdefault(k, v)
    verificados, malos = 0, []
    for clave, t in tot.items():
        if not {"A", "P", "E"} <= t.keys():
            continue
        verificados += 1
        delta = t["A"] - t["P"] - t["E"]
        if abs(delta) > max(tol_abs, abs(t["A"]) * 1e-6):
            malos.append(f"{'/'.join(map(str, clave))}: activos {t['A']} ≠ pasivos {t['P']} + patrimonio {t['E']} (Δ {delta})")
    return verificados, malos


def clasificar_ifrs(f: dict):
    g = _glosa(f)
    return "A" if g in ACTIVOS else "P" if g in PASIVOS else "E" if g in PATRIMONIO else None


CLAVES_IFRS = ("rut", "tipo_balance", "moneda", "estado_financiero", "repeticion")
CLAVES_FL = ("rut", "tipo_balance", "moneda_archivo", "estado_financiero", "repeticion_contexto")


def verificar_ifrs(filas, tol_abs=1000):
    """Balances de los TXT IFRS (AGF, securitizadoras, CCAF)."""
    return verificar(filas, CLAVES_IFRS, "valor", clasificar_ifrs, tol_abs)


def verificar_fl(filas, tol_abs=1000):
    """Balances de la serie de factoring y leasing (mismo TXT, otro esquema de columnas)."""
    return verificar(filas, CLAVES_FL, "valor_archivo", clasificar_ifrs, tol_abs)


def clasificar_fecu(f: dict):
    return {"10.00.00": "A", "21.00.00": "P", "22.00.00": "E"}.get(str(f.get("codigo_fecu")))


def verificar_fecu(filas, tol_abs=1):
    """Balances de corredores y agentes de valores (plan FECU IFRS, miles de pesos)."""
    return verificar(filas, ("rut", "tipo_intermediario"), "valor_miles_clp", clasificar_fecu, tol_abs)


# ---------------------------------------------------------------------------
# Estado de resultados
# ---------------------------------------------------------------------------

def clasificar_resultado(f: dict):
    """'G' ganancia del ejercicio · 'I' ingresos · 'C' costo de ventas · 'B' ganancia bruta."""
    g = _glosa(f)
    if g in GANANCIA:
        return "G"
    if g in INGRESOS:
        return "I"
    if g in COSTO_VENTAS:
        return "C"
    if g in GANANCIA_BRUTA:
        return "B"
    return None


def verificar_resultados(filas, claves, valor, cuenta="cuenta", estado="estado_financiero",
                         repeticion="repeticion", tol_abs=1):
    """Identidades del estado de resultados por sociedad.

    filas   filas de resultados de un trimestre (ERFG, ERNG y ERI mezclados, como vienen)
    claves  campos que identifican a la sociedad y su presentación
            (p. ej. rut, tipo_balance, moneda); la repetición y el estado se agregan acá
    Devuelve (verificaciones, [descripción de cada divergencia]).
    """
    ganancia_er: dict[tuple, float] = {}
    ganancia_eri: dict[tuple, float] = {}
    bruta: dict[tuple, dict[str, float]] = {}
    for f in filas:
        est = str(f.get(estado) or "")
        if not est.startswith("ER"):
            continue
        letra = clasificar_resultado(f)
        v = f.get(valor)
        if letra is None or v is None:
            continue
        base = tuple(f.get(c) for c in claves) + (f.get(repeticion),)
        if est.startswith("ERI"):
            if letra == "G":
                ganancia_eri.setdefault(base, v)
            continue
        if letra == "G":
            ganancia_er.setdefault(base, v)
        elif letra in ("I", "C", "B"):
            bruta.setdefault(base + (est,), {}).setdefault(letra, v)

    verificaciones, malos = 0, []
    # 1) El resultado integral arrastra la misma ganancia del ejercicio que el estado de
    #    resultados. Si dejan de coincidir, una de las dos lecturas está mal.
    for clave, v in sorted(ganancia_er.items()):
        if clave not in ganancia_eri:
            continue
        verificaciones += 1
        otra = ganancia_eri[clave]
        if abs(otra - v) > max(tol_abs, abs(v) * 1e-6):
            malos.append(f"{'/'.join(map(str, clave))}: ERI {otra} ≠ ER {v} (Δ {otra - v})")
    # 2) Ganancia bruta = ingresos ordinarios − costo de ventas.
    for clave, t in sorted(bruta.items()):
        if not {"I", "C", "B"} <= t.keys():
            continue
        verificaciones += 1
        delta = t["B"] - (t["I"] - t["C"])
        if abs(delta) > max(tol_abs, abs(t["I"]) * 1e-6):
            malos.append(f"{'/'.join(map(str, clave))}: ganancia bruta {t['B']} ≠ "
                         f"ingresos {t['I']} − costo {t['C']} (Δ {delta})")
    return verificaciones, malos


def verificar_resultados_ifrs(filas, tol_abs=1):
    """Estado de resultados de los TXT IFRS (AGF, securitizadoras, CCAF)."""
    return verificar_resultados(filas, ("rut", "tipo_balance", "moneda"), "valor")


def verificar_resultados_fl(filas, tol_abs=1):
    """Estado de resultados de la serie de factoring y leasing."""
    return verificar_resultados(filas, ("rut", "tipo_balance", "moneda_archivo"), "valor_archivo",
                                repeticion="repeticion_contexto")


# ---------------------------------------------------------------------------
# Compuerta
# ---------------------------------------------------------------------------

def debe_detener(verificados: int, malos: list, balances_totales: int | None = None,
                 cobertura_minima: float = COBERTURA_MINIMA) -> bool:
    """¿Hay que frenar la publicación del trimestre?

    Además del descuadre por bloque, se detiene cuando la fracción de balances que se pudo
    verificar cae por debajo de `cobertura_minima`: es la señal de que la compuerta se quedó
    ciega (cambiaron las glosas de los totales) y no de que los balances estén bien.
    """
    if (verificados >= MIN_PARA_COMPUERTA and len(malos) >= MIN_MALOS
            and len(malos) > MAX_DESCUADRE * verificados):
        return True
    if balances_totales and balances_totales >= MIN_PARA_COMPUERTA:
        if verificados < cobertura_minima * balances_totales:
            return True
    return False


def motivo_detener(verificados: int, malos: list, balances_totales: int | None = None,
                   cobertura_minima: float = COBERTURA_MINIMA) -> str:
    """Explicación de `debe_detener`, para el manifiesto y el log de la corrida."""
    if (verificados >= MIN_PARA_COMPUERTA and len(malos) >= MIN_MALOS
            and len(malos) > MAX_DESCUADRE * verificados):
        return (f"{len(malos)} de {verificados} balances no cuadran "
                f"(activos ≠ pasivos + patrimonio). Ej.: {malos[0]}")
    if balances_totales and balances_totales >= MIN_PARA_COMPUERTA:
        if verificados < cobertura_minima * balances_totales:
            return (f"solo {verificados} de {balances_totales} balances traen los tres totales "
                    f"reconocibles ({verificados / balances_totales:.0%} < {cobertura_minima:.0%}): "
                    "cambiaron las glosas del archivo y la compuerta no puede verificar la lectura")
    return ""

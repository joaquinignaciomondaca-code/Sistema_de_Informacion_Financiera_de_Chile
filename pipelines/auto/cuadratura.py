"""Cuadratura contable de los balances antes de publicarlos: activos = pasivos + patrimonio.

El README promete que «un balance que no cuadra detiene la publicación». Este módulo es esa
compuerta para los extractores de estados financieros IFRS (AGF, securitizadoras, cajas de
compensación y corredoras). Sigue la política de fondos de inversión (fi/scripts), ajustada a que aquí hay ~50 balances por
trimestre y no ~900:

  * un balance aislado que no cuadra no se descarta: queda como aviso en el manifiesto
    (a veces es la propia sociedad la que presentó mal su XBRL y la fuente nunca lo corrige;
    detener el trimestre por eso lo dejaría sin publicar para siempre);
  * si descuadran al menos MIN_MALOS balances y más de MAX_DESCUADRE de los verificados, es un
    problema de lectura (columnas corridas, glosas nuevas), no de una sociedad: el trimestre no
    se publica y se reintenta en la próxima corrida (fail-closed).

Tolerancia: los totales vienen redondeados (a miles de pesos), así que se acepta una diferencia
de hasta `tol_abs` (una unidad del redondeo) o de 1 millonésima del activo, lo que sea mayor.
Con la historia publicada (2009-2026) cuadran los 3.793 balances IFRS de AGF, securitizadoras y
CCAF (uno de ellos con 1 mil pesos de redondeo) y los 2.861 de corredores y agentes de valores.
"""
from __future__ import annotations

MAX_DESCUADRE = 0.05
MIN_MALOS = 3
MIN_PARA_COMPUERTA = 20  # con menos balances verificados no se puede hablar de «porcentaje»

# Glosas de los totales en los TXT IFRS de la CMF (comparadas en minúsculas y sin espacios sobrantes).
ACTIVOS = {"total de activos", "total activos", "activos totales"}
PASIVOS = {"total de pasivos", "total pasivos", "pasivos totales"}
PATRIMONIO = {"patrimonio total", "total patrimonio", "total de patrimonio"}


def _glosa(f: dict) -> str:
    return " ".join(str(f.get("cuenta") or "").lower().split())


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


def verificar_ifrs(filas, tol_abs=1000):
    """Balances de los TXT IFRS (AGF, securitizadoras, CCAF)."""
    return verificar(filas, ("rut", "tipo_balance", "moneda", "estado_financiero", "repeticion"),
                     "valor", clasificar_ifrs, tol_abs)


def clasificar_fecu(f: dict):
    return {"10.00.00": "A", "21.00.00": "P", "22.00.00": "E"}.get(str(f.get("codigo_fecu")))


def verificar_fecu(filas, tol_abs=1):
    """Balances de corredores y agentes de valores (plan FECU IFRS, miles de pesos)."""
    return verificar(filas, ("rut", "tipo_intermediario"), "valor_miles_clp", clasificar_fecu, tol_abs)


def debe_detener(verificados: int, malos: list) -> bool:
    return (verificados >= MIN_PARA_COMPUERTA and len(malos) >= MIN_MALOS
            and len(malos) > MAX_DESCUADRE * verificados)

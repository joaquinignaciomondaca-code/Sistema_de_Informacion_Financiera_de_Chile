"""Lectura del XML IFRS de fondos mutuos de la CMF («FMEF», Circular 1997 de 2010) y de la ficha que lo enlaza.

Módulo puro: sin red ni disco. Lo usa `actualizar_eeff.py` y lo prueban `ffmm/tests`.

Qué es el archivo
-----------------
Cada fondo envía a la CMF un XML con raíz `<IFRS>`: `Identificacion`, `DatosPeriodo`, `Contextos` y una lista
plana de `<Cuenta CodigoCuenta=… Context=PeriodoActual|PeriodoAnterior Nota=… Serie=…>valor</Cuenta>`. Trae el
ejercicio y el anterior, en **miles de la moneda funcional**, sin decimales. Para balance y resultados las cuentas
no llevan serie; el estado de cambios del activo neto sí (no se publica). El XML lista las cuentas en orden
alfabético, no en el de presentación: el `orden` sale del catálogo `CATALOGO` (el de la ficha de la CMF).

Lo que se midió con 278 fondo-años reales (docs/notas/ffmm_estados_financieros_xml_2026-10-01.md) y este módulo
maneja a propósito:

  * la declaración de codificación no es fiable (UTF-8 falso, ausente o inventada: `iso-8011-K`): se descarta y el
    cuerpo se decodifica por contenido (UTF-8 estricto y, si falla, latin-1);
  * la CMF a veces responde una página de desafío JavaScript en lugar de la ficha, o algo que no es el XML: eso es
    un error **transitorio** (se reintenta) y nunca equivale a «sin información»;
  * el modelo Excel oficial de 2011 llama `Otros` a la línea «Otros» del estado de resultados; los archivos reales
    usan `OtrosEri` (`Otros` existe además en el flujo de efectivo). Se acepta `Otros` solo si falta `OtrosEri`
    y las identidades contables lo validan;
  * códigos con espacio final y elementos de cuenta con código vacío;
  * `PROM` es dólares (la ficha dice «miles de Dolar»), `$$` es pesos y `EUR` euros.
"""
from __future__ import annotations

import html as _html
import re
import unicodedata
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Catálogo oficial de cuentas: (orden, código del XML, glosa, sección, tipo de línea)
# El orden es el de presentación de la ficha de la CMF y es fijo por cuenta.
# ---------------------------------------------------------------------------
CATALOGO: dict[str, list[tuple[int, str, str, str, str]]] = {
    "balance": [
        (1, "EfectivoYEfectivoEquivalente", "Efectivo y efectivo equivalente", "ACTIVO", "detalle"),
        (2, "ActivosFinancierosAValorRazonableConEfectoEnResultados",
         "Activos financieros a valor razonable con efecto en resultados", "ACTIVO", "detalle"),
        (3, "ActivosFinancierosAValorRazonableConEfectoEnResultadosEntregadosEnGarantia",
         "Activos financieros a valor razonable con efecto en resultados entregados en garantía", "ACTIVO", "detalle"),
        (4, "ActivosFinancierosACostoAmortizado", "Activos financieros a costo amortizado", "ACTIVO", "detalle"),
        (5, "CuentasPorCobrarAIntermediarios", "Cuentas por cobrar a intermediarios", "ACTIVO", "detalle"),
        (6, "OtrasCuentasPorCobrar", "Otras cuentas por cobrar", "ACTIVO", "detalle"),
        (7, "OtrosActivos", "Otros activos", "ACTIVO", "detalle"),
        (8, "TotalActivo", "Total activo", "ACTIVO", "total"),
        (9, "PasivosFinancierosAValorRazonableConEfectoEnResultados",
         "Pasivos financieros a valor razonable con efecto en resultados", "PASIVO", "detalle"),
        (10, "CuentasPorAPagarIntermediarios", "Cuentas por pagar a intermediarios", "PASIVO", "detalle"),
        (11, "RescatesPorPagar", "Rescates por pagar", "PASIVO", "detalle"),
        (12, "RemuneracionesSociedadAdministradora", "Remuneraciones sociedad administradora", "PASIVO", "detalle"),
        (13, "OtrosDocumentosYCuentasPorPagar", "Otros documentos y cuentas por pagar", "PASIVO", "detalle"),
        (14, "OtrosPasivos", "Otros pasivos", "PASIVO", "detalle"),
        (15, "TotalPasivo", "Total pasivo (excluido el activo neto atribuible a partícipes)", "PASIVO", "total"),
        (16, "ActivoNetoAtribuibleALosParticipes", "Activo neto atribuible a los partícipes", "ACTIVO NETO", "total"),
    ],
    "resultados": [
        (1, "InteresesYReajustes", "Intereses y reajustes", "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "detalle"),
        (2, "IngresosPorDividendos", "Ingresos por dividendos", "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "detalle"),
        (3, "DiferenciasDeCambioNetasSobreActivosFinancierosACostoAmortizado",
         "Diferencias de cambio netas sobre activos financieros a costo amortizado",
         "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "detalle"),
        (4, "DiferenciasDeCambioNetasSobreEfectivoYEfectivoEquivalente",
         "Diferencias de cambio netas sobre efectivo y efectivo equivalente",
         "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "detalle"),
        (5, "CambiosNetosEnValorRazonableDeActivosYPasivosFinancierosAValorRazonableConEfectoEnResultados",
         "Cambios netos en valor razonable de activos financieros y pasivos financieros a valor razonable "
         "con efecto en resultados", "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "detalle"),
        (6, "ResultadoEnVentaDeInstrumentosFinancieros", "Resultado en venta de instrumentos financieros",
         "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "detalle"),
        (7, "OtrosEri", "Otros", "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "detalle"),
        (8, "TotalIngresosPerdidasNetosDeLaOperacion", "Total ingresos/(pérdidas) netos de la operación",
         "INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "total"),
        (9, "ComisionDeAdministracion", "Comisión de administración", "GASTOS", "detalle"),
        (10, "HonorariosPorCustodiaYAdministracion", "Honorarios por custodia y administración", "GASTOS", "detalle"),
        (11, "CostosDeTransaccion", "Costos de transacción", "GASTOS", "detalle"),
        (12, "OtrosGastosDeOperacion", "Otros gastos de operación", "GASTOS", "detalle"),
        (13, "TotalGastosDeOperacion", "Total gastos de operación", "GASTOS", "total"),
        (14, "UtilidadPerdidaDeLaOperacionAntesDeImpuesto", "Utilidad/(pérdida) de la operación antes de impuesto",
         "RESULTADO", "total"),
        (15, "ImpuestosALasGananciasPorInversionesEnElExterior",
         "Impuestos a las ganancias por inversiones en el exterior", "RESULTADO", "detalle"),
        (16, "UtilidadPerdidaDeLaOperacionDespuesDeImpuesto", "Utilidad/(pérdida) de la operación después de impuesto",
         "RESULTADO", "total"),
        (17, "AumentoDisminucionDeActivoNetoAtribuibleAParticipesOriginadasPorActividadesDeLaOperacionAntesDeDistribucionDeBeneficios",
         "Aumento/(disminución) de activo neto atribuible a partícipes originadas por actividades de la operación "
         "antes de distribución de beneficios", "RESULTADO", "total"),
        (18, "DistribucionDeBeneficios", "Distribución de beneficios", "RESULTADO", "detalle"),
        (19, "AumentoDisminucionDeActivoNetoAtribuibleAParticipesOriginadasPorActividadesDeLaOperacionDespuesDeDistribucionDeBeneficios",
         "Aumento/(disminución) de activo neto atribuible a partícipes originadas por actividades de la operación "
         "después de distribución de beneficios", "RESULTADO", "total"),
    ],
}
CODIGOS = {c[1] for lineas in CATALOGO.values() for c in lineas}
# El modelo oficial de 2011 llamaba `Otros` a la línea de resultados; hoy es `OtrosEri`.
ALIAS = {"OtrosEri": ("Otros",)}
# `$$` pesos · `PROM` dólares (la ficha dice «miles de Dolar») · `EUR` euros (hay fondos en euros: no aparecieron en la
# muestra de 278 fondo-años, sí en el primer recorrido completo). Un código nuevo deja el fondo y cierre como ilegible.
MONEDAS = {"$$": "CLP", "PROM": "USD", "EUR": "EUR"}
CONTEXTOS = ("PeriodoActual", "PeriodoAnterior")

RE_XML = re.compile(r"ifrs_xml_verarchivo\.php\?archivo=(FMEF[A-Za-z0-9_\-]+\.xml)")
RE_ENVIO = re.compile(r"_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_")


class ErrorFuente(Exception):
    """El contenido llegó completo pero no sirve (cuentas faltantes, otro fondo, moneda desconocida…)."""


class ErrorTransitorio(Exception):
    """No llegó la ficha o el XML (desafío de la CMF, respuesta intermedia, corte): se reintenta."""


# ---------------------------------------------------------------------------
# Ficha del fondo
# ---------------------------------------------------------------------------

def _decodificar(cuerpo: bytes | str) -> str:
    if isinstance(cuerpo, str):
        return cuerpo
    try:
        return cuerpo.decode("utf-8")
    except UnicodeDecodeError:
        return cuerpo.decode("latin-1")


def _plano(html: str) -> str:
    """Texto visible, en minúsculas y sin acentos (la ficha llega en UTF-8 o latin-1, con o sin entidades)."""
    t = _html.unescape(re.sub(r"<[^>]+>", " ", html))
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).lower()


def clave_envio(archivo: str) -> tuple[str, str]:
    return (enviado_de(archivo) or "", archivo)


def enviado_de(archivo: str) -> str | None:
    """Fecha y hora de envío a la CMF, que lleva el nombre del archivo: `…_20260330_110924_8011.xml`."""
    m = RE_ENVIO.search(archivo or "")
    return f"{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}:{m[6]}" if m else None


def clasificar_ficha(cuerpo: bytes | str) -> tuple[str, str | None]:
    """Qué dice la ficha de un fondo para un cierre.

    Devuelve ('xml', archivo) · ('sin_informacion', None) · ('sin_enlace', None).
    Lanza ErrorTransitorio si la respuesta no es la ficha (p. ej. la página de desafío JavaScript de la CMF):
    confundirla con «sin información» abriría un hueco silencioso en la serie.
    """
    html = _decodificar(cuerpo)
    texto = _plano(html)
    # El enlace al XML o el aviso de «sin información» bastan por sí solos: no dependen de que el menú esté en el HTML.
    enlaces = set(RE_XML.findall(html.replace("&amp;", "&")))
    if enlaces:
        return "xml", max(enlaces, key=clave_envio)  # si hubo reenvíos, el más reciente
    if "no existe informacion de la entidad" in texto:
        return "sin_informacion", None
    # Sin lo anterior, solo una ficha real (su menú dice «Información Financiera») puede estar sin enlace; el desafío
    # JavaScript de la CMF no trae nada de eso.
    if "informacion financiera" in texto:
        return "sin_enlace", None
    raise ErrorTransitorio("la respuesta no es la ficha del fondo (¿página de desafío de la CMF?): «"
                           + (texto[:100] or "vacía") + "»")


# ---------------------------------------------------------------------------
# XML
# ---------------------------------------------------------------------------

def leer_xml(raw: bytes) -> ET.Element:
    """Parsea el XML ignorando su declaración de codificación (no es fiable) y valida que esté completo."""
    cuerpo = raw.lstrip(b"\xef\xbb\xbf")
    cuerpo = re.sub(rb"^\s*<\?xml[^>]*\?>", b"", cuerpo)
    if b"<IFRS" not in cuerpo[:3000]:
        raise ErrorTransitorio("la respuesta no es el XML IFRS (¿página intermedia de la CMF?)")
    if not cuerpo.rstrip().endswith(b"</IFRS>"):
        raise ErrorTransitorio("XML incompleto (no cierra </IFRS>)")
    try:
        txt = cuerpo.decode("utf-8")
    except UnicodeDecodeError:
        txt = cuerpo.decode("latin-1")
    try:
        return ET.fromstring(txt)
    except ET.ParseError as e:
        raise ErrorFuente(f"XML mal formado: {e}") from e


def _texto(nodo: ET.Element | None, ruta: str) -> str:
    if nodo is None:
        return ""
    return " ".join((nodo.findtext(ruta) or "").split())


def _entero(txt: str | None, codigo: str) -> int:
    s = (txt or "").strip()
    if re.fullmatch(r"[+-]?\d+", s):
        return int(s)
    if re.fullmatch(r"[+-]?\d+[.,]0+", s):
        return int(re.split(r"[.,]", s)[0])
    raise ErrorFuente(f"{codigo}: importe no entero {s!r}")


def dv(cuerpo: str) -> str:
    s, m = 0, 2
    for c in reversed(cuerpo):
        s += int(c) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def _solo_digitos(s: str) -> str:
    d = re.sub(r"\D", "", s or "").lstrip("0")
    return d


def extraer(raiz: ET.Element, run: str, anio: int) -> dict:
    """Identificación, moneda y las 35 cuentas de balance y resultados del ejercicio (y del anterior).

    Lanza ErrorFuente si el archivo no es del fondo y cierre pedidos, si la moneda es desconocida o si falta
    alguna cuenta del ejercicio actual.
    """
    ident, per = raiz.find("Identificacion"), raiz.find("DatosPeriodo")
    if ident is None or per is None:
        raise ErrorFuente("faltan los bloques Identificacion o DatosPeriodo")
    run_xml = _solo_digitos(_texto(ident, "RUTFondoInforma"))
    if run_xml != run:
        raise ErrorFuente(f"el archivo es del fondo {run_xml or '?'}, no del {run}")
    mes = _texto(per, "PeriodoPresentacionEstadosFinancieros/Mes")
    anio_xml = _texto(per, "PeriodoPresentacionEstadosFinancieros/Anio")
    if mes.lstrip("0") != "12" or anio_xml != str(anio):
        raise ErrorFuente(f"el archivo informa {mes or '?'}/{anio_xml or '?'}, no 12/{anio}")
    moneda_cmf = _texto(per, "MonedaPresentacionEstadosFinancieros")
    moneda = MONEDAS.get(moneda_cmf)
    if moneda is None:
        raise ErrorFuente(f"moneda desconocida {moneda_cmf!r}")

    crudo: dict[str, dict[str, int]] = {c: {} for c in CONTEXTOS}
    notas: dict[str, str] = {}
    repetidas = 0
    buscados = CODIGOS | {a for al in ALIAS.values() for a in al}
    for c in raiz.iterfind("Cuenta"):
        if c.get("Serie"):
            continue
        ctx = c.get("Context") or ""
        cod = (c.get("CodigoCuenta") or "").strip()
        if ctx not in crudo or cod not in buscados:
            continue
        v = _entero(c.text, cod)
        if cod in crudo[ctx]:
            if crudo[ctx][cod] != v:
                raise ErrorFuente(f"{cod}: aparece dos veces en {ctx} con importes distintos")
            repetidas += 1
            continue
        crudo[ctx][cod] = v
        if ctx == "PeriodoActual" and (c.get("Nota") or "").strip():
            notas[cod] = c.get("Nota").strip()

    def con_alias(cuentas: dict[str, int]) -> dict[str, int]:
        out = {k: v for k, v in cuentas.items() if k in CODIGOS}
        for canonico, otros in ALIAS.items():
            if canonico not in out:
                for a in otros:
                    if a in cuentas:
                        out[canonico] = cuentas[a]
                        break
        return out

    actual, anterior = con_alias(crudo["PeriodoActual"]), con_alias(crudo["PeriodoAnterior"])
    faltan = sorted(CODIGOS - actual.keys())
    if faltan:
        raise ErrorFuente(f"faltan {len(faltan)} cuentas del ejercicio: {', '.join(faltan[:4])}"
                          + ("…" if len(faltan) > 4 else ""))
    # Si la línea de resultados vino con el alias antiguo, la nota (si la hay) se guarda con el código canónico.
    for canonico, otros in ALIAS.items():
        for a in otros:
            if canonico not in crudo["PeriodoActual"] and a in notas:
                notas[canonico] = notas.pop(a)
    # El dígito verificador del XML es un dato digitado por la administradora y a veces está mal (85 fondo-años de 61 fondos
    # en el primer recorrido completo, con el mismo fondo bien en otros años). El del RUN se calcula, y coincide con el
    # registro oficial de la CMF en los 1.124 fondos publicados: ese es el que se publica; la diferencia queda como aviso.
    dv_xml = _texto(ident, "DVFondoInforma").upper()
    return {
        "run_dv": f"{run}-{dv(run)}",
        "dv_xml": dv_xml,
        "dv_coincide": (not dv_xml) or dv_xml == dv(run),
        "nombre": _texto(ident, "NombreEntidadInforma"),
        "rut_agf": _solo_digitos(_texto(ident, "RUTAdministradora")),
        "agf": _texto(ident, "NombreAdministradoraInforma"),
        "moneda_cmf": moneda_cmf,
        "moneda": moneda,
        "actual": actual,
        "anterior": anterior,
        "notas": {k: v for k, v in notas.items() if k in CODIGOS},
        "repetidas": repetidas,
        "usa_alias": any(canonico not in crudo["PeriodoActual"] for canonico in ALIAS),
    }


# ---------------------------------------------------------------------------
# Filas publicadas
# ---------------------------------------------------------------------------

COLUMNAS = ("periodo", "run_fondo", "run_fondo_dv", "nombre_fondo", "rut_agf", "razon_social_agf", "moneda",
            "moneda_cmf", "seccion", "tipo_linea", "orden", "codigo_cuenta", "cuenta", "nota", "valor_miles_mf",
            "valor_anterior_miles_mf", "fuente_archivo", "enviado_cmf", "sha256_archivo")


def filas(reg: dict) -> dict[str, list[dict]]:
    """Filas de balance y de resultados de un fondo y cierre, en el orden oficial de las líneas."""
    out: dict[str, list[dict]] = {}
    for tabla, lineas in CATALOGO.items():
        out[tabla] = [{
            "periodo": f"{reg['anio']}-12", "run_fondo": reg["run"], "run_fondo_dv": f"{reg['run']}-{dv(reg['run'])}",
            "nombre_fondo": reg["nombre"] or None, "rut_agf": reg["rut_agf"] or None,
            "razon_social_agf": reg["agf"] or None, "moneda": reg["moneda"], "moneda_cmf": reg["moneda_cmf"],
            "seccion": seccion, "tipo_linea": tipo, "orden": orden, "codigo_cuenta": codigo, "cuenta": cuenta,
            "nota": (reg.get("notas") or {}).get(codigo), "valor_miles_mf": reg["actual"][codigo],
            "valor_anterior_miles_mf": (reg.get("anterior") or {}).get(codigo),
            "fuente_archivo": reg["archivo"], "enviado_cmf": reg.get("enviado"), "sha256_archivo": reg["sha256"],
        } for orden, codigo, cuenta, seccion, tipo in lineas]
    return out

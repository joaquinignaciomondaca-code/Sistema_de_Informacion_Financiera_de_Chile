"""XML IFRS FIEF de fondos de inversión (Circular 1998): balance y resultados.

Catálogo cotejado con fichas CMF FIRES/FINRE. No es el de fondos mutuos: aquí
TotalPasivo incluye patrimonio. El balance compara con PeriodoAnualAnterior;
resultados separa acumulados y trimestres con sus propios comparativos.
Módulo puro, sin red ni escrituras. Todo importe se conserva como entero exacto
(miles de la moneda de presentación), sin inferir ceros, moneda ni contextos.
"""

from __future__ import annotations

import calendar
import hashlib
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from pipelines.auto.rut import dv

# (código literal, glosa, sección, tipo de línea). Orden de la ficha, no del XML.
_BALANCE = [
    (
        "EfectivoYEfectivoEquivalente",
        "Efectivo y efectivo equivalente",
        "ACTIVO CORRIENTE",
        "detalle",
    ),
    (
        "ActivosFinancierosAValorRazonableConEfectoEnResultadosCorriente",
        "Activos financieros a valor razonable con efecto en resultados",
        "ACTIVO CORRIENTE",
        "detalle",
    ),
    (
        "ActivosFinancierosAValorRazonableConEfectoEnOtrosResultadosIntegralesCorriente",
        "Activos financieros a valor razonable con efecto en otros resultados integrales",
        "ACTIVO CORRIENTE",
        "detalle",
    ),
    (
        "ActivosFinancierosAValorRazonableConEfectoEnResultadosEntregadosEnGarantia",
        "Activos financieros a valor razonable con efecto en resultados entregados en garantía",
        "ACTIVO CORRIENTE",
        "detalle",
    ),
    (
        "ActivosFinancierosACostoAmortizadoCorriente",
        "Activos financieros a costo amortizado",
        "ACTIVO CORRIENTE",
        "detalle",
    ),
    (
        "CuentasYDocumentosPorCobrarPorOperacionesCorriente",
        "Cuentas y documentos por cobrar por operaciones",
        "ACTIVO CORRIENTE",
        "detalle",
    ),
    (
        "OtrosDocumentosYCuentasPorCobrarCorriente",
        "Otros documentos y cuentas por cobrar",
        "ACTIVO CORRIENTE",
        "detalle",
    ),
    ("OtrosActivosCorriente", "Otros activos", "ACTIVO CORRIENTE", "detalle"),
    ("TotalActivoCorriente", "Total activo corriente", "ACTIVO CORRIENTE", "total"),
    (
        "ActivosFinancierosAValorRazonableConEfectoEnResultadosNoCorriente",
        "Activos financieros a valor razonable con efecto en resultados",
        "ACTIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "ActivosFinancierosAValorRazonableConEfectoEnOtrosResultadosIntegralesNoCorriente",
        "Activos financieros a valor razonable con efecto en otros resultados integrales",
        "ACTIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "ActivosFinancierosACostoAmortizadoNoCorriente",
        "Activos financieros a costo amortizado",
        "ACTIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "CuentasYDocumentosPorCobrarPorOperacionesNoCorriente",
        "Cuentas y documentos por cobrar por operaciones",
        "ACTIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "OtrosDocumentosYCuentasPorCobrarNoCorriente",
        "Otros documentos y cuentas por cobrar",
        "ACTIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "InversionesValorizadasPorElMetodoDeLaParticipacion",
        "Inversiones valorizadas por el método de la participación",
        "ACTIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "PropiedadesDeInversion",
        "Propiedades de inversión",
        "ACTIVO NO CORRIENTE",
        "detalle",
    ),
    ("OtrosActivosNoCorriente", "Otros activos", "ACTIVO NO CORRIENTE", "detalle"),
    (
        "TotalActivoNoCorriente",
        "Total activo no corriente",
        "ACTIVO NO CORRIENTE",
        "total",
    ),
    ("TotalActivo", "Total activo", "ACTIVO", "total"),
    (
        "PasivosFinancierosAValorRazonableConEfectoEnResultados",
        "Pasivos financieros a valor razonable con efecto en resultados",
        "PASIVO CORRIENTE",
        "detalle",
    ),
    ("PrestamosCorriente", "Préstamos", "PASIVO CORRIENTE", "detalle"),
    (
        "OtrosPasivosFinancierosCorriente",
        "Otros pasivos financieros",
        "PASIVO CORRIENTE",
        "detalle",
    ),
    (
        "CuentasYDocumentosPorPagarPorOperacionesCorriente",
        "Cuentas y documentos por pagar por operaciones",
        "PASIVO CORRIENTE",
        "detalle",
    ),
    (
        "RemuneracionesSociedadAdministradora",
        "Remuneraciones sociedad administradora",
        "PASIVO CORRIENTE",
        "detalle",
    ),
    (
        "OtrosDocumentosYCuentasPorPagarCorriente",
        "Otros documentos y cuentas por pagar",
        "PASIVO CORRIENTE",
        "detalle",
    ),
    (
        "IngresosAnticipadosCorriente",
        "Ingresos anticipados",
        "PASIVO CORRIENTE",
        "detalle",
    ),
    ("OtrosPasivosCorriente", "Otros pasivos", "PASIVO CORRIENTE", "detalle"),
    ("TotalPasivoCorriente", "Total pasivo corriente", "PASIVO CORRIENTE", "total"),
    ("PrestamosNoCorriente", "Préstamos", "PASIVO NO CORRIENTE", "detalle"),
    (
        "OtrosPasivosFinancierosNoCorriente",
        "Otros pasivos financieros",
        "PASIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "CuentasYDocumentosPorPagarPorOperacionesNoCorriente",
        "Cuentas y documentos por pagar por operaciones",
        "PASIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "OtrosDocumentosYCuentasPorPagarNoCorriente",
        "Otros documentos y cuentas por pagar",
        "PASIVO NO CORRIENTE",
        "detalle",
    ),
    (
        "IngresosAnticipadosNoCorriente",
        "Ingresos anticipados",
        "PASIVO NO CORRIENTE",
        "detalle",
    ),
    ("OtrosPasivosNoCorriente", "Otros pasivos", "PASIVO NO CORRIENTE", "detalle"),
    (
        "TotalPasivoNoCorriente",
        "Total pasivo no corriente",
        "PASIVO NO CORRIENTE",
        "total",
    ),
    ("AportesPatrimonioNeto", "Aportes", "PATRIMONIO NETO", "detalle"),
    ("OtrasReservas", "Otras reservas", "PATRIMONIO NETO", "detalle"),
    ("ResultadosAcumulados", "Resultados acumulados", "PATRIMONIO NETO", "detalle"),
    ("ResultadoDelEjercicio", "Resultado del ejercicio", "PATRIMONIO NETO", "detalle"),
    ("DividendosProvisorios", "Dividendos provisorios", "PATRIMONIO NETO", "detalle"),
    ("TotalPatrimonioNeto", "Total patrimonio neto", "PATRIMONIO NETO", "total"),
    (
        "TotalPasivo",
        "Total pasivo y patrimonio (TotalPasivo en la fuente)",
        "PASIVO Y PATRIMONIO",
        "total",
    ),
]
_RESULTADOS = [
    ("InteresesYReajustes", "Intereses y reajustes", "INGRESOS/PÉRDIDAS", "detalle"),
    (
        "IngresosPorDividendos",
        "Ingresos por dividendos",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "DiferenciasDeCambioNetasSobreActivosFinancierosACostoAmortizado",
        "Diferencias de cambio netas sobre activos financieros a costo amortizado",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "DiferenciasDeCambioNetasSobreEfectivoYEfectivoEquivalente",
        "Diferencias de cambio netas sobre efectivo y efectivo equivalente",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "CambiosNetosEnValorRazonableDeActivosFinancierosYPasivosFinancierosAValorRazonableConEfectoEnResultados",
        "Cambios netos en valor razonable de activos y pasivos financieros con efecto en resultados",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "ResultadoEnVentaDeInstrumentosFinancieros",
        "Resultado en venta de instrumentos financieros",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "ResultadosPorVentaDeInmuebles",
        "Resultados por venta de inmuebles",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "IngresoPorArriendoDeBienesRaices",
        "Ingreso por arriendo de bienes raíces",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "VariacionesEnValorRazonableDePropiedadesDeInversion",
        "Variaciones en valor razonable de propiedades de inversión",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "ResultadoEnInversionesValorizadasPorElMetodoDeLaParticipacion",
        "Resultado en inversiones valorizadas por el método de la participación",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "OtrosIngresosPerdidasDeLaOperacion",
        "Otros ingresos/(pérdidas) de la operación",
        "INGRESOS/PÉRDIDAS",
        "detalle",
    ),
    (
        "TotalIngresosPerdidasNetosDeLaOperacion",
        "Total ingresos/(pérdidas) netos de la operación",
        "INGRESOS/PÉRDIDAS",
        "total",
    ),
    ("DepreciacionesGastos", "Depreciaciones", "GASTOS", "detalle"),
    (
        "RemuneracionDelComiteDeVigilancia",
        "Remuneración del comité de vigilancia",
        "GASTOS",
        "detalle",
    ),
    ("ComisionDeAdministracion", "Comisión de administración", "GASTOS", "detalle"),
    (
        "HonorariosPorCustodiaYAdmistracion",
        "Honorarios por custodia y administración",
        "GASTOS",
        "detalle",
    ),
    ("CostosDeTransaccion", "Costos de transacción", "GASTOS", "detalle"),
    ("OtrosGastosDeOperacion", "Otros gastos de operación", "GASTOS", "detalle"),
    ("TotalGastosDeOperacion", "Total gastos de operación", "GASTOS", "total"),
    (
        "UtilidadPerdidaDeLaOperacion",
        "Utilidad/(pérdida) de la operación",
        "RESULTADO",
        "total",
    ),
    ("CostosFinancieros", "Costos financieros", "RESULTADO", "detalle"),
    (
        "UtilidadPerdidaAntesDeImpuesto",
        "Utilidad/(pérdida) antes de impuesto",
        "RESULTADO",
        "total",
    ),
    (
        "ImpuestoALasGananciasPorInversionesEnElExterior",
        "Impuesto a las ganancias por inversiones en el exterior",
        "RESULTADO",
        "detalle",
    ),
    ("ResultadoDelEjercicio", "Resultado del ejercicio", "RESULTADO", "total"),
    (
        "CoberturaDeFlujoDeCaja",
        "Cobertura de flujo de caja",
        "OTROS RESULTADOS INTEGRALES",
        "detalle",
    ),
    (
        "AjustesPorConversion",
        "Ajustes por conversión",
        "OTROS RESULTADOS INTEGRALES",
        "detalle",
    ),
    (
        "AjustesProvenientesDeInversionesValorizadasPorElMetodoDeLaParticipacion",
        "Ajustes provenientes de inversiones valorizadas por el método de la participación",
        "OTROS RESULTADOS INTEGRALES",
        "detalle",
    ),
    (
        "OtrosAjustesAlPatrimonioNeto",
        "Otros ajustes al patrimonio neto",
        "OTROS RESULTADOS INTEGRALES",
        "detalle",
    ),
    (
        "TotalDeOtrosResultadosIntegrales",
        "Total de otros resultados integrales",
        "OTROS RESULTADOS INTEGRALES",
        "total",
    ),
    (
        "TotalResultadoIntegral",
        "Total resultado integral",
        "RESULTADO INTEGRAL",
        "total",
    ),
]
CATALOGO = {
    t: [(i, *fila) for i, fila in enumerate(fs, 1)]
    for t, fs in (("balance", _BALANCE), ("resultados", _RESULTADOS))
}
CODIGOS_TABLA = {t: {c[1] for c in filas} for t, filas in CATALOGO.items()}
CODIGOS = set.union(*CODIGOS_TABLA.values())
CONTEXTOS_TABLA = {
    "balance": ("PeriodoActual", "PeriodoAnualAnterior", "SaldoInicialTerceraColumna"),
    "resultados": (
        "PeriodoActual",
        "PeriodoAnterior",
        "TrimestreActual",
        "TrimestreAnterior",
    ),
}
CONTEXTOS = tuple(dict.fromkeys(c for cs in CONTEXTOS_TABLA.values() for c in cs))
MONEDAS = {
    "$$": "CLP",
    "PROM": "USD",
    "EUR": "EUR",
    "COP": "COP",
    "CLP": "CLP",
    "USD": "USD",
}
MAX_XML = 10_000_000
VERSION_PARSER = 1
TOL_ABS = 2


class ErrorFuente(ValueError):
    """Contenido completo pero no publicable: identidad, esquema, moneda o contabilidad."""


class ErrorTransitorio(ValueError):
    """Desafío, error HTTP o respuesta incompleta; nunca equivale a sin información."""


def decodificar(raw: bytes | str) -> str:
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def leer_xml(raw: bytes) -> ET.Element:
    if not raw or len(raw) > MAX_XML:
        raise ErrorTransitorio("XML vacío o mayor del límite de 10 MB")
    texto = re.sub(r"^\s*<\?xml[^>]*\?>", "", decodificar(raw))
    if "<!DOCTYPE" in texto.upper() or "<!ENTITY" in texto.upper():
        raise ErrorFuente("no se admiten DTD ni entidades en el XML")
    if "<IFRS" not in texto[:4000] or not texto.rstrip().endswith("</IFRS>"):
        raise ErrorTransitorio("la respuesta no es un XML IFRS completo")
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError as e:
        raise ErrorFuente(f"XML mal formado: {e}") from e
    if raiz.tag != "IFRS":
        raise ErrorFuente("raíz distinta de IFRS")
    return raiz


def fin_periodo(periodo: str) -> date:
    if not re.fullmatch(r"\d{4}-(03|06|09|12)", periodo):
        raise ErrorFuente(f"cierre trimestral inválido {periodo!r}")
    y, m = map(int, periodo.split("-"))
    return date(y, m, calendar.monthrange(y, m)[1])


def _texto(raiz, ruta):
    return " ".join((raiz.findtext(ruta) or "").split())


def entero(txt: str | None, codigo: str) -> int:
    token = (txt or "").strip()
    if not re.fullmatch(r"[+-]?\d+(?:[.,]0+)?", token):
        raise ErrorFuente(f"{codigo}: importe no entero {token!r}")
    n = int(re.split(r"[.,]", token)[0])
    if not -(2**63) <= n < 2**63:
        raise ErrorFuente(f"{codigo}: importe fuera de int64")
    return n


def _fechas(raiz, periodo):
    fin = fin_periodo(periodo)
    nodo = raiz.find("Contextos")
    if nodo is None:
        raise ErrorFuente("faltan Contextos")
    out = {}
    for c in nodo:
        if c.tag not in CONTEXTOS:
            continue
        if c.tag in out:
            raise ErrorFuente(f"contexto duplicado: {c.tag}")
        try:
            inicio = date.fromisoformat(_texto(c, "FechaInicio"))
            # El saldo de apertura es un instante; el formato oficial solo trae FechaInicio.
            termino_txt = _texto(c, "FechaTermino")
            termino = (
                inicio
                if c.tag == "SaldoInicialTerceraColumna" and not termino_txt
                else date.fromisoformat(termino_txt)
            )
        except ValueError as e:
            raise ErrorFuente(f"fechas inválidas en {c.tag}") from e
        if c.tag == "SaldoInicialTerceraColumna":
            if not inicio <= termino < date(fin.year, 1, 1):
                raise ErrorFuente("fecha del balance de apertura incoherente")
        else:
            anio = (
                fin.year
                if c.tag in ("PeriodoActual", "TrimestreActual")
                else fin.year - 1
            )
            mes = 12 if c.tag == "PeriodoAnualAnterior" else fin.month
            esperado = date(anio, mes, calendar.monthrange(anio, mes)[1])
            minimo = (
                date(anio, mes - 2, 1)
                if c.tag.startswith("Trimestre")
                else date(anio, 1, 1)
            )
            if termino != esperado or not minimo <= inicio <= termino:
                raise ErrorFuente(
                    f"{c.tag}: fechas {inicio}..{termino} incoherentes con {periodo}"
                )
        out[c.tag] = {"inicio": inicio.isoformat(), "termino": termino.isoformat()}
    if "PeriodoActual" not in out:
        raise ErrorFuente("falta el contexto PeriodoActual")
    return out


def verificar_cuentas(
    tabla: str, cuentas: dict, tol_abs: int = TOL_ABS
) -> tuple[int, list[str]]:
    """Todas las reglas de una tabla/contexto, incluyendo completitud; no verifica reglas vacías."""
    faltan = sorted(CODIGOS_TABLA[tabla] - cuentas.keys())
    if faltan:
        return 0, [f"faltan {len(faltan)} cuentas: {', '.join(faltan[:5])}"]
    if any(type(cuentas[k]) is not int for k in CODIGOS_TABLA[tabla]):
        return 0, ["cuentas sin entero exacto"]
    malos, n = [], 0

    def check(regla, obtenido, esperado):
        nonlocal n
        n += 1
        delta = obtenido - esperado
        if abs(delta) > max(tol_abs, abs(esperado) * 1e-6):
            malos.append(f"{regla} (Δ {delta})")

    def sumar(seccion):
        return sum(
            cuentas[cod]
            for _, cod, _, sec, tipo in CATALOGO[tabla]
            if sec == seccion and tipo == "detalle"
        )

    if tabla == "balance":
        for sec, total in (
            ("ACTIVO CORRIENTE", "TotalActivoCorriente"),
            ("ACTIVO NO CORRIENTE", "TotalActivoNoCorriente"),
            ("PASIVO CORRIENTE", "TotalPasivoCorriente"),
            ("PASIVO NO CORRIENTE", "TotalPasivoNoCorriente"),
            ("PATRIMONIO NETO", "TotalPatrimonioNeto"),
        ):
            check(f"Σ {sec.lower()} = {total}", sumar(sec), cuentas[total])
        check(
            "activo corriente + no corriente = activo",
            cuentas["TotalActivoCorriente"] + cuentas["TotalActivoNoCorriente"],
            cuentas["TotalActivo"],
        )
        check(
            "pasivo corriente + no corriente + patrimonio = TotalPasivo",
            cuentas["TotalPasivoCorriente"]
            + cuentas["TotalPasivoNoCorriente"]
            + cuentas["TotalPatrimonioNeto"],
            cuentas["TotalPasivo"],
        )
        check(
            "activo = pasivo y patrimonio",
            cuentas["TotalActivo"],
            cuentas["TotalPasivo"],
        )
    else:
        check(
            "Σ ingresos = total ingresos",
            sumar("INGRESOS/PÉRDIDAS"),
            cuentas["TotalIngresosPerdidasNetosDeLaOperacion"],
        )
        check(
            "Σ gastos = total gastos",
            sumar("GASTOS"),
            cuentas["TotalGastosDeOperacion"],
        )
        check(
            "ingresos + gastos = utilidad de operación",
            cuentas["TotalIngresosPerdidasNetosDeLaOperacion"]
            + cuentas["TotalGastosDeOperacion"],
            cuentas["UtilidadPerdidaDeLaOperacion"],
        )
        check(
            "operación + costos financieros = utilidad antes de impuesto",
            cuentas["UtilidadPerdidaDeLaOperacion"] + cuentas["CostosFinancieros"],
            cuentas["UtilidadPerdidaAntesDeImpuesto"],
        )
        check(
            "antes de impuesto + impuestos = resultado",
            cuentas["UtilidadPerdidaAntesDeImpuesto"]
            + cuentas["ImpuestoALasGananciasPorInversionesEnElExterior"],
            cuentas["ResultadoDelEjercicio"],
        )
        check(
            "Σ otros integrales = total otros integrales",
            sumar("OTROS RESULTADOS INTEGRALES"),
            cuentas["TotalDeOtrosResultadosIntegrales"],
        )
        check(
            "resultado + otros integrales = resultado integral",
            cuentas["ResultadoDelEjercicio"]
            + cuentas["TotalDeOtrosResultadosIntegrales"],
            cuentas["TotalResultadoIntegral"],
        )
    return n, malos


def extraer(
    raw: bytes, run: str, periodo: str, estricto_comparativos: bool = False
) -> dict:
    """Valida identidad, fechas y TODAS las tablas/contextos presentes antes de devolver cifras.

    Un comparativo ausente se declara sin_cuentas. Uno parcial o descuadrado queda
    rechazado y NO aporta filas; nunca se rellena con ceros. El actual (incluido
    TrimestreActual si viene) siempre es fail-closed. La política estricta opcional
    rechaza también todo el documento si falla un comparativo.
    """
    raiz = leer_xml(raw)
    fin_periodo(periodo)
    if not re.fullmatch(r"\d+", run):
        raise ErrorFuente("RUN solicitado inválido")
    run_xml = _texto(raiz, "Identificacion/RUTFondoInforma").replace(".", "")
    if run_xml != run:
        raise ErrorFuente(f"XML de fondo {run_xml!r}, no del {run}")
    declarado = (
        _texto(raiz, "DatosPeriodo/PeriodoPresentacionEstadosFinancieros/Anio")
        + "-"
        + _texto(raiz, "DatosPeriodo/PeriodoPresentacionEstadosFinancieros/Mes").zfill(
            2
        )
    )
    if declarado != periodo:
        raise ErrorFuente(f"XML de {declarado}, no de {periodo}")
    for campo in ("EstadoSituacionFinanciera", "EstadoResultadosIntegrales"):
        if _texto(raiz, f"DatosPeriodo/{campo}") != "S":
            raise ErrorFuente(f"el XML no declara {campo} presente")
    moneda_cmf = _texto(raiz, "DatosPeriodo/MonedaPresentacionEstadosFinancieros")
    moneda = MONEDAS.get(moneda_cmf)
    if not moneda:
        raise ErrorFuente(f"moneda desconocida {moneda_cmf!r}")
    fechas = _fechas(raiz, periodo)
    crudo = {c: {} for c in CONTEXTOS}
    notas, duplicadas = {}, 0
    for cuenta in raiz.findall("Cuenta"):
        if cuenta.get("Serie"):
            continue
        ctx, codigo = cuenta.get("Context"), (cuenta.get("CodigoCuenta") or "").strip()
        if ctx not in crudo or codigo not in CODIGOS:
            continue
        if ctx not in fechas:
            raise ErrorFuente(f"cuenta en contexto no declarado: {ctx}")
        valor = entero(cuenta.text, codigo)
        if codigo in crudo[ctx]:
            if crudo[ctx][codigo] != valor:
                raise ErrorFuente(f"{ctx}/{codigo}: repetido con valores distintos")
            duplicadas += 1
        else:
            crudo[ctx][codigo] = valor
        nota = (cuenta.get("Nota") or "").strip()
        if nota:
            notas.setdefault(ctx, {})[codigo] = nota
    tablas, validacion = {}, {}
    for tabla, contextos in CONTEXTOS_TABLA.items():
        tablas[tabla], validacion[tabla] = {}, {}
        for ctx in contextos:
            c = {k: v for k, v in crudo[ctx].items() if k in CODIGOS_TABLA[tabla]}
            if not c and ctx != "PeriodoActual":
                validacion[tabla][ctx] = {"estado": "sin_cuentas", "reglas": 0}
                continue
            n, malos = verificar_cuentas(tabla, c)
            if malos:
                if ctx in ("PeriodoActual", "TrimestreActual") or estricto_comparativos:
                    raise ErrorFuente(f"{tabla}/{ctx}: {'; '.join(malos[:5])}")
                validacion[tabla][ctx] = {
                    "estado": "rechazado",
                    "reglas": n,
                    "errores": malos,
                }
                continue
            tablas[tabla][ctx] = c
            validacion[tabla][ctx] = {"estado": "validado", "reglas": n}
    dv_xml = _texto(raiz, "Identificacion/DVFondoInforma").upper()
    avisos = []
    if dv_xml != dv(run):
        avisos.append(
            f"DV del XML {dv_xml!r} distinto de {dv(run)}; se conserva en dv_fondo_fuente"
        )
    rut_agf = _texto(raiz, "Identificacion/RUTAdministradora").replace(".", "")
    if not rut_agf.isdigit():
        raise ErrorFuente("falta RUT válido de administradora")
    return {
        "run": run,
        "periodo": periodo,
        "nombre": _texto(raiz, "Identificacion/NombreEntidadInforma"),
        "rut_agf": rut_agf,
        "agf": _texto(raiz, "Identificacion/NombreAdministradoraInforma"),
        "dv_fondo_fuente": dv_xml,
        "moneda": moneda,
        "moneda_cmf": moneda_cmf,
        "contextos": fechas,
        "tablas": tablas,
        "notas": notas,
        "validacion": validacion,
        "duplicadas": duplicadas,
        "avisos": avisos,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "version_parser": VERSION_PARSER,
    }


ARCHIVO_RE = re.compile(r"FIEF[A-Za-z0-9_-]+\.xml\Z")
ENVIO_RE = re.compile(r"_(\d{8})_(\d{6})_\d+\.xml\Z")


def enviado_de(archivo: str) -> str | None:
    m = ENVIO_RE.search(archivo)
    if not m:
        return None
    try:
        return datetime.strptime("".join(m.groups()), "%Y%m%d%H%M%S").isoformat()  # noqa: DTZ007 - hora fuente, sin adivinar huso
    except ValueError:
        return None


class _Ficha(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.archivos, self.textos = [], []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        partes = urlsplit(dict(attrs).get("href") or "")
        if partes.hostname and partes.hostname.lower() not in (
            "www.cmfchile.cl",
            "cmfchile.cl",
            "www.svs.cl",
        ):
            return
        if not partes.path.endswith("ifrs_xml_verarchivo.php"):
            return
        for a in parse_qs(partes.query).get("archivo", []):
            if ARCHIVO_RE.fullmatch(a):
                self.archivos.append(a)

    def handle_data(self, data):
        self.textos.append(data)


def clasificar_ficha(raw: bytes, periodo: str | None = None) -> tuple[str, str | None]:
    p = _Ficha()
    try:
        p.feed(decodificar(raw))
    except Exception as e:
        raise ErrorTransitorio("ficha ilegible") from e
    if p.archivos:
        archivo = max(set(p.archivos), key=lambda a: (enviado_de(a) or "", a))
        return "xml", archivo
    texto = html.unescape(" ".join(p.textos)).lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    texto = " ".join(texto.split())
    ausencia_fechada = re.search(
        r"no existe informacion de la entidad para el periodo (\d{4})/(03|06|09|12)\b",
        texto,
    )
    if ausencia_fechada:
        cierre = "-".join(ausencia_fechada.groups())
        if periodo is not None and cierre != periodo:
            raise ErrorTransitorio(
                f"la ausencia declarada es de {cierre}, no de {periodo}"
            )
        return "sin_informacion", None
    if "no existe informacion de la entidad para el periodo senalado" in texto:
        return "sin_informacion", None
    if "informacion financiera" in texto:
        return "sin_enlace", None
    raise ErrorTransitorio("la respuesta no es la ficha FI (posible desafío CMF)")


COLUMNAS = (
    "periodo",
    "run_fondo",
    "run_fondo_dv",
    "dv_fondo_fuente",
    "nombre_fondo",
    "tipo_entidad",
    "rut_agf",
    "razon_social_agf",
    "moneda",
    "moneda_cmf",
    "contexto",
    "fecha_inicio_contexto",
    "fecha_fin_contexto",
    "tipo_periodo",
    "seccion",
    "tipo_linea",
    "orden",
    "codigo_cuenta",
    "cuenta",
    "nota",
    "valor_miles_mf",
    "fuente_archivo",
    "enviado_cmf",
    "sha256_archivo",
    "cotejo_ficha",
)


def filas(reg: dict) -> dict[str, list[dict]]:
    out = {t: [] for t in CATALOGO}
    for tabla, contextos in reg["tablas"].items():
        for ctx, cuentas in contextos.items():
            fechas = reg["contextos"][ctx]
            for orden, codigo, glosa, seccion, tipo in CATALOGO[tabla]:
                if codigo not in cuentas:
                    raise ErrorFuente(f"registro incompleto {tabla}/{ctx}/{codigo}")
                out[tabla].append(
                    {
                        "periodo": reg["periodo"],
                        "run_fondo": reg["run"],
                        "run_fondo_dv": f"{reg['run']}-{dv(reg['run'])}",
                        "dv_fondo_fuente": reg["dv_fondo_fuente"],
                        "nombre_fondo": reg["nombre"],
                        "tipo_entidad": reg["tipo_entidad"],
                        "rut_agf": reg["rut_agf"],
                        "razon_social_agf": reg["agf"],
                        "moneda": reg["moneda"],
                        "moneda_cmf": reg["moneda_cmf"],
                        "contexto": ctx,
                        "fecha_inicio_contexto": fechas["inicio"],
                        "fecha_fin_contexto": fechas["termino"],
                        "tipo_periodo": "saldo"
                        if tabla == "balance"
                        else "trimestre"
                        if ctx.startswith("Trimestre")
                        else "acumulado",
                        "seccion": seccion,
                        "tipo_linea": tipo,
                        "orden": orden,
                        "codigo_cuenta": codigo,
                        "cuenta": glosa,
                        "nota": reg["notas"].get(ctx, {}).get(codigo),
                        "valor_miles_mf": cuentas[codigo],
                        "fuente_archivo": reg["archivo"],
                        "enviado_cmf": reg.get("enviado"),
                        "sha256_archivo": reg["sha256"],
                        "cotejo_ficha": "coincide"
                        if reg.get("cotejo", {})
                        .get("cuentas", {})
                        .get(tabla, {})
                        .get(ctx)
                        == len(cuentas)
                        else "sin_columna",
                    }
                )
    return out

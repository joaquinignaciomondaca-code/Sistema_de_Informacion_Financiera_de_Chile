"""XML y fichas sintéticos con la forma —y los valores— reales de la CMF.

Los importes son los del fondo 8011-K (cierre 2025 y comparativo 2024), cotejados contra la ficha de la CMF;
`factor` los escala por un entero, así las identidades contables se mantienen para fondos «distintos».
El XML real lista las cuentas en orden alfabético y mezcla estados con y sin serie; aquí también.
"""
from __future__ import annotations

AUMENTO_ANTES = ("AumentoDisminucionDeActivoNetoAtribuibleAParticipesOriginadasPorActividadesDeLaOperacion"
                 "AntesDeDistribucionDeBeneficios")
AUMENTO_DESPUES = ("AumentoDisminucionDeActivoNetoAtribuibleAParticipesOriginadasPorActividadesDeLaOperacion"
                   "DespuesDeDistribucionDeBeneficios")

ESF_2025 = {
    "EfectivoYEfectivoEquivalente": 116573, "ActivosFinancierosAValorRazonableConEfectoEnResultados": 0,
    "ActivosFinancierosAValorRazonableConEfectoEnResultadosEntregadosEnGarantia": 0,
    "ActivosFinancierosACostoAmortizado": 192755620, "CuentasPorCobrarAIntermediarios": 0,
    "OtrasCuentasPorCobrar": 0, "OtrosActivos": 7, "TotalActivo": 192872200,
    "PasivosFinancierosAValorRazonableConEfectoEnResultados": 0, "CuentasPorAPagarIntermediarios": 0,
    "RescatesPorPagar": 0, "RemuneracionesSociedadAdministradora": 12234, "OtrosDocumentosYCuentasPorPagar": 14691,
    "OtrosPasivos": 0, "TotalPasivo": 26925, "ActivoNetoAtribuibleALosParticipes": 192845275,
}
ESF_2024 = {**ESF_2025, "EfectivoYEfectivoEquivalente": 650421, "ActivosFinancierosACostoAmortizado": 251319861,
            "OtrosActivos": 0, "TotalActivo": 251970282, "RescatesPorPagar": 29572,
            "RemuneracionesSociedadAdministradora": 15814, "OtrosDocumentosYCuentasPorPagar": 12562,
            "TotalPasivo": 57948, "ActivoNetoAtribuibleALosParticipes": 251912334}
ERI_2025 = {
    "InteresesYReajustes": 11317039, "IngresosPorDividendos": 0,
    "DiferenciasDeCambioNetasSobreActivosFinancierosACostoAmortizado": 0,
    "DiferenciasDeCambioNetasSobreEfectivoYEfectivoEquivalente": 0,
    "CambiosNetosEnValorRazonableDeActivosYPasivosFinancierosAValorRazonableConEfectoEnResultados": -3823,
    "ResultadoEnVentaDeInstrumentosFinancieros": -20255, "OtrosEri": 73,
    "TotalIngresosPerdidasNetosDeLaOperacion": 11293034, "ComisionDeAdministracion": -2552317,
    "HonorariosPorCustodiaYAdministracion": 0, "CostosDeTransaccion": 0, "OtrosGastosDeOperacion": -50997,
    "TotalGastosDeOperacion": -2603314, "UtilidadPerdidaDeLaOperacionAntesDeImpuesto": 8689720,
    "ImpuestosALasGananciasPorInversionesEnElExterior": 0, "UtilidadPerdidaDeLaOperacionDespuesDeImpuesto": 8689720,
    AUMENTO_ANTES: 8689720, "DistribucionDeBeneficios": 0, AUMENTO_DESPUES: 8689720,
}
ERI_2024 = {**ERI_2025, "InteresesYReajustes": 18212619,
            "CambiosNetosEnValorRazonableDeActivosYPasivosFinancierosAValorRazonableConEfectoEnResultados": 2818,
            "ResultadoEnVentaDeInstrumentosFinancieros": 5371, "OtrosEri": -224,
            "TotalIngresosPerdidasNetosDeLaOperacion": 18220584, "ComisionDeAdministracion": -3206224,
            "OtrosGastosDeOperacion": -42479, "TotalGastosDeOperacion": -3248703,
            "UtilidadPerdidaDeLaOperacionAntesDeImpuesto": 14971881,
            "UtilidadPerdidaDeLaOperacionDespuesDeImpuesto": 14971881,
            AUMENTO_ANTES: 14971881, AUMENTO_DESPUES: 14971881}
NOTAS_2025 = {"EfectivoYEfectivoEquivalente": "6", "ActivosFinancierosACostoAmortizado": "7",
              "RemuneracionesSociedadAdministradora": "8", "InteresesYReajustes": "7",
              "CambiosNetosEnValorRazonableDeActivosYPasivosFinancierosAValorRazonableConEfectoEnResultados": "12",
              "ResultadoEnVentaDeInstrumentosFinancieros": "13", "ComisionDeAdministracion": "8"}

AUDITOR = "Ernst & Young Auditoría y Asesorías Ltda."
AGF_RUT, AGF_NOMBRE = "91999000", "Principal Administradora General de Fondos"


def dv(cuerpo: str) -> str:
    s, m = 0, 2
    for c in reversed(cuerpo):
        s += int(c) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def nombre_archivo(run: str, anio: int, version: int = 0) -> str:
    """`FMEF<año de envío><correlativo>_<aaaammdd>_<hhmmss>_<run>.xml`; `version` simula un reenvío."""
    return f"FMEF{anio + 1}{811894 + int(run) % 1000}_{anio + 1}0330_{110924 + version * 100:06d}_{run}.xml"


def _cuentas(ctx: str, valores: dict, factor: int, notas: dict | None, omitir, con_espacio) -> str:
    out = []
    for cod in sorted(valores):                    # el XML real va en orden alfabético
        if cod in omitir:
            continue
        nota = f' Nota="{notas[cod]}"' if notas and cod in notas else ""
        etiqueta = cod + " " if cod in con_espacio else cod
        out.append(f'  <Cuenta CodigoCuenta="{etiqueta}" Context="{ctx}"{nota}>{valores[cod] * factor}</Cuenta>\n')
    return "".join(out)


def xml(run: str = "8011", anio: int = 2025, moneda: str = "$$", factor: int = 1, declaracion: str | None = "iso-8859-1",
        codificacion: str = "latin-1", sin_anterior: bool = False, omitir=(), con_espacio=(), extra: str = "",
        sobrescribir: dict | None = None, mes: str = "12", run_xml: str | None = None, dv_xml: str | None = None,
        anterior_distinto: dict | None = None, alias_otros: bool = False, nombre: str = "FONDO MUTUO DE PRUEBA",
        bom: bool = False) -> bytes:
    """XML IFRS de un fondo. `sobrescribir` cambia importes del ejercicio actual (para forzar descuadres)."""
    actual = {**ESF_2025, **ERI_2025, **(sobrescribir or {})}
    anterior = {**ESF_2024, **ERI_2024, **(anterior_distinto or {})}
    if alias_otros:                                  # el modelo antiguo: «Otros» en lugar de «OtrosEri»
        actual["Otros"] = actual.pop("OtrosEri")
        anterior["Otros"] = anterior.pop("OtrosEri")
    decl = f'<?xml version="1.0" encoding="{declaracion}"?>\n' if declaracion else ""
    d_v = dv_xml if dv_xml is not None else dv(run)
    cab = (f"{decl}<!-- Generado por DBNeT GX  3.9.5 -  http://www.dbnet.cl -->\n<IFRS>\n"
           f"  <Identificacion>\n    <RUTFondoInforma>{run_xml or run}</RUTFondoInforma>\n"
           f"    <DVFondoInforma>{d_v}</DVFondoInforma>\n    <NombreEntidadInforma>{nombre}</NombreEntidadInforma>\n"
           f"    <RUTAdministradora>{AGF_RUT}</RUTAdministradora>\n    <DVAdministradora>7</DVAdministradora>\n"
           f"    <NombreAdministradoraInforma>{AGF_NOMBRE}</NombreAdministradoraInforma>\n  </Identificacion>\n"
           f"  <DatosPeriodo>\n    <MonedaPresentacionEstadosFinancieros>{moneda}</MonedaPresentacionEstadosFinancieros>\n"
           f"    <PeriodoPresentacionEstadosFinancieros>\n      <Mes>{mes}</Mes>\n      <Anio>{anio}</Anio>\n"
           f"    </PeriodoPresentacionEstadosFinancieros>\n    <NumUltimaNotaInformada>24</NumUltimaNotaInformada>\n"
           f"    <NombreAuditoresExternos>{AUDITOR.replace('&', '&amp;')}</NombreAuditoresExternos>\n"
           f"    <EstadoSituacionFinanciera>S</EstadoSituacionFinanciera>\n"
           f"    <EstadoResultadosIntegrales>S</EstadoResultadosIntegrales>\n  </DatosPeriodo>\n"
           f"  <Contextos>\n    <PeriodoActual><FechaInicio>{anio}-01-01</FechaInicio><FechaTermino>{anio}-12-31</FechaTermino></PeriodoActual>\n"
           f"    <PeriodoAnterior><FechaInicio>{anio - 1}-01-01</FechaInicio><FechaTermino>{anio - 1}-12-31</FechaTermino></PeriodoAnterior>\n"
           f"  </Contextos>\n")
    # Cuentas del estado de cambios del activo neto (con serie) y del flujo (con «Otros»): deben ignorarse.
    ajenas = ('  <Cuenta CodigoCuenta="RescateDeCuotasPorSerie" Context="PeriodoActual" Serie="B">-5651077</Cuenta>\n'
              '  <Cuenta CodigoCuenta="TotalActivo" Context="PeriodoActual" Serie="B">999999</Cuenta>\n'
              '  <Cuenta CodigoCuenta="Otros" Context="PeriodoActual">424242</Cuenta>\n' if not alias_otros else "")
    cuerpo = ajenas + _cuentas("PeriodoActual", actual, factor, NOTAS_2025 if anio == 2025 else None, omitir, con_espacio)
    if not sin_anterior:
        cuerpo += _cuentas("PeriodoAnterior", anterior, factor, None, omitir, con_espacio)
    texto = cab + cuerpo + extra + "</IFRS>\n"
    datos = texto.encode(codificacion)
    return (b"\xef\xbb\xbf" if bom else b"") + datos


def ficha(run: str, anio: int, estado: str = "xml", archivo: str | None = None, extras: tuple[str, ...] = (),
          codificacion: str = "utf-8") -> bytes:
    """HTML de la ficha de un fondo para un cierre: 'xml', 'sin_informacion', 'sin_enlace' o 'desafio'."""
    if estado == "desafio":      # la página JavaScript ofuscada que la CMF sirve a veces; sin menú ni texto
        return ("<html><script>eval(function(p,a,c,k,e,d){return p}('1B 13=\"a+/=\";V s(12){1B 18=\"\"}',62,5,''))"
                "</script></html>").encode()
    menu = ('<ul><li><a href="entidad.php?pestania=1">Identificación</a></li>'
            '<li><a href="entidad.php?pestania=3">Información Financiera</a></li></ul>')
    cuerpo = f"<html><body>{menu}<h2>INFORMACION FINANCIERA BAJO ESTANDAR IFRS</h2>"
    if estado == "sin_informacion":
        cuerpo += "<p>No existe información de la entidad para el periodo señalado.</p>"
    elif estado == "xml":
        for a in (archivo or nombre_archivo(run, anio),) + tuple(extras):
            cuerpo += (f'<a href="https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php'
                       f'?archivo={a}&amp;&amp;rut={run}&amp;&amp;periodo={anio}12&amp;&amp;path=/web/ifrs_xml/fmifr/xml/'
                       f'&amp;&amp;desc_archivo=Estados_financieros_">DESCARGAR ARCHIVO XML</a>')
    cuerpo += "</body></html>"
    return cuerpo.encode(codificacion)

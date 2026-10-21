"""Inventario de campos de la Circular 1835 (seguros) derivado de las fichas técnicas.

La CMF publica las fichas (``seguros/fuentes/fichas_tecnicas_1835/``) con el nombre,
la descripción y el PICTURE de cada campo.  ``ficha_1835.py`` las convierte en
posiciones; este módulo decide qué se publica y con qué nombre:

  - el nombre publicado es el de la ficha, en minúsculas y sin acentos;
  - se repara el nombre cuando la ficha lo partió a media palabra
    (``PARTICIPACION_PORC`` + ``ENTUAL`` -> ``PARTICIPACION_PORCENTUAL``);
  - se agrega el sufijo de la unidad declarada (``_m_clp``, ``_clp``, ``_uf``, ``_um``);
  - los nombres que la ficha repite dentro de un mismo registro se distinguen con un
    alias curado (dos RUT de deudor, activo objeto en unidades, etc.).

Uso::

    python -m seguros.scripts.inventario_1835 --escribir   # fuentes/inventario_1835.json
    python -m seguros.scripts.inventario_1835 --reporte    # resumen por tabla
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .ficha_1835 import FUENTES, FICHA, registros, unidad_del_texto

RUTA_JSON = Path(__file__).resolve().parent.parent / "fuentes" / "inventario_1835.json"

FORMATOS = ("v2016", "v2024")

# (letra, tipo de registro) -> (tabla publicada, subtipo)
DESTINO = {
    ("i", "2"): ("renta_fija", None),
    ("a", "2"): ("acciones", None),
    ("f", "2"): ("fondos_mutuos", None),
    ("b", "2"): ("bienes_raices", None),
    ("x", "2"): ("extranjeros", "deuda"),
    ("x", "3"): ("extranjeros", "acciones_y_fondos"),
    ("x", "4"): ("extranjeros", "bienes_raices"),
    ("x", "5"): ("extranjeros", "filiales"),
    ("c", "2"): ("control_inversiones", None),
    ("o", "2"): ("otras_inversiones", None),
    ("d", "2"): ("tablas_descriptores", None),
    ("t", "2"): ("tablas_desarrollo", None),
    ("e", "2"): ("flujos_activos_elegibles", None),
    ("r", "2"): ("prestamos", None),
    ("v", "2"): ("bienes_raices_arriendo_morosidad", None),
    ("g", "2"): ("garantias_derivados", None),
    ("p", "2"): ("derivados", "opcion"),
    ("p", "3"): ("derivados", "forward"),
    ("p", "4"): ("derivados", "futuro"),
    ("p", "5"): ("derivados", "swap"),
    ("p", "6"): ("pactos", None),
}

# Unidad declarada en la ficha -> sufijo del nombre publicado.
SUFIJO_UNIDAD = {"(M$)": "M_CLP", "($)": "CLP", "(UM)": "UM", "(US$)": "USD", "(UF)": "UF"}

# La ficha imprime el nombre en una columna angosta y a veces lo corta a media palabra;
# el trozo suelto queda en el renglón siguiente y el parser lo une con "_".
REPARAR = (
    (r"^PARTICIPACION_PORC_ENTUAL$", "PARTICIPACION_PORCENTUAL"),
    (r"^PORCENTAJE_PARTICI_PACION$", "PORCENTAJE_PARTICIPACION"),
    (r"^RESULTADO_DE_LA_S_OCIEDAD_FILIAL$", "RESULTADO_DE_LA_SOCIEDAD_FILIAL"),
    (r"^MODELO_PROPIO_DE_TERIORO$", "MODELO_PROPIO_DETERIORO"),
    (r"^MODELO_PROPIO_DET_ERIORO$", "MODELO_PROPIO_DETERIORO"),
    (r"^TOTAL_COSTO_AMOR_TIZADO$", "TOTAL_COSTO_AMORTIZADO"),
    (r"^TOTAL_VALOR_RAZON_ABLE$", "TOTAL_VALOR_RAZONABLE"),
    (r"^TOTAL_EFECTIVO_EQ_UIVALENTE$", "TOTAL_EFECTIVO_EQUIVALENTE"),
    (r"^TOTAL_INST_OTRAS_C_LASIF$", "TOTAL_INST_OTRAS_CLASIF"),
    (r"^CODIGO_ACTIVIDAD_E(?:_CONOMICA)?$", "CODIGO_ACTIVIDAD_ECONOMICA"),
    (r"^CLASIFICACION_DE_RI_ESGO_PAIS$", "CLASIFICACION_DE_RIESGO_PAIS"),
    (r"^COSTO_HISTORICO_C_ORREGIDO$", "COSTO_HISTORICO_CORREGIDO"),
    (r"^TOTAL_M2_CONSTRU_CCION$", "TOTAL_M2_CONSTRUCCION"),
    (r"^VALOR_TASACION_TE_RRENO_M2$", "VALOR_TASACION_TERRENO_M2"),
    (r"^VALOR_TASACION_CO_NSTRUCCION_M2$", "VALOR_TASACION_CONSTRUCCION_M2"),
    (r"^DIG_RUT_ACTIVO_OBJ_ETO$", "DIG_RUT_ACTIVO_OBJETO"),
    (r"^VALORIZACION_DE_PACTO_A_LA_FEC_HA_DE_CIERRE$", "VALORIZACION_DE_PACTO_A_LA_FECHA_DE_CIERRE"),
    (r"^TIPO_DOCUMENTACIO$", "TIPO_DOCUMENTACION"),
    (r"^DESARROLLO_AVANC$", "DESARROLLO_AVANCE"),
    (r"^TIR_SIN_COSTO_NCG$", "TIR_SIN_COSTO"),
    (r"^FECHA_INSCRIPCION_AAAAMMDD$", "FECHA_INSCRIPCION"),
    (r"^VERIFICADOR_DEUDO$", "VERIFICADOR_DEUDOR"),
    (r"^VALOR_RAZONABLE_D_EL_", "VALOR_RAZONABLE_DEL_"),
    # Los dos campos de relación deuda-garantía se cortaron en "OT"/"OR" y "PE"/"R";
    # la descripción distingue la fecha de otorgamiento de la de información.
    (r"^DEUDA_GARANTIA_OT(?:_.*)?$", "DEUDA_GARANTIA_OTORGAMIENTO"),
    (r"^DEUDA_GARANTIA_PE(?:_.*)?$", "DEUDA_GARANTIA_INFORMACION"),
    # "INVERSIONES_REPRESENTATIVAS_D_E_(RT_+_PR)" = de reservas técnicas + patrimonio de riesgo.
    (r"^INVERSIONES_(NO_)?REPRESENTATIVAS_D_E_RT_PR$", r"INVERSIONES_\1REPRESENTATIVAS_DE_RT_PR"),
)
_REPARAR = tuple((re.compile(p), r) for p, r in REPARAR)

# Registros donde el nombre en la ficha se repara además en ``nombre_ficha`` (los que todavía no
# tienen columnas publicadas): en el resto se conserva el texto tal como lo imprime el anexo.
REPARAR_NOMBRE_FICHA = {"o", "r", "v", "g"}

# El PDF 2024 corta/mezcla algunos encabezados de B.12–B.14 al extraer el texto. Estas
# correcciones se anclan a la posición fija del campo (no a una coincidencia ambigua de nombre)
# y reconstruyen el rótulo de la ficha según la misma tabla técnica.
NOMBRES_POSICION = {
    ("r", "2", 1): "CODIGO_PRESTAMO",
    ("r", "2", 10): "FECHA_PRESTAMO",
    ("r", "2", 20): "FECHA_VENCIMIENTO",
    ("r", "2", 30): "TIPO_DEUDOR",
    ("r", "2", 31): "CODIGO_ACTIVIDAD_ECONOMICA",
    ("r", "2", 37): "PRESTAMOS_TRABAJADORES",
    ("r", "2", 39): "CLASE_DEUDOR",
    ("r", "2", 40): "RUT_DEUDOR",
    ("r", "2", 49): "VER_DEUDOR",
    ("r", "2", 50): "RAZON_SOCIAL_DEUDOR",
    ("r", "2", 150): "NOMBRE_DEUDOR",
    ("r", "2", 230): "PRIMER_APELLIDO_DEUDOR",
    ("r", "2", 250): "SEGUNDO_APELLIDO_DEUDOR",
    ("r", "2", 270): "PENSIONADO",
    ("r", "2", 271): "DESCUENTO_PENSION",
    ("r", "2", 272): "MONTO_PENSION",
    ("r", "2", 280): "TIPO_PRESTAMO",
    ("r", "2", 282): "MONTO_ASEGURADO",
    ("r", "2", 291): "PRESTAMO_REPRESENTATIVO",
    ("r", "2", 292): "ORIGEN_PRESTAMO",
    ("r", "2", 293): "FECHA_ORIGINACION_O_RENEGOCIACION_ANTERIOR",
    ("r", "2", 303): "CODIGO_RENEGOCIADO_MAYOR_ORDEN",
    ("r", "2", 312): "CODIGO_RENEGOCIADO_SEGUNDO_ORDEN",
    ("r", "2", 321): "CODIGO_RENEGOCIADO_TERCER_ORDEN",
    ("r", "2", 330): "RUT_VENDEDORA_PRESTAMO",
    ("r", "2", 339): "VER_VENDEDORA_PRESTAMO",
    ("r", "2", 340): "CATEGORIA_RIESGO_VENDEDOR",
    ("r", "2", 343): "PORCENTAJE_PROVISION_VENDEDOR",
    ("r", "2", 347): "CATEGORIA_RIESGO_ADQUIRIDO",
    ("r", "2", 349): "PORCENTAJE_PROVISION_ADQUIRIDO",
    ("r", "2", 353): "CATEGORIA_RIESGO_OTORGADO",
    ("r", "2", 356): "PORCENTAJE_PROVISION_OTORGADO",
    ("r", "2", 361): "VENDEDORA_RELACIONADA",
    ("r", "2", 362): "CODIGO_PRESTAMO_ADQUIRIDO",
    ("r", "2", 377): "UNIDAD_REAJUSTE",
    ("r", "2", 383): "CUOTAS_IMPAGAS",
    ("r", "2", 400): "CUOTAS_IMPAGAS",
    ("r", "2", 413): "SALDO_INSOLUTO_DEUDA",
    ("r", "2", 430): "SALDO_INSOLUTO_DEUDA",
    ("r", "2", 443): "MONTO",
    ("r", "2", 458): "MONTO_PESOS",
    ("r", "2", 468): "CUOTA",
    ("r", "2", 483): "PERIODO_PAGO_CUOTA",
    ("r", "2", 485): "GARANTIAS",
    ("r", "2", 487): "PLAZO_PRESTAMO",
    ("r", "2", 490): "PLAZO_GRACIA",
    ("r", "2", 492): "TIPO_TASA",
    ("r", "2", 493): "TASA_FIJA_PACTADA",
    ("r", "2", 499): "TASA_FIJA_EFECTIVA",
    ("r", "2", 505): "TASA_VARIABLE_BASE",
    ("r", "2", 507): "SPREAD_TASA_VARIABLE",
    ("r", "2", 511): "VALOR_FINAL_B.12",
    ("r", "2", 521): "MONTO_PROVISION",
    ("r", "2", 531): "MODELO_DETERIORO",
    ("r", "2", 533): "MOROSIDAD",
    ("r", "2", 534): "TIPO_TASA_MORA",
    ("r", "2", 535): "TASA_MORA",
    ("r", "2", 541): "COMISION_PREPAGO",
    ("r", "2", 542): "OTRO_PREPAGO",
    ("r", "2", 592): "SEG_DESGRAVAMEN",
    ("r", "2", 593): "SEG_INVALIDEZ",
    ("r", "2", 594): "SEG_CESANTIA",
    ("r", "2", 595): "SEG_INCENDIO",
    ("r", "2", 596): "SEG_TERREMOTO",
    ("r", "2", 597): "SEG_OTRO_SEGURO",
    ("r", "2", 598): "RUT_ASEG_DESGRAVAMEN",
    ("r", "2", 607): "DV_ASEG_DESGRAVAMEN",
    ("r", "2", 608): "RUT_ASEG_INVALIDEZ",
    ("r", "2", 617): "DV_ASEG_INVALIDEZ",
    ("r", "2", 618): "RUT_ASEG_CESANTIA",
    ("r", "2", 627): "DV_ASEG_CESANTIA",
    ("r", "2", 628): "RUT_ASEG_INCENDIO",
    ("r", "2", 637): "DV_ASEG_INCENDIO",
    ("r", "2", 638): "RUT_ASEG_TERREMOTO",
    ("r", "2", 647): "DV_ASEG_TERREMOTO",
    ("r", "2", 648): "RUT_ASEG_OTRO",
    ("r", "2", 657): "DV_ASEG_OTRO",
    ("v", "2", 1): "TIPO_INSTRUMENTO",
    ("v", "2", 11): "ROL",
    ("v", "2", 22): "COMUNA",
    ("v", "2", 33): "NOMBRE_ARRENDATARIO_DEUDOR",
    ("v", "2", 93): "RUT_ARRENDATARIO_DEUDOR",
    ("v", "2", 102): "DV_ARRENDATARIO_DEUDOR",
    ("v", "2", 103): "CODIGO_ACTIVIDAD_ECONOMICA",
    ("v", "2", 109): "RELACION",
    ("v", "2", 111): "FECHA_VENCIMIENTO_CONTRATO",
    ("v", "2", 119): "CODIGO_IDENTIFICACION",
    ("v", "2", 149): "FACTURACION_MES",
    ("v", "2", 162): "RECAUDACION_MES_ACTUAL",
    ("v", "2", 175): "RECAUDACION_MESES_ANTERIORES",
    ("v", "2", 188): "RECAUDACION_MES_TOTAL",
    ("v", "2", 201): "MONTO_SIN_MOROSIDAD",
    ("v", "2", 213): "MOROSIDAD_MENOR_A_30_DIAS",
    ("v", "2", 225): "MOROSIDAD_ENTRE_30_Y_MENOR_A_60_DIAS",
    ("v", "2", 237): "MOROSIDAD_ENTRE_60_Y_MENOR_A_90_DIAS",
    ("v", "2", 249): "MOROSIDAD_ENTRE_90_Y_MENOR_A_180_DIAS",
    ("v", "2", 261): "MOROSIDAD_MAYOR_A_180_DIAS_Y_MENOR_A_1_ANO",
    ("v", "2", 273): "MOROSIDAD_MAYOR_A_1_ANO_Y_MENOR_A_2_ANOS",
    ("v", "2", 285): "MOROSIDAD_MAYOR_A_2_ANOS_Y_MENOR_A_3_ANOS",
    ("v", "2", 297): "MOROSIDAD_MAYOR_A_3_ANOS_Y_MENOR_A_4_ANOS",
    ("v", "2", 309): "MOROSIDAD_MAYOR_A_4_ANOS",
    ("v", "2", 321): "MOROSIDAD_TOTAL",
    ("v", "2", 333): "PROVISION_INCOBRABILIDAD",
    ("v", "2", 345): "TIPO_BIEN_RAIZ",
    ("v", "2", 357): "NUMERO_CUOTAS_VENCIDAS",
    ("v", "2", 361): "CARACTERISTICA_DE_REPROGRAMACION",
    ("v", "2", 364): "MONTO_TOTAL_REPROGRAMACION",
    ("v", "2", 376): "TOTAL_M2_DISPONIBLES_ARRIENDO",
    ("v", "2", 383): "TOTAL_M2_EN_ARRIENDO",
    ("v", "2", 390): "TOTAL_M2_NO_ARRENDADOS",
    ("v", "2", 397): "TIPO_CONTRATO",
    ("v", "2", 399): "VALOR_M2_ARRIENDO",
    ("v", "2", 406): "VALOR_M2_ESPERADO",
    ("v", "2", 413): "DEUDA_CAPITAL_INTERESES_DEVENGADOS",
    ("v", "2", 430): "DEUDA_CAPITAL_INTERESES_DEVENGADOS",
    ("g", "2", 1): "RUT_CONTRAPARTE_NACIONAL",
    ("g", "2", 10): "DV_CONTRAPARTE_NACIONAL",
    ("g", "2", 11): "LEI_CONTRAPARTE_EXTRANJERA",
    ("g", "2", 31): "NOMBRE_CONTRAPARTE_GARANTIA",
    ("g", "2", 131): "NACIONALIDAD_CONTRAPARTE_GARANTIA",
    ("g", "2", 133): "RELACIONADO",
    ("g", "2", 135): "POSICION_COMPANIA",
    ("g", "2", 137): "TIPO_GARANTIA",
    ("g", "2", 139): "IDENTIFICADOR_GARANTIA",
    ("g", "2", 153): "TIPO_ACTIVO_EN_GARANTIA",
    ("g", "2", 163): "FOLIO_INSTRUMENTO_EN_GARANTIA",
    ("g", "2", 173): "ITEM_INSTRUMENTO_EN_GARANTIA",
    ("g", "2", 176): "VALOR_NOMINAL_INSTRUMENTO_EN_GARANTIA",
    ("g", "2", 193): "CODIGO_IDENTIFICACION_INSTRUMENTO_EN_GARANTIA",
    ("g", "2", 223): "MONEDA_DENOMINACION_ACTIVO_EN_GARANTIA",
    ("g", "2", 229): "CLASIFICACION_DE_RIESGO_PAIS",
    ("g", "2", 233): "VALOR_CONTABLE_ACTIVO_EN_GARANTIA_UM",
    ("g", "2", 250): "VALOR_CONTABLE_ACTIVO_EN_GARANTIA",
    ("g", "2", 263): "VALOR_RAZONABLE_ACTIVO_EN_GARANTIA_UM",
    ("g", "2", 280): "VALOR_RAZONABLE_ACTIVO_EN_GARANTIA",
    ("g", "2", 293): "CUENTA_EEFF_DE_REGISTRO_DE_LA_GARANTIA",
}

# Etiquetas literales de la ficha que incluyen unidad en el propio CAMPO; el identificador
# técnico de Parquet deriva la unidad al sufijo, pero el diccionario debe mostrar el rótulo CMF.
NOMBRES_FICHA_POSICION = {
    ("g", "2", 250): "VALOR_CONTABLE_ACTIVO_EN_GARANTIA_M$",
    ("g", "2", 280): "VALOR_RAZONABLE_ACTIVO_EN_GARANTIA_M$",
}
UNIDAD_POSICION = {
    ("r", "2", 521): "(M$)",
    ("v", "2", 201): "(M$)", ("v", "2", 333): "(M$)",
    ("v", "2", 413): "(UM)", ("v", "2", 430): "(M$)",
    ("g", "2", 250): "(M$)", ("g", "2", 280): "(M$)",
}
# Un mismo campo, dos nombres: la ficha de 2024 renombra o trunca distinto que la de 2016.
# Sin esto la tabla publicada tendría dos columnas para lo mismo (una nula en cada época).
PARES = {
    ("a", "TIPO_FONDO_ACC"): "TIPO_FONDO",
    ("x", "CODIGO_INDIVIDUALIZACION_O"): "CODIGO_INDIVIDUALIZACION_O_NEMOTECNICO",
    ("x", "ACTIVO_EN_MARGEN_O_SUJETO_A"): "ACTIVO_EN_MARGEN_O_SUJETO_A_PACTO",
    ("x", "CRITERIO_VALORIZ"): "CRITERIO_VALORIZACION",
    ("x", "CRITERIO_VALORIZACI"): "CRITERIO_VALORIZACION",
    ("x", "NOMBRE_CUSTODI"): "NOMBRE_CUSTODIO",
    ("x", "ACTIVO_RESPALDA_DFL_RESERVA_VALOR_DE_FONDO"): "ACTIVO_RESPALDA_RESERVA_VALOR_DE_FONDO",
    ("p", "FECHA_DE_LA"): "FECHA_DE_LA_OPERACION",
    ("p", "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMAC"):
        "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMACION",
    ("p", "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMAC_ION"):
        "VALOR_RAZONABLE_DEL_CONTRATO_FUTURO_A_LA_FECHA_DE_INFORMACION",
    ("p", "TASA_A_FUTURO_MERCADO"): "TASA_A_FUTURO_MERCADO_POSICION_LARGA",
    # B.6 (Otras inversiones): la conversión del anexo 2024 cortó estos nombres a media
    # palabra; el nombre completo está en la ficha, en el renglón del PICTURE o al lado.
    ("o", "ACTIVO_EN_MARGEN_O_SUJETO_A"): "ACTIVO_EN_MARGEN_O_SUJETO_A_PACTO",
    ("o", "METOD_CLASIF_VALO"): "METOD_CLASIF_VALORIZ_EEFF",
    ("o", "CRITERIO_VALORIZAC"): "CRITERIO_VALORIZACION",
    ("o", "MODELO_VALORACIO"): "MODELO_VALORACION",
    ("o", "MODELO_PROPIO_DE_TERIORO"): "MODELO_PROPIO_DETERIORO",
    ("o", "COLIGADA_FILIAL_INM_OB"): "COLIGADA_FILIAL_INMOB",
    ("o", "DESCRIPCION_ACTIVO"): "DESCRIPCION_ACTIVOS",
    ("o", "CLASIFICACION_DE_RI"): "CLASIFICACION_DE_RIESGO_PAIS",
}


# Nombres que la ficha repite dentro de un mismo registro: (letra, tipo, nombre, aparición).
ALIAS = {
    # En los swaps (p5) la ficha usa el mismo nombre del activo objeto para el nocional del
    # contrato: se desambigua con el sufijo _NOCIONAL para no mezclar texto con número.
    ("p", "5", "ACTIVO_OBJETO_POSICION_LARGA", 1): "ACTIVO_OBJETO_POSICION_LARGA_NOCIONAL",
    ("p", "5", "ACTIVO_OBJETO_POSICION_CORTA", 1): "ACTIVO_OBJETO_POSICION_CORTA_NOCIONAL",
    ("i", "2", "DIG_RUT", 2): "DIG_RUT_PROVEEDOR_PRECIOS",
    ("i", "2", "RUT_DEUDOR", 2): "RUT_DEUDOR_SINDICADO",
    ("i", "2", "VERIFICADOR_DEUDOR", 1): "VERIFICADOR_DEUDOR_SINDICADO",
    ("p", "2", "ACTIVO_OBJETO", 1): "ACTIVO_OBJETO_POSICION_CORTA",
    ("p", "2", "ACTIVO_OBJETO", 2): "ACTIVO_OBJETO_UNIDADES",
    ("p", "3", "ACTIVO_OBJETO", 1): "ACTIVO_OBJETO_POSICION_CORTA",
    ("p", "3", "ACTIVO_OBJETO_POSICION_LARGA", 2): "ACTIVO_OBJETO_POSICION_LARGA_UNIDADES",
    ("p", "3", "ACTIVO_OBJETO_POSICION_CORTA", 1): "ACTIVO_OBJETO_POSICION_CORTA_UNIDADES",
    ("p", "4", "ACTIVO_OBJETO", 1): "ACTIVO_OBJETO_POSICION_CORTA",
    ("p", "4", "ACTIVO_OBJETO_POSICION_LARGA", 2): "ACTIVO_OBJETO_POSICION_LARGA_UNIDADES",
    ("p", "4", "ACTIVO_OBJETO_POSICION_CORTA", 1): "ACTIVO_OBJETO_POSICION_CORTA_UNIDADES",
    ("p", "6", "ACTIVO_OBJETO", 2): "ACTIVO_OBJETO_VALOR_CONTABLE",
}

# Unidades que la ficha declara en un renglón que el lector no alcanzó a unir al campo, porque
# el nombre está partido y la descripción sigue al trozo final. Se declaran acá para no dejar un
# monto en M$ sin su sufijo (mismo criterio que REPARAR: corrección explícita y acotada).
UNIDAD_CURADA = {
    ("o", "2", "DEPRECIACION_ACUMULADA"): "(M$)",
    ("o", "2", "VALOR_RAZONABLE"): "(M$)",
}

# Campos que no se publican: relleno, tipo de registro y el dígito verificador
# (se publica junto al RUT, como ``97004000-5``).
_OMITIR_NOMBRE = {"FILLER", "FLLER"}
_OMITIR_INICIO = {(0, "TIPO")}
_RE_DV = re.compile(r"^(DIG_RUT|DIG|D_V|DV|VERIFICADOR)")
_RE_RUT = re.compile(r"^(RUT|NRO_RUT|RUN|NRO_RUN)")


def _reparar(nombre: str) -> str:
    for patron, reemplazo in _REPARAR:
        if patron.match(nombre):
            return re.sub(patron, reemplazo, nombre)
    return nombre


_SIN_UNIDAD = re.compile(r"UNIDAD_MONETARIA|MONEDA|UNIDAD$|CODIGO|TIPO|FECHA|NOMBRE|PAIS")


def _unidad(campo, curada: str | None = None) -> str | None:
    """Unidad del campo: la anotada al lado del nombre o la que dice la descripción.

    Sólo aplica a los montos: los campos de texto (códigos, nombres) y los que la
    descripción menciona de paso ("en la unidad monetaria del instrumento") quedan sin
    sufijo, o terminarían llamándose ``unidad_monetaria_um``.
    """
    if curada:
        return curada
    if campo.unidad:
        return campo.unidad
    if campo.tipo != "n" or _SIN_UNIDAD.search(campo.nombre):
        return None
    return unidad_del_texto(campo.descripcion)


def _con_unidad(nombre: str, unidad: str | None) -> str:
    if not unidad:
        return nombre
    sufijo = SUFIJO_UNIDAD.get(unidad)
    if not sufijo or nombre.endswith("_" + sufijo):
        return nombre
    return f"{nombre}_{sufijo}"


def columna(nombre: str) -> str:
    """Nombre publicado en la base: minúsculas, sin acentos ni guiones."""
    return re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")


def _es_fecha(campo) -> bool:
    return campo.largo == 8 and campo.decimales == 0 and (
        campo.nombre.startswith("FECHA") or "AAAAMMDD" in campo.descripcion.upper()
    )


def _es_rut(campo, siguiente) -> bool:
    """9(09) seguido del dígito verificador X(01)."""
    return (
        campo.largo == 9
        and campo.tipo == "n"
        and _RE_RUT.match(campo.nombre) is not None
        and siguiente is not None
        and siguiente.largo == 1
        and siguiente.tipo == "t"
        and _RE_DV.match(siguiente.nombre) is not None
    )


def _tipo(campo, siguiente) -> tuple[str, int]:
    """(tipo publicado, largo publicado)."""
    if _es_rut(campo, siguiente):
        return "r", campo.largo + 1
    if _es_fecha(campo):
        return "f", campo.largo
    return ("s" if campo.con_signo else campo.tipo), campo.largo


def _base(formato: str) -> dict[tuple[str, str], list[dict]]:
    """Campos de un formato con el nombre de la ficha ya reparado, sin sufijo de unidad."""
    salida: dict[tuple[str, str], list[dict]] = {}
    for clave, registro in sorted(registros(formato).items()):
        if clave not in DESTINO:
            continue
        vistos: dict[str, int] = {}
        campos: list[dict] = []
        for n, campo in enumerate(registro.campos):
            nombre_oficial = NOMBRES_POSICION.get((clave[0], clave[1], campo.inicio))
            if nombre_oficial:
                campo.nombre = nombre_oficial
                campo.nombre_ficha = NOMBRES_FICHA_POSICION.get(
                    (clave[0], clave[1], campo.inicio), nombre_oficial)
            nombre = _reparar(campo.nombre)
            if nombre in _OMITIR_NOMBRE or (campo.inicio, nombre) in _OMITIR_INICIO:
                continue
            aparece = vistos[nombre] = vistos.get(nombre, 0) + 1
            nombre = ALIAS.get((clave[0], clave[1], nombre, aparece), nombre)
            reparado = PARES.get((clave[0], nombre))
            if reparado and clave[0] in REPARAR_NOMBRE_FICHA:
                # B.6 no tiene historia publicada: se publica el nombre completo de la ficha y
                # no el trozo que dejó la conversión del anexo.
                campo.nombre_ficha = reparado
            nombre = reparado or nombre
            campos.append({
                "nombre": nombre,
                "aparece": aparece,
                "campo": campo,
                "unidad_curada": UNIDAD_POSICION.get(
                    (clave[0], clave[1], campo.inicio), UNIDAD_CURADA.get((clave[0], clave[1], nombre))),
                "siguiente": registro.campos[n + 1] if n + 1 < len(registro.campos) else None,
            })
        salida[clave] = campos
    return salida


def inventario(formato: str) -> dict[tuple[str, str], list[dict]]:
    """{(letra, tipo): [campos publicados]} de un formato, listos para publicar.

    La unidad se toma de los dos formatos: si la ficha de 2016 dice "en miles de pesos"
    y la de 2024 no lo repite, el sufijo se publica igual en las dos épocas.
    """
    base = {f: _base(f) for f in FORMATOS}
    # La unidad se guarda por (registro, nombre, aparición): los campos que la ficha repite
    # con distinta unidad ((UM) y (M$)) conservan así su propio sufijo.
    unidades: dict[tuple[tuple[str, str], str, int], str] = {}
    for f in FORMATOS:
        for clave, campos in base[f].items():
            for c in campos:
                unidad = _unidad(c["campo"], c.get("unidad_curada"))
                if unidad:
                    unidades.setdefault((clave, c["nombre"], c["aparece"]), unidad)
    salida: dict[tuple[str, str], list[dict]] = {}
    for clave, campos in base[formato].items():
        publicados: list[dict] = []
        salta_dv = False
        for c in campos:
            campo = c["campo"]
            if salta_dv:  # el dígito verificador viaja con el RUT
                salta_dv = False
                continue
            unidad = unidades.get((clave, c["nombre"], c["aparece"]))
            nombre = _con_unidad(c["nombre"], unidad)
            tipo, largo = _tipo(campo, c["siguiente"])
            if tipo == "r":
                salta_dv = True
            publicados.append({
                "nombre": nombre,
                "columna": columna(nombre),
                "inicio": campo.inicio,
                "largo": largo,
                "picture": campo.picture,
                "tipo": tipo,
                "decimales": campo.decimales,
                "unidad": unidad,
                "nombre_ficha": campo.nombre_ficha,
                "descripcion": campo.descripcion,
                "renglon": campo.renglon,
                "ficha": campo.ficha,
            })
        salida[clave] = publicados
    return salida


def escribir(ruta: Path = RUTA_JSON) -> Path:
    datos = {
        "origen": "Anexos técnicos de la Circular 1835 (CMF), copiados en seguros/fuentes/fichas_tecnicas_1835",
        "formatos": {
            formato: {
                f"{letra}{tipo}": {
                    "tabla": DESTINO[(letra, tipo)][0],
                    "subtipo": DESTINO[(letra, tipo)][1],
                    "campos": campos,
                }
                for (letra, tipo), campos in inventario(formato).items()
            }
            for formato in FORMATOS
        },
    }
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ruta


def reporte() -> None:
    for formato in FORMATOS:
        print(f"===== {formato}")
        for (letra, tipo), campos in inventario(formato).items():
            tabla, subtipo = DESTINO[(letra, tipo)]
            cols = [c["columna"] for c in campos]
            repetidas = sorted({c for c in cols if cols.count(c) > 1})
            print(f"  {letra}{tipo} {tabla}/{subtipo}: {len(campos)} campos"
                  + (f"  REPETIDAS {repetidas}" if repetidas else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--escribir", action="store_true", help="escribe el JSON del inventario")
    ap.add_argument("--reporte", action="store_true", help="resume campos por tabla")
    a = ap.parse_args()
    if a.escribir:
        print(escribir())
    if a.reporte or not a.escribir:
        reporte()

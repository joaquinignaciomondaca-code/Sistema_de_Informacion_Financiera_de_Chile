"""Posiciones oficiales de los archivos de cartera de inversiones de seguros (CMF, Circular 1835).

Las posiciones salen de las fichas técnicas de la CMF (copia en texto en
seguros/fuentes/fichas_tecnicas_1835/) y se verificaron contra líneas reales
(seguros/fuentes/muestras_1835/):

  - "v2016": ficha vigente hasta el 30-11-2024 (B.1 a B.8, versión 22-11-2016).
  - "v2024": Anexo Técnico vigente desde el 01-12-2024 (Circular 2354).

Cada campo es (columna, inicio, largo, tipo, decimales), con inicio en base 0.
Tipos: "t" texto, "n" número sin signo, "s" número con signo en el primer carácter
("+", "-", espacio o "0"), "f" fecha AAAAMMDD, "r" RUT (9 dígitos + DV en el carácter
siguiente). Los montos van en la unidad que dice la ficha: la columna lo indica
(_m_clp = miles de pesos, _clp = pesos).
"""

FORMATO_2024_DESDE = "2024-12"

# Largo exacto de cada línea (todas las líneas de un archivo tienen el mismo largo).
LARGO = {
    "v2016": {"i": 930, "a": 470, "f": 338, "b": 477, "x": 513, "p": 489, "c": 138},
    "v2024": {"i": 970, "a": 572, "f": 361, "b": 506, "x": 611, "p": 587, "c": 138},
}

# Tipo de registro de totales (cuenta las líneas de detalle) por archivo.
TIPO_TOTAL = {"i": "3", "a": "3", "f": "3", "b": "3", "x": "6", "p": "7", "c": "3"}

# Encabezado (registro tipo 1), igual en todos los archivos y formatos.
ENCABEZADO = [("rut_aseguradora", 1, 10, "r", 0), ("nombre_aseguradora", 11, 60, "t", 0), ("periodo_archivo", 71, 6, "t", 0)]


def _renta_fija(fv, tasa, tasa_tipo, d):
    """B.1 renta fija. fv/tasa: inicio de fecha de vencimiento y tasa de emisión;
    d: inicio del campo CUSTODIA_INV (el bloque final se ubica desde ahí)."""
    return [
        ("tipo_instrumento", 43, 10, "t", 0), ("nemotecnico", 53, 30, "t", 0), ("serie", 104, 10, "t", 0),
        ("rut_emisor", 33, 9, "r", 0), ("pais", 114, 2, "t", 0),
        ("fecha_compra", 17, 8, "f", 0), ("fecha_emision", 83, 8, "f", 0), ("fecha_vencimiento", fv, 8, "f", 0),
        ("unidad_monetaria", 150, 6, "t", 0), ("valor_nominal", 116, 17, "n", 4),
        ("tasa_emision_pct", tasa, 8, tasa_tipo, 4),
        ("tir_compra_pct", d - 84, 8, "s", 4), ("tir_mercado_pct", d - 48, 8, "s", 4),
        ("valor_compra_clp", d - 105, 13, "n", 0), ("costo_amortizado_clp", d - 61, 13, "n", 0),
        ("valor_razonable_clp", d - 40, 13, "n", 0), ("deterioro_clp", d - 27, 14, "s", 0),
        ("valor_final_m_clp", d - 13, 13, "n", 0), ("custodia", d, 3, "t", 0),
    ]


def _acciones(o):
    """B.2 acciones y cuotas de fondos de inversión. o: desplazamientos del formato."""
    return [
        ("tipo_instrumento", o["tipo"], 10, "t", 0), ("rut_emisor", 1, 9, "r", 0), ("run_fondo", 11, 9, "r", 0),
        ("nemotecnico", o["nemo"], 60, "t", 0), ("serie", o["serie"], o["serie_largo"], "t", 0),
        ("unidades", o["unid"], 17, "n", 4), ("presencia_bursatil_pct", o["unid"] + 17, 5, "n", 2),
        ("valor_costo_clp", o["costo"], 13, "n", 0), ("valor_bolsa_clp", o["costo"] + 26, 13, "n", 0),
        ("valor_razonable_m_clp", o["costo"] + 39, 13, "n", 0), ("deterioro_m_clp", o["costo"] + 52, 14, "s", 0),
        ("valor_final_m_clp", o["vf"], 13, "n", 0), ("unidad_monetaria", o["vf"] + 13, 6, "t", 0),
        ("custodia", o["cust"], 3, "t", 0),
    ]


def _fondos(o):
    """B.3 cuotas de fondos mutuos."""
    return [
        ("tipo_instrumento", 21, 10, "t", 0), ("rut_administradora", 1, 9, "r", 0), ("run_fondo", 11, 9, "r", 0),
        ("nemotecnico", 31, 10, "t", 0), ("tipo_fondo", 41, 2, "t", 0), ("serie", 43, o["serie_largo"], "t", 0),
        ("unidades", o["unid"], 17, "n", 4), ("unidad_monetaria", o["unid"] + 17, 6, "t", 0),
        ("valor_cuota", o["unid"] + 23, 17, "n", 4), ("valor_final_m_clp", o["vf"], 12, "n", 0),
        ("custodia", o["cust"], 3, "t", 0), ("clasificacion_riesgo", o["clas"], 15, "t", 0),
    ]


def _bienes_raices(k):
    """B.4 bienes raíces y contratos de leasing. k: desplazamiento (0 viejo, 3 nuevo)."""
    return [
        ("rol", 1, 11, "t", 0), ("tipo_instrumento", 34 + k, 10, "t", 0), ("nemotecnico", 44 + k, 30, "t", 0),
        ("direccion", 145 + k, 40, "t", 0), ("codigo_comuna", 185 + k, 3, "t", 0), ("ciudad", 188 + k, 30, "t", 0),
        ("monto_arriendo_uf", 139 + k, 6, "n", 2), ("fecha_compra", 218 + k, 8, "f", 0),
        ("costo_m_clp", 227 + k, 11, "n", 0), ("depreciacion_m_clp", 238 + k, 11, "n", 0),
        ("costo_corregido_m_clp", 253 + k, 11, "n", 0), ("tasacion_1_m_clp", 264 + k, 11, "n", 0),
        ("tasacion_2_m_clp", 275 + k, 11, "n", 0),
    ]


BIENES_RAICES_FINAL = {  # deterioro y valor final (la versión nueva agrega campos de m2 antes)
    "v2016": [("deterioro_m_clp", 382, 11, "n", 0), ("valor_final_m_clp", 393, 12, "n", 0)],
    "v2024": [("deterioro_m_clp", 411, 11, "n", 0), ("valor_final_m_clp", 422, 12, "n", 0)],
}

EXTRANJEROS_DEUDA = {  # B.5 registro tipo 2: instrumentos de deuda
    "v2016": [("tipo_instrumento", 14, 10, "t", 0), ("valor_nominal", 24, 15, "n", 4), ("pais", 39, 2, "t", 0),
              ("emisor", 43, 40, "t", 0), ("codigo", 83, 30, "t", 0), ("moneda", 113, 6, "t", 0),
              ("fecha_compra", 127, 8, "f", 0), ("fecha_vencimiento", 135, 8, "f", 0),
              ("tasa_emision_pct", 146, 7, "n", 4), ("valor_final_m_clp", 253, 12, "n", 0),
              ("clasificacion_riesgo", 266, 15, "t", 0)],
    "v2024": [("tipo_instrumento", 14, 10, "t", 0), ("valor_nominal", 24, 15, "n", 4), ("pais", 39, 2, "t", 0),
              ("emisor", 45, 40, "t", 0), ("codigo", 85, 30, "t", 0), ("moneda", 115, 6, "t", 0),
              ("fecha_compra", 129, 8, "f", 0), ("fecha_vencimiento", 137, 8, "f", 0),
              ("tasa_emision_pct", 157, 8, "s", 4), ("valor_final_m_clp", 266, 12, "n", 0),
              ("clasificacion_riesgo", 279, 15, "t", 0)],
}

EXTRANJEROS_ACCIONES = {  # B.5 registro tipo 3: acciones y cuotas de fondos extranjeros
    "v2016": [("tipo_instrumento", 1, 10, "t", 0), ("pais", 11, 2, "t", 0), ("emisor", 53, 60, "t", 0),
              ("codigo", 113, 30, "t", 0), ("serie", 143, 10, "t", 0), ("moneda", 153, 6, "t", 0),
              ("unidades", 161, 17, "n", 4), ("valor_final_m_clp", 262, 12, "n", 0),
              ("clasificacion_riesgo", 275, 15, "t", 0)],
    "v2024": [("tipo_instrumento", 1, 10, "t", 0), ("pais", 11, 2, "t", 0), ("emisor", 55, 60, "t", 0),
              ("codigo", 155, 30, "t", 0), ("serie", 185, 30, "t", 0), ("moneda", 215, 6, "t", 0),
              ("unidades", 237, 17, "n", 4), ("valor_final_m_clp", 355, 12, "n", 0),
              ("clasificacion_riesgo", 368, 15, "t", 0)],
}

# B.8 información de control: igual en ambos formatos.
CONTROL = [
    ("tipo_inversion", 1, 3, "t", 0), ("valor_final_m_clp", 4, 12, "s", 0),
    ("inversiones_representativas_m_clp", 16, 12, "s", 0), ("inversiones_no_representativas_m_clp", 28, 12, "s", 0),
    ("total_costo_amortizado_m_clp", 40, 14, "s", 0), ("total_valor_razonable_m_clp", 54, 14, "s", 0),
    ("total_efectivo_equivalente_m_clp", 68, 14, "s", 0), ("total_cui_apv_m_clp", 82, 14, "s", 0),
    ("total_otra_clasificacion_m_clp", 96, 14, "s", 0), ("total_filiales_m_clp", 110, 14, "s", 0),
    ("total_coligadas_m_clp", 124, 14, "s", 0),
]


def _derivado(k_ident, k, obj, pos):
    """B.7 opciones, forwards, futuros y swaps: columnas comunes.
    k_ident: largo de OBJETIVO (3 o 5); k: 0 en v2016, o el bloque de contraparte de v2024."""
    base = 1 + obj
    cols = [
        ("objetivo", 1, obj, "t", 0), ("tipo_operacion", base, 10, "t", 0),
    ]
    b = base + 10 + (2 if k else 0)  # v2024 agrega TIPO_CONTRATO 9(02)
    cols += [("folio", b, 10, "t", 0), ("item", b + 10, 3, "t", 0),
             ("fecha_operacion", b + 13, 8, "f", 0), ("fecha_vencimiento", b + 21, 8, "f", 0)]
    c = b + 29 + (30 if k else 0)  # v2024 agrega RUT nacional (9+1) e identificador extranjero (20)
    cols += [("contraparte", c, 60, "t", 0), ("nacionalidad_contraparte", c + 60, 2, "t", 0),
             ("relacionado", c + 62, 2, "t", 0)]
    cols += pos
    return cols


def _pos_opcion(v):
    o = 162 if v == "v2024" else 122
    return [("clasificacion_riesgo", o - 15, 15, "t", 0), ("activo_objeto_largo", o, 30, "t", 0),
            ("activo_objeto_corto", o + 30, 30, "t", 0), ("nocional_largo", o + 60, 16, "n", 3),
            ("moneda", o + 76, 6, "t", 0), ("valor_razonable_m_clp", o + 149, 13, "s", 0),
            ("origen_valorizacion", o + 162, 30, "t", 0),
            ("efecto_resultados_m_clp", 472 if v == "v2024" else 418, 14, "s", 0)]


def _pos_forward(v):
    o = 229 if v == "v2024" else 189
    vr = 426 if v == "v2024" else 360
    ef = 537 if v == "v2024" else 443
    return [("clasificacion_riesgo", o - 80, 15, "t", 0), ("activo_objeto_largo", o, 30, "t", 0),
            ("activo_objeto_corto", o + 30, 30, "t", 0), ("nocional_largo", o + 60, 16, "n", 3),
            ("nocional_corto", o + 76, 16, "n", 3),
            ("moneda", 347 if v == "v2024" else 281, 6, "t", 0),
            ("valor_razonable_m_clp", vr, 14, "s", 0),
            ("origen_valorizacion", vr + (28 if v == "v2024" else 14), 30, "t", 0),
            ("efecto_resultados_m_clp", ef, 14, "s", 0)]


def _pos_futuro(v):
    o = 227 if v == "v2024" else 187
    return [("clasificacion_riesgo", 147 if v == "v2024" else 107, 15, "t", 0),
            ("activo_objeto_largo", o, 30, "t", 0), ("activo_objeto_corto", o + 30, 30, "t", 0),
            ("nocional_largo", o + 60, 16, "n", 3), ("nocional_corto", o + 76, 16, "n", 3),
            ("moneda", 345 if v == "v2024" else 279, 6, "t", 0),
            ("valor_razonable_m_clp", 498 if v == "v2024" else 418, 14, "s", 0),
            ("origen_valorizacion", 415 if v == "v2024" else 349, 30, "t", 0)]


def _pos_swap(v):
    if v == "v2024":
        return [("clasificacion_riesgo", 149, 15, "t", 0), ("nocional_largo", 190, 16, "n", 3),
                ("nocional_corto", 206, 16, "n", 3), ("moneda_larga", 222, 6, "t", 0), ("moneda_corta", 228, 6, "t", 0),
                ("tasa_larga", 234, 30, "t", 0), ("tasa_corta", 264, 30, "t", 0),
                ("valor_razonable_m_clp", 389, 14, "s", 0), ("origen_valorizacion", 417, 30, "t", 0),
                ("efecto_resultados_m_clp", 565, 14, "s", 0)]
    return [("clasificacion_riesgo", 109, 15, "t", 0), ("nocional_largo", 124, 16, "n", 3),
            ("nocional_corto", 140, 16, "n", 3), ("moneda_larga", 156, 6, "t", 0), ("moneda_corta", 162, 6, "t", 0),
            ("tasa_larga", 168, 30, "t", 0), ("tasa_corta", 198, 30, "t", 0),
            ("valor_razonable_m_clp", 319, 14, "s", 0), ("origen_valorizacion", 333, 30, "t", 0),
            ("efecto_resultados_m_clp", 467, 14, "s", 0)]


def _pactos(v):
    k = 1 if v == "v2024" else 0  # v2024: TIR_COMPRA y TASA_EMISION pasan a -9(10)V9(03) con signo (14)
    return [("tipo_operacion", 1, 10, "t", 0), ("folio", 11, 10, "t", 0), ("item", 21, 3, "t", 0),
            ("fecha_operacion", 24, 8, "f", 0), ("fecha_vencimiento", 32, 8, "f", 0),
            ("tasa_pacto_pct", 40, 13, "n", 3), ("contraparte", 53, 60, "t", 0),
            ("nacionalidad_contraparte", 113, 2, "t", 0), ("relacionado", 115, 2, "t", 0),
            ("activo_objeto", 117, 30, "t", 0), ("serie_activo_objeto", 147, 30, "t", 0),
            ("rut_emisor_activo_objeto", 177, 9, "r", 0), ("valor_nominal", 187, 16, "n", 3),
            ("moneda", 242 + 2 * k, 6, "t", 0),
            ("interes_devengado_m_clp", 309 + 3 * k, 13, "n", 0), ("valor_contable_m_clp", 322 + 3 * k, 13, "n", 0),
            ("valor_mercado_activo_objeto_m_clp", 335 + 3 * k, 13, "n", 0)]


def campos(formato):
    """Diccionario {(archivo, tipo_registro): (tabla, subtipo, campos)} para un formato."""
    v24 = formato == "v2024"
    rf = _renta_fija(266, 283, "s", 906) if v24 else _renta_fija(264, 272, "s", 866)
    acc = _acciones({"tipo": 61, "nemo": 71, "serie": 131, "serie_largo": 30, "unid": 161, "costo": 189,
                     "vf": 271, "cust": 398} if v24 else
                    {"tipo": 21, "nemo": 31, "serie": 91, "serie_largo": 10, "unid": 101, "costo": 123,
                     "vf": 203, "cust": 330})
    fon = _fondos({"serie_largo": 30, "unid": 73, "vf": 153, "cust": 258, "clas": 324} if v24 else
                  {"serie_largo": 10, "unid": 53, "vf": 133, "cust": 238, "clas": 304})
    br = _bienes_raices(3 if v24 else 0) + BIENES_RAICES_FINAL[formato]
    k = 1 if v24 else 0
    return {
        ("i", "2"): ("renta_fija", None, rf),
        ("a", "2"): ("acciones", None, acc),
        ("f", "2"): ("fondos_mutuos", None, fon),
        ("b", "2"): ("bienes_raices", None, br),
        ("x", "2"): ("extranjeros", "deuda", EXTRANJEROS_DEUDA[formato]),
        ("x", "3"): ("extranjeros", "acciones_y_fondos", EXTRANJEROS_ACCIONES[formato]),
        ("c", "2"): ("control_inversiones", None, CONTROL),
        ("p", "2"): ("derivados", "opcion", _derivado(3, k, 3, _pos_opcion(formato))),
        ("p", "3"): ("derivados", "forward", _derivado(5, k, 5, _pos_forward(formato))),
        ("p", "4"): ("derivados", "futuro", _derivado(3, k, 3, _pos_futuro(formato))),
        ("p", "5"): ("derivados", "swap", _derivado(5, k, 5, _pos_swap(formato))),
        ("p", "6"): ("pactos", None, _pactos(formato)),
    }


def formato_de(periodo):
    return "v2024" if periodo >= FORMATO_2024_DESDE else "v2016"

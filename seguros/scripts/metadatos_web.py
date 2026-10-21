"""Descripción de las tablas de seguros para la web (diccionario, diagrama y data_manifest.json).

Las descripciones de las columnas salen de la ficha técnica de la Circular 1835 (ver
``diccionario_1835.py``): se publican todos los campos, con el nombre original de la CMF.
"""

ORIGEN = ("CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales "
          "de vida (CSVID) y generales (CSGEN), conforme a la ficha técnica oficial (formato vigente "
          "hasta 2024-11 y formato desde 2024-12). Fuente: "
          "https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf")

TABLAS = {
    "aseguradoras": ("seguros.lista_entidades",
                     "Compañías de seguros de vida y generales que envían su cartera a la CMF, con el primer y el "
                     "último mes informado. Sirve para detectar compañías nuevas y las que dejan de reportar."),
    "renta_fija": ("B.1 INSTRUMENTOS DE RENTA FIJA",
                   "Bonos, letras, depósitos y demás instrumentos de renta fija nacionales, uno por fila, con sus "
                   "tasas, costo amortizado, valor razonable y valor final."),
    "acciones": ("B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS Y CUOTAS DE FONDOS DE INVERSIÓN",
                 "Acciones de sociedades anónimas y cuotas de fondos de inversión nacionales."),
    "fondos_mutuos": ("B.3 CUOTAS DE FONDOS MUTUOS", "Cuotas de fondos mutuos nacionales."),
    "bienes_raices": ("B.4 BIENES RAICES",
                      "Bienes raíces por inmueble: arriendo, costo, depreciación, tasaciones y valor final. El rol y la dirección exacta se suprimen por privacidad y se reemplazan por property_id."),
    "extranjeros": ("B.5 INVERSIONES EN EL EXTRANJERO",
                    "Inversiones en el extranjero: deuda (tipo_registro = 'deuda'), acciones y fondos "
                    "(tipo_registro = 'acciones_y_fondos'), bienes raíces (tipo_registro = 'bienes_raices') y "
                    "filiales (tipo_registro = 'filiales')."),
    "derivados": ("B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS",
                  "Contratos de opciones, forwards, futuros y swaps (tipo_registro), con contraparte, nocional, "
                  "valor razonable y efecto en resultados."),
    "pactos": ("B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS", "Compras y ventas con pacto (repos), con contraparte, tasa y activo objeto."),
    "control_inversiones": ("B.8 INFORMACION DE CONTROL",
                            "Información de control que cada compañía envía con su cartera: totales por tipo de "
                            "inversión (valor final, representativas y no representativas de reservas, etc.)."),
    # "Otros registros" del anexo 2024 (B.6 y B.9–B.11): existen solo desde 2024-12.
    "otras_inversiones": ("B.6 OTRAS INVERSIONES",
                          "Otras inversiones de la cartera: saldos en cuenta corriente y caja, inversiones "
                          "mobiliarias, avances a tenedores de pólizas, préstamos y otras inversiones "
                          "financieras que no caben en los archivos anteriores."),
    "tablas_descriptores": ("B.9 TABLAS DE DESCRIPTORES",
                            "Descriptores de los instrumentos de la cartera: emisor, tipo de instrumento, "
                            "fechas y tasas de emisión y descuento, número de flujos y opciones de prepago."),
    "tablas_desarrollo": ("B.10 TABLAS DE DESARROLLO",
                          "Desarrollo de los flujos de cada instrumento: cupón, fecha de vencimiento, "
                          "interés, amortización y saldo insoluto."),
    "flujos_activos_elegibles": ("B.11 FLUJOS DE ACTIVOS ELEGIBLES",
                                 "Flujos de activos elegibles por tramo, para el cálculo del test de "
                                 "suficiencia de activos (circular aplicada y tipo de información)."),
    "prestamos": ("B.12 PRÉSTAMOS",
                  "Préstamos informados por las compañías, con características del deudor, condiciones financieras, "
                  "saldo, provisiones y morosidad."),
    "bienes_raices_arriendo_morosidad": (
        "B.13 BIENES RAICES EN ARRIENDO Y MOROSIDAD DE MUTUOS HIPOTECARIOS ENDOSABLES Y CONTRATOS DE LEASING",
        "Detalle por inmueble, unidad o contrato: arriendos, recaudación, morosidad, reprogramaciones y saldos."),
    "garantias_derivados": ("B.14 GARANTÍAS EN INSTRUMENTOS DERIVADOS",
                            "Garantías en efectivo o instrumentos, recibidas u otorgadas, asociadas a derivados."),
    "registros_tipo6": ("Registros tipo 6 de B.11 y B.14",
                        "Líneas tipo 6 reportadas por la CMF en archivos B.11 (E) y B.14 (G). Se conserva íntegra cada línea, junto con período, sector, aseguradora y archivo de origen; los campos internos no se interpretan porque no están descritos en el anexo consultado."),
    "renta_fija_relevante": ("B.1 INSTRUMENTOS DE RENTA FIJA",
                             "Vista analítica de B.1 con identificación, vencimiento, magnitudes de costo y valor, "
                             "riesgo y representatividad. La tabla completa conserva todos los campos."),
    "acciones_relevantes": ("B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS Y CUOTAS DE FONDOS DE INVERSIÓN",
                            "Vista analítica de B.2 con identificación del instrumento, unidades, valorización, "
                            "deterioro y riesgo. La tabla completa conserva todos los campos."),
    "bienes_raices_relevantes": ("B.4 BIENES RAICES",
                                 "Vista analítica de B.4 con ubicación geográfica general, superficie y valorización; "
                                 "no incluye rol ni dirección exacta."),
    "extranjeros_relevantes": ("B.5 INVERSIONES EN EL EXTRANJERO",
                               "Vista analítica de B.5 con país, instrumento, moneda, vencimiento y valorización."),
    "derivados_relevantes": ("B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS",
                             "Vista analítica de derivados con tipo, vencimiento, nocionales y valores razonables."),
    "prestamos_relevantes": ("B.12 PRÉSTAMOS",
                             "Vista analítica de B.12 con condiciones, saldo, provisión y morosidad; no incluye "
                             "identificadores personales de deudores."),
    "bienes_raices_arriendo_morosidad_relevantes": (
        "B.13 BIENES RAICES EN ARRIENDO Y MOROSIDAD DE MUTUOS HIPOTECARIOS ENDOSABLES Y CONTRATOS DE LEASING",
        "Vista analítica de B.13 con cobranza, mora, provisión, superficie y valorización; suprime identificadores personales."),
}

# Orden visible del manual (B.1 → B.14); cada vista simplificada sigue inmediatamente a su registro.
_ORDEN_TABLAS = [
    "aseguradoras", "renta_fija", "renta_fija_relevante", "acciones", "acciones_relevantes",
    "fondos_mutuos", "bienes_raices", "bienes_raices_relevantes", "extranjeros", "extranjeros_relevantes",
    "otras_inversiones", "derivados", "derivados_relevantes", "pactos", "control_inversiones",
    "tablas_descriptores", "tablas_desarrollo", "flujos_activos_elegibles", "prestamos",
    "prestamos_relevantes", "bienes_raices_arriendo_morosidad",
    "bienes_raices_arriendo_morosidad_relevantes", "garantias_derivados", "registros_tipo6",
]
TABLAS = {tabla: TABLAS[tabla] for tabla in _ORDEN_TABLAS}

# Columnas que arma el pipeline (no vienen en la ficha): se describen a mano.
COLUMNAS_CONTROL = {
    "periodo": "Mes de la cartera (AAAA-MM).",
    "sector": "vida o generales.",
    "rut_aseguradora": "RUT de la compañía de seguros, con dígito verificador "
                       "(une con seguros.lista_entidades).",
    "nombre_aseguradora": "Nombre de la compañía tal como aparece en el archivo del mes.",
    "tipo_registro": "Subtipo de registro de la ficha (p. ej. forward, swap, deuda).",
    "primer_periodo": "Primer mes en que la compañía aparece en los archivos publicados.",
    "ultimo_periodo": "Último mes en que la compañía aparece.",
    "meses_reportados": "Número de meses publicados en que la compañía tiene filas publicadas "
                        "(meses con al menos una fila en alguna tabla; no cuenta meses en que solo "
                        "envió archivos sin detalle).",
    "reporta_ultimo_mes": "Verdadero si aparece en el último mes publicado.",
    "archivo_origen": "Nombre del archivo fuente publicado por la CMF.",
    "tipo_archivo": "Sección del anexo a la que corresponde el archivo (B.11 o B.14).",
    "largo_registro": "Longitud de la línea original, en caracteres.",
    "registro_original": "Línea íntegra publicada por la CMF; sus posiciones internas se conservan sin interpretación.",
}


def _columnas_ficha() -> dict:
    """{columna: descripción} de todos los campos de la Circular 1835, desde el inventario.

    La descripción es la de la ficha técnica de la CMF (resumida), con la unidad al final
    cuando el campo la declara (miles de pesos, pesos, UF...).
    """
    from seguros.scripts import diccionario_1835 as dic
    salida = {}
    for filas_ in dic.genera().values():
        for fila in filas_:
            if fila["columna"] in salida:
                continue
            texto = dic._resumen(fila["descripcion"])
            unidad = dic._unidad(fila)
            if unidad:
                texto = f"{texto} Expresado en {unidad}." if texto else f"Expresado en {unidad}."
            salida[fila["columna"]] = texto
    return salida


COLUMNAS = {**_columnas_ficha(), **COLUMNAS_CONTROL}

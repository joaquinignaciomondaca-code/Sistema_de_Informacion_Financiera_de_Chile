"""Descripción de las tablas de seguros para la web (diccionario, diagrama y data_manifest.json).

Las descripciones de las columnas salen de la ficha técnica de la Circular 1835 (ver
``diccionario_1835.py``): se publican todos los campos, con el nombre original de la CMF.
"""

ORIGEN = ("CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales "
          "de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial "
          "(formato vigente hasta 2024-11 y formato desde 2024-12).")

TABLAS = {
    "aseguradoras": ("seguros.lista_entidades",
                     "Compañías de seguros de vida y generales que envían su cartera a la CMF, con el primer y el "
                     "último mes informado. Sirve para detectar compañías nuevas y las que dejan de reportar."),
    "renta_fija": ("seguros.renta_fija",
                   "Bonos, letras, depósitos y demás instrumentos de renta fija nacionales, uno por fila, con sus "
                   "tasas, costo amortizado, valor razonable y valor final."),
    "acciones": ("seguros.acciones",
                 "Acciones de sociedades anónimas y cuotas de fondos de inversión nacionales."),
    "fondos_mutuos": ("seguros.fondos_mutuos", "Cuotas de fondos mutuos nacionales."),
    "bienes_raices": ("seguros.bienes_raices",
                      "Bienes raíces por rol: dirección, arriendo, costo, depreciación, tasaciones y valor final."),
    "extranjeros": ("seguros.extranjeros",
                    "Inversiones en el extranjero: deuda (tipo_registro = 'deuda'), acciones y fondos "
                    "(tipo_registro = 'acciones_y_fondos'), bienes raíces (tipo_registro = 'bienes_raices') y "
                    "filiales (tipo_registro = 'filiales')."),
    "derivados": ("seguros.derivados",
                  "Contratos de opciones, forwards, futuros y swaps (tipo_registro), con contraparte, nocional, "
                  "valor razonable y efecto en resultados."),
    "pactos": ("seguros.pactos", "Compras y ventas con pacto (repos), con contraparte, tasa y activo objeto."),
    "control_inversiones": ("seguros.control_inversiones",
                            "Información de control que cada compañía envía con su cartera: totales por tipo de "
                            "inversión (valor final, representativas y no representativas de reservas, etc.)."),
}

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

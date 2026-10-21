"""Vistas simplificadas de registros extensos de la Circular 1835.

Cada vista conserva las filas de la tabla completa y proyecta un subconjunto explícito de
campos de análisis financiero. Las columnas son identificadores técnicos del Parquet; la ficha
CMF literal y su descripción se conservan en el diccionario. No se transforman ni agregan
magnitudes: la simplificación es sólo de columnas.
"""

# tabla completa -> (tabla derivada, título del anexo, columnas incluidas)
RESUMENES_RELEVANTES = {
    "renta_fija": (
        "renta_fija_relevante",
        "B.1 INSTRUMENTOS DE RENTA FIJA",
        ("periodo", "sector", "rut_aseguradora", "nombre_aseguradora", "codigo_operacion",
         "folio_operacion", "item_operacion", "tipo_instrumento", "nemotecnico", "serie",
         "unidad_monetaria", "fecha_compra", "fecha_vencimiento", "valor_nominal_vigente",
         "costo_amortizado_clp", "valor_razonable_clp", "deterioro_clp", "valor_final_m_clp",
         "clasificacion_de_riesgo", "activo_respalda_reserva_valor_de_fondo", "relacionado"),
    ),
    "acciones": (
        "acciones_relevantes",
        "B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS Y CUOTAS DE FONDOS DE INVERSIÓN",
        ("periodo", "sector", "rut_aseguradora", "nombre_aseguradora", "tipo_instrumento",
         "nemotecnico", "serie", "unidad_monetaria", "unidades", "valor_costo_clp",
         "valor_libro_clp", "valor_bolsa_clp", "valor_razonable_m_clp", "deterioro_m_clp",
         "valor_final_m_clp", "clasificacion_de_riesgo", "relacionado"),
    ),
    "bienes_raices": (
        "bienes_raices_relevantes",
        "B.4 BIENES RAICES",
        ("periodo", "sector", "rut_aseguradora", "nombre_aseguradora", "property_id",
         "tipo_de_inmueble", "tipo_instrumento", "destino", "uso", "comuna", "ciudad",
         "porcentaje_uso_propio", "monto_arriendo_uf", "costo_actualizado_m_clp",
         "depreciacion_acumulada_m_clp", "tasacion_1_m_clp", "tasacion_2_m_clp",
         "deterioro_m_clp", "valor_final_m_clp", "total_m2_terreno", "total_m2_construccion"),
    ),
    "extranjeros": (
        "extranjeros_relevantes",
        "B.5 INVERSIONES EN EL EXTRANJERO",
        ("periodo", "sector", "rut_aseguradora", "nombre_aseguradora", "tipo_registro",
         "tipo_instrumento", "codigo_individualizacion_o_nemotecnico", "pais",
         "moneda", "valor_nominal", "valor_compra_clp", "valor_razonable_m_clp",
         "deterioro_m_clp", "valor_final_m_clp", "costo_historico_m_clp", "valor_contable_m_clp",
         "plazo_al_vencimiento", "duracion", "clasificacion_de_riesgo", "relacionado"),
    ),
    "derivados": (
        "derivados_relevantes",
        "B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS",
        ("periodo", "sector", "rut_aseguradora", "nombre_aseguradora", "tipo_registro",
         "tipo_operacion", "folio_operacion", "item_operacion", "fecha_de_la_operacion",
         "fecha_de_vencimiento_del_contrato", "tipo_contrato", "activo_objeto_posicion_larga",
         "activo_objeto_posicion_corta", "activo_objeto_posicion_larga_nocional",
         "activo_objeto_posicion_corta_nocional", "nocional_posicion_larga_monto",
         "nocional_posicion_corta_monto_m_clp", "valor_razonable_m_clp",
         "valor_presente_posicion_larga_m_clp", "valor_presente_posicion_corta_m_clp",
         "moneda", "tipo_contraparte", "relacionado"),
    ),
    "prestamos": (
        "prestamos_relevantes",
        "B.12 PRÉSTAMOS",
        ("periodo", "sector", "rut_aseguradora", "nombre_aseguradora", "codigo_prestamo",
         "fecha_prestamo", "fecha_vencimiento", "tipo_deudor", "tipo_prestamo",
         "prestamo_representativo", "origen_prestamo", "unidad_reajuste", "monto",
         "monto_pesos", "cuota", "periodo_pago_cuota", "plazo_prestamo", "tipo_tasa",
         "tasa_fija_pactada", "tasa_fija_efectiva", "tasa_variable_base", "spread_tasa_variable",
         "saldo_insoluto_deuda_um", "saldo_insoluto_deuda_m_clp", "valor_final_b_12_m_clp",
         "monto_provision_m_clp", "morosidad", "cuotas_impagas_um", "cuotas_impagas_m_clp"),
    ),
    "bienes_raices_arriendo_morosidad": (
        "bienes_raices_arriendo_morosidad_relevantes",
        "B.13 BIENES RAICES EN ARRIENDO Y MOROSIDAD DE MUTUOS HIPOTECARIOS ENDOSABLES Y CONTRATOS DE LEASING",
        ("periodo", "sector", "rut_aseguradora", "nombre_aseguradora", "property_id",
         "tipo_instrumento", "comuna", "fecha_vencimiento_contrato", "facturacion_mes_m_clp",
         "recaudacion_mes_actual_m_clp", "recaudacion_mes_total_m_clp", "monto_sin_morosidad_m_clp",
         "morosidad_total_m_clp", "provision_incobrabilidad_m_clp", "numero_cuotas_vencidas",
         "monto_total_reprogramacion_m_clp", "total_m2_disponibles_arriendo",
         "total_m2_en_arriendo", "total_m2_no_arrendados", "valor_m2_arriendo_uf",
         "valor_m2_esperado", "deuda_capital_intereses_devengados_um",
         "deuda_capital_intereses_devengados_m_clp"),
    ),
}

FUENTE_MANUAL = "https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf"

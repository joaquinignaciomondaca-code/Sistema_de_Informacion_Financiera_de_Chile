/**
 * Diccionario de Datos & Contabilidad Regulatoria
 * Monitor Financiero Chile
 * Detalla el significado, tipo, rol y criterio contable de cada columna en el sistema.
 * Criterios contables:
 *   - Valor Razonable / MtM (Mark-to-Market)
 *   - Valor de Mercado Bruto
 *   - Valor de Mercado Neto
 *   - Costo Amortizado / Devengado
 *   - Avaluo Fiscal vs Tasacion Comercial
 *   - Pacto Activo (CRV) / Pasivo (VRC)
 *   - No aplica (Identificadores, Fechas, Categorias)
 */

const DATA_DICTIONARY = [
  {
    id: "seguros_maestro",
    name: "seguros.lista_entidades",
    viewName: "seguros_maestro",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Una fila por compañía y sector",
    descripcion: "Compañías de seguros de vida y generales que envían su cartera a la CMF, con el primer y el último mes informado. Sirve para detectar compañías nuevas y las que dejan de reportar.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "PK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "primer_periodo", type: "VARCHAR", role: "Fecha", significado: "Primer mes en que la compañía aparece en los archivos publicados.", contable: "No aplica" },
      { name: "ultimo_periodo", type: "VARCHAR", role: "Fecha", significado: "Último mes en que la compañía aparece.", contable: "No aplica" },
      { name: "meses_reportados", type: "BIGINT", role: "Métrica", significado: "Número de meses publicados en que aparece.", contable: "No aplica" },
      { name: "reporta_ultimo_mes", type: "BOOLEAN", role: "Atributo", significado: "Verdadero si aparece en el último mes publicado.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_renta_fija",
    name: "seguros.renta_fija",
    viewName: "seguros_renta_fija",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2024-12 (ampliable)",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Bonos, letras, depósitos y demás instrumentos de renta fija nacionales, uno por fila, con sus tasas, costo amortizado, valor razonable y valor final.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Código del tipo de instrumento según la ficha técnica de la CMF.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico o código del instrumento.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Serie del instrumento.", contable: "No aplica" },
      { name: "rut_emisor", type: "VARCHAR", role: "Atributo", significado: "RUT del emisor.", contable: "No aplica" },
      { name: "pais", type: "VARCHAR", role: "Atributo", significado: "País del emisor o de la inversión.", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Fecha de compra (AAAA-MM-DD).", contable: "No aplica" },
      { name: "fecha_emision", type: "VARCHAR", role: "Fecha", significado: "Fecha de emisión (AAAA-MM-DD).", contable: "No aplica" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha de vencimiento (AAAA-MM-DD).", contable: "No aplica" },
      { name: "unidad_monetaria", type: "VARCHAR", role: "Atributo", significado: "Unidad o moneda en que está expresado el instrumento (UF, $$, PROM, USD...).", contable: "No aplica" },
      { name: "valor_nominal", type: "DOUBLE", role: "Métrica", significado: "Valor nominal en la unidad del instrumento.", contable: "No aplica" },
      { name: "tasa_emision_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de emisión (%).", contable: "No aplica" },
      { name: "tir_compra_pct", type: "DOUBLE", role: "Métrica", significado: "TIR de compra (%).", contable: "No aplica" },
      { name: "tir_mercado_pct", type: "DOUBLE", role: "Métrica", significado: "TIR de mercado al cierre (%).", contable: "No aplica" },
      { name: "valor_compra_clp", type: "BIGINT", role: "Métrica", significado: "Valor de compra, en pesos.", contable: "No aplica" },
      { name: "costo_amortizado_clp", type: "BIGINT", role: "Métrica", significado: "Costo amortizado, en pesos.", contable: "Costo amortizado" },
      { name: "valor_razonable_clp", type: "BIGINT", role: "Métrica", significado: "Valor razonable, en pesos.", contable: "Valor razonable" },
      { name: "deterioro_clp", type: "BIGINT", role: "Métrica", significado: "Deterioro, en pesos.", contable: "Deterioro" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor final informado, en miles de pesos (M$).", contable: "Valor contable informado" },
      { name: "custodia", type: "VARCHAR", role: "Atributo", significado: "Dónde está custodiado (DCV, compañía, extranjero...).", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_acciones",
    name: "seguros.acciones",
    viewName: "seguros_acciones",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Acciones de sociedades anónimas y cuotas de fondos de inversión nacionales.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Código del tipo de instrumento según la ficha técnica de la CMF.", contable: "No aplica" },
      { name: "rut_emisor", type: "VARCHAR", role: "Atributo", significado: "RUT del emisor.", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "Atributo", significado: "RUN del fondo.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico o código del instrumento.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Serie del instrumento.", contable: "No aplica" },
      { name: "unidades", type: "DOUBLE", role: "Métrica", significado: "Número de acciones o cuotas.", contable: "No aplica" },
      { name: "presencia_bursatil_pct", type: "DOUBLE", role: "Métrica", significado: "Presencia bursátil (%).", contable: "No aplica" },
      { name: "valor_costo_clp", type: "BIGINT", role: "Métrica", significado: "Costo, en pesos.", contable: "No aplica" },
      { name: "valor_bolsa_clp", type: "BIGINT", role: "Métrica", significado: "Valor bolsa, en pesos.", contable: "No aplica" },
      { name: "valor_razonable_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor razonable, en miles de pesos (M$).", contable: "Valor razonable" },
      { name: "deterioro_m_clp", type: "BIGINT", role: "Métrica", significado: "Deterioro, en miles de pesos (M$).", contable: "Deterioro" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor final informado, en miles de pesos (M$).", contable: "Valor contable informado" },
      { name: "unidad_monetaria", type: "VARCHAR", role: "Atributo", significado: "Unidad o moneda en que está expresado el instrumento (UF, $$, PROM, USD...).", contable: "No aplica" },
      { name: "custodia", type: "VARCHAR", role: "Atributo", significado: "Dónde está custodiado (DCV, compañía, extranjero...).", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_fondos_mutuos",
    name: "seguros.fondos_mutuos",
    viewName: "seguros_fondos_mutuos",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Cuotas de fondos mutuos nacionales.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Código del tipo de instrumento según la ficha técnica de la CMF.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "Atributo", significado: "RUT de la administradora del fondo.", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "Atributo", significado: "RUN del fondo.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico o código del instrumento.", contable: "No aplica" },
      { name: "tipo_fondo", type: "VARCHAR", role: "Atributo", significado: "Tipo de fondo mutuo.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Serie del instrumento.", contable: "No aplica" },
      { name: "unidades", type: "DOUBLE", role: "Métrica", significado: "Número de acciones o cuotas.", contable: "No aplica" },
      { name: "unidad_monetaria", type: "VARCHAR", role: "Atributo", significado: "Unidad o moneda en que está expresado el instrumento (UF, $$, PROM, USD...).", contable: "No aplica" },
      { name: "valor_cuota", type: "DOUBLE", role: "Métrica", significado: "Valor cuota al cierre.", contable: "No aplica" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor final informado, en miles de pesos (M$).", contable: "Valor contable informado" },
      { name: "custodia", type: "VARCHAR", role: "Atributo", significado: "Dónde está custodiado (DCV, compañía, extranjero...).", contable: "No aplica" },
      { name: "clasificacion_riesgo", type: "VARCHAR", role: "Atributo", significado: "Clasificación de riesgo.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_bienes_raices",
    name: "seguros.bienes_raices",
    viewName: "seguros_bienes_raices",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2024-12 (ampliable)",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Bienes raíces por rol: dirección, arriendo, costo, depreciación, tasaciones y valor final.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "rol", type: "VARCHAR", role: "Atributo", significado: "Rol de avalúo del inmueble.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Código del tipo de instrumento según la ficha técnica de la CMF.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico o código del instrumento.", contable: "No aplica" },
      { name: "direccion", type: "VARCHAR", role: "Atributo", significado: "Dirección del inmueble.", contable: "No aplica" },
      { name: "codigo_comuna", type: "VARCHAR", role: "Atributo", significado: "Código de comuna.", contable: "No aplica" },
      { name: "ciudad", type: "VARCHAR", role: "Atributo", significado: "Ciudad.", contable: "No aplica" },
      { name: "monto_arriendo_uf", type: "DOUBLE", role: "Métrica", significado: "Arriendo mensual, en UF.", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Fecha de compra (AAAA-MM-DD).", contable: "No aplica" },
      { name: "costo_m_clp", type: "BIGINT", role: "Métrica", significado: "Costo del inmueble, en miles de pesos (M$).", contable: "No aplica" },
      { name: "depreciacion_m_clp", type: "BIGINT", role: "Métrica", significado: "Depreciación acumulada, en miles de pesos (M$).", contable: "No aplica" },
      { name: "costo_corregido_m_clp", type: "BIGINT", role: "Métrica", significado: "Costo corregido, en miles de pesos (M$).", contable: "No aplica" },
      { name: "tasacion_1_m_clp", type: "BIGINT", role: "Métrica", significado: "Primera tasación, en miles de pesos (M$).", contable: "No aplica" },
      { name: "tasacion_2_m_clp", type: "BIGINT", role: "Métrica", significado: "Segunda tasación, en miles de pesos (M$).", contable: "No aplica" },
      { name: "deterioro_m_clp", type: "BIGINT", role: "Métrica", significado: "Deterioro, en miles de pesos (M$).", contable: "Deterioro" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor final informado, en miles de pesos (M$).", contable: "Valor contable informado" }
    ]
  },
  {
    id: "seguros_extranjeros",
    name: "seguros.extranjeros",
    viewName: "seguros_extranjeros",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Inversiones en el extranjero: deuda (tipo_registro = 'deuda') y acciones y fondos (tipo_registro = 'acciones_y_fondos').",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "tipo_registro", type: "VARCHAR", role: "Atributo", significado: "Subtipo de registro de la ficha (p. ej. forward, swap, deuda).", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Código del tipo de instrumento según la ficha técnica de la CMF.", contable: "No aplica" },
      { name: "valor_nominal", type: "DOUBLE", role: "Métrica", significado: "Valor nominal en la unidad del instrumento.", contable: "No aplica" },
      { name: "pais", type: "VARCHAR", role: "Atributo", significado: "País del emisor o de la inversión.", contable: "No aplica" },
      { name: "emisor", type: "VARCHAR", role: "Atributo", significado: "Nombre del emisor extranjero.", contable: "No aplica" },
      { name: "codigo", type: "VARCHAR", role: "Atributo", significado: "Código del instrumento extranjero (ISIN u otro).", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda del contrato o del activo.", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Fecha de compra (AAAA-MM-DD).", contable: "No aplica" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha de vencimiento (AAAA-MM-DD).", contable: "No aplica" },
      { name: "tasa_emision_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de emisión (%).", contable: "No aplica" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor final informado, en miles de pesos (M$).", contable: "Valor contable informado" },
      { name: "clasificacion_riesgo", type: "VARCHAR", role: "Atributo", significado: "Clasificación de riesgo.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Serie del instrumento.", contable: "No aplica" },
      { name: "unidades", type: "DOUBLE", role: "Métrica", significado: "Número de acciones o cuotas.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_derivados",
    name: "seguros.derivados",
    viewName: "seguros_derivados",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Contratos de opciones, forwards, futuros y swaps (tipo_registro), con contraparte, nocional, valor razonable y efecto en resultados.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "tipo_registro", type: "VARCHAR", role: "Atributo", significado: "Subtipo de registro de la ficha (p. ej. forward, swap, deuda).", contable: "No aplica" },
      { name: "objetivo", type: "VARCHAR", role: "Atributo", significado: "Objetivo del derivado (cobertura, inversión...).", contable: "No aplica" },
      { name: "tipo_operacion", type: "VARCHAR", role: "Atributo", significado: "Tipo de operación según la ficha.", contable: "No aplica" },
      { name: "folio", type: "VARCHAR", role: "Atributo", significado: "Folio de la operación.", contable: "No aplica" },
      { name: "item", type: "VARCHAR", role: "Atributo", significado: "Ítem dentro del folio.", contable: "No aplica" },
      { name: "fecha_operacion", type: "VARCHAR", role: "Fecha", significado: "Fecha de la operación (AAAA-MM-DD).", contable: "No aplica" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha de vencimiento (AAAA-MM-DD).", contable: "No aplica" },
      { name: "contraparte", type: "VARCHAR", role: "Atributo", significado: "Nombre de la contraparte.", contable: "No aplica" },
      { name: "nacionalidad_contraparte", type: "VARCHAR", role: "Atributo", significado: "Nacionalidad de la contraparte.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Indica si la contraparte es relacionada.", contable: "No aplica" },
      { name: "clasificacion_riesgo", type: "VARCHAR", role: "Atributo", significado: "Clasificación de riesgo.", contable: "No aplica" },
      { name: "activo_objeto_largo", type: "VARCHAR", role: "Atributo", significado: "Activo objeto de la posición larga.", contable: "No aplica" },
      { name: "activo_objeto_corto", type: "VARCHAR", role: "Atributo", significado: "Activo objeto de la posición corta.", contable: "No aplica" },
      { name: "nocional_largo", type: "DOUBLE", role: "Métrica", significado: "Nocional de la posición larga.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda del contrato o del activo.", contable: "No aplica" },
      { name: "valor_razonable_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor razonable, en miles de pesos (M$).", contable: "Valor razonable" },
      { name: "origen_valorizacion", type: "VARCHAR", role: "Atributo", significado: "Fuente de la valorización.", contable: "No aplica" },
      { name: "efecto_resultados_m_clp", type: "BIGINT", role: "Métrica", significado: "Efecto en resultados, en miles de pesos (M$).", contable: "No aplica" },
      { name: "nocional_corto", type: "DOUBLE", role: "Métrica", significado: "Nocional de la posición corta.", contable: "No aplica" },
      { name: "moneda_larga", type: "VARCHAR", role: "Atributo", significado: "Moneda de la pata larga (swaps).", contable: "No aplica" },
      { name: "moneda_corta", type: "VARCHAR", role: "Atributo", significado: "Moneda de la pata corta (swaps).", contable: "No aplica" },
      { name: "tasa_larga", type: "VARCHAR", role: "Atributo", significado: "Tasa de la pata larga (swaps).", contable: "No aplica" },
      { name: "tasa_corta", type: "VARCHAR", role: "Atributo", significado: "Tasa de la pata corta (swaps).", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_pactos",
    name: "seguros.pactos",
    viewName: "seguros_pactos",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Compras y ventas con pacto (repos), con contraparte, tasa y activo objeto.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "tipo_operacion", type: "VARCHAR", role: "Atributo", significado: "Tipo de operación según la ficha.", contable: "No aplica" },
      { name: "folio", type: "VARCHAR", role: "Atributo", significado: "Folio de la operación.", contable: "No aplica" },
      { name: "item", type: "VARCHAR", role: "Atributo", significado: "Ítem dentro del folio.", contable: "No aplica" },
      { name: "fecha_operacion", type: "VARCHAR", role: "Fecha", significado: "Fecha de la operación (AAAA-MM-DD).", contable: "No aplica" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha de vencimiento (AAAA-MM-DD).", contable: "No aplica" },
      { name: "tasa_pacto_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa del pacto (%).", contable: "No aplica" },
      { name: "contraparte", type: "VARCHAR", role: "Atributo", significado: "Nombre de la contraparte.", contable: "No aplica" },
      { name: "nacionalidad_contraparte", type: "VARCHAR", role: "Atributo", significado: "Nacionalidad de la contraparte.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Indica si la contraparte es relacionada.", contable: "No aplica" },
      { name: "activo_objeto", type: "VARCHAR", role: "Atributo", significado: "Instrumento objeto del pacto.", contable: "No aplica" },
      { name: "serie_activo_objeto", type: "VARCHAR", role: "Atributo", significado: "Serie del instrumento objeto.", contable: "No aplica" },
      { name: "rut_emisor_activo_objeto", type: "VARCHAR", role: "Atributo", significado: "RUT del emisor del instrumento objeto.", contable: "No aplica" },
      { name: "valor_nominal", type: "DOUBLE", role: "Métrica", significado: "Valor nominal en la unidad del instrumento.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda del contrato o del activo.", contable: "No aplica" },
      { name: "interes_devengado_m_clp", type: "BIGINT", role: "Métrica", significado: "Interés devengado, en miles de pesos (M$).", contable: "No aplica" },
      { name: "valor_contable_m_clp", type: "BIGINT", role: "Métrica", significado: "Valorización del pacto al cierre, en miles de pesos (M$).", contable: "No aplica" },
      { name: "valor_mercado_activo_objeto_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor de mercado del activo objeto, en miles de pesos (M$).", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_control_inversiones",
    name: "seguros.control_inversiones",
    viewName: "seguros_control_inversiones",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    descripcion: "Información de control que cada compañía envía con su cartera: totales por tipo de inversión (valor final, representativas y no representativas de reservas, etc.).",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida o generales.", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el archivo del mes.", contable: "No aplica" },
      { name: "tipo_inversion", type: "VARCHAR", role: "Atributo", significado: "Código del tipo de inversión en la información de control.", contable: "No aplica" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Valor final informado, en miles de pesos (M$).", contable: "Valor contable informado" },
      { name: "inversiones_representativas_m_clp", type: "BIGINT", role: "Métrica", significado: "Inversiones representativas de reservas, en M$.", contable: "No aplica" },
      { name: "inversiones_no_representativas_m_clp", type: "BIGINT", role: "Métrica", significado: "Inversiones no representativas de reservas, en M$.", contable: "No aplica" },
      { name: "total_costo_amortizado_m_clp", type: "BIGINT", role: "Métrica", significado: "Total a costo amortizado, en M$.", contable: "Costo amortizado" },
      { name: "total_valor_razonable_m_clp", type: "BIGINT", role: "Métrica", significado: "Total a valor razonable, en M$.", contable: "Valor razonable" },
      { name: "total_efectivo_equivalente_m_clp", type: "BIGINT", role: "Métrica", significado: "Total efectivo equivalente, en M$.", contable: "No aplica" },
      { name: "total_cui_apv_m_clp", type: "BIGINT", role: "Métrica", significado: "Total de inversiones de seguros con cuenta única de inversión (CUI) y APV, en M$.", contable: "No aplica" },
      { name: "total_otra_clasificacion_m_clp", type: "BIGINT", role: "Métrica", significado: "Total en otra clasificación, en M$.", contable: "No aplica" },
      { name: "total_filiales_m_clp", type: "BIGINT", role: "Métrica", significado: "Total en filiales, en M$.", contable: "No aplica" },
      { name: "total_coligadas_m_clp", type: "BIGINT", role: "Métrica", significado: "Total en coligadas, en M$.", contable: "No aplica" }
    ]
  },
  // BEGIN AUTO FL IFRS SERIES DICTIONARY
  {"sector":"factoring_leasing","sectorLabel":"Factoring & Leasing","norma":"CMF IFRS TXT · extracción automática de cuentas ESF/ER","corte":"2009-03 a 2026-06 · 70 cierres","frescura":"Serie de la fuente CMF; valores crudos, no validación integral","modo":"Actions: descarga histórica incremental y publicación automática al completarse","ultimaActualizacion":"2026-09-27","origen":"CMF https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php; corrida Actions 36340943560. 24/28 RUT de catálogo presentes. Incluye cuentas repetidas y valores no enteros; no convertir, deduplicar ni sumar sin criterio. No cotejo integral de estados.","columnas":[{"name":"periodo","type":"VARCHAR","role":"Dimensión","significado":"Cierre informado por CMF, AAAA-MM.","contable":"No aplica"},{"name":"rut_cuerpo","type":"VARCHAR","role":"Dimensión","significado":"Identificador de 8 dígitos (sin DV) literal del TXT; rut actual proviene del catálogo.","contable":"No aplica"},{"name":"rut","type":"VARCHAR","role":"Dimensión","significado":"Unión al RUT actual del catálogo por cuerpo; no certifica vigencia ni identidad histórica.","contable":"No aplica"},{"name":"nombre_reportado","type":"VARCHAR","role":"Dimensión","significado":"Nombre reportado por CMF en ese período.","contable":"No aplica"},{"name":"segmento_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Segmento consignado en el catálogo actual; puede incluir entidades mixtas/automotrices.","contable":"No aplica"},{"name":"nombre_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Nombre del catálogo actual; puede diferir del nombre histórico.","contable":"No aplica"},{"name":"tipo_balance","type":"VARCHAR","role":"Dimensión","significado":"I individual / C consolidado. Se preservan separados; no sumar.","contable":"No aplica"},{"name":"moneda_archivo","type":"VARCHAR","role":"Dimensión","significado":"Moneda original, sin conversión.","contable":"No aplica"},{"name":"cuenta","type":"VARCHAR","role":"Dimensión","significado":"Etiqueta literal de cuenta reportada.","contable":"No aplica"},{"name":"valor_archivo","type":"BIGINT","role":"Métrica","significado":"Entero original cuando pudo leerse como entero; NULL para valores no enteros.","contable":"No aplica"},{"name":"valor_texto_original","type":"VARCHAR","role":"Métrica","significado":"Texto literal de la cifra, preservado siempre.","contable":"No aplica"},{"name":"valor_es_entero","type":"BOOLEAN","role":"Dimensión","significado":"Control de interpretación numérica; false no significa cero.","contable":"No aplica"},{"name":"taxonomia","type":"VARCHAR","role":"Dimensión","significado":"Código literal de taxonomía CMF.","contable":"No aplica"},{"name":"estado_financiero","type":"VARCHAR","role":"Dimensión","significado":"Código CMF del estado: ESF C/NC = situación financiera; ERFG = resultados por función; ERNG = resultados por naturaleza; ERI = resultado integral.","contable":"No aplica"},{"name":"repeticion_contexto","type":"BIGINT","role":"Dimensión","significado":"Ordinal de la misma etiqueta dentro del estado; se conserva sin sumar. En resultados, \"Ganancia (pérdida)\" aparece en ERFG/ERNG con ordinal 1 y 2 y otra vez al inicio de ERI, con el mismo valor: para la utilidad del período usar estado ERFG/ERNG y ordinal 1.","contable":"No aplica"},{"name":"fuente_archivo","type":"VARCHAR","role":"Dimensión","significado":"URL pública CMF que originó la fila.","contable":"No aplica"},{"name":"sha256_archivo","type":"VARCHAR","role":"Dimensión","significado":"Huella de la descarga usada.","contable":"No aplica"},{"name":"identidad_nombre_coincide_catalogo","type":"BOOLEAN","role":"Dimensión","significado":"Coincidencia de nombre normalizada; señal, no auditoría histórica.","contable":"No aplica"}],"id":"factoring_leasing_balance_serie_ifrs_cmf","name":"factoring_leasing.balance_serie_ifrs_cmf","viewName":"factoring_leasing_balance_serie_ifrs_cmf","registros":"28,938 cuentas · 24/28 RUT con datos","descripcion":"Balance IFRS CMF · serie histórica. 28,938 filas de cuentas de estados ESF entre 2009-03 a 2026-06; no son estados agregados. Incluye 2,426 importes no enteros preservados como texto/null y 902 repeticiones de contexto conservadas. Monedas, taxonomías y tipos I/C permanecen separados; sin conversión, deduplicación ni suma. Cifras no cotejadas en su totalidad."},
  {"sector":"factoring_leasing","sectorLabel":"Factoring & Leasing","norma":"CMF IFRS TXT · extracción automática de cuentas ESF/ER","corte":"2009-03 a 2026-06 · 70 cierres","frescura":"Serie de la fuente CMF; valores crudos, no validación integral","modo":"Actions: descarga histórica incremental y publicación automática al completarse","ultimaActualizacion":"2026-09-27","origen":"CMF https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php; corrida Actions 36340943560. 24/28 RUT de catálogo presentes. Incluye cuentas repetidas y valores no enteros; no convertir, deduplicar ni sumar sin criterio. No cotejo integral de estados.","columnas":[{"name":"periodo","type":"VARCHAR","role":"Dimensión","significado":"Cierre informado por CMF, AAAA-MM.","contable":"No aplica"},{"name":"rut_cuerpo","type":"VARCHAR","role":"Dimensión","significado":"Identificador de 8 dígitos (sin DV) literal del TXT; rut actual proviene del catálogo.","contable":"No aplica"},{"name":"rut","type":"VARCHAR","role":"Dimensión","significado":"Unión al RUT actual del catálogo por cuerpo; no certifica vigencia ni identidad histórica.","contable":"No aplica"},{"name":"nombre_reportado","type":"VARCHAR","role":"Dimensión","significado":"Nombre reportado por CMF en ese período.","contable":"No aplica"},{"name":"segmento_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Segmento consignado en el catálogo actual; puede incluir entidades mixtas/automotrices.","contable":"No aplica"},{"name":"nombre_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Nombre del catálogo actual; puede diferir del nombre histórico.","contable":"No aplica"},{"name":"tipo_balance","type":"VARCHAR","role":"Dimensión","significado":"I individual / C consolidado. Se preservan separados; no sumar.","contable":"No aplica"},{"name":"moneda_archivo","type":"VARCHAR","role":"Dimensión","significado":"Moneda original, sin conversión.","contable":"No aplica"},{"name":"cuenta","type":"VARCHAR","role":"Dimensión","significado":"Etiqueta literal de cuenta reportada.","contable":"No aplica"},{"name":"valor_archivo","type":"BIGINT","role":"Métrica","significado":"Entero original cuando pudo leerse como entero; NULL para valores no enteros.","contable":"No aplica"},{"name":"valor_texto_original","type":"VARCHAR","role":"Métrica","significado":"Texto literal de la cifra, preservado siempre.","contable":"No aplica"},{"name":"valor_es_entero","type":"BOOLEAN","role":"Dimensión","significado":"Control de interpretación numérica; false no significa cero.","contable":"No aplica"},{"name":"taxonomia","type":"VARCHAR","role":"Dimensión","significado":"Código literal de taxonomía CMF.","contable":"No aplica"},{"name":"estado_financiero","type":"VARCHAR","role":"Dimensión","significado":"Código CMF del estado: ESF C/NC = situación financiera; ERFG = resultados por función; ERNG = resultados por naturaleza; ERI = resultado integral.","contable":"No aplica"},{"name":"repeticion_contexto","type":"BIGINT","role":"Dimensión","significado":"Ordinal de la misma etiqueta dentro del estado; se conserva sin sumar. En resultados, \"Ganancia (pérdida)\" aparece en ERFG/ERNG con ordinal 1 y 2 y otra vez al inicio de ERI, con el mismo valor: para la utilidad del período usar estado ERFG/ERNG y ordinal 1.","contable":"No aplica"},{"name":"fuente_archivo","type":"VARCHAR","role":"Dimensión","significado":"URL pública CMF que originó la fila.","contable":"No aplica"},{"name":"sha256_archivo","type":"VARCHAR","role":"Dimensión","significado":"Huella de la descarga usada.","contable":"No aplica"},{"name":"identidad_nombre_coincide_catalogo","type":"BOOLEAN","role":"Dimensión","significado":"Coincidencia de nombre normalizada; señal, no auditoría histórica.","contable":"No aplica"}],"id":"factoring_leasing_resultados_serie_ifrs_cmf","name":"factoring_leasing.resultados_serie_ifrs_cmf","viewName":"factoring_leasing_resultados_serie_ifrs_cmf","registros":"21,464 cuentas · 24/28 RUT con datos","descripcion":"Resultados IFRS CMF · serie histórica. 21,464 filas de cuentas de estados ER entre 2009-03 a 2026-06; no son estados agregados. Incluye 2,426 importes no enteros preservados como texto/null y 902 repeticiones de contexto conservadas. Monedas, taxonomías y tipos I/C permanecen separados; sin conversión, deduplicación ni suma. Cifras no cotejadas en su totalidad."},
  // END AUTO FL IFRS SERIES DICTIONARY
  {
    id: "ffmm_eeff_xml_muestra_cmf",
    name: "ffmm.eeff_xml_muestra_cmf",
    viewName: "ffmm_eeff_xml_muestra_cmf",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "Estados financieros IFRS/XML CMF · cotejo de muestra",
    corte: "2014-12",
    frescura: "Muestra histórica de 1 fila; no es serie completa",
    modo: "XML cotejado contra tabla HTML oficial CMF",
    ultimaActualizacion: "2026-09-27",
    registros: "1 fondo / 1 período",
    descripcion: "Una fila por industria cotejada en CMF: cuatro cifras de balance y resultado iguales al XML. No extrapolar la aprobación a otros fondos, períodos ni monedas.",
    origen: "CMF, ficha individual (tabla HTML) y XML del mismo período; comprobante Actions 36332905593. Ver docs/notas/cotejo_muestra_xml_ffmm_fi_2026-09-27.md.",
    columnas: [
      { name: "run_fondo", type: "VARCHAR", role: "PK", significado: "RUN CMF del fondo; no usar el nombre actual como identificador histórico.", contable: "No aplica" },
      { name: "tipo_entidad", type: "VARCHAR", role: "Dimensión", significado: "RGFMU (fondo mutuo) o FIRES (fondo de inversión rescatable).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Cierre de la única fila cotejada, formato AAAA-MM.", contable: "No aplica" },
      { name: "nombre_xml_historico", type: "VARCHAR", role: "Atributo", significado: "Nombre tal como lo declara el XML del período; puede diferir del actual.", contable: "No aplica" },
      { name: "nombre_registro_actual", type: "VARCHAR", role: "Atributo", significado: "Nombre en el registro de entidades actual de CMF; no reemplaza al histórico.", contable: "No aplica" },
      { name: "moneda_original_xml", type: "VARCHAR", role: "Dimensión", significado: "Código de moneda literal del XML: $$ o PROM; no implica conversión.", contable: "No aplica" },
      { name: "unidad_segun_ficha_cmf", type: "VARCHAR", role: "Dimensión", significado: "Unidad monetaria indicada en la ficha financiera oficial del mismo corte.", contable: "No aplica" },
      { name: "total_activo", type: "DOUBLE", role: "Métrica", significado: "Total Activo del XML cotejado exactamente con tabla HTML CMF.", contable: "No aplica" },
      { name: "total_pasivo_reportado", type: "DOUBLE", role: "Métrica", significado: "Total Pasivo según la taxonomía del sector: FI incluye patrimonio; FFMM lo excluye.", contable: "No aplica" },
      { name: "definicion_total_pasivo", type: "VARCHAR", role: "Dimensión", significado: "Indica si Total Pasivo incluye patrimonio; evita sumar dos veces.", contable: "No aplica" },
      { name: "pasivo_sin_patrimonio", type: "DOUBLE", role: "Métrica", significado: "FFMM: pasivo reportado; FI: total activo menos patrimonio (61 en la muestra).", contable: "No aplica" },
      { name: "patrimonio_o_activo_neto", type: "DOUBLE", role: "Métrica", significado: "FI: patrimonio neto; FFMM: activo neto atribuible a partícipes.", contable: "No aplica" },
      { name: "resultado_ejercicio", type: "DOUBLE", role: "Métrica", significado: "Resultado acumulado del ejercicio cotejado con la tabla HTML CMF.", contable: "No aplica" },
      { name: "codigo_resultado_xml", type: "VARCHAR", role: "Atributo", significado: "Código exacto de la cuenta de resultado en el XML.", contable: "No aplica" },
      { name: "dv_xml_coincide", type: "BOOLEAN", role: "Auditoría", significado: "DV informado en XML coincide con el del RUN.", contable: "No aplica" },
      { name: "parseo_reparado", type: "BOOLEAN", role: "Auditoría", significado: "Falso en ambas filas: XML original parseado sin saneo.", contable: "No aplica" },
      { name: "fuente_ficha_cmf", type: "VARCHAR", role: "Fuente", significado: "URL de la ficha financiera CMF del corte.", contable: "No aplica" },
      { name: "fuente_xml_cmf", type: "VARCHAR", role: "Fuente", significado: "URL del XML CMF original sin tokens efímeros.", contable: "No aplica" },
      { name: "sha256_xml", type: "VARCHAR", role: "Auditoría", significado: "SHA256 del XML original cotejado.", contable: "No aplica" },
      { name: "run_cotejo_actions", type: "BIGINT", role: "Auditoría", significado: "Identificador de la corrida Actions que descargó y cotejó la muestra.", contable: "No aplica" },
      { name: "alcance_validacion", type: "VARCHAR", role: "Auditoría", significado: "Solo la fila correspondiente: no certifica el resto del universo.", contable: "No aplica" },
    ]
  },
  {
    id: "fi_eeff_xml_muestra_cmf",
    name: "fi.eeff_xml_muestra_cmf",
    viewName: "fi_eeff_xml_muestra_cmf",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "Estados financieros IFRS/XML CMF · cotejo de muestra",
    corte: "2021-12",
    frescura: "Muestra histórica de 1 fila; no es serie completa",
    modo: "XML cotejado contra tabla HTML oficial CMF",
    ultimaActualizacion: "2026-09-27",
    registros: "1 fondo / 1 período",
    descripcion: "Una fila por industria cotejada en CMF: cuatro cifras de balance y resultado iguales al XML. No extrapolar la aprobación a otros fondos, períodos ni monedas.",
    origen: "CMF, ficha individual (tabla HTML) y XML del mismo período; comprobante Actions 36332905593. Ver docs/notas/cotejo_muestra_xml_ffmm_fi_2026-09-27.md.",
    columnas: [
      { name: "run_fondo", type: "VARCHAR", role: "PK", significado: "RUN CMF del fondo; no usar el nombre actual como identificador histórico.", contable: "No aplica" },
      { name: "tipo_entidad", type: "VARCHAR", role: "Dimensión", significado: "RGFMU (fondo mutuo) o FIRES (fondo de inversión rescatable).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Cierre de la única fila cotejada, formato AAAA-MM.", contable: "No aplica" },
      { name: "nombre_xml_historico", type: "VARCHAR", role: "Atributo", significado: "Nombre tal como lo declara el XML del período; puede diferir del actual.", contable: "No aplica" },
      { name: "nombre_registro_actual", type: "VARCHAR", role: "Atributo", significado: "Nombre en el registro de entidades actual de CMF; no reemplaza al histórico.", contable: "No aplica" },
      { name: "moneda_original_xml", type: "VARCHAR", role: "Dimensión", significado: "Código de moneda literal del XML: $$ o PROM; no implica conversión.", contable: "No aplica" },
      { name: "unidad_segun_ficha_cmf", type: "VARCHAR", role: "Dimensión", significado: "Unidad monetaria indicada en la ficha financiera oficial del mismo corte.", contable: "No aplica" },
      { name: "total_activo", type: "DOUBLE", role: "Métrica", significado: "Total Activo del XML cotejado exactamente con tabla HTML CMF.", contable: "No aplica" },
      { name: "total_pasivo_reportado", type: "DOUBLE", role: "Métrica", significado: "Total Pasivo según la taxonomía del sector: FI incluye patrimonio; FFMM lo excluye.", contable: "No aplica" },
      { name: "definicion_total_pasivo", type: "VARCHAR", role: "Dimensión", significado: "Indica si Total Pasivo incluye patrimonio; evita sumar dos veces.", contable: "No aplica" },
      { name: "pasivo_sin_patrimonio", type: "DOUBLE", role: "Métrica", significado: "FFMM: pasivo reportado; FI: total activo menos patrimonio (61 en la muestra).", contable: "No aplica" },
      { name: "patrimonio_o_activo_neto", type: "DOUBLE", role: "Métrica", significado: "FI: patrimonio neto; FFMM: activo neto atribuible a partícipes.", contable: "No aplica" },
      { name: "resultado_ejercicio", type: "DOUBLE", role: "Métrica", significado: "Resultado acumulado del ejercicio cotejado con la tabla HTML CMF.", contable: "No aplica" },
      { name: "codigo_resultado_xml", type: "VARCHAR", role: "Atributo", significado: "Código exacto de la cuenta de resultado en el XML.", contable: "No aplica" },
      { name: "dv_xml_coincide", type: "BOOLEAN", role: "Auditoría", significado: "DV informado en XML coincide con el del RUN.", contable: "No aplica" },
      { name: "parseo_reparado", type: "BOOLEAN", role: "Auditoría", significado: "Falso en ambas filas: XML original parseado sin saneo.", contable: "No aplica" },
      { name: "fuente_ficha_cmf", type: "VARCHAR", role: "Fuente", significado: "URL de la ficha financiera CMF del corte.", contable: "No aplica" },
      { name: "fuente_xml_cmf", type: "VARCHAR", role: "Fuente", significado: "URL del XML CMF original sin tokens efímeros.", contable: "No aplica" },
      { name: "sha256_xml", type: "VARCHAR", role: "Auditoría", significado: "SHA256 del XML original cotejado.", contable: "No aplica" },
      { name: "run_cotejo_actions", type: "BIGINT", role: "Auditoría", significado: "Identificador de la corrida Actions que descargó y cotejó la muestra.", contable: "No aplica" },
      { name: "alcance_validacion", type: "VARCHAR", role: "Auditoría", significado: "Solo la fila correspondiente: no certifica el resto del universo.", contable: "No aplica" },
    ]
  },
  {
    id: "fi_maestro",
    name: "fi.lista_entidades",
    viewName: "fi_maestro",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "Cartera de Inversión (CMF)",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "1.129 entidades",
    descripcion: "Maestro de Fondos de Inversión públicos y privados (FINRE y FIRES).",
    origen: "CMF — Registro Público de Fondos de Inversión Públicos y Privados (FINRE y FIRES) y Sociedades Administradoras Generales de Fondos (AGF).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Identificador surrogate único del fondo (FI_RUN).", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "Atributo", significado: "RUN único del fondo asignado por la CMF.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Nombre registrado del fondo de inversión.", contable: "No aplica" },
      { name: "categoria_fondo", type: "VARCHAR", role: "Atributo", significado: "Tipo de fondo: Rescatable (FINRE) o No Rescatable (FIRES).", contable: "No aplica" }
    ]
  },
  {
    id: "fi_nacional",
    name: "fi.cartera_nacional",
    viewName: "fi_nacional",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "Cartera de Inversión / IFRS CMF",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "833.584 registros",
    descripcion: "Detalle de cartera de instrumentos nacionales en fondos de inversión bajo normas contables IFRS.",
    origen: "CMF — Carteras Trimestrales de Fondos de Inversión (Reporte normativo de títulos de deuda y capital nacional bajo IFRS).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Surrogate PK del activo nacional en cartera.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo trimestral reportado.", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "FK", significado: "RUN del fondo titular del activo.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico o código del instrumento.", contable: "No aplica" },
      { name: "rut_emisor", type: "VARCHAR", role: "Atributo", significado: "RUT de la entidad emisora del título.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Categoría del activo (Acciones, Bonos, Pagarés, Cuotas).", contable: "No aplica" },
      { name: "valolizacion_al_cierre", type: "DOUBLE", role: "Métrica", significado: "Valorización total del instrumento al cierre en miles de CLP.", contable: "Valor Razonable / MtM" }
    ]
  },
  {
    id: "fi_repos",
    name: "fi.repos_vrc_crv",
    viewName: "fi_repos",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "CMF VRC / CRV IFRS",
    corte: "2026-03",
    frescura: "Al dia (2014-03 a 2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    advertencia: "Falta auditar la cobertura, los montos y la unidad de esta tabla contra los informes originales de la CMF. Pertenece a la misma tarjeta en revisión que la muestra de contratos, así que sus saldos no deben sumarse ni publicarse como cifra de mercado.",
    registros: "1.366 pactos",
    descripcion: "Operaciones de Venta con Compromiso de Retrocompra (VRC) y Compra con Retroventa (CRV) de 37 fondos de inversión.",
    origen: "CMF — Registro de Operaciones con Pacto de Fondos de Inversión (Reportes de operaciones VRC y CRV a través de AGFs).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Surrogate PK determinística (FI_REPO_RUN_PERIODO_IDX).", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "FK", significado: "RUN oficial del fondo de inversión titular del pacto.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Trimestre de corte del informe CMF (201403 a 202603).", contable: "No aplica" },
      { name: "codigo_operacion", type: "VARCHAR", role: "Atributo", significado: "Código técnico: VRC (Pacto pasivo) o CRV (Pacto activo).", contable: "No aplica" },
      { name: "tipo_operacion_desc", type: "VARCHAR", role: "Atributo", significado: "Descripción oficial: Retrocompra (Pasivo) o Retroventa (Activo).", contable: "Pacto Activo (CRV) / Pasivo (VRC)" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Atributo", significado: "Institución financiera contraparte (Banco, Corredora, Aseguradora).", contable: "No aplica" },
      { name: "tasa_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés pactada entre las partes en porcentaje anual.", contable: "Costo Amortizado / Devengado" },
      { name: "valor_inicial", type: "DOUBLE", role: "Métrica", significado: "Monto desembolsado o recibido al inicio de la operación.", contable: "Valor de Mercado Bruto" },
      { name: "valor_final", type: "DOUBLE", role: "Métrica", significado: "Monto acordado a liquidar al vencimiento del pacto.", contable: "Valor de Mercado Bruto" },
      { name: "valorizacion_cierre", type: "DOUBLE", role: "Métrica", significado: "Valoración devengada al último día del trimestre según IFRS.", contable: "Valor de Mercado Neto" },
      { name: "emisor_garantia", type: "VARCHAR", role: "Atributo", significado: "Emisor del colateral entregado o recibido en garantía.", contable: "No aplica" },
      { name: "tipo_instrumento_garantia", type: "VARCHAR", role: "Atributo", significado: "Tipo de título en garantía (Bonos de Tesorería, Bancarios, etc.).", contable: "No aplica" },
      { name: "valor_mercado_garantia", type: "DOUBLE", role: "Métrica", significado: "Valor de mercado oficial del título dejado en colateral.", contable: "Valor Razonable / MtM" }
    ]
  },
  {
    id: "fi_registro_fondos_universo",
    name: "fi.universo_fondos",
    viewName: "fi_registro_fondos_universo",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "Ley Única de Fondos (LUF N° 20.712)",
    corte: "2026-03",
    frescura: "Registro CMF completo",
    modo: "Automático Streaming CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "1.677 fondos",
    descripcion: "Registro oficial completo de todos los fondos de inversión chilenos supervisados por la CMF (FINRE y FIRES), distinguiendo fondos vigentes y liquidados con sus respectivas fechas de inicio registral.",
    origen: "Comisión para el Mercado Financiero (CMF) — Nómina y Registro Público de Fondos de Inversión (Pestaña 1 y 2).",
    columnas: [
      { name: "run_fondo", type: "BIGINT", role: "PK", significado: "RUN numérico oficial del fondo de inversión ante la CMF.", contable: "No aplica" },
      { name: "rut_fondo_dv", type: "VARCHAR", role: "Atributo", significado: "RUT completo con dígito verificador del fondo ante la CMF.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Razón social completa y oficial del fondo de inversión.", contable: "No aplica" },
      { name: "administradora", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la Administradora General de Fondos (AGF) gestora.", contable: "No aplica" },
      { name: "tipo_entidad_desc", type: "VARCHAR", role: "Dimensión", significado: "Clasificación oficial CMF: Fondo Inversión No Rescatable (FINRE) o Rescatable (FIRES).", contable: "No aplica" },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Estado registral actual: Vigente o No Vigente (Liquidado).", contable: "No aplica" }
    ]
  },
  {
    id: "fi_repos_detalle_historico",
    name: "fi.repos_contratos",
    viewName: "fi_repos_detalle_historico",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "CMF VRC / CRV IFRS",
    corte: "2010-2026",
    frescura: "Muestra 2010-2026 · sin auditar",
    modo: "Experimental (extracción en revisión)",
    ultimaActualizacion: "2026-09-26",
    registros: "2.946 contratos",
    descripcion: "Extracción preliminar, contrato por contrato, de las operaciones con pacto de retroventa (CRV activo y VRC pasivo) informadas por fondos de inversión chilenos en 16 cierres anuales entre 2010 y 2026. Cada fila pretende representar un contrato: contraparte, tasa, montos y garantía colateral.",
    advertencia: "Falta auditar contra los informes originales de la CMF. No implica cobertura exhaustiva del mercado de pactos ni confiabilidad de montos y unidades. No usar totales, rankings de contrapartes ni cifras de mercado derivados de esta muestra. Una valorización de cierre no es el portafolio ni el pasivo total de un fondo.",
    origen: "Comisión para el Mercado Financiero (CMF) — Pestaña 15 (Informe Trimestral de Operaciones con Pacto VRC/CRV).",
    columnas: [
      { name: "run_fondo", type: "BIGINT", role: "PK", significado: "RUN del fondo de inversión titular del contrato.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Nombre registrado del fondo de inversión.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo trimestral de reporte (YYYYMM).", contable: "No aplica" },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año calendario del informe CMF.", contable: "No aplica" },
      { name: "codigo_operacion", type: "VARCHAR", role: "Dimensión", significado: "Tipo de operación contractual: VRC (Retrocompra) o CRV (Retroventa).", contable: "No aplica" },
      { name: "tipo_operacion_desc", type: "VARCHAR", role: "Dimensión", significado: "Descripción jurídica: Venta con Compromiso de Retrocompra o Compra con Retroventa.", contable: "Pacto Activo (CRV) / Pasivo (VRC)" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Dimensión", significado: "Entidad financiera contraparte (Banco comercial o corredora de bolsa).", contable: "No aplica" },
      { name: "tasa_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de pacto convenida en porcentaje anual.", contable: "Costo Amortizado / Devengado" },
      { name: "valor_inicial_m_moneda", type: "DOUBLE", role: "Métrica", significado: "Monto desembolsado / recibido al inicio en miles de la moneda pactada.", contable: "Valor de Mercado Bruto" },
      { name: "valor_final_m_moneda", type: "DOUBLE", role: "Métrica", significado: "Monto a liquidar al vencimiento en miles de la moneda pactada.", contable: "Valor de Mercado Bruto" },
      { name: "valorizacion_cierre_m_moneda", type: "DOUBLE", role: "Métrica", significado: "Valoración devengada a la fecha de corte en miles de la moneda pactada.", contable: "Valor de Mercado Neto" },
      { name: "emisor_garantia", type: "VARCHAR", role: "Atributo", significado: "Emisor del instrumento entregado o recibido en garantía colateral.", contable: "No aplica" },
      { name: "tipo_instrumento_garantia", type: "VARCHAR", role: "Dimensión", significado: "Tipo de título colateral (Bonos de Tesorería, Bancarios, Acciones, etc.).", contable: "No aplica" },
      { name: "valor_mercado_garantia_m_moneda", type: "DOUBLE", role: "Métrica", significado: "Valorización de mercado oficial de la garantía en miles de la moneda pactada.", contable: "Valor Razonable / MtM" }
    ]
  },
  {
    id: "ffmm_maestro",
    name: "ffmm.lista_entidades",
    viewName: "ffmm_maestro",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "Circular CMF 1333",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "1.156 entidades",
    descripcion: "Catálogo oficial de los 1.156 fondos mutuos administrados por las Administradoras Generales de Fondos (AGF).",
    origen: "Comisión para el Mercado Financiero (CMF) — Catastro Oficial de Fondos Mutuos y Series de Cuotas (Portal Estadístico CMF).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Surrogate PK del fondo mutuo (FFMM_RUN).", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "Atributo", significado: "RUN fiscal del fondo mutuo registrado en CMF.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Nombre de fantasía registrado del fondo mutuo.", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "Clasificación de industria institucional.", contable: "No aplica" }
    ]
  },
  {
    id: "ffmm_futuros",
    name: "ffmm.circular_1333_futuros",
    viewName: "ffmm_futuros",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "Circular CMF 1333",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "280.494 registros",
    descripcion: "Posiciones en contratos de futuros financieros sobre índices, monedas y commodities de fondos mutuos.",
    origen: "CMF — Circular N° 1333 (Cartera Mensual de Operaciones con Instrumentos Derivados y Futuros de Fondos Mutuos).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Surrogate PK del contrato de futuro.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo trimestral informado.", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "FK", significado: "RUN del fondo mutuo titular.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Activo subyacente del contrato de futuro.", contable: "No aplica" },
      { name: "posicion", type: "VARCHAR", role: "Atributo", significado: "Posición tomada: Largo (compra) o Corto (venta).", contable: "No aplica" },
      { name: "monto_contratado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto contratado del futuro en millones de CLP.", contable: "Valor Razonable / MtM" }
    ]
  },
  {
    id: "afp_maestro",
    name: "afp.lista_administradoras",
    viewName: "afp_maestro",
    sector: "pensiones",
    sectorLabel: "Fondos de Pensiones",
    norma: "D.L. 3.500 / SPensiones",
    corte: "Sin fecha de vigencia comprobada",
    frescura: "Listado de entidades; identidad pendiente de cotejo",
    modo: "Catálogo local",
    ultimaActualizacion: "2026-09-27",
    registros: "7 entidades",
    descripcion: "Lista de identificación sin AUM, afiliados, comisiones ni otras cifras generadas. RUT y vigencia registral requieren cotejo independiente.",
    origen: "Nombres y RUT conservados del catálogo local pensiones/scripts/generate_afp_maestro.py; no es nómina SP certificada.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "ID local de la administradora.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "Atributo", significado: "RUT del catálogo local, pendiente de cotejo.", contable: "No aplica" },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social del catálogo local.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial del catálogo local.", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_maestro",
    name: "bancos.lista_instituciones",
    viewName: "bancos_maestro",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Ley General de Bancos / CMF",
    corte: "Sin fecha de vigencia por institución",
    frescura: "Catálogo manual; pendiente de cotejo registral",
    modo: "Catálogo local",
    ultimaActualizacion: "2026-09-27",
    registros: "40 códigos (incluye agregados)",
    descripcion: "Lista local de códigos, entidades históricas, filiales y agregados sectoriales; no equivale a 40 bancos activos. Validar RUT, estado y vigencia contra CMF.",
    origen: "MAESTRO_BANCOS en bancos/scripts/pipeline_stream_bancos.py; no contrastado individualmente con la nómina CMF.",
    columnas: [
      { name: "codigo_institucion", type: "VARCHAR", role: "PK", significado: "Código del catálogo local.", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "Atributo", significado: "RUT del catálogo local, por cotejar.", contable: "No aplica" },
      { name: "razon_social", type: "VARCHAR", role: "Atributo", significado: "Nombre consignado localmente.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre abreviado consignado localmente.", contable: "No aplica" },
      { name: "tipo_licencia", type: "VARCHAR", role: "Atributo", significado: "Clasificación local, no verificada.", contable: "No aplica" },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "Estado local, no histórico por período.", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_cmf_balance",
    name: "bancos.cmf_balance_b1_b2",
    viewName: "bancos_cmf_balance",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "CMF — Manual del Sistema de Información para bancos (B1/MB1 y B2/MB2)",
    corte: "Períodos mensuales validados desde 2026-07",
    frescura: "Publicación automática después del gate mensual",
    modo: "Automático con validación de cobertura y cotejo CMF",
    registros: "Filas B1/B2 de períodos validados",
    descripcion: "Filas fuente de estados de situación financiera B1 consolidado y B2 individual. La fila física permanece en numero_fila_fuente, separada de rubro/línea/ítem. Importes fuente originales, sin interpretación ni sumas automáticas.",
    origen: "CMF — ZIP TXT mensual y XLSX de reporte mensual. Cada partición registra URL y SHA-256 de ambas fuentes en la fila y en su informe de validación.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Clave determinística compuesta por período, institución, modelo, cuenta y ocurrencia dentro del archivo.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Período mensual del archivo CMF en formato YYYY-MM.", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Último día calendario del mes informado.", contable: "No aplica" },
      { name: "codigo_institucion", type: "VARCHAR", role: "FK", significado: "Código CMF del encabezado y del nombre de archivo.", contable: "No aplica" },
      { name: "nombre_institucion_fuente", type: "VARCHAR", role: "Atributo", significado: "Nombre literal del encabezado CMF; el RUT no se infiere.", contable: "No aplica" },
      { name: "tipo_estado", type: "VARCHAR", role: "Atributo", significado: "balance o resultados según familia de archivo.", contable: "No aplica" },
      { name: "familia_archivo_fuente", type: "VARCHAR", role: "Atributo", significado: "B1, B2 o R1.", contable: "No aplica" },
      { name: "modelo_cmf", type: "VARCHAR", role: "Atributo", significado: "MB1 consolidado, MB2 individual o MR1 consolidado.", contable: "No aplica" },
      { name: "nivel_consolidacion", type: "VARCHAR", role: "Atributo", significado: "Perímetro informado por la fuente, no inferido del nombre.", contable: "No aplica" },
      { name: "codigo_cuenta", type: "VARCHAR", role: "PK parcial", significado: "Código de cuenta tal como aparece en el TXT CMF.", contable: "No aplica" },
      { name: "rubro", type: "VARCHAR", role: "Clasificación", significado: "Nivel jerárquico del modelo de cuentas CMF.", contable: "No aplica" },
      { name: "linea", type: "VARCHAR", role: "Clasificación", significado: "Nivel jerárquico del modelo; no representa el número físico de fila.", contable: "No aplica" },
      { name: "item", type: "VARCHAR", role: "Clasificación", significado: "Nivel jerárquico del modelo de cuentas CMF.", contable: "No aplica" },
      { name: "glosa_cuenta", type: "VARCHAR", role: "Atributo", significado: "Descripción obtenida del modelo CMF incluido en el ZIP del período.", contable: "No aplica" },
      { name: "tipo_linea", type: "VARCHAR", role: "Atributo", significado: "Clasificación técnica auxiliar; no sustituye la definición normativa del modelo.", contable: "No aplica" },
      { name: "numero_fila_fuente", type: "INTEGER", role: "Orden", significado: "Posición física original en el TXT; independiente de rubro, línea e ítem.", contable: "No aplica" },
      { name: "ocurrencia_codigo_cuenta", type: "INTEGER", role: "Atributo", significado: "Desempate cuando una cuenta aparece repetida dentro del mismo archivo.", contable: "No aplica" },
      { name: "unidad_monto", type: "VARCHAR", role: "Atributo", significado: "Unidad literal controlada por el extractor; no valida la semántica de cada componente B1/B2.", contable: "No aplica" },
      { name: "importes_fuente_raw", type: "VARCHAR[]", role: "Dato fuente", significado: "Campos monetarios originales sin transformación ni asignación de componente.", contable: "Pendiente de mapeo semántico" },
      { name: "importes_fuente_decimal", type: "VARCHAR[]", role: "Dato fuente", significado: "Representación decimal exacta paralela a los campos originales.", contable: "Pendiente de mapeo semántico" },
      { name: "archivo_fuente", type: "VARCHAR", role: "Procedencia", significado: "Ruta del miembro TXT dentro del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_zip", type: "VARCHAR", role: "Procedencia", significado: "URL oficial del ZIP procesado.", contable: "No aplica" },
      { name: "sha256_zip", type: "VARCHAR", role: "Procedencia", significado: "Hash de integridad del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "URL del reporte XLSX utilizado en el gate.", contable: "No aplica" },
      { name: "sha256_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "Hash del XLSX utilizado en el gate.", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_cmf_resultados",
    name: "bancos.cmf_resultados_r1",
    viewName: "bancos_cmf_resultados",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "CMF — Manual del Sistema de Información para bancos (R1/MR1)",
    corte: "Períodos mensuales validados desde 2026-07",
    frescura: "Publicación automática después del gate mensual",
    modo: "Automático con validación de cobertura y cotejo CMF",
    registros: "Filas R1 de períodos validados",
    descripcion: "Filas fuente del estado de resultados R1 consolidado. Conserva la fila física en numero_fila_fuente, separada de rubro/línea/ítem. Importes y período tal como los publica la fuente; no se derivan acumulados ni métricas.",
    origen: "CMF — ZIP TXT mensual y XLSX de reporte mensual. Cada partición registra URL y SHA-256 de ambas fuentes en la fila y en su informe de validación.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Clave determinística compuesta por período, institución, modelo, cuenta y ocurrencia dentro del archivo.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Período mensual del archivo CMF en formato YYYY-MM.", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Último día calendario del mes informado.", contable: "No aplica" },
      { name: "codigo_institucion", type: "VARCHAR", role: "FK", significado: "Código CMF del encabezado y del nombre de archivo.", contable: "No aplica" },
      { name: "nombre_institucion_fuente", type: "VARCHAR", role: "Atributo", significado: "Nombre literal del encabezado CMF; el RUT no se infiere.", contable: "No aplica" },
      { name: "tipo_estado", type: "VARCHAR", role: "Atributo", significado: "balance o resultados según familia de archivo.", contable: "No aplica" },
      { name: "familia_archivo_fuente", type: "VARCHAR", role: "Atributo", significado: "B1, B2 o R1.", contable: "No aplica" },
      { name: "modelo_cmf", type: "VARCHAR", role: "Atributo", significado: "MB1 consolidado, MB2 individual o MR1 consolidado.", contable: "No aplica" },
      { name: "nivel_consolidacion", type: "VARCHAR", role: "Atributo", significado: "Perímetro informado por la fuente, no inferido del nombre.", contable: "No aplica" },
      { name: "codigo_cuenta", type: "VARCHAR", role: "PK parcial", significado: "Código de cuenta tal como aparece en el TXT CMF.", contable: "No aplica" },
      { name: "rubro", type: "VARCHAR", role: "Clasificación", significado: "Nivel jerárquico del modelo de cuentas CMF.", contable: "No aplica" },
      { name: "linea", type: "VARCHAR", role: "Clasificación", significado: "Nivel jerárquico del modelo; no representa el número físico de fila.", contable: "No aplica" },
      { name: "item", type: "VARCHAR", role: "Clasificación", significado: "Nivel jerárquico del modelo de cuentas CMF.", contable: "No aplica" },
      { name: "glosa_cuenta", type: "VARCHAR", role: "Atributo", significado: "Descripción obtenida del modelo CMF incluido en el ZIP del período.", contable: "No aplica" },
      { name: "tipo_linea", type: "VARCHAR", role: "Atributo", significado: "Clasificación técnica auxiliar; no sustituye la definición normativa del modelo.", contable: "No aplica" },
      { name: "numero_fila_fuente", type: "INTEGER", role: "Orden", significado: "Posición física original en el TXT; independiente de rubro, línea e ítem.", contable: "No aplica" },
      { name: "ocurrencia_codigo_cuenta", type: "INTEGER", role: "Atributo", significado: "Desempate cuando una cuenta aparece repetida dentro del mismo archivo.", contable: "No aplica" },
      { name: "unidad_monto", type: "VARCHAR", role: "Atributo", significado: "Unidad literal controlada por el extractor; no valida la semántica de cada componente B1/B2.", contable: "No aplica" },
      { name: "importes_fuente_raw", type: "VARCHAR[]", role: "Dato fuente", significado: "Campos monetarios originales sin transformación ni asignación de componente.", contable: "Pendiente de mapeo semántico" },
      { name: "importes_fuente_decimal", type: "VARCHAR[]", role: "Dato fuente", significado: "Representación decimal exacta paralela a los campos originales.", contable: "Pendiente de mapeo semántico" },
      { name: "archivo_fuente", type: "VARCHAR", role: "Procedencia", significado: "Ruta del miembro TXT dentro del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_zip", type: "VARCHAR", role: "Procedencia", significado: "URL oficial del ZIP procesado.", contable: "No aplica" },
      { name: "sha256_zip", type: "VARCHAR", role: "Procedencia", significado: "Hash de integridad del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "URL del reporte XLSX utilizado en el gate.", contable: "No aplica" },
      { name: "sha256_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "Hash del XLSX utilizado en el gate.", contable: "No aplica" }
    ]
  },
  {
    id: "factoring_leasing_maestro",
    name: "factoring_leasing.lista_entidades",
    viewName: "factoring_leasing_maestro",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing",
    norma: "Nómina Oficial CMF & Registro de Valores (RVEMI / FASOC / LISOC)",
    corte: "2026-03",
    frescura: "Al día (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "28 entidades",
    descripcion: "Lista local de 28 entidades de Factoring, Leasing y financiamiento automotriz. RUT únicos con dígito verificador válido; esto no certifica identidad, estado de vigencia ni exhaustividad frente al registro CMF vigente. Balances y notas retirados por ahora.",
    origen: "Catálogo local con referencias declaradas a registros CMF FASOC, LISOC y RVEMI; procedencia y vigencia de cada entidad pendientes de cotejo registral independiente.",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "RUT oficial de la sociedad con dígito verificador auditado bajo algoritmo Módulo 11 (formato XXXXXXXX-Y).", contable: "No aplica", interpretacion: "Identificador tributario y regulatorio unívoco de la entidad ante el SII y la CMF." },
      { name: "rut_formateado", type: "VARCHAR", role: "Atributo", significado: "RUT institucional formateado con puntos y guion (XX.XXX.XXX-Y).", contable: "No aplica", interpretacion: "Formato visual para presentación de reportes corporativos." },
      { name: "razon_social", type: "VARCHAR", role: "Atributo", significado: "Razón social formal de la compañía inscrita en el registro mercantil de la CMF.", contable: "No aplica", interpretacion: "Nombre legal corporativo para contratos y obligaciones IFRS." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial o marca de fantasía de la sociedad en el mercado.", contable: "No aplica", interpretacion: "Identificador comercial estándar de la firma para análisis de mercado." },
      { name: "segmento", type: "VARCHAR", role: "Atributo", significado: "Segmentación funcional principal: Factoring, Leasing, Ambas o Automotriz.", contable: "No aplica", interpretacion: "Clasificación de la actividad financiera dominante del intermediario no bancario." },
      { name: "giro", type: "VARCHAR", role: "Atributo", significado: "Descripción detallada del giro y líneas operativas declaradas ante la CMF.", contable: "No aplica", interpretacion: "Detalle de los productos de colocación operados (descuento de facturas, leasing operativo/financiero, crédito automotriz)." },
      { name: "registro_cmf", type: "VARCHAR", role: "Atributo", significado: "Registro regulatorio CMF: Filial Bancaria LGB, Registro de Valores (RVEMI), o REEI.", contable: "No aplica", interpretacion: "Determina el perímetro de supervisión y el marco contable aplicable (Norma Bancaria vs Full IFRS de Emisores)." },
      { name: "codigo_tipoentidad", type: "VARCHAR", role: "Atributo", significado: "Código institucional en la taxonomía CMF: FASOC, LISOC, RVEMI.", contable: "No aplica", interpretacion: "Clasificador técnico para extracción directa en los portales estadísticos del regulador." },
      { name: "tipo_licencia", type: "VARCHAR", role: "Atributo", significado: "Naturaleza jurídica y corporativa de la licencia de operación.", contable: "No aplica", interpretacion: "Distingue entre filiales bancarias directas, emisores de holding financiero y entidades independientes." },
      { name: "vigencia_cmf", type: "VARCHAR", role: "Atributo", significado: "Condición registral formal informada por la CMF (Vigente vs Cancelada / No Vigente).", contable: "No aplica", interpretacion: "Permite separar intermediarios actualmente operativos de emisores históricos cerrados o absorbidos." },
      { name: "vigente", type: "INTEGER", role: "Métrica", significado: "Flag binario de vigencia operativa (1: Activo y Vigente, 0: Histórico o Cancelado).", contable: "No aplica", interpretacion: "Filtro booleano inmediato para paneles de riesgo y rankings contemporáneos." },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "Estado de la sociedad en la base de datos (Activo vs Histórico / Cancelado).", contable: "No aplica", interpretacion: "Etiqueta operativa para visualización rápida." },
      { name: "es_factoring", type: "INTEGER", role: "Métrica", significado: "Indicador si la sociedad opera factoring comercial (1 / 0).", contable: "No aplica", interpretacion: "Participación en el mercado de descuento y cesión de créditos comerciales." },
      { name: "es_leasing_financiero", type: "INTEGER", role: "Métrica", significado: "Indicador si la sociedad ofrece leasing financiero de bienes de capital (1 / 0).", contable: "No aplica", interpretacion: "Financiamiento de maquinarias, vehículos pesados y equipamiento corporativo." },
      { name: "es_leasing_habitacional", type: "INTEGER", role: "Métrica", significado: "Indicador si opera bajo el régimen especial de Leasing Habitacional Ley 19.281 (1 / 0).", contable: "No aplica", interpretacion: "Contratos de arrendamiento de viviendas con promesa de compraventa vinculados a subsidio estatal." },
      { name: "es_automotriz", type: "INTEGER", role: "Métrica", significado: "Indicador si está especializada en financiamiento automotriz (1 / 0).", contable: "No aplica", interpretacion: "Colocaciones prendarias para compra de vehículos livianos y comerciales." },
      { name: "pertenece_a_banco", type: "VARCHAR", role: "Atributo", significado: "Indicador si la entidad está ligada a un banco comercial (Sí / No).", contable: "No aplica", interpretacion: "Distingue entidades con fondeo y respaldo bancario directo de competidores independientes." },
      { name: "relacionada_banco", type: "INTEGER", role: "Métrica", significado: "Flag numérico de relación de propiedad o control con entidades bancarias (1 / 0).", contable: "No aplica", interpretacion: "Variable para análisis de conglomerados y concentración de financiamiento." },
      { name: "filial_bancaria_lgb", type: "INTEGER", role: "Métrica", significado: "Flag específico si es filial bancaria formal regida por la Ley General de Bancos (1 / 0).", contable: "No aplica", interpretacion: "Distingue filiales directas de bancos locales (supervisadas bajo FASOC/LISOC) de matrices bancarias extranjeras o holdings." },
      { name: "banco_relacionado", type: "VARCHAR", role: "Atributo", significado: "Nombre de la institución bancaria relacionada o matriz.", contable: "No aplica", interpretacion: "Identifica el banco patrocinador o coligado." },
      { name: "grupo_controlador", type: "VARCHAR", role: "Atributo", significado: "Grupo financiero, banco matriz o conglomerado económico controlador.", contable: "No aplica", interpretacion: "Permite evaluar la concentración de riesgo de crédito por grupo económico." },
      { name: "eeff_ifrs_en_cmf", type: "VARCHAR", role: "Atributo", significado: "Tipo y régimen de estados financieros informados ante la CMF.", contable: "No aplica", interpretacion: "Informa si los reportes siguen Full IFRS de emisores o normas bancarias CMF." },
      { name: "fuente_eeff", type: "VARCHAR", role: "Atributo", significado: "Ruta de extracción y acceso a los balances trimestrales oficiales.", contable: "No aplica", interpretacion: "Trazabilidad de la fuente de datos primarios." },
      { name: "observaciones", type: "VARCHAR", role: "Atributo", significado: "Notas técnicas, eventos societarios y particularidades regulatorias relevantes.", contable: "No aplica", interpretacion: "Contexto cualitativo sobre reexpresiones contables, cancelaciones o reorganizaciones societarias." }
    ]
  },
  {
    id: "corredoras_bolsa_maestro",
    name: "corredoras.lista_entidades",
    viewName: "corredoras_bolsa_maestro",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa",
    norma: "CMF Chile — Registro de Corredores de Bolsa (Ley 18.045)",
    corte: "2014-03 a 2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "120 entidades",
    descripcion: "Directorio oficial de entidades autorizadas e inscritas ante la CMF para intermediar valores de oferta pública, con validación de RUT bajo Módulo 11 y clasificación por conglomerado financiero.",
    origen: "Comisión para el Mercado Financiero (CMF) — Registro de Intermediarios de Valores.",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Rol Único Tributario oficial del corredor de bolsa con dígito verificador canónico.", contable: "No aplica", interpretacion: "Identificador tributario y regulatorio unívoco de la intermediaria bursátil." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social oficial inscrita en el Registro de Corredores de Bolsa de la CMF.", contable: "No aplica", interpretacion: "Denominación legal societaria formal." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre de fantasía o marca comercial estándar de la corredora.", contable: "No aplica", interpretacion: "Nombre representativo en el parqué y plataformas electrónicas de negociación." },
      { name: "tipo_intermediario", type: "VARCHAR", role: "Dimensión", significado: "Tipo de intermediario regulado ('CORREDOR DE BOLSA').", contable: "No aplica", interpretacion: "Distingue a los miembros de bolsas de valores facultados para transar acciones, renta fija y derivados." },
      { name: "grupo_financiero", type: "VARCHAR", role: "Dimensión", significado: "Conglomerado o matriz controladora de la corredora de bolsa.", contable: "No aplica", interpretacion: "Clasifica filiales bancarias (Banco de Chile, Santander, BCI, etc.) versus corredoras independientes (LarrainVial, BTG Pactual, etc.)." }
    ]
  },
  {
    id: "corredoras_bolsa_balance_resumen",
    name: "corredoras.balance_resumen",
    viewName: "corredoras_bolsa_balance_resumen",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa",
    norma: "CMF Chile — FECU Intermediarios IFRS (Circular NCG)",
    corte: "2014-03 a 2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "621 balances",
    descripcion: "Estados Financieros IFRS trimestrales de los intermediarios bursátiles: masa total de activos, pasivos exigibles, patrimonio neto, activos líquidos y utilidad neta del ejercicio.",
    origen: "Comisión para el Mercado Financiero (CMF) — Estadísticas del Mercado de Valores.",
    columnas: [
      { name: "id_balance", type: "VARCHAR", role: "PK", significado: "Clave primaria compuesta por periodo y RUT ({periodo}_{rut}).", contable: "No aplica", interpretacion: "Identificador unívoco del cierre contable trimestral." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo trimestral contable (formato YYYY-MM).", contable: "No aplica", interpretacion: "Eje temporal maestro para series de tiempo y cruces macroeconómicos." },
      { name: "fecha_corte", type: "DATE", role: "Dimensión", significado: "Fecha exacta de cierre de los estados financieros (YYYY-MM-DD).", contable: "No aplica", interpretacion: "Fecha oficial a la que corresponden los saldos contables informados." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT oficial de la corredora de bolsa con Módulo 11.", contable: "No aplica", interpretacion: "Clave foránea de enlace con el catálogo maestro de corredoras." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social oficial de la corredora ante la CMF.", contable: "No aplica", interpretacion: "Nombre legal de la entidad informante." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Masa total de activos informados a la CMF en millones de CLP (cuenta 10.00.00).", contable: "Valor Razonable / Devengado", interpretacion: "Dimensión económica total de la corredora (inversiones propias, caja y cuentas por cobrar bursátiles)." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Activos totales convertidos a millones de USD al dólar observado de cierre.", contable: "Valor Razonable / MtM", interpretacion: "Tamaño patrimonial y de balance expresado en moneda internacional." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos exigibles a terceros en millones de CLP (cuenta 21.00.00).", contable: "Costo Amortizado / Devengado", interpretacion: "Obligaciones totales de la corredora (acreedores por intermediación, financiamiento bancario y otros)." },
      { name: "total_pasivos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Pasivos totales convertidos a millones de USD al dólar observado de cierre.", contable: "Costo Amortizado / Devengado", interpretacion: "Volumen de endeudamiento exigible valorizado en divisa dura." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto total en millones de CLP (cuenta 22.00.00).", contable: "Valor de Mercado Neto", interpretacion: "Capital propio y reservas que garantizan el cumplimiento de los márgenes patrimoniales y de liquidez exigidos por CMF." },
      { name: "patrimonio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto convertido a millones de USD al dólar observado de cierre.", contable: "Valor de Mercado Neto", interpretacion: "Base de solvencia y capital regulatorio en moneda internacional." },
      { name: "efectivo_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Efectivo y equivalentes de efectivo en millones de CLP (cuenta 11.01.00).", contable: "Valor Razonable / MtM", interpretacion: "Disponibilidad inmediata de tesorería para honrar liquidaciones diarias en las cámaras de compensación (CCLV)." },
      { name: "efectivo_equivalentes_m_usd", type: "DOUBLE", role: "Métrica", significado: "Efectivo y equivalentes de efectivo convertidos a millones de USD.", contable: "Valor Razonable / MtM", interpretacion: "Liquidez inmediata de la corredora en divisa extranjera." },
      { name: "utilidad_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado neto final del ejercicio atribuible en millones de CLP (cuenta 30.00.00).", contable: "Devengado / IFRS", interpretacion: "Beneficio neto acumulado en el periodo generado por el corretaje, comisiones de custodia y cartera propia." },
      { name: "utilidad_ejercicio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Resultado neto final convertido a millones de USD al tipo de cambio de cierre.", contable: "Devengado / IFRS", interpretacion: "Rentabilidad neta del intermediario bursátil en divisa dura." }
    ]
  },
  {
    id: "corredoras_bolsa_registro_universo",
    name: "corredoras.registro_unico",
    viewName: "corredoras_bolsa_registro_universo",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa",
    norma: "CMF Chile — Registro Oficial de Intermediarios de Valores (Ley 18.045)",
    corte: "2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-24",
    registros: "120 entidades",
    descripcion: "Catastro exhaustivo de intermediarios de bolsa registrados ante la CMF (24 vigentes y 96 históricos/cancelados) con validación Módulo 11 y enlace a ficha oficial.",
    origen: "Comisión para el Mercado Financiero (CMF) — Consulta de Entidades Fiscalizadas.",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "RUT oficial canónico con guión y DV bajo Módulo 11.", contable: "No aplica", interpretacion: "Identificador tributario y regulatorio primario." },
      { name: "rut_cuerpo", type: "VARCHAR", role: "Dimensión", significado: "Cuerpo numérico del RUT.", contable: "No aplica", interpretacion: "Base numérica para consultas web y ordenamiento." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador canónico M11.", contable: "No aplica", interpretacion: "Dígito de control de integridad." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social oficial societaria.", contable: "No aplica", interpretacion: "Denominación legal completa." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre comercial o de fantasía.", contable: "No aplica", interpretacion: "Marca comercial estándar." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Estado registral CMF ('Vigente' o 'No Vigente').", contable: "No aplica", interpretacion: "Distingue corredoras activas que operan actualmente en el parqué de aquellas canceladas o fusionadas." },
      { name: "tipo_intermediario", type: "VARCHAR", role: "Dimensión", significado: "Clasificación ('CORREDOR DE BOLSA').", contable: "No aplica", interpretacion: "Miembro habilitado para intermediación." },
      { name: "tipo_entidad", type: "VARCHAR", role: "Dimensión", significado: "Código regulatorio CMF ('COBOL').", contable: "No aplica", interpretacion: "Tipo de entidad en sistemas SEIL/CMF." },
      { name: "grupo_financiero", type: "VARCHAR", role: "Dimensión", significado: "Conglomerado o grupo financiero de pertenencia.", contable: "No aplica", interpretacion: "Matriz bancaria o independiente." },
      { name: "row_id", type: "VARCHAR", role: "Dimensión", significado: "Identificador de fila CMF para consulta de fichas y EEFF.", contable: "No aplica", interpretacion: "Token criptográfico de navegación en el portal CMF." },
      { name: "url_ficha_cmf", type: "VARCHAR", role: "Dimensión", significado: "Enlace URL a la ficha institucional en la CMF.", contable: "No aplica", interpretacion: "Acceso a hechos esenciales y antecedentes legales." }
    ]
  },
  {
    id: "corredoras_bolsa_caratula_eeff_historico",
    name: "corredoras.estados_financieros",
    viewName: "corredoras_bolsa_caratula_eeff_historico",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa",
    norma: "CMF Chile — Estados Financieros IFRS (XML Oficial)",
    corte: "2018-12 a 2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-24",
    registros: "621 balances",
    descripcion: "Carátula completa de balance general IFRS descargada en streaming desde el XML oficial: cartera disponible, cartera comprometida, financiamiento (CRV y VRC) y verificación matemática de cuadre contable.",
    origen: "Comisión para el Mercado Financiero (CMF) — Repositorio IFRS de Intermediarios.",
    columnas: [
      { name: "id_balance", type: "VARCHAR", role: "PK", significado: "Clave compuesta {periodo}_{rut}.", contable: "No aplica", interpretacion: "Identificador de corte contable." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo trimestral YYYY-MM.", contable: "No aplica", interpretacion: "Eje temporal maestro." },
      { name: "fecha_corte", type: "DATE", role: "Dimensión", significado: "Fecha exacta de cierre del trimestre.", contable: "No aplica", interpretacion: "Fecha de devengo de los saldos." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT oficial de la corredora.", contable: "No aplica", interpretacion: "Enlace al maestro." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social oficial.", contable: "No aplica", interpretacion: "Nombre de la corredora." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activos totales en miles de CLP.", contable: "Valor Razonable / Devengado", interpretacion: "Dimensión total del balance." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Activos totales en millones de USD.", contable: "MtM", interpretacion: "Valorización en divisa extranjera." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Pasivos totales en miles de CLP.", contable: "Costo Amortizado", interpretacion: "Obligaciones totales exigibles." },
      { name: "total_pasivos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Pasivos totales en millones de USD.", contable: "Costo Amortizado", interpretacion: "Exigibilidad en divisa." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto en miles de CLP.", contable: "Patrimonio", interpretacion: "Capital propio y reservas." },
      { name: "patrimonio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto en millones de USD.", contable: "Patrimonio", interpretacion: "Capital en USD." },
      { name: "utilidad_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado neto del ejercicio en miles de CLP.", contable: "Resultado IFRS", interpretacion: "Utilidad o pérdida neta acumulada." },
      { name: "utilidad_ejercicio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Resultado neto en millones de USD.", contable: "Resultado IFRS", interpretacion: "Rentabilidad en divisa." },
      { name: "efectivo_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Caja y bancos en miles de CLP.", contable: "Liquidez", interpretacion: "Tesorería disponible." },
      { name: "efectivo_equivalentes_m_usd", type: "DOUBLE", role: "Métrica", significado: "Caja y bancos en millones de USD.", contable: "Liquidez", interpretacion: "Tesorería en USD." },
      { name: "cartera_vr_disponible_m_clp", type: "DOUBLE", role: "Métrica", significado: "Instrumentos a valor razonable de cartera propia disponible en miles de CLP.", contable: "Valor Razonable", interpretacion: "Portafolio libre para negociación bursátil." },
      { name: "cartera_vr_comprometida_m_clp", type: "DOUBLE", role: "Métrica", significado: "Instrumentos a valor razonable de cartera propia comprometida en miles de CLP.", contable: "Valor Razonable", interpretacion: "Títulos entregados en garantía o bajo pactos de retroventa." },
      { name: "operaciones_financiamiento_crv_m_clp", type: "DOUBLE", role: "Métrica", significado: "Operaciones de financiamiento - compras con retroventa (CRV) en miles de CLP.", contable: "Costo Amortizado", interpretacion: "Financiamiento otorgado a terceros con respaldo colateral (activos REPO)." },
      { name: "operaciones_financiamiento_crv_m_usd", type: "DOUBLE", role: "Métrica", significado: "Operaciones CRV en millones de USD.", contable: "Costo Amortizado", interpretacion: "Financiamiento REPO activo en divisa." },
      { name: "obligaciones_retrocompra_vrc_m_clp", type: "DOUBLE", role: "Métrica", significado: "Operaciones de venta con retrocompra (VRC) en miles de CLP.", contable: "Costo Amortizado", interpretacion: "Financiamiento recibido mediante entrega de títulos bajo pacto (pasivos REPO)." },
      { name: "obligaciones_retrocompra_vrc_m_usd", type: "DOUBLE", role: "Métrica", significado: "Operaciones VRC en millones de USD.", contable: "Costo Amortizado", interpretacion: "Financiamiento REPO pasivo en divisa." },
      { name: "cuadre_balance", type: "BOOLEAN", role: "Métrica", significado: "Bandera de cuadre matemático (Activo == Pasivo + Patrimonio).", contable: "Auditoría Contable", interpretacion: "Garantiza integridad contable estricta al 100%." }
    ]
  },
  {
    id: "securitizadoras_maestro",
    name: "securitizadoras.lista_entidades",
    viewName: "securitizadoras_maestro",
    sector: "securitizadoras",
    sectorLabel: "Securitizadoras",
    norma: "CMF Chile — Ley 18.045 de Mercado de Valores (Título XVIII)",
    corte: "2026-06",
    frescura: "Mensual / Registros CMF",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "16 entidades",
    descripcion: "Catálogo maestro oficial de Sociedades Securitizadoras registradas ante la CMF bajo el Título XVIII de la Ley N° 18.045 (9 entidades vigentes y 7 históricas / en liquidación).",
    origen: "Comisión para el Mercado Financiero (CMF) — Registro de Sociedades Securitizadoras (RGSEC).",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Rol Único Tributario del intermediario securitizador (sin DV).", contable: "No aplica", interpretacion: "Identificador tributario corporativo único de la entidad gestora." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador oficial validado bajo algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Garantía de integridad matemática del RUT fiscal." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT formal con guión y dígito verificador.", contable: "No aplica", interpretacion: "Formato canónico para reportes y citaciones regulatorias." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal inscrita en el registro de valores de la CMF.", contable: "No aplica", interpretacion: "Nombre de la sociedad anónima especial facultada para administrar patrimonios separados." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Estado de supervisión CMF: VIGENTE o NO VIGENTE / EN LIQUIDACION.", contable: "No aplica", interpretacion: "Condición operativa de la sociedad securitizadora ante el regulador." },
      { name: "tipo_entidad_cmf", type: "VARCHAR", role: "Dimensión", significado: "Código de fiscalizado CMF (RGSEC: Registro de Sociedades Securitizadoras).", contable: "No aplica", interpretacion: "Categoría reglamentaria de la entidad en el sistema de fiscalización." },
      { name: "lineas_deuda_registradas", type: "BIGINT", role: "Métrica", significado: "Número de líneas y programas de bonos securitizados inscritos ante CMF.", contable: "No aplica", interpretacion: "Volumen de programas de titulización estructurados y vigentes." },
      { name: "cmf_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace URL directo a la ficha corporativa de la entidad en el portal CMF.", contable: "No aplica", interpretacion: "Vínculo web de transparencia y auditoría documental." }
    ]
  },
  {
    id: "securitizadoras_balance_resumen",
    name: "securitizadoras.balance_resumen",
    viewName: "securitizadoras_balance_resumen",
    sector: "securitizadoras",
    sectorLabel: "Securitizadoras",
    norma: "CMF Chile — FECU / IFRS Estados Financieros Consolidados",
    corte: "2014-03 a 2026-06",
    frescura: "Trimestral (50 periodos)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "362 balances",
    descripcion: "Estados Financieros IFRS trimestrales de las Sociedades Gestoras Securitizadoras. Refleja los activos corporativos, masa de pasivos exigibles, patrimonio neto y resultado final generado por comisiones de administración.",
    origen: "Comisión para el Mercado Financiero (CMF) — Información Financiera de Intermediarios y Emisores.",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "PK", significado: "Periodo trimestral contable de reporte (formato YYYY-MM).", contable: "Corte Trimestral", interpretacion: "Momento temporal del estado de situación financiera." },
      { name: "año", type: "BIGINT", role: "Dimensión", significado: "Año calendario del balance.", contable: "No aplica", interpretacion: "Agrupador anual para análisis de series temporales." },
      { name: "trimestre", type: "BIGINT", role: "Dimensión", significado: "Número de trimestre calendario (1 a 4).", contable: "No aplica", interpretacion: "Estacionalidad trimestral de la industria de titulización." },
      { name: "rut", type: "VARCHAR", role: "PK / FK", significado: "RUT de la sociedad securitizadora gestora.", contable: "No aplica", interpretacion: "Enlace referencial con el maestro de securitizadoras." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la sociedad gestora.", contable: "No aplica", interpretacion: "Identificación de la empresa administradora." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Condición de vigencia en la fecha de reporte.", contable: "No aplica", interpretacion: "Permite separar balances de entidades activas vs liquidadas." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activos totales de la sociedad gestora en millones de CLP.", contable: "Costo Amortizado / IFRS", interpretacion: "Tamaño patrimonial propio de la securitizadora (cuentas por cobrar, inversiones de capital)." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Pasivos totales exigibles de la sociedad gestora en millones de CLP.", contable: "Costo Amortizado / IFRS", interpretacion: "Obligaciones comerciales y financieras propias de la gestora." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto corporativo de la gestora en millones de CLP.", contable: "Capital y Reservas", interpretacion: "Solvencia corporativa de la entidad para responder ante exigencias regulatorias CMF." },
      { name: "efectivo_y_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo de caja, depósitos bancarios y activos líquidos inmediatos en millones de CLP.", contable: "Valor Razonable / Nominal", interpretacion: "Cojín de liquidez operacional disponible para cubrir gastos de administración." },
      { name: "ganancia_perdida_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado neto final acumulado del ejercicio en millones de CLP.", contable: "Devengado / IFRS", interpretacion: "Margen neto generado principalmente por el cobro de comisiones de administración a los patrimonios separados." },
      { name: "tipo_cambio_usd_clp", type: "DOUBLE", role: "Métrica", significado: "Dólar observado de cierre del Banco Central de Chile a la fecha de balance.", contable: "Mercado Spot BCCh", interpretacion: "Factor oficial de conversión cambiaria a moneda extranjera." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Activos totales convertidos a millones de USD.", contable: "Conversión FX Spot", interpretacion: "Dimensión del activo corporativo en divisa dura para comparabilidad regional." },
      { name: "total_pasivos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Pasivos totales convertidos a millones de USD.", contable: "Conversión FX Spot", interpretacion: "Masa de deuda propia en moneda extranjera." },
      { name: "patrimonio_neto_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto corporativo en millones de USD.", contable: "Conversión FX Spot", interpretacion: "Capital propio de solvencia valorizado en dólares." }
    ]
  },








{
    id: "patrimonios_separados_maestro",
    name: "patrimonios_separados.lista_emisiones",
    viewName: "patrimonios_separados_maestro",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados",
    norma: "CMF Chile — Ley 18.045 Título XVIII (Registro de Títulos de Deuda)",
    corte: "2026-06",
    frescura: "Registros Oficiales CMF",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "18 emisiones",
    descripcion: "Registro oficial de líneas y emisiones de bonos securitizados constituidos como Patrimonios Separados independientes conforme a la Ley de Mercado de Valores. Detalla el colateral subyacente, montos autorizados y vencimientos.",
    origen: "Comisión para el Mercado Financiero (CMF) — Inscripción de Títulos de Deuda mediante Registro Automático.",
    columnas: [
      { name: "numero_inscripcion", type: "VARCHAR", role: "PK", significado: "Número oficial de inscripción en el Registro de Valores de la CMF.", contable: "No aplica", interpretacion: "Código identificador legal único del programa de titulización." },
      { name: "fecha_inscripcion", type: "VARCHAR", role: "Dimensión", significado: "Fecha de autorización e inscripción del título en la CMF (YYYY-MM-DD).", contable: "No aplica", interpretacion: "Fecha de nacimiento jurídico de la línea de bonos securitizados." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT de la Sociedad Securitizadora que actúa como fiduciaria/gestora.", contable: "No aplica", interpretacion: "Clave foránea hacia securitizadoras_maestro." },
      { name: "razon_social_administradora", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la securitizadora emisora.", contable: "No aplica", interpretacion: "Entidad responsable de la emisión y cobranza de la cartera colateral." },
      { name: "denominacion_emision", type: "VARCHAR", role: "Dimensión", significado: "Nombre descriptivo oficial de la emisión / línea de títulos de deuda.", contable: "No aplica", interpretacion: "Denominación contractual del programa de bonos." },
      { name: "tipo_emision", type: "VARCHAR", role: "Dimensión", significado: "Modalidad de inscripción (LINEA, SERIE).", contable: "No aplica", interpretacion: "Estructura de emisión de títulos de securitización." },
      { name: "moneda", type: "VARCHAR", role: "Dimensión", significado: "Moneda o unidad de indexación de la emisión (UF, PESOS DE CHILE, DOLAR).", contable: "No aplica", interpretacion: "Unidad monetaria del servicio de amortizaciones e intereses." },
      { name: "monto_inscrito", type: "DOUBLE", role: "Métrica", significado: "Monto total autorizado e inscrito para la emisión en su moneda original.", contable: "Valor Nominal", interpretacion: "Capacidad máxima de colocación de bonos securitizados en el mercado de capitales." },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Dimensión", significado: "Fecha de vencimiento contractual final de la línea o serie (YYYY-MM-DD).", contable: "No aplica", interpretacion: "Plazo máximo de liquidación total del patrimonio separado." },
      { name: "clase_colateral_subyacente", type: "VARCHAR", role: "Dimensión", significado: "Clase de activo que nutre el patrimonio separado (Mutuos Hipotecarios, Factoring, Leasing, Automotriz).", contable: "Cartera Cedida", interpretacion: "Tipo de activo generador de los flujos de pago para los inversionistas institucionales." }
    ]
  },
  {
    id: "patrimonios_separados_balance",
    name: "patrimonios_separados.balance",
    viewName: "patrimonios_separados_balance",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados",
    norma: "Balance general del patrimonio separado (estados financieros publicados en la CMF)",
    corte: "Diciembre 2014 a diciembre 2025 (2010–2013 sin datos)",
    frescura: "Anual, cierre de diciembre",
    modo: "Lectura de los PDF de estados financieros, validada",
    ultimaActualizacion: "2026-09-28",
    registros: "358 balances · 7.962 cuentas",
    descripcion: "Balance general de cada patrimonio separado, cuenta por cuenta y tal como viene impreso, en M$ y con su signo: 358 balances de 10 securitizadoras. Incluye las líneas de subtotal (categorías que empiezan con Total). Todos los balances cuadran: activos = pasivo circulante + pasivo no circulante + patrimonio, y las cuentas de detalle suman su subtotal. Ojo: 'Total Pasivos' es pasivo más patrimonio (igual al total de activos); el pasivo exigible es 'Total Pasivo Circulante' + 'Total Pasivo No Circulante'. Para sumar sin contar dos veces, usa solo las categorías de detalle o solo las de Total. La serie parte en diciembre de 2014: de 2010 a 2013 no hay datos (2013 no está en la fuente y 2010–2012 se dejaron fuera para no cortar la serie).",
    origen: "Estados financieros de cada patrimonio separado (CMF) → securitizadoras/fuentes/balances_patrimonios_separados.xlsx → securitizadoras/scripts/05_publicar_balance_patrimonios.py",
    columnas: [
      { name: "archivo", type: "VARCHAR", role: "PK", significado: "PDF de estados financieros de donde sale el balance.", contable: "No aplica", interpretacion: "Identifica el balance; junto con orden_en_balance identifica la fila." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "Cuerpo del RUT de la securitizadora (8 dígitos, sin DV).", contable: "No aplica", interpretacion: "Une con securitizadoras_maestro.rut y patrimonios_separados_maestro.rut_administradora." },
      { name: "rut_completo", type: "VARCHAR", role: "Atributo", significado: "RUT con dígito verificador módulo 11.", contable: "No aplica", interpretacion: "Para mostrar." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Dimensión", significado: "Securitizadora que administra el patrimonio.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_patrimonio", type: "VARCHAR", role: "Dimensión", significado: "Código del patrimonio separado según el nombre del PDF (p. ej. BTRA15, PS13).", contable: "No aplica", interpretacion: "No siempre coincide con el número de inscripción de la lista de emisiones." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Cierre del balance, AAAA-MM (siempre diciembre).", contable: "Corte", interpretacion: "Cierre anual." },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año del cierre.", contable: "No aplica", interpretacion: "Sale del periodo." },
      { name: "orden_en_balance", type: "BIGINT", role: "Atributo", significado: "Posición de la cuenta en el balance impreso.", contable: "No aplica", interpretacion: "Ordena como en el PDF." },
      { name: "categoria", type: "VARCHAR", role: "Dimensión", significado: "Rubro: Activo Circulante, Activo No Circulante, Pasivo Circulante, Pasivo No Circulante, Patrimonio (Excedente Acumulado), o una línea Total ….", contable: "Clasificación del balance", interpretacion: "Las categorías que empiezan con Total son subtotales." },
      { name: "cuenta", type: "VARCHAR", role: "Dimensión", significado: "Nombre de la cuenta, copiado del balance.", contable: "Glosa", interpretacion: "No se renombró." },
      { name: "monto_m_clp", type: "BIGINT", role: "Métrica", significado: "Monto impreso en miles de pesos (M$), con su signo.", contable: "M$", interpretacion: "Las provisiones y los déficits vienen negativos." }
    ]
  },
  // =========================================================================
  // CAJAS DE COMPENSACION (CCAF / SUSESO - CMF)
  // =========================================================================
  {
    id: "ccaf_maestro",
    name: "ccaf.lista_entidades",
    viewName: "ccaf_maestro",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "SUSESO (Ley N° 18.833) / CMF (Ley N° 18.045 Emisores RVEMI)",
    corte: "Oficial 2026",
    frescura: "Catálogo Vigente",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "6 entidades",
    descripcion: "Catálogo institucional maestro de las Cajas de Compensación de Asignación Familiar (CCAF) de Chile. Consolida las 4 entidades activas del sistema de previsión y bienestar social, así como las 2 entidades históricas absorbidas, con sus respectivos marcos regulatorios SUSESO y registros de emisión de bonos ante la CMF.",
    origen: "Superintendencia de Seguridad Social (SUSESO) y Comisión para el Mercado Financiero (CMF) — Registro de Valores (RVEMI).",
    columnas: [
      { name: "rut", type: "BIGINT", role: "PK", significado: "Rol Único Tributario numérico de la Caja de Compensación.", contable: "No aplica", interpretacion: "Identificador unívoco corporativo de la institución previsional." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador del RUT según algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Validación de integridad del identificador legal." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT formateado con separadores de miles y guion (ej: 81.826.800-9).", contable: "No aplica", interpretacion: "Representación estándar tributaria." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Nombre legal formal de la Corporación de Derecho Privado.", contable: "No aplica", interpretacion: "Denominación legal inscrita en el registro público de la SUSESO." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre comercial o de fantasía (Los Andes, La Araucana, Los Héroes, Caja 18).", contable: "No aplica", interpretacion: "Marca de cara a afiliados, pensionados y mercado financiero." },
      { name: "tipo_entidad", type: "VARCHAR", role: "Dimensión", significado: "Clasificación institucional: Caja de Compensación de Asignación Familiar.", contable: "No aplica", interpretacion: "Entidad de seguridad social sin fines de lucro." },
      { name: "marco_legal", type: "VARCHAR", role: "Dimensión", significado: "Normativa habilitante: Ley N° 18.833 (Estatuto General de CCAF).", contable: "No aplica", interpretacion: "Régimen legal especial aplicable a la administración del régimen de prestaciones familiares y crédito social." },
      { name: "naturaleza_juridica", type: "VARCHAR", role: "Dimensión", significado: "Corporación de Derecho Privado sin fines de lucro.", contable: "No aplica", interpretacion: "Estructura asociativa que no reparte dividendos a accionistas; reinvierte sus excedentes." },
      { name: "regulador_primario", type: "VARCHAR", role: "Dimensión", significado: "Organismo supervisor técnico principal: SUSESO.", contable: "No aplica", interpretacion: "Superintendencia encargada de autorizar estatutos, balances y topes de crédito social." },
      { name: "regulador_mercado_valores", type: "VARCHAR", role: "Dimensión", significado: "Supervisión de oferta pública de valores: 'CMF (Emisor de Bonos)' o 'No Aplica (Supervisión Exclusiva SUSESO)'.", contable: "No aplica", interpretacion: "Distingue a las CCAF con emisiones de bonos en el mercado de valores de aquellas con supervisión exclusivamente previsional." },
      { name: "emisor_valores_cmf", type: "BOOLEAN", role: "Dimensión", significado: "Indica si la Caja está registrada como Emisor de Valores (RVEMI) en la CMF.", contable: "No aplica", interpretacion: "True para Los Andes, La Araucana y Los Héroes; False para Caja 18." },
      { name: "codigo_cmf", type: "VARCHAR", role: "Dimensión", significado: "Código institucional en la base de datos de la CMF.", contable: "No aplica", interpretacion: "Identificador asignado en el Registro de Valores de la CMF." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Condición operativa: 'Vigente' (4 entidades) o 'Absorbida' (2 entidades históricas).", contable: "No aplica", interpretacion: "Filtro para análisis de entidades en marcha vs series históricas." },
      { name: "ano_fundacion", type: "BIGINT", role: "Dimensión", significado: "Año de inicio de actividades institucionales.", contable: "No aplica", interpretacion: "Antigüedad corporativa de la institución en el sistema de seguridad social." },
      { name: "domicilio_casa_matriz", type: "VARCHAR", role: "Dimensión", significado: "Dirección de la sede central corporativa.", contable: "No aplica", interpretacion: "Domicilio legal para efectos regulatorios y contractuales." },
      { name: "comuna", type: "VARCHAR", role: "Dimensión", significado: "Comuna de la sede central.", contable: "No aplica", interpretacion: "Ubicación geográfica de la casa matriz." },
      { name: "region", type: "VARCHAR", role: "Dimensión", significado: "Región administrativa chilena.", contable: "No aplica", interpretacion: "Jurisdicción regional de la sede corporativa." },
      { name: "sitio_web", type: "VARCHAR", role: "Dimensión", significado: "Portal institucional oficial en internet.", contable: "No aplica", interpretacion: "Acceso a información corporativa y memoria anual." },
      { name: "cmf_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace directo al expediente del emisor en el portal de la CMF.", contable: "No aplica", interpretacion: "Ficha oficial de fiscalizado en el mercado de valores." },
      { name: "suseso_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace oficial a la sección de estados financieros de la SUSESO.", contable: "No aplica", interpretacion: "Repositorio institucional de balances y memorias de la entidad." },
      { name: "lineas_deuda_registradas", type: "BOOLEAN", role: "Dimensión", significado: "Indica si posee líneas de bonos corporativos vigentes o registradas en la CMF.", contable: "No aplica", interpretacion: "Evidencia de financiamiento mediante instrumentos de renta fija pública." },
      { name: "observaciones", type: "VARCHAR", role: "Dimensión", significado: "Notas regulatorias, prestaciones sociales y alcance institucional.", contable: "No aplica", interpretacion: "Contexto operacional y de seguridad social clave de cada Caja." }
    ]
  },
  // =========================================================================
  // ADMINISTRADORAS GENERALES DE FONDOS (AGF - Ley N° 20.712)
  // =========================================================================
  {
    id: "agf_maestro",
    name: "agf.lista_administradoras",
    viewName: "agf_maestro",
    sector: "agf",
    sectorLabel: "Administradoras Generales de Fondos",
    norma: "Ley Única de Fondos (Ley N° 20.712 - LUF) / CMF",
    corte: "Oficial CMF 2026",
    frescura: "Catálogo Vigente",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "68 entidades",
    descripcion: "Catálogo oficial de Administradoras Generales de Fondos (AGF) autorizadas por la Comisión para el Mercado Financiero (CMF) bajo la Ley N° 20.712. Incluye 52 gestoras vigentes y 16 no vigentes/canceladas, junto con su grupo financiero controlador y el número de fondos de inversión administrados.",
    origen: "Comisión para el Mercado Financiero (CMF) — Registro de Administradoras Generales de Fondos (RGAGF / RACRT).",
    columnas: [
      { name: "rut", type: "BIGINT", role: "PK", significado: "Rol Único Tributario numérico de la sociedad administradora.", contable: "No aplica", interpretacion: "Identificador tributario corporativo único de la AGF." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador calculado según algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Validación de integridad del identificador legal." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT estándar con separadores de miles y guion (ej: 96.666.870-7).", contable: "No aplica", interpretacion: "Formato canónico para consultas tributarias y regulatorias." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social formal inscrita en el registro público de la CMF.", contable: "No aplica", interpretacion: "Nombre legal de la sociedad anónima especial fiduciaria." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre comercial o marca fiduciaria de la gestora.", contable: "No aplica", interpretacion: "Identidad comercial ante inversionistas institucionales y retail." },
      { name: "tipo_entidad", type: "VARCHAR", role: "Dimensión", significado: "Clasificación institucional: Administradora General de Fondos.", contable: "No aplica", interpretacion: "Entidad fiduciaria habilitada por ley para gestionar carteras colectivas." },
      { name: "marco_legal", type: "VARCHAR", role: "Dimensión", significado: "Ley N° 20.712 (Ley Única de Fondos - LUF).", contable: "No aplica", interpretacion: "Régimen legal marco para fondos mutuos, de inversión y administración de carteras." },
      { name: "naturaleza_juridica", type: "VARCHAR", role: "Dimensión", significado: "Sociedad Anónima Especial con giro exclusivo.", contable: "No aplica", interpretacion: "Obligación de mantener patrimonio mínimo de 10.000 UF y separación patrimonial." },
      { name: "regulador", type: "VARCHAR", role: "Dimensión", significado: "Comisión para el Mercado Financiero (CMF).", contable: "No aplica", interpretacion: "Supervisor fiduciario, contable y de solvencia de la gestora." },
      { name: "codigo_cmf", type: "VARCHAR", role: "Dimensión", significado: "Código institucional asignado por la CMF.", contable: "No aplica", interpretacion: "Identificador técnico en los repositorios de información financiera de la CMF." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Condición en el registro: 'Vigente' (52) o 'No Vigente / Cancelada' (16).", contable: "No aplica", interpretacion: "Permite aislar gestoras actualmente activas de liquidaciones o fusiones históricas." },
      { name: "grupo_controlador", type: "VARCHAR", role: "Dimensión", significado: "Conglomerado financiero o clasificación de control (Banco de Chile, Santander, Bci, LarrainVial, Moneda, etc.).", contable: "No aplica", interpretacion: "Identifica la pertenencia a banca múltiple o a gestoras independientes de nicho." },
      { name: "domicilio_casa_matriz", type: "VARCHAR", role: "Dimensión", significado: "Dirección de la sede corporativa de la AGF.", contable: "No aplica", interpretacion: "Sede de operaciones y atención a inversionistas." },
      { name: "ciudad", type: "VARCHAR", role: "Dimensión", significado: "Ciudad de la casa matriz.", contable: "No aplica", interpretacion: "Localización geográfica corporativa." },
      { name: "region", type: "VARCHAR", role: "Dimensión", significado: "Región administrativa chilena.", contable: "No aplica", interpretacion: "Jurisdicción administrativa." },
      { name: "cmf_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace directo al expediente del fiscalizado en el portal de la CMF.", contable: "No aplica", interpretacion: "Acceso expedito a la ficha pública, hechos esenciales y nómina de directores." },
      { name: "fondos_inversion_administrados", type: "BIGINT", role: "Métrica", significado: "Número de Fondos de Inversión (FI) públicos reportados bajo administración de la AGF.", contable: "No aplica", interpretacion: "Proxy de escala de operación y amplitud de oferta de vehículos de inversión." }
    ]
  },
  {
    id: "agf_balance",
    name: "agf.balance",
    viewName: "agf_balance",
    sector: "agf",
    sectorLabel: "Administradoras Generales de Fondos",
    norma: "IFRS, estado de situación financiera individual (CMF)",
    corte: "2018-03 a 2026-06, trimestral",
    frescura: "Corrida manual del 2026-09-23",
    modo: "Automático (script local, sin GitHub Actions)",
    ultimaActualizacion: "2026-09-28",
    registros: "1.572 balances",
    descripcion: "Balance propio de cada AGF vigente, trimestre a trimestre (no incluye los fondos que administra). Viene de la pestaña Información Financiera de la CMF. Cifras en millones de pesos (MM$), porque la CMF publica en miles y aquí se dividen por 1.000. Todos cuadran activos = pasivos + patrimonio. Cotejado al peso contra la CMF en Banchile AGF, diciembre 2024 y 2025.",
    origen: "cmfchile.cl → agf/scripts/stream_cmf_agf.py → agf/fuentes/agf_eeff_cmf.parquet → agf/scripts/publicar_agf_balance_resultados.py",
    columnas: [
      { name: "rut", type: "BIGINT", role: "FK", significado: "RUT de la AGF, sin dígito verificador.", contable: "No aplica", interpretacion: "Une con agf_maestro.rut y con agf_resultados." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Cierre trimestral AAAA-MM (03, 06, 09, 12).", contable: "Corte", interpretacion: "Saldo a esa fecha." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la AGF.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "total_activos_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos, en MM$.", contable: "Total de activos", interpretacion: "Tamaño del balance propio." },
      { name: "total_pasivos_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos, en MM$.", contable: "Total de pasivos", interpretacion: "Obligaciones de la gestora." },
      { name: "patrimonio_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio total, en MM$.", contable: "Patrimonio total", interpretacion: "Capital propio." },
      { name: "efectivo_equivalentes_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Efectivo y equivalentes al efectivo, en MM$.", contable: "Efectivo y equivalentes al efectivo", interpretacion: "Liquidez inmediata." },
      { name: "otros_activos_financieros_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Línea Otros activos financieros, en MM$. Suele ser inversión en cuotas de fondos propios.", contable: "Otros activos financieros", interpretacion: "Un 0 puede ser un cero real o que la AGF no usa esa línea exacta (p. ej. la separa en corriente y no corriente). Viene en 0 en el 89% de las filas." },
      { name: "total_activos_mm_usd", type: "DOUBLE", role: "Métrica", significado: "Total de activos en millones de USD, al dólar de cierre del mes (macro_divisas_mercado).", contable: "Conversión", interpretacion: "Para comparar en dólares." },
      { name: "patrimonio_mm_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio en millones de USD, al dólar de cierre.", contable: "Conversión", interpretacion: "Para comparar en dólares." }
    ]
  },
  {
    id: "agf_resultados",
    name: "agf.resultados",
    viewName: "agf_resultados",
    sector: "agf",
    sectorLabel: "Administradoras Generales de Fondos",
    norma: "IFRS, estado de resultados por función, individual (CMF)",
    corte: "2018-03 a 2026-06, trimestral",
    frescura: "Corrida manual del 2026-09-23",
    modo: "Automático (script local, sin GitHub Actions)",
    ultimaActualizacion: "2026-09-28",
    registros: "1.572 trimestres",
    descripcion: "Estado de resultados propio de cada AGF vigente, en MM$. La CMF lo publica acumulado desde enero, así que marzo trae 3 meses y diciembre el año completo. El ingreso del trimestre se calcula restando el acumulado del trimestre anterior. Por ahora solo hay ingresos. Gastos de administración y Ganancia (pérdida) vienen NULL: la CMF sí los publica, pero el scraper no los capturó por un problema con las tildes. Ya está corregido y se llenarán en la próxima corrida de stream_cmf_agf.py.",
    origen: "cmfchile.cl → agf/scripts/stream_cmf_agf.py → agf/fuentes/agf_eeff_cmf.parquet → agf/scripts/publicar_agf_balance_resultados.py",
    columnas: [
      { name: "rut", type: "BIGINT", role: "FK", significado: "RUT de la AGF, sin dígito verificador.", contable: "No aplica", interpretacion: "Une con agf_maestro.rut y con agf_balance." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Cierre trimestral AAAA-MM.", contable: "Corte", interpretacion: "Fin del período acumulado." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la AGF.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "meses_acumulados", type: "BIGINT", role: "Atributo", significado: "Meses que cubren las cifras acumuladas (3, 6, 9 o 12).", contable: "Período IFRS", interpretacion: "Con 12 es el año completo." },
      { name: "ingresos_ordinarios_acum_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Ingresos de actividades ordinarias acumulados desde enero, en MM$. Son principalmente comisiones de administración.", contable: "Ingresos de actividades ordinarias", interpretacion: "No sumar trimestres de un mismo año: ya vienen acumulados." },
      { name: "ingresos_ordinarios_trimestre_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Ingresos solo de ese trimestre, en MM$: el acumulado menos el acumulado del trimestre anterior.", contable: "Derivado", interpretacion: "NULL si falta el trimestre anterior (35 casos). Un valor negativo indica una reexpresión (1 caso)." },
      { name: "gastos_administracion_acum_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Gastos de administración acumulados desde enero, en MM$.", contable: "Gastos de administración", interpretacion: "NULL por ahora: no capturado en la corrida del 2026-09-23." },
      { name: "ganancia_perdida_acum_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Ganancia (pérdida) acumulada desde enero, en MM$.", contable: "Ganancia (pérdida)", interpretacion: "NULL por ahora: no capturado en la corrida del 2026-09-23." }
    ]
  },

  // =========================================================================
  // SISTEMAS DE PAGO (BCCh / CMF)
  // =========================================================================
  {
    id: "sistemas_pago_maestro",
    name: "sistemas_pago.lista_entidades",
    viewName: "sistemas_pago_maestro",
    sector: "sistemas_pago",
    sectorLabel: "Sistemas de Pago",
    norma: "Ley Orgánica Constitucional BCCh (Ley 18.840) / Ley 18.876 (DCV) / Ley 20.345 (Cámaras) / Compendio Normas Financieras BCCh",
    corte: "Catálogo Oficial Vigente",
    frescura: "Trimestral / Eventos Registrales",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "12 entidades",
    descripcion: "Catálogo maestro de infraestructuras críticas del sistema financiero chileno: sistemas de liquidación bruta en tiempo real (LBTR-BCCh), cámaras de compensación de alto valor (Combanc), custodia centralizada de valores (DCV), contrapartes centrales para derivados OTC (ComDer) y valores (CCLV), cámara de compensación minorista (CCA), y redes de adquirencia y procesamiento de tarjetas de pago (Transbank, Getnet, Klap, Redelcom, Nexus, Banchile Pagos).",
    origen: "Banco Central de Chile (BCCh) y Comisión para el Mercado Financiero (CMF).",
    columnas: [
      { name: "rut", type: "BIGINT", role: "PK", significado: "RUT institucional sin dígito verificador.", contable: "No aplica", interpretacion: "Identificador tributario primario de la infraestructura o cámara." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador oficial verificado bajo Módulo 11.", contable: "No aplica", interpretacion: "Validación de integridad tributaria." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT en formato canónico con puntos y guion.", contable: "No aplica", interpretacion: "Formato canónico para reportes y visualización." },
      { name: "codigo_sistema", type: "VARCHAR", role: "Dimensión", significado: "Sigla de identificación de mercado (LBTR, COMBANC, DCV, COMDER, CCLV, CCA, TRANSBANK, GETNET, KLAP, REDELCOM, BANCHILE-PAGOS, NEXUS).", contable: "No aplica", interpretacion: "Código estándar en la arquitectura interbancaria." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social jurídica inscrita en registros públicos.", contable: "No aplica", interpretacion: "Sociedad anónima titular de la infraestructura." },
      { name: "nombre_comercial", type: "VARCHAR", role: "Dimensión", significado: "Marca o nombre de fantasía operativo.", contable: "No aplica", interpretacion: "Denominación pública del servicio." },
      { name: "tipo_sistema", type: "VARCHAR", role: "Dimensión", significado: "Categoría de infraestructura: Liquidación Alto Valor, CCAV, CPBV, Contraparte Central, Custodia Centralizada u Operador Adquirente.", contable: "No aplica", interpretacion: "Rol sistémico en el procesamiento de transacciones." },
      { name: "marco_legal", type: "VARCHAR", role: "Dimensión", significado: "Cuerpo normativo regulatorio aplicable.", contable: "No aplica", interpretacion: "Estatuto legal de constitución y autorización." },
      { name: "supervisor", type: "VARCHAR", role: "Dimensión", significado: "Regulador sectorial (CMF / BCCh).", contable: "No aplica", interpretacion: "Mandato de fiscalización y estabilidad financiera." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Estado de operación: Vigente.", contable: "No aplica", interpretacion: "Condición de funcionamiento activa." },
      { name: "domicilio_casa_matriz", type: "VARCHAR", role: "Dimensión", significado: "Dirección legal de la sede principal corporativa.", contable: "No aplica", interpretacion: "Ubicación administrativa." },
      { name: "comuna", type: "VARCHAR", role: "Dimensión", significado: "Comuna de la casa matriz.", contable: "No aplica", interpretacion: "Distribución geográfica institucional." },
      { name: "region", type: "VARCHAR", role: "Dimensión", significado: "Región administrativa chilena.", contable: "No aplica", interpretacion: "Jurisdicción territorial." },
      { name: "cmf_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace web a la ficha institucional oficial en CMF o BCCh.", contable: "No aplica", interpretacion: "Trazabilidad de supervisión pública." }
    ]
  },
  // =========================================================================
  // FINTECH & FINANZAS ABIERTAS (Ley N° 21.521 / CMF)
  // =========================================================================
  {
    id: "fintech_rpsf_maestro",
    name: "fintech.lista_entidades",
    viewName: "fintech_rpsf_maestro",
    sector: "fintech",
    sectorLabel: "FinTech",
    norma: "Ley N° 21.521 (Ley Fintec) / Norma de Carácter General CMF N° 502",
    corte: "Catálogo Oficial Vigente CMF",
    frescura: "Actualización Continua / Eventos Registrales CMF",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "262 entidades",
    descripcion: "Registro de Prestadores de Servicios Financieros (RPSF) de la CMF. Catálogo integral de las entidades FinTech que operan bajo el perímetro regulatorio de la Ley Fintec en Chile. Incluye personas jurídicas y naturales, estado de vigencia, número y fecha de inscripción oficial, código institucional CMF, datos de contacto y total de servicios autorizados.",
    origen: "Comisión para el Mercado Financiero (CMF) — Registro de Prestadores de Servicios Financieros (RPSF).",
    columnas: [
      { name: "rut", type: "BIGINT", role: "PK", significado: "RUT tributario del prestador FinTech.", contable: "No aplica", interpretacion: "Identificador tributario corporativo verificado bajo Módulo 11." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador oficial.", contable: "No aplica", interpretacion: "Validación tributaria oficial." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT en formato canónico con puntos y guion.", contable: "No aplica", interpretacion: "Formato canónico para reportes y visualización." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social formal legal de la empresa FinTech.", contable: "No aplica", interpretacion: "Entidad jurídica inscrita ante la CMF." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre comercial o marca operativa de la plataforma.", contable: "No aplica", interpretacion: "Marca con la que opera frente al público." },
      { name: "tipo_persona", type: "VARCHAR", role: "Dimensión", significado: "Clasificación: Persona Jurídica o Persona Natural.", contable: "No aplica", interpretacion: "Estructura jurídica del prestador." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Condición operativa: Vigente o No Vigente.", contable: "No aplica", interpretacion: "Habilitación legal para operar servicios en el mercado." },
      { name: "codigo_institucion_cmf", type: "VARCHAR", role: "Dimensión", significado: "Código correlativo institucional asignado por CMF.", contable: "No aplica", interpretacion: "Identificador de supervisión en bases de datos CMF." },
      { name: "numero_inscripcion", type: "VARCHAR", role: "Dimensión", significado: "Número correlativo de registro en el RPSF.", contable: "No aplica", interpretacion: "Número de folio registral oficial." },
      { name: "fecha_inscripcion", type: "VARCHAR", role: "Dimensión", significado: "Fecha oficial de incorporación al RPSF.", contable: "No aplica", interpretacion: "Inicio del perímetro de supervisión FinTech." },
      { name: "fecha_cancelacion", type: "VARCHAR", role: "Dimensión", significado: "Fecha de revocación o cancelación registral (si aplica).", contable: "No aplica", interpretacion: "Cese de actividades reguladas." },
      { name: "servicios_acreditados_total", type: "BIGINT", role: "Métrica", significado: "Cantidad total de servicios financieros tipificados que la entidad tiene autorizados o eximidos.", contable: "No aplica", interpretacion: "Amplitud del alcance operativo de la FinTech." },
      { name: "comuna", type: "VARCHAR", role: "Dimensión", significado: "Comuna de la sede principal corporativa.", contable: "No aplica", interpretacion: "Localización geográfica del prestador." },
      { name: "region", type: "VARCHAR", role: "Dimensión", significado: "Región administrativa chilena.", contable: "No aplica", interpretacion: "Jurisdicción geográfica." },
      { name: "email_contacto", type: "VARCHAR", role: "Dimensión", significado: "Correo electrónico institucional de contacto.", contable: "No aplica", interpretacion: "Canal oficial de comunicación corporativa." },
      { name: "sitio_web", type: "VARCHAR", role: "Dimensión", significado: "URL de la plataforma tecnológica o portal web.", contable: "No aplica", interpretacion: "Plataforma de interfaz de usuario digital." },
      { name: "cmf_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace a la ficha institucional pública en el portal CMF.", contable: "No aplica", interpretacion: "Trazabilidad oficial de fiscalización." }
    ]
  },
  {
    id: "ccaf_maestro",
    name: "ccaf.lista_entidades",
    viewName: "ccaf_maestro",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "Ley N° 18.833 / SUSESO",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "6 entidades",
    descripcion: "Catálogo maestro de Cajas de Compensación de Asignación Familiar en Chile (4 vigentes: Los Andes, La Araucana, Los Héroes, 18 de Septiembre; y 2 absorbidas: Gabriela Mistral y Javiera Carrera), detallando su estructura jurídica, reguladores primarios y líneas de deuda CMF.",
    origen: "Superintendencia de Seguridad Social (SUSESO) & Comisión para el Mercado Financiero (CMF).",
    columnas: [
      { name: "rut", type: "BIGINT", role: "PK", significado: "RUT institucional de la Caja de Compensación sin dígito verificador.", contable: "No aplica" },
      { name: "dv", type: "VARCHAR", role: "Atributo", significado: "Dígito verificador del RUT.", contable: "No aplica" },
      { name: "rut_completo", type: "VARCHAR", role: "Atributo", significado: "RUT institucional completo con formato estándar.", contable: "No aplica" },
      { name: "razon_social", type: "VARCHAR", role: "Atributo", significado: "Razón social oficial de la CCAF según estatutos vigentes.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial o de fantasía de la corporación.", contable: "No aplica" },
      { name: "tipo_entidad", type: "VARCHAR", role: "Atributo", significado: "Tipo de entidad: Caja de Compensación de Asignación Familiar.", contable: "No aplica" },
      { name: "marco_legal", type: "VARCHAR", role: "Atributo", significado: "Marco legal habilitante (Ley N° 18.833 y decretos complementarios).", contable: "No aplica" },
      { name: "naturaleza_juridica", type: "VARCHAR", role: "Atributo", significado: "Naturaleza jurídica: Corporación de derecho privado sin fines de lucro.", contable: "No aplica" },
      { name: "regulador_primario", type: "VARCHAR", role: "Atributo", significado: "Organismo regulador y fiscalizador primario: SUSESO.", contable: "No aplica" },
      { name: "regulador_mercado_valores", type: "VARCHAR", role: "Atributo", significado: "Regulador del mercado de valores y emisor de deuda: CMF.", contable: "No aplica" },
      { name: "emisor_valores_cmf", type: "BOOLEAN", role: "Atributo", significado: "Indica si la CCAF está formalmente registrada como emisor de valores en la CMF.", contable: "No aplica" },
      { name: "codigo_cmf", type: "VARCHAR", role: "Atributo", significado: "Código identificador en el registro de emisores CMF.", contable: "No aplica" },
      { name: "estado_vigencia", type: "VARCHAR", role: "Atributo", significado: "Estado operativo de la institución: Vigente o Absorbida.", contable: "No aplica" },
      { name: "ano_fundacion", type: "BIGINT", role: "Dimensión", significado: "Año oficial de constitución de la Caja de Compensación.", contable: "No aplica" },
      { name: "domicilio_casa_matriz", type: "VARCHAR", role: "Atributo", significado: "Dirección postal de la casa matriz institucional.", contable: "No aplica" },
      { name: "comuna", type: "VARCHAR", role: "Atributo", significado: "Comuna donde se ubica la sede central.", contable: "No aplica" },
      { name: "region", type: "VARCHAR", role: "Atributo", significado: "Región administrativa chilena de la casa matriz.", contable: "No aplica" },
      { name: "sitio_web", type: "VARCHAR", role: "Atributo", significado: "Sitio web oficial corporativo.", contable: "No aplica" },
      { name: "cmf_url", type: "VARCHAR", role: "Atributo", significado: "Enlace directo al perfil público en el portal CMF.", contable: "No aplica" },
      { name: "suseso_url", type: "VARCHAR", role: "Atributo", significado: "Enlace directo a las fichas oficiales del portal SUSESO.", contable: "No aplica" },
      { name: "lineas_deuda_registradas", type: "BOOLEAN", role: "Atributo", significado: "Indica si mantiene líneas vigentes de bonos corporativos o efectos de comercio.", contable: "No aplica" },
      { name: "observaciones", type: "VARCHAR", role: "Atributo", significado: "Notas explicativas, fusiones o antecedentes históricos relevantes.", contable: "No aplica" }
    ]
  },
  {
    id: "ccaf_caratula_totales",
    name: "ccaf.balances",
    viewName: "ccaf_caratula_totales",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "Circular SUSESO / IFRS CMF",
    corte: "2025-06",
    frescura: "Serie Histórica 2010-2025",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "288 filas · 72 balances (4 cuentas c/u)",
    descripcion: "Serie histórica oficial de carátula de balances (2010-2025) para las Cajas de Compensación chilenas bajo norma IFRS. Comprende los 4 asientos de cierre: Activo Total (10000), Pasivo Total (20000), Patrimonio Total (23000) y Utilidad Neta / Excedente (23050), con distinción estricta de alcance contable Consolidado vs Individual.",
    origen: "SUSESO & CMF — Balances FECU y Estados Financieros Auditados.",
    columnas: [
      { name: "ano", type: "BIGINT", role: "Fecha", significado: "Año fiscal de corte del estado de situación financiera.", contable: "No aplica" },
      { name: "mes", type: "BIGINT", role: "Fecha", significado: "Mes de cierre del reporte (12 para anual auditado, 6 para semestral interino).", contable: "No aplica" },
      { name: "ccaf", type: "VARCHAR", role: "Dimensión", significado: "Nombre o sigla de la Caja de Compensación (Los Andes, La Araucana, Los Héroes, 18 de Septiembre).", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT institucional de la CCAF (vinculado a ccaf_maestro).", contable: "No aplica" },
      { name: "tipo_eeff", type: "VARCHAR", role: "Dimensión", significado: "Alcance contable del reporte financiero: Consolidado o Individual.", contable: "No aplica" },
      { name: "asiento_contable", type: "VARCHAR", role: "Dimensión", significado: "Nombre estandarizado del rubro contable de carátula.", contable: "No aplica" },
      { name: "monto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto expresado en millones de pesos chilenos ($M CLP).", contable: "Costo Amortizado / Devengado" },
      { name: "monto_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Monto original auditado en miles de pesos chilenos ($Miles CLP).", contable: "Costo Amortizado / Devengado" },
      { name: "codigo_fecu", type: "VARCHAR", role: "Atributo", significado: "Código estandarizado FECU (10000 Activos, 20000 Pasivos, 23000 Patrimonio, 23050 Excedentes).", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda de reporte contable oficial (CLP).", contable: "No aplica" },
      { name: "escala", type: "VARCHAR", role: "Atributo", significado: "Escala numérica del estado financiero (Miles de pesos).", contable: "No aplica" }
    ]
  },
  {
    id: "ffmm_repos_detalle_historico",
    name: "ffmm.repos_contratos",
    viewName: "ffmm_repos_detalle_historico",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "IFRS / CMF Ley 20.712",
    corte: "2010-2025",
    frescura: "Muestra 2010-2025 · sin auditar",
    modo: "Experimental (extracción en revisión)",
    ultimaActualizacion: "2026-09-26",
    registros: "388 contratos",
    descripcion: "Extracción preliminar, contrato por contrato, de operaciones de compra con retroventa (REPO / SFT) en notas de estados financieros de fondos mutuos, en 16 cierres anuales de diciembre entre 2010 y 2025. Cada fila pretende representar un contrato: contraparte, instrumento, fechas, monto transado y saldo al cierre. Los montos se rotulan provisionalmente en miles de pesos (M$), pero su escala todavía debe verificarse contra cada documento original.",
    advertencia: "Falta auditar contra los PDF originales de la CMF. No implica cobertura exhaustiva ni confiabilidad de montos/unidades. Hay campos incompletos (por ejemplo, 70 de 388 contratos sin fecha de vencimiento y 133 sin nemotécnico) y al menos un saldo de 40.090.000.000 unidades registradas en 2022 que requiere verificación. No usar totales, rankings ni cifras de mercado derivados de esta muestra. Un saldo de repo no es el portafolio ni el pasivo total de un fondo.",
    origen: "Comisión para el Mercado Financiero (CMF) — nota de pactos de retroventa de los estados financieros de fondos mutuos (PDF), complementada con la información financiera histórica de la CMF.",
    columnas: [
      { name: "run_fondo", type: "BIGINT", role: "PK", significado: "RUN del fondo mutuo comprador en el pacto de retroventa.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Razón social del fondo mutuo tenedor del contrato REPO.", contable: "No aplica" },
      { name: "rut_agf", type: "VARCHAR", role: "FK", significado: "RUT de la Administradora General de Fondos que gestiona el fondo comprador.", contable: "No aplica" },
      { name: "razon_social_agf", type: "VARCHAR", role: "Dimensión", significado: "Nombre de la Administradora General de Fondos (AGF).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo anual de reporte contable (YYYYMM).", contable: "No aplica" },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año calendario del cierre contable.", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Fecha original de compra del instrumento financiero bajo pacto.", contable: "No aplica" },
      { name: "rut_contraparte", type: "VARCHAR", role: "FK", significado: "RUT institucional de la contraparte financiera vendedora.", contable: "No aplica" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la institución financiera contraparte (Banco / Corredora).", contable: "No aplica" },
      { name: "clasificacion_riesgo", type: "VARCHAR", role: "Atributo", significado: "Clasificación de riesgo del instrumento o contraparte cuando el documento la declara (puede venir como NA).", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Dimensión", significado: "Nemotécnico oficial del instrumento subyacente transado.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Dimensión", significado: "Tipo de instrumento subyacente (BTP, BTU, PDBC, BCU, BCP, DP).", contable: "No aplica" },
      { name: "unidades_nominales", type: "DOUBLE", role: "Métrica", significado: "Cantidad nominal comprometida en el contrato de retroventa.", contable: "No aplica" },
      { name: "total_transado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto transado al inicio del contrato. Rotulado provisionalmente como miles de pesos (M$); aún falta validar la unidad y el número contra el PDF original. Puede venir en cero.", contable: "Pacto Activo (CRV)" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha acordada de vencimiento de la promesa de venta.", contable: "No aplica" },
      { name: "precio_pactado_tasa", type: "VARCHAR", role: "Métrica", significado: "Precio pactado o tasa de interés de la operación, tal como aparece en el documento (texto).", contable: "No aplica" },
      { name: "saldo_al_cierre_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo del contrato al cierre del ejercicio. Rotulado provisionalmente como miles de pesos (M$); aún falta verificar el monto y la escala contra el PDF. No equivale al patrimonio o pasivo total del fondo.", contable: "Pacto Activo (CRV)" },
      { name: "pagina_pdf", type: "BIGINT", role: "Atributo", significado: "Página del PDF de la CMF de donde se leyó el contrato. Permite volver al documento para auditarlo.", contable: "No aplica" }
    ]
  },
  {
    id: "cooperativas_maestro",
    name: "cooperativas.lista_entidades",
    viewName: "cooperativas_maestro",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito",
    norma: "CMF Chile / Ley General de Cooperativas (DFL 5)",
    corte: "2026-07",
    frescura: "Al día (7 entidades sistémicas)",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "7 entidades",
    descripcion: "Catastro maestro y directorio institucional de las Cooperativas de Ahorro y Crédito (CAC) de importancia sistémica supervisadas por la CMF. Incluye Coopeuch, Oriencoop, Capual, Ahorrocoop, Detacoop, Coonfia y Coocretal con RUT canónico validado bajo Módulo 11. Criterio de inclusión: cooperativas fiscalizadas por la CMF (art. 87 Ley General de Cooperativas, patrimonio sobre UF 400.000), según la nómina vigente CMF. Cooperativas bajo supervisión DAES (p. ej. Norte Grande, Financoop) no se incluyen porque no reportan estados financieros comparables a la CMF.",
    origen: "Comisión para el Mercado Financiero (CMF) — Nómina de Cooperativas de Ahorro y Crédito Fiscalizadas.",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Rol Único Tributario canónico con guión y dígito verificador.", contable: "No aplica", interpretacion: "Identificador institucional único para interoperabilidad con el sistema financiero." },
      { name: "rut_cuerpo", type: "VARCHAR", role: "Dimensión", significado: "Cuerpo numérico del RUT sin separador de miles ni dígito verificador.", contable: "No aplica", interpretacion: "Clave numérica para cruces relacionales." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador oficial validado bajo algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Garantía de integridad y consistencia matemática de la cédula tributaria." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social corporativa completa inscrita en el registro CMF y DAES.", contable: "No aplica", interpretacion: "Denominación legal oficial de la entidad cooperativa." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre comercial o marca de atención pública de la cooperativa.", contable: "No aplica", interpretacion: "Identificador comercial estándar (ej. COOPEUCH, ORIENCOOP)." },
      { name: "tipo_institucion", type: "VARCHAR", role: "Dimensión", significado: "Clasificación sectorial: Cooperativa de Ahorro y Crédito (CAC).", contable: "No aplica", interpretacion: "Régimen regulatorio especial bajo supervisión CMF y Ministerio de Economía." },
      { name: "regulador_principal", type: "VARCHAR", role: "Dimensión", significado: "Ente regulador primario: CMF Chile.", contable: "No aplica", interpretacion: "Supervisión prudencial y solvencia financiera." },
      { name: "sede_matriz", type: "VARCHAR", role: "Dimensión", significado: "Ciudad sede de la casa matriz u oficinas centrales de la cooperativa.", contable: "No aplica", interpretacion: "Ubicación geográfica principal de la gestión directiva." },
      { name: "region", type: "VARCHAR", role: "Dimensión", significado: "Región administrativa chilena donde radica la casa central.", contable: "No aplica", interpretacion: "Distribución territorial y descentralización del sistema de cooperativas." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Condición operativa ante el regulador: VIGENTE.", contable: "No aplica", interpretacion: "Certificación de operación activa y supervisión vigente." },
      { name: "fecha_fundacion", type: "VARCHAR", role: "Dimensión", significado: "Fecha fundacional histórica de la institución cooperativa.", contable: "No aplica", interpretacion: "Trayectoria y madurez institucional en el mercado financiero chileno." },
      { name: "es_sistemica", type: "BOOLEAN", role: "Dimensión", significado: "Indicador de relevancia sistémica por activos o base de socios (>50% o supervisión CMF integral).", contable: "No aplica", interpretacion: "Sujeta a estándares de solvencia, Basilea y provisiones equivalentes a la banca." }
    ]
  }
];

class DataDictionaryController {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.currentSector = "todos";
    this.searchQuery = "";
  }

  init() {
    if (!this.container) return;
    this.render();
  }

  setFilter(sector) {
    this.currentSector = sector;
    this.render();
  }

  setSearch(query) {
    this.searchQuery = query.toLowerCase().trim();
    this.render();
  }

  getAccountingBadgeClass(criterion) {
    const c = criterion.toLowerCase();
    if (c.includes("razonable") || c.includes("mtm")) return "badge-acct-mtm";
    if (c.includes("neto")) return "badge-acct-neto";
    if (c.includes("bruto")) return "badge-acct-bruto";
    if (c.includes("amortizado") || c.includes("devengado")) return "badge-acct-amort";
    if (c.includes("tasacion") || c.includes("avaluo")) return "badge-acct-tasacion";
    if (c.includes("pacto")) return "badge-acct-pacto";
    return "badge-acct-na";
  }

  render() {
    if (!this.container) return;

    let filtered = DATA_DICTIONARY;
    if (this.currentSector !== "todos") {
      filtered = filtered.filter(d => d.sector === this.currentSector);
    }

    if (this.searchQuery) {
      filtered = filtered.filter(d => {
        const matchTable = d.name.toLowerCase().includes(this.searchQuery) ||
                           d.descripcion.toLowerCase().includes(this.searchQuery) ||
                           d.norma.toLowerCase().includes(this.searchQuery);
        const matchCol = d.columnas.some(c => 
          c.name.toLowerCase().includes(this.searchQuery) ||
          c.significado.toLowerCase().includes(this.searchQuery) ||
          c.contable.toLowerCase().includes(this.searchQuery)
        );
        return matchTable || matchCol;
      });
    }

    const html = `
      <div class="dict-view-container">
        <!-- Barra superior del diccionario -->
        <div class="dict-toolbar">
          <div class="dict-search-wrapper">
            <input type="text" id="dict-search-input" class="dict-search-input" placeholder="Buscar columna, significado o criterio contable (ej: MtM, Neto, Bruto, TIR)..." value="${this.searchQuery}">
          </div>
          <div class="dict-sector-filters">
            <button class="dict-filter-btn ${this.currentSector === 'todos' ? 'active' : ''}" data-sec="todos">Todos</button>
            <button class="dict-filter-btn ${this.currentSector === 'seguros' ? 'active' : ''}" data-sec="seguros">Seguros</button>
            <button class="dict-filter-btn ${this.currentSector === 'ffmm' ? 'active' : ''}" data-sec="ffmm">FFMM</button>
            <button class="dict-filter-btn ${this.currentSector === 'fi' ? 'active' : ''}" data-sec="fi">FFII</button>
            <button class="dict-filter-btn ${this.currentSector === 'pensiones' ? 'active' : ''}" data-sec="pensiones">Pensiones</button>
            <button class="dict-filter-btn ${this.currentSector === 'bancos' ? 'active' : ''}" data-sec="bancos">Bancos</button>
            <button class="dict-filter-btn ${this.currentSector === 'macro' ? 'active' : ''}" data-sec="macro">Macro & Tasas</button>
            <button class="dict-filter-btn ${this.currentSector === 'factoring_leasing' ? 'active' : ''}" data-sec="factoring_leasing">Factoring & Leasing</button>
            <button class="dict-filter-btn ${this.currentSector === 'corredoras_bolsa' ? 'active' : ''}" data-sec="corredoras_bolsa">Corredoras</button>
            <button class="dict-filter-btn ${this.currentSector === 'securitizadoras' ? 'active' : ''}" data-sec="securitizadoras">Securitizadoras</button>
            <button class="dict-filter-btn ${this.currentSector === 'patrimonios_separados' ? 'active' : ''}" data-sec="patrimonios_separados">Patrimonios Separados</button>
            <button class="dict-filter-btn ${this.currentSector === 'cooperativas' ? 'active' : ''}" data-sec="cooperativas">Cooperativas</button>
            <button class="dict-filter-btn ${this.currentSector === 'cajas_compensacion' ? 'active' : ''}" data-sec="cajas_compensacion">Cajas de Compensación</button>
            <button class="dict-filter-btn ${this.currentSector === 'agf' ? 'active' : ''}" data-sec="agf">AGF</button>
            <button class="dict-filter-btn ${this.currentSector === 'sistemas_pago' ? 'active' : ''}" data-sec="sistemas_pago">Sistemas de Pago</button>
            <button class="dict-filter-btn ${this.currentSector === 'fintech' ? 'active' : ''}" data-sec="fintech">FinTech</button>
          </div>
        </div>

        <!-- Lista de Tablas y sus Columnas -->
        <div class="dict-tables-grid">
          ${filtered.map(table => `
            <div class="dict-table-card">
              <div class="dict-card-header">
                <div class="dict-card-title-group">
                  <span class="dict-table-name">${table.name}</span>
                  <span class="dict-view-badge">Vista: <code>${table.viewName}</code></span>
                  <span class="dict-norma-badge">${table.norma}</span>
                  <span class="dict-mode-badge ${table.modo === 'Manual' ? 'mode-manual' : 'mode-auto'}">${table.modo || 'Automático'}</span>
                </div>
                <div class="dict-card-meta">
                  <span class="dict-freshness-tag">
                    <span class="freshness-dot"></span>
                    ${table.frescura}
                  </span>
                  <span class="dict-update-badge" title="Fecha de última actualización">Actualizado: ${table.ultimaActualizacion || '2026-09-23'}</span>
                  <span class="dict-rows-badge">${table.registros}</span>
                </div>
              </div>
              <p class="dict-table-desc">${table.descripcion}</p>
              ${table.advertencia ? `
                <div class="dict-warning-box">
                  <span class="dict-warning-badge">Sin auditar</span>
                  <span class="dict-warning-text">${table.advertencia}</span>
                </div>
              ` : ''}
              ${table.origen ? `
                <div class="dict-table-source">
                  <span class="source-badge">Origen de Datos</span>
                  <span class="source-text">${table.origen}</span>
                </div>
              ` : ''}

              <!-- Tabla de columnas -->
              <div class="dict-cols-wrapper">
                <table class="dict-cols-table">
                  <thead>
                    <tr>
                      <th style="width: 20%;">Columna</th>
                      <th style="width: 12%;">Tipo & Rol</th>
                      <th style="width: 44%;">Significado / Definición Funcional</th>
                      <th style="width: 24%;">Criterio Contable</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${table.columnas.map(col => `
                      <tr>
                        <td class="dict-col-name">
                          <code>${col.name}</code>
                        </td>
                        <td>
                          <span class="dict-type-tag">${col.type}</span>
                          ${col.role === 'PK' ? '<span class="dict-role-tag pk">PK</span>' : ''}
                          ${col.role === 'FK' ? '<span class="dict-role-tag fk">FK</span>' : ''}
                        </td>
                        <td class="dict-col-meaning">
                          <div>${col.significado}</div>
                          ${col.interpretacion ? `
                            <div class="dict-col-interpretacion" style="margin-top: 6px; padding: 6px 9px; background: rgba(56, 189, 248, 0.07); border-left: 3px solid #38bdf8; border-radius: 2px; font-size: 11px; line-height: 1.42; color: #bae6fd;">
                              <strong style="color: #38bdf8; display: block; margin-bottom: 2px; text-transform: uppercase; font-size: 9.5px; letter-spacing: 0.5px;">Interpretación Económica / Financiera:</strong>
                              ${col.interpretacion}
                            </div>
                          ` : ''}
                        </td>
                        <td>
                          <span class="acct-badge ${this.getAccountingBadgeClass(col.contable)}">
                            ${col.contable}
                          </span>
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          `).join('')}
          ${filtered.length === 0 ? '<div class="dict-empty">No se encontraron tablas o columnas que coincidan con la búsqueda.</div>' : ''}
        </div>
      </div>
    `;

    this.container.innerHTML = html;

    // Listeners
    const searchInput = document.getElementById("dict-search-input");
    if (searchInput) {
      searchInput.focus();
      searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);
      searchInput.addEventListener("input", (e) => {
        this.setSearch(e.target.value);
      });
    }

    this.container.querySelectorAll(".dict-filter-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        this.setFilter(e.target.dataset.sec);
      });
    });
  }
}

window.DataDictionary = new DataDictionaryController("dict-container");

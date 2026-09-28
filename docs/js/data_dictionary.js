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
    id: "macro_series",
    name: "macro.series",
    viewName: "macro_series",
    sector: "macro",
    sectorLabel: "Macroeconomía (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "Desde 2014",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Observaciones de las 51 series del catálogo, una fila por serie y fecha, en su frecuencia original (diaria, mensual o trimestral). El nombre, la unidad y el grupo de cada serie están en macro.series_catalogo (unir por clave).",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "Fecha", significado: "Fecha de la observación (AAAA-MM-DD). En series mensuales y trimestrales es el primer día del período.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para promediar series diarias por mes.", contable: "No aplica" },
      { name: "clave", type: "VARCHAR", role: "FK", significado: "Clave corta de la serie (por ejemplo usd_clp, oro, desocupacion); ver macro.series_catalogo.", contable: "No aplica" },
      { name: "serie_id", type: "VARCHAR", role: "Atributo", significado: "Código oficial de la serie en la Base de Datos Estadísticos del BCCh.", contable: "No aplica" },
      { name: "valor", type: "DOUBLE", role: "Métrica", significado: "Valor publicado por el BCCh, en la unidad indicada en el catálogo.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_series_catalogo",
    name: "macro.series_catalogo",
    viewName: "macro_series_catalogo",
    sector: "macro",
    sectorLabel: "Macroeconomía (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "Desde 2014",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-28",
    registros: "Ver data_manifest.json",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Una fila por serie publicada: código SIETE, nombre, grupo, frecuencia, unidad, título oficial del BCCh, cobertura y estado de la última consulta.",
    columnas: [
      { name: "clave", type: "VARCHAR", role: "PK", significado: "Clave corta de la serie.", contable: "No aplica" },
      { name: "serie_id", type: "VARCHAR", role: "Atributo", significado: "Código oficial SIETE.", contable: "No aplica" },
      { name: "nombre", type: "VARCHAR", role: "Atributo", significado: "Nombre descriptivo.", contable: "No aplica" },
      { name: "grupo", type: "VARCHAR", role: "Atributo", significado: "Tasas, Tipo de cambio, Precios y reajustes, Actividad, Mercado laboral, Commodities, Sector externo, Fiscal o Expectativas.", contable: "No aplica" },
      { name: "unidad", type: "VARCHAR", role: "Atributo", significado: "Unidad de medida del valor.", contable: "No aplica" },
      { name: "frecuencia", type: "VARCHAR", role: "Atributo", significado: "Diaria, Mensual o Trimestral.", contable: "No aplica" },
      { name: "titulo_bcch", type: "VARCHAR", role: "Atributo", significado: "Título oficial entregado por la API del BCCh.", contable: "No aplica" },
      { name: "primera_fecha", type: "VARCHAR", role: "Fecha", significado: "Primera observación publicada.", contable: "No aplica" },
      { name: "ultima_fecha", type: "VARCHAR", role: "Fecha", significado: "Última observación publicada.", contable: "No aplica" },
      { name: "observaciones", type: "BIGINT", role: "Métrica", significado: "Número de observaciones publicadas.", contable: "No aplica" },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "ok, sin datos en el BCCh o el error de la última consulta.", contable: "No aplica" },
      { name: "ultima_consulta_utc", type: "VARCHAR", role: "Fecha", significado: "Momento de la última consulta a la API (UTC).", contable: "No aplica" }
    ]
  },
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
  // FONDOS MUTUOS · Circular 1333 (generado desde ffmm/scripts/actualizar_carteras.py)
  {"id": "ffmm_maestro", "name": "ffmm.lista_entidades", "viewName": "ffmm_maestro", "sector": "ffmm", "sectorLabel": "Fondos Mutuos", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Fondos mutuos que reportan cartera a la CMF: RUN, nombre vigente, primer y último mes informado y si reportó el último mes publicado (un fondo nuevo aparece aquí el mes en que informa por primera vez).", "corte": "Desde 2001-01", "registros": "Una fila por fondo", "columnas": [{"name": "run_fondo", "type": "VARCHAR", "role": "PK", "significado": "RUN del fondo mutuo.", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en su último mes informado.", "contable": "No aplica"}, {"name": "primer_periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Primer mes en que el fondo informa cartera.", "contable": "No aplica"}, {"name": "ultimo_periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Último mes en que informa cartera.", "contable": "No aplica"}, {"name": "meses_reportados", "type": "BIGINT", "role": "Métrica", "significado": "Meses publicados en que aparece.", "contable": "No aplica"}, {"name": "reporta_ultimo_mes", "type": "BOOLEAN", "role": "Atributo", "significado": "Verdadero si aparece en el último mes publicado.", "contable": "No aplica"}]},
  {"id": "agf_balance", "name": "agf.balance", "viewName": "agf_balance", "sector": "agf", "sectorLabel": "Administradoras Generales de Fondos", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de situación financiera de cada administradora general de fondos, cuenta por cuenta, al cierre de cada trimestre.", "corte": "2010-06–2026-06", "registros": "71.423 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la CMF la repite (por ejemplo, Ganancia (pérdida) al final del estado y en su atribución).", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}]},
  {"id": "agf_resultados", "name": "agf.resultados", "viewName": "agf_resultados", "sector": "agf", "sectorLabel": "Administradoras Generales de Fondos", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de resultados y resultado integral de cada administradora general de fondos, acumulado del ejercicio a cada trimestre.", "corte": "2010-06–2026-06", "registros": "58.216 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la CMF la repite (por ejemplo, Ganancia (pérdida) al final del estado y en su atribución).", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}]},
  {"id": "securitizadoras_balance", "name": "securitizadoras.balance", "viewName": "securitizadoras_balance", "sector": "securitizadoras", "sectorLabel": "Securitizadoras", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de situación financiera de cada sociedad securitizadora, cuenta por cuenta, al cierre de cada trimestre.", "corte": "2009-12–2026-06", "registros": "13.679 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la CMF la repite (por ejemplo, Ganancia (pérdida) al final del estado y en su atribución).", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}]},
  {"id": "securitizadoras_resultados", "name": "securitizadoras.resultados", "viewName": "securitizadoras_resultados", "sector": "securitizadoras", "sectorLabel": "Securitizadoras", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de resultados y resultado integral de cada sociedad securitizadora, acumulado del ejercicio a cada trimestre.", "corte": "2009-12–2026-06", "registros": "12.290 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la CMF la repite (por ejemplo, Ganancia (pérdida) al final del estado y en su atribución).", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}]},
  {"id": "ccaf_balance", "name": "ccaf.balance", "viewName": "ccaf_balance", "sector": "cajas_compensacion", "sectorLabel": "Cajas de Compensación", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de situación financiera de cada caja de compensación que envía estados financieros a la CMF, cuenta por cuenta, al cierre de cada trimestre.", "corte": "2010-06–2026-06", "registros": "8.043 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la CMF la repite (por ejemplo, Ganancia (pérdida) al final del estado y en su atribución).", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}]},
  {"id": "ccaf_resultados", "name": "ccaf.resultados", "viewName": "ccaf_resultados", "sector": "cajas_compensacion", "sectorLabel": "Cajas de Compensación", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de resultados y resultado integral de cada caja de compensación que envía estados financieros a la CMF, acumulado del ejercicio a cada trimestre.", "corte": "2010-06–2026-06", "registros": "5.506 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la CMF la repite (por ejemplo, Ganancia (pérdida) al final del estado y en su atribución).", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}]},
  {"id": "corredoras_bolsa_balance", "name": "corredoras.balance", "viewName": "corredoras_bolsa_balance", "sector": "corredoras_bolsa", "sectorLabel": "Corredoras de Bolsa", "norma": "FECU IFRS intermediarios · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estadísticas de estados financieros IFRS de intermediarios de valores (corredores de bolsa y agentes de valores), https://www.cmfchile.cl/institucional/estadisticas/merc_valores/intermediarios_fecu_ifrs/", "descripcion": "Estado de situación financiera de corredores de bolsa y agentes de valores, cuenta FECU por cuenta, al cierre de cada trimestre.", "corte": "2010-12–2026-06", "registros": "107.976 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT sin dígito verificador (une con corredoras.lista_entidades).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del intermediario en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_intermediario", "type": "VARCHAR", "role": "Atributo", "significado": "corredor de bolsa o agente de valores.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Estado de situación financiera, Estado de resultados u Otros resultados integrales.", "contable": "No aplica"}, {"name": "seccion", "type": "VARCHAR", "role": "Atributo", "significado": "Agrupación de la cuenta en el informe (Activos, Pasivos, Resultado por intermediación, etc.).", "contable": "No aplica"}, {"name": "codigo_fecu", "type": "VARCHAR", "role": "PK", "significado": "Código de la cuenta en el plan FECU IFRS de intermediarios (10.00.00 total activos, 21.00.00 total pasivos, 22.00.00 patrimonio, 30.00.00 resultado del ejercicio).", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta.", "contable": "No aplica"}, {"name": "nivel", "type": "TINYINT", "role": "Atributo", "significado": "Nivel jerárquico de la cuenta en el informe (1 = cuenta principal).", "contable": "No aplica"}, {"name": "valor_miles_clp", "type": "BIGINT", "role": "Métrica", "significado": "Monto en miles de pesos, moneda corriente del cierre. Resultados acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector.", "contable": "No aplica"}]},
  {"id": "corredoras_bolsa_resultados", "name": "corredoras.resultados", "viewName": "corredoras_bolsa_resultados", "sector": "corredoras_bolsa", "sectorLabel": "Corredoras de Bolsa", "norma": "FECU IFRS intermediarios · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estadísticas de estados financieros IFRS de intermediarios de valores (corredores de bolsa y agentes de valores), https://www.cmfchile.cl/institucional/estadisticas/merc_valores/intermediarios_fecu_ifrs/", "descripcion": "Estado de resultados y otros resultados integrales de corredores de bolsa y agentes de valores, acumulados del ejercicio.", "corte": "2010-12–2026-06", "registros": "77.705 cuentas", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT sin dígito verificador (une con corredoras.lista_entidades).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del intermediario en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_intermediario", "type": "VARCHAR", "role": "Atributo", "significado": "corredor de bolsa o agente de valores.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Estado de situación financiera, Estado de resultados u Otros resultados integrales.", "contable": "No aplica"}, {"name": "seccion", "type": "VARCHAR", "role": "Atributo", "significado": "Agrupación de la cuenta en el informe (Activos, Pasivos, Resultado por intermediación, etc.).", "contable": "No aplica"}, {"name": "codigo_fecu", "type": "VARCHAR", "role": "PK", "significado": "Código de la cuenta en el plan FECU IFRS de intermediarios (10.00.00 total activos, 21.00.00 total pasivos, 22.00.00 patrimonio, 30.00.00 resultado del ejercicio).", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta.", "contable": "No aplica"}, {"name": "nivel", "type": "TINYINT", "role": "Atributo", "significado": "Nivel jerárquico de la cuenta en el informe (1 = cuenta principal).", "contable": "No aplica"}, {"name": "valor_miles_clp", "type": "BIGINT", "role": "Métrica", "significado": "Monto en miles de pesos, moneda corriente del cierre. Resultados acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector.", "contable": "No aplica"}]},
  {"id": "fi_maestro", "name": "fi.lista_entidades", "viewName": "fi_maestro", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Registro CMF de fondos de inversión (rescatables y no rescatables, vigentes y no vigentes) con administradora, moneda funcional y primer y último trimestre con cartera publicada.", "registros": "Una fila por fondo", "columnas": [{"name": "run_fondo", "type": "VARCHAR", "role": "PK", "significado": "RUN del fondo (sin dígito verificador).", "contable": "No aplica"}, {"name": "rut_fondo_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUN con dígito verificador.", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el registro CMF.", "contable": "No aplica"}, {"name": "administradora", "type": "VARCHAR", "role": "Atributo", "significado": "Administradora general de fondos (une por nombre con agf.lista_administradoras).", "contable": "No aplica"}, {"name": "tipo_entidad", "type": "VARCHAR", "role": "Atributo", "significado": "FIRES fondo de inversión rescatable; FINRE no rescatable.", "contable": "No aplica"}, {"name": "estado_vigencia", "type": "VARCHAR", "role": "Atributo", "significado": "Vigente / No Vigente según el registro CMF.", "contable": "No aplica"}, {"name": "moneda_funcional", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda funcional del fondo (en la que se expresan sus montos _miles_mf), leída del informe de pactos.", "contable": "No aplica"}, {"name": "primer_periodo_cartera", "type": "VARCHAR", "role": "Fecha", "significado": "Primer trimestre con cartera publicada (desde 2020-03).", "contable": "No aplica"}, {"name": "ultimo_periodo_cartera", "type": "VARCHAR", "role": "Fecha", "significado": "Último trimestre con cartera publicada.", "contable": "No aplica"}, {"name": "trimestres_con_cartera", "type": "BIGINT", "role": "Métrica", "significado": "Trimestres con cartera publicada.", "contable": "No aplica"}, {"name": "reporta_ultimo_periodo", "type": "BOOLEAN", "role": "Atributo", "significado": "Verdadero si el fondo tiene cartera en el último trimestre publicado.", "contable": "No aplica"}]},
  {"id": "fi_cartera_nacional", "name": "fi.cartera_nacional", "viewName": "fi_cartera_nacional", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Inversiones en instrumentos de emisores nacionales, instrumento por instrumento, al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Un archivo por trimestre", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "rut_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "RUT del emisor con dígito verificador.", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "codigo_grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Código del grupo empresarial del emisor (0000 si no pertenece a uno).", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_valor_par_precio", "type": "DOUBLE", "role": "Métrica", "significado": "TIR, % del valor par o precio usado para valorizar, según el código de valorización.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_cartera_extranjera", "name": "fi.cartera_extranjera", "viewName": "fi_cartera_extranjera", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Inversiones en instrumentos de emisores extranjeros al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "isin", "type": "VARCHAR", "role": "Atributo", "significado": "Código ISIN o CUSIP del instrumento.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor.", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del grupo empresarial del emisor.", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_valor_par_precio", "type": "DOUBLE", "role": "Métrica", "significado": "TIR, % del valor par o precio usado para valorizar, según el código de valorización.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_metodo_participacion", "name": "fi.metodo_participacion", "viewName": "fi_metodo_participacion", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Inversiones valorizadas por el método de la participación (sociedades filiales y coligadas). Montos en miles de la moneda funcional del fondo.", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "isin", "type": "VARCHAR", "role": "Atributo", "significado": "Código ISIN o CUSIP del instrumento.", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor.", "contable": "No aplica"}, {"name": "rut_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "RUT del emisor con dígito verificador.", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "patrimonio_emisor_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Patrimonio de la sociedad participada, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "valor_cierre_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor contable al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "provision_deterioro_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Provisión por deterioro, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "plusvalia_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Plusvalía de la inversión, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_bienes_raices", "name": "fi.bienes_raices", "viewName": "fi_bienes_raices", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Bienes raíces nacionales y extranjeros de los fondos. Montos en miles de la moneda funcional del fondo.", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "domicilio", "type": "VARCHAR", "role": "Atributo", "significado": "Dirección del inmueble.", "contable": "No aplica"}, {"name": "comuna", "type": "VARCHAR", "role": "Atributo", "significado": "Comuna del inmueble.", "contable": "No aplica"}, {"name": "ciudad", "type": "VARCHAR", "role": "Atributo", "significado": "Ciudad del inmueble.", "contable": "No aplica"}, {"name": "region", "type": "VARCHAR", "role": "Atributo", "significado": "Región del inmueble.", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país.", "contable": "No aplica"}, {"name": "tipo_bien_raiz", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de bien raíz según la CMF.", "contable": "No aplica"}, {"name": "pct_comunidad", "type": "DOUBLE", "role": "Métrica", "significado": "Porcentaje de propiedad cuando el inmueble está en comunidad.", "contable": "No aplica"}, {"name": "destino", "type": "VARCHAR", "role": "Atributo", "significado": "Destino o uso del inmueble.", "contable": "No aplica"}, {"name": "tipo_renta", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de renta que genera.", "contable": "No aplica"}, {"name": "prohibiciones_garantias", "type": "VARCHAR", "role": "Atributo", "significado": "Prohibiciones o garantías que pesan sobre el inmueble.", "contable": "No aplica"}, {"name": "valor_cierre_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor contable al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "ajustes_prohibiciones_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Ajustes y prohibiciones, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_futuros", "name": "fi.futuros_forwards", "viewName": "fi_futuros", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Contratos de futuro, forward y swap vigentes al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "unidad_cotizacion", "type": "VARCHAR", "role": "Atributo", "significado": "Unidad de cotización del contrato.", "contable": "No aplica"}, {"name": "fecha_inicio", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de inicio del contrato (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la contraparte.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país.", "contable": "No aplica"}, {"name": "posicion", "type": "VARCHAR", "role": "Atributo", "significado": "Posición: compra o venta.", "contable": "No aplica"}, {"name": "unidades_nominales", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales totales del contrato.", "contable": "No aplica"}, {"name": "precio_futuro", "type": "DOUBLE", "role": "Métrica", "significado": "Precio futuro pactado.", "contable": "No aplica"}, {"name": "monto_comprometido_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Monto comprometido, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "valor_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado del contrato, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}]},
  {"id": "fi_opciones", "name": "fi.opciones", "viewName": "fi_opciones", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Contratos de opciones vigentes al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "forma_ejercicio", "type": "VARCHAR", "role": "Atributo", "significado": "Forma de ejercicio: americana o europea.", "contable": "No aplica"}, {"name": "fecha_inicio", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de inicio del contrato (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la contraparte.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país.", "contable": "No aplica"}, {"name": "tipo_opcion", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de opción: compra (call) o venta (put).", "contable": "No aplica"}, {"name": "valor_mercado_unitario_prima", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado unitario de la prima.", "contable": "No aplica"}, {"name": "numero_contratos", "type": "DOUBLE", "role": "Métrica", "significado": "Número de contratos.", "contable": "No aplica"}, {"name": "precio_ejercicio", "type": "DOUBLE", "role": "Métrica", "significado": "Precio de ejercicio.", "contable": "No aplica"}, {"name": "valor_mercado_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado del activo objeto.", "contable": "No aplica"}, {"name": "unidades_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades del activo objeto.", "contable": "No aplica"}, {"name": "inversion_primas_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "valorizacion_precio_ejercicio_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización a precio de ejercicio, en miles de la moneda funcional.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización de mercado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "pct_primas_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_pactos", "name": "fi.pactos", "viewName": "fi_pactos", "sector": "fi", "sectorLabel": "Fondos de Inversión", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Operaciones de venta con compromiso de retrocompra (VRC) y de compra con compromiso de retroventa (CRV) vigentes al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "tipo_operacion", "type": "VARCHAR", "role": "Atributo", "significado": "VRC venta con compromiso de retrocompra; CRV compra con compromiso de retroventa.", "contable": "No aplica"}, {"name": "fecha_inicio", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de inicio del contrato (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "fecha_termino", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de término del pacto (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la contraparte.", "contable": "No aplica"}, {"name": "rut_contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "RUT de la contraparte con dígito verificador.", "contable": "No aplica"}, {"name": "valor_inicial_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor inicial del pacto, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_origen", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de origen del pacto.", "contable": "No aplica"}, {"name": "tasa_pacto_pct", "type": "DOUBLE", "role": "Métrica", "significado": "Tasa del pacto (%).", "contable": "No aplica"}, {"name": "valor_final_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor final del pacto, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_cierre_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización del pacto al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "isin", "type": "VARCHAR", "role": "Atributo", "significado": "Código ISIN o CUSIP del instrumento.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "valor_mercado_miles_moneda", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado del instrumento en compromiso, en miles de la moneda del informe.", "contable": "No aplica"}]},
  {"id": "ffmm_cartera_nacional", "name": "ffmm.cartera_nacional", "viewName": "ffmm_cartera_nacional", "sector": "ffmm", "sectorLabel": "Fondos Mutuos", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Inversiones de cada fondo en instrumentos de emisores nacionales, instrumento por instrumento, al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2022-01", "registros": "Un archivo por mes", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "rut_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "RUT del emisor con dígito verificador.", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "codigo_grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Código del grupo empresarial del emisor (0000 si no pertenece a uno).", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_pct", "type": "DOUBLE", "role": "Métrica", "significado": "TIR de valorización (%), cuando el código de valorización es 1.", "contable": "No aplica"}, {"name": "valor_par_pct", "type": "DOUBLE", "role": "Métrica", "significado": "Porcentaje del valor par, cuando el código de valorización es 2.", "contable": "No aplica"}, {"name": "valor_relevante", "type": "DOUBLE", "role": "Métrica", "significado": "Valor relevante (precio) usado, cuando el código de valorización es 3.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo, sin decimales.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "ffmm_cartera_extranjera", "name": "ffmm.cartera_extranjera", "viewName": "ffmm_cartera_extranjera", "sector": "ffmm", "sectorLabel": "Fondos Mutuos", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Inversiones de cada fondo en instrumentos de emisores extranjeros al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2001-01", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor en la bolsa extranjera.", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Grupo empresarial del emisor (NA si no aplica).", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_pct", "type": "DOUBLE", "role": "Métrica", "significado": "TIR de valorización (%), cuando el código de valorización es 1.", "contable": "No aplica"}, {"name": "valor_par_pct", "type": "DOUBLE", "role": "Métrica", "significado": "Porcentaje del valor par, cuando el código de valorización es 2.", "contable": "No aplica"}, {"name": "valor_relevante", "type": "DOUBLE", "role": "Métrica", "significado": "Valor relevante (precio) usado, cuando el código de valorización es 3.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo, sin decimales.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "ffmm_futuros", "name": "ffmm.futuros_forwards", "viewName": "ffmm_futuros", "sector": "ffmm", "sectorLabel": "Fondos Mutuos", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Contratos de futuro y forward vigentes de cada fondo al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2001-01", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "unidad_cotizacion", "type": "VARCHAR", "role": "Atributo", "significado": "Unidad o moneda de cotización del contrato.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (vacío si no aplica).", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se suscribió el contrato.", "contable": "No aplica"}, {"name": "posicion", "type": "VARCHAR", "role": "Atributo", "significado": "C posición compradora; V posición vendedora.", "contable": "No aplica"}, {"name": "unidades_nominales", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales totales comprometidas.", "contable": "No aplica"}, {"name": "precio_futuro", "type": "DOUBLE", "role": "Métrica", "significado": "Precio a futuro acordado, en la moneda de cotización.", "contable": "No aplica"}, {"name": "monto_comprometido_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor total de los contratos al precio acordado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}]},
  {"id": "ffmm_opciones", "name": "ffmm.opciones", "viewName": "ffmm_opciones", "sector": "ffmm", "sectorLabel": "Fondos Mutuos", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Contratos de opciones vigentes de cada fondo al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2001-01", "registros": "Un archivo por año", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "forma_ejercicio", "type": "VARCHAR", "role": "Atributo", "significado": "A americana; E europea.", "contable": "No aplica"}, {"name": "fecha_expiracion", "type": "VARCHAR", "role": "Fecha", "significado": "Último día en que la opción puede ejercerse.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se suscribió el contrato.", "contable": "No aplica"}, {"name": "tipo_opcion", "type": "VARCHAR", "role": "Atributo", "significado": "C derecho a comprar; V derecho a vender.", "contable": "No aplica"}, {"name": "valor_mercado_unitario_prima", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado unitario de la prima.", "contable": "No aplica"}, {"name": "numero_contratos", "type": "DOUBLE", "role": "Métrica", "significado": "Número de contratos de la misma serie.", "contable": "No aplica"}, {"name": "precio_ejercicio", "type": "DOUBLE", "role": "Métrica", "significado": "Precio de ejercicio.", "contable": "No aplica"}, {"name": "valor_mercado_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Precio de mercado del activo objeto.", "contable": "No aplica"}, {"name": "unidades_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades del activo objeto que se pueden comprar o vender.", "contable": "No aplica"}, {"name": "inversion_primas_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_precio_ejercicio_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades del activo objeto valorizadas a precio de ejercicio, en miles de la moneda funcional.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "pct_primas_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas como % del activo total del fondo.", "contable": "No aplica"}]},
  // BEGIN AUTO FL IFRS SERIES DICTIONARY
  {"sector":"factoring_leasing","sectorLabel":"Factoring & Leasing","norma":"CMF IFRS TXT · extracción automática de cuentas ESF/ER","corte":"2009-03 a 2026-06 · 70 cierres","frescura":"Serie de la fuente CMF; valores crudos, no validación integral","modo":"Actions: descarga histórica incremental y publicación automática al completarse","ultimaActualizacion":"2026-09-27","origen":"CMF https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php; corrida Actions 36340943560. 24/28 RUT de catálogo presentes. Incluye cuentas repetidas y valores no enteros; no convertir, deduplicar ni sumar sin criterio. No cotejo integral de estados.","columnas":[{"name":"periodo","type":"VARCHAR","role":"Dimensión","significado":"Cierre informado por CMF, AAAA-MM.","contable":"No aplica"},{"name":"rut_cuerpo","type":"VARCHAR","role":"Dimensión","significado":"Identificador de 8 dígitos (sin DV) literal del TXT; rut actual proviene del catálogo.","contable":"No aplica"},{"name":"rut","type":"VARCHAR","role":"Dimensión","significado":"Unión al RUT actual del catálogo por cuerpo; no certifica vigencia ni identidad histórica.","contable":"No aplica"},{"name":"nombre_reportado","type":"VARCHAR","role":"Dimensión","significado":"Nombre reportado por CMF en ese período.","contable":"No aplica"},{"name":"segmento_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Segmento consignado en el catálogo actual; puede incluir entidades mixtas/automotrices.","contable":"No aplica"},{"name":"nombre_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Nombre del catálogo actual; puede diferir del nombre histórico.","contable":"No aplica"},{"name":"tipo_balance","type":"VARCHAR","role":"Dimensión","significado":"I individual / C consolidado. Se preservan separados; no sumar.","contable":"No aplica"},{"name":"moneda_archivo","type":"VARCHAR","role":"Dimensión","significado":"Moneda original, sin conversión.","contable":"No aplica"},{"name":"cuenta","type":"VARCHAR","role":"Dimensión","significado":"Etiqueta literal de cuenta reportada.","contable":"No aplica"},{"name":"valor_archivo","type":"BIGINT","role":"Métrica","significado":"Entero original cuando pudo leerse como entero; NULL para valores no enteros.","contable":"No aplica"},{"name":"valor_texto_original","type":"VARCHAR","role":"Métrica","significado":"Texto literal de la cifra, preservado siempre.","contable":"No aplica"},{"name":"valor_es_entero","type":"BOOLEAN","role":"Dimensión","significado":"Control de interpretación numérica; false no significa cero.","contable":"No aplica"},{"name":"taxonomia","type":"VARCHAR","role":"Dimensión","significado":"Código literal de taxonomía CMF.","contable":"No aplica"},{"name":"estado_financiero","type":"VARCHAR","role":"Dimensión","significado":"Código CMF del estado: ESF C/NC = situación financiera; ERFG = resultados por función; ERNG = resultados por naturaleza; ERI = resultado integral.","contable":"No aplica"},{"name":"repeticion_contexto","type":"BIGINT","role":"Dimensión","significado":"Ordinal de la misma etiqueta dentro del estado; se conserva sin sumar. En resultados, \"Ganancia (pérdida)\" aparece en ERFG/ERNG con ordinal 1 y 2 y otra vez al inicio de ERI, con el mismo valor: para la utilidad del período usar estado ERFG/ERNG y ordinal 1.","contable":"No aplica"},{"name":"fuente_archivo","type":"VARCHAR","role":"Dimensión","significado":"URL pública CMF que originó la fila.","contable":"No aplica"},{"name":"sha256_archivo","type":"VARCHAR","role":"Dimensión","significado":"Huella de la descarga usada.","contable":"No aplica"},{"name":"identidad_nombre_coincide_catalogo","type":"BOOLEAN","role":"Dimensión","significado":"Coincidencia de nombre normalizada; señal, no auditoría histórica.","contable":"No aplica"}],"id":"factoring_leasing_balance_serie_ifrs_cmf","name":"factoring_leasing.balance_serie_ifrs_cmf","viewName":"factoring_leasing_balance_serie_ifrs_cmf","registros":"28,938 cuentas · 24/28 RUT con datos","descripcion":"Balance IFRS CMF · serie histórica. 28,938 filas de cuentas de estados ESF entre 2009-03 a 2026-06; no son estados agregados. Incluye 2,426 importes no enteros preservados como texto/null y 902 repeticiones de contexto conservadas. Monedas, taxonomías y tipos I/C permanecen separados; sin conversión, deduplicación ni suma. Cifras no cotejadas en su totalidad."},
  {"sector":"factoring_leasing","sectorLabel":"Factoring & Leasing","norma":"CMF IFRS TXT · extracción automática de cuentas ESF/ER","corte":"2009-03 a 2026-06 · 70 cierres","frescura":"Serie de la fuente CMF; valores crudos, no validación integral","modo":"Actions: descarga histórica incremental y publicación automática al completarse","ultimaActualizacion":"2026-09-27","origen":"CMF https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php; corrida Actions 36340943560. 24/28 RUT de catálogo presentes. Incluye cuentas repetidas y valores no enteros; no convertir, deduplicar ni sumar sin criterio. No cotejo integral de estados.","columnas":[{"name":"periodo","type":"VARCHAR","role":"Dimensión","significado":"Cierre informado por CMF, AAAA-MM.","contable":"No aplica"},{"name":"rut_cuerpo","type":"VARCHAR","role":"Dimensión","significado":"Identificador de 8 dígitos (sin DV) literal del TXT; rut actual proviene del catálogo.","contable":"No aplica"},{"name":"rut","type":"VARCHAR","role":"Dimensión","significado":"Unión al RUT actual del catálogo por cuerpo; no certifica vigencia ni identidad histórica.","contable":"No aplica"},{"name":"nombre_reportado","type":"VARCHAR","role":"Dimensión","significado":"Nombre reportado por CMF en ese período.","contable":"No aplica"},{"name":"segmento_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Segmento consignado en el catálogo actual; puede incluir entidades mixtas/automotrices.","contable":"No aplica"},{"name":"nombre_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Nombre del catálogo actual; puede diferir del nombre histórico.","contable":"No aplica"},{"name":"tipo_balance","type":"VARCHAR","role":"Dimensión","significado":"I individual / C consolidado. Se preservan separados; no sumar.","contable":"No aplica"},{"name":"moneda_archivo","type":"VARCHAR","role":"Dimensión","significado":"Moneda original, sin conversión.","contable":"No aplica"},{"name":"cuenta","type":"VARCHAR","role":"Dimensión","significado":"Etiqueta literal de cuenta reportada.","contable":"No aplica"},{"name":"valor_archivo","type":"BIGINT","role":"Métrica","significado":"Entero original cuando pudo leerse como entero; NULL para valores no enteros.","contable":"No aplica"},{"name":"valor_texto_original","type":"VARCHAR","role":"Métrica","significado":"Texto literal de la cifra, preservado siempre.","contable":"No aplica"},{"name":"valor_es_entero","type":"BOOLEAN","role":"Dimensión","significado":"Control de interpretación numérica; false no significa cero.","contable":"No aplica"},{"name":"taxonomia","type":"VARCHAR","role":"Dimensión","significado":"Código literal de taxonomía CMF.","contable":"No aplica"},{"name":"estado_financiero","type":"VARCHAR","role":"Dimensión","significado":"Código CMF del estado: ESF C/NC = situación financiera; ERFG = resultados por función; ERNG = resultados por naturaleza; ERI = resultado integral.","contable":"No aplica"},{"name":"repeticion_contexto","type":"BIGINT","role":"Dimensión","significado":"Ordinal de la misma etiqueta dentro del estado; se conserva sin sumar. En resultados, \"Ganancia (pérdida)\" aparece en ERFG/ERNG con ordinal 1 y 2 y otra vez al inicio de ERI, con el mismo valor: para la utilidad del período usar estado ERFG/ERNG y ordinal 1.","contable":"No aplica"},{"name":"fuente_archivo","type":"VARCHAR","role":"Dimensión","significado":"URL pública CMF que originó la fila.","contable":"No aplica"},{"name":"sha256_archivo","type":"VARCHAR","role":"Dimensión","significado":"Huella de la descarga usada.","contable":"No aplica"},{"name":"identidad_nombre_coincide_catalogo","type":"BOOLEAN","role":"Dimensión","significado":"Coincidencia de nombre normalizada; señal, no auditoría histórica.","contable":"No aplica"}],"id":"factoring_leasing_resultados_serie_ifrs_cmf","name":"factoring_leasing.resultados_serie_ifrs_cmf","viewName":"factoring_leasing_resultados_serie_ifrs_cmf","registros":"21,464 cuentas · 24/28 RUT con datos","descripcion":"Resultados IFRS CMF · serie histórica. 21,464 filas de cuentas de estados ER entre 2009-03 a 2026-06; no son estados agregados. Incluye 2,426 importes no enteros preservados como texto/null y 902 repeticiones de contexto conservadas. Monedas, taxonomías y tipos I/C permanecen separados; sin conversión, deduplicación ni suma. Cifras no cotejadas en su totalidad."},
  // END AUTO FL IFRS SERIES DICTIONARY
  {
    id: "afp_maestro",
    name: "afp.lista_administradoras",
    viewName: "afp_maestro",
    sector: "pensiones",
    sectorLabel: "Fondos de Pensiones",
    norma: "D.L. 3.500 / SPensiones",
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "7 entidades",
    descripcion: "Administradoras de fondos de pensiones: RUT, razón social y nombre de fantasía. Sin cifras.",
    origen: "Altas: AFP con valor cuota publicado a diario por la Superintendencia de Pensiones (vcfAFP.php), con el RUT del Registro de Valores CMF (RVEMI). pipelines/entidades/actualizar_listas.py.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "ID local de la administradora.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "Atributo", significado: "RUT de la administradora (Registro de Valores CMF para las altas automáticas).", contable: "No aplica" },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social de la administradora.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial (AFP + nombre publicado por la Superintendencia).", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_maestro",
    name: "bancos.lista_instituciones",
    viewName: "bancos_maestro",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Ley General de Bancos / CMF",
    corte: "Códigos históricos y vigentes",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "40 códigos (incluye agregados)",
    descripcion: "Códigos de institución de los archivos bancarios CMF: bancos vigentes, históricos (fusionados o cerrados), filiales en el exterior y agregados del sistema. No equivale al número de bancos activos. RUT de los bancos activos cotejados con el registro CMF.",
    origen: "Registro CMF de bancos (consulta.php?mercado=B&entidad=BANCO): alta de bancos nuevos y paso de «Activo» a «No vigente». Códigos históricos y agregados: lista original. pipelines/entidades/actualizar_listas.py.",
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
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 2, 12 y 22)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "28 entidades",
    descripcion: "Sociedades de factoring, leasing y financiamiento automotriz. Las sociedades nuevas se agregan cuando reportan estados financieros IFRS a la CMF con giro factoring o leasing; sus estados se publican desde entonces.",
    origen: "Lista original (referencias CMF FASOC, LISOC y RVEMI) + altas automáticas desde el TXT IFRS de la CMF (pipelines/ifrs_sectores/actualizar.py).",
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
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Vigencia en el Registro de Corredores de Bolsa de la CMF ('Vigente' / 'No Vigente'); se actualiza sola 3 veces al mes (pipelines/entidades).", contable: "No aplica", interpretacion: "Permite separar a los corredores que operan hoy de los históricos." },
      { name: "tipo_intermediario", type: "VARCHAR", role: "Dimensión", significado: "Tipo de intermediario regulado ('CORREDOR DE BOLSA').", contable: "No aplica", interpretacion: "Distingue a los miembros de bolsas de valores facultados para transar acciones, renta fija y derivados." },
      { name: "grupo_financiero", type: "VARCHAR", role: "Dimensión", significado: "Conglomerado o matriz controladora de la corredora de bolsa.", contable: "No aplica", interpretacion: "Clasifica filiales bancarias (Banco de Chile, Santander, BCI, etc.) versus corredoras independientes (LarrainVial, BTG Pactual, etc.)." }
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
    id: "patrimonios_separados_maestro",
    name: "patrimonios_separados.lista_emisiones",
    viewName: "patrimonios_separados_maestro",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados",
    norma: "CMF Chile — Ley 18.045 Título XVIII (Registro de Títulos de Deuda)",
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "18 emisiones",
    descripcion: "Inscripciones de títulos de deuda de securitización (patrimonios separados) por registro automático: número, fecha, securitizadora, tipo, moneda, monto inscrito y vencimiento. La clase de colateral no está en el listado CMF: queda vacía en las inscripciones agregadas automáticamente.",
    origen: "CMF — Inscripciones de títulos de deuda mediante modalidad de registro automático (listado_titulos_deuda.php), filtrado a securitizadoras. pipelines/entidades/actualizar_listas.py.",
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
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 2, 12 y 22)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "6 entidades",
    descripcion: "Cajas de compensación de asignación familiar, vigentes y absorbidas, con marco legal, regulador y registro CMF. Una caja nueva se agrega cuando reporta estados financieros IFRS a la CMF.",
    origen: "Lista original (SUSESO y Registro de Valores CMF) + altas automáticas desde el TXT IFRS de la CMF (pipelines/ifrs_sectores/actualizar.py).",
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
    registros: "70 entidades",
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
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "12 entidades",
    descripcion: "Infraestructuras del sistema de pagos: LBTR del Banco Central, cámaras de compensación, depósito de valores, contrapartes centrales y operadores de tarjetas de pago.",
    origen: "Registros públicos CMF: altas desde operadores de tarjetas de pago (TPOPE) y entidades de contraparte central (RGCCO); vigencia también desde sociedades de apoyo al giro (BCSAG) y depósito de valores (DCVAL). El LBTR (BCCh) no tiene registro CMF y no se modifica. pipelines/entidades/actualizar_listas.py.",
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
    registros: "263 entidades",
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

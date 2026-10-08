/**
 * Diccionario de Datos & Contabilidad Regulatoria
 * Sistema de Información Financiera de Chile
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
  // <macro:inicio>
  {
    id: "macro_tasas_corto_plazo",
    name: "macro.tasas_corto_plazo",
    viewName: "macro_tasas_corto_plazo",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-30",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.175 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Tasas de referencia de corto plazo de Chile: Tasa de Política Monetaria (TPM) del Banco Central y tasa promedio transada en el mercado interbancario (TIB), en porcentaje.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "tpm_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de Política Monetaria fijada por el Consejo del Banco Central, en porcentaje anual.", contable: "No aplica" },
      { name: "tib_promedio_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa interbancaria promedio (TIB): tasa a la que los bancos se prestan a un día, en porcentaje anual.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_swaps_camara",
    name: "macro.swaps_camara",
    viewName: "macro_swaps_camara",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-29",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.188 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Tasa de swap promedio de cámara (SPC) del Banco Central: contratos en pesos a 90, 180 y 360 días y a 2 años, y contrato en UF a 1 año, en porcentaje.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "swap_camara_pesos_90_dias_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa fija del swap promedio de cámara en pesos a 90 días, en porcentaje anual.", contable: "No aplica" },
      { name: "swap_camara_pesos_180_dias_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa fija del swap promedio de cámara en pesos a 180 días, en porcentaje anual.", contable: "No aplica" },
      { name: "swap_camara_pesos_360_dias_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa fija del swap promedio de cámara en pesos a 360 días, en porcentaje anual.", contable: "No aplica" },
      { name: "swap_camara_pesos_2_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa fija del swap promedio de cámara en pesos a 2 años, en porcentaje anual.", contable: "No aplica" },
      { name: "swap_camara_uf_1_ano_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa fija del swap promedio de cámara en UF a 1 año, en porcentaje anual.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_curva_bonos_pesos",
    name: "macro.curva_bonos_pesos",
    viewName: "macro_curva_bonos_pesos",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-28",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.157 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Curva de rendimiento de los bonos soberanos en pesos licitados por el BCCh (Bono Corto Plazo, BCP): tasa de interés de mercado secundario a 2, 5 y 10 años.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "rendimiento_bono_pesos_2_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono del Banco Central en pesos a 2 años (BCP-2), en porcentaje anual.", contable: "No aplica" },
      { name: "rendimiento_bono_pesos_5_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono del Banco Central en pesos a 5 años (BCP-5), en porcentaje anual.", contable: "No aplica" },
      { name: "rendimiento_bono_pesos_10_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono del Banco Central en pesos a 10 años (BCP-10), en porcentaje anual.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_curva_bonos_uf",
    name: "macro.curva_bonos_uf",
    viewName: "macro_curva_bonos_uf",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-28",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.159 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Curva de rendimiento de los bonos soberanos en UF (BCU/BTU): tasa de interés de mercado secundario a 1, 2, 5, 10, 20 y 30 años.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "rendimiento_bono_uf_1_ano_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono en UF a 1 año (BCU-1), en porcentaje anual sobre UF.", contable: "No aplica" },
      { name: "rendimiento_bono_uf_2_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono en UF a 2 años (BCU-2), en porcentaje anual sobre UF.", contable: "No aplica" },
      { name: "rendimiento_bono_uf_5_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono en UF a 5 años (BCU-5), en porcentaje anual sobre UF.", contable: "No aplica" },
      { name: "rendimiento_bono_uf_10_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono en UF a 10 años (BCU-10), en porcentaje anual sobre UF.", contable: "No aplica" },
      { name: "rendimiento_bono_uf_20_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono en UF a 20 años (BCU-20), en porcentaje anual sobre UF.", contable: "No aplica" },
      { name: "rendimiento_bono_uf_30_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado secundario del bono en UF a 30 años (BCU-30), en porcentaje anual sobre UF.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_inflacion_implicita",
    name: "macro.inflacion_implicita",
    viewName: "macro_inflacion_implicita",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-28",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.063 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Inflación implícita de las curvas soberanas (breakeven): diferencia entre el rendimiento del bono en pesos y el del bono en UF del mismo plazo. Calculada por SIF a partir de las curvas publicadas por el BCCh.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "inflacion_implicita_5_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Rendimiento del bono en pesos a 5 años menos el del bono en UF a 5 años: inflación anual promedio que el mercado espera para ese plazo. Calculada por SIF.", contable: "No aplica" },
      { name: "inflacion_implicita_10_anos_pct", type: "DOUBLE", role: "Métrica", significado: "Rendimiento del bono en pesos a 10 años menos el del bono en UF a 10 años: inflación anual promedio que el mercado espera para ese plazo. Calculada por SIF.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_dolar_observado",
    name: "macro.dolar_observado",
    viewName: "macro_dolar_observado",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-30",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.174 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Dólar observado: tipo de cambio nominal del dólar de los Estados Unidos en pesos chilenos (CLP por USD), según el Banco Central.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "dolar_observado_clp_por_usd", type: "DOUBLE", role: "Métrica", significado: "Pesos chilenos por un dólar de los Estados Unidos (dólar observado publicado por el BCCh para el día).", contable: "No aplica" }
    ]
  },
  {
    id: "macro_euro_observado",
    name: "macro.euro_observado",
    viewName: "macro_euro_observado",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-30",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.174 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Euro observado: tipo de cambio nominal del euro en pesos chilenos (CLP por EUR), según el Banco Central.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "euro_observado_clp_por_eur", type: "DOUBLE", role: "Métrica", significado: "Pesos chilenos por un euro (euro observado publicado por el BCCh para el día).", contable: "No aplica" }
    ]
  },
  {
    id: "macro_tipo_cambio_multilateral",
    name: "macro.tipo_cambio_multilateral",
    viewName: "macro_tipo_cambio_multilateral",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-30",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.174 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Índices de tipo de cambio nominal multilateral del Banco Central: TCM, TCM-5 (monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro) y TCM-X.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "tipo_cambio_nominal_multilateral_indice", type: "DOUBLE", role: "Métrica", significado: "Índice de tipo de cambio nominal multilateral (TCM): valor del peso frente a una canasta de monedas de socios comerciales.", contable: "No aplica" },
      { name: "tipo_cambio_nominal_multilateral_5_monedas_indice", type: "DOUBLE", role: "Métrica", significado: "Índice TCM-5: peso frente a las monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro.", contable: "No aplica" },
      { name: "tipo_cambio_nominal_multilateral_x_indice", type: "DOUBLE", role: "Métrica", significado: "Índice TCM-X: variante del TCM que excluye a Estados Unidos.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_tipo_cambio_real",
    name: "macro.tipo_cambio_real",
    viewName: "macro_tipo_cambio_real",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-08-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "152 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Índices de tipo de cambio real (TCR) del Banco Central, promedio 1986=100: TCR general y TCR-5 (monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro).",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "tipo_cambio_real_general_indice", type: "DOUBLE", role: "Métrica", significado: "Índice de tipo de cambio real general (TCR), promedio 1986=100. Un valor mayor indica un peso más depreciado en términos reales.", contable: "No aplica" },
      { name: "tipo_cambio_real_5_monedas_indice", type: "DOUBLE", role: "Métrica", significado: "Índice de tipo de cambio real TCR-5 (monedas de Estados Unidos, Japón, Reino Unido, Canadá y Zona Euro), promedio 1986=100.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_uf",
    name: "macro.uf",
    viewName: "macro_uf",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-09-30",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "4.656 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Valor diario de la Unidad de Fomento (UF) en pesos chilenos, según el Banco Central.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "uf_valor_clp", type: "DOUBLE", role: "Métrica", significado: "Valor de la Unidad de Fomento del día, en pesos chilenos.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_utm",
    name: "macro.utm",
    viewName: "macro_utm",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-09-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "153 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Valor mensual de la Unidad Tributaria Mensual (UTM) en pesos chilenos, según el Banco Central.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "utm_valor_clp", type: "DOUBLE", role: "Métrica", significado: "Valor de la Unidad Tributaria Mensual del mes, en pesos chilenos.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_inflacion_ipc",
    name: "macro.inflacion_ipc",
    viewName: "macro_inflacion_ipc",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-08-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "152 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Índice de Precios al Consumidor (IPC), serie empalmada del BCCh base 2023=100: índice y variaciones mensual y anual en porcentaje (fuente INE).",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "ipc_indice", type: "DOUBLE", role: "Métrica", significado: "Índice de Precios al Consumidor, serie empalmada base 2023=100.", contable: "No aplica" },
      { name: "ipc_var_mensual_pct", type: "DOUBLE", role: "Métrica", significado: "Variación del IPC respecto al mes anterior, en porcentaje.", contable: "No aplica" },
      { name: "ipc_var_anual_pct", type: "DOUBLE", role: "Métrica", significado: "Variación del IPC respecto al mismo mes del año anterior, en porcentaje (inflación anual).", contable: "No aplica" }
    ]
  },
  {
    id: "macro_imacec",
    name: "macro.imacec",
    viewName: "macro_imacec",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-07-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "151 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Imacec a costo de factores, series empalmadas del BCCh (índice 2018=100): total, no minero, minero, comercio y servicios.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "imacec_empalmado_indice", type: "DOUBLE", role: "Métrica", significado: "Imacec total, serie empalmada, índice 2018=100.", contable: "No aplica" },
      { name: "imacec_no_minero_indice", type: "DOUBLE", role: "Métrica", significado: "Imacec no minero (actividad sin minería), índice 2018=100.", contable: "No aplica" },
      { name: "imacec_minero_indice", type: "DOUBLE", role: "Métrica", significado: "Imacec minero, índice 2018=100.", contable: "No aplica" },
      { name: "imacec_comercio_indice", type: "DOUBLE", role: "Métrica", significado: "Imacec de comercio, índice 2018=100.", contable: "No aplica" },
      { name: "imacec_servicios_indice", type: "DOUBLE", role: "Métrica", significado: "Imacec de servicios, índice 2018=100.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_pib_trimestral",
    name: "macro.pib_trimestral",
    viewName: "macro_pib_trimestral",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-04-01",
    frecuencia: "Trimestral",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "50 trimestres",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Producto Interno Bruto (PIB) en volumen a precios del año anterior encadenado, referencia 2018: miles de millones de pesos encadenados.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del trimestre al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "pib_encadenado_miles_mm_clp", type: "DOUBLE", role: "Métrica", significado: "PIB trimestral en volumen a precios del año anterior encadenado (referencia 2018), en miles de millones de pesos encadenados.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_mercado_laboral",
    name: "macro.mercado_laboral",
    viewName: "macro_mercado_laboral",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-08-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "152 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Mercado laboral de Chile (series no ajustadas del INE, vía BCCh): tasa de desocupación en porcentaje, y personas ocupadas, asalariadas y fuerza de trabajo en miles de personas.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "desocupacion_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de desocupación nacional del trimestre móvil terminado en el mes, en porcentaje de la fuerza de trabajo.", contable: "No aplica" },
      { name: "ocupados_miles_personas", type: "DOUBLE", role: "Métrica", significado: "Personas ocupadas, en miles.", contable: "No aplica" },
      { name: "asalariados_miles_personas", type: "DOUBLE", role: "Métrica", significado: "Personas ocupadas como asalariadas, en miles.", contable: "No aplica" },
      { name: "fuerza_trabajo_miles_personas", type: "DOUBLE", role: "Métrica", significado: "Fuerza de trabajo (ocupados más desocupados), en miles de personas.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_cobre",
    name: "macro.cobre",
    viewName: "macro_cobre",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-09-30",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.246 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Precio del cobre refinado en dólares por libra: cotización diaria de la Bolsa de Metales de Londres (BML) y valor referencial mensual publicado por el BCCh (la referencia mensual aparece en la fila del primer día de su mes).",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "cobre_refinado_usd_por_libra", type: "DOUBLE", role: "Métrica", significado: "Precio del cobre refinado en la Bolsa de Metales de Londres del día, en dólares por libra.", contable: "No aplica" },
      { name: "cobre_referencial_mensual_usd_por_libra", type: "DOUBLE", role: "Métrica", significado: "Precio referencial mensual del cobre publicado por el BCCh, en dólares por libra. Aparece en la fila del primer día de cada mes.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_metales_preciosos",
    name: "macro.metales_preciosos",
    viewName: "macro_metales_preciosos",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-02 a 2026-09-30",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.174 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Precios de los metales preciosos en dólares por onza troy: oro y plata, según el Banco Central.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "oro_usd_por_onza_troy", type: "DOUBLE", role: "Métrica", significado: "Precio del oro del día, en dólares por onza troy.", contable: "No aplica" },
      { name: "plata_usd_por_onza_troy", type: "DOUBLE", role: "Métrica", significado: "Precio de la plata del día, en dólares por onza troy.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_reservas_internacionales",
    name: "macro.reservas_internacionales",
    viewName: "macro_reservas_internacionales",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-08-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "152 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Activos de reserva internacional del Banco Central de Chile, en millones de dólares de los Estados Unidos.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "reservas_internacionales_millones_usd", type: "DOUBLE", role: "Métrica", significado: "Activos de reserva internacional del Banco Central al cierre del mes, en millones de dólares.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_tasa_referencia_fed",
    name: "macro.tasa_referencia_fed",
    viewName: "macro_tasa_referencia_fed",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-09-29",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "3.313 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Tasa de interés de política monetaria de la Reserva Federal de los Estados Unidos (fed funds), en porcentaje.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "tasa_fed_funds_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa efectiva de fondos federales de la Reserva Federal de los Estados Unidos del día, en porcentaje anual.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_deuda_publica_pct_pib",
    name: "macro.deuda_publica_pct_pib",
    viewName: "macro_deuda_publica_pct_pib",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-01-01",
    frecuencia: "Trimestral",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "49 trimestres",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Deuda bruta del Gobierno Central como porcentaje del Producto Interno Bruto (PIB), según el Banco Central.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del trimestre al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "deuda_bruta_gobierno_central_pct_pib", type: "DOUBLE", role: "Métrica", significado: "Deuda bruta del Gobierno Central de Chile al cierre del trimestre, como porcentaje del PIB.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_expectativas_inflacion",
    name: "macro.expectativas_inflacion",
    viewName: "macro_expectativas_inflacion",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-09-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "153 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Expectativas de inflación de la Encuesta de Expectativas Económicas (EEE) del Banco Central: variación del IPC en 12 meses vista, con horizonte de 11 y 23 meses, mediana en porcentaje.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "expectativa_inflacion_ipc_11_meses_pct", type: "DOUBLE", role: "Métrica", significado: "Mediana de la EEE para la variación anual del IPC dentro de 11 meses, en porcentaje.", contable: "No aplica" },
      { name: "expectativa_inflacion_ipc_23_meses_pct", type: "DOUBLE", role: "Métrica", significado: "Mediana de la EEE para la variación anual del IPC dentro de 23 meses, en porcentaje.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_expectativas_tpm",
    name: "macro.expectativas_tpm",
    viewName: "macro_expectativas_tpm",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-09-01",
    frecuencia: "Mensual",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "153 meses",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Expectativas de la Tasa de Política Monetaria (TPM) de la Encuesta de Expectativas Económicas (EEE) del Banco Central, con horizonte de 11 y 23 meses, mediana en porcentaje.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Primer día del mes al que corresponde el dato (AAAA-MM-01).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "expectativa_tpm_11_meses_pct", type: "DOUBLE", role: "Métrica", significado: "Mediana de la EEE para la TPM dentro de 11 meses, en porcentaje.", contable: "No aplica" },
      { name: "expectativa_tpm_23_meses_pct", type: "DOUBLE", role: "Métrica", significado: "Mediana de la EEE para la TPM dentro de 23 meses, en porcentaje.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_expectativas_operadores",
    name: "macro.expectativas_operadores",
    viewName: "macro_expectativas_operadores",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-07 a 2026-09-24",
    frecuencia: "Diaria",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "237 días",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Evolución diaria de la Encuesta de Operadores Financieros (EOF) del Banco Central: expectativa de inflación (variación del IPC) y de TPM para los 12 meses siguientes, en porcentaje.",
    columnas: [
      { name: "fecha", type: "VARCHAR", role: "PK", significado: "Fecha de la observación (AAAA-MM-DD), día hábil publicado por el BCCh.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la observación (AAAA-MM), útil para agrupar o cruzar con tablas mensuales.", contable: "No aplica" },
      { name: "expectativa_inflacion_12_meses_pct", type: "DOUBLE", role: "Métrica", significado: "Mediana de la Encuesta de Operadores Financieros para la inflación anual dentro de 12 meses, en porcentaje.", contable: "No aplica" },
      { name: "expectativa_tpm_12_meses_pct", type: "DOUBLE", role: "Métrica", significado: "Mediana de la Encuesta de Operadores Financieros para la TPM dentro de 12 meses, en porcentaje.", contable: "No aplica" }
    ]
  },
  {
    id: "macro_series_catalogo",
    name: "macro.series_catalogo",
    viewName: "macro_series_catalogo",
    sector: "macro",
    sectorLabel: "Macroeconomía y Tasas (BCCh)",
    norma: "Estadísticas oficiales BCCh",
    corte: "2014-01-01 a 2026-09-30",
    frecuencia: "Catálogo",
    frescura: "Se actualiza sola a diario",
    modo: "Automático · diario, incremental (cada serie desde su último dato)",
    ultimaActualizacion: "2026-09-30",
    registros: "51 series",
    origen: "Banco Central de Chile — Base de Datos Estadísticos, API REST SIETE (si3.bcentral.cl/SieteRestWS).",
    descripcion: "Una fila por serie del Banco Central que alimenta las tablas macro: código SIETE, nombre, grupo, frecuencia, unidad, título oficial del BCCh, cobertura y estado de la última consulta.",
    columnas: [
      { name: "clave", type: "VARCHAR", role: "PK", significado: "Identificador corto de la serie usado por el pipeline.", contable: "No aplica" },
      { name: "serie_id", type: "VARCHAR", role: "Atributo", significado: "Código oficial de la serie en la Base de Datos Estadísticos del BCCh.", contable: "No aplica" },
      { name: "nombre", type: "VARCHAR", role: "Atributo", significado: "Nombre descriptivo de la serie.", contable: "No aplica" },
      { name: "grupo", type: "VARCHAR", role: "Atributo", significado: "Tema: Tasas, Tipo de cambio, Precios y reajustes, Actividad, Mercado laboral, Commodities, Sector externo, Fiscal o Expectativas.", contable: "No aplica" },
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
  // <macro:fin>
  {
    id: "seguros_lista_entidades",
    name: "seguros.lista_entidades",
    viewName: "seguros_lista_entidades",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
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
      { name: "rut_aseguradora", type: "VARCHAR", role: "PK", significado: "Cuerpo del RUT de la compañía de seguros (sin dígito verificador); une con seguros.lista_entidades.", contable: "No aplica" },
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
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2024-12 (ampliable)",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Bonos, letras, depósitos y demás instrumentos de renta fija nacionales, uno por fila, con sus tasas, costo amortizado, valor razonable y valor final.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "codigo_operacion", type: "VARCHAR", role: "Atributo", significado: "Código que identifica la operación. Se informará de acuerdo a la siguiente codificación: CDT : Compra definitiva o a término. CRV : Compra con compromiso de retroventa.", contable: "No aplica" },
      { name: "folio_operacion", type: "BIGINT", role: "Métrica", significado: "Corresponde al número de la papeleta de la mesa de dinero de la compañía, donde se registra la compra del instrumento. En caso de no poder obtener este número se deberá asociar al documento contable que respalda la compra del instrumento.", contable: "No aplica" },
      { name: "item_operacion", type: "BIGINT", role: "Métrica", significado: "Secuencia del instrumento dentro del folio de la operación. No pueden existir dos instrumentos con igual folio e ítem operación.", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha en la cual la entidad aseguradora o reaseguradora adquirió el instrumento, emitió o adquirió el leasing o realizó el pacto. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "fecha_de_pago", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha en la cual la entidad aseguradora o reaseguradora realizó la liquidación de la transacción. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "nro_rut", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el RUT del emisor de cada título que forme parte de las inversiones de la compañía. Es obligatorio y no puede informarse en ceros.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Este campo es obligatorio y se informará de acuerdo a la codificación definida en SEIL, codificación S.V.S., Instrumentos.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Corresponde obligatoriamente informar el código nemotécnico de acuerdo a las instrucciones impartidas por Circular N° 1085 o la que la reemplace.", contable: "No aplica" },
      { name: "fecha_emision", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha desde la cual se inicia el devengamiento de intereses. En el caso de los Bonos de Reconocimiento corresponde a la expresión numérica de la fecha de afiliación.", contable: "No aplica" },
      { name: "num_inscripcion", type: "BIGINT", role: "Métrica", significado: "En el caso de instrumentos inscritos en la S.V.S., corresponde informar el número de inscripción del título. En caso contrario, se llenará con ceros.", contable: "No aplica" },
      { name: "fecha_inscripcion", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha de inscripción del instrumento. Se deberá informar con el siguiente formato: AAAAMMDD. Si no corresponde informar, se llenará con ceros.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la serie de cada instrumento cuando corresponda. En el caso de los instrumentos no seriados se deberá llenar con espacios.", contable: "No aplica" },
      { name: "pais", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el país donde se realizó la transacción del instrumento. Se informará de acuerdo a la codificación definida en el SEIL, Codificación S.V.S., Países. Si no corresponde informar, se llenará con espacios.", contable: "No aplica" },
      { name: "valor_nominal", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor nominal del instrumento a la fecha de cierre del mes a que se refiere la información. Es decir, los nominales comprados originalmente menos las ventas realizadas sobre el mismo título. No se deberán rebajar las amortizaciones del instrumento a la fecha de valorización.", contable: "No aplica" },
      { name: "valor_nominal_vigente", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor nominal vigente del instrumento a la fecha de cierre del mes a que se refiere la información. Se deberán rebajar las amortizaciones del instrumento a la fecha de valorización.", contable: "No aplica" },
      { name: "unidad_monetaria", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la unidad monetaria o la moneda en la cual está expresado el valor nominal. Se informará de acuerdo a la codificación definida en SEIL, codificación S.V.S., Unidades Monetarias.", contable: "No aplica" },
      { name: "prohibicion", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados se encuentran afectos a prohibiciones, gravámenes u otros impedimentos señalados en el DFL Nº 251.", contable: "No aplica" },
      { name: "activo_en_margen", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos registrados (en caso de haber agrupado instrumentos con características idénticas) se encuentran otorgados como margen de las operaciones de derivado señaladas en el DFL Nº251.", contable: "No aplica" },
      { name: "instrumento_vencido", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados, se encuentran vencidos a la fecha de cierre del mes a que se refiere la información, y no han sido cobrados; por ej.: BR vencido en proceso de cobranza al INP.", contable: "No aplica" },
      { name: "opcion_de_prepago_o_rescate", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si tienen opción de prepago. Se informará de acuerdo a la siguiente codificación: S : con opción. N : sin opción.", contable: "No aplica" },
      { name: "fecha_de_prepago", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha de prepago de los instrumentos, si la tuvieren. Se deberá informar con el siguiente formato: AAAAMMDD Si no corresponde informar, se llenará con ceros.", contable: "No aplica" },
      { name: "activo_respalda_reserva_valor_de_fondo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados, se encuentran respaldando la reserva de valor del fondo señalada en el DFL Nº251.", contable: "No aplica" },
      { name: "nombre_del_fondo", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que estén asociados a fondos que respalden seguros de vida con cuenta de inversión, se debe informar el nombre del Fondo al cual pertenece. Se entenderá por fondo al tipo de plan o modalidades de inversión convenidos para los seguros con cuentas de inversión.", contable: "No aplica" },
      { name: "nombre_cartera", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que no respalden seguros de vida con cuenta de inversión, se debe informar la sub cartera que respalda, si corresponde. Para instrumentos que no respalden una sub cartera, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "activo_calce", type: "VARCHAR", role: "Atributo", significado: "Sólo las compañías de vida deben informar si el instrumento, cumple con los requisitos establecidos en circular N° 1512 y posteriores modificaciones y además si son considerados para los distintos tramos de calce.", contable: "No aplica" },
      { name: "con_descriptor", type: "VARCHAR", role: "Atributo", significado: "Corresponde a si el instrumento tiene o no descriptor y tabla de desarrollo. Se informara de acuerdo a la siguiente codificación: “S”: Tiene descriptor y tabla de desarrollo. “B”: Para Bonos de reconocimiento. “U”. Para instrumentos distintos a los anteriores.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el emisor del instrumento está relacionado con la compañía de seguros, de acuerdo a lo establecido en el artículo N°100 de la ley N°18.045 del 22.10.1981 y sus modificaciones.", contable: "No aplica" },
      { name: "clasificacion_de_riesgo", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar la menor clasificación de riesgo vigente del instrumento a la fecha de cierre del mes a que se refiere la información. Si el instrumento no contara con clasificación de riesgo se debe informar S/C.", contable: "No aplica" },
      { name: "clasificacion_inversion", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación asignada a la inversión de renta fija, de acuerdo a la siguiente codificación: D: Disponible para la venta M: Mantenida hasta el vencimiento.", contable: "No aplica" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha en que el instrumento vence, es decir aquella del último cupón o pago único según corresponda. Se deberá informar con el siguiente formato: AAAAMMDD. Este campo debe ser informado para todos los instrumentos de este archivo.", contable: "No aplica" },
      { name: "tasa_emision", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa con la cual fue emitido el instrumento y con la cual se construyen los flujos de la tabla de desarrollo. Para el caso de instrumentos de intermediación financiera como por ejemplo: depósitos, pagarés, u otros, se deberá informar la tasa que paga el instrumento.", contable: "No aplica" },
      { name: "tasa_base", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la forma de cálculo de intereses del título. Se informará de acuerdo a la codificación definida en SEIL, codificación SVS, Circular 1835, Forma de cálculo de intereses.", contable: "No aplica" },
      { name: "tsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el instrumento está incluido en el Test de Suficiencia de Activo para el periodo informado, de acuerdo a la siguiente codificación: SI: el instrumento es utilizado para el análisis del Test de Suficiencia de Activos NO: el instrumento no es utilizado para el análisis del.", contable: "No aplica" },
      { name: "cobertura", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el instrumento está cubierto por un Derivado y qué tipo de operación de acuerdo a la siguiente Codificación En el primer carácter de este campo se debe indicar: S, si el instrumento está cubierto por un Derivado N, si el instrumento no está cubierto En los caracteres 2 al 5.", contable: "No aplica" },
      { name: "metod_clasif_valo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación dada al instrumento en los.", contable: "No aplica" },
      { name: "criterio_valorizaci", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada a Valor.", contable: "No aplica" },
      { name: "modelo_valoracion", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada por la Compañía utilizando un Modelo Propio de valorización de acuerdo a la siguiente codificación: SI : Utiliza Modelo Propio. NO: No utiliza Modelo Propio.", contable: "No aplica" },
      { name: "modelo_propio_deterioro", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el Deterioro de la inversión se determinó usando una metodología propia o es una aplicación de la metodología definida en la NCG N° 311. Se informará de acuerdo a la siguiente codificación: SI : Método propio para estimar el deterioro. NO : Aplicación de la NCG N°311.", contable: "Deterioro" },
      { name: "codigo_actividad_economica", type: "BIGINT", role: "Métrica", significado: "Se deberá informar para todos los instrumentos, la codificación designada por el Servicio Impuestos Internos para la actividad económica principal del emisor.", contable: "No aplica" },
      { name: "grupo_economico", type: "BIGINT", role: "Métrica", significado: "Se deberá informar el grupo económico al que pertenece el deudor, para los contratos de leasing, créditos sindicados, AFR y para cualquier otro activo expuesto al riesgo de crédito que no sea de oferta pública.", contable: "No aplica" },
      { name: "fuente_precios", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el nombre del proveedor del precio utilizado por la compañía para valorizar a valor razonable el instrumento.", contable: "No aplica" },
      { name: "rut_precio", type: "VARCHAR", role: "Identificador", significado: "Corresponde informar el RUT del proveedor de precios utilizado por la compañía para valorizar a valor razonable el instrumento. Para proveedores que no cuenten con RUT, se deberá informar con ceros.", contable: "No aplica" },
      { name: "tipo_nominales", type: "VARCHAR", role: "Atributo", significado: "Corresponde a si las unidades nominales están expresadas a fecha de emisión o a fecha de vencimiento. Esto especifica la forma de obtener un valor par o presente (descontando o capitalizando). Se informará de acuerdo a la siguiente codificación: I : a fecha de emisión F : a fecha de vencimiento.", contable: "No aplica" },
      { name: "tratamiento", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la forma de descuento del valor de los flujos futuros (interés más amortización). Se deberá codificar de la siguiente manera: CC : Con cupones. Indica que se trata de un instrumento con flujos de vencimiento regulares. SC : Sin cupones. CV : Cupones variables.", contable: "No aplica" },
      { name: "valor_inicial_m_clp", type: "BIGINT", role: "Métrica", significado: "En este campo se registrará el monto que resulte menor entre el valor del instrumento subyacente, según circular de valorización vigente y el monto efectivamente pagado de acuerdo al contrato de pacto, expresado en M$. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_pactado", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor al vencimiento del pacto, acordado en el contrato de pacto, expresado en la moneda del pacto.", contable: "No aplica" },
      { name: "unidad_monetaria_p", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la unidad monetaria o moneda en la cual está expresado el pacto. Se informará de acuerdo a la codificación definida en SEIL, codificación S.V.S., Unidades Monetarias.", contable: "No aplica" },
      { name: "fecha_venc_pacto", type: "VARCHAR", role: "Fecha", significado: "Corresponde informar la fecha de vencimiento del pacto. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "tasa_pacto", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar la tasa a la cual fue realizado el pacto, indicada en el contrato de pacto.", contable: "No aplica" },
      { name: "tasa_base_p", type: "VARCHAR", role: "Atributo", significado: "Corresponde informa la forma de cálculo de intereses del título. Se informará de acuerdo a la codificación definida en SEIL, codificación SVS, Circular 1835, Forma de cálculo de intereses.", contable: "No aplica" },
      { name: "tipo_nominales_p", type: "VARCHAR", role: "Atributo", significado: "Corresponde a los tipos nominales en que está expresado el pacto: I : a fecha de emisión F : a fecha de vencimiento.", contable: "No aplica" },
      { name: "valor_pacto_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el valor en que se encuentra contabilizado el pacto, de acuerdo a las instrucciones de Circular sobre valorización vigente de esta Superintendencia, a la fecha de cierre del mes a que se refiere la información, expresado en M$. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "codigo_agente", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el código de la agencia que administra el mutuo hipotecario. Se informará de acuerdo a la codificación definida en SEIL, codificación S.V.S., Agencias Administradoras de Mutuos Hipotecarios. Para el caso de los Leasing, se llenará con espacios.", contable: "No aplica" },
      { name: "fin_1", type: "BIGINT", role: "Métrica", significado: "Corresponde indicar la finalidad del mutuo otorgado. Los códigos permitidos son: 10: Bien raíz habitacional - urbano 11: Bien raíz habitacional - no urbano 20: Bien raíz no habitacional - urbano 21: Bien raíz no habitacional - no urbano 30: Fines generales Para el caso de los Leasing, se llenará.", contable: "No aplica" },
      { name: "fin_2", type: "VARCHAR", role: "Atributo", significado: "Se debe indicar para qué será utilizado el crédito. Los códigos permitidos son: A: Adquisición (bien raíz) C: Construcción (bien raíz) R: Reparación o Ampliación (bien raíz) F: Refinanciamiento (bien raíz o fines generales) P: Prepago (bien raíz o fines generales) O: Otro (fines generales) Debe.", contable: "No aplica" },
      { name: "tipo_deudor", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el deudor del mutuo o del leasing es persona natural o jurídica y si es persona relacionada o no a la compañía, de acuerdo a la siguiente codificación: A: persona natural no relacionada B: persona natural relacionada C: persona jurídica no relacionada D: persona jurídica.", contable: "No aplica" },
      { name: "rut_deudor", type: "VARCHAR", role: "Identificador", significado: "Se debe informar el Rut del deudor del mutuo hipotecario endosable o del contrato de leasing según sea el caso.", contable: "No aplica" },
      { name: "fecha_primer_dividendo", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la fecha de pago del primer dividendo en caso de mutuo y a la primera cuota en caso de leasing. Esta fecha será la que se considera como día de pago de los meses siguientes y será la que regirá para cualquier cálculo que haga la compañía.", contable: "No aplica" },
      { name: "monto_dividendo_o_cuota_um", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el monto del dividendo mensual para los mutuos, y el monto de la cuota mensual para los leasing, expresados en la unidad de reajustabilidad del instrumento. Expresado en unidad monetaria del instrumento.", contable: "No aplica" },
      { name: "dividendo_o_cuota_final_um", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el monto del último dividendo mensual para los mutuos, y el monto de la última cuota mensual para los leasing, expresados en la unidad de reajustabilidad del instrumento. Expresado en unidad monetaria del instrumento.", contable: "No aplica" },
      { name: "nro_dividendos_impagos_o_cuotas_impagas", type: "BIGINT", role: "Métrica", significado: "Corresponde al número de dividendos vencidos e impagos para los mutuos y al número de cuotas impagas para los leasings. Si las cantidades son menores a tres dígitos, se debe anteponer el dígito cero (0). Si no existen dividendos o cuotas impagas, se debe informar con ceros.", contable: "No aplica" },
      { name: "dividendos_impagos_o_cuotas_impagas_um", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la sumatoria de los dividendos vencidos e impagos a la fecha de cierre del mes a que se refiere la información, expresada en la unidad de reajustabilidad del mutuo. Para el caso de los leasings, corresponde a la sumatoria del total de cuotas vencidas e impagas a la misma fecha. Expresado en unidad monetaria del instrumento.", contable: "No aplica" },
      { name: "dividendos_impagos_o_cuotas_impagas_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor en miles de pesos (M$) del total de dividendos vencidos e impagos para los mutuos y del total de cuotas vencidas e impagas para los leasing. Si no existen dividendos o cuotas impagas, se debe informar con ceros. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_comercial_um", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor comercial del bien hipotecado entregado en garantía, que equivale al valor de la última tasación vigente, expresado en la misma unidad de reajustabilidad del mutuo. Para los leasings, se llenará con ceros. Expresado en unidad monetaria del instrumento.", contable: "No aplica" },
      { name: "valor_comercial_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor comercial en miles de pesos del bien hipotecado entregado en garantía, que equivale al valor de la última tasación vigente. Para los leasings, se llenará con ceros. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "fecha_tasacion", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha en que se efectuó la última tasación del bien hipotecado entregado en garantía. Se deberá informar con el siguiente formato: AAAAMMDD. Para los leasings, se llenará con ceros.", contable: "No aplica" },
      { name: "saldo_insoluto_deuda_um", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor presente de los flujos futuros de caja generados por el mutuo o contrato de leasing, descontados a la TIR de emisión, expresado en la unidad de reajustabilidad del instrumento a la fecha de cierre del mes a que se refiere la información. Expresado en unidad monetaria del instrumento.", contable: "No aplica" },
      { name: "saldo_insoluto_deuda_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor presente en miles de pesos de los flujos futuros de caja generados por el mutuo o contrato de leasing, descontados a la TIR de emisión, a la fecha de cierre del mes a que se refiere la información. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "spread_a_la_emision", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor del spread de tasa calculado a la emisión del contrato de leasing, según lo indicado en la NCG N° 148. Para el caso de los Mutuos Hipotecarios, se llenará con ceros.", contable: "No aplica" },
      { name: "endoso", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el mutuo hipotecario cuenta o no con la anotación del endoso a favor de la compañía, al margen de la inscripción hipotecaria de propiedad que garantiza el mutuo, la cual es requisito necesario para poder utilizar el mutuo hipotecario como in versión representativa de.", contable: "No aplica" },
      { name: "saldo_plazo_contrato", type: "BIGINT", role: "Métrica", significado: "Se deberá informar los meses restantes del contrato de leasing o mutuos hipotecarios a contar de la fecha de información.", contable: "No aplica" },
      { name: "rut_deudor_sindicado", type: "VARCHAR", role: "Identificador", significado: "Se debe informar el RUT del deudor.", contable: "No aplica" },
      { name: "nombre_deudor", type: "VARCHAR", role: "Atributo", significado: "Se debe informar el nombre del deudor del crédito.", contable: "No aplica" },
      { name: "porcentaje_participacion_compania", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar, qué porcentaje de participación le corresponde a la compañía en el capital otorgado.", contable: "No aplica" },
      { name: "monto_total_prestamo_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al monto total del crédito otorgado por las entidades que participan en la colocación. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "rut_lider", type: "VARCHAR", role: "Identificador", significado: "Se deberá informar el RUT de líder o agente del crédito sindicado.", contable: "No aplica" },
      { name: "nombre_lider", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar el nombre del Líder o agente del crédito sindicado.", contable: "No aplica" },
      { name: "porcentaje_valor_par", type: "DOUBLE", role: "Métrica", significado: "Corresponde al porcentaje de valor par al cual se adquirió el instrumento.", contable: "No aplica" },
      { name: "valor_compra_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el valor al cual la entidad aseguradora o reaseguradora adquirió el instrumento. Este monto deberá expresarse en pesos ($). Expresado en pesos.", contable: "Costo" },
      { name: "tir_sin_costo", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar la tasa de compra según lo definido en la 311, sin considerar los costos de adquisición del instrumento.", contable: "Costo" },
      { name: "tir_compra", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar la tasa de compra según lo definido en la NCG 311, esto es, la TIR de compra que incorpora los costos de adquisición. Tratándose de instrumentos adquiridos antes de 1 de enero de 2012, la TIR_COMPRA debe ser el mismo valor informado en la TIR_SIN_COSTO.", contable: "No aplica" },
      { name: "costo_amortizado_um", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el monto determinado según NCG 311 para aquellos instrumentos financieros clasificados como costo amortizado. En el caso de los contratos de leasing, se debe incluir el valor presente del contrato a TIR de compra. Este monto deberá expresarse en unidades monetarias originales. Expresado en unidad monetaria del instrumento.", contable: "Costo amortizado" },
      { name: "costo_amortizado_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el monto determinado según NCG 311 para aquellos instrumentos financieros clasificados como costo amortizado. En el caso de los contratos de leasing, se debe incluir el valor presente del contrato a TIR de compra. Este monto deberá expresarse en pesos ($). Expresado en pesos.", contable: "Costo amortizado" },
      { name: "tir_mercado", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar la tasa de mercado, utilizada para la valorización a la fecha de información, según lo indicado en la normativa de valorización.", contable: "No aplica" },
      { name: "valor_razonable_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor total de los flujos futuros del instrumento actualizados a la TIR de mercado. Este monto deberá expresarse en pesos ($). Expresado en pesos.", contable: "Valor razonable" },
      { name: "deterioro_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al deterioro de la inversión, según lo señalado en la Norma de Carácter General N°311, del 28.06.2011. Este monto deberá expresarse en pesos ($). Expresado en pesos.", contable: "Deterioro" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tiene el instrumento a la fecha de cierre del mes a que se refiere la información, según lo establecido en Circular de Valorización de Inversiones vigente. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "Valor contable informado" },
      { name: "custodia_inv", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar para cada instrumento, el tipo de custodia que presenta, de acuerdo a la siguiente codificación: CIA : Custodia en Compañía. DCV: Custodia en DCV, solo si la Cía. actuó como Depositante. EXT : Custodia en Otra entidad.", contable: "No aplica" },
      { name: "nombre_custodio", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el nombre de la entidad que custodia la inversión en el evento que se informe en el campo CUSTODIA_INV, el código EXT (otra entidad de custodia). En caso de que no corresponda informar, se deberá llenar con espacios este campo.", contable: "No aplica" },
      { name: "susceptibles_de_custodia", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si el instrumento es susceptible de ser custodiado de acuerdo a lo dispuesto en Circular N° 88 del Depósito Central de Valores S.A., y sus modificaciones posteriores, de acuerdo a la siguiente codificación: S: es susceptible de ser custodiado.", contable: "No aplica" },
      { name: "garantia_estatal", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si el instrumento cuenta con garantía por parte del Estado hasta la total extinción del instrumento, en consonancia con lo señalado en la letra a) del N°1 del artículo 21 del DFL N° 251, de 1931.", contable: "No aplica" },
      { name: "incremento_riesgo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si la situación del riesgo crediticio del instrumento financiero se ha incrementado significativamente desde el reconocimiento inicial, según lo instruido en la materia por la NCG N°311 e IFRS 9: S : Si el riesgo crediticio del instrumento financiero SI se ha incrementado.", contable: "No aplica" },
      { name: "plazo_al_vencimiento", type: "BIGINT", role: "Métrica", significado: "Se deberá informar los meses restantes al vencimiento del instrumento a contar de la fecha de información.", contable: "No aplica" },
      { name: "duracion", type: "DOUBLE", role: "Métrica", significado: "Corresponde al promedio ponderado en años de los vencimientos de sus flujos de caja, donde los ponderadores son el valor presente de cada flujo como una proporción del precio del instrumento.", contable: "No aplica" },
      { name: "tipo_amortizacion", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el tipo amortización del instrumento de renta fija, de acuerdo a la siguiente clasificación: 1: Cero 2: Francés 3: Bullet 16 4: Baloon 0: Otra.", contable: "No aplica" },
      { name: "subyacente", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar, para los instrumentos tipo BS, el tipo de activo al que corresponde el/los subyacente(s) , de acuerdo a la siguiente Codificación: M: Mutuos Hipotecarios. C: Créditos de Consumo. L: Contratos de Leasing. T: Tarjetas de Crédito. X: Cuentas por Cobrar. A: Créditos Automotriz.", contable: "No aplica" },
      { name: "efecto_patrimonio", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si una inversión, es valorizada a Valor razonable (VR) con cambios en otro resultado integral: SI: Con cambios en otro resultado integral. NO: Sin cambios en otro resultado integral. NA: Inversión valorizada a Costo Amortizado.", contable: "No aplica" },
      { name: "fin_cleas", type: "VARCHAR", role: "Atributo", significado: "Para el caso de leasing, se debe indicar si el financiamiento será utilizado para la construcción, de acuerdo a la siguiente codificación: S: Si N: No Para el caso de mutuos, completar con espacios.", contable: "No aplica" },
      { name: "deuda_garantia_otorgamiento", type: "DOUBLE", role: "Métrica", significado: "Se deberá informar la relación entre deuda y garantía del contrato de leasing o mutuo hipotecario a la fecha de otorgamiento. Por ejemplo, si para un registro el valor es 56,78%, se deberá informar 00567800.", contable: "No aplica" },
      { name: "deuda_garantia_informacion", type: "DOUBLE", role: "Métrica", significado: "Se deberá informar la relación entre deuda y garantía del contrato.", contable: "No aplica" },
      { name: "clasificacion_bco_lider", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si el Crédito Sindicado se encuentra o no en Cartera Normal, de acuerdo con la siguiente codificación: SI: el crédito sindicado se encuentra en Cartera Normal. NO: el crédito sindicado no se encuentra en Cartera Normal.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_acciones",
    name: "seguros.acciones",
    viewName: "seguros_acciones",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Acciones de sociedades anónimas y cuotas de fondos de inversión nacionales.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "Identificador", significado: "Se deberá informar el RUT del emisor de cada título, o el RUT de la administradora del fondo.", contable: "No aplica" },
      { name: "run", type: "VARCHAR", role: "Identificador", significado: "Se deberá informar el RUN del fondo que forma parte de las inversiones de cada compañía, de acuerdo a la codificación definida en SEIL, codificación S.V.S., Fondos de Inversión. Para el caso de acciones de sociedades anónimas se informara con ceros.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Este campo es obligatorio y se informará de acuerdo a la codificación definida en SEIL, codificación S.V.S., Instrumentos.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el código nemotécnico, de acuerdo a las instrucciones impartidas por Circular N° 1085 o la que la reemplace, utilizado para identificar el instrumento cuando se trate de acciones nacionales transadas en el mercado nacional o cuotas de fondos.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar la serie del instrumento cuando corresponda.", contable: "No aplica" },
      { name: "unidades", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el número de acciones o cuotas, propiedad de la entidad a la fecha de cierre del mes a que se refiere la información, agrupando todas las compras correspondientes al mismo emisor, fondo de inversión y serie, cuando corresponda.", contable: "No aplica" },
      { name: "pres_bursatil", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar la presencia bursátil de la acción o fondo, propiedad de la compañía, a la fecha de cierre del mes a que se refiere la información. Si no cuenta con presencia bursátil, se informará con ceros (0).", contable: "No aplica" },
      { name: "valor_costo_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al precio pagado por las acciones o por las cuotas de fondos de inversión, más los gastos asociados, tales como comisiones e impuestos (exceptos aquellos recuperables), a la fecha de cierre del mes a que se refiere la información. Este monto se deberá expresar en pesos ($). Expresado en pesos.", contable: "Costo" },
      { name: "valor_libro_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor libro unitario de una acción o al valor contable unitario de la cuota, por el número de UNIDADES. Expresado en pesos.", contable: "No aplica" },
      { name: "valor_bolsa_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor bolsa de la cuota o de la acción definido en Circular de Valorización, multiplicado por el número de UNIDADES, este monto se deberá expresar en pesos ($). Para el caso de sociedades anónimas cerradas o cuotas de fondos que no tengan valor bolsa, se deberá informar con ceros. Expresado en pesos.", contable: "Valor de mercado bruto" },
      { name: "valor_razonable_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor de mercado del instrumento a la fecha de la información. Se debe presentar en M$. Para las inversiones que no se transen en un mercado primario o secundario, se deberá informar una estimación del valor de mercado realizada por la compañía. Expresado en miles de pesos.", contable: "Valor razonable" },
      { name: "deterioro_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al deterioro de la inversión, según lo señalado en la Norma de Carácter General N°311, del 28.06.2011. Este monto deberá expresarse en miles de pesos (M$). Expresado en miles de pesos.", contable: "Deterioro" },
      { name: "provision_voluntaria_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde a la provisión voluntaria que pueden efectuar las entidades aseguradoras o reaseguradoras de acuerdo a lo indicado en la Circular de Valorización de Inversiones, en pesos ($). Expresado en pesos.", contable: "No aplica" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tiene el instrumento a la fecha de cierre del mes a que se refiere la información, según lo establecido en Circular de Valorización de Inversiones vigente. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "Valor contable informado" },
      { name: "unidad_monetaria", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la unidad monetaria o moneda de origen de la acción o cuota. Se informará de acuerdo a la codificación definida en SEIL.", contable: "No aplica" },
      { name: "ajuste_a_valor_economico", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la valorización de la cuota del fondo es ajustada a valor económico. Se informará de acuerdo a la siguiente codificación: S : Ajustado N : No ajustado Si no corresponde informar, se llenará con espacios.", contable: "No aplica" },
      { name: "prohibicion", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si los títulos registrados se encuentran afectos a prohibiciones, gravámenes u otros impedimentos señalados en el DFL Nº251. Se informará de acuerdo a la siguiente codificación: S : Si tiene prohibición. N : No tiene prohibición.", contable: "No aplica" },
      { name: "activo_en_margen", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos registrados (en caso de haber agrupado instrumentos con características idénticas) se encuentran otorgados como margen de las operaciones de derivado señaladas en el DFL Nº251.", contable: "No aplica" },
      { name: "unidades_en_margen", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el número de acciones o cuotas de fondos que se encuentran otorgados como margen de las operaciones de derivados señaladas en el DFL Nº251.", contable: "No aplica" },
      { name: "accion_en_prestamo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si una o más acciones registradas se encuentran, prestadas por la compañía, en operaciones de venta corta. Se informará de acuerdo a la siguiente codificación: S : acción afecta a préstamo por operación de venta corta.", contable: "No aplica" },
      { name: "unidades_en_prestamo", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el número de acciones prestadas por la compañía, en operaciones de venta corta.", contable: "No aplica" },
      { name: "activo_respalda_reserva_valor_de_fondo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados, se encuentran respaldando la reserva de valor del fondo señalada en el DFL Nº251.", contable: "No aplica" },
      { name: "nombre_del_fondo", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que estén asociados a fondos que respalden seguros de vida con cuenta de inversión, se debe informar el nombre del Fondo al cual pertenece. Se entenderá por fondo al tipo de plan o modalidades de inversión convenidos para los seguros con cuentas de inversión.", contable: "No aplica" },
      { name: "nombre_cartera", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que no respalden seguros de vida con cuenta de inversión, se debe informar la sub cartera que respalda, si corresponde. Para instrumentos que no respalden una sub cartera, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "custodia_inv", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar para cada instrumento, el tipo de custodia que presenta, de acuerdo a la siguiente codificación: CIA : Custodia en Compañía. DCV : Custodia en DCV, solo si la Cía. actuó como Depositante. EXT : Custodia en Otra entidad.", contable: "No aplica" },
      { name: "nombre_custodio", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el nombre de la entidad que custodia la inversión en el evento que se informe en el campo CUSTODIA_INV, el código EXT (otra entidad de custodia). En caso de que no corresponda informar, se deberá llenar con espacios este campo.", contable: "No aplica" },
      { name: "susceptibles_de_custodia", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si el instrumento es susceptible de ser custodiado de acuerdo a lo dispuesto en Circular N° 88 del Depósito Central de Valores S.A., y sus modificaciones posteriores, de acuerdo a la siguiente codificación: S: es susceptible de ser custodiado.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el emisor del instrumento está relacionado con la compañía de seguros, de acuerdo a lo establecido en el artículo N°100 de la ley N°18.045 del 22.10.1981 y sus modificaciones. Se señalará de acuerdo a la siguiente codificación: RE : Relacionado NR : No Relacionado.", contable: "No aplica" },
      { name: "filial_coligada", type: "VARCHAR", role: "Atributo", significado: "Se debe informar si la inversión informada corresponde a una empresa Filial o Coligada de acuerdo a la circular 2022, utilizando la siguiente codificación: FI: Empresa Filial CO: Empresa Coligada NA: Empresa que no es Filial o Coligada.", contable: "No aplica" },
      { name: "participacion_porcentual", type: "DOUBLE", role: "Métrica", significado: "Corresponde señalar el porcentaje de participación de la compañía en la sociedad filial a la fecha de cierre del mes al que se refiere la información.", contable: "No aplica" },
      { name: "patrimonio_filial_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el patrimonio contable de la filial a la fecha de cierre de los estados financieros para los meses de marzo, junio, septiembre y diciembre. Para los otros períodos, se debe informar el patrimonio contable de la filial del trimestre anterior al período informado. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "resultado_de_la_sociedad_filial_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al resultado (utilidad o pérdida) contable de la filial a la fecha de cierre de los estados financieros para los meses de marzo, junio, septiembre y diciembre. Para los otros períodos se debe informar el resultado contable de la filial del trimestre anterior al período informado. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "clasificacion_de_riesgo", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar la menor clasificación de riesgo vigente del instrumento a la fecha de cierre del mes a que se refiere la información. Si el instrumento no contara con clasificación de riesgo se debe informar S/C.", contable: "No aplica" },
      { name: "simultanea", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si una o más acciones registradas forman parte de una operación simultánea de acciones. Se informará de acuerdo a la siguiente codificación: CVS : acción afecta a operación simultánea. NVS : acción no afecta a operación simultánea.", contable: "No aplica" },
      { name: "tsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el instrumento está incluido en el Test de Suficiencia de Activos para el periodo informado, de acuerdo a la siguiente codificación: SI: el instrumento es utilizado para el análisis del Test de Suficiencia de Activos NO: el instrumento no es utilizado para el análisis del.", contable: "No aplica" },
      { name: "cobertura", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el instrumento está cubierto por un Derivado y qué tipo de operación de acuerdo a la siguiente Codificación En el primer carácter de este campo se debe indicar: S, si el instrumento está cubierto por un Derivado N, si el instrumento no está cubierto En los caracteres 2 al 5.", contable: "No aplica" },
      { name: "metod_clasif_valo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación dada al instrumento en los.", contable: "No aplica" },
      { name: "criterio_valorizaci", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada a Valor.", contable: "No aplica" },
      { name: "modelo_valoracion", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada por la Compañía utilizando un Modelo Propio de valorización de acuerdo a la siguiente codificación: SI : Utiliza Modelo Propio. NO: No utiliza Modelo Propio.", contable: "No aplica" },
      { name: "modelo_propio_deterioro", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el Deterioro de la inversión se determinó usando una metodología propia o es una aplicación de la metodología definida en la NCG N° 311. Se informará de acuerdo a la siguiente codificación: SI : Método propio para estimar el deterioro. NO : Aplicación de la NCG N°311.", contable: "Deterioro" },
      { name: "tipo_fondo", type: "VARCHAR", role: "Atributo", significado: "Para los fondos de inversiones corresponde informar el tipo de fondo según la siguiente clasificación: IN : Inmobiliario. CR : Capital de Riesgo. IE : Infraestructura OT : Otros. Para las acciones se deberá informar: AC.", contable: "No aplica" },
      { name: "rut_fondo_p", type: "VARCHAR", role: "Identificador", significado: "Para instrumentos de tipo CFIP y CFIPOIND, se debe informar el 31 Para instrumentos distintos a CFIP y CFIPOIND, se debe completar este campo con ceros.", contable: "No aplica" },
      { name: "nombre_fondo_p", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos de tipo CFIP y CFIPOIND, se debe informar el nombre del Fondo al cual pertenece. Para instrumentos distintos a CFIP y CFIPOIND, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "codigo_actividad_economica", type: "BIGINT", role: "Métrica", significado: "Se deberá informar para todos los instrumentos (acciones), la codificación designada por el Servicio Impuestos Internos para la actividad económica principal del emisor. Para fondos, se informará con ceros (0).", contable: "No aplica" },
      { name: "efecto_patrimonio", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si una inversión, es valorizada a Valor razonable (VR) con cambios en otro resultado integral: SI: Con cambios en otro resultado integral. NO: Sin cambios en otro resultado integral.", contable: "No aplica" },
      { name: "subyacente", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar los activos subyacentes de los fondos de inversión. Solo se informarán los tipos de activos cuya participación en la cartera de inversiones del fondo sea superior o igual al 10%.", contable: "No aplica" },
      { name: "segmento_fondo", type: "VARCHAR", role: "Atributo", significado: "Para los fondos de inversiones corresponde informar el segmento del fondo según la siguiente clasificación: 01: Accionarios; Fondos cuyas inversiones en al menos un 70% sean acciones de sociedades anónimas abiertas nacionales o extranjeras. 02: Capital Privado;", contable: "No aplica" },
      { name: "tipo_inmobiliario", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar, para inversiones en fondos con riesgo subyacente de tipo inmobiliario, el tipo de inversión inmobiliaria según la siguiente clasificación: 01: Renta Habitacional (Residencial): Corresponden a aquellos fondos que tienen por objetivo principal invertir en bienes raíces.", contable: "No aplica" },
      { name: "cuotas_suscritas", type: "BIGINT", role: "Métrica", significado: "Para los fondos de inversiones corresponde informar el número de cuotas suscritas y pagadas del fondo de inversión. Para acciones, se deberá completar con ceros.", contable: "No aplica" },
      { name: "porcentaje_participacion", type: "DOUBLE", role: "Métrica", significado: "Corresponde Informar el porcentaje de participación de la compañía respecto a las cuotas suscritas y pagadas del fondo de inversión. Para acciones, se deberá completar con ceros.", contable: "No aplica" },
      { name: "desarrollo_avance", type: "VARCHAR", role: "Atributo", significado: "Para el caso de TIPO_INMOBILIARIO 04, 05, 06 y 07, se debe.", contable: "No aplica" },
      { name: "tipo_gestion", type: "VARCHAR", role: "Atributo", significado: "Para el caso de TIPO_INMOBILIARIO 04, 05, 06 y 07, se debe indicar el tipo de gestión, de acuerdo a lo siguiente: A: Compañía es responsable de gestionar el proyecto y contrata directamente a una constructora para su desarrollo.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_fondos_mutuos",
    name: "seguros.fondos_mutuos",
    viewName: "seguros_fondos_mutuos",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Cuotas de fondos mutuos nacionales.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "Identificador", significado: "Se deberá informar el RUT de la administradora del fondo.", contable: "No aplica" },
      { name: "run", type: "VARCHAR", role: "Identificador", significado: "Corresponde informar el RUN de cada fondo que forma parte de las inversiones de la compañía de acuerdo a codificación definida en SEIL, Codificación S.V.S., Fondos Mutuos.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Este campo es obligatorio y se informará de acuerdo a la codificación definida en SEIL, Codificación S.V.S., Instrumentos.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el código nemotécnico de acuerdo a las instrucciones impartidas por Circular N° 1085 o la que la reemplace.", contable: "No aplica" },
      { name: "tipo_fondo", type: "VARCHAR", role: "Atributo", significado: "Se debe informar el tipo de fondo según la siguiente clasificación: IN : Inmobiliario. CA : Capital de Riesgo. IE : Infraestructura OT : Otros.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Se debe informar la serie del fondo mutuo. Si el fondo mutuo posee una serie única de cuotas se debe informar UNICA.", contable: "No aplica" },
      { name: "unidades", type: "DOUBLE", role: "Métrica", significado: "Corresponde al número de cuotas propiedad de la entidad a la fecha de cierre del mes a que se refiere la información.", contable: "No aplica" },
      { name: "unidad_monetaria", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la unidad monetaria o moneda en la que se contabiliza el fondo. Se informará de acuerdo a la codificación definida en SEIL, codificación S.V.S., Unidades Monetarias.", contable: "No aplica" },
      { name: "valor_cuota_clp", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor de rescate de la cuota a la fecha de cierre del mes a que se refiere la información, expresados en pesos ($). Expresado en pesos.", contable: "No aplica" },
      { name: "valor_de_inversion_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor pagado por las cuotas, más las comisiones e impuestos (exceptos aquellos recuperables) contabilizado a la fecha de cierre del mes a que se refiere la información, expresado en pesos ($). Expresado en pesos.", contable: "No aplica" },
      { name: "valor_razonable_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al producto del número de unidades por el valor de la cuota a la fecha de cierre del mes a que se refiere la información, en pesos ($). Expresado en pesos.", contable: "Valor razonable" },
      { name: "deterioro_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al deterioro de la inversión, según lo señalado en la Norma de Carácter General N°311, del 28.06.2011. Este monto deberá expresarse en pesos ($)”. Expresado en pesos.", contable: "Deterioro" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tiene el instrumento a la fecha de cierre del mes a que se refiere la información, según lo establecido en Circular de Valorización de Inversiones vigente. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "Valor contable informado" },
      { name: "prohibicion_o_gravamen", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si las cuotas de fondos mutuos registrados se encuentran afectos a prohibición o gravamen. Se informará de acuerdo a la siguiente codificación: S : Si tiene prohibición N : No tiene prohibición.", contable: "No aplica" },
      { name: "activo_en_margen", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos registrados (en caso de haber agrupado instrumentos con características idénticas) se encuentran otorgados como margen de las operaciones de derivado señaladas en el DFL Nº251.", contable: "No aplica" },
      { name: "unidades_en_margen", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el número de cuotas de fondos que se encuentran otorgados como margen de las operaciones de derivados señaladas en el DFL Nº251.", contable: "No aplica" },
      { name: "activo_respalda_reserva_valor_de_fondo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados, se encuentran respaldando la reserva de valor del fondo señalada en el DFL Nº251.", contable: "No aplica" },
      { name: "nombre_del_fondo", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que estén asociados a fondos que respalden seguros de vida con cuenta de inversión, se debe informar el nombre del Fondo al cual pertenece. Se entenderá por fondo al tipo de plan o modalidades de inversión convenidos para los seguros con cuentas de inversión.", contable: "No aplica" },
      { name: "nombre_cartera", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que no respalden seguros de vida con cuenta de inversión, se debe informar la sub cartera que respalda, si corresponde. Para instrumentos que no respalden una sub cartera, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "custodia_inv", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar para cada instrumento, el tipo de custodia que presenta, de acuerdo a la siguiente codificación: CIA: Custodia en Compañía. DCV: Custodia en DCV, solo si la Cía. actuó como Depositante. EXT: Custodia en Otra entidad.", contable: "No aplica" },
      { name: "nombre_custodio", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el nombre de la entidad que custodia la inversión en el evento que se informe en el campo CUSTODIA_INV, el código EXT (otra entidad de custodia). En caso de que no corresponda informar, se deberá llenar con espacios este campo.", contable: "No aplica" },
      { name: "susceptibles_de_custodia", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si el instrumento es susceptible de ser custodiado de acuerdo a lo dispuesto en Circular N° 88 del Depósito Central de Valores S.A., y sus modificaciones posteriores, de acuerdo a la siguiente codificación: S: es susceptible de ser custodiado.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el emisor del instrumento está relacionado con la compañía de seguros, de acuerdo a lo establecido en el artículo N°100 de la ley N°18.045 del 22.10.1981 y sus modificaciones. Se señalará de acuerdo a la siguiente codificación: RE : Relacionado NR : No Relacionado.", contable: "No aplica" },
      { name: "clasificacion_de_riesgo", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar la menor clasificación de riesgo vigente del instrumento a la fecha de cierre del mes a que se refiere la información. Si el instrumento no contara con clasificación de riesgo se debe informar S/C.", contable: "No aplica" },
      { name: "tsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el instrumento está incluido en el Test de Suficiencia de Activos para el periodo informado, de acuerdo a la siguiente codificación: SI: el instrumento es utilizado para el análisis del Test de Suficiencia de Activos NO: el instrumento no es utilizado para el análisis del.", contable: "No aplica" },
      { name: "cobertura", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el instrumento está cubierto por un Derivado y qué tipo de operación de acuerdo a la siguiente Codificación En el primer carácter de este campo se debe indicar: S, si el instrumento está cubierto por un Derivado N, si el instrumento no está cubierto En los caracteres 2 al 5.", contable: "No aplica" },
      { name: "metod_clasif_valo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación dada al instrumento en los.", contable: "No aplica" },
      { name: "criterio_valorizaci", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada a Valor.", contable: "No aplica" },
      { name: "modelo_valoracion", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada por la Compañía utilizando un Modelo Propio de valorización de acuerdo a la siguiente codificación: SI : Utiliza Modelo Propio. NO: No utiliza Modelo Propio.", contable: "No aplica" },
      { name: "modelo_propio_deterioro", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el Deterioro de la inversión se determinó usando una metodología propia o es una aplicación de la metodología definida en la NCG N° 311. Se informará de acuerdo a la siguiente codificación: SI : Método propio para estimar el deterioro. NO : Aplicación de la NCG N°311.", contable: "Deterioro" },
      { name: "simultanea", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si una o más cuotas de fondos registradas forman parte de una operación simultánea. Se informará de acuerdo a la siguiente codificación: CVS : Cuota de fondo afecta a operación simultánea. NVS : Cuota de fondo no afecta a operación simultánea.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_bienes_raices",
    name: "seguros.bienes_raices",
    viewName: "seguros_bienes_raices",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2024-12 (ampliable)",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Bienes raíces por rol: dirección, arriendo, costo, depreciación, tasaciones y valor final.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "rol", type: "VARCHAR", role: "Identificador", significado: "Corresponde señalar el número bajo el cual se encuentra identificado el bien raíz en el Servicio de Impuestos Internos.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_local", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un local. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_oficina", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una oficina. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_bodega", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una bodega. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_estacionamiento", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un estacionamiento. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_terreno", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un terreno. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_casa", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una casa. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_edificio", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un edificio. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_piso_completo_de_edificio", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un piso completo del edificio. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_piso_incompleto_de_edificio", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un piso incompleto del edificio. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_departamento", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un departamento. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_obra_en_construccion", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una obra en construcción. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_inmueble_otros", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es otros. S : Si N : No Ejemplos: 1. Si el bien raíz es una casa, se informará con una S en el campo CASA, y todos los otros campos deberán informarse con una N. 1.", contable: "No aplica" },
      { name: "tipo_de_inmueble", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar si el bien raíz es urbano o no urbano. Se informará de acuerdo a la siguiente codificación: UR : Urbano NU : No Urbano.", contable: "No aplica" },
      { name: "destino", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el bien raíz es \"Habitacional\" o \"No Habitacional\", de acuerdo a las correspondientes autorizaciones municipales. Se informará de acuerdo a la siguiente codificación: HA : Habitacional NH : No Habitacional.", contable: "No aplica" },
      { name: "uso", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar el uso que se le da al bien raíz, es decir si se arrienda con el fin de obtener una renta o es ocupado para desarrollar la actividad de seguros.", contable: "No aplica" },
      { name: "porcentaje_uso_propio", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar, cuando el uso es mixto, qué porcentaje del bien raíz está destinado para uso propio.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Este campo es obligatorio y se informará de acuerdo a la codificación definida en SEIL, Codificación S.V.S., Instrumentos. Para los bienes raíces dados en leasing, el tipo de instrumento será CLEAS.", contable: "No aplica" },
      { name: "codigo_nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar, cuando sea un bien raíz dado en leasing, el código asignado por esta Superintendencia, según lo señalado en Anexo Nº1 de esta Circular, si no corresponde, se informará con espacios.", contable: "No aplica" },
      { name: "arrendatario", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la razón social o el nombre del arrendatario de la forma: apellido paterno, apellido materno y primer nombre. Se informará para los bienes raíces dado en arrendamiento, ya sea como leasing financiero u operacional o simple arrendamiento.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "En el caso que el bien raíz se encuentre arrendado, corresponde informar si el arrendatario está relacionado con la compañía de seguros, de acuerdo a lo establecido en el artículo N°100 de la ley N°18.045 del 22.10.1981 y sus modificaciones.", contable: "No aplica" },
      { name: "saldo_plazo_arriendo", type: "BIGINT", role: "Métrica", significado: "Se deberá informar los meses restantes del contrato de arriendo a contar de la fecha de información. En el caso de los contratos de leasing, se debe indicar el plazo informado en el archivo B.1. En el caso de los bienes raíces de uso propio se debe informar en cero (0).", contable: "No aplica" },
      { name: "monto_arriendo_uf", type: "DOUBLE", role: "Métrica", significado: "Para los bienes raíces en arriendo, corresponde informar el monto de arriendo mensual expresado en UF. En caso de arriendos trimestrales, semestrales, anuales u otros deberán informarse el valor equivalente mensual de éstos. Expresado en UF.", contable: "No aplica" },
      { name: "ubicacion", type: "VARCHAR", role: "Atributo", significado: "Corresponderá señalar la dirección exacta del bien raíz.", contable: "No aplica" },
      { name: "comuna", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar la comuna donde se ubica geográficamente el bien raíz, de acuerdo a listado de códigos establecidos en el módulo SEIL, codificación SVS, Comuna.", contable: "No aplica" },
      { name: "ciudad", type: "VARCHAR", role: "Atributo", significado: "Corresponderá señalar la ciudad en donde se encuentra el bien raíz.", contable: "No aplica" },
      { name: "fecha_de_compra", type: "VARCHAR", role: "Fecha", significado: "Corresponderá señalar la fecha de adquisición del bien raíz. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "compra_entidad_relacionada", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el bien raíz fue adquirido a una entidad relacionada con la compañía de seguros, de acuerdo a lo establecido en las letras a) y b) del artículo N°100 de la ley N°18.045 de 22.10.1981.", contable: "No aplica" },
      { name: "costo_actualizado_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde señalar el valor de adquisición del bien raíz más su correspondiente revalorización a la fecha de cierre del mes a que se refiere la información, en miles de pesos (M$). Expresado en miles de pesos.", contable: "Costo" },
      { name: "depreciacion_acumulada_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde señalar el monto de depreciación acumulada a deducir del activo inmovilizado, en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "plazo", type: "BIGINT", role: "Métrica", significado: "Se deberá informar los meses de vida útil restante del bien raíz.", contable: "No aplica" },
      { name: "costo_corregido_y_depreciado_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde a la diferencia entre el costo actualizado del bien raíz y la depreciación acumulada, en miles de pesos (M$). Expresado en miles de pesos.", contable: "Costo" },
      { name: "tasacion_1_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde señalar el valor según lo dispuesto en Norma de Carácter General Nº42 de esta Superintendencia o la que la reemplace; Expresado en miles de pesos.", contable: "No aplica" },
      { name: "tasacion_2_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde señalar el valor según lo dispuesto en Norma de Carácter General Nº42 de esta Superintendencia o la que la reemplace; Expresado en miles de pesos.", contable: "No aplica" },
      { name: "nombre_del_tasador_1", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar la razón social o el nombre del profesional que emitió el informe de tasación 1. En este último caso, se indicará: apellido paterno, apellido materno y primer nombre.", contable: "No aplica" },
      { name: "nombre_del_tasador_2", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar la razón social o el nombre del profesional que emitió el informe de tasación 2. En este último caso, se indicará: apellido paterno, apellido materno, y primer nombre.", contable: "No aplica" },
      { name: "fecha_tasacion_1", type: "VARCHAR", role: "Fecha", significado: "Corresponderá señalar la fecha en que se efectuó la tasación 1. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "fecha_tasacion_2", type: "VARCHAR", role: "Fecha", significado: "Corresponderá señalar la fecha en que se efectuó la tasación 2. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "deterioro_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al deterioro de la inversión, según lo señalado en la Norma de Carácter General N°311, del 28.06.2011. Este monto deberá expresarse en miles de pesos (M$). Expresado en miles de pesos.", contable: "Deterioro" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tiene el bien raíz a la fecha de cierre del mes a que se refiere la información, según lo establecido en Circular de Valorización vigente, expresados en miles de pesos (M$). Expresado en miles de pesos.", contable: "Valor contable informado" },
      { name: "copropietaria", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar si la compañía es copropietaria de un bien raíz, si lo fuera, en este campo deberá informar el porcentaje de propiedad de la compañía.", contable: "No aplica" },
      { name: "prohibicion_o_gravamen", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si los bienes raíces registrados se encuentran afectos a prohibiciones o gravámenes u otros impedimentos señalados en el Art 22 DFL N°251. Se informará de acuerdo a la siguiente codificación: S : Si tiene prohibición N : No tiene prohibición.", contable: "No aplica" },
      { name: "activo_respalda_reserva_valor_de_fondo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados, se encuentran respaldando la reserva de valor del fondo señalada en el DFL Nº251.", contable: "No aplica" },
      { name: "nombre_del_fondo", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que estén asociados a fondos que respalden seguros de vida con cuenta de inversión, se debe informar el nombre del Fondo al cual pertenece. Se entenderá por fondo al tipo de plan o modalidades de inversión convenidos para los seguros con cuentas de inversión.", contable: "No aplica" },
      { name: "nombre_cartera", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que no respalden seguros de vida con cuenta de inversión, se debe informar la sub cartera que respalda, si corresponde. Para instrumentos que no respalden una sub cartera, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "tsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el instrumento está incluido en el Test de Suficiencia de Activos para el periodo informado, de acuerdo a la siguiente codificación: SI: el instrumento es utilizado para el análisis del Test de Suficiencia de Activos NO: el instrumento no es utilizado para el análisis del.", contable: "No aplica" },
      { name: "desarrollo_avance", type: "VARCHAR", role: "Atributo", significado: "Para el caso de bienes raíces en construcción, se debe indicar el.", contable: "No aplica" },
      { name: "tipo_gestion", type: "VARCHAR", role: "Atributo", significado: "Para el caso de bienes raíces en construcción, se debe indicar el tipo de gestión, de acuerdo a lo siguiente: A: La compañía es responsable de gestionar el proyecto y contrata directamente a una constructora para su desarrollo.", contable: "No aplica" },
      { name: "total_m2_terreno", type: "BIGINT", role: "Métrica", significado: "Para todos los bienes raíces informados, se deberá indicar el total de m2 del terreno. Para el caso de departamentos u oficinas en un edificio, se debe informar con ceros.", contable: "No aplica" },
      { name: "total_m2_construccion", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el total de m2 construidos del bien raíz.", contable: "No aplica" },
      { name: "valor_tasacion_terreno_m2_uf", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor en UF por metro cuadrado del terreno, obtenido a partir de la menor tasación de la propiedad. Si la tasación no presenta separada la valorización del terreno y la construcción, se debe informar con ceros. Expresado en UF.", contable: "No aplica" },
      { name: "valor_tasacion_construccion_m2_uf", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor en UF por metro cuadrado de la construcción, obtenido a partir de la menor tasación de la propiedad. Si la tasación no presenta separada la valorización del terreno y la construcción, se debe informar con ceros. Expresado en UF.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_extranjeros",
    name: "seguros.extranjeros",
    viewName: "seguros_extranjeros",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Inversiones en el extranjero: deuda (tipo_registro = 'deuda') y acciones y fondos (tipo_registro = 'acciones_y_fondos').",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "tipo_registro", type: "VARCHAR", role: "Atributo", significado: "Subtipo de registro dentro del archivo (por ejemplo forward, swap o deuda).", contable: "No aplica" },
      { name: "folio_operacion", type: "BIGINT", role: "Métrica", significado: "Corresponde al número de la papeleta de la mesa de dinero de la compañía, donde se registra la compra del instrumento. En caso de no poder obtener este número se deberá asociar al documento contable que respalda la compra del instrumento.", contable: "No aplica" },
      { name: "item_operacion", type: "BIGINT", role: "Métrica", significado: "Secuencia del instrumento dentro del folio de la operación. No pueden existir dos instrumentos con igual folio e ítem operación.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Este campo es obligatorio y se informará de acuerdo a la codificación definida en SEIL, Codificación S.V.S., Instrumentos.", contable: "No aplica" },
      { name: "valor_nominal", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor nominal vigente del instrumento a la fecha de cierre del mes a que se refiere la información. Es decir, los nominales comprados originalmente menos las ventas realizadas sobre el mismo título.", contable: "No aplica" },
      { name: "pais", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar el país donde se emitió el instrumento. Se informará de acuerdo a la codificación definida en SEIL, Codificación S.V.S., Países.", contable: "No aplica" },
      { name: "estado_garante", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar el estado u organismo garante del título. Este campo se llenará para el caso de instrumentos, como los Bonos Brady. Se informará de acuerdo a la codificación definida en SEIL, Codificación S.V.S., Países.", contable: "No aplica" },
      { name: "nombre_del_emisor", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la razón social o el nombre del emisor de cada título que forma parte de las inversiones de la compañía.", contable: "No aplica" },
      { name: "codigo_individualizacion_o_nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Corresponde obligatoriamente informar el código universal “ISIN” (International Securities Identification Number), a falta de éste, el código “CUSIP” (Commitee On Uniform Securities Identification Procedures). De no existir los anteriores, se deberá consultar a esta Superintendencia.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar la moneda en la cual está expresado el valor nominal. Se informara de acuerdo a la codificación definida en SEIL, Codificación S.V.S., Unidades Monetarias.", contable: "No aplica" },
      { name: "fecha_emision", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la expresión numérica de la fecha desde la cual se inicia el devengamiento de intereses. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la fecha en la cual la entidad aseguradora o reaseguradora adquirió el instrumento. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Corresponde a la fecha de vencimiento del instrumento. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "tipo_nominales", type: "VARCHAR", role: "Atributo", significado: "Corresponde a si las unidades nominales están expresadas a fecha de emisión o a fecha de vencimiento. Esto especifica la forma de obtener un valor par o presente (descontando o capitalizando). Se informará de acuerdo a la siguiente codificación: I : a fecha de emisión F : a fecha de vencimiento.", contable: "No aplica" },
      { name: "tratamiento", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la forma de descuento del valor de los flujos futuros (interés más amortización). Se deberá codificar de la siguiente manera: CC : Con cupones. Indica que se trata de un instrumento con flujos de vencimiento regulares. SC : Sin cupones. CV : Cupones variables.", contable: "No aplica" },
      { name: "tasa_emision", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa con la cual fue emitido el instrumento de deuda de tasa fija y con la cual se construyen los flujos de la tabla de desarrollo.", contable: "No aplica" },
      { name: "tasa_de_interes", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar para los instrumentos de deuda de interés variable la tasa de interés de referencia del instrumento. Por ejemplo Libor 360 Para los instrumentos de interés fijo se llenará con la tasa fijada.", contable: "Devengado" },
      { name: "tasa_base", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la forma de cálculo de intereses del título. Se informará de acuerdo a la codificación definida en SEIL, codificación SVS, Circular 1835, Forma de cálculo de intereses.", contable: "No aplica" },
      { name: "valor_compra_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el valor al cual la entidad aseguradora o reaseguradora adquirió el instrumento. Este monto deberá expresarse en pesos ($) a la paridad del tipo de cambio de cierre de la moneda de emisión. Expresado en pesos.", contable: "Costo" },
      { name: "tir_de_compra", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa de descuento utilizada para determinar el precio del instrumento al momento de la compra. Esta información será llenada para los instrumentos de deuda con tasa de interés fija, para los de interés variable se llenará con ceros (0).", contable: "No aplica" },
      { name: "valor_presente_tir_de_compra_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor presente de los flujos futuros del instrumento actualizados a la TIR de compra. Este monto deberá expresarse en miles de pesos (M$) a la paridad del tipo de cambio de cierre de la moneda de emisión. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "tir_mercado", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa de mercado, a la fecha de información, para un contrato de similares características. Según lo indicado en circular de valorización.", contable: "No aplica" },
      { name: "valor_razonable_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor total de los flujos futuros del instrumento actualizados a la TIR de mercado. Este monto deberá expresarse en miles de pesos (M$) a la paridad del tipo de cambio de cierre de la moneda de emisión. Expresado en miles de pesos.", contable: "Valor razonable" },
      { name: "deterioro_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al deterioro de la inversión, según lo señalado en la Norma de Carácter General N°311, del 28.06.2011. Este monto deberá expresarse en miles de pesos (M$). Expresado en miles de pesos.", contable: "Deterioro" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tiene el instrumento a la fecha de cierre del mes a que se refiere la información, según lo establecido en Circular de Valorización de Inversiones vigente. Este monto se deberá expresar en miles de pesos (M$) a la paridad del tipo de cambio de cierre de la moneda de emisión. Expresado en miles de pesos.", contable: "Valor contable informado" },
      { name: "prohibicion", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si uno o más títulos (en caso de haber agrupados instrumentos con características idénticas) registrados se encuentran afectos a prohibiciones, gravámenes u otros impedimentos señalados en el DFL Nº251.", contable: "No aplica" },
      { name: "clasificacion_de_riesgo", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar la menor clasificación de riesgo vigente del instrumento a la fecha de cierre del mes a que se refiere la información. Si el instrumento no contara con clasificación de riesgo se debe informar S/C.", contable: "No aplica" },
      { name: "activo_en_margen_o_sujeto_a_pacto", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos registrados (en caso de haber agrupado instrumentos con características idénticas) se encuentran otorgados como margen de las operaciones de derivados señaladas en el DFL Nº251 o si se encuentran sujetos a pacto, de acuerdo a lo señalado en la Circular de.", contable: "No aplica" },
      { name: "activo_comprado_a_traves_de_cdv", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) se adquirieron a través de CDV (Certificados de Depósito de Valores). Se informará de acuerdo a la siguiente codificación: CDV : inversión adquirida a través de CDV.", contable: "No aplica" },
      { name: "activo_respalda_reserva_valor_de_fondo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados, se encuentran respaldando la reserva de valor del fondo señalada en el DFL Nº251.", contable: "No aplica" },
      { name: "nombre_del_fondo", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que estén asociados a fondos que respalden seguros de vida con cuenta de inversión, se debe informar el nombre del Fondo al cual pertenece. Se entenderá por fondo al tipo de plan o modalidades de inversión convenidos para los seguros con cuentas de inversión.", contable: "No aplica" },
      { name: "nombre_cartera", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que no respalden seguros de vida con cuenta de inversión, se debe informar la sub cartera que respalda, si corresponde. Para instrumentos que no respalden una sub cartera, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el emisor del instrumento está relacionado con la compañía de seguros, de acuerdo a lo establecido en el artículo N°100 de la ley N°18.045 del 22.10.1981 y sus modificaciones. Se señalará de acuerdo a la siguiente codificación: RE : Relacionado NR : No Relacionado.", contable: "No aplica" },
      { name: "clasificacion_inversion", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación de la inversión, de acuerdo a la siguiente codificación: D: Disponible para la venta. M: Mantenida hasta el vencimiento.", contable: "No aplica" },
      { name: "tsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el instrumento está incluido en el Test de Suficiencia de Activos para el periodo informado, de acuerdo a la siguiente codificación: SI: el instrumento es utilizado para el análisis del Test de Suficiencia de Activos NO: el instrumento no es utilizado para el análisis del.", contable: "No aplica" },
      { name: "cobertura", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el instrumento está cubierto por un Derivado y qué tipo de operación de acuerdo a la siguiente Codificación En el primer carácter de este campo se debe indicar: S, si el instrumento está cubierto por un Derivado N, si el instrumento no está cubierto En los caracteres 2 al 5.", contable: "No aplica" },
      { name: "metod_clasif_valo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación dada al instrumento en los.", contable: "No aplica" },
      { name: "criterio_valorizacion", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada a Valor.", contable: "No aplica" },
      { name: "modelo_valoracio", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si la inversión está valorizada por la.", contable: "No aplica" },
      { name: "modelo_propio_deterioro", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el Deterioro de la inversión se determinó usando una metodología propia o es una aplicación de la metodología definida en la NCG N° 311. Se informará de acuerdo a la siguiente codificación: SI : Método propio para estimar el deterioro. NO : Aplicación de la NCG N°311.", contable: "Deterioro" },
      { name: "custodiado", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar si el instrumento se encuentra o no custodiado, de acuerdo a la siguiente codificación: S: Está custodiado N: No está custodiado.", contable: "No aplica" },
      { name: "nombre_custodio", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el nombre de la entidad que custodia la.", contable: "No aplica" },
      { name: "clasificacion_de_riesgo_pais", type: "VARCHAR", role: "Atributo", significado: "Las inversiones extranjeras del N°7 de la NCG 152, deberán indicar la clasificación de riesgo del país donde se encuentra el activo o donde se encuentra registrado el instrumento financiero correspondiente. Si no corresponde informar se llenará con espacios.", contable: "No aplica" },
      { name: "regulador", type: "VARCHAR", role: "Atributo", significado: "Las inversiones extranjeras del N°7 de la NCG 152, deberán indicar organismo supervisor del mercado financiero del emisor o administrador de la inversión del N°7 de la NCG 152. Si no corresponde informar, se llenará con espacios.", contable: "No aplica" },
      { name: "bolsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la Bolsa de Valores en la cual se adquirió el instrumento. Para aquellos que no se transen en Bolsa, se deberá colocar NT (no transa).", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "Identificador", significado: "Se deberá informar el RUT de la administradora del fondo en caso que corresponda. Si no corresponde informar, se llenará con ceros.", contable: "No aplica" },
      { name: "run", type: "VARCHAR", role: "Identificador", significado: "Se deberá informar el RUN de cada fondo que forma parte de las inversiones de la compañía, de acuerdo a codificación definida en SEIL, Codificación S.V.S., Fondos de Inversión o Fondos Mutuos. Si no corresponde informar, se llenará con ceros.", contable: "No aplica" },
      { name: "nombre_emisor", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la razón social o el nombre del emisor de cada título que forme parte de las inversiones de la compañía. De acuerdo a lo indicado en Anexo N° 6.", contable: "No aplica" },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Se deberá informar la serie del instrumento cuando corresponda.", contable: "No aplica" },
      { name: "tipo_fondo", type: "VARCHAR", role: "Atributo", significado: "Para los fondos mutuos y fondos de inversiones se debe informar el tipo de fondo según la siguiente clasificación: IN : Inmobiliario. CR : Capital de Riesgo. IE : Infraestructura OT : Otros. Para las acciones se deberá informar: AC.", contable: "No aplica" },
      { name: "unidades", type: "DOUBLE", role: "Métrica", significado: "Corresponde al número de acciones o cuotas de propiedad de la entidad a la fecha de cierre del mes a que se refiere la información.", contable: "No aplica" },
      { name: "requisito_presencia", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el instrumento cumple con los requisitos de presencia indicados en la normativa vigente. Se informará de acuerdo a la codificación definida en SEIL, codificación SVS, Circular 1835, Requisito presencia.", contable: "No aplica" },
      { name: "valor_bursatil_unitario", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor bolsa de la cuota o de la acción definido en Circular de Valorización, observado en la Bolsa de Valores donde se adquirió el título; y deberá expresarse en moneda de emisión del instrumento. Si no corresponde, esta información será llenada con ceros (0).", contable: "No aplica" },
      { name: "valor_libro_m_clp", type: "BIGINT", role: "Métrica", significado: "Para el caso de las cuotas de fondos de inversión nacionales cuyos activos estén invertidos en el extranjero, se indicará el valor libro de la cuota. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_bursatil_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor bursátil unitario, multiplicado por el número de unidades de propiedad de la compañía; deberá expresarse en miles de pesos (M$). Si no corresponde, esta información será llenada con ceros (0). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "costo_historico_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor de compra promedio ponderado de las acciones, expresado en miles de pesos (M$). Esta información para las cuotas de fondos será llenada con ceros (0). Expresado en miles de pesos.", contable: "Costo" },
      { name: "valor_cuota", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor de cierre de la cuota del fondo del último día hábil bursátil del mes a que se refiere la información, expresados en moneda de emisión de la cuota. Esta información para las acciones será llenada con ceros (0).", contable: "No aplica" },
      { name: "unidades_en_margen", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el número de acciones o de cuotas de fondos que se encuentran otorgados como margen de las operaciones de derivados señaladas en el DFL Nº251, o sujeto a pacto.", contable: "No aplica" },
      { name: "filial_coligada", type: "VARCHAR", role: "Atributo", significado: "Se debe informar si la inversión informada corresponde a una empresa Filial o Coligada de acuerdo a la circular 2022, utilizando la siguiente codificación: FI: Empresa Filial CO: Empresa Coligada NA: Empresa que no es Filial o Coligada.", contable: "No aplica" },
      { name: "descripcion_del_local", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un local. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_oficina", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una oficina. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_bodega", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una bodega. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_estacionamiento", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un estacionamiento. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_terreno", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un terreno. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_casa", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una casa. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_edificio", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un edificio. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_piso_completo_de_edificio", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un piso completo del edificio. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_piso_incompleto_de_edificio", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un piso incompleto del edificio. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_departamento", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es un departamento. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_obra_en_construccion", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es una obra en construcción. S : Si N : No.", contable: "No aplica" },
      { name: "descripcion_del_otros", type: "VARCHAR", role: "Atributo", significado: "Se indicará si es otros. S : Si N : No Ejemplos: 1. Si el bien raíz es una casa, se informará con una S en el campo CASA, y todos los otros campos deberán informarse con una N. 2.", contable: "No aplica" },
      { name: "tipo_de_inmueble", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar si el bien raíz es urbano o no urbano. Se informará de acuerdo a la siguiente codificación: UR : Urbano UN : No urbano.", contable: "No aplica" },
      { name: "destino", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el bien raíz es \"Habitacional\" o \"No Habitacional\". Se informara de acuerdo a la siguiente codificación: HA : Habitacional NH : No habitacional.", contable: "No aplica" },
      { name: "uso", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar el uso que se le da al bien raíz, es decir si se arrienda con el fin de obtener una renta o es ocupado para desarrollar la actividad de seguros.", contable: "No aplica" },
      { name: "porcentaje_uso_propio", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar cuando el uso es mixto, qué porcentaje del bien raíz está destinado para uso propio.", contable: "No aplica" },
      { name: "ubicacion", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar la dirección exacta del bien raíz.", contable: "No aplica" },
      { name: "saldo_plazo_arriendo", type: "BIGINT", role: "Métrica", significado: "Se deberá informar los meses restantes del contrato de arriendo a contar de la fecha de información. En el caso de los bienes raíces de uso propio se debe informar en cero (0).", contable: "No aplica" },
      { name: "monto_arriendo_uf", type: "DOUBLE", role: "Métrica", significado: "Para los bienes raíces en arriendo, corresponde informar el monto de arriendo mensual expresado en UF. En el caso de los bienes raíces de uso propio y de los leasing se debe informar en cero (0). Expresado en UF.", contable: "No aplica" },
      { name: "costo_historico_corregido_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde señalar el valor de adquisición del bien raíz expresado en miles de pesos (M$). Expresado en miles de pesos.", contable: "Costo" },
      { name: "depreciacion_acumulada_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde señalar el monto de depreciación acumulada del bien raíz a la fecha de cierre del mes a que se refiere la información, expresada en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_contable_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al costo histórico menos depreciación acumulada, en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_tasacion_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor, en miles de pesos (M$), de la última tasación efectuada, conforme a lo señalado en Norma de Carácter General Nº42 o la que la reemplace. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "fecha_de_tasacion", type: "VARCHAR", role: "Fecha", significado: "Corresponde señalar la fecha en que se efectuó la tasación. Se deberá informar en el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "nombre_filial", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar el nombre de la sociedad filial.", contable: "No aplica" },
      { name: "participacion_porcentual", type: "DOUBLE", role: "Métrica", significado: "Corresponde señalar el porcentaje de participación del inversionista en la sociedad filial a la fecha de cierre del mes a que se refiere la información.", contable: "No aplica" },
      { name: "patrimonio_filial_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el patrimonio contable de la filial a la fecha de cierre de los estados financieros para los meses de marzo, junio, septiembre y diciembre. Para los otros períodos se debe informar el patrimonio contable de la filial del trimestre anterior al período informado. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "resultado_de_la_sociedad_filial_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el resultado (utilidad o pérdida) contable de la filial a la fecha de cierre de los estados financieros para los meses de marzo, junio, septiembre y diciembre. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "fecha_estados_financieros", type: "VARCHAR", role: "Fecha", significado: "Corresponde señalar la fecha de cierre de los últimos estados financieros de la filial, utilizados para determinar el Valor Patrimonial Proporcional, VPP. Se deberá informar con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "valor_de_mercado_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor de mercado del instrumento a la fecha de la información. Se debe presentar en M$. Para las inversiones que no se transen en un mercado primario o secundario, se deberá informar una estimación del valor de mercado realizada por la compañía. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "mayor_o_menor_valor_de_inversiones_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al mayor o menor valor determinado entre el costo de adquisición y su VPP, ambos conceptos definidos en la Circular de Valorización de Inversiones, en miles de pesos (M$). Expresado en miles de pesos.", contable: "Valor razonable" },
      { name: "pais_matriz", type: "VARCHAR", role: "Atributo", significado: "Corresponde señalar el país donde reside la casa matriz del emisor del instrumento. Se informará de acuerdo a la codificación definida en SEIL, Codificación CMF, Países.", contable: "No aplica" },
      { name: "plazo_al_vencimiento", type: "BIGINT", role: "Métrica", significado: "Se deberá informar los meses restantes al vencimiento del instrumento a contar de la fecha de información.", contable: "No aplica" },
      { name: "duracion", type: "DOUBLE", role: "Métrica", significado: "Corresponde al promedio ponderado en años de los vencimientos de sus flujos de caja, donde los ponderadores son el valor presente de cada flujo como una proporción del precio del instrumento.", contable: "No aplica" },
      { name: "tipo_amortizacion", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el tipo amortización del instrumento de renta fija, de acuerdo a la siguiente clasificación: 1: Cero 2: Francés 3: Bullet 4: Baloon 0: Otra.", contable: "No aplica" },
      { name: "incremento_riesgo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si la situación del riesgo crediticio del instrumento financiero se ha incrementado significativamente desde el reconocimiento inicial, según lo instruido en la materia por la NCG N°311 e IFRS 9: S : Si el riesgo crediticio del instrumento financiero SI se ha incrementado.", contable: "No aplica" },
      { name: "efecto_patrimonio", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si una inversión, es valorizada a Valor razonable (VR) con cambios en otro resultado integral: SI: Con cambios en otro resultado integral. NO: Sin cambios en otro resultado integral. NA: Inversión valorizada a Costo Amortizado.", contable: "No aplica" },
      { name: "rut_fondo_p", type: "VARCHAR", role: "Identificador", significado: "Para instrumentos de tipo CFIIEP y CFIIEPOIED, constituidos en el país, se debe informar el RUT asociado. Para instrumentos distintos a CFIIEP y CFIIEPOIED, se debe completar este campo con ceros.", contable: "No aplica" },
      { name: "nombre_fondo_p", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos de tipo CFIIEP y CFIIEPOIED, constituidos en el país, se debe informar el nombre del Fondo. Para instrumentos distintos a CFIIEP y CFIIEPOIED, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "segmento_fondo", type: "VARCHAR", role: "Atributo", significado: "Para los fondos de inversiones corresponde informar el segmento del fondo según la siguiente clasificación: 01: Accionarios; Fondos cuyas inversiones en al menos un 70% sean acciones de sociedades anónimas abiertas nacionales o extranjeras. 02: Capital Privado;", contable: "No aplica" },
      { name: "tipo_inmobiliario", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar, para inversiones con riesgo subyacente de tipo inmobiliario, el tipo de inversión inmobiliaria según la siguiente clasificación: 80 01: Renta Habitacional (Residencial): Corresponden a aquellos fondos que tienen por objetivo principal invertir en bienes raíces habitacionales,.", contable: "No aplica" },
      { name: "subyacente", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar los activos subyacentes de los fondos de inversión. Solo se informarán los tipos de activos cuya participación en la cartera de inversiones del fondo sea superior o igual al 10%.", contable: "No aplica" },
      { name: "cuotas_suscritas", type: "BIGINT", role: "Métrica", significado: "Para los fondos mutuos y de inversión constituidos fuera del país y fondos de inversión constituidos en el país, cuyos activos estén invertidos en valores extranjeros, corresponde informar el número de cuotas suscritas y pagadas del fondo.", contable: "No aplica" },
      { name: "porcentaje_participacion", type: "DOUBLE", role: "Métrica", significado: "Corresponde Informar el porcentaje de participación de la compañía respecto a las cuotas suscritas y pagadas del fondo en aquellos casos que corresponda informar datos en el campo CUOTAS_SUSCRITAS. Para inversiones que no corresponda informar datos, se deberá completar con ceros.", contable: "No aplica" },
      { name: "simultanea", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si una o más acciones o cuotas de fondos registradas forman parte de una operación simultánea. Se informará de acuerdo a la siguiente codificación: CVS : acción o cuota de fondo afecta a operación simultánea. NVS : acción o cuota de fondo no afecta a operación simultánea.", contable: "No aplica" },
      { name: "total_m2_terreno", type: "BIGINT", role: "Métrica", significado: "Para todos los bienes raíces informados, se deberá indicar el total de m2 del terreno. Para el caso de departamentos u oficinas en un edificio, se debe informar con ceros.", contable: "No aplica" },
      { name: "total_m2_construccion", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el total de m2 construidos del bien raíz.", contable: "No aplica" },
      { name: "valor_tasacion_terreno_m2", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor por metro cuadrado del terreno, obtenido a partir de la menor tasación de la propiedad. Si la tasación no presenta separada la valorización del terreno y la construcción, se debe informar con ceros.", contable: "No aplica" },
      { name: "valor_tasacion_construccion_m2", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor por metro cuadrado de la construcción, obtenido a partir de la menor tasación de la propiedad. Si la tasación no presenta separada la valorización del terreno y la construcción, se debe informar con ceros.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_derivados",
    name: "seguros.derivados",
    viewName: "seguros_derivados",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Contratos de opciones, forwards, futuros y swaps (tipo_registro), con contraparte, nocional, valor razonable y efecto en resultados.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "tipo_registro", type: "VARCHAR", role: "Atributo", significado: "Subtipo de registro dentro del archivo (por ejemplo forward, swap o deuda).", contable: "No aplica" },
      { name: "objetivo_contrato", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el objetivo del contrato derivado, de acuerdo a lo señalado en la NCG N°200 de fecha 07.08.2006. Se señalará de acuerdo a la siguiente codificación: INV : Inversión CBE : Cobertura de riesgos financieros.", contable: "No aplica" },
      { name: "tipo_operacion", type: "VARCHAR", role: "Atributo", significado: "Código que identifica las operaciones informadas por la compañía, deben informarse todas las operaciones vigentes a la fecha de presentación de la información.", contable: "No aplica" },
      { name: "folio_operacion", type: "BIGINT", role: "Métrica", significado: "Corresponde al número de la papeleta de la mesa de dinero de la compañía, donde se registra la compra del instrumento derivado. En caso de no poder obtener este número se deberá asociar al documento contable que respalda la compra del instrumento.", contable: "No aplica" },
      { name: "item_operacion", type: "BIGINT", role: "Métrica", significado: "Secuencia del instrumento derivado dentro del folio de la operación. No pueden existir dos instrumentos derivados con igual folio e ítem operación.", contable: "No aplica" },
      { name: "fecha_de_la_operacion", type: "VARCHAR", role: "Fecha", significado: "Corresponde informar la fecha de inicio del contrato con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "fecha_de_vencimiento_del_contrato", type: "VARCHAR", role: "Fecha", significado: "Corresponde informar la fecha de término del contrato con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "nombre", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el nombre o razón social de la contraparte de la operación. Para el caso de las operaciones realizadas con bancos nacionales se informará de acuerdo a codificación definida en SEIL, Codificación SVS, Códigos Circular 1835, Códigos de Bancos, Nombre del Banco para C.1835.", contable: "No aplica" },
      { name: "nacionalidad", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la nacionalidad de la contraparte de la operación, de acuerdo a la codificación definida en SEIL, Codificación SVS, Países.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si la contraparte de la operación está relacionada con la compañía de seguros, de acuerdo a lo establecido en el artículo N°100 de la ley N°18.045 del 22.10.1981 y modificaciones. Se señalará de acuerdo a la siguiente codificación: RE : Relacionado NR : No Relacionado.", contable: "No aplica" },
      { name: "clasificacion_de_riesgo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la menor clasificación de riesgo vigente de la contraparte de la operación. Si la contraparte no contara con clasificación de riesgo se debe informar S/C.", contable: "No aplica" },
      { name: "activo_objeto_posicion_larga", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el activo objeto para opciones con posición larga, para opciones con posición corta indicar NO APLICA.", contable: "No aplica" },
      { name: "activo_objeto_posicion_corta", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el activo objeto para opciones con posición.", contable: "No aplica" },
      { name: "activo_objeto_unidades", type: "DOUBLE", role: "Métrica", significado: "Corresponde al número de unidades del activo subyacente de cada.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la moneda en la cual está denominado el derivado, cuando corresponda. Se informará de acuerdo a la codificación definida en el sitio web de esta Superintendencia en el módulo SEIL, Codificación SVS, Unidad Monetaria. De no existir, se deberá consultar a esta Superintendencia.", contable: "No aplica" },
      { name: "precio_de_ejercicio", type: "DOUBLE", role: "Métrica", significado: "Precio de intercambio a futuro fijado en el contrato, por una unidad del activo subyacente. Debe ser expresado en la moneda en la cual está denominado el derivado.", contable: "No aplica" },
      { name: "precio_spot_del_activo_subyacente", type: "DOUBLE", role: "Métrica", significado: "Corresponde al precio de cierre observado del activo subyacente a la opción, a la fecha de la información. En caso de Opción sobre moneda, corresponde al valor de la moneda en el mercado contado a la fecha de información.", contable: "No aplica" },
      { name: "prima_de_la_opcion_monto", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor pagado o recibido por la suscripción de la opción.", contable: "No aplica" },
      { name: "prima_de_la_opcion_moneda", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la moneda en que se encuentra expresada la prima de la opción, de acuerdo a la codificación definida en SEIL, Codificación SVS, Unidades Monetarias.", contable: "No aplica" },
      { name: "valor_razonable_del_activo_objeto_a_la_fecha_de_informacion_monto", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el precio spot del activo objeto a la fecha de información multiplicado por el número de unidades del activo subyacente de cada contrato (M$).", contable: "Valor razonable" },
      { name: "numero_de_contratos", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el número de contratos comprados o vendidos en cada operación.", contable: "No aplica" },
      { name: "valor_razonable_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor razonable de la opción, a la fecha de cierre del mes a que se refiere la información (M$). Expresado en miles de pesos.", contable: "Valor razonable" },
      { name: "origen_de_la_informacion", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la fuente de donde se obtuvieron los datos para valorizar el contrato.", contable: "No aplica" },
      { name: "activo_respalda_reserva_valor_de_fondo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si uno o más títulos (en caso de haber agrupado instrumentos con características idénticas) registrados, se encuentran respaldando la reserva de valor del fondo señalada en el DFL Nº251.", contable: "No aplica" },
      { name: "nombre_del_fondo", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que estén asociados a fondos que respalden seguros de vida con cuenta de inversión, se debe informar el nombre del Fondo al cual pertenece. Se entenderá por fondo al tipo de plan o modalidades de inversión convenidos para los seguros con cuentas de inversión.", contable: "No aplica" },
      { name: "nombre_cartera", type: "VARCHAR", role: "Atributo", significado: "Para instrumentos que no respalden seguros de vida con cuenta de inversión, se debe informar la sub cartera que respalda, si corresponde. Para instrumentos que no respalden una sub cartera, se debe informar “NO APLICA”.", contable: "No aplica" },
      { name: "monto_activos_en_margen_m_clp", type: "BIGINT", role: "Métrica", significado: "Se deberá informar el valor final, a la fecha de información, de los activos entregados como margen en la operación, expresado en miles de pesos (M$). Si para la operación no es necesario dejar activos en margen indicar cero. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "monto_activo_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el monto contabilizado en activos producto de este contrato, es decir, el producto entre el valor de la opción a la fecha de la información y el número de contratos. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "monto_pasivo_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el monto contabilizado en pasivos producto de este contrato, es decir, el producto entre el valor de la opción a la fecha de la información y el número de contratos. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "efecto_en_resultados_realizados_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el efecto realizado en los resultados de las operaciones a la fecha de los estados financieros. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "tsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el instrumento está incluido en el Test de Suficiencia de Activos para el periodo informado, de acuerdo a la siguiente codificación: SI: el instrumento es utilizado para el análisis del Test de Suficiencia de Activos NO: el instrumento no es utilizado para el análisis del.", contable: "No aplica" },
      { name: "metod_clasif_valo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación dada al instrumento en los.", contable: "No aplica" },
      { name: "activo_objeto_posicion_larga_unidades", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el número de unidades del activo subyacente en el cual esta expresada la posición larga de cada contrato.", contable: "No aplica" },
      { name: "activo_objeto_posicion_corta_unidades", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el número de unidades del activo subyacente en el cual esta expresada la posición corta de cada contrato.", contable: "No aplica" },
      { name: "precio_forward_contrato", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el precio a futuro establecido en el contrato. En caso de un forward de moneda corresponde informar el valor al cual será intercambiada la moneda de acuerdo a la posición que tenga la compañía en el contrato.", contable: "No aplica" },
      { name: "valor_de_mercado_del_activo_objeto_a_la_fecha_de_informacion_monto", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el precio spot del activo objeto a la fecha de información multiplicado por el número de unidades del activo subyacente de cada contrato (M$).", contable: "No aplica" },
      { name: "precio_forward_mercado", type: "DOUBLE", role: "Métrica", significado: "Precio forward de mercado a la fecha de valorización, para un contrato de similares características al valorizado, entendiéndose por características del contrato, el activo subyacente y la fecha que le resta al vencimiento desde la fecha de valorización.", contable: "No aplica" },
      { name: "tasa_descuento_de_flujos", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa de interés real anual de mercado para operaciones similares a plazos equivalentes a la madurez del contrato o a la Tir de compra para los derivados que cubren activos acogidos a la Circular N° 1512.", contable: "No aplica" },
      { name: "valor_razonable_del_contrato_a_la_fecha_de_la_informacion", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que presenta el contrato forward a la fecha de información, que se define como el valor actual de la diferencia entre el precio forward de mercado para un contrato de similares características menos el precio forward fijado en el contrato, multiplicado por los nominales del.", contable: "Valor razonable" },
      { name: "precio_futuro_de_mercado_al_inicio_de_la_operacion", type: "DOUBLE", role: "Métrica", significado: "Corresponde al precio futuro de mercado del contrato a la fecha de cierre del trimestre anterior; o bien, a la fecha de inicio de la operación si es que ésta se efectúo durante el trimestre que se está informando.", contable: "No aplica" },
      { name: "precio_futuro_de_mercado_a_la_fecha_de_informacion", type: "DOUBLE", role: "Métrica", significado: "Corresponde al precio futuro de mercado a la fecha de información, para un contrato de idénticas características. Este debe ser expresado de acuerdo a la moneda extranjera establecida por contrato a ser entregada o recibida en una fecha futura.", contable: "No aplica" },
      { name: "valor_razonable_del_contrato_futuro_a_la_fecha_de_informacion", type: "BIGINT", role: "Métrica", significado: "Para aquellos Futuros que no tengan compensación diaria se debe informar el valor neto de la posición del futuro, el cual corresponde a la diferencia entre los montos contabilizados en activos y pasivos producto de este contrato, a la fecha de cierre en miles de pesos (M$).", contable: "Valor razonable" },
      { name: "activo_objeto_posicion_larga_nocional", type: "DOUBLE", role: "Métrica", significado: "Corresponde al Valor nocional establecido por contrato, que será recibido en una fecha futura por la compañía.", contable: "No aplica" },
      { name: "activo_objeto_posicion_corta_nocional", type: "DOUBLE", role: "Métrica", significado: "Corresponde al Valor nocional establecido por contrato, que será entregado en una fecha futura por la compañía.", contable: "No aplica" },
      { name: "moneda_posicion_larga", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la moneda en la cual está expresada la posición larga en el contrato swap, es decir la moneda en que está denominada la tasa o el nocional, que debe ser recibido en una fecha futura, cuando corresponda.", contable: "No aplica" },
      { name: "moneda_posicion_corta", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la moneda en la cual está expresada la posición corta en el contrato swap, es decir la moneda en que está denominada la tasa o el nocional, que debe ser entregado en una fecha futura, cuando corresponda.", contable: "No aplica" },
      { name: "tasa_a_futuro_contrato_posicion_larga", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la tasa a futuro establecida en el contrato swap la cual generará los flujos a ser recibidos en una fecha futura, cuando corresponda. Ej.: Fija 8,5%, Libor, etc.", contable: "No aplica" },
      { name: "tasa_a_futuro_contrato_posicion_corta", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la tasa a futuro establecida en el contrato swap la cual generará los flujos a ser entregados en una fecha futura, cuando corresponda. Ej: Fija 7,4%, Libor, etc.", contable: "No aplica" },
      { name: "t_c_futuro_contrato", type: "DOUBLE", role: "Métrica", significado: "Corresponde al tipo de cambio a futuro establecido en el contrato swap y deberá ser expresado de acuerdo a la moneda extranjera establecida por contrato a ser entregada o recibida en una fecha futura.", contable: "No aplica" },
      { name: "tasa_a_futuro_mercado_posicion_larga", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa de interés única, que aplicada a cada flujo del swap de la posición larga, genera el mismo valor presente que al valorizar cada flujo usando la estructura cero cupón de mercado a la fecha.", contable: "No aplica" },
      { name: "tasa_a_futuro_mercado_posicion_corta", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa de interés única, que aplicada a cada flujo del swap de la posición corta, genera el mismo valor presente que al valorizar cada flujo usando la estructura cero cupón de mercado a la fecha.", contable: "No aplica" },
      { name: "tipo_de_cambio_me", type: "DOUBLE", role: "Métrica", significado: "Tipo de cambio spot de mercado a la fecha de valorización.", contable: "No aplica" },
      { name: "valor_presente_posicion_larga_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor actual de los flujos a recibir descontados a la tasa de mercado posición larga o a Tir de compra según corresponda. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_presente_posicion_corta_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor actual de los flujos a entregar descontados a la tasa de mercado posición corta o a Tir de compra según corresponda. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_razonable_del_activo_objeto_a_la_fecha_de_la_informacion_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar, en caso de: Swaps de monedas: el valor de mercado de la moneda multiplicada por los nominales del contrato Swaps de tasa de interés: el valor presente del nocional o de referencia del contrato Swaps sobre instrumento de renta fija: el número de unidades del instrumento o. Expresado en miles de pesos.", contable: "Valor razonable" },
      { name: "valor_razonable_del_contrato_a_la_fecha_de_la_informacion_m", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor razonable que presenta el contrato swap, o uno de similares características, a la fecha de información. En el caso de derivados que cubran activos acogidos a la Circular N°1.512, corresponde al valor del contrato utilizando la TIR de compra.", contable: "Valor razonable" },
      { name: "tipo_contrato", type: "BIGINT", role: "Métrica", significado: "Se debe informar el tipo de subyacente sobre el cual está realizado el contrato, de acuerdo con la siguiente codificación: 01: Tasas de interés o inflación 02: Monedas extranjeras 110 03: Acciones o Índices Accionarios.", contable: "No aplica" },
      { name: "rut_contraparte_nacional", type: "VARCHAR", role: "Identificador", significado: "informa sólo para contrapartes nacionales. En caso de contrapartes extranjeras, se deberá informar con ceros (0). Dígito verificador del RUT de la contraparte. Este campo se informa.", contable: "No aplica" },
      { name: "lei_contraparte_extranjera", type: "VARCHAR", role: "Identificador", significado: "En caso de contrapartes nacionales, o contrapartes extranjeras que no tuvieran código LEI, se deberá informar con espacios.", contable: "No aplica" },
      { name: "tipo_contraparte", type: "BIGINT", role: "Métrica", significado: "Se debe informar el tipo de contraparte de acuerdo con la siguiente codificación: 01: ECC (entidades de contraparte central) nacional 02: Banco nacional 03: Otras autorizadas CMF nacional 04: ECC (entidades de contraparte central) en el exterior 05: Banco exterior 06: Otras en el exterior.", contable: "No aplica" },
      { name: "cm_compensacion_bilateral", type: "VARCHAR", role: "Atributo", significado: "Corresponde indicar si el contrato de derivado se ampara bajo un Central de Chile, de acuerdo con la siguiente codificación: SI: El contrato ha sido celebrado bajo el amparo de un contrato marco de compensación bilateral de aquellos reconocidos por el Banco Central de Chile.", contable: "No aplica" },
      { name: "tipo_documentacion", type: "BIGINT", role: "Métrica", significado: "Se debe indicar el tipo de contrato marco bajo el cual se ampara la.", contable: "No aplica" },
      { name: "anexo_garantia", type: "VARCHAR", role: "Atributo", significado: "Para el caso de que el contrato de derivados haya sido celebrado bajo el amparo de un contrato marco, corresponde informar si dicho contrato marco cuenta con anexo de garantías, según la siguiente codificación: SI: El contrato marco cuenta con anexo de garantías NO: El contrato marco no cuenta con.", contable: "No aplica" },
      { name: "identificador_garantia", type: "VARCHAR", role: "Atributo", significado: "Sólo se debe informar el identificador para instrumentos derivados que posean márgenes de variación. En caso de que no corresponda informar un código, se deberá completar con espacios.", contable: "No aplica" },
      { name: "nocional_posicion_larga_monto", type: "BIGINT", role: "Métrica", significado: "", contable: "No aplica" },
      { name: "nocional_posicion_corta_monto_m_clp", type: "BIGINT", role: "Métrica", significado: "contrato, expresado en M$, a la fecha de la información. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_razonable_del_contrato_a_la_fecha_de_la_informacion_ec", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que presenta el contrato forward a la fecha de el precio forward de mercado para un contrato de similares características menos el precio forward fijado en el contrato, a comprar o vender. (M$).", contable: "Valor razonable" },
      { name: "tasa_a_futuro_contrato_posicion_larga_ec", type: "BIGINT", role: "Métrica", significado: "Corresponde informar si la tasa de interés del contrato es fija o 02: Flotante.", contable: "No aplica" },
      { name: "tasa_a_futuro_contrato_posicion_corta_ec", type: "BIGINT", role: "Métrica", significado: "Corresponde informar si la tasa de interés del contrato es fija o 02: Flotante.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_pactos",
    name: "seguros.pactos",
    viewName: "seguros_pactos",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Compras y ventas con pacto (repos), con contraparte, tasa y activo objeto.",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "tipo_operacion", type: "VARCHAR", role: "Atributo", significado: "Código que identifica las operaciones informadas por la compañía, deben informarse todas las operaciones vigentes a la fecha de presentación de la información.", contable: "No aplica" },
      { name: "folio_operacion", type: "BIGINT", role: "Métrica", significado: "En el caso que la operación corresponda a una retroventa, se debe indicar el número de la papeleta de la mesa de dinero de la compañía, donde se registra la operación subyacente al pacto. Para otro tipo de pacto se debe informar el folio de la operación de pacto.", contable: "No aplica" },
      { name: "item_operacion", type: "BIGINT", role: "Métrica", significado: "Secuencia dentro del folio de la operación. No pueden existir dos operaciones con igual folio e ítem operación.", contable: "No aplica" },
      { name: "fecha_de_la_operacion", type: "VARCHAR", role: "Fecha", significado: "Corresponde informar la fecha de inicio del contrato de pacto con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "fecha_de_vencimiento_del_contrato", type: "VARCHAR", role: "Fecha", significado: "Corresponde informar la fecha de vencimiento del contrato de pacto con el siguiente formato: AAAAMMDD.", contable: "No aplica" },
      { name: "tasa_pacto", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar la tasa a la cual fue realizado el pacto, indicada en el contrato de pacto.", contable: "No aplica" },
      { name: "nombre", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el nombre o razón social de la contraparte del pacto. Para el caso de las operaciones realizadas con bancos nacionales se informará de acuerdo a codificación definida en SEIL, Codificación SVS, Códigos Circular 1835, Códigos de Bancos, Nombre del Banco para C.1835.", contable: "No aplica" },
      { name: "nacionalidad", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la nacionalidad de la contraparte del pacto, de acuerdo a la codificación definida en SEIL, Codificación SVS, Países.", contable: "No aplica" },
      { name: "relacionado", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si la contraparte del pacto de la operación está relacionada con la compañía de seguros, de acuerdo a lo establecido en el artículo N°100 de la ley N°18.045 del 22.10.1981 y modificaciones. Se señalará de acuerdo a la siguiente codificación: RE : Relacionado NR : No Relacionado.", contable: "No aplica" },
      { name: "activo_objeto", type: "VARCHAR", role: "Atributo", significado: "Instrumento subyacente al pacto. En el caso de tratarse de un.", contable: "No aplica" },
      { name: "serie_activo_objeto", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la serie del instrumento subyacente al pacto cuando corresponda.", contable: "No aplica" },
      { name: "nro_rut_activo_objeto", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar el Rut del emisor del instrumento subyacente.", contable: "No aplica" },
      { name: "valor_nominal", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el valor nominal del instrumento subyacente a la fecha de presentación de la información. Se entiende por “nominal” los nominales comprados originalmente menos las ventas realizadas sobre este título.", contable: "No aplica" },
      { name: "tir_compra", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa anual de descuento utilizada para determinar el precio del instrumento subyacente al momento de la compra.", contable: "No aplica" },
      { name: "tasa_emision", type: "DOUBLE", role: "Métrica", significado: "Corresponde a la tasa a la cual fue emitido el instrumento subyacente.", contable: "No aplica" },
      { name: "activo_objeto_valor_contable", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor contable del instrumento subyacente al pacto.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Corresponde a la moneda en la cual está denominado el instrumento subyacente el pacto, cuando corresponda. Se informará de acuerdo a la codificación definida en el sitio web de esta Superintendencia en el módulo SEIL, Codificación SVS, Unidades Monetarias.", contable: "No aplica" },
      { name: "tasa_o_precio_de_mercado", type: "DOUBLE", role: "Métrica", significado: "Tasa de mercado del instrumento subyacente al pacto, a la fecha de valorización.", contable: "No aplica" },
      { name: "valor_de_mercado_a_la_fecha_de_suscripcion_monto", type: "DOUBLE", role: "Métrica", significado: "Corresponde informar el monto del valor de mercado, del activo objeto a la fecha de suscripción del pacto.", contable: "No aplica" },
      { name: "valor_inicial_um", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor invertido en la operación, indicado en el contrato de pacto, expresado en la moneda del pacto.", contable: "No aplica" },
      { name: "valor_pactado", type: "DOUBLE", role: "Métrica", significado: "Corresponde al valor del pacto al vencimiento, acordado en el contrato de pacto, expresado en la moneda del pacto.", contable: "No aplica" },
      { name: "interes_devengado_del_pacto_m", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el interés que resulte de aplicar la tasa implícita entre el valor de compra del activo objeto y el monto a recibir por el cumplimiento del compromiso de venta, en proporción.", contable: "Devengado" },
      { name: "valorizacion_de_pacto_a_la_fecha_de_cierre_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el valor en que se encuentra contabilizado el pacto, de acuerdo a las instrucciones de circular sobre valorización de esta Superintendencia, a la fecha de cierre del mes a que se refiere la información, expresado en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "valor_de_mercado_a_la_fecha_de_informacion", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el monto del valor de mercado, del activo subyacente del pacto, a la fecha de información.", contable: "No aplica" },
      { name: "tsa", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar si el instrumento está incluido en el Test de Suficiencia de Activos para el periodo informado, de acuerdo a la siguiente codificación: SI: el instrumento es utilizado para el análisis del Test de Suficiencia de Activos NO: el instrumento no es utilizado para el análisis del.", contable: "No aplica" },
      { name: "metod_clasif_valo", type: "VARCHAR", role: "Atributo", significado: "Corresponde informar la clasificación dada al instrumento en los.", contable: "No aplica" }
    ]
  },
  {
    id: "seguros_control_inversiones",
    name: "seguros.control_inversiones",
    viewName: "seguros_control_inversiones",
    sector: "seguros",
    sectorLabel: "Seguros de Vida y Generales (CMF)",
    norma: "Circular CMF 1835",
    corte: "Desde 2016-11",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, cada mes validado antes de publicarse",
    ultimaActualizacion: "2026-09-28",
    registros: "Un archivo por mes",
    descripcion: "Información de control que cada compañía envía con su cartera: totales por tipo de inversión (valor final, representativas y no representativas de reservas, etc.).",
    origen: "CMF — Cartera de inversiones de las compañías de seguros (Circular 1835), archivos mensuales de vida (CSVID) y generales (CSGEN) en cmfchile.cl, leídos con la ficha técnica oficial (formato vigente hasta 2024-11 y formato desde 2024-12).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Mes de la cartera informada (AAAA-MM).", contable: "No aplica" },
      { name: "sector", type: "VARCHAR", role: "Atributo", significado: "vida (archivos CSVID) o generales (CSGEN).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía de seguros, con dígito verificador (une con seguros.lista_entidades).", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Nombre de la compañía tal como aparece en el encabezado del archivo del mes.", contable: "No aplica" },
      { name: "tipo_de_inversion", type: "VARCHAR", role: "Atributo", significado: "Corresponderá a la letra con la cual se clasifica la inversión. Se informará de acuerdo a la codificación definida en SEIL, Codificación S.V.S., Tipo de Inversión.", contable: "No aplica" },
      { name: "valor_final_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tienen los instrumentos a la fecha de cierre del mes a que se refiere la información, según lo establecido en Circular de Valorización de Inversiones vigente. Este monto se deberá expresar en miles de pesos (M$). Expresado en miles de pesos.", contable: "Valor contable informado" },
      { name: "inversiones_representativas_de_rt_pr_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor de las inversiones que la Compañía considera para respaldar reservas técnicas y patrimonio de riesgo, de acuerdo a los límites señalados en el DFL N°251 expresados en miles de pesos (M$). Expresado en miles de pesos.", contable: "No aplica" },
      { name: "inversiones_no_representativas_de_rt_pr_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor de las inversiones que la Compañía no considera para respaldar reservas técnicas y patrimonio de riesgo, expresados en miles de pesos (M$). Al respecto, sólo para los derivados pasivos la información debe presentarse con signo negativo. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "total_costo_amortizado_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tienen los instrumentos a la fecha del cierre del mes a que se refiere la información, y que están clasificados como “CA” (Costo Amortizado) en el campo METOD_CLASIF_VALORIZ_EEFF de los archivos anteriores de esta circular. Expresado en miles de pesos.", contable: "Costo amortizado" },
      { name: "total_valor_razonable_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tienen los instrumentos a la fecha del cierre del mes a que se refiere la información, y que están clasificados como “VR” (Valor Razonable) en el campo METOD_CLASIF_VALORIZ_EEFF de los archivos anteriores de esta circular. Este monto deberá expresarse en miles de pesos (M$). Expresado en miles de pesos.", contable: "Valor razonable" },
      { name: "total_efectivo_equivalente_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tienen los instrumentos a la fecha del cierre del mes a que se refiere la información, y que están clasificados como “EE” (Efectivo Equivalente) en el campo METOD_CLASIF_VALORIZ_EEFF de los archivos anteriores de esta circular. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "total_instrumento_s_cui_apv_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tienen los instrumentos a la fecha del cierre del mes a que se refiere la información, y que NO están clasificados como “VIDA” o “GRAL” en el campo ACTIVO_RESPALDA_RESERVA_VALOR_DEL_FONDO de los archivos anteriores de esta circular. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "total_inst_otras_clasif_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde al valor que tienen los instrumentos a la fecha del cierre del mes a que se refiere la información, y que están clasificados como “OTRCLA” (Otra Clasificación dentro de los Estados de Situación Financiera) en el campo METOD_CLASIF_VALORIZ_EEFF de los archivos anteriores de esta. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "total_soc_filiales_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el monto que tiene invertido a la fecha del cierre del mes a que se refiere la información y que corresponde a las Participaciones y Acciones en Sociedades Filiales. Adicionalmente, se deberá incluir en este campo el monto final invertido en acciones de Sociedades Filiales. Expresado en miles de pesos.", contable: "No aplica" },
      { name: "total_coligadas_m_clp", type: "BIGINT", role: "Métrica", significado: "Corresponde informar el monto que tiene invertido a la fecha del cierre del mes a que se refiere la información y que corresponde a las Participaciones y Acciones en Sociedades Coligadas. Adicionalmente, se deberá incluir en este campo el monto final invertido en acciones de Sociedades Coligadas. Expresado en miles de pesos.", contable: "No aplica" }
    ]
  },
  // FONDOS MUTUOS · Circular 1333 (generado desde ffmm/scripts/actualizar_carteras.py)
  {"id": "ffmm_lista_entidades", "name": "ffmm.lista_entidades", "viewName": "ffmm_lista_entidades", "sector": "ffmm", "sectorLabel": "Fondos Mutuos (CMF)", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Fondos mutuos que reportan cartera a la CMF: RUN, nombre vigente, primer y último mes informado y si reportó el último mes publicado (un fondo nuevo aparece aquí el mes en que informa por primera vez).", "corte": "Desde 2001-01", "registros": "Una fila por fondo", "columnas": [{"name": "run_fondo", "type": "VARCHAR", "role": "PK", "significado": "RUN del fondo mutuo.", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en su último mes informado.", "contable": "No aplica"}, {"name": "primer_periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Primer mes en que el fondo informa cartera.", "contable": "No aplica"}, {"name": "ultimo_periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Último mes en que informa cartera.", "contable": "No aplica"}, {"name": "meses_reportados", "type": "BIGINT", "role": "Métrica", "significado": "Meses publicados en que aparece.", "contable": "No aplica"}, {"name": "reporta_ultimo_mes", "type": "BOOLEAN", "role": "Atributo", "significado": "Verdadero si aparece en el último mes publicado.", "contable": "No aplica"}]},
  {"id": "agf_balance", "name": "agf.balance", "viewName": "agf_balance", "sector": "agf", "sectorLabel": "Administradoras Generales de Fondos (CMF)", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de situación financiera de cada administradora general de fondos, cuenta por cuenta, al cierre de cada trimestre. Una cuenta puede aparecer más de una vez en el mismo estado (columna repeticion), así que no sume por nombre de cuenta sin mirar repeticion y estado_financiero.", "corte": "2010-06–2026-06", "registros": "Serie IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral, que vuelve a informar la ganancia del ejercicio).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la fuente la repite. Sumar sin filtrar repeticion = 1 cuenta dos veces la misma cifra.", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}], "cobertura": "Cobertura 2026-06: informan 53 de las 72 entidades del catálogo del sector. Dejaron de informar: TAURUS ADMINISTRADORA GENERAL DE FONDOS S.A. (último 2025-09); AZIMUT INVESTMENTS S.A. ADMINISTRADORA GENERAL DE FONDOS (último 2025-09); SARTOR ADMINISTRADORA GENERAL DE FONDOS S.A. (último 2024-12). Sin dato en 2026-06: 19 entidades (EQUITAS MANAGEMENT PARTNERS S.A. ADMINISTRADORA GENERAL DE FONDOS, AURUS CAPITAL S.A. ADMINISTRADORA GENERAL DE FONDOS, AZIMUT INVESTMENTS S.A. ADMINISTRADORA GENERAL DE FONDOS…)."},
  {"id": "agf_resultados", "name": "agf.resultados", "viewName": "agf_resultados", "sector": "agf", "sectorLabel": "Administradoras Generales de Fondos (CMF)", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de resultados y resultado integral de cada administradora general de fondos, acumulado del ejercicio a cada trimestre. El resultado integral (ERI) repite la línea «Ganancia (pérdida)» y un mismo estado la trae dos veces: para sumar utilidades sin triplicarlas filtre estado_financiero IN ('ERFG', 'ERNG') y repeticion = 1.", "corte": "2010-06–2026-06", "registros": "Serie IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral, que vuelve a informar la ganancia del ejercicio).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la fuente la repite. Sumar sin filtrar repeticion = 1 cuenta dos veces la misma cifra.", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}], "cobertura": "Cobertura 2026-06: informan 53 de las 72 entidades del catálogo del sector. Dejaron de informar: TAURUS ADMINISTRADORA GENERAL DE FONDOS S.A. (último 2025-09); AZIMUT INVESTMENTS S.A. ADMINISTRADORA GENERAL DE FONDOS (último 2025-09); SARTOR ADMINISTRADORA GENERAL DE FONDOS S.A. (último 2024-12). Sin dato en 2026-06: 19 entidades (EQUITAS MANAGEMENT PARTNERS S.A. ADMINISTRADORA GENERAL DE FONDOS, AURUS CAPITAL S.A. ADMINISTRADORA GENERAL DE FONDOS, AZIMUT INVESTMENTS S.A. ADMINISTRADORA GENERAL DE FONDOS…)."},
  {"id": "securitizadoras_balance", "name": "securitizadoras.balance", "viewName": "securitizadoras_balance", "sector": "securitizadoras", "sectorLabel": "Sociedades Securitizadoras (CMF)", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de situación financiera de cada sociedad securitizadora, cuenta por cuenta, al cierre de cada trimestre. Una cuenta puede aparecer más de una vez en el mismo estado (columna repeticion), así que no sume por nombre de cuenta sin mirar repeticion y estado_financiero.", "corte": "2009-12–2026-06", "registros": "Serie IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral, que vuelve a informar la ganancia del ejercicio).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la fuente la repite. Sumar sin filtrar repeticion = 1 cuenta dos veces la misma cifra.", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}], "cobertura": "Cobertura 2026-06: informan 9 de las 16 entidades del catálogo del sector. Dejaron de informar: FINTESA SECURITIZADORA S.A. (último 2024-12). Sin dato en 2026-06: 7 entidades (FINTESA SECURITIZADORA S.A., CB SECURITIZADORA S.A., SECURITIZADORA LA CONSTRUCCION S.A.…)."},
  {"id": "securitizadoras_resultados", "name": "securitizadoras.resultados", "viewName": "securitizadoras_resultados", "sector": "securitizadoras", "sectorLabel": "Sociedades Securitizadoras (CMF)", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de resultados y resultado integral de cada sociedad securitizadora, acumulado del ejercicio a cada trimestre. El resultado integral (ERI) repite la línea «Ganancia (pérdida)» y un mismo estado la trae dos veces: para sumar utilidades sin triplicarlas filtre estado_financiero IN ('ERFG', 'ERNG') y repeticion = 1.", "corte": "2009-12–2026-06", "registros": "Serie IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral, que vuelve a informar la ganancia del ejercicio).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la fuente la repite. Sumar sin filtrar repeticion = 1 cuenta dos veces la misma cifra.", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}], "cobertura": "Cobertura 2026-06: informan 9 de las 16 entidades del catálogo del sector. Dejaron de informar: FINTESA SECURITIZADORA S.A. (último 2024-12). Sin dato en 2026-06: 7 entidades (FINTESA SECURITIZADORA S.A., CB SECURITIZADORA S.A., SECURITIZADORA LA CONSTRUCCION S.A.…)."},
  {"id": "ccaf_balance", "name": "ccaf.balance", "viewName": "ccaf_balance", "sector": "cajas_compensacion", "sectorLabel": "Cajas de Compensación (CCAF / SUSESO)", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de situación financiera de cada caja de compensación que envía estados financieros a la CMF, cuenta por cuenta, al cierre de cada trimestre. Una cuenta puede aparecer más de una vez en el mismo estado (columna repeticion), así que no sume por nombre de cuenta sin mirar repeticion y estado_financiero.", "corte": "2010-06–2026-06", "registros": "Serie IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral, que vuelve a informar la ganancia del ejercicio).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la fuente la repite. Sumar sin filtrar repeticion = 1 cuenta dos veces la misma cifra.", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}], "cobertura": "Cobertura 2026-06: informan 4 de las 6 entidades del catálogo del sector. Sin dato en 2026-06: 2 entidades (CAJA DE COMPENSACION DE ASIGNACION FAMILIAR JAVIERA CARRERA, CAJA DE COMPENSACION DE ASIGNACION FAMILIAR GABRIELA MISTRAL…)."},
  {"id": "ccaf_resultados", "name": "ccaf.resultados", "viewName": "ccaf_resultados", "sector": "cajas_compensacion", "sectorLabel": "Cajas de Compensación (CCAF / SUSESO)", "norma": "IFRS · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estados financieros bajo estándar IFRS (archivo TXT trimestral con todas las sociedades que envían estados financieros XBRL), https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php", "descripcion": "Estado de resultados y resultado integral de cada caja de compensación que envía estados financieros a la CMF, acumulado del ejercicio a cada trimestre. El resultado integral (ERI) repite la línea «Ganancia (pérdida)» y un mismo estado la trae dos veces: para sumar utilidades sin triplicarlas filtre estado_financiero IN ('ERFG', 'ERNG') y repeticion = 1.", "corte": "2010-06–2026-06", "registros": "Serie IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, cierre del trimestre).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT de la sociedad sin dígito verificador (une con la lista de entidades del sector).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre informado por la sociedad en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_balance", "type": "VARCHAR", "role": "Atributo", "significado": "individual o consolidado.", "contable": "No aplica"}, {"name": "moneda", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de presentación (CLP o USD). Los montos no se convierten.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Código CMF del estado: ESF C/NC (corriente/no corriente), ESF OL (orden de liquidez), ERFG (resultados por función), ERNG (por naturaleza), ERI (resultado integral, que vuelve a informar la ganancia del ejercicio).", "contable": "No aplica"}, {"name": "orden", "type": "INTEGER", "role": "Atributo", "significado": "Posición de la cuenta dentro del estado, tal como viene en el archivo.", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta según la taxonomía IFRS de la CMF.", "contable": "No aplica"}, {"name": "valor", "type": "BIGINT", "role": "Métrica", "significado": "Monto en pesos (o dólares si moneda = USD), sin decimales. Los resultados son acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "valor_no_numerico", "type": "VARCHAR", "role": "Atributo", "significado": "Texto original cuando la CMF publica un valor que no es un número entero (valor queda nulo).", "contable": "No aplica"}, {"name": "repeticion", "type": "SMALLINT", "role": "Atributo", "significado": "1 la primera vez que aparece la cuenta en el estado; 2 o más si la fuente la repite. Sumar sin filtrar repeticion = 1 cuenta dos veces la misma cifra.", "contable": "No aplica"}, {"name": "taxonomia", "type": "VARCHAR", "role": "Atributo", "significado": "Taxonomía XBRL declarada en el archivo.", "contable": "No aplica"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector; false si fue reconocida por su nombre (entidad nueva).", "contable": "No aplica"}], "cobertura": "Cobertura 2026-06: informan 4 de las 6 entidades del catálogo del sector. Sin dato en 2026-06: 2 entidades (CAJA DE COMPENSACION DE ASIGNACION FAMILIAR JAVIERA CARRERA, CAJA DE COMPENSACION DE ASIGNACION FAMILIAR GABRIELA MISTRAL…)."},
  {"id": "corredoras_bolsa_balance", "name": "corredoras.balance", "viewName": "corredoras_bolsa_balance", "sector": "corredoras_bolsa", "sectorLabel": "Corredoras de Bolsa (CMF)", "norma": "FECU IFRS intermediarios · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estadísticas de estados financieros IFRS de intermediarios de valores (corredores de bolsa y agentes de valores), https://www.cmfchile.cl/institucional/estadisticas/merc_valores/intermediarios_fecu_ifrs/", "descripcion": "Estado de situación financiera de corredores de bolsa y agentes de valores, cuenta FECU por cuenta, al cierre de cada trimestre.", "corte": "2010-12–2026-06", "registros": "FECU IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT sin dígito verificador (une con corredoras.lista_entidades).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del intermediario en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_intermediario", "type": "VARCHAR", "role": "Atributo", "significado": "corredor de bolsa o agente de valores.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Estado de situación financiera, Estado de resultados u Otros resultados integrales.", "contable": "No aplica"}, {"name": "seccion", "type": "VARCHAR", "role": "Atributo", "significado": "Agrupación de la cuenta en el informe (Activos, Pasivos, Resultado por intermediación, etc.).", "contable": "No aplica"}, {"name": "codigo_fecu", "type": "VARCHAR", "role": "PK", "significado": "Código de la cuenta en el plan FECU IFRS de intermediarios (10.00.00 total activos, 21.00.00 total pasivos, 22.00.00 patrimonio, 30.00.00 resultado del ejercicio).", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta.", "contable": "No aplica"}, {"name": "nivel", "type": "TINYINT", "role": "Atributo", "significado": "Nivel jerárquico de la cuenta en el informe (1 = cuenta principal).", "contable": "No aplica"}, {"name": "valor_miles_clp", "type": "BIGINT", "role": "Métrica", "significado": "Monto en miles de pesos, moneda corriente del cierre. Resultados acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector.", "contable": "No aplica"}]},
  {"id": "corredoras_bolsa_resultados", "name": "corredoras.resultados", "viewName": "corredoras_bolsa_resultados", "sector": "corredoras_bolsa", "sectorLabel": "Corredoras de Bolsa (CMF)", "norma": "FECU IFRS intermediarios · CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, trimestres ya publicados no se repiten", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Estadísticas de estados financieros IFRS de intermediarios de valores (corredores de bolsa y agentes de valores), https://www.cmfchile.cl/institucional/estadisticas/merc_valores/intermediarios_fecu_ifrs/", "descripcion": "Estado de resultados y otros resultados integrales de corredores de bolsa y agentes de valores, acumulados del ejercicio.", "corte": "2010-12–2026-06", "registros": "FECU IFRS", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM).", "contable": "No aplica"}, {"name": "rut", "type": "VARCHAR", "role": "FK", "significado": "RUT sin dígito verificador (une con corredoras.lista_entidades).", "contable": "No aplica"}, {"name": "rut_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUT con dígito verificador.", "contable": "No aplica"}, {"name": "razon_social", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del intermediario en el archivo del trimestre.", "contable": "No aplica"}, {"name": "tipo_intermediario", "type": "VARCHAR", "role": "Atributo", "significado": "corredor de bolsa o agente de valores.", "contable": "No aplica"}, {"name": "estado_financiero", "type": "VARCHAR", "role": "Atributo", "significado": "Estado de situación financiera, Estado de resultados u Otros resultados integrales.", "contable": "No aplica"}, {"name": "seccion", "type": "VARCHAR", "role": "Atributo", "significado": "Agrupación de la cuenta en el informe (Activos, Pasivos, Resultado por intermediación, etc.).", "contable": "No aplica"}, {"name": "codigo_fecu", "type": "VARCHAR", "role": "PK", "significado": "Código de la cuenta en el plan FECU IFRS de intermediarios (10.00.00 total activos, 21.00.00 total pasivos, 22.00.00 patrimonio, 30.00.00 resultado del ejercicio).", "contable": "No aplica"}, {"name": "cuenta", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la cuenta.", "contable": "No aplica"}, {"name": "nivel", "type": "TINYINT", "role": "Atributo", "significado": "Nivel jerárquico de la cuenta en el informe (1 = cuenta principal).", "contable": "No aplica"}, {"name": "valor_miles_clp", "type": "BIGINT", "role": "Métrica", "significado": "Monto en miles de pesos, moneda corriente del cierre. Resultados acumulados del ejercicio.", "contable": "Valor contable"}, {"name": "en_lista_entidades", "type": "BOOLEAN", "role": "Atributo", "significado": "true si el RUT está en la lista de entidades del sector.", "contable": "No aplica"}]},
  {"id": "fi_lista_entidades", "name": "fi.lista_entidades", "viewName": "fi_lista_entidades", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Registro CMF de fondos de inversión (rescatables y no rescatables, vigentes y no vigentes) con administradora, moneda funcional y primer y último trimestre con cartera publicada.", "registros": "Una fila por fondo", "columnas": [{"name": "run_fondo", "type": "VARCHAR", "role": "PK", "significado": "RUN del fondo (sin dígito verificador).", "contable": "No aplica"}, {"name": "rut_fondo_dv", "type": "VARCHAR", "role": "Atributo", "significado": "RUN con dígito verificador.", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el registro CMF.", "contable": "No aplica"}, {"name": "administradora", "type": "VARCHAR", "role": "Atributo", "significado": "Administradora general de fondos (une por nombre con agf.lista_entidades).", "contable": "No aplica"}, {"name": "tipo_entidad", "type": "VARCHAR", "role": "Atributo", "significado": "FIRES fondo de inversión rescatable; FINRE no rescatable.", "contable": "No aplica"}, {"name": "estado_vigencia", "type": "VARCHAR", "role": "Atributo", "significado": "Vigente / No Vigente según el registro CMF.", "contable": "No aplica"}, {"name": "moneda_funcional", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda funcional del fondo (en la que se expresan sus montos _miles_mf), leída del informe de pactos.", "contable": "No aplica"}, {"name": "primer_periodo_cartera", "type": "VARCHAR", "role": "Fecha", "significado": "Primer trimestre con cartera publicada (desde 2020-03).", "contable": "No aplica"}, {"name": "ultimo_periodo_cartera", "type": "VARCHAR", "role": "Fecha", "significado": "Último trimestre con cartera publicada.", "contable": "No aplica"}, {"name": "trimestres_con_cartera", "type": "BIGINT", "role": "Métrica", "significado": "Trimestres con cartera publicada.", "contable": "No aplica"}, {"name": "reporta_ultimo_periodo", "type": "BOOLEAN", "role": "Atributo", "significado": "Verdadero si el fondo tiene cartera en el último trimestre publicado.", "contable": "No aplica"}]},
  {"id": "fi_cartera_nacional", "name": "fi.cartera_nacional", "viewName": "fi_cartera_nacional", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Inversiones en instrumentos de emisores nacionales, instrumento por instrumento, al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Trimestral", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD; vacío si no aplica).", "contable": "No aplica"}, {"name": "rut_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Cuerpo del RUT del emisor (sin dígito verificador).", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "codigo_grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Código del grupo empresarial del emisor (0000 si no pertenece a uno).", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_valor_par_precio", "type": "DOUBLE", "role": "Métrica", "significado": "TIR, % del valor par o precio usado para valorizar, según el código de valorización.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_cartera_extranjera", "name": "fi.cartera_extranjera", "viewName": "fi_cartera_extranjera", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Inversiones en instrumentos de emisores extranjeros al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Trimestral", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "isin", "type": "VARCHAR", "role": "Atributo", "significado": "Código ISIN o CUSIP del instrumento (vacío si no aplica).", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD; vacío si no aplica).", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor (vacío si no aplica).", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del grupo empresarial del emisor.", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_valor_par_precio", "type": "DOUBLE", "role": "Métrica", "significado": "TIR, % del valor par o precio usado para valorizar, según el código de valorización.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_metodo_participacion", "name": "fi.metodo_participacion", "viewName": "fi_metodo_participacion", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Inversiones valorizadas por el método de la participación (sociedades filiales y coligadas). Montos en miles de la moneda funcional del fondo.", "registros": "Trimestral", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "isin", "type": "VARCHAR", "role": "Atributo", "significado": "Código ISIN o CUSIP del instrumento (vacío si no aplica).", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor (vacío si no aplica).", "contable": "No aplica"}, {"name": "rut_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Cuerpo del RUT del emisor (sin dígito verificador).", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "patrimonio_emisor_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Patrimonio de la sociedad participada, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "valor_cierre_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor contable al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "provision_deterioro_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Provisión por deterioro, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "plusvalia_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Plusvalía de la inversión, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_bienes_raices", "name": "fi.bienes_raices", "viewName": "fi_bienes_raices", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Bienes raíces nacionales y extranjeros de los fondos. Montos en miles de la moneda funcional del fondo. Sin datos publicados por la fuente: ningún fondo de inversión ha informado cartera de bienes raíces a la CMF (2020-03 → 2026-06); la tabla se completa sola cuando la fuente publique.", "registros": "Sin datos", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "domicilio", "type": "VARCHAR", "role": "Atributo", "significado": "Dirección del inmueble.", "contable": "No aplica"}, {"name": "comuna", "type": "VARCHAR", "role": "Atributo", "significado": "Comuna del inmueble.", "contable": "No aplica"}, {"name": "ciudad", "type": "VARCHAR", "role": "Atributo", "significado": "Ciudad del inmueble.", "contable": "No aplica"}, {"name": "region", "type": "VARCHAR", "role": "Atributo", "significado": "Región del inmueble.", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país.", "contable": "No aplica"}, {"name": "tipo_bien_raiz", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de bien raíz según la CMF.", "contable": "No aplica"}, {"name": "pct_comunidad", "type": "DOUBLE", "role": "Métrica", "significado": "Porcentaje de propiedad cuando el inmueble está en comunidad.", "contable": "No aplica"}, {"name": "destino", "type": "VARCHAR", "role": "Atributo", "significado": "Destino o uso del inmueble.", "contable": "No aplica"}, {"name": "tipo_renta", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de renta que genera.", "contable": "No aplica"}, {"name": "prohibiciones_garantias", "type": "VARCHAR", "role": "Atributo", "significado": "Prohibiciones o garantías que pesan sobre el inmueble.", "contable": "No aplica"}, {"name": "valor_cierre_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor contable al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "ajustes_prohibiciones_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Ajustes y prohibiciones, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_futuros", "name": "fi.futuros_forwards", "viewName": "fi_futuros", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Contratos de futuro, forward y swap vigentes al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Trimestral", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD; vacío si no aplica).", "contable": "No aplica"}, {"name": "unidad_cotizacion", "type": "VARCHAR", "role": "Atributo", "significado": "Unidad de cotización del contrato.", "contable": "No aplica"}, {"name": "fecha_inicio", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de inicio del contrato (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la contraparte.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país.", "contable": "No aplica"}, {"name": "posicion", "type": "VARCHAR", "role": "Atributo", "significado": "Posición: compra o venta.", "contable": "No aplica"}, {"name": "unidades_nominales", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales totales del contrato.", "contable": "No aplica"}, {"name": "precio_futuro", "type": "DOUBLE", "role": "Métrica", "significado": "Precio futuro pactado.", "contable": "No aplica"}, {"name": "monto_comprometido_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Monto comprometido, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "valor_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado del contrato, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}]},
  {"id": "fi_opciones", "name": "fi.opciones", "viewName": "fi_opciones", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "Desde 2020-03", "descripcion": "Contratos de opciones vigentes al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Trimestral", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "clasificacion_esf", "type": "VARCHAR", "role": "Atributo", "significado": "Clasificación del instrumento en el estado de situación financiera del fondo.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD; vacío si no aplica).", "contable": "No aplica"}, {"name": "forma_ejercicio", "type": "VARCHAR", "role": "Atributo", "significado": "Forma de ejercicio: americana o europea.", "contable": "No aplica"}, {"name": "fecha_inicio", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de inicio del contrato (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (AAAA-MM-DD; vacío si no aplica).", "contable": "No aplica"}, {"name": "contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la contraparte.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país.", "contable": "No aplica"}, {"name": "tipo_opcion", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de opción: compra (call) o venta (put).", "contable": "No aplica"}, {"name": "valor_mercado_unitario_prima", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado unitario de la prima.", "contable": "No aplica"}, {"name": "numero_contratos", "type": "DOUBLE", "role": "Métrica", "significado": "Número de contratos.", "contable": "No aplica"}, {"name": "precio_ejercicio", "type": "DOUBLE", "role": "Métrica", "significado": "Precio de ejercicio.", "contable": "No aplica"}, {"name": "valor_mercado_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado del activo objeto.", "contable": "No aplica"}, {"name": "unidades_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades del activo objeto.", "contable": "No aplica"}, {"name": "inversion_primas_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas, en miles de la moneda funcional del fondo.", "contable": "No aplica"}, {"name": "valorizacion_precio_ejercicio_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización a precio de ejercicio, en miles de la moneda funcional.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización de mercado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "pct_primas_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "fi_pactos", "name": "fi.pactos", "viewName": "fi_pactos", "sector": "fi", "sectorLabel": "Fondos de Inversión (CMF)", "norma": "IFRS · informes de cartera CMF", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada trimestre validado contra los totales CMF antes de publicarse", "ultimaActualizacion": "2026-10-07", "origen": "CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos (consulta.php, FINRE y FIRES).", "corte": "2012-03 a 2026-06 (barrido desde 2008-03)", "descripcion": "Operaciones de venta con compromiso de retrocompra (VRC) y de compra con compromiso de retroventa (CRV) vigentes al cierre de cada trimestre. Montos en miles de la moneda funcional del fondo.", "registros": "Trimestral", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Trimestre informado (AAAA-MM, mes de cierre: 03, 06, 09 o 12).", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo de inversión (une con fi.lista_entidades).", "contable": "No aplica"}, {"name": "tipo_operacion", "type": "VARCHAR", "role": "Atributo", "significado": "VRC venta con compromiso de retrocompra; CRV compra con compromiso de retroventa.", "contable": "No aplica"}, {"name": "fecha_inicio", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de inicio del contrato (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "fecha_termino", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de término del pacto (AAAA-MM-DD).", "contable": "No aplica"}, {"name": "contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre de la contraparte (grafía canónica del padrón CMF cuando su RUT está en el padrón).", "contable": "No aplica"}, {"name": "rut_contraparte", "type": "VARCHAR", "role": "Atributo", "significado": "Cuerpo del RUT de la contraparte (sin dígito verificador).", "contable": "No aplica"}, {"name": "valor_inicial_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor inicial del pacto, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_origen", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de origen del pacto.", "contable": "No aplica"}, {"name": "tasa_pacto_pct", "type": "DOUBLE", "role": "Métrica", "significado": "Tasa del pacto (%).", "contable": "No aplica"}, {"name": "valor_final_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor final del pacto, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_cierre_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización del pacto al cierre, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "isin", "type": "VARCHAR", "role": "Atributo", "significado": "Código ISIN o CUSIP del instrumento (vacío si no aplica).", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD; vacío si no aplica).", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor (vacío si no aplica).", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "valor_mercado_miles_moneda", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado del instrumento en compromiso, en miles de la moneda del informe.", "contable": "No aplica"}]},
  {"id": "ffmm_cartera_nacional", "name": "ffmm.cartera_nacional", "viewName": "ffmm_cartera_nacional", "sector": "ffmm", "sectorLabel": "Fondos Mutuos (CMF)", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Inversiones de cada fondo en instrumentos de emisores nacionales, instrumento por instrumento, al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2022-01", "registros": "Mensual", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "rut_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Cuerpo del RUT del emisor (sin dígito verificador).", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "codigo_grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Código del grupo empresarial del emisor (0000 si no pertenece a uno).", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_pct", "type": "DOUBLE", "role": "Métrica", "significado": "TIR de valorización (%), cuando el código de valorización es 1.", "contable": "No aplica"}, {"name": "valor_par_pct", "type": "DOUBLE", "role": "Métrica", "significado": "Porcentaje del valor par, cuando el código de valorización es 2.", "contable": "No aplica"}, {"name": "valor_relevante", "type": "DOUBLE", "role": "Métrica", "significado": "Valor relevante (precio) usado, cuando el código de valorización es 3.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo, sin decimales.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "ffmm_cartera_extranjera", "name": "ffmm.cartera_extranjera", "viewName": "ffmm_cartera_extranjera", "sector": "ffmm", "sectorLabel": "Fondos Mutuos (CMF)", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Inversiones de cada fondo en instrumentos de emisores extranjeros al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2001-01", "registros": "Mensual", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "nombre_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del emisor en la bolsa extranjera.", "contable": "No aplica"}, {"name": "pais_emisor", "type": "VARCHAR", "role": "Atributo", "significado": "Código del país del emisor.", "contable": "No aplica"}, {"name": "tipo_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "Tipo de instrumento según la codificación SEIL de la CMF.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (vacío si no aplica).", "contable": "No aplica"}, {"name": "situacion_instrumento", "type": "VARCHAR", "role": "Atributo", "significado": "1 sin restricción; 2 con compromiso (pacto); 3 en garantía de derivados o venta corta; 4 otra restricción; 5 préstamo para venta corta.", "contable": "No aplica"}, {"name": "clasificacion_riesgo", "type": "VARCHAR", "role": "Atributo", "significado": "Menor categoría de riesgo (AAA … E, N-1 … N-5; NA si no aplica).", "contable": "No aplica"}, {"name": "grupo_empresarial", "type": "VARCHAR", "role": "Atributo", "significado": "Grupo empresarial del emisor (NA si no aplica).", "contable": "No aplica"}, {"name": "cantidad_unidades", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales (deuda) o número de unidades (capitalización).", "contable": "No aplica"}, {"name": "tipo_unidades", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda o unidad de reajuste de la cantidad de unidades.", "contable": "No aplica"}, {"name": "tir_pct", "type": "DOUBLE", "role": "Métrica", "significado": "TIR de valorización (%), cuando el código de valorización es 1.", "contable": "No aplica"}, {"name": "valor_par_pct", "type": "DOUBLE", "role": "Métrica", "significado": "Porcentaje del valor par, cuando el código de valorización es 2.", "contable": "No aplica"}, {"name": "valor_relevante", "type": "DOUBLE", "role": "Métrica", "significado": "Valor relevante (precio) usado, cuando el código de valorización es 3.", "contable": "No aplica"}, {"name": "codigo_valorizacion", "type": "VARCHAR", "role": "Atributo", "significado": "1 TIR; 2 % del valor par; 3 valor relevante.", "contable": "No aplica"}, {"name": "base_tasa_dias", "type": "DOUBLE", "role": "Atributo", "significado": "Días que cubre la tasa (30, 360, 365; 0 si no aplica).", "contable": "No aplica"}, {"name": "tipo_interes", "type": "VARCHAR", "role": "Atributo", "significado": "NL nominal lineal; NC nominal compuesto; RL real lineal; RC real compuesto; NA no aplica.", "contable": "No aplica"}, {"name": "valorizacion_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valorización al cierre, en miles de la moneda funcional del fondo, sin decimales.", "contable": "Valor Razonable / MtM"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais_transaccion", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se adquirió el instrumento.", "contable": "No aplica"}, {"name": "pct_capital_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "% del capital del emisor que posee el fondo (acciones y cuotas; 0 en deuda).", "contable": "No aplica"}, {"name": "pct_activo_emisor", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del emisor.", "contable": "No aplica"}, {"name": "pct_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión como % del activo total del fondo.", "contable": "No aplica"}]},
  {"id": "ffmm_futuros", "name": "ffmm.futuros_forwards", "viewName": "ffmm_futuros", "sector": "ffmm", "sectorLabel": "Fondos Mutuos (CMF)", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Contratos de futuro y forward vigentes de cada fondo al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2001-01", "registros": "Mensual", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "unidad_cotizacion", "type": "VARCHAR", "role": "Atributo", "significado": "Unidad o moneda de cotización del contrato.", "contable": "No aplica"}, {"name": "fecha_vencimiento", "type": "VARCHAR", "role": "Fecha", "significado": "Fecha de vencimiento (vacío si no aplica).", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se suscribió el contrato.", "contable": "No aplica"}, {"name": "posicion", "type": "VARCHAR", "role": "Atributo", "significado": "C posición compradora; V posición vendedora.", "contable": "No aplica"}, {"name": "unidades_nominales", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades nominales totales comprometidas.", "contable": "No aplica"}, {"name": "precio_futuro", "type": "DOUBLE", "role": "Métrica", "significado": "Precio a futuro acordado, en la moneda de cotización.", "contable": "No aplica"}, {"name": "monto_comprometido_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor total de los contratos al precio acordado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}]},
  {"id": "ffmm_opciones", "name": "ffmm.opciones", "viewName": "ffmm_opciones", "sector": "ffmm", "sectorLabel": "Fondos Mutuos (CMF)", "norma": "Circular CMF 1333", "frescura": "Se actualiza sola 3 veces al mes", "modo": "Automático · incremental, cada mes validado antes de publicarse", "ultimaActualizacion": "2026-09-28", "origen": "CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php", "descripcion": "Contratos de opciones vigentes de cada fondo al cierre de cada mes. Montos en miles de la moneda funcional del fondo.", "corte": "Desde 2001-01", "registros": "Mensual", "columnas": [{"name": "periodo", "type": "VARCHAR", "role": "Fecha", "significado": "Mes informado (AAAA-MM), cartera al último día del mes.", "contable": "No aplica"}, {"name": "run_fondo", "type": "VARCHAR", "role": "FK", "significado": "RUN del fondo mutuo (une con ffmm.lista_entidades).", "contable": "No aplica"}, {"name": "nombre_fondo", "type": "VARCHAR", "role": "Atributo", "significado": "Nombre del fondo en el archivo del mes.", "contable": "No aplica"}, {"name": "activo_objeto", "type": "VARCHAR", "role": "Atributo", "significado": "Activo objeto del contrato.", "contable": "No aplica"}, {"name": "nemotecnico", "type": "VARCHAR", "role": "Atributo", "significado": "Nemotécnico del instrumento o contrato (en forwards, la palabra FORWARD).", "contable": "No aplica"}, {"name": "forma_ejercicio", "type": "VARCHAR", "role": "Atributo", "significado": "A americana; E europea.", "contable": "No aplica"}, {"name": "fecha_expiracion", "type": "VARCHAR", "role": "Fecha", "significado": "Último día en que la opción puede ejercerse.", "contable": "No aplica"}, {"name": "moneda_liquidacion", "type": "VARCHAR", "role": "Atributo", "significado": "Moneda de liquidación (codificación SEIL; $$ pesos, PROM dólar, UF, etc.).", "contable": "No aplica"}, {"name": "pais", "type": "VARCHAR", "role": "Atributo", "significado": "País donde se suscribió el contrato.", "contable": "No aplica"}, {"name": "tipo_opcion", "type": "VARCHAR", "role": "Atributo", "significado": "C derecho a comprar; V derecho a vender.", "contable": "No aplica"}, {"name": "valor_mercado_unitario_prima", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado unitario de la prima.", "contable": "No aplica"}, {"name": "numero_contratos", "type": "DOUBLE", "role": "Métrica", "significado": "Número de contratos de la misma serie.", "contable": "No aplica"}, {"name": "precio_ejercicio", "type": "DOUBLE", "role": "Métrica", "significado": "Precio de ejercicio.", "contable": "No aplica"}, {"name": "valor_mercado_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Precio de mercado del activo objeto.", "contable": "No aplica"}, {"name": "unidades_activo_objeto", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades del activo objeto que se pueden comprar o vender.", "contable": "No aplica"}, {"name": "inversion_primas_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_precio_ejercicio_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Unidades del activo objeto valorizadas a precio de ejercicio, en miles de la moneda funcional.", "contable": "Valor Razonable / MtM"}, {"name": "valorizacion_mercado_miles_mf", "type": "DOUBLE", "role": "Métrica", "significado": "Valor de mercado, en miles de la moneda funcional del fondo.", "contable": "Valor Razonable / MtM"}, {"name": "pct_primas_activo_fondo", "type": "DOUBLE", "role": "Métrica", "significado": "Inversión en primas como % del activo total del fondo.", "contable": "No aplica"}]},
  // BEGIN AUTO FI EEFF DICTIONARY
{
  id: "fi_balance",
  name: "fi.balance",
  viewName: "fi_balance",
  sector: "fi",
  sectorLabel: "Fondos de Inversión (CMF)",
  norma: "IFRS · XML CMF FIEF (Circular 1998)",
  corte: "2022-03 a 2026-06 · 16 cierres publicados",
  frecuencia: "Trimestral",
  frescura: "Se actualiza sola 3 veces al mes",
  modo: "Automático · incremental; identidades y cotejo antes de publicar",
  ultimaActualizacion: "2026-10-02",
  registros: "Trimestral · contextos separados",
  origen: "CMF — XML IFRS FIEF (Circular 1998) de cada fondo, enlazado en entidad.php?tipoentidad=FIRES|FINRE&pestania=29. Cotejo con las tablas de su ficha; no es una auditoría independiente del PDF firmado.",
  descripcion: "Estado de situación financiera de fondos de inversión FIRES/FINRE, cuenta por cuenta (42 líneas por contexto). TotalPasivo de la fuente incluye patrimonio: el pasivo exigible es TotalPasivoCorriente + TotalPasivoNoCorriente. Miles de la moneda de presentación, sin conversión. Solo se publican contextos completos y que cuadran. Los contextos adicionales rechazados/ausentes se declaran en el manifiesto, no se rellenan con ceros.",
  advertencia: "El archivo puede traer varios contextos para la misma cuenta. Elegir PeriodoActual para el saldo/acumulado actual; no sumar contextos ni monedas. sin_columna no significa cotejado contra HTML. Las exclusiones y huecos están en fi_eeff_control.json y manifest.json.",
  columnas: [
    {
      name: "periodo",
      type: "VARCHAR",
      role: "PK",
      significado: "Cierre del archivo AAAA-MM. En comparativos no es la fecha de la cifra: usar fecha_fin_contexto.",
      contable: "No aplica"
    },
    {
      name: "run_fondo",
      type: "VARCHAR",
      role: "FK",
      significado: "RUN del fondo, sin DV; une directamente con fi.lista_entidades.",
      contable: "No aplica"
    },
    {
      name: "run_fondo_dv",
      type: "VARCHAR",
      role: "Atributo",
      significado: "RUN con DV módulo 11. El DV recibido se conserva separado.",
      contable: "No aplica"
    },
    {
      name: "dv_fondo_fuente",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "Dígito verificador literal del XML; las discrepancias quedan como aviso.",
      contable: "No aplica"
    },
    {
      name: "nombre_fondo",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Nombre reportado en el XML; puede ser abreviado y diferir del maestro.",
      contable: "No aplica"
    },
    {
      name: "tipo_entidad",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "FIRES rescatable / FINRE no rescatable, según registro CMF.",
      contable: "No aplica"
    },
    {
      name: "rut_agf",
      type: "VARCHAR",
      role: "FK",
      significado: "RUT de la administradora reportada, sin DV; une con agf.lista_entidades.",
      contable: "No aplica"
    },
    {
      name: "razon_social_agf",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Nombre de administradora declarado en este envío.",
      contable: "No aplica"
    },
    {
      name: "moneda",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Moneda de presentación: CLP, USD, EUR o COP; no sumar monedas distintas.",
      contable: "No aplica"
    },
    {
      name: "moneda_cmf",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "Código CMF literal ($$ pesos, PROM dólar, EUR euro, COP peso colombiano).",
      contable: "No aplica"
    },
    {
      name: "contexto",
      type: "VARCHAR",
      role: "PK",
      significado: "Contexto original. PeriodoActual = saldo/acumulado actual; PeriodoAnualAnterior = balance al diciembre anterior; PeriodoAnterior = acumulado comparable; TrimestreActual/TrimestreAnterior = solo el trimestre. SaldoInicialTerceraColumna = apertura IFRS cuando se informa. Filtrar el contexto antes de agregar.",
      contable: "No aplica"
    },
    {
      name: "fecha_inicio_contexto",
      type: "VARCHAR",
      role: "Fecha",
      significado: "Inicio declarado del contexto. Para el saldo de apertura, la única fecha del XML.",
      contable: "No aplica"
    },
    {
      name: "fecha_fin_contexto",
      type: "VARCHAR",
      role: "Fecha",
      significado: "Corte/fin declarado de las cifras; en apertura es el mismo instante de FechaInicio.",
      contable: "No aplica"
    },
    {
      name: "tipo_periodo",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "saldo, acumulado o trimestre; evita confundir stocks y flujos.",
      contable: "No aplica"
    },
    {
      name: "seccion",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Rubro del estado: corriente/no corriente, patrimonio, ingresos, gastos u otros integrales.",
      contable: "No aplica"
    },
    {
      name: "tipo_linea",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "detalle o total. No sumar detalles con sus totales.",
      contable: "No aplica"
    },
    {
      name: "orden",
      type: "INTEGER",
      role: "Atributo",
      significado: "Orden de presentación de la cuenta en la ficha CMF, dentro de cada tabla/contexto.",
      contable: "No aplica"
    },
    {
      name: "codigo_cuenta",
      type: "VARCHAR",
      role: "PK",
      significado: "Código FIEF literal. La clave de fila es periodo + run_fondo + contexto + codigo_cuenta.",
      contable: "No aplica"
    },
    {
      name: "cuenta",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Glosa del modelo CMF. TotalPasivo se explicita como pasivo más patrimonio.",
      contable: "No aplica"
    },
    {
      name: "nota",
      type: "VARCHAR",
      role: "Atributo",
      significado: "Referencia a nota del XML, si existe. No se extrae su texto PDF.",
      contable: "No aplica"
    },
    {
      name: "valor_miles_mf",
      type: "BIGINT",
      role: "Métrica",
      significado: "Entero exacto del XML, en miles de su moneda. No convertido, redondeado ni rellenado. No sumar contextos.",
      contable: "Valor contable"
    },
    {
      name: "fuente_archivo",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "Nombre del FIEF original; la URL se reconstruye con RUN, período y la ruta CMF fiifr/xml.",
      contable: "No aplica"
    },
    {
      name: "enviado_cmf",
      type: "VARCHAR",
      role: "Fecha",
      significado: "Fecha/hora de envío leída del nombre del archivo; hora local declarada, sin inventar zona.",
      contable: "No aplica"
    },
    {
      name: "sha256_archivo",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "SHA-256 de los bytes originales del XML descargado.",
      contable: "No aplica"
    },
    {
      name: "cotejo_ficha",
      type: "VARCHAR",
      role: "Atributo",
      significado: "coincide = importe cotejado exactamente con su concepto y columna HTML. sin_columna = contexto del XML no expuesto por la ficha (por ejemplo trimestres en el cierre anual), validado contablemente pero no cotejable allí.",
      contable: "No aplica"
    }
  ]
},
{
  id: "fi_resultados",
  name: "fi.resultados",
  viewName: "fi_resultados",
  sector: "fi",
  sectorLabel: "Fondos de Inversión (CMF)",
  norma: "IFRS · XML CMF FIEF (Circular 1998)",
  corte: "2022-03 a 2026-06 · 16 cierres publicados",
  frecuencia: "Trimestral",
  frescura: "Se actualiza sola 3 veces al mes",
  modo: "Automático · incremental; identidades y cotejo antes de publicar",
  ultimaActualizacion: "2026-10-02",
  registros: "Trimestral · contextos separados",
  origen: "CMF — XML IFRS FIEF (Circular 1998) de cada fondo, enlazado en entidad.php?tipoentidad=FIRES|FINRE&pestania=29. Cotejo con las tablas de su ficha; no es una auditoría independiente del PDF firmado.",
  descripcion: "Estado de resultados integrales de fondos de inversión FIRES/FINRE, cuenta por cuenta (30 líneas por contexto). Se separan acumulado del ejercicio, trimestre y sus comparativos; no se suman entre sí. Miles de la moneda de presentación, gastos con signo original. Solo se publican contextos completos y que cuadran. Los contextos adicionales rechazados/ausentes se declaran en el manifiesto, no se rellenan con ceros.",
  advertencia: "El archivo puede traer varios contextos para la misma cuenta. Elegir PeriodoActual para el saldo/acumulado actual; no sumar contextos ni monedas. sin_columna no significa cotejado contra HTML. Las exclusiones y huecos están en fi_eeff_control.json y manifest.json.",
  columnas: [
    {
      name: "periodo",
      type: "VARCHAR",
      role: "PK",
      significado: "Cierre del archivo AAAA-MM. En comparativos no es la fecha de la cifra: usar fecha_fin_contexto.",
      contable: "No aplica"
    },
    {
      name: "run_fondo",
      type: "VARCHAR",
      role: "FK",
      significado: "RUN del fondo, sin DV; une directamente con fi.lista_entidades.",
      contable: "No aplica"
    },
    {
      name: "run_fondo_dv",
      type: "VARCHAR",
      role: "Atributo",
      significado: "RUN con DV módulo 11. El DV recibido se conserva separado.",
      contable: "No aplica"
    },
    {
      name: "dv_fondo_fuente",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "Dígito verificador literal del XML; las discrepancias quedan como aviso.",
      contable: "No aplica"
    },
    {
      name: "nombre_fondo",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Nombre reportado en el XML; puede ser abreviado y diferir del maestro.",
      contable: "No aplica"
    },
    {
      name: "tipo_entidad",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "FIRES rescatable / FINRE no rescatable, según registro CMF.",
      contable: "No aplica"
    },
    {
      name: "rut_agf",
      type: "VARCHAR",
      role: "FK",
      significado: "RUT de la administradora reportada, sin DV; une con agf.lista_entidades.",
      contable: "No aplica"
    },
    {
      name: "razon_social_agf",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Nombre de administradora declarado en este envío.",
      contable: "No aplica"
    },
    {
      name: "moneda",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Moneda de presentación: CLP, USD, EUR o COP; no sumar monedas distintas.",
      contable: "No aplica"
    },
    {
      name: "moneda_cmf",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "Código CMF literal ($$ pesos, PROM dólar, EUR euro, COP peso colombiano).",
      contable: "No aplica"
    },
    {
      name: "contexto",
      type: "VARCHAR",
      role: "PK",
      significado: "Contexto original. PeriodoActual = saldo/acumulado actual; PeriodoAnualAnterior = balance al diciembre anterior; PeriodoAnterior = acumulado comparable; TrimestreActual/TrimestreAnterior = solo el trimestre. SaldoInicialTerceraColumna = apertura IFRS cuando se informa. Filtrar el contexto antes de agregar.",
      contable: "No aplica"
    },
    {
      name: "fecha_inicio_contexto",
      type: "VARCHAR",
      role: "Fecha",
      significado: "Inicio declarado del contexto. Para el saldo de apertura, la única fecha del XML.",
      contable: "No aplica"
    },
    {
      name: "fecha_fin_contexto",
      type: "VARCHAR",
      role: "Fecha",
      significado: "Corte/fin declarado de las cifras; en apertura es el mismo instante de FechaInicio.",
      contable: "No aplica"
    },
    {
      name: "tipo_periodo",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "saldo, acumulado o trimestre; evita confundir stocks y flujos.",
      contable: "No aplica"
    },
    {
      name: "seccion",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Rubro del estado: corriente/no corriente, patrimonio, ingresos, gastos u otros integrales.",
      contable: "No aplica"
    },
    {
      name: "tipo_linea",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "detalle o total. No sumar detalles con sus totales.",
      contable: "No aplica"
    },
    {
      name: "orden",
      type: "INTEGER",
      role: "Atributo",
      significado: "Orden de presentación de la cuenta en la ficha CMF, dentro de cada tabla/contexto.",
      contable: "No aplica"
    },
    {
      name: "codigo_cuenta",
      type: "VARCHAR",
      role: "PK",
      significado: "Código FIEF literal. La clave de fila es periodo + run_fondo + contexto + codigo_cuenta.",
      contable: "No aplica"
    },
    {
      name: "cuenta",
      type: "VARCHAR",
      role: "Dimensión",
      significado: "Glosa del modelo CMF. TotalPasivo se explicita como pasivo más patrimonio.",
      contable: "No aplica"
    },
    {
      name: "nota",
      type: "VARCHAR",
      role: "Atributo",
      significado: "Referencia a nota del XML, si existe. No se extrae su texto PDF.",
      contable: "No aplica"
    },
    {
      name: "valor_miles_mf",
      type: "BIGINT",
      role: "Métrica",
      significado: "Entero exacto del XML, en miles de su moneda. No convertido, redondeado ni rellenado. No sumar contextos.",
      contable: "Valor contable"
    },
    {
      name: "fuente_archivo",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "Nombre del FIEF original; la URL se reconstruye con RUN, período y la ruta CMF fiifr/xml.",
      contable: "No aplica"
    },
    {
      name: "enviado_cmf",
      type: "VARCHAR",
      role: "Fecha",
      significado: "Fecha/hora de envío leída del nombre del archivo; hora local declarada, sin inventar zona.",
      contable: "No aplica"
    },
    {
      name: "sha256_archivo",
      type: "VARCHAR",
      role: "Dato fuente",
      significado: "SHA-256 de los bytes originales del XML descargado.",
      contable: "No aplica"
    },
    {
      name: "cotejo_ficha",
      type: "VARCHAR",
      role: "Atributo",
      significado: "coincide = importe cotejado exactamente con su concepto y columna HTML. sin_columna = contexto del XML no expuesto por la ficha (por ejemplo trimestres en el cierre anual), validado contablemente pero no cotejable allí.",
      contable: "No aplica"
    }
  ]
},
  // END AUTO FI EEFF DICTIONARY
  {
    id: "ffmm_balance",
    name: "ffmm.balance",
    viewName: "ffmm_balance",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos (CMF)",
    norma: "IFRS · XML CMF (Circular 1997)",
    corte: "Cierres de diciembre desde 2010",
    frecuencia: "Anual",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, los cierres ya publicados se revisan una vez al año",
    ultimaActualizacion: "2026-10-01",
    registros: "Una fila por fondo, cierre y línea",
    origen: "CMF — Estados financieros IFRS de fondos mutuos (XML «FMEF», Circular 1997 de 2010), enlazado en la ficha de cada fondo: https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&tipoentidad=RGFMU",
    descripcion: "Estado de situación financiera de cada fondo mutuo, vigente o extinto, al 31 de diciembre de cada año desde 2010, línea por línea (16 líneas), con el comparativo del año anterior.",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Cierre del ejercicio (AAAA-12): estados al 31 de diciembre.", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "FK", significado: "RUN del fondo sin dígito verificador (une con ffmm.lista_entidades).", contable: "No aplica" },
      { name: "run_fondo_dv", type: "VARCHAR", role: "Atributo", significado: "RUN del fondo con dígito verificador.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Nombre del fondo en el archivo de ese año.", contable: "No aplica" },
      { name: "rut_agf", type: "VARCHAR", role: "FK", significado: "RUT de la administradora sin dígito verificador (une con agf.lista_entidades).", contable: "No aplica" },
      { name: "razon_social_agf", type: "VARCHAR", role: "Atributo", significado: "Nombre de la administradora en el archivo.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda del fondo: CLP, USD o EUR. Los importes están en miles de esa moneda; no sumar monedas distintas.", contable: "No aplica" },
      { name: "moneda_cmf", type: "VARCHAR", role: "Atributo", significado: "Código de moneda tal como lo informa la CMF ($$ = pesos, PROM = dólares, EUR = euros).", contable: "No aplica" },
      { name: "seccion", type: "VARCHAR", role: "Atributo", significado: "Agrupación de la línea: ACTIVO, PASIVO o ACTIVO NETO.", contable: "No aplica" },
      { name: "tipo_linea", type: "VARCHAR", role: "Atributo", significado: "detalle o total. Los totales ya suman sus detalles: no sumarlos juntos.", contable: "No aplica" },
      { name: "orden", type: "INTEGER", role: "PK", significado: "Número de línea del balance como lo presenta la CMF (1 a 16). Es fijo por cuenta: la 8 es siempre el total activo y la 16 el activo neto.", contable: "No aplica" },
      { name: "codigo_cuenta", type: "VARCHAR", role: "PK", significado: "Código de la cuenta en el XML de la CMF (por ejemplo TotalActivo, TotalPasivo, ActivoNetoAtribuibleALosParticipes).", contable: "No aplica" },
      { name: "cuenta", type: "VARCHAR", role: "Atributo", significado: "Nombre de la línea del estado financiero.", contable: "No aplica" },
      { name: "nota", type: "VARCHAR", role: "Atributo", significado: "Número de la nota de los estados financieros que respalda la línea, si el fondo la informa.", contable: "No aplica" },
      { name: "valor_miles_mf", type: "BIGINT", role: "Métrica", significado: "Importe al 31 de diciembre en miles de la moneda del fondo.", contable: "Valor contable" },
      { name: "valor_anterior_miles_mf", type: "BIGINT", role: "Métrica", significado: "Comparativo del ejercicio anterior tal como lo presenta el mismo archivo; puede diferir de lo publicado un año antes si el fondo reexpresó. Vacío en el primer envío (2010).", contable: "Valor contable" },
      { name: "fuente_archivo", type: "VARCHAR", role: "Atributo", significado: "Nombre del XML de la CMF del que sale la fila.", contable: "No aplica" },
      { name: "enviado_cmf", type: "VARCHAR", role: "Atributo", significado: "Fecha y hora en que el fondo envió el archivo a la CMF (sale del nombre del archivo).", contable: "No aplica" },
      { name: "sha256_archivo", type: "VARCHAR", role: "Atributo", significado: "Huella SHA-256 del XML, para detectar reenvíos.", contable: "No aplica" }
    ]
  },
  {
    id: "ffmm_resultados",
    name: "ffmm.resultados",
    viewName: "ffmm_resultados",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos (CMF)",
    norma: "IFRS · XML CMF (Circular 1997)",
    corte: "Cierres de diciembre desde 2010",
    frecuencia: "Anual",
    frescura: "Se actualiza sola 3 veces al mes",
    modo: "Automático · incremental, los cierres ya publicados se revisan una vez al año",
    ultimaActualizacion: "2026-10-01",
    registros: "Una fila por fondo, cierre y línea",
    origen: "CMF — Estados financieros IFRS de fondos mutuos (XML «FMEF», Circular 1997 de 2010), enlazado en la ficha de cada fondo: https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&tipoentidad=RGFMU",
    descripcion: "Estado de resultados integrales de cada fondo mutuo, vigente o extinto, del ejercicio completo de cada año desde 2010, línea por línea (19 líneas), con el comparativo del año anterior.",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Cierre del ejercicio (AAAA-12): estados al 31 de diciembre.", contable: "No aplica" },
      { name: "run_fondo", type: "VARCHAR", role: "FK", significado: "RUN del fondo sin dígito verificador (une con ffmm.lista_entidades).", contable: "No aplica" },
      { name: "run_fondo_dv", type: "VARCHAR", role: "Atributo", significado: "RUN del fondo con dígito verificador.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Nombre del fondo en el archivo de ese año.", contable: "No aplica" },
      { name: "rut_agf", type: "VARCHAR", role: "FK", significado: "RUT de la administradora sin dígito verificador (une con agf.lista_entidades).", contable: "No aplica" },
      { name: "razon_social_agf", type: "VARCHAR", role: "Atributo", significado: "Nombre de la administradora en el archivo.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda del fondo: CLP, USD o EUR. Los importes están en miles de esa moneda; no sumar monedas distintas.", contable: "No aplica" },
      { name: "moneda_cmf", type: "VARCHAR", role: "Atributo", significado: "Código de moneda tal como lo informa la CMF ($$ = pesos, PROM = dólares, EUR = euros).", contable: "No aplica" },
      { name: "seccion", type: "VARCHAR", role: "Atributo", significado: "Agrupación de la línea: INGRESOS/PÉRDIDAS DE LA OPERACIÓN, GASTOS o RESULTADO.", contable: "No aplica" },
      { name: "tipo_linea", type: "VARCHAR", role: "Atributo", significado: "detalle o total. Los totales ya suman sus detalles: no sumarlos juntos.", contable: "No aplica" },
      { name: "orden", type: "INTEGER", role: "PK", significado: "Número de línea del estado de resultados como lo presenta la CMF (1 a 19). Es fijo por cuenta: la 8 es siempre el total de ingresos y la 14 la utilidad antes de impuesto.", contable: "No aplica" },
      { name: "codigo_cuenta", type: "VARCHAR", role: "PK", significado: "Código de la cuenta en el XML de la CMF (por ejemplo TotalIngresosPerdidasNetosDeLaOperacion, ComisionDeAdministracion).", contable: "No aplica" },
      { name: "cuenta", type: "VARCHAR", role: "Atributo", significado: "Nombre de la línea del estado financiero.", contable: "No aplica" },
      { name: "nota", type: "VARCHAR", role: "Atributo", significado: "Número de la nota de los estados financieros que respalda la línea, si el fondo la informa.", contable: "No aplica" },
      { name: "valor_miles_mf", type: "BIGINT", role: "Métrica", significado: "Importe acumulado del ejercicio (1 de enero a 31 de diciembre) en miles de la moneda del fondo. Los gastos van con signo negativo.", contable: "Valor contable" },
      { name: "valor_anterior_miles_mf", type: "BIGINT", role: "Métrica", significado: "Comparativo del ejercicio anterior tal como lo presenta el mismo archivo; puede diferir de lo publicado un año antes si el fondo reexpresó. Vacío en el primer envío (2010).", contable: "Valor contable" },
      { name: "fuente_archivo", type: "VARCHAR", role: "Atributo", significado: "Nombre del XML de la CMF del que sale la fila.", contable: "No aplica" },
      { name: "enviado_cmf", type: "VARCHAR", role: "Atributo", significado: "Fecha y hora en que el fondo envió el archivo a la CMF (sale del nombre del archivo).", contable: "No aplica" },
      { name: "sha256_archivo", type: "VARCHAR", role: "Atributo", significado: "Huella SHA-256 del XML, para detectar reenvíos.", contable: "No aplica" }
    ]
  },
  // BEGIN AUTO FL IFRS SERIES DICTIONARY
  {"sector":"factoring_leasing","sectorLabel":"Factoring y Leasing (CMF)","norma":"CMF IFRS TXT · extracción automática de cuentas ESF/ER","corte":"2009-03 a 2026-06 · 70 cierres","frescura":"Serie de la fuente CMF; valores crudos, no validación integral","modo":"Actions: descarga histórica incremental y publicación automática al completarse","ultimaActualizacion":"2026-10-07","origen":"CMF https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php; corrida Actions 37670992999. 28/32 RUT del catálogo con datos en la fuente. Incluye cuentas repetidas y valores no enteros; no convertir, deduplicar ni sumar sin criterio. No cotejo integral de estados.","columnas":[{"name":"periodo","type":"VARCHAR","role":"Dimensión","significado":"Cierre informado por CMF, AAAA-MM.","contable":"No aplica"},{"name":"rut","type":"VARCHAR","role":"Dimensión","significado":"Cuerpo del RUT actual del catálogo (sin DV); la unión es por cuerpo y no certifica vigencia ni identidad histórica.","contable":"No aplica"},{"name":"nombre_reportado","type":"VARCHAR","role":"Dimensión","significado":"Nombre reportado por CMF en ese período.","contable":"No aplica"},{"name":"segmento_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Segmento consignado en el catálogo actual; puede incluir entidades mixtas/automotrices.","contable":"No aplica"},{"name":"nombre_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Nombre del catálogo actual; puede diferir del nombre histórico.","contable":"No aplica"},{"name":"tipo_balance","type":"VARCHAR","role":"Dimensión","significado":"I individual / C consolidado. Se preservan separados; no sumar.","contable":"No aplica"},{"name":"moneda_archivo","type":"VARCHAR","role":"Dimensión","significado":"Moneda original, sin conversión.","contable":"No aplica"},{"name":"orden","type":"BIGINT","role":"Dimensión","significado":"Posición de la cuenta dentro de su estado (sociedad, tipo de balance, moneda, taxonomía y estado), tal como viene en el archivo; permite leer el estado en el orden que lo presenta la sociedad. Mismo criterio que las series de AGF, securitizadoras y CCAF.","contable":"No aplica"},{"name":"cuenta","type":"VARCHAR","role":"Dimensión","significado":"Etiqueta literal de cuenta reportada.","contable":"No aplica"},{"name":"valor_archivo","type":"BIGINT","role":"Métrica","significado":"Entero original cuando pudo leerse como entero; NULL para valores no enteros.","contable":"No aplica"},{"name":"valor_texto_original","type":"VARCHAR","role":"Métrica","significado":"Texto literal de la cifra, preservado siempre.","contable":"No aplica"},{"name":"valor_es_entero","type":"BOOLEAN","role":"Dimensión","significado":"Control de interpretación numérica; false no significa cero.","contable":"No aplica"},{"name":"taxonomia","type":"VARCHAR","role":"Dimensión","significado":"Código literal de taxonomía CMF.","contable":"No aplica"},{"name":"estado_financiero","type":"VARCHAR","role":"Dimensión","significado":"Código CMF del estado: ESF C/NC = situación financiera; ERFG = resultados por función; ERNG = resultados por naturaleza; ERI = resultado integral.","contable":"No aplica"},{"name":"repeticion_contexto","type":"BIGINT","role":"Dimensión","significado":"Ordinal de la misma etiqueta dentro del estado; se conserva sin sumar. En resultados, \"Ganancia (pérdida)\" aparece en ERFG/ERNG con ordinal 1 y 2 y otra vez al inicio de ERI, con el mismo valor: para la utilidad del período usar estado ERFG/ERNG y ordinal 1.","contable":"No aplica"},{"name":"fuente_archivo","type":"VARCHAR","role":"Dimensión","significado":"URL pública CMF que originó la fila.","contable":"No aplica"},{"name":"sha256_archivo","type":"VARCHAR","role":"Dimensión","significado":"Huella de la descarga usada.","contable":"No aplica"},{"name":"identidad_nombre_coincide_catalogo","type":"BOOLEAN","role":"Dimensión","significado":"Coincidencia de nombre normalizada; señal, no auditoría histórica.","contable":"No aplica"},{"name":"rut_dv","type":"VARCHAR","role":"Dimensión","significado":"RUT del catálogo con dígito verificador (cuerpo-DV).","contable":"No aplica"}],"id":"factoring_leasing_balance","name":"factoring_leasing.balance","viewName":"factoring_leasing_balance","registros":"Serie IFRS · sin cotejo integral","descripcion":"Balance IFRS CMF · serie histórica. 30,046 filas de cuentas de estados ESF entre 2009-03 a 2026-06; no son estados agregados. Incluye 2,446 importes no enteros preservados como texto/null y 950 repeticiones de contexto conservadas. Monedas, taxonomías y tipos I/C permanecen separados; sin conversión, deduplicación ni suma. Cifras no cotejadas en su totalidad."},
  {"sector":"factoring_leasing","sectorLabel":"Factoring y Leasing (CMF)","norma":"CMF IFRS TXT · extracción automática de cuentas ESF/ER","corte":"2009-03 a 2026-06 · 70 cierres","frescura":"Serie de la fuente CMF; valores crudos, no validación integral","modo":"Actions: descarga histórica incremental y publicación automática al completarse","ultimaActualizacion":"2026-10-07","origen":"CMF https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php; corrida Actions 37670992999. 28/32 RUT del catálogo con datos en la fuente. Incluye cuentas repetidas y valores no enteros; no convertir, deduplicar ni sumar sin criterio. No cotejo integral de estados.","columnas":[{"name":"periodo","type":"VARCHAR","role":"Dimensión","significado":"Cierre informado por CMF, AAAA-MM.","contable":"No aplica"},{"name":"rut","type":"VARCHAR","role":"Dimensión","significado":"Cuerpo del RUT actual del catálogo (sin DV); la unión es por cuerpo y no certifica vigencia ni identidad histórica.","contable":"No aplica"},{"name":"nombre_reportado","type":"VARCHAR","role":"Dimensión","significado":"Nombre reportado por CMF en ese período.","contable":"No aplica"},{"name":"segmento_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Segmento consignado en el catálogo actual; puede incluir entidades mixtas/automotrices.","contable":"No aplica"},{"name":"nombre_catalogo","type":"VARCHAR","role":"Dimensión","significado":"Nombre del catálogo actual; puede diferir del nombre histórico.","contable":"No aplica"},{"name":"tipo_balance","type":"VARCHAR","role":"Dimensión","significado":"I individual / C consolidado. Se preservan separados; no sumar.","contable":"No aplica"},{"name":"moneda_archivo","type":"VARCHAR","role":"Dimensión","significado":"Moneda original, sin conversión.","contable":"No aplica"},{"name":"orden","type":"BIGINT","role":"Dimensión","significado":"Posición de la cuenta dentro de su estado (sociedad, tipo de balance, moneda, taxonomía y estado), tal como viene en el archivo; permite leer el estado en el orden que lo presenta la sociedad. Mismo criterio que las series de AGF, securitizadoras y CCAF.","contable":"No aplica"},{"name":"cuenta","type":"VARCHAR","role":"Dimensión","significado":"Etiqueta literal de cuenta reportada.","contable":"No aplica"},{"name":"valor_archivo","type":"BIGINT","role":"Métrica","significado":"Entero original cuando pudo leerse como entero; NULL para valores no enteros.","contable":"No aplica"},{"name":"valor_texto_original","type":"VARCHAR","role":"Métrica","significado":"Texto literal de la cifra, preservado siempre.","contable":"No aplica"},{"name":"valor_es_entero","type":"BOOLEAN","role":"Dimensión","significado":"Control de interpretación numérica; false no significa cero.","contable":"No aplica"},{"name":"taxonomia","type":"VARCHAR","role":"Dimensión","significado":"Código literal de taxonomía CMF.","contable":"No aplica"},{"name":"estado_financiero","type":"VARCHAR","role":"Dimensión","significado":"Código CMF del estado: ESF C/NC = situación financiera; ERFG = resultados por función; ERNG = resultados por naturaleza; ERI = resultado integral.","contable":"No aplica"},{"name":"repeticion_contexto","type":"BIGINT","role":"Dimensión","significado":"Ordinal de la misma etiqueta dentro del estado; se conserva sin sumar. En resultados, \"Ganancia (pérdida)\" aparece en ERFG/ERNG con ordinal 1 y 2 y otra vez al inicio de ERI, con el mismo valor: para la utilidad del período usar estado ERFG/ERNG y ordinal 1.","contable":"No aplica"},{"name":"fuente_archivo","type":"VARCHAR","role":"Dimensión","significado":"URL pública CMF que originó la fila.","contable":"No aplica"},{"name":"sha256_archivo","type":"VARCHAR","role":"Dimensión","significado":"Huella de la descarga usada.","contable":"No aplica"},{"name":"identidad_nombre_coincide_catalogo","type":"BOOLEAN","role":"Dimensión","significado":"Coincidencia de nombre normalizada; señal, no auditoría histórica.","contable":"No aplica"},{"name":"rut_dv","type":"VARCHAR","role":"Dimensión","significado":"RUT del catálogo con dígito verificador (cuerpo-DV).","contable":"No aplica"}],"id":"factoring_leasing_resultados","name":"factoring_leasing.resultados","viewName":"factoring_leasing_resultados","registros":"Serie IFRS · sin cotejo integral","descripcion":"Resultados IFRS CMF · serie histórica. 22,368 filas de cuentas de estados ER entre 2009-03 a 2026-06; no son estados agregados. Incluye 2,446 importes no enteros preservados como texto/null y 950 repeticiones de contexto conservadas. Monedas, taxonomías y tipos I/C permanecen separados; sin conversión, deduplicación ni suma. Cifras no cotejadas en su totalidad."},
  // END AUTO FL IFRS SERIES DICTIONARY
  {
    id: "afp_lista_entidades",
    name: "afp.lista_entidades",
    viewName: "afp_lista_entidades",
    sector: "pensiones",
    sectorLabel: "Fondos de Pensiones (SPensiones)",
    norma: "D.L. 3.500 / SPensiones",
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "Una fila por administradora",
    descripcion: "Administradoras de fondos de pensiones: RUT, razón social y nombre de fantasía. Sin cifras.",
    origen: "Altas: AFP con valor cuota publicado a diario por la Superintendencia de Pensiones (vcfAFP.php), con el RUT del Registro de Valores CMF (RVEMI). pipelines/entidades/actualizar_listas.py.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "ID local de la administradora.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "Atributo", significado: "Cuerpo del RUT de la administradora (sin dígito verificador; Registro de Valores CMF para las altas automáticas).", contable: "No aplica" },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social de la administradora.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial (AFP + nombre publicado por la Superintendencia).", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_lista_entidades",
    name: "bancos.lista_entidades",
    viewName: "bancos_lista_entidades",
    sector: "bancos",
    sectorLabel: "Banca (CMF)",
    norma: "Ley General de Bancos / CMF",
    corte: "Códigos históricos y vigentes",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "Una fila por institución y agregado",
    descripcion: "Códigos de institución de los archivos bancarios CMF: bancos vigentes, históricos (fusionados o cerrados), filiales en el exterior y agregados del sistema. No equivale al número de bancos activos. RUT de los bancos activos cotejados con el registro CMF.",
    origen: "Registro CMF de bancos (consulta.php?mercado=B&entidad=BANCO): alta de bancos nuevos y paso de «Activo» a «No vigente». Códigos históricos y agregados: lista original. pipelines/entidades/actualizar_listas.py.",
    columnas: [
      { name: "codigo_institucion", type: "VARCHAR", role: "PK", significado: "Código del catálogo local.", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "Atributo", significado: "Cuerpo del RUT del catálogo local (sin dígito verificador), por cotejar.", contable: "No aplica" },
      { name: "rut_dv", type: "VARCHAR", role: "Atributo", significado: "RUT del catálogo con dígito verificador (cuerpo-DV).", contable: "No aplica" },
      { name: "razon_social", type: "VARCHAR", role: "Atributo", significado: "Nombre consignado localmente.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre abreviado consignado localmente.", contable: "No aplica" },
      { name: "tipo_licencia", type: "VARCHAR", role: "Atributo", significado: "Clasificación local, no verificada.", contable: "No aplica" },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "Estado local, no histórico por período.", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_balance",
    name: "bancos.balance",
    viewName: "bancos_balance",
    sector: "bancos",
    sectorLabel: "Banca (CMF)",
    norma: "CMF — Manual del Sistema de Información para bancos (B1/MB1 y B2/MB2)",
    corte: "Períodos mensuales validados desde 2026-07",
    frescura: "Publicación automática después del gate mensual",
    modo: "Automático con validación de cobertura y cotejo CMF",
    registros: "B1/B2 · importes fuente",
    descripcion: "Filas fuente de estados de situación financiera B1 (consolidado) y B2 (individual). La fila física permanece en numero_fila_fuente, separada de rubro/línea/ítem. Cada línea trae cuatro importes en pesos, uno por tipo de moneda (ver importes_fuente_raw): para el total de la cuenta hay que sumarlos, no hay total precalculado. B2 trae solo unas 8 cuentas por banco y mes (adeudado por bancos y colocaciones comerciales, de vivienda y de consumo): no es un balance individual completo. La institución 999 es el total del sistema financiero: no se suma con los bancos. B1 y B2 son perímetros distintos: no se suman entre sí, ni una cuenta padre con sus descendientes.",
    origen: "CMF — ZIP TXT mensual y XLSX de reporte mensual. Cada partición registra URL y SHA-256 de ambas fuentes en la fila y en su informe de validación.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Clave determinística compuesta por período, institución, modelo, cuenta y ocurrencia dentro del archivo.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Período mensual del archivo CMF en formato YYYY-MM.", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Último día calendario del mes informado.", contable: "No aplica" },
      { name: "codigo_institucion", type: "VARCHAR", role: "FK", significado: "Código CMF del encabezado y del nombre de archivo. El 999 es el total del sistema financiero (no un banco): excluirlo al sumar instituciones.", contable: "No aplica" },
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
      { name: "importes_fuente_raw", type: "VARCHAR[]", role: "Dato fuente", significado: "Cuatro importes en pesos, con ceros a la izquierda y sin transformar, en el orden del archivo CMF: [1] moneda chilena no reajustable, [2] reajustable por IPC, [3] reajustable por tipo de cambio, [4] moneda extranjera (Manual del Sistema de Información de la CMF, archivos MB1 y MB2).", contable: "La suma de los cuatro es el total de la cuenta (activos = pasivos + patrimonio al sumarlos, en 989 de 991 balances banco-mes publicados, con diferencia máxima de $1)" },
      { name: "importes_fuente_decimal", type: "VARCHAR[]", role: "Dato fuente", significado: "Representación decimal exacta de los cuatro importes, en el mismo orden que importes_fuente_raw.", contable: "La suma de los cuatro es el total de la cuenta" },
      { name: "archivo_fuente", type: "VARCHAR", role: "Procedencia", significado: "Ruta del miembro TXT dentro del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_zip", type: "VARCHAR", role: "Procedencia", significado: "URL oficial del ZIP procesado.", contable: "No aplica" },
      { name: "sha256_zip", type: "VARCHAR", role: "Procedencia", significado: "Hash de integridad del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "URL del reporte XLSX utilizado en el gate.", contable: "No aplica" },
      { name: "sha256_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "Hash del XLSX utilizado en el gate.", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_resultados",
    name: "bancos.resultados",
    viewName: "bancos_resultados",
    sector: "bancos",
    sectorLabel: "Banca (CMF)",
    norma: "CMF — Manual del Sistema de Información para bancos (R1/MR1)",
    corte: "Períodos mensuales validados desde 2026-07",
    frescura: "Publicación automática después del gate mensual",
    modo: "Automático con validación de cobertura y cotejo CMF",
    registros: "R1 · importes fuente",
    descripcion: "Filas fuente del estado de resultados R1 consolidado. Conserva la fila física en numero_fila_fuente, separada de rubro/línea/ítem. El importe, en pesos, es el ACUMULADO DEL EJERCICIO (de enero al mes informado; vuelve a empezar en enero): para el resultado de un mes hay que restar el del mes anterior del mismo año. La publicación no deriva acumulados ni métricas. La institución 999 es el total del sistema financiero: no se suma con los bancos.",
    origen: "CMF — ZIP TXT mensual y XLSX de reporte mensual. Cada partición registra URL y SHA-256 de ambas fuentes en la fila y en su informe de validación.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Clave determinística compuesta por período, institución, modelo, cuenta y ocurrencia dentro del archivo.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Período mensual del archivo CMF en formato YYYY-MM.", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Último día calendario del mes informado.", contable: "No aplica" },
      { name: "codigo_institucion", type: "VARCHAR", role: "FK", significado: "Código CMF del encabezado y del nombre de archivo. El 999 es el total del sistema financiero (no un banco): excluirlo al sumar instituciones.", contable: "No aplica" },
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
      { name: "importes_fuente_raw", type: "VARCHAR[]", role: "Dato fuente", significado: "Un único importe en pesos, con ceros a la izquierda y sin transformar.", contable: "Acumulado del ejercicio (de enero al mes informado)" },
      { name: "importes_fuente_decimal", type: "VARCHAR[]", role: "Dato fuente", significado: "Representación decimal exacta del importe, acumulado del ejercicio.", contable: "Acumulado del ejercicio (de enero al mes informado)" },
      { name: "archivo_fuente", type: "VARCHAR", role: "Procedencia", significado: "Ruta del miembro TXT dentro del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_zip", type: "VARCHAR", role: "Procedencia", significado: "URL oficial del ZIP procesado.", contable: "No aplica" },
      { name: "sha256_zip", type: "VARCHAR", role: "Procedencia", significado: "Hash de integridad del ZIP oficial.", contable: "No aplica" },
      { name: "fuente_url_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "URL del reporte XLSX utilizado en el gate.", contable: "No aplica" },
      { name: "sha256_xlsx_cotejo", type: "VARCHAR", role: "Procedencia", significado: "Hash del XLSX utilizado en el gate.", contable: "No aplica" }
    ]
  },
  {
    id: "factoring_leasing_lista_entidades",
    name: "factoring_leasing.lista_entidades",
    viewName: "factoring_leasing_lista_entidades",
    sector: "factoring_leasing",
    sectorLabel: "Factoring y Leasing (CMF)",
    norma: "Nómina Oficial CMF & Registro de Valores (RVEMI / FASOC / LISOC)",
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 2, 12 y 22)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "Una fila por sociedad",
    descripcion: "Sociedades de factoring, leasing y financiamiento automotriz. Las sociedades nuevas se agregan cuando reportan estados financieros IFRS a la CMF con giro factoring o leasing; sus estados se publican desde entonces.",
    origen: "Lista original (referencias CMF FASOC, LISOC y RVEMI) + altas automáticas desde el TXT IFRS de la CMF (pipelines/ifrs_sectores/actualizar.py).",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Cuerpo del RUT de la sociedad (sin dígito verificador), auditado bajo algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Identificador tributario y regulatorio unívoco de la entidad ante el SII y la CMF." },
      { name: "rut_completo", type: "VARCHAR", role: "Atributo", significado: "RUT institucional formateado con puntos y guion (XX.XXX.XXX-Y).", contable: "No aplica", interpretacion: "Formato visual para presentación de reportes corporativos." },
    { name: "rut_dv", type: "VARCHAR", role: "Atributo", significado: "RUT con dígito verificador (cuerpo-DV, Módulo 11).", contable: "No aplica", interpretacion: "Formato canónico cuerpo-DV para cruces con registros oficiales." },
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
    id: "corredoras_bolsa_lista_entidades",
    name: "corredoras.lista_entidades",
    viewName: "corredoras_bolsa_lista_entidades",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa (CMF)",
    norma: "CMF Chile — Registro de Corredores de Bolsa (Ley 18.045)",
    corte: "2014-03 a 2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "Una fila por corredora",
    descripcion: "Directorio oficial de entidades autorizadas e inscritas ante la CMF para intermediar valores de oferta pública, con validación de RUT bajo Módulo 11 y clasificación por conglomerado financiero.",
    origen: "Comisión para el Mercado Financiero (CMF) — Registro de Intermediarios de Valores.",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Cuerpo del RUT del corredor de bolsa (sin dígito verificador); clave canónica para cruces relacionales.", contable: "No aplica", interpretacion: "Identificador tributario y regulatorio unívoco de la intermediaria bursátil." },
    { name: "rut_dv", type: "VARCHAR", role: "Atributo", significado: "RUT con dígito verificador (cuerpo-DV, Módulo 11).", contable: "No aplica", interpretacion: "Formato canónico cuerpo-DV para cruces con registros oficiales." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social oficial inscrita en el Registro de Corredores de Bolsa de la CMF.", contable: "No aplica", interpretacion: "Denominación legal societaria formal." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre de fantasía o marca comercial estándar de la corredora.", contable: "No aplica", interpretacion: "Nombre representativo en el parqué y plataformas electrónicas de negociación." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Vigencia en el Registro de Corredores de Bolsa de la CMF ('Vigente' / 'No Vigente'); se actualiza sola 3 veces al mes (pipelines/entidades).", contable: "No aplica", interpretacion: "Permite separar a los corredores que operan hoy de los históricos." },
      { name: "tipo_intermediario", type: "VARCHAR", role: "Dimensión", significado: "Tipo de intermediario regulado ('CORREDOR DE BOLSA').", contable: "No aplica", interpretacion: "Distingue a los miembros de bolsas de valores facultados para transar acciones, renta fija y derivados." },
      { name: "grupo_financiero", type: "VARCHAR", role: "Dimensión", significado: "Conglomerado o matriz controladora de la corredora de bolsa.", contable: "No aplica", interpretacion: "Clasifica filiales bancarias (Banco de Chile, Santander, BCI, etc.) versus corredoras independientes (LarrainVial, BTG Pactual, etc.)." }
    ]
  },

  {
    id: "corredoras_bolsa_lista_entidades_registro",
    name: "corredoras.lista_entidades_registro",
    viewName: "corredoras_bolsa_lista_entidades_registro",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa (CMF)",
    norma: "CMF Chile — Registro Oficial de Intermediarios de Valores (Ley 18.045)",
    corte: "2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-24",
    registros: "Una fila por corredora",
    descripcion: "Catastro exhaustivo de intermediarios de bolsa registrados ante la CMF (24 vigentes y 96 históricos/cancelados) con validación Módulo 11 y enlace a ficha oficial.",
    origen: "Comisión para el Mercado Financiero (CMF) — Consulta de Entidades Fiscalizadas.",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Cuerpo del RUT (sin dígito verificador), canónico bajo Módulo 11.", contable: "No aplica", interpretacion: "Identificador tributario y regulatorio primario." },
            { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador canónico M11.", contable: "No aplica", interpretacion: "Dígito de control de integridad." },
    { name: "rut_dv", type: "VARCHAR", role: "Atributo", significado: "RUT con dígito verificador (cuerpo-DV, Módulo 11).", contable: "No aplica", interpretacion: "Formato canónico cuerpo-DV para cruces con registros oficiales." },
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
    id: "securitizadoras_lista_entidades",
    name: "securitizadoras.lista_entidades",
    viewName: "securitizadoras_lista_entidades",
    sector: "securitizadoras",
    sectorLabel: "Sociedades Securitizadoras (CMF)",
    norma: "CMF Chile — Ley 18.045 de Mercado de Valores (Título XVIII)",
    corte: "2026-06",
    frescura: "Mensual / Registros CMF",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "Una fila por sociedad",
    descripcion: "Catálogo oficial de Sociedades Securitizadoras registradas ante la CMF bajo el Título XVIII de la Ley N° 18.045 (9 entidades vigentes y 7 históricas / en liquidación).",
    origen: "Comisión para el Mercado Financiero (CMF) — Registro de Sociedades Securitizadoras (RGSEC).",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Rol Único Tributario del intermediario securitizador (sin DV).", contable: "No aplica", interpretacion: "Identificador tributario corporativo único de la entidad gestora." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador oficial validado bajo algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Garantía de integridad matemática del RUT fiscal." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT formal con puntos, guión y dígito verificador (ej: 97.004.000-5).", contable: "No aplica", interpretacion: "Formato canónico para reportes y citaciones regulatorias." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal inscrita en el registro de valores de la CMF.", contable: "No aplica", interpretacion: "Nombre de la sociedad anónima especial facultada para administrar patrimonios separados." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Estado de supervisión CMF: VIGENTE o NO VIGENTE / EN LIQUIDACION.", contable: "No aplica", interpretacion: "Condición operativa de la sociedad securitizadora ante el regulador." },
      { name: "tipo_entidad_cmf", type: "VARCHAR", role: "Dimensión", significado: "Código de fiscalizado CMF (RGSEC: Registro de Sociedades Securitizadoras).", contable: "No aplica", interpretacion: "Categoría reglamentaria de la entidad en el sistema de fiscalización." },
      { name: "lineas_deuda_registradas", type: "BIGINT", role: "Métrica", significado: "Número de líneas y programas de bonos securitizados inscritos ante CMF.", contable: "No aplica", interpretacion: "Volumen de programas de titulización estructurados y vigentes." },
      { name: "cmf_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace URL directo a la ficha corporativa de la entidad en el portal CMF.", contable: "No aplica", interpretacion: "Vínculo web de transparencia y auditoría documental." }
    ]
  },









{
    id: "patrimonios_separados_lista_entidades",
    name: "patrimonios_separados.lista_entidades",
    viewName: "patrimonios_separados_lista_entidades",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF)",
    norma: "CMF Chile — Ley 18.045 Título XVIII (Registro de Títulos de Deuda)",
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "Una fila por patrimonio",
    descripcion: "Inscripciones de títulos de deuda de securitización (patrimonios separados) por registro automático: número, fecha, securitizadora, tipo, moneda, monto inscrito y vencimiento. La clase de colateral no está en el listado CMF: queda vacía en las inscripciones agregadas automáticamente.",
    origen: "CMF — Inscripciones de títulos de deuda mediante modalidad de registro automático (listado_titulos_deuda.php), filtrado a securitizadoras. pipelines/entidades/actualizar_listas.py.",
    columnas: [
      { name: "numero_inscripcion", type: "VARCHAR", role: "PK", significado: "Número oficial de inscripción en el Registro de Valores de la CMF.", contable: "No aplica", interpretacion: "Código identificador legal único del programa de titulización." },
      { name: "fecha_inscripcion", type: "VARCHAR", role: "Dimensión", significado: "Fecha de autorización e inscripción del título en la CMF (YYYY-MM-DD).", contable: "No aplica", interpretacion: "Fecha de nacimiento jurídico de la línea de bonos securitizados." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "Cuerpo del RUT de la Sociedad Securitizadora (sin dígito verificador) que actúa como fiduciaria/gestora.", contable: "No aplica", interpretacion: "Clave foránea hacia securitizadoras_lista_entidades." },
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
    sectorLabel: "Patrimonios Separados (CMF)",
    norma: "Balance general del patrimonio separado (estados financieros publicados en la CMF)",
    corte: "Diciembre 2014 a diciembre 2025 (2010–2013 sin datos)",
    frescura: "Anual, cierre de diciembre",
    modo: "Híbrido · extracción PDF/Excel local; validación y publicación reproducibles",
    modoAyuda: "La extracción y curación inicial se consolidan fuera del workflow programado, en un Excel preparado desde PDFs; el script 05_publicar_balance_patrimonios.py valida y compila el resultado en Parquet.",
    ultimaActualizacion: "2026-09-28",
    registros: "Balance",
    descripcion: "Balance general de cada patrimonio separado, cuenta por cuenta y tal como viene impreso, en M$ y con su signo: 358 balances de 10 securitizadoras. Incluye las líneas de subtotal (categorías que empiezan con Total). Todos los balances cuadran: activos = pasivo circulante + pasivo no circulante + patrimonio, y las cuentas de detalle suman su subtotal. Ojo: 'Total Pasivos' es pasivo más patrimonio (igual al total de activos); el pasivo exigible es 'Total Pasivo Circulante' + 'Total Pasivo No Circulante'. Para sumar sin contar dos veces, usa solo las categorías de detalle o solo las de Total. La serie parte en diciembre de 2014: de 2010 a 2013 no hay datos (2013 no está en la fuente y 2010–2012 se dejaron fuera para no cortar la serie).",
    origen: "Estados financieros de cada patrimonio separado (CMF) → securitizadoras/fuentes/balances_patrimonios_separados.xlsx → securitizadoras/scripts/05_publicar_balance_patrimonios.py",
    columnas: [
      { name: "archivo", type: "VARCHAR", role: "PK", significado: "PDF de estados financieros de donde sale el balance.", contable: "No aplica", interpretacion: "Identifica el balance; junto con orden_en_balance identifica la fila." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "Cuerpo del RUT de la securitizadora (8 dígitos, sin DV).", contable: "No aplica", interpretacion: "Une con securitizadoras_lista_entidades.rut y patrimonios_separados_lista_entidades.rut_administradora." },
      { name: "rut_completo", type: "VARCHAR", role: "Atributo", significado: "RUT con puntos, guión y dígito verificador (módulo 11).", contable: "No aplica", interpretacion: "Para mostrar." },
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
    id: "ccaf_lista_entidades",
    name: "ccaf.lista_entidades",
    viewName: "ccaf_lista_entidades",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación (CCAF / SUSESO)",
    norma: "SUSESO (Ley N° 18.833) / CMF (Ley N° 18.045 Emisores RVEMI)",
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 2, 12 y 22)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "Una fila por caja",
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
    id: "agf_lista_entidades",
    name: "agf.lista_entidades",
    viewName: "agf_lista_entidades",
    sector: "agf",
    sectorLabel: "Administradoras Generales de Fondos (CMF)",
    norma: "Ley Única de Fondos (Ley N° 20.712 - LUF) / CMF",
    corte: "Oficial CMF 2026",
    frescura: "Catálogo Vigente",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "Una fila por administradora",
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
    id: "sistemas_pago_lista_entidades",
    name: "sistemas_pago.lista_entidades",
    viewName: "sistemas_pago_lista_entidades",
    sector: "sistemas_pago",
    sectorLabel: "Sistemas de Pago (BCCh / CMF)",
    norma: "Ley Orgánica Constitucional BCCh (Ley 18.840) / Ley 18.876 (DCV) / Ley 20.345 (Cámaras) / Compendio Normas Financieras BCCh",
    corte: "Lista vigente",
    frescura: "Se actualiza sola 3 veces al mes (días 10, 20 y 28)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-28",
    registros: "Una fila por entidad",
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
    id: "fintech_rpsf_lista_entidades",
    name: "fintech.lista_entidades",
    viewName: "fintech_rpsf_lista_entidades",
    sector: "fintech",
    sectorLabel: "Fintech y Finanzas Abiertas (CMF)",
    norma: "Ley N° 21.521 (Ley Fintec) / Norma de Carácter General CMF N° 502",
    corte: "Catálogo Oficial Vigente CMF",
    frescura: "Actualización Continua / Eventos Registrales CMF",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "Una fila por prestador",
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
    id: "cooperativas_lista_entidades",
    name: "cooperativas.lista_entidades",
    viewName: "cooperativas_lista_entidades",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito (CMF)",
    norma: "CMF Chile / Ley General de Cooperativas (DFL 5)",
    corte: "2026-07",
    frescura: "Al día (7 entidades sistémicas)",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "Una fila por cooperativa",
    descripcion: "Directorio institucional de las Cooperativas de Ahorro y Crédito (CAC) de importancia sistémica supervisadas por la CMF. Incluye Coopeuch, Oriencoop, Capual, Ahorrocoop, Detacoop, Coonfia y Coocretal con RUT canónico validado bajo Módulo 11. Criterio de inclusión: cooperativas fiscalizadas por la CMF (art. 87 Ley General de Cooperativas, patrimonio sobre UF 400.000), según la nómina vigente CMF. Cooperativas bajo supervisión DAES (p. ej. Norte Grande, Financoop) no se incluyen porque no reportan estados financieros comparables a la CMF.",
    origen: "Comisión para el Mercado Financiero (CMF) — Nómina de Cooperativas de Ahorro y Crédito Fiscalizadas.",
    columnas: [
      { name: "rut", type: "VARCHAR", role: "PK", significado: "Cuerpo numérico del RUT (sin dígito verificador); clave canónica para cruces relacionales.", contable: "No aplica", interpretacion: "Identificador institucional único para interoperabilidad con el sistema financiero." },
            { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador oficial validado bajo algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Garantía de integridad y consistencia matemática de la cédula tributaria." },
    { name: "rut_dv", type: "VARCHAR", role: "Atributo", significado: "RUT con dígito verificador (cuerpo-DV, Módulo 11).", contable: "No aplica", interpretacion: "Formato canónico cuerpo-DV para cruces con registros oficiales." },
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

// La modalidad separa la automatización del procesamiento de la automatización
// de su orquestación. Un flujo híbrido puede compilar y validar con código sin
// tener todavía un workflow programado que lo ejecute.
function modalidadDatos(modo) {
  const texto = String(modo || "Automático").toLowerCase();
  if (texto.startsWith("híbrido") || texto.startsWith("hibrido")) return "hybrid";
  if (texto.startsWith("manual")) return "manual";
  return "auto";
}

function ayudaModalidadDatos(modo) {
  const clase = modalidadDatos(modo);
  if (clase === "hybrid") {
    return "Híbrido: la extracción o curación inicial ocurre fuera del workflow programado; la validación, normalización y compilación del resultado son reproducibles mediante código.";
  }
  if (clase === "manual") {
    return "Manual: la extracción, selección o transcripción todavía requiere intervención y no cuenta con un compilador reproducible integrado.";
  }
  return "Automático: extracción, validación y publicación ejecutadas por código y workflows programados.";
}

window.SIFDataMode = {
  className: modalidadDatos,
  title: ayudaModalidadDatos,
  label: (modo) => modalidadDatos(modo) === "hybrid"
    ? "Híbrido"
    : modalidadDatos(modo) === "manual" ? "Manual" : "Automático"
};
window.SIFDataDictionary = DATA_DICTIONARY;

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
          <div class="dict-mode-legend" title="La modalidad describe la extracción y la publicación, no solo si existe un workflow de Actions.">
            <span class="dict-mode-legend-label">Modalidad:</span>
            <span class="dict-mode-badge mode-auto">Automático</span>
            <span class="dict-mode-badge mode-hybrid">Híbrido</span>
            <span class="dict-mode-badge mode-manual">Manual</span>
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
                  <span class="dict-mode-badge mode-${modalidadDatos(table.modo)}" title="${table.modoAyuda || ayudaModalidadDatos(table.modo)}">${table.modo || 'Automático'}</span>
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
              ${table.cobertura ? `
                <div class="dict-table-source">
                  <span class="source-badge">Cobertura</span>
                  <span class="source-text">${table.cobertura}</span>
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

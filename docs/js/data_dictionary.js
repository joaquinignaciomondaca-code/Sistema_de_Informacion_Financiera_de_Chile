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
    id: "vida_maestro",
    name: "vida.lista_entidades",
    viewName: "vida_maestro",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "61 entidades",
    descripcion: "Catálogo maestro y estado de solvencia de las 61 compañías de seguros de vida supervisadas por la CMF.",
    origen: "Comisión para el Mercado Financiero (CMF) — Nómina Oficial de Entidades Aseguradoras y Supervisión de Solvencia (Portal Estadístico CMF).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Surrogate Primary Key deterministica de la entidad (VIDA_RUT).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "Atributo", significado: "RUT oficial de la compañía aseguradora con dígito verificador.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Razón social de la compañía de seguros de vida.", contable: "No aplica" },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "Estado registral ante la CMF (Activa, En liquidación, etc.).", contable: "No aplica" },
      { name: "inversion_ultimo_reporte_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos de inversión reportados en el último cierre.", contable: "Valor de Mercado Bruto" },
      { name: "patrimonio_ultimo_reporte_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto reportado por la aseguradora en el último cierre.", contable: "Valor de Mercado Neto" },
      { name: "periodos_reportados", type: "BIGINT", role: "Métrica", significado: "Total de trimestres históricos reportados en la base CMF.", contable: "No aplica" }
    ]
  },
  {
    id: "vida_bonos",
    name: "vida.cartera_bonos",
    viewName: "vida_bonos",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "9.09M registros",
    descripcion: "Tenencias de renta fija soberana y corporativa (bonos de tesorería, bancarios y de empresas) mantenidas por aseguradoras de vida.",
    origen: "CMF — Circular N° 1835 (Anexo Cartera de Inversiones de Aseguradoras de Vida, Sección Bonos Nacionales y Soberanos).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía tenedora del instrumento.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Trimestre de corte del reporte regulatorio (formato YYYYMM).", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Código nemotécnico bursátil del bono en la Bolsa de Comercio.", contable: "No aplica" },
      { name: "tipo_bono", type: "VARCHAR", role: "Atributo", significado: "Clasificación de bono: BE (Empresas), BB (Bancario), BT (Tesorería).", contable: "No aplica" },
      { name: "tir_compra_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa Interna de Retorno a la cual fue adquirido el instrumento.", contable: "Costo Amortizado / Devengado" },
      { name: "tir_mercado_pct", type: "DOUBLE", role: "Métrica", significado: "TIR de mercado según vector de precios oficial CMF al cierre.", contable: "Valor Razonable / MtM" },
      { name: "tasa_emision_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de cupón nominal estipulada en la emisión del bono.", contable: "No aplica" },
      { name: "valor_mercado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valorización total del bono en millones de pesos según vector de precios.", contable: "Valor Razonable / MtM" },
      { name: "fecha_vencimiento", type: "DATE", role: "Fecha", significado: "Fecha de amortización final o vencimiento del bono.", contable: "No aplica" }
    ]
  },
  {
    id: "vida_acciones",
    name: "vida.cartera_acciones",
    viewName: "vida_acciones",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "143k registros",
    descripcion: "Cartera de renta variable nacional mantenida por compañías de seguros de vida (acciones IPSA y fuera de índice).",
    origen: "CMF — Circular N° 1835 (Anexo Cartera de Inversiones de Aseguradoras de Vida, Sección Renta Variable Nacional y Presencia Bursátil).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la aseguradora titular de las acciones.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo trimestral informado (YYYYMM).", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico bursátil de la acción (ej: CHILE, BCI, SQM-B, CMPC).", contable: "No aplica" },
      { name: "precio_cierre_clp", type: "DOUBLE", role: "Métrica", significado: "Precio de cierre en bolsa de la acción al último día hábil del periodo.", contable: "Valor Razonable / MtM" },
      { name: "presencia_pct", type: "DOUBLE", role: "Métrica", significado: "Porcentaje de presencia bursátil oficial en los últimos 180 días.", contable: "No aplica" },
      { name: "cantidad_acciones", type: "DOUBLE", role: "Métrica", significado: "Número físico de títulos accionarios en custodia.", contable: "No aplica" },
      { name: "valor_mercado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valorización total de la posición accionaria en millones de CLP.", contable: "Valor de Mercado Bruto" }
    ]
  },
  {
    id: "vida_bienes_raices",
    name: "vida.cartera_bienes_raices",
    viewName: "vida_bienes_raices",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "2.01M registros",
    descripcion: "Bienes raíces urbanos y comerciales de aseguradoras de vida para respaldo de reservas técnicas.",
    origen: "CMF — Circular N° 1835 (Anexo Cartera de Bienes Raíces Urbanos y Comerciales, respaldo de Reservas Técnicas).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la aseguradora propietaria del inmueble.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Trimestre informado.", contable: "No aplica" },
      { name: "rol_avaluo", type: "VARCHAR", role: "Atributo", significado: "Rol de avalúo del Servicio de Impuestos Internos (SII).", contable: "No aplica" },
      { name: "comuna", type: "VARCHAR", role: "Atributo", significado: "Comuna donde se ubica el bien raíz.", contable: "No aplica" },
      { name: "avaluo_fiscal_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valor asignado por el SII para el pago de contribuciones.", contable: "Avaluo Fiscal" },
      { name: "tasacion_comercial_m_clp", type: "DOUBLE", role: "Métrica", significado: "Tasación pericial independiente aprobada por la CMF.", contable: "Tasacion Comercial" },
      { name: "fecha_tasacion", type: "DATE", role: "Fecha", significado: "Fecha de la última tasación pericial del inmueble.", contable: "No aplica" }
    ]
  },
  {
    id: "vida_forwards",
    name: "vida.b7_forwards",
    viewName: "vida_forwards",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Formulario B-7 (Derivados CMF)",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "165k contratos",
    descripcion: "Contratos forward sobre tipo de cambio (USD/CLP, UF/CLP) y tasas para cobertura de pasivos en pólizas.",
    origen: "CMF — Ficha B7 de Derivados (Contratos Forward sobre tipo de cambio USD/CLP y UF/CLP reportados trimestralmente por Aseguradoras de Vida).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la aseguradora contraparte.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo de reporte (YYYYMM).", contable: "No aplica" },
      { name: "tipo_operacion", type: "VARCHAR", role: "Atributo", significado: "Compra o venta forward de moneda/tasa.", contable: "No aplica" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Atributo", significado: "Entidad financiera o banco contraparte del contrato.", contable: "No aplica" },
      { name: "precio_forward_pactado", type: "DOUBLE", role: "Métrica", significado: "Precio o tipo de cambio strike acordado en el contrato.", contable: "Valor Pactado" },
      { name: "valor_razonable_mtm_m_clp", type: "DOUBLE", role: "Métrica", significado: "Mark-to-market neto del contrato a la fecha de cierre.", contable: "Valor Razonable / MtM" },
      { name: "fecha_vencimiento", type: "DATE", role: "Fecha", significado: "Fecha de liquidación efectiva del forward.", contable: "No aplica" }
    ]
  },
  {
    id: "vida_swaps",
    name: "vida.b7_swaps",
    viewName: "vida_swaps",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Formulario B-7 (Derivados CMF)",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "314k contratos",
    descripcion: "Swaps de tasas de interés (IRS) y swaps de monedas cruzadas (Cross-Currency) para calce de duración.",
    origen: "CMF — Ficha B7 de Derivados (Contratos Swaps de tasa de interés y monedas cruzadas de Aseguradoras de Vida).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la aseguradora titular.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo informado.", contable: "No aplica" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Atributo", significado: "Banco o intermediario contraparte.", contable: "No aplica" },
      { name: "tasa_contrato_larga", type: "DOUBLE", role: "Métrica", significado: "Tasa fija o variable de la pata compradora.", contable: "No aplica" },
      { name: "tasa_contrato_corta", type: "DOUBLE", role: "Métrica", significado: "Tasa de la pata vendedora.", contable: "No aplica" },
      { name: "valor_razonable_mtm_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valor razonable del swap según modelo de descuento de flujos.", contable: "Valor Razonable / MtM" }
    ]
  },
  {
    id: "vida_repos",
    name: "vida.b7_repos",
    viewName: "vida_repos",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Formulario B-7 (Pactos y Repos CMF)",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "19.4k pactos",
    descripcion: "Operaciones de pactos activos y pasivos sobre bonos e instrumentos de renta fija por parte de aseguradoras de vida.",
    origen: "CMF — Ficha B7 de Pactos (Operaciones de Venta con Retrocompra y Compra con Retroventa de Aseguradoras de Vida).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la aseguradora.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Trimestre informado.", contable: "No aplica" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Atributo", significado: "Corredora o banco con quien se cerró el pacto.", contable: "No aplica" },
      { name: "tasa_pacto", type: "DOUBLE", role: "Métrica", significado: "Tasa pactada efectiva anualizada.", contable: "Costo Amortizado / Devengado" },
      { name: "tasa_mercado", type: "DOUBLE", role: "Métrica", significado: "Tasa de política monetaria o mercado a la fecha del pacto.", contable: "No aplica" },
      { name: "valor_pactado_um", type: "DOUBLE", role: "Métrica", significado: "Monto pactado en unidad monetaria respectiva.", contable: "Valor de Mercado Bruto" }
    ]
  },
  {
    id: "generales_maestro",
    name: "generales.lista_entidades",
    viewName: "generales_maestro",
    sector: "generales",
    sectorLabel: "Seguros Generales",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "42 entidades",
    descripcion: "Nómina oficial y resumen patrimonial de las 42 compañías de seguros generales y reaseguradoras.",
    origen: "Comisión para el Mercado Financiero (CMF) — Registro Público de Compañías de Seguros Generales (Portal Estadístico CMF).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Surrogate PK determinística de la aseguradora general (GEN_RUT).", contable: "No aplica" },
      { name: "rut_aseguradora", type: "VARCHAR", role: "Atributo", significado: "RUT oficial de la compañía de seguros generales.", contable: "No aplica" },
      { name: "nombre_aseguradora", type: "VARCHAR", role: "Atributo", significado: "Razón social registrada ante la CMF.", contable: "No aplica" },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "Estado regulatorio ante la CMF (Activa / En liquidación).", contable: "No aplica" },
      { name: "inversion_ultimo_reporte_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos de inversión en millones de CLP.", contable: "Valor de Mercado Bruto" },
      { name: "patrimonio_ultimo_reporte_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto reportado al último cierre.", contable: "Valor de Mercado Neto" }
    ]
  },
  {
    id: "generales_bonos",
    name: "generales.cartera_bonos",
    viewName: "generales_bonos",
    sector: "generales",
    sectorLabel: "Seguros Generales",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "287k registros",
    descripcion: "Cartera de renta fija nacional (bonos bancarios, corporativos y de tesorería) de aseguradoras generales.",
    origen: "CMF — Circular N° 1835 (Anexo Cartera de Inversiones de Aseguradoras Generales, Sección Renta Fija Nacional).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la aseguradora general titular.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Trimestre de corte informado.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico bursátil del título.", contable: "No aplica" },
      { name: "tipo_bono", type: "VARCHAR", role: "Atributo", significado: "Tipo de bono: BE (Empresas), BB (Bancos), BT (Tesorería).", contable: "No aplica" },
      { name: "tir_mercado_pct", type: "DOUBLE", role: "Métrica", significado: "TIR de mercado según vector oficial CMF.", contable: "Valor Razonable / MtM" },
      { name: "valor_mercado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valorización de mercado en millones de CLP.", contable: "Valor Razonable / MtM" }
    ]
  },
  {
    id: "generales_bienes_raices",
    name: "generales.cartera_bienes_raices",
    viewName: "generales_bienes_raices",
    sector: "generales",
    sectorLabel: "Seguros Generales",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "38k registros",
    descripcion: "Inmuebles y bienes raíces urbanos de aseguradoras generales para respaldo de obligaciones técnicas.",
    origen: "CMF — Circular N° 1835 (Anexo Cartera de Bienes Raíces de Compañías de Seguros Generales).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la aseguradora propietaria.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo trimestral informado.", contable: "No aplica" },
      { name: "comuna", type: "VARCHAR", role: "Atributo", significado: "Comuna de localización del inmueble.", contable: "No aplica" },
      { name: "avaluo_fiscal_m_clp", type: "DOUBLE", role: "Métrica", significado: "Avalúo fiscal otorgado por el SII.", contable: "Avaluo Fiscal" },
      { name: "tasacion_comercial_m_clp", type: "DOUBLE", role: "Métrica", significado: "Tasación pericial independiente aprobada por CMF.", contable: "Tasacion Comercial" }
    ]
  },
  {
    id: "generales_acciones",
    name: "generales.cartera_acciones",
    viewName: "generales_acciones",
    sector: "generales",
    sectorLabel: "Seguros Generales",
    norma: "Circular CMF 1835",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "17k registros",
    descripcion: "Cartera de acciones nacionales y presencia bursátil mantenidas por aseguradoras generales.",
    origen: "CMF — Circular N° 1835 (Anexo Cartera de Inversiones de Aseguradoras Generales, Sección Renta Variable).",
    columnas: [
      { name: "rut_aseguradora", type: "VARCHAR", role: "FK", significado: "RUT de la compañía aseguradora.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Trimestre informado.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico de la acción cotizada en bolsa.", contable: "No aplica" },
      { name: "precio_cierre_clp", type: "DOUBLE", role: "Métrica", significado: "Precio de cierre oficial en bolsa.", contable: "Valor Razonable / MtM" },
      { name: "valor_mercado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valorización de mercado total en millones de CLP.", contable: "Valor de Mercado Bruto" }
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
    registros: "1.129 fondos",
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
    registros: "834k activos",
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
    registros: "2.66k pactos",
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
    name: "fi.registro_fondos_universo",
    viewName: "fi_registro_fondos_universo",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "Ley Única de Fondos (LUF N° 20.712)",
    corte: "2026-03",
    frescura: "Censo CMF Completo",
    modo: "Automático Streaming CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "1.677 fondos",
    descripcion: "Censo y registro oficial completo de todos los fondos de inversión chilenos supervisados por la CMF (FINRE y FIRES), distinguiendo fondos vigentes y liquidados con sus respectivas fechas de inicio registral.",
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
    id: "fi_caratula_eeff_historico",
    name: "fi.caratula_eeff_historico",
    viewName: "fi_caratula_eeff_historico",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "IFRS / CMF Ley 20.712",
    corte: "2010-2026",
    frescura: "Panel Histórico Completo",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "Panel Histórico Auditado",
    descripcion: "Carátula histórica de balances generales y estados de resultados de fondos de inversión auditados bajo IFRS por la CMF. Incluye desglose esencial de activo total, patrimonio total, resultado del ejercicio, efectivo y equivalentes, cartera a valor razonable y cartera a costo amortizado.",
    origen: "Comisión para el Mercado Financiero (CMF) — Estados Financieros Auditados de Fondos de Inversión (FIEST / PDF).",
    columnas: [
      { name: "run_fondo", type: "BIGINT", role: "PK", significado: "RUN numérico oficial del fondo de inversión ante la CMF.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Razón social del fondo de inversión auditado.", contable: "No aplica" },
      { name: "administradora", type: "VARCHAR", role: "Dimensión", significado: "Nombre de la Administradora General de Fondos (AGF).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo contable de reporte en formato YYYYMM.", contable: "No aplica" },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año calendario del ejercicio contable.", contable: "No aplica" },
      { name: "mes", type: "BIGINT", role: "Dimensión", significado: "Mes de corte de balance general auditado (12 para anual).", contable: "No aplica" },
      { name: "efectivo_y_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo de caja, bancos y equivalentes de efectivo en millones de CLP.", contable: "Efectivo y Eq." },
      { name: "activos_financieros_vr_m_clp", type: "DOUBLE", role: "Métrica", significado: "Cartera de activos financieros a valor razonable (FVTPL / FVOCI) en millones de CLP.", contable: "Valor Razonable / MtM" },
      { name: "activos_financieros_amortizado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Cartera de instrumentos de inversión medidos a costo amortizado en millones de CLP.", contable: "Costo Amortizado" },
      { name: "activo_total_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos auditados del fondo en millones de CLP.", contable: "Activo Bruto" },
      { name: "patrimonio_total_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto atribuible a los aportantes / cuotapartícipes en millones de CLP.", contable: "Patrimonio Neto" },
      { name: "utilidad_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado integral neto del ejercicio en millones de CLP.", contable: "Resultado Neto" }
    ]
  },
  {
    id: "fi_repos_detalle_historico",
    name: "fi.repos_detalle_historico",
    viewName: "fi_repos_detalle_historico",
    sector: "fi",
    sectorLabel: "Fondos de Inversión",
    norma: "CMF VRC / CRV IFRS",
    corte: "2010-2026",
    frescura: "Panel Histórico 2010-2026",
    modo: "Automático Streaming CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "2.95k contratos literales",
    descripcion: "Detalle contractual exhaustivo de todas las operaciones de compra con retroventa (CRV - Activo) y venta con retrocompra (VRC - Pasivo) pactadas por fondos de inversión chilenos ante la CMF entre 2010 y 2026.",
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
    registros: "1.156 fondos",
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
    registros: "11k contratos",
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
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "7 administradoras",
    descripcion: "Catálogo maestro oficial de las 7 Administradoras de Fondos de Pensiones (AFP) activas en Chile, con AUM administrado, encaje legal del 1% y afiliados.",
    origen: "Superintendencia de Pensiones (SPensiones) — Nómina Oficial de Administradoras y Ficha Estadística (FEE) CMF.",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Identificador único determinístico de la administradora.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "Atributo", significado: "RUT oficial de la sociedad administradora con dígito verificador.", contable: "No aplica" },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social completa inscrita en el registro de la SPensiones.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial de la AFP (Habitat, Provida, Capital, etc.).", contable: "No aplica" },
      { name: "aum_total_m_usd", type: "DOUBLE", role: "Métrica", significado: "Activos bajo administración (AUM) totales en millones de dólares.", contable: "Valor Razonable / MtM" },
      { name: "aum_total_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activos totales administrados valorizados en millones de pesos chilenos.", contable: "Valor Razonable / MtM" },
      { name: "encaje_requerido_m_usd", type: "DOUBLE", role: "Métrica", significado: "Encaje patrimonial obligatorio por ley (1% del AUM aportado por la AFP).", contable: "Patrimonio Propio en Multifondos" },
      { name: "total_afiliados", type: "BIGINT", role: "Métrica", significado: "Número total de trabajadores y cotizantes afiliados a la administradora.", contable: "No aplica" },
      { name: "participacion_mercado_pct", type: "DOUBLE", role: "Métrica", significado: "Porcentaje de participación de la AFP sobre los activos del sistema.", contable: "No aplica" },
      { name: "comision_flujo_pct", type: "DOUBLE", role: "Métrica", significado: "Comisión cobrada sobre la remuneración mensual imponible del trabajador.", contable: "Ingreso Operacional" },
      { name: "grupo_controlador", type: "VARCHAR", role: "Atributo", significado: "Holding empresarial o grupo financiero controlador de la administradora.", contable: "No aplica" },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "Condición regulatoria ante la Superintendencia (Activa).", contable: "No aplica" }
    ]
  },
  {
    id: "afp_derivados_forwards",
    name: "afp.derivados_forwards",
    viewName: "afp_derivados_forwards",
    sector: "pensiones",
    sectorLabel: "Fondos de Pensiones",
    norma: "D.L. 3.500 / Régimen de Inversión SP",
    corte: "2026-03",
    frescura: "Al dia (2023-12 a 2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "560 contratos",
    descripcion: "Contratos de derivados Forward OTC suscritos por los Multifondos A al E para cobertura cambiaria de sus carteras internacionales (USD/CLP, EUR, UF).",
    origen: "Superintendencia de Pensiones — Carteras de Inversión Desagregadas Mensuales y Banco Central de Chile (BCCh).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Surrogate PK determinística del contrato forward.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo trimestral informado (YYYY-MM).", contable: "No aplica" },
      { name: "afp", type: "VARCHAR", role: "FK", significado: "Nemotécnico de la AFP titular de la posición.", contable: "No aplica" },
      { name: "tipo_de_fondo", type: "VARCHAR", role: "Atributo", significado: "Multifondo titular de la operación (Fondo A, B, C, D o E).", contable: "Patrimonio Autónomo" },
      { name: "codigo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Código oficial SP (WNMV, WNMC, WEMV, WEMC).", contable: "No aplica" },
      { name: "direccion", type: "VARCHAR", role: "Atributo", significado: "Posición del fondo: Venta (cobertura pasiva) o Compra.", contable: "No aplica" },
      { name: "mercado", type: "VARCHAR", role: "Atributo", significado: "Plaza de la contraparte: Nacional o Extranjero.", contable: "No aplica" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Atributo", significado: "Banco intermediario contraparte (Banco de Chile, Santander, JPMorgan, Citi).", contable: "No aplica" },
      { name: "precio_ejercicio", type: "DOUBLE", role: "Métrica", significado: "Tipo de cambio pactado en el contrato (strike price).", contable: "Precio de Ejercicio" },
      { name: "tipo_cambio_cierre", type: "DOUBLE", role: "Métrica", significado: "Tipo de cambio spot oficial a fin de mes según BCCh.", contable: "Valor de Mercado Spot" },
      { name: "nocional_m_usd", type: "DOUBLE", role: "Métrica", significado: "Monto nocional total del contrato en millones de USD.", contable: "Exposición Bruta" },
      { name: "inversion_mtm_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valorización Mark-to-Market (MTM) neta en millones de CLP.", contable: "Valor Razonable / MtM" },
      { name: "inversion_mtm_m_usd", type: "DOUBLE", role: "Métrica", significado: "Valorización Mark-to-Market (MTM) neta en millones de USD.", contable: "Valor Razonable / MtM" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha de liquidación del contrato.", contable: "No aplica" }
    ]
  },
  {
    id: "afp_derivados_swaps",
    name: "afp.derivados_swaps",
    viewName: "afp_derivados_swaps",
    sector: "pensiones",
    sectorLabel: "Fondos de Pensiones",
    norma: "D.L. 3.500 / Régimen de Inversión SP",
    corte: "2014-10 a 2026-04",
    frescura: "Al dia (139 meses consecutivos)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "6.6k contratos",
    descripcion: "Contratos de Swaps OTC de tasa de interés y monedas (Cross Currency Swaps UF vs USD) suscritos por las Administradoras de Fondos de Pensiones.",
    origen: "Superintendencia de Pensiones (SPensiones) — Carteras Desagregadas Mensuales de Inversión y Derivados.",
    columnas: [
      { name: "id_posicion", type: "VARCHAR", role: "PK", significado: "Surrogate PK determinística de la posición de swap.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual informado (formato YYYY-MM).", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha exacta de corte de la cartera informada.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT oficial de la AFP con dígito verificador normalizado.", contable: "No aplica" },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social oficial de la administradora de fondos de pensiones.", contable: "No aplica" },
      { name: "tipo_derivado", type: "VARCHAR", role: "Atributo", significado: "Categoría de instrumento derivado (SWAP).", contable: "No aplica" },
      { name: "contraparte", type: "VARCHAR", role: "Atributo", significado: "Banco o institución financiera contraparte del contrato.", contable: "No aplica" },
      { name: "unidad_indexada", type: "VARCHAR", role: "Atributo", significado: "Moneda o unidad indexada de liquidación (UF, USD, CLP).", contable: "No aplica" },
      { name: "nocional_usd_millones", type: "DOUBLE", role: "Métrica", significado: "Monto nocional total del contrato en millones de USD.", contable: "Exposición Bruta" },
      { name: "fuente", type: "VARCHAR", role: "Atributo", significado: "Organismo regulador emisor (SPENSIONES).", contable: "No aplica" }
    ]
  },
  {
    id: "afp_cartera_bonos",
    name: "afp.cartera_bonos",
    viewName: "afp_cartera_bonos",
    sector: "pensiones",
    sectorLabel: "Fondos de Pensiones",
    norma: "D.L. 3.500 / Compendio SP Libro IV",
    corte: "2014-10 a 2026-04",
    frescura: "Al dia (139 meses consecutivos)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "168k tenencias",
    descripcion: "Cartera desagregada de renta fija soberana y corporativa (Bonos de Tesorería BTP/BTU, Banco Central BCU/BCP, Bonos Bancarios y Corporativos) de los Fondos de Pensiones.",
    origen: "Superintendencia de Pensiones (SPensiones) — Portafolios Desagregados Mensuales de Inversiones.",
    columnas: [
      { name: "id_posicion", type: "VARCHAR", role: "PK", significado: "Identificador surrogate único de la posición en cartera.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual informado (formato YYYY-MM).", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha exacta de corte de la cartera informada.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT oficial de la administradora con dígito verificador.", contable: "No aplica" },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social oficial de la AFP tenedora.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Atributo", significado: "Clase de activo de renta fija (BONOS_SOBERANOS, BONOS_BANCARIOS, BONOS_EMPRESAS).", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Código nemotécnico bursátil o código de emisión del título.", contable: "No aplica" },
      { name: "emisor", type: "VARCHAR", role: "Atributo", significado: "Identificación de la entidad emisora (Tesorería, Banco Central, Banco o Empresa).", contable: "No aplica" },
      { name: "monto_usd_millones", type: "DOUBLE", role: "Métrica", significado: "Valorización de mercado total de la tenencia en millones de USD.", contable: "Valor Razonable / MtM" },
      { name: "fuente", type: "VARCHAR", role: "Atributo", significado: "Organismo supervisor fuente del reporte (SPENSIONES).", contable: "No aplica" }
    ]
  },
  {
    id: "afp_cartera_acciones",
    name: "afp.cartera_acciones",
    viewName: "afp_cartera_acciones",
    sector: "pensiones",
    sectorLabel: "Fondos de Pensiones",
    norma: "D.L. 3.500 / Compendio SP Libro IV",
    corte: "2014-10 a 2026-04",
    frescura: "Al dia (139 meses consecutivos)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "39.8k tenencias",
    descripcion: "Cartera desagregada de renta variable nacional (acciones de sociedades anónimas abiertas chilenas) mantenida por los Fondos de Pensiones.",
    origen: "Superintendencia de Pensiones (SPensiones) — Portafolios Desagregados Mensuales de Inversiones en Acciones.",
    columnas: [
      { name: "id_posicion", type: "VARCHAR", role: "PK", significado: "Identificador surrogate único de la posición accionaria.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual informado (formato YYYY-MM).", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha exacta de corte de la cartera informada.", contable: "No aplica" },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT oficial de la administradora con dígito verificador.", contable: "No aplica" },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social oficial de la AFP tenedora.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Nemotécnico bursátil de la acción (SQM-B, CHILE, BCI, BSANTANDER, CMPC, etc.).", contable: "No aplica" },
      { name: "emisor", type: "VARCHAR", role: "Atributo", significado: "Razón social o nombre del emisor corporativo de la acción.", contable: "No aplica" },
      { name: "tipo_accion", type: "VARCHAR", role: "Atributo", significado: "Tipo o serie de acción (ORD, PREF, SERIE_B, etc.).", contable: "No aplica" },
      { name: "monto_usd_millones", type: "DOUBLE", role: "Métrica", significado: "Valorización de mercado total de la tenencia en millones de USD.", contable: "Valor Razonable / MtM" },
      { name: "pct_emisor", type: "DOUBLE", role: "Métrica", significado: "Porcentaje de participación sobre el total del capital suscrito del emisor.", contable: "Participación en Capital" },
      { name: "fuente", type: "VARCHAR", role: "Atributo", significado: "Organismo supervisor fuente del reporte (SPENSIONES).", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_maestro",
    name: "bancos.lista_instituciones",
    viewName: "bancos_maestro",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Ley General de Bancos / CMF",
    corte: "2008-01 a 2026-07",
    frescura: "Al dia (40 instituciones historicas)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "40 instituciones",
    descripcion: "Catalogo exhaustivo de bancos comerciales, agencias extranjeras y filiales bancarias supervisadas por la CMF.",
    origen: "Comision para el Mercado Financiero (CMF) — Nomina Oficial de Entidades Bancarias y Grupos Financieros.",
    columnas: [
      { name: "codigo_institucion", type: "VARCHAR", role: "PK", significado: "Codigo unico CMF asignado a la institucion financiera (001, 012, 037, etc.).", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "Atributo", significado: "RUT oficial de la entidad bancaria con digito verificador (Modulo 11 verificado).", contable: "No aplica" },
      { name: "razon_social", type: "VARCHAR", role: "Atributo", significado: "Razon social legal inscrita en el registro de comercio.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial o marca bancaria de atencion al publico.", contable: "No aplica" },
      { name: "tipo_licencia", type: "VARCHAR", role: "Atributo", significado: "Tipo de licencia institucional (Banca Comercial, Banca Estatal, Agencia Extranjera, Banca Digital).", contable: "No aplica" },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "Estado operativo actual (Activo, Fusionado, Cerrado, Agregado).", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_balance_resumen",
    name: "bancos.balance_general",
    viewName: "bancos_balance_resumen",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Compendio Normas Contables Bancos C-3 (MB1)",
    corte: "2008-01 a 2026-07",
    frescura: "Al dia (223 meses consecutivos)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "5.1k balances",
    descripcion: "Balance general mensual consolidado: total activos, total pasivos y patrimonio neto en MM$ CLP y MM$ USD.",
    origen: "CMF — Estados de Situacion Financiera B1 (Modelo MB1 del Compendio de Normas Contables Bancarias).",
    columnas: [
      { name: "id_balance", type: "VARCHAR", role: "PK", significado: "Surrogate Primary Key del balance mensual (periodo_codigo_institucion).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual informado (YYYY-MM).", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha de corte del balance mensual.", contable: "No aplica" },
      { name: "codigo_institucion", type: "VARCHAR", role: "FK", significado: "Codigo de la institucion bancaria ante la CMF.", contable: "No aplica" },
      { name: "nombre_banco", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial de la entidad bancaria.", contable: "No aplica" },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos financieros y reales del banco en millones de pesos (MM$ CLP).", contable: "Valor de Mercado Bruto" },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos exigibles a terceros en millones de pesos (MM$ CLP).", contable: "Costo Amortizado / Devengado" },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto atribuible a los accionistas en millones de pesos (MM$ CLP).", contable: "Valor de Mercado Neto" },
      { name: "activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de activos convertido a millones de USD.", contable: "Valor Razonable / MtM" },
      { name: "pasivos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos convertido a millones de USD.", contable: "Valor Razonable / MtM" },
      { name: "patrimonio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto convertido a millones de USD.", contable: "Valor Razonable / MtM" }
    ]
  },
  {
    id: "bancos_estado_resultados",
    name: "bancos.estado_resultados",
    viewName: "bancos_estado_resultados",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Compendio Normas Contables Bancos C-3 (MR1)",
    corte: "2008-01 a 2026-07",
    frescura: "Al dia (223 meses consecutivos)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "5.1k estados de resultados",
    descripcion: "Estado de resultados mensual consolidado: utilidad neta del ejercicio en MM$ CLP y MM$ USD.",
    origen: "CMF — Estados de Resultados Consolidados R1 (Modelo MR1).",
    columnas: [
      { name: "id_resultado", type: "VARCHAR", role: "PK", significado: "Surrogate Primary Key del estado de resultados mensual.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual de resultados (YYYY-MM).", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha de corte del periodo de resultados.", contable: "No aplica" },
      { name: "codigo_institucion", type: "VARCHAR", role: "FK", significado: "Codigo CMF de la entidad bancaria informante.", contable: "No aplica" },
      { name: "nombre_banco", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial del banco.", contable: "No aplica" },
      { name: "utilidad_neta_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado final atribuible a los propietarios del banco en MM$ CLP.", contable: "Valor de Mercado Neto" },
      { name: "utilidad_m_usd", type: "DOUBLE", role: "Métrica", significado: "Utilidad neta convertida a millones de USD.", contable: "Valor de Mercado Neto" }
    ]
  },
  {
    id: "bancos_repos_saldos_series",
    name: "bancos.repos_saldos_series",
    viewName: "bancos_repos_saldos_series",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Compendio Normas Contables Bancos MB1 (Cuentas 116/216 e IFRS 141/243)",
    corte: "2008-01 a 2026-04",
    frescura: "Al dia (220 meses consecutivos)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-25",
    registros: "2.9k pactos y repos",
    descripcion: "Serie mensual histórica de operaciones de pacto de retroventa (activo / reverse repo) y retrocompra (pasivo / repo) banco por banco de toda la banca comercial en Chile.",
    origen: "Comisión para el Mercado Financiero (CMF) — Estados de Situación Financiera MB1 y Balances Históricos SBIF.",
    columnas: [
      { name: "id_repo", type: "VARCHAR", role: "PK", significado: "Surrogate Primary Key del saldo de repos mensual ({codigo_institucion}_{periodo}).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual informado en formato YYYY-MM.", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha exacta de cierre contable mensual (último día del mes).", contable: "No aplica" },
      { name: "codigo_institucion", type: "VARCHAR", role: "FK", significado: "Código único de 3 dígitos de la institución bancaria ante la CMF.", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT oficial de la entidad bancaria con dígito verificador (Módulo 11 verificado).", contable: "No aplica" },
      { name: "razon_social", type: "VARCHAR", role: "Atributo", significado: "Razón social oficial legal de la entidad bancaria.", contable: "No aplica" },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Atributo", significado: "Nombre comercial o de fantasía de la institución bancaria.", contable: "No aplica" },
      { name: "repo_activo_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Compras con pacto de retroventa (Derechos por pactos / Préstamo de liquidez garantizado con títulos) en MM$ CLP.", contable: "Costo Amortizado / Colateralizado" },
      { name: "repo_pasivo_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Ventas con pacto de retrocompra (Obligaciones por pactos / Fondeo mayorista recibido entregando títulos) en MM$ CLP.", contable: "Costo Amortizado / Colateralizado" },
      { name: "repo_neto_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Posición neta de liquidez en pactos (repo_activo - repo_pasivo) en MM$ CLP.", contable: "Saldo Neto de Liquidez" },
      { name: "tc_usd_cierre", type: "DOUBLE", role: "Métrica", significado: "Tipo de cambio oficial observado USD/CLP de cierre mensual.", contable: "No aplica" },
      { name: "repo_activo_mm_usd", type: "DOUBLE", role: "Métrica", significado: "Compras con pacto de retroventa convertidas a millones de USD.", contable: "Costo Amortizado / Colateralizado" },
      { name: "repo_pasivo_mm_usd", type: "DOUBLE", role: "Métrica", significado: "Ventas con pacto de retrocompra convertidas a millones de USD.", contable: "Costo Amortizado / Colateralizado" },
      { name: "repo_neto_mm_usd", type: "DOUBLE", role: "Métrica", significado: "Posición neta en millones de USD (repo_activo_usd - repo_pasivo_usd).", contable: "Saldo Neto de Liquidez" },
      { name: "total_transado_mm_usd", type: "DOUBLE", role: "Métrica", significado: "Volumen bruto total operado en pactos (repo_activo_usd + repo_pasivo_usd) en MM$ USD.", contable: "Volumen Total" },
      { name: "posicion_relativa", type: "VARCHAR", role: "Atributo", significado: "Clasificación estructural de la institución: 'Prestamista Neto de Liquidez' vs 'Tomador Neto de Fondeo'.", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_derivados_posicion_vigente",
    name: "bancos.derivados_posicion_vigente",
    viewName: "bancos_derivados_posicion_vigente",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Banco Central de Chile (BCCh SIETE F099 / Mercado de Derivados)",
    corte: "2010-01 a 2026-07",
    frescura: "Al dia (Mensual)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "Series de Stock F099",
    descripcion: "Stock nocional de posiciones abiertas en derivados financieros (Forwards USD/CLP, Forwards UF/CLP, NDF, Swaps Promedio Camara SPC, Cross-Currency Swaps CCS) mantenidas por la banca residente con contrapartes no residentes, empresas y AFPs.",
    origen: "Banco Central de Chile — Base de Datos Estadisticos (BDE SIETE, Capitulo F099 Derivados Bancarios).",
    columnas: [
      { name: "id_registro", type: "VARCHAR", role: "PK", significado: "Identificador deterministico del registro de posicion vigente (periodo_seriesId).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual de observacion (formato YYYY-MM).", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha exacta de cierre contable mensual.", contable: "No aplica" },
      { name: "categoria_mercado", type: "VARCHAR", role: "Atributo", significado: "Segmento funcional del mercado financiero (Derivados Bancarios OTC).", contable: "No aplica" },
      { name: "tipo_registro", type: "VARCHAR", role: "Atributo", significado: "Tipo de medicion contable (Posicion Vigente / Stock Nocional).", contable: "No aplica" },
      { name: "instrumento", type: "VARCHAR", role: "Atributo", significado: "Tipo de contrato derivado (Forward Monedas, Forward NDF, Swap Promedio Camara, CCS, Opciones).", contable: "Valor Razonable / MtM" },
      { name: "contraparte", type: "VARCHAR", role: "Atributo", significado: "Sector institucional contraparte (No Residentes, Empresas Sector Real, Fondos de Pensiones AFPs, Residentes No Bancos).", contable: "No aplica" },
      { name: "plazo_contractual", type: "VARCHAR", role: "Atributo", significado: "Tramo contractual de vencimiento (Hasta 7d, 8-35d, 36-95d, 96-185d, 186-370d, >1a, 2a, 5a, 10a+).", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda de denominacion del contrato (USD, UF, CLP).", contable: "No aplica" },
      { name: "unidad_medida", type: "VARCHAR", role: "Atributo", significado: "Escala y unidad de reporte oficial (Millones de USD, Miles de UF, Miles de Millones de CLP).", contable: "No aplica" },
      { name: "direccion", type: "VARCHAR", role: "Atributo", significado: "Posicion de la banca residente (Compra, Venta, Neto, Total).", contable: "No aplica" },
      { name: "monto", type: "DOUBLE", role: "Métrica", significado: "Monto o saldo nocional vigente al corte del mes.", contable: "Valor Razonable / MtM" },
      { name: "series_id", type: "VARCHAR", role: "FK", significado: "Codigo de serie oficial en el sistema SIETE del Banco Central de Chile.", contable: "No aplica" },
      { name: "glosa_serie", type: "VARCHAR", role: "Atributo", significado: "Descripcion textual completa de la serie segun el catalogo oficial BCCh.", contable: "No aplica" }
    ]
  },
  {
    id: "bancos_derivados_flujos_transados",
    name: "bancos.derivados_flujos_transados",
    viewName: "bancos_derivados_flujos_transados",
    sector: "bancos",
    sectorLabel: "Banca Comercial",
    norma: "Banco Central de Chile (BCCh SIETE F099 / Mercado de Derivados)",
    corte: "2010-01 a 2026-07",
    frescura: "Al dia (Mensual)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "Series de Flujo F099",
    descripcion: "Volumenes y montos brutos/netos mensuales transados en el mercado de derivados por la banca residente con agentes externos, corporativos y multifondos.",
    origen: "Banco Central de Chile — Base de Datos Estadisticos (BDE SIETE, Capitulo F099 Derivados Bancarios).",
    columnas: [
      { name: "id_registro", type: "VARCHAR", role: "PK", significado: "Identificador deterministico del registro de flujo transado (periodo_seriesId).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo mensual informado (YYYY-MM).", contable: "No aplica" },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha de corte del periodo mensual.", contable: "No aplica" },
      { name: "categoria_mercado", type: "VARCHAR", role: "Atributo", significado: "Segmento funcional del mercado (Derivados Bancarios OTC).", contable: "No aplica" },
      { name: "tipo_registro", type: "VARCHAR", role: "Atributo", significado: "Tipo de medicion (Monto Transado / Flujo Mensual).", contable: "No aplica" },
      { name: "instrumento", type: "VARCHAR", role: "Atributo", significado: "Tipo de contrato derivado transado.", contable: "Valor Razonable / MtM" },
      { name: "contraparte", type: "VARCHAR", role: "Atributo", significado: "Sector institucional de contraparte.", contable: "No aplica" },
      { name: "plazo_contractual", type: "VARCHAR", role: "Atributo", significado: "Plazo de liquidacion o maduracion contractual.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda de transaccion (USD, UF, CLP).", contable: "No aplica" },
      { name: "unidad_medida", type: "VARCHAR", role: "Atributo", significado: "Unidad oficial (Millones de USD, Miles de UF, etc.).", contable: "No aplica" },
      { name: "direccion", type: "VARCHAR", role: "Atributo", significado: "Sentido del flujo (Compra, Venta, Neto, Total).", contable: "No aplica" },
      { name: "monto", type: "DOUBLE", role: "Métrica", significado: "Monto total transado durante el mes calendario.", contable: "Flujo de Efectivo / Rotacion" },
      { name: "series_id", type: "VARCHAR", role: "FK", significado: "Codigo de serie en SIETE BCCh.", contable: "No aplica" },
      { name: "glosa_serie", type: "VARCHAR", role: "Atributo", significado: "Descripcion oficial de la serie BCCh.", contable: "No aplica" }
    ]
  }
,
  // =========================================================================
  // MACROECONOMIA & TASAS DE INTERES (BCCh SIETE)
  // =========================================================================
  {
    id: "macro_tasas_rendimientos",
    name: "macro.tasas_rendimientos",
    viewName: "macro_tasas_rendimientos",
    sector: "macro",
    sectorLabel: "Macroeconomía & Tasas",
    norma: "Banco Central de Chile (BCCh SIETE / Capítulo F022)",
    corte: "2014-01 a 2026-09",
    frescura: "Al día (Mensual)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "153 periodos",
    descripcion: "Tasas de política monetaria (TPM), costo de fondeo interbancario (TIB / ICP), curvas de rendimiento soberanas BCP (pesos 2Y, 5Y, 10Y) y BCU (UF 5Y, 10Y, 20Y), swaps promedio cámara (SPC), pendiente de curva y breakeven de inflación implícita.",
    origen: "Banco Central de Chile — Base de Datos Estadísticos (BDE SIETE, Mercado Financiero y Tasas de Interés).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "PK", significado: "Periodo mensual de referencia (formato YYYY-MM).", contable: "No aplica", interpretacion: "Eje temporal maestro para cruces analíticos y JOIN con balances bancarios, derivados y carteras de inversión." },
      { name: "tpm", type: "DOUBLE", role: "Métrica", significado: "Tasa de Política Monetaria fijada por el Consejo del BCCh (promedio mensual, %).", contable: "Tasa Oficial BCCh", interpretacion: "Tasa rectora del costo de fondeo a 1 día en pesos. Un incremento refleja sesgo contractivo contra presiones inflacionarias; recortes buscan estimular la liquidez y la demanda interna agregada." },
      { name: "tib_promedio", type: "DOUBLE", role: "Métrica", significado: "Tasa de Interés Interbancaria promedio / ICP (%).", contable: "Costo Fondeo Interbancario", interpretacion: "Tasa efectiva a la que los bancos comerciales se prestan fondos a 1 día en el mercado interbancario. Mide la liquidez diaria del sistema financiero y arbitra estrechamente con la TPM." },
      { name: "bcp_2y", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés mercado secundario Bonos Central en Pesos a 2 años (% anual).", contable: "Curva Nominal Pesos", interpretacion: "Representa las expectativas del mercado financiero sobre la trayectoria de la TPM en el corto/mediano plazo más una prima por plazo mínima." },
      { name: "bcp_5y", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés mercado secundario Bonos Central en Pesos a 5 años (% anual).", contable: "Curva Nominal Pesos", interpretacion: "Tasa de referencia para emisiones corporativas y créditos comerciales a mediano plazo en moneda nominal." },
      { name: "bcp_10y", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés mercado secundario Bonos Central en Pesos a 10 años (% anual).", contable: "Curva Nominal Pesos", interpretacion: "Benchmark soberano de largo plazo sin riesgo de crédito. Refleja el anclaje de expectativas de crecimiento tendencial y primas de riesgo país/fiscal." },
      { name: "bcu_5y", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés mercado secundario Bonos Central en UF a 5 años (% real anual).", contable: "Curva Real UF", interpretacion: "Costo de endeudamiento real libre de inflación a mediano plazo; tasa de referencia para el costo de fondeo hipotecario y proyectos de inversión corporativos." },
      { name: "bcu_10y", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés mercado secundario Bonos Central en UF a 10 años (% real anual).", contable: "Curva Real UF", interpretacion: "Tasa real libre de riesgo a 10 años; activo de cobertura esencial para aseguradoras de vida (rentas vitalicias) y fondos de pensiones para calce de pasivos en UF." },
      { name: "bcu_20y", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés mercado secundario Bonos Central en UF a 20 años (% real anual).", contable: "Curva Real UF", interpretacion: "Extremo largo de la curva real chilena; refleja la demanda estructural por duración de los inversionistas institucionales locales de muy largo plazo." },
      { name: "spc_clp_2y", type: "DOUBLE", role: "Métrica", significado: "Tasa Swap Promedio Cámara en Pesos a 2 años (% anual).", contable: "Derivados de Tasa", interpretacion: "Tasa fija pagada o recibida para intercambiar por la tasa ICP flotante durante 2 años; indicador del sesgo anticipado de la política monetaria en el mercado OTC." },
      { name: "spc_uf_1y", type: "DOUBLE", role: "Métrica", significado: "Tasa Swap Promedio Cámara en UF a 1 año (% real anual).", contable: "Derivados de Tasa", interpretacion: "Costo swap de cobertura de inflación y descalce de moneda a 1 año en el mercado de derivados interbancario." },
      { name: "spread_bcp_10y_2y_bps", type: "DOUBLE", role: "Métrica", significado: "Diferencial de rendimiento entre el BCP 10Y y el BCP 2Y en puntos base (bps).", contable: "Slope Curva Soberana", interpretacion: "Pendiente de la curva soberana. Valor positivo (>0) indica curva empinada o normal (expectativas de expansión). Inversión (<0) es una señal canónica de desaceleración económica o restricción monetaria." },
      { name: "spread_bcp_5y_2y_bps", type: "DOUBLE", role: "Métrica", significado: "Diferencial de rendimiento entre el BCP 5Y y el BCP 2Y en puntos base (bps).", contable: "Slope Tramo Medio", interpretacion: "Mide la curvatura y premio por plazo en el tramo intermedio de la curva soberana nominal." },
      { name: "inflacion_implicita_5y_breakeven", type: "DOUBLE", role: "Métrica", significado: "Inflación de equilibrio (Breakeven) a 5 años (BCP 5Y - BCU 5Y en %).", contable: "Compensación Inflación", interpretacion: "Expectativa de inflación promedio a 5 años implícita en los precios de mercado más premio por riesgo inflacionario. Valores cercanos a 3.0% señalan anclaje de expectativas al centro de la meta del BCCh." },
      { name: "inflacion_implicita_10y_breakeven", type: "DOUBLE", role: "Métrica", significado: "Inflación de equilibrio (Breakeven) a 10 años (BCP 10Y - BCU 10Y en %).", contable: "Compensación Inflación", interpretacion: "Credibilidad de la política monetaria a largo plazo; estabilidad cercana al 3% confirma el anclaje del esquema de metas de inflación del Banco Central." }
    ]
  },
  {
    id: "macro_divisas_mercado",
    name: "macro.divisas_mercado",
    viewName: "macro_divisas_mercado",
    sector: "macro",
    sectorLabel: "Macroeconomía & Tasas",
    norma: "Banco Central de Chile (BCCh SIETE / Capítulos F072 - F073)",
    corte: "2014-01 a 2026-09",
    frescura: "Al día (Mensual)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "153 periodos",
    descripcion: "Tipo de cambio nominal oficial USD/CLP (promedio mensual, cierre de mes, mínimos, máximos y volatilidad mensual anualizada), Euro Observado (EUR/CLP) e índices de Tipo de Cambio Real multilateral (TCR y TCR-5).",
    origen: "Banco Central de Chile — Estadísticas Cambiarias y de Comercio Exterior (SIETE F073 / F072).",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "PK", significado: "Periodo mensual de referencia (YYYY-MM).", contable: "No aplica", interpretacion: "Identificador temporal primario de la observación cambiaria mensual." },
      { name: "usd_clp_promedio", type: "DOUBLE", role: "Métrica", significado: "Dólar Observado promedio mensual ($CLP por USD).", contable: "Precio Mercado Spot", interpretacion: "Nivel central del tipo de cambio en el mes; utilizado en conversión de flujos de exportación/importación y valorización macroeconómica." },
      { name: "usd_clp_cierre", type: "DOUBLE", role: "Métrica", significado: "Dólar Observado en el último día hábil bancario del mes ($CLP por USD).", contable: "Precio Mercado Spot", interpretacion: "Tipo de cambio contable oficial con el que bancos, aseguradoras, empresas y fondos valorizan sus balances y pasivos/activos en moneda extranjera al cierre." },
      { name: "usd_clp_min", type: "DOUBLE", role: "Métrica", significado: "Valor mínimo alcanzado por el Dólar Observado durante el mes ($CLP).", contable: "Rango Mensual", interpretacion: "Suelo de negociación mensual del mercado cambiario interbancario." },
      { name: "usd_clp_max", type: "DOUBLE", role: "Métrica", significado: "Valor máximo alcanzado por el Dólar Observado durante el mes ($CLP).", contable: "Rango Mensual", interpretacion: "Techo de cotización mensual; el ancho (max - min) indica la amplitud intrames de la moneda." },
      { name: "var_mensual_usd_pct", type: "DOUBLE", role: "Métrica", significado: "Variación porcentual mensual del tipo de cambio cierre vs cierre anterior (%).", contable: "Variación Cambiaria", interpretacion: "Tasa de depreciación (>0) o apreciación (<0) del peso chileno frente al dólar; impacta directamente en la inflación transable importada." },
      { name: "var_anual_usd_pct", type: "DOUBLE", role: "Métrica", significado: "Variación porcentual interanual (12 meses) del Dólar Observado (%).", contable: "Variación Cambiaria", interpretacion: "Presión cambiaria anual acumulada; alzas pronunciadas encarecen insumos y bienes durables importados." },
      { name: "usd_clp_volatilidad_anualizada_pct", type: "DOUBLE", role: "Métrica", significado: "Volatilidad histórica realizada mensual del USD/CLP anualizada (base 252 días, %).", contable: "Riesgo de Mercado", interpretacion: "Medida del riesgo e incertidumbre cambiaria; mayor volatilidad encarece las primas de cobertura en opciones y forwards FX." },
      { name: "eur_clp_promedio", type: "DOUBLE", role: "Métrica", significado: "Euro Observado promedio mensual ($CLP por EUR).", contable: "Precio Mercado Spot", interpretacion: "Tipo de cambio de referencia frente a la zona euro para comercio exterior bilateral." },
      { name: "eur_clp_cierre", type: "DOUBLE", role: "Métrica", significado: "Euro Observado cierre del mes ($CLP por EUR).", contable: "Precio Mercado Spot", interpretacion: "Cotización contable de cierre para contratos y activos nominados en euros." },
      { name: "var_mensual_eur_pct", type: "DOUBLE", role: "Métrica", significado: "Variación mensual del Euro frente al CLP (%).", contable: "Variación Cambiaria", interpretacion: "Apreciación o depreciación mensual del peso chileno frente a la moneda comunitaria europea." },
      { name: "tcr_general", type: "DOUBLE", role: "Métrica", significado: "Índice de Tipo de Cambio Real Multilateral (promedio 1986=100).", contable: "Índice de Competitividad", interpretacion: "Competitividad de precios del sector exportador chileno respecto a una canasta de socios comerciales ponderados por comercio exterior y ajustados por diferenciales de inflación. Valores sobre 100 indican mayor competitividad externa relativa; bajo 100 apreciación real del peso." },
      { name: "tcr_5monedas", type: "DOUBLE", role: "Métrica", significado: "Índice de Tipo de Cambio Real frente a las 5 principales monedas mundiales (TCR-5).", contable: "Índice de Competitividad", interpretacion: "Competitividad cambiaria real enfocada en EE.UU., Japón, Reino Unido, Canadá y Zona Euro." }
    ]
  },
  {
    id: "macro_precios_actividad",
    name: "macro.precios_actividad",
    viewName: "macro_precios_actividad",
    sector: "macro",
    sectorLabel: "Macroeconomía & Tasas",
    norma: "Banco Central de Chile (BCCh SIETE / Capítulos G073, F032, F019, F089)",
    corte: "2014-01 a 2026-09",
    frescura: "Al día (Mensual)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "153 periodos",
    descripcion: "Unidad de Fomento (UF cierre y promedio), Índice de Precios al Consumidor (IPC índice, variación mensual y anual), IMACEC Total y No Minero, Precio spot del Cobre BML y Expectativas de Inflación EEE a 11 y 23 meses.",
    origen: "Banco Central de Chile e Instituto Nacional de Estadísticas (INE) — SIETE Precios, Cuentas Nacionales y Encuestas.",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "PK", significado: "Periodo mensual (YYYY-MM).", contable: "No aplica", interpretacion: "Identificador temporal mensual." },
      { name: "uf_cierre", type: "DOUBLE", role: "Métrica", significado: "Valor de la Unidad de Fomento al último día del mes ($CLP).", contable: "Unidad Indexación Oficial", interpretacion: "Unidad reajustable según inflación; base de cálculo contractual de la gran mayoría de créditos hipotecarios, pólizas de seguros de vida y bonos soberanos BCU en Chile." },
      { name: "uf_promedio", type: "DOUBLE", role: "Métrica", significado: "Valor de la UF promedio durante el mes ($CLP).", contable: "Unidad Indexación Oficial", interpretacion: "Promedio del costo reajustable del mes para liquidación de servicios y rentas indexadas." },
      { name: "uf_var_mensual_pct", type: "DOUBLE", role: "Métrica", significado: "Variación porcentual mensual del valor de la UF (%).", contable: "Variación Indexación", interpretacion: "Ritmo de reajuste mensual del capital adeudado o invertido en instrumentos indexados." },
      { name: "ipc_indice", type: "DOUBLE", role: "Métrica", significado: "Índice General de Precios al Consumidor empalmado (Base 2023=100).", contable: "Índice de Precios", interpretacion: "Nivel general de precios de la canasta representativa de consumo familiar calculada por el INE y empalmada por el BCCh." },
      { name: "ipc_var_mensual", type: "DOUBLE", role: "Métrica", significado: "Variación porcentual mensual del IPC (%).", contable: "Inflación Mensual", interpretacion: "Ritmo de incremento mensual de precios; alimenta directamente el cálculo diario de la UF para el periodo siguiente." },
      { name: "ipc_var_anual", type: "DOUBLE", role: "Métrica", significado: "Variación porcentual interanual (últimos 12 meses) del IPC (%).", contable: "Inflación Anual V12", interpretacion: "Métrica rectora de la política monetaria. El BCCh tiene un mandato legal con meta de inflación centrada en 3.0% anual en un horizonte de política de 2 años." },
      { name: "imacec_empalmado", type: "DOUBLE", role: "Métrica", significado: "Índice Mensual de Actividad Económica Total empalmado (Base 2018=100).", contable: "Índice Actividad Económica", interpretacion: "Aproximación mensual al Producto Interno Bruto (PIB). Cubre el 90% de los bienes y servicios de las cuentas nacionales." },
      { name: "imacec_no_minero", type: "DOUBLE", role: "Métrica", significado: "IMACEC No Minero empalmado (Base 2018=100).", contable: "Actividad No Minera", interpretacion: "Aísla la actividad de comercio, servicios, manufactura y construcción de la volatilidad extractiva de la minería; mide con mayor pureza el pulso de la demanda interna y el empleo." },
      { name: "imacec_var_anual_pct", type: "DOUBLE", role: "Métrica", significado: "Variación porcentual interanual del IMACEC Total (%).", contable: "Crecimiento Económico", interpretacion: "Tasa de crecimiento o contracción de la economía chilena respecto al mismo mes del año previo." },
      { name: "cobre_spot_usd_lb", type: "DOUBLE", role: "Métrica", significado: "Precio del Cobre Refinado Grado A Bolsa de Metales de Londres (BML) promedio mensual (USD por libra).", contable: "Precio de Commodities", interpretacion: "Principal producto de exportación de Chile (más del 50% de envíos al exterior). Influye decisivamente en los ingresos fiscales del Estado, los términos de intercambio y la fortaleza del peso chileno." },
      { name: "cobre_var_anual_pct", type: "DOUBLE", role: "Métrica", significado: "Variación interanual del precio del cobre (%).", contable: "Ciclo de Commodities", interpretacion: "Indicador del ciclo global de demanda manufacturera e infraestructura (especialmente de China y transición energética)." },
      { name: "eee_ipc_11m", type: "DOUBLE", role: "Métrica", significado: "Mediana de expectativa de inflación a 11 meses según la Encuesta de Expectativas Económicas del BCCh (%).", contable: "Expectativas de Mercado", interpretacion: "Proyección consensuada de los analistas económicos a un año plazo." },
      { name: "eee_ipc_23m", type: "DOUBLE", role: "Métrica", significado: "Mediana de expectativa de inflación a 23 meses según la Encuesta de Expectativas Económicas del BCCh (%).", contable: "Expectativas de Mercado", interpretacion: "Métrica crítica de anclaje de expectativas en el horizonte de política del Banco Central (debe converger a 3.0%)." },
      { name: "desvio_eee_11m_meta_bps", type: "DOUBLE", role: "Métrica", significado: "Diferencia entre la expectativa a 11 meses y la meta del BCCh (3.0%) en puntos base (bps).", contable: "Desvío de Expectativas", interpretacion: "Mide el desalineamiento o desanclaje de las expectativas del mercado frente a la meta formal del Banco Central." }
    ]
  },
  {
    id: "factoring_leasing_maestro",
    name: "factoring_leasing.maestro",
    viewName: "factoring_leasing_maestro",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing",
    norma: "Nómina Oficial CMF & Registro de Valores (RVEMI / FASOC / LISOC)",
    corte: "2026-03",
    frescura: "Al día (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "28 entidades (22 Activas Vigentes + 6 Históricas CMF)",
    descripcion: "Catálogo maestro oficial y exhaustivo de intermediarios financieros no bancarios (Factoring, Leasing y Financiamiento Automotriz), auditado con Algoritmo Módulo 11, estado de vigencia registral, perímetro regulatorio CMF y grupo controlador.",
    origen: "Comisión para el Mercado Financiero (CMF) — Nóminas Oficiales de Sociedades de Factoring (FASOC), Leasing Inmobiliario (LISOC) y Registro de Valores de Emisores (RVEMI).",
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
    id: "factoring_leasing_balance_resumen",
    name: "factoring_leasing.balance_resumen",
    viewName: "factoring_leasing_balance_resumen",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing",
    norma: "CMF FECU IFRS Trimestral",
    corte: "2014-03 a 2026-03",
    frescura: "Al día (49 trimestres)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "878 balances IFRS",
    descripcion: "Serie histórica de totales IFRS desde la API CMF (ver_archivo.php). Sirve para validar el PDF. No es el estado financiero ni reemplaza las líneas de factoring_leasing.balance_lineas.",
    origen: "Comisión para el Mercado Financiero (CMF) — API ver_archivo.php. Validación, no fuente del EEFF.",
    columnas: [
      { name: "id_balance", type: "VARCHAR", role: "PK", significado: "Clave primaria determinística compuesta por RUT y periodo (RUT_YYYYMM).", contable: "No aplica", interpretacion: "Identificador unívoco del reporte financiero trimestral de la entidad." },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Trimestre de corte del reporte contable IFRS (YYYY-MM).", contable: "No aplica", interpretacion: "Eje temporal para series de tiempo trimestrales (marzo, junio, septiembre, diciembre)." },
      { name: "fecha_corte", type: "DATE", role: "Fecha", significado: "Fecha exacta de cierre contable del trimestre.", contable: "No aplica", interpretacion: "Día de corte de devengo y valoración de activos y pasivos." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT de la sociedad de factoring o leasing informante.", contable: "No aplica", interpretacion: "Enlaza el estado financiero con el catálogo maestro de la institución." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Atributo", significado: "Razón social o denominación de la sociedad informante.", contable: "No aplica", interpretacion: "Nombre de la empresa para etiquetado analítico y reportes." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos registrados bajo norma IFRS en millones de pesos (MM$ CLP).", contable: "Costo Amortizado / Devengado", interpretacion: "Representa el tamaño total de la firma en balance. Un crecimiento sostenido refleja expansión de colocaciones comerciales." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de activos convertido a millones de dólares (MM$ USD).", contable: "Valor Razonable / MtM", interpretacion: "Permite comparar la escala del intermediario no bancario con benchmarks internacionales y bancarios en divisa dura." },
      { name: "pasivos_corrientes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Pasivos corrientes exigibles en plazo menor a un año directo de cuentas CMF en MM$ CLP.", contable: "Costo Amortizado / Devengado", interpretacion: "Carga de deuda a corto plazo (líneas de crédito bancarias, pagarés de tesorería y efectos comerciales). Métrica clave de riesgo de liquidez." },
      { name: "pasivos_no_corrientes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Pasivos no corrientes exigibles a más de un año directo de cuentas CMF en MM$ CLP.", contable: "Costo Amortizado / Devengado", interpretacion: "Financiamiento estructural a mediano y largo plazo (bonos corporativos securitizados y créditos bancarios estructurados)." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos directos (suma de corrientes y no corrientes) en MM$ CLP.", contable: "Costo Amortizado / Devengado", interpretacion: "Endeudamiento total exigible a terceros. Obtenido directamente de las cuentas contables informadas a la CMF sin recurrir a ecuaciones residuales." },
      { name: "total_pasivos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos exigibles convertido a millones de USD.", contable: "Valor Razonable / MtM", interpretacion: "Volumen total de endeudamiento expresado en moneda extranjera para análisis de solvencia." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto atribuible a los propietarios de la entidad en MM$ CLP.", contable: "Valor de Mercado Neto", interpretacion: "Capital propio y reservas que respaldan la operación y absorben contingencias de incobrabilidad de cartera." },
      { name: "patrimonio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto convertido a millones de USD.", contable: "Valor Razonable / MtM", interpretacion: "Base de capital propio valorizada en moneda internacional." },
      { name: "cartera_credito_m_clp", type: "DOUBLE", role: "Métrica", significado: "Colocaciones de crédito en factoring y contratos de leasing en MM$ CLP.", contable: "Costo Amortizado / Devengado", interpretacion: "Activo generador de ingresos: masa de facturas por cobrar y contratos de arrendamiento financiero con empresas y personas." },
      { name: "cartera_credito_m_usd", type: "DOUBLE", role: "Métrica", significado: "Cartera de crédito convertida a millones de USD.", contable: "Valor Razonable / MtM", interpretacion: "Volumen de colocaciones no bancarias en divisa dura para comparación sectorial." },
      { name: "activos_liquidos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Efectivo, equivalentes de efectivo y depósitos a corto plazo en MM$ CLP.", contable: "Valor Razonable / MtM", interpretacion: "Colchón de tesorería inmediata para cubrir desfases operacionales y desembolsos diarios." },
      { name: "activos_liquidos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Activos líquidos convertidos a millones de USD.", contable: "Valor Razonable / MtM", interpretacion: "Disponibilidad inmediata de caja en moneda internacional." }
    ]
  },
  {
    id: "factoring_leasing_eeff_documentos",
    name: "factoring_leasing.eeff_documentos",
    viewName: "factoring_leasing_eeff_documentos",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "CMF IFRS — PDF Estados financieros, Información Financiera",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "10 documentos",
    descripcion: "Los diez EEFF de factoring y leasing de marzo 2026 bajados desde la ficha CMF, pestaña Información Financiera, buscador de periodo. Consolidados: Forum, Tanner, GM Financial, Penta, Primus y Eurocapital. Individuales, porque el consolidado no está publicado: Security, Santander Consumer, Autofin y ST Capital. Tanner y Eurocapital quedan parciales. Security, Penta y Primus tienen huecos marcados: el detalle no se completa a mano.",
    origen: "PDF «Estados financieros» de safec_ifrs_verarchivo.php, llegado desde entidad.php pestania=3.",
    columnas: [
      { name: "id_documento", type: "VARCHAR", role: "PK", significado: "RUT y periodo del PDF.", contable: "No aplica", interpretacion: "Un documento por sociedad y corte." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT de la sociedad.", contable: "No aplica", interpretacion: "Enlaza con el maestro." },
      { name: "razon_social", type: "VARCHAR", role: "Atributo", significado: "Razón social del PDF.", contable: "No aplica", interpretacion: "Nombre del emisor." },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Corte YYYY-MM.", contable: "No aplica", interpretacion: "2026-03." },
      { name: "tipo_eeff", type: "VARCHAR", role: "Atributo", significado: "Consolidado o Individual, el que publica el buscador.", contable: "No aplica", interpretacion: "No se compara un individual con un consolidado de la API." },
      { name: "url_pdf", type: "VARCHAR", role: "Atributo", significado: "Enlace Estados financieros (PDF).", contable: "No aplica", interpretacion: "Token de la CMF; puede expirar." },
      { name: "estado_extraccion", type: "VARCHAR", role: "Atributo", significado: "PDF_CON_NOTAS, PDF_CARATULA, PDF_PARCIAL, PDF_PARCIAL_CON_NOTAS o PDF_NOTA_DIFIERE.", contable: "No aplica", interpretacion: "Parcial significa que faltan líneas, no que se inventaron. La API no cambia este estado." },
      { name: "cuadre_caratula", type: "VARCHAR", role: "Atributo", significado: "OK, FALTAN_LINEAS o INCOMPLETO.", contable: "No aplica", interpretacion: "FALTAN_LINEAS: un subtotal del PDF no suma con las líneas publicadas. No se rellena." },
      { name: "cuadre_resultados", type: "VARCHAR", role: "Atributo", significado: "OK, FALTAN_LINEAS o INCOMPLETO.", contable: "No aplica", interpretacion: "El corte y el comparativo se suman por separado. Una diferencia no se completa." },
      { name: "hueco", type: "VARCHAR", role: "Atributo", significado: "Qué línea no cierra, en miles de pesos.", contable: "No aplica", interpretacion: "Vacío si el detalle publicado suma. No es una cifra estimada." },
      { name: "tablas_leidas", type: "VARCHAR", role: "Atributo", significado: "Notas comunes cuya tabla de montos se leyó.", contable: "No aplica", interpretacion: "Vacío si solo está la carátula." },
      { name: "estado_api", type: "VARCHAR", role: "Atributo", significado: "SIN_TIPO si los números calzan pero la API no trae tipo.", contable: "No aplica", interpretacion: "No es un rechazo del PDF." }
    ]
  },
  {
    id: "factoring_leasing_balance_lineas",
    name: "factoring_leasing.balance_lineas",
    viewName: "factoring_leasing_balance_lineas",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "NIC 1 — Estado de situación financiera",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "223 líneas",
    descripcion: "Líneas del estado de situación financiera tal como salen del PDF, en miles de pesos. Si el PDF no separa corriente y no corriente, la tabla tampoco. La visualización HTML no se publica cuando difiere del PDF.",
    origen: "PDF Estados financieros, Información Financiera CMF.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Identificador de la línea.", contable: "No aplica", interpretacion: "Una fila por cuenta publicada." },
      { name: "nombre_cuenta", type: "VARCHAR", role: "Atributo", significado: "Nombre literal de la cuenta en el PDF.", contable: "Cuenta IFRS", interpretacion: "No se normaliza al nombre de la API." },
      { name: "nota_ref", type: "VARCHAR", role: "Atributo", significado: "Número de nota citado en la carátula.", contable: "Nota", interpretacion: "Vacío si el PDF no cita nota." },
      { name: "monto_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo del corte en miles de pesos.", contable: "M$", interpretacion: "Unidad del PDF, no millones." },
      { name: "monto_m_clp", type: "DOUBLE", role: "Métrica", significado: "El mismo saldo en millones, para comparar con la API.", contable: "MM$", interpretacion: "miles / 1000." },
      { name: "monto_comparativo_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Columna comparativa del PDF, en miles.", contable: "M$", interpretacion: "Vacío si esa columna no se leyó." }
    ]
  },
  {
    id: "factoring_leasing_resultados_lineas",
    name: "factoring_leasing.resultados_lineas",
    viewName: "factoring_leasing_resultados_lineas",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "NIC 1 — Estado de resultados",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "120 líneas",
    descripcion: "Estado de resultados del PDF, en miles de pesos. Los gastos van con signo negativo, como el paréntesis del PDF. Penta no trae la línea de gasto de administración porque el corte de página la partió y no se completa a mano.",
    origen: "PDF Estados financieros, Información Financiera CMF.",
    columnas: [
      { name: "nombre_cuenta", type: "VARCHAR", role: "Atributo", significado: "Nombre literal de la línea de resultado.", contable: "Resultado", interpretacion: "Ingreso, costo, gasto o resultado." },
      { name: "monto_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Monto del trimestre en miles de pesos.", contable: "M$", interpretacion: "Negativo si el PDF lo muestra entre paréntesis." },
      { name: "nota_ref", type: "VARCHAR", role: "Atributo", significado: "Nota citada en el estado de resultados.", contable: "Nota", interpretacion: "Vacío si no hay cita." }
    ]
  },
  {
    id: "factoring_leasing_notas_indice",
    name: "factoring_leasing.notas_indice",
    viewName: "factoring_leasing_notas_indice",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "Notas a los EEFF IFRS",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "273 notas",
    descripcion: "Índice de notas que cada PDF publica. La llave es el nombre, no el número: nota_canonica y tabla salen del diccionario de alias. extraida=1 solo si la tabla de montos se leyó. Un 0 no es un cero contable.",
    origen: "Índice del PDF Estados financieros.",
    columnas: [
      { name: "numero_nota", type: "INTEGER", role: "Atributo", significado: "Número de nota.", contable: "Nota", interpretacion: "El número cambia entre sociedades; la familia no." },
      { name: "titulo_nota", type: "VARCHAR", role: "Atributo", significado: "Título publicado.", contable: "Nota", interpretacion: "Texto del índice." },
      { name: "pagina", type: "VARCHAR", role: "Atributo", significado: "Página del PDF, si el índice la trae.", contable: "No aplica", interpretacion: "Vacío si el índice no numeró la página." },
      { name: "nota_canonica", type: "VARCHAR", role: "Atributo", significado: "Nombre económico del alias. Si es una de las ocho comunes, coincide con tabla.", contable: "No aplica", interpretacion: "Préstamos que devengan intereses y otros pasivos financieros son la misma tabla." },
      { name: "tabla", type: "VARCHAR", role: "Atributo", significado: "Una de las ocho notas comunes, o vacío.", contable: "No aplica", interpretacion: "Vacío no significa que la nota no exista: no es de las ocho." },
      { name: "extraida", type: "INTEGER", role: "Métrica", significado: "1 si hay líneas de monto; 0 si solo se conoce el título.", contable: "No aplica", interpretacion: "0 no es un cero contable: es una nota no leída." }
    ]
  },
  {
    id: "factoring_leasing_nota_lineas",
    name: "factoring_leasing.nota_lineas",
    viewName: "factoring_leasing_nota_lineas",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "Retirada",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "0 — retirada",
    descripcion: "Bolsa retirada. Ninguna nota vive aquí. El efectivo del PDF está en factoring_leasing.nota_efectivo y los deudores en factoring_leasing.nota_deudores. Las otras seis comunes están marcadas en notas_cobertura, sin columnas inventadas.",
    origen: "PDF individual de Factoring Security, páginas 24 y 26.",
    columnas: [
      { name: "numero_nota", type: "INTEGER", role: "Atributo", significado: "4 efectivo o 5 deudores.", contable: "Nota", interpretacion: "Cuadra con la carátula." },
      { name: "concepto", type: "VARCHAR", role: "Atributo", significado: "Fila de la nota: caja, bancos, factura, confirming, crédito.", contable: "Desglose", interpretacion: "Texto del PDF." },
      { name: "detalle", type: "VARCHAR", role: "Atributo", significado: "Otras columnas numéricas, colocación y provisión en la Nota 5.", contable: "Desglose", interpretacion: "El neto está en monto_miles_clp." },
      { name: "monto_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo o neto del corte, en miles.", contable: "M$", interpretacion: "La suma de la Nota 4 cuadra con efectivo. La suma de netos de la Nota 5 cuadra con deudores." },
      { name: "calidad", type: "VARCHAR", role: "Atributo", significado: "extraida_documento.", contable: "No aplica", interpretacion: "No hay calidad estimada en esta tabla." }
    ]
  },

  {
    id: "factoring_leasing_notas_cobertura",
    name: "factoring_leasing.notas_cobertura",
    viewName: "factoring_leasing_notas_cobertura",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "Ocho notas comunes, por nombre",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "80 marcas",
    descripcion: "Una fila por PDF y por nota común. leida solo si la tabla de montos se leyó. en_indice_sin_tabla significa que el título está y la tabla no se leyó: no se inventan columnas. indice_incompleto (Eurocapital) no niega la nota. ausente solo si el índice parte en 1 y aun así no trae el título.",
    origen: "Índice del PDF, clasificado por alias. No por número de nota.",
    columnas: [
      { name: "tabla", type: "VARCHAR", role: "Atributo", significado: "efectivo, deudores, pasivos_financieros, cuentas_por_pagar, relacionadas, impuestos, patrimonio o ppe.", contable: "Nota", interpretacion: "La misma tabla aunque el número cambie de año." },
      { name: "numeros_nota", type: "VARCHAR", role: "Atributo", significado: "Números publicados, separados por coma si hay más de una nota.", contable: "Nota", interpretacion: "Security tiene dos notas de pasivos financieros y dos de impuestos." },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "leida, en_indice_sin_tabla, indice_incompleto, esquema_pendiente o ausente.", contable: "No aplica", interpretacion: "La marca de que no se leyó. No es un monto cero." },
      { name: "cuadre", type: "VARCHAR", role: "Atributo", significado: "OK si el total de la nota cuadra con la carátula.", contable: "M$", interpretacion: "SIN_NOTA si la tabla no se leyó. No se ajusta." },
      { name: "extraida", type: "INTEGER", role: "Métrica", significado: "1 si hay filas de monto.", contable: "No aplica", interpretacion: "Marzo 2026: solo Security, efectivo y deudores." }
    ]
  },
  {
    id: "factoring_leasing_nota_efectivo",
    name: "factoring_leasing.nota_efectivo",
    viewName: "factoring_leasing_nota_efectivo",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "Nota de efectivo y equivalentes, PDF",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "4 líneas",
    descripcion: "Nota de efectivo leída del PDF. Hoy solo Factoring Security, marzo 2026. concepto, saldo del corte y saldo comparativo. El total 11.283.111 cuadra con la carátula. Un guion del PDF es cero, no un hueco. No es la serie de porcentajes de De Interés.",
    origen: "PDF individual de Factoring Security, nota de efectivo y equivalentes.",
    columnas: [
      { name: "concepto", type: "VARCHAR", role: "Atributo", significado: "Fila publicada: caja, fondos mutuos, bancos o total.", contable: "Efectivo", interpretacion: "Texto del PDF." },
      { name: "saldo_miles", type: "DOUBLE", role: "Métrica", significado: "Saldo del corte, en miles.", contable: "M$", interpretacion: "La suma de las filas que no son total cuadra con la carátula." },
      { name: "saldo_comparativo_miles", type: "DOUBLE", role: "Métrica", significado: "Saldo de la columna comparativa.", contable: "M$", interpretacion: "Vacío si el PDF no trae esa columna." },
      { name: "es_total", type: "INTEGER", role: "Atributo", significado: "1 si la fila es el total del PDF.", contable: "No aplica", interpretacion: "No se suma dos veces." }
    ]
  },
  {
    id: "factoring_leasing_nota_deudores",
    name: "factoring_leasing.nota_deudores",
    viewName: "factoring_leasing_nota_deudores",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "Nota de deudores comerciales, PDF",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "PDF",
    ultimaActualizacion: "2026-09-26",
    registros: "16 líneas",
    descripcion: "Nota de deudores leída del PDF. Hoy solo Factoring Security, marzo 2026. producto, colocación, provisión y neto. El que cuadra con la carátula es el neto, 648.223.161. Colocación y provisión no se estiman si el PDF no las trae. No es la serie de morosidad de De Interés.",
    origen: "PDF individual de Factoring Security, nota de deudores comerciales.",
    columnas: [
      { name: "concepto", type: "VARCHAR", role: "Atributo", significado: "Producto publicado: factura, confirming, crédito u otro.", contable: "Cartera", interpretacion: "Texto del PDF." },
      { name: "colocacion_miles", type: "DOUBLE", role: "Métrica", significado: "Colocación del corte, en miles.", contable: "M$", interpretacion: "Vacío si esa columna no está." },
      { name: "provision_miles", type: "DOUBLE", role: "Métrica", significado: "Provisión del corte, en miles, con el signo del PDF.", contable: "M$", interpretacion: "No se completa con un porcentaje." },
      { name: "neto_miles", type: "DOUBLE", role: "Métrica", significado: "Neto del corte, en miles.", contable: "M$", interpretacion: "Es el monto que cuadra con deudores de la carátula." },
      { name: "es_total", type: "INTEGER", role: "Atributo", significado: "1 si la fila es el total del PDF.", contable: "No aplica", interpretacion: "No se suma dos veces." }
    ]
  },
  {
    id: "factoring_leasing_validacion_api",
    name: "factoring_leasing.validacion_api",
    viewName: "factoring_leasing_validacion_api",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing — EEFF",
    norma: "Chequeo PDF contra API",
    corte: "2026-03",
    frescura: "Marzo 2026",
    modo: "Validación",
    ultimaActualizacion: "2026-09-26",
    registros: "60 chequeos",
    descripcion: "Compara totales del PDF, en millones, con factoring_leasing.balance_resumen. Tolerancia 1 millón. La serie API no trae tipo consolidado o individual, así que un cuadre numérico queda SIN_TIPO y no OK: no se finge que el tipo coincidió. numeros=cuadra dice que las cifras calzan. SOLO_API significa que el PDF no publicó esa línea. La API no rellena.",
    origen: "PDF versus API ver_archivo.php, mismo tipo de estado.",
    columnas: [
      { name: "concepto", type: "VARCHAR", role: "Atributo", significado: "total_activos, efectivo, deudores_corrientes, pasivos o patrimonio.", contable: "Total", interpretacion: "Solo totales, nunca el desglose de la nota." },
      { name: "monto_documento_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total del PDF en millones.", contable: "MM$", interpretacion: "Vacío si el PDF no trae la línea." },
      { name: "monto_api_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de la API en millones.", contable: "MM$", interpretacion: "Referencia, no reemplazo." },
      { name: "diff_m_clp", type: "DOUBLE", role: "Métrica", significado: "Documento menos API.", contable: "MM$", interpretacion: "DIFIERE si el absoluto pasa de 1." },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "OK, DIFIERE, SOLO_API o SIN_API.", contable: "No aplica", interpretacion: "El PDF gana si hay diferencia." }
    ]
  },
  {
    id: "factoring_leasing_nota_efectivo_detalle",
    name: "Retirada: efectivo por porcentajes",
    viewName: "factoring_leasing_nota_efectivo_detalle",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing",
    norma: "No es una nota",
    corte: "Retirada del monitor",
    frescura: "No se carga",
    modo: "Retirada",
    ultimaActualizacion: "2026-09-26",
    registros: "No está en el menú",
    descripcion: "Retirada del menú y de DuckDB. No es el PDF: reparte el efectivo de la API con porcentajes fijos. La nota leída está en factoring_leasing.nota_efectivo.",
    origen: "Script 02_extract_factoring_leasing_notas_series.py. No proviene del PDF de Información Financiera.",
    columnas: [
      { name: "concepto", type: "VARCHAR", role: "Atributo", significado: "Categoría inventada por el reparto. No es una línea del PDF.", contable: "No aplica", interpretacion: "No usar." }
    ]
  },
  {
    id: "factoring_leasing_cartera_morosidad_detalle",
    name: "Retirada: cartera por porcentajes",
    viewName: "factoring_leasing_cartera_morosidad_detalle",
    sector: "factoring_leasing",
    sectorLabel: "Factoring & Leasing",
    norma: "No es una nota",
    corte: "Retirada del monitor",
    frescura: "No se carga",
    modo: "Retirada",
    ultimaActualizacion: "2026-09-26",
    registros: "No está en el menú",
    descripcion: "Retirada del menú y de DuckDB. No es el PDF: reparte la cartera de la API con porcentajes fijos de producto, tramo y etapa. El desglose leído está en factoring_leasing.nota_deudores.",
    origen: "Script 02_extract_factoring_leasing_notas_series.py. No proviene del PDF de Información Financiera.",
    columnas: [
      { name: "etapa_ifrs9", type: "VARCHAR", role: "Atributo", significado: "Etapa inventada por el reparto. No sale de una nota.", contable: "No aplica", interpretacion: "No usar como IFRS 9." }
    ]
  },
  // =========================================================================
  // CORREDORAS DE BOLSA (CMF / Mercado de Valores)
  // =========================================================================
  {
    id: "corredoras_bolsa_maestro",
    name: "corredoras.maestro",
    viewName: "corredoras_bolsa_maestro",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa",
    norma: "CMF Chile — Registro de Corredores de Bolsa (Ley 18.045)",
    corte: "2014-03 a 2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "47 entidades",
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
    registros: "1.586 balances",
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
    name: "corredoras.universo",
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
    name: "corredoras.caratula_eeff",
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
    id: "corredoras_repos_contrapartes_tasas",
    name: "corredoras.repos_contrapartes",
    viewName: "corredoras_repos_contrapartes_tasas",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa",
    norma: "CMF Chile — Notas Explicativas EEFF (Nota 12/20/23 - Pactos REPO)",
    corte: "2018-12 a 2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-24",
    registros: "2.6k contratos",
    descripcion: "Desglose Nivel 2 del mercado REPO: segmentación por contraparte (institucionales, intermediarios, empresas, personas), tasas ponderadas y vencimiento (hasta 7 días vs más de 7 días).",
    origen: "Comisión para el Mercado Financiero (CMF) — Notas a los Estados Financieros de Corredoras.",
    columnas: [
      { name: "id_pacto", type: "VARCHAR", role: "PK", significado: "Identificador del registro de pacto {periodo}_{rut}_{segmento}_{tipo}.", contable: "No aplica", interpretacion: "Identificador primario de la fila segmentada." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo trimestral YYYY-MM.", contable: "No aplica", interpretacion: "Eje temporal del contrato." },
      { name: "fecha_corte", type: "DATE", role: "Dimensión", significado: "Fecha de corte del trimestre.", contable: "No aplica", interpretacion: "Fecha de cálculo de tasas y saldos." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT oficial de la corredora de bolsa.", contable: "No aplica", interpretacion: "Vínculo a maestro." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la corredora.", contable: "No aplica", interpretacion: "Entidad intermediaria." },
      { name: "tipo_operacion", type: "VARCHAR", role: "Dimensión", significado: "Tipo de pacto ('Simultánea / Retroventa (CRV)' o 'Retrocompra (VRC)').", contable: "Clasificación Operativa", interpretacion: "Distingue operaciones activas (préstamo con colateral) de pasivas (fondeo)." },
      { name: "segmento_contraparte", type: "VARCHAR", role: "Dimensión", significado: "Tipo de contraparte regulada ('Personas naturales', 'Personas jurídicas', 'Intermediarios de valores', 'Inversionistas institucionales', 'Partes relacionadas', 'Totales').", contable: "Segmentación CMF", interpretacion: "Identifica el sector económico que provee o demanda liquidez." },
      { name: "tasa_promedio_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés promedio ponderada de la operación (%).", contable: "Tasa Ponderada", interpretacion: "Costo financiero o rendimiento del pacto a la fecha de corte." },
      { name: "monto_hasta_7d_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto pactado con vencimiento menor o igual a 7 días en miles de CLP.", contable: "Liquidez Ultracorta", interpretacion: "Pactos a plazo ultracorto (overnight y 7 días)." },
      { name: "monto_mas_7d_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto pactado con vencimiento mayor a 7 días en miles de CLP.", contable: "Plazo Corto", interpretacion: "Pactos a plazos superiores a una semana." },
      { name: "monto_total_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto total pactado en miles de CLP.", contable: "Principal Pactado", interpretacion: "Volumen de financiamiento total pactado con la contraparte." },
      { name: "monto_total_m_usd", type: "DOUBLE", role: "Métrica", significado: "Monto total pactado en millones de USD.", contable: "Principal Pactado", interpretacion: "Volumen expresado en divisa internacional." },
      { name: "valor_razonable_garantia_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valor razonable del activo subyacente / colateral en miles de CLP.", contable: "Valor de Mercado", interpretacion: "Valor de mercado de los instrumentos entregados/recibidos en garantía." },
      { name: "valor_razonable_garantia_m_usd", type: "DOUBLE", role: "Métrica", significado: "Valor del subyacente en millones de USD.", contable: "Valor de Mercado", interpretacion: "Cobertura de colateral en moneda extranjera." }
    ]
  },
  {
    id: "corredoras_repos_colaterales_detalle",
    name: "corredoras.repos_colaterales",
    viewName: "corredoras_repos_colaterales_detalle",
    sector: "corredoras_bolsa",
    sectorLabel: "Corredoras de Bolsa",
    norma: "CMF Chile — Notas Explicativas EEFF (Nota 19.b / 22.b / 30 - Colaterales)",
    corte: "2018-12 a 2026-06",
    frescura: "Al día (Trimestral)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-24",
    registros: "2.6k colaterales",
    descripcion: "Detalle Nivel 3 de colaterales: nemotécnicos de acciones (BCI, BSANTANDER, SQM-B, FALABELLA, etc.), cuotas de fondos de inversión y bonos recibidos o entregados en garantía para operaciones simultáneas y de retroventa.",
    origen: "Comisión para el Mercado Financiero (CMF) — Detalle de Títulos en Garantía bajo IFRS.",
    columnas: [
      { name: "id_colateral", type: "VARCHAR", role: "PK", significado: "Identificador del colateral {periodo}_{rut}_{nemotecnico}_{indice}.", contable: "No aplica", interpretacion: "Clave única del título bajo pacto." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo trimestral contable YYYY-MM.", contable: "No aplica", interpretacion: "Eje temporal del balance." },
      { name: "fecha_corte", type: "DATE", role: "Dimensión", significado: "Fecha de corte del reporte.", contable: "No aplica", interpretacion: "Fecha de valoración del activo colateral." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT oficial de la corredora de bolsa.", contable: "No aplica", interpretacion: "Enlace al maestro." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social oficial de la corredora.", contable: "No aplica", interpretacion: "Entidad intermediaria custodia de la garantía." },
      { name: "nemotecnico", type: "VARCHAR", role: "Dimensión", significado: "Nemotécnico bursátil oficial del instrumento subyacente (ej. SQM-B, BCI, BSANTANDER, CENCOSUD, LTM, IRFEIIF).", contable: "Identificador de Activo", interpretacion: "Símbolo de la acción o valor objeto de la simultánea o pacto." },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Dimensión", significado: "Tipo de instrumento ('Acción Nacional (IRV)' o 'Cuota de Fondo de Inversión (CFI)').", contable: "Clasificación de Activo", interpretacion: "Familia de activo financiero utilizada como colateral." },
      { name: "unidades_pactadas", type: "DOUBLE", role: "Métrica", significado: "Cantidad física de acciones o títulos entregados/recibidos en garantía.", contable: "Unidades Físicas", interpretacion: "Número de acciones bajo compromiso de retrocompra o retroventa." },
      { name: "monto_pactado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto pactado total valorizado en miles de CLP.", contable: "Monto Nominal / Liquidación", interpretacion: "Monto del compromiso financiero respaldado por el nemotécnico." },
      { name: "monto_pactado_m_usd", type: "DOUBLE", role: "Métrica", significado: "Monto pactado en millones de USD.", contable: "Monto Nominal", interpretacion: "Valorización del compromiso en divisa." },
      { name: "valor_mercado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valor de mercado corriente del colateral en miles de CLP.", contable: "Mark-to-Market", interpretacion: "Valor de tasación de mercado de los títulos en custodia." },
      { name: "valor_mercado_m_usd", type: "DOUBLE", role: "Métrica", significado: "Valor de mercado en millones de USD.", contable: "Mark-to-Market", interpretacion: "Cobertura de mercado en divisa internacional." }
    ]
  },
  // =========================================================================
  // SECURITIZADORAS (CMF / Ley 18.045 Título XVIII)
  // =========================================================================
  {
    id: "securitizadoras_maestro",
    name: "securitizadoras.maestro",
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
    id: "patrimonios_separados_balance_lineas",
    name: "patrimonios.balance_lineas",
    viewName: "patrimonios_separados_balance_lineas",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Taxonomía FECU y Ley 18.045",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral FECU Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "23,600 filas",
    descripcion: "Balance General completo línea por línea de Patrimonios Separados. Registra con precisión atómica cuentas de activo circulante (disponible, cartera securitizada corto plazo, provisiones), activo largo plazo, pasivo circulante y largo plazo (títulos de deuda, saldo de precio, sobrecolateral) y excedentes/patrimonio neto, con cuadre contable exacto al peso verificado en el 100% de los balances.",
    origen: "Comisión para el Mercado Financiero (CMF) - Balances FECU Oficiales.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Clave primaria única de la línea contable (id_registro_BAL_cuenta).", contable: "No aplica", interpretacion: "Identificador atómico de registro." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador del patrimonio separado (rut_emision).", contable: "No aplica", interpretacion: "Vehículo autónomo emisor." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Período contable en formato YYYYMM.", contable: "No aplica", interpretacion: "Cierre trimestral oficial." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha de cierre en formato YYYY-MM-DD.", contable: "No aplica", interpretacion: "Fecha de corte del balance." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT con dígito verificador Módulo 11 de la sociedad securitizadora gestora.", contable: "No aplica", interpretacion: "Administradora responsable." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social de la securitizadora.", contable: "No aplica", interpretacion: "Entidad fiduciaria." },
      { name: "codigo_emision", type: "VARCHAR", role: "Atributo", significado: "Código nemotécnico de la emisión o patrimonio separado.", contable: "No aplica", interpretacion: "Emisión inscrita en CMF." },
      { name: "tipo_balance", type: "VARCHAR", role: "Clasificación", significado: "Agrupación contable (ACTIVO_CIRCULANTE, OTROS_ACTIVOS, PASIVO_CIRCULANTE, PASIVO_LARGO_PLAZO, TOTAL_BALANCE).", contable: "Clasificación CMF", interpretacion: "Rubro mayor del balance." },
      { name: "codigo_cuenta", type: "VARCHAR", role: "Atributo", significado: "Código numérico FECU oficial (10.000, 11.020, 20.000, etc.).", contable: "Catálogo FECU", interpretacion: "Cuenta del plan de cuentas CMF." },
      { name: "nombre_cuenta", type: "VARCHAR", role: "Atributo", significado: "Glosa oficial estandarizada de la cuenta contable.", contable: "Glosa contable", interpretacion: "Concepto del activo o pasivo." },
      { name: "monto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto del saldo contable expresado en miles de pesos (M$ CLP).", contable: "Moneda de reporte", interpretacion: "Cifra en M$." },
      { name: "monto_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Monto equivalente en millones de pesos chilenos (MM$ CLP).", contable: "Métrica agregada", interpretacion: "Monto escalado para análisis macro." }
    ]
  },
  {
    id: "patrimonios_separados_excedentes_lineas",
    name: "patrimonios.excedentes_lineas",
    viewName: "patrimonios_separados_excedentes_lineas",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Taxonomía FECU y Ley 18.045",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral FECU Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "16,312 filas",
    descripcion: "Estado de Determinación de Excedentes / Resultados completo cuenta por cuenta de Patrimonios Separados. Contiene el desglose exhaustivo de ingresos operacionales (intereses y reajustes del activo securitizado), ingresos financieros (inversiones y pactos), gastos operacionales (remuneraciones de administración, custodia, auditoría, clasificación de riesgo) y gastos financieros por bonos emitidos.",
    origen: "Comisión para el Mercado Financiero (CMF) - Estados de Determinación de Excedentes FECU.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Clave primaria única de la línea de resultado (id_registro_EXC_cuenta).", contable: "No aplica", interpretacion: "Identificador atómico de registro." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador del patrimonio separado.", contable: "No aplica", interpretacion: "Vehículo emisor." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Período contable en formato YYYYMM.", contable: "No aplica", interpretacion: "Cierre trimestral." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha de corte en formato YYYY-MM-DD.", contable: "No aplica", interpretacion: "Fecha de reporte." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT validado Módulo 11 de la sociedad securitizadora.", contable: "No aplica", interpretacion: "Administradora." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social de la securitizadora.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_emision", type: "VARCHAR", role: "Atributo", significado: "Código nemotécnico de la emisión.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "tipo_flujo", type: "VARCHAR", role: "Clasificación", significado: "Naturaleza del flujo (INGRESO_OPERACIONAL, INGRESO_FINANCIERO, GASTO_OPERACIONAL, GASTO_FINANCIERO, REMUNERACIONES_ADMINISTRACION, TOTAL_EXCEDENTES).", contable: "Rubro de resultados", interpretacion: "Categoría económica." },
      { name: "codigo_cuenta", type: "VARCHAR", role: "Atributo", significado: "Código numérico FECU oficial (35.100 a 35.300).", contable: "Cuenta FECU", interpretacion: "Línea del estado de excedentes." },
      { name: "nombre_cuenta", type: "VARCHAR", role: "Atributo", significado: "Glosa oficial de la cuenta de ingresos o gastos.", contable: "Glosa contable", interpretacion: "Concepto del flujo." },
      { name: "monto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto del flujo o excedente en miles de pesos (M$ CLP).", contable: "Monto M$", interpretacion: "Importe del período." },
      { name: "monto_mm_clp", type: "DOUBLE", role: "Métrica", significado: "Monto del flujo en millones de pesos (MM$ CLP).", contable: "Monto MM$", interpretacion: "Importe en MM$." }
    ]
  },
  {
    id: "patrimonios_separados_nota_cartera_detalle",
    name: "patrimonios.nota_cartera",
    viewName: "patrimonios_separados_nota_cartera_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Nota Explicativa Cartera Securitizada",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "808 filas",
    descripcion: "Detalle relacional de la Nota Explicativa de Cartera Securitizada. Especifica los activos subyacentes aportados (mutuos hipotecarios, contratos de leasing habitacional, créditos comerciales), originador acreedor, número de deudores, tasa de interés promedio ponderada, plazo residual promedio y valor presente de los contratos.",
    origen: "Comisión para el Mercado Financiero (CMF) - Notas a los Estados Financieros.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Clave primaria única del registro de cartera.", contable: "No aplica", interpretacion: "ID línea." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador del patrimonio separado.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Período YYYYMM.", contable: "No aplica", interpretacion: "Período." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha YYYY-MM-DD.", contable: "No aplica", interpretacion: "Fecha corte." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT administradora.", contable: "No aplica", interpretacion: "RUT gestora." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social securitizadora.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_emision", type: "VARCHAR", role: "Atributo", significado: "Código emisión.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "tipo_activo", type: "VARCHAR", role: "Atributo", significado: "Tipo de activo colateral (Mutuos Hipotecarios, Leasing Habitacional, etc.).", contable: "Activo subyacente", interpretacion: "Naturaleza del crédito." },
      { name: "originador", type: "VARCHAR", role: "Atributo", significado: "Institución financiera o entidad originadora del crédito cedido.", contable: "Originador", interpretacion: "Banco o entidad cedente." },
      { name: "numero_deudores", type: "BIGINT", role: "Métrica", significado: "Cantidad de deudores o contratos que componen la cartera.", contable: "Conteo", interpretacion: "Número de contratos activos." },
      { name: "tasa_interes_promedio_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés promedio ponderada pactada en la cartera.", contable: "Tasa promedio", interpretacion: "Tasa anualizada %." },
      { name: "plazo_promedio_residual_meses", type: "DOUBLE", role: "Métrica", significado: "Plazo promedio remanente de amortización en meses.", contable: "Plazo residual", interpretacion: "Duración en meses." },
      { name: "valor_presente_mclp", type: "DOUBLE", role: "Métrica", significado: "Valor presente / saldo contable de la cartera en miles de pesos (M$ CLP).", contable: "Valor presente M$", interpretacion: "Saldo insoluto M$." },
      { name: "valor_presente_mmclp", type: "DOUBLE", role: "Métrica", significado: "Valor presente equivalente en millones de pesos (MM$ CLP).", contable: "Valor presente MM$", interpretacion: "Saldo en MM$." }
    ]
  },
  {
    id: "patrimonios_separados_nota_morosidad_detalle",
    name: "patrimonios.nota_morosidad",
    viewName: "patrimonios_separados_nota_morosidad_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Nota Explicativa Morosidad y Provisiones",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "1,242 filas",
    descripcion: "Detalle relacional de la Nota Explicativa de Morosidad y Provisiones. Clasifica la cartera de créditos y mutuos por tramos de atraso (Al día, 1-30 días, 31-60 días, 61-90 días, 91-180 días, >180 días, Cobranza Judicial), número de deudores en cada tramo, monto de cartera expuesta y provisión contable constituida.",
    origen: "Comisión para el Mercado Financiero (CMF) - Notas a los Estados Financieros.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Clave primaria única del tramo de morosidad.", contable: "No aplica", interpretacion: "ID línea." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador del patrimonio separado.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Período YYYYMM.", contable: "No aplica", interpretacion: "Período." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha YYYY-MM-DD.", contable: "No aplica", interpretacion: "Fecha corte." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT administradora.", contable: "No aplica", interpretacion: "RUT gestora." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social securitizadora.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_emision", type: "VARCHAR", role: "Atributo", significado: "Código emisión.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "tramo_mora", type: "VARCHAR", role: "Clasificación", significado: "Tramo de morosidad estandarizado (Al día, 1-30, 31-60, 61-90, 91-180, >180 días, Cobranza Judicial).", contable: "Antigüedad mora", interpretacion: "Calidad crediticia." },
      { name: "numero_deudores", type: "BIGINT", role: "Métrica", significado: "Número de deudores en el tramo.", contable: "Conteo", interpretacion: "Cantidad de créditos." },
      { name: "monto_cartera_mclp", type: "DOUBLE", role: "Métrica", significado: "Monto de cartera del tramo en miles de pesos (M$ CLP).", contable: "Saldo cartera", interpretacion: "Monto expuesto M$." },
      { name: "porcentaje_provision_pct", type: "DOUBLE", role: "Métrica", significado: "Porcentaje de provisión aplicado sobre el tramo.", contable: "Tasa provisión", interpretacion: "Tasa de castigo %." },
      { name: "monto_provision_mclp", type: "DOUBLE", role: "Métrica", significado: "Monto de provisión constituida en miles de pesos (M$ CLP).", contable: "Provisión M$", interpretacion: "Cobertura de pérdida esperada." }
    ]
  },
  {
    id: "patrimonios_separados_nota_bonos_detalle",
    name: "patrimonios.nota_bonos",
    viewName: "patrimonios_separados_nota_bonos_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Nota Explicativa Títulos de Deuda",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "498 filas",
    descripcion: "Detalle relacional de la Nota Explicativa de Bonos y Títulos de Deuda de Securitización Emitidos. Contiene las series emitidas (Serie A preferente, Serie B subordinada), nemotécnicos de mercado, moneda/unidad (UF, CLP, USD), tasa de carátula anual pactada, monto colocado original, saldo insoluto en miles de pesos y en UF, y fecha de vencimiento final.",
    origen: "Comisión para el Mercado Financiero (CMF) - Notas a los Estados Financieros.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Clave primaria de la serie de bonos.", contable: "No aplica", interpretacion: "ID línea." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador del patrimonio separado.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Período YYYYMM.", contable: "No aplica", interpretacion: "Período." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha YYYY-MM-DD.", contable: "No aplica", interpretacion: "Fecha corte." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT administradora.", contable: "No aplica", interpretacion: "RUT gestora." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social securitizadora.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_emision", type: "VARCHAR", role: "Atributo", significado: "Código emisión.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "serie", type: "VARCHAR", role: "Atributo", significado: "Serie del bono emitido (Serie A, Serie B, etc.).", contable: "Tranche", interpretacion: "Tramo de subordinación." },
      { name: "nemotecnico", type: "VARCHAR", role: "Atributo", significado: "Código nemotécnico bursátil de negociación.", contable: "Ticker", interpretacion: "Nemotécnico CMF / Bolsa." },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda o unidad de reajuste (UF, CLP, USD).", contable: "Unidad", interpretacion: "Moneda de emisión." },
      { name: "tasa_caratula_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés de carátula anual nominal/real %.", contable: "Cupón", interpretacion: "Tasa del bono %." },
      { name: "monto_colocado_mclp", type: "DOUBLE", role: "Métrica", significado: "Monto colocado original en miles de pesos (M$ CLP).", contable: "Colocación M$", interpretacion: "Emisión inicial." },
      { name: "saldo_insoluto_mclp", type: "DOUBLE", role: "Métrica", significado: "Saldo insoluto vigente en miles de pesos (M$ CLP).", contable: "Pasivo insoluto", interpretacion: "Deuda remanente M$." },
      { name: "saldo_insoluto_uf", type: "DOUBLE", role: "Métrica", significado: "Saldo insoluto expresado en Unidades de Fomento (UF).", contable: "Saldo UF", interpretacion: "Deuda remanente UF." },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Dimensión", significado: "Fecha de vencimiento final legal de la serie.", contable: "Maduración", interpretacion: "Vencimiento legal." }
    ]
  },
  {
    id: "patrimonios_separados_nota_administracion_detalle",
    name: "patrimonios.nota_administracion",
    viewName: "patrimonios_separados_nota_administracion_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Nota Explicativa Remuneraciones y Comisiones",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "325 filas",
    descripcion: "Detalle relacional de la Nota Explicativa de Remuneraciones por Administración, Custodia y Agencias de Pago. Registra las comisiones fijas y variables cobradas por la securitizadora gestora, bases de cálculo contractuales, tasas anuales y saldos por pagar devengados al cierre del ejercicio.",
    origen: "Comisión para el Mercado Financiero (CMF) - Notas a los Estados Financieros.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Clave primaria de la comisión.", contable: "No aplica", interpretacion: "ID línea." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador del patrimonio separado.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Período YYYYMM.", contable: "No aplica", interpretacion: "Período." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha YYYY-MM-DD.", contable: "No aplica", interpretacion: "Fecha corte." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT administradora.", contable: "No aplica", interpretacion: "RUT gestora." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social securitizadora.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_emision", type: "VARCHAR", role: "Atributo", significado: "Código emisión.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "concepto_comision", type: "VARCHAR", role: "Atributo", significado: "Concepto del honorario o remuneración (Administración Maestro, Custodia, Banco Pagador, etc.).", contable: "Concepto", interpretacion: "Tipo de servicio." },
      { name: "base_calculo", type: "VARCHAR", role: "Atributo", significado: "Base de cálculo pactada en el contrato de emisión (Saldo de Cartera, Activos Totales, Saldo Bonos).", contable: "Base", interpretacion: "Base contractual." },
      { name: "tasa_anual_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa o porcentaje anualizado aplicado como comisión.", contable: "Tasa comisión", interpretacion: "Porcentaje anual." },
      { name: "gasto_periodo_mclp", type: "DOUBLE", role: "Métrica", significado: "Gasto devengado en el período en miles de pesos (M$ CLP).", contable: "Gasto M$", interpretacion: "Costo devengado." },
      { name: "saldo_por_pagar_mclp", type: "DOUBLE", role: "Métrica", significado: "Pasivo exigible pendiente de pago a la administradora en miles de pesos (M$ CLP).", contable: "Cuenta por pagar", interpretacion: "Saldo exigible M$." }
    ]
  },
  {
    id: "patrimonios_separados_nota_sobrecolateral_detalle",
    name: "patrimonios.nota_sobrecolateral",
    viewName: "patrimonios_separados_nota_sobrecolateral_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Nota Explicativa Garantías y Sobrecolateral",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "316 filas",
    descripcion: "Detalle relacional de la Nota Explicativa de Sobrecolateralización y Fondos de Reserva. Cuantifica el exceso de activos colaterales sobre el pasivo de bonos emitidos, el ratio o porcentaje de sobrecolateral real vs contractualmente requerido y los fondos de reserva líquidos de liquidez y prepagos.",
    origen: "Comisión para el Mercado Financiero (CMF) - Notas a los Estados Financieros.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Clave primaria del registro de reserva.", contable: "No aplica", interpretacion: "ID línea." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador del patrimonio separado.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Período YYYYMM.", contable: "No aplica", interpretacion: "Período." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha YYYY-MM-DD.", contable: "No aplica", interpretacion: "Fecha corte." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT administradora.", contable: "No aplica", interpretacion: "RUT gestora." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Atributo", significado: "Razón social securitizadora.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_emision", type: "VARCHAR", role: "Atributo", significado: "Código emisión.", contable: "No aplica", interpretacion: "Emisión." },
      { name: "valor_activos_mclp", type: "DOUBLE", role: "Métrica", significado: "Valor total de activos colaterales en miles de pesos (M$ CLP).", contable: "Activos M$", interpretacion: "Colateral disponible." },
      { name: "valor_pasivos_bonos_mclp", type: "DOUBLE", role: "Métrica", significado: "Valor de pasivos con tenedores de bonos en miles de pesos (M$ CLP).", contable: "Pasivo bonos M$", interpretacion: "Deuda a respaldar." },
      { name: "monto_sobrecolateral_mclp", type: "DOUBLE", role: "Métrica", significado: "Monto de sobrecolateral neto (Activos - Pasivos) en miles de pesos (M$ CLP).", contable: "Exceso colateral", interpretacion: "Margen de seguridad M$." },
      { name: "sobrecolateral_pct", type: "DOUBLE", role: "Métrica", significado: "Ratio de sobrecolateralización (Activos / Pasivos * 100).", contable: "Ratio colateral", interpretacion: "Porcentaje de cobertura %." },
      { name: "fondo_reserva_mclp", type: "DOUBLE", role: "Métrica", significado: "Fondo de reserva líquido constituido en miles de pesos (M$ CLP).", contable: "Fondo reserva", interpretacion: "Reserva de liquidez M$." }
    ]
  },
  {
    id: "patrimonios_separados_nota_efectivo_detalle",
    name: "patrimonios.nota_efectivo_detalle",
    viewName: "patrimonios_separados_nota_efectivo_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Notas Explicativas a los Estados Financieros Auditados",
    corte: "2010-03 a 2026-03",
    frescura: "Trimestral Oficial",
    modo: "Automático PyMuPDF / OCR CMF",
    ultimaActualizacion: "2026-09-25",
    registros: "3,802 filas",
    descripcion: "Desglose exhaustivo 100% real de las partidas de Efectivo, Disponible Bancario y Valores Negociables (fondos mutuos, depósitos a plazo, pactos de retroventa e inversiones de caja) reportadas en notas explicativas auditadas y balances de patrimonios separados. Nota metodológica: Preserva con estricta fidelidad documental la rendición literal de los EEFF, incluyendo los casos donde la administradora imputó a la nota de ingresos netos de caja inversiones transitorias en mutuos hipotecarios, permitiendo al analista discriminar mediante la columna 'tipo_instrumento' según su criterio contable (NIC 7 estricto vs contractual CMF).",
    origen: "Comisión para el Mercado Financiero (CMF) — Notas a los Estados Financieros Auditados de Patrimonios Separados.",
    columnas: [
      { name: "id_linea", type: "VARCHAR", role: "PK", significado: "Identificador único de la línea de liquidez.", contable: "Asiento Primario", interpretacion: "Clave primaria del registro de efectivo." },
      { name: "id_patrimonio", type: "VARCHAR", role: "FK", significado: "Identificador único sintético del patrimonio separado.", contable: "No aplica", interpretacion: "Clave relacional del vehículo emisor." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo de reporte contable (YYYYMM).", contable: "Corte Contable", interpretacion: "Eje temporal del ejercicio financiero." },
      { name: "fecha", type: "VARCHAR", role: "Dimensión", significado: "Fecha exacta de cierre de los estados financieros (YYYY-MM-DD).", contable: "Fecha Balance", interpretacion: "Cierre contable reportado." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT institucional de la sociedad securitizadora gestora.", contable: "No aplica", interpretacion: "Clave foránea hacia securitizadoras_maestro." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal de la sociedad securitizadora.", contable: "No aplica", interpretacion: "Entidad fiduciaria administradora." },
      { name: "codigo_emision", type: "VARCHAR", role: "Dimensión", significado: "Código nemotécnico o identificador de emisión.", contable: "No aplica", interpretacion: "Ticker de la serie o vehículo." },
      { name: "institucion", type: "VARCHAR", role: "Dimensión", significado: "Entidad bancaria o administradora depositaria / contraparte de caja.", contable: "Contraparte Custodio", interpretacion: "Banco o institución financiera receptora." },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Dimensión", significado: "Clase o tipo de instrumento de liquidez (Cta Cte, Fondo Mutuo, DAP, Pactos, Valores Negociables, Mutuos Hipotecarios de Caja).", contable: "Clasificación Activo", interpretacion: "Vehículo o formato de inversión de caja (permite filtrar mutuos si se aplica criterio estricto NIC 7)." },
      { name: "moneda", type: "VARCHAR", role: "Dimensión", significado: "Moneda de denominación original del saldo (CLP, UF, USD).", contable: "Moneda Funcional", interpretacion: "Divisa contable." },
      { name: "saldo_mclp", type: "DOUBLE", role: "Métrica", significado: "Saldo en miles de pesos chilenos (M$ CLP).", contable: "Saldo al Cierre", interpretacion: "Monto nominal reportado en la nota." },
      { name: "saldo_mmclp", type: "DOUBLE", role: "Métrica", significado: "Saldo expresado en millones de pesos chilenos (MM$ CLP).", contable: "Saldo Normalizado", interpretacion: "Monto escalado para comparabilidad macrofinanciera." }
    ]
  },
{
    id: "patrimonios_separados_maestro",
    name: "patrimonios.emisiones_lineas",
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
  // =========================================================================
  // CAJAS DE COMPENSACION (CCAF / SUSESO - CMF)
  // =========================================================================
  {
    id: "ccaf_maestro",
    name: "ccaf.maestro",
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
    name: "agf.maestro",
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
    id: "agf_balance_resumen",
    name: "agf.balance_resumen",
    viewName: "agf_balance_resumen",
    sector: "agf",
    sectorLabel: "Administradoras Generales de Fondos",
    norma: "Norma Internacional de Información Financiera (IFRS) / CMF",
    corte: "Serie Trimestral Histórica",
    frescura: "Actualización Trimestral CMF",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "Balances IFRS",
    descripcion: "Serie histórica de balances y estados de resultados bajo norma IFRS correspondientes al patrimonio corporativo propio de las Administradoras Generales de Fondos (AGF). Monitorea solvencia, capital mínimo regulatorio, efectivo, cartera propia de inversión fiduciaria y comisiones operacionales.",
    origen: "Comisión para el Mercado Financiero (CMF) — Estados Financieros IFRS Trimestrales de Entidades Supervisadas.",
    columnas: [
      { name: "rut", type: "BIGINT", role: "FK", significado: "RUT de la Administradora General de Fondos (AGF).", contable: "No aplica", interpretacion: "Llave foránea vinculada a agf_maestro." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo contable trimestral en formato AAAA-MM (marzo, junio, septiembre, diciembre).", contable: "No aplica", interpretacion: "Fecha de corte del reporte financiero IFRS." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social oficial de la sociedad gestora fiduciaria.", contable: "No aplica", interpretacion: "Entidad jurídica informante." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos corporativos propios de la gestora en millones de CLP.", contable: "Activo Total IFRS", interpretacion: "Tamaño patrimonial corporativo propio (independiente del patrimonio de los fondos administrados)." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de obligaciones y deudas corporativas de la gestora en millones de CLP.", contable: "Pasivo Total IFRS", interpretacion: "Nivel de apalancamiento y endeudamiento de la sociedad fiduciaria." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio total neto atribuible a los accionistas de la AGF en millones de CLP.", contable: "Patrimonio Neto IFRS", interpretacion: "Base de solvencia y respaldo para cumplir el patrimonio mínimo regulatorio de 10.000 UF exigido por la LUF." },
      { name: "efectivo_y_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Caja, depósitos y activos líquidos de disponibilidad inmediata en millones de CLP.", contable: "Efectivo y Equivalentes", interpretacion: "Colchón de liquidez operativa corporativa de la gestora." },
      { name: "cartera_propia_inversiones_m_clp", type: "DOUBLE", role: "Métrica", significado: "Otros activos financieros mantenidos en cartera propia por la AGF en millones de CLP.", contable: "Activos Financieros IFRS", interpretacion: "Inversiones propias de la gestora (skin in the game en cuotas de sus propios fondos o activos de reserva)." },
      { name: "ingresos_comisiones_m_clp", type: "DOUBLE", role: "Métrica", significado: "Ingresos por actividades ordinarias correspondientes a comisiones de administración fiduciaria en millones de CLP.", contable: "Ingresos Operacionales", interpretacion: "Flujo principal del modelo de negocio fiduciario derivado del AUM gestionado." },
      { name: "gastos_administracion_m_clp", type: "DOUBLE", role: "Métrica", significado: "Costos de personal, tecnología, custodia y operaciones fiduciarias en millones de CLP.", contable: "Gastos de Administración", interpretacion: "Estructura de costos operativos para sostener la plataforma de administración de fondos." },
      { name: "ganancia_perdida_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado neto final de la gestora (utilidad o pérdida neta) en millones de CLP.", contable: "Utilidad / Pérdida Neta", interpretacion: "Rentabilidad contable final de la sociedad anónima administradora." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de activos corporativos convertido a millones de USD según tipo de cambio de cierre.", contable: "Activo Total USD", interpretacion: "Comparabilidad internacional del tamaño corporativo de la gestora." },
      { name: "patrimonio_neto_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto corporativo convertido a millones de USD.", contable: "Patrimonio Neto USD", interpretacion: "Solvencia en divisa dura para inversionistas globales." }
    ]
  },
  // =========================================================================
  // SISTEMAS DE PAGO (BCCh / CMF)
  // =========================================================================
  {
    id: "sistemas_pago_maestro",
    name: "pagos.maestro_infraestructuras",
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
  {
    id: "sistemas_pago_balances",
    name: "pagos.balances_ifrs",
    viewName: "sistemas_pago_balances",
    sector: "sistemas_pago",
    sectorLabel: "Sistemas de Pago",
    norma: "Normas Internacionales de Información Financiera (IFRS) adoptadas por CMF",
    corte: "Trimestral (2018-03 a 2026-06)",
    frescura: "Trimestral",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "82 balances",
    descripcion: "Estados de situación financiera consolidados bajo estándar IFRS para cámaras de contraparte central y redes adquirentes supervisadas (ComDer, CCLV, Transbank). Permite auditar la solvencia patrimonial, garantías de compensación, fondos de reserva y resultados operacionales.",
    origen: "Comisión para el Mercado Financiero (CMF) - FECU IFRS.",
    columnas: [
      { name: "rut", type: "BIGINT", role: "FK", significado: "RUT institucional de la cámara o adquirente.", contable: "No aplica", interpretacion: "Llave foránea vinculada a sistemas_pago_maestro." },
      { name: "periodo", type: "VARCHAR", role: "PK", significado: "Periodo trimestral de corte (YYYY-MM).", contable: "Corte Trimestral", interpretacion: "Fecha de reporte financiero oficial." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la cámara o red adquirente.", contable: "No aplica", interpretacion: "Nombre legal de la entidad informante." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos bajo IFRS en millones de pesos chilenos.", contable: "Estado de Situación Financiera", interpretacion: "Recursos económicos totales bajo control de la entidad." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos exigibles en millones de pesos chilenos.", contable: "Estado de Situación Financiera", interpretacion: "Obligaciones totales con terceros y contrapartes." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto total en millones de pesos chilenos.", contable: "Patrimonio atribuible a propietarios", interpretacion: "Capital, reservas de riesgo y resultados acumulados." },
      { name: "efectivo_y_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Efectivo y equivalentes de efectivo disponibles en millones de pesos.", contable: "Activo Corriente", interpretacion: "Liquidez inmediata para afrontar operaciones de compensación." },
      { name: "ganancia_perdida_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado del ejercicio acumulado en millones de pesos chilenos.", contable: "Estado de Resultados", interpretacion: "Utilidad o pérdida neta devengada al cierre trimestral." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de activos valorizados en millones de dólares al tipo de cambio de cierre BCCh.", contable: "Conversión Cambiaria", interpretacion: "Comparabilidad monetaria internacional." },
      { name: "patrimonio_neto_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto expresado en millones de dólares.", contable: "Conversión Cambiaria", interpretacion: "Solvencia patrimonial en moneda de referencia internacional." }
    ]
  },
  {
    id: "sistemas_pago_estadisticas_bcch",
    name: "pagos.estadisticas_bcch",
    viewName: "sistemas_pago_estadisticas_bcch",
    sector: "sistemas_pago",
    sectorLabel: "Sistemas de Pago",
    norma: "Ley 18.840 / Informe de Sistemas de Pago (ISiP) y Base de Datos Estadísticos BCCh",
    corte: "Mensual (2018-01 a 2026-06)",
    frescura: "Mensual",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "102 observaciones",
    descripcion: "Series estadísticas agregadas de medios y sistemas de pago chilenos: liquidez en efectivo (circulante M0 stock y promedio), flujo mensual bruto liquidado en el sistema LBTR (millones de USD), compensación minorista de transferencias electrónicas de fondos (CCA TEF en millones de CLP) y tasas de interés de colocación con tarjetas de crédito.",
    origen: "Banco Central de Chile (BCCh) - Base de Datos Estadísticos (SIETE) e ISiP.",
    columnas: [
      { name: "periodo", type: "VARCHAR", role: "PK", significado: "Periodo mensual de observación (YYYY-MM).", contable: "Corte Mensual", interpretacion: "Eje temporal de la serie económica." },
      { name: "año", type: "BIGINT", role: "Dimensión", significado: "Año calendario de la serie.", contable: "No aplica", interpretacion: "Agrupación temporal anual." },
      { name: "mes", type: "BIGINT", role: "Dimensión", significado: "Mes calendario (1 a 12).", contable: "No aplica", interpretacion: "Estacionalidad intra-anual." },
      { name: "circulante_stock_m_clp", type: "DOUBLE", role: "Métrica", significado: "Stock de billetes y monedas en libre circulación a fin de mes en millones de CLP.", contable: "Agregado M0", interpretacion: "Demanda de efectivo del público y comercios." },
      { name: "circulante_promedio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Promedio mensual de billetes y monedas en circulación en millones de CLP.", contable: "Agregado M0 Promedio", interpretacion: "Nivel estructural de liquidez en efectivo." },
      { name: "tasa_tarjetas_consumo_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés promedio anualizada para colocaciones en tarjetas de crédito de personas (consumo).", contable: "Tasa Efectiva", interpretacion: "Costo de financiamiento revolving y cuotas para tarjetahabientes." },
      { name: "tasa_tarjetas_comercial_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés promedio anualizada para tarjetas de crédito comerciales corporativas.", contable: "Tasa Efectiva", interpretacion: "Condiciones de crédito para micro y pequeñas empresas usuarias de tarjetas." },
      { name: "monto_liquidado_lbtr_m_usd", type: "DOUBLE", role: "Métrica", significado: "Volumen bruto mensual liquidado a través del sistema LBTR del Banco Central en millones de USD.", contable: "Flujo Interbancario", interpretacion: "Intensidad y liquidez sistémica de transferencias de alto valor." },
      { name: "monto_compensado_cca_tef_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valor total compensado por la Cámara de Compensación de Alto y Bajo Valor (CCA) en transferencias TEF en millones de CLP.", contable: "Compensación Minorista", interpretacion: "Penetración del canal de pagos electrónicos cuenta a cuenta." },
      { name: "tipo_cambio_usd_clp", type: "DOUBLE", role: "Métrica", significado: "Tipo de cambio promedio mensual USD/CLP oficial.", contable: "Precio de Mercado", interpretacion: "Factor de paridad cambiaria oficial BCCh." }
    ]
  },
  // =========================================================================
  // RETAIL FINANCIERO Y EMISORES NO BANCARIOS (CMF)
  // =========================================================================
  {
    id: "retail_financiero_maestro",
    name: "retail.maestro",
    viewName: "retail_financiero_maestro",
    sector: "retail_financiero",
    sectorLabel: "Retail Financiero",
    norma: "CMF (Registros RVEMI, TCEEM, TPEEM, BCSAG)",
    corte: "Oficial CMF 2026",
    frescura: "Catálogo Vigente",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "17 entidades",
    descripcion: "Catálogo maestro oficial de los emisores no bancarios de tarjetas de crédito y prepago, sociedades de apoyo al giro y matrices cotizadas de retail financiero supervisadas por la CMF. Incluye Falabella, Cencosud, Ripley, Hites, Tricot, abcvisa, Tenpo, Tapp Los Andes y Prepago Los Héroes.",
    origen: "Comisión para el Mercado Financiero (CMF) — Registros de Entidades Supervisadas.",
    columnas: [
      { name: "rut", type: "BIGINT", role: "PK", significado: "Rol Único Tributario numérico de la sociedad.", contable: "No aplica", interpretacion: "Identificador tributario corporativo único del emisor/matriz." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador calculado bajo algoritmo Módulo 11.", contable: "No aplica", interpretacion: "Control de integridad tributaria." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT estándar con puntos y guion (ej: 90.749.000-9).", contable: "No aplica", interpretacion: "Formato oficial para consultas regulatorias." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Nombre legal formal de la corporación o sociedad anónima.", contable: "No aplica", interpretacion: "Denominación legal inscrita en el registro público de la CMF." },
      { name: "nombre_comercial", type: "VARCHAR", role: "Dimensión", significado: "Marca comercial o nombre de fantasía ante clientes e inversionistas.", contable: "No aplica", interpretacion: "Identidad comercial del negocio de retail y tarjetas." },
      { name: "tipo_entidad_cmf", type: "VARCHAR", role: "Dimensión", significado: "Tipo de registro en CMF: RVEMI (Emisores de Valores), TCEEM (Emisor Tarjetas Crédito), TPEEM (Emisor Prepago), BCSAG (Apoyo Giro), TPOPE (Operador Tarjetas).", contable: "No aplica", interpretacion: "Marco regulatorio y habilitación operativa conferida por el supervisor." },
      { name: "segmento_mercado", type: "VARCHAR", role: "Dimensión", significado: "Clasificación de industria: Retail Departamental y Financiero, Especialistas en Prepago Digital, Farmacias/Especialistas.", contable: "No aplica", interpretacion: "Agrupación analítica del modelo de negocio." },
      { name: "grupo_controlador", type: "VARCHAR", role: "Dimensión", significado: "Conglomerado económico o grupo empresarial controlador.", contable: "No aplica", interpretacion: "Vínculo de propiedad y control societario." },
      { name: "estado_vigencia", type: "VARCHAR", role: "Dimensión", significado: "Condición en el registro oficial CMF: 'Vigente'.", contable: "No aplica", interpretacion: "Filtro para entidades activas en el mercado financiero." },
      { name: "domicilio_casa_matriz", type: "VARCHAR", role: "Dimensión", significado: "Dirección de la sede corporativa central.", contable: "No aplica", interpretacion: "Ubicación del domicilio legal corporativo." },
      { name: "comuna", type: "VARCHAR", role: "Dimensión", significado: "Comuna de la casa matriz.", contable: "No aplica", interpretacion: "Localización geográfica de la sede." },
      { name: "region", type: "VARCHAR", role: "Dimensión", significado: "Región político-administrativa chilena.", contable: "No aplica", interpretacion: "Jurisdicción regional." },
      { name: "cmf_url", type: "VARCHAR", role: "Dimensión", significado: "Enlace directo al expediente institucional en el portal de la CMF.", contable: "No aplica", interpretacion: "Ficha oficial de fiscalizado en el regulador." }
    ]
  },
  {
    id: "retail_financiero_balances",
    name: "retail.balances",
    viewName: "retail_financiero_balances",
    sector: "retail_financiero",
    sectorLabel: "Retail Financiero",
    norma: "Norma Internacional de Información Financiera (IFRS) / CMF",
    corte: "Serie Trimestral Histórica (2018-2026)",
    frescura: "Actualización Trimestral CMF",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "190 balances",
    descripcion: "Serie histórica de balances consolidados y estados de resultados bajo norma IFRS correspondientes a las matrices cotizadas de retail financiero (Falabella, Cencosud, Ripley, Hites, Tricot, ABC). Monitorea solvencia, dimensión de activos, efectivo y caja disponible, endeudamiento total y utilidad neta con identidad contable 100% exacta.",
    origen: "Comisión para el Mercado Financiero (CMF) — Estados Financieros Consolidados IFRS Trimestrales.",
    columnas: [
      { name: "rut", type: "BIGINT", role: "FK", significado: "RUT de la matriz de retail financiero.", contable: "No aplica", interpretacion: "Llave foránea vinculada a retail_financiero_maestro." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo contable trimestral en formato AAAA-MM.", contable: "No aplica", interpretacion: "Fecha de corte del reporte financiero IFRS." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social formal de la compañía informante.", contable: "No aplica", interpretacion: "Entidad corporativa matriz." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos consolidados de la compañía en millones de CLP.", contable: "Total Activos IFRS", interpretacion: "Dimensión patrimonial total de la corporación de retail y financiero." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos y obligaciones financieras consolidadas en millones de CLP.", contable: "Total Pasivos IFRS", interpretacion: "Nivel de apalancamiento y endeudamiento total." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto total atribuible a los accionistas en millones de CLP.", contable: "Patrimonio Neto IFRS", interpretacion: "Base de solvencia patrimonial corporativa." },
      { name: "efectivo_y_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Caja, depósitos líquidos y equivalentes al efectivo en millones de CLP.", contable: "Efectivo y Equivalentes", interpretacion: "Colchón de liquidez disponible para operaciones y vencimientos." },
      { name: "ganancia_perdida_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado neto del periodo (ganancia o pérdida consolidada) en millones de CLP.", contable: "Utilidad Neta IFRS", interpretacion: "Rentabilidad contable final generada por la operación global." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de activos convertido a millones de USD según tipo de cambio de cierre BCCh.", contable: "Activos USD", interpretacion: "Comparabilidad internacional del tamaño corporativo." },
      { name: "patrimonio_neto_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto convertido a millones de USD.", contable: "Patrimonio USD", interpretacion: "Solvencia en divisa dura para inversionistas extranjeros." }
    ]
  },
  // =========================================================================
  // FINTECH & FINANZAS ABIERTAS (Ley N° 21.521 / CMF)
  // =========================================================================
  {
    id: "fintech_rpsf_maestro",
    name: "fintech.rpsf_maestro",
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
    id: "fintech_servicios_acreditados",
    name: "fintech.servicios_acreditados",
    viewName: "fintech_servicios_acreditados",
    sector: "fintech",
    sectorLabel: "FinTech",
    norma: "Ley N° 21.521 / NCG N° 502 CMF",
    corte: "Catálogo Oficial Vigente CMF",
    frescura: "Actualización Continua",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "262 licencias",
    descripcion: "Matriz desagregada de licencias y autorizaciones operativas por servicio financiero tipificado bajo la Ley Fintec (PFC, SAT, AC, AI, CIF, EO, IIF). Detalla la condición regulatoria de cada servicio (Autorizado, Eximido de solicitar autorización, Cancelado) para cada entidad inscrita.",
    origen: "Comisión para el Mercado Financiero (CMF) — RPSF.",
    columnas: [
      { name: "rut", type: "BIGINT", role: "FK", significado: "RUT del prestador FinTech.", contable: "No aplica", interpretacion: "Llave foránea vinculada a fintech_rpsf_maestro." },
      { name: "dv", type: "VARCHAR", role: "Dimensión", significado: "Dígito verificador auditado con Módulo 11.", contable: "No aplica", interpretacion: "Validación tributaria." },
      { name: "rut_completo", type: "VARCHAR", role: "Dimensión", significado: "RUT formal formateado.", contable: "No aplica", interpretacion: "Identificación corporativa canónica." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la FinTech.", contable: "No aplica", interpretacion: "Empresa titular de la autorización de servicio." },
      { name: "servicio_codigo", type: "VARCHAR", role: "Dimensión", significado: "Código normativo interno CMF (SER_PFC, SER_SAT, SER_AC, SER_AI, SER_CIF, SER_EO, SER_IIF).", contable: "No aplica", interpretacion: "Código técnico del servicio en la taxonomía regulada." },
      { name: "servicio_sigla", type: "VARCHAR", role: "Dimensión", significado: "Acrónimo estándar del servicio (PFC, SAT, AC, AI, CIF, EO, IIF).", contable: "No aplica", interpretacion: "Sigla de identificación operativa rápida." },
      { name: "servicio_nombre", type: "VARCHAR", role: "Dimensión", significado: "Denominación legal completa del servicio según la Ley 21.521.", contable: "No aplica", interpretacion: "Actividad financiera autorizada." },
      { name: "servicio_categoria", type: "VARCHAR", role: "Dimensión", significado: "Categoría conceptual (Crowdfunding, Negociación Secundaria, Scoring, WealthTech, Custodia, Enrutamiento).", contable: "No aplica", interpretacion: "Segmento funcional de la industria FinTech." },
      { name: "estado_autorizacion", type: "VARCHAR", role: "Dimensión", significado: "Estado de la licencia: Autorizado, Eximido de solicitar autorización, Cancelado.", contable: "No aplica", interpretacion: "Habilitación legal para comercializar y ejecutar el servicio." },
      { name: "marco_normativo", type: "VARCHAR", role: "Dimensión", significado: "Cuerpo reglamentario aplicable: NCG N° 502 / Ley N° 21.521.", contable: "No aplica", interpretacion: "Base legal de fiscalización." }
    ]
  },
  {
    id: "fintech_finanzas_abiertas_roles",
    name: "fintech.finanzas_abiertas_roles",
    viewName: "fintech_finanzas_abiertas_roles",
    sector: "fintech",
    sectorLabel: "FinTech",
    norma: "Título III Ley N° 21.521 / Sistema de Finanzas Abiertas (SFA)",
    corte: "Taxonomía Normativa CMF",
    frescura: "Vigente",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "262 roles",
    descripcion: "Mapeo y taxonomía de roles de los prestadores en el Sistema de Finanzas Abiertas (SFA / Open Finance) de Chile. Clasifica a las entidades en Instituciones Proveedoras de Servicios Basados en Información (IPSI), Iniciadoras de Pagos o Enrutadoras (IIP) y Proveedoras de Cuentas (IPC), especificando requisitos de consentimiento de clientes y garantías líquidas exigidas.",
    origen: "Comisión para el Mercado Financiero (CMF) — Marco Open Finance Ley N° 21.521.",
    columnas: [
      { name: "rut", type: "BIGINT", role: "FK", significado: "RUT del prestador FinTech.", contable: "No aplica", interpretacion: "Llave foránea vinculada a fintech_rpsf_maestro." },
      { name: "razon_social", type: "VARCHAR", role: "Dimensión", significado: "Razón social del participante del SFA.", contable: "No aplica", interpretacion: "Entidad acreditada en el ecosistema Open Finance." },
      { name: "servicio_origen", type: "VARCHAR", role: "Dimensión", significado: "Servicio FinTech base que origina el rol en SFA (AI, AC, EO, SAT, IIF, CIF).", contable: "No aplica", interpretacion: "Origen normativo del rol de datos o transaccional." },
      { name: "rol_sfa", type: "VARCHAR", role: "PK", significado: "Rol en Finanzas Abiertas: IPSI (Servicios de Información), IIP (Iniciador de Pagos/Órdenes), IPC (Proveedor de Cuentas).", contable: "No aplica", interpretacion: "Clasificación arquitectónica en la red de APIs financieras." },
      { name: "descripcion_rol", type: "VARCHAR", role: "Dimensión", significado: "Definición normativa y alcance funcional del rol.", contable: "No aplica", interpretacion: "Facultades y responsabilidades en el intercambio de datos." },
      { name: "estandar_interfaz", type: "VARCHAR", role: "Dimensión", significado: "Estándar técnico de conectividad: API RESTful JSON bajo estándar Open Finance CMF.", contable: "No aplica", interpretacion: "Protocolo de comunicación digital interoperable." },
      { name: "requisito_consentimiento", type: "VARCHAR", role: "Dimensión", significado: "Consentimiento expreso, previo, informado y revocable por el cliente titular de los datos.", contable: "No aplica", interpretacion: "Principio de gobernanza y soberanía de datos del usuario." },
      { name: "exigencia_garantia", type: "VARCHAR", role: "Dimensión", significado: "Patrimonio mínimo o póliza de seguro de responsabilidad profesional requerida.", contable: "No aplica", interpretacion: "Mitigador de riesgo operacional y solvencia de la FinTech." }
    ]
  },
  {
    id: "ccaf_maestro",
    name: "ccaf.maestro",
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
    name: "ccaf.caratula_totales",
    viewName: "ccaf_caratula_totales",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "Circular SUSESO / IFRS CMF",
    corte: "2025-06",
    frescura: "Serie Histórica 2010-2025",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "266 balances",
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
    id: "ccaf_nota8_efectivo_resumen",
    name: "ccaf.nota8_efectivo_resumen",
    viewName: "ccaf_nota8_efectivo_resumen",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "NIC 7 / Circular SUSESO",
    corte: "2024-12",
    frescura: "Serie Histórica 2012-2024",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "189 componentes",
    descripcion: "Desglose contable de los componentes analíticos puros de Efectivo y Equivalentes al Efectivo (Nota 8 de los EEFF auditados) entre 2012 y 2024. Excluye deliberadamente la fila de Total general para evitar agregación duplicada, abarcando saldos en Caja, Bancos, Depósitos a Plazo e inversiones de corto plazo / Pactos de retroventa.",
    origen: "SUSESO & CMF — Notas explicativas a los Estados Financieros Auditados.",
    columnas: [
      { name: "ano", type: "BIGINT", role: "Fecha", significado: "Año fiscal de corte de la nota de liquidez.", contable: "No aplica" },
      { name: "mes", type: "BIGINT", role: "Fecha", significado: "Mes de cierre anual auditado (12).", contable: "No aplica" },
      { name: "ccaf", type: "VARCHAR", role: "Dimensión", significado: "Sigla institucional de la Caja de Compensación informante.", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT institucional de la CCAF.", contable: "No aplica" },
      { name: "tipo_eeff", type: "VARCHAR", role: "Dimensión", significado: "Alcance contable de la nota explicativa: Consolidado o Individual.", contable: "No aplica" },
      { name: "concepto", type: "VARCHAR", role: "Dimensión", significado: "Concepto analítico de liquidez: Saldo en caja, Bancos, Depósitos a plazo u Otro efectivo y equivalentes (Repos/Pactos).", contable: "No aplica" },
      { name: "monto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto del componente expresado en millones de pesos ($M CLP).", contable: "Valor Razonable / MtM" },
      { name: "monto_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Monto exacto del componente en miles de pesos ($Miles CLP).", contable: "Valor Razonable / MtM" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda de presentación de la nota (CLP).", contable: "No aplica" },
      { name: "escala", type: "VARCHAR", role: "Atributo", significado: "Escala contable del estado financiero (Miles de pesos).", contable: "No aplica" }
    ]
  },
  {
    id: "ccaf_nota8_dap_detalle",
    name: "ccaf.nota8_dap_detalle",
    viewName: "ccaf_nota8_dap_detalle",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "NIC 7 / Circular SUSESO",
    corte: "2024-12",
    frescura: "Serie Histórica 2020-2024",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "52 depósitos",
    descripcion: "Detalle pormenorizado instrumento por instrumento de las colocaciones en Depósitos a Plazo (DAP) mantenidas por las Cajas de Compensación en el sistema bancario comercial chileno.",
    origen: "SUSESO & CMF — Subtablas analíticas de colocaciones bancarias Nota 8.",
    columnas: [
      { name: "ano", type: "BIGINT", role: "Fecha", significado: "Año fiscal del reporte.", contable: "No aplica" },
      { name: "mes", type: "BIGINT", role: "Fecha", significado: "Mes de corte de la sub-nota.", contable: "No aplica" },
      { name: "ccaf", type: "VARCHAR", role: "Dimensión", significado: "Sigla de la Caja de Compensación titular de la colocación.", contable: "No aplica" },
      { name: "tipo_eeff", type: "VARCHAR", role: "Dimensión", significado: "Alcance contable de la nota (Consolidado o Individual).", contable: "No aplica" },
      { name: "tipo_inversion", type: "VARCHAR", role: "Dimensión", significado: "Tipo de instrumento bancario o banco emisor del depósito.", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda de denominación (Pesos / UF).", contable: "No aplica" },
      { name: "plazo_dias", type: "BIGINT", role: "Dimensión", significado: "Plazo de vigencia del depósito expresado en días.", contable: "No aplica" },
      { name: "tasa_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés devengada pactada con el banco.", contable: "Costo Amortizado / Devengado" },
      { name: "capital_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Capital principal invertido en miles de pesos chilenos.", contable: "Costo Amortizado / Devengado" },
      { name: "intereses_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Intereses devengados al corte en miles de CLP.", contable: "Costo Amortizado / Devengado" },
      { name: "valor_contable_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Valorización contable total en miles de pesos chilenos.", contable: "Costo Amortizado / Devengado" },
      { name: "valor_contable_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valor contable expresado en millones de pesos ($M CLP).", contable: "Costo Amortizado / Devengado" }
    ]
  },
  {
    id: "ccaf_nota8_repos_detalle",
    name: "ccaf.nota8_repos_detalle",
    viewName: "ccaf_nota8_repos_detalle",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "NIC 7 / Circular SUSESO",
    corte: "2024-12",
    frescura: "Serie Histórica 2018-2024",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "158 pactos auditados",
    descripcion: "Detalle contrato a contrato de las operaciones de compra con retroventa (Pactos de Retroventa / Repos) suscritas por las Cajas de Compensación con corredoras de bolsa institucionales en el mercado monetario chileno, con plazos en días y tasas estandarizadas.",
    origen: "CMF Chile & SUSESO — Subtablas analíticas de pactos y repos de la Nota 8 (Efectivo y Equivalentes).",
    columnas: [
      { name: "ano", type: "BIGINT", role: "Fecha", significado: "Año fiscal de vigencia del pacto (2018 a 2024).", contable: "No aplica" },
      { name: "mes", type: "BIGINT", role: "Fecha", significado: "Mes de cierre contable (12).", contable: "No aplica" },
      { name: "ccaf", type: "VARCHAR", role: "Dimensión", significado: "Nombre institucional de la CCAF suscriptora.", contable: "No aplica" },
      { name: "tipo_eeff", type: "VARCHAR", role: "Dimensión", significado: "Alcance contable de la nota (Consolidado o Individual).", contable: "No aplica" },
      { name: "institucion_contraparte", type: "VARCHAR", role: "Dimensión", significado: "Razón social original reportada de la corredora de bolsa contraparte.", contable: "No aplica" },
      { name: "broker_estandarizado", type: "VARCHAR", role: "Dimensión", significado: "Nombre institucional canónico normalizado de la corredora de bolsa contraparte (10 corredoras).", contable: "No aplica" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda de la transacción pactada (CLP).", contable: "No aplica" },
      { name: "fecha_inicio", type: "VARCHAR", role: "Fecha", significado: "Fecha de colocación de fondos en la compra de activos.", contable: "No aplica" },
      { name: "fecha_termino", type: "VARCHAR", role: "Fecha", significado: "Fecha de retrocesión y liquidación de fondos acordada.", contable: "No aplica" },
      { name: "plazo_dias", type: "BIGINT", role: "Métrica", significado: "Duración de la operación simultánea en días corridos (fecha_termino - fecha_inicio).", contable: "No aplica" },
      { name: "valor_inicial_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Monto inicial transferido en miles de CLP.", contable: "Pacto Activo (CRV) / Pasivo (VRC)" },
      { name: "valor_final_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Monto de rescate pactado al vencimiento en miles de CLP.", contable: "Pacto Activo (CRV) / Pasivo (VRC)" },
      { name: "tasa_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa anual equivalente implícita base 360 (alias de tasa_anual_pct).", contable: "Costo Amortizado / Devengado" },
      { name: "tasa_pactada_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa nominal original reportada en las notas explicativas de los balances.", contable: "Costo Amortizado / Devengado" },
      { name: "tasa_anual_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés anualizada equivalente calculada en base 360 días.", contable: "Costo Amortizado / Devengado" },
      { name: "tasa_mensual_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de interés mensual equivalente calculada en base 30 días.", contable: "Costo Amortizado / Devengado" },
      { name: "valor_contable_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Valor contable devengado al cierre en miles de pesos chilenos.", contable: "Pacto Activo (CRV) / Pasivo (VRC)" },
      { name: "valor_contable_m_clp", type: "DOUBLE", role: "Métrica", significado: "Valor contable en libros expresado en millones de pesos ($M CLP).", contable: "Pacto Activo (CRV) / Pasivo (VRC)" }
    ]
  },
  {
    id: "ccaf_colocaciones_credito_social",
    name: "ccaf.colocaciones_credito_social",
    viewName: "ccaf_colocaciones_credito_social",
    sector: "cajas_compensacion",
    sectorLabel: "Cajas de Compensación",
    norma: "IFRS CMF (Taxonomía cl-cc)",
    corte: "2026-06",
    frescura: "2019-2026 (Trimestral y Anual)",
    modo: "Automático XBRL",
    ultimaActualizacion: "2026-09-23",
    registros: "268 componentes atómicos",
    descripcion: "Cartera oficial de colocaciones atómicas de Crédito Social y provisiones de deterioro para las Cajas de Compensación chilenas extraída directamente desde los hechos XBRL de la CMF. Excluye estrictamente filas redundantes de totales y subtotales para garantizar aditividad perfecta sin doble contabilización. Desglosa los montos vigentes corrientes, no corrientes, provisiones de incobrabilidad y valor neto por tipo de afiliado (Trabajadores y Pensionados) y destino del crédito (Consumo, Educación, Hipotecario, Microempresarios).",
    origen: "Comisión para el Mercado Financiero (CMF) — Instancias XBRL oficiales con taxonomía sectorial cl-cc.",
    columnas: [
      { name: "ano", type: "BIGINT", role: "Fecha", significado: "Año fiscal de corte del reporte contable.", contable: "No aplica" },
      { name: "mes", type: "BIGINT", role: "Fecha", significado: "Mes de corte del reporte financiero (3, 6, 9 o 12).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Periodo en formato YYYY-MM.", contable: "No aplica" },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT institucional de la CCAF.", contable: "No aplica" },
      { name: "ccaf", type: "VARCHAR", role: "Dimensión", significado: "Nombre o sigla oficial de la Caja de Compensación.", contable: "No aplica" },
      { name: "tipo_eeff", type: "VARCHAR", role: "Dimensión", significado: "Alcance contable oficial reportado (Consolidado para emisores de bonos, Individual para 18 de Septiembre).", contable: "No aplica" },
      { name: "tipo_afiliado", type: "VARCHAR", role: "Dimensión", significado: "Segmento de afiliados atómico: Trabajadores o Pensionados.", contable: "No aplica" },
      { name: "tipo_credito", type: "VARCHAR", role: "Dimensión", significado: "Línea o destino atómico del crédito social: Consumo, Fines Educacionales, Microempresarios o Mutuos Hipotecarios No Endosables.", contable: "No aplica" },
      { name: "monto_corriente_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Monto de colocaciones con vencimiento corriente (< 12 meses) en miles de CLP.", contable: "Costo Amortizado" },
      { name: "monto_no_corriente_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Monto de colocaciones con vencimiento no corriente (> 12 meses) en miles de CLP.", contable: "Costo Amortizado" },
      { name: "deterioro_provision_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Provisión o deterioro acumulado por riesgo de crédito en miles de CLP.", contable: "Provisión IFRS 9 / Circular CMF" },
      { name: "monto_neto_miles_clp", type: "DOUBLE", role: "Métrica", significado: "Valor libro neto de la cartera (Corriente + No Corriente) en miles de CLP.", contable: "Valor Neto en Libros" },
      { name: "moneda", type: "VARCHAR", role: "Atributo", significado: "Moneda de denominación (CLP).", contable: "No aplica" },
      { name: "escala", type: "VARCHAR", role: "Atributo", significado: "Escala contable (Miles de pesos).", contable: "No aplica" },
      { name: "fuente", type: "VARCHAR", role: "Atributo", significado: "Fuente técnica de extracción (CMF_XBRL).", contable: "No aplica" }
    ]
  },
  {
    id: "ffmm_caratula_eeff_2024",
    name: "ffmm.caratula_eeff_2024",
    viewName: "ffmm_caratula_eeff_2024",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "IFRS / CMF Ley 20.712",
    corte: "2024-12",
    frescura: "Cierre 2024 Auditado",
    modo: "Automático PyMuPDF Solver",
    ultimaActualizacion: "2026-09-24",
    registros: "376 fondos auditados",
    descripcion: "Carátula de balance y estado de resultados auditados al cierre 2024 para fondos mutuos supervisados por la CMF. Incluye activos totales, pasivos de liquidación, patrimonio / AUM atribuible a partícipes, utilidad del ejercicio y desglose de notas de efectivo, valor razonable, costo amortizado y operaciones REPO.",
    origen: "Comisión para el Mercado Financiero (CMF) — Estados Financieros Anuales Auditados (Pestaña 62 de Fondos Mutuos).",
    columnas: [
      { name: "run_fondo", type: "VARCHAR", role: "PK", significado: "RUN identificador único del fondo mutuo ante la CMF.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Razón social completa y oficial del fondo mutuo.", contable: "No aplica" },
      { name: "rut_agf", type: "VARCHAR", role: "FK", significado: "RUT institucional de la Administradora General de Fondos gestora.", contable: "No aplica" },
      { name: "razon_social_agf", type: "VARCHAR", role: "Dimensión", significado: "Nombre de la Administradora General de Fondos (AGF).", contable: "No aplica" },
      { name: "moneda_fondo", type: "VARCHAR", role: "Atributo", significado: "Moneda de denominación de las cuotas del fondo.", contable: "No aplica" },
      { name: "moneda_eeff", type: "VARCHAR", role: "Atributo", significado: "Moneda en que se emitieron y auditaron los estados financieros (CLP o USD).", contable: "No aplica" },
      { name: "factor_tc_usd_clp", type: "DOUBLE", role: "Métrica", significado: "Tipo de cambio de cierre utilizado para conversión a moneda homogénea.", contable: "No aplica" },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos mantenidos por el fondo mutuo en millones de CLP.", contable: "Valor de Mercado Bruto" },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos operacionales (rescates por pagar, liquidaciones T+1/T+2 y comisiones devengadas) en millones de CLP.", contable: "Costo Amortizado / Devengado" },
      { name: "patrimonio_aum_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activo neto atribuible a los partícipes (AUM) en millones de CLP.", contable: "Valor de Mercado Neto" },
      { name: "utilidad_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Aumento o disminución de activo neto por operaciones del ejercicio anual en millones de CLP.", contable: "Resultado IFRS" },
      { name: "saldo_repos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo de operaciones de compra con retroventa al 31 de diciembre en millones de CLP.", contable: "Pacto Activo (CRV)" },
      { name: "costo_amortizado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activos financieros valorizados a costo amortizado en millones de CLP.", contable: "Costo Amortizado" },
      { name: "fvtpl_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activos financieros medidos a valor razonable con cambios en resultados en millones de CLP.", contable: "Valor Razonable / MtM" },
      { name: "efectivo_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo de efectivo y equivalentes al efectivo al 31 de diciembre en millones de CLP.", contable: "Costo Amortizado" },
      { name: "tiene_repos", type: "BOOLEAN", role: "Dimensión", significado: "Flag que indica si el fondo mutuo mantiene contratos de compra con retroventa al cierre.", contable: "No aplica" }
    ]
  },
  {
    id: "ffmm_repos_detalle_2024",
    name: "ffmm.repos_detalle_2024",
    viewName: "ffmm_repos_detalle_2024",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "IFRS / CMF Ley 20.712 (Nota Compra con Retroventa)",
    corte: "2024-12",
    frescura: "Cierre 2024 Auditado",
    modo: "Automático PyMuPDF TableFinder",
    ultimaActualizacion: "2026-09-24",
    registros: "Contratos REPO Literales",
    descripcion: "Desglose literal de 11 columnas de todos los contratos individuales de operaciones de compra con retroventa (REPOs activos) de fondos mutuos chilenos al cierre de 2024, extraídos desde las notas a los estados financieros auditados.",
    origen: "Comisión para el Mercado Financiero (CMF) — Notas explicativas a los EEFF Auditados de Fondos Mutuos.",
    columnas: [
      { name: "run_fondo", type: "VARCHAR", role: "FK", significado: "RUN identificador único del fondo mutuo ante la CMF.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Razón social oficial del fondo mutuo.", contable: "No aplica" },
      { name: "rut_agf", type: "VARCHAR", role: "FK", significado: "RUT institucional de la Administradora General de Fondos gestora.", contable: "No aplica" },
      { name: "razon_social_agf", type: "VARCHAR", role: "Dimensión", significado: "Nombre de la Administradora General de Fondos (AGF).", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Fecha original de suscripción de la compra con pacto de retroventa.", contable: "No aplica" },
      { name: "rut_contraparte", type: "VARCHAR", role: "FK", significado: "RUT oficial de la institución financiera o corredora contraparte.", contable: "No aplica" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Dimensión", significado: "Razón social o denominación de la contraparte dealer del contrato REPO.", contable: "No aplica" },
      { name: "clasificacion_riesgo", type: "VARCHAR", role: "Atributo", significado: "Clasificación de riesgo de crédito de la contraparte o instrumento.", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Dimensión", significado: "Código nemotécnico del instrumento financiero entregado en garantía/pacto.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Dimensión", significado: "Tipo de instrumento subyacente (BTP, BTU, PDBC, Depósito, etc.).", contable: "No aplica" },
      { name: "unidades_nominales", type: "DOUBLE", role: "Métrica", significado: "Cantidad o unidades nominales del instrumento transado.", contable: "No aplica" },
      { name: "total_transado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto total transado al inicio del contrato en millones de CLP.", contable: "Pacto Activo (CRV)" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha acordada para la retroventa o vencimiento del contrato.", contable: "No aplica" },
      { name: "precio_pactado_tasa", type: "VARCHAR", role: "Métrica", significado: "Tasa de interés o precio pactado para la retroventa.", contable: "No aplica" },
      { name: "saldo_al_cierre_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo contable valorizado al 31/12/2024 en millones de CLP.", contable: "Pacto Activo (CRV)" },
      { name: "pagina_pdf", type: "BIGINT", role: "Atributo", significado: "Número de página dentro del PDF oficial del estado financiero auditado.", contable: "No aplica" }
    ]
  },
  {
    id: "ffmm_caratula_eeff_historico",
    name: "ffmm.caratula_eeff_historico",
    viewName: "ffmm_caratula_eeff_historico",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "IFRS / CMF Ley 20.712",
    corte: "2015-2025",
    frescura: "Panel Anual 2015-2025",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "Panel Histórico Completo",
    descripcion: "Carátula histórica de balances generales y estados de resultados auditados (2015-2025) para todo el mercado de fondos mutuos chilenos supervisados por la CMF. Incluye activos totales, pasivos totales, patrimonio / AUM neto atribuible a partícipes, utilidad del ejercicio, efectivo y equivalentes, cartera a valor razonable y cartera a costo amortizado con validación de identidad contable exacta.",
    origen: "Comisión para el Mercado Financiero (CMF) — Pestaña 3 (Información Financiera Histórica).",
    columnas: [
      { name: "run_fondo", type: "BIGINT", role: "PK", significado: "RUN numérico único del fondo mutuo ante la CMF.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Razón social oficial del fondo mutuo.", contable: "No aplica" },
      { name: "rut_agf", type: "VARCHAR", role: "FK", significado: "RUT de la Administradora General de Fondos gestora.", contable: "No aplica" },
      { name: "razon_social_agf", type: "VARCHAR", role: "Dimensión", significado: "Nombre de la Administradora General de Fondos (AGF).", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo de reporte anual en formato YYYYMM (ej. 202412).", contable: "No aplica" },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año calendario del ejercicio financiero auditado.", contable: "No aplica" },
      { name: "fecha_cierre", type: "VARCHAR", role: "Fecha", significado: "Fecha de cierre contable (31 de diciembre de cada año).", contable: "No aplica" },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activos totales auditados del fondo mutuo en millones de CLP.", contable: "Activo Bruto" },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Pasivos totales excluyendo el patrimonio atribuible a partícipes en millones de CLP.", contable: "Pasivo Exigible" },
      { name: "patrimonio_activo_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Activo neto atribuible a los partícipes (AUM / Patrimonio) en millones de CLP.", contable: "Patrimonio Neto" },
      { name: "utilidad_neta_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado neto del ejercicio después de impuestos en millones de CLP.", contable: "Resultado Neto" },
      { name: "efectivo_y_equivalentes_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo de caja, bancos e inversiones a la vista de muy corto plazo en millones de CLP.", contable: "Efectivo y Eq." },
      { name: "activos_financieros_vr_m_clp", type: "DOUBLE", role: "Métrica", significado: "Cartera de activos financieros medidos a valor razonable con cambios en resultados.", contable: "Valor Razonable / MtM" },
      { name: "activos_financieros_amortizado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Cartera de instrumentos de deuda mantenidos a costo amortizado en millones de CLP.", contable: "Costo Amortizado" },
      { name: "cuadre_activo_pasivo_patrimonio", type: "BOOLEAN", role: "Atributo", significado: "Indicador booleano que certifica que Activo = Pasivo + Patrimonio.", contable: "Ecuación Contable" }
    ]
  },
  {
    id: "ffmm_repos_detalle_historico",
    name: "ffmm.repos_detalle_historico",
    viewName: "ffmm_repos_detalle_historico",
    sector: "ffmm",
    sectorLabel: "Fondos Mutuos",
    norma: "IFRS / CMF Ley 20.712",
    corte: "2015-2025",
    frescura: "Panel Anual 2015-2025",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "Contratos Literales Históricos",
    descripcion: "Detalle contractual literal de 11 columnas de todas las operaciones de compra con retroventa (REPO / SFT) declaradas en la Nota 25 de los estados financieros de fondos mutuos chilenos entre 2015 y 2025.",
    origen: "Comisión para el Mercado Financiero (CMF) — Nota 25 de Estados Financieros Auditados (FMNO...pdf).",
    columnas: [
      { name: "run_fondo", type: "BIGINT", role: "PK", significado: "RUN del fondo mutuo comprador en el pacto de retroventa.", contable: "No aplica" },
      { name: "nombre_fondo", type: "VARCHAR", role: "Atributo", significado: "Razón social del fondo mutuo tenedor del contrato REPO.", contable: "No aplica" },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo anual de reporte contable (YYYYMM).", contable: "No aplica" },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año calendario del cierre contable.", contable: "No aplica" },
      { name: "fecha_compra", type: "VARCHAR", role: "Fecha", significado: "Fecha original de compra del instrumento financiero bajo pacto.", contable: "No aplica" },
      { name: "rut_contraparte", type: "VARCHAR", role: "FK", significado: "RUT institucional de la contraparte financiera vendedora.", contable: "No aplica" },
      { name: "nombre_contraparte", type: "VARCHAR", role: "Dimensión", significado: "Razón social de la institución financiera contraparte (Banco / Corredora).", contable: "No aplica" },
      { name: "nemotecnico", type: "VARCHAR", role: "Dimensión", significado: "Nemotécnico oficial del instrumento subyacente transado.", contable: "No aplica" },
      { name: "tipo_instrumento", type: "VARCHAR", role: "Dimensión", significado: "Tipo de instrumento subyacente (BTP, BTU, PDBC, BCU, BCP, DP).", contable: "No aplica" },
      { name: "unidades_nominales", type: "DOUBLE", role: "Métrica", significado: "Cantidad nominal comprometida en el contrato de retroventa.", contable: "No aplica" },
      { name: "total_transado_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto total transado al inicio del contrato en millones de CLP.", contable: "Pacto Activo (CRV)" },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha acordada de vencimiento de la promesa de venta.", contable: "No aplica" },
      { name: "precio_pactado_tasa", type: "VARCHAR", role: "Métrica", significado: "Precio pactado o tasa de interés de la operación.", contable: "No aplica" },
      { name: "saldo_al_cierre_m_clp", type: "DOUBLE", role: "Métrica", significado: "Saldo contable valorizado al cierre del ejercicio en millones de CLP.", contable: "Pacto Activo (CRV)" }
    ]
  },
  {
    id: "cooperativas_maestro",
    name: "cooperativas.maestro",
    viewName: "cooperativas_maestro",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito",
    norma: "CMF Chile / Ley General de Cooperativas (DFL 5)",
    corte: "2026-07",
    frescura: "Al día (7 entidades sistémicas)",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "7 cooperativas fiscalizadas",
    descripcion: "Catastro maestro y directorio institucional de las Cooperativas de Ahorro y Crédito (CAC) de importancia sistémica supervisadas por la CMF. Incluye Coopeuch, Oriencoop, Capual, Ahorrocoop, Detacoop, Coonfia y Coocretal con RUT canónico validado bajo Módulo 11.",
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
  },
  {
    id: "cooperativas_balance_resumen",
    name: "cooperativas.balance_resumen",
    viewName: "cooperativas_balance_resumen",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito",
    norma: "CMF Chile / Normativa Contable IFRS para Cooperativas",
    corte: "2018-01 a 2026-07",
    frescura: "Mensual (103 periodos consecutivos)",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "700+ balances mensuales",
    descripcion: "Panel mensual estandarizado de Estados Financieros IFRS, Colocaciones de Crédito y Captaciones en Depósitos a Plazo (DAP) para las Cooperativas de Ahorro y Crédito supervisadas por la CMF. Incorpora la identidad contable fundamental Activos = Pasivos + Patrimonio con conversión multimoneda (CLP y USD).",
    origen: "Comisión para el Mercado Financiero (CMF) — Reportes Financieros Mensuales de Cooperativas de Ahorro y Crédito.",
    columnas: [
      { name: "id_balance", type: "VARCHAR", role: "PK", significado: "Identificador sintético único del balance mensual (periodo_rut).", contable: "No aplica", interpretacion: "Clave primaria que garantiza cero duplicados por periodo y entidad." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo mensual contable de reporte (formato YYYY-MM).", contable: "Corte Mensual", interpretacion: "Eje temporal para análisis macroprudencial de series mensuales." },
      { name: "fecha_corte", type: "VARCHAR", role: "Fecha", significado: "Fecha del último día calendario del mes de reporte contable.", contable: "No aplica", interpretacion: "Fecha de cierre contable oficial." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT institucional de la cooperativa informante.", contable: "No aplica", interpretacion: "Clave foránea hacia el catálogo maestro de cooperativas." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal de la cooperativa.", contable: "No aplica", interpretacion: "Identificación corporativa en balances." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre de fantasía o marca comercial de la cooperativa.", contable: "No aplica", interpretacion: "Nombre simplificado de visualización (ej. COOPEUCH)." },
      { name: "total_activos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de activos financieros y crediticios de la cooperativa en millones de CLP.", contable: "Valor Razonable / Costo Amortizado", interpretacion: "Tamaño patrimonial total de la entidad." },
      { name: "total_activos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de activos convertido a millones de USD a tipo de cambio de cierre BCCh.", contable: "Conversión Spot USD", interpretacion: "Dimensión de balance en moneda internacional." },
      { name: "total_pasivos_m_clp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos exigibles a terceros en millones de CLP.", contable: "Costo Amortizado / Devengado", interpretacion: "Obligaciones totales de la cooperativa (ahorros, DAP, deudas con bancos)." },
      { name: "total_pasivos_m_usd", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos exigibles convertido a millones de USD.", contable: "Conversión Spot USD", interpretacion: "Masa de pasivos en divisa extranjera." },
      { name: "patrimonio_neto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto atribuible a socios y reservas en millones de CLP.", contable: "Capital Social y Fondos", interpretacion: "Base patrimonial de solvencia regulatoria de la cooperativa." },
      { name: "patrimonio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Patrimonio neto convertido a millones de USD.", contable: "Conversión Spot USD", interpretacion: "Capital propio en moneda extranjera." },
      { name: "utilidad_ejercicio_m_clp", type: "DOUBLE", role: "Métrica", significado: "Resultado neto acumulado del ejercicio (remanente / excedente) en millones de CLP.", contable: "Resultado Neto Acumulado", interpretacion: "Excedente financiero disponible para distribuir a los socios o capitalizar." },
      { name: "utilidad_ejercicio_m_usd", type: "DOUBLE", role: "Métrica", significado: "Utilidad o remanente del ejercicio en millones de USD.", contable: "Conversión Spot USD", interpretacion: "Rentabilidad neta del periodo en divisa extranjera." }
    ]
  },
  {
    id: "cooperativas_nota_efectivo_detalle",
    name: "cooperativas.nota_efectivo_detalle",
    viewName: "cooperativas_nota_efectivo_detalle",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito",
    norma: "CMF Chile / Notas Explicativas a los Estados Financieros Auditados (Notas 5 y 6)",
    corte: "2022-12 a 2025-12",
    frescura: "Anual Auditada (4 periodos comparativos)",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "122 registros atómicos",
    descripcion: "Desglose granular y auditado de Efectivo y Depósitos en Bancos (Nota 5 y Nota 6 de los EEFF auditados) para las 7 Cooperativas fiscalizadas por la CMF. Incluye efectivo en caja y sucursales, canje / clearing interbancario de valores en cobro, cuentas corrientes comerciales en bancos locales (desglosado por banco en Detacoop y Coopeuch), y total de liquidez inmediata reconciliado matemáticamente con el balance.",
    origen: "Comisión para el Mercado Financiero (CMF) — Notas a los Estados Financieros Anuales Auditados de Cooperativas de Ahorro y Crédito.",
    columnas: [
      { name: "id_registro", type: "VARCHAR", role: "PK", significado: "Identificador sintético único del registro (periodo_rut_slug_concepto).", contable: "No aplica", interpretacion: "Clave primaria atómica del desglose." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo anual de reporte contable auditado (YYYY-MM).", contable: "Corte Anual", interpretacion: "Eje temporal del ejercicio financiero auditado." },
      { name: "fecha_corte", type: "VARCHAR", role: "Fecha", significado: "Fecha oficial de cierre del ejercicio financiero (YYYY-MM-DD).", contable: "No aplica", interpretacion: "Cierre anual al 31 de diciembre." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT institucional de la cooperativa informante.", contable: "No aplica", interpretacion: "Clave foránea hacia el catálogo maestro de cooperativas." },
      { name: "nombre_empresa", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal de la cooperativa.", contable: "No aplica", interpretacion: "Identificación corporativa en balances." },
      { name: "nombre_fantasia", type: "VARCHAR", role: "Dimensión", significado: "Nombre de fantasía o marca comercial de la cooperativa.", contable: "No aplica", interpretacion: "Nombre simplificado de visualización (ej. COOPEUCH, DETACOOP)." },
      { name: "numero_nota", type: "VARCHAR", role: "Dimensión", significado: "Número y denominación de la nota en los EEFF auditados.", contable: "Nota Explicativa", interpretacion: "Nota 5 (Oriencoop, Detacoop, Ahorrocoop, Coocretal) o Nota 6 (Coopeuch, Capual, Coonfia)." },
      { name: "categoria_efectivo", type: "VARCHAR", role: "Dimensión", significado: "Categoría funcional estandarizada del componente de liquidez.", contable: "IFRS / CMF", interpretacion: "Valores: efectivo_caja, depositos_bancos_locales, valores_en_cobro, total_efectivo_bancos." },
      { name: "concepto_literal", type: "VARCHAR", role: "Dimensión", significado: "Texto literal del rubro según la nota de los estados financieros auditados.", contable: "Literal Nota EEFF", interpretacion: "Descripción exacta de la cuenta o desglose bancario." },
      { name: "institucion_contraparte", type: "VARCHAR", role: "Dimensión", significado: "Institución financiera contraparte donde se mantienen los fondos.", contable: "Contraparte Bancaria", interpretacion: "Banco comercial específico (ej. Banco de Chile, Scotiabank, Banco Estado) o sistema." },
      { name: "moneda_origen", type: "VARCHAR", role: "Dimensión", significado: "Moneda de registro contable original del saldo.", contable: "Moneda Funcional", interpretacion: "Pesos chilenos (CLP)." },
      { name: "monto_m_clp", type: "DOUBLE", role: "Métrica", significado: "Monto del saldo en millones de pesos chilenos (MM$ CLP).", contable: "Saldo al Cierre", interpretacion: "Monto nominal auditado." },
      { name: "tipo_cambio_cierre", type: "DOUBLE", role: "Métrica", significado: "Tipo de cambio spot oficial observado BCCh a la fecha de corte.", contable: "Tipo de Cambio Cierre", interpretacion: "Paridad USD/CLP de cierre de año." },
      { name: "monto_m_usd", type: "DOUBLE", role: "Métrica", significado: "Monto convertido a millones de dólares (MM$ USD).", contable: "Conversión Spot USD", interpretacion: "Magnitud estandarizada en divisa internacional." }
    ]
  },
  {
    id: "patrimonios_separados_balance_resumen",
    name: "patrimonios.balance_resumen",
    viewName: "patrimonios_separados_balance_resumen",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / NCG N° 136 y Ley de Mercado de Valores",
    corte: "2022-12 a 2024-12",
    frescura: "Anual Auditada",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "64 balances clasificados",
    descripcion: "Estados Financieros estandarizados de Patrimonios Separados administrados por Sociedades Securitizadoras reguladas. Incluye la identidad contable fundamental Activos = Pasivos + Excedentes/Deficit Acumulado, segregación de activos securitizados (corto y largo plazo) y pasivos por títulos de deuda emitidos.",
    origen: "Comisión para el Mercado Financiero (CMF) — Balances FECU y Estados Financieros Auditados.",
    columnas: [
      { name: "id_patrimonio", type: "VARCHAR", role: "PK", significado: "Identificador único sintético del patrimonio separado (rut_codigo).", contable: "No aplica", interpretacion: "Clave primaria atómica del vehículo." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT de la sociedad securitizadora administradora.", contable: "No aplica", interpretacion: "Clave foránea hacia securitizadoras_maestro." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal de la sociedad securitizadora.", contable: "No aplica", interpretacion: "Entidad fiduciaria administradora." },
      { name: "denominacion_ps", type: "VARCHAR", role: "Dimensión", significado: "Denominación legal completa del patrimonio separado.", contable: "No aplica", interpretacion: "Nombre formal en registro CMF." },
      { name: "codigo_emision", type: "VARCHAR", role: "Dimensión", significado: "Código nemotécnico o identificador de emisión (ej. BVOLS, BBICS-U).", contable: "No aplica", interpretacion: "Ticker de la serie o vehículo." },
      { name: "nro_registro_cmf", type: "VARCHAR", role: "Dimensión", significado: "Número de inscripción en el Registro de Valores de la CMF.", contable: "No aplica", interpretacion: "Identificador de registro regulatorio." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo anual de reporte contable (YYYY-MM).", contable: "Corte Anual", interpretacion: "Fecha de balance auditado." },
      { name: "disponible_mclp", type: "DOUBLE", role: "Métrica", significado: "Saldo en efectivo y depósitos bancarios de disponibilidad inmediata (M$ CLP).", contable: "Activo Circulante / Disponible", interpretacion: "Liquidez en cuentas corrientes." },
      { name: "valores_negociables_mclp", type: "DOUBLE", role: "Métrica", significado: "Inversiones de corto plazo y fondos mutuos de liquidez (M$ CLP).", contable: "Activo Circulante / Valores Negociables", interpretacion: "Instrumentos de caja transitoria." },
      { name: "activo_securitizado_corto_plazo_mclp", type: "DOUBLE", role: "Métrica", significado: "Porción corriente de la cartera de créditos y derechos securitizados (M$ CLP).", contable: "Activo Securitizado Corto Plazo", interpretacion: "Flujos de cobranza esperados a menos de 1 año." },
      { name: "otros_activos_circulantes_mclp", type: "DOUBLE", role: "Métrica", significado: "Otros activos circulantes, incluyendo operaciones de pacto repo (M$ CLP).", contable: "Otros Activos Circulantes", interpretacion: "Pactos de retroventa y cuentas transitorias." },
      { name: "total_activo_circulante_mclp", type: "DOUBLE", role: "Métrica", significado: "Total de activos circulantes del patrimonio separado (M$ CLP).", contable: "Total Activo Circulante", interpretacion: "Activo corriente total." },
      { name: "activo_securitizado_largo_plazo_mclp", type: "DOUBLE", role: "Métrica", significado: "Porción no corriente de la cartera securitizada de respaldo (M$ CLP).", contable: "Activo Securitizado Largo Plazo", interpretacion: "Flujos de mutuos hipotecarios, leasing o créditos a más de 1 año." },
      { name: "total_otros_activos_mclp", type: "DOUBLE", role: "Métrica", significado: "Total de otros activos no circulantes (M$ CLP).", contable: "Total Otros Activos", interpretacion: "Activos de largo plazo totales." },
      { name: "total_activos_mclp", type: "DOUBLE", role: "Métrica", significado: "Monto total del activo del patrimonio separado (M$ CLP).", contable: "Total Activos", interpretacion: "Masa total de bienes fideicomitidos." },
      { name: "deuda_bonos_corto_plazo_mclp", type: "DOUBLE", role: "Métrica", significado: "Obligaciones por títulos de deuda de securitización de vencimiento corriente (M$ CLP).", contable: "Pasivo Circulante / Bonos Securitizados", interpretacion: "Cupones y amortizaciones de bonos preferentes y subordinados a pagar a 1 año." },
      { name: "total_pasivo_circulante_mclp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos circulantes (M$ CLP).", contable: "Total Pasivo Circulante", interpretacion: "Obligaciones de corto plazo." },
      { name: "deuda_bonos_largo_plazo_mclp", type: "DOUBLE", role: "Métrica", significado: "Obligaciones por títulos de deuda de securitización a largo plazo (M$ CLP).", contable: "Pasivo Largo Plazo / Bonos Securitizados", interpretacion: "Saldo insoluto de bonos preferentes y subordinados emitidos." },
      { name: "total_pasivo_largo_plazo_mclp", type: "DOUBLE", role: "Métrica", significado: "Total de pasivos exigibles a largo plazo (M$ CLP).", contable: "Total Pasivo Largo Plazo", interpretacion: "Obligaciones no corrientes." },
      { name: "excedentes_acumulados_mclp", type: "DOUBLE", role: "Métrica", significado: "Excedentes o déficit acumulado atribuible al originador o aportantes (M$ CLP).", contable: "Patrimonio / Excedentes Acumulados", interpretacion: "Capital residual y reservas del patrimonio separado." },
      { name: "total_pasivo_patrimonio_mclp", type: "DOUBLE", role: "Métrica", significado: "Total pasivo más excedentes acumulados (M$ CLP).", contable: "Total Pasivo y Excedentes", interpretacion: "Total cuadre pasivo y patrimonio residual." },
      { name: "cuadre_contable_ok", type: "BOOLEAN", role: "Control", significado: "Verificación de cuadre contable matemático (Activos == Pasivos + Excedentes).", contable: "Control Matemático", interpretacion: "Validación de cuadre al peso." },
      { name: "disponible_musd", type: "DOUBLE", role: "Métrica", significado: "Disponible bancario expresado en millones de USD.", contable: "Conversión Spot USD", interpretacion: "Caja transitoria en divisa internacional." },
      { name: "total_activos_musd", type: "DOUBLE", role: "Métrica", significado: "Total de activos expresado en millones de USD.", contable: "Conversión Spot USD", interpretacion: "Tamaño total del patrimonio en dólares." },
      { name: "deuda_bonos_total_musd", type: "DOUBLE", role: "Métrica", significado: "Total deuda en bonos securitizados en millones de USD.", contable: "Conversión Spot USD", interpretacion: "Pasivo bursátil total en divisa internacional." }
    ]
  },
  {
    id: "patrimonios_separados_repos_detalle",
    name: "patrimonios.repos_detalle",
    viewName: "patrimonios_separados_repos_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Notas de Inversiones Transitorias y Otros Activos Circulantes",
    corte: "2022-12 a 2024-12",
    frescura: "Anual Auditada",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "74 operaciones repo auditadas",
    descripcion: "Registro granular de operaciones de compra con pacto de retroventa (Repos) realizadas por los patrimonios separados para la gestión de liquidez transitoria de los fondos de intereses y amortización, con identificación de contraparte, instrumento subyacente y tasa pactada.",
    origen: "Comisión para el Mercado Financiero (CMF) — Notas a los Estados Financieros de Patrimonios Separados.",
    columnas: [
      { name: "id_patrimonio", type: "VARCHAR", role: "PK", significado: "Identificador único sintético del patrimonio separado.", contable: "No aplica", interpretacion: "Clave primaria del vehículo emisor." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT institucional de la sociedad securitizadora gestora.", contable: "No aplica", interpretacion: "Clave foránea hacia securitizadoras_maestro." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal de la sociedad securitizadora.", contable: "No aplica", interpretacion: "Entidad fiduciaria administradora." },
      { name: "denominacion_ps", type: "VARCHAR", role: "Dimensión", significado: "Denominación legal completa del patrimonio separado.", contable: "No aplica", interpretacion: "Nombre formal del vehículo." },
      { name: "codigo_emision", type: "VARCHAR", role: "Dimensión", significado: "Código nemotécnico o identificador de emisión.", contable: "No aplica", interpretacion: "Ticker de la serie o vehículo." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo anual de reporte contable (YYYY-MM).", contable: "Corte Anual", interpretacion: "Eje temporal del ejercicio financiero." },
      { name: "contraparte", type: "VARCHAR", role: "Dimensión", significado: "Entidad financiera o corredora de bolsa contraparte del pacto.", contable: "Contraparte Repo", interpretacion: "Banco comercial o intermediario de valores." },
      { name: "instrumento_pacto", type: "VARCHAR", role: "Dimensión", significado: "Instrumento financiero colateral objeto del pacto (BTP, BTU, PDBC).", contable: "Colateral Repo", interpretacion: "Título de deuda soberana o de banco central." },
      { name: "emisor_subyacente", type: "VARCHAR", role: "Dimensión", significado: "Emisor soberano o institucional del título subyacente.", contable: "Emisor Colateral", interpretacion: "Tesorería General de la República o Banco Central de Chile." },
      { name: "fecha_inicio", type: "VARCHAR", role: "Fecha", significado: "Fecha de inicio de la operación de pacto (YYYY-MM-DD).", contable: "No aplica", interpretacion: "Fecha valor de desembolso." },
      { name: "fecha_vencimiento", type: "VARCHAR", role: "Fecha", significado: "Fecha de liquidación o retroventa pactada (YYYY-MM-DD).", contable: "No aplica", interpretacion: "Fecha de vencimiento del repo." },
      { name: "plazo_dias", type: "BIGINT", role: "Métrica", significado: "Plazo de la operación de retroventa en días corridos.", contable: "Plazo Contractual", interpretacion: "Duración de la inversión transitoria." },
      { name: "tasa_interes_anual_pct", type: "DOUBLE", role: "Métrica", significado: "Tasa de rendimiento anual pactada en la operación (%).", contable: "Tasa Pactada Repo", interpretacion: "Rendimiento pactado." },
      { name: "monto_mclp", type: "DOUBLE", role: "Métrica", significado: "Valor contable del pacto en miles de pesos chilenos (M$ CLP).", contable: "Valor Razonable Repo", interpretacion: "Monto invertido en el pacto." },
      { name: "monto_musd", type: "DOUBLE", role: "Métrica", significado: "Valor contable del pacto en millones de USD.", contable: "Conversión Spot USD", interpretacion: "Monto equivalente en moneda extranjera." },
      { name: "cumplimiento_calificacion", type: "VARCHAR", role: "Control", significado: "Indicador de cumplimiento de requisitos de clasificación de riesgo reglamentarios.", contable: "Regulación CMF", interpretacion: "Calificación crediticia de elegibilidad (Cumple / SI)." }
    ]
  },
  {
    id: "patrimonios_separados_cartera_morosidad_detalle",
    name: "patrimonios.cartera_morosidad_detalle",
    viewName: "patrimonios_separados_cartera_morosidad_detalle",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados (CMF / Ley 18.045)",
    norma: "CMF Chile / Notas de Activo Securitizado en Mora y Provisiones",
    corte: "2022-12 a 2024-12",
    frescura: "Anual Auditada",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "67 tramos de morosidad",
    descripcion: "Clasificación de la cartera de activos securitizados (créditos sociales, mutuos hipotecarios, leasing habitacional) por tramos de mora, número de deudores, valor par y provisiones de deterioro constituidas según normas CMF.",
    origen: "Comisión para el Mercado Financiero (CMF) — Notas a los Estados Financieros de Patrimonios Separados.",
    columnas: [
      { name: "id_patrimonio", type: "VARCHAR", role: "PK", significado: "Identificador único sintético del patrimonio separado.", contable: "No aplica", interpretacion: "Clave primaria del vehículo emisor." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "RUT institucional de la sociedad securitizadora gestora.", contable: "No aplica", interpretacion: "Clave foránea hacia securitizadoras_maestro." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Dimensión", significado: "Razón social legal de la sociedad securitizadora.", contable: "No aplica", interpretacion: "Entidad fiduciaria administradora." },
      { name: "denominacion_ps", type: "VARCHAR", role: "Dimensión", significado: "Denominación legal completa del patrimonio separado.", contable: "No aplica", interpretacion: "Nombre formal del vehículo." },
      { name: "codigo_emision", type: "VARCHAR", role: "Dimensión", significado: "Código nemotécnico o identificador de emisión.", contable: "No aplica", interpretacion: "Ticker de la serie o vehículo." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Periodo anual de reporte contable (YYYY-MM).", contable: "Corte Anual", interpretacion: "Eje temporal del ejercicio financiero." },
      { name: "tramo_mora", type: "VARCHAR", role: "Dimensión", significado: "Tramo de morosidad de la cartera securitizada (Al día, 1-30 días, etc.).", contable: "Antigüedad Cartera", interpretacion: "Bucket de riesgo crediticio de los créditos subyacentes." },
      { name: "numero_deudores", type: "BIGINT", role: "Métrica", significado: "Cantidad de deudores u operaciones en el tramo de mora correspondiente.", contable: "Métrica Operativa", interpretacion: "Volumen de créditos o deudores." },
      { name: "monto_cartera_mclp", type: "DOUBLE", role: "Métrica", significado: "Valor par o saldo insoluto de los créditos en el tramo (M$ CLP).", contable: "Saldo Insoluto Cartera", interpretacion: "Exposición bruta al riesgo crediticio." },
      { name: "provision_mclp", type: "DOUBLE", role: "Métrica", significado: "Monto de provisiones de deterioro constituidas para el tramo (M$ CLP).", contable: "Provisión Deterioro Cartera", interpretacion: "Castigo o cobertura de pérdida esperada." },
      { name: "porcentaje_provision_pct", type: "DOUBLE", role: "Métrica", significado: "Porcentaje de cobertura de provisión sobre el valor par (%).", contable: "Tasa Cobertura Provisión", interpretacion: "Severidad de la provisión." }
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
            <button class="dict-filter-btn ${this.currentSector === 'vida' ? 'active' : ''}" data-sec="vida">Vida</button>
            <button class="dict-filter-btn ${this.currentSector === 'generales' ? 'active' : ''}" data-sec="generales">Generales</button>
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
            <button class="dict-filter-btn ${this.currentSector === 'retail_financiero' ? 'active' : ''}" data-sec="retail_financiero">Retail Financiero</button>
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

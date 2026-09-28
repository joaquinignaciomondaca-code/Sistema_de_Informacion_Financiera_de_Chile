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
    registros: "9,09 M registros",
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
    registros: "142.944 registros",
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
    registros: "2,01 M registros",
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
    name: "vida.derivados_forwards",
    viewName: "vida_forwards",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Formulario B-7 (Derivados CMF)",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "165.354 registros",
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
    name: "vida.derivados_swaps",
    viewName: "vida_swaps",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Formulario B-7 (Derivados CMF)",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "314.683 registros",
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
    name: "vida.pactos_repos",
    viewName: "vida_repos",
    sector: "vida",
    sectorLabel: "Seguros de Vida",
    norma: "Formulario B-7 (Pactos y Repos CMF)",
    corte: "2026-03",
    frescura: "Al dia (2026-03)",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "19.408 registros",
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
    registros: "287.214 registros",
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
    registros: "38.257 registros",
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
    registros: "17.457 registros",
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
    id: "patrimonios_separados_balance_fsb",
    name: "patrimonios_separados.balance_fsb",
    viewName: "patrimonios_separados_balance_fsb",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados",
    norma: "Balance del patrimonio separado (EEFF CMF), métricas FSB EF5",
    corte: "Diciembre 2014 a diciembre 2025 (2010–2013 sin datos)",
    frescura: "Anual, cierre de diciembre",
    modo: "Excel de lectura de los PDF (NotebookLM), recalculado y validado",
    ultimaActualizacion: "2026-09-28",
    registros: "358 balances",
    descripcion: "Un balance por patrimonio separado y cierre de diciembre. Las cifras se calculan desde las cuentas de balance_cuentas, no se copian de la hoja resumen del Excel, y todos los balances cuadran (activos = pasivos + patrimonio). Métricas FSB: CI2 = cartera securitizada / activos totales, MT2 = pasivos de corto plazo / activos de corto plazo y L5 = (activos − patrimonio) / activos. Hay 10 balances con revisar = true: en 4 la hoja resumen del Excel trae otros totales y en 6 solo cambia la cartera securitizada. La serie parte en diciembre de 2014: de 2010 a 2013 no hay datos publicados (2013 no está en la fuente y 2010–2012 se dejaron fuera para no cortar la serie; eran además los años más dudosos).",
    origen: "Estados financieros de cada patrimonio separado (CMF) → securitizadoras/fuentes/FSB_Patrimonio_Separado_v4.xlsx → securitizadoras/scripts/05_publicar_balance_patrimonios_fsb.py",
    columnas: [
      { name: "archivo", type: "VARCHAR", role: "PK", significado: "Nombre del PDF de estados financieros leído.", contable: "No aplica", interpretacion: "Una fila por documento. Une con balance_cuentas." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "Cuerpo del RUT de la securitizadora (8 dígitos, sin DV).", contable: "No aplica", interpretacion: "Une con securitizadoras_maestro.rut y patrimonios_separados_maestro.rut_administradora." },
      { name: "rut_completo", type: "VARCHAR", role: "Atributo", significado: "RUT con dígito verificador módulo 11.", contable: "No aplica", interpretacion: "Para mostrar." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Dimensión", significado: "Securitizadora que administra el patrimonio.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_patrimonio", type: "VARCHAR", role: "Dimensión", significado: "Código del patrimonio separado según el nombre del PDF (p. ej. BTRA15, PS13).", contable: "No aplica", interpretacion: "No siempre coincide con el número de inscripción de lista_emisiones." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Cierre del balance, AAAA-MM (siempre diciembre).", contable: "Corte", interpretacion: "Cierre anual." },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año del cierre.", contable: "No aplica", interpretacion: "Sale del periodo." },
      { name: "total_activos_m_clp", type: "BIGINT", role: "Métrica", significado: "Total activos (TFA en la metodología FSB), en M$.", contable: "Total Activos", interpretacion: "Tamaño del vehículo." },
      { name: "cartera_securitizada_m_clp", type: "BIGINT", role: "Métrica", significado: "Activo securitizado de corto y largo plazo, neto de provisiones (Loans en FSB), en M$.", contable: "Activo securitizado ± provisiones", interpretacion: "Numerador de CI2. Las provisiones vienen negativas y se restan." },
      { name: "activos_corto_plazo_m_clp", type: "BIGINT", role: "Métrica", significado: "Total activo circulante, en M$.", contable: "Activo Circulante", interpretacion: "Denominador de MT2." },
      { name: "pasivos_corto_plazo_m_clp", type: "BIGINT", role: "Métrica", significado: "Total pasivo circulante, en M$.", contable: "Pasivo Circulante", interpretacion: "Numerador de MT2." },
      { name: "pasivos_largo_plazo_m_clp", type: "BIGINT", role: "Métrica", significado: "Total pasivo no circulante (principalmente bonos securitizados), en M$.", contable: "Pasivo No Circulante", interpretacion: "Deuda de largo plazo." },
      { name: "patrimonio_m_clp", type: "BIGINT", role: "Métrica", significado: "Total patrimonio o excedente acumulado, en M$. Suele ser negativo.", contable: "Patrimonio (Excedente Acumulado)", interpretacion: "Si es negativo, el vehículo debe más de lo que tiene. Por eso L5 queda sobre 1." },
      { name: "ci2_intermediacion_credito", type: "DOUBLE", role: "Métrica", significado: "Cartera securitizada / total activos.", contable: "FSB EF5 CI2", interpretacion: "Qué parte del activo es crédito." },
      { name: "mt2_transformacion_plazos", type: "DOUBLE", role: "Métrica", significado: "Pasivos de corto plazo / activos de corto plazo.", contable: "FSB EF5 MT2", interpretacion: "Sobre 1 indica presión de liquidez. Es nulo si no hay activo circulante." },
      { name: "l5_apalancamiento", type: "DOUBLE", role: "Métrica", significado: "(Total activos − patrimonio) / total activos.", contable: "FSB EF5 L5", interpretacion: "Sobre 1 cuando el patrimonio es negativo." },
      { name: "motivo_revision", type: "VARCHAR", role: "Atributo", significado: "Por qué el balance está marcado para revisar. Nulo si no hay reparos.", contable: "Calidad de dato", interpretacion: "Lista de reparos separados por punto y coma." },
      { name: "revisar", type: "BOOLEAN", role: "Atributo", significado: "Verdadero si hay dudas sobre la lectura de este balance.", contable: "Calidad de dato", interpretacion: "Filtrar con revisar = false para análisis conservadores." }
    ]
  },
  {
    id: "patrimonios_separados_balance_cuentas",
    name: "patrimonios_separados.balance_cuentas",
    viewName: "patrimonios_separados_balance_cuentas",
    sector: "patrimonios_separados",
    sectorLabel: "Patrimonios Separados",
    norma: "Balance del patrimonio separado (EEFF CMF)",
    corte: "Diciembre 2014 a diciembre 2025 (2010–2013 sin datos)",
    frescura: "Anual, cierre de diciembre",
    modo: "Excel de lectura de los PDF (NotebookLM), validado",
    ultimaActualizacion: "2026-09-28",
    registros: "7.962 cuentas",
    descripcion: "Cada cuenta del balance tal como viene impresa, en M$ y con su signo, para 358 balances de 10 securitizadoras. La serie parte en diciembre de 2014: de 2010 a 2013 no hay datos publicados (2013 no está en la fuente y 2010–2012 se dejaron fuera para no cortar la serie; eran además los años más dudosos). Incluye las líneas de subtotal (Total Activo Circulante, Total Activos, etc.). Si sumas cuentas, filtra por categorías de detalle o usa balance_fsb para no contar dos veces. Se descartaron 4 filas vacías del Excel.",
    origen: "securitizadoras/fuentes/FSB_Patrimonio_Separado_v4.xlsx, hoja Detalle_de_Cuentas.",
    columnas: [
      { name: "archivo", type: "VARCHAR", role: "FK", significado: "PDF de donde sale la cuenta.", contable: "No aplica", interpretacion: "Une con balance_fsb." },
      { name: "rut_administradora", type: "VARCHAR", role: "FK", significado: "Cuerpo del RUT de la securitizadora (8 dígitos).", contable: "No aplica", interpretacion: "Une con securitizadoras_maestro.rut." },
      { name: "rut_completo", type: "VARCHAR", role: "Atributo", significado: "RUT con dígito verificador.", contable: "No aplica", interpretacion: "Para mostrar." },
      { name: "nombre_administradora", type: "VARCHAR", role: "Dimensión", significado: "Securitizadora.", contable: "No aplica", interpretacion: "Gestora." },
      { name: "codigo_patrimonio", type: "VARCHAR", role: "Dimensión", significado: "Código del patrimonio separado.", contable: "No aplica", interpretacion: "Según el nombre del PDF." },
      { name: "periodo", type: "VARCHAR", role: "Dimensión", significado: "Cierre AAAA-MM.", contable: "Corte", interpretacion: "Siempre diciembre." },
      { name: "anio", type: "BIGINT", role: "Dimensión", significado: "Año del cierre.", contable: "No aplica", interpretacion: "Sale del periodo." },
      { name: "orden_en_balance", type: "BIGINT", role: "Atributo", significado: "Posición de la cuenta en el balance impreso.", contable: "No aplica", interpretacion: "Ordena como en el PDF." },
      { name: "categoria", type: "VARCHAR", role: "Dimensión", significado: "Rubro: Activo Circulante, Activo No Circulante, Pasivo Circulante, Pasivo No Circulante, Patrimonio, o una línea Total ….", contable: "Clasificación del balance", interpretacion: "Las categorías que empiezan con Total son subtotales." },
      { name: "cuenta", type: "VARCHAR", role: "Dimensión", significado: "Nombre de la cuenta, copiado del balance.", contable: "Glosa", interpretacion: "No se renombró." },
      { name: "monto_m_clp", type: "BIGINT", role: "Métrica", significado: "Monto impreso en M$, con su signo.", contable: "M$", interpretacion: "Las provisiones y los déficits vienen negativos." },
      { name: "categoria_fsb", type: "VARCHAR", role: "Dimensión", significado: "Rol de la cuenta en las métricas FSB: Loans, Short-term assets, Short-term liabilities, Total Financial Assets, Equity. Nulo en las demás.", contable: "Mapeo FSB del Excel", interpretacion: "Loans = activo securitizado y sus provisiones." },
      { name: "revisar", type: "BOOLEAN", role: "Atributo", significado: "Copiado del balance: verdadero si hay dudas sobre ese documento.", contable: "Calidad de dato", interpretacion: "El motivo está en balance_fsb.motivo_revision." }
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
    registros: "1.572 balances",
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
  {
    id: "sistemas_pago_balances",
    name: "sistemas_pago.balances",
    viewName: "sistemas_pago_balances",
    sector: "sistemas_pago",
    sectorLabel: "Sistemas de Pago",
    norma: "Normas Internacionales de Información Financiera (IFRS) adoptadas por CMF",
    corte: "Trimestral (2018-03 a 2026-06)",
    frescura: "Trimestral",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "82 registros",
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
    name: "sistemas_pago.estadisticas_bcch",
    viewName: "sistemas_pago_estadisticas_bcch",
    sector: "sistemas_pago",
    sectorLabel: "Sistemas de Pago",
    norma: "Ley 18.840 / Informe de Sistemas de Pago (ISiP) y Base de Datos Estadísticos BCCh",
    corte: "Mensual (2018-01 a 2026-06)",
    frescura: "Mensual",
    modo: "Automático",
    ultimaActualizacion: "2026-09-23",
    registros: "102 registros",
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
    registros: "262 registros",
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
    registros: "262 registros",
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
    registros: "288 balances",
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
    registros: "213 registros",
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
    registros: "52 registros",
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
    registros: "158 operaciones",
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
    registros: "268 registros",
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
  },
  {
    id: "cooperativas_cmf_balance",
    name: "cooperativas.cmf_balance",
    viewName: "cooperativas_cmf_balance",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito",
    norma: "CMF Chile — Reporte Financiero de Cooperativas de Ahorro y Crédito (plan de cuentas 2017+)",
    corte: "2017-01 a 2026-07 (115 meses)",
    frescura: "Publicación mensual automática; la serie completa se valida y se publica en bloque",
    modo: "Automático CMF con validación fail-closed",
    registros: "23.345 registros (activos y pasivos por concepto)",
    descripcion: "Balance de cada cooperativa fiscalizada por la CMF al grano concepto contable: activos (efectivo, instrumentos, colocaciones y provisiones) y pasivos (depósitos y captaciones, préstamos, provisiones y patrimonio). Montos en millones de pesos tal como los publica la fuente. Antes de 2017 la CMF usaba otra planilla y otro plan de cuentas: esa parte no se mezcla en esta serie.",
    origen: "CMF — Reporte Financiero de Cooperativas de Ahorro y Crédito (planilla mensual, hojas Activos y Pasivos Cooperativas).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Clave determinística del registro (período + RUT + sección + código de concepto).", contable: "No aplica", interpretacion: "Identifica una celda contable única de la planilla CMF." },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Período mensual de la planilla CMF en formato YYYY-MM.", contable: "No aplica", interpretacion: "Eje temporal mensual de la serie (2017-01 en adelante)." },
      { name: "fecha_corte", type: "VARCHAR", role: "Fecha", significado: "Último día calendario del mes informado, en formato ISO (AAAA-MM-DD).", contable: "No aplica", interpretacion: "Fecha de cierre del balance o del acumulado." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT de la cooperativa informante, tomado del catálogo maestro validado.", contable: "No aplica", interpretacion: "Enlaza con cooperativas.lista_entidades." },
      { name: "cooperativa", type: "VARCHAR", role: "Dimensión", significado: "Nombre de fantasía de la cooperativa (COOPEUCH, CAPUAL, ...).", contable: "No aplica", interpretacion: "Identificación de la entidad que reporta." },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "balance (saldos al cierre) o resultados (acumulado del año a la fecha).", contable: "Naturaleza del saldo", interpretacion: "Evita confundir un saldo con un acumulado del ejercicio." },
      { name: "seccion", type: "VARCHAR", role: "Clasificación", significado: "Hoja de origen: activos, pasivos, resultados o margen.", contable: "No aplica", interpretacion: "Permite filtrar por estado financiero y por hoja CMF." },
      { name: "orden", type: "INTEGER", role: "Orden", significado: "Posición del concepto dentro de su hoja, en el orden de la planilla CMF.", contable: "No aplica", interpretacion: "Reconstruye el orden de las líneas tal como las publica la CMF." },
      { name: "codigo_concepto", type: "VARCHAR", role: "Clave", significado: "Código estable del concepto (activos_totales, depositos_plazo, margen_intereses, ...).", contable: "No aplica", interpretacion: "Clave para series y cruces entre períodos." },
      { name: "glosa", type: "VARCHAR", role: "Atributo", significado: "Nombre del concepto en lenguaje contable.", contable: "Nombre de la cuenta", interpretacion: "Texto legible del rubro." },
      { name: "nivel", type: "INTEGER", role: "Atributo", significado: "Profundidad del concepto en la jerarquía de la planilla (0 = total).", contable: "Jerarquía de cuentas", interpretacion: "Distingue totales de sus componentes; no sumar niveles distintos." },
      { name: "monto_mm_clp", type: "BIGINT", role: "Métrica", significado: "Monto en millones de pesos, tal como lo publica la CMF (sin reinterpretar).", contable: "Saldo al cierre o acumulado", interpretacion: "Cifra oficial de la fuente; el signo lo define la CMF." },
      { name: "base_monto", type: "VARCHAR", role: "Atributo", significado: "saldo al cierre (balance) o acumulado del año a la fecha (resultados).", contable: "Base de medición", interpretacion: "Indica si el monto es foto del mes o flujo del año." },
      { name: "fuente_url", type: "VARCHAR", role: "Procedencia", significado: "URL de la planilla CMF descargada para ese período.", contable: "No aplica", interpretacion: "Trazabilidad directa a la fuente oficial." },
      { name: "sha256_fuente", type: "VARCHAR", role: "Procedencia", significado: "Hash SHA-256 del archivo CMF usado.", contable: "No aplica", interpretacion: "Permite verificar que la cifra viene del archivo exacto." }
    ]
  },
  {
    id: "cooperativas_cmf_resultados",
    name: "cooperativas.cmf_resultados",
    viewName: "cooperativas_cmf_resultados",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito",
    norma: "CMF Chile — Reporte Financiero de Cooperativas de Ahorro y Crédito (plan de cuentas 2017+)",
    corte: "2017-01 a 2026-07 (115 meses)",
    frescura: "Publicación mensual automática; la serie completa se valida y se publica en bloque",
    modo: "Automático CMF con validación fail-closed",
    registros: "28.980 registros (resultados y margen por concepto)",
    descripcion: "Estado de resultados de cada cooperativa fiscalizada por la CMF, al grano concepto contable: margen de intereses, comisiones netas, gasto en provisiones, gastos de apoyo, resultado del ejercicio y castigos, más el desglose de margen y comisiones. Los montos son acumulados del año a la fecha, tal como los publica la fuente.",
    origen: "CMF — Reporte Financiero de Cooperativas de Ahorro y Crédito (planilla mensual, hojas Estado Resultados Coop y Margen Interes - Comisiones).",
    columnas: [
      { name: "id", type: "VARCHAR", role: "PK", significado: "Clave determinística del registro (período + RUT + sección + código de concepto).", contable: "No aplica", interpretacion: "Identifica una celda contable única de la planilla CMF." },
      { name: "periodo", type: "VARCHAR", role: "Fecha", significado: "Período mensual de la planilla CMF en formato YYYY-MM.", contable: "No aplica", interpretacion: "Eje temporal mensual de la serie (2017-01 en adelante)." },
      { name: "fecha_corte", type: "VARCHAR", role: "Fecha", significado: "Último día calendario del mes informado, en formato ISO (AAAA-MM-DD).", contable: "No aplica", interpretacion: "Fecha de cierre del balance o del acumulado." },
      { name: "rut", type: "VARCHAR", role: "FK", significado: "RUT de la cooperativa informante, tomado del catálogo maestro validado.", contable: "No aplica", interpretacion: "Enlaza con cooperativas.lista_entidades." },
      { name: "cooperativa", type: "VARCHAR", role: "Dimensión", significado: "Nombre de fantasía de la cooperativa (COOPEUCH, CAPUAL, ...).", contable: "No aplica", interpretacion: "Identificación de la entidad que reporta." },
      { name: "estado", type: "VARCHAR", role: "Atributo", significado: "balance (saldos al cierre) o resultados (acumulado del año a la fecha).", contable: "Naturaleza del saldo", interpretacion: "Evita confundir un saldo con un acumulado del ejercicio." },
      { name: "seccion", type: "VARCHAR", role: "Clasificación", significado: "Hoja de origen: activos, pasivos, resultados o margen.", contable: "No aplica", interpretacion: "Permite filtrar por estado financiero y por hoja CMF." },
      { name: "orden", type: "INTEGER", role: "Orden", significado: "Posición del concepto dentro de su hoja, en el orden de la planilla CMF.", contable: "No aplica", interpretacion: "Reconstruye el orden de las líneas tal como las publica la CMF." },
      { name: "codigo_concepto", type: "VARCHAR", role: "Clave", significado: "Código estable del concepto (activos_totales, depositos_plazo, margen_intereses, ...).", contable: "No aplica", interpretacion: "Clave para series y cruces entre períodos." },
      { name: "glosa", type: "VARCHAR", role: "Atributo", significado: "Nombre del concepto en lenguaje contable.", contable: "Nombre de la cuenta", interpretacion: "Texto legible del rubro." },
      { name: "nivel", type: "INTEGER", role: "Atributo", significado: "Profundidad del concepto en la jerarquía de la planilla (0 = total).", contable: "Jerarquía de cuentas", interpretacion: "Distingue totales de sus componentes; no sumar niveles distintos." },
      { name: "monto_mm_clp", type: "BIGINT", role: "Métrica", significado: "Monto en millones de pesos, tal como lo publica la CMF (sin reinterpretar).", contable: "Saldo al cierre o acumulado", interpretacion: "Cifra oficial de la fuente; el signo lo define la CMF." },
      { name: "base_monto", type: "VARCHAR", role: "Atributo", significado: "saldo al cierre (balance) o acumulado del año a la fecha (resultados).", contable: "Base de medición", interpretacion: "Indica si el monto es foto del mes o flujo del año." },
      { name: "fuente_url", type: "VARCHAR", role: "Procedencia", significado: "URL de la planilla CMF descargada para ese período.", contable: "No aplica", interpretacion: "Trazabilidad directa a la fuente oficial." },
      { name: "sha256_fuente", type: "VARCHAR", role: "Procedencia", significado: "Hash SHA-256 del archivo CMF usado.", contable: "No aplica", interpretacion: "Permite verificar que la cifra viene del archivo exacto." }
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
    registros: "294 balances",
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
    name: "cooperativas.nota_efectivo",
    viewName: "cooperativas_nota_efectivo_detalle",
    sector: "cooperativas",
    sectorLabel: "Cooperativas de Ahorro y Crédito",
    norma: "CMF Chile / Notas Explicativas a los Estados Financieros Auditados (Notas 5 y 6)",
    corte: "2022-12 a 2025-12",
    frescura: "Anual Auditada (4 periodos comparativos)",
    modo: "Automático Streaming RAM CMF",
    ultimaActualizacion: "2026-09-24",
    registros: "122 registros",
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

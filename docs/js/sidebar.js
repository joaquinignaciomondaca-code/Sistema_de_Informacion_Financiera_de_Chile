/**
 * Explorer Tree Controller (Patron DBeaver / Supabase Studio / VS Code)
 * Sistema de Información Financiera de Chile
 * Navegacion jerarquica de alta densidad por Grupos, Sectores, Circulares y Tablas.
 * Sin emojis.
 */

// Iconos vectoriales limpios (SVG)
const ICONS = {
  chevronDown: `<svg class="tree-arrow open" width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M12.78 6.22a.75.75 0 010 1.06l-4.25 4.25a.75.75 0 01-1.06 0L3.22 7.28a.75.75 0 011.06-1.06L8 9.69l3.72-3.47a.75.75 0 011.06 0z"/></svg>`,
  chevronRight: `<svg class="tree-arrow" width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M6.22 3.22a.75.75 0 011.06 0l4.25 4.25a.75.75 0 010 1.06l-4.25 4.25a.75.75 0 01-1.06-1.06L9.69 8 6.22 4.28a.75.75 0 010-1.06z"/></svg>`,
  folder: `<svg class="tree-icon icon-folder" width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path d="M1.75 2.5a.25.25 0 00-.25.25v10.5c0 .138.112.25.25.25h12.5a.25.25 0 00.25-.25V5.5a.25.25 0 00-.25-.25H7.81a.75.75 0 01-.53-.22L5.81 3.56a.75.75 0 00-.53-.22H1.75z"/></svg>`,
  table: `<svg class="tree-icon icon-table" width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M1.5 2.5A1.5 1.5 0 013 1h10a1.5 1.5 0 011.5 1.5v11A1.5 1.5 0 0113 15H3a1.5 1.5 0 01-1.5-1.5v-11zM3 2.5a.5.5 0 00-.5.5V5h11V3a.5.5 0 00-.5-.5H3zm10.5 4h-4v7h4a.5.5 0 00.5-.5v-6.5zm-5.5 7V6.5h-5.5v6.5a.5.5 0 00.5.5h5z"/></svg>`,
  database: `<svg class="tree-icon icon-db" width="13" height="13" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1c3.866 0 7 1.12 7 2.5v10c0 1.38-3.134 2.5-7 2.5s-7-1.12-7-2.5v-10C1 2.12 4.134 1 8 1zm0 1.5c-3.176 0-5.5.86-5.5 1s2.324 1 5.5 1 5.5-.86 5.5-1-2.324-1-5.5-1zm5.5 4.385C12.39 7.494 10.378 8 8 8s-4.39-.506-5.5-1.115v2.23C3.61 9.724 5.622 10.23 8 10.23s4.39-.506 5.5-1.115v-2.23zm0 4C12.39 11.494 10.378 12 8 12s-4.39-.506-5.5-1.115v2.23c1.11.609 3.122 1.115 5.5 1.115s4.39-.506 5.5-1.115v-2.23z"/></svg>`,
  search: `<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M11.5 7a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zm-.82 4.74a6 6 0 111.06-1.06l3.04 3.04a.75.75 0 11-1.06 1.06l-3.04-3.04z"/></svg>`
};

const EXPLORER_TREE = [
  {
    id: "group_seguros",
    type: "group",
    label: "COMPAÑIAS DE SEGUROS (CMF)",
    badges: [
      { type: "entities", text: "Vida y generales", title: "Compañías de seguros de vida y generales que informan su cartera a la CMF (Circular 1835)" },
      { type: "data", text: "Mensual · 2016–2026", title: "Cartera mensual validada: se actualiza sola 3 veces al mes y cada mes se valida antes de publicarse" }
    ],
    status: "active",
    children: [
      {
        id: "sector_seguros",
        type: "sector",
        label: "Seguros de Vida y Generales (CMF)",
        sector: "seguros",
        children: [
          {
            id: "cat_seguros_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "Desde los reportes",
            badgeType: "entities",
            status: "active",
            sector: "seguros",
            chips: [
              { label: "Compañías que reportan en el último mes", query: "SELECT sector, rut_aseguradora, nombre_aseguradora, primer_periodo, meses_reportados FROM seguros_lista_entidades WHERE reporta_ultimo_mes ORDER BY sector, nombre_aseguradora;" },
              { label: "Compañías que dejaron de reportar", query: "SELECT sector, rut_aseguradora, nombre_aseguradora, primer_periodo, ultimo_periodo FROM seguros_lista_entidades WHERE NOT reporta_ultimo_mes ORDER BY ultimo_periodo DESC;" },
              { label: "Compañías que empezaron a reportar más recientemente", query: "SELECT sector, rut_aseguradora, nombre_aseguradora, primer_periodo FROM seguros_lista_entidades ORDER BY primer_periodo DESC, nombre_aseguradora LIMIT 10;" }
            ],
            tables: [
              { id: "seguros_lista_entidades", name: "seguros.lista_entidades", rows: "Una fila por compañía y sector", file: "outputs/seguros/aseguradoras.parquet" }
            ]
          },
          {
            id: "cat_seguros_cartera_1835",
            type: "circular",
            label: "Circular 1835 · Cartera de inversiones",
            badge: "Mensual validada",
            badgeType: "data",
            status: "active",
            sector: "seguros",
            chips: [
              { label: "Renta fija por tipo de instrumento, último mes (M$)", query: "SELECT sector, tipo_instrumento, count(*) AS instrumentos, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_renta_fija WHERE periodo = (SELECT max(periodo) FROM seguros_renta_fija) GROUP BY sector, tipo_instrumento ORDER BY valor_final_m_clp DESC LIMIT 15;" },
              { label: "Instrumentos de renta fija con más inversión, último mes (M$)", query: "SELECT nemotecnico, count(DISTINCT rut_aseguradora) AS aseguradoras, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_renta_fija WHERE periodo = (SELECT max(periodo) FROM seguros_renta_fija) GROUP BY nemotecnico ORDER BY valor_final_m_clp DESC LIMIT 10;" },
              { label: "Acciones con mayor inversión, último mes (M$)", query: "SELECT nemotecnico, count(DISTINCT rut_aseguradora) AS aseguradoras, SUM(unidades) AS unidades, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_acciones WHERE periodo = (SELECT max(periodo) FROM seguros_acciones) GROUP BY nemotecnico ORDER BY valor_final_m_clp DESC LIMIT 10;" },
              { label: "Evolución de la inversión en acciones por sector (M$)", query: "SELECT periodo, sector, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_acciones GROUP BY periodo, sector ORDER BY periodo DESC, sector LIMIT 24;" },
              { label: "Fondos mutuos por administradora, último mes (M$)", query: "SELECT rut_administradora, count(*) AS inversiones, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_fondos_mutuos WHERE periodo = (SELECT max(periodo) FROM seguros_fondos_mutuos) GROUP BY rut_administradora ORDER BY valor_final_m_clp DESC LIMIT 10;" },
              { label: "Bienes raíces por ciudad, último mes (M$)", query: "SELECT ciudad, count(*) AS inmuebles, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_bienes_raices WHERE periodo = (SELECT max(periodo) FROM seguros_bienes_raices) GROUP BY ciudad ORDER BY valor_final_m_clp DESC LIMIT 10;" },
              { label: "Otras inversiones por tipo de instrumento, último mes (M$)", query: "SELECT tipo_instrumento, count(*) AS inversiones, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_otras_inversiones WHERE periodo = (SELECT max(periodo) FROM seguros_otras_inversiones) GROUP BY tipo_instrumento ORDER BY valor_final_m_clp DESC LIMIT 15;" },
              { label: "Inversiones en el extranjero por país, último mes (M$)", query: "SELECT pais, tipo_registro, count(*) AS instrumentos, SUM(valor_final_m_clp) AS valor_final_m_clp FROM seguros_extranjeros WHERE periodo = (SELECT max(periodo) FROM seguros_extranjeros) GROUP BY pais, tipo_registro ORDER BY valor_final_m_clp DESC LIMIT 10;" }
            ],
            tables: [
              { id: "seguros_renta_fija", name: "B.1 INSTRUMENTOS DE RENTA FIJA", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/renta_fija/manifest.json"] },
              { id: "seguros_renta_fija_relevante", name: "B.1 INSTRUMENTOS DE RENTA FIJA", rows: "Vista de campos relevantes · desde 2024-12", file: "", files: ["outputs/seguros/renta_fija_relevante/manifest.json"] },
              { id: "seguros_acciones", name: "B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS Y CUOTAS DE FONDOS DE INVERSIÓN", rows: "Mensual · desde 2016-11", file: "", files: ["outputs/seguros/acciones/manifest.json"] },
              { id: "seguros_acciones_relevantes", name: "B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS Y CUOTAS DE FONDOS DE INVERSIÓN", rows: "Vista de campos relevantes · desde 2016-11", file: "", files: ["outputs/seguros/acciones_relevantes/manifest.json"] },
              { id: "seguros_fondos_mutuos", name: "B.3 CUOTAS DE FONDOS MUTUOS", rows: "Mensual · desde 2016-11", file: "", files: ["outputs/seguros/fondos_mutuos/manifest.json"] },
              { id: "seguros_bienes_raices", name: "B.4 BIENES RAICES", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/bienes_raices/manifest.json"] },
              { id: "seguros_bienes_raices_relevantes", name: "B.4 BIENES RAICES", rows: "Vista de campos relevantes · desde 2024-12", file: "", files: ["outputs/seguros/bienes_raices_relevantes/manifest.json"] },
              { id: "seguros_extranjeros", name: "B.5 INVERSIONES EN EL EXTRANJERO", rows: "Mensual · desde 2016-11", file: "", files: ["outputs/seguros/extranjeros/manifest.json"] },
              { id: "seguros_extranjeros_relevantes", name: "B.5 INVERSIONES EN EL EXTRANJERO", rows: "Vista de campos relevantes · desde 2016-11", file: "", files: ["outputs/seguros/extranjeros_relevantes/manifest.json"] },
              { id: "seguros_otras_inversiones", name: "B.6 OTRAS INVERSIONES", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/otras_inversiones/manifest.json"] },
              { id: "seguros_control_inversiones", name: "B.8 INFORMACION DE CONTROL", rows: "Mensual · desde 2016-11", file: "", files: ["outputs/seguros/control_inversiones/manifest.json"] },
              { id: "seguros_tablas_descriptores", name: "B.9 TABLAS DE DESCRIPTORES", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/tablas_descriptores/manifest.json"] },
              { id: "seguros_tablas_desarrollo", name: "B.10 TABLAS DE DESARROLLO", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/tablas_desarrollo/manifest.json"] },
              { id: "seguros_flujos_activos_elegibles", name: "B.11 FLUJOS DE ACTIVOS ELEGIBLES", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/flujos_activos_elegibles/manifest.json"] }
            ]
          },
          {
            id: "cat_seguros_derivados_1835",
            type: "circular",
            label: "Circular 1835 · Derivados y pactos",
            badge: "Mensual validada",
            badgeType: "data",
            status: "active",
            sector: "seguros",
            chips: [
              { label: "Derivados por tipo y sector, último mes", query: "SELECT sector, tipo_registro, count(*) AS contratos, SUM(valor_razonable_m_clp) AS valor_razonable_m_clp FROM seguros_derivados WHERE periodo = (SELECT max(periodo) FROM seguros_derivados) GROUP BY sector, tipo_registro ORDER BY sector, contratos DESC;" },
              { label: "Principales contrapartes de derivados, último mes", query: "SELECT COALESCE(NULLIF(TRIM(nombre), ''), 'Sin nombre informado') AS contraparte, count(*) AS contratos, count(DISTINCT rut_aseguradora) AS aseguradoras FROM seguros_derivados WHERE periodo = (SELECT max(periodo) FROM seguros_derivados) GROUP BY 1 ORDER BY contratos DESC LIMIT 10;" },
              { label: "Pactos: contrapartes y tasa promedio, último mes", query: "SELECT COALESCE(NULLIF(TRIM(nombre), ''), 'Sin nombre informado') AS contraparte, count(*) AS pactos, AVG(tasa_pacto) AS tasa_pacto_promedio FROM seguros_pactos WHERE periodo = (SELECT max(periodo) FROM seguros_pactos) GROUP BY 1 ORDER BY pactos DESC LIMIT 10;" }
            ],
            tables: [
              { id: "seguros_derivados", name: "B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS", rows: "Mensual · desde 2016-11", file: "", files: ["outputs/seguros/derivados/manifest.json"] },
              { id: "seguros_derivados_relevantes", name: "B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS", rows: "Vista de campos relevantes · desde 2016-11", file: "", files: ["outputs/seguros/derivados_relevantes/manifest.json"] },
              { id: "seguros_pactos", name: "B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS", rows: "Mensual · desde 2016-11", file: "", files: ["outputs/seguros/pactos/manifest.json"] }
            ]
          },
          {
            id: "cat_seguros_registros_2024",
            type: "circular",
            label: "Circular 1835 · B.12–B.14",
            badge: "Desde 2024-12",
            badgeType: "data",
            status: "active",
            sector: "seguros",
            chips: [
              { label: "B.14 Garantías por posición y tipo (M$)", query: "SELECT periodo, sector, posicion_compania, tipo_garantia, SUM(valor_razonable_activo_en_garantia_m_clp) AS valor_m_clp FROM seguros_garantias_derivados GROUP BY periodo, sector, posicion_compania, tipo_garantia ORDER BY periodo DESC LIMIT 50;" },
              { label: "Registros tipo 6 por periodo y archivo", query: "SELECT periodo, tipo_archivo, sector, COUNT(*) AS registros, MIN(largo_registro) AS largo_minimo, MAX(largo_registro) AS largo_maximo FROM seguros_registros_tipo6 GROUP BY periodo, tipo_archivo, sector ORDER BY periodo DESC, tipo_archivo, sector LIMIT 66;" }
            ],
            tables: [
              { id: "seguros_prestamos", name: "B.12 PRÉSTAMOS", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/prestamos/manifest.json"] },
              { id: "seguros_prestamos_relevantes", name: "B.12 PRÉSTAMOS", rows: "Vista de campos relevantes · desde 2024-12", file: "", files: ["outputs/seguros/prestamos_relevantes/manifest.json"] },
              { id: "seguros_bienes_raices_arriendo_morosidad", name: "B.13 BIENES RAICES EN ARRIENDO Y MOROSIDAD DE MUTUOS HIPOTECARIOS ENDOSABLES Y CONTRATOS DE LEASING", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/bienes_raices_arriendo_morosidad/manifest.json"] },
              { id: "seguros_bienes_raices_arriendo_morosidad_relevantes", name: "B.13 BIENES RAICES EN ARRIENDO Y MOROSIDAD DE MUTUOS HIPOTECARIOS ENDOSABLES Y CONTRATOS DE LEASING", rows: "Vista de campos relevantes · desde 2024-12", file: "", files: ["outputs/seguros/bienes_raices_arriendo_morosidad_relevantes/manifest.json"] },
              { id: "seguros_garantias_derivados", name: "B.14 GARANTÍAS EN INSTRUMENTOS DERIVADOS", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/garantias_derivados/manifest.json"] },
              { id: "seguros_registros_tipo6", name: "Registros tipo 6 de B.11 y B.14", rows: "Mensual · desde 2024-12", file: "", files: ["outputs/seguros/registros_tipo6/manifest.json"] }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_administracion_fondos",
    type: "group",
    label: "FONDOS MUTUOS Y DE INVERSIÓN (CMF / LEY 20.712)",
    badges: [
      { type: "entities", text: "Fondos mutuos y de inversión", title: "Fondos regidos por la Ley Única de Fondos. Sus administradoras (AGF) son unidades jurídicas y contables distintas: están en «Instituciones y estados financieros»" },
      { type: "data", text: "Mensual y trimestral · 2001–2026", title: "Los fondos mutuos informan cartera mensual (2001–2026) y los de inversión trimestral (2012–2026): cada tabla declara su propio periodo" }
    ],
    status: "active",
    children: [
      {
        id: "sector_ffmm",
        type: "sector",
        label: "Fondos Mutuos (CMF)",
        sector: "ffmm",
        children: [
          {
            id: "cat_ffmm_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "Desde los reportes",
            badgeType: "entities",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Fondos que reportan en el último mes", query: "SELECT run_fondo, nombre_fondo, primer_periodo, meses_reportados FROM ffmm_lista_entidades WHERE reporta_ultimo_mes ORDER BY nombre_fondo;" },
              { label: "Fondos nuevos (primer reporte más reciente)", query: "SELECT run_fondo, nombre_fondo, primer_periodo FROM ffmm_lista_entidades ORDER BY primer_periodo DESC, nombre_fondo LIMIT 20;" },
              { label: "Fondos que dejaron de reportar", query: "SELECT run_fondo, nombre_fondo, primer_periodo, ultimo_periodo FROM ffmm_lista_entidades WHERE NOT reporta_ultimo_mes ORDER BY ultimo_periodo DESC LIMIT 20;" }
            ],
            tables: [
              { id: "ffmm_lista_entidades", name: "ffmm.lista_entidades", rows: "Una fila por fondo", file: "outputs/ffmm/maestro_fondos_mutuos.parquet" }
            ]
          },
          {
            id: "cat_ffmm_cartera_1333",
            type: "circular",
            label: "Circular 1333 · Cartera de inversiones",
            badge: "Mensual validada",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Cartera nacional por tipo de instrumento, último mes", query: "SELECT tipo_instrumento, count(*) AS posiciones, count(DISTINCT run_fondo) AS fondos, SUM(valorizacion_miles_mf) AS valorizacion_miles_mf FROM ffmm_cartera_nacional WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_nacional) GROUP BY tipo_instrumento ORDER BY valorizacion_miles_mf DESC LIMIT 15;" },
              { label: "Mayores emisores nacionales, último mes", query: "SELECT rut_emisor, count(DISTINCT run_fondo) AS fondos, SUM(valorizacion_miles_mf) AS valorizacion_miles_mf FROM ffmm_cartera_nacional WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_nacional) GROUP BY rut_emisor ORDER BY valorizacion_miles_mf DESC LIMIT 10;" },
              { label: "Instrumentos con compromiso o en garantía, último mes", query: "SELECT situacion_instrumento, count(*) AS posiciones, count(DISTINCT run_fondo) AS fondos FROM ffmm_cartera_nacional WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_nacional) GROUP BY situacion_instrumento ORDER BY situacion_instrumento;" },
              { label: "Cartera extranjera por país emisor, último mes", query: "SELECT pais_emisor, count(*) AS posiciones, count(DISTINCT run_fondo) AS fondos FROM ffmm_cartera_extranjera WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_extranjera) GROUP BY pais_emisor ORDER BY posiciones DESC LIMIT 15;" },
              { label: "Fondos con inversión extranjera por mes", query: "SELECT periodo, count(DISTINCT run_fondo) AS fondos, count(*) AS posiciones FROM ffmm_cartera_extranjera GROUP BY periodo ORDER BY periodo DESC LIMIT 24;" }
            ],
            tables: [
              { id: "ffmm_cartera_nacional", name: "ffmm.cartera_nacional", rows: "Mensual", file: "", files: ["outputs/ffmm/cartera_nacional/manifest.json"] },
              { id: "ffmm_cartera_extranjera", name: "ffmm.cartera_extranjera", rows: "Mensual", file: "", files: ["outputs/ffmm/cartera_extranjera/manifest.json"] }
            ]
          },
          {
            id: "cat_ffmm_derivados_1333",
            type: "circular",
            label: "Circular 1333 · Derivados",
            badge: "Mensual validada",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Forwards y futuros por activo objeto, último mes", query: "SELECT activo_objeto, posicion, count(*) AS contratos, SUM(monto_comprometido_miles_mf) AS monto_comprometido_miles_mf FROM ffmm_futuros WHERE periodo = (SELECT max(periodo) FROM ffmm_futuros) GROUP BY activo_objeto, posicion ORDER BY contratos DESC LIMIT 15;" },
              { label: "Contratos vigentes por mes", query: "SELECT periodo, count(*) AS contratos, count(DISTINCT run_fondo) AS fondos FROM ffmm_futuros GROUP BY periodo ORDER BY periodo DESC LIMIT 24;" },
              { label: "Opciones del último mes", query: "SELECT run_fondo, nombre_fondo, activo_objeto, nemotecnico, tipo_opcion, fecha_expiracion, numero_contratos, precio_ejercicio, inversion_primas_miles_mf FROM ffmm_opciones WHERE periodo = (SELECT max(periodo) FROM ffmm_opciones) ORDER BY run_fondo;" }
            ],
            tables: [
              { id: "ffmm_futuros", name: "ffmm.futuros_forwards", rows: "Mensual", file: "", files: ["outputs/ffmm/futuros_forwards/manifest.json"] },
              { id: "ffmm_opciones", name: "ffmm.opciones", rows: "Mensual", file: "", files: ["outputs/ffmm/opciones/manifest.json"] }
            ]
          },
          {
            id: "cat_ffmm_balance",
            type: "circular",
            label: "Balance anual IFRS · CMF",
            badge: "Anual validada",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Mayores fondos en pesos por activo neto, último cierre (MM$)", query: "SELECT run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS activo_neto_mm, round(valor_anterior_miles_mf / 1e3, 1) AS activo_neto_anterior_mm FROM ffmm_balance WHERE codigo_cuenta = 'ActivoNetoAtribuibleALosParticipes' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM ffmm_balance) ORDER BY valor_miles_mf DESC LIMIT 20;" },
              { label: "Activo neto de la industria en pesos, por cierre (MM$)", query: "SELECT periodo, count(DISTINCT run_fondo) AS fondos, round(sum(valor_miles_mf) / 1e3, 0) AS activo_neto_mm FROM ffmm_balance WHERE codigo_cuenta = 'ActivoNetoAtribuibleALosParticipes' AND moneda = 'CLP' GROUP BY periodo ORDER BY periodo;" },
              { label: "Fondos que informan en dólares, por cierre (miles de US$)", query: "SELECT periodo, count(DISTINCT run_fondo) AS fondos, round(sum(valor_miles_mf), 0) AS activo_neto_miles_usd FROM ffmm_balance WHERE codigo_cuenta = 'ActivoNetoAtribuibleALosParticipes' AND moneda = 'USD' GROUP BY periodo ORDER BY periodo;" },
              { label: "Balance completo del mayor fondo en pesos, último cierre", query: "SELECT periodo, nombre_fondo, orden, seccion, cuenta, valor_miles_mf, valor_anterior_miles_mf FROM ffmm_balance WHERE run_fondo = (SELECT run_fondo FROM ffmm_balance WHERE codigo_cuenta = 'ActivoNetoAtribuibleALosParticipes' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM ffmm_balance) ORDER BY valor_miles_mf DESC LIMIT 1) AND periodo = (SELECT max(periodo) FROM ffmm_balance) ORDER BY orden;" }
            ],
            tables: [
              { id: "ffmm_balance", name: "ffmm.balance", rows: "Anual", file: "", files: ["outputs/ffmm/ffmm_balance/manifest.json"] }
            ]
          },
          {
            id: "cat_ffmm_resultados",
            type: "circular",
            label: "Estado de Resultados anual IFRS · CMF",
            badge: "Anual validada",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Mayores utilidades del último ejercicio, fondos en pesos (MM$)", query: "SELECT run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS utilidad_mm FROM ffmm_resultados WHERE codigo_cuenta = 'UtilidadPerdidaDeLaOperacionDespuesDeImpuesto' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM ffmm_resultados) ORDER BY valor_miles_mf DESC LIMIT 20;" },
              { label: "Comisión de administración cobrada, por ejercicio (MM$, fondos en pesos)", query: "SELECT periodo, count(DISTINCT run_fondo) AS fondos, round(-sum(valor_miles_mf) / 1e3, 0) AS comisiones_mm FROM ffmm_resultados WHERE codigo_cuenta = 'ComisionDeAdministracion' AND moneda = 'CLP' GROUP BY periodo ORDER BY periodo;" },
              { label: "Fondos con pérdida en cada ejercicio", query: "SELECT periodo, count(*) AS fondos, count(*) FILTER (WHERE valor_miles_mf < 0) AS con_perdida, round(100.0 * count(*) FILTER (WHERE valor_miles_mf < 0) / count(*), 1) AS pct_con_perdida FROM ffmm_resultados WHERE codigo_cuenta = 'UtilidadPerdidaDeLaOperacionDespuesDeImpuesto' GROUP BY periodo ORDER BY periodo;" },
              { label: "Estado de resultados del mayor fondo en pesos, último ejercicio", query: "SELECT periodo, nombre_fondo, orden, seccion, cuenta, valor_miles_mf, valor_anterior_miles_mf FROM ffmm_resultados WHERE run_fondo = (SELECT run_fondo FROM ffmm_balance WHERE codigo_cuenta = 'ActivoNetoAtribuibleALosParticipes' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM ffmm_balance) ORDER BY valor_miles_mf DESC LIMIT 1) AND periodo = (SELECT max(periodo) FROM ffmm_resultados) ORDER BY orden;" }
            ],
            tables: [
              { id: "ffmm_resultados", name: "ffmm.resultados", rows: "Anual", file: "", files: ["outputs/ffmm/ffmm_resultados/manifest.json"] }
            ]
          }
        ]
      },
      {
        id: "sector_fi",
        type: "sector",
        label: "Fondos de Inversión (CMF)",
        sector: "fi",
        children: [
          {
            id: "cat_fi_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "Registro CMF",
            badgeType: "entities",
            status: "active",
            sector: "fi",
            chips: [
              { label: "Fondos que reportan cartera en el último trimestre", query: "SELECT run_fondo, nombre_fondo, administradora, moneda_funcional, trimestres_con_cartera FROM fi_lista_entidades WHERE reporta_ultimo_periodo ORDER BY administradora, nombre_fondo;" },
              { label: "Fondos por administradora (vigentes)", query: "SELECT administradora, count(*) AS fondos FROM fi_lista_entidades WHERE estado_vigencia = 'Vigente' GROUP BY administradora ORDER BY fondos DESC LIMIT 20;" },
              { label: "Fondos por moneda funcional", query: "SELECT moneda_funcional, count(*) AS fondos FROM fi_lista_entidades WHERE reporta_ultimo_periodo GROUP BY moneda_funcional ORDER BY fondos DESC;" }
            ],
            tables: [
              { id: "fi_lista_entidades", name: "fi.lista_entidades", rows: "Una fila por fondo", file: "outputs/fi/maestro_fondos_inversion.parquet" }
            ]
          },
          {
            id: "cat_fi_cartera",
            type: "circular",
            label: "Cartera de Inversiones · Informes IFRS",
            badge: "Trimestral desde 2020-03",
            badgeType: "data",
            status: "active",
            sector: "fi",
            chips: [
              { label: "Cartera nacional por tipo de instrumento, último trimestre", query: "SELECT tipo_instrumento, count(*) AS posiciones, count(DISTINCT run_fondo) AS fondos, SUM(valorizacion_miles_mf) AS valorizacion_miles_mf FROM fi_cartera_nacional WHERE periodo = (SELECT max(periodo) FROM fi_cartera_nacional) GROUP BY tipo_instrumento ORDER BY posiciones DESC;" },
              { label: "Mayores emisores nacionales, último trimestre", query: "SELECT rut_emisor, count(DISTINCT run_fondo) AS fondos, count(*) AS posiciones FROM fi_cartera_nacional WHERE periodo = (SELECT max(periodo) FROM fi_cartera_nacional) GROUP BY rut_emisor ORDER BY fondos DESC LIMIT 20;" },
              { label: "Cartera extranjera por país emisor, último trimestre", query: "SELECT pais_emisor, count(*) AS posiciones, count(DISTINCT run_fondo) AS fondos FROM fi_cartera_extranjera WHERE periodo = (SELECT max(periodo) FROM fi_cartera_extranjera) GROUP BY pais_emisor ORDER BY posiciones DESC;" },
              { label: "Filiales y coligadas (método de la participación)", query: "SELECT periodo, count(DISTINCT run_fondo) AS fondos, count(*) AS inversiones FROM fi_metodo_participacion GROUP BY periodo ORDER BY periodo DESC LIMIT 12;" }
            ],
            tables: [
              { id: "fi_cartera_nacional", name: "fi.cartera_nacional", rows: "Trimestral", file: "", files: ["outputs/fi/cartera_nacional/manifest.json"] },
              { id: "fi_cartera_extranjera", name: "fi.cartera_extranjera", rows: "Trimestral", file: "", files: ["outputs/fi/cartera_extranjera/manifest.json"] },
              { id: "fi_metodo_participacion", name: "fi.metodo_participacion", rows: "Trimestral", file: "", files: ["outputs/fi/metodo_participacion/manifest.json"] },
              { id: "fi_bienes_raices", name: "fi.bienes_raices", rows: "Sin datos", file: "", files: ["outputs/fi/bienes_raices/manifest.json"], nota: "Ningún fondo ha informado cartera de bienes raíces a la CMF (2020-03 → 2026-06); la tabla se completa sola cuando la fuente publique datos." }
            ]
          },
          {
            id: "cat_fi_derivados_pactos",
            type: "circular",
            label: "Derivados y Pactos · Informes IFRS",
            badge: "Derivados desde 2020-03 · pactos desde 2012-03",
            badgeType: "data",
            status: "active",
            sector: "fi",
            chips: [
              { label: "Forwards y futuros por activo objeto, último trimestre", query: "SELECT activo_objeto, posicion, count(*) AS contratos, count(DISTINCT run_fondo) AS fondos FROM fi_futuros WHERE periodo = (SELECT max(periodo) FROM fi_futuros) GROUP BY activo_objeto, posicion ORDER BY contratos DESC LIMIT 20;" },
              { label: "Contrapartes de derivados, último trimestre", query: "SELECT contraparte, count(*) AS contratos FROM fi_futuros WHERE periodo = (SELECT max(periodo) FROM fi_futuros) GROUP BY contraparte ORDER BY contratos DESC LIMIT 15;" },
              { label: "Opciones por trimestre", query: "SELECT periodo, count(*) AS contratos, count(DISTINCT run_fondo) AS fondos FROM fi_opciones GROUP BY periodo ORDER BY periodo DESC LIMIT 12;" },
              { label: "Pactos por tipo de operación y contraparte, último trimestre", query: "SELECT tipo_operacion, contraparte, count(*) AS pactos, AVG(tasa_pacto_pct) AS tasa_prom_pct FROM fi_pactos WHERE periodo = (SELECT max(periodo) FROM fi_pactos) GROUP BY tipo_operacion, contraparte ORDER BY pactos DESC LIMIT 20;" }
            ],
            tables: [
              { id: "fi_futuros", name: "fi.futuros_forwards", rows: "Trimestral", file: "", files: ["outputs/fi/futuros_forwards/manifest.json"] },
              { id: "fi_opciones", name: "fi.opciones", rows: "Trimestral", file: "", files: ["outputs/fi/opciones/manifest.json"] },
              { id: "fi_pactos", name: "fi.pactos", rows: "Trimestral", file: "", files: ["outputs/fi/pactos/manifest.json"] }
            ]
          },
          // BEGIN AUTO FI EEFF NAVIGATION
{
  id: "cat_fi_balance",
  type: "circular",
  label: "Balance trimestral IFRS · CMF",
  badge: "16 cierres validados",
  badgeType: "data",
  status: "active",
  sector: "fi",
  chips: [
    {
      label: "Mayores patrimonios en pesos, último cierre (MM$)",
      query: "SELECT run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS patrimonio_mm FROM fi_balance WHERE contexto = 'PeriodoActual' AND codigo_cuenta = 'TotalPatrimonioNeto' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM fi_balance) ORDER BY valor_miles_mf DESC LIMIT 20;"
    },
    {
      label: "Balance actual del mayor fondo en pesos, último cierre",
      query: "SELECT periodo, nombre_fondo, orden, seccion, cuenta, valor_miles_mf FROM fi_balance WHERE contexto = 'PeriodoActual' AND periodo = (SELECT max(periodo) FROM fi_balance) AND run_fondo = (SELECT run_fondo FROM fi_balance WHERE contexto = 'PeriodoActual' AND moneda = 'CLP' AND codigo_cuenta = 'TotalPatrimonioNeto' AND periodo = (SELECT max(periodo) FROM fi_balance) ORDER BY valor_miles_mf DESC LIMIT 1) ORDER BY orden;"
    },
    {
      label: "Cobertura de balances por cierre y contexto",
      query: "SELECT periodo, contexto, moneda, count(DISTINCT run_fondo) AS fondos FROM fi_balance GROUP BY periodo, contexto, moneda ORDER BY periodo DESC, contexto, moneda;"
    }
  ],
  tables: [
    {
      id: "fi_balance",
      name: "fi.balance",
      rows: "Trimestral · contextos separados",
      file: "",
      files: [
        "outputs/fi/fi_balance/manifest.json"
      ]
    }
  ]
},
{
  id: "cat_fi_resultados",
  type: "circular",
  label: "Estado de Resultados trimestral IFRS · CMF",
  badge: "16 cierres validados",
  badgeType: "data",
  status: "active",
  sector: "fi",
  chips: [
    {
      label: "Mayores resultados acumulados en pesos, último cierre (MM$)",
      query: "SELECT run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS resultado_mm FROM fi_resultados WHERE contexto = 'PeriodoActual' AND codigo_cuenta = 'ResultadoDelEjercicio' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM fi_resultados) ORDER BY valor_miles_mf DESC LIMIT 20;"
    },
    {
      label: "Resultado SOLO del trimestre en pesos, según XML (MM$)",
      query: "SELECT periodo, run_fondo, nombre_fondo, round(valor_miles_mf / 1e3, 1) AS resultado_trimestre_mm, cotejo_ficha FROM fi_resultados WHERE contexto = 'TrimestreActual' AND codigo_cuenta = 'ResultadoDelEjercicio' AND moneda = 'CLP' AND periodo = (SELECT max(periodo) FROM fi_resultados) ORDER BY valor_miles_mf DESC LIMIT 20;"
    },
    {
      label: "Comisiones acumuladas por cierre y moneda, sin mezclar contextos",
      query: "SELECT periodo, moneda, count(DISTINCT run_fondo) AS fondos, -sum(valor_miles_mf) AS comision_miles_moneda FROM fi_resultados WHERE contexto = 'PeriodoActual' AND codigo_cuenta = 'ComisionDeAdministracion' GROUP BY periodo, moneda ORDER BY periodo DESC, moneda;"
    }
  ],
  tables: [
    {
      id: "fi_resultados",
      name: "fi.resultados",
      rows: "Trimestral · contextos separados",
      file: "",
      files: [
        "outputs/fi/fi_resultados/manifest.json"
      ]
    }
  ]
},
  // END AUTO FI EEFF NAVIGATION
        ]
      }
    ]
  },
  {
    id: "group_agf",
    type: "group",
    label: "ADMINISTRADORAS GENERALES DE FONDOS (CMF)",
    badges: [
      { type: "entities", text: "Administran los fondos", title: "Sociedades que administran los fondos mutuos y de inversión: unidades jurídicas y contables distintas de los fondos" },
      { type: "data", text: "Trimestral · 2010–2026", title: "Balance y estado de resultados de cada administradora desde el TXT trimestral de la CMF (estados financieros IFRS)" }
    ],
    status: "active",
    children: [
      {
        id: "sector_agf",
        type: "sector",
        label: "Administradoras Generales de Fondos (CMF)",
        sector: "agf",
        children: [
          {
            id: "cat_agf_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "68 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "agf",
            chips: [
              { label: "Catálogo de AGF (Vigentes vs Canceladas)", query: "SELECT rut_completo, razon_social, estado_vigencia, grupo_controlador, fondos_inversion_administrados FROM agf_lista_entidades ORDER BY estado_vigencia, razon_social;" },
              { label: "Ranking de AGF por Fondos de Inversión Administrados", query: "SELECT razon_social, grupo_controlador, fondos_inversion_administrados, cmf_url FROM agf_lista_entidades WHERE fondos_inversion_administrados > 0 ORDER BY fondos_inversion_administrados DESC LIMIT 15;" },
              { label: "AGF por Grupo Financiero Controlador", query: "SELECT grupo_controlador, count(*) as cantidad_agf, sum(fondos_inversion_administrados) as total_fondos FROM agf_lista_entidades WHERE estado_vigencia = 'Vigente' GROUP BY grupo_controlador ORDER BY total_fondos DESC;" }
            ],
            tables: [
              { id: "agf_lista_entidades", name: "agf.lista_entidades", rows: "Una fila por administradora", file: "outputs/agf/agf_maestro.parquet" }
            ]
          },
          {
            id: "cat_agf_balance",
            type: "circular",
            label: "Balance IFRS · CMF (2010-06–2026-06)",
            badge: "65 trimestres",
            badgeType: "data",
            status: "active",
            sector: "agf",
            chips: [
              { label: "Activos, pasivos y patrimonio por AGF, último trimestre (MM$)", query: "SELECT periodo, razon_social, tipo_balance, moneda, round(max(valor) FILTER (WHERE cuenta = 'Total de activos') / 1e6, 1) AS activos_mm, round(max(valor) FILTER (WHERE cuenta = 'Total de pasivos') / 1e6, 1) AS pasivos_mm, round(max(valor) FILTER (WHERE cuenta = 'Patrimonio total') / 1e6, 1) AS patrimonio_mm FROM agf_balance WHERE periodo = (SELECT max(periodo) FROM agf_balance) AND repeticion = 1 GROUP BY ALL ORDER BY activos_mm DESC NULLS LAST;" },
              { label: "Evolución del sector: activos totales por trimestre (MM$, CLP)", query: "SELECT periodo, count(DISTINCT rut) AS entidades, round(sum(valor) / 1e6, 1) AS activos_mm_clp FROM agf_balance WHERE cuenta = 'Total de activos' AND moneda = 'CLP' AND repeticion = 1 GROUP BY periodo ORDER BY periodo;" },
              { label: "Balance completo de Banchile AGF, último trimestre", query: "SELECT periodo, tipo_balance, estado_financiero, orden, cuenta, valor FROM agf_balance WHERE rut = '96767630' AND periodo = (SELECT max(periodo) FROM agf_balance WHERE rut = '96767630') ORDER BY tipo_balance, estado_financiero, orden;" }
            ],
            tables: [
              { id: "agf_balance", name: "agf.balance", rows: "Serie IFRS", file: "", files: ["outputs/agf/agf_balance/manifest.json"] }
            ]
          },
          {
            id: "cat_agf_resultados",
            type: "circular",
            label: "Estado de Resultados IFRS · CMF (2010-06–2026-06)",
            badge: "65 trimestres",
            badgeType: "data",
            status: "active",
            sector: "agf",
            chips: [
              { label: "Ingresos y utilidad por AGF, ejercicio 2025 (MM$)", query: "SELECT razon_social, tipo_balance, moneda, round(max(valor) FILTER (WHERE cuenta = 'Ingresos de actividades ordinarias') / 1e6, 1) AS ingresos_mm, round(max(valor) FILTER (WHERE cuenta = 'Ganancia (pérdida)') / 1e6, 1) AS ganancia_mm FROM agf_resultados WHERE periodo = '2025-12' AND estado_financiero IN ('ERFG', 'ERNG') AND repeticion = 1 GROUP BY ALL ORDER BY ganancia_mm DESC NULLS LAST;" },
              { label: "Por qué hay que filtrar: «Ganancia (pérdida)» aparece varias veces", query: "SELECT estado_financiero, repeticion, count(*) AS filas, count(DISTINCT rut) AS entidades FROM agf_resultados WHERE periodo = '2025-12' AND cuenta = 'Ganancia (pérdida)' GROUP BY ALL ORDER BY estado_financiero, repeticion;" },
              { label: "Utilidad del sector por año (cierres de diciembre, MM$, CLP)", query: "SELECT left(periodo, 4) AS anio, count(DISTINCT rut) AS entidades, round(sum(valor) / 1e6, 1) AS ganancia_mm_clp FROM agf_resultados WHERE periodo LIKE '%-12' AND cuenta = 'Ganancia (pérdida)' AND estado_financiero IN ('ERFG', 'ERNG') AND repeticion = 1 AND moneda = 'CLP' GROUP BY 1 ORDER BY 1;" },
              { label: "Estado de resultados completo de Banchile AGF, ejercicio 2025", query: "SELECT tipo_balance, estado_financiero, orden, cuenta, valor FROM agf_resultados WHERE rut = '96767630' AND periodo = '2025-12' ORDER BY tipo_balance, estado_financiero, orden;" }
            ],
            tables: [
              { id: "agf_resultados", name: "agf.resultados", rows: "Serie IFRS", file: "", files: ["outputs/agf/agf_resultados/manifest.json"] }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_pensiones",
    type: "group",
    label: "FONDOS DE PENSIONES (SPENSIONES)",
    badges: [
      { type: "entities", text: "7 administradoras", title: "Lista local de AFP; verificar identidad y vigencia contra la Superintendencia de Pensiones" },
      { type: "data", text: "Sólo registro de entidades", title: "Esta edición no publica carteras de fondos de pensiones: de las AFP sólo está el registro de administradoras" }
    ],
    status: "active",
    children: [
      {
        id: "sector_afp_corporativo",
        type: "sector",
        label: "Administradoras de Fondos de Pensiones",
        sector: "afp_corporativo",
        children: [
          {
            id: "cat_afp_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "7 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "afp_corporativo",
            chips: [
              { label: "Identificación de administradoras", query: "SELECT rut_administradora, nombre_administradora, nombre_fantasia FROM afp_lista_entidades ORDER BY nombre_fantasia;" }
            ],
            tables: [
              { id: "afp_lista_entidades", name: "afp.lista_entidades", rows: "Una fila por administradora", file: "outputs/pensiones/afp_maestro_administradoras.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_bancos",
    type: "group",
    label: "BANCA Y ESTADOS FINANCIEROS CMF",
    badges: [
      { type: "entities", text: "40 instituciones", title: "Catálogo histórico de instituciones bancarias; requiere validación independiente" },
      { type: "data", text: "Mensual · 2022–2026", title: "Balance (B1/B2) y resultados (R1) mensuales de la CMF. Cada periodo se incorpora solo si el gate de validación CMF pasa" }
    ],
    status: "por_auditar",
    open: true,
    children: [
      {
        id: "sector_bancos_comercial",
        type: "sector",
        label: "Instituciones y reportes bancarios",
        sector: "bancos",
        open: true,
        children: [
          {
            id: "cat_bancos_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "40 códigos · Falta validar",
            badgeType: "entities",
            status: "por_auditar",
            sector: "bancos",
            open: false,
            chips: [
              { label: "Bancos Comerciales Activos", query: "SELECT codigo_institucion, rut, nombre_fantasia, tipo_licencia, estado FROM bancos_lista_entidades WHERE estado = 'Activo' ORDER BY codigo_institucion;" },
              { label: "Historial de Bancos Fusionados / Cerrados", query: "SELECT codigo_institucion, nombre_fantasia, razon_social, estado FROM bancos_lista_entidades WHERE estado != 'Activo' ORDER BY estado, nombre_fantasia;" }
            ],
            tables: [
              { id: "bancos_lista_entidades", name: "bancos.lista_entidades", rows: "Una fila por institución y agregado", file: "outputs/bancos/bancos_maestro.parquet" }
            ]
          },
          {
            id: "cat_bancos_balance",
            type: "circular",
            label: "Estados de Situación Financiera CMF · B1/B2",
            badge: "Publicación mensual validada",
            badgeType: "data",
            status: "active",
            sector: "bancos",
            open: false,
            chips: [
              { label: "Muestra de líneas de balance B1/B2 (sin sumar importes)", query: "SELECT periodo, codigo_institucion, nombre_institucion_fuente, familia_archivo_fuente, modelo_cmf, codigo_cuenta, glosa_cuenta, rubro, linea, item, numero_fila_fuente, importes_fuente_raw FROM bancos_balance ORDER BY periodo DESC, codigo_institucion, familia_archivo_fuente, numero_fila_fuente LIMIT 100;" },
              { label: "Cobertura de balance por periodo y modelo", query: "SELECT periodo, familia_archivo_fuente, modelo_cmf, count(*) AS filas, count(DISTINCT codigo_institucion) AS instituciones FROM bancos_balance GROUP BY periodo, familia_archivo_fuente, modelo_cmf ORDER BY periodo DESC, familia_archivo_fuente;" }
            ],
            tables: [
              { id: "bancos_balance", name: "bancos.balance", rows: "B1/B2 · importes fuente", file: "", files: ["outputs/bancos/cmf_b1_b2_r1/manifest.json"] }
            ]
          },
          {
            id: "cat_bancos_resultados",
            type: "circular",
            label: "Estado de Resultados CMF · R1",
            badge: "Publicación mensual validada",
            badgeType: "data",
            status: "active",
            sector: "bancos",
            open: false,
            chips: [
              { label: "Muestra de líneas de resultados R1 (sin sumar importes)", query: "SELECT periodo, codigo_institucion, nombre_institucion_fuente, familia_archivo_fuente, modelo_cmf, codigo_cuenta, glosa_cuenta, rubro, linea, item, numero_fila_fuente, importes_fuente_raw FROM bancos_resultados ORDER BY periodo DESC, codigo_institucion, numero_fila_fuente LIMIT 100;" },
              { label: "Cobertura de resultados por periodo", query: "SELECT periodo, modelo_cmf, count(*) AS filas, count(DISTINCT codigo_institucion) AS instituciones FROM bancos_resultados GROUP BY periodo, modelo_cmf ORDER BY periodo DESC;" }
            ],
            tables: [
              { id: "bancos_resultados", name: "bancos.resultados", rows: "R1 · importes fuente", file: "", files: ["outputs/bancos/cmf_b1_b2_r1/manifest.json"] }
            ]
          }
        ]
      }
    ]
  },
  // <macro:inicio>
  {
    id: "group_macro",
    type: "group",
    label: "MACROECONOMÍA Y TASAS (BCCh)",
    badges: [
      { type: "data", text: "24 tablas", title: "23 tablas por indicador económico, en la frecuencia en que lo publica el Banco Central (diaria, mensual o trimestral), más el catálogo de series; agrupadas en tasas y curvas, tipo de cambio, actividad y precios y expectativas" },
      { type: "data", text: "Diaria, mensual y trimestral · 2014–2026", title: "Cada serie está en la frecuencia en que la publica el Banco Central. Cobertura: desde 2014 hasta la última publicación" }
    ],
    status: "active",
    children: [
      {
        id: "sector_macro_general",
        type: "sector",
        label: "Banco Central de Chile · Base de Datos Estadísticos",
        sector: "macro",
        children: [
          {
            id: "cat_macro_tasas_curvas",
            type: "circular",
            label: "Tasas y curvas",
            badge: "6 tablas",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "TPM y tasa interbancaria: últimos 60 días", query: "SELECT fecha, tpm_pct, tib_promedio_pct, round(tib_promedio_pct - tpm_pct, 3) AS diferencia_tib_tpm FROM macro_tasas_corto_plazo ORDER BY fecha DESC LIMIT 60;" },
              { label: "Curva de bonos en pesos: promedio mensual, últimos 24 meses", query: "SELECT periodo, round(avg(rendimiento_bono_pesos_2_anos_pct), 3) AS bono_2_anos_pct, round(avg(rendimiento_bono_pesos_5_anos_pct), 3) AS bono_5_anos_pct, round(avg(rendimiento_bono_pesos_10_anos_pct), 3) AS bono_10_anos_pct FROM macro_curva_bonos_pesos GROUP BY periodo ORDER BY periodo DESC LIMIT 24;" },
              { label: "Curva de bonos en UF: último dato disponible por plazo", query: "SELECT fecha, rendimiento_bono_uf_1_ano_pct, rendimiento_bono_uf_2_anos_pct, rendimiento_bono_uf_5_anos_pct, rendimiento_bono_uf_10_anos_pct, rendimiento_bono_uf_20_anos_pct, rendimiento_bono_uf_30_anos_pct FROM macro_curva_bonos_uf ORDER BY fecha DESC LIMIT 20;" },
              { label: "Inflación implícita a 5 y 10 años: promedio mensual", query: "SELECT periodo, round(avg(inflacion_implicita_5_anos_pct), 3) AS implicita_5_anos_pct, round(avg(inflacion_implicita_10_anos_pct), 3) AS implicita_10_anos_pct FROM macro_inflacion_implicita GROUP BY periodo ORDER BY periodo DESC LIMIT 24;" },
              { label: "Swaps de cámara en pesos: curva 90 días a 2 años", query: "SELECT fecha, swap_camara_pesos_90_dias_pct, swap_camara_pesos_180_dias_pct, swap_camara_pesos_360_dias_pct, swap_camara_pesos_2_anos_pct, swap_camara_uf_1_ano_pct FROM macro_swaps_camara ORDER BY fecha DESC LIMIT 30;" },
              { label: "Tasa de la Fed frente a la TPM de Chile: promedio mensual", query: "SELECT f.periodo, round(avg(f.tasa_fed_funds_pct), 2) AS fed_funds_pct, round(avg(t.tpm_pct), 2) AS tpm_chile_pct FROM macro_tasa_referencia_fed f JOIN macro_tasas_corto_plazo t USING (periodo) GROUP BY f.periodo ORDER BY f.periodo DESC LIMIT 24;" }
            ],
            tables: [
              { id: "macro_tasas_corto_plazo", name: "macro.tasas_corto_plazo", rows: "Una fila por día", file: "outputs/macro/macro_tasas_corto_plazo.parquet" },
              { id: "macro_swaps_camara", name: "macro.swaps_camara", rows: "Una fila por día", file: "outputs/macro/macro_swaps_camara.parquet" },
              { id: "macro_curva_bonos_pesos", name: "macro.curva_bonos_pesos", rows: "Una fila por día", file: "outputs/macro/macro_curva_bonos_pesos.parquet" },
              { id: "macro_curva_bonos_uf", name: "macro.curva_bonos_uf", rows: "Una fila por día", file: "outputs/macro/macro_curva_bonos_uf.parquet" },
              { id: "macro_inflacion_implicita", name: "macro.inflacion_implicita", rows: "Una fila por día", file: "outputs/macro/macro_inflacion_implicita.parquet" },
              { id: "macro_tasa_referencia_fed", name: "macro.tasa_referencia_fed", rows: "Una fila por día", file: "outputs/macro/macro_tasa_referencia_fed.parquet" }
            ]
          },
          {
            id: "cat_macro_tipo_cambio_uf_utm",
            type: "circular",
            label: "Tipo de cambio, UF y UTM",
            badge: "6 tablas",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "Dólar observado: últimos 30 días hábiles", query: "SELECT fecha, dolar_observado_clp_por_usd FROM macro_dolar_observado ORDER BY fecha DESC LIMIT 30;" },
              { label: "Dólar observado por mes: promedio, mínimo, máximo y cierre", query: "SELECT periodo, round(avg(dolar_observado_clp_por_usd), 2) AS promedio_clp, min(dolar_observado_clp_por_usd) AS minimo_clp, max(dolar_observado_clp_por_usd) AS maximo_clp, arg_max(dolar_observado_clp_por_usd, fecha) AS cierre_clp FROM macro_dolar_observado GROUP BY periodo ORDER BY periodo DESC LIMIT 24;" },
              { label: "Dólar y euro observados en la misma fecha", query: "SELECT d.fecha, d.dolar_observado_clp_por_usd, e.euro_observado_clp_por_eur, round(e.euro_observado_clp_por_eur / d.dolar_observado_clp_por_usd, 4) AS euro_por_dolar FROM macro_dolar_observado d JOIN macro_euro_observado e USING (fecha) ORDER BY d.fecha DESC LIMIT 30;" },
              { label: "Tipo de cambio real: TCR general y TCR-5", query: "SELECT periodo, tipo_cambio_real_general_indice, tipo_cambio_real_5_monedas_indice FROM macro_tipo_cambio_real ORDER BY periodo DESC LIMIT 24;" },
              { label: "UF: valor de cierre de cada mes y variación mensual", query: "SELECT periodo, uf_cierre_clp, round((uf_cierre_clp / lag(uf_cierre_clp) OVER (ORDER BY periodo) - 1) * 100, 2) AS uf_var_mensual_pct FROM (SELECT periodo, arg_max(uf_valor_clp, fecha) AS uf_cierre_clp FROM macro_uf GROUP BY periodo) ORDER BY periodo DESC LIMIT 24;" },
              { label: "UF y UTM vigentes: último valor de cada mes", query: "SELECT u.periodo, arg_max(u.uf_valor_clp, u.fecha) AS uf_cierre_clp, max(t.utm_valor_clp) AS utm_valor_clp FROM macro_uf u LEFT JOIN macro_utm t USING (periodo) GROUP BY u.periodo ORDER BY u.periodo DESC LIMIT 24;" }
            ],
            tables: [
              { id: "macro_dolar_observado", name: "macro.dolar_observado", rows: "Una fila por día", file: "outputs/macro/macro_dolar_observado.parquet" },
              { id: "macro_euro_observado", name: "macro.euro_observado", rows: "Una fila por día", file: "outputs/macro/macro_euro_observado.parquet" },
              { id: "macro_tipo_cambio_multilateral", name: "macro.tipo_cambio_multilateral", rows: "Una fila por día", file: "outputs/macro/macro_tipo_cambio_multilateral.parquet" },
              { id: "macro_tipo_cambio_real", name: "macro.tipo_cambio_real", rows: "Una fila por mes", file: "outputs/macro/macro_tipo_cambio_real.parquet" },
              { id: "macro_uf", name: "macro.uf", rows: "Una fila por día", file: "outputs/macro/macro_uf.parquet" },
              { id: "macro_utm", name: "macro.utm", rows: "Una fila por mes", file: "outputs/macro/macro_utm.parquet" }
            ]
          },
          {
            id: "cat_macro_actividad_precios",
            type: "circular",
            label: "Actividad y precios",
            badge: "8 tablas",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "Inflación IPC: índice y variaciones mensual y anual", query: "SELECT periodo, ipc_indice, ipc_var_mensual_pct, ipc_var_anual_pct FROM macro_inflacion_ipc ORDER BY periodo DESC LIMIT 24;" },
              { label: "Imacec total y no minero con variación anual", query: "SELECT periodo, imacec_empalmado_indice, round((imacec_empalmado_indice / lag(imacec_empalmado_indice, 12) OVER (ORDER BY periodo) - 1) * 100, 2) AS imacec_var_anual_pct, imacec_no_minero_indice, imacec_minero_indice FROM macro_imacec ORDER BY periodo DESC LIMIT 24;" },
              { label: "Imacec por sector: comercio y servicios", query: "SELECT periodo, imacec_comercio_indice, imacec_servicios_indice, imacec_no_minero_indice FROM macro_imacec ORDER BY periodo DESC LIMIT 24;" },
              { label: "PIB trimestral con variación respecto al mismo trimestre del año anterior", query: "SELECT periodo, pib_encadenado_miles_mm_clp, round((pib_encadenado_miles_mm_clp / lag(pib_encadenado_miles_mm_clp, 4) OVER (ORDER BY periodo) - 1) * 100, 2) AS pib_var_anual_pct FROM macro_pib_trimestral ORDER BY periodo DESC LIMIT 20;" },
              { label: "Desocupación, ocupados y fuerza de trabajo: últimos 24 meses", query: "SELECT periodo, desocupacion_pct, ocupados_miles_personas, asalariados_miles_personas, fuerza_trabajo_miles_personas FROM macro_mercado_laboral ORDER BY periodo DESC LIMIT 24;" },
              { label: "Participación de asalariados sobre ocupados", query: "SELECT periodo, round(asalariados_miles_personas / ocupados_miles_personas * 100, 2) AS asalariados_sobre_ocupados_pct, desocupacion_pct FROM macro_mercado_laboral ORDER BY periodo DESC LIMIT 24;" },
              { label: "Cobre: precio diario BML, últimos 30 días", query: "SELECT fecha, cobre_refinado_usd_por_libra FROM macro_cobre WHERE cobre_refinado_usd_por_libra IS NOT NULL ORDER BY fecha DESC LIMIT 30;" },
              { label: "Cobre: promedio mensual y referencia BCCh con variación anual", query: "SELECT periodo, promedio_diario_usd_lb, referencia_mensual_usd_lb, round((referencia_mensual_usd_lb / lag(referencia_mensual_usd_lb, 12) OVER (ORDER BY periodo) - 1) * 100, 2) AS referencia_var_anual_pct FROM (SELECT periodo, round(avg(cobre_refinado_usd_por_libra), 4) AS promedio_diario_usd_lb, max(cobre_referencial_mensual_usd_por_libra) AS referencia_mensual_usd_lb FROM macro_cobre GROUP BY periodo) ORDER BY periodo DESC LIMIT 24;" },
              { label: "Oro y plata: últimos 30 días", query: "SELECT fecha, oro_usd_por_onza_troy, plata_usd_por_onza_troy, round(oro_usd_por_onza_troy / plata_usd_por_onza_troy, 2) AS relacion_oro_plata FROM macro_metales_preciosos ORDER BY fecha DESC LIMIT 30;" },
              { label: "Reservas internacionales: últimos 24 meses", query: "SELECT periodo, reservas_internacionales_millones_usd FROM macro_reservas_internacionales ORDER BY periodo DESC LIMIT 24;" },
              { label: "Deuda pública sobre PIB: serie trimestral", query: "SELECT periodo, deuda_bruta_gobierno_central_pct_pib FROM macro_deuda_publica_pct_pib ORDER BY periodo DESC LIMIT 20;" }
            ],
            tables: [
              { id: "macro_inflacion_ipc", name: "macro.inflacion_ipc", rows: "Una fila por mes", file: "outputs/macro/macro_inflacion_ipc.parquet" },
              { id: "macro_imacec", name: "macro.imacec", rows: "Una fila por mes", file: "outputs/macro/macro_imacec.parquet" },
              { id: "macro_pib_trimestral", name: "macro.pib_trimestral", rows: "Una fila por trimestre", file: "outputs/macro/macro_pib_trimestral.parquet" },
              { id: "macro_mercado_laboral", name: "macro.mercado_laboral", rows: "Una fila por mes", file: "outputs/macro/macro_mercado_laboral.parquet" },
              { id: "macro_cobre", name: "macro.cobre", rows: "Una fila por día", file: "outputs/macro/macro_cobre.parquet" },
              { id: "macro_metales_preciosos", name: "macro.metales_preciosos", rows: "Una fila por día", file: "outputs/macro/macro_metales_preciosos.parquet" },
              { id: "macro_reservas_internacionales", name: "macro.reservas_internacionales", rows: "Una fila por mes", file: "outputs/macro/macro_reservas_internacionales.parquet" },
              { id: "macro_deuda_publica_pct_pib", name: "macro.deuda_publica_pct_pib", rows: "Una fila por trimestre", file: "outputs/macro/macro_deuda_publica_pct_pib.parquet" }
            ]
          },
          {
            id: "cat_macro_expectativas",
            type: "circular",
            label: "Expectativas",
            badge: "3 tablas",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "Inflación anual efectiva frente a la esperada (EEE)", query: "SELECT i.periodo, i.ipc_var_anual_pct, e.expectativa_inflacion_ipc_11_meses_pct, e.expectativa_inflacion_ipc_23_meses_pct, round((e.expectativa_inflacion_ipc_11_meses_pct - 3.0) * 100, 0) AS desvio_11_meses_vs_meta_puntos_basicos FROM macro_inflacion_ipc i JOIN macro_expectativas_inflacion e USING (periodo) ORDER BY i.periodo DESC LIMIT 24;" },
              { label: "TPM efectiva frente a la esperada por la EEE", query: "SELECT e.periodo, round(avg(t.tpm_pct), 2) AS tpm_pct, max(e.expectativa_tpm_11_meses_pct) AS expectativa_tpm_11_meses_pct, max(e.expectativa_tpm_23_meses_pct) AS expectativa_tpm_23_meses_pct FROM macro_expectativas_tpm e JOIN macro_tasas_corto_plazo t USING (periodo) GROUP BY e.periodo ORDER BY e.periodo DESC LIMIT 24;" },
              { label: "Encuesta de Operadores Financieros: últimas 20 encuestas", query: "SELECT fecha, expectativa_inflacion_12_meses_pct, expectativa_tpm_12_meses_pct FROM macro_expectativas_operadores ORDER BY fecha DESC LIMIT 20;" }
            ],
            tables: [
              { id: "macro_expectativas_inflacion", name: "macro.expectativas_inflacion", rows: "Una fila por mes", file: "outputs/macro/macro_expectativas_inflacion.parquet" },
              { id: "macro_expectativas_tpm", name: "macro.expectativas_tpm", rows: "Una fila por mes", file: "outputs/macro/macro_expectativas_tpm.parquet" },
              { id: "macro_expectativas_operadores", name: "macro.expectativas_operadores", rows: "Una fila por día", file: "outputs/macro/macro_expectativas_operadores.parquet" }
            ]
          },
          {
            id: "cat_macro_series_catalogo",
            type: "circular",
            label: "Catálogo de series",
            badge: "51 series",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "Catálogo: series, frecuencia, unidad y última fecha", query: "SELECT grupo, nombre, frecuencia, unidad, primera_fecha, ultima_fecha, observaciones, estado FROM macro_series_catalogo ORDER BY grupo, nombre;" },
              { label: "Estado de la última consulta al BCCh por grupo", query: "SELECT grupo, count(*) AS series, sum(CASE WHEN estado = 'ok' THEN 1 ELSE 0 END) AS series_ok, max(ultima_fecha) AS dato_mas_reciente, max(ultima_consulta_utc) AS ultima_consulta_utc FROM macro_series_catalogo GROUP BY grupo ORDER BY grupo;" }
            ],
            tables: [
              { id: "macro_series_catalogo", name: "macro.series_catalogo", rows: "Una fila por serie", file: "outputs/macro/macro_series_catalogo.parquet" }
            ]
          }
        ]
      }
    ]
  },
  // <macro:fin>
  {
    id: "group_factoring_leasing",
    type: "group",
    label: "FACTORING & LEASING (CMF / NBFI)",
    badges: [
      { type: "entities", text: "32 entidades", title: "Lista de 32 entidades de factoring y leasing" },
      { type: "data", text: "Trimestral · 2009–2026", title: "Balance y resultados IFRS de la serie CMF: 70 cierres trimestrales, de 2009-03 a 2026-06" }
    ],
    status: "active",
    children: [
      {
        id: "sector_factoring_leasing",
        type: "sector",
        label: "Factoring y Leasing (CMF)",
        sector: "factoring_leasing",
        children: [
          {
            id: "cat_factoring_leasing_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "32 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "factoring_leasing",
            chips: [
              { label: "Lista por segmento y licencia (catálogo local)", query: "SELECT rut, razon_social, nombre_fantasia, segmento, tipo_licencia, grupo_controlador, vigente FROM factoring_leasing_lista_entidades ORDER BY vigente DESC, segmento, razon_social;" },
              { label: "Estado consignado en la lista", query: "SELECT vigente, estado, count(*) as total_entidades, string_agg(nombre_fantasia, ', ') as instituciones FROM factoring_leasing_lista_entidades GROUP BY vigente, estado ORDER BY vigente DESC;" },
              { label: "Tipos de licencia consignados", query: "SELECT tipo_licencia, count(*) as total, string_agg(nombre_fantasia, ', ') as instituciones FROM factoring_leasing_lista_entidades WHERE vigente = 1 GROUP BY tipo_licencia;" },
              { label: "Segmentación por Línea de Negocio", query: "SELECT segmento, count(*) as entidades, sum(es_factoring) as con_factoring, sum(es_leasing_financiero) as con_leasing, sum(es_automotriz) as con_automotriz FROM factoring_leasing_lista_entidades WHERE vigente = 1 GROUP BY segmento;" }
            ],
            tables: [
              { id: "factoring_leasing_lista_entidades", name: "factoring_leasing.lista_entidades", rows: "Una fila por sociedad", file: "outputs/factoring_leasing/factoring_leasing_maestro.parquet" }
            ]
          },
          // BEGIN AUTO FL IFRS SERIES NAVIGATION
          {
            id: "cat_factoring_leasing_balance", type: "circular",
            label: "Balance · Serie CMF (2009-03–2026-06)", badge: "70 cierres · 28 RUT", badgeType: "data", status: "active",
            sector: "factoring_leasing",
            chips: [{ label: "Cuentas de balance CMF · primeros 500", query: "SELECT periodo, rut, nombre_reportado, tipo_balance, moneda_archivo, orden, cuenta, valor_archivo, valor_texto_original, valor_es_entero, taxonomia, estado_financiero, repeticion_contexto FROM factoring_leasing_balance ORDER BY periodo DESC, rut, tipo_balance, estado_financiero, orden LIMIT 500;" }],
            tables: [{ id: "factoring_leasing_balance", name: "factoring_leasing.balance",
                       rows: "Serie IFRS · sin cotejo integral",
                       file: "outputs/factoring_leasing/factoring_leasing_balance_serie_ifrs_cmf.parquet" }]
          },
          {
            id: "cat_factoring_leasing_resultados", type: "circular",
            label: "Resultados · Serie CMF (2009-03–2026-06)", badge: "70 cierres · 28 RUT", badgeType: "data", status: "active",
            sector: "factoring_leasing",
            chips: [{ label: "Cuentas de resultados CMF · primeros 500", query: "SELECT periodo, rut, nombre_reportado, tipo_balance, moneda_archivo, orden, cuenta, valor_archivo, valor_texto_original, valor_es_entero, taxonomia, estado_financiero, repeticion_contexto FROM factoring_leasing_resultados ORDER BY periodo DESC, rut, tipo_balance, estado_financiero, orden LIMIT 500;" },
                    { label: "Utilidad del periodo · 1 fila por estado", query: "SELECT periodo, rut, nombre_reportado, tipo_balance, estado_financiero, valor_archivo AS ganancia_perdida FROM factoring_leasing_resultados WHERE lower(cuenta) = 'ganancia (pérdida)' AND estado_financiero IN ('ERFG', 'ERNG') AND repeticion_contexto = 1 ORDER BY periodo DESC, rut;" },
                    { label: "Dónde se repite 'Ganancia (pérdida)'", query: "SELECT estado_financiero, repeticion_contexto, count(*) AS filas, count(DISTINCT (periodo, rut, tipo_balance)) AS estados FROM factoring_leasing_resultados WHERE lower(cuenta) = 'ganancia (pérdida)' GROUP BY ALL ORDER BY estado_financiero, repeticion_contexto;" }],
            tables: [{ id: "factoring_leasing_resultados", name: "factoring_leasing.resultados",
                       rows: "Serie IFRS · sin cotejo integral",
                       file: "outputs/factoring_leasing/factoring_leasing_resultados_serie_ifrs_cmf.parquet" }]
          },
  // END AUTO FL IFRS SERIES NAVIGATION
        ]
      }
    ]
  },
  {
    id: "group_corredoras_bolsa",
    type: "group",
    label: "CORREDORAS DE BOLSA (CMF)",
    badges: [
      { type: "entities", text: "120 entidades", title: "Intermediarios de valores supervisados por la CMF (24 vigentes + 96 históricas)" },
      { type: "data", text: "Trimestral · 2010–2026", title: "Balance y resultados FECU IFRS de corredores de bolsa y agentes de valores, archivo trimestral CMF (63 trimestres). Se actualiza solo 3 veces al mes" }
    ],
    status: "active",
    children: [
      {
        id: "sector_corredoras_bolsa",
        type: "sector",
        label: "Corredoras de Bolsa (CMF)",
        sector: "corredoras_bolsa",
        children: [
          {
            id: "cat_corredoras_bolsa_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "120 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "corredoras_bolsa",
            chips: [
              { label: "Catálogo de Corredoras Vigentes", query: "SELECT rut, nombre_empresa, nombre_fantasia, grupo_financiero, estado_vigencia FROM corredoras_bolsa_lista_entidades WHERE estado_vigencia = 'Vigente' ORDER BY nombre_empresa;" },
              { label: "Distribución por Conglomerado", query: "SELECT grupo_financiero, count(*) as total_corredoras, sum(CASE WHEN estado_vigencia = 'Vigente' THEN 1 ELSE 0 END) as vigentes FROM corredoras_bolsa_lista_entidades GROUP BY grupo_financiero ORDER BY total_corredoras DESC;" }
            ],
            tables: [
              { id: "corredoras_bolsa_lista_entidades", name: "corredoras.lista_entidades", rows: "Una fila por corredora", file: "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet" }
            ]
          },
          {
            id: "cat_corredoras_bolsa_lista_entidades_registro",
            type: "circular",
            label: "Lista de Entidades · Registro",
            badge: "120 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "corredoras_bolsa",
            chips: [
              { label: "Catálogo de Corredoras por Grupo Financiero", query: "SELECT rut, nombre_empresa, nombre_fantasia, grupo_financiero, estado_vigencia FROM corredoras_bolsa_lista_entidades_registro ORDER BY estado_vigencia DESC, grupo_financiero, nombre_empresa;" },
              { label: "Distribución de Corredoras por Conglomerado", query: "SELECT grupo_financiero, count(*) as total_corredoras, sum(CASE WHEN estado_vigencia = 'Vigente' THEN 1 ELSE 0 END) as vigentes, string_agg(nombre_fantasia, ', ') as instituciones FROM corredoras_bolsa_lista_entidades_registro GROUP BY grupo_financiero ORDER BY total_corredoras DESC;" }
            ],
            tables: [
              { id: "corredoras_bolsa_lista_entidades_registro", name: "corredoras.lista_entidades_registro", rows: "Una fila por corredora", file: "outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.parquet" }
            ]
          },
          {
            id: "cat_corredoras_bolsa_balance",
            type: "circular",
            label: "Balance FECU IFRS · CMF (2010-12–2026-06)",
            badge: "63 trimestres",
            badgeType: "data",
            status: "active",
            sector: "corredoras_bolsa",
            chips: [
              { label: "Activos, pasivos y patrimonio por intermediario, último trimestre (MM$)", query: "SELECT periodo, razon_social, tipo_intermediario, round(max(valor_miles_clp) FILTER (WHERE codigo_fecu = '10.00.00') / 1e3, 1) AS activos_mm, round(max(valor_miles_clp) FILTER (WHERE codigo_fecu = '21.00.00') / 1e3, 1) AS pasivos_mm, round(max(valor_miles_clp) FILTER (WHERE codigo_fecu = '22.00.00') / 1e3, 1) AS patrimonio_mm FROM corredoras_bolsa_balance WHERE periodo = (SELECT max(periodo) FROM corredoras_bolsa_balance) GROUP BY ALL ORDER BY activos_mm DESC NULLS LAST;" },
              { label: "Evolución de los corredores de bolsa: activos totales por trimestre (MM$)", query: "SELECT periodo, count(DISTINCT rut) AS corredores, round(sum(valor_miles_clp) / 1e3, 1) AS activos_mm FROM corredoras_bolsa_balance WHERE codigo_fecu = '10.00.00' AND tipo_intermediario = 'corredor de bolsa' GROUP BY periodo ORDER BY periodo;" },
              { label: "Balance completo de Banchile Corredores, último trimestre", query: "SELECT periodo, seccion, codigo_fecu, nivel, cuenta, valor_miles_clp FROM corredoras_bolsa_balance WHERE rut = '96571220' AND periodo = (SELECT max(periodo) FROM corredoras_bolsa_balance) ORDER BY codigo_fecu;" }
            ],
            tables: [
              { id: "corredoras_bolsa_balance", name: "corredoras.balance", rows: "FECU IFRS", file: "", files: ["outputs/corredoras_bolsa/corredoras_bolsa_balance/manifest.json"] }
            ]
          },
          {
            id: "cat_corredoras_bolsa_resultados",
            type: "circular",
            label: "Estado de Resultados FECU IFRS · CMF (2010-12–2026-06)",
            badge: "63 trimestres",
            badgeType: "data",
            status: "active",
            sector: "corredoras_bolsa",
            chips: [
              { label: "Resultado del ejercicio por intermediario, 2025 (MM$)", query: "SELECT razon_social, tipo_intermediario, round(max(valor_miles_clp) FILTER (WHERE codigo_fecu = '30.00.00') / 1e3, 1) AS resultado_ejercicio_mm FROM corredoras_bolsa_resultados WHERE periodo = '2025-12' GROUP BY ALL ORDER BY resultado_ejercicio_mm DESC NULLS LAST;" },
              { label: "Estructura de resultados de Banchile Corredores, 2025", query: "SELECT estado_financiero, seccion, codigo_fecu, nivel, cuenta, valor_miles_clp FROM corredoras_bolsa_resultados WHERE rut = '96571220' AND periodo = '2025-12' ORDER BY codigo_fecu;" },
              { label: "Catálogo de cuentas FECU de resultados", query: "SELECT codigo_fecu, any_value(cuenta) AS cuenta, any_value(seccion) AS seccion, count(*) AS filas FROM corredoras_bolsa_resultados GROUP BY codigo_fecu ORDER BY codigo_fecu;" }
            ],
            tables: [
              { id: "corredoras_bolsa_resultados", name: "corredoras.resultados", rows: "FECU IFRS", file: "", files: ["outputs/corredoras_bolsa/corredoras_bolsa_resultados/manifest.json"] }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_securitizacion",
    type: "group",
    label: "SECURITIZACIÓN (CMF / LEY 18.045)",
    badges: [
      { type: "entities", text: "16 gestoras", title: "Sociedades securitizadoras y sus patrimonios separados son entidades distintas" },
      { type: "data", text: "Anual · 2009–2026", title: "Balances de diciembre 2014–2025 de patrimonios separados (de 2010 a 2013 no hay datos); los balances de las gestoras son otra serie, anual 2009–2026" }
    ],
    status: "active",
    children: [
      {
        id: "sector_securitizadoras",
        type: "sector",
        label: "Sociedades Securitizadoras (CMF)",
        sector: "securitizadoras",
        children: [
          {
            id: "cat_securitizadoras_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "16 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "securitizadoras",
            chips: [
              { label: "Catálogo de Securitizadoras (Vigentes vs Históricas)", query: "SELECT rut_completo, razon_social, estado_vigencia, lineas_deuda_registradas FROM securitizadoras_lista_entidades ORDER BY estado_vigencia, razon_social;" },
              { label: "Securitizadoras con Emisiones Activas CMF", query: "SELECT razon_social, rut_completo, lineas_deuda_registradas, cmf_url FROM securitizadoras_lista_entidades WHERE lineas_deuda_registradas > 0 ORDER BY lineas_deuda_registradas DESC;" }
            ],
            tables: [
              { id: "securitizadoras_lista_entidades", name: "securitizadoras.lista_entidades", rows: "Una fila por sociedad", file: "outputs/securitizadoras/securitizadoras_maestro.parquet" }
            ]
          },
          {
            id: "cat_securitizadoras_balance",
            type: "circular",
            label: "Balance IFRS · CMF (2009-12–2026-06)",
            badge: "66 trimestres",
            badgeType: "data",
            status: "active",
            sector: "securitizadoras",
            chips: [
              { label: "Activos, pasivos y patrimonio por securitizadora, último trimestre (MM$)", query: "SELECT periodo, razon_social, tipo_balance, moneda, round(max(valor) FILTER (WHERE cuenta = 'Total de activos') / 1e6, 1) AS activos_mm, round(max(valor) FILTER (WHERE cuenta = 'Total de pasivos') / 1e6, 1) AS pasivos_mm, round(max(valor) FILTER (WHERE cuenta = 'Patrimonio total') / 1e6, 1) AS patrimonio_mm FROM securitizadoras_balance WHERE periodo = (SELECT max(periodo) FROM securitizadoras_balance) AND repeticion = 1 GROUP BY ALL ORDER BY activos_mm DESC NULLS LAST;" },
              { label: "Evolución del sector: activos totales por trimestre (MM$, CLP)", query: "SELECT periodo, count(DISTINCT rut) AS entidades, round(sum(valor) / 1e6, 1) AS activos_mm_clp FROM securitizadoras_balance WHERE cuenta = 'Total de activos' AND moneda = 'CLP' AND repeticion = 1 GROUP BY periodo ORDER BY periodo;" },
              { label: "Balance completo de BCI Securitizadora, último trimestre", query: "SELECT periodo, tipo_balance, estado_financiero, orden, cuenta, valor FROM securitizadoras_balance WHERE rut = '96948880' AND periodo = (SELECT max(periodo) FROM securitizadoras_balance WHERE rut = '96948880') ORDER BY tipo_balance, estado_financiero, orden;" }
            ],
            tables: [
              { id: "securitizadoras_balance", name: "securitizadoras.balance", rows: "Serie IFRS", file: "", files: ["outputs/securitizadoras/securitizadoras_balance/manifest.json"] }
            ]
          },
          {
            id: "cat_securitizadoras_resultados",
            type: "circular",
            label: "Estado de Resultados IFRS · CMF (2009-12–2026-06)",
            badge: "66 trimestres",
            badgeType: "data",
            status: "active",
            sector: "securitizadoras",
            chips: [
              { label: "Ingresos y utilidad por securitizadora, ejercicio 2025 (MM$)", query: "SELECT razon_social, tipo_balance, moneda, round(max(valor) FILTER (WHERE cuenta = 'Ingresos de actividades ordinarias') / 1e6, 1) AS ingresos_mm, round(max(valor) FILTER (WHERE cuenta = 'Ganancia (pérdida)') / 1e6, 1) AS ganancia_mm FROM securitizadoras_resultados WHERE periodo = '2025-12' AND estado_financiero IN ('ERFG', 'ERNG') AND repeticion = 1 GROUP BY ALL ORDER BY ganancia_mm DESC NULLS LAST;" },
              { label: "Por qué hay que filtrar: «Ganancia (pérdida)» aparece varias veces", query: "SELECT estado_financiero, repeticion, count(*) AS filas, count(DISTINCT rut) AS entidades FROM securitizadoras_resultados WHERE periodo = '2025-12' AND cuenta = 'Ganancia (pérdida)' GROUP BY ALL ORDER BY estado_financiero, repeticion;" },
              { label: "Utilidad del sector por año (cierres de diciembre, MM$, CLP)", query: "SELECT left(periodo, 4) AS anio, count(DISTINCT rut) AS entidades, round(sum(valor) / 1e6, 1) AS ganancia_mm_clp FROM securitizadoras_resultados WHERE periodo LIKE '%-12' AND cuenta = 'Ganancia (pérdida)' AND estado_financiero IN ('ERFG', 'ERNG') AND repeticion = 1 AND moneda = 'CLP' GROUP BY 1 ORDER BY 1;" },
              { label: "Estado de resultados completo de BCI Securitizadora, ejercicio 2025", query: "SELECT tipo_balance, estado_financiero, orden, cuenta, valor FROM securitizadoras_resultados WHERE rut = '96948880' AND periodo = '2025-12' ORDER BY tipo_balance, estado_financiero, orden;" }
            ],
            tables: [
              { id: "securitizadoras_resultados", name: "securitizadoras.resultados", rows: "Serie IFRS", file: "", files: ["outputs/securitizadoras/securitizadoras_resultados/manifest.json"] }
            ]
          }
        ]
      },
      {
        id: "sector_patrimonios_separados",
        type: "sector",
        label: "Patrimonios Separados (CMF)",
        sector: "patrimonios_separados",
        children: [
          {
            id: "cat_patrimonios_separados_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "18 Emisiones",
            badgeType: "entities",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Líneas por clase de colateral", query: "SELECT clase_colateral_subyacente, count(*) as lineas, string_agg(razon_social_administradora, ', ') as administradoras FROM patrimonios_separados_lista_entidades GROUP BY clase_colateral_subyacente ORDER BY lineas DESC;" },
              { label: "Inscripciones por moneda y monto", query: "SELECT numero_inscripcion, fecha_inscripcion, razon_social_administradora, denominacion_emision, moneda, monto_inscrito, clase_colateral_subyacente FROM patrimonios_separados_lista_entidades ORDER BY fecha_inscripcion DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_lista_entidades", name: "patrimonios_separados.lista_entidades", rows: "Una fila por patrimonio", file: "outputs/securitizadoras/patrimonios_separados_maestro.parquet" }
            ]
          },
          {
            id: "cat_patrimonios_separados_balance",
            type: "circular",
            label: "Balance General (diciembre 2014–2025; 2010–2013 sin datos)",
            badge: "358 Balances",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Cobertura por año (2010–2013 sin datos)", query: "SELECT a.anio, count(DISTINCT b.archivo) AS balances, CASE WHEN a.anio < 2014 THEN 'Sin datos: la serie parte en diciembre de 2014' ELSE 'Cierre de diciembre' END AS nota FROM range(2010, 2026) a(anio) LEFT JOIN patrimonios_separados_balance b ON b.anio = a.anio GROUP BY a.anio ORDER BY a.anio;" },
              { label: "Totales por patrimonio, diciembre 2025", query: "SELECT nombre_administradora, codigo_patrimonio, activos_m_clp, pasivos_m_clp, patrimonio_m_clp FROM (SELECT periodo, rut_administradora, nombre_administradora, codigo_patrimonio, sum(monto_m_clp) FILTER (WHERE categoria = 'Total Activos') AS activos_m_clp, sum(monto_m_clp) FILTER (WHERE categoria IN ('Total Pasivo Circulante', 'Total Pasivo No Circulante')) AS pasivos_m_clp, sum(monto_m_clp) FILTER (WHERE categoria = 'Total Patrimonio (Excedente Acumulado)') AS patrimonio_m_clp FROM patrimonios_separados_balance GROUP BY ALL) WHERE periodo = '2025-12' ORDER BY activos_m_clp DESC;" },
              { label: "Agregado del sector por cierre", query: "SELECT periodo, count(*) AS patrimonios, sum(activos_m_clp) AS activos_m_clp, sum(pasivos_m_clp) AS pasivos_m_clp, sum(patrimonio_m_clp) AS patrimonio_m_clp FROM (SELECT periodo, rut_administradora, nombre_administradora, codigo_patrimonio, sum(monto_m_clp) FILTER (WHERE categoria = 'Total Activos') AS activos_m_clp, sum(monto_m_clp) FILTER (WHERE categoria IN ('Total Pasivo Circulante', 'Total Pasivo No Circulante')) AS pasivos_m_clp, sum(monto_m_clp) FILTER (WHERE categoria = 'Total Patrimonio (Excedente Acumulado)') AS patrimonio_m_clp FROM patrimonios_separados_balance GROUP BY ALL) GROUP BY periodo ORDER BY periodo;" },
              { label: "Por securitizadora, diciembre 2025", query: "SELECT coalesce(s.razon_social, t.nombre_administradora) AS securitizadora, count(*) AS patrimonios, sum(t.activos_m_clp) AS activos_m_clp, sum(t.pasivos_m_clp) AS pasivos_m_clp, sum(t.patrimonio_m_clp) AS patrimonio_m_clp FROM (SELECT periodo, rut_administradora, nombre_administradora, codigo_patrimonio, sum(monto_m_clp) FILTER (WHERE categoria = 'Total Activos') AS activos_m_clp, sum(monto_m_clp) FILTER (WHERE categoria IN ('Total Pasivo Circulante', 'Total Pasivo No Circulante')) AS pasivos_m_clp, sum(monto_m_clp) FILTER (WHERE categoria = 'Total Patrimonio (Excedente Acumulado)') AS patrimonio_m_clp FROM patrimonios_separados_balance GROUP BY ALL) t LEFT JOIN securitizadoras_lista_entidades s ON s.rut = t.rut_administradora WHERE t.periodo = '2025-12' GROUP BY ALL ORDER BY activos_m_clp DESC;" },
              { label: "Balance completo de un patrimonio", query: "SELECT orden_en_balance, categoria, cuenta, monto_m_clp FROM patrimonios_separados_balance WHERE periodo = '2025-12' AND nombre_administradora = 'SECURITIZADORA SECURITY' AND codigo_patrimonio = (SELECT min(codigo_patrimonio) FROM patrimonios_separados_balance WHERE periodo = '2025-12' AND nombre_administradora = 'SECURITIZADORA SECURITY') ORDER BY orden_en_balance;" },
              { label: "Pasivos de diciembre 2025 por cuenta", query: "SELECT categoria, cuenta, sum(monto_m_clp) AS monto_m_clp, count(*) AS patrimonios FROM patrimonios_separados_balance WHERE categoria IN ('Pasivo Circulante', 'Pasivo No Circulante') AND periodo = '2025-12' GROUP BY ALL ORDER BY monto_m_clp DESC;" },
              { label: "Cuentas más frecuentes por rubro", query: "SELECT categoria, cuenta, count(*) AS balances, sum(monto_m_clp) AS suma_m_clp FROM patrimonios_separados_balance WHERE categoria NOT LIKE 'Total%' GROUP BY ALL ORDER BY balances DESC LIMIT 30;" }
            ],
            tables: [
              { id: "patrimonios_separados_balance", name: "patrimonios_separados.balance", rows: "Balance", file: "outputs/securitizadoras/patrimonios_separados_balance.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_cooperativas",
    type: "group",
    label: "COOPERATIVAS DE AHORRO Y CRÉDITO (CMF)",
    badges: [
      { type: "entities", text: "7 entidades", title: "Cooperativas de ahorro y crédito supervisadas por la CMF" },
      { type: "data", text: "Sólo registro de entidades", title: "Sólo su lista de entidades (identidad y vigencia); sin estados financieros ni carteras" }
    ],
    status: "active",
    children: [
      {
        id: "sector_cooperativas",
        type: "sector",
        label: "Cooperativas de Ahorro y Crédito (CMF)",
        sector: "cooperativas",
        children: [
          {
            id: "cat_cooperativas_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "7 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "cooperativas",
            chips: [
              { label: "Directorio de Cooperativas Fiscalizadas", query: "SELECT rut, nombre_empresa, nombre_fantasia, sede_matriz, region, estado_vigencia FROM cooperativas_lista_entidades ORDER BY nombre_fantasia;" },
              { label: "Distribución Regional de Cooperativas", query: "SELECT region, count(*) as total_entidades, string_agg(nombre_fantasia, ', ') as instituciones FROM cooperativas_lista_entidades GROUP BY region ORDER BY total_entidades DESC;" }
            ],
            tables: [
              { id: "cooperativas_lista_entidades", name: "cooperativas.lista_entidades", rows: "Una fila por cooperativa", file: "outputs/cooperativas/cooperativas_maestro.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_cajas_compensacion",
    type: "group",
    label: "CAJAS DE COMPENSACION (CCAF / SUSESO - CMF)",
    badges: [
      { type: "entities", text: "6 entidades", title: "Los Andes, La Araucana, Los Héroes, Caja 18 (y 2 históricas)" },
      { type: "data", text: "Trimestral · 2010–2026", title: "Balance y resultados IFRS de las cajas que envían estados financieros XBRL a la CMF (archivo TXT trimestral CMF, 65 trimestres). Se actualiza solo 3 veces al mes" }
    ],
    status: "active",
    children: [
      {
        id: "sector_cajas_compensacion",
        type: "sector",
        label: "Cajas de Compensación (CCAF / SUSESO)",
        sector: "cajas_compensacion",
        children: [
          {
            id: "cat_ccaf_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "6 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "cajas_compensacion",
            chips: [
              { label: "Catálogo CCAF (Vigentes vs Absorbidas)", query: "SELECT rut_completo, nombre_fantasia, estado_vigencia, regulador_mercado_valores, codigo_cmf, lineas_deuda_registradas FROM ccaf_lista_entidades ORDER BY estado_vigencia DESC, nombre_fantasia;" },
              { label: "CCAF Emisoras de Bonos Públicos CMF", query: "SELECT rut_completo, razon_social, codigo_cmf, lineas_deuda_registradas, cmf_url FROM ccaf_lista_entidades WHERE emisor_valores_cmf = true ORDER BY rut;" },
              { label: "CCAF Supervisadas Exclusivamente por SUSESO", query: "SELECT rut_completo, razon_social, domicilio_casa_matriz, suseso_url, observaciones FROM ccaf_lista_entidades WHERE emisor_valores_cmf = false AND estado_vigencia = 'Vigente';" }
            ],
            tables: [
              { id: "ccaf_lista_entidades", name: "ccaf.lista_entidades", rows: "Una fila por caja", file: "outputs/cajas_compensacion/ccaf_maestro.parquet" }
            ]
          },
          {
            id: "cat_ccaf_balance",
            type: "circular",
            label: "Balance IFRS · CMF (2010-06–2026-06)",
            badge: "65 trimestres",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            chips: [
              { label: "Activos, pasivos y patrimonio por CCAF, último trimestre (MM$)", query: "SELECT periodo, razon_social, tipo_balance, moneda, round(max(valor) FILTER (WHERE cuenta = 'Total de activos') / 1e6, 1) AS activos_mm, round(max(valor) FILTER (WHERE cuenta = 'Total de pasivos') / 1e6, 1) AS pasivos_mm, round(max(valor) FILTER (WHERE cuenta = 'Patrimonio total') / 1e6, 1) AS patrimonio_mm FROM ccaf_balance WHERE periodo = (SELECT max(periodo) FROM ccaf_balance) AND repeticion = 1 GROUP BY ALL ORDER BY activos_mm DESC NULLS LAST;" },
              { label: "Evolución del sector: activos totales por trimestre (MM$, CLP)", query: "SELECT periodo, count(DISTINCT rut) AS entidades, round(sum(valor) / 1e6, 1) AS activos_mm_clp FROM ccaf_balance WHERE cuenta = 'Total de activos' AND moneda = 'CLP' AND repeticion = 1 GROUP BY periodo ORDER BY periodo;" },
              { label: "Balance completo de CCAF Los Andes, último trimestre", query: "SELECT periodo, tipo_balance, estado_financiero, orden, cuenta, valor FROM ccaf_balance WHERE rut = '81826800' AND periodo = (SELECT max(periodo) FROM ccaf_balance WHERE rut = '81826800') ORDER BY tipo_balance, estado_financiero, orden;" }
            ],
            tables: [
              { id: "ccaf_balance", name: "ccaf.balance", rows: "Serie IFRS", file: "", files: ["outputs/cajas_compensacion/ccaf_balance/manifest.json"] }
            ]
          },
          {
            id: "cat_ccaf_resultados",
            type: "circular",
            label: "Estado de Resultados IFRS · CMF (2010-06–2026-06)",
            badge: "65 trimestres",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            chips: [
              { label: "Ingresos y utilidad por CCAF, ejercicio 2025 (MM$)", query: "SELECT razon_social, tipo_balance, moneda, round(max(valor) FILTER (WHERE cuenta = 'Ingresos de actividades ordinarias') / 1e6, 1) AS ingresos_mm, round(max(valor) FILTER (WHERE cuenta = 'Ganancia (pérdida)') / 1e6, 1) AS ganancia_mm FROM ccaf_resultados WHERE periodo = '2025-12' AND estado_financiero IN ('ERFG', 'ERNG') AND repeticion = 1 GROUP BY ALL ORDER BY ganancia_mm DESC NULLS LAST;" },
              { label: "Por qué hay que filtrar: «Ganancia (pérdida)» aparece varias veces", query: "SELECT estado_financiero, repeticion, count(*) AS filas, count(DISTINCT rut) AS entidades FROM ccaf_resultados WHERE periodo = '2025-12' AND cuenta = 'Ganancia (pérdida)' GROUP BY ALL ORDER BY estado_financiero, repeticion;" },
              { label: "Utilidad del sector por año (cierres de diciembre, MM$, CLP)", query: "SELECT left(periodo, 4) AS anio, count(DISTINCT rut) AS entidades, round(sum(valor) / 1e6, 1) AS ganancia_mm_clp FROM ccaf_resultados WHERE periodo LIKE '%-12' AND cuenta = 'Ganancia (pérdida)' AND estado_financiero IN ('ERFG', 'ERNG') AND repeticion = 1 AND moneda = 'CLP' GROUP BY 1 ORDER BY 1;" },
              { label: "Estado de resultados completo de CCAF Los Andes, ejercicio 2025", query: "SELECT tipo_balance, estado_financiero, orden, cuenta, valor FROM ccaf_resultados WHERE rut = '81826800' AND periodo = '2025-12' ORDER BY tipo_balance, estado_financiero, orden;" }
            ],
            tables: [
              { id: "ccaf_resultados", name: "ccaf.resultados", rows: "Serie IFRS", file: "", files: ["outputs/cajas_compensacion/ccaf_resultados/manifest.json"] }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_sistemas_pago",
    type: "group",
    label: "SISTEMAS DE PAGO (BCCh / CMF)",
    badges: [
      { type: "entities", text: "12 entidades", title: "Infraestructuras críticas de liquidación, custodia, compensación y adquirencia" },
      { type: "data", text: "Sólo registro de entidades", title: "Sólo su lista de entidades (identidad y vigencia)" }
    ],
    status: "active",
    children: [
      {
        id: "sector_pagos_infraestructura",
        type: "sector",
        label: "Infraestructura Financiera y Redes de Pago",
        sector: "sistemas_pago",
        children: [
          {
            id: "cat_sistemas_pago_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "12 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "sistemas_pago",
            chips: [
              { label: "Directorio de Infraestructuras", query: "SELECT codigo_sistema, nombre_comercial, tipo_sistema, supervisor FROM sistemas_pago_lista_entidades ORDER BY codigo_sistema;" },
              { label: "Cámaras y Contrapartes Centrales", query: "SELECT codigo_sistema, razon_social, marco_legal FROM sistemas_pago_lista_entidades WHERE tipo_sistema LIKE '%Cámara%' OR tipo_sistema LIKE '%Contraparte%';" }
            ],
            tables: [
              { id: "sistemas_pago_lista_entidades", name: "sistemas_pago.lista_entidades", rows: "Una fila por entidad", file: "outputs/sistemas_pago/sistemas_pago_maestro.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_fintech",
    type: "group",
    label: "FINTECH & FINANZAS ABIERTAS (LEY N° 21.521 / CMF)",
    badges: [
      { type: "entities", text: "262 entidades", title: "Entidades inscritas en el Registro de Prestadores de Servicios Financieros CMF" },
      { type: "data", text: "Sólo registro de entidades", title: "Sólo su lista de entidades (identidad y vigencia)" }
    ],
    status: "active",
    children: [
      {
        id: "sector_fintech",
        type: "sector",
        label: "Fintech y Finanzas Abiertas (CMF)",
        sector: "fintech",
        children: [
          {
            id: "cat_fintech_rpsf_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "262 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "fintech",
            chips: [
              { label: "Prestadores Vigentes", query: "SELECT rut_completo, razon_social, tipo_persona, servicios_acreditados_total FROM fintech_rpsf_lista_entidades WHERE estado_vigencia = 'Vigente' ORDER BY servicios_acreditados_total DESC, razon_social LIMIT 15;" },
              { label: "Distribución Regional", query: "SELECT region, COUNT(*) AS total_entidades FROM fintech_rpsf_lista_entidades WHERE region != '' GROUP BY region ORDER BY total_entidades DESC;" }
            ],
            tables: [
              { id: "fintech_rpsf_lista_entidades", name: "fintech.lista_entidades", rows: "Una fila por prestador", file: "outputs/fintech/fintech_rpsf_maestro.parquet" }
            ]
          }
        ]
      }
    ]
  }
];

// Clave del bloque «Archivo y registros complementarios» en expandedNodes.
const ARCHIVE_NODE = "tier_fuera";

function escapeAttr(texto) {
  return String(texto === null || texto === undefined ? "" : texto)
    .replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* El mapa relacional se construye la primera vez que se necesita (window.asegurarERD,
   en index.html). Las llamadas del explorador —enfocar un sector, abrir el esquema de
   una tabla— lo crean si aún no existe, para que el mapa refleje la selección cuando
   el visitante abra su pestaña. Al cargar la página no se construye. */
function mapaERD() {
  if (typeof window.asegurarERD === "function") return window.asegurarERD();
  return window.erdInstance || null;
}

class SidebarController {
  constructor() {
    this.sidebar = document.getElementById("sidebar");
    this.treeContainer = document.getElementById("sidebar-tree");
    this.searchInput = document.getElementById("sidebar-search");
    this.toggleBtn = document.getElementById("toggle-sidebar");
    this.breadcrumbEl = document.getElementById("erd-breadcrumb");

    this.selectedTableId = "seguros_lista_entidades";
    this.activeSector = "seguros";
    window.MFC_ACTIVE_SECTOR = this.activeSector;
    // El explorador se muestra colapsado al cargar: el usuario decide qué abrir.
    // Los identificadores son group.id, sector/circular id y "part_<tabla>" para particiones.
    this.expandedNodes = new Set();

    this.render();
    this.initEvents();
  }

  initEvents() {
    if (this.toggleBtn) {
      this.toggleBtn.addEventListener("click", () => {
        this.sidebar.classList.toggle("collapsed");
        setTimeout(() => {
          const erd = mapaERD();
          if (erd) erd.resize();
        }, 300);
      });
    }

    if (this.searchInput) {
      this.searchInput.addEventListener("input", (e) => {
        this.filterTree(e.target.value.toLowerCase().trim());
      });
    }

    this.initSidebarResizer();
  }

  initSidebarResizer() {
    const resizer = document.getElementById("sidebar-resizer");
    const sidebar = this.sidebar;
    if (!resizer || !sidebar) return;

    let isResizing = false;
    let startX = 0;
    let startWidth = 0;

    resizer.addEventListener("mousedown", (e) => {
      isResizing = true;
      startX = e.clientX;
      startWidth = sidebar.getBoundingClientRect().width;
      resizer.classList.add("resizing");
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    });

    document.addEventListener("mousemove", (e) => {
      if (!isResizing) return;
      const newWidth = Math.min(Math.max(startWidth + (e.clientX - startX), 220), 550);
      sidebar.style.width = `${newWidth}px`;
      sidebar.style.minWidth = `${newWidth}px`;
      const erd = mapaERD();
      if (erd) erd.resize();
    });

    document.addEventListener("mouseup", () => {
      if (isResizing) {
        isResizing = false;
        resizer.classList.remove("resizing");
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        const erd = mapaERD();
        if (erd) erd.resize();
      }
    });
  }

  /* ── Alcance editorial (recorte visual) ─────────────────────────────────
     El nivel de cada industria (núcleo, instituciones, contexto, archivo o
     registro) sale de docs/vocabulario.json vía window.SIFAlcance. Sin él, el
     árbol se dibuja completo y plano, como antes del recorte. */

  alcance() {
    const A = window.SIFAlcance;
    return A && A.disponible() ? A : null;
  }

  // Nivel de un grupo: el de su primer sector (los sectores de un grupo comparten nivel).
  nivelDeGrupo(group) {
    const A = this.alcance();
    const primero = A && (group.children || [])[0];
    return primero ? A.nivelDe(primero.sector) : null;
  }

  // Grupos del árbol repartidos por nivel, en el orden editorial.
  seccionesPorNivel() {
    const A = this.alcance();
    if (!A) return null;
    const niveles = A.niveles();
    const secciones = niveles.map((nivel) => ({ nivel, grupos: [] }));
    const ultimaVisible = secciones.filter((s) => s.nivel.visible).pop() || secciones[0];
    EXPLORER_TREE.forEach((group) => {
      const id = this.nivelDeGrupo(group);
      const destino = secciones.find((s) => s.nivel.id === id) || ultimaVisible;
      destino.grupos.push(group);
    });
    secciones.forEach((s) => s.grupos.sort((a, b) =>
      A.orden((a.children[0] || {}).sector) - A.orden((b.children[0] || {}).sector)));
    return secciones.filter((s) => s.grupos.length > 0);
  }

  // Carpetas de un sector tal como se muestran: sin tablas ocultas (p. ej. una tabla
  // todavía sin datos en la fuente) y con las variantes dentro de la carpeta de su tabla
  // principal (p. ej. el registro CMF de corredoras, que repite la misma lista).
  carpetasVisibles(sector) {
    const A = this.alcance();
    const carpetas = sector.children || [];
    if (!A) return carpetas.map((circ) => ({ circ, tablas: circ.tables || [], variantes: [] }));
    const absorbidas = new Set();
    const variantes = new Map();
    carpetas.forEach((circ) => {
      const tablas = circ.tables || [];
      const padres = tablas.map((t) => A.varianteDe(t.id));
      if (!tablas.length || !padres.every(Boolean)) return;
      const destino = carpetas.find((otra) => otra !== circ && (otra.tables || []).some((t) => padres.indexOf(t.id) !== -1));
      if (!destino) return;
      absorbidas.add(circ.id);
      if (!variantes.has(destino.id)) variantes.set(destino.id, []);
      tablas.forEach((tbl) => variantes.get(destino.id).push({ tbl, circ }));
    });
    return carpetas
      .filter((circ) => !absorbidas.has(circ.id))
      .map((circ) => ({
        circ,
        tablas: (circ.tables || []).filter((t) => !A.tablaOculta(t.id)),
        variantes: variantes.get(circ.id) || []
      }))
      .filter((c) => c.tablas.length > 0 || c.variantes.length > 0);
  }

  // Consultas sugeridas de una carpeta, sumando las de sus variantes.
  chipsDeCarpeta(circId) {
    for (const grp of EXPLORER_TREE) {
      for (const sec of grp.children) {
        const entrada = this.carpetasVisibles(sec).find((c) => c.circ.id === circId);
        if (!entrada) continue;
        const chips = (entrada.circ.chips || []).slice();
        const vistas = new Set();
        entrada.variantes.forEach(({ circ }) => {
          if (vistas.has(circ.id)) return;
          vistas.add(circ.id);
          (circ.chips || []).forEach((chip) => chips.push(chip));
        });
        return chips;
      }
    }
    return null;
  }

  render() {
    if (!this.treeContainer) return;

    let html = `
      <div class="explorer-toolbar">
        <div class="toolbar-title">EXPLORADOR</div>
        <div class="toolbar-actions">
          <button class="tool-btn" id="btn-expand-all" title="Expandir todo (el archivo sigue plegado)">Expandir</button>
          <button class="tool-btn" id="btn-collapse-all" title="Colapsar todo">Colapsar</button>
          <button class="tool-btn" id="btn-show-all" title="Vista principal: quita el filtro de industria (núcleo, instituciones y contexto)">Principal</button>
        </div>
      </div>
      <div class="tree-root">
    `;

    const secciones = this.seccionesPorNivel();
    if (!secciones) {
      EXPLORER_TREE.forEach((group) => { html += this.renderGroup(group, null); });
    } else {
      const dentro = secciones.filter((s) => s.nivel.visible);
      const fuera = secciones.filter((s) => !s.nivel.visible);
      dentro.forEach((seccion) => { html += this.renderTier(seccion); });
      if (fuera.length) html += this.renderArchive(fuera);
    }

    html += `</div>`;
    this.treeContainer.innerHTML = html;
    this.bindTreeEvents();
  }

  renderTier(seccion) {
    const A = this.alcance();
    const nivel = seccion.nivel;
    const meta = nivel.conjuntos
      ? `${A.numero(nivel.conjuntos)} conj. · ${A.compacto(nivel.filas)} filas`
      : "";
    const aviso = nivel.aviso ? `<div class="tree-tier-aviso">${nivel.aviso}</div>` : "";
    return `
      <div class="tree-tier tier-${nivel.id}" data-tier="${nivel.id}">
        <div class="tree-tier-header" title="${escapeAttr(nivel.descripcion || nivel.etiqueta)}">
          <span class="tree-tier-title">${nivel.etiqueta}</span>
          <span class="tree-tier-meta">${meta}</span>
        </div>
        ${aviso}
        ${seccion.grupos.map((group) => this.renderGroup(group, nivel)).join("")}
      </div>
    `;
  }

  // Archivo congelado y registro complementario: al final y plegados, pero en el DOM,
  // de modo que la búsqueda del explorador los encuentra y los abre.
  renderArchive(secciones) {
    const A = this.alcance();
    const fuera = A.datos().fuera;
    const industrias = secciones.reduce((n, s) => n + s.grupos.length, 0);
    const abierto = this.expandedNodes.has(ARCHIVE_NODE);
    return `
      <div class="tree-archive ${abierto ? "open" : ""}" data-archive="${ARCHIVE_NODE}">
        <button type="button" class="tree-archive-toggle" aria-expanded="${abierto ? "true" : "false"}"
                title="Industrias fuera del foco de esta edición: siguen publicadas, consultables y descargables">
          <span class="arrow-slot">${abierto ? ICONS.chevronDown : ICONS.chevronRight}</span>
          <span class="tree-archive-title">Archivo y registros complementarios</span>
          <span class="tree-archive-meta">${industrias} industrias · ${A.numero(fuera.conjuntos)} conj. · ${A.porcentaje(fuera.pct_filas)} de las filas</span>
        </button>
        <div class="tree-archive-body">
          ${secciones.map((seccion) => this.renderTier(seccion)).join("")}
        </div>
      </div>
    `;
  }

  renderTableRow(tbl, circular, variante) {
    const isSelected = tbl.id === this.selectedTableId ? "selected" : "";
    const hasPartitions = tbl.partitions && tbl.partitions.length > 0;
    const partKey = `part_${tbl.id}`;
    const isPartOpen = this.expandedNodes.has(partKey);
    const arrowHtml = hasPartitions
      ? `<span class="arrow-slot tbl-arrow-slot" data-target="${partKey}">${isPartOpen ? ICONS.chevronDown : ICONS.chevronRight}</span>`
      : `<span class="arrow-slot empty"></span>`;

    let partHtml = "";
    if (hasPartitions) {
      tbl.partitions.forEach((part) => {
        const isPartSelected = part.id === this.selectedTableId ? "selected" : "";
        partHtml += `
          <div class="tree-row tree-table tree-partition ${isPartSelected}" data-table-id="${part.id}" data-file="${part.file}" data-name="${tbl.name} (${part.name})" data-sector="${circular.sector}">
            <span class="tree-indent-4"></span>
            <svg class="tree-icon icon-partition" width="11" height="11" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M3 2a1 1 0 011 1v8a2 2 0 002 2h7a1 1 0 110 2H6a4 4 0 01-4-4V3a1 1 0 011-1z"/><path fill-rule="evenodd" d="M11.293 10.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L12.586 15H6a1 1 0 110-2h6.586l-1.293-1.293a1 1 0 010-1.414z"/></svg>
            <span class="tree-label partition-label">${part.name}</span>
            <span class="table-rows-tag">${part.rows}</span>
            <div class="table-hover-actions">
              <button class="table-action-btn run-btn" data-table-id="${part.id}" data-file="${part.file}" data-name="${tbl.name} (${part.name})" title="Consultar partición en DuckDB">▶ SQL</button>
            </div>
          </div>
        `;
      });
    }

    const varianteTag = variante
      ? `<span class="tree-variant-tag" title="${escapeAttr(variante.nota || "")}">${variante.etiqueta || "variante"}</span>`
      : "";
    return `
      <div class="table-node-wrapper">
        <div class="tree-row tree-table ${isSelected} ${variante ? "tree-variant" : ""}" data-table-id="${tbl.id}" data-file="${tbl.file || ''}" data-name="${tbl.name}" data-sector="${circular.sector}">
          <span class="tree-indent-3"></span>
          ${arrowHtml}
          ${ICONS.table}
          <span class="tree-label table-label">${tbl.name}</span>
          ${varianteTag}
          <span class="table-rows-tag"${tbl.nota ? ` title="${tbl.nota.replace(/"/g, "&quot;")}"` : ""}>${tbl.rows}</span>
          <div class="table-hover-actions">
            <button class="table-action-btn run-btn" data-table-id="${tbl.id}" data-file="${tbl.file || ''}" data-name="${tbl.name}" title="Consultar en Terminal DuckDB">▶ SQL</button>
            <button class="table-action-btn inspect-btn" data-table-id="${tbl.id}" title="Inspeccionar esquema">i</button>
          </div>
        </div>
        ${hasPartitions ? `<div class="table-partitions-children" id="${partKey}" style="display: ${isPartOpen ? 'block' : 'none'};">${partHtml}</div>` : ""}
      </div>
    `;
  }

  renderGroup(group, nivel) {
    const A = this.alcance();
    let groupChildrenHtml = "";

    group.children.forEach((sector) => {
      let sectorChildrenHtml = "";

      this.carpetasVisibles(sector).forEach(({ circ: circular, tablas, variantes }) => {
        let tablesHtml = tablas.map((tbl) => this.renderTableRow(tbl, circular, null)).join("");
        tablesHtml += variantes.map(({ tbl, circ }) => this.renderTableRow(tbl, circ, A ? A.variante(tbl.id) : null)).join("");

        const isCircOpen = this.expandedNodes.has(circular.id);
        const circOpenClass = isCircOpen ? "open" : "";
        const circArrow = isCircOpen ? ICONS.chevronDown : ICONS.chevronRight;
        const circPendingAudit = circular.status === "por_auditar";
        const circBadgeClass = circPendingAudit
          ? "badge-por-auditar"
          : (circular.status === "roadmap"
            ? "badge-roadmap"
            : (circular.badgeType === "entities" ? "badge-entities" : "badge-data"));
        const circRoadmapClass = circular.status === "roadmap"
          ? "roadmap-node"
          : (circPendingAudit ? "audit-pending-node" : "");

        sectorChildrenHtml += `
          <div class="tree-node circular-node ${circOpenClass} ${circRoadmapClass}" data-node-id="${circular.id}">
            <div class="tree-row tree-circular" data-circular-id="${circular.id}" data-sector="${circular.sector}">
              <span class="tree-indent-2"></span>
              <span class="arrow-slot">${circArrow}</span>
              ${ICONS.database}
              <span class="tree-label">${circular.label}</span>
              <span class="node-badge ${circBadgeClass}">${circular.badge}</span>
            </div>
            <div class="node-children">
              ${tablesHtml}
            </div>
          </div>
        `;
      });

      const isSectorOpen = this.expandedNodes.has(sector.id);
      const sectorOpenClass = isSectorOpen ? "open" : "";
      const sectorArrow = isSectorOpen ? ICONS.chevronDown : ICONS.chevronRight;

      groupChildrenHtml += `
        <div class="tree-node sector-node ${sectorOpenClass}" data-node-id="${sector.id}">
          <div class="tree-row tree-sector" data-sector-id="${sector.id}" data-sector="${sector.sector}">
            <span class="tree-indent-1"></span>
            <span class="arrow-slot">${sectorArrow}</span>
            ${ICONS.folder}
            <span class="tree-label">${sector.label}</span>
          </div>
          <div class="node-children">
            ${sectorChildrenHtml}
          </div>
        </div>
      `;
    });

    const isGroupOpen = this.expandedNodes.has(group.id);
    const groupOpenClass = isGroupOpen ? "open" : "";
    const groupArrow = isGroupOpen ? ICONS.chevronDown : ICONS.chevronRight;
    const groupRoadmapClass = group.status === "roadmap" ? "roadmap-node" : "";
    const fuera = nivel && !nivel.visible;

    let badgesHtml = "";
    if (fuera) {
      badgesHtml += `<span class="group-badge node-badge badge-nivel badge-nivel-${nivel.id}" title="${escapeAttr(nivel.aviso || nivel.etiqueta)}">${nivel.corta}</span>`;
    }
    if (group.badges && group.badges.length > 0) {
      badgesHtml += group.badges.map((b) => {
        const bClass = b.type === "pending" ? "badge-por-auditar" : (b.type === "entities" ? "badge-entities" : (b.type === "data" ? "badge-data" : "badge-roadmap"));
        return `<span class="group-badge node-badge ${bClass}" title="${b.title || b.text}">${b.text}</span>`;
      }).join("");
    } else if (group.badge) {
      const groupBadgeClass = group.status === "roadmap" ? "badge-roadmap" : "badge-data";
      badgesHtml += `<span class="group-badge node-badge ${groupBadgeClass}">${group.badge}</span>`;
    }

    return `
      <div class="tree-group ${groupOpenClass} ${groupRoadmapClass} ${fuera ? "tree-group-fuera" : ""}" data-group-id="${group.id}"${nivel ? ` data-tier="${nivel.id}"` : ""}>
        <div class="tree-group-header" title="${group.label}">
          <span class="arrow-slot">${groupArrow}</span>
          <span class="group-title">${group.label}</span>
          <div class="group-badges">
            ${badgesHtml}
          </div>
        </div>
        <div class="group-children">
          ${groupChildrenHtml}
        </div>
      </div>
    `;
  }

  // Abre en el explorador el sector pedido (desde la portada u otra vista): despliega su
  // grupo —y el archivo si hace falta—, lo marca como industria activa y lo centra.
  revealSector(sectorKey, source = "portada") {
    const A = window.SIFAlcance;
    const objetivo = A ? A.clave(sectorKey) : String(sectorKey || "");
    for (const group of EXPLORER_TREE) {
      for (const sec of group.children) {
        if ((A ? A.clave(sec.sector) : sec.sector) !== objetivo) continue;
        this.expandedNodes.add(group.id);
        this.expandedNodes.add(sec.id);
        if (this.alcance() && this.alcance().esArchivo(sec.sector)) this.expandedNodes.add(ARCHIVE_NODE);
        this.mostrarBarra();
        if (this.searchInput) this.searchInput.value = "";
        this.render();
        this.setActiveSector(sec.sector, source);
        const erdSec = mapaERD();
        if (erdSec) erdSec.focusSector(sec.sector);
        if (this.breadcrumbEl) this.breadcrumbEl.textContent = this.describeLocation(sec.sector, "");
        const nodo = this.treeContainer ? this.treeContainer.querySelector(`[data-node-id="${sec.id}"]`) : null;
        if (nodo) {
          if (typeof nodo.scrollIntoView === "function") nodo.scrollIntoView({ block: "nearest", behavior: "smooth" });
          nodo.classList.add("tree-flash");
          setTimeout(() => nodo.classList.remove("tree-flash"), 1800);
        }
        return true;
      }
    }
    return false;
  }

  // Abre la sección de archivo y registros complementarios (enlace discreto de la portada).
  openArchive() {
    this.expandedNodes.add(ARCHIVE_NODE);
    this.mostrarBarra();
    if (this.searchInput) this.searchInput.value = "";
    this.render();
    const archivo = this.treeContainer ? this.treeContainer.querySelector(".tree-archive") : null;
    if (archivo && typeof archivo.scrollIntoView === "function") archivo.scrollIntoView({ block: "start", behavior: "smooth" });
    return Boolean(archivo);
  }

  mostrarBarra() {
    if (this.sidebar && this.sidebar.classList.contains("collapsed")) {
      this.sidebar.classList.remove("collapsed");
      setTimeout(() => { const erd = mapaERD(); if (erd) erd.resize(); }, 300);
    }
  }

  bindTreeEvents() {
    // Toolbar: Expandir todo
    const expBtn = document.getElementById("btn-expand-all");
    if (expBtn) {
      expBtn.addEventListener("click", () => {
        document.querySelectorAll(".tree-group, .tree-node").forEach((node) => {
          node.classList.add("open");
          const key = node.dataset.groupId || node.dataset.nodeId;
          if (key) this.expandedNodes.add(key);
          const arrowSlot = node.querySelector(".arrow-slot");
          if (arrowSlot) arrowSlot.innerHTML = ICONS.chevronDown;
        });
        document.querySelectorAll(".table-partitions-children").forEach((el) => {
          this.expandedNodes.add(el.id);
          el.style.display = "block";
          const slot = document.querySelector(`.tbl-arrow-slot[data-target="${el.id}"]`);
          if (slot) slot.innerHTML = ICONS.chevronDown;
        });
      });
    }

    // Toolbar: Colapsar todo
    const colBtn = document.getElementById("btn-collapse-all");
    if (colBtn) {
      colBtn.addEventListener("click", () => {
        this.expandedNodes.clear();
        document.querySelectorAll(".tree-group, .tree-node").forEach((node) => {
          node.classList.remove("open");
          const arrowSlot = node.querySelector(".arrow-slot");
          if (arrowSlot) arrowSlot.innerHTML = ICONS.chevronRight;
        });
        document.querySelectorAll(".table-partitions-children").forEach((el) => {
          el.style.display = "none";
          const slot = document.querySelector(`.tbl-arrow-slot[data-target="${el.id}"]`);
          if (slot) slot.innerHTML = ICONS.chevronRight;
        });
        document.querySelectorAll(".tree-archive").forEach((archivo) => {
          archivo.classList.remove("open");
          const toggle = archivo.querySelector(".tree-archive-toggle");
          if (toggle) toggle.setAttribute("aria-expanded", "false");
          const arrow = archivo.querySelector(".tree-archive-toggle .arrow-slot");
          if (arrow) arrow.innerHTML = ICONS.chevronRight;
        });
      });
    }

    // Archivo y registros complementarios: plegado por defecto, al final del árbol.
    document.querySelectorAll(".tree-archive-toggle").forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const archivo = toggle.closest(".tree-archive");
        const isOpen = archivo.classList.toggle("open");
        this.setNodeExpanded(ARCHIVE_NODE, isOpen);
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        const arrow = toggle.querySelector(".arrow-slot");
        if (arrow) arrow.innerHTML = isOpen ? ICONS.chevronDown : ICONS.chevronRight;
      });
    });

    // Toolbar: Ver todo
    const allBtn = document.getElementById("btn-show-all");
    if (allBtn) {
      allBtn.addEventListener("click", () => {
        this.setActiveSector("todos", "all-industries");
        document.querySelectorAll(".tree-row").forEach((r) => r.classList.remove("selected"));
        if (this.breadcrumbEl) this.breadcrumbEl.textContent = "Vista principal";
        const erdTodos = mapaERD();
        if (erdTodos) erdTodos.focusSector("todos");
        if (window.ChatTerminal) {
          window.ChatTerminal.restoreDefaultChips();
          window.ChatTerminal.addSystemMessage("Vista restablecida: vista principal (núcleo, instituciones y contexto).");
        }
      });
    }

    // Header de Grupo
    document.querySelectorAll(".tree-group-header").forEach((header) => {
      header.addEventListener("click", (e) => {
        const group = e.currentTarget.closest(".tree-group");
        const isOpen = group.classList.toggle("open");
        this.setNodeExpanded(group.dataset.groupId, isOpen);
        const arrow = header.querySelector(".arrow-slot");
        if (arrow) arrow.innerHTML = isOpen ? ICONS.chevronDown : ICONS.chevronRight;
      });
    });

    // Row de Sector
    document.querySelectorAll(".tree-sector").forEach((row) => {
      row.addEventListener("click", (e) => {
        const node = e.currentTarget.closest(".sector-node");
        const isOpen = node.classList.toggle("open");
        this.setNodeExpanded(node.dataset.nodeId, isOpen);
        const arrow = row.querySelector(".arrow-slot");
        if (arrow) arrow.innerHTML = isOpen ? ICONS.chevronDown : ICONS.chevronRight;

        const sector = row.dataset.sector;
        if (sector) this.setActiveSector(sector, "sector");
        if (sector) {
          const erd = mapaERD();
          if (erd) erd.focusSector(sector);
        }
      });
    });

    // Row de Circular
    document.querySelectorAll(".tree-circular").forEach((row) => {
      row.addEventListener("click", (e) => {
        const node = e.currentTarget.closest(".circular-node");
        const isOpen = node.classList.toggle("open");
        this.setNodeExpanded(node.dataset.nodeId, isOpen);
        const arrow = row.querySelector(".arrow-slot");
        if (arrow) arrow.innerHTML = isOpen ? ICONS.chevronDown : ICONS.chevronRight;

        const circId = row.dataset.circularId;
        const sector = row.dataset.sector;
        this.onCircularSelect(circId, sector);
      });
    });

    // Row de Tabla Individual
    document.querySelectorAll(".tree-table").forEach((row) => {
      row.addEventListener("click", (e) => {
        e.stopPropagation();
        const tableId = e.currentTarget.dataset.tableId;
        const tableName = e.currentTarget.dataset.name;
        const file = e.currentTarget.dataset.file;
        const sector = e.currentTarget.dataset.sector;
        this.onTableSelect(tableId, tableName, file, sector);
      });
    });

    // Acciones rapidas en hover de tablas
    document.querySelectorAll(".run-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const name = e.currentTarget.dataset.name;
        // Se consulta la vista semántica registrada en DuckDB-Wasm, no la ruta del
        // archivo: así funcionan también las tablas unidas desde varias particiones.
        const viewId = e.currentTarget.dataset.tableId;
        const file = e.currentTarget.dataset.file;
        if (window.ChatTerminal) {
          const sql = viewId
            ? `SELECT * FROM ${viewId} LIMIT 10;`
            : `SELECT * FROM '${file}' LIMIT 10;`;
          window.ChatTerminal.setQueryInput(sql, name);
          window.ChatTerminal.handleSend();
        }
      });
    });

    document.querySelectorAll(".inspect-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const tableId = e.currentTarget.dataset.tableId;
        const erd = mapaERD();
        if (erd) {
          const node = erd.tables.find((t) => t.id === tableId || t.name === tableId);
          if (node) {
            erd.showSchemaModal(node);
          }
        }
      });
    });

    // Flecha de expansion de particiones de tabla
    document.querySelectorAll(".tbl-arrow-slot").forEach((slot) => {
      slot.addEventListener("click", (e) => {
        e.stopPropagation();
        const targetId = e.currentTarget.dataset.target;
        const partContainer = document.getElementById(targetId);
        if (partContainer) {
          const isHidden = partContainer.style.display === "none";
          partContainer.style.display = isHidden ? "block" : "none";
          this.setNodeExpanded(targetId, isHidden);
          slot.innerHTML = isHidden ? ICONS.chevronDown : ICONS.chevronRight;
        }
      });
    });
  }

  // Ruta legible de la ubicación actual, usada por la barra de contexto del panel.
  describeLocation(sector, tableName) {
    if (!sector || sector === "todos") return "Vista principal";
    const prefijo = this.prefijoNivel(sector);
    for (const grupo of EXPLORER_TREE) {
      for (const sec of grupo.children) {
        if (sec.sector !== sector) continue;
        let circularLabel = "";
        for (const circ of sec.children || []) {
          const tablas = circ.tables || [];
          if (tablas.some((t) => t.name === tableName || t.id === this.selectedTableId)) {
            circularLabel = circ.label;
            break;
          }
        }
        const tablaCorta = tableName && tableName.includes(".") ? tableName.split(".").pop() : tableName;
        return prefijo + [sec.label, circularLabel, tablaCorta].filter(Boolean).join(" \u203a ");
      }
    }
    return tableName || sector;
  }

  // "Archivo › " o "Registro › " para las industrias fuera del foco; vacío en el resto.
  prefijoNivel(sector) {
    const A = this.alcance();
    if (!A || !A.esArchivo(sector)) return "";
    const nivel = A.infoNivelDe(sector);
    return nivel ? `${nivel.corta} \u203a ` : "";
  }

  setNodeExpanded(nodeId, isOpen) {
    if (!nodeId) return;
    if (isOpen) {
      this.expandedNodes.add(nodeId);
    } else {
      this.expandedNodes.delete(nodeId);
    }
  }

  setActiveSector(sector, source = "sidebar") {
    if (!sector) return;
    this.activeSector = String(sector);
    window.MFC_ACTIVE_SECTOR = this.activeSector;
    window.dispatchEvent(new CustomEvent("mfc:industry-change", {
      detail: { sector: this.activeSector, tableId: this.selectedTableId, source }
    }));
  }

  onCircularSelect(circId, sector) {
    let targetCirc = null;
    let targetSectorName = "";
    let targetGroupName = "";

    for (const grp of EXPLORER_TREE) {
      for (const sec of grp.children) {
        for (const circ of sec.children) {
          if (circ.id === circId) {
            targetCirc = circ;
            targetSectorName = sec.label;
            targetGroupName = grp.label;
            break;
          }
        }
      }
    }

    if (!targetCirc) return;
    this.setActiveSector(sector, "circular");

    if (this.breadcrumbEl) {
      this.breadcrumbEl.textContent = `${this.prefijoNivel(sector)}${targetSectorName} \u203a ${targetCirc.label}`;
    }

    const erdCircular = mapaERD();
    if (erdCircular) {
      erdCircular.focusSector(sector);
    }

    const chips = this.chipsDeCarpeta(circId) || targetCirc.chips;
    if (window.ChatTerminal && chips) {
      window.ChatTerminal.setCustomChips(chips, `${this.prefijoNivel(sector)}${targetSectorName} · ${targetCirc.label}`);
    }

    // Sincronizar automáticamente el Visor de Datos con la primera tabla visible de la circular
    const A = this.alcance();
    const visibles = (targetCirc.tables || []).filter((t) => !A || !A.tablaOculta(t.id));
    if (visibles.length > 0) {
      const primary = visibles[0];
      this.onTableSelect(primary.id, primary.name, primary.file, sector);
    }
  }

  onTableSelect(tableId, tableName, file, sector) {
    this.selectedTableId = tableId;
    this.setActiveSector(sector, "table");

    // Actualizar clase seleccionada en la fila del arbol
    document.querySelectorAll(".tree-table").forEach((el) => {
      el.classList.toggle("selected", el.dataset.tableId === tableId);
    });

    // Actualizar la barra de contexto del panel
    if (this.breadcrumbEl) {
      this.breadcrumbEl.textContent = this.describeLocation(sector, tableName);
      this.breadcrumbEl.title = `Ubicación actual: ${this.breadcrumbEl.textContent}`;
    }

    // Enfocar y centrar la tabla en el Canvas ERD
    const erdTabla = mapaERD();
    if (erdTabla) {
      erdTabla.focusTable(tableId);
    }

    // Sincronizar con el Visor de Datos
    if (window.DataViewer) {
      window.DataViewer.loadTable(tableId, tableName);
    }

    // Cargar consulta automatica en el chat/terminal usando vista semántica
    if (window.ChatTerminal) {
      const defaultSql = `SELECT * FROM ${tableId} LIMIT 10;`;
      window.ChatTerminal.setQueryInput(defaultSql, tableName);
    }
  }

  filterTree(query) {
    if (!query) {
      document.querySelectorAll(".tree-group, .tree-node, .tree-table, .tree-tier, .tree-archive").forEach((el) => {
        el.style.display = "";
      });
      document.querySelectorAll(".tree-archive").forEach((el) => el.classList.remove("search-open"));
      return;
    }

    document.querySelectorAll(".tree-group").forEach((group) => {
      let groupHasMatch = false;

      group.querySelectorAll(".sector-node").forEach((sectorNode) => {
        let sectorHasMatch = false;

        sectorNode.querySelectorAll(".circular-node").forEach((circNode) => {
          let circHasMatch = false;

          circNode.querySelectorAll(".tree-table").forEach((tblRow) => {
            const name = tblRow.dataset.name.toLowerCase();
            if (name.includes(query)) {
              tblRow.style.display = "flex";
              circHasMatch = true;
            } else {
              tblRow.style.display = "none";
            }
          });

          const circTitle = circNode.querySelector(".tree-circular .tree-label").textContent.toLowerCase();
          if (circHasMatch || circTitle.includes(query)) {
            if (circTitle.includes(query)) {
              circNode.querySelectorAll(".tree-table").forEach((table) => { table.style.display = "flex"; });
            }
            circNode.style.display = "block";
            circNode.classList.add("open");
            const arrow = circNode.querySelector(".tree-circular .arrow-slot");
            if (arrow) arrow.innerHTML = ICONS.chevronDown;
            sectorHasMatch = true;
          } else {
            circNode.style.display = "none";
          }
        });

        const sectorTitle = sectorNode.querySelector(".tree-sector .tree-label").textContent.toLowerCase();
        if (sectorTitle.includes(query)) {
          sectorNode.querySelectorAll(".circular-node, .tree-table").forEach((node) => {
            node.style.display = node.classList.contains("tree-table") ? "flex" : "";
          });
          sectorNode.querySelectorAll(".circular-node").forEach((node) => {
            node.classList.add("open");
            const arrow = node.querySelector(".arrow-slot");
            if (arrow) arrow.innerHTML = ICONS.chevronDown;
          });
        }
        if (sectorHasMatch || sectorTitle.includes(query)) {
          sectorNode.style.display = "block";
          sectorNode.classList.add("open");
          const arrow = sectorNode.querySelector(".tree-sector .arrow-slot");
          if (arrow) arrow.innerHTML = ICONS.chevronDown;
          groupHasMatch = true;
        } else {
          sectorNode.style.display = "none";
        }
      });

      const groupTitle = group.querySelector(".group-title").textContent.toLowerCase();
      if (groupTitle.includes(query)) {
        // Si se busca la familia, mostrar todos sus subsectores y categorías.
        group.querySelectorAll(".sector-node, .circular-node, .tree-table").forEach((node) => {
          node.style.display = node.classList.contains("tree-table") ? "flex" : "";
        });
        group.querySelectorAll(".sector-node, .circular-node").forEach((node) => {
          node.classList.add("open");
          const arrow = node.querySelector(".arrow-slot");
          if (arrow) arrow.innerHTML = ICONS.chevronDown;
        });
      }
      if (groupHasMatch || groupTitle.includes(query)) {
        group.style.display = "block";
        group.classList.add("open");
        const arrow = group.querySelector(".tree-group-header .arrow-slot");
        if (arrow) arrow.innerHTML = ICONS.chevronDown;
      } else {
        group.style.display = "none";
      }
    });

    // Niveles sin coincidencias se ocultan; el archivo se abre solo si tiene alguna.
    const conCoincidencias = (contenedor) => Array.from(contenedor.querySelectorAll(".tree-group"))
      .some((group) => group.style.display !== "none");
    document.querySelectorAll(".tree-tier").forEach((tier) => {
      tier.style.display = conCoincidencias(tier) ? "" : "none";
    });
    document.querySelectorAll(".tree-archive").forEach((archivo) => {
      const hay = conCoincidencias(archivo);
      archivo.classList.toggle("search-open", hay);
      archivo.style.display = hay ? "" : "none";
    });
  }
}

window.SidebarController = SidebarController;

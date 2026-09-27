/**
 * Explorer Tree Controller (Patron DBeaver / Supabase Studio / VS Code)
 * Monitor Financiero Chile
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
      { type: "entities", text: "103 Entidades", title: "103 Compañías de Seguros reguladas (61 Vida + 42 Generales)" },
      { type: "data", text: "12.5M Datos", title: "12.5M Registros históricos de carteras e inversiones CMF 1835" }
    ],
    status: "active",
    children: [
      {
        id: "sector_vida",
        type: "sector",
        label: "Seguros de Vida",
        sector: "vida",
        children: [
          {
            id: "cat_vida_aseguradoras",
            type: "circular",
            label: "Lista de Entidades",
            badge: "61 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "vida",
            chips: [
              { label: "Aseguradoras de Vida Activas", query: "SELECT rut_aseguradora, nombre_aseguradora, ultimo_periodo, inversion_ultimo_reporte_m_clp FROM vida_maestro WHERE estado = 'Activa' ORDER BY inversion_ultimo_reporte_m_clp DESC;" },
              { label: "Ranking Inversiones Vida (M$)", query: "SELECT nombre_aseguradora, inversion_ultimo_reporte_m_clp, patrimonio_ultimo_reporte_m_clp FROM vida_maestro ORDER BY inversion_ultimo_reporte_m_clp DESC LIMIT 10;" },
              { label: "Historial de Reportes por Aseguradora", query: "SELECT nombre_aseguradora, primer_periodo, ultimo_periodo, periodos_reportados, estado FROM vida_maestro ORDER BY periodos_reportados DESC LIMIT 10;" }
            ],
            tables: [
              { id: "vida_maestro", name: "vida.lista_entidades", rows: "61 entidades", file: "outputs/vida/maestro_aseguradoras_vida.parquet" }
            ]
          },
          {
            id: "c1835_vida_cartera",
            type: "circular",
            label: "Circular 1835 · Cartera",
            badge: "11,59 M Registros",
            badgeType: "data",
            status: "active",
            sector: "vida",
            chips: [
              { label: "Top 5 Bonos Vida", query: "SELECT nemotecnico, tipo_bono, AVG(tir_mercado_pct) as tir_prom, count(*) as tenencias FROM vida_bonos GROUP BY nemotecnico, tipo_bono ORDER BY tenencias DESC LIMIT 5;" },
              { label: "Inmuebles por Comuna (Vida)", query: "SELECT comuna, count(*) as propiedades, SUM(tasacion_comercial_m_clp) as tasacion_total_m FROM vida_bienes_raices GROUP BY comuna ORDER BY propiedades DESC LIMIT 5;" },
              { label: "Acciones IPSA en Vida", query: "SELECT nemotecnico, AVG(precio_cierre_clp) as precio_promedio, AVG(presencia_pct) as presencia FROM vida_acciones WHERE nemotecnico IN ('CHILE', 'BCI', 'BSANTANDER', 'SQM-B', 'CMPC') GROUP BY nemotecnico;" },
              { label: "Activos Extranjeros (Vida)", query: "SELECT gestora_fondo, moneda, count(*) as fondos FROM vida_extranjeros GROUP BY gestora_fondo, moneda ORDER BY fondos DESC LIMIT 5;" }
            ],
            tables: [
              {
                id: "vida_bonos",
                name: "vida.cartera_bonos",
                rows: "9,09 M registros",
                // El Parquet consolidado (9,09M filas) supera el límite de 100 MB de GitHub
                // y no está versionado: la vista vida_bonos se arma con las dos particiones.
                files: [
                  "outputs/vida/cartera_bonos_2021_2024.parquet",
                  "outputs/vida/cartera_bonos_2016_2020.parquet"
                ],
                partitions: [
                  { id: "vida_bonos_reciente", name: "2021-2026 · Tramo reciente", rows: "4,00 M registros", file: "outputs/vida/cartera_bonos_2021_2024.parquet" },
                  { id: "vida_bonos_historico", name: "2016-2020 · Tramo histórico", rows: "5,08 M registros", file: "outputs/vida/cartera_bonos_2016_2020.parquet" }
                ]
              },
              { id: "vida_bienes_raices", name: "vida.cartera_bienes_raices", rows: "2,01 M registros", file: "outputs/vida/cartera_bienes_raices.parquet" },
              { id: "vida_extranjeros", name: "vida.cartera_extranjeros", rows: "146.365 registros", file: "outputs/vida/cartera_extranjeros.parquet" },
              { id: "vida_acciones", name: "vida.cartera_acciones", rows: "142.944 registros", file: "outputs/vida/cartera_acciones.parquet" },
              { id: "vida_fondos", name: "vida.cartera_fondos", rows: "76.902 registros", file: "outputs/vida/cartera_fondos.parquet" },
              { id: "vida_solvencia", name: "vida.cartera_solvencia", rows: "126.586 registros", file: "outputs/vida/cartera_solvencia.parquet" }
            ]
          },
          {
            id: "c1835_vida_derivados",
            type: "circular",
            label: "Circular 1835 · Derivados",
            badge: "482.710 Registros",
            badgeType: "data",
            status: "active",
            sector: "vida",
            chips: [
              { label: "Forwards Vida: Contrapartes", query: "SELECT nombre_contraparte, count(*) as contratos, AVG(precio_forward_pactado) as fwd_pactado FROM vida_forwards GROUP BY nombre_contraparte ORDER BY contratos DESC LIMIT 5;" },
              { label: "Swaps Vida: Tasas y MtM", query: "SELECT nombre_contraparte, count(*) as operaciones, AVG(tasa_contrato_larga) as tasa_larga, AVG(valor_razonable_mtm_m_clp) as mtm_prom FROM vida_swaps GROUP BY nombre_contraparte ORDER BY operaciones DESC LIMIT 5;" },
              { label: "Opciones Financieras Vida", query: "SELECT tipo_opcion, count(*) as contratos, AVG(precio_ejercicio) as precio_ejercicio_prom FROM vida_opciones GROUP BY tipo_opcion;" }
            ],
            tables: [
              { id: "vida_swaps", name: "vida.derivados_swaps", rows: "314.683 registros", file: "outputs/vida/b7_swaps.parquet" },
              { id: "vida_forwards", name: "vida.derivados_forwards", rows: "165.354 registros", file: "outputs/vida/b7_forwards.parquet" },
              { id: "vida_opciones", name: "vida.derivados_opciones", rows: "2.673 registros", file: "outputs/vida/b7_opciones.parquet" }
            ]
          },
          {
            id: "c1835_vida_repos",
            type: "circular",
            label: "Circular 1835 · Pactos y Repos",
            badge: "19.408 Registros",
            badgeType: "data",
            status: "active",
            sector: "vida",
            chips: [
              { label: "Repos Vida: Tasas y Contrapartes", query: "SELECT nombre_contraparte, count(*) as pactos, AVG(tasa_pacto) as tasa_prom, SUM(monto_pacto_m_clp) as monto_total_m FROM vida_repos GROUP BY nombre_contraparte ORDER BY pactos DESC LIMIT 5;" },
              { label: "Repos Vida: Tasa Pacto vs Mercado", query: "SELECT periodo, AVG(tasa_pacto) as tasa_pacto_prom, AVG(tasa_mercado) as tasa_mercado_prom FROM vida_repos GROUP BY periodo ORDER BY periodo DESC LIMIT 5;" }
            ],
            tables: [
              { id: "vida_repos", name: "vida.pactos_repos", rows: "19.408 registros", file: "outputs/vida/b7_repos.parquet" }
            ]
          }
        ]
      },
      {
        id: "sector_generales",
        type: "sector",
        label: "Seguros Generales",
        sector: "generales",
        children: [
          {
            id: "cat_gen_aseguradoras",
            type: "circular",
            label: "Lista de Entidades",
            badge: "42 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "generales",
            chips: [
              { label: "Aseguradoras Generales Activas", query: "SELECT rut_aseguradora, nombre_aseguradora, ultimo_periodo, inversion_ultimo_reporte_m_clp FROM generales_maestro WHERE estado = 'Activa' ORDER BY inversion_ultimo_reporte_m_clp DESC;" },
              { label: "Ranking Inversiones Generales (M$)", query: "SELECT nombre_aseguradora, inversion_ultimo_reporte_m_clp, patrimonio_ultimo_reporte_m_clp FROM generales_maestro ORDER BY inversion_ultimo_reporte_m_clp DESC LIMIT 10;" },
              { label: "Historial de Reportes Generales", query: "SELECT nombre_aseguradora, primer_periodo, ultimo_periodo, periodos_reportados, estado FROM generales_maestro ORDER BY periodos_reportados DESC LIMIT 10;" }
            ],
            tables: [
              { id: "generales_maestro", name: "generales.lista_entidades", rows: "42 entidades", file: "outputs/generales/maestro_aseguradoras_generales.parquet" }
            ]
          },
          {
            id: "c1835_gen_cartera",
            type: "circular",
            label: "Circular 1835 · Cartera",
            badge: "417.303 Registros",
            badgeType: "data",
            status: "active",
            sector: "generales",
            chips: [
              { label: "Bonos Seguros Generales", query: "SELECT tipo_bono, count(*) as tenencias, AVG(tir_mercado_pct) as tir_prom FROM generales_bonos GROUP BY tipo_bono ORDER BY tenencias DESC LIMIT 5;" },
              { label: "Inmuebles Seguros Generales", query: "SELECT comuna, count(*) as inmuebles, SUM(tasacion_comercial_m_clp) as tasacion_m FROM generales_bienes_raices GROUP BY comuna ORDER BY inmuebles DESC LIMIT 5;" },
              { label: "Acciones Seguros Generales", query: "SELECT nemotecnico, count(*) as tenencias, AVG(precio_cierre_clp) as precio_prom FROM generales_acciones GROUP BY nemotecnico ORDER BY tenencias DESC LIMIT 5;" },
              { label: "Solvencia y Balance Generales", query: "SELECT periodo, SUM(total_inversion_m_clp) as total_inversion_m FROM generales_solvencia GROUP BY periodo ORDER BY periodo DESC LIMIT 5;" }
            ],
            tables: [
              { id: "generales_bonos", name: "generales.cartera_bonos", rows: "287.214 registros", file: "outputs/generales/cartera_bonos.parquet" },
              { id: "generales_bienes_raices", name: "generales.cartera_bienes_raices", rows: "38.257 registros", file: "outputs/generales/cartera_bienes_raices.parquet" },
              { id: "generales_acciones", name: "generales.cartera_acciones", rows: "17.457 registros", file: "outputs/generales/cartera_acciones.parquet" },
              { id: "generales_fondos", name: "generales.cartera_fondos", rows: "8.935 registros", file: "outputs/generales/cartera_fondos.parquet" },
              { id: "generales_extranjeros", name: "generales.cartera_extranjeros", rows: "5.590 registros", file: "outputs/generales/cartera_extranjeros.parquet" },
              { id: "generales_solvencia", name: "generales.cartera_solvencia", rows: "59.850 registros", file: "outputs/generales/cartera_solvencia.parquet" }
            ]
          },
          {
            id: "c1835_gen_derivados",
            type: "circular",
            label: "Circular 1835 · Derivados",
            badge: "4.270 Registros",
            badgeType: "data",
            status: "active",
            sector: "generales",
            chips: [
              { label: "Forwards Generales: Contrapartes", query: "SELECT nombre_contraparte, count(*) as contratos, AVG(precio_forward_pactado) as fwd_pactado FROM generales_forwards GROUP BY nombre_contraparte ORDER BY contratos DESC LIMIT 5;" },
              { label: "Swaps Generales: Tasas y MtM", query: "SELECT nombre_contraparte, count(*) as operaciones, AVG(tasa_contrato_larga) as tasa_larga FROM generales_swaps GROUP BY nombre_contraparte ORDER BY operaciones DESC LIMIT 5;" }
            ],
            tables: [
              { id: "generales_forwards", name: "generales.derivados_forwards", rows: "2.847 registros", file: "outputs/generales/b7_forwards.parquet" },
              { id: "generales_swaps", name: "generales.derivados_swaps", rows: "1.423 registros", file: "outputs/generales/b7_swaps.parquet" }
            ]
          },
          {
            id: "c1835_gen_repos",
            type: "circular",
            label: "Circular 1835 · Pactos y Repos",
            badge: "275 Registros",
            badgeType: "data",
            status: "active",
            sector: "generales",
            chips: [
              { label: "Repos Generales: Pactos y Tasas", query: "SELECT nombre_contraparte, count(*) as pactos, AVG(tasa_pacto) as tasa_prom FROM generales_repos GROUP BY nombre_contraparte ORDER BY pactos DESC LIMIT 5;" }
            ],
            tables: [
              { id: "generales_repos", name: "generales.pactos_repos", rows: "275 registros", file: "outputs/generales/b7_repos.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_administracion_fondos",
    type: "group",
    label: "ADMINISTRACIÓN DE FONDOS (CMF / LEY 20.712)",
    badges: [
      { type: "entities", text: "AGF · FFMM · FI", title: "Sociedades administradoras y fondos son unidades jurídicas y contables distintas" }
    ],
    status: "active",
    children: [
      {
        id: "sector_agf",
        type: "sector",
        label: "Administradoras Generales de Fondos (AGF)",
        sector: "agf",
        children: [
          {
            id: "cat_agf_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "68 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "agf",
            chips: [
              { label: "Catálogo de AGF (Vigentes vs Canceladas)", query: "SELECT rut_completo, razon_social, estado_vigencia, grupo_controlador, fondos_inversion_administrados FROM agf_maestro ORDER BY estado_vigencia, razon_social;" },
              { label: "Ranking de AGF por Fondos de Inversión Administrados", query: "SELECT razon_social, grupo_controlador, fondos_inversion_administrados, cmf_url FROM agf_maestro WHERE fondos_inversion_administrados > 0 ORDER BY fondos_inversion_administrados DESC LIMIT 15;" },
              { label: "AGF por Grupo Financiero Controlador", query: "SELECT grupo_controlador, count(*) as cantidad_agf, sum(fondos_inversion_administrados) as total_fondos FROM agf_maestro WHERE estado_vigencia = 'Vigente' GROUP BY grupo_controlador ORDER BY total_fondos DESC;" }
            ],
            tables: [
              { id: "agf_maestro", name: "agf.lista_administradoras", rows: "68 entidades", file: "outputs/agf/agf_maestro.parquet" }
            ]
          },
          {
            id: "circ_agf_balances",
            type: "circular",
            label: "Balances y Resultados (IFRS)",
            badge: "1.572 Balances",
            badgeType: "data",
            status: "active",
            sector: "agf",
            chips: [
              { label: "Ranking Activos Propios de las Gestoras (MM$ CLP)", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, efectivo_y_equivalentes_m_clp, cartera_propia_inversiones_m_clp FROM agf_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM agf_balance_resumen) ORDER BY total_activos_m_clp DESC LIMIT 15;" },
              { label: "Ingresos por Comisiones de Administración (Top 10 AGF)", query: "SELECT periodo, razon_social, ingresos_comisiones_m_clp, ganancia_perdida_ejercicio_m_clp, patrimonio_neto_m_clp FROM agf_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM agf_balance_resumen) ORDER BY ingresos_comisiones_m_clp DESC LIMIT 10;" },
              { label: "Cartera Propia de Inversión (Coinversión AGF)", query: "SELECT periodo, razon_social, cartera_propia_inversiones_m_clp, total_activos_m_clp, round(cartera_propia_inversiones_m_clp / NULLIF(total_activos_m_clp, 0) * 100, 1) as pct_cartera_propia FROM agf_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM agf_balance_resumen) AND cartera_propia_inversiones_m_clp > 0 ORDER BY cartera_propia_inversiones_m_clp DESC LIMIT 15;" },
              { label: "Utilidad Neta del Ejercicio: Banchile vs Santander vs LarrainVial", query: "SELECT periodo, razon_social, ganancia_perdida_ejercicio_m_clp, ingresos_comisiones_m_clp, total_activos_m_usd FROM agf_balance_resumen WHERE razon_social LIKE '%BANCHILE%' OR razon_social LIKE '%SANTANDER%' OR razon_social LIKE '%LARRAIN%' ORDER BY periodo DESC, ingresos_comisiones_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "agf_balance_resumen", name: "agf.balance_resumen", rows: "1.572 balances", file: "outputs/agf/agf_balance_resumen.parquet" }
            ]
          }
        ]
      },
      {
        id: "sector_ffmm",
        type: "sector",
        label: "Fondos Mutuos (FFMM)",
        sector: "ffmm",
        children: [
          {
            id: "c1333_ffmm_cat",
            type: "circular",
            label: "Lista de Entidades",
            badge: "1.156 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Listado de Fondos Mutuos", query: "SELECT run_fondo, nombre_fondo, sector FROM ffmm_maestro ORDER BY nombre_fondo LIMIT 10;" }
            ],
            tables: [
              { id: "ffmm_maestro", name: "ffmm.lista_entidades", rows: "1.156 entidades", file: "ffmm/circular_1333_cartera/outputs/maestro_fondos_mutuos.parquet" }
            ]
          },
          {
            id: "c1333_ffmm",
            type: "circular",
            label: "Circular 1333 · Derivados",
            badge: "285.841 Registros",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Futuros Circular 1333", query: "SELECT * FROM ffmm_futuros LIMIT 10;" },
              { label: "Opciones Circular 1333", query: "SELECT * FROM ffmm_opciones LIMIT 10;" }
            ],
            tables: [
              { id: "ffmm_futuros", name: "ffmm.derivados_futuros", rows: "280.494 registros", file: "ffmm/circular_1333_cartera/outputs/ffmm_futu_normalizado.parquet" },
              { id: "ffmm_opciones", name: "ffmm.derivados_opciones", rows: "5.347 registros", file: "ffmm/circular_1333_cartera/outputs/ffmm_opci_normalizado.parquet" }
            ]
          },
          {
            id: "ffmm_eeff_xml_muestra_cmf_folder",
            type: "circular",
            label: "Estados financieros XML · Muestra cotejada CMF",
            badge: "1 fondo · 2014-12",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            chips: [
              { label: "Ver balance y resultado cotejados (miles de pesos)", query: "SELECT run_fondo, periodo, nombre_xml_historico, nombre_registro_actual, unidad_segun_ficha_cmf, total_activo, pasivo_sin_patrimonio, patrimonio_o_activo_neto, resultado_ejercicio, fuente_ficha_cmf FROM ffmm_eeff_xml_muestra_cmf;" }
            ],
            tables: [
              { id: "ffmm_eeff_xml_muestra_cmf", name: "ffmm.eeff_xml_muestra_cmf", rows: "1 fila cotejada · no es histórico", file: "outputs/ffmm/ffmm_eeff_xml_muestra_cmf.parquet" }
            ]
          },
          {
            id: "repos_ffmm_historico",
            type: "circular",
            label: "Operaciones REPO · Muestra en revisión",
            badge: "⚠ Falta auditar",
            badgeType: "data",
            status: "por_auditar",
            sector: "ffmm",
            chips: [
              { label: "Registros Extraídos por Año (muestra sin auditar)", query: "SELECT periodo, count(*) as registros, count(distinct run_fondo) as fondos FROM ffmm_repos_detalle_historico GROUP BY periodo ORDER BY periodo DESC;" },
              { label: "Campos Incompletos de la Extracción", query: "SELECT periodo, count(*) as registros, count(*) FILTER (WHERE fecha_vencimiento IS NULL OR fecha_vencimiento IN ('', 'NA')) as sin_vencimiento, count(*) FILTER (WHERE nemotecnico IS NULL OR nemotecnico IN ('', 'NA')) as sin_nemotecnico FROM ffmm_repos_detalle_historico GROUP BY periodo ORDER BY periodo DESC;" },
              { label: "Detalle de Contratos (muestra sin auditar)", query: "SELECT periodo, run_fondo, nombre_fondo, fecha_compra, nombre_contraparte, nemotecnico, total_transado_m_clp, fecha_vencimiento, saldo_al_cierre_m_clp, pagina_pdf FROM ffmm_repos_detalle_historico ORDER BY periodo DESC, run_fondo LIMIT 25;" }
            ],
            tables: [
              { id: "ffmm_repos_detalle_historico", name: "ffmm.repos_contratos", rows: "388 contratos", file: "outputs/ffmm/ffmm_repos_detalle_historico.parquet" }
            ]
          }
        ]
      },
      {
        id: "sector_fi",
        type: "sector",
        label: "Fondos de Inversión (Públicos y Privados)",
        sector: "fi",
        children: [
          {
            id: "fi_cat_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "1.129 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "fi",
            chips: [
              { label: "Listado de Fondos de Inversión", query: "SELECT run_fondo, nombre_fondo, tipo_entidad_desc, administradora FROM fi_maestro ORDER BY nombre_fondo LIMIT 15;" },
              { label: "Fondos por Administradora", query: "SELECT administradora, count(*) as total_fondos FROM fi_maestro GROUP BY administradora ORDER BY total_fondos DESC LIMIT 10;" }
            ],
            tables: [
              { id: "fi_maestro", name: "fi.lista_entidades", rows: "1.129 entidades", file: "fi/cartera_inversiones/outputs/maestro_fondos_inversion.parquet" }
            ]
          },
          {
            id: "fi_cat_censo",
            type: "circular",
            label: "Universo de Fondos · Registro CMF",
            badge: "1.677 Fondos",
            badgeType: "data",
            status: "active",
            sector: "fi",
            chips: [
              { label: "Vigentes vs Liquidados (Registro CMF)", query: "SELECT estado_vigencia, tipo_entidad_desc, count(*) as total_fondos FROM fi_registro_fondos_universo GROUP BY estado_vigencia, tipo_entidad_desc;" },
              { label: "Fondos Rescatables vs No Rescatables", query: "SELECT tipo_entidad_desc, count(*) as total FROM fi_registro_fondos_universo GROUP BY tipo_entidad_desc;" },
              { label: "Directorio de Fondos Vigentes", query: "SELECT run_fondo, nombre_fondo, tipo_entidad_desc, administradora FROM fi_registro_fondos_universo WHERE estado_vigencia = 'Vigente' ORDER BY nombre_fondo LIMIT 15;" }
            ],
            tables: [
              { id: "fi_registro_fondos_universo", name: "fi.universo_fondos", rows: "1.677 fondos", file: "outputs/fi/fi_registro_fondos_universo.parquet" }
            ]
          },
          {
            id: "fi_eeff_xml_muestra_cmf_folder",
            type: "circular",
            label: "Estados financieros XML · Muestra cotejada CMF",
            badge: "1 fondo · 2021-12",
            badgeType: "data",
            status: "active",
            sector: "fi",
            chips: [
              { label: "Ver balance y resultado cotejados (miles de dólares)", query: "SELECT run_fondo, periodo, nombre_xml_historico, nombre_registro_actual, unidad_segun_ficha_cmf, total_activo, pasivo_sin_patrimonio, patrimonio_o_activo_neto, resultado_ejercicio, fuente_ficha_cmf FROM fi_eeff_xml_muestra_cmf;" }
            ],
            tables: [
              { id: "fi_eeff_xml_muestra_cmf", name: "fi.eeff_xml_muestra_cmf", rows: "1 fila cotejada · no es histórico", file: "outputs/fi/fi_eeff_xml_muestra_cmf.parquet" }
            ]
          },
          {
            id: "fi_repos_historico",
            type: "circular",
            label: "Operaciones REPO · Muestra en revisión",
            badge: "⚠ Falta auditar",
            badgeType: "data",
            status: "por_auditar",
            sector: "fi",
            chips: [
              { label: "Operaciones REPO por Tipo (VRC vs CRV)", query: "SELECT codigo_operacion, tipo_operacion_desc, count(*) as contratos, round(sum(valorizacion_cierre_m_moneda), 2) as saldo_cierre FROM fi_repos_detalle_historico GROUP BY codigo_operacion, tipo_operacion_desc;" },
              { label: "Registros Extraídos por Año (muestra sin auditar)", query: "SELECT anio, count(*) as registros, count(distinct run_fondo) as fondos FROM fi_repos_detalle_historico GROUP BY anio ORDER BY anio DESC;" },
              { label: "Campos Incompletos de la Extracción", query: "SELECT anio, count(*) as registros, count(*) FILTER (WHERE tasa_pct IS NULL) as sin_tasa, count(*) FILTER (WHERE nombre_contraparte IS NULL OR nombre_contraparte IN ('', 'NA')) as sin_contraparte FROM fi_repos_detalle_historico GROUP BY anio ORDER BY anio DESC;" }
            ],
            tables: [
              { id: "fi_repos_detalle_historico", name: "fi.repos_contratos", rows: "2.946 contratos", file: "outputs/fi/fi_repos_detalle_historico.parquet" },
              { id: "fi_repos", name: "fi.repos_vrc_crv", rows: "1.366 pactos", file: "fi/repos/outputs/fi_repos_vrc_crv.parquet" }
            ]
          },
          {
            id: "luf_cartera_fi",
            type: "circular",
            label: "Cartera de Inversión",
            badge: "920.414 Registros",
            badgeType: "data",
            status: "active",
            sector: "fi",
            chips: [
              { label: "Top Inversiones Nacionales", query: "SELECT nemotecnico, rut_emisor, sum(valolizacion_al_cierre) as total_m FROM fi_nacional GROUP BY nemotecnico, rut_emisor ORDER BY total_m DESC LIMIT 10;" },
              { label: "Top Inversiones Extranjeras", query: "SELECT nemotecnico, nombre_del_emisor, sum(valolizacion_al_cierre) as total_m FROM fi_extranjera GROUP BY nemotecnico, nombre_del_emisor ORDER BY total_m DESC LIMIT 10;" },
              { label: "Derivados Forwards FFII", query: "SELECT nombre_contraparte, count(*) as contratos FROM fi_derivados GROUP BY nombre_contraparte ORDER BY contratos DESC LIMIT 10;" }
            ],
            tables: [
              { id: "fi_nacional", name: "fi.cartera_nacional", rows: "833.584 registros", file: "fi/cartera_inversiones/outputs/fi_cartera_nacional.parquet" },
              { id: "fi_extranjera", name: "fi.cartera_extranjera", rows: "67.371 registros", file: "fi/cartera_inversiones/outputs/fi_cartera_extranjera.parquet" },
              { id: "fi_derivados", name: "fi.derivados_futuros", rows: "3.611 registros", file: "fi/cartera_inversiones/outputs/fi_futuros_forward.parquet" },
              { id: "fi_metodo_part", name: "fi.metodo_participacion", rows: "14.401 registros", file: "fi/cartera_inversiones/outputs/fi_metodo_participacion.parquet" },
              { id: "fi_opciones", name: "fi.derivados_opciones", rows: "1.447 registros", file: "fi/cartera_inversiones/outputs/fi_opciones.parquet" }
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
      { type: "entities", text: "7 Entidades", title: "Lista local de AFP; verificar identidad y vigencia contra la SP" }
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
            id: "cat_afp_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "7 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "afp_corporativo",
            chips: [
              { label: "Identificación de administradoras", query: "SELECT rut_administradora, nombre_administradora, nombre_fantasia FROM afp_maestro ORDER BY nombre_fantasia;" }
            ],
            tables: [
              { id: "afp_maestro", name: "afp.lista_administradoras", rows: "7 entidades", file: "outputs/pensiones/afp_maestro_administradoras.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_bancos",
    type: "group",
    label: "BANCA E INST. FINANCIERAS (CMF)",
    badges: [
      { type: "entities", text: "40 Códigos", title: "Catálogo local: incluye instituciones históricas, filiales y agregados; cotejo registral pendiente" },
      { type: "data", text: "REPO · Saldos cotejados", title: "Saldos CLP: 2.947 filas y 220 meses cotejados con B1 CMF; FX 220/220 con SII. RUT, nombres, perímetro y total_transado no están aprobados." }
    ],
    status: "active",
    children: [
      {
        id: "sector_bancos_comercial",
        type: "sector",
        label: "Banca Comercial e Instituciones Supervisadas",
        sector: "bancos",
        children: [
          {
            id: "cat_bancos_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "40 Códigos",
            badgeType: "entities",
            status: "active",
            sector: "bancos",
            chips: [
              { label: "Identificación de instituciones", query: "SELECT codigo_institucion, rut, razon_social, nombre_fantasia FROM bancos_maestro ORDER BY codigo_institucion;" }
            ],
            tables: [
              { id: "bancos_maestro", name: "bancos.lista_instituciones", rows: "40 códigos", file: "outputs/bancos/bancos_maestro.parquet" }
            ]
          },
          {
            id: "circ_bancos_repos",
            type: "circular",
            label: "Saldos REPO · Cotejados con CMF",
            badge: "Saldos cotejados",
            badgeType: "data",
            status: "active",
            sector: "bancos",
            chips: [
              { label: "Muestra de saldos (no flujo ni RUT histórico)", query: "SELECT periodo, codigo_institucion, repo_activo_mm_clp, repo_pasivo_mm_clp, repo_neto_mm_clp FROM bancos_repos_saldos_series ORDER BY periodo DESC LIMIT 25;" }
            ],
            tables: [
              { id: "bancos_repos_saldos_series", name: "bancos.repos_saldos_series", rows: "2.947 registros", file: "outputs/bancos/bancos_repos_saldos_series.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_macro",
    type: "group",
    label: "MACROECONOMIA & TASAS (BCCh)",
    badges: [
      { type: "entities", text: "1 Entidad", title: "Series canónicas oficiales del Banco Central de Chile" },
      { type: "data", text: "459 Datos", title: "Historial mensual y métricas consolidadas (2014 a 2026)" }
    ],
    status: "active",
    children: [
      {
        id: "sector_macro_general",
        type: "sector",
        label: "Estadísticas Financieras y Macroeconómicas",
        sector: "macro",
        children: [
          {
            id: "circ_macro_tasas",
            type: "circular",
            label: "Tasas de Interés y Curvas Soberanas",
            badge: "153 Registros",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "Curva Rendimiento BCP vs BCU (Spread 10y-2y)", query: "SELECT periodo, tpm, tib_promedio, bcp_2y, bcp_5y, bcp_10y, bcu_5y, bcu_10y, spread_bcp_10y_2y_bps, inflacion_implicita_5y_breakeven FROM macro_tasas_rendimientos ORDER BY periodo DESC LIMIT 12;" },
              { label: "Evolución TPM vs Tasa Interbancaria (ICP)", query: "SELECT periodo, tpm, tib_promedio, round(tpm - tib_promedio, 3) as spread_tpm_tib, spc_clp_2y FROM macro_tasas_rendimientos ORDER BY periodo DESC LIMIT 24;" },
              { label: "Breakeven de Inflación a 5 y 10 años", query: "SELECT periodo, bcp_5y, bcu_5y, inflacion_implicita_5y_breakeven, bcp_10y, bcu_10y, inflacion_implicita_10y_breakeven FROM macro_tasas_rendimientos WHERE inflacion_implicita_5y_breakeven IS NOT NULL ORDER BY periodo DESC LIMIT 24;" }
            ],
            tables: [
              { id: "macro_tasas_rendimientos", name: "macro.tasas_rendimientos", rows: "153 registros", file: "outputs/macro/macro_tasas_rendimientos.parquet" }
            ]
          },
          {
            id: "circ_macro_divisas",
            type: "circular",
            label: "Mercado Cambiario & Divisas",
            badge: "153 Registros",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "Dólar Observado: Promedio vs Cierre vs Volatilidad", query: "SELECT periodo, usd_clp_promedio, usd_clp_cierre, var_mensual_usd_pct, var_anual_usd_pct, usd_clp_volatilidad_anualizada_pct FROM macro_divisas_mercado ORDER BY periodo DESC LIMIT 15;" },
              { label: "Tipo de Cambio Real Multilateral (TCR vs TCR-5)", query: "SELECT periodo, usd_clp_cierre, tcr_general, tcr_5monedas FROM macro_divisas_mercado WHERE tcr_general IS NOT NULL ORDER BY periodo DESC LIMIT 18;" },
              { label: "Dólar vs Euro Observado y Variación Mensual", query: "SELECT periodo, usd_clp_cierre, var_mensual_usd_pct, eur_clp_cierre, var_mensual_eur_pct FROM macro_divisas_mercado ORDER BY periodo DESC LIMIT 15;" }
            ],
            tables: [
              { id: "macro_divisas_mercado", name: "macro.divisas_mercado", rows: "153 registros", file: "outputs/macro/macro_divisas_mercado.parquet" }
            ]
          },
          {
            id: "circ_macro_precios",
            type: "circular",
            label: "Precios, Actividad y Expectativas",
            badge: "153 Registros",
            badgeType: "data",
            status: "active",
            sector: "macro",
            chips: [
              { label: "Inflación IPC Anual vs Expectativas EEE (11m y 23m)", query: "SELECT periodo, ipc_var_anual, eee_ipc_11m, eee_ipc_23m, desvio_eee_11m_meta_bps FROM macro_precios_actividad WHERE ipc_var_anual IS NOT NULL ORDER BY periodo DESC LIMIT 18;" },
              { label: "IMACEC Total vs No Minero vs Cobre BML", query: "SELECT periodo, imacec_empalmado, imacec_no_minero, imacec_var_anual_pct, cobre_spot_usd_lb, cobre_var_anual_pct FROM macro_precios_actividad WHERE imacec_empalmado IS NOT NULL ORDER BY periodo DESC LIMIT 18;" },
              { label: "Valor de la UF y Variación Mensual", query: "SELECT periodo, uf_cierre, uf_promedio, uf_var_mensual_pct FROM macro_precios_actividad ORDER BY periodo DESC LIMIT 18;" }
            ],
            tables: [
              { id: "macro_precios_actividad", name: "macro.precios_actividad", rows: "153 registros", file: "outputs/macro/macro_precios_actividad.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_factoring_leasing",
    type: "group",
    label: "FACTORING & LEASING (CMF / NBFI)",
    badges: [
      { type: "entities", text: "28 Entidades", title: "Lista de 28 entidades de Factoring y Leasing" }
    ],
    status: "active",
    children: [
      {
        id: "sector_factoring_leasing",
        type: "sector",
        label: "Intermediación Financiera No Bancaria",
        sector: "factoring_leasing",
        children: [
          {
            id: "cat_fl_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "28 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "factoring_leasing",
            chips: [
              { label: "Lista por segmento y licencia (catálogo local)", query: "SELECT rut, razon_social, nombre_fantasia, segmento, tipo_licencia, grupo_controlador, vigente FROM factoring_leasing_maestro ORDER BY vigente DESC, segmento, razon_social;" },
              { label: "Estado consignado en la lista", query: "SELECT vigente, estado, count(*) as total_entidades, string_agg(nombre_fantasia, ', ') as instituciones FROM factoring_leasing_maestro GROUP BY vigente, estado ORDER BY vigente DESC;" },
              { label: "Tipos de licencia consignados", query: "SELECT tipo_licencia, count(*) as total, string_agg(nombre_fantasia, ', ') as instituciones FROM factoring_leasing_maestro WHERE vigente = 1 GROUP BY tipo_licencia;" },
              { label: "Segmentación por Línea de Negocio", query: "SELECT segmento, count(*) as entidades, sum(es_factoring) as con_factoring, sum(es_leasing_financiero) as con_leasing, sum(es_automotriz) as con_automotriz FROM factoring_leasing_maestro WHERE vigente = 1 GROUP BY segmento;" }
            ],
            tables: [
              { id: "factoring_leasing_maestro", name: "factoring_leasing.lista_entidades", rows: "28 entidades", file: "outputs/factoring_leasing/factoring_leasing_maestro.parquet" }
            ]
          },
          // BEGIN AUTO FL IFRS SERIES NAVIGATION
          // END AUTO FL IFRS SERIES NAVIGATION
          {
            id: "fl_balance_muestra_cmf_folder",
            type: "circular",
            label: "Balance · Muestra cotejada CMF (2 filas)",
            badge: "2 entidades · 2022",
            badgeType: "data",
            status: "active",
            sector: "factoring_leasing",
            chips: [
              { label: "Balance cotejado (miles de pesos)", query: "SELECT segmento, rut, nombre_en_archivo_y_ficha, periodo, total_activos_miles_clp, total_pasivos_miles_clp, patrimonio_miles_clp, efectivo_miles_clp, fuente_ficha_cmf FROM factoring_leasing_eeff_muestra_cmf ORDER BY segmento;" }
            ],
            tables: [
              { id: "factoring_leasing_eeff_muestra_cmf", name: "factoring_leasing.balance_muestra_cmf", rows: "2 filas cotejadas · no es el sector", file: "outputs/factoring_leasing/factoring_leasing_eeff_muestra_cmf.parquet" }
            ]
          },
          {
            id: "fl_resultados_muestra_cmf_folder",
            type: "circular",
            label: "Estado de resultados · Muestra cotejada CMF (2 filas)",
            badge: "2 entidades · 2022",
            badgeType: "data",
            status: "active",
            sector: "factoring_leasing",
            chips: [
              { label: "Resultados acumulados desde enero (miles de pesos)", query: "SELECT segmento, rut, periodo, resultado_antes_impuestos_miles_clp, resultado_operaciones_continuadas_miles_clp, definicion_periodo_resultado, fuente_ficha_cmf FROM factoring_leasing_resultados_muestra_cmf ORDER BY segmento;" }
            ],
            tables: [
              { id: "factoring_leasing_resultados_muestra_cmf", name: "factoring_leasing.resultados_muestra_cmf", rows: "2 filas cotejadas · acumulado desde enero", file: "outputs/factoring_leasing/factoring_leasing_resultados_muestra_cmf.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_corredoras_bolsa",
    type: "group",
    label: "CORREDORAS DE BOLSA (CMF)",
    badges: [
      { type: "entities", text: "120 Entidades", title: "Intermediarios de valores supervisados por la CMF (24 vigentes + 96 históricas)" },
      { type: "data", text: "621 Balances", title: "Carátulas XML CMF y resumen derivado; cotejo independiente de fuente en curso" }
    ],
    status: "active",
    children: [
      {
        id: "sector_corredoras_bolsa",
        type: "sector",
        label: "Intermediación de Valores y Corretaje Bursátil",
        sector: "corredoras_bolsa",
        children: [
          {
            id: "cat_cb_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "120 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "corredoras_bolsa",
            chips: [
              { label: "Catálogo de Corredoras Vigentes", query: "SELECT rut, nombre_empresa, nombre_fantasia, grupo_financiero, estado_vigencia FROM corredoras_bolsa_maestro WHERE estado_vigencia = 'Vigente' ORDER BY nombre_empresa;" },
              { label: "Distribución por Conglomerado", query: "SELECT grupo_financiero, count(*) as total_corredoras, sum(CASE WHEN estado_vigencia = 'Vigente' THEN 1 ELSE 0 END) as vigentes FROM corredoras_bolsa_maestro GROUP BY grupo_financiero ORDER BY total_corredoras DESC;" }
            ],
            tables: [
              { id: "corredoras_bolsa_maestro", name: "corredoras.lista_entidades", rows: "120 entidades", file: "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet" }
            ]
          },
          {
            id: "cat_cb_registro",
            type: "circular",
            label: "Registro Único de Corredoras",
            badge: "120 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "corredoras_bolsa",
            chips: [
              { label: "Catálogo de Corredoras por Grupo Financiero", query: "SELECT rut, nombre_empresa, nombre_fantasia, grupo_financiero, estado_vigencia FROM corredoras_bolsa_registro_universo ORDER BY estado_vigencia DESC, grupo_financiero, nombre_empresa;" },
              { label: "Distribución de Corredoras por Conglomerado", query: "SELECT grupo_financiero, count(*) as total_corredoras, sum(CASE WHEN estado_vigencia = 'Vigente' THEN 1 ELSE 0 END) as vigentes, string_agg(nombre_fantasia, ', ') as instituciones FROM corredoras_bolsa_registro_universo GROUP BY grupo_financiero ORDER BY total_corredoras DESC;" }
            ],
            tables: [
              { id: "corredoras_bolsa_registro_universo", name: "corredoras.registro_unico", rows: "120 entidades", file: "outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.parquet" }
            ]
          },
          {
            id: "circ_cb_balances",
            type: "circular",
            label: "Estados Financieros · XML CMF (en auditoría)",
            badge: "621 Balances · 2 vistas",
            badgeType: "data",
            status: "active",
            sector: "corredoras_bolsa",
            chips: [
              { label: "Ranking por Activos Totales (MM$ USD)", query: "SELECT b.periodo, m.nombre_fantasia, b.total_activos_m_usd, b.total_pasivos_m_usd, b.patrimonio_m_usd, b.utilidad_ejercicio_m_usd, m.grupo_financiero FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.total_activos_m_usd DESC LIMIT 15;" },
              { label: "Utilidad Neta del Ejercicio (Líderes Bursátiles)", query: "SELECT b.periodo, m.nombre_fantasia, b.utilidad_ejercicio_m_clp, b.utilidad_ejercicio_m_usd, b.total_activos_m_usd FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.utilidad_ejercicio_m_usd DESC LIMIT 15;" },
              { label: "Cartera Comprometida vs Disponible en Corredoras", query: "SELECT b.periodo, m.nombre_fantasia, b.cartera_vr_comprometida_m_clp, b.cartera_vr_disponible_m_clp, b.operaciones_financiamiento_crv_m_clp, b.obligaciones_retrocompra_vrc_m_clp FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.cartera_vr_comprometida_m_clp DESC LIMIT 15;" },
              { label: "Liquidez: Proporción de Caja sobre Activos (%)", query: "SELECT b.periodo, m.nombre_fantasia, b.efectivo_equivalentes_m_usd, b.total_activos_m_usd, round(b.efectivo_equivalentes_m_usd / NULLIF(b.total_activos_m_usd, 0) * 100, 2) as pct_caja_activos FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.efectivo_equivalentes_m_usd DESC LIMIT 15;" }
            ],
            tables: [
              { id: "corredoras_bolsa_caratula_eeff_historico", name: "corredoras.estados_financieros", rows: "621 balances", file: "outputs/corredoras_bolsa/corredoras_bolsa_caratula_eeff_historico.parquet" },
              { id: "corredoras_bolsa_balance_resumen", name: "corredoras.balance_resumen", rows: "621 balances", file: "outputs/corredoras_bolsa/corredoras_bolsa_balance_resumen.parquet" }
            ]
          },
        ]
      }
    ]
  },
  {
    id: "group_securitizacion",
    type: "group",
    label: "SECURITIZACIÓN (CMF / LEY 18.045)",
    badges: [
      { type: "entities", text: "16 Gestoras", title: "Sociedades securitizadoras y sus patrimonios separados son entidades distintas" },
      { type: "data", text: "2.086 PDF", title: "Balances de patrimonios separados leídos de PDF; los balances de las gestoras son otra serie" }
    ],
    status: "active",
    children: [
      {
        id: "sector_securitizadoras",
        type: "sector",
        label: "Sociedades Securitizadoras",
        sector: "securitizadoras",
        children: [
          {
            id: "cat_sec_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "16 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "securitizadoras",
            chips: [
              { label: "Catálogo de Securitizadoras (Vigentes vs Históricas)", query: "SELECT rut_completo, razon_social, estado_vigencia, lineas_deuda_registradas FROM securitizadoras_maestro ORDER BY estado_vigencia, razon_social;" },
              { label: "Securitizadoras con Emisiones Activas CMF", query: "SELECT razon_social, rut_completo, lineas_deuda_registradas, cmf_url FROM securitizadoras_maestro WHERE lineas_deuda_registradas > 0 ORDER BY lineas_deuda_registradas DESC;" }
            ],
            tables: [
              { id: "securitizadoras_maestro", name: "securitizadoras.lista_entidades", rows: "16 entidades", file: "outputs/securitizadoras/securitizadoras_maestro.parquet" }
            ]
          },
          {
            id: "circ_sec_balances",
            type: "circular",
            label: "Balances IFRS de Sociedades Gestoras",
            badge: "362 Balances",
            badgeType: "data",
            status: "active",
            sector: "securitizadoras",
            chips: [
              { label: "Ranking por Activos de la Sociedad Gestora (MM$)", query: "SELECT periodo, razon_social, total_activos_m_clp, total_pasivos_m_clp, patrimonio_neto_m_clp, efectivo_y_equivalentes_m_clp FROM securitizadoras_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM securitizadoras_balance_resumen) ORDER BY total_activos_m_clp DESC;" },
              { label: "Utilidad Neta de las Gestoras por Comisiones", query: "SELECT periodo, razon_social, ganancia_perdida_ejercicio_m_clp, total_activos_m_usd, patrimonio_neto_m_usd FROM securitizadoras_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM securitizadoras_balance_resumen) ORDER BY ganancia_perdida_ejercicio_m_clp DESC;" },
              { label: "Evolución Activos Gestora: BCI vs Santander vs BICE", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, efectivo_y_equivalentes_m_clp FROM securitizadoras_balance_resumen WHERE razon_social IN ('BCI SECURITIZADORA S.A.', 'SANTANDER S.A. SOCIEDAD SECURITIZADORA', 'SECURITIZADORA BICE S.A.') ORDER BY periodo DESC, total_activos_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "securitizadoras_balance_resumen", name: "securitizadoras.balance_resumen", rows: "362 balances", file: "outputs/securitizadoras/securitizadoras_balance_resumen.parquet" }
            ]
          }
        ]
      },
      {
        id: "sector_patrimonios_separados",
        type: "sector",
        label: "Patrimonios Separados",
        sector: "patrimonios_separados",
        children: [
          {
            id: "circ_ps_emisiones",
            type: "circular",
            label: "Lista de Entidades",
            badge: "18 Emisiones",
            badgeType: "entities",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Líneas por clase de colateral", query: "SELECT clase_colateral_subyacente, count(*) as lineas, string_agg(razon_social_administradora, ', ') as administradoras FROM patrimonios_separados_maestro GROUP BY clase_colateral_subyacente ORDER BY lineas DESC;" },
              { label: "Inscripciones por moneda y monto", query: "SELECT numero_inscripcion, fecha_inscripcion, razon_social_administradora, denominacion_emision, moneda, monto_inscrito, clase_colateral_subyacente FROM patrimonios_separados_maestro ORDER BY fecha_inscripcion DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_maestro", name: "patrimonios_separados.lista_emisiones", rows: "18 emisiones", file: "outputs/securitizadoras/patrimonios_separados_maestro.parquet" }
            ]
          },
          {
            id: "circ_ps_balance_pdf",
            type: "circular",
            label: "Balances · Cuentas por Línea",
            badge: "46.502 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Total activos de marzo 2026", query: "SELECT nombre_administradora, codigo_patrimonio, nombre_cuenta, monto_m_clp FROM patrimonios_separados_balance_pdf WHERE categoria = 'Total Activos' AND periodo = '202603' ORDER BY monto_m_clp DESC;" },
              { label: "Cuentas de un PDF", query: "SELECT categoria, nombre_cuenta, monto_m_clp FROM patrimonios_separados_balance_pdf WHERE archivo = '201003_96765170_TRANSA_SECURITIZADORA_TRANSA_PATRIMONIO_SEPARADO_BTRA1.pdf' ORDER BY id_linea;" },
              { label: "Rubros del balance", query: "SELECT categoria, count(*) AS filas FROM patrimonios_separados_balance_pdf GROUP BY categoria ORDER BY filas DESC;" },
              { label: "PDF por securitizadora del catálogo", query: "SELECT s.razon_social, count(DISTINCT p.archivo) AS pdfs FROM patrimonios_separados_balance_pdf p JOIN securitizadoras_maestro s ON s.rut = p.rut_administradora GROUP BY s.razon_social ORDER BY pdfs DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_balance_pdf", name: "patrimonios_separados.balance_cuentas", rows: "46.502 registros", file: "outputs/securitizadoras/patrimonios_separados_balance_pdf.parquet" }
            ]
          },
          {
            id: "circ_ps_balance_resumen",
            type: "circular",
            label: "Estados Financieros · Resumen Anual",
            badge: "64 Balances",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Mayores activos del resumen", query: "SELECT codigo_emision, denominacion_ps, nombre_administradora, periodo, total_activos_mclp, deuda_bonos_largo_plazo_mclp, cuadre_contable_ok FROM patrimonios_separados_balance_resumen ORDER BY total_activos_mclp DESC LIMIT 15;" },
              { label: "Marca de cuadre que trae el archivo", query: "SELECT periodo, count(*) as balances, SUM(CASE WHEN cuadre_contable_ok THEN 1 ELSE 0 END) as marca_cuadre FROM patrimonios_separados_balance_resumen GROUP BY periodo ORDER BY periodo;" }
            ],
            tables: [
              { id: "patrimonios_separados_balance_resumen", name: "patrimonios_separados.balance_resumen", rows: "64 balances", file: "outputs/securitizadoras/patrimonios_separados_balance_resumen.parquet" }
            ]
          },
          {
            id: "circ_ps_balance_lineas",
            type: "circular",
            label: "Estados Financieros · Balance Línea a Línea",
            badge: "16.842 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Activos contra pasivo y patrimonio", query: "SELECT id_patrimonio, periodo, MAX(CASE WHEN codigo_cuenta = '10.000' THEN monto_m_clp END) as total_activos_mclp, MAX(CASE WHEN codigo_cuenta = '20.000' THEN monto_m_clp END) as total_pasivo_y_patrimonio_mclp, MAX(CASE WHEN codigo_cuenta = '21.000' THEN monto_m_clp END) as pasivos_circulantes_mclp, MAX(CASE WHEN codigo_cuenta = '22.000' THEN monto_m_clp END) as pasivos_largo_plazo_mclp FROM patrimonios_separados_balance_lineas GROUP BY id_patrimonio, periodo ORDER BY periodo DESC, total_activos_mclp DESC LIMIT 20;" },
              { label: "Activo securitizado y su provisión", query: "SELECT id_patrimonio, periodo, codigo_cuenta, nombre_cuenta, monto_m_clp FROM patrimonios_separados_balance_lineas WHERE codigo_cuenta IN ('11.030', '11.120', '13.010') ORDER BY periodo DESC, monto_m_clp DESC LIMIT 20;" },
              { label: "Disponible y valores negociables", query: "SELECT id_patrimonio, periodo, nombre_cuenta, monto_m_clp FROM patrimonios_separados_balance_lineas WHERE codigo_cuenta IN ('11.010', '11.020') AND monto_m_clp > 0 ORDER BY periodo DESC, monto_m_clp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "patrimonios_separados_balance_lineas", name: "patrimonios_separados.balance_lineas", rows: "16.842 registros", file: "outputs/securitizadoras/patrimonios_separados_balance_lineas.parquet" }
            ]
          },
          {
            id: "circ_ps_excedentes_lineas",
            type: "circular",
            label: "Estados Financieros · Excedentes y Resultados",
            badge: "11.157 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Ingresos del estado de excedentes", query: "SELECT id_patrimonio, periodo, codigo_cuenta, nombre_cuenta, monto_m_clp FROM patrimonios_separados_excedentes_lineas WHERE codigo_cuenta IN ('31.000', '31.030', '31.040') ORDER BY periodo DESC, monto_m_clp DESC LIMIT 20;" },
              { label: "Remuneraciones de administración y servicios", query: "SELECT id_patrimonio, periodo, codigo_cuenta, nombre_cuenta, monto_m_clp FROM patrimonios_separados_excedentes_lineas WHERE codigo_cuenta IN ('35.210', '35.215', '35.220', '35.230') ORDER BY periodo DESC, monto_m_clp DESC LIMIT 20;" },
              { label: "Excedente o déficit del ejercicio", query: "SELECT id_patrimonio, periodo, nombre_cuenta, monto_m_clp FROM patrimonios_separados_excedentes_lineas WHERE codigo_cuenta = '30.000' ORDER BY periodo DESC, monto_m_clp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "patrimonios_separados_excedentes_lineas", name: "patrimonios_separados.excedentes", rows: "11.157 registros", file: "outputs/securitizadoras/patrimonios_separados_excedentes_lineas.parquet" }
            ]
          },
          {
            id: "circ_ps_nota_cartera",
            type: "circular",
            label: "Notas · Cartera Securitizada",
            badge: "796 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Cartera por Originador y Tipo de Activo", query: "SELECT originador, tipo_activo, count(*) as emisiones, SUM(valor_presente_mclp) as valor_total_mclp FROM patrimonios_separados_nota_cartera_detalle GROUP BY originador, tipo_activo ORDER BY valor_total_mclp DESC;" },
              { label: "Tasas Promedio y Plazos Residuales", query: "SELECT codigo_emision, periodo, originador, tasa_interes_promedio_pct, plazo_promedio_residual_meses, valor_presente_mclp FROM patrimonios_separados_nota_cartera_detalle ORDER BY valor_presente_mclp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "patrimonios_separados_nota_cartera_detalle", name: "patrimonios_separados.nota_cartera", rows: "796 registros", file: "outputs/securitizadoras/patrimonios_separados_nota_cartera_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_nota_morosidad",
            type: "circular",
            label: "Notas · Morosidad",
            badge: "6.632 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Distribución de Cartera y Provisiones por Tramo", query: "SELECT tramo_mora, SUM(numero_deudores) as deudores, SUM(monto_cartera_mclp) as cartera_mclp, SUM(monto_provision_mclp) as provision_mclp FROM patrimonios_separados_nota_morosidad_detalle GROUP BY tramo_mora ORDER BY cartera_mclp DESC;" },
              { label: "Etiquetas de tramo tal como están guardadas", query: "SELECT tramo_mora, count(*) as filas FROM patrimonios_separados_nota_morosidad_detalle GROUP BY tramo_mora ORDER BY filas DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_nota_morosidad_detalle", name: "patrimonios_separados.nota_morosidad", rows: "6.632 registros", file: "outputs/securitizadoras/patrimonios_separados_nota_morosidad_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_nota_bonos",
            type: "circular",
            label: "Notas · Bonos",
            badge: "8.001 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Series Emitidas por Moneda y Tasa Carátula", query: "SELECT serie, moneda, AVG(tasa_caratula_pct) as tasa_prom, SUM(saldo_insoluto_mclp) as saldo_total_mclp FROM patrimonios_separados_nota_bonos_detalle GROUP BY serie, moneda ORDER BY saldo_total_mclp DESC;" },
              { label: "Vencimientos y Saldo Insoluto de Bonos", query: "SELECT codigo_emision, serie, nemotecnico, fecha_vencimiento, tasa_caratula_pct, saldo_insoluto_mclp FROM patrimonios_separados_nota_bonos_detalle ORDER BY saldo_insoluto_mclp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "patrimonios_separados_nota_bonos_detalle", name: "patrimonios_separados.nota_bonos", rows: "8.001 registros", file: "outputs/securitizadoras/patrimonios_separados_nota_bonos_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_nota_administracion",
            type: "circular",
            label: "Notas · Administración",
            badge: "2.153 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Comisiones de Administración por Concepto", query: "SELECT nombre_administradora, concepto_comision, SUM(gasto_periodo_mclp) as gasto_total_mclp FROM patrimonios_separados_nota_administracion_detalle GROUP BY nombre_administradora, concepto_comision ORDER BY gasto_total_mclp DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_nota_administracion_detalle", name: "patrimonios_separados.nota_administracion", rows: "2.153 registros", file: "outputs/securitizadoras/patrimonios_separados_nota_administracion_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_nota_sobrecolateral",
            type: "circular",
            label: "Notas · Sobrecolateral y Reservas",
            badge: "679 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Sobrecolateral y Fondo de Reserva por Emisión", query: "SELECT codigo_emision, periodo, valor_activos_mclp, valor_pasivos_bonos_mclp, monto_sobrecolateral_mclp, sobrecolateral_pct, fondo_reserva_mclp FROM patrimonios_separados_nota_sobrecolateral_detalle ORDER BY monto_sobrecolateral_mclp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "patrimonios_separados_nota_sobrecolateral_detalle", name: "patrimonios_separados.nota_sobrecolateral", rows: "679 registros", file: "outputs/securitizadoras/patrimonios_separados_nota_sobrecolateral_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_nota_efectivo",
            type: "circular",
            label: "Notas · Efectivo y Valores Negociables",
            badge: "3.802 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Efectivo y Equivalentes Estrictos (NIC 7 - Bancos, FFMM, DAP, Repos)", query: "SELECT institucion, tipo_instrumento, count(*) as num_partidas, SUM(saldo_mclp) as total_mclp, SUM(saldo_mmclp) as total_mmclp FROM patrimonios_separados_nota_efectivo_detalle WHERE tipo_instrumento NOT LIKE '%Mutuo%' GROUP BY institucion, tipo_instrumento ORDER BY total_mclp DESC;" },
              { label: "Saldos Totales por Institución Depositaria", query: "SELECT institucion, tipo_instrumento, count(*) as num_partidas, SUM(saldo_mclp) as total_mclp, SUM(saldo_mmclp) as total_mmclp FROM patrimonios_separados_nota_efectivo_detalle GROUP BY institucion, tipo_instrumento ORDER BY total_mclp DESC;" },
              { label: "Inversiones Transitorias de Caja en Mutuos Hipotecarios", query: "SELECT codigo_emision, periodo, institucion, tipo_instrumento, saldo_mclp, saldo_mmclp FROM patrimonios_separados_nota_efectivo_detalle WHERE tipo_instrumento LIKE '%Mutuo%' ORDER BY saldo_mclp DESC LIMIT 20;" },
              { label: "Top Posiciones de Liquidez y Depósitos", query: "SELECT codigo_emision, periodo, institucion, tipo_instrumento, saldo_mclp, saldo_mmclp FROM patrimonios_separados_nota_efectivo_detalle ORDER BY saldo_mclp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "patrimonios_separados_nota_efectivo_detalle", name: "patrimonios_separados.nota_efectivo", rows: "3.802 registros", file: "outputs/securitizadoras/patrimonios_separados_nota_efectivo_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_cartera_morosidad",
            type: "circular",
            label: "Notas · Extracto de Mora",
            badge: "67 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Tramos del extracto, sin la columna de porcentaje", query: "SELECT codigo_emision, periodo, tramo_mora, numero_deudores, monto_cartera_mclp, provision_mclp FROM patrimonios_separados_cartera_morosidad_detalle WHERE tramo_mora <> 'Total' ORDER BY periodo DESC, monto_cartera_mclp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "patrimonios_separados_cartera_morosidad_detalle", name: "patrimonios_separados.cartera_morosidad", rows: "67 registros", file: "outputs/securitizadoras/patrimonios_separados_cartera_morosidad_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_repos",
            type: "circular",
            label: "Operaciones · Pactos de Retroventa",
            badge: "52 Pactos",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            chips: [
              { label: "Pactos por contraparte", query: "SELECT contraparte, count(*) as pactos, ROUND(SUM(monto_mclp)/1000, 1) as monto_mm_clp, ROUND(AVG(tasa_interes_anual_pct), 2) as tasa_prom_pct FROM patrimonios_separados_repos_detalle GROUP BY contraparte ORDER BY monto_mm_clp DESC;" },
              { label: "Instrumentos de los pactos", query: "SELECT instrumento_pacto, emisor_subyacente, count(*) as operaciones, ROUND(SUM(monto_mclp)/1000, 1) as monto_mm_clp FROM patrimonios_separados_repos_detalle GROUP BY instrumento_pacto, emisor_subyacente ORDER BY monto_mm_clp DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_repos_detalle", name: "patrimonios_separados.repos_contratos", rows: "52 pactos", file: "outputs/securitizadoras/patrimonios_separados_repos_detalle.parquet" }
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
      { type: "entities", text: "7 Entidades", title: "Cooperativas de ahorro y crédito supervisadas por la CMF" },
      { type: "data", text: "700+ Datos", title: "Balances IFRS mensuales y colocaciones (2018 a 2026)" }
    ],
    status: "active",
    children: [
      {
        id: "sector_cooperativas",
        type: "sector",
        label: "Ahorro y Crédito Cooperativo",
        sector: "cooperativas",
        children: [
          {
            id: "cat_coop_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "7 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "cooperativas",
            chips: [
              { label: "Directorio de Cooperativas Fiscalizadas", query: "SELECT rut, nombre_empresa, nombre_fantasia, sede_matriz, region, estado_vigencia FROM cooperativas_maestro ORDER BY nombre_fantasia;" },
              { label: "Distribución Regional de Cooperativas", query: "SELECT region, count(*) as total_entidades, string_agg(nombre_fantasia, ', ') as instituciones FROM cooperativas_maestro GROUP BY region ORDER BY total_entidades DESC;" }
            ],
            tables: [
              { id: "cooperativas_maestro", name: "cooperativas.lista_entidades", rows: "7 entidades", file: "outputs/cooperativas/cooperativas_maestro.parquet" }
            ]
          },
          {
            id: "circ_coop_balances",
            type: "circular",
            label: "Estados Financieros · IFRS y Solvencia",
            badge: "294 Balances",
            badgeType: "data",
            status: "active",
            sector: "cooperativas",
            chips: [
              { label: "Ranking de Cooperativas por Activos Totales (MM$ USD)", query: "SELECT periodo, nombre_fantasia, total_activos_m_usd, total_pasivos_m_usd, patrimonio_m_usd, utilidad_ejercicio_m_usd FROM cooperativas_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM cooperativas_balance_resumen) ORDER BY total_activos_m_usd DESC;" },
              { label: "Solvencia Patrimonial (Patrimonio / Activos %)", query: "SELECT periodo, nombre_fantasia, total_activos_m_usd, patrimonio_m_usd, round(patrimonio_m_usd / NULLIF(total_activos_m_usd, 0) * 100, 2) as ratio_patrimonio_activos_pct FROM cooperativas_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM cooperativas_balance_resumen) ORDER BY ratio_patrimonio_activos_pct DESC;" },
              { label: "Estructura de Apalancamiento (Pasivos / Patrimonio)", query: "SELECT periodo, nombre_fantasia, total_activos_m_clp, total_pasivos_m_clp, patrimonio_neto_m_clp, round(total_pasivos_m_clp / NULLIF(patrimonio_neto_m_clp, 0), 2) as leverage_contable FROM cooperativas_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM cooperativas_balance_resumen) ORDER BY total_activos_m_clp DESC;" },
              { label: "Evolución de Excedentes Netos (Coopeuch vs Sistema)", query: "SELECT periodo, nombre_fantasia, utilidad_ejercicio_m_clp, utilidad_ejercicio_m_usd FROM cooperativas_balance_resumen WHERE nombre_fantasia IN ('COOPEUCH', 'ORIENCOOP', 'CAPUAL') ORDER BY periodo DESC, utilidad_ejercicio_m_clp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "cooperativas_balance_resumen", name: "cooperativas.balance_resumen", rows: "294 balances", file: "outputs/cooperativas/cooperativas_balance_resumen.parquet" }
            ]
          },
          {
            id: "circ_coop_efectivo_bancos",
            type: "circular",
            label: "Notas · Efectivo y Depósitos en Bancos",
            badge: "122 Registros",
            badgeType: "data",
            status: "active",
            sector: "cooperativas",
            chips: [
              { label: "Composición de Liquidez: Caja vs Cuentas Bancarias (2025)", query: "SELECT periodo, nombre_fantasia, categoria_efectivo, round(sum(monto_m_clp), 1) as total_m_clp, round(sum(monto_m_usd), 2) as total_m_usd FROM cooperativas_nota_efectivo_detalle WHERE periodo = '2025-12' AND categoria_efectivo != 'total_efectivo_bancos' GROUP BY periodo, nombre_fantasia, categoria_efectivo ORDER BY nombre_fantasia, total_m_clp DESC;" },
              { label: "Exposición a Bancos Comerciales Locales (Detacoop)", query: "SELECT periodo, concepto_literal, institucion_contraparte, monto_m_clp, monto_m_usd FROM cooperativas_nota_efectivo_detalle WHERE rut = '70017860-9' AND categoria_efectivo = 'depositos_bancos_locales' ORDER BY periodo DESC, monto_m_clp DESC;" },
              { label: "Evolución de Fondos Disponibles en Coopeuch (2022-2025)", query: "SELECT periodo, concepto_literal, monto_m_clp, monto_m_usd FROM cooperativas_nota_efectivo_detalle WHERE rut = '82878900-7' ORDER BY periodo ASC, monto_m_clp DESC;" },
              { label: "Cheques en Canje y Valores en Cobro del Sector", query: "SELECT periodo, nombre_fantasia, concepto_literal, monto_m_clp, monto_m_usd FROM cooperativas_nota_efectivo_detalle WHERE categoria_efectivo = 'valores_en_cobro' ORDER BY periodo DESC, monto_m_clp DESC;" }
            ],
            tables: [
              { id: "cooperativas_nota_efectivo_detalle", name: "cooperativas.nota_efectivo", rows: "122 registros", file: "outputs/cooperativas/cooperativas_nota_efectivo_detalle.parquet" }
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
      { type: "entities", text: "6 Entidades", title: "Los Andes, La Araucana, Los Héroes, Caja 18 (y 2 históricas)" },
      { type: "data", text: "6 Datos", title: "Entidades de previsión y bienestar social reguladas por la Ley 18.833" }
    ],
    status: "active",
    children: [
      {
        id: "sector_cajas_compensacion",
        type: "sector",
        label: "Crédito Social y Emisión de Bonos Públicos",
        sector: "cajas_compensacion",
        children: [
          {
            id: "cat_ccaf_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "6 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "cajas_compensacion",
            chips: [
              { label: "Catálogo CCAF (Vigentes vs Absorbidas)", query: "SELECT rut_completo, nombre_fantasia, estado_vigencia, regulador_mercado_valores, codigo_cmf, lineas_deuda_registradas FROM ccaf_maestro ORDER BY estado_vigencia DESC, nombre_fantasia;" },
              { label: "CCAF Emisoras de Bonos Públicos CMF", query: "SELECT rut_completo, razon_social, codigo_cmf, lineas_deuda_registradas, cmf_url FROM ccaf_maestro WHERE emisor_valores_cmf = true ORDER BY rut;" },
              { label: "CCAF Supervisadas Exclusivamente por SUSESO", query: "SELECT rut_completo, razon_social, domicilio_casa_matriz, suseso_url, observaciones FROM ccaf_maestro WHERE emisor_valores_cmf = false AND estado_vigencia = 'Vigente';" }
            ],
            tables: [
              { id: "ccaf_maestro", name: "ccaf.lista_entidades", rows: "6 entidades", file: "outputs/cajas_compensacion/ccaf_maestro.parquet" }
            ]
          },
          {
            id: "cat_ccaf_caratula",
            type: "circular",
            label: "Balances y Situación Financiera · XBRL (2019-2026)",
            badge: "288 Balances",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            chips: [
              { label: "Totales Cierre 2024 por CCAF y Alcance", query: "SELECT ccaf, tipo_eeff, asiento_contable, monto_m_clp FROM ccaf_caratula_totales WHERE ano = 2024 AND mes = 12 ORDER BY ccaf, tipo_eeff, asiento_contable;" },
              { label: "Evolución Activos Totales (2019-2026)", query: "SELECT ano, mes, ccaf, tipo_eeff, monto_m_clp FROM ccaf_caratula_totales WHERE asiento_contable = 'Total de activos' ORDER BY ano DESC, mes DESC, ccaf;" },
              { label: "Utilidad Neta del Sistema (Últimos Años)", query: "SELECT ano, ccaf, tipo_eeff, monto_m_clp FROM ccaf_caratula_totales WHERE asiento_contable = 'Utilidad neta' AND mes = 12 ORDER BY ano DESC, monto_m_clp DESC;" }
            ],
            tables: [
              { id: "ccaf_caratula_totales", name: "ccaf.balances", rows: "288 balances", file: "outputs/cajas_compensacion/ccaf_caratula_totales.parquet" }
            ]
          },
          {
            id: "cat_ccaf_credito_social",
            type: "circular",
            label: "Colocaciones de Crédito Social y Provisiones (2019-2026)",
            badge: "268 Registros",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            chips: [
              { label: "Cartera Crédito Social Total por CCAF (Último Corte)", query: "SELECT ccaf, tipo_eeff, ROUND(SUM(monto_neto_miles_clp) / 1e3, 1) as total_neto_m_clp, ROUND(SUM(deterioro_provision_miles_clp) / 1e3, 1) as provision_m_clp FROM ccaf_colocaciones_credito_social WHERE periodo = '2026-06' GROUP BY ccaf, tipo_eeff ORDER BY total_neto_m_clp DESC;" },
              { label: "Trabajadores vs Pensionados (Consumo Cierre 2024)", query: "SELECT ccaf, tipo_afiliado, tipo_credito, ROUND(monto_neto_miles_clp / 1e3, 1) as neto_m_clp, ROUND(deterioro_provision_miles_clp / 1e3, 1) as provision_m_clp FROM ccaf_colocaciones_credito_social WHERE periodo = '2024-12' AND tipo_credito = 'Consumo' ORDER BY ccaf, tipo_afiliado;" },
              { label: "Evolución Cartera Total del Sistema (2019-2026)", query: "SELECT periodo, ROUND(SUM(monto_neto_miles_clp) / 1e6, 2) as cartera_neta_mm_clp, ROUND(SUM(deterioro_provision_miles_clp) / 1e6, 2) as provisiones_mm_clp FROM ccaf_colocaciones_credito_social GROUP BY periodo ORDER BY periodo;" },
              { label: "Provisión sobre Cartera Bruta por CCAF (2025-12)", query: "SELECT ccaf, ROUND(SUM(monto_neto_miles_clp)/1e3, 1) as colocaciones_netas_m_clp, ROUND(SUM(deterioro_provision_miles_clp)/1e3, 1) as provisiones_m_clp, ROUND(SUM(deterioro_provision_miles_clp) * 100.0 / NULLIF(SUM(monto_neto_miles_clp + deterioro_provision_miles_clp), 0), 2) as cobertura_pct FROM ccaf_colocaciones_credito_social WHERE periodo = '2025-12' GROUP BY ccaf ORDER BY colocaciones_netas_m_clp DESC;" }
            ],
            tables: [
              { id: "ccaf_colocaciones_credito_social", name: "ccaf.colocaciones_credito_social", rows: "268 registros", file: "outputs/cajas_compensacion/ccaf_colocaciones_credito_social.parquet" }
            ]
          },
          {
            id: "cat_ccaf_nota8_efectivo",
            type: "circular",
            label: "Nota 8 · Efectivo y Equivalentes (2019-2026)",
            badge: "423 Registros",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            chips: [
              { label: "Desglose Liquidez Cierre 2024", query: "SELECT ccaf, tipo_eeff, concepto, monto_m_clp FROM ccaf_nota8_efectivo_resumen WHERE ano = 2024 AND mes = 12 ORDER BY ccaf, monto_m_clp DESC;" },
              { label: "Ranking Cajas por Inversiones Corto Plazo (2024)", query: "SELECT ccaf, tipo_eeff, monto_m_clp FROM ccaf_nota8_efectivo_resumen WHERE ano = 2024 AND mes = 12 AND concepto LIKE '%Inversiones%' ORDER BY monto_m_clp DESC;" },
              { label: "Top Repos por Corredora 2024", query: "SELECT ccaf, broker_estandarizado, plazo_dias, tasa_anual_pct, valor_contable_m_clp FROM ccaf_nota8_repos_detalle WHERE ano = 2024 ORDER BY valor_contable_m_clp DESC LIMIT 10;" },
              { label: "Ranking Histórico Corredoras en Repos CCAF", query: "SELECT broker_estandarizado, count(*) AS contratos, round(sum(valor_contable_m_clp), 1) AS total_mm_clp, round(avg(plazo_dias), 1) AS plazo_prom_dias, round(avg(tasa_anual_pct), 2) AS tasa_prom_pct FROM ccaf_nota8_repos_detalle GROUP BY broker_estandarizado ORDER BY total_mm_clp DESC;" }
            ],
            tables: [
              { id: "ccaf_nota8_efectivo_resumen", name: "ccaf.nota8_efectivo_resumen", rows: "213 registros", file: "outputs/cajas_compensacion/ccaf_nota8_efectivo_resumen.parquet" },
              { id: "ccaf_nota8_dap_detalle", name: "ccaf.nota8_dap_detalle", rows: "52 registros", file: "outputs/cajas_compensacion/ccaf_nota8_dap_detalle.parquet" },
              { id: "ccaf_nota8_repos_detalle", name: "ccaf.nota8_repos_detalle", rows: "158 operaciones", file: "outputs/cajas_compensacion/ccaf_nota8_repos_detalle.parquet" }
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
      { type: "entities", text: "12 Entidades", title: "Infraestructuras críticas de liquidación, custodia, compensación y adquirencia" },
      { type: "data", text: "196 Datos", title: "82 balances trimestrales IFRS y 102 meses de tráfico LBTR/CCA" }
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
            id: "cat_pagos_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "12 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "sistemas_pago",
            chips: [
              { label: "Directorio de Infraestructuras", query: "SELECT codigo_sistema, nombre_comercial, tipo_sistema, supervisor FROM sistemas_pago_maestro ORDER BY codigo_sistema;" },
              { label: "Cámaras y Contrapartes Centrales", query: "SELECT codigo_sistema, razon_social, marco_legal FROM sistemas_pago_maestro WHERE tipo_sistema LIKE '%Cámara%' OR tipo_sistema LIKE '%Contraparte%';" }
            ],
            tables: [
              { id: "sistemas_pago_maestro", name: "sistemas_pago.lista_entidades", rows: "12 entidades", file: "outputs/sistemas_pago/sistemas_pago_maestro.parquet" }
            ]
          },
          {
            id: "cat_pagos_balances",
            type: "circular",
            label: "Balances IFRS de Cámaras y Adquirentes",
            badge: "82 Registros",
            badgeType: "data",
            status: "active",
            sector: "sistemas_pago",
            chips: [
              { label: "Último Cierre IFRS (2026-06)", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, total_activos_m_usd FROM sistemas_pago_balances WHERE periodo = '2026-06';" },
              { label: "Evolución Patrimonial Cámaras", query: "SELECT periodo, razon_social, total_activos_m_clp, total_pasivos_m_clp, patrimonio_neto_m_clp FROM sistemas_pago_balances ORDER BY periodo DESC, total_activos_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "sistemas_pago_balances", name: "sistemas_pago.balances", rows: "82 registros", file: "outputs/sistemas_pago/sistemas_pago_balances.parquet" }
            ]
          },
          {
            id: "cat_pagos_estadisticas",
            type: "circular",
            label: "Estadísticas de Liquidación y Tráfico · BCCh",
            badge: "102 Registros",
            badgeType: "data",
            status: "active",
            sector: "sistemas_pago",
            chips: [
              { label: "Volumen LBTR y TEF CCA", query: "SELECT periodo, monto_liquidado_lbtr_m_usd, monto_compensado_cca_tef_m_clp, circulante_stock_m_clp FROM sistemas_pago_estadisticas_bcch ORDER BY periodo DESC LIMIT 12;" },
              { label: "Tasas de Tarjetas vs TC", query: "SELECT periodo, tasa_tarjetas_consumo_pct, tasa_tarjetas_comercial_pct, tipo_cambio_usd_clp FROM sistemas_pago_estadisticas_bcch ORDER BY periodo DESC LIMIT 12;" }
            ],
            tables: [
              { id: "sistemas_pago_estadisticas_bcch", name: "sistemas_pago.estadisticas_bcch", rows: "102 registros", file: "outputs/sistemas_pago/sistemas_pago_estadisticas_bcch.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_retail_financiero",
    type: "group",
    label: "RETAIL FINANCIERO (CREDITO NO BANCARIO / CMF)",
    badges: [
      { type: "entities", text: "17 Entidades", title: "Emisores de tarjetas no bancarias, prepago y matrices de retail cotizadas" },
      { type: "data", text: "207 Datos", title: "Solvencia patrimonial, activos, efectivo y resultados de matrices de retail" }
    ],
    status: "active",
    children: [
      {
        id: "sector_retail_financiero",
        type: "sector",
        label: "Tarjetas Comerciales, Prepago y Matrices de Retail",
        sector: "retail_financiero",
        children: [
          {
            id: "cat_retail_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "17 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "retail_financiero",
            chips: [
              { label: "Catálogo Emisores y Matrices de Retail", query: "SELECT rut_completo, razon_social, nombre_comercial, tipo_entidad_cmf, grupo_controlador FROM retail_financiero_maestro ORDER BY segmento_mercado, razon_social;" },
              { label: "Emisores por Segmento de Mercado", query: "SELECT segmento_mercado, count(*) as total_entidades FROM retail_financiero_maestro GROUP BY segmento_mercado ORDER BY total_entidades DESC;" },
              { label: "Emisores de Prepago y Crédito Digital", query: "SELECT rut_completo, razon_social, nombre_comercial, tipo_entidad_cmf, comuna FROM retail_financiero_maestro WHERE tipo_entidad_cmf IN ('TCEEM', 'TPEEM');" }
            ],
            tables: [
              { id: "retail_financiero_maestro", name: "retail_financiero.lista_entidades", rows: "17 entidades", file: "outputs/retail_financiero/retail_financiero_maestro.parquet" }
            ]
          },
          {
            id: "circ_retail_balances",
            type: "circular",
            label: "Balances y Solvencia · IFRS Trimestral",
            badge: "190 Registros",
            badgeType: "data",
            status: "active",
            sector: "retail_financiero",
            chips: [
              { label: "Ranking Activos Totales Cierre Reciente", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, total_activos_m_usd FROM retail_financiero_balances WHERE periodo = (SELECT MAX(periodo) FROM retail_financiero_balances) ORDER BY total_activos_m_clp DESC;" },
              { label: "Utilidad Neta del Ejercicio: Falabella vs Cencosud vs Ripley", query: "SELECT periodo, razon_social, ganancia_perdida_ejercicio_m_clp, total_activos_m_clp FROM retail_financiero_balances WHERE razon_social LIKE '%FALABELLA%' OR razon_social LIKE '%CENCOSUD%' OR razon_social LIKE '%RIPLEY%' ORDER BY periodo DESC, total_activos_m_clp DESC LIMIT 15;" },
              { label: "Efectivo y Caja Disponible (MM$ CLP)", query: "SELECT periodo, razon_social, efectivo_y_equivalentes_m_clp, total_activos_m_clp, round(efectivo_y_equivalentes_m_clp / NULLIF(total_activos_m_clp, 0) * 100, 1) as pct_caja FROM retail_financiero_balances WHERE periodo = (SELECT MAX(periodo) FROM retail_financiero_balances) ORDER BY efectivo_y_equivalentes_m_clp DESC;" },
              { label: "Evolución Trimestral Patrimonio Neto (Hites vs Tricot vs ABC)", query: "SELECT periodo, razon_social, patrimonio_neto_m_clp, ganancia_perdida_ejercicio_m_clp FROM retail_financiero_balances WHERE razon_social LIKE '%HITES%' OR razon_social LIKE '%TRICOT%' OR razon_social LIKE '%ABC%' ORDER BY periodo DESC, razon_social LIMIT 18;" }
            ],
            tables: [
              { id: "retail_financiero_balances", name: "retail_financiero.balances", rows: "190 registros", file: "outputs/retail_financiero/retail_financiero_balances.parquet" }
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
      { type: "entities", text: "262 Entidades", title: "Entidades inscritas en el Registro de Prestadores de Servicios Financieros CMF" },
      { type: "data", text: "786 Datos", title: "Acreditaciones de 7 servicios FinTech y roles de Finanzas Abiertas" }
    ],
    status: "active",
    children: [
      {
        id: "sector_fintech",
        type: "sector",
        label: "Prestadores de Servicios Financieros y Open Finance",
        sector: "fintech",
        children: [
          {
            id: "cat_fintech_maestro",
            type: "circular",
            label: "Lista de Entidades",
            badge: "262 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "fintech",
            chips: [
              { label: "Prestadores Vigentes", query: "SELECT rut_completo, razon_social, tipo_persona, servicios_acreditados_total FROM fintech_rpsf_maestro WHERE estado_vigencia = 'Vigente' ORDER BY servicios_acreditados_total DESC, razon_social LIMIT 15;" },
              { label: "Distribución Regional", query: "SELECT region, COUNT(*) AS total_entidades FROM fintech_rpsf_maestro WHERE region != '' GROUP BY region ORDER BY total_entidades DESC;" }
            ],
            tables: [
              { id: "fintech_rpsf_maestro", name: "fintech.lista_entidades", rows: "262 entidades", file: "outputs/fintech/fintech_rpsf_maestro.parquet" }
            ]
          },
          {
            id: "cat_fintech_servicios",
            type: "circular",
            label: "Servicios Acreditados · CMF",
            badge: "262 Registros",
            badgeType: "data",
            status: "active",
            sector: "fintech",
            chips: [
              { label: "Servicios por Categoría", query: "SELECT servicio_nombre, estado_autorizacion, COUNT(*) AS entidades FROM fintech_servicios_acreditados GROUP BY servicio_nombre, estado_autorizacion ORDER BY entidades DESC;" },
              { label: "Plataformas Transaccionales (SAT / EO)", query: "SELECT rut_completo, razon_social, servicio_nombre, estado_autorizacion FROM fintech_servicios_acreditados WHERE servicio_sigla IN ('SAT', 'EO', 'IIF', 'CIF') ORDER BY servicio_sigla;" }
            ],
            tables: [
              { id: "fintech_servicios_acreditados", name: "fintech.servicios_acreditados", rows: "262 registros", file: "outputs/fintech/fintech_servicios_acreditados.parquet" }
            ]
          },
          {
            id: "cat_fintech_sfa",
            type: "circular",
            label: "Taxonomía de Finanzas Abiertas",
            badge: "262 Registros",
            badgeType: "data",
            status: "active",
            sector: "fintech",
            chips: [
              { label: "Distribución Roles SFA", query: "SELECT rol_sfa, COUNT(*) AS total_entidades, descripcion_rol FROM fintech_finanzas_abiertas_roles GROUP BY rol_sfa, descripcion_rol ORDER BY total_entidades DESC;" },
              { label: "Iniciadores de Pagos (IIP)", query: "SELECT rut, razon_social, rol_sfa, estandar_interfaz FROM fintech_finanzas_abiertas_roles WHERE rol_sfa = 'IIP';" }
            ],
            tables: [
              { id: "fintech_finanzas_abiertas_roles", name: "fintech.finanzas_abiertas_roles", rows: "262 registros", file: "outputs/fintech/fintech_finanzas_abiertas_roles.parquet" }
            ]
          }
        ]
      }
    ]
  }
];

class SidebarController {
  constructor() {
    this.sidebar = document.getElementById("sidebar");
    this.treeContainer = document.getElementById("sidebar-tree");
    this.searchInput = document.getElementById("sidebar-search");
    this.toggleBtn = document.getElementById("toggle-sidebar");
    this.breadcrumbEl = document.getElementById("erd-breadcrumb");

    this.selectedTableId = "vida_bonos";
    this.activeSector = "vida";
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
          if (window.erdInstance) {
            window.erdInstance.resize();
          }
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
      if (window.erdInstance) {
        window.erdInstance.resize();
      }
    });

    document.addEventListener("mouseup", () => {
      if (isResizing) {
        isResizing = false;
        resizer.classList.remove("resizing");
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        if (window.erdInstance) {
          window.erdInstance.resize();
        }
      }
    });
  }

  render() {
    if (!this.treeContainer) return;

    let html = `
      <div class="explorer-toolbar">
        <div class="toolbar-title">EXPLORADOR</div>
        <div class="toolbar-actions">
          <button class="tool-btn" id="btn-expand-all" title="Expandir todo">Expandir</button>
          <button class="tool-btn" id="btn-collapse-all" title="Colapsar todo">Colapsar</button>
          <button class="tool-btn" id="btn-show-all" title="Ver todo">Todo</button>
        </div>
      </div>
      <div class="tree-root">
    `;

    EXPLORER_TREE.forEach((group) => {
      let groupChildrenHtml = "";

      group.children.forEach((sector) => {
        let sectorChildrenHtml = "";

        sector.children.forEach((circular) => {
          let tablesHtml = "";
          circular.tables.forEach((tbl) => {
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

            tablesHtml += `
              <div class="table-node-wrapper">
                <div class="tree-row tree-table ${isSelected}" data-table-id="${tbl.id}" data-file="${tbl.file || ''}" data-name="${tbl.name}" data-sector="${circular.sector}">
                  <span class="tree-indent-3"></span>
                  ${arrowHtml}
                  ${ICONS.table}
                  <span class="tree-label table-label">${tbl.name}</span>
                  <span class="table-rows-tag">${tbl.rows}</span>
                  <div class="table-hover-actions">
                    <button class="table-action-btn run-btn" data-table-id="${tbl.id}" data-file="${tbl.file || ''}" data-name="${tbl.name}" title="Consultar en Terminal DuckDB">▶ SQL</button>
                    <button class="table-action-btn inspect-btn" data-table-id="${tbl.id}" title="Inspeccionar esquema">i</button>
                  </div>
                </div>
                ${hasPartitions ? `<div class="table-partitions-children" id="${partKey}" style="display: ${isPartOpen ? 'block' : 'none'};">${partHtml}</div>` : ""}
              </div>
            `;
          });

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

      let badgesHtml = "";
      if (group.badges && group.badges.length > 0) {
        badgesHtml = group.badges.map((b) => {
          const bClass = b.type === "pending" ? "badge-por-auditar" : (b.type === "entities" ? "badge-entities" : (b.type === "data" ? "badge-data" : "badge-roadmap"));
          return `<span class="group-badge node-badge ${bClass}" title="${b.title || b.text}">${b.text}</span>`;
        }).join("");
      } else if (group.badge) {
        const groupBadgeClass = group.status === "roadmap" ? "badge-roadmap" : "badge-data";
        badgesHtml = `<span class="group-badge node-badge ${groupBadgeClass}">${group.badge}</span>`;
      }

      html += `
        <div class="tree-group ${groupOpenClass} ${groupRoadmapClass}" data-group-id="${group.id}">
          <div class="tree-group-header">
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
    });

    html += `</div>`;
    this.treeContainer.innerHTML = html;
    this.bindTreeEvents();
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
      });
    }

    // Toolbar: Ver todo
    const allBtn = document.getElementById("btn-show-all");
    if (allBtn) {
      allBtn.addEventListener("click", () => {
        document.querySelectorAll(".tree-row").forEach((r) => r.classList.remove("selected"));
        if (this.breadcrumbEl) this.breadcrumbEl.textContent = "Todas las Industrias";
        if (window.erdInstance) window.erdInstance.focusSector("todos");
        if (window.ChatTerminal) {
          window.ChatTerminal.restoreDefaultChips();
          window.ChatTerminal.addSystemMessage("Vista restablecida: Todas las Industrias.");
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
        if (sector && window.erdInstance) {
          window.erdInstance.focusSector(sector);
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
        if (window.erdInstance) {
          const node = window.erdInstance.tables.find((t) => t.id === tableId || t.name === tableId);
          if (node) {
            window.erdInstance.showSchemaModal(node);
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

  setNodeExpanded(nodeId, isOpen) {
    if (!nodeId) return;
    if (isOpen) {
      this.expandedNodes.add(nodeId);
    } else {
      this.expandedNodes.delete(nodeId);
    }
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

    if (this.breadcrumbEl) {
      this.breadcrumbEl.textContent = `${targetSectorName} > ${targetCirc.label}`;
    }

    if (window.erdInstance) {
      window.erdInstance.focusSector(sector);
    }

    if (window.ChatTerminal && targetCirc.chips) {
      window.ChatTerminal.setCustomChips(targetCirc.chips, `${targetSectorName} · ${targetCirc.label}`);
    }

    // Sincronizar automáticamente el Visor de Datos con la primera tabla de la circular
    if (targetCirc.tables && targetCirc.tables.length > 0) {
      const primary = targetCirc.tables[0];
      this.onTableSelect(primary.id, primary.name, primary.file, sector);
    }
  }

  onTableSelect(tableId, tableName, file, sector) {
    this.selectedTableId = tableId;

    // Actualizar clase seleccionada en la fila del arbol
    document.querySelectorAll(".tree-table").forEach((el) => {
      el.classList.toggle("selected", el.dataset.tableId === tableId);
    });

    // Actualizar Breadcrumb
    if (this.breadcrumbEl) {
      this.breadcrumbEl.textContent = `Tabla: ${tableName}`;
    }

    // Enfocar y centrar la tabla en el Canvas ERD
    if (window.erdInstance) {
      window.erdInstance.focusTable(tableId);
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
      document.querySelectorAll(".tree-group, .tree-node, .tree-table").forEach((el) => {
        el.style.display = "";
      });
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
  }
}

window.SidebarController = SidebarController;

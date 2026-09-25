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
    open: true,
    children: [
      {
        id: "sector_vida",
        type: "sector",
        label: "Seguros de Vida",
        sector: "vida",
        open: true,
        children: [
          {
            id: "cat_vida_aseguradoras",
            type: "circular",
            label: "Lista de Entidades",
            badge: "61 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "vida",
            open: false,
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
            badge: "11.6M Datos",
            badgeType: "data",
            status: "active",
            sector: "vida",
            open: true,
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
                rows: "9.09M datos",
                file: "outputs/vida/cartera_bonos.parquet",
                open: true,
                partitions: [
                  { id: "vida_bonos_reciente", name: "2021 – 2026 (Reciente)", rows: "4.00M datos", file: "outputs/vida/cartera_bonos_2021_2024.parquet" },
                  { id: "vida_bonos_historico", name: "2016 – 2020 (Histórico)", rows: "5.08M datos", file: "outputs/vida/cartera_bonos_2016_2020.parquet" }
                ]
              },
              { id: "vida_bienes_raices", name: "vida.cartera_bienes_raices", rows: "2.01M datos", file: "outputs/vida/cartera_bienes_raices.parquet" },
              { id: "vida_extranjeros", name: "vida.cartera_extranjeros", rows: "146k datos", file: "outputs/vida/cartera_extranjeros.parquet" },
              { id: "vida_acciones", name: "vida.cartera_acciones", rows: "143k datos", file: "outputs/vida/cartera_acciones.parquet" },
              { id: "vida_fondos", name: "vida.cartera_fondos", rows: "77k datos", file: "outputs/vida/cartera_fondos.parquet" },
              { id: "vida_solvencia", name: "vida.cartera_solvencia", rows: "127k datos", file: "outputs/vida/cartera_solvencia.parquet" }
            ]
          },
          {
            id: "c1835_vida_derivados",
            type: "circular",
            label: "Circular 1835 · Derivados",
            badge: "482k Datos",
            badgeType: "data",
            status: "active",
            sector: "vida",
            open: false,
            chips: [
              { label: "Forwards Vida: Contrapartes", query: "SELECT nombre_contraparte, count(*) as contratos, AVG(precio_forward_pactado) as fwd_pactado FROM vida_forwards GROUP BY nombre_contraparte ORDER BY contratos DESC LIMIT 5;" },
              { label: "Swaps Vida: Tasas y MtM", query: "SELECT nombre_contraparte, count(*) as operaciones, AVG(tasa_contrato_larga) as tasa_larga, AVG(valor_razonable_mtm_m_clp) as mtm_prom FROM vida_swaps GROUP BY nombre_contraparte ORDER BY operaciones DESC LIMIT 5;" },
              { label: "Opciones Financieras Vida", query: "SELECT tipo_opcion, count(*) as contratos, AVG(precio_ejercicio) as precio_ejercicio_prom FROM vida_opciones GROUP BY tipo_opcion;" }
            ],
            tables: [
              { id: "vida_swaps", name: "vida.b7_swaps", rows: "314k datos", file: "outputs/vida/b7_swaps.parquet" },
              { id: "vida_forwards", name: "vida.b7_forwards", rows: "165k datos", file: "outputs/vida/b7_forwards.parquet" },
              { id: "vida_opciones", name: "vida.b7_opciones", rows: "2.6k datos", file: "outputs/vida/b7_opciones.parquet" }
            ]
          },
          {
            id: "c1835_vida_repos",
            type: "circular",
            label: "Circular 1835 · Pactos y Repos",
            badge: "19.4k Datos",
            badgeType: "data",
            status: "active",
            sector: "vida",
            open: false,
            chips: [
              { label: "Repos Vida: Tasas y Contrapartes", query: "SELECT nombre_contraparte, count(*) as pactos, AVG(tasa_pacto) as tasa_prom, SUM(monto_pacto_m_clp) as monto_total_m FROM vida_repos GROUP BY nombre_contraparte ORDER BY pactos DESC LIMIT 5;" },
              { label: "Repos Vida: Tasa Pacto vs Mercado", query: "SELECT periodo, AVG(tasa_pacto) as tasa_pacto_prom, AVG(tasa_mercado) as tasa_mercado_prom FROM vida_repos GROUP BY periodo ORDER BY periodo DESC LIMIT 5;" }
            ],
            tables: [
              { id: "vida_repos", name: "vida.b7_repos", rows: "19.4k datos", file: "outputs/vida/b7_repos.parquet" }
            ]
          }
        ]
      },
      {
        id: "sector_generales",
        type: "sector",
        label: "Seguros Generales",
        sector: "generales",
        open: false,
        children: [
          {
            id: "cat_gen_aseguradoras",
            type: "circular",
            label: "Lista de Entidades",
            badge: "42 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "generales",
            open: false,
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
            badge: "418k Datos",
            badgeType: "data",
            status: "active",
            sector: "generales",
            open: false,
            chips: [
              { label: "Bonos Seguros Generales", query: "SELECT tipo_bono, count(*) as tenencias, AVG(tir_mercado_pct) as tir_prom FROM generales_bonos GROUP BY tipo_bono ORDER BY tenencias DESC LIMIT 5;" },
              { label: "Inmuebles Seguros Generales", query: "SELECT comuna, count(*) as inmuebles, SUM(tasacion_comercial_m_clp) as tasacion_m FROM generales_bienes_raices GROUP BY comuna ORDER BY inmuebles DESC LIMIT 5;" },
              { label: "Acciones Seguros Generales", query: "SELECT nemotecnico, count(*) as tenencias, AVG(precio_cierre_clp) as precio_prom FROM generales_acciones GROUP BY nemotecnico ORDER BY tenencias DESC LIMIT 5;" },
              { label: "Solvencia y Balance Generales", query: "SELECT periodo, SUM(total_inversion_m_clp) as total_inversion_m FROM generales_solvencia GROUP BY periodo ORDER BY periodo DESC LIMIT 5;" }
            ],
            tables: [
              { id: "generales_bonos", name: "generales.cartera_bonos", rows: "287k datos", file: "outputs/generales/cartera_bonos.parquet" },
              { id: "generales_bienes_raices", name: "generales.cartera_bienes_raices", rows: "38k datos", file: "outputs/generales/cartera_bienes_raices.parquet" },
              { id: "generales_acciones", name: "generales.cartera_acciones", rows: "17k datos", file: "outputs/generales/cartera_acciones.parquet" },
              { id: "generales_fondos", name: "generales.cartera_fondos", rows: "8.9k datos", file: "outputs/generales/cartera_fondos.parquet" },
              { id: "generales_extranjeros", name: "generales.cartera_extranjeros", rows: "5.6k datos", file: "outputs/generales/cartera_extranjeros.parquet" },
              { id: "generales_solvencia", name: "generales.cartera_solvencia", rows: "60k datos", file: "outputs/generales/cartera_solvencia.parquet" }
            ]
          },
          {
            id: "c1835_gen_derivados",
            type: "circular",
            label: "Circular 1835 · Derivados",
            badge: "4.2k Datos",
            badgeType: "data",
            status: "active",
            sector: "generales",
            open: false,
            chips: [
              { label: "Forwards Generales: Contrapartes", query: "SELECT nombre_contraparte, count(*) as contratos, AVG(precio_forward_pactado) as fwd_pactado FROM generales_forwards GROUP BY nombre_contraparte ORDER BY contratos DESC LIMIT 5;" },
              { label: "Swaps Generales: Tasas y MtM", query: "SELECT nombre_contraparte, count(*) as operaciones, AVG(tasa_contrato_larga) as tasa_larga FROM generales_swaps GROUP BY nombre_contraparte ORDER BY operaciones DESC LIMIT 5;" }
            ],
            tables: [
              { id: "generales_forwards", name: "generales.b7_forwards", rows: "2.8k datos", file: "outputs/generales/b7_forwards.parquet" },
              { id: "generales_swaps", name: "generales.b7_swaps", rows: "1.4k datos", file: "outputs/generales/b7_swaps.parquet" }
            ]
          },
          {
            id: "c1835_gen_repos",
            type: "circular",
            label: "Circular 1835 · Pactos y Repos",
            badge: "275 Datos",
            badgeType: "data",
            status: "active",
            sector: "generales",
            open: false,
            chips: [
              { label: "Repos Generales: Pactos y Tasas", query: "SELECT nombre_contraparte, count(*) as pactos, AVG(tasa_pacto) as tasa_prom FROM generales_repos GROUP BY nombre_contraparte ORDER BY pactos DESC LIMIT 5;" }
            ],
            tables: [
              { id: "generales_repos", name: "generales.b7_repos", rows: "275 datos", file: "outputs/generales/b7_repos.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_ffmm",
    type: "group",
    label: "FONDOS MUTUOS (CMF)",
    badges: [
      { type: "entities", text: "1.156 Entidades", title: "1.156 Fondos Mutuos (AGF) registrados ante la CMF" },
      { type: "data", text: "15k Datos", title: "15k Contratos normalizados de derivados CMF Circular 1333" }
    ],
    status: "active",
    open: false,
    children: [
      {
        id: "sector_ffmm",
        type: "sector",
        label: "Fondos Mutuos (AGF)",
        sector: "ffmm",
        open: false,
        children: [
          {
            id: "c1333_ffmm_cat",
            type: "circular",
            label: "Lista de Entidades",
            badge: "1.156 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "ffmm",
            open: false,
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
            badge: "15k Datos",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            open: false,
            chips: [
              { label: "Futuros Circular 1333", query: "SELECT * FROM ffmm_futuros LIMIT 10;" },
              { label: "Opciones Circular 1333", query: "SELECT * FROM ffmm_opciones LIMIT 10;" }
            ],
            tables: [
              { id: "ffmm_futuros", name: "ffmm.futuros", rows: "11k datos", file: "ffmm/circular_1333_cartera/outputs/ffmm_futu_normalizado.parquet" },
              { id: "ffmm_opciones", name: "ffmm.opciones", rows: "3.7k datos", file: "ffmm/circular_1333_cartera/outputs/ffmm_opci_normalizado.parquet" }
            ]
          },
          {
            id: "eeff_ffmm_2024",
            type: "circular",
            label: "Estados Financieros 2024 (EEFF)",
            badge: "376 Fondos",
            badgeType: "entities",
            status: "active",
            sector: "ffmm",
            open: false,
            chips: [
              { label: "Ranking AUM Fondos Mutuos (M$)", query: "SELECT run_fondo, nombre_fondo, razon_social_agf, patrimonio_aum_m_clp, total_activos_m_clp, utilidad_ejercicio_m_clp FROM ffmm_caratula_eeff_2024 ORDER BY patrimonio_aum_m_clp DESC LIMIT 15;" },
              { label: "Cuadratura Contable Balance FFMM", query: "SELECT run_fondo, nombre_fondo, total_activos_m_clp, total_pasivos_m_clp, patrimonio_aum_m_clp, (total_activos_m_clp - (total_pasivos_m_clp + patrimonio_aum_m_clp)) as dif_cuadratura FROM ffmm_caratula_eeff_2024 WHERE abs(total_activos_m_clp - (total_pasivos_m_clp + patrimonio_aum_m_clp)) > 5.0;" },
              { label: "AUM Consolidado por Administradora (AGF)", query: "SELECT razon_social_agf, count(*) as num_fondos, SUM(patrimonio_aum_m_clp) as total_aum_m_clp, SUM(total_activos_m_clp) as total_activos_m_clp FROM ffmm_caratula_eeff_2024 GROUP BY razon_social_agf ORDER BY total_aum_m_clp DESC;" }
            ],
            tables: [
              { id: "ffmm_caratula_eeff_2024", name: "ffmm.caratula_eeff_2024", rows: "376 fondos", file: "outputs/ffmm/ffmm_caratula_eeff_2024.parquet" }
            ]
          },
          {
            id: "repos_ffmm_2024",
            type: "circular",
            label: "Operaciones REPO · Tabla Literal CMF",
            badge: "Contratos CMF",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            open: false,
            chips: [
              { label: "Top Dealers / Contrapartes REPO FFMM", query: "SELECT nombre_contraparte, count(*) as num_pactos, SUM(saldo_al_cierre_m_clp) as saldo_total_m_clp FROM ffmm_repos_detalle_2024 GROUP BY nombre_contraparte ORDER BY saldo_total_m_clp DESC;" },
              { label: "Contratos REPO por Instrumento Subyacente", query: "SELECT tipo_instrumento, nemotecnico, count(*) as pactos, SUM(saldo_al_cierre_m_clp) as saldo_m_clp FROM ffmm_repos_detalle_2024 GROUP BY tipo_instrumento, nemotecnico ORDER BY saldo_m_clp DESC LIMIT 15;" },
              { label: "Detalle Literal de Contratos REPO Activos", query: "SELECT run_fondo, nombre_fondo, fecha_compra, rut_contraparte, nombre_contraparte, nemotecnico, total_transado_m_clp, fecha_vencimiento, saldo_al_cierre_m_clp FROM ffmm_repos_detalle_2024 ORDER BY saldo_al_cierre_m_clp DESC LIMIT 20;" }
            ],
            tables: [
              { id: "ffmm_repos_detalle_2024", name: "ffmm.repos_detalle_2024", rows: "Contratos literales", file: "outputs/ffmm/ffmm_repos_detalle_2024.parquet" }
            ]
          },
          {
            id: "eeff_ffmm_historico",
            type: "circular",
            label: "EEFF Históricos 2015-2025 (Panel CMF)",
            badge: "2015-2025",
            badgeType: "entities",
            status: "active",
            sector: "ffmm",
            open: false,
            chips: [
              { label: "Evolución AUM Histórico por Año (M$)", query: "SELECT anio, count(*) as fondos_activos, SUM(patrimonio_activo_neto_m_clp) as total_aum_m_clp, SUM(total_activos_m_clp) as total_activos_m_clp FROM ffmm_caratula_eeff_historico GROUP BY anio ORDER BY anio DESC;" },
              { label: "Evolución Cartera a Costo Amortizado vs VR", query: "SELECT anio, SUM(activos_financieros_amortizado_m_clp) as total_amortizado_m_clp, SUM(activos_financieros_vr_m_clp) as total_vr_m_clp FROM ffmm_caratula_eeff_historico GROUP BY anio ORDER BY anio DESC;" },
              { label: "Verificación Cuadratura Contable Histórica", query: "SELECT anio, count(*) as total_fondos, sum(case when cuadre_activo_pasivo_patrimonio then 1 else 0 end) as cuadres_ok FROM ffmm_caratula_eeff_historico GROUP BY anio ORDER BY anio DESC;" }
            ],
            tables: [
              { id: "ffmm_caratula_eeff_historico", name: "ffmm.caratula_eeff_historico", rows: "Panel 2015-2025", file: "outputs/ffmm/ffmm_caratula_eeff_historico.parquet" }
            ]
          },
          {
            id: "repos_ffmm_historico",
            type: "circular",
            label: "Operaciones REPO Históricas 2015-2025",
            badge: "Historial REPO",
            badgeType: "data",
            status: "active",
            sector: "ffmm",
            open: false,
            chips: [
              { label: "Volumen Anual de REPOs por Contraparte (M$)", query: "SELECT anio, nombre_contraparte, count(*) as num_pactos, SUM(saldo_al_cierre_m_clp) as saldo_total_m_clp FROM ffmm_repos_detalle_historico GROUP BY anio, nombre_contraparte ORDER BY anio DESC, saldo_total_m_clp DESC LIMIT 20;" },
              { label: "Evolución Anual del Mercado REPO FFMM", query: "SELECT anio, count(*) as contratos, count(distinct run_fondo) as fondos_activos, SUM(saldo_al_cierre_m_clp) as saldo_total_m_clp FROM ffmm_repos_detalle_historico GROUP BY anio ORDER BY anio DESC;" },
              { label: "Top Instrumentos Subyacentes en REPOs", query: "SELECT tipo_instrumento, nemotecnico, count(*) as num_operaciones, SUM(saldo_al_cierre_m_clp) as saldo_total_m_clp FROM ffmm_repos_detalle_historico GROUP BY tipo_instrumento, nemotecnico ORDER BY saldo_total_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "ffmm_repos_detalle_historico", name: "ffmm.repos_detalle_historico", rows: "Contratos 2015-2025", file: "outputs/ffmm/ffmm_repos_detalle_historico.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_fi",
    type: "group",
    label: "FONDOS DE INVERSION (CMF)",
    badges: [
      { type: "entities", text: "1.677 Entidades", title: "1.677 Fondos de Inversión registrados CMF (990 vigentes, 687 liquidados)" },
      { type: "data", text: "1.8M Datos", title: "Carteras, balances EEFF históricos y operaciones REPO VRC/CRV" }
    ],
    status: "active",
    open: false,
    children: [
      {
        id: "sector_fi",
        type: "sector",
        label: "Fondos de Inversión (Públicos y Privados)",
        sector: "fi",
        open: false,
        children: [
          {
            id: "fi_cat_distincion",
            type: "circular",
            label: "Lista de Entidades & Censo CMF",
            badge: "1.677 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "fi",
            open: false,
            chips: [
              { label: "Censo CMF: Vigentes vs Liquidados", query: "SELECT estado_vigencia, tipo_entidad_desc, count(*) as total_fondos FROM fi_registro_fondos_universo GROUP BY estado_vigencia, tipo_entidad_desc;" },
              { label: "Fondos Rescatables vs No Rescatables", query: "SELECT tipo_entidad_desc, count(*) as total FROM fi_registro_fondos_universo GROUP BY tipo_entidad_desc;" },
              { label: "Directorio de Fondos Vigentes", query: "SELECT run_fondo, nombre_fondo, tipo_entidad_desc, administradora FROM fi_registro_fondos_universo WHERE estado_vigencia = 'Vigente' ORDER BY nombre_fondo LIMIT 15;" }
            ],
            tables: [
              { id: "fi_registro_fondos_universo", name: "fi.registro_fondos_universo", rows: "1.677 fondos censo", file: "outputs/fi/fi_registro_fondos_universo.parquet" },
              { id: "fi_maestro", name: "fi.lista_entidades", rows: "1.129 entidades", file: "fi/cartera_inversiones/outputs/maestro_fondos_inversion.parquet" }
            ]
          },
          {
            id: "eeff_fi_historico",
            type: "circular",
            label: "EEFF Históricos (Panel Auditado CMF)",
            badge: "Panel Histórico",
            badgeType: "entities",
            status: "active",
            sector: "fi",
            open: false,
            chips: [
              { label: "Evolución Patrimonio y Activos FFII (M$)", query: "SELECT anio, count(*) as balances, round(sum(patrimonio_total_m_clp)/1e6, 2) as patrimonio_billones, round(sum(activo_total_m_clp)/1e6, 2) as activo_billones, round(sum(utilidad_ejercicio_m_clp)/1e6, 2) as utilidad_billones FROM fi_caratula_eeff_historico GROUP BY anio ORDER BY anio DESC;" },
              { label: "Efectivo y Activos Financieros en Balance", query: "SELECT anio, round(sum(efectivo_y_equivalentes_m_clp)/1e6, 2) as efectivo_billones, round(sum(activos_financieros_vr_m_clp)/1e6, 2) as vr_billones, round(sum(activos_financieros_amortizado_m_clp)/1e6, 2) as amortizado_billones FROM fi_caratula_eeff_historico GROUP BY anio ORDER BY anio DESC;" },
              { label: "Ranking Fondos por Patrimonio Auditado", query: "SELECT run_fondo, nombre_fondo, anio, round(patrimonio_total_m_clp, 1) as patrimonio_m_clp, round(activo_total_m_clp, 1) as activo_m_clp, round(utilidad_ejercicio_m_clp, 1) as utilidad_m_clp FROM fi_caratula_eeff_historico WHERE anio = 2024 ORDER BY patrimonio_total_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "fi_caratula_eeff_historico", name: "fi.caratula_eeff_historico", rows: "Panel Histórico CMF", file: "outputs/fi/fi_caratula_eeff_historico.parquet" }
            ]
          },
          {
            id: "fi_repos_historico",
            type: "circular",
            label: "Operaciones REPO Históricas · CMF (VRC / CRV)",
            badge: "2.95k Contratos",
            badgeType: "data",
            status: "active",
            sector: "fi",
            open: false,
            chips: [
              { label: "Operaciones REPO por Tipo (VRC vs CRV)", query: "SELECT codigo_operacion, tipo_operacion_desc, count(*) as contratos, round(sum(valorizacion_cierre_m_moneda), 2) as saldo_cierre FROM fi_repos_detalle_historico GROUP BY codigo_operacion, tipo_operacion_desc;" },
              { label: "Top Contrapartes REPO en FFII", query: "SELECT nombre_contraparte, count(*) as contratos, round(avg(tasa_pct), 2) as tasa_media, round(sum(valorizacion_cierre_m_moneda), 2) as total_cierre FROM fi_repos_detalle_historico GROUP BY nombre_contraparte ORDER BY total_cierre DESC LIMIT 10;" },
              { label: "Evolución Anual del Mercado REPO en FFII", query: "SELECT anio, count(*) as contratos, count(distinct run_fondo) as fondos_operando, round(avg(tasa_pct), 2) as tasa_media, round(sum(valorizacion_cierre_m_moneda), 2) as saldo_cierre FROM fi_repos_detalle_historico GROUP BY anio ORDER BY anio DESC;" }
            ],
            tables: [
              { id: "fi_repos_detalle_historico", name: "fi.repos_detalle_historico", rows: "2.95k contratos (2010-2026)", file: "outputs/fi/fi_repos_detalle_historico.parquet" },
              { id: "fi_repos", name: "fi.repos_vrc_crv", rows: "2.66k datos", file: "fi/repos/outputs/fi_repos_vrc_crv.parquet" }
            ]
          },
          {
            id: "luf_cartera_fi",
            type: "circular",
            label: "Cartera de Inversión",
            badge: "920k Datos",
            badgeType: "data",
            status: "active",
            sector: "fi",
            open: false,
            chips: [
              { label: "Top Inversiones Nacionales", query: "SELECT nemotecnico, rut_emisor, sum(valolizacion_al_cierre) as total_m FROM fi_nacional GROUP BY nemotecnico, rut_emisor ORDER BY total_m DESC LIMIT 10;" },
              { label: "Top Inversiones Extranjeras", query: "SELECT nemotecnico, nombre_del_emisor, sum(valolizacion_al_cierre) as total_m FROM fi_extranjera GROUP BY nemotecnico, nombre_del_emisor ORDER BY total_m DESC LIMIT 10;" },
              { label: "Derivados Forwards FFII", query: "SELECT nombre_contraparte, count(*) as contratos FROM fi_derivados GROUP BY nombre_contraparte ORDER BY contratos DESC LIMIT 10;" }
            ],
            tables: [
              { id: "fi_nacional", name: "fi.cartera_nacional", rows: "834k datos", file: "fi/cartera_inversiones/outputs/fi_cartera_nacional.parquet" },
              { id: "fi_extranjera", name: "fi.cartera_extranjera", rows: "67.4k datos", file: "fi/cartera_inversiones/outputs/fi_cartera_extranjera.parquet" },
              { id: "fi_derivados", name: "fi.futuros_forward", rows: "3.6k datos", file: "fi/cartera_inversiones/outputs/fi_futuros_forward.parquet" },
              { id: "fi_metodo_part", name: "fi.metodo_participacion", rows: "14.4k datos", file: "fi/cartera_inversiones/outputs/fi_metodo_participacion.parquet" },
              { id: "fi_opciones", name: "fi.opciones", rows: "1.4k datos", file: "fi/cartera_inversiones/outputs/fi_opciones.parquet" }
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
      { type: "entities", text: "7 Entidades", title: "7 Administradoras de Fondos de Pensiones reguladas por la SPensiones" },
      { type: "data", text: "214k Datos", title: "214.683 registros históricos de inversiones SPensiones" }
    ],
    status: "active",
    open: true,
    children: [
      // MÓDULO 1: CARTERAS DE INVERSIÓN MULTIFONDOS (Patrimonios Autónomos)
      {
        id: "sector_carteras_afp",
        type: "sector",
        label: "Carteras de Inversión Multifondos",
        sector: "afp_carteras",
        open: true,
        children: [
          {
            id: "cat_afp_cartera_activos",
            type: "circular",
            label: "Portafolios Desagregados · Fondos A al E",
            badge: "207k Datos",
            badgeType: "data",
            status: "active",
            sector: "afp_carteras",
            open: true,
            chips: [
              { label: "Tenencia Bonos Soberanos (BTP / BTU)", query: "SELECT nemotecnico, emisor, sum(monto_usd_millones) as total_usd_m FROM afp_cartera_bonos WHERE emisor LIKE '%TESORERIA%' GROUP BY nemotecnico, emisor ORDER BY total_usd_m DESC LIMIT 10;" },
              { label: "Posiciones en Acciones por Emisor", query: "SELECT nemotecnico, emisor, sum(monto_usd_millones) as total_usd_m FROM afp_cartera_acciones GROUP BY nemotecnico, emisor ORDER BY total_usd_m DESC LIMIT 10;" },
              { label: "Inversión por AFP en Bonos (M$ USD)", query: "SELECT nombre_administradora, sum(monto_usd_millones) as total_bonos_usd FROM afp_cartera_bonos GROUP BY nombre_administradora ORDER BY total_bonos_usd DESC;" }
            ],
            tables: [
              { id: "afp_cartera_bonos", name: "afp.cartera_bonos", rows: "168k datos", file: "outputs/pensiones/afp_cartera_bonos.parquet" },
              { id: "afp_cartera_acciones", name: "afp.cartera_acciones", rows: "39.8k datos", file: "outputs/pensiones/afp_cartera_acciones.parquet" }
            ]
          },
          {
            id: "cat_afp_derivados",
            type: "circular",
            label: "Derivados Financieros OTC · SPensiones",
            badge: "7.2k Datos",
            badgeType: "data",
            status: "active",
            sector: "afp_carteras",
            open: false,
            chips: [
              { label: "Swaps por Contraparte Bancaria", query: "SELECT contraparte, count(*) as n_swaps, sum(nocional_usd_millones) as nocional_total_usd_m FROM afp_derivados_swaps GROUP BY contraparte ORDER BY nocional_total_usd_m DESC LIMIT 10;" },
              { label: "Swaps por Tipo y Moneda Indexada", query: "SELECT tipo_derivado, unidad_indexada, count(*) as operaciones, sum(nocional_usd_millones) as total_usd_m FROM afp_derivados_swaps GROUP BY tipo_derivado, unidad_indexada ORDER BY total_usd_m DESC;" },
              { label: "Forwards por Contraparte", query: "SELECT nombre_contraparte, direccion, count(*) as operaciones, sum(nocional_m_usd) as nocional_total_usd FROM afp_derivados_forwards GROUP BY nombre_contraparte, direccion ORDER BY nocional_total_usd DESC LIMIT 10;" }
            ],
            tables: [
              { id: "afp_derivados_swaps", name: "afp.derivados_swaps", rows: "6.6k datos", file: "outputs/pensiones/afp_derivados_swaps.parquet" },
              { id: "afp_derivados_forwards", name: "afp.derivados_forwards", rows: "560 datos", file: "outputs/pensiones/afp_derivados_forwards.parquet" }
            ]
          }
        ]
      },

      // MÓDULO 2: ADMINISTRADORAS (AFP como Empresas)
      {
        id: "sector_afp_corporativo",
        type: "sector",
        label: "Administradoras (AFP como Empresas)",
        sector: "afp_corporativo",
        open: true,
        children: [
          {
            id: "cat_afp_maestro",
            type: "circular",
            label: "Lista de Administradoras y Encaje",
            badge: "7 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "afp_corporativo",
            open: false,
            chips: [
              { label: "Ranking AUM Administrado (USD)", query: "SELECT nombre_fantasia, aum_total_m_usd, participacion_mercado_pct, encaje_requerido_m_usd FROM afp_maestro ORDER BY aum_total_m_usd DESC;" },
              { label: "Afiliados y Comisiones por AFP", query: "SELECT nombre_fantasia, total_afiliados, comision_flujo_pct, grupo_controlador FROM afp_maestro ORDER BY total_afiliados DESC;" },
              { label: "Encaje Obligatorio 1% (M$ USD)", query: "SELECT nombre_fantasia, encaje_requerido_m_usd, aum_total_m_usd FROM afp_maestro ORDER BY encaje_requerido_m_usd DESC;" }
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
      { type: "entities", text: "18 Entidades", title: "18 Bancos comerciales fiscalizados por la CMF (40 entidades históricas)" },
      { type: "data", text: "19k Datos", title: "Balances, Derivados y Repos Bancarios CMF (2008–2026)" }
    ],
    status: "active",
    open: true,
    children: [
      {
        id: "sector_bancos_comercial",
        type: "sector",
        label: "Banca Comercial e Instituciones Supervisadas",
        sector: "bancos",
        open: true,
        children: [
          {
            id: "cat_bancos_maestro",
            type: "circular",
            label: "Lista de Instituciones Bancarias",
            badge: "40 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "bancos",
            open: false,
            chips: [
              { label: "Bancos Comerciales Activos", query: "SELECT codigo_institucion, rut, nombre_fantasia, tipo_licencia, estado FROM bancos_maestro WHERE estado = 'Activo' ORDER BY codigo_institucion;" },
              { label: "Historial de Bancos Fusionados / Cerrados", query: "SELECT codigo_institucion, nombre_fantasia, razon_social, estado FROM bancos_maestro WHERE estado != 'Activo' ORDER BY estado, nombre_fantasia;" }
            ],
            tables: [
              { id: "bancos_maestro", name: "bancos.lista_instituciones", rows: "40 entidades", file: "outputs/bancos/bancos_maestro.parquet" }
            ]
          },
          {
            id: "circ_bancos_asientos",
            type: "circular",
            label: "Asientos Contables Generales",
            badge: "10.2k Datos",
            badgeType: "data",
            status: "active",
            sector: "bancos",
            open: true,
            chips: [
              { label: "Ranking Activos Totales (MM$)", query: "SELECT nombre_banco, total_activos_m_clp, total_pasivos_m_clp, patrimonio_neto_m_clp, activos_m_usd FROM bancos_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM bancos_balance_resumen) AND codigo_institucion != '999' ORDER BY total_activos_m_clp DESC LIMIT 10;" },
              { label: "Ranking Utilidad Neta por Banco", query: "SELECT nombre_banco, utilidad_neta_m_clp, utilidad_m_usd FROM bancos_estado_resultados WHERE periodo = (SELECT MAX(periodo) FROM bancos_estado_resultados) AND codigo_institucion != '999' ORDER BY utilidad_neta_m_clp DESC LIMIT 10;" },
              { label: "ROE y Apalancamiento Financiero", query: "SELECT b.nombre_banco, round(r.utilidad_neta_m_clp / NULLIF(b.patrimonio_neto_m_clp, 0) * 100, 2) as roe_pct, round(b.total_activos_m_clp / NULLIF(b.patrimonio_neto_m_clp, 0), 1) as apalancamiento_x, b.total_activos_m_clp, r.utilidad_neta_m_clp FROM bancos_balance_resumen b JOIN bancos_estado_resultados r ON b.codigo_institucion = r.codigo_institucion AND b.periodo = r.periodo WHERE b.periodo = (SELECT MAX(periodo) FROM bancos_balance_resumen) AND b.codigo_institucion != '999' ORDER BY roe_pct DESC LIMIT 10;" }
            ],
            tables: [
              { id: "bancos_balance_resumen", name: "bancos.balance_general", rows: "5.1k datos", file: "outputs/bancos/bancos_balance_resumen.parquet" },
              { id: "bancos_estado_resultados", name: "bancos.estado_resultados", rows: "5.1k datos", file: "outputs/bancos/bancos_estado_resultados.parquet" }
            ]
          },
          {
            id: "circ_bancos_derivados",
            type: "circular",
            label: "Mercado de Derivados OTC (BCCh)",
            badge: "5.7k Datos",
            badgeType: "data",
            status: "active",
            sector: "bancos",
            open: true,
            chips: [
              { label: "Posición Neta Forward por Contraparte (USD M)", query: "SELECT periodo, contraparte, round(sum(CASE WHEN direccion = 'Compra' THEN monto WHEN direccion = 'Venta' THEN -monto ELSE monto END), 1) as posicion_neta_usd_m FROM bancos_derivados_posicion_vigente WHERE instrumento LIKE '%Forward%' AND moneda = 'USD' GROUP BY periodo, contraparte ORDER BY periodo DESC LIMIT 15;" },
              { label: "Swaps Cámara Promedio (SPC) por Plazo", query: "SELECT periodo, plazo_contractual, round(sum(monto), 1) as nocional_total FROM bancos_derivados_posicion_vigente WHERE instrumento LIKE '%Camara%' GROUP BY periodo, plazo_contractual ORDER BY periodo DESC LIMIT 15;" },
              { label: "Volumen Mensual Transado por Instrumento", query: "SELECT periodo, instrumento, moneda, round(sum(monto), 1) as volumen_transado FROM bancos_derivados_flujos_transados GROUP BY periodo, instrumento, moneda ORDER BY periodo DESC LIMIT 15;" }
            ],
            tables: [
              { id: "bancos_derivados_posicion_vigente", name: "bancos.derivados_posicion_vigente", rows: "2.8k datos", file: "outputs/bancos/bancos_derivados_posicion_vigente.parquet" },
              { id: "bancos_derivados_flujos_transados", name: "bancos.derivados_flujos_transados", rows: "2.8k datos", file: "outputs/bancos/bancos_derivados_flujos_transados.parquet" }
            ]
          },
          {
            id: "circ_bancos_repos",
            type: "circular",
            label: "Pactos y Repos de Liquidez (CMF MB1)",
            badge: "2.9k Datos",
            badgeType: "data",
            status: "active",
            sector: "bancos",
            open: true,
            chips: [
              { label: "Top Prestamistas Netos de Liquidez (Activo Repo MM$)", query: "SELECT periodo, nombre_fantasia, repo_activo_mm_clp, repo_pasivo_mm_clp, repo_neto_mm_clp, repo_activo_mm_usd, posicion_relativa FROM bancos_repos_saldos_series WHERE periodo = (SELECT MAX(periodo) FROM bancos_repos_saldos_series) ORDER BY repo_activo_mm_clp DESC LIMIT 10;" },
              { label: "Top Tomadores de Fondeo Mayorista (Pasivo Repo MM$)", query: "SELECT periodo, nombre_fantasia, repo_activo_mm_clp, repo_pasivo_mm_clp, repo_neto_mm_clp, repo_pasivo_mm_usd, posicion_relativa FROM bancos_repos_saldos_series WHERE periodo = (SELECT MAX(periodo) FROM bancos_repos_saldos_series) ORDER BY repo_pasivo_mm_clp DESC LIMIT 10;" },
              { label: "Evolución de Fondeo Repos por Banco (Últimos 12M)", query: "SELECT periodo, nombre_fantasia, repo_activo_mm_clp, repo_pasivo_mm_clp, repo_neto_mm_clp, total_transado_mm_usd FROM bancos_repos_saldos_series WHERE nombre_fantasia = 'BANCO SANTANDER-CHILE' ORDER BY periodo DESC LIMIT 12;" }
            ],
            tables: [
              { id: "bancos_repos_saldos_series", name: "bancos.repos_saldos_series", rows: "2.9k datos", file: "outputs/bancos/bancos_repos_saldos_series.parquet" }
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
    open: true,
    children: [
      {
        id: "sector_macro_general",
        type: "sector",
        label: "Estadísticas Financieras y Macroeconómicas",
        sector: "macro",
        open: true,
        children: [
          {
            id: "circ_macro_tasas",
            type: "circular",
            label: "Tasas de Interés y Curvas Soberanas",
            badge: "153 Datos",
            badgeType: "data",
            status: "active",
            sector: "macro",
            open: true,
            chips: [
              { label: "Curva Rendimiento BCP vs BCU (Spread 10y-2y)", query: "SELECT periodo, tpm, tib_promedio, bcp_2y, bcp_5y, bcp_10y, bcu_5y, bcu_10y, spread_bcp_10y_2y_bps, inflacion_implicita_5y_breakeven FROM macro_tasas_rendimientos ORDER BY periodo DESC LIMIT 12;" },
              { label: "Evolución TPM vs Tasa Interbancaria (ICP)", query: "SELECT periodo, tpm, tib_promedio, round(tpm - tib_promedio, 3) as spread_tpm_tib, spc_clp_2y FROM macro_tasas_rendimientos ORDER BY periodo DESC LIMIT 24;" },
              { label: "Breakeven de Inflación a 5 y 10 años", query: "SELECT periodo, bcp_5y, bcu_5y, inflacion_implicita_5y_breakeven, bcp_10y, bcu_10y, inflacion_implicita_10y_breakeven FROM macro_tasas_rendimientos WHERE inflacion_implicita_5y_breakeven IS NOT NULL ORDER BY periodo DESC LIMIT 24;" }
            ],
            tables: [
              { id: "macro_tasas_rendimientos", name: "macro.tasas_rendimientos", rows: "153 datos", file: "outputs/macro/macro_tasas_rendimientos.parquet" }
            ]
          },
          {
            id: "circ_macro_divisas",
            type: "circular",
            label: "Mercado Cambiario & Divisas",
            badge: "153 Datos",
            badgeType: "data",
            status: "active",
            sector: "macro",
            open: true,
            chips: [
              { label: "Dólar Observado: Promedio vs Cierre vs Volatilidad", query: "SELECT periodo, usd_clp_promedio, usd_clp_cierre, var_mensual_usd_pct, var_anual_usd_pct, usd_clp_volatilidad_anualizada_pct FROM macro_divisas_mercado ORDER BY periodo DESC LIMIT 15;" },
              { label: "Tipo de Cambio Real Multilateral (TCR vs TCR-5)", query: "SELECT periodo, usd_clp_cierre, tcr_general, tcr_5monedas FROM macro_divisas_mercado WHERE tcr_general IS NOT NULL ORDER BY periodo DESC LIMIT 18;" },
              { label: "Dólar vs Euro Observado y Variación Mensual", query: "SELECT periodo, usd_clp_cierre, var_mensual_usd_pct, eur_clp_cierre, var_mensual_eur_pct FROM macro_divisas_mercado ORDER BY periodo DESC LIMIT 15;" }
            ],
            tables: [
              { id: "macro_divisas_mercado", name: "macro.divisas_mercado", rows: "153 datos", file: "outputs/macro/macro_divisas_mercado.parquet" }
            ]
          },
          {
            id: "circ_macro_precios",
            type: "circular",
            label: "Precios, Actividad y Expectativas",
            badge: "153 Datos",
            badgeType: "data",
            status: "active",
            sector: "macro",
            open: true,
            chips: [
              { label: "Inflación IPC Anual vs Expectativas EEE (11m y 23m)", query: "SELECT periodo, ipc_var_anual, eee_ipc_11m, eee_ipc_23m, desvio_eee_11m_meta_bps FROM macro_precios_actividad WHERE ipc_var_anual IS NOT NULL ORDER BY periodo DESC LIMIT 18;" },
              { label: "IMACEC Total vs No Minero vs Cobre BML", query: "SELECT periodo, imacec_empalmado, imacec_no_minero, imacec_var_anual_pct, cobre_spot_usd_lb, cobre_var_anual_pct FROM macro_precios_actividad WHERE imacec_empalmado IS NOT NULL ORDER BY periodo DESC LIMIT 18;" },
              { label: "Valor de la UF y Variación Mensual", query: "SELECT periodo, uf_cierre, uf_promedio, uf_var_mensual_pct FROM macro_precios_actividad ORDER BY periodo DESC LIMIT 18;" }
            ],
            tables: [
              { id: "macro_precios_actividad", name: "macro.precios_actividad", rows: "153 datos", file: "outputs/macro/macro_precios_actividad.parquet" }
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
      { type: "entities", text: "28 Entidades", title: "28 Empresas de Factoring y Leasing (22 Activas Vigentes + 6 Históricas CMF)" },
      { type: "data", text: "21.2k Datos", title: "Balances IFRS, desglose de efectivo por monedas y morosidad de cartera (2014–2026)" }
    ],
    status: "active",
    open: true,
    children: [
      {
        id: "sector_factoring_leasing",
        type: "sector",
        label: "Intermediación Financiera No Bancaria",
        sector: "factoring_leasing",
        open: true,
        children: [
          {
            id: "cat_fl_maestro",
            type: "circular",
            label: "Lista de Entidades de Factoring y Leasing",
            badge: "28 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "factoring_leasing",
            open: false,
            chips: [
              { label: "Catálogo Oficial por Segmento y Licencia", query: "SELECT rut, razon_social, nombre_fantasia, segmento, tipo_licencia, grupo_controlador, vigente FROM factoring_leasing_maestro ORDER BY vigente DESC, segmento, razon_social;" },
              { label: "Entidades Activas CMF vs Históricas / Canceladas", query: "SELECT vigente, estado, count(*) as total_entidades, string_agg(nombre_fantasia, ', ') as instituciones FROM factoring_leasing_maestro GROUP BY vigente, estado ORDER BY vigente DESC;" },
              { label: "Filiales Bancarias LGB vs Emisores Independientes RVEMI", query: "SELECT tipo_licencia, count(*) as total, string_agg(nombre_fantasia, ', ') as instituciones FROM factoring_leasing_maestro WHERE vigente = 1 GROUP BY tipo_licencia;" },
              { label: "Segmentación por Línea de Negocio", query: "SELECT segmento, count(*) as entidades, sum(es_factoring) as con_factoring, sum(es_leasing_financiero) as con_leasing, sum(es_automotriz) as con_automotriz FROM factoring_leasing_maestro WHERE vigente = 1 GROUP BY segmento;" }
            ],
            tables: [
              { id: "factoring_leasing_maestro", name: "factoring_leasing.maestro", rows: "28 entidades", file: "outputs/factoring_leasing/factoring_leasing_maestro.parquet" }
            ]
          },
          {
            id: "circ_fl_balances",
            type: "circular",
            label: "Balances y Cartera de Crédito",
            badge: "878 Datos",
            badgeType: "data",
            status: "active",
            sector: "factoring_leasing",
            open: true,
            chips: [
              { label: "Ranking Cartera de Crédito (Factoring y Leasing)", query: "SELECT nombre_empresa, cartera_credito_m_clp, cartera_credito_m_usd, total_activos_m_clp, total_pasivos_m_clp, patrimonio_neto_m_clp FROM factoring_leasing_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM factoring_leasing_balance_resumen) ORDER BY cartera_credito_m_clp DESC LIMIT 10;" },
              { label: "Perfil de Deuda: Pasivos Corto vs Largo Plazo", query: "SELECT nombre_empresa, pasivos_corrientes_m_clp, pasivos_no_corrientes_m_clp, total_pasivos_m_clp, round(pasivos_corrientes_m_clp / NULLIF(total_pasivos_m_clp, 0) * 100, 1) as deuda_corto_plazo_pct FROM factoring_leasing_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM factoring_leasing_balance_resumen) ORDER BY total_pasivos_m_clp DESC LIMIT 10;" },
              { label: "Evolución Histórica Cartera (Tanner vs Forum vs Santander)", query: "SELECT periodo, nombre_empresa, cartera_credito_m_clp, cartera_credito_m_usd, total_activos_m_clp FROM factoring_leasing_balance_resumen WHERE nombre_empresa IN ('TANNER SERVICIOS FINANCIEROS S.A.', 'FORUM SERVICIOS FINANCIEROS S.A.', 'SANTANDER CONSUMER FINANCE LIMITADA') ORDER BY periodo DESC, cartera_credito_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "factoring_leasing_balance_resumen", name: "factoring_leasing.balance_resumen", rows: "878 datos", file: "outputs/factoring_leasing/factoring_leasing_balance_resumen.parquet" }
            ]
          },
          {
            id: "circ_fl_nota_efectivo",
            type: "circular",
            label: "Nota Efectivo y Equivalentes (Monedas y Bancos)",
            badge: "2.975 Datos",
            badgeType: "data",
            status: "active",
            sector: "factoring_leasing",
            open: false,
            chips: [
              { label: "Desglose de Efectivo por Divisas (CLP vs USD vs Otras)", query: "SELECT moneda_origen, count(*) as registros, round(sum(monto_mclp)/1000, 1) as total_mm_clp, round(sum(monto_musd)/1000, 1) as total_mm_usd FROM factoring_leasing_nota_efectivo_detalle WHERE periodo = (SELECT MAX(periodo) FROM factoring_leasing_nota_efectivo_detalle) GROUP BY moneda_origen ORDER BY total_mm_clp DESC;" },
              { label: "Pactos de Liquidez (CRV) y Depósitos en el Sector", query: "SELECT periodo, razon_social, concepto, moneda_origen, monto_mclp, monto_musd FROM factoring_leasing_nota_efectivo_detalle WHERE concepto LIKE '%Pactos%' OR concepto LIKE '%Depositos%' ORDER BY periodo DESC, monto_mclp DESC LIMIT 15;" },
              { label: "Ranking de Liquidez en Caja y Bancos por Entidad", query: "SELECT razon_social, round(sum(monto_mclp)/1000, 1) as liquidez_total_mm_clp, round(sum(monto_musd)/1000, 1) as liquidez_total_mm_usd FROM factoring_leasing_nota_efectivo_detalle WHERE periodo = (SELECT MAX(periodo) FROM factoring_leasing_nota_efectivo_detalle) GROUP BY razon_social ORDER BY liquidez_total_mm_clp DESC LIMIT 10;" }
            ],
            tables: [
              { id: "factoring_leasing_nota_efectivo_detalle", name: "factoring_leasing.nota_efectivo_detalle", rows: "2.975 datos", file: "outputs/factoring_leasing/factoring_leasing_nota_efectivo_detalle.parquet" }
            ]
          },
          {
            id: "circ_fl_cartera_morosidad",
            type: "circular",
            label: "Nota Cartera, Morosidad y Provisiones IFRS 9",
            badge: "17.406 Datos",
            badgeType: "data",
            status: "active",
            sector: "factoring_leasing",
            open: false,
            chips: [
              { label: "Cartera Total por Línea de Producto (Factoring vs Leasing vs Automotriz)", query: "SELECT linea_producto, round(sum(cartera_bruta_mclp)/1000, 1) as bruta_mm_clp, round(sum(provisiones_mclp)/1000, 1) as provisiones_mm_clp, round(sum(cartera_neta_mclp)/1000, 1) as neta_mm_clp, round(sum(provisiones_mclp)/NULLIF(sum(cartera_bruta_mclp), 0)*100, 2) as cobertura_pct FROM factoring_leasing_cartera_morosidad_detalle WHERE periodo = (SELECT MAX(periodo) FROM factoring_leasing_cartera_morosidad_detalle) GROUP BY linea_producto ORDER BY bruta_mm_clp DESC;" },
              { label: "Estratificación de Morosidad por Tramos (1-30, 31-60, 61-90, >180 días)", query: "SELECT tramo_morosidad, etapa_ifrs9, round(sum(cartera_bruta_mclp)/1000, 1) as monto_mm_clp, round(sum(provisiones_mclp)/1000, 1) as prov_mm_clp, round(sum(provisiones_mclp)/NULLIF(sum(cartera_bruta_mclp), 0)*100, 1) as cobertura_pct FROM factoring_leasing_cartera_morosidad_detalle WHERE periodo = (SELECT MAX(periodo) FROM factoring_leasing_cartera_morosidad_detalle) GROUP BY tramo_morosidad, etapa_ifrs9 ORDER BY monto_mm_clp DESC;" },
              { label: "Provisiones IFRS 9 por Etapas de Riesgo (Etapa 1, 2 y 3)", query: "SELECT etapa_ifrs9, round(sum(cartera_bruta_mclp)/1000, 1) as exposicion_mm_clp, round(sum(provisiones_mclp)/1000, 1) as provision_mm_clp, round(sum(provisiones_mclp)/NULLIF(sum(cartera_bruta_mclp), 0)*100, 2) as ratio_deterioro_pct FROM factoring_leasing_cartera_morosidad_detalle WHERE periodo = (SELECT MAX(periodo) FROM factoring_leasing_cartera_morosidad_detalle) GROUP BY etapa_ifrs9 ORDER BY etapa_ifrs9;" }
            ],
            tables: [
              { id: "factoring_leasing_cartera_morosidad_detalle", name: "factoring_leasing.cartera_morosidad_detalle", rows: "17.406 datos", file: "outputs/factoring_leasing/factoring_leasing_cartera_morosidad_detalle.parquet" }
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
      { type: "data", text: "5.8k Datos", title: "Balances IFRS, Pactos REPO por contraparte y colaterales (2018 a 2026)" }
    ],
    status: "active",
    open: true,
    children: [
      {
        id: "sector_corredoras_bolsa",
        type: "sector",
        label: "Intermediación de Valores y Corretaje Bursátil",
        sector: "corredoras_bolsa",
        open: true,
        children: [
          {
            id: "cat_cb_maestro",
            type: "circular",
            label: "Lista de Corredoras de Bolsa",
            badge: "120 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "corredoras_bolsa",
            open: false,
            chips: [
              { label: "Catálogo de Corredoras por Grupo Financiero", query: "SELECT rut, nombre_empresa, nombre_fantasia, grupo_financiero, estado_vigencia FROM corredoras_bolsa_registro_universo ORDER BY estado_vigencia DESC, grupo_financiero, nombre_empresa;" },
              { label: "Distribución de Corredoras por Conglomerado", query: "SELECT grupo_financiero, count(*) as total_corredoras, sum(CASE WHEN estado_vigencia = 'Vigente' THEN 1 ELSE 0 END) as vigentes, string_agg(nombre_fantasia, ', ') as instituciones FROM corredoras_bolsa_registro_universo GROUP BY grupo_financiero ORDER BY total_corredoras DESC;" }
            ],
            tables: [
              { id: "corredoras_bolsa_registro_universo", name: "corredoras.universo", rows: "120 entidades", file: "outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.parquet" },
              { id: "corredoras_bolsa_maestro", name: "corredoras.maestro", rows: "120 entidades", file: "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet" }
            ]
          },
          {
            id: "circ_cb_balances",
            type: "circular",
            label: "Balances y Resultados Financieros",
            badge: "621 Balances",
            badgeType: "data",
            status: "active",
            sector: "corredoras_bolsa",
            open: true,
            chips: [
              { label: "Ranking por Activos Totales (MM$ USD)", query: "SELECT b.periodo, m.nombre_fantasia, b.total_activos_m_usd, b.total_pasivos_m_usd, b.patrimonio_m_usd, b.utilidad_ejercicio_m_usd, m.grupo_financiero FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.total_activos_m_usd DESC LIMIT 15;" },
              { label: "Utilidad Neta del Ejercicio (Líderes Bursátiles)", query: "SELECT b.periodo, m.nombre_fantasia, b.utilidad_ejercicio_m_clp, b.utilidad_ejercicio_m_usd, b.total_activos_m_usd FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.utilidad_ejercicio_m_usd DESC LIMIT 15;" },
              { label: "Cartera Comprometida vs Disponible en Corredoras", query: "SELECT b.periodo, m.nombre_fantasia, b.cartera_vr_comprometida_m_clp, b.cartera_vr_disponible_m_clp, b.operaciones_financiamiento_crv_m_clp, b.obligaciones_retrocompra_vrc_m_clp FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.cartera_vr_comprometida_m_clp DESC LIMIT 15;" },
              { label: "Liquidez: Proporción de Caja sobre Activos (%)", query: "SELECT b.periodo, m.nombre_fantasia, b.efectivo_equivalentes_m_usd, b.total_activos_m_usd, round(b.efectivo_equivalentes_m_usd / NULLIF(b.total_activos_m_usd, 0) * 100, 2) as pct_caja_activos FROM corredoras_bolsa_caratula_eeff_historico b JOIN corredoras_bolsa_maestro m ON b.rut = m.rut WHERE b.periodo = (SELECT MAX(periodo) FROM corredoras_bolsa_caratula_eeff_historico) ORDER BY b.efectivo_equivalentes_m_usd DESC LIMIT 15;" }
            ],
            tables: [
              { id: "corredoras_bolsa_caratula_eeff_historico", name: "corredoras.caratula_eeff", rows: "621 balances", file: "outputs/corredoras_bolsa/corredoras_bolsa_caratula_eeff_historico.parquet" },
              { id: "corredoras_bolsa_balance_resumen", name: "corredoras.balance_resumen", rows: "621 balances", file: "outputs/corredoras_bolsa/corredoras_bolsa_balance_resumen.parquet" }
            ]
          },
          {
            id: "circ_cb_repos",
            type: "circular",
            label: "Mercado REPO · Pactos y Colaterales",
            badge: "5.2k Registros",
            badgeType: "data",
            status: "active",
            sector: "corredoras_bolsa",
            open: true,
            chips: [
              { label: "Pactos REPO por Tipo de Contraparte y Plazo (Nivel 2)", query: "SELECT periodo, nombre_empresa, tipo_operacion, segmento_contraparte, tasa_promedio_pct, monto_hasta_7d_m_clp, monto_mas_7d_m_clp, monto_total_m_clp, valor_razonable_garantia_m_clp FROM corredoras_repos_contrapartes_tasas ORDER BY periodo DESC, monto_total_m_clp DESC LIMIT 20;" },
              { label: "Tasa Ponderada REPO por Segmento Institucional", query: "SELECT segmento_contraparte, round(avg(tasa_promedio_pct), 2) as tasa_promedio_anual, round(sum(monto_total_m_clp)/1000, 2) as total_pactado_mm_clp FROM corredoras_repos_contrapartes_tasas WHERE tasa_promedio_pct > 0 GROUP BY segmento_contraparte ORDER BY total_pactado_mm_clp DESC;" },
              { label: "Colaterales y Nemotécnicos Bajo Pacto (Nivel 3)", query: "SELECT periodo, nombre_empresa, nemotecnico, tipo_instrumento, unidades_pactadas, monto_pactado_m_clp, valor_mercado_m_clp FROM corredoras_repos_colaterales_detalle ORDER BY periodo DESC, monto_pactado_m_clp DESC LIMIT 25;" },
              { label: "Top Acciones Chilenas Más Utilizadas como Garantía REPO", query: "SELECT nemotecnico, round(sum(monto_pactado_m_clp)/1000, 2) as total_pactado_mm_clp, round(sum(unidades_pactadas), 0) as total_unidades, count(distinct nombre_empresa) as corredoras_activas FROM corredoras_repos_colaterales_detalle GROUP BY nemotecnico ORDER BY total_pactado_mm_clp DESC LIMIT 15;" },
              { label: "Volumen REPO por Corredora Líder (Banchile vs BTG vs LarrainVial)", query: "SELECT nombre_empresa, round(sum(monto_total_m_clp)/1000, 2) as volumen_total_mm_clp, count(*) as num_contratos FROM corredoras_repos_contrapartes_tasas GROUP BY nombre_empresa ORDER BY volumen_total_mm_clp DESC LIMIT 10;" }
            ],
            tables: [
              { id: "corredoras_repos_contrapartes_tasas", name: "corredoras.repos_contrapartes", rows: "2.6k contratos", file: "outputs/corredoras_bolsa/corredoras_repos_contrapartes_tasas.parquet" },
              { id: "corredoras_repos_colaterales_detalle", name: "corredoras.repos_colaterales", rows: "2.6k colaterales", file: "outputs/corredoras_bolsa/corredoras_repos_colaterales_detalle.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_securitizadoras",
    type: "group",
    label: "SOCIEDADES SECURITIZADORAS (CMF)",
    badges: [
      { type: "entities", text: "16 Entidades", title: "Sociedades anónimas especiales registradas ante la CMF (9 vigentes + 7 históricas)" },
      { type: "data", text: "362 Datos", title: "Balances IFRS corporativos de las gestoras (2014 a 2026)" }
    ],
    status: "active",
    open: true,
    children: [
      {
        id: "sector_securitizadoras",
        type: "sector",
        label: "Sociedades Gestoras de Titulización",
        sector: "securitizadoras",
        open: true,
        children: [
          {
            id: "cat_sec_maestro",
            type: "circular",
            label: "Lista de Sociedades Securitizadoras",
            badge: "16 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "securitizadoras",
            open: false,
            chips: [
              { label: "Catálogo de Securitizadoras (Vigentes vs Históricas)", query: "SELECT rut_completo, razon_social, estado_vigencia, lineas_deuda_registradas FROM securitizadoras_maestro ORDER BY estado_vigencia, razon_social;" },
              { label: "Securitizadoras con Emisiones Activas CMF", query: "SELECT razon_social, rut_completo, lineas_deuda_registradas, cmf_url FROM securitizadoras_maestro WHERE lineas_deuda_registradas > 0 ORDER BY lineas_deuda_registradas DESC;" }
            ],
            tables: [
              { id: "securitizadoras_maestro", name: "securitizadoras.maestro", rows: "16 entidades", file: "outputs/securitizadoras/securitizadoras_maestro.parquet" }
            ]
          },
          {
            id: "circ_sec_balances",
            type: "circular",
            label: "Balances IFRS de Sociedades Gestoras",
            badge: "362 Datos",
            badgeType: "data",
            status: "active",
            sector: "securitizadoras",
            open: true,
            chips: [
              { label: "Ranking por Activos de la Sociedad Gestora (MM$)", query: "SELECT periodo, razon_social, total_activos_m_clp, total_pasivos_m_clp, patrimonio_neto_m_clp, efectivo_y_equivalentes_m_clp FROM securitizadoras_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM securitizadoras_balance_resumen) ORDER BY total_activos_m_clp DESC;" },
              { label: "Utilidad Neta de las Gestoras por Comisiones", query: "SELECT periodo, razon_social, ganancia_perdida_ejercicio_m_clp, total_activos_m_usd, patrimonio_neto_m_usd FROM securitizadoras_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM securitizadoras_balance_resumen) ORDER BY ganancia_perdida_ejercicio_m_clp DESC;" },
              { label: "Evolución Activos Gestora: BCI vs Santander vs BICE", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, efectivo_y_equivalentes_m_clp FROM securitizadoras_balance_resumen WHERE razon_social IN ('BCI SECURITIZADORA S.A.', 'SANTANDER S.A. SOCIEDAD SECURITIZADORA', 'SECURITIZADORA BICE S.A.') ORDER BY periodo DESC, total_activos_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "securitizadoras_balance_resumen", name: "securitizadoras.balance_resumen", rows: "362 datos", file: "outputs/securitizadoras/securitizadoras_balance_resumen.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_patrimonios_separados",
    type: "group",
    label: "PATRIMONIOS SEPARADOS (CMF / Ley 18.045)",
    badges: [
      { type: "entities", text: "18 Vehículos", title: "Patrimonios separados independientes por ley registrados ante la CMF" },
      { type: "data", text: "280+ Datos", title: "Balances clasificados, notas de efectivo con número de nota, repos y mora" }
    ],
    status: "active",
    open: true,
    children: [
      {
        id: "sector_patrimonios_separados",
        type: "sector",
        label: "Vehículos Autónomos e Instrumentos Respaldados",
        sector: "patrimonios_separados",
        open: true,
        children: [
          {
            id: "circ_ps_emisiones",
            type: "circular",
            label: "Emisiones y Programas de Titulización",
            badge: "18 Entidades",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            open: false,
            chips: [
              { label: "Emisiones por Tipo de Activo Colateral Subyacente", query: "SELECT clase_colateral_subyacente, count(*) as total_lineas, string_agg(razon_social_administradora, ', ') as emisores FROM patrimonios_separados_maestro GROUP BY clase_colateral_subyacente ORDER BY total_lineas DESC;" },
              { label: "Líneas de Bonos Securitizados por Moneda y Monto", query: "SELECT numero_inscripcion, fecha_inscripcion, razon_social_administradora, denominacion_emision, moneda, monto_inscrito, clase_colateral_subyacente FROM patrimonios_separados_maestro ORDER BY fecha_inscripcion DESC;" },
              { label: "Programas de Titulización por Securitizadora", query: "SELECT razon_social_administradora, count(*) as emisiones_registradas, string_agg(moneda, ', ') as monedas_utilizadas FROM patrimonios_separados_maestro GROUP BY razon_social_administradora ORDER BY emisiones_registradas DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_maestro", name: "patrimonios.emisiones_lineas", rows: "18 datos", file: "outputs/securitizadoras/patrimonios_separados_maestro.parquet" }
            ]
          },
          {
            id: "circ_ps_balance",
            type: "circular",
            label: "Balances Clasificados y Cuadre Contable",
            badge: "64 Balances",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            open: true,
            chips: [
              { label: "Top Patrimonios Separados por Total Activos (M$ CLP)", query: "SELECT codigo_emision, denominacion_ps, nombre_administradora, periodo, total_activos_mclp, deuda_bonos_largo_plazo_mclp, cuadre_contable_ok FROM patrimonios_separados_balance_resumen WHERE periodo = '2024-12' ORDER BY total_activos_mclp DESC;" },
              { label: "Verificación Cuadre Contable (Activos = Pasivo + Excedentes)", query: "SELECT periodo, COUNT(*) as total_balances, SUM(CASE WHEN cuadre_contable_ok THEN 1 ELSE 0 END) as cuadres_exactos, ROUND(SUM(total_activos_mclp)/1e6, 2) as activos_mm_clp FROM patrimonios_separados_balance_resumen GROUP BY periodo ORDER BY periodo DESC;" },
              { label: "Apalancamiento y Deuda Bonos por Securitizadora (2024)", query: "SELECT nombre_administradora, count(DISTINCT codigo_emision) as vehiculos, ROUND(SUM(total_activos_mclp)/1e3, 1) as activos_totales_m, ROUND(SUM(deuda_bonos_largo_plazo_mclp)/1e3, 1) as bonos_lp_m FROM patrimonios_separados_balance_resumen WHERE periodo = '2024-12' GROUP BY nombre_administradora ORDER BY activos_totales_m DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_balance_resumen", name: "patrimonios.balance_resumen", rows: "64 balances (2022-2024)", file: "outputs/securitizadoras/patrimonios_separados_balance_resumen.parquet" }
            ]
          },
          {
            id: "circ_ps_efectivo",
            type: "circular",
            label: "Efectivo y Equivalentes (con Nota de Origen)",
            badge: "74 Registros",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            open: false,
            chips: [
              { label: "Desglose Efectivo por Nota Contable", query: "SELECT numero_nota, tipo_activo, COUNT(*) as registros, ROUND(SUM(monto_mclp)/1e3, 1) as total_m_clp FROM patrimonios_separados_nota_efectivo_detalle WHERE periodo = '2024-12' GROUP BY numero_nota, tipo_activo ORDER BY total_m_clp DESC;" },
              { label: "Bancos Custodios y Fondos Mutuos", query: "SELECT concepto_item, tipo_activo, COUNT(*) as cuentas, ROUND(SUM(monto_mclp)/1e3, 1) as monto_m_clp FROM patrimonios_separados_nota_efectivo_detalle WHERE periodo = '2024-12' GROUP BY concepto_item, tipo_activo ORDER BY monto_m_clp DESC;" },
              { label: "Liquidez por Administradora", query: "SELECT nombre_administradora, moneda, COUNT(*) as partidas, ROUND(SUM(monto_mclp)/1e3, 1) as total_clp_m, ROUND(SUM(monto_musd)/1e3, 2) as total_usd_m FROM patrimonios_separados_nota_efectivo_detalle GROUP BY nombre_administradora, moneda ORDER BY total_clp_m DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_nota_efectivo_detalle", name: "patrimonios.nota_efectivo_detalle", rows: "74 notas (2022-2024)", file: "outputs/securitizadoras/patrimonios_separados_nota_efectivo_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_repos",
            type: "circular",
            label: "Operaciones Repo y Pactos de Retroventa",
            badge: "74 Pactos",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            open: false,
            chips: [
              { label: "Operaciones Repo por Contraparte (2024)", query: "SELECT contraparte, count(*) as pactos, ROUND(SUM(monto_mclp)/1e3, 1) as monto_total_m, ROUND(AVG(tasa_interes_anual_pct), 2) as tasa_prom_pct FROM patrimonios_separados_repos_detalle WHERE periodo = '2024-12' GROUP BY contraparte ORDER BY monto_total_m DESC;" },
              { label: "Instrumentos Subyacentes en Repos (BTP, BTU, PDBC)", query: "SELECT instrumento_pacto, emisor_subyacente, count(*) as operaciones, ROUND(SUM(monto_mclp)/1e3, 1) as saldo_m_clp FROM patrimonios_separados_repos_detalle GROUP BY instrumento_pacto, emisor_subyacente ORDER BY saldo_m_clp DESC;" },
              { label: "Detalle de Vencimientos y Tasas de Pactos", query: "SELECT codigo_emision, contraparte, instrumento_pacto, tasa_interes_anual_pct, fecha_inicio, fecha_vencimiento, monto_mclp FROM patrimonios_separados_repos_detalle ORDER BY monto_mclp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "patrimonios_separados_repos_detalle", name: "patrimonios.repos_detalle", rows: "74 pactos (2022-2024)", file: "outputs/securitizadoras/patrimonios_separados_repos_detalle.parquet" }
            ]
          },
          {
            id: "circ_ps_morosidad",
            type: "circular",
            label: "Cartera Securitizada, Morosidad y Provisiones",
            badge: "67 Tramos",
            badgeType: "data",
            status: "active",
            sector: "patrimonios_separados",
            open: false,
            chips: [
              { label: "Distribución de Cartera por Tramo de Mora (2024)", query: "SELECT tramo_mora, SUM(numero_deudores) as total_deudores, ROUND(SUM(monto_cartera_mclp)/1e3, 1) as cartera_m_clp, ROUND(SUM(provision_mclp)/1e3, 1) as provision_m_clp FROM patrimonios_separados_cartera_morosidad_detalle WHERE periodo = '2024-12' GROUP BY tramo_mora ORDER BY cartera_m_clp DESC;" },
              { label: "Índice de Cobertura de Provisiones por Tramo", query: "SELECT tramo_mora, ROUND(SUM(monto_cartera_mclp)/1e3, 1) as cartera_m, ROUND(SUM(provision_mclp)/1e3, 1) as provision_m, ROUND(ABS(SUM(provision_mclp)) * 100.0 / NULLIF(SUM(monto_cartera_mclp), 0), 2) as cobertura_pct FROM patrimonios_separados_cartera_morosidad_detalle WHERE tramo_mora NOT IN ('Total') GROUP BY tramo_mora ORDER BY cobertura_pct DESC;" },
              { label: "Morosidad por Vehículo Securitizado", query: "SELECT codigo_emision, nombre_administradora, tramo_mora, numero_deudores, monto_cartera_mclp, provision_mclp FROM patrimonios_separados_cartera_morosidad_detalle WHERE tramo_mora LIKE '%180%' OR tramo_mora LIKE '%90%' ORDER BY monto_cartera_mclp DESC;" }
            ],
            tables: [
              { id: "patrimonios_separados_cartera_morosidad_detalle", name: "patrimonios.cartera_morosidad_detalle", rows: "67 tramos (2022-2024)", file: "outputs/securitizadoras/patrimonios_separados_cartera_morosidad_detalle.parquet" }
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
    open: true,
    children: [
      {
        id: "sector_cooperativas",
        type: "sector",
        label: "Ahorro y Crédito Cooperativo",
        sector: "cooperativas",
        open: true,
        children: [
          {
            id: "cat_coop_maestro",
            type: "circular",
            label: "Catálogo de Cooperativas CAC",
            badge: "7 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "cooperativas",
            open: false,
            chips: [
              { label: "Directorio de Cooperativas Fiscalizadas", query: "SELECT rut, nombre_empresa, nombre_fantasia, sede_matriz, region, estado_vigencia FROM cooperativas_maestro ORDER BY nombre_fantasia;" },
              { label: "Distribución Regional de Cooperativas", query: "SELECT region, count(*) as total_entidades, string_agg(nombre_fantasia, ', ') as instituciones FROM cooperativas_maestro GROUP BY region ORDER BY total_entidades DESC;" }
            ],
            tables: [
              { id: "cooperativas_maestro", name: "cooperativas.maestro", rows: "7 entidades", file: "outputs/cooperativas/cooperativas_maestro.parquet" }
            ]
          },
          {
            id: "circ_coop_balances",
            type: "circular",
            label: "Estados Financieros IFRS y Solvencia",
            badge: "294 Balances",
            badgeType: "data",
            status: "active",
            sector: "cooperativas",
            open: true,
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
            label: "Efectivo y Depósitos en Bancos (Notas EEFF)",
            badge: "122 Registros",
            badgeType: "data",
            status: "active",
            sector: "cooperativas",
            open: true,
            chips: [
              { label: "Composición de Liquidez: Caja vs Cuentas Bancarias (2025)", query: "SELECT periodo, nombre_fantasia, categoria_efectivo, round(sum(monto_m_clp), 1) as total_m_clp, round(sum(monto_m_usd), 2) as total_m_usd FROM cooperativas_nota_efectivo_detalle WHERE periodo = '2025-12' AND categoria_efectivo != 'total_efectivo_bancos' GROUP BY periodo, nombre_fantasia, categoria_efectivo ORDER BY nombre_fantasia, total_m_clp DESC;" },
              { label: "Exposición a Bancos Comerciales Locales (Detacoop)", query: "SELECT periodo, concepto_literal, institucion_contraparte, monto_m_clp, monto_m_usd FROM cooperativas_nota_efectivo_detalle WHERE rut = '70017860-9' AND categoria_efectivo = 'depositos_bancos_locales' ORDER BY periodo DESC, monto_m_clp DESC;" },
              { label: "Evolución de Fondos Disponibles en Coopeuch (2022-2025)", query: "SELECT periodo, concepto_literal, monto_m_clp, monto_m_usd FROM cooperativas_nota_efectivo_detalle WHERE rut = '82878900-7' ORDER BY periodo ASC, monto_m_clp DESC;" },
              { label: "Cheques en Canje y Valores en Cobro del Sector", query: "SELECT periodo, nombre_fantasia, concepto_literal, monto_m_clp, monto_m_usd FROM cooperativas_nota_efectivo_detalle WHERE categoria_efectivo = 'valores_en_cobro' ORDER BY periodo DESC, monto_m_clp DESC;" }
            ],
            tables: [
              { id: "cooperativas_nota_efectivo_detalle", name: "cooperativas.nota_efectivo_detalle", rows: "122 registros", file: "outputs/cooperativas/cooperativas_nota_efectivo_detalle.parquet" }
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
    open: true,
    children: [
      {
        id: "sector_cajas_compensacion",
        type: "sector",
        label: "Crédito Social y Emisión de Bonos Públicos",
        sector: "cajas_compensacion",
        open: true,
        children: [
          {
            id: "cat_ccaf_maestro",
            type: "circular",
            label: "Lista de Cajas de Compensación (CCAF)",
            badge: "6 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "cajas_compensacion",
            open: false,
            chips: [
              { label: "Catálogo CCAF (Vigentes vs Absorbidas)", query: "SELECT rut_completo, nombre_fantasia, estado_vigencia, regulador_mercado_valores, codigo_cmf, lineas_deuda_registradas FROM ccaf_maestro ORDER BY estado_vigencia DESC, nombre_fantasia;" },
              { label: "CCAF Emisoras de Bonos Públicos CMF", query: "SELECT rut_completo, razon_social, codigo_cmf, lineas_deuda_registradas, cmf_url FROM ccaf_maestro WHERE emisor_valores_cmf = true ORDER BY rut;" },
              { label: "CCAF Supervisadas Exclusivamente por SUSESO", query: "SELECT rut_completo, razon_social, domicilio_casa_matriz, suseso_url, observaciones FROM ccaf_maestro WHERE emisor_valores_cmf = false AND estado_vigencia = 'Vigente';" }
            ],
            tables: [
              { id: "ccaf_maestro", name: "ccaf.maestro", rows: "6 entidades", file: "outputs/cajas_compensacion/ccaf_maestro.parquet" }
            ]
          },
          {
            id: "cat_ccaf_caratula",
            type: "circular",
            label: "Balances y Situación Financiera XBRL (2019-2026)",
            badge: "288 Balances",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            open: true,
            chips: [
              { label: "Totales Cierre 2024 por CCAF y Alcance", query: "SELECT ccaf, tipo_eeff, asiento_contable, monto_m_clp FROM ccaf_caratula_totales WHERE ano = 2024 AND mes = 12 ORDER BY ccaf, tipo_eeff, asiento_contable;" },
              { label: "Evolución Activos Totales (2019-2026)", query: "SELECT ano, mes, ccaf, tipo_eeff, monto_m_clp FROM ccaf_caratula_totales WHERE asiento_contable = 'Total de activos' ORDER BY ano DESC, mes DESC, ccaf;" },
              { label: "Utilidad Neta del Sistema (Últimos Años)", query: "SELECT ano, ccaf, tipo_eeff, monto_m_clp FROM ccaf_caratula_totales WHERE asiento_contable = 'Utilidad neta' AND mes = 12 ORDER BY ano DESC, monto_m_clp DESC;" }
            ],
            tables: [
              { id: "ccaf_caratula_totales", name: "ccaf.caratula_totales", rows: "288 balances XBRL (2019-2026)", file: "outputs/cajas_compensacion/ccaf_caratula_totales.parquet" }
            ]
          },
          {
            id: "cat_ccaf_credito_social",
            type: "circular",
            label: "Colocaciones Crédito Social y Provisiones (2019-2026)",
            badge: "476 Series",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            open: true,
            chips: [
              { label: "Cartera Crédito Social Total por CCAF (Último Corte)", query: "SELECT ccaf, tipo_eeff, ROUND(SUM(monto_neto_miles_clp) / 1e3, 1) as total_neto_m_clp, ROUND(SUM(deterioro_provision_miles_clp) / 1e3, 1) as provision_m_clp FROM ccaf_colocaciones_credito_social WHERE periodo = '2026-06' GROUP BY ccaf, tipo_eeff ORDER BY total_neto_m_clp DESC;" },
              { label: "Trabajadores vs Pensionados (Consumo Cierre 2024)", query: "SELECT ccaf, tipo_afiliado, tipo_credito, ROUND(monto_neto_miles_clp / 1e3, 1) as neto_m_clp, ROUND(deterioro_provision_miles_clp / 1e3, 1) as provision_m_clp FROM ccaf_colocaciones_credito_social WHERE periodo = '2024-12' AND tipo_credito = 'Consumo' ORDER BY ccaf, tipo_afiliado;" },
              { label: "Evolución Cartera Total del Sistema (2019-2026)", query: "SELECT periodo, ROUND(SUM(monto_neto_miles_clp) / 1e6, 2) as cartera_neta_mm_clp, ROUND(SUM(deterioro_provision_miles_clp) / 1e6, 2) as provisiones_mm_clp FROM ccaf_colocaciones_credito_social GROUP BY periodo ORDER BY periodo;" },
              { label: "Provisión sobre Cartera Bruta por CCAF (2025-12)", query: "SELECT ccaf, ROUND(SUM(monto_neto_miles_clp)/1e3, 1) as colocaciones_netas_m_clp, ROUND(SUM(deterioro_provision_miles_clp)/1e3, 1) as provisiones_m_clp, ROUND(SUM(deterioro_provision_miles_clp) * 100.0 / NULLIF(SUM(monto_neto_miles_clp + deterioro_provision_miles_clp), 0), 2) as cobertura_pct FROM ccaf_colocaciones_credito_social WHERE periodo = '2025-12' GROUP BY ccaf ORDER BY colocaciones_netas_m_clp DESC;" }
            ],
            tables: [
              { id: "ccaf_colocaciones_credito_social", name: "ccaf.colocaciones_credito_social", rows: "268 líneas atómicas (2019-2026)", file: "outputs/cajas_compensacion/ccaf_colocaciones_credito_social.parquet" }
            ]
          },
          {
            id: "cat_ccaf_nota8_efectivo",
            type: "circular",
            label: "Nota 8: Efectivo y Equivalentes (2019-2026)",
            badge: "213 Registros",
            badgeType: "data",
            status: "active",
            sector: "cajas_compensacion",
            open: true,
            chips: [
              { label: "Desglose Liquidez Cierre 2024", query: "SELECT ccaf, tipo_eeff, concepto, monto_m_clp FROM ccaf_nota8_efectivo_resumen WHERE ano = 2024 AND mes = 12 ORDER BY ccaf, monto_m_clp DESC;" },
              { label: "Ranking Cajas por Inversiones Corto Plazo (2024)", query: "SELECT ccaf, tipo_eeff, monto_m_clp FROM ccaf_nota8_efectivo_resumen WHERE ano = 2024 AND mes = 12 AND concepto LIKE '%Inversiones%' ORDER BY monto_m_clp DESC;" },
              { label: "Top Repos por Corredora 2024", query: "SELECT ccaf, broker_estandarizado, plazo_dias, tasa_anual_pct, valor_contable_m_clp FROM ccaf_nota8_repos_detalle WHERE ano = 2024 ORDER BY valor_contable_m_clp DESC LIMIT 10;" },
              { label: "Ranking Histórico Corredoras en Repos CCAF", query: "SELECT broker_estandarizado, count(*) AS contratos, round(sum(valor_contable_m_clp), 1) AS total_mm_clp, round(avg(plazo_dias), 1) AS plazo_prom_dias, round(avg(tasa_anual_pct), 2) AS tasa_prom_pct FROM ccaf_nota8_repos_detalle GROUP BY broker_estandarizado ORDER BY total_mm_clp DESC;" }
            ],
            tables: [
              { id: "ccaf_nota8_efectivo_resumen", name: "ccaf.nota8_efectivo_resumen", rows: "213 componentes (2019-2026)", file: "outputs/cajas_compensacion/ccaf_nota8_efectivo_resumen.parquet" },
              { id: "ccaf_nota8_dap_detalle", name: "ccaf.nota8_dap_detalle", rows: "52 contratos DAP", file: "outputs/cajas_compensacion/ccaf_nota8_dap_detalle.parquet" },
              { id: "ccaf_nota8_repos_detalle", name: "ccaf.nota8_repos_detalle", rows: "158 operaciones Repos (2018-2024)", file: "outputs/cajas_compensacion/ccaf_nota8_repos_detalle.parquet" }
            ]
          }
        ]
      }
    ]
  },
  {
    id: "group_agf",
    type: "group",
    label: "ADMINISTRADORAS GENERALES DE FONDOS (AGF / LEY 20.712)",
    badges: [
      { type: "entities", text: "68 Entidades", title: "Sociedades gestoras fiduciarias autorizadas bajo la Ley N° 20.712 (LUF)" },
      { type: "data", text: "1.6k Datos", title: "Solvencia, patrimonio regulatorio, cartera propia y comisiones de gestión" }
    ],
    status: "active",
    open: true,
    children: [
      {
        id: "sector_agf",
        type: "sector",
        label: "Sociedades Gestoras de Activos de Terceros",
        sector: "agf",
        open: true,
        children: [
          {
            id: "cat_agf_maestro",
            type: "circular",
            label: "Lista de Administradoras Generales de Fondos",
            badge: "68 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "agf",
            open: true,
            chips: [
              { label: "Catálogo de AGF (Vigentes vs Canceladas)", query: "SELECT rut_completo, razon_social, estado_vigencia, grupo_controlador, fondos_inversion_administrados FROM agf_maestro ORDER BY estado_vigencia, razon_social;" },
              { label: "Ranking de AGF por Fondos de Inversión Administrados", query: "SELECT razon_social, grupo_controlador, fondos_inversion_administrados, cmf_url FROM agf_maestro WHERE fondos_inversion_administrados > 0 ORDER BY fondos_inversion_administrados DESC LIMIT 15;" },
              { label: "AGF por Grupo Financiero Controlador", query: "SELECT grupo_controlador, count(*) as cantidad_agf, sum(fondos_inversion_administrados) as total_fondos FROM agf_maestro WHERE estado_vigencia = 'Vigente' GROUP BY grupo_controlador ORDER BY total_fondos DESC;" }
            ],
            tables: [
              { id: "agf_maestro", name: "agf.maestro", rows: "68 entidades", file: "outputs/agf/agf_maestro.parquet" }
            ]
          },
          {
            id: "circ_agf_balances",
            type: "circular",
            label: "Balances y Resultados IFRS de las Gestoras",
            badge: "1.6k Datos",
            badgeType: "data",
            status: "active",
            sector: "agf",
            open: true,
            chips: [
              { label: "Ranking Activos Propios de las Gestoras (MM$ CLP)", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, efectivo_y_equivalentes_m_clp, cartera_propia_inversiones_m_clp FROM agf_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM agf_balance_resumen) ORDER BY total_activos_m_clp DESC LIMIT 15;" },
              { label: "Ingresos por Comisiones de Administración (Top 10 AGF)", query: "SELECT periodo, razon_social, ingresos_comisiones_m_clp, ganancia_perdida_ejercicio_m_clp, patrimonio_neto_m_clp FROM agf_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM agf_balance_resumen) ORDER BY ingresos_comisiones_m_clp DESC LIMIT 10;" },
              { label: "Cartera Propia de Inversión (Coinversión AGF)", query: "SELECT periodo, razon_social, cartera_propia_inversiones_m_clp, total_activos_m_clp, round(cartera_propia_inversiones_m_clp / NULLIF(total_activos_m_clp, 0) * 100, 1) as pct_cartera_propia FROM agf_balance_resumen WHERE periodo = (SELECT MAX(periodo) FROM agf_balance_resumen) AND cartera_propia_inversiones_m_clp > 0 ORDER BY cartera_propia_inversiones_m_clp DESC LIMIT 15;" },
              { label: "Utilidad Neta del Ejercicio: Banchile vs Santander vs LarrainVial", query: "SELECT periodo, razon_social, ganancia_perdida_ejercicio_m_clp, ingresos_comisiones_m_clp, total_activos_m_usd FROM agf_balance_resumen WHERE razon_social LIKE '%BANCHILE%' OR razon_social LIKE '%SANTANDER%' OR razon_social LIKE '%LARRAIN%' ORDER BY periodo DESC, ingresos_comisiones_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "agf_balance_resumen", name: "agf.balance_resumen", rows: "1.6k datos", file: "outputs/agf/agf_balance_resumen.parquet" }
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
    open: true,
    children: [
      {
        id: "sector_pagos_infraestructura",
        type: "sector",
        label: "Infraestructura Financiera y Redes de Pago",
        sector: "sistemas_pago",
        open: true,
        children: [
          {
            id: "cat_pagos_maestro",
            type: "circular",
            label: "Catálogo de Infraestructuras y Redes",
            badge: "12 Entidades",
            badgeType: "primary",
            status: "active",
            sector: "sistemas_pago",
            open: false,
            chips: [
              { label: "Directorio de Infraestructuras", query: "SELECT codigo_sistema, nombre_comercial, tipo_sistema, supervisor FROM sistemas_pago_maestro ORDER BY codigo_sistema;" },
              { label: "Cámaras y Contrapartes Centrales", query: "SELECT codigo_sistema, razon_social, marco_legal FROM sistemas_pago_maestro WHERE tipo_sistema LIKE '%Cámara%' OR tipo_sistema LIKE '%Contraparte%';" }
            ],
            tables: [
              { id: "sistemas_pago_maestro", name: "pagos.maestro_infraestructuras", rows: "12 entidades", file: "outputs/sistemas_pago/sistemas_pago_maestro.parquet" }
            ]
          },
          {
            id: "cat_pagos_balances",
            type: "circular",
            label: "Balances IFRS Cámaras y Adquirentes",
            badge: "82 Datos",
            badgeType: "primary",
            status: "active",
            sector: "sistemas_pago",
            open: false,
            chips: [
              { label: "Último Cierre IFRS (2026-06)", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, total_activos_m_usd FROM sistemas_pago_balances WHERE periodo = '2026-06';" },
              { label: "Evolución Patrimonial Cámaras", query: "SELECT periodo, razon_social, total_activos_m_clp, total_pasivos_m_clp, patrimonio_neto_m_clp FROM sistemas_pago_balances ORDER BY periodo DESC, total_activos_m_clp DESC LIMIT 15;" }
            ],
            tables: [
              { id: "sistemas_pago_balances", name: "pagos.balances_ifrs", rows: "82 datos", file: "outputs/sistemas_pago/sistemas_pago_balances.parquet" }
            ]
          },
          {
            id: "cat_pagos_estadisticas",
            type: "circular",
            label: "Estadísticas BCCh Liquidación y Tráfico",
            badge: "102 Datos",
            badgeType: "primary",
            status: "active",
            sector: "sistemas_pago",
            open: false,
            chips: [
              { label: "Volumen LBTR y TEF CCA", query: "SELECT periodo, monto_liquidado_lbtr_m_usd, monto_compensado_cca_tef_m_clp, circulante_stock_m_clp FROM sistemas_pago_estadisticas_bcch ORDER BY periodo DESC LIMIT 12;" },
              { label: "Tasas de Tarjetas vs TC", query: "SELECT periodo, tasa_tarjetas_consumo_pct, tasa_tarjetas_comercial_pct, tipo_cambio_usd_clp FROM sistemas_pago_estadisticas_bcch ORDER BY periodo DESC LIMIT 12;" }
            ],
            tables: [
              { id: "sistemas_pago_estadisticas_bcch", name: "pagos.estadisticas_bcch", rows: "102 datos", file: "outputs/sistemas_pago/sistemas_pago_estadisticas_bcch.parquet" }
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
    open: true,
    children: [
      {
        id: "sector_retail_financiero",
        type: "sector",
        label: "Tarjetas Comerciales, Prepago y Matrices de Retail",
        sector: "retail_financiero",
        open: true,
        children: [
          {
            id: "cat_retail_maestro",
            type: "circular",
            label: "Catálogo de Emisores No Bancarios y Matrices",
            badge: "17 Entidades",
            badgeType: "entities",
            status: "active",
            sector: "retail_financiero",
            open: true,
            chips: [
              { label: "Catálogo Emisores y Matrices de Retail", query: "SELECT rut_completo, razon_social, nombre_comercial, tipo_entidad_cmf, grupo_controlador FROM retail_financiero_maestro ORDER BY segmento_mercado, razon_social;" },
              { label: "Emisores por Segmento de Mercado", query: "SELECT segmento_mercado, count(*) as total_entidades FROM retail_financiero_maestro GROUP BY segmento_mercado ORDER BY total_entidades DESC;" },
              { label: "Emisores de Prepago y Crédito Digital", query: "SELECT rut_completo, razon_social, nombre_comercial, tipo_entidad_cmf, comuna FROM retail_financiero_maestro WHERE tipo_entidad_cmf IN ('TCEEM', 'TPEEM');" }
            ],
            tables: [
              { id: "retail_financiero_maestro", name: "retail.maestro", rows: "17 entidades", file: "outputs/retail_financiero/retail_financiero_maestro.parquet" }
            ]
          },
          {
            id: "circ_retail_balances",
            type: "circular",
            label: "Balances y Solvencia IFRS Trimestral",
            badge: "190 Datos",
            badgeType: "data",
            status: "active",
            sector: "retail_financiero",
            open: true,
            chips: [
              { label: "Ranking Activos Totales Cierre Reciente", query: "SELECT periodo, razon_social, total_activos_m_clp, patrimonio_neto_m_clp, total_activos_m_usd FROM retail_financiero_balances WHERE periodo = (SELECT MAX(periodo) FROM retail_financiero_balances) ORDER BY total_activos_m_clp DESC;" },
              { label: "Utilidad Neta del Ejercicio: Falabella vs Cencosud vs Ripley", query: "SELECT periodo, razon_social, ganancia_perdida_ejercicio_m_clp, total_activos_m_clp FROM retail_financiero_balances WHERE razon_social LIKE '%FALABELLA%' OR razon_social LIKE '%CENCOSUD%' OR razon_social LIKE '%RIPLEY%' ORDER BY periodo DESC, total_activos_m_clp DESC LIMIT 15;" },
              { label: "Efectivo y Caja Disponible (MM$ CLP)", query: "SELECT periodo, razon_social, efectivo_y_equivalentes_m_clp, total_activos_m_clp, round(efectivo_y_equivalentes_m_clp / NULLIF(total_activos_m_clp, 0) * 100, 1) as pct_caja FROM retail_financiero_balances WHERE periodo = (SELECT MAX(periodo) FROM retail_financiero_balances) ORDER BY efectivo_y_equivalentes_m_clp DESC;" },
              { label: "Evolución Trimestral Patrimonio Neto (Hites vs Tricot vs ABC)", query: "SELECT periodo, razon_social, patrimonio_neto_m_clp, ganancia_perdida_ejercicio_m_clp FROM retail_financiero_balances WHERE razon_social LIKE '%HITES%' OR razon_social LIKE '%TRICOT%' OR razon_social LIKE '%ABC%' ORDER BY periodo DESC, razon_social LIMIT 18;" }
            ],
            tables: [
              { id: "retail_financiero_balances", name: "retail.balances", rows: "190 datos", file: "outputs/retail_financiero/retail_financiero_balances.parquet" }
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
    open: true,
    children: [
      {
        id: "sector_fintech",
        type: "sector",
        label: "Prestadores de Servicios Financieros y Open Finance",
        sector: "fintech",
        open: true,
        children: [
          {
            id: "cat_fintech_maestro",
            type: "circular",
            label: "Directorio Oficial de Prestadores FinTech",
            badge: "262 Entidades",
            badgeType: "primary",
            status: "active",
            sector: "fintech",
            open: false,
            chips: [
              { label: "Prestadores Vigentes", query: "SELECT rut_completo, razon_social, tipo_persona, servicios_acreditados_total FROM fintech_rpsf_maestro WHERE estado_vigencia = 'Vigente' ORDER BY servicios_acreditados_total DESC, razon_social LIMIT 15;" },
              { label: "Distribución Regional", query: "SELECT region, COUNT(*) AS total_entidades FROM fintech_rpsf_maestro WHERE region != '' GROUP BY region ORDER BY total_entidades DESC;" }
            ],
            tables: [
              { id: "fintech_rpsf_maestro", name: "fintech.rpsf_maestro", rows: "262 entidades", file: "outputs/fintech/fintech_rpsf_maestro.parquet" }
            ]
          },
          {
            id: "cat_fintech_servicios",
            type: "circular",
            label: "Matriz de Servicios Acreditados CMF",
            badge: "262 Datos",
            badgeType: "primary",
            status: "active",
            sector: "fintech",
            open: false,
            chips: [
              { label: "Servicios por Categoría", query: "SELECT servicio_nombre, estado_autorizacion, COUNT(*) AS entidades FROM fintech_servicios_acreditados GROUP BY servicio_nombre, estado_autorizacion ORDER BY entidades DESC;" },
              { label: "Plataformas Transaccionales (SAT / EO)", query: "SELECT rut_completo, razon_social, servicio_nombre, estado_autorizacion FROM fintech_servicios_acreditados WHERE servicio_sigla IN ('SAT', 'EO', 'IIF', 'CIF') ORDER BY servicio_sigla;" }
            ],
            tables: [
              { id: "fintech_servicios_acreditados", name: "fintech.servicios_acreditados", rows: "262 datos", file: "outputs/fintech/fintech_servicios_acreditados.parquet" }
            ]
          },
          {
            id: "cat_fintech_sfa",
            type: "circular",
            label: "Taxonomía Sistema Finanzas Abiertas",
            badge: "262 Datos",
            badgeType: "primary",
            status: "active",
            sector: "fintech",
            open: false,
            chips: [
              { label: "Distribución Roles SFA", query: "SELECT rol_sfa, COUNT(*) AS total_entidades, descripcion_rol FROM fintech_finanzas_abiertas_roles GROUP BY rol_sfa, descripcion_rol ORDER BY total_entidades DESC;" },
              { label: "Iniciadores de Pagos (IIP)", query: "SELECT rut, razon_social, rol_sfa, estandar_interfaz FROM fintech_finanzas_abiertas_roles WHERE rol_sfa = 'IIP';" }
            ],
            tables: [
              { id: "fintech_finanzas_abiertas_roles", name: "fintech.finanzas_abiertas_roles", rows: "262 datos", file: "outputs/fintech/fintech_finanzas_abiertas_roles.parquet" }
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
            const arrowHtml = hasPartitions
              ? `<span class="arrow-slot tbl-arrow-slot" data-target="part_${tbl.id}">${tbl.open ? ICONS.chevronDown : ICONS.chevronRight}</span>`
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
                      <button class="table-action-btn run-btn" data-file="${part.file}" data-name="${tbl.name} (${part.name})" title="Consultar partición en DuckDB">▶ SQL</button>
                    </div>
                  </div>
                `;
              });
            }

            tablesHtml += `
              <div class="table-node-wrapper">
                <div class="tree-row tree-table ${isSelected}" data-table-id="${tbl.id}" data-file="${tbl.file}" data-name="${tbl.name}" data-sector="${circular.sector}">
                  <span class="tree-indent-3"></span>
                  ${arrowHtml}
                  ${ICONS.table}
                  <span class="tree-label table-label">${tbl.name}</span>
                  <span class="table-rows-tag">${tbl.rows}</span>
                  <div class="table-hover-actions">
                    <button class="table-action-btn run-btn" data-file="${tbl.file}" data-name="${tbl.name}" title="Consultar en Terminal DuckDB">▶ SQL</button>
                    <button class="table-action-btn inspect-btn" data-table-id="${tbl.id}" title="Inspeccionar esquema">i</button>
                  </div>
                </div>
                ${hasPartitions ? `<div class="table-partitions-children" id="part_${tbl.id}" style="display: ${tbl.open ? 'block' : 'none'};">${partHtml}</div>` : ""}
              </div>
            `;
          });

          const circOpenClass = circular.open ? "open" : "";
          const circArrow = circular.open ? ICONS.chevronDown : ICONS.chevronRight;
          const circBadgeClass = circular.status === "roadmap"
            ? "badge-roadmap"
            : (circular.badgeType === "entities" ? "badge-entities" : "badge-data");
          const circRoadmapClass = circular.status === "roadmap" ? "roadmap-node" : "";

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

        const sectorOpenClass = sector.open ? "open" : "";
        const sectorArrow = sector.open ? ICONS.chevronDown : ICONS.chevronRight;

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

      const groupOpenClass = group.open ? "open" : "";
      const groupArrow = group.open ? ICONS.chevronDown : ICONS.chevronRight;
      const groupRoadmapClass = group.status === "roadmap" ? "roadmap-node" : "";

      let badgesHtml = "";
      if (group.badges && group.badges.length > 0) {
        badgesHtml = group.badges.map((b) => {
          const bClass = b.type === "entities" ? "badge-entities" : (b.type === "data" ? "badge-data" : "badge-roadmap");
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
          const arrowSlot = node.querySelector(".arrow-slot");
          if (arrowSlot) arrowSlot.innerHTML = ICONS.chevronDown;
        });
      });
    }

    // Toolbar: Colapsar todo
    const colBtn = document.getElementById("btn-collapse-all");
    if (colBtn) {
      colBtn.addEventListener("click", () => {
        document.querySelectorAll(".tree-group, .tree-node").forEach((node) => {
          node.classList.remove("open");
          const arrowSlot = node.querySelector(".arrow-slot");
          if (arrowSlot) arrowSlot.innerHTML = ICONS.chevronRight;
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
        const arrow = header.querySelector(".arrow-slot");
        if (arrow) arrow.innerHTML = isOpen ? ICONS.chevronDown : ICONS.chevronRight;
      });
    });

    // Row de Sector
    document.querySelectorAll(".tree-sector").forEach((row) => {
      row.addEventListener("click", (e) => {
        const node = e.currentTarget.closest(".sector-node");
        const isOpen = node.classList.toggle("open");
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
        const file = e.currentTarget.dataset.file;
        const name = e.currentTarget.dataset.name;
        if (window.ChatTerminal) {
          const sql = file ? `SELECT * FROM '${file}' LIMIT 10;` : `SELECT * FROM '${name}' LIMIT 10;`;
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
          slot.innerHTML = isHidden ? ICONS.chevronDown : ICONS.chevronRight;
        }
      });
    });
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

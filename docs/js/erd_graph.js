/**
 * ERD Graph Renderer (Canvas 2D con Pan, Zoom y Nodos Draggable)
 * Monitor Financiero Chile — Circular 1835 CMF
 */

const ERD_TABLES = [
  {
    id: "seguros_maestro",
    name: "seguros.lista_entidades",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 480,
    y: -80,
    w: 240,
    h: 152,
    rows: "Compañías",
    file: "outputs/seguros/aseguradoras.parquet",
    cols: [
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", pk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "primer_periodo", type: "VARCHAR" },
      { name: "ultimo_periodo", type: "VARCHAR" },
      { name: "meses_reportados", type: "BIGINT" },
      { name: "reporta_ultimo_mes", type: "BOOLEAN" }
    ]
  },
  {
    id: "seguros_renta_fija",
    name: "seguros.renta_fija",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 80,
    y: 160,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/renta_fija/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "serie", type: "VARCHAR" },
      { name: "rut_emisor", type: "VARCHAR" },
      { name: "pais", type: "VARCHAR" },
      { name: "fecha_compra", type: "VARCHAR" },
      { name: "fecha_emision", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_acciones",
    name: "seguros.acciones",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 380,
    y: 160,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/acciones/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "rut_emisor", type: "VARCHAR" },
      { name: "run_fondo", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "serie", type: "VARCHAR" },
      { name: "unidades", type: "DOUBLE" },
      { name: "presencia_bursatil_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "seguros_fondos_mutuos",
    name: "seguros.fondos_mutuos",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 680,
    y: 160,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/fondos_mutuos/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "rut_administradora", type: "VARCHAR" },
      { name: "run_fondo", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "tipo_fondo", type: "VARCHAR" },
      { name: "serie", type: "VARCHAR" },
      { name: "unidades", type: "DOUBLE" }
    ]
  },
  {
    id: "seguros_bienes_raices",
    name: "seguros.bienes_raices",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 980,
    y: 160,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/bienes_raices/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "rol", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "direccion", type: "VARCHAR" },
      { name: "codigo_comuna", type: "VARCHAR" },
      { name: "ciudad", type: "VARCHAR" },
      { name: "monto_arriendo_uf", type: "DOUBLE" }
    ]
  },
  {
    id: "seguros_extranjeros",
    name: "seguros.extranjeros",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 80,
    y: 490,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/extranjeros/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "tipo_registro", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "valor_nominal", type: "DOUBLE" },
      { name: "pais", type: "VARCHAR" },
      { name: "emisor", type: "VARCHAR" },
      { name: "codigo", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_derivados",
    name: "seguros.derivados",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 380,
    y: 490,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/derivados/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "tipo_registro", type: "VARCHAR" },
      { name: "objetivo", type: "VARCHAR" },
      { name: "tipo_operacion", type: "VARCHAR" },
      { name: "folio", type: "VARCHAR" },
      { name: "item", type: "VARCHAR" },
      { name: "fecha_operacion", type: "VARCHAR" },
      { name: "fecha_vencimiento", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_pactos",
    name: "seguros.pactos",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 680,
    y: 490,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/pactos/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "tipo_operacion", type: "VARCHAR" },
      { name: "folio", type: "VARCHAR" },
      { name: "item", type: "VARCHAR" },
      { name: "fecha_operacion", type: "VARCHAR" },
      { name: "fecha_vencimiento", type: "VARCHAR" },
      { name: "tasa_pacto_pct", type: "DOUBLE" },
      { name: "contraparte", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_control_inversiones",
    name: "seguros.control_inversiones",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 980,
    y: 490,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/control_inversiones/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "tipo_inversion", type: "VARCHAR" },
      { name: "valor_final_m_clp", type: "BIGINT" },
      { name: "inversiones_representativas_m_clp", type: "BIGINT" },
      { name: "inversiones_no_representativas_m_clp", type: "BIGINT" },
      { name: "total_costo_amortizado_m_clp", type: "BIGINT" },
      { name: "total_valor_razonable_m_clp", type: "BIGINT" },
      { name: "total_efectivo_equivalente_m_clp", type: "BIGINT" }
    ]
  },
  {
    id: "ffmm_maestro",
    name: "ffmm.lista_entidades",
    sector: "ffmm",
    color: "var(--accent-mint)",
    x: 1340,
    y: -80,
    w: 240,
    h: 148,
    rows: "Fondos",
    file: "outputs/ffmm/maestro_fondos_mutuos.parquet",
    cols: [
      { name: "run_fondo", pk: true, type: "VARCHAR" },
      { name: "nombre_fondo", type: "VARCHAR" },
      { name: "primer_periodo", type: "VARCHAR" },
      { name: "ultimo_periodo", type: "VARCHAR" },
      { name: "meses_reportados", type: "BIGINT" },
      { name: "reporta_ultimo_mes", type: "BOOLEAN" }
    ]
  },
  {
    id: "ffmm_cartera_nacional",
    name: "ffmm.cartera_nacional",
    sector: "ffmm",
    color: "var(--accent-mint)",
    x: 1340,
    y: 90,
    w: 240,
    h: 184,
    rows: "Un archivo por mes",
    file: "outputs/ffmm/cartera_nacional/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "rut_emisor", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "situacion_instrumento", type: "VARCHAR" },
      { name: "valorizacion_miles_mf", type: "DOUBLE" },
      { name: "pct_activo_fondo", type: "DOUBLE" }
    ]
  },
  {
    id: "ffmm_cartera_extranjera",
    name: "ffmm.cartera_extranjera",
    sector: "ffmm",
    color: "var(--accent-mint)",
    x: 1340,
    y: 299,
    w: 240,
    h: 166,
    rows: "Un archivo por año",
    file: "outputs/ffmm/cartera_extranjera/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "nombre_emisor", type: "VARCHAR" },
      { name: "pais_emisor", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "valorizacion_miles_mf", type: "DOUBLE" }
    ]
  },
  {
    id: "ffmm_futuros",
    name: "ffmm.futuros_forwards",
    sector: "ffmm",
    color: "#22577A",
    x: 1340,
    y: 490,
    w: 240,
    h: 184,
    rows: "Un archivo por año",
    file: "outputs/ffmm/futuros_forwards/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "activo_objeto", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "posicion", type: "VARCHAR" },
      { name: "fecha_vencimiento", type: "VARCHAR" },
      { name: "monto_comprometido_miles_mf", type: "DOUBLE" },
      { name: "valorizacion_mercado_miles_mf", type: "DOUBLE" }
    ]
  },
  {
    id: "ffmm_opciones",
    name: "ffmm.opciones",
    sector: "ffmm",
    color: "#22577A",
    x: 1340,
    y: 699,
    w: 240,
    h: 166,
    rows: "Un archivo por año",
    file: "outputs/ffmm/opciones/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "activo_objeto", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "tipo_opcion", type: "VARCHAR" },
      { name: "numero_contratos", type: "DOUBLE" },
      { name: "inversion_primas_miles_mf", type: "DOUBLE" }
    ]
  },
  {
    id: "fi_maestro",
    name: "fi.lista_entidades",
    sector: "fi",
    color: "var(--accent-mint)",
    x: 1620,
    y: -80,
    w: 220,
    h: 145,
    rows: "1.129 fondos",
    file: "outputs/fi/maestro_fondos_inversion.parquet",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "run_fondo", type: "VARCHAR" },
      { name: "nombre_fondo", type: "VARCHAR" },
      { name: "categoria_fondo", type: "VARCHAR" }
    ]
  },
  {
    id: "fi_nacional",
    name: "fi.cartera_nacional",
    sector: "fi",
    color: "var(--accent-mint)",
    x: 1620,
    y: 85,
    w: 220,
    h: 155,
    rows: "834k activos",
    file: "outputs/fi/fi_cartera_nacional.parquet",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "rut_emisor", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "valolizacion_al_cierre", type: "DOUBLE" }
    ]
  },
  {
    id: "fi_extranjera",
    name: "fi.cartera_extranjera",
    sector: "fi",
    color: "var(--accent-contrast)",
    x: 1620,
    y: 260,
    w: 220,
    h: 155,
    rows: "67.4k activos",
    file: "outputs/fi/fi_cartera_extranjera.parquet",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "nombre_del_emisor", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "valolizacion_al_cierre", type: "DOUBLE" }
    ]
  },
  {
    id: "fi_derivados",
    name: "fi.derivados_futuros",
    sector: "fi",
    color: "#696E79",
    x: 1620,
    y: 435,
    w: 220,
    h: 145,
    rows: "3.6k contratos",
    file: "outputs/fi/fi_futuros_forward.parquet",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "nombre_contraparte", type: "VARCHAR" },
      { name: "val_merc_contrato", type: "DOUBLE" }
    ]
  },
  {
    id: "fi_repos",
    name: "fi.repos_vrc_crv",
    sector: "fi",
    color: "#00ADB5",
    x: 1620,
    y: 600,
    w: 220,
    h: 165,
    rows: "Pactos CMF",
    file: "outputs/fi/fi_repos_vrc_crv.parquet",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "codigo_operacion", type: "VARCHAR" },
      { name: "nombre_contraparte", type: "VARCHAR" },
      { name: "tasa_pct", type: "DOUBLE" },
      { name: "valorizacion_cierre", type: "DOUBLE" },
      { name: "emisor_garantia", type: "VARCHAR" }
    ]
  },
  {
    id: "afp_maestro",
    name: "afp.lista_administradoras",
    sector: "pensiones",
    color: "var(--accent-mint)",
    x: 1900,
    y: -80,
    w: 230,
    h: 160,
    rows: "7 administradoras",
    file: "outputs/pensiones/afp_maestro_administradoras.parquet",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "rut_administradora", type: "VARCHAR" },
      { name: "nombre_administradora", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" }
    ]
  },
  {
    id: "bancos_maestro",
    name: "bancos.lista_instituciones",
    sector: "bancos",
    color: "var(--accent-mint)",
    x: 2480,
    y: -80,
    w: 240,
    h: 160,
    rows: "40 instituciones",
    file: "outputs/bancos/bancos_maestro.parquet",
    cols: [
      { name: "codigo_institucion", pk: true, type: "VARCHAR" },
      { name: "rut", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" },
      { name: "tipo_licencia", type: "VARCHAR" },
      { name: "estado", type: "VARCHAR" }
    ]
  },
  {
    id: "bancos_cmf_balance",
    name: "bancos.cmf_balance_b1_b2",
    sector: "bancos",
    color: "#2E7D32",
    x: 2760,
    y: 320,
    w: 280,
    h: 250,
    rows: "CMF B1/B2 validados",
    file: "outputs/bancos/cmf_b1_b2_r1/manifest.json",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "codigo_institucion", type: "VARCHAR" },
      { name: "nombre_institucion_fuente", type: "VARCHAR" },
      { name: "familia_archivo_fuente", type: "VARCHAR" },
      { name: "modelo_cmf", type: "VARCHAR" },
      { name: "nivel_consolidacion", type: "VARCHAR" },
      { name: "codigo_cuenta", type: "VARCHAR" },
      { name: "rubro", type: "VARCHAR" },
      { name: "linea", type: "VARCHAR" },
      { name: "item", type: "VARCHAR" },
      { name: "glosa_cuenta", type: "VARCHAR" },
      { name: "numero_fila_fuente", type: "INTEGER" },
      { name: "importes_fuente_raw", type: "VARCHAR[]" },
      { name: "importes_fuente_decimal", type: "VARCHAR[]" },
      { name: "fuente_url_zip", type: "VARCHAR" },
      { name: "sha256_zip", type: "VARCHAR" }
    ]
  },
  {
    id: "bancos_cmf_resultados",
    name: "bancos.cmf_resultados_r1",
    sector: "bancos",
    color: "#2E7D32",
    x: 2760,
    y: 590,
    w: 280,
    h: 250,
    rows: "CMF R1 validado",
    file: "outputs/bancos/cmf_b1_b2_r1/manifest.json",
    cols: [
      { name: "id", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "codigo_institucion", type: "VARCHAR" },
      { name: "nombre_institucion_fuente", type: "VARCHAR" },
      { name: "familia_archivo_fuente", type: "VARCHAR" },
      { name: "modelo_cmf", type: "VARCHAR" },
      { name: "nivel_consolidacion", type: "VARCHAR" },
      { name: "codigo_cuenta", type: "VARCHAR" },
      { name: "rubro", type: "VARCHAR" },
      { name: "linea", type: "VARCHAR" },
      { name: "item", type: "VARCHAR" },
      { name: "glosa_cuenta", type: "VARCHAR" },
      { name: "numero_fila_fuente", type: "INTEGER" },
      { name: "importes_fuente_raw", type: "VARCHAR[]" },
      { name: "importes_fuente_decimal", type: "VARCHAR[]" },
      { name: "fuente_url_zip", type: "VARCHAR" },
      { name: "sha256_zip", type: "VARCHAR" }
    ]
  },
  {
    id: "macro_tasas_rendimientos",
    name: "macro.tasas_rendimientos",
    sector: "macro",
    color: "#E65100",
    x: 3040,
    y: 110,
    w: 240,
    h: 180,
    rows: "153 periodos",
    file: "outputs/macro/macro_tasas_rendimientos.parquet",
    cols: [
      { name: "periodo", pk: true, type: "VARCHAR" },
      { name: "tpm", type: "DOUBLE" },
      { name: "tib_promedio", type: "DOUBLE" },
      { name: "bcp_2y", type: "DOUBLE" },
      { name: "bcp_5y", type: "DOUBLE" },
      { name: "bcp_10y", type: "DOUBLE" },
      { name: "bcu_5y", type: "DOUBLE" },
      { name: "spread_bcp_10y_2y_bps", type: "DOUBLE" },
      { name: "inflacion_implicita_5y_breakeven", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_divisas_mercado",
    name: "macro.divisas_mercado",
    sector: "macro",
    color: "#F57C00",
    x: 3320,
    y: 110,
    w: 240,
    h: 180,
    rows: "153 periodos",
    file: "outputs/macro/macro_divisas_mercado.parquet",
    cols: [
      { name: "periodo", pk: true, type: "VARCHAR" },
      { name: "usd_clp_promedio", type: "DOUBLE" },
      { name: "usd_clp_cierre", type: "DOUBLE" },
      { name: "var_mensual_usd_pct", type: "DOUBLE" },
      { name: "usd_clp_volatilidad_anualizada_pct", type: "DOUBLE" },
      { name: "eur_clp_cierre", type: "DOUBLE" },
      { name: "tcr_general", type: "DOUBLE" },
      { name: "tcr_5monedas", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_precios_actividad",
    name: "macro.precios_actividad",
    sector: "macro",
    color: "#FF9800",
    x: 3040,
    y: 320,
    w: 240,
    h: 180,
    rows: "153 periodos",
    file: "outputs/macro/macro_precios_actividad.parquet",
    cols: [
      { name: "periodo", pk: true, type: "VARCHAR" },
      { name: "uf_cierre", type: "DOUBLE" },
      { name: "ipc_indice", type: "DOUBLE" },
      { name: "ipc_var_anual", type: "DOUBLE" },
      { name: "imacec_empalmado", type: "DOUBLE" },
      { name: "cobre_spot_usd_lb", type: "DOUBLE" },
      { name: "eee_ipc_11m", type: "DOUBLE" },
      { name: "desvio_eee_11m_meta_bps", type: "DOUBLE" }
    ]
  },
  {
    id: "factoring_leasing_maestro",
    name: "factoring_leasing.lista_entidades",
    sector: "factoring_leasing",
    color: "#D97706",
    x: 3600,
    y: -80,
    w: 240,
    h: 180,
    rows: "28 entidades",
    file: "outputs/factoring_leasing/factoring_leasing_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" },
      { name: "segmento", type: "VARCHAR" },
      { name: "tipo_licencia", type: "VARCHAR" },
      { name: "grupo_controlador", type: "VARCHAR" },
      { name: "vigente", type: "INTEGER" },
      { name: "estado", type: "VARCHAR" }
    ]
  },
  {
    id: "corredoras_bolsa_maestro",
    name: "corredoras.lista_entidades",
    sector: "corredoras_bolsa",
    color: "#8B5CF6",
    x: 3900,
    y: 110,
    w: 240,
    h: 180,
    rows: "47 entidades",
    file: "outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "VARCHAR" },
      { name: "nombre_empresa", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" },
      { name: "tipo_intermediario", type: "VARCHAR" },
      { name: "grupo_financiero", type: "VARCHAR" }
    ]
  },

  {
    id: "securitizadoras_maestro",
    name: "securitizadoras.lista_entidades",
    sector: "securitizadoras",
    color: "#0284C7",
    x: 3900,
    y: 340,
    w: 240,
    h: 175,
    rows: "16 entidades (9 vigentes)",
    file: "outputs/securitizadoras/securitizadoras_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "VARCHAR" },
      { name: "dv", type: "VARCHAR" },
      { name: "rut_completo", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "estado_vigencia", type: "VARCHAR" },
      { name: "tipo_entidad_cmf", type: "VARCHAR" },
      { name: "lineas_deuda_registradas", type: "BIGINT" }
    ]
  },










  {
    id: "patrimonios_separados_balance",
    name: "patrimonios_separados.balance",
    sector: "patrimonios_separados",
    color: "#0F766E",
    x: 4460,
    y: 580,
    w: 270,
    h: 230,
    rows: "358 balances · 7.962 cuentas",
    file: "outputs/securitizadoras/patrimonios_separados_balance.parquet",
    cols: [
      { name: "archivo", pk: true, type: "VARCHAR" },
      { name: "rut_administradora", fk: true, type: "VARCHAR" },
      { name: "codigo_patrimonio", type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "orden_en_balance", type: "BIGINT" },
      { name: "categoria", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "monto_m_clp", type: "BIGINT" }
    ]
  },
  {
    id: "patrimonios_separados_maestro",
    name: "patrimonios_separados.lista_emisiones",
    sector: "patrimonios_separados",
    color: "#075985",
    x: 4460,
    y: 340,
    w: 260,
    h: 200,
    rows: "18 programas CMF",
    file: "outputs/securitizadoras/patrimonios_separados_maestro.parquet",
    cols: [
      { name: "numero_inscripcion", pk: true, type: "VARCHAR" },
      { name: "fecha_inscripcion", type: "VARCHAR" },
      { name: "rut_administradora", fk: true, type: "VARCHAR" },
      { name: "razon_social_administradora", type: "VARCHAR" },
      { name: "denominacion_emision", type: "VARCHAR" },
      { name: "tipo_emision", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "monto_inscrito", type: "DOUBLE" },
      { name: "clase_colateral_subyacente", type: "VARCHAR" }
    ]
  },



  {
    id: "cooperativas_maestro",
    name: "cooperativas.lista_entidades",
    sector: "cooperativas",
    color: "#16A34A",
    x: 4750,
    y: 600,
    w: 260,
    h: 180,
    rows: "7 entidades",
    file: "outputs/cooperativas/cooperativas_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "VARCHAR" },
      { name: "rut_cuerpo", type: "VARCHAR" },
      { name: "dv", type: "VARCHAR" },
      { name: "nombre_empresa", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" },
      { name: "sede_matriz", type: "VARCHAR" },
      { name: "region", type: "VARCHAR" },
      { name: "estado_vigencia", type: "VARCHAR" }
    ]
  },
  {
    id: "ccaf_maestro",
    name: "ccaf.lista_entidades",
    sector: "cajas_compensacion",
    color: "#D97706",
    x: 4750,
    y: 340,
    w: 260,
    h: 210,
    rows: "6 entidades",
    file: "outputs/cajas_compensacion/ccaf_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "BIGINT" },
      { name: "dv", type: "VARCHAR" },
      { name: "rut_completo", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" },
      { name: "regulador_primario", type: "VARCHAR" },
      { name: "regulador_mercado_valores", type: "VARCHAR" },
      { name: "emisor_valores_cmf", type: "BOOLEAN" },
      { name: "estado_vigencia", type: "VARCHAR" }
    ]
  },
  {
    id: "agf_maestro",
    name: "agf.lista_administradoras",
    sector: "agf",
    color: "#6366F1",
    x: 5040,
    y: 200,
    w: 260,
    h: 175,
    rows: "68 entidades",
    file: "outputs/agf/agf_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "BIGINT" },
      { name: "dv", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "grupo_controlador", type: "VARCHAR" },
      { name: "estado_vigencia", type: "VARCHAR" },
      { name: "fondos_inversion_administrados", type: "BIGINT" }
    ]
  },
  {
    id: "agf_balance",
    name: "agf.balance",
    sector: "agf",
    color: "#6366F1",
    x: 5040,
    y: 460,
    w: 260,
    h: 222,
    rows: "71.423 cuentas",
    file: "outputs/agf/agf_balance/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_balance", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "estado_financiero", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor", type: "BIGINT" },
      { name: "repeticion", type: "SMALLINT" }
    ]
  },
  {
    id: "agf_resultados",
    name: "agf.resultados",
    sector: "agf",
    color: "#6366F1",
    x: 5040,
    y: 720,
    w: 260,
    h: 222,
    rows: "58.216 cuentas",
    file: "outputs/agf/agf_resultados/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_balance", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "estado_financiero", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor", type: "BIGINT" },
      { name: "repeticion", type: "SMALLINT" }
    ]
  },
  {
    id: "securitizadoras_balance",
    name: "securitizadoras.balance",
    sector: "securitizadoras",
    color: "#0284C7",
    x: 3900,
    y: 600,
    w: 260,
    h: 222,
    rows: "13.679 cuentas",
    file: "outputs/securitizadoras/securitizadoras_balance/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_balance", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "estado_financiero", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor", type: "BIGINT" },
      { name: "repeticion", type: "SMALLINT" }
    ]
  },
  {
    id: "securitizadoras_resultados",
    name: "securitizadoras.resultados",
    sector: "securitizadoras",
    color: "#0284C7",
    x: 3900,
    y: 860,
    w: 260,
    h: 222,
    rows: "12.290 cuentas",
    file: "outputs/securitizadoras/securitizadoras_resultados/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_balance", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "estado_financiero", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor", type: "BIGINT" },
      { name: "repeticion", type: "SMALLINT" }
    ]
  },
  {
    id: "ccaf_balance",
    name: "ccaf.balance",
    sector: "cajas_compensacion",
    color: "#D97706",
    x: 4750,
    y: 600,
    w: 260,
    h: 222,
    rows: "8.043 cuentas",
    file: "outputs/cajas_compensacion/ccaf_balance/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_balance", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "estado_financiero", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor", type: "BIGINT" },
      { name: "repeticion", type: "SMALLINT" }
    ]
  },
  {
    id: "ccaf_resultados",
    name: "ccaf.resultados",
    sector: "cajas_compensacion",
    color: "#D97706",
    x: 4750,
    y: 860,
    w: 260,
    h: 222,
    rows: "5.506 cuentas",
    file: "outputs/cajas_compensacion/ccaf_resultados/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_balance", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "estado_financiero", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor", type: "BIGINT" },
      { name: "repeticion", type: "SMALLINT" }
    ]
  },
  {
    id: "corredoras_bolsa_balance",
    name: "corredoras.balance",
    sector: "corredoras_bolsa",
    color: "#8B5CF6",
    x: 3900,
    y: 370,
    w: 260,
    h: 204,
    rows: "107.976 cuentas",
    file: "outputs/corredoras_bolsa/corredoras_bolsa_balance/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_intermediario", type: "VARCHAR" },
      { name: "seccion", type: "VARCHAR" },
      { name: "codigo_fecu", pk: true, type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor_miles_clp", type: "BIGINT" }
    ]
  },
  {
    id: "corredoras_bolsa_resultados",
    name: "corredoras.resultados",
    sector: "corredoras_bolsa",
    color: "#8B5CF6",
    x: 3900,
    y: 630,
    w: 260,
    h: 204,
    rows: "77.705 cuentas",
    file: "outputs/corredoras_bolsa/corredoras_bolsa_resultados/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "rut", fk: true, type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_intermediario", type: "VARCHAR" },
      { name: "seccion", type: "VARCHAR" },
      { name: "codigo_fecu", pk: true, type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor_miles_clp", type: "BIGINT" }
    ]
  },


  {
    id: "sistemas_pago_maestro",
    name: "pagos.maestro",
    sector: "sistemas_pago",
    color: "#0F766E",
    x: 5340,
    y: 150,
    w: 260,
    h: 180,
    rows: "12 entidades",
    file: "outputs/sistemas_pago/sistemas_pago_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "BIGINT" },
      { name: "codigo_sistema", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "tipo_sistema", type: "VARCHAR" },
      { name: "supervisor", type: "VARCHAR" }
    ]
  },
  {
    id: "fintech_rpsf_maestro",
    name: "fintech.lista_entidades",
    sector: "fintech",
    color: "#D97706",
    x: 5920,
    y: 150,
    w: 260,
    h: 180,
    rows: "262 entidades",
    file: "outputs/fintech/fintech_rpsf_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "BIGINT" },
      { name: "dv", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "estado_vigencia", type: "VARCHAR" },
      { name: "tipo_persona", type: "VARCHAR" },
      { name: "servicios_acreditados_total", type: "BIGINT" }
    ]
  },
  {
    id: "ccaf_maestro",
    name: "ccaf.lista_entidades",
    sector: "cajas_compensacion",
    color: "#10B981",
    x: 6300,
    y: 100,
    w: 260,
    h: 170,
    rows: "6 entidades",
    file: "outputs/cajas_compensacion/ccaf_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "BIGINT" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" },
      { name: "estado_vigencia", type: "VARCHAR" },
      { name: "emisor_valores_cmf", type: "BOOLEAN" }
    ]
  },

];

// Relaciones entre tablas (Claves Foráneas lógicas)
const ERD_LINKS = [
  { from: "seguros_maestro", to: "seguros_renta_fija", key: "sector, rut_aseguradora" },
  { from: "seguros_maestro", to: "seguros_acciones", key: "sector, rut_aseguradora" },
  { from: "seguros_maestro", to: "seguros_fondos_mutuos", key: "sector, rut_aseguradora" },
  { from: "seguros_maestro", to: "seguros_bienes_raices", key: "sector, rut_aseguradora" },
  { from: "seguros_maestro", to: "seguros_extranjeros", key: "sector, rut_aseguradora" },
  { from: "seguros_maestro", to: "seguros_derivados", key: "sector, rut_aseguradora" },
  { from: "seguros_maestro", to: "seguros_pactos", key: "sector, rut_aseguradora" },
  { from: "seguros_maestro", to: "seguros_control_inversiones", key: "sector, rut_aseguradora" },
  { from: "agf_maestro", to: "fi_maestro", key: "rut_administradora (gestión fiduciaria LUF)" },
  { from: "securitizadoras_maestro", to: "patrimonios_separados_maestro", key: "rut_administradora (administración fiduciaria)" },
  { from: "securitizadoras_maestro", to: "patrimonios_separados_balance", key: "rut = rut_administradora (cuerpo, sin dígito verificador)" },
  { from: "macro_tasas_rendimientos", to: "macro_precios_actividad", key: "periodo (expectativas e inflación)" },
  { from: "bancos_maestro", to: "bancos_cmf_balance", key: "codigo_institucion (código fuente CMF)" },
  { from: "bancos_maestro", to: "bancos_cmf_resultados", key: "codigo_institucion (código fuente CMF)" },
  { from: "agf_maestro", to: "agf_balance", key: "rut" },
  { from: "agf_maestro", to: "agf_resultados", key: "rut" },
  { from: "securitizadoras_maestro", to: "securitizadoras_balance", key: "rut" },
  { from: "securitizadoras_maestro", to: "securitizadoras_resultados", key: "rut" },
  { from: "ccaf_maestro", to: "ccaf_balance", key: "rut" },
  { from: "ccaf_maestro", to: "ccaf_resultados", key: "rut" },
  { from: "corredoras_bolsa_maestro", to: "corredoras_bolsa_balance", key: "rut" },
  { from: "corredoras_bolsa_maestro", to: "corredoras_bolsa_resultados", key: "rut" },
  { from: "ffmm_maestro", to: "ffmm_cartera_nacional", key: "run_fondo" },
  { from: "ffmm_maestro", to: "ffmm_cartera_extranjera", key: "run_fondo" },
  { from: "ffmm_maestro", to: "ffmm_futuros", key: "run_fondo" },
  { from: "ffmm_maestro", to: "ffmm_opciones", key: "run_fondo" },
  { from: "fi_maestro", to: "fi_nacional", key: "run_fondo" },
  { from: "fi_maestro", to: "fi_extranjera", key: "run_fondo" },
  { from: "fi_maestro", to: "fi_derivados", key: "run_fondo" },
  { from: "fi_maestro", to: "fi_repos", key: "run_fondo" },
  { from: "fi_nacional", to: "fi_extranjera", key: "run_fondo, periodo" },
  { from: "fi_nacional", to: "fi_derivados", key: "run_fondo (cobertura)" },
  { from: "fi_nacional", to: "fi_repos", key: "run_fondo (liquidez pactos)" },
];

class ERDGraph {
  /**
   * Resuelve un color de la paleta activa. Acepta un valor CSS literal o
   * var(--token), de modo que los nodos sigan el tema seleccionado.
   */
  resolveColor(value, fallback) {
    if (!value) return fallback;
    const match = /var\((--[a-z0-9-]+)\)/i.exec(value);
    if (!match) return value;
    const resolved = getComputedStyle(document.documentElement)
      .getPropertyValue(match[1])
      .trim();
    return resolved || fallback;
  }

  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    
    // Estado de transformación
    this.scale = 0.85;
    this.offsetX = 40;
    this.offsetY = 30;
    
    // Arrastre e interacción
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.activeNode = null;
    this.hoveredNode = null;
    
    this.tables = JSON.parse(JSON.stringify(ERD_TABLES));
    this.filter = "seguros";
    
    this.initEvents();
    this.resize();
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
    this.autoCenterSector(this.filter);
    this.render();
  }

  initEvents() {
    window.addEventListener("resize", () => this.resize());
    window.addEventListener("mfc:themechange", () => this.render());

    // Zoom con rueda
    this.canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      this.zoom(zoomFactor, e.clientX, e.clientY);
    });

    // Mouse events para Pan y Arrastre de Nodos
    this.canvas.addEventListener("mousedown", (e) => {
      const pos = this.getCanvasCoords(e);
      this.activeNode = this.getNodeAt(pos.x, pos.y);

      if (this.activeNode) {
        this.activeNode._dragOffset = {
          x: pos.x - this.activeNode.x,
          y: pos.y - this.activeNode.y
        };
      } else {
        this.isDragging = true;
        this.dragStart = { x: e.clientX - this.offsetX, y: e.clientY - this.offsetY };
      }
    });

    this.canvas.addEventListener("mousemove", (e) => {
      const pos = this.getCanvasCoords(e);

      if (this.activeNode) {
        this.activeNode.x = pos.x - this.activeNode._dragOffset.x;
        this.activeNode.y = pos.y - this.activeNode._dragOffset.y;
        this.render();
      } else if (this.isDragging) {
        this.offsetX = e.clientX - this.dragStart.x;
        this.offsetY = e.clientY - this.dragStart.y;
        this.render();
      } else {
        const hover = this.getNodeAt(pos.x, pos.y);
        if (hover !== this.hoveredNode) {
          this.hoveredNode = hover;
          this.canvas.style.cursor = hover ? "pointer" : "grab";
          this.render();
        }
      }
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
      this.activeNode = null;
    });

    // Clic en tabla -> Seleccionar para consulta
    this.canvas.addEventListener("click", (e) => {
      const pos = this.getCanvasCoords(e);
      const clickedNode = this.getNodeAt(pos.x, pos.y);
      if (clickedNode) {
        this.onTableSelect(clickedNode);
      }
    });

    // Botones Zoom In / Out
    document.getElementById("btn-zoom-in").addEventListener("click", () => this.zoom(1.2));
    document.getElementById("btn-zoom-out").addEventListener("click", () => this.zoom(0.8));
    document.getElementById("btn-zoom-reset").addEventListener("click", () => {
      this.scale = 0.85;
      this.offsetX = 40;
      this.offsetY = 30;
      this.render();
    });

    // Filtros
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const targetFilter = e.target.dataset.filter;
        this.focusSector(targetFilter);
      });
    });
  }

  autoCenterSector(sectorKey) {
    const visibleTables = this.tables.filter((t) => sectorKey === "todos" || t.sector === sectorKey);
    if (!visibleTables || visibleTables.length === 0) return;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    visibleTables.forEach((t) => {
      minX = Math.min(minX, t.x);
      minY = Math.min(minY, t.y);
      maxX = Math.max(maxX, t.x + t.w);
      maxY = Math.max(maxY, t.y + t.h);
    });

    const bboxW = Math.max(maxX - minX, 200);
    const bboxH = Math.max(maxY - minY, 200);
    const canvasW = this.canvas.width || 800;
    const canvasH = this.canvas.height || 500;

    const scaleX = (canvasW - 90) / bboxW;
    const scaleY = (canvasH - 90) / bboxH;
    this.scale = Math.min(Math.max(Math.min(scaleX, scaleY), 0.55), 1.05);

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    this.offsetX = (canvasW / 2) - (centerX * this.scale);
    this.offsetY = (canvasH / 2) - (centerY * this.scale);
  }

  focusSector(sectorKey) {
    this.filter = sectorKey || "seguros";
    document.querySelectorAll(".filter-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.filter === this.filter);
    });

    this.autoCenterSector(this.filter);
    this.render();
  }

  focusTable(tableId) {
    const table = this.tables.find((t) => t.id === tableId || t.name === tableId);
    if (!table) return;

    if (this.filter !== "todos" && this.filter !== table.sector) {
      this.filter = table.sector;
      document.querySelectorAll(".filter-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.filter === this.filter);
      });
    }

    this.scale = 1.0;
    const canvasW = this.canvas.width || 800;
    const canvasH = this.canvas.height || 500;
    this.offsetX = (canvasW / 2) - ((table.x + table.w / 2) * this.scale);
    this.offsetY = (canvasH / 2) - ((table.y + table.h / 2) * this.scale);
    this.hoveredNode = table;
    this.render();
  }

  getCanvasCoords(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left - this.offsetX) / this.scale,
      y: (e.clientY - rect.top - this.offsetY) / this.scale
    };
  }

  getNodeAt(x, y) {
    for (let i = this.tables.length - 1; i >= 0; i--) {
      const t = this.tables[i];
      if (this.filter !== "todos" && t.sector !== this.filter) continue;
      if (x >= t.x && x <= t.x + t.w && y >= t.y && y <= t.y + t.h) {
        return t;
      }
    }
    return null;
  }

  zoom(factor, clientX, clientY) {
    const prevScale = this.scale;
    this.scale = Math.min(Math.max(0.3, this.scale * factor), 2.5);

    if (clientX && clientY) {
      const rect = this.canvas.getBoundingClientRect();
      const mx = clientX - rect.left;
      const my = clientY - rect.top;
      this.offsetX = mx - (mx - this.offsetX) * (this.scale / prevScale);
      this.offsetY = my - (my - this.offsetY) * (this.scale / prevScale);
    }
    this.render();
  }

  onTableSelect(node) {
    const query = `SELECT * FROM ${node.id} LIMIT 10;`;
    if (window.ChatTerminal) {
      window.ChatTerminal.setQueryInput(query, node.name);
    }
    if (window.DataViewer) {
      window.DataViewer.loadTable(node.id, node.name);
    }
    this.showSchemaModal(node);
  }

  showSchemaModal(node) {
    const modal = document.getElementById("schema-modal");
    if (!modal) return;
    document.getElementById("modal-table-name").textContent = node.name;
    const list = document.getElementById("modal-columns-list");
    list.innerHTML = "";
    node.cols.forEach((col) => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="schema-col-name">${col.name}${col.pk ? " (PK)" : col.fk ? " (FK)" : ""}</span><span class="schema-col-type">${col.type}</span>`;
      list.appendChild(li);
    });

    // Botón de acción rápida para abrir en el Visor de Datos
    let actionContainer = modal.querySelector(".schema-modal-actions");
    if (!actionContainer) {
      actionContainer = document.createElement("div");
      actionContainer.className = "schema-modal-actions";
      modal.appendChild(actionContainer);
    }
    actionContainer.innerHTML = `
      <button class="schema-open-btn" onclick="if(window.switchMainTab) window.switchMainTab('data'); if(window.DataViewer) window.DataViewer.loadTable('${node.id}', '${node.name}'); document.getElementById('schema-modal').classList.remove('visible');">
        Explorar datos de esta tabla &rarr;
      </button>
    `;

    modal.classList.add("visible");
  }

  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    ctx.save();
    ctx.translate(this.offsetX, this.offsetY);
    ctx.scale(this.scale, this.scale);

    // 1. Dibujar Cuadrícula de Fondo Estilo Blueprint
    this.drawGrid(ctx);

    // 2. Dibujar Conexiones Relacionales
    this.drawLinks(ctx);

    // 3. Dibujar Nodos / Tablas
    this.drawNodes(ctx);

    ctx.restore();
  }

  drawGrid(ctx) {
    ctx.save();
    const style = getComputedStyle(document.documentElement);
    ctx.strokeStyle = style.getPropertyValue('--border-color').trim() || "rgba(19, 45, 70, 0.6)";
    ctx.lineWidth = 1;
    const step = 40;
    const minX = -this.offsetX / this.scale - 100;
    const maxX = (this.canvas.width - this.offsetX) / this.scale + 100;
    const minY = -this.offsetY / this.scale - 100;
    const maxY = (this.canvas.height - this.offsetY) / this.scale + 100;

    ctx.beginPath();
    for (let x = Math.floor(minX / step) * step; x < maxX; x += step) {
      ctx.moveTo(x, minY);
      ctx.lineTo(x, maxY);
    }
    for (let y = Math.floor(minY / step) * step; y < maxY; y += step) {
      ctx.moveTo(minX, y);
      ctx.lineTo(maxX, y);
    }
    ctx.stroke();
    ctx.restore();
  }

  drawLinks(ctx) {
    const style = getComputedStyle(document.documentElement);
    const accent = style.getPropertyValue('--accent-mint').trim() || "#01C38D";

    ERD_LINKS.forEach((link) => {
      const fromNode = this.tables.find((t) => t.id === link.from);
      const toNode = this.tables.find((t) => t.id === link.to);
      if (!fromNode || !toNode) return;
      if (this.filter !== "todos" && (fromNode.sector !== this.filter || toNode.sector !== this.filter)) return;

      const p1 = { x: fromNode.x + fromNode.w / 2, y: fromNode.y + fromNode.h / 2 };
      const p2 = { x: toNode.x + toNode.w / 2, y: toNode.y + toNode.h / 2 };

      ctx.save();
      ctx.strokeStyle = accent;
      ctx.globalAlpha = 0.45;
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);

      // Curva Bezier
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      const midX = (p1.x + p2.x) / 2;
      ctx.bezierCurveTo(midX, p1.y, midX, p2.y, p2.x, p2.y);
      ctx.stroke();

      // Punto central conector
      ctx.globalAlpha = 1.0;
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.arc((p1.x + p2.x) / 2, (p1.y + p2.y) / 2, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });
  }

  drawNodes(ctx) {
    const style = getComputedStyle(document.documentElement);
    const bgCard = style.getPropertyValue('--bg-secondary').trim() || "#132D46";
    const accent = style.getPropertyValue('--accent-mint').trim() || "#01C38D";
    const borderColor = style.getPropertyValue('--border-color').trim() || "rgba(105, 110, 121, 0.4)";

    this.tables.forEach((t) => {
      if (this.filter !== "todos" && t.sector !== this.filter) return;
      const isHovered = this.hoveredNode === t;

      ctx.save();
      // Sombra
      ctx.shadowColor = isHovered ? accent : "rgba(0, 0, 0, 0.5)";
      ctx.shadowBlur = isHovered ? 16 : 8;

      // Fondo tarjeta
      ctx.fillStyle = bgCard;
      this.roundRect(ctx, t.x, t.y, t.w, t.h, 8);
      ctx.fill();

      // Borde
      ctx.strokeStyle = isHovered ? accent : borderColor;
      ctx.lineWidth = isHovered ? 2 : 1;
      ctx.stroke();
      ctx.restore();

      // Barra de Cabecera con Color Temático
      ctx.save();
      ctx.fillStyle = this.resolveColor(t.color, accent);
      this.roundRectTop(ctx, t.x, t.y, t.w, 28, 8);
      ctx.fill();

      // Título de la tabla
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "bold 11px Inter, -apple-system, BlinkMacSystemFont, sans-serif";
      ctx.fillText(t.name, t.x + 10, t.y + 18);

      // Badge de filas
      ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
      ctx.font = "10px monospace";
      const badgeW = ctx.measureText(t.rows).width + 8;
      ctx.fillRect(t.x + t.w - badgeW - 6, t.y + 6, badgeW, 16);
      ctx.fillStyle = "#FFFFFF";
      ctx.fillText(t.rows, t.x + t.w - badgeW - 2, t.y + 18);

      // Columnas
      ctx.font = "10px monospace";
      let colY = t.y + 46;
      const style = getComputedStyle(document.documentElement);
      const teal = style.getPropertyValue("--accent-teal").trim() || "#06B6D4";
      const textSecondary = style.getPropertyValue("--text-secondary").trim() || "#9CA3AF";
      const textMuted = style.getPropertyValue("--text-muted").trim() || "#6B7280";
      t.cols.slice(0, 5).forEach((col) => {
        ctx.fillStyle = col.pk ? accent : col.fk ? teal : textSecondary;
        const prefix = col.pk ? "PK " : col.fk ? "FK " : "   ";
        ctx.fillText(prefix + col.name, t.x + 8, colY);

        ctx.fillStyle = textMuted;
        ctx.fillText(col.type, t.x + t.w - 55, colY);
        colY += 16;
      });

      if (t.cols.length > 5) {
        ctx.fillStyle = accent;
        ctx.fillText(`+ ${t.cols.length - 5} columnas mas...`, t.x + 10, colY + 2);
      }

      ctx.restore();
    });
  }

  roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // Barra de cabecera: sólo se redondean las dos esquinas superiores, con el
  // mismo radio de la tarjeta. El trazado anterior arrancaba en (x + r, y) sin
  // unir la esquina superior izquierda y remataba con un chaflán en la inferior
  // izquierda, lo que dejaba la cabecera "cortada" en esa esquina.
  roundRectTop(ctx, x, y, w, h, r) {
    const rad = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + rad, y);
    ctx.lineTo(x + w - rad, y);
    ctx.arcTo(x + w, y, x + w, y + h, rad); // esquina superior derecha
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x, y + h);
    ctx.lineTo(x, y + rad);
    ctx.arcTo(x, y, x + w, y, rad); // esquina superior izquierda
    ctx.closePath();
  }
}

window.ERDGraph = ERDGraph;

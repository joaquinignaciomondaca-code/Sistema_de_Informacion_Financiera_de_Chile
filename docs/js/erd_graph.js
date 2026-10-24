/**
 * ERD Graph Renderer (Canvas 2D con Pan, Zoom y Nodos Draggable)
 * Sistema de Información Financiera de Chile — Circular 1835 CMF
 */

const ERD_TABLES = [
  {
    id: "seguros_lista_entidades",
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
    name: "B.1 INSTRUMENTOS DE RENTA FIJA",
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
      { name: "nro_rut", type: "VARCHAR" },
      { name: "pais", type: "VARCHAR" },
      { name: "fecha_compra", type: "VARCHAR" },
      { name: "fecha_emision", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_acciones",
    name: "B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS Y CUOTAS DE FONDOS DE INVERSIÓN",
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
      { name: "rut", type: "VARCHAR" },
      { name: "run", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "serie", type: "VARCHAR" },
      { name: "unidades", type: "DOUBLE" },
      { name: "pres_bursatil", type: "DOUBLE" }
    ]
  },
  {
    id: "seguros_fondos_mutuos",
    name: "B.3 CUOTAS DE FONDOS MUTUOS",
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
      { name: "run", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "tipo_fondo", type: "VARCHAR" },
      { name: "serie", type: "VARCHAR" },
      { name: "unidades", type: "DOUBLE" }
    ]
  },
  {
    id: "seguros_bienes_raices",
    name: "B.4 BIENES RAICES",
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
      { name: "property_id", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "destino", type: "VARCHAR" },
      { name: "comuna", type: "VARCHAR" },
      { name: "ciudad", type: "VARCHAR" },
      { name: "monto_arriendo_uf", type: "DOUBLE" }
    ]
  },
  {
    id: "seguros_extranjeros",
    name: "B.5 INVERSIONES EN EL EXTRANJERO",
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
      { name: "nombre_del_emisor", type: "VARCHAR" },
      { name: "codigo_individualizacion_o_nemotecnico", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_derivados",
    name: "B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS",
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
      { name: "objetivo_contrato", type: "VARCHAR" },
      { name: "tipo_operacion", type: "VARCHAR" },
      { name: "folio_operacion", type: "VARCHAR" },
      { name: "item_operacion", type: "VARCHAR" },
      { name: "fecha_de_la_operacion", type: "VARCHAR" },
      { name: "fecha_de_vencimiento_del_contrato", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_pactos",
    name: "B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS",
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
      { name: "folio_operacion", type: "VARCHAR" },
      { name: "item_operacion", type: "VARCHAR" },
      { name: "fecha_de_la_operacion", type: "VARCHAR" },
      { name: "fecha_de_vencimiento_del_contrato", type: "VARCHAR" },
      { name: "tasa_pacto", type: "DOUBLE" },
      { name: "nombre", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_control_inversiones",
    name: "B.8 INFORMACION DE CONTROL",
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
      { name: "tipo_de_inversion", type: "VARCHAR" },
      { name: "valor_final_m_clp", type: "BIGINT" },
      { name: "inversiones_representativas_de_rt_pr_m_clp", type: "BIGINT" },
      { name: "inversiones_no_representativas_de_rt_pr_m_clp", type: "BIGINT" },
      { name: "total_costo_amortizado_m_clp", type: "BIGINT" },
      { name: "total_valor_razonable_m_clp", type: "BIGINT" },
      { name: "total_efectivo_equivalente_m_clp", type: "BIGINT" }
    ]
  },
  {
    id: "seguros_otras_inversiones",
    name: "B.6 OTRAS INVERSIONES",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 80,
    y: 820,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/otras_inversiones/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "codigo_o_nombre_de_la_inversion", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "pais", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "unidad_monetaria", type: "VARCHAR" },
      { name: "valor_costo_actualizado_m_clp", type: "BIGINT" },
      { name: "depreciacion_acumulada_m_clp", type: "BIGINT" }
    ]
  },
  {
    id: "seguros_tablas_descriptores",
    name: "B.9 TABLAS DE DESCRIPTORES",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 380,
    y: 820,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/tablas_descriptores/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "rut_del_emisor", type: "VARCHAR" },
      { name: "codigo_nemotecnico", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "fecha_emision", type: "VARCHAR" },
      { name: "tasa_emision", type: "DOUBLE" },
      { name: "tasa_descto", type: "DOUBLE" },
      { name: "unidad_monetaria", type: "VARCHAR" }
    ]
  },
  {
    id: "seguros_tablas_desarrollo",
    name: "B.10 TABLAS DE DESARROLLO",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 680,
    y: 820,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/tablas_desarrollo/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "rut_del_emisor", type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "nro_cupon", type: "BIGINT" },
      { name: "fecha_vcto_cupon", type: "VARCHAR" },
      { name: "interes", type: "DOUBLE" },
      { name: "amortizacion", type: "DOUBLE" },
      { name: "saldo_insoluto", type: "DOUBLE" }
    ]
  },
  {
    id: "seguros_flujos_activos_elegibles",
    name: "B.11 FLUJOS DE ACTIVOS ELEGIBLES",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 980,
    y: 820,
    w: 240,
    h: 216,
    rows: "Mensual",
    file: "outputs/seguros/flujos_activos_elegibles/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", fk: true, type: "VARCHAR" },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "circular_aplicada", type: "BIGINT" },
      { name: "tipo_de_informacion", type: "VARCHAR" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "tramo_1_uf", type: "DOUBLE" },
      { name: "tramo_2_uf", type: "DOUBLE" },
      { name: "tramo_3_uf", type: "DOUBLE" },
      { name: "tramo_4_uf", type: "DOUBLE" }
    ]
  },
  {
    id: "ffmm_lista_entidades",
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
    id: "ffmm_balance",
    name: "ffmm.balance",
    sector: "ffmm",
    color: "var(--accent-mint)",
    x: 1340,
    y: 890,
    w: 240,
    h: 184,
    rows: "Un archivo por año",
    file: "outputs/ffmm/ffmm_balance/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nombre_fondo", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "orden", pk: true, type: "INTEGER" },
      { name: "codigo_cuenta", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor_miles_mf", type: "BIGINT" }
    ]
  },
  {
    id: "ffmm_resultados",
    name: "ffmm.resultados",
    sector: "ffmm",
    color: "var(--accent-mint)",
    // Estaba en (1340, 1099) y quedaba debajo de las dos tarjetas de seguros
    // que llegan hasta x=1540. Baja al hueco libre bajo esa rejilla.
    x: 1340,
    y: 1630,
    w: 240,
    h: 184,
    rows: "Un archivo por año",
    file: "outputs/ffmm/ffmm_resultados/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nombre_fondo", type: "VARCHAR" },
      { name: "moneda", type: "VARCHAR" },
      { name: "orden", pk: true, type: "INTEGER" },
      { name: "codigo_cuenta", type: "VARCHAR" },
      { name: "cuenta", type: "VARCHAR" },
      { name: "valor_miles_mf", type: "BIGINT" }
    ]
  },
  {
    id: "fi_lista_entidades",
    name: "fi.lista_entidades",
    sector: "fi",
    color: "var(--accent-mint)",
    x: 1620,
    y: -80,
    w: 240,
    h: 148,
    rows: "Fondos",
    file: "outputs/fi/maestro_fondos_inversion.parquet",
    cols: [
      { name: "run_fondo", pk: true, type: "VARCHAR" },
      { name: "nombre_fondo", type: "VARCHAR" },
      { name: "administradora", type: "VARCHAR" },
      { name: "moneda_funcional", type: "VARCHAR" },
      { name: "ultimo_periodo_cartera", type: "VARCHAR" }
    ]
  },
  {
    id: "fi_cartera_nacional",
    name: "fi.cartera_nacional",
    sector: "fi",
    color: "var(--accent-mint)",
    x: 1620,
    y: 90,
    w: 240,
    h: 176,
    rows: "Un archivo por trimestre",
    file: "outputs/fi/cartera_nacional/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "nemotecnico", type: "VARCHAR" },
      { name: "rut_emisor", type: "VARCHAR" },
      { name: "emisor_tipo", type: "VARCHAR" },
      { name: "rut_omitido_por_ley", type: "BOOLEAN" },
      { name: "tipo_instrumento", type: "VARCHAR" },
      { name: "valorizacion_miles_mf", type: "DOUBLE" }
    ]
  },
  {
    id: "fi_cartera_extranjera",
    name: "fi.cartera_extranjera",
    sector: "fi",
    color: "var(--accent-contrast)",
    x: 1620,
    y: 280,
    w: 240,
    h: 166,
    rows: "Un archivo por año",
    file: "outputs/fi/cartera_extranjera/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "isin", type: "VARCHAR" },
      { name: "nombre_emisor", type: "VARCHAR" },
      { name: "pais_emisor", type: "VARCHAR" },
      { name: "valorizacion_miles_mf", type: "DOUBLE" }
    ]
  },
  {
    id: "fi_futuros",
    name: "fi.futuros_forwards",
    sector: "fi",
    color: "#696E79",
    x: 1620,
    y: 470,
    w: 240,
    h: 148,
    rows: "Un archivo por año",
    file: "outputs/fi/futuros_forwards/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "activo_objeto", type: "VARCHAR" },
      { name: "contraparte", type: "VARCHAR" },
      { name: "valor_mercado_miles_mf", type: "DOUBLE" }
    ]
  },
  {
    id: "fi_pactos",
    name: "fi.pactos",
    sector: "fi",
    color: "#00ADB5",
    x: 1620,
    y: 640,
    w: 240,
    h: 166,
    rows: "Un archivo por año",
    file: "outputs/fi/pactos/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "run_fondo", fk: true, type: "VARCHAR" },
      { name: "tipo_operacion", type: "VARCHAR" },
      { name: "contraparte", type: "VARCHAR" },
      { name: "tasa_pacto_pct", type: "DOUBLE" },
      { name: "valorizacion_cierre_miles_mf", type: "DOUBLE" }
    ]
  },
  {
    id: "afp_lista_entidades",
    name: "afp.lista_entidades",
    sector: "pensiones",
    color: "var(--accent-mint)",
    x: 5790,
    y: -80,
    w: 230,
    h: 160,
    rows: "7 administradoras",
    file: "outputs/pensiones/afp_maestro_administradoras.parquet",
    cols: [
      { name: "rut_administradora", pk: true, type: "VARCHAR" },
      { name: "nombre_administradora", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" }
    ]
  },
  {
    id: "bancos_lista_entidades",
    name: "bancos.lista_entidades",
    sector: "bancos",
    color: "var(--accent-mint)",
    x: 2480,
    y: -80,
    w: 240,
    h: 160,
    rows: "41 instituciones · 20 vigentes",
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
    id: "bancos_balance",
    name: "bancos.balance",
    sector: "bancos",
    color: "#2E7D32",
    x: 2760,
    y: 320,
    w: 280,
    h: 250,
    rows: "CMF B1/B2 validados",
    file: "outputs/bancos/cmf_b1_b2_r1/manifest.json",
    cols: [
      { name: "periodo", pk: true, type: "VARCHAR" },
      { name: "codigo_institucion", pk: true, type: "VARCHAR" },
      { name: "rut", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "codigo_cuenta", pk: true, type: "VARCHAR" },
      { name: "glosa_cuenta", type: "VARCHAR" },
      { name: "tipo_linea", type: "VARCHAR" },
      { name: "importe_clp", type: "BIGINT" },
      { name: "importes_fuente_raw", type: "VARCHAR[]" },
      { name: "familia_archivo_fuente", type: "VARCHAR" },
      { name: "modelo_cmf", pk: true, type: "VARCHAR" },
      { name: "nivel_consolidacion", type: "VARCHAR" },
      { name: "numero_fila_fuente", type: "BIGINT" }
    ]
  },
  {
    id: "bancos_resultados",
    name: "bancos.resultados",
    sector: "bancos",
    color: "#2E7D32",
    x: 2760,
    y: 590,
    w: 280,
    h: 250,
    rows: "CMF R1 validado · descarga filtrada",
    file: "outputs/bancos/resultados_r1/manifest.json",
    cols: [
      { name: "periodo", pk: true, type: "VARCHAR" },
      { name: "codigo_institucion", pk: true, type: "VARCHAR" },
      { name: "rut", type: "VARCHAR" },
      { name: "razon_social", type: "VARCHAR" },
      { name: "codigo_cuenta", pk: true, type: "VARCHAR" },
      { name: "glosa_cuenta", type: "VARCHAR" },
      { name: "tipo_linea", type: "VARCHAR" },
      { name: "importe_clp", type: "BIGINT" },
      { name: "importes_fuente_raw", type: "VARCHAR[]" },
      { name: "familia_archivo_fuente", type: "VARCHAR" },
      { name: "modelo_cmf", pk: true, type: "VARCHAR" },
      { name: "nivel_consolidacion", type: "VARCHAR" },
      { name: "numero_fila_fuente", type: "BIGINT" }
    ]
  },
  // <macro:inicio>
  {
    id: "macro_tasas_corto_plazo",
    name: "macro.tasas_corto_plazo",
    sector: "macro",
    color: "#E65100",
    x: 3760,
    y: 110,
    w: 250,
    h: 116,
    rows: "3.187 días",
    file: "outputs/macro/macro_tasas_corto_plazo.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "tpm_pct", type: "DOUBLE" },
      { name: "tib_promedio_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_swaps_camara",
    name: "macro.swaps_camara",
    sector: "macro",
    color: "#E65100",
    x: 4050,
    y: 110,
    w: 250,
    h: 170,
    rows: "3.200 días",
    file: "outputs/macro/macro_swaps_camara.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "swap_camara_pesos_90_dias_pct", type: "DOUBLE" },
      { name: "swap_camara_pesos_180_dias_pct", type: "DOUBLE" },
      { name: "swap_camara_pesos_360_dias_pct", type: "DOUBLE" },
      { name: "swap_camara_pesos_2_anos_pct", type: "DOUBLE" },
      { name: "swap_camara_uf_1_ano_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_curva_bonos_pesos",
    name: "macro.curva_bonos_pesos",
    sector: "macro",
    color: "#E65100",
    x: 3760,
    y: 256,
    w: 250,
    h: 134,
    rows: "3.169 días",
    file: "outputs/macro/macro_curva_bonos_pesos.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "rendimiento_bono_pesos_2_anos_pct", type: "DOUBLE" },
      { name: "rendimiento_bono_pesos_5_anos_pct", type: "DOUBLE" },
      { name: "rendimiento_bono_pesos_10_anos_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_curva_bonos_uf",
    name: "macro.curva_bonos_uf",
    sector: "macro",
    color: "#E65100",
    x: 4050,
    y: 310,
    w: 250,
    h: 188,
    rows: "3.171 días",
    file: "outputs/macro/macro_curva_bonos_uf.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "rendimiento_bono_uf_1_ano_pct", type: "DOUBLE" },
      { name: "rendimiento_bono_uf_2_anos_pct", type: "DOUBLE" },
      { name: "rendimiento_bono_uf_5_anos_pct", type: "DOUBLE" },
      { name: "rendimiento_bono_uf_10_anos_pct", type: "DOUBLE" },
      { name: "rendimiento_bono_uf_20_anos_pct", type: "DOUBLE" },
      { name: "rendimiento_bono_uf_30_anos_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_inflacion_implicita",
    name: "macro.inflacion_implicita",
    sector: "macro",
    color: "#E65100",
    x: 3760,
    y: 420,
    w: 250,
    h: 116,
    rows: "3.075 días",
    file: "outputs/macro/macro_inflacion_implicita.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "inflacion_implicita_5_anos_pct", type: "DOUBLE" },
      { name: "inflacion_implicita_10_anos_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_dolar_observado",
    name: "macro.dolar_observado",
    sector: "macro",
    color: "#E65100",
    x: 4050,
    y: 528,
    w: 250,
    h: 98,
    rows: "3.186 días",
    file: "outputs/macro/macro_dolar_observado.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "dolar_observado_clp_por_usd", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_euro_observado",
    name: "macro.euro_observado",
    sector: "macro",
    color: "#E65100",
    x: 3760,
    y: 566,
    w: 250,
    h: 98,
    rows: "3.186 días",
    file: "outputs/macro/macro_euro_observado.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "euro_observado_clp_por_eur", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_tipo_cambio_multilateral",
    name: "macro.tipo_cambio_multilateral",
    sector: "macro",
    color: "#E65100",
    x: 4050,
    y: 656,
    w: 250,
    h: 134,
    rows: "3.186 días",
    file: "outputs/macro/macro_tipo_cambio_multilateral.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "tipo_cambio_nominal_multilateral_indice", type: "DOUBLE" },
      { name: "tipo_cambio_nominal_multilateral_5_monedas_indice", type: "DOUBLE" },
      { name: "tipo_cambio_nominal_multilateral_x_indice", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_tipo_cambio_real",
    name: "macro.tipo_cambio_real",
    sector: "macro",
    color: "#F57C00",
    x: 3760,
    y: 694,
    w: 250,
    h: 116,
    rows: "152 meses",
    file: "outputs/macro/macro_tipo_cambio_real.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "tipo_cambio_real_general_indice", type: "DOUBLE" },
      { name: "tipo_cambio_real_5_monedas_indice", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_uf",
    name: "macro.uf",
    sector: "macro",
    color: "#E65100",
    x: 4050,
    y: 820,
    w: 250,
    h: 98,
    rows: "4.675 días",
    file: "outputs/macro/macro_uf.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "uf_valor_clp", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_utm",
    name: "macro.utm",
    sector: "macro",
    color: "#F57C00",
    x: 3760,
    y: 840,
    w: 250,
    h: 98,
    rows: "154 meses",
    file: "outputs/macro/macro_utm.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "utm_valor_clp", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_inflacion_ipc",
    name: "macro.inflacion_ipc",
    sector: "macro",
    color: "#F57C00",
    x: 4050,
    y: 948,
    w: 250,
    h: 134,
    rows: "153 meses",
    file: "outputs/macro/macro_inflacion_ipc.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "ipc_indice", type: "DOUBLE" },
      { name: "ipc_var_mensual_pct", type: "DOUBLE" },
      { name: "ipc_var_anual_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_imacec",
    name: "macro.imacec",
    sector: "macro",
    color: "#F57C00",
    x: 3760,
    y: 968,
    w: 250,
    h: 170,
    rows: "152 meses",
    file: "outputs/macro/macro_imacec.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "imacec_empalmado_indice", type: "DOUBLE" },
      { name: "imacec_no_minero_indice", type: "DOUBLE" },
      { name: "imacec_minero_indice", type: "DOUBLE" },
      { name: "imacec_comercio_indice", type: "DOUBLE" },
      { name: "imacec_servicios_indice", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_pib_trimestral",
    name: "macro.pib_trimestral",
    sector: "macro",
    color: "#FF9800",
    x: 4050,
    y: 1112,
    w: 250,
    h: 98,
    rows: "50 trimestres",
    file: "outputs/macro/macro_pib_trimestral.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "pib_encadenado_miles_mm_clp", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_mercado_laboral",
    name: "macro.mercado_laboral",
    sector: "macro",
    color: "#F57C00",
    x: 3760,
    y: 1168,
    w: 250,
    h: 152,
    rows: "152 meses",
    file: "outputs/macro/macro_mercado_laboral.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "desocupacion_pct", type: "DOUBLE" },
      { name: "ocupados_miles_personas", type: "DOUBLE" },
      { name: "asalariados_miles_personas", type: "DOUBLE" },
      { name: "fuerza_trabajo_miles_personas", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_cobre",
    name: "macro.cobre",
    sector: "macro",
    color: "#E65100",
    x: 4050,
    y: 1240,
    w: 250,
    h: 116,
    rows: "3.258 días",
    file: "outputs/macro/macro_cobre.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "cobre_refinado_usd_por_libra", type: "DOUBLE" },
      { name: "cobre_referencial_mensual_usd_por_libra", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_metales_preciosos",
    name: "macro.metales_preciosos",
    sector: "macro",
    color: "#E65100",
    x: 3760,
    y: 1350,
    w: 250,
    h: 116,
    rows: "3.186 días",
    file: "outputs/macro/macro_metales_preciosos.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "oro_usd_por_onza_troy", type: "DOUBLE" },
      { name: "plata_usd_por_onza_troy", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_reservas_internacionales",
    name: "macro.reservas_internacionales",
    sector: "macro",
    color: "#F57C00",
    x: 4050,
    y: 1386,
    w: 250,
    h: 98,
    rows: "153 meses",
    file: "outputs/macro/macro_reservas_internacionales.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "reservas_internacionales_millones_usd", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_tasa_referencia_fed",
    name: "macro.tasa_referencia_fed",
    sector: "macro",
    color: "#E65100",
    x: 3760,
    y: 1496,
    w: 250,
    h: 98,
    rows: "3.323 días",
    file: "outputs/macro/macro_tasa_referencia_fed.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "tasa_fed_funds_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_deuda_publica_pct_pib",
    name: "macro.deuda_publica_pct_pib",
    sector: "macro",
    color: "#FF9800",
    x: 4050,
    y: 1514,
    w: 250,
    h: 98,
    rows: "49 trimestres",
    file: "outputs/macro/macro_deuda_publica_pct_pib.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "deuda_bruta_gobierno_central_pct_pib", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_expectativas_inflacion",
    name: "macro.expectativas_inflacion",
    sector: "macro",
    color: "#F57C00",
    x: 3760,
    y: 1624,
    w: 250,
    h: 116,
    rows: "154 meses",
    file: "outputs/macro/macro_expectativas_inflacion.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "expectativa_inflacion_ipc_11_meses_pct", type: "DOUBLE" },
      { name: "expectativa_inflacion_ipc_23_meses_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_expectativas_tpm",
    name: "macro.expectativas_tpm",
    sector: "macro",
    color: "#F57C00",
    x: 4050,
    y: 1642,
    w: 250,
    h: 116,
    rows: "154 meses",
    file: "outputs/macro/macro_expectativas_tpm.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "expectativa_tpm_11_meses_pct", type: "DOUBLE" },
      { name: "expectativa_tpm_23_meses_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_expectativas_operadores",
    name: "macro.expectativas_operadores",
    sector: "macro",
    color: "#E65100",
    x: 3760,
    y: 1770,
    w: 250,
    h: 116,
    rows: "237 días",
    file: "outputs/macro/macro_expectativas_operadores.parquet",
    cols: [
      { name: "fecha", pk: true, type: "VARCHAR" },
      { name: "periodo", type: "VARCHAR" },
      { name: "expectativa_inflacion_12_meses_pct", type: "DOUBLE" },
      { name: "expectativa_tpm_12_meses_pct", type: "DOUBLE" }
    ]
  },
  {
    id: "macro_series_catalogo",
    name: "macro.series_catalogo",
    sector: "macro",
    color: "#FF9800",
    x: 4050,
    y: 1788,
    w: 250,
    h: 170,
    rows: "51 series",
    file: "outputs/macro/macro_series_catalogo.parquet",
    cols: [
      { name: "clave", pk: true, type: "VARCHAR" },
      { name: "serie_id", type: "VARCHAR" },
      { name: "nombre", type: "VARCHAR" },
      { name: "grupo", type: "VARCHAR" },
      { name: "unidad", type: "VARCHAR" },
      { name: "frecuencia", type: "VARCHAR" },
      { name: "titulo_bcch", type: "VARCHAR" }
    ]
  },
  // <macro:fin>
  {
    id: "factoring_leasing_lista_entidades",
    name: "factoring_leasing.lista_entidades",
    sector: "factoring_leasing",
    color: "#D97706",
    x: 4460,
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
    id: "corredoras_bolsa_lista_entidades",
    name: "corredoras.lista_entidades",
    sector: "corredoras_bolsa",
    color: "#8B5CF6",
    x: 3420,
    y: -80,
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
    id: "securitizadoras_lista_entidades",
    name: "securitizadoras.lista_entidades",
    sector: "securitizadoras",
    color: "#0284C7",
    x: 4760,
    y: -80,
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
    x: 5080,
    y: 320,
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
    id: "patrimonios_separados_lista_entidades",
    name: "patrimonios_separados.lista_entidades",
    sector: "patrimonios_separados",
    color: "#075985",
    x: 5080,
    y: -80,
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
    id: "cooperativas_lista_entidades",
    name: "cooperativas.lista_entidades",
    sector: "cooperativas",
    color: "#16A34A",
    x: 6080,
    y: -80,
    w: 260,
    h: 180,
    rows: "7 entidades",
    file: "outputs/cooperativas/cooperativas_maestro.parquet",
    cols: [
      { name: "rut", pk: true, type: "VARCHAR" },
      { name: "rut_dv", type: "VARCHAR" },
      { name: "dv", type: "VARCHAR" },
      { name: "nombre_empresa", type: "VARCHAR" },
      { name: "nombre_fantasia", type: "VARCHAR" },
      { name: "sede_matriz", type: "VARCHAR" },
      { name: "region", type: "VARCHAR" },
      { name: "estado_vigencia", type: "VARCHAR" }
    ]
  },
  {
    id: "ccaf_lista_entidades",
    name: "ccaf.lista_entidades",
    sector: "cajas_compensacion",
    color: "#D97706",
    x: 5410,
    y: -80,
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
    id: "agf_lista_entidades",
    name: "agf.lista_entidades",
    sector: "agf",
    color: "#6366F1",
    x: 3100,
    y: -80,
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
    x: 3100,
    y: 320,
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
    x: 3100,
    y: 590,
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
    x: 4760,
    y: 320,
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
    x: 4760,
    y: 590,
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
    x: 5410,
    y: 320,
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
    x: 5410,
    y: 590,
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
    x: 3420,
    y: 320,
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
    x: 3420,
    y: 590,
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
    id: "sistemas_pago_lista_entidades",
    name: "sistemas_pago.lista_entidades",
    sector: "sistemas_pago",
    color: "#0F766E",
    x: 5790,
    y: 320,
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
    id: "fintech_rpsf_lista_entidades",
    name: "fintech.lista_entidades",
    sector: "fintech",
    color: "#D97706",
    x: 6080,
    y: 320,
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

  // BEGIN AUTO FI EEFF ERD
{
  id: "fi_balance",
  name: "fi.balance",
  sector: "fi",
  color: "var(--accent-mint)",
  x: 1620,
  y: 850,
  w: 270,
  h: 248,
  rows: "Trimestral · contextos separados",
  file: "outputs/fi/fi_balance/manifest.json",
  cols: [
    {
      name: "periodo",
      pk: true,
      type: "VARCHAR"
    },
    {
      name: "run_fondo",
      fk: true,
      type: "VARCHAR"
    },
    {
      name: "contexto",
      pk: true,
      type: "VARCHAR"
    },
    {
      name: "codigo_cuenta",
      pk: true,
      type: "VARCHAR"
    },
    {
      name: "rut_agf",
      fk: true,
      type: "VARCHAR"
    },
    {
      name: "moneda",
      type: "VARCHAR"
    },
    {
      name: "valor_miles_mf",
      type: "BIGINT"
    }
  ]
},
{
  id: "fi_resultados",
  name: "fi.resultados",
  sector: "fi",
  color: "var(--accent-mint)",
  x: 1920,
  y: 850,
  w: 270,
  h: 248,
  rows: "Trimestral · contextos separados",
  file: "outputs/fi/fi_resultados/manifest.json",
  cols: [
    {
      name: "periodo",
      pk: true,
      type: "VARCHAR"
    },
    {
      name: "run_fondo",
      fk: true,
      type: "VARCHAR"
    },
    {
      name: "contexto",
      pk: true,
      type: "VARCHAR"
    },
    {
      name: "codigo_cuenta",
      pk: true,
      type: "VARCHAR"
    },
    {
      name: "rut_agf",
      fk: true,
      type: "VARCHAR"
    },
    {
      name: "moneda",
      type: "VARCHAR"
    },
    {
      name: "valor_miles_mf",
      type: "BIGINT"
    }
  ]
},
  // END AUTO FI EEFF ERD
  {
    id: "seguros_prestamos",
    name: "B.12 PRÉSTAMOS",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 80,
    y: 1080,
    w: 260,
    h: 230,
    rows: "Mensual · desde 2024-12",
    file: "outputs/seguros/prestamos/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "codigo_prestamo",
        type: "BIGINT"
      },
      {
        name: "fecha_prestamo",
        type: "VARCHAR"
      },
      {
        name: "fecha_vencimiento",
        type: "VARCHAR"
      },
      {
        name: "tipo_deudor",
        type: "VARCHAR"
      },
      {
        name: "valor_final_b_12_m_clp",
        type: "BIGINT"
      }
    ]
  },
  {
    id: "seguros_bienes_raices_arriendo_morosidad",
    name: "B.13 BIENES RAICES EN ARRIENDO Y MOROSIDAD DE MUTUOS HIPOTECARIOS ENDOSABLES Y CONTRATOS DE LEASING",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 380,
    y: 1080,
    w: 260,
    h: 230,
    rows: "Mensual · desde 2024-12",
    file: "outputs/seguros/bienes_raices_arriendo_morosidad/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "property_id",
        type: "VARCHAR"
      },
      {
        name: "tipo_instrumento",
        type: "VARCHAR"
      },
      {
        name: "comuna",
        type: "VARCHAR"
      },
      {
        name: "recaudacion_mes_total_m_clp",
        type: "BIGINT"
      },
      {
        name: "morosidad_total_m_clp",
        type: "BIGINT"
      }
    ]
  },
  {
    id: "seguros_garantias_derivados",
    name: "B.14 GARANTÍAS EN INSTRUMENTOS DERIVADOS",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 680,
    y: 1080,
    w: 260,
    h: 230,
    rows: "Mensual · desde 2024-12",
    file: "outputs/seguros/garantias_derivados/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "rut_contraparte_nacional",
        type: "VARCHAR"
      },
      {
        name: "contraparte_tipo",
        type: "VARCHAR"
      },
      {
        name: "posicion_compania",
        type: "VARCHAR"
      },
      {
        name: "tipo_garantia",
        type: "VARCHAR"
      },
      {
        name: "valor_razonable_activo_en_garantia_m_clp",
        type: "BIGINT"
      }
    ]
  },
  {
    id: "seguros_renta_fija_relevante",
    name: "B.1 INSTRUMENTOS DE RENTA FIJA",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 980,
    y: 1080,
    w: 260,
    h: 230,
    rows: "Campos relevantes",
    file: "outputs/seguros/renta_fija_relevante/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "codigo_operacion",
        type: "VARCHAR"
      },
      {
        name: "folio_operacion",
        type: "BIGINT"
      },
      {
        name: "item_operacion",
        type: "BIGINT"
      },
      {
        name: "tipo_instrumento",
        type: "VARCHAR"
      },
      {
        name: "nemotecnico",
        type: "VARCHAR"
      },
      {
        name: "serie",
        type: "VARCHAR"
      }
    ]
  },
  {
    id: "seguros_acciones_relevantes",
    name: "B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS Y CUOTAS DE FONDOS DE INVERSIÓN",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 1280,
    y: 1080,
    w: 260,
    h: 230,
    rows: "Campos relevantes",
    file: "outputs/seguros/acciones_relevantes/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "tipo_instrumento",
        type: "VARCHAR"
      },
      {
        name: "nemotecnico",
        type: "VARCHAR"
      },
      {
        name: "serie",
        type: "VARCHAR"
      },
      {
        name: "unidad_monetaria",
        type: "VARCHAR"
      },
      {
        name: "unidades",
        type: "DOUBLE"
      },
      {
        name: "valor_costo_clp",
        type: "BIGINT"
      }
    ]
  },
  {
    id: "seguros_bienes_raices_relevantes",
    name: "B.4 BIENES RAICES",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 80,
    y: 1370,
    w: 260,
    h: 230,
    rows: "Campos relevantes",
    file: "outputs/seguros/bienes_raices_relevantes/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "property_id",
        type: "VARCHAR"
      },
      {
        name: "tipo_de_inmueble",
        type: "VARCHAR"
      },
      {
        name: "tipo_instrumento",
        type: "VARCHAR"
      },
      {
        name: "destino",
        type: "VARCHAR"
      },
      {
        name: "uso",
        type: "VARCHAR"
      },
      {
        name: "comuna",
        type: "VARCHAR"
      }
    ]
  },
  {
    id: "seguros_extranjeros_relevantes",
    name: "B.5 INVERSIONES EN EL EXTRANJERO",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 380,
    y: 1370,
    w: 260,
    h: 230,
    rows: "Campos relevantes",
    file: "outputs/seguros/extranjeros_relevantes/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "tipo_registro",
        type: "VARCHAR"
      },
      {
        name: "tipo_instrumento",
        type: "VARCHAR"
      },
      {
        name: "codigo_individualizacion_o_nemotecnico",
        type: "VARCHAR"
      },
      {
        name: "pais",
        type: "VARCHAR"
      },
      {
        name: "moneda",
        type: "VARCHAR"
      },
      {
        name: "valor_nominal",
        type: "DOUBLE"
      }
    ]
  },
  {
    id: "seguros_derivados_relevantes",
    name: "B.7 INVERSIONES EN INSTRUMENTOS DERIVADOS Y PACTOS",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 680,
    y: 1370,
    w: 260,
    h: 230,
    rows: "Campos relevantes",
    file: "outputs/seguros/derivados_relevantes/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "tipo_registro",
        type: "VARCHAR"
      },
      {
        name: "tipo_operacion",
        type: "VARCHAR"
      },
      {
        name: "folio_operacion",
        type: "BIGINT"
      },
      {
        name: "item_operacion",
        type: "BIGINT"
      },
      {
        name: "fecha_de_la_operacion",
        type: "VARCHAR"
      },
      {
        name: "fecha_de_vencimiento_del_contrato",
        type: "VARCHAR"
      }
    ]
  },
  {
    id: "seguros_prestamos_relevantes",
    name: "B.12 PRÉSTAMOS",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 980,
    y: 1370,
    w: 260,
    h: 230,
    rows: "Campos relevantes",
    file: "outputs/seguros/prestamos_relevantes/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "codigo_prestamo",
        type: "BIGINT"
      },
      {
        name: "fecha_prestamo",
        type: "VARCHAR"
      },
      {
        name: "fecha_vencimiento",
        type: "VARCHAR"
      },
      {
        name: "tipo_deudor",
        type: "VARCHAR"
      },
      {
        name: "tipo_prestamo",
        type: "VARCHAR"
      },
      {
        name: "prestamo_representativo",
        type: "VARCHAR"
      }
    ]
  },
  {
    id: "seguros_bienes_raices_arriendo_morosidad_relevantes",
    name: "B.13 BIENES RAICES EN ARRIENDO Y MOROSIDAD DE MUTUOS HIPOTECARIOS ENDOSABLES Y CONTRATOS DE LEASING",
    sector: "seguros",
    color: "var(--accent-mint)",
    x: 1280,
    y: 1370,
    w: 260,
    h: 230,
    rows: "Campos relevantes",
    file: "outputs/seguros/bienes_raices_arriendo_morosidad_relevantes/manifest.json",
    cols: [
      {
        name: "periodo",
        type: "VARCHAR"
      },
      {
        name: "sector",
        type: "VARCHAR"
      },
      {
        name: "rut_aseguradora",
        type: "VARCHAR",
        fk: true
      },
      {
        name: "nombre_aseguradora",
        type: "VARCHAR"
      },
      {
        name: "property_id",
        type: "VARCHAR"
      },
      {
        name: "tipo_instrumento",
        type: "VARCHAR"
      },
      {
        name: "comuna",
        type: "VARCHAR"
      },
      {
        name: "fecha_vencimiento_contrato",
        type: "VARCHAR"
      },
      {
        name: "facturacion_mes_m_clp",
        type: "BIGINT"
      },
      {
        name: "recaudacion_mes_actual_m_clp",
        type: "BIGINT"
      }
    ]
  },
  {
    id: "seguros_registros_tipo6",
    name: "Registros tipo 6 de B.11 y B.14",
    sector: "seguros",
    color: "var(--accent-mint)",
    // Estaba en (1280, 1080), la misma coordenada que `seguros_acciones_relevantes`:
    // dos tarjetas dibujadas una sobre otra, con los títulos cruzándose. Se mueve
    // a la franja libre entre el bloque de seguros y el de fondos de inversión.
    x: 1580,
    y: 1120,
    w: 300,
    h: 230,
    rows: "Mensual · desde 2024-12",
    file: "outputs/seguros/registros_tipo6/manifest.json",
    cols: [
      { name: "periodo", type: "VARCHAR" },
      { name: "sector", type: "VARCHAR" },
      { name: "rut_aseguradora", type: "VARCHAR", fk: true },
      { name: "nombre_aseguradora", type: "VARCHAR" },
      { name: "archivo_origen", type: "VARCHAR" },
      { name: "tipo_archivo", type: "VARCHAR" },
      { name: "tipo_registro", type: "VARCHAR" },
      { name: "largo_registro", type: "BIGINT" },
      { name: "registro_original", type: "VARCHAR" }
    ]
  }

];

// Relaciones entre tablas (Claves Foráneas lógicas)
const ERD_LINKS = [
  // BEGIN AUTO FI EEFF LINKS
  { from: "fi_lista_entidades", to: "fi_balance", key: "run_fondo" },
  { from: "agf_lista_entidades", to: "fi_balance", key: "rut = rut_agf" },
  { from: "fi_lista_entidades", to: "fi_resultados", key: "run_fondo" },
  { from: "agf_lista_entidades", to: "fi_resultados", key: "rut = rut_agf" },
  // END AUTO FI EEFF LINKS
  { from: "seguros_lista_entidades", to: "seguros_renta_fija", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_acciones", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_fondos_mutuos", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_bienes_raices", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_extranjeros", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_derivados", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_pactos", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_control_inversiones", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_otras_inversiones", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_tablas_descriptores", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_tablas_desarrollo", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_flujos_activos_elegibles", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_prestamos", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_bienes_raices_arriendo_morosidad", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_garantias_derivados", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_registros_tipo6", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_renta_fija_relevante", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_acciones_relevantes", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_bienes_raices_relevantes", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_extranjeros_relevantes", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_derivados_relevantes", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_prestamos_relevantes", key: "sector, rut_aseguradora" },
  { from: "seguros_lista_entidades", to: "seguros_bienes_raices_arriendo_morosidad_relevantes", key: "sector, rut_aseguradora" },
  { from: "agf_lista_entidades", to: "fi_lista_entidades", key: "rut_administradora (gestión fiduciaria LUF)" },
  { from: "fi_lista_entidades", to: "fi_cartera_nacional", key: "run_fondo" },
  { from: "fi_lista_entidades", to: "fi_cartera_extranjera", key: "run_fondo" },
  { from: "fi_lista_entidades", to: "fi_futuros", key: "run_fondo" },
  { from: "fi_lista_entidades", to: "fi_pactos", key: "run_fondo" },
  { from: "securitizadoras_lista_entidades", to: "patrimonios_separados_lista_entidades", key: "rut_administradora (administración fiduciaria)" },
  { from: "securitizadoras_lista_entidades", to: "patrimonios_separados_balance", key: "rut = rut_administradora (cuerpo, sin dígito verificador)" },
  // <macro-links:inicio>
  { from: "macro_curva_bonos_pesos", to: "macro_inflacion_implicita", key: "fecha (bono pesos − bono UF)" },
  { from: "macro_curva_bonos_uf", to: "macro_inflacion_implicita", key: "fecha (bono pesos − bono UF)" },
  { from: "macro_inflacion_ipc", to: "macro_expectativas_inflacion", key: "periodo (inflación efectiva vs esperada)" },
  { from: "macro_tasas_corto_plazo", to: "macro_expectativas_tpm", key: "periodo (TPM efectiva vs esperada)" },
  { from: "macro_dolar_observado", to: "macro_euro_observado", key: "fecha" },
  // <macro-links:fin>
  { from: "bancos_lista_entidades", to: "bancos_balance", key: "codigo_institucion (código fuente CMF)" },
  { from: "bancos_lista_entidades", to: "bancos_resultados", key: "codigo_institucion (código fuente CMF)" },
  { from: "agf_lista_entidades", to: "agf_balance", key: "rut" },
  { from: "agf_lista_entidades", to: "agf_resultados", key: "rut" },
  { from: "securitizadoras_lista_entidades", to: "securitizadoras_balance", key: "rut" },
  { from: "securitizadoras_lista_entidades", to: "securitizadoras_resultados", key: "rut" },
  { from: "ccaf_lista_entidades", to: "ccaf_balance", key: "rut" },
  { from: "ccaf_lista_entidades", to: "ccaf_resultados", key: "rut" },
  { from: "corredoras_bolsa_lista_entidades", to: "corredoras_bolsa_balance", key: "rut" },
  { from: "corredoras_bolsa_lista_entidades", to: "corredoras_bolsa_resultados", key: "rut" },
  { from: "ffmm_lista_entidades", to: "ffmm_cartera_nacional", key: "run_fondo" },
  { from: "ffmm_lista_entidades", to: "ffmm_cartera_extranjera", key: "run_fondo" },
  { from: "ffmm_lista_entidades", to: "ffmm_futuros", key: "run_fondo" },
  { from: "ffmm_lista_entidades", to: "ffmm_opciones", key: "run_fondo" },
  { from: "ffmm_lista_entidades", to: "ffmm_balance", key: "run_fondo" },
  { from: "ffmm_lista_entidades", to: "ffmm_resultados", key: "run_fondo" },
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

    // Cardinalidad medida de cada unión (punto 10): se marca en el mapa si no es uno a uno.
    this.cardinalidad = {};
    this.cargarCardinalidad();

    this.initEvents();
    this.resize();
  }

  async cargarCardinalidad() {
    try {
      // El <head> ya dejó esta descarga en marcha (window.SIF_JSON); si no existe
      // —navegador sin fetch o prueba en jsdom— se pide aquí como antes.
      let datos;
      if (window.SIF_JSON && window.SIF_JSON.cardinalidad) {
        datos = await window.SIF_JSON.cardinalidad;
      } else {
        const respuesta = await fetch("outputs/cardinalidad_relaciones.json", { cache: "force-cache" });
        if (!respuesta.ok) throw new Error("HTTP " + respuesta.status);
        datos = await respuesta.json();
      }
      this.cardinalidad = Object.fromEntries(
        datos.uniones.map((u) => [`${u.from}|${u.to}`, u])
      );
      this.render();
    } catch (e) {
      // Sin el archivo el mapa funciona igual, solo sin advertencias de cardinalidad.
      console.warn("Cardinalidad de uniones no disponible:", e.message);
    }
  }

  resize() {
    // El canvas comparte el panel con la cabecera de pestañas y la franja de
    // filtros, así que se mide a sí mismo (y no al panel completo) para no
    // dibujar más alto que su espacio visible. Con la pestaña oculta el rect
    // es 0x0: se usa 1 para no dejar un canvas inválido y se recalcula al abrir.
    const rect = this.canvas.getBoundingClientRect();
    const width = Math.max(1, Math.round(rect.width));
    const height = Math.max(1, Math.round(rect.height));
    if (this.canvas.width !== width) this.canvas.width = width;
    if (this.canvas.height !== height) this.canvas.height = height;
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

    /* Pan, arrastre de nodos y pellizco.
     *
     * Antes sólo había mousedown/mousemove/wheel: en un teléfono el mapa no se
     * podía mover ni ampliar, que es justo lo que se hace con un grafo. Se usan
     * Pointer Events, que cubren ratón, dedo y lápiz con el mismo código, y se
     * añade el pellizco de dos dedos. El arrastre con ratón mantiene su
     * comportamiento: los botones laterales no cuentan.
     */
    const punteros = new Map();
    let pellizco = null;

    const distancia = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    const medio = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });

    this.canvas.addEventListener("pointerdown", (e) => {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      if (this.canvas.setPointerCapture) {
        try { this.canvas.setPointerCapture(e.pointerId); } catch (_) { /* puntero ya liberado */ }
      }
      punteros.set(e.pointerId, { x: e.clientX, y: e.clientY });
      this.arrastro = false;
      this.downAt = { x: e.clientX, y: e.clientY };

      if (punteros.size === 2) {
        const [a, b] = Array.from(punteros.values());
        pellizco = { distancia: distancia(a, b), medio: medio(a, b) };
        this.isDragging = false;
        this.activeNode = null;
        return;
      }

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

    this.canvas.addEventListener("pointermove", (e) => {
      const puntero = punteros.get(e.pointerId);
      if (!puntero) {
        // Sin puntero activo sólo hay hover, y el hover es cosa del ratón.
        if (e.pointerType !== "mouse") return;
        const pos = this.getCanvasCoords(e);
        const hover = this.getNodeAt(pos.x, pos.y);
        if (hover !== this.hoveredNode) {
          this.hoveredNode = hover;
          this.canvas.style.cursor = hover ? "pointer" : "grab";
          this.render();
        }
        return;
      }

      puntero.x = e.clientX;
      puntero.y = e.clientY;

      if (punteros.size === 2 && pellizco) {
        const [a, b] = Array.from(punteros.values());
        const ahora = medio(a, b);
        const factor = distancia(a, b) / (pellizco.distancia || 1);
        if (Number.isFinite(factor) && factor > 0) {
          this.zoom(factor, ahora.x, ahora.y);
        }
        // El punto medio también desplaza: pellizcar y arrastrar a la vez.
        this.offsetX += ahora.x - pellizco.medio.x;
        this.offsetY += ahora.y - pellizco.medio.y;
        pellizco = { distancia: distancia(a, b), medio: ahora };
        this.render();
        return;
      }

      // 6 px de tolerancia: el temblor del dedo no debe anular el toque.
      if (this.downAt && Math.hypot(e.clientX - this.downAt.x, e.clientY - this.downAt.y) > 6) {
        this.arrastro = true;
      }

      const pos = this.getCanvasCoords(e);
      if (this.activeNode) {
        this.activeNode.x = pos.x - this.activeNode._dragOffset.x;
        this.activeNode.y = pos.y - this.activeNode._dragOffset.y;
        this.render();
      } else if (this.isDragging) {
        this.offsetX = e.clientX - this.dragStart.x;
        this.offsetY = e.clientY - this.dragStart.y;
        this.render();
      }
    });

    const soltar = (e) => {
      punteros.delete(e.pointerId);
      if (this.canvas.releasePointerCapture) {
        try { this.canvas.releasePointerCapture(e.pointerId); } catch (_) { /* ya liberado */ }
      }
      if (punteros.size < 2) pellizco = null;
      if (punteros.size === 0) {
        this.isDragging = false;
        this.activeNode = null;
      }
    };

    this.canvas.addEventListener("pointerup", soltar);
    this.canvas.addEventListener("pointercancel", soltar);
    this.canvas.addEventListener("pointerleave", (e) => {
      if (e.pointerType === "mouse" && punteros.size === 0) {
        this.hoveredNode = null;
        this.canvas.style.cursor = "grab";
        this.render();
      }
    });

    // Clic en tabla -> Seleccionar para consulta. Después de arrastrar, el
    // navegador igual dispara `click`: se descarta para no cambiar de tabla sin
    // querer al mover el mapa con el dedo.
    this.canvas.addEventListener("click", (e) => {
      if (this.arrastro) {
        this.arrastro = false;
        return;
      }
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
        const targetFilter = e.currentTarget.dataset.filter;
        this.focusSector(targetFilter);
      });
    });

    // Archivo y registros: sus filtros quedan plegados detrás de un botón propio.
    const archivoBtn = document.getElementById("erd-archive-toggle");
    if (archivoBtn) {
      archivoBtn.addEventListener("click", () => {
        const fila = document.getElementById("erd-archive-filters");
        this.mostrarFiltrosArchivo(Boolean(fila && fila.hidden));
      });
    }
  }

  /* ── Alcance editorial: qué nodos entran en cada filtro ──────────────────
     "todos"     → vista principal (núcleo, instituciones y contexto).
     "completo"  → todo el mapa, archivo incluido.
     agrupación  → varios sectores como uno (securitizacion = securitizadoras +
                   patrimonios separados); nivel → todos sus sectores (registro).
     sector      → sólo ese sector (con alias: afp_corporativo = pensiones). */
  claveSector(sector) {
    const A = window.SIFAlcance;
    return A ? A.clave(sector) : String(sector || "");
  }

  // Filtro que corresponde a un sector pedido desde fuera (explorador, portada):
  // los sectores agrupados se muestran juntos.
  filtroPara(sectorKey) {
    const A = window.SIFAlcance;
    const clave = this.claveSector(sectorKey || "seguros");
    if (!A || clave === "todos" || clave === "completo") return clave;
    return A.agrupacionDe(clave) || clave;
  }

  sectoresDelFiltro(filtro) {
    const A = window.SIFAlcance;
    if (!A || !A.disponible() || filtro === "todos" || filtro === "completo") return null;
    return A.sectoresDe(filtro);
  }

  matchesFilter(t) {
    const filtro = this.filter;
    if (filtro === "completo") return true;
    const A = window.SIFAlcance;
    if (filtro === "todos") return !A || A.esVisible(t.sector);
    const sectores = this.sectoresDelFiltro(filtro);
    if (sectores) return sectores.indexOf(this.claveSector(t.sector)) !== -1;
    return t.sector === filtro;
  }

  esFiltroDeArchivo(filtro) {
    const A = window.SIFAlcance;
    if (!A || !A.disponible()) return false;
    if (filtro === "completo") return true;
    const sectores = this.sectoresDelFiltro(filtro) || [];
    return sectores.length > 0 && sectores.every((s) => A.esArchivo(s));
  }

  mostrarFiltrosArchivo(mostrar) {
    const fila = document.getElementById("erd-archive-filters");
    const boton = document.getElementById("erd-archive-toggle");
    if (fila) fila.hidden = !mostrar;
    if (boton) {
      boton.setAttribute("aria-expanded", mostrar ? "true" : "false");
      boton.classList.toggle("open", mostrar);
    }
  }

  // Botón activo, fila de archivo y aviso de alcance según el filtro vigente.
  syncFilterUi() {
    document.querySelectorAll(".filter-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.filter === this.filter);
    });
    const archivo = this.esFiltroDeArchivo(this.filter);
    if (archivo) this.mostrarFiltrosArchivo(true);
    const nota = document.getElementById("erd-scope-note");
    if (nota) {
      const A = window.SIFAlcance;
      const sectores = this.sectoresDelFiltro(this.filter) || [];
      const aviso = archivo && A && sectores.length ? A.aviso(sectores[0]) : "";
      nota.hidden = !aviso && this.filter !== "completo";
      nota.textContent = this.filter === "completo"
        ? "Mapa completo: incluye el archivo congelado y los registros complementarios."
        : aviso;
    }
  }

  autoCenterSector() {
    const visibleTables = this.tables.filter((t) => this.matchesFilter(t));
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
    // Las vistas de conjunto (principal y completa) se muestran enteras aunque el texto
    // quede chico: se ven los bloques por nivel y luego se acerca con la rueda o con +.
    const minimo = (this.filter === "todos" || this.filter === "completo") ? 0.25 : 0.55;
    this.scale = Math.min(Math.max(Math.min(scaleX, scaleY), minimo), 1.05);

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    this.offsetX = (canvasW / 2) - (centerX * this.scale);
    this.offsetY = (canvasH / 2) - (centerY * this.scale);
  }

  focusSector(sectorKey) {
    this.filter = this.filtroPara(sectorKey || "seguros");
    this.syncFilterUi();
    this.autoCenterSector(this.filter);
    this.render();
  }

  focusTable(tableId) {
    const table = this.tables.find((t) => t.id === tableId || t.name === tableId);
    if (!table) return;

    if (!this.matchesFilter(table)) {
      this.filter = this.filtroPara(table.sector);
      this.syncFilterUi();
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
      if (!this.matchesFilter(t)) continue;
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
      <button class="schema-open-btn" onclick="if(window.switchMainTab) window.switchMainTab('data'); if(window.DataViewer) window.DataViewer.loadTable('${node.id}', '${node.name}'); if(window.cerrarEsquema) window.cerrarEsquema();">
        Explorar datos de esta tabla &rarr;
      </button>
    `;

    // El esquema es un diálogo: se recuerda dónde estaba el foco para devolverlo
    // al cerrar y se entra en el propio diálogo (el botón de cerrar).
    window.__focoAntesDelEsquema = document.activeElement;
    modal.classList.add("visible");
    const cerrar = document.getElementById("close-schema-modal");
    if (cerrar && typeof cerrar.focus === "function") cerrar.focus();
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

    // 4. Nombre completo del nodo bajo el puntero y leyenda de cardinalidad:
    //    los dos van fuera de la transformación, fijos en la esquina.
    this.drawTooltip(ctx);
    this.drawLeyendaCardinalidad(ctx);
  }

  drawLeyendaCardinalidad(ctx) {
    const medidas = Object.values(this.cardinalidad);
    if (!medidas.length) return;
    const hay = medidas.some((u) => u.cardinalidad && u.cardinalidad !== "1:1" && u.cardinalidad !== "no medido");
    if (!hay) return;
    const lineas = [
      "1:N = un registro de la izquierda tiene varios a la derecha: filtre por periodo antes de sumar o unir.",
      "Etiqueta amarilla: unión no uno a uno · roja: sin coincidencias · sin etiqueta: 1:1 o no medido.",
    ];
    ctx.save();
    ctx.font = "12px 'Schibsted Grotesk', sans-serif";
    ctx.fillStyle = "rgba(20, 24, 30, 0.85)";
    const alto = lineas.length * 17 + 12;
    const ancho = Math.min(this.canvas.width - 16, Math.max(...lineas.map((l) => ctx.measureText(l).width)) + 16);
    ctx.fillRect(8, this.canvas.height - alto - 8, ancho, alto);
    ctx.fillStyle = "#c9d1d9";
    lineas.forEach((l, i) => ctx.fillText(l, 16, this.canvas.height - alto - 8 + 18 + i * 17));
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
      if (!this.matchesFilter(fromNode) || !this.matchesFilter(toNode)) return;

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

      // Advertencia de cardinalidad: solo si la unión no es uno a uno (o si no encontró coincidencias).
      const medida = this.cardinalidad[`${link.from}|${link.to}`];
      if (medida && medida.cardinalidad && medida.cardinalidad !== "1:1" && medida.cardinalidad !== "no medido") {
        this.dibujarAdvertencia(ctx, (p1.x + p2.x) / 2, (p1.y + p2.y) / 2, medida.cardinalidad);
      }
    });
  }

  dibujarAdvertencia(ctx, x, y, cardinalidad) {
    const texto = cardinalidad === "sin coincidencias" ? "sin coincidencias" : cardinalidad;
    const color = cardinalidad === "sin coincidencias" ? "#d9534f" : "#e0a526";
    ctx.save();
    ctx.font = "600 12px 'Schibsted Grotesk', sans-serif";
    const ancho = ctx.measureText(texto).width + 12;
    ctx.fillStyle = "rgba(20, 24, 30, 0.9)";
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    this.roundRect(ctx, x - ancho / 2, y - 24, ancho, 18, 4);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(texto, x, y - 15);
    ctx.restore();
  }

  /**
   * Recorta un texto al ancho disponible y le añade «…».
   *
   * En el mapa los nodos miden 240–300 px y hay títulos de 118 caracteres
   * («B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, …»): sin recorte, el texto
   * se salía de la tarjeta y se dibujaba encima de los nodos vecinos. Se mide
   * con la fuente ya puesta en el contexto.
   */
  recortar(ctx, texto, ancho) {
    const cadena = String(texto == null ? "" : texto);
    if (ancho <= 0) return "";
    if (ctx.measureText(cadena).width <= ancho) return cadena;
    const puntos = "\u2026";
    let corte = cadena.length;
    while (corte > 0 && ctx.measureText(cadena.slice(0, corte) + puntos).width > ancho) {
      corte -= 1;
    }
    return corte > 0 ? cadena.slice(0, corte).trimEnd() + puntos : puntos;
  }

  drawNodes(ctx) {
    const style = getComputedStyle(document.documentElement);
    const bgCard = style.getPropertyValue('--bg-secondary').trim() || "#132D46";
    const accent = style.getPropertyValue('--accent-mint').trim() || "#01C38D";
    const borderColor = style.getPropertyValue('--border-color').trim() || "rgba(105, 110, 121, 0.4)";
    const teal = style.getPropertyValue("--accent-teal").trim() || "#06B6D4";
    const textSecondary = style.getPropertyValue("--text-secondary").trim() || "#9CA3AF";
    const textMuted = style.getPropertyValue("--text-muted").trim() || "#6B7280";

    this.tables.forEach((t) => {
      if (!this.matchesFilter(t)) return;
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

      // A partir de aquí todo se dibuja recortado a la tarjeta: es la garantía
      // de que nada pueda volver a salirse, aunque el título cambie mañana.
      ctx.save();
      this.roundRect(ctx, t.x, t.y, t.w, t.h, 8);
      ctx.clip();

      // Cabecera: el título ocupa la primera línea y, si no cabe junto a la
      // insignia de la derecha, la insignia baja a una segunda línea.
      const ALTO_TITULO = 28;
      const insignia = String(t.rows || "");
      const FUENTE_TITULO = "bold 12px 'Schibsted Grotesk', Inter, -apple-system, BlinkMacSystemFont, sans-serif";
      ctx.font = FUENTE_TITULO;
      const anchoTituloEntero = ctx.measureText(t.name).width;
      ctx.font = "12px monospace";
      const anchoInsignia = insignia ? ctx.measureText(insignia).width + 14 : 0;
      // La insignia comparte la cabecera con el título sólo si le deja al menos
      // 110 px de título. Antes se dibujaba siempre, y en los títulos largos
      // quedaban las dos cosas encimadas.
      const cabeInsigniaAlLado = anchoInsignia > 0 &&
        (t.w - 20 - anchoInsignia) >= Math.min(anchoTituloEntero, 110);
      const ALTO_CABECERA = cabeInsigniaAlLado ? ALTO_TITULO : (insignia ? ALTO_TITULO + 16 : ALTO_TITULO);

      ctx.fillStyle = this.resolveColor(t.color, accent);
      this.roundRectTop(ctx, t.x, t.y, t.w, ALTO_CABECERA, 8);
      ctx.fill();

      // Título
      ctx.fillStyle = "#FFFFFF";
      ctx.font = FUENTE_TITULO;
      const anchoTitulo = t.w - 20 - (cabeInsigniaAlLado ? anchoInsignia : 0);
      ctx.fillText(this.recortar(ctx, t.name, anchoTitulo), t.x + 10, t.y + 18);

      // Insignia: a la derecha del título si cabe; si no, en su propia línea.
      if (insignia) {
        ctx.font = "12px monospace";
        if (cabeInsigniaAlLado) {
          const anchoBadge = ctx.measureText(insignia).width + 8;
          ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
          ctx.fillRect(t.x + t.w - anchoBadge - 6, t.y + 4, anchoBadge, 18);
          ctx.fillStyle = "#FFFFFF";
          ctx.fillText(insignia, t.x + t.w - anchoBadge - 2, t.y + 18);
        } else {
          ctx.fillStyle = "rgba(255, 255, 255, 0.82)";
          ctx.font = "11px monospace";
          ctx.fillText(this.recortar(ctx, insignia, t.w - 20), t.x + 10, t.y + 34);
        }
      }

      // Columnas. Cuántas caben se calcula con el alto real de la tarjeta: antes
      // se dibujaban siempre cinco y en los nodos bajos la última línea se
      // salía por el borde inferior.
      const inicioColumnas = t.y + ALTO_CABECERA + 18;
      const disponible = t.y + t.h - inicioColumnas - 10;
      const caben = Math.max(1, Math.floor(disponible / 16));
      const conNota = t.cols.length > Math.min(caben, 5);
      const visibles = Math.min(t.cols.length, 5, conNota ? Math.max(1, caben - 1) : caben);

      ctx.font = "12px monospace";
      let colY = inicioColumnas + 8;
      t.cols.slice(0, visibles).forEach((col) => {
        ctx.fillStyle = col.pk ? accent : col.fk ? teal : textSecondary;
        const prefijo = col.pk ? "PK " : col.fk ? "FK " : "   ";
        const anchoTipo = ctx.measureText(col.type || "").width;
        const anchoNombre = t.w - 16 - anchoTipo - 10;
        // Si el tipo deja el nombre sin sitio, se sacrifica el tipo: el nombre
        // es lo que identifica la columna.
        if (anchoNombre < 90) {
          ctx.fillText(this.recortar(ctx, prefijo + col.name, t.w - 16), t.x + 8, colY);
        } else {
          ctx.fillText(this.recortar(ctx, prefijo + col.name, anchoNombre), t.x + 8, colY);
          ctx.fillStyle = textMuted;
          ctx.textAlign = "right";
          ctx.fillText(col.type, t.x + t.w - 8, colY);
          ctx.textAlign = "left";
        }
        colY += 16;
      });

      if (conNota) {
        const restantes = t.cols.length - visibles;
        ctx.fillStyle = accent;
        ctx.font = "12px 'Schibsted Grotesk', sans-serif";
        ctx.fillText(`+ ${restantes} columnas m\u00e1s\u2026`, t.x + 10, colY + 2);
      }

      ctx.restore();
    });
  }

  /**
   * Nombre completo del nodo bajo el puntero, en pantalla.
   *
   * Los títulos largos se recortan en la tarjeta; esto devuelve el texto entero
   * sin que se cruce con nada, y de paso recuerda la frecuencia del objeto.
   */
  drawTooltip(ctx) {
    const t = this.hoveredNode;
    if (!t || !this.matchesFilter(t)) return;
    const texto = t.rows ? `${t.name} \u00b7 ${t.rows}` : t.name;
    ctx.save();
    ctx.font = "600 13px 'Schibsted Grotesk', Inter, sans-serif";
    const ancho = Math.min(this.canvas.width - 24, ctx.measureText(texto).width + 24);
    ctx.fillStyle = "rgba(10, 18, 28, 0.94)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.22)";
    ctx.lineWidth = 1;
    this.roundRect(ctx, 12, 12, ancho, 30, 6);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#F2F6FB";
    ctx.textBaseline = "middle";
    ctx.fillText(this.recortar(ctx, texto, ancho - 24), 24, 28);
    ctx.restore();
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

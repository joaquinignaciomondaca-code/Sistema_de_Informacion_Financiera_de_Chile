export type ColumnType = "text" | "number" | "date";

export type Column = {
  name: string;
  type: ColumnType;
  pk?: boolean;
  unit?: string;
  note?: string;
};

export type Dataset = {
  slug: string;
  nombre: string;
  industria: IndustriaId;
  circular: string;
  archivo: string;
  descripcion: string;
  columnas: Column[];
  filas: Record<string, string | number | null>[];
};

export type IndustriaId = "vida" | "generales" | "ffmm" | "fi" | "pensiones" | "mercado";

export type Industria = {
  id: IndustriaId;
  label: string;
  corto: string;
  emisor: string;
  norma: string;
};

export const INDUSTRIAS: Industria[] = [
  { id: "vida", label: "Seguros de Vida", corto: "Vida", emisor: "CMF · Seguros", norma: "Circular N°1835" },
  { id: "generales", label: "Seguros Generales", corto: "Generales", emisor: "CMF · Seguros", norma: "Circular N°1835" },
  { id: "ffmm", label: "Fondos Mutuos & FFII", corto: "FFMM", emisor: "CMF · Valores", norma: "Circular N°474" },
  { id: "fi", label: "Establecimientos Financieros", corto: "FFII", emisor: "CMF · Bancos", norma: "Circular N°2080" },
  { id: "pensiones", label: "Administradoras de Fondos de Pensiones", corto: "AFP", emisor: "CMF · Previred.", norma: "Circular N°1478" },
  { id: "mercado", label: "Series de Mercado", corto: "Mercado", emisor: "BCCh · Bolsa", norma: "Serie diaria" },
];

/** Relaciones del mapa relacional (join real sobre el dato reportado). */
export type Edge = {
  from: string;
  to: string;
  fromCol: string;
  toCol: string;
  kind: "1:n" | "n:n" | "1:1" | "n:1";
};

export const EDGES: Edge[] = [
  { from: "vida.aseguradoras", to: "vida.solvencia", fromCol: "rut_entidad", toCol: "rut_entidad", kind: "1:n" },
  { from: "vida.aseguradoras", to: "vida.bonos", fromCol: "rut_entidad", toCol: "rut_entidad", kind: "1:n" },
  { from: "vida.aseguradoras", to: "vida.acciones", fromCol: "rut_entidad", toCol: "rut_entidad", kind: "1:n" },
  { from: "vida.solvencia", to: "generales.bienes_raices", fromCol: "periodo", toCol: "periodo_tasacion", kind: "n:n" },
  { from: "ffmm.derivados", to: "fi.repos", fromCol: "nombre_contraparte", toCol: "nombre_contraparte", kind: "n:n" },
  { from: "vida.bonos", to: "mercado.indicadores", fromCol: "fecha_corte", toCol: "fecha", kind: "n:1" },
  { from: "vida.acciones", to: "mercado.indicadores", fromCol: "fecha_corte", toCol: "fecha", kind: "n:1" },
  { from: "pensiones.fondos", to: "mercado.indicadores", fromCol: "fecha_corte", toCol: "fecha", kind: "n:1" },
];

const C = (name: string, type: ColumnType, unit?: string, pk?: boolean, note?: string): Column => ({
  name,
  type,
  unit,
  pk,
  note,
});

export const SEED_DATASETS: Dataset[] = [
  {
    slug: "vida.bonos",
    nombre: "Cartera de Bonos",
    industria: "vida",
    circular: "Circular N°1835",
    archivo: "outputs/vida/cartera_bonos.parquet",
    descripcion: "Rentabilidad fija reportada por aseguradoras de vida: nemotécnico, TIR de mercado y duración.",
    columnas: [
      C("rut_entidad", "text", undefined, true),
      C("nemotecnico", "text", undefined, true),
      C("emisor", "text"),
      C("tipo_bono", "text"),
      C("moneda", "text"),
      C("monto_m_clp", "number", "MM CLP"),
      C("tir_mercado_pct", "number", "%"),
      C("duration_anios", "number", "años"),
      C("presencia_pct", "number", "%"),
      C("fecha_corte", "date"),
    ],
    filas: [
      { rut_entidad: "96.842.100-3", nemotecnico: "BIP 12-26", emisor: "Tesoro Nacional", tipo_bono: "Tasa fija", moneda: "CLF", monto_m_clp: 1840.2, tir_mercado_pct: 5.12, duration_anios: 1.4, presencia_pct: 88, fecha_corte: "2026-09-30" },
      { rut_entidad: "96.842.100-3", nemotecnico: "BIP 15-31", emisor: "Tesoro Nacional", tipo_bono: "Indexado", moneda: "CLP", monto_m_clp: 2310.7, tir_mercado_pct: 4.86, duration_anios: 4.9, presencia_pct: 81, fecha_corte: "2026-09-30" },
      { rut_entidad: "96.842.100-3", nemotecnico: "BCP 09-28", emisor: "Banco de Chile", tipo_bono: "Tasa fija", moneda: "CLP", monto_m_clp: 964.5, tir_mercado_pct: 6.05, duration_anios: 2.1, presencia_pct: 64, fecha_corte: "2026-09-30" },
      { rut_entidad: "97.450.100-5", nemotecnico: "BSANTANDER 11-29", emisor: "Santander-Chile", tipo_bono: "Indexado", moneda: "CLP", monto_m_clp: 1122.9, tir_mercado_pct: 5.74, duration_anios: 2.7, presencia_pct: 57, fecha_corte: "2026-09-30" },
      { rut_entidad: "97.450.100-5", nemotecnico: "CENCOSUD 8-30", emisor: "Cencosud S.A.", tipo_bono: "Tasa fija", moneda: "USD", monto_m_clp: 705.3, tir_mercado_pct: 6.92, duration_anios: 3.6, presencia_pct: 42, fecha_corte: "2026-09-30" },
      { rut_entidad: "96.842.100-3", nemotecnico: "COPEC 10-32", emisor: "Empresas Copec", tipo_bono: "Tasa fija", moneda: "USD", monto_m_clp: 830.1, tir_mercado_pct: 6.41, duration_anios: 5.2, presencia_pct: 39, fecha_corte: "2026-09-30" },
      { rut_entidad: "99.672.300-K", nemotecnico: "FALABELLA 7-31", emisor: "Banco Falabella", tipo_bono: "Indexado", moneda: "CLP", monto_m_clp: 612.4, tir_mercado_pct: 5.98, duration_anios: 3.9, presencia_pct: 35, fecha_corte: "2026-09-30" },
      { rut_entidad: "99.672.300-K", nemotecnico: "ENELCHILE 6-29", emisor: "Enel Chile", tipo_bono: "Tasa fija", moneda: "CLP", monto_m_clp: 498.8, tir_mercado_pct: 5.51, duration_anios: 2.4, presencia_pct: 31, fecha_corte: "2026-09-30" },
      { rut_entidad: "96.842.100-3", nemotecnico: "SQM 9-30", emisor: "SQM S.A.", tipo_bono: "Indexado", moneda: "CLP", monto_m_clp: 421.6, tir_mercado_pct: 6.22, duration_anios: 3.1, presencia_pct: 27, fecha_corte: "2026-09-30" },
      { rut_entidad: "97.450.100-5", nemotecnico: "CMPC 11-33", emisor: "CMPC S.A.", tipo_bono: "Tasa fija", moneda: "USD", monto_m_clp: 356.0, tir_mercado_pct: 6.77, duration_anios: 6.4, presencia_pct: 22, fecha_corte: "2026-09-30" },
    ],
  },
  {
    slug: "vida.acciones",
    nombre: "Cartera de Acciones",
    industria: "vida",
    circular: "Circular N°1835",
    archivo: "outputs/vida/cartera_acciones.parquet",
    descripcion: "Tenencias de renta variable de las aseguradoras sobre emisores del IPSA.",
    columnas: [
      C("rut_entidad", "text", undefined, true),
      C("nemotecnico", "text", undefined, true),
      C("emisor", "text"),
      C("precio_cierre_clp", "number", "CLP"),
      C("variacion_pct", "number", "%"),
      C("presencia_pct", "number", "%"),
      C("peso_ipsa_pct", "number", "%"),
      C("fecha_corte", "date"),
    ],
    filas: [
      { rut_entidad: "96.842.100-3", nemotecnico: "CHILE", emisor: "Banco de Chile", precio_cierre_clp: 184.96, variacion_pct: -1.01, presencia_pct: 74, peso_ipsa_pct: 7.4, fecha_corte: "2026-09-30" },
      { rut_entidad: "96.842.100-3", nemotecnico: "SQM-B", emisor: "SQM", precio_cierre_clp: 65305, variacion_pct: -0.84, presencia_pct: 66, peso_ipsa_pct: 6.1, fecha_corte: "2026-09-30" },
      { rut_entidad: "97.450.100-5", nemotecnico: "BSANTANDER", emisor: "Santander-Chile", precio_cierre_clp: 78.37, variacion_pct: -2.28, presencia_pct: 61, peso_ipsa_pct: 5.8, fecha_corte: "2026-09-30" },
      { rut_entidad: "99.672.300-K", nemotecnico: "COPEC", emisor: "Empresas Copec", precio_cierre_clp: 5964, variacion_pct: -1.09, presencia_pct: 57, peso_ipsa_pct: 9.2, fecha_corte: "2026-09-30" },
      { rut_entidad: "96.842.100-3", nemotecnico: "FALABELLA", emisor: "Cencosud/Falabella", precio_cierre_clp: 6334, variacion_pct: -1.48, presencia_pct: 48, peso_ipsa_pct: 3.9, fecha_corte: "2026-09-30" },
      { rut_entidad: "97.450.100-5", nemotecnico: "CENCOSUD", emisor: "Cencosud S.A.", precio_cierre_clp: 1946, variacion_pct: -2.19, presencia_pct: 45, peso_ipsa_pct: 4.4, fecha_corte: "2026-09-30" },
      { rut_entidad: "99.672.300-K", nemotecnico: "CMPC", emisor: "CMPC S.A.", precio_cierre_clp: 1020, variacion_pct: -1.96, presencia_pct: 41, peso_ipsa_pct: 2.6, fecha_corte: "2026-09-30" },
      { rut_entidad: "96.842.100-3", nemotecnico: "ENELAM", emisor: "Enel Américas", precio_cierre_clp: 87.09, variacion_pct: 0.1, presencia_pct: 38, peso_ipsa_pct: 3.1, fecha_corte: "2026-09-30" },
      { rut_entidad: "97.450.100-5", nemotecnico: "LTM", emisor: "LATAM Airlines", precio_cierre_clp: 24.08, variacion_pct: -1.11, presencia_pct: 33, peso_ipsa_pct: 4.7, fecha_corte: "2026-09-30" },
      { rut_entidad: "99.672.300-K", nemotecnico: "BCI", emisor: "Banco Internacional", precio_cierre_clp: 34510, variacion_pct: -0.62, presencia_pct: 29, peso_ipsa_pct: 4.9, fecha_corte: "2026-09-30" },
    ],
  },
  {
    slug: "vida.solvencia",
    nombre: "Solvencia y Balance",
    industria: "vida",
    circular: "Circular N°1835",
    archivo: "outputs/vida/cartera_solvencia.solvencia.parquet",
    descripcion: "Carátula de inversiones por rubro: activo total, patrimonio técnico y ratio de solvencia.",
    columnas: [
      C("rut_entidad", "text", undefined, true),
      C("periodo", "date", undefined, true),
      C("rubro_caratula", "text", undefined, true),
      C("total_inversion_m_clp", "number", "MM CLP"),
      C("activo_total_m_clp", "number", "MM CLP"),
      C("patrimonio_tecnico_m_clp", "number", "MM CLP"),
      C("ratio_solvencia_pct", "number", "%"),
    ],
    filas: [
      { rut_entidad: "96.842.100-3", periodo: "2026-09-30", rubro_caratula: "Renta fija", total_inversion_m_clp: 8420.5, activo_total_m_clp: 12860.4, patrimonio_tecnico_m_clp: 2140.8, ratio_solvencia_pct: 187.4 },
      { rut_entidad: "96.842.100-3", periodo: "2026-09-30", rubro_caratula: "Renta variable", total_inversion_m_clp: 3180.2, activo_total_m_clp: 12860.4, patrimonio_tecnico_m_clp: 2140.8, ratio_solvencia_pct: 187.4 },
      { rut_entidad: "96.842.100-3", periodo: "2026-09-30", rubro_caratula: "Bienes raíces", total_inversion_m_clp: 902.7, activo_total_m_clp: 12860.4, patrimonio_tecnico_m_clp: 2140.8, ratio_solvencia_pct: 187.4 },
      { rut_entidad: "96.842.100-3", periodo: "2026-09-30", rubro_caratula: "Derivados", total_inversion_m_clp: 411.9, activo_total_m_clp: 12860.4, patrimonio_tecnico_m_clp: 2140.8, ratio_solvencia_pct: 187.4 },
      { rut_entidad: "97.450.100-5", periodo: "2026-09-30", rubro_caratula: "Renta fija", total_inversion_m_clp: 6105.8, activo_total_m_clp: 9430.1, patrimonio_tecnico_m_clp: 1520.3, ratio_solvencia_pct: 172.9 },
      { rut_entidad: "97.450.100-5", periodo: "2026-09-30", rubro_caratula: "Renta variable", total_inversion_m_clp: 2044.6, activo_total_m_clp: 9430.1, patrimonio_tecnico_m_clp: 1520.3, ratio_solvencia_pct: 172.9 },
      { rut_entidad: "97.450.100-5", periodo: "2026-09-30", rubro_caratula: "Depósitos a plazo", total_inversion_m_clp: 780.4, activo_total_m_clp: 9430.1, patrimonio_tecnico_m_clp: 1520.3, ratio_solvencia_pct: 172.9 },
      { rut_entidad: "99.672.300-K", periodo: "2026-09-30", rubro_caratula: "Renta fija", total_inversion_m_clp: 4230.9, activo_total_m_clp: 6870.2, patrimonio_tecnico_m_clp: 1040.5, ratio_solvencia_pct: 165.2 },
      { rut_entidad: "99.672.300-K", periodo: "2026-09-30", rubro_caratula: "Renta variable", total_inversion_m_clp: 1310.4, activo_total_m_clp: 6870.2, patrimonio_tecnico_m_clp: 1040.5, ratio_solvencia_pct: 165.2 },
      { rut_entidad: "99.672.300-K", periodo: "2026-06-30", rubro_caratula: "Renta fija", total_inversion_m_clp: 4088.1, activo_total_m_clp: 6602.7, patrimonio_tecnico_m_clp: 1002.9, ratio_solvencia_pct: 161.8 },
      { rut_entidad: "99.672.300-K", periodo: "2026-06-30", rubro_caratula: "Renta variable", total_inversion_m_clp: 1245.0, activo_total_m_clp: 6602.7, patrimonio_tecnico_m_clp: 1002.9, ratio_solvencia_pct: 161.8 },
      { rut_entidad: "96.842.100-3", periodo: "2026-06-30", rubro_caratula: "Renta fija", total_inversion_m_clp: 8201.3, activo_total_m_clp: 12410.9, patrimonio_tecnico_m_clp: 2061.4, ratio_solvencia_pct: 184.1 },
    ],
  },
  {
    slug: "generales.bienes_raices",
    nombre: "Bienes Raíces en Arriendo",
    industria: "generales",
    circular: "Circular N°1835",
    archivo: "outputs/generales/cartera_bienes_raices.parquet",
    descripcion: "Propiedades tasadas de seguros generales, con comuna, tasación comercial y arriendo mensual.",
    columnas: [
      C("id_propiedad", "text", undefined, true),
      C("tipo", "text"),
      C("comuna", "text"),
      C("region", "text"),
      C("superficie_m2", "number", "m²"),
      C("tasacion_comercial_m_clp", "number", "MM CLP"),
      C("arriendo_mensual_clp", "number", "CLP"),
      C("ocupacion_pct", "number", "%"),
      C("periodo_tasacion", "date"),
    ],
    filas: [
      { id_propiedad: "BR-0114", tipo: "Oficina", comuna: "Las Condes", region: "Metropolitana", superficie_m2: 1840, tasacion_comercial_m_clp: 4820.0, arriendo_mensual_clp: 26800000, ocupacion_pct: 100, periodo_tasacion: "2026-09-30" },
      { id_propiedad: "BR-0127", tipo: "Oficina", comuna: "Vitacura", region: "Metropolitana", superficie_m2: 960, tasacion_comercial_m_clp: 3110.5, arriendo_mensual_clp: 17400000, ocupacion_pct: 92, periodo_tasacion: "2026-09-30" },
      { id_propiedad: "BR-0139", tipo: "Local comercial", comuna: "Providencia", region: "Metropolitana", superficie_m2: 620, tasacion_comercial_m_clp: 1780.2, arriendo_mensual_clp: 11200000, ocupacion_pct: 100, periodo_tasacion: "2026-09-30" },
      { id_propiedad: "BR-0152", tipo: "Bodega", comuna: "Santiago", region: "Metropolitana", superficie_m2: 4200, tasacion_comercial_m_clp: 2460.8, arriendo_mensual_clp: 14800000, ocupacion_pct: 78, periodo_tasacion: "2026-09-30" },
      { id_propiedad: "BR-0166", tipo: "Edificio", comuna: "Ñuñoa", region: "Metropolitana", superficie_m2: 2310, tasacion_comercial_m_clp: 3640.0, arriendo_mensual_clp: 19600000, ocupacion_pct: 88, periodo_tasacion: "2026-09-30" },
      { id_propiedad: "BR-0171", tipo: "Departamento", comuna: "Viña del Mar", region: "Valparaíso", superficie_m2: 310, tasacion_comercial_m_clp: 980.4, arriendo_mensual_clp: 5200000, ocupacion_pct: 100, periodo_tasacion: "2026-09-30" },
      { id_propiedad: "BR-0185", tipo: "Local comercial", comuna: "Concepción", region: "Biobío", superficie_m2: 740, tasacion_comercial_m_clp: 1120.6, arriendo_mensual_clp: 6800000, ocupacion_pct: 64, periodo_tasacion: "2026-09-30" },
      { id_propiedad: "BR-0190", tipo: "Bodega", comuna: "Quilicura", region: "Metropolitana", superficie_m2: 5600, tasacion_comercial_m_clp: 2870.3, arriendo_mensual_clp: 16900000, ocupacion_pct: 95, periodo_tasacion: "2026-09-30" },
    ],
  },
  {
    slug: "ffmm.derivados",
    nombre: "Forwards y Derivados",
    industria: "ffmm",
    circular: "Circular N°474",
    archivo: "outputs/b7_forwards.parquet",
    descripcion: "Operaciones B7: forwards de tipo de cambio y tasas con su contraparte financiera.",
    columnas: [
      C("codigo_operacion", "text", undefined, true),
      C("nombre_contraparte", "text"),
      C("tipo_derivado", "text"),
      C("fecha_vencimiento", "date"),
      C("notional_m_clp", "number", "MM CLP"),
      C("precio_forward_pactado", "number", "CLP/USD"),
      C("tasa_pct", "number", "%"),
    ],
    filas: [
      { codigo_operacion: "FWD-2411", nombre_contraparte: "Banco de Chile", tipo_derivado: "Forward USD/CLP", fecha_vencimiento: "2026-12-18", notional_m_clp: 4280.0, precio_forward_pactado: 941.2, tasa_pct: 5.1 },
      { codigo_operacion: "FWD-2418", nombre_contraparte: "Banco de Chile", tipo_derivado: "Forward USD/CLP", fecha_vencimiento: "2027-03-16", notional_m_clp: 3120.5, precio_forward_pactado: 958.7, tasa_pct: 5.25 },
      { codigo_operacion: "FWD-2426", nombre_contraparte: "BCI", tipo_derivado: "Forward USD/CLP", fecha_vencimiento: "2026-12-18", notional_m_clp: 2760.9, precio_forward_pactado: 939.8, tasa_pct: 5.08 },
      { codigo_operacion: "FWD-2433", nombre_contraparte: "Santander-Chile", tipo_derivado: "Swap de tasa", fecha_vencimiento: "2028-01-04", notional_m_clp: 5410.2, precio_forward_pactado: 5.62, tasa_pct: 5.62 },
      { codigo_operacion: "FWD-2440", nombre_contraparte: "Itaú Corpbanca", tipo_derivado: "Forward USD/CLP", fecha_vencimiento: "2027-06-15", notional_m_clp: 1980.4, precio_forward_pactado: 972.5, tasa_pct: 5.4 },
      { codigo_operacion: "FWD-2451", nombre_contraparte: "Scotiabank Chile", tipo_derivado: "Option collar", fecha_vencimiento: "2027-09-15", notional_m_clp: 2240.0, precio_forward_pactado: 985.0, tasa_pct: 5.55 },
      { codigo_operacion: "FWD-2462", nombre_contraparte: "BCI", tipo_derivado: "Swap de tasa", fecha_vencimiento: "2029-02-01", notional_m_clp: 3890.7, precio_forward_pactado: 5.81, tasa_pct: 5.81 },
      { codigo_operacion: "FWD-2477", nombre_contraparte: "Banco de Chile", tipo_derivado: "Forward UF/CLP", fecha_vencimiento: "2027-03-16", notional_m_clp: 1620.3, precio_forward_pactado: 41680, tasa_pct: 4.9 },
    ],
  },
  {
    slug: "fi.repos",
    nombre: "Repos y Crédito Garantizado",
    industria: "fi",
    circular: "Circular N°2080",
    archivo: "fi/repos/outputs/fi_repos_vrc_crv.parquet",
    descripcion: "Operaciones repo interbancarias con plazo, tasa y valorización de cierre.",
    columnas: [
      C("codigo_operacion", "text", undefined, true),
      C("nombre_contraparte", "text"),
      C("plazo_dias", "number", "días"),
      C("tasa_pct", "number", "%"),
      C("valorizacion_cierre_m_clp", "number", "MM CLP"),
      C("garantia_tipo", "text"),
      C("fecha_corte", "date"),
    ],
    filas: [
      { codigo_operacion: "REP-8841", nombre_contraparte: "Banco de Chile", plazo_dias: 30, tasa_pct: 4.85, valorizacion_cierre_m_clp: 6120.4, garantia_tipo: "BCP", fecha_corte: "2026-09-30" },
      { codigo_operacion: "REP-8856", nombre_contraparte: "Banco de Chile", plazo_dias: 90, tasa_pct: 5.05, valorizacion_cierre_m_clp: 4310.7, garantia_tipo: "BIP", fecha_corte: "2026-09-30" },
      { codigo_operacion: "REP-8862", nombre_contraparte: "Santander-Chile", plazo_dias: 14, tasa_pct: 4.7, valorizacion_cierre_m_clp: 2890.1, garantia_tipo: "BCP", fecha_corte: "2026-09-30" },
      { codigo_operacion: "REP-8874", nombre_contraparte: "Santander-Chile", plazo_dias: 60, tasa_pct: 4.95, valorizacion_cierre_m_clp: 3540.9, garantia_tipo: "Corporate", fecha_corte: "2026-09-30" },
      { codigo_operacion: "REP-8889", nombre_contraparte: "Itaú Corpbanca", plazo_dias: 30, tasa_pct: 4.88, valorizacion_cierre_m_clp: 1975.6, garantia_tipo: "BIP", fecha_corte: "2026-09-30" },
      { codigo_operacion: "REP-8895", nombre_contraparte: "Scotiabank Chile", plazo_dias: 180, tasa_pct: 5.2, valorizacion_cierre_m_clp: 5230.2, garantia_tipo: "BCP", fecha_corte: "2026-09-30" },
      { codigo_operacion: "REP-8903", nombre_contraparte: "BCI", plazo_dias: 7, tasa_pct: 4.62, valorizacion_cierre_m_clp: 1420.8, garantia_tipo: "Letras BCCh", fecha_corte: "2026-09-30" },
      { codigo_operacion: "REP-8917", nombre_contraparte: "BCI", plazo_dias: 120, tasa_pct: 5.12, valorizacion_cierre_m_clp: 2660.5, garantia_tipo: "Corporate", fecha_corte: "2026-09-30" },
    ],
  },
  {
    slug: "vida.aseguradoras",
    nombre: "Maestro Aseguradoras",
    industria: "vida",
    circular: "Circular N°1835",
    archivo: "outputs/vida/maestro_aseguradoras_vida.parquet",
    descripcion: "Entidad reportante: RUT, grupo (1 generales / 2 vida), estado e inversión del último reporte.",
    columnas: [
      C("rut_entidad", "text", undefined, true),
      C("nombre_aseguradora", "text"),
      C("grupo", "number", "1/2"),
      C("estado", "text"),
      C("ultimo_periodo", "date"),
      C("inversion_ultimo_reporte_m_clp", "number", "MM CLP"),
      C("participacion_pct", "number", "%"),
      C("periodos_reportados", "number", "n"),
    ],
    filas: [
      { rut_entidad: "96.842.100-3", nombre_aseguradora: "Mapfre Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 12915.3, participacion_pct: 21.4, periodos_reportados: 234 },
      { rut_entidad: "97.450.100-5", nombre_aseguradora: "Vida Nacional", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 8940.8, participacion_pct: 14.8, periodos_reportados: 234 },
      { rut_entidad: "99.672.300-K", nombre_aseguradora: "Consorcio Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 6341.2, participacion_pct: 10.5, periodos_reportados: 231 },
      { rut_entidad: "96.943.600-2", nombre_aseguradora: "Zurich Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 5810.6, participacion_pct: 9.6, periodos_reportados: 228 },
      { rut_entidad: "96.780.100-8", nombre_aseguradora: "MetLife Chile", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 5122.4, participacion_pct: 8.5, periodos_reportados: 234 },
      { rut_entidad: "97.016.900-1", nombre_aseguradora: "BCI Seguros de Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 4380.9, participacion_pct: 7.2, periodos_reportados: 219 },
      { rut_entidad: "96.402.200-4", nombre_aseguradora: "Sura Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 3905.1, participacion_pct: 6.5, periodos_reportados: 207 },
      { rut_entidad: "96.873.700-9", nombre_aseguradora: "Generali Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 2744.7, participacion_pct: 4.5, periodos_reportados: 186 },
      { rut_entidad: "96.556.300-6", nombre_aseguradora: "Chubb Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 2110.5, participacion_pct: 3.5, periodos_reportados: 174 },
      { rut_entidad: "96.764.400-1", nombre_aseguradora: "Bice Vida", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 1480.2, participacion_pct: 2.5, periodos_reportados: 165 },
      { rut_entidad: "96.675.100-7", nombre_aseguradora: "Tattica Seguros", grupo: 2, estado: "Activa", ultimo_periodo: "2026-09-30", inversion_ultimo_reporte_m_clp: 980.6, participacion_pct: 1.6, periodos_reportados: 132 },
      { rut_entidad: "96.881.500-3", nombre_aseguradora: "Winkler Seguros", grupo: 2, estado: "Cesante", ultimo_periodo: "2024-12-31", inversion_ultimo_reporte_m_clp: 0, participacion_pct: 0, periodos_reportados: 96 },
    ],
  },
  {
    slug: "pensiones.fondos",
    nombre: "Cartera de Fondos AFP",
    industria: "pensiones",
    circular: "Circular N°1478",
    archivo: "outputs/pensiones/fondos_afp.parquet",
    descripcion: "Patrimonio por fondo obligatorio, número de afiliados al fondo y rentabilidad 12 meses.",
    columnas: [
      C("fondo", "text", undefined, true),
      C("adm_principal", "text"),
      C("patrimonio_m_clp", "number", "MM CLP"),
      C("afiliados", "number", "n"),
      C("cuota_valor_clp", "number", "CLP"),
      C("rentabilidad_12m_pct", "number", "%"),
      C("fecha_corte", "date"),
    ],
    filas: [
      { fondo: "A", adm_principal: "Cuprum", patrimonio_m_clp: 4820.4, afiliados: 612000, cuota_valor_clp: 42180.55, rentabilidad_12m_pct: 12.4, fecha_corte: "2026-09-30" },
      { fondo: "B", adm_principal: "Habitat", patrimonio_m_clp: 31450.9, afiliados: 2914000, cuota_valor_clp: 38905.12, rentabilidad_12m_pct: 9.8, fecha_corte: "2026-09-30" },
      { fondo: "C", adm_principal: "Capital", patrimonio_m_clp: 42180.6, afiliados: 4630000, cuota_valor_clp: 36120.44, rentabilidad_12m_pct: 7.6, fecha_corte: "2026-09-30" },
      { fondo: "D", adm_principal: "ProVital", patrimonio_m_clp: 18760.2, afiliados: 3120000, cuota_valor_clp: 33980.9, rentabilidad_12m_pct: 5.1, fecha_corte: "2026-09-30" },
      { fondo: "E", adm_principal: "Model", patrimonio_m_clp: 5240.7, afiliados: 890000, cuota_valor_clp: 31240.18, rentabilidad_12m_pct: 2.9, fecha_corte: "2026-09-30" },
    ],
  },
  {
    slug: "mercado.indicadores",
    nombre: "Serie de Indicadores",
    industria: "mercado",
    circular: "Serie diaria BCCh",
    archivo: "outputs/mercado/indicadores.parquet",
    descripcion: "Cierres mensuales de referencia: dólar observado, UF, TPM, IPC 12m e IPSA.",
    columnas: [
      C("fecha", "date", undefined, true),
      C("usd_clp", "number", "CLP"),
      C("uf_clp", "number", "CLP"),
      C("tpm_pct", "number", "%"),
      C("ipc_12m_pct", "number", "%"),
      C("ipsa", "number", "pts"),
    ],
    filas: [
      { fecha: "2025-10-31", usd_clp: 948.2, uf_clp: 38412.5, tpm_pct: 5.0, ipc_12m_pct: 4.2, ipsa: 10420.5 },
      { fecha: "2025-11-28", usd_clp: 936.7, uf_clp: 38701.9, tpm_pct: 5.0, ipc_12m_pct: 4.4, ipsa: 10612.8 },
      { fecha: "2025-12-31", usd_clp: 952.4, uf_clp: 38998.3, tpm_pct: 4.75, ipc_12m_pct: 4.6, ipsa: 10488.1 },
      { fecha: "2026-01-30", usd_clp: 961.8, uf_clp: 39306.7, tpm_pct: 4.75, ipc_12m_pct: 4.9, ipsa: 10355.4 },
      { fecha: "2026-02-27", usd_clp: 944.1, uf_clp: 39602.4, tpm_pct: 4.5, ipc_12m_pct: 4.7, ipsa: 10590.2 },
      { fecha: "2026-03-31", usd_clp: 932.5, uf_clp: 39854.8, tpm_pct: 4.5, ipc_12m_pct: 4.5, ipsa: 10744.6 },
      { fecha: "2026-04-30", usd_clp: 925.9, uf_clp: 40010.2, tpm_pct: 4.5, ipc_12m_pct: 4.4, ipsa: 10898.3 },
      { fecha: "2026-05-29", usd_clp: 918.4, uf_clp: 40188.6, tpm_pct: 4.5, ipc_12m_pct: 4.3, ipsa: 11042.7 },
      { fecha: "2026-06-30", usd_clp: 921.7, uf_clp: 40342.1, tpm_pct: 4.5, ipc_12m_pct: 4.5, ipsa: 11120.9 },
      { fecha: "2026-07-31", usd_clp: 928.3, uf_clp: 40495.7, tpm_pct: 4.5, ipc_12m_pct: 4.6, ipsa: 11004.2 },
      { fecha: "2026-08-31", usd_clp: 917.6, uf_clp: 40648.9, tpm_pct: 4.5, ipc_12m_pct: 4.5, ipsa: 11315.26 },
      { fecha: "2026-09-15", usd_clp: 913.98, uf_clp: 40054.2, tpm_pct: 4.5, ipc_12m_pct: 4.5, ipsa: 11342.39 },
    ],
  },
];

/** Cinta de cotizaciones — cierres de referencia septiembre 2026 (BCCh, INE, BSoL, LME). */
export type TickerItem = { sym: string; label: string; value: string; delta: number | null };

export const TICKER: TickerItem[] = [
  { sym: "IPSA", label: "Bolsa de Santiago", value: "11.342,39", delta: 1.09 },
  { sym: "USD/CLP", label: "Dólar observado", value: "913,98", delta: 0.04 },
  { sym: "UF", label: "Unidad de Fomento", value: "40.054,20", delta: null },
  { sym: "TPM", label: "Política monetaria", value: "4,50%", delta: 0 },
  { sym: "IPC 12M", label: "INE acumulado", value: "4,5%", delta: -0.1 },
  { sym: "COBRE", label: "USD/lb LME", value: "6,61", delta: 0.03 },
  { sym: "SQM-B", label: "Química y Minera", value: "65.305", delta: -0.84 },
  { sym: "COPEC", label: "Empresas Copec", value: "5.964", delta: -1.09 },
  { sym: "BSANTANDER", label: "Santander-Chile", value: "78,37", delta: -2.28 },
  { sym: "CHILE", label: "Banco de Chile", value: "184,96", delta: -1.01 },
  { sym: "FALABELLA", label: "Banco Falabella", value: "6.334", delta: -1.48 },
  { sym: "CENCOSUD", label: "Cencosud S.A.", value: "1.946", delta: -2.19 },
  { sym: "CMPC", label: "CMPC S.A.", value: "1.020", delta: -1.96 },
  { sym: "LTM", label: "LATAM Airlines", value: "24,08", delta: -1.11 },
  { sym: "ENELAM", label: "Enel Américas", value: "87,09", delta: 0.1 },
  { sym: "UTM", label: "SII mes actual", value: "71.649", delta: null },
];

/** Auditoría del prototipo HTML que entregó el usuario. */
export type Recomendacion = {
  n: string;
  titulo: string;
  severidad: "Crítica" | "Alta" | "Media";
  area: string;
  diagnostico: string;
  accion: string;
};

export const RECOMENDACIONES: Recomendacion[] = [
  {
    n: "01",
    titulo: "DuckDB-Wasm se carga desde CDN con una URL fija y sin plan B",
    severidad: "Crítica",
    area: "Arquitectura",
    diagnostico: "Un script de ~10 MB servido desde jsDelivr en el <head> bloquea el render; si el CDN cae, cambia de versión o el usuario está tras un proxy corporativo, la app queda muda sin mensaje alguno. Además no hay política de permisos ni integridad (SRI).",
    accion: "Cargar con defer + Dynamic Import bajo demanda al primer uso, fijar versión con SRI, y ejecutar la consulta contra Postgres cuando WASM falle. Aquí el motor SQL corre en el servidor sobre datasets en Postgres y degrada a datos en memoria.",
  },
  {
    n: "02",
    titulo: "El mapa relacional es un <canvas> sin semántica accesible",
    severidad: "Crítica",
    area: "Accesibilidad",
    diagnostico: "Un canvas no tiene nodos, no se navega con teclado, no se anuncia con lector de pantalla y pierde nitidez en pantallas retina salvo que se multiplique por devicePixelRatio.",
    accion: "Dibujar el ERD en SVG con nodos <g role=\"button\" tabindex=\"0\">, foco visible y descripción por tabla; el usuario recorre el esquema con Tab y Enter, no sólo con el mouse.",
  },
  {
    n: "03",
    titulo: "Los datos no tienen procedencia ni fecha de corte visibles",
    severidad: "Alta",
    area: "Confianza",
    diagnostico: "Un monitor financiero sin sello de fuente y periodo es una maqueta: el usuario no puede saber si mira cierre de agosto o de 2023, ni si el valor viene del BCCh, la CMF o fue escrito a mano.",
    accion: "Sellar cada tabla con fuente, periodo y fecha de cierre en el encabezado y en el pie; separar explícitamente 'cierres de referencia' de 'datos demostrativos'.",
  },
  {
    n: "04",
    titulo: "Los splitters no persisten y no responden a teclado",
    severidad: "Media",
    area: "UX",
    diagnostico: "Los divisores de panel (panel-splitter, sidebar-resizer) son divs con cursor: col-resize. Se pierden al recargar, no se anuncian y no funcionan en táctil ni con flechas del teclado.",
    accion: "Persistir anchos en localStorage, publicarlos como variables CSS, usar role=\"separator\" con aria-valuenow y mover con flechas ±16 px.",
  },
  {
    n: "05",
    titulo: "La consola SQL es un mockup: no valida ni explica errores",
    severidad: "Alta",
    area: "Producto",
    diagnostico: "El campo acepta cualquier texto y no hay feedback de error, de tiempo de ejecución ni de número de filas, que es lo primero que espera quien escribe SQL.",
    accion: "Motor real con parser propio: SELECT/WHERE/IN/GROUP BY/ORDER BY/LIMIT/ROUND, respuesta con ms, filas devueltas y mensaje de error en español que sugiera la corrección.",
  },
  {
    n: "06",
    titulo: "El árbol lateral codifica industrias sólo con color y opacidad",
    severidad: "Alta",
    area: "Diseño / a11y",
    diagnostico: "Los nodos 'roadmap' usan opacity: 0.65 y los badges dependen del tono. Con daltonismo o en proyector, la jerarquía desaparece. Los targets de 28 px quedan bajo el mínimo táctil de 44 px.",
    accion: "Estado explícito con etiqueta y icono además del color, contraste AA verificado (≥4.5:1 sobre #0D1315) y filas de 36 px en dispositivos táctiles.",
  },
  {
    n: "07",
    titulo: "Cinco temas de color sólo cambian variables, no la jerarquía",
    severidad: "Media",
    area: "Diseño",
    diagnostico: "Swissborg, Bloomberg, Nord y Midnight reemplazan el mismo acento en todos los roles: el color deja de informar. Además ningún tema ofrece variante clara, necesaria para impresión y ambientes de oficina.",
    accion: "Un solo acento semántica-mente estable (esmeralda = activo/positivo, ámbar = alerta, rojo = baja) y una variante clara completa, sin multiplicar paletas decorativas.",
  },
  {
    n: "08",
    titulo: "Todo es cliente: no hay persistencia, API ni trazabilidad",
    severidad: "Crítica",
    area: "Producto",
    diagnostico: "Consultas guardadas en localStorage, sin historial de ejecución, sin endpoint y sin capa de datos: el proyecto no puede crecer hacia el 'centralizador de data' que buscas.",
    accion: "Schema Drizzle con dataset / consulta / ejecucion, rutas API tipadas, historial de corridas y registro de errores. Es la base sobre la que después conectas tus pipelines Parquet.",
  },
];

export const FUENTES = [
  { fuente: "CMF · Cartera de inversiones (Circular N°1835)", uso: "Estructura de renta fija, renta variable, bienes raíces y solvencia de aseguradoras.", url: "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/" },
  { fuente: "CMF · Anexos técnicos Circular N°1835", uso: "Diccionario de datos y validación física/lógica de los archivos de cartera.", url: "https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf" },
  { fuente: "Banco Central de Chile", uso: "Dólar observado, UF, TPM e IPC de referencia de la cinta.", url: "https://si3.bcentral.cl/IndicadoresSiete/Excel/..." },
  { fuente: "Bolsa de Santiago / Bloomberg Línea", uso: "Cierres del IPSA y de emisores del índice.", url: "https://www.bolsadesantiago.com/" },
];

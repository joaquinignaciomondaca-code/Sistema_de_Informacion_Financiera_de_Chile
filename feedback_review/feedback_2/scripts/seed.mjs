/**
 * MFC seed — ejecutable con `node scripts/seed.mjs` DESPUES de
 * `npx drizzle-kit push`.
 *
 * 1. Crea el data plane de ejemplo (schema `mart`) + vistas gobernadas.
 * 2. Genera datos sintéticos deterministas (NO es información real).
 * 3. Construye el catálogo A PARTIR de las specs: columnas, joins derivados,
 *    run ledger y quality checks MEDIDOS contra los datos reales.
 */
import "dotenv/config";
import pg from "pg";

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });

/* ------------------------------------------------------------- utilidades */

function mulberry32(a) {
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rnd = mulberry32(20260215);
const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
const between = (lo, hi) => lo + rnd() * (hi - lo);
const round = (v, d = 2) => Number(v.toFixed(d));
const q = (s) => `"${s.replace(/"/g, '""')}"`;
const lit = (v) =>
  v === null || v === undefined
    ? "NULL"
    : typeof v === "number"
      ? String(v)
      : `'${String(v).replace(/'/g, "''")}'`;

const PERIODS = ["2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01"];
const LAST = PERIODS[PERIODS.length - 1];

/* --------------------------------------------------------------- data plane */

const DIM_ASEG = [
  { rut: "80.112.300-1", nombre: "Aseguradora Andes Vida S.A.", sector: "vida", region: "Metropolitana", estado: "Activa", inversion: 4_812_000, periodos: 7 },
  { rut: "80.221.400-2", nombre: "Cordillera Vida Chile", sector: "vida", region: "Metropolitana", estado: "Activa", inversion: 3_145_800, periodos: 7 },
  { rut: "80.334.500-3", nombre: "Pacífico Seguros de Vida", sector: "vida", region: "Valparaíso", estado: "Activa", inversion: 1_987_400, periodos: 6 },
  { rut: "80.445.600-4", nombre: "Bío Bío Vida Institucional", sector: "vida", region: "Biobío", estado: "Activa", inversion: 902_100, periodos: 7 },
  { rut: "80.556.700-5", nombre: "Aconcagua Vida S.A.", sector: "vida", region: "Metropolitana", estado: "En liquidación", inversion: 118_400, periodos: 4 },
  { rut: "81.112.800-6", nombre: "Andes Generales Renta", sector: "generales", region: "Metropolitana", estado: "Activa", inversion: 2_210_500, periodos: 7 },
  { rut: "81.221.900-7", nombre: "Mar Seguros Generales", sector: "generales", region: "Antofagasta", estado: "Activa", inversion: 1_104_300, periodos: 7 },
];

const INSTRUMENTS = [
  { nemotecnico: "BCP0123435001", tipo: "Bono Hypothecarius", emisor: "Banco de Crédito", moneda: "CLP", riesgo: "Grado de inversión", sector: "Banca" },
  { nemotecnico: "SCIA281026001", tipo: "Banco Central", emisor: "Banco Central", moneda: "CLF", riesgo: "Soberano", sector: "Fiscal" },
  { nemotecnico: "MOP2207150001", tipo: "Mercado de Dinero", emisor: "Tesorería General", moneda: "CLP", riesgo: "Soberano", sector: "Fiscal" },
  { nemotecnico: "CHILE", tipo: "Acción", emisor: "Liquen Group", moneda: "CLP", riesgo: "Mercado", sector: "Retail" },
  { nemotecnico: "BCI", tipo: "Acción", emisor: "Banco de Chile", moneda: "CLP", riesgo: "Mercado", sector: "Banca" },
  { nemotecnico: "SQM-B", tipo: "Acción", emisor: "SQM", moneda: "CLP", riesgo: "Mercado", sector: "Minería no metálica" },
  { nemotecnico: "CMPC", tipo: "Acción", emisor: "Empresas CMPC", moneda: "CLP", riesgo: "Mercado", sector: "Forestal" },
  { nemotecnico: "CAP", tipo: "Acción", emisor: "CAP S.A.", moneda: "CLP", riesgo: "Mercado", sector: "Siderurgia" },
  { nemotecnico: "ENELGXCH", tipo: "Acción", emisor: "Enel Chile", moneda: "CLP", riesgo: "Mercado", sector: "Eléctricidad" },
  { nemotecnico: "FORWARD-USD-360", tipo: "Forward", emisor: "OTC", moneda: "USD", riesgo: "Contraparte", sector: "Derivados" },
];

async function createDataPlane(client) {
  await client.query(`DROP SCHEMA IF EXISTS mart CASCADE`);
  await client.query(`CREATE SCHEMA mart`);

  await client.query(`
    CREATE TABLE mart.dim_periodo (
      period_key text PRIMARY KEY,
      anio integer NOT NULL,
      mes integer NOT NULL,
      trimestre text NOT NULL,
      cierre_label text NOT NULL,
      is_quarter_end boolean NOT NULL
    );
    CREATE TABLE mart.dim_aseguradora (
      rut text PRIMARY KEY,
      nombre text NOT NULL,
      sector text NOT NULL,
      region text NOT NULL,
      estado text NOT NULL,
      ultimo_periodo text,
      inversion_ultimo_reporte_m_clp numeric(18,2),
      periodos_reportados integer
    );
    CREATE TABLE mart.ref_instrumento (
      nemotecnico text PRIMARY KEY,
      tipo_activo text NOT NULL,
      emisor text NOT NULL,
      moneda text NOT NULL,
      riesgo_crediticio text,
      sector_economico text
    );
    CREATE TABLE mart.vida_bonos (
      id serial PRIMARY KEY, periodo text NOT NULL, rut_aseguradora text NOT NULL,
      nemotecnico text NOT NULL, tipo_bono text NOT NULL, emisor text NOT NULL,
      moneda text NOT NULL, tir_mercado_pct numeric(10,4), precio numeric(12,4),
      vencimiento date, duration_mod numeric(8,3), monto_m_clp numeric(18,2),
      calificador text
    );
    CREATE TABLE mart.vida_acciones (
      id serial PRIMARY KEY, periodo text NOT NULL, rut_aseguradora text NOT NULL,
      nemotecnico text NOT NULL, precio_cierre_clp numeric(14,2),
      presencia_pct numeric(8,4), capitalizacion_m_clp numeric(18,2),
      rentabilidad_mensual_pct numeric(8,4)
    );
    CREATE TABLE mart.vida_bienes_raices (
      id serial PRIMARY KEY, periodo text NOT NULL, rut_aseguradora text NOT NULL,
      comuna text NOT NULL, tipo_propiedad text NOT NULL, propiedades integer,
      tasacion_comercial_m_clp numeric(18,2), arriendo_anual_m_clp numeric(18,2),
      ocupacion_pct numeric(6,2)
    );
    CREATE TABLE mart.vida_solvencia (
      id serial PRIMARY KEY, periodo text NOT NULL, rut_aseguradora text NOT NULL,
      rubro_caratula text NOT NULL, total_inversion_m_clp numeric(18,2),
      patrimonio_adj_m_clp numeric(18,2), requerido_m_clp numeric(18,2),
      cobertura_pct numeric(8,3)
    );
    CREATE TABLE mart.generales_bonos (
      id serial PRIMARY KEY, periodo text NOT NULL, rut_aseguradora text NOT NULL,
      nemotecnico text NOT NULL, tipo_bono text NOT NULL, moneda text NOT NULL,
      tir_mercado_pct numeric(10,4), monto_m_clp numeric(18,2)
    );
    CREATE TABLE mart.generales_siniestros (
      id serial PRIMARY KEY, periodo text NOT NULL, rut_aseguradora text NOT NULL,
      ramo text NOT NULL, prima_emitida_m_clp numeric(18,2),
      siniestro_ocurrido_m_clp numeric(18,2), siniestros_cantidad integer,
      loss_ratio_pct numeric(8,3), reserva_ibnr_m_clp numeric(18,2)
    );
    CREATE TABLE mart.ffmm_fondos (
      id serial PRIMARY KEY, periodo text NOT NULL, codigo_fondo text NOT NULL,
      nombre_fondo text NOT NULL, tipo_fondo text NOT NULL, administradora text NOT NULL,
      patrimonio_m_clp numeric(18,2), rentabilidad_mensual_pct numeric(8,4),
      liquidez_pct numeric(6,2), inversores integer
    );
    CREATE TABLE mart.ffii_repos (
      id serial PRIMARY KEY, periodo text NOT NULL, codigo_operacion text NOT NULL,
      nombre_contraparte text NOT NULL, tasa_pct numeric(8,4), plazo_dias integer,
      valorizacion_cierre_m_clp numeric(18,2), garantia text NOT NULL
    );
    CREATE TABLE mart.derivatives_forwards (
      id serial PRIMARY KEY, periodo text NOT NULL, codigo_operacion text NOT NULL,
      nombre_contraparte text NOT NULL, sentido text NOT NULL, subyacente text NOT NULL,
      precio_forward_pactado numeric(12,4), nocional_m_clp numeric(18,2),
      vencimiento date
    );
  `);

  /* --- vistas gobernadas: la unidad que se publica, no la tabla cruda --- */
  await client.query(`
    CREATE VIEW mart.v_maestro_aseguradoras AS
    SELECT
      a.rut AS rut_aseguradora,
      a.nombre AS nombre_aseguradora,
      a.sector,
      a.region,
      a.estado,
      a.ultimo_periodo,
      a.inversion_ultimo_reporte_m_clp,
      a.periodos_reportados,
      COALESCE(s.periodos_cubiertos, 0) AS periodos_cubiertos,
      CASE WHEN a.periodos_reportados >= 6 THEN 'Completo' ELSE 'Parcial' END AS estado_cobertura
    FROM mart.dim_aseguradora a
    LEFT JOIN (
      SELECT rut_aseguradora, count(DISTINCT periodo) AS periodos_cubiertos
      FROM mart.vida_solvencia GROUP BY 1
    ) s ON s.rut_aseguradora = a.rut;

    CREATE VIEW mart.v_inversion_consolidada AS
    SELECT 'vida' AS dominio, 'Bonos' AS clase_activo, periodo, sum(monto_m_clp) AS monto_m_clp,
           count(*) AS posiciones FROM mart.vida_bonos GROUP BY 1,2,3
    UNION ALL
    SELECT 'vida', 'Acciones', periodo, sum(capitalizacion_m_clp * presencia_pct / 100.0), count(*)
    FROM mart.vida_acciones GROUP BY 1,2,3
    UNION ALL
    SELECT 'vida', 'Bienes raíces', periodo, sum(tasacion_comercial_m_clp), count(*)
    FROM mart.vida_bienes_raices GROUP BY 1,2,3
    UNION ALL
    SELECT 'generales', 'Bonos', periodo, sum(monto_m_clp), count(*) FROM mart.generales_bonos GROUP BY 1,2,3
    UNION ALL
    SELECT 'ffmm', 'Depósitos a plazo', periodo, sum(patrimonio_m_clp), count(*) FROM mart.ffmm_fondos GROUP BY 1,2,3
    UNION ALL
    SELECT 'fi', 'Repo', periodo, sum(valorizacion_cierre_m_clp), count(*) FROM mart.ffii_repos GROUP BY 1,2,3;
  `);
}

async function insertRows(client, table, cols, rows) {
  if (!rows.length) return 0;
  const values = rows
    .map((r) => `(${r.map((v) => lit(v)).join(", ")})`)
    .join(",\n");
  await client.query(
    `INSERT INTO mart.${table} (${cols.map(q).join(", ")}) VALUES ${values}`,
  );
  return rows.length;
}

async function seedFacts(client) {
  /* dims */
  await insertRows(
    client,
    "dim_periodo",
    ["period_key", "anio", "mes", "trimestre", "cierre_label", "is_quarter_end"],
    PERIODS.map((p) => {
      const [y, m] = p.split("-").map(Number);
      const tq = `T${Math.ceil(m / 3)}`;
      return [p, y, m, tq, m === 12 ? "Cierre anual" : `Cierre ${tq}`, m % 3 === 0];
    }),
  );
  await insertRows(
    client,
    "dim_aseguradora",
    ["rut", "nombre", "sector", "region", "estado", "ultimo_periodo", "inversion_ultimo_reporte_m_clp", "periodos_reportados"],
    DIM_ASEG.map((a) => [a.rut, a.nombre, a.sector, a.region, a.estado, a.estado === "En liquidación" ? "2025-10" : LAST, a.inversion, a.periodos]),
  );
  await insertRows(
    client,
    "ref_instrumento",
    ["nemotecnico", "tipo_activo", "emisor", "moneda", "riesgo_crediticio", "sector_economico"],
    INSTRUMENTS.map((i) => [i.nemotecnico, i.tipo, i.emisor, i.moneda, i.riesgo, i.sector]),
  );

  const bonosVida = [];
  const bonosGen = [];
  const acciones = [];
  const br = [];
  const solv = [];
  const siniest = [];
  const fondos = [];
  const repos = [];
  const fwd = [];
  const ruts = { vida: DIM_ASEG.filter((a) => a.sector === "vida").map((a) => a.rut), generales: DIM_ASEG.filter((a) => a.sector === "generales").map((a) => a.rut) };
  const bonosIns = INSTRUMENTS.filter((i) => i.tipo !== "Acción" && i.tipo !== "Forward");
  const accIns = INSTRUMENTS.filter((i) => i.tipo === "Acción");

  for (const [pi, periodo] of PERIODS.entries()) {
    for (const rut of ruts.vida) {
      for (const ins of bonosIns) {
        for (let k = 0; k < 2; k++) {
          bonosVida.push([
            periodo, rut, ins.nemotecnico, ins.tipo, ins.emisor, ins.moneda,
            round(between(3.1, 7.4), 4), round(between(21.4, 118.9), 4),
            `${2027 + Math.floor(rnd() * 9)}-${String(1 + Math.floor(rnd() * 12)).padStart(2, "0")}-15`,
            round(between(0.4, 8.7), 3),
            round(between(4_200, 268_000) * (1 + pi * 0.01), 2),
            pick(["Feller Rate", "Hercules", "ICRA", "Fitch"]),
          ]);
        }
      }
      for (const ins of accIns) {
        acciones.push([
          periodo, rut, ins.nemotecnico, round(between(18.6, 12_400), 2),
          round(between(0.05, 9.4), 4), round(between(120_000, 4_900_000), 2),
          round(between(-11.4, 13.8), 4),
        ]);
      }
      for (const comuna of ["Las Condes", "Providencia", "Santiago", "Ñuñoa", "Concepción", "Viña del Mar"]) {
        br.push([
          periodo, rut, comuna, pick(["Oficina", "Bodega", "Local comercial", "Sitio eriaz"]),
          Math.floor(between(1, 14)), round(between(9_800, 410_000), 2),
          round(between(240, 9_800), 2), round(between(52, 99), 2),
        ]);
      }
      for (const rubro of ["Rentas inmobiliarias", "Depósitos a plazo", "Acciones", "Bonos y efectos de comercio", "Cuotas de fondos mutuos", "Operaciones con repo"]) {
        const inv = round(between(50_000, 1_450_000), 2);
        const req = round(between(20_000, 640_000), 2);
        solv.push([periodo, rut, rubro, inv, round(req * between(1.05, 2.3), 2), req, round((inv / req) * 100, 3)]);
      }
    }

    for (const rut of ruts.generales) {
      for (const ins of bonosIns) {
        bonosGen.push([periodo, rut, ins.nemotecnico, ins.tipo, ins.moneda, round(between(3.4, 7.9), 4), round(between(12_000, 210_000), 2)]);
      }
      for (const ramo of ["Automotriz", "Incendio", "Robo", "Responsabilidad civil", "Personas", "Transporte de carga"]) {
        const prima = round(between(18_000, 240_000), 2);
        const sin = round(prima * between(0.41, 0.97), 2);
        siniest.push([periodo, rut, ramo, prima, sin, Math.floor(between(40, 1800)), round((sin / prima) * 100, 3), round(sin * between(0.18, 0.61), 2)]);
      }
    }

    for (const f of [
      ["FM001", "Fondo Mutuo Estratégico Renta Fija", "Renta fija nominal"],
      ["FM002", "Fondo Mutuo Acciones Chile", "Renta variable"],
      ["FM003", "Fondo Mutuo Dollar", "Internacional"],
      ["FM004", "Fondo Mutuo Corporativo 90", "Renta fija corporativa"],
      ["FM005", "Fondo Mutuo Equilibrado", "Mixto"],
    ]) {
      fondos.push([
        periodo, f[0], f[1], f[2], pick(["BICE Asset Management", "BTG Pactual AM", "Sterling Asset Chile", "Moneda Asset"]),
        round(between(42_000, 1_890_000), 2), round(between(-4.8, 6.2), 4), round(between(4, 46), 2), Math.floor(between(180, 24_000)),
      ]);
    }

    for (const cp of ["Banco Security", "Banco de Crédito e Inversiones", "BTG Pactual Chile", "Banco Consorcio", "Itaú Chile", "Banco Estado"]) {
      repos.push([periodo, `REPO-${periodo.replace("-", "")}-${cp.slice(0, 3).toUpperCase()}-${Math.floor(between(100, 999))}`, cp, round(between(4.1, 8.9), 4), Math.floor(between(1, 180)), round(between(6_400, 340_000), 2), pick(["Banco Central", "Bonos MPR", "Depósitos a plazo"])]);
    }

    for (const cp of ["Banco Santander", "Scotiabank Chile", "Banco Security", "Itaú Chile", "BTG Pactual Chile"]) {
      fwd.push([periodo, `FWD-${periodo.replace("-", "")}-${Math.floor(between(1000, 9999))}`, cp, pick(["Compra", "Venta"]), pick(["USD/CLP", "EUR/CLP", "UF/CLP"]), round(between(905.4, 1042.8), 4), round(between(12_000, 520_000), 2), `${2026}-${String(1 + Math.floor(rnd() * 12)).padStart(2, "0")}-${String(1 + Math.floor(rnd() * 27)).padStart(2, "0")}`]);
    }
  }

  const counts = {};
  counts.vida_bonos = await insertRows(client, "vida_bonos", ["periodo", "rut_aseguradora", "nemotecnico", "tipo_bono", "emisor", "moneda", "tir_mercado_pct", "precio", "vencimiento", "duration_mod", "monto_m_clp", "calificador"], bonosVida);
  counts.generales_bonos = await insertRows(client, "generales_bonos", ["periodo", "rut_aseguradora", "nemotecnico", "tipo_bono", "moneda", "tir_mercado_pct", "monto_m_clp"], bonosGen);
  counts.vida_acciones = await insertRows(client, "vida_acciones", ["periodo", "rut_aseguradora", "nemotecnico", "precio_cierre_clp", "presencia_pct", "capitalizacion_m_clp", "rentabilidad_mensual_pct"], acciones);
  counts.vida_bienes_raices = await insertRows(client, "vida_bienes_raices", ["periodo", "rut_aseguradora", "comuna", "tipo_propiedad", "propiedades", "tasacion_comercial_m_clp", "arriendo_anual_m_clp", "ocupacion_pct"], br);
  counts.vida_solvencia = await insertRows(client, "vida_solvencia", ["periodo", "rut_aseguradora", "rubro_caratula", "total_inversion_m_clp", "patrimonio_adj_m_clp", "requerido_m_clp", "cobertura_pct"], solv);
  counts.generales_siniestros = await insertRows(client, "generales_siniestros", ["periodo", "rut_aseguradora", "ramo", "prima_emitida_m_clp", "siniestro_ocurrido_m_clp", "siniestros_cantidad", "loss_ratio_pct", "reserva_ibnr_m_clp"], siniest);
  counts.ffmm_fondos = await insertRows(client, "ffmm_fondos", ["periodo", "codigo_fondo", "nombre_fondo", "tipo_fondo", "administradora", "patrimonio_m_clp", "rentabilidad_mensual_pct", "liquidez_pct", "inversores"], fondos);
  counts.ffii_repos = await insertRows(client, "ffii_repos", ["periodo", "codigo_operacion", "nombre_contraparte", "tasa_pct", "plazo_dias", "valorizacion_cierre_m_clp", "garantia"], repos);
  counts.derivatives_forwards = await insertRows(client, "derivatives_forwards", ["periodo", "codigo_operacion", "nombre_contraparte", "sentido", "subyacente", "precio_forward_pactado", "nocional_m_clp", "vencimiento"], fwd);
  return counts;
}

/* ------------------------------------------------------- specs del catálogo */

const col = (name, type, description, extra = {}) => ({ name, type, description, ...extra });

const DATASET_SPECS = [
  {
    domain: "comun",
    name: "dim_periodo",
    table: "dim_periodo",
    layer: "dim",
    grain: "1 fila por período contable (YYYY-MM)",
    owner: "plataforma-datos",
    desc: "Calendario de cierres regulatorios. Clave conformada que permite comparar Vida, Generales, FFMM y FFII en el mismo eje temporal.",
    slo: 8760,
    cadence: "anual",
    cols: [
      col("period_key", "text", "Clave del período", { pk: true, nn: true }),
      col("anio", "integer", "Año contable", { nn: true }),
      col("mes", "integer", "Mes 1-12", { nn: true }),
      col("trimestre", "text", "T1..T4"),
      col("cierre_label", "text", "Etiqueta de cierre regulatorio"),
      col("is_quarter_end", "boolean", "true si corresponde a cierre trimestral"),
    ],
  },
  {
    domain: "vida",
    name: "dim_aseguradora",
    table: "dim_aseguradora",
    layer: "dim",
    grain: "1 fila por entidad fiscalizada",
    owner: "equipo-vida",
    desc: "Maestro de entidades. RUT normalizado (sin puntos, con dígito verificador) para que el join con hechos sea estable entre circulares.",
    slo: 8760,
    cadence: "por reporte",
    cols: [
      col("rut", "text", "RUT con dígito verificador", { pk: true, nn: true, masking: "none" }),
      col("nombre", "text", "Razón social", { nn: true }),
      col("sector", "text", "vida | generales", { nn: true }),
      col("region", "text", "Región de domicilio"),
      col("estado", "text", "Activa | En liquidación", { nn: true }),
      col("ultimo_periodo", "text", "Último período informado", { fk: ["dim_periodo", "period_key"] }),
      col("inversion_ultimo_reporte_m_clp", "numeric", "Inversiones totales último reporte", { unit: "MMCLP" }),
      col("periodos_reportados", "integer", "N° de períodos con información"),
    ],
  },
  {
    domain: "vida",
    name: "ref_instrumento",
    table: "ref_instrumento",
    layer: "dim",
    grain: "1 fila por instrumento",
    owner: "plataforma-datos",
    desc: "Referencia de instrumentos. El nemotecnico es la clave conformada entre bonos, acciones y derivados.",
    slo: 2160,
    cadence: "diaria",
    cols: [
      col("nemotecnico", "text", "Nemotécnico de mercado", { pk: true, nn: true }),
      col("tipo_activo", "text", "Banco Central | Hypothecarius | Acción | Forward ...", { nn: true }),
      col("emisor", "text", "Emisor del instrumento", { nn: true }),
      col("moneda", "text", "CLP | CLF | USD", { nn: true }),
      col("riesgo_crediticio", "text", "Clasificación de riesgo"),
      col("sector_economico", "text", "Sector GICS-style del emisor"),
    ],
  },
  {
    domain: "vida",
    name: "cartera_bonos",
    table: "vida_bonos",
    layer: "fact",
    grain: "tenencia · instrumento · período",
    owner: "equipo-vida",
    desc: "Detalle de tenencias de renta fija de aseguradoras de vida (Anexos 3 y 5 de la Circular 1835). TIR y duration provienen del reporte, no se recalculan.",
    slo: 720,
    cadence: "mensual",
    model: "models/vida/cartera_bonos.sql",
    tags: "inversiones,circular-1835,core",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período del anexo", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("rut_aseguradora", "text", "Entidad reportante", { nn: true, fk: ["dim_aseguradora", "rut"] }),
      col("nemotecnico", "text", "Instrumento", { nn: true, fk: ["ref_instrumento", "nemotecnico"] }),
      col("tipo_bono", "text", "Clase de bono", { nn: true }),
      col("emisor", "text", "Emisor reportado"),
      col("moneda", "text", "Moneda de contratación", { nn: true }),
      col("tir_mercado_pct", "numeric", "TIR de mercado", { unit: "%", range: [0, 30], nn: true }),
      col("precio", "numeric", "Precio de cierre", { range: [0, 10000] }),
      col("vencimiento", "date", "Vencimiento final"),
      col("duration_mod", "numeric", "Duration modificada", { range: [0, 40] }),
      col("monto_m_clp", "numeric", "Monto en miles de CLP", { unit: "MMCLP", nn: true, range: [0, 1e9] }),
      col("calificador", "text", "Calificadora de riesgo"),
    ],
  },
  {
    domain: "vida",
    name: "cartera_acciones",
    table: "vida_acciones",
    layer: "fact",
    grain: "emisor · período",
    owner: "equipo-vida",
    desc: "Renta variable chilena con presencia relativa sobre el fondo de inversiones (Anexo 6).",
    slo: 720,
    cadence: "mensual",
    model: "models/vida/cartera_acciones.sql",
    tags: "inversiones,circular-1835",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("rut_aseguradora", "text", "Entidad reportante", { nn: true, fk: ["dim_aseguradora", "rut"] }),
      col("nemotecnico", "text", "Nemotécnico IPSA", { nn: true, fk: ["ref_instrumento", "nemotecnico"] }),
      col("precio_cierre_clp", "numeric", "Precio de cierre", { unit: "CLP", range: [0, 1e6] }),
      col("presencia_pct", "numeric", "Participación en la cartera", { unit: "%", range: [0, 100] }),
      col("capitalizacion_m_clp", "numeric", "Capitalización de mercado", { unit: "MMCLP" }),
      col("rentabilidad_mensual_pct", "numeric", "Rentabilidad del mes", { unit: "%" }),
    ],
  },
  {
    domain: "vida",
    name: "cartera_bienes_raices",
    table: "vida_bienes_raices",
    layer: "fact",
    grain: "comuna · tipo · período",
    owner: "equipo-vida",
    desc: "Inversiones inmobiliarias tasadas a valor comercial (Anexo 8). Volumen bajo pero alto impacto en solvencia.",
    slo: 2160,
    cadence: "trimestral",
    model: "models/vida/cartera_bienes_raices.sql",
    tags: "inversiones,inmobiliario",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("rut_aseguradora", "text", "Entidad", { nn: true, fk: ["dim_aseguradora", "rut"] }),
      col("comuna", "text", "Comuna del inmueble", { nn: true }),
      col("tipo_propiedad", "text", "Oficina | Bodega | Local | Sitio"),
      col("propiedades", "integer", "N° de propiedades", { range: [0, 500] }),
      col("tasacion_comercial_m_clp", "numeric", "Tasación comercial", { unit: "MMCLP", nn: true }),
      col("arriendo_anual_m_clp", "numeric", "Arriendo anual", { unit: "MMCLP" }),
      col("ocupacion_pct", "numeric", "Ocupación", { unit: "%", range: [0, 100] }),
    ],
  },
  {
    domain: "vida",
    name: "cartera_solvencia",
    table: "vida_solvencia",
    layer: "fact",
    grain: "rubro de carátula · entidad · período",
    owner: "equipo-vida",
    desc: "Balance de inversiones por rubro de carátula vs. requerimiento de solvencia. Fuente de la mayoría de los KPI del monitor.",
    slo: 720,
    cadence: "mensual",
    model: "models/vida/cartera_solvencia.sql",
    tags: "solvencia,core",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("rut_aseguradora", "text", "Entidad", { nn: true, fk: ["dim_aseguradora", "rut"] }),
      col("rubro_caratula", "text", "Rubro del balance de inversiones", { nn: true }),
      col("total_inversion_m_clp", "numeric", "Inversión total del rubro", { unit: "MMCLP", nn: true }),
      col("patrimonio_adj_m_clp", "numeric", "Patrimonio adjudicado", { unit: "MMCLP" }),
      col("requerido_m_clp", "numeric", "Requerimiento de solvencia", { unit: "MMCLP" }),
      col("cobertura_pct", "numeric", "Cobertura = inversión / requerido", { unit: "%", range: [0, 1000] }),
    ],
  },
  {
    domain: "generales",
    name: "cartera_bonos",
    table: "generales_bonos",
    layer: "fact",
    grain: "tenencia · instrumento · período",
    owner: "equipo-generales",
    desc: "Renta fija de aseguradoras generales. Misma granularidad que Vida a propósito: las dos tablas comparten claves conformadas para poder consolidar.",
    slo: 720,
    cadence: "mensual",
    model: "models/generales/cartera_bonos.sql",
    tags: "inversiones,circular-1836",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("rut_aseguradora", "text", "Entidad", { nn: true, fk: ["dim_aseguradora", "rut"] }),
      col("nemotecnico", "text", "Instrumento", { nn: true, fk: ["ref_instrumento", "nemotecnico"] }),
      col("tipo_bono", "text", "Clase de bono"),
      col("moneda", "text", "Moneda"),
      col("tir_mercado_pct", "numeric", "TIR de mercado", { unit: "%", range: [0, 30] }),
      col("monto_m_clp", "numeric", "Monto", { unit: "MMCLP", nn: true }),
    ],
  },
  {
    domain: "generales",
    name: "siniestros",
    table: "generales_siniestros",
    layer: "fact",
    grain: "ramo · entidad · período",
    owner: "equipo-generales",
    desc: "Siniestralidad por ramo: prima emitida, siniestro ocurrido, cantidad y reserva IBNR. Loss ratio calculado en el modelo, no en el dashboard.",
    slo: 360,
    cadence: "mensual",
    model: "models/generales/siniestros.sql",
    tags: "siniestralidad,core",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("rut_aseguradora", "text", "Entidad", { nn: true, fk: ["dim_aseguradora", "rut"] }),
      col("ramo", "text", "Ramo asegurador", { nn: true }),
      col("prima_emitida_m_clp", "numeric", "Prima emitida", { unit: "MMCLP", nn: true }),
      col("siniestro_ocurrido_m_clp", "numeric", "Siniestro ocurrido", { unit: "MMCLP" }),
      col("siniestros_cantidad", "integer", "N° de siniestros"),
      col("loss_ratio_pct", "numeric", "Loss ratio", { unit: "%", range: [0, 100] }),
      col("reserva_ibnr_m_clp", "numeric", "Reserva IBNR", { unit: "MMCLP" }),
    ],
  },
  {
    domain: "ffmm",
    name: "fondos_mutuos",
    table: "ffmm_fondos",
    layer: "fact",
    grain: "fondo · período",
    owner: "equipo-ffmm",
    desc: "Indicadores de fondos mutuos fiscalizados (Ley 18.815, Normas Letra A). Patrimonio y liquidez en miles de CLP.",
    slo: 24,
    cadence: "diaria hábil",
    model: "models/ffmm/fondos_mutuos.sql",
    tags: "ffmm,liquidez",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("codigo_fondo", "text", "Código interno del fondo", { nn: true }),
      col("nombre_fondo", "text", "Nombre comercial", { nn: true }),
      col("tipo_fondo", "text", "Categoría regulatoria"),
      col("administradora", "text", "Administradora general de fondos"),
      col("patrimonio_m_clp", "numeric", "Patrimonio", { unit: "MMCLP", nn: true }),
      col("rentabilidad_mensual_pct", "numeric", "Rentabilidad mensual", { unit: "%" }),
      col("liquidez_pct", "numeric", "Liquidez inmediata", { unit: "%", range: [0, 100] }),
      col("inversores", "integer", "N° de partícipes"),
    ],
  },
  {
    domain: "fi",
    name: "repos",
    table: "ffii_repos",
    layer: "fact",
    grain: "operación de repo · período",
    owner: "equipo-ffii",
    desc: "Operaciones de compraventa con pacto de retrovio (repo) de fondos de inversión. Concentración de contrapartes es el riesgo que se monitorea.",
    slo: 24,
    cadence: "diaria hábil",
    model: "models/ffii/repos.sql",
    tags: "repos,contraparte",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("codigo_operacion", "text", "ID de operación", { pk: true, nn: true }),
      col("nombre_contraparte", "text", "Contraparte (aun sin normalizar a RUT: deuda de datos)"),
      col("tasa_pct", "numeric", "Tasa pactada", { unit: "%", range: [0, 30] }),
      col("plazo_dias", "integer", "Plazo en días"),
      col("valorizacion_cierre_m_clp", "numeric", "Valorización de cierre", { unit: "MMCLP", nn: true }),
      col("garantia", "text", "Garantía entregada"),
    ],
  },
  {
    domain: "fi",
    name: "forwards_otc",
    table: "derivatives_forwards",
    layer: "fact",
    grain: "contrato forward · período",
    owner: "equipo-derivados",
    desc: "Derivados OTC reportados en Formulario B-7. Nocional y precio pactado; el valor de reposición se calcula aguas abajo.",
    slo: 168,
    cadence: "mensual",
    model: "models/derivados/forwards.sql",
    tags: "derivados,b7",
    cols: [
      col("id", "integer", "Surrogado", { pk: true, nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("codigo_operacion", "text", "ID de contrato", { nn: true }),
      col("nombre_contraparte", "text", "Contraparte"),
      col("sentido", "text", "Compra | Venta"),
      col("subyacente", "text", "Par de divisas / índice"),
      col("precio_forward_pactado", "numeric", "Precio forward pactado", { range: [0, 1e5] }),
      col("nocional_m_clp", "numeric", "Nocional", { unit: "MMCLP", nn: true }),
      col("vencimiento", "date", "Fecha de vencimiento"),
    ],
  },
  {
    domain: "vida",
    name: "v_maestro_aseguradoras",
    table: "v_maestro_aseguradoras",
    layer: "view",
    grain: "entidad",
    owner: "plataforma-datos",
    desc: "Vista gobernada y versionada. ES la superficie pública: los consumidores leen esta vista, nunca la dim cruda, para poder cambiar el modelo sin romper dashboards.",
    slo: 720,
    cadence: "mensual",
    model: "models/semantic/v_maestro_aseguradoras.sql",
    tags: "semantic-layer,public",
    cols: [
      col("rut_aseguradora", "text", "RUT"),
      col("nombre_aseguradora", "text", "Razón social"),
      col("sector", "text", "vida | generales"),
      col("region", "text", "Región"),
      col("estado", "text", "Estado regulatorio"),
      col("ultimo_periodo", "text", "Último período", { fk: ["dim_periodo", "period_key"] }),
      col("inversion_ultimo_reporte_m_clp", "numeric", "Inversión último reporte", { unit: "MMCLP" }),
      col("periodos_reportados", "integer", "Períodos informados"),
      col("periodos_cubiertos", "integer", "Períodos con solvencia materializada"),
      col("estado_cobertura", "text", "Completo | Parcial"),
    ],
    edges: [
      ["dim_aseguradora", "rut", "rut_aseguradora", "view_union"],
    ],
  },
  {
    domain: "comun",
    name: "v_inversion_consolidada",
    table: "v_inversion_consolidada",
    layer: "view",
    grain: "dominio · clase de activo · período",
    owner: "plataforma-datos",
    desc: "Capa semántica transversal: un solo lugar donde Vida, Generales, FFMM y FFII significan lo mismo. Es la vista que deberían consumir los dashboards.",
    slo: 720,
    cadence: "mensual",
    model: "models/semantic/v_inversion_consolidada.sql",
    tags: "semantic-layer,core,public",
    cols: [
      col("dominio", "text", "vida | generales | ffmm | fi", { nn: true }),
      col("clase_activo", "text", "Clase normalizada", { nn: true }),
      col("periodo", "text", "Período", { nn: true, fk: ["dim_periodo", "period_key"] }),
      col("monto_m_clp", "numeric", "Monto consolidado", { unit: "MMCLP" }),
      col("posiciones", "integer", "N° de posiciones que componen el monto"),
    ],
    edges: [
      ["cartera_bonos", "periodo", "periodo", "view_union"],
      ["cartera_solvencia", "periodo", "periodo", "view_union"],
    ],
  },
];

const DOMAINS = [
  { slug: "vida", name: "Seguros de Vida", kind: "vida", regulator: "CMF", team: "equipo-vida", contact: "vida-data@mfchile.cl", desc: "Fondo de inversiones y solvencia de las 5 aseguradoras de vida fiscalizadas." },
  { slug: "generales", name: "Seguros Generales", kind: "generales", regulator: "CMF", team: "equipo-generales", contact: "generales-data@mfchile.cl", desc: "Cartera de inversiones y siniestralidad por ramo." },
  { slug: "ffmm", name: "Fondos Mutuos", kind: "ffmm", regulator: "CMF", team: "equipo-ffmm", contact: "ffmm-data@mfchile.cl", desc: "Indicadores de fondos mutuos y liquidez bajo Ley 18.815." },
  { slug: "fi", name: "Fondos de Inversión", kind: "fi", regulator: "CMF", team: "equipo-ffii", contact: "ffii-data@mfchile.cl", desc: "Repos, derivados OTC y concentración de contrapartes." },
  { slug: "comun", name: "Dimensiones compartidas", kind: "dim", regulator: "—", team: "plataforma-datos", contact: "platform@mfchile.cl", desc: "Claves conformadas y calendario: la pieza que hace que todo lo demás se pueda unir." },
];

const SOURCES = {
  vida: [["Circular 1835", "Normas sobre inversiones de las aseguradoras de vida", "CMF", "2019-06-01", "https://www.cmfchile.cl", true], ["IFRS 17 · Nota 12", "Reconocimiento de contratos de seguro y desglose de activos financieros", "IASB", "2023-01-01", "https://www.ifrs.org", true]],
  generales: [["Circular 1836", "Normas sobre inversiones de las aseguradoras generales", "CMF", "2019-06-01", "https://www.cmfchile.cl", true], ["Formulario B-7", "Derivados OTC: nocional, contrapartes y vencimientos", "CMF", "2021-03-01", "https://www.cmfchile.cl", false]],
  ffmm: [["Ley 18.815 · Normas Letra A", "Información mensual de fondos mutuos fiscalizados", "CMF", "2018-01-01", "https://www.cmfchile.cl", true]],
  fi: [["Ley 20.712", "Fondos de inversión y fondos de inversión cerrados", "CMF", "2014-01-01", "https://www.cmfchile.cl", true], ["Anexo 3 · Repos", "Operaciones con pacto de retrovo y garantías", "CMF", "2020-07-01", "https://www.cmfchile.cl", true]],
  comun: [["Estándar interno MFC", "Convención de claves conformadas (RUT, nemotécnico, YYYY-MM)", "Plataforma de datos", null, null, true]],
};

/* ------------------------------------------------------------- catálogo */

async function seedCatalog(client, counts) {
  await client.query(`TRUNCATE TABLE
      catalog.quality_checks, catalog.ingest_runs, catalog.dataset_relations,
      catalog.dataset_columns, catalog.datasets, catalog.saved_queries,
      catalog.query_log, catalog.sources, catalog.domains RESTART IDENTITY CASCADE`);

  const domainId = new Map();
  for (const d of DOMAINS) {
    const res = await client.query(
      `INSERT INTO catalog.domains (slug,name,kind,regulator,owner_team,owner_contact,description)
       VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id`,
      [d.slug, d.name, d.kind, d.regulator, d.team, d.contact, d.desc],
    );
    domainId.set(d.slug, res.rows[0].id);
  }

  const sourceIdByName = new Map();
  for (const [dom, list] of Object.entries(SOURCES)) {
    for (const [code, title, issuer, eff, url, mandatory] of list) {
      const res = await client.query(
        `INSERT INTO catalog.sources (domain_id,code,title,issuer,effective_date,url,mandatory)
         VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id, code`,
        [domainId.get(dom), code, title, issuer, eff, url, mandatory],
      );
      sourceIdByName.set(res.rows[0].code, res.rows[0].id);
    }
  }
  const sourceFor = (dom, spec) => {
    const map = {
      vida_bonos: "Circular 1835", vida_acciones: "Circular 1835", vida_bienes_raices: "Circular 1835",
      vida_solvencia: "Circular 1835", generales_bonos: "Circular 1836", derivatives_forwards: "Formulario B-7",
      ffmm_fondos: "Ley 18.815 · Normas Letra A", ffii_repos: "Anexo 3 · Repos",
    };
    const key = map[spec.table];
    return key ? sourceIdByName.get(key) ?? null : null;
  };

  const dsIdByName = new Map();
  for (const spec of DATASET_SPECS) {
    const rows = counts[spec.table];
    let rowCount = 0;
    let sizeMb = "0.0";
    if (spec.layer === "view") {
      const r = await client.query(`SELECT count(*)::int c FROM mart.${q(spec.table)}`);
      rowCount = r.rows[0].c;
      sizeMb = "0.1";
    } else {
      const r = await client.query(`SELECT count(*)::int c FROM mart.${q(spec.table)}`);
      rowCount = r.rows[0].c;
      const s = await client.query(
        `SELECT COALESCE(pg_total_relation_size('mart.' || quote_ident($1)) / 1048576.0, 0)::numeric(10,2) sz`,
        [spec.table],
      );
      sizeMb = s.rows[0].sz;
    }
    // frescura simulada: a propósitos dos datasets quedan fuera de SLO
    const lagHours = spec.table === "vida_bienes_raices" ? 3200 : spec.table === "ffii_repos" ? 96 : Math.round(between(2, 180));
    const lastRun = new Date(Date.now() - lagHours * 3600 * 1000);
    const status = lagHours > spec.slo ? "degraded" : "live";

    const res = await client.query(
      `INSERT INTO catalog.datasets
        (domain_id, source_id, name, physical_schema, physical_table, layer, grain, description, owner,
         refresh_cadence, freshness_slo_hours, row_count, size_mb, schema_version, status, access_policy,
         model_path, tags, last_materialized_at)
       VALUES ($1,$2,$3,'mart',$4,$5,$6,$7,$8,$9,$10,$11,$12,1,$13,$14,$15,$16,$17)
       RETURNING id`,
      [
        domainId.get(spec.domain), sourceFor(spec.domain, spec), spec.name, spec.table, spec.layer,
        spec.grain, spec.desc, spec.owner, spec.cadence ?? "mensual", spec.slo, rowCount, sizeMb, status,
        spec.layer === "view" ? "public" : "internal", spec.model ?? null, spec.tags ?? "", lastRun,
      ],
    );
    const datasetId = res.rows[0].id;
    dsIdByName.set(`${spec.domain}.${spec.name}`, datasetId);

    for (let i = 0; i < spec.cols.length; i++) {
      const c = spec.cols[i];
      await client.query(
        `INSERT INTO catalog.dataset_columns
          (dataset_id, ordinal, name, data_type, description, is_pk, nullable, masking, business_tag, unit)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,
        [datasetId, i + 1, c.name, c.type, c.description ?? "", !!c.pk, !c.nn, c.masking ?? "none", c.unit ? c.unit : null, c.unit ?? null],
      );
    }

    /* run ledger: 6 corridas, la última con el estado real */
    for (let k = 5; k >= 0; k--) {
      const started = new Date(lastRun.getTime() - k * 30 * 24 * 3600 * 1000);
      const failed = k === 2 && spec.table === "vida_bienes_raices";
      const durationMs = Math.round(between(4_200, 240_000));
      await client.query(
        `INSERT INTO catalog.ingest_runs
          (dataset_id, started_at, finished_at, status, rows_in, rows_out, rows_dropped, watermark, commit_sha, duration_ms, error_message)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`,
        [
          datasetId, started, new Date(started.getTime() + durationMs), failed ? "failed" : "success",
          Math.round((rows ?? rowCount) * between(0.95, 1.06)), rows ?? rowCount, failed ? 1_842 : 0,
          PERIODS[PERIODS.length - 1 - Math.min(k, 5)], `a1b9c${k}f${datasetId}`, durationMs,
          failed ? "schema drift: columna 'bodega_id' ausente en el archivo fuente" : null,
        ],
      );
    }

    /* quality checks MEDIDOS sobre los datos */
    const checks = [];
    checks.push(["freshness", `hours_since(last_materialized) <= ${spec.slo}`, lagHours <= spec.slo, lagHours, spec.slo, "error"]);
    checks.push(["volume", `count(*) > 0`, rowCount > 0, rowCount, 1, "error"]);
    const nnCol = spec.cols.find((c) => c.nn);
    if (nnCol) {
      const r = await client.query(
        `SELECT count(*)::int c FROM mart.${q(spec.table)} WHERE "${nnCol.name}" IS NULL`,
      );
      checks.push(["not_null", `count(*) WHERE ${nnCol.name} IS NULL = 0`, r.rows[0].c === 0, r.rows[0].c, 0, "error"]);
    }
    const pkCol = spec.cols.find((c) => c.pk);
    if (pkCol && spec.layer !== "view") {
      const r = await client.query(
        `SELECT (count(*) - count(DISTINCT "${pkCol.name}"))::int c FROM mart.${q(spec.table)}`,
      );
      checks.push(["uniqueness", `count(*) - count(DISTINCT ${pkCol.name}) = 0`, r.rows[0].c === 0, r.rows[0].c, 0, "error"]);
    }
    const rangeCol = spec.cols.find((c) => c.range);
    if (rangeCol && spec.layer !== "view") {
      const r = await client.query(
        `SELECT count(*)::int c FROM mart.${q(spec.table)} WHERE "${rangeCol.name}" IS NOT NULL AND ("${rangeCol.name}" < ${rangeCol.range[0]} OR "${rangeCol.name}" > ${rangeCol.range[1]})`,
      );
      checks.push(["range", `${rangeCol.name} BETWEEN ${rangeCol.range[0]} AND ${rangeCol.range[1]}`, r.rows[0].c === 0, r.rows[0].c, 0, "warn"]);
    }
    for (const [kind, expr, passed, observed, threshold, severity] of checks) {
      await client.query(
        `INSERT INTO catalog.quality_checks
          (dataset_id, name, kind, expression, passed, observed_value, threshold, severity, ran_at)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)`,
        [datasetId, `${spec.name}_${kind}`, kind, expr, passed, observed, threshold, severity, lastRun],
      );
    }
  }

  /* ---- relaciones DERIVADAS de la metadata de columnas (nunca a mano) ---- */
  const resolve = (name) => {
    for (const spec of DATASET_SPECS) if (spec.name === name) return dsIdByName.get(`${spec.domain}.${spec.name}`);
    return null;
  };
  for (const spec of DATASET_SPECS) {
    const from = dsIdByName.get(`${spec.domain}.${spec.name}`);
    for (const c of spec.cols) {
      if (!c.fk) continue;
      const to = resolve(c.fk[0]);
      if (!to) continue;
      await client.query(
        `INSERT INTO catalog.dataset_relations
          (from_dataset_id, from_column, to_dataset_id, to_column, relation_type, cardinality, evidence, confidence)
         VALUES ($1,$2,$3,$4,'fk','many-to-one','column_metadata',1.0)`,
        [from, c.name, to, c.fk[1]],
      );
    }
    for (const e of spec.edges ?? []) {
      const to = resolve(e[0]);
      if (!to) continue;
      await client.query(
        `INSERT INTO catalog.dataset_relations
          (from_dataset_id, from_column, to_dataset_id, to_column, relation_type, cardinality, evidence, confidence)
         VALUES ($1,$2,$3,$4,$5,'one-to-many','view_definition',0.85)`,
        [from, e[2], to, e[1], e[3]],
      );
    }
  }

  /* ------------------------- consultas guardadas (queries as code) -------- */
  const saved = [
    ["top5-bonos-vida", "Top 5 emisores de bonos en Vida", "TIR promedio ponderada por tenencias; la consulta que más se repite en los informes mensuales.", ["bonos", "core"], true, `SELECT i.sector_economico AS emisor_sector, b.tipo_bono,
       round(avg(b.tir_mercado_pct), 3) AS tir_promedio_pct,
       count(*)                         AS tenencias,
       round(sum(b.monto_m_clp))         AS monto_m_clp
FROM mart.vida_bonos b
JOIN mart.ref_instrumento i USING (nemotecnico)
WHERE b.periodo = '2026-01'
GROUP BY 1, 2
ORDER BY monto_m_clp DESC
LIMIT 5;`],
    ["concentracion-repos", "Concentración de contrapartes en repos", "HHI simplificado por contraparte para el comité de riesgos.", ["riesgo", "ffii"], true, `SELECT nombre_contraparte,
       count(*)                              AS operaciones,
       round(avg(tasa_pct), 2)               AS tasa_media_pct,
       round(sum(valorizacion_cierre_m_clp)) AS valor_m_clp,
       round(100.0 * sum(valorizacion_cierre_m_clp) /
             sum(sum(valorizacion_cierre_m_clp)) OVER (), 2) AS share_pct
FROM mart.ffii_repos
GROUP BY 1
ORDER BY valor_m_clp DESC;`],
    ["cobertura-solvencia", "Cobertura de solvencia por entidad", "Inversión / requerimiento; dispara alerta bajo 120 %.", ["solvencia", "alerta"], true, `SELECT a.nombre AS aseguradora, s.periodo,
       round(sum(s.total_inversion_m_clp)) AS inversion_m_clp,
       round(sum(s.requerido_m_clp))       AS requerido_m_clp,
       round(100.0 * sum(s.total_inversion_m_clp) / nullif(sum(s.requerido_m_clp), 0), 1) AS cobertura_pct
FROM mart.vida_solvencia s
JOIN mart.dim_aseguradora a ON a.rut = s.rut_aseguradora
GROUP BY 1, 2
HAVING 100.0 * sum(s.total_inversion_m_clp) / nullif(sum(s.requerido_m_clp), 0) < 130
ORDER BY cobertura_pct;`],
    ["loss-ratio-ramos", "Loss ratio por ramo (Generales)", "Comparación prima emitida vs siniestro ocurrido, con IBNR.", ["generales", "siniestralidad"], false, `SELECT ramo,
       round(sum(prima_emitida_m_clp))       AS prima_m_clp,
       round(sum(siniestro_ocurrido_m_clp))  AS siniestro_m_clp,
       round(100.0 * sum(siniestro_ocurrido_m_clp) / nullif(sum(prima_emitida_m_clp),0), 1) AS loss_ratio_pct,
       round(sum(reserva_ibnr_m_clp))        AS ibnr_m_clp
FROM mart.generales_siniestros
GROUP BY 1
ORDER BY loss_ratio_pct DESC;`],
    ["consolidado-semantic", "Inversión consolidada (capa semántica)", "Consulta contra la vista gobernada: el único acceso aprobado entre dominios.", ["semantic-layer"], true, `SELECT periodo, dominio, clase_activo,
       round(sum(monto_m_clp)) AS monto_m_clp, sum(posiciones) AS posiciones
FROM mart.v_inversion_consolidada
GROUP BY 1, 2, 3
ORDER BY periodo DESC, monto_m_clp DESC;`],
    ["inmobiliario-comuna", "Inmobiliario por comuna", "Tasación y ocupación; útil para el anexo de bienes raíces.", ["inmobiliario"], false, `SELECT comuna, sum(propiedades) AS propiedades,
       round(sum(tasacion_comercial_m_clp)) AS tasacion_m_clp,
       round(avg(ocupacion_pct), 1)         AS ocupacion_pct
FROM mart.vida_bienes_raices
WHERE periodo = '2026-01'
GROUP BY 1
ORDER BY tasacion_m_clp DESC
LIMIT 6;`],
  ];
  for (const s of saved) {
    await client.query(
      `INSERT INTO catalog.saved_queries (slug,title,sql,author,description,tags,dataset_refs,is_favorite,run_count,last_run_at)
       VALUES ($1,$2,$3,'analista-inversiones',$4,$5,$6,$7,$8,$9)`,
      [s[0], s[1], s[5], s[2], s[3].join(","), "", s[4], Math.floor(between(3, 140)), new Date(Date.now() - between(0, 72) * 3600 * 1000)],
    );
  }

  /* auditoría con ejemplos para que la pestaña no nazca vacía */
  const samples = [
    ["select * from mart.vida_bonos limit 10;", "success", 10, 41, false],
    ["DELETE FROM mart.vida_bonos;", "blocked", 0, 0, false],
    ["SELECT count(*) FROM mart.v_inversion_consolidada;", "success", 1, 22, false],
    ["select * from pg_shadow;", "blocked", 0, 0, false],
    ["SELECT ramo FROM mart.generales_siniestros GROUP BY 1;", "success", 6, 18, true],
    ["COPY mart.vida_bonos TO '/tmp/x.csv';", "blocked", 0, 0, false],
  ];
  for (const [sqlText, status, rowCount, dur, cached] of samples) {
    await client.query(
      `INSERT INTO catalog.query_log (actor, sql_text, status, engine, row_count, duration_ms, cached, blocked_by, error_message, created_at)
       VALUES ('analista-inversiones',$1,$2,'postgres',$3,$4,$5,$6,$7,$8)`,
      [
        sqlText, status, rowCount, dur, cached,
        status === "blocked" ? "read_only_guard" : null,
        status === "blocked" ? "Sentencia no permitida en modo lectura" : null,
        new Date(Date.now() - between(1, 240) * 60 * 1000),
      ],
    );
  }
}

/* ---------------------------------------------------------------- runner */

async function main() {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query(`CREATE SCHEMA IF NOT EXISTS catalog`);
    await createDataPlane(client);
    const counts = await seedFacts(client);
    await seedCatalog(client, counts);
    await client.query("COMMIT");

    const t = {};
    for (const [k] of Object.entries(counts)) {
      const r = await client.query(`SELECT count(*)::int c FROM mart.${q(k)}`);
      t[k] = r.rows[0].c;
    }
    const c = await client.query(`SELECT
      (SELECT count(*) FROM catalog.datasets) ds,
      (SELECT count(*) FROM catalog.dataset_columns) cols,
      (SELECT count(*) FROM catalog.dataset_relations) rel,
      (SELECT count(*) FROM catalog.ingest_runs) runs,
      (SELECT count(*) FROM catalog.quality_checks) qc,
      (SELECT count(*) FROM catalog.saved_queries) sq`);
    console.log("seed ok", JSON.stringify({ mart: t, catalog: c.rows[0] }, null, 2));
  } catch (e) {
    await client.query("ROLLBACK");
    throw e;
  } finally {
    client.release();
    await pool.end();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

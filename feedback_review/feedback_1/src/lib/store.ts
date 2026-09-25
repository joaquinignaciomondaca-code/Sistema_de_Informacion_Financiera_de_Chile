import { SEED_DATASETS, type Dataset } from "./data";
import { detectIndustry } from "./sql";

type SchemaModule = typeof import("@/db/schema");

let dbRef: { db: import("drizzle-orm/node-postgres").NodePgDatabase<Record<string, never>>; schema: SchemaModule } | null = null;
let dbFailed = false;

async function getDb() {
  if (dbFailed) return null;
  if (dbRef) return dbRef;
  try {
    const [{ db }, schema] = await Promise.all([import("@/db"), import("@/db/schema")]);
    dbRef = { db, schema };
    return dbRef;
  } catch {
    dbFailed = true;
    return null;
  }
}

export type PersistState = { ok: boolean; mode: "postgres" | "memoria" };

let memoryDatasets: Dataset[] | null = null;
let memoryConsultas: { id: number; titulo: string; sql: string; industria: string | null; createdAt: Date }[] = [
  {
    id: 1,
    titulo: "Ranking de aseguradoras por inversión",
    sql: "SELECT nombre_aseguradora, participacion_pct, inversion_ultimo_reporte_m_clp FROM 'vida.aseguradoras' WHERE estado = 'Activa' ORDER BY inversion_ultimo_reporte_m_clp DESC LIMIT 5;",
    industria: "vida",
    createdAt: new Date("2026-09-12T14:02:00Z"),
  },
  {
    id: 2,
    titulo: "Contrapartes con más repos",
    sql: "SELECT nombre_contraparte, COUNT(*) AS operaciones, ROUND(AVG(tasa_pct), 2) AS tasa_media FROM 'fi.repos' GROUP BY nombre_contraparte ORDER BY operaciones DESC;",
    industria: "fi",
    createdAt: new Date("2026-09-14T09:41:00Z"),
  },
];

let seeded = false;

/** Inserta el catálogo semilla en Postgres la primera vez que se consulta. */
export async function ensureSeed(): Promise<PersistState> {
  const handle = await getDb();
  if (!handle) return { ok: false, mode: "memoria" };
  const { db, schema } = handle;
  try {
    if (!seeded) {
      const existing = await db.select({ slug: schema.datasets.slug }).from(schema.datasets);
      const have = new Set(existing.map((r) => r.slug));
      const missing = SEED_DATASETS.filter((d) => !have.has(d.slug));
      if (missing.length) {
        for (const d of missing) {
          await db.insert(schema.datasets).values({
            slug: d.slug,
            nombre: d.nombre,
            industria: d.industria,
            circular: d.circular,
            archivo: d.archivo,
            descripcion: d.descripcion,
            columnas: d.columnas,
            filas: d.filas,
          }).onConflictDoNothing({ target: schema.datasets.slug });
        }
      }
      const saved = await db.select().from(schema.consultas);
      if (saved.length === 0) {
        for (const c of memoryConsultas) {
          await db.insert(schema.consultas).values({
            titulo: c.titulo,
            sql: c.sql,
            industria: c.industria,
            origen: "semilla",
          }).onConflictDoNothing();
        }
      }
      seeded = true;
    }
    return { ok: true, mode: "postgres" };
  } catch {
    dbFailed = true;
    return { ok: false, mode: "memoria" };
  }
}

export async function getDatasets(): Promise<{ datasets: Dataset[]; persist: PersistState }> {
  const seed = await ensureSeed();
  if (!seed.ok) {
    memoryDatasets = memoryDatasets ?? SEED_DATASETS;
    return { datasets: memoryDatasets, persist: seed };
  }
  const handle = await getDb();
  if (!handle) return { datasets: SEED_DATASETS, persist: { ok: false, mode: "memoria" } };
  try {
    const rows = await handle.db.select().from(handle.schema.datasets);
    if (!rows.length) return { datasets: SEED_DATASETS, persist: seed };
    const mapped: Dataset[] = rows.map((r) => ({
      slug: r.slug,
      nombre: r.nombre,
      industria: r.industria as Dataset["industria"],
      circular: r.circular,
      archivo: r.archivo,
      descripcion: r.descripcion,
      columnas: r.columnas as Dataset["columnas"],
      filas: r.filas as Dataset["filas"],
    }));
    return { datasets: mapped, persist: seed };
  } catch {
    return { datasets: SEED_DATASETS, persist: { ok: false, mode: "memoria" } };
  }
}

export type SavedQuery = {
  id: number;
  titulo: string;
  sql: string;
  industria: string | null;
  origen: string;
  createdAt: string;
};

export async function listConsultas(): Promise<SavedQuery[]> {
  const handle = await getDb();
  if (!handle) return memoryConsultas.map((c) => ({ ...c, origen: "semilla", createdAt: c.createdAt.toISOString() }));
  try {
    const rows = await handle.db.select().from(handle.schema.consultas).orderBy(handle.schema.consultas.id);
    if (!rows.length) {
      await ensureSeed();
      const again = await handle.db.select().from(handle.schema.consultas).orderBy(handle.schema.consultas.id);
      return again.map(mapConsulta);
    }
    return rows.map(mapConsulta);
  } catch {
    return memoryConsultas.map((c) => ({ ...c, origen: "semilla", createdAt: c.createdAt.toISOString() }));
  }
}

function mapConsulta(r: { id: number; titulo: string; sql: string; industria: string | null; origen: string; createdAt: Date }): SavedQuery {
  return { id: r.id, titulo: r.titulo, sql: r.sql, industria: r.industria, origen: r.origen, createdAt: r.createdAt.toISOString() };
}

export async function createConsulta(input: { titulo: string; sql: string }): Promise<SavedQuery> {
  const industria = detectIndustry(input.sql);
  const handle = await getDb();
  if (!handle) {
    const row = { id: memoryConsultas.length + 1, titulo: input.titulo, sql: input.sql, industria, createdAt: new Date() };
    memoryConsultas = [...memoryConsultas, row];
    return { ...row, origen: "usuario", createdAt: row.createdAt.toISOString() };
  }
  try {
    const [row] = await handle.db
      .insert(handle.schema.consultas)
      .values({ titulo: input.titulo, sql: input.sql, industria, origen: "usuario" })
      .returning();
    return mapConsulta(row);
  } catch {
    const row = { id: memoryConsultas.length + 1, titulo: input.titulo, sql: input.sql, industria, createdAt: new Date() };
    memoryConsultas = [...memoryConsultas, row];
    return { ...row, origen: "usuario", createdAt: row.createdAt.toISOString() };
  }
}

export async function logEjecucion(entry: {
  sql: string;
  datasetSlug: string | null;
  filas: number;
  ms: number;
  ok: boolean;
  error?: string;
}): Promise<void> {
  const handle = await getDb();
  if (!handle) return;
  try {
    await handle.db.insert(handle.schema.ejecuciones).values({
      sql: entry.sql,
      datasetSlug: entry.datasetSlug,
      filas: entry.filas,
      ms: entry.ms,
      ok: entry.ok,
      error: entry.error ?? null,
    });
  } catch {
    /* el historial nunca debe romper la consulta */
  }
}

import { db, pool } from "@/db";
import { asc, eq, inArray, sql } from "drizzle-orm";
import {
  catalog,
  datasetColumns,
  datasetRelations,
  datasets,
  domains,
  ingestRuns,
  qualityChecks,
  savedQueries,
  queryLog,
  sources,
} from "@/db/schema";
import { hoursSince } from "@/lib/format";
import type {
  CatalogTree,
  DatasetNode,
  DomainNode,
  FreshnessState,
  Graph,
  GraphEdge,
  GraphNode,
  HistoryItem,
  SavedQuery,
  SourceNode,
} from "@/lib/types";

export type {
  CatalogTree,
  DatasetNode,
  DomainNode,
  Graph,
  GraphEdge,
  GraphNode,
  HistoryItem,
  SavedQuery,
  SourceNode,
};

function state(hours: number | null, slo: number): FreshnessState {
  if (hours === null) return "unknown";
  if (hours <= slo) return "ok";
  if (hours <= slo * 1.5) return "warn";
  return "breach";
}

async function raw<T>(text: string, params: unknown[] = []): Promise<T[]> {
  const res = await pool.query(text, params);
  return res.rows as T[];
}

async function qualityByDataset(): Promise<Map<number, { passed: number; total: number }>> {
  const res = await raw<{ id: number; total: number; passed: number }>(`
    select dataset_id as id,
           count(*)::int as total,
           count(*) filter (where passed)::int as passed
    from catalog.quality_checks
    group by 1
  `);
  const map = new Map<number, { passed: number; total: number }>();
  for (const r of res) map.set(r.id, { passed: r.passed, total: r.total });
  return map;
}

async function latestRunByDataset(): Promise<Map<number, Date | null>> {
  const res = await raw<{ id: number; last_run: Date | null }>(`
    select dataset_id as id, max(started_at) as last_run
    from catalog.ingest_runs
    group by 1
  `);
  const map = new Map<number, Date | null>();
  for (const r of res) map.set(r.id, r.last_run);
  return map;
}

function toNode(
  d: typeof datasets.$inferSelect,
  quality: Map<number, { passed: number; total: number }>,
  runs: Map<number, Date | null>,
): DatasetNode {
  const lastRun = runs.get(d.id) ?? d.lastMaterializedAt ?? null;
  const hours = hoursSince(lastRun);
  const q = quality.get(d.id) ?? { passed: 0, total: 0 };
  return {
    id: d.id,
    name: d.name,
    layer: d.layer,
    physical: `${d.physicalSchema}.${d.physicalTable}`,
    rows: d.rowCount,
    sizeMb: Number(d.sizeMb),
    status: d.status,
    freshnessHours: hours,
    sloHours: d.freshnessSloHours,
    freshness: state(hours, d.freshnessSloHours),
    quality: q,
    tags: d.tags ? d.tags.split(",").filter(Boolean) : [],
    cadence: d.refreshCadence,
  };
}

export async function getCatalogTree(kindFilter?: string): Promise<CatalogTree> {
  const [dom, src, ds, quality, runs] = await Promise.all([
    db.select().from(domains).orderBy(asc(domains.id)),
    db.select().from(sources).orderBy(asc(sources.id)),
    db.select().from(datasets).orderBy(asc(datasets.domainId), asc(datasets.name)),
    qualityByDataset(),
    latestRunByDataset(),
  ]);

  const nodes = ds.map((d) => toNode(d, quality, runs));
  const nodesById = new Map(nodes.map((n) => [n.id, n]));

  const out: DomainNode[] = dom
    .filter((d) => !kindFilter || kindFilter === "todos" || d.kind === kindFilter || d.slug === "comun")
    .map((d) => {
      const own = nodes.filter((n) => ds.find((x) => x.id === n.id)?.domainId === d.id);
      const bySource = new Map<number, DatasetNode[]>();
      const shared: DatasetNode[] = [];
      for (const n of own) {
        const meta = ds.find((x) => x.id === n.id)!;
        if (meta.sourceId) {
          const arr = bySource.get(meta.sourceId) ?? [];
          arr.push(n);
          bySource.set(meta.sourceId, arr);
        } else {
          shared.push(n);
        }
      }
      const srcNodes = src
        .filter((s) => s.domainId === d.id)
        .map<SourceNode>((s) => ({
          id: s.id,
          code: s.code,
          title: s.title,
          issuer: s.issuer,
          url: s.url,
          mandatory: s.mandatory,
          datasets: bySource.get(s.id) ?? [],
        }))
        .filter((s) => s.datasets.length > 0 || s.mandatory);

      return {
        id: d.id,
        slug: d.slug,
        name: d.name,
        kind: d.kind,
        regulator: d.regulator,
        ownerTeam: d.ownerTeam,
        ownerContact: d.ownerContact,
        description: d.description,
        sources: srcNodes,
        shared,
        stats: {
          datasets: own.length,
          rows: own.reduce((a, b) => a + b.rows, 0),
          breaches: own.filter((n) => n.freshness === "breach").length,
          failedChecks: own.reduce((a, b) => a + (b.quality.total - b.quality.passed), 0),
        },
      };
    });

  const datasetMeta = ds;
  return {
    domains: out,
    generatedAt: new Date().toISOString(),
    datasetCount: nodes.length,
    rowCount: nodes.reduce((a, b) => a + b.rows, 0),
    breachCount: nodes.filter((n) => n.freshness === "breach").length,
    failedChecks: nodes.reduce((a, b) => a + (b.quality.total - b.quality.passed), 0),
    engines: [
      { name: "postgres (mart)", datasets: datasetMeta.filter((x) => x.physicalSchema === "mart").length },
      { name: "postgres (catalog)", datasets: datasetMeta.filter((x) => x.layer === "view").length },
    ],
  };
}

export async function getGraph(kindFilter?: string): Promise<Graph> {
  const [ds, dom, rel, cols, quality, runs] = await Promise.all([
    db.select().from(datasets),
    db.select().from(domains),
    db.select().from(datasetRelations),
    raw<{ id: number; n: number }>(`select dataset_id as id, count(*)::int as n from catalog.dataset_columns group by 1`),
    qualityByDataset(),
    latestRunByDataset(),
  ]);
  const colCount = new Map(cols.map((c) => [c.id, c.n]));
  const domById = new Map(dom.map((d) => [d.id, d]));
  const keep = new Set(
    ds
      .filter((d) => {
        const dm = domById.get(d.domainId);
        return !kindFilter || kindFilter === "todos" || dm?.kind === kindFilter || dm?.slug === "comun";
      })
      .map((d) => d.id),
  );

  const nodes: GraphNode[] = ds
    .filter((d) => keep.has(d.id))
    .map((d) => {
      const n = toNode(d, quality, runs);
      const dm = domById.get(d.domainId);
      return {
        id: d.id,
        name: d.name,
        domain: dm?.name ?? String(d.domainId),
        domainKind: dm?.kind ?? "comun",
        layer: d.layer,
        rows: d.rowCount,
        columns: colCount.get(d.id) ?? 0,
        freshness: n.freshness,
        quality: n.quality.total ? Math.round((n.quality.passed / n.quality.total) * 100) : 100,
        status: d.status,
        physical: `${d.physicalSchema}.${d.physicalTable}`,
        access: d.accessPolicy,
        grain: d.grain,
      };
    });

  const ids = new Set(nodes.map((n) => n.id));
  const edges: GraphEdge[] = rel
    .filter((r) => ids.has(r.fromDatasetId) && ids.has(r.toDatasetId))
    .map((r) => ({
      id: r.id,
      from: r.fromDatasetId,
      to: r.toDatasetId,
      fromColumn: r.fromColumn,
      toColumn: r.toColumn,
      type: r.relationType,
      confidence: Number(r.confidence),
    }));

  return { nodes, edges };
}

export async function getDatasetDetail(id: number) {
  const [ds] = await db.select().from(datasets).where(eq(datasets.id, id));
  if (!ds) return null;
  const [cols, relOut, relIn, runs, checks, dom, src] = await Promise.all([
    db.select().from(datasetColumns).where(eq(datasetColumns.datasetId, id)).orderBy(asc(datasetColumns.ordinal)),
    db.select().from(datasetRelations).where(eq(datasetRelations.fromDatasetId, id)),
    db.select().from(datasetRelations).where(eq(datasetRelations.toDatasetId, id)),
    db
      .select()
      .from(ingestRuns)
      .where(eq(ingestRuns.datasetId, id))
      .orderBy(sql`${ingestRuns.startedAt} desc`)
      .limit(8),
    db.select().from(qualityChecks).where(eq(qualityChecks.datasetId, id)),
    db.select().from(domains).where(eq(domains.id, ds.domainId)),
    ds.sourceId ? db.select().from(sources).where(eq(sources.id, ds.sourceId)) : Promise.resolve([]),
  ]);

  const nameOf = async (ids: number[]) => {
    if (!ids.length) return new Map<number, string>();
    const r = await db
      .select({ id: datasets.id, name: datasets.name, physical: datasets.physicalTable })
      .from(datasets)
      .where(inArray(datasets.id, ids));
    return new Map(r.map((x) => [x.id, `${x.name}`]));
  };
  const names = await nameOf([
    ...relOut.map((r) => r.toDatasetId),
    ...relIn.map((r) => r.fromDatasetId),
  ]);

  let preview: { columns: string[]; rows: Record<string, unknown>[]; error?: string } = {
    columns: [],
    rows: [],
  };
  try {
    const p = await raw<Record<string, unknown>>(
      `select * from "${ds.physicalSchema}"."${ds.physicalTable}" limit 8`,
    );
    preview = { columns: p.length ? Object.keys(p[0]) : [], rows: serializable(p) };
  } catch (e) {
    preview = { columns: [], rows: [], error: (e as Error).message };
  }

  return {
    dataset: {
      ...ds,
      physical: `${ds.physicalSchema}.${ds.physicalTable}`,
      freshnessHours: hoursSince(runs[0]?.startedAt ?? ds.lastMaterializedAt),
    },
    domain: dom[0] ?? null,
    source: src[0] ?? null,
    columns: cols,
    outbound: relOut.map((r) => ({ ...r, target: names.get(r.toDatasetId) ?? `#${r.toDatasetId}` })),
    inbound: relIn.map((r) => ({ ...r, origin: names.get(r.fromDatasetId) ?? `#${r.fromDatasetId}` })),
    runs,
    checks,
    preview,
  };
}

export async function listSaved(): Promise<SavedQuery[]> {
  const rows = await db.select().from(savedQueries).orderBy(sql`${savedQueries.isFavorite} desc, ${savedQueries.runCount} desc`);
  return rows.map((r) => ({
    title: r.title,
    slug: r.slug,
    sql: r.sql,
    description: r.description,
    tags: r.tags.split(",").filter(Boolean),
    favorite: r.isFavorite,
    runCount: r.runCount,
  }));
}

/** pg devuelve numeric como string y date como Date: lo normalizamos para el cliente. */
export function serializable(rows: Record<string, unknown>[]): Record<string, unknown>[] {
  return rows.map((r) => {
    const o: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(r)) {
      if (v instanceof Date) o[k] = v.toISOString();
      else if (typeof v === "bigint") o[k] = Number(v);
      else if (typeof v === "string" && /^-?\d+(\.\d+)?$/.test(v) && k !== "id") o[k] = Number(v);
      else o[k] = v;
    }
    return o;
  });
}

export async function recordQuery(input: {
  actor: string;
  sqlText: string;
  status: string;
  rowCount: number;
  durationMs: number;
  cached: boolean;
  blockedBy?: string | null;
  errorMessage?: string | null;
}) {
  await db.insert(queryLog).values({
    actor: input.actor,
    sqlText: input.sqlText.slice(0, 4000),
    status: input.status,
    engine: "postgres",
    rowCount: input.rowCount,
    durationMs: input.durationMs,
    cached: input.cached,
    blockedBy: input.blockedBy ?? null,
    errorMessage: input.errorMessage ?? null,
  });
}

export async function recentQueries(limit = 12): Promise<HistoryItem[]> {
  const rows = await db
    .select()
    .from(queryLog)
    .orderBy(sql`${queryLog.createdAt} desc`)
    .limit(limit);
  return rows.map((r) => ({
    id: r.id,
    sql: r.sqlText,
    status: r.status,
    rows: r.rowCount,
    durationMs: r.durationMs,
    cached: r.cached,
    blockedBy: r.blockedBy,
    at: r.createdAt?.toISOString?.() ?? null,
  }));
}

export async function bumpSaved(slug: string) {
  await db.execute(
    sql`update catalog.saved_queries
          set run_count = run_count + 1, last_run_at = now()
        where slug = ${slug}`,
  );
}

export async function toggleFavorite(slug: string, value: boolean) {
  await db.execute(
    sql`update catalog.saved_queries set is_favorite = ${value} where slug = ${slug}`,
  );
}

export async function insertSaved(input: { title: string; sql: string; description: string }) {
  const slug = `${input.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40)}-${Date.now().toString(36)}`;
  await db.execute(
    sql`insert into catalog.saved_queries (slug, title, sql, author, description, tags, dataset_refs, is_favorite, run_count)
        values (${slug}, ${input.title}, ${input.sql}, 'anon', ${input.description}, 'personal', '', true, 0)`,
  );
  return slug;
}

export async function deleteSaved(slug: string) {
  await db.execute(sql`delete from catalog.saved_queries where slug = ${slug} and author = 'anon'`);
}

/**
 * MFC — Capa de METADATOS (catalog plane).
 *
 * Principio de diseño: los datos NO viven en el navegador.
 * El navegador sólo ve (a) este catálogo y (b) resultados paginados que
 * devuelve el servidor. Los Parquet/DuckDB-Wasm pasan a ser una *cache
 * opcional* de lectura, no la fuente de verdad.
 */
import {
  boolean,
  date,
  integer,
  numeric,
  pgSchema,
  pgTable,
  serial,
  text,
  timestamp,
  unique,
} from "drizzle-orm/pg-core";

export const catalog = pgSchema("catalog");

/* ---------------------------------------------------------------- dominio */

export const domains = catalog.table("domains", {
  id: serial("id").primaryKey(),
  slug: text("slug").notNull().unique(),
  name: text("name").notNull(),
  /** vida | generales | ffmm | fi — coincide con los filtros del mapa */
  kind: text("kind").notNull(),
  regulator: text("regulator").notNull(),
  /** equipo humano responsable (data product owner) */
  ownerTeam: text("owner_team").notNull(),
  ownerContact: text("owner_contact").notNull(),
  description: text("description").notNull(),
});

/* ------------------------------------------------------- fuente normativa */

export const sources = catalog.table("sources", {
  id: serial("id").primaryKey(),
  domainId: integer("domain_id")
    .notNull()
    .references(() => domains.id, { onDelete: "cascade" }),
  code: text("code").notNull(),
  title: text("title").notNull(),
  issuer: text("issuer").notNull(),
  effectiveDate: date("effective_date"),
  url: text("url"),
  /** true => obligatorio en el reporte; false => roadmap / voluntario */
  mandatory: boolean("mandatory").notNull().default(true),
});

/* --------------------------------------------------------------- datasets */

export const datasets = catalog.table(
  "datasets",
  {
    id: serial("id").primaryKey(),
    domainId: integer("domain_id")
      .notNull()
      .references(() => domains.id, { onDelete: "cascade" }),
    sourceId: integer("source_id").references(() => sources.id, {
      onDelete: "set null",
    }),
    name: text("name").notNull(),
    physicalSchema: text("physical_schema").notNull().default("mart"),
    physicalTable: text("physical_table").notNull(),
    /** raw | staging | mart | view */
    layer: text("layer").notNull(),
    grain: text("grain").notNull(),
    description: text("description").notNull(),
    owner: text("owner").notNull(),
    refreshCadence: text("refresh_cadence").notNull().default("monthly"),
    freshnessSloHours: integer("freshness_slo_hours").notNull().default(720),
    /** contadores medidos en el último run (no inventados) */
    rowCount: integer("row_count").notNull().default(0),
    sizeMb: numeric("size_mb").notNull().default("0"),
    schemaVersion: integer("schema_version").notNull().default(1),
    /** live | degraded | roadmap */
    status: text("status").notNull().default("live"),
    /** política de acceso: public | internal | restricted */
    accessPolicy: text("access_policy").notNull().default("internal"),
    /** dónde vive el modelo que lo materializa (dbt / SQL as code) */
    modelPath: text("model_path"),
    /** CSV simple: "inversiones,monthly" — fácil de exponer en una API */
    tags: text("tags").notNull().default(""),
    lastMaterializedAt: timestamp("last_materialized_at", {
      withTimezone: true,
    }),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (t) => [unique("datasets_domain_name_uq").on(t.domainId, t.name)],
);

/* ------------------------------------------------------------- columnas */

export const datasetColumns = catalog.table("dataset_columns", {
  id: serial("id").primaryKey(),
  datasetId: integer("dataset_id")
    .notNull()
    .references(() => datasets.id, { onDelete: "cascade" }),
  ordinal: integer("ordinal").notNull(),
  name: text("name").notNull(),
  dataType: text("data_type").notNull(),
  description: text("description").notNull().default(""),
  isPk: boolean("is_pk").notNull().default(false),
  nullable: boolean("nullable").notNull().default(true),
  /** none | hash | redact — enmascaramiento aplicado en el servidor */
  masking: text("masking").notNull().default("none"),
  businessTag: text("business_tag"),
  unit: text("unit"),
});

/**
 * Relaciones DERIVADAS de la metadata de columnas (no dibujadas a mano):
 * así el mapa relacional nunca miente y se actualiza solo con el catálogo.
 */
export const datasetRelations = catalog.table("dataset_relations", {
  id: serial("id").primaryKey(),
  fromDatasetId: integer("from_dataset_id")
    .notNull()
    .references(() => datasets.id, { onDelete: "cascade" }),
  fromColumn: text("from_column").notNull(),
  toDatasetId: integer("to_dataset_id")
    .notNull()
    .references(() => datasets.id, { onDelete: "cascade" }),
  toColumn: text("to_column").notNull(),
  /** fk | conformed_key | view_union */
  relationType: text("relation_type").notNull().default("fk"),
  cardinality: text("cardinality").notNull().default("many-to-one"),
  /** de dónde salió la evidencia del join */
  evidence: text("evidence").notNull().default("column_metadata"),
  confidence: numeric("confidence").notNull().default("1.0"),
});

/* ------------------------------------------------------- run ledger / SLO */

export const ingestRuns = catalog.table("ingest_runs", {
  id: serial("id").primaryKey(),
  datasetId: integer("dataset_id")
    .notNull()
    .references(() => datasets.id, { onDelete: "cascade" }),
  startedAt: timestamp("started_at", { withTimezone: true }).notNull(),
  finishedAt: timestamp("finished_at", { withTimezone: true }),
  /** success | failed | partial | running */
  status: text("status").notNull(),
  rowsIn: integer("rows_in").notNull().default(0),
  rowsOut: integer("rows_out").notNull().default(0),
  rowsDropped: integer("rows_dropped").notNull().default(0),
  watermark: text("watermark"),
  commitSha: text("commit_sha"),
  durationMs: integer("duration_ms").notNull().default(0),
  errorMessage: text("error_message"),
});

export const qualityChecks = catalog.table("quality_checks", {
  id: serial("id").primaryKey(),
  datasetId: integer("dataset_id")
    .notNull()
    .references(() => datasets.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  /** freshness | volume | uniqueness | not_null | range | custom */
  kind: text("kind").notNull(),
  expression: text("expression").notNull().default(""),
  passed: boolean("passed").notNull(),
  observedValue: numeric("observed_value"),
  threshold: numeric("threshold"),
  severity: text("severity").notNull().default("warn"),
  ranAt: timestamp("ran_at", { withTimezone: true }).notNull().defaultNow(),
});

/* ------------------------------------------- consultas guardadas + auditoría */

export const savedQueries = catalog.table("saved_queries", {
  id: serial("id").primaryKey(),
  slug: text("slug").notNull().unique(),
  title: text("title").notNull(),
  sql: text("sql").notNull(),
  author: text("author").notNull().default("analista"),
  description: text("description").notNull().default(""),
  tags: text("tags").notNull().default(""),
  /** CSV de ids de dataset tocados — alimenta impacto y recomendaciones */
  datasetRefs: text("dataset_refs").notNull().default(""),
  isFavorite: boolean("is_favorite").notNull().default(false),
  runCount: integer("run_count").notNull().default(0),
  lastRunAt: timestamp("last_run_at", { withTimezone: true }),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

/** cada ejecución queda auditada: quién, qué, cuántas filas, cuánto tardó */
export const queryLog = catalog.table("query_log", {
  id: serial("id").primaryKey(),
  actor: text("actor").notNull().default("anon"),
  sqlText: text("sql_text").notNull(),
  status: text("status").notNull(),
  engine: text("engine").notNull().default("postgres"),
  rowCount: integer("row_count").notNull().default(0),
  durationMs: integer("duration_ms").notNull().default(0),
  cached: boolean("cached").notNull().default(false),
  blockedBy: text("blocked_by"),
  errorMessage: text("error_message"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export type DomainRow = typeof domains.$inferSelect;
export type DatasetRow = typeof datasets.$inferSelect;
export type ColumnRow = typeof datasetColumns.$inferSelect;

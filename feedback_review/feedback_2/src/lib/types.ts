/** Tipos compartidos entre servidor y cliente (única fuente de verdad). */

export type FreshnessState = "ok" | "warn" | "breach" | "unknown";

export type DatasetNode = {
  id: number;
  name: string;
  layer: string;
  physical: string;
  rows: number;
  sizeMb: number;
  status: string;
  freshnessHours: number | null;
  sloHours: number;
  freshness: FreshnessState;
  quality: { passed: number; total: number };
  tags: string[];
  cadence: string;
};

export type SourceNode = {
  id: number;
  code: string;
  title: string;
  issuer: string;
  url: string | null;
  mandatory: boolean;
  datasets: DatasetNode[];
};

export type DomainNode = {
  id: number;
  slug: string;
  name: string;
  kind: string;
  regulator: string;
  ownerTeam: string;
  ownerContact: string;
  description: string;
  sources: SourceNode[];
  shared: DatasetNode[];
  stats: { datasets: number; rows: number; breaches: number; failedChecks: number };
};

export type CatalogTree = {
  domains: DomainNode[];
  generatedAt: string;
  datasetCount: number;
  rowCount: number;
  breachCount: number;
  failedChecks: number;
  engines: { name: string; datasets: number }[];
};

export type GraphNode = {
  id: number;
  name: string;
  domain: string;
  domainKind: string;
  layer: string;
  rows: number;
  columns: number;
  freshness: FreshnessState;
  quality: number;
  status: string;
  physical: string;
  access: string;
  grain: string;
};

export type GraphEdge = {
  id: number;
  from: number;
  to: number;
  fromColumn: string;
  toColumn: string;
  type: string;
  confidence: number;
};

export type Graph = { nodes: GraphNode[]; edges: GraphEdge[] };

export type SavedQuery = {
  title: string;
  slug: string;
  sql: string;
  description: string;
  tags: string[];
  favorite: boolean;
  runCount: number;
};

export type HistoryItem = {
  id: number;
  sql: string;
  status: string;
  rows: number;
  durationMs: number;
  cached: boolean;
  blockedBy: string | null;
  at: string | null;
};

export type RunResult = {
  ok: boolean;
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  truncated: boolean;
  durationMs: number;
  cached: boolean;
  error?: string;
  code?: string;
  tables: string[];
};

export type ColumnMeta = {
  id: number;
  name: string;
  dataType: string;
  description: string;
  isPk: boolean;
  nullable: boolean;
  masking: string;
  unit: string | null;
};

export type DatasetDetail = {
  dataset: {
    id: number;
    name: string;
    physical: string;
    physicalSchema: string;
    physicalTable: string;
    layer: string;
    grain: string;
    description: string;
    owner: string;
    refreshCadence: string;
    freshnessSloHours: number;
    rowCount: number;
    sizeMb: number | string;
    schemaVersion: number;
    status: string;
    accessPolicy: string;
    modelPath: string | null;
    tags: string;
    lastMaterializedAt: string | null;
    freshnessHours: number | null;
  };
  domain: { name: string; slug: string; regulator: string; ownerTeam: string; ownerContact: string } | null;
  source: { code: string; title: string; issuer: string; url: string | null; effectiveDate: string | null } | null;
  columns: ColumnMeta[];
  outbound: { id: number; fromColumn: string; toColumn: string; relationType: string; target: string }[];
  inbound: { id: number; fromColumn: string; toColumn: string; relationType: string; origin: string }[];
  runs: {
    id: number;
    startedAt: string;
    finishedAt: string | null;
    status: string;
    rowsIn: number;
    rowsOut: number;
    rowsDropped: number;
    watermark: string | null;
    commitSha: string | null;
    durationMs: number;
    errorMessage: string | null;
  }[];
  checks: {
    id: number;
    name: string;
    kind: string;
    expression: string;
    passed: boolean;
    observedValue: number | string | null;
    threshold: number | string | null;
    severity: string;
    ranAt: string;
  }[];
  preview: { columns: string[]; rows: Record<string, unknown>[]; error?: string };
};

export const KINDS = [
  { id: "vida", label: "Vida" },
  { id: "generales", label: "Generales" },
  { id: "ffmm", label: "FFMM" },
  { id: "fi", label: "FFII" },
  { id: "todos", label: "Todos" },
] as const;

export type KindId = (typeof KINDS)[number]["id"];

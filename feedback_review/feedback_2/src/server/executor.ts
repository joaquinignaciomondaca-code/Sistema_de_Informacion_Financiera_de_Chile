import { pool } from "@/db";
import { checksum, guardQuery } from "@/lib/sql-guard";
import { recordQuery, serializable } from "@/server/catalog";

export const MAX_ROWS = 400;
const TIMEOUT_MS = 5_000;
const CACHE_TTL_MS = 30_000;

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

type Cached = { columns: string[]; rows: Record<string, unknown>[]; at: number; tookMs: number };

const store = globalThis as typeof globalThis & { __mfcQueryCache?: Map<string, Cached> };
const cache = store.__mfcQueryCache ?? new Map<string, Cached>();
store.__mfcQueryCache = cache;

/**
 * Único camino permitido para ejecutar SQL desde la UI:
 * guard -> cache -> transacción read-only con timeout -> auditoría.
 */
export async function runSql(
  sqlText: string,
  opts: { actor: string; maxRows?: number; useCache?: boolean } = { actor: "anon" },
): Promise<RunResult> {
  const maxRows = Math.min(opts.maxRows ?? MAX_ROWS, MAX_ROWS);
  const started = Date.now();

  const guarded = guardQuery(sqlText, maxRows);
  if (!guarded.ok) {
    await recordQuery({
      actor: opts.actor,
      sqlText,
      status: "blocked",
      rowCount: 0,
      durationMs: Date.now() - started,
      cached: false,
      blockedBy: guarded.code,
      errorMessage: guarded.reason,
    });
    return {
      ok: false,
      columns: [],
      rows: [],
      rowCount: 0,
      truncated: false,
      durationMs: Date.now() - started,
      cached: false,
      code: guarded.code,
      error: guarded.reason,
      tables: [],
    };
  }

  const key = checksum(`${guarded.sql}|${maxRows}`);
  if (opts.useCache !== false) {
    const hit = cache.get(key);
    if (hit && Date.now() - hit.at < CACHE_TTL_MS) {
      return {
        ok: true,
        columns: hit.columns,
        rows: hit.rows.slice(0, maxRows),
        rowCount: hit.rows.length,
        truncated: hit.rows.length > maxRows,
        durationMs: Date.now() - started,
        cached: true,
        tables: guarded.tables,
      };
    }
  }

  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("SET TRANSACTION READ ONLY");
    await client.query(`SET LOCAL statement_timeout = ${TIMEOUT_MS}`);
    await client.query(`SET LOCAL lock_timeout = 2000`);
    await client.query(`SET LOCAL search_path TO mart, catalog, public`);
    const res = await client.query(guarded.sql);
    await client.query("COMMIT");

    const rows = serializable(res.rows ?? []);
    const columns = res.fields?.map((f) => f.name) ?? (rows[0] ? Object.keys(rows[0]) : []);
    const truncated = rows.length > maxRows;
    const limited = truncated ? rows.slice(0, maxRows) : rows;
    const durationMs = Date.now() - started;

    cache.set(key, { columns, rows, at: Date.now(), tookMs: durationMs });
    if (cache.size > 40) {
      const oldest = [...cache.entries()].sort((a, b) => a[1].at - b[1].at)[0];
      if (oldest) cache.delete(oldest[0]);
    }

    await recordQuery({
      actor: opts.actor,
      sqlText,
      status: "success",
      rowCount: limited.length,
      durationMs,
      cached: false,
    });

    return {
      ok: true,
      columns,
      rows: limited,
      rowCount: limited.length,
      truncated,
      durationMs,
      cached: false,
      tables: guarded.tables,
    };
  } catch (e) {
    await client.query("ROLLBACK").catch(() => undefined);
    const msg = (e as Error).message;
    await recordQuery({
      actor: opts.actor,
      sqlText,
      status: msg.toLowerCase().includes("canceling") ? "timeout" : "error",
      rowCount: 0,
      durationMs: Date.now() - started,
      cached: false,
      errorMessage: msg,
    });
    return {
      ok: false,
      columns: [],
      rows: [],
      rowCount: 0,
      truncated: false,
      durationMs: Date.now() - started,
      cached: false,
      code: msg.toLowerCase().includes("canceling") ? "statement_timeout" : "postgres_error",
      error: msg,
      tables: guarded.tables,
    };
  } finally {
    client.release();
  }
}

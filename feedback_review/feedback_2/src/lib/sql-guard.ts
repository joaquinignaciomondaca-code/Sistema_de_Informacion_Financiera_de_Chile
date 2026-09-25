/**
 * Guard de solo lectura para el ejecutor de SQL.
 *
 * Regla de oro del proyecto: el navegador NUNCA decide qué datos se leen.
 * Toda consulta pasa por este filtro (esquema permitido, sentencia única,
 * palabras prohibidas, límite de filas y timeout) y queda auditada.
 */

export const ALLOWED_SCHEMAS = ["mart", "catalog"] as const;

export const BLOCKED_TABLES = [
  "catalog.query_log",
  "catalog.saved_queries",
  "pg_shadow",
  "pg_user",
  "pg_authid",
  "pg_stat_activity",
];

const FORBIDDEN_WORDS = [
  "insert", "update", "delete", "drop", "alter", "create", "truncate",
  "grant", "revoke", "copy", "vacuum", "analyze", "call", "do", "merge",
  "upsert", "attach", "install", "load", "export", "import", "set", "reset",
  "listen", "notify", "refresh", "comment", "prepare", "deallocate", "lock",
];

export type GuardOk = { ok: true; sql: string; tables: string[] };
export type GuardFail = { ok: false; reason: string; code: string };
export type GuardResult = GuardOk | GuardFail;

export function guardQuery(raw: string, maxRows: number): GuardResult {
  // Los comentarios se ARRANCAN (no se prohíben): así un `-- nota` no rompe la
  // consulta, pero nadie puede esconder `; DROP TABLE` detrás de uno.
  let sql = (raw ?? "")
    .replace(/\/\*[\s\S]*?\*\//g, " ")
    .replace(/--[^\n]*/g, " ")
    .trim()
    .replace(/\s+/g, " ");
  if (!sql) return fail("empty", "La consulta está vacía.");

  sql = sql.replace(/;+$/, "");
  if (sql.includes(";")) {
    return fail("multi_statement", "Ejecuta una sola sentencia por vez.");
  }
  if (!/^(select|with|explain\s+select|explain\s+with)\b/i.test(sql)) {
    return fail(
      "not_a_select",
      "Sólo se permiten SELECT / WITH (el endpoint es de sólo lectura).",
    );
  }
  const lower = sql.toLowerCase();
  const hit = FORBIDDEN_WORDS.find((w) => new RegExp(`\\b${w}\\b`, "i").test(lower));
  if (hit) {
    return fail("forbidden_keyword", `Palabra clave no permitida: ${hit.toUpperCase()}`);
  }

  const tables = [
    ...new Set(
      [...lower.matchAll(/\b(?:from|join)\s+([a-z0-9_."]+)/gi)].map((m) =>
        m[1].replace(/["`]/g, "").replace(/^public\./, ""),
      ),
    ),
  ];
  for (const t of tables) {
    if (t.startsWith("(") || t.startsWith("$")) continue;
    const qualified = t.includes(".") ? t : `mart.${t}`;
    const schema = qualified.split(".")[0];
    if (!ALLOWED_SCHEMAS.includes(schema as "mart" | "catalog")) {
      return fail(
        "schema_not_allowed",
        `El esquema "${schema}" no está expuesto por esta API. Usa mart.* o catalog.*.`,
      );
    }
    if (BLOCKED_TABLES.includes(qualified)) {
      return fail("table_blocked", `La relación ${qualified} no es consultable desde la consola.`);
    }
  }

  // EXPLAIN ya devuelve pocas filas y no se puede envolver en un subselect.
  if (/^explain\b/i.test(sql)) {
    return { ok: true, sql, tables };
  }

  return {
    ok: true,
    // límite duro: se envuelve para que nadie pueda extraer la tabla completa
    sql: `SELECT * FROM (\n${sql}\n) AS _mfc_limit LIMIT ${Math.max(1, maxRows) + 1}`,
    tables,
  };
}

function fail(code: string, reason: string): GuardFail {
  return { ok: false, code, reason };
}

export function checksum(s: string): string {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}

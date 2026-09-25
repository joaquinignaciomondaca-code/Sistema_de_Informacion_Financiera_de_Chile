import type { Dataset } from "./data";

export type ResultColumn = { name: string; type: "text" | "number" | "date" };

export type QueryResult = {
  columns: ResultColumn[];
  rows: (string | number | null)[][];
  ms: number;
  rowCount: number;
  datasetSlug: string | null;
};

export class SqlError extends Error {
  hint?: string;
  constructor(message: string, hint?: string) {
    super(message);
    this.name = "SqlError";
    this.hint = hint;
  }
}

type Expr =
  | { k: "col"; name: string }
  | { k: "agg"; fn: "COUNT" | "SUM" | "AVG" | "MIN" | "MAX"; col: string | null; round?: number };

function splitTopLevel(input: string, sep: string): string[] {
  const out: string[] = [];
  let depth = 0;
  let inStr = false;
  let buf = "";
  const lowerSep = sep.toLowerCase();
  let i = 0;
  while (i < input.length) {
    const ch = input[i];
    if (ch === "'") inStr = !inStr;
    if (!inStr) {
      if (ch === "(") depth++;
      else if (ch === ")") depth--;
      if (depth === 0 && input.slice(i, i + sep.length).toLowerCase() === lowerSep) {
        out.push(buf);
        buf = "";
        i += sep.length;
        continue;
      }
    }
    buf += ch;
    i++;
  }
  out.push(buf);
  return out.map((s) => s.trim()).filter((s) => s.length > 0);
}

function parseLiteral(raw: string): string | number {
  const v = raw.trim();
  if (/^'.*'$/.test(v) || /^".*"$/.test(v)) return v.slice(1, -1);
  const n = Number(v.replace(/\./g, "").replace(",", "."));
  if (!Number.isNaN(n) && /^-?[\d.,\s]+$/.test(v)) return n;
  return v;
}

function parseExpr(raw: string): Expr {
  let expr = raw.trim();
  const aliasSplit = /\s+as\s+[a-z_][a-z0-9_]*\s*$/i.exec(expr);
  if (aliasSplit) expr = expr.slice(0, aliasSplit.index).trim();
  const roundMatch = /^round\s*\((.+),\s*(\d+)\s*\)$/i.exec(expr);
  if (roundMatch) {
    const inner = parseExpr(roundMatch[1]);
    if (inner.k !== "agg") throw new SqlError(`ROUND sólo admite agregados, se recibió: ${roundMatch[1]}`);
    return { ...inner, round: Number(roundMatch[2]) };
  }

  const aggMatch = /^(count|sum|avg|min|max)\s*\(\s*(\*|[a-z_][\w.]*)\s*\)$/i.exec(expr);
  if (aggMatch) {
    const fn = aggMatch[1].toUpperCase() as Expr extends { k: "agg"; fn: infer F } ? F : never;
    const col = aggMatch[2] === "*" ? null : aggMatch[2];
    return { k: "agg", fn, col };
  }
  if (/^[\w"]+"?\.[\w"]+"?$/.test(expr) || /^[a-z_][a-z0-9_]*$/i.test(expr)) {
    return { k: "col", name: expr.replace(/"/g, "") };
  }
  throw new SqlError(
    `Expresión no soportada en SELECT: «${raw.trim()}»`,
    "Admitidas: columna, COUNT(*), SUM(col), AVG(col), MIN(col), MAX(col) y ROUND(agg, 2), con alias opcional AS nombre.",
  );
}

function aliasOf(raw: string, expr: Expr): string {
  const m = /\s+as\s+([a-z_][a-z0-9_]*)\s*$/i.exec(raw.trim());
  if (m) return m[1];
  if (expr.k === "col") return expr.name;
  return `${expr.fn.toLowerCase()}_${expr.col ?? "*"}`.replace(/\*/g, "star");
}

type Condition = (row: Record<string, unknown>) => boolean;

function buildCondition(fragment: string, dataset: Dataset): Condition {
  const parts = splitTopLevel(fragment, " and ");
  const cols = new Set(dataset.columnas.map((c) => c.name));
  const fns = parts.map((part) => {
    const inMatch = /^([a-z_][\w]*)\s+(not\s+)?in\s*\((.+)\)$/i.exec(part.trim());
    if (inMatch) {
      const col = inMatch[1];
      const negated = Boolean(inMatch[2]);
      assertColumn(col, cols, dataset);
      const values = inMatch[3].split(",").map(parseLiteral);
      return (row: Record<string, unknown>) => {
        const hit = values.some((v) => looseEq(row[col], v));
        return negated ? !hit : hit;
      };
    }
    const m = /^([a-z_][\w]*)\s*(=|!=|<>|>=|<=|>|<)\s*(.+)$/i.exec(part.trim());
    if (m) {
      const [, col, op, rawValue] = m;
      assertColumn(col, cols, dataset);
      const value = parseLiteral(rawValue);
      return (row: Record<string, unknown>) => compare(row[col], op, value);
    }
    throw new SqlError(
      `Condición WHERE no reconocida: «${part.trim()}»`,
      "Formatos válidos: columna > 100, columna = 'texto', columna IN ('a', 'b'), combinadas con AND.",
    );
  });
  return (row) => fns.every((f) => f(row));
}

function assertColumn(col: string, cols: Set<string>, dataset: Dataset) {
  if (!cols.has(col)) {
    throw new SqlError(
      `La columna «${col}» no existe en ${dataset.slug}`,
      `Columnas disponibles: ${[...cols].join(", ")}.`,
    );
  }
}

function looseEq(a: unknown, b: unknown) {
  if (typeof a === "number" && typeof b === "number") return a === b;
  return String(a ?? "").toLowerCase() === String(b ?? "").toLowerCase();
}

function compare(left: unknown, op: string, right: unknown) {
  const bothNumeric = typeof left === "number" && typeof right === "number";
  const l = bothNumeric ? (left as number) : String(left ?? "").toLowerCase();
  const r = bothNumeric ? (right as number) : String(right ?? "").toLowerCase();
  switch (op) {
    case "=":
      return l === r;
    case "!=":
    case "<>":
      return l !== r;
    case ">":
      return l > r;
    case "<":
      return l < r;
    case ">=":
      return l >= r;
    case "<=":
      return l <= r;
    default:
      return false;
  }
}

function roundTo(v: number, n: number) {
  const f = Math.pow(10, n);
  return Math.round(v * f) / f;
}

function evaluate(expr: Expr, group: Record<string, unknown>[]): number | string | null {
  if (expr.k === "col") {
    const first = group[0]?.[expr.name];
    return (first ?? null) as number | string | null;
  }
  const values = expr.col
    ? group.map((r) => r[expr.col as string]).filter((v) => v !== null && v !== undefined)
    : [];
  switch (expr.fn) {
    case "COUNT":
      return expr.col ? values.length : group.length;
    case "SUM":
    case "AVG": {
      const nums = values.map(Number).filter((v) => !Number.isNaN(v));
      if (nums.length === 0) return null;
      const total = nums.reduce((a, b) => a + b, 0);
      const out = expr.fn === "SUM" ? total : total / nums.length;
      return expr.round !== undefined ? roundTo(out, expr.round) : out;
    }
    case "MIN":
    case "MAX": {
      const nums = values.map(Number).filter((v) => !Number.isNaN(v));
      if (nums.length === 0) return null;
      const out = expr.fn === "MIN" ? Math.min(...nums) : Math.max(...nums);
      return expr.round !== undefined ? roundTo(out, expr.round) : out;
    }
    default:
      return null;
  }
}

const PATTERN =
  /^select\s+([\s\S]+?)\s+from\s+['"`]([^'"`]+)['"`](?:\s+where\s+([\s\S]+?))?(?:\s+group\s+by\s+([\s\S]+?))?(?:\s+order\s+by\s+([\s\S]+?))?(?:\s+limit\s+(\d+))?\s*$/i;

export function runQuery(sql: string, datasets: Dataset[]): QueryResult {
  const started = performance.now();
  const clean = sql.trim().replace(/;\s*$/, "").trim();

  if (/^show\s+tables$/i.test(clean)) {
    return {
      columns: [
        { name: "tabla", type: "text" },
        { name: "industria", type: "text" },
        { name: "filas", type: "number" },
      ],
      rows: datasets.map((d) => [d.slug, d.industria, d.filas.length]),
      ms: Math.max(1, Math.round(performance.now() - started)),
      rowCount: datasets.length,
      datasetSlug: null,
    };
  }

  const match = PATTERN.exec(clean);
  if (!match) {
    throw new SqlError(
      "No pude parsear la consulta.",
      "Sintaxis admitida: SELECT campos FROM 'tabla' [WHERE …] [GROUP BY …] [ORDER BY campo DESC] [LIMIT n]. La tabla va entre comillas simples.",
    );
  }

  const [, fields, table, where, group, order, limit] = match;
  const dataset = datasets.find((d) => d.slug === table);
  if (!dataset) {
    throw new SqlError(
      `No existe la tabla «${table}».`,
      `Usa una de: ${datasets.map((d) => `'${d.slug}'`).join(", ")}. Escribe SHOW TABLES para listarlas.`,
    );
  }

  const colNames = new Set(dataset.columnas.map((c) => c.name));
  let source = dataset.filas as Record<string, unknown>[];
  if (where) {
    const cond = buildCondition(where, dataset);
    source = source.filter(cond);
  }

  const selectItems = splitTopLevel(fields, ",").map((raw) => {
    if (raw.trim() === "*") return null;
    const expr = parseExpr(raw);
    if (expr.k === "col") assertColumn(expr.name, colNames, dataset);
    if (expr.k === "agg" && expr.col) assertColumn(expr.col, colNames, dataset);
    return { expr, alias: aliasOf(raw, expr) };
  });

  const groupCols = group ? splitTopLevel(group, ",") : null;
  let outColumns: ResultColumn[];
  let outRows: (string | number | null)[][];

  if (groupCols) {
    groupCols.forEach((c) => assertColumn(c, colNames, dataset));
    const buckets = new Map<string, Record<string, unknown>[]>();
    for (const row of source) {
      const key = groupCols.map((c) => String(row[c])).join("\u0001");
      const list = buckets.get(key);
      if (list) list.push(row);
      else buckets.set(key, [row]);
    }
    const items = selectItems.map((it, idx) => {
      if (it) return it;
      const fallback = groupCols[idx];
      if (!fallback) {
        throw new SqlError("SELECT * no puede combinarse con GROUP BY.", `Agrupa y lista campos: SELECT ${groupCols.join(", ")}, COUNT(*) …`);
      }
      return { expr: { k: "col", name: fallback } as Expr, alias: fallback };
    });
    outColumns = items.map((it) => ({
      name: it.alias,
      type: (it.expr.k === "agg" && it.expr.fn !== "COUNT" ? "number" : dataset.columnas.find((c) => c.name === (it.expr.k === "col" ? it.expr.name : it.expr.col))?.type ?? "number") as ResultColumn["type"],
    }));
    outRows = [...buckets.values()].map((rowsInGroup) => items.map((it) => evaluate(it.expr, rowsInGroup)));
  } else {
    if (selectItems.some((it) => it === null)) {
      outColumns = dataset.columnas.map((c) => ({ name: c.name, type: c.type }));
      outRows = source.map((row) => dataset.columnas.map((c) => (row[c.name] ?? null) as string | number | null));
    } else {
      const items = selectItems as { expr: Expr; alias: string }[];
      outColumns = items.map((it) => ({
        name: it.alias,
        type: (dataset.columnas.find((c) => c.name === (it.expr.k === "col" ? it.expr.name : it.expr.col))?.type ??
          (it.expr.k === "agg" ? "number" : "text")) as ResultColumn["type"],
      }));
      outRows = source.map((row) => items.map((it) => evaluate(it.expr, [row])));
    }
  }

  if (order) {
    const om = /^([a-z_][\w]*)\s*(asc|desc)?$/i.exec(order.trim());
    if (!om) throw new SqlError(`ORDER BY no reconocido: «${order}»`, "Usa ORDER BY columna [ASC|DESC].");
    const key = om[1].toLowerCase();
    const dir = (om[2] ?? "asc").toLowerCase() === "desc" ? -1 : 1;
    const idx = outColumns.findIndex((c) => c.name.toLowerCase() === key);
    if (idx < 0) throw new SqlError(`No puedo ordenar por «${om[1]}».`, `Ordena por: ${outColumns.map((c) => c.name).join(", ")}.`);
    outRows = [...outRows].sort((a, b) => {
      const av = a[idx];
      const bv = b[idx];
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
      return String(av).localeCompare(String(bv), "es") * dir;
    });
  }

  if (limit) outRows = outRows.slice(0, Number(limit));

  return {
    columns: outColumns,
    rows: outRows,
    ms: Math.max(1, Math.round(performance.now() - started)),
    rowCount: outRows.length,
    datasetSlug: dataset.slug,
  };
}

export function detectIndustry(sql: string): string | null {
  const m = /from\s+['"`]([^'"`]+)['"`]/i.exec(sql);
  return m ? m[1].split(".")[0] : null;
}

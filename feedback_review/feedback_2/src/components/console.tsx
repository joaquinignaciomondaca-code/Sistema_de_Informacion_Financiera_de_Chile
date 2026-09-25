"use client";

import { useMemo, useRef, useState } from "react";
import type { HistoryItem, RunResult, SavedQuery } from "@/lib/types";
import { fmtCell, fmtDuration, fmtNum, relTime } from "@/lib/format";

type Props = {
  sql: string;
  onSqlChange: (v: string) => void;
  result: RunResult | null;
  running: boolean;
  onRun: () => void;
  maxRows: number;
  onMaxRows: (n: number) => void;
  saved: SavedQuery[];
  onPickSaved: (s: SavedQuery) => void;
  onToggleFavorite: (s: SavedQuery) => void;
  onSaveCurrent: () => void;
  onShare: () => void;
  shareNote: string;
  history: HistoryItem[];
  onReloadHistory: () => void;
  onUseHistory: (sqlText: string) => void;
};

function formatSql(s: string) {
  return s
    .replace(/\s+/g, " ")
    .replace(/\b(select|from|where|group by|order by|limit|having|join|left join|inner join|on|union all|with)\b/gi, "\n$1")
    .replace(/^\n/, "")
    .split("\n")
    .map((l) => l.trim().replace(/\s+/g, " "))
    .map((l) => (/^(from|where|group|order|having|limit|join|left|inner|union)/i.test(l) ? l : l))
    .join("\n");
}

function toCsv(columns: string[], rows: Record<string, unknown>[]) {
  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [columns.join(";"), ...rows.map((r) => columns.map((c) => esc(r[c])).join(";"))].join("\n");
}

export function Console(p: Props) {
  const [tab, setTab] = useState<"grid" | "chart" | "json" | "history">("grid");
  const [sort, setSort] = useState<{ col: string; dir: 1 | -1 } | null>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  const rows = useMemo(() => {
    if (!p.result?.rows.length) return [];
    if (!sort) return p.result.rows;
    return [...p.result.rows].sort((a, b) => {
      const av = a[sort.col];
      const bv = b[sort.col];
      const an = typeof av === "number" ? av : Number(av);
      const bn = typeof bv === "number" ? bv : Number(bv);
      if (Number.isFinite(an) && Number.isFinite(bn)) return (an - bn) * sort.dir;
      return String(av ?? "").localeCompare(String(bv ?? "")) * sort.dir;
    });
  }, [p.result, sort]);

  const chart = useMemo(() => {
    if (!rows.length) return null;
    const cols = p.result?.columns ?? Object.keys(rows[0]);
    const numCol = cols.find((c) => rows.some((r) => Number.isFinite(Number(r[c])) && r[c] !== null) && !/^(id|anio|mes)$/.test(c));
    const labelCol = cols.find((c) => c !== numCol && typeof rows[0][c] !== "number");
    if (!numCol) return null;
    const data = rows
      .slice(0, 14)
      .map((r) => ({ label: String(r[labelCol ?? cols[0]] ?? "—"), value: Number(r[numCol]) || 0 }));
    const max = Math.max(...data.map((d) => Math.abs(d.value)), 1);
    return { data, numCol, labelCol: labelCol ?? "—", max };
  }, [rows, p.result]);

  return (
    <div className="flex h-full min-h-0 flex-col" style={{ background: "var(--bg-panel)" }}>
      {/* barra de acciones */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[var(--border)] px-3 py-2" style={{ background: "var(--bg-raised)" }}>
        <span className="text-[11px] font-bold tracking-[0.6px] uppercase">Consola SQL</span>
        <span className="mono text-[10px] text-[var(--text-mute)]">postgres · read-only · search_path=mart,catalog</span>
        <div className="ml-auto flex flex-wrap items-center gap-1.5">
          <select
            value={p.maxRows}
            onChange={(e) => p.onMaxRows(Number(e.target.value))}
            aria-label="Filas máximas"
            className="inset focus-ring rounded-md px-1.5 py-1 text-[11px]"
          >
            {[50, 100, 200, 400].map((n) => (
              <option key={n} value={n}>
                top {n}
              </option>
            ))}
          </select>
          <button className="btn focus-ring" onClick={() => taRef.current && p.onSqlChange(formatSql(p.sql))} title="Formateo simple (no es un parser)">
            Formatear
          </button>
          <button className="btn focus-ring" onClick={() => p.onSqlChange(`EXPLAIN ${p.sql.replace(/;+$/, "")}`)} title="Plan de ejecución (también pasa por el guard)">
            Plan
          </button>
          <button className="btn focus-ring" onClick={p.onSaveCurrent} disabled={!p.sql.trim()}>
            Guardar
          </button>
          <button className="btn focus-ring" onClick={p.onShare}>
            Compartir link
          </button>
          <button className="btn btn-primary focus-ring" onClick={p.onRun} disabled={p.running}>
            {p.running ? "Ejecutando…" : "Ejecutar ⌘↵"}
          </button>
        </div>
      </div>

      {/* chips de consultas guardadas */}
      <div className="flex items-center gap-1.5 overflow-x-auto border-b border-[var(--border)] px-3 py-1.5" style={{ background: "var(--bg-inset)" }}>
        {p.saved.length === 0 && <span className="text-[10.5px] text-[var(--text-mute)]">Sin consultas guardadas todavía.</span>}
        {p.saved.map((s) => (
          <span key={s.slug} className={`chip ${s.favorite ? "chip-active" : ""}`} title={`${s.description}\n\nEjecuciones: ${s.runCount}`}>
            <button
              className="focus-ring cursor-pointer"
              onClick={() => (s.favorite ? p.onToggleFavorite(s) : p.onPickSaved(s))}
              aria-label={`Ejecutar ${s.title}`}
            >
              {s.title}
            </button>
            <button className="focus-ring cursor-pointer opacity-70 hover:opacity-100" title={s.favorite ? "Quitar de favoritos" : "Marcar favorito"} onClick={() => p.onToggleFavorite(s)}>
              {s.favorite ? "★" : "☆"}
            </button>
          </span>
        ))}
        <span className="ml-auto shrink-0 text-[10px] text-[var(--text-mute)]">
          <button className="focus-ring cursor-pointer underline decoration-dotted" onClick={() => { p.onReloadHistory(); setTab("history"); }}>
            historial
          </button>
        </span>
      </div>

      {/* editor */}
      <div className="relative border-b border-[var(--border)]" style={{ background: "var(--bg-inset)" }}>
        <textarea
          ref={taRef}
          value={p.sql}
          onChange={(e) => p.onSqlChange(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
              e.preventDefault();
              p.onRun();
            }
            if (e.key === "Tab") {
              e.preventDefault();
              const el = e.currentTarget;
              const start = el.selectionStart;
              p.onSqlChange(`${p.sql.slice(0, start)}  ${p.sql.slice(el.selectionEnd)}`);
              requestAnimationFrame(() => el.setSelectionRange(start + 2, start + 2));
            }
          }}
          spellCheck={false}
          aria-label="Editor SQL"
          placeholder="SELECT ... FROM mart.vida_bonos WHERE periodo = '2026-01' GROUP BY 1 ORDER BY 2 DESC;"
          className="mono block h-[104px] w-full resize-y bg-transparent px-3 py-2.5 text-[12.5px] leading-[1.55] outline-none"
        />
        <span className="mono absolute right-3 top-1.5 text-[9.5px] text-[var(--text-mute)]">
          {p.sql.split("\n").length} ln · {p.sql.length} ch
        </span>
      </div>

      {/* resultados */}
      <div className="flex items-center gap-1.5 border-b border-[var(--border)] px-3 py-1.5 text-[10.5px]">
        {(["grid", "chart", "json", "history"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`chip ${tab === t ? "chip-active" : ""}`}>
            {t === "grid" ? "Tabla" : t === "chart" ? "Gráfico" : t === "json" ? "JSON" : "Auditoría"}
          </button>
        ))}
        {p.result && (
          <span className="mono ml-2 flex flex-wrap items-center gap-2 text-[10px] text-[var(--text-dim)]">
            <span>{fmtNum(p.result.rowCount)} filas</span>
            <span>· {fmtDuration(p.result.durationMs)}</span>
            {p.result.cached && <span style={{ color: "var(--warn)" }}>· cache hit (30 s)</span>}
            {p.result.truncated && <span style={{ color: "var(--bad)" }}>· recortado a {p.maxRows}</span>}
            {p.result.tables.length > 0 && <span className="truncate">· {p.result.tables.join(", ")}</span>}
          </span>
        )}
        <span className="ml-auto flex items-center gap-1.5">
          {p.shareNote && <span className="mono text-[10px] text-[var(--ok)]">{p.shareNote}</span>}
          {p.result?.ok && (
            <button
              className="btn focus-ring"
              onClick={() => {
                const blob = new Blob([toCsv(p.result!.columns, rows)], { type: "text/csv;charset=utf-8" });
                const a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                a.download = `mfc-${Date.now()}.csv`;
                a.click();
                URL.revokeObjectURL(a.href);
              }}
            >
              CSV
            </button>
          )}
        </span>
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        {p.result === null && !p.running && <IdleState onPick={p.onPickSaved} saved={p.saved} />}
        {p.running && <div className="p-4 text-[11.5px] text-[var(--text-mute)]">Ejecutando contra Postgres con statement_timeout=5 s…</div>}
        {p.result && !p.result.ok && (
          <div className="fade-up m-3 rounded-lg border p-3" style={{ borderColor: "var(--bad)", background: "color-mix(in srgb, var(--bad) 9%, transparent)" }}>
            <div className="mb-1 text-[11.5px] font-bold" style={{ color: "var(--bad)" }}>
              {p.result.code === "statement_timeout" ? "Query cancelada por timeout" : "Consulta rechazada o inválida"}
            </div>
            <div className="mono text-[11px] text-[var(--text-dim)]">{p.result.error}</div>
            <div className="mt-2 text-[10.5px] text-[var(--text-mute)]">
              El guard bloquea DML/DDL, comentarios, sentencias múltiples y esquemas no publicados. Cada intento (incluidos los bloqueos) queda en{" "}
              <span className="mono">catalog.query_log</span>.
            </div>
          </div>
        )}
        {p.result?.ok && tab === "grid" && (
          <table className="w-full border-collapse text-[11.5px]">
            <thead>
              <tr>
                <th className="th w-8">#</th>
                {p.result.columns.map((c) => (
                  <th
                    key={c}
                    className="th"
                    onClick={() => setSort((s) => (s?.col === c ? (s.dir === 1 ? { col: c, dir: -1 } : null) : { col: c, dir: 1 }))}
                    title="Ordenar"
                  >
                    {c}
                    {sort?.col === c && <span className="ml-1">{sort.dir === 1 ? "▲" : "▼"}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} onClick={() => {
                  const text = p.result!.columns.map((c) => `${c}: ${fmtCell(c, r[c])}`).join("\n");
                  navigator.clipboard?.writeText(text);
                }} className="cursor-copy hover:bg-[var(--bg-hover)]">
                  <td className="td mono text-[var(--text-mute)]">{i + 1}</td>
                  {p.result!.columns.map((c) => (
                    <td key={c} className={`td mono ${typeof r[c] === "number" || /^-?\d+(\.\d+)?$/.test(String(r[c])) ? "num text-[var(--text)]" : ""}`} title={fmtCell(c, r[c])}>
                      {fmtCell(c, r[c])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {p.result?.ok && tab === "chart" && chart && (
          <div className="p-4">
            <div className="mb-2 text-[11px] text-[var(--text-dim)]">
              <span className="mono">{chart.numCol}</span> por <span className="mono">{chart.labelCol}</span> · máx {fmtNum(chart.max)}
            </div>
            <div className="flex flex-col gap-1.5">
              {chart.data.map((d, i) => (
                <div key={i} className="flex items-center gap-2 text-[10.5px]">
                  <span className="mono w-[150px] shrink-0 truncate text-right text-[var(--text-dim)]" title={d.label}>
                    {d.label}
                  </span>
                  <span className="relative h-4 flex-1 overflow-hidden rounded-sm" style={{ background: "var(--bg-raised)" }}>
                    <span
                      className="absolute inset-y-0 left-0 rounded-sm"
                      style={{ width: `${Math.max(1, (Math.abs(d.value) / chart.max) * 100)}%`, background: d.value < 0 ? "var(--bad)" : "var(--accent)" }}
                    />
                  </span>
                  <span className="mono w-[110px] shrink-0 text-[var(--text)]">{fmtCell(chart.numCol, d.value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {p.result?.ok && tab === "chart" && !chart && <div className="p-4 text-[11.5px] text-[var(--text-mute)]">Se necesita al menos una columna numérica para graficar.</div>}
        {p.result?.ok && tab === "json" && (
          <pre className="mono m-0 p-3 text-[10.5px] leading-relaxed text-[var(--text-dim)]">{JSON.stringify(rows, null, 2).slice(0, 20000)}</pre>
        )}
        {tab === "history" && (
          <table className="w-full border-collapse text-[11px]">
            <thead>
              <tr>
                <th className="th">cuándo</th>
                <th className="th">estado</th>
                <th className="th">filas</th>
                <th className="th">duración</th>
                <th className="th">consulta</th>
              </tr>
            </thead>
            <tbody>
              {p.history.map((h) => (
                <tr key={h.id} onClick={() => p.onUseHistory(h.sql)} className="cursor-pointer hover:bg-[var(--bg-hover)]" title="Reutilizar esta consulta">
                  <td className="td mono text-[var(--text-mute)]">{relTime(h.at)}</td>
                  <td className="td">
                    <span
                      className="tag"
                      style={{
                        color: h.status === "success" ? "var(--ok)" : h.status === "blocked" ? "var(--warn)" : "var(--bad)",
                        borderColor: "currentColor",
                      }}
                    >
                      {h.blockedBy ?? h.status}
                    </span>
                  </td>
                  <td className="td mono num">{fmtNum(h.rows)}</td>
                  <td className="td mono">{fmtDuration(h.durationMs)}</td>
                  <td className="td mono max-w-[520px] truncate text-[var(--text-dim)]">{h.sql}</td>
                </tr>
              ))}
              {p.history.length === 0 && (
                <tr>
                  <td className="td text-[var(--text-mute)]" colSpan={5}>
                    Ejecuta algo: toda corrida (y todo intento bloqueado) se registra en catalog.query_log.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function IdleState({ saved, onPick }: { saved: SavedQuery[]; onPick: (s: SavedQuery) => void }) {
  return (
    <div className="p-4">
      <div className="mb-3 text-[11.5px] text-[var(--text-dim)]">
        Sin resultados aún. Elige una consulta del equipo (son <span className="mono">catalog.saved_queries</span>, versionables en Git) o escribe SQL:
      </div>
      <ul className="flex flex-col gap-1.5">
        {saved.map((s) => (
          <li key={s.slug}>
            <button onClick={() => onPick(s)} className="focus-ring w-full rounded-lg border border-[var(--border)] p-2 text-left hover:bg-[var(--bg-hover)]">
              <div className="flex items-baseline gap-2">
                <span className="text-[11.5px] font-semibold">{s.title}</span>
                <span className="tag">{s.tags.join(" · ") || "query"}</span>
                <span className="mono ml-auto text-[10px] text-[var(--text-mute)]">{s.runCount} ejecuciones</span>
              </div>
              <div className="mono mt-1 line-clamp-2 text-[10.5px] text-[var(--text-mute)]">{s.sql}</div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import type { SavedQuery } from "@/lib/store";
import type { Dataset } from "@/lib/data";

type Result = {
  columns: { name: string; type: string }[];
  rows: (string | number | null)[][];
  ms: number;
  rowCount: number;
  datasetSlug: string | null;
};

type Run = {
  id: number;
  sql: string;
  ok: boolean;
  error?: string;
  hint?: string;
  result?: Result;
};

const CHIPS: { label: string; sql: string }[] = [
  {
    label: "Renta fija por tipo de bono",
    sql: "SELECT tipo_bono, COUNT(*) AS tenencias, ROUND(AVG(tir_mercado_pct), 2) AS tir_promedio, ROUND(SUM(monto_m_clp), 1) AS monto_total FROM 'vida.bonos' GROUP BY tipo_bono ORDER BY monto_total DESC;",
  },
  {
    label: "Aseguradoras por participación",
    sql: "SELECT nombre_aseguradora, participacion_pct, inversion_ultimo_reporte_m_clp FROM 'vida.aseguradoras' WHERE estado = 'Activa' ORDER BY participacion_pct DESC LIMIT 8;",
  },
  {
    label: "TIR media por emisor",
    sql: "SELECT emisor, ROUND(AVG(tir_mercado_pct), 2) AS tir_media, ROUND(SUM(monto_m_clp), 1) AS monto_total FROM 'vida.bonos' GROUP BY emisor ORDER BY monto_total DESC;",
  },
  {
    label: "Repos: contrapartes y tasas",
    sql: "SELECT nombre_contraparte, COUNT(*) AS operaciones, ROUND(AVG(tasa_pct), 2) AS tasa_media, SUM(valorizacion_cierre_m_clp) AS total_m_clp FROM 'fi.repos' GROUP BY nombre_contraparte ORDER BY total_m_clp DESC;",
  },
  {
    label: "Forwards por contraparte",
    sql: "SELECT nombre_contraparte, tipo_derivado, notional_m_clp, precio_forward_pactado FROM 'ffmm.derivados' ORDER BY notional_m_clp DESC LIMIT 6;",
  },
  {
    label: "Bienes raíces por comuna",
    sql: "SELECT comuna, COUNT(*) AS propiedades, SUM(tasacion_comercial_m_clp) AS tasacion_m_clp FROM 'generales.bienes_raices' GROUP BY comuna ORDER BY tasacion_m_clp DESC LIMIT 5;",
  },
  {
    label: "Rentabilidad 12m por fondo",
    sql: "SELECT fondo, rentabilidad_12m_pct, patrimonio_m_clp FROM 'pensiones.fondos' ORDER BY rentabilidad_12m_pct DESC;",
  },
];

const fmt = (v: string | number | null, type: string) => {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") {
    const dec = Number.isInteger(v) ? 0 : Math.abs(v) < 10 ? 2 : 1;
    return v.toLocaleString("es-CL", { minimumFractionDigits: dec, maximumFractionDigits: dec });
  }
  if (type === "date") return String(v).slice(0, 10);
  return String(v);
};

function Chart({ result }: { result: Result }) {
  const numericIdx = result.columns.findIndex((c) => c.type === "number");
  const labelIdx = result.columns.findIndex((c) => c.type !== "number");
  if (numericIdx < 0 || result.rows.length < 2) return null;

  const vals = result.rows.map((r) => Number(r[numericIdx] ?? 0));
  const labels = result.rows.map((r) => String(labelIdx >= 0 ? r[labelIdx] : "").slice(0, 14));
  const max = Math.max(...vals.map(Math.abs), 1);
  const bars = vals.length <= 16;

  if (bars) {
    const w = 720;
    const h = 240;
    const bw = (w - 24) / vals.length;
    return (
      <div className="border border-rule bg-ink p-4">
        <div className="label text-mut">
          {result.columns[numericIdx].name} · {result.columns[labelIdx >= 0 ? labelIdx : 0].name}
        </div>
        <svg viewBox={`0 0 ${w} ${h}`} className="mt-3 w-full" role="img" aria-label="Gráfico de barras del resultado">
          {[0, 1, 2, 3].map((i) => (
            <line key={i} x1="0" x2={w} y1={20 + i * 50} y2={20 + i * 50} stroke="#1f2a2c" />
          ))}
          {vals.map((v, i) => {
            const bh = Math.max(2, (Math.abs(v) / max) * (h - 70));
            const x = 12 + i * bw;
            return (
              <g key={i} className="grow-bar" style={{ animationDelay: `${i * 45}ms` }}>
                <rect x={x} y={h - 40 - bh} width={Math.max(4, bw - 10)} height={bh} fill="#00d09a" opacity="0.85" />
                <text x={x} y={h - 24} fill="#7e8f8b" fontSize="11" fontFamily="IBM Plex Mono, monospace">
                  {labels[i]}
                </text>
                <text x={x} y={h - 46 - bh} fill="#e6edea" fontSize="11" fontFamily="IBM Plex Mono, monospace">
                  {fmt(v, "number")}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    );
  }

  const w = 720;
  const h = 240;
  const min = Math.min(...vals);
  const span = max - min || 1;
  const d = vals
    .map((v, i) => {
      const x = 12 + (i / (vals.length - 1)) * (w - 24);
      const y = h - 40 - ((v - min) / span) * (h - 80);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="border border-rule bg-ink p-4">
      <div className="label text-mut">{result.columns[numericIdx].name}</div>
      <svg viewBox={`0 0 ${w} ${h}`} className="mt-3 w-full" role="img" aria-label="Serie del resultado">
        {[0, 1, 2, 3].map((i) => (
          <line key={i} x1="0" x2={w} y1={20 + i * 50} y2={20 + i * 50} stroke="#1f2a2c" />
        ))}
        <path className="draw-line" d={d} fill="none" stroke="#00d09a" strokeWidth="2" />
      </svg>
    </div>
  );
}

function ResultBlock({ run }: { run: Run }) {
  const [view, setView] = useState<"tabla" | "grafico">("tabla");
  const [saving, setSaving] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [saved, setSaved] = useState(false);

  const save = async () => {
    const res = await fetch("/api/consultas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ titulo, sql: run.sql }),
    });
    if (res.ok) {
      setSaved(true);
      setSaving(false);
      window.dispatchEvent(new CustomEvent("consulta:guardada"));
    }
  };

  if (run.ok && run.result) {
    const r = run.result;
    return (
      <div className="fade border border-rule bg-panel">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rule px-4 py-2">
          <div className="flex items-center gap-3 label text-mut">
            <span className="text-em">{r.ms} ms</span>
            <span>{r.rowCount} filas</span>
            <span className="text-rule2">/</span>
            <span>{r.datasetSlug ?? "metadata"}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex border border-rule">
              <button
                onClick={() => setView("tabla")}
                className={`px-3 py-1 label transition-colors ${view === "tabla" ? "bg-em text-ink" : "text-mut hover:text-paper"}`}
              >
                Tabla
              </button>
              <button
                onClick={() => setView("grafico")}
                className={`px-3 py-1 label transition-colors ${view === "grafico" ? "bg-em text-ink" : "text-mut hover:text-paper"}`}
              >
                Gráfico
              </button>
            </div>
            <button
              onClick={() => setSaving((s) => !s)}
              className="border border-rule px-3 py-1 label text-mut transition-colors hover:border-em hover:text-em"
            >
              {saved ? "Guardada ✓" : "Guardar"}
            </button>
          </div>
        </div>

        {saving && (
          <div className="flex flex-wrap items-center gap-2 border-b border-rule bg-panel2 px-4 py-3">
            <input
              autoFocus
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              placeholder="Título de la consulta guardada…"
              className="min-w-[240px] flex-1 border border-rule bg-ink px-3 py-2 font-mono text-xs text-paper outline-none placeholder:text-mut focus:border-em"
            />
            <button onClick={save} className="bg-em px-4 py-2 label text-ink transition-colors hover:bg-[#02e2a4]">
              Guardar en Postgres
            </button>
          </div>
        )}

        {view === "tabla" ? (
          <div className="max-h-[320px] overflow-auto">
            <table className="w-full border-collapse font-mono text-xs tnum">
              <thead className="sticky top-0 z-10">
                <tr>
                  <th className="w-10 border-b border-rule bg-panel2 px-3 py-2 text-right label text-mut">#</th>
                  {r.columns.map((c) => (
                    <th
                      key={c.name}
                      className={`border-b border-rule bg-panel2 px-3 py-2 label ${
                        c.type === "number" ? "text-right text-em" : "text-left text-em"
                      }`}
                    >
                      {c.name}
                      <span className="ml-1 text-mut normal-case">{c.type === "number" ? "n" : ""}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {r.rows.map((row, i) => (
                  <tr key={i} className="border-b border-rule/70 transition-colors hover:bg-em/5">
                    <td className="px-3 py-1.5 text-right text-rule2">{i + 1}</td>
                    {row.map((cell, j) => {
                      const numeric = r.columns[j].type === "number";
                      const negative = numeric && typeof cell === "number" && cell < 0;
                      return (
                        <td
                          key={j}
                          className={`px-3 py-1.5 whitespace-nowrap ${
                            numeric ? "text-right" : "text-left"
                          } ${negative ? "text-loss" : numeric ? "text-paper" : "text-paper/85"}`}
                        >
                          {fmt(cell, r.columns[j].type)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
                {r.rows.length === 0 && (
                  <tr>
                    <td colSpan={r.columns.length + 1} className="px-4 py-8 text-center text-mut">
                      La consulta corrió bien pero no devolvió filas.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-4">
            <Chart result={r} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="fade border border-loss/40 bg-loss/5 px-4 py-3">
      <div className="label text-loss">Error en la consulta</div>
      <p className="mt-2 font-mono text-xs text-paper">{run.error}</p>
      {run.hint && <p className="mt-2 text-xs leading-relaxed text-mut">{run.hint}</p>}
    </div>
  );
}

export function Terminal({
  datasets,
  initialConsultas,
  onConsultasChanged,
}: {
  datasets: Dataset[];
  initialConsultas: SavedQuery[];
  onConsultasChanged: (items: SavedQuery[]) => void;
}) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [sql, setSql] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<SavedQuery[]>(initialConsultas);
  const [showSaved, setShowSaved] = useState(false);
  const nextId = useRef(1);
  const started = useRef(false);
  const feed = useRef<HTMLDivElement>(null);

  const execute = async (query: string) => {
    const text = query.trim();
    if (!text || busy) return;
    setBusy(true);
    setSql("");
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql: text }),
      });
      const data = await res.json();
      const run: Run = res.ok
        ? { id: nextId.current++, sql: text, ok: true, result: data as Result }
        : { id: nextId.current++, sql: text, ok: false, error: data.error, hint: data.hint };
      setRuns((prev) => [...prev, run]);
    } catch {
      setRuns((prev) => [
        ...prev,
        {
          id: nextId.current++,
          sql: text,
          ok: false,
          error: "No pude contactar al servidor.",
          hint: "Revisa que la API /api/query esté disponible e inténtalo de nuevo.",
        },
      ]);
    } finally {
      setBusy(false);
      requestAnimationFrame(() => {
        if (feed.current) feed.current.scrollTop = feed.current.scrollHeight;
      });
    }
  };

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    execute(CHIPS[0].sql);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const reload = async () => {
      const res = await fetch("/api/consultas");
      const data = await res.json();
      if (Array.isArray(data.items)) {
        setSaved(data.items);
        onConsultasChanged(data.items);
      }
    };
    window.addEventListener("consulta:guardada", reload);
    return () => window.removeEventListener("consulta:guardada", reload);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex h-full flex-col">
      {/* barra de acciones */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rule bg-panel2 px-4 py-2">
        <div className="flex items-center gap-3">
          <span className="label text-paper">Terminal SQL</span>
          <span className="label text-mut">motor TypeScript sobre datasets en Postgres</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSaved((s) => !s)}
            className={`border px-3 py-1 label transition-colors ${
              showSaved ? "border-em text-em" : "border-rule text-mut hover:border-em hover:text-em"
            }`}
          >
            Guardadas ({saved.length})
          </button>
          <button
            onClick={() => setRuns([])}
            className="border border-rule px-3 py-1 label text-mut transition-colors hover:border-em hover:text-em"
          >
            Limpiar
          </button>
        </div>
      </div>

      {showSaved && (
        <div className="border-b border-rule bg-panel2 px-4 py-3">
          <div className="label text-mut">Consultas persistidas en la tabla consulta</div>
          <ul className="mt-2 flex flex-col gap-1">
            {saved.map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => {
                    execute(c.sql);
                    setShowSaved(false);
                  }}
                  className="group flex w-full items-baseline gap-3 border border-rule/60 px-3 py-2 text-left transition-colors hover:border-em"
                >
                  <span className="text-xs font-semibold text-paper group-hover:text-em">{c.titulo}</span>
                  <span className="truncate font-mono text-[10px] text-mut">{c.sql}</span>
                  <span className="ml-auto shrink-0 label text-mut">{c.origen}</span>
                </button>
              </li>
            ))}
            {saved.length === 0 && <li className="py-3 text-xs text-mut">Aún no hay consultas guardadas.</li>}
          </ul>
        </div>
      )}

      {/* chips */}
      <div className="flex gap-2 overflow-x-auto border-b border-rule bg-panel px-4 py-2">
        {CHIPS.map((c) => (
          <button
            key={c.label}
            onClick={() => execute(c.sql)}
            className="shrink-0 border border-rule px-3 py-1.5 label text-mut transition-colors hover:border-em hover:bg-em/10 hover:text-em"
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* salida */}
      <div ref={feed} className="flex-1 space-y-4 overflow-y-auto bg-ink px-4 py-4">
        <div className="flex items-start gap-3 font-mono text-xs text-mut">
          <span className="text-em">mfc ›</span>
          <span>
            Motor listo. {datasets.length} tablas cargadas. Escribe SQL, elige un chip o pulsa ↑ para repetir la última
            consulta.
          </span>
        </div>

        {runs.map((run) => (
          <div key={run.id} className="space-y-2">
            <div className="flex items-start gap-2 font-mono text-xs leading-relaxed text-em">
              <span className="shrink-0 text-rule2">›</span>
              <span className="break-all">{run.sql}</span>
            </div>
            <ResultBlock run={run} />
          </div>
        ))}

        {busy && (
          <div className="flex items-center gap-2 font-mono text-xs text-mut">
            <span className="text-amber">ejecutando</span>
            <span className="caret inline-block h-3 w-2 bg-em" />
          </div>
        )}
      </div>

      {/* entrada */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          execute(sql);
        }}
        className="flex items-center gap-3 border-t border-rule bg-panel2 px-4 py-3"
      >
        <span className="shrink-0 font-mono text-xs text-em">mfc:~$</span>
        <input
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          spellCheck={false}
          autoComplete="off"
          placeholder="SELECT nombre_aseguradora, participacion_pct FROM 'vida.aseguradoras' LIMIT 5;"
          className="min-w-0 flex-1 bg-transparent font-mono text-xs text-paper outline-none placeholder:text-mut/70"
        />
        <button
          type="submit"
          disabled={busy || !sql.trim()}
          className="shrink-0 bg-em px-4 py-2 label text-ink transition-colors hover:bg-[#02e2a4] disabled:cursor-not-allowed disabled:bg-rule2 disabled:text-mut"
        >
          {busy ? "…" : "Ejecutar ▸"}
        </button>
      </form>
    </div>
  );
}

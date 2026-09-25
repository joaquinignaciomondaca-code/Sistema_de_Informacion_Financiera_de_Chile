"use client";

import { useState } from "react";
import type { DatasetDetail } from "@/lib/types";
import { fmtCell, fmtDuration, fmtNum, freshnessLabel, relTime } from "@/lib/format";

type Props = {
  detail: DatasetDetail | null;
  loading: boolean;
  onClose: () => void;
  onRunSql: (sql: string) => void;
  onOpenContract: () => void;
};

export function Inspector({ detail, loading, onClose, onRunSql, onOpenContract }: Props) {
  const [tab, setTab] = useState<"schema" | "quality" | "lineage" | "sample">("schema");

  if (loading) {
    return (
      <aside className="panel flex w-[360px] shrink-0 flex-col border-l p-3 text-[11.5px] text-[var(--text-mute)]">
        Cargando ficha del dataset…
      </aside>
    );
  }
  if (!detail) return null;

  const d = detail.dataset;
  const freshState = d.freshnessHours === null ? "unknown" : d.freshnessHours <= d.freshnessSloHours ? "ok" : d.freshnessHours <= d.freshnessSloHours * 1.5 ? "warn" : "breach";
  const failed = detail.checks.filter((c) => !c.passed);

  return (
    <aside className="panel flex h-full w-[380px] shrink-0 flex-col border-l" style={{ background: "var(--bg-panel)" }}>
      <header className="border-b border-[var(--border)] p-3" style={{ background: "var(--bg-raised)" }}>
        <div className="flex items-start gap-2">
          <div className="min-w-0 flex-1">
            <div className="mono truncate text-[12.5px] font-bold" style={{ color: "var(--accent)" }}>
              {d.name}
            </div>
            <div className="mono mt-0.5 truncate text-[10px] text-[var(--text-mute)]">{d.physical}</div>
          </div>
          <button className="btn btn-ghost !px-1.5" onClick={onClose} aria-label="Cerrar ficha">
            ✕
          </button>
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-[var(--text-dim)]">{d.description}</p>
        <div className="mt-2 flex flex-wrap gap-1">
          <span className="tag">{d.layer}</span>
          <span className="tag">v{d.schemaVersion}</span>
          <span className="tag" style={{ color: d.accessPolicy === "public" ? "var(--ok)" : "var(--text-dim)" }}>
            {d.accessPolicy}
          </span>
          {(d.tags || "").split(",").filter(Boolean).map((t) => (
            <span key={t} className="tag">
              {t}
            </span>
          ))}
        </div>
        <div className="mt-2 flex gap-1.5">
          <button className="btn focus-ring" onClick={() => onRunSql(`SELECT * FROM ${d.physical} LIMIT 50;`)}>
            Preview
          </button>
          <button className="btn focus-ring" onClick={() => onOpenContract()}>
            Contrato
          </button>
          <button
            className="btn focus-ring"
            onClick={() => navigator.clipboard?.writeText(`SELECT * FROM ${d.physical} LIMIT 100;`)}
          >
            Copiar SQL
          </button>
        </div>
      </header>

      <div className="grid grid-cols-2 gap-px border-b border-[var(--border)]" style={{ background: "var(--border)" }}>
        <Stat label="Filas medidas" value={fmtNum(d.rowCount)} />
        <Stat label="Tamaño" value={`${fmtNum(Number(d.sizeMb), 2)} MB`} />
        <Stat
          label="Frescura vs SLO"
          value={`${freshnessLabel(d.freshnessHours)} / ${Math.round(d.freshnessSloHours / 24)} d`}
          tone={freshState === "ok" ? "ok" : freshState === "warn" ? "warn" : "bad"}
        />
        <Stat
          label="Calidad"
          value={detail.checks.length ? `${detail.checks.length - failed.length}/${detail.checks.length}` : "—"}
          tone={failed.length === 0 ? "ok" : "warn"}
        />
      </div>

      <nav className="flex gap-1 border-b border-[var(--border)] px-2 py-1.5">
        {(
          [
            ["schema", "Esquema"],
            ["quality", `Calidad${failed.length ? ` (${failed.length})` : ""}`],
            ["lineage", "Linaje"],
            ["sample", "Muestra"],
          ] as const
        ).map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} className={`chip ${tab === id ? "chip-active" : ""}`}>
            {label}
          </button>
        ))}
      </nav>

      <div className="min-h-0 flex-1 overflow-y-auto p-2 text-[11px]">
        {tab === "schema" && (
          <table className="w-full border-collapse">
            <tbody>
              {detail.columns.map((c) => (
                <tr key={c.id} className="align-top hover:bg-[var(--bg-hover)]">
                  <td className="w-[38%] py-1 pr-1">
                    <span className="mono text-[10.5px]" style={{ color: c.isPk ? "var(--accent)" : "var(--text)" }}>
                      {c.name}
                    </span>
                    {c.isPk && <span className="mono ml-1 text-[9px] text-[var(--accent)]">PK</span>}
                    {!c.nullable && <span className="mono ml-1 text-[9px] text-[var(--text-mute)]">NN</span>}
                    <div className="mono text-[9.5px] text-[var(--text-mute)]">
                      {c.dataType}
                      {c.unit ? ` · ${c.unit}` : ""}
                      {c.masking !== "none" ? ` · ${c.masking}` : ""}
                    </div>
                  </td>
                  <td className="py-1 text-[10.5px] leading-snug text-[var(--text-dim)]">{c.description || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === "quality" && (
          <ul className="flex flex-col gap-1.5">
            {detail.checks.map((c) => (
              <li key={c.id} className="rounded-md border p-2" style={{ borderColor: c.passed ? "var(--border)" : "var(--bad)" }}>
                <div className="flex items-center gap-1.5">
                  <span className={`dot ${c.passed ? "dot-ok" : "dot-bad"}`} />
                  <span className="mono text-[10.5px]">{c.kind}</span>
                  <span className="tag ml-auto">{c.severity}</span>
                </div>
                <div className="mono mt-1 break-words text-[10px] text-[var(--text-mute)]">{c.expression}</div>
                <div className="mt-1 text-[10px] text-[var(--text-dim)]">
                  observado <span className="mono">{fmtNum(c.observedValue as number, 3)}</span>
                  {c.threshold !== null && (
                    <>
                      {" "}
                      umbral <span className="mono">{fmtNum(c.threshold as number, 3)}</span>
                    </>
                  )}{" "}
                  · {relTime(c.ranAt)}
                </div>
              </li>
            ))}
            <li className="mt-1 rounded-md border border-dashed p-2 text-[10px] leading-relaxed text-[var(--text-mute)]">
              Los checks corren en el pipeline de ingest (post-run) y se publican aquí; la UI nunca recalcula la calidad, sólo la muestra.
            </li>
          </ul>
        )}

        {tab === "lineage" && (
          <div className="flex flex-col gap-3">
            <section>
              <h4 className="mb-1 text-[10px] font-bold tracking-wide text-[var(--text-mute)] uppercase">Junta hacia (n:1)</h4>
              {detail.outbound.length === 0 && <div className="text-[10.5px] text-[var(--text-mute)]">Sin claves salientes.</div>}
              {detail.outbound.map((r) => (
                <div key={r.id} className="mono mb-1 flex items-center gap-1 text-[10.5px]">
                  <span style={{ color: "var(--accent)" }}>{r.fromColumn}</span>
                  <span className="text-[var(--text-mute)]">→</span>
                  <span className="truncate text-[var(--text-dim)]">{r.target}</span>
                  <span className="ml-auto shrink-0 text-[9.5px] text-[var(--text-mute)]">{r.relationType}</span>
                </div>
              ))}
            </section>
            <section>
              <h4 className="mb-1 text-[10px] font-bold tracking-wide text-[var(--text-mute)] uppercase">Consumido por</h4>
              {detail.inbound.length === 0 && <div className="text-[10.5px] text-[var(--text-mute)]">Sin dependientes registrados.</div>}
              {detail.inbound.map((r) => (
                <div key={r.id} className="mono mb-1 truncate text-[10.5px] text-[var(--text-dim)]">
                  <span style={{ color: "var(--warn)" }}>{r.origin}</span> · {r.toColumn}
                </div>
              ))}
            </section>
            <section>
              <h4 className="mb-1 text-[10px] font-bold tracking-wide text-[var(--text-mute)] uppercase">Run ledger</h4>
              <ul className="flex flex-col gap-1">
                {detail.runs.map((r) => (
                  <li key={r.id} className="rounded-md border p-1.5">
                    <div className="flex items-center gap-1.5 text-[10px]">
                      <span className={`dot ${r.status === "success" ? "dot-ok" : r.status === "failed" ? "dot-bad" : "dot-warn"}`} />
                      <span className="mono">{r.status}</span>
                      <span className="mono ml-auto text-[var(--text-mute)]">{relTime(r.startedAt)}</span>
                    </div>
                    <div className="mono mt-0.5 text-[9.5px] text-[var(--text-mute)]">
                      in {fmtNum(r.rowsIn)} → out {fmtNum(r.rowsOut)} · drop {fmtNum(r.rowsDropped)} · {fmtDuration(r.durationMs)} · wm{" "}
                      {r.watermark ?? "—"} · {r.commitSha ? `git:${r.commitSha}` : "sin sha"}
                    </div>
                    {r.errorMessage && <div className="mono mt-0.5 text-[9.5px]" style={{ color: "var(--bad)" }}>{r.errorMessage}</div>}
                  </li>
                ))}
              </ul>
            </section>
            <section className="rounded-md border p-2 text-[10px] leading-relaxed text-[var(--text-mute)]">
              <div>
                owner técnico: <span className="mono text-[var(--text-dim)]">{d.owner}</span>
              </div>
              <div>
                modelo: <span className="mono text-[var(--text-dim)]">{d.modelPath ?? "n/d"}</span>
              </div>
              <div>
                contacto: <span className="mono text-[var(--text-dim)]">{detail.domain?.ownerContact ?? "—"}</span>
              </div>
              {detail.source && (
                <div className="mt-1">
                  fuente: <span className="text-[var(--text-dim)]">{detail.source.code}</span> · {detail.source.issuer}
                  {detail.source.url ? " ·" : ""}{" "}
                  {detail.source.url && (
                    <a href={detail.source.url} target="_blank" rel="noreferrer" className="mono">
                      enlace
                    </a>
                  )}
                </div>
              )}
            </section>
          </div>
        )}

        {tab === "sample" && (
          <div className="overflow-x-auto">
            {detail.preview.error ? (
              <div className="text-[10.5px]" style={{ color: "var(--bad)" }}>
                {detail.preview.error}
              </div>
            ) : (
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    {detail.preview.columns.map((c) => (
                      <th key={c} className="th !text-[9.5px]">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {detail.preview.rows.map((r, i) => (
                    <tr key={i}>
                      {detail.preview.columns.map((c) => (
                        <td key={c} className="td mono !px-1.5 !py-0.5 !text-[9.5px]">
                          {fmtCell(c, r[c])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <div className="mt-2 text-[10px] leading-relaxed text-[var(--text-mute)]">
              8 filas leídas por el servidor con <span className="mono">LIMIT</span> fijo. El navegador nunca recibe la tabla completa.
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "ok" | "warn" | "bad" }) {
  const c = tone === "ok" ? "var(--ok)" : tone === "warn" ? "var(--warn)" : tone === "bad" ? "var(--bad)" : "var(--text)";
  return (
    <div className="px-2.5 py-1.5" style={{ background: "var(--bg-panel)" }}>
      <div className="text-[9.5px] tracking-wide text-[var(--text-mute)] uppercase">{label}</div>
      <div className="mono text-[11.5px]" style={{ color: c }}>
        {value}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { CatalogTree, DatasetNode } from "@/lib/types";
import { fmtNum, freshnessLabel } from "@/lib/format";

type Props = {
  tree: CatalogTree | null;
  selectedId: number | null;
  onSelect: (id: number) => void;
  onPreview: (d: DatasetNode) => void;
};

const dotFor = (f: string) => (f === "ok" ? "dot-ok" : f === "warn" ? "dot-warn" : f === "breach" ? "dot-bad" : "dot-unknown");

function Row({
  d,
  selected,
  onSelect,
  onPreview,
  depth,
}: {
  d: DatasetNode;
  selected: boolean;
  onSelect: (id: number) => void;
  onPreview: (d: DatasetNode) => void;
  depth: number;
}) {
  return (
    <div
      role="treeitem"
      aria-selected={selected}
      tabIndex={-1}
      onClick={() => onSelect(d.id)}
      className="group flex h-[27px] cursor-pointer items-center gap-1.5 border-l-2 pr-2 text-[11.5px]"
      style={{
        paddingLeft: 8 + depth * 12,
        borderLeftColor: selected ? "var(--accent)" : "transparent",
        background: selected ? "var(--bg-select)" : undefined,
      }}
    >
      <span className={`dot ${dotFor(d.freshness)}`} title={`Frescura ${freshnessLabel(d.freshnessHours)} · SLO ${d.sloHours} h`} />
      <span className="mono truncate" style={{ color: selected ? "var(--accent)" : "var(--text)" }}>
        {d.name}
      </span>
      <span className="tag shrink-0">{d.layer}</span>
      <span className="mono ml-auto shrink-0 text-[10px] text-[var(--text-mute)] group-hover:hidden">
        {fmtNum(d.rows)}
      </span>
      <span className="hidden shrink-0 items-center gap-1 group-hover:flex">
        <button
          className="btn btn-ghost !px-1.5 !py-0 !text-[10px]"
          title="Ejecificar SELECT de muestra"
          onClick={(e) => {
            e.stopPropagation();
            onPreview(d);
          }}
        >
          Preview
        </button>
        <button
          className="btn btn-ghost !px-1.5 !py-0 !text-[10px]"
          title="Copiar FROM mart.tabla"
          onClick={(e) => {
            e.stopPropagation();
            navigator.clipboard?.writeText(`FROM ${d.physical}`);
          }}
        >
          FROM
        </button>
      </span>
    </div>
  );
}

export function Explorer({ tree, selectedId, onSelect, onPreview }: Props) {
  const [q, setQ] = useState("");
  const [openDomains, setOpenDomains] = useState<Set<string>>(new Set());
  const [openSources, setOpenSources] = useState<Set<number>>(new Set());
  const rootRef = useRef<HTMLDivElement>(null);
  const initialised = useRef(false);

  const filtered = useMemo(() => {
    if (!tree) return null;
    const needle = q.trim().toLowerCase();
    if (!needle) return tree;
    return {
      ...tree,
      domains: tree.domains
        .map((dom) => ({
          ...dom,
          sources: dom.sources
            .map((s) => ({
              ...s,
              datasets: s.datasets.filter((d) => match(d.name, needle) || match(s.code, needle) || match(dom.name, needle)),
            }))
            .filter((s) => s.datasets.length > 0),
          shared: dom.shared.filter((d) => match(d.name, needle) || match(dom.name, needle)),
        }))
        .filter((dom) => dom.sources.length > 0 || dom.shared.length > 0),
    };
  }, [tree, q]);

  useEffect(() => {
    if (!tree || initialised.current) return;
    initialised.current = true;
    setOpenDomains(new Set(tree.domains.map((d) => d.slug)));
    setOpenSources(new Set(tree.domains.flatMap((d) => d.sources.map((s) => s.id))));
  }, [tree]);

  const flat = useMemo(() => {
    const out: DatasetNode[] = [];
    for (const dom of filtered?.domains ?? []) {
      for (const s of dom.sources) if (openDomains.has(dom.slug) && openSources.has(s.id)) out.push(...s.datasets);
      if (openDomains.has(dom.slug)) out.push(...dom.shared);
    }
    return out;
  }, [filtered, openDomains, openSources]);

  const move = (delta: number) => {
    if (!flat.length) return;
    const idx = flat.findIndex((d) => d.id === selectedId);
    const next = flat[Math.min(flat.length - 1, Math.max(0, idx + delta))] ?? flat[0];
    onSelect(next.id);
    rootRef.current?.querySelector(`[data-ds="${next.id}"]`)?.scrollIntoView({ block: "nearest" });
  };

  const searching = q.trim().length > 0;

  return (
    <div className="flex h-full flex-col overflow-hidden" style={{ background: "var(--bg-sidebar)" }}>
      <div className="border-b border-[var(--border)] p-2.5" style={{ background: "var(--bg-raised)" }}>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[10px] font-bold tracking-[0.9px] text-[var(--accent)] uppercase">Catálogo financiero CL</span>
          <span className="mono text-[9.5px] text-[var(--text-mute)]">{tree ? `${tree.datasetCount} ds` : "…"}</span>
        </div>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              move(1);
            }
            if (e.key === "ArrowUp") {
              e.preventDefault();
              move(-1);
            }
            if (e.key === "Enter" && selectedId) {
              const d = flat.find((x) => x.id === selectedId);
              if (d) onPreview(d);
            }
            if (e.key === "Escape") setQ("");
          }}
          placeholder="Filtrar dataset, circular o dominio…"
          aria-label="Filtrar catálogo"
          className="inset focus-ring w-full rounded-md px-2.5 py-1.5 text-[11.5px] outline-none"
        />
      </div>

      <div ref={rootRef} role="tree" className="flex-1 overflow-y-auto py-1" onKeyDown={(e) => e.key === "Escape" && setQ("")}>
        {!tree && <div className="p-3 text-[11px] text-[var(--text-mute)]">Cargando catálogo…</div>}
        {filtered?.domains.length === 0 && (
          <div className="p-3 text-[11px] text-[var(--text-mute)]">Sin coincidencias para “{q}”.</div>
        )}
        {filtered?.domains.map((dom) => {
          const open = searching || openDomains.has(dom.slug);
          return (
            <div key={dom.slug} className="mb-1">
              <button
                onClick={() => setOpenDomains((s) => toggle(s, dom.slug))}
                className="flex w-full items-center gap-1.5 px-2 py-1.5 text-left"
                style={{ background: "var(--bg-raised)" }}
              >
                <Caret open={open} />
                <span className="truncate text-[10.5px] font-bold tracking-[0.4px] uppercase">{dom.name}</span>
                {dom.stats.breaches > 0 && (
                  <span className="tag shrink-0" style={{ color: "var(--bad)", borderColor: "var(--bad)" }}>
                    {dom.stats.breaches} SLO
                  </span>
                )}
                <span className="tag shrink-0 ml-auto">{dom.stats.datasets} ds</span>
              </button>
              {open && (
                <div>
                  <div className="px-2 py-1 text-[10px] leading-snug text-[var(--text-mute)]">
                    {dom.regulator !== "—" && <span className="mono">{dom.regulator} · </span>}
                    {dom.description}
                  </div>
                  {dom.sources.map((s) => {
                    const sOpen = searching || openSources.has(s.id) || openDomains.has(dom.slug);
                    return (
                      <div key={s.id}>
                        <div
                          onClick={() => setOpenSources((v) => toggle(v, s.id))}
                          className="flex cursor-pointer items-center gap-1.5 py-[3px] pr-2 text-[11px]"
                          style={{ paddingLeft: 20 }}
                        >
                          <Caret open={sOpen} />
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-mute)" strokeWidth="2">
                            <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                          </svg>
                          <span className="truncate text-[var(--text-dim)]">{s.code}</span>
                          {s.mandatory ? (
                            <span className="tag ml-auto shrink-0" title="Obligatorio en el reporte">
                              mand.
                            </span>
                          ) : (
                            <span className="tag ml-auto shrink-0" title="Voluntario / roadmap">
                              roadmap
                            </span>
                          )}
                        </div>
                        {sOpen && s.datasets.map((d) => (
                          <div key={d.id} data-ds={d.id}>
                            <Row d={d} depth={2} selected={selectedId === d.id} onSelect={onSelect} onPreview={onPreview} />
                          </div>
                        ))}
                      </div>
                    );
                  })}
                  {dom.shared.map((d) => (
                    <div key={d.id} data-ds={d.id}>
                      <Row d={d} depth={1} selected={selectedId === d.id} onSelect={onSelect} onPreview={onPreview} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {tree && (
        <div className="border-t border-[var(--border)] px-2.5 py-2 text-[10px] leading-relaxed text-[var(--text-mute)]">
          <div className="mono">
            {tree.datasetCount} datasets · {fmtNum(tree.rowCount)} filas · {tree.failedChecks} checks caídos
          </div>
          <div className="mt-0.5">
            Árbol generado desde <span className="mono text-[var(--text-dim)]">catalog.datasets</span>; nada está hardcodeado en la UI.
          </div>
        </div>
      )}
    </div>
  );
}

function Caret({ open }: { open: boolean }) {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 16 16"
      fill="currentColor"
      className="shrink-0 text-[var(--text-mute)] transition-transform"
      style={{ transform: open ? "rotate(90deg)" : undefined }}
    >
      <path d="M6 4l4 4-4 4z" />
    </svg>
  );
}

function toggle<T>(set: Set<T>, value: T): Set<T> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

function match(haystack: string, needle: string) {
  return haystack.toLowerCase().includes(needle);
}

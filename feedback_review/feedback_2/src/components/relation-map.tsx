"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Graph, GraphNode } from "@/lib/types";

type Props = {
  graph: Graph | null;
  selectedId: number | null;
  onSelect: (id: number) => void;
  kindLabel: string;
};

const NODE_W = 178;
const NODE_H = 46;
const RANK: Record<string, number> = { dim: 0, raw: 0, staging: 1, fact: 1, mart: 1, view: 2 };

const color = (kind: string) =>
  kind === "vida"
    ? "var(--ok)"
    : kind === "generales"
      ? "var(--info)"
      : kind === "ffmm"
        ? "var(--warn)"
        : kind === "fi"
          ? "var(--bad)"
          : "var(--text-mute)";

export function RelationMap({ graph, selectedId, onSelect, kindLabel }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 900, h: 380 });
  const [view, setView] = useState({ k: 1, x: 0, y: 0 });
  const [hover, setHover] = useState<number | null>(null);
  const drag = useRef<{ x: number; y: number; ox: number; oy: number } | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  const layout = useMemo(() => {
    if (!graph) return null;
    const byRank = new Map<number, GraphNode[]>();
    for (const n of graph.nodes) {
      const r = RANK[n.layer] ?? 1;
      byRank.set(r, [...(byRank.get(r) ?? []), n]);
    }
    const ranks = [...byRank.keys()].sort((a, b) => a - b);
    const maxRows = Math.max(...ranks.map((r) => (byRank.get(r) ?? []).length), 1);
    const colGap = 118;
    const rowGap = 16;
    const totalW = ranks.length * NODE_W + (ranks.length - 1) * colGap;
    const totalH = maxRows * (NODE_H + rowGap);
    const pos = new Map<number, { x: number; y: number; node: GraphNode }>();
    ranks.forEach((r, ri) => {
      const list = (byRank.get(r) ?? []).slice().sort((a, b) => a.domainKind.localeCompare(b.domainKind) || a.name.localeCompare(b.name));
      const colH = list.length * NODE_H + (list.length - 1) * rowGap;
      const y0 = (totalH - colH) / 2;
      list.forEach((n, i) => {
        pos.set(n.id, { x: ri * (NODE_W + colGap), y: y0 + i * (NODE_H + rowGap), node: n });
      });
    });
    return { pos, totalW, totalH, offsetX: 0, offsetY: 0 };
  }, [graph]);

  useEffect(() => {
    if (!layout) return;
    const pad = 46;
    const k = Math.min(1, (size.w - pad * 2) / Math.max(layout.totalW, 1), (size.h - pad * 2) / Math.max(layout.totalH, 1));
    setView({
      k: Math.max(0.35, k),
      x: (size.w - layout.totalW * k) / 2,
      y: (size.h - layout.totalH * k) / 2,
    });
  }, [layout, size.w, size.h]);

  const related = useMemo(() => {
    const focus = hover ?? selectedId;
    if (!graph || focus === null) return null;
    const ids = new Set<number>([focus]);
    const edges = new Set<number>();
    for (const e of graph.edges) {
      if (e.from === focus || e.to === focus) {
        ids.add(e.from);
        ids.add(e.to);
        edges.add(e.id);
      }
    }
    return { ids, edges };
  }, [graph, hover, selectedId]);

  const zoom = (factor: number) => setView((v) => ({ ...v, k: Math.min(2.4, Math.max(0.3, v.k * factor)) }));

  return (
    <div ref={wrapRef} className="grid-bg relative h-full w-full overflow-hidden" style={{ background: "var(--bg-panel)" }}>
      {!graph && (
        <div className="absolute inset-0 grid place-items-center text-[11.5px] text-[var(--text-mute)]">
          Calculando mapa relacional…
        </div>
      )}
      {graph && layout && (
        <svg
          className="h-full w-full"
          style={{ cursor: drag.current ? "grabbing" : "grab", touchAction: "none" }}
          onWheel={(e) => {
            const factor = e.deltaY < 0 ? 1.09 : 0.92;
            zoom(factor);
          }}
          onPointerDown={(e) => {
            (e.target as Element).setPointerCapture?.(e.pointerId);
            drag.current = { x: e.clientX, y: e.clientY, ox: view.x, oy: view.y };
          }}
          onPointerMove={(e) => {
            if (!drag.current) return;
            setView((v) => ({ ...v, x: drag.current!.ox + (e.clientX - drag.current!.x), y: drag.current!.oy + (e.clientY - drag.current!.y) }));
          }}
          onPointerUp={() => (drag.current = null)}
          onPointerLeave={() => (drag.current = null)}
        >
          <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
            {graph.edges.map((e) => {
              const a = layout.pos.get(e.from);
              const b = layout.pos.get(e.to);
              if (!a || !b) return null;
              const x1 = a.x;
              const y1 = a.y + NODE_H / 2;
              const x2 = b.x + NODE_W;
              const y2 = b.y + NODE_H / 2;
              const mx = (x1 + x2) / 2;
              const on = !related || related.edges.has(e.id);
              return (
                <g key={e.id} opacity={on ? 1 : 0.14}>
                  <path
                    d={`M${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
                    fill="none"
                    stroke={e.type === "view_union" ? "var(--warn)" : "var(--border-strong)"}
                    strokeWidth={1.2}
                    strokeDasharray={e.type === "view_union" ? "4 3" : undefined}
                  />
                  <circle cx={x2} cy={y2} r={2.6} fill="var(--border-strong)" />
                  <text x={mx} y={(y1 + y2) / 2 - 4} fontSize="8" textAnchor="middle" fill="var(--text-mute)" className="mono">
                    {e.fromColumn}
                  </text>
                </g>
              );
            })}
            {graph.nodes.map((n) => {
              const p = layout.pos.get(n.id);
              if (!p) return null;
              const on = !related || related.ids.has(n.id);
              const isSel = selectedId === n.id;
              return (
                <g
                  key={n.id}
                  transform={`translate(${p.x} ${p.y})`}
                  opacity={on ? 1 : 0.28}
                  onMouseEnter={() => setHover(n.id)}
                  onMouseLeave={() => setHover(null)}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelect(n.id);
                  }}
                  style={{ cursor: "pointer" }}
                >
                  <title>{`${n.domain} · ${n.grain}\n${n.columns} columnas · calidad ${n.quality}%`}</title>
                  <rect
                    width={NODE_W}
                    height={NODE_H}
                    rx={7}
                    fill="var(--bg-raised)"
                    stroke={isSel ? "var(--accent)" : "var(--border)"}
                    strokeWidth={isSel ? 1.8 : 1}
                  />
                  <rect width={3.5} height={NODE_H} rx={2} fill={color(n.domainKind)} />
                  <text x={12} y={18} fontSize="11" fill="var(--text)" className="mono">
                    {n.name.length > 24 ? `${n.name.slice(0, 23)}…` : n.name}
                  </text>
                  <text x={12} y={32} fontSize="8.5" fill="var(--text-mute)" className="mono">
                    {n.layer} · {n.columns} col · {n.rows.toLocaleString("es-CL")} filas
                  </text>
                  <rect x={12} y={37} width={NODE_W - 24} height={3} rx={1.5} fill="var(--border)" />
                  <rect
                    x={12}
                    y={37}
                    width={((NODE_W - 24) * n.quality) / 100}
                    height={3}
                    rx={1.5}
                    fill={n.quality > 85 ? "var(--ok)" : n.quality > 60 ? "var(--warn)" : "var(--bad)"}
                  />
                  <circle
                    cx={NODE_W - 11}
                    cy={15}
                    r={4}
                    fill={n.freshness === "ok" ? "var(--ok)" : n.freshness === "warn" ? "var(--warn)" : n.freshness === "breach" ? "var(--bad)" : "var(--text-mute)"}
                  />
                </g>
              );
            })}
          </g>
        </svg>
      )}

      <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap items-center gap-2 text-[10px]">
        <span className="tag" style={{ background: "var(--bg-raised)" }}>
          {kindLabel} · {graph?.nodes.length ?? 0} nodos · {graph?.edges.length ?? 0} aristas
        </span>
        <span className="tag" style={{ background: "var(--bg-raised)" }}>
          layout por capa: dim → fact → view
        </span>
        <span className="tag" style={{ background: "var(--bg-raised)" }}>
          aristas derivadas de metadata de columnas
        </span>
      </div>

      <div className="absolute bottom-3 right-3 flex flex-col gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--bg-raised)] p-1.5">
        <button className="btn btn-ghost !h-[26px] !w-[26px] !p-0" onClick={() => zoom(1.25)} title="Acercar (+)" aria-label="Acercar">
          +
        </button>
        <button className="btn btn-ghost !h-[26px] !w-[26px] !p-0" onClick={() => zoom(0.8)} title="Alejar (−)" aria-label="Alejar">
          −
        </button>
        <button
          className="btn btn-ghost !h-[26px] !w-[26px] !p-0"
          title="Encuadrar"
          aria-label="Encuadrar"
          onClick={() => {
            if (!layout) return;
            const k = Math.min(1, (size.w - 92) / Math.max(layout.totalW, 1), (size.h - 92) / Math.max(layout.totalH, 1));
            setView({ k: Math.max(0.35, k), x: (size.w - layout.totalW * k) / 2, y: (size.h - layout.totalH * k) / 2 });
          }}
        >
          ⟲
        </button>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { EDGES, INDUSTRIAS, type Dataset, type IndustriaId } from "@/lib/data";
import type { PersistState, SavedQuery } from "@/lib/store";
import { Terminal } from "./Terminal";

type Tab = "erd" | "sql" | "diccionario";

const NODE_W = 250;
const NODE_H = 138;
const GAP_X = 88;
const GAP_Y = 64;

function layout(nodes: Dataset[]) {
  const cols = Math.min(3, Math.max(1, nodes.length));
  return nodes.map((n, i) => ({
    dataset: n,
    x: 40 + (i % cols) * (NODE_W + GAP_X),
    y: 40 + Math.floor(i / cols) * (NODE_H + GAP_Y),
  }));
}

function ErdPanel({
  datasets,
  selected,
  onSelect,
  filter,
  setFilter,
}: {
  datasets: Dataset[];
  selected: Dataset | null;
  onSelect: (d: Dataset | null) => void;
  filter: IndustriaId | "todos";
  setFilter: (f: IndustriaId | "todos") => void;
}) {
  const [zoom, setZoom] = useState(1);

  const visible = useMemo(
    () => (filter === "todos" ? datasets : datasets.filter((d) => d.industria === filter)),
    [datasets, filter],
  );
  const positioned = useMemo(() => layout(visible), [visible]);
  const cols = Math.min(3, Math.max(1, visible.length));
  const rows = Math.ceil(visible.length / cols) || 1;
  const vw = 40 * 2 + cols * NODE_W + (cols - 1) * GAP_X;
  const vh = 40 * 2 + rows * NODE_H + (rows - 1) * GAP_Y;

  const pos = new Map(positioned.map((p) => [p.dataset.slug, p]));
  const edges = EDGES.filter((e) => pos.has(e.from) && pos.has(e.to));

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      if (e.key === "+" || e.key === "=") setZoom((z) => Math.min(2, z + 0.15));
      if (e.key === "-") setZoom((z) => Math.max(0.5, z - 0.15));
      if (e.key === "0") setZoom(1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="relative h-[560px] overflow-hidden bg-ink">
      <div className="rule-grid pointer-events-none absolute inset-0 opacity-60" />

      {/* encabezado / filtros */}
      <div className="absolute left-4 top-4 z-10 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-1 border border-rule bg-panel/90 p-1 backdrop-blur-sm">
        <span className="px-2 label text-mut">Filtrar</span>
        {[{ id: "todos" as const, label: "Todos" }, ...INDUSTRIAS.map((i) => ({ id: i.id, label: i.corto }))].map(
          (f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id as IndustriaId | "todos")}
              className={`px-3 py-1.5 label transition-colors ${
                filter === f.id ? "bg-em text-ink" : "text-mut hover:text-paper"
              }`}
            >
              {f.label}
            </button>
          ),
        )}
      </div>

      <div className="absolute left-4 top-16 z-10 font-mono text-xs text-em">
        {selected ? `${INDUSTRIAS.find((i) => i.id === selected.industria)?.label} › ${selected.nombre}` : `${visible.length} tablas en el grafo · clic para ver el esquema`}
      </div>

      <svg
        viewBox={`0 0 ${vw} ${vh}`}
        preserveAspectRatio="xMidYMid meet"
        className="h-full w-full"
        role="group"
        aria-label="Mapa relacional de los datasets"
      >
        <g
          style={{
            transform: `translate(${vw / 2}px, ${vh / 2}px) scale(${zoom}) translate(${-vw / 2}px, ${-vh / 2}px)`,
            transformOrigin: "0 0",
            transition: "transform 260ms cubic-bezier(.16,.84,.32,1)",
          }}
        >
          {edges.map((e) => {
            const a = pos.get(e.from)!;
            const b = pos.get(e.to)!;
            const x1 = a.x + NODE_W / 2;
            const y1 = a.y + NODE_H / 2;
            const x2 = b.x + NODE_W / 2;
            const y2 = b.y + NODE_H / 2;
            const mx = (x1 + x2) / 2;
            const my = (y1 + y2) / 2;
            const label = `${e.fromCol} ⇢ ${e.toCol}`;
            return (
              <g key={`${e.from}-${e.to}-${e.fromCol}`}>
                <path
                  d={`M${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
                  fill="none"
                  stroke="#2f3f41"
                  strokeWidth="1.5"
                  strokeDasharray={e.kind === "n:n" ? "5 4" : undefined}
                />
                <rect x={mx - label.length * 3.4} y={my - 9} width={label.length * 6.8} height="18" fill="#070b0c" stroke="#1f2a2c" />
                <text x={mx} y={my + 4} textAnchor="middle" fill="#7e8f8b" fontSize="10.5" fontFamily="IBM Plex Mono, monospace">
                  {label}
                </text>
              </g>
            );
          })}

          {positioned.map(({ dataset, x, y }) => {
            const isSelected = selected?.slug === dataset.slug;
            return (
              <g
                key={dataset.slug}
                transform={`translate(${x}, ${y})`}
                tabIndex={0}
                role="button"
                aria-label={`Tabla ${dataset.nombre}, ${dataset.filas.length} filas. Ver esquema.`}
                className="group cursor-pointer outline-none"
                onClick={() => onSelect(isSelected ? null : dataset)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelect(isSelected ? null : dataset);
                  }
                }}
              >
                <rect
                  width={NODE_W}
                  height={NODE_H}
                  fill="#0d1315"
                  strokeWidth={isSelected ? 2 : 1}
                  className={
                    isSelected
                      ? "stroke-em"
                      : "stroke-rule2 transition-colors group-hover:stroke-em group-focus-visible:stroke-em"
                  }
                />
                <rect width={NODE_W} height="30" fill={isSelected ? "rgba(0,208,154,0.16)" : "rgba(0,208,154,0.06)"} />
                <line x1="0" y1="30" x2={NODE_W} y2="30" stroke="#1f2a2c" />
                <text x="12" y="20" fill="#e6edea" fontSize="13" fontFamily="IBM Plex Mono, monospace" fontWeight="500">
                  {dataset.slug}
                </text>
                <text x={NODE_W - 12} y="20" textAnchor="end" fill={isSelected ? "#00d09a" : "#7e8f8b"} fontSize="10.5" fontFamily="IBM Plex Mono, monospace">
                  {dataset.filas.length} filas
                </text>
                {dataset.columnas.slice(0, 6).map((c, i) => (
                  <text key={c.name} x="12" y={50 + i * 15} fontSize="11" fontFamily="IBM Plex Mono, monospace" fill={c.pk ? "#f2a93b" : "#7e8f8b"}>
                    {c.pk ? "◆ " : "· "}
                    {c.name}
                    <tspan fill="#4d5c59"> {c.type}</tspan>
                  </text>
                ))}
                {dataset.columnas.length > 6 && (
                  <text x="12" y={50 + 6 * 15} fontSize="11" fontFamily="IBM Plex Mono, monospace" fill="#4d5c59">
                    +{dataset.columnas.length - 6} columnas
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* controles de zoom */}
      <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-px border border-rule bg-panel">
        {[
          { l: "+", fn: () => setZoom((z) => Math.min(2, z + 0.15)), aria: "Acercar" },
          { l: "−", fn: () => setZoom((z) => Math.max(0.5, z - 0.15)), aria: "Alejar" },
          { l: "⟲", fn: () => setZoom(1), aria: "Restablecer vista" },
        ].map((b) => (
          <button
            key={b.aria}
            onClick={b.fn}
            aria-label={b.aria}
            className="h-9 w-9 bg-panel2 font-mono text-sm text-paper transition-colors hover:bg-em hover:text-ink"
          >
            {b.l}
          </button>
        ))}
        <div className="bg-panel2 px-1 py-1 text-center font-mono text-[10px] text-mut tnum">{Math.round(zoom * 100)}%</div>
      </div>

      {/* leyenda */}
      <div className="absolute bottom-4 left-4 z-10 hidden border border-rule bg-panel/90 px-3 py-2 font-mono text-[10.5px] text-mut backdrop-blur-sm sm:block">
        <div className="mb-1 label text-mut">Leyenda</div>
        <div>◆ llave primaria</div>
        <div>── relación 1:n</div>
        <div>┄┄ relación n:n</div>
        <div className="mt-1 text-rule2">+ − 0 zoom · Tab navega</div>
      </div>

      {/* modal de esquema */}
      {selected && (
        <aside className="fade absolute right-4 top-4 z-20 w-[300px] border border-em bg-panel/95 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-rule px-4 py-3">
            <div>
              <div className="font-mono text-sm text-em">{selected.slug}</div>
              <div className="mt-1 label text-mut">{selected.circular}</div>
            </div>
            <button
              onClick={() => onSelect(null)}
              aria-label="Cerrar esquema"
              className="text-lg leading-none text-mut transition-colors hover:text-paper"
            >
              ×
            </button>
          </div>
          <div className="px-4 py-3 label text-mut">{selected.nombre}</div>
          <p className="px-4 pb-3 text-xs leading-relaxed text-mut">{selected.descripcion}</p>
          <div className="max-h-[260px] overflow-y-auto border-t border-rule">
            <table className="w-full font-mono text-[11px]">
              <tbody>
                {selected.columnas.map((c) => (
                  <tr key={c.name} className="border-b border-rule/60">
                    <td className="px-4 py-1.5 text-paper">
                      {c.pk && <span className="text-amber">◆ </span>}
                      {c.name}
                    </td>
                    <td className="px-2 py-1.5 text-right text-mut">{c.type}</td>
                    <td className="px-4 py-1.5 text-right text-rule2">{c.unit ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-rule px-4 py-2 font-mono text-[10.5px] text-mut">{selected.archivo}</div>
        </aside>
      )}
    </div>
  );
}

function Diccionario({ datasets }: { datasets: Dataset[] }) {
  return (
    <div className="h-[560px] overflow-y-auto bg-ink">
      <table className="w-full min-w-[900px] border-collapse text-sm">
        <thead className="sticky top-0 bg-panel2">
          <tr className="label text-em">
            <th className="border-b border-rule px-4 py-3 text-left font-normal">Tabla</th>
            <th className="border-b border-rule px-4 py-3 text-left font-normal">Industria</th>
            <th className="border-b border-rule px-4 py-3 text-left font-normal">Circular</th>
            <th className="border-b border-rule px-4 py-3 text-right font-normal">Cols</th>
            <th className="border-b border-rule px-4 py-3 text-right font-normal">Filas</th>
            <th className="border-b border-rule px-4 py-3 text-left font-normal">Archivo</th>
          </tr>
        </thead>
        <tbody className="font-mono text-xs tnum">
          {datasets.map((d) => (
            <tr key={d.slug} className="border-b border-rule transition-colors hover:bg-em/5">
              <td className="px-4 py-3">
                <div className="text-paper">{d.slug}</div>
                <div className="mt-1 max-w-md font-sans text-[11.5px] leading-snug text-mut">{d.descripcion}</div>
              </td>
              <td className="px-4 py-3 text-mut">{INDUSTRIAS.find((x) => x.id === d.industria)?.corto ?? d.industria}</td>
              <td className="px-4 py-3 text-mut">{d.circular}</td>
              <td className="px-4 py-3 text-right text-paper">{d.columnas.length}</td>
              <td className="px-4 py-3 text-right text-em">{d.filas.length}</td>
              <td className="px-4 py-3 text-[11px] text-rule2">{d.archivo}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Workspace({
  initialDatasets,
  initialConsultas,
  persist,
}: {
  initialDatasets: Dataset[];
  initialConsultas: SavedQuery[];
  persist: PersistState;
}) {
  const [tab, setTab] = useState<Tab>("erd");
  const [filter, setFilter] = useState<IndustriaId | "todos">("vida");
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const selected = initialDatasets.find((d) => d.slug === selectedSlug) ?? null;

  const filteredGroups = useMemo(() => {
    const q = query.trim().toLowerCase();
    return INDUSTRIAS.map((ind) => ({
      ind,
      items: initialDatasets.filter(
        (d) =>
          d.industria === ind.id &&
          (!q || d.slug.toLowerCase().includes(q) || d.nombre.toLowerCase().includes(q) || d.circular.toLowerCase().includes(q)),
      ),
    })).filter((g) => g.items.length > 0);
  }, [initialDatasets, query]);

  useEffect(() => {
    const onClick = (e: Event) => {
      const el = (e.target as HTMLElement).closest<HTMLElement>("[data-tab]");
      if (el?.dataset.tab) setTab(el.dataset.tab as Tab);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  const tabs: { id: Tab; label: string }[] = [
    { id: "erd", label: "Mapa relacional" },
    { id: "sql", label: "Terminal SQL" },
    { id: "diccionario", label: "Diccionario de datos" },
  ];

  return (
    <section id="workspace" className="scroll-mt-12 border-b border-rule bg-panel">
      {/* barra de pestañas */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rule bg-panel2 px-4 md:px-8">
        <div className="flex">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              aria-pressed={tab === t.id}
              className={`relative px-4 py-4 label transition-colors ${
                tab === t.id ? "text-em" : "text-mut hover:text-paper"
              }`}
            >
              {t.label}
              {tab === t.id && <span className="absolute inset-x-0 bottom-0 h-0.5 bg-em" />}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 label text-mut">
          <span>{initialDatasets.length} tablas</span>
          <span className="text-rule2">·</span>
          <span>{initialDatasets.reduce((a, d) => a + d.filas.length, 0)} filas</span>
          <span className="text-rule2">·</span>
          <span className={persist.ok ? "text-em" : "text-amber"}>
            {persist.ok ? "Postgres conectado" : "Modo memoria"}
          </span>
        </div>
      </div>

      <div className="grid lg:grid-cols-[300px_1fr]">
        {/* rail explorador */}
        <aside className="border-b border-rule bg-ink lg:border-b-0 lg:border-r">
          <div className="border-b border-rule px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="label text-em">Explorador</span>
              <span className="label text-mut">CMF / BCCh</span>
            </div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filtrar tabla o circular…"
              className="mt-3 w-full border border-rule bg-panel px-3 py-2 text-xs text-paper outline-none transition-colors placeholder:text-mut focus:border-em"
            />
          </div>

          <div className="max-h-[560px] overflow-y-auto">
            {filteredGroups.map(({ ind, items }) => (
              <div key={ind.id}>
                <div className="sticky top-0 z-10 flex items-center justify-between border-y border-rule bg-panel2 px-4 py-2">
                  <span className="text-[11.5px] font-semibold text-paper">{ind.label}</span>
                  <span className="label text-mut">{items.length}</span>
                </div>
                <div className="label px-4 py-1.5 text-rule2">{ind.norma}</div>
                {items.map((d) => {
                  const active = selectedSlug === d.slug;
                  return (
                    <button
                      key={d.slug}
                      onClick={() => {
                        setSelectedSlug(active ? null : d.slug);
                        setFilter(d.industria);
                        setTab("erd");
                      }}
                      className={`flex w-full items-center gap-2 border-l-2 px-4 py-2.5 text-left transition-colors ${
                        active ? "border-em bg-em/10" : "border-transparent hover:bg-em/5"
                      }`}
                    >
                      <span className={`font-mono text-[11.5px] ${active ? "text-em" : "text-paper/85"}`}>
                        {d.slug.split(".")[1]}
                      </span>
                      <span className="ml-auto font-mono text-[10.5px] text-mut tnum">{d.filas.length}</span>
                    </button>
                  );
                })}
              </div>
            ))}
            {filteredGroups.length === 0 && (
              <div className="px-4 py-8 text-xs leading-relaxed text-mut">
                Ninguna tabla coincide con «{query}». Prueba con <span className="text-em">bonos</span>,{" "}
                <span className="text-em">repos</span> o <span className="text-em">1835</span>.
              </div>
            )}
          </div>
        </aside>

        {/* panel principal */}
        <div className="min-w-0">
          <div className={tab === "erd" ? "block" : "hidden"}>
            <ErdPanel
              datasets={initialDatasets}
              selected={selected}
              onSelect={(d) => setSelectedSlug(d?.slug ?? null)}
              filter={filter}
              setFilter={setFilter}
            />
          </div>

          <div className={tab === "sql" ? "block h-[620px] overflow-hidden" : "hidden"}>
            <Terminal datasets={initialDatasets} initialConsultas={initialConsultas} onConsultasChanged={() => {}} />
          </div>

          <div className={tab === "diccionario" ? "block" : "hidden"}>
            <Diccionario datasets={initialDatasets} />
          </div>
        </div>
      </div>
    </section>
  );
}

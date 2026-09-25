"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CommandPalette, type PaletteAction } from "@/components/command-palette";
import { Console } from "@/components/console";
import { Explorer } from "@/components/explorer";
import { Inspector } from "@/components/inspector";
import { RelationMap } from "@/components/relation-map";
import { ThemePicker } from "@/components/theme-picker";
import { fmtNum, relTime } from "@/lib/format";
import {
  KINDS,
  type CatalogTree,
  type DatasetDetail,
  type DatasetNode,
  type Graph,
  type HistoryItem,
  type KindId,
  type RunResult,
  type SavedQuery,
} from "@/lib/types";

type Props = {
  initialTree: CatalogTree;
  initialGraph: Graph;
  initialSaved: SavedQuery[];
  initialSql: string;
};

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const LS = { sw: "mfc.sidebar.w", top: "mfc.panel.top" };

export function Workbench({ initialTree, initialGraph, initialSaved, initialSql }: Props) {
  const [kind, setKind] = useState<KindId>("vida");
  const [tree, setTree] = useState<CatalogTree>(initialTree);
  const [graph, setGraph] = useState<Graph | null>(initialGraph);
  const [saved, setSaved] = useState<SavedQuery[]>(initialSaved);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [sql, setSql] = useState(initialSql);
  const [maxRows, setMaxRows] = useState(200);
  const [result, setResult] = useState<RunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [shareNote, setShareNote] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const [saveTitle, setSaveTitle] = useState("");
  const [saveDesc, setSaveDesc] = useState("");
  const [contract, setContract] = useState<string | null>(null);
  const [sidebarW, setSidebarW] = useState(324);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [topPct, setTopPct] = useState(50);
  const [booted, setBooted] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);
  const firstFetch = useRef(true);

  /* ------------------------------------------------------- hidratación URL */
  useEffect(() => {
    const p = new URLSearchParams(window.location.search);
    const k = p.get("kind") as KindId | null;
    const q = p.get("q");
    const ds = p.get("dataset");
    if (k && KINDS.some((x) => x.id === k)) setKind(k);
    if (q) setSql(q);
    if (ds) void selectDataset(Number(ds));
    setBooted(true);
    if (q && p.get("autorun") !== "0") void run(q);
    else void run(initialSql);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!booted) return;
    const p = new URLSearchParams();
    p.set("kind", kind);
    if (selectedId) p.set("dataset", String(selectedId));
    if (sql.trim() && sql !== initialSql) p.set("q", sql);
    window.history.replaceState(null, "", `${window.location.pathname}?${p.toString()}`);
  }, [kind, selectedId, sql, booted, initialSql]);

  /* ------------------------------------------------------------- loaders */
  const run = useCallback(async (text?: string) => {
    const sqlText = (text ?? "").trim();
    if (!sqlText) return;
    setRunning(true);
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "content-type": "application/json", "x-mfc-actor": "analista-demo" },
        body: JSON.stringify({ sql: sqlText, maxRows }),
      });
      setResult(await res.json());
    } catch (e) {
      setResult({
        ok: false,
        columns: [],
        rows: [],
        rowCount: 0,
        truncated: false,
        durationMs: 0,
        cached: false,
        code: "network",
        error: (e as Error).message,
        tables: [],
      });
    } finally {
      setRunning(false);
    }
  }, [maxRows]);

  useEffect(() => {
    if (firstFetch.current) {
      firstFetch.current = false;
      return;
    }
    const p = new URLSearchParams({ kind });
    void fetch(`/api/catalog?${p}`)
      .then((r) => r.json())
      .then((t) => setTree(t as CatalogTree))
      .catch(() => undefined);
    void fetch(`/api/graph?${p}`)
      .then((r) => r.json())
      .then((g) => setGraph(g as Graph))
      .catch(() => undefined);
  }, [kind]);

  const selectDataset = useCallback(async (id: number) => {
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/datasets/${id}`);
      setDetail(res.ok ? ((await res.json()) as DatasetDetail) : null);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const loadHistory = useCallback(() => {
    void fetch("/api/query")
      .then((r) => r.json())
      .then((d) => setHistory((d.history ?? []) as HistoryItem[]))
      .catch(() => undefined);
  }, []);

  const reloadSaved = useCallback(() => {
    void fetch("/api/saved")
      .then((r) => r.json())
      .then((d) => setSaved((d.queries ?? []) as SavedQuery[]))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  /* ----------------------------------------------------------- shortcuts */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
      if (e.key === "?" && !(e.target as HTMLElement)?.closest("input,textarea")) {
        e.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  /* --------------------------------------------------------------- resizers */
  const startDrag = (mode: "sidebar" | "split") => (e: React.PointerEvent) => {
    e.preventDefault();
    const move = (ev: PointerEvent) => {
      if (mode === "sidebar") setSidebarW(clamp(ev.clientX, 240, 520));
      else {
        const box = mainRef.current?.getBoundingClientRect();
        if (box) setTopPct(clamp(((ev.clientY - box.top) / box.height) * 100, 24, 76));
      }
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      const w = mode === "sidebar" ? String(sidebarWRef.current) : String(topPctRef.current);
      localStorage.setItem(mode === "sidebar" ? LS.sw : LS.top, w);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };
  const sidebarWRef = useRef(sidebarW);
  const topPctRef = useRef(topPct);
  sidebarWRef.current = sidebarW;
  topPctRef.current = topPct;

  useEffect(() => {
    const sw = Number(localStorage.getItem(LS.sw));
    const tp = Number(localStorage.getItem(LS.top));
    if (Number.isFinite(sw) && sw >= 240 && sw <= 520) setSidebarW(sw);
    if (Number.isFinite(tp) && tp >= 24 && tp <= 76) setTopPct(tp);
  }, []);

  /* ---------------------------------------------------------------- derived */
  const flatDatasets = useMemo<DatasetNode[]>(
    () => tree.domains.flatMap((d) => [...d.sources.flatMap((s) => s.datasets), ...d.shared]),
    [tree],
  );
  const breadcrumb = useMemo(() => {
    if (!detail) return `${tree.domains.find((d) => d.kind === kind)?.name ?? "Todos los dominios"}`;
    const dom = tree.domains.find((d) => d.name === detail.domain?.name);
    const src = dom?.sources.find((s) => s.code === detail.source?.code);
    return [dom?.name, src?.code, detail.dataset.name].filter(Boolean).join(" › ");
  }, [detail, tree, kind]);

  const onPickSaved = useCallback(
    (s: SavedQuery) => {
      setSql(s.sql);
      void run(s.sql);
    },
    [run],
  );

  const toggleFavorite = useCallback(
    (s: SavedQuery) => {
      void fetch("/api/saved", {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ slug: s.slug, favorite: !s.favorite }),
      })
        .then(reloadSaved)
        .catch(() => undefined);
    },
    [reloadSaved],
  );

  const saveCurrent = useCallback(async () => {
    if (!saveTitle.trim()) return;
    await fetch("/api/saved", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ title: saveTitle.trim(), sql, description: saveDesc.trim() }),
    }).catch(() => undefined);
    setSaveOpen(false);
    setSaveTitle("");
    setSaveDesc("");
    reloadSaved();
  }, [saveTitle, saveDesc, sql, reloadSaved]);

  const share = useCallback(() => {
    const p = new URLSearchParams({ kind, q: sql, autorun: "1" });
    if (selectedId) p.set("dataset", String(selectedId));
    const url = `${window.location.origin}${window.location.pathname}?${p.toString()}`;
    void navigator.clipboard?.writeText(url).catch(() => undefined);
    setShareNote("enlace copiado");
    setTimeout(() => setShareNote(""), 2600);
  }, [kind, sql, selectedId]);

  const previewDataset = useCallback(
    (d: DatasetNode) => {
      const text = `SELECT * FROM ${d.physical} LIMIT 25;`;
      setSql(text);
      void run(text);
    },
    [run],
  );

  const actions = useMemo<PaletteAction[]>(
    () => [
      { id: "refresh", label: "Refrescar catálogo y mapa", hint: "recarga desde /api/catalog", run: () => {
          void fetch(`/api/catalog?kind=${kind}`).then((r) => r.json()).then(setTree);
          void fetch(`/api/graph?kind=${kind}`).then((r) => r.json()).then(setGraph);
        } },
      { id: "history", label: "Ver auditoría de consultas", hint: "catalog.query_log", run: loadHistory },
      { id: "review", label: "Abrir la revisión de arquitectura", hint: "/review", run: () => { window.location.href = "/review"; } },
      { id: "cycle-theme", label: "Rotar paleta de colores", run: () => {
          const order = ["swissborg", "bloomberg", "nord", "midnight", "informe"];
          const cur = document.documentElement.dataset.theme ?? "swissborg";
          const next = order[(order.indexOf(cur) + 1) % order.length];
          document.documentElement.dataset.theme = next;
          localStorage.setItem("mfc.theme", next);
        } },
    ],
    [kind, loadHistory],
  );

  const breachList = useMemo(
    () => flatDatasets.filter((d) => d.freshness === "breach").map((d) => d.name),
    [flatDatasets],
  );

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      {/* ------------------------------------------------------------ header */}
      <header
        className="no-print flex shrink-0 items-center gap-3 border-b px-3 py-2"
        style={{ background: "var(--bg-raised)", borderColor: "var(--border-accent)" }}
      >
        <button
          className="btn btn-ghost focus-ring !px-1.5"
          onClick={() => setSidebarOpen((v) => !v)}
          aria-expanded={sidebarOpen}
          aria-label="Mostrar u ocultar el explorador"
          title="Mostrar / ocultar explorador (colapsa el ancho, no con margen negativo)"
        >
          <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
            <path d="M1 2.5h14v11H1zM1 5.5h4v8H1z" />
          </svg>
        </button>
        <span className="mono rounded-md px-2 py-[3px] text-[10.5px] font-extrabold tracking-[0.8px]" style={{ background: "var(--accent)", color: "var(--accent-ink)" }}>
          MFC
        </span>
        <div className="flex min-w-0 items-baseline gap-2">
          <span className="text-[14px] font-bold tracking-[-0.2px]">Monitor Financiero Chile</span>
          <span className="hidden text-[11px] text-[var(--text-dim)] md:inline">Catálogo + consultas gobernadas sobre carteras institucionales</span>
        </div>

        <span className="hidden items-center gap-1.5 xl:flex">
          <span className="chip !cursor-default">
            <span className="dot dot-ok" />
            {tree.datasetCount} datasets · {fmtNum(tree.rowCount)} filas
          </span>
          <span className="chip !cursor-default" style={{ color: breachList.length ? "var(--bad)" : undefined, borderColor: breachList.length ? "var(--bad)" : undefined }} title={breachList.join(", ")}>
            {tree.breachCount} SLO incumplidos · {tree.failedChecks} checks caídos
          </span>
          <span className="chip !cursor-default" title="Engine que resuelve las consultas">
            Postgres 16 · server-side
          </span>
        </span>

        <div className="ml-auto flex items-center gap-1.5">
          {KINDS.map((k) => (
            <button key={k.id} onClick={() => setKind(k.id)} className={`chip ${kind === k.id ? "chip-active" : ""}`}>
              {k.label}
            </button>
          ))}
          <button className="btn focus-ring ml-1" onClick={() => setPaletteOpen(true)} title="Paleta de comandos">
            ⌘K
          </button>
          <Link href="/review" className="btn focus-ring" style={{ borderColor: "var(--border-accent)", color: "var(--accent)" }}>
            Revisión de arquitectura
          </Link>
          <ThemePicker />
        </div>
      </header>

      {/* -------------------------------------------------------------- body */}
      <div className="flex min-h-0 flex-1">
        <div
          className="no-print shrink-0 overflow-hidden border-r border-[var(--border)] transition-[width] duration-200"
          style={{ width: sidebarOpen ? sidebarW : 0, borderColor: sidebarOpen ? undefined : "transparent" }}
        >
          <div style={{ width: sidebarW }} className="h-full">
            <Explorer tree={tree} selectedId={selectedId} onSelect={(id) => void selectDataset(id)} onPreview={previewDataset} />
          </div>
        </div>
        {sidebarOpen && (
          <div
            onPointerDown={startDrag("sidebar")}
            className="no-print w-[5px] shrink-0 cursor-col-resize transition-colors hover:bg-[var(--accent)]"
            title="Arrastra para ajustar el explorador"
          />
        )}

        <div ref={mainRef} className="flex min-w-0 flex-1 flex-col">
          {/* mapa relacional */}
          <section className="relative min-h-0 overflow-hidden" style={{ height: `${topPct}%` }}>
            <div
              className="absolute top-2.5 left-3 z-10 flex flex-wrap items-center gap-2 rounded-lg border px-2.5 py-1.5 backdrop-blur-md"
              style={{ background: "color-mix(in srgb, var(--bg-panel) 88%, transparent)", borderColor: "var(--border-accent)" }}
            >
              <span className="text-[10.5px] font-bold tracking-[0.6px] uppercase">Mapa relacional</span>
              <span className="mono max-w-[46vw] truncate text-[10.5px]" style={{ color: "var(--accent)" }}>
                {breadcrumb}
              </span>
              <span className="tag" title="Las aristas se generan desde catalog.dataset_relations, que a su vez se deriva de la metadata de columnas">
                auto-derivado
              </span>
              {graph && (
                <span className="mono text-[10px] text-[var(--text-mute)]">
                  {graph.nodes.length} nodos / {graph.edges.length} joins válidos
                </span>
              )}
            </div>
            <RelationMap graph={graph} selectedId={selectedId} onSelect={(id) => void selectDataset(id)} kindLabel={KINDS.find((k) => k.id === kind)?.label ?? ""} />
          </section>

          <div onPointerDown={startDrag("split")} className="no-print h-[6px] shrink-0 cursor-row-resize relative" style={{ background: "var(--border)" }} title="Arrastra para reequilizar">
            <span className="absolute top-1/2 left-1/2 h-[2px] w-9 -translate-x-1/2 -translate-y-1/2 rounded" style={{ background: "var(--text-mute)" }} />
          </div>

          {/* consola */}
          <section className="min-h-0 flex-1">
            <Console
              sql={sql}
              onSqlChange={setSql}
              result={result}
              running={running}
              onRun={() => void run(sql)}
              maxRows={maxRows}
              onMaxRows={setMaxRows}
              saved={saved}
              onPickSaved={onPickSaved}
              onToggleFavorite={toggleFavorite}
              onSaveCurrent={() => setSaveOpen(true)}
              onShare={share}
              shareNote={shareNote}
              history={history}
              onReloadHistory={loadHistory}
              onUseHistory={(t) => setSql(t)}
            />
          </section>
        </div>

        {(detail || detailLoading) && (
          <Inspector
            detail={detail}
            loading={detailLoading}
            onClose={() => {
              setDetail(null);
              setSelectedId(null);
            }}
            onRunSql={(t) => {
              setSql(t);
              void run(t);
            }}
            onOpenContract={() => setContract(buildContract(detail))}
          />
        )}
      </div>

      {/* ------------------------------------------------------------ status */}
      <footer className="no-print flex shrink-0 items-center gap-3 border-t px-3 py-1 text-[10px] text-[var(--text-mute)]" style={{ background: "var(--bg-raised)", borderColor: "var(--border)" }}>
        <span className="mono">actor: analista-demo (sin SSO: talón de Aquiles del diseño actual)</span>
        <span>· catálogo leído {relTime(tree.generatedAt)}</span>
        <span className="ml-auto">
          datos <strong style={{ color: "var(--warn)" }}>sintéticos</strong> generados por <span className="mono">scripts/seed.mjs</span> · el diseño apunta a
          Parquet versionado + vista gobernada
        </span>
      </footer>

      {paletteOpen && (
        <CommandPalette
          open={paletteOpen}
          onClose={() => setPaletteOpen(false)}
          datasets={flatDatasets}
          saved={saved}
          actions={actions}
          onPickDataset={(d) => {
            void selectDataset(d.id);
            previewDataset(d);
          }}
          onPickSaved={onPickSaved}
        />
      )}

      {saveOpen && (
        <Modal title="Guardar consulta en el catálogo" onClose={() => setSaveOpen(false)}>
          <p className="mb-2 text-[11px] text-[var(--text-dim)]">
            En producción esto sería un <span className="mono">merge request</span> contra <span className="mono">queries/*.sql</span> (queries as code), no un
            <span className="mono"> localStorage</span>: así quedan revisión, dueño y CI.
          </p>
          <label className="mb-1 block text-[10px] tracking-wide uppercase">Título</label>
          <input value={saveTitle} onChange={(e) => setSaveTitle(e.target.value)} className="inset focus-ring mb-2 w-full rounded-md px-2 py-1.5 text-[12px] outline-none" placeholder="Riesgo de concentración por contraparte" />
          <label className="mb-1 block text-[10px] tracking-wide uppercase">Para qué sirve</label>
          <textarea value={saveDesc} onChange={(e) => setSaveDesc(e.target.value)} rows={2} className="inset focus-ring mb-3 w-full rounded-md px-2 py-1.5 text-[12px] outline-none" placeholder="Se revisa en el comité de riesgos monthly" />
          <pre className="mono inset mb-3 max-h-[120px] overflow-auto rounded-md p-2 text-[10px] whitespace-pre-wrap">{sql}</pre>
          <div className="flex justify-end gap-2">
            <button className="btn" onClick={() => setSaveOpen(false)}>
              Cancelar
            </button>
            <button className="btn btn-primary" onClick={() => void saveCurrent()}>
              Guardar
            </button>
          </div>
        </Modal>
      )}

      {contract && (
        <Modal title="Contrato de datos (yaml)" onClose={() => setContract(null)} wide>
          <p className="mb-2 text-[11px] text-[var(--text-dim)]">
            Publica esto junto al dataset: SLA de frescura, dueños, granularidad y expectativas de calidad. Es el artefacto que evita que el catálogo se pudra.
          </p>
          <pre className="mono inset max-h-[52vh] overflow-auto rounded-md p-3 text-[10.5px] leading-relaxed whitespace-pre-wrap">{contract}</pre>
        </Modal>
      )}
    </div>
  );
}

function Modal({ title, children, onClose, wide }: { title: string; children: React.ReactNode; onClose: () => void; wide?: boolean }) {
  return (
    <div className="fixed inset-0 z-[70] grid place-items-center bg-black/55 p-6" onClick={onClose}>
      <div className={`panel fade-up max-h-[80vh] w-full ${wide ? "max-w-[720px]" : "max-w-[520px]"} overflow-hidden rounded-xl`} style={{ boxShadow: "var(--shadow)" }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-[var(--border)] px-3 py-2" style={{ background: "var(--bg-raised)" }}>
          <span className="text-[11.5px] font-bold tracking-[0.4px] uppercase">{title}</span>
          <button className="btn btn-ghost !px-1.5" onClick={onClose} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="p-3">{children}</div>
      </div>
    </div>
  );
}

function buildContract(d: DatasetDetail | null): string {
  if (!d) return "";
  const ds = d.dataset;
  return [
    "version: 2",
    `name: ${ds.name}`,
    `domain: ${d.domain?.slug ?? "unknown"}`,
    `owner: ${d.domain?.ownerTeam ?? ds.owner}`,
    `contact: ${d.domain?.ownerContact ?? ds.owner}`,
    `source_of_truth: ${d.source?.code ?? "intno"}`,
    `materialization: ${ds.physicalSchema}.${ds.physicalTable} (view=${ds.layer === "view"})`,
    `grain: ${ds.grain}`,
    "freshness_sla:",
    `  cadence: ${ds.refreshCadence}`,
    `  max_age_hours: ${ds.freshnessSloHours}`,
    "schema_version: " + ds.schemaVersion,
    "access_policy: " + ds.accessPolicy,
    "columns:",
    ...d.columns.map((c) => `  - { name: ${c.name}, type: ${c.dataType}, nullable: ${c.nullable}, pk: ${c.isPk}${c.unit ? `, unit: ${c.unit}` : ""} }`),
    "expectations:",
    ...d.checks.map((c) => `  - { id: ${c.kind}, expression: "${c.expression.replace(/"/g, "'")}", severity: ${c.severity} }`),
    "lineage:",
    `  upstream: [${d.outbound.map((r) => `${r.target}.${r.toColumn}`).join(", ")}]`,
    `  downstream: [${d.inbound.map((r) => r.origin).join(", ")}]`,
    "consumers_approved:",
    `  - mart.v_inversion_consolidada   # capa semántica; el resto lee de aquí`,
    "pii_classification: " + (d.columns.some((c) => c.masking !== "none") ? "internal+masking" : "internal"),
  ].join("\n");
}

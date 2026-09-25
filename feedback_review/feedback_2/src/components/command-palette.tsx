"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { DatasetNode, SavedQuery } from "@/lib/types";

export type PaletteAction = { id: string; label: string; hint?: string; run: () => void };

type Props = {
  open: boolean;
  onClose: () => void;
  datasets: DatasetNode[];
  saved: SavedQuery[];
  actions: PaletteAction[];
  onPickDataset: (d: DatasetNode) => void;
  onPickSaved: (s: SavedQuery) => void;
};

type Item = { key: string; group: string; label: string; sub: string; run: () => void };

export function CommandPalette({ open, onClose, datasets, saved, actions, onPickDataset, onPickSaved }: Props) {
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setQ("");
      setIdx(0);
    }
  }, [open]);

  const items = useMemo<Item[]>(() => {
    const needle = q.trim().toLowerCase();
    const has = (s: string) => !needle || s.toLowerCase().includes(needle);
    return [
      ...datasets.filter((d) => has(d.name) || has(d.physical)).slice(0, 9).map<Item>((d) => ({
        key: `ds-${d.id}`,
        group: "Dataset",
        label: d.name,
        sub: `${d.physical} · ${d.layer} · ${d.rows} filas`,
        run: () => onPickDataset(d),
      })),
      ...saved.filter((s) => has(s.title) || has(s.sql)).slice(0, 6).map<Item>((s) => ({
        key: `q-${s.slug}`,
        group: "Consulta guardada",
        label: s.title,
        sub: s.description,
        run: () => onPickSaved(s),
      })),
      ...actions.filter((a) => has(a.label)).map<Item>((a) => ({
        key: `a-${a.id}`,
        group: "Acción",
        label: a.label,
        sub: a.hint ?? "",
        run: a.run,
      })),
    ];
  }, [q, datasets, saved, actions, onPickDataset, onPickSaved]);

  useEffect(() => setIdx(0), [q]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-start justify-center bg-black/55 pt-[12vh]" onClick={onClose}>
      <div
        className="panel fade-up w-[620px] max-w-[92vw] overflow-hidden rounded-xl"
        style={{ boxShadow: "var(--shadow)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <input
          autoFocus
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setIdx((i) => Math.min(items.length - 1, i + 1));
            }
            if (e.key === "ArrowUp") {
              e.preventDefault();
              setIdx((i) => Math.max(0, i - 1));
            }
            if (e.key === "Enter") {
              e.preventDefault();
              items[idx]?.run();
              onClose();
            }
            if (e.key === "Escape") onClose();
          }}
          placeholder="Buscar dataset, consulta o acción…"
          className="mono w-full border-b border-[var(--border)] bg-transparent px-4 py-3 text-[13px] outline-none"
        />
        <div ref={listRef} className="max-h-[46vh] overflow-y-auto py-1">
          {items.map((it, i) => (
            <button
              key={it.key}
              onMouseEnter={() => setIdx(i)}
              onClick={() => {
                it.run();
                onClose();
              }}
              className="flex w-full items-baseline gap-3 px-4 py-2 text-left"
              style={{ background: i === idx ? "var(--bg-select)" : undefined }}
            >
              <span className="tag w-[112px] shrink-0">{it.group}</span>
              <span className="mono truncate text-[12px]">{it.label}</span>
              <span className="ml-auto max-w-[46%] truncate text-[10.5px] text-[var(--text-mute)]">{it.sub}</span>
            </button>
          ))}
          {items.length === 0 && <div className="px-4 py-4 text-[11.5px] text-[var(--text-mute)]">Sin coincidencias.</div>}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";

export const THEMES = [
  { id: "swissborg", name: "SwissBorg", sw: ["#191e29", "#01c38d", "#4aa8ff"] },
  { id: "bloomberg", name: "Terminal", sw: ["#0f0f10", "#ff9900", "#fcd34d"] },
  { id: "nord", name: "Nórdico", sw: ["#242933", "#88c0d0", "#a3be8c"] },
  { id: "midnight", name: "Medianoche", sw: ["#0b1120", "#38bdf8", "#34d399"] },
  { id: "informe", name: "Informe (claro)", sw: ["#f5f6f8", "#0b6f54", "#1657a8"] },
];

const KEY = "mfc.theme";

export function ThemePicker() {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState("swissborg");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem(KEY);
    if (stored) {
      setActive(stored);
      document.documentElement.dataset.theme = stored;
    } else {
      setActive(document.documentElement.dataset.theme ?? "swissborg");
    }
  }, []);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const choose = (id: string) => {
    document.documentElement.dataset.theme = id;
    localStorage.setItem(KEY, id);
    setActive(id);
    setOpen(false);
  };

  const current = THEMES.find((t) => t.id === active) ?? THEMES[0];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="btn focus-ring"
        title="Paleta de colores (se guarda en este navegador)"
      >
        <span className="mono" style={{ color: "var(--text-mute)" }}>
          {current.name}
        </span>
        <span className="flex gap-[3px]">
          {current.sw.map((c) => (
            <i key={c} className="block h-3 w-3 rounded-[3px] border border-black/30" style={{ background: c }} />
          ))}
        </span>
      </button>
      {open && (
        <ul
          role="listbox"
          className="panel fade-up absolute right-0 top-[calc(100%+6px)] z-50 flex w-[190px] flex-col gap-1 rounded-lg p-1.5"
          style={{ boxShadow: "var(--shadow)" }}
        >
          {THEMES.map((t) => (
            <li key={t.id}>
              <button
                type="button"
                role="option"
                aria-selected={t.id === active}
                onClick={() => choose(t.id)}
                className="focus-ring flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[11.5px]"
                style={{
                  background: t.id === active ? "var(--bg-select)" : "transparent",
                  color: t.id === active ? "var(--accent)" : "var(--text-dim)",
                }}
              >
                <span className="flex gap-[2px]">
                  {t.sw.map((c) => (
                    <i key={c} className="block h-2.5 w-2.5 rounded-[2px] border border-black/30" style={{ background: c }} />
                  ))}
                </span>
                {t.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

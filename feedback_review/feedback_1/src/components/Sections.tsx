"use client";

import { useEffect, useRef, useState } from "react";
import { RECOMENDACIONES, TICKER, type Dataset } from "@/lib/data";
import type { PersistState } from "@/lib/store";

const fmt = (n: number, dec = 0) =>
  n.toLocaleString("es-CL", { minimumFractionDigits: dec, maximumFractionDigits: dec });

/* ──────────────────────────────────────────────────────────── */

function Mark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 34 34" className={className} aria-hidden="true">
      <rect x="0.75" y="0.75" width="32.5" height="32.5" fill="none" stroke="currentColor" strokeOpacity="0.35" />
      <path d="M5 27h5V16H5zM12.5 27h5V11h-5zM20 27h5V19h-5z" fill="currentColor" />
      <path
        d="M27.4 4.2l1.35 2.9 2.9 1.35-2.9 1.35-1.35 2.9-1.35-2.9-2.9-1.35 2.9-1.35z"
        fill="currentColor"
        opacity="0.9"
      />
      <path d="M4 29.5h26" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

export function Masthead({ persist }: { persist: PersistState }) {
  return (
    <header className="sticky top-0 z-50 border-b border-rule bg-ink/92 backdrop-blur-sm">
      <div className="mx-auto flex h-12 max-w-[1680px] items-center justify-between gap-4 px-4 md:px-8">
        <a href="#top" className="flex items-center gap-3 text-em transition-opacity hover:opacity-80">
          <Mark className="h-6 w-6" />
          <span className="label text-paper">Monitor Financiero Chile</span>
          <span className="hidden label text-mut sm:inline">/ Carteras institucionales</span>
        </a>
        <div className="flex items-center gap-4">
          <span className="hidden label text-mut md:inline">Cierres de referencia · 15 sep 2026</span>
          <span className="flex items-center gap-2 border border-rule px-2 py-1 label text-mut">
            <span
              className={`h-1.5 w-1.5 rounded-full ${persist.ok ? "bg-em" : "bg-amber"}`}
              style={{ boxShadow: persist.ok ? "0 0 6px #00d09a" : "0 0 6px #f2a93b" }}
            />
            {persist.ok ? "Postgres · Drizzle" : "Memoria · fallback"}
          </span>
        </div>
      </div>
    </header>
  );
}

/* ──────────────────────────────────────────────────────────── */

export function Ticker() {
  const items = [...TICKER, ...TICKER];
  return (
    <div className="marquee-host relative overflow-hidden border-b border-rule bg-panel2">
      <div className="marquee-track">
        {items.map((t, i) => {
          const positive = t.delta !== null && t.delta > 0;
          const negative = t.delta !== null && t.delta < 0;
          return (
            <span
              key={`${t.sym}-${i}`}
              aria-hidden={i >= TICKER.length}
              className="flex shrink-0 items-baseline gap-2 border-r border-rule px-5 py-2 font-mono text-[12px] tnum"
            >
              <span className="tracking-[0.14em] text-paper">{t.sym}</span>
              <span className="text-mut">{t.value}</span>
              {t.delta !== null && (
                <span className={positive ? "text-em" : negative ? "text-loss" : "text-mut"}>
                  {positive ? "▲" : negative ? "▼" : "•"} {Math.abs(t.delta).toFixed(2)}%
                </span>
              )}
            </span>
          );
        })}
      </div>
      <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-ink to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-ink to-transparent" />
    </div>
  );
}

/* ──────────────────────────────────────────────────────────── */

function useCountUp(target: number, ms = 1200) {
  const [value, setValue] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setValue(target);
      return;
    }
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);

  return { value, ref };
}

function Stat({ target, suffix, caption, dec = 0 }: { target: number; suffix?: string; caption: string; dec?: number }) {
  const { value } = useCountUp(target);
  return (
    <div className="border-l border-rule2 pl-4">
      <div className="font-display text-4xl leading-none text-paper tnum md:text-5xl">
        {fmt(value, dec)}
        {suffix && <span className="text-em">{suffix}</span>}
      </div>
      <div className="mt-2 label text-mut">{caption}</div>
    </div>
  );
}

export function Hero({ totalDatasets, totalFilas }: { totalDatasets: number; totalFilas: number }) {
  return (
    <section id="top" className="relative overflow-hidden border-b border-rule">
      <img
        src="images/sanhattan.jpg"
        alt="Distrito financiero de Santiago al anochecer"
        className="absolute inset-0 h-full w-full object-cover object-right"
        style={{ opacity: 0.62 }}
        loading="eager"
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(90deg, #070b0c 0%, rgba(7,11,12,0.94) 38%, rgba(7,11,12,0.55) 72%, rgba(7,11,12,0.25) 100%)",
        }}
      />
      <div
        className="absolute inset-x-0 bottom-0 h-40"
        style={{ background: "linear-gradient(to top, #070b0c, rgba(7,11,12,0))" }}
      />

      <div className="relative mx-auto max-w-[1680px] px-4 py-16 md:px-8 md:py-24">
        <div className="rise max-w-4xl">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 label text-em">
            <span>CMF · Circular N°1835</span>
            <span className="text-rule2">/</span>
            <span className="text-mut">Banco Central · series diarias</span>
            <span className="text-rule2">/</span>
            <span className="text-mut">Bolsa de Santiago</span>
          </div>

          <h1 className="mt-6 font-display text-[clamp(2.6rem,7vw,6rem)] leading-[0.9] tracking-[-0.02em] text-paper">
            El dato regulatorio chileno,
            <br />
            <span className="italic text-em">centralizado</span> en una sola pantalla.
          </h1>

          <p className="mt-6 max-w-xl text-[15px] leading-relaxed text-mut">
            Nueve datasets de cartera de inversiones, derivados, repos y fondos obligatorios —modelados sobre los
            requerimientos de la CMF— consultables con SQL en lenguaje natural y explorables en un mapa relacional
            navegable con teclado.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <a
              href="#workspace"
              data-tab="sql"
              className="group flex items-center gap-2 bg-em px-5 py-3 label text-ink transition-colors hover:bg-[#02e2a4]"
            >
              Abrir terminal SQL
              <span className="transition-transform group-hover:translate-x-1">→</span>
            </a>
            <a
              href="#workspace"
              data-tab="erd"
              className="flex items-center gap-2 border border-rule2 px-5 py-3 label text-paper transition-colors hover:border-em hover:text-em"
            >
              Ver mapa relacional
            </a>
          </div>

          <div className="mt-12 grid max-w-2xl grid-cols-2 gap-6 md:grid-cols-4">
            <Stat target={totalDatasets} caption="Datasets" />
            <Stat target={totalFilas} caption="Filas indexadas" />
            <Stat target={6} caption="Industrias" />
            <Stat target={4.5} dec={1} suffix="%" caption="TPM vigente" />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────────────────── */

export function Serie({ datasets }: { datasets: Dataset[] }) {
  const serie = datasets.find((d) => d.slug === "mercado.indicadores");
  const filas = serie?.filas ?? [];
  const valores = filas.map((f) => Number(f.usd_clp)).filter((v) => !Number.isNaN(v));
  const ipsa = filas.map((f) => Number(f.ipsa)).filter((v) => !Number.isNaN(v));

  const w = 640;
  const h = 180;
  const path = (vals: number[]) => {
    if (vals.length < 2) return "";
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const span = max - min || 1;
    return vals
      .map((v, i) => {
        const x = (i / (vals.length - 1)) * (w - 20) + 10;
        const y = h - 18 - ((v - min) / span) * (h - 44);
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ");
  };

  return (
    <section className="relative border-b border-rule bg-panel">
      <img
        src="images/metal.jpg"
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-25"
      />
      <div className="relative mx-auto grid max-w-[1680px] gap-10 px-4 py-14 md:grid-cols-[1fr_1.4fr] md:px-8">
        <div>
          <div className="label text-em">Serie macro · 12 meses</div>
          <h2 className="mt-4 font-display text-4xl leading-tight text-paper md:text-5xl">
            Dólar observado e IPSA,
            <br />
            <span className="italic text-mut">mes a mes</span>.
          </h2>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-mut">
            La capa de series del centralizador alimenta la cinta superior, los indicadores de portada y cualquier
            consulta SQL que cruces contra <span className="font-mono text-paper">{'mercado.indicadores'}</span>.
          </p>
          <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-rule pt-6">
            {[
              ["Dólar observado", "913,98 CLP"],
              ["UF", "40.054,20 CLP"],
              ["TPM", "4,50%"],
              ["IPC 12 meses", "4,5%"],
              ["IPSA", "11.342,39"],
              ["Cobre LME", "6,61 USD/lb"],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="label text-mut">{k}</dt>
                <dd className="mt-1 font-mono text-lg text-paper tnum">{v}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="border border-rule bg-ink/70 p-5">
          <div className="flex items-baseline justify-between">
            <span className="label text-mut">USD/CLP — cierre mensual</span>
            <span className="font-mono text-xs text-loss tnum">−3,61% en 12 m</span>
          </div>
          <svg viewBox={`0 0 ${w} ${h}`} className="mt-3 w-full" role="img" aria-label="Serie del dólar observado">
            {[0, 1, 2, 3].map((i) => (
              <line key={i} x1="0" x2={w} y1={18 + i * 40} y2={18 + i * 40} stroke="#1f2a2c" strokeWidth="1" />
            ))}
            <path d={`${path(valores)} L ${w - 10} ${h - 18} L 10 ${h - 18} Z`} fill="#00d09a" opacity="0.08" />
            <path className="draw-line" d={path(valores)} fill="none" stroke="#00d09a" strokeWidth="2" />
          </svg>

          <div className="mt-4 flex items-baseline justify-between border-t border-rule pt-4">
            <span className="label text-mut">IPSA — cierre mensual</span>
            <span className="font-mono text-xs text-em tnum">+8,84% en 12 m</span>
          </div>
          <svg viewBox={`0 0 ${w} ${h}`} className="mt-3 w-full" role="img" aria-label="Serie del IPSA">
            {[0, 1, 2, 3].map((i) => (
              <line key={i} x1="0" x2={w} y1={18 + i * 40} y2={18 + i * 40} stroke="#1f2a2c" strokeWidth="1" />
            ))}
            <path d={`${path(ipsa)} L ${w - 10} ${h - 18} L 10 ${h - 18} Z`} fill="#f2a93b" opacity="0.07" />
            <path className="draw-line" d={path(ipsa)} fill="none" stroke="#f2a93b" strokeWidth="2" />
          </svg>

          <p className="mt-4 label text-mut">
            Fuente: Banco Central de Chile y Bolsa de Santiago · serie de referencia
          </p>
        </div>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────────────────── */

export function TablaTenencias({ dataset }: { dataset?: Dataset }) {
  const filas = [...(dataset?.filas ?? [])].sort(
    (a, b) => Number(b.monto_m_clp ?? 0) - Number(a.monto_m_clp ?? 0),
  );
  const max = Math.max(...filas.map((f) => Number(f.monto_m_clp ?? 0)), 1);

  return (
    <section className="border-b border-rule">
      <div className="mx-auto max-w-[1680px] px-4 py-14 md:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-rule pb-4">
          <div>
            <div className="label text-em">Tabla de tenencias · renta fija</div>
            <h2 className="mt-3 font-display text-4xl leading-tight text-paper md:text-5xl">
              Cartera de bonos de las aseguradoras de vida
            </h2>
          </div>
          <div className="text-right label text-mut">
            <div>{dataset?.archivo ?? "—"}</div>
            <div className="mt-1">{dataset?.circular ?? "Circular N°1835"} · corte 30 sep 2026</div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] border-collapse text-sm">
            <thead>
              <tr className="label text-mut">
                <th className="py-3 pr-4 text-left font-normal">Nemotécnico</th>
                <th className="py-3 pr-4 text-left font-normal">Emisor</th>
                <th className="py-3 pr-4 text-left font-normal">Tipo</th>
                <th className="py-3 pr-4 text-left font-normal">Mon.</th>
                <th className="py-3 pr-4 text-right font-normal">Monto MM CLP</th>
                <th className="py-3 pr-4 text-right font-normal">TIR %</th>
                <th className="py-3 pr-4 text-right font-normal">Duración</th>
                <th className="py-3 text-right font-normal">Presencia</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[13px] tnum">
              {filas.map((f, i) => (
                <tr
                  key={String(f.nemotecnico)}
                  className="rise border-t border-rule transition-colors hover:bg-em/5"
                  style={{ animationDelay: `${i * 45}ms` }}
                >
                  <td className="py-2.5 pr-4 text-paper">{String(f.nemotecnico)}</td>
                  <td className="py-2.5 pr-4 text-mut">{String(f.emisor)}</td>
                  <td className="py-2.5 pr-4 text-mut">{String(f.tipo_bono)}</td>
                  <td className="py-2.5 pr-4 text-amber">{String(f.moneda)}</td>
                  <td className="relative py-2.5 pr-4 text-right text-paper">
                    <span
                      className="absolute inset-y-1 right-0 bg-em/10"
                      style={{ width: `${(Number(f.monto_m_clp) / max) * 100}%` }}
                    />
                    <span className="relative">{fmt(Number(f.monto_m_clp), 1)}</span>
                  </td>
                  <td className="py-2.5 pr-4 text-right text-em">{fmt(Number(f.tir_mercado_pct), 2)}</td>
                  <td className="py-2.5 pr-4 text-right text-mut">{fmt(Number(f.duration_anios), 1)} a</td>
                  <td className="py-2.5 text-right text-mut">{fmt(Number(f.presencia_pct))}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-4 label text-mut">
          Valores de muestra con estructura equivalente a los archivos de la CMF · no constituyen información oficial
        </p>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────────────────── */

const severidadColor: Record<string, string> = {
  Crítica: "text-loss border-loss/40",
  Alta: "text-amber border-amber/40",
  Media: "text-mut border-rule2",
};

export function Auditoria() {
  return (
    <section className="border-b border-rule bg-panel">
      <div className="mx-auto max-w-[1680px] px-4 py-16 md:px-8">
        <div className="grid gap-8 border-b border-rule pb-8 md:grid-cols-[1fr_auto] md:items-end">
          <div>
            <div className="label text-em">Auditoría del prototipo</div>
            <h2 className="mt-3 max-w-3xl font-display text-4xl leading-[1.05] text-paper md:text-6xl">
              Ocho reparaciones para pasar de maqueta a{" "}
              <span className="italic text-em">centralizador de datos</span>.
            </h2>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-mut">
            Revisión del HTML/CSS que entregaste: arquitectura, accesibilidad, diseño, producto y persistencia. Cada
            ítem trae el diagnóstico y la corrección aplicada en esta versión.
          </p>
        </div>

        <ol className="mt-2">
          {RECOMENDACIONES.map((r, i) => (
            <li
              key={r.n}
              className="rise grid gap-4 border-b border-rule py-7 md:grid-cols-[4rem_11rem_1fr_1fr] md:gap-8"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="font-display text-3xl leading-none text-rule2 tnum md:text-4xl">{r.n}</div>
              <div className="flex flex-wrap items-start gap-2 md:block">
                <span className={`border px-2 py-1 label ${severidadColor[r.severidad]}`}>{r.severidad}</span>
                <span className="mt-2 block label text-mut">{r.area}</span>
              </div>
              <div>
                <h3 className="text-base font-semibold leading-snug text-paper">{r.titulo}</h3>
                <p className="mt-2 text-sm leading-relaxed text-mut">{r.diagnostico}</p>
              </div>
              <div className="border-l-2 border-em/60 pl-4">
                <div className="label text-em">Acción tomada</div>
                <p className="mt-2 text-sm leading-relaxed text-paper/90">{r.accion}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────────────────── */

const FUENTES = [
  {
    fuente: "CMF · Cartera de inversiones (Circular N°1835)",
    uso: "Estructura de renta fija, renta variable, bienes raíces y solvencia de las aseguradoras.",
    url: "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/",
  },
  {
    fuente: "CMF · Anexos técnicos Circular N°1835",
    uso: "Diccionario de datos y proceso de validación física y lógica de los archivos.",
    url: "https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf",
  },
  {
    fuente: "Banco Central de Chile · Si3",
    uso: "Dólar observado, UF, TPM e IPC de la cinta de cotizaciones.",
    url: "https://si3.bcentral.cl/",
  },
  {
    fuente: "Bolsa de Santiago",
    uso: "Cierres del IPSA y de los emisores del índice.",
    url: "https://www.bolsadesantiago.com/",
  },
];

export function Fuentes({ aseguradoras }: { aseguradoras?: Dataset }) {
  return (
    <section className="border-b border-rule">
      <div className="mx-auto grid max-w-[1680px] gap-10 px-4 py-16 md:grid-cols-[1.1fr_1fr] md:px-8">
        <div className="relative overflow-hidden border border-rule">
          <img src="images/circulares.jpg" alt="Circulares impresas sobre una mesa de trabajo" className="h-full w-full object-cover" style={{ opacity: 0.85 }} />
          <div className="absolute inset-0" style={{ background: "linear-gradient(to top, rgba(7,11,12,0.95), rgba(7,11,12,0.1))" }} />
          <div className="absolute inset-x-0 bottom-0 p-6">
            <div className="label text-em">Procedencia</div>
            <p className="mt-2 max-w-md font-display text-2xl leading-snug text-paper">
              Cada cifra lleva su fuente, su periodo y su circular. Sin sello, no hay dato.
            </p>
          </div>
        </div>

        <div>
          <div className="label text-em">Fuentes y método</div>
          <h2 className="mt-3 font-display text-4xl leading-tight text-paper md:text-5xl">De dónde sale cada fila</h2>

          <ul className="mt-6">
            {FUENTES.map((f) => (
              <li key={f.fuente} className="border-t border-rule py-4">
                <a
                  href={f.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="group flex items-baseline justify-between gap-4"
                >
                  <span className="text-sm font-semibold text-paper transition-colors group-hover:text-em">
                    {f.fuente}
                  </span>
                  <span className="label text-mut transition-transform group-hover:translate-x-1">↗</span>
                </a>
                <p className="mt-1 text-sm leading-relaxed text-mut">{f.uso}</p>
              </li>
            ))}
          </ul>

          <div className="mt-6 border border-rule bg-panel p-5">
            <div className="label text-amber">Descargo</div>
            <p className="mt-2 text-sm leading-relaxed text-mut">
              Los valores cargados en esta demostración son de muestra y reproducen la estructura de los archivos
              reportados a la CMF; las cotizaciones de la cinta corresponden a cierres de referencia de septiembre de
              2026. Para uso productivo, reemplaza <span className="font-mono text-paper">SEED_DATASETS</span> por tus
              pipelines Parquet {aseguradoras ? `(${aseguradoras.filas.length} entidades en el maestro)` : ""}.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────────────────── */

export function Pie() {
  return (
    <footer className="bg-ink">
      <div className="mx-auto flex max-w-[1680px] flex-col gap-6 px-4 py-10 md:flex-row md:items-center md:justify-between md:px-8">
        <div className="flex items-center gap-3 text-em">
          <Mark className="h-7 w-7" />
          <div>
            <div className="label text-paper">Monitor Financiero Chile</div>
            <div className="mt-1 label text-mut">Next.js · PostgreSQL · Drizzle · SQL engine propio</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2 label text-mut">
          <span>9 datasets</span>
          <span>6 industrias</span>
          <span>3 rutas API</span>
          <span>© 2026 · Uso demostrativo</span>
        </div>
      </div>
    </footer>
  );
}

const nf = (opts: Intl.NumberFormatOptions) => new Intl.NumberFormat("es-CL", opts);
const int0 = nf({ maximumFractionDigits: 0 });
const dec2 = nf({ minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Los montos del data plane ya vienen en miles de CLP: 1 unidad = $1.000. */
export function fmtMClp(v: number | string | null | undefined): string {
  const n = toNum(v);
  if (n === null) return "—";
  const clp = n * 1000;
  const compact = new Intl.NumberFormat("es-CL", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(clp);
  return `$ ${compact}`;
}

/** Formato de celda: decide según el nombre/tipo de la columna. */
export function fmtCell(name: string, v: unknown): string {
  if (v === null || v === undefined) return "∅";
  if (typeof v === "boolean") return v ? "sí" : "no";
  const n = typeof v === "number" ? v : /^\d+([.,]\d+)?$/.test(String(v)) ? Number(v) : null;
  if (n === null) return String(v);
  if (/_pct$/.test(name)) return `${dec2.format(n)} %`;
  if (/_m_clp$/.test(name)) return fmtMClp(n);
  if (Number.isInteger(n) && Math.abs(n) < 100000) return int0.format(n);
  return fmtNum(n, Math.abs(n) < 100 ? 4 : 2);
}

export function fmtNum(v: unknown, maxFrac = 2): string {
  if (v === null || v === undefined) return "—";
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) return String(v);
  return new Intl.NumberFormat("es-CL", { maximumFractionDigits: maxFrac }).format(n);
}

export function fmtPct(v: unknown): string {
  const n = toNum(v);
  return n === null ? "—" : `${dec2.format(n)} %`;
}

export function toNum(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function fmtRows(n: number): string {
  return int0.format(n);
}

export function hoursSince(d: Date | string | null | undefined): number | null {
  if (!d) return null;
  const t = typeof d === "string" ? new Date(d).getTime() : d.getTime();
  if (!Number.isFinite(t)) return null;
  return (Date.now() - t) / 3_600_000;
}

export function freshnessLabel(hours: number | null): string {
  if (hours === null) return "sin datos";
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  if (hours < 48) return `${Math.round(hours)} h`;
  return `${Math.round(hours / 24)} d`;
}

export function relTime(d: Date | string | null | undefined): string {
  const h = hoursSince(d);
  if (h === null) return "—";
  if (h < 1) return "hace minutos";
  if (h < 24) return `hace ${Math.round(h)} h`;
  const days = Math.round(h / 24);
  return days < 30 ? `hace ${days} d` : `hace ${(days / 30).toFixed(1)} meses`;
}

export function fmtDuration(ms: number): string {
  if (ms < 1000) return `${ms} ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(2)} s`;
  return `${(ms / 60_000).toFixed(1)} min`;
}

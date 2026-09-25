import { NextResponse } from "next/server";
import { getDatasets } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function GET() {
  const started = Date.now();
  const { datasets, persist } = await getDatasets();
  return NextResponse.json({
    status: "ok",
    engine: "postgres + sql-ts",
    datasets: datasets.length,
    filas: datasets.reduce((acc, d) => acc + d.filas.length, 0),
    persist,
    latencyMs: Date.now() - started,
    ts: new Date().toISOString(),
  });
}

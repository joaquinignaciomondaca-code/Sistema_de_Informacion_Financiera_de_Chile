import { NextResponse } from "next/server";
import { SqlError, runQuery } from "@/lib/sql";
import { ensureSeed, getDatasets, logEjecucion } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let sql = "";
  try {
    const body = await request.json();
    sql = typeof body?.sql === "string" ? body.sql : "";
  } catch {
    return NextResponse.json({ error: "Cuerpo inválido.", hint: 'Envía { "sql": "SELECT …" }.' }, { status: 400 });
  }

  if (!sql.trim()) {
    return NextResponse.json({ error: "La consulta está vacía.", hint: "Escribe una sentencia SQL o elige un chip de sugerencia." }, { status: 400 });
  }

  const { datasets, persist } = await getDatasets();

  try {
    const result = runQuery(sql, datasets);
    await logEjecucion({ sql, datasetSlug: result.datasetSlug, filas: result.rowCount, ms: result.ms, ok: true });
    return NextResponse.json({ ...result, persist });
  } catch (err) {
    const isSql = err instanceof SqlError;
    const message = err instanceof Error ? err.message : "Error desconocido.";
    const hint = isSql ? (err as SqlError).hint : undefined;
    await logEjecucion({ sql, datasetSlug: null, filas: 0, ms: 0, ok: false, error: message });
    return NextResponse.json({ error: message, hint, persist }, { status: 400 });
  }
}

export async function GET() {
  const seed = await ensureSeed();
  return NextResponse.json({ ...seed });
}

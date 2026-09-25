import { NextResponse } from "next/server";
import { createConsulta, listConsultas } from "@/lib/store";

export const dynamic = "force-dynamic";

export async function GET() {
  const items = await listConsultas();
  return NextResponse.json({ items });
}

export async function POST(request: Request) {
  let titulo = "";
  let sql = "";
  try {
    const body = await request.json();
    titulo = typeof body?.titulo === "string" ? body.titulo.trim() : "";
    sql = typeof body?.sql === "string" ? body.sql.trim() : "";
  } catch {
    return NextResponse.json({ error: "Cuerpo inválido." }, { status: 400 });
  }

  if (!sql) return NextResponse.json({ error: "Falta la consulta SQL." }, { status: 400 });
  if (!titulo) {
    titulo = sql.replace(/\s+/g, " ").slice(0, 48).replace(/[;,]+$/, "");
  }

  const item = await createConsulta({ titulo, sql });
  return NextResponse.json({ item }, { status: 201 });
}

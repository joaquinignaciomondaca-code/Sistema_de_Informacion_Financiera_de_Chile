import { z } from "zod";
import { recentQueries } from "@/server/catalog";
import { MAX_ROWS, runSql } from "@/server/executor";

export const dynamic = "force-dynamic";

const bodySchema = z.object({
  sql: z.string().min(4).max(8000),
  maxRows: z.number().int().min(1).max(MAX_ROWS).optional(),
  slug: z.string().max(64).optional(),
});

export async function POST(req: Request) {
  const parsed = bodySchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return Response.json(
      { ok: false, error: "payload_inválido", details: parsed.error.issues.map((i) => i.message) },
      { status: 400 },
    );
  }
  const actor = req.headers.get("x-mfc-actor") ?? "anon";
  const result = await runSql(parsed.data.sql, { actor, maxRows: parsed.data.maxRows });
  return Response.json(result);
}

export async function GET() {
  return Response.json({ history: await recentQueries(15) });
}

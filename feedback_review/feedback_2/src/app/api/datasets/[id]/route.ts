import { getDatasetDetail } from "@/server/catalog";

export const dynamic = "force-dynamic";

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const detail = await getDatasetDetail(Number(id));
  if (!detail) return Response.json({ error: "not_found" }, { status: 404 });
  return Response.json(detail);
}

import { getCatalogTree } from "@/server/catalog";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const kind = new URL(req.url).searchParams.get("kind") ?? undefined;
  try {
    return Response.json(await getCatalogTree(kind));
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 500 });
  }
}

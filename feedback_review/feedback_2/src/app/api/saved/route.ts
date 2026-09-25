import { z } from "zod";
import { deleteSaved, insertSaved, listSaved, toggleFavorite } from "@/server/catalog";

export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json({ queries: await listSaved() });
}

const postSchema = z.object({
  title: z.string().min(3).max(120),
  sql: z.string().min(8).max(8000),
  description: z.string().max(500).default(""),
});

export async function POST(req: Request) {
  const parsed = postSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) {
    return Response.json({ ok: false, error: parsed.error.issues[0]?.message }, { status: 400 });
  }
  const slug = await insertSaved(parsed.data);
  return Response.json({ ok: true, slug });
}

const patchSchema = z.object({ slug: z.string().min(1), favorite: z.boolean() });

export async function PATCH(req: Request) {
  const parsed = patchSchema.safeParse(await req.json().catch(() => null));
  if (!parsed.success) return Response.json({ ok: false }, { status: 400 });
  await toggleFavorite(parsed.data.slug, parsed.data.favorite);
  return Response.json({ ok: true });
}

export async function DELETE(req: Request) {
  const slug = new URL(req.url).searchParams.get("slug");
  if (!slug) return Response.json({ ok: false }, { status: 400 });
  await deleteSaved(slug);
  return Response.json({ ok: true });
}

import { Workbench } from "@/components/workbench";
import { getCatalogTree, getGraph, listSaved } from "@/server/catalog";

export const dynamic = "force-dynamic";

const INITIAL_SQL = `-- Primera pasada: renta fija por entidad y período, contra la MART gobernada.
-- (nunca contra un parquet suelto: la superficie pública son estas vistas/tablas)
SELECT b.periodo,
       a.nombre                          AS aseguradora,
       b.tipo_bono,
       count(*)                          AS posiciones,
       round(avg(b.tir_mercado_pct), 3)  AS tir_promedio_pct,
       round(sum(b.monto_m_clp))          AS monto_m_clp
FROM mart.vida_bonos b
JOIN mart.dim_aseguradora a ON a.rut = b.rut_aseguradora
GROUP BY 1, 2, 3
ORDER BY b.periodo DESC, monto_m_clp DESC
LIMIT 24;`;

export default async function HomePage() {
  try {
    const [tree, graph, saved] = await Promise.all([
      getCatalogTree("vida"),
      getGraph("vida"),
      listSaved(),
    ]);
    return (
      <Workbench
        initialTree={tree}
        initialGraph={graph}
        initialSaved={saved}
        initialSql={INITIAL_SQL}
      />
    );
  } catch (e) {
    return <SetupNotice message={(e as Error).message} />;
  }
}

function SetupNotice({ message }: { message: string }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-[680px] flex-col justify-center gap-4 p-8">
      <h1 className="text-2xl font-bold">Catálogo no disponible todavía</h1>
      <p className="text-sm leading-relaxed text-[var(--text-dim)]">
        La base de datos está Reachable pero sin el esquema <span className="mono">catalog.*</span> poblado. Ejecuta:
      </p>
      <pre className="rounded-lg border border-[var(--border)] bg-[var(--bg-inset)] p-3 text-xs leading-relaxed">
{`npx drizzle-kit generate --name init
psql "$DATABASE_URL" -f drizzle/0000_init.sql
node scripts/seed.mjs`}
      </pre>
      <p className="mono text-[11px] text-[var(--text-mute)]">error: {message}</p>
    </main>
  );
}

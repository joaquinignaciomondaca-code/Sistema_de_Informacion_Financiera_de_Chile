import { getDatasets, listConsultas } from "@/lib/store";
import {
  Auditoria,
  Fuentes,
  Hero,
  Masthead,
  Pie,
  Serie,
  TablaTenencias,
  Ticker,
} from "@/components/Sections";
import { Workspace } from "@/components/Workspace";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [{ datasets, persist }, consultas] = await Promise.all([getDatasets(), listConsultas()]);
  const bonos = datasets.find((d) => d.slug === "vida.bonos");
  const aseguradoras = datasets.find((d) => d.slug === "vida.aseguradoras");

  return (
    <div className="flex min-h-screen flex-col">
      <Masthead persist={persist} />
      <Ticker />
      <Hero totalDatasets={datasets.length} totalFilas={datasets.reduce((a, d) => a + d.filas.length, 0)} />

      <Workspace initialDatasets={datasets} initialConsultas={consultas} persist={persist} />

      <Serie datasets={datasets} />

      <TablaTenencias dataset={bonos} />

      <Auditoria />

      <Fuentes aseguradoras={aseguradoras} />

      <Pie />
    </div>
  );
}

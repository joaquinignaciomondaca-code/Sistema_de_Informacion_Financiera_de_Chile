import Link from "next/link";
import { ThemePicker } from "@/components/theme-picker";

export const metadata = {
  title: "Revisión de arquitectura · MFC",
  description: "Auditoría de diseño para el Monitor Financiero Chile: referentes, hallazgos y roadmap.",
};

const REFERENTS = [
  {
    name: "Apache Superset — SQL Lab",
    tag: "workbench SQL multiusuario",
    lesson:
      "Separación editor/resultados, guardas de seguridad por base de datos (permisos por schema, statement timeout, límite de filas), consultas guardadas como objeto con dueño y historial de ejecución.",
    copy: "El patrón 'SQL Lab' que ya imitas: ejecuta en el servidor, limita filas, guarda historial y audita. Nada de motor en el cliente para datos sensibles.",
  },
  {
    name: "Metabase",
    tag: "autoservicio para no-analistas",
    lesson:
      "La gente sin SQL no escribe `FROM 'outputs/vida/cartera_bonos.parquet'`. Publica preguntas guardadas, filtros y una semántica de campos (unidades, tipos, descripciones) que la UI consume.",
    copy: "Tipos de campo + unidades en el catálogo → la UI formatea MMCLP/UF/% sola, como hace esta maqueta con fmtCell().",
  },
  {
    name: "Evidence.dev / Lightdash / Rill",
    tag: "BI-as-code",
    lesson:
      "Los reportes son archivos versionados en Git (SQL + markdown / dbt metrics), no filas en una tabla de favoritos del navegador. CI valida que las consultas corran y que los tests pasen.",
    copy: "Tus 6 chips de 'consultas rápidas' deberían vivir en /queries/*.sql, generarse a markdown y publicarse con el run ledger.",
  },
  {
    name: "dbt docs + OpenMetadata / DataHub",
    tag: "catálogo y linaje",
    lesson:
      "El ERD no se dibuja a mano: se deriva del grafo de modelos y de la metadata de columnas. Linaje a nivel de columna, frescura por dataset, dueño, tests y soft-delete de relaciones obsoletas.",
    copy: "Aquí: catalog.dataset_relations se genera desde la metadata de columnas en el seed. Si cambia el modelo, cambia el mapa.",
  },
  {
    name: "DBeaver / Beekeeper / DbGate / Dory",
    tag: "clientes de datos",
    lesson:
      "Explorer jerárquico con búsqueda difusa, acciones al hover (preview, copiar FROM, abrir tabla), pestañas de resultados con grid virtualizado, edición inline sólo con modo seguro, exportación y planes de ejecución.",
    copy: "Tu sidebar apunta al patrón correcto; el detalle que gana usuarios es el grid virtualizado + copiar celda + ordenar sin recargar.",
  },
  {
    name: "huey / dbxlite / datakit (DuckDB-Wasm)",
    tag: "SQL 100 % en navegador",
    lesson:
      "Excelentes como analítica personal sobre datasets públicos o subidos por el usuario: range requests a Parquet, Arrow IPC al worker, OPFS para persistir, export client-side.",
    copy: "Como modo 'offline/what-if' sobre una snapshot de 10-50 MB: brillante. Como plano de datos institucional: no.",
  },
];

const FINDINGS = [
  {
    sev: "crítico",
    title: "El navegador es a la vez motor, almacén y capa de seguridad",
    evidence:
      "DuckDB-Wasm + `SELECT ... FROM 'outputs/vida/cartera_bonos.parquet'`: quien abre la página puede consultar todo; el 'permiso' es la ofuscación.",
    risk:
      "Datos de la CMF/aseguradoras son información confidencial-privada. Un enlace público a tu SPA = fuga de la cartera completa. Además no hay forma de aplicar RLS, enmascarar columnas ni auditar antes de salir.",
    fix:
      "Divide los dos planos: Postgres/DuckDB/MotherDuck en el servidor con un rol read-only por perfil, search_path fijado, statement_timeout, límite duro de filas y allowlist de esquemas. DuckDB-Wasm queda como cache opcional de una snapshot ya autorizada (máx. ~50 MB) y nunca como fuente de verdad.",
    effort: "S · ya aplicado en esta maqueta (src/lib/sql-guard.ts + src/server/executor.ts)",
  },
  {
    sev: "crítico",
    title: "Sin identidad, sin auditoría, sin linaje de quién pidió qué",
    evidence: "No hay actor en la UI ni registro de ejecuciones; los favoritos van a localStorage.",
    risk: "En un entorno supervisado el log 'quién consultó qué, cuántas filas, cuándo' no es opcional (Ley 19.628 de datos personales + exigencias de la CMF sobre información reservada).",
    fix:
      "SSO (Clerk/Auth.js/OIDC del proveedor corporativo) + tabla query_log inmutable (aquí catalog.query_log) + retención. Las consultas guardadas pasan a la BD y, las 'oficiales', a Git con code review.",
    effort: "M",
  },
  {
    sev: "alto",
    title: "Rutas de archivo como API pública",
    evidence: "El chip dice literalmente FROM 'outputs/vida/cartera_bonos.parquet'.",
    risk:
      "Cada re-run del pipeline que cambie un nombre de carpeta rompe seis consultas de los usuarios, sin versionado, sin deprecación, sin tests. El consumidor queda acoplado al layout de un directorio.",
    fix:
      "Expone una capa semántica estable: vistas/martes gobernadas (aquí mart.v_inversion_consolidada y mart.v_maestro_aseguradoras) + sinónimos. El consumidor escribe contra `v_inversion_consolidada`, tú reordenas los parquet detrás.",
    effort: "S",
  },
  {
    sev: "alto",
    title: "El ERD se mantiene a mano",
    evidence: "erd_graph.js con nodos/aristas estáticos + breadcrumb 'Seguros de Vida > Circular 1835'.",
    risk: "El diagrama se pudre a la segunda semana y la gente empieza a desconfiar de todo el monitor (el peor fallo de un catálogo).",
    fix:
      "Genera nodos y aristas desde la metadata (PK/FK declaradas, claves conformadas, definiciones de vista parseadas con sqlglot). Layout automático con elkjs/dagre por capa dim→fact→view; nada de coordenadas escritas a mano.",
    effort: "M · en esta maqueta el mapa sale 100 % de catalog.dataset_relations",
  },
  {
    sev: "alto",
    title: "Sin contrato de datos ni frescura observable",
    evidence: "Badge 'DuckDB-Wasm Activo' como única señal de salud; ningún dataset dice cuándo se materializó por última vez.",
    risk: "Un monitor financiero que muestra datos de hace 4 meses sin avisar es peor que no tener monitor.",
    fix:
      "Por dataset: dueño, granularidad, cadencia, max_age (SLO), row_count medido, schema_version, expectativas de calidad y run ledger (watermark, rows_in/out/dropped, commit_sha). UI con semáforo ok/warn/breach en el árbol, el mapa y la ficha.",
    effort: "M · aplicado (catalog.ingest_runs + quality_checks + freshness dots)",
  },
  {
    sev: "medio",
    title: "Resultados como 'chat'",
    evidence: "message-bot / message-user y cada corrida como burbuja.",
    risk:
      "Precioso en una demo, incómodo en el día 30: no hay ordenación por columna, ni copiar celda, ni paginación, ni comparar dos consultas, y el scroll se vuelve inmanejable con grids de 200 filas.",
    fix:
      "Consola con pestañas Tabla / Gráfico / JSON / Auditoría, grid con sort + copy + formato por unidad, y una cola de ejecuciones en lugar de un hilo conversacional. Deja el chat para un asistente NL→SQL encima del mismo guard.",
    effort: "S · aplicado",
  },
  {
    sev: "medio",
    title: "Sin virtualización ni presupuesto de render",
    evidence: "tables DOM completas + canvas del grafo dibujado sin ResizeObserver ni devicePixelRatio.",
    risk: "Con 40 datasets × 30 columnas y 400 filas el layout se cuelga; en pantallas HiDPI el canvas se ve borroso.",
    fix:
      "@tanstack/react-virtual para el grid, SVG (como aquí) o canvas con DPR y ResizeObserver, y recorte de columnas/filas en el servidor antes de serializar. Presupuesto: < 250 KB de JSON por página de resultados.",
    effort: "S",
  },
  {
    sev: "medio",
    title: "CSS con colores hardcodeados y alturas mágicas",
    evidence:
      "#191E29 repetido en body/canvas/panel, `.app-layout { height: calc(100vh - 45px) }`, `.sidebar.collapsed { margin-left: -320px }` con un sidebar arrastrable de 220-550 px.",
    risk: "El tema 'Bloomberg' pinta paneles azul marino, el layout se rompe al cambiar el alto del header y colapsar el sidebar deja un hueco cuando el usuario lo redimensionó.",
    fix:
      "Todos los colores desde tokens por tema (5 paletas en esta maqueta, incluida una clara para imprimir el informe), layout `flex` + `min-h-0`, colapso con `width:0` en lugar de margen negativo, y `focus-visible` + AA en los tokens de texto.",
    effort: "S · aplicado",
  },
  {
    sev: "medio",
    title: "Vanilla JS con 6 globales y window.*",
    evidence: "new window.ERDGraph(...), window.ChatTerminal, window.SidebarNav, sin módulos ni tipos.",
    risk: "Sin tipos no hay refactor seguro; sin bundler no hay code-splitting, ni tests unitarios, ni tree-shaking del WASM.",
    fix:
      "Next/React + TypeScript con tipos compartidos entre servidor y cliente (src/lib/types.ts aquí) y Drizzle como capa de datos: el catálogo pasa a ser type-safe y testeable.",
    effort: "M · aplicado",
  },
  {
    sev: "bajo",
    title: "Sin estado compartible ni accesibilidad",
    evidence: "Nada en la URL; roles ARIA ausentes; atajos inexistentes.",
    risk: "La gente reproduce análisis por captura de pantalla. Y sin roles, el árbol y los dropdowns son invisibles para lector de pantalla.",
    fix:
      "Estado en la query string (kind/dataset/q/autorun → 'Compartir link' real), paleta ⌘K, navegación con flechas en el árbol, role=tree/treeitem/listbox/option y anillo de foco visible.",
    effort: "S · aplicado",
  },
];

const CHECKLIST = [
  ["Ingesta idempotente", "upsert por (dataset, watermark) + overwrite por partición; reintentos no duplican filas."],
  ["Overlap y reconciliación", "crawl incremental con ventana de solapamiento, snapshot completo periódico y reconciliación de borrados (soft-delete)."],
  ["Contrato publicado", "YAML junto al modelo: grain, SLA de frescura, expectativas, dueños, política de acceso, schema_version."],
  ["Calidad en el pipeline", "not_null / unique / range / row_count corriendo post-run; el resultado se expone, la UI nunca recalcula."],
  ["Archivos para range reads", "Parquet 128-512 MB, particionado por periodo=<YYYY-MM>/, con manifest; si sirve por HTTP: CORS + Accept-Ranges."],
  ["Privacidad por diseño", "rol de sólo lectura, columnas sensibles enmascaradas en el servidor, RLS por dominio, límites de extracción, log de accesos."],
  ["Consultas como código", "queries/*.sql versionados + test de que corren; lo experimental en la BD, lo oficial en Git."],
  ["Presupuestos de plataforma", "p95 < 1,5 s para proyecciones de < 100 KB; 100 % de datasets con dueño+descripción+tests; < 2 % consultas bloqueadas por el guard."],
];

export default function ReviewPage() {
  return (
    <main className="mx-auto max-h-screen overflow-y-auto px-6 py-8">
      <div className="mx-auto max-w-[920px]">
        <header className="mb-8 flex flex-wrap items-center gap-3 border-b border-[var(--border)] pb-5">
          <span className="mono rounded-md px-2 py-[3px] text-[10.5px] font-extrabold tracking-[0.8px]" style={{ background: "var(--accent)", color: "var(--accent-ink)" }}>
            MFC
          </span>
          <div>
            <h1 className="text-[22px] leading-tight font-bold tracking-[-0.4px]">Revisión de arquitectura y feedback</h1>
            <p className="text-[12px] text-[var(--text-dim)]">
              Monitor Financiero Chile · comparado con Superset, Metabase, Evidence, dbt docs/OpenMetadata, DBeaver y las apps DuckDB-Wasm del ecosistema.
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Link href="/" className="btn focus-ring">
              ← Volver al monitor
            </Link>
            <ThemePicker />
          </div>
        </header>

        <section className="mb-8 grid gap-3 md:grid-cols-3">
          <Card title="Veredicto" tone="var(--ok)">
            La idea (un workbench único donde se explora el mapa, se consulta y se comparte) es exactamente el producto que falta en ese mundo. El diseño visual ya está
            maduro; la arquitectura de datos es lo que hay corregir.
          </Card>
          <Card title="Qué duele hoy" tone="var(--bad)">
            El navegador hace de motor, almacén y control de acceso a la vez, las rutas de archivo son la API y el ERD es decorativo. Ninguna de las tres se arregla
            parcheando CSS.
          </Card>
          <Card title="Por dónde empezar" tone="var(--warn)">
            Catálogo en Postgres + ejecutor read-only en el servidor + vistas gobernadas. Con eso, todo lo demás (mapa, chips, favoritos, auditoría) pasa a ser
            consecuencia de la metadata en vez de mantenimiento manual.
          </Card>
        </section>

        <section className="mb-8">
          <SectionTitle>1 · Referentes y qué copiar de cada uno</SectionTitle>
          <div className="overflow-hidden rounded-xl border border-[var(--border)]">
            <table className="w-full border-collapse text-[12px]">
              <thead>
                <tr>
                  <th className="th">Proyecto</th>
                  <th className="th">Categoría</th>
                  <th className="th">Lo que enseñan</th>
                  <th className="th">Aplicado a tu caso</th>
                </tr>
              </thead>
              <tbody>
                {REFERENTS.map((r) => (
                  <tr key={r.name} className="align-top hover:bg-[var(--bg-hover)]">
                    <td className="td font-semibold">{r.name}</td>
                    <td className="td text-[var(--text-dim)]">{r.tag}</td>
                    <td className="td whitespace-normal text-[var(--text-dim)]">{r.lesson}</td>
                    <td className="td whitespace-normal text-[var(--text)]">{r.copy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mb-8">
          <SectionTitle>2 · Hallazgos en tu código, con evidencia y corrección</SectionTitle>
          <div className="flex flex-col gap-2.5">
            {FINDINGS.map((f) => (
              <article key={f.title} className="rounded-xl border p-3.5" style={{ borderColor: f.sev === "crítico" ? "var(--bad)" : f.sev === "alto" ? "var(--warn)" : "var(--border)" }}>
                <div className="mb-1.5 flex flex-wrap items-center gap-2">
                  <span className="tag" style={{ color: f.sev === "crítico" ? "var(--bad)" : f.sev === "alto" ? "var(--warn)" : "var(--text-dim)", borderColor: "currentColor" }}>
                    {f.sev}
                  </span>
                  <h3 className="text-[13.5px] font-bold">{f.title}</h3>
                  <span className="mono ml-auto text-[10px] text-[var(--text-mute)]">esfuerzo {f.effort}</span>
                </div>
                <dl className="grid gap-1.5 text-[11.5px] leading-relaxed sm:grid-cols-[92px_1fr]">
                  <dt className="text-[var(--text-mute)]">Evidencia</dt>
                  <dd className="mono text-[var(--text-dim)]">{f.evidence}</dd>
                  <dt className="text-[var(--text-mute)]">Riesgo</dt>
                  <dd className="text-[var(--text-dim)]">{f.risk}</dd>
                  <dt className="text-[var(--text-mute)]">Corrección</dt>
                  <dd className="text-[var(--text)]">{f.fix}</dd>
                </dl>
              </article>
            ))}
          </div>
        </section>

        <section className="mb-8 grid gap-4 lg:grid-cols-2">
          <div>
            <SectionTitle>3 · Arquitectura objetivo</SectionTitle>
            <pre className="mono inset overflow-x-auto rounded-xl p-3 text-[10.5px] leading-[1.6] whitespace-pre">
{`┌────────────────────────── fuente ──────────────────────────┐
│ CMF / Circulares · Form. B-7 · Ley 18.815 · Ley 20.712     │
└───────────────┬────────────────────────────────────────────┘
                ▼  ingesta idempotente (watermark + overlap)
   raw parquet en object storage (s3/r2), particionado
                ▼  dbt / SQLMesh  (modelos = código, CI + tests)
   staging ──► mart (hechos conformados) ──► vistas gobernadas v_*
                │        ▲
                │        └── Postgres: catálogo, runs, checks, saved, auditoría
                ▼
   API Next.js  ── guard read-only · timeout · row cap · RLS · cache 30s
                ▼
   UI  explorer · mapa auto-derivado · consola · fichas · auditoría
                └─(opcional) DuckDB-Wasm = cache de una snapshot autorizada)`}
            </pre>
          </div>
          <div>
            <SectionTitle>4 · Lo que debería exigir cada dataset</SectionTitle>
            <ul className="flex flex-col gap-1.5">
              {CHECKLIST.map(([k, v]) => (
                <li key={k} className="raised flex gap-2 rounded-lg p-2.5 text-[11.5px] leading-relaxed">
                  <span className="mono shrink-0 font-semibold" style={{ color: "var(--accent)" }}>
                    {k}
                  </span>
                  <span className="text-[var(--text-dim)]">{v}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="mb-8">
          <SectionTitle>5 · Roadmap sugerido (4 sprints)</SectionTitle>
          <div className="grid gap-2.5 md:grid-cols-2">
            <Card title="S1 · Base gobernada" tone="var(--accent)">
              Catálogo en Postgres (domains/datasets/columns), ejecutor read-only con guard + timeout + límite, 3 mart views publicadas. <em>Criterio:</em> la consola
              ya no toca archivos y toda corrida deja registro.
            </Card>
            <Card title="S2 · Confiabilidad visible" tone="var(--info)">
              Run ledger + quality checks post-run + SLO de frescura por dataset. <em>Criterio:</em> un retraso de la fuente CMF se ve en el árbol antes de que alguien
              pregunte “¿por qué bajó la cobertura?”.
            </Card>
            <Card title="S3 · Mapa y linaje reales" tone="var(--warn)">
              Relaciones derivadas de metadata + parseo de las vistas (sqlglot), layout con elkjs, drill-down a columnas. <em>Criterio:</em> cambiar un modelo mueve el
              diagrama sin tocar la UI.
            </Card>
            <Card title="S4 · Consumo y distribución" tone="var(--ok)">
              Queries as code en Git, suscripciones/alertas (SLA roto → Slack/correo), informe imprimible y API para que otros equipos consuman la capa semántica.
              <em>Criterio:</em> el reporte mensual sale del monitor, no de un Excel pegado.
            </Card>
          </div>
        </section>

        <section className="mb-8">
          <SectionTitle>6 · Lo que ya está bien y no tocaría</SectionTitle>
          <ul className="grid gap-2 text-[12px] leading-relaxed md:grid-cols-2">
            {[
              "Tres paneles (explorador / mapa / consola) con splitters arrastrables: el 90 % de los workbench comerciales lo hace peor.",
              "Sistema de temas por tokens + paleta persistida: está bien pensado, sólo había que eliminar los hex sueltos.",
              "Modo terminal con prefijo de prompt: le da identidad al producto; conviene conservarlo como tecla estética.",
              "Chips de consultas sugeridas: muy buena avenida de adopción; ahora apuntan a vistas gobernadas y viven en la BD.",
              "Foco en el dominio regulatorio (circular por dataset): es tu foso competitivo; genéralo como metadata, no como texto en la UI.",
            ].map((t) => (
              <li key={t} className="raised rounded-lg p-2.5">
                {t}
              </li>
            ))}
          </ul>
        </section>

        <footer className="mono border-t border-[var(--border)] pt-4 text-[10.5px] leading-relaxed text-[var(--text-mute)]">
          <p>
            Nota: los datos de esta maqueta son <strong style={{ color: "var(--warn)" }}>sintéticos</strong> y deterministas (scripts/seed.mjs). Las referencias
            normativas (Circular 1835/1836, Formulario B-7, Leyes 18.815 y 20.712) se usan como estructura de ejemplo, no como fuente autorizada.
          </p>
          <p className="mt-1">
            Fuentes de la comparación: docs y repos de Apache Superset (SQL Lab), Metabase, Evidence.dev, Lightdash, Rill, dbt docs, OpenMetadata/DataHub, DBeaver,
            Beekeeper Studio, DbGate, y las apps DuckDB-Wasm (huey, dbxlite, datakit), con las notas del ecosistema sobre CORS+Range, límites de memoria del tab y
            que WASM no sirve para multiusuario/RLS.
          </p>
        </footer>
      </div>
    </main>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="mb-3 text-[11px] font-bold tracking-[1.1px] text-[var(--accent)] uppercase">{children}</h2>;
}

function Card({ title, children, tone }: { title: string; children: React.ReactNode; tone: string }) {
  return (
    <article className="panel rounded-xl p-3.5" style={{ borderColor: tone }}>
      <h3 className="mb-1.5 text-[12px] font-bold tracking-[0.2px]" style={{ color: tone }}>
        {title}
      </h3>
      <p className="text-[11.5px] leading-relaxed text-[var(--text-dim)]">{children}</p>
    </article>
  );
}

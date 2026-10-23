#!/usr/bin/env node
/**
 * Descubrir el contrato desde JavaScript, sin motor SQL.
 *
 * Una aplicación web o un script de Node que solo quiere saber qué hay y dónde
 * está no necesita DuckDB: `catalog.json` y `queries.json` son dos `fetch`.
 * Aquí se comprueba que el catálogo sea coherente —90 objetos, ids únicos,
 * rutas declaradas— y se imprime el reparto por sector.
 *
 *   node examples/javascript/catalogo.mjs
 *   SIF_CHILE_BASE=http://127.0.0.1:8000 node examples/javascript/catalogo.mjs
 *
 * `SIF_CHILE_BASE` tiene que ser una URL: si trabajas contra una copia local,
 * sírvela con `python3 -m scripts.preview_no_cache --port 8000`.
 */
const CANONICA = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile";
const BASE = (process.env.SIF_CHILE_BASE ??
  "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile").replace(/\/+$/, "");

// El catálogo publica URLs absolutas del sitio; si se mira un espejo o una copia
// local, se cambia el prefijo y no se toca nada más.
const enBase = (url) => (url.startsWith(CANONICA) ? BASE + url.slice(CANONICA.length) : url);

async function json(ruta) {
  const respuesta = await fetch(`${BASE}/${ruta}`, { signal: AbortSignal.timeout(30_000) });
  if (!respuesta.ok) throw new Error(`${ruta}: HTTP ${respuesta.status}`);
  return respuesta.json();
}

const catalogo = await json("api/v2/catalog.json");
const consultas = await json("api/v2/queries.json");

const objetos = catalogo.objetos ?? [];
const ids = new Set(objetos.map((o) => o.id));

if (objetos.length !== catalogo.totales.objetos) {
  throw new Error(`el catálogo dice ${catalogo.totales.objetos} objetos y trae ${objetos.length}`);
}
if (ids.size !== objetos.length) throw new Error("hay ids repetidos en el catálogo");
if (consultas.consultas.length !== catalogo.totales.consultas) {
  throw new Error(`el catálogo dice ${catalogo.totales.consultas} consultas y hay ${consultas.consultas.length}`);
}
for (const objeto of objetos) {
  if (!objeto.esquema || !objeto.particiones_url) throw new Error(`${objeto.id}: le faltan rutas en el catálogo`);
}

// Dos rutas de verdad, para no dar por bueno un contrato que solo se describe.
const muestra = objetos.find((o) => o.estado === "publicado");
for (const ruta of [enBase(muestra.esquema), enBase(muestra.particiones_url)]) {
  const respuesta = await fetch(ruta, { method: "HEAD", signal: AbortSignal.timeout(30_000) });
  if (!respuesta.ok) throw new Error(`${ruta}: HTTP ${respuesta.status}`);
}

const porSector = new Map();
for (const { sector } of objetos) porSector.set(sector, (porSector.get(sector) ?? 0) + 1);

console.log(`Contrato en ${BASE}`);
console.log(`data_release ${catalogo.data_release} · ${objetos.length} objetos · ${consultas.consultas.length} consultas\n`);
console.log("objetos por sector");
for (const [sector, n] of [...porSector].sort((a, b) => b[1] - a[1])) {
  console.log(`  ${sector.padEnd(14)} ${String(n).padStart(3)}`);
}

const ejemplo = consultas.consultas[0];
console.log("\nuna consulta publicada, por id estable:");
console.log(`  ${ejemplo.id}`);
console.log(`  ${ejemplo.sql.split("\n")[0].slice(0, 70)}…`);

if (!objetos.length || !consultas.consultas.length) throw new Error("el contrato llegó vacío");
console.log(`\nOK · catálogo coherente, ${ids.size} ids únicos y las rutas de ${muestra.id} responden`);

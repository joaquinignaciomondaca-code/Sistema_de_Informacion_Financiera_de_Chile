#!/usr/bin/env node
/**
 * Prueba de la lógica de registro de vistas de docs/js/duckdb_client.js,
 * sin navegador: se carga el script en un contexto Node con fetch, document y
 * window emulados, y se comprueba el comportamiento de registerSemanticViews:
 *
 *   * todas las vistas semánticas (según SEMANTIC_VIEWS) y sus alias de compatibilidad se crean todas,
 *   * los Parquet se registran una sola vez aunque varias vistas los compartan,
 *   * el SQL generado coincide con el fichero real de cada vista (el mismo
 *     arnés de scripts/audit_consultas_sugeridas.py debe poder ejecutarlo),
 *   * un manifiestro inexistente desactiva solo su vista (fail-closed), sin
 *     tumbar el arranque.
 *
 * Uso: node scripts/audit_duckdb_client.js
 * No requiere dependencias (ni jsdom): el motor no se instancia, sólo se
 * ejercita la lógica de registro sobre los archivos publicados.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.dirname(__dirname);
const DOCS = path.join(ROOT, "docs");
const CLIENTE = path.join(DOCS, "js", "duckdb_client.js");

let fallos = 0;
function check(nombre, ok, extra = "") {
  console.log(`${ok ? "OK   " : "FALLA"}  ${nombre}${ok || !extra ? "" : "  -> " + extra}`);
  if (!ok) fallos++;
}

// --- Contexto emulado -------------------------------------------------------
// fetch lee manifiestos del disco; todo lo que no existe responde 404 para
// simular el servidor. document y window son lo justo para cargar el script.
const fetchCalls = { manifiestos: 0, urls: [] };
function emularFetch(url) {
  const relativo = String(url).replace(/^.*?:\/\/[^/]+\//, "");
  fetchCalls.urls.push(relativo);
  if (relativo.endsWith(".json")) {
    fetchCalls.manifiestos++;
    const ruta = path.join(DOCS, relativo);
    if (fs.existsSync(ruta)) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(JSON.parse(fs.readFileSync(ruta, "utf8"))) });
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error("404")) });
  }
  return Promise.reject(new Error("fetch inesperado: " + url));
}

const createdViews = [];
const registeredFiles = new Set();
const registeredUrls = [];
const contexto = {
  console,
  URL,
  Promise,
  WebAssembly: { validate: () => true },
  setTimeout, clearTimeout,
  CustomEvent: function (t, d) { this.type = t; this.detail = d && d.detail; },
  fetch: (url) => emularFetch(url),
  document: {
    baseURI: "https://sitio.local/",
    getElementById: () => null,
  },
  window: { dispatchEvent: () => true },
  __connStub: { query: (sql) => { createdViews.push(sql); return Promise.resolve({}); } },
  __dbStub: {
    registerFileURL: (rel, abs, proto, persist) => { registeredFiles.add(rel); registeredUrls.push(abs); return Promise.resolve(); },
  },
};
contexto.window.DuckDBClient = null;
vm.createContext(contexto);

let fuente = fs.readFileSync(CLIENTE, "utf8");
// Conteos esperados derivados del propio catálogo de vistas (no literales a mano).
const DECLARACIONES = [...fuente.matchAll(/\{\s*name:\s*"[a-z0-9_]+"[^{}]*\}/g)].map(([declaracion]) => declaracion);
const N_VISTAS = DECLARACIONES.filter((vista) => /\b(?:file|manifest):/.test(vista)).length;
const N_MANIFIESTOS = DECLARACIONES.filter((vista) => /\bmanifest:/.test(vista)).length;
const N_MANIFIESTOS_DIRECTOS = DECLARACIONES.filter((vista) => /\bmanifest:/.test(vista) && !/\bqueryFile:/.test(vista)).length;
const VISTAS_SQL_COMPACTAS = DECLARACIONES.filter((vista) => /\bqueryFile:/.test(vista));
const VISTAS_SIN_PARTICIONES = [...fuente.matchAll(/\{\s*name:\s*"([a-z0-9_]+)"\s*,\s*manifest:\s*"([^"]+)"/g)]
  .filter(([, , manifest]) => {
    const ruta = path.join(DOCS, manifest);
    return fs.existsSync(ruta) && !(JSON.parse(fs.readFileSync(ruta, "utf8")).files || []).length;
  })
  .map(([, name]) => name);
const N_VISTAS_PUBLICADAS = N_VISTAS - VISTAS_SIN_PARTICIONES.length;
// No se instancia el motor de verdad: el script termina creando
// window.DuckDBClient = new DuckDBClient(); y eso dispararía init() sobre
// archivos de red. Se corta ahí y se recupera la clase para probarla.
const corte = fuente.indexOf("window.DuckDBClient = new DuckDBClient();");
if (corte === -1) { console.log("FALLA  no se encontró la instancia global en duckdb_client.js"); process.exit(1); }
vm.runInContext(fuente.slice(0, corte) + "\nglobalThis.__DuckDBClient = DuckDBClient;", contexto);

(async () => {
  const DuckDBClient = contexto.__DuckDBClient;
  const protocolo = { DuckDBDataProtocol: { HTTP: 4 } };
  const cliente = Object.create(DuckDBClient.prototype);
  cliente.db = contexto.__dbStub;
  cliente.conn = contexto.__connStub;
  cliente.duckdb = protocolo;
  cliente.isReady = true;
  cliente.registeredFiles = new Set();
  cliente.engineAvailable = true;
  cliente.unavailableViews = [];

  // 1) Arranque completo con todos los manifiestos presentes.
  await cliente.registerSemanticViews();
  const principales = createdViews.filter((s) => s.includes("read_parquet"));
  check(`se crean las ${N_VISTAS_PUBLICADAS} vistas con particiones publicadas`, principales.length === N_VISTAS_PUBLICADAS, `${principales.length}`);
  check("las vistas sin particiones se reportan explícitamente como no publicadas",
    VISTAS_SIN_PARTICIONES.every((name) => cliente.unavailableViews.includes(name)) &&
    cliente.unavailableViews.length === VISTAS_SIN_PARTICIONES.length,
    cliente.unavailableViews.join(", "));
  const alias = createdViews.length - principales.length;
  check("se crean los 19 alias de compatibilidad", alias === 19, `${alias}`);
  check("las vistas particionadas usan su compacto SQL sin pedir sus manifiestos de descarga", fetchCalls.manifiestos === N_MANIFIESTOS_DIRECTOS, `${fetchCalls.manifiestos} solicitudes; ${N_MANIFIESTOS_DIRECTOS} vistas requieren manifiesto`);
  check("los compactos SQL conservan los manifiestos particionados independientes para descargas",
    N_MANIFIESTOS - N_MANIFIESTOS_DIRECTOS === VISTAS_SQL_COMPACTAS.length &&
    VISTAS_SQL_COMPACTAS.every((vista) => vista.includes("manifest:")),
    `${N_MANIFIESTOS - N_MANIFIESTOS_DIRECTOS} manifiestos compactados / ${VISTAS_SQL_COMPACTAS.length} compactos`);
  const compactasEsperadas = ["bancos_balance", "bancos_resultados", "ffmm_cartera_nacional", "seguros_acciones"];
  check("las cuatro vistas de alto costo usan los Parquet compactos SQL-only",
    VISTAS_SQL_COMPACTAS.length === compactasEsperadas.length && compactasEsperadas.every((name) =>
      principales.some((sql) => sql.includes(`outputs/sql_query/${name}.parquet`))),
    `${VISTAS_SQL_COMPACTAS.length} compactos declarados`);
  // 2) El SQL de cada vista apunta a ficheros que existen en docs/.
  const rutasEnSql = new Set();
  for (const sql of principales) {
    const m = sql.match(/read_parquet\(([^)]*)\)/);
    if (!m) continue;
    for (const ruta of m[1].matchAll(/'([^']+)'/g)) rutasEnSql.add(ruta[1]);
  }
  const faltantes = [...rutasEnSql].filter((r) => !fs.existsSync(path.join(DOCS, r)));
  check("todas las rutas del SQL existen en docs/", faltantes.length === 0, faltantes.slice(0, 3).join(", "));
  check("cada Parquet se registra una sola vez", registeredFiles.size === rutasEnSql.size,
    `${registeredFiles.size} vs ${rutasEnSql.size}`);
  // 2b) Las URL registradas deben salir de la caché HTTP del navegador:
  //     Chrome/Edge en Windows entrega respuestas de rango corridas tras un
  //     recargo y el parser Thrift de Parquet falla con TProtocolException
  //     (duckdb/duckdb-wasm#1658). registerFile añade "?cb=<carga>" por eso.
  const sinBuster = registeredUrls.filter((u) => !/[?&]cb=/.test(u));
  check("las URL de Parquet llevan el sufijo anti-caché (?cb=...)", sinBuster.length === 0,
    sinBuster.slice(0, 3).join(", "));

  // 3) Fail-closed: un manifiestro ausente solo desactiva su vista.
  const vistas3 = [];
  const cliente2 = Object.create(DuckDBClient.prototype);
  cliente2.db = { registerFileURL: (rel) => { registeredFiles.add(rel); return Promise.resolve(); } };
  cliente2.conn = { query: (sql) => { vistas3.push(sql); return Promise.resolve({}); } };
  cliente2.duckdb = protocolo;
  cliente2.registeredFiles = new Set();
  cliente2.engineAvailable = true;
  cliente2.unavailableViews = [];
  const fetchReal = contexto.fetch;
  const errorReal = contexto.console.error;
  contexto.fetch = (url) => {
    if (String(url).includes("fi/bienes_raices/manifest.json")) {
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.reject(new Error("404")) });
    }
    return fetchReal(url);
  };
  contexto.console = { ...contexto.console, error: () => {} }; // el 404 es esperado
  await cliente2.registerSemanticViews();
  contexto.console = { ...contexto.console, error: errorReal };
  const noDisponiblesEsperadas = [...new Set([...VISTAS_SIN_PARTICIONES, "fi_bienes_raices"])].sort();
  check("un manifiesto 404 desactiva solo su vista, además de las tablas sin filas",
    JSON.stringify([...cliente2.unavailableViews].sort()) === JSON.stringify(noDisponiblesEsperadas),
    JSON.stringify(cliente2.unavailableViews));
  check("las demás vistas siguen creadas",
    vistas3.filter((s) => s.includes("read_parquet")).length === N_VISTAS - noDisponiblesEsperadas.length,
    `${vistas3.filter((s) => s.includes("read_parquet")).length}`);
  contexto.fetch = fetchReal;

  // 4) Una consulta prepara solo la vista solicitada; una tabla sin datos
  //    devuelve un mensaje explícito en vez de un error de catálogo engañoso.
  const clienteLazy = Object.create(DuckDBClient.prototype);
  clienteLazy.db = contexto.__dbStub;
  clienteLazy.conn = contexto.__connStub;
  clienteLazy.duckdb = protocolo;
  clienteLazy.registeredFiles = new Set();
  clienteLazy.queryQueue = Promise.resolve();
  clienteLazy.unavailableViews = [];
  clienteLazy.viewErrors = {};
  clienteLazy.viewPromises = new Map();
  clienteLazy.createdViews = new Set();
  const antesLazy = createdViews.length;
  await clienteLazy.ensureSemanticViewsForQuery("SELECT * FROM seguros_registros_tipo6 LIMIT 100");
  const sqlLazy = createdViews.slice(antesLazy);
  check("una consulta crea solo la vista tipo 6 que necesita",
    sqlLazy.length === 1 && sqlLazy[0].includes("outputs/seguros/registros_tipo6/"),
    `${sqlLazy.length} sentencia(s)`);
  let errorSinDatos = "";
  try {
    await clienteLazy.ensureSemanticViewsForQuery("SELECT * FROM seguros_prestamos LIMIT 100");
  } catch (err) { errorSinDatos = err.message; }
  check("una vista con manifiesto vacío falla con causa explícita, no como tabla inexistente",
    /seguros_prestamos.*No hay particiones publicadas/.test(errorSinDatos), errorSinDatos);
  check("una tabla sin particiones no genera CREATE VIEW", createdViews.length === antesLazy + 1,
    `${createdViews.length - antesLazy} sentencia(s)`);

  // 5) enTandas respeta la concurrencia máxima.
  let activos = 0, maximo = 0;
  await cliente.enTandas([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3, async () => {
    activos++; maximo = Math.max(maximo, activos);
    await new Promise((r) => setTimeout(r, 1));
    activos--;
  });
  check("enTandas nunca supera la concurrencia máxima", maximo <= 3, `máximo ${maximo}`);

  // 5b) Una consulta con muchas tablas no dispara más de cuatro preparaciones
  //     remotas simultáneas desde una pestaña.
  let vistasActivas = 0, maximoVistas = 0, vistasPreparadas = 0;
  const clienteLimitado = Object.create(DuckDBClient.prototype);
  clienteLimitado.ensureSemanticView = async () => {
    vistasActivas++;
    maximoVistas = Math.max(maximoVistas, vistasActivas);
    await new Promise((r) => setTimeout(r, 2));
    vistasActivas--;
    vistasPreparadas++;
  };
  const nombresConsultaAmplia = ["macro_uf", "macro_utm", "macro_cobre", "macro_imacec", "macro_inflacion_ipc"];
  await clienteLimitado.ensureSemanticViewsForQuery(`SELECT * FROM ${nombresConsultaAmplia.join(", ")}`);
  check("la preparación de vistas en una consulta amplia está limitada a cuatro",
    maximoVistas <= 4 && vistasPreparadas === nombresConsultaAmplia.length,
    `máximo ${maximoVistas}; preparadas ${vistasPreparadas}`);

  // 5c) Dos vistas de la misma partición/manifiesto comparten un solo GET.
  const clienteManifiestos = Object.create(DuckDBClient.prototype);
  clienteManifiestos.manifestPromises = new Map();
  const antesManifiestos = fetchCalls.manifiestos;
  const manifestCompartido = "outputs/ffmm/cartera_extranjera/manifest.json";
  await Promise.all([
    clienteManifiestos.prepararVista({ name: "vista_a", manifest: manifestCompartido }),
    clienteManifiestos.prepararVista({ name: "vista_b", sourceManifest: manifestCompartido, latestManifestFile: true })
  ]);
  check("vistas que comparten manifiesto deduplican la petición HTTP",
    fetchCalls.manifiestos - antesManifiestos === 1,
    `${fetchCalls.manifiestos - antesManifiestos} GET`);
  await clienteManifiestos.prepararVista({ name: "vista_reciente", manifest: manifestCompartido });
  check("un manifiesto se vuelve a consultar en una preparación posterior",
    fetchCalls.manifiestos - antesManifiestos === 2,
    `${fetchCalls.manifiestos - antesManifiestos} GET`);

  // 5d) Registros concurrentes del mismo Parquet se consolidan en una operación.
  let registrosDuplicados = 0;
  const clienteArchivos = Object.create(DuckDBClient.prototype);
  clienteArchivos.registeredFiles = new Set();
  clienteArchivos.fileRegistrationPromises = new Map();
  clienteArchivos.duckdb = protocolo;
  clienteArchivos.db = { registerFileURL: async () => {
    registrosDuplicados++;
    await new Promise((r) => setTimeout(r, 2));
  } };
  await Promise.all([
    clienteArchivos.registerFile("outputs/macro/macro_uf.parquet"),
    clienteArchivos.registerFile("outputs/macro/macro_uf.parquet")
  ]);
  check("el mismo Parquet no se registra dos veces en paralelo", registrosDuplicados === 1,
    `${registrosDuplicados} registros`);

  // 5e) Las consultas sobre una misma conexión deben serializarse aunque
  //    distintos componentes las disparen al mismo tiempo. Esto reproduce la
  //    condición que en el navegador producía TProtocolException: Invalid data.
  let consultasActivas = 0, maximoConsultas = 0;
  const cliente3 = Object.create(DuckDBClient.prototype);
  cliente3.queryQueue = Promise.resolve();
  cliente3.conn = { query: async (sql) => {
    consultasActivas++;
    maximoConsultas = Math.max(maximoConsultas, consultasActivas);
    await new Promise((r) => setTimeout(r, 1));
    consultasActivas--;
    return { sql };
  } };
  await Promise.all(["uno", "dos", "tres", "cuatro"].map((sql) => cliente3.runQuerySerial(sql)));
  check("runQuerySerial mantiene una consulta activa por conexión", maximoConsultas === 1,
    `máximo ${maximoConsultas}`);

  console.log(`\n${fallos === 0 ? "CLIENTE DUCKDB: registro de vistas OK" : "CLIENTE DUCKDB: " + fallos + " fallos"}`);
  process.exit(fallos === 0 ? 0 : 1);
})().catch((e) => { console.error("Error de prueba:", e); process.exit(1); });

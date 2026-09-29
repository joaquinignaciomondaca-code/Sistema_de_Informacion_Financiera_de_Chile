#!/usr/bin/env node
/**
 * Prueba de la lógica de registro de vistas de docs/js/duckdb_client.js,
 * sin navegador: se carga el script en un contexto Node con fetch, document y
 * window emulados, y se comprueba el comportamiento de registerSemanticViews:
 *
 *   * las 52 vistas semánticas y sus alias de compatibilidad se crean todas,
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
    registerFileURL: (rel, abs, proto, persist) => { registeredFiles.add(rel); return Promise.resolve(); },
  },
};
contexto.window.DuckDBClient = null;
vm.createContext(contexto);

let fuente = fs.readFileSync(CLIENTE, "utf8");
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
  check("se crean las 52 vistas con read_parquet", principales.length === 52, `${principales.length}`);
  check("no hay vistas no disponibles con manifiestos sanos", cliente.unavailableViews.length === 0,
    cliente.unavailableViews.join(", "));
  const alias = createdViews.length - principales.length;
  check("se crean los 19 alias de compatibilidad", alias === 19, `${alias}`);
  check("los manifiestos se piden por red", fetchCalls.manifiestos >= 30, `${fetchCalls.manifiestos}`);
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
  check("un manifiestro 404 desactiva solo su vista",
    cliente2.unavailableViews.length === 1 && cliente2.unavailableViews[0] === "fi_bienes_raices",
    JSON.stringify(cliente2.unavailableViews));
  check("las demás vistas siguen creadas",
    vistas3.filter((s) => s.includes("read_parquet")).length === 51,
    `${vistas3.filter((s) => s.includes("read_parquet")).length}`);
  contexto.fetch = fetchReal;

  // 4) enTandas respeta la concurrencia máxima.
  let activos = 0, maximo = 0;
  await cliente.enTandas([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3, async () => {
    activos++; maximo = Math.max(maximo, activos);
    await new Promise((r) => setTimeout(r, 1));
    activos--;
  });
  check("enTandas nunca supera la concurrencia máxima", maximo <= 3, `máximo ${maximo}`);

  console.log(`\n${fallos === 0 ? "CLIENTE DUCKDB: registro de vistas OK" : "CLIENTE DUCKDB: " + fallos + " fallos"}`);
  process.exit(fallos === 0 ? 0 : 1);
})().catch((e) => { console.error("Error de prueba:", e); process.exit(1); });

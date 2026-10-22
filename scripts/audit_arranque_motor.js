#!/usr/bin/env node
/**
 * Arranque bajo demanda del motor DuckDB (docs/js/duckdb_client.js).
 *
 * El wasm pesa 3,8 MB transferidos: si el constructor vuelve a llamar a init(),
 * toda visita los paga aunque nunca abra Consultas ni Datos. Esta prueba fija
 * ese contrato sin navegador:
 *
 *   1. cargar el script no arranca el motor ni hace peticiones de red,
 *   2. ensureStarted() arranca una sola vez aunque se llame en paralelo,
 *   3. query() arranca el motor si nadie lo hizo antes,
 *   4. un arranque fallido devuelve un error explícito y no una promesa colgada,
 *   5. mientras arranca, la insignia dice «Inicializando DuckDB…».
 *
 * Uso: node scripts/audit_arranque_motor.js
 * No requiere dependencias.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const CLIENTE = path.join(path.dirname(__dirname), "docs", "js", "duckdb_client.js");

let fallos = 0;
function check(nombre, ok, extra = "") {
  console.log(`${ok ? "OK   " : "FALLA"}  ${nombre}${ok || !extra ? "" : "  -> " + extra}`);
  if (!ok) fallos++;
}

const insignia = { textContent: "" };
let fetchCalls = 0;
const contexto = {
  console, URL, Promise, Math, JSON, Set, Map, Error, String, Number, Object, Array,
  WebAssembly: { validate: () => true },
  performance: { now: () => Date.now() },
  setTimeout, clearTimeout,
  CustomEvent: function (tipo, detalle) { this.type = tipo; this.detail = detalle && detalle.detail; },
  fetch: () => { fetchCalls++; return Promise.reject(new Error("sin red en la prueba")); },
  document: {
    baseURI: "https://sitio.local/",
    getElementById: (id) => (id === "engine-badge" ? insignia : null),
  },
  window: { dispatchEvent: () => true },
};
vm.createContext(contexto);
vm.runInContext(fs.readFileSync(CLIENTE, "utf8"), contexto);

const cliente = contexto.window.DuckDBClient;
if (!cliente) {
  console.log("FALLA  duckdb_client.js no expone window.DuckDBClient");
  process.exit(1);
}

(async () => {
  check("cargar el script no arranca el motor", cliente.initPromise === null);
  check("cargar el script no hace peticiones de red", fetchCalls === 0, `${fetchCalls} fetch`);

  let arranques = 0;
  cliente.init = () => {
    arranques++;
    return Promise.resolve("listo");
  };
  const primera = cliente.ensureStarted();
  const segunda = cliente.ensureStarted();
  check("ensureStarted() es idempotente", primera === segunda && arranques === 1,
    `${arranques} arranque(s)`);
  check("la insignia avisa mientras arranca", /Inicializando DuckDB/.test(insignia.textContent),
    insignia.textContent);
  check("ensureStarted() resuelve con el arranque", (await primera) === "listo");

  // query() debe arrancar por su cuenta y, si el motor no quedó disponible,
  // devolver el error explícito de siempre.
  const otro = Object.create(Object.getPrototypeOf(cliente));
  otro.engineAvailable = false;
  otro.conn = null;
  otro.initPromise = null;
  otro.queryQueue = Promise.resolve();
  otro.revisarSoloLectura = () => ({ ok: true });
  let arrancadoPorQuery = 0;
  otro.init = () => { arrancadoPorQuery++; return Promise.resolve(); };
  const resultado = await otro.query("SELECT 1");
  check("query() arranca el motor si no estaba iniciado", arrancadoPorQuery === 1);
  check("query() informa el motor no disponible tras un arranque fallido",
    resultado.success === false && /no disponible/i.test(resultado.error || ""),
    (resultado.error || "").slice(0, 80));

  console.log(fallos === 0
    ? "\nARRANQUE BAJO DEMANDA: contrato OK"
    : `\nARRANQUE BAJO DEMANDA: ${fallos} fallo(s)`);
  process.exit(fallos === 0 ? 0 : 1);
})();

#!/usr/bin/env node
/**
 * Prueba de comportamiento del cajón del explorador en un teléfono (jsdom).
 *
 * `scripts/audit_movil.py` comprueba que las reglas de CSS y los manejadores
 * existan. Esto comprueba que funcionen: se carga la página con una consulta de
 * medios de 900 px activa —como en un teléfono— y se toca el botón, el fondo, la
 * tecla Escape y una tabla del árbol.
 *
 * Uso:
 *   npm install jsdom
 *   node scripts/audit_movil_dom.js
 *
 * Sin jsdom imprime un aviso y termina en 0, igual que la prueba de interfaz.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.dirname(__dirname);
const DOCS = path.join(ROOT, "docs");

function loadJsdom() {
  for (const candidato of [path.join(ROOT, "node_modules", "jsdom"), "/tmp/node_modules/jsdom"]) {
    try {
      return require(candidato);
    } catch (error) {
      /* siguiente candidato */
    }
  }
  try {
    return require("jsdom");
  } catch (error) {
    return null;
  }
}

const jsdom = loadJsdom();
if (!jsdom) {
  console.log("jsdom no está instalado: se omite la prueba del cajón.");
  console.log("Para ejecutarla: npm install jsdom && node scripts/audit_movil_dom.js");
  process.exit(0);
}

const { JSDOM, VirtualConsole } = jsdom;
let html = fs.readFileSync(path.join(DOCS, "index.html"), "utf8");
html = html.replace(/<link rel="preconnect"[^>]*>/g, "").replace(/<link href="https:\/\/fonts[^>]*>/g, "");

const errores = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on("jsdomError", (event) => {
  const msg = event && event.message ? event.message : String(event);
  if (/Could not load|Not implemented/.test(msg)) return;
  errores.push("jsdomError: " + msg);
});
virtualConsole.on("error", (...args) => {
  const msg = args.map(String).join(" ");
  if (/DuckDB-Wasm|Failed to fetch|fetch is not defined|NetworkError|wasm/i.test(msg)) return;
  errores.push("console.error: " + msg);
});

const dom = new JSDOM(html, {
  url: "http://localhost:8000/",
  runScripts: "outside-only",
  pretendToBeVisual: true,
  virtualConsole,
  beforeParse(window) {
    const noop = () => undefined;
    const gradient = { addColorStop: noop };
    const ctx = new Proxy({}, {
      get: (target, prop) => {
        if (prop === "createLinearGradient" || prop === "createRadialGradient") return () => gradient;
        if (prop === "measureText") return () => ({ width: 42 });
        if (prop === "getImageData") return () => ({ data: [] });
        return typeof prop === "string" ? noop : undefined;
      },
      set: () => true
    });
    window.HTMLCanvasElement.prototype.getContext = () => ctx;
    // Teléfono: toda consulta de ancho pequeño responde que sí.
    window.matchMedia = (consulta) => {
      const pequeño = /max-width:\s*(\d+)px/.test(consulta);
      const ancho = pequeño ? Number(consulta.match(/max-width:\s*(\d+)px/)[1]) : 9999;
      const objeto = {
        media: consulta,
        matches: ancho >= 900,
        onchange: null,
        addListener: noop,
        removeListener: noop,
        addEventListener: noop,
        removeEventListener: noop,
        dispatchEvent: () => false
      };
      return objeto;
    };
    window.requestAnimationFrame = window.requestAnimationFrame || ((cb) => setTimeout(() => cb(Date.now()), 0));
    window.fetch = () => Promise.reject(new Error("fetch simulado: sin red en la prueba"));
    window.scrollTo = () => undefined;
    window.addEventListener("error", (event) => {
      const err = event.error;
      errores.push("window.error: " + (err && err.stack ? err.stack : event.message));
    });
  }
});

const { window } = dom;
const document = window.document;

const scripts = Array.from(document.querySelectorAll("script"));
for (const tag of scripts) {
  const src = tag.getAttribute("src");
  if (!src) continue;
  const file = path.join(DOCS, src.split("?")[0]);
  if (!fs.existsSync(file)) throw new Error("script local ausente: " + src);
  window.eval(fs.readFileSync(file, "utf8"));
}
window.eval(scripts.filter((tag) => !tag.getAttribute("src")).map((tag) => tag.textContent).join("\n"));
// No se dispara DOMContentLoaded a mano: jsdom lo emite solo al terminar de
// cargar. Dispararlo además del nativo construía dos veces el explorador y la
// segunda instancia volvía a cerrar el cajón que la primera acababa de abrir.

const resultados = [];
function check(nombre, condicion, extra) {
  resultados.push({ nombre, ok: Boolean(condicion), extra });
}
const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function correr() {
  if (document.readyState === "loading") {
    await new Promise((resolver) => document.addEventListener("DOMContentLoaded", resolver, { once: true }));
  }
  await esperar(1200);
  const sidebar = document.getElementById("sidebar");
  const fondo = document.getElementById("sidebar-backdrop");
  const boton = document.getElementById("toggle-sidebar");

  check("en un teléfono el explorador arranca cerrado", sidebar.classList.contains("collapsed"));
  check("el fondo del cajón arranca oculto", fondo && fondo.hidden === true);
  check("el botón del explorador anuncia el estado", boton.getAttribute("aria-expanded") === "false");

  boton.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await esperar(20);
  check("al tocar el botón se abre el explorador", !sidebar.classList.contains("collapsed"));
  check("al abrir aparece el fondo oscurecido", fondo.hidden === false);
  check("el botón anuncia que está abierto", boton.getAttribute("aria-expanded") === "true");

  document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  await esperar(20);
  check("Escape cierra el explorador", sidebar.classList.contains("collapsed"));
  check("al cerrar el fondo se oculta", fondo.hidden === true);

  boton.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await esperar(20);
  fondo.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await esperar(20);
  check("tocar el fondo cierra el explorador", sidebar.classList.contains("collapsed"));

  boton.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await esperar(20);
  const tabla = document.querySelector("#sidebar-tree .tree-table");
  if (tabla) {
    tabla.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    await esperar(20);
    check("elegir una tabla cierra el explorador", sidebar.classList.contains("collapsed"));
  } else {
    check("elegir una tabla cierra el explorador", false, "no se dibujó ninguna fila de tabla");
  }

  check("el explorador fuera de pantalla no recibe foco (inert)",
    sidebar.getAttribute("aria-hidden") === "true");

  // Aviso de teléfono: aparece, se cierra y el descarte queda guardado.
  const aviso = document.getElementById("aviso-movil");
  const cerrarAviso = document.getElementById("aviso-movil-cerrar");
  check("el aviso de computador aparece en un teléfono", aviso && aviso.hidden === false);
  if (aviso && cerrarAviso) {
    cerrarAviso.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    await esperar(20);
    check("el aviso se cierra con su botón", aviso.hidden === true);
    check("el descarte se recuerda en el navegador",
      window.localStorage.getItem("sif-aviso-movil-cerrado") === "1");
    check("al cerrarlo el foco no queda en el vacío",
      document.activeElement === document.getElementById("main-content"));
  } else {
    check("el aviso se cierra con su botón", false, "falta el aviso o su botón");
  }

  const fallos = resultados.filter((r) => !r.ok);
  for (const r of resultados) {
    console.log(`${r.ok ? "OK  " : "FALLA"}  ${r.nombre}${r.extra ? "  -> " + r.extra : ""}`);
  }
  if (errores.length) {
    console.log("\nErrores inesperados:");
    errores.slice(0, 6).forEach((e) => console.log("  " + e));
  }
  console.log(`\n${resultados.length - fallos.length}/${resultados.length} comprobaciones OK`);
  process.exit(fallos.length === 0 && errores.length === 0 ? 0 : 1);
}

correr();

#!/usr/bin/env node
/**
 * Prueba interactiva de la interfaz (DOM real, con jsdom).
 *
 * Complementa a scripts/audit_interfaz.py, que sólo mira texto: acá se ejecutan
 * los scripts de docs/ en un DOM y se comprueba el comportamiento —conmutación de
 * pestañas, memoria de pestaña, avisos, barra de contexto, autocompletado del
 * terminal y que la pestaña Descargas funcione de verdad: catálogo dibujado, filtros,
 * archivos por periodo, contexto del visor y traspaso a Consultas SQL.
 *
 * Uso:
 *   npm install jsdom        # o cualquier node_modules con jsdom
 *   node scripts/audit_interfaz_dom.js
 *
 * Sin jsdom (por ejemplo en CI, donde no se instala nada de npm) imprime un aviso
 * y termina con código 0: es una ayuda de desarrollo, no un requisito del flujo.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const Module = require("module");

const ROOT = path.dirname(__dirname);
const DOCS = path.join(ROOT, "docs");

function loadJsdom() {
  const candidatos = [
    path.join(ROOT, "node_modules", "jsdom"),
    "/tmp/node_modules/jsdom"
  ];
  for (const candidato of candidatos) {
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
  console.log("jsdom no está instalado: se omite la prueba interactiva.");
  console.log("Para ejecutarla: npm install jsdom && node scripts/audit_interfaz_dom.js");
  process.exit(0);
}

const { JSDOM, VirtualConsole } = jsdom;

let html = fs.readFileSync(path.join(DOCS, "index.html"), "utf8");
html = html.replace(/<link rel="preconnect"[^>]*>/g, "")
           .replace(/<link href="https:\/\/fonts[^>]*>/g, "");

const errors = [];
const virtualConsole = new VirtualConsole();
virtualConsole.on("jsdomError", (event) => {
  const msg = (event && event.message) ? event.message : String(event);
  if (/Could not load|Not implemented/.test(msg)) return;
  errors.push("jsdomError: " + msg);
});
virtualConsole.on("error", (...args) => {
  const msg = args.map(String).join(" ");
  if (/DuckDB-Wasm|Failed to fetch|fetch is not defined|NetworkError|wasm/i.test(msg)) return;
  errors.push("console.error: " + msg);
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
    window.matchMedia = window.matchMedia || (() => ({
      matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}
    }));
    window.requestAnimationFrame = window.requestAnimationFrame || ((cb) => setTimeout(() => cb(Date.now()), 0));
    window.fetch = () => Promise.reject(new Error("fetch simulado: sin red en la prueba"));
    window.scrollTo = () => undefined;
    window.addEventListener("error", (event) => {
      const err = event.error;
      errors.push("window.error: " + (err && err.stack ? err.stack : event.message));
    });
  }
});

const { window } = dom;
const document = window.document;

// Ejecuta los scripts locales en el mismo orden que el navegador y luego el inline.
const scripts = Array.from(document.querySelectorAll("script"));
for (const tag of scripts) {
  const src = tag.getAttribute("src");
  if (!src) continue;
  const file = path.join(DOCS, src.split("?")[0]);
  if (!fs.existsSync(file)) throw new Error("script local ausente: " + src);
  window.eval(fs.readFileSync(file, "utf8"));
}
window.eval(scripts.filter((tag) => !tag.getAttribute("src")).map((tag) => tag.textContent).join("\n"));
document.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true }));

const results = [];
function check(name, condition, extra) {
  results.push({ name, ok: Boolean(condition), extra });
}

setTimeout(() => {
  const tabIds = ["tab-btn-info", "tab-btn-erd", "tab-btn-dict", "tab-btn-data", "tab-btn-sql", "tab-btn-downloads", "tab-btn-normativa"];
  check("existen las 7 pestañas", tabIds.every((id) => document.getElementById(id)));
  check("cada pestaña apunta a un panel existente", tabIds.every((id) => {
    const controls = document.getElementById(id).getAttribute("aria-controls");
    return controls && document.getElementById(controls);
  }));

  // Descargas: pestaña propia con catálogo publicado a la vista.
  check("no queda el botón de descarga en la cabecera del panel", !document.getElementById("tab-btn-export"));
  check("tampoco queda el modal de exportación", typeof window.ExportModal === "undefined");
  check("el catálogo expone tipo y descripción de cada tabla",
    Boolean(window.DOWNLOAD_CATALOG.grupos[0].items[0].detalle && window.DOWNLOAD_CATALOG.grupos[0].items[0].descripcion));
  check("el catálogo de descargas está disponible",
    Boolean(window.DOWNLOAD_CATALOG && window.DOWNLOAD_CATALOG.conjuntos >= 40),
    window.DOWNLOAD_CATALOG ? String(window.DOWNLOAD_CATALOG.conjuntos) + " conjuntos" : "sin catálogo");

  window.switchMainTab("downloads");
  const panelDl = document.getElementById("downloads-container");
  check("la pestaña Descargas queda visible",
    panelDl.style.display === "flex" && document.getElementById("tab-btn-downloads").getAttribute("aria-selected") === "true");
  check("el resto queda oculto al abrir Descargas",
    document.getElementById("info-container").style.display === "none" &&
    document.getElementById("sql-container").style.display === "none");

  const tarjetas = document.querySelectorAll("#downloads-container .dl-item:not([hidden])");
  check("el catálogo se dibuja completo",
    tarjetas.length >= 40, tarjetas.length + " conjuntos visibles");
  check("cada conjunto trae su descarga de Parquet",
    document.querySelectorAll('#downloads-container [data-action="parquet"]').length > 0);
  check("cada conjunto trae CSV, Excel y SQL",
    document.querySelectorAll('#downloads-container [data-action="csv"]').length > 0 &&
    document.querySelectorAll('#downloads-container [data-action="xlsx"]').length > 0 &&
    document.querySelectorAll('#downloads-container [data-action="sql"]').length > 0);

  const buscador = document.getElementById("dl-search");
  buscador.value = "renta_fija";
  buscador.dispatchEvent(new window.Event("input", { bubbles: true }));
  const filtradas = document.querySelectorAll("#downloads-container .dl-item:not([hidden])");
  check("el buscador filtra el catálogo",
    filtradas.length === 1 && /1 de \d+ conjuntos/.test(document.getElementById("dl-counter").textContent),
    filtradas.length + " visibles · " + document.getElementById("dl-counter").textContent);
  buscador.value = "";
  buscador.dispatchEvent(new window.Event("input", { bubbles: true }));

  const selectorSector = document.getElementById("dl-sector");
  const opcionSector = Array.from(selectorSector.options).find((o) => o.value !== "todos");
  selectorSector.value = opcionSector ? opcionSector.value : "todos";
  selectorSector.dispatchEvent(new window.Event("change", { bubbles: true }));
  const porSector = document.querySelectorAll("#downloads-container .dl-item:not([hidden])");
  check("el filtro por sector acota el catálogo",
    Boolean(opcionSector) && porSector.length > 0 && porSector.length < 20,
    porSector.length + " de " + (opcionSector ? opcionSector.value : "sector"));
  selectorSector.value = "todos";
  selectorSector.dispatchEvent(new window.Event("change", { bubbles: true }));

  // Vocabulario: nombres canónicos y ninguna lista de entidades con otro nombre.
  const nombres = Array.from(document.querySelectorAll("#downloads-container .dl-item-title code"))
    .map((n) => n.textContent.trim());
  check("todos los nombres siguen <sector>.<tipo>",
    nombres.length > 40 && nombres.every((n) => /^[a-z_]+\.[a-z_]+$/.test(n)),
    nombres.length ? nombres[0] + " … " + nombres[nombres.length - 1] : "sin nombres");
  const vocab = JSON.parse(fs.readFileSync(path.join(DOCS, "vocabulario.json"), "utf8"));
  const prohibidos = vocab.nombres_retirados || [];
  check("ninguna tabla usa un nombre retirado por el vocabulario",
    !prohibidos.some((p) => html.includes(p)), prohibidos.filter((p) => html.includes(p)).join(", ") || "sin restos");
  check("cada lista de entidades se llama lista_entidades",
    Array.from(document.querySelectorAll("#downloads-container .dl-item"))
      .filter((fila) => /lista_entidades/.test(fila.querySelector("code").textContent))
      .length >= 14);

  const botonArchivos = document.querySelector('#downloads-container [data-action="files"]');
  if (botonArchivos) {
    const idArchivos = botonArchivos.dataset.id;
    botonArchivos.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    const bloque = document.querySelector(`[data-files="${idArchivos}"]`);
    const enlaces = bloque ? bloque.querySelectorAll("a.dl-file") : [];
    check("los conjuntos multiarchivo despliegan sus Parquet por periodo",
      bloque && !bloque.hasAttribute("hidden") && enlaces.length > 1 && /outputs\//.test(enlaces[0].getAttribute("href")),
      enlaces.length + " archivos");
  } else {
    check("los conjuntos multiarchivo despliegan sus Parquet por periodo", false, "no hay conjuntos multiarchivo");
  }

  // El visor abre la pestaña con su tabla activa en pantalla.
  window.MFCUI.openDownloads({
    viewName: "seguros_renta_fija",
    displayName: "seguros.renta_fija",
    rows: [{ periodo: "2026-06" }, { periodo: "2026-05" }],
    columns: ["periodo"],
    origen: "visor"
  });
  const contexto = document.getElementById("dl-context");
  check("la tabla activa se anuncia en Descargas",
    !contexto.hidden && /seguros\.renta_fija/.test(contexto.textContent) && /2 filas en pantalla/.test(contexto.textContent),
    contexto.textContent.replace(/\s+/g, " ").slice(0, 80));
  check("hay descarga de lo que está en pantalla",
    Boolean(contexto.querySelector('[data-action="pantalla"][data-fmt="csv"]')));

  // Con el motor caído, CSV/Excel avisan en vez de fallar en silencio.
  check("sin motor, CSV y Excel quedan marcados como no disponibles",
    document.querySelectorAll("#downloads-container .dl-btn-motor.dl-btn-off").length > 0);

  const botonSql = document.querySelector('#downloads-container [data-action="sql"]');
  if (botonSql) {
    botonSql.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    check("SQL lleva la tabla a Consultas SQL",
      document.getElementById("sql-container").style.display === "flex" &&
      /^SELECT \* FROM /i.test(document.getElementById("chat-input").value),
      document.getElementById("chat-input").value.slice(0, 40));
  } else {
    check("SQL lleva la tabla a Consultas SQL", false, "sin botón SQL");
  }

  window.switchMainTab("sql");
  check("pestaña SQL activa y visible",
    document.getElementById("sql-container").style.display === "flex" &&
    document.getElementById("tab-btn-sql").getAttribute("aria-selected") === "true");
  check("el resto queda oculto",
    document.getElementById("info-container").style.display === "none" &&
    document.getElementById("normativa-container").style.display === "none");
  window.switchMainTab("erd");
  check("mapa: filtros y zoom visibles",
    document.getElementById("erd-controls-group").style.display === "flex" &&
    document.querySelector(".zoom-controls").style.display === "flex");
  window.switchMainTab("info");
  check("fuera del mapa: filtros y zoom ocultos",
    document.getElementById("erd-controls-group").style.display === "none" &&
    document.querySelector(".zoom-controls").style.display === "none");

  check("MFCUI disponible", window.MFCUI && typeof window.MFCUI.toast === "function");
  window.MFCUI.rememberTab("sql");
  check("recuerda la última pestaña", window.MFCUI.initialTab() === "sql");
  window.MFCUI.toast("prueba", "ok");
  check("aviso breve dibujado", document.querySelector(".toast-host .toast"));

  const chip = document.getElementById("erd-breadcrumb");
  chip.textContent = window.SidebarNav.describeLocation("seguros", "seguros.lista_entidades");
  check("barra de contexto describe la ubicación",
    chip.textContent.includes("Seguros") && chip.textContent.includes("lista_entidades"), chip.textContent);

  const input = document.getElementById("chat-input");
  input.value = "SELECT * FROM segur";
  input.selectionStart = input.selectionEnd = input.value.length;
  window.ChatTerminal.completeInput();
  check("Tab completa nombres de vista", input.value.startsWith("SELECT * FROM seguros_"), input.value);

  const antes = document.querySelectorAll("#chat-messages .message").length;
  window.ChatTerminal.clearTerminal();
  check("Limpiar deja sólo la bienvenida",
    antes > 0 && document.querySelectorAll("#chat-messages .message").length === 1);

  // Motor caído: debe mostrarse el motivo del primer intento, el entorno y las
  // acciones de reintento y copia.
  window.dispatchEvent(new window.CustomEvent("duckdb-ready", {
    detail: {
      available: false,
      error: "todas las fuentes fallaron",
      source: null,
      attempts: [
        { id: "local", label: "copia local del repositorio", error: "fallo simulado del motor" },
        { id: "jsdelivr", label: "CDN jsDelivr", error: "sin salida a internet" }
      ],
      environment: { wasm: true, wasmExceptions: true, wasmSIMD: true, crossOriginIsolated: false, blobWorker: false, blobWorkerError: "bloqueado por CSP" },
      unavailableViews: []
    }
  }));
  const alert = document.getElementById("sql-engine-alert");
  const motivo = document.getElementById("sql-engine-error");
  check("el fallo del motor se explica en pantalla", alert && !alert.hidden && motivo.textContent.includes("fallo simulado"));
  check("el motivo viene del primer intento", motivo.textContent.includes("copia local del repositorio"), motivo.textContent.slice(0, 70));
  const env = document.getElementById("sql-engine-env");
  check("se muestra el entorno sondado", /WebAssembly/.test(env.textContent) && /bloqueado/.test(env.textContent), env.textContent.replace(/\s+/g, " ").slice(0, 90));
  check("hay acción de copiar diagnóstico", Boolean(document.getElementById("btn-engine-copy")));

  // El badge del encabezado es un botón que lleva al diagnóstico.
  const badge = document.getElementById("engine-badge");
  check("el badge del motor es un botón", badge && badge.tagName === "BUTTON");
  window.switchMainTab("info");
  if (badge) badge.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("al hacer clic en el badge se abre la pestaña de consultas",
    document.getElementById("sql-container").style.display === "flex");

  window.dispatchEvent(new window.CustomEvent("duckdb-ready", {
    detail: { available: true, error: null, source: "local", sourceLabel: "copia local del repositorio", unavailableViews: [] }
  }));
  check("cuando el motor responde, el aviso desaparece", alert.hidden);
  check("la pista indica motor local",
    /navegador|local/i.test(document.getElementById("sql-engine-hint").textContent),
    document.getElementById("sql-engine-hint").textContent.slice(0, 70));

  const fallos = results.filter((r) => !r.ok);
  for (const r of results) console.log(`${r.ok ? "OK  " : "FALLA"}  ${r.name}${r.extra ? "  -> " + r.extra : ""}`);
  if (errors.length) {
    console.log("\nErrores inesperados:");
    errors.slice(0, 8).forEach((e) => console.log("  " + e));
  }
  console.log(`\n${results.length - fallos.length}/${results.length} comprobaciones OK`);
  process.exit(fallos.length === 0 && errors.length === 0 ? 0 : 1);
}, 1200);

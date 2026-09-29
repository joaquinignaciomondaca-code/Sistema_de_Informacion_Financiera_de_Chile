#!/usr/bin/env node
/**
 * Prueba de regresión: los datos que llegan a una tabla (celdas de Parquet, alias de columna,
 * SQL del usuario) no pueden ejecutar código ni salirse de un atributo HTML.
 *
 * Carga data_viewer.js y chat_terminal.js en jsdom con los manejadores inline ACTIVOS
 * (runScripts: "dangerously"), pinta filas con valores hostiles, hace clic en cada celda y
 * comprueba que (1) no se ejecutó nada, (2) no apareció ningún elemento inyectado y (3) el
 * valor que se copia al portapapeles es exactamente el original.
 *
 * Uso: npm install jsdom && node scripts/audit_xss_celdas.js
 * Sin jsdom imprime un aviso y termina con código 0 (igual que audit_interfaz_dom.js).
 */
"use strict";

const fs = require("fs");
const path = require("path");

let JSDOM;
try {
  ({ JSDOM } = require(path.join(__dirname, "..", "node_modules", "jsdom")));
} catch (e1) {
  try { ({ JSDOM } = require("jsdom")); } catch (e2) {
    console.log("jsdom no está instalado: se omite la prueba de XSS en celdas.");
    process.exit(0);
  }
}

const JS = path.join(__dirname, "..", "docs", "js");
const fallas = [];
const ok = (cond, msg) => { console.log((cond ? "OK    " : "FALLA ") + msg); if (!cond) fallas.push(msg); };

const HOSTILES = [
  "');window.__pwn=1;//",
  "&#39;);window.__pwn=2;//",
  "\\",
  '"><img src=x onerror=window.__pwn=3>',
  "<b>negrita</b> & co",
];
const COL = "<img src=x onerror=window.__pwn=4>";
const SQL = "SELECT '\"><img src=x onerror=window.__pwn=5>'";

function ventana(html) {
  const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/" });
  const w = dom.window;
  w.eval("window.__pwn = 0");
  w.__copiado = [];
  w.navigator.clipboard = { writeText: (t) => { w.__copiado.push(t); return Promise.resolve(); } };
  return w;
}

async function main() {
  // --- Visor de datos -------------------------------------------------------
  {
    const w = ventana('<div id="data-viewer-container"></div>');
    w.eval(fs.readFileSync(path.join(JS, "data_viewer.js"), "utf8"));
    const dv = w.DataViewer;
    dv.container = w.document.getElementById("data-viewer-container");
    dv.currentView = "x"; dv.isLoading = false; dv.error = null;
    dv.currentColumns = [COL, "v"];
    dv.currentRows = HOSTILES.map((h, i) => ({ [COL]: h, v: i }));
    dv.render();
    const celdas = [...dv.container.querySelectorAll("td[data-copy]")];
    celdas.forEach((td) => td.click());
    ok(celdas.length === HOSTILES.length * 2, "visor: una celda por valor");
    ok(dv.container.querySelectorAll("img").length === 0, "visor: no se inyectan elementos desde celdas ni alias");
    ok(w.__pwn === 0, "visor: no se ejecuta código desde las celdas");
    const copiados = w.__copiado.filter((_, i) => i % 2 === 0);
    ok(JSON.stringify(copiados) === JSON.stringify(HOSTILES), "visor: lo copiado es el valor original");
  }

  // --- Terminal SQL ---------------------------------------------------------
  {
    const w = ventana('<div id="chat-messages"></div><input id="chat-input">');
    w.eval(fs.readFileSync(path.join(JS, "chat_terminal.js"), "utf8")
      .replace("window.ChatTerminalController = ChatTerminalController;", "window.__C = ChatTerminalController;"));
    const c = Object.create(w.__C.prototype);
    c.messagesContainer = w.document.getElementById("chat-messages");
    c.resultsMap = {};
    w.ChatTerminal = c;
    c.renderQueryResult(SQL, { columns: [COL], rows: HOSTILES.map((h) => ({ [COL]: h })), count: HOSTILES.length, elapsedMs: 1 });
    const m = c.messagesContainer;
    m.querySelectorAll("td").forEach((td) => td.click());
    const btn = [...m.querySelectorAll("button")].find((b) => b.dataset.sql);
    if (btn) btn.click();
    ok(!!btn, "terminal: el botón «Copiar SQL» existe");
    ok(m.querySelectorAll("img").length === 0, "terminal: no se inyectan elementos desde celdas, alias ni SQL");
    ok(w.__pwn === 0, "terminal: no se ejecuta código desde las celdas");
    ok(JSON.stringify(w.__copiado) === JSON.stringify(HOSTILES.concat([SQL])), "terminal: lo copiado es el valor original");
  }

  console.log(fallas.length ? `\n${fallas.length} comprobaciones fallaron` : `\nXSS en celdas: todas las comprobaciones OK`);
  process.exit(fallas.length ? 1 : 0);
}

main();

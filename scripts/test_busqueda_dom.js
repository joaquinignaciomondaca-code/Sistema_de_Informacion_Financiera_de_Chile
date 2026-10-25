#!/usr/bin/env node
"use strict";

// Prueba DOM de la búsqueda por pregunta: estado sin resultados, recuperación,
// accesibilidad del mensaje y ausencia de solicitudes por cada pulsación.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const raiz = path.resolve(__dirname, "..");
const indice = JSON.parse(fs.readFileSync(path.join(raiz, "docs/outputs/indice_busqueda.json"), "utf8"));
const catalogoApi = JSON.parse(fs.readFileSync(path.join(raiz, "docs/api/v2/catalog.json"), "utf8"));
const codigoDescargas = fs.readFileSync(path.join(raiz, "docs/js/download_catalog.js"), "utf8");
const catalogoDescargas = JSON.parse(codigoDescargas.split("window.DOWNLOAD_CATALOG =", 2)[1].trim().replace(/;\s*$/, ""));
const fuente = fs.readFileSync(path.join(raiz, "docs/js/busqueda_pregunta.js"), "utf8");

async function cargar(indicePromise) {
  const dom = new JSDOM(`<!doctype html><html lang="es"><body>
    <div class="sidebar-search-box"><label for="sidebar-search">Filtrar tablas</label>
      <input id="sidebar-search" type="search"></div>
  </body></html>`, { runScripts: "outside-only", url: "https://ejemplo.invalid/" });
  const { window } = dom;
  const solicitudes = { fetch: 0, xhr: 0, beacon: 0 };
  window.SIF_JSON = { indice: indicePromise };
  window.fetch = () => { solicitudes.fetch++; return Promise.reject(new Error("red inesperada en prueba")); };
  window.XMLHttpRequest = class { constructor() { solicitudes.xhr++; } };
  Object.defineProperty(window.navigator, "sendBeacon", {
    configurable: true,
    value: () => { solicitudes.beacon++; return true; },
  });
  window.eval(fuente);
  window.document.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true }));
  await new Promise((resolve) => window.setTimeout(resolve, 0));
  return { dom, window, solicitudes: () => ({ ...solicitudes }) };
}

(async () => {
  assert.equal(indice.tablas.length, 90, "el índice conserva todos los IDs publicados");
  assert.equal(indice.tablas.filter((t) => t.formatos.includes("PARQUET")).length, 86,
    "se identifican como Parquet solo los objetos con archivos físicos declarados");
  assert.equal(indice.tablas.filter((t) => t.formatos.length === 0).length, 4,
    "los cuatro objetos sin archivo directo no reciben formatos inventados");
  const itemsDescarga = catalogoDescargas.grupos.flatMap((g) => g.items);
  for (const tabla of indice.tablas) {
    const api = catalogoApi.objetos.find((o) => o.id === tabla.id);
    const descarga = itemsDescarga.find((o) => o.id === tabla.id);
    assert.ok(api && descarga, `cada tarjeta debe conservar el mismo ID en API y descargas: ${tabla.id}`);
    assert.equal(tabla.fuente, api.fuente, `fuente de ${tabla.id}`);
    assert.equal(tabla.corte, api.corte, `cobertura/corte de ${tabla.id}`);
    const formatos = [...new Set(descarga.archivos.map((a) => path.extname(a.ruta).slice(1).toUpperCase()))].sort();
    assert.deepEqual(tabla.formatos, formatos, `formatos directos de ${tabla.id}`);
  }

  const prueba = await cargar(Promise.resolve(indice));
  const { dom, window } = prueba;
  const entrada = window.document.getElementById("pregunta-buscar");
  const estado = window.document.getElementById("pregunta-estado");
  const resultados = window.document.getElementById("pregunta-resultados");
  assert.ok(entrada && estado && resultados, "la interfaz debe insertar campo, estado y lista");
  assert.equal(estado.getAttribute("aria-live"), "polite", "el estado debe anunciarse sin interrumpir");
  assert.equal(window.document.querySelector('label[for="pregunta-buscar"]')?.textContent.trim(), "Buscar por pregunta o concepto");

  entrada.value = "qwertyuiop asdfgh";
  entrada.dispatchEvent(new window.Event("input", { bubbles: true }));
  assert.match(estado.textContent, /Sin resultados.*otro concepto.*nombre de la industria/i);
  assert.equal(resultados.children.length, 0, "un resultado vacío no debe dejar botones obsoletos");
  assert.deepEqual(prueba.solicitudes(), { fetch: 0, xhr: 0, beacon: 0 }, "escribir una consulta no debe enviar solicitudes ni telemetría");

  entrada.value = "inflación IPC";
  entrada.dispatchEvent(new window.Event("input", { bubbles: true }));
  assert.match(estado.textContent, /resultado\(s\).*relevancia/i);
  const resultado = resultados.querySelector(".pregunta-item");
  assert.equal(resultado?.querySelector(".pregunta-nombre")?.textContent, "macro.inflacion_ipc");
  assert.ok(resultado?.querySelector(".pregunta-sector")?.textContent.trim(), "el resultado muestra el sector legible");
  assert.ok(resultado?.querySelector(".pregunta-desc")?.textContent.trim(), "el resultado explica qué contiene la tabla");
  assert.ok(resultado?.querySelector(".pregunta-motivo")?.textContent.trim(), "el resultado explica por qué coincide");
  const entradaIndice = indice.tablas.find((t) => t.id === "macro_inflacion_ipc");
  const apiEsperada = catalogoApi.objetos.find((t) => t.id === "macro_inflacion_ipc");
  const descargaEsperada = catalogoDescargas.grupos.flatMap((g) => g.items).find((t) => t.id === "macro_inflacion_ipc");
  const formatosEsperados = [...new Set(descargaEsperada.archivos.map((a) => a.ruta.split(".").pop().toUpperCase()))].sort();
  assert.equal(resultado.querySelector(".pregunta-identificador")?.textContent, "ID: macro_inflacion_ipc");
  assert.equal(resultado.querySelector(".pregunta-metadatos span:nth-child(1)")?.textContent, `Fuente: ${apiEsperada.fuente}`);
  assert.equal(resultado.querySelector(".pregunta-metadatos span:nth-child(2)")?.textContent, `Cobertura: ${apiEsperada.corte}`);
  assert.equal(resultado.querySelector(".pregunta-metadatos span:nth-child(3)")?.textContent, `Archivo: ${formatosEsperados.map((f) => f === "PARQUET" ? "Parquet" : f).join(", ")}`);
  assert.deepEqual(entradaIndice.formatos, formatosEsperados, "el índice conserva formatos del catálogo de descargas");
  assert.equal(resultado.querySelector(".pregunta-boton")?.getAttribute("type"), "button");
  assert.match(resultado.querySelector(".pregunta-accion")?.textContent || "", /Seleccionar en el explorador/);
  assert.deepEqual(prueba.solicitudes(), { fetch: 0, xhr: 0, beacon: 0 }, "la recuperación tampoco debe hacer solicitudes por consulta");
  const botones = [...resultados.querySelectorAll(".pregunta-boton")];
  assert.ok(botones.length > 1, "la consulta de regresión permite recorrer varios resultados");
  entrada.dispatchEvent(new window.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true, cancelable: true }));
  assert.equal(window.document.activeElement, botones[0], "ArrowDown desde el campo enfoca el primer resultado");
  botones[0].dispatchEvent(new window.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true, cancelable: true }));
  assert.equal(window.document.activeElement, botones[1], "ArrowDown avanza al resultado siguiente");
  botones[1].dispatchEvent(new window.KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true, cancelable: true }));
  assert.equal(window.document.activeElement, botones[0], "ArrowUp regresa al resultado anterior");
  botones[0].dispatchEvent(new window.KeyboardEvent("keydown", { key: "End", bubbles: true, cancelable: true }));
  assert.equal(window.document.activeElement, botones[botones.length - 1], "End enfoca el último resultado");
  botones[botones.length - 1].dispatchEvent(new window.KeyboardEvent("keydown", { key: "Home", bubbles: true, cancelable: true }));
  assert.equal(window.document.activeElement, botones[0], "Home regresa al primer resultado");
  botones[0].dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }));
  assert.equal(window.document.activeElement, entrada, "Escape devuelve el foco al campo de búsqueda");
  entrada.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  assert.equal(window.document.getElementById("sidebar-search").value, "macro.inflacion_ipc");

  entrada.value = "";
  entrada.dispatchEvent(new window.Event("input", { bubbles: true }));
  assert.equal(estado.textContent, "", "limpiar la consulta debe limpiar el estado");
  assert.equal(resultados.children.length, 0);
  assert.deepEqual(prueba.solicitudes(), { fetch: 0, xhr: 0, beacon: 0 });
  dom.window.close();

  const error = await cargar(Promise.reject(new Error("fallo simulado")));
  assert.match(error.window.document.getElementById("pregunta-estado").textContent, /no se pudo cargar.*filtro por nombre.*disponible/i);
  assert.equal(error.window.document.getElementById("pregunta-buscar").disabled, true);
  assert.deepEqual(error.solicitudes(), { fetch: 0, xhr: 0, beacon: 0 }, "un índice ya entregado como error no provoca reintentos ocultos");
  error.dom.window.close();

  const tablaSinArchivo = { ...indice.tablas.find((t) => t.formatos.length === 0), terminos: ["prueba tarjeta sin archivo"] };
  const sinArchivo = await cargar(Promise.resolve({ tablas: [tablaSinArchivo] }));
  const entradaSinArchivo = sinArchivo.window.document.getElementById("pregunta-buscar");
  entradaSinArchivo.value = "prueba tarjeta sin archivo";
  entradaSinArchivo.dispatchEvent(new sinArchivo.window.Event("input", { bubbles: true }));
  assert.equal(sinArchivo.window.document.querySelector(".pregunta-metadatos span:nth-child(3)")?.textContent,
    "Archivo: sin archivo directo", "la tarjeta no debe insinuar formatos derivados como archivos físicos");
  sinArchivo.dom.window.close();

  console.log("OK búsqueda DOM: estados vacío/error, metadatos trazables, archivo sin formatos, Enter, flechas, Home/End, Escape, foco y recuperación");
  console.log("OK privacidad de interacción: fetch, XHR y sendBeacon no se invocan al consultar; índice local disponible");
})().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});

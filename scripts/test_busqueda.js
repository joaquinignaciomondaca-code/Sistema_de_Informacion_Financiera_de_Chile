#!/usr/bin/env node
"use strict";

// Batería determinista del ranking de búsqueda: usa el índice publicado y el
// mismo módulo JavaScript que carga la interfaz, sin red ni dependencias externas.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const raiz = path.resolve(__dirname, "..");
const archivoIndice = path.join(raiz, "docs/outputs/indice_busqueda.json");
const indice = JSON.parse(fs.readFileSync(archivoIndice, "utf8"));
const contexto = {
  window: {},
  document: { readyState: "loading", addEventListener() {} },
  console,
  Set,
  String,
  Math,
  WeakMap,
  Map,
};
vm.createContext(contexto);
vm.runInContext(fs.readFileSync(path.join(raiz, "docs/js/busqueda_pregunta.js"), "utf8"), contexto);
const buscar = contexto.window.busquedaPregunta.buscar;

const casos = [
  ["UF", "macro_uf"],
  ["unidad de fomento", "macro_uf"],
  ["IPC mensual", "macro_inflacion_ipc"],
  ["tasa de política monetaria", "macro_tasas_corto_plazo"],
  ["TPM", "macro_tasas_corto_plazo"],
  ["expectativas TPM", "macro_expectativas_tpm"],
  ["dólar observado", "macro_dolar_observado"],
  ["desempleo", "macro_mercado_laboral"],
  ["precio del cobre", "macro_cobre"],
  ["bonos en pesos", "macro_curva_bonos_pesos"],
  ["bonos UF", "macro_curva_bonos_uf"],
  ["cartera extranjera fondos mutuos", "ffmm_cartera_extranjera"],
  ["cartera nacional fondos mutuos", "ffmm_cartera_nacional"],
  ["cartera nacional fondos de inversión", "fi_cartera_nacional"],
  ["balance bancos", "bancos_balance"],
  ["resultados bancos", "bancos_resultados"],
  ["renta fija aseguradoras", "seguros_renta_fija"],
  ["derivados seguros", "seguros_derivados"],
  ["fondos de inversión inmuebles", "fi_bienes_raices"],
  ["Ley Fintec", "fintech_rpsf_lista_entidades"],
  ["Banco Central", "macro_reservas_internacionales"],
  ["Banco de Chile", "bancos_balance"],
  ["ffmm_cartera_nacional", "ffmm_cartera_nacional"],
  ["inflasión IPC", "macro_inflacion_ipc"],
  ["balnce bancos", "bancos_balance"],
  ["dolar observdo", "macro_dolar_observado"],
];

let fallos = 0;
for (const [consulta, esperado] of casos) {
  const resultado = buscar(indice, consulta);
  const obtenido = resultado[0]?.tabla.id || null;
  const fuzzyEsperado = /inflasión|balnce|observdo/i.test(consulta);
  const fuzzyDetectado = Boolean(resultado[0]?.correcciones?.length);
  const ok = obtenido === esperado && (!fuzzyEsperado || fuzzyDetectado);
  console.log(`${ok ? "OK" : "FALLA"} ${JSON.stringify(consulta)} → ${obtenido || "sin resultados"}${fuzzyEsperado ? `; fuzzy=${fuzzyDetectado}` : ""}`);
  if (!ok) fallos++;
}

// Todas las etiquetas curadas deben recuperar al menos una de sus tablas destino
// dentro del límite visible. Esto detecta un alias que quedó fuera del ranking
// aunque su ID siga existiendo; no certifica que la curación semántica sea correcta.
const archivoSinonimos = path.join(raiz, "docs/busqueda_sinonimos.json");
const sinonimos = JSON.parse(fs.readFileSync(archivoSinonimos, "utf8"));
let sinonimosRevisados = 0;
for (const concepto of sinonimos.conceptos) {
  const destinos = new Set(concepto.tablas);
  for (const consulta of [concepto.termino, ...(concepto.alias || [])]) {
    sinonimosRevisados++;
    const encontrados = buscar(indice, consulta).map((r) => r.tabla.id);
    const ok = encontrados.some((id) => destinos.has(id));
    if (!ok) {
      console.log(`FALLA el término curado ${JSON.stringify(consulta)} no recupera ninguna tabla destino: ${[...destinos].join(", ")}`);
      fallos++;
    }
  }
}
console.log(`${fallos ? "FALLA" : "OK"} términos curados: ${sinonimosRevisados} consultas llegan a por lo menos una tabla destino`);

const ambiguosSwaps = buscar(indice, "swaps").map((r) => r.tabla.id);
const muestraAmbosContextos = ambiguosSwaps.includes("macro_swaps_camara") && ambiguosSwaps.includes("seguros_derivados");
console.log(`${muestraAmbosContextos ? "OK" : "FALLA"} «swaps» mantiene visibles los contextos macro y de seguros sin fijar un orden no validado`);
if (!muestraAmbosContextos) fallos++;

const conTilde = buscar(indice, "inflación IPC").map((r) => r.tabla.id);
const sinTilde = buscar(indice, "inflacion IPC").map((r) => r.tabla.id);
const sinCoincidencias = buscar(indice, "qwertyuiop asdfgh");
const limiteResultados = buscar(indice, "fondos").length <= 8;
for (const [nombre, ok] of [
  ["la búsqueda ignora tildes sin cambiar el orden", JSON.stringify(conTilde) === JSON.stringify(sinTilde)],
  ["una consulta irrelevante conserva el estado sin resultados", sinCoincidencias.length === 0],
  ["el ranking no devuelve más de ocho resultados", limiteResultados],
]) {
  console.log(`${ok ? "OK" : "FALLA"} ${nombre}`);
  if (!ok) fallos++;
}

console.log(`\nBÚSQUEDA: ${casos.length} casos prioritarios + ${sinonimosRevisados} términos curados, ${fallos} fallos`);
process.exitCode = fallos ? 1 : 0;

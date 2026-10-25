#!/usr/bin/env node
"use strict";

// Medición reproducible de la búsqueda en Node/VM. No representa bytes servidos
// por el hosting, ejecución DOM ni latencia de un navegador/dispositivo.
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const zlib = require("node:zlib");
const { performance } = require("node:perf_hooks");

const raiz = path.resolve(__dirname, "..");
const rutaIndice = path.join(raiz, "docs/outputs/indice_busqueda.json");
const rutaFuente = path.join(raiz, "docs/js/busqueda_pregunta.js");
const bufferIndice = fs.readFileSync(rutaIndice);
const indice = JSON.parse(bufferIndice.toString("utf8"));
const fuente = fs.readFileSync(rutaFuente, "utf8");
const iteraciones = Number(process.argv[2] || 500);
if (!Number.isInteger(iteraciones) || iteraciones < 20) {
  console.error("Uso: node scripts/bench_busqueda.js [iteraciones>=20]");
  process.exit(2);
}

const contexto = {
  document: { readyState: "loading", addEventListener() {} },
  window: null,
};
contexto.window = contexto;
vm.runInNewContext(fuente, contexto, { filename: "busqueda_pregunta.js" });
const buscar = contexto.busquedaPregunta && contexto.busquedaPregunta.buscar;
if (typeof buscar !== "function") throw new Error("No se expuso busquedaPregunta.buscar");

const consultas = [
  "inflación IPC",
  "dólar observado",
  "tasa TPM",
  "fondos mutuos cartera",
  "acciones seguros",
];
const inicioFrio = performance.now();
buscar(indice, consultas[0]);
const primeraFria = performance.now() - inicioFrio;
const muestras = [];
for (let i = 0; i < iteraciones; i++) {
  const inicio = performance.now();
  buscar(indice, consultas[i % consultas.length]);
  muestras.push(performance.now() - inicio);
}
muestras.sort((a, b) => a - b);
const percentil = (p) => muestras[Math.floor((muestras.length - 1) * p)];
const salida = {
  entorno: `Node ${process.version} / VM (sin DOM)`,
  iteraciones,
  indice_bytes: bufferIndice.length,
  indice_gzip_nivel_6_bytes: zlib.gzipSync(bufferIndice, { level: 6 }).length,
  primera_busqueda_fria_ms: Number(primeraFria.toFixed(2)),
  busqueda_caliente_p50_ms: Number(percentil(0.50).toFixed(2)),
  busqueda_caliente_p95_ms: Number(percentil(0.95).toFixed(2)),
  consultas: consultas.length,
};
console.log(JSON.stringify(salida, null, 2));

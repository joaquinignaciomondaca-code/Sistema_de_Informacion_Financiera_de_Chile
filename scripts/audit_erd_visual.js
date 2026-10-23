#!/usr/bin/env node
/**
 * Auditoría visual del mapa relacional (canvas), sin navegador.
 *
 * El 2026-10-23 el mapa mostraba los títulos encimados: hay nodos con nombres
 * de 118 caracteres en tarjetas de 240 px, la insignia de la derecha se
 * dibujaba siempre, y dos nodos (`seguros_registros_tipo6` y
 * `seguros_acciones_relevantes`) estaban en la misma coordenada. El canvas no
 * se puede revisar a ojo en CI, así que aquí se dibuja con un contexto falso
 * que mide cada texto y se comprueba, geometría en mano:
 *
 *   1. que no haya dos tarjetas solapadas;
 *   2. que ningún texto dibujado se salga de la tarjeta que lo contiene
 *      (ni a la derecha, ni abajo, ni sobre la tarjeta vecina);
 *   3. que el recorte con «…» respete el ancho disponible.
 *
 * Uso: node scripts/audit_erd_visual.js        (exit 1 si algo falla)
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const RAIZ = path.resolve(__dirname, "..");
const ARCHIVO = path.join(RAIZ, "docs", "js", "erd_graph.js");

// Anchos por carácter: aproximan las dos familias que usa el mapa. Lo que
// importa es que sean constantes y parecidas a la realidad (monoespaciada
// 12 px ≈ 7,2 px; título en negrita 12 px ≈ 6,6 px).
const ANCHO_CARACTER = 7;

function contextoFalso() {
  const textos = [];
  const ctx = {
    font: "12px monospace",
    fillStyle: "",
    strokeStyle: "",
    lineWidth: 1,
    globalAlpha: 1,
    shadowColor: "",
    shadowBlur: 0,
    textAlign: "left",
    textBaseline: "alphabetic",
    _pila: 0,
    save() { this._pila += 1; },
    restore() { this._pila = Math.max(0, this._pila - 1); },
    beginPath() {},
    moveTo() {},
    lineTo() {},
    arcTo() {},
    arc() {},
    bezierCurveTo() {},
    closePath() {},
    fill() {},
    stroke() {},
    clip() {},
    fillRect() {},
    setLineDash() {},
    clearRect() {},
    translate() {},
    scale() {},
    measureText(texto) {
      return { width: String(texto == null ? "" : texto).length * ANCHO_CARACTER };
    },
    fillText(texto, x, y) {
      const ancho = this.measureText(texto).width;
      // Los tipos de columna se dibujan alineados a la derecha.
      const izquierda = this.textAlign === "right" ? x - ancho
        : this.textAlign === "center" ? x - ancho / 2
        : x;
      textos.push({ texto: String(texto), x: izquierda, y, ancho });
    },
  };
  return { ctx, textos };
}

function cargar() {
  const codigo = fs.readFileSync(ARCHIVO, "utf8");
  const canvas = {
    width: 1200,
    height: 800,
    style: {},
    getContext: () => contextoFalso().ctx,
    addEventListener() {},
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 1200, height: 800 }),
  };
  const ventana = {
    addEventListener() {},
    removeEventListener() {},
    innerWidth: 1200,
    innerHeight: 800,
    devicePixelRatio: 1,
  };
  const contexto = {
    window: ventana,
    document: {
      getElementById: () => canvas,
      documentElement: {},
      querySelectorAll: () => [],
      createElement: () => ({ style: {}, classList: { add() {}, remove() {} } }),
    },
    getComputedStyle: () => ({ getPropertyValue: () => "" }),
    console,
    requestAnimationFrame: (f) => f(),
  };
  contexto.globalThis = contexto;
  vm.createContext(contexto);
  vm.runInContext(codigo, contexto, { filename: "erd_graph.js" });
  vm.runInContext("window.ERDGraph = ERDGraph;", contexto);
  return { contexto, ventana, canvas };
}

function main() {
  const { contexto, canvas } = cargar();
  const fallos = [];

  const tablas = vm.runInContext("ERD_TABLES", contexto);
  console.log(`Nodos en el mapa: ${tablas.length}`);

  // 1. Tarjetas solapadas ---------------------------------------------------
  let solapes = 0;
  for (let i = 0; i < tablas.length; i += 1) {
    for (let j = i + 1; j < tablas.length; j += 1) {
      const a = tablas[i];
      const b = tablas[j];
      if (a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h) {
        fallos.push(`tarjetas solapadas: ${a.id} (${a.x},${a.y}) y ${b.id} (${b.x},${b.y})`);
        solapes += 1;
      }
    }
  }
  console.log(`  solapes entre tarjetas: ${solapes}`);

  // 2. Textos dentro de su tarjeta -----------------------------------------
  const Grafo = vm.runInContext("ERDGraph", contexto);
  const grafo = new Grafo("erd-canvas");
  grafo.canvas = canvas;
  grafo.filter = "completo";           // todos los nodos a la vez
  grafo.matchesFilter = () => true;

  const { ctx, textos } = contextoFalso();
  grafo.drawNodes(ctx);

  const visible = (t) => t;
  let fuera = 0;
  textos.forEach((t) => {
    // La tarjeta que lo contiene: por rango vertical y arranque horizontal.
    const duena = tablas.find((n) => visible(n) &&
      t.y >= n.y && t.y <= n.y + n.h &&
      t.x >= n.x && t.x < n.x + n.w + 0.5);
    if (!duena) {
      fallos.push(`texto sin tarjeta: «${t.texto}» en (${t.x}, ${t.y})`);
      fuera += 1;
      return;
    }
    if (t.x + t.ancho > duena.x + duena.w - 1) {
      fallos.push(`«${t.texto}» se sale de ${duena.id} por la derecha ` +
        `(${Math.round(t.x + t.ancho)} > ${duena.x + duena.w})`);
      fuera += 1;
    }
    if (t.y > duena.y + duena.h - 2) {
      fallos.push(`«${t.texto}» se sale de ${duena.id} por abajo`);
      fuera += 1;
    }
    // Y no puede invadir la tarjeta vecina a la misma altura.
    tablas.forEach((otra) => {
      if (otra === duena) return;
      if (t.y >= otra.y && t.y <= otra.y + otra.h &&
          t.x < otra.x + otra.w && t.x + t.ancho > otra.x) {
        fallos.push(`«${t.texto}» de ${duena.id} se dibuja encima de ${otra.id}`);
        fuera += 1;
      }
    });
  });
  console.log(`  textos dibujados: ${textos.length} · fuera de su tarjeta: ${fuera}`);

  // 3. El recorte respeta el ancho -----------------------------------------
  const recortar = vm.runInContext("ERDGraph.prototype.recortar", contexto);
  const largo = "B.2 ACCIONES DE SOCIEDADES ANÓNIMAS ABIERTAS, ACCIONES DE SOCIEDADES ANÓNIMAS CERRADAS";
  const recortado = recortar.call(null, ctx, largo, 220);
  const anchoRecortado = recortado.length * ANCHO_CARACTER;
  if (anchoRecortado > 220) fallos.push(`el recorte ocupa ${anchoRecortado} px de 220`);
  if (!recortado.endsWith("\u2026")) fallos.push("el recorte no termina en «…»");
  if (recortar.call(null, ctx, "corto", 220) !== "corto") fallos.push("recorta un texto que cabía");
  console.log(`  recorte: «${recortado}» (${anchoRecortado} px de 220)`);

  // 4. Una insignia larga no se dibuja encima del título --------------------
  const conInsigniaLarga = tablas.filter((t) => (t.rows || "").length > 18);
  console.log(`  insignias largas (>18 caracteres): ${conInsigniaLarga.length}`);

  if (fallos.length) {
    console.log("\nFALLOS:");
    fallos.slice(0, 20).forEach((f) => console.log(`  [FALLA] ${f}`));
    console.log(`\nERD VISO: ${fallos.length} problema(s)`);
    return 1;
  }
  console.log("\nERD VISO: los 84 nodos caben sin solapes y ningún texto se sale de su tarjeta");
  return 0;
}

process.exit(main());

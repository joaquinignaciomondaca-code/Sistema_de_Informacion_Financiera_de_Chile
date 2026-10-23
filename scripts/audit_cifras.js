#!/usr/bin/env node
/**
 * Las cifras de la portada, contra el catálogo publicado.
 *
 * El 2026-10-23 la portada decía «19,7 millones de filas (99,5 % de los 19,8
 * millones publicados)» con 19.777.517 filas de verdad: el número estaba escrito
 * a mano y la redacción lo redondeaba al alza. Ahora las cifras salen del
 * catálogo en el navegador (`data-alcance`), se truncan hacia abajo y llevan
 * «más de» cuando queda resto; el texto del HTML es sólo el respaldo sin
 * JavaScript, y por eso tiene que coincidir con lo que calcula la página.
 *
 * Esta auditoría comprueba tres cosas:
 *   1. que el respaldo del HTML sea exactamente lo que pinta `portada.js`
 *      (si no, quien entre sin JavaScript lee una cifra vieja);
 *   2. que ninguna cifra redondee hacia arriba (nunca «más filas» de las que hay);
 *   3. que los dos formateadores usen la misma regla.
 *
 * Uso: node scripts/audit_cifras.js        (exit 1 si algo falla)
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const RAIZ = path.resolve(__dirname, "..");
const HTML = path.join(RAIZ, "docs", "index.html");

function cargar() {
  const ventana = { addEventListener() {}, removeEventListener() {} };
  const contexto = {
    window: ventana,
    document: {
      readyState: "complete",
      addEventListener() {},
      getElementById: () => null,
      querySelectorAll: () => [],
      documentElement: {},
    },
    console,
    Set,
    Math,
    Number,
  };
  contexto.globalThis = contexto;
  vm.createContext(contexto);
  for (const archivo of ["download_catalog.js", "alcance.js", "portada.js"]) {
    const ruta = path.join(RAIZ, "docs", "js", archivo);
    vm.runInContext(fs.readFileSync(ruta, "utf8"), contexto, { filename: archivo });
  }
  return contexto;
}

function main() {
  const contexto = cargar();
  const A = contexto.window.SIFAlcance;
  const Portada = contexto.window.SIFPortada;
  const catalogo = contexto.window.DOWNLOAD_CATALOG;
  const fallos = [];

  if (!A || !Portada || !catalogo) {
    console.log("CIFRAS: no se pudo cargar alcance.js / portada.js / download_catalog.js");
    return 1;
  }

  // 1. El respaldo del HTML coincide con lo que pinta la página -------------
  const html = fs.readFileSync(HTML, "utf8");
  const marcas = [...html.matchAll(/data-alcance="([^"]+)"[^>]*>([^<]*)</g)];
  console.log(`Cifras en el HTML con respaldo: ${marcas.length}`);
  let desfasadas = 0;
  for (const [, ruta, textoHtml] of marcas) {
    const esperado = Portada.valor(ruta);
    if (esperado == null) {
      // Una ruta que el catálogo no sabe responder es un fallo del marcado.
      fallos.push(`data-alcance="${ruta}" no tiene valor en el catálogo`);
      continue;
    }
    if (textoHtml.trim() !== esperado) {
      fallos.push(`data-alcance="${ruta}": el HTML dice «${textoHtml.trim()}» y la página pinta «${esperado}»`);
      desfasadas += 1;
    }
  }
  console.log(`  desfasadas: ${desfasadas}`);

  // 2. Ninguna cifra redondea hacia arriba ---------------------------------
  const total = catalogo.filas;
  const casos = [
    ["catalogo.filas", total],
    ["visible.filas", catalogo.alcance.visible.filas],
    ["nucleo.filas", catalogo.alcance.niveles.find((n) => n.id === "nucleo").filas],
  ];
  function valorDe(texto) {
    const limpio = texto.replace("más de ", "").replace(/\s/g, "");
    if (limpio.endsWith("millones")) return parseFloat(limpio.replace("millones", "").replace(",", ".")) * 1e6;
    if (limpio.endsWith("M")) return parseFloat(limpio.replace("M", "").replace(",", ".")) * 1e6;
    if (limpio.endsWith("mil")) return parseFloat(limpio.replace("mil", "").replace(/\./g, "")) * 1e3;
    return parseFloat(limpio.replace(/\./g, ""));
  }
  for (const [nombre, real] of casos) {
    for (const [etiqueta, texto] of [["millones", A.millones(real)], ["compacto", A.compacto(real)]]) {
      const declarado = valorDe(texto);
      if (!(declarado <= real)) {
        fallos.push(`${nombre}.${etiqueta} = «${texto}» declara ${declarado} sobre ${real}`);
      }
      // Y no se queda absurdamente corto (dos cifras significativas).
      if (real >= 1e6 && declarado < real / 100) {
        fallos.push(`${nombre}.${etiqueta} = «${texto}» pierde más de dos cifras`);
      }
      if (declarado < real && !texto.startsWith("más de ")) {
        fallos.push(`${nombre}.${etiqueta} = «${texto}» es aproximada pero no lo dice`);
      }
      if (declarado === real && texto.startsWith("más de ")) {
        fallos.push(`${nombre}.${etiqueta} = «${texto}» dice «más de» una cifra exacta`);
      }
    }
  }

  // 3. Los dos formateadores usan la misma regla ---------------------------
  const pct = catalogo.alcance.visible.pct_filas;
  const pctTexto = parseFloat(A.porcentaje(pct).replace(",", "."));
  if (pctTexto > pct) {
    fallos.push(`porcentaje(${pct}) = «${pctTexto}» redondea al alza`);
  }
  if (!A.millones(2_000_000).startsWith("2 millones")) {
    fallos.push(`millones(2.000.000) = «${A.millones(2_000_000)}»: una cifra exacta no lleva «más de»`);
  }

  if (fallos.length) {
    console.log("\nFALLOS:");
    fallos.forEach((f) => console.log(`  [FALLA] ${f}`));
    console.log(`\nCIFRAS: ${fallos.length} problema(s)`);
    return 1;
  }
  const cifras = [
    `catálogo ${A.millones(total)} de filas`,
    `visible ${A.millones(catalogo.alcance.visible.filas)}`,
    `núcleo ${A.millones(catalogo.alcance.niveles.find((n) => n.id === "nucleo").filas)}`,
  ];
  console.log(`\nCIFRAS: ${marcas.length} respaldos al día y ninguna cifra redondea al alza (${cifras.join(" · ")})`);
  return 0;
}

process.exit(main());

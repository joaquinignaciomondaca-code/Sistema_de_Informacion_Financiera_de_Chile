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
  for (const archivo of ["download_catalog.js", "estado_claves.js", "alcance.js", "portada.js"]) {
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

  // 4. El README del repositorio tampoco puede prometer más de lo que hay -----
  // El 2026-10-23 decía «75 tablas y 13,5 millones de filas» con 90 objetos y
  // 19.777.517 filas: seis millones de filas de diferencia en la portada del
  // repositorio. Las cifras del README se corrigen contra el catálogo y esta
  // comprobación impide que vuelvan a quedarse atrás.
  const readme = fs.readFileSync(path.join(RAIZ, "README.md"), "utf8");
  const promesas = [...readme.matchAll(/(\d[\d.]*(?:,\d+)?)\s*(millones|M|mil)?\s*(?:de\s+)?filas/g)];
  for (const [texto, cifra, escala] of promesas) {
    const limpio = cifra.replace(/\./g, "").replace(",", ".");
    const valor = escala === "millones" || escala === "M" ? parseFloat(limpio) * 1e6
      : escala === "mil" ? parseFloat(limpio) * 1e3
      : parseFloat(limpio);
    if (Number.isFinite(valor) && valor > total) {
      fallos.push(`README: «${texto}» declara ${valor} filas y el catálogo tiene ${total}`);
    }
  }
  const totalFila = readme.match(/\|\s*\*\*Total\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*([\d.]+)\*\*/);
  if (!totalFila) {
    fallos.push("README: no se encontró la fila Total de la tabla de industrias");
  } else {
    const objetos = catalogo.alcance.orden.reduce((n, k) => n + catalogo.alcance.sectores[k].conjuntos, 0);
    const filas = catalogo.alcance.orden.reduce((n, k) => n + catalogo.alcance.sectores[k].filas, 0);
    if (Number(totalFila[1]) !== objetos) {
      fallos.push(`README: la tabla suma ${totalFila[1]} objetos y el catálogo ${objetos}`);
    }
    if (Number(totalFila[2].replace(/\./g, "")) !== filas) {
      fallos.push(`README: la tabla suma ${totalFila[2]} filas y el catálogo ${filas}`);
    }
  }

  // 5. Las cifras del bloque de calidad del dato ------------------------------
  // Van escritas en el HTML como respaldo sin JavaScript; el módulo
  // `calidad_datos.js` las repinta desde `estado_claves.js`. Si el CSV cambia y
  // el respaldo no, quien entre sin JavaScript lee una cifra vieja.
  const estado = contexto.window.ESTADO_CLAVES;
  if (!estado) {
    fallos.push("no se pudo cargar docs/js/estado_claves.js");
  } else {
    const ranking = Object.keys(estado.objetos)
      .map((id) => ({ id, sobrantes: Number(estado.objetos[id].sobrantes) || 0, datos: estado.objetos[id] }))
      .filter((o) => o.sobrantes > 0)
      .sort((a, b) => b.sobrantes - a.sobrantes);
    const peor = ranking.find((o) => o.datos.ejemplo) || ranking[0] || null;
    const cifra = (n) => A.numero(n);
    const pct = (n) => Number(n).toFixed(1).replace(".", ",") + " %";
    const esperado = {
      repetidas: cifra(estado.resumen.filas_repetidas),
      objetos: `${estado.resumen.con_repetidas} de ${estado.resumen.objetos}`,
      peor: peor ? cifra(peor.sobrantes) : null,
      "peor-objeto": peor ? peor.id : null,
      "peor-pct": peor ? pct(peor.datos.pct_repetidas) : null,
      sobreestima: peor && peor.datos.ejemplo ? pct(peor.datos.ejemplo.pct) : null,
      "ejemplo-periodo": peor && peor.datos.ejemplo ? peor.datos.ejemplo.periodo : null,
    };
    // Toda la página, no sólo el bloque: la etiqueta de la primera pantalla repite
    // una de estas cifras y también tiene que cuadrar.
    const marcasCalidad = [...html.matchAll(/data-calidad="([^"]+)"[^>]*>([^<]*)</g)];
    console.log(`Cifras del bloque de calidad: ${marcasCalidad.length}`);
    if (marcasCalidad.length < 8) {
      fallos.push(`la portada tiene ${marcasCalidad.length} cifras de calidad y se esperaban 8`);
    }
    let desfasadasCalidad = 0;
    for (const [, clave, textoHtml] of marcasCalidad) {
      const valor = esperado[clave];
      if (valor == null) {
        fallos.push(`data-calidad="${clave}" no tiene valor calculado`);
        continue;
      }
      if (textoHtml.trim() !== valor) {
        fallos.push(`data-calidad="${clave}": el HTML dice «${textoHtml.trim()}» y el dato es «${valor}»`);
        desfasadasCalidad += 1;
      }
    }
    console.log(`  desfasadas: ${desfasadasCalidad}`);
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
  console.log(`\nCIFRAS: ${marcas.length} respaldos al día, el README cuadra con el catálogo y ninguna cifra redondea al alza (${cifras.join(" · ")})`);
  return 0;
}

process.exit(main());

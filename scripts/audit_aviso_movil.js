#!/usr/bin/env node
/**
 * La nota de pantalla angosta, comprobada de verdad (jsdom).
 *
 * Historia: primero fue un bloque del flujo que empujaba el contenido; después
 * una tarjeta flotante que se cerraba por tres vías. Las dos se leían como un
 * bloqueo («este sitio es para un computador») aunque el sitio es responsive.
 * Ahora es una franja del flujo que informa dónde rinden mejor el explorador y
 * el mapa, no atrapa el foco ni secuestra el teclado, y se ocupa una vez.
 * `audit_movil.py` comprueba que el CSS y el marcado lo declaren; esto comprueba
 * que funcione, que es otra cosa.
 *
 * Se ejecuta con jsdom (`npm install --no-save jsdom`). Sin jsdom avisa y sale
 * en verde sin fingir que probó algo.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..");
const HTML = path.join(RAIZ, "docs", "index.html");
const CSS = path.join(RAIZ, "docs", "css", "app.css");

let JSDOM;
try {
  ({ JSDOM } = require("jsdom"));
} catch (error) {
  console.log("AVISO-MOVIL: sin jsdom; no se pudo probar el comportamiento");
  process.exit(0);
}

let fallos = 0;
function check(nombre, condicion, detalle) {
  if (condicion) {
    console.log(`OK    ${nombre}`);
  } else {
    fallos += 1;
    console.log(`FALLA ${nombre}${detalle ? " -> " + detalle : ""}`);
  }
}

const html = fs.readFileSync(HTML, "utf8");
const css = fs.readFileSync(CSS, "utf8");

function montar({ ancho = 390, descartado = false } = {}) {
  const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true, url: "https://local/" });
  const w = dom.window;
  // jsdom no aplica media queries: se simula el resultado de matchMedia y el
  // `hidden` que pondría el JS. Lo que se prueba aquí es la lógica del aviso.
  w.matchMedia = (consulta) => ({
    matches: ancho <= 900 && consulta.includes("max-width"),
    media: consulta,
    addEventListener() {},
    removeEventListener() {},
  });
  if (descartado) w.localStorage.setItem("sif-aviso-movil-cerrado", "1");
  const shell = fs.readFileSync(path.join(RAIZ, "docs", "js", "ux_shell.js"), "utf8");
  // jsdom deja el documento en `loading`: `ux_shell.js` espera DOMContentLoaded
  // para arrancar, así que se dispara aquí en vez de esperar al parseo.
  w.eval(shell);
  w.document.dispatchEvent(new w.Event("DOMContentLoaded"));
  const aviso = w.document.getElementById("aviso-movil");
  return { w, aviso };
}

// 1. El marcado y el CSS lo declaran como nota, no como bloqueo --------------
const bloqueCss = css.slice(css.indexOf(".aviso-movil {"), css.indexOf(".aviso-movil[hidden]"));
check("el CSS lo oculta por defecto", /display:\s*none/.test(bloqueCss));
check("el CSS no lo flota sobre el contenido", !/position:\s*(fixed|absolute|sticky)/.test(bloqueCss));
check("el CSS no lo apila en z-index", !/z-index/.test(bloqueCss));
check("el CSS lo muestra sólo en pantalla pequeña",
  /@media \(max-width: 600px\)[\s\S]{0,200}\.aviso-movil\s*\{[\s\S]{0,80}display:\s*flex/.test(css));
// Fuera del layout (que es `overflow: hidden`) y antes del contenido: así se
// anuncia al empezar y no queda al final del documento, tras la app entera.
check("la nota vive fuera del layout",
  html.indexOf('class="aviso-movil"') < html.indexOf('<div class="app-layout">'));
check("la nota precede al contenido principal en el documento",
  html.indexOf('class="aviso-movil"') < html.indexOf('class="main-container"'));
check("no se anuncia como diálogo",
  !/id="aviso-movil"[^>]*\brole=|aria-modal/.test(html));
check("dice que todo el sitio funciona",
  /todo el sitio funciona/.test(html));
check("no vuelve a decir que es para un computador",
  !/pensado para un computador/i.test(html));
check("tiene un botón para ocultarla", html.includes('id="aviso-movil-cerrar"'));
check("el botón tiene nombre accesible",
  /id="aviso-movil-cerrar"[^>]*aria-label="[^"]+"/.test(html));
check("no publica alto para apartar avisos flotantes", !/sif-aviso-alto/.test(css));

// 2. En un teléfono aparece, sin apoderarse del foco -----------------------
{
  const { w, aviso } = montar({ ancho: 390 });
  check("en un teléfono de 390 px aparece", aviso && aviso.hidden === false);
  check("no mueve el foco al aparecer", w.document.activeElement === w.document.body);
  check("no marca el body como bloqueado",
    !aviso.ownerDocument.body.classList.contains("sif-aviso-movil"));
}

// 3. En escritorio no aparece ----------------------------------------------
{
  const { aviso } = montar({ ancho: 1280 });
  check("en un computador no aparece", aviso && aviso.hidden === true);
  check("y no deja la clase colgada en el body",
    !aviso.ownerDocument.body.classList.contains("sif-aviso-movil"));
}

// 4. Se oculta con su botón y lo recuerda ----------------------------------
{
  const { w, aviso } = montar({ ancho: 390 });
  w.document.getElementById("aviso-movil-cerrar").click();
  check("se oculta con su botón", aviso.hidden === true);
  check("  y recuerda el descarte", w.localStorage.getItem("sif-aviso-movil-cerrado") === "1");
}

// 5. Un descarte anterior se respeta ---------------------------------------
{
  const { aviso } = montar({ ancho: 390, descartado: true });
  check("si ya se ocultó antes, no vuelve a aparecer", aviso.hidden === true);
}

// 6. No secuestra el teclado ------------------------------------------------
{
  const { w, aviso } = montar({ ancho: 390 });
  w.document.getElementById("aviso-movil-cerrar").dispatchEvent(
    new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  check("Escape no la trata como diálogo", aviso.hidden === false);
}

// 7. El texto de la nota no promete ni niega de más -------------------------
// Se mira sólo la nota: en otras partes de la página «SQL de solo lectura»
// describe el motor, y eso es correcto.
const cuerpoNota = html.slice(html.indexOf('id="aviso-movil-titulo"'), html.indexOf("</p>", html.indexOf('id="aviso-movil-titulo"')));
check("la nota no dice que algo esté inhabilitado en el teléfono",
  !/no disponible|inhabilitad|necesitas un computador|sólo funciona/i.test(cuerpoNota));
check("la nota no menciona cifras ni plazos que puedan envejecer",
  !/\d/.test(cuerpoNota));

console.log(fallos === 0 ? "\nAVISO-MOVIL: nota del flujo, sólo en pantalla angosta, sin foco ni teclado secuestrados"
  : `\nAVISO-MOVIL: ${fallos} problema(s)`);
process.exit(fallos === 0 ? 0 : 1);

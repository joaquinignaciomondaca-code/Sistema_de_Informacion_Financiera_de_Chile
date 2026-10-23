#!/usr/bin/env node
/**
 * El aviso de teléfono, comprobado de verdad (jsdom).
 *
 * El 2026-10-23 el aviso era un bloque del flujo: empujaba el contenido hacia
 * abajo y se leía como parte de la página, no como algo que se puede quitar. Se
 * convirtió en tarjeta flotante con tres salidas —«Entendido», el aspa y
 * Escape— y descarte recordado. `audit_movil.py` comprueba que el CSS y el
 * marcado lo declaren; esto comprueba que funcione, que es otra cosa.
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

// 1. El marcado y el CSS lo declaran flotante -------------------------------
const bloqueCss = css.slice(css.indexOf(".aviso-movil {"), css.indexOf(".aviso-movil[hidden]"));
check("el CSS lo posiciona como flotante", /position:\s*fixed/.test(bloqueCss));
check("el CSS lo ancla abajo con área segura", /bottom:\s*calc\([^)]*env\(safe-area-inset-bottom/.test(bloqueCss));
check("el CSS lo oculta por defecto", /display:\s*none/.test(bloqueCss));
check("el CSS lo muestra sólo en pantalla pequeña",
  /@media \(max-width: 900px\)[\s\S]{0,200}\.aviso-movil\s*\{[\s\S]{0,80}display:\s*flex/.test(css));
check("el aviso vive fuera del layout",
  html.indexOf('class="aviso-movil"') > html.indexOf("</div> <!-- Cierre de app-layout -->"));
check("tiene aspa además del botón", html.includes('id="aviso-movil-aspa"'));
check("el aspa tiene nombre accesible", /id="aviso-movil-aspa"[^>]*aria-label="[^"]+"/.test(html));

// 2. En un teléfono aparece -------------------------------------------------
{
  const { aviso } = montar({ ancho: 390 });
  check("en un teléfono de 390 px aparece", aviso && aviso.hidden === false);
  // jsdom no calcula layout (`getBoundingClientRect` da 0), así que lo que se
  // comprueba es que la página marque el estado; el alto lo publica el navegador
  // real y el CSS tiene respaldo para cuando no llega.
  check("avisa al body para apartar los avisos breves",
    aviso.ownerDocument.body.classList.contains("sif-aviso-movil"));
  check("el CSS tiene respaldo de alto para los avisos breves",
    /--sif-aviso-alto,\s*\d+px/.test(css));
}

// 3. En escritorio no aparece ----------------------------------------------
{
  const { aviso } = montar({ ancho: 1280 });
  check("en un computador no aparece", aviso && aviso.hidden === true);
  check("y no deja la clase colgada en el body",
    !aviso.ownerDocument.body.classList.contains("sif-aviso-movil"));
}

// 4. Se cierra por las tres vías y lo recuerda -----------------------------
for (const [nombre, accion] of [
  ["«Entendido»", (w) => w.document.getElementById("aviso-movil-cerrar").click()],
  ["el aspa", (w) => w.document.getElementById("aviso-movil-aspa").click()],
  ["Escape", (w) => {
    // Escape sólo cierra la tarjeta si el foco está dentro: un Escape suelto es
    // del explorador o de un modal y no debe llevarse el aviso por delante.
    w.document.getElementById("aviso-movil-aspa").focus();
    w.document.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  }],
]) {
  const { w, aviso } = montar({ ancho: 390 });
  accion(w);
  check(`se cierra con ${nombre}`, aviso.hidden === true);
  check(`  y recuerda el descarte (${nombre})`, w.localStorage.getItem("sif-aviso-movil-cerrado") === "1");
  check(`  y deja de apartar los avisos breves (${nombre})`,
    !w.document.body.classList.contains("sif-aviso-movil"));
}

// 5. Un Escape ajeno no se lleva la tarjeta ---------------------------------
{
  const { w, aviso } = montar({ ancho: 390 });
  w.document.getElementById("main-content").focus();
  w.document.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  check("un Escape con el foco fuera no cierra el aviso", aviso.hidden === false);
}

// 6. Un descarte anterior se respeta ---------------------------------------
{
  const { aviso } = montar({ ancho: 390, descartado: true });
  check("si ya se cerró antes, no vuelve a aparecer", aviso.hidden === true);
}

console.log(fallos === 0 ? "\nAVISO-MOVIL: flota, aparece sólo en el teléfono y se cierra por las tres vías"
  : `\nAVISO-MOVIL: ${fallos} problema(s)`);
process.exit(fallos === 0 ? 0 : 1);

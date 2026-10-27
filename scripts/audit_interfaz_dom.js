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
const metricasPublicadas = JSON.parse(fs.readFileSync(path.join(DOCS, "metricas_publicadas.json"), "utf8"));

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
const alcancesFallback = Array.from(document.querySelectorAll("[data-alcance]"))
  .map((el) => ({ ruta: el.dataset.alcance, texto: el.textContent.trim() }));
const modosFallback = Array.from(document.querySelectorAll("#info-container [data-modo]"))
  .map((el) => ({ modo: el.dataset.modo, texto: el.textContent.trim() }));

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

setTimeout(async () => {
  // El arranque de la página se reparte en tareas (ver el script final de
  // index.html). Se espera la señal explícita antes de mirar el DOM.
  if (window.SIF_LISTO) await window.SIF_LISTO;

  const selectorPaletas = document.getElementById("theme-dropdown-btn");
  const grupoPaletas = document.getElementById("theme-dropdown-menu");
  const opcionesPaleta = Array.from(document.querySelectorAll(".theme-palette-item"));
  const temaOriginal = window.MFCThemes.getCurrentTheme();
  const nombresPaleta = opcionesPaleta.map((boton) => boton.getAttribute("aria-label"));
  check("el selector de paletas identifica el grupo que controla",
    selectorPaletas.getAttribute("aria-label") === "Seleccionar paleta de colores"
      && selectorPaletas.getAttribute("aria-controls") === grupoPaletas.id
      && grupoPaletas.getAttribute("role") === "group"
      && grupoPaletas.getAttribute("aria-label") === "Paletas de colores");
  check("las seis paletas tienen nombres accesibles únicos y descriptivos",
    opcionesPaleta.length === 6
      && nombresPaleta.every((nombre) => nombre && nombre.startsWith("Paleta: "))
      && new Set(nombresPaleta).size === opcionesPaleta.length,
    nombresPaleta.join("; "));
  const paletasSeleccionadas = () => opcionesPaleta.filter((boton) => boton.getAttribute("aria-pressed") === "true");
  check("una sola paleta declara su estado seleccionado y coincide con el tema activo",
    paletasSeleccionadas().length === 1 && paletasSeleccionadas()[0].dataset.theme === temaOriginal);
  selectorPaletas.click();
  check("el selector refleja al abrirse su estado expandido",
    selectorPaletas.getAttribute("aria-expanded") === "true" && document.getElementById("theme-dropdown-container").classList.contains("open"),
    `aria-expanded=${selectorPaletas.getAttribute("aria-expanded")} · open=${document.getElementById("theme-dropdown-container").classList.contains("open")}`);
  const paletaAlternativa = opcionesPaleta.find((boton) => boton.dataset.theme !== temaOriginal);
  if (paletaAlternativa) {
    paletaAlternativa.focus();
    paletaAlternativa.click();
  }
  check("elegir una paleta actualiza selección, cierra el selector y devuelve el foco",
    Boolean(paletaAlternativa)
      && window.MFCThemes.getCurrentTheme() === paletaAlternativa.dataset.theme
      && paletasSeleccionadas().length === 1
      && paletasSeleccionadas()[0] === paletaAlternativa
      && selectorPaletas.getAttribute("aria-expanded") === "false"
      && !document.getElementById("theme-dropdown-container").classList.contains("open")
      && document.activeElement === selectorPaletas);
  selectorPaletas.click();
  const opcionConFoco = opcionesPaleta[0];
  opcionConFoco.focus();
  opcionConFoco.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  check("Escape cierra el selector y devuelve el foco al disparador",
    selectorPaletas.getAttribute("aria-expanded") === "false"
      && !document.getElementById("theme-dropdown-container").classList.contains("open")
      && document.activeElement === selectorPaletas);
  window.MFCThemes.applyTheme(temaOriginal);

  const modalConsultas = document.getElementById("saved-queries-modal");
  const abrirConsultas = document.getElementById("btn-show-favorites");
  const cerrarConsultas = document.getElementById("close-fav-modal");
  check("el cierre de consultas tiene nombre y el disparador controla el panel",
    Boolean(cerrarConsultas)
      && cerrarConsultas.getAttribute("aria-label") === "Cerrar consultas guardadas"
      && Boolean(cerrarConsultas.querySelector('svg[aria-hidden="true"]'))
      && !cerrarConsultas.textContent.trim()
      && abrirConsultas.getAttribute("aria-controls") === modalConsultas.id
      && abrirConsultas.getAttribute("aria-expanded") === "false");
  // Arranque bajo demanda: ni el mapa relacional (canvas) ni el motor DuckDB
  // (wasm de 3,8 MB) deben construirse con la página.
  check("el mapa relacional no se construye al cargar", !window.erdInstance);
  check("el motor DuckDB no arranca al cargar",
    window.DuckDBClient && window.DuckDBClient.initPromise === null);
  check("el gráfico de la Guía arranca oculto y sin pintar",
    document.getElementById("calidad-chart").hidden === true
    && !document.getElementById("calidad-chart").querySelector("canvas"));

  const principal = metricasPublicadas.fuentes.descargas.principal;
  const alcanceInicialDatos = window.SIFAlcance && window.SIFAlcance.datos();
  check("portada: los 74 elementos, filas y bytes visibles coinciden con el artefacto común",
    Boolean(alcanceInicialDatos && alcanceInicialDatos.visible.conjuntos === principal.elementos
      && alcanceInicialDatos.visible.filas === principal.filas
      && alcanceInicialDatos.visible.bytes === principal.bytes
      && window.SIFPortada.valor("visible.conjuntos") === String(principal.elementos)),
    alcanceInicialDatos && alcanceInicialDatos.visible ? `${alcanceInicialDatos.visible.conjuntos} elementos · ${alcanceInicialDatos.visible.filas} filas · ${alcanceInicialDatos.visible.bytes} bytes` : "sin alcance");
  const alcancesDesfasados = alcancesFallback.filter(({ ruta, texto }) =>
    !window.SIFPortada || window.SIFPortada.valor(ruta) !== texto
  );
  check("los valores de respaldo data-alcance de la portada coinciden con el catálogo generado",
    alcancesDesfasados.length === 0,
    alcancesDesfasados.map((x) => `${x.ruta}: ${x.texto}`).join("; ") || `${alcancesFallback.length} valores alineados`);

  const conteoModos = { auto: 0, hybrid: 0, manual: 0 };
  (window.SIFDataDictionary || []).forEach((tabla) => {
    const modo = String(tabla.modo || "").toLowerCase();
    conteoModos[modo.startsWith("híbrido") || modo.startsWith("hibrido")
      ? "hybrid" : modo.startsWith("manual") ? "manual" : "auto"]++;
  });
  const modosEsperados = {
    auto: String(conteoModos.auto),
    hybrid: String(conteoModos.hybrid),
    manual: String(conteoModos.manual),
    total: String((window.SIFDataDictionary || []).length),
  };
  const modosDesfasados = modosFallback.filter(({ modo, texto }) => texto !== modosEsperados[modo]);
  const conteosContrato = metricasPublicadas.fuentes;
  check("la metodología distingue 89 entradas ETL de 90 objetos; modos y respaldos coinciden",
    (window.SIFDataDictionary || []).length === conteosContrato.api_v2.objetos
      && conteosContrato.inventario_etl.tablas !== conteosContrato.api_v2.objetos
      && conteosContrato.inventario_etl.tablas === 89
      && conteosContrato.api_v2.objetos === 90
      && conteoModos.auto === 89 && conteoModos.hybrid === 1 && conteoModos.manual === 0
      && modosDesfasados.length === 0
      && /89 entradas de origen/.test(document.querySelector(".info-processing-block").textContent)
      && /bancos_cmf_lineas/.test(document.querySelector(".info-processing-block").textContent),
    `ETL ${conteosContrato.inventario_etl.tablas} · objetos ${conteosContrato.api_v2.objetos} · automáticos ${conteoModos.auto} · híbridos ${conteoModos.hybrid}`);

  const tabIds = ["tab-btn-info", "tab-btn-erd", "tab-btn-dict", "tab-btn-data", "tab-btn-sql",
    "tab-btn-downloads", "tab-btn-guia"];
  check("existen las 7 pestañas", tabIds.every((id) => document.getElementById(id)),
    tabIds.filter((id) => !document.getElementById(id)).join(", "));
  check("la pestaña Guía arranca oculta y no roba el foco a Información",
    document.getElementById("guia-container").style.display === "none"
    && document.getElementById("info-container").style.display !== "none");
  check("la pestaña de normativa está retirada", !document.getElementById("tab-btn-normativa") && !document.getElementById("normativa-container"));
  check("cada pestaña apunta a un panel existente", tabIds.every((id) => {
    const controls = document.getElementById(id).getAttribute("aria-controls");
    return controls && document.getElementById(controls);
  }));
  const pestañasPrincipales = tabIds.map((id) => document.getElementById(id));
  const índiceSeleccionado = pestañasPrincipales.findIndex((boton) => boton.getAttribute("aria-selected") === "true");
  const pestañaSeleccionada = pestañasPrincipales[índiceSeleccionado] || pestañasPrincipales[0];
  check("el tablist principal mantiene una sola parada de tabulación",
    índiceSeleccionado >= 0 && pestañasPrincipales.filter((boton) => boton.tabIndex === 0).length === 1 && pestañaSeleccionada.tabIndex === 0);
  const moverConFlecha = (boton, key) => boton.dispatchEvent(new window.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }));
  pestañaSeleccionada.focus();
  moverConFlecha(pestañaSeleccionada, "ArrowRight");
  const pestañaSiguiente = pestañasPrincipales[(índiceSeleccionado + 1) % pestañasPrincipales.length];
  check("flecha derecha mueve el foco sin activar la pestaña ni arrancar SQL",
    document.activeElement === pestañaSiguiente && pestañaSiguiente.tabIndex === 0 &&
      pestañaSeleccionada.getAttribute("aria-selected") === "true" &&
      window.DuckDBClient.initPromise === null);
  moverConFlecha(pestañaSiguiente, "ArrowLeft");
  check("flecha izquierda devuelve el foco al tab seleccionado",
    document.activeElement === pestañaSeleccionada && pestañaSeleccionada.tabIndex === 0 &&
      pestañaSeleccionada.getAttribute("aria-selected") === "true");
  const índiceSql = tabIds.indexOf("tab-btn-sql");
  let índiceFoco = índiceSeleccionado;
  while (índiceFoco !== índiceSql) {
    moverConFlecha(pestañasPrincipales[índiceFoco], "ArrowRight");
    índiceFoco = (índiceFoco + 1) % pestañasPrincipales.length;
  }
  check("llegar a Consultas con flechas no activa el panel ni arranca DuckDB",
    document.activeElement === pestañasPrincipales[índiceSql] &&
      pestañasPrincipales[índiceSql].getAttribute("aria-selected") === "false" &&
      document.getElementById("sql-container").style.display === "none" &&
      window.DuckDBClient.initPromise === null);
  while (índiceFoco !== índiceSeleccionado) {
    moverConFlecha(pestañasPrincipales[índiceFoco], "ArrowLeft");
    índiceFoco = (índiceFoco - 1 + pestañasPrincipales.length) % pestañasPrincipales.length;
  }
  moverConFlecha(pestañaSeleccionada, "End");
  const ultimaPestaña = pestañasPrincipales[pestañasPrincipales.length - 1];
  const finEnFoco = document.activeElement === ultimaPestaña &&
    pestañaSeleccionada.getAttribute("aria-selected") === "true";
  moverConFlecha(ultimaPestaña, "Home");
  check("Home y End recorren el tablist sin cambiar la pestaña activa",
    finEnFoco && document.activeElement === pestañasPrincipales[0] &&
      pestañaSeleccionada.getAttribute("aria-selected") === "true");

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
    filtradas.length > 0 && filtradas.length < tarjetas.length && /\d+ de \d+ conjuntos/.test(document.getElementById("dl-counter").textContent),
    filtradas.length + " visibles · " + document.getElementById("dl-counter").textContent);
  buscador.value = "";
  buscador.dispatchEvent(new window.Event("input", { bubbles: true }));

  const selectorSector = document.getElementById("dl-sector");
  const opcionesSector = Array.from(selectorSector.options).map((o) => o.value).filter((v) => v !== "todos").sort();
  const ADescargas = window.SIFAlcance;
  const sectoresCatalogados = [...new Set((window.DOWNLOAD_CATALOG.grupos || [])
    .filter((g) => (g.items || []).some((item) => !item.oculto))
    .map((g) => ADescargas.agrupacionDe(g.clave) || g.clave).filter(Boolean))].sort();
  check("descargas: las opciones del filtro derivan de claves sectoriales del catálogo y agrupaciones declaradas",
    opcionesSector.length > 0 && opcionesSector.join(",") === sectoresCatalogados.join(","),
    `filtro=${opcionesSector.join(",")} · catálogo=${sectoresCatalogados.join(",")}`);
  const opcionSector = Array.from(selectorSector.options).find((o) => o.value !== "todos");
  selectorSector.value = opcionSector ? opcionSector.value : "todos";
  selectorSector.dispatchEvent(new window.Event("change", { bubbles: true }));
  const porSector = document.querySelectorAll("#downloads-container .dl-item:not([hidden])");
  check("el filtro por sector acota el catálogo",
    Boolean(opcionSector) && porSector.length > 0 && porSector.length < tarjetas.length,
    porSector.length + " de " + (opcionSector ? opcionSector.value : "sector"));
  selectorSector.value = "todos";
  selectorSector.dispatchEvent(new window.Event("change", { bubbles: true }));

  // Vocabulario: nombres canónicos y ninguna lista de entidades con otro nombre.
  const nombres = Array.from(document.querySelectorAll("#downloads-container .dl-item"))
    .map((n) => n.dataset.id);
  const etiquetasManuales = Array.from(document.querySelectorAll("#downloads-container .dl-item-title code"))
    .map((n) => n.textContent.trim());
  check("las vistas usan IDs canónicos y la renta fija conserva el nombre CMF",
    nombres.length > 40 && nombres.every((n) => /^[a-z0-9_]+$/.test(n)) &&
    nombres.includes("seguros_renta_fija") && etiquetasManuales.some((n) => n === "B.1 INSTRUMENTOS DE RENTA FIJA"),
    nombres.length ? nombres.filter((n) => !/^[a-z0-9_]+$/.test(n)).join(", ") || etiquetasManuales.find((n) => n.startsWith("B.1")) : "sin nombres");
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

  // Con el motor caído, CSV/Excel avisan en vez de fallar en silencio. El motor
  // arranca bajo demanda, así que aquí se simula el estado final de un arranque
  // que no pudo completarse (antes ese estado llegaba solo porque el motor se
  // inicializaba al cargar la página).
  if (window.DuckDBClient) {
    window.DuckDBClient.initPromise = Promise.resolve();
    window.DuckDBClient.engineAvailable = false;
    window.DownloadsPanel.refrescarEstadoMotor();
  }
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

  // Se deja el motor sin arrancar otra vez para comprobar el cableado real:
  // abrir Consultas debe disparar ensureStarted() (el estado «sin motor» que se
  // simuló más arriba no es el de una página recién cargada).
  if (window.DuckDBClient) {
    window.DuckDBClient.initPromise = null;
    window.DuckDBClient.engineAvailable = false;
  }
  window.switchMainTab("sql");
  // El disparador vive en el panel SQL: probar el retorno de foco con el panel
  // visible reproduce el único recorrido real desde el que se puede abrirlo.
  window.ChatTerminal.toggleFavoritesModal();
  const modalAbierto = modalConsultas.classList.contains("visible");
  const estadoExpandidoAlAbrir = abrirConsultas.getAttribute("aria-expanded");
  cerrarConsultas.focus();
  cerrarConsultas.click();
  check("el botón accesible cierra el panel, actualiza el estado y devuelve el foco",
    modalAbierto
      && estadoExpandidoAlAbrir === "true"
      && !modalConsultas.classList.contains("visible")
      && abrirConsultas.getAttribute("aria-expanded") === "false"
      && document.activeElement === abrirConsultas);
  check("abrir Consultas arranca el motor bajo demanda",
    Boolean(window.DuckDBClient && window.DuckDBClient.initPromise));
  check("pestaña SQL activa y visible",
    document.getElementById("sql-container").style.display === "flex" &&
    document.getElementById("tab-btn-sql").getAttribute("aria-selected") === "true");
  check("el resto queda oculto",
    document.getElementById("info-container").style.display === "none" &&
    document.getElementById("downloads-container").style.display === "none");
  window.switchMainTab("erd");
  check("abrir Mapa construye el mapa relacional", Boolean(window.erdInstance));
  check("mapa: filtros y zoom visibles",
    document.getElementById("erd-controls-group").style.display === "flex" &&
    document.querySelector(".zoom-controls").style.display === "flex");
  const nodoEsquema = window.erdInstance.tables[0];
  const modalEsquema = document.getElementById("schema-modal");
  const botonCerrarEsquema = document.getElementById("close-schema-modal");
  const disparadorEsquema = document.getElementById("btn-zoom-reset");
  disparadorEsquema.focus();
  window.erdInstance.showSchemaModal(nodoEsquema);
  check("mapa: diálogo de esquema anuncia tabla y cierre accesible",
    modalEsquema.getAttribute("role") === "dialog"
      && modalEsquema.getAttribute("aria-labelledby") === "modal-table-name"
      && document.getElementById("modal-table-name").textContent === nodoEsquema.name
      && botonCerrarEsquema.getAttribute("aria-label") === "Cerrar el esquema de la tabla"
      && botonCerrarEsquema.type === "button");
  check("mapa: al abrir esquema el foco entra en Cerrar",
    modalEsquema.classList.contains("visible") && document.activeElement === botonCerrarEsquema);
  botonCerrarEsquema.click();
  check("mapa: cerrar esquema con botón devuelve el foco",
    !modalEsquema.classList.contains("visible") && document.activeElement === disparadorEsquema);
  disparadorEsquema.focus();
  window.erdInstance.showSchemaModal(nodoEsquema);
  document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  check("mapa: Escape cierra esquema y devuelve el foco",
    !modalEsquema.classList.contains("visible") && document.activeElement === disparadorEsquema);
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
  check("barra de contexto describe la ubicación (solo la industria, sin ruta de tabla)",
    chip.textContent.includes("Seguros") && !chip.textContent.includes(" › "), chip.textContent);

  const input = document.getElementById("chat-input");
  input.value = "SELECT * FROM segur";
  input.selectionStart = input.selectionEnd = input.value.length;
  window.ChatTerminal.completeInput();
  check("Tab completa nombres de vista", input.value.startsWith("SELECT * FROM seguros_"), input.value);
  input.value = "SELECT * FROM ffmm_cartera_extranjera_ultima";
  input.selectionStart = input.selectionEnd = input.value.length;
  window.ChatTerminal.completeInput();
  check("Tab ofrece las vistas auxiliares SQL-only",
    input.value === "SELECT * FROM ffmm_cartera_extranjera_ultima_particion", input.value);

  const antes = document.querySelectorAll("#chat-messages .message").length;
  window.ChatTerminal.clearTerminal();
  check("Limpiar deja sólo la bienvenida",
    antes > 0 && document.querySelectorAll("#chat-messages .message").length === 1);

  // Estados de consulta: espera, éxito, error SQL y excepción deben diferenciarse.
  const clienteQueryOriginal = window.DuckDBClient;
  const inputConsulta = document.getElementById("chat-input");
  const botonEjecutar = document.getElementById("send-btn");
  const mensajesSql = document.getElementById("chat-messages");
  check("SQL: el registro de mensajes anuncia cambios de estado", mensajesSql.getAttribute("aria-live") === "polite");
  let resolverConsulta;
  let sqlCapturado = "";
  window.DuckDBClient = {
    query(sql) {
      sqlCapturado = sql;
      return new Promise((resolve) => { resolverConsulta = resolve; });
    }
  };
  inputConsulta.value = "SELECT 1 AS n";
  const promesaSql = window.ChatTerminal.handleSend();
  check("SQL: ejecución muestra estado en curso y bloquea el botón",
    botonEjecutar.disabled && Array.from(mensajesSql.querySelectorAll(".message"))
      .some((m) => /Ejecutando consulta con DuckDB-Wasm/.test(m.textContent)), sqlCapturado);
  resolverConsulta({ success: true, columns: ["n"], rows: [{ n: 1 }], count: 1, elapsedMs: 2 });
  await promesaSql;
  const resultadoSql = mensajesSql.querySelector(".query-meta");
  check("SQL: éxito muestra filas y una grilla de resultado",
    Boolean(resultadoSql && /1 fila/.test(resultadoSql.textContent) && mensajesSql.querySelector(".results-table tbody tr")));
  check("SQL: éxito retira el estado en curso y reactiva Ejecutar",
    !botonEjecutar.disabled && !Array.from(mensajesSql.querySelectorAll(".message"))
      .some((m) => /Ejecutando consulta con DuckDB-Wasm/.test(m.textContent)));

  window.DuckDBClient = { query: async () => ({ success: true, columns: ["n"], rows: [], count: 0, elapsedMs: 1 }) };
  inputConsulta.value = "SELECT n FROM t WHERE false";
  await window.ChatTerminal.handleSend();
  const vacioSql = mensajesSql.querySelector(".query-empty-state");
  check("SQL: éxito sin filas se diferencia del error y explica el resultado",
    Boolean(vacioSql && vacioSql.getAttribute("role") === "status" && /no devolvió filas/.test(vacioSql.textContent)));

  window.DuckDBClient = { query: async () => ({ success: false, error: "Parser Error: sintaxis" }) };
  inputConsulta.value = "SELEC FROM";
  await window.ChatTerminal.handleSend();
  const errorSql = mensajesSql.querySelector(".message:last-child");
  check("SQL: error de consulta se distingue como Error SQL",
    Boolean(errorSql && /\[Error SQL\]/.test(errorSql.textContent) && /Parser Error/.test(errorSql.textContent)));

  window.DuckDBClient = { query: async () => { throw new Error("worker no disponible"); } };
  inputConsulta.value = "SELECT 1";
  await window.ChatTerminal.handleSend();
  const excepcionSql = mensajesSql.querySelector(".message:last-child");
  check("SQL: excepción del motor se distingue de un Error SQL",
    Boolean(excepcionSql && /\[Excepción\]/.test(excepcionSql.textContent) && /worker no disponible/.test(excepcionSql.textContent)));
  check("SQL: todos los finales de consulta devuelven el botón a estado listo", !botonEjecutar.disabled);
  window.DuckDBClient = clienteQueryOriginal;
  window.ChatTerminal.clearTerminal();

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
  const descargasMotor = document.getElementById("btn-engine-downloads");
  check("el fallo de DuckDB ofrece una alternativa y aclara los formatos",
    Boolean(descargasMotor && /Abrir Descargas/.test(descargasMotor.textContent) &&
      /Parquet original/.test(alert.textContent) && /CSV y Excel requieren el motor/.test(alert.textContent)));
  if (descargasMotor) descargasMotor.click();
  check("la alternativa abre Descargas, enfoca su pestaña y conserva el Parquet directo",
    document.getElementById("downloads-container").style.display === "flex" &&
      document.getElementById("tab-btn-downloads").getAttribute("aria-selected") === "true" &&
      document.activeElement === document.getElementById("tab-btn-downloads") &&
      Boolean(document.querySelector('#downloads-container a[download$=".parquet"]')));
  window.switchMainTab("sql");

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
  check("estado listo se anuncia en el punto de estado SQL",
    document.getElementById("sql-engine-dot").classList.contains("ready") &&
      /operativo/.test(document.getElementById("sql-engine-dot").title));
  check("la pista indica motor local",
    /navegador|local/i.test(document.getElementById("sql-engine-hint").textContent),
    document.getElementById("sql-engine-hint").textContent.slice(0, 70));

  // ── Recorte visual de industrias (alcance editorial, 2026-10-20) ─────────
  // La portada, el explorador, el mapa, el diccionario, el visor y Descargas leen la
  // misma bandera por sector; el archivo queda al final y plegado, pero alcanzable.
  const alcance = window.DOWNLOAD_CATALOG.alcance;
  const A = window.SIFAlcance;
  check("el catálogo trae el alcance editorial", Boolean(alcance && A && A.disponible()));
  const cifra = (ruta) => (document.querySelector(`[data-alcance="${ruta}"]`) || {}).textContent;
  const nucleo = alcance.niveles.find((n) => n.id === "nucleo");
  check("la portada muestra sólo los conteos esenciales del núcleo desde el catálogo",
    cifra("nucleo.sectores") === "3" && cifra("nucleo.conjuntos") === String(nucleo.conjuntos)
    && !document.querySelector(".info-nucleo-cifras [data-alcance='nucleo.filas']"),
    [cifra("nucleo.sectores"), cifra("nucleo.conjuntos")].join(" · "));
  check("la portada no promete una cobertura global (cada tabla tiene su periodo)",
    !/cobertura máxima/.test(document.getElementById("info-container").textContent)
    && !/data-alcance="nucleo\.periodo"/.test(document.getElementById("info-container").innerHTML));
  check("la portada tiene tres tarjetas grandes: seguros, fondos mutuos y fondos de inversión",
    Array.from(document.querySelectorAll(".info-core-card")).map((c) => c.dataset.sector).join(",") === "seguros,ffmm,fi");
  check("el inicio destaca la propuesta y ofrece explorar o ir a descargas",
    /abierto en datos/.test(document.getElementById("home-title").textContent)
    && Boolean(document.querySelector('.info-hero-btn[href="#catalogo-principal"]'))
    && Boolean(document.querySelector('.info-hero-btn[data-portada="descargas"]')));
  check("la portada ya no anuncia 15 industrias",
    !/15 industrias/.test(document.getElementById("info-container").textContent));
  // El detalle de alcance y metodología se conserva, pero deja de competir
  // con la navegación principal: aparece bajo una divulgación cerrada.
  const alcanceDetalle = document.getElementById("info-alcance");
  const textoAlcance = alcanceDetalle.textContent;
  const lineasAlcance = document.querySelectorAll("#info-alcance > p:not(.info-scope-foot)");
  check("el alcance completo queda disponible en detalles plegados y sólo enumera lo publicado",
    alcanceDetalle.closest("details").open === false && lineasAlcance.length === 3 &&
    !/no incluye|no se publica|no publicó|no publica/i.test(textoAlcance) &&
    /más de 19 millones/.test(document.querySelector("#info-alcance .info-scope-foot").textContent),
    textoAlcance.slice(0, 80));

  const archivoNav = document.querySelector("#sidebar-tree .tree-archive");
  check("explorador: el archivo está al final y plegado",
    archivoNav && !archivoNav.classList.contains("open") &&
    archivoNav === document.querySelector("#sidebar-tree .tree-root").lastElementChild);
  check("explorador: el núcleo va primero",
    document.querySelector("#sidebar-tree .tree-tier").dataset.tier === "nucleo");
  const buscadorNav = document.getElementById("sidebar-search");
  buscadorNav.value = "factoring";
  buscadorNav.dispatchEvent(new window.Event("input", { bubbles: true }));
  check("explorador: la búsqueda encuentra industrias archivadas y abre el archivo",
    archivoNav.classList.contains("search-open") &&
    document.querySelector('[data-group-id="group_factoring_leasing"]').style.display !== "none");
  buscadorNav.value = "";
  buscadorNav.dispatchEvent(new window.Event("input", { bubbles: true }));
  check("explorador: al limpiar la búsqueda el archivo vuelve a plegarse", !archivoNav.classList.contains("search-open"));

  window.switchMainTab("erd");
  const grupoMapa = document.getElementById("erd-group-select");
  const sectorMapa = document.getElementById("erd-sector-select");
  check("mapa: filtros dependientes Grupo y Sector disponibles", Boolean(grupoMapa && sectorMapa));
  window.erdInstance.focusSector("patrimonios_separados");

  check("mapa: securitizadoras y patrimonios separados se ven como una sola entrada",
    window.erdInstance.filter === "securitizacion" && grupoMapa.value === "archivo" && sectorMapa.value === "securitizacion" &&
    window.erdInstance.tables.filter((t) => window.erdInstance.matchesFilter(t)).length === 5);
  check("mapa: una industria archivada muestra el aviso de alcance",
    !document.getElementById("erd-scope-note").hidden && /Alcance congelado/.test(document.getElementById("erd-scope-note").textContent));
  window.erdInstance.focusSector("todos");
  const enPrincipal = window.erdInstance.tables.filter((t) => window.erdInstance.matchesFilter(t));
  check("mapa: la vista principal no incluye el archivo",
    enPrincipal.length > 0 && enPrincipal.every((t) => A.esVisible(t.sector)), enPrincipal.length + " nodos");
  window.erdInstance.focusSector("afp_corporativo");
  check("mapa: el alias del explorador para AFP encuentra su nodo",
    window.erdInstance.tables.some((t) => window.erdInstance.matchesFilter(t) && t.id === "afp_lista_entidades"));
  window.erdInstance.focusSector("seguros");

  window.switchMainTab("dict");
  const fichas = () => Array.from(document.querySelectorAll("#dict-container .dict-table-name")).map((n) => n.textContent.trim());
  window.SIFTableContext.clear();
  window.DataDictionary.currentGroup = "todos";
  window.DataDictionary.setFilter("todos");
  check("diccionario: todos los grupos permite descubrir también archivo y tablas sin datos",
    fichas().length > 0 && fichas().includes("ccaf.balance") && fichas().includes("fi.bienes_raices") &&
    fichas().some((n) => n.startsWith("B.1 INSTRUMENTOS DE RENTA FIJA")), fichas().filter((n) => n === "ccaf.balance" || n === "fi.bienes_raices").join(", ") || fichas().length + " fichas");
  window.DataDictionary.setFilter("registro");
  check("diccionario: el registro complementario reúne las cuatro listas",
    fichas().sort().join(",") === "afp.lista_entidades,cooperativas.lista_entidades,fintech.lista_entidades,sistemas_pago.lista_entidades" &&
    document.querySelectorAll("#dict-container .dict-scope-box").length === 4, fichas().join(","));
  window.DataDictionary.setFilter("principal");
  const fichaTecnica = window.DataDictionary.renderSource("Ficha CMF: https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf");
  check("diccionario: la ficha técnica CMF se presenta como enlace seguro y clicable",
    fichaTecnica.includes('<a href="https://www.cmfchile.cl/') && fichaTecnica.includes('rel="noopener noreferrer"') && !fichaTecnica.includes("&lt;a"));

  // Dos selecciones rápidas: la respuesta tardía de B.12 no puede sustituir
  // la vista tipo 6 elegida después.
  const clienteDuckDBReal = window.DuckDBClient;
  const sidebarReal = window.SidebarNav;
  const renderReal = window.DataViewer.render;
  const consultasPendientes = [];
  window.DuckDBClient = { query: (sql) => new Promise((resolve) => consultasPendientes.push({ sql, resolve })) };
  window.SidebarNav = null;
  window.DataViewer.render = () => {};
  const consultaAnterior = window.DataViewer.loadTable("seguros_prestamos", "B.12 PRÉSTAMOS");
  const consultaActual = window.DataViewer.loadTable("seguros_registros_tipo6", "Registros tipo 6");
  consultasPendientes[1].resolve({ success: true, columns: ["tipo_registro"], rows: [{ tipo_registro: "6" }], count: 1 });
  await consultaActual;
  consultasPendientes[0].resolve({ success: false, error: "Table seguros_prestamos does not exist" });
  await consultaAnterior;
  check("visor: una respuesta atrasada de otra tabla no pisa el tipo 6 seleccionado",
    window.DataViewer.currentView === "seguros_registros_tipo6" &&
    window.DataViewer.currentRows.length === 1 && window.DataViewer.currentRows[0].tipo_registro === "6" &&
    !window.DataViewer.error);
  window.DuckDBClient = clienteDuckDBReal;
  window.SidebarNav = sidebarReal;
  window.DataViewer.render = renderReal;

  const grupos = window.DataViewer.catalogoOrdenado();
  check("visor: los grupos siguen el orden editorial y el archivo se rotula",
    /^Seguros/.test(grupos[0].etiqueta) && grupos.some((g) => /^Archivo · /.test(g.etiqueta)) &&
    !grupos.some((g) => g.tablas.some((t) => t.id === "fi_bienes_raices")), grupos.slice(0, 3).map((g) => g.etiqueta).join(" | "));

  // Columnas del visor: un estado financiero se lee como el estado (periodo, institución,
  // cuenta, importe), no como el volcado técnico del archivo de origen. Las columnas
  // técnicas no se borran: quedan tras el botón «Todas las columnas».
  // Las 13 columnas que publica `bancos_cmf_lineas` desde el recorte de esquema.
  const COLUMNAS_BALANCE = [
    "periodo", "codigo_institucion", "rut", "razon_social", "codigo_cuenta",
    "glosa_cuenta", "tipo_linea", "importe_clp", "importes_fuente_raw",
    "familia_archivo_fuente", "modelo_cmf", "nivel_consolidacion", "numero_fila_fuente"
  ];
  // El nombre de la columna está en el botón de orden; la subetiqueta va aparte.
  const cabecerasVisor = () => [...document.querySelectorAll("#data-viewer-container .dv-table th .th-sort-btn")]
    .map((b) => b.textContent.trim());
  window.DataViewer.currentView = "bancos_balance";
  window.DataViewer.currentColumns = COLUMNAS_BALANCE.slice();
  // Fila real: 2022-01, Banco de Chile, TOTAL ACTIVOS. El desglose por moneda llega
  // como el texto JSON de la lista (así lo devuelve el motor), no como arreglo.
  window.DataViewer.currentRows = [{
    periodo: "2022-01", codigo_institucion: "001", rut: "97004000", razon_social: "Banco de Chile",
    codigo_cuenta: "100000000", glosa_cuenta: "TOTAL ACTIVOS", tipo_linea: "total",
    importe_clp: 50164403436446,
    importes_fuente_raw: "[26458735676131,00,18194231752989,00,0086353276604,00,5425082730722,00]",
    familia_archivo_fuente: "B1", modelo_cmf: "MB1", nivel_consolidacion: "consolidado_global",
    numero_fila_fuente: 3
  }];
  window.DataViewer.mostrarTodasLasColumnas = false;
  window.DataViewer.render();
  check("visor: el balance abre por periodo, institución, cuenta e importe",
    cabecerasVisor().slice(0, 8).join(",") ===
      "periodo,codigo_institucion,rut,razon_social,codigo_cuenta,glosa_cuenta,tipo_linea,importe_clp",
    cabecerasVisor().slice(0, 8).join(","));
  check("visor: la traza a la línea del TXT no ocupa la tabla",
    cabecerasVisor().length === 12 && !cabecerasVisor().includes("numero_fila_fuente"),
    cabecerasVisor().join(","));
  const botonColumnas = document.querySelector("#data-viewer-container .dv-cols-btn");
  check("visor: hay un botón que ofrece las columnas restantes",
    Boolean(botonColumnas) && /Todas las columnas \(13\)/.test(botonColumnas.textContent) &&
    /window\.DataViewer\.alternarColumnas\(\)/.test(botonColumnas.getAttribute("onclick")));
  // jsdom en modo "outside-only" no ejecuta los onclick en línea: se llama al método
  // que el botón invoca y se comprueba aparte que el botón lo tenga enlazado.
  window.DataViewer.alternarColumnas();
  check("visor: el botón devuelve las 13 columnas en el mismo orden editorial",
    cabecerasVisor().length === COLUMNAS_BALANCE.length &&
    cabecerasVisor().slice(0, 2).join(",") === "periodo,codigo_institucion" &&
    cabecerasVisor().slice(-1).join(",") === "numero_fila_fuente",
    cabecerasVisor().length + " columnas");
  window.DataViewer.alternarColumnas();
  check("visor: se vuelve a las columnas del dato",
    cabecerasVisor().length === 12 && /Columnas del dato|Todas las columnas/.test(
      document.querySelector("#data-viewer-container .dv-cols-btn").textContent));
  const contadorMuestra = document.querySelector("#data-viewer-container .dv-count-info");
  const avisoMuestra = document.querySelector("#data-viewer-container .dv-sample-hint");
  const limitesMuestra = Array.from(document.querySelectorAll("#data-viewer-container .dv-limit-btn"))
    .map((b) => b.textContent.trim()).join(",");
  check("visor: rotula las filas como muestra y no como total",
    /Muestra: 1 fila/.test(contadorMuestra.textContent) && /no es el total/.test(contadorMuestra.title),
    contadorMuestra.textContent);
  check("visor: distingue filtro y orden de pantalla de la descarga completa",
    /filtro y el orden solo afectan la pantalla/.test(avisoMuestra.textContent) && /no la descarga completa/.test(avisoMuestra.textContent),
    avisoMuestra.textContent);
  check("visor: los controles son topes, no páginas, de 50 a 500 filas",
    /Máx\. filas/.test(document.querySelector("#data-viewer-container .dv-limit-label").textContent) &&
      /no es paginación/.test(document.querySelector("#data-viewer-container .dv-limit-label").title) &&
      limitesMuestra === "50,100,250,500",
    limitesMuestra);
  window.DataViewer.setFilter("banco");
  check("visor: el filtro cuenta solo las filas de la muestra cargada",
    /1 de 1 fila de muestra/.test(contadorMuestra.textContent), contadorMuestra.textContent);
  window.DataViewer.setFilter("");
  const filaTexto = () => document.querySelector("#data-viewer-container .dv-table tbody tr").textContent;
  check("visor: el desglose por moneda se muestra como importe legible",
    /26\.458\.735\.676\.131 · 18\.194\.231\.752\.989 · 86\.353\.276\.604 · 5\.425\.082\.730\.722/.test(filaTexto()) &&
    !/\[/.test(filaTexto()), filaTexto().slice(0, 160));
  check("visor: la cabecera dice qué es cada componente del desglose",
    /nacional · reajustable IPC · reajustable por tipo de cambio · extranjera/.test(
      document.querySelector("#data-viewer-container .dv-table th:nth-child(9)").textContent),
    (document.querySelector("#data-viewer-container .dv-table th:nth-child(9) .dv-th-sub") || {}).textContent);
  // El desglose que se muestra tiene que sumar el importe publicado en la misma fila.
  const celdasFila = [...document.querySelectorAll("#data-viewer-container .dv-table tbody tr td")];
  const sumaComponentes = celdasFila[8].textContent.split("·")
    .map((v) => Number(v.replace(/\./g, "").replace(/\s/g, "")))
    .reduce((a, b) => a + b, 0);
  const importePublicado = Number(celdasFila[7].textContent.replace(/[^\d]/g, ""));
  check("visor: los cuatro componentes suman el importe en pesos de la fila",
    sumaComponentes === importePublicado && importePublicado === 50164403436446,
    `${sumaComponentes} vs ${importePublicado}`);

  // El TXT de la CMF no trae las líneas en el orden del estado: al cargar, la tabla
  // se ordena por institución y código de cuenta.
  const clienteOrden = window.DuckDBClient;
  const sidebarOrden = window.SidebarNav;
  const filaBalance = (institucion, cuenta) => ({
    id: institucion + "-" + cuenta, periodo: "2026-08", codigo_institucion: institucion,
    rut: "97004000", razon_social: "Banco " + institucion, codigo_cuenta: cuenta,
    glosa_cuenta: "cuenta " + cuenta, tipo_linea: "total", importe_clp: 1,
    importes_fuente_raw: ["0", "0", "0", "1"], familia_archivo_fuente: "B1", modelo_cmf: "MB1",
    nivel_consolidacion: "consolidado"
  });
  window.SidebarNav = null;
  window.DuckDBClient = {
    query: async () => ({
      success: true, count: 3, columns: COLUMNAS_BALANCE.slice(),
      rows: [filaBalance("001", "411000000"), filaBalance("002", "105000000"),
        filaBalance("001", "100000000")]
    })
  };
  await window.DataViewer.loadTable("bancos_balance", "bancos.balance", 100);
  const ordenCargado = window.DataViewer.currentRows
    .map((r) => r.codigo_institucion + ":" + r.codigo_cuenta).join(",");
  check("visor: el balance se carga en el orden del estado (institución y cuenta)",
    ordenCargado === "001:100000000,001:411000000,002:105000000", ordenCargado);
  window.DuckDBClient = clienteOrden;
  window.SidebarNav = sidebarOrden;

  window.switchMainTab("downloads");
  check("contexto: Descargas sigue la tabla seleccionada sin requerir otra búsqueda",
    window.DownloadsPanel.busqueda === "bancos_balance");
  window.SIFTableContext.clear();
  window.DownloadsPanel.container.querySelector("#dl-clear").click();
  const itemsDl = () => Array.from(document.querySelectorAll("#downloads-container .dl-item"));
  const visiblesDl = () => itemsDl().filter((i) => !i.hidden);
  check("descargas: el archivo empieza plegado y fuera del conteo visible",
    visiblesDl().every((i) => i.dataset.fuera !== "1") && itemsDl().some((i) => i.dataset.fuera === "1"));
  check("descargas: fi.bienes_raices (0 filas) no se lista",
    !itemsDl().some((i) => i.dataset.id === "fi_bienes_raices"));
  const ordenCorredoras = itemsDl().map((i) => i.dataset.id).filter((id) => id.startsWith("corredoras_bolsa_lista"));
  check("descargas: la lista registro de corredoras va bajo la lista principal",
    ordenCorredoras.join(",") === "corredoras_bolsa_lista_entidades,corredoras_bolsa_lista_entidades_registro" &&
    document.querySelector('[data-id="corredoras_bolsa_lista_entidades_registro"]').classList.contains("dl-item-variante"));
  document.querySelector("#dl-archive .dl-archive-toggle").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("descargas: al abrir el archivo aparece el catálogo completo",
    visiblesDl().length === itemsDl().length, visiblesDl().length + " de " + itemsDl().length);
  document.querySelector("#dl-archive .dl-archive-toggle").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));

  // Autoría y reproducibilidad (docs/js/creditos.js). El sitio no publica cita,
  // DOI, versión congelada ni una fecha de corte única: la cobertura no es
  // homogénea y cada tabla declara su periodo. Estos checks cuidan esa frontera.
  const creditosAutor = document.getElementById("creditos-autor");
  const creditosGuia = document.getElementById("creditos-guia");
  const creditosPuntero = document.getElementById("creditos-puntero");
  check("autoría: el bloque de autoría se pinta en Información",
    /Sobre el autor/.test(creditosAutor.textContent) && /Joaquín Mondaca/.test(creditosAutor.textContent));
  check("autoría: declara cuándo partió el proyecto",
    /septiembre de 2026/.test(creditosAutor.textContent));
  check("portada: autoría, nota y auditorías forman un remate visual único",
    Boolean(document.querySelector(".info-endmatter-grid #creditos-autor"))
    && Boolean(document.querySelector(".info-endmatter .info-note"))
    && Boolean(document.querySelector(".info-endmatter a.info-foot .info-foot-copy small")));
  check("autoría: no queda ningún bloque de citación en el sitio",
    !document.getElementById("cita-info") && !document.getElementById("cita-autor")
    && !document.getElementById("cita-descargas"));
  // El chequeo se acota a Información y Descargas: en el Diccionario la palabra
  // «pendiente» aparece describiendo columnas de las fuentes, y eso es legítimo.
  const textoSitio = creditosAutor.textContent + " " + creditosGuia.textContent + " "
    + document.getElementById("info-container").textContent + " "
    + document.getElementById("downloads-container").textContent + " "
    + document.getElementById("guia-container").textContent;
  check("autoría: el sitio no menciona DOI, versión congelada ni snapshot",
    !/\bDOI\b|versión congelada|snapshot/i.test(textoSitio),
    (textoSitio.match(/\bDOI\b|versión congelada|snapshot/gi) || []).join(", "));
  check("autoría: no hay cita armada (APA/BibTeX) ni nada pendiente",
    !/\[Conjunto de datos\]|@misc\{|\bpendiente\b|en preparación/i.test(textoSitio),
    (textoSitio.match(/\[Conjunto de datos\]|@misc\{|\bpendiente\b|en preparación/gi) || []).join(", "));
  check("autoría: no hay una fecha de corte global",
    !/datos al \d{4}-\d{2}/i.test(textoSitio) && !/fecha de corte:/i.test(textoSitio));
  check("manuales: el bloque de la Guía sobrevive a que Descargas se redibuje",
    Boolean(creditosGuia.querySelector(".dl-usos")) && /Para leer/.test(creditosGuia.textContent));
  check("descargas: remite a la Guía en vez de repetir la lista de archivos",
    /Guía/.test(creditosPuntero.textContent) && creditosPuntero.querySelector("[data-ir-guia]"));
  const archivosRepo = [...document.querySelectorAll("#creditos-guia .dl-creditos-archivos a")]
    .map((a) => a.getAttribute("href"));
  check("reproducibilidad: hay enlaces a los archivos planos", archivosRepo.length > 0,
    archivosRepo.length + " enlaces");
  const leadReproducibilidad = (document.querySelector("#guia-manuales .info-uso-lead")?.textContent || "").replace(/\s+/g, " ");
  check("reproducibilidad: la Guía anuncia fuentes, cobertura y hashes, no una certificación general",
    /Ocho archivos.*procedencia.*cobertura y hashes/i.test(leadReproducibilidad)
      && /no certifican la calidad semántica/i.test(leadReproducibilidad)
      && !/comprobaciones/.test(leadReproducibilidad));
  const enlaceResumenValidacion = document.querySelector('#creditos-guia a[href="reproducibilidad/validacion_resumen.csv"]');
  check("reproducibilidad: el resumen de validación se describe como metadatos, no como pruebas superadas",
    Boolean(enlaceResumenValidacion)
      && /Resumen de fuentes y cobertura/.test(enlaceResumenValidacion.textContent)
      && /no es un informe de pruebas ni un sello de calidad/.test(enlaceResumenValidacion.textContent));
  const readmeReproducibilidad = fs.readFileSync(path.join(DOCS, "reproducibilidad/README.md"), "utf8");
  check("reproducibilidad: alcance separa metadatos, mediciones y snapshot local no publicado",
    /no contiene resultados de pruebas, tolerancias ni una certificación de calidad/i.test(readmeReproducibilidad)
      && /Ejecutarlo no publica el snapshot, no crea un DOI y no\s+garantiza recuperar archivos históricos/i.test(readmeReproducibilidad));
  const inventarioReproducibilidad = fs.readFileSync(path.join(DOCS, "reproducibilidad/inventario_fuentes.csv"), "utf8");
  check("reproducibilidad: el índice de búsqueda tiene su control propio y no causa un ciclo en el inventario",
    !/^outputs\/indice_busqueda\.json,/m.test(inventarioReproducibilidad));
  check("reproducibilidad: todos los archivos enlazados existen en el disco",
    archivosRepo.length > 0 && archivosRepo.every((href) => fs.existsSync(path.join(DOCS, href))),
    archivosRepo.filter((href) => !fs.existsSync(path.join(DOCS, href))).join(", "));
  // El bloque de reproducibilidad separa dos audiencias: lo que se abre en una
  // planilla y lo que consume código. Mezclados en una lista, el visitante no
  // sabía cuál de los seis enlaces le servía.
  const gruposUso = [...document.querySelectorAll("#creditos-guia .dl-uso")];
  check("reproducibilidad: separa «para leer» de «para programas y agentes»",
    gruposUso.length === 2
    && /Para leer/.test(gruposUso[0].querySelector("h4").textContent)
    && /Para programas y agentes/.test(gruposUso[1].querySelector("h4").textContent),
    gruposUso.map((g) => g.querySelector("h4").textContent).join(" | "));
  check("reproducibilidad: cada archivo declara su formato a la vista",
    [...document.querySelectorAll("#creditos-guia .dl-uso-item")].length >= 6
    && [...document.querySelectorAll("#creditos-guia .dl-uso-item")]
      .every((a) => ["CSV", "JSON", "TXT", "MD"].includes((a.querySelector(".dl-chip").textContent || "").trim())),
    [...document.querySelectorAll("#creditos-guia .dl-chip")].map((c) => c.textContent).join(" "));
  const enlacesMaquina = gruposUso.length === 2
    ? [...gruposUso[1].querySelectorAll("a")].map((a) => a.getAttribute("href")) : [];
  check("reproducibilidad: el grupo de máquinas incluye el contrato y la guía para agentes",
    enlacesMaquina.includes("api/v2/catalog.json") && enlacesMaquina.includes("llms.txt"),
    enlacesMaquina.join(", "));
  const irAgentes = document.querySelector("#creditos-guia [data-ir-uso]");
  if (irAgentes) irAgentes.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("guía: el enlace a las instrucciones de agentes abre esa sub-pestaña",
    Boolean(irAgentes)
    && document.getElementById("guia-container").style.display !== "none"
    && document.getElementById("uso-panel-agentes").hidden === false
    && document.getElementById("uso-panel-humanos").hidden === true);

  // Las rutas hash de la Guía deben funcionar incluso después de cargar, pero
  // un ancla de Información o un enlace SQL no debe cambiar de pestaña.
  window.location.hash = "#como-usar-humanos";
  await new Promise((resolve) => setTimeout(resolve, 0));
  check("URL: #como-usar-humanos abre Guía y su panel de personas",
    document.getElementById("guia-container").style.display !== "none"
    && document.getElementById("uso-panel-humanos").hidden === false);
  window.location.hash = "#como-usar-agentes";
  await new Promise((resolve) => setTimeout(resolve, 0));
  check("URL: #como-usar-agentes abre la sub-pestaña de agentes",
    document.getElementById("guia-container").style.display !== "none"
    && document.getElementById("uso-panel-agentes").hidden === false);
  window.location.hash = "#guia-como-sumar";
  await new Promise((resolve) => setTimeout(resolve, 0));
  check("URL: #guia-como-sumar abre la Guía y selecciona el panel de sumas",
    document.getElementById("guia-container").style.display !== "none"
    && document.getElementById("guia-como-sumar").hidden === false);
  window.switchMainTab("info");
  window.location.hash = "#catalogo-principal";
  await new Promise((resolve) => setTimeout(resolve, 0));
  check("URL: un ancla de la portada no salta a la Guía",
    document.getElementById("info-container").style.display !== "none"
    && document.getElementById("guia-container").style.display === "none");
  window.location.hash = "#sql=SELECT%201";
  await new Promise((resolve) => setTimeout(resolve, 0));
  check("URL: un hash de consulta SQL no es interceptado por la Guía",
    document.getElementById("info-container").style.display !== "none"
    && document.getElementById("guia-container").style.display === "none");
  window.history.replaceState(null, "", window.location.pathname);

  // El puntero de Descargas tiene que llevar a la Guía, no dejar al visitante
  // en la misma pestaña: es el enlace que faltaba entre las dos secciones.
  document.querySelector("#creditos-puntero [data-ir-guia]")
    .dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("descargas: «Abrir la guía» cambia a la pestaña Guía",
    document.getElementById("guia-container").style.display !== "none"
    && document.getElementById("downloads-container").style.display === "none");
  check("la Guía ya no vive dentro de Información",
    !document.getElementById("info-container").querySelector("#guia-como-usar")
    && !document.getElementById("downloads-container").querySelector("#guia-como-usar"));
  const lecturaGuia = document.querySelector(".guia-lectura-details");
  check("la Guía conserva la lectura de frecuencia, unidades, presencia y trazabilidad en un detalle plegado",
    Boolean(lecturaGuia) && lecturaGuia.open === false
    && /frecuencia/i.test(lecturaGuia.textContent)
    && /unidades/i.test(lecturaGuia.textContent)
    && /reportando/i.test(lecturaGuia.textContent)
    && /manifiesto/i.test(lecturaGuia.textContent));
  window.switchMainTab("info");

  check("la web advierte que la base puede tener errores y pide verificar",
    /Puede haber errores/.test(document.querySelector(".info-fuentes").textContent) &&
    /puede contener errores/.test(document.querySelector(".info-note").textContent) &&
    /revísalos antes de usarlos/.test(document.getElementById("downloads-container").textContent));
  check("fuentes y limitaciones: la sección declara respaldo y cobertura",
    /sin respaldo|respaldo oficial/i.test(document.body.textContent) &&
    /fuentes oficiales/i.test(document.querySelector(".info-fuentes").textContent) &&
    /homogeneización generalizada/i.test(document.querySelector(".info-fuentes").textContent));

  window.switchMainTab("info");
  document.querySelector('.info-core-card[data-sector="ffmm"] [data-portada="explorar"]')
    .dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("portada: «Ver tablas» abre el sector en el explorador y en el mapa",
    document.querySelector('[data-node-id="sector_ffmm"]').classList.contains("open") &&
    document.getElementById("erd-canvas").style.display === "block" && window.erdInstance.filter === "ffmm");
  const sectoresPortada = ["seguros", "ffmm", "fi", "bancos", "agf", "corredoras_bolsa", "macro"];
  const accionesPortada = Array.from(document.querySelectorAll('[data-portada="explorar"][data-sector]'));
  let todosLosSectoresAbren = accionesPortada.length === sectoresPortada.length;
  for (const sector of sectoresPortada) {
    const boton = accionesPortada.find((el) => el.dataset.sector === sector);
    if (!boton) { todosLosSectoresAbren = false; continue; }
    window.switchMainTab("info");
    boton.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    todosLosSectoresAbren = todosLosSectoresAbren
      && window.erdInstance.filter === sector
      && document.getElementById("erd-canvas").style.display === "block";
  }
  check("portada: los siete enlaces sectoriales abren el sector correcto en el mapa",
    todosLosSectoresAbren, sectoresPortada.join(", "));
  window.switchMainTab("info");
  document.querySelector('.info-hero-btn-secondary[data-portada="descargas"]')
    .dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("portada: la acción principal abre Descargas sin filtrar el catálogo",
    document.getElementById("downloads-container").style.display === "flex" &&
    document.getElementById("dl-sector").value === "todos" && visiblesDl().length > 0);
  window.DownloadsPanel.filtrarSector("todos");
  window.switchMainTab("info");
  document.querySelector('[data-portada="archivo"]').dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("portada: el enlace discreto abre el archivo del explorador",
    document.querySelector("#sidebar-tree .tree-archive").classList.contains("open"));
  document.querySelector('[data-portada="alcance"]').dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("portada: el enlace de metodología abre los detalles plegados",
    document.querySelector(".info-disclosure").open === true);

  // El resumen de duplicados ya no ocupa la portada: la explicación completa,
  // la medición reproducible y el código permanecen en la Guía.
  window.switchMainTab("info");
  const infoPortada = document.getElementById("info-container");
  check("portada: la advertencia detallada de filas repetidas no desplaza la navegación",
    !infoPortada.querySelector(".info-calidad") && !/LO QUE LA FUENTE REPITE/.test(infoPortada.textContent));
  const sumar = document.getElementById("guia-como-sumar");
  check("calidad: la Guía conserva las cifras medidas y el ejemplo",
    Boolean(sumar.querySelector('[data-calidad="repetidas"]'))
    && /230\.288/.test(sumar.textContent)
    && /22 de 90/.test(sumar.textContent)
    && /ffmm_cartera_nacional/.test(sumar.textContent));
  check("calidad: la Guía mantiene la consulta y la nota de criterio reproducible",
    Boolean(sumar.querySelector("[data-calidad-sql]"))
    && /claves_duplicados/.test(sumar.querySelector('a[href*="claves_duplicados"]').getAttribute("href")));
  const valoresAgregadosCalidad = [...document.querySelectorAll("[data-calidad]")];
  const consultasCalidad = [...document.querySelectorAll("[data-calidad-sql]")];
  check("las cifras agregadas y la consulta de calidad siguen en la Guía, no como sustituto en otra pestaña",
    valoresAgregadosCalidad.length > 0 && valoresAgregadosCalidad.every((el) => sumar.contains(el))
      && consultasCalidad.length === 1 && sumar.contains(consultasCalidad[0])
      && !infoPortada.querySelector(".info-calidad"));
  // ── Puertas nuevas: cifras medidas y enlaces ancla con ruta ──────────────
  const info = document.getElementById("info-container");
  const marcadas = info.querySelectorAll("[data-alcance], [data-calidad], [data-modo], [data-fuentes]");
  check("cada cifra del panel trae su origen medido (sin cifras escritas a mano)",
    marcadas.length > 0 && [...marcadas].every((el) => el.textContent.trim()));
  const anclas = [...document.querySelectorAll('a[href^="#"]')];
  const ids = new Set([...document.querySelectorAll("[id]")].map((el) => el.id));
  const rutas = new Set(["sql", "guia", "como-usar-humanos", "como-usar-agentes", "como-usar-sumar"]);
  const huorfanos = anclas.filter((a) => {
    const destino = a.href.split("#")[1];
    return !ids.has(destino) && !rutas.has(destino);
  });
  check("cada enlace ancla apunta a un id existente o a una ruta registrada",
    huorfanos.length === 0, huorfanos.map((a) => a.getAttribute("href")).join(", ") || "sin huérfanos");

  const fallos = results.filter((r) => !r.ok);
  for (const r of results) console.log(`${r.ok ? "OK  " : "FALLA"}  ${r.name}${r.extra ? "  -> " + r.extra : ""}`);
  if (errors.length) {
    console.log("\nErrores inesperados:");
    errors.slice(0, 8).forEach((e) => console.log("  " + e));
  }
  console.log(`\n${results.length - fallos.length}/${results.length} comprobaciones OK`);
  process.exit(fallos.length === 0 && errors.length === 0 ? 0 : 1);
}, 1200);

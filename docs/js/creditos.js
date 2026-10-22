/**
 * Autoría y reproducibilidad
 * Sistema de Información Financiera de Chile
 *
 * Pinta dos bloques:
 *
 *   #creditos-autor      → Información: quién construye esto, desde cuándo y
 *                          dónde está el código.
 *   #creditos-descargas  → Descargas: reproducibilidad y código, sobre el
 *                          catálogo.
 *
 * Regla de este módulo: en el sitio se escribe sólo lo que existe hoy. No hay
 * DOI, ni una versión congelada, ni una fecha de corte única. La cobertura no
 * es homogénea —seguros, fondos mutuos, fondos de inversión, banca y contexto
 * publican con frecuencias y rezagos distintos—, así que una fecha global
 * resumiría mal a la mayoría de las tablas. El periodo de cada conjunto se ve
 * donde corresponde: en el explorador, en el diccionario y en Descargas.
 */
(function (global) {
  "use strict";

  const CREDITOS = {
    autor: "Joaquín Mondaca",
    inicio: "septiembre de 2026",   // el repositorio se creó el 2026-09-25
    github: "https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile",
    linkedin: "https://www.linkedin.com/in/joaqu%C3%ADnmondaca/",

    // Archivos generados por scripts/construir_reproducibilidad.py.
    // Van en dos grupos porque no se consumen igual: los CSV se abren en una
    // planilla y el JSON y los hashes los lee un script. Mezclarlos en una sola
    // lista de enlaces dejaba al visitante sin saber cuál le servía.
    reproducibilidad: {
      leer: [
        {
          archivo: "reproducibilidad/diccionario.csv",
          nombre: "Diccionario de datos",
          detalle: "Qué significa cada columna, en qué unidad y con qué criterio contable.",
          formato: "CSV"
        },
        {
          archivo: "reproducibilidad/cobertura_por_periodo.csv",
          nombre: "Cobertura por periodo y tabla",
          detalle: "Hasta qué mes llega cada conjunto, sin suponerlo por el resto.",
          formato: "CSV"
        },
        {
          archivo: "reproducibilidad/validacion_resumen.csv",
          nombre: "Resultados de validación",
          detalle: "Qué comprobaciones pasó cada conjunto y con qué tolerancia.",
          formato: "CSV"
        },
        {
          archivo: "reproducibilidad/README.md",
          nombre: "Qué es cada archivo",
          detalle: "El método: de dónde sale cada cifra y cómo se regenera.",
          formato: "MD"
        }
      ],
      maquinas: [
        {
          archivo: "reproducibilidad/diccionario.json",
          nombre: "Diccionario de datos",
          detalle: "El mismo diccionario, con tipos, para leerlo desde código.",
          formato: "JSON"
        },
        {
          archivo: "reproducibilidad/inventario_fuentes.csv",
          nombre: "Inventario con SHA-256",
          detalle: "Cada archivo publicado con su hash, para verificar una descarga.",
          formato: "CSV"
        },
        {
          archivo: "api/v1/catalog.json",
          nombre: "Contrato de la API",
          detalle: "Los objetos publicados con filas, corte, clave y ruta a su esquema.",
          formato: "JSON"
        },
        {
          archivo: "llms.txt",
          nombre: "Guía para agentes",
          detalle: "Qué hay, cómo se consulta y qué no suponer, en una página.",
          formato: "TXT"
        }
      ]
    }
  };

  function escapar(texto) {
    return String(texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function enlace(href, texto) {
    return `<a href="${escapar(href)}" target="_blank" rel="noopener noreferrer">${escapar(texto)}</a>`;
  }

  function itemUso(r) {
    return `<li>
        <a class="dl-uso-item" href="${escapar(r.archivo)}" download>
          <span class="dl-uso-texto">
            <span class="dl-uso-nombre">${escapar(r.nombre)}</span>
            <span class="dl-uso-detalle">${escapar(r.detalle)}</span>
          </span>
          <span class="dl-chip">${escapar(r.formato)}</span>
        </a>
      </li>`;
  }

  function grupoUso(id, titulo, nota, items) {
    return `
      <section class="dl-uso" aria-labelledby="${id}">
        <h4 id="${id}">${escapar(titulo)}</h4>
        <p class="dl-uso-nota">${escapar(nota)}</p>
        <ul class="dl-creditos-archivos dl-uso-list">${items.map(itemUso).join("")}</ul>
      </section>`;
  }

  /* ── Autoría: pestaña Información ──────────────────────────────────────── */

  function htmlAutor() {
    return `
      <div class="info-section-kicker">AUTORÍA</div>
      <h2>Quién construye esto</h2>
      <div class="creditos-autor">
        <p><strong>${escapar(CREDITOS.autor)}</strong> · proyecto iniciado en ${escapar(CREDITOS.inicio)}</p>
        <p class="creditos-autor-rol">Proyecto de datos de punta a punta: extracción desde las fuentes oficiales,
        validación estadística y contable, publicación incremental, automatización y producto web.</p>
        <p class="creditos-autor-enlaces">
          ${enlace(CREDITOS.github, "GitHub")} · ${enlace(CREDITOS.linkedin, "LinkedIn")}
        </p>
      </div>
    `;
  }

  /* ── Reproducibilidad y código: pestaña Descargas ──────────────────────── */

  function htmlDescargas() {
    const R = CREDITOS.reproducibilidad;
    return `
      <div class="dl-creditos-head">
        <div>
          <h3>Reproducibilidad y código</h3>
          <p>Lo publicado se puede auditar. Los archivos vienen en dos grupos porque no se
          consumen igual: unos se abren en una planilla, otros los lee un programa.</p>
        </div>
      </div>
      <div class="dl-usos">
        ${grupoUso("dl-uso-leer", "Para leer",
          "Se abren en Excel, Numbers o cualquier hoja de cálculo.", R.leer)}
        ${grupoUso("dl-uso-maquinas", "Para programas y agentes de IA",
          "JSON, hashes y el contrato: pensados para consumirse con código.", R.maquinas)}
      </div>
      <p class="dl-uso-pie">
        Se regeneran con <code>scripts/construir_reproducibilidad.py</code>; el método completo
        está en <a href="reproducibilidad/README.md">reproducibilidad/README.md</a> y el código en
        ${enlace(CREDITOS.github, "GitHub")}.
        ¿Un agente que no ejecuta código? También hay
        <button type="button" class="dl-uso-enlace" data-ir-uso="agentes">SDK y servidor MCP</button>.
      </p>
    `;
  }

  /* El bloque de Descargas remite a las instrucciones para agentes, que viven
   * en otra pestaña y en otra sub-pestaña. Se navega por código en vez de con un
   * ancla: un `href="#…"` no cambia de pestaña y el visitante aterrizaría en el
   * mismo sitio sin entender por qué. */
  function llevarAUso(agentes) {
    if (window.switchMainTab) window.switchMainTab("info");
    const seccion = document.getElementById("info-como-usar");
    if (seccion) {
      if (window.SIFComoUsar && typeof window.SIFComoUsar.activar === "function") {
        window.SIFComoUsar.activar(agentes ? 1 : 0, false);
      }
      // `scrollIntoView` no existe en todos los entornos (jsdom, por ejemplo).
      if (typeof seccion.scrollIntoView === "function") {
        seccion.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }

  function pintar() {
    const autor = document.getElementById("creditos-autor");
    const descargas = document.getElementById("creditos-descargas");
    if (autor) autor.innerHTML = htmlAutor();
    if (descargas) {
      descargas.innerHTML = htmlDescargas();
      const boton = descargas.querySelector("[data-ir-uso]");
      if (boton) {
        boton.addEventListener("click", () => llevarAUso(boton.dataset.irUso === "agentes"));
      }
    }
  }

  global.SIFCreditos = { datos: CREDITOS, pintar };
})(window);

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

    // Archivos generados por scripts/construir_reproducibilidad.py
    reproducibilidad: [
      { archivo: "reproducibilidad/diccionario.csv", texto: "Diccionario de datos (CSV)" },
      { archivo: "reproducibilidad/diccionario.json", texto: "Diccionario de datos (JSON)" },
      { archivo: "reproducibilidad/inventario_fuentes.csv", texto: "Inventario de archivos con SHA-256" },
      { archivo: "reproducibilidad/cobertura_por_periodo.csv", texto: "Cobertura por periodo y tabla" },
      { archivo: "reproducibilidad/validacion_resumen.csv", texto: "Resultados de validación" },
      { archivo: "reproducibilidad/README.md", texto: "Qué es cada archivo y cómo se genera" }
    ]
  };

  function escapar(texto) {
    return String(texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function enlace(href, texto) {
    return `<a href="${escapar(href)}" target="_blank" rel="noopener">${escapar(texto)}</a>`;
  }

  function enlacesReproducibilidad() {
    return CREDITOS.reproducibilidad
      .map((r) => `<li><a class="creditos-link" href="${escapar(r.archivo)}" download>${escapar(r.texto)}</a></li>`)
      .join("");
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
    return `
      <div class="dl-creditos-head">
        <div>
          <h3>Reproducibilidad y código</h3>
          <p>Lo publicado se puede auditar: diccionario de datos, inventario con SHA-256, cobertura por
          periodo y resultados de validación. El periodo de cada conjunto está en su ficha de descarga.</p>
        </div>
      </div>
      <div class="dl-creditos-enlaces">
        ${enlace(CREDITOS.github, "Código y metodología")}
      </div>
      <ul class="dl-creditos-archivos">${enlacesReproducibilidad()}</ul>
    `;
  }

  function pintar() {
    const autor = document.getElementById("creditos-autor");
    const descargas = document.getElementById("creditos-descargas");
    if (autor) autor.innerHTML = htmlAutor();
    if (descargas) descargas.innerHTML = htmlDescargas();
  }

  global.SIFCreditos = { datos: CREDITOS, pintar };
})(window);

/**
 * Citación, versión académica, autoría y reproducibilidad
 * Sistema de Información Financiera de Chile
 *
 * Un solo objeto (CITA) define versión, fecha de corte, DOI, autoría, licencias
 * y enlaces, y se pinta en dos bloques:
 *
 *   #cita-info        → Información: cómo citar, versión congelada, snapshot,
 *                       código, autoría y contacto (bloque largo).
 *   #cita-descargas   → Descargas: misma información en formato compacto,
 *                       junto a los archivos de reproducibilidad.
 *
 * Regla de este módulo: si un dato todavía no existe (DOI, ORCID, filiación),
 * el bloque lo declara pendiente. Nunca inventa un identificador: un DOI falso
 * es peor que un DOI pendiente.
 *
 * El sitio es la plataforma viva de exploración y cambia con cada publicación.
 * Lo que se cita es la versión congelada (SIF-Chile Core Holdings vX.Y), con su
 * fecha de corte y su DOI: mismos datos, mismos archivos, mismos hashes.
 */
(function (global) {
  "use strict";

  const CITA = {
    // Versión congelada y citable.
    nombre: "SIF-Chile Core Holdings",
    version: "1.0",
    corte: "2026-08",          // último periodo publicado incluido en el snapshot
    publicada: "2026-10-20",
    doi: "",                   // ← completar cuando Zenodo asigne el DOI
    zenodo: "",                // ← URL del registro en Zenodo
    estado: "En preparación: el snapshot descargable de la versión congelada y su DOI están pendientes.",

    // Autoría y contacto (se completa con los datos públicos del autor).
    autor: "Joaquín Mondaca",
    afiliacion: "",            // ← universidad o programa, si se quiere declarar
    orcid: "",                 // ← 0000-0000-0000-0000
    contacto: "",              // ← correo público de contacto
    github: "https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile",
    linkedin: "https://www.linkedin.com/in/joaqu%C3%ADnmondaca/",

    // Alcance de la versión congelada: el núcleo, tal como se publica.
    alcance: "Seguros, fondos mutuos y fondos de inversión: 25 conjuntos, 11,1 millones de registros, 2001–2026.",

    // Licencias. El código es MIT; los datos son de sus fuentes oficiales.
    licencia_codigo: "MIT (ver LICENSE en el repositorio)",
    licencia_datos: "Datos de fuentes oficiales (CMF, Banco Central de Chile, SPensiones, SUSESO), publicados sin modificar su contenido.",

    // Reproducibilidad: archivos generados por scripts/construir_reproducibilidad.py
    reproducibilidad: [
      { archivo: "reproducibilidad/diccionario.csv", texto: "Diccionario de datos (CSV)" },
      { archivo: "reproducibilidad/diccionario.json", texto: "Diccionario de datos (JSON)" },
      { archivo: "reproducibilidad/inventario_fuentes.csv", texto: "Inventario de archivos con SHA-256" },
      { archivo: "reproducibilidad/cobertura_por_periodo.csv", texto: "Cobertura por periodo y tabla" },
      { archivo: "reproducibilidad/validacion_resumen.csv", texto: "Resultados de validación" },
      { archivo: "reproducibilidad/README.md", texto: "Qué es cada archivo y cómo se genera" }
    ]
  };

  function escapar(valor) {
    return String(valor == null ? "" : valor)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // Un dato vacío se declara pendiente en vez de omitirse en silencio.
  function dato(valor, etiquetaPendiente) {
    const texto = String(valor == null ? "" : valor).trim();
    return texto || `<span class="cita-pendiente">${escapar(etiquetaPendiente || "pendiente")}</span>`;
  }

  function enlace(href, texto) {
    if (!href) return "";
    return `<a href="${escapar(href)}" target="_blank" rel="noopener">${escapar(texto)}</a>`;
  }

  function tituloDataset() {
    return `${CITA.nombre} v${CITA.version}: carteras y estados financieros de seguros, `
         + `fondos mutuos y fondos de inversión de Chile (2001–${CITA.corte.slice(0, 4)})`;
  }

  /**
   * Cita en formato APA 7 para conjuntos de datos. Sin DOI se cae al repositorio
   * y se declara el DOI pendiente, en vez de omitir el campo.
   */
  function apa() {
    const año = (CITA.publicada || "").slice(0, 4) || new Date().getFullYear();
    const base = `Mondaca, J. (${año}). ${tituloDataset()} [Conjunto de datos].`;
    if (CITA.doi) {
      const url = CITA.doi.startsWith("http") ? CITA.doi : `https://doi.org/${CITA.doi}`;
      return `${base} Zenodo. ${url}`;
    }
    return `${base} Sistema de Información Financiera de Chile. ${CITA.github} `
         + `(versión congelada v${CITA.version}; DOI pendiente).`;
  }

  function bibtex() {
    const año = (CITA.publicada || "").slice(0, 4) || new Date().getFullYear();
    const lineas = [
      "@misc{sif_chile_core_holdings_v" + CITA.version.replace(/\./g, "_") + ",",
      "  author       = {Mondaca, Joaquín},",
      `  title        = {${CITA.nombre} v${CITA.version}: carteras y estados financieros de seguros, fondos mutuos y fondos de inversión de Chile},`,
      `  year         = {${año}},`,
      "  publisher    = {Zenodo},",
      `  note         = {Corte de datos: ${CITA.corte}. ${CITA.estado}}`,
    ];
    if (CITA.doi) lineas.push(`  doi          = {${CITA.doi}},`);
    if (CITA.zenodo) lineas.push(`  url          = {${CITA.zenodo}}`);
    else lineas.push(`  url          = {${CITA.github}}`);
    lineas[lineas.length - 1] = lineas[lineas.length - 1].replace(/,$/, "");
    lineas.push("}");
    return lineas.join("\n");
  }

  function fila(etiqueta, valor) {
    return `<div class="cita-fila"><dt>${escapar(etiqueta)}</dt><dd>${valor}</dd></div>`;
  }

  function botonCopiar(objetivo, texto) {
    return `<button type="button" class="cita-copiar" data-cita-copiar="${escapar(objetivo)}">${escapar(texto)}</button>`;
  }

  function enlacesReproducibilidad(clase) {
    return CITA.reproducibilidad
      .map((r) => `<li><a class="${clase}" href="${escapar(r.archivo)}" download>${escapar(r.texto)}</a></li>`)
      .join("");
  }

  /* ── Bloque largo: pestaña Información ─────────────────────────────────── */

  function htmlInformacion() {
    const doiFila = CITA.doi
      ? fila("DOI", enlace(CITA.doi.startsWith("http") ? CITA.doi : `https://doi.org/${CITA.doi}`, CITA.doi))
      : fila("DOI", dato("", "pendiente"));
    const snapshot = CITA.zenodo
      ? enlace(CITA.zenodo, `Descargar snapshot v${CITA.version}`)
      : `<span class="cita-pendiente">Snapshot en preparación: se publicará con DOI y registro de cambios.</span>`;

    return `
      <div class="info-section-kicker">CITACIÓN Y VERSIÓN ACADÉMICA</div>
      <h2>Cómo citar esta base</h2>
      <p class="cita-lead">El sitio es la plataforma viva de exploración y cambia con cada publicación.
      Para investigar se cita la <strong>versión congelada ${escapar(CITA.nombre)} v${escapar(CITA.version)}</strong>,
      depositada con DOI: misma data, mismos archivos, mismos hashes, para siempre.</p>

      <div class="cita-caja">
        <div class="cita-caja-head">
          <span>Cita recomendada (APA 7)</span>
          ${botonCopiar("cita-apa", "Copiar")}
        </div>
        <pre class="cita-pre" id="cita-apa">${escapar(apa())}</pre>
        <details class="cita-detalle">
          <summary>BibTeX</summary>
          <div class="cita-caja-head">
            <span>Entrada para gestores de referencias</span>
            ${botonCopiar("cita-bibtex", "Copiar")}
          </div>
          <pre class="cita-pre" id="cita-bibtex">${escapar(bibtex())}</pre>
        </details>
      </div>

      <dl class="cita-fichas">
        ${fila("Versión", escapar(CITA.nombre) + " v" + escapar(CITA.version))}
        ${fila("Fecha de corte", escapar(CITA.corte))}
        ${fila("Publicada", escapar(CITA.publicada))}
        ${doiFila}
        ${fila("Alcance", escapar(CITA.alcance))}
        ${fila("Licencia del código", escapar(CITA.licencia_codigo))}
        ${fila("Licencia de los datos", escapar(CITA.licencia_datos))}
      </dl>

      <div class="cita-enlaces">
        <div class="cita-enlace"><span>Versión citable</span>${snapshot}</div>
        <div class="cita-enlace"><span>Código y metodología</span>${enlace(CITA.github, "Repositorio público en GitHub")}</div>
        <div class="cita-enlace"><span>Reproducibilidad</span>
          <ul class="cita-lista">${enlacesReproducibilidad("cita-link")}</ul>
        </div>
      </div>

      <p class="cita-nota">${escapar(CITA.estado)} La versión congelada es la que se cita; la página viva se referencia como la herramienta de exploración.</p>
    `;
  }

  /* ── Bloque de autoría ─────────────────────────────────────────────────── */

  function htmlAutor() {
    const piezas = [];
    if (CITA.github) piezas.push(enlace(CITA.github, "GitHub"));
    if (CITA.linkedin) piezas.push(enlace(CITA.linkedin, "LinkedIn"));
    if (CITA.orcid) {
      piezas.push(enlace(CITA.orcid.startsWith("http") ? CITA.orcid : `https://orcid.org/${CITA.orcid}`, `ORCID ${CITA.orcid}`));
    } else {
      piezas.push(`<span class="cita-pendiente">ORCID pendiente</span>`);
    }
    if (CITA.contacto) piezas.push(enlace(`mailto:${CITA.contacto}`, CITA.contacto));
    return `
      <div class="info-section-kicker">AUTORÍA</div>
      <h2>Quién construye esto</h2>
      <div class="cita-autor">
        <p><strong>${escapar(CITA.autor)}</strong>${CITA.afiliacion ? " · " + escapar(CITA.afiliacion) : ""}</p>
        <p class="cita-autor-rol">Proyecto de datos de punta a punta: extracción desde las fuentes oficiales, validación
        estadística y contable, publicación incremental, automatización y producto web.</p>
        <p class="cita-autor-enlaces">${piezas.join(" · ")}</p>
        ${CITA.contacto ? "" : "<p class=\"cita-nota\">Correo de contacto pendiente: se recomienda publicar uno para que quien use la base pueda informar errores.</p>"}
      </div>
    `;
  }

  /* ── Bloque compacto: pestaña Descargas ────────────────────────────────── */

  function htmlDescargas() {
    const snapshot = CITA.zenodo
      ? `<a class="dl-cita-btn" href="${escapar(CITA.zenodo)}" target="_blank" rel="noopener">Descargar snapshot académico (v${escapar(CITA.version)})</a>`
      : `<span class="cita-pendiente">Snapshot v${escapar(CITA.version)} en preparación (DOI pendiente)</span>`;
    return `
      <div class="dl-cita-head">
        <div>
          <h3>Citación y versión académica</h3>
          <p>Si vas a compartir una cifra, un gráfico o un archivo, cita la versión congelada
          <b>${escapar(CITA.nombre)} v${escapar(CITA.version)}</b> (corte ${escapar(CITA.corte)}), no la página viva.</p>
        </div>
        ${botonCopiar("cita-apa-dl", "Copiar cita")}
      </div>
      <pre class="cita-pre" id="cita-apa-dl">${escapar(apa())}</pre>
      <div class="dl-cita-enlaces">
        ${snapshot}
        ${enlace(CITA.github, "Código y metodología")}
        ${CITA.doi ? enlace(CITA.doi.startsWith("http") ? CITA.doi : `https://doi.org/${CITA.doi}`, `DOI ${CITA.doi}`) : `<span class="cita-pendiente">DOI pendiente</span>`}
      </div>
      <ul class="dl-cita-archivos">${enlacesReproducibilidad("cita-link")}</ul>
    `;
  }

  /* ── Pintado y copiado ─────────────────────────────────────────────────── */

  function bindCopiar(raiz) {
    (raiz || document).querySelectorAll("[data-cita-copiar]").forEach((boton) => {
      if (boton.dataset.listo === "1") return;
      boton.dataset.listo = "1";
      boton.addEventListener("click", () => {
        const objetivo = document.getElementById(boton.dataset.citaCopiar);
        if (!objetivo) return;
        const original = boton.textContent;
        const hecho = () => {
          boton.textContent = "Copiado";
          setTimeout(() => { boton.textContent = original; }, 1600);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(objetivo.textContent).then(hecho, () => {});
        }
      });
    });
  }

  function pintar() {
    const info = document.getElementById("cita-info");
    const autor = document.getElementById("cita-autor");
    const descargas = document.getElementById("cita-descargas");
    if (info) { info.innerHTML = htmlInformacion(); bindCopiar(info); }
    if (autor) { autor.innerHTML = htmlAutor(); bindCopiar(autor); }
    if (descargas) { descargas.innerHTML = htmlDescargas(); bindCopiar(descargas); }
  }

  global.SIFCita = { datos: CITA, apa, bibtex, pintar };
})(window);

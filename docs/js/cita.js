/**
 * Citación de la base, autoría y reproducibilidad
 * Sistema de Información Financiera de Chile
 *
 * Un solo objeto (CITA) define autoría, licencias y enlaces, y se pinta en dos
 * bloques:
 *
 *   #cita-info        → Información: cómo citar, alcance, código, licencias,
 *                       reproducibilidad y autoría (bloque largo).
 *   #cita-descargas   → Descargas: la cita en formato compacto, junto a los
 *                       archivos de reproducibilidad.
 *
 * Regla de este módulo: en el sitio se escribe sólo lo que existe hoy. No hay
 * DOI, no hay una versión congelada publicada y no hay ORCID ni correo
 * declarados, así que ninguna de esas cosas aparece: ni inventada ni anunciada
 * como pendiente. La cita se arma con lo que sí se puede verificar: autor,
 * título, fecha de corte de los datos, fecha de consulta y URL.
 *
 * El corte, el alcance y la fecha del catálogo se leen de window.DOWNLOAD_CATALOG
 * (generado por scripts/build_download_catalog.py) para que la cita nunca se
 * atrase respecto de lo publicado. Si el catálogo no está cargado, se cae a los
 * valores de CITA.
 */
(function (global) {
  "use strict";

  const CITA = {
    titulo: "Sistema de Información Financiera de Chile",
    autor: "Joaquín Mondaca",
    apellidoAutor: "Mondaca, J.",
    autorBibtex: "Mondaca, Joaquín",
    github: "https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile",
    linkedin: "https://www.linkedin.com/in/joaqu%C3%ADnmondaca/",

    // Respaldo: sólo se usa si no está cargado window.DOWNLOAD_CATALOG.
    corte: "2026-09",
    generado: "2026-10-16",
    alcance: "59 conjuntos · 13,4 millones de registros · 2001-01 → 2026-09",

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

  /* ── Datos que salen del catálogo publicado ────────────────────────────── */

  function catalogo() {
    return global.DOWNLOAD_CATALOG || null;
  }

  /** Alcance publicado: vive en la sección `alcance` del catálogo. */
  function alcanceCatalogo() {
    const c = catalogo();
    return (c && c.alcance && c.alcance.visible) || null;
  }

  /** Último periodo publicado: es la fecha de corte de los datos. */
  function corte() {
    const v = alcanceCatalogo();
    return (v && v.periodo && v.periodo.hasta) || CITA.corte;
  }

  /** Día en que se generó el catálogo de descargas. */
  function generado() {
    const c = catalogo();
    return (c && c.generado) || CITA.generado;
  }

  function alcance() {
    const v = alcanceCatalogo();
    if (v && v.periodo) {
      const millones = v.filas / 1e6;
      const filas = millones >= 1
        ? `${millones.toFixed(1).replace(".", ",")} millones`
        : v.filas.toLocaleString("es-CL");
      return `${v.conjuntos} conjuntos · ${filas} de registros · `
           + `${v.periodo.desde} → ${v.periodo.hasta}`;
    }
    return CITA.alcance;
  }

  function año() {
    return corte().slice(0, 4) || String(new Date().getFullYear());
  }

  function hoy() {
    const d = new Date();
    const dos = (n) => String(n).padStart(2, "0");
    return `${dos(d.getDate())}-${dos(d.getMonth() + 1)}-${d.getFullYear()}`;
  }

  /* ── Citas ─────────────────────────────────────────────────────────────── */

  /**
   * Cita en formato APA 7 para conjuntos de datos vivos: autor, año, título,
   * sitio y URL, con la fecha de corte de los datos y la fecha de consulta.
   */
  function apa() {
    return `${CITA.apellidoAutor} (${año()}). ${CITA.titulo} [Conjunto de datos]. GitHub. `
         + `${CITA.github} (datos al ${corte()}; consultado el ${hoy()}).`;
  }

  function bibtex() {
    const lineas = [
      "@misc{sistema_de_informacion_financiera_de_chile,",
      `  author       = {${CITA.autorBibtex}},`,
      `  title        = {${CITA.titulo}},`,
      `  year         = {${año()}},`,
      "  howpublished = {GitHub},",
      `  note         = {Conjunto de datos. Datos al ${corte()}. Consultado el ${hoy()}.},`,
      `  url          = {${CITA.github}}`
    ];
    lineas[lineas.length - 1] = lineas[lineas.length - 1].replace(/,$/, "");
    lineas.push("}");
    return lineas.join("\n");
  }

  /* ── Utilidades de pintado ─────────────────────────────────────────────── */

  function escapar(texto) {
    return String(texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function enlace(href, texto, extra) {
    return `<a href="${escapar(href)}" ${extra || ""}>${escapar(texto)}</a>`;
  }

  function fila(etiqueta, valor) {
    return `<div class="cita-fila"><dt>${escapar(etiqueta)}</dt><dd>${escapar(valor)}</dd></div>`;
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
    return `
      <div class="info-section-kicker">CÓMO CITAR ESTA BASE</div>
      <h2>Cómo citar esta base</h2>
      <p class="cita-lead">La base se actualiza cada vez que las fuentes publican. Si usas estos datos,
      cítalos con su <strong>fecha de corte</strong> y la fecha en que los consultaste: la cita de abajo
      ya incluye ambas.</p>

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
        ${fila("Datos al", corte() + " (último periodo publicado)")}
        ${fila("Catálogo de descargas del", generado())}
        ${fila("Alcance de la vista principal", alcance())}
        ${fila("Licencia del código", CITA.licencia_codigo)}
        ${fila("Licencia de los datos", CITA.licencia_datos)}
      </dl>

      <div class="cita-enlaces">
        <div class="cita-enlace"><span>Código y metodología</span>${enlace(CITA.github, "Repositorio público en GitHub", 'target="_blank" rel="noopener"')}</div>
        <div class="cita-enlace"><span>Reproducibilidad</span>
          <ul class="cita-lista">${enlacesReproducibilidad("cita-link")}</ul>
        </div>
      </div>

      <p class="cita-nota">No hay DOI: la base no está depositada en un repositorio con identificador
      permanente, así que se cita por su URL, con la fecha de corte de los datos y la fecha de consulta.</p>
    `;
  }

  /* ── Bloque de autoría ─────────────────────────────────────────────────── */

  function htmlAutor() {
    const piezas = [
      enlace(CITA.github, "GitHub", 'target="_blank" rel="noopener"'),
      enlace(CITA.linkedin, "LinkedIn", 'target="_blank" rel="noopener"')
    ];
    return `
      <div class="info-section-kicker">AUTORÍA</div>
      <h2>Quién construye esto</h2>
      <div class="cita-autor">
        <p><strong>${escapar(CITA.autor)}</strong></p>
        <p class="cita-autor-rol">Proyecto de datos de punta a punta: extracción desde las fuentes oficiales, validación
        estadística y contable, publicación incremental, automatización y producto web.</p>
        <p class="cita-autor-enlaces">${piezas.join(" · ")}</p>
      </div>
    `;
  }

  /* ── Bloque compacto: pestaña Descargas ────────────────────────────────── */

  function htmlDescargas() {
    return `
      <div class="dl-cita-head">
        <div>
          <h3>Cómo citar esta base</h3>
          <p>Cita la base con su fecha de corte (${escapar(corte())}): el sitio se actualiza
          y los periodos cambian.</p>
        </div>
        ${botonCopiar("cita-apa-dl", "Copiar cita")}
      </div>
      <pre class="cita-pre" id="cita-apa-dl">${escapar(apa())}</pre>
      <div class="dl-cita-enlaces">
        ${enlace(CITA.github, "Código y metodología")}
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

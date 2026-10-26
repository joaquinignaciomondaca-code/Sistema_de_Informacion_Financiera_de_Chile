/**
 * Autoría y reproducibilidad
 * Sistema de Información Financiera de Chile
 *
 * Pinta dos bloques:
 *
 *   #creditos-autor      → Información: sobre el autor, desde cuándo y
 *                          dónde está el código.
 *   #creditos-guia       → Guía: el método y los archivos auditables, en dos
 *                          grupos (planilla y código).
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
          nombre: "Resumen de fuentes y cobertura",
          detalle: "Fuente, modalidad, periodos y registros por objeto; no es un informe de pruebas ni un sello de calidad.",
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
          archivo: "api/v2/catalog.json",
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
      <h2>Sobre el autor</h2>
      <div class="creditos-autor">
        <p><strong>${escapar(CREDITOS.autor)}</strong> · proyecto iniciado en ${escapar(CREDITOS.inicio)}</p>
        <p class="creditos-autor-rol">Proyecto de datos de punta a punta: extracción desde las fuentes oficiales,
        validación estadística y contable, publicación incremental, automatización y producto web.</p>
        <p class="creditos-autor-enlaces">
          ${enlace(CREDITOS.github, "GitHub")} · ${enlace(CREDITOS.linkedin, "LinkedIn")} ·
          <a href="privacidad.html">Privacidad y datos personales</a>
        </p>
      </div>
    `;
  }

  /* Fuentes, cita y condiciones de uso. Las tres fuentes autorizan la
   * republicación con una sola condición: mencionarlas. La restricción de «uso
   * exclusivo para fines de investigación» que pesa sobre la Base de Cartera de
   * los Fondos de Pensiones no aparece aquí porque esa base no se publica. */
  const FUENTES = [
    {
      sigla: "CMF",
      nombre: "Comisión para el Mercado Financiero",
      cita: "Fuente: Comisión para el Mercado Financiero (CMF). Reproducción autorizada citando la fuente.",
      url: "https://www.cmfchile.cl/portal/principal/623/w4-article-1833.html"
    },
    {
      sigla: "BCCh",
      nombre: "Banco Central de Chile",
      cita: "Fuente: Banco Central de Chile (BDE). La información es propiedad del Banco Central de Chile.",
      url: "https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/terms_es.htm"
    },
    {
      sigla: "SPensiones",
      nombre: "Superintendencia de Pensiones",
      cita: "Fuente: Superintendencia de Pensiones. Reproducción autorizada citando la fuente.",
      url: "https://www.spensiones.cl/portal/institucional/594/w3-article-5885.html"
    }
  ];

  function htmlFuentes() {
    return `
      <section class="dl-fuentes" aria-labelledby="dl-fuentes-titulo">
        <h3 id="dl-fuentes-titulo">Fuentes y condiciones de uso</h3>
        <p class="dl-uso-nota">Cada conjunto declara su fuente y su cita en el catálogo de descargas.
        Las tres fuentes autorizan la reproducción citándolas; ninguna exige autorización escrita.</p>
        <ul class="dl-fuentes-lista">
          ${FUENTES.map((f) => `<li>
            <a href="${escapar(f.url)}" target="_blank" rel="noopener"><strong>${escapar(f.sigla)}</strong></a>
            · ${escapar(f.nombre)}
            <span class="dl-fuentes-cita">${escapar(f.cita)}</span>
          </li>`).join("")}
        </ul>
        <p class="dl-uso-pie">Los datos personales que contienen algunos registros se tratan conforme a la
        Ley 21.719: <a href="privacidad.html">aviso de privacidad y derechos</a>.</p>
      </section>
    `;
  }

  /* ── Reproducibilidad y código: pestaña Guía ──────────────────────────── */

  function htmlGuia() {
    const R = CREDITOS.reproducibilidad;
    return `
      <div class="dl-usos">
        ${grupoUso("dl-uso-leer", "Para leer",
          "CSV y Markdown: se abren en una hoja de cálculo o en un editor de texto.", R.leer)}
        ${grupoUso("dl-uso-maquinas", "Para programas y agentes de IA",
          "JSON, hashes y el contrato: se consumen desde código.", R.maquinas)}
      </div>
      <p class="dl-uso-pie">
        Se regeneran con <code>scripts/construir_reproducibilidad.py</code>. El método completo está en
        <a href="reproducibilidad/README.md">reproducibilidad/README.md</a> y el código en
        ${enlace(CREDITOS.github, "GitHub")}. Las instrucciones para agentes están en
        <button type="button" class="dl-uso-enlace" data-ir-uso="agentes">la sub-pestaña «Para agentes de IA»</button>.
      </p>
      ${htmlFuentes()}
    `;
  }

  /* La guía vive en su propia pestaña. Desde Descargas se llega con un puntero:
   * quien está eligiendo un archivo necesita saber dónde está el método, no
   * leerlo entero aquí. Un `href="#…"` no cambia de pestaña, así que la
   * navegación se hace por código. */
  function irA(pestana) {
    if (window.switchMainTab) window.switchMainTab(pestana);
  }

  function htmlPuntero() {
    return `
      <span class="dl-puntero-texto">El método, los diccionarios y el contrato de la API están en la
      pestaña <strong>Guía</strong>, con instrucciones para personas y para agentes.</span>
      <button type="button" class="dl-puntero-btn" data-ir-guia="1">Abrir la guía</button>
    `;
  }

  function pintar() {
    const autor = document.getElementById("creditos-autor");
    const guia = document.getElementById("creditos-guia");
    const puntero = document.getElementById("creditos-puntero");
    if (autor) autor.innerHTML = htmlAutor();
    if (guia) {
      guia.innerHTML = htmlGuia();
      const boton = guia.querySelector("[data-ir-uso]");
      if (boton) {
        boton.addEventListener("click", () => {
          const seccion = document.getElementById("guia-como-usar");
          irA("guia");
          if (window.SIFComoUsar) window.SIFComoUsar.activar(1, false);
          if (seccion && typeof seccion.scrollIntoView === "function") {
            seccion.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      }
    }
    if (puntero) {
      puntero.innerHTML = htmlPuntero();
      const boton = puntero.querySelector("[data-ir-guia]");
      if (boton) boton.addEventListener("click", () => irA("guia"));
    }
  }

  global.SIFCreditos = { datos: CREDITOS, pintar };
})(window);

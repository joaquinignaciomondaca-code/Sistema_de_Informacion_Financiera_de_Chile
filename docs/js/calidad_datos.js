/**
 * Calidad del dato publicado (bloque de la portada)
 * Sistema de Información Financiera de Chile
 *
 * En los archivos regulatorios chilenos la misma posición aparece más de una
 * vez: la fuente la repite y, al publicarla tal cual, sumar una columna sin
 * agrupar sobreestima. Eso no es un defecto del proyecto, es una propiedad de
 * los datos, y se mide en `docs/api/claves.csv` para los 90 objetos.
 *
 * Este módulo lleva esa medición a la portada con sus cifras reales, tomadas de
 * `js/estado_claves.js` (generado a su vez desde `claves.csv`, nunca escrito a
 * mano). Si ese archivo no está cargado, el bloque se queda con el texto del
 * HTML y no inventa nada.
 *
 * Regla de las cifras: los conteos salen exactos (230.288 filas, no «230 mil»)
 * porque aquí no se promete una magnitud: se denuncia un problema y el número
 * es la prueba.
 */
(function () {
  "use strict";

  const TOTAL_ETIQUETA = "filas idénticas publicadas";

  function datos() {
    return window.ESTADO_CLAVES || null;
  }

  function numero(n) {
    const A = window.SIFAlcance;
    return A && A.numero ? A.numero(n) : Number(n || 0).toLocaleString("es-CL");
  }

  // Objetos con filas repetidas, de mayor a menor.
  function ranking(estado) {
    const objetos = (estado && estado.objetos) || {};
    return Object.keys(objetos)
      .map((id) => ({ id, sobrantes: Number(objetos[id].sobrantes) || 0, datos: objetos[id] }))
      .filter((o) => o.sobrantes > 0)
      .sort((a, b) => b.sobrantes - a.sobrantes);
  }

  function peorEjemplo(estado) {
    const filas = ranking(estado);
    const conEjemplo = filas.find((f) => f.datos.ejemplo);
    return conEjemplo || filas[0] || null;
  }

  function pintarCifras(raiz, estado) {
    const resumen = (estado && estado.resumen) || {};
    const peor = peorEjemplo(estado);
    const valores = {
      repetidas: resumen.filas_repetidas ? numero(resumen.filas_repetidas) : null,
      objetos: resumen.con_repetidas && resumen.objetos
        ? `${resumen.con_repetidas} de ${resumen.objetos}` : null,
      peor: peor ? numero(peor.sobrantes) : null,
      "peor-objeto": peor ? peor.id : null,
      "peor-pct": peor && peor.datos.pct_repetidas
        ? Number(peor.datos.pct_repetidas).toFixed(1).replace(".", ",") + " %" : null,
      sobreestima: peor && peor.datos.ejemplo && peor.datos.ejemplo.pct
        ? Number(peor.datos.ejemplo.pct).toFixed(1).replace(".", ",") + " %" : null,
      "pct-repetidas": (function () {
        const rep = Number(resumen.filas_repetidas || 0);
        const tot = window.DOWNLOAD_CATALOG && window.DOWNLOAD_CATALOG.filas ? Number(window.DOWNLOAD_CATALOG.filas) : 0;
        if (!rep || !tot) return null;
        const pct = Math.floor(rep / tot * 1000) / 10;
        return pct.toFixed(1).replace(".", ",") + " %";
      })(),
      "ejemplo-periodo": peor && peor.datos.ejemplo ? peor.datos.ejemplo.periodo : null,
      "ejemplo-columna": peor && peor.datos.ejemplo ? peor.datos.ejemplo.columna : null,
    };
    raiz.querySelectorAll("[data-calidad]").forEach((el) => {
      const valor = valores[el.dataset.calidad];
      if (valor) el.textContent = valor;
    });
  }

  // Consulta citada: la misma que reproduce la medición, sin atajos. Se muestra
  // en pantalla y se puede lanzar en la terminal con un botón.
  function consulta(objeto, periodo) {
    const tabla = objeto || "ffmm_cartera_nacional";
    const mes = periodo || "2026-09";
    return [
      `-- ${tabla}, ${mes}: filas publicadas frente a filas distintas`,
      `WITH crudo AS (SELECT * FROM ${tabla} WHERE periodo = '${mes}'),`,
      "     mes   AS (SELECT DISTINCT * FROM crudo)",
      "SELECT (SELECT count(*) FROM crudo) AS filas,",
      "       (SELECT count(*) FROM mes)   AS distintas;"
    ].join("\n");
  }

  // El gráfico vive dentro de un plegable: cerrado no tiene ancho y el lienzo
  // saldría vacío. Por eso no se llama al cargar, sino la primera vez que se
  // abre el bloque (ver `init`).
  function grafico(estado) {
    const contenedor = document.getElementById("calidad-chart");
    if (!contenedor || !window.ChartRenderer) return;
    const top = ranking(estado).slice(0, 6);
    if (!top.length) return;
    // Sin canvas 2D (navegadores antiguos, pruebas con jsdom) el bloque se queda
    // con las cifras y la consulta: el gráfico es un adorno, no la prueba.
    try {
      // El lienzo se muestra antes de medirse: con `hidden` el contenedor mide
      // cero, el gráfico caería al ancho mínimo de 320 px y no llenaría la caja.
      contenedor.hidden = false;
      const renderer = new window.ChartRenderer(contenedor);
      renderer.setData(
        ["objeto", "sobrantes"],
        top.map((o) => ({ objeto: o.id, sobrantes: o.sobrantes }))
      );
    } catch (error) {
      if (window.console && console.warn) console.warn('calidad: sin gráfico', error);
      contenedor.hidden = true;
    }
  }

  var pintado = false;
  function pintarGrafico() {
    if (pintado) return;
    const estado = datos();
    if (!estado) return;
    pintado = true;
    grafico(estado);
  }

  function init() {
    document.querySelectorAll(".info-calidad, #guia-como-sumar").forEach(function (raiz) {
      if (raiz.dataset.calidadListo === "1") return;
      const estado = datos();
      if (!estado) return;

      pintarCifras(raiz, estado);
      const peor = peorEjemplo(estado);

      const codigo = raiz.querySelector("[data-calidad-sql]");
      if (codigo && peor) {
        codigo.textContent = consulta(peor.id, peor.datos.ejemplo && peor.datos.ejemplo.periodo);
      }
      raiz.dataset.calidadListo = "1";
    });
    // El gráfico vive en la sub-pestaña de la Guía: un contenedor oculto mide
    // cero y el lienzo saldría vacío, así que se pinta la primera vez que se
    // activa «Cómo sumar sin sobreestimar» (ver como_usar.js).
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // `init` se expone para poder probarlo sin esperar el evento del navegador.
  window.SIFCalidad = { init, ranking: (estado) => ranking(estado || datos()), consulta, TOTAL_ETIQUETA, pintarGrafico };
})();

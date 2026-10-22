/**
 * Portada (pestaña Información)
 * Sistema de Información Financiera de Chile
 *
 * 1. Completa las cifras marcadas con data-alcance="<ámbito>.<campo>" con el alcance
 *    editorial del catálogo generado (window.DOWNLOAD_CATALOG.alcance, vía
 *    window.SIFAlcance). Así la portada no se queda atrás cuando los workflows de
 *    datos publican un mes nuevo. Sin catálogo quedan las cifras escritas en el HTML.
 * 2. Conecta los botones de la portada con el explorador, el mapa y Descargas.
 *
 * Ámbitos: un nivel ("nucleo", "secundario", …), "visible", "fuera" o
 * "sector.<clave>". Campos: sectores, conjuntos, filas, filas_cortas, periodo, pct
 * y resumen.
 */
(function () {
  "use strict";

  function alcance() {
    const A = window.SIFAlcance;
    return A && A.disponible() ? A : null;
  }

  // Industrias tal como se ven: las agrupaciones (p. ej. Securitización) cuentan una vez.
  function industrias(A, sectores) {
    return new Set((sectores || []).map((s) => A.agrupacionDe(s) || s)).size;
  }

  function resumen(A, ambito, info) {
    if (ambito === "visible") {
      return `${A.numero(info.conjuntos)} conjuntos · ${A.millones(info.filas)} de filas (${A.porcentaje(info.pct_filas)})`;
    }
    if (ambito === "fuera") {
      return `${industrias(A, info.sectores)} industrias · ${A.numero(info.conjuntos)} conjuntos · ${A.porcentaje(info.pct_filas)} de las filas`;
    }
    const partes = [`${A.numero(info.conjuntos)} conjuntos`, `${A.compacto(info.filas)} filas`];
    const periodo = A.periodo(info.periodo);
    if (periodo) partes.push(periodo);
    return partes.join(" · ");
  }

  function valor(A, ruta) {
    const partes = String(ruta || "").split(".");
    const datos = A.datos();
    let ambito = partes[0];
    let campo = partes[1];
    let info = null;
    if (ambito === "sector") {
      info = datos.sectores[partes[1]] || null;
      campo = partes[2];
    } else if (ambito === "visible" || ambito === "fuera") {
      info = datos[ambito];
    } else {
      info = A.nivel(ambito);
    }
    if (!info) return null;
    switch (campo) {
      case "sectores": return A.numero((info.sectores || []).length);
      case "conjuntos": return A.numero(info.conjuntos);
      case "filas": return A.millones(info.filas);
      case "filas_cortas": return A.compacto(info.filas);
      case "periodo": return A.periodo(info.periodo) || null;
      case "pct": return A.porcentaje(info.pct_filas);
      case "resumen": return resumen(A, ambito, info);
      default: return null;
    }
  }

  function pintarCifras(raiz) {
    const A = alcance();
    if (!A || !raiz) return;
    raiz.querySelectorAll("[data-alcance]").forEach((el) => {
      const texto = valor(A, el.dataset.alcance);
      if (texto) el.textContent = texto;
    });
  }

  function accion(boton) {
    const tipo = boton.dataset.portada;
    const sector = boton.dataset.sector;
    const nav = window.SidebarNav;
    if (tipo === "explorar" && sector) {
      if (nav && typeof nav.revealSector === "function") nav.revealSector(sector, "portada");
      if (typeof window.switchMainTab === "function") window.switchMainTab("erd");
      if (window.erdInstance) window.erdInstance.focusSector(sector);
    } else if (tipo === "descargas" && sector) {
      if (typeof window.switchMainTab === "function") window.switchMainTab("downloads");
      if (window.DownloadsPanel && typeof window.DownloadsPanel.filtrarSector === "function") {
        window.DownloadsPanel.filtrarSector(sector);
      }
    } else if (tipo === "archivo") {
      if (nav && typeof nav.openArchive === "function") nav.openArchive();
      if (window.MFCUI && window.MFCUI.toast) {
        window.MFCUI.toast("Archivo y registros complementarios abiertos al final del explorador.", "info");
      }
    } else if (tipo === "alcance") {
      const destino = document.getElementById("info-alcance");
      if (destino && typeof destino.scrollIntoView === "function") destino.scrollIntoView({ block: "start", behavior: "smooth" });
    }
  }

  function init() {
    const raiz = document.getElementById("info-container");
    if (!raiz) return;
    pintarCifras(raiz);
    raiz.addEventListener("click", (event) => {
      const boton = event.target.closest("[data-portada]");
      if (boton) accion(boton);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.SIFPortada = { pintarCifras, valor: (ruta) => (alcance() ? valor(alcance(), ruta) : null) };
})();

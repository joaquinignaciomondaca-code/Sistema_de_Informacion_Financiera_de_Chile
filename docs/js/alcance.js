/**
 * Alcance editorial de la web (recorte visual de industrias)
 * Sistema de Información Financiera de Chile
 *
 * Qué industrias se destacan y cuáles pasan a archivo lo decide docs/vocabulario.json
 * («alcance»). El catálogo generado (window.DOWNLOAD_CATALOG.alcance) lo trae junto con
 * las cifras de cada nivel, de modo que la portada, el explorador, el mapa, el diccionario,
 * el visor y Descargas leen la misma bandera por sector:
 *
 *   núcleo · instituciones (secundario) · contexto · archivo · registro
 *
 * Este módulo sólo responde preguntas: nunca borra datos, vistas SQL ni rutas de descarga.
 * Si el catálogo no está cargado, todo se considera visible: la web vuelve a la navegación
 * completa en lugar de esconder algo por error.
 */
(function (global) {
  "use strict";

  // Claves con que los distintos catálogos nombran a la misma industria.
  const ALIAS = {
    afp_corporativo: "pensiones",
    afp: "pensiones",
    ccaf: "cajas_compensacion",
    corredoras: "corredoras_bolsa"
  };

  function datos() {
    const catalogo = global.DOWNLOAD_CATALOG;
    return catalogo && catalogo.alcance ? catalogo.alcance : null;
  }

  function disponible() {
    return Boolean(datos());
  }

  function clave(sector) {
    const valor = String(sector || "").trim().toLowerCase();
    return ALIAS[valor] || valor;
  }

  function niveles() {
    const d = datos();
    return d ? d.niveles : [];
  }

  function nivel(id) {
    return niveles().find((n) => n.id === id) || null;
  }

  function sector(sectorClave) {
    const d = datos();
    return d ? d.sectores[clave(sectorClave)] || null : null;
  }

  // Nivel ("nucleo", "secundario", "contexto", "archivo", "registro") o null si se desconoce.
  function nivelDe(sectorClave) {
    const info = sector(sectorClave);
    return info ? info.nivel : null;
  }

  function infoNivelDe(sectorClave) {
    return nivel(nivelDe(sectorClave));
  }

  // Visible en la navegación principal. Sin datos de alcance, todo es visible.
  function esVisible(sectorClave) {
    const d = datos();
    const n = nivelDe(sectorClave);
    if (!d || !n) return true;
    return d.visibles.indexOf(n) !== -1;
  }

  // Archivo congelado o registro complementario: fuera de la navegación principal.
  function esArchivo(sectorClave) {
    return !esVisible(sectorClave);
  }

  function aviso(sectorClave) {
    const n = infoNivelDe(sectorClave);
    return n && n.aviso ? n.aviso : "";
  }

  function tablaOculta(id) {
    const d = datos();
    return Boolean(d && d.tablas_ocultas && d.tablas_ocultas[id]);
  }

  function motivoOculta(id) {
    const d = datos();
    return (d && d.tablas_ocultas && d.tablas_ocultas[id]) || "";
  }

  // Una variante se muestra junto a su tabla principal, no como entrada aparte.
  function variante(id) {
    const d = datos();
    return (d && d.variantes && d.variantes[id]) || null;
  }

  function varianteDe(id) {
    const v = variante(id);
    return v ? v.de : null;
  }

  function agrupaciones() {
    const d = datos();
    return (d && d.agrupaciones) || {};
  }

  // Agrupación visual a la que pertenece un sector (p. ej. securitizadoras -> securitizacion).
  function agrupacionDe(sectorClave) {
    const k = clave(sectorClave);
    const todas = agrupaciones();
    return Object.keys(todas).find((id) => (todas[id].sectores || []).indexOf(k) !== -1) || null;
  }

  // Sectores que abarca un filtro: una agrupación, un nivel, "principal" (niveles visibles),
  // "fuera" (archivo y registro) o un sector suelto.
  function sectoresDe(filtro) {
    const d = datos();
    if (!d) return null;
    const f = String(filtro || "");
    const todas = agrupaciones();
    if (todas[f]) return todas[f].sectores.slice();
    if (f === "principal") return d.visible.sectores.slice();
    if (f === "fuera") return d.fuera.sectores.slice();
    const porNivel = d.orden.filter((k) => d.sectores[k].nivel === f);
    if (porNivel.length) return porNivel;
    return [clave(f)];
  }

  // Posición en el orden editorial (núcleo primero); lo desconocido va al final.
  function orden(sectorClave) {
    const d = datos();
    if (!d) return 999;
    const i = d.orden.indexOf(clave(sectorClave));
    return i === -1 ? 999 : i;
  }

  function rangoNivel(id) {
    const i = niveles().findIndex((n) => n.id === id);
    return i === -1 ? 999 : i;
  }

  // ── Formato es-CL ────────────────────────────────────────────────────────
  function numero(n) {
    return Number(n || 0).toLocaleString("es-CL");
  }

  // 11063323 -> "11,1 millones"; 129711 -> "129.711".
  function millones(n) {
    const v = Number(n || 0);
    if (v >= 1e6) {
      return (v / 1e6).toLocaleString("es-CL", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " millones";
    }
    return numero(v);
  }

  // Versión corta para etiquetas: "4,3 M", "185 mil", "296".
  function compacto(n) {
    const v = Number(n || 0);
    if (v >= 1e6) return (v / 1e6).toLocaleString("es-CL", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " M";
    if (v >= 1e4) return Math.round(v / 1e3).toLocaleString("es-CL") + " mil";
    return numero(v);
  }

  function porcentaje(p) {
    return Number(p || 0).toLocaleString("es-CL", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " %";
  }

  // {desde: "2001-01", hasta: "2026-09"} -> "2001–2026".
  function periodo(p) {
    if (!p || !p.desde || !p.hasta) return "";
    const a = p.desde.slice(0, 4);
    const b = p.hasta.slice(0, 4);
    return a === b ? a : `${a}\u2013${b}`;
  }

  global.SIFAlcance = {
    datos,
    disponible,
    clave,
    niveles,
    nivel,
    sector,
    nivelDe,
    infoNivelDe,
    esVisible,
    esArchivo,
    aviso,
    tablaOculta,
    motivoOculta,
    variante,
    varianteDe,
    agrupaciones,
    agrupacionDe,
    sectoresDe,
    orden,
    rangoNivel,
    numero,
    millones,
    compacto,
    porcentaje,
    periodo
  };
})(typeof window !== "undefined" ? window : this);

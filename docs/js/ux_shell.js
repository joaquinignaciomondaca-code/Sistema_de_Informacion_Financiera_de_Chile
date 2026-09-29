/**
 * Capa de experiencia de usuario
 * Sistema de Información Financiera de Chile
 *
 * Responsabilidades, todas de interfaz:
 *   1. Recordar la última pestaña usada (localStorage) y respetar los enlaces #sql=.
 *   2. Avisos breves (toasts) para acciones que hoy sólo dejaban un mensaje perdido.
 *   3. Reflejar el estado del motor DuckDB en la pestaña "Consultas SQL".
 *   4. Puente hacia la pestaña "Descargas": cualquier vista del sistema puede
 *      pedir que se abra con su tabla ya seleccionada.
 *   5. Atajos de teclado: Alt+1..7 cambia de pestaña, "/" enfoca la búsqueda.
 *
 * No consulta datos, no publica nada y no modifica los pipelines.
 */
(function () {
  "use strict";

  const TAB_KEY = "sif.ui.tab";
  const VALID_TABS = ["info", "erd", "dict", "data", "sql", "downloads", "normativa"];
  let toastHost = null;

  // Pestaña inicial: un enlace compartido (#sql=...) siempre abre el terminal;
  // si no, se retoma la última pestaña usada y, en su defecto, Información.
  function initialTab() {
    if (window.location.hash && window.location.hash.indexOf("#sql=") === 0) return "sql";
    let saved = null;
    try {
      saved = window.localStorage.getItem(TAB_KEY);
    } catch (e) {
      saved = null;
    }
    return VALID_TABS.indexOf(saved) !== -1 ? saved : "info";
  }

  function rememberTab(tab) {
    if (VALID_TABS.indexOf(tab) === -1) return;
    try {
      window.localStorage.setItem(TAB_KEY, tab);
    } catch (e) {
      /* almacenamiento no disponible (modo privado): se ignora */
    }
  }

  function toast(message, kind, duration) {
    if (!message) return;
    if (!toastHost) {
      toastHost = document.createElement("div");
      toastHost.className = "toast-host";
      toastHost.setAttribute("role", "status");
      toastHost.setAttribute("aria-live", "polite");
      document.body.appendChild(toastHost);
    }
    const item = document.createElement("div");
    item.className = "toast toast-" + (kind || "info");
    item.textContent = message;
    toastHost.appendChild(item);
    setTimeout(() => {
      item.classList.add("toast-out");
      setTimeout(() => item.remove(), 250);
    }, duration || 2600);
  }

  function initEngineStatus() {
    const alert = document.getElementById("sql-engine-alert");
    const errorEl = document.getElementById("sql-engine-error");
    const envEl = document.getElementById("sql-engine-env");
    const retryBtn = document.getElementById("btn-engine-retry");
    const copyBtn = document.getElementById("btn-engine-copy");
    const badge = document.getElementById("engine-badge");

    // El badge del encabezado también es un botón: al hacer clic lleva al
    // diagnóstico completo, en la pestaña de consultas.
    if (badge) {
      badge.addEventListener("click", () => {
        const client = window.DuckDBClient;
        if (client && client.engineAvailable) {
          if (typeof window.switchMainTab === "function") window.switchMainTab("sql");
          toast("Motor DuckDB activo: " + (client.engineSourceLabel || client.engineSource), "ok");
          return;
        }
        if (typeof window.switchMainTab === "function") window.switchMainTab("sql");
        if (alert && !alert.hidden && typeof alert.scrollIntoView === "function") {
          alert.scrollIntoView({ block: "nearest" });
        }
      });
    }

    if (retryBtn) {
      retryBtn.addEventListener("click", async () => {
        if (!window.DuckDBClient || !window.DuckDBClient.retry) return;
        retryBtn.disabled = true;
        const original = retryBtn.textContent;
        retryBtn.textContent = "Reintentando…";
        try {
          await window.DuckDBClient.retry();
        } finally {
          retryBtn.disabled = false;
          retryBtn.textContent = original;
        }
      });
    }

    if (copyBtn) {
      copyBtn.addEventListener("click", async () => {
        const client = window.DuckDBClient;
        const informe = (client && client.buildDiagnostics) ? client.buildDiagnostics() : "Sin diagnóstico disponible.";
        try {
          await navigator.clipboard.writeText(informe);
          toast("Diagnóstico copiado al portapapeles", "ok");
        } catch (err) {
          // Sin permiso de portapapeles, se deja el informe en la consola.
          console.log(informe);
          toast("No se pudo copiar automáticamente: el informe quedó en la consola", "info");
        }
      });
    }

    window.addEventListener("duckdb-ready", (event) => {
      const detail = (event && event.detail) || {};
      const dot = document.getElementById("sql-engine-dot");
      const hint = document.getElementById("sql-engine-hint");

      if (dot) {
        dot.classList.toggle("ready", Boolean(detail.available));
        dot.classList.toggle("failed", !detail.available);
        dot.title = detail.available
          ? `DuckDB-Wasm operativo (${detail.sourceLabel || "motor cargado"})`
          : "DuckDB-Wasm no disponible: " + (detail.error || "error desconocido");
      }

      if (hint && detail.available) {
        if (detail.source && detail.source !== "local") {
          hint.textContent = `DuckDB-Wasm activo (${detail.sourceLabel || detail.source}; la copia local no se pudo usar). Las consultas se ejecutan en tu navegador.`;
        } else {
          hint.textContent = "DuckDB-Wasm activo: cada consulta se ejecuta en tu navegador sobre los Parquet publicados.";
        }
        if (detail.unavailableViews && detail.unavailableViews.length) {
          hint.textContent += ` ${detail.unavailableViews.length} vista(s) sin archivo publicado.`;
        }
      }

      if (!alert) return;
      if (detail.available) {
        alert.hidden = true;
        return;
      }

      // Motivo: el primer intento explica casi siempre la causa raíz.
      const intentos = detail.attempts || [];
      const primero = intentos.length ? intentos[0] : null;
      errorEl.innerHTML = primero
        ? `<b>${escapeHtml(primero.label)}</b>: <code>${escapeHtml(String(primero.error))}</code>`
        : `Motivo: <code>${escapeHtml(String(detail.error || "error desconocido"))}</code>`;

      const entorno = detail.environment;
      if (entorno && envEl) {
        const si = (valor) => (valor === null || valor === undefined) ? "sin dato" : (valor ? "sí" : "no");
        const filas = [
          `WebAssembly: <b>${si(entorno.wasm)}</b>`,
          `exception handling: <b>${si(entorno.wasmExceptions)}</b>`,
          `Web Worker desde Blob: <b>${entorno.blobWorker === false ? "bloqueado" : si(entorno.blobWorker)}</b>`
        ];
        const pistas = [];
        if (entorno.blobWorker === false) {
          pistas.push("Sin Web Workers, DuckDB-Wasm no puede arrancar en este navegador o contexto.");
        }
        if (entorno.wasmExceptions === false) {
          pistas.push("Sin exception handling, el motor requiere el bundle mvp (el respaldo por CDN lo intenta).");
        }
        envEl.innerHTML = `<div class="engine-env-row">${filas.join("</div><div class=\"engine-env-row\">")}</div>` +
          (pistas.length ? `<div class="engine-env-hint">${pistas.map(escapeHtml).join(" ")}</div>` : "");
      }

      alert.hidden = false;
      if (intentos.length) {
        toast("Motor SQL no disponible: " + (primero ? primero.label : "sin detalle") + ". Ver diagnóstico en Consultas SQL.", "info");
      }
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function initShortcuts() {
    document.addEventListener("keydown", (event) => {
      const el = event.target;
      const typing = el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable);

      // Alt+1..7: cambiar de pestaña sin tocar el mouse.
      if (event.altKey && !event.ctrlKey && !event.metaKey && !typing) {
        const index = parseInt(event.key, 10);
        if (index >= 1 && index <= VALID_TABS.length) {
          event.preventDefault();
          if (typeof window.switchMainTab === "function") window.switchMainTab(VALID_TABS[index - 1]);
        }
        return;
      }

      // "/": enfocar la búsqueda del explorador (estilo GitHub).
      if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
        const search = document.getElementById("sidebar-search");
        if (search) {
          event.preventDefault();
          search.focus();
          search.select();
        }
      }
    });
  }

  // Abre la pestaña Descargas con el contexto de la vista que el visitante está
  // mirando (tabla activa del visor, con sus filas y columnas en pantalla).
  function openDownloads(contexto) {
    if (typeof window.switchMainTab === "function") window.switchMainTab("downloads");
    if (window.DownloadsPanel && contexto) {
      window.DownloadsPanel.setContexto(contexto);
      window.DownloadsPanel.render();
    }
  }

  function boot() {
    initShortcuts();
    initEngineStatus();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.MFCUI = {
    initialTab: initialTab,
    rememberTab: rememberTab,
    toast: toast,
    openDownloads: openDownloads
  };
})();

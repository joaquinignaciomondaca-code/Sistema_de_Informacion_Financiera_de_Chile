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
  const VALID_TABS = ["info", "erd", "dict", "data", "sql", "downloads", "guia"];
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
        if (client && !client.initPromise && typeof client.ensureStarted === "function") {
          // El motor arranca bajo demanda: este clic es una petición explícita.
          if (typeof window.switchMainTab === "function") window.switchMainTab("sql");
          client.ensureStarted();
          toast("Cargando DuckDB-Wasm… (wasm de 3,8 MB, sólo esta vez)", "info");
          return;
        }
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
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
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

  /* La cabecera tiene alto variable (título largo, tipografía del sistema,
   * botón de 44 px en celular). El cajón del explorador y el fondo oscurecido
   * necesitan saber dónde empieza, así que se publica como variable CSS en vez
   * de repetir el 45 px mágico en tres reglas. */
  function medirCabecera() {
    const cabecera = document.querySelector("header");
    if (!cabecera) return;
    const alto = Math.round(cabecera.getBoundingClientRect().height);
    if (alto > 0) {
      document.documentElement.style.setProperty("--sif-header-h", alto + "px");
    }
  }

  function initCabecera() {
    medirCabecera();
    window.addEventListener("resize", medirCabecera);
    window.addEventListener("orientationchange", () => setTimeout(medirCabecera, 150));
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(medirCabecera).catch(() => {});
    }
  }

  /* Aviso de teléfono: el sitio se pensó para un computador. Es una tarjeta
   * flotante que se muestra sólo por debajo de 900 px —la misma consulta que usa
   * el CSS— y sólo si la persona no la cerró antes. El descarte se guarda en el
   * navegador; si el almacenamiento está bloqueado, el aviso vuelve, que es el
   * lado seguro.
   *
   * Se cierra por tres vías —«Entendido», el aspa y la tecla Escape— porque una
   * tarjeta flotante que tapa la esquina sin una salida clara es peor que no
   * tenerla. Mientras está visible publica su alto en `--sif-aviso-alto` para
   * que los avisos breves no queden debajo. */
  const CLAVE_AVISO_MOVIL = "sif-aviso-movil-cerrado";

  function initAvisoMovil() {
    const aviso = document.getElementById("aviso-movil");
    if (!aviso) return;
    const movil = window.matchMedia ? window.matchMedia("(max-width: 900px)") : null;
    const boton = document.getElementById("aviso-movil-cerrar");
    const aspa = document.getElementById("aviso-movil-aspa");
    let cerrado = false;
    try {
      cerrado = window.localStorage.getItem(CLAVE_AVISO_MOVIL) === "1";
    } catch (error) {
      cerrado = false;
    }

    // Mide la tarjeta para que el resto de elementos flotantes se aparten.
    const medir = () => {
      if (aviso.hidden) {
        document.body.classList.remove("sif-aviso-movil");
        document.body.style.removeProperty("--sif-aviso-alto");
        return;
      }
      document.body.classList.add("sif-aviso-movil");
      const alto = Math.ceil(aviso.getBoundingClientRect().height || 0);
      if (alto) document.body.style.setProperty("--sif-aviso-alto", `${alto}px`);
    };

    const sincronizar = () => {
      aviso.hidden = cerrado || !(movil && movil.matches);
      medir();
    };

    const cerrar = () => {
      cerrado = true;
      try {
        window.localStorage.setItem(CLAVE_AVISO_MOVIL, "1");
      } catch (error) {
        /* almacenamiento bloqueado: se cierra igual en esta visita */
      }
      const activo = document.activeElement;
      const teniaFoco = aviso.contains(activo) || !activo || activo === document.body;
      sincronizar();
      // El botón desaparece con el aviso: el foco no debe quedar en el vacío.
      if (teniaFoco) {
        const principal = document.getElementById("main-content");
        if (principal) principal.focus();
      }
    };

    if (boton) boton.addEventListener("click", cerrar);
    if (aspa) aspa.addEventListener("click", cerrar);

    // Escape cierra la tarjeta sólo si el foco está dentro de ella. Un Escape
    // suelto pertenece a lo que el usuario esté usando —el explorador, un
    // modal—: cerrar el aviso por un Escape ajeno sería quitarlo sin querer.
    document.addEventListener("keydown", (evento) => {
      if (aviso.hidden || evento.key !== "Escape") return;
      if (!aviso.contains(document.activeElement)) return;
      evento.preventDefault();
      cerrar();
    });

    if (movil && movil.addEventListener) movil.addEventListener("change", sincronizar);
    window.addEventListener("resize", medir);
    if (window.ResizeObserver) {
      try {
        new ResizeObserver(medir).observe(aviso);
      } catch (error) {
        /* sin observador: la medición inicial y el resize bastan */
      }
    }
    sincronizar();
  }

  function boot() {
    initShortcuts();
    initEngineStatus();
    initCabecera();
    initAvisoMovil();
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

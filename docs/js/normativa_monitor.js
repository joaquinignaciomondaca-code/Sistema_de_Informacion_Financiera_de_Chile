/* Seguimiento normativo CMF: feed estático, filtrado por la industria activa del explorador. */
(function (global) {
  "use strict";

  const FEED_URL = "outputs/normativa_cmf/feed.json";
  const CMF_LIST_FALLBACK = "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php";
  const isOfficialCmfUrl = (value) => /^https:\/\/www\.cmfchile\.cl\//i.test(String(value || ""));
  const SECTOR_ALIASES = { afp_corporativo: "pensiones" };
  const SECTOR_LABELS = {
    seguros: "Seguros de Vida y Generales",
    agf: "Administradoras Generales de Fondos (AGF)",
    ffmm: "Fondos Mutuos (FFMM)",
    fi: "Fondos de Inversión (FI)",
    pensiones: "Fondos de Pensiones",
    bancos: "Banca Comercial",
    macro: "Macroeconomía y Tasas",
    factoring_leasing: "Factoring y Leasing",
    corredoras_bolsa: "Corredoras de Bolsa",
    securitizadoras: "Sociedades Securitizadoras",
    patrimonios_separados: "Patrimonios Separados",
    cooperativas: "Cooperativas de Ahorro y Crédito",
    cajas_compensacion: "Cajas de Compensación",
    sistemas_pago: "Sistemas de Pago",
    fintech: "FinTech y Finanzas Abiertas"
  };
  const EVENT_LABELS = {
    consulta_publica: "Consulta pública",
    nueva_norma: "Nueva norma",
    modificacion: "Modificación",
    derogacion: "Derogación",
    circular_instruccion: "Circular o instrucción",
    prorroga_o_aclaracion: "Prórroga o aclaración",
    otro: "Publicación CMF"
  };

  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[char]);

  function normalizeSector(sector) {
    const value = String(sector || "todos").trim().toLowerCase();
    return SECTOR_ALIASES[value] || value || "todos";
  }

  function filterEventsBySector(events, sector) {
    const active = normalizeSector(sector);
    const rows = Array.isArray(events) ? events : [];
    if (!active || active === "todos") return rows.slice();
    return rows.filter((event) => {
      const sectors = Array.isArray(event && event.sectors) ? event.sectors.map(normalizeSector) : [];
      return sectors.includes(active);
    });
  }

  function formatDate(value) {
    if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return "Fecha de publicación no informada";
    const [year, month, day] = value.split("-").map(Number);
    return new Date(year, month - 1, day).toLocaleDateString("es-CL", {
      day: "2-digit", month: "long", year: "numeric"
    });
  }

  function formatTimestamp(value) {
    if (!value) return "Aún no hay una ejecución registrada";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Fecha de consulta no disponible";
    return new Intl.DateTimeFormat("es-CL", {
      dateStyle: "medium", timeStyle: "short", timeZone: "America/Santiago"
    }).format(date) + " · hora de Chile";
  }

  function formatEffectiveDate(event) {
    const value = event && event.effective_date;
    const precision = event && event.effective_date_precision;
    if (precision === "inmediata" && value === "inmediata") return "Inmediata (según documento)";
    if (!value || precision === "sin_fecha") return "No identificada";
    if (precision === "mes" && /^\d{4}-\d{2}$/.test(value)) {
      const [year, month] = value.split("-").map(Number);
      return new Date(year, month - 1, 1).toLocaleDateString("es-CL", { month: "long", year: "numeric" });
    }
    return formatDate(value);
  }

  function currentSectorFromApp() {
    if (global.SidebarNav && global.SidebarNav.activeSector) return normalizeSector(global.SidebarNav.activeSector);
    if (global.MFC_ACTIVE_SECTOR) return normalizeSector(global.MFC_ACTIVE_SECTOR);
    return "seguros";
  }

  const monitor = {
    container: null,
    feed: null,
    activeSector: "seguros",
    initialized: false,
    loading: false,
    error: null,
    search: "",
    eventType: "todos",

    init() {
      this.container = document.getElementById("normativa-monitor");
      if (!this.container) return;
      if (!this.initialized) {
        this.initialized = true;
        this.activeSector = currentSectorFromApp();
        global.addEventListener("mfc:industry-change", (event) => {
          this.activeSector = normalizeSector(event.detail && event.detail.sector);
          this.render();
        });
      }
      if (!this.feed && !this.loading) this.loadFeed();
      this.render();
    },

    async loadFeed() {
      this.loading = true;
      this.error = null;
      this.render();
      try {
        const response = await fetch(`${FEED_URL}?v=${Date.now()}`, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!data || data.schema_version !== 1 || !Array.isArray(data.events)) {
          throw new Error("Estructura del feed inválida");
        }
        this.feed = data;
      } catch (error) {
        this.error = error && error.message ? error.message : "No se pudo cargar el feed";
      } finally {
        this.loading = false;
        this.render();
      }
    },

    setSearch(value) {
      this.search = String(value || "").trim().toLocaleLowerCase("es-CL");
      this.renderTimeline();
    },

    setEventType(value) {
      this.eventType = value || "todos";
      this.renderTimeline();
    },

    render() {
      if (!this.container) return;
      const feed = this.feed || {};
      const label = this.activeSector === "todos"
        ? "Todas las industrias"
        : (SECTOR_LABELS[this.activeSector] || this.activeSector);
      const relevant = filterEventsBySector(feed.events, this.activeSector);
      const unassigned = Array.isArray(feed.events)
        ? feed.events.filter((event) => !Array.isArray(event.sectors) || event.sectors.length === 0).length
        : 0;
      const needsReviewCount = Array.isArray(feed.events)
        ? feed.events.filter((event) => event.analysis_status !== "complete" || event.needs_human_review).length
        : 0;
      const latestPublished = relevant.slice().sort((a, b) => String(b.publication_date || "").localeCompare(String(a.publication_date || "")))[0];
      const latestDetectedAt = relevant.reduce((latest, event) => {
        const detectedAt = String(event.last_detected_at || "");
        return detectedAt > String(latest || "") ? detectedAt : latest;
      }, "");
      const latestPublishedText = latestPublished
        ? formatDate(latestPublished.publication_date)
        : (feed.status === "sin_ejecucion"
          ? "Pendiente de primera consulta"
          : unassigned > 0 ? "Publicaciones pendientes de clasificación" : "Sin novedades clasificadas");
      const latestDetectedText = latestDetectedAt
        ? `Detectada por el monitor: ${formatTimestamp(latestDetectedAt)}`
        : "Sin detección registrada para esta industria";
      const sourceListUrl = isOfficialCmfUrl(feed.source_url) ? feed.source_url : CMF_LIST_FALLBACK;
      const status = this.error
        ? `<div class="normativa-alert normativa-alert-error" role="alert">No se pudo actualizar el panel (${escapeHtml(this.error)}). La fecha de la última revisión exitosa se conserva.</div>`
        : this.loading
          ? `<div class="normativa-alert" role="status">Cargando publicaciones oficiales…</div>`
          : feed.status === "sin_ejecucion"
            ? `<div class="normativa-alert" role="status">El monitor aún no registra una ejecución automática. La primera consulta se realiza desde GitHub Actions.</div>`
            : needsReviewCount
              ? `<div class="normativa-alert" role="status">El feed conserva ${needsReviewCount} publicación(es) con análisis o revisión pendiente. No se interpretan como ausencia de novedades; las que no tienen sector verificado se mantienen fuera del filtro por industria.</div>`
              : "";

      this.container.innerHTML = `
        <section class="normativa-heading">
          <div class="normativa-heading-copy">
            <div class="info-section-kicker">FUENTE OFICIAL · COMISIÓN PARA EL MERCADO FINANCIERO</div>
            <h2>Novedades normativas CMF</h2>
            <p>Publicaciones oficiales relacionadas con la industria seleccionada en el explorador. La clasificación automática se muestra con citas y enlaces para que puedas verificarla en la fuente.</p>
          </div>
          <div class="normativa-status-card">
            <span class="normativa-status-dot ${feed.status === "ok" ? "is-ok" : ""}"></span>
            <span><strong>Industria activa</strong><small id="normativa-active-industry">${escapeHtml(label)}</small></span>
            <span class="normativa-status-divider"></span>
            <span><strong>Última revisión de la fuente</strong><small>${escapeHtml(formatTimestamp(feed.last_checked_at))}</small></span>
            <span><strong>Última novedad detectada</strong><small>${escapeHtml(latestPublishedText)}</small><small class="normativa-status-detected">${escapeHtml(latestDetectedText)}</small></span>
          </div>
        </section>
        ${status}
        <section class="normativa-summary-row" aria-label="Resumen del monitoreo">
          <div class="normativa-summary-chip"><strong>${relevant.length}</strong><span>publicación(es) para esta industria</span></div>
          <div class="normativa-summary-chip"><strong>${unassigned}</strong><span>sin industria asignada · no se mezclan con este filtro</span></div>
          <div class="normativa-summary-chip"><strong>${needsReviewCount}</strong><span>en análisis o revisión · no equivale a cero novedades</span></div>
          <div class="normativa-summary-source"><a href="${escapeHtml(sourceListUrl)}" target="_blank" rel="noopener noreferrer">Abrir listado oficial CMF ↗</a></div>
        </section>
        <section class="normativa-controls" aria-label="Buscar y filtrar novedades">
          <label class="normativa-search-label" for="normativa-search">Buscar en las publicaciones</label>
          <input id="normativa-search" type="search" value="${escapeHtml(this.search)}" placeholder="Norma, palabra o resumen…" autocomplete="off">
          <label class="normativa-type-label" for="normativa-type-filter">Tipo</label>
          <select id="normativa-type-filter">
            <option value="todos">Todos los tipos</option>
            ${Object.entries(EVENT_LABELS).map(([key, value]) => `<option value="${key}" ${this.eventType === key ? "selected" : ""}>${escapeHtml(value)}</option>`).join("")}
          </select>
          <span class="normativa-period-note">Últimos ${Number(feed.history_days) || 365} días</span>
        </section>
        <div id="normativa-timeline" class="normativa-timeline" aria-live="polite"></div>
        <p class="normativa-disclaimer">Herramienta informativa, no asesoría legal. Los resúmenes son asistidos por IA; la fecha de publicación proviene del listado CMF. Verifica siempre el documento oficial. Las vigencias y asociaciones sectoriales sin evidencia suficiente quedan pendientes de revisión.</p>
      `;

      const searchInput = this.container.querySelector("#normativa-search");
      if (searchInput) searchInput.addEventListener("input", (event) => this.setSearch(event.target.value));
      const typeFilter = this.container.querySelector("#normativa-type-filter");
      if (typeFilter) typeFilter.addEventListener("change", (event) => this.setEventType(event.target.value));
      this.renderTimeline();
    },

    renderTimeline() {
      if (!this.container) return;
      const timeline = this.container.querySelector("#normativa-timeline");
      if (!timeline) return;
      if (this.error) {
        timeline.innerHTML = `<div class="normativa-empty"><strong>Feed temporalmente no disponible</strong><p>La página conserva la última fecha de revisión exitosa. Vuelve a intentar más tarde.</p><button type="button" class="normativa-retry">Reintentar carga</button></div>`;
        const retry = timeline.querySelector(".normativa-retry");
        if (retry) retry.addEventListener("click", () => this.loadFeed());
        return;
      }
      const feed = this.feed || {};
      const reviewQueueCount = Array.isArray(feed.events)
        ? feed.events.filter((event) => event.analysis_status !== "complete" || event.needs_human_review).length
        : 0;
      if (this.loading && !Array.isArray(feed.events)) {
        timeline.innerHTML = `<div class="normativa-empty">Consultando el feed publicado…</div>`;
        return;
      }
      let events = filterEventsBySector(feed.events, this.activeSector);
      if (this.eventType !== "todos") events = events.filter((event) => event.event_type === this.eventType);
      if (this.search) {
        events = events.filter((event) => {
          const searchable = [
            event.title, event.description_cmf, event.summary,
            ...(event.affected_norms || []), ...(event.sectors || []).map((sector) => SECTOR_LABELS[sector] || sector)
          ].join(" ").toLocaleLowerCase("es-CL");
          return searchable.includes(this.search);
        });
      }
      events.sort((a, b) => String(b.publication_date || "").localeCompare(String(a.publication_date || "")));
      if (!events.length) {
        const noInitialRun = feed.status === "sin_ejecucion";
        const hasReviewQueue = reviewQueueCount > 0;
        const emptyTitle = noInitialRun
          ? "El monitor está listo para su primera consulta"
          : hasReviewQueue
            ? "Hay publicaciones pendientes de análisis o revisión"
            : "Sin novedades clasificadas para esta industria";
        const emptyText = noInitialRun
          ? "Cuando se ejecute el flujo de actualización, las publicaciones oficiales aparecerán aquí."
          : hasReviewQueue
            ? `El feed conserva ${reviewQueueCount} publicación(es) con revisión pendiente. No se cuentan como cero novedades; los documentos sin sector verificado se excluyen de este filtro.`
            : "No hay publicaciones asignadas a esta industria en el período cargado. Esto no descarta documentos aún pendientes de clasificación.";
        timeline.innerHTML = `<div class="normativa-empty">
          <span class="normativa-empty-icon">${noInitialRun || hasReviewQueue ? "◷" : "✓"}</span>
          <strong>${emptyTitle}</strong>
          <p>${emptyText}</p>
        </div>`;
        return;
      }
      timeline.innerHTML = events.map((event) => this.renderEvent(event)).join("");
    },

    renderEvent(event) {
      const typeLabel = EVENT_LABELS[event.event_type] || EVENT_LABELS.otro;
      const documentIdentity = [
        event.document_type,
        event.document_number ? `N° ${event.document_number}` : "",
        event.document_year || ""
      ].filter(Boolean).join(" · ");
      const dateText = formatDate(event.publication_date);
      const summary = event.summary || event.description_cmf || "Resumen pendiente de análisis.";
      const analysisPending = event.analysis_status !== "complete";
      const reviewNeeded = Boolean(event.needs_human_review);
      const pendingNotice = analysisPending
        ? `<div class="normativa-pending-note">${event.analyzed_at ? "La versión actual está pendiente de analizar; el resumen o las etiquetas conservadas pueden corresponder al análisis anterior." : "Publicación oficial conservada; el resumen y la clasificación están pendientes de análisis."}</div>`
        : "";
      const reviewFlags = Array.isArray(event.review_flags) ? event.review_flags.filter(Boolean) : [];
      const reviewFlagNote = reviewNeeded && reviewFlags.length
        ? `<div class="normativa-pending-note"><strong>Revisión requerida:</strong> ${reviewFlags.map(escapeHtml).join(" · ")}</div>`
        : "";
      const sectors = Array.isArray(event.sectors) ? event.sectors : [];
      const tags = sectors.map((sector) => `<span class="normativa-sector-tag">${escapeHtml(SECTOR_LABELS[sector] || sector)}</span>`).join("");
      const norms = Array.isArray(event.affected_norms) ? event.affected_norms : [];
      const effective = formatEffectiveDate(event);
      const sourceQuote = event.summary_evidence
        ? `<blockquote class="normativa-evidence">“${escapeHtml(event.summary_evidence)}”${event.summary_evidence_page ? `<small>PDF, pág. ${Number(event.summary_evidence_page)}</small>` : `<small>Descripción del listado CMF</small>`}</blockquote>`
        : "";
      const sectorEvidence = (Array.isArray(event.sector_evidence) ? event.sector_evidence : [])
        .filter((item) => item && item.quote)
        .map((item) => `<li><strong>${escapeHtml(SECTOR_LABELS[item.sector] || item.sector)}:</strong> “${escapeHtml(item.quote)}”${item.page ? ` · pág. ${Number(item.page)}` : " · listado CMF"}</li>`).join("");
      const normEvidence = (Array.isArray(event.norm_evidence) ? event.norm_evidence : [])
        .filter((item) => item && item.quote)
        .map((item) => `<li><strong>${escapeHtml(item.norm)}:</strong> “${escapeHtml(item.quote)}”${Number(item.page) > 0 ? ` · pág. ${Number(item.page)}` : " · listado CMF"}</li>`).join("");
      const details = sourceQuote || sectorEvidence || normEvidence
        ? `<details class="normativa-details"><summary>Ver evidencia usada en la clasificación</summary>${sourceQuote}<ul>${sectorEvidence}${normEvidence}</ul></details>`
        : `<div class="normativa-pending-note">El documento aún no cuenta con citas validadas para esta clasificación.</div>`;
      const revision = Array.isArray(event.revisions) && event.revisions.length
        ? `<span class="normativa-badge normativa-badge-update">PDF actualizado</span>` : "";
      const reviewBadge = reviewNeeded
        ? `<span class="normativa-badge normativa-badge-review">Revisión pendiente</span>`
        : analysisPending
          ? `<span class="normativa-badge normativa-badge-pending">Análisis pendiente</span>`
          : `<span class="normativa-badge normativa-badge-ok">Evidencia disponible</span>`;
      const normValue = norms.length
        ? norms.map(escapeHtml).join(" · ")
        : (analysisPending ? "Pendiente de análisis" : "No identificadas en el documento");
      const normText = `<div class="normativa-event-meta"><strong>Norma(s) relacionada(s)</strong><span>${normValue}</span></div>`;
      const officialUrl = isOfficialCmfUrl(event.document_url)
        ? event.document_url
        : (isOfficialCmfUrl(event.source_url) ? event.source_url : CMF_LIST_FALLBACK);
      const documentLink = isOfficialCmfUrl(event.document_url)
        ? `<a class="normativa-link-primary" href="${escapeHtml(event.document_url)}" target="_blank" rel="noopener noreferrer">Documento oficial ↗</a>`
        : "";
      return `<article class="normativa-event" data-event-id="${escapeHtml(event.id)}">
        <div class="normativa-event-rail"><span class="normativa-event-dot"></span><time>${escapeHtml(dateText)}</time></div>
        <div class="normativa-event-card">
          <div class="normativa-event-topline"><span class="normativa-badge normativa-badge-type">${escapeHtml(typeLabel)}</span>${documentIdentity ? `<span class="normativa-badge normativa-badge-document">${escapeHtml(documentIdentity)}</span>` : ""}${reviewBadge}${revision}</div>
          <h3>${escapeHtml(event.title || "Publicación normativa CMF")}</h3>
          <p class="normativa-summary">${escapeHtml(summary)}</p>
          ${tags ? `<div class="normativa-sector-tags" aria-label="Industrias asignadas">${tags}</div>` : ""}
          <div class="normativa-event-facts">
            ${normText}
            <div class="normativa-event-meta"><strong>Vigencia identificada</strong><span>${escapeHtml(effective)}${event.effective_date_evidence ? ` <small>· cita en el documento</small>` : ""}</span></div>
          </div>
          ${pendingNotice}
          ${reviewFlagNote}
          ${details}
          <div class="normativa-event-actions">${documentLink}<a href="${escapeHtml(officialUrl)}" target="_blank" rel="noopener noreferrer">Ficha/listado CMF ↗</a></div>
          <div class="normativa-ai-note">${event.ai_model ? `Análisis asistido por ${escapeHtml(event.ai_model)}` : "Análisis automático pendiente"}${event.confidence ? ` · confianza cualitativa: ${escapeHtml(event.confidence)}` : ""}</div>
        </div>
      </article>`;
    }
  };

  global.NormativaMonitor = {
    init: () => monitor.init(),
    refresh: () => monitor.loadFeed(),
    filterEventsBySector,
    normalizeSector,
    get activeSector() { return monitor.activeSector; }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => monitor.init(), { once: true });
  } else {
    monitor.init();
  }
})(window);

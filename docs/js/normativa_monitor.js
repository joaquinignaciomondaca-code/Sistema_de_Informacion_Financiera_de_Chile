/* Seguimiento normativo CMF: feed estático sincronizado con la industria activa del explorador. */
(function (global) {
  "use strict";

  const FEED_URL = "outputs/normativa_cmf/feed.json";
  const CMF_LIST_FALLBACK = "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php";
  const PAGE_SIZE = 20;
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
  const REVIEW_FLAG_LABELS = {
    resumen_sin_evidencia_verificable: "Resumen sin cita verificable",
    vigencia_sin_evidencia_verificable: "Vigencia sin evidencia verificable",
    sector_sin_evidencia_verificable: "Industria sin cita verificable",
    sin_industria_asignada: "Industria pendiente de verificación",
    norma_sin_evidencia_verificable: "Norma relacionada sin cita verificable",
    norma_afectada_sin_respaldo: "Norma afectada sin respaldo verificable",
    pdf_sin_texto_nativo_o_no_disponible: "No se pudo extraer texto del PDF",
    tipo_evento_no_validado: "Tipo de publicación pendiente de validación",
    confianza_no_validada: "Confianza del análisis no validada"
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

  function formatReviewFlag(flag) {
    const value = String(flag || "").trim();
    if (REVIEW_FLAG_LABELS[value]) return REVIEW_FLAG_LABELS[value];
    if (/^API de análisis suspendida tras HTTP \d{3}/i.test(value)) {
      return "Análisis automático pausado por el servicio; se reintentará en otra ejecución";
    }
    if (/^API de análisis no disponible/i.test(value)) {
      return "Análisis automático no disponible en esta ejecución";
    }
    if (/^Límite de llamadas de análisis alcanzado/i.test(value)) {
      return "Análisis pendiente por el límite de esta ejecución";
    }
    if (/^Límite de descargas PDF alcanzado/i.test(value)) {
      return "Documento pendiente de descarga en la próxima ejecución";
    }
    if (/^Estado de interacción no completado/i.test(value)) {
      return "El servicio de análisis no completó la respuesta";
    }
    if (/^HTTP \d{3}$/i.test(value)) {
      return "Error temporal al consultar el servicio de análisis";
    }
    return "Dato pendiente de verificación";
  }

  function buildDocumentTitle(event) {
    const row = event || {};
    const documentType = String(row.document_type || "").trim();
    const documentNumber = String(row.document_number || "").trim();
    const documentYear = String(row.document_year || "").trim();
    const title = String(row.title || "").trim();
    const bareNumber = /^\d[\d.]*$/.test(title);

    if (documentType && documentNumber) {
      return `${documentType} N° ${documentNumber}${documentYear ? ` · ${documentYear}` : ""}`;
    }
    if (title && !bareNumber) return title;
    if (documentType) return documentType;
    if (bareNumber) return `Documento CMF N° ${title}`;
    return "Publicación normativa CMF";
  }

  function paginateEvents(events, requestedPage, pageSize = PAGE_SIZE) {
    const rows = Array.isArray(events) ? events : [];
    const size = Math.max(1, Math.floor(Number(pageSize) || PAGE_SIZE));
    const totalPages = Math.max(1, Math.ceil(rows.length / size));
    const page = Math.min(totalPages, Math.max(1, Math.floor(Number(requestedPage) || 1)));
    const startIndex = rows.length ? (page - 1) * size : 0;
    return {
      items: rows.slice(startIndex, startIndex + size),
      page,
      pageSize: size,
      totalPages,
      totalCount: rows.length,
      start: rows.length ? startIndex + 1 : 0,
      end: Math.min(startIndex + size, rows.length)
    };
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
    page: 1,

    init() {
      this.container = document.getElementById("normativa-monitor");
      if (!this.container) return;
      if (!this.initialized) {
        this.initialized = true;
        this.activeSector = currentSectorFromApp();
        global.addEventListener("mfc:industry-change", (event) => {
          this.activeSector = normalizeSector(event.detail && event.detail.sector);
          this.page = 1;
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
      this.search = String(value || "").trim();
      this.page = 1;
      this.renderTimeline();
    },

    setEventType(value) {
      this.eventType = value || "todos";
      this.page = 1;
      this.renderTimeline();
    },

    setPage(value) {
      this.page = Number(value) || 1;
      this.renderTimeline();
    },

    clearSearchAndType() {
      this.search = "";
      this.eventType = "todos";
      this.page = 1;
      this.render();
    },

    render() {
      if (!this.container) return;
      const feed = this.feed || {};
      const feedEvents = Array.isArray(feed.events) ? feed.events : [];
      const industryLabel = this.activeSector === "todos"
        ? "Todas las industrias"
        : (SECTOR_LABELS[this.activeSector] || this.activeSector);
      const relevant = filterEventsBySector(feedEvents, this.activeSector);
      const unassignedCount = feedEvents.filter((event) => !Array.isArray(event.sectors) || event.sectors.length === 0).length;
      const pendingAnalysisCount = feedEvents.filter((event) => event.analysis_status !== "complete").length;
      const humanReviewCount = feedEvents.filter((event) => event.analysis_status === "complete" && event.needs_human_review).length;
      const latestPublished = relevant.slice().sort((a, b) => String(b.publication_date || "").localeCompare(String(a.publication_date || "")))[0];
      const latestDetectedAt = feed.last_detected_at || feedEvents.reduce((latest, event) => {
        const detectedAt = String(event.last_detected_at || "");
        return detectedAt > String(latest || "") ? detectedAt : latest;
      }, "");
      const sourceListUrl = isOfficialCmfUrl(feed.source_url) ? feed.source_url : CMF_LIST_FALLBACK;
      const status = this.error
        ? `<div class="normativa-alert normativa-alert-error" role="alert"><span>No se pudo actualizar la fuente CMF. ${Array.isArray(feed.events) ? "La última consulta exitosa sigue visible." : "Las publicaciones no están disponibles por ahora."}</span><button type="button" class="normativa-retry">Reintentar</button></div>`
        : this.loading
          ? `<div class="normativa-alert" role="status">Cargando publicaciones oficiales…</div>`
          : feed.status === "sin_ejecucion"
            ? `<div class="normativa-alert" role="status">El monitor aún no registra una consulta exitosa. Las publicaciones aparecerán cuando se ejecute la actualización automática.</div>`
            : pendingAnalysisCount > 0
              ? `<div class="normativa-alert normativa-alert-global" role="status"><strong>Estado global del feed:</strong> ${pendingAnalysisCount} publicación(es) todavía tienen análisis automático pendiente. No equivale a ausencia de novedades ni es una cifra exclusiva de ${escapeHtml(industryLabel)}.</div>`
              : "";

      this.container.innerHTML = `
        <section class="normativa-heading">
          <div class="normativa-heading-copy">
            <div class="info-section-kicker">FUENTE OFICIAL · COMISIÓN PARA EL MERCADO FINANCIERO</div>
            <h2 id="normativa-title">Novedades normativas CMF</h2>
            <p>La industria se sincroniza automáticamente con la tabla seleccionada en el explorador. Las fichas conservan sus marcas de revisión; las publicaciones sin industria asignada se informan por separado y no aparecen al filtrar una industria.</p>
          </div>
          <div class="normativa-status-card" aria-label="Estado y fechas del monitoreo">
            <div class="normativa-status-feed">
              <span class="normativa-status-dot ${feed.status === "ok" ? "is-ok" : ""}" aria-hidden="true"></span>
              <span><strong>Estado de la fuente</strong><small>${feed.status === "ok" ? "Consulta oficial completada" : "Estado no disponible"}</small></span>
            </div>
            <div class="normativa-status-item">
              <strong>Industria activa</strong>
              <small>${escapeHtml(industryLabel)}</small>
            </div>
            <div class="normativa-status-item">
              <strong>Última publicación asociada a esta industria</strong>
              <small>${escapeHtml(latestPublished ? formatDate(latestPublished.publication_date) : "Sin publicaciones clasificadas")}</small>
            </div>
            <div class="normativa-status-item">
              <strong>Última consulta oficial</strong>
              <small>${escapeHtml(formatTimestamp(feed.last_checked_at))}</small>
            </div>
            <div class="normativa-status-item normativa-status-item-global">
              <strong>Última detección del feed · global</strong>
              <small>${escapeHtml(latestDetectedAt ? formatTimestamp(latestDetectedAt) : "Sin detección registrada")}</small>
            </div>
          </div>
        </section>
        ${status}
        <section class="normativa-summary-section" aria-label="Indicadores del monitor">
          <div class="normativa-summary-row">
            <div class="normativa-summary-chip normativa-summary-chip-industry">
              <strong>${relevant.length}</strong>
              <span class="normativa-chip-copy"><span>Publicaciones asociadas</span><small>Industria activa</small></span>
            </div>
            <div class="normativa-summary-chip">
              <strong>${unassignedCount}</strong>
              <span class="normativa-chip-copy"><span>Sin industria verificada</span><small>Total del feed</small></span>
            </div>
            <div class="normativa-summary-chip">
              <strong>${pendingAnalysisCount}</strong>
              <span class="normativa-chip-copy"><span>Análisis pendiente</span><small>Total del feed</small></span>
            </div>
            <div class="normativa-summary-chip">
              <strong>${humanReviewCount}</strong>
              <span class="normativa-chip-copy"><span>Análisis completo con revisión humana</span><small>Total del feed</small></span>
            </div>
          </div>
          <div class="normativa-summary-footer">
            <p>Las cifras globales describen todo el feed y pueden superponerse; no son conteos de la industria activa.</p>
            <a href="${escapeHtml(sourceListUrl)}" target="_blank" rel="noopener noreferrer">Abrir listado oficial CMF ↗</a>
          </div>
        </section>
        <section class="normativa-controls" aria-label="Buscar y filtrar publicaciones por texto o tipo">
          <div class="normativa-control-field">
            <label for="normativa-search">Buscar publicaciones</label>
            <input id="normativa-search" type="search" value="${escapeHtml(this.search)}" placeholder="Norma, número, palabra o resumen…" autocomplete="off">
          </div>
          <div class="normativa-control-field">
            <label for="normativa-type-filter">Tipo de publicación</label>
            <select id="normativa-type-filter">
              <option value="todos">Todos los tipos</option>
              ${Object.entries(EVENT_LABELS).map(([key, value]) => `<option value="${key}" ${this.eventType === key ? "selected" : ""}>${escapeHtml(value)}</option>`).join("")}
            </select>
          </div>
          <span class="normativa-period-note">Últimos ${Number(feed.history_days) || 365} días</span>
        </section>
        <div id="normativa-timeline" class="normativa-timeline"></div>
        <p class="normativa-disclaimer">Herramienta informativa, no asesoría legal. Los resúmenes son asistidos por IA; la fecha de publicación proviene del listado CMF. Verifica siempre el documento oficial. Las fechas de vigencia y asociaciones sectoriales sin evidencia suficiente requieren revisión.</p>
      `;

      const searchInput = this.container.querySelector("#normativa-search");
      if (searchInput) searchInput.addEventListener("input", (event) => this.setSearch(event.target.value));
      const typeFilter = this.container.querySelector("#normativa-type-filter");
      if (typeFilter) typeFilter.addEventListener("change", (event) => this.setEventType(event.target.value));
      const retryButton = this.container.querySelector(".normativa-retry");
      if (retryButton) retryButton.addEventListener("click", () => this.loadFeed());
      this.renderTimeline();
    },

    renderTimeline() {
      if (!this.container) return;
      const timeline = this.container.querySelector("#normativa-timeline");
      if (!timeline) return;
      const feed = this.feed || {};
      if (this.error && !Array.isArray(feed.events)) {
        timeline.innerHTML = `<div class="normativa-empty" role="alert"><strong>No fue posible cargar las publicaciones</strong><p>Inténtalo de nuevo cuando la fuente esté disponible.</p></div>`;
        return;
      }
      if (this.loading && !Array.isArray(feed.events)) {
        timeline.innerHTML = `<div class="normativa-empty" role="status"><strong>Consultando el feed CMF…</strong><p>Las publicaciones oficiales aparecerán aquí.</p></div>`;
        return;
      }

      const feedEvents = Array.isArray(feed.events) ? feed.events : [];
      const unassignedCount = feedEvents.filter((event) => !Array.isArray(event.sectors) || event.sectors.length === 0).length;
      const pendingAnalysisCount = feedEvents.filter((event) => event.analysis_status !== "complete").length;
      const filtersActive = Boolean(this.search.trim()) || this.eventType !== "todos";
      let events = filterEventsBySector(feedEvents, this.activeSector);
      if (this.eventType !== "todos") events = events.filter((event) => event.event_type === this.eventType);
      const searchTerm = this.search.trim().toLocaleLowerCase("es-CL");
      if (searchTerm) {
        events = events.filter((event) => {
          const searchable = [
            event.title,
            event.document_type,
            event.document_number,
            event.document_year,
            event.description_cmf,
            event.summary,
            ...(event.affected_norms || []),
            ...(event.sectors || []).map((sector) => SECTOR_LABELS[sector] || sector),
            ...(event.review_flags || []).map(formatReviewFlag)
          ].join(" ").toLocaleLowerCase("es-CL");
          return searchable.includes(searchTerm);
        });
      }
      events.sort((a, b) => String(b.publication_date || "").localeCompare(String(a.publication_date || "")));

      if (!events.length) {
        this.page = 1;
        const noInitialRun = feed.status === "sin_ejecucion";
        let emptyTitle;
        let emptyText;
        if (noInitialRun) {
          emptyTitle = "El monitor está listo para su primera consulta";
          emptyText = "Cuando se ejecute la actualización automática, las publicaciones oficiales aparecerán aquí.";
        } else if (filtersActive) {
          emptyTitle = "No hay coincidencias con estos criterios";
          emptyText = "Prueba otra palabra o selecciona todos los tipos de publicación.";
        } else if (this.activeSector !== "todos") {
          const context = [
            unassignedCount ? `${unassignedCount} publicación(es) del feed global no tienen industria verificada` : "",
            pendingAnalysisCount ? `${pendingAnalysisCount} publicación(es) tienen análisis automático pendiente` : ""
          ].filter(Boolean).join("; ");
          emptyTitle = `Sin publicaciones clasificadas para ${SECTOR_LABELS[this.activeSector] || this.activeSector}`;
          emptyText = `El filtro sigue la selección del explorador y muestra las publicaciones clasificadas para esa industria. Las publicaciones sin industria asignada no se mezclan en esta vista; las marcas de revisión indican qué datos requieren confirmación.${context ? ` ${context}.` : ""}`;
        } else {
          emptyTitle = "No hay publicaciones en el período cargado";
          emptyText = "El listado oficial CMF no contiene publicaciones dentro de la ventana consultada.";
        }
        timeline.innerHTML = `<div class="normativa-empty" role="status">
          <span class="normativa-empty-icon" aria-hidden="true">${noInitialRun || pendingAnalysisCount ? "◷" : "✓"}</span>
          <strong>${escapeHtml(emptyTitle)}</strong>
          <p>${escapeHtml(emptyText)}</p>
          ${filtersActive ? `<button type="button" class="normativa-clear-filters">Limpiar búsqueda y tipo</button>` : ""}
        </div>`;
        const clearButton = timeline.querySelector(".normativa-clear-filters");
        if (clearButton) clearButton.addEventListener("click", () => this.clearSearchAndType());
        return;
      }

      const page = paginateEvents(events, this.page, PAGE_SIZE);
      this.page = page.page;
      const cards = page.items.map((event) => this.renderEvent(event)).join("");
      const pagination = page.totalPages > 1
        ? `<nav class="normativa-pagination" aria-label="Páginas de publicaciones">
            <button type="button" data-normativa-page="${page.page - 1}" ${page.page === 1 ? "disabled" : ""} aria-label="Página anterior">Anterior</button>
            <span aria-live="polite">Página <strong>${page.page}</strong> de ${page.totalPages}</span>
            <button type="button" data-normativa-page="${page.page + 1}" ${page.page === page.totalPages ? "disabled" : ""} aria-label="Página siguiente">Siguiente</button>
          </nav>`
        : "";
      timeline.innerHTML = `
        <div class="normativa-results-header">
          <p role="status" aria-live="polite">Mostrando <strong>${page.start}–${page.end}</strong> de <strong>${page.totalCount}</strong> publicaciones</p>
          <span>Ordenadas por fecha de publicación</span>
        </div>
        <div class="normativa-timeline-list">${cards}</div>
        ${pagination}
      `;
      timeline.querySelectorAll("[data-normativa-page]").forEach((button) => {
        button.addEventListener("click", () => this.setPage(button.dataset.normativaPage));
      });
    },

    renderEvent(event) {
      const typeLabel = EVENT_LABELS[event.event_type] || EVENT_LABELS.otro;
      const heading = buildDocumentTitle(event);
      const dateText = formatDate(event.publication_date);
      const summary = String(event.summary || event.description_cmf || "Resumen pendiente de análisis.").trim();
      const analysisPending = event.analysis_status !== "complete";
      const reviewFlags = Array.isArray(event.review_flags) ? event.review_flags.filter(Boolean) : [];
      const reviewNeeded = Boolean(event.needs_human_review || reviewFlags.length);
      const reviewLabels = [...new Set(reviewFlags.map(formatReviewFlag))];
      const pendingNotice = analysisPending
        ? `<p class="normativa-pending-note">El análisis automático de esta publicación todavía no está completo. Esto no significa que la publicación no exista.</p>`
        : "";
      const reviewFlagNote = reviewNeeded
        ? reviewLabels.length
          ? `<div class="normativa-review-summary"><strong>Revisión pendiente:</strong>${reviewLabels.map((label) => `<span class="normativa-review-reason">${escapeHtml(label)}</span>`).join("")}</div>`
          : `<p class="normativa-pending-note">Esta publicación requiere verificación humana adicional.</p>`
        : "";
      const sectors = Array.isArray(event.sectors) ? event.sectors : [];
      const tags = sectors.length
        ? sectors.map((sector) => `<span class="normativa-sector-tag">${escapeHtml(SECTOR_LABELS[sector] || sector)}</span>`).join("")
        : `<span class="normativa-sector-tag normativa-sector-tag-unassigned">Industria sin verificar</span>`;
      const norms = Array.isArray(event.affected_norms) ? event.affected_norms : [];
      const effective = formatEffectiveDate(event);
      const sourceQuote = event.summary_evidence
        ? `<blockquote class="normativa-evidence">“${escapeHtml(event.summary_evidence)}”<small>${Number(event.summary_evidence_page) > 0 ? `PDF, pág. ${Number(event.summary_evidence_page)}` : "Descripción del listado oficial CMF"}</small></blockquote>`
        : "";
      const sectorEvidence = (Array.isArray(event.sector_evidence) ? event.sector_evidence : [])
        .filter((item) => item && item.quote)
        .map((item) => `<li><strong>${escapeHtml(SECTOR_LABELS[item.sector] || item.sector)}:</strong> “${escapeHtml(item.quote)}”${Number(item.page) > 0 ? ` · pág. ${Number(item.page)}` : " · listado CMF"}</li>`).join("");
      const normEvidence = (Array.isArray(event.norm_evidence) ? event.norm_evidence : [])
        .filter((item) => item && item.quote)
        .map((item) => `<li><strong>${escapeHtml(item.norm)}:</strong> “${escapeHtml(item.quote)}”${Number(item.page) > 0 ? ` · pág. ${Number(item.page)}` : " · listado CMF"}</li>`).join("");
      const evidenceRows = `${sectorEvidence}${normEvidence}`;
      const evidenceDetails = sourceQuote || evidenceRows
        ? `<details class="normativa-details"><summary>Ver citas y evidencia</summary>${sourceQuote}${evidenceRows ? `<ul>${evidenceRows}</ul>` : ""}</details>`
        : "";
      const statusBadge = analysisPending
        ? `<span class="normativa-badge normativa-badge-pending">Análisis pendiente</span>`
        : reviewNeeded
          ? `<span class="normativa-badge normativa-badge-review">Revisión humana</span>`
          : `<span class="normativa-badge normativa-badge-ok">Análisis completo</span>`;
      const revision = Array.isArray(event.revisions) && event.revisions.length
        ? `<span class="normativa-badge normativa-badge-update">PDF actualizado</span>` : "";
      const normSummary = norms.length
        ? `${norms.slice(0, 2).map(escapeHtml).join(" · ")}${norms.length > 2 ? ` · +${norms.length - 2} más` : ""}`
        : (analysisPending ? "Pendiente de análisis" : "No identificadas");
      const summaryHtml = summary.length > 300
        ? `<p class="normativa-summary">${escapeHtml(summary.slice(0, 280).trim())}…</p><details class="normativa-summary-more"><summary>Leer resumen completo</summary><p>${escapeHtml(summary)}</p></details>`
        : `<p class="normativa-summary">${escapeHtml(summary)}</p>`;
      const normText = `<div class="normativa-event-meta"><strong>Normas relacionadas</strong><span>${normSummary}</span></div>`;
      const documentUrl = isOfficialCmfUrl(event.document_url) ? event.document_url : "";
      const officialUrl = documentUrl || (isOfficialCmfUrl(event.source_url) ? event.source_url : CMF_LIST_FALLBACK);
      const documentLink = documentUrl
        ? `<a class="normativa-link-primary" href="${escapeHtml(documentUrl)}" target="_blank" rel="noopener noreferrer">Abrir documento oficial ↗</a>`
        : "";
      const modelLabel = event.ai_model ? `Análisis asistido por ${event.ai_model}` : "Sin modelo registrado";
      const confidenceLabel = event.confidence ? ` · confianza cualitativa: ${event.confidence}` : "";
      const publicationDateAttr = /^\d{4}-\d{2}-\d{2}$/.test(String(event.publication_date || ""))
        ? ` datetime="${escapeHtml(event.publication_date)}"`
        : "";

      return `<article class="normativa-event" data-event-id="${escapeHtml(event.id)}">
        <div class="normativa-event-rail"><span class="normativa-event-dot" aria-hidden="true"></span><time${publicationDateAttr}>${escapeHtml(dateText)}</time></div>
        <div class="normativa-event-card">
          <div class="normativa-event-topline">
            <span class="normativa-badge normativa-badge-type">${escapeHtml(typeLabel)}</span>
            ${statusBadge}${revision}
          </div>
          <h3>${escapeHtml(heading)}</h3>
          ${summaryHtml}
          <div class="normativa-sector-tags" aria-label="Industrias clasificadas">${tags}</div>
          <div class="normativa-event-facts">
            ${normText}
            <div class="normativa-event-meta"><strong>Vigencia identificada</strong><span>${escapeHtml(effective)}${event.effective_date_evidence ? ` <small>· cita respaldada</small>` : ""}</span></div>
          </div>
          ${pendingNotice}
          ${reviewFlagNote}
          ${evidenceDetails}
          <div class="normativa-event-actions">${documentLink}<a href="${escapeHtml(officialUrl)}" target="_blank" rel="noopener noreferrer">Ficha/listado CMF ↗</a></div>
          <details class="normativa-details normativa-provenance"><summary>Detalles del análisis</summary><p>${escapeHtml(modelLabel)}${escapeHtml(confidenceLabel)}</p></details>
        </div>
      </article>`;
    }
  };

  global.NormativaMonitor = {
    init: () => monitor.init(),
    refresh: () => monitor.loadFeed(),
    filterEventsBySector,
    normalizeSector,
    formatReviewFlag,
    buildDocumentTitle,
    paginateEvents,
    renderEvent: (event) => monitor.renderEvent(event),
    get activeSector() { return monitor.activeSector; }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => monitor.init(), { once: true });
  } else {
    monitor.init();
  }
})(window);

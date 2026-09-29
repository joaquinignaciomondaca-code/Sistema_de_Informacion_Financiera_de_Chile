#!/usr/bin/env node
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const monitorPath = "docs/js/normativa_monitor.js";
const htmlPath = "docs/index.html";
const cssPath = "docs/css/app.css";
const sidebarPath = "docs/js/sidebar.js";
const viewerPath = "docs/js/data_viewer.js";
const feedPath = "docs/outputs/normativa_cmf/feed.json";

const monitorSource = fs.readFileSync(monitorPath, "utf8");
const feed = JSON.parse(fs.readFileSync(feedPath, "utf8"));
const industryListeners = {};
const fakeTimeline = {
  innerHTML: "",
  buttons: [],
  querySelector() { return null; },
  querySelectorAll() {
    this.buttons = [...this.innerHTML.matchAll(/<button\b[^>]*data-normativa-page="(\d+)"[^>]*>/g)].map((match) => {
      const button = {
        dataset: { normativaPage: match[1] },
        listener: null,
        addEventListener(name, listener) { if (name === "click") this.listener = listener; },
        click() { if (this.listener) this.listener({ target: this }); }
      };
      return button;
    });
    return this.buttons;
  }
};
const fakeContainer = {
  innerHTML: "",
  querySelector(selector) { return selector === "#normativa-timeline" ? fakeTimeline : null; }
};
const fakeWindow = {
  MFC_ACTIVE_SECTOR: "seguros",
  addEventListener(name, listener) { industryListeners[name] = listener; },
  dispatchEvent(event) { if (industryListeners[event.type]) industryListeners[event.type](event); }
};
const fakeDocument = {
  readyState: "loading",
  addEventListener() {},
  getElementById(id) { return id === "normativa-monitor" ? fakeContainer : null; }
};
vm.runInNewContext(monitorSource, {
  window: fakeWindow,
  document: fakeDocument,
  Intl,
  Date,
  String,
  Array,
  Number,
  RegExp,
  setTimeout,
  clearTimeout,
  fetch() { return Promise.resolve({ ok: true, json: () => Promise.resolve(feed) }); }
});

const monitor = fakeWindow.NormativaMonitor;
assert.ok(monitor, "El módulo expone window.NormativaMonitor");
monitor.init();
fakeWindow.dispatchEvent({ type: "mfc:industry-change", detail: { sector: "ffmm", source: "table" } });
assert.equal(monitor.activeSector, "ffmm", "la vista sigue el cambio de industria de la tabla seleccionada");

const sampleEvents = [
  { id: "ffmm-a", sectors: ["ffmm"] },
  { id: "insurance-a", sectors: ["seguros"] },
  { id: "cross-sector", sectors: ["ffmm", "agf"] },
  { id: "unassigned", sectors: [] }
];
assert.deepEqual(
  monitor.filterEventsBySector(sampleEvents, "ffmm").map((event) => event.id).sort(),
  ["cross-sector", "ffmm-a"]
);
assert.deepEqual(
  monitor.filterEventsBySector(sampleEvents, "seguros").map((event) => event.id),
  ["insurance-a"]
);
assert.deepEqual(
  monitor.filterEventsBySector(sampleEvents, "afp_corporativo"),
  [],
  "una publicación sin industria no se asigna por defecto al alias AFP"
);
assert.equal(monitor.normalizeSector("afp_corporativo"), "pensiones");
assert.equal(monitor.filterEventsBySector(sampleEvents, "todos").length, 4);

const reviewEvent = {
  id: "cmf-review-fixture",
  publication_date: "2026-09-28",
  title: "1234",
  document_type: "Circular",
  document_number: "1234",
  document_year: "2026",
  event_type: "circular_instruccion",
  analysis_status: "complete",
  needs_human_review: true,
  review_flags: ["vigencia_sin_evidencia_verificable", "sector_sin_evidencia_verificable"],
  sectors: ["ffmm"],
  summary: "Resumen de prueba con <contenido> y & caracteres especiales.",
  summary_evidence: "La entidad debe informar el cambio en el plazo indicado.",
  summary_evidence_page: 4,
  sector_evidence: [{ sector: "ffmm", quote: "Fondos mutuos y sus administradoras", page: 2 }],
  affected_norms: ["NCG N° 123"],
  effective_date: "2027-01-01",
  effective_date_precision: "dia",
  source_url: "https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php",
  document_url: "https://www.cmfchile.cl/normativa/cir_1234_2026.pdf",
  ai_model: "gemini-flash-lite-latest",
  confidence: "media"
};

assert.equal(monitor.buildDocumentTitle(reviewEvent), "Circular N° 1234 · 2026");
assert.equal(monitor.buildDocumentTitle({ title: "42" }), "Documento CMF N° 42");
assert.equal(monitor.buildDocumentTitle({ title: "Consulta sobre fondos" }), "Consulta sobre fondos");
assert.equal(
  monitor.formatReviewFlag("vigencia_sin_evidencia_verificable"),
  "Vigencia sin evidencia verificable"
);
assert.equal(
  monitor.formatReviewFlag("sector_sin_evidencia_verificable"),
  "Industria sin cita verificable"
);
assert.equal(
  monitor.formatReviewFlag("API de análisis suspendida tras HTTP 429"),
  "Análisis automático pausado por el servicio; se reintentará en otra ejecución"
);
assert.equal(monitor.formatReviewFlag("marca_tecnica_desconocida"), "Dato pendiente de verificación");

const renderedReview = monitor.renderEvent(reviewEvent);
assert.ok(renderedReview.includes("Circular N° 1234 · 2026"), "el encabezado identifica tipo, número y año");
assert.ok(renderedReview.includes("Revisión humana"), "la revisión pendiente queda visible en la ficha");
assert.ok(renderedReview.includes("class=\"normativa-review-summary\""), "los motivos de revisión quedan visibles sin abrir otra sección");
assert.ok(renderedReview.includes("Revisión pendiente:"), "la ficha explica por qué conserva la marca de revisión");
assert.ok(renderedReview.includes("Vigencia sin evidencia verificable"));
assert.ok(renderedReview.includes("Industria sin cita verificable"));
assert.ok(!renderedReview.includes("vigencia_sin_evidencia_verificable"), "no se filtra la clave técnica al usuario");
assert.ok(renderedReview.includes("&lt;contenido&gt; y &amp; caracteres especiales."), "el resumen se escapa antes de insertarse en HTML");
assert.ok(renderedReview.includes("href=\"https://www.cmfchile.cl/normativa/cir_1234_2026.pdf\""));
assert.ok(renderedReview.includes("PDF, pág. 4"), "se conserva la cita con su página");
assert.ok(renderedReview.includes("normativa-badge-update") === false, "no se muestra una actualización PDF sin revisiones registradas");
const renderedUnassigned = monitor.renderEvent({ ...reviewEvent, sectors: [], review_flags: ["sin_industria_asignada"] });
assert.ok(renderedUnassigned.includes("Industria sin verificar"), "las fichas sin clasificación no inventan una industria");
const renderedFlagWithoutReviewBoolean = monitor.renderEvent({ ...reviewEvent, needs_human_review: false, review_flags: ["vigencia_sin_evidencia_verificable"] });
assert.ok(renderedFlagWithoutReviewBoolean.includes("Revisión humana"), "una marca de revisión no se oculta si falta el indicador redundante");
const renderedPending = monitor.renderEvent({ ...reviewEvent, analysis_status: "pending", needs_human_review: false, review_flags: [] });
assert.ok(renderedPending.includes("Análisis pendiente"));
assert.ok(renderedPending.includes("Esto no significa que la publicación no exista."));

const seventyEight = Array.from({ length: 78 }, (_, index) => ({ id: index + 1 }));
const firstPage = monitor.paginateEvents(seventyEight, 1, 20);
const lastPage = monitor.paginateEvents(seventyEight, 99, 20);
const emptyPage = monitor.paginateEvents([], 1, 20);
assert.equal(firstPage.totalPages, 4);
assert.equal(firstPage.start, 1);
assert.equal(firstPage.end, 20);
assert.equal(firstPage.items.length, 20);
assert.equal(lastPage.page, 4, "el número de página se limita al máximo disponible");
assert.equal(lastPage.start, 61);
assert.equal(lastPage.end, 78);
assert.equal(lastPage.items.length, 18);
assert.equal(emptyPage.totalPages, 1);
assert.equal(emptyPage.start, 0);
assert.equal(emptyPage.end, 0);

const html = fs.readFileSync(htmlPath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");
const sidebar = fs.readFileSync(sidebarPath, "utf8");
const viewer = fs.readFileSync(viewerPath, "utf8");
const viewerWindow = {};
vm.runInNewContext(viewer, {
  window: viewerWindow,
  document: { getElementById() { return null; } }
});

assert.match(html, /id="tab-btn-normativa"[^>]*aria-controls="normativa-container"/);
assert.match(html, />\s*Normativa CMF\s*</);
assert.match(html, /id="normativa-container"/);
assert.match(html, /id="normativa-monitor"/);
assert.match(html, /js\/normativa_monitor\.js\?v=/);
assert.doesNotMatch(html, /tab-btn-soon|soon-container|Próximamente/);
assert.match(html, /activeTab === "normativa"/);
assert.match(html, /window\.switchMainTab\("normativa"\)/);
assert.match(monitorSource, /Publicaciones asociadas/);
assert.match(monitorSource, /Industria activa/);
assert.match(monitorSource, /Sin industria verificada/);
assert.match(monitorSource, /Total del feed/);
assert.match(monitorSource, /Las cifras globales describen todo el feed/);
assert.match(monitorSource, /aria-label="Páginas de publicaciones"/);
assert.match(monitorSource, /PAGE_SIZE = 20/);
assert.match(monitorSource, /data-normativa-page/);
assert.match(css, /\.normativa-summary-row[\s\S]*grid-template-columns: repeat\(4, minmax\(0, 1fr\)\)/);
assert.match(css, /\.normativa-pagination/);
assert.match(css, /@media \(max-width: 600px\)/);
assert.doesNotMatch(monitorSource, /API_GOOGLE_AI_STUDIO|generativelanguage\.googleapis\.com/);
assert.match(sidebar, /mfc:industry-change/);
assert.match(sidebar, /setActiveSector\(sector, "table"\)/);
assert.match(viewer, /sectorForView\(viewName\)/);
assert.equal(viewerWindow.DataViewer.sectorForView("ffmm_maestro"), "ffmm");
assert.equal(viewerWindow.DataViewer.sectorForView("ccaf_balance"), "cajas_compensacion");
assert.equal(viewerWindow.DataViewer.sectorForView("afp_maestro"), "afp_corporativo");
assert.equal(viewerWindow.DataViewer.sectorForView("bancos_cmf_balance"), "bancos");

assert.equal(feed.schema_version, 1);
assert.ok(Array.isArray(feed.events));
assert.equal(feed.events.length, feed.run_summary.listed_records, "el total global coincide con las fichas del feed");
assert.equal(feed.run_summary.unassigned_records, feed.events.filter((event) => !event.sectors || event.sectors.length === 0).length);
const reviewedCircular2372 = feed.events.find((event) => event.id === "cmf-875e5371629ea44e7089");
if (reviewedCircular2372) {
  assert.deepEqual(reviewedCircular2372.sectors, ["bancos", "cooperativas", "sistemas_pago"]);
  assert.equal(reviewedCircular2372.needs_human_review, true, "la revisión de industria no elimina la revisión pendiente de vigencia");
  assert.ok(reviewedCircular2372.review_flags.includes("vigencia_sin_evidencia_verificable"));
  assert.ok(!reviewedCircular2372.review_flags.includes("sin_industria_asignada"));
  for (const sector of reviewedCircular2372.sectors) {
    assert.ok(monitor.filterEventsBySector(feed.events, sector).some((event) => event.id === reviewedCircular2372.id));
  }
  assert.ok(!monitor.filterEventsBySector(feed.events, "fi").some((event) => event.id === reviewedCircular2372.id));
}
for (const event of feed.events) {
  assert.ok(event.id, "cada publicación tiene un identificador estable");
  assert.ok(!event.document_url || /^https:\/\/www\.cmfchile\.cl\//i.test(event.document_url), `${event.id}: enlace oficial CMF`);
  assert.ok(!event.source_url || /^https:\/\/www\.cmfchile\.cl\//i.test(event.source_url), `${event.id}: fuente oficial CMF`);
  const rendered = monitor.renderEvent(event);
  assert.ok(rendered.includes('<article class="normativa-event"'), `${event.id}: la ficha se renderiza`);
  for (const flag of event.review_flags || []) {
    assert.ok(!rendered.includes(flag), `${event.id}: no se expone la clave técnica ${flag}`);
    assert.ok(rendered.includes(monitor.formatReviewFlag(flag)), `${event.id}: ${flag} aparece en lenguaje legible`);
  }
}

setTimeout(() => {
  const ffmmCount = monitor.filterEventsBySector(feed.events, "ffmm").length;
  const assertMetric = (html, value, label, scope) => {
    const valueAt = html.indexOf(`<strong>${value}</strong>`);
    const labelAt = html.indexOf(`<span>${label}</span>`, valueAt);
    const scopeAt = html.indexOf(`<small>${scope}</small>`, labelAt);
    assert.ok(valueAt >= 0 && labelAt > valueAt && labelAt - valueAt < 250 && scopeAt > labelAt && scopeAt - labelAt < 100, `${label}: valor ${value} y alcance ${scope}`);
  };
  assertMetric(fakeContainer.innerHTML, ffmmCount, "Publicaciones asociadas", "Industria activa");
  assert.match(fakeContainer.innerHTML, /Las cifras globales describen todo el feed/);
  assert.match(fakeTimeline.innerHTML, new RegExp(`Mostrando <strong>1–${Math.min(20, ffmmCount)}</strong> de <strong>${ffmmCount}</strong> publicaciones`));

  fakeWindow.dispatchEvent({ type: "mfc:industry-change", detail: { sector: "todos", source: "audit" } });
  const total = feed.events.length;
  const totalPages = Math.max(1, Math.ceil(total / 20));
  const unassigned = feed.events.filter((event) => !Array.isArray(event.sectors) || event.sectors.length === 0).length;
  const pending = feed.events.filter((event) => event.analysis_status !== "complete").length;
  const humanReview = feed.events.filter((event) => event.analysis_status === "complete" && event.needs_human_review).length;
  assert.match(fakeContainer.innerHTML, /Todas las industrias/);
  assertMetric(fakeContainer.innerHTML, unassigned, "Sin industria verificada", "Total del feed");
  assertMetric(fakeContainer.innerHTML, pending, "Análisis pendiente", "Total del feed");
  assertMetric(fakeContainer.innerHTML, humanReview, "Análisis completo con revisión humana", "Total del feed");
  assert.match(fakeTimeline.innerHTML, new RegExp(`Mostrando <strong>1–${Math.min(20, total)}</strong> de <strong>${total}</strong> publicaciones`));
  if (totalPages > 1) {
    const firstPageCards = (fakeTimeline.innerHTML.match(/<article class="normativa-event"/g) || []).length;
    assert.equal(firstPageCards, 20, "el renderizador muestra solo 20 fichas por página");
    assert.ok(fakeTimeline.innerHTML.includes(`Página <strong>1</strong> de ${totalPages}`));
    const nextButton = fakeTimeline.buttons.find((button) => button.dataset.normativaPage === "2");
    assert.ok(nextButton, "la paginación renderiza el control para avanzar");
    nextButton.click();
    assert.ok(fakeTimeline.innerHTML.includes(`Página <strong>2</strong> de ${totalPages}`), "el botón avanza a la página siguiente");
    assert.equal((fakeTimeline.innerHTML.match(/<article class="normativa-event"/g) || []).length, 20);
  }
  console.log("AUDITORÍA WEB NORMATIVA OK: sincronización con el explorador, separación de métricas, renderizado, revisión humana, citas oficiales y paginación.");
}, 0);

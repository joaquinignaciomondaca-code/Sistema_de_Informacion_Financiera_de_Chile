#!/usr/bin/env node
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const monitorPath = "docs/js/normativa_monitor.js";
const htmlPath = "docs/index.html";
const sidebarPath = "docs/js/sidebar.js";
const viewerPath = "docs/js/data_viewer.js";
const feedPath = "docs/outputs/normativa_cmf/feed.json";

const monitorSource = fs.readFileSync(monitorPath, "utf8");
const industryListeners = {};
const fakeContainer = { innerHTML: "", querySelector() { return null; } };
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
  fetch() { return new Promise(() => {}); }
});

const monitor = fakeWindow.NormativaMonitor;
assert.ok(monitor, "El módulo expone window.NormativaMonitor");
monitor.init();
fakeWindow.dispatchEvent({ type: "mfc:industry-change", detail: { sector: "ffmm", source: "test" } });
assert.equal(monitor.activeSector, "ffmm", "la vista sigue el cambio de industria del explorador");
const events = [
  { id: "ffmm-a", sectors: ["ffmm"] },
  { id: "insurance-a", sectors: ["seguros"] },
  { id: "cross-sector", sectors: ["ffmm", "agf"] },
  { id: "unassigned", sectors: [] }
];
assert.deepEqual(
  monitor.filterEventsBySector(events, "ffmm").map((event) => event.id).sort(),
  ["cross-sector", "ffmm-a"]
);
assert.deepEqual(
  monitor.filterEventsBySector(events, "seguros").map((event) => event.id),
  ["insurance-a"]
);
assert.deepEqual(
  monitor.filterEventsBySector(events, "afp_corporativo"),
  []
);
assert.equal(monitor.normalizeSector("afp_corporativo"), "pensiones");
assert.equal(monitor.filterEventsBySector(events, "todos").length, 4);

const html = fs.readFileSync(htmlPath, "utf8");
const sidebar = fs.readFileSync(sidebarPath, "utf8");
const viewer = fs.readFileSync(viewerPath, "utf8");
const feed = JSON.parse(fs.readFileSync(feedPath, "utf8"));
const viewerWindow = {};
vm.runInNewContext(viewer, {
  window: viewerWindow,
  document: { getElementById() { return null; } }
});
assert.match(html, /id="normativa-monitor"/);
assert.match(html, /js\/normativa_monitor\.js\?v=/);
assert.match(monitorSource, /Última revisión de la fuente/);
assert.match(monitorSource, /Última novedad detectada/);
assert.match(monitorSource, /last_detected_at/);
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

console.log("AUDITORÍA WEB NORMATIVA OK: filtro automático por industria, alias AFP, feed y conexión de navegación.");

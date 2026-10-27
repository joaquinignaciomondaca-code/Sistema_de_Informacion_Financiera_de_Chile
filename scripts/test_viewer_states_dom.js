// Estados reales del Visor con respuestas sintéticas, sin DuckDB ni red.
const assert = require('node:assert/strict');
const fs = require('node:fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch { ({ JSDOM } = require('/tmp/node_modules/jsdom')); }
const dom = new JSDOM('<main id="data-viewer-container"></main>', { runScripts: 'outside-only', url: 'https://sif.test/' });
const { window } = dom;
window.eval(fs.readFileSync('docs/js/data_viewer.js', 'utf8'));
const viewer = window.DataViewer;
const doc = window.document;
const container = viewer.container;
const sinPublicar = () => ({ success: false, noPublishedData: true, error: 'Sin archivos publicados' });
(async () => {
  window.DuckDBClient = { query: async () => sinPublicar() };
  await viewer.loadTable('fi_bienes_raices', 'Bienes raíces');
  assert.equal(container.querySelector('.dv-error-state'), null);
  assert.match(container.textContent, /no permite concluir que las instituciones no hayan reportado/);
  assert.equal(container.querySelector('.dv-info-notice').hidden, false);
  container.querySelector('.dv-notice-close').click();
  assert.equal(container.querySelector('.dv-info-notice').hidden, true);
  assert.equal(doc.activeElement, container.querySelector('.dv-notice-reopen'));
  await viewer.loadTable('fi_bienes_raices', 'Bienes raíces');
  assert.equal(container.querySelector('.dv-info-notice').hidden, true);
  container.querySelector('.dv-notice-reopen').click();
  assert.equal(container.querySelector('.dv-info-notice').hidden, false);
  assert.equal(doc.activeElement, container.querySelector('.dv-notice-close'));
  container.querySelector('.dv-notice-close').click();
  await viewer.loadTable('otra_sin_publicacion', 'Otra tabla');
  assert.equal(container.querySelector('.dv-info-notice').hidden, false);

  const sqls = [];
  window.DuckDBClient.query = async sql => { sqls.push(sql); throw new Error('Fallo <em>simulado</em>'); };
  await viewer.loadTable('seguros_lista_entidades', 'Aseguradoras', 250);
  assert.equal(container.querySelector('.dv-info-notice'), null);
  assert.match(container.querySelector('.dv-error-state').textContent, /Fallo <em>simulado<\/em>/);
  assert.equal(container.querySelector('.dv-error-state em'), null);
  let terminar;
  window.DuckDBClient.query = sql => { sqls.push(sql); return new Promise(resolve => { terminar = resolve; }); };
  container.querySelector('.dv-retry').click();
  assert.equal(viewer.isLoading, true);
  assert.ok(container.querySelector('.dv-loading-state[role="status"]'));
  assert.equal(sqls.at(-1), 'SELECT * FROM seguros_lista_entidades LIMIT 250;');
  terminar({ success: true, columns: ['valor'], rows: [{ valor: 0 }] });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(viewer.isLoading, false);
  assert.equal(viewer.currentRows[0].valor, 0);
  assert.equal(container.querySelector('.dv-info-notice'), null);
  assert.equal(container.querySelector('.dv-error-state'), null);
  assert.equal(container.querySelector('tbody td').textContent.trim(), '0');

  window.DuckDBClient.query = async () => ({ success: true, columns: ['valor'], rows: [] });
  await viewer.loadTable('seguros_lista_entidades', 'Aseguradoras');
  assert.equal(viewer.currentRows.length, 0);
  assert.equal(container.querySelector('.dv-info-notice'), null);
  assert.equal(container.querySelector('.dv-error-state'), null);

  // Una respuesta vieja no puede sustituir el estado de la selección nueva.
  let responderAntigua;
  window.DuckDBClient.query = () => new Promise(resolve => { responderAntigua = resolve; });
  const antigua = viewer.loadTable('tabla_antigua', 'Antigua');
  window.DuckDBClient.query = async () => sinPublicar();
  await viewer.loadTable('tabla_nueva', 'Nueva');
  responderAntigua({ success: true, rows: [{ valor: 99 }], columns: ['valor'] });
  await antigua;
  assert.equal(viewer.currentView, 'tabla_nueva');
  assert.equal(container.querySelector('.dv-info-notice').hidden, false);
  assert.equal(viewer.currentRows.length, 0);

  window.ESTADO_CLAVES = { objetos: { tabla_nueva: { sobrantes: 1, filas: 10000, pct_repetidas: 0.01 } } };
  const aviso = doc.createElement('div');
  aviso.innerHTML = viewer.avisoClaves();
  assert.ok(aviso.querySelector('[role="note"]'));
  assert.equal(aviso.querySelector('[role="alert"]'), null);
  assert.match(aviso.textContent, /Observación sobre la fuente/);
  assert.match(aviso.textContent, /Se conservan para mantener la fidelidad/);
  assert.match(aviso.textContent, /0,010 %/);
  console.log('OK DOM: sin publicación ≠ fallo ≠ cero; aviso cerrable por tabla; reintento y carga; respuesta antigua ignorada; repeticiones como observación.');
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => dom.window.close());

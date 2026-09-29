#!/usr/bin/env python3
"""Comprueba la taxonomía de navegación sin requerir Parquet ni red.

Se apoya en Node/V8 para evaluar los catálogos JS, no en expresiones regulares
que pueden omitir categorías anidadas. No descarga ni modifica datos.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const industryEvents = [];
class CustomEvent { constructor(type, options = {}) { this.type = type; this.detail = options.detail || {}; } }
const context = {
  window: { dispatchEvent: event => industryEvents.push(event) },
  document: { getElementById: () => null, querySelectorAll: () => [] },
  CustomEvent
};
vm.createContext(context);
for (const file of ['sidebar.js', 'data_viewer.js']) {
  vm.runInContext(fs.readFileSync('docs/js/' + file, 'utf8'), context);
}
const tree = vm.runInContext('EXPLORER_TREE', context);
const viewer = vm.runInContext('DATA_VIEWER_CATALOG', context);
const byGroup = Object.fromEntries(tree.map(g => [g.id, g]));
assert.equal(Object.keys(byGroup).length, tree.length, 'grupo duplicado');
assert.deepEqual(Array.from(byGroup.group_securitizacion.children, s => s.sector),
  ['securitizadoras', 'patrimonios_separados']);
assert.deepEqual(Array.from(byGroup.group_administracion_fondos.children, s => s.sector),
  ['agf', 'ffmm', 'fi']);
const expected = new Map();
const circularIds = new Set();
for (const group of tree) for (const sector of group.children) {
  assert.equal(sector.type, 'sector');
  for (const category of sector.children) {
    assert.equal(category.sector, sector.sector, category.id);
    assert(!circularIds.has(category.id), 'categoría duplicada: ' + category.id);
    circularIds.add(category.id);
    for (const table of category.tables) {
      assert(!expected.has(table.id), 'tabla duplicada: ' + table.id);
      expected.set(table.id, table.file || table.files);
      // Una tabla puede publicarse como particiones (varias rutas) cuando el
      // Parquet consolidado supera el límite de GitHub: todas deben existir.
      for (const file of [table.file, ...(table.files || [])]) {
        if (file && file !== '#') {
          assert(fs.existsSync('docs/' + file), 'archivo ausente: ' + file);
        }
      }
    }
  }
}
const options = viewer.flatMap(group => group.tables.map(table => table.id));
assert.equal(new Set(options).size, options.length, 'opciones duplicadas en visor');
for (const id of options) assert(expected.has(id), 'opción no encontrada en sidebar: ' + id);

// Factoring/Leasing: lista de entidades + serie completa (balance y resultados en
// carpetas separadas). Las muestras cotejadas de 2 filas repetían cifras de la
// serie y se retiraron de la web (sus Parquet quedan como respaldo de auditoría).
const fl = byGroup.group_factoring_leasing.children[0];
const hasFullSeries = fs.existsSync('docs/outputs/factoring_leasing/factoring_leasing_balance_serie_ifrs_cmf.parquet') &&
  fs.existsSync('docs/outputs/factoring_leasing/factoring_leasing_resultados_serie_ifrs_cmf.parquet');
const expectedFolders = ['cat_factoring_leasing_lista_entidades'];
const expectedSeriesTables = [];
if (hasFullSeries) {
  expectedFolders.push('cat_factoring_leasing_balance', 'cat_factoring_leasing_resultados');
  expectedSeriesTables.push('factoring_leasing_balance', 'factoring_leasing_resultados');
}
assert.deepEqual(Array.from(fl.children, c => c.id), expectedFolders);
const tableForFolder = Object.fromEntries(fl.children.filter(c => c.type === 'circular')
  .map(c => [c.id, c.tables[0].id]));
assert.equal(Object.keys(tableForFolder).length, fl.children.length);
if (hasFullSeries) {
  assert.deepEqual(tableForFolder.cat_factoring_leasing_balance, 'factoring_leasing_balance');
  assert.deepEqual(tableForFolder.cat_factoring_leasing_resultados, 'factoring_leasing_resultados');
  // "Ganancia (pérdida)" se repite hasta 3 veces por estado: debe existir el chip que elige una fila.
  const flResults = fl.children.find(c => c.id === 'cat_factoring_leasing_resultados');
  assert(flResults.chips.some(c => /repeticion_contexto = 1/.test(c.query) && /'ERFG', 'ERNG'/.test(c.query)),
    'falta chip de utilidad del período sin repeticiones');
}
const expectedViewerTables = ['factoring_leasing_lista_entidades', ...expectedSeriesTables];
assert.deepEqual(Array.from(viewer.find(g => g.group.startsWith('Factoring y Leasing')).tables, t => t.id), expectedViewerTables);
// Verificar el HTML real del explorador y qué tabla se abre al pulsar cada carpeta.
const SidebarController = vm.runInContext('SidebarController', context);
const sidebar = Object.create(SidebarController.prototype);
sidebar.treeContainer = { innerHTML: '' };
sidebar.selectedTableId = null;
sidebar.expandedNodes = new Set();
sidebar.bindTreeEvents = () => {};
sidebar.render();
const flHtml = sidebar.treeContainer.innerHTML.split('data-group-id="group_factoring_leasing"')[1]
  .split('data-group-id="group_corredoras_bolsa"')[0];
for (const id of expectedFolders) {
  assert(flHtml.includes(`data-node-id="${id}"`), 'carpeta invisible: ' + id);
}
for (const id of ['fl_balance_muestra_cmf_folder', 'fl_resultados_muestra_cmf_folder',
                  'factoring_leasing_eeff_muestra_cmf', 'factoring_leasing_resultados_muestra_cmf']) {
  assert(!flHtml.includes(id), 'muestra retirada reaparece: ' + id);
}
const opened = [];
sidebar.onTableSelect = (id) => opened.push(id);
for (const id of expectedFolders) sidebar.onCircularSelect(id, 'factoring_leasing');
assert.deepEqual(opened, ['factoring_leasing_lista_entidades', ...expectedSeriesTables]);
assert(industryEvents.some(event => event.type === 'mfc:industry-change' && event.detail.sector === 'factoring_leasing'),
  'al seleccionar una tabla/carpeta debe notificarse la industria activa');
context.window.DataViewer = { loadTable() {} };
const selectedTable = Object.create(SidebarController.prototype);
selectedTable.selectedTableId = null;
selectedTable.breadcrumbEl = null;
selectedTable.onTableSelect('ffmm_lista_entidades', 'ffmm.lista_entidades', '', 'ffmm');
assert(industryEvents.some(event => event.type === 'mfc:industry-change' &&
  event.detail.sector === 'ffmm' && event.detail.source === 'table'),
  'al seleccionar una tabla FFMM debe publicarse exactamente la industria FFMM');

// AFP: sólo identidad sin métricas generadas. Bancos: identidad + líneas
// CMF B1/B2 y R1 publicadas por partición mensual validada. El REPO legado
// (bancos_repos_saldos_series) fue retirado y no debe reaparecer.
const pensiones = byGroup.group_pensiones;
const bancos = byGroup.group_bancos;
assert.deepEqual(Array.from(pensiones.children, s => s.sector), ['afp_corporativo']);
assert.deepEqual(Array.from(pensiones.children[0].children, c => c.id), ['cat_afp_lista_entidades']);
assert.deepEqual(Array.from(bancos.children[0].children, c => c.id),
  ['cat_bancos_lista_entidades', 'cat_bancos_balance', 'cat_bancos_resultados']);
assert.equal(pensiones.status, 'active');
for (const c of bancos.children[0].children.slice(1)) {
  assert.equal(c.status, 'active', 'carpeta CMF bancaria no activa: ' + c.id);
  assert.deepEqual(Array.from(c.tables[0].files), ['outputs/bancos/cmf_b1_b2_r1/manifest.json']);
}
assert.deepEqual(Array.from(viewer.find(g => g.group.startsWith('Fondos de Pensiones')).tables, t => t.id), ['afp_lista_entidades']);
assert.deepEqual(Array.from(viewer.find(g => g.group.startsWith('Banca (CMF)')).tables, t => t.id),
  ['bancos_lista_entidades', 'bancos_balance', 'bancos_resultados']);
assert(!expected.has('bancos_repos_saldos_series'), 'REPO bancario retirado todavía visible');
assert(!pensiones.badges.some(b => b.text.includes('Falta validar')));
for (const id of ['afp_cartera_bonos','afp_cartera_acciones','afp_derivados_swaps','afp_derivados_forwards',
                 'bancos_balance_resumen','bancos_estado_resultados','bancos_derivados_posicion_vigente',
                 'bancos_derivados_flujos_transados']) {
  assert(!expected.has(id), 'tabla retirada todavía visible: ' + id);
}
const restrictedFiles = ['duckdb_client.js', 'downloads_panel.js', 'data_dictionary.js', 'erd_graph.js', 'index.html'];
for (const file of restrictedFiles) {
  const text = fs.readFileSync('docs/' + (file.endsWith('.js') ? 'js/' : '') + file, 'utf8');
  for (const id of ['afp_cartera_bonos','afp_cartera_acciones','afp_derivados_swaps','afp_derivados_forwards',
                    'bancos_balance_resumen','bancos_estado_resultados','bancos_derivados_posicion_vigente',
                    'bancos_derivados_flujos_transados','bancos_colocaciones',
                    'vida_bonos','vida_acciones','vida_maestro','vida_forwards','vida_swaps','vida_repos','vida_solvencia',
                    'generales_bonos','generales_acciones','generales_maestro','generales_repos','generales_solvencia',
                    'outputs/vida/','outputs/generales/',
                    'ffmm_futu_normalizado','ffmm_opci_normalizado','ffmm_inversiones_nac','ffmm_repos_detalle_historico',
                    'ffmm_eeff_xml_muestra_cmf','fi_eeff_xml_muestra_cmf','ffmm_registro_fondos_universo',
                    'fi_nacional','fi_extranjera','fi_derivados','fi_metodo_part"','fi_repos','fi_registro_fondos_universo"',
                    'fi_cartera_nacional.parquet','fi_futuros_forward']) {
    assert(!text.includes(id), file + ' expone tabla retirada: ' + id);
  }
}
const bundleContext = { window: {} };
vm.createContext(bundleContext);
vm.runInContext(fs.readFileSync('docs/js/data_bundles.js', 'utf8'), bundleContext);
assert.deepEqual(Array.from(Object.keys(bundleContext.window.DATA_BUNDLES)
  .filter(k => k.startsWith('afp_') || k.startsWith('bancos_')).sort()),
  ['afp_lista_entidades', 'bancos_lista_entidades']);
const afpKeys = Object.keys(bundleContext.window.DATA_BUNDLES.afp_lista_entidades[0]).sort();
assert.deepEqual(afpKeys, ['id', 'nombre_administradora', 'nombre_fantasia', 'rut_administradora']);

// --- Vocabulario canónico (docs/vocabulario.json) ----------------------------
// Cada sector abre con una carpeta "Lista de Entidades" (badge de tipo entities)
// que contiene sólo la lista de entidades del sector; su nodo se llama
// cat_<tabla_id>. No hay sectores sin lista de entidades salvo macro, que son
// series estadísticas.
const SIN_LISTA_ENTIDADES = ['macro'];
const BADGE_TYPES = ['entities', 'data', 'roadmap'];
for (const group of tree) for (const sector of group.children) {
  for (const category of sector.children) {
    assert(BADGE_TYPES.includes(category.badgeType),
      'badgeType no soportado por el render: ' + category.id + ' -> ' + category.badgeType);
  }
  const carpetasEntidades = sector.children.filter(c => c.label === 'Lista de Entidades');
  if (SIN_LISTA_ENTIDADES.includes(sector.sector)) {
    assert.equal(carpetasEntidades.length, 0,
      'sector sin lista de entidades no debe declarar esa carpeta: ' + sector.sector);
    continue;
  }
  assert.equal(carpetasEntidades.length, 1,
    'el sector debe tener exactamente una carpeta Lista de Entidades: ' + sector.sector);
  const entidades = sector.children[0];
  assert.equal(entidades.label, 'Lista de Entidades',
    'Lista de Entidades debe ser el primer nodo del sector: ' + sector.sector);
  assert.equal(entidades.badgeType, 'entities', 'badge incorrecto en ' + sector.sector);
  assert.equal(entidades.tables.length, 1,
    'Lista de Entidades debe contener sólo la lista de entidades: ' + sector.sector);
  assert(/\.lista_entidades$|\.lista_entidades_registro$/.test(entidades.tables[0].name),
    'Lista de Entidades debe apuntar a la lista de entidades canónica: ' + sector.sector + ' -> ' + entidades.tables[0].name);
}
console.log(`Navegación OK: ${tree.length} familias, ${expected.size} tablas, ${options.length} opciones del visor.`);
console.log(`Catálogo de entidades normalizado en ${tree.reduce((n, g) => n + g.children.length, 0) - SIN_LISTA_ENTIDADES.length} sectores.`);
"""


if __name__ == '__main__':
    subprocess.run(['node', '-e', CHECK], cwd=ROOT, check=True)

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
const context = { window: {}, document: { getElementById: () => null } };
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

// AFP: sólo identidad sin métricas generadas. Bancos: identidad y REPO,
// mantenido expresamente como excepción con advertencia de auditoría.
const pensiones = byGroup.group_pensiones;
const bancos = byGroup.group_bancos;
assert.deepEqual(Array.from(pensiones.children, s => s.sector), ['afp_corporativo']);
assert.deepEqual(Array.from(pensiones.children[0].children, c => c.id), ['cat_afp_maestro']);
assert.deepEqual(Array.from(bancos.children[0].children, c => c.id),
  ['cat_bancos_maestro', 'circ_bancos_repos']);
assert.equal(pensiones.status, 'active');
assert.equal(bancos.status, 'active');
assert.equal(bancos.children[0].children[1].status, 'por_auditar');
assert.deepEqual(Array.from(viewer.find(g => g.group.startsWith('Fondos de Pensiones')).tables, t => t.id), ['afp_maestro']);
assert.deepEqual(Array.from(viewer.find(g => g.group.startsWith('Banca Comercial')).tables, t => t.id),
  ['bancos_maestro', 'bancos_repos_saldos_series']);
assert(!pensiones.badges.some(b => b.text.includes('Falta validar')));
for (const id of ['afp_cartera_bonos','afp_cartera_acciones','afp_derivados_swaps','afp_derivados_forwards',
                 'bancos_balance_resumen','bancos_estado_resultados','bancos_derivados_posicion_vigente',
                 'bancos_derivados_flujos_transados']) {
  assert(!expected.has(id), 'tabla retirada todavía visible: ' + id);
}
const restrictedFiles = ['duckdb_client.js', 'export_modal.js', 'data_dictionary.js', 'erd_graph.js', 'index.html'];
for (const file of restrictedFiles) {
  const text = fs.readFileSync('docs/' + (file.endsWith('.js') ? 'js/' : '') + file, 'utf8');
  for (const id of ['afp_cartera_bonos','afp_cartera_acciones','afp_derivados_swaps','afp_derivados_forwards',
                    'bancos_balance_resumen','bancos_estado_resultados','bancos_derivados_posicion_vigente',
                    'bancos_derivados_flujos_transados','bancos_colocaciones']) {
    assert(!text.includes(id), file + ' expone tabla retirada: ' + id);
  }
}
const bundleContext = { window: {} };
vm.createContext(bundleContext);
vm.runInContext(fs.readFileSync('docs/js/data_bundles.js', 'utf8'), bundleContext);
assert.deepEqual(Array.from(Object.keys(bundleContext.window.DATA_BUNDLES)
  .filter(k => k.startsWith('afp_') || k.startsWith('bancos_')).sort()),
  ['afp_maestro', 'bancos_maestro']);
const afpKeys = Object.keys(bundleContext.window.DATA_BUNDLES.afp_maestro[0]).sort();
assert.deepEqual(afpKeys, ['id', 'nombre_administradora', 'nombre_fantasia', 'rut_administradora']);

// --- Normalización del catálogo de entidades ---------------------------------
// Estándar: cada sector abre con una carpeta "Lista de Entidades" (badge de tipo
// entities) que contiene sólo la tabla maestra del sector. Las excepciones son
// sectores sin maestra propia: macro (series estadísticas).
const SIN_MAESTRA = ['macro'];
const BADGE_TYPES = ['entities', 'data', 'roadmap'];
for (const group of tree) for (const sector of group.children) {
  for (const category of sector.children) {
    assert(BADGE_TYPES.includes(category.badgeType),
      'badgeType no soportado por el render: ' + category.id + ' -> ' + category.badgeType);
  }
  const carpetasEntidades = sector.children.filter(c => c.label === 'Lista de Entidades');
  if (SIN_MAESTRA.includes(sector.sector)) {
    assert.equal(carpetasEntidades.length, 0,
      'sector sin tabla maestra no debe declarar Lista de Entidades: ' + sector.sector);
    continue;
  }
  assert.equal(carpetasEntidades.length, 1,
    'el sector debe tener exactamente una carpeta Lista de Entidades: ' + sector.sector);
  const entidades = sector.children[0];
  assert.equal(entidades.label, 'Lista de Entidades',
    'Lista de Entidades debe ser el primer nodo del sector: ' + sector.sector);
  assert.equal(entidades.badgeType, 'entities', 'badge incorrecto en ' + sector.sector);
  assert.equal(entidades.tables.length, 1,
    'Lista de Entidades debe contener sólo la tabla maestra: ' + sector.sector);
  assert(/_maestro$/.test(entidades.tables[0].id),
    'Lista de Entidades debe apuntar a la tabla maestra: ' + sector.sector + ' -> ' + entidades.tables[0].id);
}
console.log(`Navegación OK: ${tree.length} familias, ${expected.size} tablas, ${options.length} opciones del visor.`);
console.log(`Catálogo de entidades normalizado en ${tree.reduce((n, g) => n + g.children.length, 0) - SIN_MAESTRA.length} sectores.`);
"""


if __name__ == '__main__':
    subprocess.run(['node', '-e', CHECK], cwd=ROOT, check=True)

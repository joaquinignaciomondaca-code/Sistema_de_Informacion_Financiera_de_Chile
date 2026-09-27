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
      expected.set(table.id, table.file);
      // Incidencia previa a esta reorganización: vida_bonos apunta al Parquet
      // consolidado excluido por .gitignore; el sidebar ofrece sus particiones.
      if (table.file !== '#' && table.id !== 'vida_bonos') {
        assert(fs.existsSync('docs/' + table.file), 'archivo ausente: ' + table.file);
      }
    }
  }
}
const options = viewer.flatMap(group => group.tables.map(table => table.id));
assert.equal(new Set(options).size, options.length, 'opciones duplicadas en visor');
for (const id of options) assert(expected.has(id), 'opción no encontrada en sidebar: ' + id);
console.log(`Navegación OK: ${tree.length} familias, ${expected.size} tablas, ${options.length} opciones del visor.`);
"""


if __name__ == '__main__':
    subprocess.run(['node', '-e', CHECK], cwd=ROOT, check=True)

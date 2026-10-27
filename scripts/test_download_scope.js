// Alcance de exportación: contratos SQL/texto y captura de controles al hacer clic.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const item = { id: 'macro_prueba', cobertura: 'Una observación por día', periodo: { desde: '2020-01', hasta: '2026-10' }, filas: 10 };
const sinPeriodo = { id: 'entidades_prueba', cobertura: 'Una fila por entidad', filas: 3 };
const descargas = [];
const window = { DOWNLOAD_CATALOG: { grupos: [{ items: [item, sinPeriodo] }] }, MFCDownload: {
  numero: String,
  exportarFilas: async (rows, cols, options) => { descargas.push({ rows, cols, options }); return { filas: rows.length, comprimido: false }; }
} };
vm.runInNewContext(fs.readFileSync('docs/js/downloads_panel.js', 'utf8'), { window, document: { addEventListener() {} }, console });
const panel = window.DownloadsPanel;
const avisos = [];
panel.avisar = texto => avisos.push(texto);
panel.recorte = { activo: true, desde: 2022, hasta: 2024 };
assert.match(panel.resumenExportacion(item), /años 2022–2024/);
assert.match(panel.resumenExportacion(item), /Parquet: archivos originales/);
assert.match(panel.sqlSerie(item), /periodo >= '2022-01' AND periodo <= '2024-12'/);
assert.equal(panel.sqlSerie(sinPeriodo), 'SELECT * FROM entidades_prueba');
assert.match(panel.resumenExportacion(sinPeriodo), /no admite recorte/);
panel.frecuencias = new Map([[item.id, 'mensual']]);
assert.match(panel.resumenExportacion(item), /cierre mensual, no suma mensual/);
const mensual = panel.sqlSerieMensual(item, ['valor']);
assert.match(mensual, /arg_max\(valor, fecha\)/);
assert.doesNotMatch(mensual, /sum\(/i);
panel.recorte = { activo: true, desde: 2025, hasta: 2022 };
assert.throws(() => panel.sqlSerie(item), /año inicial/);
assert.equal(panel.errorRecorte(sinPeriodo), '');
(async () => {
  let consultas = 0;
  window.DuckDBClient = { engineAvailable: true, query: async () => { consultas++; } };
  await panel.exportarSerie(item.id, 'csv', null);
  assert.equal(consultas, 0);
  assert.equal(descargas.length, 0);
  assert.match(avisos.at(-1), /año inicial/);
  panel.recorte = { activo: true, desde: 2022, hasta: 2024 };
  panel.frecuencias.set(item.id, 'diaria');
  const sqls = [];
  const motor = window.DuckDBClient = {
    engineAvailable: false,
    ensureStarted: async () => {
      // El usuario mueve controles mientras se prepara el motor.
      panel.recorte = { activo: true, desde: 2025, hasta: 2026 };
      panel.frecuencias.set(item.id, 'mensual');
      motor.engineAvailable = true;
    },
    query: async sql => { sqls.push(sql); return { success: true, rows: [{ valor: 7 }], columns: ['valor'] }; }
  };
  await panel.exportarSerie(item.id, 'csv', null);
  assert.equal(sqls.length, 1);
  assert.match(sqls[0], /2022-01/);
  assert.match(sqls[0], /2024-12/);
  assert.doesNotMatch(sqls[0], /arg_max/);
  assert.equal(descargas.length, 1);
  console.log('OK: rango inválido no consulta; sin período no recorta; cierre no suma; exportación conserva años/frecuencia del clic.');
})().catch(error => { console.error(error); process.exitCode = 1; });

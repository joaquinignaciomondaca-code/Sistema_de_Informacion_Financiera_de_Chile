// Exportaciones reales con filas sintéticas y las bibliotecas ya incluidas en docs/.
// Sin red, DuckDB, archivos privados ni cambios en los datos publicados.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const XLSX = require('../docs/js/xlsx.full.min.js');
const JSZip = require('../docs/js/jszip.min.js');
const window = { XLSX, JSZip };
let blobActual;
const descargas = [];
const document = {
  body: { appendChild() {} },
  createElement() {
    return { click() { descargas.push({ nombre: this.download, blob: blobActual }); }, remove() {} };
  }
};
vm.runInNewContext(fs.readFileSync('docs/js/download_utils.js', 'utf8'), {
  window, document, Blob,
  URL: { createObjectURL(blob) { blobActual = blob; return 'blob:prueba'; }, revokeObjectURL() {} },
  setTimeout() {}
});
const utils = window.MFCDownload;
async function ultima() { return descargas[descargas.length - 1]; }
async function filasExcel(bytes) {
  const libro = XLSX.read(bytes, { type: 'buffer' });
  return XLSX.utils.sheet_to_json(libro.Sheets[libro.SheetNames[0]], { header: 1 });
}
(async () => {
  const filas = [{ id: 1, texto: 'Compañía; "Chile"', valor: 0 }, { id: 2, texto: 'Seguros', valor: null }];
  const cols = ['id', 'texto', 'valor'];
  const resumen = await utils.exportarFilas(filas, cols, { formato: 'csv', nombre: 'prueba' });
  assert.equal(resumen.filas, 2);
  const csvBlob = (await ultima()).blob;
  assert.equal(Buffer.from(await csvBlob.arrayBuffer()).subarray(0, 3).toString('hex'), 'efbbbf');
  const csv = await csvBlob.text();
  assert.ok(csv.includes('"Compañía; ""Chile"""'));
  assert.ok(csv.includes('"1";"Compañía; ""Chile""";"0"'));
  assert.ok(csv.includes('"2";"Seguros";""'));
  assert.ok((await ultima()).nombre.endsWith('.csv'));
  await utils.exportarFilas(filas, cols, { formato: 'xlsx', nombre: 'prueba' });
  const excel = await filasExcel(Buffer.from(await (await ultima()).blob.arrayBuffer()));
  assert.deepEqual(excel[0], cols);
  assert.equal(excel.length, filas.length + 1);
  assert.equal(excel[1][1], filas[0].texto);
  assert.equal(excel[1][2], 0);
  // >250.000 registros: verificar cada parte CSV, orden y total sin truncamiento.
  const grandes = Array.from({ length: 250001 }, (_, id) => ({ id }));
  const grande = await utils.exportarFilas(grandes, ['id'], { formato: 'csv', nombre: 'grande' });
  assert.equal(grande.comprimido, true);
  assert.equal(grande.archivos, 2);
  let zip = await JSZip.loadAsync(Buffer.from(await (await ultima()).blob.arrayBuffer()));
  let total = 0;
  for (const nombre of Object.keys(zip.files).sort()) {
    const lineas = (await zip.file(nombre).async('string')).replace(/^\uFEFF/, '').split('\n');
    assert.equal(lineas.shift(), '"id"');
    for (const linea of lineas) assert.equal(linea, `"${total++}"`);
  }
  assert.equal(total, grandes.length);
  // Excel grande se divide antes de alcanzar el límite de filas de una hoja.
  const xgrande = await utils.exportarFilas(grandes.slice(0, 150001), ['id'], { formato: 'xlsx', nombre: 'excel_grande' });
  assert.equal(xgrande.comprimido, true);
  assert.equal(xgrande.archivos, 2);
  zip = await JSZip.loadAsync(Buffer.from(await (await ultima()).blob.arrayBuffer()));
  total = 0;
  for (const nombre of Object.keys(zip.files).sort()) {
    const datos = await filasExcel(await zip.file(nombre).async('nodebuffer'));
    assert.deepEqual(datos.shift(), ['id']);
    assert.ok(datos.length + 1 <= 1048576);
    for (const fila of datos) assert.equal(fila[0], total++);
  }
  assert.equal(total, 150001);
  const antes = descargas.length;
  await assert.rejects(utils.exportarFilas([], ['id'], { formato: 'csv' }), /No hay filas/);
  assert.equal(descargas.length, antes);
  console.log('OK: CSV y XLSX reales; 250.001 filas CSV/ZIP y 150.001 XLSX/ZIP íntegros, ordenados y sin truncamiento; vacío no descarga.');
})().catch(error => { console.error(error); process.exitCode = 1; });

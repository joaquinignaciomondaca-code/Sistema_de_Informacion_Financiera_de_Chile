// Prueba DOM de los disparadores reales: sugerencias iniciales/dinámicas y favoritas.
const assert = require('node:assert/strict');
const fs = require('node:fs');
let JSDOM;
try { ({ JSDOM } = require('jsdom')); }
catch { try { ({ JSDOM } = require('/tmp/node_modules/jsdom')); }
catch { console.log('jsdom no está instalado: se omite test_sql_draft_dom.js'); process.exit(0); } }
const dom = new JSDOM(`<textarea id="editor"></textarea><button id="send"></button>
<div id="chips"><button class="chip" data-query="SELECT inicial;">Inicial</button></div>
<div id="saved-queries-modal" class="visible"><ul id="saved-queries-list"></ul></div>
<button id="btn-show-favorites" aria-expanded="true"></button>`, { url: 'http://sif.test/', runScripts: 'outside-only' });
const { window } = dom;
window.eval(fs.readFileSync('docs/js/chat_terminal.js', 'utf8'));
const terminal = Object.create(window.ChatTerminalController.prototype);
terminal.input = window.document.getElementById('editor');
terminal.sendBtn = window.document.getElementById('send');
terminal.chipsContainer = window.document.getElementById('chips');
terminal.history = [];
terminal.addSystemMessage = () => {};
let aceptada = false, ejecutadas = 0;
window.confirm = () => aceptada;
terminal.handleSend = () => ejecutadas++;
terminal.initEvents();
function probarChip(sql) {
  const chip = window.document.querySelector('.chip');
  terminal.input.value = 'SELECT borrador;';
  const antes = ejecutadas;
  aceptada = false;
  chip.click();
  assert.equal(terminal.input.value, 'SELECT borrador;');
  assert.equal(ejecutadas, antes);
  aceptada = true;
  chip.click();
  assert.equal(terminal.input.value, sql);
  assert.equal(ejecutadas, antes + 1);
}
probarChip('SELECT inicial;');
terminal.setCustomChips([{ label: 'Dinámica', query: 'SELECT dinamica;' }], 'Prueba');
probarChip('SELECT dinamica;');
window.localStorage.setItem('mfc_saved_queries', JSON.stringify([{ title: 'Favorita', sql: 'SELECT favorita;' }]));
terminal.renderFavoritesList();
const modal = window.document.getElementById('saved-queries-modal');
terminal.input.value = 'SELECT borrador;';
const antes = ejecutadas;
aceptada = false;
window.document.querySelector('.saved-item').click();
assert.equal(terminal.input.value, 'SELECT borrador;');
assert.equal(ejecutadas, antes);
assert.ok(modal.classList.contains('visible'));
aceptada = true;
window.document.querySelector('.saved-item').click();
assert.equal(terminal.input.value, 'SELECT favorita;');
assert.equal(ejecutadas, antes + 1);
assert.ok(!modal.classList.contains('visible'));
dom.window.close();
console.log('OK DOM: sugerencias iniciales/dinámicas y favoritas confirman reemplazo; cancelar no ejecuta ni cierra favoritas.');

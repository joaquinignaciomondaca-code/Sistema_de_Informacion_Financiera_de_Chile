# Explorador sin solapes en pantalla pequeña — 2026-10-22

**Qué se vio.** En un teléfono (captura de 319 px de ancho) el árbol del explorador
se dibuja encima de sí mismo: los distintivos de la carpeta —«Trimestral desde
2020-03», «Derivados desde 2020-03 · pactos desde 2012-03», «16 cierres
validados»— aparecen como píldoras sueltas sobre los renglones siguientes, y la
etiqueta de una fila se cruza con la de la anterior.

**Diagnóstico.** No es un problema de pintado del navegador: es una caja de 28 px
con contenido que necesita dos líneas.

| Pieza | Dónde | Qué hace |
|---|---|---|
| `.tree-row { height: 28px }` | `docs/css/app.css:993` | Fija el alto del renglón. El alto se declara, no se calcula. |
| `.tree-partition { height: 25px }` | `docs/css/app.css:1253` | Lo mismo para las particiones (`.tree-row.tree-table.tree-partition`). |
| `.tree-sector, .tree-circular { flex-wrap: wrap }` | `docs/css/app.css:4315` | Permite que el distintivo baje a una segunda línea. |
| `.tree-circular .tree-label { flex: 1 1 120px; min-width: 120px }` | `docs/css/app.css:4316` | La etiqueta nunca se encoge por debajo de 120 px. |
| `.node-badge` dentro de `.tree-circular` | `docs/js/sidebar.js` (`renderGroup`) | El distintivo que baja de línea. |
| `@media (pointer: coarse) { .tree-label { min-height: 40px } }` | `docs/css/app.css:6038` | En un teléfono la etiqueta mide 40 px dentro de un renglón de 28 px. |

La cuenta en un cajón de 300 px (86 % de 350) para «Derivados y Pactos · Informes
IFRS»: 24 px de sangría + 16 de flecha + 16 de icono + 120 de etiqueta + el
distintivo («Derivados desde 2020-03 · pactos desde 2012-03», ~250 px) ≈ 426 px.
No cabe: el distintivo salta a la segunda línea. Esa segunda línea empieza en
`y + 21` y termina en `y + 39`, dentro de una caja de 28 px, así que se pinta
sobre el renglón siguiente. Con `pointer: coarse` se suma la etiqueta de 40 px,
que desborda 12 px por sí sola.

Lo correcto es que la fila **crezca** cuando su contenido ocupe dos líneas, y que
el distintivo que baja se alinee con su propia fila en vez de quedar pegado al
borde izquierdo.

## Pasos

- [x] **T1 · Diagnóstico con evidencia.** Medir la caja y el contenido de cada
  renglón en `app.css` y `sidebar.js`, y descartar que sea un artefacto de
  captura: las tres píldoras que se ven flotando son distintivos de `.tree-circular`
  en su segunda línea.
- [x] **T2 · Filas que crecen.** `.tree-row` pasa de `height: 28px` a
  `min-height: 28px` y `.tree-partition` de `height: 25px` a `min-height: 25px`:
  el alto mínimo se conserva y la fila se estira si el contenido la necesita.
- [x] **T3 · Distintivo alineado.** En `.tree-circular`, el `.node-badge` lleva
  `margin-left: auto`: si cabe, sigue a la derecha del nombre como hasta ahora;
  si baja de línea, queda a la derecha de su propio renglón y no sobre el
  siguiente.
- [x] **T4 · Objetivo táctil en la fila, no en la etiqueta.** La regla de puntero
  grueso pide los 40 px a `.tree-row`, `.tree-group-header` y `.dl-uso-item`
  (`min-height: 40px`) y deja de imponerle 40 px a `.tree-label`, que era lo que
  desbordaba la caja. De paso se corrige el selector `.tree-group > .tree-header`,
  que no existía en el marcado: la cabecera de industria nunca recibía su objetivo
  táctil. Los botones de la barra del explorador (`.tool-btn`) pasan a 44 px como
  el resto de las acciones.
- [x] **T4 bis · El distintivo no empuja la fila.** `.node-badge` recibe
  `max-width: 100%`, para que un texto largo como «Derivados desde 2020-03 ·
  pactos desde 2012-03» envuelva su propio contenido en vez de forzar un ancho
  mayor que el del cajón.
- [x] **T5 · Compuerta.** Regla 14 en `scripts/audit_movil.py`: ninguna fila del
  árbol puede declarar un `height` en píxeles, la etiqueta no puede llevar un
  `min-height` de 32 px o más, la fila tiene que alcanzar 40 px con puntero grueso
  y `.tool-btn` 44 px. Se suma su mutación a `--autoprueba` para confirmar que la
  regla detecta la avería.
- [x] **T6 · Versión de los archivos y compuertas.** Se cambia la etiqueta
  `?v=` de todos los archivos locales de `index.html` (la auditoría exige una
  sola etiqueta compartida) y se corren `audit_movil.py --autoprueba`,
  `audit_interfaz.py`, `audit_interfaz_dom.js`, `audit_navigation.py` y
  `audit_web_full.py`.

## Lo que no se toca

- La densidad del árbol en escritorio: `min-height: 28px` da el mismo alto
  cuando el contenido ocupa una línea, que es el caso normal a 320 px de ancho de
  barra lateral.
- El texto de los distintivos: son información del alcance y la cobertura. Si no
  caben, la fila crece; no se recortan ni se ocultan.

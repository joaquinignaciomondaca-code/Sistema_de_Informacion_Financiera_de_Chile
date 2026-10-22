# Ruta de optimización para celulares — 2026-10-22

**Objetivo:** que el sitio sea usable con una mano en un teléfono de 360–430 px, sin
perder nada de lo que ya funciona en escritorio.

**Cómo se midió:** no hay navegador en el entorno de trabajo, así que la revisión
es estática sobre `docs/css/app.css`, `docs/index.html` y los módulos JS que
generan marcado, y se cierra con dos compuertas nuevas que codifican las reglas
para que se puedan volver a comprobar en cada integración:

- `scripts/audit_movil.py` — doce reglas sobre CSS, marcado y eventos, con una
  autoprueba (`--autoprueba`) que rompe el diseño a propósito para confirmar que
  cada regla lo detecta.
- `scripts/audit_movil_dom.js` — con jsdom y una consulta de medios de 900 px
  activa, toca el botón, el fondo, `Escape` y una tabla del árbol para comprobar
  que el cajón se abre, se cierra y devuelve el foco al lugar correcto.

## Lo que estaba roto

| # | Problema | Dónde | Efecto en un teléfono |
|---|---|---|---|
| 1 | `body { height: 100vh; overflow: hidden }` y `.app-layout { height: calc(100vh - 45px) }` | `app.css` | En iOS Safari la barra del navegador recorta el panel inferior: el terminal SQL y sus botones quedan detrás de la barra. |
| 2 | La barra lateral no se colapsa al cargar y mide 320 px fijos | `sidebar.js`, `app.css` | En 390 px deja 70 px para el contenido: el sitio entra sin poder leer nada. |
| 3 | No hay reglas por debajo de 1020 px | `app.css` | Encabezado, pestañas, tarjetas y tablas mantienen medidas de escritorio. |
| 4 | Pestañas de 26 px de alto y sin deslizamiento guiado | `.panel-tab-btn` | Zonas táctiles por debajo de 44 px; siete pestañas que no se alcanzan con el pulgar. |
| 5 | Entradas de texto a 12 px | búsqueda del explorador, diccionario, descargas, terminal | iOS hace zoom al enfocar y descoloca la vista. |
| 6 | Tabla de la Guía de tres columnas con ancho fijo | `.uso-tabla` | Desborda a lo ancho en 360 px. |
| 7 | Modal de consultas guardadas de 360 px con `right: 18px` | `.saved-queries-modal` | Se sale del viewport en 360 px. |
| 8 | Avisos (toasts) fijos a 16 px del borde inferior | `.toast-host` | Quedan debajo del área segura del iPhone. |
| 9 | El mapa relacional sólo escucha `mousedown`, `mousemove` y `wheel` | `erd_graph.js` | No se puede arrastrar ni ampliar con el dedo: la pestaña Mapa es inútil en táctil. |
| 10 | No hay `viewport-fit=cover` ni `interactive-widget` | `index.html` | El teclado tapa el campo activo en Android y el contenido no respeta el notch. |

## Pasos

- [x] **M1 · Alto real.** `100dvh` con respaldo en `100vh`; `.app-layout` deja de
  calcular la altura con el 45 px mágico y pasa a `flex: 1`; la altura real de la
  cabecera se publica como `--sif-header-h` desde `ux_shell.js`.
- [x] **M2 · Explorador como cajón.** Por debajo de 900 px la barra lateral es un
  panel superpuesto (`position: fixed`) que arranca cerrado, con fondo oscurecido,
  cierre por toque fuera, por `Escape` y al elegir una tabla; el botón de la
  cabecera expone `aria-expanded`. El divisor de ancho se oculta.
- [x] **M3 · Cabecera y pestañas.** Cabecera compacta, título con elipsis, motor
  acortado; pestañas de 44 px con desplazamiento y `scroll-snap`, más un degradado
  en el borde derecho que avisa que hay más.
- [x] **M4 · Contenido.** Tabla de la Guía convertida en tarjetas con etiqueta por
  celda; entradas a 16 px; modal y avisos dentro del viewport con área segura;
  rellenos de 12–16 px; tablas del visor y de descargas con desplazamiento táctil.
- [x] **M5 · Objetivos táctiles.** Mínimos de 44 px en acciones y de 40 px en filas
  del árbol cuando el puntero es grueso; se anulan los efectos `:hover` que mueven
  o escalan tarjetas.
- [x] **M6 · Mapa táctil.** `erd_graph.js` pasa a Pointer Events: arrastre con un
  dedo, pellizco de dos dedos para ampliar y `click` suprimido después de arrastrar.
- [x] **M7 · Compuertas.** `scripts/audit_movil.py` (doce reglas, con autoprueba) y
  `scripts/audit_movil_dom.js` (comportamiento del cajón en jsdom) corren en
  `web_audit.yml`, después del paso que instala jsdom.

## Cómo se comprueba

```bash
python3 scripts/audit_movil.py --autoprueba   # las reglas detectan su avería
python3 scripts/audit_movil.py                # informe y código de salida
node scripts/audit_movil_dom.js               # el cajón, en jsdom
node scripts/audit_interfaz_dom.js            # las 90 comprobaciones de siempre
python3 scripts/audit_interfaz.py             # estructura, temas y motor
```

Resultado de la última ejecución (2026-10-22): `audit_movil.py` 12/12 reglas en
verde y su autoprueba 9/9 mutaciones detectadas; `audit_movil_dom.js` 11/11
comprobaciones OK; `audit_interfaz_dom.js` 90/90; `audit_interfaz.py` interfaz
coherente; `audit_web_full.py` todas las secciones operativas.

La compuerta no sustituye probar en un teléfono real: cubre lo que se puede
afirmar sin navegador (reglas de CSS presentes, marcado, eventos táctiles y
desbordes declarados). Lo que falta —rendimiento del motor en un equipo de gama
baja y comportamiento exacto de la barra de iOS— se anota como pendiente y se
resuelve con una prueba manual.

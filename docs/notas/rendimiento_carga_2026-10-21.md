# Rendimiento de carga: qué se cambió tras el informe Lighthouse — 2026-10-21

**Encargo:** el informe de Lighthouse del sitio desplegado señaló TBT de 680 ms, 21 peticiones que
bloquean el render (~557 KiB) y una cadena crítica de 3.578 ms. Esta nota registra qué se cambió,
qué se midió antes y después, y qué quedó **sin resolver** a propósito.

**Alcance:** sólo `docs/`, `scripts/audit_interfaz_dom.js`, el nuevo `scripts/audit_arranque_motor.js` y su paso en `.github/workflows/web_audit.yml`. Sin datos, sin pipelines, sin
dependencias nuevas. La etiqueta de versión de los activos locales pasa a
`fl-202610-2410-bajo-demanda`.

**Dos rondas.** La primera (commit `0570a99`, etiqueta `fl-202610-2400-rendimiento`) atacó los
scripts, los JSON y los reflujos. La segunda —la de esta etiqueta— saca del arranque el motor
DuckDB y el mapa relacional, que el informe mostraba dentro de la cadena crítica; la §3.4 la detalla
y corrige un diagnóstico equivocado de la §6.

---

## 1. La línea base

Medición entregada por el usuario sobre el despliegue con la etiqueta `fl-202610-212101-duckdb-lazy`:

| Métrica | Valor |
|---|---:|
| First Contentful Paint | 1,0 s |
| Largest Contentful Paint | 1,0 s |
| Total Blocking Time | **680 ms** |
| Cumulative Layout Shift | 0,03 |
| Speed Index | 2,4 s |
| Peso total de la página | 4.633 KiB |
| Tareas largas | 9 |
| Animaciones no compuestas | 8 |

Cadena crítica: HTML 366 ms → `portada.js` 1.585 ms → `cardinalidad_relaciones.json` 3.578 ms.

Peticiones que bloqueaban el render (557 KiB en total), de mayor a menor: `xlsx.full.min.js` 284,1 ·
`data_dictionary.js` 62,9 · `diccionario_seguros.js` 35,3 · `jszip.min.js` 29,5 · `sidebar.js` 24,3 ·
`download_catalog.js` 16,3 · `erd_graph.js` 14,1 · `duckdb_client.js` 12,6 · `data_viewer.js` 11,3 ·
`downloads_panel.js` 10,4 · `app.css` 23,0 (KiB transferidos, ya comprimidos).

## 2. El diagnóstico

Seis causas, no una:

1. **19 `<script src>` sin `defer`**, en el `<body>` pero antes de que el navegador pudiera pintar:
   todo el JS se descargaba y se ejecutaba en serie antes del primer pintado.
2. **Dos librerías que nadie usa al cargar.** `xlsx.full.min.js` (861 KiB en disco, 308 KiB
   comprimidos) y `jszip.min.js` (95 KiB, 28 comprimidos) sólo hacen falta cuando alguien pide una
   descarga en Excel o un paquete ZIP. Estaban en el `<body>` desde el principio, y el
   informe incluso detectó 50,9 KiB de `xlsx` descargados **sin ejecutarse**.
3. **Los dos JSON se pedían tarde.** `erd_graph.js` pedía `cardinalidad_relaciones.json` al
   construirse (después de todos los scripts) y `busqueda_pregunta.js` pedía el índice de 213 KiB en
   su `iniciar()`. La cadena crítica de 3,5 s es exactamente eso: el JSON no empieza a viajar hasta
   que termina el último script.
4. **El arranque era una sola tarea larga.** Un `DOMContentLoaded` que construía el explorador, la
   terminal, el grafo ERD y el diccionario (67 fichas, ~1.100 columnas) de un tirón. Eso es lo que
   mide el TBT: no el peso, sino el tiempo en que el hilo principal no atiende clics.
5. **`scrollToBottom()` leía `scrollHeight` en cada mensaje**, forzando un reflujo síncrono
   (72 ms en `chat_terminal.js:625` según el propio informe).
6. **El motor DuckDB y el mapa relacional se construían al cargar.** El `<head>` precargaba el wasm
   de 3.826 KiB, el worker y el módulo, y el constructor del cliente llamaba a `init()`. El mapa
   leía la geometría de un canvas oculto: 80 ms de reflujo forzado en `(index):568`.

## 3. Los cambios

| Archivo | Cambio |
|---|---|
| `docs/index.html` | Los 19 `<script src>` llevan `defer`; fuera `xlsx.full.min.js` y `jszip.min.js`; bloque `window.SIF_JSON` en el `<head>` que pide los dos JSON en paralelo al parseo; arranque partido en dos tareas (`setTimeout(0)`) y señal `window.SIF_LISTO`; fuera los precargados de DuckDB; Google Fonts deja de bloquear el pintado; insignia «DuckDB-Wasm · bajo demanda»; `window.asegurarERD()` |
| `docs/js/download_utils.js` | `cargarLibreria("excel" \| "zip")`: inyecta el `<script>` la primera vez, deduplica la promesa y reintenta si falla la red; `empaquetar()` y `exportarFilas(..., "xlsx")` la esperan |
| `docs/js/erd_graph.js` | La cardinalidad sale de `window.SIF_JSON.cardinalidad` si está; si no, del `fetch` original |
| `docs/js/busqueda_pregunta.js` | El índice sale de `window.SIF_JSON.indice` si está; si no, del `fetch` original |
| `docs/js/chat_terminal.js` | `scrollToBottom()` se difiere con `requestAnimationFrame`, se coalesce y usa `scrollTop = 1e7` en vez de leer `scrollHeight` |
| `docs/js/duckdb_client.js` | `ensureStarted()`: el motor arranca la primera vez que se necesita, no en el constructor. `query()` lo espera |
| `docs/js/downloads_panel.js` | Los botones CSV/Excel del motor se consideran disponibles hasta que un arranque falle; `exportarSerie()` arranca el motor y avisa mientras carga |
| `docs/js/ux_shell.js` | Clic en la insignia con el motor sin arrancar: lo inicia y lo dice |
| `docs/js/sidebar.js` | `mapaERD()`: el explorador construye el mapa la primera vez que lo necesita, sin hacerlo al cargar |
| `docs/css/app.css` | `tree-flash` anima `opacity` de una capa (compuesta) en vez de `background-color` |
| `scripts/audit_interfaz_dom.js` | 78 → **82** comprobaciones: ni el mapa ni el motor se construyen al cargar; abrir Mapa los construye y abrir Consultas arranca el motor |

### 3.1 Cuánto pesa menos el arranque

| | Antes | Ahora |
|---|---:|---:|
| Scripts que se descargan al cargar | 21 | 19 |
| JS en disco al cargar | 2.196,6 KiB | 1.240,2 KiB |
| De eso, comprimido (suma por archivo) | 559,7 KiB | 223,7 KiB |
| ¿Bloquea el primer pintado? | sí, 21 peticiones | no: todos `defer` |
| Peticiones del motor DuckDB al cargar | 3 archivos, 3.946,6 KiB | 0 hasta que se usa |

Los 956,4 KiB que salieron del arranque son `xlsx.full.min.js` (861,1) y `jszip.min.js` (95,3).
Ambos siguen en `docs/js/`: se cargan **sólo** cuando el usuario pide una descarga en Excel o un
ZIP, y la segunda vez ya están en caché.

### 3.2 Por qué el JSON va al `<head>`

Los dos archivos son pequeños y se necesitan en cuanto el usuario abre el mapa o busca:
`cardinalidad_relaciones.json` pesa 16,9 KiB (1,6 comprimido) e `indice_busqueda.json` 213,4 (33
comprimido). Pedirlos en el `<head>` no bloquea el render —son `fetch`, no `<script`— y ganan todo
el tiempo de descarga de los 19 scripts. Era el eslabón más caro de la cadena crítica.

El `catch(() => {})` de cada promesa no oculta el error: sólo evita un rechazo sin manejar; quien
consume la promesa sigue viendo la falla y cae al `fetch` propio.

### 3.3 Por qué dos tareas y no una

`setTimeout(fn, 0)` no adelanta trabajo: lo **parte**. Entre la primera tarea (explorador y
terminal, lo que el usuario ve y toca) y la segunda (el diccionario, y sólo si su pestaña está
visible) el navegador puede pintar y atender un clic. El diccionario, además, ahora sólo se pinta si su pestaña está visible:
si el usuario nunca la abre, se ahorra el trabajo entero. `switchMainTab` lo pinta al abrirla, como
ya hacía.

### 3.4 El motor y el mapa, sólo cuando se usan

El informe no sólo medía el peso: mostraba `duckdb-eh.wasm` y `duckdb-browser-eh.worker.js`
**dentro de la cadena crítica**, a 2,3 s. La causa era doble: el `<head>` precargaba los tres
archivos del motor y el constructor de `DuckDBClient` llamaba a `init()` al ejecutarse. Es decir,
los 3.826 KiB se descargaban y se compilaban en **todas** las visitas, aunque nadie abriera
Consultas ni Datos.

Ahora:

- fuera los tres `<link rel="preload">` del `<head>`;
- `new DuckDBClient()` ya no arranca nada; `ensureStarted()` lo hace la primera vez que se pide
  (pestaña SQL, pestaña de datos, descarga con motor o clic en la insignia) y devuelve siempre la
  misma promesa;
- el mapa relacional se construye al abrir su pestaña (`window.asegurarERD`). Su constructor leía
  `offsetWidth`/`offsetHeight` de un canvas oculto: el informe atribuía a esa llamada
  `(index):568` **80 ms** de reflujo forzado.

Con eso, la carga inicial deja de pedir el motor. Contando con los números de transferencia del
propio informe: 4.633 − 3.826 (wasm) − 68,5 (worker) − 52,1 (mjs) − 284,1 (xlsx) − 29,5 (jszip) =
**≈ 373 KiB** de primera carga, frente a los 4.633 KiB medidos. El ahorro no es magia: quien abra
Consultas seguirá pagando el wasm, pero sólo esa persona y sólo en ese momento.

## 4. Qué se midió

Todo lo que sigue se ejecutó y pasó:

| Verificación | Resultado |
|---|---|
| `node --check` en los 4 JS | OK |
| Carga diferida (`/tmp/test_lazy.js`, VM con DOM simulado) | 6/6: CSV no pide librerías · `xlsx` pide `js/xlsx.full.min.js` · no resuelve antes de `onload` · dos pedidos = una etiqueta · un fallo de red propaga «No se pudo descargar» y permite reintentar |
| `scripts/audit_interfaz.py` | exit 0 — «INTERFAZ COHERENTE» y los 15 archivos locales con la etiqueta nueva |
| `scripts/audit_navigation.py` | exit 0 |
| `scripts/audit_web_full.py` | exit 0 — «TODAS LAS SECCIONES DE LA WEB ESTAN 100% OPERATIVAS» |
| `scripts/audit_interfaz_dom.js` (con jsdom) | **82/82**, incluidas «el mapa relacional no se construye al cargar», «el motor DuckDB no arranca al cargar», «abrir Mapa construye el mapa relacional» y «abrir Consultas arranca el motor bajo demanda» |
| `scripts/audit_arranque_motor.js` (VM, **nuevo paso 11 del job `audit`**) | 7/7: el constructor no arranca ni pide red · la insignia avisa al arrancar · `ensureStarted()` es idempotente (dos llamadas, un arranque) · `query()` arranca si nadie lo hizo · un arranque fallido devuelve el error explícito |
| `scripts/audit_xss_celdas.js` | exit 0 |
| `scripts/audit_sql_guard.js` | exit 0 |
| `scripts/audit_duckdb_client.js` | exit 0 — registro de vistas OK |
| Detector de diseño (`impeccable detect --no-config docs/`) | 0 hallazgos |

## 5. Qué **no** se midió

- **El TBT real después del cambio.** No hay Chrome en este entorno: el TBT sólo se confirma con
  Lighthouse sobre el sitio servido (idealmente el despliegue) o con el panel *Performance* de un
  navegador. Un `setTimeout(0)` reduce el bloqueo esperado, pero no lo demuestra. **No** se afirma
  una cifra nueva.
- **El efecto visual de `defer`** en conexiones lentas: los scripts ya no bloquean, pero el orden
  relativo de ejecución cambió respecto del HTML. Las auditorías lo cubren por comportamiento (la
  página funciona y el DOM queda completo), no por cronómetro.
- **La carga de `xlsx`/`jszip` contra el CDN**: se sirven del mismo origen que el resto de `docs/js/`.
- **El intercambio de la fuente.** Google Fonts pasa a precargarse y aplicarse al llegar: deja de
  bloquear el pintado, pero el texto puede verse un instante con la fuente de reserva. No hay
  navegador aquí para medir ese parpadeo ni para compararlo con el `font-display=swap` anterior.
- **El costo del motor al abrir Consultas.** El wasm de 3,8 MB se sigue descargando la primera vez
  que se usa el motor; no se midió cuánto tarda ese arranque en frío en el despliegue.

## 6. Lo que quedó pendiente, a propósito

El informe también señala cosas que **no** se tocaron o que quedan abiertas. Conviene dejarlas
escritas para que no se lean como resueltas:

1. **`data_dictionary.js` (495,8 KiB) y `diccionario_seguros.js` (212,7 KiB)** son ahora, de lejos,
   lo más pesado del arranque: 709 KiB de los 1.240. Son datos con forma de JS (`window.SIFDataDictionary`,
   `window.DICCIONARIO_SEGUROS`) que consumen `data_viewer.js`, `download_utils.js` y
   `downloads_panel.js` de forma **síncrona**. Convertirlos en `fetch` exige volver asíncronos esos
   tres consumidores; es una intervención de otro tamaño y con riesgo real de regresión silenciosa.
   Queda como la siguiente palanca, medida antes de tocarla.
2. **DuckDB: 3.826 KiB de wasm** más el worker (68,5) y `duckdb-browser.mjs` (52,1). La primera
   versión de esta nota decía que el motor «se levanta cuando se usa»; era falso: el `<head>`
   precargaba los archivos y el constructor llamaba a `init()` al cargar. El informe lo desmintió al
   mostrarlo en la cadena crítica, y la segunda ronda lo corrigió (§3.4). Lo que queda es el costo
   real del motor: quien abre Consultas o Datos lo descarga una vez; quien no, nunca.
3. **CSS y JS sin minificar** (113,8 KiB de CSS, 1.240 de JS). Minificar exigiría un paso de
   compilación y una copia generada por archivo; hoy el sitio se sirve tal cual desde `docs/` y así
   lo leen las auditorías y el detector. El ahorro comprimido sería de decenas de KiB, no de cientos.
   No se hizo.
4. **Las 8 animaciones no compuestas.** De las seis reglas `@keyframes`, sólo `tree-flash` animaba
   una propiedad no compuesta (`background-color`); las otras cinco ya usaban `transform`/`opacity`.
   Se pasó a una capa con `opacity` (§3, `app.css`). Las que Lighthouse seguía contando de más no se
   pudieron identificar sin Chrome: la medición dirá si bajó el número.
5. **Las auditorías de minificación y de JS sin usar estaban contaminadas por una extensión de
   Chrome** (`chrome-extension://gighmmpiobklfepjocnamgkkbiglidom`, un bloqueador de anuncios):
   73 KiB de los 73 KiB de «Minify JavaScript» y 103 de los 154 KiB de «Reduce unused JavaScript»
   eran de la extensión, no del sitio. Del sitio, lo único accionable era `xlsx` (50,9 KiB sin
   usar), ya fuera del arranque.

## 7. Cómo volver a medir

```bash
# sitio local, mismo origen que producción
node scripts/servir_sitio_local.mjs          # 0.0.0.0:8000, raíz docs/

# en el navegador: DevTools → Lighthouse → Performance, móvil, sin caché
# comparar contra la línea base de §1 (TBT 680 ms, 21 peticiones bloqueantes)
```

Para que la comparación sea justa, la etiqueta de versión tiene que ser la nueva
(`fl-202610-2410-bajo-demanda`): si Lighthouse sigue viendo `fl-202610-212101-duckdb-lazy` en las
URL, está midiendo la caché anterior. En el informe nuevo deberían desaparecer del árbol de
dependencias `duckdb-eh.wasm`, el worker y `duckdb-browser.mjs`, y el peso total debería quedar en
el orden de los ~373 KiB contados en §3.4. El TBT sólo bajará si además desaparecen las tareas
largas del arranque; eso es lo que hay que mirar, no el peso.

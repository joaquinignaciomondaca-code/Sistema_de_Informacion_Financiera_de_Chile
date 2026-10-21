# Rendimiento de carga: qué se cambió tras el informe Lighthouse — 2026-10-21

**Encargo:** el informe de Lighthouse del sitio desplegado señaló TBT de 680 ms, 21 peticiones que
bloquean el render (~557 KiB) y una cadena crítica de 3.578 ms. Esta nota registra qué se cambió,
qué se midió antes y después, y qué quedó **sin resolver** a propósito.

**Alcance:** sólo `docs/` y `scripts/audit_interfaz_dom.js`. Sin datos, sin pipelines, sin
dependencias nuevas. La etiqueta de versión de los activos locales pasa a
`fl-202610-2400-rendimiento`.

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

Cuatro causas, no una:

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

## 3. Los cambios

| Archivo | Cambio |
|---|---|
| `docs/index.html` | Los 19 `<script src>` llevan `defer`; fuera `xlsx.full.min.js` y `jszip.min.js`; bloque `window.SIF_JSON` en el `<head>` que pide los dos JSON en paralelo al parseo; arranque partido en dos tareas (`setTimeout(0)`) y señal `window.SIF_LISTO` |
| `docs/js/download_utils.js` | `cargarLibreria("excel" \| "zip")`: inyecta el `<script>` la primera vez, deduplica la promesa y reintenta si falla la red; `empaquetar()` y `exportarFilas(..., "xlsx")` la esperan |
| `docs/js/erd_graph.js` | La cardinalidad sale de `window.SIF_JSON.cardinalidad` si está; si no, del `fetch` original |
| `docs/js/busqueda_pregunta.js` | El índice sale de `window.SIF_JSON.indice` si está; si no, del `fetch` original |
| `docs/js/chat_terminal.js` | `scrollToBottom()` se difiere con `requestAnimationFrame`, se coalesce y usa `scrollTop = 1e7` en vez de leer `scrollHeight` |
| `scripts/audit_interfaz_dom.js` | Espera `window.SIF_LISTO` antes de mirar el DOM (el init ya no es síncrono) |

### 3.1 Cuánto pesa menos el arranque

| | Antes | Ahora |
|---|---:|---:|
| Scripts que se descargan al cargar | 21 | 19 |
| JS en disco al cargar | 2.196,6 KiB | 1.240,2 KiB |
| De eso, comprimido (suma por archivo) | 559,7 KiB | 223,7 KiB |
| ¿Bloquea el primer pintado? | sí, 21 peticiones | no: todos `defer` |

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
terminal, lo que el usuario ve y toca) y la segunda (grafo ERD y diccionario) el navegador puede
pintar y atender un clic. El diccionario, además, ahora sólo se pinta si su pestaña está visible:
si el usuario nunca la abre, se ahorra el trabajo entero. `switchMainTab` lo pinta al abrirla, como
ya hacía.

## 4. Qué se midió

Todo lo que sigue se ejecutó y pasó:

| Verificación | Resultado |
|---|---|
| `node --check` en los 4 JS | OK |
| Carga diferida (`/tmp/test_lazy.js`, VM con DOM simulado) | 6/6: CSV no pide librerías · `xlsx` pide `js/xlsx.full.min.js` · no resuelve antes de `onload` · dos pedidos = una etiqueta · un fallo de red propaga «No se pudo descargar» y permite reintentar |
| `scripts/audit_interfaz.py` | exit 0 — «INTERFAZ COHERENTE» y los 15 archivos locales con la etiqueta nueva |
| `scripts/audit_navigation.py` | exit 0 |
| `scripts/audit_web_full.py` | exit 0 — «TODAS LAS SECCIONES DE LA WEB ESTAN 100% OPERATIVAS» |
| `scripts/audit_interfaz_dom.js` (con jsdom) | **78/78** |
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

## 6. Lo que quedó pendiente, a propósito

El informe también señala cosas que **no** se tocaron, y conviene dejarlas escritas para que no se
lean como resueltas:

1. **`data_dictionary.js` (495,8 KiB) y `diccionario_seguros.js` (212,7 KiB)** son ahora, de lejos,
   lo más pesado del arranque: 709 KiB de los 1.240. Son datos con forma de JS (`window.SIFDataDictionary`,
   `window.DICCIONARIO_SEGUROS`) que consumen `data_viewer.js`, `download_utils.js` y
   `downloads_panel.js` de forma **síncrona**. Convertirlos en `fetch` exige volver asíncronos esos
   tres consumidores; es una intervención de otro tamaño y con riesgo real de regresión silenciosa.
   Queda como la siguiente palanca, medida antes de tocarla.
2. **DuckDB: 3.826 KiB de wasm** más el worker (68,5) y `duckdb-browser.mjs` (52,1). No es un
   problema de carga inicial —el motor se levanta cuando se usa la terminal SQL o la vista de
   datos—, pero sí explica parte del peso total de 4.633 KiB. Se dejó como estaba: es el costo del
   motor en el navegador, no un descuido.
3. **CSS y JS sin minificar** (113,8 KiB de CSS, 1.240 de JS). Minificar exigiría un paso de
   compilación y una copia generada por archivo; hoy el sitio se sirve tal cual desde `docs/` y así
   lo leen las auditorías y el detector. El ahorro comprimido sería de decenas de KiB, no de cientos.
   No se hizo.
4. **Las 8 animaciones no compuestas** son decorativas (pulsos, transiciones de insignias). Pasarlas
   a `transform`/`opacity` es cosmético y no mueve el TBT; no se tocaron para no cambiar el aspecto
   sin un antes/después visual.

## 7. Cómo volver a medir

```bash
# sitio local, mismo origen que producción
node scripts/servir_sitio_local.mjs          # 0.0.0.0:8000, raíz docs/

# en el navegador: DevTools → Lighthouse → Performance, móvil, sin caché
# comparar contra la línea base de §1 (TBT 680 ms, 21 peticiones bloqueantes)
```

Para que la comparación sea justa, la etiqueta de versión tiene que ser la nueva
(`fl-202610-2400-rendimiento`): si Lighthouse sigue viendo `fl-202610-212101-duckdb-lazy` en las
URL, está midiendo la caché anterior.

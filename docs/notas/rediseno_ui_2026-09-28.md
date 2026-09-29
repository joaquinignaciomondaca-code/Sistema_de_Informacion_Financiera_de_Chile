# Rediseño de interfaz y cambio de nombre (2026-09-28)

Objeto: el sitio estático de `docs/` (ahora **Sistema de Información Financiera de
Chile**). No se tocaron pipelines, datos publicados ni `docs/outputs/`.

## 1. Qué cambió

| Área | Antes | Ahora |
| :--- | :--- | :--- |
| Nombre | "Monitor Financiero Chile (MFC)" | "Sistema de Información Financiera de Chile (SIF)" en `<title>`, encabezado, README, pseudocódigo y encabezados de los módulos JS |
| Terminal SQL | Panel inferior fijo con divisor arrastrable, visible siempre junto al resto | Pestaña propia **Consultas SQL** a pantalla completa; se eliminó el panel inferior y el divisor |
| Pestañas | Información · Mapa Relacional · Diccionario · Visor de Datos · Normativa CMF · Descargar Datos (acción mezclada entre pestañas) | Información · Mapa relacional · Diccionario · Visor de datos · **Consultas SQL** · Normativa CMF, con `role="tab"` y `aria-selected`; *Descargar datos* pasó a ser un botón de acción separado |
| Contexto | El breadcrumb (industria › carpeta) vivía dentro de los filtros del mapa y sólo se veía en esa pestaña | Franja de contexto siempre visible en la cabecera (`#erd-breadcrumb`) con la ruta completa: sector › carpeta › tabla |
| Filtros del mapa | Comprimidos en la misma fila que las pestañas, con desplazamiento horizontal | Franja propia bajo la cabecera, con salto de línea |
| Información | Guía narrativa | Mismo enfoque, con cifras verificadas (15 industrias, 52 tablas), tarjeta de Normativa CMF y atajos documentados |
| Colores | `#191E29`, `#151A24`, `#FFFFFF` fijos y badges con hex propios | Variables de la paleta activa: superficies (`--bg-secondary`, `--bg-primary`), textos (`--text-bright`, `--text-muted`) y semánticos nuevos `--warn-rgb`, `--info-rgb`, `--teal-rgb`, `--violet-rgb`, `--orange-rgb`, `--red-rgb` en los seis temas |
| Accesibilidad | Sin foco visible consistente | `:focus-visible` global, `kbd`, `aria-live` en mensajes del terminal y avisos |
| Detalles | — | Avisos breves (toasts), pestaña recordada en `localStorage`, autocompletado con `Tab`, botón *Limpiar*, ERD que se redimensiona al abrir su pestaña |

Archivos nuevos: `docs/js/ux_shell.js` (pestaña recordada, avisos, estado del motor
DuckDB, atajos `Alt`+`1`…`6` y `/`).

## 2. Defectos corregidos en el camino

1. **Regresión propia detectada por prueba**: el modal de consultas guardadas se
   anclaba a `.bottom-panel`; al eliminar ese panel quedaba sin montar y lanzaba
   excepción. Ahora se monta en `document.body` con posición fija.
2. **ERD fuera de escala**: `erd_graph.resize()` medía el panel completo (que ahora
   incluye cabecera y franja de filtros) en lugar del propio canvas.
3. **Tema claro roto por colores fijos**: con la paleta `informe`, textos blancos
   sobre fondo blanco y badges ámbar ilegibles. Se sustituyeron por variables.

## 3. Cómo se verificó (no hubo navegador disponible)

En el entorno de trabajo no se pudo bajar un navegador headless (los CDN de
Playwright y de Chromium están bloqueados y no hay permisos de root para `apt`), así
que la comprobación fue estática y funcional, no visual:

* `node -c` sobre todos los módulos JS y `vm.createScript` sobre el script en línea.
* `python3 scripts/audit_web_full.py` → *todas las secciones 100% operativas*
  (assets, sidebar, visor, diccionario y ERD contra los Parquet reales).
* `python3 scripts/audit_navigation.py` → 12 familias, 52 tablas, 52 opciones.
* `python3 scripts/audit_automatizacion.py` → 53 tablas inventariadas, 0 problemas.
* `node scripts/audit_normativa_web.js` → OK (se adaptaron dos comprobaciones que
  buscaban los literales de `switchMainTab`, hoy reemplazados por un registro de
  pestañas).
* Prueba de humo con jsdom (script temporal, fuera del repositorio): 19/19
  comprobaciones sobre estructura de pestañas, pestaña SQL, barra de contexto,
  avisos, autocompletado y limpieza del terminal.

**Falta la revisión visual humana.** El diseño se validó por lógica y auditoría, no
por captura de pantalla: conviene revisar el ancho de la cabecera con seis pestañas,
el alto del terminal en pantallas bajas y el contraste de los badges contables en la
paleta `informe`.

## 4. Pendiente sugerido para la próxima iteración

* Indicador en la pestaña *Consultas SQL* cuando el explorador deja una consulta
  preparada mientras el usuario está en otra pestaña.
* Estados vacíos del visor de datos y del diccionario cuando no hay tabla cargada.
* Revisión de contraste fina en los temas `bloomberg` y `swissborg`, donde el acento
  y el color de advertencia comparten tono.

## 5. Segunda pasada, a partir de la revisión visual del usuario (2026-09-28)

La captura de pantalla del usuario mostró tres defectos que la verificación
estática no podía ver.

1. **Pestañas cortadas y contexto invisible (alto).** Con seis pestañas, el grupo
   no cedía espacio: "Consultas SQL" quedaba recortada y "Normativa CMF" fuera de
   vista, con barra de desplazamiento horizontal; la barra de contexto quedaba
   empujada fuera del panel. Se acortaron las etiquetas (Mapa, Visor, Normativa),
   se ajustó el espaciado, las pestañas ahora ceden ancho antes que el contexto y
   la barra de contexto se recorta sola o desaparece bajo 1020 px.
2. **Botón de descarga duplicado.** Existía "Descargar Base de Datos" en el
   encabezado y "Descargar Datos" dentro del panel, ambos con la misma acción. Se
   eliminó el del panel (decisión revisada después: ver la tercera pasada, punto 4).
3. **Nombres de familia ilegibles en el explorador (medio).** Los badges dejaban
   el título en "COMP...", "ADMINISTRACIÓN DE FONDOS …". Ahora los badges pasan a
   una segunda línea antes que comerse el nombre (grupos, sectores y carpetas).

### Motor DuckDB: la causa de "Motor DuckDB no disponible"

El motor se cargaba sólo desde `cdn.jsdelivr.net`. Si la red del visitante bloquea
ese CDN, el terminal SQL queda muerto. Se cambió a:

1. **Copia local incluida en el repositorio** (`docs/vendor/duckdb/`, 17,5 MB:
   `duckdb-browser.mjs`, `duckdb-browser-eh.worker.js` y `duckdb-eh.wasm` de
   @duckdb/duckdb-wasm 1.28.0, MIT). El sitio se sirve completo desde su origen.
2. **CDN como respaldo** si la copia local falta o el navegador no soporta el
   bundle `eh`.
3. **Diagnóstico visible**: si el motor no arranca, la pestaña de consultas muestra
   el motivo concreto y un botón *Reintentar* (antes sólo lo insinuaba el badge del
   encabezado, con el detalle escondido en un tooltip).

También se sirve `.wasm` como `application/wasm` en `scripts/preview_no_cache.py`
(y se cachea, para no rebajar 18 MB en cada recarga).

### Guardián automático

Nuevo `scripts/audit_interfaz.py` (sin dependencias, apto para CI): verifica
pestañas y paneles, componentes del terminal, ausencia de restos del panel
inferior, capa `ux_shell.js`, que no haya colores fijos fuera de las paletas (esta
comprobación encontró dos fallbacks que se me habían pasado: `#172433` y
`#ff6b6b`) y que la copia local del motor exista y se use antes que el CDN.

### Verificación de esta pasada

* `python scripts/audit_interfaz.py` → INTERFAZ COHERENTE.
* `python scripts/audit_web_full.py` → todas las secciones 100% operativas.
* `python scripts/audit_navigation.py`, `audit_automatizacion.py`,
  `node scripts/audit_normativa_web.js` → sin hallazgos.
* Prueba de humo con jsdom (16 comprobaciones): conmutación de pestañas, pestaña
  recordada, avisos, barra de contexto, autocompletado, limpieza del terminal y
  aparición/ocultamiento del diagnóstico del motor.
* Servido por HTTP: `duckdb-eh.wasm` responde 200 con `application/wasm`, acepta
  rangos (206) y el módulo tiene cabecera wasm válida.

Sigue pendiente la confirmación visual del usuario. En particular, si el motor
ahora arranca, el badge del encabezado debe decir "DuckDB-Wasm activo" y la pista
de la pestaña de consultas "DuckDB-Wasm activo: cada consulta se ejecuta en tu
navegador…".

## 6. Tercera pasada: la descarga vuelve al panel (2026-09-28)

**4. La descarga vive en la cabecera del panel, no en el encabezado.** Por pedido
del usuario se invirtió la decisión de la segunda pasada: el botón *Descargar datos*
está ahora junto a la barra de contexto, en la cabecera del panel, y el encabezado
superior quedó sólo con la marca, el estado del motor y el selector de paletas. Para
que las seis pestañas sigan entrando, la barra de contexto cede ancho antes que
ellas y desaparece bajo 1280 px; bajo 1020 px el botón se queda sólo con su ícono.

**Defecto grave encontrado al hacer este cambio (alto, funcional).** El botón de
descarga del encabezado **no hacía nada**: al reescribir el bloque de pestañas en la
primera pasada se perdió, sin que ninguna comprobación lo notara, el bloque que
conectaba el botón con `ExportModal.open`. La lección quedó incorporada al guardián:
`scripts/audit_interfaz.py` ahora exige, además del id en el HTML, que el botón tenga
manejador de click, que llame a `ExportModal.open` y que `export_modal.js` se cargue.
Se verificó que la comprobación falla de verdad quitando el cableado a propósito.

**Nuevas comprobaciones automáticas de comportamiento.** La prueba que antes vivía
fuera del repositorio queda como `scripts/audit_interfaz_dom.js`: ejecuta los scripts
de `docs/` en un DOM (jsdom) y verifica 19 comportamientos, entre ellos que al hacer
clic en *Descargar datos* se abra el centro de exportación. Si jsdom no está
instalado, avisa y termina sin error (no se agrega esa dependencia al flujo de CI).

## 7. Cuarta pasada: la descarga pasa a ser una pestaña (2026-09-28)

**El diagnóstico del usuario fue el correcto.** "Siento que el sistema de descarga
actual es poco intuitivo": el modal *Centro de Exportación & Descarga* obligaba a
elegir formato (CSV / Excel / Parquet), alcance (pantalla / años / todo) y particionado
antes de saber qué había del otro lado, y escondía en un `<select>` la tabla a
exportar. La decisión anterior —un único botón en la cabecera del panel— había
eliminado la duplicación, pero no la opacidad.

**Qué cambió.** La descarga es ahora la séptima pestaña, *Descargas*, con el catálogo
completo a la vista:

- `scripts/build_download_catalog.py` genera `docs/js/download_catalog.js`
  (`window.DOWNLOAD_CATALOG`) leyendo las vistas publicadas (`SEMANTIC_VIEWS`), los
  nombres legibles del visor (`DATA_VIEWER_CATALOG`), los manifiestos de
  `docs/outputs/**/manifest.json` y los tamaños reales en disco. Resultado: **52
  conjuntos, 12.787.887 filas documentadas y 261,8 MB de Parquet**, agrupados en 15
  sectores. Se regenera con `python3 scripts/build_download_catalog.py` y
  `--check` falla si quedó desactualizado (lo ejecuta la auditoría de interfaz).
- `docs/js/downloads_panel.js` dibuja cada conjunto con sus filas, periodo, peso y
  archivos, y pone la acción al lado: **Parquet original** (descarga directa, un
  enlace por periodo cuando el conjunto se publica por partes), **CSV** y **Excel**
  (serie completa, armados con DuckDB en el navegador) y **SQL** (abre el terminal
  con la consulta lista). Hay búsqueda, filtro por sector y recorte opcional por años.
- **Lo que estás viendo**: si se llega desde el Visor, la pestaña trae esa tabla
  seleccionada con sus filas en pantalla, más un acceso al Parquet original. El visor
  ya no abre un modal: llama a `MFCUI.openDownloads({...})`.
- El modal se retiró por completo (`docs/js/export_modal.js`, sus 415 líneas de CSS y
  el botón `#tab-btn-export`). Sus reglas de particionado sobrevivieron en
  `docs/js/download_utils.js` (`window.MFCDownload`), compartido con el visor.

**Guardianes actualizados.** `scripts/audit_interfaz.py` ahora verifica las siete
pestañas, que el catálogo esté sincronizado (`--check`), que existan Parquet directo y
CSV/Excel por motor, que el visor abra Descargas y que no queden restos del modal
(retiró también la clase `.panel-action-btn`, ya sin uso). `scripts/audit_interfaz_dom.js`
pasó de 19 a **35 comprobaciones**: dibujo del catálogo, búsqueda, filtro por sector,
despliegue de los Parquet por periodo, contexto del visor, aviso cuando el motor no
está disponible y traspaso a Consultas SQL.

**Conteos honestos.** Cinco conjuntos (los catálogos de instituciones) no declaran
filas en su manifiesto: la web lo dice tal cual ("filas: se cuentan al consultar") en
vez de inventar un número. Los dos conjuntos unificados de banca (B1/B2 y R1) avisan
que el Parquet original baja los archivos completos.

## 8. Quinta pasada: el vocabulario de las tablas (2026-09-28)

**La observación del usuario**: "revisar vocabulario, cómo se nombran cada tabla…
todo lo que sea lista de entidades normalizar el nombre a ese y que no se use otro".
La revisión encontró que la misma idea tenía hasta cinco nombres a la vez
(`*.lista_administradoras`, `*.lista_instituciones`, `*.lista_emisiones`,
`corredoras.registro_unico`, `*.catalogo_institucional`) y que los ids internos
convivían con prefijos de sector de tres generaciones (`pensiones_*`, `cajas_compensacion_*`,
`cb_*`, `sec_*`, `fl_*`, `*_maestro`, `bancos_cmf_*`).

**Una sola autoridad: `docs/vocabulario.json`.** Describe las 52 tablas publicadas con
`id`, `nombre`, `tipo`, `sector`, `descripcion`, `cobertura` y los nombres anteriores
como `alias`. La regla queda escrita en el propio archivo: *una tabla se llama
`<sector>.<tipo>`; toda lista de entidades de un sector se llama `lista_entidades` y
no admite otro nombre* (la única variante es `lista_entidades_registro`, para el
registro único de corredoras). Son **15 sectores, 22 tipos de tabla y 15 listas de
entidades**, con prefijos de sector cortos y estables (`afp`, `bancos`, `ccaf`,
`corredoras`, `fi`, `ffmm`, `fintech`, `macro`, `factoring_leasing`,
`patrimonios_separados`, `cooperativas`, `agf`, `securitizadoras`, `seguros`,
`sistemas_pago`) y una lista explícita de `nombres_retirados`.

**`scripts/normalizar_vocabulario.py` aplica el vocabulario y lo vigila.** Sin
argumentos reescribe los archivos vivos (ids, nombres visibles, etiquetas de sector,
diccionario, catálogo del visor, ids de nodo del explorador, bloques de alias SQL,
`README.md`); con `--check` falla si algo se salió del vocabulario. La auditoría de
interfaz ejecuta `--check` en cada corrida, así que el vocabulario no se puede
desincronizar sin que la suite lo diga.

**Qué quedó normalizado en la interfaz**

- Nombres de tabla en el árbol, el visor, el diccionario, el mapa y Descargas:
  `afp.lista_entidades`, `bancos.balance`, `bancos.resultados`, `ccaf.*`,
  `corredoras.lista_entidades_registro`, `factoring_leasing.balance`, etc.
- Ids internos: `afp_maestro` → `afp_lista_entidades`, `bancos_cmf_balance` →
  `bancos_balance`, `corredoras_bolsa_registro_universo` →
  `corredoras_bolsa_lista_entidades_registro`, todos los `*_maestro` de una vez.
- Nodos del explorador: `cat_<tabla_id>` (`cat_afp_lista_entidades`,
  `cat_bancos_balance`); las carpetas que agrupan varias tablas usan
  `cat_<prefijo>_<contenido>` (`cat_seguros_cartera_1835`, `cat_ffmm_cartera_1333`).
  Las cinco carpetas de lista de entidades que se llamaban distinto
  (`fi_cat_entidades`, `c1333_ffmm_cat`, `circ_ps_emisiones`, …) ahora abren
  `Lista de Entidades` y su nodo es el de su tabla.
- Etiquetas de sector: las 15 son idénticas en árbol, visor, diccionario y Descargas
  (incluida Fintech, que en el visor había quedado con el nombre antiguo porque la
  expresión regular no alcanzaba el último bloque del catálogo).
- La cobertura de cada tabla (`rows` en el árbol, `registros` en el diccionario) y el
  tipo de tabla (`detalle`) salen del vocabulario: una sola fuente, sin prosa copiada.
- Caché: los 15 archivos locales de `docs/index.html` comparten una etiqueta de
  versión (`?v=20260928-vocabulario-1`) y la auditoría lo verifica; antes convivían
  cinco etiquetas distintas y dos archivos tocados podían quedar cacheados.

**Compatibilidad SQL, no en la interfaz.** `docs/js/duckdb_client.js` conserva los
nombres anteriores en `LEGACY_VIEW_ALIASES` (bloque `BEGIN/END VOCABULARIO ALIAS`) y
crea una vista de alias junto a cada vista canónica: `SELECT * FROM bancos_cmf_balance`
sigue funcionando para consultas guardadas o pegadas, pero el autocompletado, los
chips y las sugerencias sólo ofrecen el nombre canónico.

**Los datos no se movieron.** Los Parquet publicados conservan sus nombres de archivo
(`bancos_maestro.parquet`, `ccaf_maestro.parquet`) porque renombrarlos rompería los
pipelines y los enlaces ya publicados; el vocabulario los declara como ruta de origen.
`data_manifest.json` y `pipelines/auto/inventario.json` siguen el mismo criterio: los
ids de publicación son los históricos y `scripts/audit_automatizacion.py` los traduce
al vocabulario para cruzar manifiesto, inventario y web.

**Verificación.** `audit_interfaz.py` (vocabulario + caché), `audit_interfaz_dom.js`
(**39/39**, con tres pruebas nuevas: nombres `<sector>.<tipo>`, nombres retirados
ausentes y 15 listas de entidades), `audit_navigation.py` (52 tablas, 52 opciones,
14 sectores), `audit_automatizacion.py` (0 problemas), `audit_normativa_web.js` y
`audit_web_full.py` en verde. El catálogo de Descargas se regeneró: **52 conjuntos,
8.942.772 filas contadas y 261,8 MB**, con dos conjuntos unificados de banca que
informan "filas: se cuentan al consultar" en vez de repetir el total del manifiesto
(que suma B1, B2 y R1, no lo que muestra la vista).

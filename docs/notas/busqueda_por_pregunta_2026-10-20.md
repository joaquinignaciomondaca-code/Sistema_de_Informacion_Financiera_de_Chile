# Búsqueda por pregunta o concepto (punto 9)

Fecha: 2026-10-20.

> **Snapshot histórico (2026-10-20).** Los conteos de tablas y consultas describen ese release; para métricas actuales consulta [`metricas_publicadas.json`](../metricas_publicadas.json).

## Qué había antes

- El filtro de la barra lateral busca por nombre de tabla, familia o subsector.
- El diccionario busca por columna, significado o criterio contable.
- Las descargas buscan por conjunto, tabla o sector.

Ninguno responde a una pregunta como "¿cuánto es la UF?" o "tasa de desempleo", porque el texto de la pregunta no aparece en el nombre de la tabla.

## Qué se agregó

- **`docs/busqueda_sinonimos.json`**: 40 conceptos y alias en español (por ejemplo, `inflacion` → IPC, expectativas y breakeven; `dolar` → dólar observado y tipos de cambio multilaterales y reales). Está escrito a mano.
- **`scripts/generar_indice_busqueda.py`**: une los sinónimos con `docs/reproducibilidad/diccionario.json` y escribe `docs/outputs/indice_busqueda.json` (75 tablas). Falla si un sinónimo apunta a una tabla que no existe.
- **`docs/js/busqueda_pregunta.js`**: campo "Buscar por pregunta o concepto" bajo el filtro existente. Puntúa por concepto o alias (más peso), nombre y descripción de la tabla, y nombres de columna. Al elegir un resultado, escribe el nombre de la tabla en el filtro del árbol, así que reutiliza la navegación existente. Enter elige el primero.
- Los listados de entidades bajan en el orden, salvo que la pregunta hable de entidades o registros. Sin eso, "fondos mutuos cartera" mostraba primero el listado de entidades.

## Verificación

- Consultas de prueba con el índice real (`node`): "uf", "inflación", "dólar", "tpm", "desempleo", "bonos", "cobre", "factoring", "bancos balance", "derivados", "Ley fintec" y "tipo de cambio" devuelven la tabla esperada en primer lugar. Una consulta sin sentido devuelve "sin resultados".
- Prueba de DOM con jsdom (no hay navegador en el sandbox): la interfaz se crea; escribir genera resultados; clic y Enter escriben el nombre en `#sidebar-search` y disparan el evento `input`; sin resultados muestra el mensaje; si el índice no carga, el campo queda deshabilitado con el error y el filtro normal sigue disponible.
- Pendiente: prueba en un navegador real y en el sitio publicado. El sandbox no tiene navegador ni acceso a GitHub Pages.

## Hallazgo: nombres de tablas distintos entre manifiesto y web

El manifiesto (`data_manifest.json`) y la web usan ids distintos para las mismas tablas. La web es la que ve el usuario:

| Manifiesto | Web (diccionario y barra lateral) |
|---|---|
| `afp_maestro`, `agf_maestro`, `ccaf_maestro`, `bancos_maestro`, `ffmm_maestro`, `fi_maestro`, `securitizadoras_maestro`, `patrimonios_separados_maestro`, `seguros_maestro`, `corredoras_bolsa_maestro`, `factoring_leasing_maestro`, `fintech_rpsf_maestro`, `sistemas_pago_maestro` | `*_lista_entidades` |
| `bancos_cmf_lineas` (una sola tabla) | `bancos_balance` y `bancos_resultados` (vistas sobre el mismo archivo, filtradas por familia de archivo) |
| `factoring_leasing_balance_serie_ifrs_cmf`, `factoring_leasing_resultados_serie_ifrs_cmf` | `factoring_leasing_balance`, `factoring_leasing_resultados` |

El vocabulario canónico (`docs/vocabulario.json`) dice que las listas de entidades se llaman `lista_entidades` y no admiten otro nombre. Por eso el índice usa los nombres de la web. Corregirlo en el manifiesto implica cambiar ids que usan los scripts de verificación y los metadatos del punto 7; no se hizo en esta entrega.

Además, el diccionario tiene 75 tablas y el manifiesto 74. La diferencia es el efecto de `bancos_balance` y `bancos_resultados`, que existen como vistas en la web pero no como entradas separadas en el manifiesto.

## Límites al 2026-10-20

- La búsqueda es por palabras y sinónimos, no entiende preguntas complejas. Un concepto que no esté en `busqueda_sinonimos.json` depende de que aparezca en el nombre, la descripción o las columnas.
- Un sinónimo nuevo se agrega en `docs/busqueda_sinonimos.json` y se regenera el índice con `python3 scripts/generar_indice_busqueda.py`.

## Actualización 2026-10-24: ranking y erratas moderadas

La propuesta de rediseño pidió auditar la búsqueda existente antes de sustituirla. La búsqueda actual se conserva; se corrigió un resultado de ranking y se añadió tolerancia acotada a errores de escritura, sin incorporar un motor ni una dependencia externa.

- Una consulta `TPM` ahora prioriza `macro.tasas_corto_plazo`, que publica la tasa observada; `macro.expectativas_tpm` se mantiene como resultado apropiado al buscar «expectativas TPM».
- Se corrige una sola edición (inserción, eliminación o sustitución) para tokens de al menos cinco letras y solo cuando existe un candidato único en el índice. No se adivinan siglas breves ni se fuerzan correcciones ambiguas.
- Los resultados de esa ruta muestran «Coincidencia aproximada por escritura»; las coincidencias exactas conservan su ranking normal.
- `scripts/test_busqueda.js` contiene 26 consultas de aceptación (IDs, conceptos, fuentes, sectores, tildes, resultados vacíos y tres erratas). El 2026-10-24 la batería termina con cero fallos.
- Durante esta auditoría, el índice estaba desactualizado respecto al diccionario (el campo de origen `generado` decía 2026-10-22 y el diccionario 2026-10-24). Se regeneró; `scripts/generar_indice_busqueda.py --check` ahora compara el índice publicado con sus fuentes, y la batería/control quedaron añadidos a `web_audit.yml`.
- El workflow `contrato_publicado.yml` ahora reconstruye ese índice al regenerar el diccionario y lo verifica antes del push automático; una prueba de `test_contrato_publicadores.py` protege ese paso.
- Una prueba puntual con jsdom confirmó que al escribir «inflasión IPC» se muestra `macro.inflacion_ipc` junto con el texto «Coincidencia aproximada por escritura». Esto no reemplaza la prueba en navegador real.
- Tamaño medido del índice actual: 290.571 bytes sin compresión y 47.529 bytes con gzip de nivel 6. No representa necesariamente los bytes transferidos por los hostings.
- En la máquina de desarrollo (Node.js, VM, índice ya cargado), la consulta tuvo p50 8,68 ms y p95 9,21 ms después de calentar el vocabulario; la primera búsqueda fría midió 53,60 ms. No son mediciones de navegador ni de teléfono y falta repetirlas en dispositivos reales.

**Pendiente:** probar el buscador en navegador real y móvil; medir la descarga comprimida y la latencia en esos entornos; comprobar estados de carga/error con interacción; decidir si «buscar por institución» significa fuente oficial, institución listada como fila o ambas. Hoy el índice busca metadatos de objetos y columnas, no recorre los valores de todas las filas para localizar una institución.

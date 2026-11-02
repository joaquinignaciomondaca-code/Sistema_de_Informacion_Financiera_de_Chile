# Auditoría inicial de fuentes y cifras para el rediseño

**Fecha:** 2026-10-24.
**Alcance:** contraste de la afirmación sobre SUSESO, fuentes directas del catálogo, cifras de archivos y unidades de conteo durante la Fase 0. El nuevo reconciliador verifica los contratos vigentes entre sí; todavía no reemplaza todas las cifras editoriales escritas a mano ni una auditoría completa del contenido de cada objeto.

## Fuentes: separar descarga vigente de procedencia del padrón

El campo `fuente` de los 90 objetos de `docs/api/v2/catalog.json` tiene actualmente tres valores: `CMF`, `BCCh` y `SPensiones`. Eso describe las fuentes directas asignadas en el contrato, pero no agota la procedencia de cada campo del catálogo institucional.

El objeto CCAF es una excepción que requiere describir dos capas:

- `ccaf_balance` y `ccaf_resultados` se extraen del TXT trimestral IFRS de la CMF; `data_manifest.json` los identifica así.
- `ccaf_maestro` se genera desde una lista institucional mantenida en `ccaf/scripts/build_ccaf_maestro.py`. El manifiesto y `ccaf/README.md` indican que el universo inicial se construyó a partir de la lista SUSESO y del Registro de Valores CMF, y que las altas nuevas se incorporan desde el TXT IFRS de la CMF.
- `ccaf/README.md` declara que las memorias y estados financieros PDF de SUSESO son fuentes complementarias no usadas por el pipeline actual; los antiguos extractores PDF/OCR fueron retirados.

Por tanto, la frase web «SUSESO no entrega datos» era demasiado absoluta: confundía **fuente directa actual de archivos financieros** con **procedencia histórica/editorial del padrón CCAF**. La redacción ahora distingue esas funciones. No se añadió SUSESO como cuarta fuente de extracción periódica ni se afirma que hoy se descarguen sus estados financieros.

El contrato API ahora expone esa distinción de forma aditiva en `procedencia` para el objeto `ccaf_lista_entidades` (alias heredado `ccaf_maestro`) y en `resources[].sif.procedencia` del Data Package. `fuentes_directas_actuales` identifica CMF/TXT IFRS y limita expresamente su alcance a la detección e incorporación de altas; `procedencia_editorial.universo_inicial` registra la lista SUSESO y el Registro de Valores CMF. Se conserva `fuente: CMF` junto con `atribucion` para cita/condiciones de uso, pero se aclara que no significa que la base completa se descargue de CMF en cada corrida. La estructura inicial se versionó como 2.2.0; al añadir el estado de revisión de condiciones por fuente (CMF verificada; SUSESO pendiente de verificación) también al contrato, se amplió a 2.3.0. La prueba comprueba ambos estados y la igualdad entre catálogo y Data Package.

### Reutilización de la procedencia histórica

La revisión del repositorio encontró que `DATA_LICENSE.md` decía que SUSESO no era fuente de ningún objeto y que sus condiciones no aplicaban. Esa frase ya no se sostiene tras confirmar la procedencia editorial de `ccaf_maestro`. En el repositorio no quedó evidencia de un documento oficial de condiciones de SUSESO aplicable a la lista inicial. Se corrigieron `DATA_LICENSE.md`, `docs/api/README.md` y el alcance descrito en `pipelines/api/fuentes.py`: ahora se limita la conclusión de permiso a las fuentes directas con términos revisados y se deja explícitamente sin resolver la condición del insumo histórico SUSESO. Esto no afirma que SUSESO prohíba ni autorice la reutilización. Falta consultar y registrar la fuente oficial antes de cerrar ese pendiente.

## Cifras verificadas para el corte del catálogo

Fuente principal: `docs/api/v2/catalog.json`, `data_manifest.json`, `docs/api/v2/partitions/*.json` y el árbol de archivos `docs/outputs/`.

| Métrica | Valor actual | Definición / fuente |
|---|---:|---|
| Objetos del contrato | 90 | `catalog.totales.objetos` |
| Objetos con datos publicados | 86 | `catalog.totales.con_datos` |
| Objetos con filas | 85 | `catalog.totales.con_filas` |
| Filas | 19.777.522 | `catalog.totales.filas`; no es número de entidades ni de archivos |
| Bytes Parquet referenciados | 487.665.276 bytes (≈488 MB decimales; 465,1 MiB) | `catalog.totales.bytes` y 728 particiones referenciadas |
| Consultas precalculadas | 159 | `catalog.totales.consultas` y `api/v2/queries.json` |
| Data release | `2026-10-24.1681bebfe7ef` | `catalog.data_release` |
| Tamaño entero de `docs/` | 591,0 MiB | Medido localmente; incluye más que los Parquet catalogados |

El README decía «482 MB» para los 728 archivos del catálogo; se actualizó a **≈488 MB** con el valor actual del catálogo.

## Reconciliación de unidades: no confundir tabla ETL, objeto API y elemento de navegación

La diferencia de nombres se convirtió en un control reproducible, no en una resta manual. `scripts/build_metricas_publicadas.py` genera [`docs/metricas_publicadas.json`](../metricas_publicadas.json), y `--check` compara los artefactos de origen sin declararlos equivalentes:

| Contrato | Conteo | Qué representa |
|---|---:|---|
| `data_manifest.json` | 89 tablas ETL | Entradas del inventario de extracción; suman 19.777.522 filas. |
| `docs/api/v2/catalog.json` | 90 objetos: 79 publicados, 7 derivados y 4 sin particiones | Unidades lógicas del contrato. Hay 86 con archivo, 85 con filas y 1 Parquet vacío. |
| Catálogo de Descargas | 90 elementos = 74 principales + 15 fuera del foco + 1 oculto | El alcance editorial no elimina recursos. Una variante de corredoras cuenta como elemento, aunque se presenta junto a su lista base. |
| `docs/api/reconciliacion.csv` | 73 directos + 15 alias + 2 de origen compartido | Puente de nombres entre los objetos API y las 89 entradas ETL. |

Las 89 entradas ETL no son las mismas 89 filas no ocultas de Descargas, aunque hoy los números coincidan. La relación sí está explicada: `bancos_cmf_lineas` se convierte en dos objetos API y Descargas —balance B1/B2 y resultados R1—; los nombres alias no generan nuevos objetos. Los 90 IDs aparecen tanto en API como en Descargas, y cada objeto coincide en filas, bytes, número de particiones y rutas. El auditor también comprueba que balance y resultados usen archivos y filtros separados, no el Parquet combinado bajo ambos nombres.

Filas coinciden entre manifiesto, API y Descargas: **19.777.522**. Bytes API y Descargas coinciden: **487.665.276**. El resumen de alcance cuenta **19.677.258 filas / 485.772.310 bytes** en los niveles principales, **100.264 / 1.890.377** fuera del foco y un objeto oculto de cero filas y **2.589 bytes**. Por eso las cifras de sectores visibles excluyen ese pequeño archivo, mientras el total contractual lo incluye.

DuckDB usa además **4 Parquet compactos** sólo para acelerar algunas consultas: **3.662.207 filas materializadas y 43.916.543 bytes**. No se agregan a las filas/bytes únicos del catálogo ni a Descargas. La suma física del contrato más esas copias da 732 archivos, 23.439.729 filas y 531.581.819 bytes; sirve para describir recursos de runtime, **no cobertura única**. `docs/metricas_publicadas.json` separa estos tres valores.

El generador y su `--check` quedaron incluidos en `web_audit.yml` y en el workflow «Contrato derivado», para regenerar el artefacto después de los catálogos de API y descargas.

## Revisión de cifras manuales del README y de la API (corte 2026-10-24)

La tabla sectorial de `README.md` ahora contrasta elementos, filas y extremos de período con el artefacto común. `scripts/build_metricas_publicadas.py` valida las 15 filas de sector, el total y los cortes declarados por API, verifica que el calendario nombre los 18 workflows y concuerde con el reparto de horarios, además de generar `por_sector` en `docs/metricas_publicadas.json`. Las filas son sumas por objeto, no valores de registros globalmente únicos. En banca, el total sectorial **1.963.033** incluye las 41 filas de `bancos_lista_entidades`; `bancos_balance` (B1/B2: 722.931) y `bancos_resultados` (R1: 1.240.061) suman por separado **1.962.992**, igual que `bancos_cmf_lineas`, y no comparten archivos.

| Afirmación revisada | Evidencia vigente | Corrección aplicada |
|---|---|---|
| Consultas sugeridas | 159 en `docs/api/v2/queries.json` y prueba de contrato del 2026-10-24 | README y API README usan 159; se retiró 146 como cifra total. |
| Seguros y FFMM | Cortes de catálogo hasta 2026-09 | Tabla sectorial del README actualizada. |
| Factoring y leasing | `catalog.json`: 2009-03 a 2026-09 | README actualizado de junio a septiembre. |
| Pactos de seguros | Lectura DuckDB de `docs/outputs/seguros/pactos/*.parquet`: **11.371 filas**, 2016-11 a 2026-09; **218 filas en septiembre** | README corregido desde el snapshot de agosto (11.153 filas y 155 en agosto). `data_manifest.json` registra actualización 2026-10-21; el manifiesto específico de pactos tiene `updated_at=2026-10-16`. |
| Pactos de FI | Lectura DuckDB de `docs/outputs/fi/pactos/*.parquet`: **1.698 filas**, 55 períodos con operaciones; **40 filas en 2026-06** | README corregido de 777 a 1.698; los cierres 2026-03 y 2026-06 siguen expresamente cautelares. |
| Columnas sin valores | `esquemas.json`: **1**, `agf_lista_entidades.codigo_cmf` | API README corregido desde cinco. |
| Estados de PK en `claves.csv` | 48 `ok`, 15 `propuesta`, 22 `sin_clave` por filas idénticas y 1 `sin_datos` | API README corregido desde 28 propuestas y 9 tablas duplicadas. Son 63 recursos con clave en el Data Package; 27 `primaryKey: null` en API = 22 duplicados + 1 sin filas + 4 sin particiones. |
| Relaciones FK | 36 `ok`, 6 `sin_destino`, 1 `huerfanas` (3.604/7.962; 45,3 %) y 1 `sin_datos` | Desglose vigente añadido al API README. |
| Workflows | 18 archivos; 17 con `schedule`; `fi_cobertura_eeff.yml` sin horario | README actualiza 16/15 y agrega `contrato_publicado.yml` y `pensiones_carteras.yml`. El cron de pensiones no promete publicación: la ingesta depende de runner privado y gates. |
| Navegación de catálogo | Auditoría actual: 13 familias, 90 tablas y 90 opciones | Actualizado el comentario del comando en README (antes decía 75/75). |

El campo `filas_unicas` de `esquemas.json` no cuenta valores de fila distintos: suma las filas de cada ruta física Parquet una vez; `filas_por_objeto` puede volver a contar una ruta compartida. Esta distinción quedó documentada. También se quitó el claim «50 ms» sin medición de navegador y se retiraron del README los conteos de suites/pruebas que mezclaban inventario estático con ejecuciones de CI.

El valor **35.570** de FI es `reglas_verificadas` del cierre 2026-06 en `docs/outputs/fi/fi_eeff_control.json`, no el total histórico. La auditoría completa local (`.venv/bin/python -m fi.scripts.auditar_eeff`) recalculó **459.392 reglas** en **13.056 fondo-cierres**, con 0 fallas. Se dejó el valor de junio en README, pero ahora se lo nombra como reglas contables de ese cierre para no confundirlo con la cobertura histórica.

Las notas fechadas `cifras_oficiales_2026-10-20.md`, `portada_calidad_2026-10-23.md`, `portada_registro_2026-10-23.md`, `mapa_cifras_2026-10-23.md`, `revision_externa_2026-10-23.md`, `busqueda_por_pregunta_2026-10-20.md`, `recorte_visual_industrias_2026-10-20.md`, `api_publica_factibilidad_2026-10-22.md`, `ruta_api_v1_2026-10-22.md`, `auditoria_seguros_2026-10-07.md` y `cobertura_repos_pactos_2026-10-07.md` se conservan como snapshots de sus cortes, con aviso histórico o actualización claramente separada; no se reescriben para aparentar que reflejaban el release actual. Esta auditoría y los manifests vigentes son la referencia de cifras actuales.

## Parquet fuera de las particiones API v2: no equivale a archivos huérfanos

En `docs/outputs/` hay **805 archivos `.parquet` físicos**, mientras que los manifiestos de partición de `docs/api/v2/` referencian 728. Los otros **77 archivos (61.048.363 bytes)** no forman parte de esas particiones, pero el contraste de referencias del repositorio los clasifica así:

| Grupo fuera de API v2 | Cantidad | Evidencia de otro uso |
|---|---:|---|
| `outputs/bancos/cmf_b1_b2_r1/*/lineas.parquet` | 56 | Manifiesto propio `docs/outputs/bancos/cmf_b1_b2_r1/manifest.json`; el último período también figura en `data_manifest.json`. |
| `outputs/macro/series/*.parquet` | 13 | Manifiesto propio `docs/outputs/macro/series/manifest.json` y código de actualización de series BCCh. |
| `outputs/sql_query/*.parquet` | 4 | Manifiestos propios y `docs/js/duckdb_client.js` los carga para consultas SQL. |
| Muestras factoring/leasing y registros FFMM | 4 | Referencias en READMEs, scripts de publicación/actualización, auditorías y pruebas. |

Por tanto, **“fuera de las particiones de API v2” no significa “no usado”**. No se borró ningún archivo; la auditoría sí encontró referencias de mantenimiento/consumo para los cuatro grupos. `scripts/audit_pages_capacity.py` ahora reconcilia en cada `web_audit.yml` los 805 Parquet físicos: 728 de API/Descargas, 4 auxiliares SQL, 69 en manifiestos separados y 4 muestras/registros con referencias de mantenimiento; falla ante solapes, rutas ausentes o archivos sin categoría. Es un inventario estático: no demuestra que cada URL responda en el hosting ni que un usuario la consuma. Cualquier limpieza futura debe contrastar también el contrato de descargas, el pipeline y las rutas históricas, no solo el catálogo API.

## Cambios de precisión aplicados

- `docs/index.html`: reemplazó la afirmación absoluta sobre SUSESO por una distinción entre las tres fuentes directas actuales y la procedencia mixta del catálogo CCAF; aclara que balances/resultados CCAF vienen de CMF y que el pipeline actual no consume PDF financieros de SUSESO.
- `README.md`: explica la misma diferencia de fuentes, corrige 482 MB a ≈488 MB y distingue tablas ETL, objetos API y elementos de navegación.
- `docs/api/README.md`: corrigió un ejemplo desactualizado que mostraba el Parquet bancario combinado bajo balance/resultados; ahora documenta los archivos filtrados separados y enlaza la reconciliación.
- `docs/notas/cifras_oficiales_2026-10-20.md`: se marcó como snapshot histórico y enlazó el corte vigente.
- `scripts/auditar_personas_publicadas.py`: dejó de exigir el texto incorrecto «SUSESO no entrega datos» y ahora comprueba que la web explique la procedencia CCAF y la fuente CMF de sus estados financieros.
- `data_manifest.json`, `scripts/build_api.py` y `scripts/build_contrato.py`: exponen la fuente directa limitada a altas y la procedencia editorial inicial del maestro CCAF; `scripts/test_contrato.py` comprueba que el objeto de catálogo y el recurso del Data Package coincidan y que ambas capas estén completas.
- `DATA_LICENSE.md`, `docs/api/README.md` y `pipelines/api/fuentes.py`: quitan la afirmación de que las condiciones SUSESO no aplican; distinguen términos verificados para fuentes directas de la procedencia histórica pendiente de revisión. No se añade una autorización ni se concluye que haya una prohibición.
- `scripts/build_metricas_publicadas.py` + `docs/metricas_publicadas.json`:  consolidan las definiciones y verifican IDs, rutas, filas, bytes, estados, filtros bancarios y totales entre manifiesto, API y Descargas; los workflows regeneran y comprueban el resultado.
- `docs/index.html`: los contadores `data-alcance` son datos de respaldo que `portada.js` recalcula desde `DOWNLOAD_CATALOG.alcance`; se cambió la etiqueta «conjuntos» por «elementos» donde se cuentan entradas de Descargas, para no presentar la variante como una tabla distinta. Se aclaró la unidad de 89 ETL frente a 90 objetos del diccionario/API y el split de `bancos_cmf_lineas`.
- El bloque principal verifica **74 elementos**, **19.677.258 filas**, **485.772.310 bytes** y 99,5 % del total; coincide con `fuentes.descargas.principal` del artefacto común y las filas/bytes exactas con `DOWNLOAD_CATALOG.alcance.visible`. El resto de las cifras por nivel/sector/periodo se recalcula desde ese mismo catálogo; una prueba contrasta también cada valor de respaldo HTML con el valor calculado.
- El bloque de modalidad cuenta los **90 objetos del diccionario** (89 automáticos, 1 híbrido, 0 manuales). El artefacto común distingue esos objetos de las 89 entradas ETL; se agregó esa explicación junto a la división bancaria. La imagen social comunica 90 objetos y más de 19 millones de filas como dos totales, no afirma que los 90 tengan filas: el contrato confirma 86 con archivo y 85 con filas.
- Las cifras de repetición en la Guía siguen viniendo del artefacto `estado_claves.js`, no del total de la reconciliación de objetos; su semántica es distinta y no se suman a la cobertura.

## Revisión de descripciones filtradas de banca (2026-10-25)

Al probar el Data Package contra los 90 objetos para la ficha genérica, se encontró que las descripciones de `bancos_balance` y `bancos_resultados` heredaban la primera frase común del manifiesto (`Filas fuente de B1 consolidado, B2 individual y R1 consolidado`) y luego añadían el filtro de cada recurso. Las rutas y conteos ya estaban separados, pero esa combinación podía leerse como si cada recurso incluyera los tres tipos.

`_descripcion_objeto()` en `scripts/build_api.py` ahora omite esa frase compartida únicamente en esos recursos filtrados; preserva el resto de la descripción y añade la selección explícita: B1/B2 excluye R1, y R1 excluye B1/B2. No se alteraron filtros, filas, archivos ni montos.

`test_fichas_candidatas.py` comprueba para los 90 IDs que los 86 recursos Data Package correspondan al catálogo y al descriptor en rutas, filas totales, bytes y SHA-256 por partición; además exige descripciones distintas y explícitas para esos dos recursos. Verificación local: `build_api.py --check`, `test_fichas_candidatas.py` y `test_contrato.py --check` pasan; esta última revisó 908 rutas, 728 Parquet y 159 consultas.

## Validación ejecutada

- `python scripts/build_metricas_publicadas.py --check`: coherencia confirmada para ETL/API/Descargas, rutas, filas, bytes, filtros bancarios y compactos SQL.
- `.venv/bin/python scripts/build_esquemas.py --check`, `.venv/bin/python scripts/build_reconciliacion.py --check`, `python scripts/build_download_catalog.py --check` y `python scripts/build_contrato.py --check`: contratos al día; 89/89 entradas ETL cubiertas.
- `python -m unittest pipelines.auto.tests.test_contrato_publicadores`: 11/11 pruebas.
- `.venv/bin/python scripts/build_estado_claves.py --check`: al día (90 objetos, 22 con repetición, 230.288 filas repetidas).
- `.venv/bin/python scripts/auditar_mcp.py --check`: 8/8 comprobaciones; presupuesto de herramientas 191/1.000 tokens.
- `node scripts/test_busqueda.js`: 26/26 consultas.
- `.venv/bin/python scripts/auditar_personas_publicadas.py --verbose`: pasó 6 comprobaciones sobre los Parquet y el texto publicado.
- `.venv/bin/python scripts/audit_web_full.py`: activos y enlaces válidos; detecta 732 archivos/23.439.729 filas del runtime (incluidas las copias SQL, no 732 tablas únicas).
- `NODE_PATH=/tmp/sif-jsdom/node_modules node scripts/audit_interfaz_dom.js`: **119/119** comprobaciones en tres ejecuciones consecutivas. Incluye comparación de los valores de respaldo HTML con el catálogo calculado, totales visibles con `metricas_publicadas.json` y los 89/90 objetos; la comprobación inicial del gráfico también se ejecuta antes de las interacciones.
- YAML de `.github/workflows/contrato_publicado.yml` y `web_audit.yml` parsea sin errores; `python scripts/build_indice_notas.py --check`, `python scripts/generar_indice_busqueda.py --check` y `git diff --check`: OK. `python scripts/audit_pages_capacity.py` pasó con `docs/` en 591,0 MiB y clasificó los 805 Parquet físicos sin faltantes: 728 API/Descargas, 4 auxiliares SQL, 69 bajo manifiestos separados y 4 muestras/registros.
- El nuevo `build_metricas_publicadas.py --check` contrasta la tabla de 15 sectores del README (elementos, filas, total y extremos de período), los 18 nombres del calendario y el reparto de 17 con horario/1 sin horario; también valida las 159 consultas. Pasa.
- `build_esquemas.py --check`, `build_api.py --check`, `build_contrato.py --check`, `build_download_catalog.py --check` y `build_resultados.py --check`: al día; 63/86 recursos tienen `primaryKey`, 27 objetos API lo omiten y el contrato tiene 159 consultas.
- `test_contrato.py --autoprueba`: 908 rutas HTTP, 0 × 404; 1.474 columnas; 105 vistas + 4 temporales; 159 consultas; 728 archivos; procedencia CCAF y estados de reutilización alineados entre catálogo y Data Package; autoprueba negativa aprobada. Identifica la única columna sin valores.
- `auditar_contrato.py`: 185 piezas coherentes en versión 2.3.0; catálogo, particiones, resultados y Data Package alineados.
- `audit_automatizacion.py`: 0 problemas; comparación estática de `.github/workflows/*.yml` con README: 18 nombres, 17 con cron y uno sin horario. `audit_navigation.py`: 13 familias, 90 tablas y 90 opciones.
- Lectura local DuckDB de ambos conjuntos de pactos confirmó los totales descritos arriba; auditoría completa FI: 13.056 fondo-cierres y 459.392 reglas, 0 fallas.

## Pendiente

- La revisión de cifras vigentes en README, README de API y notas recientes quedó completada; los snapshots anteriores se preservan con su corte histórico. El comentario de `index.html` ahora dice 23 activos locales (el auditor cuenta 23, antes decía 22).
- Los tamaños/tiempos que quedan en comentarios HTML son mediciones de profiling, no cifras de cobertura, y no se revalidaron contra el hosting. Localmente, JSON de cardinalidad: 17.305 B crudo/1.677 B gzip; índice: 290.571/47.529 B; DuckDB wasm: 18.105.915/4.197.834 B y worker: 265.771/68.578 B. Esto no prueba lo que se transfiere: el informe pudo usar Brotli u otra versión. No se cambia el comentario «3,8 MB + 68 KB» sin captura de red actual.
- Revisar las condiciones de reutilización de las fuentes históricas/editoriales por separado; el campo `procedencia` documenta origen y método, no establece una autorización legal nueva.
- Aunque los 77 Parquet fuera de API v2 tienen referencias de manifiestos o código, revisar accesibilidad y consumo real de las rutas antiguas antes de cualquier política de retención.
- Completar pruebas de navegación, rutas, descargas y SQL en navegador real; las pruebas DOM no sustituyen una prueba de usuario.

# Serie IFRS CMF para Factoring y Leasing: extracción y publicación automática

El backfill descarga el histórico del índice CMF para los RUT del catálogo de Factoring/Leasing. La fuente es [Estados financieros IFRS en TXT](https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php), con archivos `ver_archivo.php?inicio=AAAAMM&termino=AAAAMM`. El índice se consulta en cada corrida; los archivos trimestrales ya completos se recuperan de la caché de Actions y solo se descargan los cierres nuevos/fallidos.

## Comportamiento del workflow

`.github/workflows/factoring_leasing_backfill.yml` ejecuta `factoring_leasing/scripts/backfill_ifrs.py`, conserva el estado por período y, **solo cuando todos los períodos anunciados por el índice están completos**, llama a `factoring_leasing/scripts/publish_backfill.py`. El publicador consolida dos Parquets y los añade a `docs/outputs/factoring_leasing/`; actualiza DuckDB, el explorador lateral, el selector y el diccionario; ejecuta auditorías; y el workflow comitea los cambios a la misma rama que ejecutó la corrida. El push automático de datos no vuelve a disparar el workflow porque el filtro de rutas excluye los outputs generados. Si falta un período, un Parquet o hay errores en el resumen, el publicador no toca la web. Cada run deja además un artifact de la extracción con retención de 90 días.

El `schedule` diario de GitHub solo se ejecuta desde la rama por defecto (`main`). En una rama de PR, el workflow corre al modificar su código o manualmente con `workflow_dispatch`, no cada día. Tras incorporar el workflow a la rama por defecto, los nuevos cierres se procesan y publican en los siguientes runs diarios. La corrida de Actions no fusiona un PR.

## Qué se conserva y qué no se afirma

El TXT contiene filas `periodo;rut;nombre;I/C;moneda;cuenta;valor;taxonomia;estado`. Se conservan todas las cuentas ESF (balance) y ER (resultados) sin sumar, agregar ni deduplicar filas. Se mantienen separados tipo I/C, moneda y taxonomía. Los importes no enteros quedan con su texto literal y `valor_archivo = NULL`; **no** se fuerzan a cero ni se adivina un separador decimal. Las repeticiones bajo la misma clave/contexto llevan ordinal `repeticion_contexto` y no se suman. El saldo/resultado no se presenta como un agregado contable o como resultado trimestral si el archivo no codifica esa semántica de forma inequívoca.

El universo es el catálogo local de 28 RUT (incluye segmentos mixtos y 2 automotrices). La fuente tiene filas para una parte del catálogo; ausencia en el TXT no demuestra que una entidad carezca de EEFF en otra publicación CMF. El TXT trae cuerpo de RUT sin DV; el DV/nombre del catálogo se conserva como referencia actual, no como identidad histórica certificada. Se retienen las unidades y monedas originales sin conversión FX ni división por miles.

La publicación lleva advertencia visible de extracción automática **sin cotejo integral**; el cotejo previo de dos muestras comprueba solo esas filas, no certifica el histórico completo. Este proceso no sustituye la validación independiente de nombres/RUT históricos, taxonomías, escala/unidad ni periodicidad de resultados.

## Web pública y PR

El job comitea los nuevos Parquets y catálogos web en la rama que ejecuta. Un PR abierto muestra el cambio en sus archivos/vista previa; no actualiza la rama pública hasta fusionarse. El repositorio no tiene GitHub Pages configurado (`has_pages: false` en la última revisión); por eso la publicación al directorio `docs/` no crea por sí sola un sitio público nuevo. Un hosting externo puede desplegar esa carpeta al recibir el cambio fusionado; si se necesita GitHub Pages, primero hay que configurarlo expresamente.

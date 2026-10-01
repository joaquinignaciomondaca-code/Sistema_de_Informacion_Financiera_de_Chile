# Factoring y Leasing — catálogo, muestras y serie IFRS CMF

## Datos de entidades y muestras cotejadas

`docs/outputs/factoring_leasing/factoring_leasing_maestro.{json,parquet}` contiene 32 registros del catálogo local al 2026-10-01 (la lista crece sola: el flujo IFRS agrega las sociedades de factoring o leasing que empiezan a reportar; la cifra vigente está en `data_manifest.json`). Su dígito verificador no certifica que la identidad/vigencia esté cotejada contra el padrón CMF.

Las muestras previas se mantienen separadas:

- `factoring_leasing_eeff_muestra_cmf.parquet`: cuatro cuentas de balance cotejadas para dos entidades y sus cierres 2022.
- `factoring_leasing_resultados_muestra_cmf.parquet`: dos cuentas de resultados acumulados desde enero, cotejadas para las mismas entidades/períodos.

La muestra prueba que esas filas coinciden con el archivo CMF; no valida todos los períodos o entidades.

**Retiradas de la web (2026-09-28):** sus cifras son idénticas a las de la serie IFRS (misma entidad y período; la muestra en miles de pesos, la serie en pesos), por lo que aparecían como tablas duplicadas. Los Parquet y los scripts de cotejo se conservan como evidencia de auditoría, pero ya no tienen vista DuckDB, carpeta en el explorador, entrada en el visor/diccionario ni en `data_manifest.json`.

## Serie histórica IFRS completa de la fuente TXT

El workflow `.github/workflows/factoring_leasing_backfill.yml` obtiene los cierres publicados por CMF, mantiene caché por período y, al completarse **todos** los períodos del índice, arma y publica dos archivos distintos:

- `factoring_leasing_balance_serie_ifrs_cmf.parquet`: todas las filas `ESF*` del TXT para los RUT del catálogo.
- `factoring_leasing_resultados_serie_ifrs_cmf.parquet`: todas las filas `ER*`.
- `factoring_leasing_balance_serie_ifrs_cmf_metadata.json`: cobertura, faltantes, corrida y advertencias.

El publicador actualiza automáticamente DuckDB, el explorador (una carpeta independiente por tabla), el selector, diccionario, `data_manifest.json` y cache-busting de la interfaz; corre auditorías y comitea los cambios a la rama que ejecutó Actions. No publica si falta un cierre, error o partición. La programación diaria solo corre cuando el workflow está en la rama por defecto `main`; el PR abierto puede ejecutarse por cambio de código o `workflow_dispatch`.

### Compuerta contable, relectura y publicación en la rama

* **Compuerta antes de escribir.** `publish_backfill.py` aplica a la serie completa la misma cuadratura que
  usan AGF, securitizadoras y CCAF (`pipelines/auto/cuadratura.py`), trimestre por trimestre: activos =
  pasivos + patrimonio, las identidades del estado de resultados y una cobertura mínima de balances
  verificables (si cambian las glosas de los totales y casi ninguno se puede leer, no se publica a ciegas).
  Un descuadre aislado no detiene: queda contado en el bloque `cuadratura` de la metadata y lo marca la
  auditoría de la web (`scripts/auditar_eeff_ifrs.py`); una falla en bloque no publica nada y deja la corrida en
  rojo.
* **Cierres reeditados.** La caché guarda un par de Parquet por trimestre y no los vuelve a bajar... salvo
  que la CMF los reedite: el índice muestra «(actualizado: dd/mm/aaaa hh:mm)» junto a cada archivo y, si esa
  fecha es posterior a la descarga guardada, el trimestre se baja otra vez. Mientras no se refresque, la serie no
  se publica (fail-closed) y la copia anterior sigue publicada.
* **Publicación en la rama.** El commit del workflow lleva solo los dos Parquet y su metadata. Los catálogos de la
  web, `data_manifest.json` y el catálogo de descargas los editan todos los publicadores, así que se regeneran
  sobre la cabeza vigente de la rama en cada intento (`python factoring_leasing/scripts/publish_backfill.py
  --solo-catalogos`) en lugar de viajar en el commit, donde chocaban con la edición de otro publicador y la serie
  quedaba sin publicar («8 intentos por contención»).
* **Convenciones.** El parseo del TXT es el compartido (`pipelines/auto/ifrs_txt.py`) y desde el esquema v2 la
  tabla trae `orden`. Se mantienen, a propósito, `tipo_balance` como `I`/`C` literal y los nombres
  `valor_archivo`, `moneda_archivo` y `repeticion_contexto`: AGF, securitizadoras y CCAF usan
  `individual`/`consolidado`, `valor`, `moneda` y `repeticion`, de modo que una misma sentencia no sirve para
  ambas familias sin ajustar esos nombres.

### "Ganancia (pérdida)" repetida en resultados

No es un duplicado del extractor: el formato IFRS de la CMF trae esa etiqueta hasta 3 veces por estado, siempre con el mismo valor.

| estado_financiero | repeticion_contexto | dónde |
|---|---|---|
| ERFG (por función) / ERNG (por naturaleza) | 1 | resultado tras operaciones continuadas |
| ERFG / ERNG | 2 | total de la atribución controladora + no controladora |
| ERI (resultado integral) | 1 | línea inicial del resultado integral |

Hay 900 estados (899 ERFG + 1 ERNG: Tanner 2021-03 reportó por naturaleza). En 2009-03 Interfactor usa la taxonomía antigua ("Ganancia (Pérdida)", hasta 3 repeticiones y sin ERI). Sumar la cuenta sin filtrar triplica la utilidad. Para una fila por estado: `lower(cuenta) = 'ganancia (pérdida)' AND estado_financiero IN ('ERFG','ERNG') AND repeticion_contexto = 1`. Esa consulta está como chip en la web y la genera `publish_backfill.profit_queries`.

La extracción conserva las cuentas tal como llegan: tipo individual/consolidado, moneda, taxonomía y texto original. Los importes no enteros permanecen como texto con `valor_archivo = NULL`; las repeticiones llevan ordinal. No hay conversión de moneda/unidades, agregación, deduplicación ni suma. La serie representa lo que se encontró en el TXT para **28 de los 32 RUT del catálogo** (cifras al 2026-10-01; la vigente está en `factoring_leasing_balance_serie_ifrs_cmf_metadata.json`), no necesariamente todos los EEFF disponibles de cada entidad. El DV se asocia desde el catálogo actual; no es una validación histórica completa. La etiqueta de la web advierte que no se cotejó integralmente cada cifra.

Los extractores y publicadores heredados de otros balances/notas retirados siguen bloqueados; la serie nueva es una ruta de publicación independiente, en dos tablas crudas con sus límites declarados.

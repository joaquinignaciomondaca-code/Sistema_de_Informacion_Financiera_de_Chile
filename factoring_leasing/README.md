# Factoring y Leasing — catálogo, muestras y serie IFRS CMF

## Datos de entidades y muestras cotejadas

`docs/outputs/factoring_leasing/factoring_leasing_maestro.{json,parquet}` contiene 28 registros del catálogo local. Su dígito verificador no certifica que la identidad/vigencia esté cotejada contra el padrón CMF.

Las muestras previas se mantienen separadas:

- `factoring_leasing_eeff_muestra_cmf.parquet`: cuatro cuentas de balance cotejadas para dos entidades y sus cierres 2022.
- `factoring_leasing_resultados_muestra_cmf.parquet`: dos cuentas de resultados acumulados desde enero, cotejadas para las mismas entidades/períodos.

La muestra prueba que esas filas coinciden con el archivo CMF; no valida todos los períodos o entidades.

## Serie histórica IFRS completa de la fuente TXT

El workflow `.github/workflows/factoring_leasing_backfill.yml` obtiene los cierres publicados por CMF, mantiene caché por período y, al completarse **todos** los períodos del índice, arma y publica dos archivos distintos:

- `factoring_leasing_balance_serie_ifrs_cmf.parquet`: todas las filas `ESF*` del TXT para los RUT del catálogo.
- `factoring_leasing_resultados_serie_ifrs_cmf.parquet`: todas las filas `ER*`.
- `factoring_leasing_balance_serie_ifrs_cmf_metadata.json`: cobertura, faltantes, corrida y advertencias.

El publicador actualiza automáticamente DuckDB, el explorador (una carpeta independiente por tabla), el selector, diccionario, `data_manifest.json` y cache-busting de la interfaz; corre auditorías y comitea los cambios a la rama que ejecutó Actions. No publica si falta un cierre, error o partición. La programación diaria solo corre cuando el workflow está en la rama por defecto `main`; el PR abierto puede ejecutarse por cambio de código o `workflow_dispatch`.

La extracción conserva las cuentas tal como llegan: tipo individual/consolidado, moneda, taxonomía y texto original. Los importes no enteros permanecen como texto con `valor_archivo = NULL`; las repeticiones llevan ordinal. No hay conversión de moneda/unidades, agregación, deduplicación ni suma. La serie representa lo que se encontró en el TXT para **24 de 28 RUT del catálogo**, no necesariamente todos los EEFF disponibles de cada entidad. El DV se asocia desde el catálogo actual; no es una validación histórica completa. La etiqueta de la web advierte que no se cotejó integralmente cada cifra.

Los extractores y publicadores heredados de otros balances/notas retirados siguen bloqueados; la serie nueva es una ruta de publicación independiente, en dos tablas crudas con sus límites declarados.

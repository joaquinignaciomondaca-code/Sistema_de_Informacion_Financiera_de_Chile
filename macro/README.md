# Macroeconomía — BCCh SIETE

Tres tablas mensuales publicadas en `docs/outputs/macro/` (2014-01–2026-09 en el corte actual): tasas y rendimientos, divisas y mercado, precios y actividad. **El último mes de una tabla no significa que todas sus series tengan dato ese mes.** En el corte actual, IMACEC y TCR terminan en 2026-07, IPC y cobre en 2026-08, mientras USD/CLP y UF llegan a 2026-09. Los valores pendientes permanecen nulos; no se imputan.

Fuente técnica: catálogo de 23 códigos BCCh en `scripts/pipeline_stream_macro_bcch.py`, consultado por `bcchapi`. La actualización diaria (`.github/workflows/macro.yml`) usa secrets de Actions y reconsulta desde el último mes extraído; series mensuales con rezago se reconsultan desde su último mes observado, con retroceso máximo de tres meses anteriores al último corte de tabla, **no desde 2014**. Las respuestas no nulas se fusionan sobre el baseline; errores de API no deben escribir staging. Se valida continuidad, rangos, JSON/Parquet y no regresión contra lo publicado. En Actions, lo que pasa la validación se publica solo (commit al repositorio, con reintento si otro bot publicó al mismo tiempo).

Pruebas locales offline (sin secretos): `python -m unittest discover -s macro/tests -q` y `python -m macro.scripts.audit_macro_bcch --input-dir docs/outputs/macro`. Para ejecutar descargas hace falta configurar `BCCH_EMAIL` y `BCCH_PASSWORD` en el entorno (en Actions: `USER_BCCH` y `PASSWORD_BCCH` como secrets); no se guardan en el repositorio. La auditoría de integridad y plausibilidad **no sustituye cotejar valores históricos con la fuente primaria**. Una revisión retroactiva publicada fuera de la ventana de tres meses requiere backfill explícito y revisión antes de actualizar el sitio.

## Catálogo amplio de series (`scripts/series_bcch.py`)

53 series del BCCh en formato largo, con su frecuencia original: tasas (TPM, TIB, swaps SPC en pesos y UF, BCP y BCU de 1 a 30 años), tipo de cambio (dólar, euro, TCM, TCM-5, TCM-X y TCR), UF, UTM, IPC, Imacec (total, no minero, minería, comercio y servicios), PIB trimestral, mercado laboral (desocupación, ocupados, asalariados y fuerza de trabajo), cobre, oro, plata, IPSA, reservas internacionales, Treasury 10 años, tasa de la Fed, deuda pública/PIB y expectativas (EEE y EOF).

- Salida: `docs/outputs/macro/series/<AAAA>.parquet` (fecha, periodo, clave, serie_id, valor) con `series/manifest.json`, y `macro_series_catalogo.parquet` (nombre, grupo, unidad, frecuencia, título oficial, cobertura y estado por serie).
- Usa directamente la API REST SIETE (`GetSeries`). Cada serie se consulta solo desde su último dato menos una ventana de revisión: 10 días en diarias, 6 meses en mensuales y 13 meses en trimestrales.
- Nada publicado se borra. Una serie con error o inexistente no bloquea a las demás: queda con su estado en el catálogo y un aviso en Actions. Si fallan todas, no se escribe nada.
- Para agregar una serie basta con sumar una línea a `CATALOGO`; la primera corrida trae su historia desde 2014.
- Pruebas sin red: `python -m unittest macro.tests.test_series_bcch`.

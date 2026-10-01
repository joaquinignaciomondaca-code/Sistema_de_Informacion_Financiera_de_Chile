# Macroeconomía — BCCh SIETE

23 tablas temáticas publicadas en `docs/outputs/macro/`, una por indicador o familia de indicadores del Banco Central (2014 en adelante), más el catálogo de series. Cada tabla viene en la frecuencia en que el BCCh publica sus series (diaria, mensual o trimestral) y sus columnas llevan nombres autoexplicativos con indicador, detalle y unidad (`dolar_observado_clp_por_usd`, `rendimiento_bono_uf_10_anos_pct`, `oro_usd_por_onza_troy`). Ninguna fila depende de un código opaco: los códigos SIETE viven solo en `macro.series_catalogo`.

| Carpeta | Tablas |
|---|---|
| Tasas de interés | `tasas_corto_plazo` (TPM, TIB) · `swaps_camara` (SPC pesos 90d–2a, UF 1a) · `curva_bonos_pesos` (BCP 2/5/10a) · `curva_bonos_uf` (BCU 1–30a) · `inflacion_implicita` (BCP−BCU 5/10a, calculada) |
| Tipo de cambio | `dolar_observado` · `euro_observado` · `tipo_cambio_multilateral` (TCM, TCM-5, TCM-X) · `tipo_cambio_real` (TCR, TCR-5) |
| Precios y reajustes | `uf` · `utm` · `inflacion_ipc` (índice, var. mensual y anual) |
| Actividad económica | `imacec` (total, no minero, minero, comercio, servicios) · `pib_trimestral` |
| Mercado laboral | `mercado_laboral` (desocupación, ocupados, asalariados, fuerza de trabajo) |
| Materias primas | `cobre` (BML diario y referencia mensual) · `metales_preciosos` (oro, plata) |
| Sector externo y fiscal | `reservas_internacionales` · `tasa_referencia_fed` · `deuda_publica_pct_pib` |
| Expectativas | `expectativas_inflacion` (EEE 11/23m) · `expectativas_tpm` (EEE 11/23m) · `expectativas_operadores` (EOF 12m) |
| Catálogo de series | `series_catalogo` (51 series: código SIETE, nombre, unidad, frecuencia, cobertura y estado) |

**Descarga diaria o mensual.** En la pestaña Descargas, las tablas diarias ofrecen un selector de frecuencia para el CSV/Excel: *Diaria* (la tabla tal cual) o *Mensual · cierre*, donde cada columna toma el valor del último día del mes con dato y se acompaña de la fecha de ese dato (`<columna>_fecha_dato`). El Parquet original es siempre diario.

**La última fecha de una tabla no significa que todas sus columnas tengan dato ese día.** Dentro de una misma tabla cada columna llega hasta donde el BCCh la haya publicado; los valores pendientes quedan nulos y se completan solos cuando el BCCh publica.

## Flujo (`.github/workflows/macro.yml`, diario 10:00 UTC)

1. `scripts/series_bcch.py` — descarga incremental de las 51 series nativas vía API REST SIETE (`GetSeries`). Cada serie se consulta solo desde su último dato menos una ventana de revisión (10 días en diarias, 6 meses en mensuales, 13 meses en trimestrales). Nada publicado se borra; una serie con error no bloquea a las demás (queda con su estado en el catálogo). Salida: `series/<AAAA>.parquet` (fecha, periodo, clave, serie_id, valor) + `series/manifest.json` + `macro_series_catalogo.parquet`. Las particiones `series/` son la materia prima interna; la web no las expone.
2. `scripts/build_tablas_tematicas.py` — pivota las series nativas en las 23 tablas temáticas (`TABLAS` es la especificación: id, frecuencia, descripción y mapa serie → columna). Verifica fila a fila que no se pierde ninguna observación y refresca `data_manifest.json`. Sin acceso a la API.
3. `scripts/audit_macro_bcch.py` — integridad (columnas declaradas, fechas únicas y ordenadas, sin futuras), rangos plausibles de indicadores clave y cobertura de las 51 series. Si falla, no se publica nada.
4. Commit al repositorio; después `scripts/build_macro_web.py` mantiene la web sincronizada.

La sección de la web (árbol, visor, diccionario, ERD, vistas SQL y vocabulario) se genera con `python3 scripts/build_macro_web.py` desde la misma especificación `TABLAS`; `--check` falla si está desactualizada. Para agregar una serie: sumar una línea a `CATALOGO` en `series_bcch.py`, asignarla a una tabla en `TABLAS` (o crear una), documentar su columna en `SIGNIFICADO` de `build_macro_web.py` y regenerar.

Pruebas locales offline (sin secretos): `python -m unittest discover -s macro/tests -q`, `python -m macro.scripts.build_tablas_tematicas --check` y `python -m macro.scripts.audit_macro_bcch`. Para descargar hace falta `BCCH_EMAIL` y `BCCH_PASSWORD` en el entorno (en Actions: secrets `USER_BCCH` y `PASSWORD_BCCH`); no se guardan en el repositorio. La auditoría de integridad y plausibilidad **no sustituye cotejar valores históricos con la fuente primaria**. IPSA y Treasury 10 años no se incluyen: la API del BCCh no los entrega (código -50, datos de proveedores externos).

## Historial

- 2026-09-30: retiradas `macro.tasas_rendimientos`, `macro.divisas_mercado`, `macro.precios_actividad` (resúmenes mensuales que mezclaban temas) y `macro.series` (formato largo con claves opacas), junto con `pipeline_stream_macro_bcch.py`, `daily_macro.py` y `publish_macro.py`. Las sustituyen las 23 tablas temáticas. Propuesta y motivación en `docs/notas/rediseno_seccion_macro_2026-09-30.md`.

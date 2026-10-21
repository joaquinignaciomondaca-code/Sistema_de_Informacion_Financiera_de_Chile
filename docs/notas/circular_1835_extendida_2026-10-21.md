# Circular 1835 completa y vistas analíticas — 2026-10-21

## Implementación

El catálogo y el extractor ahora cubren los registros B.1–B.14 del anexo técnico, en el orden del manual. B.7 aparece en dos tablas lógicas (derivados y pactos), con el mismo título oficial y etiquetas de tipo diferenciadas. Se conservan las tablas completas y se agregan proyecciones sin agregación de filas para B.1, B.2, B.4, B.5, B.7 (derivados), B.12 y B.13. Las columnas proceden de `seguros/scripts/vistas_1835.py` y la ficha oficial sigue disponible en el Diccionario de Datos.

La publicación oculta valores personales en B.12–B.14, y en B.4/B.13 reemplaza el rol del inmueble por `property_id`. El detalle está en `seguros/README.md` y en los metadatos de cada tabla.

## Prueba real de publicación

El workflow [39569977464](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/39569977464) terminó correctamente. Revisó 22 cierres, desde 2024-12 hasta 2026-09, y publicó los archivos que la CMF entregó. B.14 contiene 6.518 filas. B.12 y B.13 aparecen con cero filas en los 22 cierres; sus tablas y esquemas quedan registrados, pero no se generaron particiones Parquet sin datos. Las vistas simplificadas B.12/B.13 también quedan vacías hasta que la fuente informe detalle.

Las vistas B.1, B.2, B.4, B.5 y B.7 se reconstruyeron desde los Parquet completos ya publicados; no hubo que volver a descargar los 119 cierres históricos. Se mantienen como Parquet, que es el formato consumido directamente por DuckDB-WASM. Un segundo formato no aporta valor práctico al catálogo estático actual y duplicaría el almacenamiento/transferencia.

## Alertas pendientes de aclaración con la CMF

En diez archivos de compañías generales, entre 2024-12 y 2025-03, se encontró un registro tipo `6` en archivos B.11 (`e`) o B.14 (`g`). La ficha técnica disponible sólo documenta los tipos 1, 2 y 3 para esos archivos. El extractor **no interpreta ni descarta silenciosamente** el registro: conserva la alerta y excluye el archivo de esa compañía, que queda listado en `docs/outputs/seguros/manifest.json`. Los otros archivos y períodos se publican. No se debe reutilizar la semántica del tipo 6 de B.7 (pactos) para B.11/B.14: son archivos distintos.

La sonda real de 2024-12 ([run 39632257071](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/39632257071)) encontró tres archivos generales afectados (uno `e`, dos `g`). Las líneas tipo 6 tienen el largo completo esperado: 178/178 bytes para `e` y 300/300 para `g`; no parecen truncadas, pero su significado sigue sin documentarse. No se leyeron ni expusieron sus campos.

Luego, la auditoría de entradas de los 22 cierres ([run 39635877769](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/39635877769)) registró los conteos de archivos por prefijo en `docs/outputs/seguros/manifest.json`, campo `archivos_fuente_por_prefijo`. En **cada uno de los 22 cierres**, los ZIP de vida y generales tenían cero archivos `r` (B.12) y `v` (B.13). Así queda confirmado que los ceros B.12/B.13 reflejan ausencia en los ZIP fuente de los 22 meses, no un fallo de detección del parser. La auditoría solo contó nombres de archivo; no leyó ni publicó registros adicionales.

Se requiere confirmación de la CMF o una versión actualizada del anexo antes de integrar el tipo 6 con seguridad. Dejé preparado, sin enviar, un [borrador de consulta técnica](consulta_cmf_registro_tipo6_1835.md). El manifiesto conserva los nombres de los archivos afectados y las alertas del proceso.

## Verificación

- `test_formato_1835`, `test_inventario_1835` y `test_registros_2024`: OK; el último usa registros sintéticos con el período inicial real 2024-12 y prueba privacidad, esquemas y conservación de filas.
- `test_vistas_1835`: OK; prueba el backfill analítico desde Parquet sin descargar ZIP.
- Pruebas de privacidad: OK para supresión de identidades personales en B.12–B.14.
- `audit_web_full.py`: OK; catálogos, manifiestos, columnas, navegación y ERD validados.
- No se accedió a los datos originales de los diez archivos excluidos; no se inventaron interpretaciones para el tipo no documentado.

# Reproducibilidad

Archivos planos para consultar y auditar aspectos concretos de la publicación,
sin depender del JavaScript de la web. Se generan con:

```
python3 scripts/construir_reproducibilidad.py
```

Se publican junto al sitio, pero no todos son consumidos directamente por la
interfaz. `diccionario.csv` y `diccionario.json` se derivan del mismo
`docs/js/data_dictionary.js` que alimenta el Diccionario; los demás son artefactos
complementarios para inspeccionar archivos y cobertura.

| Archivo | Qué trae y de dónde sale |
|---|---|
| `diccionario.csv` | Cada columna de cada tabla: tipo, rol, significado y criterio contable (1640 columnas en 90 tablas). Los campos descriptivos/editoriales proceden del diccionario mantenido en el repositorio. |
| `diccionario.json` | El mismo contenido estructurado en JSON, para cargarlo con pandas o DuckDB. |
| `inventario_fuentes.csv` | Ruta, tamaño y SHA-256 de los archivos Parquet/JSON de datos y metadata bajo `docs/outputs`; se incluye el conteo de filas cuando está disponible. Excluye `indice_busqueda.json`, que es un artefacto de interfaz con su propio control. |
| `cobertura_por_periodo.csv` | Registros por tabla y periodo, leídos de los manifiestos de publicación. |
| `validacion_resumen.csv` | Fuente, norma, modalidad, fecha/rango, periodos, registros y ruta por objeto. Combina metadatos del manifiesto/diccionario con conteos de manifiestos; **no contiene resultados de pruebas, tolerancias ni una certificación de calidad**. |

## Cómo se verifica un archivo

1. Descarga un Parquet de la pestaña Descargas.
2. Calcula su SHA-256: `sha256sum archivo.parquet` (o `shasum -a 256` en macOS).
3. Compáralo con la columna `sha256` de `inventario_fuentes.csv` para esa ruta.

La coincidencia indica que el archivo coincide con el artefacto descrito en este
inventario. No demuestra que su contenido sea semánticamente correcto ni que una
versión anterior siga disponible en el hosting.

## Alcance y límites

Estos archivos documentan aspectos de la base publicada; no son una capa
armonizada para investigación y sus controles no constituyen un sello general
de calidad. Los campos editoriales (por ejemplo, significado, norma o modalidad)
y las mediciones derivadas de manifiestos se distinguen por su fuente; no se
debe inferir una propiedad no documentada a partir de filas o de una clave.

`scripts/construir_snapshot_academico.py` puede armar una copia local con fecha,
hashes y documentación. Ejecutarlo no publica el snapshot, no crea un DOI y no
garantiza recuperar archivos históricos que no se hayan conservado aparte.

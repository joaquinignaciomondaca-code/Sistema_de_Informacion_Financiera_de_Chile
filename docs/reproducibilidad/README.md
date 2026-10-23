# Reproducibilidad

Archivos planos para auditar y citar la base sin depender del JavaScript de la
web. Se generan con:

```
python3 scripts/construir_reproducibilidad.py
```

y se publican junto al sitio, así que lo que ves aquí es exactamente lo que usa
la interfaz.

| Archivo | Qué trae |
|---|---|
| `diccionario.csv` | Cada columna de cada tabla: tipo, rol, significado y criterio contable (1647 columnas en 90 tablas). |
| `diccionario.json` | Lo mismo, en JSON, para cargarlo con pandas o DuckDB. |
| `inventario_fuentes.csv` | Todos los Parquet y manifiestos publicados, con peso y SHA-256. Permite verificar que una copia descargada no fue alterada. |
| `cobertura_por_periodo.csv` | Registros por tabla y periodo, según los manifiestos publicados. |
| `validacion_resumen.csv` | Una fila por tabla: fuente, norma, modalidad de procesamiento, rango cubierto, periodos, registros y archivo. |

## Cómo se verifica

1. Descarga un Parquet de la pestaña Descargas.
2. Calcula su SHA-256: `sha256sum archivo.parquet` (o `shasum -a 256` en macOS).
3. Compáralo con la columna `sha256` de `inventario_fuentes.csv` para esa ruta.

Si coinciden, estás usando el mismo archivo que publica el proyecto.

## Alcance

Estos archivos documentan la base tal como se publica: no son una capa
armonizada para investigación. La versión congelada y citable —con DOI, fecha de
corte y registro de cambios— se arma con `scripts/construir_snapshot_academico.py`
y se deposita aparte; la referencia se publica en la sección *Citación y versión
académica* de la web.

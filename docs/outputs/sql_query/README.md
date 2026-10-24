# Parquet compactos para consultas SQL

Estos archivos son copias compactas de ciertos objetos semánticos, generadas por
`scripts/build_sql_compact_parquets.py` para reducir aperturas de archivos remotos
en DuckDB-Wasm. La interfaz SQL los usa como fuente de lectura; **no son archivos
de descarga ni objetos adicionales del catálogo**.

Los manifiestos de cada objeto, el catálogo de Descargas y sus períodos, filtros,
conteos y particiones no cambian: siguen describiendo y enlazando los Parquet
originales. El manifiesto `.manifest.json` junto a cada copia registra sus fuentes,
conteo de filas, esquema y huellas para detectar desincronizaciones.

| Vista SQL | Contenido de la copia compacta |
| --- | --- |
| `bancos_balance` | Solo familias CMF B1 y B2 (el filtro queda materializado desde su manifiesto filtrado). |
| `bancos_resultados` | Solo familia CMF R1 (su manifiesto filtrado es independiente). |
| `ffmm_cartera_nacional` | Cartera nacional de fondos mutuos, todas las particiones publicadas. |
| `seguros_acciones` | Acciones de aseguradoras, todas las particiones publicadas. |

No se combina B1+B2+R1 en una misma copia bancaria ni se publica una copia
combinada bajo los nombres de balance o resultados. Se puede regenerar todo con:

```sh
python scripts/build_sql_compact_parquets.py
```

Y revisar que los artefactos estén sincronizados con sus fuentes con:

```sh
python scripts/build_sql_compact_parquets.py --check
```

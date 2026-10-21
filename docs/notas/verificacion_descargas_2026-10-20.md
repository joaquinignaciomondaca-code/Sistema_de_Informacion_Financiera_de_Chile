# Verificación de descargas contra el manifiesto — 2026-10-20

Punto 5 de la checklist. Dos niveles de prueba:

1. **Parquet publicados vs manifiesto** (`scripts/verificar_parquet_manifiesto.py`): filas y esquema de
   cada archivo, para las 74 tablas de `data_manifest.json`.
2. **Descargas CSV y Excel generadas por el sitio** (sitio simulado con `scripts/servir_sitio_local.mjs`,
   motor DuckDB-Wasm real, botones y funciones del propio panel de descargas).

## 1. Parquet vs manifiesto

- **66 de 74 tablas OK.** Filas y esquema coinciden en todas sus partes.
- **Total de filas en Parquet: 13.483.676**, igual que el manifiesto. Ningún archivo se pierde al publicarse.
- **8 tablas con esquema distinto entre partes** (todas de Seguros, Circular 1835). La parte más reciente
  tiene columnas con nombres distintos a las históricas (p. ej. `rut_emisor` → `nro_rut`,
  `tasa_emision_pct` → `tasa_emision`, `custodia` → `custodia_inv`). La parte de 2026 pasa de 23 a 105 columnas en `seguros_renta_fija`.

| Tabla | Parte con esquema distinto | Filas que una descarga completa puede omitir |
|---|---|---:|
| seguros_renta_fija | 2026-09 | 105.569 |
| seguros_bienes_raices | 2026-09 | 35.833 |
| seguros_derivados | 2026 | 48.847 |
| seguros_extranjeros | 2026 | 52.092 |
| seguros_acciones | 2026 | 8.307 |
| seguros_control_inversiones | 2026 | 7.925 |
| seguros_fondos_mutuos | 2026 | 5.580 |
| seguros_pactos | 2026 | 1.463 |

## 2. Descargas del sitio (motor real en el navegador)

### Fallo silencioso en la serie completa de Seguros

- `SELECT * FROM seguros_pactos` devuelve **9.908 filas** sin error, pero la tabla tiene **11.371**
  (`count(*)` y pedir solo columnas comunes también dan 11.371).
- Con `ORDER BY` la misma consulta falla con `schema mismatch in glob`. Sin `ORDER BY` no hay error.
- Las filas que faltan son **exactamente** las del archivo con esquema distinto (1.463 = 2026).
  Lo mismo ocurre en `seguros_control_inversiones` (103.483 de 111.408; faltan 7.925) y en
  `seguros_acciones` (100.711 de 109.018; faltan 8.307).
- Consultas que leen columnas nuevas (p. ej. `rut_emisor` sobre `seguros_renta_fija`) fallan con error de esquema.
  `SELECT count(*)` y filtros por `periodo` siguen funcionando, por eso el arranque y las pruebas simples no lo detectan.

**Impacto:** el botón "Serie completa · CSV/Excel" de estas tablas entrega un archivo incompleto,
sin aviso. Es el caso más grave de los que he verificado: el usuario cree haber descargado todo.

### Formato correcto en el caso sano

Descarga de `macro_uf` (4.676 filas, 3 columnas):

| Verificación | CSV | Excel (.xlsx) |
|---|---|---|
| Filas de datos | 4.676 (= Parquet) | 4.676 (= Parquet) |
| Cabecera | `fecha;periodo;uf_valor_clp` (= Parquet) | igual |
| Valores | 0 celdas distintas del Parquet | — |
| Codificación | UTF-8 con BOM | — |
| Separador | `;` (para Excel en Chile) | — |
| Hojas | — | 1 (`macro_uf`) |

## 3. Observaciones

- **`bancos_cmf_lineas`** (1.962.992 registros) figura en el manifiesto con 56 particiones mensuales. Sus filas
  son la suma de `bancos_balance` (722.931) y `bancos_resultados` (1.240.061), así que no tiene vista ni descarga
  propia, y el total la cuenta una sola vez. Es coherente con el README; se documenta en `cifras_oficiales`.
- El script de verificación ahora sigue el `manifest.json` de la carpeta cuando `file_parquet` apunta a un solo
  mes. Antes marcaba la tabla como error por un falso positivo.

## 4. Decisión pendiente

No cambié el pipeline ni la web en este punto, porque hay que decidir cómo unificar el esquema:

- **A. Normalizar el esquema de 2026 al histórico** en el pipeline de Seguros (renombrar columnas y regenerar).
  Es la solución de datos más limpia, pero requiere el mapeo de cada columna nueva; hay que confirmarlo con el origen.
- **B. Leer con `union_by_name=true`** en el cliente. Evita la pérdida y los errores, pero las columnas
  equivalentes quedan duplicadas (una con NULL en los años antiguos y otra con NULL en los nuevos).
- **C. Guardia inmediata en la exportación**: comparar `count(*)` con las filas devueltas y avisar o bloquear
  si no coinciden. No corrige los datos, pero evita entregar archivos incompletos mientras se decide A o B.

Recomendación: **C ahora** y **A** en el pipeline, con **B** solo si la normalización no es posible.

## Limitaciones

- Medí la exportación completa solo en `seguros_pactos`, `seguros_control_inversiones` y `seguros_acciones`.
  Para las otras cinco tablas con esquema distinto la pérdida es la esperada según el Parquet, pero no la medí en el navegador.
- Probé CSV y Excel solo en `macro_uf`. Los formatos de las tablas con esquema distinto no tienen una diferencia de
  formato, sino de filas.
- Todo se midió en el sitio simulado en local, no en la URL pública.

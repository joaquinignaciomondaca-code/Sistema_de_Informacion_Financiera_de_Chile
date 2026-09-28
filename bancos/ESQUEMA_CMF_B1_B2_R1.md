# Esquema analítico CMF para estados financieros bancarios

## Alcance confirmado

| Archivo público | Modelo CMF | Estado | Perímetro |
|---|---|---|---|
| B1 | MB1 | Balance | Consolidado global |
| B2 | MB2 | Balance | Individual |
| R1 | MR1 | Estado de resultados | Consolidado global |

La muestra CMF de 2026-07 contiene B1, B2 y R1 para las instituciones del ZIP; no se observó R2/MR2. No se debe etiquetar R1 como resultado individual ni inferir que R2 está disponible.

## Grano recomendado para tablas analíticas

Mantener dos tablas largas en vez de una tabla ancha con una columna por cuenta:

- **`bancos_balance_cuentas`**: una fila por período, institución, modelo/perímetro y código de cuenta. Incluye B1 y B2, distinguidos mediante `modelo_cmf` y `nivel_consolidacion`.
- **`bancos_resultados_cuentas`**: una fila por período, institución y código de cuenta de R1, marcado como consolidado global.

El primer artefacto de extracción produce ambas familias en un JSONL común de revisión. Esta es una zona de staging, no un output registrado en `data_manifest.json` ni un dataset publicado.

### Columnas comunes propuestas

| Columna | Regla |
|---|---|
| `id` | Clave determinística compuesta por período, código institucional, modelo CMF, cuenta y ocurrencia de esa cuenta. |
| `periodo`, `fecha_corte` | Mes informado y último día del mes. |
| `codigo_institucion` | Código leído del encabezado y del nombre del archivo CMF. |
| `nombre_institucion_fuente` | Texto del encabezado original. |
| `rut`, `razon_social` | Enriquecer desde el maestro solo cuando el cruce de identidad esté validado; no inferir el RUT desde el nombre. |
| `tipo_estado` | `balance` o `resultados`. |
| `familia_archivo_fuente`, `modelo_cmf` | B1/MB1, B2/MB2 o R1/MR1. |
| `nivel_consolidacion` | `consolidado_global` o `individual`. |
| `codigo_cuenta`, `glosa_cuenta` | Código CMF y glosa obtenida del modelo correspondiente dentro del ZIP. |
| `rubro`, `linea`, `item` | Códigos jerárquicos del modelo CMF; `linea` no es la posición de la fila en el TXT. |
| `tipo_linea` | Se conserva la fila fuente; el prototipo etiqueta `total` ante glosa explícita `TOTAL`, `subtotal` cuando el modelo tiene descendientes de esa cuenta y `detalle` en los demás casos. |
| `numero_fila_fuente` | Posición física original en el TXT, separada de la jerarquía de cuentas. |
| `fuente_url`, `sha256`, `archivo_fuente` | Procedencia y reproducibilidad del dato. |

### Importes

- B1/B2: la extracción inicial conserva el arreglo `importes_fuente_raw` y su representación decimal exacta. No asigna todavía nombres de moneda ni suma esos campos de forma general. La forma observada en el TXT debe cotejarse con la versión aplicable del modelo CMF antes de crear columnas semánticas.
- R1: conserva el único importe de la línea; antes de calcular variaciones mensuales, confirmar si el período corresponde a flujo mensual o acumulado del ejercicio.
- En la capa curada, renombrar las medidas con significado oficial y mantener también una representación fiel al dato fuente.

## Totales, subtotales y análisis

No descartar las cuentas que representan totales o subtotales. Clasificarlas con el plan CMF una vez verificado y advertir en las consultas que sumar simultáneamente una línea padre con sus cuentas descendientes puede duplicar montos. Las vistas resumidas para gráficos deben ser derivadas y no reemplazar las filas de cuenta.

## Estado de validación y publicación

`bancos/scripts/extract_cmf_bank_lines.py` valida que cada institución incluida tenga un B1, B2 y R1 único, conserva todas las filas y sus campos originales, y guarda resultados en `.local-data/review/`. No escribe en `docs/outputs/`, no actualiza el manifest ni publica cifras. El extractor mapea glosas y rubro/línea/ítem desde los tres modelos del ZIP; también incluye la fila fuente física en `numero_fila_fuente`.

### Muestra julio de 2026

La ejecución de revisión de [GitHub Actions](https://github.com/joaquinignaciomondaca-code/monitor-financiero-chile/actions/runs/36362212221) procesó **18 instituciones**, 54 archivos B1/B2/R1 y **35.028 filas de cuentas**: 12.762 B1, 144 B2 y 22.122 R1.

- Banco de Chile, B1 `100000000` (**TOTAL ACTIVOS**): la suma diagnóstica de los cuatro campos fuente es **$54.712.553.524.383** y coincide con la hoja `Est. Situación Financ. Bancos` del XLSX (**54.712.553,524383 MM$**).
- Banco de Chile, R1: **11 cuentas** coinciden exactamente con importes de la hoja `Est. del Resultado Bancos`, entre ellas `590000000` (utilidad del ejercicio) por **$750.034.790.494** y `594000000` (resultado de los propietarios) por **$750.034.662.608**.
- B2 quedó extraído y separado como individual; ese XLSX no ofrece un cotejo individual en la fila consolidada usada para este control.

Antes de cualquier backfill se deben terminar: (1) asignar significado oficial a los campos monetarios B1/B2, (2) revisar la regla derivada de total/subtotal/detalle contra el plan CMF, (3) validar el cruce a RUT/razón social, y (4) confirmar el tratamiento temporal de R1 (mensual o acumulado del ejercicio). La salida actual es una muestra de revisión, no una publicación ni autorización para backfill.

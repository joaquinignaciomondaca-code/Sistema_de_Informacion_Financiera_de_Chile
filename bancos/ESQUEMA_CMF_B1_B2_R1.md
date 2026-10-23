# Esquema analítico CMF para estados financieros bancarios

## Alcance confirmado

| Archivo público | Modelo CMF | Estado | Perímetro |
|---|---|---|---|
| B1 | MB1 | Balance | Consolidado global |
| B2 | MB2 | Balance | Individual (en lo publicado, solo ~8 cuentas por banco; ver «Estado al 2026-10-01») |
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
| `rut`, `razon_social` | Se completan desde el maestro de bancos por `codigo_institucion` (el código viene en el nombre del archivo y en la cabecera). No se infiere el RUT desde el nombre. |
| `tipo_estado` | `balance` o `resultados`. |
| `familia_archivo_fuente`, `modelo_cmf` | B1/MB1, B2/MB2 o R1/MR1. |
| `nivel_consolidacion` | `consolidado_global` o `individual`. |
| `codigo_cuenta`, `glosa_cuenta` | Código CMF y glosa obtenida del modelo correspondiente dentro del ZIP. |
| `rubro`, `linea`, `item` | Códigos jerárquicos del modelo CMF; `linea` no es la posición de la fila en el TXT. |
| `tipo_linea` | Se conserva la fila fuente; el prototipo etiqueta `total` ante glosa explícita `TOTAL`, `subtotal` cuando el modelo tiene descendientes de esa cuenta y `detalle` en los demás casos. |
| `numero_fila_fuente` | Posición física original en el TXT, separada de la jerarquía de cuentas. |
| `fuente_url`, `sha256`, `archivo_fuente` | Procedencia y reproducibilidad del dato. |

### Importes

- B1/B2: la extracción conserva el arreglo `importes_fuente_raw`, su representación decimal exacta (`importes_fuente_decimal`) y agrega `importe_clp` con el total de la cuenta ya sumado (ver «Importes normalizados»). **Significado (resuelto 2026-10-01):** los cuatro importes son, en el orden del archivo, el monto en moneda chilena no reajustable, en moneda reajustable por IPC, en moneda reajustable por tipo de cambio y en moneda extranjera (Manual del Sistema de Información de la CMF, archivos MB1 y MB2, Circular 2.295/2021), en pesos. **Su suma es el total de la cuenta**: sumando los cuatro, `TOTAL ACTIVOS` = `TOTAL PASIVOS Y PATRIMONIO` en 989 de los 991 balances banco-mes publicados (diferencia máxima $1); columna por columna no cuadra, como corresponde (la diferencia por moneda es la posición neta del banco).
- R1: un único importe en pesos, que se publica además como número en `importe_clp`. **Es el acumulado del ejercicio** (de enero al mes informado), no el flujo del mes (resuelto 2026-10-01): crece mes a mes dentro del año en el 97,2 % de los 759 pares de meses consecutivos de bancos con utilidad anual positiva, y se reinicia en enero en 69 de 69 casos (el total del sistema, código 999, pasa de enero a diciembre multiplicado por 13–17). Para el resultado de un mes hay que restar el mes anterior del mismo año.
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

Lo anterior describe la fase de muestra de revisión (julio de 2026). Era una condición previa a cualquier backfill terminar: (1) asignar significado oficial a los campos monetarios B1/B2, (2) revisar la regla derivada de total/subtotal/detalle contra el plan CMF, (3) validar el cruce a RUT/razón social, y (4) confirmar el tratamiento temporal de R1.

## Estado al 2026-10-01

- **Publicación.** `bancos/scripts/publish_cmf_bank_period.py` (workflow `bancos_cmf_mensual.yml`, días 1, 11 y 21) publica una partición Parquet por mes desde 2022-01, solo si pasa el gate: tres archivos por institución, `TOTAL ACTIVOS` de B1 y las cuentas `590000000`/`594000000` de R1 cotejados contra el XLSX de la CMF. Hoy hay 55 particiones (2022-01 a 2026-07). El commit lleva solo las particiones; `data_manifest.json` se regenera después sobre la cabeza de la rama (`--solo-data-manifest`), como en los demás publicadores.
- **Formato del archivo.** Los TXT de la CMF son TSV (campos separados por tabulador); los importes llevan ceros a la izquierda hasta un ancho fijo de 15 dígitos, pero el archivo **no** es de ancho fijo.
- **Resuelto:** (1) significado de los cuatro importes y (4) tratamiento temporal de R1; ver «Importes».
- **B2 no es un balance individual completo.** El manual de la CMF llama MB2 al balance individual, pero lo publicado trae solo unas 8 cuentas por banco y mes (adeudado por bancos y colocaciones comerciales, de vivienda y de consumo; 144 filas B2 frente a 12.762 de B1 en julio de 2026). No usarlo para reconstruir el balance individual.
- **Código 999.** `TOTAL SISTEMA FINANCIERO` viene como una institución más: al sumar sobre `codigo_institucion` hay que excluirlo o se duplica el sistema.
- **Resuelto 2026-10-22:** (3) el cruce a RUT. `rut` y `razon_social` se publicaban nulos desde 2022-01 (una consulta por RUT devolvía 0 filas sin error, hallazgo 16 de la ruta de la API); ahora el extractor los toma del maestro de bancos y `bancos/scripts/completar_entidades.py` reparó las 56 particiones publicadas.
- **Pendiente:** (2) contrastar la regla total/subtotal/detalle (`tipo_linea`) con el plan de cuentas.

## Importes normalizados (2026-10-23)

La sección de Banca llegó al sitio con un defecto de lectura: el Visor mostraba
`001345990724750` (el campo del archivo CMF, 15 dígitos con ceros a la
izquierda y a veces con coma decimal) porque no había ninguna columna numérica
que sumar ni formatear. Se agregaron **dos columnas**, sin tocar el grano ni las
columnas de origen:

| Columna | Tipo | Contenido |
|---|---|---|
| `importe_clp` | `BIGINT` | En R1, el importe en pesos. En B1/B2, la suma de los cuatro componentes por moneda, es decir, el total de la cuenta. |
| `formato_monto_fuente` | `VARCHAR` | `decimal_coma` (15 dígitos con coma decimal, 2022-01 → 2024-05) o `entero_15` (15 dígitos enteros, 2024-06 → 2026-08). |

- **Cómo se calcula.** `importe_clp` = suma exacta con `Decimal` de
  `importes_fuente_decimal`; nunca se reinterpreta el texto crudo. Los
  4.131.785 valores de la serie no tienen centavos, así que la conversión a
  entero es exacta.
- **Relleno de lo publicado.** `bancos/scripts/normalizar_importes.py` agrega
  las columnas a las particiones existentes en un archivo temporal, verifica
  filas y valores y recién entonces reemplaza. Resultado: **56 particiones,
  1.962.992 filas, 0 importes incorrectos**; una segunda corrida reescribe 0.
  `--check` recorre todas las particiones sin red.
- **Extractor.** `bancos/scripts/extract_cmf_bank_lines.py` calcula las dos
  columnas al extraer, de modo que las particiones nuevas ya nacen legibles.
- **Ejemplos verificados.** R1 2024-06, cuenta `411000000` (INGRESOS POR
  INTERESES), Banco de Chile: `1542552118136` (`entero_15`). B1 2022-01,
  `TOTAL ACTIVOS`: `50164403436446` (`decimal_coma`), suma de
  `26.458.735.676.131,00` + `18.194.231.752.989,00` + `86.353.276.604,00` +
  `5.425.082.730.722,00`.
- **Lo que no cambia.** `importes_fuente_raw` e `importes_fuente_decimal` siguen
  publicadas: son la representación fiel del archivo, y el marcador de formato
  existe para no perder de vista qué mitad de la serie usa coma decimal.

## Identidades cotejadas (2026-10-23)

El maestro dejó de estar «pendiente de validación»:

- `bancos/scripts/validar_identidades.py` compara las 41 filas contra
  `docs/outputs/bancos/registro_cmf_banco.json` (copia fechada del registro
  BANCO de la CMF, vigentes y no vigentes). Resultado: **30 cotejadas, 7
  agregados sectoriales, 4 declaradas** (027, 816, 916 y 927). Cero filas fuera
  del registro.
- `bancos/scripts/corregir_identidades.py` aplicó los **9 RUT** que no existían
  en el registro y fija el formato único del maestro: `rut_dv` sin puntos e
  igual a `rut` más el dígito verificador. `--check` falla si reaparece un punto
  o un RUT conocido por la CMF.
- `--check` de ambos scripts corre **sin red** sobre la copia publicada, así que
  la compuerta es reproducible en cualquier máquina y en CI.

# Auditoría forense — Patrimonios Separados (consolidado 2014-2026)

Fecha: 2026-09-27 · Base auditada: consolidado de corridas 3 y 4 (`consolidar_tramos.py`,
tramos 2014-2017, 2018-2021, 2022-2026) · 1.450 balances, 78.678 líneas EEFF, 715 filas de notas.
Complementa `AUDITORIA_2026-09-26.md` (audit v2 formal). Aquí se buscan **cosas raras**:
series por PS, identidad, duplicados, signos, desplazamientos de columna.

## Resumen ejecutivo

| # | Hallazgo | Severidad | Filas afectadas | Tipo |
|---|----------|-----------|-----------------|------|
| 1 | **Identidad fragmentada**: el mismo PS aparece bajo dos `id_patrimonio` según cómo lo etiquetó la CMF ese trimestre (`BSECS-10` vs `Patrimonio Separado N°10`, `BBICS-L` vs `N°12`, `BTRA1-23` typo de `BTRA1-3`, `PS-112` typo de `PS-12`, `VBOLS-A1`, `BVOLS-1`, Fintesa `PS-2` = `BSABN-ABH`) | **ALTA** | 83 ids → ~66 PS reales; 20+ series partidas | Canonización de id |
| 2 | **Columna “Nota” leída como monto**: en tablas con columna de notas sin encabezado, el número de nota queda en `monto_mclp` y el monto real en `monto_anterior_mclp` (ej. Volcom 2026-06 bonos = −18; Banchile 2017 = −10) | **ALTA** | 967 líneas / 70 balances; 33 resúmenes con deuda_bonos = ±10..40 | Parser |
| 3 | **PDF de otro PS bajo la etiqueta equivocada**: Transa `BTRA1-5` 2016-09 es el PDF de `BTRA1-4` (mismos montos, registro 236) | MEDIA | 1 | Fuente CMF |
| 4 | **Mismo PDF en dos períodos**: Security PS-2 2019-03 es el mismo archivo (sha256 idéntico) que 2019-12 | MEDIA | 1 | Fuente CMF |
| 5 | **Valores idénticos en trimestres consecutivos** (distinto archivo): BICE PS-12/PS-21/PS-6 2025-12 = 2026-03 | MEDIA | 3 | Fuente CMF o parser de período |
| 6 | **Duplicado del mismo período bajo dos etiquetas**: Volcom `BVOLS` y `VBOLS-A1` 2020-03 (mismos montos) | BAJA | 1 | Identidad |
| 7 | `periodo_inconsistente` en 21 balances; 14 son BICE con desfase de exactamente un año → probable lectura del año comparativo en el encabezado | MEDIA | 21 | Detector de período (verificar con PNG) |
| 8 | `nro_registro_cmf` no fiable en algunos PDFs: Security PS-4 y PS-6 muestran registro 270 (el de PS-3) desde 2022-06; EF PS-7/PS-10/PS-11/PS-15 muestran “1” | MEDIA | ~40 | Parser (regex de registro captura otro número) |
| 9 | Montos no enteros (`4.15264`, `4619.6`, `22.5`) en 16 líneas: restos de OCR y de la glosa “c/u a” | BAJA | 16 | Parser |
| 10 | Saltos de activos >3× entre trimestres consecutivos: 9 casos, 8 explicables por liquidación/prepago (último período o rebote posterior), 1 (Security PS-14 2018-06→2019-12) es hueco de 5 trimestres | INFO | 9 | Real |
| 11 | Excedente neto del período nulo en 8-22 % de balances por año (mayor en 2014-2017, OCR) | INFO | 190 | Cobertura de líneas |

Lo que **sí está bien**: 0 duplicados (id, período); 0 balances `ok` en cobertura sin resumen;
activos siempre > 0; `total_activos_musd` consistente con tipo de cambio (ratio 0,984-1,0003);
26-95 líneas por balance (ninguno vacío); ningún monto > 1e9 M$ (sin errores de unidad);
1.446/1.450 cuadran (los 4 restantes ya diagnosticados).

## Detalle por hallazgo

### 1. Identidad fragmentada (el más importante)

Evidencia por `nro_registro_cmf` impreso en el PDF y por continuidad de activos:

| Administradora | ids que son el mismo PS | Registro CMF | Evidencia |
|---|---|---|---|
| Security | `bsecs_2`≡`ps_2`, `bsecs_3`≡`ps_3`, `bsecs_4`≡`ps_4`, `bsecs_5`≡`ps_5`, `bsecs_6`≡`ps_6`, `bsecs_7`≡`ps_7`, `bsecs_9`≡`ps_9`, `bsecs_10`≡`ps_10`, `bsecs_13`≡`ps_13`, `bsecs_14`≡`ps_14` | 228, 270, 319, 341, 367, 420, 495, 510, 582, 866 | Los huecos son complementarios: `bsecs_*` falta 2018-03/06, `ps_*` falta 2018-09…2019-06. BSECS-10: 13,19 MM (2017-12) → 12,80 (2018-03, como PS-10) → 11,89 (2018-09, como BSECS-10) |
| BICE | `bbics_f`≡`ps_6` (322), `bbics_l`≡`ps_12` (351), `bbics_u`≡`ps_21` (437) | | Series `bbics_*` terminan 2025-09, `ps_*` empiezan 2025-12; registro coincide |
| Transa | `btra_1_2`≡`ps_2` (199, hueco 2020-12), `btra_1_23`≡`btra_1_3` (202, hueco 2016-06), `btra_1`(2014-12→2015-09) = ¿`btra_1_?`; ver PDF | | |
| Fintesa | `ps_2`≡`bsabn_abh` (huecos 2015-03/09, activos 4,9 MM continuos) | | |
| Volcom | `bvols_1` (2019-12) ≡ `bvols`; `vbols_a1` 2020-03 duplica `bvols` 2020-03 | | |
| EF | `ps_112` (2026-06) ≡ `ps_12` (42,5 MM continua con 42,7 MM) | | |

Consecuencia: cualquier serie temporal por PS en la web queda cortada; conteo “83 PS” está inflado (~66 reales).

**Solución propuesta (reproducible):** tabla `securitizadoras/data/alias_patrimonios.csv`
(`rut_administradora, id_observado, id_canonico, evidencia, fuente, autor, fecha`) aplicada en
`derivar_resumen`/consolidación, con regla automática previa: dentro de una administradora, si dos ids
comparten `nro_registro_cmf` validado y sus períodos no se solapan (o los solapados tienen montos idénticos),
se unifican; el id observado se conserva en columna `codigo_emision_segun_cmf` para trazabilidad.
Prohibido unir por “parecido de números” sin registro ni continuidad exacta.

### 2. Columna Nota → monto (desplazamiento)

Patrón: `|monto_mclp| ≤ 40`, `monto_mclp ≠ 0`, `nota` vacía, `|monto_anterior_mclp| ≥ 1.000`.
967 líneas en 70 balances (Banchile 656, Fintesa 195, Volcom 90, Security 11, BCI 6, Santander 6, BICE 2, EF 1).
Ejemplo: Volcom BVOLS 2026-06 “Obligaciones por títulos de deuda (largo plazo)” → `monto=-18`, `anterior=93.407.732`.
Los totales no se ven afectados (por eso cuadran), pero `deuda_bonos_*`, `valores_negociables`, gastos, etc. sí:
33 resúmenes tienen deuda de bonos = −10…−22.

**Solución:** en `parse_eeff_lineas`, cuando la fila tiene ≥3 números y el primero es entero pequeño (1-60)
sin separador de miles mientras los demás sí lo tienen (o superan 1.000), tratarlo como `nota` y desplazar
columnas; añadir test con fixture Volcom/Banchile. Re-derivar resumen.

### 3-6. Errores de fuente (CMF publica el archivo equivocado)

- `96765170_btra_1_5` 2016-09: activos 2.408.826 = `btra_1_4` 2016-09; registro impreso 236 (= BTRA1-4). La serie 1-5 va 4,85 MM → **2,41** → 4,58 MM.
- `96847360_ps_2` 2019-03: `pdf_sha256 490a05c2…` idéntico al de 2019-12; `periodo_segun_pdf`=2019-12.
- BICE `ps_12`, `ps_21`, `ps_6`: 2025-12 y 2026-03 con activos/excedentes exactamente iguales (archivos distintos). Verificar PNG; si el PDF de 2026-03 es el de 2025-12, marcar.
- Volcom 2020-03 listado dos veces (BVOLS y VBOLS-A1).

**Solución:** nuevo estado de cobertura `pdf_de_otro_periodo` / `pdf_de_otro_ps` / `pdf_duplicado`, decidido
por reglas objetivas (sha256 repetido; `periodo_segun_pdf` ≠ período con montos idénticos a otro período;
registro impreso ≠ registro del id). La fila se conserva en cobertura con el motivo y **no** entra al resumen;
se documenta en README como error de fuente con URL.

### 7. `periodo_inconsistente` (21)

BICE (`bbics_l` 2018-06, 2019-06, 2019-12, 2024-03/06/09, 2025-03/06/09; `bbics_u` 2024-06, 2025-06; `ps_12` 2026-03/06; `ps_21` 2026-06),
Banchile PS-12/13/18 2018-06 → “2017-12”, BCI PS-30 2017-09 → 2016-09, EF PS-1 2016-03 → 2015-03, Sudamericana 2016-09 → 2016-06, Security PS-2 2019-03 → 2019-12 (este último es el duplicado real).
El patrón “mismo mes, año −1” en BICE apunta a que el detector toma el año de la columna comparativa. Pendiente: leer 2 PNG de BICE y corregir el detector (preferir el año mayor cuando el encabezado trae “2024 y 2023”).

### 8. `nro_registro_cmf` erróneo

Security PS-4 (2022-06→2024-06) y PS-6 (2022-06→2026-06) reportan 270, que es el registro de PS-3; sus montos siguen su propia serie, así que es el **regex de registro** que captura otro número (probablemente cambió el formato de la portada en 2022). EF PS-7/10/11/15 → “1”. Como el registro es la llave para el alias (hallazgo 1), debe validarse: aceptar sólo si el mismo id lo repite en ≥2 períodos y no colisiona con otro id de la administradora con montos distintos en el mismo período.

### 9-11. Menores

- Montos con decimales: `c/u a 22,5` (glosa de texto libre en Transa) y `4.15264`/`4619.6` (OCR Santander PS-13 2014-15). Rechazar montos no enteros en `parse_eeff_lineas`.
- Santander PS-13 2016-06→12 y Banchile PS-13/18 2020-09: caídas >90 % en el último trimestre = liquidación (consistente con “EN LIQUIDACIÓN”). PS-13 2016-12 muestra bonos LP −6.871.389 con activos 14.807: revisar líneas.
- Excedente neto nulo: concentrado en OCR 2014-2017; se resuelve en parte con el hallazgo 2.

## Plan de corrección (orden propuesto)

1. Fix 39 — desplazamiento columna Nota (parser + test + re-derivar). Impacta 70 balances.
2. Fix 40 — validación de `nro_registro_cmf` y detector de período (año mayor del encabezado).
3. Fix 41 — `alias_patrimonios.csv` + regla automática por registro; columna `codigo_emision_segun_cmf`.
4. Fix 42 — estados `pdf_duplicado` / `pdf_de_otro_ps` / `pdf_de_otro_periodo` en cobertura; excluir del resumen.
5. Nuevos chequeos en `audit_patrimonios_separados_v2.py`: sha256 repetido, ids con mismo registro, montos pequeños con `anterior` grande, valores idénticos consecutivos, montos no enteros, registro con >1 valor por id.
6. Corrida corta dirigida con los casos de arriba (regla del usuario) antes de re-derivar todo.

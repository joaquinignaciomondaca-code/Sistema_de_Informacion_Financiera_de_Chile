# Valor cuota de fondos mutuos: lo que había en la cartera de seguros y no se leía

**Fecha:** 2026-10-02 · **Alcance:** solo documentación y el flujo nuevo
`ffmm/scripts/valor_cuota.py` + `ffmm/scripts/actualizar_valor_cuota.py`. No se tocó ninguna tabla
ya publicada.

Este trabajo parte de una revisión de enlaces externos y termina en un agujero del propio sitio: el
repositorio tenía el valor cuota de los fondos dentro de una tabla y no lo sabía.

---

## 1. El hallazgo

`seguros_fondos_mutuos` —la sección B.3 de la Circular 1835, el reporte mensual de cartera que cada
aseguradora declara— trae por línea `run_fondo`, `serie`, `nemotecnico`, `unidades`,
**`valor_cuota`** y `valor_final`. Son **99.853 líneas** en `docs/outputs/seguros/fondos_mutuos/`,
publicadas desde 2016, con su fuente y su hash, que hasta ahora se leían solo como «posiciones de
una aseguradora». Nada en el repositorio las unía por fondo y por mes.

Al cruzarlas con el maestro de fondos mutuos: **309 de los 1.543 RUN** del registro tienen valor
cuota, mes a mes. Un 20,0 % del universo que ya estaba en el sitio, sin usarse, y que además habilita una
magnitud que no existía en ninguna forma: `unidades × valor_cuota` de cada fondo, que es el
patrimonio que las aseguradoras tienen invertido en él.

## 2. El grano, y por qué casi se hace mal

El valor cuota es de la **serie**, y la serie se identifica por su **nemotécnico**. Esto no es un
detalle: se probó primero con (período, fondo, serie) y produjo **271 falsos desacuerdos** entre
aseguradoras que no existían.

El caso que lo dejó claro es el fondo 8806 en 2016-11:

| Reporta | Nemotécnico | Serie | Unidades | Valor cuota |
|---|---|---|---:|---:|
| CESCE CHILE | `CFMSECCORB` | B | 97.277,797 | 1.394,8885 |
| VIDA SECURITY | `CFMSECCORG` | G | 5.003.828,0829 | 1.042,3925 |
| VIDA SECURITY | `CFMSECCORH` | H | 1.004,1948 | 1.027,558 |

Agrupado por (período, fondo) son tres valores que parecen tres aseguradoras discrepando. Son tres
series distintas del mismo fondo, y la clave correcta es
**(período, fondo, nemotécnico, serie)**: 51.512 grupos, de los que 1.360 discrepan y solo 30 de esos
son de una sola aseguradora.

## 3. Las tres compuertas, calibradas sobre los datos reales

| | Qué comprueba | Tolerancia | Resultado medido |
|---|---|---|---|
| **C1** identidad | `unidades × valor_cuota = valor_final × 1000` | 1.000.000 de pesos o 0,5 % | 99,85 % de las 99.853 líneas |
| **C2** consenso | todas las aseguradoras de la serie coinciden | la misma | 1.289 series con desacuerdo real |
| **C3** positivo | el valor cuota es > 0 | — | 92 series con valor 0 |

**C1** necesita tolerancia mixta y no exacta: el desvío mediano es 6,6·10⁻⁷ y el percentil 90
es 1,8·10⁻⁴, pero la cola la forman las carteras chicas. La mediana de `valor_final` de las líneas
que fallan es de **4 miles**: ahí el redondeo a miles del archivo domina y la diferencia no es un
error, es la escala del dato.

**C3** existe porque **C1 se abre por atrás con un cero**: 0 × 0 = 0 × 1.000. Hay 94 líneas así en la
fuente, en 5 fondos, y esos fondos sí tienen valores normales en otros períodos (el 9328, 190
veces). Sin este control, 92 ceros se habrían publicado como si fueran valores cuota. Es el mismo
tipo de defecto que F3 en la revisión de estados financieros: la compuerta verde por una vía que
nadie miró.

Cuando C1, C2 o C3 no pasan, la fila **se publica con `valor_cuota` nulo** y un `estado` que lo
explica. No se promedia, no se elige la primera y no se rellena con cero.

## 4. Lo que sale, y lo que no sale

| | Filas | Fondos | Período |
|---|---:|---:|---|
| Publicado | 51.509 | 309 | 2016-11 → 2026-08 |
| Sin valor (C1) | 81 | | |
| Sin valor (C2) | 71 | | |
| Sin valor (C3) | 92 | | |

**Reconciliación exacta.** 51.512 grupos en la fuente − 2 del RUN 2597 (no figura en ningún padrón
oficial) − 1 del fondo de inversión 9144 (esta fuente no alcanza para el sector de inversión) =
51.509 publicados. No se perdió ni se inventó ningún grupo; lo comprobó
`ffmm.tests.test_valor_cuota::TestPropiedades`.

**Fondos de inversión no se publica.** La Circular 1835 entrega **un solo** fondo de inversión de los
1.679 del registro (0,06 %): el 9144, Zurich Gestión Patrimonial C, en 2018-10. Una tabla de una fila
no sostiene ninguna consulta, así que el umbral está declarado (`MIN_FONDOS = 10`), el motivo escrito
en `docs/outputs/valor_cuota_control.json` y la tabla no existe. **Para fondos de inversión la ruta
es la ficha de la CMF** (pestaña 7, valor cuota; pestaña 27, aportantes), que no se puede hacer aquí
porque este entorno no alcanza a `cmfchile.cl`.

## 5. Tres cosas que esta tabla **no** es

1. **No es el patrimonio del fondo.** Es el patrimonio que las aseguradoras tienen invertido en él: una
   cota inferior. Por eso las columnas se llaman `unidades_aseguradoras` y
   `patrimonio_aseguradoras_m`, y no `patrimonio`.
2. **No es el mercado.** 309 de 1.543 fondos mutuos (20,0 %) y 0,06 % de los fondos de inversión. La
   cobertura es un dato de la tabla, no una promesa del sitio.

   ### Por qué el número es 20,0 % y no indica trabajo pendiente

   Conviene desarmarlo, porque leído en crudo parece que falta por procesar y no es así:

   | Eje | Resultado |
   |---|---|
   | Periodos de la fuente / publicados | **118 / 118**, del 2016-11 al 2026-08. Ninguno ausente. |
   | Grupos `(periodo, run, nemotécnico, serie)` de la fuente / publicados | 51.512 / 51.509. Los 3 que faltan están explicados. |
   | Fondos vigentes del registro CMF con valor cuota | 204 de 449 (**45,4 %**) |
   | Fondos «No Vigente» del registro con valor cuota | 105 de 1.094 (9,6 %), los que se tenían en periodos antigos |
   | Total, que es el 20,0 % publicado | 309 de 1.543 |

   El denominador de 1.543 mezcla 449 fondos vigentes con 1.094 que la CMF ya da por cerrados: un
   fondo cerrado en 2017 no puede aparecer en una cartera de 2026, así que medir contra el total
   subestima la cobertura por construcción. Entre los vigentes, que es la comparación que tiene
   sentido, es 45,4 %. El resto de esa brecha tampoco es un fallo: hay fondos que las aseguradoras
   no pueden mantener por sus propias normas de inversión.

   Las 99.853 filas de la fuente contra las 51.512 series no son una pérdida: la fuente está a nivel
   de aseguradora (68 aseguradoras, 1,15 por grupo de media y mediana 1, con cola larga en los
   fondos grandes) y la tabla publicada agrega a nivel de fondo.

   `docs/outputs/valor_cuota_control.json` publica el desglose en `cobertura.ffmm.por_vigencia` y
   `periodos_fuente`, para que el número no dependa de que alguien lo interprete.
3. **No es lo que la CMF llama «valor cuota» del fondo**, aunque venga de la CMF: es el precio que
   cada aseguradora usó para valorar su posición, y que todas coinciden en reportar. La diferencia se
   reduce al 3,25 % de las series y, tras aplicar C1, a 152 filas de 51.512 (0,3 %).

## 6. Defecto preexistente encontrado: la codificación de los nombres de fondos mutuos

Al cruzar con el maestro apareció que **206 de los 1.543** nombres del universo de fondos mutuos
llegaron con el UTF-8 leído como latin-1: `HASTA 3 AÃ\x91OS` (Ñ), `INVERSIÃ\x93N` (Ó), `DÃ\x93LAR`
(DÓLAR). El maestro publicado (`maestro_fondos_mutuos.parquet`) tiene al menos un caso.

**Causa raíz:** `ffmm/scripts/01b_build_universe_funds.py:35` hace
`r.read().decode('latin1', errors='ignore')` sobre la página de la CMF, sin probar UTF-8 antes.
`ffmm/scripts/actualizar_carteras.py:206-208` sí lo hace (`utf-8-sig` y, si falla, `latin-1`).

**Lo que hace esta tabla:** repara el nombre alPublicarlo (`valor_cuota.reparar_mojibake`), con dos
salvedades. 205 de 206 se reparan limpiamente. El RUN 9049 (`DEPÃ\x83Â¿SITO`) tiene corrupción en dos
capas e **invertir una vez no alcanza**; se publica como vino y queda anotado en el control. Y hay un
caso donde la reparación da una palabra **distinta y equivocada** sin avisar (`DEPÃ¿SITO` → `DEPÿSITO`):
por eso la reparación no se conforma con dejar de verse mal, sino que marca la huella y manda el caso
a revisión.

**Lo que NO se hizo y queda recomendado:** arreglar `01b_build_universe_funds.py` para decodificar
como UTF-8 primero, y corregir los nombres ya publicados. No se hizo en este cambio porque modifica
una tabla publicada que tiene su propia cadena de procedencia, y `01b` no se puede ejercitar sin red.

## 7. Archivos

**Nuevos**
- `ffmm/scripts/valor_cuota.py` — grano, compuertas C1/C2/C3, reparación de codificación, clasificación de RUN
- `ffmm/scripts/actualizar_valor_cuota.py` — publicación, manifiestos, control y entrada en `data_manifest.json`
- `ffmm/tests/test_valor_cuota.py` — 31 pruebas, sin red, con las rarezas medidas
- `.github/workflows/valor_cuota.yml` — días 9, 19 y 29 a las 12:50 UTC, dos días después de que
  `seguros_carteras.yml` publique (7, 17 y 27) y antes de que ningún otro flujo comparta horario
- `docs/outputs/valor_cuota_control.json` — cobertura, tolerancias, 244 avisos y pendientes de codificación
- `docs/outputs/valor_cuota/ffmm/<AAAA>.parquet` + `manifest.json` — 51.509 filas en 11 Parquet

**Modificados**
- `docs/js/duckdb_client.js` (vista `ffmm_valor_cuota`) · `docs/js/sidebar.js` (tarjeta y 5 consultas)
- `docs/vocabulario.json` · `pipelines/auto/inventario.json` · `data_manifest.json` · `docs/js/download_catalog.js`

## 8. Estado de las auditorías

| Auditoría | Resultado |
|---|---|
| `audit_automatizacion` | 77 tablas inventariadas, 0 problemas |
| `audit_rut_formatos` | 680 archivos, 0 problemas |
| `audit_web_full` | 100 % operativo |
| `audit_interfaz` | coherente |
| `normalizar_vocabulario --check` | 76 tablas, 15 sectores, 42 tipos |
| `audit_navigation` | 12 familias, 76 tablas, 76 opciones |
| `audit_consultas_sugeridas` | **151 OK, 0 vacías, 0 con error** (5 nuevas) |
| `unittest ffmm.tests.test_valor_cuota` | 31 OK |

## 9. Lo que queda para completar el sector

1. **Fondos de inversión, de verdad:** la ficha de la CMF (pestañas 7 y 27), que además trae los
   **aportantes**, otra magnitud que hoy no existe en ninguna tabla. Requiere red: solo en Actions.
2. **Completar el 80 % que falta de fondos mutuos** por la misma vía, y cotejar contra lo que se
   publica hoy: donde coincidan, es una confirmación de que el valor cuota derivado es el del fondo.
3. **Aportantes de fondos mutuos**, que la Circular 1333 no trae y la ficha sí.
4. **Decidir si `unidades × valor_cuota` se publica como columna propia** una vez exista la serie
   completa de la CMF; hoy la agregación vive en la consulta para no duplicar la fuente.

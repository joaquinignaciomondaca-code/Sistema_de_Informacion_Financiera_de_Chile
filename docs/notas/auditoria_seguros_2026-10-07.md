# Auditoría profunda de los datos de compañías de seguros (CMF, Circular 1835) — 2026-10-07

Objeto auditado: **todos los datos publicados del sector seguros** — las 8 tablas de
`docs/outputs/seguros/` (`renta_fija`, `acciones`, `fondos_mutuos`, `bienes_raices`,
`extranjeros`, `derivados`, `pactos`, `control_inversiones`), el maestro
`aseguradoras.parquet`, los manifiestos (`manifest.json` raíz y por tabla), las entradas de
`data_manifest.json`, el catálogo web (`docs/js/download_catalog.js`, `docs/js/data_dictionary.js`),
los scripts del pipeline (`seguros/scripts/`), el workflow `seguros_carteras.yml` y las
afirmaciones del `seguros/README.md`.

No es una certificación externa: es una auditoría interna de consistencia, contra la ficha
técnica de la CMF (copia en `seguros/fuentes/fichas_tecnicas_1835/`) y contra líneas reales
de la fuente (`seguros/fuentes/muestras_1835/`).

Método: recálculo completo con pandas/pyarrow sobre los 109 archivos Parquet publicados
(**4.103.006 filas** de detalle + 87 aseguradoras), validación de RUT con el módulo 11 de
`pipelines/auto/rut.py`, pruebas de duplicidad exacta y por clave natural, validación de
fechas y sus lógicas cruzadas, cuadraturas contables por tabla, y cotejo de cada manifiesto
contra los archivos en disco. Se corrieron además las pruebas del lector
(`python -m seguros.tests.test_formato_1835`) y las de `pipelines.auto` (14/14 OK).

## Veredicto

**Los datos publicados son fieles a lo que la CMF entrega y pasan la auditoría estructural
completa.** La cobertura es continua, los esquemas son estables, los manifiestos cuadran al
100 % con los Parquet, las cuadraturas contables centrales se cumplen y los RUT y fechas
son válidos. Se encontraron **un defecto de la automatización (corregido)**, **tres
defectos de calidad que vienen de la fuente** (duplicados exactos, doble reporte en meses de
fusión, fechas imposibles) y **un defecto del maestro de entidades** (meses contados sin filas
publicadas). Nada de esto invalida la serie publicada, pero tres puntos ameritan decisión del
dueño del pipeline (ver Recomendaciones).

## 1. Verificaciones que cuadran

| Verificación | Resultado |
| :--- | :--- |
| Cobertura temporal | 118 meses continuos **2016-11 a 2026-08**, sin huecos, en las 6 tablas por año; 21 meses **2024-12 a 2026-08** en `renta_fija` y `bienes_raices` (política de tamaño declarada en `DESDE_TABLA` del publicador) |
| Cambio de formato 2024-12 | Correcto: 2024-11 figura como `v2016` y 2024-12 como `v2024`; los lectores de ambos formatos se probaron con muestras reales |
| Esquema por tabla | Idéntico (columnas y tipos) en todos los archivos de cada tabla; el esquema fijo evita que un mes cambie el tipo de una columna |
| Manifiesto raíz vs Parquet | Registros por período y tabla cuadran en el **100 %** (118 períodos × tablas); cada período declara formato, compañías y registros |
| Manifiestos por tabla | `total_records`, períodos y lista de archivos cuadran en el 100 % con lo publicado en disco |
| `aseguradoras.parquet` vs manifiesto | 87 compañías; primer/último mes, meses reportados y nombre cuadran en el 100 % una vez normalizado el formato del RUT (ver F8) |
| RUT | Más de 6,6 millones de valores en columnas RUT (aseguradora, emisor, administradora, RUN, emisor del activo objeto): todos numéricos y con dígito verificador válido donde la fuente lo trae; formato canónico (cuerpo sin DV) en todas las tablas publicadas |
| Fechas | 100 % con formato `AAAA-MM-DD` válido; 0 filas con `fecha_emision > fecha_vencimiento`, `fecha_operacion > fecha_vencimiento` o `fecha_compra` posterior al período informado |
| Cuadratura `renta_fija` | `costo_amortizado − deterioro = valor_final` cuadra en el **100 %** de 2.216.342 filas (tolerancia de redondeo) |
| Cuadratura `acciones` | `valor_final = valor_razonable` (95,9 %) o `costo − deterioro` (resto): **100 %** combinado; 0 valores finales negativos |
| Cuadratura `bienes_raices` | `costo − depreciación = costo_corregido` exacto en 724.311/724.319 filas (±1 M$ en el resto) |
| Cuadratura `control_inversiones` | `representativas + no representativas = valor_final` cuadra en el **99,83 %** (193 filas con ±2 M$ de redondeo) |
| Cuadratura `fondos_mutuos` | `unidades × valor_cuota = valor_final` cuadra en el 93,8 % de las filas en pesos (el resto: redondeo de cuota y 1.808 filas en PROM) |
| Claves naturales | 0 duplicados por clave en `derivados`, `pactos`, `bienes_raices`; los duplicados por clave en `acciones`/`fondos_mutuos`/`renta_fija` son compras distintas del mismo instrumento (valores distintos) |
| `data_manifest.json` | 9 entradas de seguros; `registros_reales` y corte cuadran con los Parquet/manifests |
| Web | `download_catalog.js` publica las 9 tablas con rutas, cobertura y bytes reales; `data_dictionary.js` define las vistas y columnas; `inventario.json` mapea las tablas al workflow `seguros_carteras.yml` |
| Afirmaciones del README | 11.153 filas de pactos ✔; 155 filas en 2026-08 ✔; cobertura 2016-11 a 2026-08 ✔; `updated_at` 2026-09-28 ✔ |
| Pruebas | Lector 1835 OK sobre muestras reales de ambos formatos (cuadratura de bonos 100 %, exclusión de archivos defectuosos OK); `pipelines.auto` 14/14 OK; contrato de publicadores OK |
| Avisos de la fuente | 1.947 avisos acumulados y publicados en el manifiesto: 1.381 totales declarados que no cuadran, 280 encabezados con otro período, 149 archivos sin registro de totales, 124 sin encabezado, 11 campos ilegibles, 2 archivos excluidos (2025-05) |

## 2. Hallazgos

### F1 (alto, automatización — **corregido en esta auditoría**)

El paso de pruebas de `seguros_carteras.yml` corría
`python -m unittest -v seguros.tests.test_formato_1835`, pero ese módulo **no define ningún
`TestCase`**: es un módulo con `main()`. El paso ejecutaba **0 pruebas y siempre salía
verde**, así que el contrato «todo publicador prueba antes de escribir» se cumplía en la
forma pero el lector nunca se probaba de verdad en CI (un lector roto habría publicado
igual). Corregido: el paso ahora corre `python -m seguros.tests.test_formato_1835` (el
`main()` real, que falla con assert) además de `python -m unittest -v
pipelines.auto.tests.test_estable`. El contrato de publicadores sigue pasando (9/9) y el
YAML valida.

### F2 (medio, maestro de entidades — defecto del pipeline — **corregido**)

`meses_reportados` (y con él `primer_periodo`) **sobraba la cobertura real en 11 de 87
compañías**: el publicador contaba un mes cuando la compañía aparecía en el ZIP (en el
encabezado de un archivo leído), no cuando aportaba filas publicadas. Tres compañías
figuraban con meses reportados pero **cero filas en todas las tablas**: HUELEN generales
(`96994700`, 70 meses contados, 0 filas; sus 70 archivos C llegan con encabezado y sin
detalle), Suramericana Vida (`99017000`, 8 meses, 0 filas) y Chubb Seguros de Vida en
generales (`99588060`, 2 meses, 0 filas). Otras 8 compañías sobraban entre 1 y 7 meses
(p. ej. Banchile Vida en generales: 10 contados, 3 reales; Starr: 117 contados, 115 reales).

**Corrección aplicada**: (1) el publicador ahora cuenta los meses por filas efectivamente
publicadas; (2) se agregó `--solo-maestro`, que recalcula `aseguradoras.parquet` desde los
Parquet publicados, y se ejecutó: el maestro pasó de 87 a **84 compañías** (las 3 sin filas
quedaron fuera, coherente con la definición del diccionario: «meses publicados en que
aparece») y los 11 casos corregidos cuadran al 100 % con los datos; (3) `data_manifest.json`
se recalculó (solo cambió `seguros_maestro`: 87 → 84 registros; el orden del catálogo se
conserva reemplazando in-place); (4) la descripción de `meses_reportados` en
`metadatos_web.py` ahora dice explícitamente «meses con filas publicadas». Las tres
compañías retiradas siguen documentadas aquí: enviaron reporte (archivos C sin detalle) pero
nunca publicaron una fila.

### F3 (medio, calidad de la fuente — duplicados exactos)

Hay **filas 100 % idénticas** publicadas: `renta_fija` 28.240 filas de más (1,27 %),
`extranjeros` 5.931 (1,27 %), `fondos_mutuos` 92, `acciones` 4. Llegan con multiplicidad de
hasta 22 (ej.: bono `BNTRA-D` de Seguros Vida Security, 2025-03, 22 copias idénticas). No es
un artefacto del lector: las muestras de la fuente no traen duplicados, la escritura
reemplaza el período completo y ningún compañía-mes está duplicado por entero — las líneas
repetidas vienen dentro del archivo que envía la compañía y la CMF las publica tal cual. El
pipeline no deduplica. Al agregar por instrumento o compañía, esos meses sobrestiman
el valor final. **Mitigación aplicada**: el publicador ahora avisa cada mes con duplicados
exactos (`<tabla>: N filas 100% idénticas (duplicados de la fuente)`), así el lector queda
documentado en el manifiesto; los datos ya publicados se conservan tal cual (son la fuente).
La deduplicación aktive queda como decisión de política (ver Recomendaciones).

### F4 (medio, calidad de la fuente — doble reporte en el control)

`control_inversiones` tiene **155 claves repetidas** `(periodo, sector, rut,
tipo_inversion)` en **13 compañías-mes**, todas con valores distintos: la compañía envió dos
archivos C en el mismo mes (dos nombres, dos valores). Son fusiones con reporte cruzado:
Zurich Rentas Vitalicias / Chilena Consolidada (`99185000`, 2024-11 a 2025-07),
Alemana / Principal (`96588080`, 2017-02), CLC / Principal (`96588080`, 2018-06),
Alemana / Uc-Christus (`76511423`, 2024-12) y HDI (`99231000`, 2024-06, mismo nombre, valores
distintos). No hay aviso en el manifiesto para este patrón (los avisos de esos meses no lo
mencionan) y las agregaciones por compañía-mes suman ambos reportes.

### F5 (bajo, calidad de la fuente — fechas imposibles)

- `renta_fija`: 378 filas con vencimiento **> 2070** (máx. `2173-03-12`; nemotécnicos
  `BLAPO-F/G/H`, `USP32133CH47`, `US05890PAC05`, `USP1027DHQ71`). El mismo bono aparece en
  otros meses con vencimiento razonable (2034), así que es la fuente, no el lector.
- `bienes_raices`: 235 filas con `fecha_compra` < 1970 (`1940-01-30` ×126, `1950-02-02`,
  `1955-06-30`, `1965-01-07`, `1942-01-14`, `1952-09-08`, `1900-01-01` ×4), de Mutual de
  Seguros de Chile (168), Mutualidad de Carabineros (63) y Metlife (4).
- `extranjeros`: vencimientos > 2100 en 4.379 filas (v2016 y v2024). Incluye bonos
  soberanos a 100 años legítimos (México, bono `91086QAZ1`, vence 2110) y otros dudosos
  (máx. `2174-11-18`).

### F6 (bajo, calidad de la fuente — identificadores y nombres)

- `acciones`: 39 filas con `run_fondo = "1"` (Euroamerica, nemotécnico `CFIPLIDER`,
  2016-11 a 2017-06 y más).
- 6 aseguradoras con `#` donde va la Ñ (`BUPA COMPA#IA…`, `RENTA NACIONAL COMPA#IA…`,
  HUELEN ×3, `Compa#ia … Continental`) y 3 con prefijo numérico (`033 METLIFE…`,
  `0PENTA VIDA`, `4 LIFE SEGUROS DE VIDA S.A`). El lector preserva el dato tal como llega;
  la mezcla (otras sí traen la Ñ, p. ej. `CN LIFE COMPAÑIA…`) indica que cada compañía
  envía el archivo en una codificación distinta.

### F7 (bajo, calidad de la fuente — cuadratura parcial en bienes raíces)

`costo_corregido − deterioro = valor_final` cuadra en el 90,58 % de las filas; en el 9,42 %
restante el valor final informado es distinto (mediana de desvío 405 M$) y el deterioro
informado es 0 en la mayoría de esos casos: la compañía informa un valor final menor sin
informar deterioro. No es un error de lectura (la otra identidad, `costo − depreciación =
costo_corregido`, cuadra siempre).

### F8 (bajo, consistencia interna — formato del RUT)

El manifiesto raíz guarda las claves de compañías como `sector|RUT-con-DV` (formato B) y
`aseguradoras.parquet` publica el RUT como cuerpo sin DV (formato C, la convención canónica
del repo). No rompe nada (el manifiesto es control interno del pipeline), pero cualquier
cruce entre ambos archivos debe normalizar el RUT primero.

### F9 (informativo — RUT en ambos sectores)

6 RUT reportan en vida y generales a la vez. Es legítimo cuando la sociedad opera ambos ramos
(Mutualidad de Carabineros `99024000`, HUELEN `99196000`). Otros 4 son reclasificaciones de
la fuente: Banchile Vida (`96917990`) reportó como generales 2017-03 a 2019-10;
Suramericana (`99017000`) como vida 2024-12 a 2025-07; Chubb (`99225000`) abrió vida en
2026-03; Chubb Seguros de Vida (`99588060`) reportó como generales 2025-05 a 2025-11.

### F10 (informativo — huecos internos por compañía)

10 de 82 compañías tienen meses faltantes dentro de su rango (ej.: AUGUSTAR y Uc-Christus
2024-11 a 2025-04; HUELEN vida 2022-08 a 2022-11; SUAVAL 2026-04 y 2026-05). Son meses que
la compañía no reportó; el pipeline publica lo que la CMF publica y no interpola.

## 3. Descartados tras verificar (no son defectos)

- **Detalle vs control no cuadra**: la suma del detalle B.1–B.7 no pretende igualar al
  control B.8; este incluye partidas fuera del detalle (efectivo y equivalentes, CUI/APV,
  filiales, coligadas y otras clasificaciones). La comparación es inválida como control.
- **`acciones`: costo − deterioro ≠ valor_final**: la identidad correcta es
  `valor_final = valor_razonable` cuando existe y `costo − deterioro` cuando no; cuadra el
  100 % combinado.
- **`pactos`: contable ≠ nominal + interés**: no es una identidad de la ficha; el valor
  contable se acerca al valor de mercado del activo objeto (44,5 % exacto; el resto por
  devengo y por moneda del nominal, que puede ser UF o extranjera).
- **Vencimientos largos (2041–2070)**: normales en renta fija (bonos a 30+ años); sólo los
  > 2070 se reportan en F5.

## 4. Correcciones aplicadas en esta auditoría

| # | Hallazgo | Corrección | Archivos |
| :--- | :--- | :--- | :--- |
| 1 | F1: el paso de pruebas del workflow ejecutaba 0 pruebas | El paso corre `python -m seguros.tests.test_formato_1835` (el `main()` real) además del unittest de `estable`; contrato de publicadores sigue pasando (9/9) | `.github/workflows/seguros_carteras.yml` |
| 2 | F2: maestro con meses sobrestimados (11 compañías; 3 sin filas publicadas) | Los meses se cuentan por filas publicadas; se agregó `--solo-maestro` y se recalculó el maestro desde los Parquet: 87 → **84 compañías**, métricas cuadradas al 100 %; `data_manifest.json` recalculado (solo cambió `seguros_maestro` 87 → 84, con el orden del catálogo preservado); la descripción de `meses_reportados` ahora dice «meses con filas publicadas» | `seguros/scripts/actualizar_carteras.py`, `seguros/scripts/metadatos_web.py`, `docs/outputs/seguros/aseguradoras.parquet`, `docs/outputs/seguros/manifest.json`, `data_manifest.json` |
| 3 | F3: duplicados exactos sin aviso | El publicador avisa cada mes con duplicados exactos por tabla en el manifiesto | `seguros/scripts/actualizar_carteras.py` |
| 4 | F4: doble reporte en el control sin aviso | `leer_zip` avisa cada clave `(rut, tipo_inversion)` con valores distintos en el mes | `seguros/scripts/actualizar_carteras.py` |
| 5 | F8: formato del RUT distinto entre manifiesto y Parquet | `cargar_control` normaliza las claves al formato canónico (cuerpo sin DV); el control recalculado ya se guarda así | `seguros/scripts/actualizar_carteras.py`, `docs/outputs/seguros/manifest.json` |

**Verificación tras las correcciones**: `python -m seguros.tests.test_formato_1835` OK;
`pipelines.auto` 14/14 OK; el maestro recalculado cuadra al 100 % con las filas publicadas
(0 diferencias en 84 compañías); los 118 períodos y las 8 tablas de detalle **no se
tocaron** (siguen siendo la fuente CMF tal cual).

## 5. Recomendaciones pendientes (decisión de política del pipeline)

1. **F3**: deduplicar filas 100 % idénticas al publicar (hoy se avisan, no se eliminan). Si se
   adopta, conviene reescribir la historia afectada (28.240 filas en `renta_fija`, 5.931 en
   `extranjeros`, 92 en `fondos_mutuos`, 4 en `acciones`).
2. **F4**: en meses de traslape de fusiones, decidir si el control publica ambos reportes
   (hoy, con aviso) o solo el de la sociedad sobreviviente.
3. **F5–F7**: documentar en el diccionario de datos como calidad de la fuente (fechas
   imposibles, `run_fondo = "1"`, nombres con `#`); no corregir unilateralmente.
4. **Cobertura**: `renta_fija` y `bienes_raices` parten en 2024-12 por peso (~5 MB/mes). Si
   se quiere la historia completa, basta bajar `DESDE_TABLA` y dejar que el flujo
   incremental complete los meses (el código ya lo soporta).

## 6. Corroboración: ¿tema de la CMF o error nuestro?

**Veredicto: los hallazgos de calidad (F3, F4, F5) son de la fuente (compañías/CMF), no del
lector.** El pipeline publica fielmente lo que la CMF entrega. Evidencia:

**El lector está bien verificado**

- Posiciones comparadas contra la ficha técnica oficial (`seguros/fuentes/fichas_tecnicas_1835/`):
  los campos verificables cuadran (B.1: `tipo_instrumento` 43, `nemotecnico` 53, `serie` 104,
  `rut_emisor` 33, `pais` 114, `fecha_compra` 17, `fecha_emision` 83, `unidad_monetaria` 150,
  `valor_nominal` 116; B.2 y B.8 likewise).
- Línea real de muestra (`i161031v.70015730`, CSVID 2016-10): todos los campos coherentes
  (nemotécnico `BSECG11206`, UF, fechas 2010/2006/2016, tasas 3,0 %/5,74 %/1,5 %, custodia
  DCV) y la cuadratura `costo_amortizado − deterioro = valor_final` exacta.
- El test del lector sobre muestras reales de ambos formatos pasa con cuadratura 100 %.

**F3 (duplicados) — fuente**

- La propia compañía declaró menos líneas de las que envió: 2025-03, `99301000`, archivo de
  acciones declaró 77 líneas y envió 84; control declaró 30 y envió 37 (avisos del
  manifiesto). Las líneas extra son los duplicados.
- Multiplicidad variable (2–22) distribuida en todos los meses; un lector con corrimiento
  produciría basura, no filas 100 % idénticas, y la cuadratura (100 %) se rompería.
- Las muestras de la fuente no traen duplicados (son chicas; no concluyentes solas).

**F4 (doble reporte) — fuente**

- HDI 2024-06: los 12 `tipo_inversion` aparecen exactamente 2 veces con **valores distintos**;
  un lector duplicador produciría valores idénticos → son dos reportes distintos (dos
  archivos C en el ZIP de la CMF).
- Eventos societarios corroborados públicamente: Zurich (división 2024; fusión por
  incorporación de la NewCo Rentas Vitalicias materializada el 4-11-2024 y posterior venta a
  Ohio National — Diario Oficial/Diario Estrategia/CMF); Chilena Consolidada cambió de razón
  social a Zurich Chile Seguros de Vida en 2022; CLC es de Clínica Las Condes y **sigue
  vigente** (CMF) → el archivo «SEGUROS CLC» bajo el RUT de Principal (2018-06) es un error
  de la fuente, no una fusión; Alemana es de Clínica Alemana (CMF) y se asoció con UC
  Christus en 2024. Principal (96588080) fue Seguros de Vida Banmédica hasta 1998 (CMF).

**F5 (fechas imposibles) — fuente**

- `BLAPO-F`/`BLAPO-G` son bonos de **Empresas La Polar**: BLAPO-F venció el 31-07-2022 y
  BLAPO-G vence el 31-07-2032 (cbonds). En los datos aparecen con vencimiento 2173 → error
  de la compañía en el archivo.
- Los bonos del Tesoro de EE.UU. a 30 años emitidos en 2024 vencen en 2054; ninguno vence
  en 2173. El mismo bono (`USP32133CH47`) aparece con vencimiento 2034-12-12 en otras filas
  del mismo mes.
- México sí emitió bonos a 100 años (vence 2110): esos vencimientos largos son legítimos.

**Límite: la corroboración cruda quedó bloqueada por billing**

Descargar el ZIP real y ver las líneas era la prueba directa; GitHub Actions está con límite
de gasto agotado ("recent account payments have failed or your spending limit needs to be
increased" — corridas 37583101363 y 37583312889 fallaron antes de iniciar el job). La
herramienta queda lista para correr cuando haya billing: `python -m
seguros.scripts.corroborar_fuente_cmf 2025-03:vida 2024-06:generales ...` (descarga el ZIP,
cuenta duplicados/dobles C/fechas raras en el crudo y verifica que releer reproduce exactamente
lo publicado). El workflow temporal usado para el intento se retiró; el script se conserva.

## 7. Límites de la auditoría

- No se pudo descargar los ZIP originales de la CMF desde este entorno (el proxy no lo
  permite), así que la atribución «dato fuente vs. error del lector» se hizo por consistencia
  interna: muestras reales, cambio de formato 2024-12, distribuciones por período y
  cuadraturas. Donde la duda es razonable (F3, F4, F5) se indica la evidencia interna.
- La corrida programada del 2026-10-04 no se pudo re-verificar en vivo (requiere GitHub
  Actions); se auditó su configuración y el estado publicado que resultó de ella.
- No se auditaron los estados financieros IFRS del sector (no están en este repositorio);
  el alcance es la cartera de inversiones Circular 1835.

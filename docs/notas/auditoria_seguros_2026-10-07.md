# Auditoría profunda de los datos de compañías de seguros (CMF, Circular 1835) — 2026-10-07

> **Snapshot histórico (2026-10-07).** Las coberturas y cifras siguientes reflejan los archivos de ese corte; no describen la publicación actual. El corte vigente de `seguros_pactos` (2026-09, 11.371 filas) está en [`cobertura_repos_pactos_2026-10-07.md`](cobertura_repos_pactos_2026-10-07.md) y la evidencia general en [`auditoria_fuentes_cifras_rediseno_2026-10-24.md`](auditoria_fuentes_cifras_rediseno_2026-10-24.md).

> **Rectificación de clasificación (2026-10-26).** La atribución de F3 a la fuente en esta nota era demasiado concluyente: no se conserva aquí el ZIP CMF crudo y la corroboración directa no se pudo ejecutar. Lo comprobado es que los Parquet publicados contienen filas completas idénticas y que el parser actual no las elimina; los conteos declarados en cabeceras/manifiestos y las pruebas sobre muestras no permiten identificar qué filas estaban en el ZIP histórico. Para F3, la clasificación vigente es **repeticiones observadas en la publicación; origen y causa no determinados**. Esta precisión también aplica al veredicto general sobre F3/F4/F5: la evidencia interna y el contexto son hipótesis, no una corroboración directa del contenido de cada ZIP. Este párrafo sustituye cualquier afirmación causal anterior en la nota; no declara las filas defectuosas ni legítimas.

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

## Veredicto (rectificado 2026-10-26)

**El corte auditado es internamente coherente en los controles medidos:** cobertura, esquemas,
conteos de manifiesto, algunas cuadraturas y pruebas locales del lector. Esto no acredita
fidelidad línea a línea con los ZIP de la CMF, que no están archivados aquí. Se corrigió un
defecto de automatización y otro del maestro; F3, F4 y F5 siguen siendo anomalías observadas
en la publicación con origen sin corroborar directamente. No se deduplicaron filas ni se
concluye que las anomalías sean legítimas o defectuosas. La clasificación y las decisiones
sobre uso/mitigación siguen abiertas.

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
| Claves naturales | 0 colisiones por clave en `derivados`, `pactos`, `bienes_raices`; en `acciones`/`fondos_mutuos`/`renta_fija` hay varias filas con la misma clave propuesta y valores distintos. Sin línea cruda o identificador de evento, la clave no basta para decidir si son compras distintas o un reporte repetido |
| `data_manifest.json` | 9 entradas de seguros; `registros_reales` y corte cuadran con los Parquet/manifests |
| Web | `download_catalog.js` publica las 9 tablas con rutas, cobertura y bytes reales; `data_dictionary.js` define las vistas y columnas; `inventario.json` mapea las tablas al workflow `seguros_carteras.yml` |
| Afirmaciones del README | 11.153 filas de pactos ✔; 155 filas en 2026-08 ✔; cobertura 2016-11 a 2026-08 ✔; `updated_at` 2026-09-28 ✔ |
| Pruebas | Lector 1835 OK sobre muestras reales de ambos formatos (cuadratura de bonos 100 %, exclusión de archivos defectuosos OK); `pipelines.auto` 14/14 OK; contrato de publicadores OK |
| Avisos registrados en manifiesto | 1.947 avisos acumulados en el corte auditado: 1.381 diferencias entre conteos declarados y leídos, 280 encabezados con otro período, 149 archivos sin registro de totales, 124 sin encabezado, 11 campos ilegibles, 2 archivos excluidos (2025-05). Son observaciones del proceso de lectura, no corroboración independiente del ZIP |

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

### F3 (medio, filas exactamente repetidas en la publicación; origen no confirmado)

Los Parquet del corte auditado contienen **filas 100 % idénticas**: `renta_fija` 28.240
apariciones extra (1,27 %), `extranjeros` 5.931 (1,27 %), `fondos_mutuos` 92 y `acciones` 4.
La multiplicidad observada llega a 22 (ej.: bono `BNTRA-D` de Seguros Vida Security,
2025-03). El parser actual no deduplica y reemplaza el período completo, pero no se conservan
los ZIP históricos para comparar sus líneas con las publicadas. Las muestras disponibles son
pequeñas y no contienen estas repeticiones. Por ello, no puede descartarse ni una repetición
presente en el archivo de origen ni una introducida por una versión histórica del proceso;
las cifras no determinan por sí solas si las filas representan eventos distintos ni si deben
sumarse. El pipeline conserva las filas y registra un aviso neutral de repetición; no aplica
deduplicación automática. La política de uso y cualquier mitigación siguen pendientes.

### F4 (medio, claves repetidas con valores distintos; causalidad no confirmada)

`control_inversiones` tiene **155 claves repetidas** `(periodo, sector, rut,
tipo_inversion)` en **13 compañías-mes**, todas con valores distintos: la compañía envió dos
archivos C en el mismo mes (dos nombres, dos valores). Son fusiones con reporte cruzado:
Zurich Rentas Vitalicias / Chilena Consolidada (`99185000`, 2024-11 a 2025-07),
Alemana / Principal (`96588080`, 2017-02), CLC / Principal (`96588080`, 2018-06),
Alemana / Uc-Christus (`76511423`, 2024-12) y HDI (`99231000`, 2024-06, mismo nombre, valores
distintos). No hay aviso en el manifiesto para este patrón (los avisos de esos meses no lo
mencionan) y las agregaciones por compañía-mes suman ambos reportes.

### F5 (bajo, fechas anómalas en la publicación; origen no cotejado)

- `renta_fija`: 378 filas con vencimiento **> 2070** (máx. `2173-03-12`; nemotécnicos
  `BLAPO-F/G/H`, `USP32133CH47`, `US05890PAC05`, `USP1027DHQ71`). El mismo bono aparece en
  otros meses con vencimiento razonable (2034), así que es la fuente, no el lector.
- `bienes_raices`: 235 filas con `fecha_compra` < 1970 (`1940-01-30` ×126, `1950-02-02`,
  `1955-06-30`, `1965-01-07`, `1942-01-14`, `1952-09-08`, `1900-01-01` ×4), de Mutual de
  Seguros de Chile (168), Mutualidad de Carabineros (63) y Metlife (4).
- `extranjeros`: vencimientos > 2100 en 4.379 filas (v2016 y v2024). Incluye bonos
  soberanos a 100 años legítimos (México, bono `91086QAZ1`, vence 2110) y otros dudosos
  (máx. `2174-11-18`).

### F6 (bajo, identificadores y nombres publicados; origen no cotejado)

- `acciones`: 39 filas con `run_fondo = "1"` (Euroamerica, nemotécnico `CFIPLIDER`,
  2016-11 a 2017-06 y más).
- 6 aseguradoras con `#` donde va la Ñ (`BUPA COMPA#IA…`, `RENTA NACIONAL COMPA#IA…`,
  HUELEN ×3, `Compa#ia … Continental`) y 3 con prefijo numérico (`033 METLIFE…`,
  `0PENTA VIDA`, `4 LIFE SEGUROS DE VIDA S.A`). El lector preserva el dato tal como llega;
  la mezcla (otras sí traen la Ñ, p. ej. `CN LIFE COMPAÑIA…`) indica que cada compañía
  envía el archivo en una codificación distinta.

### F7 (bajo, cuadratura parcial en bienes raíces; origen no corroborado)

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
| 3 | F3: filas completas idénticas sin aviso | El publicador registra las apariciones extra observadas tras la lectura y explicita que origen/validez no están determinados; no deduplica | `seguros/scripts/actualizar_carteras.py` |
| 4 | F4: doble reporte en el control sin aviso | `leer_zip` avisa cada clave `(rut, tipo_inversion)` con valores distintos en el mes | `seguros/scripts/actualizar_carteras.py` |
| 5 | F8: formato del RUT distinto entre manifiesto y Parquet | `cargar_control` normaliza las claves al formato canónico (cuerpo sin DV); el control recalculado ya se guarda así | `seguros/scripts/actualizar_carteras.py`, `docs/outputs/seguros/manifest.json` |

**Verificación tras las correcciones**: `python -m seguros.tests.test_formato_1835` OK;
`pipelines.auto` 14/14 OK; el maestro recalculado cuadra al 100 % con las filas publicadas
(0 diferencias en 84 compañías); los 118 períodos y las 8 tablas de detalle **no se
tocaron** en aquellas correcciones. Su cotejo histórico línea a línea con la fuente CMF
permanece pendiente.

## 5. Recomendaciones pendientes (decisión de política del pipeline)

1. **F3**: conservar las filas mientras no haya clasificación con evidencia. Cotejar ZIPs
   originales y salida histórica; después decidir, como política explícita, si corresponde un
   aviso contextual, una limitación de agregaciones o alguna transformación. No deduplicar
   automáticamente; los conteos anteriores no prueban que esas apariciones sean sobrantes.
2. **F4**: en meses de traslape de fusiones, decidir si el control publica ambos reportes
   (hoy, con aviso) o solo el de la sociedad sobreviviente.
3. **F5–F7**: documentar en el diccionario de datos como calidad de la fuente (fechas
   imposibles, `run_fondo = "1"`, nombres con `#`); no corregir unilateralmente.
4. **Cobertura**: `renta_fija` y `bienes_raices` parten en 2024-12 por peso (~5 MB/mes). Si
   se quiere la historia completa, basta bajar `DESDE_TABLA` y dejar que el flujo
   incremental complete los meses (el código ya lo soporta).

## 6. Contraste de hipótesis: ¿tema de la CMF o del proceso?

**Conclusión revisada (2026-10-26):** las pruebas disponibles comprueban el parser contra las
muestras versionadas y permiten describir anomalías en los Parquet publicados, pero los ZIP
crudos históricos no están disponibles aquí. Por eso, el veredicto previo que atribuía F3,
F4 y F5 a la fuente, y afirmaba fidelidad para esos ZIP, no está corroborado directamente.
Para F3 se conserva la clasificación «repeticiones observadas en la publicación; origen y
causa no determinados». En F4/F5, los patrones internos y el contexto externo citados abajo
son indicios, no una comparación línea a línea con la fuente.

**El lector está bien verificado**

- Posiciones comparadas contra la ficha técnica oficial (`seguros/fuentes/fichas_tecnicas_1835/`):
  **B.8 cuadra 12/12 campos** (`tipo_inversion` 1,3; `valor_final` 4,12; representativas 16,12;
  no representativas 28,12; los seis totales de 14; largo 138) y **B.1 cuadra en toda la
  sección general** (`tipo_instrumento` 43, `nemotecnico` 53, `serie` 104, `rut_emisor` 33,
  `pais` 114, `fecha_compra` 17, `fecha_emision` 83, `unidad_monetaria` 150,
  `valor_nominal` 116).
- Línea real de muestra (`i161031v.70015730`, CSVID 2016-10): todos los campos coherentes
  (nemotécnico `BSECG11206`, UF, fechas 2010/2006/2016, tasas 3,0 %/5,74 %/1,5 %, custodia
  DCV) y la cuadratura `costo_amortizado − deterioro = valor_final` exacta.
- El test del lector sobre muestras reales de ambos formatos pasa con cuadratura 100 %.

**F3 — evidencia indirecta, causa sin corroborar**

- Para 2025-03, `99301000`, los controles guardados reportan diferencias entre líneas
  declaradas y leídas (acciones 77/84; control 30/37). Sin el ZIP, esto no identifica cuáles
  líneas concretas son repetidas ni demuestra que el exceso esté en el archivo de origen.
- La multiplicidad 2–22 y las cuadraturas conservadas son compatibles con filas idénticas ya
  presentes antes de la publicación, pero no excluyen un defecto histórico de extracción o
  transformación. Las muestras versionadas no traen duplicados y son demasiado pequeñas para
  decidirlo.
- El parser actual conserva las filas recibidas y avisa la repetición calculada después de
  leerlas; ese comportamiento no prueba la procedencia de los Parquet históricos.

**F4 — claves repetidas en el control publicado; ZIP crudo no cotejado**

- HDI 2024-06: los 12 `tipo_inversion` aparecen exactamente 2 veces con valores distintos en
  los datos publicados. El patrón es compatible con dos líneas o reportes, pero sin el ZIP no
  verifica que sean dos archivos C ni descarta otra explicación del proceso.
- El contexto societario documentado para Zurich, Chilena Consolidada, CLC, Alemana y
  Principal ayuda a generar hipótesis sobre posibles traslapes. No demuestra por sí mismo qué
  archivos incluyó cada ZIP ni autoriza atribuir a la fuente el caso «SEGUROS CLC» asociado a
  Principal en 2018-06; ese enlace requiere corroboración del archivo crudo.

**F5 — fechas anómalas en la publicación; origen no cotejado**

- En los datos publicados, `BLAPO-F`/`BLAPO-G` aparecen con vencimiento 2173. Referencias
  externas de instrumentos sitúan los bonos de Empresas La Polar con vencimientos en 2022 y
  2032, respectivamente; la discrepancia es real en la publicación, pero sin el ZIP no se
  determina si ya venía en el archivo o surgió en el proceso.
- Los bonos del Tesoro de EE.UU. a 30 años emitidos en 2024 se esperan con vencimiento en
  2054; el mismo bono (`USP32133CH47`) aparece con 2034-12-12 en otras filas del mismo mes.
  Son señales para cotejar, no trazabilidad a la línea cruda.
- México sí emitió bonos a 100 años (vencimiento 2110), por lo que una fecha larga no es
  anómala por sí sola.

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
  permite). Las muestras, el cambio de formato 2024-12, las distribuciones por período y las
  cuadraturas son controles internos; no sustituyen el cotejo línea a línea y no bastan para
  atribuir F3/F4/F5 a la fuente o al proceso histórico.
- La corrida programada del 2026-10-04 no se pudo re-verificar en vivo (requiere GitHub
  Actions); se auditó su configuración y el estado publicado que resultó de ella.
- No se auditaron los estados financieros IFRS del sector (no están en este repositorio);
  el alcance es la cartera de inversiones Circular 1835.

<div align="center">
  <img src="docs/assets/logo_sif.svg" alt="SIF — Sistema de Información Financiera de Chile" width="430">
</div>

# Sistema de Información Financiera de Chile (SIF)

**25 años del sistema financiero chileno, consultables con SQL desde el navegador.**
Extrae, valida y publica archivos financieros y series que las entidades reportan a la CMF, el Banco Central y la Superintendencia de Pensiones: **15 sectores, 90 objetos y más de 19 millones de filas** desde enero de 2001. El catálogo institucional de cajas de compensación conserva además un universo inicial construido a partir de listados de SUSESO y del Registro de Valores de la CMF, con altas posteriores desde los TXT IFRS de la CMF. No hay backend propio de consultas ni base de datos central: el sitio y los datos se sirven como archivos estáticos, y DuckDB-Wasm ejecuta SQL en el navegador.

**En la web, el foco es la inversión institucional:** seguros, fondos mutuos y fondos de inversión (**40 elementos del núcleo**, más de 17 millones de filas, 2001 → 2026), con bancos, AGF y corredoras como instituciones y las series del Banco Central como contexto. El catálogo de descargas sitúa **74 elementos** en los niveles visibles (40 núcleo, 10 instituciones, 24 contexto); **15** quedan fuera del foco —archivo y registros— y **1** objeto sin filas se conserva oculto. Una variante de la lista de corredoras se cuenta como elemento, pero se presenta junto a la lista base. Todo sigue publicado y disponible en el catálogo de descargas; el criterio editorial se explica en el [alcance de la edición](docs/notas/recorte_visual_industrias_2026-10-20.md).

**▶ [Abrir el sistema](https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/)** — sin instalar nada, las consultas corren en tu navegador.

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![DuckDB-Wasm 1.28.0](https://img.shields.io/badge/DuckDB--Wasm-1.28.0-FFF000?logo=duckdb&logoColor=black)
![SQL local en el navegador](https://img.shields.io/badge/SQL-local%20en%20el%20navegador-2ea44f)
![Datos](https://img.shields.io/badge/datos-90%20objetos%20%C2%B7%20m%C3%A1s%20de%2019%20M%20filas-blue)
![Serie](https://img.shields.io/badge/serie-2001--01%20%E2%86%92%202026--09-informational)

| En números | |
|---|---|
| Historia cubierta | **25 años** · 2001-01 → 2026-09 |
| Sectores del catálogo | **15**; fuentes directas: CMF, Banco Central y SPensiones. El padrón CCAF conserva procedencia histórica de SUSESO |
| Objetos publicados | **90** (86 con archivo, 85 con filas) · más de 19 millones de filas · **≈488 MB** en 728 archivos referenciados por el catálogo |
| Consultas sugeridas listas para usar | **159** |
| Actualización | **18 workflows** en GitHub Actions (17 con horario; 1 sin `schedule`) |
| Verificación | Auditorías de datos, interfaz, privacidad, automatización y pruebas unitarias en CI |

Las auditorías de CI comprueban reglas concretas; no constituyen una certificación
integral de calidad ni garantizan que no existan errores semánticos en los datos.
El archivo `docs/reproducibilidad/validacion_resumen.csv` describe fuente,
modalidad y cobertura por objeto: no es un informe de resultados de pruebas ni
de tolerancias. Verifica la fuente, el periodo, la unidad y las limitaciones de
cada conjunto antes de publicar un análisis.

Los recuentos tienen unidades distintas: `data_manifest.json` registra **89 entradas ETL**; el contrato API publica **90 objetos lógicos**, porque la tabla fuente de líneas bancarias se materializa como dos vistas filtradas; y el catálogo de descargas distribuye esos 90 elementos en **74 visibles + 15 fuera del foco + 1 oculto**. «Objetos», «tablas de origen» y «elementos de navegación» no son sinónimos. Filas, bytes, IDs, particiones y rutas se contrastan automáticamente en [`metricas_publicadas.json`](docs/metricas_publicadas.json).

Para leer estos términos: **objeto** es un recurso con ID propio en el catálogo API; **entrada ETL** es una unidad del manifiesto de extracción; **elemento de descarga** es una opción del catálogo, cuyo nivel visible es una clasificación editorial. «**Conjunto de datos**» se usa aquí en sentido general y no como un nivel adicional del contrato. Una **vista SQL** es un nombre consultable por DuckDB: puede corresponder a un objeto, ser un alias o una vista auxiliar; las cuatro auxiliares no son objetos ni descargas. Una **consulta** es una instrucción SQL, no un objeto de datos. **Filas** cuenta registros por objeto o archivo; no implica unicidad global y una ruta compartida puede aparecer en más de un objeto. La **unidad de observación** depende de cada tabla y fuente: el catálogo API no ofrece un campo uniforme para ella, así que hay que revisarla en la ficha, el esquema y la documentación de la fuente, sin inferirla del conteo de filas o de una clave aparente.

---

## 1. El problema

Los datos del mercado financiero chileno son públicos, y son casi inusables.

Los archivos financieros y series publicados provienen de tres fuentes directas —CMF, Banco Central y Superintendencia de Pensiones— y llegan en formatos que no conversan: TXT delimitados, XLSX, ZIP con XML/XBRL, PDF de estados financieros y HTML sin API. El registro de CCAF tiene un antecedente distinto: su universo inicial combina listados de SUSESO y del Registro de Valores CMF; el pipeline actual incorpora altas desde el TXT IFRS de CMF, pero no descarga los PDF de SUSESO. Cada fuente usa sus propios identificadores y nombres, y no garantiza que el próximo archivo conserve las mismas columnas.

El resultado práctico: **cruzar la cartera de una aseguradora con la de un fondo mutuo es un proyecto, no una consulta.** Un analista que quiera saber qué emisores concentran riesgo en dos industrias a la vez pasa más tiempo homologando identificadores que analizando.

Este proyecto convierte eso en una base de datos que se consulta en el navegador.

---

## 2. Qué puedes preguntarle

Las consultas se escriben en SQL estándar y se ejecutan **en tu máquina**, sobre los Parquet publicados. El navegador solicita al hosting los archivos o rangos que necesita; la consulta y sus resultados se procesan localmente y no se envían a un endpoint SQL compartido.

```sql
-- ¿Dónde invierten fuera de Chile los fondos mutuos, en el último mes publicado?
SELECT pais_emisor,
       count(*)                  AS posiciones,
       count(DISTINCT run_fondo) AS fondos
FROM ffmm_cartera_extranjera
WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_extranjera)
GROUP BY pais_emisor
ORDER BY posiciones DESC;
```

Resultado real, último período publicado (2026-09, verificado el 2026-10-20):

| pais_emisor | posiciones | fondos |
|---|---:|---:|
| US | 1.100 | 146 |
| LU | 524 | 141 |
| IE | 489 | 103 |
| BR | 100 | 14 |
| GB | 84 | 42 |

Luxemburgo e Irlanda por delante de Brasil y Reino Unido: el patrón esperable de domiciliación de vehículos de fondos, visible en una consulta.

Y el caso que motiva el proyecto — **un emisor presente en carteras de seguros y fondos mutuos, que además figura en el padrón bancario**:

```sql
-- ¿Qué bancos del padrón CMF también aparecen como emisores en seguros y fondos mutuos?
WITH bancos AS (
  SELECT rut, razon_social
  FROM bancos_lista_entidades
),
seguros AS (
  SELECT nro_rut AS rut, count(DISTINCT rut_aseguradora) AS aseguradoras
  FROM seguros_renta_fija
  WHERE periodo = (SELECT max(periodo) FROM seguros_renta_fija)
  GROUP BY 1
),
fondos AS (
  SELECT rut_emisor AS rut, count(DISTINCT run_fondo) AS fondos_mutuos
  FROM ffmm_cartera_nacional
  WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_nacional)
  GROUP BY 1
)
SELECT b.razon_social AS emisor, s.aseguradoras, f.fondos_mutuos
FROM bancos b JOIN seguros s USING (rut) JOIN fondos f USING (rut)
ORDER BY s.aseguradoras + f.fondos_mutuos DESC;
```

| emisor | aseguradoras | fondos_mutuos |
|---|---:|---:|
| Banco de Credito e Inversiones | 57 | 200 |
| Banco Santander-Chile | 51 | 198 |
| Banco de Chile | 59 | 176 |
| Banco Itau Chile | 50 | 176 |
| Scotiabank Chile | 52 | 164 |
| Banco BICE | 47 | 158 |
| Banco del Estado de Chile | 54 | 151 |

*(Período 2026-09, leído el 2026-10-22. Estos conteos cambian cuando la CMF
republica un cierre o el pipeline reprocesa una cartera —pasó entre el 20 y el 22
de octubre—, así que [el ejemplo que lo ejecuta](examples/python/02_cruce_tres_industrias.py)
comprueba el conjunto y un umbral, no las cifras.)*

Una consulta cruza el padrón de emisores bancarios con exposiciones de seguros y fondos mutuos mediante `JOIN`s directos: el RUT está homologado a toda la base bajo una convención canónica (sección 4).

La web publica **159 consultas sugeridas** organizadas por sector, para no partir de una pantalla en blanco. Cada resultado se ve como tabla o gráfico y se exporta a CSV, Excel o Parquet.

---

## 3. Los datos

**Actualización FI (2026-10-02):** el balance y los resultados de FIRES/FINRE desde XML FIEF
se publican con contextos separados, cuadraturas y cotejo por cuenta/columna. El cierre más reciente,
**2026-06**, incluye **908 fondos**, 66.864 filas de balance, 97.860 de resultados y **35.570
reglas contables validadas en ese cierre**. El backfill ya cubre **16 cierres entre 2022-03 y 2026-06**
(985.908 filas de balance y 1.164.000 de resultados), pero aún faltan 2023-06, 2025-03 y cierres
anteriores a 2022; no se presenta como una serie continua. La corrida del 2026-10-04 se detuvo al
releer cierres históricos porque la CMF rechazó parte de las descargas; el último cierre y las carteras
siguen en 2026-06. Seis documentos y los contextos adicionales defectuosos se excluyen con motivo
explícito. [Fuente, controles y ejecución](fi/README.md).

*Cifras del catálogo publicado (`docs/api/v2/catalog.json`); cada serie muestra su propio último período publicado.*

| Sector | Elementos | Filas (suma por objeto) | Serie | Fuente |
|---|---:|---:|---|---|
| Seguros de Vida y Generales | 24 | 10.553.271 | 2016-11 → 2026-09 | CMF · Circular 1835 |
| Fondos Mutuos | 7 | 3.616.378 | Carteras 2001-01 → 2026-09; EEFF 2010-12 → 2025-12 | CMF · Circulares 1333 y 1997 |
| Fondos de Inversión | 9 | 3.187.474 | Carteras 2020-03 → 2026-06; pactos 2012-03 → 2026-06; EEFF 2022-03 → 2026-06 (16 cierres, backfill parcial) | CMF · LUF / Circular 1998 · XML FIEF |
| Corredoras de Bolsa | 4 | 185.921 | 2010-12 → 2026-06 | CMF · FECU IFRS |
| Administradoras Generales de Fondos | 3 | 129.711 | 2010-06 → 2026-06 | CMF · IFRS |
| Macroeconomía y Tasas | 24 | 41.470 | diaria / mensual / trimestral | BCCh |
| Factoring y Leasing | 3 | 52.446 | 2009-03 → 2026-09 | CMF · IFRS |
| Sociedades Securitizadoras | 3 | 25.985 | 2009-12 → 2026-06 | CMF · IFRS |
| Cajas de Compensación | 3 | 13.555 | 2010-06 → 2026-06 | CMF · TXT IFRS (XBRL) |
| Patrimonios Separados | 2 | 7.981 | 2014-12 → 2025-12 | CMF · PDF de estados financieros |
| Banca | 3 | 1.963.033 † | 2022-01 → 2026-08 | CMF · B1/B2/R1 |
| FinTech | 1 | 264 | registro vigente | CMF · Ley 21.521 (RPSF) |
| Sistemas de Pago | 1 | 19 | registro vigente | BCCh / CMF |
| Fondos de Pensiones | 1 | 7 | registro vigente | SPensiones · D.L. 3.500 |
| Cooperativas de Ahorro y Crédito | 1 | 7 | registro vigente | CMF |
| **Total** | **89** | **19.777.522** | **2001 → 2026** | |

† En banca, *balance* y *resultados* son dos vistas y dos conjuntos de archivos **filtrados por separado**: B1/B2 (722.931 filas) y R1 (1.240.061), sin solape; sus filas suman las 1.962.992 de la tabla de origen `bancos_cmf_lineas`. El total sectorial de 1.963.033 incluye además las 41 filas de `bancos_lista_entidades`. Por eso el manifiesto ETL cuenta una tabla fuente y la API/Descargas exponen dos objetos lógicos filtrados más el padrón, sin duplicar filas ni compartir el Parquet combinado. El catálogo API suma 90 objetos y 19.777.522 filas. Esta tabla enumera 89 elementos de Descargas porque excluye `fi_bienes_raices`, retenido con su archivo de esquema de 0 filas pero oculto de la navegación. De esos 89 elementos, 74 están en niveles principales (19.677.258 filas; 99,5 %) y 15 en archivo/registro (100.264; 0,5 %); una variante de corredoras se cuenta como elemento y se muestra junto a su lista base. Las filas son una suma por objeto y no un conteo de registros globalmente únicos: algunas vistas pueden solaparse. El detalle de unidades y la reconciliación por IDs, filas, bytes, particiones y rutas está en [`metricas_publicadas.json`](docs/metricas_publicadas.json).

### Operaciones REPO (pactos): cobertura vigente

- **Seguros:** `seguros_pactos`, mensual, hasta **2026-09** (218 filas en septiembre; 11.371 en la serie).
- **Fondos de inversión:** `fi_pactos`, trimestral, hasta **2026-06** (40 filas en junio; 1.698 en la serie), con VRC y CRV. Por prudencia, los dos últimos períodos disponibles se tratan como cautelares (**2026-03** y **2026-06**); sus datos se conservan, pero no se consideran definitivos para comparaciones concluyentes.
- **Fondos mutuos:** no hay una tabla independiente de pactos/REPO en la extracción actual; su ausencia no equivale a cero operaciones.

Las corridas del 2026-10-04 terminaron bien sin período nuevo; una actualización posterior incorporó seguros 2026-09 (218 filas; `data_manifest.json` registra `ultima_actualizacion=2026-10-21`). FI sigue en 2026-06, con los dos cierres recientes en cautela. [Cobertura, fuentes, unidades y consultas SQL](docs/notas/cobertura_repos_pactos_2026-10-07.md).

Cada tabla publica su **manifiesto** —períodos, archivos y registros—, de modo que se puede verificar qué contiene la web. Donde la fuente es un archivo descargable único (banca B1/B2/R1, y los TXT IFRS de AGF, securitizadoras, cajas de compensación y factoring/leasing) el manifiesto además guarda el **SHA-256 del archivo de origen**, y ahí se puede comprobar que lo publicado sale exactamente de lo descargado. En los estados financieros de fondos mutuos cada fila lleva el nombre y el SHA-256 del XML de origen (`fuente_archivo`, `sha256_archivo`). En seguros, carteras de fondos mutuos, fondos de inversión y corredoras el extractor guarda el SHA-256 de lo que devolvió la CMF (`sha256_origen` en el manifiesto) **solo para los períodos que se publiquen desde el 2026-09-29**: los anteriores se descargaron sin registrar hash y no se pueden reconstruir. En fondos de inversión, que son miles de páginas por trimestre, se guarda un hash que las resume. Macroeconomía, pensiones, fintech y los registros vigentes (listas de entidades) no tienen hash de origen.

Las marcas de tiempo de los manifiestos (`updated_at`, `ultima_actualizacion`, `leido_utc`) indican cuándo **cambió** algo, no cuándo corrió el workflow: si una corrida no trae datos nuevos, el extractor no reescribe el manifiesto (ni se crea commit ni se regenera el catálogo). Que los workflows siguen corriendo se comprueba con sus corridas en Actions (`audit_automatizacion.py --frescura`). Los trimestres IFRS ya leídos cuyo TXT de origen no cambió (mismo SHA-256) tampoco se reescriben ni se vuelven a desplegar. Excepción: el monitor normativo registra cada revisión a propósito.

---

## 4. Por qué confiar en la cifra

Un dato financiero mal extraído es peor que no tener el dato. El sistema valida **antes** de publicar y se detiene si algo no cuadra:

- **Identidad**: RUT validado con dígito verificador módulo 11 y homologado **a toda la base** bajo una convención canónica (cuerpo / cuerpo-DV / puntos, según la columna).
- **Cuadraturas contables**: activos = pasivos + patrimonio. En los estados financieros IFRS de AGF, securitizadoras, cajas de compensación, factoring y leasing, corredoras y fondos mutuos (donde la identidad es activo − pasivo = activo neto atribuible a los partícipes) se verifica antes de publicar: un balance aislado que no cuadra queda registrado como aviso (en el manifiesto o en la metadata de la serie), y si la lectura falla en bloque (al menos 3 balances y más del 5 %) el trimestre no se publica. Banca cotea el total de activos contra el Excel de la CMF y fondos de inversión cuadra cada cartera con la fila TOTAL de la fuente. Patrimonios separados cuadra cada balance (±2 mil pesos) y sus subtotales al compilar el Parquet. Además, `scripts/auditar_eeff_ifrs.py` repasa en cada push y PR **toda la historia publicada** de AGF, securitizadoras, CCAF, factoring y leasing, corredores y fondos mutuos (hoy cuadran todos, con diferencias de hasta 1 mil pesos por redondeo).
- **Cobertura mínima**: si un mes trae menos del 90 % de las entidades del mes anterior, no se publica. En los estados financieros, además, si casi ningún balance trae los tres totales reconocibles (cambiaron las glosas o los códigos), el trimestre tampoco se publica.
- **Cierres reeditados**: la CMF reedita a veces cierres antiguos y lo avisa en su índice («actualizado: …»). Si la fecha es posterior a la última lectura, el trimestre se vuelve a leer y pasa las mismas compuertas; si no las cumple, se conserva lo publicado. (Corredores y agentes no la tienen: su informe no trae esa fecha. En fondos mutuos no hay índice con fecha: el nombre del XML lleva la fecha y hora de envío, así que cada corrida revisa las fichas de los dos últimos cierres y de 1/36 del resto —toda la historia una vez al año— y baja de nuevo solo los archivos cuyo nombre cambió.)
- **Legibilidad**: más de 1 % de filas ilegibles en un archivo aborta el proceso.
- **Esquema**: si la fuente cambia las columnas, el flujo falla en vez de publicar basura.

Cuando algo falla, la web dice «no disponible». Nunca un número inventado.

**Normalización de identificadores RUT.** Antes del 2026-09-29 convivían formatos con puntos, con guion y sin dígito verificador según la industria, por lo que un `JOIN` podía devolver cero filas en silencio. El normalizador documentado en [`pipelines/auto/rut.py`](pipelines/auto/rut.py) aplica reglas por nombre de columna: `rut` y claves foráneas `rut_<entidad>` se expresan como cuerpo; `rut_dv` y campos `*_dv` se normalizan a cuerpo-DV (si la entrada es parseable y no trae DV, el código lo calcula); `rut_completo` y campos `*_completo` usan puntos y DV para cuerpos de al menos seis cifras; los identificadores de cuatro o cinco cifras quedan en formato cuerpo-DV sin puntos (los RUN de fondos son un caso observado). El antiguo `rut_formateado` pasa a `rut_completo`; si coexiste `rut_cuerpo` con `rut`, el auxiliar se combina y se retira. Cuando la fuente CMF usa el campo `nro_rut`, se conserva ese nombre, se separa el cuerpo en `nro_rut` y, si la entrada trae DV, este queda en `nro_rut_dv`; las claves `nro_rut_<...>` usan el cuerpo. Los campos `run_*` quedan fuera de esta normalización RUT. La normalización es por columna reconocida, no una afirmación de que todos los identificadores distintos representen la misma entidad. Sus pruebas cubren DV, ceros iniciales, idempotencia y conservación de otros campos; `scripts/audit_rut_formatos.py` vigila los formatos publicados y pasó sobre 887 archivos. El historial y la comparación de formatos están en [`docs/notas/rut_formatos_2026-09-29.md`](docs/notas/rut_formatos_2026-09-29.md).

---

## 5. La web

Aplicación estática de siete pestañas, sin framework y sin build:

| Pestaña | Qué hace |
|---|---|
| **Información** | Portada con el núcleo (seguros, fondos mutuos y de inversión), las instituciones, el contexto macro y el alcance de la edición. |
| **Mapa relacional** | Diagrama entidad-relación con zoom, paneo y enlaces entre tablas. |
| **Diccionario** | Campo por campo: rol (PK, FK, dimensión, métrica), definición y criterio contable. |
| **Visor de datos** | Consulta tabular con filtro, orden y copia de celdas. |
| **Consultas SQL** | Terminal con autocompletado, historial, favoritos y enlaces compartibles. |
| **Descargas** | Todos los conjuntos publicados, con filas, período y peso, en Parquet, CSV y Excel; el núcleo primero y el archivo al final, plegado. |
| **Normativa CMF** | Seguimiento de la normativa publicada por la CMF (ver §7.6). |

El **explorador jerárquico** organiza 15 sectores → carpetas temáticas → 90 objetos del catálogo. Hay 89 elementos de Descargas no ocultos (74 en niveles principales y 15 en archivo/registro); `fi_bienes_raices` conserva esquema y archivo vacío, pero no se muestra en la navegación. Una variante del registro de corredoras se presenta junto a su lista base. Las consultas sugeridas aparecen en cada carpeta, ordenadas por nivel. El nivel de cada sector es una bandera en `docs/vocabulario.json` (`alcance`): cambiarla y regenerar el catálogo revierte o ajusta el recorte sin tocar datos. El motor DuckDB-Wasm 1.28.0 va **embebido en el propio sitio** (`docs/vendor/duckdb/`), así que las consultas funcionan aunque la red del visitante bloquee los CDN públicos. La preparación de datos remotos por pestaña está limitada y el control preventivo de tamaño del sitio está en [`docs/notas/capacidad_trafico.md`](docs/notas/capacidad_trafico.md).

### Verlo funcionando

```bash
git clone https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile
cd Sistema_de_Informacion_Financiera_de_Chile
python3 -m scripts.preview_no_cache --port 8000     # sirve docs/ sin caché, con soporte HTTP Range
# → http://localhost:8000
```

El servidor local responde `206 Partial Content` igual que GitHub Pages, así que DuckDB-Wasm lee sólo el pie y los grupos de fila que necesita en vez de bajar archivos completos.

### Consumirlo desde Python

El sitio publica además un **contrato estático** (`docs/api/v2/`) y un SDK que lo lee, para quien no quiere abrir el navegador:

```bash
pip install -e sdk/python   # paquete `sif-chile`, DuckDB + pyarrow
```

```python
import sif_chile

sif = sif_chile.connect()                    # o connect(base="/ruta/a/docs") sin red
sif.buscar("seguros renta")                  # qué hay, sin saberse los nombres
sif.esquema("seguros_renta_fija")            # columnas y tipos reales
sif.sql("SELECT count(*) FROM bancos_balance").fetchone()
```

Las 105 vistas de catálogo salen del `views.sql` publicado, junto con vistas temporales SQL-only para chips rápidos: algunas exponen sólo el último período y otras la última partición disponible; no alteran el catálogo ni las descargas. Detalle en [`sdk/python/README.md`](sdk/python/README.md) y en [`docs/api/README.md`](docs/api/README.md).

Hay ejemplos ejecutables en Python, R y JavaScript, y una guía para agentes con [`llms.txt`](docs/llms.txt): ver [`examples/`](examples/README.md).

---

## 6. Se mantiene solo

Hay **18 workflows** en GitHub Actions: **17 tienen horario (`schedule`)** y `fi_cobertura_eeff.yml` es el único sin horario; varios flujos también corren en `push`, `pull_request` o `workflow_dispatch`. La existencia de un cron no implica que un paso protegido publique datos: `pensiones_carteras.yml` depende de runner privado y gates. Un **guardián de automatización** cruza el manifiesto de datos, el inventario de flujos y las vistas del sitio: cada tabla publicada tiene un responsable declarado, y si una fuente se atrasa más allá de su plazo, se abre un issue automáticamente.

La ausencia de un workflow no implica ausencia de procesamiento automático. El catálogo distingue tres modalidades: **Automático** (extracción, validación y publicación programadas), **Híbrido** (extracción o curación inicial local desde fuentes no estructuradas, seguida de validación y compilación reproducibles) y **Manual** (intervención todavía no respaldada por un compilador reproducible). El balance de patrimonios separados es actualmente híbrido: la CMF publica los estados como PDF, la consolidación inicial se hace fuera de Actions y `05_publicar_balance_patrimonios.py` ejecuta las validaciones y genera el Parquet.

<details>
<summary>Calendario de los 18 flujos (17 con horario)</summary>

| Flujo | Frecuencia (UTC) | Publica |
|---|---|---|
| `contrato_publicado.yml` | cada 2 h, al minuto 23 | nada: regenera esquemas, catálogo, resultados y métricas derivados de los datos publicados |
| `macro.yml` | diario 10:00 | Macro BCCh: 51 series nativas → 23 tablas temáticas (tasas, tipo de cambio, precios, actividad, laboral, materias primas, sector externo, expectativas) + catálogo |
| `factoring_leasing_backfill.yml` | cada 3 días, 12:20 | Serie IFRS de balance y resultados |
| `bancos_cmf_mensual.yml` | cada 3 días, 13:00 | Particiones B1/B2/R1 de la CMF (incremental) |
| `ifrs_sectores.yml` | cada 3 días, 13:30 | Estados IFRS de AGF, securitizadoras y CCAF |
| `ifrs_sondeo.yml` | día 5, 13:40 | nada: describe qué sociedades del TXT IFRS quedan fuera (solo lectura) |
| `corredoras_eeff.yml` | cada 3 días, 13:45 | FECU IFRS de corredores y agentes de valores |
| `seguros_carteras.yml` | cada 3 días, 14:00 | Cartera de inversiones Circular 1835 |
| `ffmm_carteras.yml` | cada 3 días, 14:00 | Cartera de fondos mutuos Circular 1333 |
| `web_audit.yml` | lunes 14:00, push y PR | nada: auditorías del sitio + guardián de frescura |
| `ffmm_eeff.yml` | cada 3 días, 14:20 | Balance y estado de resultados anuales de fondos mutuos (XML IFRS, Circular 1997) |
| `fi_carteras.yml` | cada 3 días, 15:00 | Cartera y pactos de fondos de inversión |
| `fi_eeff.yml` | cada 3 días, 15:35 | Balance y resultados anuales de fondos de inversión (XML IFRS) |
| `entidades.yml` | días 10, 20 y 28, 12:30 | Altas y vigencia de las listas de entidades |
| `normativa_cmf.yml` | lunes a viernes, 13:23 | Feed de normativa publicada por la CMF |
| `pensiones_carteras.yml` | día 10, 10:25 | Revisión de estado; ingesta BDP solo con runner privado habilitado y gates aprobados |
| `fi_cobertura_eeff.yml` | sin horario (push) | nada: revisión de cobertura de FI (solo lectura) |
| `pages.yml` | cada 6 h (03:15, 09:15, 15:15, 21:15) y push a `main` | Despliegue de `docs/` en GitHub Pages |

Cada publicador deja su rastro en la cabecera del archivo de datos y en `data_manifest.json`; los horarios
son los `cron` reales de `.github/workflows/*.yml`.

</details>

<details>
<summary>Auditorías que corren en cada push y PR</summary>

```bash
python scripts/audit_web_full.py            # Parquet, enlaces, chips SQL, diccionario y ERD
python scripts/audit_interfaz.py            # pestañas, catálogo, vocabulario, temas, motor
python scripts/audit_navigation.py          # taxonomía: 13 familias, 90 tablas, 90 opciones del visor; niveles de alcance
python scripts/audit_automatizacion.py      # quién actualiza cada tabla y con qué frecuencia
python scripts/build_download_catalog.py --check   # el catálogo refleja lo publicado
python scripts/normalizar_vocabulario.py --check   # los nombres no se desincronizan
```

Más `audit_interfaz_dom.js` (comportamiento en un DOM real), `audit_normativa_web.js` y `audit_secretos.py`. **Todo workflow que escribe en la rama corre sus pruebas unitarias antes del `git commit`** —incluidos macro, entidades, carteras de FI y de fondos mutuos, cuya auditoría `web_audit` no cubre en las corridas programadas— y lo vigila `pipelines/auto/tests/test_contrato_publicadores.py`, que además exige que el `timeout-minutes` del job cubra el presupuesto `--minutos` del extractor y que los módulos compartidos que un publicador importa estén en sus `on.push.paths`. `web_audit.yml` ejecuta en cada push y PR las pruebas de los extractores de estados financieros, macro y seguros, sin red y con fuentes sintéticas.

</details>

---

## 7. Decisiones de diseño

1. **Sin backend de consultas ni base de datos central.** El hosting estático sirve los Parquet; DuckDB-Wasm ejecuta SQL en el navegador y lee por HTTP Range solo los archivos que necesita. Cuatro vistas usan copias Parquet compactas de uso exclusivo de SQL para reducir aperturas; se generan desde los datos publicados, pero no son objetos adicionales ni archivos de Descargas. No hay un servicio compartido que reciba o ejecute SQL.
2. **Fail-closed antes que «algo es mejor que nada».** Publicar un balance descuadrado es peor que no publicarlo: quien lo use tomará una decisión con un número falso sin saberlo. Por eso la validación aborta en vez de degradar.
3. **Un vocabulario, no convenciones orales.** Todo nombre visible vive en `docs/vocabulario.json` y un verificador recorre el repositorio; los sinónimos desaparecieron de la interfaz por construcción, no por disciplina.
4. **Compatibilidad sin contaminar.** Los nombres históricos siguen funcionando como alias en SQL, pero no se sugieren en pantalla: quien tenía una consulta guardada no se rompe, y quien llega nuevo ve un solo criterio.
5. **Auditorías como contrato ejecutable.** Cada promesa de este README se traduce en un chequeo automático. Si el catálogo de la web y los Parquet publicados divergen, el push falla.
6. **El modelo lee prosa, nunca cifras.** El único flujo con lectura asistida es el de normativa CMF, donde la fuente son PDF jurídicos sin formato estable. El modelo devuelve JSON contra un esquema cerrado, con tope de llamadas por corrida, el texto del documento tratado como dato no confiable —no como instrucción— y marca `needs_human_review` cuando la evidencia es incompleta. Cada ficha conserva sus citas y el enlace al documento oficial. Los estados financieros, carteras y series macro se parsean con código determinista y se validan contra cuadraturas: **ningún número publicado proviene de un modelo.**

---

## 8. Próximos pasos

- **Más profundidad por entidad**: incorporar las notas a los estados financieros y otros desgloses que hoy quedan fuera del dato tabular (comisiones, juicios pendientes, vencimientos, covenants).
- **Nuevas fuentes de interés** para completar la vista por industria.

---

## 9. Documentación

[`PSEUDOCODIGO.md`](PSEUDOCODIGO.md) — mapa de código, estructura del repositorio y decisiones ·
[`pipelines/README.md`](pipelines/README.md) — operación de datos y credenciales ·
[`docs/vendor/duckdb/README.md`](docs/vendor/duckdb/README.md) — cómo se vendoriza el motor ·
[`docs/notas/version_academica_y_privacidad_2026-10-20.md`](docs/notas/version_academica_y_privacidad_2026-10-20.md) — versión citable, reproducibilidad y protección de identificadores ·
READMEs por sector en `bancos/`, `ccaf/`, `factoring_leasing/`, `ffmm/`, `fi/`, `macro/`, `pensiones/` y `seguros/`.

---

## 10. Reproducibilidad y privacidad

La base se actualiza cada vez que las fuentes publican y **cada tabla tiene su
propio periodo**: seguros, fondos mutuos, fondos de inversión, banca y contexto
reportan con frecuencias y rezagos distintos. Por eso el sitio no muestra una
fecha de corte única ni una versión congelada —resumirían mal a la mayoría de
las tablas— y tampoco hay cita armada ni DOI. El periodo de cada conjunto se ve
en el explorador, en el diccionario y en Descargas.

No confundir esos datos de tiempo e integridad: `periodo` y `corte` describen la
cobertura de cada objeto; `generado` en el catálogo API indica cuándo se generó
ese descriptor, no cuándo se desplegó el sitio; `data_release` identifica el
contenido de los recursos del contrato, no una edición histórica recuperable;
y el SHA-256 de cada partición permite comprobar los bytes de ese archivo. El
repositorio no publica un archivo inmutable de versiones anteriores ni una fecha
común de despliegue. Para reproducir una edición, hay que conservar entonces los
archivos y sus hashes en una copia local; el script de snapshot de la tabla
siguiente no publica esa copia.

| Qué necesitas | Dónde |
|---|---|
| Decisiones, mediciones y auditorías | [Índice de notas](docs/notas/README.md): notas de `docs/notas/`, agrupadas por mes y con resumen. Se genera con `python3 scripts/build_indice_notas.py` |
| Auditar la base | `docs/reproducibilidad/`: diccionario CSV/JSON, inventario de archivos con SHA-256, cobertura por periodo y resumen de validación. Se regeneran con `python3 scripts/construir_reproducibilidad.py` |
| Armar una copia local con hashes | `python3 scripts/construir_snapshot_academico.py --zip`: junta los 40 conjuntos del núcleo en una carpeta con `README.md`, `CHANGELOG.md` y el inventario SHA-256. Es una herramienta local; no hay copia publicada |
| Fuentes, licencia y limitaciones | sección *Fuentes, licencia y limitaciones* de la web y `docs/notas/version_academica_y_privacidad_2026-10-20.md` |
| Criterio de privacidad | `pipelines/auto/privacidad.py` (RUT de personas naturales en `fi.cartera_nacional`; dirección y rol en `seguros.bienes_raices`) |

---

## Autor

**Joaquín Mondaca** — [LinkedIn](https://www.linkedin.com/in/joaqu%C3%ADnmondaca/) · [GitHub](https://github.com/joaquinignaciomondaca-code)

Proyecto de datos de punta a punta: extracción, validación estadística y contable, publicación incremental, automatización y producto web.

## Licencia

**Código:** MIT ([`LICENSE`](LICENSE)).

**Datos:** proceden de fuentes oficiales, con condiciones de reutilización propias por organismo y conjunto. Los archivos financieros y series con extracción directa provienen de CMF, Banco Central y Superintendencia de Pensiones. El universo inicial de `ccaf.lista_entidades` se construyó a partir de listados de SUSESO y del Registro de Valores CMF; sus balances y resultados publicados proceden de CMF. El SIF estructura y normaliza los archivos, y puede aplicar transformaciones documentadas según el conjunto. Antes de redistribuir, verifica la procedencia, las transformaciones y las condiciones de reutilización aplicables.

**Límites que conviene declarar al usar la base:**

- Las fuentes de archivo directo son CMF, Banco Central y Superintendencia de Pensiones; el SIF aporta extracción, estructura, normalización, validación y documentación. El registro de CCAF tiene el antecedente de fuentes adicionales descrito arriba.
- Es un proyecto independiente: no tiene respaldo ni aval de la CMF ni del
  Banco Central de Chile.
- La extensión de la serie de tiempo de cada tabla dependerá de cada fuente de
  origen; es por ello que no hay homogeneización generalizada de periodos entre
  todas las tablas.
- Los montos conservan la unidad y el criterio de valorización de la fuente; no
  se convierten ni se reexpresan.
- La extracción y la validación son automáticas, así que la base puede contener
  errores: úsala con criterio y haz las verificaciones propias que consideres
  necesarias antes de publicar una cifra.
- Esta edición no publica carteras de AFP: de las AFP sólo está el registro de
  administradoras.
- Los identificadores sensibles están protegidos en la versión pública: ver
  `pipelines/auto/privacidad.py`.

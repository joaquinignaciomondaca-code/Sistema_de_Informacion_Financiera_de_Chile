# P3 · API pública documentada y ejemplos reproducibles — estudio de factibilidad

**Fecha:** 2026-10-22

> **Estado (2026-10-23).** El contrato vigente es **2.0.0** y se publica en
> `docs/api/v2/`. Esta nota se escribió cuando la ruta era `api/v1/`: las rutas de
> archivo y de URL se actualizaron para que los comandos sigan funcionando, y las
> referencias a «v1» como nombre de la fase se conservan como se escribieron. Los conteos de tablas, columnas, archivos y consultas del análisis son un snapshot de 2026-10-22; para el corte vigente usa `docs/metricas_publicadas.json` y `docs/api/v2/`.

**Pregunta:** qué tan factible es añadir una API pública documentada, ejemplos
reproducibles y consumo desde Python, R, aplicaciones y agentes de IA.
**Método:** no es una opinión. Se midió el repositorio tal como está publicado hoy
(689 Parquet, 53 manifiestos, 1.284 columnas documentadas, 149 consultas
sugeridas) y se ejecutaron las consultas del README contra los archivos reales.
Los comandos están en la sección 10. En una segunda pasada se revisaron issues y
PRs del repositorio, el ecosistema chileno de datos financieros y **siete
proyectos con API ya montada** que sirven de base (sección 11); dos hallazgos de
esa pasada cambian el plan: el estándar Data Package cubre medio contrato y
DuckDB 2.0 LTS (publicado el 2026-10-21) elimina la necesidad de escribir un
servidor para "SQL sobre HTTP".

---

## 0. Veredicto

| Afirmación | Estado |
|---|---|
| ¿Se puede publicar una API documentada sin backend nuevo? | **Sí**, y cuesta ~1 día de trabajo. |
| ¿Cubre Python, R, aplicaciones y agentes? | **Sí**, si se define como *contrato de datos* (catálogo + esquema + particiones + DDL + SDK) y no como *servidor SQL HTTP*. |
| ¿Se puede además ofrecer `GET /sql?q=…`? | **Sí, y desde ayer es más barato**: DuckDB 2.0 LTS trae Quack estable, así que no hay que escribir el servidor. Sigue siendo otro producto: proceso, TLS, cuotas y disponibilidad. ~1 semana. |
| ¿Hay bloqueadores? | **No hay ninguno estructural.** Hay 10 defectos concretos de datos y metadatos (sección 4); **5 son bloqueantes** y hay que arreglarlos **antes** de anunciar nada. |

**Recomendación:** hacer Fase 0 + Fase 1 (≈ 3,5 días-persona) y publicar como
*v1 en beta* sólo después de que un test de contrato en CI ejecute los ejemplos
del README y de Python/R contra los datos publicados. Ese test es obligatorio:
hoy el ejemplo estrella del README **devuelve 0 filas** (sección 4.2).

La revisión de proyectos comparables (sección 9) no cambia la recomendación,
pero la abarata y le da estándar: **`datapackage.json` de Frictionless** cubre
esquema, claves y hashes sin código propio, y **`owid/etl`** ya publicó el patrón
de `llms.txt` + cliente que hay que copiar. Dos cosas se descartan de plano:
duplicar bytes por versión y montar una API REST operada.

Reparto honesto del trabajo: **el 70 % de la API ya existe**, pero está en
formatos de consumo humano (JS del navegador, Markdown, notas). Falta
empaquetarlo, versionarlo y congelarlo contractualmente.

---

## 1. Lo que ya está hecho (y por qué abarata todo)

| Activo | Dónde | Estado |
|---|---|---|
| Catálogo de tablas con metadatos (fuente, norma, corte, frescura, modo, origen, QA) | `data_manifest.json` (89 tablas, 19.777.492 filas) | Listo, pero con **ids heredados** |
| Catálogo de descargas con nivel, filas, peso, periodos y lista de archivos | `docs/js/download_catalog.js` (90 conjuntos, 496 MB, 41 de núcleo) | Listo, generado por script |
| Diccionario de 1.284 columnas con tipo, rol, significado y criterio contable | `docs/reproducibilidad/diccionario.{csv,json}` | Listo para 75 tablas |
| Particiones + total de filas + periodos por tabla | 53 `manifest.json` en `docs/outputs/` | Listo y ya lo consume la web |
| Integridad verificable | `inventario_fuentes.csv` con SHA-256 | Listo |
| Grafo de relaciones (PK/FK) | `docs/outputs/cardinalidad_relaciones.json` | Listo |
| 149 consultas sugeridas ya validadas contra los datos | `docs/js/sidebar.js` + `scripts/audit_consultas_sugeridas.py` | Listo y auditado en CI |
| **Registro de las 90 vistas SQL** (`read_parquet` sobre manifiesto o archivo) | `docs/js/duckdb_client.js` (`SEMANTIC_VIEWS`) | Listo, y ya hay un parser en Python |
| Guardián de SQL de lectura | `docs/js/sql_guard.js` | Sólo navegador |
| Licencia | MIT (`LICENSE`) | Cubre el código |

El activo decisivo es `scripts/audit_consultas_sugeridas.py`: ya sabe leer
`SEMANTIC_VIEWS`, resolver manifiestos y crear las 90 vistas en DuckDB **en
0,16 s**. Es decir, el "SDK" de Python no hay que inventarlo: hay que extraer ese
parser y ese registro de vistas (~90 líneas de las 234 del script) a un paquete
y publicarlos.

Medido hoy en este entorno: registrar las 90 vistas y correr la consulta de
cartera extranjera del README tarda **0,02 s** sobre disco local. No hay problema
de rendimiento en el diseño; el coste está en la red (sección 4.5).

---

## 2. Los cuatro caminos posibles

| # | Camino | Qué ofrece | Esfuerzo | Coste recurrente | Riesgo | Veredicto |
|---|---|---|---|---|---|---|
| **A** | **Contrato estático versionado + SDK + ejemplos** | URLs estables para catálogo, esquema, particiones y DDL; `pip install sif-chile`; snippets R/JS/agente | **3–4 días** | **0 €** | Bajo. Sólo depende de GitHub Pages | **Hacer ahora** |
| B | SQL sobre HTTP con **Quack** (DuckDB 2.0 LTS `quack_serve` detrás de un proxy TLS) | Clientes DuckDB (Python/R/CLI) se conectan al catálogo completo | ~1 semana + operación | 10–60 €/mes según tráfico | Alto: abuso, cuotas, coste por consulta, SLA | Sólo si hay usuarios que lo pidan |
| C | Servidor MCP local (`npx sif-mcp` / `pip install sif-mcp`) | Herramientas `buscar_tabla`, `esquema`, `consultar`, `descargar` para agentes | 2–4 días | 0 € | Medio: mantener un protocolo joven | Fase 2 natural, tras A |
| D | Endpoints JSON precalculados (último período, series, indicadores) | `GET /v1/ultimo/ffmm_cartera_extranjera.json` | 1 día + 1 por tabla que se quiera | 0 €, pero **duplica datos** | Medio: 19,8 M filas no caben en JSON; infla el repo | Sólo para 3–5 tablas de portada |

**A + C es el paquete natural**: A resuelve Python/R/apps con datos completos y
C resuelve agentes sin hosting. B es un producto distinto (y el README tendría
que dejar de decir "sin backend" si se ofrece).

Dos matices que salen de la sección 9: **C ya no es imprescindible** para
agentes que pueden ejecutar código, porque DuckDB 2.0 en *agent mode* leyendo
`views.sql` ya es una interfaz de agente (menos tokens que 88 herramientas MCP);
y **D pierde casi todo el sentido** si el contrato estático está bien hecho.

### Qué NO resuelve una API estática (y hay que decirlo en la portada)

Sin servidor no existe `GET /sql?q=…`: el consumidor ejecuta la consulta en su
máquina sobre los Parquet. Eso está bien para analistas (DuckDB/pandas/arrow lo
hacen en una línea) y para agentes que pueden ejecutar código, pero **no** para
un agente que sólo puede hacer HTTP, ni para una app móvil. Si ese es el público
objetivo, hay que ir a B y asumir sus costes.

---

## 3. Diseño propuesto para la Fase 1 (≈ 450 KB de metadatos)

Todo generado desde una sola fuente (`data_manifest.json`, `download_catalog.js`,
`SEMANTIC_VIEWS`, `diccionario.json`), sin tocar los Parquet:

```
docs/api/v2/catalog.json          # 89 tablas: id canónico, nombre, sector, nivel,
                                  # filas, bytes, particiones, corte, frescura  (26 KB medidos)
docs/api/v2/schema/{id}.json      # columnas con tipo, rol, significado             (283 KB medidos)
docs/api/v2/partitions/{id}.json  # lista de Parquet + total de filas + periodos   (desde los 53 manifiestos)
docs/api/v2/queries.json          # 149 consultas con id estable, título y SQL     (48 KB medidos)
docs/api/v2/datapackage.json      # estándar Data Package: recursos, esquema, PK/FK, hashes
docs/api/v2/openapi.json          # OpenAPI 3.1 sobre esas rutas estáticas (son GET, sin parámetros)
docs/api/v2/llms.txt              # guía de 40 líneas para agentes (patrón owid/etl)
skills/sif/SKILL.md               # skill de agente: cuándo usar SIF y cómo consultar
catalog/views.sql                 # DDL de las 90 vistas, generado                (42 KB medidos)
sdk/python/sif_chile/__init__.py  # connect(), tables(), view(), download()
examples/python|r|javascript|agent/
scripts/build_api.py              # genera todo lo anterior
scripts/audit_api.py              # test de contrato en CI (ver 4.2 y 5)
```

Coste total del contrato: **~450 KB**, un 0,09 % del sitio. No hay razón de peso
para no tenerlo. `datapackage.json` y `openapi.json` se **generan**; no se
escriben a mano, para que no puedan divergir del catálogo.

### Consumo resultante

```python
# Python — 3 líneas, sin descargar el sitio completo
import sif_chile, duckdb
con = sif_chile.connect()          # registra las 90 vistas vía HTTP Range
con.sql("""
  SELECT pais_emisor, count(*) AS posiciones
  FROM ffmm_cartera_extranjera
  WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_extranjera)
  GROUP BY 1 ORDER BY 2 DESC
""").show()
```

```r
# R — mismas vistas, mismo SQL
library(DBI); library(duckdb)
con <- sif_chile_connect()   # devuelve una conexión duckdb con las vistas creadas
dbGetQuery(con, "SELECT count(*) FROM seguros_renta_fija")
```

```js
// Aplicación — el catálogo es JSON plano, el dato es Parquet por Range
const cat = await (await fetch(`${BASE}/api/v2/catalog.json`)).json();
const vista = cat.tablas.find(t => t.id === "ffmm_cartera_extranjera");
```

Para agentes, `llms.txt` + `queries.json` + `schema/` ya son suficientes para
que un agente construya SQL correcto sin ver la web; C añade la ejecución.

---

## 4. Bloqueadores reales, medidos hoy

Ninguno es estructural. Todos son de contrato y todos tienen arreglo barato,
pero **cualquiera de ellos basta para que un usuario nuevo concluya que la API
está rota**.

**Bloqueantes para anunciar (5):** 4.1 identificadores, 4.2 RUT, 4.3 esquema,
4.7 versionado y 4.8 licencia de datos. Los demás (4.4–4.6, 4.9, 4.10) son
mejoras que conviene hacer en la misma pasada porque tocan los mismos archivos.

### 4.1 Tres identificadores por la misma tabla

- `data_manifest.json` usa ids heredados: `seguros_maestro`, `ffmm_maestro`,
  `bancos_cmf_lineas`…
- `SEMANTIC_VIEWS` y `download_catalog.js` usan el nombre canónico:
  `seguros_lista_entidades`, `ffmm_lista_entidades`…
- El nombre visible es `seguros.lista_entidades`.

Consecuencia: **16 de las 89 tablas del manifiesto no cruzan con el catálogo de
descargas** por id. Una API necesita un identificador estable y único, con
alias documentados y una regla de deprecación. Es la decisión más cara de
cambiar después; hoy cuesta 2 horas.

### 4.2 El RUT no está homologado donde el README dice que sí

Medición sobre lo publicado (no sobre los scripts):

- `seguros_renta_fija.nro_rut` está en formato `97006000-6` (**cuerpo-DV**) en
  las 2.321.911 filas.
- `seguros_pactos.nro_rut_activo_objeto` también (`81826800-9`).
- `bancos_lista_entidades.rut` está en formato cuerpo (`97004000`) en las 41 filas.
- El `JOIN` del README (bancos ∩ seguros ∩ FFMM) devuelve **0 filas** hoy.
  Quitando el DV con `split_part(nro_rut,'-',1)` devuelve **15 bancos**,
  exactamente lo que el README afirma: el dato es correcto, lo que no es
  consistente es su representación publicada.

El guardián `scripts/audit_rut_formatos.py` pasa en verde (769 archivos, 0
problemas) porque sólo vigila columnas que empiezan por `rut`; `nro_rut` queda
fuera. Y el README (§4) afirma que "toda la base publica bajo una convención
única" y que los JOIN directos funcionan: columna por columna la afirmación se
cumple salvo en dos (`nro_rut`, `nro_rut_activo_objeto`), que son justo las que
sostienen el ejemplo de portada.

Para una API esto es crítico por dos motivos: (a) los ejemplos son el contrato
y hoy el ejemplo publicado no reproduce; (b) cualquier cliente que cruce
industrias fallará en silencio, que es justo el fallo que el proyecto dice
resolver.

**Arreglo (medio día):** publicar `nro_rut` = cuerpo y `nro_rut_dv` = cuerpo-DV
(como ya hacen 25 columnas `*_dv`), añadir `nro_*` al guardián y meter la consulta
del README en `audit_api.py` con resultado esperado distinto de cero.

### 4.3 Falta esquema para 31 de las 89 tablas

El diccionario cubre 75 tablas / 1.284 columnas; el manifiesto publica 89.
Faltan, entre otras, tablas grandes: `seguros_renta_fija_relevante` (2,3 M
filas), `seguros_tablas_desarrollo` (2,2 M), `bancos_cmf_lineas` (2,0 M).

Un cliente no puede escribir SQL sin saber las columnas. **Arreglo (2 horas):**
generar el esquema desde el Parquet (`DESCRIBE`), no desde el diccionario
editorial; el diccionario añade significado cuando exista, pero la API siempre
publica tipos reales. Añadir al CI: toda tabla del catálogo debe tener esquema.

### 4.4 CORS, content-type y caché en GitHub Pages

- GitHub Pages no permite configurar cabeceras, pero en la práctica responde
  `access-control-allow-origin: *` (reportado con `curl` por la comunidad; no es
  una garantía documentada). De eso depende que una app de otro dominio pueda
  leer catálogo y Parquet: **confirmarlo con un `curl -H 'Origin: …'` antes de
  anunciar nada.** Si faltara, el camino A sigue sirviendo para Python/R/agentes
  y no para navegadores.
- Los `.parquet` se sirven como `application/octet-stream`; correcto para
  descarga, malo para `Content-Encoding`/inspección. No es bloqueante.
- `docs/vercel.json` (y `vercel.json`) fijan `Cache-Control: no-store` para
  `outputs/*.parquet`. Sirve para el visor, es **contraproducente** para una API
  (impide caché de CDN y de cliente). Si se publica la API, separar rutas:
  `/api/v2/**` con `max-age=300`, Parquet con `no-store` sólo donde haga falta.
- `X-Frame-Options: DENY` y CSP están bien y no afectan a consumidores HTTP.

### 4.5 Ancho de banda: 223 descargas del núcleo al mes

GitHub Pages tiene límite blando de **100 GB/mes** de tráfico y **1 GB** de sitio
publicado. El sitio pesa **517 MB** (núcleo: 448 MB en 41 conjuntos).

- 100 GB ÷ 448 MB ≈ **223 descargas completas del núcleo al mes**.
- 100 GB ÷ 496 MB ≈ **206 descargas completas del sitio**.
- Una lectura por Range (lo que hace DuckDB) gasta mucho menos: una consulta
  típica lee pie + grupos de fila, no el archivo. Pero un usuario que hace
  `sif.download("seguros_renta_fija")` sí se lo baja entero (225 MB en 22
  archivos).

**Implicaciones:** (a) el SDK debe leer por Range y cachear en disco, no
descargar todo; (b) documentar el peso antes de cada descarga (el catálogo ya
trae `bytes`); (c) si la API crece, espejar los Parquet en un CDN con egress
gratuito (Cloudflare R2, Hugging Face Datasets) y dejar Pages como escaparate;
(d) no duplicar datos para la API (ver 4.9).

### 4.6 El repositorio ya pesa 468 MB y no hay margen para duplicar

El pack de Git pesa **467,8 MB** y el árbol de trabajo 517 MB; GitHub recomienda
no pasar de 1 GB por repositorio. Si cada corrida mensual agrega ~10 MB, el
margen se agota en pocos años, y **antes** si la API necesita otra copia de los
datos (por ejemplo, JSON precalculados). Regla de oro: una sola copia de los
bytes, N vistas de metadatos.

### 4.7 No hay contrato de estabilidad (y una API es exactamente eso)

Hoy los nombres de vista cambian y se conservan con `LEGACY_VIEW_ALIASES`;
`docs/vocabulario.json` registra `nombres_retirados`. Eso es buena disciplina
interna, pero una API pública exige además: versión en la URL (`/api/v2/`),
política de deprecación (p. ej. 6 meses), `CHANGELOG` de contrato y fecha de
corte por tabla (ya está en `corte`/`ultima_actualizacion`). Coste: 1 día de
redacción; coste de no hacerlo: cada renombre rompe a terceros sin aviso.

### 4.8 La licencia MIT cubre el código, no los datos

Los datos son de la CMF, el BCCh, la Superintendencia de Pensiones y la SUSESO;
sus condiciones de uso no son MIT. Una API pública que redistribuye necesita:
aviso de atribución por fuente, nota de "sin garantía", y una frase sobre qué
puede hacer un tercero con los datos. Es media página de `DATA_LICENSE.md`, pero
sin ella el proyecto no debería llamarse "API pública".

### 4.9 Duplicados que confunden al cliente y engordan el núcleo

`seguros_renta_fija` (105 columnas, 225 MB) y `seguros_renta_fija_relevante`
(21 columnas, 42 MB) tienen **el mismo número de filas (2.321.911)** y los mismos
22 períodos: la segunda es una proyección de la primera. Lo mismo ocurre con
`_relevantes` de acciones, bienes raíces, extranjeros, derivados y préstamos.

Para el navegador tiene sentido (column pruning). Para una API es una trampa:
dos IDs para el mismo hecho, y quien descarga el "núcleo" (448 MB) está bajando
ambas. Hay que documentarlo como `deriva_de: seguros_renta_fija` y decidir cuál
es la canónica. Además hay **4 vistas con 0 filas**
(`seguros_prestamos`, `seguros_bienes_raices_arriendo_morosidad` y sus
`_relevantes`): la API debe marcarlas `vacía: true` en lugar de devolver un
Parquet de 0 filas sin explicación.

### 4.10 Bug encontrado de paso: la auditoría de alias no ve ningún alias

`scripts/audit_consultas_sugeridas.py:37` (`_bloque`) elige el delimitador por la
primera aparición de `[` o `{` en los 200 caracteres siguientes al marcador. En
`const LEGACY_VIEW_ALIASES` aparece un `[` (el de `["seguros_maestro"]`) antes
que el `{`, así que el bloque devuelto es `["seguros_maestro"]` y
`alias_heredados()` devuelve **0 alias** de los 19 declarados. La comprobación de
compatibilidad de nombres existe pero nunca comprueba nada. Arreglo: buscar
desde el `{`. Es relevante ahora porque la API hereda esa promesa de
compatibilidad.

---

## 5. Plan por fases, con criterio de aceptación

| Fase | Qué se entrega | Horas | Criterio de aceptación (medible) |
|---|---|---|---|
| **0 · Decisiones** | Un `docs/api/README.md` con: id canónico, alias, semver, política de deprecación, licencia de datos, "sin SLA / best effort" | 4 | 5 decisiones escritas y aprobadas |
| **0b · Higiene de datos** | `nro_rut`/`nro_rut_dv` normalizados; guardián ampliado a `nro_rut*`; esquema para las 89 tablas | 8 | `audit_rut_formatos.py` verde **y** la consulta del README devuelve >0 filas |
| **1 · Contrato estático** | `docs/api/v2/{catalog,schema,partitions,queries,openapi,llms}.` + `catalog/views.sql` generados por `scripts/build_api.py` | 10 | catálogo cubre 89/89 tablas con esquema; `views.sql` crea las 90 vistas sin error |
| **1a · Data Package** | `datapackage.json` generado (recursos, esquema, PK/FK, hash) validado con `frictionless validate` | 6 | `frictionless validate` en verde; 89 recursos, 0 claves huérfanas |
| **1b · SDK Python** | `sif_chile` (connect/tables/view/download), reutilizando el parser de `SEMANTIC_VIEWS` | 10 | `pip install -e .` y el snippet de §3 corre en máquina limpia |
| **1c · Ejemplos** | `examples/python`, `examples/r`, `examples/javascript`, `examples/agent` (con `llms.txt`) | 8 | cada ejemplo corre contra la URL publicada y no contra `localhost` |
| **1d · Test de contrato en CI** | `scripts/audit_api.py` + paso en `web_audit.yml` | 8 | falla si un link del catálogo da 404, si un esquema no cubre sus columnas reales, si un ejemplo del README/R/Python devuelve 0 filas o si el peso declarado difiere >5 % |
| **2 · Agentes sin código** (opcional) | `sif-mcp` en **modo código** (2 herramientas) sobre el contrato de Fase 1 | 8 | un agente responde "¿cuánto invierten los FFMM en el exterior?" con <1.000 tokens de herramientas |
| **3 · SQL sobre HTTP** (opcional) | `quack_serve` + proxy TLS + cuotas | 24–40 | p95 < 2 s en consultas del núcleo; coste acotado por cuota |

**Total hasta "una API pública v1 anunciable": ~54 h-persona (7 días)**, de las
cuales 12 h no son API sino arreglar lo que la API expondría. Sin ellas, el
contrato en sí son ~42 h.

R no se pudo ejecutar en este entorno (no está instalado); el snippet usa
`duckdb`/`DBI`, que son las dependencias estándar, pero debe entrar en CI antes
de publicarse como "soportado". Es el único punto de la Fase 1 con incertidumbre
(±4 h).

---

## 6. Qué NO conviene hacer

1. **Duplicar los datos en JSON** para "tener una API". 19,8 M filas no caben y
   el repo ya está en la mitad del límite.
2. **Montar un servidor** sólo para devolver `SELECT *` de una tabla: eso ya lo
   hace un Parquet por HTTP con Range y sin logística.
3. **Prometer una API sin test de contrato.** El fallo de 4.2 convive con un
   guardián en verde y con un README que afirma lo contrario, porque **ningún
   test ejecuta el ejemplo de portada**. Una API sin ese test repetirá el
   problema a escala.
4. **Llamar "API" a `download_catalog.js`.** Es un archivo JavaScript con
   `window.DOWNLOAD_CATALOG = {…}`: un cliente Python no lo puede parsear sin
   trucos, y no tiene URL versionada ni esquema.
5. **Publicar la API en el mismo dominio con `no-store`.** Mata la caché de CDN
   justo cuando el límite es de ancho de banda.

---

## 7. Riesgos residuales

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Se supera el tráfico blando de Pages | Media si la API se difunde | SDK con caché local y Range; espejo en CDN si crece |
| Terceros dependen de un nombre y el proyecto lo renombra | Alta sin política | semver + alias + deprecación de 6 meses |
| Las fuentes cambian de formato y rompen la serie | Ya ocurre | Los flujos fallan en vez de publicar basura (ya implementado); la API debe exponer `corte` y `ultima_actualizacion` para que el cliente detecte huecos |
| Un agente escribe SQL caro y tumba la máquina del usuario | Media | `sql_guard.js` ya existe para el navegador; portarlo al SDK (`LIMIT` por defecto, sin `INSTALL`/`ATTACH` arbitrarios) |
| Interpretación de los datos como asesoría financiera | Baja | Aviso ya presente; reforzarlo en `llms.txt` y en la respuesta del MCP |
| Adoptar DuckDB 2.0 recién publicado (2026-10-21) | Media | Fijar versión; el contrato estático no depende de Quack, así que se puede posponer esa pieza sin frenar Fase 1 |
| Depender de una herramienta de terceros (frictionless) para validar | Baja | El `datapackage.json` es un JSON; la validación es una comodidad, no un requisito del formato |

---

## 8. Recomendación concreta

1. **Sí a P3**, pero reformulado: *"contrato de datos público, documentado y
   versionado, con SDK y ejemplos"*, no *"API REST con endpoints de consulta"*.
2. **Orden:** Fase 0 → 0b (arreglar RUT y esquema) → 1a (Data Package) → 1 →
   1b/1c → 1d. Anunciar sólo cuando 1d esté en verde.
3. **Primer hito visible y barato:** `datapackage.json` + `views.sql` + ejemplo
   de Python. Eso ya convierte "clone el repo y lea el README" en tres líneas, y
   es lo que hace que un analista de R o un agente puedan usar el sistema hoy.
   El `datapackage.json` se valida con `frictionless validate`, así que el primer
   día ya hay una compuerta de calidad en CI.
4. **Copiar, no inventar**: el patrón de `llms.txt` y el cliente
   `search()/fetch()` salen de `owid/etl`; el layout de metadatos y el paquete R
   gemelo, de `basedosdados/sdk`; las reglas de agente (RUT, paginación,
   catálogos de códigos), de `mcp-cmf-chile`. Los tres son MIT y resuelven el
   mismo tipo de problema: datos públicos, curados y documentados para que los
   use alguien de fuera del equipo.
5. **Decisión pendiente del dueño (bloquea la Fase 0):** ¿basta el contrato
   estático o se quiere SQL remoto? Si es lo segundo, hoy sale casi gratis en
   código (Quack de DuckDB 2.0) pero sigue habiendo proceso, TLS, cuotas y
   egress, y el README deja de poder decir "sin backend".

---

## 9. Bases reutilizables: siete proyectos con API ya montada

Criterio de selección: licencia compatible con la MIT del proyecto, mantenido en
2026, y que resuelva **una pieza concreta** del contrato. No se propone forkear
ninguno: se copia la pieza y se adapta.

| Proyecto | Licencia | Qué montó | Qué copiar | Qué no copiar |
|---|---|---|---|---|
| [`owid/etl`](https://github.com/owid/etl) | MIT | Catálogo de datos público con cliente propio | Forma de la URL versionada, `llms.txt`, patrón `search()/fetch()` | Duplicar bytes por versión |
| [`basedosdados/sdk`](https://github.com/basedosdados/sdk) | MIT | Metadatos en el repo + clientes Python/R/Stata | Layout de metadatos, API del cliente, paquete R gemelo | Depender de BigQuery y del proyecto de facturación del usuario |
| [`JoaquinMulet/mcp-cmf-chile`](https://github.com/JoaquinMulet/mcp-cmf-chile) | MIT | MCP con 91 operaciones sobre la CMF | Reglas de agente, paginación, catálogo generado | 88 herramientas en el contexto del modelo |
| [`frictionlessdata/datapackage`](https://github.com/frictionlessdata/datapackage) + `frictionless-py` | Unlicense / MIT | **Estándar** de descripción de datos | `datapackage.json` con esquema, PK, FK y hashes; validación en CI | Nada: es sólo un estándar |
| [`simonw/datasette`](https://github.com/simonw/datasette) | Apache-2.0 | Explorador con API JSON sobre SQLite | Idea de "una tabla, N serializaciones" y `_shape=array` | Montarlo como servicio (SIF no lo necesita) |
| [`turicas/brasil.io`](https://github.com/turicas/brasil.io) | GPL-3.0 | API REST sobre Postgres con token | Contrato de formatos, paginación y límites documentados | La operación completa y su licencia |
| [DuckDB 2.0 LTS](https://duckdb.org/2026/10/21/announcing-duckdb-200) | MIT | Motor + protocolo cliente-servidor | `views.sql`, Quack y *agent mode* | Servir SQL a internet sin cuotas |

### 9.1 owid/etl — la referencia más cercana a lo que falta

Es un catálogo de datos públicos con API **documentada por lenguaje** y cliente
propio. Tres piezas concretas:

**a. URL estable y versionada.** Su documentación pública define el patrón:

```
https://catalog.ourworldindata.org/[channel]/[dataset]/[version]/[dataset]/[table].parquet
```

La versión es una **fecha** (`2025-04-07`), así que la URL es inmutable y
citable. Hoy SIF publica en `docs/outputs/…`, donde la ruta es la misma para
todas las versiones: el consumidor no puede pedir "lo que estaba publicado el
2026-06-30" sin apoyarse en un commit. Para una API esto es una carencia real,
pero **SIF no puede copiar la solución de OWID** (duplicar bytes por versión) por
el límite de 1 GB: tiene que versionar por **manifiesto con SHA-256**, que ya
existe en `inventario_fuentes.csv`.

**b. `llms.txt`.** Mantienen un archivo por biblioteca
(`docs/libraries/catalog/llms.txt`) con la misma información que el README pero
en el formato que los agentes leen, y desde la documentación enlazan
explícitamente: *"An `llms.txt` file is available for AI agents and LLM tools"*.
Cuesta 40 líneas y es lo que hace que un agente use bien el catálogo.

**c. Cliente con `search()` + `fetch()`.**

```python
client = Client()
results = client.tables.search(table="population", namespace="un")
tb = results[0].fetch()
```

Es la interfaz correcta para SIF: buscar (índice) y traer (Parquet). SIF ya tiene
`docs/outputs/indice_busqueda.json`; lo que falta es empaquetarlo en esa forma.

También documentan el acceso SQL con DuckDB y con Datasette en pestañas
separadas, y mantienen un *skill* de agente (`lib/catalog/skills/owid-catalog`)
en el repositorio.

### 9.2 basedosdados/sdk — el layout de metadatos y el gemelo en R

Metadatos **en el repositorio**, un directorio por conjunto y un YAML por tabla:

```
bases/br_ibge_pib/dataset_config.yaml      # título, organización, descripción, temas
bases/br_ibge_pib/municipio/table_config.yaml
```

Clientes en tres lenguajes desde un solo repo (`python-package/`, `r-package/`,
`stata-package/`) con la misma superficie:

```
read_table(dataset, table)   read_sql(query)   download(query, path)
list_dataset_tables()        get_table_columns()
```

Esto valida dos decisiones del plan: (1) el **esquema debe viajar con el dato**
en un YAML/JSON por tabla, no sólo en el diccionario editorial; (2) el paquete de
R no es un extra: es la segunda puerta de entrada y cuesta poco si comparte
metadatos con el de Python. Lo que **no** hay que copiar es el acoplamiento a
BigQuery y al `billing_project_id` del usuario: SIF no cobra ni pide cuenta.

### 9.3 mcp-cmf-chile — mismo dominio, y corrobora la convención de RUT

Proyecto MIT, TypeScript, del mismo dominio (CMF), con dos ideas que sirven
aunque no se adopte MCP:

- **`docs/catalogo-agentes.md` generado**: el catálogo de lo que ve el agente
  (nombre, descripción, parámetros requeridos, `outputSchema` y anotaciones) se
  emite desde el propio servidor y se versiona. Es el "manual del agente" que
  SIF necesita para `llms.txt`.
- **Reglas explícitas en el `INSTRUCTIONS`**: RUT canónico, paginación con
  `next_offset`/`total` ("nunca asuma que la primera página es el total"),
  catálogos de códigos para no pedir códigos de memoria, y qué hacer ante
  `sin datos`. Son exactamente las trampas en las que cae un agente con 89
  tablas.
- **Catálogos de códigos** (`cmf_codigos`): bancos, seguros y cartera de FFMM.
  SIF puede exponer lo mismo con su propia tabla maestra de entidades, que hoy
  está repartida por sector.

Y un dato que importa para el arreglo 4.2: su servidor documenta la misma
convención canónica de SIF — *"todo catálogo entrega el campo `rut` en ese mismo
formato, sin puntos ni DV, y si la fuente traía el DV viaja en `rut_dv`"*.
O sea: `nro_rut` con DV no es una convención alternativa, es una **desviación
aislada** del estándar que ya siguen 87 tablas de SIF y un proyecto externo del
mismo ecosistema.

Lo que no hay que copiar: 88 herramientas cuestan ~37.000 tokens de contexto por
petición; ellos mismos lo midieron y por eso ofrecen un "modo código" con 2
herramientas y ~736 tokens. Si SIF llega a MCP, debe nacer en modo código.

### 9.4 frictionlessdata — el estándar que cubre medio contrato sin escribir código

`datapackage.json` es un estándar abierto (Unlicense; implementación MIT en
`frictionless-py`, 846★, último release 2026-10-15) para describir datos
estáticos: recursos (ruta, formato, bytes, hash), **esquema de tabla** (nombre,
tipo, restricciones, `primaryKey`, `foreignKeys`), licencia y fuentes. Se valida
con `frictionless validate` y lo consumen herramientas en Python y en R.

Para SIF reemplaza, sin coste, buena parte de los artefactos que el plan
proponía a mano:

| Artefacto propuesto en §3 | Lo cubre Data Package |
|---|---|
| `catalog.json` | `datapackage.json` (`resources[]` con nombre, ruta, bytes, hash) |
| `schema/{id}.json` | `schema.fields[]` por recurso, con tipos y restricciones |
| `partitions/{id}.json` | un `resource` por archivo, más una tabla lógica por `name` |
| Relaciones PK/FK | `primaryKey` y `foreignKeys` (SIF ya mide cardinalidad en `cardinalidad_relaciones.json`) |
| Integridad | `hash` por recurso (ya hay SHA-256 en `inventario_fuentes.csv`) |

Lo que **no** cubre: versionado del contrato, política de depuración, `llms.txt`
ni el DDL de vistas. Esas siguen siendo propias.

### 9.5 simonw/datasette — una tabla, N serializaciones

Datasette (Apache-2.0) muestra el patrón barato: la misma tabla responde como
HTML, JSON (`?_shape=array`) y CSV (`?_size=`), sin escribir endpoints. SIF ya
hace eso con Parquet/CSV/Excel en la pestaña Descargas; la lección es **no
inventar un formato nuevo** para la API, sino declarar los que ya existen.

### 9.6 turicas/brasil.io — el techo de esfuerzo

Brasil.io (GPL-3.0) muestra el patrón caro: Postgres + Django REST Framework +
tokens + límites por usuario + operación 24/7. Es el techo de esfuerzo, y sirve
para dimensionar: esa es la factura de "tener una API REST de verdad", no la de
publicar un contrato sobre archivos estáticos. Su licencia, además, sería
incompatible con MIT si se copiara código.

### 9.7 DuckDB 2.0 LTS: lo que cambió ayer

El 2026-10-21 DuckDB publicó la 2.0.0 LTS (soporte hasta al menos octubre de
2027) con dos novedades que tocan este plan de cerca:

- **Quack**, el protocolo cliente-servidor sobre HTTP, ya es estable: cualquier
  proceso DuckDB se vuelve servidor con `CALL quack_serve(token = '…')` y otro se
  conecta con `ATTACH 'quack:localhost' AS qk (TOKEN '…')` o `CONNECT`. Es decir,
  **"SQL sobre HTTP" deja de requerir escribir un servidor**: no hay worker, no
  hay driver, no hay esquema de respuesta que mantener.
- **Agent mode** en la CLI: detecta que lo maneja un agente y emite tablas
  Markdown compactas, avisa del truncamiento, devuelve los errores en JSON y
  estima el coste antes de ejecutar (en TPC-H, −59 % de tokens leídos).

Consecuencias para la propuesta:

1. La Fase 3 baja de 60–120 h a ~24–40 h, porque el servidor ya existe. **No
   desaparece el problema de operación**: sigue habiendo proceso, TLS, cuotas,
   egress y disponibilidad.
2. Quack sólo habla con DuckDB (Python, CLI y R cuando publique 2.0; los
   clientes de Go, Java y R llegan "en unos días" según la nota de release). Un
   agente que sólo hace HTTP **no** puede usarlo, y un navegador tampoco (aunque
   DuckDB-Wasm sí sabe hablarlo, el sitio no tiene servidor al que conectarse).
3. Para agentes que pueden ejecutar código, **la interfaz ya está construida**:
   `duckdb` + `views.sql` + agent mode. Eso degrada MCP de "Fase 2 necesaria" a
   "opcional para agentes sin capacidad de ejecutar código".
4. Riesgo nuevo: la 2.0 tiene un día de vida. Si se adopta, fijar versión (hoy
   el sitio fija `duckdb-wasm` 1.28.0) y no mezclar el formato de almacenamiento
   2.0 con el de 1.x, que no lo puede leer.

### 9.8 Cómo se ensambla (y qué queda fuera)

| Pieza del contrato | De dónde sale | Trabajo propio |
|---|---|---|
| Descripción del paquete, esquema, PK/FK, hashes | `datapackage.json` (Frictionless) | Generador desde `data_manifest.json` + diccionario |
| Catálogo y búsqueda | `owid-catalog` (`search()`/`fetch()`) | Envolver `indice_busqueda.json` |
| Cliente Python | `basedosdados` (`read_table`/`read_sql`/`download`) | Adaptar a DuckDB + Parquet remoto |
| Cliente R | `basedosdados/r-package` | Paquete delgado sobre `duckdb` |
| DDL de las 90 vistas | `SEMANTIC_VIEWS` de SIF | Generar `views.sql` (42 KB) |
| Guía para agentes | `owid` `llms.txt` + `catalogo-agentes.md` de mcp-cmf | 40 líneas + reglas (RUT, paginación, periodos) |
| SQL remoto (si se quiere) | Quack de DuckDB 2.0 | Servidor, TLS y cuotas |
| Versionado y deprecación | ninguno de los anteriores | Propio: `/v2/`, política de 6 meses |

Lo que se descarta tras la revisión: escribir un OpenAPI a mano para endpoints
que no existen (se genera desde el catálogo o no se publica), duplicar bytes por
versión como OWID (no cabe en 1 GB), y montar Postgres + DRF como brasil.io
(la operación se come el proyecto).

### 9.9 Contexto chileno

- La CMF ya tiene **API oficial v3** (`api.cmfchile.cl`, key gratuita) para
  indicadores y balances bancarios. SIF no debe duplicar ese rol: su valor es lo
  que la API oficial no entrega (carteras por instrumento, 25 años homologados,
  cruces entre industrias).
- La normativa de Finanzas Abiertas (Ley 21.521, NCG 514) exige para las APIs
  reguladas **OpenAPI 3.1, JSON, REST, OAuth 2.0, 99 % de disponibilidad y
  ≤ 3,5 s**. No aplica a SIF (no es un participante del SFA), pero marca el
  vocabulario que el mercado chileno espera: si SIF publica OpenAPI 3.1 como
  documentación del contrato, habla el idioma local aunque sirva archivos.
- SIF no figura en [`juanbrujo/listado-apis-publicas-en-chile`](https://github.com/juanbrujo/listado-apis-publicas-en-chile),
  que es donde se buscan las APIs chilenas. Un PR de tres líneas, después de que
  exista el contrato.

---

## 10. Cómo se midió

```bash
# volumen y forma de lo publicado
du -sh docs/outputs                                  # 517M
find docs/outputs -name '*.parquet' | wc -l           # 689
find docs/outputs -name 'manifest.json' | wc -l       # 53

# catálogo, diccionario y consultas
python3 -c "import json;m=json.load(open('data_manifest.json'));print(len(m['tables']),m['total_records'])"
python3 -c "import json;d=json.load(open('docs/reproducibilidad/diccionario.json'));print(len(d['datos']),d['columnas'])"

# vistas semánticas y tiempos (requiere duckdb)
python3 - <<'PY'
import sys; sys.path.insert(0,'scripts')
import audit_consultas_sugeridas as a, duckdb
con=duckdb.connect(); a.registrar(con,a.vistas_semanticas(),a.alias_heredados())
print(con.sql("SELECT count(*) FROM seguros_renta_fija"))
PY

# formatos de RUT realmente publicados
python3 -c "
import duckdb;c=duckdb.connect()
print(c.sql(\"select nro_rut from 'docs/outputs/seguros/renta_fija/*.parquet' limit 1\").fetchall())
print(c.sql(\"select rut from 'docs/outputs/bancos/cmf_b1_b2_r1/*.parquet' limit 1\").fetchall())"

# guardián de RUT (pasa en verde pese a lo anterior)
python3 scripts/audit_rut_formatos.py
```

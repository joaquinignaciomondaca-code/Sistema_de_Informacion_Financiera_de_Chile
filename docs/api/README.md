# Contrato de la API pública (v2)

**v2** (2026-10-23): recorta las columnas de control interno que viajaban en cada
fila (huellas, rutas y URLs de la fuente, claves sintéticas). Quitar columnas
rompe clientes, así que es un cambio **mayor**: el descriptor pasa a `2.0.0` y la
carpeta a `api/v2/`. El contrato 1.x queda retirado, con un aviso en `api/v1/`.

**v1 completa** (2026-10-22): contrato estático, SDK de Python, ejemplos en
Python/R/JavaScript y test de contrato en CI.

Lo que hay aquí es el **contrato estático** de la API: artefactos generados
desde los datos publicados, versionados junto al código y verificados en cada
CI. No son documentación escrita a mano, así que no pueden desviarse de lo que
el usuario descarga.

| Archivo | Qué responde |
|---|---|
| `reconciliacion.csv` | Qué objeto consume el cliente, con qué datos se sirve y en qué estado está (publicado, derivado o vacío). |
| `esquemas.json` | Qué columnas y qué tipos tiene cada objeto, con el significado del diccionario editorial cuando existe. |
| `../metricas_publicadas.json` | Reconciliación generada de unidades ETL/API/Descargas, con definiciones, desglose por sector y controles de filas, bytes, IDs, rutas, particiones y filtros. |
| `claves.csv` | Qué combinación de columnas identifica una fila (verificada sobre **todas** las filas) y qué claves foráneas cierran contra su lista de entidades. |
| `v2/datapackage.json` | El **Data Package**: 86 recursos con ruta, tamaño, SHA-256, esquema y `primaryKey`, legible por cualquier herramienta Frictionless. |
| `reglas.json` | Las comprobaciones con su nivel (invariante / expectativa / informativo) y las excepciones declaradas con su motivo. Hoy: **0 excepciones**. |
| `prueba_maquina_limpia.log` | Evidencia de que un consumidor **sin el repo** descubre el catálogo, lee el esquema y consulta por HTTP. |
| `mcp.log` | Evidencia del servidor MCP: dos herramientas, 191 tokens de contexto y la pregunta del README respondida con dos llamadas. |
| `test_contrato.log` | Evidencia del test de contrato: 908 rutas HTTP sin 404, 1.474 columnas comparadas con `DESCRIBE`, 105 vistas de catálogo + 4 auxiliares temporales, 159 consultas, 728 archivos verificados y cobertura manifiesto ↔ catálogo. El corte actual tolera y nombra una columna sin valores. |
| `v2/catalog.json` | El índice de los 90 objetos: estado, filas, bytes, clave, corte y a dónde ir por más detalle. |
| `v2/schema/{id}.json` | Columnas, tipos, significado y clave de cada objeto. |
| `v2/partitions/{id}.json` | Los archivos que componen el objeto, con período y SHA-256. |
| `v2/queries.json` | Las 159 consultas de la web, con **id estable** y la expectativa declarada. |
| `v2/resultados/index.json` | El resultado ya calculado de las 159 consultas: filas, columnas, tope, `sha256` y URL de cada uno. Para quien necesita el número sin descargar los ≈488 MB del catálogo Parquet. |
| `v2/openapi.json` | **Sólo** las 11 rutas GET que existen. |
| `v2/views.sql` | Las 105 vistas SQL de catálogo (86 objetos con datos + 19 alias) y las auxiliares temporales de los chips: `*_ultimo_periodo` sólo muestra ese período; `*_ultima_particion` puede contener varios períodos del último archivo. No son objetos catalogados ni descargas. |
| `llms.txt` | La puerta de entrada para un agente: qué hay, cómo se consulta, qué no suponer. Sus cifras y rutas se auditan como el resto. |

Se regeneran con:

```bash
python3 scripts/build_reconciliacion.py   # docs/api/reconciliacion.csv
python3 scripts/build_esquemas.py         # docs/api/esquemas.json
python3 scripts/verificar_claves.py       # docs/api/claves.csv
python3 scripts/build_api.py              # docs/api/v2/datapackage.json
python3 scripts/auditar_datapackage.py    # valida el descriptor
python3 scripts/probar_maquina_limpia.py  # consumidor sin el repo
python3 scripts/build_contrato.py         # catálogo, esquemas, particiones, consultas, OpenAPI y vistas
python3 scripts/build_download_catalog.py # catálogo de descargas de la web
python3 scripts/build_metricas_publicadas.py # reconciliación ETL/API/Descargas
python3 scripts/build_resultados.py       # resultados de las 159 consultas
python3 scripts/auditar_contrato.py       # audita el contrato
python3 scripts/probar_ejemplos.py        # ejemplos de Python y JS
python3 scripts/test_contrato.py --autoprueba  # test del consumidor (~7 s)
python3 scripts/auditar_mcp.py            # servidor MCP y presupuesto
python3 scripts/build_estado_claves.py    # docs/js/estado_claves.js (Diccionario y visor)
python3 scripts/build_og_image.py         # assets/og_sif_1200x630.png   (tarjeta social)
python3 scripts/build_metadatos.py        # <head> social, robots.txt y sitemap.xml
python3 scripts/construir_reproducibilidad.py  # docs/reproducibilidad/
```

Los tres últimos existen para que la web no repita a mano lo que ya está medido:
el estado de la clave de cada tabla sale de `claves.csv`, y la descripción y las
cifras de la tarjeta social salen de `catalog.json`. Si se escribieran a mano,
en dos releases dirían otra cosa.

Y el CI falla si quedan desactualizados (`--check` en cada uno) o si algo del
contrato deja de cumplirse.

Como los datos cambian solos, el flujo **«Contrato derivado»**
(`.github/workflows/contrato_publicado.yml`) regenera estos archivos cuando un
publicador deja filas nuevas bajo `docs/outputs/`. Sin él, cada actualización
diaria del Banco Central obligaba a regenerar a mano: el contrato quedaba con un
`data_release` viejo y la auditoría fallaba en el siguiente push.

## `reconciliacion.csv`

Cruza los tres niveles —objeto del contrato, entrada de `data_manifest.json` y salida física— porque no son 1:1: hay objetos que usan un alias del nombre heredado y una tabla ETL (`bancos_cmf_lineas`) que se publica como dos vistas con archivos filtrados distintos.

| Columna | Significado |
|---|---|
| `objeto` | Nombre de la vista que escribe el cliente (`FROM bancos_balance`). |
| `nombre_visible` | Rótulo heredado de `data_manifest.json`; no es el título del objeto ni identifica el archivo. Para el nombre de publicación, usa `titulo` en `v2/catalog.json`. |
| `manifest_id` | Fila de `data_manifest.json` que lo respalda; vacío si no hay dato. |
| `puente` | Cómo se emparejó: `directo`, `alias` (nombre heredado) u `origen_compartido` (una entrada ETL da origen a dos vistas; no implica que compartan el archivo publicado). |
| `nivel` | `nucleo`, `secundario`, `archivo` o `registro`. |
| `estado` | `publicado`, `derivado` (proyección de otro objeto) o `vacio` (sin particiones). |
| `motivo` | Por qué está vacío o de dónde deriva. |
| `deriva_de` | Objeto del que es proyección, si aplica. |
| `particiones`, `filas`, `bytes` | Tamaño real publicado. |
| `corte`, `ultima_actualizacion` | Cobertura temporal y fecha del último dato. |

Estado actual: **90 objetos API** = 79 publicados + 7 derivados + 4 sin particiones, reconciliados con 89 entradas ETL. El puente se reparte en 73 directos, 15 alias y 2 de origen compartido. La entrada bancaria `bancos_cmf_lineas` se divide en dos vistas; `bancos_balance` y `bancos_resultados` publican Parquet distintos y no exponen el archivo combinado. Filas/bytes y rutas por ID entre contrato API y Descargas se contrastan en [`../metricas_publicadas.json`](../metricas_publicadas.json).

## `esquemas.json`

```jsonc
{
  "contrato": "sif-api/esquemas",
  "version": "v2",
  "resumen": { "objetos": 90, "con_esquema": 86, "filas_unicas": 19777522, ... }, // suma sobre rutas Parquet distintas; no desduplicación de valores de fila
  "objetos": {
    "bancos_balance": {
      "manifest_id": "bancos_cmf_lineas",
      "nombre_visible": "bancos.cmf_lineas_b1_b2_r1", // rótulo heredado del origen
      "sector": "bancos",
      "estado": "derivado",
      "particiones": 56,
      "filas": 722931, // sólo las filas B1/B2 de esta vista
      "archivo": "outputs/bancos/balance_b1_b2/2022-01/lineas.parquet", // sólo B1/B2
      "filtro": "familia_archivo_fuente IN ('B1', 'B2')",
      "columnas": [
        { "nombre": "periodo", "tipo": "VARCHAR", "rol": "Fecha",
          "significado": "Periodo mensual del archivo CMF en formato YYYY-MM.",
          "criterio_contable": "No aplica" }
      ]
    }
  }
}
```

Reglas que el CI verifica:

1. **El tipo es el del Parquet**, en nombres de DuckDB (`VARCHAR`, `BIGINT`,
   `DOUBLE`, `DATE`…), que es lo que devuelve `DESCRIBE` sobre la vista. El
   diccionario editorial añade `rol`, `significado` y `criterio_contable`, y
   **nunca** cambia el tipo: si discrepa, manda el Parquet y el CI falla hasta
   que se corrija el diccionario.
2. **Todas las particiones de un objeto comparten esquema.** Si una tabla
   cambiara de forma según el corte, el script falla en vez de publicar dos
   verdades.
3. **Las 89 tablas del manifiesto tienen objeto** y los 90 objetos están en la
   reconciliación.
4. **Una columna vacía se declara.** Si una columna no tiene ningún valor en
   ninguna partición, se publica con el tipo que promete el diccionario (o
   `VARCHAR`) y dos marcas explícitas: `"tipo_fisico": "null"` y
   `"sin_valores": true`. Hoy es una columna (`agf_lista_entidades.codigo_cmf`),
   declarada y explicada; no es un error de tipos.
5. **`filas` cuenta lo que recibe cada objeto.** `bancos_balance` publica sólo
   los 722.931 registros B1/B2 y `bancos_resultados` sólo los 1.240.061 R1, en
   archivos Parquet separados y sin solape. Suman 1.962.992 filas de la tabla
   fuente `bancos_cmf_lineas`; ningún objeto balance/resultados entrega por
   error el archivo combinado B1+B2+R1.
6. **Los 4 objetos sin dato no desaparecen**: se publican con `estado: "vacio"`,
   `columnas: []` y `motivo_sin_esquema`.
7. **«Tiene archivo» y «tiene filas» son cosas distintas.** `fi_bienes_raices`
   publica su esquema con un Parquet vacío (0 filas y las 15 columnas) para que
   la vista SQL exista: cuenta en `totales.con_datos` (86) y no en
   `totales.con_filas` (85). Los dos números van con nombre propio para que
   nadie tenga que restarlos a mano.

Estado actual: 86 objetos con esquema, 1.474 columnas (3 sin documentar en el
diccionario y 1 sin valores en origen). En `esquemas.json`, `filas_unicas` suma
las filas de cada ruta Parquet distinta una sola vez; `filas_por_objeto` suma lo
que recibe cada vista y puede volver a contar una ruta compartida. Ninguno de los
dos campos desduplica valores de fila. Las unidades y la reconciliación vigente
se explican en [`metricas_publicadas.json`](../metricas_publicadas.json).

Las cifras que suelen confundirse están reconciliadas, con sus definiciones y procedencia, en [`metricas_publicadas.json`](../metricas_publicadas.json):

| Cifra | Fuente/campo | Qué cuenta |
|---|---|---|
| 89 | `data_manifest.json: total_tables` | entradas ETL, no objetos API |
| 90 | `catalog.json: totales.objetos` | objetos lógicos API; una tabla bancaria de origen se divide en dos vistas |
| 90 | `download_catalog.js: conjuntos` | elementos de descarga: 74 principales + 15 fuera de foco + 1 oculto |
| 86 | `catalog.json: totales.con_datos` | objetos con una o más particiones, incluido el Parquet vacío |
| 85 | `catalog.json: totales.con_filas` | objetos con más de cero filas |
| 159 | `catalog.json: totales.consultas` | consultas publicadas con resultado precalculado |

## `v2/datapackage.json`

Un recurso por objeto (86), con las particiones en `path` y el detalle en
`sif.particiones`. Los campos salen de `esquemas.json` —no hay ni uno escrito a
mano—, y los tipos se traducen a Table Schema (`VARCHAR` → `string`,
`BIGINT` → `integer`, `DOUBLE` → `number`).

`primaryKey` **sólo aparece cuando está probada** sobre todas las filas: 63 de
86 recursos (48 verificadas desde la definición y 15 propuestas por el análisis
que también pasan unicidad). De los 23 recursos restantes, 22 contienen filas
idénticas que impiden una clave única y uno (`fi_bienes_raices`) está vacío; en
este último no hay filas cuya clave pueda probarse.

En `catalog.json` y en cada `schema/{id}.json`, la ausencia de clave se publica
como `"primaryKey": null` —nunca `[]`, que se leería como una clave de cero
columnas—. Son 27 objetos: 22 con filas repetidas, uno sin filas y cuatro sin
particiones. El desglose vigente de estados está en [`claves.csv`](claves.csv).

El descriptor pasa a **2.0.1** en ese mismo cambio: retirar una afirmación falsa
es una corrección, no una funcionalidad nueva, pero sí cambia lo que el
descriptor dice, así que se versiona.

Y a **2.1.0** al añadir `totales.con_filas`: un campo nuevo es un cambio menor,
no rompe a ningún cliente y no toca ni una fila ni una columna.

Y a **2.2.0** al añadir `procedencia` a `ccaf_maestro` en `catalog.json` y en
`resources[].sif` del Data Package. El campo separa las fuentes directas que
alimentan las altas automáticas actuales de la procedencia editorial del
universo inicial. `fuente` y `atribucion` se conservan para la atribución y las
condiciones de uso; no implican que toda la lista base se descargue de CMF en
cada actualización.

Y a **2.3.0** al incorporar dentro de `procedencia` el estado de revisión de
condiciones de reutilización por fuente para ese objeto: CMF verificada y
SUSESO pendiente de verificación. Ese estado documenta lo que se sabe; no
resuelve por sí mismo la autorización de la fuente histórica.

El 2026-10-23 se corrigió un estado histórico del descriptor: **13 claves que la
verificación anterior había aprobado no eran únicas** (`ffmm_cartera_nacional`
entre ellas, con 160.564 filas repetidas). Un error de
`scripts/verificar_claves.py` marcaba las repeticiones con una comparación de
tuplas que DuckDB no evalúa fila a fila, y el vacío se leía como «no hay
duplicados». Esto describe la corrección de aquel corte, no el número de fallos
vigentes. Ver [`docs/notas/claves_duplicados_2026-10-23.md`](../notas/claves_duplicados_2026-10-23.md).

El `hash` de cada recurso es el SHA-256 de la concatenación de los SHA-256 de
sus particiones, y el conjunto de todos ellos produce el `data_release`: no es
una fecha elegida a mano, es el contenido. El vigente se lee en `catalog.json`
—no se copia aquí, porque cambia con cada serie diaria—.

### URLs

El descriptor publica **URLs absolutas** del sitio canónico:

```
https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/
```

Por dos motivos: `frictionless` rechaza las rutas con `..` («path is not safe»),
y un consumidor remoto necesita una dirección completa. **Decisión D1**: Pages
publica la API y Vercel **redirige `/api/*` a Pages con un 307** (temporal a
propósito, para que revertirlo siga siendo posible). El visor sigue viviendo en
Vercel sin cambios.

## Claves

`claves.csv` responde dos preguntas sobre las filas publicadas:

- **PK (86 objetos con archivo)**: 48 verificadas, 15 propuestas cuya unicidad
  pasó el análisis, 22 objetos sin combinación única porque contienen filas
  idénticas y 1 objeto sin datos (`fi_bienes_raices`). El catálogo/Data Package
  declara clave en 63 recursos. **Ninguna clave que se publica como verificada
  falla en el corte auditado.**
- **FK (44 relaciones evaluadas)**: 36 cierran; 6 no tienen destino publicado;
  1 presenta 3.604 valores huérfanos de 7.962 (45,3 %) en patrimonios separados;
  y 1 está sin datos, por lo que no se puede medir.

### Hallazgo histórico de la auditoría (2026-10-23; tarea 1a.9)

En esa revisión, 8 claves declaradas que no eran únicas compartían este vicio:
**la clave natural omitía una dimensión**. Es un hallazgo del estado anterior, no
el conteo vigente; el estado actual de PK/FK está resumido arriba y en
`claves.csv`.

| Objeto | Declaraba | Clave real | Qué faltaba |
|---|---|---|---|
| `corredoras_bolsa_balance` / `_resultados` | `codigo_fecu` | `periodo + rut + codigo_fecu` | el periodo y la entidad |
| `ffmm_balance` / `_resultados` | `orden + codigo_cuenta` | `periodo + run_fondo + codigo_cuenta` | el periodo y el fondo |
| `fi_balance` / `_resultados` | `periodo + contexto + codigo_cuenta` | `+ run_fondo` | el fondo de inversión |
| `patrimonios_separados_balance` | `archivo` | `periodo + codigo_patrimonio + cuenta + archivo + orden_en_balance` | todo menos el archivo |
| `seguros_lista_entidades` | `rut_aseguradora` | `sector + rut_aseguradora` | el sector |

El caso de seguros no era un dato sucio: la misma aseguradora tiene registro de
**vida** y de **generales**, así que `sector + rut` da 84 de 84.

## El contrato estático (`v2/`)

`catalog.json` es la puerta de entrada: 90 objetos con `estado`, `filas`,
`bytes`, `primaryKey` y las rutas a su esquema y sus particiones. Si la
procedencia necesita distinguir entradas directas de una base editorial, el
objeto `procedencia` lo declara por separado (hoy, en `ccaf_maestro`). Los 159
`queries.json` traen **id estable** (`titulo-slug` + 6 hex del SQL): un id no
cambia mientras el SQL no cambie, así que sirve para citar una consulta en un
artículo o en una prueba.

### `views.sql`

Se ejecuta tal cual y crea las 105 vistas de catálogo más cuatro vistas temporales auxiliares (no catalogadas):

```bash
duckdb < v2/views.sql
```

La base de los archivos sale de una variable de sesión, así que **el mismo
archivo** sirve para el sitio, para una copia local o para un espejo:

```sql
SET VARIABLE sif_base = 'https://…/Sistema_de_Informacion_Financiera_de_Chile';
CREATE OR REPLACE VIEW "afp_lista_entidades" AS
SELECT * FROM read_parquet(getvariable('sif_base') || '/outputs/pensiones/afp_maestro_administradoras.parquet');
```

Para trabajar contra una copia local, se cambia sólo esa línea
(`SET VARIABLE sif_base = '/ruta/a/docs';`) y todo lo demás funciona igual. Los
4 objetos vacíos **no** crean vista (no hay archivo); quedan listados como
comentario al final, con su motivo.

### `resultados/` · el número, sin bajar los Parquet

La fase 3 pedía SQL remoto. Un servidor DuckDB (Quack) no cabe en este
despliegue: GitHub Pages sirve archivos y no ejecuta procesos, y Actions no
recibe tráfico entrante. Lo que sí cabe se hace en el build: **las 159 consultas
del catálogo se ejecutan** contra los mismos Parquet que publica el sitio y cada
una queda como archivo.

```
v2/resultados/index.json                                   qué hay y cuánto pesa
v2/resultados/cartera-extranjera-por-pais-emisor-…json     columnas, filas, datos, sql
```

Cada resultado lleva `data_release`, el `sql` que lo produjo, `max_filas` (500),
`truncado` y `filas`. La salida se ordena con `ORDER BY ALL` para que el archivo
no cambie cuando el dato no cambia, y `build_resultados.py --check` falla si
quedó atrasado. **No es SQL arbitrario**: es el catálogo publicado, con su SQL a
la vista para poder reproducirlo o discutirlo.

La receta para levantar un servidor Quack propio —con TLS, token y cuotas— está
en [`servidor/README.md`](servidor/README.md). No está desplegada, y el motivo
está escrito ahí: cuesta una máquina y un certificado que hoy nadie pidió.

### `openapi.json`

Once rutas, todas GET y todas reales: los cinco documentos del contrato, el
índice de resultados —y cada resultado—, el CSV de reconciliación, el de claves y
los Parquet del sitio. **No hay `/query` ni SQL arbitrario por HTTP**; si algún
día se añade, será una versión mayor (decisión D3).

## SDK de Python

`sdk/python/` es el paquete `sif-chile`: lee el catálogo publicado, ejecuta el
`views.sql` con la base que se le pida y consulta con DuckDB. No tiene listas
propias: lo que el contrato publica es lo que el cliente conoce.

```bash
pip install -e sdk/python          # o: pip install "sif-chile[pandas] @ git+…@main#subdirectory=sdk/python"
```

```python
import sif_chile

sif = sif_chile.connect()                       # sitio publicado
sif = sif_chile.connect(base="/ruta/a/docs")    # copia local, sin red
sif.tablas()                                    # los 90 objetos
sif.esquema("seguros_renta_fija")               # columnas y tipos reales
sif.sql("SELECT count(*) FROM bancos_balance").fetchone()
```

Detalle y tabla de métodos: `sdk/python/README.md`. Los tests
(`python3 -m unittest discover -s sdk/python/tests -t sdk/python`) no usan red:
corren contra la copia del repo, y `web_audit.yml` los ejecuta en cada push.

## Prueba de máquina limpia

`scripts/probar_maquina_limpia.py` comprueba lo que de verdad importa de un
contrato: que sirva a quien **no tiene el repo**. Levanta el sitio con
`http.server`, y en un **venv aparte**, desde un directorio temporal y sin
`PYTHONPATH`, un cliente descarga el descriptor, lee el esquema de un recurso,
se baja su Parquet y lo consulta. El registro más reciente ejecutó 11 pasos y tuvo 0 fallos. Desde 1.7 también
lee el catálogo del contrato, el esquema por su ruta y ejecuta las 105 vistas de catálogo más las cuatro auxiliares temporales de
`views.sql` contra la copia local.

No reproduce el CDN de GitHub Pages (el sandbox no sale a internet), pero sí el
protocolo, el formato y los archivos que sirve.

## Lo que el test de contrato tolera, y por qué

`scripts/test_contrato.py` falla si el contrato promete algo que no está, pero hay
dos cosas que hoy se toleran **nombrándolas** en el código, no en silencio:

- **Una columna declarada sin un solo valor**: `agf_lista_entidades.codigo_cmf`.
  El registro RGAGF de la CMF no publica código institucional para las AGF, así
  que la columna hereda la plantilla del maestro de entidades y sale vacía. Está
  en `COLUMNAS_VACIAS_CONOCIDAS` con su motivo, el diccionario de la web lo dice
  al abrir la tabla, y el test falla si aparece otra.

Las cuatro columnas de banca que estaban en esa situación (`rut` y
`razon_social` en `bancos_balance` y `bancos_resultados`) **se repararon el
2026-10-22**: un `WHERE rut = '97004000'` devolvía 0 filas sin error y ahora
devuelve 40.123. Ver 1d.8 en la ruta.
- **Cobertura del manifiesto**: los 112 archivos de `bancos_balance` y
  `bancos_resultados` se cubren por `bancos_cmf_lineas`, y los 4 objetos sin
  particiones se admiten porque su estado es `vacio`.

Si aparece otra columna muerta u otra fila huérfana, el test falla: la lista es
cerrada, no una amnistía.

## Alcance del servicio

**Best effort, sin SLA.** Este contrato describe datos públicos que publica un
tercero y que se normalizan y se republican; no hay compromiso de
disponibilidad, latencia ni corrección en un plazo. La API **no** es un servicio
de consulta: no hay `/query`, no hay SQL arbitrario y no hay autenticación. Lo
que hay son archivos Parquet en una URL estable, un descriptor que dice cómo
leerlos y el resultado de las 159 consultas del catálogo ya calculado. Si algo falta, se arregla en el siguiente release, y cada release queda
identificado por su hash.

## Retención

**El hash identifica, no recupera.** Cada edición queda en el historial de git y
el sitio sirve siempre la última versión publicada; no hay archivo histórico
público de Parquet. Un `data_release` permite comprobar que dos descargas son la
misma, no volver a una anterior. Si necesitas una serie congelada, descarga y
guarda el release que estás usando.

## Lo que todavía no es

- No hay **SQL arbitrario por HTTP**: quien necesite una consulta distinta a las
  159 publicadas ejecuta el motor en su máquina (SDK, `views.sql` o DuckDB).
- No hay **servidor DuckDB compartido** (Quack): la receta está en
  [`servidor/README.md`](servidor/README.md), sin desplegar. Implica una máquina,
  un certificado y un costo mensual.
- **Las condiciones de las fuentes directas están documentadas por fuente**
  (`DATA_LICENSE.md`): CMF, BCCh y SPensiones, con las citas publicadas en
  `catalog.json` y `sources[].sif_cita` del Data Package. La procedencia histórica
  SUSESO de `ccaf_maestro` está identificada, pero sus condiciones de reutilización
  no se verificaron en esta revisión; la autorización CMF no resuelve ese punto.
  La MIT es del código, no de los datos.
- La **misma consulta en R y en JavaScript** existe como ejemplo
  (`examples/`), pero sólo Python tiene cliente propio: R y JavaScript usan
  DuckDB directamente.

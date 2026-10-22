# Contrato de la API pública (v1, en construcción)

Lo que hay aquí es el **contrato estático** de la API: cinco archivos generados
desde los datos publicados, versionados junto al código y verificados en cada
CI. No son documentación escrita a mano, así que no pueden desviarse de lo que
el usuario descarga.

| Archivo | Qué responde |
|---|---|
| `reconciliacion.csv` | Qué objeto consume el cliente, con qué datos se sirve y en qué estado está (publicado, derivado o vacío). |
| `esquemas.json` | Qué columnas y qué tipos tiene cada objeto, con el significado del diccionario editorial cuando existe. |
| `claves.csv` | Qué combinación de columnas identifica una fila (verificada sobre **todas** las filas) y qué claves foráneas cierran contra su lista de entidades. |
| `v1/datapackage.json` | El **Data Package**: 86 recursos con ruta, tamaño, SHA-256, esquema y `primaryKey`, legible por cualquier herramienta Frictionless. |
| `reglas.json` | Las comprobaciones con su nivel (invariante / expectativa / informativo) y las excepciones declaradas con su motivo. Hoy: **0 excepciones**. |
| `prueba_maquina_limpia.log` | Evidencia de que un consumidor **sin el repo** descubre el catálogo, lee el esquema y consulta por HTTP. |
| `v1/catalog.json` | El índice de los 90 objetos: estado, filas, bytes, clave, corte y a dónde ir por más detalle. |
| `v1/schema/{id}.json` | Columnas, tipos, significado y clave de cada objeto. |
| `v1/partitions/{id}.json` | Los archivos que componen el objeto, con período y SHA-256. |
| `v1/queries.json` | Las 156 consultas de la web, con **id estable** y la expectativa declarada. |
| `v1/openapi.json` | **Sólo** las 9 rutas GET que existen. |
| `v1/views.sql` | Las 105 vistas SQL (90 objetos + 19 alias), ejecutables tal cual. |

Se regeneran con:

```bash
python3 scripts/build_reconciliacion.py   # docs/api/reconciliacion.csv
python3 scripts/build_esquemas.py         # docs/api/esquemas.json
python3 scripts/verificar_claves.py       # docs/api/claves.csv      (~60 s)
python3 scripts/build_api.py              # docs/api/v1/datapackage.json
python3 scripts/auditar_datapackage.py    # valida el descriptor    (~12 s)
python3 scripts/probar_maquina_limpia.py  # consumidor sin el repo  (~5 s)
python3 scripts/build_contrato.py         # catálogo, esquemas, particiones, consultas, OpenAPI y vistas
python3 scripts/auditar_contrato.py       # audita el contrato     (~1 s)
```

Y el CI falla si quedan desactualizados (`--check` en cada uno) o si algo del
contrato deja de cumplirse.

## `reconciliacion.csv`

Cruza los tres niveles que hasta ahora nadie había cruzado —objeto del
contrato, fila de `data_manifest.json` y dataset físico— porque no son 1:1:
hay objetos que son alias del nombre heredado y un dataset (`bancos_cmf_lineas`)
que se publica como dos objetos.

| Columna | Significado |
|---|---|
| `objeto` | Nombre de la vista que escribe el cliente (`FROM bancos_balance`). |
| `nombre_visible` | Nombre de catálogo que muestra la web. |
| `manifest_id` | Fila de `data_manifest.json` que lo respalda; vacío si no hay dato. |
| `puente` | Cómo se emparejó: `directo`, `alias` (nombre heredado) u `origen_compartido` (un dataset, dos vistas). |
| `nivel` | `nucleo`, `secundario`, `archivo` o `registro`. |
| `estado` | `publicado`, `derivado` (proyección de otro objeto) o `vacio` (sin particiones). |
| `motivo` | Por qué está vacío o de dónde deriva. |
| `deriva_de` | Objeto del que es proyección, si aplica. |
| `particiones`, `filas`, `bytes` | Tamaño real publicado. |
| `corte`, `ultima_actualizacion` | Cobertura temporal y fecha del último dato. |

Estado actual: **90 objetos** = 79 publicados + 7 derivados + 4 vacíos, sobre
las 89 filas del manifiesto. El puente se reparte en 73 directos, 15 alias y 2
de origen compartido.

## `esquemas.json`

```jsonc
{
  "contrato": "sif-api/esquemas",
  "version": "v1",
  "resumen": { "objetos": 90, "con_esquema": 86, "filas_unicas": 19777492, ... },
  "objetos": {
    "bancos_balance": {
      "manifest_id": "bancos_cmf_lineas",
      "nombre_visible": "bancos.cmf_lineas_b1_b2_r1",
      "sector": "bancos",
      "estado": "publicado",
      "particiones": 56,
      "filas": 722931,          // lo que devuelve la vista ya filtrada
      "filas_dataset": 1962992, // filas de los archivos, compartidos con bancos_resultados
      "archivo": "outputs/bancos/cmf_b1_b2_r1/2022-01/lineas.parquet",
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
   `"sin_valores": true`. Hoy son 5 columnas de origen vacío, no un error de
   tipos.
5. **`filas` cuenta lo que ve el cliente.** Cuando dos objetos comparten un
   dataset (`bancos_balance` y `bancos_resultados`), `filas` aplica el filtro
   de la vista y `filas_dataset` deja el total del archivo: 722.931 + 1.240.061
   = 1.962.992, las filas del dataset.
6. **Los 4 objetos sin dato no desaparecen**: se publican con `estado: "vacio"`,
   `columnas: []` y `motivo_sin_esquema`.

Estado actual: 86 objetos con esquema, 1.509 columnas (7 sin documentar en el
diccionario, 5 sin valores en origen), 19.777.492 filas únicas.

## `v1/datapackage.json`

Un recurso por objeto (86), con las particiones en `path` y el detalle en
`sif.particiones`. Los campos salen de `esquemas.json` —no hay ni uno escrito a
mano—, y los tipos se traducen a Table Schema (`VARCHAR` → `string`,
`BIGINT` → `integer`, `DOUBLE` → `number`).

`primaryKey` **sólo aparece cuando está probada** sobre todas las filas: 76 de
86 recursos. Los 10 restantes no la llevan porque la tabla publica filas
idénticas (9) o porque la fila entera es la única garantía (1). Prometer una
clave falsa es peor que no tener ninguna; las 8 que la tenían mal se
corrigieron en la tarea 1a.9.

El `hash` de cada recurso es el SHA-256 de la concatenación de los SHA-256 de
sus particiones, y el conjunto de todos ellos produce el `data_release`
(`2026-10-21.dd49f53bf82b`): no es una fecha elegida a mano, es el contenido.

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

- **PK**: 48 claves declaradas se verifican tal cual; 28 se proponen porque el
  diccionario no las traía y la búsqueda encontró una combinación única; 1 sólo
  se sostiene con la fila completa; 9 tablas publican filas idénticas y no
  pueden tener clave. **Ninguna clave declarada es falsa.**
- **FK**: 36 relaciones cierran; 1 tiene huérfanas (patrimonios separados
  45,3 %); 6 no tienen destino porque el sector no publica lista de entidades
  con esa columna.

### Lo que encontró la verificación (tarea 1a.9)

Las 8 claves declaradas que no eran únicas tenían el mismo vicio: **la clave
natural omitía una dimensión**.

| Objeto | Declaraba | Clave real | Qué faltaba |
|---|---|---|---|
| `corredoras_bolsa_balance` / `_resultados` | `codigo_fecu` | `periodo + rut + codigo_fecu` | el periodo y la entidad |
| `ffmm_balance` / `_resultados` | `orden + codigo_cuenta` | `periodo + run_fondo + codigo_cuenta` | el periodo y el fondo |
| `fi_balance` / `_resultados` | `periodo + contexto + codigo_cuenta` | `+ run_fondo` | el fondo de inversión |
| `patrimonios_separados_balance` | `archivo` | `periodo + codigo_patrimonio + cuenta + archivo + orden_en_balance` | todo menos el archivo |
| `seguros_lista_entidades` | `rut_aseguradora` | `sector + rut_aseguradora` | el sector |

El caso de seguros no era un dato sucio: la misma aseguradora tiene registro de
**vida** y de **generales**, así que `sector + rut` da 84 de 84.

## El contrato estático (`v1/`)

`catalog.json` es la puerta de entrada: 90 objetos con `estado`, `filas`,
`bytes`, `primaryKey` y las rutas a su esquema y sus particiones. Los 156
`queries.json` traen **id estable** (`titulo-slug` + 6 hex del SQL): un id no
cambia mientras el SQL no cambie, así que sirve para citar una consulta en un
artículo o en una prueba.

### `views.sql`

Se ejecuta tal cual y crea las 105 vistas:

```bash
duckdb < v1/views.sql
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

### `openapi.json`

Nueve rutas, todas GET y todas reales: los cinco documentos del contrato, el CSV
de reconciliación, el de claves y los Parquet del sitio. **No hay `/query` ni
JSON por fila**; si algún día se añade, será una versión mayor (decisión D3).

## Prueba de máquina limpia

`scripts/probar_maquina_limpia.py` comprueba lo que de verdad importa de un
contrato: que sirva a quien **no tiene el repo**. Levanta el sitio con
`http.server`, y en un **venv aparte**, desde un directorio temporal y sin
`PYTHONPATH`, un cliente descarga el descriptor, lee el esquema de un recurso,
se baja su Parquet y lo consulta. 8 pasos, 0 fallos, ~5 s.

No reproduce el CDN de GitHub Pages (el sandbox no sale a internet), pero sí el
protocolo, el formato y los archivos que sirve.

## Alcance del servicio

**Best effort, sin SLA.** Este contrato describe datos públicos que publica un
tercero y que se normalizan y se republican; no hay compromiso de
disponibilidad, latencia ni corrección en un plazo. La API **no** es un servicio
de consulta: no hay `/query`, no hay JSON por fila y no hay autenticación. Lo
que hay son archivos Parquet en una URL estable y un descriptor que dice cómo
leerlos. Si algo falta, se arregla en el siguiente release, y cada release queda
identificado por su hash.

## Retención

**El hash identifica, no recupera.** Cada edición queda en el historial de git y
el sitio sirve siempre la última versión publicada; no hay archivo histórico
público de Parquet. Un `data_release` permite comprobar que dos descargas son la
misma, no volver a una anterior. Si necesitas una serie congelada, descarga y
guarda el release que estás usando.

## Lo que todavía no es

- No hay **URL canónica** decidida (tarea 0.1 de la ruta): los archivos viven
  en el repo y en el sitio, pero la API aún no anuncia una dirección estable.
- No hay **OpenAPI**, **SDK** ni **ejemplos** (fases 1 a 1d). Este contrato es
  la materia prima de esos pasos: sin tipos reales no hay cliente que valga.
- **No hay una licencia de datos verificada** (`DATA_LICENSE.md`): los 86
  recursos declaran `pendiente`, no MIT. La MIT es del código.
- **D2 sin cerrar**: el identificador es el nombre del objeto del contrato, pero
  la decisión formal sigue pendiente (ver `docs/notas/decisiones_api_v1_2026-10-22.md`).

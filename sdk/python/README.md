# `sif-chile` · SDK de Python

Cliente mínimo sobre el **contrato estático** del Sistema de Información
Financiera de Chile. No hay servidor: el SDK lee el catálogo publicado
(`docs/api/v1/`) y ejecuta SQL con DuckDB directamente sobre los Parquet,
sean del sitio o de una copia local.

```bash
pip install -e sdk/python                 # desde el repo
pip install "sif-chile[pandas] @ git+https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile@main#subdirectory=sdk/python"
```

## Tres líneas

```python
import sif_chile

sif = sif_chile.connect()                      # contra el sitio publicado
sif.tablas()                                   # los 90 objetos del contrato
sif.esquema("seguros_renta_fija")              # columnas, tipos, clave
sif.sql("SELECT count(*) FROM bancos_balance").fetchone()
```

## Qué sabe el SDK

Todo lo que sabe lo lee del contrato, no de una lista escrita a mano: si el
contrato gana un objeto, el SDK lo gana sin actualizar el paquete. Las vistas
se crean ejecutando el `views.sql` publicado, con la base que use el cliente.

| método | devuelve |
| --- | --- |
| `tablas(sector=None, estado=None)` | los objetos del catálogo |
| `sectores()` | cuántos objetos por sector |
| `buscar(texto)` | objetos que coinciden en id, título, descripción, sector o alias |
| `tabla(nombre)` | una entrada del catálogo; acepta alias heredados |
| `esquema(nombre)` | columnas, tipos, clave primaria y foráneas |
| `particiones(nombre)` | archivos, filas, bytes y SHA-256 |
| `consultas()` · `consulta(id)` | las 156 consultas publicadas, con id estable |
| `read_table(nombre, limite=None)` | DataFrame (o tabla de Arrow) |
| `sql(consulta, limite=None)` | resultado de DuckDB de una consulta de lectura |
| `descargar(nombre, destino=None)` | los Parquet del objeto, con hash verificado |

`sif.consultas()` es lo que usa la web: cada consulta tiene un id estable
(`slug` + 6 hex del SHA-1 de su SQL), así que un enlace o un ejemplo puede
citarla sin copiar el SQL.

## Servidor MCP (para agentes)

Si el agente **no puede ejecutar código** —Claude Desktop, un asistente con
`function calling`—, el mismo cliente se expone como servidor MCP:

```bash
pip install "sif-chile[mcp] @ git+https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile@main#subdirectory=sdk/python"
sif-mcp                     # servidor por stdio
```

```json
{"mcpServers": {"sif-chile": {"command": "sif-mcp",
                              "env": {"SIF_CHILE_BASE": "/ruta/a/docs"}}}}
```

Dos herramientas, no noventa: `sif_buscar` (descubre tabla y columnas con
lenguaje natural) y `sif_ejecutar` (SQL de solo lectura). Las herramientas que ve
el modelo ocupan **191 tokens**; el MCP de la CMF revisado en el estudio expone
88 y cuesta ~37.000. Lo vigila `scripts/auditar_mcp.py`, que además levanta el
servidor como lo haría un agente y responde la pregunta del README:

```
OK 2.1 herramientas · 2 herramientas: ['sif_buscar', 'sif_ejecutar']
OK 2.2 presupuesto · 191 tokens de 1000 permitidos (764 caracteres)
OK 2.3 descubrir · «dónde invierten fuera de Chile los fondos mutuos» → ['ffmm_cartera_extranjera', …]
OK 2.3 responder · 5 filas; en cabeza ['US', 'LU', 'IE', 'BR', 'GB']
OK 2.3 error útil · error con pista: Esa tabla o columna no existe…
OK 2.3 solo lectura · el guardia rechaza DROP y responde con JSON
```

Las respuestas de las herramientas son JSON compacto y recortado (200 filas como
máximo, 160 caracteres por celda) porque el recurso escaso es el contexto del
modelo. Los errores vuelven como `{"error": …, "pista": …}`: un agente que recibe
una excepción suele repetirla, uno que recibe una pista la corrige.

## Trabajar contra una copia local

Útil para probar cambios del contrato sin publicar, o sin red:

```python
sif = sif_chile.connect(base="/ruta/al/repo/docs")
```

o bien `export SIF_CHILE_BASE=/ruta/al/repo/docs`. Si `base` es una carpeta, el
SDK no hace ninguna petición HTTP.

## Caché

`connect(cache="~/.cache/sif-chile")` guarda los documentos del contrato y, si
se llama a `descargar()` sin destino, los Parquet en ese mismo caché. Un archivo
que ya está y cuyo SHA-256 coincide con el del contrato no se vuelve a bajar.

## El guardia de SQL

`sif.sql()` acepta solo lectura (`SELECT`, `WITH`, `DESCRIBE`, `SUMMARIZE`…),
una sentencia por vez, y rechaza escrituras sueltas como `SELECT … INTO`.
El mismo criterio aplica la consola de la web (`docs/js/sql_guard.js`).

**Es una conveniencia, no una frontera de seguridad**: protege de una consulta
ajena que altere tu propia sesión, no de alguien que importe DuckDB por su
cuenta. La frontera real es que los archivos publicados son de solo lectura.

## Tests

No usan red: corren contra la copia del repo.

```bash
python3 -m unittest discover -s sdk/python/tests -t sdk/python
```

## Licencia

MIT, la misma del repositorio.

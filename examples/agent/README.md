# Un agente, con dos llamadas en vez de noventa

Un agente que descubre herramientas leyendo un catálogo paga cada herramienta en
contexto. Noventa tablas como noventa herramientas son decenas de miles de
tokens antes de la primera pregunta. Aquí no hay herramientas: hay **tres
documentos** y SQL.

| Paso | Qué pide | Para qué |
|---|---|---|
| 1 | [`llms.txt`](../../docs/llms.txt) | ~800 palabras: qué hay, dónde está, cómo se consulta y qué no se debe suponer |
| 2 | [`api/v1/catalog.json`](../../docs/api/v1/catalog.json) | los 90 objetos, con estado, filas, clave primaria y rutas |
| 3 | [`api/v1/queries.json`](../../docs/api/v1/queries.json) | 156 consultas de ejemplo con id estable: el agente puede citar una en vez de inventarla |

```text
usuario  ¿Dónde invierten fuera de Chile los fondos mutuos?
agente   GET llms.txt                     → «views.sql + catalog.json»
agente   GET catalog.json                 → busca "extranjera" → ffmm_cartera_extranjera
agente   GET schema/ffmm_cartera_extranjera.json → columnas reales
agente   ejecuta views.sql en DuckDB y consulta por periodo
```

El agente nunca ve las 90 tablas: ve una búsqueda y un esquema. El `id` estable
de las consultas es lo que evita que invente SQL: encuentra la consulta que ya
resuelve su pregunta, o al menos la usa de plantilla.

## Por qué `llms.txt` y no un `openapi.json` más grande

`openapi.json` describe **archivos HTTP**, y un agente no necesita eso para
consultar: necesita saber que hay un `views.sql` y qué columnas tiene cada
objeto. `llms.txt` dice eso en el formato que los agentes ya leen
(`owid/etl`, `llms.txt` de cada proyecto), sin obligarlos a interpretar un JSON
Schema de 300 KB.

## Lo que un agente no debe hacer

- **No supone el último período.** `max(periodo)` es una consulta, no un dato
  del catálogo. El campo `corte` dice el rango, no el máximo garantizado.
- **No descarga los 90 objetos.** 517 MB. Se filtra por `sector` en el catálogo y
  se consultan las vistas: DuckDB pide solo los grupos de fila que necesita.
- **No cita cifras sin `data_release`.** El release identifica la edición; sin él
  una cifra no es reproducible.

## Si el agente no puede ejecutar código

Todo lo anterior supone un agente que corre Python. Cuando no puede —Claude
Desktop, un asistente con `function calling`—, el mismo contenido se sirve como
**servidor MCP en modo código**:

```bash
pip install "sif-chile[mcp]" && sif-mcp
```

Dos herramientas (`sif_buscar`, `sif_ejecutar`) que cuestan **191 tokens** de
contexto; el MCP de la CMF revisado en el estudio expone 88 y cuesta ~37.000.
La compuerta `scripts/auditar_mcp.py` levanta el servidor como lo haría un agente
y responde, con dos llamadas, la pregunta de este mismo documento. Detalle en
[`../../sdk/python/README.md`](../../sdk/python/README.md).

## Prueba de extremo a extremo

La ruta deja para la fase 2 (opcional) un MCP en modo código con dos
herramientas (`sif_buscar`, `sif_ejecutar`). Mientras tanto, lo de arriba se
puede reproducir a mano, y los ejemplos de Python son exactamente esos pasos:
[`../python/01_ffmm_extranjero.py`](../python/01_ffmm_extranjero.py) hace la
pregunta de arriba de principio a fin.

# Claves primarias: el defecto del 2026-10-23 y su corrección

**Fecha:** 2026-10-23
**Alcance:** `scripts/verificar_claves.py`, `docs/api/claves.csv` y el contrato `docs/api/v2/`.
**Estado:** corregido en la versión 2.0.1 del contrato (hoy el contrato va en 2.1.0,
que sólo añade `totales.con_filas`); publicado en 2.0.0 hasta el
despliegue.

---

## 1. Qué se afirmaba y qué había

`docs/api/claves.csv` declaraba clave primaria única para 76 objetos del
catálogo, y `catalog.json` publicaba la misma afirmación en `primaryKey`. Trece
de esas claves no eran únicas: los objetos **publicaban filas idénticas entre sí**
y la clave no distinguía una fila de otra.

El caso mayor es `ffmm_cartera_nacional`:

| Medición | Valor |
|---|---|
| Filas publicadas | 1.590.196 |
| Filas distintas (`SELECT DISTINCT *`) | 1.429.632 |
| Filas repetidas | **160.564 (10,1 %)** |
| Grupo mayor de filas idénticas | 33 copias |
| Sobrestimación al sumar `valorizacion_miles_mf` en 2026-04 | **9,94 %** (77.518.922.784 → 70.512.537.130) |
| Sobrestimación en 2026-09 | **9,71 %** (82.192.969.139 → 74.916.218.817) |

`fi_cartera_nacional` ya se declaraba `sin_clave` y estaba bien: 11.033
sobrantes. El defecto no era de los datos, era de la verificación.

## 2. La causa

`scripts/verificar_claves.py` marcaba las filas repetidas con

```sql
WHERE (a, b, c) IN (SELECT a, b, c FROM t GROUP BY a, b, c HAVING count(*) > 1)
```

En DuckDB esa tupla **no** se compara fila a fila: se evalúa como un valor
compuesto, y si alguna de las columnas es `NULL` el conjunto sale vacío. El
vacío se interpretaba como «no hay duplicados» y la clave se daba por buena.
`ffmm_cartera_nacional` incluye en su clave propuesta columnas que llegan nulas
(`fecha_vencimiento`, `tir_pct`), de modo que el caso que debía detectar era
justamente el que no detectaba.

Había un segundo defecto que impedía notarlo: el informe copiaba `filas` en la
columna `distintas`, así que el CSV **no podía** contradecirse a sí mismo.

## 3. La corrección

1. Las repeticiones se marcan con `count(*) OVER (PARTITION BY …)`, que agrupa
   igual que `DISTINCT`, y la respuesta se vuelve a medir contra la vista
   completa antes de declarar una clave única.
2. `distintas` se mide con `SELECT DISTINCT`, no se copia.
3. Un objeto sin filas se informa como `sin_datos`, no como una clave que ganó
   por no tener con quién chocar.
4. El contrato publica `primaryKey: null` —no `[]`— cuando no hay clave única
   medida. Son 27 objetos en la 2.0.1: los 13 falsos más los 14 que ya no la
   tenían. El `[]` se lee como «clave de cero columnas» y es una afirmación
   distinta de «no hay clave».

Tras la corrección: **86 objetos con datos · 48 claves verificadas · 15
propuestas · 22 sin clave · 1 sin datos**, con 230.288 filas repetidas medidas
en todo el catálogo.

## 4. Cómo se comprueba que no vuelva

La prueba de mutación (reponer la consulta rota y mostrar que la suite se pone
en rojo) es parte del arreglo, no una formalidad. Con la redacción anterior,
reponer el defecto dejaba **5 de 6 pruebas en verde**: cubrían el caso escrito a
mano, no el comportamiento.

Las pruebas que ahora lo impiden, en `pipelines/auto/tests/test_claves.py`:

- treinta tablas generadas al azar, con repetición y `NULL`, contrastadas contra
  `SELECT DISTINCT` (una medición independiente del módulo);
- el `NULL` en la primera, la segunda y la tercera columna de la clave;
- que todo objeto del catálogo con filas tenga una clave medida en `claves.csv`;
- que el informe cuadre consigo mismo (`filas − distintas = sobrantes`).

Con la mutación repuesta, **4 de 9 pruebas fallan**. En el SDK, la ficha de un
objeto sin clave llega con `"pk": null`, y el servidor MCP se audita con la misma
comprobación (`scripts/auditar_mcp.py`, punto 2.4).

## 5. Qué no cambia

No se tocaron filas ni columnas: las 0 columnas descartadas entre TXT y Parquet
y el hecho de que no hay ningún join después de la lectura siguen siendo válidos,
porque el arreglo vive en la verificación y en el contrato, no en los datos.

El Diccionario del sitio muestra ahora, por objeto, el estado derivado de
`claves.csv` en el build (`docs/js/estado_claves.js`, generado por
`scripts/build_estado_claves.py`): el número de filas idénticas, el porcentaje y
la sobreestimación medida en su último período. El visor repite el aviso al
abrir una tabla con duplicados. Ninguno de esos textos se escribe a mano.

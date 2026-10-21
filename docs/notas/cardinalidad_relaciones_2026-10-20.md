# Cardinalidad de las uniones del mapa relacional (punto 10)

Fecha: 2026-10-20.

## Qué había antes

El mapa relacional (`docs/js/erd_graph.js`, `ERD_LINKS`) mostraba cada unión con su clave, pero no decía si era uno a uno. Quien uniera un maestro con su tabla de balance o de cartera podía duplicar filas sin darse cuenta.

## Qué se hizo

- **`scripts/medir_cardinalidad_relaciones.py`**: lee `ERD_LINKS` y las rutas de `ERD_TABLES` directamente de `erd_graph.js` (una sola fuente), cuenta claves distintas en cada lado y clasifica cada unión. Escribe `docs/outputs/cardinalidad_relaciones.json`. Trabaja con claves distintas (no copia filas), para caber en memoria con tablas de más de dos millones de filas.
- **`docs/js/erd_graph.js`**: carga ese JSON y, en el mapa, marca con una etiqueta cada unión que no es 1:1 (amarilla si se repite, roja si no tiene coincidencias). La leyenda dentro del canvas explica la notación.

## Resultados (40 uniones)

| Cardinalidad | Uniones | Qué significa |
|---|---|---|
| 1:1 | 4 | La clave identifica una fila en ambos lados. Ejemplo: `macro_dolar_observado` → `macro_euro_observado` por fecha. |
| 1:N | 34 | Un registro del maestro tiene varios en la tabla de datos (balances, cartera, cuentas, o un mes por fila). Es la estructura esperada, no un error. |
| N:1 | 1 | `macro_tasas_corto_plazo` (diaria) → `macro_expectativas_tpm` (mensual) por `periodo`: varias filas diarias por cada mes. |
| sin coincidencias | 0 | — |
| no medido | 1 | `agf_lista_entidades` → `fi_lista_entidades`, clave en texto libre («rut_administradora (gestión fiduciaria LUF)»). No se adivina la columna. |

Las 4 uniones 1:1 son las de macro por fecha o periodo, con una coincidencia de claves entre 99,35 % y 100 % (`macro_inflacion_ipc` → `macro_expectativas_inflacion` tiene 0,65 % de periodos sin par).

## Cómo leer las advertencias

- **1:N en maestro → balance o cartera** (por ejemplo `ffmm_lista_entidades` → `ffmm_cartera_nacional`): un fondo o una entidad aparece en muchas filas. Para una foto de un período hay que filtrar por `periodo` antes de unir, y para totales hay que agregar antes de unir. Si no se hace, los importes se multiplican.
- **N:1 en macro**: una tasa diaria y una expectativa mensual. Para comparar, primero hay que llevar la serie diaria a mensual.

## Límites de la medición

- Se mide sobre la tabla completa, no por período. Es posible que una unión 1:N sea 1:1 dentro de un solo período, pero eso no se midió; el mapa advierte sobre la tabla completa, que es lo que la persona une si no filtra.
- Solo se miden las claves que son columnas reales. Las descritas en texto libre quedan como «no medido».
- La cardinalidad se midió con los archivos publicados en el repositorio (`docs/outputs`) en la fecha de la nota. Si la publicación cambia, hay que volver a correr el script.
- Verificación: la prueba en jsdom con un canvas de prueba dibuja 34 etiquetas 1:N y 1 etiqueta N:1, y no dibuja las uniones 1:1 ni la no medida. No se probó en un navegador real.

## Uso

```
python scripts/medir_cardinalidad_relaciones.py
```

Tarda unos dos minutos. Vuelve a escribir `docs/outputs/cardinalidad_relaciones.json`.

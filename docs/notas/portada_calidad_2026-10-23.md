# La portada muestra lo que el proyecto mide

**Fecha:** 2026-10-23
**Motivo:** una revisión externa del sitio desplegado dijo que la capa técnica ya
aguanta la auditoría, pero que la primera pantalla no lo muestra. Se contrastó
cada afirmación contra el repositorio y los datos antes de tocar nada.
**Método:** leer el catálogo publicado, `claves.csv` y `estado_claves.js`;
reproducir la medición de duplicados con DuckDB sobre los Parquet; y comprobar
cada cifra citada, incluidas las que la revisión daba por ausentes.

---

> **Snapshot histórico (2026-10-23).** Las cifras de esta nota describen el corte auditado ese día, incluida la cantidad de notas indexadas entonces; no son métricas actuales del release 2026-10-24. El README ya evita fijar ese conteo manual.

## 1. Qué dijo la revisión, y qué resultó ser cierto

| Afirmación | Verificación |
|---|---|
| `ffmm_cartera_nacional`: 1.590.196 filas, 1.429.632 distintas, 160.564 sobrantes | **cierta**, tal cual está en `docs/api/claves.csv` |
| El aviso del Diccionario lleva la cifra, el porcentaje y el ejemplo del período | **cierta**: «publica 160.564 filas idénticas (10,1 % de 1.590.196)… sobreestima 9,7 %» |
| 22 objetos con filas repetidas y 230.288 filas repetidas en total | **cierta**, es `resumen` de `estado_claves.js` |
| La nota `claves_duplicados` dice «corregido en 2.0.1» y el contrato va en 2.1.0 | **cierta**: la nota se actualizó para decir que 2.1.0 sólo añade `totales.con_filas` |
| `con_filas` no aparece en ningún artefacto servido | **falsa**: está en `docs/api/v2/catalog.json` (`"con_filas": 85`, junto a `"con_datos": 86`) y en la tabla del README del contrato. No está —ni tiene por qué— en `alcance.js`, que es código, ni en `data_bundles.js`, que son datos de entidades |
| El `og:description` dice 19 millones y la portada 17 | **cierta como ambigüedad**: son dos universos distintos (catálogo completo frente al núcleo). La cifra del núcleo ahora se rotula «de filas del núcleo» |
| `canonical` apunta a Pages y el enlace que circula es el de Vercel | **cierta y deliberada**: es la decisión D1 —dos URLs, Pages como canónica y Vercel redirigiendo `/api/*`— |

Reproducción de la medición con DuckDB (la misma consulta que ahora publica la
portada):

```sql
WITH crudo AS (SELECT * FROM ffmm_cartera_nacional WHERE periodo = '2026-09'),
     mes   AS (SELECT DISTINCT * FROM crudo)
SELECT (SELECT count(*) FROM crudo) AS filas,
       (SELECT count(*) FROM mes)   AS distintas,
       (SELECT sum(valorizacion_miles_mf) FROM crudo) AS con_repetidas,
       (SELECT sum(valorizacion_miles_mf) FROM mes)   AS sin_repetidas;
-- 29.366 · 26.382 · 82.192.969.139 · 74.916.218.817 → 2.984 repetidas, 9,7 % de sobreestimación
```

## 2. Lo que se construyó

**Bloque «Calidad del dato» en la portada** (`docs/js/calidad_datos.js`): las
cifras salen de `estado_claves.js`, que se genera desde `claves.csv`, y no se
escriben a mano. Muestra las 230.288 filas repetidas, los 22 objetos afectados,
el peor caso con su nombre y su porcentaje, y la sobreestimación medida del
ejemplo. Incluye el gráfico de los seis objetos con más filas idénticas y la
consulta citada, con un botón que la carga en la terminal SQL.

En la primera pantalla se añadió una etiqueta con la cifra que salta al bloque:
la portada ya dice, sin desplazarse, que el dato tiene un problema medido.

**Índice de notas** (`docs/notas/README.md`, generado por
`scripts/build_indice_notas.py`): las 61 notas agrupadas por mes, con título y
resumen, para que las decisiones y las concesiones se puedan citar. `--check`
falla si el índice no coincide con la carpeta, y corre en CI.

**Respaldos sin JavaScript con guarda**: las cifras del bloque están también en
el HTML; `scripts/audit_cifras.js` comprueba que coincidan con `claves.csv`
(mutación probada: con 230.000 en el HTML, falla y dice la cifra real).

## 3. Lo que sigue sin tocarse

- **Portada como escaparate**: el bloque nuevo es una pieza, no un rediseño. La
  fila del héroe, las siete pestañas y los seis botones siguen igual.
- **Móvil**: se mantiene el aviso de «mejor en un computador», que es una
  decisión anterior y no se revierte por una revisión.
- **Dominio**: `canonical` seguirá apuntando a Pages mientras no haya dominio
  propio; es la decisión D1 y no la cambia una nota.

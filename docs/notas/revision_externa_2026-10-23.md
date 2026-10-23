# Revisión externa del 2026-10-23: qué aguanta y qué no

**Fecha:** 2026-10-23
**Motivo:** una revisión externa del sitio afirmó que `ffmm_cartera_nacional` publica
~10 % de filas duplicadas y que `claves.csv` declara una clave única que no lo es.
**Método:** cada afirmación se contrastó contra los Parquet publicados con DuckDB
(no contra la documentación), y contra el código que genera cada artefacto.

---

## 1. Veredicto por afirmación

| Afirmación | Resultado | Evidencia |
|---|---|---|
| `ffmm_cartera_nacional` tiene filas duplicadas exactas, todos los meses | **cierta** | 2026-04: 29.012 filas, 2.917 sobrantes; 2026-09: 29.366 y 2.984. En toda la serie: **1.590.196 filas, 1.429.632 distintas → 160.564 repetidas (10,1 %)** |
| `claves.csv` declara para esa tabla una clave única que no se cumple | **cierta** | el informe decía `distintas=1590196, sobrantes=0`; la medición real sobre la clave propuesta da 1.428.136 distintas |
| `fi_cartera_nacional` sí está declarada como `sin_clave` | **cierta** | `estado=sin_clave`, 11.033 sobrantes; confirmado |
| «Es un problema de normalización: se perdió una dimensión» | **no demostrada, y los datos apuntan a lo contrario** | ver §2 |
| 14 de 90 objetos sin clave primaria | **cierta** | 14 en el catálogo publicado; ahora son 27, porque 13 de las declaradas eran falsas |
| Varias «PK» son 12-15 columnas de medidas (`seguros_renta_fija`) | **cierta** | la clave propuesta son `costo_amortizado_clp`, `valor_razonable_clp`, `deterioro_clp`… Es única, pero no identifica una posición: se rompe cuando la fuente corrige una cifra |
| Faltan `meta description`, `og:`, `twitter:` y `canonical` | **cierta** | `docs/index.html` sólo tiene `charset` y `viewport` |
| `robots.txt` y `sitemap.xml` dan 404 | **cierta** | no existen en `docs/` ni en la raíz |
| `llms.txt` y `views.sql` llevan la base absoluta incrustada | **cierta, con matices** | 9 apariciones en `llms.txt`; `views.sql` la publica en una sola línea `SET VARIABLE sif_base`, documentada como el punto que se cambia para usar una copia local |
| El canal de derechos es un issue público | **cierta** | `docs/privacidad.html`, paso 1: «Abrir un issue en el repositorio» |
| Los dos hosts declaran el mismo `data_release` | **no verificable desde aquí** | el sitio respondía a esta sesión con `2026-10-22.9c002673eed5`; el valor citado (`2026-10-22.5027fd71…`) no coincide con ninguno de los releases generados en el repositorio |
| «Demasiados totales distintos» (90 objetos, 105 vistas, 159 consultas, 86 recursos, 74 conjuntos…) | **cierta como observación editorial** | cada cifra es correcta y derivable, pero el sitio no tiene un párrafo único que diga cómo se cuenta |

## 2. Los duplicados no son un defecto del pipeline

La hipótesis de la revisión era que la normalización perdió una columna. No es así:

- `ffmm/scripts/actualizar_carteras.py::leer()` produce **una fila por línea** del TXT de la
  CMF, sin deduplicar, y exige que el encabezado coincida **exactamente** con la lista de
  campos de la Circular 1333. Si la fuente trajera una columna más, el extractor fallaría
  en vez de ignorarla.
- El manifiesto guarda, por periodo, cuántas filas se escribieron y cuántas líneas se
  descartaron: 2026-09 → `registros: 29366`, `avisos: 0`. Es decir, el archivo de la CMF
  tiene 29.366 líneas de datos y se publicaron 29.366 filas. **Las repeticiones vienen de
  la fuente.**
- Las repeticiones se concentran en renta fija (`BB` 519 grupos, `BE` 212, `BTU` 209,
  `BTP` 204, `DPC` 200 en 2026-04) y todas tienen nemotécnico y RUT: no son filas vacías
  ni de relleno.

Conclusión: **el dato está bien copiado; lo que estaba mal era la afirmación de que una
combinación de columnas identifica una fila**. Eso sí es un defecto nuestro, y grave:
quien leyera `primaryKey` para deduplicar habría creído que no había nada que deduplicar,
y cualquier `SUM(valorizacion_miles_mf)` cuenta esas líneas dos veces.

## 3. La causa: una comparación de tuplas que DuckDB no evalúa fila a fila

`scripts/verificar_claves.py` buscaba las filas repetidas con

```sql
WHERE (a, b, c) IN (SELECT a, b, c FROM t GROUP BY a, b, c HAVING count(*) > 1)
```

En DuckDB esa tupla se lee como un valor compuesto: no es un `EXISTS` fila a fila.
Con un **NULL** en cualquiera de las columnas devuelve el conjunto vacío:

```
filas en grupos repetidos con IN y NULL: 0
con ventana:                             2
```

El vacío se interpretaba como «no hay duplicados» y la clave se daba por buena. La clave
propuesta de `ffmm_cartera_nacional` incluía `fecha_vencimiento` y `tir_pct`, que llegan
nulas, así que cayó siempre en ese caso.

Segundo defecto, que ocultaba el primero: al publicar una clave propuesta, el informe
escribía `distintas = filas` en vez de la medición. Aunque la clave fuera falsa, el CSV
no podía contradecirse.

## 4. Qué se corrigió

- `buscar_clave()` marca las repeticiones con una **función de ventana**
  (`count(*) OVER (PARTITION BY …)`) y **vuelve a medir** cada clave contra la vista
  completa antes de darla por buena.
- El CSV publica la medición, no el total.
- Un objeto **sin filas** ya no recibe clave: cualquier columna es «única» sobre el vacío
  (le pasaba a `fi_bienes_raices`, que publicaba `primaryKey: ["periodo"]` con 0 filas).
- Regresión cubierta en `pipelines/auto/tests/test_claves.py` (6 pruebas, incluida la del
  NULL, que con el código anterior devolvía `(['a','b'], True)`).

**Efecto en el contrato** (2.0.1): 14 afirmaciones retiradas —13 claves que no eran únicas
y 1 clave sobre una tabla vacía—. Objetos sin `primaryKey`: de 14 a **27**. Recursos del
Data Package con clave: de 76 a **63**. Objetos declarados «sin clave» en `claves.csv`:
de 9 a **22**. No cambia ni una fila ni una columna publicada.

## 5. Lo que queda, y por qué no se tocó aquí

1. **Estado de la clave en el Diccionario**, con el número de filas repetidas por tabla
   («publica 160.564 filas idénticas: no sumes sin agrupar»). Es la parte útil de la
   crítica: el dato hoy está en `claves.csv`, que casi nadie lee.
2. **Claves de medidas.** `seguros_renta_fija` y otras cinco publican claves compuestas
   sólo por importes. Son únicas y por eso se publican, pero no identifican una posición.
   Requiere una decisión de vocabulario (¿una clave así se llama clave?).
3. **Vitrina social**: `meta description`, `og:`, `twitter:`, `canonical`, `robots.txt`,
   `sitemap.xml`.
4. **Hosts y base absoluta**: hoy `llms.txt` y `views.sql` apuntan a Pages y el espejo de
   Vercel redirige. Un dominio propio con `canonical` resolvería ambos.
5. **Canal de derechos**: hoy es un issue público. Es una decisión legal del responsable,
   no técnica.
6. **Párrafo único de conteo** para que 90/86/105/159/74 dejen de parecer contradictorios.

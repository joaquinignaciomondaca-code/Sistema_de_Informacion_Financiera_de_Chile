# La repetición no es ocasional: se midió período por período

**Fecha:** 2026-10-23
**Motivo:** una revisión externa señaló que el titular de la portada decía
«La fuente repite filas en algunos meses». La frase describía mal el hallazgo
en el objeto que lo sostiene: en `ffmm_cartera_nacional` la repetición aparece
en **los 57 períodos publicados**, no en algunos.
**Método:** contar, para cada objeto con filas repetidas y cada una de sus
particiones, las filas publicadas y las filas distintas, con DuckDB sobre los
Parquet publicados (`read_parquet(..., union_by_name=true)`).

---

## 1. Lo que se midió

Los 22 objetos con filas repetidas, ordenados por volumen. «Períodos» es el
número de particiones publicadas; «con repetidas», en cuántas hay al menos una
fila idéntica a otra.

| Objeto | Filas repetidas | Períodos | Con repetidas | Mínimo por período | Máximo |
|---|---:|---:|---:|---:|---:|
| `ffmm_cartera_nacional` | 160.564 | 57 | 57 | 2.127 | 3.335 |
| `ffmm_cartera_extranjera` | 15.410 | 309 | 309 | 5 | 280 |
| `ffmm_futuros` | 13.938 | 309 | 245 | 0 | 259 |
| `seguros_derivados_relevantes` | 11.929 | 119 | 97 | 0 | 159 |
| `fi_cartera_nacional` | 11.033 | 26 | 26 | 200 | 671 |
| `seguros_extranjeros_relevantes` | 7.402 | 119 | 119 | 35 | 426 |
| `seguros_tablas_desarrollo` | 7.044 | 22 | 1 | 0 | 7.044 |
| `fi_cartera_extranjera` | 806 | 26 | 21 | 0 | 65 |
| `seguros_derivados` | 771 | 119 | 6 | 0 | 149 |
| `seguros_extranjeros` | 613 | 119 | 17 | 0 | 341 |
| `seguros_otras_inversiones` | 276 | 22 | 1 | 0 | 276 |
| `seguros_bienes_raices_relevantes` | 138 | 22 | 14 | 0 | 27 |
| `seguros_bienes_raices` | 136 | 22 | 14 | 0 | 27 |
| `seguros_pactos` | 92 | 119 | 6 | 0 | 31 |
| `ffmm_opciones` | 74 | 292 | 30 | 0 | 8 |
| `seguros_control_inversiones` | 24 | 119 | 6 | 0 | 5 |
| `fi_pactos` | 12 | 55 | 5 | 0 | 6 |
| `fi_futuros` | 9 | 26 | 2 | 0 | 7 |
| `seguros_fondos_mutuos` | 6 | 119 | 6 | 0 | 1 |
| `seguros_acciones` | 4 | 119 | 4 | 0 | 1 |
| `seguros_acciones_relevantes` | 4 | 119 | 4 | 0 | 1 |
| `seguros_garantias_derivados` | 3 | 22 | 3 | 0 | 1 |

Sólo cuatro objetos repiten en **todos** sus períodos
(`ffmm_cartera_nacional`, `ffmm_cartera_extranjera`, `fi_cartera_nacional` y
`seguros_extranjeros_relevantes`). En los otros 18 la repetición es
intermitente: `seguros_tablas_desarrollo` la tiene en 1 de 22 períodos y
`seguros_acciones` en 4 de 119.

Por eso «en algunos meses» era falso para el objeto que encabeza el bloque y
verdadero para el catálogo en conjunto: una misma frase no puede describir a
los dos. El titular de la portada ya no hace una afirmación temporal; lleva
las dos cifras que sí se sostienen sobre todo el catálogo (230.288 filas
idénticas en 22 de 90 objetos) y este documento guarda la medición temporal.

## 2. Cómo se reproduce

```sql
WITH base AS (SELECT * FROM read_parquet(
       'docs/outputs/ffmm/cartera_nacional/*.parquet', union_by_name = true)),
     a AS (SELECT periodo, count(*) AS filas FROM base GROUP BY periodo),
     b AS (SELECT periodo, count(*) AS filas
           FROM (SELECT DISTINCT * FROM base) GROUP BY periodo)
SELECT a.periodo, a.filas AS publicadas, b.filas AS distintas, a.filas - b.filas AS repetidas
FROM a JOIN b USING (periodo)
ORDER BY a.periodo;
-- 57 períodos, 57 con repetidas, entre 2.127 y 3.335 por mes
```

## 3. Lo que no se hizo

No se añadió ninguna cifra temporal a la página: ni «57 meses» ni «todos los
períodos» son datos que hoy publique el catálogo, y escribirlos a mano en el
HTML sería la misma clase de defecto que este repositorio ya corrigió con las
demás cifras. Si se quiere en pantalla, primero tiene que salir de
`docs/api/claves.csv`, con una columna medida en el pipeline.

## 4. Addendum — inspección local de `fi_pactos` (2026-10-26)

La relectura de los 15 Parquet anuales confirma **1.698 filas, 1.686 distintas y
12 filas extra idénticas**, distribuidas en cinco cierres: 2016-09 (6; fondos
7182: 4 y 9082: 2), 2016-12 (3; 9082), 2017-03 (1; 9082), 2019-03 (1; 9280) y
2019-06 (1; 9280). Para esos cierres, `historico_control.json` registra,
respectivamente, 48, 38, 49, 41 y 53 operaciones; esos conteos coinciden con
las filas publicadas y el control registra cero filas ilegibles y cero
cuadraturas fallidas.

Reproducción de la distribución (las columnas de `*` forman la identidad de
fila completa; `copias - 1` cuenta sólo las apariciones extra):

```sql
WITH duplicadas AS (
  SELECT *, count(*) AS copias
  FROM read_parquet('docs/outputs/fi/pactos/*.parquet', union_by_name = true)
  GROUP BY ALL
  HAVING count(*) > 1
)
SELECT periodo, run_fondo, sum(copias - 1) AS filas_extra_identicas
FROM duplicadas
GROUP BY periodo, run_fondo
ORDER BY periodo, run_fondo;
-- 2016-09: 7182=4, 9082=2; 2016-12: 9082=3; 2017-03: 9082=1;
-- 2019-03: 9280=1; 2019-06: 9280=1; total=12.
```

El control conserva conteos y resúmenes SHA-256 de respuestas, no el HTML ni
las filas fuente. El repositorio tampoco contiene las páginas de origen de esos
fondos y cierres. El parser actual conserva filas legibles y excluye plantillas
sólo bajo condiciones explícitas, pero eso no prueba qué respuesta histórica
produjo cada Parquet. Por tanto, la causa de las 12 repeticiones sigue sin
clasificarse como propia de la fuente o introducida por el proceso. No se
eliminaron ni se etiquetaron como defecto o como legítimas.

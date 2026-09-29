# Auditoría de formatos de RUT entre industrias

**Fecha:** 2026-09-29
**Alcance:** todas las columnas `rut*` y `run_*` de los Parquet publicados en `docs/outputs/`.
**Estado:** hallazgo abierto. Afecta a los cruces entre industrias.

---

## Resumen

El RUT está homologado **dentro** de cada industria, pero no **entre** industrias. Conviven
tres convenciones de escritura, y la misma columna `rut` significa cosas distintas según el
sector que la publique.

| Formato | Ejemplo | Columnas afectadas |
|---|---|---:|
| A — puntos y dígito verificador | `12.345.678-9` | 7 |
| B — dígito verificador, sin puntos | `12345678-9` | 12 |
| C — cuerpo solo, sin dígito verificador | `12345678` | 17 |
| E — otros / mixto | — | 1 |

La consecuencia práctica es que **un `JOIN` directo entre dos industrias devuelve cero filas
sin lanzar ningún error**. El fallo es silencioso: la consulta parece correcta, el resultado
parece «no hay coincidencias», y en realidad los identificadores nunca se compararon en el
mismo formato.

---

## Caso que lo motivó

```sql
-- Devuelve 0 filas.
SELECT ...
FROM seguros_renta_fija s
JOIN ffmm_cartera_nacional f USING (rut_emisor)
WHERE s.periodo = '2026-08';
```

Porque la misma entidad se escribe distinto en cada origen:

| Vista | `rut_emisor` |
|---|---|
| `seguros_renta_fija` | `97006000` |
| `ffmm_cartera_nacional` | `97006000-9` |
| `bancos_lista_entidades` (columna `rut`) | `97.006.000-9` |

Normalizando al cuerpo del RUT, el cruce sí funciona y aparecen **147 emisores** presentes a
la vez en carteras de seguros y de fondos mutuos, en el período 2026-08.

```sql
-- Funciona: 147 emisores compartidos.
... split_part(replace(rut, '.', ''), '-', 1) ...
```

---

## El caso más grave: falla dentro de una misma industria

En `corredoras_bolsa` el maestro y los estados financieros no comparten formato:

| Conjunto | Columna | Ejemplo |
|---|---|---|
| `corredoras_bolsa_maestro` | `rut` | `96571220-8` |
| `corredoras_bolsa_registro_universo` | `rut` | `96571220-8` |
| `corredoras_bolsa_balance` | `rut` | `76017206` |
| `corredoras_bolsa_resultados` | `rut` | `76017206` |

Resultado de cruzar maestro con balance:

| Condición de cruce | Coincidencias |
|---|---:|
| `maestro.rut = balance.rut` | **0** |
| `maestro.rut = balance.rut_dv` | 24 |
| `split_part(maestro.rut,'-',1) = balance.rut` | 24 |

El cruce por el nombre de columna obvio es precisamente el que falla.

---

## Inventario por industria

| Industria | Columna | Formato |
|---|---|---|
| agf | `rut` | C |
| agf | `rut_dv` | B |
| agf | `rut_completo` | A |
| bancos | `rut` | A |
| cajas_compensacion | `rut` | C |
| cajas_compensacion | `rut_dv` | B |
| cajas_compensacion | `rut_completo` | A |
| cooperativas | `rut` | B |
| cooperativas | `rut_cuerpo` | C |
| corredoras_bolsa | `rut` | **B y C** |
| corredoras_bolsa | `rut_cuerpo` | C |
| corredoras_bolsa | `rut_dv` | B |
| factoring_leasing | `rut` | B |
| factoring_leasing | `rut_cuerpo` | C |
| factoring_leasing | `rut_formateado` | A |
| ffmm | `rut_emisor` | B |
| ffmm | `rut_fondo_completo` | B |
| ffmm | `rut_agf` | C y otros |
| ffmm | `run_fondo` | C |
| fi | `rut_emisor` | C |
| fi | `rut_contraparte` | C |
| fi | `rut_fondo_dv` | B |
| fintech | `rut_completo` | A |
| pensiones | `rut_administradora` | A |
| securitizadoras | `rut`, `rut_administradora` | C |
| securitizadoras | `rut_dv`, `rut_completo` | B |
| seguros | `rut_aseguradora` | B |
| seguros | `rut_emisor` | C |
| seguros | `rut_emisor_activo_objeto` | C |
| seguros | `rut_administradora` | C |
| sistemas_pago | `rut_completo` | A |

Observación: las industrias que publican el trío `rut` / `rut_dv` / `rut_completo`
(agf, cajas_compensacion, factoring_leasing, securitizadoras) son las que mejor resuelven
el problema, porque dejan elegir el formato al consumidor. El patrón recomendable es ese.

---

## Corrección propuesta

1. **Convención única**: `rut` = cuerpo sin puntos ni DV (formato C), en todas las industrias.
2. **Columnas acompañantes** `rut_dv` (B) y `rut_completo` (A) donde ya existan, para no
   romper a quien las use hoy.
3. **Auditoría que lo vigile**: una comprobación que recorra los Parquet publicados y falle
   si una columna `rut*` no cumple el formato declarado para su nombre.
4. **Homologar `corredoras_bolsa` primero**, por ser el caso que falla dentro de una misma
   industria.

Mientras tanto, el README documenta la limitación de forma explícita y los ejemplos de
consulta incluyen la normalización con `split_part`.

---

## Hallazgo adicional, no relacionado con el RUT

`agf_lista_entidades.fondos_inversion_administrados` vale **0 en los 72 registros**
(56 vigentes y 16 no vigentes). La consulta sugerida en la web «Ranking de AGF por Fondos de
Inversión Administrados», que filtra por `fondos_inversion_administrados > 0`, devuelve por
tanto una tabla vacía. Hay que corregir el extractor o retirar la consulta sugerida.

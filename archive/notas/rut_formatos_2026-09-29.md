# Auditoría de formatos de RUT entre industrias

**Fecha:** 2026-09-29
**Alcance:** todas las columnas `rut*` y `run_*` de los Parquet publicados en `docs/outputs/`.
**Estado:** RESUELTO (2026-09-29). Convención aplicada a todo lo publicado, guardián
en CI y todos los writers blindados para que la próxima corrida no la regrese.

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

## Corrección aplicada (decisión del mantenedor: «aplica todo», ambas fases)

### Convención canónica (única, transversal)

| Columna | Formato | Ejemplo |
|---|---|---|
| `rut` | C — cuerpo | `97004000` |
| `rut_<entidad>` (FK: `rut_emisor`, `rut_aseguradora`, `rut_administradora`, …) | C | `97004000` |
| `rut_dv`, `*_dv` | B — cuerpo-DV | `97004000-5` |
| `rut_completo`, `*_completo` | A — puntos y DV (RUNs de 4-5 cifras quedan B) | `97.004.000-5` |
| `run_*` | fuera de convención (identificador de fondo) | `0023-2` |
| columnas `rut` numéricas (int64) | ya son el cuerpo | `97004000` |

- `rut_cuerpo` y `rut_formateado` **dejan de existir** (sobreviven `rut` y `rut_completo`).
- DV oficial módulo 11 (multiplicadores 2-7 con retorno a 2): verificado contra DVs
  publicados (97004000→5, 82878900→7, 96571220→8, 92770000→K).
- Placeholders numéricos cortos del origen (`'0'`, `'1'`, `'90'` = emisor no identificado)
  se conservan tal cual.

### Implementación

1. **`pipelines/auto/rut.py`** — módulo de la convención: `dv()`, `dv_valido()`,
   `cuerpo/con_dv/con_puntos`, `normalizar_registro(s)` (JSON/listas) y
   `normalizar_tabla`/`normalizar_dataframe` (PyArrow/pandas). Idempotente.
2. **Backfill aplicado a lo publicado** (`scripts/normalizar_rut_publicado.py --apply`):
   **193 Parquet + 7 JSON** reescritos conservando límites de row group, codec y estilo de
   JSON; sin metadata `pandas` obsoleta. Segunda corrida: 0 pendientes (idempotente).
3. **Valores corruptos de fuente corregidos** (ffmm `cartera_nacional`): `92770000-X`
   (DV inválido) → DV `K` calculado por módulo 11, y luego a cuerpo; `0-.` → `0`
   (4 filas en 2024-10, 2026-04 y 2026-05). Conteos de filas intactos.
4. **Guardián en CI** (`scripts/audit_rut_formatos.py`, paso en `web_audit.yml`):
   audita los 613 archivos publicados y falla si una columna `rut*`/`run*` incumple su
   formato, si reaparece `rut_cuerpo`/`rut_formateado`, o si la metadata pandas heredada
   describe columnas RUT que ya no existen.
5. **Writers blindados** (la próxima corrida de CI no regresa el problema):
   `pipelines/entidades/actualizar_listas.py::guardar()` (único punto de escritura de las
   listas de entidades), `cooperativas/scripts/01_build_cooperativas_maestro.py`,
   `corredoras_bolsa/scripts/01_build_universe_corredoras.py`,
   `factoring_leasing/scripts/publish_backfill.py` (`atomic_parquet` + diccionario),
   `ffmm/scripts/actualizar_carteras.py`, `seguros/scripts/actualizar_carteras.py`
   (series + `aseguradoras.parquet`) y `pensiones/scripts/generate_afp_maestro.py`.
   `pipelines/ifrs_sectores/actualizar.py` ya emitía el formato canónico.
6. **Consumidores actualizados**: diccionario de datos (`data_dictionary.js`), ERD
   (`erd_graph.js`), bundles (`data_bundles.js`), catálogo de descargas regenerado,
   `audit_factoring_leasing.py`, `test_bank_master_identity.py` y las auditorías locales
   de cooperativas y pensiones.
7. **Resultado**: el cruce que motivó el hallazgo vuelve a funcionar sin trucos —
   `corredoras_bolsa_maestro.rut = corredoras_bolsa_balance.rut` pasa de 0 a miles de
   filas; el guardián reporta 613 archivos auditados, 0 problemas.

---

## Hallazgo adicional, no relacionado con el RUT (resuelto)

`agf_lista_entidades.fondos_inversion_administrados` valía **0 en los 72 registros**
(56 vigentes y 16 no vigentes). La consulta sugerida en la web «Ranking de AGF por Fondos de
Inversión Administrados», que filtra por `fondos_inversion_administrados > 0`, devolvía por
tanto una tabla vacía.

**Resuelto (2026-09-29):** el extractora de AGF (`fi/scripts/actualizar_carteras.py`, función
`actualizar_fondos_agf`) ahora calcula el total de fondos de inversión administrados desde las
carteras publicadas, y el backfill ya actualizó `docs/outputs/agf/agf_maestro.parquet`:
**47 de los 72 registros** quedan con valor > 0 (los 25 restantes son no vigentes o sin
carteras publicadas, y conservan 0 legítimamente). La consulta sugerida vuelve a devolver
resultados y la auditoría la reporta como OK.

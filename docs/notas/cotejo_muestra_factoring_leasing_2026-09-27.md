# Cotejo de muestra — Factoring y Leasing (archivo estructurado CMF vs ficha)

Fecha: 2026-09-27. Corrida aprobada: Actions [36337279448](https://github.com/joaquinignaciomondaca-code/monitor-financiero-chile/actions/runs/36337279448), commit `4355226`. Solo se publican **dos filas**.

## Qué se cotejó y qué no

Se comparó, por entidad y período, el **archivo estructurado público** de CMF
(`institucional/estadisticas/ver_archivo.php?inicio=AAAAMM&termino=AAAAMM`, texto delimitado por `;`, **no XML**)
contra la **tabla HTML de la ficha de información financiera** de la misma entidad y corte:

| Segmento | Entidad | RUT | Período | Balance | Activos | Pasivos | Patrimonio | Efectivo |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| Factoring | FACTORING SECURITY S.A. | 96655860-1 | 2022-06 | Individual | 435.359.519 | 376.903.204 | 58.456.315 | 6.110.582 |
| Leasing | UNIDAD LEASING HABITACIONAL S.A. | 96809970-1 | 2022-09 | Individual | 28.116.046 | 21.817.177 | 6.298.869 | 66.021 |

Unidad: **miles de pesos chilenos (CLP)** en ambos casos. Activos = pasivos + patrimonio en las dos filas.
La selección de entidad y período fue anterior al cotejo, no se eligió después de ver los resultados.

Controles que deben pasar para aprobar (si uno falla, la muestra se rechaza y no se publica):
identidad por nombre y RUT-DV en la ficha, tipo de balance individual, unidad CLP en miles, cierre visible,
etiqueta exacta de cada cuenta, comparativo numérico presente, valor entero convertible a miles sin pérdida,
cuenta sin duplicados en el archivo, coincidencia exacta y cuadre contable.

## Límites explícitos

* Son **dos entidades y un período cada una**. No certifica los 28 miembros del catálogo, ni otros períodos,
  ni balances consolidados, ni la vigencia registral de la lista.
* Los **XBRL y los PDF** que ofrecen las mismas fichas **no** fueron cotejados; CMF advierte que su contenido está en revisión.
* Los scripts antiguos (`pipeline_stream_factoring_leasing.py`, `stream_cmf_eeff_series.py`) siguen bloqueados:
  redondeaban a millones, rellenaban faltantes con cero, calculaban el DV en vez de contrastarlo y usaban tipo de
  cambio de respaldo. La publicación usa un camino distinto y verificado.
* La unidad publicada es la de la ficha; no se convierte a unidades ni a USD.

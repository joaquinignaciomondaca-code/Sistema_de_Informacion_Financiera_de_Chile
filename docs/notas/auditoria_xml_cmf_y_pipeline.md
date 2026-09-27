# Auditoría acotada XML CMF y extracción masiva en cuarentena

Corte 2026-09-27. **No certificación oficial ni sustitución automática de datos publicados.**

## Corredoras (carátula publicada)

Se midió directamente el Parquet publicado `corredoras_bolsa_caratula_eeff_historico`:
621 balances, 24 corredoras, 26 cortes (2018-12 a 2026-06). No hay filas duplicadas
por `(rut, periodo)`, ni RUT fuera del universo registrado, ni nulos en columnas.
`total_activos_m_clp - total_pasivos_m_clp - patrimonio_neto_m_clp = 0`
exactamente en 621/621; ningún total de activos, pasivos o patrimonio es cero.
El `balance_resumen` replica exactamente todas las columnas compartidas: **no constituye
un cotejo externo**. En la ficha CMF se contrastaron dos períodos de Banchile:
activos 2024-12 = 807.006.393 y 2023-12 = 894.203.128 (M$) — iguales al Parquet.

**Límites:** 2 comparaciones / una entidad no prueban el universo; el extractor
original silencia errores, puede convertir parseos inválidos a cero y usa FX de
respaldo. La tabla de carátulas permanece publicada, no así los pactos de PDF.
El pipeline nuevo valida RUT, DV del XML cuando existe, período XML, moneda,
cuadre, resultado no ausente y hash de fuente. Esto mejora la calidad de *nuevas*
extracciones; **no retrocertifica** las filas históricas ya publicadas.

## Industrias / alcance de la automatización

| Sector | Universo del repo | Fuente | Objetivo de la ruta nueva | Publicación |
|---|---|---|---|---|
| Corredoras | 120, 24 vigentes | COBOL `IVEF` XML | balance + resultado | Solo artifact |
| Fondos mutuos | 1.543 registrados | RGFMU `FMEF` XML | balance (activo neto) + resultado | Solo artifact |
| Fondos de inversión | 1.677, FIRES/FINRE | `FIEF` XML, pestaña 29 | balance + resultado cuando existen | Solo artifact |
| AGF | 68 | XBRL individual | inventario de contextos y unidades; **sin cifras comparables hasta mapear taxonomía** | Solo artifact |
| Retail financiero | 17 | RVEMI XBRL individual | igual, sin cifras presumidas | Solo artifact |

El job `xml_eeff_review.yml` reparte entidades en 4 shards estables, limita a 90
combinaciones por sector/shard y corrida, usa cursor y cache de Actions para
continuar; por defecto consulta los dos últimos cortes. La ejecución manual
`all_periods=true` avanza sobre cortes trimestrales desde 2011 y entidades históricas
**por lotes**, sin intentar todo en un job de 35 minutos. Resultados crudos de
balance/resultado XML en el JSONL de revisión, manifest y excepciones; NO se
escriben `docs/outputs`, ni se hace commit. Para XBRL se incluye inventario pero
no balance/resultado inferidos; hace falta desarrollar mapeo versionado de
conceptos, dimensión, moneda, consolidación y períodos antes de publicar.

Nota operativa: el HTML/XML CMF no responde desde este sandbox (EOF TLS local);
la prueba real depende de la red de GitHub Actions y **una corrida exitosa de
workflow no implica que exista ningún XML validado**. Revisar los artifacts por
`status` antes de usar cualquier cifra. Los fondos pueden reportar moneda propia:
no convertir USD/PROM a CLP sin tipo de cambio, ni mezclar unidades en agregaciones.

Pendientes explícitos: pólizas de seguros, cooperativas, bancos y patrimonio
separado requieren endpoints o formatos distintos; no se los marca como
soportados. `docs/notas/fuentes_xml_por_industria.md` mantiene el inventario.

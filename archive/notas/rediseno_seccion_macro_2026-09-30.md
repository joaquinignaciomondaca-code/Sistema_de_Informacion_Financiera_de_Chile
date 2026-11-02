# Rediseño de la sección Macroeconomía — propuesta de estructura (2026-09-30)

Objeto: la sección macro del sitio (`docs/`), hoy desplegada en Vercel. **Este documento es una propuesta para aprobar; no se ha tocado ningún dato ni código.** La implementación parte cuando se valide esta estructura.

Motivación del usuario: la sección no es lo que se debería entregar al cliente final — está mal jerarquizada y hay tablas que mezclan temas distintos y conviene separarlas. Principios pedidos:

1. **Cada serie con tema o contenido diferente, separada** (nada de tablas cajón de sastre).
2. **El nombre de la tabla describe su contenido** (no nombres genéricos tipo "precios_actividad").
3. **Los datos son autoexplicativos**: ninguna fila depende de un código críptico (tipo nemotécnico o `clave`) para saber qué es. Si hay códigos, la fila trae también su significado.

---

## 1. Qué está mal hoy

Árbol actual:

```
MACROECONOMÍA & TASAS (BCCh)  [1 Entidad · 51 series]
└─ Estadísticas Financieras y Macroeconómicas      ← sector de relleno
   ├─ Tasas de Interés y Curvas Soberanas [153 Registros]
   │  └─ macro.tasas_rendimientos   153 × 15 col  (TPM, TIB, BCP, BCU, SPC, breakevens)
   ├─ Mercado Cambiario & Divisas [153 Registros]
   │  └─ macro.divisas_mercado      153 × 13 col  (USD, EUR, TCM, TCR)
   ├─ Precios, Actividad y Expectativas [153 Registros]
   │  └─ macro.precios_actividad    153 × 15 col  (UF, UTM?, IPC, IMACEC, cobre, EEE)
   └─ Catálogo amplio de series BCCh (diarias, mensuales y trimestrales) [51 series]
      ├─ macro.series               79.895 filas  (fecha, periodo, clave, serie_id, valor)
      └─ macro.series_catalogo      51 filas
```

Defectos concretos:

| # | Defecto | Evidencia |
|---|---------|-----------|
| 1 | Nivel de jerarquía muerto | "Estadísticas Financieras y Macroeconómicas" no agrega información; en otros sectores ese nivel identifica la industria y las carpetas siguen un patrón uniforme |
| 2 | Tablas cajón de sastre | `precios_actividad` mezcla UF (reajustes), IPC (inflación), IMACEC (actividad), cobre (materia prima) y expectativas (EEE) — 4 temas en 15 columnas. `tasas_rendimientos` mezcla política monetaria, curvas soberanas, swaps y breakevens |
| 3 | Nombres no descriptivos | "divisas_mercado", "precios_actividad" no dicen qué encontrarás dentro; el nombre debería ser el contenido |
| 4 | Datos no autoexplicativos | En `macro.series` cada fila es `(fecha, periodo, clave, serie_id, valor)`: sin unirse al catálogo no se sabe qué es `oro` ni qué unidad trae. `serie_id` (p. ej. `F022.TPM.TIN.D001.NO.Z.D`) es un código opaco |
| 5 | Cobertura incompleta de las tablas anchas | Los paneles mensuales solo traen ~33 de las 51 series: UTM, PIB, reservas, deuda/PIB, IMACEC minería/comercio/servicios, BCU 1/2/30 años, SPC 90/180/360d, EEE TPM, EOF, oro, plata, TCM y fed funds solo viven en `macro.series` |
| 6 | Etiquetas para desarrollador, no para cliente | Badges "153 Registros" (¿registros de qué?), "51 series" que solo cuenta el catálogo; el grupo se llama "MACROECONOMÍA & TASAS (BCCh)" en el árbol, "Macroeconomía y Tasas" en Descargas y "Macroeconomía (BCCh)" en el manifiesto |
| 7 | Diccionario incompleto | Solo `macro.series` y `macro.series_catalogo` tienen ficha; las 3 tablas mensuales no aparecen en el Diccionario |
| 8 | ERD truncado y relaciones confusas | Muestra 8–9 de las 15 columnas reales y un enlace "periodo (expectativas e inflación)" que mezcla conceptos |

---

## 2. Propuesta de jerarquía (explorador)

Una carpeta por tema económico. Sin nivel de relleno. Nombres cortos y paralelos entre sí.

```
MACROECONOMÍA (BCCh)                                          [51 series · 2014 → 2026]
└─ Estadísticas Económicas (BCCh · Base de Datos Estadísticos SIETE)
   ├─ Tasas de interés
   │  ├─ macro.tasas_corto_plazo            TPM y TIB, promedio mensual
   │  ├─ macro.swaps_camara                 Swap promedio de cámara (SPC), pesos y UF
   │  ├─ macro.curva_bonos_pesos            Rendimientos BCP 2, 5 y 10 años
   │  ├─ macro.curva_bonos_uf               Rendimientos BCU 1 a 30 años
   │  └─ macro.inflacion_implicita          Breakeven de inflación 5 y 10 años
   ├─ Tipo de cambio
   │  ├─ macro.dolar_observado              USD/CLP: promedio, cierre, rango, variaciones y volatilidad
   │  ├─ macro.euro_observado               EUR/CLP: promedio, cierre y variación
   │  ├─ macro.tipo_cambio_multilateral     Índices TCM, TCM-5 y TCM-X
   │  └─ macro.tipo_cambio_real             Índices TCR y TCR-5
   ├─ Precios y reajustes
   │  ├─ macro.uf                           Unidad de Fomento: cierre, promedio y variación
   │  ├─ macro.utm                          Unidad Tributaria Mensual
   │  └─ macro.inflacion_ipc                IPC: índice y variaciones mensual y anual
   ├─ Actividad económica
   │  ├─ macro.imacec                       IMACEC total, no minero, minería, comercio y servicios
   │  └─ macro.pib_trimestral               PIB volumen encadenado, trimestral
   ├─ Mercado laboral
   │  └─ macro.mercado_laboral              Desocupación, ocupados, asalariados y fuerza de trabajo
   ├─ Materias primas
   │  ├─ macro.cobre                        Cobre refinado BML (USD/libra)
   │  └─ macro.metales_preciosos            Oro y plata (USD/onza troy)
   ├─ Sector externo y fiscal
   │  ├─ macro.reservas_internacionales     Activos de reserva (millones de USD)
   │  ├─ macro.tasa_referencia_fed          Tasa de política EE.UU. (fed funds)
   │  └─ macro.deuda_publica_pct_pib        Deuda bruta Gobierno Central (% del PIB, trimestral)
   ├─ Expectativas
   │  ├─ macro.expectativas_inflacion       EEE inflación 11 y 23 meses y desvío vs meta
   │  ├─ macro.expectativas_tpm             EEE TPM 11 y 23 meses
   │  └─ macro.expectativas_operadores      EOF inflación y TPM a 12 meses
   └─ Metadatos
      ├─ macro.series_catalogo              Las 51 series: nombre oficial, unidad, frecuencia, cobertura y estado
      └─ macro.series_formato_largo         Detalle en frecuencia nativa, con nombre y unidad en cada fila
```

Mejoras frente al árbol actual:

- **8 carpetas temáticas** en lugar de 4 con nombres de largo desigual.
- Cada carpeta contiene tablas del mismo tema; ninguna tabla mezcla temas.
- El badge del grupo pasa a ser cobertura y fuente (`2014 → 2026 · BCCh SIETE`), no "1 Entidad".
- Badges de tarjeta con unidad real del contenido (`153 meses`, `6 tenores`, `51 series`), según `docs/NAMING.md` §3.

---

## 3. Propuesta de tablas (modelo de datos)

Reglas aplicadas (alineadas con `docs/NAMING.md` y con los principios del usuario):

- **Una tabla = un tema/indicador.** Si dos series son el mismo instrumento a distinto plazo o variante (curva BCP, IMACEC, IPC) van juntas; si son de contenido distinto (cobre vs oro, dólar vs euro) van separadas.
- **El nombre de la tabla es el contenido en español**: `macro.dolar_observado`, no `macro.divisas_mercado`.
- **Columnas autoexplicativas**: `<indicador>_<métrica>_<unidad>` cuando aporta (`dolar_observado_cierre_clp`, `tasa_rendimiento_bcp_2_anos_pct`). Sin abreviaturas internas del pipeline (`spc_clp_2y`, `eee_ipc_11m`).
- **Sin códigos crípticos en las filas**: `clave`/`serie_id` solo quedan en `macro.series_formato_largo` y siempre acompañados de `nombre_serie`, `unidad`, `frecuencia` y `grupo` en la misma fila (más `codigo_bcch` para trazabilidad).
- **Frecuencia de cada tabla = la de su tema**: mensual para la mayoría, trimestral para PIB y deuda pública. Las series diarias se resumen a mes con regla declarada en el diccionario (tipo de cambio y UF: promedio y cierre de mes; tasas y swaps: promedio mensual; commodities y fed funds: promedio mensual; EOF: promedio mensual). El detalle diario vive en `macro.series_formato_largo`.

### 3.1 Inventario de tablas temáticas (23)

| Tabla nueva | Frec. | Columnas (nuevo ← origen) | Viene de |
|---|---|---|---|
| `macro.tasas_corto_plazo` | M | `tpm_pct` ← tpm · `tib_promedio_pct` ← tib_promedio | tasas_rendimientos |
| `macro.swaps_camara` | M | `swap_pesos_90_dias_pct` ← spc_clp_90d · `swap_pesos_180_dias_pct` · `swap_pesos_360_dias_pct` · `swap_pesos_2_anos_pct` · `swap_uf_1_ano_pct` ← spc_uf_1y | tasas_rendimientos + series (completa) |
| `macro.curva_bonos_pesos` | M | `tasa_rendimiento_bcp_2_anos_pct` ← bcp_2y · `…_5_anos_pct` · `…_10_anos_pct` · `pendiente_10_2_puntos_basicos` ← spread_bcp_10y_2y_bps · `pendiente_5_2_puntos_basicos` | tasas_rendimientos |
| `macro.curva_bonos_uf` | M | `tasa_rendimiento_bcu_1_ano_pct` … `…_30_anos_pct` (6 tenores) | tasas_rendimientos + series (completa) |
| `macro.inflacion_implicita` | M | `breakeven_5_anos_pct` ← inflacion_implicita_5y_breakeven · `breakeven_10_anos_pct` | tasas_rendimientos |
| `macro.dolar_observado` | M | `dolar_observado_promedio_clp` ← usd_clp_promedio · `…_cierre_clp` · `…_minimo_clp` · `…_maximo_clp` · `…_var_mensual_pct` · `…_var_anual_pct` · `…_volatilidad_anualizada_pct` | divisas_mercado |
| `macro.euro_observado` | M | `euro_observado_promedio_clp` ← eur_clp_promedio · `…_cierre_clp` · `…_var_mensual_pct` | divisas_mercado |
| `macro.tipo_cambio_multilateral` | M | `tipo_cambio_nominal_multilateral_indice` ← tcm · `…_5_monedas_indice` ← tcm_5 · `…_tcm_x_indice` ← tcm_x | **series (nuevo al panel)** |
| `macro.tipo_cambio_real` | M | `tipo_cambio_real_general_indice` ← tcr_general · `tipo_cambio_real_5_monedas_indice` ← tcr_5monedas | divisas_mercado |
| `macro.uf` | M | `uf_cierre_clp` ← uf_cierre · `uf_promedio_clp` · `uf_var_mensual_pct` | precios_actividad |
| `macro.utm` | M | `utm_clp` ← utm | **series (nuevo al panel)** |
| `macro.inflacion_ipc` | M | `ipc_indice_2023_100` ← ipc_indice · `ipc_var_mensual_pct` · `ipc_var_anual_pct` | precios_actividad |
| `macro.imacec` | M | `imacec_empalmado_indice_2018_100` ← imacec_empalmado · `imacec_no_minero_indice_2018_100` · `imacec_mineria_indice_2018_100` · `imacec_comercio_indice_2018_100` · `imacec_servicios_indice_2018_100` · `imacec_var_anual_pct` | precios_actividad + series (completa) |
| `macro.pib_trimestral` | T | `pib_encadenado_2018_miles_mm_clp` ← pib | **series (nuevo al panel)** |
| `macro.mercado_laboral` | M | `desocupacion_pct` ← desocupacion · `ocupados_miles_personas` · `asalariados_miles_personas` · `fuerza_trabajo_miles_personas` | **series (nuevo al panel)** |
| `macro.cobre` | M | `cobre_spot_usd_por_libra` ← cobre_mensual · `cobre_var_anual_pct` | precios_actividad + series |
| `macro.metales_preciosos` | M | `oro_usd_por_onza_troy` ← oro · `plata_usd_por_onza_troy` ← plata | **series (nuevo al panel)** |
| `macro.reservas_internacionales` | M | `reservas_internacionales_millones_usd` ← reservas | **series (nuevo al panel)** |
| `macro.tasa_referencia_fed` | M | `tasa_fed_funds_pct` ← fed_funds | **series (nuevo al panel)** |
| `macro.deuda_publica_pct_pib` | T | `deuda_bruta_gobierno_central_pct_pib` ← deuda_publica_pib | **series (nuevo al panel)** |
| `macro.expectativas_inflacion` | M | `expectativa_inflacion_ipc_11m_pct` ← eee_ipc_11m · `expectativa_inflacion_ipc_23m_pct` · `desvio_expectativa_11m_vs_meta_puntos_basicos` ← desvio_eee_11m_meta_bps | precios_actividad + series |
| `macro.expectativas_tpm` | M | `expectativa_tpm_11m_pct` ← eee_tpm_11m · `expectativa_tpm_23m_pct` | **series (nuevo al panel)** |
| `macro.expectativas_operadores` | M | `expectativa_inflacion_12m_eof_pct` ← eof_ipc_12m · `expectativa_tpm_12m_eof_pct` ← eof_tpm_12m | **series (nuevo al panel)** |

Todas llevan `periodo` (`AAAA-MM`); las trimestrales usan el mes de referencia del trimestre (como hoy).

**Esto arregla el defecto 5**: las 51 series del catálogo tienen por fin un panel mensual propio. Hoy 18 series solo existen en la tabla larga.

### 3.2 Tablas de metadatos

| Tabla | Contenido |
|---|---|
| `macro.series_catalogo` | Se mantiene: 51 filas con nombre, grupo, unidad, frecuencia, título oficial BCCh, cobertura y estado. Ya es autoexplicativa |
| `macro.series_formato_largo` | Hoy `macro.series`. Se le agregan las columnas `nombre_serie`, `unidad`, `frecuencia`, `grupo` (desnormalizadas del catálogo) y `codigo_bcch` (hoy `serie_id`). **Cada fila se entiende sola.** Sirve como detalle en frecuencia nativa (diaria, mensual, trimestral) y como respaldo de los paneles |

### 3.3 Ejemplo de autoexplicatividad (el caso del "nemotécnico")

Fila de `macro.series` hoy — no se entiende sin ir al catálogo:

```
fecha=2026-09-30  periodo=2026-09  clave=oro  serie_id=F030.PRE.USD.ZOZ.D  valor=4XXX.XX
```

La misma fila en `macro.series_formato_largo`:

```
fecha=2026-09-30  periodo=2026-09  nombre_serie=Oro (precio spot)  unidad=USD por onza troy
frecuencia=Diaria  grupo=Commodities  codigo_bcch=F030.PRE.USD.ZOZ.D  valor=4XXX.XX
```

Y el panel equivalente, `macro.metales_preciosos`:

```
periodo=2026-09  oro_usd_por_onza_troy=4XXX.XX  plata_usd_por_onza_troy=XX.XX
```

> Nota: si la tabla con nemotécnicos que se vio es de otra industria (`seguros.acciones`, `ffmm.cartera_nacional`…), el principio se aplica igual: cada fila debe traer el nombre/descripción del instrumento, no solo su código. Eso puede ser una segunda pasada fuera de macro.

---

## 4. Qué pasa con las 3 tablas anchas de hoy

| Tabla actual | Destino |
|---|---|
| `macro.tasas_rendimientos` | Se reparte en `tasas_corto_plazo`, `swaps_camara`, `curva_bonos_pesos`, `curva_bonos_uf`, `inflacion_implicita` |
| `macro.divisas_mercado` | Se reparte en `dolar_observado`, `euro_observado`, `tipo_cambio_real` |
| `macro.precios_actividad` | Se reparte en `uf`, `inflacion_ipc`, `imacec`, `cobre`, `expectativas_inflacion` |

Opción recomendada: **retirarlas del sitio en el mismo release** y dejar una nota de migración en el README (hoy solo las consume el propio sitio). Opción conservadora: mantenerlas un tiempo como vistas de compatibilidad marcadas como "legado" en el diccionario. Punto de decisión (§6).

---

## 5. Mapa de impacto (para la fase de implementación)

| Área | Archivos |
|---|---|
| Pipeline de datos | `macro/scripts/{pipeline_stream_macro_bcch, daily_macro, publish_macro, audit_macro_bcch, series_bcch}.py`, `macro/tests/*` — la publicación derivada de paneles se puede generar desde `macro.series` + catálogo (no requiere tocar la descarga BCCh) |
| Explorador y visor | `docs/js/sidebar.js` (EXPLORER_TREE + chips de consultas sugeridas), `docs/js/data_viewer.js` (DATA_VIEWER_CATALOG) |
| Diccionario | `docs/js/data_dictionary.js` — 25 fichas nuevas con todas las columnas (hoy macro casi no está documentado) |
| ERD | `docs/js/erd_graph.js` — nodos por tabla con todas las columnas, layout por carpetas temáticas |
| Motor SQL | `docs/js/duckdb_client.js` (registro de vistas) |
| Descargas y manifiestos | `docs/js/download_catalog.js` (regenerar), `data_manifest.json` (regenerar) |
| Cifras y textos | `README.md`, `docs/index.html` (52 tablas → nuevo conteo), badges del explorador |
| Automatización | `.github/workflows/macro.yml` |
| Auditorías | `scripts/audit_navigation.py` (SIN_LISTA_ENTIDADES), `scripts/audit_web_full.py`, `scripts/audit_automatizacion.py`, `scripts/audit_consultas_sugeridas.py` |

## 6. Decisiones y puntos abiertos

**Decidido (2026-09-30):** la tabla de oro y plata se llama `macro.metales_preciosos` (término técnico estándar). Se descartó "metales_commodity": mezcla idiomas y, sobre todo, el cobre de la carpeta vecina también es metal commodity, así que el nombre no distinguía el contenido. La carpeta se mantiene como **Materias primas** (agrupa cobre y metales preciosos).

Puntos abiertos:

1. **Granularidad**: ¿23 tablas temáticas como se propone (una por indicador/familia) o consolidar en ~10 (p. ej. una sola `macro.curvas_soberanas` con BCP y BCU, o `macro.expectativas` con EEE y EOF juntas)?
2. **Frecuencia de los paneles**: ¿mensual agregado (recomendado, continuidad con lo actual) o frecuencia nativa por tabla (diaria donde la serie es diaria)?
3. **Vida de las tablas actuales**: ¿retiro inmediato de las 3 tablas anchas o periodo de compatibilidad?
4. **`macro.series_formato_largo`**: ¿visible en el explorador (carpeta Metadatos) o solo disponible en Descargas?
5. **Nemotécnico**: ¿la tabla con nemotécnicos que se vio era de macro (clave/serie_id) o de otra industria? Define si esta pasada alcanza o si abrimos una tarea aparte.

## 7. Plan de implementación (una vez aprobado)

1. Generar las 23 tablas temáticas (publicación derivada desde las series nativas) + `macro.series_formato_largo` enriquecida.
2. Reescribir la sección macro de la web: árbol, visor, diccionario (25 fichas), ERD y consultas sugeridas con lenguaje de cliente.
3. Regenerar `data_manifest.json` y `download_catalog.js`; actualizar contadores del README y auditorías.
4. Retirar (o deprecar) las 3 tablas anchas y `macro.series` actual.
5. Verificar con las suites existentes (`audit_navigation`, `audit_web_full`, `audit_automatizacion`, pruebas de `macro/tests`) + revisión visual.

---

## 8. Implementado (2026-09-30)

Decisiones finales del usuario: **23 tablas** (una por indicador/familia), **frecuencia nativa por serie** (diaria donde existe, mensual o trimestral donde corresponde), **retiro inmediato** de las 3 tablas anchas, y `macro.series` (la tabla del "nemotécnico": `clave`/`serie_id` opacos) **descompuesta en las tablas temáticas** y retirada de la web. Nombre `macro.metales_preciosos` confirmado.

Ajustes respecto a la propuesta del §3: al ser frecuencia nativa desaparecen las columnas de resumen mensual (promedio/cierre/min/max/variaciones); esos cálculos quedan como **consultas sugeridas** en cada carpeta (p. ej. "Dólar observado por mes: promedio, mínimo, máximo y cierre", "UF: valor de cierre de cada mes y variación mensual"). `macro.cobre` conserva dos columnas porque la referencia mensual del BCCh no es el promedio del diario (difieren hasta 0,09 USD/lb). Las fechas donde ningún indicador de la tabla tiene dato se omiten.

Piezas:
- `macro/scripts/build_tablas_tematicas.py` — especificación `TABLAS` (única fuente de verdad) y generación desde las series nativas, con verificación fila a fila.
- `macro/scripts/audit_macro_bcch.py` — reescrito para las tablas temáticas (columnas, fechas, rangos plausibles, cobertura de las 51 series).
- `scripts/build_macro_web.py` — genera el bloque macro de `sidebar.js`, `data_viewer.js`, `data_dictionary.js` (24 fichas con todas las columnas), `erd_graph.js`, `duckdb_client.js` y `vocabulario.json` entre marcadores `<macro:inicio>`/`<macro:fin>`; `--check` para auditoría.
- `.github/workflows/macro.yml` — `series_bcch` → `build_tablas_tematicas` → `audit_macro_bcch` → commit. Sin checkpoint ni `bcchapi`.
- Retirados: `pipeline_stream_macro_bcch.py`, `daily_macro.py`, `publish_macro.py`, sus tests, y los 6 archivos de las tablas anchas. `sistemas_pago/scripts/stream_sistemas_pago.py` pasa a leer `macro_dolar_observado` y `macro_tasas_corto_plazo`.
- Cifras globales: 71 tablas web / 70 datasets, 10.831.640 filas (README, `index.html`, PSEUDOCODIGO, inventario de automatización).

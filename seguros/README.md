# Seguros de vida y generales (CMF — Circular 1835)

El extractor lee los archivos mensuales de cartera de las compañías de vida (`CSVID`) y generales (`CSGEN`) y publica las tablas de `docs/outputs/seguros/`. La ficha técnica cubre dos formatos: el vigente hasta 2024-11 y el formato usado desde 2024-12.

## Qué se publica y con qué nombres

Se publican **todos** los campos de cada registro de la Circular 1835, con el **nombre original
con que la CMF los imprime en la ficha técnica** (en minúsculas; p. ej. `costo_amortizado_clp`,
`nro_rut`, `pres_bursatil`). Dos reglas derivadas de la fuente:

- **Unidad al final del nombre.** Si la ficha declara la unidad, el nombre la lleva como sufijo:
  `_m_clp` (miles de pesos), `_clp` (pesos), `_uf`, `_um` (unidad monetaria del instrumento).
  Una misma columna puede cambiar de unidad entre épocas; el diccionario lo indica.
- **Nombres repetidos.** Cuando la ficha repite un nombre dentro de un registro, el segundo
  lleva el sufijo que corresponda a su uso (`..._unidades`, `..._valor_contable`, ...). En los
  swaps (`p5`) `ACTIVO_OBJETO_POSICION_LARGA/CORTA` es el nocional, no el nombre del activo:
  se publica como `activo_objeto_posicion_larga_nocional` / `..._corta_nocional` para no
  mezclar texto con número.

No se publican el tipo de registro, los rellenos (`FILLER`) ni los dígitos verificadores sueltos
(el DV viaja con el RUT, como `97.004.000-5`).

De ahí salen, generados:

| Archivo | Qué es | Cómo se regenera |
|---|---|---|
| `seguros/fuentes/inventario_1835.json` | todos los campos, posiciones y descripciones de la ficha | `python -m seguros.scripts.inventario_1835 --escribir` |
| `docs/js/diccionario_seguros.js` | diccionario de columnas para la web y el Excel | `python -m seguros.scripts.diccionario_1835` |
| columnas de seguros en `docs/js/data_dictionary.js` | ficha de cada tabla en el Diccionario de Datos | `python -m seguros.scripts.diccionario_1835` |

**Descargas:** el Excel lleva dos hojas, `Datos` y `Diccionario` (una fila por columna: nombre,
tipo, unidad, nombre en la ficha, registro y descripción). El CSV se mantiene como estaba.

## Circular 1835 · catálogo completo y vistas analíticas

El catálogo respeta la numeración y los títulos del manual CMF, desde **B.1 INSTRUMENTOS DE RENTA FIJA** hasta **B.14 GARANTÍAS EN INSTRUMENTOS DERIVADOS**. Las tablas de cada registro conservan el conjunto completo de campos oficiales. Para los registros extensos, se agregan vistas paralelas de **campos relevantes** (no agregan ni resumen filas; sólo proyectan columnas) para análisis económico-financiero:

- B.1 Renta fija, B.2 Acciones, B.4 Bienes raíces, B.5 Inversiones en el extranjero, B.7 Derivados, B.12 Préstamos y B.13 Bienes raíces en arriendo/morosidad.
- Las vistas completas y reducidas coexisten como tablas separadas; la numeración y el nombre del registro siguen los del manual. El detalle del tipo indica «Campos relevantes».
- El catálogo, diccionario de columnas, visor, explorador SQL y descargas se construyen a partir de `seguros/scripts/vistas_1835.py`, `metadatos_web.py`, el inventario y `docs/vocabulario.json`.

### Privacidad de los registros B.4 y B.12–B.14

Las columnas de la ficha oficial se mantienen en el esquema para preservar compatibilidad, pero los valores sensibles se suprimen antes de publicar:

- B.4: dirección exacta y rol se sustituyen por `property_id`, seudónimo estable que permite análisis longitudinal sin revelar ubicación o identificador tributario del inmueble.
- B.12: RUT, DV y nombres del deudor se suprimen cuando corresponde a una persona natural.
- B.13: rol del inmueble y datos identificadores de arrendatarios/deudores personas naturales; se conserva `property_id`.
- B.14: RUT y nombre de contrapartes que probablemente sean personas naturales; se añade `contraparte_tipo` para dejar constancia de la clasificación de privacidad.

La fuente y los nombres de los campos corresponden al [anexo técnico oficial de la Circular 1835 (CMF)](https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf). La lista exacta de campos, posición, tipo, unidad y etiqueta CMF está en `seguros/fuentes/inventario_1835.json` y en el Diccionario de Datos del sitio.

### Formato de publicación

Se mantiene Parquet como formato principal: el sitio ya consume directamente los Parquet con DuckDB-WASM y los manifiestos describen la cobertura por período. Un duplicado CSV/JSON aumentaría transferencia y almacenamiento y perdería tipado; un snapshot DuckDB o un formato de tabla transaccional (Delta/Iceberg) no aporta consultas incrementales adicionales en el uso estático actual. Se podrá añadir una exportación puntual si la demanda de usuarios la justifica, sin sustituir los Parquet.

## Operaciones REPO (pactos)

La tabla consultable es **`seguros_pactos`** (nombre lógico `seguros.pactos`), publicada por `seguros/scripts/actualizar_carteras.py` dentro del flujo incremental `seguros_carteras.yml`.

Incluye compras y ventas con pacto, fecha de operación y vencimiento, contraparte y datos del activo objeto. Campos principales:

- `tipo_operacion`, `folio_operacion`, `item_operacion`, `fecha_de_la_operacion`, `fecha_de_vencimiento_del_contrato`;
- `nombre` (contraparte), `nacionalidad`, `relacionado`;
- `activo_objeto`, `serie_activo_objeto`, `nro_rut_activo_objeto`;
- `tasa_pacto`, `valor_nominal`, `interes_devengado_del_pacto_m`, `valorizacion_de_pacto_a_la_fecha_de_cierre_m_clp` y `valor_de_mercado_a_la_fecha_de_informacion`.

**Unidades:** los campos terminados en `_m_clp` están en miles de pesos (M$); `valor_nominal` conserva la unidad/moneda reportada para el activo. El valor nominal no debe sumarse como si siempre fueran pesos.

## Cobertura revisada

Al 2026-10-07, el manifiesto contiene **11.153 filas** de pactos desde **2016-11** hasta **2026-08**; el último mes tiene **155 filas**. El workflow programado terminó correctamente el 2026-10-04; su diagnóstico no reportó problemas y no añadió un período nuevo. La fecha `updated_at` del manifiesto (2026-09-28) señala el último cambio de datos, no la última ejecución del flujo.

Archivos por año: `docs/outputs/seguros/pactos/AAAA.parquet`; cobertura detallada por período: `docs/outputs/seguros/pactos/manifest.json` y `docs/outputs/seguros/manifest.json`.

```sql
SELECT periodo,
       count(*) AS filas,
       count(DISTINCT rut_aseguradora) AS companias
FROM seguros_pactos
GROUP BY periodo
ORDER BY periodo DESC
LIMIT 12;
```

Para el estado comparado con fondos de inversión y la aclaración sobre fondos mutuos, ver [cobertura de REPO/pactos](../docs/notas/cobertura_repos_pactos_2026-10-07.md). Para la auditoría profunda de estos datos (cobertura, esquemas, RUT, fechas, cuadraturas, duplicados y maestro de entidades), ver [auditoría 2026-10-07](../docs/notas/auditoria_seguros_2026-10-07.md).

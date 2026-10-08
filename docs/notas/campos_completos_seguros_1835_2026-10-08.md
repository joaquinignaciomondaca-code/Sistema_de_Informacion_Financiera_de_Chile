# Seguros (Circular 1835): todos los campos de la ficha, con el nombre original de la CMF

**Fecha:** 2026-10-08 · **Alcance:** extractor de cartera de inversiones de seguros
(`seguros/scripts/`), diccionario de datos de la web y descargas de Excel.

## Qué se pidió y qué se hizo

1. **Publicar todos los campos** que define la fuente, no un subconjunto elegido.
2. **Usar los nombres originales** con que la CMF imprime cada campo en los anexos técnicos
   de la Circular 1835 (aceptando que eso rompa consultas sugeridas, ERD, diccionario y
   documentación heredados).
3. **Diccionario de datos en el Excel** de descarga: hoja 1 = datos, hoja 2 = diccionario.
   El CSV queda como estaba (decisión explícita).

## Cómo queda el extractor

```
fichas_tecnicas_1835/*.txt   (copia local de los anexos de la CMF)
        │
        │  seguros/scripts/inventario_1835.py  --escribir
        ▼
seguros/fuentes/inventario_1835.json      (todos los campos: posición, PICTURE, unidad, descripción)
        │
        ├── seguros/scripts/formato_1835.py ............ lo lee el lector (campos por registro)
        └── seguros/scripts/diccionario_1835.py ........ genera el diccionario publicado
                 ├── docs/js/diccionario_seguros.js .... hoja "Diccionario" del Excel
                 └── docs/js/data_dictionary.js ........ columnas de seguros en el Diccionario de Datos
```

- `formato_1835.py` ya no lleva tuplas escritas a mano: las posiciones y los nombres salen del
  inventario. `LARGO` sigue declarado a mano y las 30 combinaciones registro×formato cuadran.
- El inventario conserva la **descripción literal** de la ficha de la CMF, que es el texto que
  se publica en el diccionario.

## Reglas de nombres

- Nombre de la ficha en minúsculas: `NRO_RUT` → `nro_rut`, `PRES_BURSATIL` → `pres_bursatil`.
- **Unidad como sufijo** cuando la ficha la declara: `_m_clp` (miles de pesos), `_clp` (pesos),
  `_uf`, `_um` (unidad monetaria del instrumento). La unidad se toma de los dos formatos: si la
  ficha de 2016 la dice y la de 2024 no la repite, el sufijo se publica en ambas épocas.
- **Nombres repetidos en un registro:** el segundo lleva el sufijo de su uso
  (`activo_objeto_unidades`, `activo_objeto_valor_contable`, ...). Cuando el mismo nombre tiene
  sentidos distintos entre subtipos se separa: en los swaps (`p5`) `ACTIVO_OBJETO_POSICION_LARGA`
  es el nocional (numérico) y no el nombre del activo (texto, `p2`–`p4`), así que se publica
  como `activo_objeto_posicion_larga_nocional`.
- **No se publica:** relleno (`FILLER`), tipo de registro y dígito verificador suelto (el DV
  viaja con el RUT, `97.004.000-5`).

## Cobertura: antes y después (columnas publicadas por tabla)

| Tabla | Antes | Ahora |
|---|---:|---:|
| `seguros.renta_fija` | 23 | 105 |
| `seguros.acciones` | 18 | 56 |
| `seguros.fondos_mutuos` | 16 | 35 |
| `seguros.bienes_raices` | 19 | 56 |
| `seguros.extranjeros` | 17 | 112 |
| `seguros.derivados` | 26 | 73 |
| `seguros.pactos` | 21 | 30 |
| `seguros.control_inversiones` | 15 | 15 |

El conteo incluye las columnas que agrega el pipeline (`periodo`, `sector`,
`rut_aseguradora`, `nombre_aseguradora` y, en extranjeros y derivados, `tipo_registro`).

Los mayores saltos son dos: renta fija (la ficha de 2024 agregó clasificación, garantías,
custodia, calce, etc.) y extranjeros, donde **antes se descartaban por completo los registros
de bienes raíces en el extranjero (x4) y de filiales (x5)**: hoy se publican con
`tipo_registro = 'bienes_raices'` y `'filiales'`.

## Descargas

- **Excel:** dos hojas, `Datos` y `Diccionario`. La hoja `Diccionario` trae una fila por
  columna: nombre publicado, tipo, unidad, nombre en la ficha CMF, registro de origen, vigencia
  (hasta 2024-11 / desde 2024-12 / ambos) y la descripción de la ficha. La generación es en el
  navegador, desde `docs/js/diccionario_seguros.js` (archivo generado, no se edita a mano).
- **CSV:** sin cambios (sin hoja de diccionario).

## Verificación

- `python -m seguros.tests.test_formato_1835`: lee las muestras reales de ambos formatos
  (2016-10, 2016-11, 2024-11, 2024-12, 2026-08; vida y generales) y ahora **además escribe el
  Parquet** en una carpeta temporal, así el esquema (unión de formatos y subtipos) se prueba
  antes de publicar. Cuadratura de bonos 100 %, fechas válidas 100 %, exclusión de archivos
  defectuosos OK.
- 66 pruebas de `seguros` y `pipelines/auto` en verde; contrato de publicadores en verde.
- `scripts/audit_consultas_sugeridas.py`: 146/146 consultas ejecutan.

## Paso pendiente: recarga histórica

Los Parquet publicados conservan las columnas antiguas hasta que se vuelvan a descargar y
publicar los meses. Desde un entorno sin acceso a cmfchile.cl no se puede hacer; en GitHub
Actions sí:

* Se agregó `--forzar` al extractor (y el input `forzar` a `seguros_carteras.yml`): con
  `workflow_dispatch`, `forzar = true` y `desde = 2016-11`, el flujo vuelve a descargar y
  escribir todos los meses del rango.
* Hasta que esa recarga termine, `scripts/audit_web_full.py` acusará el desfase entre el
  diccionario (nombres nuevos) y el Parquet (nombres antiguos). Es esperable y se resuelve
  con la recarga, no con un cambio de código.

## Cómo replicar el patrón en otros sectores

1. Guardar la especificación de la fuente en texto dentro de `<sector>/fuentes/`.
2. Un `<sector>/scripts/inventario_<norma>.py` que la parseé y publique un JSON con todos los
   campos (posición, tipo, unidad, descripción).
3. El módulo de formato del sector lee ese JSON en vez de llevar tuplas a mano.
4. Un `<sector>/scripts/diccionario_<norma>.py` genera el diccionario para la web y para la
   hoja `Diccionario` del Excel (o la entrada sectorial equivalente en `docs/js/diccionario_*.js`).
5. La prueba del lector escribe Parquet en una carpeta temporal, para que el esquema completo
   se valide en CI.

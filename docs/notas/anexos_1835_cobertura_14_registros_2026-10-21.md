# Anexos técnicos 2024 (B.1–B.14): qué hay hoy en el repo y qué falta para publicarlos todos

**Fecha:** 2026-10-21 · **Alcance:** extractor de seguros (`seguros/scripts/`), inventario de
campos y publicación web/Parquet. Esta nota **no cambia código**: verifica la tabla de campos que
se pidió revisar y deja el diagnóstico y el plan.

## 1. De qué documento estamos hablando

La tabla y el enlace que llegaron (14 archivos, B.1 a B.14, con el "N° de campos" de cada registro
de detalle) **no son de una Circular 1845**: son los **Anexos Técnicos de la Circular 1835**,
versión vigente **desde el 01-12-2024** (dictada por la Circular 2354, de 30-07-2024, que trasladó
los anexos de la circular al módulo SEIL). En el repo no hay ninguna referencia a una Circular
1845 (búsqueda en todo el árbol, incluido `data/normativa_cmf/`): el anexo copiado y el que usa el
extractor es el de la 1835.

Copia local usada para todo lo que sigue:

```
seguros/fuentes/fichas_tecnicas_1835/Anexos_Tecnicos_Circular_N1835.txt   (11.461 líneas, v2024)
seguros/fuentes/fichas_tecnicas_1835/B.*.txt                              (fichas sueltas v2016)
```

El anexo completo **ya trae B.6 y B.9–B.14**; las fichas sueltas, en cambio, solo cubren
B.1–B.5, B.7 y B.8. Eso es lo que hoy marca el alcance del inventario y, por lo tanto, de las
tablas publicadas.

## 2. Verificación de la tabla de campos

Conté los campos de cada registro de detalle (tipo 2…6) directamente del anexo local, aceptando la
misma convención que usa la tabla de la CMF: **incluye el campo `TIPO` y no cuenta los `FILLER`**.

| Registro | Archivo | Campos según la tabla | Contados en la copia local | Largo del registro | Estado |
|---|---|---:|---:|---:|---|
| B.1 Renta fija | `IaammddG` | 107 | **107** | 970 | publicado |
| B.2 Acciones SA y cuotas FI | `AaammddG` | 56 | **56** | 572 | publicado |
| B.3 Cuotas de fondos mutuos | `FaammddG` | 34 | **34** | 361 | publicado |
| B.4 Bienes raíces | `BaammddG` | 53 | **53** | 506 | publicado |
| B.5 Extranjero · deuda | `XaammddG` | 50 | **50** | 611 | publicado |
| B.5 · acciones y cuotas | ídem | 54 | **54** | 611 | publicado |
| B.5 · bienes raíces | ídem | 41 | **41** | 611 | publicado |
| B.5 · filiales | ídem | 15 | **15** | 611 | publicado |
| B.6 Otras inversiones | `OaammddG` | 31 | **31** | 510 | **falta** |
| B.7 · opciones | `PaammddG` | 41 | **41** | 587 | publicado |
| B.7 · forwards | ídem | 44 | **44** | 587 | publicado |
| B.7 · futuros | ídem | 42 | **42** | 587 | publicado |
| B.7 · swaps | ídem | 49 | **49** | 587 | publicado |
| B.7 · pactos | ídem | 28 | **28** | 587 | publicado |
| B.8 Información de control | `CaammddG` | 12 | **12** | 138 | publicado |
| B.9 Tablas de descriptores | `DaammddG` | 18 | **18** | 108 | **falta** |
| B.10 Tablas de desarrollo | `TaammddG` | 9 | **9** | 80 | **falta** |
| B.11 Flujos de activos elegibles | `EaammddG` | 14 | **14** | 178 | **falta** |
| B.12 Préstamos | `RaammddG` | 78 | **69** ❌ | 658 (declarado) | **falta y no se puede leer** |
| B.13 Bienes raíces en arriendo y morosidad | `VaammddG` | 39 | **39** | 443 | **falta** |
| B.14 Garantías en derivados | `GaammddG` | 22 | **22** | 300 | **falta** |

**20 de 21 registros coinciden exactamente.** La única excepción es B.12 y no es un error de
conteo: a la copia local del anexo le faltan campos (ver §4).

La suma de los largos de cada registro cuadra con el largo del registro tipo 1 y tipo 3 del mismo
archivo en **todos** los casos salvo B.12. Esa es la validación fuerte de que las posiciones están
bien: si un campo falta o se cuela uno de más, la suma deja de cuadrar.

## 3. Qué publicamos hoy

Ocho tablas (14 registros de detalle, 7 archivos), desde 2016-11; renta fija y bienes raíces desde
2024-12 por tamaño. Último mes publicado: **2026-09** (119 períodos en el manifiesto).

| Tabla | Registros | Columnas publicadas |
|---|---|---:|
| `seguros.renta_fija` | B.1 · tipo 2 | 105 |
| `seguros.acciones` | B.2 · tipo 2 | 56 |
| `seguros.fondos_mutuos` | B.3 · tipo 2 | 35 |
| `seguros.bienes_raices` | B.4 · tipo 2 | 56 |
| `seguros.extranjeros` | B.5 · tipos 2–5 | 112 |
| `seguros.derivados` | B.7 · tipos 2–5 | 73 |
| `seguros.pactos` | B.7 · tipo 6 | 30 |
| `seguros.control_inversiones` | B.8 · tipo 2 | 15 |

(Las columnas incluyen las que agrega el pipeline: `periodo`, `sector`, `rut_aseguradora`,
`nombre_aseguradora` y, donde corresponde, `tipo_registro`.)

**Faltan 7 archivos / 7 registros: B.6, B.9, B.10, B.11, B.12, B.13 y B.14**, con 211 campos
declarados en total. De esos 211, la copia local permite ubicar **202** (posición y PICTURE) y de
ellos **170 tienen nombre**; quedan **32 nombres perdidos** (27 en B.12, 4 en B.13 y 1 en B.14) y
**9 campos de B.12** que directamente no están en el texto.

## 4. Qué se puede hacer ya y qué bloquea

### B.6 Otras inversiones (`o2`, 31 campos, 510 caracteres) — legible
Saldos en cuenta corriente, caja, inversiones mobiliarias (equipos, muebles, vehículos), avances a
tenedores, préstamos y otras inversiones. La suma cuadra (510 = tipo 1 = tipo 3) y no hay
`SIN_NOMBRE`.

Dos cosas a resolver al implementarlo:
- la maqueta parte varios nombres (`METOD_CLASIF_VALO`, `CRITERIO_VALORIZAC`, `MODELO_VALORACIO`,
  `MODELO_PROPIO_DE_TERIORO`, `CLASIFICACION_DE_RI`, `ACTIVO_EN_MARGEN_O_SUJETO_A`): se reparan con
  las tablas `REPARAR`/`PARES` que ya existen para B.5, porque son los mismos campos;
- **no hay ficha v2016 en el repo** para el archivo O. Se puede publicar desde 2024-12 sin más, o
  conseguir el anexo anterior si se quiere la serie completa (el archivo O existe desde antes).

### B.9, B.10 y B.11 — legibles y sin nombres perdidos
- **B.9 Tablas de descriptores** (`d2`, 18 campos, 108): RUT y nemotécnico del emisor, tipo de
  instrumento, fecha y tasas de emisión/descuento, `TRATAMIENTO`, `NRO_FLUJOS`,
  `MESES_ENTRE_VENCIMIENTO`, `TIPO_INTERES`, `TIPO_NOMINALES`, `OPCION_PREPAGO`, `FECHA_OPCION`,
  `PLAZO_GRACIA`.
- **B.10 Tablas de desarrollo** (`t2`, 9 campos, 80): cupones por instrumento (`NRO_CUPON`,
  `FECHA_VCTO_CUPON`, `INTERES`, `AMORTIZACION`, `SALDO_INSOLUTO`).
- **B.11 Flujos de activos elegibles** (`e2`, 14 campos, 178): `CIRCULAR_APLICADA`,
  `TIPO_DE_INFORMACION`, `TIPO_INSTRUMENTO` y `TRAMO_1`…`TRAMO_10`.

Los tres suman exacto contra su registro tipo 1. Son tablas "de apoyo" (descriptores y flujos), no
cartera instrumento por instrumento: conviene decidir el nombre lógico (`seguros.tablas_descriptores`,
`seguros.tablas_desarrollo`, `seguros.flujos_activos_elegibles`) antes de escribirlas.

### B.13 Bienes raíces en arriendo y morosidad (`v2`, 39 campos, 443) — legible con 4 nombres perdidos
La suma cuadra (443) y hay 35 nombres recuperados: `TIPO_INSTRUMENTO`, `ROL`, `COMUNA`, nombre/RUT/DV
del arrendatario-deudor, morosidad por tramos, provisión de incobrabilidad, m² disponibles y no
arrendados, valor m², deuda por capital e intereses. Faltan **4 nombres** en la copia de texto (la
posición y el PICTURE sí están):

| Pos. | Largo | PICTURE | Pista en la descripción |
|---:|---:|---|---|
| 103 | 6 | `9(06)` | "…para la actividad económica principal del arrendatario" |
| 119 | 30 | `X(30)` | sin descripción (vecino de `COMUNA`: probable dirección) |
| 201 | 12 | `9(12)` | sin descripción (bloque de facturación/morosidad) |
| 383 | 7 | `9(07)` | sin descripción (entre m² disponibles y m² no arrendados) |

Además hay nombres truncados por la maqueta (`DIAS_Y_MENOR_A_1_A_NO`, `1_ANO_Y_MENOR_A_2_A_NOS`,
`TOTAL_M2_DISPONIBLESARRIENDO`, `DEUDA_CAPITAL_INTERESES_DEVENGADOS_UM`). **No conviene inventar los
4 nombres**: el repo publica el nombre original de la CMF y ese es el contrato de la tabla.

Privacidad: esta tabla trae `ROL`, `COMUNA`, y nombre + RUT del arrendatario/deudor (que puede ser
persona natural). Hoy `seguros.bienes_raices` **retira `rol` y la dirección** y agrega `property_id`
(`pipelines/auto/privacidad.py`); acá habría que aplicar el mismo criterio y decidir qué se hace con
el RUT del deudor.

### B.14 Garantías de derivados (`g2`, 22 campos, 300) — legible con 1 nombre perdido
Suma exacta (300). Campos: contraparte (RUT/DV nacional o LEI extranjera), nacionalidad, relación,
posición de la compañía (constituye/recibe), `TIPO_GARANTIA`, tipo de activo en garantía, folio e
ítem del instrumento, valor nominal, identificador (ISIN), clasificación de riesgo país, valores
contable y razonable en UM y M$, y cuenta de los EEFF. Falta **1 nombre** (pos. 139, `X(14)`, entre
`TIPO_GARANTIA` y `TIPO_ACTIVO_EN_GARANTIA`). Hay nombres truncados
(`NOMBRE_CONTRAPARTEGARANTIA`, `ITEM_INSTRUMENTO_ENGARANTIA`, `CODIGO_IDENTIFICACIORANTIA`,
`N_ACTIVO_EN_GARANTI`) y un PICTURE mal impreso (`X(4)` en `CLASIFICACION_DE_RIESGO_PAIS`, que
debería ser `X(04)`; el largo 4 es correcto).

### B.12 Préstamos (`r2`, 78 campos, 658) — bloqueado
Es el registro grande y el único que **no se puede reconstruir** con la copia local:

- el texto trae 69 campos y suma **589** caracteres; el registro tipo 1 dice **658** → faltan
  **9 campos (69 caracteres)**;
- **27 campos quedaron sin nombre** (`SIN_NOMBRE`): el conversor de PDF se comió la columna del
  nombre en ese tramo (posiciones 1, 10, 30, 39, 49, 230, 250, 270, 271, 283, 284, 285, 295, 313,
  331, 332, 335, 340, 341, 432, 434, 439, 442, 470, 471, 472, 473);
- varios nombres llegaron cortados: `R` (pos. 50, `X(100)`, es `RAZON_SOCIAL_DEUDOR`), `CUOTAS_`,
  `SALDO_INSOLUTO_`, `VER_VENDEDORA_PRES_TAMO`, `ORGADO`, etc.

Lo que sí está identificado y sirve de punto de partida: `TIPO`, `CODIGO_PRESTAMO`,
`FECHA_PRESTAMO`, `FECHA_VENCIMIENTO`, `TIPO_DEUDOR`, `CODIGO_ACTIVIDAD_ECONOMICA`,
`PRESTAMOS_TRABAJADORES`, `CLASE_DEUDOR`, `RUT_DEUDOR`, `VER_DEUDOR`, `NOMBRE_DEUDOR`, `PENSIONADO`,
`DESCUENTO_PENSION`, `MONTO_PENSION`, `PRESTAMO_REPRESENTATIVO`, `ORIGEN_PRESTAMO`,
`FECHA_ORIGINACION_O_RENEGOCIACION_ANTERIOR`, `CODIGO_RENEGOCIADO` (×3),
`RUT_VENDEDORA_PRESTAMO`, `VER_VENDEDORA_PRESTAMO`, `CATEGORIA_RIESGO_VENDEDOR`,
`PORCENTAJE_PROVISION_VENDEDOR`, `CATEGORIA_RIESGO_ADQUIRIDO`, `PORCENTAJE_PROVISION_ADQUIRIDO`,
`CATEGORIA_RIESGO_OTORGADO`, `PORCENTAJE_PROVISION_OTORGADO`, `VENDEDORA_RELACIONADA`,
`CODIGO_PRESTAMO_ADQUIRIDO`, `UNIDAD_REAJUSTE`, `CUOTAS_IMPAGAS (UM/M$)`,
`SALDO_INSOLUTO_DEUDA (UM/M$)`, `MONTO`, `MONTO_PESOS`, `CUOTA`, `PERIODO_PAGO_CUOTA`, `GARANTIAS`,
`PLAZO_PRESTAMO`, `PLAZO_GRACIA`, `TIPO_TASA`, `TASA_FIJA_PACTADA`, `TASA_FIJA_EFECTIVA`,
`TASA_VARIABLE_BASE`, `SPREAD_TASA_VARIABLE`, `VALOR_FINAL`, `MONTO_PROVISION`,
`MODELO_DETERIORO`, `MOROSIDAD`, `TIPO_TASA_MORA`, `COMISION_PREPAGO`, `OTRO_PREPAGO`,
`SEG_DESGRAVAMEN`, `SEG_INVALIDEZ`, `SEG_CESANTIA`, `SEG_INCENDIO`, `SEG_TERREMOTO`, `SEG_OTRO` y
los pares `RUT_ASEG_*`/`DV_ASEG_*`.

**Conclusión:** para B.12 hay que volver a bajar el PDF de la CMF y convertirlo (o la ficha suelta
`B.12_Prestamos.pdf`). Reparar a mano no sirve: la mitad del valor de estas tablas es que el nombre
de la columna sea el de la ficha.

## 5. Bloqueos del entorno

1. **Sin red a `cmfchile.cl` desde este sandbox**: `curl https://www.cmfchile.cl/` falla con
   `OpenSSL SSL_connect: SSL_ERROR_SYSCALL`. Por eso no se pueden bajar ni los PDF de las fichas ni
   un ZIP mensual de muestra.
2. **GitHub Actions sí tiene red** (es de donde salen los Parquet publicados) y las dependencias de
   PDF ya están en `requirements.txt` (`PyMuPDF`, `pdfplumber`). Un paso de descarga + conversión de
   los anexos en el flujo resuelve B.12, B.13 y B.14 sin depender del sandbox.
3. **No hay muestras de los archivos nuevos**: `seguros/fuentes/muestras_1835/` solo tiene
   `a, b, c, f, i, p, x`. Sin una muestra de `O/D/T/E/R/V/G` la validación "largo de línea == largo
   de ficha" solo puede correr en Actions (o con un ZIP que se suba al repo).
4. **Falta confirmar que la CMF publique esos archivos en la descarga pública**. B.9–B.14 existen
   desde 2024-12; B.6 desde antes. Si el ZIP de cartera no los incluye, las tablas quedarían vacías
   y hay que revisar de dónde se bajan. Se puede verificar en la primera corrida contando archivos
   por letra.

## 6. Qué habría que tocar para publicarlas

Checklist por archivo (mismo patrón que se usó al ampliar B.1–B.8):

| Archivo | Cambio |
|---|---|
| `seguros/scripts/ficha_1835.py` | `LETRA`: agregar 6→`o`, 9→`d`, 10→`t`, 11→`e`, 12→`r`, 13→`v`, 14→`g`; `FICHA["v2024"]` con esas letras |
| `seguros/scripts/inventario_1835.py` | `DESTINO` para los 7 registros nuevos; `REPARAR`/`PARES` para los nombres truncados; `ALIAS` para nombres repetidos (`CODIGO_RENEGOCIADO` ×3, `CUOTAS_IMPAGAS (UM)/(M$)`, etc.) |
| `seguros/fuentes/inventario_1835.json` | regenerar con `python -m seguros.scripts.inventario_1835 --escribir` |
| `seguros/scripts/formato_1835.py` | `LARGO["v2024"]` para las letras nuevas (510, 108, 80, 178, 658, 443, 300) y `TIPO_TOTAL` |
| `seguros/scripts/actualizar_carteras.py` | `ARCHIVOS`, `TABLAS`, `DESDE_TABLA` (2024-12), `POR_MES`/`ORDEN`, privacidad de B.13 |
| `seguros/scripts/metadatos_web.py` | descripción de cada tabla nueva |
| `seguros/scripts/diccionario_1835.py` | genera `docs/js/diccionario_seguros.js` y las columnas de `docs/js/data_dictionary.js` |
| web | `docs/js/duckdb_client.js`, `sidebar.js`, `data_viewer.js`, `erd_graph.js` y `scripts/build_download_catalog.py` |
| pruebas | `seguros/tests/test_formato_1835.py` (con muestras), `scripts/audit_consultas_sugeridas.py`, `scripts/audit_web_full.py` |
| documentación | `seguros/README.md`, esta nota y `data_manifest.json` regenerado |

## 7. Orden propuesto

1. Conseguir las fichas autorizadas de B.12/B.13/B.14 (script de descarga + conversión en CI, o los
   PDF a mano) y regenerar el inventario. Sin eso, B.12 no se puede empezar.
2. Publicar **B.6, B.9, B.10 y B.11** (limpias) con `DESDE = 2024-12`.
3. Publicar **B.13 y B.14** una vez recuperados los 5 nombres, definiendo antes la política de
   privacidad de B.13 (rol, dirección y RUT del deudor).
4. Dejar **B.12** al final: es la más grande y la única que exige rehacer la ficha completa.

## 8. Preguntas abiertas

- ¿"1845" es otra norma distinta de la 1835, o es un lapsus por el nombre del PDF?
  Si es otra, decime cuál y la busco aparte.
- ¿Se publican B.12 y B.13 con RUT y nombre de deudores/arrendatarios, o se aplican los mismos
  criterios de privacidad que ya usa `bienes_raices` y `fi.cartera_nacional`?
- ¿Alcanza con publicar desde 2024-12, o se quiere buscar el anexo anterior para la serie histórica
  de B.6?

---

### Cómo se verificó

```python
from seguros.scripts import ficha_1835 as F
F.LETRA.update({"6": "o", "9": "d", "10": "t", "11": "e", "12": "r", "13": "v", "14": "g"})
regs = F.parsear(F.FUENTES / "Anexos_Tecnicos_Circular_N1835.txt")
# campos por registro, suma de largos y campos SIN_NOMBRE
for clave, r in sorted(regs.items()):
    print(clave, len(r.campos), r.total, sum(c.nombre == "SIN_NOMBRE" for c in r.campos))
```

`LETRA` hoy solo mapea 1–8; por eso el inventario publicado no ve B.6 ni B.9–B.14 aunque estén en el
texto. La comparación con la tabla de la CMF se hizo sobre el conteo que incluye `TIPO` y excluye
`FILLER`; con esa regla coinciden 20 de 21 registros y B.12 queda corto en 9 campos y 69 caracteres.

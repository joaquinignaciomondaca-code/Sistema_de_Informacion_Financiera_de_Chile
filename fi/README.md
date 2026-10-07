# Fondos de Inversión (CMF — Ley Única de Fondos)

Dos flujos **independientes** para fondos públicos rescatables (`FIRES`) y no rescatables
(`FINRE`), incluidos vigentes y no vigentes. No equivalen a un censo de fondos privados no
reportantes a la CMF.

| Flujo | Fuente | Código / workflow | Salida |
|---|---|---|---|
| Carteras y pactos | Informes HTML IFRS por fondo/trimestre | `scripts/actualizar_carteras.py` · `fi_carteras.yml` | Siete carteras/pactos y maestro |
| **Balance y resultados** | **XML IFRS `FIEF`**, Circular 1998, enlazado en la ficha | `scripts/actualizar_eeff.py`, `eeff_xml.py`, `cotejo_eeff.py` · **`fi_eeff.yml`** | **`fi_balance/` y `fi_resultados/`** |

## Balance y estado de resultados

### Publicación y backfill (estado al 2026-10-04)

El cierre más reciente publicado es **2026-06**: censo local de **1.679** RUN; **908** fondos
con estados, **765** con ausencia explícita de información y **6** excluidos (5 negativas de
descarga CMF, 1 moneda COP no expuesta en la ficha HTML). Para junio:

- Balance: **66.864 filas**; resultados: **97.860 filas**.
- Auditoría: **35.570 identidades**, cero fallas en la salida.
- Contextos excluidos con motivo: 253 de balance y 135 de resultados. No implican descartar
  el actual válido del fondo, ni se rellenan sus importes.

Desde la publicación inicial del 2026-10-01 se completó un backfill **parcial**: hay **16 cierres
publicados entre 2022-03 y 2026-06**, con **985.908 filas de balance** y **1.164.000 de resultados**.
No se publica una serie continua: faltan los cierres **2023-06** y **2025-03**, además de la
historia anterior a 2022. El intento programado del 2026-10-04 no completó el backfill: la CMF
rechazó 175 de 782 descargas XML de 2023-06 (`ACCION NO PERMITIDA 16`); en 2025-03 quedaron
3 rechazos y 1 envío pendiente. Las compuertas conservaron los períodos válidos ya publicados.

Los metadatos detallan cada exclusión y la fuente/hash de cada documento aceptado. La revisión de
cobertura del 2026-10-01 sigue describiendo el padrón y la evidencia disponibles a esa fecha;
no debe confundirse con el estado del backfill aquí actualizado.


### Revisión de cobertura: rescatables y no rescatables (2026-10-01)

La primera publicación contiene **142 FIRES** y **766 FINRE**: no se omite una categoría.
De los 765 RUN sin envío de junio, **679** figuran como no vigentes en la copia local y
**86** como vigentes. En estos últimos, la identificación CMF declara inicio posterior
al cierre para **31**, no informa fecha de inicio para **48** y muestra **7** en liquidación.
Una fecha vacía no demuestra que el fondo nunca haya operado, ni la liquidación prueba
por sí sola una exención de reportar.

Se contrastaron las cuatro listas oficiales y **768** casos (765 ausencias más 3 altas
fuera de la copia local), consultando **ambos tipos** y **VI/NV** cuando corresponde.
**Ningún enlace FIEF de junio se recupera cambiando el tipo o la vigencia.** El registro
oficial observado contiene **1.682 RUN únicos** en 1.683 filas: el RUN 9251 aparece en VI
y NV simultáneamente, sin cambiar de categoría. El diagnóstico conserva esa ambigüedad
sin duplicar el fondo ni inventarle una vigencia.

**Padrón local pendiente de actualización:** falta incorporar los RUN **10926** (AMERIS
Dover Street XII), **10927** (Neorentas Diecinueve) y **10928** (Principal BC XII), todos
FINRE. Sus fichas tampoco muestran EEFF para junio; incorporarlos al maestro no significa
crear tres balances de cero. El censo publicado de 1.679 corresponde a la copia local
anterior a estas altas, no se presenta como el registro CMF actualizado.

Se corrigió además la consulta de los no vigentes: el extractor usa `vig=NV` según el
padrón, en lugar de pedir siempre `VI`; los cambios de tipo/vigencia invalidan la caché
pertinente. En la muestra revisada esto corrige la identificación de la ficha, **no añade
importes ni recupera nuevos estados de junio**. Los datos ya publicados se mantienen.

Informe y evidencia por RUN, URL, fecha y SHA-256:
[`revisión de cobertura`](../docs/notas/revision_cobertura_fi_2026-10-01.md) y
[`JSON de evidencia`](../docs/notas/revision_cobertura_fi_2026-10-01.json).
Las cuatro listas originales comprimidas y sus hashes quedan como fixtures de regresión.

```bash
python -m fi.scripts.revisar_cobertura_eeff                  # cruce local, sin red
python -m fi.scripts.revisar_cobertura_eeff --red            # listas y ausencias en ambos tipos
python -m fi.scripts.revisar_cobertura_eeff --red --reanudar # solo reusa respuestas con hash válido
```

El workflow de revisión es **de solo lectura**, sin horario ni permisos de publicación.
La corrección de `vig` tiene pruebas de conservación/caché; el conjunto FI suma **97**
pruebas, y la batería unitaria del repositorio comprobada suma **440**.

### Fuente verificada

Cada ficha CMF (`entidad.php?tipoentidad=FIRES|FINRE&pestania=29&mm=MM&aa=AAAA&tipo=I&tipo_norma=IFRS`)
enlaza el XML `FIEF…` en `/web/ifrs_xml/fiifr/xml/`. No se adivina su correlativo: se lee el
nombre de la ficha. La extracción es determinista, sin OCR ni modelo de lenguaje.

Se descargaron **ocho XML originales con sus fichas** desde Actions el 2026-10-01, incluyendo
2010-12, 2011-03, 2021-12, 2025-12 y 2026-06, FIRES/FINRE, pesos y dólares. Los fixtures de
`tests/fixtures/` conservan bytes originales y SHA-256. Las **303 identidades evaluables** de
los contextos admitidos y su cotejo numérico se prueban sin red. Es una muestra de formato y
lectura, no certifica por sí sola toda la industria.

El modelo tiene **42 cuentas de balance** y **30 de resultados integrales** por contexto:
activos corrientes/no corrientes, pasivos corrientes/no corrientes, patrimonio; ingresos,
gastos, utilidad antes de impuesto, resultado y otros resultados integrales.

**Importante:** `TotalPasivo` de FI **incluye patrimonio**, como lo presenta la ficha CMF:

```text
TotalActivo = TotalPasivo
TotalPasivo = TotalPasivoCorriente + TotalPasivoNoCorriente + TotalPatrimonioNeto
```

No aplicar la fórmula de fondos mutuos usando ese `TotalPasivo` como pasivo exigible.

### Contextos separados, sin dobles sumas

Se publica una fila por **archivo/cierre + RUN + contexto + cuenta**, en formato largo.
`periodo` identifica el cierre del archivo; las fechas de la cifra están en
`fecha_inicio_contexto` y `fecha_fin_contexto`.

| Contexto | Balance | Resultados |
|---|---|---|
| `PeriodoActual` | Saldo al cierre pedido | Acumulado del ejercicio al cierre |
| `PeriodoAnualAnterior` | Comparativo al diciembre anterior | — |
| `PeriodoAnterior` | — | Acumulado comparable del ejercicio anterior |
| `TrimestreActual` | — | Solo el trimestre, si lo informa el XML |
| `TrimestreAnterior` | — | Trimestre comparable del año anterior |
| `SaldoInicialTerceraColumna` | Saldo de apertura IFRS cuando se informa | — |

Las cifras son **enteros exactos en miles de la moneda de presentación**: `moneda_cmf`
conserva `$$`, `PROM`, `EUR` o `COP`; `moneda` expone CLP, USD, EUR o COP. No se convierte,
redondea, cambia el signo ni rellena con cero. Los gastos conservan su signo de fuente.

No sumar contextos, monedas, detalles y totales. Tampoco interpretar un trimestre informado
con ceros como un importe faltante, ni derivarlo automáticamente del acumulado. Las cifras
XML y las columnas que la ficha no muestra quedan diferenciadas por `cotejo_ficha`.

### Validación antes de publicar

1. RUN, período, fechas de cada contexto, moneda y banderas de estados presentes.
2. Catálogo completo por contexto. Duplicados idénticos no duplican filas; valores distintos
   para la misma cuenta/contexto rechazan el documento.
3. **Ocho identidades de balance**: sumas de detalles, subtotales, patrimonio y total.
4. **Siete identidades de resultados**: ingresos, gastos, operación, costos financieros,
   impuestos, otros resultados integrales y resultado integral.
5. Cotejo exacto XML ↔ ficha **por concepto y columna**, no por coincidencia en cualquier
   celda. El actual siempre debe estar cotejado. Un contexto no expuesto en HTML se marca
   `sin_columna` y solo se publica si valida internamente.
6. Completitud del cierre: cada fondo del registro debe estar resuelto (`ok`, ausencia
   declarada o rechazo explícito). Un desafío/corte/JSON de error sigue pendiente, nunca
   equivale a ausencia. Más del 2 % de envíos con XML conocidos rechazados bloquea la publicación.
   Una negativa explícita `ACCION NO PERMITIDA` se registra como exclusión de descarga
   (no como ausencia), sin buscar rutas que eludan la negativa de acceso.
7. Auditoría de la salida completa, incluidos comparativos, claves, cobertura igual entre
   balance y resultados actuales, conteos y hashes de Parquet, antes de habilitar el push.

Tolerancia contable: ±2 miles de la moneda o 1 millonésima del importe esperado, lo mayor,
para cuentas redondeadas en la fuente. El cotejo con HTML exige igualdad exacta.

**Contextos adicionales defectuosos:** en dos muestras reales la fuente omite una cuenta del balance
comparativo. No se fabrica un cero ni se traslada otra cuenta de contexto. Se excluye ese
contexto y su motivo aparece en `manifest.json` y `fi_eeff_control.json`; el actual completo
puede publicarse. Los trimestres con importes incorrectos o sin fechas declaradas también se excluyen: no se
infiere un rango de fechas ni se publica un trimestre que no cuadra. El balance y el
acumulado de PeriodoActual deben estar completos y cotejados. Si una reedición pierde un contexto previamente validado, se conserva
**todo el documento anterior** con su archivo/hash y se registra la actualización rechazada.
También se conserva ante una fuente desaparecida o una falla de red. No se mezclan cifras de
dos envíos dentro de un documento para disimular una pérdida.

Este cotejo confirma la lectura y la presentación del envío CMF. **No es una auditoría
independiente contra el PDF firmado.**

### Incremental e historia

- Ventana predeterminada desde **2010-12** (pro forma verificado); modificable con `--desde`.
- Último cierre admisible: espera 75 días tras marzo/junio/septiembre y 100 tras diciembre,
  igual al criterio prudente de carteras. No presenta un cierre reciente sin información
  como un estado vacío.
- No se usa la vida observada en carteras como vida legal: también se consultan fondos sin
  cartera o cuyo estado financiero puede existir fuera de esa ventana.
- Avanza desde el cierre más reciente hacia la historia, publicando cada trimestre completo
  por separado. No presenta el rango como una serie contigua hasta terminar el backfill:
  los cierres efectivamente publicados están en los manifiestos.
- Revisa siempre los dos últimos cierres y 1/36 de la historia por corrida. Un nuevo nombre
  de XML señala un reenvío. `--refrescar-todo` relee también el contenido con el mismo nombre.
- Progreso comprimido y verificado en `.local-data/fi_eeff/`, fuera de Git. La caché de Actions
  lo conserva; si se pierde, se reconstruye desde los Parquet/control publicados.
- `fi_eeff.yml` ejecuta pruebas y cotejo de muestra antes de descargar, y audita los Parquet
  antes del commit/push. `always()` se reserva para recuperación y diagnóstico, no elude
  una auditoría fallida.

**Horario:** días 5, 15 y 25. La programación solo se activa cuando el workflow está en la
rama predeterminada. En ramas de trabajo un push normal solo prueba; `workflow_dispatch`
permite cargar una ventana explícita. Un commit marcado `[fi-carga-inicial]` habilita una
primera carga acotada de un único cierre reciente (45 minutos), siempre en esa misma rama,
con las mismas compuertas.

### Archivos y vistas

```text
docs/outputs/fi/fi_balance/AAAA-MM.parquet       + manifest.json
docs/outputs/fi/fi_resultados/AAAA-MM.parquet    + manifest.json
docs/outputs/fi/fi_eeff_control.json
```

25 columnas: `periodo`, `run_fondo`, `run_fondo_dv`, `dv_fondo_fuente`, `nombre_fondo`,
`tipo_entidad`, `rut_agf`, `razon_social_agf`, `moneda`, `moneda_cmf`, `contexto`,
`fecha_inicio_contexto`, `fecha_fin_contexto`, `tipo_periodo`, `seccion`, `tipo_linea`,
`orden`, `codigo_cuenta`, `cuenta`, `nota`, `valor_miles_mf`, `fuente_archivo`,
`enviado_cmf`, `sha256_archivo`, `cotejo_ficha`.

El publicador registra **`fi.balance` / `fi_balance`** y **`fi.resultados` / `fi_resultados`**
solo después del primer cierre validado: dos carpetas separadas en el explorador, visor,
diccionario, mapa relacional y catálogo de descargas. Los catálogos compartidos se regeneran
sobre la cabeza vigente de la rama, separados del commit de datos.

### Probar y ejecutar

```bash
python -m unittest discover -s fi/tests -v
python -m fi.scripts.validar_fuente_eeff             # cotejo real, staging; requiere red CMF
python -m fi.scripts.actualizar_eeff --max-periodos 1 --sin-publicar
python -m fi.scripts.actualizar_eeff                 # carga reanudable, 270 min
python -m fi.scripts.actualizar_eeff --desde 2026-06 --hasta 2026-06
python -m fi.scripts.auditar_eeff                    # toda la salida publicada, sin red
python -m fi.scripts.actualizar_eeff --solo-catalogos # desde los datos ya publicados
python scripts/build_download_catalog.py
```

Ejemplo SQL seguro, sin contar comparativos ni otros contextos:

```sql
SELECT periodo, run_fondo, nombre_fondo, valor_miles_mf AS patrimonio_miles_clp
FROM fi_balance
WHERE contexto = 'PeriodoActual'
  AND codigo_cuenta = 'TotalPatrimonioNeto'
  AND moneda = 'CLP'
ORDER BY periodo DESC, patrimonio_miles_clp DESC;
```

## Carteras y pactos (estado al 2026-10-07)

La CMF no publica un archivo masivo de carteras FI: cada fondo tiene, por trimestre, una
página por tipo de cartera y otra de pactos. `scripts/actualizar_carteras.py` las recorre.

- **`fi_pactos`** reúne operaciones VRC (venta con compromiso de retrocompra) y CRV (compra con
  compromiso de retroventa). El manifiesto registra **1.716 filas** en **58 cierres con operaciones**,
  desde **2012-03** hasta **2026-06**; junio de 2026 aporta **40 filas**. El primer cierre con filas
  reales apareció al consultar el registro completo, no al extrapolar períodos de un fondo aislado.
- El barrido histórico exclusivo de pactos cubrió **2008-03–2019-12**, los **48 cierres** y los
  **1.683 RUN** devueltos por el registro CMF. Los 48 cierres quedaron parseados; **32** tuvieron
  operaciones (**939 filas**) y **16** no devolvieron operaciones reales. Se excluyeron **107 filas
  centinela** de relleno y no se fabricaron filas cero. `pactos/historico_control.json` conserva el
  resultado y las huellas SHA-256 por cierre; `periodos_sondeados` distingue la consulta completa
  de los 58 períodos que sí tienen filas.
- El backfill de Actions (2026-10-07) terminó correctamente; el cierre 2026-09 aún está dentro del
  plazo de presentación y no se espera todavía.
- **Cautela móvil:** para análisis, se recomienda tratar siempre los dos cierres trimestrales más
  recientes de `fi_pactos` como cautelares por posible rezago de carga de la fuente CMF. Hoy son
  **2026-03** y **2026-06**. Los registros se conservan, pero no se consideran definitivos para
  comparaciones concluyentes; al publicarse un trimestre nuevo, la ventana se desplaza al nuevo par.
  Es una precaución por posible falta de carga, no un fallo del extractor.
- El workflow es incremental; valida encabezados, cuadratura contra la fila TOTAL, legibilidad y
  cobertura respecto al trimestre anterior. Los importes `*_miles_mf` están en miles de la moneda
  funcional de cada fondo y no se deben sumar entre monedas sin conversión.
- Salidas: `cartera_nacional/`, `cartera_extranjera/`, `metodo_participacion/`, `bienes_raices/`,
  `futuros_forwards/`, `opciones/`, `pactos/`, `maestro_fondos_inversion.parquet` y
  `fi_registro_fondos_universo.json`.
- Vistas: `fi_lista_entidades`, `fi_cartera_nacional`, `fi_cartera_extranjera`,
  `fi_metodo_participacion`, `fi_bienes_raices`, `fi_futuros`, `fi_opciones`, `fi_pactos`.

Los extractores/REPO antiguos (`cartera_inversiones/`, `repos/`, scripts 01–04) se retiraron el
2026-09-28; la cartera actual y `fi_pactos` se alimentan del flujo IFRS vigente. Para comparar
con seguros y ver por qué FFMM no tiene una tabla específica, consulta
[la nota de cobertura REPO](../docs/notas/cobertura_repos_pactos_2026-10-07.md).

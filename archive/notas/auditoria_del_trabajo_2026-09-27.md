# Auditoría del trabajo de la sesión (2026-09-27)

Objeto auditado: **mis propios cambios** de la sesión en la rama
`arena/01a0e08b-monitor-financiero-chile` (commits `5a72440`, `78cb876`, `7f22974`,
`5599f90`, `5797da8`, `6d0756d` y las correcciones de este mismo día).
No es una auditoría de los datos históricos de terceros ni una certificación externa.

Método: recalcular las afirmaciones con código (no de memoria), contar referencias en el
repositorio, validar YAML, correr las pruebas, revisar el historial de git y consultar el
estado real de las corridas de GitHub Actions.

## 1. Afirmaciones que resistieron la verificación

| Afirmación | Cómo se comprobó | Resultado |
| :--- | :--- | :--- |
| Pactos de corredoras retirados del sitio | `rg` de los dos identificadores en `docs/` y `data_manifest.json` | 0 referencias |
| Archivos retirados de verdad | `ls docs/outputs/corredoras_bolsa/` y `git show --stat 5a72440` | 4 archivos eliminados (Parquet y JSON) |
| Carátulas XML cuadran | recálculo desde Parquet con pandas 3.0.6 | 621/621, diferencia máxima 0 |
| Sin duplicados, nulos ni RUT ajenos | recálculo desde Parquet | 0 duplicados `(rut, periodo)`, 0 nulos, 0 RUT fuera del universo |
| `balance_resumen` no es cotejo externo | comparación columna a columna | réplica exacta de las columnas compartidas |
| Universos declarados en las notas | largo de los JSON publicados | ffmm 1.543 · fi 1.677 · agf 68 · retail 17 · corredoras 120 |
| Fuentes XML de fondos | descarga real del archivo `FMEF` y `FIEF` | XML IFRS válido, con `TotalActivo`, contexto y moneda |
| XBRL de AGF y RVEMI | inspección de la ficha CMF | enlaces XBRL existen; CMF advierte que su contenido está en revisión |
| Dígito verificador Módulo 11 | 6 RUT reales de CMF | 6/6 correctos |
| Workflows válidos | `yaml.safe_load` + `argparse --help` + validación de sector inválido | parsean y validan |
| Pruebas del pipeline | `python -m unittest discover` | 11/11 pasan |
| Corrida masiva en Actions | `gh run view` | 4 shards en `success` |

## 2. Defectos encontrados y corregidos

**F1 (alto, funcional).** `periodos_ultimo()` calculaba mal el último cierre en febrero y marzo:
devolvía un trimestre **futuro**. Fórmula antigua reproducida: mes 02 → `2026-12`, mes 03 → `2026-12`
(cuando corresponde `2025-12`). Corregido y cubierto con prueba de regresión para los 12 meses,
incluida una que prohíbe fechas futuras.

**F2 (medio, riesgo de falsa confianza).** El job podía terminar en verde con **cero filas
verificadas**: el código de salida solo fallaba si *todos* los intentos eran error. Ahora el resumen
declara `estado_global` (`con_datos_verificados`, `sin_datos_verificados`, `falla_red_o_parseo`,
`sin_intentos`) y el backfill manual usa `--fail-if-sin-datos`, que falla si no se validó ninguna fila.

**F3 (declarativo).** Afirmé haber retirado las tablas también del `data_manifest.json` y del ERD.
Verificado: esos archivos **nunca** las referenciaban (`git show 16b3486:...` da 0 coincidencias).
La nota de fuentes fue corregida; el PR se corrigió en el mismo sentido.

## 3. Límites y defectos abiertos (no corregidos)

* **F4.** Desde este sandbox no pude descargar artifacts ni logs de Actions (el proxy corta la
  descarga). Por lo tanto **no está comprobado que la corrida masiva extrajera filas**: `success`
  prueba que los jobs no reventaron, no que existan datos. Lo mismo vale para la sonda de fuentes:
  sus corridas dan verde, pero **su informe nunca fue revisado**.
* **F5.** El XBRL de AGF y retail no tiene mapeo versionado de taxonomía, dimensiones, moneda ni
  consolidación: por diseño no produce balance ni resultado. Es alcance pendiente, no un dato oculto.
* **F6.** La caché de Actions usa clave por `run_id` con ledger acumulativo (4 cachés por día):
  puede acercarse al límite de 10 GB del repositorio. Conviene rotar o compactar el ledger.
* **F7.** Cobertura del barrido diario: con 90 combinaciones por sector y shard, y ~380 entidades por
  shard en fondos mutuos, una vuelta completa toma alrededor de 8 corridas. No es un error, pero
  conviene no confundir "corrió" con "ya cubrió todo".
* **F8.** El checkout local se había reseteado al commit base y se perdió el `.venv`. Lo publicado
  estaba intacto en `origin`; el estado local previo quedó guardado en `git stash`. Este audit se hizo
  tras restaurar la rama, reinstalando pandas para poder recalcular.
* **F9.** Los vicios del extractor original de Corredoras (tipo de cambio de respaldo `900`, errores
  numéricos convertidos en cero, DV recalculado, `except: pass`) **siguen presentes**: la ruta nueva
  no los hereda, pero las filas ya publicadas no quedan retrocertificadas por eso.
* **F10.** El cotejo contra la ficha CMF sigue siendo de 2 filas de una entidad. Es evidencia de que
  la ruta XML reproduce lo oficial, no una certificación del universo.

## 4. Conclusión

Lo entregado funciona y las afirmaciones centrales se sostienen al recalcularlas. Los errores
encontrados fueron de cálculo de fechas, de semántica de éxito en CI y de una afirmación mía
exagerada; los tres quedaron corregidos y con prueba. Lo que **no** puedo afirmar todavía es que la
extracción masiva haya producido datos: eso sigue pendiente de revisar los artifacts en la interfaz
de Actions y de cotejar una muestra XML contra la ficha CMF, como se hizo en Corredoras.

## 5. Segunda revisión tras observar los resúmenes reales de Actions

La corrida `36329495131` produjo (cuatro shards, combinaciones evaluadas esa corrida):
46 `ok_xml` Corredoras, 335 FFMM y 335 FI; 0 XBRL AGF/RVEMI.
La siguiente corrida `36330191580` registró 46/289/348 respectivamente;
**son muestras de diferentes posiciones del cursor**, no una comparación A/B de calidad.

Al continuar la revisión se corrigieron otras afirmaciones y controles:

* La ficha CMF de AGF Security `96639280` ofrece XBRL para **2026-03 y 2026-06**;
  por tanto mi generalización de AGF como exclusivamente anual era errónea.
  Se consultan cortes trimestrales para AGF; para RVEMI/retail se consultan también
  pero **su cobertura trimestral aún no está cotejada por entidad**. Para FFMM sí se confirma
  periodicidad anual explícita en la ficha del fondo RUN 8490.
* Se quitó la lógica que borraba **cualquier** carácter no numérico de un monto al reparar
  XML. Un `2&957448` no es prueba de que el monto original sea `2957448`:
  ahora esa cuenta se rechaza. Reparar codificación o un `&` en el **nombre** queda marcado
  `revisar_xml`, y no cuenta como `ok_xml`. Igual para DV del archivo incorrecto.
* Los enlaces `safec_ifrs_verarchivo.php?auth=...&send=...` pueden responder HTML;
  eso se informa como `xbrl_descarga_html`, **no** se declara XBRL extraído.
  Los tokens efímeros se quitan de la URL escrita al artifact. Cookies/referer no
  resolvieron esta descarga en la corrida anterior; sigue pendiente hallar una vía oficial.
* La cache ledger se acota a las últimas 500 filas por sector/shard; el cursor queda aparte.
  Esto reduce el crecimiento de los artifacts/cachés; no constituye un histórico completo.

Cotejo puntual contra fichas CMF: fondo mutuo RUN 8490, diciembre 2014,
activos 2.957.448 = pasivos 5.947 + activo neto 2.951.501, y utilidad tras
impuestos 3.470 (miles de pesos). FIRES RUN 7064, diciembre 2021: activos
24.887, patrimonio 24.826, pasivos corrientes 61, resultado -122; la ficha
indica **miles de dólares**, y `TotalPasivo=24.887` XML incluye patrimonio.
Estos ejemplos no demuestran cobertura universal ni certifican cada JSONL.

Fuente de cotejo:
* [FFMM CMF RUN 8490, 2014-12](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=8490&tipoentidad=RGFMU&vig=VI&control=svs&pestania=3&mm=12&aa=2014&tipo=I&tipo_norma=IFRS).
* [FIRES CMF RUN 7064, 2021-12](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=7064&tipoentidad=FIRES&vig=VI&control=svs&pestania=29&mm=12&aa=2021&tipo=I&tipo_norma=IFRS).
* [AGF Security CMF 2026-06](https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=96639280&tipoentidad=RGAGF&vig=VI&control=svs&pestania=3&mm=06&aa=2026&tipo=I&tipo_norma=IFRS).

**Persistencia del schedule:** `schedule` solo se ejecuta desde la rama por defecto de
GitHub; estos workflows aún están en el PR y no se han fusionado a `main`.
Los `push` de esta rama sí los prueban; no afirmar automatización diaria activa todavía.

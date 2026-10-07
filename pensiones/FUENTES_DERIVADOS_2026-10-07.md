# Dónde obtener derivados de los fondos de pensiones chilenos

**Revisión: 7 de octubre de 2026. Estado: portal BDP confirmado por captura del usuario; manual y archivo histórico inspeccionados en espejo de terceros; descarga vigente SP y autorización de publicación pendientes.**

## Conclusión ejecutiva

**Objetivo vigente: detalle de instrumento/contrato o pata, comparable con `fi_futuros` y `fi_opciones`.** No basta una apertura por AFP y fondo.

1. **Candidato público principal encontrado: portal BDP, «Carteras históricas de Inversión de los Fondos de Pensiones».** La captura aportada por el usuario confirma paquetes 1996–2005, 2006–2015, 2016–a la fecha y documentación. El usuario confirma descarga mediante selección y botón al pie. La captura indica cierre de base `01/MAY/2026`; no se ha verificado el último corte de las filas.
2. **Evidencia instrumental real, aunque secundaria:** un espejo público conserva `docchist.pdf` (manual SP, mayo 2020) y archivos anuales convertidos a Excel. Se leyó el manual y recorrieron las 157.421 filas del XLSX 2021 (enero–mayo). Contiene serie/nemotécnico, nombre de entidad, unidades, precio, inversión, precio de ejercicio forward y tasas de swaps: **sí existe evidencia de una base histórica instrumental mucho más próxima a FI que los listados 22–29.**
3. **Límites:** no hay ID contractual universal ni fechas de inicio/vencimiento separadas en esas 18 columnas; la serie puede codificar vencimiento conforme a la norma correspondiente. No transformar duración (`plazo_economico`) en fecha de vencimiento. Debe validarse el CSV SP original: el espejo XLSX muestra indicios graves de pérdida de separadores decimales.
4. **Uso/publicación bloqueados por revisión de condiciones:** el manual histórico declara «uso exclusivo para fines de investigación» y solicita no distribuir la información. Investigar y resumir hallazgos no autoriza a publicar la base en `docs/outputs/`, ni Parquet/JSON derivado masivo. Revisar condiciones actuales y pedir autorización antes de integrarla públicamente.
5. **Fuentes complementarias:** archivo regulatorio de cartera (Título VI, Cap. II), D-2.5–D-2.8 y D-2.16, listados públicos SP 22–29 y SIID. Ya no corresponde recomendar Transparencia como primer paso antes de inspeccionar esta descarga pública.

**Corrección explícita de la investigación anterior:** la imposibilidad del lector web de abrir BDP y las búsquedas sin resultados no acreditaban ausencia de carteras públicas. La captura confirma el catálogo. El manual histórico y el XLSX del espejo también respaldan el esquema `cartera_mensual_*.csv` y los campos del ejemplo de script, con diferencias de versión/nombre pendientes de cotejo con SP.

**Hallazgo financiero bloqueante:** la nota al pie del cuadro SP 26 dice explícitamente «Corresponde a la valorización del contrato Swap». No es un nocional. El extractor retirado lo llamaba `nocional_usd_millones` y descartaba importes negativos. Es necesario reemplazar la lógica, no sólo cambiar el enlace de descarga.

## Nivel de detalle requerido — aclaración tras revisar derivados FI

**El objetivo del usuario es el detalle contractual publicado en FI, no una serie agregada de exposición.** La propuesta SP de listados 22–29 y el monitor SIID descritos arriba son complementos; **no cumplen por sí solos ese objetivo**.

Se revisaron `fi/scripts/actualizar_carteras.py`, los Parquet reales de `futuros_forwards/2026.parquet` y `opciones/2026.parquet`, y dos páginas CMF de junio 2026. La referencia es:

- `fi_futuros` / `fi.futuros_forwards`: 16 columnas, con periodo y RUN del fondo, clasificación ESF, activo objeto, nemotécnico, unidad de cotización, inicio y vencimiento, **nombre de la entidad contraparte**, moneda de liquidación, país, posición compra/venta, unidades nominales, precio futuro, monto comprometido y valor de mercado.
- `fi_opciones`: 21 columnas; además incluye forma de ejercicio, tipo de opción, número de contratos, precio de ejercicio, prima, unidades y valor del activo objeto y valorizaciones.
- Junio 2026 contiene localmente **569 filas de futuros/forwards/swaps en 41 fondos** y **4 filas de opciones**. Son conteos de renglones publicados, no una certificación de 569 contratos económicos distintos.

Ejemplo cotejado en [CMF, RUN 7141, junio 2026](https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_fut_fw.php?rut=7141&periodo=202606&tipo=fi&cartera=F): forward USD con Banco Santander Chile, posición V, inicio 22-05-2026, vencimiento 20-08-2026, 4.400.000 unidades nominales, precio futuro 898,55, monto comprometido 3.928.177 y valor de mercado 4.029.333 (los dos últimos en miles de moneda funcional según el modelo FI). Esos atributos coinciden con la fila del Parquet.

**Precisión sobre la granularidad FI:** no hay un ID contractual único en este esquema. En [RUN 7099](https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_fut_fw.php?rut=7099&periodo=202606&tipo=fi&cartera=F) aparecen renglones SWAP con igual contraparte/inicio/vencimiento pero posiciones y unidades de cotización distintas: pueden corresponder a patas del contrato. No agregarlos ni contar cada pata como contrato único sin identificación adicional. Tampoco reinterpretar automáticamente `valor_mercado_miles_mf` como MTM neto: conservar el significado de la columna de origen.

**Cambio de prioridad para investigar pensiones:** buscar primero una cartera instrumental, anexo o archivo de posiciones con serie/nemotécnico y condiciones de cada contrato o pata, AFP y tipo de fondo, contraparte, fechas, unidades, precio/tasa y valorización. Los reportes D-2 y las especificaciones de carteras SP son pistas regulatorias, pero todavía falta demostrar una publicación accesible con ese detalle. SIID sectorial y listados agregados no deben presentarse como sustitutos ni usarse para fabricar contratos.

## 1. Contexto del proyecto revisado

El SIF publica Parquet estático en `docs/outputs/`, consultado con DuckDB-Wasm desde `docs/js/duckdb_client.js`. Los procesos deben seguir fuente → staging → auditoría → publicación; el linaje y el significado financiero son más importantes que conseguir una tabla con claves únicas.

Archivos revisados: README general, `pipelines/README.md`, `pensiones/README.md`, auditoría AFP del 27-09-2026, downloader, generador de derivados, parsers en streaming, consolidadores e inspectores de pensiones; catálogo/cliente SQL y extractor macro; workflow de entidades.

- Pensiones publica únicamente el maestro de identificación; no hay una tabla observacional vigente de derivados. La auditoría explica el retiro de las antiguas series.
- `generate_derivados_afp.py` construye forwards mediante fórmulas y contrapartes/periodos fijados. **No ejecutarlo para recuperar datos reales.**
- `parse_sp_carteras.py` y `pipeline_stream_history.py` seleccionan únicamente listados 26/28 para derivados, tipifican todo como swap de tasas y conservan sólo `monto_usd > 0`. Pierden el tipo de fondo y categorías presentes en el contexto XML; posteriormente agrupan.
- `pipeline_stream_history.py` elimina ZIP tras procesarlo: eso impide reproducir la auditoría si no existe conservación externa verificable.
- El parser busca nodos con namespace fijo `http://www.spensiones.cl/xml`; la documentación consultada declara `http://www.safp.cl/xml`. Debe detectarse la versión/namespace real del XML, no asumirse que un documento antiguo comparte el esquema reciente.
- `all_periods.json` y los scripts de prueba son pistas de laboratorio, no evidencia de que cada mes se haya descargado correctamente.
- El workflow `entidades.yml` actualiza listas de entidades, no posiciones de derivados. Las tasas SPC disponibles en macro son precios/tasas de mercado, **no exposición de las AFP**.

No se ejecutaron generadores, no se modificaron Parquet, manifiestos, SQL ni workflows.

## 2. SP: fuente principal por AFP y fondo

### Acceso y disponibilidad observada

[Centro de estadísticas financieras](https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=estfinfp&menuN2=NOID).

En la página consultada, el selector muestra:

| Serie | Rango del selector observado | Qué certifica |
|---|---|---|
| Cartera de inversiones desagregada | 2000-06 a **2026-05** | Existencia de opciones en el selector, no descarga/cobertura íntegra de derivados |
| Cartera agregada | 2008-09 a **2026-08** | Disponibilidad anunciada; no igual detalle que la desagregada |
| Estados financieros | 2002-09 a **2026-06** | Cierres anunciados; no todos los meses |

Confirmé que [mayo de 2026](https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo=202605&ext=.php) tiene una página titulada correctamente, enlace de ZIP y documentación XML. Usé **marzo 2026** para leer tablas concretas. No afirmo que mayo sea el último mes de cada servidor o que el ZIP se haya descargado: el contenido web puede actualizarse o quedar en caché.

[Norma de publicación: Libro IV, Título V](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-2551.html): agregado al cierre del mes anterior; desagregado al último día del mes anterior al cuarto mes precedente. El material divulgativo habla de cuatro meses de rezago y también del quinto mes precedente. **Usar el selector y verificar el encabezado de cada documento; no extrapolar el último mes desde la fecha actual.**

### Mapa de listados

[Índice SP de marzo de 2026](https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo=202603&ext=.php).

| Listado | Contenido | Orientación de la tabla | Uso recomendado |
|---|---|---|---|
| 22 | Derivados nacionales; la vista examinada se titula forwards nacionales | Un fondo, columnas AFP; también Total Fondos | Extracción primaria de forwards nacionales |
| 23 | Derivados nacionales | Una AFP, columnas A–E y total | Cotejo contra 22, no concatenar |
| 24 | Derivados extranjeros; vista examinada: forwards extranjeros | Un fondo, columnas AFP; también Total Fondos | Extracción primaria de forwards extranjeros |
| 25 | Derivados extranjeros | Una AFP, columnas A–E y total | Cotejo contra 24 |
| 26 | Swaps nacionales | Un fondo, columnas AFP y total | Extracción primaria de valorizaciones |
| 27 | Swaps nacionales | Una AFP, columnas A–E | Cotejo contra 26 |
| 28 | Swaps extranjeros | Un fondo, columnas AFP y total | Extracción primaria de valorizaciones |
| 29 | Swaps extranjeros | Una AFP, columnas A–E | Cotejo contra 28 |

**Son orientaciones alternativas de la misma información.** Extraer una orientación y auditar contra la otra. No sumar ambos miembros de cada par ni incluir Total Fondos junto a A–E.

### Qué representa realmente el dato

**Forwards (22/24):** encabezado «En millones de dólares»; nota «Corresponde a las unidades del contrato en función del activo objeto». El monto es una magnitud ligada al subyacente expresada en USD equivalentes: no es precio pactado, resultado, patrimonio invertido ni MTM. Conservar la descripción original de la medida; no etiquetar `nocional` hasta validar su equivalencia exacta.

La tabla muestra jerarquía **moneda objeto → Forward → código (WNMC, WNMV, YNMC, YNMV, WNNC, etc.) → moneda contraparte**. El renglón del código puede repetir el total de sus monedas hijas. No basta excluir filas cuya glosa comience con TOTAL: se requiere identificar hojas.

**Importante sobre “contraparte”:** en las vistas 22/24 examinadas aparece la **moneda contraparte**, no el nombre del banco para cada forward. No confundir una moneda con la entidad contraparte; el título genérico del listado no prueba que esté disponible un RUT bancario.

**Swaps (26/28):** encabezado «En millones de dólares y porcentaje»; nota «Corresponde a la valorización del contrato Swap». Aparecen valores positivos, negativos y ceros redondeados, categorías de tasas, índices de tasas y monedas, operaciones en cámaras y con garantías bilaterales. La columna `Unidad de Reajuste` (NO, UF, US$) **no cambia la moneda de presentación del importe, que sigue siendo MMUS$**.

Estas filas son agregados publicados, no operaciones identificadas una a una. Tampoco prueban que se observen exposiciones brutas positivas/negativas por contrato: puede haber compensación dentro de un agregado.

### Evidencia de celdas oficiales — fondo C, 31-03-2026

| Cuadro | Selección | Valor publicado | Implicación |
|---|---|---:|---|
| 22 | USD objeto, WNMV, moneda contraparte pesos, Habitat | **4.796,63 MMUS$** | Magnitud del activo objeto; no MTM |
| 26 | Swap nacional de tasas, Banco de Chile, unidad NO, Capital | **−1,99 MMUS$** | El filtro `> 0` elimina información oficial |
| 26 | Total swap nacional de monedas, todas las AFP | **−26,74 MMUS$** | No todos los swaps son de tasas |
| 28 | Total swaps extranjeros de tasas con garantías bilaterales, todas las AFP | **−396,88 MMUS$** | Valorización negativa, no nocional negativo |

Vistas oficiales utilizadas:

- [Cuadro 22, C](https://www.spensiones.cl/apps/carteras/genera_desagregada_xsl_v2.0.php?param=MFNjdDc0RXZPaWU0Q0diTGt3OWhrTjVwNy92Q1BRb01wOThBdzl0WW10aG1ZSFdBYWFMOVRRPT0=).
- [Cuadro 24, C](https://www.spensiones.cl/apps/carteras/genera_desagregada_xsl_v2.0.php?param=MFNjdDc0RXZPaWU0Q0diTGt3OWhrQlVuelJFUjA3b2VwOThBdzl0WW10aG1ZSFdBYWFMOVRRPT0=).
- [Cuadro 26, C](https://www.spensiones.cl/apps/carteras/genera_desagregada_xsl_v2.0.php?param=MFNjdDc0RXZPaWU0Q0diTGt3OWhrTzdEZEczUG45cDFwOThBdzl0WW10aG1ZSFdBYWFMOVRRPT0=).
- [Cuadro 28, C](https://www.spensiones.cl/apps/carteras/genera_desagregada_xsl_v2.0.php?param=MFNjdDc0RXZPaWU0Q0diTGt3OWhrTGR5eFFQc0ljelBwOThBdzl0WW10aG1ZSFdBYWFMOVRRPT0=).

Son ejemplos de la fuente, **no un cotejo contra un nuevo Parquet**. No recalcular totales exactos sumando celdas ya redondeadas a dos decimales.

### Descarga y esquema

1. Abrir `loadCarInv.php` con `periodo=YYYYMM`.
2. Resolver desde esa página el enlace «Obtener Aquí»; actualmente apunta a `GetFile_v2.0.php?param=...`. No fabricar el parámetro ni suponer estable una ruta ZIP antigua.
3. Guardar URL índice, URL resuelta, fecha UTC, headers disponibles, tamaño y SHA-256 del ZIP; conservar fuente externa o en staging ignorado.
4. Validar ZIP real, inventariar miembros, identificar XML y comprobar periodo, namespace, títulos, subtítulos y notas.
5. Leer el [esquema documentado](https://www.spensiones.cl/xml/doc/apps/finmes/ultima_version_cartera_desagregada/). Incluye `listado_por_instrumento_monedaobjeto_afp`, `afp_por_moneda_objeto`, `fondos_por_moneda_objeto`, agrupaciones y notas. Preservar esos ancestros: una `fila` aislada no conserva su significado.
6. Resolver enlaces HTML/Excel de la misma página para auditoría. No dar por hecho que el enlace «Excel» entregue XLSX: inspeccionar contenido.

El índice de marzo incluye aviso de copyright CUSIP/FactSet. Revisar términos de reutilización de identificadores de terceros antes de redistribuir una cartera completa. No implica automáticamente que los agregados de derivados tengan la misma restricción, pero tampoco que todo el ZIP sea de libre redistribución.

## 3. BCCh / SIID-TR: fuente específica, agregada y automatizable

**Ruta correcta:** [Monitor de Fondos de Pensiones](https://www.siid.cl/fondos-de-pensiones).

La página consultada identifica estas secciones:

- Comparación mercados.
- Tipos de cambio.
- Swap promedio cámara nominal.
- Swap tasa interés extranjera.
- Derivados UF-CLP.
- **Códigos de series para API - FP.**

El [recuadro del informe de abril 2025, página 4](https://www.bcentral.cl/documents/33528/7252524/Informe%20Mensual%20del%20Mercado%20de%20Derivados%20abril%202025.pdf/33d8514a-1e1d-46f3-e787-157d33310888?version=1.0&t=1747953309955) confirma que el monitor presenta **montos vigentes y transados**, detalle de **sector de contraparte, plazos y monedas**, archivos para descargar datos y códigos para acceder vía **API-BDE**. Una [publicación BCCh del 11-06-2025](https://www.siid.cl/web/siid/contenido/-/detalle/nota-tecnica-n-5-fondos-de-pensiones-transacciones-en-los-mercados-de-derivados-financieros-duplicar-2) enlaza expresamente ese monitor. El slug contiene “nota-tecnica-n-5”, pero el documento abierto se titula **Presentación FIF 2025**: no citarlo erróneamente como la Nota Técnica 5.

### Qué se debe confirmar antes de integrar

El monitor está incrustado en Power BI. La lectura textual verificó secciones, **no descargó sus tablas ni códigos de API**. Quedan pendientes:

- Código BDE exacto de cada serie, título, frecuencia, primera y última observación.
- Unidad: MMUSD, CLP, UF u otra; paridades utilizadas y tratamiento de revisiones.
- Perspectiva de compra/venta, bruto/neto, stock/flujo, plazo original/residual.
- Cobertura del reporte directo de AFP versus operaciones reportadas por bancos; tratamiento de duplicados, novaciones y compensación.
- Disponibilidad de identificación AFP/fondo: la evidencia leída confirma sectores de contraparte, **no** una apertura pública por RUT de cada AFP.

**No inventar códigos de serie ni convertir todas las magnitudes a MMUSD por conveniencia.** El extractor macro existente puede reutilizarse para la API sólo después de registrar y cotejar esas series.

[Monitor mensual bancario](https://www.siid.cl/monitor-mensual) e [informe general de derivados](https://www.siid.cl/informe-derivados-financieros) sirven como complemento. Si se usa una serie bancaria cuya contraparte sea “Fondos de pensiones”, se observa la perspectiva del banco y ese perímetro, no necesariamente todo el universo AFP. El informe general declara rezago de 23 días y revisión de tres meses previos; **no trasladar automáticamente esa política a todas las series FP sin su metodología**.

## 4. Microdatos y fuentes de contraste

### Reportes regulatorios SP

[Libro IV, Título VIII, capítulo IV](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-3830.html):

| Formulario | Materia | Documentación |
|---|---|---|
| D-2.5 | Opciones, futuros y forwards nacionales | [Instrucciones](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-3836.html) |
| D-2.6 | Opciones, futuros y forwards extranjeros | [Instrucciones](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-3837.html) |
| D-2.7 | Swaps nacionales | [Instrucciones](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-3838.html) |
| D-2.8 | Swaps extranjeros | [Instrucciones](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-3839.html) |
| D-2.16 | Valoración de derivados vigentes con garantías bilaterales | [Instrucciones](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-9567.html) |
| D-2.17 / D-2.18 | Movimientos y cartera de garantías recibidas | Índice del capítulo |

D-2.5 exige registro operación a operación y define folios, códigos, series y vencimientos. Eso demuestra que existe información regulatoria más granular, **no** que sus archivos de envío puedan descargarse públicamente. Para datos contractuales, preguntar primero por versión histórica pública, anonimizada o agregada, plazo de divulgación, diccionario y restricciones. No se envió ninguna solicitud en esta revisión.

### Archivo mensual de cartera: el candidato principal para igualar FI

Fuente: [Libro IV, Título VI, Capítulo II](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-3786.html), numerales 4–6. Cada registro incluye **13 campos**:

`administrador de cartera`, `código de custodia`, `tipo de instrumento`, `moneda de emisión`, `instrumento objeto`, `nemotécnico o serie`, `precio de ejercicio o del contrato`, `fecha de vencimiento`, `unidades`, `unidades moneda no objeto`, `precio unitario`, `valor total`, `tipo de operación`.

La entrega corresponde al **último día hábil de cada mes**, antes de las 24:00 horas del día hábil siguiente, y utiliza `TOT` como código de custodia salvo instrucción contraria. Los últimos 30 días deben estar disponibles para transmisión inmediata a requerimiento de la SP; eso no significa que se publiquen diariamente.

| Atributo del patrón FI | Evidencia regulatoria AFP | Acceso observado |
|---|---|---|
| AFP + fondo + fecha de corte | Archivo separado por tipo de fondo y cierre mensual | Existe en agregados; microarchivo pendiente |
| Serie/nemotécnico | Cap. II, 4.f | No encontrado por contrato en listados 22–29 |
| Contraparte | Series de forwards/swaps incluyen código de contraparte según D-2.5/D-2.7 | Requiere serie real y catálogo código → entidad; no inferir RUT |
| Inicio/suscripción | Serie de swap incluye inicio; D-2.16 tiene fecha explícita | No verificado públicamente por contrato |
| Vencimiento | Cap. II, 4.h, AAAAMMDD | No verificado públicamente por contrato |
| Unidades/nominal | Cap. II, 4.i–j; D-2.7 precisa entregar/recibir | Disponible sólo agregado en listados examinados |
| Precio de ejercicio/contrato | Cap. II, 4.g; D-2.5–D-2.6 | No verificado públicamente por contrato |
| Tasas de cada parte de swap | D-2.7/D-2.8 y D-2.16 | No verificado públicamente por contrato |
| Precio unitario/valor total | Cap. II, 4.k–l, pesos | No equiparar a toda medida FI ni a nocional |
| Ganancia/pérdida de cierre explícita | D-2.16: valorizaciones SP, AFP y contraparte en moneda de liquidación | Sólo perímetro D-2.16; microdatos sin acceso validado |
| ID contractual único | Folio D-2.5 corresponde a transacciones bursátiles de opciones/futuros; serie no demuestra unicidad | No hay identificación universal verificada |

La [instrucción D-2.16](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-9567.html), 1.c, exige stock de **derivados extranjeros con garantías bilaterales**, incluidos vencimientos/liquidaciones anticipadas del día. Sus instrucciones específicas también describen campos para instrumentos nacionales; conservar esa diferencia y pedir aclaración a SP, sin ampliar por cuenta propia el perímetro. D-2.16 no sustituye la cartera completa de derivados.

Las [instrucciones D-2.7](https://www.spensiones.cl/portal/compendio/596/w3-propertyvalue-3838.html) exigen además envío de contratos definitivos o borradores de estructura de swaps a `sprecios@spensiones.cl`, al menos dos días antes del inicio. Es un canal de reporte AFP → SP, **no** un buzón público de descarga ni una invitación a solicitar documentos por ese correo.

### Códigos oficiales: comprobación adicional, no prueba de un CSV

Se leyó el [Capítulo VI, Código de instrumentos, PDF oficial](https://www.spensiones.cl/portal/compendio/596/fo-article-10775.pdf), incluidas las tablas de D-2.5–D-2.8. También se verificó el [esquema XML histórico del informe diario AFP v1.1, D-2.5](https://www.spensiones.cl/xml/doc/apps/informe_diario/afp/v1.1/id9.html), que enumera WNMC/WNMV y define `nemotecnico`, `precio_ejercicio`, `unidades`, `precio_unitario`, `valor_total`, etc. **Es documentación del envío, no un archivo con observaciones.**

Los códigos del ejemplo de consolidación sí tienen respaldo normativo; no corresponde tratarlos como inventados por no aparecer en una búsqueda inicial:

| Códigos | Significado oficial |
|---|---|
| WNMC / WNMV | Forward compra/venta de monedas con una moneda nacional |
| WNNC / WNNV | Forward nacional compra/venta de monedas, ambas extranjeras |
| WEMC / WEMV | Forward compra/venta de monedas, ambas extranjeras, tabla D-2.6 |
| WENC / WENV | Forward extranjero compra/venta con una moneda nacional |
| YNMC / YNMV | Forward compra/venta con moneda nacional y garantías bilaterales |
| YEMC / YEMV | Forward compra/venta, ambas monedas extranjeras, garantías bilaterales |
| YENC / YENV | Forward extranjero compra/venta con moneda nacional, garantías bilaterales |
| SNT / SNM | Swap nacional de tasas / moneda |
| YSNT / YSNM | Swap nacional de tasas / moneda con garantías bilaterales |
| YSET / YSEM | Swap extranjero de tasas / moneda con garantías bilaterales |

No usar esta lista parcial como universo: también hay futuros/opciones y códigos X para compensación e I para índices de tasas, entre otros. Verificar vigencia por fecha. La comprobación normativa de los códigos no bastaba para acreditar una publicación CSV; **la comprobación adicional del manual histórico en el espejo sí describe `cartera_mensual_xxxx.csv` delimitado por `;` y sus 18 campos** (ver sección BDP). Falta cotejar con la documentación vigente descargada de SP.

### Precedente de Transparencia: C350-17

Se leyó íntegramente la [decisión CPLT C350-17, 26-05-2017](https://extranet.consejotransparencia.cl/Web_SCW/Archivos/C350-17/DecisionWeb_C350-17.pdf).

- La solicitud pedía informes diarios electrónicos originales de Bansander para noviembre/diciembre de 2007 y enero de 2008, no un stock mensual acotado de derivados.
- La SP sostuvo que sólo entregaba D-1 y que las transacciones desagregadas afectaban estrategia comercial; afirmó que publicaba el stock histórico mensual agregado/desagregado.
- El CPLT consideró la información pública por formar parte de la fiscalización y **desestimó** la causal del art. 21 Nº 2: la AFP no acreditó daño comercial con suficiente especificidad.
- **No ordenó entregar**: rechazó el amparo por art. 21 Nº 1 letra c), debido a la carga de recuperación/procesamiento de cintas e informes (universo de más de 300 ID/6.000 formularios según el expediente).
- No se pronunció sobre art. 21 Nº 5 en relación con art. 50 de la Ley 20.255 por resultar inoficioso.

Implicación de investigación, no garantía jurídica: priorizar consulta por **un archivo existente de stock de cierre de un mes y un fondo**, formato original y diccionario, sin pedir un análisis nuevo ni reconstrucción histórica. Si hay reservas parciales, consultar por entrega divisible manteniendo el detalle instrumental. No presentar el fallo como aprobación de acceso ni como prohibición absoluta de acceder a derivados.

### Portal BDP: catálogo confirmado y evidencia instrumental encontrada

URL: [Acceso a bases de datos](https://www.spensiones.cl/apps/bdp/index.php).

#### A. Evidencia directa del usuario

La captura muestra la categoría expandida **«Carteras históricas de Inversión de los Fondos de Pensiones»** y estas opciones:

| Opción | Tamaño anunciado en la captura |
|---|---|
| Desde 2016 a la fecha | 113,2 MB |
| Desde 2006 a 2015 | 164,0 MB |
| Desde 1996 a 2005 | 151,7 MB |
| Documentación archivos de carteras históricas | No indicado |

Fecha de cierre anunciada: **01/MAY/2026**. Es metadata de la base/portal, no una certificación de fecha de posición ni del último mes dentro de los archivos. El usuario indica que hay que seleccionar la opción y accionar el botón de descarga al pie de la página.

La página [Estadísticas e Informes](https://www.spensiones.cl/portal/institucional/594/w3-propertyname-621.html) enlaza exactamente al portal. El lector web sigue redirigiendo a `404%20HTML`; una prueba de conexión directa desde el entorno falló durante TLS. **No se pudo accionar el botón ni obtener su petición o la descarga vigente.** No se intentó eludir CAPTCHA/WAF ni se inventó el destino del formulario.

#### B. Evidencia secundaria: manual SP y archivos históricos en GitHub

Se encontró el repositorio público [Sud-Austral/Descargas](https://github.com/Sud-Austral/Descargas/tree/699e896c470420577989c350adff5546c11127fc), con una carpeta de carteras históricas, `docchist.pdf` y XLSX anuales 1996–2021. Se descargaron sólo el manual y 2021 mediante la API GitHub, en `scratch/bdp-research/` (ignorado por Git), sin ejecutar código de terceros.

**Proveniencia:** espejo de un tercero, **no descarga actual SP ni certificación de identidad binaria**. El manual tiene título «BASE DE CARTERA DE LOS FONDOS DE PENSIONES — MANUAL DE USO», versión mayo 2020, y referencia SP. Los notebooks muestran conversiones a Excel y agregaciones; no reutilizarlas para el objetivo FI porque eliminan serie, unidades, inversión, strike y tasas.

Manual: [docchist.pdf en espejo](https://github.com/Sud-Austral/Descargas/blob/699e896c470420577989c350adff5546c11127fc/Carteras%20hist%C3%B3ricas%20de%20Inversi%C3%B3n%20de%20los%20Fondos%20de%20Pensiones/docchist.pdf).

El manual describe **`cartera_mensual_xxxx.csv`**, por año, separado por **`;`**, con 18 campos:

| Posición | Campo del manual histórico | Definición relevante |
|---|---|---|
| 1 | `fecha` | AAAAMMDD |
| 2 | `afp` | Sigla de AFP que informa; catálogo histórico incluido |
| 3 | `tipo_de_fondo` | A–E |
| 4 | `tipo_de_instrumento` | Código y glosario anexo |
| 5 | `nemotecnico_del_instrumento` | Nemotécnico; admite identificación de series de derivados en archivo observado |
| 6 | `nombre_del_emisor` | Entidad nombrada; en muestras de derivados coincide con banco/contraparte |
| 7 | `nacionalidad_del_emisor` | E = extranjero |
| 8 | `unidad_de_reajuste_de_moneda` | Código de reajuste/moneda |
| 9 | `unidades` | Unidades del instrumento en cartera |
| 10 | `precio` | Precio del instrumento/operación de cobertura, pesos y centavos |
| 11 | `inversion` | Cantidad total invertida en instrumento, pesos chilenos según manual |
| 12 | `grupo_economico` | Grupo empresarial del emisor |
| 13 | `moneda_contrato_forward` | Moneda contraparte del forward |
| 14 | `moneda_objeto_forward` | Moneda objeto del forward |
| 15 | `precio_ejercicio_forward` | Precio por unidad del activo objeto |
| 16 | `plazo_economico` | **Duración** del instrumento, no fecha de vencimiento |
| 17 | `tasa_pactada_del_fondo_swap` | Tasa a pagar por fondo sobre capital insoluto |
| 18 | `tasa_pactada_de_la_contraparte_s` | Tasa a pagar por contraparte; nombre truncado en manual |

El XLSX 2021 usa `tasa_pactada_de_la_contraparte_swap` completo. **Registrar ambas variantes como diferencia de esquema**, no afirmar que el CSV original tiene la variante larga sin abrirlo. El manual referencia normativa antigua para tipos de instrumento; cotejar con Cap. VI vigente según fecha. No corregir silenciosamente las erratas del manual ni los datos del espejo.

#### C. Inspección real del XLSX 2021

Archivo: [cartera_mensual_2021.xlsx en espejo](https://github.com/Sud-Austral/Descargas/blob/699e896c470420577989c350adff5546c11127fc/Carteras%20hist%C3%B3ricas%20de%20Inversi%C3%B3n%20de%20los%20Fondos%20de%20Pensiones/cartera_mensual_2021.xlsx).

- **157.421 filas, 18 columnas**, cortes `20210129`, `20210226`, `20210331`, `20210430`, `20210531`. No cubre todo 2021.
- **55.361 filas de códigos de derivados observados:** 48.850 forwards, 6.462 swaps y 49 opciones de suscripción OSAN. Son renglones mensuales, **no contratos económicos únicos ni todos los años**.
- Familias observadas: WNMV/WNMC/WEMV/WEMC/WNNV/WNNC/WENV/WNTC, YEMV/YEMC/YENV/YENC, SNT/SNM/YSET/YSEM y OSAN.
- Todas esas filas tienen fecha, AFP, fondo, serie, nombre de entidad, unidades, precio e inversión informados. `plazo_economico` está vacío en todas; tampoco hay columnas de fecha de suscripción o vencimiento separado.
- Hay **5.773 claves repetidas** de fecha + AFP + fondo + tipo + serie, con 13.911 filas; 5.762 de esas claves presentan unidades, strike o tasas distintas. **No agrupar por serie ni deduplicar esas filas como si fueran duplicados.** No hay ID de contrato universal en el esquema.
- Ejemplo de identidad instrumental observado: Habitat A, 29-01-2021, WNMV, serie `FALNO US$210719`, entidad Banco Falabella, 90.000.000 unidades y precio de ejercicio almacenado como texto `736.9`. Conforme a D-2.5, el sufijo de esa serie codifica liquidación 19-07-2021. Es una derivación documentada de serie, no una columna original de vencimiento.
- Para swaps hay tasas completas en las dos columnas y valores de `inversion` positivos/negativos. No llamar a `inversion` nocional; no etiquetarlo como MTM neto validado sin cuadratura y semántica vigente. Conservar etiqueta de fuente.

**Bloqueo numérico del espejo:** mezcla textos con punto decimal y números enteros en columnas de precio/strike. Por ejemplo, en 38.071 filas la relación `unidades × precio / inversion` está cerca de **10^10**, mientras que en 11.401 está cerca de 1. Esto es consistente con pérdida de separadores en una conversión, pero **no autoriza a dividir todo por 10^10**. El CSV original debe resolver la ambigüedad. No publicar ni usar estos precios para calcular valores económicos.

Hashes de los archivos leídos:

- Manual SHA-256: `2c3153be6f0c68fa86a06a13e16e8efa56f4feb060f9bfdaf65802e89a0147e4`.
- XLSX 2021 SHA-256: `5042f3f49503a7e4a6fe7948076ec4f75346bb526c36bec4512119604a488377`.

Inventario y pruebas locales: `scratch/bdp-research/inspection_2021.json`, `checks_2021.json`, `docchist.txt`; no son salidas publicadas.

#### D. Condiciones de uso: revisar antes de publicar en el SIF

La portada del manual histórico dice literalmente: **«Esta base es de uso exclusivo para fines de investigación. Se solicita no distribuir esta información.»**

La disponibilidad de descarga no equivale a licencia de redistribución. Este informe investiga estructura y calidad, **no incorpora el dataset a Git ni a las salidas públicas**. Obtener documentación y términos vigentes y, si mantienen la condición, autorización expresa para una publicación masiva o derivada en el SIF. No extrapolar estas condiciones a la información agregada con otra fuente/licencia.

#### E. Siguiente comprobación

Prioridad: descargar del portal **documentación y paquete 2016–a la fecha**, o al menos el último CSV anual dentro del paquete. Validar separador, codificación, decimales, último corte, campos, contrapartes y multiplicidad de series; comparar contra una muestra FI sin inventar fechas de inicio/IDs/patas. Si no puede accederse desde el entorno, basta que el usuario adjunte la documentación y un CSV anual extraído (no necesita subir los tres paquetes) o un enlace directo de descarga sin credenciales/tokens.

### Estados financieros de los fondos, no de la sociedad AFP

Sirven para contrastar valorización y resultados de derivados a nivel contable. Ejemplos localizados: [Habitat marzo 2024](https://www.spensiones.cl/inf_estadistica/iftfp/2024/03/HA202403.pdf) y [ProVida marzo 2024](https://www.spensiones.cl/inf_estadistica/iftfp/2024/03/PR202403.pdf). No extraer magnitudes de snippets ni asumir unidades: leer cada encabezado y nota. Un resultado contable del período no equivale al MTM de cierre ni al nocional.

### Otras instituciones

CMF (bancos y aseguradoras), ComDer, bolsas y CCR pueden complementar perímetro bancario, compensación, contratos listados y elegibilidad de contrapartes. **No se verificó en esta revisión una descarga de cartera AFP completa en esas instituciones.** No sustituir datos SP por posiciones bancarias ni por listas de contrapartes elegibles.

FAPP, fondos de cesantía y patrimonio propio/encaje de las AFP requieren perímetros separados; este informe prioriza fondos de pensiones administrados por AFP.

## 5. Diseño recomendado para el SIF

**Propuesta complementaria, aún no implementada y no equivalente al nivel FI:** dos familias SP agregadas separadas y otra BCCh sectorial. La tabla instrumental objetivo sigue bloqueada por acceso a la fuente; no reemplazarla por estas familias.

### A. `afp_derivados_forwards_posiciones`

Una observación publicada por periodo + AFP histórica + fondo + mercado + moneda objeto + tipo/código + moneda contraparte + demás dimensiones efectivamente presentes en el XML.

Campos mínimos: `periodo`, `fecha_corte_fuente`, `rut_administradora_fuente`, `tipo_fondo`, `mercado`, `tipo_derivado_fuente`, `codigo_instrumento_fuente`, `moneda_objeto_fuente`, `moneda_contraparte_fuente`, `monto_activo_objeto_m_usd`, `medida_fuente`, `unidad_fuente` y linaje.

No crear ID de contrato, banco contraparte, strike, vencimiento ni MTM si no aparecen. Validar el código normativo vigente por fecha antes de derivar dirección, finalidad o modalidad. La ausencia de opciones/futuros en una vista no demuestra que no existan en todo el sistema.

### B. `afp_derivados_swaps_valorizaciones`

Observación por periodo + AFP histórica + fondo + mercado + categoría fuente + entidad publicada + unidad de reajuste + modalidad de garantías/compensación.

Importe: `valorizacion_m_usd`, firmado. Mantener categoría original para distinguir tasas, índices y monedas. Normalizar contraparte sólo con evidencia; un nombre no prueba un RUT. No agrupar operaciones bilaterales con otras modalidades borrando la distinción.

### C. `pensiones_derivados_siid_series`

Formato largo por fecha/periodo + código de serie oficial + valor + unidad + dimensiones/metadatos verificados. No asignar una serie sectorial a siete AFP mediante prorrateos. Reutilizar infraestructura API macro, no el generador de forwards.

### Controles obligatorios antes de publicar

1. Descargar un mes reciente y conservar ZIP/XML con SHA-256 en `.local-data/` o almacenamiento externo. No añadir grandes fuentes a Git ni escribir directamente en `docs/outputs/`.
2. Inventariar todos los listados de derivados, esquema, encabezados, notas y jerarquías. Versionar esquema según fuente real.
3. Probar extracción de A–E sin Total Fondos; excluir subtotales jerárquicos, no sólo glosas TOTAL.
4. Conservar negativos, ceros reportados y ausencias por separado; el guion de presentación no se convierte automáticamente a cero observado.
5. Cotejar 22↔23, 24↔25, 26↔27 y 28↔29 por AFP/fondo/dimensiones comunes, con tolerancia que refleje el redondeo publicado.
6. Comparar hojas con subtotales SP y separar esa cuadratura de las comparaciones contables. No cuadrar nocionales con patrimonio.
7. Validar celdas positivas y negativas y categorías de garantías, monedas y tasas. Repetir en años de diferentes formatos, sin imponer siete AFP actuales a toda la historia.
8. No llamar “contratos” a `COUNT(*)` de agregados. No sumar forwards y valorizaciones de swaps bajo un campo “exposición total”.
9. Verificar trazabilidad: URL, archivo, hash, periodo declarado, listado, ruta XML/fila, fecha de lectura, versión del extractor y estado del cotejo.
10. Publicar sólo después de auditoría; entonces registrar las nuevas tablas en manifiesto, cliente SQL, diccionario, catálogo y pruebas. No reactivar el backfill antiguo.

## 6. Límites de esta revisión y siguiente paso

Se verificaron páginas oficiales, documentación XML y celdas HTML de marzo 2026; disponibilidad web de mayo 2026 y monitor FP de SIID. También se inspeccionaron el manual histórico y XLSX 2021 en un espejo GitHub; **no se descargó el paquete BDP vigente ni los CSV originales SP**, ni las exportaciones Power BI; no hay un pipeline de publicación nuevo validado ni códigos API certificados. La red del entorno de ejecución está restringida para descargas directas a los dominios oficiales; la consulta de contenidos se realizó mediante herramientas web.

**Siguiente paso prioritario para el objetivo FI:** completar la descarga BDP confirmada por el usuario, cotejar manual vigente y CSV original, resolver formatos numéricos e identificar límites de fecha/ID/serie. Revisar licencia antes de publicación. Sólo solicitar complementos por Transparencia para campos realmente ausentes o problemas de acceso, no como sustitución prematura del archivo público localizado. Listados 22–29 y SIID son controles agregados, no fuente de fabricación de contratos.

## 7. Alcance ampliado: extracción de toda la cartera

Ante la consulta del usuario sobre extracción masiva, se clasificaron los **63 códigos**
del archivo espejo enero–mayo 2021 en **14 familias disjuntas**, conservando las
157.421 filas. Incluye renta fija, intermediación financiera, acciones, cuotas FI/FFMM,
ETF, capital/deuda privados, créditos sindicados, promesas, disponibilidades y derivados.
Ver [diseño de tablas, campos, cobertura y controles](PLAN_EXTRACCION_CARTERAS_BDP.md).
El archivo original y las condiciones de redistribución siguen pendientes; no hay una
extracción histórica SP completa ni publicación nueva. **Adenda posterior al PR #28:**
se implementaron descarga con catálogo oficial bloqueado, staging reanudable/incremental,
auditoría y gate de publicación; al no existir aún enlaces observados ni CSV SP, no se ha
ejecutado con datos reales. Ver [AUTOMATIZACION_BDP.md](AUTOMATIZACION_BDP.md).

# Auditoría de calidad de datos FI — 2026-10-07

## Alcance

Revisión local de los extractores `fi/scripts/actualizar_carteras.py` y `fi/scripts/eeff_xml.py`,
pruebas FI y Parquet/manifiestos publicados bajo `docs/outputs/fi/`. No se cambió el significado
ni la unidad de ningún importe. La corrección de pactos usa una firma compuesta de fila de plantilla;
no elimina registros por el solo hecho de tener importes en cero.

## Hallazgo corregido: plantillas publicadas como pactos

En `fi_pactos` aparecieron **18 filas ficticias** distribuidas en nueve cierres trimestrales entre
2012-03 y 2014-03, dos por cierre (RUN 7111 y 7185). No eran operaciones con monto cero: eran filas
de plantilla con este patrón conjunto:

- `tipo_operacion = VRC`, contraparte `Nombre Contraparte 1`;
- RUT ficticio `999234999` o `111111111`;
- `isin = ISIN`, `nemotecnico = Nemotecnico`, `nombre_emisor = Nombre Emisor`, `tipo_instrumento = CFI`;
- valor inicial/final, valorización, valor de mercado y tasa iguales a cero.

El filtro anterior reconocía el formato más nuevo (contraparte genérica y RUT 0), pero no este
formato histórico con sufijo «1» y RUT sintético no cero. Por eso el valor de la columna
`nemotecnico` era literalmente `Nemotecnico`.

Se amplió el filtro, manteniendo las señales en conjunto, y se agregó regresión del parser más una
comprobación sobre todo el `fi_pactos` publicado. Se retiraron las 18 filas; los conteos se
reconciliaron en los Parquet, manifiestos, control histórico y catálogo de descargas:

- `fi_pactos`: **1.716 → 1.698 filas**; **58 → 55 cierres con operaciones**.
- Los cierres **2012-06, 2013-03 y 2013-06** quedaron sin filas después de excluir sus plantillas;
  siguen registrados como cierres sondeados completos, no como fallas de descarga.
- En el backfill 2008-03–2019-12 se consultaron los **48 cierres** y **1.683 RUN**: **29** cierres
  con operaciones reales (**921 filas**), **19** cierres sin operaciones y **125** plantillas
  excluidas. No hubo cierres fallidos. El control conserva las huellas SHA-256 de las páginas
  descargadas.
- Junio de 2026 conserva sus **40 operaciones**; la corrección es histórica.

## Texto Unicode en pactos

Se encontró la variante `Larra�Vial S.A.Corredora de Bolsa` en `fi_pactos`, junto con otras
formas dañadas o inconsistentes del nombre. El Parquet y el JSON se publican en UTF-8; el
carácter `�` ya estaba dentro del dato recibido y no se puede recuperar cambiando la codificación
del archivo: la lectura de la página ahora prueba el charset declarado, UTF-8, cp1252 y latin-1
(reparando el mojibake cuando corresponde) y el carácter sólo se restituye cuando hay reconstrucción
verificada. El RUT de contraparte `80.537.000-9` permite identificarla sin ambigüedad con el
padrón de corredoras CMF: `LARRAIN VIAL S.A. CORREDORA DE BOLSA`.

Estado del Parquet **publicado** tras la corrección (`scripts/reparar_pactos_fi.py`, idempotente;
una segunda corrida no escribe nada): **1.181 celdas en 14 archivos**, repartidas así.

- `contraparte`: **157** celdas — 12 con `�`, 1 vacía completada con el padrón y 144 grafías del
  mismo RUT unificadas al nombre canónico (variantes de Larraín Vial, `EUROAMERICA C. DE B.`,
  `CONSORCIO FINANCIERO`, `MBI CB`/`MBICB`, variantes de `BCI` y la forma corta de Larraín Vial
  Activos). No se fusionaron entidades distintas que comparten RUT por un rebautizo
  (p. ej. IM Trust / Credicorp) ni se reescribieron los casos en que el RUT y el nombre del padrón
  no coinciden.
- `isin`: **896** centinelas `NA`/`N/A` publicados como vacío (la convención de la casa para
  «sin dato»); lo mismo aplica a `nemotecnico` y `nombre_emisor`.
- `rut_contraparte`: **118** DV pegados descartados (`805370009` → `80537000`).
- `nemotecnico` + `nombre_emisor`: **2 + 8** celdas con `�` reparadas (`FNBNS-…`, `QUIÑENCO`,
  `Banco Itaú`, `Compañía General de Electricidad`).

Los **1.698 registros** y sus importes no cambian. El parser aplica las mismas reglas en futuras
descargas y una regresión comprueba el RUT, las grafías y la lectura de nombres con tildes en UTF-8.
Si queda un `�` sin reconstrucción verificada, el trimestre lo anota en los avisos en vez de
sustituirlo a ciegas.

La búsqueda también detecta caracteres `�` en nemotécnicos, emisores y contrapartes de otras tablas
FI (cartera nacional y extranjera, método de participación, futuros/forwards y opciones). No se
sustituyen globalmente —no siempre hay una clave o padrón suficiente para reconstruir el texto— y el
Parquet ya publicado de esas tablas **no** se reescribió en esta corrección; el extractor ahora los
reporta en los avisos de cada trimestre.

## Interpretación de ceros: qué sí y qué no se debe eliminar

### Estados financieros `fi_balance` / `fi_resultados`

Hay muchas líneas contables con importe cero: **675.571 de 985.908** filas de balance y **745.746
de 1.164.000** de resultados. Eso no significa que el extractor haya rellenado importes ausentes.
El XML FIEF de origen trae explícitamente, por ejemplo, `<Cuenta ...>0</Cuenta>` en la muestra
`fi/tests/fixtures/7002_2026-06.xml`. El parser conserva ese entero; además, exige la presencia de
cada cuenta del catálogo y rechaza una cuenta ausente en vez de inventarle un cero. Por tanto, un
cero en `valor_miles_mf` es el dato informado por la fuente para esa cuenta/contexto.

### Carteras instrumentales

También hay filas con valoración cero que conservan otros atributos reales (instrumento, emisor,
cuotas/unidades, contraparte o fechas). En el barrido local se contaron 790 valorizaciones cero en
cartera nacional, 1.364 en cartera extranjera, 887 filas de método de participación con todos los
campos monetarios nulos/cero, y 3 de opciones. Además, hay dos filas de swaps de 2025-12 con
contrapartes ITAU y SCOTIABANK y todas sus métricas numéricas en cero; y una inversión de Serendip
Investment Limited en 2021-12 con todas sus métricas numéricas en cero.

Estas filas se **conservaron**: sus identificadores/contrapartes no son rótulos de plantilla, y un
importe cero, incluso cuando todos los importes son cero, no prueba por sí solo que una fila sea
ficticia. Los informes HTML originales de esos casos no están versionados junto a los Parquet, así
que requieren cotejo adicional con la fuente antes de reclasificarlos. En cambio, `fi_pactos` sí
tenía 18 filas que reunían simultáneamente campos genéricos, RUT de plantilla y métricas en cero;
esa firma justifica su exclusión.

## Verificación

```bash
python -m unittest fi.tests.test_actualizar_carteras -v
python -m unittest discover -s fi/tests -v
python scripts/build_download_catalog.py --check
```

La suite FI ejecutada en esta revisión terminó con **120 pruebas aprobadas** (**23** de
`fi/tests/test_actualizar_carteras.py`, que incluyen las regresiones de decodificación, centinelas,
grafías de contraparte y Parquet publicado) y `scripts/build_download_catalog.py --check` quedó al
día tras regenerar el catálogo. La salida vacía de
`bienes_raices/_vacio.parquet` se conserva como tabla sin filas publicadas; por sí sola no demuestra
exposición inmobiliaria igual a cero.

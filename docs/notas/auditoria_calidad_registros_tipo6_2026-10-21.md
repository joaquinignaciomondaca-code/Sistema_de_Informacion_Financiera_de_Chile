# Auditoría de calidad: registros tipo 6 de la Circular 1835

**Fecha:** 2026-10-21  
**Alcance:** ingestión, normalización, publicación Parquet, linaje, validaciones y exposición en la web de los registros tipo `6` hallados en B.11 (archivos E) y B.14 (archivos G), más las salidas reprocesadas para 2024-12 a 2026-09.  
**Fuente:** CMF, [Anexos Técnicos de la Circular 1835](https://www.cmfchile.cl/sitio/seil/software-manual/sgsci/Anexos_Tecnicos_Circular_N1835.pdf).

## Dictamen ejecutivo

La publicación de la tabla `registros_tipo6` y el reproceso histórico pasaron los controles de lectura, esquema Parquet, conteos y coherencia de manifiestos. Se conservaron los registros sin asignarles semántica no documentada y se reescribieron los cierres afectados para recuperar también los demás detalles de archivos que antes se excluían por el tipo 6.

La auditoría detectó además una brecha de integración: el conjunto estaba en Parquet y en `data_manifest.json`, pero no figuraba inicialmente en el catálogo de descargas, en la lista de vistas DuckDB ni en todos los componentes de exploración/documentación. La brecha se corrigió en esta rama: se registró en vocabulario, vista DuckDB, catálogo de descargas, visor, consultas sugeridas, diccionario de columnas y diagrama ER. La corrida posterior de CI **39650264525** pasó en 52 segundos, con 0 meses pendientes, 0 errores fatales y 0 archivos excluidos.

**Estado global:** aprobado con observaciones y pendientes menores de linaje/versionado descritos abajo. No es una validación semántica del tipo 6 ni una certificación de la CMF.

## Resultados de perfilado

- Cobertura publicada: **22 de 22 cierres**, desde 2024-12 hasta 2026-09.
- Filas: **66**; 22 de B.11 y 44 de B.14. Todas corresponden al sector `generales` en los ZIP examinados.
- Distribución: tres líneas por cierre (una B.11 y dos B.14).
- Largo fijo: B.11 = **178** caracteres (22/22); B.14 = **300** caracteres (44/44).
- Todas las líneas empiezan con `6`; las posiciones 2–7 contienen `000002` en los 66 casos y el resto son espacios. Se registra como perfil observado, **no** como interpretación de negocio.
- Nulos: **0** en las nueve columnas.
- Repeticiones: **0** duplicados por `(periodo, sector, archivo_origen)` y **0** líneas idénticas repetidas con el mismo contexto.
- `largo_registro` coincide con la longitud de `registro_original` en todas las filas. Las posiciones internas no se convierten a campos con nombre porque la ficha consultada no documenta ese layout.

## Controles de consistencia ejecutados

1. Los archivos Parquet enumerados por cada manifiesto existen; la suma de sus metadatos de filas coincide con `total_records` en **todas las tablas de seguros**.
2. Los períodos en los manifiestos de tabla coinciden con los períodos que registra el manifiesto principal. Los manifiestos de la tabla nueva declaran 66 filas y los tres Parquet anuales suman 66.
3. Los 22 cierres tienen hashes SHA-256 de los ZIP de ambos sectores en el manifiesto principal.
4. No quedan exclusiones históricas por `tipo de registro '6' desconocido`.
5. El catálogo de descargas publica el conjunto con 66 filas y cobertura 2024-12 a 2026-09; la vista `seguros_registros_tipo6` apunta al manifiesto correcto.
6. Revisión de contenido de las 66 líneas: no se observaron letras ni campos de identificación personal; el contenido visible es numérico y relleno con espacios. Esto es un perfil de la muestra auditada, no una garantía para futuras publicaciones.

## Validaciones automatizadas

- GitHub Actions **[run 39645086998](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/39645086998)**: éxito; pruebas de lector, diagnóstico y publicación; reproceso de 22 cierres completado.
- `seguros.tests.test_formato_1835`: OK; muestras reales disponibles, cuadraturas y exclusión de entradas defectuosas.
- `seguros.tests.test_inventario_1835`: OK; cobertura del inventario oficial.
- `seguros.tests.test_registros_2024`: OK; prueba sintética de lectura, preservación de tipo 6 y escritura Parquet en B.11 y B.14.
- `unittest` de vistas, diagnóstico, escritura estable y privacidad: **30 pruebas, OK**.
- `scripts/audit_web_full.py`: sintaxis JS válida; vistas y archivos enlazados; catálogo del visor y consultas SQL comprobados; columnas declaradas cotejadas con Parquet.
- `scripts/audit_navigation.py`, `scripts/normalizar_vocabulario.py --check`, `scripts/build_download_catalog.py --check` y `seguros.scripts.diccionario_1835 --check`: OK después de integrar la ampliación de interfaz.
- GitHub Actions **[run 39658191864](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/39658191864)**: sonda acotada de DNS/TCP/TLS/TTFB y transferencia CMF; conectividad actual satisfactoria.
- GitHub Actions **[run 39659027638](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/39659027638)**: perfil de cuatro ZIP representativos, terminado con éxito; no publicó datos ni conservó payloads fuente.
- GitHub Actions **[run 39660648174](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/39660648174)**: perfil de los cuatro ZIP G restantes, terminado con éxito; no publicó datos ni conservó payloads fuente.

## Observaciones y riesgos residuales

### 1. Alertas de archivos ajenas al tipo 6

En la primera lectura del manifiesto aparecían **nueve entradas**, pero una era duplicada: el mismo archivo C de vida figuraba dos veces para el mismo tipo `x`, una con el mensaje antiguo sin largo y otra con el mensaje completo. La auditoría posterior detectó que el código acumulaba exclusiones históricas y variantes del mismo aviso al reconstruir un período. Se cambió para que la lista refleje el resultado de la lectura completa más reciente y se depuró la entrada duplicada del manifiesto. Quedan **ocho casos distintos**: seis tipo 4 en archivos G de vida, un tipo `x` en un archivo C de vida y una línea truncada en un archivo A de generales. El proceso mantiene el comportamiento fail-closed y no los incorpora como filas válidas. Los seis tipo `4` son del archivo G `g202604v.76282191` a `g202609v.76282191` (300 caracteres esperados); el tipo `x` está en `c202505v.99289000` (138 caracteres esperados); y la línea de 571 frente a 572 caracteres corresponde a `a202505g.99017000` de `generales`.

### 2. Caracterización de las ocho exclusiones

Se compararon las estructuras con el manual CMF incluido en el repositorio. En la sección B.8 (archivo C) se describen registros tipo 1, 2 y 3, no tipo `x`; en B.14 (archivo G), las estructuras documentadas son tipos 1 a 3, no tipo `4`. Por tanto, no hay soporte documental para incorporar esos registros ni para asignarles campos o semántica. La fila truncada del archivo A tampoco satisface el largo fijo y no se corrigió ni completó.

La primera ejecución de perfilado tenía un escape doble en el separador LF: concatenó artificialmente las líneas y sus máscaras se descartaron. Corregí el separador y repetí la prueba. La sonda corregida perfiló cuatro ZIP representativos (A, C y los G de abril y septiembre); una segunda inspeccionó los cuatro G de mayo a agosto. En total se leyeron **ocho ZIP distintos**, una descarga por ZIP, con los sectores correctos y sin persistir payloads. Los resultados confirmaron:

- **Generales, 2025-05, A `a202505g.99017000`:** 8 líneas; 7 de 572 caracteres y 1 de 571 (línea 2). SHA-256 del ZIP `94355cd83b08f4ecb71415669ee91c1dfb2a12e44ce23bbabd4b328d2f4ebf43`; del miembro `454db90dfec398227a11043090ef9861a30743c541cff7f5b0813d4ccf1f0cd8`.
- **Vida, 2025-05, C `c202505v.99289000`:** 36 líneas de 138 caracteres; una línea tipo `x` (línea 1). SHA-256 del ZIP `9aa54067a771de92e3c1d05c0f18d4e5512b5de54ca7b4f4fdc56149ca596aaf`; del miembro `ea2c1f8e42c7f18aaa54cc45dda2c0314059c3a026d0227d6d594869b6a9050f`.
- **Vida, archivos G `g202604v.76282191` a `g202609v.76282191`:** los seis ZIP mensuales (2026-04 a 2026-09) contienen 2 líneas de 300 caracteres: una tipo `4` y una tipo `3`. La línea tipo `4` está en la posición 1 y tiene exactamente la misma máscara de caracteres en los seis meses. SHA-256 ZIP / miembro por período:
  - 2026-04: `78429066ef65e17510d22902d302d2b9a3b0276454611211f7a2ff7b07626ef7` / `014753ef214de0945e06263004c1f0d7a60453aeadd3a9d075b9a36c5752b5ef`.
  - 2026-05: `4bd230dab954565feffee40c4ddc00f1f46ec3afc6dfd6a778fdefbf2116327b` / `0c383fcbbcbdc66ed9e02c94a84d50a40167a2cf153443d5f01b0b794818b873`.
  - 2026-06: `19909b40d045801d1adf31b5c53402e436e12db89abe7521ff65811641468744` / `0d36b0fe6117e799203d3e2418a48d688c5183076dec6b44a113c4a22bb92a4c`.
  - 2026-07: `e87ed57ba3e84b5a1306ede332bc9ab9f2ab5be5e0210c284fa504752f9972d2` / `ac467b244965411c470315cc3627f03c65d486ebd60f489fad072f73db239786`.
  - 2026-08: `9b8826b4774eb845c77609aa861dc3b9c418310874dd7e93a60ad059b4f2dfb4` / `c02078d718356f9e5e0ff0e9328d92c0020153f3b876b6e6309a8e45c0f391b9`.
  - 2026-09: `03d7f138e80b3f59eccfd6dd86e04ad5b0373f7159c6f3c449ce3b9128c87434` / `aaad7c69139d6fb5e581ca32c8a8557bfd1a895002e259a2a81a1155498108ce`.

Las máscaras de caracteres de los seis registros tipo `4` son iguales; se conservaron solo máscaras, largos, conteos y hashes, no valores de registros. No se asignó significado a sus posiciones. Estos perfiles confirman que los tipos `x` y `4` no están descritos por los formatos consultados y que el registro A corto incumple el largo fijo; los ocho casos siguen excluidos.

**Resultado de la investigación de los timeouts:** la repetición controlada de conectividad en Actions obtuvo HTTP 200 de `archi`, con respuesta `1`. También funcionó la descarga ZIP por `curl` y por el mismo `_get` de Python que usa el publicador. En la medición de `curl`, DNS tomó 0,15 s, TCP 0,27 s, TLS 0,39 s, pero el primer byte tardó 18,19 s; el ZIP de 13.773.609 bytes terminó en 20,84 s. Las ocho descargas Python de perfilado completaron en 12,6–22,4 s. Esto apunta a latencia/variabilidad del lado del endpoint CMF al preparar la descarga, no a un fallo persistente de DNS, conexión, TLS, sector o nombre de archivo. No quedó una traza de fases del run anterior que permita probar la causa exacta de aquellos `URLError: timed out`; por eso se registra como una intermitencia observada, no como causa raíz demostrada. Las sondas temporales se retiraron del workflow tras obtener evidencia, y el parser permanece fail-closed.

### 3. Trazabilidad de versión de la fuente

Al comparar el manifiesto anterior a la reconstrucción con el publicado por Actions, cambiaron los hashes de **12 ZIP** en **10 cierres**: 2025-07, 2025-08, 2025-10, 2025-11, 2026-01 (ambos sectores), 2026-03, 2026-06, 2026-07, 2026-08 y 2026-09. El manifiesto conserva el hash vigente, pero el ZIP histórico anterior y un registro de diferencias de datos no se archivan aquí. Por tanto, el estado actual es trazable por hash, pero no ofrece una historia de revisiones reproducible de esas fuentes.

### 4. Linaje a nivel de línea

Cada fila guarda el nombre del archivo, y el manifiesto del período guarda el SHA-256 del ZIP por sector. No se persisten todavía el número ordinal de línea ni el SHA-256 del miembro del ZIP. En los datos actuales hay una sola línea tipo 6 por archivo, sin colisiones; para blindar futuras fuentes con varias líneas tipo 6 en un archivo, conviene añadir `numero_linea` y `sha256_archivo` o guardar una copia inmutable del ZIP.

### 5. Preservación de bytes y alcance de la normalización

`registro_original` es texto decodificado y conserva espacios y largo. Las 66 líneas examinadas son ASCII, así que en esta muestra no hay pérdida por decodificación. La tabla normaliza el contexto relacional (período, sector, aseguradora, archivo y tipo) y conserva el payload opaco; no es todavía una descomposición posicional campo por campo. Si futuras líneas incluyen bytes no ASCII, o si se acuerda una ficha para el registro, será necesario versionar la codificación y/o guardar el payload binario original antes de interpretarlo.

## Acciones recomendadas

1. Mantener los controles de largo, tipo de registro, conteos y manifiestos en cada ejecución.
2. Incorporar número de línea y hash del archivo miembro (o archivo fuente inmutable) si se exige trazabilidad transaccional fuerte.
3. Registrar cambios de hashes de ZIP como revisiones de fuente y conservar diffs de filas al reconstruir períodos.
4. Mantener los ocho casos excluidos. La caracterización cubre los seis meses con tipo `4` y confirma la misma máscara en todos; no ampliar el parser ni asignar semántica sin documentación oficial.
5. Mantener `registro_original` aun si se agrega una proyección posicional: la fila fuente íntegra sirve como evidencia y permite reprocesar el contenido.

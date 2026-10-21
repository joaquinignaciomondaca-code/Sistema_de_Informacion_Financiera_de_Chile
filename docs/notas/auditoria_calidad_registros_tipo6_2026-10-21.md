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
- `scripts/audit_navigation.py`, `scripts/normalizar_vocabulario.py --check`, `scripts/build_download_catalog.py --check` y `seguros.scripts.diccionario_1835 --check`: deben permanecer verdes después de integrar esta ampliación de interfaz.

## Observaciones y riesgos residuales

### 1. Alertas de archivos ajenas al tipo 6

En la primera lectura del manifiesto aparecían **nueve entradas**, pero una era duplicada: el mismo archivo C de vida figuraba dos veces para el mismo tipo `x`, una con el mensaje antiguo sin largo y otra con el mensaje completo. La auditoría posterior detectó que el código acumulaba exclusiones históricas y variantes del mismo aviso al reconstruir un período. Se cambió para que la lista refleje el resultado de la lectura completa más reciente y se depuró la entrada duplicada del manifiesto. Quedan **ocho casos distintos**: seis tipo 4 en archivos G de vida, un tipo `x` en un archivo C de vida y una línea truncada en un archivo A de generales. El proceso mantiene el comportamiento fail-closed y no los incorpora como filas válidas.

### 2. Trazabilidad de versión de la fuente

Al comparar el manifiesto anterior a la reconstrucción con el publicado por Actions, cambiaron los hashes de **12 ZIP** en **10 cierres**: 2025-07, 2025-08, 2025-10, 2025-11, 2026-01 (ambos sectores), 2026-03, 2026-06, 2026-07, 2026-08 y 2026-09. El manifiesto conserva el hash vigente, pero el ZIP histórico anterior y un registro de diferencias de datos no se archivan aquí. Por tanto, el estado actual es trazable por hash, pero no ofrece una historia de revisiones reproducible de esas fuentes.

### 3. Linaje a nivel de línea

Cada fila guarda el nombre del archivo, y el manifiesto del período guarda el SHA-256 del ZIP por sector. No se persisten todavía el número ordinal de línea ni el SHA-256 del miembro del ZIP. En los datos actuales hay una sola línea tipo 6 por archivo, sin colisiones; para blindar futuras fuentes con varias líneas tipo 6 en un archivo, conviene añadir `numero_linea` y `sha256_archivo` o guardar una copia inmutable del ZIP.

### 4. Preservación de bytes y alcance de la normalización

`registro_original` es texto decodificado y conserva espacios y largo. Las 66 líneas examinadas son ASCII, así que en esta muestra no hay pérdida por decodificación. La tabla normaliza el contexto relacional (período, sector, aseguradora, archivo y tipo) y conserva el payload opaco; no es todavía una descomposición posicional campo por campo. Si futuras líneas incluyen bytes no ASCII, o si se acuerda una ficha para el registro, será necesario versionar la codificación y/o guardar el payload binario original antes de interpretarlo.

## Acciones recomendadas

1. Mantener los controles de largo, tipo de registro, conteos y manifiestos en cada ejecución.
2. Incorporar número de línea y hash del archivo miembro (o archivo fuente inmutable) si se exige trazabilidad transaccional fuerte.
3. Registrar cambios de hashes de ZIP como revisiones de fuente y conservar diffs de filas al reconstruir períodos.
4. Investigar por separado las nueve alertas aún activas; no ampliar el parser con semánticas no documentadas.
5. Mantener `registro_original` aun si se agrega una proyección posicional: la fila fuente íntegra sirve como evidencia y permite reprocesar el contenido.

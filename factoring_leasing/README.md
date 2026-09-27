# Factoring y Leasing — publicación limitada

Por decisión editorial, **únicamente se conserva la Lista de Entidades**: `docs/outputs/factoring_leasing/factoring_leasing_maestro.{json,parquet}` (28 registros). Se retiraron los balances trimestrales, la nota de efectivo y la nota de cartera/morosidad, tanto JSON como Parquet, del sitio y del repositorio de datos publicados. Se eliminaron sus accesos del explorador, visor, diccionario, diagrama, exportador, vistas DuckDB y manifiesto. No presentar esos datos como disponibles.

Los scripts históricos se mantienen solo para investigación, pero sus funciones de publicación fallan explícitamente. Una reextracción futura requiere auditoría y decisión de publicación propia; no se reponen automáticamente los archivos retirados. `python factoring_leasing/scripts/audit_factoring_leasing.py` comprueba unicidad, módulo 11 y equivalencia JSON/Parquet del listado, **no** certifica por sí mismo que la identidad, el estado o el universo estén verificados frente al padrón CMF vigente. La lista existente no fue alterada.

## Nueva revisión estructurada (sin publicación)

`python factoring_leasing/scripts/audit_structured_sample.py` compara dos muestras (un factoring y un leasing) del archivo público de texto delimitado de CMF con sus fichas HTML, y ya fue **aprobado** en la corrida Actions 36337279448. Rechaza falta de RUT/DV, nombre, período, tipo de balance, unidad, cuentas únicas, coincidencia exacta y cuadre. El informe queda en `.local-data/factoring_leasing_muestra/` y el workflow `factoring_leasing_sample.yml` lo sube como artifact privado; jamás modifica `docs/outputs`. Las fichas ofrecen además XBRL y PDF, cuyo contenido **no** está todavía cotejado. Solo después de una muestra aprobada podrá proponerse una publicación limitada.

## Publicación acotada vigente

`python factoring_leasing/scripts/publish_structured_sample.py --report .local-data/factoring_leasing_muestra/cotejo.json`
escribe `docs/outputs/factoring_leasing/factoring_leasing_eeff_muestra_cmf.parquet` con **dos filas** y falla si el reporte no proviene del run aprobado, si cambia cualquier cifra, si aparece una tercera fila, si la unidad no es miles de CLP, si el balance no cuadra o si falta la advertencia de alcance. Esa muestra se presenta en el sitio como «muestra cotejada CMF», no como el sector. El resto de los balances sigue retirado y los XBRL/PDF siguen sin cotejar.

## Estado de resultados (tabla separada)

A solicitud del usuario, `factoring_leasing.resultados_muestra_cmf` contiene solamente dos cuentas de resultados **acumulados desde enero**, cotejadas en [Actions 36337715177](https://github.com/joaquinignaciomondaca-code/monitor-financiero-chile/actions/runs/36337715177) para las mismas dos entidades y períodos. El balance permanece aparte en `factoring_leasing.eeff_muestra_cmf`, con sus cuatro cuentas y su cotejo original. `python factoring_leasing/scripts/publish_income_sample.py --report .local-data/factoring_leasing_muestra/cotejo_resultados.json` exige valores exactos, unidad, identidades, advertencia, corrida y coherencia de las cuatro cifras del balance original. No es el estado de resultado completo ni el sector.

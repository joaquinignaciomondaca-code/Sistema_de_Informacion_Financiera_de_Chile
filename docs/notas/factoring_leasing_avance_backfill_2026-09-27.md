# Avance real del backfill IFRS Factoring y Leasing (2026-09-27)

Corrida [36338897994](https://github.com/joaquinignaciomondaca-code/monitor-financiero-chile/actions/runs/36338897994) en el PR #3; estado de la extracción **`parcial_con_errores_sin_publicar`** pese a que el job terminó exitosamente (ese estado significa que se conservaron las filas obtenidas, no que el histórico esté aprobado).

- Índice CMF: **70 cierres trimestrales, 2009-03 a 2026-06**.
- En caché/artefacto privado temporal: **69/70 cierres**, **28.911 filas de cuentas de balance (ESF)** y **21.441 de resultados (ER)**. Son *cuentas individuales*, no 28.911 balances ni 21.441 estados de resultados.
- Catálogo de la carpeta Factoring y Leasing: **28 RUT** (9 Leasing, 9 Factoring, 8 Ambas, 2 Automotriz); **24 RUT** aparecen en al menos un período del TXT. No hay filas para **76562786-9, 96611310-3, 96720830-2 y 96805850-9** en los 69 cierres accesibles. Ausencia en esta fuente ≠ ausencia de EEFF en otras fichas/PDF ni inexistencia de la entidad.
- **2009-03** sigue pendiente: el endpoint CMF devolvió HTML/no entregó TXT (la consulta externa también falló con HTTP 500). No se convirtió en período vacío ni se afirmó que está completo. Se reintentará al ejecutar otra vez el workflow.
- **2.426 importes no enteros** preservados con el texto original y valor numérico nulo, sin convertir a cero. **899 repeticiones de cuenta/contexto** preservadas por ordinal, sin sumarlas. Estos conteos requieren estudio antes de crear una serie analítica.

El workflow `factoring_leasing_backfill.yml` recupera el estado desde la caché de Actions de **esta rama**, consulta primero los trimestres nuevos y después vuelve a intentar los fallidos. Publica un resumen en las anotaciones del job y guarda un artifact por 30 días. **GitHub solo ejecuta `schedule` automáticamente en la rama por defecto (`main`)**: mientras el PR #3 permanezca abierto, la programación diaria declarada en el YAML **no corre sola**; `push` y `workflow_dispatch` en esta rama sí funcionan. No fusionar un PR con retiros/cambios de web sin revisarlo. La caché/artefacto es temporal y no sustituye un almacenamiento duradero aprobado.

**Nada de esta serie masiva se publica en la web.** `docs/outputs` mantiene las dos filas cotejadas de prueba. La publicación del histórico requiere resolver unidades, duplicados, cobertura y verificar cifras de otros períodos/entidades contra fichas CMF antes de reemplazar las muestras.

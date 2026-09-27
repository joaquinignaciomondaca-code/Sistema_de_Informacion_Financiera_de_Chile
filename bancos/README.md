# Bancos — estado de publicación

**Publicado en el sitio:** `bancos_maestro` (40 códigos de un catálogo local, entre instituciones históricas, filiales y agregados) y `bancos_repos_saldos_series` (saldos de pactos provenientes de un Excel local, **pendientes de auditoría**). Los nombres, RUT y estados del catálogo todavía requieren cotejo registral con CMF. REPO no es volumen transado del mes: `total_transado_mm_usd` es la suma de dos saldos.

El 27-09-2026 se retiraron del sitio y del repositorio de datos publicados los balances, estados de resultados y derivados anteriores para extraerlos nuevamente desde cero. **No volver a publicarlos con los extractores actuales sin revisión:** los balances presentan rupturas de escala, conversiones USD con tipos de cambio fijos, y los derivados mezclan dimensiones/unidades de series BCCh. Los scripts y catálogos en `bancos/scripts/` y `bancos/derivados_otc/` quedan sólo como material de investigación; no constituyen una extracción validada ni un flujo automatizado incremental. Véase [auditoría bancaria](AUDITORIA_BANCOS_2026-09-27.md) para las comprobaciones, fuentes y criterios de nueva publicación.

El Excel `repo_banco.xlsx` que usa `02_extract_bancos_repos_series.py` no está en el repositorio. No regenerar REPO sin el archivo, su procedencia y cotejo con las cuentas CMF.

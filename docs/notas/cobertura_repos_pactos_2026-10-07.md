# Cobertura de operaciones REPO (pactos) — revisión 2026-10-07

En esta nota, **REPO** significa operación de compra/venta con pacto; no repositorios de código.
La revisión cruza los manifiestos publicados en `docs/outputs/`, las corridas programadas y el backfill histórico de pactos en GitHub Actions (2026-10-07).

## Estado publicado

| Industria | Tabla | Frecuencia | Último período | Filas del último período | Filas publicadas | Estado de la revisión |
|---|---|---|---|---:|---:|---|
| Compañías de seguros | `seguros_pactos` | Mensual | 2026-08 | 155 | 11.153 | Publicado hasta agosto; la corrida del 2026-10-04 terminó bien, con diagnóstico sin problemas, y no añadió un período nuevo. |
| Fondos de inversión | `fi_pactos` | Trimestral | 2026-06 | 40 | 1.716 | Publicado desde 2012-03. El backfill histórico de 2026-10-07 concluyó correctamente: 48/48 cierres consultados entre 2008-03 y 2019-12 quedaron completos, sin cierres fallidos. Por prudencia analítica, los dos últimos períodos disponibles se tratan siempre como cautelares por posible rezago de carga de la fuente (hoy 2026-03 y 2026-06). Los registros se conservan y esto no se atribuye a una falla del extractor; la ventana se desplaza al publicarse un nuevo trimestre. El cierre 2026-09 aún está dentro del plazo de presentación. |
| Fondos mutuos | — | — | — | — | — | No hay una tabla independiente de pactos/REPO en el extractor actual. No se debe interpretar como exposición cero. |

Los manifiestos muestran secuencias continuas, sin huecos de calendario dentro de los rangos con datos: seguros tiene **118 períodos mensuales** (2016-11–2026-08) y FI **58 cierres trimestrales con operaciones** (2012-03–2026-06). El manifiesto de pactos registra además **74 cierres sondeados** (2008-03–2026-06). En la auditoría histórica se consultaron los **1.683 RUN** del registro en cada uno de los 48 cierres de 2008-03–2019-12: 32 cierres tuvieron operaciones reales (**939 filas**), 16 no devolvieron operaciones y se excluyeron **107 filas centinela**; no hubo cierres fallidos. Por eso esos 16 períodos son sondeos completos sin operaciones, no huecos de calendario. El conteo representa filas publicadas, no operaciones únicas deduplicadas por folio/contrato. La cobertura comprobada empieza en 2008-03; no se extrapola una ausencia anterior. En FI, los dos cierres más recientes se consideran cautelares aunque ya figuren en el manifiesto.

## Fuentes, definiciones y unidades

- **Seguros (`seguros_pactos`)**: Circular CMF 1835; reportes mensuales de compañías de vida (`CSVID`) y generales (`CSGEN`). La tabla contiene compras/ventas con pacto, fechas, contraparte y activo objeto. La valorización contable y el interés devengado se publican en **miles de pesos (`M$`)**; `valor_nominal` conserva la unidad/moneda del instrumento. Fuente del extractor: `seguros/scripts/actualizar_carteras.py`; workflow: `seguros_carteras.yml`.
- **Fondos de inversión (`fi_pactos`)**: informes IFRS trimestrales de la CMF. Registra `VRC` (venta con compromiso de retrocompra) y `CRV` (compra con compromiso de retroventa), con contraparte, tasa, instrumento y valorizaciones. Los importes `*_miles_mf` son miles de la moneda funcional del fondo; no se deben sumar entre monedas sin convertirlas. La CMF presenta carteras trimestrales con plazos de 60 días (90 para el cierre anual); el publicador espera 75/100 días y valida cobertura antes de publicar. Fuente del extractor: `fi/scripts/actualizar_carteras.py`; workflow: `fi_carteras.yml`.
- **Fondos mutuos (`ffmm`)**: la extracción de Circular 1333 publica `NACI`, `EXTR`, `FUTU` y `OPCI` (cartera nacional/extranjera, futuros/forwards y opciones), pero no una salida separada `pactos`. Por ello el sistema no puede cuantificar REPO de FFMM a partir de sus tablas actuales; la ausencia de una tabla específica no prueba ausencia económica de estas operaciones.

## Consultas de cobertura

```sql
SELECT periodo,
       count(*) AS filas,
       count(DISTINCT rut_aseguradora) AS companias
FROM seguros_pactos
GROUP BY periodo
ORDER BY periodo DESC
LIMIT 12;
```

```sql
SELECT periodo,
       count(*) AS filas,
       count(DISTINCT run_fondo) AS fondos
FROM fi_pactos
GROUP BY periodo
ORDER BY periodo DESC
LIMIT 12;
```

No se agrega el valor monetario de ambas tablas en una cifra común: seguros reporta valorizaciones en M$ CLP y FI en miles de la moneda funcional de cada fondo.

## Evidencia de frescura

- Manifiesto seguros: `docs/outputs/seguros/manifest.json`, `updated_at=2026-09-28T17:19:17Z`, período más reciente `2026-08`.
- Manifiesto específico FI pactos: `docs/outputs/fi/pactos/manifest.json`, `updated_at=2026-10-07T04:13:38Z`, **1.716 filas**, 58 períodos con operaciones (2012-03–2026-06) y 74 cierres sondeados (2008-03–2026-06).
- Control histórico FI: `docs/outputs/fi/pactos/historico_control.json`, `updated_at=2026-10-07T04:13:38Z`; 48/48 cierres completos y `fallidos={}`.
- [Corrida seguros del 2026-10-04](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/37222435865): éxito; el diagnóstico reportó cero problemas y no se publicó un período nuevo.
- [Corrida programada de carteras FI del 2026-10-04](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/37224800560): éxito; cero trimestres nuevos.
- [Backfill histórico de pactos FI del 2026-10-07](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/37568576713): éxito, incluidos descarga, validación, publicación y confirmación.

El manifiesto de seguros no cambió desde septiembre porque no se publicó un mes nuevo; el de pactos FI sí se actualizó con el backfill histórico. Esto no implica que se haya añadido un trimestre reciente: 2026-09 todavía está dentro del plazo de presentación y los cierres FI 2026-03 y 2026-06 se mantienen como cautelares por posible rezago de la fuente.

# Cobertura de operaciones REPO (pactos) — revisión 2026-10-07

En esta nota, **REPO** significa operación de compra/venta con pacto; no repositorios de código.
La revisión cruza los manifiestos publicados en `docs/outputs/` con las últimas corridas programadas de los extractores en GitHub Actions (2026-10-04).

## Estado publicado

| Industria | Tabla | Frecuencia | Último período | Filas del último período | Filas históricas | Estado de la revisión |
|---|---|---|---|---:|---:|---|
| Compañías de seguros | `seguros_pactos` | Mensual | 2026-08 | 155 | 11.153 | Publicado hasta agosto; la corrida del 2026-10-04 terminó bien, con diagnóstico sin problemas, y no añadió un período nuevo. |
| Fondos de inversión | `fi_pactos` | Trimestral | 2026-06 | 40 | 777 | Publicado hasta junio; la corrida del 2026-10-04 terminó bien y reportó 0 trimestres nuevos. El cierre 2026-09 aún está dentro del plazo de presentación. |
| Fondos mutuos | — | — | — | — | — | No hay una tabla independiente de pactos/REPO en el extractor actual. No se debe interpretar como exposición cero. |

Las series de seguros y FI cubren, respectivamente, **118 períodos mensuales** entre 2016-11 y 2026-08 y **26 períodos trimestrales** entre 2020-03 y 2026-06. En ambos casos el conteo representa filas publicadas, no operaciones únicas deduplicadas por folio/contrato.

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
- Manifiesto FI: `docs/outputs/fi/manifest.json`, `updated_at=2026-09-28T17:20:36Z`, período más reciente `2026-06`.
- [Corrida seguros del 2026-10-04](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/37222435865): éxito; el diagnóstico reportó cero problemas y no se publicó un período nuevo.
- [Corrida de carteras FI del 2026-10-04](https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile/actions/runs/37224800560): éxito; cero trimestres nuevos.

Los manifiestos registran cuándo cambió lo publicado; que no hayan cambiado desde septiembre no significa que el flujo esté detenido. A la fecha de revisión, las dos corridas más recientes terminaron correctamente, aunque ninguna añadió un período nuevo.

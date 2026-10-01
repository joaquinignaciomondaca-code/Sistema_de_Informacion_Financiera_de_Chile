# Módulo Cajas de Compensación de Asignación Familiar (CCAF)

> **Estado al 2026-10-01.** En la web hay tres tablas: `ccaf_maestro` (lista de entidades) y
> `ccaf_balance` / `ccaf_resultados`. Estas dos últimas las publica automáticamente
> `pipelines/ifrs_sectores/actualizar.py` (workflow `ifrs_sectores.yml`, días 2, 12 y 22 de cada mes)
> desde el TXT IFRS trimestral de la CMF, la exportación de los estados financieros XBRL que envían
> las cajas (Los Andes, La Araucana, Los Héroes y 18 de Septiembre, desde 2010-06).
>
> Hasta el 2026-09-28 este módulo tenía otra vía, manual: extractores de PDF/OCR sobre las memorias
> de la SUSESO que producían `ccaf_caratula_totales` (266 balances), la Nota 8 (efectivo, DAP y repos)
> y las colocaciones de crédito social. Esos scripts y tablas **se retiraron** (la serie IFRS de la
> CMF cubre balance y resultados completos, con cuadratura, sin OCR) y esta guía ya no los describe.

## 1. Alcance normativo y universo de entidades

Las CCAF están reguladas primariamente por la **Superintendencia de Seguridad Social (SUSESO)**
(Ley N° 18.833) y, en su calidad de emisoras de bonos y efectos de comercio de oferta pública, por la
**Comisión para el Mercado Financiero (CMF)**.

El universo es de 6 entidades (`ccaf_maestro`):

| Entidad | RUT | Situación |
|---|---|---|
| CCAF Los Andes | 81.826.800-9 | Vigente · informa a la CMF |
| CCAF La Araucana | 70.016.160-9 | Vigente · informa a la CMF |
| CCAF Los Héroes | 70.016.330-K | Vigente · informa a la CMF |
| CCAF 18 de Septiembre (Caja 18) | 82.606.800-0 | Vigente · informa a la CMF (individual: no tiene filiales consolidables) |
| CCAF Gabriela Mistral | 70.017.000-4 | Absorbida por La Araucana · nunca aparece en la fuente |
| CCAF Javiera Carrera | 70.014.300-7 | Absorbida por Los Héroes · nunca aparece en la fuente |

La lista crece sola: una sociedad que, en el último trimestre del TXT, reporta con nombre de caja de
compensación y no está en `ccaf_maestro` se agrega (máximo 10 por corrida; si calzan más, el patrón es
sospechoso y no se agrega nada). El evento queda en `docs/outputs/entidades/novedades_ifrs.json`.

## 2. De dónde sale cada tabla

| Tabla | Fuente | Cómo |
|---|---|---|
| `ccaf_balance` | TXT IFRS de la CMF (`estadisticas_ifrs.php` → `ver_archivo.php?inicio=AAAAMM&termino=AAAAMM`), estados `ESF*` | Un archivo por trimestre con todas las sociedades que envían XBRL; se reparte por sector según el RUT de la lista o el nombre. |
| `ccaf_resultados` | El mismo archivo, estados `ER*` (`ERFG`, `ERNG`, `ERI`) | Importes **acumulados del ejercicio** a cada trimestre. |
| `ccaf_maestro` | `ccaf/scripts/build_ccaf_maestro.py` + altas automáticas del flujo IFRS | Catálogo de las 6 cajas; valida el RUT con módulo 11. |

Los flujos de efectivo (`EFMD`/`EFMI`) viajan en el mismo archivo y **no se publican**.

Fuentes complementarias, no usadas por el pipeline: la ficha de cada entidad en la CMF
(<https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&pestania=3>) y las memorias y
estados financieros auditados en PDF de la SUSESO (<https://www.suseso.cl/609/w3-propertyvalue-10337.html>).

## 3. Cómo se publica y se valida

Es el mismo mecanismo de AGF y securitizadoras (detalle en `pipelines/ifrs_sectores/actualizar.py` y
`pipelines/auto/README.md`):

* **Incremental.** Un trimestre cerrado (más de 150 días) no se vuelve a descargar, salvo que la CMF lo
  reedite: el índice muestra «(actualizado: …)» junto a cada archivo y, si esa fecha es posterior a la
  última lectura, se vuelve a leer. Los trimestres recientes se releen en cada corrida.
* **Compuertas contables antes de publicar:** activos = pasivos + patrimonio (tolerancia de 1.000
  pesos), cobertura mínima de balances verificables (90 %), identidades del estado de resultados y
  guarda contra pérdida de filas por tabla.
* **Auditoría de toda la historia:** `scripts/auditar_eeff_ifrs.py` (corre en `web_audit.yml`)
  recorre los Parquet publicados. Para CCAF: 224 balances, 224 verificables, 0 descuadres.

## 4. Datasets en `docs/outputs/cajas_compensacion/`

| Tabla | Formato | Registros | Cobertura | Descripción |
|---|---|---:|---|---|
| `ccaf_maestro` | Parquet / JSON | 6 | Lista vigente | Catálogo institucional: razón social, RUT, reguladores. |
| `ccaf_balance/<AAAA>.parquet` | Parquet por año | 8.043 | 2010-06 a 2026-06 | Estado de situación financiera cuenta por cuenta, en pesos. |
| `ccaf_resultados/<AAAA>.parquet` | Parquet por año | 5.506 | 2010-06 a 2026-06 | Estado de resultados y resultado integral, acumulado del ejercicio, en pesos. |

Para sumar utilidades sin triplicarlas: `estado_financiero IN ('ERFG','ERNG') AND repeticion = 1`
(la etiqueta «Ganancia (pérdida)» aparece hasta tres veces por estado, siempre con el mismo valor).

## 5. Ejecución y pruebas

```bash
python pipelines/ifrs_sectores/actualizar.py            # necesita red hacia la CMF (la hace Actions)
python -m unittest pipelines.ifrs_sectores.tests.test_actualizar    # sin red
python scripts/auditar_eeff_ifrs.py                     # cuadratura de toda la historia publicada
python scripts/audit_web_full.py                        # integración con la web
```

## 6. Pendiente

La Nota 8 (efectivo, DAP, repos), el crédito social (colocaciones por segmento, deudores previsionales,
provisiones y castigos), los mutuos hipotecarios endosables y los derivados de cobertura dependían de los
extractores de PDF retirados. Si se retoman, hay que reconstruir el extractor desde las memorias de la
SUSESO; no hay un reemplazo en el pipeline automático.

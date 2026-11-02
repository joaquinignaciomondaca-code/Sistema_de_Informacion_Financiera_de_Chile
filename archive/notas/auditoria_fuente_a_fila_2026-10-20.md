# Auditoría de punta a punta: fuente → fila publicada (punto 6)

Fecha: 2026-10-20. Script reproducible: `scripts/auditar_fuente_a_fila.py` (ejecutado sin fallas de integridad; ver salida al final).

## Alcance

Tres conjuntos, uno por tipo de fuente:

| Conjunto | Tipo | Parquet publicado | Filas |
|---|---|---|---|
| `ffmm/cartera_nacional` | automático (CMF) | `docs/outputs/ffmm/cartera_nacional/*.parquet` (57 archivos) | 1.590.196 |
| `securitizadoras/patrimonios_separados_balance` | híbrido: PDF de la CMF → Excel curado → Parquet | `docs/outputs/securitizadoras/patrimonios_separados_balance.parquet` | 7.962 |
| `macro/macro_uf` | serie diaria (Banco Central) | `docs/outputs/macro/macro_uf.parquet` | 4.676 |

Qué se comprobó en cada uno: integridad de archivos, conteos contra el manifiesto o la fuente intermedia, reglas de contenido, y trazabilidad de una fila hasta su origen.

## Integridad de archivos

Los 104 archivos de los tres conjuntos (incluidos `ffmm_balance` y `cartera_nacional` de `fi`, usados en el cruce) tienen un SHA-256 que coincide con `docs/reproducibilidad/inventario_fuentes.csv`. Ninguno falta.

## 1. `ffmm/cartera_nacional` (automático)

**Pasa:**
- 1.590.196 filas en los Parquet = 1.590.196 del manifiesto.
- Valorización sin nulos ni negativos.
- Cruce con `ffmm_balance` (2025-12): la cartera de ningún fondo supera su total de activo (386 fondos cruzados de 392). Mediana del cociente 0,99.

**Hallazgos:**
- **2.960 filas exactamente duplicadas** en 2025-12, repartidas en 108 fondos (cerca del 10 % de las filas). Sin identificador de línea de origen no se puede decidir si son lotes distintos o repeticiones. Con los duplicados, la suma de `pct_activo_fondo` tiene mediana 98,8 %; sin ellos, 95,2 %. Eso sugiere que los duplicados son reales en la fuente, pero no es prueba concluyente. **Indeterminado; requiere revisar el formulario original de la CMF en 3 o 4 fondos.**
- **Trazabilidad débil:** `cartera_nacional` no guarda archivo de origen ni hash por fila. `ffmm_balance` sí los guarda (`fuente_archivo`, `sha256_archivo`). Es la diferencia más importante para el punto 7.
- **Cobertura parcial:** 91 de 386 fondos tienen cartera por debajo del 50 % de su activo. Puede ser normal (instrumentos fuera del formulario), pero debe explicarse en la metodología.
- **Colisión de nombre:** `cartera_nacional` existe en el sector `ffmm` (57 archivos) y en el sector `fi` (27 archivos). El identificador de tabla no es único; la clave correcta es sector + tabla.

## 2. `securitizadoras/patrimonios_separados_balance` (híbrido)

**Pasa:**
- Conteo: 11.086 filas del Excel − 4 vacías − 3.120 anteriores a 2014 = 7.962 publicadas.
- Identidad contable: activos = pasivos + patrimonio en los 358 balances; diferencia máxima 1 M$.
- Fila de muestra (SECURITIZADORA BICE, 2015-12, «Total Activos»): 16.124.910 M$ en el Parquet = 16.124.910 en el Excel.
- El script de publicación (`05_publicar_balance_patrimonios.py --seco`) pasa con las validaciones fail-closed.

**Hallazgos:**
- **Trazabilidad parcial:** el campo `archivo` nombra el PDF de la CMF (por ejemplo `201512_96819300_SECURITIZADORA_BICE_…pdf`), pero ni el PDF ni la página están en el repositorio. Con los datos del repositorio se llega al Excel curado, no al documento original.
- **Cuatro filas del Excel descartadas** por cuenta o categoría inválida, todas con monto 0. Tres tienen columnas desplazadas o abreviadas (por ejemplo, una categoría «2» con moneda «CLP» en BANCHILE 2017-12, y «Pasivo No Circ» en VOLCOM 2025-12). La identidad contable cuadra, lo que sugiere que no se perdió monto, pero sin el PDF no puede asegurarse.
- **Clave no única:** 2 pares archivo + categoría + cuenta se repiten (una misma cuenta dividida en dos líneas). La clave correcta incluye `orden_en_balance`.
- **Cobertura:** 2010–2013 están en la fuente pero no se publican; el docstring lo documenta («para no dejar un hueco» se publica desde 2014, aunque 2013 no existe en la fuente).

## 3. `macro/macro_uf` (serie Banco Central)

**Pasa:**
- Calendario diario completo de 2014-01-01 a 2026-10-20 (4.676 filas, 0 huecos, 0 duplicados, 0 nulos).
- Ningún salto diario mayor a 0,1 %.
- Signo constante dentro de cada ciclo de reajuste. La UF se reajusta del día 10 al día 9 del mes siguiente, según el IPC del mes anterior. Los 155 ciclos son coherentes; 15 tienen caída por IPC negativo.
- Seis valores comparados con fuentes públicas: coinciden exactamente.

| Fecha | Parquet | Referencia pública |
|---|---|---|
| 2024-01-01 | 36.797,64 | 36.797,64 ([valor-uf.cl](https://valor-uf.cl/uf-historico/2025/)) |
| 2025-01-01 | 38.419,17 | 38.419,17 ([SII](https://www.sii.cl/valores_y_fechas/uf/uf2025.htm)) |
| 2025-01-31 | 38.384,41 | 38.384,41 ([valor-uf.cl](https://valor-uf.cl/uf-historico/2025/enero/)) |
| 2025-12-31 | 39.727,96 | 39.727,96 ([valor-uf.cl](https://valor-uf.cl/uf-historico/2025/)) |
| 2026-01-01 | 39.731,79 | 39.731,79 ([Banco Central, cuadro UF_IVP_DIARIO](https://si3.bcentral.cl/Siete/ES/Siete/Cuadro/CAP_PRECIOS/MN_CAP_PRECIOS/UF_IVP_DIARIO/UF_IVP_DIARIO)) |
| 2026-10-19 | 41.183,94 | 41.183,94 ([Banco Central, convertidor](https://www.bcentral.cl/en/web/banco-central/convertidor-calculadora)) |

**Limitación:** la API del Banco Central no es accesible desde el sandbox. La comparación se hizo con páginas públicas que reproducen sus valores, no con la fuente directa. Una comprobación completa requiere ejecutar la descarga contra la API desde un entorno con acceso.

**Nota de interpretación:** agrupar por `periodo` (mes calendario) parece mostrar meses con signos mezclados. No es un error: la UF cambia de tramo el día 10. Cualquier cálculo mensual debe usar el ciclo del día 10 al 9.

## Qué no se pudo trazar

- Ninguna fila de `cartera_nacional` llega a la planilla de la CMF: el Parquet no tiene archivo de origen ni número de línea, y el sandbox no accede a cmfchile.cl.
- Ningún PDF del híbrido está en el repositorio.
- La serie UF no se pudo contrastar con la API del Banco Central (ver limitación).

## Conclusión

- Los tres conjuntos son internamente coherentes y sus conteos cuadran con sus fuentes intermedias o manifiestos.
- El hallazgo que cambia algo es la **trazabilidad**: `ffmm_balance` guarda origen y hash por fila, `cartera_nacional` no, y el híbrido solo llega hasta un nombre de PDF que no está almacenado.
- Quedan **2.960 filas duplicadas** en la cartera de fondos mutuos por decidir con la fuente original. No se corrigieron en esta auditoría.

## Pendientes derivados (para el punto 7 y decisiones posteriores)

1. Añadir `archivo_origen` y `sha256_origen` a `cartera_nacional`, como ya tiene `ffmm_balance`.
2. Decidir si los duplicados exactos de `cartera_nacional` se eliminan o se conservan con una columna de número de línea.
3. Documentar la clave única del híbrido (incluir `orden_en_balance`) y las cuatro filas con columnas desplazadas.
4. Documentar la cobertura parcial de la cartera (91 fondos bajo el 50 % del activo).
5. Renombrar o calificar `cartera_nacional` por sector en el inventario.

## Salida del script (2026-10-20)

```
== 0. SHA-256 de los archivos frente a docs/reproducibilidad/inventario_fuentes.csv
  OK    hashes coinciden: 104; distintos o ausentes: 0
== 1. ffmm/cartera_nacional (automático, CMF)
  OK    filas Parquet 1,590,196 = manifiesto 1,590,196
  AVISO 2025-12: 2,960 filas exactamente duplicadas en 108 fondos
  OK    cartera ≤ total activo en todos los fondos cruzados (386 de 392 fondos tienen balance)
  AVISO fondos con cartera < 50 % del activo: 91 de 386
== 2. securitizadoras/patrimonios_separados_balance (híbrido PDF → Excel curado)
  OK    conteo: Excel 11,086 − vacías 4 − anteriores a 2014 3,120 = publicado 7,962
  OK    activos = pasivos + patrimonio en 358 balances (máx. diferencia 1 M$)
  OK    fila de muestra SECURITIZADORA BICE 2015-12: Parquet 16,124,910 = Excel
== 3. macro/macro_uf (series, Banco Central)
  OK    calendario diario completo 2014-01-01 → 2026-10-20, sin duplicados (4,676 filas)
  OK    signo constante dentro de cada ciclo de reajuste (día 10 → día 9): 155 ciclos
  OK    6 fechas de referencia públicas coinciden con el Parquet
Resultado: sin fallas de integridad
```

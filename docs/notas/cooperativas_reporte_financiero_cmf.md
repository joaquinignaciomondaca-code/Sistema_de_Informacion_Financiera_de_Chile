# Cooperativas: balance y resultados del Reporte Financiero de la CMF

Estado al 2026-09-28 (rama `arena/01a0e66e-monitor-financiero-chile`).

## Qué se publicó

Una serie mensual con el **balance y el estado de resultados de cada cooperativa**
fiscalizada por la CMF, cuenta por cuenta, en millones de pesos.

* **Cobertura:** 115 meses, desde 2017-01 hasta 2026-07.
* **Volumen:** 52.325 registros (7 cooperativas × 65 conceptos × 115 meses).
* **Entidades:** Coopeuch, Oriencoop, Capual, Ahorrocoop, Detacoop, Coonfia y Coocretal
  (la nómina CMF vigente; no se agregan ni se quitan entidades automáticamente).
* **Archivos:** `docs/outputs/cooperativas/cmf_reporte_financiero/estados.parquet`
  y `validacion.json`.

Los resultados son **acumulados del año a la fecha** (así los publica la CMF); los montos
del balance son **saldos al cierre del mes**. La columna `base_monto` lo dice en cada fila.

## Por qué la serie parte en 2017

Antes de 2017 la CMF usaba **otra planilla y otro plan de cuentas**. Mezclar ambas épocas
produciría una serie que parece continua pero no lo es. Por eso la serie parte en 2017-01
y lo anterior queda fuera; no es un dato faltante, es un formato distinto.

## Cómo se valida (nada se publica si algo no cuadra)

Cada período pasa por un control estricto (*fail-closed*): si un solo mes no cumple, **no se
publica nada** (ni siquiera los meses que sí estaban bien), para que nunca haya series a medias.

Se revisa: cabecera con las frases clave · cantidad exacta de montos por fila · subtotales
internos (por ejemplo, colocaciones = comerciales + personas) · activos = pasivos + patrimonio ·
la suma de las cooperativas contra la fila "Total Cooperativas" · coincidencia entre la hoja de
resultados y la de margen.

## Diferencias de la propia fuente, declaradas

La CMF publica algunos subtotales redondeados por separado. En **7 casos** la diferencia va de
3 a 5 millones de pesos (Coonfia en 6 meses, Detacoop en 2022-02). Esos casos se aceptan **pero
quedan escritos** en `validacion.json` (`diferencias_fuente_declaradas`), con el monto publicado,
la suma de sus componentes y la diferencia. Una diferencia mayor a 5 MM$ detiene todo.

Ninguna diferencia se esconde: o se explica en el archivo, o el mes no se publica.

## Casos raros ya resueltos

* **2019-11 · hoja de resultados duplicada.** Ese archivo trae "Estado Resultados Coop" (la
  tabla buena) y "Estado Resultados Coop 2" (un resumen con otras columnas). Se usa la tabla
  buena y la hoja descartada queda registrada en `validacion.json` (`hojas_ignoradas`).
* **2019-11 · área de trabajo a la derecha.** Las planillas imprimibles traen, a la derecha,
  una copia de los mismos datos. En el balance de ese mes la tabla queda pegada al área de
  trabajo con **una sola columna vacía** entre ambas; ahora se reconoce y se descarta lo de
  la derecha.

## Dónde se ve en el sitio

* Explorador → **Cooperativas de Ahorro y Crédito (CMF)** → *Balance y Resultados CMF · por
  cuenta (2017+)*: seis consultas listas (activos por cooperativa, evolución del sistema,
  colocaciones por tipo, excedentes, margen vs provisiones, depósitos).
* Visor de datos: `cooperativas.cmf_balance` y `cooperativas.cmf_resultados`.
* Diccionario de datos: definición de cada columna, incluida la diferencia entre saldo y acumulado.
* Diagrama ERD: ambas tablas enlazadas con la lista de entidades por RUT.

## Cómo se mantiene al día

El flujo `cooperativas_cmf_mensual.yml` corre solo (día 16 de cada mes) o cuando cambia el
extractor: descarga la planilla nueva, reconstruye la serie completa, corre las pruebas,
valida los 115+ períodos y publica. Si un período falla, no commitea nada y avisa con un error.

Además, `web_audit.yml` revisa que el explorador, el visor, el diccionario y el ERD apunten a
los Parquet reales después de cada cambio en `docs/`.

## Pendientes del usuario

1. **Activar GitHub Pages** (Settings → Pages → Source: GitHub Actions) para que el sitio se publique.
2. Fusionar el PR de esta rama a `main`.

# Receta: dashboard de fondos mutuos (balance)

Paso a paso para armar en Looker Studio un informe con el **balance anual** de los fondos
mutuos chilenos: cuánto tienen, cuánto deben y cómo se compone su activo, por fondo y por
administradora.

Se apoya en dos marts publicados en este directorio:

| Mart | Grano | Qué aporta |
|---|---|---|
| `ffmm_balance_fondo` | año × fondo | activo, pasivo y activo neto al 31 de diciembre, con administradora y moneda |
| `ffmm_balance_cuentas` | año × moneda × sección × cuenta | composición del activo y del pasivo por línea del estado financiero |

Antes de empezar, tres cosas que definen todo el informe:

* **Es anual.** El balance cierra al 31 de diciembre; el último corte publicado es **2025-12**.
  La cartera mensual llega más lejos (2026-09), pero no es el balance: no las mezcles en un
  mismo eje sin decirlo.
* **La unidad es «miles de la moneda del fondo».** Hay fondos en CLP, USD y EUR. El propio
  esquema de la CMF dice «no sumar monedas distintas»: si sumas todo junto, el total queda mal
  por unos **US$ 10.500 millones** (ver §6).
* **Los importes no están en pesos.** Para mostrar millones de pesos hay que dividir por
  1.000; para miles de millones, por 1.000.000.

---

## 1. Agrega las dos fuentes

Con el conector: **Crear → Fuente de datos → SIF Chile · marts →** elige la tabla. Sin
conector (prueba rápida): **Subida de archivos CSV** con
`docs/looker/marts/ffmm_balance_fondo.csv` y `docs/looker/marts/ffmm_balance_cuentas.csv`, o
`=IMPORTDATA(...)` en una hoja.

Renombra las fuentes a **«FM · balance por fondo»** y **«FM · composición»**; con dos fuentes
en el informe, los nombres genéricos se confunden.

---

## 2. Campos calculados

En «FM · balance por fondo» → **Agregar un campo**:

| Nombre | Fórmula | Por qué |
|---|---|---|
| `Activo neto (MM$)` | `activo_neto_miles_mf / 1000` | millones de pesos, para tarjetas y rankings |
| `Activo (MM$)` | `activo_miles_mf / 1000` | idem |
| `Pasivo (MM$)` | `pasivo_miles_mf / 1000` | idem |
| `Pasivo / Activo %` | `pasivo_miles_mf / activo_miles_mf` | formato porcentaje; detecta fondos con deuda |
| `Año` | `YEAR(fecha)` | etiqueta corta para el eje y los filtros |

En «FM · composición» → **Agregar un campo**:

| Nombre | Fórmula |
|---|---|
| `Monto (MM$)` | `monto_miles_mf / 1000` |

`pasivo_sobre_activo_pct` ya viene calculado por el mart y su agregación es **AVG**: promediar
un ratio tiene sentido; sumarlo, no.

---

## 3. Controles (arriba del informe)

| Control | Campo | Configuración |
|---|---|---|
| Lista desplegable | `Año` | una sola selección, 2025 por defecto |
| Lista desplegable | `moneda` | CLP por defecto (USD y EUR son 84 y 0 fondos en 2025) |
| Lista desplegable | `razon_social_agf` | opcional, para mirar una administradora |
| Cuadro de búsqueda | `nombre_fondo` | para encontrar un fondo puntual |

El control de `moneda` no es cosmético: es el que evita la suma incorrecta.

---

## 4. Los gráficos, uno por uno

Todos usan **«FM · balance por fondo»** salvo el 6, que usa **«FM · composición»**.

### 4.1 Tarjeta — «Fondos informantes»

* Métrica: `COUNT_DISTINCT(run_fondo)`.
* Filtro: `Año` = 2025 y `moneda` = CLP.
* Esperado: **365**.

### 4.2 Tarjeta — «Activo neto de la industria»

* Métrica: `SUM(Activo neto (MM$))`.
* Filtro: `Año` = 2025, `moneda` = CLP.
* Esperado: **79.446.918 MM$** (≈ 79,4 billones de pesos, ≈ US$ 87 mil millones al dólar de
  cierre de 2025).
* Comparación de fecha: **período anterior** → muestra +14,7 % contra 2024.

### 4.3 Serie de tiempo — activo y pasivo por año

* Dimensión: `fecha` (agrupada por año).
* Métricas: `SUM(Activo (MM$))` y `SUM(Pasivo (MM$))`.
* Filtro: `moneda` = CLP.
* Para qué: ver si el crecimiento viene de más patrimonio o de más deuda.

### 4.4 Barras horizontales — top 10 administradoras

* Dimensión: `razon_social_agf`.
* Métrica: `SUM(Activo neto (MM$))`.
* Filtro: `Año` = 2025, `moneda` = CLP.
* Orden: descendente por la métrica; **límite 10 filas**.
* Esperado, en orden: Banchile 17.217.726 · Santander 13.964.424 · BCI 9.639.279 ·
  BancoEstado 7.798.316 · BICE 4.827.065 · Itaú 4.557.033 · LarrainVial 3.605.340 ·
  SURA 3.322.416 · Scotia 3.296.183 · Security 2.756.652 (MM$).

### 4.5 Barras horizontales — top 10 fondos

* Dimensión: `nombre_fondo`.
* Métrica: `SUM(Activo neto (MM$))`.
* Filtro: `Año` = 2025, `moneda` = CLP.
* Orden descendente, límite 10.
* Esperado: primer lugar **FONDO MUTUO SANTANDER MONEY MARKET** con 3.322.541 MM$; segundo
  **FM BANCHILE CAPITAL FINANCIERO** con 3.064.485 MM$.

### 4.6 Composición del activo (fuente «FM · composición»)

* Tipo: barras apiladas al 100 % o tabla.
* Dimensión: `cuenta`.
* Métrica: `SUM(Monto (MM$))`; alternativa: `AVG(participacion_pct)`.
* Filtros: `Año` = 2025, `moneda` = CLP, `seccion` = **ACTIVO**.
* Esperado: «Activos financieros a valor razonable con efecto en resultados» **69,0 %**;
  «Activos financieros a costo amortizado» **30,5 %**; el resto (efectivo, cuentas por cobrar)
  suma menos de 0,5 %.
* Truco: una tabla con `cuenta`, `SUM(Monto (MM$))` y `SUM(fondos)` muestra además en cuántos
  fondos aparece cada línea (365 en las dos grandes).

### 4.7 Dispersión — tamaño contra endeudamiento

* Dimensión: `nombre_fondo`.
* Eje X: `SUM(Activo neto (MM$))`.
* Eje Y: `AVG(pasivo_sobre_activo_pct)`.
* Filtro: `Año` = 2025, `moneda` = CLP.
* Para qué: encontrar fondos que financian su cartera con deuda. La mediana es **0,3 %**; el
  máximo de la industria es **25,2 %**, así que un puñado de puntos se despega del resto.

### 4.8 Tabla de detalle

Columnas: `nombre_fondo`, `razon_social_agf`, `Activo (MM$)`, `Pasivo (MM$)`,
`Activo neto (MM$)`, `Pasivo / Activo %`, `run_fondo`.

* Orden: `Activo neto (MM$)` descendente.
* Filtro: `Año` = 2025, `moneda` = CLP.
* Formato: números con separador de miles; `Pasivo / Activo %` como porcentaje con un decimal.
* Paginación: 10 filas por página. Con 365 filas, es la vista para auditar un fondo puntual.

---

## 5. Cifras de control (2025-12)

Si el informe no muestra esto, algo está mal configurado:

| Control | Valor |
|---|---|
| Fondos con balance, CLP | **365** |
| Fondos con balance, USD | **84** |
| Activo total, CLP | **80.315.591 MM$** |
| Pasivo total, CLP | **868.673 MM$** |
| Activo neto, CLP | **79.446.918 MM$** |
| Activo neto 2024, CLP | 69.275.571 MM$ (410 fondos) |
| Mediana pasivo / activo | 0,3 % |
| Línea de activo más grande | valor razonable con efecto en resultados, 69,0 % |

Fuente: `catalogo.json` → `data_release` del mart. Si comparas con la web, el corte del
balance es el mismo (31-12-2025).

---

## 6. Los cuatro errores que hay que evitar

1. **Sumar monedas distintas.** `SUM(activo_neto_miles_mf)` sin filtrar por `moneda` da
   79.457.486 MM$: parece correcto, pero suma 10.568 millones de *dólares* como si fueran
   pesos. El número correcto es 79.446.918 MM$ en CLP **más** US$ 10.568 millones (≈ 9,6
   billones de pesos al dólar de cierre).
2. **Sumar totales y detalles.** `ffmm_balance_cuentas` publica sólo líneas de detalle
   justamente para que no pase esto: los totales del balance ya suman sus detalles. Si armas
   tu propia fuente desde el Parquet, filtra `tipo_linea = 'detalle'` o `= 'total'`, nunca
   ambos.
3. **Comparar el balance con la cartera como si fueran lo mismo.** El balance es anual y
   cierra en diciembre; `ffmm_cartera_nacional_fondo` es mensual y mide la cartera de
   inversiones, no el patrimonio. Un gráfico que mezcle 2026-09 de cartera con 2025-12 de
   balance compara dos cosas y dos fechas.
4. **Leer «activo neto» como «activo menos pasivo del mes».** Es el activo neto atribuible a
   los partícipes al cierre del ejercicio; es el mejor proxy de patrimonio, pero no incluye
   aportes ni rescates posteriores a esa fecha.

---

## 7. Siguiente paso: la cartera mensual

El balance dice cuánto hay; la cartera dice en qué está invertido, mes a mes. Cuando el
informe de balance esté cerrado, agrega una segunda página con:

* `ffmm_cartera_nacional_tipo` → mix de instrumentos de la industria (mensual, hasta 2026-09).
* `ffmm_cartera_extranjera_pais` → dónde está lo invertido fuera de Chile.
* `ffmm_cartera_nacional_fondo` → cartera nacional por fondo, para cruzar con el ranking de
  activo neto usando `run_fondo`.

Ese cruce —activo neto del balance contra cartera del mes— es el que responde «este fondo
creció, ¿y en qué está invertido?».

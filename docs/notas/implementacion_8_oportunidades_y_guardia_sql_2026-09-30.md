# Las 8 oportunidades, implementadas — y el veredicto de la pestaña SQL

Fecha: 2026-09-30 · Corte de datos: 2026-06 (69 trimestres publicados)
Nota madre: `docs/notas/revision_extraccion_eeff_industrias_2026-10-01.md` (F1–F12 y el plan)

Esta nota es el cierre de las dos cosas que quedaron pendientes:

1. **El miedo a la pestaña SQL**: ¿puede alguien borrarme la base o inyectarme filas?
2. **Las 8 oportunidades** del §5 de la revisión, que pediste implementar todas.

Todo está en código y con pruebas; nada queda solo en la intención.

---

## 1. La pestaña SQL: veredicto

**No se puede borrar la base de datos. No se pueden inyectar filas en los datos publicados.
Lo que sí se podía hacer —hasta hoy— era suplantar el dato *en pantalla*. Eso ya está cerrado.**

Por qué lo primero es imposible, por construcción:

* El motor es **DuckDB-Wasm y corre dentro del navegador del visitante**. No hay servidor de
  base de datos, no hay backend, no hay credenciales. Los Parquet se registran con
  `registerFileURL` sobre **HTTP de solo lectura**: el navegador hace `GET` y `Range`; no existe
  un camino de vuelta para escribir el archivo.
* Los datos publicados viven en el repositorio (`docs/outputs/...`). Aunque el navegador quisiera,
  no tiene permiso de escritura sobre GitHub: para cambiar un Parquet hay que pasar por un
  pipeline con `git`.

El riesgo real era otro, y era serio: DuckDB acepta sentencias de escritura **sobre su catálogo en
memoria**. Es decir, no podían tocar tus datos, pero sí podían cambiar lo que *tú ves*:

```sql
DROP VIEW agf_balance;                        -- la tabla desaparece de la pestaña
CREATE OR REPLACE VIEW agf_balance AS ...     -- pasa a mostrar cifras inventadas
CREATE TABLE falso AS SELECT ...; INSERT ...  -- filas fabricadas con la misma piel que las reales
```

Y se agravaba porque `checkUrlHash()` **ejecuta automáticamente** lo que venga en `#sql=`: un
enlace compartido podía ejecutar sentencias en el navegador de otra persona.

**Qué se hizo.** `docs/js/sql_guard.js` (nuevo) es la única puerta de entrada:
`DuckDBClient.query()` lo consulta **antes** de enviar cualquier SQL al motor.

* Es una **lista blanca** (solo `SELECT`, `WITH`, `VALUES`, `TABLE`, `DESCRIBE`, `SHOW`,
  `EXPLAIN`, `SUMMARIZE`, `PRAGMA`, `PIVOT`, `UNPIVOT`), no una lista negra —las negras siempre
  se quedan cortas.
* Se aplica **después de quitar comentarios y literales de texto**: una cuenta que contenga la
  palabra «drop» no bloquea una consulta legítima, y un comentario no puede esconder una sentencia.
* Además bloquea escritura «suelta»: `SELECT ... INTO tabla` (CTAS), `COPY`, `ATTACH`, `INSTALL`,
  `LOAD`, y rechaza **más de una sentencia** aunque ambas lean.
* El rechazo no es un error críptico: dice que la consola es de solo lectura y nombra la sentencia
  que se intentó.

**Comprobación:** `scripts/audit_sql_guard.js` — 41 casos automáticos (19 de rechazo, entre ellos
`DROP`, `DELETE`, `UPDATE`, `INSERT`, `CREATE OR REPLACE VIEW`, `CREATE TABLE AS`, `ALTER`,
`TRUNCATE`, `CALL`, `SET`; y 22 de aceptación legítima, incluidos los «falsos positivos» de
literales y comentarios). **Las 132 consultas sugeridas siguen pasando: 0 bloqueadas.**

De paso quedó reforzado lo que ya estaba: `scripts/audit_xss_celdas.js` (jsdom) inyecta valores
hostiles en celdas y alias de columna y comprueba que nada se ejecute, y
`docs/js/chat_terminal.js` / `data_viewer.js` escapan toda interpolación.

**Respuesta corta, para quedarse tranquilo:** nadie puede borrarte los datos ni agregarte filas
en lo publicado; y desde hoy tampoco puede hacerte creer que las ve.

---

## 2. Las 8 oportunidades

### 1 · Auditoría ejecutable de cuadratura sobre toda la historia → **hecha**

`scripts/auditar_eeff_ifrs.py` recorre **todo lo publicado** (no solo el último trimestre, que era
lo único que pasaba por la compuerta del extractor) y falla si algo no cuadra. Corre en
`web_audit.yml` en cada push y PR.

```
Sector                 Balances  Verificados  Cobertura  Descuadres  Identidades  Divergencias
AGF                        2935         2925     99.7%           0         4107             0
Securitizadoras             646          644     99.7%           0          965             0
CCAF                        224          224    100.0%           0          222             0
Factoring y leasing         949          947     99.8%           0         1863             0

Total: 4740/4754 balances verificados (99.7%) · 7157 identidades de resultados comprobadas
Cuadratura IFRS: toda la historia publicada cuadra.
```

La cobertura (99,7 %) es ahora un **dato medido**: los 14 balances que faltan son sociedades cuya
glosa no trae los tres totales reconocibles, no un agujero de la validación.

### 2 · Cerrar F3 (glosas) → **hecha**

En `pipelines/auto/cuadratura.py`: la detección de totales ya no depende de una lista blanca
frágil, y se exige una **cobertura mínima de cuadratura** (≥ 90 % de los balances del trimestre
deben ser verificables: `cuadratura.COBERTURA_MINIMA`; la primera versión de esta nota decía 95 %). Si cambian las glosas y la compuerta se queda ciega, **el trimestre no se
publica** en vez de publicarse a ciegas. 19 pruebas unitarias.

### 3 · Validar el estado de resultados → **hecha**

Dos identidades, con la misma política fail-closed por bloque que el balance:

* el resultado integral (`ERI`) arrastra la **misma** ganancia del ejercicio que el `ERFG`/`ERNG`;
* ganancia bruta = ingresos − costo de ventas.

Medido sobre la historia: **7.157 identidades comprobadas, 0 divergencias**.

### 4 · Unificar los dos extractores del TXT (F1) → **hecha**

`pipelines/auto/ifrs_txt.py` es ahora el único parseo del TXT de la CMF; lo usan tanto
`pipelines/ifrs_sectores/actualizar.py` como `factoring_leasing/scripts/backfill_ifrs.py`
(12 pruebas). Convenciones compartidas: `orden` presente, cuadratura para todos, y el
mismo contador de `orden`/`repeticion`. **`tipo_balance` no se tradujo en factoring/leasing**: queda
`I`/`C` literal (y sus columnas siguen llamándose `valor_archivo`, `moneda_archivo`,
`repeticion_contexto`) para no romper las consultas ya guardadas; la primera versión de esta nota
decía lo contrario.

**Prueba de que no se movió ningún dato publicado:**
`pipelines/ifrs_sectores/tests/test_roundtrip_publicado.py` reconstruye el TXT de la CMF desde el
Parquet publicado y vuelve a leerlo campo por campo. Barrido ad-hoc sobre 2011, 2015, 2019, 2023,
2025 y 2026 (agf, securitizadoras, ccaf): **60.590 filas comparadas, 0 diferencias.**

Efecto secundario bueno: `factoring_leasing` gana la columna `orden` (esquema v2) y su consulta
sugerida ordena por `estado_financiero, orden`.

### 5 · Sondeo para ampliar industrias (F2) → **hecho, se ejecuta en Actions**

`scripts/sondear_ifrs_sectores.py` descarga el archivo vigente y clasifica las ~300 sociedades
descartadas por patrón de `GIROS`, cruzando cada RUT con lo ya publicado: cuántas son de cada giro,
por taxonomía y por estado, y cuáles son sociedades nuevas. No escribe en `docs/` ni hace commit;
deja su JSON en `.local-data/`. 5 pruebas unitarias y workflow propio
`.github/workflows/ifrs_sondeo.yml` (manual + mensual, sin credenciales).

**No se pudo correr desde este entorno**: la CMF no es alcanzable desde el sandbox (se verificó:
la conexión TLS a `www.cmfchile.cl` falla). Por eso el sondeo vive en Actions: ahí sí hay red.
Se lanza con el botón «Run workflow» o solo, el día 5 de cada mes.

### 6 · Cobertura y continuidad (F10) → **hecha**

El pipeline ahora publica quién falta y quién se fue, y lo muestra **en el sitio**:

* `cobertura()` en `actualizar.py` calcula la cobertura **de lo publicado** (leyendo solo tres
  columnas de los Parquet), no de la memoria del pipeline: así la información se reconstruye
  completa aunque se pierda el `control.json`.
* Va en cada `manifest.json` de las 6 tablas (para que viaje con la descarga) y en las fichas del
  **Diccionario de Datos**, con un recuadro «Cobertura».

Lo que se ve hoy en el sitio:

| Sector | Informan | Catálogo | Dejaron de informar |
| :--- | ---: | ---: | :--- |
| AGF | 53 | 72 | TAURUS AGF (último 2025-09), AZIMUT (2025-09), SARTOR AGF (2024-12) |
| Securitizadoras | 9 | 16 | FINTESA SECURITIZADORA (2024-12) |
| CCAF | 4 | 6 | — (Javiera Carrera y Gabriela Mistral nunca aparecen en la fuente) |

Ventana de novedad: 8 trimestres. Alguien que se fue antes sigue en la lista de `sin_datos`, con
el último trimestre en que apareció, pero ya no sale como novedad del trimestre.

### 7 · Documentar la duplicidad (F7) → **hecha**

Que el error dejara de ser silencioso:

* **Diccionario de datos**: las 6 fichas (balance y resultados de AGF, securitizadoras y CCAF)
  explican ahora `repeticion` y `estado_financiero`, y la descripción de resultados avisa del caso
  concreto: *«para sumar utilidades sin triplicarlas filtre
  `estado_financiero IN ('ERFG','ERNG')` y `repeticion = 1`»*.
* **3 consultas sugeridas nuevas** («Por qué hay que filtrar: «Ganancia (pérdida)» aparece varias
  veces») que muestran el problema con datos reales: en 2025-12 la cuenta aparece 52 veces en
  ERFG repetición 1, 52 en repetición 2 y 53 en ERI. Total sugeridas: **132, 0 vacías, 0 con error.**

### 8 · Pruebas unitarias de `ifrs_sectores` (F11, F8) → **hechas**

`pipelines/ifrs_sectores/tests/test_actualizar.py`, 24 pruebas: reparto por sector (por RUT y por
nombre), `orden`/`repeticion` por taxonomía, importe no entero, guardas de fuente y contenido,
cierre a 150 días, cobertura, y una **corrida completa sin red** (se sirven de memoria el índice y
el TXT) que publica y comprueba que la segunda corrida no repite el trabajo.

**El caso F8.** La guarda anti-pérdida comparaba *entidades*, no filas por tabla: si una relectura
perdía las filas de balance (p. ej. un cambio de glosas) pero la sociedad seguía apareciendo en
resultados, `escribir(sec, "balance", periodo, [])` **borraba el balance de ese trimestre** del
Parquet publicado, sin aviso. Se cerró comparando tabla por tabla y se demuestra en dos niveles:

* prueba unitaria sobre `publicar_sector()` (extraída de `main` para poder probarla): el archivo
  no cambia ni de tamaño ni de marca de tiempo, y el aviso dice `pierde filas en balance`;
* prueba de punta a punta: una corrida completa cuyo TXT llega sin líneas de balance deja el
  Parquet exactamente igual y registra el aviso en el manifiesto.

**Estado de las pruebas del repositorio: 189 OK.** Quedan fuera `pensiones/` (necesita ZIP crudos
que no están en el repo) y `macro/` (necesita credenciales del BCCh); ambas corren en Actions.

---

## 3. Auditorías, todas en verde

`audit_navigation` (12 familias, 71 tablas) · `audit_web_full` (100 % operativo) ·
`audit_interfaz` (coherente) · `audit_rut_formatos` (630 archivos, 0 problemas) ·
`normalizar_vocabulario --check` (71 tablas, 15 sectores) · `build_download_catalog` (71 conjuntos,
10.831.652 filas, 273,4 MB) · `audit_consultas_sugeridas` (132 OK) · `audit_automatizacion`
(72 tablas, 0 problemas) · `audit_duckdb_client` · `audit_sql_guard` (41) ·
`audit_interfaz_dom` (39/39) · `audit_xss_celdas` · `auditar_eeff_ifrs` (toda la historia cuadra).

## 4. Archivos

**Nuevos:** `docs/js/sql_guard.js` · `scripts/audit_sql_guard.js` · `scripts/auditar_eeff_ifrs.py` ·
`scripts/sondear_ifrs_sectores.py` · `pipelines/auto/ifrs_txt.py` ·
`pipelines/ifrs_sectores/tests/` (3 archivos, 31 pruebas) · `pipelines/auto/tests/test_ifrs_txt.py` ·
`.github/workflows/ifrs_sondeo.yml`.

**Modificados:** `pipelines/ifrs_sectores/actualizar.py` (parseo compartido, `publicar_sector`,
cobertura publicada) · `pipelines/auto/cuadratura.py` · `factoring_leasing/scripts/backfill_ifrs.py` ·
`factoring_leasing/scripts/publish_backfill.py` (`orden`, esquema v2) · `docs/js/duckdb_client.js`
(guardia) · `docs/js/data_dictionary.js` (duplicidad + recuadro de cobertura) ·
`docs/js/sidebar.js` (3 consultas nuevas) · `docs/js/chat_terminal.js` · `docs/index.html` ·
los 6 `manifest.json` de AGF/securitizadoras/CCAF (cobertura) · `docs/js/download_catalog.js` ·
`scripts/audit_xss_celdas.js` · `.github/workflows/web_audit.yml`.

## 5. Lo único que queda afuera

* **Correr el sondeo (oportunidad 5)** con red real: se dispara desde Actions.
* **Ampliar industrias** de verdad con lo que diga ese sondeo: es un trabajo de datos, no de código,
  y conviene decidirlo mirando el resultado, no antes.
* Los trimestres cerrados hace más de 150 días nunca se releen (F12): decisión documentada y
  razonable, pero significa que una corrección tardía de la CMF no se recoge. Si quieres, se
  cambia por una relectura anual de todo el historial.

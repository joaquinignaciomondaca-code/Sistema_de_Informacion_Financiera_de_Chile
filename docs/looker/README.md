# Looker Studio sobre SIF Chile

**Sí, se puede.** Pero conviene decirlo de entrada: Looker Studio **no lee Parquet** y este
sitio no tiene un motor SQL remoto —GitHub Pages sirve archivos y no ejecuta procesos—.
Así que la conexión no puede ser «pegar la URL del Parquet»: hay que elegir por dónde
entra el dato.

Este directorio publica la pieza que hace falta para el camino más corto: **marts**, tablas
agregadas en CSV, con grano y unidad declarados, calculadas en el build sobre el mismo
Parquet que publica el sitio.

| Pieza | Qué es |
|---|---|
| `marts/{id}.csv` | 10 tablas agregadas (≈6,7 MB, ≈94.000 filas) listas para graficar. |
| `catalogo.json` | Qué mart existe, qué columnas tiene, cuál es su grano, su unidad y su `sha256`. |
| `conector/` | Conector comunitario de Looker Studio (Apps Script) que sirve esos marts como fuente de datos. |

Cifras exactas de filas y bytes: `catalogo.json` (`filas`, `bytes`, `data_release`). Se
regeneran con `python3 scripts/build_marts_looker.py` y el CI falla con `--check` si quedan
atrás.

---

## 1. Cinco caminos, elige según lo que necesites

| Camino | Sirve para | Actualización | Detalle | Esfuerzo |
|---|---|---|---|---|
| **A. CSV a mano** (carga de archivo) | una primera maqueta, un informe puntual | manual | marts | 2 min |
| **B. Google Sheets + `IMPORTDATA`** | informe que se refresca sin tocar nada | al abrir la hoja | marts | 10 min |
| **C. Conector comunitario** (este repo) | dashboards sobre los marts, fuente propia | al refrescar el dato | marts | 20 min |
| **D. BigQuery nativo** | detalle fila a fila, SQL, 19 M de filas | la que fijes | todo | 30 min + cuenta GCP |
| **E. MotherDuck** (DuckDB) | SQL completo sin GCP, equipo chico | la que fijes | todo | 30 min + cuenta |

Regla práctica: **marts para mirar, BigQuery/MotherDuck para preguntar**. Un dashboard que
sólo grafica series y composiciones vive bien con los marts; uno que necesita filtrar
instrumento por instrumento, no.

---

## 2. Camino A: subir el CSV (2 minutos)

1. Descarga el mart que quieras desde
   `https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/looker/marts/{id}.csv`
   (la lista está en `catalogo.json`).
2. Looker Studio → **Crear** → **Fuente de datos** → **Carga de archivo CSV**.
3. Arrastra el archivo, comprueba los tipos y **Conectar**. Crea el informe.

Límite del camino A: 100 MB por conjunto de datos y 2 GB por usuario. Los marts pesan menos
de 2 MB cada uno, así que entran de sobra. Es una foto: si el dato cambia, hay que volver a
subir el archivo.

> No uses este camino con el Parquet original: Looker Studio no lo abre, y convertirlo a CSV
> sin agregar produce archivos de cientos de MB que ninguna de estas rutas acepta.

---

## 3. Camino B: Google Sheets + `IMPORTDATA` (se refresca al abrir la hoja)

La hoja se actualiza cada vez que se abre y Looker Studio lee la hoja, así que el informe
sigue al dato publicado sin que nadie suba nada.

1. Crea una hoja de cálculo.
2. En `A1`:
   ```
   =IMPORTDATA("https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/looker/marts/ffmm_cartera_extranjera_pais.csv")
   ```
3. Looker Studio → **Crear** → **Fuente de datos** → **Google Sheets** → elige la hoja.
4. Marca la primera fila como encabezado y revisa que `fecha` quede como fecha y los montos
   como número.

Límites: una hoja admite **10 millones de celdas**. `seguros_inversiones_clase` (14 mil filas
× 7 columnas) y `macro_series_diaria` (26 mil × 7) caben; una tabla de un millón de filas, no.

---

## 4. Camino C: conector comunitario (fuente de datos propia)

El conector lee `catalogo.json`, muestra la lista de marts y devuelve el CSV elegido como
tabla. No hay backend ni credenciales: sólo descarga archivos estáticos del sitio.

1. Entra a [script.google.com](https://script.google.com) → **Nuevo proyecto**.
2. Crea `Code.gs` con el contenido de [`conector/Code.gs`](conector/Code.gs) y reemplaza
   `appsscript.json` por [`conector/appsscript.json`](conector/appsscript.json) (menú
   **Ver → Mostrar archivo de manifiesto**).
3. **Implementar → Implementaciones de prueba**, copia el **ID de la implementación Head** y
   abre `https://datastudio.google.com/datasources/create?connectorId=<ID>`. Autoriza el
   permiso `script.external_request` cuando lo pida.
4. Elige la tabla en la lista y **Conectar**. Para publicarlo con versión fija, crea una
   implementación versionada y usa el ID de esa implementación en lugar del Head.

Qué hace y qué no:

* Devuelve las filas del mart tal cual, con `fecha` como eje temporal.
* Las métricas traen su agregación declarada: los montos y los conteos se suman; las
  participaciones (`participacion_pct`) y los valores macro se promedian. Cambiar eso es un
  clic en la fuente de datos.
* **No** agrega del lado del servidor y **no** sustituye a BigQuery: Apps Script tiene
  límites de tiempo y de tamaño de respuesta. Por eso el conector está pensado para los
  marts (máximo ≈26.000 filas), no para los 2,3 millones de filas de `seguros_renta_fija`.

**Actualización:** no hay nada que programar. El conector baja el CSV vigente en cada
refresco y Looker Studio aplica su intervalo de actualización de datos (ver §9).

---

## 5. Camino D: BigQuery (el detalle completo)

Es el único camino que le da a Looker Studio el catálogo entero con SQL del lado del motor.
El repositorio ya publica Parquet particionado; el script lo consolida y lo carga.

```bash
# una vez: gcloud auth login, y un proyecto con facturación habilitada
python3 scripts/cargar_bigquery.py --proyecto mi-proyecto --dry-run   # qué haría
python3 scripts/cargar_bigquery.py --proyecto mi-proyecto             # carga 86 tablas
python3 scripts/cargar_bigquery.py --proyecto mi-proyecto --verificar # cuenta filas
```

* Crea el dataset `sif_chile` (configurable con `--dataset`) y carga una tabla por objeto
  con `bq load --replace`, así que se puede repetir sin duplicar.
* Respeta los filtros del contrato: `bancos_balance` se carga sólo con las líneas B1/B2 y
  `bancos_resultados` sólo con R1, igual que las vistas del sitio.
* Costo: ≈0,5 GB de almacenamiento activo (centavos al mes) y consultas que caben en el
  terabyte gratuito mensual de BigQuery. La cuenta es tuya; este proyecto no cobra ni pide
  credenciales.

Después, en Looker Studio: **Crear → Fuente de datos → BigQuery →** proyecto → dataset →
tabla. Las vistas `*_ultimo_periodo` y `*_ultima_particion` no viajan a BigQuery: son alias
del visor. Si quieres ese atajo, crea una vista en BigQuery con el mismo `WHERE periodo =
(SELECT max(periodo) …)`.

---

## 6. Camino E: MotherDuck (DuckDB administrado, sin GCP)

Looker Studio no tiene conector de DuckDB, pero sí uno de **PostgreSQL**, y MotherDuck expone
un endpoint compatible. Con eso, un DuckDB en la nube lee los Parquet del sitio por HTTP y
Looker Studio consulta como si fuera Postgres.

```sql
-- una vez, en MotherDuck (o con el CLI `duckdb md:`)
CREATE DATABASE sif_chile;
USE sif_chile;
CREATE TABLE seguros_renta_fija AS
  SELECT * FROM read_parquet(
    'https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/outputs/seguros/renta_fija/*.parquet');
```

Y en Looker Studio: **Crear → Fuente de datos → PostgreSQL**, con el host
`pg.<región>.aws.motherduck.com`, puerto 5432, usuario `postgres`, contraseña = token de
MotherDuck y SSL activado. Requiere crear un esquema `public` para que el selector de tablas
liste algo.

Es la ruta más corta para un equipo que ya usa DuckDB, pero agrega una dependencia externa
(cuenta y token) que el resto del proyecto no tiene.

---

## 7. Qué hay en cada mart

| id | Grano | Unidad | Dashboard típico |
|---|---|---|---|
| `directorio_entidades` | entidad | sin cifras | filtro de entidades, tabla de vigencia |
| `seguros_inversiones_clase` | mes × aseguradora × clase | M$ | composición de cartera por compañía |
| `seguros_renta_fija_tipo` | mes × tipo × país | M$ | concentración de renta fija |
| `ffmm_cartera_nacional_fondo` | mes × fondo | miles de moneda funcional | tamaño y diversificación por fondo |
| `ffmm_cartera_nacional_tipo` | mes × tipo de instrumento | miles de moneda funcional | mix de instrumentos de la industria |
| `ffmm_cartera_extranjera_pais` | mes × país | miles de moneda funcional | dónde invierten fuera de Chile |
| `fi_cartera_nacional_tipo` | trimestre × tipo | miles de moneda funcional | mix de los fondos de inversión |
| `bancos_totales` | mes × banco | CLP | activos, pasivos, patrimonio y colocaciones |
| `macro_series_mensual` | mes × serie | según `unidad` | contexto macro de cualquier informe |
| `macro_series_diaria` | día × serie | según `unidad` | TPM, dólar, UF, cobre, bonos |

Todas traen `periodo` (`AAAA-MM`) y `fecha` (primer día del período, tipo fecha). Las claves
de entidad son las mismas del catálogo API: `rut_aseguradora`, `run_fondo`, `rut`,
`codigo_institucion`, así que `directorio_entidades` sirve para cruzar y para etiquetar.

**Unidades, que es donde se pierde la gente:** los montos de seguros están en **miles de
pesos (M$)**; los de fondos, en **miles de la moneda funcional del fondo** (mayoritariamente
CLP, pero no siempre). Los totales de bancos están en **pesos**. Para mostrar «miles de
millones de pesos» en un gráfico de seguros, divide `valor_final_m_clp` por 1.000.000.

---

## 8. Un dashboard mínimo, en cuatro gráficos

Fuente: `seguros_inversiones_clase`.

1. **Serie temporal** — dimensión `fecha` (mes), métrica `SUM(valor_final_m_clp)`, desglose
   por `clase_activo`. Responde cómo se movió la cartera de la industria.
2. **Barras** — dimensión `nombre_aseguradora`, métrica `SUM(valor_final_m_clp)`, filtro
   `periodo` = último mes. Quién concentra.
3. **Torta o barras 100 %** — dimensión `clase_activo`, métrica `SUM(valor_final_m_clp)`,
   mismo filtro. Con qué se compone.
4. **Tarjeta** — `SUM(valor_final_m_clp)/1000000` con formato «MM$», filtro último mes.

Controles útiles: selector de `periodo`, filtro de `clase_activo` y —si cruzas con
`directorio_entidades`— una lista de entidades. Para mezclar dos marts, el campo común es
`periodo`; para mezclar con el directorio, la clave es el id de la entidad.

---

## 9. Cómo se mantiene solo (y qué parte te toca a ti)

Hay dos relojes, y conviene no confundirlos: **cuándo cambia el archivo** y **cuándo Looker
Studio vuelve a leerlo**.

### El dato ya se actualiza solo

No hay nada que programar de nuestro lado. Los publicadores escriben en `docs/outputs/`, y el
flujo **«Contrato derivado»** (`contrato_publicado.yml`) recalcula los marts después de cada
publicación —y además cada dos horas, porque los push del bot no disparan otros workflows—.
Los CSV que sirve el sitio son siempre los del último corte; el `data_release` de
`catalogo.json` lo delata.

### Looker Studio: la caché

Looker Studio no consulta la fuente en cada visita: guarda una copia y la refresca según el
intervalo de **actualización de datos** del origen.

* Con el **conector comunitario** cada refresco vuelve a bajar el CSV, es decir, toma el corte
  vigente. El intervalo no siempre se puede bajar (en los conectores comunitarios suele quedar
  en 12 horas). Para datos que se publican tres veces al mes, 12 horas no cambian nada.
* Con **Google Sheets**, el intervalo se puede fijar en 15 minutos; `IMPORTDATA` refresca al
  abrir la hoja y la hoja necesita abrirse cada tanto.
* En ambos casos, el botón **⋮ → Actualizar datos** fuerza una lectura nueva; y el editor del
  informe puede activar la actualización para quien lo mira (Configuración del informe).

Si el informe muestra un corte viejo, casi siempre es este reloj, no el dato: compara el
`data_release` de `catalogo.json` con lo que dice el dashboard.

### Si necesitas el detalle y también quieres que se cargue solo

Los marts se autoactualizan porque viven en el repositorio. Las **86 tablas de BigQuery** se
cargan cuando alguien corre el script, así que para que eso también sea automático hay que
programarlo en GitHub Actions. La plantilla está en
[`plantillas/cargar_bigquery.yml`](plantillas/cargar_bigquery.yml):

1. En Google Cloud, crea una cuenta de servicio con **BigQuery Data Editor** y **BigQuery Job
   User**, y descarga su clave JSON.
2. En GitHub: **Settings → Secrets and variables → Actions**. Agrega el secreto `GCP_SA_KEY`
   con el JSON y la variable `GCP_PROJECT` con el ID del proyecto.
3. Copia la plantilla a `.github/workflows/cargar_bigquery.yml`.
4. Listo: corre cada seis horas y al lanzarlo a mano. Looker Studio consulta BigQuery en vivo,
   así que sólo queda su propia caché (12 horas por defecto, configurable).

Si activas ese flujo, súmalo al calendario de workflows del README y al inventario de
`scripts/audit_automatizacion.py`; esa auditoría conoce los flujos declarados y falla con uno
que no lo esté. Con MotherDuck el equivalente es una Action con el token como secreto que
ejecute el `CREATE TABLE ... AS SELECT` de la sección 6.

### Lo que no se actualiza solo

* **Camino A** (CSV subido a mano): es una foto; hay que volver a subir el archivo.
* **Camino B**: la hoja se refresca cuando se abre, y la caché de Sheets/Looker agrega su
  propio retraso.
* Un **conector comunitario copiado** en otra cuenta no se actualiza si el dueño de esa copia
  no vuelve a implementar: sólo lee el catálogo y los CSV publicados, así que en la práctica
  sigue al dato sin intervención.

---

## 10. Advertencias que conviene leer antes de publicar

* **Los marts agregan.** No permiten auditar una posición ni reconstruir un instrumento. Si
  el informe necesita ese nivel, el camino es BigQuery o MotherDuck sobre el Parquet.
* **Unidad y moneda funcional.** Sumar `valorizacion_miles_mf` de fondos con distinta moneda
  funcional es una suma de peras y manzanas. El agregado de industria se publica porque es
  lo que hace el sitio, pero un informe serio debería filtrar por fondo o por moneda.
* **Frescura.** El sitio se actualiza solo, varias veces al mes, y los marts se regeneran con
  el contrato derivado. Looker Studio cachea respuestas y Google Sheets refresca
  `IMPORTDATA` al abrir: un informe puede mostrar el corte anterior sin avisar. El corte
  vigente está en `catalogo.json` (`data_release`) y en la web.
* **Sin autenticación.** GitHub Pages sirve los CSV a cualquiera. Los datos son públicos y
  agregados; aun así, revisa [`PRIVACIDAD.md`](../../PRIVACIDAD.md) antes de combinarlos con
  datos propios.
* **Atribución.** La fuente es CMF, Banco Central de Chile y Superintendencia de Pensiones.
  Cita la fuente y el `data_release`. Condiciones en [`DATA_LICENSE.md`](../../DATA_LICENSE.md).

---

## 11. Mantenimiento

```bash
python3 scripts/build_marts_looker.py          # regenera marts y catálogo
python3 scripts/build_marts_looker.py --check  # falla si quedaron atrás
```

El flujo **«Contrato derivado»** (`.github/workflows/contrato_publicado.yml`) corre ambos
después de cada publicación de datos: si un publicador deja filas nuevas, los marts se
recalculan y se commitean en el mismo paso que el resto de los artefactos derivados.

Para agregar un mart, añade una entrada a `DEFINICIONES` en
`scripts/build_marts_looker.py` con su SQL, grano, unidad, objetos de origen y columnas
(`nombre`, `tipo`, `rol`, y `agregacion` si es métrica). El catálogo y el conector lo recogen
sin tocar nada más; el script falla si el CSV no publica exactamente las columnas declaradas.

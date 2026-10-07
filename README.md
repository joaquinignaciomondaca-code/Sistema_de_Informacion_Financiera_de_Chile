# Sistema de Información Financiera de Chile (SIF)

**25 años del sistema financiero chileno, consultables con SQL desde el navegador.**
Extrae, valida y publica lo que las entidades reportan a la CMF, el Banco Central, la Superintendencia de Pensiones y la SUSESO: **15 industrias, 75 tablas y 13,3 millones de filas** desde enero de 2001. Sin backend, sin base de datos, sin servidores — el dato viaja como Parquet estático y el motor corre en el cliente.

**▶ [Abrir el sistema](https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/)** — sin instalar nada, las consultas corren en tu navegador.

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![DuckDB-Wasm 1.28.0](https://img.shields.io/badge/DuckDB--Wasm-1.28.0-FFF000?logo=duckdb&logoColor=black)
![Sin backend](https://img.shields.io/badge/backend-ninguno-2ea44f)
![Datos](https://img.shields.io/badge/datos-75%20tablas%20%C2%B7%2013%2C3%20M%20filas-blue)
![Serie](https://img.shields.io/badge/serie-2001--01%20%E2%86%92%202026--08-informational)

| En números | |
|---|---|
| Historia cubierta | **25 años** · 2001-01 → 2026-08 |
| Industrias supervisadas | **15** (CMF · BCCh · SPensiones · SUSESO) |
| Tablas publicadas | **75** Parquet · 13.292.809 filas (manifiesto al 2026-10-06) · 283 MB |
| Consultas sugeridas listas para usar | **146** |
| Actualización | **16 workflows** en GitHub Actions (15 con horario; 1 solo por evento) |
| Verificación | **7 suites** de auditoría + **440** pruebas unitarias (97 de FI) |

---

## 1. El problema

Los datos del mercado financiero chileno son públicos, y son casi inusables.

Están repartidos entre cuatro organismos, en formatos que no conversan: TXT delimitados, XLSX, ZIP con XML/XBRL, PDF escaneados, HTML sin API. Cada fuente escribe el RUT a su manera, cada una nombra distinto la misma entidad, y ninguna garantiza que el archivo del mes que viene tenga las columnas de este mes.

El resultado práctico: **cruzar la cartera de una aseguradora con la de un fondo mutuo es un proyecto, no una consulta.** Un analista que quiera saber qué emisores concentran riesgo en dos industrias a la vez pasa más tiempo homologando identificadores que analizando.

Este proyecto convierte eso en una base de datos que se consulta en el navegador.

---

## 2. Qué puedes preguntarle

Las consultas se escriben en SQL estándar y se ejecutan **en tu máquina**, sobre los Parquet publicados. No hay servidor de datos ni se envía nada a terceros.

```sql
-- ¿Dónde invierten fuera de Chile los fondos mutuos, en el último mes publicado?
SELECT pais_emisor,
       count(*)                  AS posiciones,
       count(DISTINCT run_fondo) AS fondos
FROM ffmm_cartera_extranjera
WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_extranjera)
GROUP BY pais_emisor
ORDER BY posiciones DESC;
```

Resultado real, último período publicado:

| pais_emisor | posiciones | fondos |
|---|---:|---:|
| US | 1.131 | 148 |
| LU | 512 | 141 |
| IE | 489 | 101 |
| BR | 98 | 14 |
| GB | 84 | 43 |

Luxemburgo e Irlanda por delante de Brasil y Reino Unido: el patrón esperable de domiciliación de vehículos de fondos, visible en una consulta.

Y el caso que motiva el proyecto — **un emisor visto desde tres industrias a la vez**:

```sql
-- ¿Qué emisores concentran exposición simultánea de aseguradoras y fondos mutuos?
WITH bancos AS (
  SELECT rut, razon_social
  FROM bancos_lista_entidades
),
seguros AS (
  SELECT rut_emisor AS rut, count(DISTINCT rut_aseguradora) AS aseguradoras
  FROM seguros_renta_fija
  WHERE periodo = (SELECT max(periodo) FROM seguros_renta_fija)
  GROUP BY 1
),
fondos AS (
  SELECT rut_emisor AS rut, count(DISTINCT run_fondo) AS fondos_mutuos
  FROM ffmm_cartera_nacional
  WHERE periodo = (SELECT max(periodo) FROM ffmm_cartera_nacional)
  GROUP BY 1
)
SELECT b.razon_social AS emisor, s.aseguradoras, f.fondos_mutuos
FROM bancos b JOIN seguros s USING (rut) JOIN fondos f USING (rut)
ORDER BY s.aseguradoras + f.fondos_mutuos DESC;
```

| emisor | aseguradoras | fondos_mutuos |
|---|---:|---:|
| Banco de Credito e Inversiones | 57 | 205 |
| Banco Santander-Chile | 51 | 199 |
| Banco Itau Chile | 52 | 194 |
| Banco de Chile | 60 | 179 |
| Scotiabank Chile | 51 | 167 |
| Banco BICE | 50 | 161 |
| Banco del Estado de Chile | 53 | 145 |

Tres industrias cruzadas en 50 ms, en el navegador, con `JOIN`s directos: el RUT está homologado a toda la base bajo una convención canónica (sección 4).

La web trae **146 consultas sugeridas** organizadas por industria, para no partir de una pantalla en blanco. Cada resultado se ve como tabla o gráfico y se exporta a CSV, Excel o Parquet.

---

## 3. Los datos

**Actualización FI (2026-10-02):** el balance y los resultados de FIRES/FINRE desde XML FIEF
se publican con contextos separados, cuadraturas y cotejo por cuenta/columna. El cierre más reciente,
**2026-06**, incluye **908 fondos**, 66.864 filas de balance, 97.860 de resultados y **35.570
identidades contables verificadas**. El backfill ya cubre **16 cierres entre 2022-03 y 2026-06**
(985.908 filas de balance y 1.164.000 de resultados), pero aún faltan 2023-06, 2025-03 y cierres
anteriores a 2022; no se presenta como una serie continua. La corrida del 2026-10-04 se detuvo al
releer cierres históricos porque la CMF rechazó parte de las descargas; el último cierre y las carteras
siguen en 2026-06. Seis documentos y los contextos adicionales defectuosos se excluyen con motivo
explícito. [Fuente, controles y ejecución](fi/README.md).

*Cifras del manifiesto 2026-10-06; cada serie muestra su propio último período publicado.*

| Industria | Tablas | Filas | Serie | Fuente |
|---|---:|---:|---|---|
| Seguros de Vida y Generales | 9 | 4.103.093 | 2016-11 → 2026-08 | CMF · Circular 1835 |
| Fondos Mutuos | 7 | 3.582.929 | Carteras 2001-01 → 2026-08; EEFF 2010-12 → 2025-12 | CMF · Circulares 1333 y 1997 |
| Fondos de Inversión | 10 | 3.186.553 | Carteras 2020-03 → 2026-06; EEFF 2022-03 → 2026-06 (16 cierres, backfill parcial) | CMF · LUF / Circular 1998 · XML FIEF |
| Corredoras de Bolsa | 4 | 185.921 | 2010-12 → 2026-06 | CMF · FECU IFRS |
| Administradoras Generales de Fondos | 3 | 129.711 | 2010-06 → 2026-06 | CMF · IFRS |
| Macroeconomía y Tasas | 24 | 41.306 | diaria / mensual / trimestral | BCCh |
| Factoring y Leasing | 3 | 52.446 | 2009-03 → 2026-06 | CMF · IFRS |
| Sociedades Securitizadoras | 3 | 25.985 | 2009-12 → 2026-06 | CMF · IFRS |
| Cajas de Compensación | 3 | 13.555 | 2010-06 → 2026-06 | CMF · TXT IFRS (XBRL) |
| Patrimonios Separados | 2 | 7.981 | dic. 2014 → 2025 | CMF · PDF de estados financieros |
| Banca | 3 | 41 · 1,96 M † | 2022-01 → 2026-08 | CMF · B1/B2/R1 |
| FinTech | 1 | 263 | registro vigente | CMF · Ley 21.521 (RPSF) |
| Sistemas de Pago | 1 | 19 | registro vigente | BCCh / CMF |
| Fondos de Pensiones | 1 | 7 | registro vigente | SPensiones · D.L. 3.500 |
| Cooperativas de Ahorro y Crédito | 1 | 7 | registro vigente | CMF |
| **Total** | **75** | **13.292.809** | **2001 → 2026** | |

† En banca, *balance* y *resultados* son vistas filtradas sobre las mismas 56 particiones mensuales: B1 y B2 (722.931 filas) y R1 (1.240.061), sin solape. Por eso se cuentan como **un solo dataset** (1.962.992 filas) detrás de ambas vistas. El total del catálogo (75 salidas; 13.292.809 filas) cuenta esas particiones una sola vez.

### Operaciones REPO (pactos): cobertura vigente

- **Seguros:** `seguros_pactos`, mensual, hasta **2026-08** (155 filas en agosto; 11.153 en la serie).
- **Fondos de inversión:** `fi_pactos`, trimestral, hasta **2026-06** (40 filas en junio; 777 en la serie), con VRC y CRV.
- **Fondos mutuos:** no hay una tabla independiente de pactos/REPO en la extracción actual; su ausencia no equivale a cero operaciones.

Las corridas de seguros y carteras FI del 2026-10-04 terminaron bien y no publicaron un período nuevo. [Cobertura, fuentes, unidades y consultas SQL](docs/notas/cobertura_repos_pactos_2026-10-07.md).

Cada tabla publica su **manifiesto** —períodos, archivos y registros—, de modo que se puede verificar qué contiene la web. Donde la fuente es un archivo descargable único (banca B1/B2/R1, y los TXT IFRS de AGF, securitizadoras, cajas de compensación y factoring/leasing) el manifiesto además guarda el **SHA-256 del archivo de origen**, y ahí se puede comprobar que lo publicado sale exactamente de lo descargado. En los estados financieros de fondos mutuos cada fila lleva el nombre y el SHA-256 del XML de origen (`fuente_archivo`, `sha256_archivo`). En seguros, carteras de fondos mutuos, fondos de inversión y corredoras el extractor guarda el SHA-256 de lo que devolvió la CMF (`sha256_origen` en el manifiesto) **solo para los períodos que se publiquen desde el 2026-09-29**: los anteriores se descargaron sin registrar hash y no se pueden reconstruir. En fondos de inversión, que son miles de páginas por trimestre, se guarda un hash que las resume. Macroeconomía, pensiones, fintech y los registros vigentes (listas de entidades) no tienen hash de origen.

Las marcas de tiempo de los manifiestos (`updated_at`, `ultima_actualizacion`, `leido_utc`) indican cuándo **cambió** algo, no cuándo corrió el workflow: si una corrida no trae datos nuevos, el extractor no reescribe el manifiesto (ni se crea commit ni se regenera el catálogo). Que los workflows siguen corriendo se comprueba con sus corridas en Actions (`audit_automatizacion.py --frescura`). Los trimestres IFRS ya leídos cuyo TXT de origen no cambió (mismo SHA-256) tampoco se reescriben ni se vuelven a desplegar. Excepción: el monitor normativo registra cada revisión a propósito.

---

## 4. Por qué confiar en la cifra

Un dato financiero mal extraído es peor que no tener el dato. El sistema valida **antes** de publicar y se detiene si algo no cuadra:

- **Identidad**: RUT validado con dígito verificador módulo 11 y homologado **a toda la base** bajo una convención canónica (cuerpo / cuerpo-DV / puntos, según la columna).
- **Cuadraturas contables**: activos = pasivos + patrimonio. En los estados financieros IFRS de AGF, securitizadoras, cajas de compensación, factoring y leasing, corredoras y fondos mutuos (donde la identidad es activo − pasivo = activo neto atribuible a los partícipes) se verifica antes de publicar: un balance aislado que no cuadra queda registrado como aviso (en el manifiesto o en la metadata de la serie), y si la lectura falla en bloque (al menos 3 balances y más del 5 %) el trimestre no se publica. Banca cotea el total de activos contra el Excel de la CMF y fondos de inversión cuadra cada cartera con la fila TOTAL de la fuente. Patrimonios separados cuadra cada balance (±2 mil pesos) y sus subtotales al compilar el Parquet. Además, `scripts/auditar_eeff_ifrs.py` repasa en cada push y PR **toda la historia publicada** de AGF, securitizadoras, CCAF, factoring y leasing, corredores y fondos mutuos (hoy cuadran todos, con diferencias de hasta 1 mil pesos por redondeo).
- **Cobertura mínima**: si un mes trae menos del 90 % de las entidades del mes anterior, no se publica. En los estados financieros, además, si casi ningún balance trae los tres totales reconocibles (cambiaron las glosas o los códigos), el trimestre tampoco se publica.
- **Cierres reeditados**: la CMF reedita a veces cierres antiguos y lo avisa en su índice («actualizado: …»). Si la fecha es posterior a la última lectura, el trimestre se vuelve a leer y pasa las mismas compuertas; si no las cumple, se conserva lo publicado. (Corredores y agentes no la tienen: su informe no trae esa fecha. En fondos mutuos no hay índice con fecha: el nombre del XML lleva la fecha y hora de envío, así que cada corrida revisa las fichas de los dos últimos cierres y de 1/36 del resto —toda la historia una vez al año— y baja de nuevo solo los archivos cuyo nombre cambió.)
- **Legibilidad**: más de 1 % de filas ilegibles en un archivo aborta el proceso.
- **Esquema**: si la fuente cambia las columnas, el flujo falla en vez de publicar basura.

Cuando algo falla, la web dice «no disponible». Nunca un número inventado.

**Convención canónica de RUT.** Antes del 2026-09-29 el RUT estaba homologado solo *dentro* de cada industria: convivían tres convenciones (`12.345.678-9`, `12345678-9`, `12345678`) según el origen del archivo, y un `JOIN` directo entre sectores devolvía cero filas en silencio, que es la peor forma de fallar. Ahora toda la base publica bajo una convención única — `rut` = cuerpo, `rut_dv` = cuerpo-DV, `rut_completo` = puntos y DV —, los `JOIN` directos funcionan (los 147 emisores que comparten aseguradoras y fondos mutuos salen sin trucos, y 15 de ellos también son bancos, como en el ejemplo de arriba), y un guardián en CI (`scripts/audit_rut_formatos.py`) detiene cualquier corrida que publique otro formato. La auditoría completa, columna por columna, y el registro de la corrección están en [`docs/notas/rut_formatos_2026-09-29.md`](docs/notas/rut_formatos_2026-09-29.md).

---

## 5. La web

Aplicación estática de siete pestañas, sin framework y sin build:

| Pestaña | Qué hace |
|---|---|
| **Información** | Cobertura, fuentes y estado de cada industria. |
| **Mapa relacional** | Diagrama entidad-relación con zoom, paneo y enlaces entre tablas. |
| **Diccionario** | Campo por campo: rol (PK, FK, dimensión, métrica), definición y criterio contable. |
| **Visor de datos** | Consulta tabular con filtro, orden y copia de celdas. |
| **Consultas SQL** | Terminal con autocompletado, historial, favoritos y enlaces compartibles. |
| **Descargas** | Los 75 conjuntos con filas, período y peso, en Parquet, CSV y Excel. |
| **Normativa CMF** | Seguimiento de la normativa publicada por la CMF (ver §7.6). |

El **explorador jerárquico** organiza 12 industrias → 15 sectores → 45 carpetas temáticas → 75 tablas, con consultas sugeridas en cada carpeta. El motor DuckDB-Wasm 1.28.0 va **embebido en el propio sitio** (`docs/vendor/duckdb/`), así que las consultas funcionan aunque la red del visitante bloquee los CDN públicos.

### Verlo funcionando

```bash
git clone https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile
cd Sistema_de_Informacion_Financiera_de_Chile
python3 -m scripts.preview_no_cache --port 8000     # sirve docs/ sin caché, con soporte HTTP Range
# → http://localhost:8000
```

El servidor local responde `206 Partial Content` igual que GitHub Pages, así que DuckDB-Wasm lee sólo el pie y los grupos de fila que necesita en vez de bajar archivos completos.

---

## 6. Se mantiene solo

Hay **16 workflows** en GitHub Actions: **15 tienen horario (`schedule`)** y `fi_cobertura_eeff.yml` se activa solo por evento; varios de los programados también corren en `push`, `pull_request` o `workflow_dispatch`. Un **guardián de automatización** cruza el manifiesto de datos, el inventario de flujos y las vistas del sitio: cada tabla publicada tiene un responsable declarado, y si una fuente se atrasa más allá de su plazo, se abre un issue automáticamente.

La ausencia de un workflow no implica ausencia de procesamiento automático. El catálogo distingue tres modalidades: **Automático** (extracción, validación y publicación programadas), **Híbrido** (extracción o curación inicial local desde fuentes no estructuradas, seguida de validación y compilación reproducibles) y **Manual** (intervención todavía no respaldada por un compilador reproducible). El balance de patrimonios separados es actualmente híbrido: la CMF publica los estados como PDF, la consolidación inicial se hace fuera de Actions y `05_publicar_balance_patrimonios.py` ejecuta las validaciones y genera el Parquet.

<details>
<summary>Calendario de los 16 flujos</summary>

| Flujo | Frecuencia (UTC) | Publica |
|---|---|---|
| `macro.yml` | diario 10:00 | Macro BCCh: 51 series nativas → 23 tablas temáticas (tasas, tipo de cambio, precios, actividad, laboral, materias primas, sector externo, expectativas) + catálogo |
| `factoring_leasing_backfill.yml` | cada 3 días, 12:20 | Serie IFRS de balance y resultados |
| `bancos_cmf_mensual.yml` | cada 3 días, 13:00 | Particiones B1/B2/R1 de la CMF (incremental) |
| `ifrs_sectores.yml` | cada 3 días, 13:30 | Estados IFRS de AGF, securitizadoras y CCAF |
| `ifrs_sondeo.yml` | día 5, 13:40 | nada: describe qué sociedades del TXT IFRS quedan fuera (solo lectura) |
| `corredoras_eeff.yml` | cada 3 días, 13:45 | FECU IFRS de corredores y agentes de valores |
| `seguros_carteras.yml` | cada 3 días, 14:00 | Cartera de inversiones Circular 1835 |
| `ffmm_carteras.yml` | cada 3 días, 14:00 | Cartera de fondos mutuos Circular 1333 |
| `web_audit.yml` | lunes 14:00, push y PR | nada: auditorías del sitio + guardián de frescura |
| `ffmm_eeff.yml` | cada 3 días, 14:20 | Balance y estado de resultados anuales de fondos mutuos (XML IFRS, Circular 1997) |
| `fi_carteras.yml` | cada 3 días, 15:00 | Cartera y pactos de fondos de inversión |
| `fi_eeff.yml` | cada 3 días, 15:35 | Balance y resultados anuales de fondos de inversión (XML IFRS) |
| `entidades.yml` | días 10, 20 y 28, 12:30 | Altas y vigencia de las listas de entidades |
| `normativa_cmf.yml` | lunes a viernes, 13:23 | Feed de normativa publicada por la CMF |
| `fi_cobertura_eeff.yml` | sin horario (push) | nada: revisión de cobertura de FI (solo lectura) |
| `pages.yml` | cada 6 h (03:15, 09:15, 15:15, 21:15) y push a `main` | Despliegue de `docs/` en GitHub Pages |

Cada publicador deja su rastro en la cabecera del archivo de datos y en `data_manifest.json`; los horarios
son los `cron` reales de `.github/workflows/*.yml`.

</details>

<details>
<summary>Auditorías que corren en cada push y PR</summary>

```bash
python scripts/audit_web_full.py            # Parquet, enlaces, chips SQL, diccionario y ERD
python scripts/audit_interfaz.py            # pestañas, catálogo, vocabulario, temas, motor
python scripts/audit_navigation.py          # taxonomía: 12 familias, 75 tablas, 75 opciones del visor
python scripts/audit_automatizacion.py      # quién actualiza cada tabla y con qué frecuencia
python scripts/build_download_catalog.py --check   # el catálogo refleja lo publicado
python scripts/normalizar_vocabulario.py --check   # los nombres no se desincronizan
```

Más `audit_interfaz_dom.js` (comportamiento en un DOM real), `audit_normativa_web.js` y `audit_secretos.py`. **Todo workflow que escribe en la rama corre sus pruebas unitarias antes del `git commit`** —incluidos macro, entidades, carteras de FI y de fondos mutuos, cuya auditoría `web_audit` no cubre en las corridas programadas— y lo vigila `pipelines/auto/tests/test_contrato_publicadores.py`, que además exige que el `timeout-minutes` del job cubra el presupuesto `--minutos` del extractor y que los módulos compartidos que un publicador importa estén en sus `on.push.paths`. `web_audit.yml` ejecuta en cada push y PR todas las pruebas de los extractores de estados financieros, macro y seguros (más de 300, sin red y con fuentes sintéticas).

</details>

---

## 7. Decisiones de diseño

1. **Sin backend.** Parquet estático + HTTP Range + DuckDB-Wasm: cero infraestructura y ninguna copia de los datos fuera de la fuente. El mismo archivo que se descarga es el que se consulta, así que cualquiera puede recalcular el resultado por su cuenta.
2. **Fail-closed antes que «algo es mejor que nada».** Publicar un balance descuadrado es peor que no publicarlo: quien lo use tomará una decisión con un número falso sin saberlo. Por eso la validación aborta en vez de degradar.
3. **Un vocabulario, no convenciones orales.** Todo nombre visible vive en `docs/vocabulario.json` y un verificador recorre el repositorio; los sinónimos desaparecieron de la interfaz por construcción, no por disciplina.
4. **Compatibilidad sin contaminar.** Los nombres históricos siguen funcionando como alias en SQL, pero no se sugieren en pantalla: quien tenía una consulta guardada no se rompe, y quien llega nuevo ve un solo criterio.
5. **Auditorías como contrato ejecutable.** Cada promesa de este README se traduce en un chequeo automático. Si el catálogo de la web y los Parquet publicados divergen, el push falla.
6. **El modelo lee prosa, nunca cifras.** El único flujo con lectura asistida es el de normativa CMF, donde la fuente son PDF jurídicos sin formato estable. El modelo devuelve JSON contra un esquema cerrado, con tope de llamadas por corrida, el texto del documento tratado como dato no confiable —no como instrucción— y marca `needs_human_review` cuando la evidencia es incompleta. Cada ficha conserva sus citas y el enlace al documento oficial. Los estados financieros, carteras y series macro se parsean con código determinista y se validan contra cuadraturas: **ningún número publicado proviene de un modelo.**

---

## 8. Próximos pasos

- **Más profundidad por entidad**: incorporar las notas a los estados financieros y otros desgloses que hoy quedan fuera del dato tabular (comisiones, juicios pendientes, vencimientos, covenants).
- **Nuevas fuentes de interés** para completar la vista por industria.

---

## 9. Documentación

[`PSEUDOCODIGO.md`](PSEUDOCODIGO.md) — mapa de código, estructura del repositorio y decisiones ·
[`pipelines/README.md`](pipelines/README.md) — operación de datos y credenciales ·
[`docs/vendor/duckdb/README.md`](docs/vendor/duckdb/README.md) — cómo se vendoriza el motor ·
READMEs por sector en `bancos/`, `ccaf/`, `factoring_leasing/`, `ffmm/`, `fi/`, `macro/`, `pensiones/` y `seguros/`.

---

## Autor

**Joaquín Mondaca** — [LinkedIn](https://www.linkedin.com/in/joaqu%C3%ADnmondaca/) · [GitHub](https://github.com/joaquinignaciomondaca-code)

Proyecto de datos de punta a punta: extracción, validación estadística y contable, publicación incremental, automatización y producto web.

## Licencia

© 2026 Joaquín Mondaca. Todos los derechos reservados; el código se publica para consulta y evaluación técnica. Los datos pertenecen a sus fuentes oficiales (CMF, Banco Central de Chile, SPensiones, SUSESO) y se publican tal como ellas los emiten.

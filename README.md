# Sistema de Información Financiera de Chile (SIF)

**25 años del sistema financiero chileno, consultables con SQL desde el navegador.**
Extrae, valida y publica lo que las entidades reportan a la CMF, el Banco Central, la Superintendencia de Pensiones y la SUSESO: **15 industrias, 52 tablas, 10,9 millones de filas** desde enero de 2001. Sin backend, sin base de datos, sin servidores — el dato viaja como Parquet estático y el motor corre en el cliente.

**▶ [Abrir el sistema](https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/)** — sin instalar nada, las consultas corren en tu navegador.

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![DuckDB-Wasm 1.28.0](https://img.shields.io/badge/DuckDB--Wasm-1.28.0-FFF000?logo=duckdb&logoColor=black)
![Sin backend](https://img.shields.io/badge/backend-ninguno-2ea44f)
![Datos](https://img.shields.io/badge/datos-52%20tablas%20%C2%B7%2010%2C9%20M%20filas-blue)
![Serie](https://img.shields.io/badge/serie-2001--01%20%E2%86%92%202026--08-informational)

| En números | |
|---|---|
| Historia cubierta | **25 años** · 2001-01 → 2026-08 |
| Industrias supervisadas | **15** (CMF · BCCh · SPensiones · SUSESO) |
| Tablas publicadas | **52** Parquet · 10.870.763 filas · 273 MB |
| Consultas sugeridas listas para usar | **116** |
| Actualización | **11 flujos** automáticos en GitHub Actions |
| Verificación | **7 suites** de auditoría + **130** pruebas unitarias |

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

La web trae **116 consultas sugeridas** organizadas por industria, para no partir de una pantalla en blanco. Cada resultado se ve como tabla o gráfico y se exporta a CSV, Excel o Parquet.

---

## 3. Los datos

| Industria | Tablas | Filas | Serie | Fuente |
|---|---:|---:|---|---|
| Seguros de Vida y Generales | 9 | 4.103.093 | 2016-11 → 2026-08 | CMF · Circular 1835 |
| Fondos Mutuos | 5 | 3.306.744 | 2001-01 → 2026-08 | CMF · Circular 1333 |
| Fondos de Inversión | 8 | 1.036.645 | 2020-03 → 2026-06 | CMF · LUF / Circular 1998 |
| Corredoras de Bolsa | 4 | 185.921 | 2010-12 → 2026-06 | CMF · FECU IFRS |
| Administradoras Generales de Fondos | 3 | 129.711 | 2010-06 → 2026-06 | CMF · IFRS |
| Macroeconomía y Tasas | 5 | 80.375 | diaria → mensual | BCCh |
| Factoring y Leasing | 3 | 52.446 | 2009-03 → 2026-06 | CMF · IFRS |
| Sociedades Securitizadoras | 3 | 25.985 | 2009-12 → 2026-06 | CMF · IFRS |
| Cajas de Compensación | 3 | 13.555 | 2010-06 → 2026-06 | CMF · TXT IFRS (XBRL) |
| Patrimonios Separados | 2 | 7.981 | dic. 2014 → 2025 | CMF · PDF de estados financieros |
| Banca | 3 | 41 · 1,93 M † | 2022-01 → 2026-07 | CMF · B1/B2/R1 |
| FinTech | 1 | 263 | registro vigente | CMF · Ley 21.521 (RPSF) |
| Sistemas de Pago | 1 | 19 | registro vigente | BCCh / CMF |
| Fondos de Pensiones | 1 | 7 | registro vigente | SPensiones · D.L. 3.500 |
| Cooperativas de Ahorro y Crédito | 1 | 7 | registro vigente | CMF |
| **Total** | **52** | **10.870.763** | **2001 → 2026** | |

† En banca, *balance* y *resultados* son vistas filtradas sobre las mismas 55 particiones mensuales: B1 y B2 (710.025 filas) y R1 (1.217.939), sin solape. Por eso el manifiesto las declara como **un solo datasete** (1.927.964 filas) detrás de las dos vistas: 52 tablas publicadas = 51 datasets, cada uno contado una vez, y la pestaña Descargas muestra el total completo de 10.870.763 sin doble contar las particiones de banca.

Cada tabla publica su **manifiesto** —períodos, archivos, registros y hash de origen—, de modo que se puede verificar que lo que muestra la web es exactamente lo que se descargó de la fuente.

---

## 4. Por qué confiar en la cifra

Un dato financiero mal extraído es peor que no tener el dato. El sistema valida **antes** de publicar y se detiene si algo no cuadra:

- **Identidad**: RUT validado con dígito verificador módulo 11 y homologado **a toda la base** bajo una convención canónica (cuerpo / cuerpo-DV / puntos, según la columna).
- **Cuadraturas contables**: activos = pasivos + patrimonio. Un balance que no cuadra detiene la publicación.
- **Cobertura mínima**: si un mes trae menos del 90 % de las entidades del mes anterior, no se publica.
- **Legibilidad**: más de 1 % de filas ilegibles en un archivo aborta el proceso.
- **Esquema**: si la fuente cambia las columnas, el flujo falla en vez de publicar basura.

Cuando algo falla, la web dice «no disponible». Nunca un número inventado.

**Convención canónica de RUT.** Antes del 2026-09-29 el RUT estaba homologado solo *dentro* de cada industria: convivían tres convenciones (`12.345.678-9`, `12345678-9`, `12345678`) según el origen del archivo, y un `JOIN` directo entre sectores devolvía cero filas en silencio, que es la peor forma de fallar. Ahora toda la base publica bajo una convención única — `rut` = cuerpo, `rut_dv` = cuerpo-DV, `rut_completo` = puntos y DV —, los `JOIN` directos funcionan (los 147 emisores que comparten aseguradoras y fondos mutuos salen sin trucos, como en el ejemplo de arriba), y un guardián en CI (`scripts/audit_rut_formatos.py`) detiene cualquier corrida que publique otro formato. La auditoría completa, columna por columna, y el registro de la corrección están en [`docs/notas/rut_formatos_2026-09-29.md`](docs/notas/rut_formatos_2026-09-29.md).

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
| **Descargas** | Los 52 conjuntos con filas, período y peso, en Parquet, CSV y Excel. |
| **Normativa CMF** | Seguimiento de la normativa publicada por la CMF (ver §7.6). |

El **explorador jerárquico** organiza 12 industrias → 15 sectores → 38 carpetas temáticas → 52 tablas, con consultas sugeridas en cada carpeta. El motor DuckDB-Wasm 1.28.0 va **embebido en el propio sitio** (`docs/vendor/duckdb/`), así que las consultas funcionan aunque la red del visitante bloquee los CDN públicos.

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

Once flujos programados en GitHub Actions extraen, validan y publican con commit controlado. Un **guardián de automatización** cruza el manifiesto de datos, el inventario de flujos y las vistas del sitio: cada tabla publicada tiene un responsable declarado, y si una fuente se atrasa más allá de su plazo, se abre un issue automáticamente.

<details>
<summary>Calendario de los 11 flujos</summary>

| Flujo | Frecuencia | Publica |
|---|---|---|
| `macro.yml` | diario | Macro BCCh: tasas, divisas, precios y catálogo de series |
| `bancos_cmf_mensual.yml` | días 1, 11, 21 | Particiones B1/B2/R1 de la CMF (incremental) |
| `ifrs_sectores.yml` | días 2, 12, 22 | Estados IFRS de AGF, securitizadoras y CCAF |
| `factoring_leasing_backfill.yml` | días 3, 13, 23 | Serie IFRS de balance y resultados |
| `corredoras_eeff.yml` | días 6, 16, 26 | FECU IFRS de corredores y agentes de valores |
| `seguros_carteras.yml` | días 7, 17, 27 | Cartera de inversiones Circular 1835 |
| `ffmm_carteras.yml` | días 8, 18, 28 | Cartera de fondos mutuos Circular 1333 |
| `fi_carteras.yml` | días 9, 19, 29 | Cartera y pactos de fondos de inversión |
| `entidades.yml` | días 10, 20, 28 | Altas y vigencia de las listas de entidades |
| `normativa_cmf.yml` | lunes a viernes | Normativa publicada por la CMF |
| `web_audit.yml` | lunes, push y PR | Auditorías del sitio + guardián de frescura |
| `pages.yml` | push a `main` | Despliegue del sitio estático |

</details>

<details>
<summary>Auditorías que corren en cada push y PR</summary>

```bash
python scripts/audit_web_full.py            # Parquet, enlaces, chips SQL, diccionario y ERD
python scripts/audit_interfaz.py            # pestañas, catálogo, vocabulario, temas, motor
python scripts/audit_navigation.py          # taxonomía: 12 familias, 52 tablas, 52 opciones del visor
python scripts/audit_automatizacion.py      # quién actualiza cada tabla y con qué frecuencia
python scripts/build_download_catalog.py --check   # el catálogo refleja lo publicado
python scripts/normalizar_vocabulario.py --check   # los nombres no se desincronizan
```

Más `audit_interfaz_dom.js` (comportamiento en un DOM real), `audit_normativa_web.js` y `audit_secretos.py`. Los flujos maduros —bancos, factoring-leasing, macro y normativa— corren además sus **130 pruebas unitarias** antes de publicar.

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
READMEs por sector en `bancos/`, `ccaf/`, `factoring_leasing/`, `fi/`, `macro/` y `pensiones/`.

---

## Autor

**Joaquín Mondaca** — [LinkedIn](https://www.linkedin.com/in/joaqu%C3%ADnmondaca/) · [GitHub](https://github.com/joaquinignaciomondaca-code)

Proyecto de datos de punta a punta: extracción, validación estadística y contable, publicación incremental, automatización y producto web.

## Licencia

© 2026 Joaquín Mondaca. Todos los derechos reservados; el código se publica para consulta y evaluación técnica. Los datos pertenecen a sus fuentes oficiales (CMF, Banco Central de Chile, SPensiones, SUSESO) y se publican tal como ellas los emiten.

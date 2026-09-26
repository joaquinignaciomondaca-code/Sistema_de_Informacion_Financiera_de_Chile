# Auditoría del sector Factoring & Leasing — 2026-09-26

Alcance: `factoring_leasing/scripts/*`, `docs/outputs/factoring_leasing/*`, entradas del sector en
`data_manifest.json`, `docs/js/sidebar.js` y `docs/js/data_dictionary.js`.
Método: lectura de código + consultas DuckDB sobre los 4 Parquet publicados. Todo lo reportado es
reproducible con `python factoring_leasing/scripts/audit_factoring_leasing_v2.py`.

Severidad: 🔴 bloqueante · 🟠 alta · 🟡 media · 🟢 baja/mejora.

---

## Resumen ejecutivo

| # | Hallazgo | Sev. |
|---|----------|------|
| 1 | Credencial BCCh (email + contraseña) hardcodeada en el repo público | 🔴 |
| 2 | Las dos tablas de "notas desagregadas" (2.975 + 17.406 filas) son **sintéticas**: porcentajes fijos aplicados al balance, no extracción CMF. Están publicadas como "Automático / CMF" | 🔴 |
| 3 | Pipeline principal no reproducible: depende de rutas `C:\Users\joaqu\Desktop\Respaldo_BCCH\...` y de un Excel externo; el catálogo CSV de entidades está git-ignorado | 🟠 |
| 4 | `cartera_credito` = "Deudores comerciales" subestima gravemente la cartera de leasing/automotriz (Gama 9 %, GM 31 %, Forum 47 % de activos) | 🟠 |
| 5 | Inconsistencias maestro ↔ balances: 3 entidades "Histórico/Cancelado" con EEFF hasta 2026-03; 4 filiales bancarias "Activas" sin ningún balance | 🟠 |
| 6 | La auditoría existente (`audit_factoring_leasing.py`) reporta "100 % EXITOSA … más altos estándares" sobre datos sintéticos; no valida procedencia ni plausibilidad | 🟠 |
| 7 | Cuadre contable tautológico: `patrimonio = activos − pasivos` cuando falta la cuenta; `total_pasivos = PC + PNC` por construcción | 🟡 |
| 8 | Tipo de cambio: fallback silencioso `900.0`/`850.0` si falta el período; `ssl.CERT_NONE` en todas las descargas | 🟡 |
| 9 | Huecos y anomalías de serie no documentados (Penta 15 trimestres faltantes y salto +151 %; SMB patrimonio negativo; Mercantil 11/45 trimestres) | 🟡 |
| 10 | Nomenclatura no homogénea con el resto del repo (`_m_clp` vs `_mclp` vs `_musd`; `periodo` `YYYY-MM` aquí vs `YYYYMM` en FFMM/FI) | 🟡 |
| 11 | Descripciones en `data_dictionary.js` prometen divisas "USD, EUR, GBP" y "cuentas bancarias"; los datos sólo contienen CLP/USD generados | 🟢 |

Lo que **sí** está bien: `factoring_leasing_maestro` (28 RUT válidos módulo 11, sin duplicados),
`factoring_leasing_balance_resumen` (878 filas, clave única, 0 nulos, cuadre A = P + Pat a 0,01 M$,
49 trimestres 2014-03 → 2026-03, magnitudes plausibles: Forum 2,65 y Tanner 2,23 billones CLP a 2025-12,
tipo de cambio implícito coherente con el dólar observado de cierre). El extractor
`stream_cmf_eeff_series.py` (CMF texto plano `ver_archivo.php`) es el único pipeline realmente
autónomo del sector y es una buena base.

---

## 1. 🔴 Credencial expuesta

`pipeline_stream_factoring_leasing.py:59`
```python
siete = bcchapi.Siete("<correo>", "<contraseña en texto plano>")   # redactado en este informe
```
La misma contraseña aparece como `PASS_BCCH = "..."` en `bancos/scripts/pipeline_stream_derivados_bcch.py`,
`macro/scripts/pipeline_stream_macro_bcch.py` y `sistemas_pago/scripts/stream_sistemas_pago.py`.
El repositorio es **público** (`gh api repos/... → visibility: public`).

**Acción (dueño del repo, hoy):** cambiar la contraseña en el portal SIETE del BCCh. Si está
reutilizada en el correo u otros servicios, cambiarla también.

**Acción (agente de arreglos):**
- Reemplazar por `os.environ["BCCH_USER"]` / `os.environ["BCCH_PASS"]` (fallar con mensaje claro si faltan).
- Añadir `.env` a `.gitignore` y un `.env.example`.
- Aunque el historial tiene 1 commit, la versión pública ya la expone; tras rotar, opcionalmente
  reescribir historia (`git filter-repo`) y forzar push, pero la rotación es lo esencial.
- Añadir al CI un scan de secretos (`gitleaks` o `detect-secrets`).

## 2. 🔴 Notas "desagregadas" sintéticas publicadas como datos CMF

`02_extract_factoring_leasing_notas_series.py` define `fetch_cmf_pdf_stream()` (descarga del PDF
de EEFF desde CMF) pero **nunca lo llama**. `extract_all()` genera las dos tablas así:

```python
# Nota efectivo
pct_bancos_clp = 0.78; pct_dap_fmm = 0.20; pct_caja = 0.02
items_cash = [("Saldos en cuentas corrientes ...", "CLP", activos_liq * pct_bancos_clp), ...]
# Nota cartera / morosidad
tramos_dist = [("Vigente / Al dia", "Etapa 1", 0.885, 0.008), ("Mora 1 a 30 dias", "Etapa 1", 0.052, 0.035), ...]
bruta_mclp = cartera_prod * pct_tramo; prov_mclp = bruta_mclp * tasa_prov
```

Evidencia en los datos publicados (`audit_v2`, check `synthetic_shares`):

| Tabla | Concepto | Participación mín–máx en 100 % de entidades/períodos |
|---|---|---|
| nota_efectivo | Saldos en bancos moneda extranjera (USD) | 25,00 % – 25,00 % |
| nota_efectivo | Pactos de liquidez / CRV | 50,00 % – 50,00 % |
| cartera_morosidad | Vigente / Al día | 88,1 % – 88,6 % (2.901 filas, 24 entidades, 49 trimestres) |
| cartera_morosidad | Mora > 180 días | 1,35 % – 1,69 % |

Ninguna cartera real de 24 empresas durante 12 años mantiene la misma estratificación de mora al
décimo de punto. Además, `numero_nota` está fijado por un diccionario manual (`"Nota 5"/"Nota 7"`
por defecto) sin verificar contra ningún documento.

Mientras tanto, el manifest y `data_dictionary.js` las presentan como:
`modo: "Automático"`, `origen: "CMF — Notas a los Estados Financieros de Sociedades de Factoring y
Leasing"`, y el sidebar expone chips como *"Estratificación de Morosidad por Tramos"* y
*"Provisiones IFRS 9 por Etapas de Riesgo"*.

Para un proyecto cuyo argumento central es "dato fuente auditable → transformación propia", esto
es el riesgo reputacional más grande del repo. Un revisor de CMF/BCCh que abra esa tabla lo detecta
en minutos.

**Acción (agente de arreglos), en este orden:**
1. **Retirar de la publicación** ambas tablas (Parquet + JSON), sus entradas en `data_manifest.json`,
   `sidebar.js`, `data_dictionary.js` y `erd_graph.js`. No dejarlas "por mientras".
2. Si se quiere conservar el script como *scaffold*, renombrarlo (`_MOCK_` / `_TEMPLATE_`), moverlo
   fuera de `scripts/` y dejar en el docstring, en mayúsculas, que genera datos ficticios.
3. Reimplementar la extracción real por uno de estos caminos (ordenados por costo):
   - **XBRL CMF** (`estados financieros (XBRL)` en la ficha del emisor RVEMI): las notas de efectivo
     y de deudores/deterioro suelen venir taggeadas (`ifrs-full:CashAndCashEquivalents` con
     desgloses en `cl-ci`/extensión del emisor). Es el mismo camino que ya usa `ccaf/scripts/pipeline_extract_ccaf_xbrl.py`.
   - PDF + `pdfplumber` con localización de la nota por título (el `fetch_cmf_pdf_stream` ya existe),
     con validación obligatoria: suma de líneas de la nota = cuenta del balance (`activos_liquidos`
     / `cartera_credito`) con tolerancia ≤ 0,5 %.
   - Pipeline manual NotebookLM (ya documentado en `pipelines/manual/`) etiquetado como `modo: Manual`.
4. Cualquier tabla reconstruida debe llevar columnas de procedencia: `fuente_url`, `metodo`
   (`xbrl|pdf|manual`), `fecha_extraccion`, `script_version`, y un check de reconciliación
   con el balance que falle en CI.

## 3. 🟠 Pipeline no reproducible / etiqueta "Automático" incorrecta

`pipeline_stream_factoring_leasing.py`:
```python
BASE_RESPALDO = r"C:\Users\joaqu\Desktop\Respaldo_BCCH"
RUTA_SOCIEDADES = ...\"Sociedades leasing y factoring.xlsx"
RUTA_METRICAS   = ...\"Metricas_Finales_Entregable.xlsx"  (o ...\FSB\...\Metricas_FSB_Finales_Entregable.xlsx)
df_raw = pd.read_excel(RUTA_METRICAS, sheet_name="Metricas_Empresas")   # AUM, NAV, Credit_Assets, ...
```
- El balance se construye desde un Excel de un trabajo previo, no desde CMF. `stream_cmf_eeff_series.py`
  sí baja de CMF, pero ambos escriben el **mismo** `factoring_leasing_balance_resumen.parquet` y no
  está documentado cuál produjo el archivo publicado (el docstring del primero dice "2018 a 2026";
  los datos van desde 2014-03, lo que sugiere que fue el segundo).
- Ambos scripts leen `factoring_leasing/data/catalogo_factoring_leasing_cmf.csv`, que **no existe en el
  repo** porque `.gitignore` tiene `*.csv`. Nadie puede regenerar el maestro.
- `pipelines/auto/README.md` referencia `factoring_leasing/scripts/stream_cmf_factoring_leasing.py`,
  archivo que no existe.

**Acción:** dejar un único pipeline (`stream_cmf_eeff_series.py`) como fuente del balance, borrar o
archivar el basado en Excel, versionar el catálogo (excepción en `.gitignore` o convertirlo a
`catalogo_factoring_leasing_cmf.json`), corregir el README de pipelines, y añadir `requirements.txt`
del sector (`pandas`, `pyarrow`, `pdfplumber`, `beautifulsoup4`, `bcchapi`).

## 4. 🟠 Definición de `cartera_credito` incorrecta para leasing/automotriz

`stream_cmf_eeff_series.py` suma sólo:
```
Deudores comerciales y otras cuentas por cobrar (corrientes / no corrientes)
```
Ratio `cartera_credito / total_activos` a 2025-12: Gama **0,09**, Concreces 0,15, Unidad Leasing 0,19,
GM Financial 0,31, Global 0,33, Tanner 0,36, Santander Consumer 0,40, Forum 0,47. Para financieras
cuyo negocio es prestar, eso indica que la cartera está en otras cuentas de la taxonomía CMF
(p. ej. *"Cuentas por cobrar por arrendamientos financieros"*, *"Otros activos financieros
corrientes/no corrientes"*, *"Colocaciones"* en emisores con plan de cuentas propio). El chip
*"Ranking Cartera de Crédito"* del sidebar hoy ordena mal a las entidades.

**Acción:** volcar todas las cuentas del archivo CMF a formato largo (`cuenta`, `valor`) antes de
resumir, y construir `cartera_credito` con un mapeo explícito por entidad/taxonomía documentado en
`factoring_leasing/README.md`. Añadir check: `cartera_credito/total_activos ≥ 0,5` salvo excepción
justificada.

## 5. 🟠 Maestro ↔ balances inconsistentes

| Entidad | Maestro | Balances |
|---|---|---|
| Concreces Leasing | `vigente=0`, "Histórico / Cancelado" | 49/49 trimestres hasta 2026-03 |
| HLC / Vive Leasing | `vigente=0` | 48 trimestres hasta 2026-03 |
| Interfactor | `vigente=0`, "No en CMF con este RUT" | 48 trimestres hasta 2025-12 |
| BCI Factoring, BICE Factoring, Scotia Azul Leasing, Bandesarrollo Leasing | `vigente=1`, "Activo" | **0** balances |

Las 4 filiales bancarias reportan bajo norma bancaria (no en `ver_archivo.php` de emisores), así que
el sidebar ("28 entidades, 22 activas") sobrevende la cobertura: hay 24 con datos y 21 al último corte.

**Acción:** corregir `vigente` de las 3 primeras; para las filiales bancarias, o extraerlas desde
"Información financiera filiales bancarias" de CMF o marcarlas `cobertura_eeff = 'pendiente'` y
reflejarlo en el chip del sidebar.

## 6. 🟠 La auditoría actual da falsa seguridad

`audit_factoring_leasing.py` valida unicidad, nulos, módulo 11, `total_pasivos == PC + PNC` (que es
verdad por construcción) y `provisiones ≤ bruta` (también por construcción, `tasa_prov < 1`).
Termina con *"AUDITORIA 100% EXITOSA … los más altos estándares"* sobre tablas sintéticas.

**Acción:** sustituir por `audit_factoring_leasing_v2.py` (adjunto), que además verifica
plausibilidad (dispersión de participaciones, ratios cartera/activos, saltos QoQ), consistencia
maestro↔balance, cobertura, procedencia y secretos en código, y **devuelve exit code ≠ 0** si falla.

## 7. 🟡 Cuadre tautológico

```python
if patrimonio == 0.0 and tot_act > 0:
    patrimonio = tot_act - tot_pas
```
Cuando CMF no trae `Patrimonio total`, el cuadre pasa por definición. Registrar `patrimonio_origen`
(`cmf|derivado`) y contar cuántas filas son derivadas. Lo mismo para el caso de SMB Factoring con
patrimonio negativo en 2023-12 / 2024-03 (−4.108 y −1.420 M$): puede ser real (quiebra) o un
`Patrimonio total` ausente; hoy no se puede distinguir.

## 8. 🟡 Tipo de cambio y TLS

- `rates_map.get(periodo, 900.0)` (stream) y `850.0` (pipeline): si falta el período, los `_m_usd`
  se calculan con un valor inventado sin aviso. Debe fallar o marcar `tc_fuente='fallback'`.
- Los 8 fallbacks 2018-2019 están hardcodeados; el resto depende de `macro_divisas_mercado.parquet`,
  creando una dependencia implícita entre sectores no documentada.
- `ssl_ctx.verify_mode = ssl.CERT_NONE` en los 3 scripts. Usar `certifi`; si CMF tiene cadena rota,
  fijar el bundle, no desactivar la verificación.

## 9. 🟡 Serie: huecos y anomalías sin documentar

- Penta Financiero: 34/49 trimestres, **15 huecos** intermedios y salto de activos +151 % en 2019-12
  (79.824 → 200.181 M$). Latam Trade: 3 huecos, +65 % 2022-03. Coval +71 % 2024-12. HLC −60 % 2025-06.
- Factoring Mercantil: 11 trimestres dispersos entre 2014-12 y 2025-12 (34 huecos).
- 44 filas con `pasivos_no_corrientes = 0` (Factoring Security 12 trimestres) → probablemente la
  cuenta viene con otro nombre en su taxonomía.

**Acción:** tabla `factoring_leasing_cobertura` (entidad × trimestre × estado: `ok | sin_archivo |
sin_cuenta_X`) generada por el pipeline, y una nota de anomalías conocidas en el README del sector.

## 10. 🟡 Homogeneidad con el resto del repo

- Balance: `total_activos_m_clp`; notas: `monto_mclp` / `cartera_bruta_mclp`. Elegir una convención
  global (propuesta: `_mm_clp` para millones, `_mm_usd`) y aplicarla en todos los sectores.
- `periodo` `YYYY-MM` aquí; FFMM/FI usan `YYYYMM`; CCAF usa `anio`+`mes`. Este sector es el que hay
  que mantener como estándar.
- `rut` `12345678-9` sin puntos: buena elección, mantener como estándar global.

## 11. 🟢 Textos de diccionario/manifest

`data_dictionary.js` (nota efectivo): "cuentas corrientes … en moneda nacional y extranjera (USD,
EUR, GBP)". No hay EUR/GBP. Ajustar todas las descripciones al contenido real una vez reconstruidas.

---

## Orden sugerido para el agente de arreglos

1. Rotar credencial (usuario) → variables de entorno + `.env.example` + scan de secretos.
2. Despublicar notas sintéticas (Parquet/JSON/manifest/sidebar/dictionary/ERD); marcar script como mock.
3. Un solo pipeline de balance (`stream_cmf_eeff_series.py`), catálogo versionado, README corregido.
4. Formato largo de cuentas CMF + redefinir `cartera_credito`; columnas de procedencia.
5. Corregir maestro (vigencia, filiales bancarias) y chips del sidebar.
6. Reemplazar auditoría por `audit_factoring_leasing_v2.py` y colgarla de CI.
7. Reconstruir notas reales (XBRL → PDF → manual), con reconciliación contra balance.

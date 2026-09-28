# Pseudocódigo del proyecto — Monitor Financiero Chile (MFC)

> Mapa de referencia interno. Resume **qué hace cada pieza y en qué orden**, no reemplaza al código.
> Generado a partir de una revisión completa del repo (commit `37f7cea`, 2026-09-28).
> **Revisado y actualizado** sobre `df3e26c` (2026-09-28, 2ª pasada): bancos B1/B2/R1 publicado 2022-01→2026-07, nuevo flujo mensual de Cooperativas CMF, `requirements.txt` global, nuevas sondas y `web_audit.yml`.
> Convención: `→` = produce / escribe, `⟵` = lee, `✗` = aborta (fail-closed).

---

## 0. Visión global

```
FUENTES OFICIALES (CMF, BCCh, SPensiones, SUSESO, SII)
      │   descarga en streaming (RAM / tmp que se borra en finally)
      ▼
SCRIPTS POR SECTOR  <sector>/scripts/*.py
      │   parsear → normalizar (RUT mód.11, períodos AAAA-MM, CLP/USD) → deduplicar
      ▼
STAGING (.local-data/, ignorado por Git)          ← solo en los flujos "maduros"
      │   auditoría: fail-closed si falta/regresa/no concilia
      ▼
PUBLICADO  docs/outputs/<sector>/*.parquet|*.json  + data_manifest.json
      │   (GitHub Pages sirve docs/)
      ▼
WEB ESTÁTICA docs/index.html
      DuckDB-Wasm crea VISTAS sobre los Parquet → sidebar / visor / diccionario / ERD / terminal SQL / export
```

Dos tipos de flujo (ver `pipelines/README.md`):

| Tipo | Dónde corre | Cómo publica |
|---|---|---|
| **Maduro/automático** (macro, bancos B1/B2/R1, factoring-leasing IFRS) | GitHub Actions + PC | staging → validación → artifact o commit controlado |
| **Manual/experimental** (PDFs, notas, seguros, FFMM, FI, AFP, CCAF…) | PC | escritura directa a `docs/outputs/` tras auditoría sectorial |
| **Laboratorio** (bancos REPO, XML/XBRL, sondas) | Actions | **nunca publica**; deja reportes en `.local-data/review/` o artifacts |

---

## 1. Utilidades que se repiten en casi todos los scripts

```
func dv_m11(rut_cuerpo):                     # calcular_dv / validate_rut_m11 / clean_rut
    suma = Σ dígito_i * serie(2,3,4,5,6,7,2,3…) de derecha a izquierda
    r = 11 - (suma mod 11)
    return "0" si r==11, "K" si r==10, str(r) en otro caso

func formatear_rut(raw) → "12.345.678-9"   ✗ si DV no calza

func parse_num(texto):                       # parse_num / clean_num / parse_num_clp
    quitar "$", espacios; "(123)" → -123
    "1.234.567,89" → 1234567.89   (formato chileno)
    "-" o vacío → None   (¡nunca 0 si está ausente!)

func get_usd_rates_map():                    # obtener_tc_map / get_usd_rates_map
    ⟵ docs/outputs/macro/macro_divisas_mercado.parquet
    return { "AAAA-MM": usd_clp_cierre }
    # Se usa para agregar columnas *_mm_usd a balances en CLP

func slugify / normalize_name → claves estables para IDs
func atomic_json(path, obj): escribir tmp → os.replace   (sin archivos a medio escribir)
```

> ⚠️ Esta lógica está **copiada** en ~15 archivos. Candidata #1 a un módulo común (`common/chile.py`).

---

## 2. Macro BCCh (`macro/`) — flujo automático piloto

```
daily_macro.run():                                   # Actions diario 10:00 UTC
    source = docs/outputs/macro
    si existe checkpoint .local-data/checkpoint/macro y es ≥ publicado:
        source = checkpoint
    run_macro_pipeline(output=STAGE, baseline=source)
    validate(STAGE, source)                          ✗ nunca guardar checkpoint no auditado
    published_changed = publish(STAGE, docs/outputs/macro, data_manifest.json)
    si STAGE ≠ source: copiar STAGE → checkpoint
    escribir GITHUB_OUTPUT (checkpoint_changed, published_changed)
    # Workflow: si published_changed → artifact "macro-validada" (revisión humana + PR). Sin commits automáticos.

run_macro_pipeline(output_dir, baseline_dir):
    ✗ si faltan BCCH_EMAIL / BCCH_PASSWORD
    baseline = load_baseline(dir)      # 3 tablas, mismos períodos, ordenados, sin futuro; si no hay → {} (backfill)
    starts   = query_starts(baseline)  # por serie: desde último mes (mensuales rezagadas: hasta 3 meses atrás)
    en paralelo (8 hilos): fetch_single_series(serie, start, hoy) vía bcchapi (23 series SIETE)
    ✗ si todas vacías (auth/API)   ✗ si backfill y alguna vacía
    para cada mes en rango:
        diarias → promedio y cierre del mes; mensuales → valor directo
    construir 3 tablas:
        macro_tasas_rendimientos   (TPM, TIB, BCP/BCU…)
        macro_divisas_mercado      (USD, EUR, TCR…, var% mensual/anual)
        macro_precios_actividad    (UF, IPC, IMACEC, cobre, EEE…)
    merge_incremental(fresh, baseline):  nuevo no-nulo prevalece (combine_first); ✗ si cambia el esquema
        recalcular var% solo donde cambió la fuente
    → output_dir/{tabla}.parquet + .json

publish_macro.validate(stage, published):
    run_audit(stage)
    por tabla: JSON == Parquet (filas, períodos, columnas, valores ±1e-8)
               ✗ período futuro
               ✗ mes nuevo sin dato central (usd_clp_cierre / uf_cierre)
               ✗ menos filas / menos cobertura / menos no-nulos que lo publicado  (anti-regresión)
    ✗ si las 3 tablas no tienen la misma cobertura
publish(): copiar solo si difiere + actualizar data_manifest.json
```

---

## 3. Bancos (`bancos/`)

### 3.1 Publicación incremental B1/B2/R1 (automático, `publish_cmf_bank_period.py`)
```
Workflow bancos_cmf_mensual.yml: días 1, 11 y 21 13:00 UTC → tests → publish --catch-up (incremental)
# Meses ya en manifest se saltan sin descargar. find_source lanza SourceNotPublished si la CMF aún no
# publica el mes pendiente: si han pasado ≤ DIAS_MAX_ESPERA (75) días desde el cierre → aviso y salida 0
# ("Nada nuevo"); si pasaron más → error (la CMF cambió el índice o el mes se perdió).

main(period?):
    period = select_period(pedido, manifest, hoy)
        # solo el PRIMER mes faltante tras SEED_PERIOD (2026-07); rechaza saltos/backfills manuales
    publish_period(period):
        ✗ período abierto/futuro
        si ya en manifest o existe carpeta → no-op
        zip_url  = find_source(índice ZIP CMF, period)     # scraping del índice del portal
        xlsx_url = find_source(índice XLSX CMF, period)
        descargar ambos (límites de tamaño) + sha256
        rows = extract_archive(zip)          # extract_cmf_bank_lines: 1 fila por cuenta, importe exacto como texto
        validate_release(rows, report, xlsx):
            ✗ ≠ 3 archivos (B1,B2,R1) por institución   ✗ familias vacías
            ✗ IDs vacíos/duplicados   ✗ período distinto   ✗ nombres inconsistentes por código
            por institución (excepto agregado 999):
                ✗ B1 TOTAL ACTIVOS ≠ XLSX   ✗ R1 sin cuenta clave (590000000/594000000) en XLSX
            ✗ < 17 instituciones individuales cotejadas
        escribir docs/outputs/bancos/cmf_b1_b2_r1/<period>/lineas.parquet (tmp → verificar round-trip → replace)
                 + validacion.json
        actualizar manifest.json de particiones + data_manifest.json (rollback si falla)
    → GITHUB_OUTPUT
# La web lee estas particiones vía `manifest` en SEMANTIC_VIEWS.
#
# Estado publicado: 55 particiones 2022-01 → 2026-07 (1.927.964 filas). SEED_PERIOD = 2026-07, así que
# next_unpublished_period() arranca desde ahí y avanza mes a mes (2026-08, …). El histórico 2022–2026-06
# se cargó con `--start` (umbral de cuentas de 9 dígitos de 2022).
# manifest.json de particiones: { periods:[{period,file,validation_file,records,sha256_zip,sha256_xlsx,zip_url,xlsx_url,…}],
#                                 files:[…lineas.parquet], total_records }   ← la web usa `files`
#
# update_data_manifest(period_manifest, latest):        (corregido 2026-09-28)
#     entrada bancos_cmf_lineas: corte = primer..último período; file_parquet = ÚLTIMO período del manifiesto
#     total_tables  = len(tables)                          # antes: +1 incremental → derivaba (65 vs 63)
#     total_records = Σ registros_reales de todas las tablas   # antes: += records del mes
```

### 3.1b Sondas bancarias nuevas (no publican)
```
probe_history_layout      : por mes 2022→hoy: ¿hay ZIP/XLSX?, miembros b1/b2/r1/c*, modelos de cuentas, hojas exigidas → ::notice
parse_mb1_fixed.parse_record(line, period): MB1 de longitud fija: cuenta 7/9 dígitos + total + 4 desgloses s9(14) con signo
                            unidad = MM CLP antes de 2022, pesos desde 2022   (no extrapolar a TXT B1 tabulado)
inspect_repo_source_layout: muestra encabezado + cuentas REPO (1160000/2160000/141000000/243000000) de 2 bancos por período
```

### 3.2 REPO bancario (laboratorio, NUNCA publica)
```
probe_repos_zip_cmf     : descubre ZIP por mes (índice + catálogo cmf_bancos_packages.json), inspecciona cuentas candidatas
                          pre-2022: 1160000/2160000 ; post-2022: 141000000/243000000
audit_repos_zip_cmf     : compara ZIP vs JSON legado probando divisores 1/1000/1e6 (sin asumir unidad)
rebuild_repo_from_cmf   : reextrae B1 → informe .local-data/review/bancos/reconstruccion_cmf
backfill_repo_audit     : barrido histórico por años
audit_repo_fx_sii       : coteja FX usado vs tablas diarias SII
transfer/hydrate_repo_review : empaqueta la revisión en anotaciones de Actions (chunks) y la reconstruye local
summarize_repo_audit, analyze_repo_snapshot, prepare_repo_corrections : resúmenes y propuestas (no publican)
audit_repo_release_gate : puerta de aprobación de la tabla legada bancos_repos_saldos_series
```
### 3.3 Legado bancos
```
pipeline_stream_bancos.py      : paquetes mensuales CMF → balance/resultados (MAESTRO_BANCOS hardcodeado) — tablas RETIRADAS de la web
pipeline_stream_derivados_bcch : BCCh F099 derivados OTC — RETIRADO de la web
02_extract_bancos_repos_series : LEGACY deshabilitado
```

---

## 4. Factoring & Leasing (`factoring_leasing/`)
```
Web actual: solo Lista de Entidades + muestras cotejadas (+ serie IFRS si backfill completo)

backfill_ifrs.run(batch):                        # Actions diario 12:20 UTC
    ⟵ catálogo 28 RUT (factoring_leasing_maestro.json)
    períodos = periods_from_index(estadisticas_ifrs.php)
    por período no cacheado (y batch restante):
        raw = fetch(ver_archivo.php?…)   si falla → annual_fallback (solo enlace anual anunciado)
        parse_period: 1 fila por cuenta/contexto, sin sumar ni redondear
        save_period → .local-data/factoring_leasing_serie/<period>.json (atomic)
publish_backfill.publish():
    ✗ si el índice no está completo localmente
    → docs/outputs/factoring_leasing/{balance,resultados}_serie_ifrs_cmf.parquet
    reescribe bloques entre marcadores "// BEGIN AUTO …" en duckdb_client.js, sidebar.js, data_viewer.js, data_dictionary.js
    update_root_manifest
    luego workflow corre scripts/audit_navigation.py + audit_web_full.py
audit_structured_sample : coteja archivo plano vs ficha HTML (2 entidades)
publish_structured_sample / publish_income_sample : publican SOLO filas aprobadas (run id + valores fijos)
    → sus Parquet ya NO se muestran en la web (2026-09-28): repetían cifras de la serie IFRS. Quedan como evidencia.
Resultados IFRS: "Ganancia (pérdida)" aparece 3 veces por estado (ERFG/ERNG ordinal 1 y 2 + ERI), mismo valor.
    utilidad del período = estado IN (ERFG, ERNG) AND repeticion_contexto = 1   → chip generado por profit_queries()
Legado: pipeline_stream_factoring_leasing (rutas C:\), stream_cmf_eeff_series, 02_extract_…_notas (PDF)
```

---

## 5. EEFF XML/XBRL CMF (`pipelines/xml_eeff/`, laboratorio)
```
extract.main(--sector --batch --shard):
    plan(sector) = entidades × periodos_para(sector)   # periodicidad real por industria
    por (entidad, período):
        html ficha → link_from_html → read_url
        raw = desempaquetar_xbrl (ZIP → instancia mayor) → sanear_xml → reencodear_xml
        parse_ifrs | parse_xbrl  (solo métricas inequívocas, sin homologar conceptos)
        url_fuente_segura (quita tokens auth/send)
    → .local-data (cuarentena), nunca docs/outputs
audit_sample           : XML vs tabla HTML CMF
publish_approved_sample: publica SOLO las 2 filas cotejadas (fi/ffmm _eeff_xml_muestra_cmf)
scripts/probe_xml_sources.py : sonda diaria de disponibilidad de fuentes XML por industria
```

---

## 6. Seguros (`seguros/circular_1835_cartera/`) — manual
```
download_seguros / orchestrate_activos(_batch) / orchestrate_seguros:
    por período × sector (vida=CSVID, generales=CSGEN):
        si control_descargas*.csv dice procesado y !forzar → saltar
        check_availability(url CMF) → descargar ZIP (RAM/BytesIO)
        process_cartera_activos.extract_all_assets_from_zip:
            por archivo de ancho fijo: parse_{acciones,fondos,extranjeros,bonos,bienes_raices,caratula}
        process_b7_derivatives.extract_contracts_from_zip:
            parse_{forward(3),swap(5),repo(6),opcion(2)}_row con "anclaje dinámico" de signos
        consolidate_*: merge incremental + dedup por DEDUP_KEYS → outputs/<sector>/*.parquet
        record_status en CSV de control
split_bonos_parquet: parte vida/cartera_bonos (148 MB) en 2016_2020 + 2021_2024 (<100 MB GitHub)
build_maestro_aseguradoras: maestro desde cartera_solvencia
reprocess_history: reproceso paralelo B.7
test_* / audit_full_history / check_health / final_report: calibración y auditoría (algunos con rutas C:\)
```

---

## 7. Fondos Mutuos (`ffmm/`) y Fondos de Inversión (`fi/`)
```
FFMM
  circular_1333_cartera/update_pipeline(months_back): descarga FUTU/OPCI mensuales si faltan → normalize → parquet
      (run_update.bat lo lanza en Windows)
  01  registro fondos activos (fm_ident2.php)          → ffmm_registro_fondos
  01b universo vigentes + históricos                   → ffmm_registro_fondos_universo
  02  resolver URLs EEFF (pestaña 62)                  → ffmm_eeff_urls_2024
  03  extraer carátula + tabla REPO 11 columnas (PDF)  → ffmm_caratula_eeff_2024 / repos_detalle_2024  (checkpoint JSON)
  03b histórico 2015–2025 (HTML + PDF en RAM)          → *_historico  (checkpoint atómico)
  04/04b auditoría (04b usa benchmark en ruta C:\)
  sync_checkpoint_to_parquet: vuelca checkpoint → parquet en caliente

FI
  cartera_inversiones/extract_cartera_fi.FIIExtractor: XML IFRS CMF N/E/M/… → fi_cartera_nacional/extranjera/derivados/...
  repos/scrape_repos_fi_cmf → normalize_repos_fi (RUT_MAP contrapartes, ISIN/nemo, fechas) → export (parquet+json+data_bundles.js)
  01 universo FI  → 02 REPO histórico (VRC/CRV)  → 03 EEFF desde PDF → 04 auditoría
```

---

## 8. Otros sectores (patrón común "stream + audit")
```
patrón:
  stream_*.main():
      universo = catálogo (hardcodeado o scrapeado de CMF)
      tareas = universo × períodos (trimestres)
      ThreadPool: fetch_*_task → HTML/PDF/XBRL CMF → parse_*_balance → filas
      enriquecer: rut formateado, usd = clp / tc_map[periodo]
      → docs/outputs/<sector>/*_balance_resumen.parquet + .json (+ maestro)
  audit_*.run_audit(): DV mód.11, PK únicas, nulos, activos = pasivos + patrimonio, cobertura temporal

agf/                stream_cmf_agf (manual, sin Actions): lista AGF + EEFF IFRS trimestrales → agf/fuentes/agf_eeff_cmf.parquet
                    publicar_agf_balance_resultados: valida (A = P + Pat, sin duplicados, RUT en maestro) y separa
                      → agf_balance (activos, pasivos, patrimonio, efectivo…) + agf_resultados (ingresos acum. y del trimestre;
                        gastos y ganancia NULL hasta la próxima corrida: antes no se capturaban por las tildes)
                    audit_agf
corredoras_bolsa/   01 universo → 02 EEFF + REPO → 03 audit ; stream_cmf_corredoras_series (50 trimestres 2014-03..2026-06)
securitizadoras/    stream_cmf_securitizadoras (gestoras + lista de patrimonios separados)
                    05_publicar_balance_patrimonios:
                      leer fuentes/balances_patrimonios_separados.xlsx (hoja Balance_por_cuenta)
                      descartar filas vacías y años < 2014 (2013 no está; 2010–2013 sin datos)
                      exigir: DV mód.11, periodo AAAA12, un documento por patrimonio y cierre,
                              activos = PC + PNC + patrimonio (±2 M$) y detalle = subtotal en todos
                      → patrimonios_separados_balance.parquet (7.962 cuentas, 358 balances)
                    audit_securitizadoras (gestoras, lista y balance de patrimonios separados)
cooperativas/       01 maestro → 03 audit (solo lista de entidades)
                    (balances CMF en Excel retirados, ver §8b)
ccaf/               build_ccaf_maestro ; pipeline_extract_ccaf_xbrl (XBRL CMF → solo ccaf_caratula_totales) ; audit
retail_financiero/  stream_cmf_retail_financiero + audit
sistemas_pago/      stream_sistemas_pago (solo maestro) + audit
fintech/            stream_fintech_rpsf (registro RPSF Ley 21.521, solo maestro) + audit ; explore.py (roto, ver §11)
pensiones/          pipeline_stream_history(_parallel): Playwright descarga ZIP SP → parse → particiones → consolidate
                    generate_afp_maestro (única tabla AFP publicada); cartera/derivados AFP RETIRADOS de la web
                    ~25 scripts inspect_*/test_*/sample_* = exploración ad-hoc (rutas C:\)
pipelines/manual/   ingest_manual_notes: plantillas CSV de notas transcritas → valida RUT → parquet
```

---

## 8b. Cooperativas, CCAF, Sistemas de Pago y FinTech — recorte 2026-09-28
```
Criterio: balances/resultados solo si salen de XML o XBRL oficial; si no, solo la lista de entidades.
cooperativas : balances venían de planillas Excel CMF (Reporte Financiero y 02_extract) → RETIRADOS.
               Se borraron extract_cmf_coop_report, 02_extract, 04 nota efectivo, probe_coop_layout,
               sus tests y los workflows cooperativas_cmf_mensual.yml y coop_probe.yml. Queda cooperativas_maestro.
ccaf         : ccaf_caratula_totales sale del XBRL CMF (safec_ifrs_verarchivo → .xbrl) → SE QUEDA (72 balances,
               2019-12..2026-06). Nota 8 (efectivo, DAP, repos) y colocaciones de crédito social → RETIRADAS.
               Se borraron build_ccaf_repos_enriquecido y ccaf/scripts/legacy.
sistemas_pago: solo sistemas_pago_maestro (balances y estadísticas BCCh retirados).
fintech      : solo fintech_rpsf_maestro (servicios acreditados y roles de finanzas abiertas retirados).
Los extractores que quedan ya no escriben las tablas retiradas; las auditorías sectoriales solo revisan lo publicado.
```

### Otras sondas nuevas
```
retail_financiero/probe_ifrs_rut_cross.py PERIODO: TXT IFRS CMF → RUT únicos × maestro retail (EN_MAESTRO / CANDIDATO) → CSV + ::warning
```

---

## 9. Web estática (`docs/`)

```
index.html carga en orden:
  data_bundles.js   window.DATA_BUNDLES = {fi_repos, afp_maestro, bancos_maestro, …}  (JSON embebido, fallback liviano)
  chart_renderer.js, erd_graph.js, duckdb_client.js, chat_terminal.js, sidebar.js,
  theme_switcher.js, data_dictionary.js, data_viewer.js, jszip, xlsx, export_modal.js
  script inline: instancia ERD, wiring de pestañas

DuckDBClient (singleton window.DuckDBClient):
  init():
      import duckdb-wasm desde jsDelivr (v1.28.0) → worker → db → conn
      registerSemanticViews()
      badge de motor (OK / parcial / caído)
  registerSemanticViews():
      para view en SEMANTIC_VIEWS:        # {name, file | [files] | manifest, where?}
          files = view.manifest ? fetch(manifest).files : view.file
          ✗ rutas absolutas o con ".."
          registerFileURL(cada file, HTTP)
          CREATE OR REPLACE VIEW name AS SELECT * FROM read_parquet(files) [WHERE …]
          si falla → unavailableViews (no se inventan datos)
  query(sql) → {success, rows (BigInt→Number), columns, elapsedMs} | {success:false, error}

SidebarController (EXPLORER_TREE: grupo → sector → carpeta/circular → tablas + chips SQL):
  render árbol, búsqueda, resizer
  onCircularSelect → breadcrumb, ERD.focusSector, ChatTerminal.setCustomChips, abrir 1ª tabla
  onTableSelect    → ERD.focusTable, DataViewer.load(view), terminal "SELECT * … LIMIT"

DataViewerController (DATA_VIEWER_CATALOG): query view LIMIT n → tabla con filtro, orden, copiar celda, export
DataDictionaryController: diccionario por sector (rol PK/FK/Dim/Métrica, criterio contable) con filtro y búsqueda
ERDGraph (canvas): nodos por tabla + enlaces FK; zoom/pan; click → modal esquema / abrir tabla
ChatTerminalController: input SQL, historial ↑↓, favoritos en localStorage, compartir por #hash, render + ChartRenderer
ExportModalController: alcance (pantalla / todo / años) × formato (CSV, XLSX, JSON, Parquet directo); ZIP si >150k filas; XLSX parte en 1.048.576
theme_switcher: 6 paletas vía CSS vars; persistencia localStorage; re-render ERD

Contrato de coherencia (lo verifica scripts/audit_navigation.py y audit_web_full.py):
  cada tabla del sidebar ↔ vista en SEMANTIC_VIEWS ↔ opción del visor ↔ entrada en diccionario ↔ nodo ERD ↔ archivo existente
  cada sector abre con "Lista de Entidades" = tabla *_maestro (salvo macro)
  tablas retiradas (afp_cartera_*, bancos_balance_resumen, derivados…) no deben aparecer en ningún JS
```

Cómo levantarla en local:
```
python -m scripts.preview_no_cache --port 8000      # sirve docs/ en 0.0.0.0:8000, sin caché
    soporta HTTP Range (206 Partial Content) igual que GitHub Pages → DuckDB-Wasm lee solo pie + row groups
    (antes devolvía 200 con el archivo completo: 71 MB para leer 100 bytes)
requisitos del navegador: acceso a cdn.jsdelivr.net (DuckDB-Wasm 1.28.0) y fonts.googleapis.com
```

Otros scripts transversales (`scripts/`): `preview_no_cache.py` (servidor local), `standardize_schema_keys.py` (PK/FK/IDs), `verify_joins.py`, `orchestrate_overnight_market_pipeline.py` (FFMM+FI nocturno).

---

## 10. CI (`.github/workflows/`)

| Workflow | Cron (UTC) | Publica | Qué hace |
|---|---|---|---|
| macro.yml | diario 10:00 | artifact (PR humano) | daily_macro con cache checkpoint |
| bancos_cmf_mensual.yml | días 1, 11, 21 13:00 | **sí** (commit + Pages) | tests + publish_cmf_bank_period --catch-up (incremental) |
| web_audit.yml | push a docs/** | no | audit_navigation + audit_web_full (anotaciones) |
| bancos_probe_historia.yml / retail_probe_ifrs.yml | manual | no | sondas de formato |
| bancos_repo.yml | días 4, 14, 24 11:00 | no | laboratorio REPO |
| bancos_repo_historico.yml / bancos_muestra_inspeccion.yml | manual | no | barridos / inspección |
| factoring_leasing_backfill.yml | días 3, 13, 23 12:20 | **sí** | backfill_ifrs + publish_backfill + auditorías web |
| factoring_leasing_sample.yml | manual | no | cotejo muestra |
| xml_eeff_review.yml | días 5, 15, 25 11:30 | no | extract.py en 4 shards |
| xml_eeff_sample.yml | manual | no | audit_sample |
| probe_xml_sources.yml | diario 12:00 | no | sonda fuentes |

---

## 11. Hallazgos de la revisión (estado al 2026-09-28)

**2ª pasada (sobre `df3e26c`)**
- Tests: `bancos` 81 OK · `factoring_leasing` 42 OK (tras corregir el manifiesto) · `xml_eeff` 44 OK · `macro` requiere `bcchapi`.
- `audit_navigation.py`: 12 familias, 86 tablas, 86 opciones del visor ✅ · `audit_web_full.py`: 100% (831 columnas del diccionario, 74 nodos / 69 enlaces ERD) ✅.
- ✅ `data_manifest.json` decía `total_tables: 65` con 63 entradas (fallaba `test_publication`). Causa: `update_data_manifest` sumaba incrementos. Ahora recalcula desde la lista; `file_parquet` de bancos apunta al último período (2026-07, antes 2026-06).
- ✅ `preview_no_cache.py` sin soporte HTTP Range → agregado.
- ✅ (2026-09-28) Se quitaron de `data_manifest.json` las 4 tablas AFP retiradas cuyos Parquet ya no existían.
- ⚠️ `web_audit.yml` se dispara en push a `arena/01a0e66e-…` (rama de una sesión anterior); conviene dejar solo `main` + `pull_request`.
- Muchas vistas del visor no tienen entrada en `data_manifest.json` (vida_fondos, fi_*, bancos_cmf_balance/resultados agrupadas como `bancos_cmf_lineas`…): el manifiesto es un catálogo parcial, no la fuente de verdad de la web (esa es `SEMANTIC_VIEWS`).

**1ª pasada**

**Tests** (tras las correcciones del 2026-09-28)
- `bancos/tests` 68 OK · `factoring_leasing/tests` 42 OK · `pipelines/xml_eeff/tests` 44 OK · `macro/tests` 9 OK (requiere `bcchapi`).
- ✅ Se agregó `__init__.py` a las carpetas `tests/`: `unittest discover -s <dir> -t .` ya funciona.
- ✅ `scripts/audit_navigation.py` actualizado a la estructura real de Bancos (maestro + CMF B1/B2 + R1; REPO legado retirado).
- ✅ `scripts/audit_web_full.py` ahora entiende vistas por `manifest` (particiones) y avisa sin fallar si aún no hay períodos.
- ℹ️ `docs/outputs/bancos/cmf_b1_b2_r1/manifest.json` sigue vacío (no hay Parquet bancario en ningún lado; se llena ejecutando `python -m bancos.scripts.publish_cmf_bank_period` con internet, o el workflow manualmente): las vistas `bancos_cmf_balance/resultados` aparecen "no disponibles" hasta la primera corrida mensual exitosa de `bancos_cmf_mensual.yml`.

**Deuda técnica / riesgos**
1. ✅ **Rutas `C:\Users\joaqu\…` eliminadas** (32 scripts): la raíz vieja `bcch_market_monitor` → `_ROOT` relativo al repo; `Desktop\Respaldo_BCCH` → `_RESPALDO` (variable `MFC_RESPALDO_DIR`, por defecto `~/Desktop/Respaldo_BCCH`); otros archivos del Escritorio → `Path.home()/'Desktop'/…`.
2. ✅ `docs/ffmm/` y `docs/fi/` eliminados (624 archivos idénticos); sidebar y ERD leen ahora `outputs/ffmm|fi/…`. Pendiente: `docs/outputs/b7_*.parquet` (versión antigua distinta de `vida/b7_*`, solo usada por `feedback_review/`). Ojo: los pipelines FFMM/FI escriben en `ffmm/…/outputs` y `fi/…/outputs`; hay que copiar a `docs/outputs/` al publicar.
3. Utilidades (DV, parse_num, tc_map) repetidas en ~15 archivos.
4. ✅ `fintech/scripts/explore.py` corregido (compilaba solo en Python ≥ 3.12).
5. ✅ BOM UTF-8 eliminado de 9 scripts.
6. Credenciales: README pide rotar la contraseña BCCh expuesta en el historial Git — sigue pendiente de confirmar. (`ccaf/scripts/legacy` se eliminó.)
7. `.git` pesa ~237 MB; binarios en Git (`scratch/sample_202406_vida.zip`, Parquet grandes). Considerar Git LFS o releases.
8. ✅ Ya existe `requirements.txt` global (Python 3.11, pyarrow/openpyxl/xlrd fijados igual que en Actions).
9. Muchos scripts exploratorios (`pensiones/inspect_*`, `test_*` que no son tests) mezclados con pipelines productivos.

**Siguientes pasos sugeridos (por prioridad)**
1. ✅ ~~Arreglar auditorías web~~ (hecho).
2. ✅ ~~Duplicados docs/ffmm, docs/fi~~ y ✅ ~~rutas C:\~~.
3. Crear `common/` con utilidades chilenas (DV, parse_num, tc_map).
4. Mover exploratorios a `*/scratch/` o `archive/`; (`__init__.py` en `tests/` ✅).
5. ✅ ~~`requirements.txt` global~~ (hecho).

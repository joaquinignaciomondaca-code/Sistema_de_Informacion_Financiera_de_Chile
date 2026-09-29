# Pseudocódigo del proyecto — Sistema de Información Financiera de Chile (SIF)

> Mapa de referencia interno. Resume **qué hace cada pieza y en qué orden**, no reemplaza al código.
> Generado a partir de una revisión completa del repo (commit `37f7cea`, 2026-09-28).
> **Revisado y actualizado** sobre `df3e26c` (2026-09-28, 2ª pasada): bancos B1/B2/R1 publicado 2022-01→2026-07, nuevo flujo mensual de Cooperativas CMF, `requirements.txt` global, nuevas sondas y `web_audit.yml`.
> **Revisado y actualizado** (2026-09-28, 3ª pasada): proyecto renombrado a **SIF**, la descarga pasó a ser la
> 7ª pestaña (sin panel inferior) y el **vocabulario de tablas** quedó en `docs/vocabulario.json`, aplicado por
> `scripts/normalizar_vocabulario.py`. Detalle en `docs/notas/rediseno_ui_2026-09-28.md` (§7 y §8).
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
      DuckDB-Wasm crea VISTAS sobre los Parquet → siete pestañas (Información · Mapa · Diccionario ·
      Visor · Consultas SQL · Descargas · Normativa CMF)
```

**Nombres.** Los Parquet publicados y `data_manifest.json` conservan sus ids históricos
(`bancos_maestro`, `ccaf_maestro`, …) porque renombrarlos rompería los pipelines y los enlaces ya
publicados. La web los muestra con el vocabulario canónico (`bancos.lista_entidades`,
`ccaf.lista_entidades`, …) que manda `docs/vocabulario.json` (§9), y en SQL los nombres viejos
siguen vivos sólo como vistas de alias. En las secciones 2–8 de este mapa aparecen los **nombres
reales de scripts y archivos** (`build_ccaf_maestro.py`, `ccaf_maestro.parquet`): son los del
repositorio, no los que ve el usuario en pantalla.

Dos tipos de flujo (ver `pipelines/README.md`):

| Tipo | Dónde corre | Cómo publica |
|---|---|---|
| **Maduro/automático** (macro, bancos B1/B2/R1, factoring-leasing IFRS) | GitHub Actions + PC | staging → validación → artifact o commit controlado |
| **Manual/experimental** (PDFs, notas, FFMM, FI, AFP, CCAF…) | PC | escritura directa a `docs/outputs/` tras auditoría sectorial |
| ~~Laboratorio~~ (bancos REPO, XML/XBRL, sondas) | — | **eliminado el 2026-09-28** (no publicaban; quedan en el historial de Git) |

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
    # Workflow: commit de lo validado (reintento con cherry-pick) y, en main, redespliegue del sitio.

series_bcch.main():                                  # mismo workflow, después de daily_macro
    CATALOGO = 51 series (clave, código SIETE, grupo, unidad; frecuencia = sufijo D/M/T)
    previo = docs/outputs/macro/series/*.parquet
    por serie (6 hilos): desde = última fecha − ventana (D 10 días · M 6 meses · T 13 meses), o 2014-01-01
        GetSeries (API REST SIETE) → [(fecha, valor)]; descarta NaN y fechas futuras
        error o código inexistente → estado en el catálogo + aviso, sigue con las demás
        combinar: la fecha nueva reemplaza a la misma fecha; ninguna observación previa se borra
    ✗ si fallan todas (credenciales/API)   ✗ si alguna serie queda con menos observaciones
    → series/<AAAA>.parquet (solo años que cambian) + series/manifest.json
    → macro_series_catalogo.parquet (nombre, frecuencia, unidad, título BCCh, cobertura, estado)
    → data_manifest: macro_series, macro_series_catalogo (+ corte de las 3 tablas mensuales)

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

### 3.1b Sondas, laboratorio REPO y legado bancos
```
Eliminados el 2026-09-28 (no publicaban): probe_history_layout, parse_mb1_fixed, laboratorio REPO completo
(probe/audit/rebuild/backfill/fx_sii/transfer/hydrate/summarize/analyze/prepare/release_gate), pipeline_stream_bancos,
pipeline_stream_derivados_bcch + catálogo derivados_otc, 02_extract_bancos_repos_series, audit_bancos_data/repos,
y los workflows bancos_repo, bancos_repo_historico, bancos_probe_historia, bancos_muestra_inspeccion.
Queda: publish_cmf_bank_period + extract_cmf_bank_lines + inspect_cmf_bank_sample (+ tests).
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
audit_structured_sample : coteja archivo plano vs ficha HTML (2 entidades; su workflow manual factoring_leasing_sample se eliminó el 2026-09-28)
publish_structured_sample / publish_income_sample : publican SOLO filas aprobadas (run id + valores fijos)
    → sus Parquet ya NO se muestran en la web (2026-09-28): repetían cifras de la serie IFRS. Quedan como evidencia.
Resultados IFRS: "Ganancia (pérdida)" aparece 3 veces por estado (ERFG/ERNG ordinal 1 y 2 + ERI), mismo valor.
    utilidad del período = estado IN (ERFG, ERNG) AND repeticion_contexto = 1   → chip generado por profit_queries()
Legado (pipeline_stream_factoring_leasing, stream_cmf_eeff_series, 02_extract_…_notas PDF): eliminado 2026-09-28
```

---

## 5. EEFF XML/XBRL CMF (laboratorio eliminado)
```
pipelines/xml_eeff/ (extract en cuarentena + audit_sample) y sus workflows xml_eeff_review / xml_eeff_sample:
eliminados el 2026-09-28. Nunca publicaron: desde Actions la descarga XBRL de la CMF devuelve HTML.
(scripts/probe_xml_sources.py y su workflow diario: eliminados antes; las fuentes que vigilaban se
 automatizaron por otras vías: TXT IFRS CMF, carteras FFMM/FI y Excel FECU de corredoras)
```

---

## 6. Seguros (`seguros/scripts/`) — automático, 3 veces al mes (días 7, 17, 27)
```
formato_1835.py: posiciones oficiales de cada archivo (I renta fija, A acciones, F fondos mutuos,
    B bienes raíces, X extranjero, P derivados y pactos, C control) en los dos formatos:
    v2016 (hasta 2024-11) y v2024 (desde 2024-12, Circular 2354). Verificadas contra líneas reales
    (seguros/fuentes/muestras_1835) y la ficha técnica (seguros/fuentes/fichas_tecnicas_1835).
actualizar_carteras.py (workflow seguros_carteras.yml):
    meses pendientes = meses desde DESDE_TABLA (2016-11; renta_fija y bienes_raices 2024-12)
                       cuyas tablas no están en docs/outputs/seguros/manifest.json
    diagnóstico: lee todos los pendientes sin escribir y anota los que tienen problemas
    por mes, en orden:
        descargar ZIP de vida (CSVID) y generales (CSGEN); si no está publicado → terminar sin cambios
        por archivo: decodificar (UTF-8 o Latin-1 según el largo), largo exacto de cada línea,
                     encabezado (o RUT/mes desde el nombre si falta), totales y mes → avisos
                     campos numéricos y fechas: ilegibles > 1 % de las filas de una tabla → no publicar (fail-closed)
                     archivo defectuoso de una compañía (línea de otro largo, tipo de registro inválido) →
                       se excluye SOLO ese archivo (aviso + manifest "archivos_excluidos"); si son > 2 y > 5 %
                       de los archivos del sector → no publicar el mes (lectura mal hecha)
        escribir: renta_fija y bienes_raices un archivo por mes; resto un archivo por año
                  (esquema fijo por tabla); manifiesto por tabla, aseguradoras.parquet, data_manifest.json
tests/test_formato_1835.py: lee las muestras de ambos formatos; cuadratura de bonos y fechas válidas
```

---

## 7. Fondos Mutuos (`ffmm/`) y Fondos de Inversión (`fi/`)
```
FFMM  scripts/actualizar_carteras.py  (workflow ffmm_carteras.yml: días 8, 18 y 28; incremental)
  para cada mes pendiente según docs/outputs/ffmm/manifest.json (desde 2001-01; nacional desde 2022-01):
      POST ffm_download.php aa, mm, cartera ∈ {NACI, EXTR, FUTU, OPCI}   (OPLA viene siempre vacía)
      leer CSV ";": encabezado idéntico al de la Circular 1333 (FFM_60xxxxx) o error
          números con punto decimal (".019"), fechas DD/MM/AAAA, sin rellenar con ceros
          > 1 % de filas ilegibles → el mes no se publica (error)
      completitud: NACI con datos y ≥ 90 % de los fondos del mes anterior; si no → esperar
          (en meses antiguos esto es error, no espera)
      escribir: cartera_nacional un archivo por mes, resto uno por año; montos en miles de la
                moneda funcional del fondo (_miles_mf)
      lista de fondos (maestro_fondos_mutuos.parquet): primer/último mes informado, reporta_ultimo_mes
      manifiestos por tabla + data_manifest.json (entradas del sector, recalculadas tras el pull)
  01  registro fondos activos (fm_ident2.php)          → ffmm_registro_fondos
  01b universo vigentes + históricos                   → ffmm_registro_fondos_universo

FI    scripts/actualizar_carteras.py  (workflow fi_carteras.yml: días 9, 19 y 29; incremental, --minutos 270)
  registro CMF (consulta.php FINRE + FIRES, vigentes y no vigentes) en cada corrida
  para cada trimestre pendiente según docs/outputs/fi/manifest.json (desde 2020-03; espera 75 días,
  100 en diciembre):
      por fondo: ifrs_cartera_{nac,ext,met_part,bie_rai,fut_fw,op}.php + ifrs_informe_vrc_crv.php
          (12 hilos; trimestres recientes: vigentes + los que reportaron el anterior)
      encabezado exacto o error; números 1.234.567,89 y fechas DD/MM/AAAA; nada se rellena con ceros
      suma de cada columna de montos = fila TOTAL de la CMF (descuadre en > 2 % de los fondos → no publica)
      > 1 % de filas ilegibles o páginas inesperadas → no publica
      completitud: fondos con cartera ≥ 90 % del trimestre anterior; si no → esperar
      escribir: cartera_nacional un archivo por trimestre, resto uno por año (_miles_mf = miles de la
                moneda funcional, leída del informe de pactos)
      maestro_fondos_inversion.parquet (registro + moneda + primer/último trimestre con cartera)
      fi_registro_fondos_universo.json
      confirmación: commit de datos, cherry-pick sobre la rama al día + --solo-data-manifest
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

agf/                balance y resultados: ver §8a (automático). audit/lista: agf_maestro
corredoras_bolsa/   01 universo (lista) ; balance y resultados: ver §8a (automático)
securitizadoras/    balance y resultados de las gestoras: ver §8a (automático)
                    05_publicar_balance_patrimonios:
                      leer fuentes/balances_patrimonios_separados.xlsx (hoja Balance_por_cuenta)
                      descartar filas vacías y años < 2014 (2013 no está; 2010–2013 sin datos)
                      exigir: DV mód.11, periodo AAAA12, un documento por patrimonio y cierre,
                              activos = PC + PNC + patrimonio (±2 M$) y detalle = subtotal en todos
                      → patrimonios_separados_balance.parquet (7.962 cuentas, 358 balances)
                    audit_securitizadoras (gestoras, lista y balance de patrimonios separados)
cooperativas/       01 maestro → 03 audit (solo lista de entidades)
                    (balances CMF en Excel retirados, ver §8b)
ccaf/               build_ccaf_maestro (lista) ; balance y resultados: ver §8a (automático)
sistemas_pago/      stream_sistemas_pago (solo maestro) + audit
fintech/            stream_fintech_rpsf (registro RPSF Ley 21.521, solo maestro) + audit ; explore.py (roto, ver §11)
pensiones/          pipeline_stream_history(_parallel): Playwright descarga ZIP SP → parse → particiones → consolidate
                    generate_afp_maestro (única tabla AFP publicada); cartera/derivados AFP RETIRADOS de la web
                    ~25 scripts inspect_*/test_*/sample_* = exploración ad-hoc (rutas C:\)
pipelines/manual/   ingest_manual_notes: plantillas CSV de notas transcritas → valida RUT → parquet
```

---

## 8a. Estados IFRS de AGF, securitizadoras, CCAF y corredoras — automático, 3 veces al mes
```
pipelines/ifrs_sectores/actualizar.py   (ifrs_sectores.yml, días 2, 12, 22)
  índice estadisticas_ifrs.php → trimestres (2009-03..último); ver_archivo.php?inicio=P&termino=P = TXT con
    TODAS las sociedades que envían EEFF XBRL: periodo;rut;nombre;I|C;moneda;cuenta;valor;taxonomía;estado
  si el trimestre falla → mismo trimestre desde el archivo anual del índice
  por línea: sector = RUT en la lista de entidades (agf, securitizadoras, ccaf) o nombre que calza
             (ADMINISTRADORA GENERAL DE FONDOS | SECURITIZADORA | CAJA DE COMPENSACI) → en_lista_entidades=false
  ESF* → <prefijo>_balance ; ER* → <prefijo>_resultados ; flujos (EFM*) no se publican
  valor = entero literal en pesos (o USD); no entero → nulo + valor_no_numerico; repeticion = n-ésima vez de la cuenta
  incremental: docs/outputs/ifrs_sectores/manifest.json. Trimestre > 150 días desde el cierre = cerrado, no se
    vuelve a pedir; los recientes se releen (presentaciones tardías) y nunca pierden entidades ya publicadas
  → docs/outputs/{agf,securitizadoras,cajas_compensacion}/<prefijo>_{balance,resultados}/<AAAA>.parquet + manifest
  entidades del sector que reportan y no están en la lista → ::notice + manifest (entidades_fuera_de_lista_…)
  último trimestre: CCAF y sociedades FACTORING|LEASING (no bancos) fuera de su lista → alta en ccaf_maestro /
    factoring_leasing_maestro (máx. 10 por corrida; si calzan más, el patrón es sospechoso y no se agrega nada)

corredoras_bolsa/scripts/actualizar_eeff.py   (corredoras_eeff.yml, días 6, 16, 26)
  intermediarios_ifrs1.php?xls=y&tiposociedad={1 corredores, 2 agentes}&mes1=MM&anno1=AAAA → Excel trimestral
    (desde 2010-12): fila por sociedad, columna por cuenta FECU «11.01.00Nombre» (sin espacios, UTF-8 mal leído)
  nombres legibles y nivel: versión HTML del mismo informe (xls=n), una vez por corrida
  1x-2x → corredoras_bolsa_balance ; 30 → resultados ; 31-32 → otros resultados integrales ; 5x (flujo) no
  30.00.00 se repite en el Excel → solo la primera aparición ; miles de pesos
  mismo esquema incremental (manifest.json del sector, cerrado a 150 días)
  controles: DV mód.11, fecha de cada fila = trimestre pedido, valores enteros; activos = pasivos + patrimonio
    cuadra en 2.860 de 2.861 balances (el TXT IFRS: 2.934/2.935 AGF, 223/223 CCAF, 645/645 securitizadoras)
```

## 8c. Listas de entidades y guardián de automatización
```
pipelines/entidades/actualizar_listas.py   (entidades.yml, días 10, 20, 28)
  por sector: registros CMF consulta.php?mercado=M&Estado={VI,NV}&entidad=CÓDIGO (uno o varios)
    RUT vigente fuera de la lista → alta (solo registros marcados «altas»; BCSAG y DCVAL solo vigencia)
    RUT de la lista en NV y no en VI → no vigente ; vuelve a VI → vigente ; nunca baja por ausencia
    bancos: solo Activo → No vigente (fusionados comparten RUT con el banco que los absorbió)
    resguardo: VI con menos de la mitad de los vigentes ya listados → no se toca ese sector
  patrimonios separados: listado_titulos_deuda.php (todas las inscripciones por registro automático)
    → emisor securitizadora (RUT en la lista o nombre) con número nuevo → alta (colateral vacío)
  AFP: vcfAFP.php (valor cuota por AFP) → nombre nuevo → alta con RUT de RVEMI
  → novedades.json + conteos del menú y del diccionario + registros_reales de data_manifest

scripts/audit_automatizacion.py   (web_audit.yml: en cada push; --frescura cada lunes)
  inventario pipelines/auto/inventario.json: cada tabla de data_manifest y cada vista SEMANTIC_VIEWS
    → {workflow} o {manual: motivo}
  los ids de publicación (data_manifest) se traducen al vocabulario por los alias de vocabulario.json
  antes de cruzar manifiesto ↔ inventario ↔ vistas del sitio (así «bancos_cmf_balance» y
  «bancos_balance» son la misma tabla)
  push: workflow existe + cron + ejecuta su script + el script nombra el archivo (o «marca») + modo coherente
  lunes: última corrida exitosa en la rama por defecto ≤ max_dias (16; macro 3) → si no, issue
```

## 8b. Cooperativas, CCAF, Sistemas de Pago y FinTech — recorte 2026-09-28
```
Criterio: balances/resultados solo si salen de XML o XBRL oficial; si no, solo la lista de entidades.
cooperativas : balances venían de planillas Excel CMF (Reporte Financiero y 02_extract) → RETIRADOS.
               Se borraron extract_cmf_coop_report, 02_extract, 04 nota efectivo, probe_coop_layout,
               sus tests y los workflows cooperativas_cmf_mensual.yml y coop_probe.yml. Queda
               cooperativas.lista_entidades (archivo cooperativas_maestro.parquet).
ccaf         : balance y resultados salen del TXT IFRS CMF, que es la exportación de los estados XBRL enviados
               por las cajas (ver §8a); reemplazan a ccaf_caratula_totales (XBRL bajado a mano, retirado).
               Nota 8 (efectivo, DAP, repos) y colocaciones de crédito social → RETIRADAS.
sistemas_pago: solo sistemas_pago.lista_entidades (archivo sistemas_pago_maestro.parquet; balances y
               estadísticas BCCh retirados).
fintech      : solo fintech.lista_entidades (archivo fintech_rpsf_maestro.parquet; servicios acreditados
               y roles de finanzas abiertas retirados).
Los extractores que quedan ya no escriben las tablas retiradas; las auditorías sectoriales solo revisan lo publicado.
```

---

## 9. Web estática (`docs/`)

```
docs/vocabulario.json — ÚNICA fuente de nombres de la web
  52 tablas: {id, alias[], nombre, tipo, sector, descripcion, cobertura} · 15 sectores · 22 tipos
  regla: una tabla se llama <sector>.<tipo>; TODA lista de entidades se llama lista_entidades
         (única variante: lista_entidades_registro, para el registro único de corredoras)
  nombres_retirados: lista_administradoras, lista_instituciones, lista_emisiones, registro_unico, …
  scripts/normalizar_vocabulario.py  sin argumentos: aplica el vocabulario a los archivos vivos
      (ids *_maestro → *_lista_entidades, nombres visibles, etiquetas de sector, filas «rows/registros»,
       ids de nodo del árbol, encabezados del diccionario, bloques de alias SQL, README.md)
      --check: falla si un archivo se salió del vocabulario (lo corre scripts/audit_interfaz.py)

index.html carga en orden:
  data_bundles.js   window.DATA_BUNDLES = {afp_lista_entidades, bancos_lista_entidades}  (fallback liviano)
  theme_switcher.js, ux_shell.js, chart_renderer.js, erd_graph.js, duckdb_client.js, sidebar.js,
  data_dictionary.js, data_viewer.js, chat_terminal.js, download_utils.js, download_catalog.js,
  downloads_panel.js, jszip, xlsx
  script inline: instancia ERD, wiring de pestañas y atajos
  los 15 archivos locales comparten una sola etiqueta de versión (?v=20260928-vocabulario-1)
Siete pestañas, cada una a pantalla completa (ya no existe el panel inferior ni el divisor):
  Información · Mapa relacional · Diccionario · Visor de datos · Consultas SQL · Descargas · Normativa CMF

DuckDBClient (singleton window.DuckDBClient):
  init():
      import duckdb-wasm: copia local docs/vendor/duckdb/ → jsDelivr → unpkg (mvp de respaldo)
      registerSemanticViews()
      badge de motor (OK / parcial / caído) con el motivo del primer intento
  registerSemanticViews():
      para view en SEMANTIC_VIEWS:        # {name, file | [files] | manifest, where?}
          files = view.manifest ? fetch(manifest).files : view.file
          ✗ rutas absolutas o con ".."
          registerFileURL(cada file, HTTP)
          CREATE OR REPLACE VIEW name AS SELECT * FROM read_parquet(files) [WHERE …]
          + CREATE OR REPLACE VIEW alias AS SELECT * FROM name
            (LEGACY_VIEW_ALIASES con los nombres anteriores: compatibilidad SQL, nunca en la interfaz)
          si falla → unavailableViews (no se inventan datos)
  query(sql) → {success, rows (BigInt→Number), columns, elapsedMs} | {success:false, error}

SidebarController (EXPLORER_TREE: grupo → sector → carpeta/circular → tablas + chips SQL):
  cada carpeta se identifica con cat_<tabla_id> (cat_afp_lista_entidades, cat_bancos_balance);
  si agrupa varias tablas, cat_<prefijo>_<contenido> (cat_seguros_cartera_1835, cat_ffmm_cartera_1333)
  toda carpeta de lista de entidades se rotula «Lista de Entidades» (el registro único, «· Registro»)
  render árbol, búsqueda, resizer
  onCircularSelect → breadcrumb, ERD.focusSector, ChatTerminal.setCustomChips, abrir 1ª tabla
  onTableSelect    → ERD.focusTable, DataViewer.load(view), terminal "SELECT * … LIMIT"

DataViewerController (DATA_VIEWER_CATALOG): opción = <sector>.<tipo> · tipo de tabla; query LIMIT n → tabla con filtro, orden, copiar celda; «Descargar datos» abre Descargas con la tabla puesta
DataDictionaryController: diccionario por sector (rol PK/FK/Dim/Métrica, criterio contable) con filtro y búsqueda
ERDGraph (canvas): nodos por tabla + enlaces FK; zoom/pan; click → modal esquema / abrir tabla
ChatTerminalController: input SQL, historial ↑↓, favoritos en localStorage, compartir por #hash, render + ChartRenderer
DownloadsPanelController (js/downloads_panel.js): dibuja DOWNLOAD_CATALOG con búsqueda, filtro por sector y
  recorte por años; Parquet directo (un enlace por periodo cuando el conjunto va por partes), CSV y Excel
  armados con DuckDB, y «SQL» que abre el terminal con la consulta lista
MFCDownload (js/download_utils.js): numero/bytes/fecha, CSV con BOM y «;», XLSX, descarga por Blob,
  ZIP si supera 250.000 filas en CSV / 150.000 en Excel, tope de 1.048.576 filas por hoja
UX shell (js/ux_shell.js): pestaña recordada, avisos, estado del motor, Alt+1…7 y «/»
theme_switcher: 6 paletas vía CSS vars; persistencia localStorage; re-render ERD

Contrato de coherencia (lo verifican audit_interfaz.py, audit_interfaz_dom.js, audit_navigation.py y audit_web_full.py):
  cada tabla del sidebar ↔ vista SEMANTIC_VIEWS ↔ opción del visor ↔ diccionario ↔ nodo ERD ↔ Parquet existente
  cada sector abre con «Lista de Entidades» = su lista_entidades canónica (salvo macro, que son series)
  ningún nombre retirado por el vocabulario aparece en los archivos de la web
  cada conjunto del catálogo de Descargas ↔ vista publicada ↔ manifest/Parquet existente
  los 15 assets locales llevan la misma etiqueta de versión (evita caché vieja entre pestañas)
```

Cómo levantarla en local:
```
python -m scripts.preview_no_cache --port 8000      # sirve docs/ en 0.0.0.0:8000, sin caché
    soporta HTTP Range (206 Partial Content) igual que GitHub Pages → DuckDB-Wasm lee solo pie + row groups
    (antes devolvía 200 con el archivo completo: 71 MB para leer 100 bytes)
requisitos del navegador: la copia local de DuckDB-Wasm cubre el caso normal; jsDelivr/unpkg sólo si falta
```

Otros scripts transversales (`scripts/`): `preview_no_cache.py` (servidor local), `audit_secretos.py` (credenciales
en el historial), `build_download_catalog.py`
(genera `docs/js/download_catalog.js`: 52 conjuntos, filas, peso y periodo de cada vista publicada),
`normalizar_vocabulario.py` (aplica y vigila el vocabulario de §9).
(`standardize_schema_keys.py`, `verify_joins.py` y `orchestrate_overnight_market_pipeline.py` se eliminaron
con los pipelines antiguos de FFMM y FI.)

---

## 10. CI (`.github/workflows/`)

| Workflow | Cron (UTC) | Publica | Qué hace |
|---|---|---|---|
| macro.yml | diario 10:00 | commit automático | daily_macro (3 tablas mensuales) + series_bcch (51 series, formato largo) |
| bancos_cmf_mensual.yml | días 1, 11, 21 13:00 | **sí** (commit + Pages) | tests + publish_cmf_bank_period --catch-up (incremental) |
| web_audit.yml | push a main, PR hacia main y lunes | no | audit_navigation + audit_web_full + audit_interfaz + prueba DOM + audit_secretos (anotaciones); el lunes, guardián de frescura |
| factoring_leasing_backfill.yml | días 3, 13, 23 12:20 | **sí** | backfill_ifrs + publish_backfill + auditorías web |
| ifrs_sectores.yml | días 2, 12, 22 13:30 | **sí** (commit + Pages) | estados IFRS de AGF, securitizadoras y CCAF (§8a) |
| corredoras_eeff.yml | días 6, 16, 26 13:45 | **sí** (commit + Pages) | estados FECU IFRS de corredores y agentes (§8a) |
| seguros_carteras.yml | días 7, 17, 27 14:00 | **sí** (commit + Pages) | cartera de inversiones de aseguradoras (§6) |
| ffmm_carteras.yml | días 8, 18, 28 14:00 | **sí** (commit + Pages) | cartera de fondos mutuos, Circular 1333 (§7) |
| fi_carteras.yml | días 9, 19, 29 15:00 | **sí** (commit + Pages) | cartera y pactos de fondos de inversión (§7) |
| entidades.yml | días 10, 20, 28 12:30 | **sí** (commit + Pages) | altas y vigencia de las listas de AGF, securitizadoras, corredores, fintech, bancos, cooperativas y sistemas de pago (registros CMF), patrimonios separados (inscripciones por registro automático) y AFP (Superintendencia de Pensiones) (§8c) |

---

## 11. Hallazgos de la revisión (estado al 2026-09-29)

**Auditoría de eficiencia (2026-09-29) — todo medido, defectos 2–6 cerrados o documentados**
- **Arranque en frío** (prioridad 1): 23 s en frío vs ~3,5 ms en caliente se descompuso en wasm 18,1 MB
  + 31 manifiestos en serie + 536 `registerFileURL` en serie + 71 `CREATE VIEW` en serie. Solución:
  las tres fases del arranque ahora son paralelas (`Promise.all`) y el wasm y los manifiestos se
  precalientan con `<link rel="preload">`. La medición en el navegador queda en manos de quien
  tenga un navegador (en este entorno no hay Chromium); en el arnés `scripts/audit_duckdb_client.js`
  el registro de las 52 vistas + 10 comprobaciones sale OK sin navegador.
- **Defecto 6 (conteos)**: `data_manifest.json` pasó de 49/10.870.630 a **51 datasets · 10.870.757
  filas** (faltaban `cooperativas_lista_entidades` y `corredoras_bolsa_lista_entidades_registro`).
  52 vistas = 51 datasets: `bancos_balance` y `bancos_resultados` comparten el datasete
  `bancos_cmf_lineas` (55 particiones, contado una vez). **Nueva guardia**:
  `audit_automatizacion.py::alineacion_manifest()` falla si una entrada del manifiesto deja de
  coincidir con las filas reales de sus Parquet, o si una vista publicada queda sin entrada.
- **Defecto 3 (AGF vacía)**: `fi/scripts/actualizar_carteras.py` calcula
  `fondos_inversion_administrados`; backfill ya publicado → 47/72 AGF con valor > 0.
- **Defecto 4 (bienes raíces)**: la CMF publica 0 filas de bienes raíces para FI en los 26
  trimestres disponibles (vs 933.532 de cartera nacional) → se publica la vista marcada
  «Sin datos» en sidebar, diccionario y vocabulario; su consulta va en `VACIAS_ESPERADAS`.
- **Defecto 2 (formatos RUT)**: **corregido (2026-09-29)**, decisión «aplica todo».
  Convención canónica: `rut` = **cuerpo** (C), `rut_dv`/`*_dv` = cuerpo-DV (B),
  `rut_completo`/`*_completo` = puntos y DV (A; RUNs de 4-5 cifras quedan B).
  `rut_cuerpo` y `rut_formateado` dejan de existir. Aplicado a **193 Parquet + 7 JSON**
  (`scripts/normalizar_rut_publicado.py --apply`, idempotente, conserva row groups y codec);
  5 valores corruptos de fuente en `ffmm_cartera_nacional` corregidos (DV `X` inválido →
  `K` por módulo 11; `0-.` → `0`). El cruce que motivó el hallazgo
  (`corredoras_bolsa_maestro.rut = corredoras_bolsa_balance.rut`) pasa de 0 a miles de filas.
  Ver `docs/notas/rut_formatos_2026-09-29.md`.
- **Catálogo de Descargas** ahora cuenta también las dos vistas unificadas de banca por sus filas
  heredadas (fue 8.942.793 → ahora **10.870.757**, igual con o sin pyarrow); la nota de pie del
  README se actualizó.
- **CI**: `web_audit.yml` ahora corre `audit_consultas_sugeridas.py --check` (116/0/0),
  `scripts/audit_duckdb_client.js` y el **guardián de RUT**
  (`scripts/audit_rut_formatos.py`: 613 archivos, 0 problemas) en cada push; el flujo de
  automatización instala pyarrow para la nueva guardia de alineación.
- **Writers blindados**: `pipelines/auto/rut.py::normalizar_*` se aplica en el único punto de
  escritura de las listas (`entidades/actualizar_listas.py::guardar`), en los constructores de
  maestros de cooperativas y corredoras, en `factoring_leasing/publish_backfill.py`, en las
  actualizaciones de carteras de ffmm y seguros y en el maestro de pensiones: la próxima
  corrida de CI publica el formato canónico, no lo que traiga la fuente.
- Auditorías en verde: navegación 12/52/52 · automatización 53 tablas / 0 problemas ·
  vocabulario 52/15/22 · consultas sugeridas **116 OK · 0 VACIA · 0 ERROR** · web full 100 % ·
  cliente DuckDB 10/10.

**3ª pasada (rama de trabajo, 2026-09-28) — interfaz, descargas y vocabulario**
- Proyecto renombrado a **Sistema de Información Financiera de Chile (SIF)**; el panel principal pasó a
  **siete pestañas** con el terminal SQL como pestaña propia (se eliminó el panel inferior y su divisor).
- La descarga dejó de ser un modal: es la pestaña **Descargas**, alimentada por el catálogo generado
  (`scripts/build_download_catalog.py` → `docs/js/download_catalog.js`). `docs/js/export_modal.js` se eliminó.
- **Vocabulario canónico** (§9): `docs/vocabulario.json` + `scripts/normalizar_vocabulario.py`. Todos los ids
  `*_maestro` pasaron a `*_lista_entidades`, las cinco variantes de «lista de entidades» desaparecieron de la
  interfaz, los nodos del árbol se llaman `cat_<tabla_id>` y los nombres anteriores sólo sobreviven como
  vistas de alias en SQL.
- ✅ Auditorías en verde: `audit_interfaz.py` («INTERFAZ COHERENTE», incluye vocabulario y caché) ·
  `audit_interfaz_dom.js` **39/39** · `audit_navigation.py` 12 familias, **52 tablas, 52 opciones del visor,
  14 sectores** · `audit_automatizacion.py` **0 problemas** (traduce los ids históricos por los alias del
  vocabulario) · `audit_normativa_web.js` OK · `audit_web_full.py` 100%.
- ✅ Catálogo de Descargas regenerado con conteo real de filas (pyarrow): **52 conjuntos, 8.942.772 filas y
  261,8 MB**; los dos conjuntos unificados de banca informan «filas: se cuentan al consultar» en vez de
  repetir el total del manifiesto (que suma B1 + B2 + R1, no lo que muestra la vista).
- ✅ Los 15 assets locales de `docs/index.html` comparten una sola etiqueta de versión
  (`?v=20260928-vocabulario-1`), verificada por `audit_interfaz.py`; antes convivían cinco etiquetas.

**2ª pasada (sobre `df3e26c`)**
- Tests: `bancos` 81 OK · `factoring_leasing` 42 OK (tras corregir el manifiesto) · `xml_eeff` 44 OK · `macro` requiere `bcchapi`.
- `audit_navigation.py`: 12 familias, 86 tablas, 86 opciones del visor ✅ · `audit_web_full.py`: 100% (831 columnas del diccionario, 74 nodos / 69 enlaces ERD) ✅.
- ✅ `data_manifest.json` decía `total_tables: 65` con 63 entradas (fallaba `test_publication`). Causa: `update_data_manifest` sumaba incrementos. Ahora recalcula desde la lista; `file_parquet` de bancos apunta al último período (2026-07, antes 2026-06).
- ✅ `preview_no_cache.py` sin soporte HTTP Range → agregado.
- ✅ (2026-09-28) Se quitaron de `data_manifest.json` las 4 tablas AFP retiradas cuyos Parquet ya no existían.
- ✅ `web_audit.yml` y `factoring_leasing_backfill.yml` se disparaban en push a ramas de sesiones anteriores; ahora `main` + rama de trabajo actual.
- ~~Muchas vistas del visor no tienen entrada en `data_manifest.json`…~~ → **Resuelto en la
  auditoría de eficiencia (2026-09-29):** cada vista publicada tiene entrada en el manifiesto
  (51 datasets para 52 vistas; `bancos_balance`/`bancos_resultados` comparten `bancos_cmf_lineas`),
  vigilado por `alineacion_manifest()`. La fuente de verdad del visor sigue siendo
  `SEMANTIC_VIEWS`; el manifiesto es el inventario contable.

**1ª pasada**

**Tests** (tras las correcciones del 2026-09-28)
- `bancos/tests` 68 OK · `factoring_leasing/tests` 42 OK · `pipelines/xml_eeff/tests` 44 OK · `macro/tests` 9 OK (requiere `bcchapi`).
- ✅ Se agregó `__init__.py` a las carpetas `tests/`: `unittest discover -s <dir> -t .` ya funciona.
- ✅ `scripts/audit_navigation.py` actualizado a la estructura real de Bancos (maestro + CMF B1/B2 + R1; REPO legado retirado).
- ✅ `scripts/audit_web_full.py` ahora entiende vistas por `manifest` (particiones) y avisa sin fallar si aún no hay períodos.
- ℹ️ `docs/outputs/bancos/cmf_b1_b2_r1/manifest.json` sigue vacío (no hay Parquet bancario en ningún lado; se llena ejecutando `python -m bancos.scripts.publish_cmf_bank_period` con internet, o el workflow manualmente): las vistas `bancos_cmf_balance/resultados` aparecen "no disponibles" hasta la primera corrida mensual exitosa de `bancos_cmf_mensual.yml`.

**Deuda técnica / riesgos**
1. ✅ **Rutas `C:\Users\joaqu\…` eliminadas** (32 scripts): la raíz vieja `bcch_market_monitor` → `_ROOT` relativo al repo; `Desktop\Respaldo_BCCH` → `_RESPALDO` (variable `MFC_RESPALDO_DIR`, por defecto `~/Desktop/Respaldo_BCCH`); otros archivos del Escritorio → `Path.home()/'Desktop'/…`.
2. ✅ `docs/ffmm/` y `docs/fi/` eliminados (624 archivos idénticos); sidebar y ERD leen ahora `outputs/ffmm|fi/…`. ✅ `docs/outputs/b7_*.parquet` y todo lo antiguo de seguros eliminados (2026-09-28). Ojo: los pipelines FFMM/FI escriben en `ffmm/…/outputs` y `fi/…/outputs`; hay que copiar a `docs/outputs/` al publicar.
3. Utilidades (DV, parse_num, tc_map) repetidas en ~15 archivos.
4. ✅ `fintech/scripts/explore.py` corregido (compilaba solo en Python ≥ 3.12).
5. ✅ BOM UTF-8 eliminado de 9 scripts.
6. ✅ Credenciales: `scripts/audit_secretos.py` audita todo el historial alcanzable (2.551 blobs de texto).
   Resultado: los únicos valores ligados a las variables BCCh fueron marcadores de posición del commit inicial
   (`REMOVED_BCCH_EMAIL`, `CAMBIAR_ESTE_PASSWORD`) y claves de prueba; ninguna credencial real. La nota anterior
   («hay que rotar la contraseña expuesta») quedó sin sustento y se corrigió en `pipelines/README.md`.
7. `.git` pesa ~270 MB por el historial (los Parquet antiguos de seguros siguen en commits viejos). Considerar Git LFS o releases.
8. ✅ Ya existe `requirements.txt` global (Python 3.11, pyarrow/openpyxl/xlrd fijados igual que en Actions).
9. Muchos scripts exploratorios (`pensiones/inspect_*`, `test_*` que no son tests) mezclados con pipelines productivos.

**Siguientes pasos sugeridos (por prioridad)**
1. ✅ ~~Arreglar auditorías web~~ (hecho).
2. ✅ ~~Duplicados docs/ffmm, docs/fi~~ y ✅ ~~rutas C:\~~.
3. Crear `common/` con utilidades chilenas (DV, parse_num, tc_map).
4. Mover exploratorios a `*/scratch/` o `archive/`; (`__init__.py` en `tests/` ✅).
5. ✅ ~~`requirements.txt` global~~ (hecho).

---

## Mapa del repositorio

```
<fuente>/            extracción por sector (seguros, ffmm, fi, bancos, macro, ccaf, …)
  scripts/           extractores, normalizadores y auditorías del sector
  tests/             pruebas unitarias del flujo
pipelines/           flujos transversales
  entidades/         altas y vigencia de las listas de entidades (CMF y SPensiones)
  ifrs_sectores/     estados IFRS trimestrales (AGF, securitizadoras, CCAF)
  normativa_cmf/     seguimiento de normativa (único flujo con lectura asistida)
  auto/inventario.json  quién actualiza cada tabla y con qué frecuencia
  auto/rut.py          convención canónica de RUT (cuerpo / cuerpo-DV / puntos)
  manual/            ingesta de notas y reportes transcritos
docs/                sitio estático (lo que se publica)
  index.html         la aplicación (7 pestañas)
  js/  css/          interfaz, motor DuckDB, catálogo de descargas
  img/               capturas usadas en el README
  vocabulario.json   nombres canónicos de todas las tablas
  outputs/           52 Parquet publicados + manifiestos
  vendor/duckdb/     DuckDB-Wasm embebido (MIT) — ver su README antes de actualizarlo
  notas/             bitácora técnica de las decisiones
scripts/             auditorías, generadores y servidor de vista previa
.github/workflows/   11 flujos programados + despliegue
```

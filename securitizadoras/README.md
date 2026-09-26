# Securitizadoras y Patrimonios Separados — Manual del sector

Estado tras la fase de arreglos (2026-09-26). Auditoría de origen: [`AUDITORIA_2026-09-26.md`](AUDITORIA_2026-09-26.md).
Auditoría automática: `python securitizadoras/scripts/audit_patrimonios_separados_v2.py` → hoy **0 FAIL · 2 WARN**.

## 1. Qué hay ahora

```
securitizadoras/
├── scripts/
│   ├── pipeline_securitizadoras.py         # ÚNICO pipeline (maestro, gestoras, ps, reparar-legacy, todo)
│   └── audit_patrimonios_separados_v2.py   # auditoría de sustancia; exit 1 si hay FAIL (corre en CI)
├── tests/test_pipeline_securitizadoras.py  # 24 pruebas del parser sin red (corre en CI)
├── legacy/                                 # 10 tablas v1 en cuarentena (Parquet) + README con motivos
├── AUDITORIA_2026-09-26.md
└── README.md                               # este manual
docs/outputs/securitizadoras/               # 4 tablas publicadas (ver §3)
```

Publicado en la web (sidebar, diccionario, ERD, visor, manifest):

| Tabla | Filas | Fuente CMF | Paso |
|---|---|---|---|
| `securitizadoras_maestro` | 16 | Búsqueda de entidades RGSEC | `maestro` |
| `securitizadoras_balance_resumen` | 362 | FECU IFRS trimestral (HTML, pestaña 3) | `gestoras` |
| `patrimonios_separados_maestro` | 18 | Listado de títulos de deuda inscritos | `maestro` |
| `patrimonios_separados_balance_resumen` | 64 | EEFF anuales de PS (PDF, pestaña 18) | `ps` |

El paso `ps` (trimestral, 2010 → hoy, todas las securitizadoras incluidas las no vigentes) genera además:

| Tabla (se crea al correr el pipeline) | Contenido |
|---|---|
| `patrimonios_separados_eeff_lineas` | **Balance general y estado de excedentes línea a línea** (formato largo: `estado`, `codigo_fecu` si el PDF lo trae, `glosa` original, `nota`, `monto_mclp`, `monto_anterior_mclp`, `cuenta_canonica`, `seccion`, `es_total`, `pagina_pdf`). Reemplaza a `balance_lineas` + `excedentes_lineas` de la cuarentena. |
| `patrimonios_separados_balance_resumen` | Pivot de las líneas por cuenta canónica + `cuadre_contable_ok`, `conciliacion_componentes_ok`, `cuentas_reconocidas / no_reconocidas`. |
| `patrimonios_separados_notas_detalle` | Efectivo y morosidad (sólo PDFs de diciembre), formato largo. |
| `patrimonios_separados_cobertura` | Un registro por PDF: `ok`, `sin_codigo_emision`, `pdf_sin_texto_(escaneado)`, `pdf_no_disponible`, `error_*`, más nº de líneas y cuentas reconocidas. |

El mapeo glosa/código → cuenta canónica está en `securitizadoras/data/catalogo_fecu_ps.json` (versionado; 40
cuentas FECU-PS, 3 conciliaciones). Soporta los dos layouts reales encontrados en CMF: glosas sin código (p. ej.
Volcom/KPMG) y FECU con códigos `11.010…` (p. ej. Security). Ninguna de estas tablas existe todavía en el repo
porque en el sandbox no hay acceso a CMF; se crean al ejecutar el pipeline (§4) y quedan **fuera de la web** hasta
que pasen la auditoría.

## 2. Qué se arregló y cómo (hallazgo → solución)

| # | Hallazgo de la auditoría | Solución aplicada |
|---|---|---|
| 1 | 8 tablas de PS (49.868 filas) sin script generador | **Despublicadas**: Parquet movido a `securitizadoras/legacy/` (JSON eliminado), quitadas de `sidebar.js`, `data_dictionary.js`, `erd_graph.js`, `duckdb_client.js`, `data_viewer.js`. **Fuente identificada**: los mismos PDFs de la pestaña 18 de CMF pero trimestrales (03/06/09/12, disponibles desde 2000). Se implementó su reconstrucción reproducible como `patrimonios_separados_eeff_lineas` (paso `ps`, catálogo FECU-PS). Al contrastar con el PDF real de Volcom BVOLS 12/2024, la tabla v1 tenía montos corruptos (p. ej. `11.030 = 94.335.870` donde el PDF dice `4.335.870`: concatenó el N° de nota 9 con el monto), lo que confirma que no debía repararse sino regenerarse. |
| 2 | Placeholders al 100 % (`nota_bonos`, `nota_sobrecolateral`, `repos_detalle`) y `cartera_morosidad` con provisión > cartera | Despublicadas (mismo mecanismo). El pipeline v2 **no** produce repos ni bonos: no había forma de extraerlos sin inventar plazo, tasa, emisor y cumplimiento. |
| 3 | RUT de administradora truncado (`9676517-0` en vez de `96765170-2`) | `rut_completo()` con módulo 11 sobre el cuerpo íntegro. `reparar-legacy` recalculó los RUT de las 4 tablas publicadas (el cuerpo correcto estaba en `id_patrimonio` y en `rut`). `securitizadoras_balance_resumen.rut` y `patrimonios_separados_maestro.rut_administradora` ahora llevan DV y cruzan con `securitizadoras_maestro.rut_completo`. La auditoría valida DV en todas las tablas. |
| 4 | `id_patrimonio` inestable (573 ids, 3 slugs por PS) y sin cruce entre tablas | Las tablas con slugs inestables están en cuarentena. En v2 el id es determinista: `{rut_cuerpo}_{codigo_emision}` con `codigo_emision` normalizado (`PS-12` → `ps_12`, nemotécnico en mayúsculas) y se captura `nro_registro_cmf` para cruzar con `patrimonios_separados_maestro.numero_inscripcion`. Si el PDF no permite identificar el PS, **no se emite fila** (`estado = sin_codigo_emision` en cobertura) en lugar de inventar `PS-GEN`. |
| 5 | `balance_lineas` con 25 % de cuadre; `balance_resumen` v1 igualaba activos a pasivos cuando faltaba uno | v2: los totales faltantes quedan `NULL`; `cuadre_contable_ok` sólo es verdadero si ambos totales existen y coinciden (±0,1 %). Para los 64 balances v1 se **recalculó** el flag con componentes (pasivo circulante + largo plazo + excedentes vs activos, ±1 %): 31 cuadran, 33 no. La web muestra el flag. |
| 6 | Defaults inventados en el parser (tasa 0,39, plazo 30, "Banco Central de Chile", fechas sintéticas, "Cumple / SI"), TC hardcodeado, `CERT_NONE` | Parser reescrito sin valores por defecto (pruebas lo cubren: "sin total → NULL", "sin número de nota → no se publica", "sin código → None"). Tipo de cambio sólo desde `macro_divisas_mercado.parquet`; si falta, las columnas `_musd` quedan `NULL` (en v1 se anularon porque usaban tasas fijas). TLS verificado; `MFC_CMF_INSECURE_TLS=1` es opt-in explícito y queda registrado en `metodo`. La auditoría detecta `else <número>`/strings de negocio y `CERT_NONE` sin opt-in. |
| 7 | 27 variantes de tramo de mora, % provisión absurdos | Catálogo cerrado `TRAMOS_MORA` (12 claves). Lo no reconocido se descarta y se cuenta en `cobertura.tramos_mora_descartados`; filas con provisión > cartera se descartan (mala lectura de columnas). |
| 8 | `ganancia_perdida_ejercicio_m_clp = 0` en 362/362 (regex fallaba) | Regex ampliada (`Ganancia (pérdida) [del ejercicio / atribuible…]`) con prueba unitaria; ausencia → `NULL`. En los datos v1 los ceros se pasaron a `NULL` para no simular resultado cero. Además `patrimonio_neto` ahora se lee de la FECU (`Patrimonio total`) y `patrimonio_neto_es_derivado` marca cuándo tuvo que calcularse como A − P (v1: siempre derivado, por eso su "cuadre 100 %" era tautológico). |
| 9 | `clase_colateral_subyacente` en el maestro de PS era una heurística por nombre de emisor | Columna eliminada (dato no publicado por CMF). Chip del sidebar reemplazado por "Líneas por Administradora". |
| 10 | Sin columnas de procedencia | Todas las tablas llevan `fuente_url`, `metodo`, `fecha_extraccion`, `script_version` (y `pdf_sha256` en las de PDF). Los datos v1 reparados llevan `metodo = legacy_v1_*` y `script_version = …|reparar-legacy` hasta que se regeneren. |
| 11 | Dos formatos de `periodo` (`202412` y `2024-12`) | Sólo queda `YYYY-MM`. |
| 13 | (datos reales, corrida 2021–2026) la etiqueta web de CMF nombra al mismo PS de varias formas: `PATRIMONIO SEPARADO N°35`, `Patrimonio 10`, `PS7 firmadp`, `BVOLS3` / `BVOLS 3`, `V` | `canonizar_codigo()`: quita palabras genéricas y sufijos de archivo, número (con o sin `N°`/`PS`/`NA`) → `PS-n`, romanos → `PS-n`, letras+dígitos pegados → `BVOLS-3`. La etiqueta web es la fuente primaria del código; el texto del PDF sólo se usa si la web no trae código. Pruebas con 12 etiquetas reales. |
| 14 | Glosas sin plazo (`Obligaciones por títulos de deuda de securitización`, `Otros acreedores`, `Activo securitizado`) aparecen tanto en pasivo circulante como en largo plazo | El parser sigue la **sección del balance** (encabezados `Pasivos circulantes`, `Pasivos largo plazo`, `Otros activos`…) y el catálogo tiene `regex_seccion`, que sólo aplica dentro de esa sección. La sección queda en `seccion_balance`. |
| 15 | El estado de excedentes venía en la misma página que el pasivo y sus líneas se etiquetaban `BALANCE`; páginas de notas (tramos de mora `1 a 3`, `Totales`) se leían como balance | El estado cambia a `EXCEDENTES` al aparecer su encabezado dentro de la página; una página sólo se conserva si contiene al menos una línea de **total reconocida**; encabezados de columna (`ACTIVOS`, `Concepto`, `$REAJUSTABLES`, `MONEDA`…) están en `glosas_ignoradas`. |
| 16 | Layout FECU con columnas `$ reajustables / $ no reajustables / total` | Se leen hasta 4 columnas (`monto_col3`, `monto_col4`) y la página se marca `layout_multicolumna` para poder revisar qué columna es el total; no se descarta ni se adivina. |
| 17 | Ganancia de las gestoras seguía `NULL`: la fila `Ganancia (pérdida)` del estado de resultados `[310000]` no tiene la misma estructura HTML que el balance, y CMF escribe `p&eacute;rdida` | `html.unescape` + lectura genérica "glosa → primer número" excluyendo `[sinopsis]`, `, antes de impuestos`, `procedente de…`. La auditoría ahora **falla** si la columna queda nula/0 en ≥ 50 % (antes sólo miraba ceros). |
| 18 | (diagnóstico con texto real de 36 PDFs que no cuadraban) En EF los dos montos vienen en **una sola línea** (`5.762   5.750`) debajo de la glosa y el nº de nota; el lector sólo aceptaba una cifra por línea → páginas enteras de pasivo perdidas | `_numeros_siguientes` acepta líneas con varias cifras. Sólo este cambio recuperó 16 de los 36 casos. |
| 19 | Códigos FECU impresos poco fiables: Security repite `15.210` en casi todas las filas y Transa pone `23.000` delante de `TOTAL PASIVOS`; el código mandaba sobre la glosa y el total quedaba mal clasificado | Prioridad invertida: glosa (regex curada) → glosa dentro de la sección → código FECU sólo como último recurso. |
| 20 | Texto con letras espaciadas (`T OT A L A C T IVOS`) en PDFs de Security | Si la glosa tiene mayoría de tokens de 1–2 letras se compara sin espacios contra los mismos regex sin espacios. |
| 21 | Sudamericana imprime `11.010 Disponible` (código y glosa en la misma línea) con los montos debajo | Se separa el código al inicio de la glosa. |
| 22 | El cuadro de la Nota 7 de EF trae `Total de Activo | 456` (nº de contratos) y pisaba `TOTAL ACTIVOS = 16.624.735`; tramos de mora en notas parseados como balance | Las páginas con encabezado `NOTA n -` y sin línea `TOTAL ACTIVOS` se excluyen del EEFF; el resumen toma la **primera** ocurrencia de cada cuenta (orden del PDF). |
| 23 | La pestaña 18 lista también "A. Razonado" (reporte de cartera, no EEFF) | Excluido al listar, igual que las declaraciones de responsabilidad. |
| 24 | Balances **embebidos como imagen** dentro de PDFs con texto (EF 06/2023, Security BSECS-6/10 06/2025): sin texto no hay líneas | OCR con Tesseract (`spa`, `--psm 6`, 300 dpi) sólo para páginas con imagen y < 300 caracteres; el workflow instala `tesseract-ocr-spa`. Las líneas quedan con `metodo = …+ocr_tesseract` y la cobertura registra `paginas_ocr`. Sin tesseract no se inventa nada. |
| 12 | Dos auditorías legadas que ya fallaban y tablas fuera de `data_manifest.json` | Retiradas (`04_audit_patrimonios_separados.py`, `audit_securitizadoras.py`); también `stream_cmf_securitizadoras.py` y `03_extract_…` (reemplazados por el pipeline). `patrimonios_separados_balance_resumen` añadida al manifest; badges del sidebar con los conteos reales (18 líneas / 64 balances, antes "485 vehículos / 42.800+ líneas"). |

Hallazgos de la **primera corrida completa 2010-2026** (2.727 PDF listados; 93,3 % cuadraba). Se revisaron uno a uno los volcados de páginas de los 272 PDF que no cuadraban:

| # | Hallazgo | Solución |
|---|----------|----------|
| 25 | PDFs antiguos con separadores mixtos (`5.155,432`, `3,549,070`) leídos como decimales | `parse_num`: un token `\d{1,3}([.,]\d{3})+` es siempre miles, sea cual sea el separador. |
| 26 | OCR con basura en los bordes (`\| Total pasivo circulante …`, `: TOTAL ACTIVOS …;`) y códigos FECU mal leídos (`20. TOTAL PASIVOS`) | Limpieza de bordes por línea; el código se acepta sólo con forma `dd.ddd`. |
| 27 | Sudamericana imprime **activos y pasivos lado a lado** en la misma línea | Cada línea con ≥ 2 pares (glosa + cifras) se separa en filas independientes. |
| 28 | Encabezados `PASIVOS Y PATRIMONIO` seguidos de la fila de fechas `31.12.2013` tomaban la fecha como monto | `_numeros_siguientes` corta al encontrar filas de fecha/año; encabezados en `glosas_ignoradas`. |
| 29 | Glosas truncadas por OCR (`AL OTROS ACTIVOS`, `RGO PLAZO`) o con erratas | Mapeo difuso (`_mapear_difuso`, difflib ≥ 0,86 o sufijo cortado a mitad de palabra) como **último** recurso; un total exige la palabra TOTAL. |
| 30 | Security BSECS-3 2021-22 imprime `TOTAL PASIVOS (x)` entre paréntesis | Cuadra si `A + P = 0` y los subtotales de pasivo suman el total; flag `signo_total_pasivos_invertido`. |
| 31 | Total impreso ausente o mal leído (`TOTALACTIVOS AR 000522`) mientras los subtotales de ese lado suman exactamente el total del otro | Se usa la suma de subtotales; el impreso queda en `total_*_impreso_mclp` y `total_corregido_por_componentes` indica el lado (`activos`, `pasivo_patrimonio`, `ambos`). Nunca se inventa: exige igualdad ≤ 0,1 % con el otro lado. |
| 32 | Páginas escaneadas **giradas** (Transa 2010-17, Sudamericana 2010-12): el OCR devuelve basura; PDFs con fuente sin mapa Unicode (EF 2013) devuelven caracteres de control y no se hacía OCR | Se mide la calidad del OCR (cifras con miles + palabras); si es baja se reintenta a 90°/270° y con `--psm 4`; el texto ilegible se descarta y la página pasa a OCR. Encabezado ilegible → la página se clasifica por su contenido (`TOTAL PASIVOS`, `ACTIVO CIRCULANTE`). |
| 33 | 2.249 etiquetas web distintas → 569 `id_patrimonio` para ≈70 PS reales (`BSECS-9 12.2012`, `PS12 Banchile EEFF Marzo 2020`, `NÂ°13_0915`, `201912 - Patrimonio Separado 5`, `PRIMER PATRIMONIO SEPARADO`, `PATRIMONIO NÂ°`…) | `canonizar_codigo` reescrito: **extrae** el código en vez de limpiar el resto — primero un código de serie (`BSECS-9`, `BBICS-A`, `BTRA1-1`, `BVOLS 3`, `BSABN-ABH`, `VBOLS-A1`), si no el primer número de 1-3 cifras u ordinal/romano (`V`, `DOS`, `PRIMER`); fechas (4+ dígitos), meses y razón social nunca se consumen. `Nº` sin número → `None` y el código se toma del PDF (`N*2`). Sobre las 2.249 etiquetas quedan 71 códigos. Cuando un PS+período viene en dos PDF (`BTRA1-1 INFORMACION FINANCIERA` y `PATRIMONIO SEPARADO BTRA1-1`) se conserva un solo documento (el que cuadra y con más cuentas) para balance, líneas y notas. `INFORME PATRIMONIO SEPARADO Nº1` (Santander 2010-11) sí es el EEFF: ya no se excluye por la palabra *informe* (sí por *auditor*, *anexo*). |
| 34 | `paso gestoras` sin balances anteriores a 2017 y `ganancia` vacía | Timeout 60 s + reintento (la CMF tarda en períodos antiguos); en modo diagnóstico guarda hasta 3 FECU HTML sin ganancia para revisar el selector. |
| 35 | Escaneos nítidos pero con **celdas bordeadas** (Transa 12/2015): tesseract mezcla bordes y dígitos (`TOTAL ACTIVOS 2 or \| too 03`); páginas **boca abajo** (180°) en Transa 2010-12 pasaban por texto válido | OCR v5: rotaciones 90/180/270; la calidad se mide con cifras + palabras castellanas reales (lista cerrada), no con "palabras largas"; para toda página OCR se prueba además la imagen **sin líneas de tabla** (morfología OpenCV, 400 dpi, psm 6 y 4) y gana la lectura con más filas *glosa + monto*. En modo debug se guarda el PNG de las páginas OCR que no cuadran: la evidencia visual es la que permitió diagnosticar esto. |
| 36 | Restos de OCR entre glosa y cifras (`TOTAL PASIVOS ] - 828.802 \| 1.312.589`, `TOTAL PASIVOS g al 2 1.356.630.`, `TOTAL PASIVOS. 0 5.239.679`) | Limpieza determinista por línea: tokens `\| ] [ l` sueltos, signo separado (`- 40.836`), punto final pegado a la cifra, letras/dígitos sueltos antes de la primera cifra; la glosa se compara sin puntuación final antes de recurrir al código impreso (`TOTAL PASIVOS.` con código 23.000 caía en excedentes). Transa 12/2015: 0/7 → 5/7. |
| 37 | Cifras que el OCR no puede leer (dígito ilegible, celda vacía en el escaneo) | **Corrección manual con evidencia**: `securitizadoras/data/correcciones_manuales.csv` (`id_patrimonio, periodo, cuenta_canonica, monto_mclp, fuente_url, pagina_pdf, justificacion, autor, fecha`). El pipeline la aplica antes de conciliar; la línea queda con `origen_monto = correccion_manual`, conserva `monto_leido_mclp`, y el balance lleva `correcciones_manuales = n` y `metodo …\|correccion_manual(n)`. La auditoría v2 (`correcciones_manuales`) **falla** si una fila no cita PDF+página+justificación+autor o si el balance no cuadra después de aplicarla. No hay imputación estadística: sólo cifras leídas del documento. |

Resultado sobre los 272 volcados: 146 cuadran ya con el texto guardado; 109 son páginas escaneadas giradas/ilegibles (requieren la nueva pasada de OCR en Actions); 17 casos residuales (p. ej. Security PS-14 03/2022, cuyo propio PDF descuadra en 1,1 MM$).

## 3. Diccionario mínimo de las tablas publicadas

- **securitizadoras_maestro** — `rut` (cuerpo), `dv`, `rut_completo` (PK), `razon_social`, `estado_vigencia`, `lineas_deuda_registradas`, `cmf_url` + procedencia.
- **securitizadoras_balance_resumen** — clave (`rut`, `periodo`); montos en **miles de CLP** (`_m_clp`); `patrimonio_neto_es_derivado`; `tipo_estado` (I individual / C consolidado, sólo v2); `tipo_cambio_usd_clp` y `_m_usd` `NULL` si no hay TC.
- **patrimonios_separados_maestro** — clave `numero_inscripcion`; `rut_administradora` con DV; `monto_inscrito` en la `moneda` indicada; fechas ISO.
- **patrimonios_separados_balance_resumen** — clave (`id_patrimonio`, `periodo`); `codigo_emision`, `nro_registro_cmf`; cuentas `_mclp` (miles de CLP) en `NULL` cuando no se leyeron; `cuadre_contable_ok`; `campos_extraidos` (v2) como medida de calidad de la lectura.

## 4. Cómo regenerar (sin instalar nada: GitHub Actions)

El sandbox del agente no llega a CMF, así que la extracción corre en **GitHub Actions**
(`.github/workflows/securitizadoras_extraccion.yml`), cuyos runners sí acceden a `cmfchile.cl`.

1. Edita `securitizadoras/extraccion/run.json` (`desde`, `hasta`, `trimestres` = `"03,06,09,12"` o `"12"`, `step` =
   `todo | maestro | gestoras | ps`) y haz commit/push (o usa *Run workflow* en la pestaña Actions).
2. El job: pruebas del parser → prueba de conectividad CMF → pipeline → auditoría v2 (no bloqueante) → **commit de
   `docs/outputs/securitizadoras/` en una rama `actions/ps-extraccion-<desde>-<hasta>-<run_id>`** + artefacto con
   `pipeline.log` y el JSON de la auditoría. No toca `main` ni la rama de trabajo.
3. Revisión antes de publicar (desde cualquier rama):
   ```bash
   git fetch origin actions/ps-extraccion-2010-2026-<run_id>:ext && mkdir -p /tmp/ext && git archive ext docs/outputs/securitizadoras | tar -x -C /tmp/ext
   PS_OUT_DIR=/tmp/ext/docs/outputs/securitizadoras python securitizadoras/scripts/audit_patrimonios_separados_v2.py
   ```
   Se miran `patrimonios_separados_cobertura` (estados ≠ `ok`), `cuadre_contable_ok` y el check
   `eeff_lineas_glosas_no_reconocidas_top`. Las glosas frecuentes sin cuenta canónica se agregan al catálogo
   (`regex` / `regex_seccion` / `glosas_ignoradas`) subiendo `version`; **nunca** se editan los Parquet a mano.
4. Si la auditoría da 0 FAIL, se copian las tablas a `docs/outputs/securitizadoras/` en la rama de trabajo, se
   actualizan `data_manifest.json`, `duckdb_client.js`, sidebar y diccionario, y se abre/actualiza el PR.

Modo diagnóstico: `run.json` acepta `"ruts": "96971830,…"` (sólo esas administradoras) y `"debug": "true"`, que vuelca el
texto de cada PDF que no cuadra en `docs/outputs/securitizadoras/_debug/` de la rama de resultados; con esos textos se
reproduce el caso en local (`parse_eeff_lineas`) y se agrega una prueba antes de tocar el parser. Así se resolvieron los
arreglos 18–24: la muestra de 36 PDFs sin cuadre pasó a 29/29 con texto nativo + 5 por OCR.

Tiempos observados: 72 PDFs (3 años, sólo diciembre) ≈ 8 min; 773 PDFs (2021–2026 trimestral) ≈ 35 min; la corrida
completa 2010–2026 trimestral (~2.000 PDFs) toma 1,5–3 h (límite del job: 350 min; si se corta, partir en tramos de años).

Alternativas equivalentes: el cuaderno `securitizadoras/colab/extraer_patrimonios_separados.ipynb` (misma
lógica, entrega por rama o zip) o localmente:

```bash
pip install -r requirements.txt
python securitizadoras/scripts/pipeline_securitizadoras.py --step ps --desde 2023 --trimestres 12   # rápido
python securitizadoras/scripts/pipeline_securitizadoras.py --step todo --desde 2010                 # completo
python securitizadoras/tests/test_pipeline_securitizadoras.py && python securitizadoras/scripts/audit_patrimonios_separados_v2.py
```

Los PDFs anteriores a ~2012 suelen ser escaneados: quedan como `pdf_sin_texto_(escaneado)` y no se inventan. Si CMF
rechaza la conexión TLS en tu red: `MFC_CMF_INSECURE_TLS=1 python …` (queda en `metodo`; no lo uses en CI).

## 5. Límites conocidos (WARN de la auditoría)

- Cobertura de balances de PS: 27 PS, 2022-12 → 2024-12, sólo securitizadoras vigentes. Ampliar con `MFC_PS_ANIOS`.
- `patrimonios_separados_cobertura` no existe hasta correr el paso `ps`.
- El parser lee **texto** de PDF: PDFs escaneados no se procesan (quedan en cobertura, no se inventan).
- Los datos v1 reparados conservan las lecturas originales del PDF; sólo se corrigieron RUT, cuadre, TC y ceros
  falsos. Se reemplazan íntegramente al correr `--step todo`.

## 6. Reglas para futuras extensiones

1. Nada se rellena: dato ausente = `NULL` + registro en cobertura.
2. Toda tabla nueva lleva las 4 columnas de procedencia y pasa `audit_patrimonios_separados_v2.py`.
3. Claves: `numero_inscripcion` (registro) e `id_patrimonio = {rut}_{codigo_emision}`; RUT siempre con DV.
4. Formato largo para notas (una fila por partida), catálogos cerrados para tramos/conceptos.
5. Sin credenciales ni rutas locales; TLS verificado por defecto.

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
| 12 | Dos auditorías legadas que ya fallaban y tablas fuera de `data_manifest.json` | Retiradas (`04_audit_patrimonios_separados.py`, `audit_securitizadoras.py`); también `stream_cmf_securitizadoras.py` y `03_extract_…` (reemplazados por el pipeline). `patrimonios_separados_balance_resumen` añadida al manifest; badges del sidebar con los conteos reales (18 líneas / 64 balances, antes "485 vehículos / 42.800+ líneas"). |

## 3. Diccionario mínimo de las tablas publicadas

- **securitizadoras_maestro** — `rut` (cuerpo), `dv`, `rut_completo` (PK), `razon_social`, `estado_vigencia`, `lineas_deuda_registradas`, `cmf_url` + procedencia.
- **securitizadoras_balance_resumen** — clave (`rut`, `periodo`); montos en **miles de CLP** (`_m_clp`); `patrimonio_neto_es_derivado`; `tipo_estado` (I individual / C consolidado, sólo v2); `tipo_cambio_usd_clp` y `_m_usd` `NULL` si no hay TC.
- **patrimonios_separados_maestro** — clave `numero_inscripcion`; `rut_administradora` con DV; `monto_inscrito` en la `moneda` indicada; fechas ISO.
- **patrimonios_separados_balance_resumen** — clave (`id_patrimonio`, `periodo`); `codigo_emision`, `nro_registro_cmf`; cuentas `_mclp` (miles de CLP) en `NULL` cuando no se leyeron; `cuadre_contable_ok`; `campos_extraidos` (v2) como medida de calidad de la lectura.

## 4. Cómo regenerar (en tu equipo, con acceso a CMF)

```bash
pip install -r requirements.txt
# rápido (sólo cierres anuales recientes) para validar el parser contra PDFs reales:
python securitizadoras/scripts/pipeline_securitizadoras.py --step ps --desde 2023 --trimestres 12
# completo (todas las securitizadoras, trimestral 2010 → hoy; varias horas, ~3.000 PDFs):
python securitizadoras/scripts/pipeline_securitizadoras.py --step todo --desde 2010
# o por partes: --step maestro | gestoras | ps
python securitizadoras/tests/test_pipeline_securitizadoras.py
python securitizadoras/scripts/audit_patrimonios_separados_v2.py
```

Después de correr `ps`, revisa `patrimonios_separados_cobertura.parquet` (estados distintos de `ok`) y el check
`eeff_lineas_glosas_no_reconocidas_top` de la auditoría: las glosas frecuentes sin cuenta canónica se agregan al
catálogo (`regex`) y se sube `version`; nunca se corrigen a mano en los Parquet. Los PDFs anteriores a ~2012 suelen
ser escaneados: quedan como `pdf_sin_texto_(escaneado)` y no se inventan. Sólo cuando la auditoría dé 0 FAIL conviene publicar `patrimonios_separados_notas_detalle`
(añadir a manifest + `duckdb_client.js` + sidebar).

Si CMF rechaza la conexión TLS en tu red: `MFC_CMF_INSECURE_TLS=1 python …` (queda en `metodo`; no lo uses en CI).

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

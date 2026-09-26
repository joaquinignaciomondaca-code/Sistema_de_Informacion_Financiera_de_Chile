# Factoring & Leasing — Manual de operación y de arreglos

Este documento explica **qué se arregló** tras la auditoría del 2026-09-26 (`AUDITORIA_2026-09-26.md`),
**cómo se arregló** y **cómo se opera el sector de aquí en adelante** para que se mantenga solo.
Sirve también de plantilla para aplicar el mismo tratamiento a los demás sectores.

---

## 0. Qué tienes que hacer tú (una sola vez)

1. **Rotar la contraseña del BCCh** (SIETE). Estuvo en 4 scripts de un repo que fue público. Ponerlo en
   privado no deshace la exposición.
2. Crear el archivo `.env` en la raíz del repo (está git-ignorado) a partir de `.env.example`:
   ```
   BCCH_USER=tu_correo
   BCCH_PASS=la_contraseña_nueva
   ```
3. Instalar dependencias: `pip install -r requirements.txt`.
4. Correr la primera regeneración completa del sector (necesita acceso a `cmfchile.cl`, ~49 descargas,
   5–10 min):
   ```
   python factoring_leasing/scripts/pipeline_factoring_leasing.py --step todo
   python factoring_leasing/scripts/audit_factoring_leasing_v2.py
   ```
   Este sandbox no tenía salida a CMF, por eso el resumen publicado sigue siendo el v1 (con columnas de
   trazabilidad ya añadidas) hasta que corras este paso.
5. Revisar `factoring_leasing/data/cuentas_no_mapeadas.json` (ver §4.3) y agregar al mapeo lo que corresponda.

---

## 1. Estructura del sector (después del arreglo)

```
factoring_leasing/
├── README.md                          ← este manual
├── AUDITORIA_2026-09-26.md            ← hallazgos y evidencia
├── data/                              ← FUENTES DE VERDAD versionadas (editar aquí, no en los outputs)
│   ├── catalogo_factoring_leasing.json    28 entidades, RUT módulo 11, vigencia, cobertura de EEFF
│   ├── mapeo_cuentas.json                 cuentas CMF → métricas del resumen (versionado)
│   └── cuentas_no_mapeadas.json           generado por el pipeline: lo que falta mapear
├── scripts/
│   ├── pipeline_factoring_leasing.py      ÚNICO pipeline (maestro → descarga → resumen)
│   └── audit_factoring_leasing_v2.py      auditoría de sustancia; exit 1 si hay FAIL
└── tests/
    └── fixture_cmf_202503.txt             muestra del formato CMF para pruebas offline

docs/outputs/factoring_leasing/
├── factoring_leasing_maestro.parquet/.json
├── factoring_leasing_eeff_cuentas.parquet        ← NUEVO: todas las cuentas CMF, formato largo
├── factoring_leasing_balance_resumen.parquet/.json
└── factoring_leasing_cobertura.parquet/.json     ← NUEVO: entidad × trimestre: ok / sin_archivo / sin_entidad
```

Se **eliminaron**: `pipeline_stream_factoring_leasing.py` (dependía de `C:\Users\...\*.xlsx` y tenía la
contraseña), `stream_cmf_eeff_series.py` (reemplazado por el pipeline único), `02_extract_..._notas_series.py`
(generaba datos sintéticos), `audit_factoring_leasing.py` (daba PASS a datos sintéticos) y las tablas
`factoring_leasing_nota_efectivo_detalle` y `factoring_leasing_cartera_morosidad_detalle` con todas sus
referencias en la web (`sidebar.js`, `erd_graph.js`, `data_dictionary.js`, `data_viewer.js`,
`duckdb_client.js`, `export_modal.js`).

---

## 2. Cada hallazgo y cómo quedó resuelto

| # | Hallazgo | Solución | Cómo se sostiene |
|---|----------|----------|------------------|
| 1 | Contraseña BCCh en código | `mfc_common/credentials.py` lee `BCCH_USER`/`BCCH_PASS` del entorno o `.env`; los 3 scripts restantes (bancos, macro, sistemas_pago) lo usan; `.env` git-ignorado; `.env.example` | `scripts/scan_secrets.py` corre en CI en cada push y falla si detecta credenciales |
| 2 | Notas sintéticas publicadas como CMF | Despublicadas de datos y web; script eliminado | Auditoría v2 detecta participaciones rígidas (sd < 0,005) en cualquier tabla `*_detalle` que se vuelva a publicar, y detecta scripts que multiplican por porcentajes fijos |
| 3 | Pipeline no reproducible (Excel local, CSV ignorado) | Un solo `pipeline_factoring_leasing.py`; catálogo en JSON versionado (`.gitignore` tiene excepción `!factoring_leasing/data/*.json`) | Check `catalogo_versionado` y `pipeline_unico` en auditoría |
| 4 | `cartera_credito` subestimada (sólo deudores comerciales) | El pipeline guarda **todas** las cuentas en formato largo y calcula el resumen con `mapeo_cuentas.json` v2 (deudores + arrendamiento financiero + colocaciones), exponiendo cada componente como columna | `cuentas_no_mapeadas.json` lista cuentas de crédito >5 % de activos sin mapear; check `cartera_sobre_activos_plausible` |
| 5 | Maestro inconsistente (cancelados con EEFF, filiales sin datos) | Catálogo corregido: Concreces, HLC, Interfactor, Mercantil → vigentes; campo `fuente_eeff_pipeline` = `cmf_ver_archivo` (24) / `pendiente_filial_bancaria` (4); chips del sidebar reescritos | Checks `cancelados_con_eeff_recientes`, `vigentes_sin_balance` |
| 6 | Auditoría de falsa seguridad | Reemplazada por v2 (32 checks, exit ≠ 0) | Workflow `.github/workflows/audit.yml` en push, PR y lunes semanal |
| 7 | Cuadre tautológico | Columna `patrimonio_origen` (`cmf` / `derivado_A_menos_P`); `cuadre_ok` explícito | Se reporta el conteo en cada corrida |
| 8 | TC fallback 900/850 y TLS desactivado | TC sólo desde `macro_divisas_mercado.parquet` (2014-01→2026-09); si falta, USD = NULL y `tc_fuente='faltante'`; TLS verificado por defecto (`--inseguro` opcional y logueado) | Check `tipo_cambio_sin_fallback` |
| 9 | Huecos/saltos sin documentar | Tabla `factoring_leasing_cobertura` generada en cada descarga | Checks `huecos_intermedios`, `saltos_qoq_activos_gt_60pct` (WARN informativo) |
| 10 | Nomenclatura | Se mantiene `rut` `NNNNNNNN-D`, `periodo` `YYYY-MM`, sufijo `_m_clp`/`_m_usd` como estándar a replicar en otros sectores | — |
| 11 | Textos del diccionario | Entradas eliminadas; columnas de trazabilidad documentadas en `data_dictionary.js` | — |

---

## 3. Operación periódica (cada trimestre)

CMF publica los EEFF ~60–90 días después del cierre. Calendario sugerido: **1 de marzo, junio,
septiembre y diciembre**.

```bash
# 1) Descarga sólo lo nuevo, regenera resumen y cobertura
python factoring_leasing/scripts/pipeline_factoring_leasing.py --step todo

# 2) Audita
python factoring_leasing/scripts/audit_factoring_leasing_v2.py

# 3) Revisa cuentas nuevas que no calzan con el mapeo (si hay)
cat factoring_leasing/data/cuentas_no_mapeadas.json

# 4) Commit de datos + catálogo/mapeo si cambiaron
git add docs/outputs/factoring_leasing factoring_leasing/data
git commit -m "data(factoring_leasing): EEFF 2026-06"
```

`--step todo` es incremental (`--solo-faltantes` implícito): sólo descarga trimestres que no están en el
formato largo. Para reprocesar un período (p. ej. CMF reexpresó cifras):

```bash
python factoring_leasing/scripts/pipeline_factoring_leasing.py --step descargar --desde 202512 --hasta 202512
python factoring_leasing/scripts/pipeline_factoring_leasing.py --step resumen
```

Otras opciones: `--step maestro` (sólo catálogo), `--fixture factoring_leasing/tests/fixture_cmf_202503.txt`
(prueba sin red), `--inseguro` (si CMF rompe su cadena TLS; queda en el log).

### Automatizar en GitHub Actions (opcional)

Añadir un job programado que ejecute `--step todo` y abra un PR con los cambios. No requiere
credenciales BCCh (el TC sale del parquet de macro). Ejemplo mínimo:

```yaml
- run: pip install -r requirements.txt
- run: python factoring_leasing/scripts/pipeline_factoring_leasing.py --step todo
- run: python factoring_leasing/scripts/audit_factoring_leasing_v2.py
- uses: peter-evans/create-pull-request@v6
  with: { title: "data(factoring_leasing): actualización trimestral", branch: "bot/factoring-leasing" }
```

---

## 4. Cómo mantener las fuentes de verdad

### 4.1 Catálogo (`data/catalogo_factoring_leasing.json`)
- Una entrada por sociedad. `rut` con módulo 11 (el pipeline aborta si no cuadra).
- `fuente_eeff_pipeline`: `cmf_ver_archivo` → el pipeline la busca en el archivo CMF de emisores;
  `pendiente_filial_bancaria` → no se busca (BCI Factoring, BICE Factoring, Scotia Azul Leasing,
  Bandesarrollo Leasing reportan bajo norma bancaria; ver §6).
- Para agregar una entidad nueva: añadir la entrada y correr `--step maestro` y luego `--step descargar --desde 201403`
  (el filtro por RUT es en la lectura, así que hay que releer los archivos históricos para incorporarla).
- `observaciones` es texto libre; anota ahí fusiones, cambios de RUT o razón social.

### 4.2 Mapeo de cuentas (`data/mapeo_cuentas.json`)
- Cada métrica tiene `exactas` (nombre completo) y `patrones` (regex sobre el nombre normalizado: minúsculas,
  sin acentos) y `excluir`.
- `cartera_credito` = suma de `cartera_credito_componentes`. Cada componente se publica como columna
  (`cartera_deudores_comerciales_m_clp`, `cartera_arrendamiento_financiero_m_clp`, `cartera_colocaciones_m_clp`)
  para que cualquier cambio de definición sea auditable.
- Al cambiar el mapeo, **subir `_meta.version`**: queda registrado en la columna `cartera_definicion` de cada fila.

### 4.3 Cuentas no mapeadas (`data/cuentas_no_mapeadas.json`)
Generado en cada `--step resumen`. Lista cuentas cuyo nombre sugiere cartera/crédito, no calzan con el mapeo y
superan el 5 % de activos de alguna entidad. Flujo: abrir el archivo → decidir si la cuenta es cartera →
añadirla a `exactas`/`patrones` → subir versión → `--step resumen`. En la primera corrida real es
**esperable** que aparezcan varias (nombres propios de cada emisor: "Colocaciones de leasing, neto",
"Créditos automotrices", etc.).

---

## 5. Contrato de datos del sector

| Tabla | Grano | Clave | Uso |
|---|---|---|---|
| `factoring_leasing_maestro` | entidad | `rut` | dimensión |
| `factoring_leasing_eeff_cuentas` | entidad × período × ind_cons × cuenta | (`rut`,`periodo`,`ind_cons`,`cuenta`) | **fuente**: cualquier análisis nuevo parte de aquí, no del resumen |
| `factoring_leasing_balance_resumen` | entidad × período | `id_balance` = `rut_YYYYMM` | vista derivada con mapeo versionado |
| `factoring_leasing_cobertura` | entidad × período | (`rut`,`periodo`) | qué falta y por qué |

Columnas de trazabilidad obligatorias en toda tabla publicada (la auditoría falla si faltan en el resumen):
`fuente_url`, `metodo`, `fecha_extraccion`, `script_version`.

Convenciones (a replicar en el resto del repo): `rut` = `NNNNNNNN-D` sin puntos; `periodo` = `YYYY-MM`;
montos en millones con sufijo `_m_clp` / `_m_usd`; USD siempre con `tc_usd_clp` y `tc_fuente`.

---

## 6. Pendientes que este arreglo deja explícitamente abiertos

1. **Primera corrida real** de `--step todo` (necesita red). Hasta entonces el resumen está marcado
   `script_version = 1.x-legacy` y `cartera_definicion = v1...`; la auditoría lo reporta como WARN.
2. **Filiales bancarias** (4): extraerlas desde "Información financiera de filiales bancarias" de CMF o desde
   el archivo de bancos (B1 consolidado no las separa). Mientras, quedan `pendiente_filial_bancaria`.
3. **Notas reales (efectivo, cartera por tramos, provisiones)**. Camino recomendado, en orden:
   1. **XBRL**: en la ficha CMF de cada emisor (`entidad.php?...&tipoentidad=RVEMI`, pestaña 3) hay
      "Estados financieros (XBRL)". Reutilizar `ccaf/scripts/pipeline_extract_ccaf_xbrl.py` como base;
      los desgloses de efectivo y deterioro suelen venir taggeados en la extensión del emisor.
   2. **PDF** con `pdfplumber`: localizar la nota por título, extraer tabla, y **reconciliar** contra la cuenta
      del formato largo (tolerancia 0,5 %); si no reconcilia, la fila no se publica.
   3. **Manual/LLM** (NotebookLM) siguiendo `pipelines/manual/`, etiquetado `metodo = manual`.
   Cualquiera de los tres debe emitir las mismas columnas de trazabilidad y pasar el check de participaciones
   rígidas de la auditoría v2.
4. `scripts/audit_web_full.py` falla por `outputs/vida/cartera_bonos.parquet` (git-ignorado, sector seguros);
   en CI está `continue-on-error`. Corregir la vista `vida_bonos` en `duckdb_client.js` y quitar el flag.
5. Añadir `factoring_leasing_eeff_cuentas` y `factoring_leasing_cobertura` a `sidebar.js`/`duckdb_client.js`
   **después** de la primera corrida (audit_web_full exige que el parquet exista).

---

## 7. Cómo replicar esto en otro sector (checklist)

- [ ] `grep -rn "PASS\|Siete(" sector/scripts` → mover a `mfc_common.credentials`.
- [ ] ¿Algún script multiplica un total por porcentajes fijos para "desglosar"? → despublicar y borrar.
- [ ] ¿Rutas `C:\...` o Excel externos? → catálogo JSON en `sector/data/` + un único pipeline.
- [ ] Guardar formato largo (todas las cuentas) antes de resumir; mapeo en JSON versionado.
- [ ] Columnas `fuente_url`, `metodo`, `fecha_extraccion`, `script_version` en toda tabla.
- [ ] TC sólo desde macro; sin defaults.
- [ ] Copiar `audit_factoring_leasing_v2.py`, adaptar nombres de tablas y agregarlo a `audit.yml`.

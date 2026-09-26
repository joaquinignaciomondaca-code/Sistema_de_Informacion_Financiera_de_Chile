# Auditoría — Securitizadoras y Patrimonios Separados — 2026-09-26

Alcance: `securitizadoras/scripts/*`, las 14 tablas de `docs/outputs/securitizadoras/`, y sus referencias en
`data_manifest.json` y `docs/js/*`. Método: lectura de código + consultas DuckDB. Reproducible con
`python securitizadoras/scripts/audit_patrimonios_separados_v2.py`.

Severidad: 🔴 bloqueante · 🟠 alta · 🟡 media · 🟢 baja.

---

## Resumen ejecutivo

El sector tiene dos partes muy distintas:

- **Sociedades securitizadoras (gestoras)**: `securitizadoras_maestro` (16) y `securitizadoras_balance_resumen`
  (362 filas, 2014-03→2026-06). Reproducibles con `stream_cmf_securitizadoras.py`, RUT válidos, cuadre 100 %.
  **Aceptable**, con observaciones menores.
- **Patrimonios separados (PS)**: 12 tablas, 50.812 filas. **8 de ellas no tienen script que las produzca** en el
  repo, y las 4 restantes salen de un parser heurístico de PDF (`03_extract_patrimonios_separados_series.py`) que
  rellena con valores por defecto lo que no encuentra. La calidad de datos es baja en casi todas
  (RUT truncados, claves inestables, cuadres que no cuadran, placeholders al 100 %). Los dos scripts de auditoría
  existentes **ya fallan** y aun así las tablas están publicadas como "Automático / CMF".

| # | Hallazgo | Sev. |
|---|----------|------|
| 1 | 8 tablas de PS (balance_lineas, excedentes_lineas, nota_efectivo, nota_bonos, nota_cartera, nota_administracion, nota_sobrecolateral, nota_morosidad; 49.868 filas) **sin script generador** en el repo → irreproducibles y sin procedencia | 🔴 |
| 2 | Placeholders al 100 %: `nota_bonos` (8.001/8.001 con `fecha_vencimiento = fecha del período` y `monto_colocado = saldo_insoluto`), `nota_sobrecolateral` (679/679 con activos = pasivos = 0 pero `sobrecolateral_pct` hasta 98 %), `repos_detalle` (52/52 con plazo 0, tasa por defecto, una sola contraparte, `"Cumple / SI"` hardcodeado) | 🔴 |
| 3 | RUT de administradora **truncado** en 11 de 11 administradoras en 9 tablas (`9676517-0` en vez de `96765170-2`): se perdió el último dígito y se recalculó el DV sobre el cuerpo mutilado | 🔴 |
| 4 | Clave `id_patrimonio` inestable: 573 ids distintos en `balance_lineas` para ≈ 60 PS reales (el mismo PS aparece como `TRANSA_BTRA12`, `TRANSA_Patrimonio_Separado_BTRA12`, `TRANSA_TRANSA_BTRA12`); `balance_resumen` usa otro esquema (`76965774_bvols`) con **0 ids en común**; el maestro usa `numero_inscripcion` y no cruza con ninguna | 🔴 |
| 5 | `balance_lineas`: sólo 330 de 1.308 balances (25 %) cuadran A = PC + PLP + Patrimonio (±1 %); 41 sin `TOTAL ACTIVOS`; 20 con activos = 0 | 🟠 |
| 6 | `nota_morosidad`: 27 variantes textuales de tramo (`1 A 6`, `1A6`, `1 - 6`, `1   A   6`, `Totales` como tramo…), `porcentaje_provision_pct` hasta 224.067.833 % (columnas desplazadas). `cartera_morosidad_detalle`: 27/67 filas con provisión > 100 % | 🟠 |
| 7 | `03_extract_patrimonios_separados_series.py` **inventa** valores cuando no parsea: `tasa = 0.39`, `plazo_dias = 30`, `emisor = "Banco Central de Chile"`, `instrumento = "Deuda Soberana / BCCH"`, fechas sintéticas, `"Cumple / SI"`; fallbacks de TC hardcodeados; `ssl.CERT_NONE` | 🟠 |
| 8 | Las auditorías existentes (`04_audit_…`, `audit_securitizadoras.py`) fallan (RUT inválidos, columna `numero_nota` ausente) → la tabla publicada de efectivo **no fue generada por el script del repo**; nadie bloqueó la publicación | 🟠 |
| 9 | `securitizadoras_balance_resumen.ganancia_perdida_ejercicio_m_clp` = 0 en 362/362 filas (columna vacía publicada como métrica); `rut` sin DV | 🟡 |
| 10 | Formatos mixtos: `periodo` `201003` (8 tablas) vs `2024-12` (4 tablas); sufijos `_mclp`, `_m_clp`, `_mm_clp`, `_mmclp`, `_musd` en el mismo sector | 🟡 |
| 11 | Cobertura irregular en `balance_lineas`: 2013 con 3 trimestres, 2014 con 1; PS por año cae de 92 (2015) a 7 (2026-03) sin tabla de cobertura que explique si es real (PS liquidados) o fallo de descarga | 🟡 |
| 12 | Maestro de PS: 18 líneas/emisiones de 5 administradoras; no cubre las 11 administradoras con balances históricos ni tiene el número de inscripción de cada PS individual | 🟡 |

Lo que **sí** está bien: `securitizadoras_maestro` (16 RUT válidos, vigencia, URL CMF), `securitizadoras_balance_resumen`
(cuadre 100 %, 49 trimestres, TC por período), y la **estructura** de `balance_lineas`/`excedentes_lineas`: usa el plan de
cuentas real de la FECU de Patrimonios Separados (10.000 TOTAL ACTIVOS … 23.000 TOTAL PATRIMONIO/EXCEDENTES, códigos
11.010, 13.140, 21.070, 22.030…). Eso indica que la **fuente estructurada existe** y es el camino para reconstruir el
sector con calidad.

---

## Evidencia

### 1. Tablas huérfanas
```
grep -rln "balance_lineas|excedentes_lineas|nota_bonos_detalle|nota_sobrecolateral|nota_administracion_detalle|nota_cartera_detalle|nota_morosidad_detalle" --include=*.py .
→ (vacío)
```
Además el esquema publicado de `nota_efectivo_detalle` (`id_linea, institucion, tipo_instrumento, saldo_mclp, saldo_mmclp`)
no coincide con el que escribe `03_extract…` (`numero_nota, concepto_item, tipo_activo, monto_mclp, monto_musd`).

### 2. Placeholders
| Tabla | Check | Resultado |
|---|---|---|
| nota_bonos_detalle | `fecha_vencimiento = fecha` | 8.001 / 8.001 |
| nota_bonos_detalle | `monto_colocado = saldo_insoluto` | 8.001 / 8.001 |
| nota_sobrecolateral_detalle | `valor_activos = 0 AND valor_pasivos_bonos = 0` | 679 / 679 (pct 0 – 98,31) |
| repos_detalle | `plazo_dias = 0` / tasa ∈ {0, 0.39} / contrapartes distintas / `Cumple / SI` | 52/52 · 52/52 · 1 · 52/52 |

### 3. RUT truncados
`balance_lineas`, `excedentes_lineas`, `nota_*` (8 tablas) y `repos_detalle`: `9676517-0` (TRANSA; real `96765170-2`),
`9681930-0` (BICE; real `96819300-7`), `9678559-0` (Santander; real `96785590-1`)… 11/11 inválidos por módulo 11.

### 4. Claves
```
ids por administradora en balance_lineas: SECURITY 198, BANCHILE 124, SANTANDER 80, BICE 47, BCI 44 … (total 573)
∩ id_patrimonio (balance_lineas, balance_resumen) = 0
maestro: clave numero_inscripcion (línea/emisión), 5 administradoras; balance_lineas: 11 administradoras
```

### 5–6. Cuadre y morosidad
```
balance_lineas (id, periodo): 1.308 balances · cuadran ±1 %: 330 · sin 10.000: 41 · activos = 0: 20
nota_morosidad tramo_mora: 'Total' 2.239 · 'Totales' 1.943 · '1   A   6' 715 · 'Al   Día' 429 · … 27 variantes
max(porcentaje_provision_pct) = 224.067.833,33
```

### 7. Defaults inventados (`03_extract…`, líneas ~430-455)
```python
"instrumento_pacto": instr if instr else "Instrumento de Deuda Soberana / BCCH",
"emisor_subyacente": emisor if emisor else "Banco Central de Chile",
"fecha_inicio": fechas[0] if len(fechas) > 0 else f"{year}-12-30",
"plazo_dias": 30,
"tasa_interes_anual_pct": tasa if tasa > 0 else 0.39,
"cumplimiento_calificacion": "Cumple / SI"
```

---

## Plan de arreglo (en orden)

1. **Despublicar** las 8 tablas huérfanas + `repos_detalle` + `cartera_morosidad_detalle` + `nota_efectivo_detalle`
   (datos, manifest, sidebar, ERD, diccionario, data_viewer, duckdb_client, export_modal). Conservar sólo
   `securitizadoras_maestro`, `securitizadoras_balance_resumen`, `patrimonios_separados_maestro` y
   `patrimonios_separados_balance_resumen` (este último con la advertencia de que cubre 27 PS × 2022-2024).
2. **Modelo de entidad correcto**: el PS se identifica por su **número de inscripción en el Registro de Valores**
   (y su nemotécnico de bonos), no por un slug del nombre del PDF. Construir `patrimonios_separados_maestro` con una
   fila por PS (no por línea de la administradora), con `rut_administradora` completo (NNNNNNNN-D), `nro_inscripcion`,
   `denominacion`, `nemotecnicos`, `fecha_inscripcion`, `estado`.
3. **Pipeline único reproducible** (`pipeline_patrimonios_separados.py`), mismo patrón que factoring:
   catálogo JSON versionado → descarga → **formato largo** de cuentas FECU-PS (código, nombre, valor, fuente_url) →
   resumen con mapeo JSON versionado → tabla de cobertura. Sin defaults: lo que no se extrae es NULL y se reporta.
   Fuente a evaluar primero: el mismo `ver_archivo.php`/estadísticas de CMF para PS (los códigos 10.000–23.000 de
   `balance_lineas` sugieren que ya se parseó algo estructurado); segundo, XBRL/PDF de `entidad.php?…&pestania=18`.
4. **Notas** (bonos, morosidad, sobrecolateral, administración): sólo con reconciliación contra el formato largo
   (p. ej. suma de `saldo_insoluto` por PS = 21.010 + 22.010 ± 0,5 %) y columnas de procedencia. Normalizar tramos de
   mora a un catálogo cerrado.
5. **Auditoría v2** (adjunta) en CI; retirar `04_audit…` y `audit_securitizadoras.py`.
6. Homogeneizar: `periodo` `YYYY-MM`, `rut` con DV, sufijos `_m_clp`/`_m_usd`; rellenar o eliminar
   `ganancia_perdida_ejercicio_m_clp` en el resumen de gestoras.

---

## Resultado del script de auditoría (ejecución 2026-09-26)

`python securitizadoras/scripts/audit_patrimonios_separados_v2.py` → **16 FAIL · 6 WARN · 6 PASS/INFO, exit 1**.
FAIL: tablas sin script generador (8/14), defaults inventados en parser, RUT inválidos/sin DV, 2 formatos de
periodo, cardinalidad de `id_patrimonio` (573), 0 ids en común resumen/lineas, placeholders 100 % en
nota_bonos (×2), sobrecolateral, repos, `ganancia_perdida_ejercicio` = 0 en 362/362, participaciones rígidas en
nota_administracion y nota_morosidad, 27 variantes de tramo de mora, cuadre 330/1.308, y 14/14 tablas sin columnas
de procedencia. El script debe quedar en 0 FAIL al cierre de la fase de arreglos.

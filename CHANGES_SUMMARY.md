# Resumen de Cambios - Automatización Financiera

## Mejoras Implementadas en TODOS los Workflows

### 1. Frecuencia Aumentada

**Antes**: 3 veces al mes (días específicos)  
**Ahora**: **Cada 3 días** (`*/3` en cron)

Esto aplica a todos los workflows que descargan datos históricos:
- bancos_cmf_mensual
- corredoras_eeff
- factoring_leasing_backfill
- ffmm_carteras
- ffmm_eeff
- fi_carteras
- fi_eeff
- ifrs_sectores
- seguros_carteras

### 2. Hilos Aumentados

**GitHub Actions specs (repositorios públicos)**:
- 4 vCPU, 16 GB RAM
- Cuello de botella: latencia de red (CMF), no CPU

| Script | Antes | Ahora |
|---|---|---|
| FI Carteras | 12 | 16 (máx 32) |
| FI EEFF | 4 | 16 (máx 32) |
| FFMM EEFF | 4 | 16 (máx 32) |

Los hilos controlan descargas HTTP simultáneas.

### 3. Inputs Workflow Dispatch Completos

Todos los workflows ahora aceptan inputs manuales:

| Input | Descripción |
|---|---|
| `desde` | Primer período/mes (AAAA-MM o AAAA); vacío = autodescubre |
| `hasta` | Último período/mes; vacío = último admisible |
| `minutos` | Tiempo máximo de la corrida (default 270 min) |
| `max_periodos` | Máximo de cierres a revisar (0 = sin tope) |
| `hilos` | Descargas simultáneas (default 16) |

### 4. Autodescubrimiento del Año Más Antiguo (FI)

Ambos scripts de Fondos de Inversión ahora detectan automáticamente hasta qué año hay datos disponibles en la CMF:

- **FI Carteras**: Prueba todos los fondos del registro (~1,679 fondos) trimestre por trimestre, caminando hacia atrás desde 2020-03 hasta encontrar el límite histórico (o hasta 2015).
- **FI EEFF**: Similar, pero con XML FIEF, caminando hacia atrás desde 2010-12 hasta 2008.

**Comportamiento**:
- Si pasas `--desde YYYY-MM` explícitamente → usa ese valor (no sondea la CMF)
- Si ya hay datos publicados → usa el trimestre más antiguo ya publicado
- Si es la primera corrida → **autodescubre** probando todos los fondos

### 5. Lógica de Huecos Inteligentes (FI)

**Problema resuelto**: Si un trimestre (ej: 2015-03) se procesa sin encontrar datos, y la CMF luego completa esa información, el script NO lo reprocesaba porque ya estaba marcado como "sondeado sin datos".

**Solución**: Reintentar TODOS los `sondeados_sin_datos`, sin importar su posición temporal. La única excepción son los ya publicados (que sí tienen datos válidos).

| Situación | ¿Se reintentará? |
|-----------|------------------|
| Trimestre ya publicado | ❌ NO (tiene datos válidos) |
| Trimestre sondeado sin datos (cualquier fecha) | ✅ SÍ (la CMF puede completar data) |

**Ejemplo**:
```
Periodos publicados: 2010-12 a 2026-06
Sondeados sin datos: 2009-06, 2015-03, 2026-09

Próxima corrida:
- 2010-12 a 2026-06: NO se reintentan (ya publicados)
- 2009-06: SE REINTENTA (por si CMF completó data)
- 2015-03: SE REINTENTA (por si CMF completó data)
- 2026-09: SE REINTENTA (por si CMF subió data nueva)
```

El costo es bajo (detectar que un trimestre sigue sin datos es rápido) y nos protege de perder correcciones de la CMF.

### 6. Parámetro `max_periodos=0` = Sin Tope

En todos los scripts, `--max-periodos 0` ahora significa procesar sin límite, en lugar de procesar 0 períodos.

## Archivos Modificados

### Workflows (9 archivos)
- `.github/workflows/bancos_cmf_mensual.yml`
- `.github/workflows/corredoras_eeff.yml`
- `.github/workflows/factoring_leasing_backfill.yml`
- `.github/workflows/ffmm_carteras.yml`
- `.github/workflows/ffmm_eeff.yml`
- `.github/workflows/fi_carteras.yml`
- `.github/workflows/fi_eeff.yml`
- `.github/workflows/ifrs_sectores.yml`
- `.github/workflows/seguros_carteras.yml`

### Scripts (9 archivos)
- `bancos/scripts/publish_cmf_bank_period.py`: agregado `--hasta`, `--max-periods 0` sin tope
- `corredoras_bolsa/scripts/actualizar_eeff.py`: agregado `--desde`, `--hasta`, `--max-periodos 0` sin tope, `--minutos`
- `factoring_leasing/scripts/backfill_ifrs.py`: `--batch 0` sin tope
- `ffmm/scripts/actualizar_carteras.py`: agregado `--desde`, `--minutos`, `--max-periodos 0` sin tope
- `ffmm/scripts/actualizar_eeff.py`: `--hilos` default 16
- `fi/scripts/actualizar_carteras.py`: autodescubrimiento, huecos inteligentes, `--desde`, `--hilos`, `--max-periodos 0` sin tope
- `fi/scripts/actualizar_eeff.py`: autodescubrimiento, huecos inteligentes, `--hilos` default 16
- `pipelines/ifrs_sectores/actualizar.py`: agregado `--desde`, `--hasta`, `--max-periodos 0` sin tope, `--minutos` default 270
- `seguros/scripts/actualizar_carteras.py`: agregado `--minutos`, `--max-periodos 0` sin tope

## Persistencia (FI)

- **FI Carteras**: `sondeados_sin_datos` se guarda en `docs/outputs/fi/manifest.json`
- **FI EEFF**: `sondeados_sin_datos` se guarda en `docs/outputs/fi/fi_eeff_control.json`

Estos campos contienen listas de trimestres (formato `YYYY-MM`) que fueron sondeados sin encontrar datos.

## Pruebas

Todas las pruebas pasan:
- FI: 97 tests ✅
- Corredoras: 19 tests ✅
- FFMM: 78 tests ✅
- Seguros: 0 tests (no hay tests definidos) ✅
- Factoring/Leasing: 59 tests ✅
- IFRS Sectores: 35 tests ✅
- Bancos: OK ✅

## Ejemplo de Uso

### Primera Corrida (Backfill Completo)

Desde GitHub Actions → "Run workflow":

**FI Carteras**:
- `desde`: (vacío) → autodescubre automáticamente
- `max_periodos`: 0 → sin límite
- `hilos`: 16

**FI EEFF**:
- `desde`: (vacío) → autodescubre automáticamente
- `max_periodos`: 0 → sin límite
- `hilos`: 16

**Cualquier otro sector**:
- `desde`: (vacío) → primer período pendiente
- `max_periodos`: 0 → sin límite
- `minutos`: 270

### Corridas Subsecuentes

El script detecta automáticamente qué períodos faltan y cuáles deben reintentarse. No necesitas pasar parámetros especiales.

## Consideraciones de Performance

- **Autodescubrimiento FI**: ~1-2 horas para sondear 20-30 trimestres con 1,679 fondos y 16 hilos
- **Corridas normales**: 3-5 minutos por trimestre (FI) o por mes (otros sectores)
- **Reintentos (FI)**: solo los huecos posteriores al último dato publicado (típicamente 1-3 trimestres)

## Ejemplo de Log (FI Carteras)

```
Descubriendo primer trimestre disponible con 1679 fondos del registro...
  2019-12: 524/1679 fondos con datos ✓
  2019-09: 498/1679 fondos con datos ✓
  2019-06: 487/1679 fondos con datos ✓
  2019-03: 475/1679 fondos con datos ✓
  2018-12: 460/1679 fondos con datos ✓
  2018-09: 0/1679 fondos con datos
  2018-06: 0/1679 fondos con datos
  Dos trimestres consecutivos sin datos. Límite detectado.
→ Primer trimestre disponible: 2018-12
→ Trimestres sondeados sin datos: 2

Trimestres publicados: 0. A procesar: 7 (0 reintentables).
2026-06: 1679 fondos consultados (11753 páginas, 245 s), 908 con cartera · ...
...
```

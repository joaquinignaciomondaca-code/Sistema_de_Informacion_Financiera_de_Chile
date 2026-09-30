# Pipelines Híbridos y Extracción Asistida (NotebookLM / LLM)

El lector automático de PDF de factoring (`pipelines/eeff`) se retiró. Las notas que se quieran publicar entran por este flujo: la extracción inicial puede requerir intervención humana o asistencia de IA, pero la ingesta, validación y compilación posterior se ejecutan mediante código reproducible.

El balance de patrimonios separados parte de un Excel curado localmente a partir de la lectura de los PDF de estados financieros publicados en la CMF (`securitizadoras/fuentes/balances_patrimonios_separados.xlsx`). Lo valida y publica `securitizadoras/scripts/05_publicar_balance_patrimonios.py` en `patrimonios_separados_balance`.

Este directorio gestiona flujos de extracción y normalización de información que **requieren intervención humana previa o procesamiento asistido por IA**, tales como el análisis de notas explicativas en memorias anuales y estados financieros en PDF. La etiqueta híbrido se refiere precisamente a esa separación: la extracción inicial no está orquestada en Actions, mientras que la transformación posterior sí queda versionada y repetible.

---

## 1. ¿Por qué existen pipelines híbridos?
A diferencia de las carteras de inversión estandarizadas por circulares CMF (Circular 1835 o 1333) que vienen en archivos tabulares directos:
- Las **Notas a los Estados Financieros** de empresas, fondos mutuos, bancos y retail financiero residen en documentos PDF no estructurados con formatos variables por emisor.
- Para extraer información granular (desagregados de comisiones, detalle de juicios pendientes, desglose de financiamiento por tramos de vencimiento o covenants) se utiliza **NotebookLM** o LLMs multimodales para parsear los PDFs y estructurarlos en JSON tabular.

---

## 2. Flujo Operativo Paso a Paso (SOP)

```
[1. PDF de Memoria / EEFF]
           │
           ▼
[2. Carga en NotebookLM] ──► Extracción con Prompts Estandarizados
           │
           ▼
[3. JSON Tabular Validado] ──► Guardar en `pipelines/manual/input_data/`
           │
           ▼
[4. Ingesta Automática] ────► Ejecutar `python pipelines/manual/ingest_manual_notes.py`
           │
           ▼
[5. Parquet Final en Web] ──► Actualización en `docs/outputs/` con etiqueta "Híbrido" cuando la compilación posterior sea reproducible
```

### Paso 1: Obtención del Archivo PDF
Descargar el Estado Financiero o Memoria Anual correspondiente desde el portal de la CMF o sitio oficial de la entidad.

### Paso 2: Extracción con NotebookLM
Subir el documento PDF a NotebookLM y ejecutar el prompt maestro de extracción correspondiente según la industria (ej. Fondos Mutuos, Retail, Banca).
El formato de respuesta debe apegarse estrictamente a la plantilla canónica: `pipelines/manual/templates/ejemplo_notas_eeff.json`.

### Paso 3: Guardar el Resultado
Almacenar el archivo generado en:
`pipelines/manual/input_data/[sector]_[entidad]_[periodo].json`

### Paso 4: Ingesta y normalización
Ejecutar el script compilador:
```bash
python pipelines/manual/ingest_manual_notes.py
```
El script realiza:
1. Lectura del JSON canónico y conservación de la fuente, operador y fecha de extracción.
2. Comprobación del RUT bajo Módulo 11, con advertencia si no coincide.
3. Aplanado de `tabla_desagregada` y escritura de un Parquet normalizado en `docs/outputs/notas_eeff/`.
4. No extrae el PDF ni certifica por sí solo la cuadratura contable: esos controles deben ejecutarse antes o mediante un auditor sectorial. Al incorporar el resultado al catálogo web se declara `"modo": "Híbrido"` cuando la extracción inicial fue asistida y la compilación posterior es reproducible.

---

## 3. Formatos y Estándares de Extracción

### A. Estándar Tabular Plano Delimitado por Pipe (`|`)
Para la extracción de notas específicas y desglose de balances en NotebookLM/LLMs, se utiliza texto plano con separador **`|` (pipe)**. Este formato:
- Reduce drásticamente el consumo de caracteres y tokens frente a JSON anidado.
- Evita colisiones con comas decimales chilenas (`0,44%`), puntos de miles (`4.700.000`) o razones sociales (`BCI C.B. S.A.`).
- Permite esquemas con columnas naturales dedicadas para cada tipo de nota.

### B. Módulos Implementados
- **Cajas de Compensación (CCAF)**: Ver guía completa, universo de entidades y columnas de las 7 tablas en [`ccaf/README.md`](../../ccaf/README.md).
  - Tabla 1: Carátula y Balance Resumen
  - Tabla 2: Nota 8 - Efectivo y Equivalentes (Resumen General)
  - Tabla 3: Nota 8 (c) - Desglose de Depósitos a Plazo (DAP)
  - Tabla 4: Nota 8 (d) - Repos / Pactos de Retroventa
  - Tabla 5: Crédito Social (Notas 9, 10 y 20)
  - Tabla 6: Mutuos Hipotecarios Endosables (Notas 11 y 22)
  - Tabla 7: Instrumentos Financieros y Derivados (Nota 13)

### C. Plantillas Legacy JSON
- `templates/ejemplo_notas_eeff.json`: Estructura general de notas explicativas y desgloses analíticos en JSON (en desuso en favor del formato pipe `|`).


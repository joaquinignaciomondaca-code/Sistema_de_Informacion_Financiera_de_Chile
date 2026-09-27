# Pipelines Manuales y Extracción Asistida (NotebookLM / LLM)

El lector automático de PDF de factoring (`pipelines/eeff`) se retiró. Las notas que se quieran publicar entran por este flujo.

El balance de patrimonios separados leído del PDF está en `patrimonios_separados_balance_pdf`. El Excel no se guarda.

Este directorio gestiona los flujos de extracción y normalización de información que **requieren intervención humana previa o procesamiento asistido por IA**, tales como el análisis de notas explicativas en memorias anuales y estados financieros en PDF.

---

## 1. ¿Por qué existen pipelines manuales?
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
[5. Parquet Final en Web] ──► Actualización en `docs/outputs/` con etiqueta "Manual"
```

### Paso 1: Obtención del Archivo PDF
Descargar el Estado Financiero o Memoria Anual correspondiente desde el portal de la CMF o sitio oficial de la entidad.

### Paso 2: Extracción con NotebookLM
Subir el documento PDF a NotebookLM y ejecutar el prompt maestro de extracción correspondiente según la industria (ej. Fondos Mutuos, Retail, Banca).
El formato de respuesta debe apegarse estrictamente a la plantilla canónica: `pipelines/manual/templates/ejemplo_notas_eeff.json`.

### Paso 3: Guardar el Resultado
Almacenar el archivo generado en:
`pipelines/manual/input_data/[sector]_[entidad]_[periodo].json`

### Paso 4: Ingesta y Validación Matemática
Ejecutar el script compilador:
```bash
python pipelines/manual/ingest_manual_notes.py
```
El script realiza:
1. Validación de RUTs (Módulo 11).
2. Verificación de campos obligatorios y tipos de datos.
3. Cuadratura contable de subtotales vs totales declarados.
4. Generación y publicación del archivo Parquet en `docs/outputs/` con metadato `"modo": "Manual"`.

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


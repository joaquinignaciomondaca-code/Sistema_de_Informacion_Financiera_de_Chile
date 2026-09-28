# Módulo Cajas de Compensación de Asignación Familiar (CCAF)

> **Estado al 2026-09-28:** en la web quedan solo `ccaf_maestro` (lista de entidades) y `ccaf_caratula_totales`
> (72 balances, 2019-12 a 2026-06), extraído por `scripts/pipeline_extract_ccaf_xbrl.py` desde el **XBRL oficial de la CMF**.
> Se retiraron Nota 8 (efectivo, DAP, repos) y colocaciones de crédito social, y se borraron
> `build_ccaf_repos_enriquecido.py` y `scripts/legacy/`. Las secciones de abajo describen el trabajo histórico.

## 1. Alcance Normativo y Universo de Entidades
Las Cajas de Compensación de Asignación Familiar (CCAF) están reguladas primariamente por la **Superintendencia de Seguridad Social (SUSESO)** bajo la Ley N° 18.833, y secundariamente por la **Comisión para el Mercado Financiero (CMF)** en su calidad de emisores de bonos y efectos de comercio de oferta pública.

El universo del sistema financiero chileno comprende:
- **4 entidades vigentes**:
  1. **CCAF Los Andes** (RUT: 81.826.800-9 | Código CMF: 1009)
  2. **CCAF La Araucana** (RUT: 70.016.160-5 | Código CMF: 2574)
  3. **CCAF Los Héroes** (RUT: 70.016.330-1 | Código CMF: 1011)
  4. **CCAF 18 de Septiembre / Caja 18** (RUT: 82.606.800-K | Supervisión SUSESO)
- **2 entidades absorbidas**:
  5. **CCAF Gabriela Mistral** (absorbida por La Araucana)
  6. **CCAF Javiera Carrera** (absorbida por Los Héroes)

---

## 2. Fuentes Oficiales de Información
- **Carátulas y Balances en Línea**: CMF Chile (https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&pestania=3).
  - Los Andes, La Araucana y Los Héroes informan bajo consolidado y en periodos intermedios bajo individual.
  - Caja 18 informa bajo alcance individual al no mantener filiales consolidadas.
- **Memorias y Estados Financieros Auditados Completos en PDF**: SUSESO (https://www.suseso.cl/609/w3-propertyvalue-10337.html), con informes independientes de firmas auditoras (KPMG, EY, PwC, Deloitte).

---

## 3. Principio de Higiene Efímera de Disco (Automatización Segura)
Para garantizar la viabilidad en entornos de integración continua, servidores y procesos desatendidos, todos los scripts de descarga y procesamiento operan bajo el principio de **cero residuos en disco**:

`python
try:
    # 1. Descarga del PDF oficial a ruta temporal
    urllib.request.urlretrieve(url, temp_pdf)
    doc = fitz.open(temp_pdf)
    # 2. Extracción focalizada de páginas contables
    ...
finally:
    # 3. Cierre de descriptores de archivo y borrado inmediato
    if 'doc' in locals() and doc:
        doc.close()
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)
`

**Resultado de higiene**: 0 bytes residuales de archivos PDF en disco en todo momento.

---

## 4. Arquitectura Modular de Scripts (ccaf/scripts/)

El módulo cuenta con scripts especializados y desacoplados:

1. **uild_ccaf_maestro.py**:
   - Genera el catálogo maestro oficial de las 6 CCAF (docs/outputs/cajas_compensacion/ccaf_maestro.parquet y .json).
   - Valida 100% de los RUTs bajo algoritmo Módulo 11.

2. **uild_ccaf_caratula_totales.py**:
   - Serie histórica completa de 15 años (2010 a septiembre 2025): **266 balances**.
   - Asientos contables estándar: Activo Total (10000), Pasivo Total (20000), Patrimonio Total (23000) y Utilidad Neta (23050).
   - Incorpora la columna 	ipo_eeff (Consolidado vs Individual).
   - Fallback de OCR nativo (winocr a 200 DPI) para memorias históricas escaneadas.
   - Verificación matemática obligatoria: Activo Total = Pasivo Total + Patrimonio Total con 0.00 de discrepancia.

3. **extract_ccaf_nota8_efectivo.py**:
   - Extracción de componentes puros de liquidez de la Nota 8 (Efectivo y Equivalentes al Efectivo) para 2012–2024: **189 registros**.
   - **Exclusión estricta de la fila de Total general**: Extrae únicamente Caja, Bancos, Depósitos a plazo y Otro efectivo y equivalentes (Repos/Pactos) para evitar doble contabilización en agregaciones SQL.
   - Incorpora la columna 	ipo_eeff (Consolidado vs Individual).
   - Consumo de tokens: **0 tokens** (algoritmo local determinístico con PyMuPDF).

4. **udit_ccaf.py**:
   - Auditor de consistencia profunda: valida integridad referencial de RUTs, paridad Parquet/JSON, balance contable de carátula (A = P + Pat), suma de componentes de Nota 8 vs total impreso en PDF, y ausencia de archivos residuales en disco.

5. **legacy/**:
   - Carpeta de archivo para prototipos exploratorios iniciales (pipeline_extract_ccaf_phase1.py, stream_mass_ccaf_eeff.py).

---

## 5. Datasets Generados en docs/outputs/cajas_compensacion/

| Tabla | Formato | Registros | Cobertura Temporal | Descripción |
|---|---|---|---|---|
| ccaf_maestro | Parquet / JSON | 6 entidades | Vigente 2026 | Catálogo institucional, Razón Social, RUT, reguladores y líneas de deuda CMF |
| ccaf_caratula_totales | Parquet / JSON | 266 balances | 2010 – 2025 (15 años) | Cifras de carátula auditadas IFRS (Activo, Pasivo, Patrimonio, Utilidad) con 	ipo_eeff |
| ccaf_nota8_efectivo_resumen | Parquet / JSON | 189 componentes | 2012 – 2024 | Desglose puro de liquidez (Caja, Bancos, DAP, Repos) sin fila Total |
| ccaf_nota8_dap_detalle | Parquet / JSON | 52 depósitos | 2017 – 2024 | Detalle analítico por plazo en días, tasas y montos devengados |
| ccaf_nota8_repos_detalle | Parquet / JSON | 100 pactos | 2017 – 2024 | Detalle contrato por contrato con corredoras de bolsa en pactos de retroventa |

---

## 6. Ejecución y Auditoría

Para ejecutar el ciclo de auditoría completo del sector CCAF:
`ash
python ccaf/scripts/audit_ccaf.py
`

Para verificar la integración con la plataforma web interactiva:
`ash
python scripts/audit_web_full.py
`

---

## 7. Roadmap de Próximas Notas Contables
- **Notas 9 y 10 (Crédito Social)**: Colocaciones brutas por segmento (Trabajadores vs Pensionados), deudores previsionales, provisiones por incobrabilidad y castigos de cartera.
- **Notas 11 y 22 (Mutuos Hipotecarios Endosables)**: Cartera de mutuos hipotecarios residenciales otorgados a afiliados.
- **Nota 13 (Instrumentos Financieros Derivados)**: Posición en Cross Currency Swaps para cobertura contable de emisiones de bonos en UF y financiamiento.

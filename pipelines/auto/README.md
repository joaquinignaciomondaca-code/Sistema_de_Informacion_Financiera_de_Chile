# Pipelines Automáticos (ETL / Autonomous Scrapers)

Este directorio cataloga y documenta los flujos de extracción y procesamiento que se ejecutan **100% de manera autónoma por código**, sin requerir intervención manual ni descargas asistidas.

---

## 1. Principio Metodológico
- **Autonomía**: Cada script se conecta a un endpoint público, API REST/SOAP o repositorio de archivos estructurados (CSV, TXT, XML, ZIP de CMF/BCCh/SPensiones) y genera tablas Parquet normalizadas.
- **Reproducibilidad**: Se pueden programar mediante cron jobs o GitHub Actions con variables de entorno estándar.
- **Validación Automática**: Todos los pipelines aplican control de tipos, validación de RUTs (Módulo 11) y cuadratura contable.

---

## 2. Inventario de Sectores y Pipelines Autónomos

| Sector / Cobertura | Archivo de Origen | Frecuencia | Script Principal | Salida Canónica |
| :--- | :--- | :--- | :--- | :--- |
| **Compañías de Seguros (Vida y Generales)** | CMF Circular 1835 (Cartera e Inversiones) | Trimestral | `seguros/circular_1835_cartera/scripts/orchestrate_seguros.py` | `docs/outputs/vida/`, `docs/outputs/generales/` |
| **Fondos Mutuos** | CMF Circular 1333 (Derivados y Futuros) | Mensual | `ffmm/circular_1333_cartera/scripts/process_circular_1333.py` | `docs/ffmm/circular_1333_cartera/outputs/` |
| **Fondos de Inversión** | CMF Circular 1835 (Activos y Repos) | Trimestral / Mensual | `fi/cartera_inversiones/scripts/process_fi.py` | `docs/fi/cartera_inversiones/outputs/` |
| **Fondos de Pensiones** | SPensiones (Archivos ZIP históricos y mensuales) | Mensual | `pensiones/scripts/pipeline_stream_history.py` | `docs/outputs/pensiones/` |
| **Banca Comercial** | CMF Balances y BCCh Derivados F099 | Mensual | `bancos/scripts/process_bancos.py` | `docs/outputs/bancos/` |
| **Macroeconomía & Tasas** | BCCh (Base de Datos Estadísticos SIETE) | Mensual / Diario | `macro/scripts/pipeline_stream_macro_bcch.py` | `docs/outputs/macro/` |
| **Factoring & Leasing** | CMF EEFF IFRS texto plano (`ver_archivo.php`) | Trimestral | `factoring_leasing/scripts/pipeline_factoring_leasing.py --step todo` (catálogo y mapeo de cuentas versionados en `factoring_leasing/data/`) | `docs/outputs/factoring_leasing/` (maestro, eeff_cuentas [largo], balance_resumen, cobertura) |
| **Corredoras de Bolsa** | CMF Estados Financieros IFRS | Trimestral | `corredoras_bolsa/scripts/stream_cmf_corredoras.py` | `docs/outputs/corredoras_bolsa/` |
| **Sociedades Securitizadoras** | CMF Balances IFRS y Ley 18.045 | Trimestral | `securitizadoras/scripts/pipeline_securitizadoras.py` | `docs/outputs/securitizadoras/` |
| **Cajas de Compensación** | SUSESO / CMF Registro Oficial | Anual / Trimestral | `cajas_compensacion/scripts/stream_ccaf.py` | `docs/outputs/cajas_compensacion/` |
| **Administradoras de Fondos (AGF)** | CMF Ley 20.712 Balances IFRS | Trimestral | `agf/scripts/stream_cmf_agf.py` | `docs/outputs/agf/` |
| **Sistemas de Pago** | BCCh Tráfico LBTR/CCA y Balances CMF | Mensual / Trimestral | `sistemas_pago/scripts/stream_sistemas_pago.py` | `docs/outputs/sistemas_pago/` |
| **Retail Financiero** | CMF Emisores no bancarios | Trimestral | `retail_financiero/scripts/stream_cmf_retail_financiero.py` | `docs/outputs/retail_financiero/` |
| **FinTech** | CMF Registro RPSF (Ley 21.521) | Mensual | `fintech/scripts/stream_cmf_fintech.py` | `docs/outputs/fintech/` |

---

## 3. Ejecución y Auditoría
Para validar la totalidad de las bases generadas automáticamente:
```bash
python scripts/audit_web_full.py
```

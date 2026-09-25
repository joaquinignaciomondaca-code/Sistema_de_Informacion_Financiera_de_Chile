# Monitor Financiero Chile (MFC)

Plataforma analítica y motor de datos para el procesamiento, normalización y exploración interactiva en el navegador (DuckDB-Wasm) del sistema financiero institucional, bancario y mercado de capitales chileno.

---

## 1. Alcance y Perímetro Regulatorio (15 Sectores Supervisados)

El repositorio consolida fuentes oficiales emitidas por la **Comisión para el Mercado Financiero (CMF)**, la **Superintendencia de Pensiones (SPensiones)**, la **Superintendencia de Seguridad Social (SUSESO)** y el **Banco Central de Chile (BCCh)**:

1. **Seguros de Vida & Generales** (seguros/): Circular CMF 1835 (Bonos, Acciones, Bienes Raíces, Derivados B.7 Forwards, Swaps, Repos).
2. **Fondos Mutuos** (fmm/): Circular CMF 1333 (Cartera de Inversiones, Futuros y Opciones).
3. **Fondos de Inversión** (i/): Ley Única de Fondos (LUF), Circular 1998 (Cartera Nacional, Extranjera, Repos).
4. **Fondos de Pensiones** (pensiones/): Sistema Previsional D.L. 3.500 (Cartera de Renta Fija, Variable, Forwards y Swaps).
5. **Banca e Instituciones Financieras** (ancos/): Balances C1, Estados de Resultados y Derivados OTC vigentes y transados.
6. **Macroeconomía & Tasas** (macro/): Estadísticas BCCh (TPM, Tipos de Cambio, Curvas de Rendimiento BCP/BCU e Inflación).
7. **Factoring & Leasing** (actoring_leasing/): Entidades registradas CMF y balances financieros bajo norma IFRS.
8. **Corredoras de Bolsa** (corredoras_bolsa/): Intermediarios de valores, balances patrimoniales y solvencia.
9. **Sociedades Securitizadoras** (securitizadoras/): Emisoras de títulos de deuda y balances IFRS.
10. **Patrimonios Separados** (securitizadoras/): Vehículos de propósito especial y carteras de activos securitizados (Ley 18.045).
11. **Cajas de Compensación** (ccaf/): Catálogo institucional, serie histórica de balances 2010–2025, desglose analítico de Efectivo (Nota 8) y carteras de crédito social.
12. **Administradoras Generales de Fondos** (gf/): Sociedades gestoras fiduciarias (Ley 20.712) y balances auditados.
13. **Retail Financiero** (
etail_financiero/): Emisores de tarjetas no bancarias y matrices comerciales supervisadas por CMF.
14. **Sistemas de Pago** (sistemas_pago/): Infraestructuras de liquidación bruta en tiempo real (LBTR), cámaras de compensación y operadores de medios de pago.
15. **FinTech & Finanzas Abiertas** (intech/): Ley N° 21.521, Registro de Prestadores de Servicios Financieros (RPSF) y taxonomía del Sistema de Finanzas Abiertas (SFA).

---

## 2. Arquitectura de la Plataforma Web Interactiva (docs/)

La interfaz opera como una aplicación web estática de alto rendimiento, ejecutando consultas SQL directamente en el cliente mediante **DuckDB-Wasm**:
- **Explorador Jerárquico & Chips SQL (js/sidebar.js)**: 15 industrias, más de 65 tablas y 81 consultas predefinidas.
- **Visor de Datos en Vivo (js/data_viewer.js)**: Visualización tabular y exportación de datos en Parquet, CSV y JSON.
- **Diccionario de Datos & Contabilidad Regulatoria (js/data_dictionary.js)**: Especificación campo por campo de roles (PK, FK, Dimensión, Métrica), definiciones funcionales y criterios contables (MtM, Costo Amortizado, Tasación).
- **Mapa Relacional ERD (js/erd_graph.js)**: Diagrama interactivo de Entidad-Relación renderizado en Canvas con zoom, pan y enlaces de integridad referencial.
- **Terminal SQL Interactiva (js/chat_terminal.js)**: Consola de ejecución de queries SQL ad-hoc sobre archivos Parquet locales.

---

## 3. Principio de Higiene Efímera de Disco (Automatización)

Todos los pipelines de descarga y extracción implementan un protocolo estricto de **cero residuos temporales en disco**:
- Los archivos PDF o insumos crudos pesados se descargan a rutas temporales.
- El procesamiento extrae únicamente los datos requeridos a memoria.
- Los descriptores de archivo se cierran y los archivos crudos se eliminan de inmediato en bloques inally.
- Este mecanismo asegura que los entornos de automatización (CI/CD, GitHub Actions, crons) operen sin acumulación de almacenamiento ni riesgo de saturación de disco.

---

## 4. Auditoría y Control de Calidad

El proyecto incluye suites de auditoría automatizadas para validar la integridad de extremo a extremo:

1. **Auditoría Integral de la Aplicación Web**:
   `ash
   python scripts/audit_web_full.py
   `
   Valida la existencia física de todos los archivos Parquet, la integridad de los enlaces del sidebar, la coherencia de las consultas de los chips SQL, el diccionario de datos y los nodos y relaciones del ERD.

2. **Auditorías de Dominio por Sector**:
   - CCAF: python ccaf/scripts/audit_ccaf.py
   - FinTech: python fintech/scripts/audit_fintech.py
   - Otros sectores en sus respectivos subdirectorios.

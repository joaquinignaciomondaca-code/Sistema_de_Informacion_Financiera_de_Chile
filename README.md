# Monitor Financiero Chile (MFC)

Plataforma analítica y motor de datos para el procesamiento, normalización y exploración interactiva en el navegador (DuckDB-Wasm) del sistema financiero institucional, bancario y mercado de capitales chileno.

---

## Operación de datos: PC + GitHub Actions

El código de los métodos se conserva en el repositorio. Las extracciones complejas pueden ejecutarse en PC; los flujos maduros y pequeños pueden correr automáticamente en Actions. El piloto macro BCCh guarda resultados en staging, audita y entrega un artifact para revisión antes de publicar en la web. **Antes de habilitarlo, rotar las credenciales BCCh expuestas anteriormente en Git.** Instrucciones: [`pipelines/README.md`](pipelines/README.md).

---

## 1. Alcance y Perímetro Regulatorio (15 Sectores Supervisados)

El repositorio consolida fuentes oficiales emitidas por la **Comisión para el Mercado Financiero (CMF)**, la **Superintendencia de Pensiones (SPensiones)**, la **Superintendencia de Seguridad Social (SUSESO)** y el **Banco Central de Chile (BCCh)**:

1. **Seguros de Vida & Generales** (seguros/): Circular CMF 1835 (Bonos, Acciones, Bienes Raíces, Derivados B.7 Forwards, Swaps, Repos).
2. **Fondos Mutuos** (fmm/): Circular CMF 1333 (Cartera de Inversiones, Futuros y Opciones).
3. **Fondos de Inversión** (i/): Ley Única de Fondos (LUF), Circular 1998 (Cartera Nacional, Extranjera, Repos).
4. **Fondos de Pensiones** (pensiones/): Sistema Previsional D.L. 3.500 (Cartera de Renta Fija, Variable, Forwards y Swaps).
5. **Banca e Instituciones Financieras** (ancos/): Balances C1, Estados de Resultados y Derivados OTC vigentes y transados.
6. **Macroeconomía & Tasas** (macro/): Estadísticas BCCh (TPM, Tipos de Cambio, Curvas de Rendimiento BCP/BCU e Inflación).
7. **Factoring & Leasing** (`factoring_leasing/`): por ahora solo la Lista de Entidades; balances y notas retirados de la publicación.
8. **Corredoras de Bolsa** (corredoras_bolsa/): Intermediarios de valores, balances patrimoniales y solvencia.
9. **Sociedades Securitizadoras** (securitizadoras/): Emisoras de títulos de deuda y balances IFRS.
10. **Patrimonios Separados** (securitizadoras/): Vehículos de propósito especial y carteras de activos securitizados (Ley 18.045). Lista de emisiones inscritas en la CMF y balance general cuenta por cuenta de cada patrimonio, cierres de diciembre 2014–2025 (de 2010 a 2013 no hay datos), leído de los PDF de estados financieros publicados en la CMF.
11. **Cajas de Compensación** (ccaf/): Lista de entidades y balance (activos, pasivos, patrimonio y utilidad) 2019-12–2026-06 extraído del XBRL oficial de la CMF. Nota 8 y crédito social se retiraron.
12. **Administradoras Generales de Fondos** (agf/): Sociedades gestoras fiduciarias (Ley 20.712), su balance y su estado de resultados IFRS trimestral (2018–2026) en tablas separadas.
13. **Sistemas de Pago** (sistemas_pago/): solo la lista de entidades (LBTR, cámaras de compensación, contrapartes centrales y operadores de medios de pago).
14. **FinTech** (fintech/): solo la lista de entidades del Registro de Prestadores de Servicios Financieros (RPSF, Ley N° 21.521).
15. **Cooperativas de Ahorro y Crédito** (cooperativas/): solo la lista de entidades (los balances venían de planillas Excel de la CMF, no de XML/XBRL, y se retiraron).

---

## 2. Arquitectura de la Plataforma Web Interactiva (docs/)

La interfaz opera como una aplicación web estática de alto rendimiento, ejecutando consultas SQL directamente en el cliente mediante **DuckDB-Wasm**:
- **Explorador Jerárquico & Chips SQL (js/sidebar.js)**: 15 industrias, 63 tablas y 80 consultas predefinidas.
- **Visor de Datos en Vivo (js/data_viewer.js)**: Visualización tabular y exportación de datos en Parquet, CSV y JSON.
- **Diccionario de Datos & Contabilidad Regulatoria (js/data_dictionary.js)**: Especificación campo por campo de roles (PK, FK, Dimensión, Métrica), definiciones funcionales y criterios contables (MtM, Costo Amortizado, Tasación).
- **Mapa Relacional ERD (js/erd_graph.js)**: Diagrama interactivo de Entidad-Relación renderizado en Canvas con zoom, pan y enlaces de integridad referencial.
- **Terminal SQL Interactiva (js/chat_terminal.js)**: Consola de ejecución de queries SQL ad-hoc sobre archivos Parquet locales.
- **Selector de Paletas (js/theme_switcher.js + css/app.css)**: Seis paletas conmutables desde el encabezado. La predeterminada es `dark-ide` (estilo IDE/editor oscuro: fondos casi negros `#121316`, paneles `#18191E` y acento azul `#3B82F6`), junto a `swissborg`, `bloomberg`, `nord`, `midnight` e `informe` (modo claro). Los gráficos y el diagrama ERD leen los colores de la paleta activa mediante variables CSS (`--accent-rgb`, `--tint-rgb`, `--neutral-rgb`, `--panel-elevated`), por lo que no requieren ajustes por tema.

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

# Modulo Bancos e Instituciones Financieras (CMF Bancos & BCCh Derivados)

## Alcance Normativo y Fuentes
Este modulo consolida la informacion de la banca comercial e instituciones financieras fiscalizadas por la Comision para el Mercado Financiero (CMF) y el Banco Central de Chile (BCCh):

1. **Catalogo Maestro Institucional (CMF)**:
   - 40 entidades bancarias (18 bancos comerciales activos + bancos historicos fusionados/cerrados, filiales extranjeras BCI/CorpBanca y agregados sectoriales).
   - RUTs verificados 100% con Algoritmo Modulo 11.
2. **Asientos Contables Generales (CMF MB1 / MR1)**:
   - **Balance General**: Total Activos, Total Pasivos y Patrimonio Neto (en MM$ CLP y MM$ USD).
   - **Estado de Resultados**: Utilidad Neta del ejercicio (en MM$ CLP y MM$ USD).
3. **Mercado de Derivados OTC Bancarios (BCCh SIETE F099)**:
   - **Posicion Vigente (Stock Nocional)**: Saldos abiertos al cierre de mes en Forwards (USD/CLP, UF/CLP, NDF) y Swaps (Promedio Camara SPC, Cross Currency Swaps CCS) por contraparte (No Residentes, Empresas Sector Real, AFPs, Residentes No Bancos) y plazo contractual.
   - **Montos Transados (Flujo Mensual)**: Volumen mensual de compras, ventas y monto neto operado.

---

## Estructura de Directorios
```
bancos/
├── scripts/
│   ├── pipeline_stream_bancos.py          # Pipeline streaming de balances y resultados CMF
│   ├── audit_bancos_data.py               # Auditoria de balances CMF
│   ├── pipeline_stream_derivados_bcch.py  # Pipeline concurrente de derivados BCCh F099
│   ├── audit_derivados_bcch.py            # Auditoria de derivados BCCh F099
│   └── cmf_bancos_packages.json           # Catalogo indexado de paquetes mensuales
├── derivados_otc/
│   └── catalog_f099.json                  # Catalogo completo de 1,314 series F099 BCCh
└── README.md
```

## Salidas Canonicas (docs/outputs/bancos/)
- `bancos_maestro.parquet` (y `.json`): 40 instituciones con RUT verificado, tipo de licencia y estado.
- `bancos_balance_resumen.parquet` (y `.json`): 5,095 balances mensuales (Total Activos, Total Pasivos, Patrimonio Neto).
- `bancos_estado_resultados.parquet` (y `.json`): 5,095 estados de resultados mensuales (Utilidad Neta).
- `bancos_derivados_posicion_vigente.parquet` (y `.json`): 2,860 observaciones mensuales de stock nocional abierto.
- `bancos_derivados_flujos_transados.parquet` (y `.json`): 2,860 observaciones mensuales de volumen transado.

## Auditoria de Calidad
Ejecutar las suites de verificacion:
```bash
python bancos/scripts/audit_bancos_data.py
python bancos/scripts/audit_derivados_bcch.py
```
- Unicidad de Primary Keys: 100%.
- Ausencia de nulos inesperados: 0 nulos.
- Validacion Modulo 11: 100% de RUTs conformes.
- Integridad referencial: 100% contra bancos_maestro.
- Cobertura temporal continua sin lagunas.
- Residuos en disco: 0 bytes.

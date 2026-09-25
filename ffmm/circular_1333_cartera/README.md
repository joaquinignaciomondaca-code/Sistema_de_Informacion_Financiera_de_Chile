# Circular 1333 (CMF) — Cartera de Inversiones y Derivados en Fondos Mutuos

## 1. Descripción Normativa
La **Circular N° 1.333** de la Comisión para el Mercado Financiero (CMF) imparte instrucciones sobre el envío de información relativa a la composición de la cartera de inversiones de los **Fondos Mutuos (FFMM)** chilenos.

Las Administradoras Generales de Fondos (AGF) reportan mensualmente el inventario detallado de instrumentos financieros mantenidos al último día del mes calendario, con plazo reglamentario de entrega de **10 días hábiles del mes siguiente**.

---

## 2. Estructura de Datos en este Módulo

```
ffmm/circular_1333_cartera/
├── inputs/                    # Archivos crudos descargados de CMF (FUTU_AAAAMM.txt, OPCI_AAAAMM.txt)
├── outputs/                   # Bases consolidadas normalizadas (.parquet y .csv UTF-8 BOM)
├── scripts/
│   ├── update_pipeline.py     # Pipeline de descarga incremental y actualización automática
│   └── normalize_ffmm.py      # Normalizador estricto según taxonomía CMF
└── README.md                  # Este documento
```

---

## 3. Diccionario de Variables Oficiales (CMF)

### Tabla FUTU (Forwards, Swaps, Futuros)
*Fuente oficial: Cuadro FFM_604*

| Campo Normalizado | Código CMF | Descripción | Formato / Valores |
| :--- | :--- | :--- | :--- |
| `periodo` | - | Mes del reporte | `AAAA-MM` |
| `run_fondo` | `Run Fondo` | RUN del Fondo Mutuo | Texto |
| `nombre_fondo` | `Nombre Fondo` | Razón social del fondo | Texto (UTF-8) |
| `moneda_subyacente`| `FFM_6040111` | Moneda del subyacente | USD, EUR, UF, CLP, etc. |
| `tipo_instrumento` | `FFM_6040112` | Tipo de derivado | FORWARD, SWAP, FUTURO |
| `nemotecnico` | `FFM_6040113` | Identificador / nemotécnico | Texto |
| `fecha_vencimiento`| `FFM_6040114` | Fecha de vencimiento | `DD/MM/AAAA` |
| `mercado` | `FFM_6040115` | Tipo de mercado | OTC / BOLS |
| `pais` | `FFM_6040116` | País de la contraparte/mercado | CL, US, etc. |
| `posicion` | `FFM_6040200` | Posición del fondo | `C` (Comprador/Largo), `V` (Vendedor/Corto) |
| `nocional` | `FFM_6040300` | Nocional del contrato | Numérico |
| `precio_pactado` | `FFM_6040400` | Tipo de cambio o tasa pactada | Numérico |
| `monto_contratado_m_clp`| `FFM_6040500` | Monto contratado en M$ CLP | Miles de pesos |
| `valor_mercado_m_clp` | `FFM_6040600` | Valor justo / MTM en M$ CLP | Miles de pesos |
| `archivo_fuente` | - | Nombre del archivo crudo | `FUTU_AAAAMM.txt` |

### Tabla OPCI (Opciones Financieras)
*Fuente oficial: Cuadro FFM_603*

| Campo Normalizado | Código CMF | Descripción | Formato / Valores |
| :--- | :--- | :--- | :--- |
| `periodo` | - | Mes del reporte | `AAAA-MM` |
| `run_fondo` | `Run Fondo` | RUN del Fondo Mutuo | Texto |
| `nombre_fondo` | `Nombre Fondo` | Razón social del fondo | Texto (UTF-8) |
| `moneda_subyacente`| `FFM_6030111` | Moneda del subyacente | Moneda ISO / UF |
| `nemotecnico` | `FFM_6030112` | Nemotécnico del contrato | Texto |
| `tipo_opcion` | `FFM_6030113` | Ejercicio | `A` (Americana), `E` (Europea) |
| `fecha_vencimiento`| `FFM_6030114` | Fecha de vencimiento | `DD/MM/AAAA` |
| `mercado` | `FFM_6030115` | Mercado de negociación | OTC / BOLS |
| `pais` | `FFM_6030116` | País emisor | Código país |
| `posicion` | `FFM_6030200` | Posición | `C` (Comprada), `V` (Lanzada/Vendida) |
| `strike` | `FFM_6030300` | Precio de ejercicio (Strike) | Numérico |
| `numero_contratos` | `FFM_6030400` | Número de contratos | Entero |
| `prima_m_clp` | `FFM_6030500` | Prima pagada/cobrada en M$ CLP | Miles de pesos |
| `valor_mercado_m_clp`| `FFM_6030900` / `800` | Valorización de mercado MTM en M$ CLP | Miles de pesos |
| `archivo_fuente` | - | Nombre del archivo crudo | `OPCI_AAAAMM.txt` |

---

## 4. Ejecución del Módulo

### Actualización Incremental (Recomendada)
```bash
python ffmm/circular_1333_cartera/scripts/update_pipeline.py
```
* Omite meses consolidados (> 2 meses con tamaño válido).
* Solo revisa los últimos 3 meses móviles.
* Tarda ~2 segundos si no hay novedades.

### Reconstrucción Completa de la Serie Histórica
```bash
python ffmm/circular_1333_cartera/scripts/update_pipeline.py --full-scan
```

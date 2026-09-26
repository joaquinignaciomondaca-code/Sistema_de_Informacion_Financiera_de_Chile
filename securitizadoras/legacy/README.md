# Tablas v1 en cuarentena (no publicadas en la web)

Retiradas de `docs/outputs/securitizadoras/` el 2026-09-26 tras la auditoría
(`../AUDITORIA_2026-09-26.md`). Se conservan sólo en Parquet para no perder información, pero **no deben usarse
para análisis** hasta que exista un pipeline que las regenere y pasen `audit_patrimonios_separados_v2.py`.

| Tabla | Filas | Motivo de cuarentena |
|---|---|---|
| patrimonios_separados_balance_lineas | 16.842 | Sin script generador; 573 `id_patrimonio` para ≈60 PS; sólo 25 % de balances cuadran; RUT truncados |
| patrimonios_separados_excedentes_lineas | 11.157 | Sin script generador; mismas claves inestables |
| patrimonios_separados_nota_efectivo_detalle | 3.802 | Sin script generador; esquema distinto al del parser existente |
| patrimonios_separados_nota_bonos_detalle | 8.001 | 100 % placeholders (`fecha_vencimiento` = fecha del período, `monto_colocado` = saldo) |
| patrimonios_separados_nota_cartera_detalle | 796 | Sin script generador |
| patrimonios_separados_nota_administracion_detalle | 2.153 | Sin script generador; participaciones rígidas por concepto |
| patrimonios_separados_nota_sobrecolateral_detalle | 679 | 100 % activos = pasivos = 0 con % de sobrecolateral no nulo |
| patrimonios_separados_nota_morosidad_detalle | 6.632 | 27 variantes de tramo; % provisión hasta 2,2e8 |
| patrimonios_separados_repos_detalle | 52 | 100 % defaults (plazo 0, tasa 0,39, "Cumple / SI") |
| patrimonios_separados_cartera_morosidad_detalle | 67 | 27/67 con provisión > cartera |

**Fuente identificada (2026-09-26):** `balance_lineas`/`excedentes_lineas` salieron de los mismos PDFs trimestrales
de la pestaña 18 de CMF (no de una fuente estructurada). Contraste con el PDF real de Volcom BVOLS al 12/2024:

| Cuenta | v1 (cuarentena) | PDF CMF | Diagnóstico |
|---|---|---|---|
| 11.030 Activo securitizado CP | 94.335.870 | 4.335.870 | N° de nota "9" concatenado al monto |
| 11.200 Otros activos circulantes | 116.488.572 | 6.488.572 | N° de nota "11" concatenado |
| 13.010 Activo securitizado LP | 989.303.250 | 89.303.250 | N° de nota "9" concatenado |
| 11.000 Total activos circulantes | 12.175.537 | 12.175.537 | correcto (sin nota) |

Por eso el 75 % de los balances v1 no cuadraba. La reconstrucción reproducible es el paso `ps` de
`../scripts/pipeline_securitizadoras.py` → `patrimonios_separados_eeff_lineas` (catálogo `../data/catalogo_fecu_ps.json`).
Estos archivos pueden eliminarse una vez que la tabla nueva cubra 2010–hoy.

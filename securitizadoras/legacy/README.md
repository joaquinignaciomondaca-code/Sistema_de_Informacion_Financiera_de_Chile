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

Las cuentas FECU-PS reales de `balance_lineas`/`excedentes_lineas` (plan 10.000…35.xxx, 2010–2026) sugieren que
existió una fuente estructurada (FECU-PS HTML/XBRL de CMF). Si se recupera esa fuente, el camino correcto es
implementarla como paso `fecu_ps` en `../scripts/pipeline_securitizadoras.py` (formato largo, clave
`numero_inscripcion`, columnas de procedencia) y no rehabilitar estos archivos.

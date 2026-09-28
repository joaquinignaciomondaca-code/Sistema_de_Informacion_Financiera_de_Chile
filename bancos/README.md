# Bancos — estado de publicación

**Publicado en el sitio (automático):**

- `bancos_maestro`: lista de instituciones (código CMF, RUT, razón social, estado). Altas y vigencia se
  actualizan con `entidades.yml` (pipelines/entidades).
- `bancos_cmf_balance` / `bancos_cmf_resultados`: líneas de los archivos oficiales CMF B1/B2/R1 por
  institución y mes, en `docs/outputs/bancos/cmf_b1_b2_r1/<periodo>/lineas.parquet`. Esquema en
  [ESQUEMA_CMF_B1_B2_R1.md](ESQUEMA_CMF_B1_B2_R1.md).

**Workflow:** `bancos_cmf_mensual.yml` (días 1, 11 y 21) → tests → `python -m bancos.scripts.publish_cmf_bank_period --catch-up`.
Es incremental: sólo descarga los meses que faltan en el manifest.

**Código vigente:**

| Archivo | Rol |
|---|---|
| `scripts/publish_cmf_bank_period.py` | descarga el paquete mensual CMF, extrae, valida y publica un período |
| `scripts/extract_cmf_bank_lines.py` | parser de líneas B1/B2/R1 |
| `scripts/inspect_cmf_bank_sample.py` | lectura/validación del ZIP CMF (usado por los dos anteriores) |
| `tests/` | tests de los tres scripts + identidad del maestro |

**Retirado (2026-09-28):** el laboratorio REPO (pactos/préstamos de valores), los derivados OTC BCCh,
el pipeline antiguo `pipeline_stream_bancos.py` y las sondas de formato/muestra. Ninguno publicaba datos;
quedan en el historial de Git si alguna vez se retoman.

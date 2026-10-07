# Seguros de vida y generales (CMF — Circular 1835)

El extractor lee los archivos mensuales de cartera de las compañías de vida (`CSVID`) y generales (`CSGEN`) y publica las tablas de `docs/outputs/seguros/`. La ficha técnica cubre dos formatos: el vigente hasta 2024-11 y el formato usado desde 2024-12.

## Operaciones REPO (pactos)

La tabla consultable es **`seguros_pactos`** (nombre lógico `seguros.pactos`), publicada por `seguros/scripts/actualizar_carteras.py` dentro del flujo incremental `seguros_carteras.yml`.

Incluye compras y ventas con pacto, fecha de operación y vencimiento, contraparte y datos del activo objeto. Campos principales:

- `tipo_operacion`, `folio`, `item`, `fecha_operacion`, `fecha_vencimiento`;
- `contraparte`, `nacionalidad_contraparte`, `relacionado`;
- `activo_objeto`, `serie_activo_objeto`, `rut_emisor_activo_objeto`;
- `tasa_pacto_pct`, `valor_nominal`, `interes_devengado_m_clp`, `valor_contable_m_clp` y `valor_mercado_activo_objeto_m_clp`.

**Unidades:** los campos terminados en `_m_clp` están en miles de pesos (M$); `valor_nominal` conserva la unidad/moneda reportada para el activo. El valor nominal no debe sumarse como si siempre fueran pesos.

## Cobertura revisada

Al 2026-10-07, el manifiesto contiene **11.153 filas** de pactos desde **2016-11** hasta **2026-08**; el último mes tiene **155 filas**. El workflow programado terminó correctamente el 2026-10-04; su diagnóstico no reportó problemas y no añadió un período nuevo. La fecha `updated_at` del manifiesto (2026-09-28) señala el último cambio de datos, no la última ejecución del flujo.

Archivos por año: `docs/outputs/seguros/pactos/AAAA.parquet`; cobertura detallada por período: `docs/outputs/seguros/pactos/manifest.json` y `docs/outputs/seguros/manifest.json`.

```sql
SELECT periodo,
       count(*) AS filas,
       count(DISTINCT rut_aseguradora) AS companias
FROM seguros_pactos
GROUP BY periodo
ORDER BY periodo DESC
LIMIT 12;
```

Para el estado comparado con fondos de inversión y la aclaración sobre fondos mutuos, ver [cobertura de REPO/pactos](../docs/notas/cobertura_repos_pactos_2026-10-07.md).

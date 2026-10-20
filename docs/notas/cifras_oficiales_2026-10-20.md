# Cifras oficiales del sitio — 2026-10-20

Única referencia para las cifras de portada, README y notas. Si una cifra cambia, se actualiza aquí
primero y luego en los demás documentos. La portada calcula sus cifras desde el catálogo
(`docs/js/alcance.js`); los textos fijos son el README y `docs/index.html`.

## Fuente

- `data_manifest.json` (actualizado 2026-10-20): 74 tablas en el manifiesto, 13.483.676 registros.
- Tabla oculta `fi.bienes_raices` (`fi_bienes_raices`): publicada, no figura en la vista principal.
  Con ella suman **75 tablas publicadas**.
- Peso de los Parquet en `docs/outputs/`: 257,8 MB en 632 archivos (medido el 2026-10-20).

## Cifras

| Concepto | Valor | Nota |
|---|---|---|
| Industrias | 15 | Sectores con datos (incluye Pensiones, Cooperativas, Sistemas de pago, Fintech como registro) |
| Tablas publicadas | 75 | 74 en el manifiesto + 1 oculta |
| Registros publicados | 13.483.676 | Suma de `registros_reales` del manifiesto. Se redondea a **13,5 millones** |
| Vista principal | 59 conjuntos · 13.383.401 registros (99,3 %) | Núcleo (25), instituciones (10) y contexto macro (24) |
| Archivo y registro | 15 conjuntos · 100.263 registros (0,7 %) | Factoring y leasing, securitización, cajas de compensación, AFP, cooperativas, pagos, fintech |
| Consultas sugeridas del explorador | 146 | `audit_consultas_sugeridas.py` |
| Consultas del terminal por defecto | 7 | 146 + 7 = 153 consultas en total |
| Peso de los Parquet | 258 MB (632 archivos) | |

## Diferencias conocidas (pendientes de conciliar)

- **12 registros** entre el total del manifiesto (13.483.676) y la suma de vista principal y archivo
  (13.383.401 + 100.263 = 13.483.664).
- **Macro:** el recorte del 2026-10-20 reporta 41.413 registros; el manifiesto suma 41.424 (11 de diferencia).

Ninguna de las dos diferencias cambia las cifras redondeadas que se muestran en la web (13,5 M y 99,3 %).
Conviene conciliarlas en el próximo recálculo del recorte.

## Versiones anteriores corregidas

- README: 13.292.809 filas y 283 MB, del manifiesto al 2026-10-06. Reemplazado por las cifras de arriba.
- README: insignia "13,3 M filas" → "13,5 M filas".
- README: ejemplo de consulta FFMM (US 1.131 / LU 512 / BR 98 / GB 84 / IE 489) reemplazado por el resultado
  verificado de la misma consulta sobre el Parquet publicado en 2026-09: US 1.100, LU 524, IE 489, BR 100, GB 84.
  No está claro si la cifra antigua venía de otra versión del dato; no hay registro de ello en el historial.

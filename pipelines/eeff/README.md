# EEFF desde el PDF de Información Financiera

El buscador de periodos ya estaba codificado y no se usaba.

En `factoring_leasing/scripts/02_extract_factoring_leasing_notas_series.py`,
`fetch_cmf_pdf_stream` hace exactamente lo que se hace a mano en la CMF:

1. Abrir la ficha, pestaña Información Financiera (`pestania=3`).
2. Enviar el formulario de periodo: `mm`, `aa`, `tipo` (C o I), `tipo_norma=IFRS`.
3. Seguir el enlace cuyo texto es `Estados financieros (PDF)`
   (`safec_ifrs_verarchivo.php`).
4. Si no hay consolidado, repetir en individual.

`extract_all()` de ese script no llama a esa función. Reparte el total de
efectivo y de cartera con porcentajes fijos. Eso no es una nota. Esas tablas
siguen en el monitor bajo De Interés, marcadas para no usarlas como EEFF.

## Qué hay de marzo 2026

Diez PDF, leídos y guardados en `factoring_leasing/eeff_fuentes/`.

Carátula que cuadra (activos = pasivos + patrimonio) y que la API confirma
en los totales, con tolerancia de 1 millón:

- Forum, Santander Consumer, Autofin, Primus, ST Capital, GM Financial,
  Security y Penta.

Parciales, a propósito. No se completan con la visualización HTML:

- Tanner: total de activos, pasivo financiero corriente, patrimonio de
  cierre y el tramo de resultados que sí se leyó. El índice de notas está.
  Las notas de monto empiezan en la página 51.
- Eurocapital: efectivo, deudores corrientes, total de activos, patrimonio
  y ganancia del periodo. Las notas de monto empiezan en la página 36.

Notas con montos: solo Factoring Security, Nota 4 (efectivo) y Nota 5
(deudores, el monto es el neto). La suma cuadra con el balance. El índice
de las demás notas está, con `extraida=0`.

Penta no trae el gasto de administración: el corte de página partió la cifra
y no se completa a mano.

## Fuente y validación

- Fuente: el PDF, transcrito a Markdown en `factoring_leasing/eeff_fuentes/`.
- Validación: `factoring_leasing_balance_resumen`. Si el total del PDF no
  cuadra con la API en más de 1 millón, la fila queda `DIFIERE`. En este
  corte no hay diferencias. `SOLO_API` significa que el PDF no publicó esa
  línea (Autofin no separa pasivo corriente; Tanner y Eurocapital están
  incompletos). La API no rellena notas.

## Cómo correrlo

```bash
python factoring_leasing/scripts/03_eeff_desde_pdf.py --periodo 2026-03
python pipelines/eeff/test_parse_md.py

# En una red que llegue a cmfchile.cl:
python factoring_leasing/scripts/03_eeff_desde_pdf.py --descargar --periodo 2026-03
```

El monitor separa Factoring en EEFF y De Interés. EEFF es el PDF.
De Interés es el maestro, la serie API y las tablas de porcentajes.

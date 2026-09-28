# Fondos de Inversión (CMF — Ley Única de Fondos)

La CMF no publica un archivo masivo de carteras de fondos de inversión (a diferencia de la
Circular 1333 de fondos mutuos): cada fondo tiene, por trimestre, una página por tipo de cartera
de sus informes IFRS y una de pactos. `scripts/actualizar_carteras.py` las recorre todas.

- Workflow: `.github/workflows/fi_carteras.yml`, días 9, 19 y 29; incremental (solo trimestres
  que faltan en `docs/outputs/fi/manifest.json`), desde 2020-03.
- Validación fail-closed: encabezados exactos, cuadratura de cada columna de montos contra la
  fila TOTAL que publica la CMF, ≤ 1 % de filas ilegibles, completitud ≥ 90 % de los fondos del
  trimestre anterior.
- Montos en miles de la moneda funcional de cada fondo (`_miles_mf`); la moneda está en la lista
  de fondos (`maestro_fondos_inversion.parquet`).

Salidas (`docs/outputs/fi/`): `cartera_nacional/` (un archivo por trimestre),
`cartera_extranjera/`, `metodo_participacion/`, `bienes_raices/`, `futuros_forwards/`,
`opciones/`, `pactos/` (uno por año), `maestro_fondos_inversion.parquet` y
`fi_registro_fondos_universo.json`.

Vistas web: `fi_maestro`, `fi_cartera_nacional`, `fi_cartera_extranjera`,
`fi_metodo_participacion`, `fi_bienes_raices`, `fi_futuros`, `fi_opciones`, `fi_pactos`.

El extractor y los REPO antiguos (`cartera_inversiones/`, `repos/`, scripts 01–04) se eliminaron
el 2026-09-28: mezclaban columnas y dañaban los acentos.

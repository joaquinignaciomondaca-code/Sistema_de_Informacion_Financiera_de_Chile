# sif-chile · notas para quien llama

Contrato estático de SIF Chile. Base: `https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile`.

- Todo es GET y de solo lectura (`readOnly: true`, `minTier: 1`): no hay cookies,
  ni login, ni escrituras. No hace falta navegador.
- `catalog` es el punto de partida: devuelve los objetos con `id`. Usa ese `id`
  en `schema` y `partitions`.
- `queries` devuelve las consultas sugeridas con `id` estable; `resultados` es su
  índice ya calculado y `resultado` trae los datos de una. Si solo necesitas el
  número, pide `resultado` y no descargues los Parquet.
- Un `id` que no existe responde 404 y api-anything lo clasifica como `input`
  (no como sitio caído): corrige el id, no reintentes a ciegas.
- Los Parquet no están en esta spec: se leen con DuckDB desde `views.sql` o con
  el SDK `sif-chile`. Esta spec cubre el contrato JSON, no la descarga masiva.

## Maintainer notes

Spec generada por `scripts/build_api_anything.py` desde `docs/api/v2/`. No editar
a mano: `python3 scripts/build_api_anything.py --check` falla si se desactualiza.
La prueba real contra un espejo local es `scripts/probar_api_anything.py`.

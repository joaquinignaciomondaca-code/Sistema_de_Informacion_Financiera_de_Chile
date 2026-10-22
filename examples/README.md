# Ejemplos reproducibles

Cada archivo es un programa completo que **se ejecuta y comprueba algo**. No son
fragmentos para copiar: si el dato deja de estar, el ejemplo falla en vez de
imprimir una tabla vacía.

Ninguno necesita el repositorio entero, solo los Parquet publicados. Si no hay
red, `SIF_CHILE_BASE` puede apuntar a una copia local de `docs/`.

| Ejemplo | Qué demuestra | Requisitos |
| --- | --- | --- |
| [`python/01_ffmm_extranjero.py`](python/01_ffmm_extranjero.py) | la consulta del README: dónde invierten fuera de Chile los fondos mutuos | `sif-chile` |
| [`python/02_cruce_tres_industrias.py`](python/02_cruce_tres_industrias.py) | el caso del proyecto: un emisor visto por aseguradoras y fondos mutuos a la vez | `sif-chile` |
| [`r/01_basico.R`](r/01_basico.R) | lo mismo sin SDK propio: `DBI` + `duckdb` y el `views.sql` publicado | `DBI`, `duckdb` |
| [`javascript/catalogo.mjs`](javascript/catalogo.mjs) | descubrir el contrato desde Node con `fetch`, sin motor SQL | Node ≥ 18 |
| [`agent/README.md`](agent/README.md) | cómo un agente lee [`llms.txt`](../docs/llms.txt) y hace dos llamadas en vez de noventa | — |

```bash
pip install -e sdk/python
python3 examples/python/01_ffmm_extranjero.py
python3 examples/python/02_cruce_tres_industrias.py
node examples/javascript/catalogo.mjs
Rscript examples/r/01_basico.R
```

Contra una copia local, sin red:

```bash
SIF_CHILE_BASE=docs python3 examples/python/01_ffmm_extranjero.py
SIF_CHILE_BASE=docs node examples/javascript/catalogo.mjs
```

Los tres primeros corren en CI (`scripts/probar_ejemplos.py` para Python y
JavaScript; el trabajo `r_ejemplos` de `web_audit.yml` para R).

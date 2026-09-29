# Motor DuckDB-Wasm incluido en el repositorio

Estos archivos son una copia sin modificar del paquete **@duckdb/duckdb-wasm 1.28.0**
(MIT License, © DuckDB Foundation y contribuyentes), publicados en npm.

| Archivo | Origen en el paquete |
| :--- | :--- |
| `duckdb-browser.mjs` | `dist/duckdb-browser.mjs` |
| `duckdb-browser-eh.worker.js` | `dist/duckdb-browser-eh.worker.js` |
| `duckdb-eh.wasm` | `dist/duckdb-eh.wasm` |

## Por qué está acá

El terminal SQL ejecuta consultas **en el navegador** con DuckDB-Wasm. La forma
habitual de cargarlo (`import` desde `cdn.jsdelivr.net`) deja el terminal inutilizable
cuando la red del visitante bloquea el CDN, cuando hay un proxy corporativo o cuando
el sitio se sirve sin salida a internet. Servir el motor desde el mismo origen elimina
esa dependencia: `docs/js/duckdb_client.js` carga primero esta copia y sólo recurre al
CDN si los archivos locales no están disponibles o el navegador no soporta el bundle
`eh` (WebAssembly exception handling).

## Actualización

```bash
npm pack @duckdb/duckdb-wasm@<versión>
tar -xzf duckdb-duckdb-wasm-<versión>.tgz \
  package/dist/duckdb-browser.mjs \
  package/dist/duckdb-browser-eh.worker.js \
  package/dist/duckdb-eh.wasm
cp package/dist/{duckdb-browser.mjs,duckdb-browser-eh.worker.js,duckdb-eh.wasm} docs/vendor/duckdb/
```

Al cambiar de versión hay que actualizar también `DUCKDB_VERSION` en
`docs/js/duckdb_client.js`, que es la que se usa para el respaldo por CDN.

## Notas de operación

* El servidor de vista previa (`scripts/preview_no_cache.py`) y GitHub Pages deben
  servir `.wasm` como `application/wasm`; si el tipo es incorrecto, el motor cae a
  `WebAssembly.instantiate` sobre el arreglo de bytes y sigue funcionando, pero más lento.
* El total son ~17,5 MB en el repositorio (el `.wasm` es el 99% del peso). No se
  publican variantes `mvp` ni `coi`: la primera sólo se necesita en navegadores sin
  soporte de exception handling y la segunda requiere aislamiento cross-origin.

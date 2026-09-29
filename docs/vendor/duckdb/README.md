# Motor DuckDB-Wasm incluido en el repositorio

Archivos derivados del paquete **@duckdb/duckdb-wasm 1.28.0**
(MIT License, © DuckDB Foundation y contribuyentes), publicado en npm.

| Archivo | Origen | Modificado |
| :--- | :--- | :--- |
| `duckdb-browser.mjs` | `@duckdb/duckdb-wasm` reempaquetado con esbuild | **Sí** (ver abajo) |
| `duckdb-browser-eh.worker.js` | `dist/duckdb-browser-eh.worker.js` | No |
| `duckdb-eh.wasm` | `dist/duckdb-eh.wasm` | No |

## Por qué el `.mjs` se reempaqueta y no se copia

El `dist/duckdb-browser.mjs` que publica upstream **no es utilizable directamente
en un navegador**: declara `apache-arrow` como dependencia externa y la importa
con un especificador desnudo.

```js
... from "apache-arrow"
```

Un navegador sólo resuelve rutas que empiecen por `/`, `./` o `../`, de modo que
al importarlo falla con:

```
Failed to resolve module specifier "apache-arrow".
```

El fallo ocurre **antes** de que se descargue el worker o el `.wasm`, así que
todos los archivos pueden existir y responder HTTP 200 mientras la terminal SQL
queda muerta. Copiar `dist/duckdb-browser.mjs` tal cual —que es lo que decía
antes este documento— deja el motor inservible en cualquier navegador.

Lo mismo vale para los CDN: `cdn.jsdelivr.net/.../dist/duckdb-browser.mjs` y
`unpkg.com/.../dist/duckdb-browser.mjs` sirven ese mismo archivo. Por eso
`duckdb_client.js` usa como respaldo los endpoints que sí resuelven
dependencias (`+esm` en jsDelivr, `esm.sh`), y toma el `.wasm` y el worker de
`dist/`, que son archivos sueltos sin ese problema.

## Actualización

```bash
# 1. Bundle autocontenido del módulo principal (inlinea apache-arrow)
mkdir -p /tmp/ddb && cd /tmp/ddb
npm init -y >/dev/null && npm install @duckdb/duckdb-wasm@<versión> apache-arrow@13 esbuild
echo 'export * from "@duckdb/duckdb-wasm";' > entry.mjs
./node_modules/.bin/esbuild entry.mjs --bundle --format=esm --platform=browser \
  --minify --target=es2020 --outfile=duckdb-browser.mjs

# 2. Worker y wasm se copian sin tocar
tar -xzf $(npm pack @duckdb/duckdb-wasm@<versión>) \
  package/dist/duckdb-browser-eh.worker.js package/dist/duckdb-eh.wasm

# 3. Instalar en el repositorio
cp duckdb-browser.mjs                        <repo>/docs/vendor/duckdb/
cp package/dist/duckdb-browser-eh.worker.js  <repo>/docs/vendor/duckdb/
cp package/dist/duckdb-eh.wasm               <repo>/docs/vendor/duckdb/
```

Comprobar siempre que el bundle quedó autocontenido:

```bash
grep -cE 'from"[^"./][^"]*"' docs/vendor/duckdb/duckdb-browser.mjs   # debe dar 0
python3 scripts/audit_interfaz.py                                    # guardián automático
```

`scripts/audit_interfaz.py` falla si el bundle local vuelve a traer imports sin
resolver, de modo que este error no puede repetirse en silencio.

Al cambiar de versión hay que actualizar también `DUCKDB_VERSION` en
`docs/js/duckdb_client.js`, que es la que usan los respaldos por CDN.

## Notas de operación

* El servidor de vista previa (`scripts/preview_no_cache.py`) y GitHub Pages deben
  servir `.wasm` como `application/wasm`; si el tipo es incorrecto, el motor cae a
  `WebAssembly.instantiate` sobre el arreglo de bytes y sigue funcionando, pero más lento.
* El total son ~17,7 MB en el repositorio (el `.wasm` es el 99% del peso). No se
  publican variantes `mvp` ni `coi`: la primera sólo se necesita en navegadores sin
  soporte de exception handling —y se toma del CDN— y la segunda requiere
  aislamiento cross-origin.

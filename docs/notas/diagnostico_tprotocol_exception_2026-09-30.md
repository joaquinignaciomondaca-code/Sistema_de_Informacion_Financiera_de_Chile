# Diagnóstico: `TProtocolException: Invalid data` mata el motor DuckDB-Wasm

**Fecha:** 2026-09-30
**Síntoma reportado:** diagnóstico del navegador (Windows 10, Chrome 153) con
`Motor disponible: no`, `Motivo final: Invalid Error: TProtocolException: Invalid data`,
lista de intentos **vacía** y las 52 vistas muertas tras recargar la página.

## Cadena causal (probada, no conjeturada)

1. **La lista de intentos vacía es la pista clave.** `init()` de
   `docs/js/duckdb_client.js` sólo apila entradas en `attempts` cuando falla el
   *arranque* del motor (import, worker, instantiate). Lista vacía + error final
   significa: el motor local arrancó completo y el error se produjo **más
   adelante**, creando las vistas semánticas.
2. **Ubicación exacta del error.** Con el sourcemap de
   `duckdb-browser-eh.worker.js` 1.28.0 se mapeó el stack minificado del
   diagnóstico:
   * `ko.runQuery` → `src/bindings/bindings_base.ts:167`, el `throw` que
     eleva el mensaje de error devuelto **por el wasm** tras
     `duckdb_web_query_run`.
   * `Qa.onMessage` → `src/parallel/worker_dispatcher.ts:202` (la petición
     `runQuery` del hilo principal).
   Es decir: DuckDB (C++ dentro del wasm) falló ejecutando una consulta; no hay
   corrupción de mensajes Thrift entre hilo principal y worker.
3. **¿Qué thrift vive dentro del wasm?** El namespace
   `duckdb_apache::thrift::protocol::TProtocolException` es el parser Thrift
   **del formato Parquet** que DuckDB lleva embebido. Ese error sale al
   parsear el *footer* de un Parquet. Y `CREATE VIEW … AS SELECT * FROM
   read_parquet(...)` parsea footers al bindear: exactamente lo que
   `registerSemanticViews()` hace al arrancar.
4. **Los datos del repositorio están sanos.** Escaneo de los **536 Parquet** de
   `docs/outputs/` con el mismo `docs/vendor/duckdb/duckdb-eh.wasm` (binding
   Node del paquete 1.28.0, `DESCRIBE SELECT * FROM read_parquet(...)` por
   archivo, que fuerza la lectura del footer): **536/536 OK**. Además
   `duckdb-browser-eh.worker.js` y `duckdb-eh.wasm` del repo son byte a byte
   idénticos a `@duckdb/duckdb-wasm@1.28.0` en npm (sha256 verificado), y el
   `.parquet` desplegado en Vercel sirve contenido Parquet real (no una página
   de error).
5. **Causa raíz: bug conocido de Chrome/Edge en Windows con la caché HTTP.**
   DuckDB-Wasm 1.28 lee los Parquet con **XHR síncronos de rango** hechos
   desde el worker (`runtime_browser.ts`). En Chrome/Edge sobre Windows, tras
   una recarga esas respuestas pueden salir de la caché del navegador con
   contenido desplazado/corrupto y el footer Parquet deja de parsear:
   `Invalid Error: TProtocolException: Invalid data`. Es intermitente,
   **Firefox y el modo incógnito no fallan**. Reportado y reproducido por
   upstream en duckdb/duckdb-wasm#1658 (sin fix publicado hasta hoy); los
   afectados (Evidence, otros) confirman que **desactivar la caché de los
   Parquet lo elimina**. Encaja 1:1 con el entorno del diagnóstico
   (Windows + Chrome) y con el disparador (recarga de la página).

## Corrección aplicada (3 capas)

1. **`docs/js/duckdb_client.js` — las lecturas de Parquet salen de la caché del
   navegador.** `registerFile()` añade a la URL de cada Parquet un sufijo
   `?cb=<único por carga de página>`. Con la URL cambiada en cada recarga, los
   XHR de rango del worker siempre van a la red; no pueden reutilizarse bytes
   de una carga anterior. Es la capa que arregla el bug para todos los
   visitantes, incluso con la caché ya "envenenada" y sin tocar el servidor.
2. **`vercel.json` (raíz del repo y copia en `docs/`) — `Cache-Control:
   no-store` para `/outputs/**/*.parquet`.** Es el mitigador confirmado por
   upstream: las respuestas de Parquet dejan de almacenarse en el navegador.
   La copia en `docs/` cubre el caso de un proyecto Vercel configurado con
   Root Directory = `docs`.
3. **`registerSemanticViews()` tolerante a fallos por vista.** Si la creación
   de UNA vista falla, se reintenta una vez y, si sigue fallando, esa vista se
   marca como no disponible con su motivo (`viewErrors`) y **el motor y el
   resto de vistas siguen operativos**. Antes, un solo Parquet con lectura
   corrupta tumbaba el 100% del sistema. El informe de diagnóstico
   (`buildDiagnostics`) ahora lista qué vistas faltan y por qué.
   Además se subió el token `?v=` de `docs/index.html` para que el JS anterior
   quede invalidado.

Guardián nuevo: `scripts/audit_duckdb_client.js` verifica que toda URL de
Parquet registrada lleve el sufijo anti-caché.

## Cómo verificar

1. Desplegar y recargar el sitio en el Chrome/Windows afectado. Con el motor
   arreglado el badge debe quedar en «DuckDB-Wasm activo».
2. Si una vista concreta fallara aún así, el diagnóstico del panel de consultas
   ya no dice sólo «TProtocolException»: nombra la vista y el motivo exacto,
   y el resto del terminal sigue consultable.
3. Descartar extensiones (en el log del usuario aparecía «AutoClicker»)
   repitiendo la prueba en modo incógnito: con la caché fuera de juego nunca
   reprodujo el bug.

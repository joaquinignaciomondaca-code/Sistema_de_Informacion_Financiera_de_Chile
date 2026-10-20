# Diagnóstico del motor SQL (DuckDB-Wasm) y tiempo de arranque — 2026-10-20

Punto 1 de la checklist de auditoría: reproducir el fallo de inicialización y registrar la etapa exacta.
Script reproducible: `scripts/diagnostico_motor_sql.mjs`.

## Método

- Sitio servido en local (`docs/`, `python3 -m http.server`) y abierto con Chromium headless
  (`@sparticuz/chromium` + `puppeteer-core`, sin acceso a internet más allá de npm).
- Se leen `window.DuckDBClient` (`isReady`, `engineAvailable`, `engineSource`, `engineError`, `attempts`) y
  se ejecuta una consulta real: `SELECT count(*) FROM seguros_lista_entidades`.
- Los CDN (jsDelivr, esm.sh) quedan bloqueados en todos los escenarios, para que el resultado no dependa de la red.
- **Limitación:** no se pudo acceder a la URL publicada (GitHub Pages ni Vercel) desde el sandbox, así que
  **el error exacto de la web publicada no se reprodujo**.

## Resultados

| Escenario | Qué se simula | ¿Queda listo? | Tiempo hasta listo | Estado final |
|---|---|---|---|---|
| `normal` | Todo disponible | Sí | ~1,8 s desde la navegación | Motor `local`, 615 vistas, consulta OK (84 filas, 22 ms) |
| `sin_mjs` | Falla `duckdb-browser.mjs` local y CDN | No (fallo explícito) | ~0,7 s | `engineError` con los 3 intentos y su causa |
| `worker_404` | El worker responde 404 | **No, se cuelga** | nunca (>20 s) | Sin error, sin intentos, `engineError = null` |
| `wasm_404` | El `.wasm` responde 404 | **No, se cuelga** | nunca (>20 s) | Sin error, sin intentos, `engineError = null` |

## Hallazgos

1. **Fallo rápido y bien explicado** cuando no carga el módulo JS: el diagnóstico lista cada intento
   (copia local, jsDelivr, esm.sh). La interfaz muestra ese detalle y un botón de copiar diagnóstico. Esta parte funciona.

2. **Colgado sin error** cuando faltan el worker o el `.wasm`. En la copia vendorizada, `createWorker`
   hace `fetch` del worker y crea el `Worker` desde un Blob con el cuerpo de la respuesta, sin comprobar
   el código HTTP. Un 404 produce un worker con código inválido que nunca responde, y `instantiate` espera
   indefinidamente. El cliente no tiene **ningún timeout de inicialización**, así que `isReady` nunca se activa.
   Consecuencia: el usuario ve el motor "cargando" para siempre, sin mensaje ni causa.

3. **Mensaje vacío ("Motivo no informado.")**: el texto por defecto de `#sql-engine-error` (`docs/index.html`)
   aparece cuando `engineError` es falso. En la ruta de error de `init()`, el motivo siempre es una cadena no vacía,
   así que ese texto solo se ve si el motor nunca registra el error. Esto coincide con la descripción de la auditoría
   ("el motivo no está disponible"), pero **no lo reproduje**: la auditoría no adjuntó la consola.

4. **Botón "Reintentar"**: si la inicialización anterior sigue colgada, reintentar crea otra y no cancela la primera.
   Hay que verificarlo al implementar el timeout.

## Medición del tiempo de arranque (local, caché caliente)

| Etapa | Tiempo |
|---|---|
| Carga de la página (`load`) | ~0,5–0,7 s |
| Importar `duckdb-browser.mjs` | ~0 ms |
| Crear worker | ~3 ms |
| Instanciar motor (compilar `.wasm` de 17,3 MB + inicializar) | ~113 ms |
| Conectar + primera consulta | ~20 ms |
| Registrar 615 vistas (33 manifiestos, `CREATE VIEW`) | ~300 ms (3 corridas: 301, 286, 271 ms) |
| **Total hasta `isReady`** | **~1,8–1,9 s** |

Lectura: la compilación del `.wasm` es barata con caché. El costo grande en una visita real será la
**descarga** de 17,3 MB en frío, que no pude medir aquí (no tengo acceso a la red pública). El registro de
vistas (~0,3 s) corre en cada visita aunque el visitante nunca use SQL.

Nota de entorno: el servidor de Python no soporta peticiones de rango, así que DuckDB avisa
"fall back to full HTTP read" al leer Parquet. Eso afecta a las consultas, no a la inicialización, y
no se sabe si GitHub Pages lo soporta: queda por verificar.

## Opciones más eficientes (por impacto)

1. **Arranque perezoso del motor**: iniciar DuckDB solo al abrir la pestaña SQL, el explorador o la descarga
   que lo necesita, no al cargar la portada. Es el mayor ahorro para quien solo navega. Riesgo: la primera consulta espera el arranque; se puede mostrar progreso.
2. **Registro perezoso de vistas**: crear cada vista la primera vez que la consulta o el explorador la usa.
   Ya existe un mecanismo parecido (`repararVistas`) para vistas faltantes; se reutilizaría. Ahorra ~0,3 s y 33 descargas de manifiesto por visita.
3. **Timeout de inicialización** (p. ej. 20 s) con error explícito, y cancelar el intento anterior antes de reintentar.
   Es obligatorio: sin esto el fallo se ve como "cargando".
4. **Verificar el estado HTTP** del worker y del `.wasm` antes de pasarlos a DuckDB (una petición cada uno, en paralelo).
   Convierte el colgado en un error con causa. Costo: ~2 peticiones extra.
5. **Medir el tamaño transferido real** del `.wasm` en el sitio publicado, y comprobar si el host lo comprime.
   Es el mayor costo en frío y no se puede evaluar desde este sandbox.

Descartado por ahora: cambiar el bundle `eh` por `mvp`. Es más pequeño, pero no medido y más lento en consultas.

## Próximos pasos sugeridos

- Implementar 3 y 4 (cambio pequeño, elimina el colgado).
- Medir 5 en la URL publicada (requiere acceso a la red pública).
- Decidir 1 y 2 según cuántos visitantes llegan sin intención de consultar.

## Actualización: punto 2 aplicado (timeout y verificación HTTP)

Cambios en `docs/js/duckdb_client.js`:

- **Verificación HTTP previa**: antes de crear el worker se comprueba con `HEAD` (con `GET` si el host
  responde 405/501) que el worker y el `.wasm` responden 2xx. Un 404 falla con la causa exacta.
- **Timeout por intento** de 15 s (`DUCKDB_INIT_TIMEOUT_MS`) sobre la creación del motor, con mensaje
  "inicializar el motor: sin respuesta tras 15 s".
- **Motivo siempre legible** (`motivoDe`): ya no puede quedar vacío, aunque el error sea un `Event`.
- **`terminarMotor()`**: libera el worker de un intento fallido y se llama al reintentar, para no dejar
  workers vivos.
- **Tiempo de arranque** en `this.initMs` y en el diagnóstico copiable.

Resultados con `scripts/diagnostico_motor_sql.mjs` (mismo entorno que la tabla de arriba):

| Escenario | Antes | Después |
|---|---|---|
| `normal` | Listo en ~1,8 s, 84 filas | Listo en ~1,8–2,0 s, 84 filas |
| `sin_mjs` | Fallo explícito en ~0,7 s | Igual (~0,6 s) |
| `worker_404` | **Colgado sin error** | Fallo en ~0,6 s: "…worker… respondió HTTP 404" |
| `wasm_404` | **Colgado sin error** | Fallo en ~0,6 s: "…eh.wasm… respondió HTTP 404" |
| `worker_mudo` | **Colgado sin error** | Fallo en ~15,5 s: "inicializar el motor: sin respuesta tras 15 s" |

`scripts/audit_duckdb_client.js` sigue pasando (registro de vistas OK).

Pendiente: verificar en la URL publicada y en un navegador distinto de Chromium (Firefox, Safari).
Si las tres fuentes fallan, el peor caso sigue siendo ~45 s antes del mensaje final.

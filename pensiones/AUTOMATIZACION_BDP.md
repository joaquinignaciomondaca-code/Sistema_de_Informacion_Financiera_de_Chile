# Automatización BDP: extracción incremental con publicación bloqueada

**Revisión: 2026-10-07 · continuación del PR #28.** El PR #28 está fusionado en `main` (`d3e295d4`); sus checks `audit`, `tests`, `automatizacion`, `pruebas` y el preview de Vercel finalizaron correctamente. Esta revisión amplía el staging privado; no modifica los datos AFP publicados ni abre el gate.

## Estado ejecutivo

- Hay código para validar/descargar paquetes ZIP oficiales una vez que se registren las URL reales y evidencia de captura saneada desde la interfaz BDP; incluye revalidación HTTP, continuidad de transferencias, procesamiento CSV por lotes reanudables, revisiones y auditoría de staging.
- El catálogo versionado `config/paquetes_bdp.json` **no contiene URLs** y declara `bloqueado_sin_captura_oficial`. Ningún paquete se ha descargado desde SP en esta revisión. El portal conocido `https://www.spensiones.cl/apps/bdp/index.php` redirige a una página 404 en la consulta web de este entorno; no se observó el formulario ni la petición real del botón.
- La clasificación de 63 códigos/14 familias sigue siendo provisional y proviene del espejo XLSX 2021, no del histórico CSV SP.
- El gate `config/publicacion_bdp.json` sigue bloqueado: faltan originales SP, cotejo, semántica/cobertura histórica y evidencia vigente de redistribución.
- Actions no guarda originales ni Parquet privados como artifacts/caché de un repositorio público. El ciclo de ingesta automática requiere un runner Linux propio, aislado, con el label `bdp-private-stage` y `.local-data/` persistente. La variable de repositorio `BDP_PRIVATE_RUNNER_READY=true` lo habilita explícitamente; hoy no se ha configurado en este cambio.
- No hay nuevos Parquet en `docs/outputs/`, tablas BDP en `data_manifest.json`, vistas DuckDB ni referencias web a manifiestos inexistentes. Vercel no publica datos BDP en este estado.

## Componentes implementados

### 1. Descarga oficial y verificación de integridad

`pensiones/scripts/download_bdp_packages.py` y `config/paquetes_bdp.json`:

- sólo aceptan HTTPS en `spensiones.cl`/subdominios; se vuelve a validar cada redirección y se rechaza salir del dominio, puertos alternativos, credenciales y parámetros de sesión/tokens;
- requieren URL/nombre/fecha y un registro de captura UI saneado, con SHA-256 fijado en el catálogo versionado; el registro debe declarar una petición GET observada con referer BDP, HTTP 200, tipo ZIP/binario y nombre de respuesta coincidente. El hash fija la evidencia revisada, no demuestra por sí solo su autenticidad; no inventan GET/POST, parámetros, tokens o URLs, no automatizan el formulario no observado y no sortean WAF/CAPTCHA;
- revalidan paquetes existentes con `HEAD`/ETag/Last-Modified; descargan de nuevo si cambiaron o si SP no ofrece validadores. Una descarga parcial se reanuda con `Range` + `If-Range` sólo si coincide URL y ETag;
- comprueban límites de tamaño, nombres/rutas del ZIP, miembros CSV, CRC, respuesta ZIP válida y SHA-256. El SHA local protege integridad/reanudación; **si SP no publica una suma oficial, no se presenta como cotejo independiente de SP**;
- dejan ZIPs y sidecars de procedencia bajo `.local-data/pensiones/bdp/originales/`; al refrescar un paquete conservan la versión anterior por SHA-256 en `originales/revisions/<id>/`. El sidecar identifica el origen técnico y el hash; no concede permiso para redistribuir.

Con la configuración actual, el comando es un no-op seguro y explica el bloqueo:

```bash
python -m pensiones.scripts.download_bdp_packages --check-only
```

Sólo después de observar la descarga normal en el navegador y revisar la petición exacta se podrán completar `download_url`, `expected_filename`, `captured_from`, `captured_at`, `capture_evidence`, `capture_sha256` y el estado del catálogo. La evidencia se guarda en `.local-data/pensiones/bdp/evidencia/` y contiene únicamente este esquema saneado (sin cookies, headers, tokens ni cuerpo POST):

```json
{
  "source_page": "https://www.spensiones.cl/apps/bdp/index.php",
  "captured_at": "2026-10-07T12:00:00Z",
  "request_method": "GET",
  "request_url": "https://www.spensiones.cl/ruta/observada.zip",
  "referer": "https://www.spensiones.cl/apps/bdp/index.php",
  "response_status": 200,
  "content_type": "application/zip",
  "response_filename": "nombre_observado.zip"
}
```

En cada entrada del catálogo, `capture_evidence` apunta a esa ruta privada y `capture_sha256` fija su digest. El archivo debe estar también en el runner privado persistente para ingesta; no se sube como artifact. Comparar el registro con la captura real y revisar el cambio sigue siendo una obligación humana: el hash sólo fija el archivo, no es una firma de SP. Si la SP usa sesión/token o una solicitud POST, esta versión se detendrá; se debe implementar el flujo observado de forma explícita, sin copiar credenciales al repositorio.

### 2. Backfill en lotes, reanudación y actualización incremental

`pensiones/scripts/extraer_carteras_afp.py`:

- exige que tanto los originales CSV/ZIP como el staging permanezcan bajo `.local-data/`; no extrae rutas ZIP al filesystem;
- conserva los **18 campos originales como texto** (incluidos signos, separadores y nulos) y añade linaje técnico. No interpreta todavía fechas, precisión, escalas ni unidades;
- calcula hash del CSV lógico, cuenta registros CSV (no líneas físicas) y escribe Parquet Zstd en bloques de 10.000 filas por familia;
- confirma cada lote con particiones y `manifest.json` atómicos. `--max-lotes` y `--minutos` dejan checkpoints; repetir la misma orden con la misma carpeta retoma desde el último lote confirmado. Código de salida `2` significa límite/checkpoint incompleto, no publicación;
- utiliza IDs de revisión por paquete + miembro + SHA-256 + codificación. Repetir fuente idéntica no duplica filas. Si un ZIP revisado cambia, los miembros nuevos se procesan en una revisión aparte y sólo se activan al finalizar todo el paquete; se conservan revisiones anteriores para auditoría;
- `--incremental` requiere un staging ya existente. Procesa los ZIPs/CSV entregados y mantiene activos los paquetes no incluidos. El proceso no inventa filtros mensuales porque el formato de fecha del CSV original sigue pendiente;
- manda códigos desconocidos a `otros_no_clasificados`; no los elimina ni los fuerza a una familia. La tabla de familias sigue siendo provisional.

Ejemplo después de que los originales hayan llegado al directorio privado:

```bash
python -m pensiones.scripts.extraer_carteras_afp \
  --scan .local-data/pensiones/bdp/originales \
  --output .local-data/pensiones/bdp/staging \
  --filas-por-lote 10000 --max-lotes 20 --minutos 240
# Si devuelve 2, repetir con los mismos ZIPs/directorio para continuar.
python -m pensiones.scripts.extraer_carteras_afp \
  --scan .local-data/pensiones/bdp/originales \
  --output .local-data/pensiones/bdp/staging \
  --filas-por-lote 10000 --max-lotes 0 --minutos 300
python -m pensiones.scripts.audit_carteras_afp .local-data/pensiones/bdp/staging
```

Para una actualización desde paquetes guardados, añadir `--incremental`. El extractor no interpreta “los tres paquetes presentes” como prueba de que haya 30 años completos: sólo significa que los tres IDs declarados están activos. La cobertura cronológica real necesita cotejo contra los originales y sus inventarios SP.

### 3. Auditorías y criterios de publicación

`pensiones/scripts/audit_carteras_afp.py` verifica manifiestos, hashes de cada partición, tipos, esquema, rutas, conservación de filas por fuente/familia, clasificación, rango del registro CSV, unicidad del linaje y cobertura agregada. El índice de IDs se construye en SQLite temporal bajo `.local-data/`, no en un set que consuma RAM proporcional a todo el histórico. `--allow-incomplete` y `--allow-quarantine` sólo sirven para inspeccionar checkpoints; no hacen publicable una corrida.

`config/publicacion_bdp.json` enumera cinco evidencias que debe aprobar una revisión humana:

1. descarga oficial y procedencia comprobadas;
2. cotejo de muestras/controles contra originales y publicaciones SP;
3. cobertura y clasificación para todos los años/paquetes;
4. semántica, escalas, signos y precisión de campos validados;
5. condiciones vigentes de redistribución revisadas y permiso aplicable demostrado.

Cada evidencia requiere documento/URL, SHA-256, fecha, revisor, resultado positivo y commit de revisión. Además, se requiere aprobación final. Ninguna variable de Actions, secret, checksum autogenerado o el simple hecho de poder descargar la base sustituye esas evidencias.

`check_publicacion_bdp.py` vuelve a ejecutar la auditoría completa de los tres paquetes, exige sidecars de origen oficial, y devuelve `ready=false` mientras falte cualquier criterio. `publish_bdp.py` vuelve a consultar ese gate antes de escribir; cuando esté autorizado, compila particiones Parquet y manifiestos bajo `docs/outputs/pensiones/bdp/`. Hoy esa carpeta no existe. La publicación de tablas en el explorador, vistas DuckDB y catálogo de descargas se mantiene deliberadamente pendiente de la misma revisión; no se generan tablas vacías.

### 4. GitHub Actions y Vercel

`.github/workflows/pensiones_carteras.yml`:

- PR/push: pruebas sintéticas sin red y chequeo explícito de que el catálogo oficial y el gate siguen bloqueados;
- horario mensual: muestra el estado, sin descargar datos por defecto;
- `workflow_dispatch`: permite pedir auditoría, backfill, incremental o publicación. La extracción sólo se ejecuta en la rama por defecto y si el propietario habilita un runner privado persistente con `BDP_PRIVATE_RUNNER_READY=true`; no usa artifacts/cachés públicos para checkpoints;
- job `publish`: sólo aparece si el gate está listo, ejecuta en el entorno de Actions `pensiones-publicacion`, vuelve a validar antes de generar salidas y confirma únicamente `docs/outputs/pensiones/bdp/`;
- tras el push, llama `VERCEL_DEPLOY_HOOK` si el propietario lo configuró como secret. Sin hook, el workflow avisa que se debe confirmar la integración Git de Vercel; no promete un despliegue por el mero hecho de usar `GITHUB_TOKEN`.

El PR #28 dejó un preview Vercel aprobado; no prueba por sí solo la configuración de producción. Antes de cualquier publicación, confirmar: raíz del proyecto `docs`, configuración estática, rama de producción correcta, integración Git o hook protegido y reviewers requeridos para `pensiones-publicacion`. GitHub Pages permanece como despliegue independiente.

## Pruebas de esta implementación

La suite `pensiones/tests/test_carteras.py` cubre preservación literal CSV/ZIP, lote y reanudación, reingesta idempotente, cambio/supresión de miembros por revisión, actualización incremental, codificación CP1252 y celdas multilínea, cuarentena de códigos, integridad SHA, descarga HTTP reanudable, host/redirecciones y bloqueo de publicación. Se ejecuta sin llamar a SP.

```bash
python -m pip install pyarrow==21.0.0
python -m unittest discover -s pensiones/tests -v
python -m pensiones.scripts.download_bdp_packages --check-only
python -m pensiones.scripts.check_publicacion_bdp
```

## Pendientes externos que no puede resolver este checkout

1. Obtener desde el navegador el enlace/flujo real del botón BDP, nombre de archivo y método HTTP; mantener ese destino bajo la SP, generar por paquete el registro saneado descrito arriba, fijar su SHA-256 en el catálogo y revisarlo. No guardar HAR/cookies/headers completos.
2. Descargar con ese flujo al menos un ZIP original actual, confirmar cabecera/codificación/formatos y luego los tres paquetes históricos; registrar sus hashes.
3. Contrastar reglas/códigos por versión, cobertura corte×AFP×fondo×instrumento y cifras/celdas con SP; no confundir filas con contratos ni suponer una medida monetaria común.
4. Leer las condiciones vigentes de la SP y obtener autorización cuando corresponda. El manual histórico de mayo de 2020 decía que el uso era para investigación y solicitaba no distribuir; Parquet no cambia ese requisito.
5. Configurar el runner privado persistente, la protección de rama/entorno y el proyecto/hook Vercel de producción.
6. Sólo tras lo anterior, integrar las tablas aprobadas al `data_manifest.json`, vistas/diccionario/interfaz y catálogo del SIF mediante un cambio revisado.

**Dictamen de este cambio:** pipeline de staging y guardias implementados y probados sintéticamente; descarga viva, histórico SP, exactitud de datos, autorización de redistribución y publicación siguen **no certificados/bloqueados**. No se añadieron datos SP ni se modificaron salidas públicas AFP.

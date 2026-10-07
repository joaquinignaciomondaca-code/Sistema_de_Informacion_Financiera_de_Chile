# Automatización BDP: extracción incremental con publicación bloqueada

**Revisión: 2026-10-07 · continuación del PR #28.** El PR #28 está fusionado en `main` (`d3e295d4`); sus checks `audit`, `tests`, `automatizacion`, `pruebas` y el preview de Vercel finalizaron correctamente. Esta revisión amplía el staging privado; no modifica los datos AFP publicados ni abre el gate.

**Re-verificación posterior al PR #30 (`aa25f740`), 2026-10-07:** se volvió a comprobar la fuente oficial antes de descargar. El portal BDP sigue respondiendo 404, el catálogo sigue sin URLs ni evidencia y el gate sigue bloqueado. **La ingesta histórica no se inició.** Detalle y comandos en [Re-verificación de fuentes](#re-verificación-de-fuentes-2026-10-07-posterior-al-pr-30).

> **Uso paso a paso:** rutas de destino, órdenes exactas, códigos de salida y condiciones de
> detención están en [GUIA_INGESTA_BDP.md](GUIA_INGESTA_BDP.md). Este documento registra estado
> y evidencia; la guía registra procedimiento.

## Estado ejecutivo

- Hay código para validar/descargar paquetes ZIP oficiales una vez que se registren las URL reales y evidencia de captura saneada desde la interfaz BDP; incluye revalidación HTTP, continuidad de transferencias, procesamiento CSV por lotes reanudables, revisiones y auditoría de staging.
- El catálogo versionado `config/paquetes_bdp.json` **no contiene URLs** y declara `bloqueado_sin_captura_oficial`. Ningún paquete se ha descargado desde SP en esta revisión. El portal conocido `https://www.spensiones.cl/apps/bdp/index.php` redirige a una página 404 en la consulta web de este entorno; no se observó el formulario ni la petición real del botón.
- La clasificación de 63 códigos/14 familias sigue siendo provisional y proviene del espejo XLSX 2021, no del histórico CSV SP.
- El gate `config/publicacion_bdp.json` sigue bloqueado: faltan originales SP, cotejo, semántica/cobertura histórica y evidencia vigente de redistribución.
- Actions no guarda originales ni Parquet privados como artifacts/caché de un repositorio público. El ciclo de ingesta automática requiere un runner Linux propio, aislado, con el label `bdp-private-stage` y `.local-data/` persistente. La variable de repositorio `BDP_PRIVATE_RUNNER_READY=true` lo habilita explícitamente; hoy no se ha configurado en este cambio.
- No hay nuevos Parquet en `docs/outputs/`, tablas BDP en `data_manifest.json`, vistas DuckDB ni referencias web a manifiestos inexistentes. Vercel no publica datos BDP en este estado.

## Re-verificación de fuentes (2026-10-07, posterior al PR #30)

Se volvió a intentar la verificación de la fuente oficial antes de cualquier descarga. **Resultado: no están dadas las condiciones; la ingesta histórica completa de los tres paquetes no se preparó ni se ejecutó. Catálogo y gate permanecen bloqueados.**

### Portal oficial de la Superintendencia

La página institucional vigente <https://www.spensiones.cl/portal/institucional/594/w3-propertyname-621.html> («Estadísticas e Informes») sigue enlazando «Acceso a bases de datos» a `https://www.spensiones.cl/apps/bdp/index.php`, pero esa ruta responde con la página 404 de la SP:

| URL consultada | Resultado observado |
|---|---|
| `https://www.spensiones.cl/apps/bdp/index.php` | redirige a `https://www.spensiones.cl/404%20HTML` («Página no encontrada») |
| `https://www.spensiones.cl/apps/bdp/` | misma 404 |
| `http://www.spensiones.cl/apps/bdp/index.php` | misma 404 |
| `https://www.spensiones.cl/apps/bdp/index.php?menu=sci` | misma 404 |

No se observaron el formulario, los tres enlaces, los nombres de archivo, las fechas ni el método HTTP de descarga. Sin esa observación no existe captura válida y el descargador no tiene nada que ejecutar. No se inventaron URLs, no se automatizó un POST no observado, no se eludió CAPTCHA/WAF y no se usaron enlaces con tokens o credenciales.

### Espejo de terceros (no oficial, no utilizable como fuente)

En `github.com/Sud-Austral/Descargas`, carpeta «Carteras históricas de Inversión de los Fondos de Pensiones» (rama `main`, 27 entradas) hay `cartera_mensual_1996.xlsx` a `cartera_mensual_2021.xlsx` y `docchist.pdf` (378.629 bytes, SHA-256 `2c3153be6f0c68fa86a06a13e16e8efa56f4feb060f9bfdaf65802e89a0147e4`). No contiene 2022 en adelante ni los tres paquetes ZIP del BDP, por lo que **no sustituye** a los originales; el plan ya lo descarta como fuente numérica del backfill.

Ese `docchist.pdf` (manual SP, versión actualizada mayo 2020, 11 páginas) conserva en su nota al pie 1: «Esta base es de uso exclusivo para fines de investigación. Se solicita no distribuir esta información». Es la única condición de uso verificable a la fecha y proviene de un espejo, no de la SP: las **condiciones vigentes siguen sin verificarse** y el criterio `redistribucion_de_datos_y_derivados` no puede aprobarse con ella.

### Estado del repositorio comprobado

- `config/paquetes_bdp.json`: `estado: bloqueado_sin_captura_oficial`; los tres IDs requeridos están presentes y los ocho campos de cada paquete están en `null`.
- `.local-data/` no existe en el checkout: sin `evidencia/`, sin `originales/` y sin `staging/`.
- `config/publicacion_bdp.json`: `bloqueado`, los cinco criterios `pendiente`, `aprobacion_final: null`.
- `docs/outputs/pensiones/bdp/` no existe y `data_manifest.json` no referencia tablas BDP.

### Comandos ejecutados

| Comando | Resultado |
|---|---|
| `python -m pensiones.scripts.download_bdp_packages --check-only` | `ready=false`, salida 0: «Faltan URL/nombre/fecha o evidencia saneada capturada desde la interfaz oficial para: historico_1996_2005, historico_2006_2015, historico_2016_actualidad». No contactó a la SP. |
| `python -m pensiones.scripts.check_publicacion_bdp` | `ready=false`: política bloqueada, los 5 criterios pendientes, «No se entregó un staging auditado», `publicacion_de_datos: "no ejecutada"`. |
| `python -m pensiones.scripts.extraer_carteras_afp --scan .local-data/pensiones/bdp/originales --output .local-data/pensiones/bdp/staging --filas-por-lote 10000 --max-lotes 0 --minutos 300` | salida 3 (sin originales que procesar). No se creó staging ni se inventaron filas. |
| `python -m pensiones.scripts.audit_carteras_afp .local-data/pensiones/bdp/staging` | falla: «Falta manifest.json de staging». |
| `python -m unittest discover -s pensiones/tests -v` | 31 pruebas, OK, sin red. |

No hubo descarga, por lo que no existen filas, fechas ni hashes de paquetes que reportar, y la publicación no está autorizada.

### Códigos de salida del extractor (corrección de esta revisión)

`extraer_carteras_afp.py` reservaba el código 2 al límite/checkpoint reanudable, pero `argparse` también terminaba con 2 ante un uso incorrecto o la ausencia de originales; repetir la orden en ese caso habría girado en bucle sin reanudar nada. Ahora: `0` staging completo, `2` límite con checkpoint íntegro (repetir la misma orden), `3` uso incorrecto o sin originales, `1` error de ingesta. Lo cubren `test_missing_originals_exits_with_usage_code_not_checkpoint_code` y `test_exit_codes_separate_checkpoint_from_complete_staging`.

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

## Preparación para la serie completa (2026-10-07)

### Ensayo general del runbook con una serie sintética (sin datos SP)

Se construyó una serie sintética de los tres paquetes (31 CSV: 1996–2005, 2006–2015 y 2016–2026) bajo `.local-data/` y se ejecutó la secuencia CLI documentada, para comprobar el procedimiento antes de que exista un original real:

| Paso | Comando | Resultado observado |
|---|---|---|
| A | `extraer_carteras_afp … --filas-por-lote 10000 --max-lotes 1 --minutos 300` | salida **2**; `status=incomplete`, `paquetes_procesados=[]` — un paquete a medias no se activa |
| B | la misma orden con `--max-lotes 0 --minutos 300` | salida **0**; `staging_complete`, 868 filas, 31 miembros, 30 lotes en la corrida |
| C | `audit_carteras_afp .local-data/pensiones/bdp/staging` | `estado=staging_completo`, `publicable=False`, `publicacion_bloqueada=True`, `historico_completo_por_paquetes=True`, **`cobertura_historica_certificada=False`**, **`paquetes_oficiales_verificados=[]`** |
| D | `check_publicacion_bdp --staging …/staging` | `ready=False`; a los cinco criterios pendientes se suma **«No todos los paquetes tienen sidecar oficial verificado»** |
| E | aislamiento | no existe `docs/outputs/pensiones/bdp/`; `data_manifest.json` sin referencias BDP; Git sólo ve cambios bajo `pensiones/` |

Conclusión operativa: el backfill, la reanudación por checkpoint y la auditoría funcionan sobre una serie de 31 años, y **el gate no se abre aunque el staging quede completo y auditado**, porque falta el sidecar de una descarga oficial. La presencia de los tres IDs de paquete no certifica cobertura: la auditoría informa cobertura *observada* (en el ensayo: 124 cortes de fecha, 3 AFP, 3 fondos, 7 códigos, 868 combinaciones) y `cobertura_historica_certificada` es `False` por construcción. Los datos sintéticos se eliminaron; `.local-data/` no se versiona.

### Asistente de captura saneada: `registrar_captura_bdp.py`

Convierte lo observado en el navegador en el registro de ocho campos que exige el descargador, calcula su SHA-256 e imprime el bloque exacto para pegar en el catálogo. **No descarga y no modifica `config/paquetes_bdp.json`.**

```bash
python -m pensiones.scripts.registrar_captura_bdp \
  --package-id historico_1996_2005 \
  --request-url https://www.spensiones.cl/ruta/observada.zip \
  --response-filename nombre_observado.zip \
  --captured-at 2026-10-07T12:00:00Z \
  --dry-run
```

Escribe en `.local-data/pensiones/bdp/evidencia/<id>.json`. Rechaza: método distinto de GET, status distinto de 200, Content-Type que no identifique ZIP/binario, referer distinto de la página BDP, hosts fuera de `spensiones.cl`, nombres de archivo inseguros, fechas sin zona horaria, paquetes no requeridos y valores con apariencia de credencial (`token`, `sessionid`, cookies, JWT). Pegar el bloque y revisarlo sigue siendo un paso humano en un pull request; `expected_sha256` se fija después de la primera descarga verificada.

### Lo que todavía falta para «todos los años»

- No hay ningún original: la cobertura real por año sólo se certifica con el inventario de cada ZIP oficial y el cotejo contra SP.
- El extractor todavía **no particiona por año** (`familia/anio=AAAA/…`); quedó pendiente de validar el formato de fecha del CSV SP, que no se ha observado.
- El espejo XLSX de terceros no sirve como entrada: `extraer_carteras_afp.py` lo rechaza explícitamente («Sólo se aceptan originales CSV o ZIP; no espejos XLSX»).

### Descarga mediante token opaco: decisión pendiente

En la página oficial de cartera desagregada (que sí responde) el botón «Versión completa en formato Zip» apunta a `https://www.spensiones.cl/apps/GetFile_v2.0.php?param=<cadena base64 larga>`. Si el BDP usa el mismo mecanismo, hay que decidirlo antes de tocar el catálogo:

- `validate_official_https_url` **acepta** `?param=` (rechaza `token`, `sessionid`, `csrf`, `expires`, `signature`, JWT y similares). Nada avisaría por sí solo.
- Si `param` fuera un token por sesión, fijarlo en `config/paquetes_bdp.json` publicaría una credencial en un repositorio **público con licencia MIT**. `registrar_captura_bdp.py` no lo detecta por nombre de parámetro: la revisión humana debe mirarlo.
- El descargador **no** concatena respuestas incompatibles: reanudar exige huella de URL coincidente y ETag fuerte, y si el servidor ignora `Range` o el objeto cambió, descarta el parcial y repite una solicitud completa. El riesgo no es corruptela de datos: es la fugacidad del enlace y la eventual credencial en Git.
- `catalog_status` no hace solicitudes de red: `ready=true` afirma que el catálogo está completo y su evidencia coincide en hash, no que el enlace siga vivo.

Decisión a tomar al observar el flujo real: si `param` es un identificador público estable, se fija en el catálogo; si es de sesión, la URL debe entregarse en tiempo de ejecución (variable de entorno o archivo privado) y el catálogo guardar sólo un localizador no sensible.

### Condiciones de uso y redistribución: qué se verificó

- Manual SP «Base de Cartera de los Fondos de Pensiones», versión mayo 2020 (obtenido del espejo de terceros, `docchist.pdf`, 11 páginas), nota al pie 1: «Esta base es de uso exclusivo para fines de investigación. Se solicita no distribuir esta información». Restringe el **propósito** y la **distribución**; no está condicionada a que exista ánimo de lucro.
- La página oficial de cartera desagregada muestra: «Copyright © 2026, American Bankers Association. CUSIP Database provided by FactSet Research Systems Inc. All rights reserved.» Reserva de derechos de terceros, independiente del uso comercial.
- Este repositorio es **público y de licencia MIT**, que concede a terceros «use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies». Publicar datos de la SP aquí chocaría con ambas restricciones, haya o no intención comercial.
- En `datos.gob.cl` la SP mantiene 8 conjuntos (XLS/HTML, creados y actualizados en 2015) bajo una licencia que la consulta muestra truncada como «Creative Commons No…» y debe confirmarse; **ninguno es la cartera histórica BDP**.
- Las condiciones **vigentes** siguen sin verificarse: el portal que aloja el manual actual responde 404.

Conclusión: usar los datos localmente para investigación no es el obstáculo; **publicarlos o redistribuirlos sí lo es**, y no se resuelve declarando ausencia de fin comercial. Sólo una condición vigente verificada o una autorización escrita de la SP desbloquea el criterio `redistribucion_de_datos_y_derivados`.

## Pendientes externos que no puede resolver este checkout

1. Obtener desde el navegador el enlace/flujo real del botón BDP, nombre de archivo y método HTTP; mantener ese destino bajo la SP, generar por paquete el registro saneado descrito arriba, fijar su SHA-256 en el catálogo y revisarlo. No guardar HAR/cookies/headers completos.
2. Descargar con ese flujo al menos un ZIP original actual, confirmar cabecera/codificación/formatos y luego los tres paquetes históricos; registrar sus hashes.
3. Contrastar reglas/códigos por versión, cobertura corte×AFP×fondo×instrumento y cifras/celdas con SP; no confundir filas con contratos ni suponer una medida monetaria común.
4. Leer las condiciones vigentes de la SP y obtener autorización cuando corresponda. El manual histórico de mayo de 2020 decía que el uso era para investigación y solicitaba no distribuir; Parquet no cambia ese requisito.
5. Configurar el runner privado persistente, la protección de rama/entorno y el proyecto/hook Vercel de producción.
6. Sólo tras lo anterior, integrar las tablas aprobadas al `data_manifest.json`, vistas/diccionario/interfaz y catálogo del SIF mediante un cambio revisado.

**Dictamen de este cambio:** pipeline de staging y guardias implementados y probados sintéticamente; descarga viva, histórico SP, exactitud de datos, autorización de redistribución y publicación siguen **no certificados/bloqueados**. No se añadieron datos SP ni se modificaron salidas públicas AFP.

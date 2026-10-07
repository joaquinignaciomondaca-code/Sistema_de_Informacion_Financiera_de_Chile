# Guía operativa: ingesta histórica BDP (AFP)

**Estado: el pipeline está implementado y probado, pero no se ha ejecutado contra datos reales.**
Esta guía describe cómo se usa cuando existan originales oficiales. Es sólo código y
procedimiento: **no contiene, genera ni referencia datos de la Superintendencia.**

Estado de fuentes, bloqueos y evidencia: [AUTOMATIZACION_BDP.md](AUTOMATIZACION_BDP.md).
Diseño de tablas y semántica: [PLAN_EXTRACCION_CARTERAS_BDP.md](PLAN_EXTRACCION_CARTERAS_BDP.md).

---

## 1. Dónde queda cada cosa

Todo lo pesado vive bajo `.local-data/`, que está en `.gitignore` y **no se versiona, no se
sube como artifact de Actions ni se publica en el sitio**.

```
.local-data/pensiones/bdp/
├── evidencia/                     ← registro saneado de captura UI (JSON, 8 campos)
│   └── <paquete>.json
├── originales/                    ← ZIP oficiales + sidecar de procedencia
│   ├── <paquete>.zip
│   ├── <paquete>.zip.source.json  ← sidecar: URL sin query, fecha, SHA-256, ETag
│   └── revisions/<paquete>/       ← versión anterior conservada al refrescar
└── staging/                       ← salida del backfill (privada)
    ├── manifest.json              ← paquetes, revisiones activas, fuentes, hashes
    ├── audit.json                 ← resumen de la última corrida
    └── revisions/<revision_id>/<familia>/batch-000001.parquet
```

| Contenido | Ruta | ¿En Git? | ¿En el sitio? |
|---|---|---|---|
| Evidencia de captura | `.local-data/pensiones/bdp/evidencia/` | No | No |
| ZIP originales y sidecars | `.local-data/pensiones/bdp/originales/` | No | No |
| Staging Parquet, manifest, checkpoints | `.local-data/pensiones/bdp/staging/` | No | No |
| Índice SQLite temporal de la auditoría | `.local-data/bdp-audit-*/` (se borra solo) | No | No |
| Catálogo de fuentes (sin datos) | `pensiones/config/paquetes_bdp.json` | **Sí** | No |
| Política de publicación (sin datos) | `pensiones/config/publicacion_bdp.json` | **Sí** | No |
| Salida pública *(bloqueada, hoy no existe)* | `docs/outputs/pensiones/bdp/` | — | — |

El staging **no particiona por año todavía**: las particiones son por revisión y familia. La
partición anual quedó pendiente de validar el formato de fecha del CSV original.

## 2. Secuencia de uso

Requisito previo: `python -m pip install pyarrow==21.0.0`.

### Paso 0 — Comprobar el estado sin tocar la red

```bash
python -m pensiones.scripts.download_bdp_packages --check-only
python -m pensiones.scripts.check_publicacion_bdp
```

Ambos imprimen JSON. Mientras falte captura oficial, el primero responde
`"ready": false` con estado `bloqueado_sin_captura_oficial` y **no hace ninguna solicitud**.
Si `ready` no es `true`, detenerse aquí.

### Paso 1 — Observar la descarga en el navegador (manual, humano)

Abrir el portal oficial, accionar el botón de cada paquete y anotar de la pestaña Network:
URL exacta, nombre de archivo con que respondió, fecha/hora, método, código de estado y
Content-Type. **No copiar cookies, headers ni cuerpo de petición.**

Si el flujo resulta ser POST, requerir sesión o entregar un enlace con token, **detenerse**:
este pipeline sólo automatiza un GET observado. Ver la sección de token opaco en
[AUTOMATIZACION_BDP.md](AUTOMATIZACION_BDP.md).

### Paso 2 — Registrar la evidencia saneada (por paquete)

```bash
python -m pensiones.scripts.registrar_captura_bdp \
  --package-id historico_1996_2005 \
  --request-url https://www.spensiones.cl/ruta/observada.zip \
  --response-filename nombre_observado.zip \
  --captured-at 2026-10-07T12:00:00Z \
  --dry-run
```

Sin `--dry-run` escribe `.local-data/pensiones/bdp/evidencia/<paquete>.json`, calcula su
SHA-256 e imprime el bloque listo para pegar en `pensiones/config/paquetes_bdp.json`.
Rechaza POST, estado ≠ 200, Content-Type que no sea ZIP/binario, referer ajeno, hosts fuera
de `spensiones.cl`, rutas inseguras, fechas sin zona y valores con apariencia de credencial.

**Pegar el bloque y revisarlo en un pull request es un paso humano.** El script nunca
modifica el catálogo por su cuenta.

Al terminar los tres paquetes, la revisión humana debe cambiar `"estado"` en
`pensiones/config/paquetes_bdp.json` de `bloqueado_sin_captura_oficial` a **`listo`**. Sin ese
valor `load_catalog` responde `CatalogNotReady` y el descargador no arranca, aunque las URLs y
la evidencia estén completas: es el candado explícito de que alguien revisó la captura.

### Paso 3 — Descargar

```bash
python -m pensiones.scripts.download_bdp_packages \
  --output .local-data/pensiones/bdp/originales
```

Vuelve a validar el host en cada redirección, comprueba límites de tamaño, rutas y CRC del
ZIP, inventaría los miembros CSV y verifica el SHA-256 contra el catálogo. Deja ZIP y sidecar
en `originales/`; al refrescar, conserva la versión anterior en `originales/revisions/<id>/`.

Dos comportamientos que conviene saber:

- Si el ZIP ya existe y su sidecar es válido, revalida con `HEAD`/ETag/`Last-Modified` y omite
  la descarga si nada cambió. Si la SP no implementa HEAD, vuelve a descargar y validar: nunca
  conserva un ZIP sólo porque la URL no cambió.
- Si `expected_sha256` del catálogo **no** coincide con el ZIP local, re-descarga de inmediato
  sin consultar HEAD. Es más estricto, no menos: un hash nuevo en el catálogo se trata como
  revisión pendiente, no como caché válida.

### Paso 4 — Backfill por lotes

```bash
python -m pensiones.scripts.extraer_carteras_afp \
  --scan .local-data/pensiones/bdp/originales \
  --output .local-data/pensiones/bdp/staging \
  --filas-por-lote 10000 --max-lotes 0 --minutos 300
```

| Código | Significado | Qué hacer |
|---|---|---|
| `0` | staging completo | continuar al paso 5 |
| `2` | límite de lotes o de tiempo alcanzado, checkpoint íntegro | **repetir la misma orden** para reanudar |
| `3` | uso incorrecto o no hay originales | revisar rutas; no hay nada que reanudar |
| `1` | error de ingesta | leer el mensaje; no reintentar a ciegas |

Un paquete a medias **no se activa**: sigue en `paquetes_pendientes` hasta completar todos
sus miembros. `--incremental` exige un staging ya existente; no usarlo para inicializar uno vacío.

Cómo leer el JSON de salida:

- `paquetes_procesados` son los paquetes **activos en el staging** (`sorted(manifest["packages"])`),
  no los procesados en esta corrida. El nombre induce a error.
- `miembros_procesados_en_corrida` y `lotes_confirmados_en_corrida` sí son de la corrida.
  Una reingesta de la misma fuente da `0` miembros: es idempotente.
- `filas_activas` es el total del staging, no el delta de la corrida.

Opciones útiles: `--package-id` (repetible, para CSV/ZIP sin sidecar), `--encoding cp1252`,
`--max-archivos` (máximo de miembros CSV por corrida, por defecto 50).

### Paso 5 — Auditar el staging

```bash
python -m pensiones.scripts.audit_carteras_afp .local-data/pensiones/bdp/staging
```

Verifica manifiestos, hash de cada partición, esquema, rutas privadas, conservación de filas
por fuente y familia, clasificación, rango del registro CSV y cobertura observada. Construye
su índice de IDs en SQLite temporal bajo `.local-data/`, no en memoria.

Campos que hay que leer juntos:

- `historico_completo_por_paquetes` — los tres IDs están activos. **No es cobertura certificada.**
- `cobertura_historica_certificada` — siempre `false`; la certificación es una revisión humana.
- `paquetes_oficiales_verificados` — cuáles tienen sidecar de una descarga oficial real.
- `codigos_no_clasificados` — cuarentena; si no está vacío, bloquea la certificación.

**La auditoría falla a propósito (código 1) si hay cuarentena o paquetes en curso.** El mensaje
es `Hay códigos sin clasificar; se conservan en cuarentena y bloquean la auditoría`. Para
inspeccionar el detalle hay que pedirlo explícitamente:

```bash
python -m pensiones.scripts.audit_carteras_afp .local-data/pensiones/bdp/staging --allow-quarantine
```

`--allow-incomplete` y `--allow-quarantine` sólo permiten *leer* el estado; no vuelven
publicable una corrida ni cambian `publicable`, que es `false` por construcción.

### Paso 6 — Evaluar el gate (no publicar)

```bash
python -m pensiones.scripts.check_publicacion_bdp \
  --staging .local-data/pensiones/bdp/staging
```

Devuelve `ready` y la lista de razones. Con el staging completo pero sin sidecars oficiales
añade: *«No todos los paquetes tienen sidecar oficial verificado»*.

`publish_bdp.py` vuelve a consultar este gate antes de escribir y es el único camino a
`docs/outputs/pensiones/bdp/`. Requiere las cinco evidencias aprobadas por revisión humana en
`config/publicacion_bdp.json`. Ninguna variable de Actions, secret o bandera de workflow
sustituye esa aprobación.

## 3. Qué nunca ocurre automáticamente

- No se descubren endpoints, no se envían formularios, no se elude CAPTCHA/WAF.
- No se extraen rutas de ZIP al filesystem; los miembros se leen en memoria.
- No se interpretan fechas, escalas, signos ni unidades: los 18 campos se conservan como texto.
- No se escribe nada en `docs/outputs/`, `data_manifest.json` ni el sitio.
- No se ejecuta código contenido en los paquetes.
- Un código de salida `2` no significa publicación; significa checkpoint.

## 4. Verificación sin datos oficiales

Dos comprobaciones complementarias, ambas sin red:

```bash
python -m pip install pyarrow==21.0.0

# Pruebas unitarias y de integración (35)
python -m unittest discover -s pensiones/tests -v

# Verificación punta a punta del procedimiento completo (37 comprobaciones)
python -m pensiones.scripts.verificar_pipeline_bdp
```

`verificar_pipeline_bdp` ejercita el código real —asistente de captura, descargador, extractor,
auditoría y gate— sobre fuentes sintéticas servidas por un transporte HTTP inyectado. El único
punto sustituido es el socket; la validación de host, el registro saneado, el inventario ZIP/CRC,
el SHA-256, los sidecars, los lotes con checkpoint, la cuarentena, las revisiones y el gate son
las funciones del repositorio. Cubre:

- catálogo bloqueado responde `ready=false` sin hacer solicitudes;
- evidencia saneada y rechazo de URLs con token;
- descarga, inventario, SHA-256 cotejado y sidecars `redistribution_status=not_reviewed`;
- salida `2` con checkpoint, reanudación a `0`, `3` sin originales, reingesta idempotente;
- auditoría fail-closed ante cuarentena y `cobertura_historica_certificada=false`;
- gate bloqueado aun con staging completo y sidecars oficiales;
- revalidación HEAD, conservación de revisión anterior e incremental sin duplicar filas;
- aislamiento: nada en `docs/outputs/`, nada visible para Git, manifiesto público intacto.

Trabaja en `.local-data/pensiones/bdp-verificacion/`, se borra solo al terminar y **se niega a
correr si ya existen originales o staging reales**, para no pisar una ingesta en curso.

Esta verificación prueba que el procedimiento funciona. **No certifica datos reales**: no hay
originales SP, no hay cotejo de cifras y el gate sigue cerrado.

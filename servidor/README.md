# Servidor HTTP de consultas SQL (fase 3)

SQL de solo lectura sobre los mismos Parquet publicados, para quien no quiere
descargar los ≈488 MB ni ejecutar DuckDB en su máquina. Es **otra forma de leer**
lo publicado: no sustituye al contrato estático (`docs/api/v2/`) ni a la web, que
siguen siendo estáticos y sin backend. Este proceso es opcional y se autoaloja.

> Estado: implementado y probado en **modo local** contra los Parquet reales del
> repositorio (`servidor/tests`, 101 pruebas). El **modo remoto** (httpfs contra
> el sitio publicado) está configurado pero no se pudo ejercitar en el entorno de
> desarrollo: `extensions.duckdb.org` está bloqueado y la extensión httpfs no
> viene instalada. Se documenta como no verificado aquí.

## Arranque rápido

```bash
pip install -r servidor/requirements.txt
pip install -e sdk/python

# Modo local: una carpeta con el contenido de docs/ (sin red).
SIF_CHILE_BASE=docs python -m servidor
# → http://localhost:8000/docs
```

```bash
# Modo remoto: lee los Parquet del sitio publicado por HTTP Range.
# Necesita la extensión httpfs de DuckDB (se instala la primera vez).
SIF_CHILE_BASE=https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile \
  python -m servidor
```

## Rutas

| Ruta | Qué devuelve |
|---|---|
| `GET /` | descriptor del servicio, versión, modo y límites |
| `GET /health` | salud, `data_release`, objetos y vistas |
| `GET /v2/catalog` | el catálogo del contrato (90 objetos) |
| `GET /v2/schema/{id}` | esquema de un objeto (o alias) |
| `GET /v2/partitions/{id}` | particiones, bytes y SHA-256 |
| `GET /v2/queries` | las 159 consultas de ejemplo |
| `GET /v2/resultados` | índice de resultados precalculados |
| `GET /v2/resultado/{id}` | un resultado precalculado |
| `GET/POST /v2/query` | **SQL de lectura** con límites |
| `GET /docs`, `/openapi.json` | documentación interactiva y OpenAPI |

`/v2/query` acepta `{"sql": "...", "limite": 100}` por POST, o `?sql=...&limite=...`
por GET. Devuelve `{ok, class, columnas, filas, datos, truncado, celdas_recortadas,
ms, data_release, limite}`. Los errores usan el sobre
`{ok:false, class, reason, next, retry}` (mismo vocabulario que api-anything):

| `class` | HTTP | Significado |
|---|---|---|
| `input` | 400 / 404 | SQL inválido, columna inexistente, id desconocido |
| `refused` | 403 | el guardia rechaza la consulta (escritura, archivo, red) |
| `auth` | 401 | falta el token Bearer o es incorrecto |
| `rate` | 429 / 503 | rate-limit por IP o pool ocupado (`Retry-After`) |
| `timeout` | 504 | la consulta superó `SIF_API_TIMEOUT_S` |
| `error` | 500 | error interno |

## Configuración

| Variable | Defecto | Para qué |
|---|---|---|
| `SIF_CHILE_BASE` | sitio publicado | carpeta local (`docs/`) o URL remota |
| `SIF_API_TOKEN` | vacío | si se define, exige `Authorization: Bearer <token>` |
| `SIF_API_MAX_FILAS` | 1000 | tope de filas por consulta |
| `SIF_API_FILAS_DEFECTO` | 100 | filas si no se pide `limite` |
| `SIF_API_MAX_CELDA` | 1000 | caracteres por celda antes de recortar |
| `SIF_API_MAX_SQL` | 20000 | caracteres máximos de SQL |
| `SIF_API_TIMEOUT_S` | 10 | timeout por consulta (`interrupt()`) |
| `SIF_API_POOL` | 4 | cursores DuckDB concurrentes |
| `SIF_API_RATE_BURST` | 20 | ráfaga por IP |
| `SIF_API_RATE_MIN` | 60 | recarga por minuto por IP |
| `SIF_API_MEMORY_LIMIT` | 1GB | memoria de DuckDB |
| `SIF_CORS_ORIGINS` | `*` | orígenes CORS separados por coma |
| `SIF_API_TRUST_PROXY` | 0 | si 1, usa `X-Forwarded-For` para el rate-limit |
| `SIF_LOG_SQL` | 0 | si 1, registra el SQL; por defecto solo su hash |
| `SIF_API_HOST` / `SIF_API_PORT` | `0.0.0.0` / `8000` | bind de uvicorn |

## Modelo de amenazas (léelo antes de exponerlo)

El guardia del SDK es una conveniencia para uso local; **no** es una frontera de
seguridad. Este servidor añade un guardia **AST fail-closed** (`guardia.py`):
parsea con `json_serialize_sql` de DuckDB y solo permite

- una sentencia SELECT/WITH/VALUES/TABLE/DESCRIBE/SHOW/SUMMARIZE;
- relaciones que sean vistas del contrato o CTEs de la propia consulta;
- funciones escalares/aggregate/window del núcleo, menos las que tienen efectos
  o leen configuración (`setseed`, `nextval`, `current_setting`, `getvariable`,
  `json_serialize_sql`, …);
- **ninguna** función de tabla (`read_text`, `glob`, `read_parquet`, `query`,
  `sqlite_scan`, …) ni *replacement scans* (`FROM 'archivo'`), estén anidados,
  tras coma o calificados (`main.read_text`).

Defensa en profundidad:

- `lock_configuration=true` en la conexión madre (se hereda a los cursores):
  nadie puede cambiar `threads`, `memory_limit` ni reactivar filesystems.
- Modo remoto: `disabled_filesystems='LocalFileSystem'` y autoinstall/autoload de
  extensiones apagados tras cargar httpfs.
- Modo local: `allowed_directories` apunta a la carpeta de datos. **Ojo:** en
  DuckDB 2.0 `allowed_directories` no bloquea `glob`/`read_text` (verificado); por
  eso el guardia AST es quien cierra esas funciones, no el setting.
- Docker: usuario `nobody`, `read_only`, `tmpfs /tmp`, `mem_limit 2g`, TLS en Caddy.
- Rate-limit por IP, pool acotado, timeout por `interrupt()` y tope de filas.

Aun así: es un servicio best effort, sin SLA. Si lo expones a Internet, pon
`SIF_API_TOKEN`, restringe `SIF_CORS_ORIGINS` y vigila el consumo. Los datos son
públicos y se republican normalizados: cita la fuente (ver `/v2/catalog`).

## Docker

```bash
docker build -f servidor/Dockerfile -t sif-api .
docker run --rm -p 8000:8000 -e SIF_API_TOKEN=$(openssl rand -hex 24) sif-api

# O con Caddy (TLS) y modo local:
SIF_CHILE_BASE=/datos SIF_API_TOKEN=… docker compose -f servidor/compose.yaml up --build
```

## Pruebas

```bash
pip install -r servidor/requirements-dev.txt   # runtime + httpx2 (TestClient) + pytest
pip install -e sdk/python
PYTHONPATH=sdk/python:. python -m pytest servidor/tests -q
```

`requirements-dev.txt` existe porque `fastapi.testclient.TestClient` necesita un
cliente HTTP (`httpx2`) que **no** viene con fastapi ni con starlette: sin él, la
colección de pytest falla en `conftest.py`. El runtime (`requirements.txt`) no lo
arrastra a propósito.

Corren contra los Parquet reales de `docs/outputs` en modo local: guardia AST
(legítimas y ataques), motor (consulta real, truncado, serialización, timeout y
reuso del cursor, pool ocupado, lock) y HTTP (rutas, auth, rate-limit, CORS,
OpenAPI, ausencia de `X-Frame-Options`).

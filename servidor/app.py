"""Servidor HTTP de consultas SQL de solo lectura sobre el contrato SIF Chile.

Es la **fase 3** que `docs/api/servidor/README.md` dejó escrita como receta: un
proceso pequeño que ejecuta SQL de lectura sobre los mismos Parquet publicados,
para quien no quiere descargar los ≈488 MB ni ejecutar DuckDB en su máquina.

No sustituye al contrato estático ni a la web: el sitio sigue siendo estático y
las consultas del navegador siguen corriendo en local. Este servidor es **otra
forma de leer** lo publicado, pensada para autoalojarse (Docker + Caddy). El
contrato que sirve (`/v2/catalog`, `/v2/schema/{id}`, …) es el mismo que genera
`scripts/build_contrato.py`; la ruta nueva es `/v2/query`.

Dos modos, según `SIF_CHILE_BASE`:

  * **local** — una carpeta con el contenido de `docs/`. DuckDB lee los Parquet
    del disco; el guardia AST bloquea funciones de archivo y `lock_configuration`
    acota el proceso. Es el modo de las pruebas y del preview, y no necesita red.
  * **remoto** — la URL del sitio publicado. DuckDB lee los Parquet por HTTP
    Range (httpfs); se deshabilita `LocalFileSystem` para que el proceso no pueda
    tocar su propio disco. Requiere descargar la extensión httpfs la primera vez.

Defensa en profundidad (ver `guardia.py` y `README.md`): guardia AST fail-closed,
`lock_configuration`, tope de filas, timeout por `interrupt()`, pool acotado de
cursores, rate-limit por IP, token opcional y usuario sin privilegios en Docker.

    pip install -r servidor/requirements.txt
    SIF_CHILE_BASE=docs python -m servidor          # local, sin red
    # → http://localhost:8000/docs
"""
from __future__ import annotations

import datetime as dt
import decimal
import hashlib
import hmac
import json
import logging
import math
import os
import queue
import re
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import duckdb
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from sif_chile import cliente as _cliente

from .guardia import GuardiaAST

VERSION = "1.0.0"
CONTRATO = "v2"
LOG = logging.getLogger("servidor")

_ID_OBJETO = re.compile(r"^[a-z0-9_]+$")
_ID_RESULTADO = re.compile(r"^[a-z0-9-]+$")


def _env_int(nombre: str, defecto: int) -> int:
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        return defecto
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser un entero, no «{valor}»") from exc


def _env_float(nombre: str, defecto: float) -> float:
    valor = os.environ.get(nombre)
    if valor is None or valor == "":
        return defecto
    try:
        return float(valor)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser un número, no «{valor}»") from exc


class Limites:
    """Límites del servicio, leídos del entorno una sola vez al crear la app."""

    def __init__(self, **kw: Any) -> None:
        self.max_filas = kw.get("max_filas") or _env_int("SIF_API_MAX_FILAS", 1000)
        self.filas_defecto = kw.get("filas_defecto") or _env_int("SIF_API_FILAS_DEFECTO", 100)
        self.max_celda = kw.get("max_celda") or _env_int("SIF_API_MAX_CELDA", 1000)
        self.max_sql = kw.get("max_sql") or _env_int("SIF_API_MAX_SQL", 20000)
        self.timeout_s = kw.get("timeout_s") or _env_float("SIF_API_TIMEOUT_S", 10.0)
        self.pool = kw.get("pool") or _env_int("SIF_API_POOL", 4)
        self.rate_burst = kw.get("rate_burst") or _env_int("SIF_API_RATE_BURST", 20)
        self.rate_min = kw.get("rate_min") or _env_int("SIF_API_RATE_MIN", 60)
        self.memoria = kw.get("memoria") or os.environ.get("SIF_API_MEMORY_LIMIT", "1GB")
        for nombre in ("max_filas", "filas_defecto", "max_celda", "max_sql", "pool",
                       "rate_burst", "rate_min"):
            if getattr(self, nombre) < 1:
                raise ValueError(f"{nombre} debe ser >= 1")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s debe ser > 0")
        if self.filas_defecto > self.max_filas:
            self.filas_defecto = self.max_filas


class Motor:
    """Pool de cursores DuckDB sobre las vistas del contrato, endurecido.

    Una conexión madre registra las vistas y fija la configuración; los cursores
    del pool heredan el catálogo y el `lock_configuration`, y cada uno fija su
    propia variable `sif_base` (las variables no se heredan entre cursores).
    """

    def __init__(self, base: str | None = None, limites: Limites | None = None) -> None:
        self.limites = limites or Limites()
        valor = base or os.environ.get("SIF_CHILE_BASE") or _cliente.BASE_CANONICA
        self.base, self.local = _normalizar(valor)
        self._cerrado = False
        # El SDK normaliza una carpeta a file://, pero no acepta que le pasen ya
        # la URI: en modo local le damos la ruta de filesystem.
        base_sdk = urlsplit(self.base).path if self.local else self.base
        self._lectura = _cliente.Sif(base=base_sdk, conectar=False)
        self.catalogo = self._lectura.catalogo
        self.data_release = self.catalogo.get("data_release")
        self._con = duckdb.connect()
        self._configurar()
        self._pool: queue.Queue = queue.Queue(maxsize=self.limites.pool)
        for _ in range(self.limites.pool):
            self._pool.put(self._nuevo_cursor())
        tablas = self._con.execute("SHOW TABLES").fetchall()
        self._n_vistas = len(tablas)
        self.guardia = GuardiaAST(relaciones=[t[0] for t in tablas])

    def _configurar(self) -> None:
        con = self._con
        con.execute(f"SET threads = {max(1, self.limites.pool)}")
        con.execute(f"SET memory_limit = '{self.limites.memoria}'")
        if not self.local:
            # Modo remoto: httpfs para leer por HTTP Range y sin disco local.
            try:
                con.execute("INSTALL httpfs; LOAD httpfs;")
            except duckdb.Error as exc:
                raise RuntimeError(
                    "El modo remoto necesita la extensión httpfs de DuckDB y no se "
                    f"pudo cargar: {str(exc).splitlines()[0][:200]}. Instala la "
                    "extensión o usa SIF_CHILE_BASE con una carpeta local."
                ) from exc
            con.execute("SET disabled_filesystems = 'LocalFileSystem'")
            con.execute("SET autoinstall_known_extensions = false")
            con.execute("SET autoload_known_extensions = false")
        else:
            # Modo local: acotar el disco a la carpeta de datos. DuckDB 2.0 no
            # bloquea glob/read_text con allowed_directories (verificado), así que
            # el guardia AST es quien cierra esas funciones; esto acota el resto.
            ruta = urlsplit(self.base).path
            con.execute("SET allowed_directories = [?]", [ruta])
        con.execute("SET lock_configuration = true")
        ddl = self._lectura._leer("api/v2/views.sql").decode("utf-8")
        con.execute(self._reescribir_base(ddl))

    def _reescribir_base(self, ddl: str) -> str:
        base = self.base.replace("'", "''")
        lineas = []
        for linea in ddl.splitlines():
            if linea.strip().startswith("SET VARIABLE sif_base"):
                lineas.append(f"SET VARIABLE sif_base = '{base}';")
            else:
                lineas.append(linea)
        return "\n".join(lineas)

    def _nuevo_cursor(self):
        cur = self._con.cursor()
        cur.execute("SET VARIABLE sif_base = ?", [self.base])
        return cur

    def consultar(self, sql: str, limite: int | None = None) -> dict[str, Any]:
        """Ejecuta una consulta de lectura y devuelve el sobre de respuesta."""
        if sql is None or not str(sql).strip():
            raise ValueError("La consulta está vacía.")
        sql = str(sql)
        if len(sql) > self.limites.max_sql:
            raise ValueError(f"La consulta supera el tope de {self.limites.max_sql} caracteres.")
        self.guardia.exigir(sql)
        limite = self.limites.filas_defecto if limite is None else int(limite)
        if limite < 1 or limite > self.limites.max_filas:
            raise ValueError(f"limite debe estar entre 1 y {self.limites.max_filas}.")
        try:
            cur = self._pool.get(timeout=min(2.0, self.limites.timeout_s))
        except queue.Empty:
            raise Ocupado("El servidor está atendiendo otras consultas.") from None
        t0 = time.perf_counter()
        hecho = threading.Event()

        def _interrumpir() -> None:
            if not hecho.is_set():
                cur.interrupt()

        temporizador = threading.Timer(self.limites.timeout_s, _interrumpir)
        temporizador.start()
        try:
            cur.execute(sql)
            columnas = [d[0] for d in cur.description]
            filas = cur.fetchmany(limite + 1)
        except duckdb.InterruptException:
            raise Timeout(
                f"La consulta superó el tiempo máximo de {self.limites.timeout_s:g} s."
            ) from None
        finally:
            hecho.set()
            temporizador.cancel()
            self._pool.put(cur)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        truncado = len(filas) > limite
        datos, celdas_recortadas = _serializar(filas[:limite], self.limites.max_celda)
        return {
            "ok": True, "class": "ok", "columnas": columnas,
            "filas": min(len(filas), limite), "truncado": truncado,
            "celdas_recortadas": celdas_recortadas, "datos": datos,
            "ms": ms, "data_release": self.data_release, "limite": limite,
        }

    def cerrar(self) -> None:
        if self._cerrado:
            return
        self._cerrado = True
        self.guardia.cerrar()
        self._lectura.cerrar()
        self._con.close()


def _normalizar(base: str) -> tuple[str, bool]:
    """Devuelve (base_normalizada, es_local). Una carpeta se vuelve URI file://."""
    if base.startswith("file://") or "://" not in base:
        ruta = Path(base.replace("file://", "")).expanduser().resolve()
        if not ruta.is_dir():
            raise FileNotFoundError(f"No existe la carpeta SIF_CHILE_BASE: {ruta}")
        return ruta.as_uri(), True
    return base.rstrip("/"), False


class Ocupado(Exception):
    """El pool está completo: el cliente debe reintentar más tarde."""


class Timeout(Exception):
    """La consulta superó el tiempo máximo."""


def _jsonable(v: Any, max_celda: int) -> tuple[Any, int]:
    """Convierte un valor DuckDB a JSON seguro, recortando strings largos."""
    if isinstance(v, str):
        if len(v) > max_celda:
            return v[:max_celda] + "…", 1
        return v, 0
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat(), 0
    if isinstance(v, dt.timedelta):
        return v.total_seconds(), 0
    if isinstance(v, decimal.Decimal):
        return str(v), 0
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None, 0
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", "replace"), 0
    if isinstance(v, dict):
        salida = {}
        recortadas = 0
        for k, valor in v.items():
            salida[str(k)], n = _jsonable(valor, max_celda)
            recortadas += n
        return salida, recortadas
    if isinstance(v, (list, tuple)):
        salida = []
        recortadas = 0
        for valor in v:
            nuevo, n = _jsonable(valor, max_celda)
            salida.append(nuevo)
            recortadas += n
        return salida, recortadas
    return v, 0


def _serializar(filas: list, max_celda: int) -> tuple[list, int]:
    datos = []
    recortadas = 0
    for fila in filas:
        nueva = []
        for v in fila:
            valor, n = _jsonable(v, max_celda)
            nueva.append(valor)
            recortadas += n
        datos.append(nueva)
    return datos, recortadas


class RateLimit:
    """Token bucket por IP, en memoria. Suficiente para una instancia.

    El mapa se poda cuando crece demasiado: un atacante que rote IPs no puede
    agotar la memoria del proceso con entradas viejas.
    """

    def __init__(self, burst: int, por_min: int, max_ips: int = 10_000) -> None:
        self.burst = burst
        self.recarga = por_min / 60.0
        self.max_ips = max_ips
        self._cubos: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def permitir(self, ip: str) -> tuple[bool, float]:
        ahora = time.monotonic()
        with self._lock:
            if len(self._cubos) >= self.max_ips:
                viejas = sorted(self._cubos, key=lambda k: self._cubos[k][1])
                for k in viejas[: len(self._cubos) // 2]:
                    del self._cubos[k]
            tokens, ultimo = self._cubos.get(ip, (float(self.burst), ahora))
            tokens = min(self.burst, tokens + (ahora - ultimo) * self.recarga)
            if tokens < 1:
                self._cubos[ip] = (tokens, ahora)
                return False, (1 - tokens) / self.recarga
            self._cubos[ip] = (tokens - 1, ahora)
            return True, 0.0


def _error(clase: str, motivo: str, siguiente: str, reintento: str,
           estado: int, extra: dict | None = None,
           cabeceras: dict | None = None) -> JSONResponse:
    cuerpo = {"ok": False, "class": clase, "reason": motivo,
              "next": siguiente, "retry": reintento}
    if extra:
        cuerpo.update(extra)
    return JSONResponse(status_code=estado, content=cuerpo, headers=cabeceras)


class ConsultaCuerpo(BaseModel):
    sql: str = Field(..., min_length=1, description="SQL de lectura, una sentencia.")
    limite: int | None = Field(None, ge=1, description="Filas a devolver (tope del servicio).")


def crear_app(base: str | None = None, *, token: str | None = None,
              cors_origins: str | None = None, log_sql: bool | None = None,
              limites: Limites | None = None, **kw: Any) -> FastAPI:
    """Crea la app FastAPI. `base` y `limites` se pueden inyectar en pruebas."""
    limites = limites or Limites(**kw)
    motor = Motor(base=base, limites=limites)
    rate = RateLimit(limites.rate_burst, limites.rate_min)
    token = token if token is not None else os.environ.get("SIF_API_TOKEN") or None
    if log_sql is None:
        log_sql = os.environ.get("SIF_LOG_SQL", "").lower() in {"1", "true", "yes"}
    origenes = cors_origins if cors_origins is not None else os.environ.get("SIF_CORS_ORIGINS", "*")
    trust_proxy = os.environ.get("SIF_API_TRUST_PROXY", "").lower() in {"1", "true", "yes"}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        motor.cerrar()

    app = FastAPI(
        title="SIF Chile · API de consultas",
        version=VERSION,
        lifespan=lifespan,
        description=(
            "SQL de solo lectura sobre los datos financieros publicados de Chile "
            "(CMF, Banco Central, Superintendencia de Pensiones). El contrato "
            "estático vive en /v2/catalog; /v2/query ejecuta SQL de lectura con "
            "límites. Best effort, sin SLA. Los datos son de organismos públicos "
            "y se republican normalizados: cita la fuente (ver /v2/catalog)."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if origenes == "*" else [o.strip() for o in origenes.split(",") if o.strip()],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Retry-After"],
    )
    app.state.motor = motor
    app.state.limites = limites

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError):
        return _error("input", "Parámetros inválidos: " + json.dumps(exc.errors(), ensure_ascii=False)[:300],
                      "Revisa sql y limite en /docs.", "after_fix", 400)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        clase = "auth" if exc.status_code == 401 else "input" if exc.status_code == 404 else "error"
        return _error(clase, str(exc.detail), "Revisa la ruta en /docs.", "no", exc.status_code)

    def _ip(request: Request) -> str:
        if trust_proxy:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "desconocida"

    def _autenticar(request: Request) -> JSONResponse | None:
        if not token:
            return None
        cabecera = request.headers.get("authorization", "")
        presented = cabecera[7:] if cabecera.lower().startswith("bearer ") else ""
        if not presented or not hmac.compare_digest(presented, token):
            return _error("auth", "Falta el token Bearer o es incorrecto.",
                          "Envía Authorization: Bearer <token>.", "no", 401)
        return None

    @app.get("/", tags=["servicio"])
    def raiz() -> dict:
        return {
            "servicio": "SIF Chile · API de consultas", "version": VERSION,
            "contrato": CONTRATO, "data_release": motor.data_release,
            "modo": "local" if motor.local else "remoto",
            "objetos": motor.catalogo["totales"]["objetos"],
            "auth_requerida": bool(token),
            "rutas": {
                "catalog": "/v2/catalog", "schema": "/v2/schema/{id}",
                "partitions": "/v2/partitions/{id}", "queries": "/v2/queries",
                "resultados": "/v2/resultados", "resultado": "/v2/resultado/{id}",
                "query": "/v2/query", "health": "/health",
                "docs": "/docs", "openapi": "/openapi.json",
            },
            "limites": {"max_filas": limites.max_filas, "timeout_s": limites.timeout_s,
                        "max_sql": limites.max_sql, "pool": limites.pool},
        }

    @app.get("/health", tags=["servicio"])
    def health() -> dict:
        return {"ok": True, "class": "ok", "data_release": motor.data_release,
                "objetos": motor.catalogo["totales"]["objetos"],
                "vistas": motor._n_vistas, "modo": "local" if motor.local else "remoto"}

    @app.get("/v2/catalog", tags=["contrato"])
    def catalog() -> JSONResponse:
        return JSONResponse(motor.catalogo)

    @app.get("/v2/schema/{ident}", tags=["contrato"])
    def schema(ident: str) -> JSONResponse:
        if not _ID_OBJETO.match(ident):
            return _error("input", "id de objeto inválido.", "Usa solo [a-z0-9_].", "no", 400)
        try:
            return JSONResponse(motor._lectura.esquema(ident))
        except KeyError as exc:
            return _error("input", str(exc), "Lista los objetos en /v2/catalog.", "no", 404)

    @app.get("/v2/partitions/{ident}", tags=["contrato"])
    def partitions(ident: str) -> JSONResponse:
        if not _ID_OBJETO.match(ident):
            return _error("input", "id de objeto inválido.", "Usa solo [a-z0-9_].", "no", 400)
        try:
            return JSONResponse(motor._lectura.particiones(ident))
        except KeyError as exc:
            return _error("input", str(exc), "Lista los objetos en /v2/catalog.", "no", 404)

    @app.get("/v2/queries", tags=["contrato"])
    def queries() -> JSONResponse:
        return JSONResponse(motor._lectura._json("api/v2/queries.json"))

    @app.get("/v2/resultados", tags=["contrato"])
    def resultados() -> JSONResponse:
        return JSONResponse(motor._lectura._json("api/v2/resultados/index.json"))

    @app.get("/v2/resultado/{ident}", tags=["contrato"])
    def resultado(ident: str) -> JSONResponse:
        if not _ID_RESULTADO.match(ident):
            return _error("input", "id de resultado inválido.", "Usa solo [a-z0-9-].", "no", 400)
        try:
            return JSONResponse(motor._lectura._json(f"api/v2/resultados/{ident}.json"))
        except (KeyError, FileNotFoundError):
            return _error("input", f"No hay resultado con id «{ident}».",
                          "Lista los resultados en /v2/resultados.", "no", 404)

    def _ejecutar(sql: str, limite: int | None, request: Request) -> JSONResponse:
        ip = _ip(request)
        ok, espera = rate.permitir(ip)
        if not ok:
            segundos = max(1, math.ceil(espera))
            return _error("rate", "Demasiadas consultas desde esta IP.",
                          f"Espera {segundos} s y reintenta.", "after_wait", 429,
                          {"retryAfterMs": segundos * 1000}, {"Retry-After": str(segundos)})
        auth = _autenticar(request)
        if auth is not None:
            return auth
        t0 = time.perf_counter()
        try:
            resultado = motor.consultar(sql, limite)
        except ValueError as exc:
            return _error("refused", str(exc),
                          "Reescribe como SELECT/WITH de una sola sentencia sobre las vistas del contrato.",
                          "no", 403)
        except Ocupado as exc:
            return _error("rate", str(exc), "Reintenta en unos segundos.", "after_wait", 503,
                          cabeceras={"Retry-After": "1"})
        except Timeout as exc:
            return _error("timeout", str(exc),
                          "Acota la consulta: filtra por periodo y agrega antes de devolver filas.",
                          "after_fix", 504)
        except duckdb.Error as exc:
            primero = str(exc).splitlines()[0][:300]
            pista = ("Revisa el nombre de la tabla y sus columnas en /v2/catalog y "
                     "/v2/schema/{id} antes de reintentar.")
            if "does not exist" in primero or "Referenced column" in primero or "Catalog Error" in primero:
                pista = "Esa tabla o columna no existe: búscala en /v2/catalog."
            return _error("input", primero, pista, "after_fix", 400)
        except Exception as exc:  # noqa: BLE001 - el cliente recibe el sobre, no un traceback
            LOG.exception("error interno al consultar")
            return _error("error", f"Error interno: {type(exc).__name__}",
                          "Reintenta más tarde; si persiste, avisa al mantenedor.", "after_wait", 500)
        finally:
            ms = round((time.perf_counter() - t0) * 1000, 1)
            huella = hashlib.sha256((sql or "").encode("utf-8")).hexdigest()[:12]
            LOG.info(json.dumps({"ip": ip, "sql_hash": huella, "ms": ms,
                                 "sql": sql if log_sql else None}, ensure_ascii=False))
        return JSONResponse(resultado, headers={"Cache-Control": "no-store"})

    @app.post("/v2/query", tags=["consulta"])
    def query_post(cuerpo: ConsultaCuerpo, request: Request) -> JSONResponse:
        return _ejecutar(cuerpo.sql, cuerpo.limite, request)

    @app.get("/v2/query", tags=["consulta"])
    def query_get(request: Request, sql: str = Query(..., min_length=1),
                  limite: int | None = Query(None, ge=1)) -> JSONResponse:
        return _ejecutar(sql, limite, request)

    return app

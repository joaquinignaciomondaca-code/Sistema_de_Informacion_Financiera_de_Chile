"""Cliente del Sistema de Información Financiera de Chile.

Todo lo que sabe este cliente lo aprende del contrato publicado
(`docs/api/v1/`): el catálogo de objetos, sus esquemas y sus particiones. No hay
listas escritas a mano, así que si el contrato cambia, el cliente cambia.

    import sif_chile
    sif = sif_chile.connect()
    sif.tablas()                       # los 90 objetos
    sif.esquema("seguros_renta_fija")  # columnas y tipos
    sif.sql("SELECT count(*) FROM seguros_renta_fija").fetchone()
"""
from __future__ import annotations

import importlib.util
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Iterable

from . import guardia

BASE_CANONICA = (
    "https://joaquinignaciomondaca-code.github.io/"
    "Sistema_de_Informacion_Financiera_de_Chile"
)
# Variable de entorno para trabajar contra una copia local sin tocar código.
ENTORNO_BASE = "SIF_CHILE_BASE"


def _es_ruta_local(base: str) -> bool:
    if base.startswith("file://"):
        return True
    return "://" not in base


def _normalizar_base(base: str | None) -> str:
    """Una base es una URL o una carpeta. Las dos se tratan igual."""
    valor = (base or os.environ.get(ENTORNO_BASE) or BASE_CANONICA).strip()
    if _es_ruta_local(valor):
        ruta = Path(valor).expanduser().resolve()
        if not ruta.is_dir():
            raise FileNotFoundError(f"No existe la carpeta indicada en base: {ruta}")
        return ruta.as_uri()
    return valor.rstrip("/")


class Sif:
    """Cliente sobre el contrato estático. Se construye con `sif_chile.connect()`."""

    def __init__(self, base: str | None = None, cache: str | os.PathLike | None = None,
                 conectar: bool = True) -> None:
        self.base = _normalizar_base(base)
        self.local = self.base.startswith("file://")
        self._cache = Path(cache).expanduser() if cache else None
        if self._cache:
            self._cache.mkdir(parents=True, exist_ok=True)
        self._catalogo: dict[str, Any] | None = None
        self._con = None
        self._consultas: dict[str, Any] | None = None
        if conectar:
            self._abrir()

    # ------------------------------------------------------------------ #
    # Lectura del contrato
    # ------------------------------------------------------------------ #
    def _leer(self, relativa: str) -> bytes:
        """Lee un archivo del contrato, por HTTP o del disco."""
        if self.local:
            return (Path(self.base.replace("file://", "")) / relativa).read_bytes()

        destino = self._cache / "contrato" / relativa.replace("/", "__") if self._cache else None
        if destino and destino.exists():
            return destino.read_bytes()
        with urllib.request.urlopen(f"{self.base}/{relativa}", timeout=30) as r:
            datos = r.read()
        if destino:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(datos)
        return datos

    def _json(self, relativa: str) -> dict:
        return json.loads(self._leer(relativa).decode("utf-8"))

    @property
    def catalogo(self) -> dict:
        if self._catalogo is None:
            self._catalogo = self._json("api/v1/catalog.json")
            self._por_id = {o["id"]: o for o in self._catalogo["objetos"]}
            self._por_alias = {
                a: o["id"] for o in self._catalogo["objetos"] for a in o.get("aliases") or []
            }
        return self._catalogo

    def _objeto(self, nombre: str) -> dict:
        self.catalogo  # asegura el índice
        ident = nombre if nombre in self._por_id else self._por_alias.get(nombre)
        if ident is None:
            parecidos = [i for i in self._por_id if nombre.lower() in i.lower()][:5]
            pista = f" Parecidos: {', '.join(parecidos)}." if parecidos else ""
            raise KeyError(f"No hay ningún objeto «{nombre}» en el catálogo.{pista}")
        return self._por_id[ident]

    # ------------------------------------------------------------------ #
    # Conexión
    # ------------------------------------------------------------------ #
    def _abrir(self) -> None:
        """Crea la conexión y registra las vistas del contrato (1b.2)."""
        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise ImportError(
                "Falta duckdb. Instálalo con: pip install sif-chile[duckdb] "
                "o pip install duckdb"
            ) from exc

        con = duckdb.connect()
        if not self.local:
            # En DuckDB-Wasm httpfs viene incluido; en Python hay que pedirlo.
            try:
                con.execute("INSTALL httpfs")
            except Exception:  # noqa: BLE001 - ya instalada o sin red para el repo
                pass
            try:
                con.execute("LOAD httpfs")
            except Exception:  # noqa: BLE001
                pass
        # El DDL publicado es la única fuente de las vistas: si el contrato
        # añade un objeto, el cliente lo tiene sin actualizar el paquete.
        ddl = self._leer("api/v1/views.sql").decode("utf-8")
        ddl = self._reescribir_base(ddl)
        con.execute(ddl)
        self._con = con

    def _reescribir_base(self, ddl: str) -> str:
        """Cambia la base de `views.sql` por la de este cliente."""
        lineas = []
        for linea in ddl.splitlines():
            if linea.strip().startswith("SET VARIABLE sif_base"):
                lineas.append(f"SET VARIABLE sif_base = '{self.base}';")
            else:
                lineas.append(linea)
        return "\n".join(lineas)

    @property
    def con(self):
        if self._con is None:
            self._abrir()
        return self._con

    def cerrar(self) -> None:
        if self._con is not None:
            self._con.close()
            self._con = None

    def __enter__(self) -> "Sif":
        return self

    def __exit__(self, *_: object) -> None:
        self.cerrar()

    # ------------------------------------------------------------------ #
    # Descubrimiento
    # ------------------------------------------------------------------ #
    def tablas(self, sector: str | None = None, estado: str | None = None) -> list[dict]:
        """Los 90 objetos, filtrables por sector y por estado."""
        objetos = self.catalogo["objetos"]
        if sector:
            objetos = [o for o in objetos if o.get("sector") == sector]
        if estado:
            objetos = [o for o in objetos if o.get("estado") == estado]
        return objetos

    def sectores(self) -> dict[str, int]:
        cuenta: dict[str, int] = {}
        for o in self.catalogo["objetos"]:
            cuenta[o.get("sector") or "sin_sector"] = cuenta.get(o.get("sector") or "sin_sector", 0) + 1
        return dict(sorted(cuenta.items(), key=lambda p: -p[1]))

    def buscar(self, texto: str) -> list[dict]:
        """Busca en id, título, descripción, sector y alias, sin distinguir mayúsculas."""
        aguja = _normalizar_texto(texto)
        fuera = []
        for o in self.catalogo["objetos"]:
            pajar = _normalizar_texto(" ".join([
                o["id"], o.get("titulo") or "", o.get("descripcion") or "",
                o.get("sector") or "", " ".join(o.get("aliases") or []),
            ]))
            if aguja in pajar:
                fuera.append(o)
        return fuera

    def tabla(self, nombre: str) -> dict:
        """Una entrada del catálogo, por nombre o por alias heredado."""
        return self._objeto(nombre)

    def esquema(self, nombre: str) -> dict:
        """Columnas, tipos, clave primaria y foráneas de un objeto."""
        ident = self._objeto(nombre)["id"]
        return self._json(f"api/v1/schema/{ident}.json")

    def particiones(self, nombre: str) -> dict:
        """Los archivos que componen el objeto, con período y hash."""
        ident = self._objeto(nombre)["id"]
        return self._json(f"api/v1/partitions/{ident}.json")

    def consultas(self) -> list[dict]:
        """Las consultas de ejemplo del sitio, con su id estable."""
        if self._consultas is None:
            self._consultas = self._json("api/v1/queries.json")
        return self._consultas["consultas"]

    # ------------------------------------------------------------------ #
    # Datos
    # ------------------------------------------------------------------ #
    def read_table(self, nombre: str, limite: int | None = None, formato: str | None = None) -> Any:
        """El contenido de un objeto, ya materializado.

        Devuelve DataFrame si hay pandas, si no una tabla de Arrow. Con
        `formato="arrow"` o `"pandas"` se elige explícitamente. Sin ninguno de
        los dos instalados hay que usar `sif.sql(...).fetchall()`.
        """
        objeto = self._objeto(nombre)
        sql = f'SELECT * FROM "{objeto["id"]}"'
        if limite:
            sql += f" LIMIT {int(limite)}"
        guardia.exigir(sql)
        return _materializar(self.con, sql, formato)

    def sql(self, consulta: str, limite: int | None = None) -> Any:
        """Ejecuta una consulta de lectura y devuelve el resultado.

        El guardia es una conveniencia, no una frontera de seguridad: ver
        `sif_chile.guardia`.
        """
        guardia.exigir(consulta)
        if limite:
            consulta = f"SELECT * FROM ({consulta.rstrip().rstrip(';')}) LIMIT {int(limite)}"
        return self.con.execute(consulta)

    def consulta(self, ident: str, limite: int | None = None) -> Any:
        """Ejecuta una de las consultas publicadas, por su id."""
        for c in self.consultas():
            if c["id"] == ident:
                return self.sql(c["sql"], limite=limite)
        raise KeyError(f"No hay ninguna consulta con id «{ident}».")

    def descargar(self, nombre: str, destino: str | os.PathLike | None = None) -> list[Path]:
        """Baja los Parquet de un objeto a `destino` y verifica cada SHA-256 (1b.4).

        Si se conectó con `cache=`, `destino` es la carpeta de datos de ese
        caché. Un archivo que ya está y cuyo hash coincide no se vuelve a bajar:
        eso es lo que evita gastar ancho de banda de Pages en la segunda pasada.
        """
        ident = self._objeto(nombre)["id"]
        if destino is None:
            if not self._cache:
                raise ValueError("Indica `destino`, o conecta con cache= para usar el caché por defecto.")
            destino = self._cache / "datos" / ident
        carpeta = Path(destino).expanduser()
        carpeta.mkdir(parents=True, exist_ok=True)
        guardados = []
        for parte in self.particiones(ident)["particiones"]:
            salida = carpeta / Path(parte["archivo"]).name
            if salida.exists() and _sha256(salida) == parte["sha256"]:
                guardados.append(salida)  # ya estaba y sigue intacto
                continue
            if self.local:
                origen = Path(self.base.replace("file://", "")) / parte["archivo"]
                salida.write_bytes(origen.read_bytes())
            else:
                url = f"{self.base}/{parte['archivo']}"
                with urllib.request.urlopen(url, timeout=120) as r:
                    salida.write_bytes(r.read())
            obtenido = _sha256(salida)
            if obtenido != parte["sha256"]:
                salida.unlink(missing_ok=True)
                raise ValueError(
                    f"{salida.name}: el SHA-256 descargado no coincide con el del contrato "
                    f"({obtenido[:12]}… ≠ {parte['sha256'][:12]}…). Se descartó el archivo."
                )
            guardados.append(salida)
        return guardados

    def __repr__(self) -> str:
        return f"Sif(base={self.base!r}, objetos={len(self.catalogo['objetos'])})"


def _normalizar_texto(texto: str) -> str:
    """Minúsculas y separadores como espacios: «seguros renta» encuentra seguros_renta_fija."""
    return " ".join(texto.lower().replace("_", " ").replace("-", " ").split())


def _hay_pandas() -> bool:
    return importlib.util.find_spec("pandas") is not None


def _materializar(con: Any, consulta: str, formato: str | None = None) -> Any:
    """Convierte el resultado de duckdb en datos, no en una conexión.

    Se mira si pandas está instalado antes de ejecutar: preguntarlo por la
    excepción de `.df()` deja la conexión con un resultado a medio consumir y
    DuckDB la rechaza en la llamada siguiente.
    """
    if formato not in (None, "pandas", "arrow"):
        raise ValueError(f"Formato desconocido: {formato}. Use 'pandas' o 'arrow'.")
    if formato in (None, "pandas"):
        if _hay_pandas():
            return con.sql(consulta).df()
        if formato == "pandas":
            raise ImportError("Falta pandas: pip install 'sif-chile[pandas]'")
    # DuckDB renombró el método en la 2.0; se prueban los dos nombres para no
    # atarse a una versión concreta.
    rel = con.sql(consulta)
    for nombre in ("to_arrow_table", "fetch_arrow_table", "arrow"):
        metodo = getattr(rel, nombre, None)
        if metodo is not None:
            return metodo()
    raise ImportError(
        "Para materializar filas hace falta pandas o pyarrow: "
        "pip install 'sif-chile[pandas]' o pip install pyarrow. "
        "Mientras tanto, `sif.sql(consulta).fetchall()` devuelve tuplas."
    )


def _sha256(ruta: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def connect(base: str | None = None, cache: str | os.PathLike | None = None) -> Sif:
    """Conecta al contrato.

    base   URL del sitio o carpeta local con el contenido de `docs/`.
           Por defecto, la URL canónica; `SIF_CHILE_BASE` la sobreescribe.
    cache  carpeta donde guardar los documentos del contrato y los Parquet.
    """
    return Sif(base=base, cache=cache)

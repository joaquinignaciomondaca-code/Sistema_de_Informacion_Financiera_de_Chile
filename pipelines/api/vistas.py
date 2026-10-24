"""Lectura del contrato de vistas de la web (base de la API, fase 1).

Este módulo es el **único** lugar que sabe leer `SEMANTIC_VIEWS` y
`LEGACY_VIEW_ALIASES` de `docs/js/duckdb_client.js`. Antes vivía dentro de
`scripts/audit_consultas_sugeridas.py`; al construir el catálogo hacían falta
las mismas funciones, así que se movieron aquí y la auditoría las importa en
vez de tener una copia.

La URL base es un parámetro: el contrato publica `{{BASE}}` y cada consumidor
lo sustituye (el sitio, una copia local, un espejo).

    from pipelines.api import vistas as V
    for v in V.vistas_semanticas():
        V.ficheros_de(v)          # rutas locales, para leer
        V.urls_de(v)              # {{BASE}}/outputs/..., para publicar
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
DOCS = RAIZ / "docs"
CLIENTE = DOCS / "js" / "duckdb_client.js"

# Marcador que reemplaza cada consumidor por su base. No se usa una URL fija
# dentro del contrato: la decisión D1 puede cambiar el dominio sin regenerar.
BASE = "{{BASE}}"


def _bloque(texto: str, marcador: str, apertura: str | None = None) -> str:
    """Devuelve el cuerpo del array/objeto que sigue a `marcador`, equilibrando corchetes.

    `apertura` fuerza el delimitador ("[" o "{"). Sin él se elige el que aparezca
    primero en los 200 caracteres siguientes, que es lo correcto para un array
    literal pero **no** para un objeto cuyos valores ya traen corchetes: en
    `LEGACY_VIEW_ALIASES` el primer `[` es el de `["seguros_maestro"]`, así que el
    bloque salía con un solo alias y la comprobación de compatibilidad no veía
    ninguno de los 19 declarados.
    """
    i = texto.index(marcador)
    if apertura:
        i = texto.index(apertura, i)
    else:
        i = texto.index("[", i) if "[" in texto[i : i + 200] else texto.index("{", i)
    apertura = texto[i]
    cierre = "]" if apertura == "[" else "}"
    nivel, j = 0, i
    while j < len(texto):
        if texto[j] == apertura:
            nivel += 1
        elif texto[j] == cierre:
            nivel -= 1
            if nivel == 0:
                return texto[i : j + 1]
        j += 1
    raise ValueError(f"bloque no equilibrado para {marcador}")


def vistas_semanticas() -> list[dict]:
    """Extrae SEMANTIC_VIEWS de duckdb_client.js: file/manifest, queryFile y filtros."""
    texto = CLIENTE.read_text(encoding="utf-8")
    bloque = _bloque(texto, "const SEMANTIC_VIEWS")
    salida = []
    for m in re.finditer(r"\{([^{}]*)\}", bloque):
        cuerpo = m.group(1)
        nombre = re.search(r'name:\s*"([^"]+)"', cuerpo)
        if not nombre:
            continue
        vista = {"name": nombre.group(1)}
        for clave in ("file", "manifest", "queryFile", "where"):
            hallado = re.search(rf'{clave}:\s*"([^"]+)"', cuerpo)
            if hallado:
                vista[clave] = hallado.group(1)
        salida.append(vista)
    return salida


def alias_heredados() -> dict[str, list[str]]:
    """{nombre canónico: [nombres heredados]} desde LEGACY_VIEW_ALIASES."""
    texto = CLIENTE.read_text(encoding="utf-8")
    bloque = _bloque(texto, "const LEGACY_VIEW_ALIASES", apertura="{")
    alias = {}
    for m in re.finditer(r"(\w+):\s*\[([^\]]*)\]", bloque):
        alias[m.group(1)] = re.findall(r'"([^"]+)"', m.group(2))
    return alias


def aliases_de(nombre: str, alias: dict[str, list[str]] | None = None) -> list[str]:
    """Nombres heredados de un objeto (lista vacía si no tiene)."""
    return list((alias if alias is not None else alias_heredados()).get(nombre, []))


def rutas_relativas(vista: dict) -> list[str]:
    """Rutas de los Parquet del objeto, relativas a `docs/`."""
    if "file" in vista:
        ruta = DOCS / vista["file"]
        return [vista["file"]] if ruta.exists() else []
    if "manifest" in vista:
        manifiesto = DOCS / vista["manifest"]
        if not manifiesto.exists():
            return []
        datos = json.loads(manifiesto.read_text(encoding="utf-8"))
        base = Path(vista["manifest"]).parent
        fuera = []
        for archivo in datos.get("files", []):
            # el manifest puede traer rutas relativas a docs/ o a su carpeta
            rel = archivo if (DOCS / archivo).exists() else str(base / archivo)
            if (DOCS / rel).exists():
                fuera.append(Path(rel).as_posix())
        return fuera
    return []


def rutas_sql_relativas(vista: dict) -> list[str]:
    """Rutas que debe leer la vista SQL (compacto si fue publicado y está presente).

    ``rutas_relativas`` sigue describiendo los Parquet públicos/descargables;
    mantener ambas funciones separadas evita que el compacto SQL se cuele en el
    catálogo de descargas o cambie sus filtros y particiones.
    """
    query_file = vista.get("queryFile")
    if query_file:
        ruta = Path(query_file)
        if ruta.is_absolute() or ".." in ruta.parts:
            return []
        return [ruta.as_posix()] if (DOCS / ruta).is_file() else []
    return rutas_relativas(vista)


def ficheros_sql_de(vista: dict) -> list[str]:
    """Rutas locales para ejecutar la definición SQL de una vista."""
    return [str(DOCS / rel) for rel in rutas_sql_relativas(vista)]


def urls_sql_de(vista: dict, base: str = BASE) -> list[str]:
    """URLs de la fuente elegida para SQL, usando el compacto cuando existe."""
    limpia = base.rstrip("/")
    return [f"{limpia}/{rel}" for rel in rutas_sql_relativas(vista)]


def ficheros_de(vista: dict) -> list[str]:
    """Rutas locales de los Parquet del objeto (vacía si no hay nada publicado)."""
    return [str(DOCS / rel) for rel in rutas_relativas(vista)]


def urls_de(vista: dict, base: str = BASE) -> list[str]:
    """URLs publicadas del objeto: `base` + ruta relativa."""
    limpia = base.rstrip("/")
    return [f"{limpia}/{rel}" for rel in rutas_relativas(vista)]


def sql_de_vista(vista: dict, base: str = BASE, union: bool = True) -> str:
    """CREATE VIEW del objeto contra la fuente SQL publicada."""
    urls = urls_sql_de(vista, base)
    if not urls:
        return ""
    rutas = urls[0] if len(urls) == 1 else "[" + ", ".join(f"'{u}'" for u in urls) + "]"
    if len(urls) == 1:
        rutas = f"'{urls[0]}'"
    extra = ", union_by_name=true" if union and len(urls) > 1 else ""
    filtro = f"\n  WHERE {vista['where']}" if vista.get("where") else ""
    return (
        f'CREATE OR REPLACE VIEW "{vista["name"]}" AS\n'
        f"SELECT * FROM read_parquet({rutas}{extra}){filtro};"
    )

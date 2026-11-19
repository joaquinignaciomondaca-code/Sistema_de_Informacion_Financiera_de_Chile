"""Lectura del contrato de vistas de la web (base de la API, fase 1).

Este módulo es el **único** lugar que sabe leer `SEMANTIC_VIEWS`,
`QUICK_QUERY_VIEWS` y `LEGACY_VIEW_ALIASES` de `docs/js/duckdb_client.js`. Antes vivía dentro de
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


def vistas_sql_auxiliares() -> list[dict]:
    """Vistas internas de consultas sugeridas, fuera del catálogo de objetos."""
    texto = CLIENTE.read_text(encoding="utf-8")
    bloque = _bloque(texto, "const QUICK_QUERY_VIEWS")
    salida = []
    for m in re.finditer(r"\{([^{}]*)\}", bloque):
        cuerpo = m.group(1)
        nombre = re.search(r'name:\s*"([^"]+)"', cuerpo)
        manifiesto = re.search(r'sourceManifest:\s*"([^"]+)"', cuerpo)
        if not nombre or not manifiesto:
            continue
        vista = {"name": nombre.group(1), "manifest": manifiesto.group(1)}
        if re.search(r"latestManifestFile:\s*true", cuerpo):
            vista["latestManifestFile"] = True
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


#: Nombre del Parquet que un publicador deja cuando una tabla no tiene filas todavía
#: (`seguros/scripts/actualizar_carteras.py`: préstamos y arriendos, que la CMF no
#: entrega en los ZIP publicados). Lleva el esquema completo y cero filas para que la
#: vista web exista y responda vacía.
ARCHIVO_VACIO = "_vacio.parquet"


def _rutas_de_manifiesto(vista: dict, incluir_vacio: bool) -> list[str]:
    """Parquet del objeto según su manifiesto, con o sin el `_vacio.parquet`.

    Los `_vacio.parquet` se excluyen a propósito. No son descargas: son el andamiaje
    de esquema de una tabla que aún no reporta, y anunciarlos como partición publicada
    cambia la semántica del catálogo. Hasta el 2026-11-19 este camino los devolvía, así
    que al regenerar el contrato los cuatro objetos de préstamos y arriendos pasaban de
    `vacio` a `publicado` **con 0 filas**: `reconciliacion.csv` perdía el motivo «la CMF
    aún no entrega la tabla», `audit_pages_capacity` dejaba esos Parquet sin categoría,
    los exportes `.completo.csv`/`.json` dejaban de generarse (con 0 filas no se
    publican) y `test_fichas_candidatas` recibía una ficha con descarga de un archivo
    que ninguna capa enlaza. El esquema sigue disponible por `rutas_sql_relativas`, que
    es la que registra la vista SQL de esos objetos.
    """
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
            if not (DOCS / rel).exists():
                continue
            if not incluir_vacio and Path(rel).name == ARCHIVO_VACIO:
                continue
            fuera.append(Path(rel).as_posix())
        return fuera
    return []


def rutas_relativas(vista: dict) -> list[str]:
    """Rutas de los Parquet **descargables** del objeto, relativas a `docs/`.

    Ver `_rutas_de_manifiesto`: los `_vacio.parquet` no cuentan como descarga.
    """
    return _rutas_de_manifiesto(vista, incluir_vacio=False)


def rutas_sql_relativas(vista: dict) -> list[str]:
    """Rutas que debe leer la vista SQL (compacto si fue publicado y está presente).

    ``rutas_relativas`` sigue describiendo los Parquet públicos/descargables;
    mantener ambas funciones separadas evita que el compacto SQL se cuele en el
    catálogo de descargas o cambie sus filtros y particiones.
    """
    if vista.get("latestManifestFile") and vista.get("manifest"):
        manifiesto = DOCS / vista["manifest"]
        if not manifiesto.is_file():
            return []
        datos = json.loads(manifiesto.read_text(encoding="utf-8"))
        base = Path(vista["manifest"]).parent
        periodos = [p for p in datos.get("periodos", [])
                    if isinstance(p, str) and re.fullmatch(r"\d{4}-\d{2}", p)]
        ultimo_periodo = max(periodos) if periodos else None
        ultimo_ano = ultimo_periodo[:4] if ultimo_periodo else None
        candidatos = []
        for archivo in datos.get("files", []):
            if not isinstance(archivo, str):
                continue
            mes = re.search(r"(?:^|/)(\d{4}-\d{2})(?=\.parquet$)", archivo)
            ano = re.search(r"(?:^|/)(\d{4})(?=\.parquet$)", archivo)
            prioridad = 2 if mes and mes.group(1) == ultimo_periodo else (
                1 if ano and ano.group(1) == ultimo_ano else 0
            )
            if not prioridad:
                continue
            rel = archivo if (DOCS / archivo).is_file() else str(base / archivo)
            if (DOCS / rel).is_file():
                candidatos.append((prioridad, Path(rel).as_posix()))
        return [max(candidatos)[1]] if candidatos else []

    query_file = vista.get("queryFile")
    if query_file:
        ruta = Path(query_file)
        if ruta.is_absolute() or ".." in ruta.parts:
            return []
        return [ruta.as_posix()] if (DOCS / ruta).is_file() else []
    # Tampoco aquí: la web debe seguir diciendo «no hay particiones publicadas» en una
    # tabla que la CMF no entrega, no mostrar una tabla vacía. Registrarla como vista
    # cambiaría ese mensaje por un resultado de 0 filas y `audit_duckdb_client.js`
    # fija justo lo contrario. El esquema del archivo vacío se lee por
    # `rutas_esquema_relativas`, que es lo que necesita `build_esquemas`.
    return _rutas_de_manifiesto(vista, incluir_vacio=False)


def rutas_esquema_relativas(vista: dict) -> list[str]:
    """Parquet para describir el esquema, incluido el `_vacio.parquet`.

    Es el único camino que incluye el archivo vacío: sin él, las cuatro tablas de
    la Circular 1835 que la CMF no entrega quedarían sin columnas publicadas. No se
    usa para descargas ni para la vista SQL, que sí deben tratarlas como vacías.
    """
    return _rutas_de_manifiesto(vista, incluir_vacio=True)


def ficheros_de_esquema(vista: dict) -> list[str]:
    """Rutas locales de los Parquet que describen el esquema del objeto."""
    return [str(DOCS / rel) for rel in rutas_esquema_relativas(vista)]


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

"""Posiciones de los archivos de cartera de inversiones de seguros (CMF, Circular 1835).

Las posiciones y los nombres salen del inventario generado desde las fichas técnicas de
la CMF (``seguros/fuentes/fichas_tecnicas_1835/``) con ``inventario_1835.py``, que las
convierte en ``seguros/fuentes/inventario_1835.json``. Ahí quedan, para cada campo:

  - el nombre con que la CMF lo imprime en la ficha (``nombre_ficha``);
  - el nombre publicado (``columna``): el original en minúsculas, con el sufijo de la
    unidad declarada (``_m_clp``, ``_clp``, ``_uf``, ``_um``);
  - su descripción textual, que alimenta la hoja "Diccionario" de los Excel.

Se publican todos los campos del registro, no un subconjunto: los rellenos (FILLER), el
tipo de registro y el dígito verificador de los RUT quedan fuera (el DV viaja con el RUT,
como ``97004000-5``).

Cada campo es (columna, inicio, largo, tipo, decimales), con inicio en base 0.
Tipos: "t" texto, "n" número sin signo, "s" número con signo en el primer carácter
("+", "-", espacio o "0"), "f" fecha AAAAMMDD, "r" RUT (9 dígitos + DV en el carácter
siguiente).

Regenerar el inventario tras un cambio en las fichas::

    python -m seguros.scripts.inventario_1835 --escribir
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

FORMATO_2024_DESDE = "2024-12"

RUTA_INVENTARIO = Path(__file__).resolve().parents[1] / "fuentes" / "inventario_1835.json"

# Largo exacto de cada línea (todas las líneas de un archivo tienen el mismo largo).
LARGO = {
    "v2016": {"i": 930, "a": 470, "f": 338, "b": 477, "x": 513, "p": 489, "c": 138},
    "v2024": {"i": 970, "a": 572, "f": 361, "b": 506, "x": 611, "p": 587, "c": 138},
}

# Tipo de registro de totales (cuenta las líneas de detalle) por archivo.
TIPO_TOTAL = {"i": "3", "a": "3", "f": "3", "b": "3", "x": "6", "p": "7", "c": "3"}

# Encabezado (registro tipo 1), igual en todos los archivos y formatos.
ENCABEZADO = [("rut_aseguradora", 1, 10, "r", 0), ("nombre_aseguradora", 11, 60, "t", 0),
              ("periodo_archivo", 71, 6, "t", 0)]


@lru_cache(maxsize=1)
def _inventario() -> dict:
    return json.loads(RUTA_INVENTARIO.read_text(encoding="utf-8"))


def _clave(letra: str, tipo: str) -> str:
    return f"{letra}{tipo}"


def registros_inventario(formato: str) -> dict[str, dict]:
    """{archivo+tipo: {"tabla", "subtipo", "campos"}} tal cual sale del inventario."""
    return _inventario()["formatos"][formato]


def _tuplas(campos: list[dict]) -> list[tuple]:
    return [(c["columna"], c["inicio"], c["largo"], c["tipo"], c["decimales"]) for c in campos]


def campos(formato: str) -> dict[tuple[str, str], tuple[str, str | None, list[tuple]]]:
    """{(archivo, tipo_registro): (tabla, subtipo, campos)} para un formato."""
    salida = {}
    for clave, dato in registros_inventario(formato).items():
        letra, tipo = clave[0], clave[1:]
        salida[(letra, tipo)] = (dato["tabla"], dato["subtipo"], _tuplas(dato["campos"]))
    return salida


def diccionario(formato: str) -> dict[tuple[str, str], list[dict]]:
    """{(archivo, tipo_registro): [campos con descripción]} para la hoja "Diccionario"."""
    salida = {}
    for clave, dato in registros_inventario(formato).items():
        letra, tipo = clave[0], clave[1:]
        salida[(letra, tipo)] = [
            {"columna": c["columna"], "nombre_ficha": c["nombre_ficha"], "picture": c["picture"],
             "tipo": c["tipo"], "decimales": c["decimales"], "unidad": c["unidad"],
             "descripcion": c["descripcion"], "tabla": dato["tabla"], "subtipo": dato["subtipo"]}
            for c in dato["campos"]
        ]
    return salida


def formato_de(periodo: str) -> str:
    return "v2024" if periodo >= FORMATO_2024_DESDE else "v2016"

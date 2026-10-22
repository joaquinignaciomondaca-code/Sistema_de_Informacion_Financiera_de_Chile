"""Las dos funciones que ve un agente, sin nada de MCP.

`buscar` descubre y `ejecutar` consulta. Son funciones puras sobre el contrato:
no saben de protocolos ni de transporte, así que se prueban sin servidor y sin
red (contra una copia local de `docs/`).

El objetivo es el **modo código**: que un agente tenga dos herramientas y un
catálogo que buscar, en vez de 90 fichas de tabla en el contexto. La referencia
medida es el MCP de la CMF: 88 herramientas ≈ 37.000 tokens, y su modo código
baja a dos. Aquí las dos herramientas ocupan **191 tokens** (ver
`scripts/auditar_mcp.py`, que lo mide sobre el esquema real).

Lo que se devuelve está pensado para leerse en contexto:

  * `buscar` devuelve una ficha por objeto —id, sector, filas, corte, clave y
    columnas en una línea—, no el esquema completo con tipos y significados.
  * `ejecutar` devuelve columnas y filas, recorta los valores largos y avisa si
    truncó. Si el SQL falla devuelve `error` + `pista` en vez de lanzar: un
    agente que recibe una excepción suele repetir el error, uno que recibe una
    pista lo corrige.
"""
from __future__ import annotations

import decimal
import datetime as dt
import json
import re
import threading
from typing import Any

from .cliente import Sif, connect

# Tope de filas por llamada: el contexto del modelo es el recurso escaso.
MAX_FILAS = 200
# Caracteres por celda antes de recortar (una glosa larga arruina una tabla).
MAX_CELDA = 160
# Columnas que se listan en la ficha de `buscar`.
MAX_COLUMNAS = 30

_cliente: Sif | None = None
_candado = threading.Lock()


def cliente() -> Sif:
    """Un único `Sif` por proceso: el servidor MCP vive muchas peticiones."""
    global _cliente
    with _candado:
        if _cliente is None:
            _cliente = connect()
        return _cliente


def cerrar() -> None:
    global _cliente
    with _candado:
        if _cliente is not None:
            _cliente.cerrar()
            _cliente = None


def _recortar(valor: Any) -> Any:
    if isinstance(valor, (dt.date, dt.datetime)):
        return valor.isoformat()
    if isinstance(valor, decimal.Decimal):
        return str(valor)
    if isinstance(valor, str) and len(valor) > MAX_CELDA:
        return valor[:MAX_CELDA] + "…"
    return valor


def _ficha(objeto: dict, columnas: list[str]) -> dict:
    titulo = (objeto.get("titulo") or "").strip()
    if len(titulo) > 90:
        titulo = titulo[:90] + "…"
    lista = ", ".join(columnas[:MAX_COLUMNAS])
    if len(columnas) > MAX_COLUMNAS:
        lista += f" (+{len(columnas) - MAX_COLUMNAS})"
    return {
        "id": objeto["id"],
        "titulo": titulo,
        "sector": objeto.get("sector"),
        "filas": objeto.get("filas"),
        "corte": objeto.get("corte"),
        "pk": ",".join(objeto.get("primaryKey") or []) or None,
        "columnas": lista,
    }


# Palabras que un humano escribe y el catálogo no usa: se traducen a los tokens
# que sí aparecen en el id, el título, la descripción o el sector.
# Palabras que aparecen en casi todas las descripciones o no discriminan nada.
_IGNORAR = {
    "chile", "chileno", "chilena", "chilenos", "chilenas", "los", "las", "que",
    "por", "para", "con", "del", "una", "unos", "unas", "donde", "dónde",
    "fuera", "cual", "cuales", "cuáles", "cuanto", "cuánto", "cuantos",
    "cuántos", "cada", "mas", "más", "sobre", "entre", "desde", "hasta",
}

_SINONIMOS = {
    "fm": ["ffmm"], "mutuo": ["ffmm"], "mutuos": ["ffmm"],
    "fondo": ["ffmm", "fi"], "fondos": ["ffmm", "fi"],
    "aseguradora": ["seguros", "aseguradora"], "aseguradoras": ["seguros", "aseguradora"],
    "banco": ["bancos"], "bancos": ["bancos"],
    "exterior": ["extranjera", "extranjero", "exterior"],
    "extranjero": ["exterior", "extranjera"], "extranjera": ["exterior", "extranjero"],
    "extranjeros": ["exterior", "extranjera"], "extranjeras": ["exterior", "extranjera"],
    "invierte": ["cartera"], "invierten": ["cartera"], "invirtieron": ["cartera"],
    "inversion": ["cartera"], "inversión": ["cartera"], "inversiones": ["cartera"],
    "dolar": ["dolar", "tipo_cambio"], "dólar": ["dolar", "tipo_cambio"],
}


def _familias(texto: str) -> list[list[str]]:
    """Cada palabra con sus variantes (sinónimos y singular) cuenta **una vez**.

    Sin esto, «fondos mutuos» sumaba cuatro veces por `fondos`/`fondo` y
    `mutuos`/`mutuo`, y una tabla de seguros le ganaba a la de fondos mutuos.
    """
    limpio = re.sub(r"[^0-9a-záéíóúñ]+", " ", texto.lower())
    familias = []
    for palabra in limpio.split():
        if len(palabra) < 3 or palabra in _IGNORAR:
            continue
        variantes = [palabra, *_SINONIMOS.get(palabra, [])]
        if palabra.endswith("s") and len(palabra) > 4:
            variantes.append(palabra[:-1])
        familias.append(list(dict.fromkeys(variantes)))
    return familias


def _puntuar(objeto: dict, familias: list[list[str]]) -> int:
    identificador = objeto["id"].lower().replace("_", " ")
    texto = " ".join([
        identificador, (objeto.get("titulo") or "").lower(),
        (objeto.get("descripcion") or "").lower(),
        (objeto.get("sector") or "").lower(),
        " ".join(a.lower() for a in objeto.get("aliases") or []),
    ])
    puntaje = 0
    for variantes in familias:
        if any(v in identificador for v in variantes):
            puntaje += 3  # el id es la señal más fuerte: es lo que se escribe en el SQL
        elif any(v in texto for v in variantes):
            puntaje += 1
    return puntaje


def buscar(texto: str, sector: str | None = None, limite: int = 5) -> str:
    """Busca objetos del catálogo por texto y devuelve una ficha compacta de cada uno.

    Usa el mismo texto que buscarías en el sitio: «fondos mutuos exterior»,
    «bancos balance», «seguros renta fija». Devuelve `id`, sector, filas, corte,
    clave primaria y la lista de columnas en una línea: con eso ya se puede
    escribir el SQL de `ejecutar`.
    """
    limite = max(1, min(int(limite or 5), 20))
    sif = cliente()
    candidatos = [o for o in sif.tablas() if not sector or o.get("sector") == sector]
    familias = _familias(texto)
    # Puntuación por palabras (no coincidencia literal: «fondos mutuos exterior»
    # no aparece escrito así en ninguna parte del catálogo).
    puntuados = sorted(((_puntuar(o, familias), o) for o in candidatos), key=lambda p: (-p[0], p[1]["id"]))
    encontrados = [o for puntaje, o in puntuados if puntaje > 0]
    fichas = []
    for objeto in encontrados[:limite]:
        try:
            columnas = [c["nombre"] for c in sif.esquema(objeto["id"])["columnas"]]
        except Exception:  # noqa: BLE001 - un esquema roto no debe tumbar la búsqueda
            columnas = []
        fichas.append(_ficha(objeto, columnas))
    salida: dict[str, Any] = {"consulta": texto, "total": len(encontrados), "objetos": fichas}
    if not encontrados:
        salida["pista"] = ("Sin coincidencias. Prueba con el sector (ffmm, bancos, seguros, "
                           "macro, fi, agf, ccaf) o con menos palabras.")
    elif len(encontrados) > len(fichas):
        salida["pista"] = f"Hay {len(encontrados)} objetos; sube `limite` o acota `sector`."
    return json.dumps(salida, ensure_ascii=False)


def ejecutar(sql: str, limite: int = 50) -> str:
    """Ejecuta SQL de solo lectura (DuckDB) sobre los 90 objetos y devuelve columnas y filas.

    Una sentencia por vez, sin escrituras. Filtra siempre por `periodo` (texto
    `AAAA-MM`) antes de agregar y usa `max(periodo)` para el último publicado.
    El RUT va sin dígito verificador en `rut`; el DV, si existe, en `rut_dv`.
    """
    limite = max(1, min(int(limite or 50), MAX_FILAS))
    sif = cliente()
    try:
        consulta = sif.sql(sql, limite=limite + 1)
        columnas = [d[0] for d in consulta.description]
        filas = consulta.fetchall()
    except ValueError as exc:  # el guardia de solo lectura
        return json.dumps({"error": str(exc),
                           "pista": "Se aceptan SELECT/WITH/DESCRIBE y una sola sentencia."},
                          ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001 - el agente necesita el motivo, no un traceback
        primero = str(exc).splitlines()[0][:300]
        pista = ("Revisa el nombre de la tabla y sus columnas con sif_buscar antes de "
                 "reintentar; no inventes columnas.")
        if "does not exist" in primero or "Referenced column" in primero:
            pista = "Esa tabla o columna no existe en el contrato: búscala con sif_buscar."
        return json.dumps({"error": primero, "pista": pista}, ensure_ascii=False)

    truncado = len(filas) > limite
    return json.dumps({
        "filas": min(len(filas), limite),
        "truncado": truncado,
        "columnas": columnas,
        "datos": [[_recortar(v) for v in fila] for fila in filas[:limite]],
    }, ensure_ascii=False, default=str)


def contar_tokens(texto: str) -> int:
    """Aproximación de tokens (4 caracteres ≈ 1 token, el sesgo habitual en JSON).

    Se usa solo para vigilar el presupuesto de contexto; el número exacto depende
    del tokenizador de cada modelo.
    """
    return (len(texto) + 3) // 4

"""Guardia de solo lectura para las consultas del SDK.

Es el mismo criterio que aplica la consola de la web (`docs/js/sql_guard.js`),
portado a Python. Sirve para que una consulta copiada de un tercero no altere la
sesión de quien la ejecuta:

    DROP VIEW agf_balance;                        → la tabla desaparece
    CREATE OR REPLACE VIEW agf_balance AS ...;    → la tabla muestra datos inventados
    SELECT ... INTO falso;                        → filas fabricadas

**No es una frontera de seguridad.** Quien quiera puede importar duckdb y
consultar los Parquet directamente; esto evita accidentes y enlaces hostiles,
no atacantes. La frontera real es que los archivos publicados son de solo
lectura y que el SDK nunca ejecuta SQL que no venga del usuario.

Se aplica **después** de quitar comentarios y literales, para que un valor que
contenga la palabra "drop" no bloquee una consulta legítima y para que un
comentario no pueda esconder una sentencia.
"""
from __future__ import annotations

import re

# Sentencias que solo leen. Todo lo demás queda fuera.
PERMITIDAS = (
    "SELECT", "WITH", "VALUES", "TABLE", "DESCRIBE", "DESC", "SHOW",
    "EXPLAIN", "SUMMARIZE", "PRAGMA", "PIVOT", "UNPIVOT",
)

# Palabras que convierten una consulta en escritura aunque no vayan al inicio.
# `SELECT ... INTO tabla` crea una tabla (CTAS) sin que suene a escritura.
ESCRITURA_SUELTA = re.compile(r"\b(INTO|COPY|ATTACH|DETACH|INSTALL|LOAD)\b", re.I)


def limpiar(sql: str) -> str:
    """Quita comentarios y literales y deja el esqueleto de la sentencia."""
    s = "" if sql is None else str(sql)
    salida: list[str] = []
    i = 0
    while i < len(s):
        dos = s[i:i + 2]
        if dos == "--":
            fin = s.find("\n", i)
            i = len(s) if fin == -1 else fin + 1
            salida.append("\n")
            continue
        if dos == "/*":
            fin = s.find("*/", i + 2)
            i = len(s) if fin == -1 else fin + 2
            salida.append(" ")
            continue
        c = s[i]
        if c in ("'", '"'):
            cierre = c
            j = i + 1
            while j < len(s):
                if s[j] == cierre:
                    # '' dentro de un literal es una comilla escapada, no el cierre.
                    if cierre == "'" and j + 1 < len(s) and s[j + 1] == "'":
                        j += 2
                        continue
                    break
                if s[j] == "\\":
                    j += 2
                    continue
                j += 1
            salida.append(" " + "·" * max(1, j - i) + " ")
            i = j + 1
            continue
        salida.append(c)
        i += 1
    return "".join(salida)


def sentencias(esqueleto: str) -> list[str]:
    return [t.strip() for t in re.split(r";", esqueleto) if t.strip()]


def primera_palabra(sentencia: str) -> str:
    m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", sentencia)
    return m.group(1).upper() if m else ""


def validar(sql: str) -> tuple[bool, str]:
    """Devuelve (permitida, motivo). El motivo está escrito para mostrarse tal cual."""
    original = "" if sql is None else str(sql)
    if not original.strip():
        return False, "La consulta está vacía."

    partes = sentencias(limpiar(original))
    if not partes:
        return False, "La consulta está vacía o es solo un comentario."
    if len(partes) > 1:
        return False, (
            f"Solo se ejecuta una sentencia por vez y esta trae {len(partes)}. "
            "No se permite encadenar sentencias con «;»: ahí es donde una consulta "
            "inocente podría esconder un DROP o un INSERT."
        )

    sentencia = partes[0]
    verbo = primera_palabra(sentencia)
    if not verbo:
        return False, "No se reconoce el inicio de la consulta."
    if verbo not in PERMITIDAS:
        return False, (
            f"«{verbo}» no está permitido. Se aceptan consultas que empiecen con "
            f"{', '.join(PERMITIDAS[:6])} (entre otras de lectura). Nada de lo que "
            "escribas puede modificar los datos publicados, pero sí podría alterar "
            "lo que ves en tu propia sesión: por eso se bloquea."
        )
    hallada = ESCRITURA_SUELTA.search(sentencia)
    if hallada:
        return False, (
            f"La consulta empieza con «{verbo}» pero contiene «{hallada.group(1).upper()}», "
            "que escribe en la base (por ejemplo SELECT ... INTO crea una tabla). "
            "El SDK es de solo lectura."
        )
    return True, ""


def exigir(sql: str) -> str:
    """Valida y devuelve el SQL, o lanza ValueError con el motivo."""
    ok, motivo = validar(sql)
    if not ok:
        raise ValueError(motivo)
    return sql

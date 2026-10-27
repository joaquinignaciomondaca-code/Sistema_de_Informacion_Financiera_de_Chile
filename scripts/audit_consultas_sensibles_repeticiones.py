#!/usr/bin/env python3
"""Detecta consultas SQL sugeridas sensibles a filas exactamente repetidas.

Compara las consultas que ve una persona en el explorador y en los chips SQL
contra dos registros locales de las vistas semánticas:

1. vistas normales, con las filas publicadas;
2. contrafactual de sensibilidad, con SELECT DISTINCT * aplicado al Parquet
   que consume cada vista SQL.

El segundo registro es sólo un experimento: no propone deduplicar, no demuestra
que una repetición sea inválida y no atribuye su causa a la fuente ni al ETL.
Una salida distinta localiza una consulta que cambia bajo esa hipótesis y que
lee una vista con repetidas en el conjunto completo; no prueba que el cambio
proceda de filas dentro del subconjunto filtrado ni certifica la semántica.

Uso:
    python3 scripts/audit_consultas_sensibles_repeticiones.py
    python3 scripts/audit_consultas_sensibles_repeticiones.py --check

`--check` falla únicamente si una consulta sugerida no puede ejecutarse en
alguno de los dos registros. Las diferencias son hallazgos, no errores.
Requiere DuckDB.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipelines.api import vistas as V  # noqa: E402
from scripts.audit_consultas_sugeridas import (  # noqa: E402
    consultas_sugeridas,
    consultas_terminal,
)

TABLE_REF = re.compile(r'(?i)\b(?:from|join)\s+(?:"([^"]+)"|([A-Za-z_][A-Za-z0-9_]*))')


def _crear_vistas(con: Any, vistas: list[dict], alias: dict[str, list[str]], *, distinct: bool) -> list[str]:
    """Registra las vistas usando las mismas rutas/filtros que el cliente web."""
    sin_archivo = []
    select = "SELECT DISTINCT *" if distinct else "SELECT *"
    for vista in vistas:
        ficheros = V.ficheros_sql_de(vista)
        if not ficheros:
            sin_archivo.append(vista["name"])
            continue
        filtro = f" WHERE {vista['where']}" if "where" in vista else ""
        scope = "TEMP " if vista.get("latestManifestFile") else ""
        con.execute(
            f'CREATE OR REPLACE {scope}VIEW "{vista["name"]}" AS '
            f"{select} FROM read_parquet({ficheros!r}, union_by_name=true){filtro}"
        )
        for viejo in alias.get(vista["name"], []):
            con.execute(
                f'CREATE OR REPLACE VIEW "{viejo}" AS SELECT * FROM "{vista["name"]}"'
            )
    return sin_archivo


def _normalizar_valor(valor: Any) -> Any:
    """Normaliza el ruido de agregación de floats a unas 12 cifras significativas."""
    if isinstance(valor, float):
        return ("__float__", format(valor, ".12g"))
    if isinstance(valor, tuple):
        return tuple(_normalizar_valor(item) for item in valor)
    if isinstance(valor, list):
        return [_normalizar_valor(item) for item in valor]
    return valor


def _salida(con: Any, sql: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Devuelve nombres de columnas y filas serializadas en orden estable."""
    cursor = con.execute(sql)
    columnas = tuple(item[0] for item in cursor.description or ())
    filas = tuple(sorted(repr(_normalizar_valor(tuple(fila))) for fila in cursor.fetchall()))
    return columnas, filas


def _hash(columnas: tuple[str, ...], filas: tuple[str, ...]) -> str:
    cuerpo = json.dumps([columnas, filas], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()


def _diferencia(filas_base: tuple[str, ...], filas_distintas: tuple[str, ...]) -> tuple[int, int]:
    """Filas resultado quitadas y agregadas/modificadas por el contrafactual."""
    base = Counter(filas_base)
    distinta = Counter(filas_distintas)
    removidas = sum((base - distinta).values())
    agregadas = sum((distinta - base).values())
    return removidas, agregadas


def _referencias(sql: str, conocidas: set[str]) -> list[str]:
    encontradas = set()
    for m in TABLE_REF.finditer(sql):
        nombre = m.group(1) or m.group(2)
        if nombre in conocidas:
            encontradas.add(nombre)
    return sorted(encontradas)


def _duplicados_por_vista(con: Any, nombres: list[str]) -> dict[str, int]:
    resultado = {}
    for nombre in nombres:
        n = con.execute(
            f'SELECT count(*) - (SELECT count(*) FROM '
            f'(SELECT DISTINCT * FROM "{nombre}")) FROM "{nombre}"'
        ).fetchone()[0]
        resultado[nombre] = int(n)
    return resultado


def auditar() -> tuple[list[dict], list[dict], list[str], dict]:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError("DuckDB no está instalado") from exc

    semanticas = V.vistas_semanticas()
    auxiliares = V.vistas_sql_auxiliares()
    vistas = semanticas + auxiliares
    alias = V.alias_heredados()
    normales = duckdb.connect()
    contrafactuales = duckdb.connect()
    sin_archivo = _crear_vistas(normales, vistas, alias, distinct=False)
    _crear_vistas(contrafactuales, vistas, alias, distinct=True)

    consultas = consultas_sugeridas() + consultas_terminal()
    nombres = {vista["name"] for vista in vistas}
    nombres.update(viejo for lista in alias.values() for viejo in lista)
    duplicados = _duplicados_por_vista(normales, sorted(nombres.intersection(
        vista["name"] for vista in vistas if vista["name"] not in sin_archivo
    )))

    cambios, errores = [], []
    alias_a_canonica = {
        viejo: canonico
        for canonico, viejos in alias.items()
        for viejo in viejos
    }
    consultas_con_repetidas = 0
    consultas_sin_cambio = 0
    for etiqueta, sql in consultas:
        referencias = _referencias(sql, nombres)
        vistas_canonicas = sorted({alias_a_canonica.get(nombre, nombre) for nombre in referencias})
        refs_con_repetidas = {
            nombre: duplicados.get(nombre, 0)
            for nombre in vistas_canonicas
            if duplicados.get(nombre, 0) > 0
        }
        # Las consultas que no leen ninguna vista con filas repetidas no forman
        # parte de esta auditoría. Así evitamos atribuir al DISTINCT diferencias
        # de orden de agregación o de punto flotante ajenas a duplicados.
        if not refs_con_repetidas:
            continue
        consultas_con_repetidas += 1
        try:
            columnas_base, filas_base = _salida(normales, sql)
            columnas_distintas, filas_distintas = _salida(contrafactuales, sql)
        except Exception as exc:  # una consulta rota se informa y --check la hace fallar
            errores.append({"etiqueta": etiqueta, "error": str(exc).splitlines()[0]})
            continue
        if columnas_base != columnas_distintas:
            errores.append({"etiqueta": etiqueta, "error": "cambió el esquema de salida"})
            continue
        if filas_base == filas_distintas:
            consultas_sin_cambio += 1
            continue
        removidas, agregadas = _diferencia(filas_base, filas_distintas)
        cambios.append({
            "etiqueta": etiqueta,
            "sha256_sql": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            "vistas_referenciadas": referencias,
            "filas_extra_en_vistas_referenciadas": refs_con_repetidas,
            "filas_resultado_publicado": len(filas_base),
            "filas_resultado_con_distinct": len(filas_distintas),
            "filas_salida_removidas": removidas,
            "filas_salida_agregadas_o_modificadas": agregadas,
            "sha256_salida_publicada": _hash(columnas_base, filas_base),
            "sha256_salida_con_distinct": _hash(columnas_distintas, filas_distintas),
            "sql": sql,
        })
    normales.close()
    contrafactuales.close()
    resumen = {
        "consultas_totales": len(consultas),
        "consultas_con_vistas_repetidas": consultas_con_repetidas,
        "consultas_con_vistas_repetidas_sin_cambio": consultas_sin_cambio,
        "consultas_con_salida_distinta": len(cambios),
        "consultas_sql_distintas_con_salida_distinta": len({
            hallazgo["sha256_sql"] for hallazgo in cambios
        }),
    }
    return cambios, errores, sin_archivo, resumen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fallar si alguna consulta no ejecuta")
    parser.add_argument("--json", action="store_true", help="imprimir los hallazgos completos en JSON")
    args = parser.parse_args()
    try:
        cambios, errores, sin_archivo, resumen = auditar()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "consultas": resumen,
            "hallazgos": cambios,
            "errores": errores,
            "vistas_sin_archivo": sin_archivo,
            "nota": "Contrafactual de sensibilidad; no recomienda deduplicar ni clasifica causa o validez.",
        }, ensure_ascii=False, indent=2))
    else:
        print(f"Consultas sugeridas analizadas: {len(consultas_sugeridas()) + len(consultas_terminal())}")
        print(f"Vistas sin archivo: {len(sin_archivo)}" + (f" ({', '.join(sin_archivo)})" if sin_archivo else ""))
        print(f"Consultas que referencian vistas con repetidas exactas: {resumen['consultas_con_vistas_repetidas']}")
        print(f"De ellas, salida estable bajo DISTINCT: {resumen['consultas_con_vistas_repetidas_sin_cambio']}")
        print(f"De ellas, salida distinta bajo el contrafactual: {resumen['consultas_con_salida_distinta']} ({resumen['consultas_sql_distintas_con_salida_distinta']} SQL distintas)")
        print(f"Consultas con error en cualquiera de las dos corridas: {len(errores)}")
        for hallazgo in cambios:
            referencias = hallazgo["filas_extra_en_vistas_referenciadas"]
            detalle = ", ".join(f"{nombre} (+{n} en vista completa)" for nombre, n in referencias.items())
            print(f"  · {hallazgo['etiqueta']} [{detalle}] "
                  f"salida {hallazgo['filas_resultado_publicado']}→{hallazgo['filas_resultado_con_distinct']} filas")
        if errores:
            for error in errores:
                print(f"  ERROR {error['etiqueta']}: {error['error']}")
        print("Nota: sensibilidad a filas exactas, no una clasificación semántica ni una corrección sugerida.")

    return 1 if args.check and errores else 0


if __name__ == "__main__":
    raise SystemExit(main())

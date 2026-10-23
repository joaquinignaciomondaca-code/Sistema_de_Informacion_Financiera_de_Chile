#!/usr/bin/env python3
"""Publica el resultado de las 156 consultas como JSON estático (fase 3 de la ruta).

El SQL remoto de verdad —un DuckDB servido con Quack— necesita una máquina que
atienda conexiones, y este sitio es estático: GitHub Pages sirve archivos y no
ejecuta procesos; Actions no recibe tráfico entrante. Así que la fase 3 se
resuelve donde sí cabe: se calculan las consultas **en el build** y cada una se
publica como un archivo.

    docs/api/v2/resultados/{id}.json      columnas, filas y el SQL que las produjo
    docs/api/v2/resultados/index.json     qué hay, cuántas filas y cuánto pesa

Con eso, quien no quiere bajar 500 MB de Parquet (una planilla, un R, un agente
sin DuckDB) obtiene el número con un `curl` a una URL estable, y el resultado
lleva dentro su `data_release` para poder citarlo.

Medido sobre la edición 2026-10-22: 156 consultas en 2,1 s y ~700 KB en total.

Uso:
    python3 scripts/build_resultados.py             # escribe los 156 archivos
    python3 scripts/build_resultados.py --check     # falla si están atrasados
"""
from __future__ import annotations

import argparse
import datetime as dt
import decimal
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
V2 = DOCS / "api" / "v2"
SALIDA = V2 / "resultados"

BASE = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile"
# Tope de filas por resultado: el mismo criterio que el servidor MCP. Una
# consulta que devuelve más es una descarga, y para eso ya están los Parquet.
MAX_FILAS = 500


def _json(valor):
    """JSON sin tipos de DuckDB, para que el archivo se lea con cualquier cosa."""
    if isinstance(valor, (dt.date, dt.datetime)):
        return valor.isoformat()
    if isinstance(valor, decimal.Decimal):
        return float(valor)
    return valor


def _conectar():
    import duckdb

    sql = (V2 / "views.sql").read_text(encoding="utf-8")
    con = duckdb.connect()
    con.execute(sql.replace(f"'{BASE}'", f"'{DOCS}'"))
    return con


def _consulta(con, c: dict) -> dict:
    cuerpo = c["sql"].strip().rstrip(";")
    # `ORDER BY ALL`: sin esto, un GROUP BY con empates devuelve las filas en
    # otro orden en cada corrida y el archivo cambia sin que cambie el dato.
    resultado = con.execute(
        f"SELECT * FROM ({cuerpo}) ORDER BY ALL LIMIT {MAX_FILAS + 1}")
    columnas = [d[0] for d in resultado.description]
    filas = resultado.fetchall()
    truncado = len(filas) > MAX_FILAS
    filas = filas[:MAX_FILAS]
    return {
        "columnas": columnas,
        "filas": len(filas),
        "truncado": truncado,
        "datos": [[_json(v) for v in fila] for fila in filas],
    }


def construir() -> tuple[dict[str, str], dict]:
    """Devuelve `{nombre: contenido}` y el índice. Determinista, sin `now()`."""
    catalogo = json.loads((V2 / "catalog.json").read_text(encoding="utf-8"))
    consultas = json.loads((V2 / "queries.json").read_text(encoding="utf-8"))["consultas"]
    con = _conectar()
    archivos: dict[str, str] = {}
    indice = []
    for c in consultas:
        cuerpo = _consulta(con, c)
        documento = {
            "contrato": "sif-api/resultado",
            "id": c["id"],
            "titulo": c["titulo"],
            "origen": c.get("origen"),
            "data_release": catalogo["data_release"],
            "generado": catalogo["generado"],
            "max_filas": MAX_FILAS,
            **cuerpo,
            "sql": c["sql"].strip(),
            "como_se_genera": "python3 scripts/build_resultados.py",
        }
        texto = json.dumps(documento, ensure_ascii=False, indent=1) + "\n"
        archivos[f"{c['id']}.json"] = texto
        indice.append({
            "id": c["id"],
            "titulo": c["titulo"],
            "origen": c.get("origen"),
            "filas": cuerpo["filas"],
            "columnas": cuerpo["columnas"],
            "truncado": cuerpo["truncado"],
            "bytes": len(texto.encode("utf-8")),
            "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            "url": f"/api/v2/resultados/{c['id']}.json",
        })

    resumen = {
        "contrato": "sif-api/resultados",
        "version": "1.0.0",
        "base": BASE,
        "data_release": catalogo["data_release"],
        "generado": catalogo["generado"],
        "total": len(indice),
        "filas": sum(i["filas"] for i in indice),
        "bytes": sum(i["bytes"] for i in indice),
        "truncadas": sum(1 for i in indice if i["truncado"]),
        "max_filas": MAX_FILAS,
        "nota": ("Resultados calculados en el build sobre el mismo Parquet que publica el "
                 "sitio. No es SQL arbitrario: son las 156 consultas del catálogo, cada una "
                 "con su SQL a la vista para poder reproducirla o discutirla."),
        "como_se_genera": "python3 scripts/build_resultados.py",
        "consultas": indice,
    }
    return archivos, resumen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="falla si los resultados están atrasados")
    args = ap.parse_args()

    archivos, resumen = construir()
    texto_indice = json.dumps(resumen, ensure_ascii=False, indent=1) + "\n"

    if args.check:
        problemas = []
        if not SALIDA.exists():
            problemas.append("falta la carpeta resultados/")
        for nombre, esperado in archivos.items():
            ruta = SALIDA / nombre
            if not ruta.exists():
                problemas.append(f"falta {nombre}")
            elif ruta.read_text(encoding="utf-8") != esperado:
                problemas.append(f"atrasado: {nombre}")
        indice = SALIDA / "index.json"
        if not indice.exists():
            problemas.append("falta index.json")
        elif indice.read_text(encoding="utf-8") != texto_indice:
            problemas.append("atrasado: index.json")
        sobran = ({p.name for p in SALIDA.glob("*.json")} - set(archivos) - {"index.json"}) \
            if SALIDA.exists() else set()
        for nombre in sorted(sobran):
            problemas.append(f"sobra {nombre}")
        for p in problemas[:15]:
            print(f"[FALLA] {p}")
        if problemas:
            print(f"\nRESULTADOS: {len(problemas)} archivo(s) fuera de fecha. "
                  f"Ejecuta: python3 scripts/build_resultados.py")
            print("Si vuelve a fallar con los archivos recién generados, la consulta no es "
                  "determinista: su ORDER BY tiene empates y el LIMIT elige filas distintas "
                  "en cada corrida. Añade un desempate al ORDER BY en docs/js/sidebar.js.")
            return 1
        print(f"RESULTADOS: {resumen['total']} consultas, {resumen['filas']} filas y "
              f"{resumen['bytes']} B al día")
        return 0

    SALIDA.mkdir(parents=True, exist_ok=True)
    for viejo in SALIDA.glob("*.json"):
        viejo.unlink()
    for nombre, contenido in archivos.items():
        (SALIDA / nombre).write_text(contenido, encoding="utf-8")
    (SALIDA / "index.json").write_text(texto_indice, encoding="utf-8")
    print(f"Resultados: {resumen['total']} archivos · {resumen['filas']} filas · "
          f"{resumen['bytes'] / 1024:.0f} KB · {resumen['truncadas']} truncada(s)")
    print(f"Índice: {(SALIDA / 'index.json').relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

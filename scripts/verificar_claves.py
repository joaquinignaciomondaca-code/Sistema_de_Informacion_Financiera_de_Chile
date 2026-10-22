#!/usr/bin/env python3
"""Verifica las claves de los objetos publicados (Fase 1a de la ruta de la API).

Una tabla sin clave declarada obliga al cliente a adivinar cómo agregar, y una
clave declarada que no es única es peor: promete algo falso. Este script prueba
las dos cosas **sobre todas las filas publicadas**, no sobre una muestra.

Qué hace, por objeto:

  1. **Clave primaria.** Si el diccionario declara una (`rol: PK`), la prueba.
     Si falla, no se queda ahí: busca la combinación mínima de columnas que sí
     sea única (empezando por las más selectivas) y dice cuál hace falta.
     Si el objeto no declara ninguna, la busca igual y la publica como
     *propuesta*. Si ni todas las columnas juntas son únicas, hay **filas
     repetidas**: eso se reporta y el objeto no recibe clave.
  2. **Clave foránea.** Para cada columna `rol: FK`, resuelve el destino por
     convención (la lista de entidades del mismo sector que tenga esa columna)
     y mide la tasa de coincidencia, con las huérfanas contadas por objeto.

Niveles de control (los que luego consume `docs/api/reglas.json`):

  * `invariante`: una PK declarada que no es única. Rompe el build.
  * `expectativa`: filas repetidas o una FK por debajo del umbral. Avisa.
  * `informativo`: PK propuesta para un objeto que no la declaraba, y FK sin
    destino resoluble. Sólo se registra.

Genera `docs/api/claves.csv`.

Uso:
    python3 scripts/verificar_claves.py                 # escribe el CSV
    python3 scripts/verificar_claves.py --check         # falla si hay invariantes rotos
    python3 scripts/verificar_claves.py --umbral-fk 0.95
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
sys.path.insert(0, str(RAIZ / "scripts"))

import audit_consultas_sugeridas as ac  # noqa: E402

DESTINO = DOCS / "api" / "claves.csv"
REGLAS = DOCS / "api" / "reglas.json"
ESQUEMAS = DOCS / "api" / "esquemas.json"
DICCIONARIO = DOCS / "reproducibilidad" / "diccionario.csv"

CAMPOS = [
    "objeto", "tipo", "columnas", "destino", "filas", "distintas",
    "sobrantes", "tasa", "declarada", "nivel", "estado", "detalle",
]


def cargar_roles() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """{objeto: [columnas PK]} y {objeto: [columnas FK]} desde el diccionario."""
    pk: dict[str, list[str]] = {}
    fk: dict[str, list[str]] = {}
    if not DICCIONARIO.exists():
        return pk, fk
    with DICCIONARIO.open(encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            if fila["rol"] in ("PK", "PK parcial"):
                pk.setdefault(fila["vista"], []).append(fila["columna"])
            elif fila["rol"] == "FK":
                fk.setdefault(fila["vista"], []).append(fila["columna"])
    return pk, fk


def registrar(con: duckdb.DuckDBPyConnection, objetos: dict, prefijo: str = "o_") -> dict[str, str]:
    """Crea una vista por objeto con datos y devuelve {objeto: vista}."""
    vistas = {}
    for nombre, info in objetos.items():
        if not info.get("columnas"):
            continue
        vista = ac.vistas_semanticas()
        datos = next(v for v in vista if v["name"] == nombre)
        ficheros = ac.ficheros_de(datos)
        if not ficheros:
            continue
        alias = f"{prefijo}{nombre}"
        sql = f"CREATE OR REPLACE VIEW {alias} AS SELECT * FROM read_parquet({json.dumps(ficheros)})"
        if datos.get("where"):
            sql += f" WHERE {datos['where']}"
        con.execute(sql)
        vistas[nombre] = alias
    return vistas


def contar(con, vista: str) -> int:
    return con.execute(f"SELECT count(*) FROM {vista}").fetchone()[0]


def selectividad(con, vista: str, columnas: list[str]) -> dict[str, int]:
    """Distintos por columna en una sola pasada."""
    expr = ", ".join(f"count(DISTINCT {c})" for c in columnas)
    fila = con.execute(f"SELECT {expr} FROM {vista}").fetchone()
    return dict(zip(columnas, fila))


def distintos(con, vista: str, columnas: list[str]) -> int:
    cols = ", ".join(columnas)
    return con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {cols} FROM {vista})").fetchone()[0]


def buscar_clave(con, vista: str, columnas: list[str], filas: int, limite: int = 12) -> tuple[list[str], bool]:
    """Combinación mínima de columnas única. Devuelve (columnas, es_unica).

    Primero prueba acumulando las más selectivas (un id suele bastar). Si con
    las 12 primeras no alcanza, sigue sólo con las filas que chocan —que son
    pocas— añadiendo la columna que más las separa. Cada paso usa una tabla
    temporal nueva: reemplazar la anterior mientras se lee devuelve vacío y
    daría por buena una clave falsa.
    """
    orden = sorted(columnas, key=lambda c: -selectividad(con, vista, [c])[c])
    elegidas: list[str] = []
    for col in orden[:limite]:
        elegidas.append(col)
        if distintos(con, vista, elegidas) == filas:
            return elegidas, True

    fuente = vista
    for intento in range(len(orden)):
        clave = ", ".join(elegidas)
        nueva = f"_dup_{intento}"
        con.execute(
            f"CREATE OR REPLACE TEMP TABLE {nueva} AS SELECT * FROM {fuente} "
            f"WHERE ({clave}) IN (SELECT {clave} FROM {fuente} GROUP BY {clave} HAVING count(*) > 1)"
        )
        total = con.execute(f"SELECT count(*) FROM {nueva}").fetchone()[0]
        if total == 0:
            return elegidas, True
        fuente = nueva
        mejor, mejor_n = None, 0
        for col in [c for c in orden if c not in elegidas]:
            prueba = ", ".join(elegidas + [col])
            n = con.execute(f"SELECT count(*) FROM (SELECT DISTINCT {prueba} FROM {fuente})").fetchone()[0]
            if n == total:  # esa columna sola desempata las repetidas
                return elegidas + [col], True
            if n > mejor_n:
                mejor, mejor_n = col, n
        if mejor is None:
            break
        elegidas.append(mejor)
        if distintos(con, vista, elegidas) == filas:
            return elegidas, True

    if distintos(con, vista, columnas) == filas:
        return columnas, True  # no hay clave corta: sólo la fila completa
    return elegidas, False


def resolver_destino(objeto: str, columna: str, objetos: dict, fk_roles: dict[str, list[str]]) -> str | None:
    """Lista de entidades del mismo sector que tenga esa columna."""
    sector = (objetos[objeto].get("sector") or "")
    candidatas = [
        n for n, i in objetos.items()
        if n.endswith("lista_entidades") and any(c["nombre"] == columna for c in i.get("columnas") or [])
    ]
    if not candidatas:
        return None
    propias = [n for n in candidatas if n.startswith(sector + "_")] if sector else []
    # Sólo vale una lista del mismo sector: un RUT de caja de compensación
    # cotejado contra la lista de bancos da 100 % de huérfanas y no significa
    # nada. Si el sector no publica lista con esa columna, no hay destino.
    return sorted(propias)[0] if propias else None


def excepciones() -> dict[str, str]:
    """Objetos cuya PK declarada ya se sabe que no es única, con su motivo."""
    if not REGLAS.exists():
        return {}
    datos = json.loads(REGLAS.read_text(encoding="utf-8"))
    return {
        e["objeto"]: e.get("motivo", "")
        for e in datos.get("excepciones", [])
        if e.get("regla") == "claves.pk_declarada"
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="falla si una invariante no se cumple")
    ap.add_argument("--umbral-fk", type=float, default=0.90, help="tasa mínima de coincidencia de una FK")
    args = ap.parse_args()

    doc = json.loads(ESQUEMAS.read_text(encoding="utf-8"))
    objetos = doc["objetos"]
    pk_roles, fk_roles = cargar_roles()

    con = duckdb.connect()
    con.execute("SET threads TO 4")
    vistas = registrar(con, objetos)

    filas_salida: list[dict] = []
    invariantes: list[str] = []
    expectativas: list[str] = []

    for nombre in sorted(vistas):
        vista = vistas[nombre]
        columnas = [c["nombre"] for c in objetos[nombre]["columnas"]]
        filas = contar(con, vista)

        # --- clave primaria -------------------------------------------------
        declarada = pk_roles.get(nombre, [])
        propias = [c for c in declarada if c in columnas]
        if propias:
            unicas = distintos(con, vista, propias)
            if unicas == filas:
                filas_salida.append({
                    "objeto": nombre, "tipo": "pk", "columnas": " + ".join(propias),
                    "destino": "", "filas": filas, "distintas": unicas, "sobrantes": filas - unicas,
                    "tasa": "", "declarada": "si", "nivel": "invariante", "estado": "ok",
                    "detalle": "la clave declarada es única sobre todas las filas",
                })
            else:
                clave, unica = buscar_clave(con, vista, columnas, filas)
                invariantes.append(
                    f"{nombre}: PK declarada ({', '.join(propias)}) con {filas - unicas} filas repetidas"
                )
                completa = unica and len(clave) == len(columnas)
                filas_salida.append({
                    "objeto": nombre, "tipo": "pk", "columnas": " + ".join(propias),
                    "destino": "", "filas": filas, "distintas": unicas, "sobrantes": filas - unicas,
                    "tasa": "", "declarada": "si", "nivel": "invariante", "estado": "falla",
                    "detalle": (
                        "no es única; no hay clave corta y sólo la fila completa es única"
                        if completa
                        else f"no es única; clave mínima única: {' + '.join(clave)}" if unica
                        else f"no es única y la fila completa tampoco: {filas - distintas(con, vista, columnas)} filas idénticas"
                    ),
                })
        else:
            clave, unica = buscar_clave(con, vista, columnas, filas)
            if unica and len(clave) < len(columnas):
                filas_salida.append({
                    "objeto": nombre, "tipo": "pk", "columnas": " + ".join(clave),
                    "destino": "", "filas": filas, "distintas": filas, "sobrantes": 0,
                    "tasa": "", "declarada": "no", "nivel": "informativo", "estado": "propuesta",
                    "detalle": "clave mínima encontrada; el diccionario no la declaraba",
                })
            elif unica:
                filas_salida.append({
                    "objeto": nombre, "tipo": "pk", "columnas": "fila completa",
                    "destino": "", "filas": filas, "distintas": filas, "sobrantes": 0,
                    "tasa": "", "declarada": "no", "nivel": "informativo", "estado": "fila_completa",
                    "detalle": "no hay clave corta; la única garantía de unicidad es la fila entera",
                })
            else:
                todas = distintos(con, vista, columnas)
                expectativas.append(
                    f"{nombre}: {filas - todas} filas repetidas con todas las columnas ({todas} distintas de {filas})"
                )
                filas_salida.append({
                    "objeto": nombre, "tipo": "pk", "columnas": "", "destino": "",
                    "filas": filas, "distintas": todas, "sobrantes": filas - todas,
                    "tasa": "", "declarada": "no", "nivel": "expectativa", "estado": "sin_clave",
                    "detalle": "ninguna combinación es única: hay filas idénticas publicadas",
                })

        # --- claves foráneas ------------------------------------------------
        for col in fk_roles.get(nombre, []):
            if col not in columnas:
                continue
            destino = resolver_destino(nombre, col, objetos, fk_roles)
            if destino is None:
                filas_salida.append({
                    "objeto": nombre, "tipo": "fk", "columnas": col, "destino": "",
                    "filas": filas, "distintas": "", "sobrantes": "", "tasa": "",
                    "declarada": "si", "nivel": "informativo", "estado": "sin_destino",
                    "detalle": "ningún objeto lista_entidades publica esa columna",
                })
                continue
            if destino not in vistas:
                continue
            if filas == 0:
                filas_salida.append({
                    "objeto": nombre, "tipo": "fk", "columnas": col, "destino": destino,
                    "filas": 0, "distintas": "", "sobrantes": "", "tasa": "",
                    "declarada": "si", "nivel": "informativo", "estado": "sin_datos",
                    "detalle": "el objeto no publica filas: la relación no se puede medir",
                })
                continue
            # Un RUT guardado como entero en la lista de entidades y como texto
            # en el hecho no se puede comparar sin cast; se compara como texto
            # para medir la relación real, y se deja dicho.
            tipo_origen = next(c["tipo"] for c in objetos[nombre]["columnas"] if c["nombre"] == col)
            tipo_destino = next(
                c["tipo"] for c in objetos[destino]["columnas"] if c["nombre"] == col
            )
            aviso_tipo = ""
            if tipo_origen != tipo_destino:
                aviso_tipo = f"tipos distintos en la columna ({tipo_origen} aquí, {tipo_destino} en el destino): el join exige cast"
            coinciden = con.execute(
                f"SELECT count(*) FROM {vista} o WHERE CAST(o.{col} AS VARCHAR) IN "
                f"(SELECT CAST({col} AS VARCHAR) FROM {vistas[destino]})"
            ).fetchone()[0]
            tasa = coinciden / filas if filas else 0.0
            estado = "ok" if tasa >= args.umbral_fk else "huerfanas"
            nivel = "expectativa" if estado == "huerfanas" else "invariante"
            if estado == "huerfanas":
                expectativas.append(
                    f"{nombre}.{col} → {destino}: {filas - coinciden} huérfanas ({(1 - tasa) * 100:.1f} %)"
                )
            filas_salida.append({
                "objeto": nombre, "tipo": "fk", "columnas": col, "destino": destino,
                "filas": filas, "distintas": "", "sobrantes": filas - coinciden,
                "tasa": f"{tasa:.4f}", "declarada": "si", "nivel": nivel, "estado": estado,
                "detalle": aviso_tipo or ("" if estado == "ok" else f"{filas - coinciden} valores sin pareja en el destino"),
            })

    con.close()

    with DESTINO.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas_salida)

    pk = [f for f in filas_salida if f["tipo"] == "pk"]
    fk = [f for f in filas_salida if f["tipo"] == "fk"]
    print(f"Objetos con datos: {len(vistas)}")
    print(f"  PK: {len([f for f in pk if f['estado'] == 'ok'])} verificadas · "
          f"{len([f for f in pk if f['estado'] == 'propuesta'])} propuestas · "
          f"{len([f for f in pk if f['estado'] == 'fila_completa'])} sólo fila completa · "
          f"{len([f for f in pk if f['estado'] == 'sin_clave'])} sin clave · "
          f"{len([f for f in pk if f['estado'] == 'falla'])} declaradas falsas")
    print(f"  FK: {len([f for f in fk if f['estado'] == 'ok'])} ok · "
          f"{len([f for f in fk if f['estado'] == 'huerfanas'])} con huérfanas · "
          f"{len([f for f in fk if f['estado'] == 'sin_destino'])} sin destino")
    for linea in invariantes:
        print(f"  [INVARIANTE] {linea}")
    for linea in expectativas[:10]:
        print(f"  [expectativa] {linea}")
    print(f"Escrito en {DESTINO.relative_to(RAIZ)}")

    if args.check:
        conocidas = excepciones()
        nuevas = [x for x in invariantes if x.split(":")[0] not in conocidas]
        for objeto in conocidas:
            if any(x.startswith(objeto + ":") for x in invariantes):
                print(f"  [excepción declarada] {objeto}: {conocidas[objeto]}")
        if nuevas:
            print(f"CLAVES: {len(nuevas)} invariante(s) nueva(s)")
            return 1
    if args.check:
        print("CLAVES: ninguna invariante rota")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

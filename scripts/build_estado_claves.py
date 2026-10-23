#!/usr/bin/env python3
"""El estado de las claves de cada objeto, para que la web lo muestre.

`docs/api/claves.csv` es la fuente de verdad —lo mide `verificar_claves.py` sobre
todas las filas publicadas—, pero vive en la carpeta de la API y casi nadie lo
abre. Este paso lo traduce a un archivo que la web carga, con el texto ya
redactado y los números dentro:

    docs/js/estado_claves.js

Reglas que no se negocian:

  * **Nada se escribe a mano.** Si el estado se copiara a mano a la web, en dos
    releases estaría mintiendo otra vez. El archivo se regenera y `--check` falla
    cuando no coincide con `claves.csv`.
  * **El texto lleva el número, no el adjetivo.** «Publica 160.564 filas idénticas
    (10,1 %): no sumes sin agrupar», no «tiene duplicados».
  * **El impacto se mide, no se estima.** Para cada objeto con filas repetidas se
    compara, en su última partición, la suma de cada columna numérica sobre todas
    las filas con la suma sobre las filas distintas. La diferencia es lo que
    sobreestima un `SUM` sin agrupar. Ojo: `GROUP BY` + `SUM(col)` **no** sirve
    para esto —cada grupo suma sus duplicados y vuelve al total crudo—; hay que
    tomar un representante por grupo (`MAX`) o hacer `SELECT DISTINCT`.

Uso:
    python3 scripts/build_estado_claves.py            # escribe docs/js/estado_claves.js
    python3 scripts/build_estado_claves.py --check    # falla si quedó atrás
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
CLAVES = DOCS / "api" / "claves.csv"
CATALOGO = DOCS / "api" / "v2" / "catalog.json"
PARTICIONES = DOCS / "api" / "v2" / "partitions"
ESQUEMAS = DOCS / "api" / "esquemas.json"
DESTINO = DOCS / "js" / "estado_claves.js"

NUMERICO = {"BIGINT", "INTEGER", "SMALLINT", "TINYINT", "DOUBLE", "REAL", "DECIMAL",
            "HUGEINT", "UBIGINT", "UINTEGER", "FLOAT"}
# Para el ejemplo de sobreestimación se prefieren los importes: el porcentaje mayor
# puede caer en una columna que no es una cifra financiera (un plazo en días, un
# porcentaje de participación) y entonces el ejemplo no dice nada a quien suma.
MONETARIA = ("_clp", "_miles_mf", "_m_clp", "_um", "valor", "monto", "importe",
             "saldo", "costo", "patrimonio")


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def decimal(x: float, cifras: int = 1) -> str:
    """Número con coma decimal, como se escribe en Chile.

    Un porcentaje pequeño no se redondea a cero: «4 filas idénticas (0,0 %)» se
    leería como que no hay duplicados, y hay cuatro.
    """
    if 0 < abs(x) < 0.1:
        cifras = 3
    return f"{x:.{cifras}f}".replace(".", ",")


def leer_claves() -> dict[str, dict]:
    """{objeto: fila de tipo pk} desde claves.csv."""
    with CLAVES.open(encoding="utf-8", newline="") as fh:
        return {f["objeto"]: f for f in csv.DictReader(fh) if f["tipo"] == "pk"}


def particion_para_ejemplo(objeto: str) -> tuple[Path | None, str]:
    """Última partición del objeto y la etiqueta del periodo."""
    doc = PARTICIONES / f"{objeto}.json"
    if not doc.exists():
        return None, ""
    partes = json.loads(doc.read_text(encoding="utf-8")).get("particiones") or []
    if not partes:
        return None, ""
    ultima = sorted(partes, key=lambda p: p.get("archivo", ""))[-1]
    archivo = DOCS / ultima["archivo"]
    if not archivo.exists():
        return None, ""
    periodo = ultima.get("periodo") or ""
    etiqueta = periodo if periodo and periodo[:2] == "20" else "la serie completa"
    return archivo, etiqueta


def impacto(archivo: Path, columnas: list[str]) -> dict | None:
    """Cuánto sobreestima un SUM sin agrupar, medido sobre la partición.

    Devuelve la columna más afectada, con las dos sumas y el porcentaje.
    """
    import duckdb

    con = duckdb.connect()
    con.execute("SET threads TO 4")
    try:
        todas = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{archivo}'").fetchall()]
        medidas = [c for c in columnas if c in todas]
        if not medidas:
            return None
        grupo = ", ".join(f'"{c}"' for c in todas)
        crudo = ", ".join(f'SUM("{c}")' for c in medidas)
        rep = ", ".join(f'MAX("{c}") AS "{c}"' for c in medidas)
        fila_cruda = con.execute(f"SELECT {crudo} FROM '{archivo}'").fetchone()
        fila_rep = con.execute(
            f"SELECT {crudo} FROM (SELECT {rep} FROM '{archivo}' GROUP BY {grupo})"
        ).fetchone()
    finally:
        con.close()

    candidatas = []
    for columna, con_rep, sin_rep in zip(medidas, fila_cruda, fila_rep):
        if con_rep is None or not sin_rep:
            continue
        pct = (con_rep / sin_rep - 1) * 100
        if abs(pct) < 0.5:
            continue
        candidatas.append({"columna": columna, "con_repetidas": int(con_rep),
                           "sin_repetidas": int(sin_rep), "pct": round(pct, 2)})
    if not candidatas:
        return None
    importes = [c for c in candidatas if any(k in c["columna"] for k in MONETARIA)]
    return max(importes or candidatas, key=lambda c: abs(c["pct"]))


def construir() -> dict:
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    esquemas = json.loads(ESQUEMAS.read_text(encoding="utf-8"))["objetos"]
    claves = leer_claves()

    objetos: dict[str, dict] = {}
    for obj in catalogo["objetos"]:
        nombre = obj["id"]
        fila = claves.get(nombre)
        if not fila:
            # No se omite en silencio: un objeto publicado sin verificación es
            # justamente el hueco que dejó pasar el defecto de claves. Si el
            # catálogo dice que no tiene filas, se declara sin datos; si tiene
            # filas y no hay verificación, se declara sin verificar y el
            # --check falla, en vez de callar.
            if not int(obj.get("filas") or 0):
                objetos[nombre] = {
                    "estado": "sin_datos",
                    "filas": 0, "distintas": 0, "sobrantes": 0,
                    "pct_repetidas": 0.0, "columnas": [], "declarada": False,
                    "texto": "Sin filas publicadas: no hay clave que verificar.",
                }
            else:
                objetos[nombre] = {
                    "estado": "sin_verificar",
                    "filas": int(obj.get("filas") or 0), "distintas": 0,
                    "sobrantes": 0, "pct_repetidas": 0.0, "columnas": [],
                    "declarada": False,
                    "texto": ("Sin verificación de clave: claves.csv no incluye este "
                              f"objeto y publica {miles(int(obj.get('filas') or 0))} filas. "
                              "No sumes sin agrupar."),
                }
            continue
        estado = fila["estado"]
        filas = int(fila["filas"]) if fila["filas"] else 0
        distintas = int(fila["distintas"]) if fila["distintas"] else 0
        sobrantes = int(fila["sobrantes"]) if fila["sobrantes"] else 0
        pct = round(sobrantes / filas * 100, 4) if filas else 0.0
        columnas = [c.strip() for c in fila["columnas"].split("+")] if fila["columnas"] else []
        tipos = {c["nombre"]: c.get("tipo") for c in esquemas.get(nombre, {}).get("columnas", [])}

        entrada: dict = {
            "estado": estado,
            "filas": filas,
            "distintas": distintas,
            "sobrantes": sobrantes,
            "pct_repetidas": pct,
            "columnas": columnas,
            "declarada": fila["declarada"] == "si",
        }

        # ¿La clave identifica una entidad o sólo sirve para deduplicar?
        if estado in ("ok", "propuesta") and columnas:
            # Una clave de 15 columnas donde 14 son importes no identifica una
            # posición: deduplica. Se marca cuando los importes son la mayoría
            # (la columna de periodo, si está, no cambia la naturaleza).
            numericas = sum(1 for c in columnas if tipos.get(c) in NUMERICO)
            entrada["tipo_clave"] = "medidas" if numericas / len(columnas) >= 0.7 else "identifica"

        if estado == "sin_datos":
            entrada["texto"] = "Sin filas publicadas: no hay clave que verificar."
        elif estado == "sin_clave":
            entrada["texto"] = (
                f"Sin clave: publica {miles(sobrantes)} filas idénticas "
                f"({decimal(pct)} % de {miles(filas)}). No sumes sin agrupar."
            )
            archivo, etiqueta = particion_para_ejemplo(nombre)
            ejemplo = impacto(archivo, [c for c, t in tipos.items() if t in NUMERICO]) if archivo else None
            if ejemplo:
                entrada["ejemplo"] = {**ejemplo, "periodo": etiqueta}
                entrada["texto"] += (
                    f" En {etiqueta}, sumar `{ejemplo['columna']}` sin agrupar "
                    f"sobreestima {decimal(ejemplo['pct'])} %."
                )
        elif estado == "propuesta":
            entrada["texto"] = (
                f"Clave propuesta: {len(columnas)} columnas, única sobre {miles(filas)} filas. "
                "El diccionario no la declaraba."
            )
        else:
            entrada["texto"] = (
                f"Clave verificada: {' + '.join(columnas)} — única sobre {miles(filas)} filas."
            )
        if entrada.get("tipo_clave") == "medidas":
            entrada["texto"] += (
                " Compuesta sobre todo por importes: sirve para deduplicar, "
                "no identifica una posición."
            )
        objetos[nombre] = entrada

    resumen = {
        "objetos": len(objetos),
        "verificadas": sum(1 for o in objetos.values() if o["estado"] == "ok"),
        "propuestas": sum(1 for o in objetos.values() if o["estado"] == "propuesta"),
        "sin_clave": sum(1 for o in objetos.values() if o["estado"] == "sin_clave"),
        "sin_datos": sum(1 for o in objetos.values() if o["estado"] == "sin_datos"),
        "sin_verificar": sum(1 for o in objetos.values() if o["estado"] == "sin_verificar"),
        "con_repetidas": sum(1 for o in objetos.values() if o["sobrantes"] > 0),
        "filas_repetidas": sum(o["sobrantes"] for o in objetos.values()),
    }
    return {
        "generado": catalogo["generado"],
        "data_release": catalogo["data_release"],
        "como_se_genera": "python3 scripts/build_estado_claves.py",
        "resumen": resumen,
        "objetos": dict(sorted(objetos.items())),
    }


def texto_js(doc: dict) -> str:
    cuerpo = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=False)
    return (
        "// GENERADO por scripts/build_estado_claves.py — no editar a mano.\n"
        "// Fuente: docs/api/claves.csv, medido sobre todas las filas publicadas.\n"
        f"// data_release: {doc['data_release']}\n"
        f"window.ESTADO_CLAVES = {cuerpo};\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="falla si el archivo no coincide")
    args = ap.parse_args()

    doc = construir()
    texto = texto_js(doc)
    actual = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else ""

    if args.check:
        if doc["resumen"]["sin_verificar"]:
            print(f"ESTADO-CLAVES: {doc['resumen']['sin_verificar']} objetos publicados "
                  "sin verificación de clave en docs/api/claves.csv")
            return 1
        if texto != actual:
            print(f"ESTADO-CLAVES: {DESTINO.relative_to(RAIZ)} está desactualizado; "
                  "ejecuta scripts/build_estado_claves.py")
            return 1
        print(f"ESTADO-CLAVES: al día ({doc['resumen']['objetos']} objetos · "
              f"{doc['resumen']['sin_clave']} sin clave · "
              f"{doc['resumen']['filas_repetidas']} filas repetidas)")
        return 0

    DESTINO.write_text(texto, encoding="utf-8")
    r = doc["resumen"]
    print(f"Escrito {DESTINO.relative_to(RAIZ)}: {r['objetos']} objetos · "
          f"{r['verificadas']} claves verificadas · {r['propuestas']} propuestas · "
          f"{r['sin_clave']} sin clave · {r['sin_datos']} sin datos")
    if r["sin_verificar"]:
        print(f"AVISO: {r['sin_verificar']} objetos publicados sin verificación de clave")
    print(f"Filas repetidas en total: {miles(r['filas_repetidas'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Publica el esquema real de cada objeto del contrato (Fase 0b de la ruta de la API).

El diccionario editorial (`docs/js/data_dictionary.js`) cubre 82 de los 89
objetos y sus tipos están escritos a mano, así que no sirve como contrato: un
cliente que quiera escribir SQL necesita las columnas y los tipos **físicos**,
no los que alguien recordaba al documentar. Este script los saca del pie de
cada Parquet publicado, que es la única fuente que no puede desviarse de lo que
el usuario descarga.

Reglas:

  * Un objeto = una vista de `SEMANTIC_VIEWS`. Sus archivos se resuelven igual
    que en el cliente (`file` o `manifest`), así que si un archivo no se
    publica tampoco aparece aquí.
  * Todas las particiones de un objeto deben compartir el mismo esquema; si no,
    el script falla (significaría que la tabla cambia de forma según el corte).
  * El tipo publicado es el de DuckDB (`VARCHAR`, `BIGINT`, `DOUBLE`…), que es
    lo que devuelve `DESCRIBE` al registrar la vista.
  * El diccionario añade `rol`, `significado` y `criterio_contable` cuando
    existe la columna, pero **nunca** cambia el tipo.
  * Excepción declarada: una columna sin ningún valor en ninguna partición se
    publica con el tipo que promete el diccionario (o `VARCHAR` si no está
    documentada), marcada con `sin_valores: true` y `tipo_fisico: "null"`. Son
    columnas vacías de origen, no un error de tipos.

Genera `docs/api/esquemas.json`.

Uso:
    python3 scripts/build_esquemas.py            # escribe el JSON y valida
    python3 scripts/build_esquemas.py --check    # sólo valida (CI)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
sys.path.insert(0, str(RAIZ / "scripts"))

import audit_consultas_sugeridas as ac  # noqa: E402

DESTINO = DOCS / "api" / "esquemas.json"
DICCIONARIO = DOCS / "reproducibilidad" / "diccionario.csv"
RECONCILIACION = DOCS / "api" / "reconciliacion.csv"


def tipo_duckdb(t: pa.DataType) -> str:
    """Nombre de tipo tal como lo reporta `DESCRIBE` en DuckDB."""
    if pa.types.is_null(t):
        return "NULL"
    if pa.types.is_string(t) or pa.types.is_large_string(t):
        return "VARCHAR"
    if pa.types.is_list(t) and pa.types.is_string(t.value_type):
        return "VARCHAR[]"
    if pa.types.is_boolean(t):
        return "BOOLEAN"
    if pa.types.is_integer(t):
        return {8: "TINYINT", 16: "SMALLINT", 32: "INTEGER", 64: "BIGINT"}[t.bit_width]
    if pa.types.is_floating(t):
        return "DOUBLE" if t.bit_width == 64 else "REAL"
    if pa.types.is_date32(t):
        return "DATE"
    if pa.types.is_timestamp(t):
        return "TIMESTAMPTZ" if t.tz else "TIMESTAMP"
    if pa.types.is_decimal(t):
        return f"DECIMAL({t.precision}, {t.scale})"
    return str(t)


def cargar_diccionario() -> dict[str, dict[str, dict]]:
    """{vista: {columna: {tipo, rol, significado, criterio}}}"""
    dic: dict[str, dict[str, dict]] = {}
    if not DICCIONARIO.exists():
        return dic
    with DICCIONARIO.open(encoding="utf-8", newline="") as fh:
        for fila in csv.DictReader(fh):
            dic.setdefault(fila["vista"], {})[fila["columna"]] = {
                "tipo": fila["tipo"],
                "rol": fila["rol"],
                "significado": fila["significado"],
                "criterio_contable": fila["criterio_contable"],
            }
    return dic


def cargar_reconciliacion() -> dict[str, dict]:
    if not RECONCILIACION.exists():
        return {}
    with RECONCILIACION.open(encoding="utf-8", newline="") as fh:
        return {fila["objeto"]: fila for fila in csv.DictReader(fh)}


def cargar_manifiesto() -> dict[str, dict]:
    """{id: tabla} del manifiesto, para sector y corte."""
    datos = json.loads((RAIZ / "data_manifest.json").read_text(encoding="utf-8"))
    return {t["id"]: t for t in datos["tables"]}


def columnas_de(ficheros: list[Path]) -> tuple[list[dict], list[str]]:
    """Columnas del objeto y avisos; falla si las particiones no coinciden."""
    esquema = pq.read_schema(ficheros[0])
    for otro in ficheros[1:]:
        if not pq.read_schema(otro).equals(esquema):
            raise SystemExit(
                f"ERROR: {otro.name} declara un esquema distinto al de {ficheros[0].name}. "
                "Una tabla no puede cambiar de forma según la partición."
            )
    columnas = [{"nombre": f.name, "tipo": tipo_duckdb(f.type), "fisico": str(f.type)} for f in esquema]
    return columnas, []


def construir() -> dict:
    vistas = ac.vistas_semanticas()
    dic = cargar_diccionario()
    recon = cargar_reconciliacion()
    manifiesto = cargar_manifiesto()

    objetos: dict[str, dict] = {}
    sin_esquema: list[str] = []
    total_filas = 0
    total_columnas = 0
    sin_valores = 0
    sin_documentar = 0
    vistos: dict[Path, int] = {}
    desacuerdos: list[dict] = []

    for vista in vistas:
        nombre = vista["name"]
        ficheros = [Path(p) for p in ac.ficheros_de(vista)]
        info = recon.get(nombre, {})
        tabla = manifiesto.get(info.get("manifest_id") or "", {})
        entrada: dict = {
            "manifest_id": info.get("manifest_id") or None,
            "nombre_visible": info.get("nombre_visible") or tabla.get("name") or None,
            "sector": tabla.get("sector") or info.get("sector") or None,
            "corte": info.get("corte") or tabla.get("corte") or None,
            "estado": info.get("estado") or None,
            "nivel": info.get("nivel") or None,
            "puente": info.get("puente") or None,
        }
        if vista.get("where"):
            entrada["filtro"] = vista["where"]

        if not ficheros:
            entrada["particiones"] = 0
            entrada["filas"] = 0
            entrada["columnas"] = []
            entrada["motivo_sin_esquema"] = info.get("motivo") or "sin archivos publicados"
            sin_esquema.append(nombre)
            objetos[nombre] = entrada
            continue

        columnas, _ = columnas_de(ficheros)
        documentadas = dic.get(nombre, {})
        filas = 0
        for f in ficheros:
            if f not in vistos:
                vistos[f] = pq.ParquetFile(f).metadata.num_rows
            filas += vistos[f]
        total_filas += filas
        total_columnas += len(columnas)

        # `filas` es lo que devuelve la vista: si el objeto filtra un dataset
        # compartido (bancos B1/B2 contra R1), el total de los archivos no es
        # lo que ve el cliente.
        filas_vista = filas
        if vista.get("where"):
            con = duckdb.connect()
            rutas = json.dumps([str(f) for f in ficheros])
            filas_vista = con.execute(
                f"SELECT count(*) FROM read_parquet({rutas}) WHERE {vista['where']}"
            ).fetchone()[0]
            con.close()

        publicadas = []
        for col in columnas:
            significado = documentadas.get(col["nombre"])
            salida = {"nombre": col["nombre"]}
            if col["tipo"] == "NULL":
                # Columna vacía en todas las particiones: se publica el tipo
                # prometido por el diccionario (o VARCHAR) y se deja dicho.
                salida["tipo"] = (significado or {}).get("tipo") or "VARCHAR"
                salida["tipo_fisico"] = "null"
                salida["sin_valores"] = True
                sin_valores += 1
            else:
                salida["tipo"] = col["tipo"]
                if significado and significado["tipo"] != col["tipo"] and significado["tipo"] != "NULL":
                    desacuerdos.append(
                        {"objeto": nombre, "columna": col["nombre"], "diccionario": significado["tipo"], "fisico": col["tipo"]}
                    )
            if significado:
                for clave in ("rol", "significado", "criterio_contable"):
                    if significado.get(clave):
                        salida[clave] = significado[clave]
            else:
                salida["documentada"] = False
                sin_documentar += 1
            publicadas.append(salida)

        entrada["particiones"] = len(ficheros)
        entrada["filas"] = filas_vista
        if filas_vista != filas:
            entrada["filas_dataset"] = filas
        entrada["archivo"] = str(ficheros[0].relative_to(DOCS))
        entrada["columnas"] = publicadas
        objetos[nombre] = entrada

    cubiertas = {o["manifest_id"] for o in objetos.values() if o.get("manifest_id")}
    faltan = [t for t in manifiesto if t not in cubiertas]

    return {
        "contrato": "sif-api/esquemas",
        "version": "v1",
        "generado": date.today().isoformat(),
        "como_se_genera": "python3 scripts/build_esquemas.py",
        "tipo_de_dato": "Tipos de DuckDB; el diccionario editorial sólo añade significado.",
        "resumen": {
            "objetos": len(objetos),
            "con_esquema": len(objetos) - len(sin_esquema),
            "sin_esquema": len(sin_esquema),
            "tablas_manifiesto": len(manifiesto),
            "tablas_manifiesto_cubiertas": len(cubiertas),
            "columnas": total_columnas,
            "columnas_sin_documentar": sin_documentar,
            "columnas_sin_valores": sin_valores,
            "filas_por_objeto": total_filas,
            "filas_unicas": sum(vistos.values()),
        },
        "objetos": objetos,
        "_avisos": {
            "sin_esquema": sin_esquema,
            "tablas_manifiesto_sin_objeto": faltan,
            "diccionario_desactualizado": desacuerdos,
        },
    }


def comparable(doc: dict) -> str:
    """El JSON sin la fecha, que cambia todos los días por definición."""
    copia = dict(doc)
    copia.pop("generado", None)
    return json.dumps(copia, ensure_ascii=False, indent=1, sort_keys=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="sólo valida contra el JSON versionado (CI)")
    args = ap.parse_args()

    doc = construir()
    res = doc["resumen"]
    avisos = doc["_avisos"]
    problemas = []

    if avisos["tablas_manifiesto_sin_objeto"]:
        problemas.append(
            f"{len(avisos['tablas_manifiesto_sin_objeto'])} tablas del manifiesto no tienen objeto: "
            + ", ".join(avisos["tablas_manifiesto_sin_objeto"][:5])
        )
    if avisos["diccionario_desactualizado"]:
        problemas.append(
            f"{len(avisos['diccionario_desactualizado'])} columnas con tipo distinto en el diccionario "
            "(el Parquet manda)"
        )

    print(f"Objetos: {res['objetos']} · con esquema: {res['con_esquema']} · sin datos: {res['sin_esquema']}")
    print(f"Columnas: {res['columnas']} · sin documentar: {res['columnas_sin_documentar']} · sin valores: {res['columnas_sin_valores']}")
    print(f"Filas: {res['filas_unicas']:,} únicas ({res['filas_por_objeto']:,} contando alias)".replace(",", "."))
    print(f"Tablas del manifiesto cubiertas: {res['tablas_manifiesto_cubiertas']}/{res['tablas_manifiesto']}")
    for p in problemas:
        print(f"  [aviso] {p}")

    if args.check:
        if not DESTINO.exists():
            print(f"ERROR: falta {DESTINO.relative_to(RAIZ)}; ejecuta scripts/build_esquemas.py")
            return 1
        actual = json.loads(DESTINO.read_text(encoding="utf-8"))
        if comparable(actual) != comparable(doc):
            print("ERROR: docs/api/esquemas.json está desactualizado; ejecuta scripts/build_esquemas.py")
            a, b = actual["objetos"], doc["objetos"]
            for nombre in sorted(set(a) | set(b)):
                if nombre not in a or nombre not in b:
                    print(f"  · objeto {'nuevo' if nombre not in a else 'retirado'}: {nombre}")
                    continue
                ca = {c["nombre"]: c["tipo"] for c in a[nombre].get("columnas", [])}
                cb = {c["nombre"]: c["tipo"] for c in b[nombre].get("columnas", [])}
                if ca != cb:
                    dif = {k: (ca.get(k), cb.get(k)) for k in set(ca) | set(cb) if ca.get(k) != cb.get(k)}
                    print(f"  · {nombre}: {list(dif.items())[:4]}")
            return 1
        if problemas:
            print("ERROR: el contrato de esquemas no cumple lo que promete")
            return 1
        print("ESQUEMAS: contrato al día")
        return 0

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Esquemas escritos en {DESTINO.relative_to(RAIZ)}")
    return 0 if not problemas else 1


if __name__ == "__main__":
    raise SystemExit(main())

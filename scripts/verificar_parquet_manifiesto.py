#!/usr/bin/env python3
"""Verifica que los Parquet publicados coincidan con su manifiesto (punto 5 de la auditoría).

Para cada tabla de data_manifest.json:
  * suma las filas de todos sus archivos Parquet (leyendo sólo los metadatos) y la compara con
    `registros_reales` del manifiesto;
  * comprueba que todas las partes de la tabla tengan el mismo esquema (mismos nombres y tipos de
    columna en el mismo orden), porque la descarga las une en un único CSV/Excel;
  * comprueba que cada archivo referenciado exista.

Uso:  python3 scripts/verificar_parquet_manifiesto.py [--json salida.json]
Requiere pyarrow (versión fijada en .github/workflows/web_audit.yml).

Las tablas en que el manifiesto cuenta registros de forma distinta a las filas del Parquet
(p. ej. particiones que se cuentan una sola vez) aparecen como DIFERENCIA y se revisan a mano.
"""
import argparse
import json
import os
import sys

import pyarrow.parquet as pq

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(RAIZ, "docs")


def archivos_de(tabla):
    """Rutas relativas a docs/ de los Parquet de una tabla.

    Si file_parquet apunta a un archivo suelto, pero una carpeta superior tiene un manifest.json
    que lista el conjunto completo (p. ej. bancos: un mes de ejemplo y 56 particiones), se usa
    ese conjunto, que es el que suma `registros_reales`.
    """
    ruta = tabla["file_parquet"]
    if ruta.endswith("manifest.json"):
        manifiesto = json.load(open(os.path.join(DOCS, ruta), encoding="utf-8"))
        return [f for f in manifiesto.get("files", []) if f.endswith(".parquet")]
    carpeta = os.path.dirname(ruta)
    for _ in range(3):
        candidato = os.path.join(DOCS, carpeta, "manifest.json")
        if carpeta and os.path.exists(candidato):
            manifiesto = json.load(open(candidato, encoding="utf-8"))
            archivos = [f for f in manifiesto.get("files", []) if f.endswith(".parquet")]
            if ruta in archivos:
                return archivos
        carpeta = os.path.dirname(carpeta)
    return [ruta]


def revisar(tabla):
    res = {"id": tabla["id"], "registros_manifiesto": tabla.get("registros_reales"),
           "filas_parquet": 0, "archivos": 0, "faltantes": [], "esquemas_distintos": [], "filas_esquema_distinto": 0,
           "columnas": None, "diferencia": None, "ok": True}
    esquema_ref = None
    for rel in archivos_de(tabla):
        ruta = os.path.join(DOCS, rel)
        if not os.path.exists(ruta):
            res["faltantes"].append(rel)
            continue
        meta = pq.ParquetFile(ruta)
        res["archivos"] += 1
        res["filas_parquet"] += meta.metadata.num_rows
        esquema = [(f.name, str(f.type)) for f in meta.schema_arrow]
        if esquema_ref is None:
            esquema_ref = esquema
            res["columnas"] = len(esquema)
        elif esquema != esquema_ref and rel not in res["esquemas_distintos"]:
            res["esquemas_distintos"].append(rel)
            res["filas_esquema_distinto"] += meta.metadata.num_rows
        elif esquema != esquema_ref:
            res["filas_esquema_distinto"] += meta.metadata.num_rows
    if res["faltantes"] or res["esquemas_distintos"]:
        res["ok"] = False
    if res["registros_manifiesto"] is not None and res["filas_parquet"] != res["registros_manifiesto"]:
        res["diferencia"] = res["filas_parquet"] - res["registros_manifiesto"]
        res["ok"] = False
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="guarda el informe completo en este archivo")
    args = ap.parse_args()
    manifiesto = json.load(open(os.path.join(RAIZ, "data_manifest.json"), encoding="utf-8"))
    resultados = [revisar(t) for t in manifiesto["tables"]]

    print(f"{'tabla':42} {'manifiesto':>12} {'parquet':>12} {'archivos':>8} {'cols':>5}  estado")
    for r in resultados:
        estado = "OK" if r["ok"] else "REVISAR"
        print(f"{r['id']:42} {r['registros_manifiesto'] or 0:>12,} {r['filas_parquet']:>12,} "
              f"{r['archivos']:>8} {str(r['columnas'] or '-'):>5}  {estado}")
        if r["faltantes"]:
            print(f"    faltan: {r['faltantes'][:3]}")
        if r["esquemas_distintos"]:
            print(f"    esquema distinto: {r['esquemas_distintos'][:3]} · {r['filas_esquema_distinto']:,} filas "
                  "que una descarga completa (SELECT *) puede omitir")
        if r["diferencia"] is not None:
            print(f"    diferencia de filas: {r['diferencia']:+,}")

    ok = sum(1 for r in resultados if r["ok"])
    total_m = sum(r["registros_manifiesto"] or 0 for r in resultados)
    total_p = sum(r["filas_parquet"] for r in resultados)
    print(f"\nTablas OK: {ok}/{len(resultados)} · filas manifiesto {total_m:,} · filas Parquet {total_p:,}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(resultados, fh, ensure_ascii=False, indent=2)
    return 0 if ok == len(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Auditoría física de los Parquet publicados: qué descarga realmente el navegador.

Las consultas corren en DuckDB-Wasm sobre Parquet servidos por HTTP con range
requests. Lo que el navegador descarga por consulta depende del tamaño de los
pies de los Parquet (metadatos de row groups) y del row group que contenga la
fila pedida — no del tamaño total del archivo. Esta auditoría mide, por cada
vista semántica:

  * tamaño publicado (bytes en el repo) y nº de ficheros,
  * compresión (codec) por vista,
  * tamaño de los pies (footers): es lo que se descarga para decidir qué
    row group leer, en TODOS los ficheros de la vista,
  * el coste estimado de la consulta típica
    `WHERE periodo = (SELECT max(periodo) FROM vista)`:
      - sin poda: bajar los ficheros enteros,
      - con poda por stats: pie de cada fichero + el row group del último
        periodo (si cada row group lleva min/max de `periodo`),
  * tamaño máximo de row group (filas y bytes): si un row group es tan
    grande como el fichero, la poda no ayuda a nada.

Uso:
    python3 scripts/medir_parquet_fisico.py           # informe completo
    python3 scripts/medir_parquet_fisico.py --json    # informe como JSON

No modifica nada. Requiere `pyarrow` (lee solo metadatos; no los datos).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
CLIENTE = DOCS / "js" / "duckdb_client.js"

try:
    import pyarrow.parquet as pq
except ImportError:
    print("pyarrow no instalado: auditoría omitida (pip install pyarrow)")
    sys.exit(0)


def vistas_semanticas() -> list[dict]:
    txt = CLIENTE.read_text(encoding="utf-8")
    bloque = txt[txt.index("const SEMANTIC_VIEWS"):txt.index("class DuckDBClient")]
    vistas = []
    for m in re.finditer(r"\{([^{}]*)\}", bloque):
        cuerpo = m.group(1)
        nombre = re.search(r'name:\s*"([^"]+)"', cuerpo)
        if not nombre:
            continue
        v: dict = {"name": nombre.group(1)}
        for clave in ("file", "manifest", "where"):
            hit = re.search(rf'{clave}:\s*"([^"]+)"', cuerpo)
            if hit:
                v[clave] = hit.group(1)
        vistas.append(v)
    return vistas


def ficheros_de(vista: dict) -> list[Path]:
    if "file" in vista:
        ruta = DOCS / vista["file"]
        return [ruta] if ruta.exists() else []
    if "manifest" in vista:
        man = DOCS / vista["manifest"]
        if not man.exists():
            return []
        datos = json.loads(man.read_text(encoding="utf-8"))
        return [DOCS / f for f in datos.get("files", [])]
    return []


def medir_fichero(ruta: Path) -> dict:
    pf = pq.ParquetFile(ruta)
    md = pf.metadata
    pie = md.serialized_size
    rgs = []
    for i in range(md.num_row_groups):
        rg = md.row_group(i)
        cols = [rg.column(j) for j in range(rg.num_columns)]
        _, periodo_bytes, stats = _col_periodo(rg)
        rgs.append({
            "filas": rg.num_rows,
            "bytes": sum(c.total_uncompressed_size for c in cols),
            "bytes_comprimido": sum(c.total_compressed_size for c in cols),
            "codec": {c.compression for c in cols},
            "periodo_bytes": periodo_bytes,
            "stats_periodo": stats,
        })
    return {
        "ruta": str(ruta.relative_to(DOCS)),
        "bytes": ruta.stat().st_size,
        "filas": md.num_rows,
        "columnas": md.num_columns,
        "row_groups": len(rgs),
        "pie": pie,
        "rowgroups": rgs,
        "periodo_en_ruta": (re.search(r"(\d{4}-\d{2})", ruta.name) or [None, None])[1]
        if re.search(r"(\d{4}-\d{2})", ruta.name) else None,
    }


def _col_periodo(rg) -> tuple[str | None, int | None, dict | None]:
    """(compresión, bytes comprimidos, stats) de la columna `periodo` del row group."""
    for j in range(rg.num_columns):
        c = rg.column(j)
        if c.path_in_schema == "periodo":
            stats = None
            if c.is_stats_set:
                st = c.statistics
                if st is not None and st.max is not None:
                    stats = {"min": st.min, "max": st.max}
            return c.compression, c.total_compressed_size, stats
    return None, None, None


def _stats_periodo(rg) -> dict | None:
    _, _, stats = _col_periodo(rg)
    return stats


def medir_vista(vista: dict) -> dict:
    rutas = ficheros_de(vista)
    if not rutas:
        return {"vista": vista["name"], "sin_ficheros": True}
    mfs = [medir_fichero(r) for r in rutas]
    total_bytes = sum(m["bytes"] for m in mfs)
    total_filas = sum(m["filas"] for m in mfs)
    pies = sum(m["pie"] for m in mfs)
    codecs = {c for m in mfs for rg in m["rowgroups"] for c in rg["codec"]}
    max_rg_filas = max((rg["filas"] for m in mfs for rg in m["rowgroups"]), default=0)
    max_rg_bytes = max((rg["bytes_comprimido"] for m in mfs for rg in m["rowgroups"]), default=0)

    # Costes de `WHERE periodo = (SELECT max(periodo) ...)` en tres supuestos:
    #  1. "stats": DuckDB calcula el max con los min/max de cada row group y
    #     baja solo el pie de cada fichero + el row group del último periodo.
    #  2. "escaneo": el motor no usa stats en la subconsulta y lee la columna
    #     `periodo` de todos los row groups (pie + columna de todos + RG final).
    #  3. "todo": descarga los ficheros enteros (sin ninguna poda).
    ultimo: dict | None = None
    for m in mfs:
        for rg in m["rowgroups"]:
            st = rg["stats_periodo"]
            if st and (ultimo is None or st["max"] > (ultimo["stats_periodo"]["max"])):
                ultimo = rg
    total_rgs = sum(m["row_groups"] for m in mfs)
    rgs_con_stats = sum(1 for m in mfs for rg in m["rowgroups"] if rg["stats_periodo"])
    con_stats = ultimo is not None and rgs_con_stats == total_rgs and total_rgs > 0
    coste_stats = (pies + ultimo["bytes_comprimido"]) if con_stats else None
    periodo_todos = sum(rg["periodo_bytes"] or 0 for m in mfs for rg in m["rowgroups"])
    coste_escaneo = (pies + periodo_todos + (ultimo["bytes_comprimido"] if ultimo else 0)) if total_rgs else None
    coste_todo = total_bytes
    return {
        "vista": vista["name"],
        "ficheros": len(mfs),
        "filas": total_filas,
        "bytes_publicados": total_bytes,
        "pie_total": pies,
        "codecs": sorted(codecs),
        "row_groups_total": total_rgs,
        "row_groups_con_stats": rgs_con_stats,
        "row_group_max_filas": max_rg_filas,
        "row_group_max_bytes": max_rg_bytes,
        "periodo_con_stats": con_stats,
        "ultimo_periodo_bytes": ultimo["bytes_comprimido"] if ultimo else None,
        "periodo_todos_rgs_bytes": periodo_todos,
        "coste_stats_bytes": coste_stats,
        "coste_escaneo_bytes": coste_escaneo,
        "coste_todo_bytes": coste_todo,
        "ahorro_pct": round((1 - coste_stats / total_bytes) * 100) if (coste_stats and total_bytes) else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    vistas = vistas_semanticas()
    resultados = []
    cache: dict[str, dict] = {}
    for v in vistas:
        key = v.get("manifest") or v.get("file") or v["name"]
        if key in cache:
            # Dos vistas comparten el mismo manifiesto (bancos_balance y
            # bancos_resultados): se mide una vez y se reporta por vista.
            r = cache[key]
            resultados.append({**r, "vista": v["name"], "comparte_manifiesto": True})
            continue
        r = medir_vista(v)
        cache[key] = r
        resultados.append(r)

    tot_bytes = sum(r.get("bytes_publicados", 0) for r in resultados)
    tot_pies = sum(r.get("pie_total", 0) for r in resultados)
    tot_filas = sum(r.get("filas", 0) for r in resultados)

    if args.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=1))
        return 0

    print(f"Vistas: {len(resultados)} · filas: {tot_filas:,} · publicados: {tot_bytes/1e6:,.1f} MB")
    print(f"Pies (metadatos) de todos los Parquet: {tot_pies/1e6:.2f} MB "
          f"({tot_pies/max(tot_bytes,1)*100:.1f} % del total publicado)\n")

    print("Coste de la consulta típica `WHERE periodo = (SELECT max(periodo) …)` por vista:")
    print("  stats   = pie de cada fichero + row group del último periodo (el mejor caso realista)")
    print("  escaneo = pie + columna `periodo` de todos los row groups (si la subconsulta no usa stats)")
    print("  todo    = los ficheros enteros (sin ninguna poda)")
    encabezado = (f"{'vista':38s} {'fich':>4s} {'filas':>10s} {'pub MB':>8s} {'pie KB':>8s} {'codec':>7s} "
                  f"{'stats MB':>9s} {'escaneo MB':>11s} {'todo MB':>8s} {'ahorro':>7s}")
    print(encabezado)
    print("-" * len(encabezado))
    for r in sorted(resultados, key=lambda x: -x.get("bytes_publicados", 0)):
        if r.get("sin_ficheros"):
            print(f"{r['vista']:38s} SIN FICHEROS")
            continue
        cod = ",".join(sorted(c[:4] for c in r["codecs"])) or "-"
        s = r.get("coste_stats_bytes"); e = r.get("coste_escaneo_bytes"); t = r.get("coste_todo_bytes")
        print(f"{r['vista']:38s} {r['ficheros']:4d} {r['filas']:10,d} {r['bytes_publicados']/1e6:8.2f} "
              f"{r['pie_total']/1024:8.1f} {cod:>7s} {(s/1e6 if s else 0):9.2f} {(e/1e6 if e else 0):11.2f} "
              f"{(t/1e6 if t else 0):8.2f} {(str(r['ahorro_pct'])+'%' if r['ahorro_pct'] is not None else '-'):>7s}")

    # Vistas grandes cuyo row group más grande no permite poda útil.
    print()
    sin_poda = [r for r in resultados if r.get("row_group_max_bytes") and r.get("bytes_publicados", 0) >= 1e6
                and r["row_group_max_bytes"] > 0.5 * r["bytes_publicados"]]
    if sin_poda:
        print("Vistas ≥1 MB con row group tan grande como medio fichero o más (la poda baja poco):")
        for r in sin_poda:
            print(f"  · {r['vista']}: RG máx {r['row_group_max_bytes']/1e6:.2f} MB de {r['bytes_publicados']/1e6:.2f} MB")
    else:
        print("Toda vista ≥1 MB tiene row groups suficientemente pequeños para podar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

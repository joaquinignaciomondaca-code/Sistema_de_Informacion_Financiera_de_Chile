#!/usr/bin/env python3
"""Carga el Parquet publicado en BigQuery para conectar Looker Studio sin servidores.

Looker Studio habla con BigQuery de forma nativa: grafica, filtra y agrega del
lado del motor, sin descargar filas al navegador. Ese es el camino cuando el
dashboard necesita el detalle de los ~19 millones de filas y no un *mart*
agregado. Este script hace la parte aburrida:

  1. junta las particiones de cada objeto en un Parquet por tabla (`build/bigquery/`);
  2. crea el dataset si falta;
  3. carga cada tabla con `bq load --replace` (idempotente: se puede repetir).

No inventa esquema: BigQuery lo lee del Parquet, que es el mismo archivo que
publica el sitio y el mismo que audita el contrato de la API.

Requisitos:
    * gcloud autenticado con permiso de BigQuery (`gcloud auth login`),
    * `bq` en el PATH,
    * duckdb y pyarrow instalados (los mismos del resto del repositorio).

Uso:
    python3 scripts/cargar_bigquery.py --proyecto mi-proyecto --dry-run
    python3 scripts/cargar_bigquery.py --proyecto mi-proyecto --dataset sif_chile
    python3 scripts/cargar_bigquery.py --proyecto mi-proyecto --objetos seguros_renta_fija,ffmm_cartera_nacional
    python3 scripts/cargar_bigquery.py --proyecto mi-proyecto --verificar

Costo aproximado: el catálogo completo pesa ~500 MB; el almacenamiento activo
ronda el centavo de dólar al mes y las consultas de un dashboard caben de sobra
en el terabyte gratuito mensual. La cuenta de facturación es la tuya: el
proyecto no cobra ni pide credenciales.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
sys.path.insert(0, str(RAIZ / "scripts"))

from version_contrato import API_VERSION  # noqa: E402

V2 = DOCS / "api" / API_VERSION
TRABAJO = RAIZ / "build" / "bigquery"


def _catalogo() -> dict:
    return json.loads((V2 / "catalog.json").read_text(encoding="utf-8"))


def _objetos(catalogo: dict, pedidos: list[str] | None) -> list[dict]:
    disponibles = [
        o for o in catalogo["objetos"]
        if o.get("particiones", 0) > 0 and o.get("estado") in ("publicado", "derivado")
    ]
    if not pedidos:
        return disponibles
    por_id = {o["id"]: o for o in catalogo["objetos"]}
    faltan = [p for p in pedidos if p not in por_id]
    if faltan:
        raise SystemExit(f"[FALLA] objetos desconocidos: {', '.join(faltan)}")
    sin_datos = [p for p in pedidos if por_id[p] not in disponibles]
    if sin_datos:
        raise SystemExit(
            f"[FALLA] sin Parquet publicado: {', '.join(sin_datos)} (mira docs/api/v2/catalog.json)"
        )
    return [por_id[p] for p in pedidos]


def _particiones(objeto: dict) -> tuple[list[Path], int, int]:
    ficha = json.loads((V2 / "partitions" / f"{objeto['id']}.json").read_text(encoding="utf-8"))
    archivos = [DOCS / p["archivo"] for p in ficha["particiones"]]
    faltan = [a for a in archivos if not a.exists()]
    if faltan:
        raise SystemExit(f"[FALLA] falta el archivo {faltan[0]} (¿clone parcial?)")
    filas = ficha.get("total", {}).get("filas", objeto.get("filas"))
    bytes_ = ficha.get("total", {}).get("bytes", objeto.get("bytes"))
    return archivos, int(filas or 0), int(bytes_ or 0)


def _consolidar(con, objeto: dict, archivos: list[Path], filtro: str | None) -> Path:
    destino = TRABAJO / f"{objeto['id']}.parquet"
    destino.parent.mkdir(parents=True, exist_ok=True)
    where = f" WHERE {filtro}" if filtro else ""
    con.execute(
        f"COPY (SELECT * FROM read_parquet(?){where}) TO '{destino}' (FORMAT PARQUET)",
        [[str(a) for a in archivos]],  # la lista va como un solo parámetro LIST
    )
    return destino


def _correr(cmd: list[str], dry_run: bool) -> str:
    if dry_run:
        print("  $ " + " ".join(cmd))
        return ""
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise SystemExit(f"[FALLA] {' '.join(cmd)}\n{resultado.stderr.strip()}")
    return resultado.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proyecto", required=True, help="ID del proyecto de Google Cloud con facturación")
    ap.add_argument("--dataset", default="sif_chile", help="dataset de destino (por defecto sif_chile)")
    ap.add_argument("--ubicacion", default="US", help="ubicación del dataset (por defecto US)")
    ap.add_argument("--objetos", help="ids separados por coma; por defecto, todos los publicados")
    ap.add_argument("--limite", type=int, help="carga sólo los primeros N objetos (para probar)")
    ap.add_argument("--dry-run", action="store_true", help="muestra los comandos sin ejecutarlos")
    ap.add_argument("--verificar", action="store_true", help="cuenta filas en BigQuery tras cargar")
    args = ap.parse_args()

    if not args.dry_run and not shutil.which("bq"):
        print("[FALLA] no encuentro `bq` en el PATH. Instala Google Cloud CLI y autentica con "
              "`gcloud auth login`.", file=sys.stderr)
        return 1

    catalogo = _catalogo()
    pedidos = [p.strip() for p in args.objetos.split(",")] if args.objetos else None
    objetos = _objetos(catalogo, pedidos)
    if args.limite:
        objetos = objetos[: args.limite]

    print(f"BigQuery: {len(objetos)} objeto(s) → {args.proyecto}:{args.dataset} "
          f"({catalogo['data_release']})")

    if not args.dry_run:
        _correr(["bq", "--project_id", args.proyecto, "--location", args.ubicacion,
                 "mk", "--force", f"{args.proyecto}:{args.dataset}"], False)

    import duckdb

    con = duckdb.connect()
    con.execute("SET TimeZone='UTC'")

    total_filas = total_bytes = 0
    for objeto in objetos:
        archivos, filas_esperadas, bytes_ = _particiones(objeto)
        ficha = json.loads((V2 / "partitions" / f"{objeto['id']}.json").read_text(encoding="utf-8"))
        filtro = ficha.get("filtro")
        print(f"· {objeto['id']}: {len(archivos)} archivo(s), {filas_esperadas} filas, "
              f"{bytes_ / 1e6:.1f} MB" + (f", filtro `{filtro}`" if filtro else ""))
        total_filas += filas_esperadas
        total_bytes += bytes_

        if args.dry_run:
            print(f"  $ bq load --source_format=PARQUET --replace "
                  f"{args.dataset}.{objeto['id']} build/bigquery/{objeto['id']}.parquet")
            continue

        parquet = _consolidar(con, objeto, archivos, filtro)
        _correr([
            "bq", "--project_id", args.proyecto, "--location", args.ubicacion,
            "load", "--source_format", "PARQUET", "--replace",
            f"{args.dataset}.{objeto['id']}",
            str(parquet),
        ], False)

        if args.verificar:
            salida = _correr([
                "bq", "--project_id", args.proyecto, "--format=json",
                "query", "--use_legacy_sql=false",
                f"SELECT COUNT(*) AS n FROM `{args.proyecto}.{args.dataset}.{objeto['id']}`",
            ], False)
            cargadas = json.loads(salida)[0]["n"] if salida else "?"
            estado = "ok" if str(cargadas) == str(filas_esperadas) else "REVISAR"
            print(f"  verificación: {cargadas} filas en BigQuery vs {filas_esperadas} esperadas ({estado})")

    print(f"Total: {total_filas} filas · {total_bytes / 1e6:.0f} MB"
          + (" · dry-run, nada se ejecutó" if args.dry_run else " · cargado"))
    if not args.dry_run:
        print("Siguiente paso: Looker Studio → Crear → Fuente de datos → BigQuery → "
              f"{args.proyecto}:{args.dataset}.")
        print("Guía: docs/looker/README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

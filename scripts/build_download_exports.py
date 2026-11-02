#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera descargas pre-construidas (CSV y JSON) para los conjuntos publicados.

Por qué existe
-------------
La pestaña Descargas publica los datos como Parquet. Power BI y Data Studio
(Looker Studio) no conversan con ese formato directamente: Data Studio sólo
lee CSV (por upload o GCS) y Power BI, aunque ya soporta Parquet, se consume
más naturalmente con CSV o JSON. Antes, el CSV y el Excel se generaban en el
navegador del visitante con DuckDB-Wasm: para series largas (p. ej. los
derivados de ffmm, 282.045 filas) esa generación bloqueaba la página mientras
construía un string gigante, y la descarga tardaba.

Este script produce los mismos CSV/JSON **en el servidor, una vez por
publicación**, junto a los Parquet que ya existen. El visitante descarga un
archivo estático: sin bloqueo, sin depender del motor del navegador y listo
para Power BI o Data Studio. El catálogo de descargas (`download_catalog.js`)
enlaza directo al archivo pre-generado; los conjuntos que superan el tope
siguen exportándose en el navegador, ahora sin bloquear (ver
docs/js/download_utils.js).

Tipos y topes
-------------
  CSV   <- 35 MB por conjunto (GitHub Pages admite 100 MB por archivo; este
           tope deja margen y mantiene el peso publicado en presupuesto).
           Escrito por DuckDB con comas y sin BOM: el formato que Power BI y
           Data Studio esperan.
  JSON  <- 5 MB por conjunto (JSON Lines; lo lee el conector JSON de Power BI).
  Parquet > 60 MB en total: no se intenta. Su CSV superaría el tope de
           todos modos (en la práctica, 8-25x el peso del Parquet) y evitar
           leerlos ahorra minutos de CI por publicación.
  Vistas con filtro SQL (`where`, hoy sólo banca B1/B2/R1): se omiten. El
           CSV de la serie filtrada supera el tope; esa descarga sigue
           disponible en el navegador con el filtro aplicado.

Incremental
-----------
Cada conjunto guarda una firma (lista de Parquet con su peso + filtro). Si no
cambió y los archivos ya publicados coinciden con el registro, no se
regenera. Si un conjunto crece hasta superar el tope, su CSV anterior se
elimina y queda registrado como `null`.

Uso:
    python3 scripts/build_download_exports.py              # genera/actualiza
    python3 scripts/build_download_exports.py --check      # falla si está desactualizado
    python3 scripts/build_download_exports.py --lista      # imprime los archivos generados (para git add)
    python3 scripts/build_download_exports.py --force      # regenera todo
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    import duckdb
except Exception:  # pragma: no cover - sin duckdb no hay generación
    duckdb = None

try:  # el conteo de filas sale del pie del Parquet: barato y exacto.
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover
    pq = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_download_catalog import parse_views  # noqa: E402

DOCS = ROOT / "docs"
INDICE = DOCS / "outputs" / "_exportes.json"

CSV_MAX_MB = 35
JSON_MAX_MB = 5
PARQUET_MAX_MB = 60


def texto(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def json_leer(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def json_escribir(path: Path, datos: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")


def peso(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def filas_parquet(rutas: list[str]) -> int | None:
    """Filas totales leyendo sólo el pie de cada Parquet (sin pyarrow, None)."""
    if pq is None or not rutas:
        return None
    total = 0
    for ruta in rutas:
        full = DOCS / ruta
        if not full.exists():
            return None
        try:
            total += int(pq.ParquetFile(full).metadata.num_rows)
        except Exception:
            return None
    return total


def archivos_de_vista(vista: dict) -> tuple[list[str], str | None]:
    """(rutas relativas a docs/, manifiesto) de una vista semántica."""
    if vista["kind"] == "file":
        return [vista["path"]], None
    manifest_path = DOCS / vista["path"]
    if not manifest_path.exists():
        return [], None
    manifest = json_leer(manifest_path)
    return [f for f in manifest.get("files", []) if (DOCS / f).exists()], manifest


def sql_lectura(rutas: list[str], where: str) -> str:
    # DuckDB resuelve los caminos relativos contra el CWD, no contra docs/:
    # se pasan absolutos para que la generación no dependa de dónde corre el
    # script (Actions lo lanza desde la raíz del repositorio).
    lista = ", ".join("'" + str((DOCS / r).resolve()).replace("'", "''") + "'" for r in rutas)
    return f"SELECT * FROM read_parquet([{lista}])" + (f" WHERE {where}" if where else "")


def ruta_destino(vista: dict, manifest: dict | None, rutas: list[str]) -> tuple[Path, str]:
    """(directorio, nombre base) donde se escribe el CSV/JSON combinado."""
    if rutas:
        directorio = (DOCS / rutas[0]).parent
    else:
        directorio = DOCS / "outputs"
    if manifest:
        nombre = manifest.get("tabla") or Path(vista["path"]).parent.name
    else:
        nombre = Path(rutas[0]).stem if rutas else vista["name"]
    return directorio, nombre


def firma(rutas: list[str], where: str) -> dict:
    """Identifica la data fuente: rutas con peso, filtro y conteo."""
    return {
        "archivos": [{"ruta": r, "bytes": peso(DOCS / r)} for r in rutas],
        "where": where,
        "filas": filas_parquet(rutas),
    }


def generar_csv(rutas: list[str], where: str, destino: Path) -> bool:
    """Escribe el CSV en destino (borrando el anterior). True si se escribió."""
    if duckdb is None:
        return False
    sql = sql_lectura(rutas, where)
    tmp = tempfile.NamedTemporaryFile(delete=False, dir=str(destino.parent), suffix=".tmp.csv")
    tmp.close()
    try:
        duckdb.connect().execute(f"COPY ({sql}) TO '{tmp.name}' (HEADER, DELIMITER ',')")
        os.replace(tmp.name, destino)
        return True
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        return False


def generar_json(rutas: list[str], where: str, destino: Path) -> None:
    """Escribe JSON Lines (lo lee Power BI) en destino, borrando el anterior."""
    if duckdb is None:
        return
    sql = sql_lectura(rutas, where)
    tmp = tempfile.NamedTemporaryFile(delete=False, dir=str(destino.parent), suffix=".tmp.json")
    tmp.close()
    try:
        duckdb.connect().execute(f"COPY ({sql}) TO '{tmp.name}' (FORMAT JSON)")
        os.replace(tmp.name, destino)
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def hay_cambio(anterior: dict, actual: dict) -> bool:
    """La firma actual difiere de la guardada (o falta)."""
    if anterior is None:
        return True
    return json.dumps(anterior, sort_keys=True) != json.dumps(actual, sort_keys=True)


def generar_conjunto(vista: dict, indice: dict, forzado: bool, escribir: bool = True) -> dict:
    """Genera (o actualiza) las exportaciones de un conjunto. Devuelve su entrada."""
    nombre = vista["name"]
    where = vista.get("where") or ""
    rutas, manifest = archivos_de_vista(vista)
    entrada = dict(indice.get("conjuntos", {}).get(nombre, {}))
    entrada["archivos"] = firma(rutas, where)["archivos"] if rutas else []
    entrada["where"] = where
    entrada["csv"] = None
    entrada["json"] = None
    entrada["nota"] = None

    if not rutas:
        entrada["nota"] = "sin archivos publicados"
        return entrada

    peso_total = sum(a["bytes"] for a in entrada["archivos"])
    filas = filas_parquet(rutas)
    entrada["filas"] = filas

    if filas == 0:
        entrada["nota"] = "sin filas publicados"
        return entrada

    if where:
        entrada["nota"] = "vista con filtro SQL: el CSV supera el tope; se exporta en el navegador con el filtro"
        return entrada

    if peso_total > PARQUET_MAX_MB * 1024 * 1024:
        entrada["nota"] = "Parquet por encima del tope de generación"
        return entrada

    directorio, base = ruta_destino(vista, manifest, rutas)
    csv_path = directorio / f"{base}.completo.csv"
    json_path = directorio / f"{base}.completo.json"

    firma_actual = firma(rutas, where)
    anterior = indice.get("conjuntos", {}).get(nombre, {})
    if not forzado and not hay_cambio(anterior.get("firma"), firma_actual):
        # Sin cambios en la fuente: verificar que los publicados existen y
        # pesan lo que se registro; si no, regenerar (un archivo truncado no
        # queda publicando media serie).
        csv_ok = anterior.get("csv") and peso(DOCS / anterior["csv"]["ruta"]) == anterior["csv"].get("bytes")
        json_ok = (not anterior.get("json")) or (
            peso(DOCS / anterior["json"]["ruta"]) == anterior["json"].get("bytes"))
        if csv_ok and json_ok:
            entrada["firma"] = firma_actual
            entrada["csv"] = anterior.get("csv")
            entrada["json"] = anterior.get("json")
            return entrada

    if not escribir:
        # --check: se calcula el estado esperado sin tocar archivos.
        entrada["firma"] = firma_actual
        return entrada

    # Generación real: CSV primero (su tamaño decide qué más se publica).
    if not generar_csv(rutas, where, csv_path):
        # Generación fallida o sobre el tope: el CSV anterior, si había, queda
        # obsoleto y debe desaparecer, no publicar una serie vieja.
        for viejo in (csv_path, json_path):
            try:
                viejo.unlink()
            except OSError:
                pass
        entrada["firma"] = firma_actual
        return entrada
    csv_bytes = peso(csv_path)
    if csv_bytes == 0 or csv_bytes > CSV_MAX_MB * 1024 * 1024:
        for viejo in (csv_path, json_path):
            try:
                viejo.unlink()
            except OSError:
                pass
        entrada["firma"] = firma_actual
        return entrada
    entrada["csv"] = {"ruta": str(csv_path.relative_to(DOCS)), "bytes": csv_bytes, "filas": filas}

    if csv_bytes <= JSON_MAX_MB * 1024 * 1024:
        generar_json(rutas, where, json_path)
        json_bytes = peso(json_path) if json_path.exists() else 0
        if 0 < json_bytes <= JSON_MAX_MB * 1024 * 1024:
            entrada["json"] = {"ruta": str(json_path.relative_to(DOCS)), "bytes": json_bytes}
        else:
            # El JSON Lines repite las claves por fila: un CSV pequeño puede
            # tener un JSON sobre el tope. No se publica.
            try:
                json_path.unlink()
            except OSError:
                pass
    entrada["firma"] = firma_actual
    return entrada


def generar_todo(forzado: bool = False, escribir: bool = True) -> dict:
    indice = json_leer(INDICE) if INDICE.exists() else {}
    conjuntos = indice.get("conjuntos", {})
    for vista in parse_views():
        entrada = generar_conjunto(vista, indice, forzado, escribir=escribir)
        conjuntos[vista["name"]] = entrada
    indice["conjuntos"] = conjuntos
    indice["generado"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    indice["parametros"] = {"csv_max_mb": CSV_MAX_MB, "json_max_mb": JSON_MAX_MB,
                            "parquet_max_mb": PARQUET_MAX_MB}
    return indice


def lista_archivos(indice: dict) -> list[str]:
    """Rutas relativas a docs/ de los CSV/JSON publicados (para git add)."""
    salida = []
    for entrada in indice.get("conjuntos", {}).values():
        for clave in ("csv", "json"):
            valor = entrada.get(clave)
            if valor and (DOCS / valor["ruta"]).exists():
                salida.append(valor["ruta"])
    return sorted(salida)


def verificar(indice: dict) -> list[str]:
    """Errores de consistencia entre el índice y la realidad."""
    errores = []
    for nombre, entrada in indice.get("conjuntos", {}).items():
        for clave in ("csv", "json"):
            valor = entrada.get(clave)
            if not valor:
                continue
            ruta = DOCS / valor["ruta"]
            if not ruta.exists():
                errores.append(f"{nombre}: {clave} registrado sin archivo ({valor['ruta']})")
            elif peso(ruta) != valor.get("bytes"):
                errores.append(f"{nombre}: {clave} con peso distinto del registro")
        for archivo in entrada.get("archivos", []):
            if not (DOCS / archivo["ruta"]).exists():
                errores.append(f"{nombre}: fuente {archivo['ruta']} ausente")
    return errores


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--check", action="store_true", help="falla si el índice está desactualizado")
    ap.add_argument("--lista", action="store_true", help="imprime los archivos generados")
    ap.add_argument("--force", action="store_true", help="regenera todo, sin comparar firmas")
    args = ap.parse_args()

    if duckdb is None:
        print("FALLA: duckdb no está instalado (pip install -r requirements.txt)")
        return 1

    indice = generar_todo(forzado=args.force, escribir=not args.check)
    errores = verificar(indice)
    if errores:
        for error in errores:
            print(f"FALLA: {error}")
        return 1

    if args.check:
        # --check compara el índice recalculado con el guardado: si el datos
        # cambió pero el índice no, el catálogo de descargas enlazaria un CSV
        # viejo (o nulo). La verificación física ya pasó; ahora la escritura.
        guardado = json_leer(INDICE) if INDICE.exists() else {}
        # El campo `generado` es la hora de la última corrida: no forma parte
        # del contenido (lo comparen conjunto a conjunto).
        for datos in (guardado, indice):
            datos.pop("generado", None)
        if json.dumps(guardado, sort_keys=True) != json.dumps(indice, sort_keys=True):
            print("INDICE DE EXPORTACIONES DESACTUALIZADO: ejecuta scripts/build_download_exports.py")
            return 1
        print(f"Índice de exportaciones al día: {len(indice.get('conjuntos', {}))} conjuntos")
        return 0

    conjuntos = indice.get("conjuntos", {})
    con_csv = sum(1 for e in conjuntos.values() if e.get("csv"))
    con_json = sum(1 for e in conjuntos.values() if e.get("json"))
    bytes_csv = sum(int(e["csv"]["bytes"]) for e in conjuntos.values() if e.get("csv"))
    bytes_json = sum(int(e["json"]["bytes"]) for e in conjuntos.values() if e.get("json"))
    json_escribir(INDICE, indice)
    print(f"Índice escrito en {INDICE.relative_to(ROOT)}: {len(conjuntos)} conjuntos · "
          f"{con_csv} con CSV ({bytes_csv / 1e6:,.1f} MB) · {con_json} con JSON ({bytes_json / 1e6:,.1f} MB)")
    if args.lista:
        for ruta in lista_archivos(indice):
            print(ruta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

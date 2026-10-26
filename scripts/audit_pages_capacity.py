#!/usr/bin/env python3
"""Guarda margen para los límites de tamaño de GitHub Pages y reporta el peso de datos.

GitHub Pages admite sitios publicados de hasta 1 GiB. Este control falla antes,
a 900 MiB, para dejar margen a despliegues y artefactos que el checkout local no
incluya. También imprime el tamaño del conjunto Parquet publicado, útil para
estimar transferencia; no presupone que una visita descargue todo ese conjunto.

Uso: python scripts/audit_pages_capacity.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CATALOG = DOCS / "api" / "v2" / "catalog.json"
MIB = 1024**2
GIB = 1024**3
LIMITE_GH_PAGES = 900 * MIB
AVISO = 750 * MIB

# Los cuatro Parquet sin contrato/manifest propio se conservan como muestras o
# registros de proceso citados por su módulo. Mantener la lista explícita impide
# que un archivo nuevo quede fuera del inventario sin revisión.
MUESTRAS_CON_REFERENCIA = {
    "outputs/factoring_leasing/factoring_leasing_eeff_muestra_cmf.parquet": (
        "factoring_leasing/scripts/publish_structured_sample.py",
    ),
    "outputs/factoring_leasing/factoring_leasing_resultados_muestra_cmf.parquet": (
        "factoring_leasing/scripts/publish_income_sample.py",
    ),
    "outputs/ffmm/ffmm_registro_fondos.parquet": (
        "ffmm/scripts/01_build_active_funds_registry.py",
        "ffmm/scripts/01b_build_universe_funds.py",
    ),
    "outputs/ffmm/ffmm_registro_fondos_universo.parquet": (
        "ffmm/scripts/01b_build_universe_funds.py",
    ),
}


def json_leer(ruta: Path) -> Any:
    return json.loads(ruta.read_text(encoding="utf-8"))


def inventariar_parquet() -> tuple[dict[str, dict[str, int]], list[str]]:
    """Clasifica todos los Parquet físicos de `docs/outputs` sin asumir uso externo."""
    errores: list[str] = []
    categorias: dict[str, set[str]] = {
        "api_v2_descargas": set(),
        "auxiliares_sql": set(),
        "manifiestos_separados": set(),
        "muestras_registros": set(MUESTRAS_CON_REFERENCIA),
    }

    for ruta in sorted((DOCS / "api" / "v2" / "partitions").glob("*.json")):
        try:
            documento = json_leer(ruta)
            categorias["api_v2_descargas"].update(
                parte["archivo"] for parte in documento.get("particiones", [])
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            errores.append(f"{ruta.relative_to(ROOT)}: particiones API no legibles ({exc})")

    sql_dir = DOCS / "outputs" / "sql_query"
    for ruta in sorted(sql_dir.glob("*.manifest.json")):
        try:
            manifiesto = json_leer(ruta)
            archivo = manifiesto.get("file", "")
            if "SQL-only" not in manifiesto.get("purpose", ""):
                errores.append(f"{ruta.relative_to(ROOT)}: propósito SQL-only no declarado")
            if not archivo.startswith("outputs/sql_query/"):
                errores.append(f"{ruta.relative_to(ROOT)}: ruta fuera de outputs/sql_query")
            categorias["auxiliares_sql"].add(archivo)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            errores.append(f"{ruta.relative_to(ROOT)}: manifiesto SQL no legible ({exc})")

    manifests_separados = (
        (DOCS / "outputs" / "bancos" / "cmf_b1_b2_r1" / "manifest.json", "periods"),
        (DOCS / "outputs" / "macro" / "series" / "manifest.json", "files"),
    )
    for ruta, clave in manifests_separados:
        try:
            manifiesto = json_leer(ruta)
            entradas = manifiesto.get(clave, [])
            if clave == "periods":
                entradas = [e.get("file", "") for e in entradas]
            categorias["manifiestos_separados"].update(entradas)
        except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
            errores.append(f"{ruta.relative_to(ROOT)}: manifiesto no legible ({exc})")

    query_files = set(re.findall(
        r'queryFile:\s*"([^"]+)"',
        (DOCS / "js" / "duckdb_client.js").read_text(encoding="utf-8"),
    ))
    if query_files != categorias["auxiliares_sql"]:
        errores.append(
            "duckdb_client.js y los manifiestos SQL no enumeran los mismos archivos: "
            f"queryFile={sorted(query_files)}, manifiestos={sorted(categorias['auxiliares_sql'])}"
        )

    clasificados: set[str] = set()
    for nombre, rutas in categorias.items():
        solape = clasificados & rutas
        if solape:
            errores.append(f"Archivos clasificados en más de una categoría ({nombre}): {sorted(solape)}")
        clasificados.update(rutas)

    fisicos = {
        p.relative_to(DOCS).as_posix(): p
        for p in (DOCS / "outputs").rglob("*.parquet")
        if p.is_file() and not p.is_symlink()
    }
    faltantes = clasificados - set(fisicos)
    no_clasificados = set(fisicos) - clasificados
    if faltantes:
        errores.append(f"El inventario apunta a Parquet inexistentes: {sorted(faltantes)}")
    if no_clasificados:
        errores.append(f"Hay Parquet físicos sin categoría explícita: {sorted(no_clasificados)}")

    for archivo, referencias in MUESTRAS_CON_REFERENCIA.items():
        presentes = [
            ref for ref in referencias
            if (ROOT / ref).is_file()
            and Path(archivo).name in (ROOT / ref).read_text(encoding="utf-8", errors="replace")
        ]
        if not presentes:
            errores.append(f"Muestra sin referencia de mantenimiento verificable: {archivo}")

    resumen: dict[str, dict[str, int]] = {}
    for nombre, rutas in categorias.items():
        bytes_categoria = sum(fisicos[r].stat().st_size for r in rutas if r in fisicos)
        resumen[nombre] = {"archivos": len(rutas), "bytes": bytes_categoria}
    resumen["total_fisico"] = {
        "archivos": len(fisicos),
        "bytes": sum(p.stat().st_size for p in fisicos.values()),
    }
    return resumen, errores


def main() -> int:
    if not DOCS.is_dir():
        print(f"FALLA: no existe el directorio publicado {DOCS}")
        return 1

    archivos = [p for p in DOCS.rglob("*") if p.is_file() and not p.is_symlink()]
    total = sum(p.stat().st_size for p in archivos)
    print(f"docs/: {total / MIB:.1f} MiB en {len(archivos):,} archivos")
    print(f"Umbral preventivo: {LIMITE_GH_PAGES / MIB:.0f} MiB (límite documentado: 1 GiB)")

    if CATALOG.exists():
        try:
            catalogo = json.loads(CATALOG.read_text(encoding="utf-8"))
            bytes_datos = int(catalogo["totales"]["bytes"])
            filas = int(catalogo["totales"]["filas"])
            transferencias = 100_000_000_000 / bytes_datos if bytes_datos else 0
            print(
                f"Parquet del catálogo: {bytes_datos / MIB:.1f} MiB · "
                f"{filas:,} filas · ~{transferencias:.0f} transferencias completas "
                "equivalen a 100 GB (solo referencia; normalmente se leen rangos parciales)."
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            print(f"FALLA: no se pudo leer el peso del catálogo ({exc})")
            return 1
    else:
        print(f"FALLA: falta el catálogo publicado {CATALOG.relative_to(ROOT)}")
        return 1

    inventario, problemas_inventario = inventariar_parquet()
    print("Parquet físicos en docs/outputs (inventario estático; no mide descargas ni demanda):")
    for categoria, valores in inventario.items():
        print(f"  {categoria}: {valores['archivos']:,} archivos · {valores['bytes']:,} bytes")
    if problemas_inventario:
        print(f"FALLA: inventario Parquet incompleto ({len(problemas_inventario)} problema(s))")
        for problema in problemas_inventario[:12]:
            print(f"  · {problema}")
        return 1
    print("OK: cada Parquet físico tiene una categoría, referencia y uso declarados.")

    if total >= LIMITE_GH_PAGES:
        print("FALLA: docs/ llegó al umbral preventivo; reducir o externalizar archivos antes de publicar.")
        return 1
    if total >= AVISO:
        print("AVISO: el sitio está sobre 750 MiB; revisar el crecimiento antes del próximo despliegue.")
    else:
        print("OK: el tamaño publicado conserva margen bajo el umbral preventivo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera los artefactos de reproducibilidad que se publican en la web.

El diccionario de la web es bueno para navegar, pero un investigador necesita
poder descargar la documentación y auditarla: este script deja en
`docs/reproducibilidad/` (y por lo tanto en el sitio y en el repositorio) cinco
archivos planos, regenerables con un solo comando:

  * `diccionario.csv` / `diccionario.json`
      Cada columna de cada tabla: tipo, rol, significado y criterio contable.
      Se levanta desde `docs/js/data_dictionary.js`, que es la misma fuente que
      usa el diccionario de la web (así no hay dos versiones que se separen).

  * `inventario_fuentes.csv`
      Archivos Parquet y JSON de datos/metadata bajo `docs/outputs/`, con peso y
      SHA-256. Omite índices de interfaz que tienen su propio generador y control.
      El hash permite comparar una descarga con el artefacto inventariado, pero
      no valida el significado de sus datos.

  * `cobertura_por_periodo.csv`
      Registros por tabla y periodo, según los manifiestos que se publican
      junto a los datos. Es la respuesta corta a «¿desde cuándo hay datos y
      cuántos por mes o trimestre?».

  * `validacion_resumen.csv`
      Una fila por objeto: fuente y otros metadatos declarados, modalidad,
      periodo/cobertura, registros y ruta. No lista resultados de pruebas ni
      tolerancias; es un resumen descriptivo, no un certificado de calidad.

Estos artefactos documentan la publicación, pero no reemplazan los datos de las
fuentes ni prueban por sí solos su validez semántica. Parte de los campos del
diccionario y del manifiesto son metadatos editoriales curados; los conteos,
hashes y cobertura se derivan de archivos/manifiestos según cada artefacto.

Requisitos:
  * `node` (para volcar el diccionario tal como lo carga el navegador).
  * `pyarrow` (opcional): sin él no se cuentan las filas reales de cada Parquet,
    y ese campo queda vacío en vez de inventarse.

Uso:
    python3 scripts/construir_reproducibilidad.py           # escribe los archivos
    python3 scripts/construir_reproducibilidad.py --check   # falla si están desactualizados
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date

try:  # pyarrow es opcional: sin él sólo se pierde el conteo de filas por archivo
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - entorno sin pyarrow
    pq = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
SALIDA = os.path.join(DOCS, "reproducibilidad")
OUTPUTS = os.path.join(DOCS, "outputs")
DATA_MANIFEST = os.path.join(ROOT, "data_manifest.json")
DICCIONARIO_JS = os.path.join(DOCS, "js", "data_dictionary.js")

# Volcado del diccionario: se evalúa el mismo arreglo que carga el navegador.
VOLCADO_JS = r"""
const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
const ini = src.indexOf("const DATA_DICTIONARY = [");
const fin = src.indexOf("\n];", ini);
if (ini < 0 || fin < 0) { console.error("no se encontró DATA_DICTIONARY"); process.exit(1); }
const arr = src.slice(src.indexOf("[", ini), fin + 2);
process.stdout.write(JSON.stringify(eval(arr)));
"""


def leer_json(ruta: str) -> dict:
    with open(ruta, "r", encoding="utf-8") as fh:
        return json.load(fh)


def escribir(ruta: str, contenido: str) -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(contenido)


def csv_texto(encabezado: list[str], filas: list[list]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(encabezado)
    w.writerows(filas)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Diccionario de datos
# ---------------------------------------------------------------------------
def cargar_diccionario() -> list[dict]:
    """Las tablas documentadas, tal como las lee el diccionario de la web."""
    if not shutil.which("node"):
        print("  [aviso] sin node en el PATH: no se puede volcar el diccionario", file=sys.stderr)
        return []
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(VOLCADO_JS)
        temporal = tmp.name
    try:
        proc = subprocess.run(["node", temporal, DICCIONARIO_JS], capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"  [aviso] node no pudo volcar el diccionario: {proc.stderr.strip()}", file=sys.stderr)
            return []
        return json.loads(proc.stdout)
    finally:
        os.unlink(temporal)


def diccionario_csv(tablas: list[dict]) -> str:
    filas = []
    for tabla in tablas:
        for col in tabla.get("columnas", []) or []:
            filas.append([
                tabla.get("name", ""),
                tabla.get("viewName", ""),
                tabla.get("sector", ""),
                tabla.get("norma", ""),
                col.get("name", ""),
                col.get("type", ""),
                col.get("role", ""),
                (col.get("significado", "") or "").replace("\n", " ").strip(),
                col.get("contable", ""),
            ])
    return csv_texto(
        ["tabla", "vista", "sector", "norma", "columna", "tipo", "rol", "significado", "criterio_contable"],
        filas,
    )


def diccionario_json(tablas: list[dict]) -> str:
    documento = {
        "generado": date.today().isoformat(),
        "origen": "docs/js/data_dictionary.js (misma fuente que el diccionario de la web)",
        "tablas": len(tablas),
        "columnas": sum(len(t.get("columnas", []) or []) for t in tablas),
        "datos": tablas,
    }
    return json.dumps(documento, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------
# 2. Inventario de archivos publicados (con SHA-256)
# ---------------------------------------------------------------------------
def sha256(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def filas_parquet(ruta: str):
    if pq is None:
        return None
    try:
        return pq.ParquetFile(ruta).metadata.num_rows
    except Exception:
        return None


def inventario() -> str:
    filas = []
    for actual, _, archivos in os.walk(OUTPUTS):
        for nombre in sorted(archivos):
            if not (nombre.endswith(".parquet") or nombre.endswith(".json")):
                continue
            ruta = os.path.join(actual, nombre)
            rel = os.path.relpath(ruta, DOCS).replace(os.sep, "/")
            # El índice estático de búsqueda es un artefacto de interfaz, no una
            # fuente de datos; tiene su propio builder/--check y debe quedar fuera
            # para que su hash no dependa del orden entre ambos generadores.
            if rel == "outputs/indice_busqueda.json":
                continue
            partes = os.path.relpath(ruta, OUTPUTS).split(os.sep)
            sector = partes[0] if len(partes) > 1 else ""
            tabla = partes[1] if len(partes) > 2 else os.path.splitext(nombre)[0]
            periodo = os.path.splitext(nombre)[0] if len(partes) > 2 and nombre.endswith(".parquet") else ""
            filas.append([
                rel,
                sector,
                tabla,
                periodo,
                os.path.getsize(ruta),
                sha256(ruta),
                "" if filas_parquet(ruta) is None else filas_parquet(ruta),
            ])
    filas.sort()
    return csv_texto(["archivo", "sector", "tabla", "periodo", "bytes", "sha256", "filas"], filas)


# ---------------------------------------------------------------------------
# 3. Cobertura por periodo (según los manifiestos publicados)
# ---------------------------------------------------------------------------
def cobertura() -> str:
    filas = []
    for actual, _, archivos in os.walk(OUTPUTS):
        if "manifest.json" not in archivos:
            continue
        ruta = os.path.join(actual, "manifest.json")
        try:
            manifesto = leer_json(ruta)
        except Exception:
            continue
        periodos = manifesto.get("periodos") if isinstance(manifesto, dict) else None
        if not isinstance(periodos, dict):
            continue
        sector = os.path.relpath(actual, OUTPUTS).split(os.sep)[0]
        for periodo in sorted(periodos):
            registros = periodos[periodo]
            if not isinstance(registros, dict):
                continue
            for tabla, conteo in sorted((registros.get("registros") or {}).items()):
                if not isinstance(conteo, (int, float)):
                    continue
                filas.append([sector, tabla, periodo, int(conteo)])
    filas.sort()
    return csv_texto(["sector", "tabla", "periodo", "registros"], filas)


# ---------------------------------------------------------------------------
# 4. Resumen de validación por tabla
# ---------------------------------------------------------------------------
def validacion(tablas_diccionario: list[dict]) -> str:
    manifesto = leer_json(DATA_MANIFEST)
    por_vista = {t.get("view_name") or t.get("id"): t for t in tablas_diccionario}

    # Cobertura por (sector, tabla) desde los manifiestos, para el ruto real.
    rango: dict[tuple[str, str], dict] = {}
    for actual, _, archivos in os.walk(OUTPUTS):
        if "manifest.json" not in archivos:
            continue
        try:
            datos = leer_json(os.path.join(actual, "manifest.json"))
        except Exception:
            continue
        periodos = datos.get("periodos") if isinstance(datos, dict) else None
        if not isinstance(periodos, dict):
            continue
        sector = os.path.relpath(actual, OUTPUTS).split(os.sep)[0]
        for periodo, detalle in periodos.items():
            if not isinstance(detalle, dict):
                continue
            for tabla, conteo in (detalle.get("registros") or {}).items():
                if not isinstance(conteo, (int, float)):
                    continue
                clave = (sector, tabla)
                info = rango.setdefault(clave, {"desde": periodo, "hasta": periodo, "periodos": 0, "filas": 0})
                info["desde"] = min(info["desde"], periodo)
                info["hasta"] = max(info["hasta"], periodo)
                info["periodos"] += 1
                info["filas"] += int(conteo)

    filas = []
    for tabla in manifesto.get("tables", []):
        vista = tabla.get("view_name") or tabla.get("id")
        doc = por_vista.get(vista, {})
        sector = tabla.get("sector", "")
        nombre_tabla = (tabla.get("name", "") or "").split(".")[-1]
        info = rango.get((sector, nombre_tabla))
        filas.append([
            tabla.get("name", ""),
            vista,
            sector,
            tabla.get("norma", ""),
            tabla.get("modo", ""),
            tabla.get("ultima_actualizacion", ""),
            info["desde"] if info else tabla.get("corte", ""),
            info["hasta"] if info else tabla.get("corte", ""),
            info["periodos"] if info else "",
            info["filas"] if info else tabla.get("registros_reales", ""),
            tabla.get("file_parquet", ""),
            (doc.get("origen") or tabla.get("origen", "")).replace("\n", " ").strip(),
        ])
    filas.sort()
    return csv_texto(
        ["tabla", "vista", "sector", "norma", "modo", "ultima_actualizacion",
         "primer_periodo", "ultimo_periodo", "periodos", "registros", "archivo", "fuente"],
        filas,
    )


# ---------------------------------------------------------------------------
# 5. README de la carpeta
# ---------------------------------------------------------------------------
def readme(tablas: int, columnas: int) -> str:
    return f"""# Reproducibilidad

Archivos planos para consultar y auditar aspectos concretos de la publicación,
sin depender del JavaScript de la web. Se generan con:

```
python3 scripts/construir_reproducibilidad.py
```

Se publican junto al sitio, pero no todos son consumidos directamente por la
interfaz. `diccionario.csv` y `diccionario.json` se derivan del mismo
`docs/js/data_dictionary.js` que alimenta el Diccionario; los demás son artefactos
complementarios para inspeccionar archivos y cobertura.

| Archivo | Qué trae y de dónde sale |
|---|---|
| `diccionario.csv` | Cada columna de cada tabla: tipo, rol, significado y criterio contable ({columnas} columnas en {tablas} tablas). Los campos descriptivos/editoriales proceden del diccionario mantenido en el repositorio. |
| `diccionario.json` | El mismo contenido estructurado en JSON, para cargarlo con pandas o DuckDB. |
| `inventario_fuentes.csv` | Ruta, tamaño y SHA-256 de los archivos Parquet/JSON de datos y metadata bajo `docs/outputs`; se incluye el conteo de filas cuando está disponible. Excluye `indice_busqueda.json`, que es un artefacto de interfaz con su propio control. |
| `cobertura_por_periodo.csv` | Registros por tabla y periodo, leídos de los manifiestos de publicación. |
| `validacion_resumen.csv` | Fuente, norma, modalidad, fecha/rango, periodos, registros y ruta por objeto. Combina metadatos del manifiesto/diccionario con conteos de manifiestos; **no contiene resultados de pruebas, tolerancias ni una certificación de calidad**. |

## Cómo se verifica un archivo

1. Descarga un Parquet de la pestaña Descargas.
2. Calcula su SHA-256: `sha256sum archivo.parquet` (o `shasum -a 256` en macOS).
3. Compáralo con la columna `sha256` de `inventario_fuentes.csv` para esa ruta.

La coincidencia indica que el archivo coincide con el artefacto descrito en este
inventario. No demuestra que su contenido sea semánticamente correcto ni que una
versión anterior siga disponible en el hosting.

## Alcance y límites

Estos archivos documentan aspectos de la base publicada; no son una capa
armonizada para investigación y sus controles no constituyen un sello general
de calidad. Los campos editoriales (por ejemplo, significado, norma o modalidad)
y las mediciones derivadas de manifiestos se distinguen por su fuente; no se
debe inferir una propiedad no documentada a partir de filas o de una clave.

`scripts/construir_snapshot_academico.py` puede armar una copia local con fecha,
hashes y documentación. Ejecutarlo no publica el snapshot, no crea un DOI y no
garantiza recuperar archivos históricos que no se hayan conservado aparte.
"""


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------
def construir() -> dict[str, str]:
    tablas = cargar_diccionario()
    columnas = sum(len(t.get("columnas", []) or []) for t in tablas)
    archivos = {
        "diccionario.csv": diccionario_csv(tablas),
        "diccionario.json": diccionario_json(tablas),
        "inventario_fuentes.csv": inventario(),
        "cobertura_por_periodo.csv": cobertura(),
        "validacion_resumen.csv": validacion(tablas),
        "README.md": readme(len(tablas), columnas),
    }
    return archivos


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera los artefactos de reproducibilidad publicados en la web.")
    parser.add_argument("--check", action="store_true", help="falla si los archivos publicados están desactualizados")
    args = parser.parse_args()

    archivos = construir()

    if args.check:
        desactualizados = []
        for nombre, contenido in archivos.items():
            ruta = os.path.join(SALIDA, nombre)
            if not os.path.exists(ruta):
                desactualizados.append(f"{nombre} (no existe)")
                continue
            with open(ruta, "r", encoding="utf-8", newline="\n") as fh:
                if fh.read() != contenido:
                    desactualizados.append(nombre)
        if desactualizados:
            print("Reproducibilidad desactualizada: " + ", ".join(desactualizados))
            print("Corre: python3 scripts/construir_reproducibilidad.py")
            return 1
        print(f"Reproducibilidad al día ({len(archivos)} archivos).")
        return 0

    for nombre, contenido in archivos.items():
        escribir(os.path.join(SALIDA, nombre), contenido)
        print(f"  {nombre}: {len(contenido.splitlines())} líneas")
    print(f"Listo: {len(archivos)} archivos en docs/reproducibilidad/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

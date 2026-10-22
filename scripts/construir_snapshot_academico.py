#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arma una copia local congelada del núcleo de la base (SIF-Chile Core Holdings).

El sitio es la plataforma viva: cambia con cada publicación. Este script junta
los 25 conjuntos del núcleo en una carpeta con fecha de corte, hashes y
documentación, para trabajar sobre una foto fija sin depender de la web.

Es una herramienta local: la copia que genera NO se publica y no tiene DOI. La
cita del sitio no sale de acá (ver docs/js/cita.js).

    snapshot/sif_chile_core_holdings_v1.0/
        README.md            qué es, alcance, cómo se generó, limitaciones
        CITATION.cff         citación en Citation File Format (lo leen GitHub, Zenodo y los gestores)
        CHANGELOG.md         registro de cambios entre versiones
        LICENSE.txt          licencia del código y nota sobre la licencia de los datos
        datos/…              los Parquet del núcleo, sin alterar
        documentacion/
            diccionario.csv / .json
            cobertura_por_periodo.csv
            validacion_resumen.csv
            inventario_snapshot.csv   SHA-256 de cada archivo de ESTE snapshot

Qué entra en el snapshot: los **25 conjuntos del núcleo** (seguros, fondos
mutuos y fondos de inversión), tal como se publican, con los identificadores ya
protegidos (ver pipelines/auto/privacidad.py). No es una capa armonizada: es la
base fiel a la CMF, congelada en una fecha de corte.

Uso:
    python3 scripts/construir_snapshot_academico.py                  # construye
    python3 scripts/construir_snapshot_academico.py --zip            # + .zip del snapshot
    python3 scripts/construir_snapshot_academico.py --version 1.1 --corte 2026-09
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUTS = DOCS / "outputs"
SALIDA = ROOT / "snapshot"
CATALOGO_JS = DOCS / "js" / "download_catalog.js"
CITA_JS = DOCS / "js" / "cita.js"
NIVEL_SNAPSHOT = "nucleo"

# Metadatos del snapshot. El corte y el github se releen de docs/js/cita.js y
# del catálogo publicado; el resto queda acá porque la web ya no publica ni
# versión congelada ni DOI.
CITA_POR_OMISION = {
    "nombre": "SIF-Chile Core Holdings",
    "version": "1.0",
    "corte": "2026-09",
    "doi": "",
    "autor": "Joaquín Mondaca",
    "orcid": "",
    "github": "https://github.com/joaquinignaciomondaca-code/Sistema_de_Informacion_Financiera_de_Chile",
}


def leer_cita() -> dict:
    """Lee los datos de citación desde docs/js/cita.js (misma fuente que la web)."""
    cita = dict(CITA_POR_OMISION)
    try:
        texto = CITA_JS.read_text(encoding="utf-8")
    except OSError:
        return cita
    for clave in ("nombre", "version", "corte", "doi", "autor", "orcid", "github", "zenodo", "contacto"):
        m = re.search(r'^\s*%s:\s*"([^"]*)"' % clave, texto, re.M)
        if m:
            cita[clave] = m.group(1)
    return cita


def leer_catalogo() -> dict:
    texto = CATALOGO_JS.read_text(encoding="utf-8")
    return json.loads(texto.split("=", 1)[1].strip().rstrip(";"))


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def items_nucleo(catalogo: dict) -> list[dict]:
    """Conjuntos del núcleo con datos publicados.

    Quedan fuera las tablas ocultas (`fi_bienes_raices`): la fuente todavía no
    publica filas para ellas, así que en el snapshot no aportan nada y sí
    confunden el conteo de conjuntos.
    """
    ocultas = set((catalogo.get("alcance") or {}).get("tablas_ocultas", []) or [])
    items = []
    for grupo in catalogo.get("grupos", []):
        for item in grupo.get("items", []):
            if item.get("nivel") != NIVEL_SNAPSHOT or item.get("id") in ocultas:
                continue
            if not item.get("archivos"):
                continue
            items.append(item)
    return items


# ---------------------------------------------------------------------------
# Documentos del snapshot
# ---------------------------------------------------------------------------
def readme(cita: dict, items: list[dict], filas: int, bytes_totales: int) -> str:
    lineas = "\n".join(
        f"| `{i['nombre']}` | {i.get('detalle', '')} | {i['filas']:,} | {i.get('cobertura', '')} |"
        for i in sorted(items, key=lambda x: x["nombre"])
    )
    return f"""# {cita['nombre']} v{cita['version']}

Versión congelada y citable del **Sistema de Información Financiera de Chile**
(SIF): las carteras y los estados financieros de los tres grandes inversionistas
institucionales chilenos —compañías de seguros, fondos mutuos y fondos de
inversión— tal como los reportan a la Comisión para el Mercado Financiero.

- **Fecha de corte:** {cita['corte']}
- **Conjuntos:** {len(items)} (el núcleo del sistema)
- **Registros:** {filas:,}
- **Peso:** {bytes_totales / 1e6:.1f} MB en Parquet
- **Publicado:** {date.today().isoformat()}
- **DOI:** {cita['doi'] or 'No tiene: esta es una copia local, sin depósito ni identificador permanente.'}

## Qué contiene

| Conjunto | Detalle | Registros | Cobertura |
|---|---|---|---|
{lineas}

Los archivos conservan la estructura y los nombres con que se publican en el
sitio, dentro de `datos/`. Los manifiestos (`manifest.json`) acompañan a cada
carpeta con los conteos por periodo.

## Cómo se generó

```
python3 scripts/construir_snapshot_academico.py --zip
```

El script copia los Parquet publicados (sin alterarlos), agrega la documentación
de `docs/reproducibilidad/` y calcula `documentacion/inventario_snapshot.csv`
con el SHA-256 de cada archivo de este snapshot. El repositorio con el código y
los pipelines está en {cita['github']}.

## Verificación

```
sha256sum datos/seguros/renta_fija/2026-09.parquet
```

El resultado debe coincidir con la columna `sha256` de
`documentacion/inventario_snapshot.csv`.

## Privacidad

Se aplican las reglas de `pipelines/auto/privacidad.py`:

- En `fi.cartera_nacional` se suprime `rut_emisor` cuando probablemente
  corresponde a una persona natural, y la columna `emisor_tipo` documenta el
  criterio aplicado en cada fila.
- En `seguros.bienes_raices` no se publican la dirección exacta (`ubicacion`,
  `direccion`) ni el rol tributario; se conservan comuna, ciudad y un
  `property_id` estable.

## Fuentes y limitaciones

- **Los datos son de sus fuentes oficiales** (CMF y Banco Central de Chile,
  principalmente). El SIF aporta extracción, normalización, validación,
  documentación y armonización: no genera ni modifica los datos.
- **Proyecto independiente:** no tiene respaldo ni aval de la CMF ni del Banco
  Central de Chile.
- **Cobertura:** la extensión de la serie de tiempo de cada tabla dependerá de
  cada fuente de origen; es por ello que no hay homogeneización generalizada de
  periodos entre todas las tablas. Revise
  `documentacion/cobertura_por_periodo.csv` antes de comparar periodos.
- **Unidades:** los montos conservan la unidad y el criterio de valorización de
  la fuente. No se convierten ni se reexpresan.
- **No incluye carteras de AFP** ni una capa armonizada para investigación: esto
  es la base fiel a la fuente, congelada.
"""


def citation_cff(cita: dict) -> str:
    autores = f"""authors:
  - family-names: "Mondaca"
    given-names: "Joaquín\""""
    if cita.get("orcid"):
        autores += f'\n    orcid: "{cita["orcid"]}"'
    doi = f'\ndoi: "{cita["doi"]}"' if cita.get("doi") else ""
    return f"""cff-version: 1.2.0
message: "Si usas estos datos, por favor cítalos con la referencia de abajo."
title: "{cita['nombre']} v{cita['version']}: carteras y estados financieros de seguros, fondos mutuos y fondos de inversión de Chile"
abstract: "Copia local congelada del Sistema de Información Financiera de Chile: carteras de inversión y estados financieros reportados a la CMF por compañías de seguros, fondos mutuos y fondos de inversión, con corte al {cita['corte']}."
type: dataset
{autores}
version: "{cita['version']}"
date-released: "{date.today().isoformat()}"
license: MIT
repository-code: "{cita['github']}"
keywords:
  - datos abiertos
  - carteras de inversión
  - inversión institucional
  - Chile
  - CMF
{doi}
"""


def changelog(cita: dict, items: list[dict], filas: int) -> str:
    return f"""# Registro de cambios

## v{cita['version']} — {date.today().isoformat()} (corte {cita['corte']})

Primera versión congelada.

- {len(items)} conjuntos del núcleo: seguros, fondos mutuos y fondos de inversión.
- {filas:,} registros en total.
- Identificadores protegidos: `rut_emisor` de personas naturales en
  `fi.cartera_nacional` (con columna `emisor_tipo`) y dirección/rol en
  `seguros.bienes_raices` (con `property_id`).
- Documentación incluida: diccionario de datos, cobertura por periodo, resumen
  de validación e inventario con SHA-256.

Convención de versiones: `X.Y`; un cambio en `X` implica un cambio de criterio
que altera cifras publicadas, y un cambio en `Y` sólo agrega periodos o corrige
documentación.
"""


def licencia(cita: dict) -> str:
    mit = (ROOT / "LICENSE").read_text(encoding="utf-8") if (ROOT / "LICENSE").exists() else ""
    return f"""{mit}

---

## Sobre los datos

Los datos incluidos en este snapshot pertenecen a sus fuentes oficiales
(Comisión para el Mercado Financiero, Banco Central de Chile, Superintendencia
de Pensiones y SUSESO) y se republican sin alterar su contenido. La licencia MIT
de arriba cubre el código del proyecto, no el contenido de los datos: antes de
redistribuirlos verifique las condiciones de reutilización de cada fuente.

© {date.today().year} {cita['autor']}
"""


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Arma la versión congelada y citable de la base.")
    parser.add_argument("--version", help="versión del snapshot (por omisión, la de docs/js/cita.js)")
    parser.add_argument("--corte", help="fecha de corte (AAAA-MM)")
    parser.add_argument("--zip", action="store_true", help="además arma un .zip con todo el snapshot")
    args = parser.parse_args()

    cita = leer_cita()
    if args.version:
        cita["version"] = args.version
    if args.corte:
        cita["corte"] = args.corte

    catalogo = leer_catalogo()
    items = items_nucleo(catalogo)
    if not items:
        print("El catálogo no declara conjuntos de nivel «nucleo». Corre scripts/build_download_catalog.py.")
        return 1

    nombre = f"sif_chile_core_holdings_v{cita['version']}".replace(" ", "_")
    destino = SALIDA / nombre
    if destino.exists():
        shutil.rmtree(destino)
    (destino / "datos").mkdir(parents=True)
    (destino / "documentacion").mkdir(parents=True)

    # 1. Datos: los Parquet del núcleo, tal como se publican.
    copiados, filas, bytes_totales = [], 0, 0
    for item in items:
        for archivo in item.get("archivos", []):
            ruta = DOCS / archivo["ruta"]
            if not ruta.exists():
                print(f"  [aviso] falta {archivo['ruta']}")
                continue
            relativo = Path(archivo["ruta"]).relative_to("outputs")
            salida = destino / "datos" / relativo
            salida.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ruta, salida)
            copiados.append((salida.relative_to(destino).as_posix(), salida.stat().st_size, sha256(salida)))
            bytes_totales += salida.stat().st_size
        filas += int(item.get("filas") or 0)
        # El manifiesto del conjunto viaja con los datos: trae los conteos por periodo.
        manifesto = OUTPUTS / Path(item["archivos"][0]["ruta"]).relative_to("outputs").parts[0] / "manifest.json"
        if manifesto.exists():
            salida = destino / "datos" / Path(manifesto).relative_to(OUTPUTS)
            salida.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(manifesto, salida)
            copiados.append((salida.relative_to(destino).as_posix(), salida.stat().st_size, sha256(salida)))

    # 2. Documentación publicada.
    for archivo in ("diccionario.csv", "diccionario.json", "cobertura_por_periodo.csv", "validacion_resumen.csv"):
        origen = DOCS / "reproducibilidad" / archivo
        if origen.exists():
            shutil.copy2(origen, destino / "documentacion" / archivo)

    # 3. Inventario con los hashes de ESTE snapshot (no los del sitio).
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["archivo", "bytes", "sha256"])
    w.writerows(sorted(copiados))
    (destino / "documentacion" / "inventario_snapshot.csv").write_text(buf.getvalue(), encoding="utf-8")

    # 4. Documentos de citación.
    (destino / "README.md").write_text(readme(cita, items, filas, bytes_totales), encoding="utf-8")
    (destino / "CITATION.cff").write_text(citation_cff(cita), encoding="utf-8")
    (destino / "CHANGELOG.md").write_text(changelog(cita, items, filas), encoding="utf-8")
    (destino / "LICENSE.txt").write_text(licencia(cita), encoding="utf-8")

    print(f"Snapshot en {destino.relative_to(ROOT).as_posix()}")
    print(f"  {len(items)} conjuntos · {filas:,} registros · {bytes_totales / 1e6:.1f} MB")
    print(f"  {len(copiados)} archivos de datos · documentación y citación incluidas")

    if args.zip:
        zip_base = SALIDA / nombre
        shutil.make_archive(str(zip_base), "zip", root_dir=destino)
        print(f"  ZIP del snapshot: {zip_base.name}.zip")

    print("\nCopia local lista. No se publica ni tiene DOI: la cita del sitio no "
          "sale de acá (ver docs/js/cita.js).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

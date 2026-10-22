#!/usr/bin/env python3
"""Reconcilia los objetos del contrato con lo publicado (Fase 0c de la ruta de la API).

Hay tres niveles que hasta ahora nadie había cruzado, y por eso el manifiesto
decía 89 donde el catálogo decía 90:

  1. **Objeto de contrato**: las vistas SQL que consume un cliente
     (`SEMANTIC_VIEWS` en `docs/js/duckdb_client.js`). Son 90.
  2. **Fila del manifiesto**: las 89 tablas de `data_manifest.json`.
  3. **Dataset físico**: los Parquet y sus `manifest.json` en `docs/outputs/`.

El cruce no es 1:1 y este script lo deja explícito:

  * 16 filas del manifiesto usan el nombre **heredado** (`seguros_maestro`) y su
    objeto canónico es el alias (`seguros_lista_entidades`).
  * 1 fila del manifiesto (`bancos_cmf_lineas`) describe un dataset del que se
    publican **dos** objetos (`bancos_balance` y `bancos_resultados`), separados
    por `familia_archivo_fuente` (B1/B2 contra R1).

Genera `docs/api/reconciliacion.csv` y falla si queda algún objeto sin estado,
alguna fila del manifiesto sin objeto o algún objeto sin fila.

Uso:
    python3 scripts/build_reconciliacion.py            # escribe el CSV y valida
    python3 scripts/build_reconciliacion.py --check    # sólo valida (CI)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
sys.path.insert(0, str(RAIZ / "scripts"))

import audit_consultas_sugeridas as ac  # noqa: E402

DESTINO = DOCS / "api" / "reconciliacion.csv"

# Filas del manifiesto que no se llaman como su objeto canónico y que no están en
# LEGACY_VIEW_ALIASES: un dataset físico con varias vistas encima.
ORIGEN_COMPARTIDO = {
    "bancos_cmf_lineas": [
        ("bancos_balance", "familia_archivo_fuente IN ('B1', 'B2')"),
        ("bancos_resultados", "familia_archivo_fuente = 'R1'"),
    ],
}

# Objetos que son proyección de otro (no son un hecho distinto).
DERIVADOS = {
    "seguros_renta_fija_relevante": "seguros_renta_fija",
    "seguros_acciones_relevantes": "seguros_acciones",
    "seguros_bienes_raices_relevantes": "seguros_bienes_raices",
    "seguros_extranjeros_relevantes": "seguros_extranjeros",
    "seguros_derivados_relevantes": "seguros_derivados",
    "seguros_prestamos_relevantes": "seguros_prestamos",
    "seguros_bienes_raices_arriendo_morosidad_relevantes": "seguros_bienes_raices_arriendo_morosidad",
}


def cargar() -> tuple[list[dict], dict[str, dict], dict[str, dict], dict[str, list[str]]]:
    manifiesto = json.loads((RAIZ / "data_manifest.json").read_text(encoding="utf-8"))
    txt = (DOCS / "js" / "download_catalog.js").read_text(encoding="utf-8")
    catalogo = json.loads(txt.split("=", 1)[1].strip().rstrip(";"))
    items = {i["id"]: i for g in catalogo["grupos"] for i in g["items"]}
    vistas = {v["name"]: v for v in ac.vistas_semanticas()}
    alias = ac.alias_heredados()
    return manifiesto["tables"], items, vistas, alias


def filas_de(vista: dict) -> list[str]:
    """Rutas publicadas de una vista, resueltas contra docs/."""
    return [str(Path(p).relative_to(DOCS)) for p in ac.ficheros_de(vista)]


def construir() -> tuple[list[dict], list[str]]:
    tablas, items, vistas, alias = cargar()
    problemas: list[str] = []

    # 1. índice por `view_name` del manifiesto. `alias` va en la dirección
    # canónico -> nombres heredados, que es la que se necesita aquí.
    por_view_name = {t["view_name"]: t for t in tablas}
    por_id = {t["id"]: t for t in tablas}

    def fila_manifiesto(objeto: str) -> tuple[dict | None, str]:
        if objeto in por_view_name:
            return por_view_name[objeto], "directo"
        for viejo in alias.get(objeto, []):
            if viejo in por_view_name:
                return por_view_name[viejo], "alias"
        for origen, destinos in ORIGEN_COMPARTIDO.items():
            if objeto in [d[0] for d in destinos] and origen in por_id:
                return por_id[origen], "origen_compartido"
        return None, ""

    filas, usados = [], set()
    for objeto in sorted(vistas):
        vista = vistas[objeto]
        fila, puente = fila_manifiesto(objeto)
        rutas = filas_de(vista)
        item = items.get(objeto, {})

        if fila is None:
            problemas.append(f"objeto sin fila en el manifiesto: {objeto}")
            fila = {}
        else:
            usados.add(fila.get("id"))

        estado, motivo = "publicado", ""
        if not rutas:
            estado, motivo = "vacio", "sin particiones publicadas (la CMF aún no entrega la tabla)"
        elif objeto in DERIVADOS:
            estado, motivo = "derivado", f"proyección de {DERIVADOS[objeto]}"
        elif puente == "origen_compartido":
            filtro = next((d[1] for d in ORIGEN_COMPARTIDO[fila["id"]] if d[0] == objeto), "")
            estado, motivo = "derivado", f"vista sobre {fila['id']} con filtro {filtro}"
        if objeto not in items:
            problemas.append(f"objeto sin entrada en el catálogo de descargas: {objeto}")

        filas.append({
            "objeto": objeto,
            "nombre_visible": fila.get("name", ""),
            "manifest_id": fila.get("id", ""),
            "puente": puente or "—",
            "nivel": item.get("nivel", ""),
            "estado": estado,
            "motivo": motivo,
            "deriva_de": DERIVADOS.get(objeto, fila.get("id", "") if puente == "origen_compartido" else ""),
            "particiones": len(rutas),
            "filas": fila.get("registros_reales", item.get("filas", "")),
            "bytes": item.get("bytes", ""),
            "corte": fila.get("corte", ""),
            "ultima_actualizacion": fila.get("ultima_actualizacion", ""),
        })

    # 2. Toda fila del manifiesto debe estar consumida por algún objeto.
    for t in tablas:
        if t["id"] not in usados:
            problemas.append(f"fila del manifiesto sin objeto en el contrato: {t['id']}")

    return filas, problemas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="sólo valida; no escribe el CSV")
    args = ap.parse_args(argv)

    filas, problemas = construir()
    por_estado: dict[str, int] = {}
    for f in filas:
        por_estado[f["estado"]] = por_estado.get(f["estado"], 0) + 1
    por_puente: dict[str, int] = {}
    for f in filas:
        por_puente[f["puente"]] = por_puente.get(f["puente"], 0) + 1

    print(f"objetos: {len(filas)}  |  manifiesto: {len({f['manifest_id'] for f in filas})} filas usadas")
    print("por estado:", ", ".join(f"{k}={v}" for k, v in sorted(por_estado.items())))
    print("por puente:", ", ".join(f"{k}={v}" for k, v in sorted(por_puente.items())))

    if problemas:
        print(f"\nPROBLEMAS ({len(problemas)}):")
        for p in problemas[:30]:
            print("  -", p)
        if len(problemas) > 30:
            print(f"  … y {len(problemas) - 30} más")
        return 1

    if not args.check:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        with DESTINO.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)
        print(f"\nEscrito {DESTINO.relative_to(RAIZ)} ({len(filas)} filas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

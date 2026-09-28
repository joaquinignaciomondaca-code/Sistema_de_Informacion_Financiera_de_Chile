#!/usr/bin/env python3
"""Guardián de automatización: ninguna tabla publicada puede quedar como «foto fija» sin aviso.

Inventario: pipelines/auto/inventario.json declara, para CADA tabla de data_manifest.json, qué
workflow y qué script la actualizan, o el motivo explícito por el que es manual.

Revisión estática (en cada push, sin red):
  1. toda tabla de data_manifest.json y toda vista del sitio (SEMANTIC_VIEWS de
     docs/js/duckdb_client.js) está en el inventario (una tabla nueva sin automatizar falla);
  2. el workflow existe, tiene horario (cron) y ejecuta el script declarado;
  3. el script (o los que declara) nombra el archivo publicado de la tabla (o la «marca» declarada
     cuando arma el nombre por partes);
  4. el texto «modo» que muestra la web coincide: «Manual» si es manual, «Automático» si no.

Revisión de frescura (--frescura, semanal en Actions, requiere GH_TOKEN y la rama por defecto):
  5. cada workflow del inventario tuvo una corrida exitosa en los últimos `max_dias` días.
     Si no, falla (y el workflow abre un issue).

Uso:  python scripts/audit_automatizacion.py [--frescura --repo dueño/repo --rama main]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INVENTARIO = RAIZ / "pipelines" / "auto" / "inventario.json"


def estatica() -> list[str]:
    errores = []
    inv = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    tablas_inv, flujos = inv["tablas"], inv["workflows"]
    man = json.loads((RAIZ / "data_manifest.json").read_text(encoding="utf-8"))
    ids = {t["id"] for t in man["tables"]}
    for t in man["tables"]:
        e = tablas_inv.get(t["id"])
        modo = (t.get("modo") or "").lower()
        if e is None:
            errores.append(f"{t['id']}: no está en pipelines/auto/inventario.json (¿quién la actualiza?)")
            continue
        if "manual" in e:
            if not str(e["manual"]).strip():
                errores.append(f"{t['id']}: manual sin motivo")
            if not modo.startswith("manual"):
                errores.append(f"{t['id']}: es manual pero la web dice «{t.get('modo')}»")
            continue
        if modo.startswith("manual") or "automático" not in modo:
            errores.append(f"{t['id']}: está automatizada pero la web dice «{t.get('modo')}»")
        wf = flujos.get(e.get("workflow"))
        if wf is None:
            errores.append(f"{t['id']}: workflow {e.get('workflow')!r} no declarado en el inventario")
            continue
        base = Path(t["file_parquet"]).name.replace(".parquet", "")
        if base == "manifest.json":  # tabla particionada: se identifica por su carpeta
            base = Path(t["file_parquet"]).parent.name
        base = e.get("marca") or base  # el script arma el nombre por partes
        textos = "".join((RAIZ / s).read_text(encoding="utf-8", errors="ignore")
                         for s in wf["scripts"] if (RAIZ / s).exists())
        if base not in textos:
            errores.append(f"{t['id']}: ningún script de {e['workflow']} nombra «{base}» (no la escribe)")
    for nombre, wf in flujos.items():
        ruta = RAIZ / ".github" / "workflows" / nombre
        if not ruta.exists():
            errores.append(f"workflow {nombre}: no existe")
            continue
        y = ruta.read_text(encoding="utf-8")
        if not re.search(r"^\s*-\s*cron:", y, re.M):
            errores.append(f"workflow {nombre}: sin horario (cron)")
        for s in wf["scripts"]:
            if not (RAIZ / s).exists():
                errores.append(f"workflow {nombre}: el script {s} no existe")
            modulo = s.removesuffix(".py").replace("/", ".")
            if s not in y and modulo not in y and not wf.get("scripts_indirectos"):
                errores.append(f"workflow {nombre}: no ejecuta {s}")
    # El sitio lee sus tablas de SEMANTIC_VIEWS (docs/js/duckdb_client.js), no solo de data_manifest:
    # cada vista debe corresponder a una tabla inventariada (por nombre o por archivo).
    por_archivo = {t["file_parquet"]: t["id"] for t in man["tables"]}
    vistas = vistas_web()
    for nombre, ruta in vistas.items():
        tid = nombre if nombre in tablas_inv else por_archivo.get(ruta)
        e = tablas_inv.get(tid) if tid else None
        if e is None:
            errores.append(f"vista web {nombre} ({ruta}): no está en pipelines/auto/inventario.json (¿quién la actualiza?)")
            continue
        if tid in ids or "manual" in e:
            continue  # ya revisada arriba
        wf = flujos.get(e.get("workflow"))
        if wf is None:
            errores.append(f"vista web {nombre}: workflow {e.get('workflow')!r} no declarado en el inventario")
            continue
        base = e.get("marca") or (Path(ruta).parent.name if ruta.endswith("manifest.json") else Path(ruta).stem)
        textos = "".join((RAIZ / s).read_text(encoding="utf-8", errors="ignore") for s in wf["scripts"] if (RAIZ / s).exists())
        if base not in textos:
            errores.append(f"vista web {nombre}: ningún script de {e['workflow']} nombra «{base}» (no la escribe)")
    for tid in set(tablas_inv) - ids - set(vistas):
        errores.append(f"inventario: {tid} ya no existe en data_manifest.json ni en el sitio (quitarla)")
    return errores


def vistas_web() -> dict[str, str]:
    s = (RAIZ / "docs" / "js" / "duckdb_client.js").read_text(encoding="utf-8")
    i = s.index("const SEMANTIC_VIEWS = [")
    j = s.index("\n];", i)
    return {n: r for n, _, r in re.findall(r'name:\s*"([^"]+)"\s*,\s*(file|manifest):\s*"([^"]+)"', s[i:j])}


def llegada(nombre: str, rama: str) -> datetime | None:
    """Fecha en que el workflow llegó a la rama (primer commit de primer padre que lo trae)."""
    import subprocess
    for ref in (f"origin/{rama}", rama, "HEAD"):
        r = subprocess.run(["git", "log", "--first-parent", "--format=%cI", ref, "--", f".github/workflows/{nombre}"],
                           cwd=RAIZ, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return datetime.fromisoformat(r.stdout.strip().splitlines()[-1])
    return None


def frescura(repo: str, rama: str) -> list[str]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    inv = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    ahora, errores = datetime.now(timezone.utc), []
    for nombre, wf in inv["workflows"].items():
        def api(ruta: str) -> dict:
            req = urllib.request.Request(f"https://api.github.com/repos/{repo}/actions/workflows/{nombre}{ruta}",
                                         headers={"Accept": "application/vnd.github+json",
                                                  **({"Authorization": f"Bearer {token}"} if token else {})})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        try:
            runs = api(f"/runs?branch={rama}&status=success&per_page=1").get("workflow_runs", [])
            if not runs:
                creado = llegada(nombre, rama) or datetime.fromisoformat(api("")["created_at"].replace("Z", "+00:00"))
        except Exception as e:
            errores.append(f"{nombre}: no se pudo consultar GitHub ({e})")
            continue
        if not runs:
            dias = (ahora - creado).days
            if dias <= wf["max_dias"]:
                print(f"{nombre:36} sin corridas aún; llegó a {rama} hace {dias} días")
            else:
                errores.append(f"{nombre}: ninguna corrida exitosa en {rama} (llegó hace {dias} días)")
            continue
        ultima = datetime.fromisoformat(runs[0]["updated_at"].replace("Z", "+00:00"))
        dias = (ahora - ultima).days
        estado = "OK" if dias <= wf["max_dias"] else "ATRASADO"
        print(f"{nombre:36} última corrida exitosa hace {dias:3d} días (máx. {wf['max_dias']}) {estado}")
        if dias > wf["max_dias"]:
            errores.append(f"{nombre}: {dias} días sin una corrida exitosa (máximo {wf['max_dias']}); "
                           f"sus tablas se están quedando como foto fija")
    return errores


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frescura", action="store_true")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--rama", default="main")
    a = ap.parse_args(argv)
    errores = estatica()
    if a.frescura:
        errores += frescura(a.repo, a.rama)
    for e in errores:
        print(f"Error: {e}")
    n = len(json.loads(INVENTARIO.read_text())["tablas"])
    print(f"Automatización: {n} tablas inventariadas, {len(errores)} problemas.")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())

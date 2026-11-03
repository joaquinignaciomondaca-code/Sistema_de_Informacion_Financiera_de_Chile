#!/usr/bin/env python3
"""Experimento ETL con api-anything: HTML de CMF/SPensiones en tier 1.

Las fuentes vivas (cmfchile.cl, spensiones.cl) no son alcanzables desde el
entorno de desarrollo, así que este experimento usa **fixtures sintéticas** con
la estructura de tabla de esas páginas (`integraciones/api-anything/etl/fixtures`).
No afirma que la extracción viva esté verificada; prueba el mecanismo:

  1. Una spec HTML (items + fields) extrae filas por HTTP puro (tier 1, sin navegador).
  2. `verify --strict` pasa con la fixture original.
  3. Se simula deriva del sitio (cambia la clase de la tabla): `verify` falla.
  4. Se repara el selector de la spec: `verify` vuelve a pasar.

Requiere Node >= 22.13 y api-anything 0.3.2 (`--cli` o `API_ANYTHING_CLI`).

    python3 scripts/probar_api_anything_etl.py
    python3 scripts/probar_api_anything_etl.py --check

Deja la evidencia en `docs/api/api_anything_etl.log`. El runbook para fuentes
vivas está en `integraciones/api-anything/etl/README.md`.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from http.server import ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from preview_no_cache import NoCacheHandler  # noqa: E402

FIXTURES = RAIZ / "integraciones" / "api-anything" / "etl" / "fixtures"
LOG = RAIZ / "docs" / "api" / "api_anything_etl.log"


class Silencioso(NoCacheHandler):
    def log_message(self, *args):
        pass


def cli_por_defecto() -> list[str]:
    if os.environ.get("API_ANYTHING_CLI"):
        return shlex.split(os.environ["API_ANYTHING_CLI"])
    return ["npx", "-y", "api-anything@0.3.2"]


def correr(cli: list[str], env: dict, *args: str, timeout: int = 180) -> dict:
    r = subprocess.run(cli + list(args), env=env, capture_output=True, text=True, timeout=timeout)
    try:
        salida = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        raise RuntimeError(f"salida no JSON de {' '.join(args)}: {r.stdout[:300]} {r.stderr[:300]}")
    salida["_rc"] = r.returncode
    return salida


def spec_html(base: str, clase: str = "tabla") -> dict:
    def op(nombre: str, archivo: str, campos: dict) -> dict:
        url = f"{base}/{archivo}"
        return {
            "name": nombre,
            "description": f"Fixture HTML de {nombre} (tier 1, sin navegador).",
            "request": {"method": "GET", "url": url, "headers": {}},
            "slots": [],
            "trigger": {"url": url},
            "match": {"method": "GET", "path": f"/{archivo}"},
            "response": {"format": "html", "html": {"items": f"table.{clase} tbody tr", "fields": campos}},
            "params": [],
            "readOnly": True,
            "minTier": 1,
            "learnedLoggedIn": False,
            "checks": [{"args": {}, "expect": "result", "purpose": "la tabla tiene filas"}],
        }
    return {
        "name": "sif-etl-fixture",
        "displayName": "SIF ETL · fixtures CMF/SPensiones",
        "baseUrl": base,
        "description": "Fixtures sintéticas para probar extracción HTML tier 1 y el ciclo deriva/reparación.",
        "operations": [
            op("cmf_entidades", "cmf_entidades.html",
               {"rut": "td:nth-child(1)", "nombre": "td:nth-child(2)", "tipo": "td:nth-child(3)", "estado": "td:nth-child(4)"}),
            op("spensiones_afp", "spensiones_afp.html",
               {"rut": "td:nth-child(1)", "administradora": "td:nth-child(2)", "fantasia": "td:nth-child(3)", "vigencia": "td:nth-child(4)"}),
        ],
    }


def instalar(home: Path, spec: dict) -> None:
    (home / "sites").mkdir(parents=True, exist_ok=True)
    (home / "sites" / "sif-etl-fixture.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--cli", default=None)
    args = ap.parse_args()
    cli = shlex.split(args.cli) if args.cli else cli_por_defecto()
    lineas = [f"# api-anything ETL (fixtures) · {datetime.now().isoformat(timespec='seconds')}", ""]
    checks: list[tuple[str, bool, str]] = []

    with tempfile.TemporaryDirectory(prefix="sif-etl-fixture-") as tmp:
        tmp = Path(tmp)
        web = tmp / "web"
        shutil.copytree(FIXTURES, web)
        servidor = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Silencioso, directory=str(web)))
        puerto = servidor.server_address[1]
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{puerto}"
        home = tmp / "home"
        env = {**os.environ, "API_ANYTHING_HOME": str(home)}
        try:
            # 1-2. Extracción tier 1 y verify en verde.
            instalar(home, spec_html(base))
            llamada = correr(cli, env, "call", "sif-etl-fixture", "spensiones_afp", "--max-tier", "1",
                             "--fields", "rut,administradora", "--max-chars", "1200")
            datos = llamada.get("data") or []
            checks.append(("tier 1 HTML", bool(llamada.get("ok")) and len(datos) == 7,
                           f"{len(datos)} AFP extraídas sin navegador"))
            v1 = correr(cli, env, "verify", "sif-etl-fixture", "--strict")
            checks.append(("verify original", bool(v1.get("ok")),
                           f"pass={v1.get('counts', {}).get('pass')} fail={v1.get('counts', {}).get('fail')}"))

            # 3. Deriva: el sitio cambia la clase de la tabla.
            for archivo in ("cmf_entidades.html", "spensiones_afp.html"):
                p = web / archivo
                p.write_text(p.read_text(encoding="utf-8").replace('class="tabla"', 'class="tabla-v2"'), encoding="utf-8")
            v2 = correr(cli, env, "verify", "sif-etl-fixture", "--strict")
            checks.append(("verify tras deriva", not v2.get("ok") and v2.get("counts", {}).get("fail", 0) > 0,
                           f"fail={v2.get('counts', {}).get('fail')} (la spec dejó de encontrar la tabla)"))

            # 4. Reparación: se actualiza el selector y vuelve a pasar.
            instalar(home, spec_html(base, clase="tabla-v2"))
            v3 = correr(cli, env, "verify", "sif-etl-fixture", "--strict")
            checks.append(("verify tras reparación", bool(v3.get("ok")),
                           f"pass={v3.get('counts', {}).get('pass')} fail={v3.get('counts', {}).get('fail')}"))
        finally:
            servidor.shutdown()
            servidor.server_close()

    for nombre, ok, detalle in checks:
        linea = f"{'OK   ' if ok else 'FALLA'} {nombre} · {detalle}"
        print(linea)
        lineas.append(linea)
    fallos = [c for c in checks if not c[1]]
    veredicto = ("ETL api-anything: extracción HTML tier 1 y ciclo deriva→reparación probados con fixtures"
                 if not fallos else f"ETL api-anything: {len(fallos)} comprobación(es) fallaron")
    print(veredicto)
    lineas += ["", veredicto]
    LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Evidencia: {LOG.relative_to(RAIZ)}")
    return 1 if (fallos and args.check) else 0


if __name__ == "__main__":
    raise SystemExit(main())

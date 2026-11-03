#!/usr/bin/env python3
"""Prueba real de la spec api-anything contra un espejo local del contrato.

El sitio publicado no es alcanzable desde el entorno de desarrollo, así que se
sirve `docs/` con el mismo handler sin caché de la web (HTTP Range incluido) y se
apunta la spec a ese espejo. Lo que se prueba es el contrato HTTP+JSON: las 6
operaciones, la clasificación de un id inexistente como `input`, la vista de
resultado paginada (`result`) y `verify --strict`.

Requiere Node >= 22.13 y api-anything 0.3.2. Por defecto lo ejecuta con
`npx -y api-anything@0.3.2`; se puede fijar otro binario con `--cli` o
`API_ANYTHING_CLI` (p. ej. `node /ruta/a/api-anything/dist/cli.js`).

    python3 scripts/probar_api_anything.py
    python3 scripts/probar_api_anything.py --check
    python3 scripts/probar_api_anything.py --cli "node /tmp/aa/node_modules/api-anything/dist/cli.js"

Deja la evidencia en `docs/api/api_anything.log`.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import shlex
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from http.server import ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import build_api_anything as B  # noqa: E402
from preview_no_cache import NoCacheHandler  # noqa: E402

LOG = RAIZ / "docs" / "api" / "api_anything.log"
NOMBRE_REPO = "Sistema_de_Informacion_Financiera_de_Chile"


class Silencioso(NoCacheHandler):
    def log_message(self, *args):  # noqa: D401
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--cli", default=None, help="comando del CLI de api-anything")
    args = ap.parse_args()
    cli = shlex.split(args.cli) if args.cli else cli_por_defecto()
    lineas = [f"# api-anything · {datetime.now().isoformat(timespec='seconds')}", ""]
    checks: list[tuple[str, bool, str]] = []

    with tempfile.TemporaryDirectory(prefix="sif-api-anything-") as tmp:
        tmp = Path(tmp)
        (tmp / NOMBRE_REPO).symlink_to(RAIZ / "docs")
        servidor = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Silencioso, directory=str(tmp)))
        puerto = servidor.server_address[1]
        hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()
        base = f"http://127.0.0.1:{puerto}/{NOMBRE_REPO}"
        try:
            spec = B.construir(base)
            for op in spec["operations"]:
                op["request"]["url"] = op["request"]["url"].replace("{base}", base)
                op["trigger"]["url"] = op["trigger"]["url"].replace("{base}", base)
            home = tmp / "home"
            (home / "sites").mkdir(parents=True)
            (home / "sites" / "sif-chile.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
            (home / "sites" / "sif-chile.md").write_text(B.notas(base), encoding="utf-8")
            env = {**os.environ, "API_ANYTHING_HOME": str(home)}

            catalog = correr(cli, env, "call", "sif-chile", "catalog", "--max-tier", "1",
                             "--fields", "id,estado,filas", "--max-chars", "1200")
            ok = catalog.get("ok") and isinstance(catalog.get("data"), list) and len(catalog["data"]) > 0
            checks.append(("call catalog", ok, f"{len(catalog.get('data', []))} objetos en la primera vista"))

            # Vista de resultado: si la respuesta se recortó, `result` continúa sin volver al sitio.
            more = catalog.get("more") or {}
            if more.get("resultId"):
                resto = correr(cli, env, "result", more["resultId"], "--offset", str(more.get("offset", 0)),
                               "--fields", "id,estado,filas", "--max-chars", "1200")
                checks.append(("result (vista paginada)", bool(resto.get("ok")),
                               f"offset {more.get('offset')} → {len(resto.get('data', []))} objetos más, sin red"))
            else:
                checks.append(("result (vista paginada)", False, "catalog no quedó recortado; no hay resultId"))

            esquema = correr(cli, env, "call", "sif-chile", "schema", "id=bancos_balance", "--max-tier", "1",
                             "--fields", "id,primaryKey", "--max-chars", "600")
            checks.append(("call schema", bool(esquema.get("ok")) and esquema.get("data", {}).get("id") == "bancos_balance",
                           f"primaryKey={esquema.get('data', {}).get('primaryKey')}"))

            malo = correr(cli, env, "call", "sif-chile", "schema", "id=no_existe_este_objeto", "--max-tier", "1")
            checks.append(("id inexistente → input", malo.get("class") == "input" and malo.get("retry") == "after_fix",
                           f"class={malo.get('class')} retry={malo.get('retry')}"))

            consultas = json.loads((RAIZ / "docs" / "api" / "v2" / "queries.json").read_text(encoding="utf-8"))
            qid = consultas["consultas"][0]["id"]
            resultado = correr(cli, env, "call", "sif-chile", "resultado", f"id={qid}", "--max-tier", "1",
                               "--fields", "id,filas,columnas", "--max-chars", "800")
            checks.append(("call resultado", bool(resultado.get("ok")) and resultado.get("data", {}).get("id") == qid,
                           f"{resultado.get('data', {}).get('filas')} filas precalculadas"))

            verify = correr(cli, env, "verify", "sif-chile", "--strict", timeout=300)
            counts = verify.get("counts", {})
            checks.append(("verify --strict", bool(verify.get("ok")) and counts.get("fail", 0) == 0,
                           f"pass={counts.get('pass')} fail={counts.get('fail')} inconclusive={counts.get('inconclusive')}"))
        finally:
            servidor.shutdown()
            servidor.server_close()

    for nombre, ok, detalle in checks:
        linea = f"{'OK   ' if ok else 'FALLA'} {nombre} · {detalle}"
        print(linea)
        lineas.append(linea)
    fallos = [c for c in checks if not c[1]]
    veredicto = ("api-anything: spec del contrato verificada contra espejo local (6 operaciones, tier 1)"
                 if not fallos else f"api-anything: {len(fallos)} comprobación(es) fallaron")
    print(veredicto)
    lineas += ["", veredicto]
    LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Evidencia: {LOG.relative_to(RAIZ)}")
    return 1 if (fallos and args.check) else 0


if __name__ == "__main__":
    raise SystemExit(main())

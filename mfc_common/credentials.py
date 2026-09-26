"""
Credenciales para APIs externas (BCCh SIETE). NUNCA se escriben en código.

Orden de resolución:
  1. Variables de entorno BCCH_USER / BCCH_PASS.
  2. Archivo .env en la raíz del repo (git-ignorado), formato KEY=VALUE.

Uso:
    from mfc_common.credentials import bcch_credentials
    email, password = bcch_credentials()
"""
import os

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_dotenv(path=os.path.join(_REPO_ROOT, ".env")):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def bcch_credentials():
    _load_dotenv()
    user, pw = os.environ.get("BCCH_USER"), os.environ.get("BCCH_PASS")
    if not user or not pw:
        raise RuntimeError(
            "Faltan credenciales BCCh. Define BCCH_USER y BCCH_PASS como variables de entorno "
            "o en un archivo .env en la raíz (ver .env.example). Nunca las escribas en el código."
        )
    return user, pw

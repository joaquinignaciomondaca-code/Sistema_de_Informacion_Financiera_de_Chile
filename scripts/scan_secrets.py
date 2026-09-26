"""
Escaneo de secretos en el repositorio (rápido, sin dependencias). Falla (exit 1) si encuentra
credenciales hardcodeadas. Se ejecuta en CI y puede usarse como pre-commit:
    python scripts/scan_secrets.py
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "outputs", "inputs", "partitions"}
EXTS = {".py", ".js", ".mjs", ".ts", ".tsx", ".json", ".md", ".bat", ".sh", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".txt"}
PATTERNS = [
    re.compile(r"""(PASS(WORD)?|PWD|SECRET|TOKEN|API_?KEY)\w*\s*[=:]\s*['"][^'"\s]{6,}['"]""", re.I),
    re.compile(r"""Siete\(\s*['"][^'"]+['"]\s*,\s*['"][^'"]+['"]"""),
    re.compile(r"""[\w.+-]+@[\w-]+\.[\w.]+['"]\s*,\s*['"][^'"]{6,}['"]"""),  # ("correo", "clave")
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
]
ALLOW = ("os.environ", "getenv", ".env.example", "BCCH_PASS=tu_", "<contraseña", "PATTERNS", "re.compile")

hits = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    for fn in fns:
        if os.path.splitext(fn)[1] not in EXTS or fn == os.path.basename(__file__):
            continue
        p = os.path.join(dp, fn)
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if len(line) > 2000 or any(a in line for a in ALLOW):
                        continue
                    if any(pt.search(line) for pt in PATTERNS):
                        hits.append(f"{os.path.relpath(p, ROOT)}:{i}: {line.strip()[:120]}")
        except OSError:
            pass
if hits:
    print("POSIBLES SECRETOS:")
    print("\n".join(hits))
    sys.exit(1)
print("scan_secrets: sin hallazgos")

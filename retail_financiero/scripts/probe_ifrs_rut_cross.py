"""Sonda (sin publicación): cruza los RUT del TXT IFRS CMF con el maestro retail.

Descarga ver_archivo.php?inicio=P&termino=P (TXT o ZIP con TXT, separado por ';'),
lista RUT únicos con razón social, y marca:
  - EN_MAESTRO: RUT presente en docs/outputs/retail_financiero/retail_financiero_maestro.json
  - CANDIDATO: razón social con palabras clave de crédito/retail
Emite resultados como anotaciones ::warning (títulos IFRS*) y un CSV en out/.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PERIOD = sys.argv[1] if len(sys.argv) > 1 else "202606"
URL = f"https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={PERIOD}&termino={PERIOD}"
KEYWORDS = [
    "CARD", "TARJET", "CREDIT", "CREDITO", "FINANC", "RETAIL", "COMERCIAL", "COFISA", "TRICARD",
    "MULTICENTRO", "UNICARD", "FAMILY", "CAR S", "ABCDIN", "AD RETAIL", "POLAR", "CORONA", "HITES",
    "RIPLEY", "FALABELLA", "CENCOSUD", "TRICOT", "PROMOTORA", "CMR", "SERVICIOS FINANC", "LEASING",
    "FACTORING", "INVERSIONES LP", "SMU", "WALMART", "LIDER", "EASY", "SODIMAC", "PARIS", "CONSORCIO",
]
CHUNK = 3900


def norm(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()


def annotate(title: str, text: str) -> None:
    text = text.replace("%", "%25").replace("\r", "")
    for i in range(0, len(text), CHUNK):
        print(f"::warning title={title}::" + text[i:i + CHUNK].replace("\n", "%0A"), flush=True)


def fetch() -> tuple[bytes, str]:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 monitor-financiero-chile"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read(), r.headers.get("Content-Type", "")


def texts(payload: bytes):
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            for n in z.namelist():
                if not n.endswith("/"):
                    yield n, z.read(n)
    else:
        yield "(directo)", payload


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", "replace")


def main() -> None:
    payload, ctype = fetch()
    maestro = json.loads((ROOT / "docs/outputs/retail_financiero/retail_financiero_maestro.json").read_text(encoding="utf-8"))
    maestro_ruts = {int(m["rut"]): m["razon_social"] for m in maestro}
    info = [f"URL={URL}", f"content-type={ctype} bytes={len(payload)}"]
    entities: dict[int, dict] = {}
    rows_by: dict[int, int] = defaultdict(int)
    for name, raw in texts(payload):
        text = decode(raw)
        lines = text.splitlines()
        info.append(f"archivo={name} lineas={len(lines)}")
        info.extend("  muestra: " + l[:300] for l in lines[:4])
        for line in lines:
            parts = [p.strip() for p in line.split(";")]
            if len(parts) < 3:
                continue
            rut_idx = next((i for i, p in enumerate(parts[:4]) if re.fullmatch(r"\d{6,9}", p.replace(".", ""))), None)
            if rut_idx is None:
                continue
            rut = int(parts[rut_idx].replace(".", ""))
            # razón social: primer campo alfabético tras el RUT (saltando DV)
            razon = next((p for p in parts[rut_idx + 1:rut_idx + 4] if re.search(r"[A-Za-z]{3}", p)), "")
            e = entities.setdefault(rut, {"rut": rut, "razon_social": razon, "campos_ejemplo": parts[:10]})
            rows_by[rut] += 1
    annotate("IFRS formato", "\n".join(info))

    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    table = []
    for rut, e in sorted(entities.items()):
        n = norm(e["razon_social"])
        hits = [k for k in KEYWORDS if k in n]
        table.append({"rut": rut, "razon_social": e["razon_social"], "filas": rows_by[rut],
                      "en_maestro": rut in maestro_ruts, "palabras_clave": "|".join(hits)})
    with (out / f"ifrs_{PERIOD}_ruts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]) if table else ["rut"])
        w.writeheader()
        w.writerows(table)

    presentes = [t for t in table if t["en_maestro"]]
    ausentes = [(r, n) for r, n in maestro_ruts.items() if r not in entities]
    candidatos = [t for t in table if not t["en_maestro"] and t["palabras_clave"]]
    annotate("IFRS resumen", "\n".join([
        f"periodo={PERIOD} RUT_unicos={len(table)} maestro={len(maestro_ruts)} maestro_en_IFRS={len(presentes)}",
        "MAESTRO PRESENTES: " + "; ".join(f"{t['rut']} {t['razon_social']} ({t['filas']})" for t in presentes),
        "MAESTRO AUSENTES: " + "; ".join(f"{r} {n}" for r, n in ausentes),
    ]))
    annotate("IFRS candidatos", "\n".join(
        f"{t['rut']};{t['razon_social']};{t['filas']};{t['palabras_clave']}" for t in candidatos) or "ninguno")
    annotate("IFRS todos", "\n".join(f"{t['rut']};{t['razon_social']}" for t in table))


if __name__ == "__main__":
    main()

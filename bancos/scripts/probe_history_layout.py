"""Sonda NO publicadora: formato de ZIP/XLSX CMF bancarios por mes (2022→hoy).

Emite un resumen compacto como anotaciones ::notice (en trozos) para poder
diagnosticar desde fuera de Actions qué meses traen modelos de cuentas,
archivos B1/B2/R1 y las hojas del Excel que exige el publicador.
"""
from __future__ import annotations

import argparse
import re
import zipfile
from collections import Counter
from io import BytesIO

from bancos.scripts.inspect_cmf_bank_sample import MAX_FILE, XLSX_INDEX, ZIP_INDEX, fetch, find_source
from bancos.scripts.publish_cmf_bank_period import next_month

CHUNK = 2800
MEMBER = re.compile(r"(?:^|/)([brc])([12])(20\d{2})(\d{2})(\d{3})\.txt$", re.I)


def probe(period: str) -> str:
    parts = [period]
    try:
        url, _ = find_source(ZIP_INDEX, period, ".zip")
        blob = fetch(url, MAX_FILE)
        with zipfile.ZipFile(BytesIO(blob)) as z:
            names = [i.filename for i in z.infolist() if not i.is_dir()]
            kinds = Counter()
            other_period = 0
            sample_b1 = None
            for n in names:
                m = MEMBER.search(n)
                if m:
                    kinds[(m.group(1) + m.group(2)).upper()] += 1
                    if f"{m.group(3)}-{m.group(4)}" != period:
                        other_period += 1
                    if sample_b1 is None and m.group(1).lower() == "b" and m.group(2) == "1":
                        sample_b1 = n
            meta = sorted({n.rsplit("/", 1)[-1] for n in names if "modelo" in n.lower() or "metadata" in n.lower()})
            parts.append(f"zip={len(blob)//1000}KB n={len(names)} {dict(kinds)} otroPeriodo={other_period}")
            parts.append(f"meta={meta[:6]}")
            unmatched = [n for n in names if not MEMBER.search(n) and n not in meta][:3]
            if unmatched:
                parts.append(f"otros={unmatched}")
            if sample_b1:
                lines = z.read(sample_b1).decode("latin-1", "replace").splitlines()[:3]
                parts.append(f"b1[{sample_b1.rsplit('/',1)[-1]}]={[l[:60] for l in lines]}")
    except Exception as exc:  # noqa: BLE001
        parts.append(f"ZIP_ERR={type(exc).__name__}:{str(exc)[:120]}")
    try:
        url, _ = find_source(XLSX_INDEX, period, ".xlsx")
        blob = fetch(url, MAX_FILE)
        from openpyxl import load_workbook
        wb = load_workbook(BytesIO(blob), read_only=True)
        parts.append(f"xlsx={[ws.title for ws in wb.worksheets][:8]}")
        wb.close()
    except Exception as exc:  # noqa: BLE001
        parts.append(f"XLSX_ERR={type(exc).__name__}:{str(exc)[:120]}")
    return " | ".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2022-01")
    ap.add_argument("--hasta", default="2026-07")
    ap.add_argument("--paso", type=int, default=1)
    a = ap.parse_args()
    lines, p = [], a.desde
    while p <= a.hasta:
        lines.append(probe(p))
        print(lines[-1], flush=True)
        for _ in range(a.paso):
            p = next_month(p)
    text = "\n".join(lines).replace("%", "%25").replace("\r", "")
    chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)][:10]
    for i, c in enumerate(chunks, 1):
        print(f"::warning title=HIST {i}/{len(chunks)}::" + c.replace("\n", "%0A"), flush=True)


if __name__ == "__main__":
    main()

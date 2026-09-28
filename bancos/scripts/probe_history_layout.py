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


def dump_models(period: str) -> str:
    url, _ = find_source(ZIP_INDEX, period, ".zip")
    blob = fetch(url, MAX_FILE)
    out = [period]
    with zipfile.ZipFile(BytesIO(blob)) as z:
        out.append("NO_DATOS=" + repr([i.filename for i in z.infolist() if not MEMBER.search(i.filename)][:25]))
        for info in z.infolist():
            low = info.filename.lower()
            base = low.rsplit("/", 1)[-1]
            want = ("mb1" in base or "mr1" in base or "plan_de_cuentas" in base) and not MEMBER.search(info.filename)
            m = MEMBER.search(info.filename)
            if m and m.group(1).lower() == "r" and m.group(5) == "001":
                want = True
            if want:
                raw = z.read(info)
                enc = "utf8" if not raw.startswith(b"\xef\xbb\xbf") else "utf8-bom"
                try:
                    raw.decode("utf-8")
                except UnicodeDecodeError:
                    enc = "latin1"
                lines = raw.decode("latin-1", "replace").splitlines()
                if "leame" in base:
                    sel = [l for l in lines if l.strip()][:45]
                elif "plan_de_cuentas" in base:
                    import collections
                    heads = collections.Counter(l.split("\t")[0][:1] for l in lines[1:] if l.strip())
                    sel = lines[:12] + ["…"] + lines[-4:] + [f"primer_digito={dict(heads)}", f"cols={collections.Counter(len(l.split(chr(9))) for l in lines)}"]
                elif base.startswith("modelo"):
                    sel = lines[3:16] + ["…"] + lines[-3:]
                else:
                    sel = lines[:3]
                out.append(f"[{info.filename} enc={enc} n={len(lines)}] " + " ¶ ".join(repr(l[:100]) for l in sel))
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2022-01")
    ap.add_argument("--hasta", default="2026-07")
    ap.add_argument("--paso", type=int, default=1)
    ap.add_argument("--xlsx", default="", help="PERIODO:NOMBRE para volcar filas del Excel")
    ap.add_argument("--modelos", default="", help="Períodos separados por coma: volcar modelos de cuentas")
    a = ap.parse_args()
    if a.xlsx:
        per, name = a.xlsx.split(":", 1)
        text = dump_xlsx_rows(per, name).replace("%", "%25")
        print(text)
        for i in range(0, min(len(text), 28000), CHUNK):
            print(f"::warning title=XLSX::" + text[i:i + CHUNK].replace("\n", "%0A"), flush=True)
        return
    if a.modelos:
        lines = []
        for per in a.modelos.split(","):
            try:
                lines.append(dump_models(per.strip()))
            except Exception as exc:  # noqa: BLE001
                lines.append(f"{per} ERR {exc}")
            print(lines[-1], flush=True)
        text = "\n".join(lines).replace("%", "%25").replace("\r", "")
        chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)][:10]
        for i, c in enumerate(chunks, 1):
            print(f"::warning title=MOD {i}/{len(chunks)}::" + c.replace("\n", "%0A"), flush=True)
        return
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


def dump_xlsx_rows(period: str, needle: str) -> str:
    """Filas del Excel CMF que contienen `needle` (hojas de balance y resultados)."""
    from openpyxl import load_workbook
    from bancos.scripts.extract_cmf_bank_lines import normalize_name
    url, _ = find_source(XLSX_INDEX, period, ".xlsx")
    wb = load_workbook(BytesIO(fetch(url, MAX_FILE)), read_only=True, data_only=True)
    out = [period]
    for ws in wb.worksheets:
        if "bancos" not in ws.title.lower():
            continue
        for n, row in enumerate(ws.iter_rows(values_only=True), start=1):
            vals = [v for v in row if v is not None]
            if n <= 6 or any(normalize_name(needle) in normalize_name(v) for v in vals if isinstance(v, str)):
                out.append(f"{ws.title.strip()}#{n}: {vals[:10]}")
    wb.close()
    return "\n".join(out)


if __name__ == "__main__":
    main()



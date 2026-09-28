"""Sonda (sin publicación): estructura del Reporte Financiero de Cooperativas CMF.

Uso:  python -m cooperativas.scripts.probe_coop_layout index
      python -m cooperativas.scripts.probe_coop_layout xlsx 2026-07
"""
from __future__ import annotations

import re
import sys
from io import BytesIO

from bancos.scripts.inspect_cmf_bank_sample import MAX_FILE, MAX_PAGE, AnchorParser, fetch, find_source

INDEX = "https://www.cmfchile.cl/portal/estadisticas/626/w4-propertyvalue-28918.html"
CHUNK = 3900


def annotate(title: str, text: str, limit: int = 9) -> None:
    text = text.replace("%", "%25").replace("\r", "")
    parts = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)][:limit]
    for part in parts:
        print(f"::warning title={title}::" + part.replace("\n", "%0A"), flush=True)


def index() -> None:
    page = fetch(INDEX, MAX_PAGE).decode("utf-8", "replace")
    p = AnchorParser(); p.feed(page); p.close()
    rows = []
    for item in p.links:
        text = re.sub(r"\s+", " ", item["text"]).strip()
        href = item["href"]
        if "recurso" in href or "w4-article" in href:
            rows.append(f"{text[:80]} | {href[-60:]}")
    more = re.findall(r"[?&](?:page|pagina|p)=\d+", page)[:5]
    annotate("COOP index", f"links={len(rows)} paginacion={more}\n" + "\n".join(rows[:60]) + "\n...\n" + "\n".join(rows[-30:]))


def xlsx(period: str) -> None:
    from openpyxl import load_workbook
    url, label = find_source(INDEX, period, ".xlsx")
    wb = load_workbook(BytesIO(fetch(url, MAX_FILE)), read_only=True, data_only=True)
    out = [f"{period} {url} hojas={wb.sheetnames}"]
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        out.append(f"=== {ws.title} filas={len(rows)} cols={max((len(r) for r in rows), default=0)}")
        for n, r in enumerate(rows, 1):
            vals = [v for v in r if v is not None]
            if not vals:
                continue
            if n <= 12 or any(isinstance(v, str) and re.search(r"coopeuch|oriencoop|oriente|total|sistema", v, re.I) for v in vals[:3]):
                out.append(f"{n}: {[str(v)[:45] for v in vals[:24]]}")
    annotate(f"COOP {period}", "\n".join(out))


def layouts(periods: list[str]) -> None:
    """Resumen compacto por período: hojas, y cabeceras de las hojas por cooperativa."""
    import xlrd  # noqa: F401  (xls antiguos)
    out = []
    for period in periods:
      try:
        _layout_one(period, out)
      except Exception:
        import traceback
        out.append(f"## {period} EXC " + traceback.format_exc()[-1200:])
    annotate("COOP layouts", "\n".join(out))


def _layout_one(period: str, out: list) -> None:
    if True:
        try:
            url, _ = find_source(INDEX, period, ".xlsx")
        except Exception:
            try:
                url, _ = find_source(INDEX, period, ".xls")
            except Exception as exc:
                out.append(f"## {period} ERROR {exc}"[:300]); return
        blob = fetch(url, MAX_FILE)
        out.append(f"## {period} {url.rsplit('/',1)[-1]} bytes={len(blob)}")
        sheets = []
        if url.split("?")[0].endswith(".xlsx"):
            from openpyxl import load_workbook
            wb = load_workbook(BytesIO(blob), read_only=True, data_only=True)
            for ws in wb.worksheets:
                sheets.append((ws.title, [list(r) for r in ws.iter_rows(values_only=True)]))
        else:
            import xlrd
            bk = xlrd.open_workbook(file_contents=blob)
            for sh in bk.sheets():
                sheets.append((sh.name, [sh.row_values(i) for i in range(sh.nrows)]))
        out.append("hojas=" + str([t for t, _ in sheets]))
        for title, rows in sheets:
            if not re.search(r"coop|anexo|activ|pasiv|result", title, re.I) or re.search(r"indic|defin|sistema", title, re.I):
                continue
            first = None
            for n, r in enumerate(rows, 1):
                vals = [v for v in r if v not in (None, "")]
                if vals and isinstance(vals[0], str) and re.search(r"coopeuch", vals[0], re.I):
                    first = n; break
            out.append(f"= {title} filas={len(rows)} primera_coop={first}")
            if first:
                for r in rows[max(0, first - 9):first]:
                    vals = [str(v)[:28] for v in r if v not in (None, "")]
                    if vals:
                        out.append("  " + " | ".join(vals[:22]))
                out.append("  >> " + " | ".join(str(v)[:12] for v in rows[first - 1] if v not in (None, ""))[:400])



def cells(period: str, sheet_pat: str) -> None:
    from cooperativas.scripts.extract_cmf_coop_report import discover, read_workbook
    url = discover(fetch(INDEX, MAX_PAGE).decode("utf-8", "replace"))[period]
    wb = read_workbook(fetch(url, MAX_FILE), url)
    name = next(n for n in wb if re.search(sheet_pat, n, re.I))
    out = [f"{period} {name}"]
    for n, r in enumerate(wb[name][:30], 1):
        cells_ = [(i, v) for i, v in enumerate(r) if v not in (None, "")]
        if cells_:
            out.append(f"{n}: n={len(cells_)} " + " ".join(f"[{i}]{str(v)[:18]}" for i, v in cells_[:40]))
    annotate("COOP cells", "\n".join(out))


if __name__ == "__main__":
    if sys.argv[1] == "cells":
        cells(sys.argv[2], sys.argv[3]); raise SystemExit
    if sys.argv[1] == "layouts":
        layouts(sys.argv[2].split(","))
        raise SystemExit
    {"index": lambda: index(), "xlsx": lambda: xlsx(sys.argv[2])}[sys.argv[1]]()

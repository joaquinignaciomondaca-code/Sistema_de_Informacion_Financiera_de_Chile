"""Resumen legible del cotejo ZIP CMF para las anotaciones del run.

No publica ni transforma datos: sólo lee el JSON de evidencia del cotejo y
emite una anotación `::notice::` **por mes** con el resultado de comparar la
suma de columnas del rubro contra la serie legacy. Sirve para revisar una
corrida sin descargar el artefacto, que conserva los montos crudos completos.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / ".local-data/review/bancos/repo_zip_audit.json"
LIMIT = 3500


def side_status(data: dict, legacy: float | None) -> str:
    """`✓` si la suma de columnas iguala la referencia; `✗` con ambos valores."""
    if not isinstance(data, dict) or data.get("estado"):
        return "sin_cuenta"
    total = data.get("suma_columnas")
    if total is None or legacy is None:
        return "sin_referencia"
    try:
        equal = Decimal(total) == Decimal(str(legacy))
    except InvalidOperation:
        return "ilegible"
    return "✓" if equal else f"✗({total}≠{legacy})"


def summarize_month(month: dict, limit: int = LIMIT) -> str:
    banks = month.get("bancos", [])
    compared = [b for b in banks if b.get("referencia_legacy_mm_clp") is not None]
    details = []
    hits = 0
    for bank in compared:
        sides = bank.get("hipotesis_escala", {})
        legacy = bank["referencia_legacy_mm_clp"]
        left = side_status(sides.get("activo", {}), legacy.get("activo"))
        right = side_status(sides.get("pasivo", {}), legacy.get("pasivo"))
        hits += left == "✓" and right == "✓"
        details.append(f"{bank.get('codigo_banco')} a{left} p{right}")
    missing = [b["codigo_banco"] for b in banks
               if all(s.get("estado") for s in b.get("hipotesis_escala", {}).values())]
    head = (f"{month.get('periodo')} bancos={len(banks)} cotejados={len(compared)} "
            f"ambos_lados_ok={hits} cuentas={month.get('candidatos_del_script_v2')} "
            f"suma_columnas=MM_CLP_sin_divisor sha={str(month.get('sha256_zip'))[:12]} "
            f"adv={month.get('advertencia')} sin_cuenta={missing}")
    return (head + " || " + " ".join(details))[:limit]


def summarize(report: dict, limit: int = LIMIT) -> str:
    if report.get("estado") == "cotejo_incompleto_no_publicado":
        return f"FALLO en {report.get('periodo_fallido')}: {report.get('error')}"[:limit]
    if "periodos" in report and report["periodos"]:
        return " || ".join(summarize_month(m, limit) for m in report["periodos"])
    return summarize_month(report, limit)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--glob", default="repo_zip_audit*.json",
                        help="Todos los meses calibrados del directorio de evidencia")
    args = parser.parse_args()
    if args.report.exists():
        reports = [args.report]
    else:
        reports = sorted(args.report.parent.glob(args.glob))
    if not reports:
        print("Sin JSON de evidencia; revisar el paso de cotejo", file=sys.stderr)
        return 0
    months = []
    for path in reports:
        data = json.loads(path.read_text(encoding="utf-8"))
        months.extend(data.get("periodos") or [data])
    for month in months:
        text = summarize_month(month)
        print(text)
        print(f"::notice title=Cotejo REPO ZIP CMF {month.get('periodo')} (sin publicar)::{text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

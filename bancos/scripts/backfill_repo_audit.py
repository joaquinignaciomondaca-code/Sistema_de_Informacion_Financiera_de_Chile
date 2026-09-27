"""Barrido histórico de ZIP CMF para auditoría, sin publicación ni checkpoint.

Descubre el índice una sola vez, coteja únicamente meses presentes en el REPO
legacy y guarda un resumen por año tras cada descarga. No cambia docs/outputs;
no usa el checkpoint del diagnóstico diario ni fuerza una escala contable.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from bancos.scripts import audit_repos_zip_cmf as audit
from bancos.scripts import probe_repos_zip_cmf as probe

OUT = probe.ROOT / ".local-data/review/bancos/historico"


def comparisons(month: dict) -> dict:
    """Verifica la hipótesis específica por plan; nunca confunde ausencia con 0."""
    period = month["periodo"]
    divisor = Decimal(1 if period < "2022-01" else 1000000)
    mismatches = []
    checked = 0
    for bank in month["bancos"]:
        reference = bank["referencia_legacy_mm_clp"]
        if reference is None:
            continue
        for side in ("activo", "pasivo"):
            data = bank["hipotesis_escala"].get(side, {})
            raw = data.get("suma_columnas")
            try:
                if data.get("estado") or raw is None:
                    raise ValueError(data.get("estado", "sin_suma"))
                calc = (Decimal(raw) / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                expected = Decimal(str(reference[side]))
                if calc != expected:
                    raise ValueError(f"valor={calc}, referencia={expected}")
                checked += 1
            except (ValueError, InvalidOperation, KeyError) as exc:
                mismatches.append({"banco": bank["codigo_banco"], "lado": side,
                                   "cuenta": data.get("cuenta"), "crudo": raw,
                                   "referencia": reference.get(side), "causa": str(exc)})
    missing_legacy = sorted(set(bank["codigo_banco"] for bank in month["bancos"]
                                if bank["referencia_legacy_mm_clp"] is None))
    return {"periodo": period, "url_zip": month.get("url_zip"),
            "sha256_zip": month["sha256_zip"], "divisor_hipotesis": int(divisor),
            "bancos_zip": len(month["bancos"]), "bancos_sin_fila_legacy": missing_legacy,
            "lados_cotejados": checked, "discrepancias": mismatches,
            "advertencia": month["advertencia"]}


def rollup(rows: list[dict]) -> dict:
    return {"meses_cotejados": len(rows), "lados_cotejados": sum(r["lados_cotejados"] for r in rows),
            "discrepancias": sum(len(r["discrepancias"]) for r in rows),
            "detalle_discrepancias": [{"periodo": r["periodo"], **m} for r in rows for m in r["discrepancias"]]}


def save(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(output: Path = OUT, from_year: int = 2008, through_year: int = 2026) -> dict:
    if not 2001 <= from_year <= through_year <= date.today().year:
        raise ValueError("Rango de años inválido")
    found, unresolved = probe.resolve_links()
    baseline = json.loads(probe.LEGACY.read_text(encoding="utf-8"))
    period_rows = {}
    for row in baseline:
        period_rows.setdefault(row["periodo"], {})[row["codigo_institucion"]] = {
            "activo": row["repo_activo_mm_clp"], "pasivo": row["repo_pasivo_mm_clp"]}
    periods = sorted(p for p in period_rows if from_year <= int(p[:4]) <= through_year)
    if not periods:
        raise ValueError("Rango sin filas legacy")
    unavailable = [p for p in periods if p not in found or p in unresolved]
    collected: list[dict] = []
    errors: list[dict] = []
    for p in periods:
        year_path = output / f"{p[:4]}.json"
        if p in unavailable:
            issue = {"periodo": p, "causa": "ZIP ambiguo" if p in unresolved else "ZIP ausente"}
            errors.append(issue)
            print(f"{p} pendiente: {issue['causa']}", flush=True)
            continue
        try:
            legacy = {(p, code): values for code, values in period_rows[p].items()}
            month = audit.inspect_all(probe.read_public(found[p], probe.MAX_ZIP), p, found[p], legacy)
            result = comparisons(month)
            collected.append(result)
            # Guardar después de cada mes: conserva evidencia parcial ante
            # errores de red y evita que un timeout pierda años ya cotejados.
            by_year = [r for r in collected if r["periodo"][:4] == p[:4]]
            save(year_path, {"estado": "auditoria_historica_parcial_no_publicada",
                             "fuente": probe.INDEX, "resumen": rollup(by_year), "meses": by_year})
            print(f"{p} cotejado: {result['lados_cotejados']} lados, "
                  f"{len(result['discrepancias'])} discrepancias", flush=True)
        except (ValueError, RuntimeError, OSError) as exc:
            issue = {"periodo": p, "causa": str(exc)}
            errors.append(issue)
            print(f"{p} pendiente: {issue['causa']}", flush=True)
            continue
    summary = rollup(collected)
    doc = {"estado": "auditoria_historica_incompleta_no_publicada" if errors else
                     "auditoria_historica_exploratoria_no_publicada",
           "fuente": probe.INDEX, "primer_periodo": periods[0], "ultimo_periodo": periods[-1],
           "meses_esperados": len(periods), "resumen": summary, "errores": errors,
           "nota": "Coincidencia con legacy no certifica rubro contable, columnas, RUT ni cobertura del universo."}
    save(output / "resumen.json", doc)
    return doc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-year", type=int, default=2008)
    parser.add_argument("--through-year", type=int, default=2026)
    args = parser.parse_args()
    try:
        result = run(from_year=args.from_year, through_year=args.through_year)
    except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"Barrido histórico incompleto: {exc}", file=sys.stderr)
        return 1
    summary = result["resumen"]
    print(f"::notice title=REPO histórico sin publicar::{result['estado']} "
          f"meses={summary['meses_cotejados']}/{result['meses_esperados']} "
          f"lados={summary['lados_cotejados']} discrepancias={summary['discrepancias']} "
          f"pendientes={len(result['errores'])}")
    for issue in result["errores"][:20]:
        print(f"::warning title=REPO mes pendiente::{issue}")
    if summary["detalle_discrepancias"]:
        for item in summary["detalle_discrepancias"][:20]:
            print(f"::warning title=REPO discrepancia histórica::{item}")
    return 1 if result["errores"] or summary["discrepancias"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

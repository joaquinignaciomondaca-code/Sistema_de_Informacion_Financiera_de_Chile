"""Resumen legible del cotejo ZIP CMF para la anotación del run.

No publica ni transforma datos: sólo lee el JSON de evidencia del cotejo y
emite una línea `::notice::` de GitHub Actions con conteos y montos **crudos**
ya conservados, para poder revisar una corrida sin descargar el artefacto.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / ".local-data/review/bancos/repo_zip_audit.json"
LIMIT = 6000
BANKS_PER_MONTH = 8


def last_error(report: dict) -> str:
    return f"FALLO en {report.get('periodo_fallido')}: {report.get('error')}"


def summarize(report: dict, limit: int = LIMIT) -> str:
    if report.get("estado") == "cotejo_incompleto_no_publicado":
        return last_error(report)[:limit]
    lines = [f"estado={report.get('estado')} meses={len(report.get('periodos', []))} (evidencia no publicada)"]
    for month in report.get("periodos", []):
        banks = month.get("bancos", [])
        with_candidates = sum(
            any(side.get("campos_crudos") for side in bank.get("hipotesis_escala", {}).values())
            for bank in banks
        )
        lines.append(
            f"{month.get('periodo')}: bancos={len(banks)} con_cuentas_candidatas={with_candidates} "
            f"con_referencia_legacy={month.get('filas_con_referencia_legacy')} "
            f"coincidencias={month.get('filas_con_alguna_coincidencia')} "
            f"cuentas_pista={month.get('candidatos_del_script_v2')} "
            f"sha256={str(month.get('sha256_zip'))[:12]} adv={month.get('advertencia')}"
        )
        for bank in banks[:BANKS_PER_MONTH]:
            parts = []
            for side, data in bank.get("hipotesis_escala", {}).items():
                matches = data.get("coincidencias_legacy") or []
                hit = f" MATCH {matches}" if matches else ""
                parts.append(
                    f"{side}({data.get('cuenta')})={data.get('campos_crudos') or data.get('estado')}"
                    f" suma={data.get('suma_columnas')} MM={data.get('suma_con_divisor')}{hit}"
                )
            lines.append(f"  {bank.get('codigo_banco')} legacy={bank.get('referencia_legacy_mm_clp')} " + " ".join(parts))
    return "\n".join(lines)[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    if not args.report.exists():
        print("Sin JSON de evidencia; revisar el paso de cotejo", file=sys.stderr)
        return 0
    text = summarize(json.loads(args.report.read_text(encoding="utf-8")))
    body = text.replace("\n", " | ")
    print(text)
    print(f"::notice title=Cotejo REPO ZIP CMF (sin publicar)::{body}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

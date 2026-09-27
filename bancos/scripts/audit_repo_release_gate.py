"""Puerta de aprobación de la tabla REPO legacy: sólo lee JSON, nunca publica.

No confundir cotejo numérico contra ZIP CMF con certificación del dataset entero.
La puerta permanece cerrada mientras haya metadatos registrales/semánticos
materialmente incorrectos o sin sustento. La ausencia de alertas aquí tampoco
certifica por sí sola la identidad legal o la completitud de instituciones.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

LEGACY = Path(__file__).resolve().parents[2] / "docs/outputs/bancos/bancos_repos_saldos_series.json"
AGGREGATES = {"900", "950", "960", "970", "980", "998", "999"}
FOREIGN_AFFILIATES = {"816", "916", "927"}


def audit(rows: list[dict]) -> dict:
    by_rut: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    by_period: dict[str, set[str]] = defaultdict(set)
    aggregate_rows = []
    foreign_rows = []
    mistaken_flow = []
    malformed = []
    for index, row in enumerate(rows):
        try:
            code, period, rut = row["codigo_institucion"], row["periodo"], row["rut"]
            active, passive = row["repo_activo_mm_usd"], row["repo_pasivo_mm_usd"]
            flow = row["total_transado_mm_usd"]
        except KeyError as exc:
            malformed.append({"fila": index, "motivo": f"falta {exc.args[0]}"})
            continue
        by_rut[rut][period].add(code)
        by_period[period].add(code)
        if code in AGGREGATES:
            aggregate_rows.append({"codigo": code, "periodo": period})
        if code in FOREIGN_AFFILIATES:
            foreign_rows.append({"codigo": code, "periodo": period})
        # Total transado es un flujo mensual de operaciones; esta columna es
        # una suma de posiciones de cierre (dos stocks), no una medida de flujo.
        if abs((active + passive) - flow) > 0.021:
            malformed.append({"fila": index, "motivo": "total_transado no equivale a suma de saldos"})
        else:
            mistaken_flow.append(row.get("id_repo", f"fila {index}"))
    overlaps = [
        {"rut": rut, "periodo": period, "codigos": sorted(codes)}
        for rut, periods in by_rut.items() for period, codes in periods.items()
        if len(codes) > 1 and rut not in {"", None}
    ]
    overlaps.sort(key=lambda x: (x["rut"], x["periodo"]))
    problems = []
    if overlaps:
        problems.append("Un RUT identifica dos o más códigos distintos en el mismo mes")
    if aggregate_rows:
        problems.append("Totales y subtotales se mezclan con bancos en la tabla publicada")
    if foreign_rows:
        problems.append("Filiales extranjeras se mezclan con bancos establecidos en Chile")
    if mistaken_flow:
        problems.append("total_transado_mm_usd es suma de saldos, no flujo negociado")
    if malformed:
        problems.append("Filas sin campos obligatorios o aritmética inconsistente")
    # Estos controles necesitan fuentes externas y no se deducen de la serie.
    pending = ["Identidad legal, nombre y vigencia por código-mes con registro oficial CMF",
               "Naturaleza del rubro: incluye préstamos de valores; especificación B1 y consolidación",
               "Cobertura del universo CMF, revisiones, ceros versus filas ausentes",
               "Procedencia del Excel original y extractor incremental de publicación auditado"]
    # Un control automatizado sobre el mismo dataset no puede emitir por sí
    # solo una certificación contable o registral; requiere fuentes externas.
    return {"estado": "NO_APROBADO",
            "filas": len(rows), "meses": len(by_period),
            "rut_simultaneo_conflictivo": {"meses_conflictivos": len(overlaps), "ejemplos": overlaps[:5]},
            "agregados": {"filas": len(aggregate_rows), "codigos": sorted({r["codigo"] for r in aggregate_rows})},
            "filiales_extranjeras": {"filas": len(foreign_rows), "codigos": sorted({r["codigo"] for r in foreign_rows})},
            "columna_transado_suma_saldos": len(mistaken_flow),
            "filas_invalidas": malformed[:20], "bloqueos": problems,
            "pendiente_de_validacion_independiente": pending}


def main() -> int:
    report = audit(json.loads(LEGACY.read_text(encoding="utf-8")))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["estado"] != "APROBADO" else 0


if __name__ == "__main__":
    raise SystemExit(main())

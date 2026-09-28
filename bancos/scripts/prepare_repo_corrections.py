"""Prepara (NO publica) una propuesta de saldos bancarios sin metadatos engañosos.

La referencia legacy conserva saldos cotejados numéricamente, pero no certifica
identidad legal por mes ni volumen negociado. El resultado se guarda solamente
en .local-data/review/ (ignorado por git). No se imputan bancos ausentes ni ceros.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from bancos.scripts.audit_repo_release_gate import AGGREGATES, FOREIGN_AFFILIATES, LEGACY

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / ".local-data/review/bancos/repo_correcciones"
# Los nombres y RUT provienen de un maestro actual aplicado retrospectivamente;
# NO son identificadores validados código-mes. El 'transado' es suma de stocks.
UNTRUSTED = {"rut", "razon_social", "nombre_fantasia", "total_transado_mm_usd"}
# Los códigos de filiales extranjeras se mantienen separados para revisión.


def split_legacy(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    banks, aggregates, foreign_affiliates = [], [], []
    seen = set()
    for row in rows:
        code = row["codigo_institucion"]
        key = (row["periodo"], code)
        if key in seen:
            raise ValueError(f"Código y mes repetidos: {key}")
        seen.add(key)
        if row["id_repo"] != f"{code}_{row['periodo']}":
            raise ValueError(f"Identificador incongruente: {key}")
        corrected = {k: v for k, v in row.items() if k not in UNTRUSTED}
        (aggregates if code in AGGREGATES else
         foreign_affiliates if code in FOREIGN_AFFILIATES else banks).append(corrected)
    assert len(banks) + len(aggregates) + len(foreign_affiliates) == len(rows)
    return banks, aggregates, foreign_affiliates


def prepare(source: Path = LEGACY, output: Path = DEFAULT_OUT) -> dict:
    rows = json.loads(source.read_text(encoding="utf-8-sig"))
    banks, aggregates, foreign_affiliates = split_legacy(rows)
    # Comprobar que el corte sólo retira columnas/segrega filas, jamás altera saldos.
    original = {r["id_repo"]: r for r in rows}
    if len(original) != len(rows):
        raise ValueError("id_repo repetido en la referencia")
    for row in banks + aggregates + foreign_affiliates:
        if row != {k: v for k, v in original[row["id_repo"]].items() if k not in UNTRUSTED}:
            raise ValueError("Saldo modificado inesperadamente")
    output.mkdir(parents=True, exist_ok=True)
    for name, data in (("bancos", banks), ("agregados", aggregates),
                       ("filiales_extranjeras", foreign_affiliates)):
        (output / f"repo_{name}_revision.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"estado": "BORRADOR_NO_PUBLICAR", "fuente": str(source),
               "filas_fuente": len(rows), "bancos_filas": len(banks),
               "agregados_filas": len(aggregates),
               "filiales_extranjeras_filas": len(foreign_affiliates),
               "codigos_agregados": dict(sorted(Counter(r["codigo_institucion"] for r in aggregates).items())),
               "columnas_descartadas": sorted(UNTRUSTED),
               "pendiente": ["confirmar glosas y disposición de columnas TXT por período",
                             "reconstruir identidad código-mes con padrón oficial",
                             "confirmar universo y tratamiento de ausentes",
                             "aprobar extractor incremental y fuente FX"]}
    (output / "dictamen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(prepare(output=args.output), ensure_ascii=False, indent=2))

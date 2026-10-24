#!/usr/bin/env python3
"""Publica Parquet descargables separados para las vistas bancarias B1/B2 y R1.

La fuente CMF consolidada sigue en ``cmf_b1_b2_r1`` (B1+B2+R1). Este generador
materializa el filtro semántico en archivos propios, para que las descargas de
``bancos_balance`` y ``bancos_resultados`` coincidan con las filas anunciadas
por sus vistas y catálogos.

Uso:
    python scripts/build_bancos_vistas.py
    python scripts/build_bancos_vistas.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE = DOCS / "outputs/bancos/cmf_b1_b2_r1/manifest.json"
TARGETS = {
    "bancos_balance": {
        "familias": ["B1", "B2"],
        "directorio": DOCS / "outputs/bancos/balance_b1_b2",
        "manifest": "outputs/bancos/balance_b1_b2/manifest.json",
    },
    "bancos_resultados": {
        "familias": ["R1"],
        "directorio": DOCS / "outputs/bancos/resultados_r1",
        "manifest": "outputs/bancos/resultados_r1/manifest.json",
    },
}


def json_bytes(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def expected_files(view: str, settings: dict, source: dict) -> tuple[dict, dict[str, bytes]]:
    periods = []
    files: dict[str, bytes] = {}
    for period in source.get("periods", []):
        source_rel = period["file"]
        source_path = DOCS / source_rel
        if not source_path.is_file():
            raise SystemExit(f"Falta la partición fuente {source_path.relative_to(ROOT)}")
        source_table = pq.read_table(source_path)
        if "familia_archivo_fuente" not in source_table.column_names:
            raise SystemExit(f"{source_rel} no contiene familia_archivo_fuente")
        familias = pa.array(settings["familias"], type=source_table["familia_archivo_fuente"].type)
        subset = source_table.filter(pc.is_in(source_table["familia_archivo_fuente"], value_set=familias))
        if subset.num_rows == 0:
            raise SystemExit(f"{source_rel}: filtro vacío para {view}")

        relative = f"outputs/bancos/{settings['directorio'].name}/{period['period']}/lineas.parquet"
        target = settings["directorio"] / period["period"] / "lineas.parquet"
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".parquet.tmp", delete=False) as handle:
            temp_path = Path(handle.name)
        try:
            pq.write_table(subset, temp_path, compression="zstd", version="2.6")
            payload = temp_path.read_bytes()
        finally:
            temp_path.unlink(missing_ok=True)
        files[relative] = payload
        periods.append({
            "period": period["period"],
            "file": relative,
            "records": subset.num_rows,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        })

    manifest = {
        "dataset": view,
        "description": ("Particiones Parquet descargables filtradas exclusivamente a las familias "
                        + ", ".join(settings["familias"]) + "."),
        "source_manifest": "outputs/bancos/cmf_b1_b2_r1/manifest.json",
        "familias_archivo_fuente": settings["familias"],
        "updated_at": source.get("updated_at"),
        "periods": periods,
        "files": [period["file"] for period in periods],
        "total_records": sum(period["records"] for period in periods),
        "total_bytes": sum(period["bytes"] for period in periods),
    }
    files[settings["manifest"]] = json_bytes(manifest)
    return manifest, files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validar los Parquet y manifiestos ya generados")
    args = parser.parse_args()
    if not SOURCE.is_file():
        raise SystemExit(f"Falta el manifiesto fuente {SOURCE.relative_to(ROOT)}")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    # Also guard the integration: the published semantic views must read the
    # corresponding filtered manifests and retain their declared family filter.
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import audit_consultas_sugeridas as audit
    declared = {view["name"]: view for view in audit.vistas_semanticas()}
    for view, settings in TARGETS.items():
        actual = declared.get(view, {})
        expected_filter = (
            "familia_archivo_fuente IN ('B1', 'B2')" if view == "bancos_balance"
            else "familia_archivo_fuente = 'R1'"
        )
        if actual.get("manifest") != settings["manifest"] or actual.get("where") != expected_filter:
            raise SystemExit(f"{view}: SEMANTIC_VIEWS debe usar {settings['manifest']} y filtro {expected_filter}")

    expected: dict[str, bytes] = {}
    summaries = []
    for view, settings in TARGETS.items():
        manifest, outputs = expected_files(view, settings, source)
        expected.update(outputs)
        summaries.append(f"{view}: {manifest['total_records']:,} filas / {len(manifest['periods'])} particiones")

    if args.check:
        errors = []
        for relative, contents in expected.items():
            path = DOCS / relative
            if not path.is_file():
                errors.append(f"falta {relative}")
            elif path.read_bytes() != contents:
                errors.append(f"desactualizado {relative}")
        if errors:
            print("VISTAS BANCARIAS: " + "; ".join(errors[:10]))
            print("Ejecuta python scripts/build_bancos_vistas.py")
            return 1
        print("VISTAS BANCARIAS: al día · " + " · ".join(summaries))
        return 0

    for relative, contents in expected.items():
        path = DOCS / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(contents)
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    print("VISTAS BANCARIAS: generadas · " + " · ".join(summaries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

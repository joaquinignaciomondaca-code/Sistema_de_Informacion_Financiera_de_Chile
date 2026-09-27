"""Valida el staging de macro antes de publicar los archivos consumidos por docs/.

Uso: python -m macro.scripts.publish_macro --stage-dir .local-data/macro
No descarga datos ni contacta BCCh. La publicación es explícita.
"""

import argparse
import json
import os
import shutil
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd

from macro.scripts.audit_macro_bcch import run_audit

ROOT = Path(__file__).resolve().parents[2]
NAMES = ("macro_tasas_rendimientos", "macro_divisas_mercado", "macro_precios_actividad")


def validate(stage: Path, published: Path):
    """Verifica que no se publique una descarga vacía, truncada o regresiva."""
    run_audit(str(stage))
    summary = {}
    for name in NAMES:
        parquet = stage / f"{name}.parquet"
        js = stage / f"{name}.json"
        if not js.is_file():
            raise ValueError(f"Falta JSON de {name}")
        df = pd.read_parquet(parquet)
        rows = json.loads(js.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or len(rows) != len(df):
            raise ValueError(f"JSON y Parquet no coinciden en {name}")
        periods = df["periodo"].tolist()
        if [row.get("periodo") for row in rows] != periods:
            raise ValueError(f"Periodos JSON/Parquet distintos en {name}")
        if periods[-1] > date.today().strftime("%Y-%m"):
            raise ValueError(f"Periodo futuro en {name}: {periods[-1]}")
        core = {
            "macro_tasas_rendimientos": "tpm",
            "macro_divisas_mercado": "usd_clp_cierre",
            "macro_precios_actividad": "uf_cierre",
        }[name]
        previous = published / f"{name}.parquet"
        # Si aparece un mes nuevo, no publicar hasta que exista su dato central.
        # Un mes incompleto ya publicado no debe romper la validación histórica.
        if pd.isna(df.iloc[-1][core]) and (not previous.exists() or periods[-1] > pd.read_parquet(previous, columns=["periodo"])["periodo"].max()):
            raise ValueError(f"Falta dato esencial en nuevo periodo: {name}.{core}")
        if previous.exists():
            old = pd.read_parquet(previous)
            if len(df) < len(old) or periods[-1] < old["periodo"].max() or periods[0] > old["periodo"].min():
                raise ValueError(f"Regresión de cobertura en {name}: {len(df)} filas, hasta {periods[-1]}")
            # Un error de API que devuelve series parcialmente vacías no debe borrar
            # datos antes publicados. Se permite revisar excepciones manualmente.
            overlap = df[df["periodo"].isin(old["periodo"])]
            for col in old.columns.intersection(df.columns).difference(["periodo"]):
                if overlap[col].notna().sum() < old[col].notna().sum():
                    raise ValueError(f"Regresión de datos no nulos en {name}.{col}")
        summary[name] = {"rows": len(df), "start": periods[0], "end": periods[-1]}
    if len({tuple(v.values()) for v in summary.values()}) != 1:
        raise ValueError("Las tres tablas macro tienen distinta cobertura temporal")
    return summary


def publish(stage: Path, published: Path, manifest: Path):
    summary = validate(stage, published)
    catalog = json.loads(manifest.read_text(encoding="utf-8"))
    entries = {t["id"]: t for t in catalog["tables"] if t["id"] in NAMES}
    if set(entries) != set(NAMES):
        raise ValueError("Faltan entradas macro en data_manifest.json")
    published.mkdir(parents=True, exist_ok=True)
    changed = any(
        not (published / f"{name}.{ext}").exists()
        or (stage / f"{name}.{ext}").read_bytes() != (published / f"{name}.{ext}").read_bytes()
        for name in NAMES for ext in ("parquet", "json")
    )
    if not changed:
        print("Macro sin cambios; no se modificó docs/ ni el manifiesto.")
        return False
    today = date.today().isoformat()
    for name, info in summary.items():
        entry = entries[name]
        entry["corte"] = f"{info['start']} a {info['end']}"
        entry["registros_reales"] = info["rows"]
        entry["ultima_actualizacion"] = today
    catalog["updated_at"] = today
    # Evitar sobrescribir archivos publicados con descargas sin auditar. Toda la
    # validación se hace antes de tocar docs/; cada archivo se reemplaza atómicamente.
    for name in NAMES:
        for ext in ("parquet", "json"):
            src = stage / f"{name}.{ext}"
            with tempfile.NamedTemporaryFile(dir=published, delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                shutil.copyfile(src, tmp_path)
                os.replace(tmp_path, published / src.name)
            finally:
                tmp_path.unlink(missing_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=manifest.parent, delete=False) as tmp:
        json.dump(catalog, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, manifest)
    print(f"Macro publicada y manifiesto actualizado: {summary}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage-dir", type=Path, default=ROOT / ".local-data" / "macro")
    args = parser.parse_args()
    publish(args.stage_dir.resolve(), ROOT / "docs" / "outputs" / "macro", ROOT / "data_manifest.json")

"""Orquesta consulta incremental BCCh y publicación solo si pasa la auditoría.

El checkpoint ignorado por Git guarda actualizaciones validadas aún no fusionadas
al repositorio. En Actions, cache/restore lo persiste entre ejecuciones.
"""
import os
import shutil
from pathlib import Path

import pandas as pd

from macro.scripts.pipeline_stream_macro_bcch import ROOT, TABLES, load_baseline, run_macro_pipeline
from macro.scripts.publish_macro import publish, validate

PUBLISHED = ROOT / "docs" / "outputs" / "macro"
CHECKPOINT = ROOT / ".local-data" / "checkpoint" / "macro"
STAGE = ROOT / ".local-data" / "macro"


def run():
    source = PUBLISHED
    if any(CHECKPOINT.glob("*.parquet")):
        cache = load_baseline(CHECKPOINT)  # abortar si está incompleto
        published = load_baseline(PUBLISHED)
        if not published or cache[TABLES[0]]["periodo"].iloc[-1] >= published[TABLES[0]]["periodo"].iloc[-1]:
            source = CHECKPOINT

    run_macro_pipeline(output_dir=STAGE, baseline_dir=source)
    validate(STAGE, source)  # nunca guardar un checkpoint no auditado
    checkpoint_changed = any(
        (STAGE / f"{name}.{ext}").read_bytes() != (source / f"{name}.{ext}").read_bytes()
        for name in TABLES for ext in ("parquet", "json")
    )
    # El repo nunca recibe commits automáticos. Publicar en la copia de trabajo
    # solo si pasa la comparación contra los datos públicos; Actions empaqueta
    # los archivos cambiados en artifact para revisión humana.
    published_changed = publish(STAGE, PUBLISHED, ROOT / "data_manifest.json")
    if checkpoint_changed:
        CHECKPOINT.mkdir(parents=True, exist_ok=True)
        for name in TABLES:
            for ext in ("parquet", "json"):
                shutil.copyfile(STAGE / f"{name}.{ext}", CHECKPOINT / f"{name}.{ext}")
    print(f"Checkpoint: {'actualizado' if checkpoint_changed else 'sin cambios'}; "
          f"publicación propuesta: {'sí' if published_changed else 'sin cambios'}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"checkpoint_changed={str(checkpoint_changed).lower()}\n")
            f.write(f"published_changed={str(published_changed).lower()}\n")
    return checkpoint_changed, published_changed


if __name__ == "__main__":
    run()

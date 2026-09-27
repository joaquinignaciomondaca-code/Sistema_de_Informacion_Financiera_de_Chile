"""Orquesta la actualización incremental diaria de REPO bancario CMF.

Sigue el mismo patrón seguro de macro:
1. Lee base desde checkpoint o datos publicados.
2. Descarga incrementalmente solo los períodos nuevos/actuales.
3. Ejecuta la auditoría estricta (audit_repos_saldos_series.py).
4. Publica en el directorio de staging y emite outputs para Actions.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from bancos.scripts.audit_repos_saldos_series import Auditoria
from bancos.scripts.pipeline_stream_repos_cmf import ROOT, run_bancos_repo_pipeline

PUBLISHED = ROOT / "docs" / "outputs" / "bancos"
CHECKPOINT = ROOT / ".local-data" / "checkpoint" / "bancos"
STAGE = ROOT / ".local-data" / "bancos_repo"


def run() -> tuple[bool, bool]:
    source = PUBLISHED
    if (CHECKPOINT / "bancos_repos_saldos_series.parquet").exists():
        source = CHECKPOINT

    STAGE.mkdir(parents=True, exist_ok=True)
    # Ejecutar pipeline hacia el directorio de stage
    ok, count = run_bancos_repo_pipeline(output_dir=STAGE)
    if not ok:
        print("[ERROR] Falló la ejecución del pipeline de REPO CMF", file=sys.stderr)
        return False, False

    # Auditar resultado en STAGE antes de considerar cualquier cambio
    # Se audita apuntando a la raíz simulada
    auditoria = Auditoria(str(ROOT))
    # Sobrescribir temporalmente las rutas de auditoría hacia STAGE si hay cambios
    p_stage = STAGE / "bancos_repos_saldos_series.parquet"
    if p_stage.exists():
        # Copiar al árbol para que la auditoría canónica evalúe
        target_parquet = PUBLISHED / "bancos_repos_saldos_series.parquet"
        target_json = PUBLISHED / "bancos_repos_saldos_series.json"

        # Verificar si hubo cambios reales en bytes
        changed = False
        if target_parquet.exists():
            changed = p_stage.read_bytes() != target_parquet.read_bytes()
        else:
            changed = True

        if changed:
            print(f"[AUDITORIA] Validando lote nuevo ({count} registros actualizados)...")
            shutil.copyfile(p_stage, target_parquet)
            shutil.copyfile(STAGE / "bancos_repos_saldos_series.json", target_json)

            code = auditoria.ejecutar()
            if code != 0:
                print("[ERROR] Auditoría reprobada: abortando actualización", file=sys.stderr)
                return False, False

            # Guardar en checkpoint
            CHECKPOINT.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(target_parquet, CHECKPOINT / "bancos_repos_saldos_series.parquet")
            shutil.copyfile(target_json, CHECKPOINT / "bancos_repos_saldos_series.json")

            print("[OK] Lote validado y checkpoint guardado.")
            gh_out = os.environ.get("GITHUB_OUTPUT")
            if gh_out:
                with open(gh_out, "a", encoding="utf-8") as f:
                    f.write("checkpoint_changed=true\n")
                    f.write("published_changed=true\n")
            return True, True

    print("Sin cambios en los saldos REPO.")
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write("checkpoint_changed=false\n")
            f.write("published_changed=false\n")
    return False, False


if __name__ == "__main__":
    ch, pub = run()

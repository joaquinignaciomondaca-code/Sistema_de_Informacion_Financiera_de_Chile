"""Evalúa los gates humanos/técnicos de publicación BDP; por defecto queda bloqueada."""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    from .bdp_common import PRIVATE_ROOT, ROOT, atomic_json
except ImportError:  # ejecución directa desde pensiones/scripts/
    from bdp_common import PRIVATE_ROOT, ROOT, atomic_json  # type: ignore

DEFAULT_POLICY = ROOT / "pensiones/config/publicacion_bdp.json"
REQUIRED_CRITERIA = (
    "descarga_oficial_y_procedencia",
    "cotejo_de_originales_sp",
    "cobertura_y_clasificacion_historica",
    "semantica_y_precision_de_campos",
    "redistribucion_de_datos_y_derivados",
)
EXPECTED_RESULTS = {
    "descarga_oficial_y_procedencia": "origen_y_archivo_verificados",
    "cotejo_de_originales_sp": "cotejo_aprobado",
    "cobertura_y_clasificacion_historica": "cobertura_aprobada",
    "semantica_y_precision_de_campos": "campos_validados",
    "redistribucion_de_datos_y_derivados": "redistribucion_permitida_o_autorizada",
}
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-fA-F0-9]{40}$")


def _evidence_errors(name: str, evidence: Any) -> list[str]:
    if not isinstance(evidence, dict):
        return [f"{name}: falta evidencia documental revisable"]
    errors = []
    for field in ("documento", "fecha", "revisor", "resultado", "revision_commit"):
        if not isinstance(evidence.get(field), str) or not evidence[field].strip():
            errors.append(f"{name}: evidencia sin {field}")
    if not evidence.get("url") and not evidence.get("archivo_repo"):
        errors.append(f"{name}: evidencia sin URL oficial ni archivo de evidencia versionado")
    if evidence.get("url") and not str(evidence["url"]).startswith("https://"):
        errors.append(f"{name}: URL de evidencia no HTTPS")
    if evidence.get("sha256") and not SHA256_RE.fullmatch(str(evidence["sha256"])):
        errors.append(f"{name}: SHA-256 de evidencia inválido")
    if not SHA256_RE.fullmatch(str(evidence.get("sha256", ""))):
        errors.append(f"{name}: falta SHA-256 verificable del documento/evidencia")
    if not COMMIT_RE.fullmatch(str(evidence.get("revision_commit", ""))):
        errors.append(f"{name}: revision_commit debe ser un commit Git completo")
    try:
        date.fromisoformat(str(evidence.get("fecha", ""))[:10])
    except ValueError:
        errors.append(f"{name}: fecha de evidencia inválida")
    return errors


def evaluate(policy_path: Path = DEFAULT_POLICY, staging: Path | None = None) -> dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("version") != 1:
        raise ValueError("Versión de política de publicación BDP no soportada")
    reasons: list[str] = []
    if policy.get("estado") != "aprobado":
        reasons.append("La política versionada mantiene el estado bloqueado")
    criteria = policy.get("criterios", {})
    for criterion in REQUIRED_CRITERIA:
        item = criteria.get(criterion)
        if not isinstance(item, dict) or item.get("estado") != "validado":
            reasons.append(f"Criterio pendiente: {criterion}")
            continue
        evidence = item.get("evidencia")
        reasons.extend(_evidence_errors(criterion, evidence))
        if isinstance(evidence, dict) and evidence.get("resultado") != EXPECTED_RESULTS[criterion]:
            reasons.append(f"{criterion}: evidencia no declara el resultado habilitante requerido")
    final_approval = policy.get("aprobacion_final")
    if policy.get("estado") == "aprobado":
        reasons.extend(_evidence_errors("aprobacion_final", final_approval))
        if isinstance(final_approval, dict) and final_approval.get("resultado") != "publicacion_aprobada":
            reasons.append("aprobacion_final: resultado distinto de publicacion_aprobada")

    audit_result = None
    if staging is None:
        reasons.append("No se entregó un staging auditado")
    else:
        try:
            try:
                from .audit_carteras_afp import audit
            except ImportError:
                from audit_carteras_afp import audit  # type: ignore
            audit_result = audit(Path(staging), require_full_history=True)
            if not audit_result.get("historico_completo_por_paquetes"):
                reasons.append("No están activos los tres paquetes históricos declarados")
            if audit_result.get("codigos_no_clasificados"):
                reasons.append("Hay códigos de instrumento sin clasificar")
            expected = {"historico_1996_2005", "historico_2006_2015", "historico_2016_actualidad"}
            actual = set(audit_result.get("paquetes_oficiales_verificados", []))
            if not expected <= actual:
                reasons.append("No todos los paquetes tienen sidecar oficial verificado")
        except Exception as exc:
            reasons.append(f"Staging no supera la auditoría completa: {type(exc).__name__}: {exc}")

    return {
        "ready": not reasons,
        "estado": "autorizado" if not reasons else "bloqueado",
        "razones": reasons,
        "politica": str(policy_path.relative_to(ROOT)) if policy_path.is_relative_to(ROOT) else policy_path.name,
        "staging_audit": audit_result,
        "publicacion_de_datos": "no ejecutada" if reasons else "requiere entorno protegido pensiones-publicacion",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--staging", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--require-ready", action="store_true", help="Devuelve código 2 si la publicación sigue bloqueada")
    args = parser.parse_args(argv)
    try:
        result = evaluate(args.policy, args.staging)
    except Exception as exc:
        result = {
            "ready": False,
            "estado": "bloqueado",
            "razones": [f"No se pudo evaluar la política: {type(exc).__name__}: {exc}"],
        }
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.output_json:
        destination = args.output_json.resolve()
        if PRIVATE_ROOT not in destination.parents:
            raise ValueError("El informe de gate debe permanecer bajo .local-data/")
        atomic_json(destination, result)
    return 2 if args.require_ready and not result["ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

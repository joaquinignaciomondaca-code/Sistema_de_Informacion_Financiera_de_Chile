"""Cotejo de cuentas de REPO en ZIP CMF; evidencia para revisión, nunca publica.

Inspecciona TODOS los balances B1/B2 de cada ZIP mensual, sin Excel, WinRAR,
credenciales ni acceso al PC. Lee los códigos candidatos proporcionados en el
script V2 del usuario, conserva montos crudos y calcula *hipótesis* de escala
para contrastar con la serie retirada de validación. No presupone cuál columna
es el total ni acepta coincidencias como certificación contable.

El checkpoint de diagnóstico solo avanza tras descarga, parseo y reporte de un
lote completo. Ninguna función modifica docs/outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from bancos.scripts import probe_repos_zip_cmf as probe

REPORT = probe.ROOT / ".local-data/review/bancos/repo_zip_audit.json"
CHECKPOINT = probe.ROOT / ".local-data/checkpoint/bancos-repo-audit/last_period.json"
# Divisores probados contra la referencia legacy. El 1 (valor ya en MM CLP) es
# una hipótesis más: el script V2 del usuario dividía por 1.000 antes de 2022,
# pero los ZIP reales de 2021-12 traen el rubro ya en MM CLP.
DIVISORS = (Decimal(1), Decimal(1000), Decimal(1000000))
CODE_HINTS = {
    "pre_2022": {"activo": "1160000", "pasivo": "2160000"},
    "post_2022": {"activo": "141000000", "pasivo": "243000000"},
}
# Cuenta y tipo de dato tomados del script principal V2 facilitado por el usuario;
# todavía no verificados contra el parser src/parser.py ni manual CMF.


def money(raw: str) -> Decimal | None:
    """Normaliza solo la sintaxis numérica, NO la unidad contable."""
    value = raw.strip().replace(" ", "")
    if not value or value == "-":
        return None
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif not re.fullmatch(r"[+-]?\d+(?:\.\d{3})*", value):
        return None
    else:
        value = value.replace(".", "")
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def fmt(value: Decimal) -> str:
    """Decimal a texto plano (evita notación científica de normalize())."""
    return format(value.normalize(), "f")


def inspect_all(blob: bytes, period: str, url: str, legacy: dict) -> dict:
    """Extrae candidatos de todos los bancos sin confundir ausente con cero."""
    if not probe.trusted_zip(url) or len(blob) > probe.MAX_ZIP:
        raise ValueError("Origen ZIP no confiable o mayor al límite")
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile:
        raise ValueError(f"ZIP CMF inválido para {period}") from None
    banks: dict[str, dict] = {}
    with z:
        for info in z.infolist():
            match = probe.BALANCE_TXT.fullmatch(Path(info.filename).name)
            if not match or f"{match[2]}-{match[3]}" != period:
                continue
            kind, bank = match[1].upper(), match[4]
            if info.file_size == 0 or info.file_size > probe.MAX_TXT:
                raise ValueError(f"Balance {period}/{bank} vacío o excesivo")
            if kind in banks.get(bank, {}).get("archivos", {}):
                raise ValueError(f"Dos archivos {kind} para {bank}/{period}; revisar versiones")
            try:
                lines = z.read(info).decode("latin-1").splitlines()
            except (RuntimeError, zipfile.BadZipFile, UnicodeError):
                raise ValueError(f"Archivo dañado {period}/{bank}/{kind}") from None
            account_rows: dict[str, list[list[str]]] = {}
            for line in lines:
                cols = [c.strip() for c in line.split("\t")]
                if cols and cols[0] in ("1160000", "2160000", "141000000", "243000000"):
                    account_rows.setdefault(cols[0], []).append(cols[1:])
            banks.setdefault(bank, {"codigo_banco": bank, "archivos": {}})["archivos"][kind] = {
                "nombre": Path(info.filename).name,
                "filas": len(lines), "cuentas": account_rows,
            }
    if not banks:
        raise ValueError(f"Sin archivos B1/B2 en ZIP de {period}")
    hints = CODE_HINTS["pre_2022" if period < "2022-01" else "post_2022"]
    results = []
    for bank, data in sorted(banks.items()):
        old = legacy.get((period, bank))
        row = {"codigo_banco": bank, "archivos": data["archivos"],
               "referencia_legacy_mm_clp": old, "hipotesis_escala": {}}
        for side, account in hints.items():
            matched = [(kind, vals) for kind, f in data["archivos"].items()
                       for vals in f["cuentas"].get(account, [])]
            if len(matched) != 1:
                row["hipotesis_escala"][side] = {"cuenta": account,
                                                   "estado": "ausente" if not matched else "duplicada"}
                continue
            kind, raw = matched[0]
            numbers = [money(v) for v in raw]
            total = sum((n for n in numbers if n is not None), Decimal(0))
            origins = [("suma_columnas", total)] + [
                (f"columna_{i}", n) for i, n in enumerate(numbers, start=1) if n is not None]
            possibilities = []
            if old is not None:
                reference = Decimal(str(old[side]))
                for origin, num in origins:
                    for divisor in DIVISORS:
                        # Comparación exploratoria, no selección automática de columna, plan ni unidad.
                        calc = num / divisor
                        if abs(calc - reference) <= Decimal("0.02"):
                            possibilities.append({"origen": origin, "divisor": int(divisor),
                                                  "valor_mm_clp": fmt(calc)})
            row["hipotesis_escala"][side] = {
                "cuenta": account, "archivo": kind, "campos_crudos": raw,
                "suma_columnas": fmt(total),
                "suma_con_divisor": {str(int(d)): fmt(total / d) for d in DIVISORS},
                "coincidencias_legacy": possibilities,
            }
        results.append(row)
    if not any(bank["hipotesis_escala"][side].get("campos_crudos")
               for bank in results for side in ("activo", "pasivo")):
        # Guardar evidencia del desacuerdo de códigos; no fabricar saldos cero.
        # El checkpoint es del diagnóstico ZIP, no de datos REPO validados.
        warning = f"No se encontraron las cuentas candidatas {hints} en {period}; revisar el plan"
    else:
        warning = None
    comparison = [bank for bank in results if bank["referencia_legacy_mm_clp"] is not None]
    return {"periodo": period, "url_zip": url, "sha256_zip": hashlib.sha256(blob).hexdigest(),
            "candidatos_del_script_v2": hints, "advertencia": warning, "bancos": results,
            "filas_con_referencia_legacy": len(comparison),
            "filas_con_alguna_coincidencia": sum(bool(bank["hipotesis_escala"][side].get("coincidencias_legacy"))
                                              for bank in comparison for side in ("activo", "pasivo"))}


def run(manual: str | None = None, output: Path = REPORT, checkpoint: Path = CHECKPOINT,
        today: date | None = None) -> dict:
    today = today or date.today()
    found, unresolved = probe.resolve_links()
    baseline = json.loads(probe.LEGACY.read_text(encoding="utf-8"))
    latest = max(row["periodo"] for row in baseline)
    saved = json.loads(checkpoint.read_text(encoding="utf-8"))["periodo"] if checkpoint.exists() else None
    if saved is not None and not probe.PERIOD.fullmatch(saved):
        raise ValueError("Checkpoint de auditoría inválido")
    periods = probe.select(found, latest, saved, today, manual)
    if manual in unresolved or (not manual and any(latest <= p <= probe.last_complete(today) for p in unresolved)):
        raise ValueError(f"Versiones ZIP ambiguas: {sorted(unresolved)}")
    legacy = {(row["periodo"], row["codigo_institucion"]):
              {"activo": row["repo_activo_mm_clp"], "pasivo": row["repo_pasivo_mm_clp"]}
              for row in baseline}
    reports = []
    for p in periods:
        try:
            reports.append(inspect_all(probe.read_public(found[p], probe.MAX_ZIP), p, found[p], legacy))
        except (ValueError, RuntimeError) as exc:
            # Un error después de descargar meses previos no debe avanzar el
            # checkpoint ni hacer pasar el lote por íntegro. Conservar evidencia
            # parcial únicamente en el directorio de revisión (no publicado).
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({
                "estado": "cotejo_incompleto_no_publicado", "fuente": probe.INDEX,
                "periodos_completos": reports, "periodo_fallido": p, "error": str(exc),
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise
    document = {"estado": "cotejo_exploratorio_no_publicado", "fuente": probe.INDEX,
                "advertencia": "Coincidencias numéricas no certifican cuenta, columna, unidad, vigencia ni RUT.",
                "periodos": reports}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not manual:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(json.dumps({"periodo": periods[-1]}) + "\n", encoding="utf-8")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", help="Mes de calibración AAAA-MM, p. ej. 2021-12")
    args = parser.parse_args()
    try:
        report = run(manual=args.period)
    except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"Cotejo ZIP CMF incompleto: {exc}", file=sys.stderr)
        return 1
    print(f"Cotejados {len(report['periodos'])} meses; evidencia para revisión; REPO publicado intacto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

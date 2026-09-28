"""Extract July-2026 CMF bank B1, B2 and R1 lines for review, never publication.

Records remain at source-account grain. Numeric fields are retained verbatim
and as exact decimal strings: B1/B2 fields are intentionally not assigned
currency-component names until their published TXT layout is reconciled with
the CMF model. This tool writes only to a review directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import unicodedata
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

from bancos.scripts.inspect_cmf_bank_sample import (
    MAX_FILE,
    MAX_ZIP_TOTAL,
    MEMBER_RE,
    ZIP_INDEX,
    fetch,
    find_source,
    period_label,
)

TARGETS = {
    "B1": {"modelo_cmf": "MB1", "tipo_estado": "balance", "nivel_consolidacion": "consolidado_global", "expected_amount_fields": 4},
    "B2": {"modelo_cmf": "MB2", "tipo_estado": "balance", "nivel_consolidacion": "individual", "expected_amount_fields": 4},
    "R1": {"modelo_cmf": "MR1", "tipo_estado": "resultados", "nivel_consolidacion": "consolidado_global", "expected_amount_fields": 1},
}
AMOUNT_RE = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")
CODE_RE = re.compile(r"^\d{9}$")


def month_end(period: str) -> str:
    period_label(period)
    year, month = map(int, period.split("-"))
    if month == 12:
        return f"{year}-12-31"
    next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).isoformat()


def parse_amount(value: str) -> str:
    """Return an exact normalized decimal string while retaining raw input elsewhere."""
    token = value.strip()
    if not AMOUNT_RE.fullmatch(token):
        raise ValueError(f"Invalid CMF amount token: {value!r}")
    try:
        amount = Decimal(token.replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"Invalid CMF amount token: {value!r}") from None
    if not amount.is_finite():
        raise ValueError(f"Non-finite CMF amount token: {value!r}")
    return format(amount, "f")


def decode_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def parse_account_model(text: str, member_name: str) -> dict[str, dict[str, str]]:
    reader = csv.reader(text.splitlines(), delimiter="\t")
    rows = list(reader)
    if not rows:
        raise RuntimeError(f"Empty CMF account model: {member_name}")
    headers = [value.strip().upper() for value in rows[0]]
    expected_headers = ["CUENTA", "RUBRO", "LINEA", "ITEM", "GLOSA"]
    if headers != expected_headers:
        raise RuntimeError(f"Unexpected columns in {member_name}: {headers!r}")
    model: dict[str, dict[str, str]] = {}
    for line_no, values in enumerate(rows[1:], start=2):
        if not values or not any(value.strip() for value in values):
            continue
        if len(values) < 5:
            raise RuntimeError(f"Malformed account definition in {member_name}:{line_no}: {values!r}")
        account, rubro, linea, item = [value.strip() for value in values[:4]]
        description = "\t".join(values[4:]).strip()
        if not CODE_RE.fullmatch(account) or not rubro or not linea or not item or not description:
            raise RuntimeError(f"Incomplete account definition in {member_name}:{line_no}")
        if account in model:
            raise RuntimeError(f"Duplicate account definition {account} in {member_name}")
        model[account] = {"rubro": rubro, "linea": linea, "item": item, "glosa_cuenta": description}
    if not model:
        raise RuntimeError(f"No account definitions in {member_name}")

    account_codes = set(model)
    for account, definition in model.items():
        if definition["glosa_cuenta"].strip().upper().startswith("TOTAL "):
            definition["tipo_linea"] = "total"
            continue
        prefix = account.rstrip("0")
        has_children = bool(prefix) and any(
            other != account and other.startswith(prefix) for other in account_codes
        )
        definition["tipo_linea"] = "subtotal" if has_children else "detalle"
    return model


def _file_kind_and_bank(filename: str, period: str) -> tuple[str, str] | None:
    match = MEMBER_RE.search(filename)
    if not match or f"{match.group(3)}-{match.group(4)}" != period:
        return None
    return f"{match.group(1).upper()}{match.group(2)}", match.group(5)


def extract_archive(blob: bytes, period: str, source_url: str = "") -> tuple[list[dict], dict]:
    """Extract all institutions' B1/B2/R1 records from one CMF ZIP in memory."""
    period_label(period)
    if len(blob) > MAX_FILE:
        raise ValueError(f"CMF ZIP exceeds {MAX_FILE} bytes")
    try:
        archive = zipfile.ZipFile(BytesIO(blob))
    except zipfile.BadZipFile:
        raise ValueError("CMF bank archive is not a valid ZIP") from None

    with archive:
        infos = [item for item in archive.infolist() if not item.is_dir()]
        if sum(item.file_size for item in infos) > MAX_ZIP_TOTAL or any(item.file_size > MAX_FILE for item in infos):
            raise ValueError("CMF ZIP exceeds safe expansion limits")
        selected: dict[tuple[str, str], list[zipfile.ZipInfo]] = defaultdict(list)
        institution_codes: set[str] = set()
        for info in infos:
            parsed = _file_kind_and_bank(info.filename, period)
            if parsed:
                kind, bank_code = parsed
                institution_codes.add(bank_code)
                if kind in TARGETS:
                    selected[(bank_code, kind)].append(info)

        if not institution_codes:
            raise RuntimeError(f"No CMF bank TXT files found for {period}")
        account_models: dict[str, dict[str, dict[str, str]]] = {}
        for kind, model_name in (("B1", "modelo_mb1.txt"), ("B2", "modelo_mb2.txt"), ("R1", "modelo_mr1.txt")):
            model_infos = [info for info in infos if info.filename.casefold().endswith("/" + model_name)]
            if len(model_infos) != 1:
                raise RuntimeError(f"Expected exactly one metadata/{model_name}; found {len(model_infos)}")
            account_models[kind] = parse_account_model(decode_text(archive.read(model_infos[0])), model_infos[0].filename)
        duplicate_sources = {f"{bank}/{kind}": len(items) for (bank, kind), items in selected.items() if len(items) != 1}
        missing_sources = [f"{bank}/{kind}" for bank in sorted(institution_codes) for kind in TARGETS if len(selected.get((bank, kind), [])) == 0]
        if duplicate_sources or missing_sources:
            raise RuntimeError(
                "Incomplete or duplicate B1/B2/R1 source files: "
                + json.dumps({"missing": missing_sources, "duplicates": duplicate_sources}, ensure_ascii=False)
            )

        rows: list[dict] = []
        file_reports: list[dict] = []
        source_names_by_code: dict[str, set[str]] = defaultdict(set)
        total_data_rows = Counter()
        account_occurrences: dict[tuple[str, str, str], int] = Counter()

        for bank_code, kind in sorted(selected, key=lambda item: (item[0], ("B1", "B2", "R1").index(item[1]))):
            info = selected[(bank_code, kind)][0]
            text = decode_text(archive.read(info))
            lines = [(line_no, line) for line_no, line in enumerate(text.splitlines(), start=1) if line.strip()]
            if not lines:
                raise RuntimeError(f"Empty CMF file: {info.filename}")
            header_no, header_line = lines[0]
            header = header_line.split("\t")
            if len(header) != 2 or header[0].strip() != bank_code or not header[1].strip():
                raise RuntimeError(f"Malformed institution header in {info.filename}: {header_line!r}")
            institution_name = header[1].strip()
            source_names_by_code[bank_code].add(institution_name)
            expected_amount_fields = TARGETS[kind]["expected_amount_fields"]
            data_rows = 0
            code_counts = Counter()
            observed_widths = Counter()

            for line_no, line in lines[1:]:
                fields = line.split("\t")
                observed_widths[len(fields)] += 1
                if len(fields) != expected_amount_fields + 1:
                    raise RuntimeError(
                        f"Unexpected field count in {info.filename}:{line_no}; "
                        f"expected {expected_amount_fields + 1}, got {len(fields)}"
                    )
                account_code = fields[0].strip()
                if not CODE_RE.fullmatch(account_code):
                    raise RuntimeError(f"Invalid account code in {info.filename}:{line_no}: {account_code!r}")
                raw_amounts = [value.strip() for value in fields[1:]]
                exact_amounts = [parse_amount(value) for value in raw_amounts]
                account_definition = account_models[kind].get(account_code)
                if account_definition is None:
                    raise RuntimeError(f"Account {account_code} is absent from {kind} model metadata")
                account_occurrences[(bank_code, kind, account_code)] += 1
                occurrence = account_occurrences[(bank_code, kind, account_code)]
                model = TARGETS[kind]
                rows.append({
                    "id": f"{period}:{bank_code}:{model['modelo_cmf']}:{account_code}:{occurrence}",
                    "periodo": period,
                    "fecha_corte": month_end(period),
                    "codigo_institucion": bank_code,
                    "rut": None,
                    "razon_social": None,
                    "nombre_institucion_fuente": institution_name,
                    "tipo_estado": model["tipo_estado"],
                    "familia_archivo_fuente": kind,
                    "modelo_cmf": model["modelo_cmf"],
                    "nivel_consolidacion": model["nivel_consolidacion"],
                    "codigo_cuenta": account_code,
                    "rubro": account_definition["rubro"],
                    "linea": account_definition["linea"],
                    "item": account_definition["item"],
                    "glosa_cuenta": account_definition["glosa_cuenta"],
                    "tipo_linea": account_definition["tipo_linea"],
                    "numero_fila_fuente": line_no,
                    "ocurrencia_codigo_cuenta": occurrence,
                    "unidad_monto": "pesos_clp",
                    "importes_fuente_raw": raw_amounts,
                    "importes_fuente_decimal": exact_amounts,
                    "archivo_fuente": info.filename,
                })
                code_counts[account_code] += 1
                data_rows += 1

            total_data_rows[kind] += data_rows
            file_reports.append({
                "source_member": info.filename,
                "codigo_institucion": bank_code,
                "nombre_institucion_fuente": institution_name,
                "familia_archivo_fuente": kind,
                "modelo_cmf": TARGETS[kind]["modelo_cmf"],
                "tipo_estado": TARGETS[kind]["tipo_estado"],
                "nivel_consolidacion": TARGETS[kind]["nivel_consolidacion"],
                "nonempty_source_lines": len(lines),
                "account_rows": data_rows,
                "field_count_distribution": dict(sorted(observed_widths.items())),
                "duplicate_account_codes": sum(count - 1 for count in code_counts.values() if count > 1),
                "amount_field_count": expected_amount_fields,
            })

        name_mismatches = {code: sorted(names) for code, names in source_names_by_code.items() if len(names) != 1}
        if name_mismatches:
            raise RuntimeError(f"Institution header names differ across statement files: {name_mismatches}")

    review_accounts = []
    for bank_code, kind, account_code in (("001", "B1", "100000000"), ("001", "R1", "411000000")):
        candidates = [
            row for row in rows
            if row["codigo_institucion"] == bank_code
            and row["familia_archivo_fuente"] == kind
            and row["codigo_cuenta"] == account_code
        ]
        for row in candidates:
            review_accounts.append({
                "codigo_institucion": bank_code,
                "familia_archivo_fuente": kind,
                "codigo_cuenta": account_code,
                "numero_fila_fuente": row["numero_fila_fuente"],
                "importes_fuente_raw": row["importes_fuente_raw"],
                "suma_campos_fuente_decimal": format(sum(Decimal(value) for value in row["importes_fuente_decimal"]), "f"),
            })

    report = {
        "status": "extracted_for_review_not_published",
        "period": period,
        "fecha_corte": month_end(period),
        "source_url": source_url or None,
        "source_sha256": hashlib.sha256(blob).hexdigest(),
        "source_zip_bytes": len(blob),
        "institution_count": len(institution_codes),
        "institution_codes": sorted(institution_codes),
        "file_count": len(file_reports),
        "account_rows_by_family": dict(sorted(total_data_rows.items())),
        "account_model_stats": {
            kind: {
                "account_definitions": len(model),
                "line_types": dict(sorted(Counter(definition["tipo_linea"] for definition in model.values()).items())),
            }
            for kind, model in sorted(account_models.items())
        },
        "review_account_samples": review_accounts,
        "file_reports": file_reports,
        "field_semantics": {
            "B1_B2": "Importes fuente se preservan sin nombres de moneda hasta cotejar el esquema TXT vigente con la definición normativa.",
            "R1": "Un campo de importe por cuenta; clasificación temporal acumulada/mensual queda pendiente de cotejo.",
            "account_hierarchy": "Glosa y códigos rubro/línea/ítem se leen del modelo CMF correspondiente; tipo_linea se deriva de TOTAL explícito o de la jerarquía de descendientes del mismo modelo.",
            "institution_identity": "El código y nombre se leen del encabezado CMF; RUT se deja nulo hasta validar el cruce con el maestro.",
        },
        "validation": {
            "all_required_statement_files_present": True,
            "all_data_rows_have_expected_shape": True,
            "duplicate_account_codes_retained_with_occurrence": True,
            "published": False,
        },
    }
    return rows, report


def normalize_name(value: object) -> str:
    # Quitar tildes antes de filtrar: "Crédito" (XLSX) debe igualar "CREDITO" (ZIP).
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def reconcile_to_inspection(rows: list[dict], inspection: dict, bank_code: str = "001", bank_name: str = "Banco de Chile") -> dict:
    """Compare CMF account amounts with the matching bank rows cached by the XLSX inspector."""
    workbook = inspection.get("workbook", {})
    target_name = normalize_name(bank_name)

    def sheet_values(title: str) -> list[dict]:
        return [
            row for row in workbook.get("bank_rows", [])
            if normalize_name(row.get("sheet")) == normalize_name(title)
            and any(target_name in normalize_name(value) for value in row.get("values", []) if isinstance(value, str))
        ]

    def numeric_cells(sheet_rows: list[dict]) -> list[dict]:
        result = []
        for sheet_row in sheet_rows:
            for index, value in enumerate(sheet_row.get("values", [])):
                if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
                    continue
                number = Decimal(str(value))
                if number.is_finite():
                    result.append({"sheet": sheet_row.get("sheet"), "row_number": sheet_row.get("row_number"), "column_index": index, "value_mm_clp": format(number, "f")})
        return result

    balance_rows = sheet_values("Est. Situación Financ. Bancos")
    balance_cells = numeric_cells(balance_rows)
    asset_lines = [
        row for row in rows
        if row["codigo_institucion"] == bank_code
        and row["familia_archivo_fuente"] == "B1"
        and row["codigo_cuenta"] == "100000000"
    ]
    asset_checks = []
    for line in asset_lines:
        candidate_pesos = sum(Decimal(value) for value in line["importes_fuente_decimal"])
        matches = [
            cell for cell in balance_cells
            if abs(Decimal(cell["value_mm_clp"]) * Decimal(1_000_000) - candidate_pesos) <= Decimal(1)
        ]
        asset_checks.append({
            "codigo_cuenta": line["codigo_cuenta"],
            "glosa_cuenta": line["glosa_cuenta"],
            "source_row": line["numero_fila_fuente"],
            "sum_of_source_fields_pesos": format(candidate_pesos, "f"),
            "matches_xlsx": matches,
            "status": "passed" if matches else "failed",
        })

    result_rows = sheet_values("Est. del Resultado Bancos")
    result_cells = numeric_cells(result_rows)
    result_matches = []
    for line in rows:
        if line["codigo_institucion"] != bank_code or line["familia_archivo_fuente"] != "R1":
            continue
        pesos = Decimal(line["importes_fuente_decimal"][0])
        if pesos == 0:
            continue
        matches = [
            cell for cell in result_cells
            if abs(Decimal(cell["value_mm_clp"]) * Decimal(1_000_000) - pesos) <= Decimal(1)
        ]
        if matches:
            result_matches.append({
                "codigo_cuenta": line["codigo_cuenta"],
                "glosa_cuenta": line["glosa_cuenta"],
                "source_row": line["numero_fila_fuente"],
                "importe_pesos": format(pesos, "f"),
                "matches_xlsx": matches,
            })
    return {
        "bank_code": bank_code,
        "bank_name": bank_name,
        "balance_sheet": "Est. Situación Financ. Bancos",
        "b1_total_assets_account": asset_checks,
        "b1_status": "passed" if asset_checks and all(item["status"] == "passed" for item in asset_checks) else "failed_or_unavailable",
        "results_sheet": "Est. del Resultado Bancos",
        "r1_exact_account_matches_in_xlsx": result_matches,
        "r1_status": "matched" if result_matches else "pending_no_exact_account_match",
        "amount_comparison": "source fields are pesos; workbook comparisons convert MM$ to pesos with tolerance of 1 peso",
    }


def write_review_outputs(rows: list[dict], report: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    jsonl = output / "bancos_cmf_b1_b2_r1_lineas.jsonl"
    with jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    (output / "extraction_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = report["account_rows_by_family"]
    markdown = [
        f"## Extracción CMF B1/B2/R1 — {report['period']} (solo revisión)",
        "",
        f"- Instituciones: **{report['institution_count']}**",
        f"- Archivos fuente procesados: **{report['file_count']}**",
        f"- Líneas por familia: **{json.dumps(counts, ensure_ascii=False, sort_keys=True)}**",
        f"- SHA-256 del ZIP: `{report['source_sha256']}`",
        "- Publicado en el sitio: **no**",
        "",
        "### Filas de referencia para cotejo",
        "",
    ]
    reconciliation = report.get("reconciliation")
    if reconciliation:
        markdown.extend([
            f"- Cotejo B1 TOTAL ACTIVOS vs Excel: **{reconciliation['b1_status']}**",
            f"- Cotejos exactos de cuentas R1 vs hoja Excel: **{len(reconciliation['r1_exact_account_matches_in_xlsx'])}** (estado: `{reconciliation['r1_status']}`)",
            "",
        ])
        for match in reconciliation["r1_exact_account_matches_in_xlsx"]:
            markdown.append(
                f"  - R1 `{match['codigo_cuenta']} {match['glosa_cuenta']}` = {match['importe_pesos']} pesos "
                f"(fila TXT {match['source_row']}; Excel {match['matches_xlsx']})"
            )
    if report["review_account_samples"]:
        markdown.extend(["| Código | Familia | Cuenta | Fila fuente | Importes fuente | Suma de campos (diagnóstico) |", "|---|---|---:|---:|---|---:|"])
        for sample in report["review_account_samples"]:
            markdown.append(
                f"| {sample['codigo_institucion']} | {sample['familia_archivo_fuente']} | "
                f"{sample['codigo_cuenta']} | {sample['numero_fila_fuente']} | "
                f"`{json.dumps(sample['importes_fuente_raw'], ensure_ascii=False)}` | "
                f"{sample['suma_campos_fuente_decimal']} |"
            )
    else:
        markdown.append("No aparecieron las cuentas de referencia configuradas para Banco de Chile.")
    markdown.extend(["", "> La suma mostrada es diagnóstica; no implica que los campos representen componentes sumables.", ""])
    summary_text = "\n".join(markdown)
    (output / "extraction_summary.md").write_text(summary_text, encoding="utf-8")
    github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary:
        with open(github_summary, "a", encoding="utf-8") as summary_file:
            summary_file.write(summary_text + "\n")
    reconciliation = report.get("reconciliation", {})
    print("::notice title=CMF B1/B2/R1 extracted for review::" + json.dumps({
        "period": report["period"],
        "institutions": report["institution_count"],
        "files": report["file_count"],
        "account_rows_by_family": counts,
        "account_model_line_type_counts": {
            kind: stats["line_types"] for kind, stats in report["account_model_stats"].items()
        },
        "b1_status": reconciliation.get("b1_status", "not_compared"),
        "b1_asset_check": reconciliation.get("b1_total_assets_account", []),
        "r1_status": reconciliation.get("r1_status", "not_compared"),
        "r1_exact_xlsx_match_count": len(reconciliation.get("r1_exact_account_matches_in_xlsx", [])),
        "r1_exact_xlsx_matches_preview": [
            {"codigo_cuenta": item["codigo_cuenta"], "glosa_cuenta": item["glosa_cuenta"], "importe_pesos": item["importe_pesos"]}
            for item in reconciliation.get("r1_exact_account_matches_in_xlsx", [])[:20]
        ],
        "source_sha256": report["source_sha256"],
        "published": False,
    }, ensure_ascii=False, separators=(",", ":")), flush=True)


def run(period: str, output: Path, zip_path: Path | None = None, inspection_json: Path | None = None, source_url: str = "") -> dict:
    inspection = None
    if zip_path is None:
        source_url, _ = find_source(ZIP_INDEX, period, ".zip")
        blob = fetch(source_url, MAX_FILE)
    else:
        blob = zip_path.read_bytes()
        if inspection_json:
            inspection = json.loads(inspection_json.read_text(encoding="utf-8"))
            source = inspection.get("sources", {}).get("zip", {})
            if inspection.get("period") != period:
                raise ValueError("Inspection report period does not match extraction period")
            observed_hash = hashlib.sha256(blob).hexdigest()
            if source.get("sha256") != observed_hash:
                raise ValueError("ZIP bytes do not match the SHA-256 in the inspection report")
            source_url = source.get("url", source_url)
    rows, report = extract_archive(blob, period, source_url)
    if inspection is not None:
        report["reconciliation"] = reconcile_to_inspection(rows, inspection)
    write_review_outputs(rows, report, output)
    if inspection is not None and report["reconciliation"]["b1_status"] != "passed":
        raise RuntimeError("B1 TOTAL ACTIVOS did not reconcile to the CMF XLSX review row")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", default="2026-07", help="CMF reporting period YYYY-MM")
    parser.add_argument("--zip-path", type=Path, help="Use a ZIP already downloaded by the sample inspection")
    parser.add_argument("--inspection-json", type=Path, help="Verify ZIP hash against inspect_cmf_bank_sample.py output")
    parser.add_argument("--output", type=Path, default=Path(".local-data/review/bancos/bank_line_extraction"))
    args = parser.parse_args()
    try:
        run(args.period, args.output, args.zip_path, args.inspection_json)
    except Exception as exc:
        message = f"CMF B1/B2/R1 extraction failed safely: {type(exc).__name__}: {exc}"
        print(message, file=sys.stderr, flush=True)
        print("::error title=CMF B1/B2/R1 extraction failed::" + message.replace("%", "%25").replace("\r", "%0D"), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

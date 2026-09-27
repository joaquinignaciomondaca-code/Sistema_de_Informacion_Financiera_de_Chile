"""Pruebas offline de cotejo B1/B2 por banco y período."""
import io
import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from bancos.scripts import audit_repos_zip_cmf as audit
from bancos.scripts import probe_repos_zip_cmf as probe

URL = "https://www.cmfchile.cl/portal/estadisticas/626/articles-50166_recurso_1.zip"


def zip_data(period="202112", a="64365000", b="95009000"):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(f"pkg/b1{period}001.txt", f"codigo\tpesos\n1160000\t{a}\n2160000\t{b}\n1000000\t123")
        z.writestr(f"pkg/b1{period}059.txt", "codigo\tpesos\n1160000\t9833000\n2160000\t0")
        z.writestr(f"pkg/r1{period}001.txt", "not balance")
    return out.getvalue()


class AuditTests(unittest.TestCase):
    def test_all_banks_match_and_no_double_count(self):
        rows = audit.inspect_all(zip_data(), "2021-12", URL,
                                 {("2021-12", "001"): {"activo":64365,"pasivo":95009}})
        self.assertEqual(len(rows["bancos"]), 2)
        self.assertEqual(rows["filas_con_alguna_coincidencia"], 2)
        self.assertEqual(rows["bancos"][0]["hipotesis_escala"]["activo"]["coincidencias_legacy"][0]["divisor"], 1000)
        self.assertEqual(rows["bancos"][1]["hipotesis_escala"]["pasivo"]["campos_crudos"], ["0"])

    def test_real_2021_format_sums_columns_in_mm_without_divisor(self):
        """Formato real del B1 2021-12: rubro ya en MM CLP y varias columnas."""
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("b1202112014.txt",
                       "1160000\t0000000120796,00\t0000000000000,00\t0,00\t0000000000000,00\n"
                       "2160000\t0000000379967,00\t0000000000000,00\t0,00\t0000000000003,00\n")
        rows = audit.inspect_all(out.getvalue(), "2021-12", URL,
                                 {("2021-12", "014"): {"activo": 120796, "pasivo": 379970}})
        side = rows["bancos"][0]["hipotesis_escala"]["pasivo"]
        self.assertEqual(side["suma_columnas"], "379970")
        self.assertEqual(side["suma_con_divisor"]["1"], "379970")
        self.assertIn({"origen": "suma_columnas", "divisor": 1, "valor_mm_clp": "379970"},
                      side["coincidencias_legacy"])
        self.assertEqual(rows["filas_con_alguna_coincidencia"], 2)

    def test_wrong_month_and_invalid_amount_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "otro mes"):
            audit.inspect_all(zip_data("202111"), "2021-12", URL, {})
        rows = audit.inspect_all(zip_data(a="12\t-", b="ilegible"), "2021-12", URL, {})
        sides = rows["bancos"][0]["hipotesis_escala"]
        self.assertEqual(sides["activo"]["estado"], "campos_ausentes_o_ilegibles")
        self.assertEqual(sides["pasivo"]["estado"], "campos_ausentes_o_ilegibles")
        self.assertNotIn("suma_columnas", sides["activo"])

    def test_missing_candidates_and_duplicate_balance_fail_closed(self):
        empty = io.BytesIO()
        with zipfile.ZipFile(empty, "w") as z:
            z.writestr("b1202112001.txt", "1000000\t123")
        no_candidates = audit.inspect_all(empty.getvalue(), "2021-12", URL, {})
        self.assertIn("No se encontraron", no_candidates["advertencia"])
        blob = io.BytesIO()
        with zipfile.ZipFile(blob, "w") as z:
            z.writestr("a/b1202112001.txt", "1160000\t1000")
            z.writestr("b/b1202112001.txt", "1160000\t1000")
        with self.assertRaises(ValueError):
            audit.inspect_all(blob.getvalue(), "2021-12", URL, {})

    def test_checkpoint_only_after_all_months_complete(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            out, cp, legacy = tmp / "audit.json", tmp / "checkpoint.json", tmp / "legacy.json"
            legacy.write_text(json.dumps([{"periodo":"2021-12", "codigo_institucion":"001",
                                           "repo_activo_mm_clp":64365,"repo_pasivo_mm_clp":95009}]))
            with patch.object(probe, "resolve_links", return_value=({"2021-12": URL},set())), \
                 patch.object(probe, "read_public", return_value=zip_data()), \
                 patch.object(probe, "LEGACY", legacy):
                before = legacy.read_bytes()
                result = audit.run(output=out, checkpoint=cp, today=date(2022, 1, 15))
            self.assertEqual(result["estado"], "cotejo_exploratorio_no_publicado")
            self.assertEqual(json.loads(cp.read_text())["periodo"], "2021-12")
            self.assertEqual(legacy.read_bytes(), before)

    def test_failure_after_one_month_keeps_partial_evidence_without_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            legacy = tmp / "legacy.json"
            cp = tmp / "cp.json"
            out = tmp / "report.json"
            legacy.write_text(json.dumps([{"periodo": "2021-12", "codigo_institucion": "001",
                                           "repo_activo_mm_clp": 64365, "repo_pasivo_mm_clp": 95009}]))
            links = {"2021-12": URL, "2022-01": URL}
            with patch.object(probe, "resolve_links", return_value=(links, set())), \
                 patch.object(probe, "read_public", side_effect=[zip_data(), RuntimeError("CMF HTTP 503")]), \
                 patch.object(probe, "LEGACY", legacy):
                with self.assertRaises(RuntimeError):
                    audit.run(output=out, checkpoint=cp, today=date(2022, 2, 15))
            self.assertFalse(cp.exists())
            saved = json.loads(out.read_text())
            self.assertEqual(saved["estado"], "cotejo_incompleto_no_publicado")
            self.assertEqual(saved["periodo_fallido"], "2022-01")
            self.assertEqual(len(saved["periodos_completos"]), 1)

    def test_manual_does_not_move_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            legacy = tmp / "legacy.json"
            cp = tmp / "cp.json"
            legacy.write_text(json.dumps([{"periodo":"2021-12","codigo_institucion":"001",
                                           "repo_activo_mm_clp":64365,"repo_pasivo_mm_clp":95009}]))
            with patch.object(probe, "resolve_links", return_value=({"2021-12": URL},set())), \
                 patch.object(probe, "read_public", return_value=zip_data()), \
                 patch.object(probe, "LEGACY", legacy):
                audit.run(manual="2021-12", output=tmp/"report.json", checkpoint=cp, today=date(2022, 1, 15))
            self.assertFalse(cp.exists())


class SummaryTests(unittest.TestCase):
    def test_summary_compares_column_sum_per_month(self):
        from bancos.scripts import summarize_repo_audit as summary
        month = {
            "periodo": "2021-12", "sha256_zip": "ab" * 32, "advertencia": None,
            "candidatos_del_script_v2": {"activo": "1160000", "pasivo": "2160000"},
            "bancos": [
                {"codigo_banco": "001", "referencia_legacy_mm_clp": {"activo": 64365, "pasivo": 95009},
                 "hipotesis_escala": {"activo": {"suma_columnas": "64365"},
                                      "pasivo": {"suma_columnas": "95009"}}},
                {"codigo_banco": "016", "referencia_legacy_mm_clp": {"activo": 186753, "pasivo": 141178},
                 "hipotesis_escala": {"activo": {"suma_columnas": "186753"},
                                      "pasivo": {"suma_columnas": "141128"}}},
                {"codigo_banco": "031", "referencia_legacy_mm_clp": None,
                 "hipotesis_escala": {"activo": {"suma_columnas": "0"}, "pasivo": {"suma_columnas": "0"}}},
            ],
        }
        text = summary.summarize_month(month)
        self.assertIn("2021-12 bancos=3 cotejados=2 ambos_lados_ok=1", text)
        self.assertIn("001 a✓/1 p✓/1", text)
        self.assertIn("016 a✓/1 p✗(141128≠141178)", text)
        self.assertEqual(summary.side_status({"suma_columnas": "136409879738"}, 136409.88), "✓/1000000")
        self.assertEqual(summary.side_status({"suma_columnas": "0"}, 0), "✓/1,1000,1000000")
        self.assertEqual(summary.side_status({"suma_columnas": "99999"}, 1), "✗(99999≠1)")
        self.assertIn("sin_cuenta=[]", text)
        self.assertLessEqual(len(summary.summarize_month(month, limit=40)), 40)
        self.assertIn("sin_cuenta", summary.summarize_month(
            {"periodo": "2026-04", "bancos": [{"codigo_banco": "001", "referencia_legacy_mm_clp": None,
                                               "hipotesis_escala": {"activo": {"cuenta": "141000000",
                                                                               "estado": "ausente"}}}]}))
        self.assertIn("FALLO en 2021-12", summary.summarize(
            {"estado": "cotejo_incompleto_no_publicado", "periodo_fallido": "2021-12", "error": "ZIP inválido"}))


if __name__ == "__main__":
    unittest.main()

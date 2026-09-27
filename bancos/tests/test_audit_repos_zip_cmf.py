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


if __name__ == "__main__":
    unittest.main()

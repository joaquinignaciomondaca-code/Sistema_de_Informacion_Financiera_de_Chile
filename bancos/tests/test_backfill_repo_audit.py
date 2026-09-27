"""Pruebas sin red del barrido histórico REPO (no publica)."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from bancos.scripts import backfill_repo_audit as backfill
from bancos.scripts import probe_repos_zip_cmf as probe

URL = "https://www.cmfchile.cl/portal/estadisticas/626/articles-50166_recurso_1.zip"


def blob():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("b1200812001.txt", "1160000\t25,00\t10,00\n2160000\t70,00\t5,00")
    return out.getvalue()


class BackfillTests(unittest.TestCase):
    def test_cotejo_and_output_no_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "legacy.json"
            legacy.write_text(json.dumps([{"periodo": "2008-12", "codigo_institucion": "001",
                                          "repo_activo_mm_clp": 35, "repo_pasivo_mm_clp": 75}]))
            with patch.object(probe, "resolve_links", return_value=({"2008-12": URL}, set())), \
                 patch.object(probe, "read_public", return_value=blob()), \
                 patch.object(probe, "LEGACY", legacy):
                result = backfill.run(root / "out", 2008, 2008)
            self.assertEqual(result["resumen"]["meses_cotejados"], 1)
            self.assertEqual(result["resumen"]["lados_cotejados"], 2)
            self.assertEqual(result["resumen"]["discrepancias"], 0)
            self.assertEqual(json.loads((root / "out/2008.json").read_text())["meses"][0]["divisor_hipotesis"], 1)
            self.assertEqual(legacy.read_text(), json.dumps([{"periodo": "2008-12", "codigo_institucion": "001",
                                                               "repo_activo_mm_clp": 35, "repo_pasivo_mm_clp": 75}]))
            self.assertFalse((root / "out/checkpoint.json").exists())

    def test_mismatch_and_missing_reference(self):
        month = {"periodo": "2008-12", "sha256_zip": "a", "advertencia": None,
                 "bancos": [
                     {"codigo_banco": "001", "referencia_legacy_mm_clp": {"activo": 36, "pasivo": 75},
                      "hipotesis_escala": {"activo": {"suma_columnas": "35", "cuenta": "1160000"},
                                           "pasivo": {"estado": "ausente", "cuenta": "2160000"}}},
                     {"codigo_banco": "002", "referencia_legacy_mm_clp": None, "hipotesis_escala": {}},
                 ]}
        result = backfill.comparisons(month)
        self.assertEqual(result["lados_cotejados"], 0)
        self.assertEqual(len(result["discrepancias"]), 2)
        self.assertEqual(result["bancos_sin_fila_legacy"], ["002"])

    def test_no_silent_skip_ambiguous_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy.json"
            legacy.write_text(json.dumps([{"periodo": "2008-12", "codigo_institucion": "001",
                                          "repo_activo_mm_clp": 35, "repo_pasivo_mm_clp": 75}]))
            with patch.object(probe, "resolve_links", return_value=({}, {"2008-12"})), \
                 patch.object(probe, "LEGACY", legacy):
                result = backfill.run(Path(tmp) / "out", 2008, 2008)
            self.assertEqual(result["estado"], "auditoria_historica_incompleta_no_publicada")
            self.assertEqual(result["errores"], [{"periodo": "2008-12", "causa": "ZIP ambiguo"}])
            self.assertEqual(result["resumen"]["meses_cotejados"], 0)


if __name__ == "__main__":
    unittest.main()

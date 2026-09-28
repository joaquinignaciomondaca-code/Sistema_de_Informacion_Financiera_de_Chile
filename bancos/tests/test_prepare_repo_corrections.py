import unittest
import importlib.util
from pathlib import Path
from bancos.scripts.prepare_repo_corrections import split_legacy


class CorrectionsTest(unittest.TestCase):
    def test_split_drops_unverified_identity_and_false_flow_not_balances(self):
        def row(code):
            return {"id_repo": f"{code}_2020-01", "periodo": "2020-01",
                    "codigo_institucion": code, "rut": "97.018.000-1",
                    "razon_social": "Nombre actual", "nombre_fantasia": "Nombre actual",
                    "total_transado_mm_usd": 3, "repo_activo_mm_clp": 100,
                    "repo_pasivo_mm_clp": 200}
        banks, totals, affiliates = split_legacy([row("014"), row("900"), row("816")])
        self.assertEqual((len(banks), len(totals), len(affiliates)), (1, 1, 1))
        self.assertEqual(affiliates[0]["codigo_institucion"], "816")
        self.assertEqual(banks[0]["repo_activo_mm_clp"], 100)
        for field in ("rut", "razon_social", "nombre_fantasia", "total_transado_mm_usd"):
            self.assertNotIn(field, banks[0])

    def test_legacy_extractor_cannot_publish(self):
        path = Path(__file__).resolve().parents[1] / "scripts/02_extract_bancos_repos_series.py"
        spec = importlib.util.spec_from_file_location("legacy_repo_extractor", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaisesRegex(RuntimeError, "bloqueado"):
            module.extract_bancos_repos_series()

    def test_duplicate_period_code_fails_closed(self):
        row = {"id_repo": "014_2020-01", "codigo_institucion": "014", "periodo": "2020-01"}
        with self.assertRaises(ValueError):
            split_legacy([row, row])


if __name__ == "__main__":
    unittest.main()

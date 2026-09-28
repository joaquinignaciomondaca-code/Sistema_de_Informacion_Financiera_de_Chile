"""El cotejo numérico no debe aprobar metadatos materialmente incorrectos."""
import unittest
from bancos.scripts.audit_repo_release_gate import audit


def row(code, rut, period="2020-01", active=12.0, passive=5.0):
    return {"codigo_institucion": code, "rut": rut, "periodo": period,
            "repo_activo_mm_usd": active, "repo_pasivo_mm_usd": passive,
            "total_transado_mm_usd": active + passive,
            "id_repo": f"{code}_{period}"}


class ReleaseGateTests(unittest.TestCase):
    def test_simultaneous_rut_aggregate_and_flow_block_approval(self):
        report = audit([row("014", "97.018.000-1"), row("504", "97.018.000-1"),
                        row("900", "99.999.900-K")])
        self.assertEqual(report["estado"], "NO_APROBADO")
        self.assertEqual(report["rut_simultaneo_conflictivo"]["meses_conflictivos"], 1)
        self.assertEqual(report["agregados"]["filas"], 1)
        self.assertEqual(report["columna_transado_suma_saldos"], 3)

    def test_foreign_affiliate_does_not_count_as_chilean_bank(self):
        report = audit([row("816", "99.999.816-0")])
        self.assertEqual(report["filiales_extranjeras"]["filas"], 1)
        self.assertIn("Filiales extranjeras se mezclan con bancos establecidos en Chile", report["bloqueos"])
        self.assertEqual(report["estado"], "NO_APROBADO")

    def test_non_overlapping_rut_is_not_simultaneous_conflict(self):
        report = audit([row("014", "97.018.000-1", "2020-01"),
                        row("504", "97.018.000-1", "2020-02")])
        self.assertEqual(report["rut_simultaneo_conflictivo"]["meses_conflictivos"], 0)
        self.assertEqual(report["estado"], "NO_APROBADO")
        self.assertTrue(report["pendiente_de_validacion_independiente"])

    def test_missing_fields_cannot_approve(self):
        report = audit([{"codigo_institucion": "001"}])
        self.assertEqual(report["estado"], "NO_APROBADO")
        self.assertEqual(len(report["filas_invalidas"]), 1)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from datetime import date
from pathlib import Path

from unittest import mock

import bancos.scripts.publish_cmf_bank_period as mod
from bancos.scripts.publish_cmf_bank_period import (
    catch_up,
    is_period_published,
    next_unpublished_period,
    previous_month,
    select_period,
    validate_release,
)


class PublishCmfBankPeriodTests(unittest.TestCase):
    def _fake_publisher(self, manifest, fail_on=()):
        def publisher(period, dry_run=False):
            if period in fail_on:
                raise RuntimeError("CMF aún no publica " + period)
            if dry_run:
                return {"published_changed": False}
            manifest["periods"].append({"period": period})
            return {"published_changed": True, "period": period}
        return publisher

    def test_catch_up_publishes_all_pending_closed_months_in_order(self):
        manifest = {"periods": []}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            result = catch_up(False, 24, date(2026, 10, 15), self._fake_publisher(manifest))
        self.assertEqual(result["periods"], ["2026-07", "2026-08", "2026-09"])
        self.assertTrue(result["published_changed"])
        self.assertEqual(result["period"], "2026-09")

    def test_catch_up_backfills_history_from_start_and_skips_published(self):
        manifest = {"periods": [{"period": "2026-07"}]}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            result = catch_up(False, 24, date(2026, 10, 15), self._fake_publisher(manifest), start="2026-04")
        self.assertEqual(result["periods"], ["2026-04", "2026-05", "2026-06", "2026-08", "2026-09"])

    def test_catch_up_keeps_validated_months_when_a_later_one_fails(self):
        manifest = {"periods": []}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            result = catch_up(False, 24, date(2026, 10, 15), self._fake_publisher(manifest, fail_on={"2026-09"}))
        self.assertEqual(result["periods"], ["2026-07", "2026-08"])
        self.assertEqual(result["status"], "partial")
        self.assertIn("2026-09", result["stopped_error"])

    def test_catch_up_first_failure_is_an_error_and_dry_run_does_not_loop(self):
        manifest = {"periods": []}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            with self.assertRaises(RuntimeError):
                catch_up(False, 24, date(2026, 10, 15), self._fake_publisher(manifest, fail_on={"2026-07"}))
            result = catch_up(True, 24, date(2026, 10, 15), self._fake_publisher(manifest))
        self.assertEqual(result["periods"], [])
        self.assertFalse(result["published_changed"])

    def test_previous_month_handles_year_boundary(self):
        self.assertEqual(previous_month(date(2027, 1, 15)), "2026-12")
        self.assertEqual(previous_month(date(2026, 10, 15)), "2026-09")

    def test_monthly_scheduler_selects_only_next_missing_closed_period(self):
        today = date(2026, 10, 15)
        self.assertEqual(next_unpublished_period({"periods": []}, today), "2026-07")
        self.assertEqual(next_unpublished_period({"periods": [{"period": "2026-07"}]}, today), "2026-08")
        self.assertEqual(next_unpublished_period({"periods": [{"period": "2026-07"}, {"period": "2026-09"}]}, today), "2026-08")
        self.assertEqual(next_unpublished_period({"periods": [{"period": "2026-08"}]}, date(2026, 8, 15)), "2026-07")
        self.assertIsNone(next_unpublished_period({"periods": [{"period": "2026-07"}, {"period": "2026-08"}]}, date(2026, 8, 15)))

    def test_dispatch_period_cannot_backfill_or_skip_and_duplicate_is_noop(self):
        today = date(2026, 10, 15)
        manifest = {"periods": []}
        self.assertEqual(select_period("2026-07", manifest, today), "2026-07")
        for rejected in ("2026-08", "2026-09", "2026-10"):
            with self.subTest(period=rejected), self.assertRaisesRegex(ValueError, "No se permite backfill"):
                select_period(rejected, manifest, today)

        with_published = {"periods": [{"period": "2026-07"}]}
        self.assertEqual(select_period("2026-07", with_published, today), "2026-07")
        self.assertEqual(select_period("2026-08", with_published, today), "2026-08")

    def test_duplicate_period_is_skipped_and_orphan_partition_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            period_dir = output / "2026-07"
            period_dir.mkdir()
            (period_dir / "lineas.parquet").write_bytes(b"not empty")
            self.assertTrue(is_period_published(
                "2026-07",
                {"periods": [{"period": "2026-07", "file": "outputs/bancos/cmf_b1_b2_r1/2026-07/lineas.parquet"}]},
                output,
            ))
            with self.assertRaisesRegex(RuntimeError, "no está registrada"):
                is_period_published("2026-07", {"periods": []}, output)

    def test_release_requires_b1_and_key_r1_tieouts_for_all_named_banks(self):
        rows = []
        file_reports = []
        workbook_rows = []
        bank_names = [f"Banco Prueba {index:02d}" for index in range(17)]
        codes = [f"{index:03d}" for index in range(1, 18)]
        for code, name in zip(codes, bank_names):
            source_files = {"B1": 0, "B2": 0, "R1": 0}
            source_files["B1"] += 1
            rows.append({
                "id": f"2026-07:{code}:MB1:100000000:1",
                "periodo": "2026-07",
                "codigo_institucion": code,
                "nombre_institucion_fuente": name,
                "familia_archivo_fuente": "B1",
                "modelo_cmf": "MB1",
                "codigo_cuenta": "100000000",
                "glosa_cuenta": "Cuenta de prueba",
                "numero_fila_fuente": 2,
                "importes_fuente_decimal": ["25", "25", "25", "25"],
            })
            source_files["B2"] += 1
            rows.append({
                "id": f"2026-07:{code}:MB2:143000000:1",
                "periodo": "2026-07",
                "codigo_institucion": code,
                "nombre_institucion_fuente": name,
                "familia_archivo_fuente": "B2",
                "modelo_cmf": "MB2",
                "codigo_cuenta": "143000000",
                "glosa_cuenta": "Cuenta de prueba",
                "numero_fila_fuente": 2,
                "importes_fuente_decimal": ["0", "0", "0", "0"],
            })
            for occurrence, (account, amount) in enumerate((("590000000", "5"), ("594000000", "6")), start=1):
                source_files["R1"] += 1
                rows.append({
                    "id": f"2026-07:{code}:MR1:{account}:{occurrence}",
                    "periodo": "2026-07",
                    "codigo_institucion": code,
                    "nombre_institucion_fuente": name,
                    "familia_archivo_fuente": "R1",
                    "modelo_cmf": "MR1",
                    "codigo_cuenta": account,
                    "glosa_cuenta": "Cuenta de resultado de prueba",
                    "numero_fila_fuente": occurrence + 1,
                    "importes_fuente_decimal": [amount],
                })
            for family in ("B1", "B2", "R1"):
                file_reports.append({
                    "codigo_institucion": code,
                    "nombre_institucion_fuente": name,
                    "familia_archivo_fuente": family,
                })
            workbook_rows.extend([
                {"sheet": "Est. Situación Financ. Bancos", "row_number": 2, "values": [name, 0.0001]},
                {"sheet": "Est. del Resultado Bancos", "row_number": 2, "values": [name, 0.000005, 0.000006]},
            ])

        report = {
            "period": "2026-07",
            "institution_count": 17,
            "institution_codes": codes,
            "file_count": 51,
            "file_reports": file_reports,
            "account_rows_by_family": {"B1": 17, "B2": 17, "R1": 34},
        }
        result = validate_release(rows, report, workbook_rows)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["individual_institutions_tied_out"], 17)
        self.assertEqual(result["total_account_rows"], 68)

    def test_release_fails_on_unmatched_b1(self):
        rows = []
        file_reports = []
        workbook_rows = []
        codes = [f"{index:03d}" for index in range(1, 18)]
        for index, code in enumerate(codes):
            name = f"Banco Prueba {index:02d}"
            rows.append({
                "id": f"2026-07:{code}:MB1:100000000:1", "periodo": "2026-07",
                "codigo_institucion": code, "familia_archivo_fuente": "B1",
                "codigo_cuenta": "100000000", "glosa_cuenta": "TOTAL ACTIVOS", "numero_fila_fuente": 2,
                "importes_fuente_decimal": ["100", "0", "0", "0"],
            })
            rows.append({
                "id": f"2026-07:{code}:MB2:143000000:1", "periodo": "2026-07",
                "codigo_institucion": code, "familia_archivo_fuente": "B2",
                "codigo_cuenta": "143000000", "glosa_cuenta": "Cuenta individual", "numero_fila_fuente": 2,
                "importes_fuente_decimal": ["0", "0", "0", "0"],
            })
            for occurrence, account in enumerate(("590000000", "594000000"), start=1):
                rows.append({
                    "id": f"2026-07:{code}:MR1:{account}:{occurrence}", "periodo": "2026-07",
                    "codigo_institucion": code, "familia_archivo_fuente": "R1",
                    "codigo_cuenta": account, "glosa_cuenta": "Cuenta de resultado", "numero_fila_fuente": occurrence + 1,
                    "importes_fuente_decimal": ["5"],
                })
            file_reports.extend({"codigo_institucion": code, "nombre_institucion_fuente": name, "familia_archivo_fuente": family} for family in ("B1", "B2", "R1"))
            workbook_rows.extend([
                {"sheet": "Est. Situación Financ. Bancos", "row_number": 2, "values": [name, 0.000102 if index == 16 else 0.0001]},
                {"sheet": "Est. del Resultado Bancos", "row_number": 2, "values": [name, 0.000005]},
            ])
        report = {
            "period": "2026-07", "institution_count": 17, "institution_codes": codes,
            "file_count": 51, "file_reports": file_reports,
            "account_rows_by_family": {"B1": 17, "B2": 17, "R1": 34},
        }
        with self.assertRaisesRegex(RuntimeError, "no concilia con el XLSX"):
            validate_release(rows, report, workbook_rows)


    @staticmethod
    def _release(xlsx_totals: dict[int, float]):
        rows, file_reports, workbook_rows = [], [], []
        codes = [f"{index:03d}" for index in range(1, 18)]
        for index, code in enumerate(codes):
            name = f"Banco Prueba {index:02d}"
            rows.append({"id": f"p:{code}:B1", "periodo": "2026-07", "codigo_institucion": code,
                         "familia_archivo_fuente": "B1", "codigo_cuenta": "100000000", "glosa_cuenta": "TOTAL ACTIVOS",
                         "numero_fila_fuente": 2, "importes_fuente_decimal": ["1000000000", "0", "0", "0"]})
            rows.append({"id": f"p:{code}:B2", "periodo": "2026-07", "codigo_institucion": code,
                         "familia_archivo_fuente": "B2", "codigo_cuenta": "143000000", "glosa_cuenta": "x",
                         "numero_fila_fuente": 2, "importes_fuente_decimal": ["0", "0", "0", "0"]})
            rows.append({"id": f"p:{code}:R1", "periodo": "2026-07", "codigo_institucion": code,
                         "familia_archivo_fuente": "R1", "codigo_cuenta": "590000000", "glosa_cuenta": "x",
                         "numero_fila_fuente": 2, "importes_fuente_decimal": ["5000000"]})
            file_reports.extend({"codigo_institucion": code, "nombre_institucion_fuente": name} for _ in range(3))
            workbook_rows += [
                {"sheet": "Est. Situación Financ. Bancos", "row_number": 10 + index, "values": [name, xlsx_totals.get(index, 1000.0)]},
                {"sheet": "Est. del Resultado Bancos", "row_number": 10 + index, "values": [name, 5.0]},
            ]
        report = {"period": "2026-07", "institution_count": 17, "institution_codes": codes, "file_count": 51,
                  "file_reports": file_reports, "account_rows_by_family": {"B1": 17, "B2": 17, "R1": 17}}
        return validate_release(rows, report, workbook_rows)

    def test_one_minor_b1_discrepancy_is_published_and_declared(self):
        result = self._release({5: 1000.2})  # 0,02 % (caso Ripley 2025-01)
        self.assertEqual(len(result["b1_discrepancias_menores"]), 1)
        d = result["b1_discrepancias_menores"][0]
        self.assertEqual(d["codigo_institucion"], "006")
        self.assertEqual(d["diferencia_relativa"], "0.000200")
        check = next(c for c in result["institution_checks"] if c["codigo_institucion"] == "006")
        self.assertEqual(check["b1_total_activos"], "discrepancia_menor_declarada")

    def test_two_minor_discrepancies_or_large_one_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError, "no concilia con el XLSX"):
            self._release({5: 1000.2, 7: 1000.1})
        with self.assertRaisesRegex(RuntimeError, "no concilia con el XLSX"):
            self._release({5: 1002.0})  # 0,2 %


if __name__ == "__main__":
    unittest.main()

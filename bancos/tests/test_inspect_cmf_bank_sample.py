import unittest
import zipfile
from io import BytesIO

from bancos.scripts.inspect_cmf_bank_sample import inspect_zip


class InspectCmfBankSampleTests(unittest.TestCase):
    def make_zip(self):
        out = BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("b1202607001.txt", "001\tBANCO DE CHILE\n141000000\t00100\t00000\t00000\t00000\n")
            zf.writestr("r1202607001.txt", "001\tBANCO DE CHILE\n510000000\t00020\t00000\t00000\t00000\n")
            zf.writestr("b2202607001.txt", "001\tBANCO DE CHILE\n143000000\t00030\t00000\t00000\t00000\n")
            zf.writestr("r2202607001.txt", "001\tBANCO DE CHILE\n520000000\t00040\t00000\t00000\t00000\n")
            zf.writestr("b1202607009.txt", "009\tBANCO INTERNACIONAL\n")
        return out.getvalue()

    def test_summarizes_financial_file_types_and_requested_bank(self):
        report = inspect_zip(self.make_zip(), "2026-07", "001")
        self.assertEqual(report["archive_member_count"], 5)
        self.assertEqual(report["matching_period_financial_file_count"], 5)
        self.assertEqual(set(report["bank_files"]), {"B1", "R1", "B2", "R2"})
        self.assertEqual(report["bank_files"]["B1"]["nonempty_lines"], 2)
        self.assertEqual(report["bank_files"]["R1"]["tab_field_counts"], {2: 1, 5: 1})
        self.assertEqual(report["bank_files"]["B1"]["encoding"], "ascii-compatible (UTF-8/Latin-1 indistinguishable)")

    def test_fails_if_required_results_file_is_missing(self):
        out = BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("b1202607001.txt", "001\tBANCO DE CHILE\n")
        with self.assertRaisesRegex(RuntimeError, "missing_core=.*R1"):
            inspect_zip(out.getvalue(), "2026-07", "001")


if __name__ == "__main__":
    unittest.main()

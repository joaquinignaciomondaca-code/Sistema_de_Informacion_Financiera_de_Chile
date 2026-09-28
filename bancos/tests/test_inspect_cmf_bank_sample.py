import unittest
import zipfile
from io import BytesIO

from bancos.scripts.inspect_cmf_bank_sample import inspect_zip, resolve_resource_from_article_links


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

    def test_resolves_blank_resource_anchor_by_matching_article_id_and_period(self):
        links = [
            {"href": "/portal/estadisticas/626/w4-article-123.html", "text": "Balance y Estado de Situación Bancos Agosto 2026"},
            {"href": "/portal/estadisticas/626/articles-123_recurso_1.zip?ts=123", "text": ""},
            {"href": "/portal/estadisticas/626/w4-article-456.html", "text": "Balance y Estado de Situación Bancos Julio 2026"},
            {"href": "/portal/estadisticas/626/articles-456_recurso_1.zip?ts=456", "text": ""},
        ]
        result = resolve_resource_from_article_links(links, "https://www.cmfchile.cl/portal/estadisticas/626/index.html", "2026-08", ".zip")
        self.assertEqual(result, ("https://www.cmfchile.cl/portal/estadisticas/626/articles-123_recurso_1.zip?ts=123", ""))

    def test_resolves_bank_workbook_resource_by_article_id(self):
        links = [
            {"href": "/portal/estadisticas/626/w4-article-789.html", "text": "Reporte Mensual Bancario Agosto 2026"},
            {"href": "/portal/estadisticas/626/articles-789_recurso_1.xlsx?ts=789", "text": ""},
        ]
        result = resolve_resource_from_article_links(links, "https://www.cmfchile.cl/portal/estadisticas/626/index.html", "2026-08", ".xlsx")
        self.assertEqual(result[0], "https://www.cmfchile.cl/portal/estadisticas/626/articles-789_recurso_1.xlsx?ts=789")

    def test_fails_if_balance_file_is_missing(self):
        out = BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("r1202607001.txt", "001\tBANCO DE CHILE\n")
        with self.assertRaisesRegex(RuntimeError, "missing_core=.*B1"):
            inspect_zip(out.getvalue(), "2026-07", "001")


if __name__ == "__main__":
    unittest.main()

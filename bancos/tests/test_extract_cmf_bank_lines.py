import json
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

from bancos.scripts.extract_cmf_bank_lines import extract_archive, parse_amount, write_review_outputs


class ExtractCmfBankLinesTests(unittest.TestCase):
    @staticmethod
    def make_zip(missing=None, duplicate=None, inconsistent_header=False):
        missing = missing or set()
        duplicate = duplicate or set()
        output = BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            examples = {
                "B1": "100000000\t0000000000001\t0000000000002\t0000000000003\t0000000000004\n",
                "B2": "143000000\t-0000000000001\t0000000000000\t0000000000000\t0000000000000\n",
                "R1": "411000000\t0000000000009\n",
            }
            for bank in ("001", "009"):
                for family, body in examples.items():
                    key = (bank, family)
                    if key in missing:
                        continue
                    bank_name = "BANCO DE CHILE" if bank == "001" else "BANCO INTERNACIONAL"
                    header_name = "NOMBRE DISTINTO" if inconsistent_header and family == "R1" and bank == "001" else bank_name
                    member = f"{family.lower()}202607{bank}.txt"
                    archive.writestr(member, f"{bank}\t{header_name}\n{body}")
                    if key in duplicate:
                        archive.writestr(f"copia/{member}", f"{bank}\t{header_name}\n{body}")
            archive.writestr("c1202607001.txt", "001\tBANCO DE CHILE\n")
        return output.getvalue()

    def test_extracts_three_families_and_keeps_row_order_separate(self):
        rows, report = extract_archive(self.make_zip(), "2026-07", "https://cmf.example/source.zip")
        self.assertEqual(report["institution_count"], 2)
        self.assertEqual(report["file_count"], 6)
        self.assertEqual(report["account_rows_by_family"], {"B1": 2, "B2": 2, "R1": 2})
        row = next(row for row in rows if row["codigo_institucion"] == "001" and row["modelo_cmf"] == "MB1")
        self.assertEqual(row["nivel_consolidacion"], "consolidado_global")
        self.assertEqual(row["tipo_estado"], "balance")
        self.assertEqual(row["codigo_cuenta"], "100000000")
        self.assertEqual(row["numero_fila_fuente"], 2)
        self.assertEqual(row["importes_fuente_raw"], ["0000000000001", "0000000000002", "0000000000003", "0000000000004"])
        self.assertIsNone(row["rut"])
        self.assertIsNone(row["razon_social"])
        self.assertEqual(row["nombre_institucion_fuente"], "BANCO DE CHILE")
        self.assertIsNone(row["glosa_cuenta"])
        result = next(row for row in rows if row["codigo_institucion"] == "001" and row["modelo_cmf"] == "MR1")
        self.assertEqual(result["nivel_consolidacion"], "consolidado_global")
        self.assertEqual(result["tipo_estado"], "resultados")
        individual = next(row for row in rows if row["codigo_institucion"] == "001" and row["modelo_cmf"] == "MB2")
        self.assertEqual(individual["nivel_consolidacion"], "individual")
        self.assertEqual(individual["importes_fuente_decimal"][0], "-1")

    def test_rejects_missing_or_duplicate_source(self):
        with self.assertRaisesRegex(RuntimeError, "Incomplete or duplicate"):
            extract_archive(self.make_zip(missing={("009", "R1")}), "2026-07")
        with self.assertRaisesRegex(RuntimeError, "Incomplete or duplicate"):
            extract_archive(self.make_zip(duplicate={("001", "B1")}), "2026-07")

    def test_rejects_header_mismatch_between_statement_families(self):
        with self.assertRaisesRegex(RuntimeError, "header names differ"):
            extract_archive(self.make_zip(inconsistent_header=True), "2026-07")

    def test_amounts_are_exact_and_fail_closed(self):
        self.assertEqual(parse_amount("-00000123,450"), "-123.450")
        with self.assertRaisesRegex(ValueError, "Invalid CMF amount"):
            parse_amount("1.234,56")

    def test_writes_review_jsonl_and_report_without_publication(self):
        rows, report = extract_archive(self.make_zip(), "2026-07")
        with tempfile.TemporaryDirectory() as directory:
            write_review_outputs(rows, report, Path(directory))
            jsonl = (Path(directory) / "bancos_cmf_b1_b2_r1_lineas.jsonl").read_text(encoding="utf-8").splitlines()
            saved_report = json.loads((Path(directory) / "extraction_report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(jsonl), len(rows))
            self.assertFalse(saved_report["validation"]["published"])
            self.assertEqual(json.loads(jsonl[0])["fecha_corte"], "2026-07-31")


if __name__ == "__main__":
    unittest.main()

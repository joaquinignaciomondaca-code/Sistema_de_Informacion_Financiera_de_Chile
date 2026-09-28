import json
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

from bancos.scripts.extract_cmf_bank_lines import extract_archive, parse_account_model, parse_amount, reconcile_to_inspection, write_review_outputs


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
            archive.writestr(
                "metadata/modelo_mb1.txt",
                "CUENTA\tRUBRO\tLINEA\tITEM\tGLOSA\n"
                "100000000\t10000\t00\t00\tTOTAL ACTIVOS\n"
                "105000000\t10500\t00\t00\tEFECTIVO\n"
                "105000100\t10500\t01\t00\tEfectivo disponible\n"
                "105000101\t10500\t01\t01\tCaja\n",
            )
            archive.writestr(
                "metadata/modelo_mb2.txt",
                "CUENTA\tRUBRO\tLINEA\tITEM\tGLOSA\n"
                "143000000\t14300\t00\t00\tAdeudado por bancos\n",
            )
            archive.writestr(
                "metadata/modelo_mr1.txt",
                "CUENTA\tRUBRO\tLINEA\tITEM\tGLOSA\n"
                "411000000\t41100\t00\t00\tINGRESOS POR INTERESES\n"
                "411100000\t41110\t00\t00\tIntereses activos\n",
            )
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
        self.assertEqual((row["rubro"], row["linea"], row["item"]), ("10000", "00", "00"))
        self.assertEqual(row["glosa_cuenta"], "TOTAL ACTIVOS")
        self.assertEqual(row["tipo_linea"], "total")
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

    def test_account_model_maps_hierarchy_and_line_type(self):
        model = parse_account_model(
            "CUENTA\tRUBRO\tLINEA\tITEM\tGLOSA\n"
            "100000000\t10000\t00\t00\tTOTAL ACTIVOS\n"
            "105000000\t10500\t00\t00\tEfectivo\n"
            "105000100\t10500\t01\t00\tCaja y bancos\n"
            "105000101\t10500\t01\t01\tCaja\n",
            "metadata/modelo_mb1.txt",
        )
        self.assertEqual(model["100000000"]["tipo_linea"], "total")
        self.assertEqual(model["105000000"]["tipo_linea"], "subtotal")
        self.assertEqual(model["105000101"]["tipo_linea"], "detalle")

    def test_amounts_are_exact_and_fail_closed(self):
        self.assertEqual(parse_amount("-00000123,450"), "-123.450")
        with self.assertRaisesRegex(ValueError, "Invalid CMF amount"):
            parse_amount("1.234,56")

    def test_reconciles_b1_total_and_r1_accounts_to_xlsx_rows(self):
        rows, _ = extract_archive(self.make_zip(), "2026-07")
        inspection = {
            "workbook": {
                "bank_rows": [
                    {"sheet": "Est. Situación Financ. Bancos", "row_number": 17, "values": [None, "Banco de Chile", 0.00001]},
                    {"sheet": "Est. del Resultado Bancos", "row_number": 17, "values": [None, "Banco de Chile", 0.000009]},
                ]
            }
        }
        result = reconcile_to_inspection(rows, inspection)
        self.assertEqual(result["b1_status"], "passed")
        self.assertEqual(result["r1_status"], "matched")
        self.assertEqual(result["r1_exact_account_matches_in_xlsx"][0]["codigo_cuenta"], "411000000")

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


class NormalizeNameAccentTests(unittest.TestCase):
    def test_accented_workbook_name_matches_plain_zip_name(self):
        from bancos.scripts.extract_cmf_bank_lines import normalize_name
        from bancos.scripts.inspect_cmf_bank_sample import norm
        for f in (normalize_name, norm):
            self.assertEqual(f("Banco de Crédito e Inversiones"), f("BANCO DE CREDITO E INVERSIONES"))
            self.assertEqual(f("Itaú Corpbanca"), "ITAUCORPBANCA")

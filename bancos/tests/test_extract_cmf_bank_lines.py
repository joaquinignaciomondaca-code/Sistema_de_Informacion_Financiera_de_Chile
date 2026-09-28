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


class LegacyFormatTests(unittest.TestCase):
    """Formato CMF 2022-01..2024-04: Instrucciones/Modelo-*.txt y montos ' 123,00<TAB>'."""

    @staticmethod
    def legacy_model(title, rows):
        body = "".join(f"{code}\t{glosa}\n" for code, glosa in rows)
        return (f"Descriptores de cuentas usados en reporte {title}\n\nPeriodo: Año 2022 - Mes: Enero\n\n"
                f"CUENTA\tGLOSA\n{body}\n\nMás información\nhttps://www.cmfchile.cl/x.html\n").encode("latin-1")

    def make_zip(self):
        out = BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            for bank, name in (("001", "BANCO DE CHILE"), ("009", "BANCO INTERNACIONAL")):
                z.writestr(f"202201/b1202201{bank}.txt", f"{bank}\t{name}\n100000000\t 0000000000010,00\t 0000000000002,00\t 0000000000003,00\t 0000000000004,00\t\n")
                z.writestr(f"202201/b2202201{bank}.txt", f"{bank}\t{name}\n143000000\t-0000000000001,00\t 0000000000000,00\t 0000000000000,00\t 0000000000000,00\t\n")
                z.writestr(f"202201/r1202201{bank}.txt", f"{bank}\t{name}\n411000000\t 0149769961175,00\t\n")
            z.writestr("202201/Instrucciones/Modelo-MB1.txt", self.legacy_model("MB1", [
                ("100000000", "TOTAL ACTIVOS"), ("105000000", "EFECTIVO Y DEPÓSITOS EN BANCOS"),
                ("105000100", "          Efectivo      ")]))
            z.writestr("202201/Instrucciones/Modelo-MB2.txt", self.legacy_model("MB2", [("143000000", "     Adeudado por bancos")]))
            z.writestr("202201/Instrucciones/Modelo-MR1.txt", self.legacy_model("MR1", [("411000000", "INGRESOS POR INTERESES")]))
            z.writestr("202201/Instrucciones/LEAME.TXT", "DOCUMENTACION\n")
        return out.getvalue()

    def test_legacy_zip_is_extracted_with_derived_hierarchy(self):
        rows, report = extract_archive(self.make_zip(), "2022-01", "https://cmf.example/2022.zip")
        self.assertEqual(report["account_rows_by_family"], {"B1": 2, "B2": 2, "R1": 2})
        b1 = next(r for r in rows if r["codigo_institucion"] == "001" and r["modelo_cmf"] == "MB1")
        self.assertEqual(b1["importes_fuente_decimal"], ["10.00", "2.00", "3.00", "4.00"])
        self.assertEqual((b1["rubro"], b1["linea"], b1["item"]), ("10000", "00", "00"))
        self.assertEqual(b1["tipo_linea"], "total")
        b2 = next(r for r in rows if r["modelo_cmf"] == "MB2")
        self.assertEqual(b2["importes_fuente_decimal"][0], "-1.00")
        self.assertEqual(b2["glosa_cuenta"], "Adeudado por bancos")

    def test_legacy_model_derives_rubro_linea_item_and_skips_footer(self):
        text = self.legacy_model("MB1", [("100000000", "TOTAL ACTIVOS"), ("105000100", "   Efectivo ")]).decode("latin-1")
        model = parse_account_model(text, "Modelo-MB1.txt")
        self.assertEqual(set(model), {"100000000", "105000100"})
        self.assertEqual(model["105000100"], {"rubro": "10500", "linea": "01", "item": "00", "glosa_cuenta": "Efectivo", "tipo_linea": "detalle"})


class RenamedBankFallbackTests(unittest.TestCase):
    def rows(self, total="40897890105783.00", r1="1000000.00"):
        base = {"codigo_institucion": "039", "numero_fila_fuente": 2, "glosa_cuenta": "x"}
        return [
            {**base, "familia_archivo_fuente": "B1", "codigo_cuenta": "100000000", "importes_fuente_decimal": [total, "0", "0", "0"]},
            {**base, "familia_archivo_fuente": "R1", "codigo_cuenta": "590000000", "importes_fuente_decimal": [r1]},
        ]

    def inspection(self, cells_bal, cells_res):
        rows = [{"sheet": "Est. Situación Financ. Bancos", "row_number": n, "values": v} for n, v in cells_bal]
        rows += [{"sheet": "Est. del Resultado Bancos ", "row_number": n, "values": v} for n, v in cells_res]
        return {"workbook": {"bank_rows": rows}}

    def test_renamed_bank_matches_by_unique_amount(self):
        insp = self.inspection([(10, ["Itaú Corpbanca", 40897890.105783]), (11, ["Otro", 5.0])],
                               [(10, ["Itaú Corpbanca", 1.0])])
        out = reconcile_to_inspection(self.rows(), insp, bank_code="039", bank_name="BANCO ITAÚ CHILE")
        self.assertEqual(out["match_mode"], "amount_only")
        self.assertEqual(out["b1_status"], "passed")
        self.assertEqual(len(out["r1_exact_account_matches_in_xlsx"]), 1)

    def test_amount_only_rejects_ambiguous_rows(self):
        insp = self.inspection([(10, ["A", 40897890.105783]), (11, ["B", 40897890.105783])], [])
        out = reconcile_to_inspection(self.rows(), insp, bank_code="039", bank_name="BANCO ITAÚ CHILE")
        self.assertNotEqual(out["b1_status"], "passed")


class Plan2024June(unittest.TestCase):
    def test_single_plan_de_cuentas_and_unpadded_bank_code(self):
        out = BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            for bank, code, name in (("001", "1", "BANCO DE CHILE"), ("009", "9", "BANCO INTERNACIONAL")):
                z.writestr(f"202406/b1202406{bank}.txt", f"{code}\t{name}\n100000000\t000000000000010\t000000000000000\t000000000000000\t000000000000000\n")
                z.writestr(f"202406/b2202406{bank}.txt", f"{code}\t{name}\n143000000\t000000000000001\t000000000000000\t000000000000000\t000000000000000\n")
                z.writestr(f"202406/r1202406{bank}.txt", f"{code}\t{name}\n411000000\t000000000000005\n")
            z.writestr("202406/metadata/plan_de_cuentas.txt",
                       "CUENTA\tDESCRIPCION\n100000000\tTOTAL ACTIVOS\n143000000\tAdeudado por bancos\n"
                       "143000000\tAdeudado por bancos\n411000000\tINGRESOS POR INTERESES\n".encode("latin-1"))
        rows, report = extract_archive(out.getvalue(), "2024-06", "https://cmf.example/2024-06.zip")
        self.assertEqual(report["account_rows_by_family"], {"B1": 2, "B2": 2, "R1": 2})
        self.assertEqual({r["codigo_institucion"] for r in rows}, {"001", "009"})

    def test_bank_header_must_still_match_file_code(self):
        out = BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("b1202406001.txt", "2\tOTRO\n100000000\t1\t0\t0\t0\n")
            z.writestr("b2202406001.txt", "1\tX\n143000000\t1\t0\t0\t0\n")
            z.writestr("r1202406001.txt", "1\tX\n411000000\t1\n")
            z.writestr("metadata/plan_de_cuentas.txt", "CUENTA\tDESCRIPCION\n100000000\tTOTAL ACTIVOS\n143000000\tA\n411000000\tI\n")
        with self.assertRaisesRegex(RuntimeError, "Malformed institution header"):
            extract_archive(out.getvalue(), "2024-06")

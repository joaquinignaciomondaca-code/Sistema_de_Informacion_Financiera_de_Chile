import json
import sys
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

    def test_el_presupuesto_de_minutos_corta_entre_meses_y_no_a_mitad_de_uno(self):
        """`--minutos` se aplica antes de empezar un mes nuevo (los tiempos van en segundos).

        Sin este corte el `timeout-minutes` del job mataba la corrida a mitad de un mes: lo
        descargado se perdía y la siguiente corrida partía de cero otra vez.
        """
        manifest = {"periods": []}
        tiempos = iter([0.0, 0.0, 3600.0, 3601.0])   # el segundo mes ya cae en los 60 min
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            result = catch_up(False, 24, date(2026, 10, 15), self._fake_publisher(manifest),
                              minutos=60, reloj=lambda: next(tiempos))
        self.assertEqual(result["periods"], ["2026-07"], "no había que empezar el mes siguiente")
        self.assertEqual(result["status"], "presupuesto_agotado")
        self.assertEqual(result["stopped_error"], "", "quedarse sin presupuesto no es un error de datos")
        self.assertTrue(result["published_changed"], "lo publicado debe confirmarse en la rama")

    def test_sin_presupuesto_la_puesta_al_dia_recorre_todos_los_meses(self):
        manifest = {"periods": []}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            result = catch_up(False, 24, date(2026, 10, 15), self._fake_publisher(manifest), minutos=None)
        self.assertEqual(result["status"], "caught_up")
        self.assertEqual(len(result["periods"]), 3)

    def test_catch_up_first_failure_is_an_error_and_dry_run_does_not_loop(self):
        manifest = {"periods": []}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            with self.assertRaises(RuntimeError):
                catch_up(False, 24, date(2026, 10, 15), self._fake_publisher(manifest, fail_on={"2026-07"}))
            result = catch_up(True, 24, date(2026, 10, 15), self._fake_publisher(manifest))
        self.assertEqual(result["periods"], [])
        self.assertFalse(result["published_changed"])

    def _not_published_publisher(self, missing):
        def publisher(period, dry_run=False):
            raise mod.SourceNotPublished("Expected one CMF .zip link for " + period + "; found 0")
        return publisher

    def test_catch_up_waits_quietly_when_next_month_is_not_yet_published(self):
        manifest = {"periods": [{"period": "2026-07"}]}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            result = catch_up(False, 24, date(2026, 9, 28), self._not_published_publisher("2026-08"), start="2026-07")
        self.assertEqual(result["periods"], [])
        self.assertFalse(result["published_changed"])
        self.assertEqual(result["waiting_for"], "2026-08")

    def test_catch_up_fails_if_a_closed_month_is_missing_for_too_long(self):
        manifest = {"periods": [{"period": "2026-07"}]}
        with mock.patch.object(mod, "load_manifest", lambda: manifest):
            with self.assertRaisesRegex(RuntimeError, "días cerrado"):
                catch_up(False, 24, date(2026, 12, 1), self._not_published_publisher("2026-08"), start="2026-07")

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


class SoloDataManifestTests(unittest.TestCase):
    """`data_manifest.json` se regenera sobre la versión vigente, no viaja en el commit de datos."""

    def _entorno(self, tmp, periodos=("2026-06", "2026-07"), crear=True):
        root = Path(tmp)
        salida = root / "docs" / "outputs" / "bancos" / "cmf_b1_b2_r1"
        registros = []
        for periodo in periodos:
            archivo = f"outputs/bancos/cmf_b1_b2_r1/{periodo}/lineas.parquet"
            if crear:
                (root / "docs" / archivo).parent.mkdir(parents=True)
                (root / "docs" / archivo).write_bytes(b"PAR1")
            registros.append({"period": periodo, "file": archivo, "records": 100,
                              "zip_url": f"https://cmf.invalid/{periodo}.zip"})
        particiones = {"dataset": "bancos_cmf_lineas", "periods": registros,
                       "files": [r["file"] for r in registros],
                       "total_records": 100 * len(registros)}
        (salida / "manifest.json").parent.mkdir(parents=True, exist_ok=True)
        (salida / "manifest.json").write_text(json.dumps(particiones))
        (root / "data_manifest.json").write_text(json.dumps({
            "version": "1.0.0", "updated_at": "2026-09-01", "total_tables": 2, "total_records": 1150,
            "tables": [{"id": "bancos_cmf_lineas", "registros_reales": 100, "corte": "2026-06 a 2026-06",
                        "file_parquet": "x"},
                       {"id": "otra_tabla", "registros_reales": 1050}]}))
        return root, salida

    def _con_rutas(self, root, salida):
        return (mock.patch.object(mod, "ROOT", root), mock.patch.object(mod, "OUTPUT_ROOT", salida),
                mock.patch.object(mod, "PARTITION_MANIFEST", salida / "manifest.json"),
                mock.patch.object(mod, "DATA_MANIFEST", root / "data_manifest.json"))

    def test_registra_el_ultimo_periodo_y_conserva_las_demas_tablas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, salida = self._entorno(tmp)
            parches = self._con_rutas(root, salida)
            with parches[0], parches[1], parches[2], parches[3]:
                self.assertEqual(mod.rebuild_data_manifest(), "2026-07")
            man = json.loads((root / "data_manifest.json").read_text())
            por_id = {t["id"]: t for t in man["tables"]}
            self.assertEqual(por_id["bancos_cmf_lineas"]["registros_reales"], 200)
            self.assertEqual(por_id["bancos_cmf_lineas"]["corte"], "2026-06 a 2026-07")
            self.assertEqual(por_id["bancos_cmf_lineas"]["file_parquet"],
                             "outputs/bancos/cmf_b1_b2_r1/2026-07/lineas.parquet")
            self.assertEqual(por_id["bancos_cmf_lineas"]["origen"], "https://cmf.invalid/2026-07.zip")
            self.assertEqual(por_id["otra_tabla"]["registros_reales"], 1050)       # lo ajeno no se toca
            self.assertEqual(man["total_records"], 1250)
            self.assertEqual(man["total_tables"], 2)

    def test_es_idempotente(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, salida = self._entorno(tmp)
            parches = self._con_rutas(root, salida)
            with parches[0], parches[1], parches[2], parches[3]:
                mod.rebuild_data_manifest()
                primero = (root / "data_manifest.json").read_bytes()
                mod.rebuild_data_manifest()
            self.assertEqual((root / "data_manifest.json").read_bytes(), primero)

    def test_sin_particiones_o_con_una_particion_faltante_falla_sin_escribir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, salida = self._entorno(tmp, periodos=(), crear=False)
            antes = (root / "data_manifest.json").read_bytes()
            parches = self._con_rutas(root, salida)
            with parches[0], parches[1], parches[2], parches[3]:
                with self.assertRaisesRegex(RuntimeError, "No hay particiones"):
                    mod.rebuild_data_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            root, salida = self._entorno(tmp, crear=False)
            antes = (root / "data_manifest.json").read_bytes()
            parches = self._con_rutas(root, salida)
            with parches[0], parches[1], parches[2], parches[3]:
                with self.assertRaisesRegex(RuntimeError, "no están en disco"):
                    mod.rebuild_data_manifest()
            self.assertEqual((root / "data_manifest.json").read_bytes(), antes)

    def test_la_opcion_de_linea_de_comandos_llama_al_modo_y_devuelve_codigo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, salida = self._entorno(tmp)
            parches = self._con_rutas(root, salida)
            with parches[0], parches[1], parches[2], parches[3]:
                with mock.patch.object(sys, "argv", ["publish_cmf_bank_period", "--solo-data-manifest"]):
                    self.assertEqual(mod.main(), 0)
            self.assertEqual(json.loads((root / "data_manifest.json").read_text())["total_records"], 1250)


if __name__ == "__main__":
    unittest.main()

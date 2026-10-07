from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import socket
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_carteras_afp import audit
from bdp_common import COLUMNS, OFFICIAL_LANDING_PAGE, PRIVATE_ROOT, REQUIRED_PACKAGE_IDS
from check_publicacion_bdp import DEFAULT_POLICY, evaluate
from download_bdp_packages import (
    CatalogNotReady,
    _archive_inventory,
    _download_to_part,
    _safe_filename,
    catalog_status,
    download_package,
    load_catalog,
)
from extraer_carteras_afp import _acquire_lock, extract, mapping
from publish_bdp import DEFAULT_PUBLIC_ROOT, _publish_tree, publish


class FakeResponse:
    def __init__(self, data: bytes, status=200, headers=None, url="https://www.spensiones.cl/file.zip", fail_after=None):
        self._data = data
        self._position = 0
        self.status = status
        self.headers = headers or {}
        self._url = url
        self.fail_after = fail_after
        self.closed = False
        self._failed = False

    def geturl(self):
        return self._url

    def read(self, size=-1):
        if self.fail_after is not None and self._position >= self.fail_after and not self._failed:
            self._failed = True
            raise OSError("simulated interrupted transfer")
        if size < 0:
            size = len(self._data) - self._position
        end = min(len(self._data), self._position + size)
        if self.fail_after is not None:
            end = min(end, self.fail_after)
        result = self._data[self._position:end]
        self._position = end
        return result

    def close(self):
        self.closed = True


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout=0):
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


class CarterasPipelineTest(unittest.TestCase):
    def setUp(self):
        (ROOT / ".local-data").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / ".local-data")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csv = self.root / "fuente.csv"
        self.out = self.root / "staging"

    def row(self, code="WNMV", fecha="2021-01-29", afp="HAB", fondo="A"):
        row = [fecha, afp, fondo, code] + [""] * (len(COLUMNS) - 4)
        row[4] = "SERIE-001"
        row[5] = "Emisor ñ"
        row[8] = "UF"
        row[9] = "736,9"
        row[10] = "-319862208,9"
        row[17] = "FIJANO +00,4550ACT/360"
        return row

    def write_csv(self, path=None, rows=None, encoding="utf-8", multiline=False):
        path = Path(path or self.csv)
        rows = rows if rows is not None else [self.row()]
        with path.open("w", encoding=encoding, newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(COLUMNS)
            for row in rows:
                if multiline:
                    row = list(row)
                    row[5] = "Emisor ñ;nombre\nsegunda línea"
                writer.writerow(row)
        return path

    def write_zip(self, path=None, files=None, include_dir=False):
        path = Path(path or self.root / "paquete.zip")
        files = files or {"cartera.csv": self.csv.read_bytes()}
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            if include_dir:
                archive.writestr("carteras/", "")
            for name, data in files.items():
                archive.writestr(name, data)
        return path

    def test_csv_literal_preservation_and_private_stage(self):
        row = self.row()
        self.write_csv(rows=[row])
        result = extract([self.csv], self.out, package_ids=["prueba"])
        checked = audit(self.out)
        import pyarrow.parquet as pq
        manifest = json.loads((self.out / "manifest.json").read_text())
        revision_id = manifest["active_sources"]["prueba!fuente.csv"]
        part = self.out / manifest["revisions"][revision_id]["parts"][0]["path"]
        stored = pq.read_table(part).to_pylist()[0]
        self.assertEqual([stored[column] for column in COLUMNS], row)
        self.assertEqual(checked["filas"], 1)
        self.assertFalse(checked["publicable"])
        self.assertEqual(result["status"], "staging_complete")
        self.assertFalse((ROOT / "docs/outputs/pensiones/bdp").exists())

    def test_resumes_at_committed_batch_boundary(self):
        rows = [self.row(code=code, fecha=f"2021-01-{i:02d}") for i, code in enumerate(["WNMV", "BTU", "ACC", "DPF", "SNT"], 1)]
        self.write_csv(rows=rows)
        first = extract(
            [self.csv], self.out, package_ids=["historico_1996_2005"],
            filas_por_lote=2, max_lotes=1,
        )
        self.assertEqual(first["status"], "incomplete")
        partial = audit(self.out, allow_incomplete=True)
        self.assertEqual(partial["filas"], 0)  # no activa un paquete a medias
        self.assertEqual(partial["estado"], "incompleto")
        resumed = extract(
            [self.csv], self.out, package_ids=["historico_1996_2005"],
            filas_por_lote=2, max_lotes=0,
        )
        self.assertEqual(resumed["status"], "staging_complete")
        result = audit(self.out)
        self.assertEqual(result["filas"], 5)
        self.assertEqual(result["particiones_auditadas"], 5)

    def test_incremental_replaces_only_changed_source_and_keeps_history(self):
        self.write_csv(rows=[self.row(), self.row(code="BTU", fecha="2021-02-26")])
        extract([self.csv], self.out, package_ids=["actualidad"])
        first = json.loads((self.out / "manifest.json").read_text())
        first_revision = first["active_sources"]["actualidad!fuente.csv"]
        self.write_csv(rows=[self.row(code="ACC", fecha="2021-03-31")])
        result = extract([self.csv], self.out, package_ids=["actualidad"], incremental=True)
        updated = json.loads((self.out / "manifest.json").read_text())
        self.assertNotEqual(updated["active_sources"]["actualidad!fuente.csv"], first_revision)
        self.assertIn(first_revision, updated["revisions"])
        self.assertEqual(result["filas_activas"], 1)
        self.assertEqual(audit(self.out)["filas"], 1)

    def test_incremental_preserves_packages_not_in_update(self):
        self.write_csv(rows=[self.row()])
        extract([self.csv], self.out, package_ids=["early"])
        later = self.root / "later.csv"
        self.write_csv(later, [self.row(code="ACC", fecha="2018-12-28")])
        extract([later], self.out, package_ids=["recent"], incremental=True)
        result = audit(self.out)
        self.assertEqual(result["filas"], 2)
        self.assertEqual(set(result["paquetes_activos"]), {"early", "recent"})

    def test_idempotent_source_does_not_create_duplicate_parts(self):
        self.write_csv(rows=[self.row(), self.row(code="BTU", fecha="2021-02-26")])
        extract([self.csv], self.out, package_ids=["paquete"])
        before = json.loads((self.out / "manifest.json").read_text())
        extract([self.csv], self.out, package_ids=["paquete"], incremental=True)
        after = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(len(before["revisions"]), len(after["revisions"]))
        self.assertEqual(len(before["revisions"][next(iter(before["revisions"]))]["parts"]),
                         len(after["revisions"][next(iter(after["revisions"]))]["parts"]))

    def test_zip_path_handling_and_directory_entries(self):
        self.write_csv()
        archive_path = self.write_zip(
            files={"carteras/anual.csv": self.csv.read_bytes()}, include_dir=True
        )
        result = extract([archive_path], self.out, package_ids=["zip_prueba"])
        self.assertEqual(result["filas_activas"], 1)
        self.assertEqual(audit(self.out)["filas"], 1)
        with zipfile.ZipFile(archive_path, "a") as archive:
            archive.writestr("../fuera.csv", self.csv.read_bytes())
        with self.assertRaises(ValueError):
            extract([archive_path], self.root / "staging_segundo", package_ids=["zip_malo"])

    def test_unknown_code_is_quarantined_not_discarded(self):
        self.write_csv(rows=[self.row(code="NUEVO_CODIGO")])
        extract([self.csv], self.out, package_ids=["paquete"])
        with self.assertRaisesRegex(ValueError, "sin clasificar"):
            audit(self.out)
        result = audit(self.out, allow_quarantine=True)
        self.assertEqual(result["codigos_no_clasificados"], {"NUEVO_CODIGO": 1})
        self.assertEqual(result["filas"], 1)
        self.assertFalse(result["publicable"])

    def test_bad_header_and_record_fail_closed(self):
        self.csv.write_text("header equivocado\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Cabecera"):
            extract([self.csv], self.out, package_ids=["mal"])
        broken = self.root / "broken.csv"
        broken.write_text(";".join(COLUMNS) + "\n2021-01-29;HAB\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Cantidad de campos"):
            extract([broken], self.root / "staging_broken", package_ids=["mal2"])

    def test_cp1252_quoted_multiline_record(self):
        self.write_csv(rows=[self.row()], encoding="cp1252", multiline=True)
        result = extract([self.csv], self.out, encoding="cp1252", package_ids=["cp1252"])
        self.assertEqual(result["filas_activas"], 1)
        self.assertEqual(audit(self.out)["filas"], 1)

    def test_archive_revision_removes_disappeared_member_only_after_complete_package(self):
        self.write_csv(rows=[self.row()])
        first_zip = self.write_zip(files={"2021.csv": self.csv.read_bytes(), "2022.csv": self.csv.read_bytes()})
        extract([first_zip], self.out, package_ids=["recent"])
        second_zip = self.write_zip(
            self.root / "updated.zip", files={"2022.csv": self.csv.read_bytes()}
        )
        extract([second_zip], self.out, package_ids=["recent"], incremental=True)
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(set(manifest["active_sources"]), {"recent!2022.csv"})
        self.assertEqual(audit(self.out)["filas"], 1)

    def test_limits_bad_ids_and_public_destinations(self):
        self.write_csv()
        for options in (
            {"minutos": float("nan")},
            {"max_archivos": 0},
            {"filas_por_lote": 0},
            {"max_lotes": -1},
        ):
            with self.assertRaises(ValueError):
                extract([self.csv], self.out, package_ids=["limite"], **options)
        with self.assertRaises(ValueError):
            extract([self.csv], ROOT / "docs/outputs/pensiones/no_publicar", package_ids=["bloqueo"])
        with self.assertRaisesRegex(ValueError, "originales.*\.local-data"):
            extract([Path(__file__)], self.out, package_ids=["fuera_privado"])
        with self.assertRaises(ValueError):
            extract([self.csv], self.out, package_ids=["INVALIDO_MAYUSCULAS"])

    def test_ingest_lock_is_valid_json_and_recovers_only_dead_local_pid(self):
        self.out.mkdir(parents=True)
        lock = self.out / ".ingest.lock"
        active = {"pid": os.getpid(), "hostname": socket.gethostname()}
        lock.write_text(json.dumps(active), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ingesta activa"):
            _acquire_lock(lock)

        dead = {"pid": 123, "hostname": socket.gethostname()}
        lock.write_text(json.dumps(dead), encoding="utf-8")
        with patch("extraer_carteras_afp.os.kill", side_effect=ProcessLookupError):
            descriptor = _acquire_lock(lock)
        try:
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["pid"], os.getpid())
        finally:
            os.close(descriptor)
            lock.unlink(missing_ok=True)

    def test_direct_csv_size_limit_is_applied(self):
        self.write_csv()
        with patch("extraer_carteras_afp.MAX_CSV_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "CSV supera el límite de tamaño"):
                extract([self.csv], self.out, package_ids=["csv_grande"])

    def test_csv_field_limit_is_applied_and_restored(self):
        row = self.row()
        row[4] = "X" * 129
        self.write_csv(rows=[row])
        original_limit = csv.field_size_limit()
        with patch("extraer_carteras_afp.MAX_CSV_FIELD_BYTES", 128):
            with self.assertRaisesRegex(ValueError, "CSV no decodificable o mal formado"):
                extract([self.csv], self.out, package_ids=["campo_grande"])
        self.assertEqual(csv.field_size_limit(), original_limit)

    def test_tampered_partition_hash_is_detected(self):
        self.write_csv()
        extract([self.csv], self.out, package_ids=["tamper"])
        manifest = json.loads((self.out / "manifest.json").read_text())
        revision_id = manifest["active_sources"]["tamper!fuente.csv"]
        part = self.out / manifest["revisions"][revision_id]["parts"][0]["path"]
        with part.open("ab") as stream:
            stream.write(b"alterado")
        with self.assertRaisesRegex(ValueError, "Hash"):
            audit(self.out)

    def test_full_history_means_three_packages_but_not_certification(self):
        inputs = []
        ids = ["historico_1996_2005", "historico_2006_2015", "historico_2016_actualidad"]
        for package_id in ids:
            path = self.root / f"{package_id}.csv"
            self.write_csv(path, [self.row(fecha=f"{1996 + len(inputs)}-01-31")])
            inputs.append(path)
        extract(inputs, self.out, package_ids=ids)
        result = audit(self.out, require_full_history=True)
        self.assertTrue(result["historico_completo_por_paquetes"])
        self.assertFalse(result["cobertura_historica_certificada"])
        self.assertEqual(result["filas"], 3)

    def test_family_catalog_is_disjoint_and_provisional(self):
        self.assertEqual(len(mapping()), 63)


class BdpDownloadTest(unittest.TestCase):
    def setUp(self):
        evidence_root = PRIVATE_ROOT / "pensiones/bdp/evidencia"
        evidence_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=evidence_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive_bytes(self, serie="SERIE-001"):
        buffer = io.BytesIO()
        row = ["2021-01-29", "HAB", "A", "WNMV"] + [""] * (len(COLUMNS) - 4)
        row[4] = serie
        text = io.StringIO(newline="")
        writer = csv.writer(text, delimiter=";")
        writer.writerow(COLUMNS)
        writer.writerow(row)
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("carteras/", "")
            archive.writestr("carteras/cartera.csv", text.getvalue().encode())
        return buffer.getvalue()

    def captured_package(
        self,
        expected_sha256=None,
        package_id="historico_1996_2005",
        filename="carteras.zip",
        download_url=None,
    ):
        captured_at = "2026-10-07T00:00:00Z"
        download_url = download_url or "https://www.spensiones.cl/descargas/carteras.zip"
        evidence_path = self.root / f"{package_id}.json"
        evidence = {
            "source_page": OFFICIAL_LANDING_PAGE,
            "captured_at": captured_at,
            "request_method": "GET",
            "request_url": download_url,
            "referer": OFFICIAL_LANDING_PAGE,
            "response_status": 200,
            "content_type": "application/zip",
            "response_filename": filename,
        }
        evidence_path.write_text(json.dumps(evidence, sort_keys=True), encoding="utf-8")
        return {
            "id": package_id,
            "download_url": download_url,
            "expected_filename": filename,
            "expected_sha256": expected_sha256,
            "captured_from": OFFICIAL_LANDING_PAGE,
            "captured_at": captured_at,
            "capture_evidence": evidence_path.relative_to(ROOT).as_posix(),
            "capture_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        }

    def test_pending_catalog_is_a_safe_noop(self):
        status = catalog_status()
        self.assertFalse(status["ready"])
        self.assertEqual(status["estado"], "bloqueado_sin_captura_oficial")
        self.assertIn("URL/nombre/fecha", status["motivo"])
        with self.assertRaises(CatalogNotReady):
            load_catalog()

    def test_catalog_requires_three_complete_pinned_captures(self):
        packages = []
        for package_id in REQUIRED_PACKAGE_IDS:
            filename = f"{package_id}.zip"
            packages.append(
                self.captured_package(
                    package_id=package_id,
                    filename=filename,
                    download_url=f"https://www.spensiones.cl/descargas/{filename}",
                )
            )
        catalog_path = self.root / "captured-catalog.json"
        catalog_path.write_text(
            json.dumps({
                "version": 1,
                "source_page": OFFICIAL_LANDING_PAGE,
                "estado": "listo",
                "packages": packages,
            }),
            encoding="utf-8",
        )
        catalog = load_catalog(catalog_path)
        self.assertEqual(set(item["id"] for item in catalog["packages"]), set(REQUIRED_PACKAGE_IDS))
        self.assertTrue(catalog_status(catalog_path)["ready"])

    def test_url_and_filename_guards(self):
        from bdp_common import validate_official_https_url
        for url in (
            "http://www.spensiones.cl/file.zip",
            "https://spensiones.cl.evil.test/file.zip",
            "https://notspensiones.cl/file.zip",
            "https://user@spensiones.cl/file.zip",
            "https://spensiones.cl:8443/file.zip",
            "https://spensiones.cl/file.zip?token=secret",
        ):
            with self.assertRaises(ValueError):
                validate_official_https_url(url)
        with self.assertRaises(ValueError):
            _safe_filename("../carteras.zip")

    def test_download_requires_sane_official_capture_and_matching_digest(self):
        package = self.captured_package()
        package["capture_sha256"] = "0" * 64
        opener = FakeOpener([])
        with self.assertRaisesRegex(ValueError, "SHA-256 de captura"):
            download_package(
                package,
                OFFICIAL_LANDING_PAGE,
                self.root / "originales",
                opener=opener,
            )
        self.assertEqual(opener.requests, [])

    def test_zip_inventory_validates_nested_csv_and_directory(self):
        path = self.root / "valid.zip"
        path.write_bytes(self.archive_bytes())
        inventory = _archive_inventory(path)
        self.assertEqual([item["name"] for item in inventory], ["carteras/cartera.csv"])
        bad = self.root / "traversal.zip"
        with zipfile.ZipFile(bad, "w") as archive:
            archive.writestr("../bad.csv", b"x")
        with self.assertRaises(ValueError):
            _archive_inventory(bad)

    def test_range_resume_requires_same_etag_and_content_range(self):
        part = self.root / "download.zip.part"
        meta = self.root / "download.zip.part.json"
        first = FakeResponse(
            b"abcdefghij", status=200,
            headers={"ETag": '"v1"', "Content-Length": "10"},
            fail_after=4,
        )
        opener = FakeOpener([first])
        package = {"download_url": "https://www.spensiones.cl/file.zip"}
        with self.assertRaises(OSError):
            _download_to_part(package, part, meta, opener=opener, timeout=5, max_bytes=100)
        self.assertEqual(part.read_bytes(), b"abcd")
        self.assertEqual(json.loads(meta.read_text())["bytes"], 4)
        second = FakeResponse(
            b"efghij", status=206,
            headers={"ETag": '"v1"', "Content-Length": "6", "Content-Range": "bytes 4-9/10"},
        )
        opener.responses.append(second)
        record = _download_to_part(package, part, meta, opener=opener, timeout=5, max_bytes=100)
        self.assertEqual(part.read_bytes(), b"abcdefghij")
        self.assertEqual(record["bytes"], 10)
        self.assertEqual(opener.requests[1].get_header("Range"), "bytes=4-")

    def test_invalid_range_bounds_discard_untrusted_partial(self):
        url = "https://www.spensiones.cl/file.zip"
        part = self.root / "bad-range.zip.part"
        meta = self.root / "bad-range.zip.part.json"
        part.write_bytes(b"abcd")
        meta.write_text(
            json.dumps({
                "url_fingerprint": hashlib.sha256(url.encode()).hexdigest(),
                "etag": '"v1"',
                "bytes": 4,
            }),
            encoding="utf-8",
        )
        response = FakeResponse(
            b"efghij",
            status=206,
            headers={"ETag": '"v1"', "Content-Length": "6", "Content-Range": "bytes 4-8/10"},
            url=url,
        )
        with self.assertRaisesRegex(ValueError, "Content-Range"):
            _download_to_part(
                {"download_url": url},
                part,
                meta,
                opener=FakeOpener([response]),
                timeout=5,
                max_bytes=100,
            )
        self.assertFalse(part.exists())
        self.assertFalse(meta.exists())

    def test_official_zip_download_hash_and_sidecar(self):
        archive = self.archive_bytes()
        digest = hashlib.sha256(archive).hexdigest()
        response = FakeResponse(
            archive,
            headers={"ETag": '"abc"', "Content-Length": str(len(archive))},
            url="https://www.spensiones.cl/descargas/carteras.zip",
        )
        package = self.captured_package(expected_sha256=digest)
        result = download_package(
            package,
            OFFICIAL_LANDING_PAGE,
            self.root / "originales",
            opener=FakeOpener([response]),
        )
        self.assertEqual(result["download_status"], "verified")
        self.assertEqual(result["sha256"], digest)
        self.assertEqual(result["redistribution_status"], "not_reviewed")
        target = self.root / "originales/historico_1996_2005.zip"
        self.assertTrue(target.with_suffix(".zip.source.json").is_file())
        self.assertEqual(result["source_filename"], "carteras.zip")
        staging = self.root / "staging"
        staged = extract([target], staging)
        self.assertEqual(staged["status"], "staging_complete")
        manifest = json.loads((staging / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["packages"]["historico_1996_2005"]["official_origin_verified"])
        not_modified = FakeResponse(
            b"", status=304, headers={},
            url="https://www.spensiones.cl/descargas/carteras.zip",
        )
        unchanged = download_package(
            package,
            OFFICIAL_LANDING_PAGE,
            self.root / "originales",
            opener=FakeOpener([not_modified]),
        )
        self.assertEqual(unchanged["sha256"], digest)
        self.assertTrue(not_modified.closed)

    def test_incremental_download_preserves_previous_official_archive(self):
        old_archive = self.archive_bytes("SERIE-OLD")
        new_archive = self.archive_bytes("SERIE-NEW")
        old_response = FakeResponse(
            old_archive,
            headers={"ETag": '"v1"', "Content-Length": str(len(old_archive))},
            url="https://www.spensiones.cl/descargas/carteras.zip",
        )
        package = self.captured_package()
        output = self.root / "originales"
        first = download_package(package, OFFICIAL_LANDING_PAGE, output, opener=FakeOpener([old_response]))

        head = FakeResponse(
            b"",
            status=200,
            headers={"ETag": '"v2"', "Content-Length": str(len(new_archive))},
            url="https://www.spensiones.cl/descargas/carteras.zip",
        )
        current = FakeResponse(
            new_archive,
            headers={"ETag": '"v2"', "Content-Length": str(len(new_archive))},
            url="https://www.spensiones.cl/descargas/carteras.zip",
        )
        second = download_package(
            package,
            OFFICIAL_LANDING_PAGE,
            output,
            opener=FakeOpener([head, current]),
        )
        previous_path = output / "revisions/historico_1996_2005" / f"{first['sha256']}.zip"
        self.assertTrue(previous_path.is_file())
        self.assertEqual(hashlib.sha256(previous_path.read_bytes()).hexdigest(), first["sha256"])
        self.assertEqual(second["previous_archive"], previous_path.relative_to(output).as_posix())
        self.assertEqual(hashlib.sha256((output / "historico_1996_2005.zip").read_bytes()).hexdigest(), second["sha256"])
        self.assertNotEqual(first["sha256"], second["sha256"])

    def test_official_download_rejects_redirect_outside_sp(self):
        response = FakeResponse(
            self.archive_bytes(),
            headers={"Content-Length": str(len(self.archive_bytes()))},
            url="https://attacker.example/payload.zip",
        )
        package = self.captured_package()
        with self.assertRaises(ValueError):
            download_package(package, OFFICIAL_LANDING_PAGE, self.root / "originales", opener=FakeOpener([response]))


class BdpPublicationGateTest(unittest.TestCase):
    def setUp(self):
        (ROOT / ".local-data").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / ".local-data")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_repository_publication_policy_is_locked_without_evidence(self):
        decision = evaluate(DEFAULT_POLICY)
        self.assertFalse(decision["ready"])
        self.assertEqual(decision["estado"], "bloqueado")
        self.assertIn("cotejo_de_originales_sp", " ".join(decision["razones"]))
        output = self.root / "would_be_public"
        with self.assertRaises(PermissionError):
            publish(self.root / "staging_inexistente", output)
        self.assertFalse(output.exists())
        self.assertFalse(DEFAULT_PUBLIC_ROOT.exists())

    def test_atomic_publication_builder_writes_only_to_private_test_root(self):
        source_dir = self.root / "sources"
        source_dir.mkdir()
        ids = ["historico_1996_2005", "historico_2006_2015", "historico_2016_actualidad"]
        inputs = []
        for package_id in ids:
            path = source_dir / f"{package_id}.csv"
            row = ["2021-01-29", "HAB", "A", "WNMV"] + [""] * (len(COLUMNS) - 4)
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream, delimiter=";")
                writer.writerow(COLUMNS)
                writer.writerow(row)
            inputs.append(path)
        staging = self.root / "staging"
        extract(inputs, staging, package_ids=ids)
        audited = audit(staging, require_full_history=True)
        output = self.root / "private-published"
        result = _publish_tree(staging, output, audited)
        self.assertEqual(result["rows"], 3)
        self.assertTrue((output / "manifest.json").is_file())
        self.assertTrue((output / ".bdp_publication.json").is_file())
        self.assertTrue((output / "afp_derivados_forwards/manifest.json").is_file())
        self.assertFalse(DEFAULT_PUBLIC_ROOT.exists())


if __name__ == "__main__":
    unittest.main()

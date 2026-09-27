"""Pruebas offline del contrato de publicación macro (sin acceso a BCCh)."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from macro.scripts.publish_macro import NAMES, ROOT, publish


class PublishMacroTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.stage = base / "stage"
        self.published = base / "published"
        self.stage.mkdir()
        self.published.mkdir()
        self.manifest = base / "data_manifest.json"
        shutil.copyfile(ROOT / "data_manifest.json", self.manifest)
        for name in NAMES:
            for ext in ("json", "parquet"):
                file = f"{name}.{ext}"
                shutil.copyfile(ROOT / "docs/outputs/macro" / file, self.stage / file)
                shutil.copyfile(ROOT / "docs/outputs/macro" / file, self.published / file)

    def test_no_change_is_noop(self):
        before = self.manifest.read_bytes()
        self.assertFalse(publish(self.stage, self.published, self.manifest))
        self.assertEqual(before, self.manifest.read_bytes())

    def test_json_mismatch_keeps_published_files(self):
        target = self.stage / f"{NAMES[0]}.json"
        rows = json.loads(target.read_text(encoding="utf-8"))
        target.write_text(json.dumps(rows[:-1]), encoding="utf-8")
        old = (self.published / target.name).read_bytes()
        with self.assertRaisesRegex(ValueError, "JSON y Parquet"):
            publish(self.stage, self.published, self.manifest)
        self.assertEqual(old, (self.published / target.name).read_bytes())

    def test_value_mismatch_keeps_published_files(self):
        target = self.stage / f"{NAMES[1]}.json"
        rows = json.loads(target.read_text(encoding="utf-8"))
        rows[0]["usd_clp_cierre"] += 1
        target.write_text(json.dumps(rows), encoding="utf-8")
        old = (self.published / target.name).read_bytes()
        with self.assertRaisesRegex(ValueError, "Valores JSON/Parquet"):
            publish(self.stage, self.published, self.manifest)
        self.assertEqual(old, (self.published / target.name).read_bytes())

    def test_null_regression_keeps_published_files(self):
        name = NAMES[1]
        path = self.stage / f"{name}.parquet"
        df = pd.read_parquet(path)
        df.loc[0, "usd_clp_cierre"] = None
        df.to_parquet(path, index=False)
        old = (self.published / path.name).read_bytes()
        with self.assertRaisesRegex(ValueError, "Valores JSON/Parquet|Regresión de datos no nulos"):
            publish(self.stage, self.published, self.manifest)
        self.assertEqual(old, (self.published / path.name).read_bytes())


if __name__ == "__main__":
    unittest.main()

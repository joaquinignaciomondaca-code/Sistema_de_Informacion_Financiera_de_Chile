from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts import build_sql_compact_parquets as compact


class CompactParquetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        self.source_dir = self.docs / "outputs" / "partitions"
        self.source_dir.mkdir(parents=True)
        self.spec = {
            "source_manifest": "docs/outputs/partitions/manifest.json",
            "file": "docs/outputs/sql_query/demo.parquet",
            "description": "Copia compacta de prueba; no es descarga.",
        }
        self.parts = [
            pa.table({"periodo": ["2025-01", "2025-01"], "valor": [10, 20]}),
            pa.table({"periodo": ["2025-02"], "valor": [30]}),
        ]
        files = []
        for i, table in enumerate(self.parts):
            name = f"{i}.parquet"
            pq.write_table(table, self.source_dir / name, compression="zstd")
            files.append(f"outputs/partitions/{name}")
        (self.source_dir / "manifest.json").write_text(
            json.dumps({"files": files, "total_records": 3, "updated_at": "2025-02-01"}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_compact_preserves_rows_schema_and_provenance(self):
        sidecar = compact.write_compact(self.root, "demo", self.spec)
        output = pq.read_table(self.root / self.spec["file"])
        expected = pa.concat_tables(self.parts)
        self.assertTrue(output.equals(expected))
        self.assertEqual(sidecar["records"], 3)
        self.assertEqual(sidecar["purpose"], "SQL-only; no forma parte del catálogo de descargas")
        self.assertEqual(compact.check_compact(self.root, "demo", self.spec), [])

    def test_check_detects_changed_source_partition(self):
        compact.write_compact(self.root, "demo", self.spec)
        pq.write_table(pa.table({"periodo": ["2025-01", "2025-01"], "valor": [99, 20]}), self.source_dir / "0.parquet")
        problems = compact.check_compact(self.root, "demo", self.spec)
        self.assertTrue(any("source_files" in problem for problem in problems))

    def test_rejects_incompatible_partition_schema(self):
        pq.write_table(pa.table({"periodo": ["2025-02"], "valor": ["texto"]}), self.source_dir / "1.parquet")
        with self.assertRaisesRegex(ValueError, "esquema incompatible"):
            compact.load_inputs(self.root, "demo", self.spec)


if __name__ == "__main__":
    unittest.main()

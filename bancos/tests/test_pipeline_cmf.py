"""Pruebas unitarias sin red para el pipeline incremental de REPO CMF."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from bancos.scripts import pipeline_stream_repos_cmf as pipeline


class FakeCMFResponse:
    def __init__(self, data: dict):
        self.data = data

    def read(self):
        import json
        return json.dumps(self.data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TestBancosRepoPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_determine_target_periods_incremental(self):
        """Verifica que el rango sea estrictamente desde el último mes guardado."""
        df_base = pd.DataFrame({"periodo": ["2026-03", "2026-04"]})
        periods = pipeline.determine_target_periods(df_base)
        self.assertTrue(len(periods) >= 1)
        self.assertEqual(periods[0], "2026-04")

    @patch("bancos.scripts.pipeline_stream_repos_cmf.get_api_key", return_value="dummy_key")
    @patch("bancos.scripts.pipeline_stream_repos_cmf.fetch_mes_cuenta")
    def test_run_bancos_repo_pipeline_with_mock_data(self, mock_cuenta, mock_key):
        """Valida que los registros descargados se estructuren y calculen adecuadamente."""
        mock_cuenta.return_value = [
            {
                "codigo_institucion": "001",
                "nombre_institucion": "BANCO DE CHILE",
                "cuenta": "1160100",
                "monto_mm_clp": 50000.0,
            }
        ]

        df_base = pd.DataFrame({
            "id_repo": ["001_2026-03"],
            "periodo": ["2026-03"],
            "fecha_corte": ["2026-03-31"],
            "codigo_institucion": ["001"],
            "rut": ["97.004.000-5"],
            "razon_social": ["Banco de Chile"],
            "nombre_fantasia": ["BANCO DE CHILE"],
            "repo_activo_mm_clp": [40000.0],
            "repo_pasivo_mm_clp": [10000.0],
            "repo_neto_mm_clp": [30000.0],
            "tc_usd_cierre": [900.0],
            "repo_activo_mm_usd": [44.44],
            "repo_pasivo_mm_usd": [11.11],
            "repo_neto_mm_usd": [33.33],
            "total_transado_mm_usd": [55.55],
            "posicion_relativa": ["Prestamista Neto de Liquidez"],
        })

        with patch("bancos.scripts.pipeline_stream_repos_cmf.determine_target_periods", return_value=["2026-04"]):
            ok, count = pipeline.run_bancos_repo_pipeline(
                output_dir=self.out_dir,
                baseline_df=df_base,
            )

        self.assertTrue(ok)
        self.assertTrue((self.out_dir / "bancos_repos_saldos_series.parquet").exists())
        self.assertTrue((self.out_dir / "bancos_repos_saldos_series.json").exists())

        out_df = pd.read_parquet(self.out_dir / "bancos_repos_saldos_series.parquet")
        # Debe contener la historia preservada (2026-03) más el nuevo período (2026-04)
        self.assertIn("2026-03", out_df["periodo"].values)
        self.assertIn("2026-04", out_df["periodo"].values)


if __name__ == "__main__":
    unittest.main()

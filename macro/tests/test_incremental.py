"""Pruebas sin red para consulta BCCh incremental y preservación del histórico."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from macro.scripts import pipeline_stream_macro_bcch as macro
from macro.scripts.publish_macro import validate


class FakeSiete:
    calls = []
    def __init__(self, user, password):
        pass

    def cuadro(self, series, desde, hasta):
        self.calls.append((series[0], desde, hasta))
        sid = series[0]
        if sid == macro.SERIES_CATALOG['usd_clp_d']['sid']:
            return pd.DataFrame({sid: [950., 951.]}, index=pd.to_datetime(['2026-09-23', '2026-09-24']))
        if sid == macro.SERIES_CATALOG['uf_d']['sid']:
            return pd.DataFrame({sid: [40999., 41000.]}, index=pd.to_datetime(['2026-09-23', '2026-09-24']))
        return pd.DataFrame()


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / 'stage'
        FakeSiete.calls = []

    @patch.object(macro, 'EMAIL_BCCH', 'test-user')
    @patch.object(macro, 'PASS_BCCH', 'test-password')
    @patch.object(macro.bcchapi, 'Siete', FakeSiete)
    def test_queries_only_latest_month_and_preserves_history(self):
        macro.run_macro_pipeline(output_dir=self.out)
        assert len(FakeSiete.calls) == len(macro.SERIES_CATALOG)
        starts = {sid: start for sid, start, _ in FakeSiete.calls}
        assert starts[macro.SERIES_CATALOG['usd_clp_d']['sid']] == '2026-09-01'
        assert starts[macro.SERIES_CATALOG['imacec_m']['sid']] == '2026-07-01'
        assert starts[macro.SERIES_CATALOG['tcr_m']['sid']] == '2026-07-01'
        assert min(starts.values()) >= '2026-06-01'  # cola acotada, nunca backfill diario
        pub = macro.ROOT / 'docs/outputs/macro'
        for name in macro.TABLES:
            old = pd.read_parquet(pub / f'{name}.parquet')
            new = pd.read_parquet(self.out / f'{name}.parquet')
            pd.testing.assert_frame_equal(old.iloc[:-1], new.iloc[:-1], check_dtype=False)
            assert new['periodo'].is_unique
            assert new['periodo'].iloc[-1] == old['periodo'].iloc[-1]
            rows = json.loads((self.out / f'{name}.json').read_text())
            assert len(rows) == len(new)
        validate(self.out, pub)

    def test_merge_new_month_preserves_old_and_calculates_returns(self):
        published = macro.ROOT / 'docs/outputs/macro'
        base = macro.load_baseline(published)
        fresh = {}
        for name, old in base.items():
            row = pd.DataFrame([{col: ('2026-10' if col == 'periodo' else float('nan')) for col in old.columns}])
            if name == 'macro_divisas_mercado':
                row.loc[:, 'usd_clp_cierre'] = 1000.0
                row.loc[:, 'eur_clp_cierre'] = 1100.0
            if name == 'macro_precios_actividad':
                row.loc[:, 'uf_cierre'] = 41000.0
            fresh[name] = pd.concat([old.tail(1), row], ignore_index=True)
        merged = macro.merge_incremental(fresh, base, '2026-09')
        for name in macro.TABLES:
            pd.testing.assert_frame_equal(merged[name].iloc[:-1], base[name], check_dtype=False)
            self.assertEqual(merged[name]['periodo'].iloc[-1], '2026-10')
        fx = merged['macro_divisas_mercado']
        prior = fx.iloc[-2]['usd_clp_cierre']
        self.assertAlmostEqual(fx.iloc[-1]['var_mensual_usd_pct'], round((1000. / prior - 1) * 100, 2))

    def test_lagged_series_retries_last_observed_month_with_bounded_lookback(self):
        baseline = macro.load_baseline(macro.ROOT / 'docs/outputs/macro')
        starts = macro.query_starts(baseline)
        self.assertEqual(starts['usd_clp_d'], '2026-09-01')
        self.assertEqual(starts['imacec_m'], '2026-07-01')
        self.assertEqual(starts['tcr_5_m'], '2026-07-01')
        self.assertEqual(starts['ipc_idx_m'], '2026-08-01')
        # Serie mensual permanentemente vacía: no retroceder ilimitadamente.
        baseline['macro_precios_actividad']['cobre_spot_usd_lb'] = float('nan')
        self.assertEqual(macro.query_starts(baseline)['cobre_m'], '2026-06-01')
        self.assertEqual(macro.query_starts({})['cobre_m'], macro.FETCH_START_DATE)

    @patch.object(macro, 'EMAIL_BCCH', 'test-user')
    @patch.object(macro, 'PASS_BCCH', 'test-password')
    def test_no_observations_fails_without_writing(self):
        class EmptySiete:
            def __init__(self, *args): pass
            def cuadro(self, *args, **kwargs): return pd.DataFrame()
        with patch.object(macro.bcchapi, 'Siete', EmptySiete):
            with self.assertRaisesRegex(RuntimeError, 'no entregó ninguna serie'):
                macro.run_macro_pipeline(output_dir=self.out)
        self.assertFalse(list(self.out.glob('*')) if self.out.exists() else False)

    @patch.object(macro, 'EMAIL_BCCH', 'test-user')
    @patch.object(macro, 'PASS_BCCH', 'test-password')
    @patch.object(macro.bcchapi, 'Siete', FakeSiete)
    def test_failed_api_does_not_write_output(self):
        class BrokenSiete:
            def __init__(self, user, password): pass
            def cuadro(self, *args, **kwargs): raise RuntimeError('auth failed')
        with patch.object(macro.bcchapi, 'Siete', BrokenSiete), patch.object(macro.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'Falló la consulta'):
                macro.run_macro_pipeline(output_dir=self.out)
        assert not list(self.out.glob('*')) if self.out.exists() else True


if __name__ == '__main__':
    unittest.main()

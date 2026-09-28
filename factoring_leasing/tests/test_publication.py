"""Web de Factoring & Leasing: maestro + serie CMF; las muestras cotejadas quedan solo como archivo de auditoría."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from factoring_leasing.scripts.audit_factoring_leasing import OUTPUT, RETIRED, ROOT, run_audit


class PublicationTests(unittest.TestCase):
    def test_only_entity_list_is_published(self):
        # La lista crece sola (altas desde el TXT IFRS): se compara con su tamaño real, mínimo 28.
        n = len(json.loads((OUTPUT / "factoring_leasing_maestro.json").read_text(encoding="utf-8")))
        self.assertGreaterEqual(n, 28)
        self.assertEqual(run_audit(), n)
        files = {p.name for p in OUTPUT.iterdir() if p.is_file()}
        # El backfill completo se publica como dos Parquets separados y con
        # metadata/advertencia, sin reemplazar las muestras previamente cotejadas.
        expected = {'factoring_leasing_maestro.json', 'factoring_leasing_maestro.parquet',
                    'factoring_leasing_eeff_muestra_cmf.parquet',
                    'factoring_leasing_resultados_muestra_cmf.parquet'}
        series = {'factoring_leasing_balance_serie_ifrs_cmf.parquet',
                  'factoring_leasing_resultados_serie_ifrs_cmf.parquet',
                  'factoring_leasing_balance_serie_ifrs_cmf_metadata.json'}
        if (OUTPUT / 'factoring_leasing_balance_serie_ifrs_cmf.parquet').exists():
            expected |= series
        self.assertEqual(files, expected)
        self.assertFalse(files.intersection({f'{name}.{ext}' for name in RETIRED for ext in ('json', 'parquet')}))

    def test_old_files_cannot_pass_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for ext in ('json', 'parquet'):
                shutil.copyfile(OUTPUT / f'factoring_leasing_maestro.{ext}', folder / f'factoring_leasing_maestro.{ext}')
            (folder / 'factoring_leasing_balance_resumen.json').write_text('[]')
            with self.assertRaisesRegex(ValueError, 'Archivos retirados'):
                run_audit(folder)

    def test_stale_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for ext in ('json', 'parquet'):
                shutil.copyfile(OUTPUT / f'factoring_leasing_maestro.{ext}', folder / f'factoring_leasing_maestro.{ext}')
            path = folder / 'factoring_leasing_maestro.json'
            rows = json.loads(path.read_text())
            rows[0]['razon_social'] = 'No coincide'
            path.write_text(json.dumps(rows))
            with self.assertRaisesRegex(ValueError, 'Valores JSON/Parquet'):
                run_audit(folder)

    def test_site_catalogs_and_manifest_expose_series_with_caveats(self):
        site_files = ('sidebar.js', 'data_viewer.js', 'data_dictionary.js',
                      'erd_graph.js', 'duckdb_client.js', 'export_modal.js')
        for file in site_files:
            source = (ROOT / 'docs/js' / file).read_text(encoding='utf-8')
            if file == 'export_modal.js':
                # El exportador no expone la muestra, pero tampoco la lista; se
                # comprueba aparte que no reaparezcan los archivos retirados.
                pass
            else:
                self.assertIn('factoring_leasing_maestro', source, file)
            for name in RETIRED:
                self.assertNotIn(name, source, file)
        manifest = json.loads((ROOT / 'data_manifest.json').read_text(encoding='utf-8'))
        sector = [entry['id'] for entry in manifest['tables']
                  if entry.get('sector') == 'factoring_leasing']
        # Las muestras cotejadas (2 filas) repetían cifras de la serie: fuera del catálogo y de la web.
        expected = ['factoring_leasing_maestro']
        samples = ('factoring_leasing_eeff_muestra_cmf', 'factoring_leasing_resultados_muestra_cmf')
        for file in site_files:
            source = (ROOT / 'docs/js' / file).read_text(encoding='utf-8')
            for name in samples:
                self.assertNotIn(name, source, file)
        full_ids = ['factoring_leasing_balance_serie_ifrs_cmf',
                    'factoring_leasing_resultados_serie_ifrs_cmf']
        if (OUTPUT / f'{full_ids[0]}.parquet').exists():
            expected.extend(full_ids)
            for table_id in full_ids:
                entry = next(x for x in manifest['tables'] if x['id'] == table_id)
                self.assertIn('no cotejadas', entry['descripcion'])
        self.assertEqual(sector, expected)
        self.assertEqual(manifest['total_tables'], len(manifest['tables']))
        self.assertEqual(manifest['total_records'],
                         sum(t.get('registros_reales', 0) for t in manifest['tables']))


if __name__ == '__main__':
    unittest.main()

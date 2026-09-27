"""La lista es la única salida pública de Factoring y Leasing."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from factoring_leasing.scripts.audit_factoring_leasing import OUTPUT, RETIRED, ROOT, run_audit


class PublicationTests(unittest.TestCase):
    def test_only_entity_list_is_published(self):
        self.assertEqual(run_audit(), 28)
        files = {p.name for p in OUTPUT.iterdir() if p.is_file()}
        # La lista de entidades y, aparte, la muestra de dos filas cotejadas con
        # CMF. Ningún otro balance puede reaparecer sin una auditoría propia.
        self.assertEqual(files, {'factoring_leasing_maestro.json', 'factoring_leasing_maestro.parquet',
                                 'factoring_leasing_eeff_muestra_cmf.parquet'})
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

    def test_site_catalogs_and_manifest_expose_only_entity_list(self):
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
        self.assertEqual(sector, ['factoring_leasing_maestro', 'factoring_leasing_eeff_muestra_cmf'])
        self.assertEqual(manifest['total_tables'], len(manifest['tables']))
        self.assertEqual(manifest['total_records'],
                         sum(t.get('registros_reales', 0) for t in manifest['tables']))

    def test_legacy_pipeline_entrypoints_fail_before_writing(self):
        from factoring_leasing.scripts import pipeline_stream_factoring_leasing as pipeline
        from factoring_leasing.scripts import stream_cmf_eeff_series as streaming
        with self.assertRaisesRegex(RuntimeError, 'suspendida'):
            pipeline.run_factoring_leasing_pipeline()
        with self.assertRaisesRegex(RuntimeError, 'suspendida'):
            streaming.run_cmf_streaming_pipeline([])


if __name__ == '__main__':
    unittest.main()

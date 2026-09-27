"""Publicador web de la serie: solo completo, sin pérdidas ni sumas."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

extract = load_module('backfill_for_publish_test', HERE / 'scripts/backfill_ifrs.py')
publish = load_module('publish_backfill_test', HERE / 'scripts/publish_backfill.py')
CATALOG = {'96655860': {'rut':'96655860-1','segmento':'Factoring','nombre':'FACTORING SECURITY S.A.'}}


def source(period='202206', value='123456789', repeat=False):
    rows = [
        f'{period};96655860;FACTORING SECURITY S.A.;I;CLP;Total de activos;{value};TAX CI;ESF C/NC',
        f'{period};96655860;FACTORING SECURITY S.A.;I;CLP;Ganancia antes de impuestos;42;TAX CI;ERFG',
        f'{period};96655860;FACTORING SECURITY S.A.;I;CLP;Ganancia antes de impuestos;NO_APLICA;TAX CI;ERFG',
    ]
    if repeat:
        rows.append(rows[0])
    return ('\n'.join(rows) + '\n').encode()


def make_docs(root):
    docs = root / 'docs'
    (docs / 'js').mkdir(parents=True)
    (docs / 'outputs' / 'factoring_leasing').mkdir(parents=True)
    fixtures = {
        'duckdb_client.js': 'const SEMANTIC_VIEWS = [\n  // BEGIN AUTO FL IFRS SERIES VIEWS\n  // END AUTO FL IFRS SERIES VIEWS\n];\n',
        'sidebar.js': 'const EXPLORER_TREE = [{ children: [\n          // BEGIN AUTO FL IFRS SERIES NAVIGATION\n          // END AUTO FL IFRS SERIES NAVIGATION\n] }];\n',
        'data_viewer.js': 'const DATA_VIEWER_CATALOG = [{ tables: [\n      // BEGIN AUTO FL IFRS SERIES VIEWER\n      // END AUTO FL IFRS SERIES VIEWER\n] }];\n',
        'data_dictionary.js': 'const DATA_DICTIONARY = [\n  // BEGIN AUTO FL IFRS SERIES DICTIONARY\n  // END AUTO FL IFRS SERIES DICTIONARY\n];\n',
    }
    for name, content in fixtures.items():
        (docs / 'js' / name).write_text(content)
    (docs / 'index.html').write_text('\n'.join(
        f'<script src="js/{name}?v=old"></script>'
        for name in ('duckdb_client.js','sidebar.js','data_dictionary.js','data_viewer.js')))
    return docs


class PublishBackfillTests(unittest.TestCase):
    def setup_data(self, root, periods=('202206','202209')):
        data = root / 'data'
        data.mkdir()
        catalog_file = root / 'catalog.json'
        catalog_file.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
        catalog_hash = extract.hashlib.sha256(catalog_file.read_bytes()).hexdigest()
        for per in periods:
            bal, inc, stats = extract.parse_period(source(per, repeat=(per == periods[0])), per, CATALOG,
                                                   f'https://cmf.invalid/{per}')
            stats.update(periodo=per, sha256_catalogo=catalog_hash,
                         filas_balance=len(bal), filas_resultados=len(inc))
            extract.save_period(data, per, bal, inc, stats)
        summary = {
            'estado_global':'completo_sin_publicar','publicado_en_web':False,
            'sha256_catalogo':catalog_hash,'fuente_indice':'https://cmf.invalid/index',
            'rut_catalogo':1,'periodos_indice':len(periods),
            'periodos_indice_lista':list(periods),'primer_periodo':periods[0],
            'ultimo_periodo':periods[-1],'pendientes':[],'errores':[],
            'filas_balance_total':sum(extract.pd.read_parquet(data/'periodos'/p/'balance.parquet').shape[0] for p in periods),
            'filas_resultados_total':sum(extract.pd.read_parquet(data/'periodos'/p/'resultados.parquet').shape[0] for p in periods),
            'ruts_con_datos_total':['96655860-1'],'ruts_sin_datos_hasta_ahora':[],
            'importes_no_enteros_total':len(periods),'cuentas_contexto_repetidas_total':int(periods[0] == '202206'),
        }
        (data/'resumen.json').write_text(json.dumps(summary))
        return data, summary

    def test_incomplete_backfill_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            data, summary = self.setup_data(root)
            summary['estado_global'] = 'en_progreso_sin_publicar'
            summary['pendientes'] = ['202212']
            (data/'resumen.json').write_text(json.dumps(summary))
            self.assertFalse(publish.publish(data, docs, '123'))
            self.assertFalse((docs/'outputs/factoring_leasing'/f'{publish.BALANCE}.parquet').exists())
            self.assertIn('// BEGIN AUTO FL IFRS SERIES VIEWS\n  // END',
                          (docs/'js/duckdb_client.js').read_text())

    def test_complete_series_builds_two_public_tables_and_catalogs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            data, _ = self.setup_data(root)
            self.assertTrue(publish.publish(data, docs, '12345'))
            out = docs/'outputs/factoring_leasing'
            balance = extract.pd.read_parquet(out/f'{publish.BALANCE}.parquet')
            results = extract.pd.read_parquet(out/f'{publish.RESULTS}.parquet')
            self.assertEqual(len(balance), 3)  # repetición explícita, no suma ni deduplicación
            self.assertEqual(len(results), 4)  # dos resultados por período, incluso texto no entero
            self.assertEqual(str(balance['valor_archivo'].dtype), 'Int64')
            self.assertEqual(balance['valor_archivo'].iloc[0], 123456789)
            self.assertEqual(balance['repeticion_contexto'].max(), 2)
            self.assertIn('NO_APLICA', set(results['valor_texto_original']))
            self.assertTrue(results.loc[results['valor_texto_original']=='NO_APLICA','valor_archivo'].isna().all())
            self.assertTrue((results['estado_financiero'].str.startswith('ER')).all())
            self.assertTrue((balance['estado_financiero'].str.startswith('ESF')).all())
            meta = json.loads((out/f'{publish.BALANCE}_metadata.json').read_text())
            self.assertTrue(meta['publicado_en_docs'])
            self.assertEqual(meta['run_actions'], '12345')
            for file in ['duckdb_client.js','sidebar.js','data_viewer.js','data_dictionary.js']:
                text=(docs/'js'/file).read_text()
                self.assertIn(publish.BALANCE, text)
                self.assertIn(publish.RESULTS, text)
            index=(docs/'index.html').read_text()
            self.assertNotIn('?v=old', index)
            self.assertIn('fl-202209-', index)
            # Catálogos generados son JS válido y los dos datasets aparecen aislados.
            import subprocess
            for file in ['duckdb_client.js','sidebar.js','data_viewer.js','data_dictionary.js']:
                subprocess.run(['node','-c',str(docs/'js'/file)],check=True,capture_output=True,text=True)

    def test_publisher_detects_missing_or_corrupted_period(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); docs=make_docs(root); data, summary=self.setup_data(root)
            (data/'periodos/202209/resultados.parquet').unlink()
            loaded, reason=publish.load_complete(data)
            self.assertIsNone(loaded)
            self.assertIn('Parquet ausente', reason)
            self.assertFalse(publish.publish(data, docs, '1'))

    def test_catalog_marker_must_be_unique(self):
        with self.assertRaisesRegex(ValueError, 'Markers ausentes/duplicados'):
            publish.replace_block('// X\n// END\n', '// BEGIN', '// END', '', 'fixture')

if __name__ == '__main__':
    unittest.main()

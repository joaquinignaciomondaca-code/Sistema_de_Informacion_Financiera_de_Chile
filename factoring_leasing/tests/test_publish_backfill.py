"""Publicador web de la serie: solo completo, sin pérdidas ni sumas."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
RAIZ = HERE.parent

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
    # El vocabulario canónico real: de ahí salen los ids y nombres que el publicador
    # inyecta en los catálogos web. Con una copia sintética, un desvío de nombres
    # (publicar con un alias retirado) pasaría desapercibido en las pruebas.
    shutil.copyfile(RAIZ / 'docs' / 'vocabulario.json', docs / 'vocabulario.json')
    (docs / 'index.html').write_text('\n'.join(
        f'<script src="js/{name}?v=old"></script>'
        for name in ('duckdb_client.js','sidebar.js','data_dictionary.js','data_viewer.js')))
    (root / 'data_manifest.json').write_text(json.dumps({
        'version':'1.0.0','updated_at':'2026-09-27','total_tables':3,'total_records':32,
        'tables':[{'id':'factoring_leasing_maestro','registros_reales':28},
                  {'id':'factoring_leasing_eeff_muestra_cmf','registros_reales':2},
                  {'id':'factoring_leasing_resultados_muestra_cmf','registros_reales':2}]}))
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
            manifest = json.loads((root/'data_manifest.json').read_text())
            sector_ids = [x['id'] for x in manifest['tables'] if x.get('sector') == 'factoring_leasing']
            self.assertEqual(sector_ids, [publish.BALANCE, publish.RESULTS])
            self.assertEqual(manifest['total_tables'], len(manifest['tables']))
            self.assertEqual(manifest['total_records'], sum(x.get('registros_reales', 0) for x in manifest['tables']))
            vocab = publish.vocabulario(RAIZ / 'docs' / 'vocabulario.json')
            retirados = [publish.BALANCE, publish.RESULTS]
            for file in ['duckdb_client.js','sidebar.js','data_viewer.js','data_dictionary.js']:
                text=(docs/'js'/file).read_text()
                for clave in ('balance','resultados'):
                    self.assertIn(vocab[clave]['id'], text)
                    if file != 'duckdb_client.js':
                        # El cliente DuckDB registra la vista por su id; el nombre
                        # punteado (<sector>.<tipo>) es el de los catálogos visibles.
                        self.assertIn(vocab[clave]['nombre'], text)
                # El nombre largo es sólo el del archivo: nunca un identificador web.
                for viejo in retirados:
                    for patron in (f'id: "{viejo}"', f'name: "{viejo}"', f'FROM {viejo}',
                                   f'"id":"{viejo}"', f'"name":"{viejo}"', f'"viewName":"{viejo}"'):
                        self.assertNotIn(patron, text)
            sidebar_text=(docs/'js/sidebar.js').read_text()
            for clave in ('balance','resultados'):
                self.assertIn(vocab[clave]['carpeta'], sidebar_text)
                self.assertIn(f"outputs/factoring_leasing/{vocab[clave]['archivo']}.parquet", sidebar_text)
                # Las consultas de los chips deben apuntar a la vista registrada.
                self.assertIn(f"FROM {vocab[clave]['id']}", sidebar_text)
            self.assertIn('2022-06–2022-09', (docs/'js/sidebar.js').read_text())
            self.assertIn('2022-06 a 2022-09', (docs/'js/data_dictionary.js').read_text())
            index=(docs/'index.html').read_text()
            self.assertNotIn('?v=old', index)
            self.assertIn('fl-202209-', index)
            # Catálogos generados son JS válido y los dos datasets aparecen aislados.
            import subprocess
            for file in ['duckdb_client.js','sidebar.js','data_viewer.js','data_dictionary.js']:
                subprocess.run(['node','-c',str(docs/'js'/file)],check=True,capture_output=True,text=True)

    def test_unchanged_daily_run_does_not_churn_publication_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); docs=make_docs(root); data,_=self.setup_data(root)
            self.assertTrue(publish.publish(data,docs,'12345'))
            meta_path=docs/'outputs/factoring_leasing'/f'{publish.BALANCE}_metadata.json'
            manifest_path=root/'data_manifest.json'
            first=meta_path.read_bytes()
            first_manifest=manifest_path.read_bytes()
            self.assertTrue(publish.publish(data,docs,'67890'))
            current=json.loads(meta_path.read_text())
            self.assertEqual(current['run_actions'],'12345')
            self.assertEqual(meta_path.read_bytes(),first)
            self.assertEqual(manifest_path.read_bytes(),first_manifest)

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

    def test_all_local_assets_share_one_version_tag(self):
        """scripts/audit_interfaz.py exige una sola etiqueta de versión en index.html."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            index = docs / 'index.html'
            # Otros assets del sitio con la etiqueta vigente, como en el index.html real.
            index.write_text(index.read_text() +
                             '\n<link href="css/estilo.css?v=20260929-seguridad-1">'
                             '\n<script src="js/ux_shell.js?v=20260929-seguridad-1"></script>\n')
            data, _ = self.setup_data(root)
            self.assertTrue(publish.publish(data, docs, '12345'))
            etiquetas = set(re.findall(r'(?:src|href)="(?:css|js)/[^"?]+\?v=([^"]+)"',
                                       index.read_text()))
            self.assertEqual(len(etiquetas), 1, f'quedaron varias etiquetas: {etiquetas}')
            self.assertTrue(etiquetas.pop().startswith('fl-202209-'))

    def test_missing_vocabulary_entry_is_explicit(self):
        """Sin entrada canónica el publicador falla en vez de inventar identificadores."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            vocab = json.loads((docs / 'vocabulario.json').read_text(encoding='utf-8'))
            vocab['tablas'] = [t for t in vocab['tablas'] if t['id'] not in
                               ('factoring_leasing_balance', 'factoring_leasing_resultados')]
            (docs / 'vocabulario.json').write_text(json.dumps(vocab, ensure_ascii=False))
            data, _ = self.setup_data(root)
            with self.assertRaisesRegex(ValueError, 'vocabulario canónico'):
                publish.publish(data, docs, '12345')

class CuadraturaYCatalogosTests(unittest.TestCase):
    """Compuerta contable previa a la publicación y regeneración de catálogos sin staging."""

    def staging(self, root, balances, periodo='202206', rut_catalogo=None):
        """Staging de un trimestre con varias sociedades: `balances` = [(activos, pasivos, patrimonio)]."""
        catalog, lines = {}, []
        for i, (a, pas, pat) in enumerate(balances):
            body = str(76100000 + i)
            nombre = f'FACTORING {i} S.A.'
            catalog[body] = {'rut': extract.con_dv(body), 'segmento': 'Factoring', 'nombre': nombre}
            for cuenta, valor in (('Total de activos', a), ('Total de pasivos', pas), ('Patrimonio total', pat)):
                lines.append(f'{periodo};{body};{nombre};I;CLP;{cuenta};{valor};TAX CI;ESF C/NC')
            lines.append(f'{periodo};{body};{nombre};I;CLP;Ganancia (pérdida);10;TAX CI;ERFG')
        data = root / 'data'
        data.mkdir()
        balance, income, stats = extract.parse_period(('\n'.join(lines) + '\n').encode(), periodo, catalog,
                                                      f'https://cmf.invalid/{periodo}')
        stats.update(periodo=periodo, sha256_catalogo='h', filas_balance=len(balance), filas_resultados=len(income))
        extract.save_period(data, periodo, balance, income, stats)
        summary = {
            'estado_global': 'completo_sin_publicar', 'publicado_en_web': False, 'sha256_catalogo': 'h',
            'fuente_indice': 'https://cmf.invalid/index', 'rut_catalogo': rut_catalogo or len(balances),
            'periodos_indice': 1, 'periodos_indice_lista': [periodo], 'primer_periodo': periodo,
            'ultimo_periodo': periodo, 'pendientes': [], 'errores': [],
            'filas_balance_total': len(balance), 'filas_resultados_total': len(income),
            'ruts_con_datos_total': [v['rut'] for v in catalog.values()], 'ruts_sin_datos_hasta_ahora': [],
            'importes_no_enteros_total': 0, 'cuentas_contexto_repetidas_total': 0,
        }
        (data / 'resumen.json').write_text(json.dumps(summary))
        return data

    CUADRADOS = [(10_000_000, 4_000_000, 6_000_000)] * 25
    # 10 de 25 con el patrimonio en 1.000.000: muy por sobre la tolerancia de 1.000 pesos.
    DESCUADRADOS = [(10_000_000, 4_000_000, 1_000_000)] * 10 + [(10_000_000, 4_000_000, 6_000_000)] * 15

    def test_una_serie_que_cuadra_se_publica_y_deja_las_estadisticas_en_la_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            data = self.staging(root, self.CUADRADOS)
            self.assertTrue(publish.publish(data, docs, '1'))
            meta = json.loads((docs / 'outputs/factoring_leasing' / f'{publish.BALANCE}_metadata.json').read_text())
            self.assertEqual(meta['cuadratura'], {
                'balances_totales': 25, 'balances_verificados': 25, 'balances_descuadrados': 0,
                'identidades_resultados': 0, 'identidades_divergentes': 0})

    def test_una_falla_en_bloque_bloquea_la_publicacion_y_no_escribe_nada(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            data = self.staging(root, self.DESCUADRADOS)
            antes = {f: (docs / 'js' / f).read_text() for f in ('duckdb_client.js', 'sidebar.js', 'data_dictionary.js')}
            manifest_antes = (root / 'data_manifest.json').read_text()
            with self.assertRaisesRegex(ValueError, 'cuadratura'):
                publish.publish(data, docs, '1')
            salida = docs / 'outputs/factoring_leasing'
            self.assertFalse((salida / f'{publish.BALANCE}.parquet').exists())
            self.assertFalse((salida / f'{publish.BALANCE}_metadata.json').exists())
            self.assertEqual(manifest_antes, (root / 'data_manifest.json').read_text())
            for f, texto in antes.items():
                self.assertEqual(texto, (docs / 'js' / f).read_text())

    def test_la_falla_deja_la_corrida_en_rojo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            data = self.staging(root, self.DESCUADRADOS)
            argv = ['publish_backfill.py', '--data', str(data), '--docs', str(docs)]
            with mock.patch.object(sys, 'argv', argv):
                self.assertEqual(publish.main(), 1)

    def test_un_descuadre_aislado_no_detiene_pero_queda_contado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            data = self.staging(root, [(10_000_000, 4_000_000, 1_000_000)] + self.CUADRADOS[:24])
            self.assertTrue(publish.publish(data, docs, '1'))
            meta = json.loads((docs / 'outputs/factoring_leasing' / f'{publish.BALANCE}_metadata.json').read_text())
            self.assertEqual(meta['cuadratura']['balances_descuadrados'], 1)

    def test_cifras_de_cobertura_salen_de_la_metadata_y_no_estan_fijas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); docs = make_docs(root)
            data = self.staging(root, self.CUADRADOS, rut_catalogo=32)
            self.assertTrue(publish.publish(data, docs, '1'))
            manifest = json.loads((root / 'data_manifest.json').read_text())
            origenes = [t['origen'] for t in manifest['tables'] if t.get('sector') == 'factoring_leasing']
            self.assertEqual(len(origenes), 2)
            for origen in origenes:
                self.assertIn('25/32 RUT del catálogo con datos', origen)
                self.assertNotIn('/28', origen)
            diccionario = (docs / 'js/data_dictionary.js').read_text()
            self.assertIn('25/32 RUT del catálogo con datos en la fuente', diccionario)
            self.assertNotIn('24/28', diccionario)

    def _copiar_publicacion(self, docs_origen, root_destino):
        """Una rama «más nueva»: mismos catálogos de base, solo llegan los datos publicados."""
        docs = make_docs(root_destino)
        for nombre in (publish.BALANCE, publish.RESULTS):
            shutil.copyfile(docs_origen / 'outputs/factoring_leasing' / f'{nombre}.parquet',
                            docs / 'outputs/factoring_leasing' / f'{nombre}.parquet')
        shutil.copyfile(docs_origen / 'outputs/factoring_leasing' / f'{publish.BALANCE}_metadata.json',
                        docs / 'outputs/factoring_leasing' / f'{publish.BALANCE}_metadata.json')
        return docs

    def test_solo_catalogos_regenera_lo_mismo_que_la_publicacion_completa(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / 'a'; b = Path(tmp) / 'b'; a.mkdir(); b.mkdir()
            docs_a = make_docs(a)
            self.assertTrue(publish.publish(self.staging(a, self.CUADRADOS, rut_catalogo=32), docs_a, '77'))
            docs_b = self._copiar_publicacion(docs_a, b)
            publish.republicar_catalogos(docs_b)
            for archivo in ('duckdb_client.js', 'sidebar.js', 'data_viewer.js', 'data_dictionary.js'):
                self.assertEqual((docs_a / 'js' / archivo).read_text(), (docs_b / 'js' / archivo).read_text(), archivo)
            self.assertEqual((docs_a / 'index.html').read_text(), (docs_b / 'index.html').read_text())
            self.assertEqual((a / 'data_manifest.json').read_text(), (b / 'data_manifest.json').read_text())

    def test_solo_catalogos_se_aplica_sobre_el_manifiesto_vigente_sin_pisar_a_los_demas(self):
        """Lo que justifica el modo: otro publicador editó data_manifest.json mientras corría este."""
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / 'a'; b = Path(tmp) / 'b'; a.mkdir(); b.mkdir()
            docs_a = make_docs(a)
            self.assertTrue(publish.publish(self.staging(a, self.CUADRADOS), docs_a, '77'))
            docs_b = self._copiar_publicacion(docs_a, b)
            vigente = json.loads((b / 'data_manifest.json').read_text())
            vigente['tables'].append({'id': 'otra_tabla', 'registros_reales': 1000})
            vigente['tables'][0]['registros_reales'] = 99
            (b / 'data_manifest.json').write_text(json.dumps(vigente))
            publish.republicar_catalogos(docs_b)
            final = json.loads((b / 'data_manifest.json').read_text())
            por_id = {t['id']: t for t in final['tables']}
            self.assertEqual(por_id['otra_tabla']['registros_reales'], 1000)           # lo ajeno se conserva
            self.assertEqual(por_id['factoring_leasing_maestro']['registros_reales'], 99)
            self.assertIn(publish.BALANCE, por_id)
            self.assertEqual(final['total_records'], sum(t.get('registros_reales', 0) for t in final['tables']))

    def test_solo_catalogos_se_niega_si_los_parquet_no_son_los_de_la_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / 'a'; b = Path(tmp) / 'b'; a.mkdir(); b.mkdir()
            docs_a = make_docs(a)
            self.assertTrue(publish.publish(self.staging(a, self.CUADRADOS), docs_a, '77'))
            docs_b = self._copiar_publicacion(docs_a, b)
            parquet = docs_b / 'outputs/factoring_leasing' / f'{publish.BALANCE}.parquet'
            parquet.write_bytes(parquet.read_bytes() + b'x')
            with self.assertRaisesRegex(ValueError, 'no coincide con la metadata'):
                publish.republicar_catalogos(docs_b)

    def test_solo_catalogos_sin_publicacion_previa_es_un_error_claro(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = make_docs(Path(tmp))
            with self.assertRaisesRegex(ValueError, 'No hay metadata publicada'):
                publish.republicar_catalogos(docs)


if __name__ == '__main__':
    unittest.main()

"""Descarga masiva en cuarentena; pruebas sin red ni escrituras en el sitio."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

SPEC = importlib.util.spec_from_file_location('backfill_ifrs', Path(__file__).resolve().parents[1] / 'scripts/backfill_ifrs.py')
b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(b)
CATALOG = {'96655860': {'rut': '96655860-1', 'segmento': 'Factoring', 'nombre': 'FACTORING SECURITY S.A.'}}


def fixture(period='202206', rut='96655860', name='FACTORING SECURITY S.A.'):
    lines = []
    for kind, state, currency in [('I', 'ESF C/NC', 'CLP'), ('C', 'ESF C/NC', 'USD')]:
        for account, value in [('Total de activos', '435359519000'),
                               ('Total de pasivos', '376903204000'), ('Patrimonio total', '58456315000')]:
            lines.append(f'{period};{rut};{name};{kind};{currency};{account};{value};TAX CI;{state}')
    lines.append(f'{period};{rut};{name};I;CLP;Ganancia (pérdida), antes de impuestos;8148312000;TAX CI;ERFG')
    lines.append('202206;12345678;OTRA;I;CLP;Total de activos;1;TAX CI;ESF C/NC')
    return ('\n'.join(lines) + '\n').encode()


class BackfillTests(unittest.TestCase):
    def test_index_annual_and_quarterly_links(self):
        html = b'''<html><a href="ver_archivo.php?inicio=202203&amp;termino=202212">2022</a>
        <a href="ver_archivo.php?inicio=202603&termino=202603">Marzo 2026</a></html>'''
        self.assertEqual(b.periods_from_index(html), ['202203','202206','202209','202212','202603'])

    def test_index_does_not_accept_error_page(self):
        with self.assertRaises(ValueError):
            b.periods_from_index(b'ACCION NO PERMITIDA')

    def test_all_accounts_preserved_separate_by_statement_and_context(self):
        balance, income, stats = b.parse_period(fixture(), '202206', CATALOG)
        self.assertEqual((len(balance), len(income), stats['entidades']), (6, 1, 1))
        self.assertEqual({r['tipo_balance'] for r in balance}, {'I', 'C'})
        self.assertEqual({r['moneda_archivo'] for r in balance}, {'CLP','USD'})
        self.assertEqual(balance[0]['valor_archivo'], 435359519000)
        self.assertFalse(any(r['cuenta'].startswith('Ganancia') for r in balance))
        self.assertNotIn('resultado', stats)

    def test_previous_entity_name_not_forced_to_current(self):
        balance, _, stats = b.parse_period(fixture(name='NOMBRE HISTORICO S.A.'), '202206', CATALOG)
        self.assertEqual(stats['nombres_distintos_catalogo'], 1)
        self.assertEqual(balance[0]['nombre_reportado'], 'NOMBRE HISTORICO S.A.')
        self.assertFalse(balance[0]['identidad_nombre_coincide_catalogo'])

    def test_missing_target_is_explicit(self):
        balance, income, stats = b.parse_period(fixture(rut='12345678'), '202206', CATALOG)
        self.assertEqual((balance, income, stats['estado']), ([], [], 'sin_rut_catalogo'))

    def test_wrong_period_and_duplicate_kept_not_summed(self):
        with self.assertRaisesRegex(ValueError, 'período'):
            b.parse_period(fixture(period='202209'), '202206', CATALOG)
        duplicate = fixture().splitlines()[0]
        balance, income, stats = b.parse_period(fixture() + duplicate + b'\n', '202206', CATALOG)
        self.assertEqual(stats['cuentas_contexto_repetidas'], 1)
        self.assertEqual((len(balance), len(income)), (7, 1))
        self.assertEqual(balance[-1]['repeticion_contexto'], 2)
        self.assertEqual(balance[-1]['valor_archivo'], 435359519000)

    def test_noninteger_kept_as_text_not_zero(self):
        balance, _, stats = b.parse_period(fixture().replace(b'435359519000', b'NO_APLICA'), '202206', CATALOG)
        self.assertEqual(stats['importes_no_enteros'], 2)  # individual y consolidado
        self.assertIsNone(balance[0]['valor_archivo'])
        self.assertEqual(balance[0]['valor_texto_original'], 'NO_APLICA')
        self.assertFalse(balance[0]['valor_es_entero'])
        with self.assertRaisesRegex(ValueError, 'no es el archivo'):
            b.parse_period(b'<html>error</html>', '202206', CATALOG)

    def test_resume_skips_saved_period_and_keeps_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            index = b'<html><a href="ver_archivo.php?inicio=202203&termino=202206">2022</a></html>'
            seen = []
            def fetch(url):
                seen.append(url)
                return index if url == b.INDEX else fixture(period=url.split('inicio=')[1][:6])
            args = SimpleNamespace(out=out, catalog=Path(tmp) / 'catalog.json', batch=1)
            args.catalog.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
            self.assertEqual(b.run(args, fetch), 0)
            self.assertTrue((out/'periodos/202206/_complete.json').is_file())
            self.assertFalse((out/'periodos/202203/_complete.json').exists())
            self.assertEqual(b.run(args, fetch), 0)
            self.assertTrue((out/'periodos/202203/_complete.json').is_file())
            self.assertEqual(len(seen), 4) # 2 index + 2 unique archive downloads
            self.assertEqual(len(b.pd.read_parquet(out/'periodos/202206/balance.parquet')), 6)
            self.assertEqual(len(b.pd.read_parquet(out/'periodos/202206/resultados.parquet')), 1)
            self.assertEqual(b.run(args, fetch), 0)
            self.assertEqual(len(seen), 5) # only index on completed run

    def test_failure_does_not_mark_period_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            args = SimpleNamespace(out=out, catalog=Path(tmp)/'catalog.json', batch=2)
            args.catalog.write_text(json.dumps([{'rut':'96655860-1','segmento':'Factoring','razon_social':'FACTORING SECURITY S.A.'}]))
            def fetch(url):
                return b'<html><a href="ver_archivo.php?inicio=202206&termino=202206">1</a></html>'
            self.assertEqual(b.run(args, fetch), 1)
            self.assertFalse((out/'periodos/202206/_complete.json').exists())
            self.assertEqual(json.loads((out/'resumen.json').read_text())['estado_global'], 'error')

if __name__ == '__main__':
    unittest.main()

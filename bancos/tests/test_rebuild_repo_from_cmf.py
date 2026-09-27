import io
import unittest
import zipfile
from bancos.scripts.rebuild_repo_from_cmf import amount, read_b1, extract, compare, reconcile_system_total

URL = 'https://www.cmfchile.cl/portal/estadisticas/626/articles-51912_recurso_1.zip'


def b1(code, a, p, bank='012'):
    return (bank + '\tBANCO DEL ESTADO\n' + code[0] + '\t' + '\t'.join(a) + '\n' +
            code[1] + '\t' + '\t'.join(p) + '\n').encode()


class RebuildTest(unittest.TestCase):
    def test_bancoestado_from_real_sample_values(self):
        raw = b1(('141000000', '243000000'),
                 ['0013249012066,00', '0,00', '0,00', '0,00'],
                 ['0806202143144,00', '0,00', '0,00', '0751586563392,00'])
        row = read_b1(raw, '2022-06', '012')
        self.assertEqual(row['repo_activo_mm_clp'], '13249.01')
        self.assertEqual(row['repo_pasivo_mm_clp'], '1557788.71')
        self.assertEqual(row['clase_para_revision'], 'codigo_sin_identidad_certificada')

    def test_2024_header_without_leading_zeros_and_integer_pesos(self):
        raw = b1(('141000000', '243000000'),
                 ['000073814715285'] + ['0']*3,
                 ['000199328917335', '0', '0', '000015087973691'], '1')
        row = read_b1(raw, '2024-06', '001')
        self.assertEqual(row['repo_activo_mm_clp'], '73814.72')
        self.assertEqual(row['repo_pasivo_mm_clp'], '214416.89')

    def test_2021_units_and_no_fabricated_zero(self):
        raw = b1(('1160000', '2160000'), ['64365,00'] + ['0,00']*3,
                 ['87671,00', '0,00', '0,00', '7338,00'], '001')
        self.assertEqual(read_b1(raw, '2021-12', '001')['repo_pasivo_mm_clp'], '95009.00')
        with self.assertRaises(ValueError):
            read_b1(raw.replace(b'7338,00', b'-'), '2021-12', '001')
        with self.assertRaises(ValueError):
            read_b1(raw.replace(b'2160000\t', b'2160001\t'), '2021-12', '001')
        with self.assertRaises(ValueError):
            read_b1(raw.replace(b'001\t', b'012\t', 1), '2021-12', '001')

    def test_four_fields_required_duplicates_forbidden(self):
        raw = b1(('141000000', '243000000'), ['1', '0', '0', '0'], ['2', '0', '0', '0'])
        with self.assertRaises(ValueError):
            read_b1(raw.replace(b'1\t0\t0\t0', b'1\t0\t0'), '2022-06', '012')
        with self.assertRaises(ValueError):
            read_b1(raw + raw.splitlines()[1] + b'\n', '2022-06', '012')

    def test_zip_extraction_and_missing_separate(self):
        raw = b1(('141000000', '243000000'), ['1']+['0']*3, ['2']+['0']*3)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('pkg/b1202206012.txt', raw)
            z.writestr('pkg/b2202206012.txt', raw)
        month = extract(buf.getvalue(), '2022-06', URL)
        self.assertEqual(len(month['filas']), 1)
        comparison = compare(month, {('2022-06', '001'): {'repo_activo_mm_clp': 0, 'repo_pasivo_mm_clp': 0}})
        self.assertEqual(comparison['solo_cmf'], ['012'])
        self.assertEqual(comparison['solo_legacy'], ['001'])

    def test_total_sistema_is_aggregate_even_if_not_in_legacy(self):
        raw = b1(('141000000', '243000000'), ['1']+['0']*3, ['2']+['0']*3, '999')
        row = read_b1(raw, '2022-06', '999')
        self.assertEqual(row['clase_para_revision'], 'agregado')

    def test_total_system_excludes_aggregates(self):
        raw = b1(('141000000', '243000000'), ['1000000']+['0']*3, ['2000000']+['0']*3)
        bank = read_b1(raw, '2022-06', '012')
        total = read_b1(raw.replace(b'012\t', b'999\t', 1), '2022-06', '999')
        doc = {'periodo': '2022-06', 'filas': [bank, total]}
        self.assertEqual(reconcile_system_total(doc)['activo']['diferencia_mm_clp'], '0.00')
        larger = dict(total, repo_activo_mm_clp='0.00', repo_pasivo_mm_clp='0.00')
        result = reconcile_system_total({'periodo': '2022-06', 'filas': [bank, larger]})
        self.assertEqual(result['exclusion_individual_que_concilia_ambos_lados'], ['012'])
        with self.assertRaises(ValueError):
            reconcile_system_total({'periodo': '2022-06', 'filas': [bank]})

    def test_invalid_cell(self):
        with self.assertRaises(ValueError):
            amount('invalid', False)


if __name__ == '__main__':
    unittest.main()

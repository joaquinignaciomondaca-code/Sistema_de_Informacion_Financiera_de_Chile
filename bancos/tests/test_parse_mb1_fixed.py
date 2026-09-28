"""El monto total NO se debe sumar con sus desgloses por moneda."""
import unittest
from bancos.scripts.parse_mb1_fixed import parse_record


def sample(code, amounts):
    return code + ''.join(f'{v:+015d}' for v in amounts)


class MB1Test(unittest.TestCase):
    def test_2022_pasivo_bancoestado(self):
        line = sample('243000000', [1557788706536, 806202143144, 0, 0, 751586563392])
        row = parse_record(line, '2022-06')
        self.assertEqual(row.total, 1557788706536)
        self.assertEqual(row.unidad, 'pesos_clp')
        self.assertNotEqual(row.total, row.total + sum(row.monedas))

    def test_2021_mm_clp(self):
        row = parse_record(sample('2160000', [95009, 87671, 7338, 0, 0]), '2021-12')
        self.assertEqual(row.total, 95009)
        self.assertEqual(row.unidad, 'millones_clp')

    def test_broken_total_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'no cuadra'):
            parse_record(sample('243000000', [200, 100, 0, 0, 0]), '2022-06')

    def test_tab_delimited_b1_is_not_mb1(self):
        with self.assertRaises(ValueError):
            parse_record('243000000\t806202143144\t751586563392', '2022-06')


if __name__ == '__main__':
    unittest.main()

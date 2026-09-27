import unittest
from decimal import Decimal
from bancos.scripts.audit_repo_fx_sii import parse_old_table, compare_year, HEADER


def table(year=2008):
    rows = ['<table><tr>' + ''.join(f'<th>{h}</th>' for h in HEADER) + '</tr>']
    for day in range(1, 32):
        vals = [str(day)] + [f'{day + month},20' if day < 31 else ''
                             for month in range(1, 13)]
        rows.append('<tr>' + ''.join(f'<td>{v}</td>' for v in vals) + '</tr>')
    rows.append('<tr><td>Promedio</td>' + '<td>0</td>'*12 + '</tr></table>')
    return ''.join(rows)


class SiiFxTest(unittest.TestCase):
    def test_last_published_not_last_calendar_or_average(self):
        values = parse_old_table(table(), 2008)
        self.assertEqual(values['2008-02'], Decimal('32.20'))
        self.assertEqual(len(values), 12)
        report = compare_year(2008, table(), values)
        self.assertEqual(report['estado'], 'COINCIDE')

    def test_changed_or_missing_table_never_counts_as_match(self):
        self.assertEqual(compare_year(2013, '<html></html>', {})['estado'], 'SIN_VERIFICAR')
        self.assertEqual(compare_year(2008, table().replace('Promedio', 'Total'), {})['estado'], 'SIN_VERIFICAR')
        values = parse_old_table(table(), 2008)
        values['2008-02'] = Decimal('40')
        report = compare_year(2008, table(), values)
        self.assertEqual(report['estado'], 'DIFERENCIA')
        self.assertEqual(report['discrepancias'][0]['mes'], '2008-02')


if __name__ == '__main__':
    unittest.main()

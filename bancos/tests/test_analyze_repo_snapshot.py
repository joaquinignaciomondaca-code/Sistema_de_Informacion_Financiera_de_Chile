import unittest
from bancos.scripts.analyze_repo_snapshot import analyze


def legacy(month, code, a, p):
    return {'periodo': month, 'codigo_institucion': code,
            'repo_activo_mm_clp': a, 'repo_pasivo_mm_clp': p}


def snapshot(month, rows):
    return {'estado': 'BORRADOR_NO_PUBLICAR', 'meses': [
        [month, 'f'*64, [[code, a, p] for code, a, p in rows]]
    ]}


class SnapshotTest(unittest.TestCase):
    def test_exclusion_is_diagnostic_only(self):
        old = [legacy('2008-01', '507', 10, 2), legacy('2008-01', '001', 100, 20)]
        data = snapshot('2008-01', [('507', '10.00', '2.00'), ('001', '100.00', '20.00'),
                                       ('999', '100.00', '20.00')])
        result = analyze(data, old)
        self.assertEqual(result['categorias_total_sistema'], {'igual_saldo_507_pre_fusion_redondeado': 1})
        self.assertEqual(result['estado'], 'NO_APROBADO')
        self.assertEqual(result['diferencias_legacy'], [])

    def test_rounding_is_not_approval_or_mask_material_difference(self):
        data = snapshot('2022-01', [('001', '100.01', '20.00'), ('999', '100.00', '20.00')])
        result = analyze(data, [legacy('2022-01', '001', 100.01, 20)])
        self.assertEqual(result['categorias_total_sistema'],
                         {'diferencia_centésimas_mm_por_investigar': 1})
        data['meses'][0][2][1][1] = '98.00'
        result = analyze(data, [legacy('2022-01', '001', 100.01, 20)])
        self.assertEqual(result['categorias_total_sistema'],
                         {'diferencia_material_sin_explicacion': 1})

    def test_unrounded_balances_explain_only_rounding(self):
        data = snapshot('2022-01', [('001', '1.01', '2.00'), ('999', '1.00', '2.00')])
        data['meses'][0][2][0].extend(['1.004999', '2.000000'])
        data['meses'][0][2][1].extend(['1.004999', '2.000000'])
        report = analyze(data, [legacy('2022-01', '001', 1.01, 2)])
        self.assertEqual(report['categorias_total_sistema'], {'conciliado_exacto_en_fuente': 1})

    def test_incomplete_invalid_and_duplicate_fail_closed(self):
        data = snapshot('2022-01', [('001', '100.00', '0.00'), ('999', '100.00', '0.00')])
        old = [legacy('2022-01', '001', 100, 0), legacy('2022-02', '001', 0, 0)]
        with self.assertRaises(ValueError):
            analyze(data, old)
        data['meses'].append(data['meses'][0])
        with self.assertRaises(ValueError):
            analyze(data, old)
        data = snapshot('2022-01', [('001', 'bad', '0.00'), ('999', '100.00', '0.00')])
        with self.assertRaises(ValueError):
            analyze(data, old[:1])


if __name__ == '__main__':
    unittest.main()

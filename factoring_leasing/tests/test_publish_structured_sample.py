"""La muestra publicada debe coincidir exactamente con el cotejo aprobado."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publish_structured_sample as pub


def report():
    base = {'aprobada_muestra': True, 'errores': [], 'acciones_run': pub.RUN,
            'head_sha': '4355226841609feb94e84cd2e30d0977c9decd41',
            'alcance_validacion': 'cuatro cuentas del balance, esta entidad y este período solamente; PDF/XBRL no cotejados',
            'tipo_balance': 'I', 'unidad': 'miles de pesos chilenos (CLP)',
            'fuente_ficha_cmf': 'https://www.cmfchile.cl/institucional/mercados/entidad.php?rut=1',
            'fuente_archivo_cmf': 'https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio=202206'}
    rows = []
    for (segmento, rut, periodo), fixed in pub.FIXED.items():
        rows.append({**base, **dict(zip(pub.COLUMNS, fixed)), 'segmento': segmento, 'rut': rut, 'periodo': periodo})
    return {'aprobada_muestra': True, 'errores': [], 'acciones_run': pub.RUN,
            'head_sha': base['head_sha'], 'registros': rows}


class PublicacionMuestraTests(unittest.TestCase):
    def test_publica_dos_filas_cuadradas(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pub.publish(report(), Path(tmp) / 'muestra.parquet')
            rows = pub.pd.read_parquet(out).to_dict('records')
            self.assertEqual(len(rows), 2)
            for r in rows:
                self.assertEqual(r['total_activos_miles_clp'],
                                 r['total_pasivos_miles_clp'] + r['patrimonio_miles_clp'])
                self.assertEqual(r['run_cotejo_actions'], pub.RUN)

    def test_rechaza_tercera_fila(self):
        value = report()
        value['registros'].append(dict(value['registros'][0]))
        with self.assertRaisesRegex(ValueError, 'exactamente las dos'):
            pub.validate(value)

    def test_rechaza_cifra_alterada(self):
        value = report()
        value['registros'][0]['total_activos_miles_clp'] += 1
        with self.assertRaisesRegex(ValueError, 'no coinciden'):
            pub.validate(value)

    def test_rechaza_run_distinto(self):
        value = report()
        value['acciones_run'] = 1
        with self.assertRaisesRegex(ValueError, 'run aprobado'):
            pub.validate(value)

    def test_rechaza_moneda_distinta(self):
        value = report()
        value['registros'][0]['unidad'] = 'miles de dólares'
        with self.assertRaisesRegex(ValueError, 'moneda'):
            pub.validate(value)

    def test_rechaza_falta_de_advertencia(self):
        value = report()
        del value['registros'][1]['alcance_validacion']
        with self.assertRaisesRegex(ValueError, 'alcance'):
            pub.validate(value)


if __name__ == '__main__':
    unittest.main()

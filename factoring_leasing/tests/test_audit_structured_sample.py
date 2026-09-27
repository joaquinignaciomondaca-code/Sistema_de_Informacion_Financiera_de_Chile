import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('fl_audit', Path(__file__).resolve().parents[1] / 'scripts/audit_structured_sample.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
SAMPLE = a.SAMPLES[0]
FICHA = b'''<html><h1>FACTORING SECURITY S.A.</h1><p>RUT:96655860-1</p>
<p>Tipo de Balance: <b>INDIVIDUAL</b></p><table>
<tr><th>[210000] Estado de situacion financiera<br>Moneda: CLP - Peso chileno (Miles)</th><th>2022-06-30</th></tr>
<tr><td>Efectivo y equivalentes al efectivo</td><td>1.000</td><td>999</td></tr>
<tr><td>Total de activos</td><td>10.000</td><td>9.999</td></tr>
<tr><td>Total de pasivos</td><td>8.000</td><td>8.999</td></tr>
<tr><td>Patrimonio total</td><td>2.000</td><td>1.000</td></tr>
<tr><th>[310000] Estado del resultado</th></tr>
<tr><td>Efectivo y equivalentes al efectivo</td><td>99.999</td></tr></table></html>'''
ARCHIVO = '\n'.join(f'202206;96655860;FACTORING SECURITY S.A.;I;CLP;{label};{amount}000;TAX CI;ESF C/NC'
                    for label, amount in [('Total de activos',10000),('Total de pasivos',8000),('Patrimonio total',2000),('Efectivo y equivalentes al efectivo',1000)]).encode()


class CotejoTests(unittest.TestCase):
    def test_igualdad_cuadre_y_unidad(self):
        r = a.audit_one(SAMPLE, FICHA, ARCHIVO)
        self.assertEqual(r['total_activos_miles_clp'], 10000)
        self.assertEqual(r['unidad'], 'miles de pesos chilenos (CLP)')
        self.assertEqual(r['tipo_balance'], 'I')

    def test_rechaza_otro_rut(self):
        with self.assertRaisesRegex(ValueError, 'Identidad'):
            a.audit_one(SAMPLE, FICHA.replace(b'96655860-1', b'96655861-1'), ARCHIVO)

    def test_rechaza_periodo_distinto(self):
        with self.assertRaisesRegex(ValueError, 'Cierre'):
            a.audit_one(SAMPLE, FICHA.replace(b'2022-06-30', b'2021-06-30'), ARCHIVO)

    def test_rechaza_diferencia(self):
        with self.assertRaisesRegex(ValueError, 'Diferencias'):
            a.audit_one(SAMPLE, FICHA, ARCHIVO.replace(b'10000000', b'10001000'))

    def test_rechaza_cuenta_duplicada(self):
        with self.assertRaisesRegex(ValueError, 'duplicadas'):
            a.stream_amounts(ARCHIVO + b'\n' + ARCHIVO.splitlines()[0], SAMPLE)

    def test_rechaza_falta_moneda(self):
        with self.assertRaisesRegex(ValueError, 'unidad'):
            a.html_amounts(FICHA.replace(b'CLP - Peso chileno (Miles)', b'USD - Dolar (Miles)'), SAMPLE)

    def test_rechaza_balance_de_otro_tipo(self):
        with self.assertRaisesRegex(ValueError, 'individual'):
            a.html_amounts(FICHA.replace(b'INDIVIDUAL', b'CONSOLIDADO'), SAMPLE)

    def test_rechaza_html_en_lugar_de_archivo(self):
        with self.assertRaisesRegex(ValueError, 'HTML'):
            a.stream_amounts(b'<html><body>acceso denegado</body></html>', SAMPLE)

    def test_rechaza_falsa_precision(self):
        with self.assertRaisesRegex(ValueError, 'convertible'):
            a.stream_amounts(ARCHIVO.replace(b'10000000', b'10000001'), SAMPLE)


if __name__ == '__main__':
    unittest.main()

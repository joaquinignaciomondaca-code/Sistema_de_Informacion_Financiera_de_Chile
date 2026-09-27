import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit_sample as a

FFMM = '''<html><table>
<tr><td>Total Activo (+)</td><td></td><td>2.957.448</td><td>4.191.714</td></tr>
<tr><td>Total Pasivo (excluido el activo neto atribuible a partícipes) (+)</td><td></td><td>5.947</td><td>64.811</td></tr>
<tr><td>Activo neto atribuible a los participes (+)</td><td></td><td>2.951.501</td><td>4.126.903</td></tr>
<tr><td>Utilidad/(pérdida) de la operación después de impuesto (+ ó -)</td><td></td><td>3.470</td><td>-1.473.980</td></tr></table></html>'''.encode('latin-1')
FI = '''<table>
<tr><td>Total Activo (+)</td><td>24.887</td><td>28.030</td></tr>
<tr><td>Total Pasivo Corriente (+)</td><td>61</td><td>32</td></tr>
<tr><td>Total Patrimonio Neto (+ ó -)</td><td>24.826</td><td>27.998</td></tr>
<tr><td>Total Pasivo (+)</td><td>24.887</td><td>28.030</td></tr>
<tr><th>ESTADO DE RESULTADOS INTEGRALES (Expresado en miles de Dolar)</th></tr>
<tr><td>Resultado del ejercicio (+ ó -)</td><td>-122</td><td>-647</td></tr>
<tr><th>ESTADO DE CAMBIOS EN EL PATRIMONIO NETO</th></tr>
<tr><td>Resultado del ejercicio (+ ó -)</td><td>0</td><td>-122</td></tr></table>'''.encode('latin-1')


class AuditSampleTests(unittest.TestCase):
    def test_ffmm_html_four_independent_values(self):
        self.assertEqual(a.html_values(FFMM, 'ffmm'), dict(total_activo=2957448,
            total_pasivo_reportado=5947, patrimonio_o_activo_neto=2951501,
            resultado_ejercicio=3470))

    def test_html_utf8_accented_labels(self):
        text = FFMM.decode('latin-1').encode('utf-8')
        self.assertEqual(a.html_values(text, 'ffmm')['resultado_ejercicio'], 3470)

    def test_fi_total_pasivo_includes_equity(self):
        self.assertEqual(a.html_values(FI, 'fi'), dict(total_activo=24887,
            total_pasivo_reportado=24887, patrimonio_o_activo_neto=24826,
            resultado_ejercicio=-122))

    def test_fi_missing_income_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'resultado_ejercicio'):
            a.html_values(FI.replace(b'<td>Resultado del ejercicio (+ \xf3 -)</td>', b'<td>Other</td>'), 'fi')

    def test_roundtrip_parquet_stays_in_quarantine(self):
        rows = [dict(sector='ffmm', rut='8490', periodo='2014-12', total_activo=2957448,
            total_pasivo_reportado=5947, patrimonio_o_activo_neto=2951501,
            resultado_ejercicio=3470, moneda_original='$$', sha256_xml='a'*64)]
        with tempfile.TemporaryDirectory() as tmp:
            p = a.save(rows, Path(tmp))
            self.assertEqual(len(a.pd.read_parquet(p)), 1)
            self.assertNotIn('docs/outputs', str(p))

    def test_difference_not_approved(self):
        with patch.object(a.extract, 'read_url', side_effect=[b'<html/>', b'<IFRS/>']), \
             patch.object(a.extract, 'link_from_html', return_value='https://www.cmfchile.cl/x'), \
             patch.object(a, 'html_values', return_value=dict(total_activo=8)), \
             patch.object(a.extract, 'parse_ifrs', return_value=dict(
                 parseo_reparado=False, dv_xml_coincide=True, total_activo=9)):
            with self.assertRaisesRegex(ValueError, 'distintas'):
                a.sample_once('ffmm', '8490', '2014-12')


if __name__ == '__main__': unittest.main()

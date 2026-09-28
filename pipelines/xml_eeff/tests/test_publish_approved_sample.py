"""Guardarraíles: una muestra aprobada no autoriza publicar el universo completo."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import publish_approved_sample as pub


def report():
    rows = []
    for (sector, rut, periodo), fixed in pub.SAMPLE.items():
        rows.append({**fixed, 'sector': sector, 'rut': rut, 'periodo': periodo,
                     'parseo_reparado': False, 'dv_xml_coincide': True, 'escala': 'miles',
                     'calidad': 'muestra_cotejada_xml_vs_html_cmf',
                     'nombre_registro_actual': 'Nombre actual CMF',
                     'fuente_ficha': 'https://www.cmfchile.cl/ficha',
                     'fuente_xml': 'https://www.cmfchile.cl/xml',
                     'codigo_resultado': 'ResultadoDelEjercicio'})
    return {'aprobada_muestra': True, 'errores': [], 'acciones_run': pub.RUN,
            'head_sha': '0b93e0f6722304b7d76000a029d958708eed8863', 'registros': rows}


class PublicacionPruebas(unittest.TestCase):
    def test_dos_filas_y_cuadre(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = pub.publish(report(), Path(tmp))
            self.assertEqual(len(paths), 2)
            for path in paths:
                row = pub.pd.read_parquet(path).iloc[0]
                self.assertEqual(row['total_activo'], row['pasivo_sin_patrimonio'] + row['patrimonio_o_activo_neto'])
                self.assertIn('solo esta fila', row['alcance_validacion'])

    def test_no_publica_tercera_fila(self):
        value = report()
        value['registros'].append(value['registros'][0].copy())
        with self.assertRaisesRegex(ValueError, 'exactamente las dos'):
            pub.validate(value)

    def test_no_publica_valor_no_cotejado(self):
        value = report()
        value['registros'][0]['total_activo'] += 1
        with self.assertRaisesRegex(ValueError, 'Dato no cotejado'):
            pub.validate(value)

    def test_no_publica_corrida_equivocada(self):
        value = report()
        value['acciones_run'] += 1
        with self.assertRaisesRegex(ValueError, 'run de cotejo'):
            pub.validate(value)

    def test_no_publica_xml_reparado(self):
        value = report()
        value['registros'][0]['parseo_reparado'] = True
        with self.assertRaisesRegex(ValueError, 'reparado'):
            pub.validate(value)


if __name__ == '__main__':
    unittest.main()

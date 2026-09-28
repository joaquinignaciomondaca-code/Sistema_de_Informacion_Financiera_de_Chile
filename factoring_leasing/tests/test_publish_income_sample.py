"""No se confunden los resultados con el balance ni con un trimestre aislado."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publish_income_sample as pub


def report():
    rows = []
    for (segmento, rut, periodo), values in pub.APPROVED.items():
        fixed = pub.BALANCE_APPROVED[(segmento, rut, periodo)]
        row = {'segmento': segmento, 'rut': rut, 'periodo': periodo,
               **dict(zip(('total_activos_miles_clp', 'total_pasivos_miles_clp',
                           'patrimonio_miles_clp', 'efectivo_miles_clp',
                           'nombre_en_archivo_y_ficha', 'tipo_entidad', 'sha256_archivo'), fixed)),
               **dict(zip(pub.RESULT_COLUMNS, values)),
               'tipo_balance': 'I', 'unidad': 'miles de pesos chilenos (CLP)',
               'alcance_validacion': pub.WARNING,
               'fuente_ficha_cmf': 'https://www.cmfchile.cl/institucional/mercados/entidad.php?rut=1',
               'fuente_archivo_cmf': 'https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio=202206',
               'sha256_ficha': 'a'*64}
        rows.append(row)
    return {'aprobada_muestra': True, 'errores': [], 'acciones_run': pub.RUN,
            'head_sha': pub.SHA, 'registros': rows}


class IncomePublicationTests(unittest.TestCase):
    def test_exactamente_dos_resultados_acumulados(self):
        with tempfile.TemporaryDirectory() as tmp:
            df = pub.pd.read_parquet(pub.publish(report(), Path(tmp) / 'resultado.parquet'))
            self.assertEqual(len(df), 2)
            self.assertTrue(all(df['definicion_periodo_resultado'].str.contains('acumulado')))
            self.assertFalse('total_activos_miles_clp' in df.columns)

    def test_rechaza_dato_falso(self):
        r = report(); r['registros'][0][pub.RESULT_COLUMNS[0]] += 1
        with self.assertRaisesRegex(ValueError, 'no corresponde'):
            pub.validate(r)

    def test_rechaza_tercera_entidad(self):
        r = report(); r['registros'].append(r['registros'][0].copy())
        with self.assertRaisesRegex(ValueError, 'exactamente dos'):
            pub.validate(r)

    def test_rechaza_balance_distinto_al_aprobado(self):
        r = report(); r['registros'][0]['total_activos_miles_clp'] += 1
        with self.assertRaisesRegex(ValueError, 'Balance'):
            pub.validate(r)

    def test_rechaza_run_ajeno(self):
        r = report(); r['acciones_run'] = 1
        with self.assertRaisesRegex(ValueError, 'procedencia'):
            pub.validate(r)


if __name__ == '__main__':
    unittest.main()

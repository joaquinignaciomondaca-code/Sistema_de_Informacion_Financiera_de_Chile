import json
import tempfile
import unittest
from pathlib import Path

from bancos.scripts.transfer_repo_review import encode_review, decode_review, PREFIX


class TransferReviewTest(unittest.TestCase):
    def test_complete_roundtrip_and_order_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            months = [f'2022-{m:02d}' for m in range(1, 4)]
            (folder / 'resumen.json').write_text(json.dumps({
                'meses_solicitados': months, 'meses_descargados': 3,
                'errores': [], 'totales': {'diferencias': 0, 'solo_legacy': 0}}))
            for m in months:
                (folder / f'{m}.json').write_text(json.dumps({
                    'periodo': m, 'sha256_zip': 'a'*64,
                    'filas': [{'codigo_institucion': '001', 'repo_activo_mm_clp': '1.00',
                               'repo_pasivo_mm_clp': '2.00', 'nombre_encabezado_b1': 'BANCO'}]}))
            parts = encode_review(folder)
            self.assertTrue(all(len(s) < 3000 for s in parts))
            doc = decode_review(parts[::-1])
            self.assertEqual(len(doc['meses']), 3)
            self.assertEqual(doc['estado'], 'BORRADOR_NO_PUBLICAR')
            with self.assertRaises(ValueError):
                decode_review(parts + parts)
            with self.assertRaises(ValueError):
                decode_review([])
            with self.assertRaises(ValueError):
                decode_review([parts[0].replace(PREFIX, 'BAD', 1)])

    def test_incomplete_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'resumen.json').write_text(json.dumps({
                'meses_solicitados': ['2022-01'], 'meses_descargados': 0,
                'errores': [{'periodo': '2022-01'}],
                'totales': {'diferencias': 0, 'solo_legacy': 0}}))
            with self.assertRaises(ValueError):
                encode_review(folder)


if __name__ == '__main__':
    unittest.main()

import csv
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from extraer_carteras_afp import COLUMNS, ROOT, extract, mapping
from audit_carteras_afp import audit


class CarterasTest(unittest.TestCase):
    def setUp(self):
        (ROOT / '.local-data').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.local-data')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csv = self.root / 'fuente.csv'
        self.out = self.root / 'staging'

    def fixture(self, code='WNMV'):
        row = ['2021-01-29', 'HAB', 'A', code] + [''] * 14
        row[9], row[10], row[17] = '736,9', '-319862208,9', 'FIJANO +00,4550ACT/360'
        with self.csv.open('w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(COLUMNS)
            writer.writerow(row)
        return row

    def test_csv_preserves_literals(self):
        import pyarrow.parquet as pq
        row = self.fixture()
        report = extract([self.csv], self.out)
        self.assertEqual(audit(self.out)['filas'], 1)
        data = pq.read_table(self.out / report['particiones'][0]['path']).to_pylist()[0]
        self.assertEqual([data[c] for c in COLUMNS], row)
        self.assertFalse(report['publicable'])

    def test_zip(self):
        self.fixture()
        z = self.root / 'fuente.zip'
        with zipfile.ZipFile(z, 'w') as f:
            f.write(self.csv, '../cartera.csv')
        extract([z], self.out)
        self.assertEqual(audit(self.out)['filas'], 1)
        self.assertFalse((self.root / 'cartera.csv').exists())

    def test_unknown_quarantine(self):
        self.fixture('NUEVO')
        self.assertEqual(extract([self.csv], self.out)['estado'], 'cuarentena')
        with self.assertRaises(ValueError):
            audit(self.out)

    def test_duplicate_source_rejected(self):
        self.fixture()
        with self.assertRaises(ValueError):
            extract([self.csv, self.csv], self.out)
        with self.assertRaises(ValueError):
            audit(self.out)

    def test_wrong_header(self):
        self.csv.write_text('otra;cabecera\n')
        with self.assertRaises(ValueError):
            extract([self.csv], self.out)

    def test_public_destination_rejected(self):
        with self.assertRaises(ValueError):
            extract([], ROOT / 'docs/outputs/pensiones/prohibido')

    def test_tampered_report(self):
        self.fixture()
        extract([self.csv], self.out)
        p = self.out / 'audit.json'
        report = json.loads(p.read_text())
        report['filas'] += 1
        p.write_text(json.dumps(report))
        with self.assertRaises(ValueError):
            audit(self.out)

    def test_limits_and_existing_output(self):
        self.fixture()
        with self.assertRaises(ValueError):
            extract([self.csv], self.out, max_archivos=0)
        extract([self.csv], self.out)
        with self.assertRaises(ValueError):
            extract([self.csv], self.out)

    def test_nonfinite_timeout(self):
        for minutes in [float('nan'), float('inf'), -1]:
            with self.assertRaises(ValueError):
                extract([], self.out, minutos=minutes)

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            extract([], self.out)
        with self.assertRaises(ValueError):
            audit(self.out)

    def test_truncated_record(self):
        self.fixture()
        with self.csv.open('a') as f:
            f.write('2021;HAB;A\n')
        with self.assertRaises(ValueError):
            extract([self.csv], self.out)
        with self.assertRaises(ValueError):
            audit(self.out)

    def test_partition_tampering(self):
        self.fixture()
        report = extract([self.csv], self.out)
        path = self.out / report['particiones'][0]['path']
        with path.open('ab') as f:
            f.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'Hash'):
            audit(self.out)

    def test_extra_partition(self):
        self.fixture()
        extract([self.csv], self.out)
        (self.out / 'extra.parquet').write_bytes(b'extra')
        with self.assertRaises(ValueError):
            audit(self.out)

    def test_batches_and_all_families(self):
        row = self.fixture()
        with self.csv.open('a', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            for code in mapping():
                row[3] = code
                writer.writerow(row)
            row[3] = 'WNMV'
            for _ in range(10001):
                writer.writerow(row)
        report = extract([self.csv], self.out)
        result = audit(self.out)
        self.assertEqual(result['filas'], 10065)
        self.assertEqual(result['familias'], 14)
        self.assertGreater(len(report['particiones']), 14)

    def test_cp1252_and_quoted_multiline(self):
        row = self.fixture()
        row[5] = 'Emisor ñ;nombre\nsegunda línea'
        with self.csv.open('w', encoding='cp1252', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(COLUMNS)
            writer.writerow(row)
        extract([self.csv], self.out, encoding='cp1252')
        self.assertEqual(audit(self.out)['filas'], 1)

    def test_mapping(self):
        self.assertEqual(len(mapping()), 63)


if __name__ == '__main__':
    unittest.main()

import base64
import hashlib
import json
import lzma
import unittest
from bancos.scripts.hydrate_repo_review import assemble_jobs
from bancos.scripts.transfer_repo_review import PREFIX


def annotations(month):
    payload = {'estado': 'BORRADOR_NO_PUBLICAR', 'meses': [[month, 'a'*64,
               [['001', '1.00', '2.00', '1.0000', '2.0000'],
                ['999', '1.00', '2.00', '1.0000', '2.0000']]]]}
    blob = lzma.compress(json.dumps(payload).encode())
    msg = f'{PREFIX}:{hashlib.sha256(blob).hexdigest()}:1/1:{base64.b64encode(blob).decode()}'
    return [{'title': PREFIX + '-01', 'message': msg}]


class HydrateTest(unittest.TestCase):
    def setUp(self):
        self.jobs = [{'name': f'transfer_review ({i})', 'id': i,
                      'conclusion': 'success'} for i in range(3)]
        self.records = {i: annotations(f'2022-0{i+1}') for i in range(3)}
        self.months = {f'2022-0{i+1}' for i in range(3)}

    def test_all_three_shards_required_and_ordered(self):
        doc = assemble_jobs(self.jobs[::-1], self.records, self.months)
        self.assertEqual([m[0] for m in doc['meses']], sorted(self.months))
        self.assertEqual(doc['estado'], 'BORRADOR_NO_PUBLICAR')
        with self.assertRaises(ValueError):
            assemble_jobs(self.jobs[:2], self.records, self.months)
        with self.assertRaises(ValueError):
            assemble_jobs(self.jobs, {**self.records, 2: []}, self.months)
        with self.assertRaises(ValueError):
            assemble_jobs(self.jobs, self.records, self.months | {'2022-04'})
        with self.assertRaises(ValueError):
            assemble_jobs(self.jobs, {**self.records, 2: self.records[0]}, self.months)


if __name__ == '__main__':
    unittest.main()

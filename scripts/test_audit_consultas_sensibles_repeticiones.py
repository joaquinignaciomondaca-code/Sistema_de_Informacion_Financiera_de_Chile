#!/usr/bin/env python3
"""Pruebas unitarias de comparación para el auditor de sensibilidad SQL."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.audit_consultas_sensibles_repeticiones import _diferencia, _hash, _normalizar_valor, _referencias


class AuditorConsultasSensiblesTest(unittest.TestCase):
    def test_diferencia_vacia_si_las_salidas_coinciden(self):
        self.assertEqual(_diferencia(("(1, 'a')", "(2, 'b')"), ("(2, 'b')", "(1, 'a')")), (0, 0))

    def test_diferencia_cuenta_filas_retiradas_y_agregadas(self):
        base = ("('x', 10)", "('y', 20)", "('z', 30)")
        distinct = ("('x', 8)", "('y', 20)")
        self.assertEqual(_diferencia(base, distinct), (2, 1))

    def test_diferencia_respeta_multiconjuntos(self):
        self.assertEqual(_diferencia(("fila", "fila", "otra"), ("fila", "otra")), (1, 0))

    def test_referencias_detecta_from_join_y_comillas(self):
        sql = '''WITH base AS (SELECT * FROM "tabla_a")
                 SELECT * FROM base JOIN tabla_b USING (id)
                 JOIN no_es_vista n ON true'''
        self.assertEqual(_referencias(sql, {"tabla_a", "tabla_b"}), ["tabla_a", "tabla_b"])

    def test_floats_ignoran_solo_ruido_menor_de_redondeo(self):
        self.assertEqual(_normalizar_valor(0.551351351351351), _normalizar_valor(0.5513513513513513))
        self.assertNotEqual(_normalizar_valor(10.0), _normalizar_valor(10.1))

    def test_hash_incluye_esquema_y_contenido(self):
        h = _hash(("id", "total"), (("(1, 2)",)))
        self.assertEqual(len(h), 64)
        self.assertNotEqual(h, _hash(("id", "total"), (("(1, 3)",))))
        self.assertNotEqual(h, _hash(("id", "importe"), (("(1, 2)",))))


if __name__ == "__main__":
    unittest.main()

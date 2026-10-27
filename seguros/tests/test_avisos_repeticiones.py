"""El aviso describe lo medido y no atribuye origen ni validez semántica."""
import unittest

from seguros.scripts.actualizar_carteras import avisos_repeticiones_exactas


class AvisosRepeticionesTest(unittest.TestCase):
    def test_no_avisa_si_no_hay_filas_exactas_repetidas(self):
        filas = {"demo": [{"id": 1, "valor": 10}, {"id": 1, "valor": 11}]}
        self.assertEqual(avisos_repeticiones_exactas(filas, ["demo"]), [])

    def test_avisa_solo_apariciones_extra_y_no_afirma_origen(self):
        row = {"id": 1, "valor": 10}
        filas = {"demo": [row, row.copy(), row.copy(), {"id": 2, "valor": 10}]}
        avisos = avisos_repeticiones_exactas(filas, ["demo"])
        self.assertEqual(len(avisos), 1)
        self.assertIn("2 apariciones extra", avisos[0])
        self.assertIn("tras la lectura", avisos[0])
        self.assertIn("origen y validez semántica no determinados", avisos[0])
        self.assertNotIn("duplicados de la fuente", avisos[0])

    def test_tabla_sin_filas_no_falla(self):
        self.assertEqual(avisos_repeticiones_exactas({"demo": []}, ["demo"]), [])


if __name__ == "__main__":
    unittest.main()

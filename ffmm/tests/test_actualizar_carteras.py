import unittest

from ffmm.scripts import actualizar_carteras as ac


def _csv_cartera(codigo):
    _, especificacion = ac.CARTERAS[codigo]
    encabezado = [codigo_cmf for _, codigo_cmf, _ in especificacion]
    fila = []
    for columna, _, tipo in especificacion:
        if columna == "run_fondo":
            fila.append("10001")
        elif columna == "nombre_fondo":
            fila.append("Fondo de prueba")
        elif columna == "rut_emisor":
            fila.append("76000000")
        elif columna == "dv_emisor":
            fila.append("1")
        elif tipo == "n":
            fila.append("1")
        elif tipo == "f":
            fila.append("31/12/2030")
        else:
            fila.append("TEST")
    return (";".join(encabezado) + "\n" + ";".join(fila) + "\n" + ";".join(fila) + "\n").encode()


class TestParserCarteras(unittest.TestCase):
    def test_conserva_lineas_identicas_en_los_cuatro_tipos_de_cartera(self):
        for codigo in ac.CARTERAS:
            with self.subTest(cartera=codigo):
                tabla, _ = ac.CARTERAS[codigo]
                filas, avisos = ac.leer(codigo, _csv_cartera(codigo), "2025-12")

                self.assertEqual(avisos, [])
                self.assertEqual(len(filas), 2)
                self.assertEqual(filas.iloc[0].to_dict(), filas.iloc[1].to_dict())
                self.assertEqual(filas.iloc[0]["periodo"], "2025-12")
                self.assertIn("run_fondo", filas.columns)
                self.assertEqual(tabla, ac.CARTERAS[codigo][0])


if __name__ == "__main__":
    unittest.main()

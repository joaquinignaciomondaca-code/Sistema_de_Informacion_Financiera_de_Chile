import unittest

from fi.scripts.actualizar_carteras import CARTERAS, leer_cartera


def _pagina_cartera(codigo):
    spec = CARTERAS[codigo][2]
    encabezados = [encabezado for encabezado, _, _ in spec]
    detalle = []
    for _, columna, tipo in spec:
        if columna == "nemotecnico":
            detalle.append("BONO-TEST")
        elif tipo == "r":
            detalle.append("76000000")
        elif tipo == "f":
            detalle.append("31/12/2030")
        elif tipo == "n":
            detalle.append("1")
        else:
            detalle.append("CL")
    filas = [detalle, detalle, ["TOTAL"] + [""] * (len(spec) - 1)]
    tabla = ["<table><tr>"]
    tabla.extend(f"<th>{valor}</th>" for valor in encabezados)
    tabla.append("</tr>")
    for fila in filas:
        tabla.append("<tr>")
        tabla.extend(f"<td>{valor}</td>" for valor in fila)
        tabla.append("</tr>")
    tabla.append("</table>")
    return "".join(tabla).encode("utf-8")


class TestUnidadCarteraNacional(unittest.TestCase):
    def test_parser_conserva_detalles_identicos_y_excluye_total_en_todas_las_carteras(self):
        for codigo in CARTERAS:
            with self.subTest(cartera=codigo):
                spec = CARTERAS[codigo][2]
                filas, ilegibles, descuadres = leer_cartera(codigo, _pagina_cartera(codigo))

                self.assertEqual(ilegibles, [])
                self.assertEqual(descuadres, [])
                self.assertEqual(len(filas), 2)
                self.assertEqual(filas[0], filas[1])
                primera_columna = spec[0][1]
                self.assertNotIn("TOTAL", [fila[primera_columna] for fila in filas])


if __name__ == "__main__":
    unittest.main()

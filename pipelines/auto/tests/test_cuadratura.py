import unittest

from pipelines.auto import cuadratura as c


def ifrs(rut, a, p, e, rep=1, **extra):
    base = {"rut": rut, "tipo_balance": "individual", "moneda": "CLP", "estado_financiero": "ESF", "repeticion": rep}
    return [dict(base, cuenta="Total de activos", valor=a), dict(base, cuenta="Total de pasivos", valor=p),
            dict(base, cuenta="Patrimonio total", valor=e), dict(base, cuenta="Otra cuenta", valor=5)]


class CuadraturaTest(unittest.TestCase):
    def test_balance_que_cuadra(self):
        v, malos = c.verificar_ifrs(ifrs("1", 100_000, 40_000, 60_000))
        self.assertEqual((v, malos), (1, []))

    def test_redondeo_de_mil_pesos_se_acepta(self):
        v, malos = c.verificar_ifrs(ifrs("1", 100_000, 40_000, 59_000))
        self.assertEqual((v, malos), (1, []))

    def test_descuadre_real_se_informa(self):
        v, malos = c.verificar_ifrs(ifrs("1", 100_000_000, 40_000_000, 50_000_000))
        self.assertEqual(v, 1)
        self.assertEqual(len(malos), 1)
        self.assertIn("Δ 10000000", malos[0])

    def test_variantes_de_glosa_y_balances_independientes(self):
        filas = ifrs("1", 10, 4, 6) + ifrs("2", 10, 4, 6, rep=2)
        for f in filas:
            f["cuenta"] = f["cuenta"].replace("Total de activos", "TOTAL  ACTIVOS")
        v, malos = c.verificar_ifrs(filas)
        self.assertEqual((v, malos), (2, []))

    def test_sin_los_tres_totales_no_se_verifica(self):
        filas = [f for f in ifrs("1", 10, 4, 6) if f["cuenta"] != "Patrimonio total"]
        self.assertEqual(c.verificar_ifrs(filas), (0, []))

    def test_valor_no_numerico_se_ignora(self):
        filas = ifrs("1", None, 4, 6)
        self.assertEqual(c.verificar_ifrs(filas), (0, []))

    def test_fecu(self):
        def fila(cod, v):
            return {"rut": "9", "tipo_intermediario": "corredor", "codigo_fecu": cod, "valor_miles_clp": v}
        ok = [fila("10.00.00", 100), fila("21.00.00", 30), fila("22.00.00", 70), fila("20.00.00", 100)]
        self.assertEqual(c.verificar_fecu(ok), (1, []))
        mal = [fila("10.00.00", 100), fila("21.00.00", 30), fila("22.00.00", 60)]
        self.assertEqual(c.verificar_fecu(mal)[0], 1)
        self.assertEqual(len(c.verificar_fecu(mal)[1]), 1)

    def test_compuerta(self):
        self.assertFalse(c.debe_detener(4700, ["x"]))            # 1 aislado: aviso
        self.assertFalse(c.debe_detener(55, ["x"] * 2))          # 2 sociedades con XBRL malo: aviso
        self.assertTrue(c.debe_detener(55, ["x"] * 10))          # lectura rota: detiene
        self.assertFalse(c.debe_detener(100, ["x"] * 3))         # 3 %: por debajo del umbral
        self.assertFalse(c.debe_detener(10, ["x"] * 5))          # muy pocos para juzgar


if __name__ == "__main__":
    unittest.main()

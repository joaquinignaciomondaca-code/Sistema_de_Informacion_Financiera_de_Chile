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


class GlosasTest(unittest.TestCase):
    """Los totales se reconocen por glosa, y la glosa cambia entre taxonomías."""

    def variantes(self, activos, pasivos, patrimonio):
        return [{"rut": "1", "tipo_balance": "individual", "moneda": "CLP",
                 "estado_financiero": "ESF C/NC", "repeticion": 1, "cuenta": activos, "valor": 100},
                {"rut": "1", "tipo_balance": "individual", "moneda": "CLP",
                 "estado_financiero": "ESF C/NC", "repeticion": 1, "cuenta": pasivos, "valor": 40},
                {"rut": "1", "tipo_balance": "individual", "moneda": "CLP",
                 "estado_financiero": "ESF C/NC", "repeticion": 1, "cuenta": patrimonio, "valor": 60}]

    def test_nomenclatura_antigua_con_comas(self):
        # Una securitizadora de 2009 informa así: sin esto, su balance queda sin verificar.
        self.assertEqual(c.verificar_ifrs(self.variantes("Activos, Total", "Pasivos, Total", "Patrimonio total")), (1, []))

    def test_acentos_y_mayusculas_no_importan(self):
        self.assertEqual(c.verificar_ifrs(self.variantes("TOTAL DE ACTIVOS", "Total de Pasivos", "PATRIMONIO TOTAL")), (1, []))

    def test_subtotales_no_se_confunden_con_el_total(self):
        # «Pasivos, Corrientes, Total» es el pasivo corriente, no el total de pasivos.
        self.assertEqual(c.verificar_ifrs(self.variantes("Total de activos", "Pasivos, Corrientes, Total", "Patrimonio total")), (0, []))


class ResultadosTest(unittest.TestCase):
    def er(self, cuenta, valor, estado="ERFG", rep=1, rut="1"):
        return {"rut": rut, "tipo_balance": "individual", "moneda": "CLP",
                "estado_financiero": estado, "repeticion": rep, "cuenta": cuenta, "valor": valor}

    def test_eri_arrastra_la_ganancia_y_la_bruta_cuadra(self):
        filas = [self.er("Ingresos de actividades ordinarias", 500), self.er("Costo de ventas", 300),
                 self.er("Ganancia bruta", 200), self.er("Ganancia (pérdida)", 100),
                 self.er("Ganancia (pérdida)", 100, estado="ERI"),
                 self.er("Resultado integral total", 100, estado="ERI")]
        verificaciones, malos = c.verificar_resultados_ifrs(filas)
        self.assertEqual((verificaciones, malos), (2, []))

    def test_eri_divergente_se_informa(self):
        filas = [self.er("Ganancia (pérdida)", 100), self.er("Ganancia (pérdida)", 999, estado="ERI")]
        _v, malos = c.verificar_resultados_ifrs(filas)
        self.assertEqual(len(malos), 1)
        self.assertIn("ERI", malos[0])

    def test_ganancia_bruta_mal_calculada_se_informa(self):
        filas = [self.er("Ingresos de actividades ordinarias", 500), self.er("Costo de ventas", 300),
                 self.er("Ganancia bruta", 250)]
        _v, malos = c.verificar_resultados_ifrs(filas)
        self.assertEqual(len(malos), 1)
        self.assertIn("ganancia bruta", malos[0])

    def test_sin_eri_no_se_verifica_y_fluir_de_efectivo_se_ignora(self):
        filas = [self.er("Ganancia (pérdida)", 100), self.er("Efectivo al inicio", 5, estado="EFMI")]
        self.assertEqual(c.verificar_resultados_ifrs(filas), (0, []))


class CoberturaTest(unittest.TestCase):
    """Si la compuerta no puede verificar, no es que esté todo bien: está ciega."""

    def test_cobertura_sana_no_detiene(self):
        self.assertFalse(c.debe_detener(100, [], balances_totales=105))
        self.assertEqual(c.motivo_detener(100, [], balances_totales=105), "")

    def test_cobertura_en_caida_libre_detiene(self):
        self.assertTrue(c.debe_detener(2, [], balances_totales=100))
        self.assertIn("no puede verificar", c.motivo_detener(2, [], balances_totales=100))

    def test_pocos_balances_no_arman_una_tasa(self):
        # Con menos de MIN_PARA_COMPUERTA no se juzga ni la cobertura ni el descuadre.
        self.assertFalse(c.debe_detener(1, [], balances_totales=10))

    def test_motivo_del_descuadre_lo_encabeza_el_primer_caso(self):
        # 6 de 100 = 6 %, por encima del umbral del 5 %: la compuerta se cierra.
        malos = [f"rut{i}: descuadra" for i in range(6)]
        motivo = c.motivo_detener(100, malos)
        self.assertIn("6 de 100 balances no cuadran", motivo)
        self.assertIn(malos[0], motivo)

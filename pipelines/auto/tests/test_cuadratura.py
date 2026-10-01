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


# ---------------------------------------------------------------------------
# Fondos mutuos (XML IFRS de la CMF): activo − pasivo = activo neto y las identidades del estado de resultados
# ---------------------------------------------------------------------------
def ffmm(run, **cuentas):
    """Filas publicadas de un fondo y cierre (solo las cuentas pedidas)."""
    return [{"periodo": "2025-12", "run_fondo": run, "codigo_cuenta": k, "valor_miles_mf": v} for k, v in cuentas.items()]


_NO_CEROS = {
    "EfectivoYEfectivoEquivalente": 116573, "ActivosFinancierosACostoAmortizado": 192755620, "OtrosActivos": 7,
    "TotalActivo": 192872200, "RemuneracionesSociedadAdministradora": 12234, "OtrosDocumentosYCuentasPorPagar": 14691,
    "TotalPasivo": 26925, "ActivoNetoAtribuibleALosParticipes": 192845275,
    "InteresesYReajustes": 11317039,
    "CambiosNetosEnValorRazonableDeActivosYPasivosFinancierosAValorRazonableConEfectoEnResultados": -3823,
    "ResultadoEnVentaDeInstrumentosFinancieros": -20255, "OtrosEri": 73,
    "TotalIngresosPerdidasNetosDeLaOperacion": 11293034, "ComisionDeAdministracion": -2552317,
    "OtrosGastosDeOperacion": -50997, "TotalGastosDeOperacion": -2603314,
    "UtilidadPerdidaDeLaOperacionAntesDeImpuesto": 8689720, "ImpuestosALasGananciasPorInversionesEnElExterior": 0,
    "UtilidadPerdidaDeLaOperacionDespuesDeImpuesto": 8689720,
    c._FFMM_AUMENTO_ANTES: 8689720, "DistribucionDeBeneficios": 0, c._FFMM_AUMENTO_DESPUES: 8689720,
}
# Los archivos reales traen siempre las 35 cuentas (las que valen cero, con 0): sin ellas las sumas no se evalúan.
COMPLETO = {**{k: 0 for k in c.FFMM_ACTIVOS + c.FFMM_PASIVOS + c.FFMM_INGRESOS + c.FFMM_GASTOS}, **_NO_CEROS}


class FondosMutuosTest(unittest.TestCase):
    def test_balance_real_cuadra(self):
        self.assertEqual(c.verificar_ffmm(ffmm("8011", **COMPLETO)), (1, []))

    def test_el_activo_neto_no_es_patrimonio_del_pasivo(self):
        # un fondo mutuo no suma el activo neto al pasivo: activo − pasivo = activo neto
        v, malos = c.verificar_ffmm(ffmm("1", TotalActivo=1_000_000, TotalPasivo=10_000, ActivoNetoAtribuibleALosParticipes=500_000))
        self.assertEqual(v, 1)
        self.assertIn("Δ 490000", malos[0])

    def test_tolerancia_de_redondeo_y_fondos_independientes(self):
        filas = (ffmm("1", TotalActivo=100, TotalPasivo=40, ActivoNetoAtribuibleALosParticipes=62)
                 + ffmm("2", TotalActivo=100, TotalPasivo=40, ActivoNetoAtribuibleALosParticipes=70))
        v, malos = c.verificar_ffmm(filas)
        self.assertEqual(v, 2)
        self.assertEqual(len(malos), 1)
        self.assertTrue(malos[0].startswith("2025-12/2:"))

    def test_sin_los_tres_totales_no_se_verifica(self):
        self.assertEqual(c.verificar_ffmm(ffmm("1", TotalActivo=10, TotalPasivo=4)), (0, []))

    def test_las_nueve_identidades_cuadran_con_los_importes_reales(self):
        self.assertEqual(c.identidades_ffmm(COMPLETO), [])

    def test_cada_identidad_detecta_su_descuadre(self):
        casos = {
            "Σ activos = total activo": {"OtrosActivos": 500},
            "Σ pasivos = total pasivo": {"OtrosDocumentosYCuentasPorPagar": 0},
            "activo − pasivo = activo neto": {"ActivoNetoAtribuibleALosParticipes": 1},
            "Σ ingresos = total ingresos": {"OtrosEri": 0},
            "Σ gastos = total gastos": {"OtrosGastosDeOperacion": 0},
            "ingresos + gastos = utilidad antes de impuesto": {"UtilidadPerdidaDeLaOperacionAntesDeImpuesto": 1},
            "utilidad antes + impuestos = utilidad después": {"UtilidadPerdidaDeLaOperacionDespuesDeImpuesto": 1},
            "utilidad después = aumento del activo neto antes de distribución": {c._FFMM_AUMENTO_ANTES: 1},
            "aumento antes + distribución = aumento después": {c._FFMM_AUMENTO_DESPUES: 1},
        }
        for regla, cambio in casos.items():
            with self.subTest(regla):
                malas = [r for r, _d in c.identidades_ffmm({**COMPLETO, **cambio})]
                self.assertIn(regla, malas)

    def test_una_regla_sin_todos_sus_datos_no_se_evalua(self):
        parcial = {k: v for k, v in COMPLETO.items() if k != "TotalPasivo"}
        self.assertEqual(c.identidades_ffmm(parcial), [])
        self.assertEqual(c.identidades_ffmm({}), [])

    def test_se_puede_pedir_solo_balance_o_solo_resultados(self):
        roto = {**COMPLETO, "TotalActivo": 1, "TotalGastosDeOperacion": 1}
        solo_balance = {r for r, _ in c.identidades_ffmm(roto, resultados=False)}
        solo_resultados = {r for r, _ in c.identidades_ffmm(roto, balance=False)}
        self.assertTrue(all("activo" in r or "pasivo" in r for r in solo_balance))
        self.assertFalse(solo_balance & solo_resultados)

    def test_resultados_publicados(self):
        v, malos = c.verificar_resultados_ffmm(ffmm("8011", **COMPLETO))
        self.assertEqual((v, malos), (6, []))
        v, malos = c.verificar_resultados_ffmm(ffmm("8011", **{**COMPLETO, "OtrosEri": 0}))
        self.assertEqual(v, 6)
        self.assertEqual(len(malos), 1)
        self.assertIn("Σ ingresos = total ingresos", malos[0])
        self.assertTrue(malos[0].startswith("2025-12/8011:"))

    def test_la_compuerta_en_bloque_de_fondos_mutuos(self):
        filas = []
        for i in range(30):
            filas += ffmm(str(i), TotalActivo=1_000_000, TotalPasivo=1_000,
                          ActivoNetoAtribuibleALosParticipes=999_000 if i >= 6 else 1)
        v, malos = c.verificar_ffmm(filas)
        self.assertEqual((v, len(malos)), (30, 6))
        self.assertTrue(c.debe_detener(v, malos, c.contar_grupos(filas, c.CLAVES_FFMM)))
        self.assertIn("6 de 30 balances no cuadran", c.motivo_detener(v, malos))

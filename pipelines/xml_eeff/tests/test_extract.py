import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('extract', Path(__file__).resolve().parents[1] / 'extract.py')
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)
ITEM = {'sector': 'ffmm', 'rut': '8490', 'tipo': 'RGFMU', 'nombre_registro': 'Fondo', 'tab': '3', 'marker': 'FMEF'}


def xml(rut='8490', periodo='2014', activo='2957448', pasivo='5947', neto='2951501'):
    return f'''<IFRS><Identificacion><RUTFondoInforma>{rut}</RUTFondoInforma><DVFondoInforma>5</DVFondoInforma></Identificacion>
<DatosPeriodo><MonedaPresentacionEstadosFinancieros>$$</MonedaPresentacionEstadosFinancieros><PeriodoPresentacionEstadosFinancieros>
<Mes>12</Mes><Anio>{periodo}</Anio></PeriodoPresentacionEstadosFinancieros></DatosPeriodo>
<Cuenta CodigoCuenta="TotalActivo" Context="PeriodoActual">{activo}</Cuenta>
<Cuenta CodigoCuenta="TotalPasivo" Context="PeriodoActual">{pasivo}</Cuenta>
<Cuenta CodigoCuenta="ActivoNetoAtribuibleALosParticipes" Context="PeriodoActual">{neto}</Cuenta>
<Cuenta CodigoCuenta="UtilidadPerdidaDeLaOperacionDespuesDeImpuesto" Context="PeriodoActual">3470</Cuenta>
</IFRS>'''.encode()


class XmlTest(unittest.TestCase):
    def test_valid(self):
        row = x.parse_ifrs(xml(), ITEM, '2014-12', 'https://www.cmfchile.cl/test')
        self.assertEqual(row['total_activo'], 2957448)
        self.assertEqual(row['resultado_ejercicio'], 3470)
        self.assertEqual(row['escala'], 'miles')

    def test_wrong_rut(self):
        with self.assertRaisesRegex(ValueError, 'RUT'): x.parse_ifrs(xml(rut='8001'), ITEM, '2014-12', 'url')

    def test_wrong_date(self):
        with self.assertRaisesRegex(ValueError, 'Periodo'): x.parse_ifrs(xml(periodo='2021'), ITEM, '2014-12', 'url')

    def test_unbalanced(self):
        with self.assertRaisesRegex(ValueError, 'no cuadra'): x.parse_ifrs(xml(activo='9'), ITEM, '2014-12', 'url')

    def test_no_income_not_zero(self):
        raw = xml().replace(b'<Cuenta CodigoCuenta="UtilidadPerdidaDeLaOperacionDespuesDeImpuesto" Context="PeriodoActual">3470</Cuenta>', b'')
        with self.assertRaisesRegex(ValueError, 'resultado'): x.parse_ifrs(raw, ITEM, '2014-12', 'url')

    def test_urls(self):
        page = b'<a href="../inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php?archivo=FMEF_8490.xml&amp;rut=8490">Descarga</a>'
        self.assertIn('archivo=FMEF_8490.xml&rut=8490', x.link_from_html(page, ITEM))
        self.assertIn('pestania=29', x.ficha_url({**ITEM, 'sector':'fi', 'tab':'29', 'tipo':'FIRES'}, '2021-12'))

    def test_xbrl_no_guess(self):
        raw = b'<xbrl xmlns="http://www.xbrl.org/2003/instance"><context id="c"/><unit id="u"/></xbrl>'
        row = x.parse_xbrl(raw, {**ITEM,'sector':'agf'}, '2021-12', 'url')
        self.assertIsNone(row['resultado_ejercicio'])
        self.assertEqual(row['calidad'], 'xbrl_pendiente_mapeo_taxonomia')


class FechasTest(unittest.TestCase):
    def _periodos(self, mes):
        original = x.date
        class Falso(x.date):
            @classmethod
            def today(cls): return cls(2026, mes, 15)
        x.date = Falso
        try:
            return x.periodos_ultimo(1)[:2]
        finally:
            x.date = original

    def test_cierres_cumplidos_todos_los_meses(self):
        esperado = {1: ['2025-12', '2025-09'], 2: ['2025-12', '2025-09'], 3: ['2025-12', '2025-09'],
                    4: ['2026-03', '2025-12'], 5: ['2026-03', '2025-12'], 6: ['2026-03', '2025-12'],
                    7: ['2026-06', '2026-03'], 8: ['2026-06', '2026-03'], 9: ['2026-06', '2026-03'],
                    10: ['2026-09', '2026-06'], 11: ['2026-09', '2026-06'], 12: ['2026-09', '2026-06']}
        for mes, exp in esperado.items():
            self.assertEqual(self._periodos(mes), exp, f'mes {mes}')

    def test_nunca_devuelve_trimestre_futuro(self):
        for mes in range(1, 13):
            for periodo in self._periodos(mes):
                self.assertLessEqual(periodo, '2026-09', f'mes {mes} devolvio {periodo}')


class PeriodicidadTest(unittest.TestCase):
    def test_anuales_solo_diciembre(self):
        for sector in ('ffmm', 'agf', 'retail'):
            for periodo in x.periodos_para(sector, todos=True):
                self.assertTrue(periodo.endswith('-12'), f'{sector} devolvio {periodo}')

    def test_historicos_desde_2011_y_sin_futuro(self):
        historico = x.periodos_para('corredoras', todos=True)
        self.assertEqual(historico[0], '2011-03')
        self.assertTrue(all(p <= '2026-06' for p in historico))
        self.assertGreater(len(historico), 50)

    def test_diario_acotado(self):
        self.assertLessEqual(len(x.periodos_para('ffmm')), 2)
        self.assertLessEqual(len(x.periodos_para('fi')), 2)


class ZipTest(unittest.TestCase):
    def test_xbrl_dentro_de_zip(self):
        import io, zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            zf.writestr('leeme.txt', 'no es instancia')
            zf.writestr('instancia.xbrl', '<xbrl xmlns="http://www.xbrl.org/2003/instance"><context id="c"/><unit id="u"/></xbrl>')
        raw, nombre = x.desempaquetar_xbrl(buffer.getvalue())
        self.assertEqual(nombre, 'instancia.xbrl')
        self.assertTrue(raw.startswith(b'<xbrl'))

    def test_zip_sin_instancia_falla(self):
        import io, zipfile
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zf:
            zf.writestr('leeme.txt', 'x')
        with self.assertRaisesRegex(ValueError, 'ZIP sin instancia'):
            x.desempaquetar_xbrl(buffer.getvalue())

    def test_payload_plano_pasa_igual(self):
        raw, nombre = x.desempaquetar_xbrl(b'<xbrl/>')
        self.assertEqual((raw, nombre), (b'<xbrl/>', None))


class DuplicadosYDvTest(unittest.TestCase):
    def test_serie_repetida_no_rompe(self):
        raw = xml().replace(b'</IFRS>', b'<Cuenta CodigoCuenta="ActivoNetoAtribuibleALosParticipesAl01DeEneroPorSerie" Context="PeriodoActual">10</Cuenta>'
                                        b'<Cuenta CodigoCuenta="ActivoNetoAtribuibleALosParticipesAl01DeEneroPorSerie" Context="PeriodoActual">20</Cuenta></IFRS>')
        fila = x.parse_ifrs(raw, ITEM, '2014-12', 'url')
        self.assertEqual(fila['codigos_repetidos_por_serie'], 1)

    def test_total_repetido_con_valores_distintos_falla(self):
        raw = xml().replace(b'</IFRS>', b'<Cuenta CodigoCuenta="TotalActivo" Context="PeriodoActual">1</Cuenta></IFRS>')
        with self.assertRaisesRegex(ValueError, 'Total exigido'): x.parse_ifrs(raw, ITEM, '2014-12', 'url')

    def test_dv_distinto_queda_como_marca(self):
        raw = xml().replace(b'<DVFondoInforma>5</DVFondoInforma>', b'<DVFondoInforma>9</DVFondoInforma>')
        fila = x.parse_ifrs(raw, ITEM, '2014-12', 'url')
        self.assertFalse(fila['dv_xml_coincide'])

    def test_html_en_lugar_de_xml_se_diagnostica(self):
        with patch.object(x, 'read_url', lambda url, limit=0, referer=None:
                          b'<html><body>error</body></html>' if 'ifrs_xml' in url else
                          b'<a href="https://c/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php?archivo=FMEF1_8490.xml">x</a>'):
            with self.assertRaisesRegex(ValueError, 'contenido=html'):
                x.process(ITEM, '2014-12')


class ParseoToleranteTest(unittest.TestCase):
    def test_xml_con_caracter_invalido_se_repara_y_marca(self):
        crudo = xml().replace(b'2957448', b'2&957448')  # & sin escapar: XML inválido real
        fila = x.parse_ifrs(crudo, ITEM, '2014-12', 'url')
        self.assertTrue(fila['parseo_reparado'])
        self.assertEqual(fila['calidad'], 'revisar_parseo_reparado')
        self.assertEqual(fila['total_activo'], 2957448.0)  # cifra recuperada y marcada

    def test_xml_valido_no_se_marca(self):
        self.assertFalse(x.parse_ifrs(xml(), ITEM, '2014-12', 'url')['parseo_reparado'])

    def test_no_se_inventa_numero_si_no_se_puede_leer(self):
        crudo = xml().replace(b'2957448', b'2&abc')
        with self.assertRaisesRegex(ValueError, 'Total exigido con valores distintos|Cuenta no numerica|no cuadra'):
            x.parse_ifrs(crudo, ITEM, '2014-12', 'url')

    def test_saneo_escapa_ampersand_y_saca_controles(self):
        self.assertEqual(x.sanear_xml(b'<a>2&3</a>'), b'<a>2&amp;3</a>')
        self.assertNotIn(b'\x0b', x.sanear_xml(b'<a>1\x0b2</a>'))
        self.assertEqual(x.sanear_xml(b'<a>&amp;</a>'), b'<a>&amp;</a>')


class FlujoTest(unittest.TestCase):
    def test_sin_enlace_es_sin_fuente(self):
        with patch.object(x, 'read_url', lambda url, limit=0, referer=None: b'<html>sin enlaces</html>'):
            self.assertEqual(x.process(ITEM, '2014-12')[0], 'sin_fuente')

    def test_xbrl_no_inventa_cifras(self):
        raw = b'<html><a href="https://x/safec_ifrs_verarchivo.php?auth=1">Estados financieros (XBRL)</a></html>'
        instancia = b'<xbrl xmlns="http://www.xbrl.org/2003/instance"><context id="c"/><unit id="u"/></xbrl>'
        # La ficha se sirve como HTML; el enlace XBRL (safec_ifrs) devuelve la instancia.
        with patch.object(x, 'read_url', lambda url, limit=0, referer=None: instancia if 'safec_ifrs' in url else raw):
            estado, fila = x.process({**ITEM, 'sector': 'agf', 'tipo': 'RGAGF', 'marker': 'XBRL'}, '2014-12')
        self.assertEqual(estado, 'pendiente_taxonomia')
        self.assertIsNone(fila['total_activo'])


if __name__ == '__main__': unittest.main()

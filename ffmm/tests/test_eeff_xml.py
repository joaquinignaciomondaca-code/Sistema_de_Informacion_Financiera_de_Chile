"""Pruebas de `ffmm/scripts/eeff_xml.py`: lectura del XML IFRS de fondos mutuos y de la ficha que lo enlaza.

Cada caso reproduce una rareza **medida** en 278 fondo-años reales de la CMF (docs/notas/
ffmm_estados_financieros_xml_2026-10-01.md): declaraciones de codificación falsas, ausentes o inventadas,
códigos con espacio final, páginas de desafío en lugar de la ficha. Los importes son los reales del fondo 8011-K.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from ffmm.tests import xml_sintetico as X  # noqa: E402
from pipelines.auto import cuadratura  # noqa: E402

SPEC = importlib.util.spec_from_file_location("eeff_xml", RAIZ / "ffmm/scripts/eeff_xml.py")
E = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E)


def extraer(raw=None, run="8011", anio=2025, **kw):
    return E.extraer(E.leer_xml(raw if raw is not None else X.xml(run, anio, **kw)), run, anio)


class TestCatalogo(unittest.TestCase):
    def test_forma_del_catalogo(self):
        bal, res = E.CATALOGO["balance"], E.CATALOGO["resultados"]
        self.assertEqual((len(bal), len(res)), (16, 19))
        for lineas in (bal, res):
            self.assertEqual([l[0] for l in lineas], list(range(1, len(lineas) + 1)), "el orden es consecutivo")
            self.assertEqual(len({l[1] for l in lineas}), len(lineas), "sin códigos repetidos")
        self.assertEqual(len(E.CODIGOS), 35)
        self.assertEqual(bal[7][1:], ("TotalActivo", "Total activo", "ACTIVO", "total"))
        self.assertEqual(res[6][1], "OtrosEri", "el modelo de 2011 decía «Otros»; los archivos reales dicen OtrosEri")
        self.assertEqual({l[4] for l in bal + res}, {"detalle", "total"})

    def test_los_codigos_de_la_cuadratura_son_los_del_catalogo(self):
        """Si alguien cambia una lista y no la otra, la compuerta dejaría de mirar lo que se publica."""
        def detalle(tabla, seccion):
            return tuple(l[1] for l in E.CATALOGO[tabla] if l[3] == seccion and l[4] == "detalle")
        self.assertEqual(detalle("balance", "ACTIVO"), cuadratura.FFMM_ACTIVOS)
        self.assertEqual(detalle("balance", "PASIVO"), cuadratura.FFMM_PASIVOS)
        self.assertEqual(detalle("resultados", "INGRESOS/PÉRDIDAS DE LA OPERACIÓN"), cuadratura.FFMM_INGRESOS)
        self.assertEqual(detalle("resultados", "GASTOS"), cuadratura.FFMM_GASTOS)

    def test_el_orden_es_el_de_la_ficha_y_no_el_alfabetico_del_xml(self):
        codigos = [l[1] for l in E.CATALOGO["balance"]]
        self.assertNotEqual(codigos, sorted(codigos))
        self.assertEqual(codigos[:2], ["EfectivoYEfectivoEquivalente", "ActivosFinancierosAValorRazonableConEfectoEnResultados"])


class TestLecturaDelXml(unittest.TestCase):
    def esperado(self, d):
        self.assertEqual(d["actual"]["TotalActivo"], 192872200)
        self.assertEqual(d["actual"]["ActivoNetoAtribuibleALosParticipes"], 192845275)
        self.assertEqual(d["anterior"]["TotalActivo"], 251970282)

    def test_codificaciones_que_declaran_mal_su_contenido(self):
        casos = {
            "latin-1 declarado": dict(),
            "UTF-8 falso (cuerpo latin-1)": dict(declaracion="UTF-8"),
            "sin declaración (latin-1)": dict(declaracion=None),
            "declaración inventada (RUN pegado)": dict(declaracion="iso-8011-K"),
            "UTF-8 real": dict(declaracion="UTF-8", codificacion="utf-8"),
            "UTF-8 sin declaración": dict(declaracion=None, codificacion="utf-8"),
            "con BOM": dict(declaracion="UTF-8", codificacion="utf-8", bom=True),
        }
        for nombre, kw in casos.items():
            with self.subTest(nombre):
                raiz = E.leer_xml(X.xml(**kw))
                self.esperado(E.extraer(raiz, "8011", 2025))
                self.assertEqual(raiz.findtext("DatosPeriodo/NombreAuditoresExternos"), X.AUDITOR,
                                 "las tildes sobreviven a la decodificación")

    def test_extrae_identificacion_moneda_notas_y_comparativo(self):
        d = extraer()
        self.assertEqual((d["run_dv"], d["dv_coincide"]), ("8011-K", True))
        self.assertEqual((d["rut_agf"], d["agf"]), ("91999000", "Principal Administradora General de Fondos"))
        self.assertEqual((d["moneda_cmf"], d["moneda"]), ("$$", "CLP"))
        self.assertEqual(len(d["actual"]), 35)
        self.assertEqual(len(d["anterior"]), 35)
        self.assertEqual(d["notas"]["EfectivoYEfectivoEquivalente"], "6")
        self.assertEqual(d["notas"]["ComisionDeAdministracion"], "8")
        self.assertNotIn("TotalActivo", d["notas"])
        self.assertEqual(d["actual"]["ComisionDeAdministracion"], -2552317, "los gastos van con signo negativo")
        self.assertEqual(cuadratura.identidades_ffmm(d["actual"]), [])
        self.assertEqual(cuadratura.identidades_ffmm(d["anterior"]), [])

    def test_pesos_y_dolares(self):
        self.assertEqual(extraer(moneda="$$")["moneda"], "CLP")
        self.assertEqual(extraer(moneda="PROM")["moneda"], "USD")

    def test_las_cuentas_con_serie_y_las_de_otros_estados_no_pisan_balance_ni_resultados(self):
        d = extraer()
        # el XML sintético trae TotalActivo con Serie=B (999999) y un «Otros» de flujo (424242)
        self.assertEqual(d["actual"]["TotalActivo"], 192872200)
        self.assertEqual(d["actual"]["OtrosEri"], 73)
        self.assertFalse(d["usa_alias"])

    def test_codigo_con_espacio_final_y_elemento_de_codigo_vacio(self):
        d = extraer(con_espacio=("TotalPasivo", "OtrosActivos"), extra='  <Cuenta CodigoCuenta="" Context="PeriodoActual">5</Cuenta>\n')
        self.esperado(d)
        self.assertEqual(d["actual"]["TotalPasivo"], 26925)

    def test_el_alias_antiguo_otros_solo_si_falta_otroseri(self):
        d = extraer(alias_otros=True)
        self.assertTrue(d["usa_alias"])
        self.assertEqual(d["actual"]["OtrosEri"], 73)
        self.assertEqual(cuadratura.identidades_ffmm(d["actual"]), [], "la identidad de ingresos valida el alias")
        # con ambos códigos manda OtrosEri y se ignora el «Otros» del flujo
        d = extraer()
        self.assertEqual(d["actual"]["OtrosEri"], 73)

    def test_sin_comparativo_el_anterior_queda_vacio(self):
        d = extraer(sin_anterior=True)
        self.assertEqual(d["anterior"], {})
        self.assertEqual(len(d["actual"]), 35)

    def test_importes_con_decimales_en_cero_se_aceptan_y_otros_no(self):
        raw = X.xml().replace(b">192872200<", b">192872200.00<")
        self.assertEqual(extraer(raw)["actual"]["TotalActivo"], 192872200)
        with self.assertRaises(E.ErrorFuente) as cm:
            extraer(X.xml().replace(b">192872200<", b">19287220x<"))
        self.assertIn("importe no entero", str(cm.exception))

    def test_cuenta_repetida_con_el_mismo_importe_se_tolera_y_con_otro_no(self):
        igual = X.xml(extra='  <Cuenta CodigoCuenta="TotalActivo" Context="PeriodoActual">192872200</Cuenta>\n')
        self.assertEqual(extraer(igual)["repetidas"], 1)
        with self.assertRaises(E.ErrorFuente) as cm:
            extraer(X.xml(extra='  <Cuenta CodigoCuenta="TotalActivo" Context="PeriodoActual">1</Cuenta>\n'))
        self.assertIn("dos veces", str(cm.exception))


class TestRechazos(unittest.TestCase):
    def rechaza(self, texto, **kw):
        with self.assertRaises(E.ErrorFuente) as cm:
            extraer(run=kw.pop("run", "8011"), anio=kw.pop("anio", 2025), **kw)
        self.assertIn(texto, str(cm.exception))

    def test_faltan_cuentas(self):
        self.rechaza("faltan 2 cuentas del ejercicio", omitir=("TotalPasivo", "OtrosActivos"))

    def test_es_de_otro_fondo_o_de_otro_cierre(self):
        self.rechaza("es del fondo 1234, no del 8011", run_xml="1234")
        self.rechaza("informa 06/2025, no 12/2025", mes="06")
        with self.assertRaises(E.ErrorFuente) as cm:
            E.extraer(E.leer_xml(X.xml("8011", 2024)), "8011", 2025)
        self.assertIn("no 12/2025", str(cm.exception))

    def test_moneda_desconocida(self):
        self.rechaza("moneda desconocida 'EUR'", moneda="EUR")

    def test_run_con_ceros_a_la_izquierda_es_el_mismo_fondo(self):
        self.assertEqual(extraer(run_xml="008011")["run_dv"], "8011-K")

    def test_digito_verificador_distinto_se_avisa_pero_no_rechaza(self):
        d = extraer(dv_xml="3")
        self.assertFalse(d["dv_coincide"])
        self.assertEqual(d["run_dv"], "8011-3")

    def test_faltan_los_bloques_de_identificacion(self):
        raw = X.xml().replace(b"<Identificacion>", b"<Otra>").replace(b"</Identificacion>", b"</Otra>")
        with self.assertRaises(E.ErrorFuente) as cm:
            E.extraer(E.leer_xml(raw), "8011", 2025)
        self.assertIn("faltan los bloques", str(cm.exception))

    def test_xml_mal_formado_pero_completo_es_error_de_contenido(self):
        raw = X.xml().replace(b"<Identificacion>", b"<Identificacion><x>")
        with self.assertRaises(E.ErrorFuente) as cm:
            E.leer_xml(raw)
        self.assertIn("mal formado", str(cm.exception))


class TestRespuestasTransitorias(unittest.TestCase):
    """Lo que la CMF a veces sirve en lugar del archivo: se reintenta, nunca se toma por dato."""

    def test_pagina_intermedia_en_lugar_del_xml(self):
        for cuerpo in (X.ficha("8011", 2025, "desafio"), b"<html><body>Servicio no disponible</body></html>", b""):
            with self.subTest(cuerpo[:30]), self.assertRaises(E.ErrorTransitorio):
                E.leer_xml(cuerpo)

    def test_xml_truncado(self):
        completo = X.xml()
        for corte in (len(completo) // 2, len(completo) - 20, 3500):
            with self.subTest(corte), self.assertRaises(E.ErrorTransitorio):
                E.leer_xml(completo[:corte])


class TestFicha(unittest.TestCase):
    def test_con_xml_sin_informacion_y_sin_enlace(self):
        self.assertEqual(E.clasificar_ficha(X.ficha("8011", 2025)), ("xml", X.nombre_archivo("8011", 2025)))
        self.assertEqual(E.clasificar_ficha(X.ficha("8011", 2025, "sin_informacion")), ("sin_informacion", None))
        self.assertEqual(E.clasificar_ficha(X.ficha("8011", 2025, "sin_enlace")), ("sin_enlace", None))

    def test_un_desafio_nunca_es_sin_informacion(self):
        with self.assertRaises(E.ErrorTransitorio):
            E.clasificar_ficha(X.ficha("8011", 2025, "desafio"))
        for basura in (b"", b"<html></html>", b"Error 503"):
            with self.subTest(basura), self.assertRaises(E.ErrorTransitorio):
                E.clasificar_ficha(basura)

    def test_la_ficha_llega_en_utf8_latin1_o_con_entidades(self):
        for cod in ("utf-8", "latin-1"):
            with self.subTest(cod):
                self.assertEqual(E.clasificar_ficha(X.ficha("8011", 2025, "sin_informacion", codificacion=cod)),
                                 ("sin_informacion", None))
                self.assertEqual(E.clasificar_ficha(X.ficha("8011", 2025, codificacion=cod))[0], "xml")
        con_entidades = (b"<html><a>Informaci&oacute;n Financiera</a><p>No existe informaci&oacute;n de la entidad "
                         b"para el periodo se&ntilde;alado.</p></html>")
        self.assertEqual(E.clasificar_ficha(con_entidades), ("sin_informacion", None))
        mayusculas = "<html><a>INFORMACIÓN FINANCIERA</a> NO EXISTE INFORMACIÓN DE LA ENTIDAD</html>"
        self.assertEqual(E.clasificar_ficha(mayusculas), ("sin_informacion", None))

    def test_si_hay_reenvios_gana_el_mas_reciente(self):
        viejo, nuevo = X.nombre_archivo("8011", 2025, 0), X.nombre_archivo("8011", 2025, 3)
        self.assertLess(E.enviado_de(viejo), E.enviado_de(nuevo))
        for extras in ((nuevo,), ):
            self.assertEqual(E.clasificar_ficha(X.ficha("8011", 2025, "xml", viejo, extras=extras)), ("xml", nuevo))
        self.assertEqual(E.clasificar_ficha(X.ficha("8011", 2025, "xml", nuevo, extras=(viejo,))), ("xml", nuevo))

    def test_enviado_de(self):
        self.assertEqual(E.enviado_de("FMEF2026811894_20260330_110924_8011.xml"), "2026-03-30 11:09:24")
        self.assertEqual(E.enviado_de("FMEF2013250151_20130228_151105_8001.xml"), "2013-02-28 15:11:05")
        self.assertIsNone(E.enviado_de("otro.xml"))
        self.assertIsNone(E.enviado_de(None))


class TestFilas(unittest.TestCase):
    def registro(self, **kw):
        d = extraer(**kw)
        return {"run": "8011", "anio": 2025, "archivo": X.nombre_archivo("8011", 2025), "sha256": "a" * 64,
                "enviado": E.enviado_de(X.nombre_archivo("8011", 2025)), "run_dv": d["run_dv"], "nombre": d["nombre"],
                "rut_agf": d["rut_agf"], "agf": d["agf"], "moneda_cmf": d["moneda_cmf"], "moneda": d["moneda"],
                "actual": d["actual"], "anterior": d["anterior"], "notas": d["notas"]}

    def test_columnas_orden_y_valores(self):
        filas = E.filas(self.registro())
        self.assertEqual({t: len(f) for t, f in filas.items()}, {"balance": 16, "resultados": 19})
        for f in filas["balance"] + filas["resultados"]:
            self.assertEqual(tuple(f), E.COLUMNAS)
            self.assertEqual(f["periodo"], "2025-12")
        bal = filas["balance"]
        self.assertEqual([f["orden"] for f in bal], list(range(1, 17)))
        self.assertEqual((bal[7]["codigo_cuenta"], bal[7]["valor_miles_mf"], bal[7]["valor_anterior_miles_mf"]),
                         ("TotalActivo", 192872200, 251970282))
        self.assertEqual((bal[0]["nota"], bal[7]["nota"]), ("6", None))
        self.assertEqual({f["tipo_linea"] for f in bal if f["orden"] in (8, 15, 16)}, {"total"})
        self.assertEqual({f["seccion"] for f in bal}, {"ACTIVO", "PASIVO", "ACTIVO NETO"})
        res = filas["resultados"]
        self.assertEqual([f["orden"] for f in res], list(range(1, 20)))
        self.assertEqual(res[8]["valor_miles_mf"], -2552317)
        self.assertEqual({f["seccion"] for f in res}, {"INGRESOS/PÉRDIDAS DE LA OPERACIÓN", "GASTOS", "RESULTADO"})

    def test_sin_comparativo_el_valor_anterior_es_nulo(self):
        for f in E.filas(self.registro(sin_anterior=True))["balance"]:
            self.assertIsNone(f["valor_anterior_miles_mf"])

    def test_la_suma_de_los_detalles_es_el_total(self):
        bal = {f["orden"]: f["valor_miles_mf"] for f in E.filas(self.registro())["balance"]}
        self.assertEqual(sum(bal[i] for i in range(1, 8)), bal[8])
        self.assertEqual(sum(bal[i] for i in range(9, 15)), bal[15])
        self.assertEqual(bal[8] - bal[15], bal[16])


class TestDv(unittest.TestCase):
    def test_digito_verificador(self):
        self.assertEqual(E.dv("8011"), "K")
        self.assertEqual(E.dv("8001"), "2")
        self.assertEqual(E.dv("76034728"), "0")


if __name__ == "__main__":
    unittest.main()

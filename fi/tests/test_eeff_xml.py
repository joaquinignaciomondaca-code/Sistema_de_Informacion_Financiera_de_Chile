"""Fuentes CMF originales y casos adversariales, sin red ni escrituras en docs/."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from fi.scripts import eeff_xml as m
from fi.scripts.auditar_eeff import verificar_tablas
from fi.scripts.cotejo_eeff import cotejar, numero

FIXTURES = Path(__file__).parent / "fixtures"
MUESTRAS = json.loads((FIXTURES / "muestras.json").read_text(encoding="utf-8"))


def datos(run="7002", periodo="2026-06"):
    meta = next(f for f in MUESTRAS if f["run"] == run and f["periodo"] == periodo)
    raw = (FIXTURES / f"{run}_{periodo}.xml").read_bytes()
    html = (FIXTURES / f"{run}_{periodo}.html").read_bytes()
    return raw, html, meta


def registro(run="7002", periodo="2026-06"):
    raw, html, meta = datos(run, periodo)
    r = m.extraer(raw, run, periodo)
    r.update(
        tipo_entidad=meta["tipo_entidad"],
        archivo=meta["archivo"],
        enviado=m.enviado_de(meta["archivo"]),
    )
    r["cotejo"] = cotejar(html, r)
    return r


def cambiar(
    codigo,
    contexto="PeriodoActual",
    valor=None,
    quitar=False,
    run="7002",
    periodo="2026-06",
):
    raiz = m.leer_xml(datos(run, periodo)[0])
    for c in list(raiz):
        if (
            c.tag == "Cuenta"
            and c.get("CodigoCuenta", "").strip() == codigo
            and c.get("Context") == contexto
        ):
            if quitar:
                raiz.remove(c)
            else:
                c.text = str(valor)
    return ET.tostring(raiz, encoding="utf-8")


class FuenteRealTest(unittest.TestCase):
    def test_hashes_originales_de_xml_y_ficha(self):
        for f in MUESTRAS:
            with self.subTest(run=f["run"], periodo=f["periodo"]):
                raw, html, _ = datos(f["run"], f["periodo"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), f["sha256_xml"])
                self.assertEqual(hashlib.sha256(html).hexdigest(), f["sha256_ficha"])

    def test_ocho_muestras_y_todos_los_contextos_publicables_cuadran(self):
        fs = {"balance": [], "resultados": []}
        for f in MUESTRAS:
            r = registro(f["run"], f["periodo"])
            for t, filas in m.filas(r).items():
                fs[t].extend(filas)
        a = verificar_tablas(fs)
        self.assertEqual(a["errores"], [])
        self.assertEqual(a["fondos_cierres"], 8)
        self.assertEqual(a["reglas"], 303)
        self.assertEqual(
            {t: len(f) for t, f in fs.items()}, {"balance": 672, "resultados": 750}
        )

    def test_no_aplica_la_cuadratura_de_fondos_mutuos(self):
        r = registro("7064", "2021-12")
        c = r["tablas"]["balance"]["PeriodoActual"]
        self.assertEqual(
            (
                c["TotalActivo"],
                c["TotalPasivo"],
                c["TotalPatrimonioNeto"],
                c["TotalPasivoCorriente"],
            ),
            (24887, 24887, 24826, 61),
        )
        self.assertEqual(r["moneda"], "USD")
        self.assertNotEqual(
            c["TotalActivo"], c["TotalPasivo"] + c["TotalPatrimonioNeto"]
        )

    def test_acumulado_trimestre_y_comparativo_no_se_mezclan(self):
        r = registro("9919", "2026-06")
        cs = r["tablas"]["resultados"]
        self.assertEqual(cs["PeriodoActual"]["ResultadoDelEjercicio"], 1907262)
        self.assertEqual(cs["TrimestreActual"]["ResultadoDelEjercicio"], 1024958)
        self.assertEqual(cs["PeriodoAnterior"]["ResultadoDelEjercicio"], 1122940)
        self.assertEqual(r["contextos"]["TrimestreActual"]["inicio"], "2026-04-01")
        self.assertEqual(
            r["contextos"]["PeriodoAnualAnterior"]["termino"], "2025-12-31"
        )

    def test_saldo_de_apertura_solo_tiene_fecha_inicio(self):
        r = registro("7002", "2010-12")
        self.assertEqual(
            r["contextos"]["SaldoInicialTerceraColumna"],
            {"inicio": "2009-01-01", "termino": "2009-01-01"},
        )
        self.assertEqual(len(m.filas(r)["balance"]), 126)

    def test_ausencia_de_comparativo_no_inventa_ceros(self):
        r = registro("7002", "2010-12")
        self.assertEqual(
            r["validacion"]["resultados"]["PeriodoAnterior"],
            {"estado": "sin_cuentas", "reglas": 0},
        )
        self.assertFalse(
            any(f["contexto"] == "PeriodoAnterior" for f in m.filas(r)["resultados"])
        )

    def test_comparativo_incompleto_real_se_excluye_con_motivo(self):
        for run in ("9919", "9383"):
            r = registro(run, "2026-06")
            self.assertEqual(
                r["validacion"]["balance"]["PeriodoAnualAnterior"]["estado"],
                "rechazado",
            )
            self.assertNotIn("PeriodoAnualAnterior", r["tablas"]["balance"])
            self.assertEqual(len(m.filas(r)["balance"]), 42)
            self.assertIn(
                "faltan 1 cuentas",
                r["validacion"]["balance"]["PeriodoAnualAnterior"]["errores"][0],
            )

    def test_contextos_no_expuestos_por_ficha_no_se_declaran_cotejados(self):
        r = registro("7008", "2025-12")
        self.assertEqual(r["cotejo"]["cuentas"]["resultados"]["TrimestreActual"], 0)
        fs = [f for f in m.filas(r)["resultados"] if f["contexto"] == "TrimestreActual"]
        self.assertTrue(all(f["cotejo_ficha"] == "sin_columna" for f in fs))
        self.assertEqual(len(fs), 30)

    def test_orden_del_catalogo_y_tipos_explicitos(self):
        r = registro()
        fs = m.filas(r)
        actual = [f for f in fs["balance"] if f["contexto"] == "PeriodoActual"]
        self.assertEqual([f["orden"] for f in actual], list(range(1, 43)))
        self.assertEqual(actual[-1]["codigo_cuenta"], "TotalPasivo")
        self.assertEqual(actual[-1]["seccion"], "PASIVO Y PATRIMONIO")
        self.assertTrue(all(f["tipo_periodo"] == "saldo" for f in fs["balance"]))
        self.assertTrue(
            all(
                f["tipo_periodo"] == "acumulado"
                for f in fs["resultados"]
                if f["contexto"] == "PeriodoActual"
            )
        )


class GuardasTest(unittest.TestCase):
    def test_rechaza_todos_los_casos_de_identidad_periodo_moneda_y_fechas(self):
        raw = datos()[0]
        cambios = [
            ("Identificacion/RUTFondoInforma", "9001"),
            ("DatosPeriodo/PeriodoPresentacionEstadosFinancieros/Mes", "03"),
            ("DatosPeriodo/MonedaPresentacionEstadosFinancieros", "XYZ"),
            ("Contextos/PeriodoActual/FechaTermino", "2026-09-30"),
            ("DatosPeriodo/EstadoResultadosIntegrales", "N"),
        ]
        for ruta, valor in cambios:
            raiz = m.leer_xml(raw)
            raiz.find(ruta).text = valor
            with self.subTest(ruta=ruta), self.assertRaises(m.ErrorFuente):
                m.extraer(ET.tostring(raiz), "7002", "2026-06")

    def test_cuenta_actual_ausente_rechaza_documento(self):
        for codigo in (
            "TotalActivo",
            "TotalPasivo",
            "ComisionDeAdministracion",
            "ResultadoDelEjercicio",
        ):
            with self.subTest(codigo=codigo), self.assertRaises(m.ErrorFuente):
                m.extraer(cambiar(codigo, quitar=True), "7002", "2026-06")

    def test_resultado_acumulado_actual_incorrecto_rechaza_documento(self):
        with self.assertRaises(m.ErrorFuente):
            m.extraer(
                cambiar("InteresesYReajustes", "PeriodoActual", valor=1000000),
                "7002",
                "2026-06",
            )

    def test_trimestre_incorrecto_no_se_publica_pero_actual_completo_se_conserva(self):
        r = m.extraer(
            cambiar("InteresesYReajustes", "TrimestreActual", valor=1000000),
            "7002",
            "2026-06",
        )
        self.assertNotIn("TrimestreActual", r["tablas"]["resultados"])
        self.assertEqual(
            r["validacion"]["resultados"]["TrimestreActual"]["estado"], "rechazado"
        )
        self.assertIn("PeriodoActual", r["tablas"]["resultados"])

    def test_trimestre_sin_fechas_declaradas_no_se_infiere(self):
        raiz = m.leer_xml(datos()[0])
        ctx = raiz.find("Contextos")
        ctx.remove(ctx.find("TrimestreActual"))
        r = m.extraer(ET.tostring(raiz), "7002", "2026-06")
        self.assertNotIn("TrimestreActual", r["tablas"]["resultados"])
        self.assertIn(
            "sin fechas declaradas",
            r["validacion"]["resultados"]["TrimestreActual"]["errores"][0],
        )

    def test_fechas_incoherentes_de_contexto_adicional_se_excluyen(self):
        raiz = m.leer_xml(datos()[0])
        raiz.find("Contextos/TrimestreActual/FechaInicio").text = "2026-01-01"
        r = m.extraer(ET.tostring(raiz), "7002", "2026-06")
        self.assertNotIn("TrimestreActual", r["tablas"]["resultados"])
        self.assertEqual(
            r["validacion"]["resultados"]["TrimestreActual"]["estado"], "rechazado"
        )

    def test_detalle_de_balance_malo_con_totales_buenos_no_pasa(self):
        with self.assertRaises(m.ErrorFuente):
            m.extraer(
                cambiar("EfectivoYEfectivoEquivalente", valor=1), "7002", "2026-06"
            )

    def test_comparativo_descuadrado_no_aporta_filas_y_politica_estricta_lo_rechaza(
        self,
    ):
        raw = cambiar("TotalActivo", "PeriodoAnualAnterior", valor=1)
        r = m.extraer(raw, "7002", "2026-06")
        self.assertNotIn("PeriodoAnualAnterior", r["tablas"]["balance"])
        self.assertEqual(
            r["validacion"]["balance"]["PeriodoAnualAnterior"]["estado"], "rechazado"
        )
        with self.assertRaises(m.ErrorFuente):
            m.extraer(raw, "7002", "2026-06", estricto_comparativos=True)

    def test_no_cambia_el_signo_de_los_gastos(self):
        r = registro()
        self.assertEqual(
            r["tablas"]["resultados"]["PeriodoActual"]["CostosFinancieros"], -8538028
        )
        with self.assertRaises(m.ErrorFuente):
            m.extraer(cambiar("CostosFinancieros", valor=8538028), "7002", "2026-06")

    def test_enteros_exactos_y_rechazo_de_decimales_separadores_e_inf(self):
        self.assertEqual(m.entero("9007199254740993", "x"), 9007199254740993)
        self.assertEqual(m.entero("-12.000", "x"), -12)
        self.assertEqual(m.entero("+42,0", "x"), 42)
        for t in ("1.234,56", "3.5", "NaN", "Inf", "", "N/A", str(2**63)):
            with self.subTest(t=t), self.assertRaises(m.ErrorFuente):
                m.entero(t, "x")

    def test_cuenta_duplicada_distinta_se_rechaza(self):
        root = m.leer_xml(datos()[0])
        root.append(
            ET.fromstring(
                '<Cuenta CodigoCuenta="TotalActivo" Context="PeriodoActual">1</Cuenta>'
            )
        )
        with self.assertRaisesRegex(m.ErrorFuente, "valores distintos"):
            m.extraer(ET.tostring(root), "7002", "2026-06")

    def test_duplicado_identico_no_duplica_filas(self):
        root = m.leer_xml(datos()[0])
        c = next(
            c
            for c in root.findall("Cuenta")
            if c.get("CodigoCuenta") == "TotalActivo"
            and c.get("Context") == "PeriodoActual"
        )
        root.append(copy.deepcopy(c))
        r = m.extraer(ET.tostring(root), "7002", "2026-06")
        self.assertEqual(len(r["tablas"]["balance"]["PeriodoActual"]), 42)
        self.assertGreater(r["duplicadas"], 0)

    def test_dv_recibido_incorrecto_se_conserva_y_se_advierte(self):
        root = m.leer_xml(datos()[0])
        root.find("Identificacion/DVFondoInforma").text = "K"
        r = m.extraer(ET.tostring(root), "7002", "2026-06")
        self.assertEqual(r["dv_fondo_fuente"], "K")
        self.assertTrue(r["avisos"])
        r.update(tipo_entidad="FINRE", archivo="FIEF202600_20260330_110000_7002.xml")
        self.assertEqual(m.filas(r)["balance"][0]["run_fondo_dv"], "7002-5")

    def test_html_y_xml_cortado_son_transitorios_no_sin_informacion(self):
        for raw in (
            b"<html><script>challenge()</script></html>",
            b"<IFRS><Cuenta>",
            b"{}",
            b"",
        ):
            with self.subTest(raw=raw), self.assertRaises(m.ErrorTransitorio):
                m.leer_xml(raw)
        with self.assertRaises(m.ErrorFuente):
            m.leer_xml(b'<!DOCTYPE IFRS [<!ENTITY x "42">]><IFRS></IFRS>')

    def test_denegacion_explicita_cmf_es_exclusion_no_ausencia_ni_ceros(self):
        with self.assertRaisesRegex(m.ErrorFuente, "rechaza explícitamente"):
            m.leer_xml(b"ACCION NO PERMITIDA 16")
        with self.assertRaises(m.ErrorTransitorio):
            m.leer_xml(b"<html>challenge() reintente</html>")

    def test_codificacion_falsa_o_inventada_no_modifica_las_cifras(self):
        for decl in ('encoding="iso-8011-K"', 'encoding="UTF-8"'):
            raw = ('<?xml version="1.0" ' + decl + "?>").encode() + ET.tostring(
                m.leer_xml(datos()[0]), encoding="utf-8"
            )
            r = m.extraer(raw, "7002", "2026-06")
            self.assertEqual(
                r["tablas"]["balance"]["PeriodoActual"]["TotalActivo"], 592906447
            )


class FichaYCotejoTest(unittest.TestCase):
    def test_clasifica_fichas_y_no_admite_enlaces_externos(self):
        self.assertEqual(m.clasificar_ficha(datos()[1])[0], "xml")
        sin = b"<html><h2>Informacion Financiera</h2>No existe informacion de la entidad para el periodo se\xc3\xb1alado.</html>"
        self.assertEqual(m.clasificar_ficha(sin), ("sin_informacion", None))
        self.assertEqual(
            m.clasificar_ficha(b"<html>Informacion Financiera</html>"),
            ("sin_enlace", None),
        )
        externo = b'<a href="https://evil.example/ifrs_xml_verarchivo.php?archivo=FIEF202600_20260330_110000_7002.xml">x</a>'
        with self.assertRaises(m.ErrorTransitorio):
            m.clasificar_ficha(externo)

    def test_ausencia_fechada_real_fi_y_rechazo_de_otro_periodo(self):
        pagina = b"<html>INFORMACION FINANCIERA. No existe informacion de la entidad para el periodo 2026/06. Verifique parametros.</html>"
        self.assertEqual(
            m.clasificar_ficha(pagina, "2026-06"), ("sin_informacion", None)
        )
        with self.assertRaises(m.ErrorTransitorio):
            m.clasificar_ficha(pagina, "2026-03")

    def test_reenvio_el_mas_reciente_por_fecha_no_correlativo(self):
        a = "FIEF2026999999_20260101_100000_7002.xml"
        b = "FIEF2026000001_20260901_100000_7002.xml"
        html = "".join(
            f'<a href="/ifrs_xml_verarchivo.php?archivo={f}">XML</a>' for f in (a, b)
        ).encode()
        self.assertEqual(m.clasificar_ficha(html), ("xml", b))

    def test_fecha_envio_es_local_y_no_adivina_huso(self):
        self.assertEqual(
            m.enviado_de("FIEF20261_20260330_110924_7002.xml"), "2026-03-30T11:09:24"
        )
        self.assertIsNone(m.enviado_de("FIEFsin_fecha.xml"))

    def test_monto_distinto_en_su_celda_rechaza_cotejo(self):
        raw, html, _ = datos()
        html = html.replace(b"3.560.527", b"3.560.528", 1)
        with self.assertRaisesRegex(m.ErrorFuente, "cotejo"):
            cotejar(html, m.extraer(raw, "7002", "2026-06"))

    def test_moneda_fecha_o_concepto_distinto_rechazan_cotejo(self):
        raw, html, _ = datos()
        for original, cambiado in (
            (b"miles de Pesos", b"miles de Dolar"),
            (b"Al 30/06/2026", b"Al 30/06/2025"),
            (b"Efectivo y efectivo equivalente", b"Concepto incorrecto"),
        ):
            with self.subTest(original=original), self.assertRaises(m.ErrorFuente):
                cotejar(
                    html.replace(original, cambiado), m.extraer(raw, "7002", "2026-06")
                )

    def test_numeros_chilenos_no_rellena_guion_o_blanco(self):
        self.assertEqual(numero("-1.234.567"), -1234567)
        self.assertIsNone(numero("-"))
        self.assertIsNone(numero(""))
        for t in ("1,2", "NaN", "1.23"):
            with self.assertRaises(m.ErrorFuente):
                numero(t)

    def test_fuente_masiva_otra_pagina_no_pasa_como_ficha_financiera(self):
        with self.assertRaises(m.ErrorFuente):
            cotejar(b"<html>sin tablas</html>", registro())


if __name__ == "__main__":
    unittest.main()

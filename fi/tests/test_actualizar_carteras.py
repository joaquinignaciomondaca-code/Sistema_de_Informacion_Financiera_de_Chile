"""Pruebas del parser y los centinelas de las páginas VRC/CRV de la CMF."""
from __future__ import annotations

import html
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyarrow.parquet as pq

from fi.scripts import actualizar_carteras as ac
from fi.scripts import backfill_pactos_historico as backfill
from fi.scripts.actualizar_carteras import (
    PACTOS_SUB,
    PACTOS_TH,
    es_relleno_pacto,
    leer_pactos,
    leer_pactos_detallado,
)


def _tabla_pactos(periodo: str, codigo: str, detalle: list[str], total: dict[int, str]) -> str:
    encabezado = "<tr>" + "".join(f"<th>{html.escape(v)}</th>" for v in PACTOS_TH) + "</tr>"
    subencabezado = "<tr>" + "".join(f"<th>{html.escape(v)}</th>" for v in PACTOS_SUB) + "</tr>"
    meta = f"<tr><td>Período: {periodo} Cifras expresadas en miles de: $$.</td></tr>"
    fila = "<tr>" + "".join(f"<td>{html.escape(v)}</td>" for v in detalle) + "</tr>"
    t = [""] * 15
    t[7] = f"TOTAL {codigo}"
    for indice, valor in total.items():
        t[indice] = valor
    total_html = "<tr>" + "".join(f"<td>{html.escape(v)}</td>" for v in t) + "</tr>"
    return f"<table>{encabezado}{subencabezado}{meta}{fila}{total_html}</table>"


class TextoCmfTest(unittest.TestCase):
    """Codificación, centinelas de texto y reparación de contrapartes de las páginas CMF."""

    def test_decodifica_latin1_declarado_y_utf8(self):
        pagina = ('<html><head><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'
                  "</head><body><p>Larraín Vial S.A. Corredora de Bolsa</p></body></html>")
        self.assertIn("Larraín Vial", ac.decodificar_html(pagina.encode("latin-1")))
        self.assertIn("Larraín Vial", ac.decodificar_html(pagina.encode("utf-8")))

    def test_repara_mojibake_de_utf8_leido_como_latin1(self):
        """Una página UTF-8 con un byte suelto se lee en latin-1: las tildes no se publican rotas."""
        raw = b'<p>Euroam' + "érica".encode() + b'\xe9 AGF S.A.</p>'
        texto = ac.decodificar_html(raw)
        self.assertIn("Euroamérica", texto)
        self.assertNotIn("Ã©", texto)

    def test_texto_sano_no_se_toca(self):
        for pagina in ("<p>Compania de Seguros S.A.</p>", "<p>Larraín Vial S.A.</p>", "<p>Pacto UF $$</p>"):
            self.assertEqual(ac.decodificar_html(pagina.encode("utf-8")), pagina)

    def test_centinelas_de_identificacion_se_publican_como_vacio(self):
        for col in ("isin", "nemotecnico", "nombre_emisor"):
            with self.subTest(col=col):
                for centinela in ("NA", "n/a", " N/A ", "S/I", "", "  "):
                    self.assertIsNone(ac.convertir(centinela, "t", col))
                self.assertEqual(ac.convertir("CL0002936111", "t", col), "CL0002936111")
        # En las columnas de codificación «NA» es un código de la CMF, no «sin dato».
        self.assertEqual(ac.convertir("NA", "t", "tipo_interes"), "NA")
        self.assertEqual(ac.convertir("NA", "t", "pais"), "NA")

    def test_cuerpo_contraparte_descarta_solo_el_dv_valido(self):
        self.assertEqual(ac.cuerpo_contraparte("805370009"), "80537000")
        self.assertEqual(ac.cuerpo_contraparte("80537000-9"), "80537000")
        self.assertEqual(ac.cuerpo_contraparte("80537000"), "80537000")
        # Sin DV válido al final el valor se conserva tal como llegó (dato de la CMF).
        self.assertEqual(ac.cuerpo_contraparte("80537001"), "80537001")
        self.assertIsNone(ac.cuerpo_contraparte(None))

    def test_contraparte_vacia_o_danada_se_completa_con_el_padron(self):
        self.assertEqual(ac.normalizar_contraparte("96921130", None), "MBI CORREDORES DE BOLSA S.A.")
        self.assertEqual(ac.normalizar_contraparte("76081215", "Larra\ufffdVial Activos S.A Adm. Gral. De Fondos"),
                         "LARRAIN VIAL ACTIVOS S.A. ADM. GRAL. DE FONDOS")
        self.assertEqual(ac.normalizar_contraparte("77750920", "Euroam\ufffdrica AGF S.A."), "Euroamérica AGF S.A.")

    def test_contraparte_con_grafias_alternativas_del_mismo_rut(self):
        casos = [
            ("80537000", "LARRAIN VIAL S.A. CORREDORA DE BOLSAS", "LARRAIN VIAL S.A. CORREDORA DE BOLSA"),
            ("8053700", "LARRAIN VIAL S.A. CORREDORA DE BOLSAS", "LARRAIN VIAL S.A. CORREDORA DE BOLSA"),
            ("76081215", "LARRAIN VIAL ACTIVOS S.A.", "LARRAIN VIAL ACTIVOS S.A. ADM. GRAL. DE FONDOS"),
            ("96899230", "EUROAMERICA C. DE B.", "EUROAMERICA CORREDORES DE BOLSA S.A."),
            ("96899230", "Euroamerica Corredora de Bolsa S.A.", "EUROAMERICA CORREDORES DE BOLSA S.A."),
            ("96772490", "CONSORCIO FINANCIERO", "CONSORCIO CORREDORES DE BOLSA S.A."),
            ("96921130", "MBI CB", "MBI CORREDORES DE BOLSA S.A."),
            ("96921130", "mbi corredores de bolsa", "MBI CORREDORES DE BOLSA S.A."),
            ("96519800", "BCI CORREDORES DE BOLSA S.A", "BCI CORREDOR DE BOLSA S.A."),
        ]
        for rut, nombre, esperado in casos:
            with self.subTest(rut=rut, nombre=nombre):
                self.assertEqual(ac.normalizar_contraparte(rut, nombre), esperado)

    def test_contraparte_no_fusiona_entidades_distintas(self):
        # La AGF Larraín Vial con el RUT de la corredora (fuente inconsistente) se deja tal cual.
        self.assertEqual(ac.normalizar_contraparte("80537000-9", "Larraín Vial Activos S.A. Adm. Gral. de Fondos"),
                         "Larraín Vial Activos S.A. Adm. Gral. de Fondos")
        self.assertEqual(ac.normalizar_contraparte("80537000", "LARRAIN VIAL ACTIVOS S.A. ADM. GRAL. DE FONDOS"),
                         "LARRAIN VIAL ACTIVOS S.A. ADM. GRAL. DE FONDOS")
        # La corredora con el RUT de la AGF tampoco: el RUT y el nombre del padrón no coinciden.
        self.assertEqual(ac.normalizar_contraparte("76081215", "LarraIn Vial S.A Corredora de Bolsa"),
                         "LarraIn Vial S.A Corredora de Bolsa")
        # El mismo RUT con otro nombre (rebautizo, p. ej. IM Trust → Credicorp) no se reescribe.
        self.assertEqual(ac.normalizar_contraparte("96489000", "IM TRUST SA CB"), "IM TRUST SA CB")
        self.assertEqual(ac.normalizar_contraparte("96489000", "CREDICORP CAPITAL S.A. CB"), "CREDICORP CAPITAL S.A. CB")

    def test_avisos_texto_danado_reporta_lo_no_reconstruido(self):
        sanas = {"pactos": [{"contraparte": "BANCO BICE", "nemotecnico": "FNBCI-151226"}]}
        self.assertEqual(ac.avisos_texto_danado(sanas), [])
        danadas = {"cartera_nacional": [{"nemotecnico": "ARRENDA.VICU\ufffdSPA"}]}
        avisos = ac.avisos_texto_danado(danadas)
        self.assertEqual(len(avisos), 1)
        self.assertIn("cartera_nacional.nemotecnico", avisos[0])

    def test_pagina_latin1_se_parsea_con_el_nombre_correcto(self):
        detalle = [
            "CRV", "31/12/2024", "01/01/2025", "Larraín Vial S.A. Corredora de Bolsa", "80537000",
            "1.000", "$$", "0,1200", "1.001", "1.000", "CL0000000001", "BCHIUO0911",
            "Banco de Chile", "BTP", "900",
        ]
        pagina = _tabla_pactos("202412", "CRV", detalle, {5: "1.000", 8: "1.001", 9: "1.000", 14: "900"})
        filas, malas, descuadres, _, _ = leer_pactos_detallado(pagina.encode("latin-1"))
        self.assertEqual(malas, [])
        self.assertEqual(descuadres, [])
        self.assertEqual(filas[0]["contraparte"], "LARRAIN VIAL S.A. CORREDORA DE BOLSA")


class PactosHistoricosTest(unittest.TestCase):
    def test_excluye_fila_ficticia_y_conserva_operacion_real(self):
        relleno = [
            "VRC", "01/01/2010", "31/10/2013", "Nombre Contraparte", "0", "0", "$$", "0,0000",
            "0", "0", "ISIN", "Nomotecnico", "Nombre Emisor", "CFI", "0",
        ]
        operacion = [
            "CRV", "31/12/2013", "01/01/2014", "Banco de Chile", "97006000", "1.000", "$$", "0,1200",
            "1.001", "1.000", "CL0000000001", "BCHIUO0911", "Banco de Chile", "BTP", "900",
        ]
        raw = (
            _tabla_pactos("201309", "VRC", relleno, {5: "0", 8: "0", 9: "0", 14: "0"})
            + _tabla_pactos("201309", "CRV", operacion, {5: "1.000", 8: "1.001", 9: "1.000", 14: "900"})
        ).encode()

        filas, malas, descuadres, moneda, excluidas = leer_pactos_detallado(raw)

        self.assertEqual(excluidas, 1)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["tipo_operacion"], "CRV")
        self.assertEqual(malas, [])
        self.assertEqual(descuadres, [])
        self.assertEqual(moneda, "$$")
        self.assertEqual(len(leer_pactos(raw)[0]), 1)

    def test_excluye_plantillas_historicas_con_rut_ficticio_no_cero(self):
        rellenos = [
            [
                "VRC", "01/01/2010", "31/10/2013", "Nombre Contraparte 1", "999234999",
                "0", "$$", "0,0000", "0", "0", "ISIN", "Nemotecnico", "Nombre Emisor", "CFI", "0",
            ],
            [
                "VRC", "01/01/2010", "31/10/2013", "Nombre Contraparte 1", "111111111",
                "0", "$$", "0,0000", "0", "0", "ISIN", "Nemotecnico", "Nombre Emisor", "CFI", "0",
            ],
        ]
        raw = b"".join(
            _tabla_pactos("201206", "VRC", fila, {5: "0", 8: "0", 9: "0", 14: "0"}).encode()
            for fila in rellenos
        )

        filas, malas, descuadres, _, excluidas = leer_pactos_detallado(raw)

        self.assertEqual(filas, [])
        self.assertEqual(excluidas, 2)
        self.assertEqual(malas, [])
        self.assertEqual(descuadres, [])

    def test_contraparte_larrain_vial_se_repara_por_rut_y_utf8_se_conserva(self):
        for rut_contraparte in ("80537000", "80537000-9", "805370009"):
            with self.subTest(rut=rut_contraparte):
                detalle = [
                    "CRV", "31/12/2024", "01/01/2025", "Larra\ufffdVial S.A.Corredora de Bolsa",
                    rut_contraparte, "1.000", "$$", "0,1200", "1.001", "1.000",
                    "CL0000000001", "BCHIUO0911", "Banco de Chile", "BTP", "900",
                ]
                raw = _tabla_pactos(
                    "202412", "CRV", detalle,
                    {5: "1.000", 8: "1.001", 9: "1.000", 14: "900"},
                ).encode("utf-8")

                filas, malas, descuadres, _, _ = leer_pactos_detallado(raw)

                self.assertEqual(malas, [])
                self.assertEqual(descuadres, [])
                self.assertEqual(filas[0]["contraparte"], "LARRAIN VIAL S.A. CORREDORA DE BOLSA")

        detalle_utf8 = [
            "CRV", "31/12/2024", "01/01/2025", "Euroamérica AGF S.A.", "77750920",
            "1.000", "$$", "0,1200", "1.001", "1.000", "CL0000000001", "BCHIUO0911",
            "Banco de Chile", "BTP", "900",
        ]
        raw_utf8 = _tabla_pactos(
            "202412", "CRV", detalle_utf8, {5: "1.000", 8: "1.001", 9: "1.000", 14: "900"}
        ).encode("utf-8")
        filas_utf8 = leer_pactos_detallado(raw_utf8)[0]
        self.assertEqual(filas_utf8[0]["contraparte"], "Euroamérica AGF S.A.")
        self.assertEqual(
            ac.normalizar_contraparte(
                "80537000-9", "Larraín Vial Activos S.A. Adm. Gral. de Fondos"
            ),
            "Larraín Vial Activos S.A. Adm. Gral. de Fondos",
        )

    def test_fila_con_rotulos_genericos_y_montos_no_cero_no_se_descarta(self):
        fila = {
            "tipo_operacion": "VRC",
            "contraparte": "Nombre Contraparte",
            "rut_contraparte": "0",
            "isin": "ISIN",
            "nemotecnico": "Nomotecnico",
            "nombre_emisor": "Nombre Emisor",
            "tipo_instrumento": "CFI",
            "valor_inicial_miles_mf": 0,
            "tasa_pacto_pct": 0,
            "valor_final_miles_mf": 1,
            "valorizacion_cierre_miles_mf": 0,
            "valor_mercado_miles_moneda": 0,
        }
        self.assertFalse(es_relleno_pacto(fila))

    def test_fila_real_con_montos_cero_no_se_descarta_solo_por_cero(self):
        fila = {
            "tipo_operacion": "CRV",
            "contraparte": "Banco de Chile",
            "rut_contraparte": "97006000",
            "isin": "CL0000000001",
            "nemotecnico": "BCHIUO0911",
            "nombre_emisor": "Banco de Chile",
            "tipo_instrumento": "BTP",
            "valor_inicial_miles_mf": 0,
            "tasa_pacto_pct": 0,
            "valor_final_miles_mf": 0,
            "valorizacion_cierre_miles_mf": 0,
            "valor_mercado_miles_moneda": 0,
        }
        self.assertFalse(es_relleno_pacto(fila))

    def test_reintenta_respuesta_con_encabezado_transitorio(self):
        parseado = ([], [], [], "$$", 0)
        with (
            patch.object(backfill.ac, "_get", side_effect=[b"interstitial", b"pagina correcta"]),
            patch.object(backfill.ac, "leer_pactos_detallado",
                         side_effect=[ac.ErrorValidacion("encabezado inesperado"), parseado]),
            patch.object(backfill.time, "sleep"),
        ):
            raw, resultado, reintentos, error, descargas = backfill._descargar_y_parsear("7182", "2013-09")
        self.assertEqual(raw, b"pagina correcta")
        self.assertEqual(resultado, parseado)
        self.assertEqual(reintentos, 1)
        self.assertIsNone(error)
        self.assertEqual(descargas, 2)

    def test_pactos_publicados_no_conservan_filas_de_plantilla(self):
        carpeta = ac.RAIZ / "docs" / "outputs" / "fi" / "pactos"
        if not carpeta.exists():
            self.skipTest("no hay salida FI publicada en este checkout")
        rutas = sorted(carpeta.glob("*.parquet"))
        sospechosas = []
        for ruta in rutas:
            if ruta.name == "_vacio.parquet":
                continue
            for fila in pq.read_table(ruta).to_pylist():
                if es_relleno_pacto(fila):
                    sospechosas.append((ruta.name, fila["periodo"], fila["run_fondo"]))
        self.assertEqual(sospechosas, [])

    def test_pactos_publicados_normalizan_larrain_vial_por_rut(self):
        carpeta = ac.RAIZ / "docs" / "outputs" / "fi" / "pactos"
        if not carpeta.exists():
            self.skipTest("no hay salida FI publicada en este checkout")
        diferencias = []
        filas_objetivo = 0
        for ruta in sorted(carpeta.glob("*.parquet")):
            if ruta.name == "_vacio.parquet":
                continue
            for fila in pq.read_table(ruta, columns=["contraparte", "rut_contraparte"]).to_pylist():
                esperado = ac.normalizar_contraparte(fila["rut_contraparte"], fila["contraparte"])
                if esperado != fila["contraparte"]:
                    diferencias.append((ruta.name, fila["rut_contraparte"], fila["contraparte"]))
                if esperado == "LARRAIN VIAL S.A. CORREDORA DE BOLSA":
                    filas_objetivo += 1
        self.assertGreater(filas_objetivo, 0)
        self.assertEqual(diferencias, [])

    def test_pactos_publicados_sin_caracter_de_reemplazo(self):
        carpeta = ac.RAIZ / "docs" / "outputs" / "fi" / "pactos"
        if not carpeta.exists():
            self.skipTest("no hay salida FI publicada en este checkout")
        danadas = []
        for ruta in sorted(carpeta.glob("*.parquet")):
            if ruta.name == "_vacio.parquet":
                continue
            tabla = pq.read_table(ruta)
            for col in ac.COLUMNAS_TEXTO:
                if col not in tabla.column_names:
                    continue
                for valor in tabla.column(col).to_pylist():
                    if isinstance(valor, str) and "\ufffd" in valor:
                        danadas.append((ruta.name, col, valor))
        self.assertEqual(danadas, [])

    def test_pactos_publicados_sin_centinelas_de_no_aplica(self):
        """«NA»/«N/A» se publican como vacío: una sola forma de decir «sin dato»."""
        carpeta = ac.RAIZ / "docs" / "outputs" / "fi" / "pactos"
        if not carpeta.exists():
            self.skipTest("no hay salida FI publicada en este checkout")
        centinelas = []
        for ruta in sorted(carpeta.glob("*.parquet")):
            if ruta.name == "_vacio.parquet":
                continue
            tabla = pq.read_table(ruta, columns=sorted(ac.CENTINELAS_TEXTO))
            for col in tabla.column_names:
                for valor in tabla.column(col).to_pylist():
                    if isinstance(valor, str) and valor.strip().upper() in ac.TEXTO_VACIO:
                        centinelas.append((ruta.name, col, valor))
        self.assertEqual(centinelas, [])

    def test_pactos_publicados_publican_el_cuerpo_del_rut(self):
        """`rut_contraparte` es el cuerpo sin DV; el DV pegado (805370009) se descarta."""
        carpeta = ac.RAIZ / "docs" / "outputs" / "fi" / "pactos"
        if not carpeta.exists():
            self.skipTest("no hay salida FI publicada en este checkout")
        pegados = []
        for ruta in sorted(carpeta.glob("*.parquet")):
            if ruta.name == "_vacio.parquet":
                continue
            for valor in pq.read_table(ruta, columns=["rut_contraparte"])["rut_contraparte"].to_pylist():
                if valor and ac.cuerpo_contraparte(valor) != valor:
                    pegados.append((ruta.name, valor))
        self.assertEqual(pegados, [])

    def test_pactos_publicados_cumplen_las_reglas_de_contraparte(self):
        """La contraparte publicada es la que devuelve la normalización vigente (idempotente)."""
        carpeta = ac.RAIZ / "docs" / "outputs" / "fi" / "pactos"
        if not carpeta.exists():
            self.skipTest("no hay salida FI publicada en este checkout")
        diferencias, filas = [], {}
        for ruta in sorted(carpeta.glob("*.parquet")):
            if ruta.name == "_vacio.parquet":
                continue
            for fila in pq.read_table(ruta, columns=["periodo", "run_fondo", "contraparte",
                                                    "rut_contraparte"]).to_pylist():
                if ac.normalizar_contraparte(fila["rut_contraparte"], fila["contraparte"]) != fila["contraparte"]:
                    diferencias.append((ruta.name, fila["rut_contraparte"], fila["contraparte"]))
                filas[(fila["periodo"], fila["run_fondo"])] = fila["contraparte"]
        self.assertEqual(diferencias, [])
        # La única contraparte vacía del histórico (2014-12, RUN 9077) se completó con el padrón.
        self.assertEqual(filas[("2014-12", "9077")], "MBI CORREDORES DE BOLSA S.A.")

    def test_escribir_vacio_reemplaza_el_cierre_anual_existente(self):
        salida_anterior = ac.SALIDA
        with tempfile.TemporaryDirectory() as tmp:
            ac.SALIDA = Path(tmp)
            try:
                ac.escribir("pactos", "2013-09", [{"periodo": "2013-09", "run_fondo": "7182",
                                                     "tipo_operacion": "CRV"}])
                ruta = Path(tmp) / "pactos" / "2013.parquet"
                self.assertEqual(pq.ParquetFile(ruta).metadata.num_rows, 1)
                ac.escribir("pactos", "2013-09", [])
                self.assertEqual(pq.ParquetFile(ruta).metadata.num_rows, 0)
            finally:
                ac.SALIDA = salida_anterior


if __name__ == "__main__":
    unittest.main()

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

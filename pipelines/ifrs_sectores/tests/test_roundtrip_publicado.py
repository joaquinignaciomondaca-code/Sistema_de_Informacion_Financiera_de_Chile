"""Ida y vuelta contra lo ya publicado: el parseo no puede cambiar lo publicado.

Reconstruye, a partir de los Parquet publicados de un trimestre, un TXT con el formato de
la CMF, lo vuelve a pasar por `leer_archivo` y comprueba que salen exactamente las mismas
filas: misma cuenta, mismo orden, misma repetición, mismo importe.

Es la prueba que faltaba para refactorizar el extractor sin miedo: si alguien cambia el
criterio de `orden`, de `repeticion` o del importe no entero, esto lo caza comparándolo
con los 17 años ya publicados en lugar de con una expectativa escrita a mano.

No descarga nada: usa docs/outputs tal como está en el repositorio.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

from pipelines.ifrs_sectores import actualizar  # noqa: E402

PERIODO = "2026-06"          # AAAA-MM publicado
PERIODO_TXT = "202606"       # como viene en el archivo
VOLVER_TIPO = {"individual": "I", "consolidado": "C"}
CAMPOS = ("periodo", "rut", "razon_social", "tipo_balance", "moneda", "estado_financiero",
          "orden", "cuenta", "valor", "valor_no_numerico", "repeticion", "taxonomia")


def publicado(sec: str, prefijo: str, tabla: str):
    ruta = RAIZ / "docs" / "outputs" / sec / f"{prefijo}_{tabla}" / f"{PERIODO[:4]}.parquet"
    if not ruta.is_file():
        return []
    return [f for f in pq.read_table(ruta).to_pylist() if f["periodo"] == PERIODO]


def a_txt(filas) -> list[str]:
    """Una fila publicada -> la línea del TXT que pudo haberla producido."""
    lineas = []
    for f in filas:
        valor = f["valor"] if f["valor"] is not None else (f["valor_no_numerico"] or "")
        lineas.append(";".join([PERIODO_TXT, str(f["rut"]), f["razon_social"],
                                VOLVER_TIPO[f["tipo_balance"]], f["moneda"], f["cuenta"],
                                str(valor), f["taxonomia"], f["estado_financiero"]]))
    return lineas


def relleno(cuantas: int = 60) -> list[str]:
    """Sociedades de otros giros: el extractor exige al menos 50 en el archivo."""
    return [";".join([PERIODO_TXT, str(90000000 + i), f"EMPRESA {i} SPA", "I", "CLP",
                      "Total de activos", "1", "TAX CI", "ESF C/NC"]) for i in range(cuantas)]


class RoundtripTest(unittest.TestCase):
    def test_lo_publicado_se_vuelve_a_leer_igual(self):
        sectores = {"agf": ("agf", "agf"), "securitizadoras": ("securitizadoras", "securitizadoras"),
                    "cajas_compensacion": ("cajas_compensacion", "ccaf")}
        revisados = 0
        for sec, (carpeta, prefijo) in sectores.items():
            esperado = {t: publicado(carpeta, prefijo, t) for t in actualizar.TABLAS}
            if not esperado["balance"]:
                continue
            # `leer_archivo` espera también las listas que solo se completan con este
            # archivo (factoring/leasing), aunque aquí lleguen vacías.
            listas = {s: {} for s in list(actualizar.SECTORES) + list(actualizar.SOLO_LISTA)}
            # Los RUT del sector van en su lista: así el reparto no depende del patrón
            # del nombre, que es justamente lo que aquí no queremos poner a prueba.
            listas[sec] = {str(f["rut"]): f["razon_social"] for f in esperado["balance"]}
            lineas = a_txt(esperado["balance"]) + a_txt(esperado["resultados"]) + relleno()
            datos, _est, avisos = actualizar.leer_archivo(
                ("\n".join(lineas) + "\n").encode("utf-8"), PERIODO_TXT, listas)
            self.assertEqual(avisos, [], f"{sec}: avisos inesperados al releer lo publicado")
            for tabla in actualizar.TABLAS:
                obtenido = datos[sec][tabla]
                self.assertEqual(len(obtenido), len(esperado[tabla]),
                                 f"{sec}.{tabla}: cambió la cantidad de filas")
                claves = lambda filas: [(tuple(str(f[c]) for c in CAMPOS)) for f in filas]  # noqa: E731
                self.assertEqual(sorted(claves(obtenido)), sorted(claves(esperado[tabla])),
                                 f"{sec}.{tabla}: el parseo ya no reproduce lo publicado")
                revisados += len(obtenido)
        self.assertGreater(revisados, 1000, "la prueba debe cubrir un trimestre completo")

    def test_orden_y_repeticion_son_los_publicados(self):
        """El `orden` reconstruido reproduce la posición original de cada cuenta."""
        filas = publicado("agf", "agf", "resultados")
        self.assertTrue(filas)
        listas = {s: {} for s in list(actualizar.SECTORES) + list(actualizar.SOLO_LISTA)}
        listas["agf"] = {str(f["rut"]): f["razon_social"] for f in filas}
        datos, _est, _a = actualizar.leer_archivo(
            ("\n".join(a_txt(filas) + relleno()) + "\n").encode("utf-8"), PERIODO_TXT, listas)
        por_cuenta = {(f["rut"], f["estado_financiero"], f["cuenta"], f["repeticion"]): f["orden"]
                      for f in datos["agf"]["resultados"]}
        for f in filas:
            clave = (str(f["rut"]), f["estado_financiero"], f["cuenta"], f["repeticion"])
            self.assertEqual(por_cuenta.get(clave), f["orden"], f["cuenta"])


if __name__ == "__main__":
    unittest.main()

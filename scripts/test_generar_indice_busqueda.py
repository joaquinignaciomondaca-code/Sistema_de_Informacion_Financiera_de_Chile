#!/usr/bin/env python3
"""Regresiones del índice y sus metadatos derivados de los catálogos publicados."""
import unittest

from scripts.generar_indice_busqueda import construir


TABLA = {
    "id": "macro_ipc",
    "name": "macro.ipc",
    "viewName": "macro_ipc",
    "sector": "macro",
    "sectorLabel": "Macroeconomía",
    "descripcion": "Índice de precios.",
    "columnas": [],
}


def fuentes(archivos=None, fuente="BCCh", corte="Mensual"):
    return (
        {"datos": [TABLA], "generado": "2026-10-25"},
        {"conceptos": [{"termino": "inflación", "tablas": ["macro_ipc"]}]},
        {"objetos": [{"id": "macro_ipc", "fuente": fuente, "corte": corte}]},
        {"grupos": [{"items": [{"id": "macro_ipc", "archivos": archivos or []}]}]},
    )


class PruebasGenerador(unittest.TestCase):
    def test_incorpora_fuente_cobertura_id_y_formatos(self):
        entrada = fuentes([{"ruta": "outputs/macro/ipc.parquet"}, {"ruta": "outputs/macro/ipc.csv"}])
        indice, errores = construir(*entrada)
        self.assertEqual(errores, [])
        tabla = indice["tablas"][0]
        self.assertEqual(tabla["id"], "macro_ipc")
        self.assertEqual(tabla["fuente"], "BCCh")
        self.assertEqual(tabla["corte"], "Mensual")
        self.assertEqual(tabla["formatos"], ["CSV", "PARQUET"])

    def test_objeto_sin_archivo_directo_no_inventa_formatos(self):
        indice, errores = construir(*fuentes())
        self.assertEqual(errores, [])
        self.assertEqual(indice["tablas"][0]["formatos"], [])

    def test_ids_desalineados_fallan_en_lugar_de_publicar_metadatos_equivocados(self):
        entrada = list(fuentes([{"ruta": "outputs/macro/ipc.parquet"}]))
        entrada[2] = {"objetos": [{"id": "otra_tabla", "fuente": "BCCh", "corte": "Mensual"}]}
        indice, errores = construir(*entrada)
        self.assertEqual(indice, {})
        self.assertTrue(any("IDs del diccionario/API distintos" in error for error in errores))

    def test_fuente_y_corte_son_obligatorios(self):
        indice, errores = construir(*fuentes(fuente="", corte=""))
        self.assertEqual(indice["tablas"], [])
        self.assertTrue(any("no tiene fuente y/o corte" in error for error in errores))


if __name__ == "__main__":
    unittest.main()

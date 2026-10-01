"""Pruebas de las etiquetas «N Entidades» del menú (`etiquetas_conteo`).

Factoring/leasing y las cajas de compensación son listas que crecen solas con las altas del TXT
IFRS; si su etiqueta es un texto fijo, el menú dice «28 Entidades» con 32 sociedades. Las demás
listas llevan etiquetas redactadas a mano que no equivalen a sus filas y no deben tocarse.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

from pipelines.entidades import actualizar_listas as al  # noqa: E402

FL = "factoring_leasing/factoring_leasing_maestro"
CCAF = "cajas_compensacion/ccaf_maestro"

# Misma sangría que el archivo real: grupos a 2 espacios, listas a 10.
SIDEBAR = '''const EXPLORER_TREE = [
  {
    id: "group_bancos",
    type: "group",
    badges: [
      { type: "entities", text: "40 códigos · Falta validar", title: "Códigos históricos y vigentes" }
    ],
    children: [
      {
        id: "sector_bancos",
        children: [
          {
            id: "cat_bancos_lista_entidades",
            badge: "40 códigos · Falta validar",
            tables: []
          },
        ]
      }
    ]
  },
  {
    id: "group_factoring_leasing",
    type: "group",
    label: "FACTORING & LEASING (CMF / NBFI)",
    badges: [
      { type: "entities", text: "28 Entidades", title: "Lista de 28 entidades de Factoring y Leasing" }
    ],
    children: [
      {
        id: "sector_factoring_leasing",
        children: [
          {
            id: "cat_factoring_leasing_lista_entidades",
            type: "circular",
            label: "Lista de Entidades",
            badge: "28 Entidades",
            tables: []
          },
          {
            id: "cat_factoring_leasing_balance",
            badge: "70 cierres · 28 RUT",
            tables: []
          },
        ]
      }
    ]
  },
  {
    id: "group_cajas_compensacion",
    type: "group",
    badges: [
      { type: "entities", text: "6 Entidades", title: "Los Andes, La Araucana, Los Héroes, Caja 18 (y 2 históricas)" },
      { type: "data", text: "65 trimestres", title: "Balance y resultados IFRS" }
    ],
    children: [
      {
        id: "sector_cajas_compensacion",
        children: [
          {
            id: "cat_ccaf_lista_entidades",
            badge: "6 Entidades",
            tables: []
          },
        ]
      }
    ]
  },
];
'''


class EtiquetasConteoTest(unittest.TestCase):
    def test_siguen_a_las_filas_de_factoring_y_de_las_cajas(self):
        t = al.etiquetas_conteo(SIDEBAR, {FL: 32, CCAF: 7})
        self.assertIn('text: "32 Entidades", title: "Lista de 32 entidades de Factoring y Leasing"', t)
        self.assertIn('id: "cat_factoring_leasing_lista_entidades",\n            type: "circular",\n'
                      '            label: "Lista de Entidades",\n            badge: "32 Entidades"', t)
        self.assertIn('text: "7 Entidades", title: "Los Andes', t)
        self.assertIn('id: "cat_ccaf_lista_entidades",\n            badge: "7 Entidades"', t)

    def test_no_toca_lo_que_no_es_conteo_de_filas(self):
        t = al.etiquetas_conteo(SIDEBAR, {FL: 32, CCAF: 7})
        self.assertIn('text: "40 códigos · Falta validar"', t)             # banca: etiqueta a mano
        self.assertIn('badge: "70 cierres · 28 RUT"', t)                   # los RUT con datos no son filas del maestro
        self.assertIn('text: "65 trimestres"', t)

    def test_solo_cambian_las_etiquetas_previstas(self):
        antes = SIDEBAR.splitlines()
        despues = al.etiquetas_conteo(SIDEBAR, {FL: 32, CCAF: 7}).splitlines()
        self.assertEqual(len(antes), len(despues))
        cambiadas = [i for i, (a, d) in enumerate(zip(antes, despues)) if a != d]
        self.assertEqual(len(cambiadas), 4)        # grupo FL, lista FL, grupo CCAF, lista CCAF

    def test_es_idempotente_y_sin_cambios_no_escribe_nada_distinto(self):
        una = al.etiquetas_conteo(SIDEBAR, {FL: 32, CCAF: 7})
        self.assertEqual(al.etiquetas_conteo(una, {FL: 32, CCAF: 7}), una)
        self.assertEqual(al.etiquetas_conteo(SIDEBAR, {FL: 28, CCAF: 6}), SIDEBAR)

    def test_una_lista_sin_dato_se_deja_como_esta(self):
        self.assertEqual(al.etiquetas_conteo(SIDEBAR, {}), SIDEBAR)
        t = al.etiquetas_conteo(SIDEBAR, {FL: 32})
        self.assertIn('text: "6 Entidades", title: "Los Andes', t)

    def test_no_cruza_al_grupo_vecino_si_falta_la_etiqueta_propia(self):
        """Si el grupo de FL perdiera su etiqueta, el patrón no puede «robarse» la de las cajas."""
        sin_etiqueta = SIDEBAR.replace(
            '      { type: "entities", text: "28 Entidades", title: "Lista de 28 entidades de Factoring y Leasing" }\n', '')
        t = al.etiquetas_conteo(sin_etiqueta, {FL: 32, CCAF: 6})
        self.assertIn('text: "6 Entidades", title: "Los Andes', t)
        self.assertNotIn('"32 Entidades", title: "Los Andes', t)


if __name__ == "__main__":
    unittest.main()

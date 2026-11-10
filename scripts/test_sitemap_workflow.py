#!/usr/bin/env python3
"""Comprobación estructural del workflow SEO (seo-sitemap-github-action.yml).

El workflow regenera el sitemap con scripts/build_metadatos.py y lo commitea
en main. Esta comprobación valida el XML y que sus URLs pertenezcan al sitio;
la lista concreta la calcula el generador desde las páginas indexables.

Stdlib únicamente: el workflow SEO no instala dependencias.
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SITEMAP = RAIZ / "docs" / "sitemap.xml"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
BASE = "https://joaquinignaciomondaca-code.github.io/Sistema_de_Informacion_Financiera_de_Chile/"


class SitemapGeneradoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml = SITEMAP.read_text(encoding="utf-8")
        cls.raiz = ET.fromstring(cls.xml)  # bien formado o declara error
        cls.urls = cls.raiz.findall("s:url", NS)

    def test_el_sitemap_es_urlset_del_esquema_oficial(self):
        self.assertEqual(self.raiz.tag, f"{{{NS['s']}}}urlset")

    def test_cada_url_tiene_loc_y_viene_del_sitio_publicado(self):
        locs = []
        for url in self.urls:
            loc = url.find("s:loc", NS)
            if loc is None or not (loc.text or "").strip():
                self.fail("Un <url> del sitemap no tiene <loc>")
            locs.append(loc.text.strip())
        self.assertTrue(locs, "El sitemap no tiene ninguna URL")
        for loc in locs:
            self.assertTrue(loc.startswith(BASE), f"Loc fuera del sitio publicado: {loc}")

    def test_no_hay_locs_duplicados(self):
        locs = [u.find("s:loc", NS).text.strip() for u in self.urls]
        duplicados = {loc for loc in locs if locs.count(loc) > 1}
        self.assertEqual(duplicados, set(), f"Locs duplicados: {sorted(duplicados)}")

    def test_excluye_las_carpetas_excluidas_por_la_accion(self):
        locs = [u.find("s:loc", NS).text.strip() for u in self.urls]
        for loc in locs:
            self.assertNotIn(".well-known", loc, f"Loc en carpeta excluida: {loc}")
            self.assertNotIn("/notas/", loc, f"Loc en carpeta excluida: {loc}")


if __name__ == "__main__":
    unittest.main()

"""Pruebas de la sincronización de las cifras publicadas del README.

El contrato derivado reescribe catálogo, descargas y `metricas_publicadas.json`, y también las
cifras que el README declara de ellos. Si esa sustitución se come una palabra o toca una cifra
que no le corresponde, la auditoría de la web deja de ser confiable. Estas pruebas fijan las
tres propiedades: solo cambian números, son idempotentes y no inventan filas.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from scripts import build_metricas_publicadas as m  # noqa: E402


README = """# Título

| Sector | Elementos | Filas (suma por objeto) | Serie | Fuente |
|---|---:|---:|---|---|
| Seguros de Vida y Generales | 24 | 10.553.271 | 2016-11 → 2026-09 | CMF |
| Macroeconomía y Tasas | 24 | 41.543 | diaria | BCCh |
| **Total** | **89** | **19.814.981** | **2001 → 2026** | |

El catálogo API suma 90 objetos y 19.814.981 filas. Esta tabla enumera 89 elementos de
Descargas. De esos 89 elementos, 74 están en niveles principales (19.714.666 filas; 99,5 %)
y 15 en archivo/registro (100.315; 0,5 %); una variante se cuenta como elemento.

Texto que no debe cambiar: 2.026 filas de ejemplo y el 74 % de otra cosa.
"""


def reporte(macro_filas: int = 41_554, total: int = 19_814_992) -> dict:
    return {
        "fuentes": {
            "api_v2": {"objetos": 90, "filas": total},
            "descargas": {
                "principal": {"elementos": 74, "filas": 19_714_677, "bytes": 486_062_058},
                "fuera_de_foco": {"elementos": 15, "filas": 100_315, "bytes": 1_896_720},
                "ocultos": {"elementos": 1, "filas": 0, "bytes": 2_589},
                "por_sector": {
                    "seguros": {"etiqueta": "Seguros de Vida y Generales", "elementos": 24,
                                "filas": 10_553_271},
                    "macro": {"etiqueta": "Macroeconomía y Tasas", "elementos": 24,
                              "filas": macro_filas},
                },
            },
        }
    }


class SincronizarReadmeTest(unittest.TestCase):
    def sincronizar(self, texto: str, datos: dict) -> tuple[str, list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "README.md"
            destino.write_text(texto, encoding="utf-8")
            with mock.patch.object(m, "ROOT", Path(tmp)):
                cambios = m.sincronizar_readme(datos)
            return destino.read_text(encoding="utf-8"), cambios

    def test_actualiza_la_tabla_el_total_y_los_resumenes(self):
        texto, cambios = self.sincronizar(README, reporte())
        self.assertIn("| Macroeconomía y Tasas | 24 | 41.554 |", texto)
        self.assertIn("| **Total** | **89** | **19.814.992** |", texto)
        self.assertIn("El catálogo API suma 90 objetos y 19.814.992 filas", texto)
        self.assertIn("(19.714.677 filas;", texto)
        self.assertIn("De esos 89 elementos, 74 están en niveles principales", texto)
        self.assertTrue(cambios)

    def test_no_toca_ninguna_palabra_ni_cifra_ajena(self):
        texto, _ = self.sincronizar(README, reporte())
        original = README.splitlines()
        nuevas = texto.splitlines()
        self.assertEqual(len(original), len(nuevas))
        for antes, despues in zip(original, nuevas):
            # Solo pueden cambiar los dígitos: se comparan los textos con los números enmascarados.
            import re
            self.assertEqual(re.sub(r"[\d.]+", "#", antes), re.sub(r"[\d.]+", "#", despues))
        self.assertIn("Texto que no debe cambiar: 2.026 filas de ejemplo y el 74 %", texto)

    def test_es_idempotente(self):
        primera, cambios = self.sincronizar(README, reporte())
        self.assertTrue(cambios)
        segunda, cambios2 = self.sincronizar(primera, reporte())
        self.assertEqual(primera, segunda)
        self.assertEqual(cambios2, [])

    def test_un_readme_ya_al_dia_no_se_reescribe(self):
        al_dia = README.replace("41.543", "41.554").replace("19.814.981", "19.814.992") \
                      .replace("19.714.666", "19.714.677")
        _texto, cambios = self.sincronizar(al_dia, reporte())
        self.assertEqual(cambios, [])

    def test_sin_tabla_sectorial_no_inventa_nada(self):
        texto, cambios = self.sincronizar("# Solo prosa\n", reporte())
        self.assertEqual(texto, "# Solo prosa\n")
        self.assertEqual(cambios, [])

    def test_sincroniza_las_etiquetas_que_el_readme_abrevia(self):
        """`FinTech` en el README, «Fintech y Finanzas Abiertas» en el catálogo.

        La auditoría ya normalizaba ese alias para comparar, pero la sincronización no, así que
        la celda no se podía reescribir nunca: fintech quedó declarado con 265 filas mientras el
        catálogo tenía 267 y `web_audit` fallaba en cada push sin que ninguna regeneración lo
        arreglara (2026-11-04). La prueba fija que el alias se sustituye igual que la etiqueta.
        """
        datos = reporte()
        datos["fuentes"]["descargas"]["por_sector"]["fintech"] = {
            "etiqueta": "Fintech y Finanzas Abiertas", "elementos": 1, "filas": 267,
        }
        texto = README.replace(
            "| Macroeconomía y Tasas |",
            "| FinTech | 1 | 265 | registro vigente | CMF |\n| Macroeconomía y Tasas |",
        )
        sincronizado, cambios = self.sincronizar(texto, datos)
        self.assertIn("| FinTech | 1 | 267 | registro vigente | CMF |", sincronizado)
        self.assertIn("tabla sectorial · FinTech", cambios)
        # Y no se duplica la fila ni se reescribe dos veces.
        self.assertEqual(sincronizado.count("| FinTech |"), 1)


class ConstruirTest(unittest.TestCase):
    def test_leer_artefactos_usa_el_catalogo_y_las_descargas_publicadas(self):
        """La sincronización necesita cifras aunque el contrato aún no haya convergido."""
        datos = m.leer_artefactos()
        api = datos["fuentes"]["api_v2"]
        descargas = datos["fuentes"]["descargas"]
        self.assertEqual(api["objetos"], len(m.cargar_json(m.DOCS / "api" / "v2" / "catalog.json")["objetos"]))
        self.assertEqual(
            descargas["principal"]["elementos"] + descargas["fuera_de_foco"]["elementos"]
            + descargas["ocultos"]["elementos"],
            len(m.cargar_catalogo_descargas().get("grupos", []) and
                [i for g in m.cargar_catalogo_descargas()["grupos"] for i in g["items"]]),
        )
        self.assertTrue(descargas["por_sector"])


if __name__ == "__main__":
    unittest.main()

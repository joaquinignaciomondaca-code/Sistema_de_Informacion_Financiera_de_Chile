"""Pruebas sin red de diagnóstico incremental de ZIP CMF (nunca publica)."""
import io
import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from bancos.scripts import probe_repos_zip_cmf as probe

URL = "https://www.cmfchile.cl/portal/estadisticas/626/articles-50166_recurso_1.zip"


def zip_data(period="202112", bank="001"):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(f"bundle/b1{period}{bank}.txt", "codigo\tclp\n1160000\t64365000\n2160000\t95009000\n1000000\t10000")
        z.writestr(f"bundle/b2{period}{bank}.txt", "codigo\tclp\n141000000\t123\n243000000\t456")
    return out.getvalue()


class ProbeTests(unittest.TestCase):
    def test_discover_period_and_deduplicate(self):
        html = f'<a href="{URL}">Descargar diciembre 2021 (zip)</a>'
        self.assertEqual(probe.discover(html), {"2021-12": URL})
        self.assertEqual(probe.discover(html + html), {"2021-12": URL})
        with self.assertRaises(ValueError):
            probe.discover(html + html.replace("50166", "50167"))
        conflicts = set()
        probe.discover(html + html.replace("50166", "50167") +
                       '<a href="https://www.cmfchile.cl/portal/estadisticas/626/articles-999_recurso_1.zip">Descargar junio 2020</a>',
                       strict=False, conflicts_out=conflicts)
        self.assertEqual(conflicts, {"2021-12"})

    def test_discover_real_cmf_structure(self):
        """El índice real rotula el mes fuera del texto del ancla."""
        href = "articles-113067_recurso_1.zip?ts=1787944720"
        # (a) mes en el encabezado que acompaña al enlace de descarga
        heading = (f'<a href="{href}"><span class="ico"></span></a>'
                   '<h3><a href="w4-article-113067.html">Balance y Estado de Situación Bancos Julio 2026</a></h3>'
                   '31/07/2026')
        self.assertEqual(probe.discover(heading)["2026-07"],
                         "https://www.cmfchile.cl/portal/estadisticas/626/" + href)
        # (b) mes en un atributo del ancla o en el alt de su ícono
        with_title = f'<a href="{href}" title="Descargar Julio 2026"><img alt="zip"/></a>'
        self.assertEqual(probe.discover(with_title)["2026-07"],
                         "https://www.cmfchile.cl/portal/estadisticas/626/" + href)
        # (c) el id del artículo por sí solo NO puede adjudicar un mes
        with self.assertRaises(ValueError):
            probe.discover('<a href="articles-113067_recurso_1.zip"></a>')

    def test_conflicting_heading_does_not_create_false_month(self):
        good = ('<a href="articles-28704_recurso_1.zip" title="Descargar Marzo 2020"></a>'
                '<h3>Balance y Estado de Situación Bancos marzo 2020</h3>')
        wrong = ('<a href="articles-39990_recurso_1.zip" title="Descargar Marzo 2020"></a>'
                 '<h3>Balance y Estado de Situación Bancos marzo 2019</h3>')
        found = probe.discover(good + wrong)
        self.assertEqual(found, {"2020-03": "https://www.cmfchile.cl/portal/estadisticas/626/articles-28704_recurso_1.zip"})
        self.assertNotIn("2020-03", probe.discover(wrong +
            '<a href="articles-50166_recurso_1.zip">Descargar diciembre 2021</a>'))

    def test_empty_index_gives_safe_diagnostics(self):
        with self.assertRaisesRegex(ValueError, r"ZIP=0") as error:
            probe.discover("<html><title>Página temporal</title><body>Sin enlaces</body></html>")
        self.assertIn("Página temporal", str(error.exception))
        self.assertNotIn("<html>", str(error.exception))

    def test_diagnostics_show_clean_signals(self):
        html = ('<html><title>Índice</title><body>'
                '<a href="articles-113067_recurso_1.zip"><img alt="zip"/></a>'
                '<h3>Balance y Estado de Situación Bancos Julio 2026</h3></body></html>')
        # Con encabezado válido sí se resuelve; forzamos el caso sin señales
        # quitando el encabezado para revisar que el mensaje sea útil y limpio.
        with self.assertRaises(ValueError) as error:
            probe.discover(html.replace("<h3>Balance y Estado de Situación Bancos Julio 2026</h3>", ""))
        message = str(error.exception)
        self.assertIn("muestra=", message)
        self.assertIn("articles-113067_recurso_1.zip", message)
        self.assertNotIn("<a ", message)
        self.assertNotIn("<img", message)

    def test_incremental_and_manual(self):
        found = {p: URL for p in ("2026-04", "2026-05", "2026-06", "2026-07")}
        self.assertEqual(probe.select(found, "2026-04", "2026-06", date(2026, 9, 27), None), ["2026-06", "2026-07"])
        self.assertEqual(probe.select(found, "2026-04", None, date(2026, 9, 27), "2026-05"), ["2026-05"])
        with self.assertRaises(ValueError):
            probe.select(found, "2026-04", None, date(2026, 9, 27), "2026-09")

    def test_inspect_raw_b1_b2_no_conversion(self):
        report = probe.inspect_zip(zip_data(), "2021-12", "001", URL)
        self.assertEqual(len(report["archivos_balance"]), 2)
        b1 = report["archivos_balance"][0]
        self.assertEqual(b1["cuentas_candidatas"][0]["campos_crudos"], ["64365000"])
        self.assertEqual(report["periodo"], "2021-12")
        with self.assertRaises(ValueError):
            probe.inspect_zip(zip_data(), "2021-11", "001", URL)

    def test_run_creates_only_review_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "review.json"
            checkpoint = Path(temp) / "checkpoint.json"
            html = f'<a href="{URL}">Descargar diciembre 2021 (zip)</a>'.encode()
            with patch.object(probe, "read_public", side_effect=[html, zip_data()]):
                with patch.object(probe, "CATALOG", Path(temp) / "catalog.json"):
                    probe.CATALOG.write_text("[]")
                    with patch.object(probe, "LEGACY", Path(temp) / "legacy.json"):
                        probe.LEGACY.write_text(json.dumps([{"periodo":"2021-12", "codigo_institucion":"001", "repo_activo_mm_clp":64_365, "repo_pasivo_mm_clp":95_009}]))
                        before = probe.LEGACY.read_bytes()
                        result = probe.run(output=output, checkpoint=checkpoint, today=date(2022, 1, 15))
                        self.assertEqual(probe.LEGACY.read_bytes(), before)
            self.assertEqual(len(result), 1)
            self.assertEqual(json.loads(checkpoint.read_text())["periodo"], "2021-12")
            self.assertEqual(json.loads(output.read_text())["estado"], "diagnostico_no_validado")

    def test_failure_does_not_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "review.json"
            checkpoint = Path(temp) / "checkpoint.json"
            html = f'<a href="{URL}">Descargar diciembre 2021 (zip)</a>'.encode()
            with patch.object(probe, "read_public", side_effect=[html, b"not a zip"]):
                with patch.object(probe, "CATALOG", Path(temp) / "catalog.json"):
                    probe.CATALOG.write_text("[]")
                    with patch.object(probe, "LEGACY", Path(temp) / "legacy.json"):
                        probe.LEGACY.write_text(json.dumps([{"periodo":"2021-12", "codigo_institucion":"001"}]))
                        with self.assertRaises(ValueError):
                            probe.run(output=output, checkpoint=checkpoint, today=date(2022, 1, 15))
            self.assertFalse(output.exists())
            self.assertFalse(checkpoint.exists())


if __name__ == "__main__":
    unittest.main()

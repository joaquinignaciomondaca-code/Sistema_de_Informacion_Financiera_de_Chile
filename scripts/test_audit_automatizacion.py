"""Pruebas del guardián de automatización: frescura, estabilidad y cobertura de escritores.

Sin red: se sustituye la consulta a la API de GitHub por un doble que devuelve el historial
que cada caso necesita.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]  # scripts/ -> raíz del repositorio
sys.path.insert(0, str(RAIZ))

from scripts import audit_automatizacion as g  # noqa: E402


def corrida(conclusion: str, hace_dias: float) -> dict:
    momento = datetime.now(timezone.utc) - timedelta(days=hace_dias)
    return {"conclusion": conclusion, "updated_at": momento.isoformat().replace("+00:00", "Z")}


class FrescuraTest(unittest.TestCase):
    """La compuerta que debía haber avisado de los 33 días de `fi_eeff`."""

    def frescura_con(self, nombre: str, historial: list[dict]) -> tuple[list[str], list[str]]:
        """Corre `frescura()` completa con un doble de la API de GitHub."""
        vistos = []

        def api(ruta: str) -> dict:
            vistos.append(ruta)
            if ruta == "":
                return {"created_at": "2020-01-01T00:00:00Z"}
            if ruta.startswith("/runs"):
                return {"workflow_runs": historial[:10]}
            if "status=success" in ruta:
                exitosas = [r for r in historial if r["conclusion"] == "success"]
                return {"workflow_runs": exitosas[:1]}
            return {"workflow_runs": historial}

        original = g.workflows_inventariables
        g.workflows_inventariables = lambda: [(nombre, {"scripts": [], "max_dias": 16})]
        try:
            import urllib.request
            real = urllib.request.urlopen
            class Respuesta:
                def __init__(self, datos): self.datos = datos
                def read(self): return json.dumps(self.datos).encode()
                def __enter__(self): return self
                def __exit__(self, *a): return False
            import json
            urllib.request.urlopen = lambda req, timeout=60: Respuesta(api(req.full_url))
            try:
                errores = g.frescura("dueno/repo", "main")
            finally:
                urllib.request.urlopen = real
        finally:
            g.workflows_inventariables = original
        return errores, vistos

    def test_un_publicador_que_falla_mas_que_acierta_se_reporte(self):
        historial = [
            corrida("failure", 0.1), corrida("success", 0.2), corrida("failure", 0.4),
            corrida("failure", 0.6), corrida("failure", 0.8), corrida("success", 1.0),
        ]
        errores, _ = self.frescura_con("contrato_publicado.yml", historial)
        self.assertEqual(len(errores), 1, errores)
        self.assertIn("4 de sus últimas 6 corridas fallaron", errores[0])

    def test_un_publicador_estable_no_se_reporte(self):
        historial = [corrida("success", d) for d in (0.1, 0.3, 0.5, 0.7)]
        historial.append(corrida("failure", 0.9))
        self.assertEqual(self.frescura_con("fi_carteras.yml", historial)[0], [])

    def test_las_corridas_canceladas_no_cuentan_como_fallas(self):
        historial = [
            corrida("cancelled", 0.1), corrida("cancelled", 0.2),
            corrida("success", 0.3), corrida("failure", 0.4),
        ]
        self.assertEqual(self.frescura_con("pages.yml", historial)[0], [])

    def test_la_frescura_cubre_los_escritores_que_no_estan_en_el_inventario(self):
        """`fi_eeff.yml` escribe la rama aunque sus tablas ya estén inventariadas."""
        nombres = dict(g.workflows_inventariables())
        self.assertIn("fi_eeff.yml", nombres)
        self.assertIn("contrato_publicado.yml", nombres)
        self.assertGreaterEqual(nombres["fi_eeff.yml"]["max_dias"], 3)

    def test_un_flujo_sin_corridas_exitosas_nunca_cuenta_como_al_dia(self):
        """Sin éxitos manda la fecha en que el flujo llegó a la rama, no la última corrida."""
        original = g.llegada
        g.llegada = lambda nombre, rama: datetime(2020, 1, 1, tzinfo=timezone.utc)
        try:
            errores, _ = self.frescura_con(
                "fi_eeff.yml", [corrida("failure", d) for d in (1, 2, 3, 4, 5)]
            )
        finally:
            g.llegada = original
        # Sin ninguna corrida exitosa no hace falta medir estabilidad: «nunca funcionó» ya
        # es un error más fuerte que «falla la mitad de las veces».
        self.assertEqual(len(errores), 1, errores)
        self.assertIn("ninguna corrida exitosa en main", errores[0])


class DisparadoresTest(unittest.TestCase):
    """Un cambio en un publicador debe volver a correr la auditoría que lo comprueba.

    `web_audit` cruza los Parquet publicados contra el catálogo y prueba las compuertas de cada
    extractor. Si sus `on.push.paths` no incluyen la carpeta del extractor, un cambio ahí se
    publica sin que nadie vuelva a auditar la web: `fi/**` estuvo fuera de la lista.
    """

    @staticmethod
    def rutas_de_push() -> list[str]:
        import re
        flujo = (RAIZ / ".github" / "workflows" / "web_audit.yml").read_text(encoding="utf-8")
        bloque = re.search(r"^  push:$(.*?)(?=^  \S|\Z)", flujo, re.M | re.S).group(1)
        return re.findall(r"^\s*-\s*'?([\w/\.\*\[\]-]+)'?\s*$", bloque, re.M)

    def test_los_extractores_por_sector_estan_en_los_disparadores(self):
        rutas = self.rutas_de_push()
        for carpeta in ("fi/**", "ffmm/**", "macro/**", "seguros/**", "pensiones/**"):
            self.assertIn(carpeta, rutas)

    def test_el_readme_esta_en_los_disparadores(self):
        self.assertIn("README.md", self.rutas_de_push())

    def test_las_pruebas_del_guardian_y_del_contrato_estan_disparadas(self):
        rutas = self.rutas_de_push()
        for prueba in ("scripts/test_audit_automatizacion.py",
                       "scripts/test_build_metricas_publicadas.py",
                       "scripts/test_refrescar_contrato.py",
                       "scripts/refrescar_contrato.py"):
            self.assertIn(prueba, rutas)


if __name__ == "__main__":
    unittest.main()

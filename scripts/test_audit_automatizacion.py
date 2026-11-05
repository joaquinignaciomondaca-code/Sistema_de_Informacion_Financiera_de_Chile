"""Pruebas del guardián de automatización: frescura, estabilidad y cobertura de escritores.

Sin red: se sustituye la consulta a la API de GitHub por un doble que devuelve el historial
que cada caso necesita.
"""
from __future__ import annotations

import json
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

    def frescura_con(self, nombre: str, historial: list[dict],
                     arreglo: datetime | None = None) -> tuple[list[str], list[str]]:
        """Corre `frescura()` completa con un doble de la API de GitHub.

        `arreglo` fija el corte de estabilidad: por defecto es muy antiguo, para que el
        historial de cada caso cuente entero (las pruebas son anteriores al corte real).
        """
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
        original_arreglo = g.ultimo_arreglo
        g.workflows_inventariables = lambda: [(nombre, {"scripts": [], "max_dias": 16})]
        g.ultimo_arreglo = lambda n, r: arreglo if arreglo else datetime(2000, 1, 1, tzinfo=timezone.utc)
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
            g.ultimo_arreglo = original_arreglo
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

    def test_un_flujo_arreglado_no_se_juzga_por_las_corridas_anteriores_al_arreglo(self):
        """El caso real del 2026-11-05: 9 fallos viejos y el arreglo de hoy.

        `ifrs_sectores.yml` acumuló 9 fallos entre el 22 de octubre y el 4 de noviembre; el
        arreglo entró el 5 y su primera corrida salió verde. Sin corte, la compuerta semanal
        del lunes 9 habría vuelto a marcarlo como inestable y a comentar el issue #24 con un
        diagnóstico sobre código que ya no existe. Con corte, el veredicto es «todavía no hay
        con qué juzgar»: una sola corrida posterior al arreglo no alcanza el mínimo de cuatro.
        """
        historial = [corrida("success", 0.02)] + [
            corrida("failure", d) for d in (1, 2, 3.5, 5, 6.5, 8, 9.5, 11, 12.5)
        ]
        errores, _ = self.frescura_con(
            "ifrs_sectores.yml", historial, arreglo=datetime.now(timezone.utc) - timedelta(hours=6)
        )
        self.assertEqual(errores, [])

    def test_si_vuelve_a_fallar_despues_del_arreglo_se_reporta_igual(self):
        """El corte no compra un perdón: lo que falla después del arreglo cuenta entero.

        Mismo historial que el caso anterior, pero el flujo vuelve a fallar tras la corrección.
        Ahí sí hay señal —4 de 5 corridas posteriores fallidas— y la compuerta tiene que decirla.
        """
        historial = [
            corrida("failure", 0.02), corrida("failure", 0.06),
            corrida("failure", 0.1), corrida("failure", 0.14), corrida("success", 0.18),
        ] + [corrida("failure", d) for d in (2, 3.5, 5, 6.5, 8)]
        errores, _ = self.frescura_con(
            "ifrs_sectores.yml", historial, arreglo=datetime.now(timezone.utc) - timedelta(hours=8)
        )
        self.assertEqual(len(errores), 1, errores)
        self.assertIn("4 de sus últimas 5 corridas fallaron", errores[0])

    def test_el_corte_incluye_los_scripts_del_inventario(self):
        """El arreglo casi nunca está en el YAML: en `ifrs_sectores` estuvo en `actualizar.py`.

        Se comprueba sobre git de verdad: se toca el extractor y la fecha del corte tiene que
        moverse a ese commit. Si `ultimo_arreglo` mirara solo el workflow, un arreglo en el
        script dejaría el historial viejo condenando al flujo durante semanas.
        """
        import subprocess
        from tempfile import TemporaryDirectory
        import os
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args, fecha="2026-01-01T00:00:00+00:00"):
                entorno = {**os.environ, "GIT_AUTHOR_DATE": fecha, "GIT_COMMITTER_DATE": fecha,
                           "GIT_AUTHOR_NAME": "prueba", "GIT_AUTHOR_EMAIL": "p@e",
                           "GIT_COMMITTER_NAME": "prueba", "GIT_COMMITTER_EMAIL": "p@e"}
                subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                               env=entorno)

            (repo / ".github" / "workflows").mkdir(parents=True)
            (repo / "pipelines" / "ifrs_sectores").mkdir(parents=True)
            (repo / "pipelines" / "auto").mkdir(parents=True)
            git("init", "-q")
            (repo / ".github" / "workflows" / "ifrs_sectores.yml").write_text("on: push\n")
            (repo / "pipelines" / "ifrs_sectores" / "actualizar.py").write_text("# v1\n")
            (repo / "pipelines" / "auto" / "inventario.json").write_text(json.dumps({
                "tablas": [], "workflows": {"ifrs_sectores.yml": {
                    "scripts": ["pipelines/ifrs_sectores/actualizar.py"], "max_dias": 16}}
            }))
            git("add", "-A"); git("commit", "-qm", "inicial", fecha="2026-01-01T00:00:00+00:00")
            # El arreglo: solo el script, nada del YAML.
            (repo / "pipelines" / "ifrs_sectores" / "actualizar.py").write_text("# v2 arreglado\n")
            git("add", "-A"); git("commit", "-qm", "arreglo", fecha="2026-03-15T12:00:00+00:00")

            original = (g.RAIZ, g.INVENTARIO)
            g.RAIZ, g.INVENTARIO = repo, repo / "pipelines" / "auto" / "inventario.json"
            try:
                corte = g.ultimo_arreglo("ifrs_sectores.yml", "main")
            finally:
                g.RAIZ, g.INVENTARIO = original
        self.assertIsNotNone(corte)
        self.assertEqual((corte.year, corte.month, corte.day), (2026, 3, 15))

    def test_un_commit_de_campana_no_reinicia_el_reloj(self):
        """El 2026-11-04 un commit tocó 17 workflows y no arregló ninguno en particular.

        Si contara como «arreglo», el corte se movería para toda la flota a la vez y la
        compuerta quedaría ciega justo cuando hay que mirarla. Se ignora y se sigue hacia
        atrás hasta el último cambio que tocó este flujo y no los diecisiete.
        """
        import subprocess
        from tempfile import TemporaryDirectory
        import os
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args, fecha="2026-01-01T00:00:00+00:00"):
                entorno = {**os.environ, "GIT_AUTHOR_DATE": fecha, "GIT_COMMITTER_DATE": fecha,
                           "GIT_AUTHOR_NAME": "p", "GIT_AUTHOR_EMAIL": "p@e",
                           "GIT_COMMITTER_NAME": "p", "GIT_COMMITTER_EMAIL": "p@e"}
                subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                               env=entorno)

            wfs = repo / ".github" / "workflows"
            wfs.mkdir(parents=True)
            git("init", "-q")
            # Arreglo específico del flujo, el 1 de marzo.
            (wfs / "macro.yml").write_text("on: push\n")
            git("add", "-A"); git("commit", "-qm", "arreglo real",
                                  fecha="2026-03-01T00:00:00+00:00")
            # Campaña: el mismo flujo y otros cuatro, el 1 de abril.
            for i in range(3):
                (wfs / f"otro{i}.yml").write_text("on: push\n")
            (wfs / "macro.yml").write_text("on: push\nruns-on: x\n")
            (wfs / "quinto.yml").write_text("on: push\n")
            git("add", "-A"); git("commit", "-qm", "campaña",
                                  fecha="2026-04-01T00:00:00+00:00")

            original = (g.RAIZ, g.INVENTARIO)
            g.RAIZ, g.INVENTARIO = repo, repo / "no-existe.json"  # inventario ilegible: sin scripts
            try:
                corte = g.ultimo_arreglo("macro.yml", "main")
            finally:
                g.RAIZ, g.INVENTARIO = original
        self.assertIsNotNone(corte)
        self.assertEqual((corte.year, corte.month, corte.day), (2026, 3, 1),
                         "la campaña del 1 de abril no debe contar como arreglo")

    def test_sin_historial_no_se_recorta_nada(self):
        """Sin git (un artefacto, un tarball) se juzga el historial completo: conservador."""
        historial = [
            corrida("failure", 0.1), corrida("success", 0.2), corrida("failure", 0.4),
            corrida("failure", 0.6), corrida("failure", 0.8), corrida("success", 1.0),
        ]
        errores, _ = self.frescura_con("contrato_publicado.yml", historial, arreglo=None)
        self.assertEqual(len(errores), 1, errores)


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
        rutas = self.rutas_de_push()
        self.assertIn("README.md", rutas)
        # `fi/README.md` describe las reglas de publicación y queda cubierto por `fi/**`;
        # se comprueba el patrón, no una ruta redundante en la lista.
        self.assertTrue({"fi/**", "fi/README.md"} & set(rutas))

    # Etiquetas admitidas. `ubuntu-latest` NO está: cambia de imagen sola (Ubuntu 24.04 →
    # 26.04 entre el 2026-10-19 y el 2026-11-19, actions/runner-images#14748), así que la
    # misma corrida puede caer en una imagen u otra sin que cambie una línea del repo.
    ETIQUETAS_FIJAS = {"ubuntu-24.04", "ubuntu-22.04", "ubuntu-26.04"}

    def test_ningun_flujo_usa_la_etiqueta_movil_ubuntu_latest(self):
        """Ningún job, publique o no, puede correr sobre una etiqueta móvil.

        La versión anterior de esta prueba solo miraba los flujos que escriben en `main`
        (`git push` o `contents: write`). Por eso no vio que `web_audit.yml` seguía en
        `ubuntu-latest` en **seis de sus siete jobs**: al no publicar, quedaba fuera del
        filtro. Y es el flujo que más importa, porque es la compuerta que avisa cuando un
        publicador se atasca: un `fail` intermitente suyo —que es exactamente lo que produce
        una imagen que cambia sola— tapa los fallos reales.

        El riesgo no es solo de los publicadores. Cualquier job intermitente gasta corridas
        y credibilidad, y el que decide si el lunes hay issue abierto es este.
        """
        import re
        culpables = []
        for flujo in sorted((RAIZ / ".github" / "workflows").glob("*.yml")):
            texto = flujo.read_text(encoding="utf-8")
            # Las menciones en comentarios no cuentan: se mira solo la línea de `runs-on`.
            for etiqueta in re.findall(r"^\s*runs-on:\s*(\S+)\s*$", texto, re.M):
                if etiqueta == "ubuntu-latest":
                    culpables.append(flujo.name)
                elif etiqueta.startswith("ubuntu-") and etiqueta not in self.ETIQUETAS_FIJAS:
                    culpables.append(f"{flujo.name} ({etiqueta})")
        self.assertEqual(culpables, [], "jobs con etiqueta de runner móvil o desconocida")

    def test_r_ejemplos_sigue_en_ubuntu_22_04_a_proposito(self):
        """`r_ejemplos` instala `duckdb` para R desde el binario de Posit, que va por `jammy`.

        Si alguien «moderniza» este job a 24.04 en una campaña de etiquetas, R puede caer a
        compilar desde fuente; el paso lo detecta y falla, pero el fallo aparecería lejos de
        su causa. Se deja escrito para que el cambio sea una decisión, no un descuido.
        """
        import re
        flujo = (RAIZ / ".github" / "workflows" / "web_audit.yml").read_text(encoding="utf-8")
        bloque = flujo[flujo.index("\n  r_ejemplos:"):]
        bloque = bloque[:bloque.index("\n  automatizacion:")]
        self.assertRegex(bloque, r"runs-on:\s*ubuntu-22\.04")
        self.assertIn("jammy", bloque)

    def test_la_compuerta_que_avisa_no_es_ella_misma_intermitente(self):
        """El job `frescura` decide si el issue se abre o se cierra: su imagen no puede moverse.

        Si `frescura` falla por la imagen, el issue no se cierra nunca —el caso que motivó
        el #24— y si falla el job `audit`, el rojo tapa los datos. Los dos van fijados.
        """
        import re
        flujo = (RAIZ / ".github" / "workflows" / "web_audit.yml").read_text(encoding="utf-8")
        for job in ("audit", "frescura"):
            bloque = flujo[flujo.index(f"\n  {job}:"):]
            bloque = bloque[:bloque.index("\n  r_ejemplos:")] if job == "audit" else bloque
            self.assertRegex(bloque, r"runs-on:\s*ubuntu-24\.04",
                             f"{job} debe correr en una imagen fija")

    def test_las_pruebas_del_guardian_y_del_contrato_estan_disparadas(self):
        rutas = self.rutas_de_push()
        for prueba in ("scripts/test_audit_automatizacion.py",
                       "scripts/test_build_metricas_publicadas.py",
                       "scripts/test_refrescar_contrato.py",
                       "scripts/refrescar_contrato.py"):
            self.assertIn(prueba, rutas)


if __name__ == "__main__":
    unittest.main()

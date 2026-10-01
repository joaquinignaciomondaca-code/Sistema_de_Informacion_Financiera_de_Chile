"""Guardia del contrato de publicación en la rama (pipelines/auto/README.md).

Varios workflows escriben en la misma rama y arrancan a la vez. Los archivos compartidos
(`data_manifest.json`, `docs/index.html`, los catálogos `docs/js/*.js`) los edita cualquiera, así
que NO pueden viajar en el commit de datos de un publicador: si otro los reescribe entre medio, el
`cherry-pick`/`rebase` choca y reintentar no lo arregla (así quedaron sin publicar factoring/leasing
y banca). Se regeneran sobre la cabeza vigente: `reset --hard FETCH_HEAD` y, después, un comando
`--solo-…` del propio publicador o el generador del catálogo.

Esta prueba lee el texto de los workflows (sin dependencias) y exige exactamente eso: todo `git add`
que nombre un archivo compartido tiene que ir precedido, en el mismo paso, de `git reset --hard
FETCH_HEAD` y de un regenerador entre ese reset y el `git add`.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
WORKFLOWS = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
COMPARTIDOS = ("data_manifest.json", "docs/index.html", "docs/js/")
REGENERADORES = ("--solo-", "build_download_catalog.py")


def logicas(texto: str) -> list[tuple[int, str]]:
    """Líneas del workflow con las continuaciones «\\» unidas: (posición en el texto, línea)."""
    salida, acumulado, inicio, pos = [], "", 0, 0
    for linea in texto.splitlines(keepends=True):
        limpia = linea.rstrip("\n")
        if not acumulado:
            inicio = pos
        acumulado += limpia.rstrip("\\").strip() + " " if limpia.rstrip().endswith("\\") else limpia.strip()
        if not limpia.rstrip().endswith("\\"):
            salida.append((inicio, acumulado))
            acumulado = ""
        pos += len(linea)
    return salida


def paso_de(texto: str, pos: int) -> tuple[int, int]:
    """Límites del paso (`- name:` … siguiente `- name:`) que contiene la posición."""
    inicios = [m.start() for m in re.finditer(r"^\s*- (?:name|uses):", texto, re.M)] + [len(texto)]
    for a, b in zip(inicios, inicios[1:]):
        if a <= pos < b:
            return a, b
    return 0, len(texto)


class ContratoDePublicadoresTest(unittest.TestCase):
    def test_hay_workflows_que_revisar(self):
        self.assertGreaterEqual(len(WORKFLOWS), 10)

    def test_los_archivos_compartidos_se_regeneran_sobre_la_cabeza_no_viajan_en_el_commit(self):
        problemas = []
        for wf in WORKFLOWS:
            texto = wf.read_text(encoding="utf-8")
            for pos, linea in logicas(texto):
                if not linea.startswith("git add ") or not any(c in linea for c in COMPARTIDOS):
                    continue
                a, _b = paso_de(texto, pos)
                previo = texto[a:pos]
                reset = previo.rfind("git reset --hard FETCH_HEAD")
                regenera = max((previo.rfind(r) for r in REGENERADORES), default=-1)
                if reset < 0 or regenera < reset:
                    problemas.append(f"{wf.name}: «{linea[:110]}» agrega archivos compartidos sin haberlos "
                                     "regenerado sobre la cabeza (falta reset --hard FETCH_HEAD y un --solo-…/"
                                     "build_download_catalog después)")
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_las_listas_de_rutas_del_commit_de_datos_no_incluyen_archivos_compartidos(self):
        problemas = []
        for wf in WORKFLOWS:
            for _pos, linea in logicas(wf.read_text(encoding="utf-8")):
                if re.match(r'rutas="', linea) and any(c in linea for c in COMPARTIDOS):
                    problemas.append(f"{wf.name}: {linea[:140]}")
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_la_guardia_detecta_el_patron_que_fallaba(self):
        """El paso antiguo de banca (commit con data_manifest.json y rebase) debe ser rechazado."""
        antiguo = ('      - name: Confirmar\n        run: |\n          git add data_manifest.json docs/outputs/bancos/cmf_b1_b2_r1\n'
                   '          git commit -m x\n          git fetch origin main\n          git rebase FETCH_HEAD\n')
        pos, linea = next((p, l) for p, l in logicas(antiguo) if l.startswith("git add "))
        a, _ = paso_de(antiguo, pos)
        previo = antiguo[a:pos]
        self.assertTrue(any(c in linea for c in COMPARTIDOS))
        self.assertLess(previo.rfind("git reset --hard FETCH_HEAD"), 0)

    def test_las_continuaciones_con_barra_se_unen(self):
        texto = "git add a.json \\\n        docs/js/x.js \\\n        data_manifest.json\necho listo\n"
        self.assertEqual([l for _p, l in logicas(texto)], ["git add a.json docs/js/x.js data_manifest.json", "echo listo"])


if __name__ == "__main__":
    unittest.main()

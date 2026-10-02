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

import ast
import fnmatch
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




# ---------------------------------------------------------------------------
# Tres guardianes que nacieron de la revisión de la automatización del 2026-10-02. Cada uno
# describe un defecto que estaba presente: publicar sin probar, matar la corrida antes de que se
# agote su propio presupuesto de tiempo y dejar de disparar un publicador al cambiar un módulo
# compartido que sí afecta lo que escribe.

def bloques_de_jobs(texto: str) -> list[tuple[str, str]]:
    """(nombre, cuerpo) de cada job declarado bajo `jobs:` (indentación de dos espacios)."""
    lineas = texto.splitlines()
    inicio = next((i for i, l in enumerate(lineas) if l.rstrip() == "jobs:"), None)
    if inicio is None:
        return []
    salida, nombre, cuerpo = [], None, []
    for linea in lineas[inicio + 1:]:
        if linea.strip() and not linea.startswith("  "):
            break
        if re.match(r"^  [\w-]+:\s*$", linea):
            if nombre:
                salida.append((nombre, "\n".join(cuerpo)))
            nombre, cuerpo = linea.strip()[:-1], []
        elif nombre is not None:
            cuerpo.append(linea)
    if nombre:
        salida.append((nombre, "\n".join(cuerpo)))
    return salida


def rutas_de_push(texto: str) -> set[str]:
    """Archivos concretos declarados en `on.push.paths` (los comodines se revisan aparte)."""
    bloque = re.search(r"^  push:$(.*?)(?=^  \S|\Z)", texto, re.M | re.S)
    if not bloque:
        return set()
    return {r for r in re.findall(r"^\s*-\s*'?([\w/\.\-]+\.py)'?\s*$", bloque.group(1), re.M)}


def comodines_de_push(texto: str) -> list[str]:
    bloque = re.search(r"^  push:$(.*?)(?=^  \S|\Z)", texto, re.M | re.S)
    if not bloque:
        return []
    return re.findall(r"^\s*-\s*'?([\w/\.\-\*\[\]]+\*)'?\s*$", bloque.group(1), re.M)


def cubierto_por_comodin(ruta: str, patrones: list[str]) -> bool:
    return any(fnmatch.fnmatch(ruta, p.replace("**", "*")) for p in patrones)


def compartidos_importados(rel: str, vistos: set[str]) -> set[str]:
    """`pipelines/auto/*.py` que un archivo importa en cascada, leyéndolo con `ast` (sin ejecutar)."""
    if rel in vistos:
        return set()
    vistos.add(rel)
    archivo = RAIZ / rel
    if not archivo.exists():
        return set()
    salida: set[str] = set()
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres = [m.name for m in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and (nodo.module or "").startswith("pipelines.auto"):
            if (nodo.module or "") == "pipelines.auto":
                nombres = [f"pipelines.auto.{m.name}" for m in nodo.names]
            else:
                nombres = [nodo.module] + [f"{nodo.module}.{m.name}" for m in nodo.names]
        else:
            continue
        for imp in nombres:
            if not imp.startswith("pipelines.auto."):
                continue
            destino = "pipelines/auto/" + imp[len("pipelines.auto."):].replace(".", "/") + ".py"
            if not (RAIZ / destino).exists():
                continue
            salida.add(destino)
            salida |= compartidos_importados(destino, vistos)
    return salida


def pasos(texto: str) -> list[str]:
    """Cuerpo de cada paso (`- name:` / `- uses:` hasta el siguiente)."""
    inicios = [m.start() for m in re.finditer(r"^\s*- (?:name|uses):", texto, re.M)] + [len(texto)]
    return [texto[a:b] for a, b in zip(inicios, inicios[1:])]


def bloque_env(paso: str) -> str:
    """Las líneas del `env:` de un paso (lo que ahí aparece nombra variables, no ejecuta nada)."""
    m = re.search(r"^(\s*)env:\s*$", paso, re.M)
    if not m:
        return ""
    sangria, salida = len(m.group(1)), []
    for linea in paso[m.end():].splitlines(keepends=True):
        if not linea.strip():
            continue
        if len(linea) - len(linea.lstrip()) <= sangria:
            break
        salida.append(linea)
    return "".join(salida)


def input_consumido(texto: str, nombre: str) -> bool:
    """¿El input llega a un comando? Vale directo (`${{ inputs.x }}` en run/with/if) o por la
    variable que el paso declara en su `env:` —que es la forma en que todos los publicadores lo
    pasan—, pero no un `env:` que luego nadie lee: eso es una perilla decorativa."""
    for paso in pasos(texto):
        if f"inputs.{nombre}" not in paso:
            continue
        fuera = paso.replace(bloque_env(paso), "")
        if f"inputs.{nombre}" in fuera:
            return True
        claves = re.findall(rf"([A-Z_][A-Z0-9_]*):\s*.*inputs\.{nombre}", bloque_env(paso))
        if any(re.search(rf"\$\{{?{clave}\b", fuera) for clave in claves):
            return True
    return False



class GuardiaDeFlujosTest(unittest.TestCase):
    """Reglas que se leen del texto de los workflows; no requieren red ni dependencias."""

    def test_todo_publicador_prueba_antes_de_escribir_en_la_rama(self):
        """Un workflow que hace `git commit` debe invocar pruebas: en el schedule no hay otro job que las corra."""
        problemas = []
        for wf in WORKFLOWS:
            texto = wf.read_text(encoding="utf-8")
            if "git commit" not in texto:
                continue
            prueba = re.search(r"python -m unittest\b|python -m pytest\b|python -m [\w.]+\.tests\.", texto)
            if not prueba:
                problemas.append(f"{wf.name}: publica con `git commit` pero no ejecuta ninguna prueba "
                                 "(web_audit sólo las corre en push/pull_request; la corrida programada no)")
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_el_tope_del_job_no_corta_el_presupuesto_de_minutos(self):
        """`--minutos N` promete N minutos de corrida: el `timeout-minutes` del job debe cubrirlo."""
        problemas = []
        for wf in WORKFLOWS:
            for nombre, cuerpo in bloques_de_jobs(wf.read_text(encoding="utf-8")):
                tope = re.search(r"timeout-minutes:\s*(\d+)", cuerpo)
                presupuestos = [int(x) for x in re.findall(r'--minutos\s*"?\$\{MINUTOS:-(\d+)\}', cuerpo)]
                presupuestos += [int(x) for x in re.findall(r"--minutos (\d+)", cuerpo)]
                presupuestos += [int(x) for x in re.findall(r"MINUTOS=(\d+)", cuerpo)]
                if not tope or not presupuestos:
                    continue
                if max(presupuestos) > int(tope.group(1)):
                    problemas.append(f"{wf.name}: job {nombre!r} se autolimita a {max(presupuestos)} min "
                                     f"pero el tope del job es {tope.group(1)} min (la corrida muere sin publicar)")
                if int(tope.group(1)) > 360:
                    problemas.append(f"{wf.name}: job {nombre!r} pide {tope.group(1)} min, más de las 6 h "
                                     "que tolera un job de GitHub Actions")
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_todo_modulo_compartido_importado_por_un_disparador_esta_en_los_paths(self):
        """Si el publicador importa `pipelines/auto/X`, un cambio en X debe volver a probarlo y publicarlo."""
        problemas = []
        for wf in WORKFLOWS:
            texto = wf.read_text(encoding="utf-8")
            entradas, comodines = rutas_de_push(texto), comodines_de_push(texto)
            vistos: set[str] = set()
            requeridos: set[str] = set()
            for entrada in sorted(entradas):
                requeridos |= compartidos_importados(entrada, vistos)
            faltan = sorted(r for r in requeridos - entradas if not cubierto_por_comodin(r, comodines))
            if faltan:
                problemas.append(f"{wf.name}: sus `on.push.paths` no incluyen {', '.join(faltan)}, que sí "
                                 "importan los archivos declarados (un cambio ahí no vuelve a correr el flujo)")
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_todo_input_de_workflow_dispatch_llega_a_un_comando(self):
        """Un input que sólo aparece en `env:` es una perilla decorativa: la pantalla de Run workflow promete algo que no ocurre."""
        problemas = []
        for wf in WORKFLOWS:
            texto = wf.read_text(encoding="utf-8")
            bloque = re.search(r"^  workflow_dispatch:\n(?:    inputs:\n((?:      [\w-]+:\n(?:        .*\n)*?)+))?",
                               texto, re.M)
            for nombre in re.findall(r"^      ([\w-]+):$", bloque.group(1) or "", re.M) if bloque else []:
                if not input_consumido(texto, nombre):
                    problemas.append(f"{wf.name}: el input {nombre!r} de workflow_dispatch no llega a ningún "
                                     "comando (aparece a lo sumo en un `env:`, que por sí solo no hace nada)")
        self.assertEqual(problemas, [], "\n".join(problemas))


if __name__ == "__main__":
    unittest.main()

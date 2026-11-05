#!/usr/bin/env python3
"""Guardián de automatización: ninguna tabla publicada puede quedar como «foto fija» sin aviso.

Inventario: pipelines/auto/inventario.json declara, para CADA tabla de data_manifest.json, qué
workflow y qué script la actualizan, o si el flujo es híbrido/manual y cuál es su motivo.

Revisión estática (en cada push, sin red):
  1. toda tabla de data_manifest.json y toda vista del sitio (SEMANTIC_VIEWS de
     docs/js/duckdb_client.js) está en el inventario (una tabla nueva sin automatizar falla);
  2. el workflow existe, tiene horario (cron) y ejecuta el script declarado;
  3. el script (o los que declara) nombra el archivo publicado de la tabla (o la «marca» declarada
     cuando arma el nombre por partes);
  4. el texto «modo» que muestra la web coincide con la modalidad del inventario:
     «Automático», «Híbrido» o «Manual».

Un flujo híbrido no se trata como una tabla automática: exige declarar los scripts reproducibles
que validan/compilan el resultado, pero no exige un workflow programado. Así se distingue la
automatización del procesamiento de la automatización de su orquestación.

Revisión de frescura (--frescura, semanal en Actions, requiere GH_TOKEN y la rama por defecto):
  5. cada workflow del inventario tuvo una corrida exitosa en los últimos `max_dias` días.
     Si no, falla (y el workflow abre un issue).
  6. los publicadores que escriben en la rama sin producir tablas del manifiesto
     (`FLUJOS_DE_ESCRITURA`: el contrato derivado y los EEFF de fondos de inversión) se
     revisan con el mismo criterio que los del inventario. `fi_eeff.yml` pasó 33 días en
     rojo sin que esta compuerta lo dijera, porque sus tablas ya estaban inventariadas y el
     flujo no.
  7. ningún workflow puede fallar más de la mitad de sus últimas corridas terminadas: tener
     «una corrida exitosa reciente» no es estar sano. El 2026-11-04 `contrato_publicado.yml`
     fallaba 4 de cada 6 corridas y el guardián solo miraba la última exitosa.
  8. pero un flujo **arreglado** no se juzga por las corridas anteriores al arreglo. La regla 7
     mira las últimas N corridas terminadas sin ventana de tiempo, así que, tras corregir la
     causa, el historial viejo sigue condenando al flujo durante semanas: el 2026-11-05
     `ifrs_sectores.yml` llevaba 9 fallos consecutivos (del 22 de octubre al 4 de noviembre,
     antes del arreglo) y la compuerta semanal lo habría vuelto a marcar el lunes 9. Un
     diagnóstico sobre corridas que ya no existen no protege a nadie y entierra el issue en
     ruido. El corte es automático: la fecha del último commit que tocó el flujo o los scripts
     que el inventario le asocia. A partir de ahí se vuelve a medir; si el flujo falla otra vez
     después del arreglo, se reporta igual. Un arreglo no compra un perdón: compra que se juzgue
     lo que vino después.

Uso:  python scripts/audit_automatizacion.py [--frescura --repo dueño/repo --rama main]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INVENTARIO = RAIZ / "pipelines" / "auto" / "inventario.json"
VOCABULARIO = RAIZ / "docs" / "vocabulario.json"

try:  # la verificación de filas necesita leer los pies de los Parquet
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover
    pq = None


def canonico() -> dict[str, str]:
    """Los pipelines publican con los ids históricos de data_manifest.json.

    El vocabulario (docs/vocabulario.json) es la autoridad de nombres: declara
    esos ids como alias de la tabla canónica, así que aquí se traducen para
    poder cruzar manifiesto, inventario y vistas del sitio.
    """
    mapa: dict[str, str] = {}
    for tabla in json.loads(VOCABULARIO.read_text(encoding="utf-8"))["tablas"]:
        mapa[tabla["id"]] = tabla["id"]
        for alias in tabla.get("alias", []):
            mapa[alias] = tabla["id"]
    return mapa


def _sin_tildes(texto: object) -> str:
    """Normaliza las etiquetas de modalidad para comparar sin depender de la tilde."""
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().split())


def modalidad_web(modo: object) -> str | None:
    """Devuelve la modalidad declarada por el texto visible en la web."""
    normalizado = _sin_tildes(modo)
    if normalizado.startswith("hibrido"):
        return "hibrido"
    if normalizado.startswith("manual"):
        return "manual"
    if normalizado.startswith("automatico") or "automatico" in normalizado:
        return "automatico"
    return None


def scripts_hibridos(entrada: dict, tabla: dict, errores: list[str]) -> None:
    """Valida la parte reproducible de una entrada híbrida sin exigir Actions."""
    rutas = entrada.get("scripts")
    if not isinstance(rutas, list) or not rutas:
        errores.append(f"{tabla['id']}: híbrida sin scripts reproducibles declarados")
        return
    textos = []
    for ruta_relativa in rutas:
        ruta = RAIZ / str(ruta_relativa)
        if not ruta.exists():
            errores.append(f"{tabla['id']}: script híbrido inexistente: {ruta_relativa}")
            continue
        textos.append(ruta.read_text(encoding="utf-8", errors="ignore"))
    if not textos:
        return
    fuente = "".join(textos)
    base = Path(tabla["file_parquet"]).stem
    if base == "manifest":
        base = Path(tabla["file_parquet"]).parent.name
    if tabla["id"] not in fuente and base not in fuente:
        errores.append(f"{tabla['id']}: ningún script híbrido nombra «{base}» (no la compila)")


def modalidad_especial(entrada: dict) -> str | None:
    """Identifica entradas que no dependen de un workflow programado."""
    claves = [clave for clave in ("hibrido", "manual") if clave in entrada]
    return claves[0] if len(claves) == 1 else ("conflicto" if claves else None)


def estatica() -> list[str]:
    errores = []
    inv = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    tablas_inv, flujos = inv["tablas"], inv["workflows"]
    man = json.loads((RAIZ / "data_manifest.json").read_text(encoding="utf-8"))
    id_canonico = canonico()
    canon_de = lambda tid: id_canonico.get(tid, tid)
    ids = {canon_de(t["id"]) for t in man["tables"]}
    for t in man["tables"]:
        e = tablas_inv.get(canon_de(t["id"]))
        modalidad = modalidad_web(t.get("modo"))
        if e is None:
            errores.append(f"{t['id']}: no está en pipelines/auto/inventario.json (¿quién la actualiza?)")
            continue
        especial = modalidad_especial(e)
        if especial == "conflicto":
            errores.append(f"{t['id']}: inventario mezcla hibrido y manual")
            continue
        if especial in {"hibrido", "manual"}:
            motivo = e.get(especial)
            if not str(motivo or "").strip():
                errores.append(f"{t['id']}: {especial} sin motivo")
            if modalidad != especial:
                errores.append(f"{t['id']}: es {especial} pero la web dice «{t.get('modo')}»")
            if especial == "hibrido":
                scripts_hibridos(e, t, errores)
            continue
        if modalidad != "automatico":
            errores.append(f"{t['id']}: está automatizada pero la web no dice «Automático»: «{t.get('modo')}»")
        wf = flujos.get(e.get("workflow"))
        if wf is None:
            errores.append(f"{t['id']}: workflow {e.get('workflow')!r} no declarado en el inventario")
            continue
        base = Path(t["file_parquet"]).name.replace(".parquet", "")
        if base == "manifest.json":  # tabla particionada: se identifica por su carpeta
            base = Path(t["file_parquet"]).parent.name
        base = e.get("marca") or base  # el script arma el nombre por partes
        textos = "".join((RAIZ / s).read_text(encoding="utf-8", errors="ignore")
                         for s in wf["scripts"] if (RAIZ / s).exists())
        if base not in textos:
            errores.append(f"{t['id']}: ningún script de {e['workflow']} nombra «{base}» (no la escribe)")
    for nombre, wf in flujos.items():
        ruta = RAIZ / ".github" / "workflows" / nombre
        if not ruta.exists():
            errores.append(f"workflow {nombre}: no existe")
            continue
        y = ruta.read_text(encoding="utf-8")
        if not re.search(r"^\s*-\s*cron:", y, re.M):
            errores.append(f"workflow {nombre}: sin horario (cron)")
        for s in wf["scripts"]:
            if not (RAIZ / s).exists():
                errores.append(f"workflow {nombre}: el script {s} no existe")
            modulo = s.removesuffix(".py").replace("/", ".")
            if s not in y and modulo not in y and not wf.get("scripts_indirectos"):
                errores.append(f"workflow {nombre}: no ejecuta {s}")
    # El sitio lee sus tablas de SEMANTIC_VIEWS (docs/js/duckdb_client.js), no solo de data_manifest:
    # cada vista debe corresponder a una tabla inventariada (por nombre o por archivo).
    por_archivo = {t["file_parquet"]: canon_de(t["id"]) for t in man["tables"]}
    vistas = vistas_web()
    for nombre, ruta in vistas.items():
        tid = nombre if nombre in tablas_inv else por_archivo.get(ruta)
        e = tablas_inv.get(tid) if tid else None
        if e is None:
            errores.append(f"vista web {nombre} ({ruta}): no está en pipelines/auto/inventario.json (¿quién la actualiza?)")
            continue
        if tid in ids or modalidad_especial(e) in {"hibrido", "manual"}:
            continue  # ya revisada arriba
        wf = flujos.get(e.get("workflow"))
        if wf is None:
            errores.append(f"vista web {nombre}: workflow {e.get('workflow')!r} no declarado en el inventario")
            continue
        base = e.get("marca") or (Path(ruta).parent.name if ruta.endswith("manifest.json") else Path(ruta).stem)
        textos = "".join((RAIZ / s).read_text(encoding="utf-8", errors="ignore") for s in wf["scripts"] if (RAIZ / s).exists())
        if base not in textos:
            errores.append(f"vista web {nombre}: ningún script de {e['workflow']} nombra «{base}» (no la escribe)")
    for tid in set(tablas_inv) - ids - set(vistas):
        errores.append(f"inventario: {tid} ya no existe en data_manifest.json ni en el sitio (quitarla)")
    return errores + alineacion_manifest(vistas)


# Datasetes fuente publicados sin vista directa en el sitio. La fuente bancaria
# completa se conserva como respaldo de extracción; las vistas semánticas y sus
# descargas se materializan en particiones filtradas separadas.
DATASETS_SIN_VISTA = {
    "bancos_cmf_lineas": "fuente CMF completa; las vistas balance y resultados se publican en particiones filtradas propias",
}
# Los Parquet semánticos se materializan desde una fuente cruda común. Sus rutas
# ya no son las del manifiesto fuente, pero siguen cubiertas por su publicación.
VISTAS_DESDE_DATASET = {
    "bancos_balance": "bancos_cmf_lineas",
    "bancos_resultados": "bancos_cmf_lineas",
}


def _registros_de(tabla: dict, raiz: Path) -> int | None:
    """Filas reales que declaran los archivos de una entrada del manifiesto."""
    ref = tabla.get("files_manifest") or tabla.get("file_parquet") or ""
    if ref.endswith(".json"):
        man = raiz / "docs" / ref
        if not man.exists():
            return None
        data = json.loads(man.read_text(encoding="utf-8"))
        archivos = data.get("files", [])
    else:
        archivos = [ref]
    total = 0
    for rel in archivos:
        ruta = raiz / "docs" / rel
        if not ruta.exists():
            return None
        total += int(pq.ParquetFile(ruta).metadata.num_rows)
    return total


def alineacion_manifest(vistas: dict[str, str]) -> list[str]:
    """data_manifest.json debe alinearse con lo publicado, no con el historial.

    * total_tables/total_records consistentes con la lista;
    * el `registros_reales` de cada entrada igual a las filas de sus archivos
      (detecta la deriva de conteo: una vez quedaron 127 filas fuera);
    * cada id del manifiesto corresponde a una vista del sitio (o a un
      datasete sin vista documentado) y viceversa: cada vista tiene entrada.
    """
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return ["alineación data_manifest: falta pyarrow (pip install pyarrow) para verificar las filas"]
    raiz = RAIZ
    errores: list[str] = []
    man = json.loads((raiz / "data_manifest.json").read_text(encoding="utf-8"))
    tablas = man.get("tables", [])
    if man.get("total_tables") != len(tablas):
        errores.append(f"data_manifest.json: total_tables={man.get('total_tables')} pero hay {len(tablas)} entradas")
    suma = sum(int(t.get("registros_reales") or 0) for t in tablas)
    if man.get("total_records") != suma:
        errores.append(f"data_manifest.json: total_records={man.get('total_records'):,} pero las entradas suman {suma:,}")
    canon_de = lambda tid: canonico().get(tid, tid)
    ids_manifiesto = {canon_de(t["id"]) for t in tablas}
    por_archivo: dict[str, str] = {}
    for t in tablas:
        ref = t.get("files_manifest") or t.get("file_parquet") or ""
        if ref:
            por_archivo[ref] = canon_de(t["id"])
        real = _registros_de(t, raiz)
        if real is None:
            errores.append(f"data_manifest.json {t['id']}: los archivos declarados no existen en docs/")
        elif real != int(t.get("registros_reales") or 0):
            errores.append(f"data_manifest.json {t['id']}: declara {t.get('registros_reales'):,} filas pero sus archivos traen {real:,}")
        if canon_de(t["id"]) not in vistas and t["id"] not in DATASETS_SIN_VISTA:
            errores.append(f"data_manifest.json {t['id']}: no corresponde a ninguna vista del sitio")
    for vista, ruta in vistas.items():
        cubre = por_archivo.get(ruta)
        fuente_compartida = VISTAS_DESDE_DATASET.get(vista)
        if (vista not in ids_manifiesto
                and cubre not in (vista, *DATASETS_SIN_VISTA)
                and fuente_compartida not in ids_manifiesto):
            errores.append(f"vista {vista}: sin entrada en data_manifest.json (¿quién la cuenta?)")
    return errores


def vistas_web() -> dict[str, str]:
    s = (RAIZ / "docs" / "js" / "duckdb_client.js").read_text(encoding="utf-8")
    i = s.index("const SEMANTIC_VIEWS = [")
    j = s.index("\n];", i)
    return {n: r for n, _, r in re.findall(r'name:\s*"([^"]+)"\s*,\s*(file|manifest):\s*"([^"]+)"', s[i:j])}


def llegada(nombre: str, rama: str) -> datetime | None:
    """Fecha en que el workflow llegó a la rama (primer commit de primer padre que lo trae)."""
    import subprocess
    for ref in (f"origin/{rama}", rama, "HEAD"):
        r = subprocess.run(["git", "log", "--first-parent", "--format=%cI", ref, "--", f".github/workflows/{nombre}"],
                           cwd=RAIZ, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return datetime.fromisoformat(r.stdout.strip().splitlines()[-1])
    return None


# Un commit que barre más workflows que esto no es un arreglo: es una campaña sobre toda la
# flota. El 2026-11-04 un solo commit fijó `ubuntu-24.04` en 17 workflows y, si contara como
# «arreglo», reiniciaría el reloj de estabilidad de toda la automatización a la vez y dejaría la
# compuerta ciega justo cuando hay que mirarla. Se mide en **workflows tocados**, no en archivos:
# los commits de regeneración del bot tocan cientos de datos sin arreglar ningún flujo, y el
# arreglo del alias del contrato (2026-11-04) tocó 192 archivos siendo un arreglo de verdad.
WORKFLOWS_PARA_CONTAR_COMO_CAMPANA = 3


def ultimo_arreglo(nombre: str, rama: str) -> datetime | None:
    """Fecha del último commit que tocó el flujo **o cualquiera de sus scripts**.

    Es el corte para juzgar estabilidad: las corridas anteriores no dicen nada del código que
    corre hoy. Se incluyen los scripts porque el arreglo casi nunca está en el YAML —el de
    `ifrs_sectores` del 2026-11-05 fue en `pipelines/ifrs_sectores/actualizar.py`—, y se
    descartan los commits de campaña (ver `WORKFLOWS_PARA_CONTAR_COMO_CAMPANA`): tocar diecisiete
    flujos a la vez no arregla ninguno en particular.

    Devuelve `None` si no hay historial (clon sin `.git`, p. ej. un artefacto) o si el único
    candidato es de campaña: ahí no se recorta nada y se juzga el historial completo, que es el
    comportamiento conservador.
    """
    import subprocess
    rutas = [f".github/workflows/{nombre}"]
    try:
        inventario = json.loads(INVENTARIO.read_text(encoding="utf-8"))["workflows"]
    except Exception:  # inventario ilegible: la revisión estática ya lo reporta
        inventario = {}
    rutas += list(inventario.get(nombre, {}).get("scripts", []))
    for ref in (f"origin/{rama}", rama, "HEAD"):
        # `%H` y `%cI` por commit; el hash hace falta para medir el tamaño de cada uno. `--name-only`
        # NO sirve para eso: con un pathspec, git lista solo los archivos que coinciden, así que un
        # commit que tocó veinte siempre informaría uno.
        r = subprocess.run(["git", "log", "--format=%H %cI", "-20", ref, "--", *rutas],
                           cwd=RAIZ, capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            continue
        for linea in r.stdout.splitlines():
            partes = linea.strip().split(" ", 1)
            if len(partes) != 2:
                continue
            sha, fecha_iso = partes
            try:
                fecha = datetime.fromisoformat(fecha_iso)
            except ValueError:
                continue
            barridos = workflows_del_commit(sha)
            if barridos is None or barridos <= WORKFLOWS_PARA_CONTAR_COMO_CAMPANA:
                return fecha   # sin poder medir se asume arreglo: el corte solo puede acortar
            # Se sigue mirando hacia atrás: puede haber un arreglo anterior más específico.
    return None


def workflows_del_commit(sha: str) -> int | None:
    """Cuántos archivos de `.github/workflows/` tocó el commit."""
    import subprocess
    r = subprocess.run(["git", "show", "--name-only", "--format=", sha, "--", ".github/workflows/"],
                       cwd=RAIZ, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return len([l for l in r.stdout.splitlines() if l.strip().endswith((".yml", ".yaml"))])


# Workflows que no producen tablas del manifiesto pero escriben en la rama por su cuenta.
# `fi_eeff.yml` es el caso que motivó esta lista: sus tablas ya estaban inventariadas, pero
# la compuerta de frescura solo miraba los flujos del inventario, así que pasó **33 días**
# en rojo (una negativa de acceso de la CMF bloqueaba cada cierre) sin que el guardián
# semanal lo dijera. Un publicador que commitea en la rama es parte de la automatización
# aunque su salida no esté en `data_manifest.json`.
FLUJOS_DE_ESCRITURA = {
    "contrato_publicado.yml": 1,   # contrato derivado, cada 2 h
    "fi_eeff.yml": 16,             # balance y resultados FI, días 1,4,7,…,28
}
FLUJO_TITULO = {
    "contrato_publicado.yml": "Contrato derivado (web, esquemas, catálogo y resultados)",
    "fi_eeff.yml": "Fondos de inversión - balance y resultados XML IFRS CMF",
}


def workflows_inventariables() -> list[tuple[str, dict]]:
    """Inventario + escritores de la rama, sin repetir los que ya están."""
    inv = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    flujos = dict(inv["workflows"])
    for nombre, maximo in FLUJOS_DE_ESCRITURA.items():
        flujos.setdefault(nombre, {"scripts": [], "max_dias": maximo})
    return list(flujos.items())


def frescura(repo: str, rama: str) -> list[str]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    ahora, errores = datetime.now(timezone.utc), []
    inv_workflows = set(json.loads(INVENTARIO.read_text(encoding="utf-8"))["workflows"])
    recortados: dict[str, str] = {}
    for nombre, wf in workflows_inventariables():
        def api(ruta: str) -> dict:
            req = urllib.request.Request(f"https://api.github.com/repos/{repo}/actions/workflows/{nombre}{ruta}",
                                         headers={"Accept": "application/vnd.github+json",
                                                  **({"Authorization": f"Bearer {token}"} if token else {})})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        try:
            runs = api(f"/runs?branch={rama}&status=success&per_page=1").get("workflow_runs", [])
            if not runs:
                creado = llegada(nombre, rama) or datetime.fromisoformat(api("")["created_at"].replace("Z", "+00:00"))
        except Exception as e:
            errores.append(f"{nombre}: no se pudo consultar GitHub ({e})")
            continue
        if not runs:
            dias = (ahora - creado).days
            if dias <= wf["max_dias"]:
                print(f"{nombre:36} sin corridas aún; llegó a {rama} hace {dias} días")
            else:
                errores.append(f"{nombre}: ninguna corrida exitosa en {rama} (llegó hace {dias} días)")
            continue
        ultima = datetime.fromisoformat(runs[0]["updated_at"].replace("Z", "+00:00"))
        dias = (ahora - ultima).days
        estado = "OK" if dias <= wf["max_dias"] else "ATRASADO"
        print(f"{nombre:36} última corrida exitosa hace {dias:3d} días (máx. {wf['max_dias']}) {estado}")
        if dias > wf["max_dias"]:
            que = ("las tablas del manifiesto" if nombre in inv_workflows
                   else "lo que publica en la rama")
            errores.append(f"{nombre}: {dias} días sin una corrida exitosa (máximo {wf['max_dias']}); "
                           f"{que} se están quedando como foto fija")
        corte = ultimo_arreglo(nombre, rama)
        encontrados, descartadas = inestabilidad(nombre, api, rama, desde=corte)
        errores += encontrados
        if corte is not None and descartadas:
            recortados[nombre] = corte.strftime("%Y-%m-%d")
    if recortados:
        # Una sola línea, no una por flujo: en la semana siguiente a un arreglo el corte toca a
        # casi todos y trece líneas iguales esconderían el resto del informe.
        fechas = sorted(set(recortados.values()))
        print(f"\nEstabilidad medida desde el último arreglo ({', '.join(fechas)}): "
              f"{len(recortados)} flujo(s) con historial anterior descartado")
    return errores


# Un flujo puede tener «una corrida exitosa reciente» y fallar casi siempre: el 2026-11-03/04
# `contrato_publicado.yml` falló 4 de 6 corridas del día y el guardián no dijo nada, porque
# solo miraba la última exitosa. Un publicador que falla más de la mitad de las veces es una
# automatización rota aunque la foto del momento esté al día.
CORRIDAS_PARA_INESTABILIDAD = 10


def _fecha_corrida(run: dict) -> datetime | None:
    """Momento de la corrida, para ordenar y recortar. `created_at` manda: `updated_at` cambia
    cuando alguien re-ejecuta el job desde la interfaz y ensuciaría el corte."""
    for campo in ("created_at", "run_started_at", "updated_at"):
        valor = run.get(campo)
        if valor:
            try:
                return datetime.fromisoformat(valor.replace("Z", "+00:00"))
            except ValueError:
                continue
    return None


def inestabilidad(nombre: str, api, rama: str,
                  desde: datetime | None = None) -> tuple[list[str], int]:
    """Falla si el flujo falla más que acierta en sus últimas corridas terminadas.

    `desde` recorta el historial anterior al último arreglo del flujo (ver `ultimo_arreglo`):
    una vez corregida la causa, las corridas viejas no describen el código que corre hoy.
    Devuelve los errores y cuántas corridas quedaron fuera por el corte.
    """
    try:
        historial = api(
            f"/runs?branch={rama}&per_page={CORRIDAS_PARA_INESTABILIDAD}"
        ).get("workflow_runs", [])
    except Exception as e:  # la consulta principal ya informó el problema si era de red
        return [f"{nombre}: no se pudo revisar la estabilidad de sus corridas ({e})"], 0
    # `cancelled` y `skipped` no dicen nada del flujo; se descartan antes de dividir.
    terminadas = [r for r in historial if r.get("conclusion") in {"success", "failure"}]
    posteriores, descartadas = terminadas, 0
    if desde is not None:
        con_fecha = [(r, _fecha_corrida(r)) for r in terminadas]
        posteriores = [r for r, f in con_fecha if f is None or f >= desde]
        descartadas = len(terminadas) - len(posteriores)
        if not posteriores:
            # Todo el historial que se ve es anterior al arreglo: todavía no hay con qué juzgar.
            return [], descartadas
    fallidas = [r for r in posteriores if r["conclusion"] == "failure"]
    if len(posteriores) < 4 or len(fallidas) * 2 <= len(posteriores):
        return [], descartadas
    ultima_falla = max(
        (r.get("updated_at", "") for r in fallidas), default=""
    )[:10]
    return [
        f"{nombre}: {len(fallidas)} de sus últimas {len(posteriores)} corridas fallaron "
        f"(última el {ultima_falla}); la automatización no es estable aunque su última "
        "corrida exitosa esté dentro del plazo"
    ], descartadas


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frescura", action="store_true")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--rama", default="main")
    a = ap.parse_args(argv)
    errores = estatica()
    if a.frescura:
        errores += frescura(a.repo, a.rama)
    for e in errores:
        print(f"Error: {e}")
    n = len(json.loads(INVENTARIO.read_text())["tablas"])
    print(f"Automatización: {n} tablas inventariadas, {len(errores)} problemas.")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())

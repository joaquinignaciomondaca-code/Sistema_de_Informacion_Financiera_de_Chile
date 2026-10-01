#!/usr/bin/env python3
"""Balance y estado de resultados anuales de los fondos mutuos (CMF, XML IFRS «FMEF», Circular 1997).

Fuente: la ficha de cada fondo (`entidad.php … pestania=3&mm=12&aa=AAAA&tipo_norma=IFRS`) enlaza el XML con los
estados financieros del cierre de diciembre. No hay descarga masiva: una ficha y un XML por fondo y año.
Formato, cuentas y mediciones: ffmm/scripts/eeff_xml.py y docs/notas/ffmm_estados_financieros_xml_2026-10-01.md.

Qué procesa
-----------
Todos los fondos —vigentes y extintos— y todos los cierres de diciembre desde 2010 (primer envío IFRS, «pro forma»).
Candidatos: por cada fondo del maestro de carteras, los diciembres dentro de su vida activa; y, para los fondos del
registro que nunca reportaron cartera, todos los años (la ficha confirma «No existe información» una sola vez).

Estado de cada fondo y cierre
-----------------------------
  ok               XML leído, con las 35 cuentas del ejercicio; se publica.
  sin_informacion  la ficha dice «No existe información de la entidad para el periodo señalado».
  ilegible         la ficha enlaza un XML que no se puede usar (otro fondo, moneda desconocida, cuentas faltantes,
                   mal formado) o, tras ILEGIBLE_TRAS corridas, no llegó completo. Se excluye y queda en el manifiesto.
  pendiente        aún sin resolver: no se intentó, o la CMF no respondió (desafío JavaScript, corte, XML a medias).
Un error transitorio nunca se confunde con «sin información»: la serie no se publica con huecos silenciosos.

Incremental
-----------
El progreso vive en .local-data/ffmm_eeff (la caché de Actions lo conserva entre corridas) y, ya publicado, en los
Parquet y en ffmm_eeff_control.json: si la caché se pierde, el estado se reconstruye desde lo publicado.
  * cierres con más de DIAS_CIERRE días de cerrados: no se vuelven a pedir, salvo una vuelta de refresco: cada corrida
    revisa la ficha de 1/36 de la historia (así toda se revisa una vez al año) y de los dos últimos cierres. Si el
    nombre del XML cambia, la CMF autorizó un reenvío: se descarga de nuevo y queda en `reediciones`;
  * un cierre abierto (menos de DIAS_CIERRE días) se publica con lo que haya, y se relee en cada corrida.

Compuertas (README §4): la serie se publica solo si todos los cierres cerrados están resueltos, y se detiene (sin
publicar nada) si descuadran en bloque (≥3 y más del 5 %) o si casi nadie trae los tres totales reconocibles
—política común de pipelines/auto/cuadratura.py—, o si más del 2 % de los XML son ilegibles (cambió el formato).
Un fondo aislado que no cuadra se publica con su aviso en el manifiesto.

Salidas (formato largo, una fila por fondo, cierre y cuenta; miles de la moneda del fondo):
  docs/outputs/ffmm/ffmm_balance/<AAAA>.parquet          16 líneas por fondo y cierre
  docs/outputs/ffmm/ffmm_resultados/<AAAA>.parquet       19 líneas por fondo y cierre
  + manifest.json de cada tabla y docs/outputs/ffmm/ffmm_eeff_control.json (estado, huecos y reediciones).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.request
import zlib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipelines.auto import cuadratura, estable  # noqa: E402
import eeff_xml  # noqa: E402
from eeff_xml import ErrorFuente, ErrorTransitorio  # noqa: E402

SALIDA = RAIZ / "docs" / "outputs" / "ffmm"
LOCAL = RAIZ / ".local-data" / "ffmm_eeff"
CONTROL = SALIDA / "ffmm_eeff_control.json"
MAESTRO = SALIDA / "maestro_fondos_mutuos.parquet"
UNIVERSO = SALIDA / "ffmm_registro_fondos_universo.parquet"
TABLAS = ("balance", "resultados")

DESDE = 2010                 # primer envío IFRS («pro forma»); antes solo hay FECU en norma chilena
DIAS_CIERRE = 150            # un cierre de diciembre se da por cerrado 150 días después (fines de mayo)
ILEGIBLE_TRAS = 3            # corridas seguidas sin poder leer el XML antes de excluirlo como ilegible
VUELTAS_REFRESCO = 36        # 3 corridas al mes × 12: cada corrida revisa 1/36 de lo ya resuelto
MAX_ILEGIBLES = 0.02         # más de 2 % de XML ilegibles = cambió el formato: no se publica
REINTENTOS_RESPUESTA = 3     # intentos por ficha o XML cuando la CMF responde algo que no es lo pedido
ESPERAS_RESPUESTA = (8, 20)  # segundos entre esos intentos
RONDAS_REZAGADOS = 2         # al final de la corrida, rondas lentas (1 hilo) para los que siguen pendientes
ESPERA_REZAGADOS = 45        # segundos antes de cada ronda
MAX_AVISOS = 300
MAX_REEDICIONES = 200

UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)"}
URL_FICHA = ("https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={run}&grupo=&tipoentidad=RGFMU"
             "&row=&vig=VI&control=svs&pestania=3&mm=12&aa={anio}&tipo_norma=IFRS")
URL_XML = ("https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_xml_verarchivo.php"
           "?archivo={archivo}&&rut={run}&&periodo={anio}12&&path=/web/ifrs_xml/fmifr/xml/&&desc_archivo=Estados_financieros_")

AVISO_DV = "el XML informa un dígito verificador distinto del RUN (se publica el correcto)"
AVISOS_ANTIGUOS = {"el dígito verificador del RUN no coincide": AVISO_DV}   # texto de la primera versión

ESQUEMA = pa.schema([
    ("periodo", pa.string()), ("run_fondo", pa.string()), ("run_fondo_dv", pa.string()),
    ("nombre_fondo", pa.string()), ("rut_agf", pa.string()), ("razon_social_agf", pa.string()),
    ("moneda", pa.string()), ("moneda_cmf", pa.string()), ("seccion", pa.string()), ("tipo_linea", pa.string()),
    ("orden", pa.int32()), ("codigo_cuenta", pa.string()), ("cuenta", pa.string()), ("nota", pa.string()),
    ("valor_miles_mf", pa.int64()), ("valor_anterior_miles_mf", pa.int64()),
    ("fuente_archivo", pa.string()), ("enviado_cmf", pa.string()), ("sha256_archivo", pa.string()),
])
assert tuple(ESQUEMA.names) == eeff_xml.COLUMNAS


def _hoy() -> date:
    """Fecha de la corrida (se aparta para que las pruebas no dependan del reloj)."""
    return date.today()


def ultimo_cierre(hoy: date) -> int:
    return hoy.year - 1


def cerrado(anio: int, hoy: date) -> bool:
    return (hoy - date(anio, 12, 31)).days > DIAS_CIERRE


# ---------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------

class Frenazo:
    """Espera compartida cuando la CMF no responde bien (desafío JavaScript, cortes) y freno de emergencia:
    tras `limite` fallas seguidas en cualquier hilo la corrida termina y guarda el progreso."""

    def __init__(self, limite: int = 40):
        self.limite = limite
        self.seguidas = 0
        self.detener = threading.Event()
        self._lock = threading.Lock()

    def ok(self) -> None:
        with self._lock:
            self.seguidas = 0

    def falla(self) -> None:
        with self._lock:
            self.seguidas += 1
            n = self.seguidas
        if n >= self.limite:
            self.detener.set()
            return
        time.sleep(min(30.0, 1.5 * 2 ** min(n, 5)))


FRENO = Frenazo()


def _get(url: str, intentos: int = 3, timeout: int = 60) -> bytes:
    ultimo = "sin intentos"
    for _ in range(intentos):
        if FRENO.detener.is_set():
            break
        time.sleep(random.uniform(0.05, 0.25))  # cortesía con la CMF
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                cuerpo = r.read()
            FRENO.ok()
            return cuerpo
        except urllib.error.HTTPError as e:
            ultimo = f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001 - cortes de red, TLS, tiempo agotado
            ultimo = type(e).__name__
        FRENO.falla()
    raise ErrorTransitorio(f"sin respuesta de la CMF ({ultimo})")


def _con_reintentos(fn):
    """Ejecuta `fn`; si la CMF responde algo que no es lo pedido (página de desafío, XML a medias) espera y reintenta.

    En el primer recorrido completo (11.242 fondos y cierres) 14 fichas recibieron el desafío JavaScript y, sin este
    reintento, quedaron pendientes y bloquearon la publicación de toda la serie.
    """
    ultimo = None
    for i in range(REINTENTOS_RESPUESTA):
        try:
            return fn()
        except ErrorTransitorio as e:
            ultimo = e
            FRENO.falla()
            if FRENO.detener.is_set():
                break
            if i < REINTENTOS_RESPUESTA - 1:
                time.sleep(ESPERAS_RESPUESTA[min(i, len(ESPERAS_RESPUESTA) - 1)])
    raise ultimo


# ---------------------------------------------------------------------------
# Candidatos
# ---------------------------------------------------------------------------

def candidatos(hoy: date, desde: int = DESDE, hasta: int | None = None) -> list[tuple[str, int]]:
    """(RUN, año) de cada cierre de diciembre que un fondo pudo informar, del más reciente al más antiguo."""
    hasta = ultimo_cierre(hoy) if hasta is None else hasta
    out: set[tuple[str, int]] = set()
    conocidos: set[str] = set()
    if MAESTRO.exists():
        for f in pq.read_table(MAESTRO, columns=["run_fondo", "primer_periodo", "ultimo_periodo"]).to_pylist():
            run = str(f["run_fondo"]).strip()
            if not run.isdigit() or not f.get("primer_periodo") or not f.get("ultimo_periodo"):
                continue
            conocidos.add(run)
            y0 = int(f["primer_periodo"][:4])
            y1, m1 = int(f["ultimo_periodo"][:4]), int(f["ultimo_periodo"][5:7])
            fin = y1 if m1 == 12 else y1 - 1
            out.update((run, a) for a in range(max(desde, y0), min(hasta, fin) + 1))
    if UNIVERSO.exists():
        for f in pq.read_table(UNIVERSO, columns=["run_fondo"]).to_pylist():
            run = str(f["run_fondo"]).strip()
            if run.isdigit() and run not in conocidos:
                out.update((run, a) for a in range(desde, hasta + 1))
    return sorted(out, key=lambda k: (-k[1], int(k[0])))


# ---------------------------------------------------------------------------
# Estado: lo publicado + el progreso de la caché
# ---------------------------------------------------------------------------

def registros_publicados() -> dict[tuple[str, int], dict]:
    """Reconstruye los registros `ok` desde los Parquet publicados y el resto desde el control."""
    reg: dict[tuple[str, int], dict] = {}
    for tabla in TABLAS:
        for ruta in sorted((SALIDA / f"ffmm_{tabla}").glob("*.parquet")):
            for f in pq.read_table(ruta).to_pylist():
                k = (f["run_fondo"], int(f["periodo"][:4]))
                r = reg.setdefault(k, {
                    "run": k[0], "anio": k[1], "estado": "ok", "revisado": "0000-00-00",
                    "archivo": f["fuente_archivo"], "sha256": f["sha256_archivo"], "enviado": f["enviado_cmf"],
                    "run_dv": f["run_fondo_dv"], "nombre": f["nombre_fondo"] or "", "rut_agf": f["rut_agf"] or "",
                    "agf": f["razon_social_agf"] or "", "moneda_cmf": f["moneda_cmf"], "moneda": f["moneda"],
                    "actual": {}, "anterior": {}, "notas": {}, "avisos": []})
                r["actual"][f["codigo_cuenta"]] = f["valor_miles_mf"]
                if f["valor_anterior_miles_mf"] is not None:
                    r["anterior"][f["codigo_cuenta"]] = f["valor_anterior_miles_mf"]
                if f["nota"] is not None:
                    r["notas"][f["codigo_cuenta"]] = f["nota"]
    ctl = cargar_control()
    for anio, runs in (ctl.get("sin_informacion") or {}).items():
        for run in runs:
            reg.setdefault((str(run), int(anio)), {"run": str(run), "anio": int(anio), "estado": "sin_informacion",
                                                   "revisado": "0000-00-00"})
    for e in ctl.get("ilegibles") or []:
        reg.setdefault((str(e["run"]), int(e["anio"])), {
            "run": str(e["run"]), "anio": int(e["anio"]), "estado": "ilegible", "revisado": "0000-00-00",
            "motivo": e.get("motivo", ""), "intentos": e.get("intentos", ILEGIBLE_TRAS), "archivo": e.get("archivo")})
    for e in ctl.get("avisos") or []:
        r = reg.get((str(e["run"]), int(e["anio"])))
        if r is not None and r["estado"] == "ok":
            r["avisos"].append(e["aviso"])
    return reg


def cargar_progreso() -> dict[tuple[str, int], dict]:
    ruta = LOCAL / "progreso.jsonl.gz"
    out: dict[tuple[str, int], dict] = {}
    if not ruta.exists():
        return out
    try:
        with gzip.open(ruta, "rt", encoding="utf-8") as fh:
            for linea in fh:
                r = json.loads(linea)
                out[(r["run"], int(r["anio"]))] = r
    except (OSError, ValueError) as e:
        print(f"::warning::progreso ilegible ({e}); se parte de lo publicado")
        return {}
    return out


def guardar_progreso(estado: dict) -> None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    tmp = LOCAL / "progreso.jsonl.gz.tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as fh:
        for k in sorted(estado, key=lambda k: (k[1], int(k[0]))):
            fh.write(json.dumps(estado[k], ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")
    os.replace(tmp, LOCAL / "progreso.jsonl.gz")


def cargar_estado() -> dict[tuple[str, int], dict]:
    """Lo publicado manda; el progreso de la caché lo reemplaza solo si es una revisión más reciente."""
    estado = registros_publicados()
    for k, r in cargar_progreso().items():
        base = estado.get(k)
        if base is None or r.get("revisado", "") >= base.get("revisado", ""):
            estado[k] = r
    for r in estado.values():
        if r.get("avisos"):
            r["avisos"] = [AVISOS_ANTIGUOS.get(a, a) for a in r["avisos"]]
    return estado


def cargar_control() -> dict:
    return json.loads(CONTROL.read_text(encoding="utf-8")) if CONTROL.exists() else {}


# ---------------------------------------------------------------------------
# Un fondo y un cierre
# ---------------------------------------------------------------------------

def _pendiente(previo: dict | None, base: dict, fase: str, motivo: str, intentos: int,
               contar: bool = True) -> tuple[dict, str]:
    """La CMF no entregó lo pedido. Un dato ya resuelto no se pierde por una falla de la relectura.

    `intentos` cuenta corridas, no peticiones: las rondas finales de la misma corrida no lo suben (`contar=False`).
    """
    if previo is not None and previo.get("estado") in ("ok", "sin_informacion"):
        return previo, "error_transitorio"
    intentos += 1 if contar else 0
    if fase in ("xml", "enlace") and intentos >= ILEGIBLE_TRAS:
        return {**base, "estado": "ilegible", "motivo": f"{motivo} (tras {intentos} corridas)", "intentos": intentos}, "ilegible"
    return {**base, "estado": "pendiente", "motivo": motivo, "fase": fase, "intentos": intentos}, "error_transitorio"


def resolver(run: str, anio: int, previo: dict | None, hoy: date, contar: bool = True) -> tuple[dict, str | None]:
    """Resuelve un fondo y un cierre. Devuelve (registro, evento); no lanza.

    evento: None · 'nuevo' · 'reedicion' · 'error_transitorio' · 'ilegible'
    """
    base = {"run": run, "anio": anio, "revisado": hoy.isoformat()}
    intentos = int((previo or {}).get("intentos", 0)) if (previo or {}).get("estado") in ("pendiente", "ilegible") else 0
    try:
        tipo, archivo = _con_reintentos(
            lambda: eeff_xml.clasificar_ficha(_get(URL_FICHA.format(run=run, anio=anio))))
    except ErrorTransitorio as e:
        return _pendiente(previo, base, "ficha", str(e), intentos, contar)
    if tipo == "sin_informacion":
        if previo is not None and previo.get("estado") == "ok":
            # La CMF ya no muestra el envío: se conserva lo publicado y se deja constancia.
            avisos = sorted(set(previo.get("avisos", [])) | {"la ficha de la CMF ya no muestra este envío"})
            return {**previo, "avisos": avisos, "revisado": base["revisado"]}, None
        return {**base, "estado": "sin_informacion"}, None
    if tipo == "sin_enlace":
        return _pendiente(previo, base, "enlace", "la ficha no enlaza ningún XML", intentos, contar)
    if previo is not None and previo.get("estado") == "ok" and previo.get("archivo") == archivo:
        return {**previo, "revisado": base["revisado"]}, None
    def pedir_xml():
        crudo = _get(URL_XML.format(archivo=archivo, run=run, anio=anio))
        return crudo, eeff_xml.leer_xml(crudo)

    try:
        raw, raiz = _con_reintentos(pedir_xml)
        datos = eeff_xml.extraer(raiz, run, anio)
    except ErrorTransitorio as e:
        return _pendiente(previo, base, "xml", str(e), intentos, contar)
    except ErrorFuente as e:
        if previo is not None and previo.get("estado") == "ok":
            avisos = sorted(set(previo.get("avisos", [])) | {f"el reenvío {archivo} no se pudo leer: {e}"})
            return {**previo, "avisos": avisos, "revisado": base["revisado"]}, "ilegible"
        return {**base, "estado": "ilegible", "motivo": str(e)[:200], "archivo": archivo,
                "intentos": intentos + 1}, "ilegible"
    avisos = [f"{regla} (Δ {delta})" for regla, delta in cuadratura.identidades_ffmm(datos["actual"])]
    if not datos["dv_coincide"]:
        avisos.append(AVISO_DV)
    if datos["usa_alias"]:
        avisos.append("la línea «Otros» de resultados viene con el código antiguo `Otros`")
    reg = {**base, "estado": "ok", "archivo": archivo, "sha256": hashlib.sha256(raw).hexdigest(),
           "bytes": len(raw), "enviado": eeff_xml.enviado_de(archivo), "run_dv": datos["run_dv"],
           "nombre": datos["nombre"], "rut_agf": datos["rut_agf"], "agf": datos["agf"],
           "moneda_cmf": datos["moneda_cmf"], "moneda": datos["moneda"], "actual": datos["actual"],
           "anterior": datos["anterior"], "notas": datos["notas"], "avisos": avisos}
    if previo is not None and previo.get("estado") == "ok":
        reg["reedicion_de"] = previo.get("archivo")
        return reg, "reedicion"
    return reg, "nuevo"


# ---------------------------------------------------------------------------
# Qué hay que pedir en esta corrida
# ---------------------------------------------------------------------------

def toca_refresco(run: str, anio: int, hoy: date, forzar: bool = False) -> bool:
    """Los dos últimos cierres se revisan siempre; el resto, una vuelta de 1/36 por corrida (toda la historia al año)."""
    if forzar or anio >= ultimo_cierre(hoy) - 1:
        return True
    vuelta = (hoy.timetuple().tm_yday // 10) % VUELTAS_REFRESCO
    return zlib.crc32(f"{run}|{anio}".encode()) % VUELTAS_REFRESCO == vuelta


def planificar(cand: list[tuple[str, int]], estado: dict, hoy: date, forzar: bool = False) -> list[tuple[str, int]]:
    pedir = []
    for run, anio in cand:
        r = estado.get((run, anio))
        if r is None or r["estado"] in ("pendiente", "ilegible") or toca_refresco(run, anio, hoy, forzar):
            pedir.append((run, anio))
    return pedir


# ---------------------------------------------------------------------------
# Compuerta
# ---------------------------------------------------------------------------

def evaluar(estado: dict, cand: list[tuple[str, int]], hoy: date) -> dict:
    """¿Se puede publicar? `bloqueo` = falta resolver cierres cerrados (se reanuda); `error` = se detiene la serie."""
    claves = set(cand) | set(estado)
    pend_cerrados = sorted(k for k in claves if cerrado(k[1], hoy) and estado.get(k, {}).get("estado") in (None, "pendiente"))
    ok = [r for r in estado.values() if r["estado"] == "ok"]
    ilegibles = [r for r in estado.values() if r["estado"] == "ilegible"]
    filas_bal = [f for r in ok for f in eeff_xml.filas(r)["balance"]]
    verificados, malos = cuadratura.verificar_ffmm(filas_bal)
    motivo = cuadratura.motivo_detener(verificados, malos, cuadratura.contar_grupos(filas_bal, cuadratura.CLAVES_FFMM))
    con_xml = len(ok) + len(ilegibles)
    if not motivo and con_xml and len(ilegibles) > MAX_ILEGIBLES * con_xml and len(ilegibles) >= 5:
        motivo = (f"{len(ilegibles)} de {con_xml} XML son ilegibles ({len(ilegibles) / con_xml:.1%} > {MAX_ILEGIBLES:.0%}): "
                  f"cambió el formato. Ej.: {ilegibles[0].get('motivo', '')}")
    return {"pendientes_cerrados": pend_cerrados, "motivo_error": motivo, "balances_verificados": verificados,
            "balances_descuadrados": len(malos), "ok": len(ok), "ilegibles": len(ilegibles),
            "puede_publicar": bool(ok) and not pend_cerrados and not motivo}


# ---------------------------------------------------------------------------
# Publicación
# ---------------------------------------------------------------------------

def escribir_tablas(estado: dict) -> dict[str, dict]:
    ok = [r for r in estado.values() if r["estado"] == "ok"]
    por_anio: dict[int, list[dict]] = defaultdict(list)
    for r in ok:
        por_anio[r["anio"]].append(r)
    esperados = {t: set() for t in TABLAS}
    for anio, regs in sorted(por_anio.items()):
        filas = {t: [] for t in TABLAS}
        for r in sorted(regs, key=lambda r: int(r["run"])):
            for t, fs in eeff_xml.filas(r).items():
                filas[t] += fs
        for t in TABLAS:
            carpeta = SALIDA / f"ffmm_{t}"
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta = carpeta / f"{anio}.parquet"
            esperados[t].add(ruta.name)
            nueva = pa.Table.from_pylist(filas[t], schema=ESQUEMA)
            if ruta.exists() and pq.read_table(ruta).equals(nueva):
                continue
            tmp = ruta.with_suffix(".tmp")
            pq.write_table(nueva, tmp, compression="zstd", compression_level=9)
            os.replace(tmp, ruta)
    resumen = {}
    for t in TABLAS:
        carpeta = SALIDA / f"ffmm_{t}"
        carpeta.mkdir(parents=True, exist_ok=True)
        for extra in carpeta.glob("*.parquet"):
            if extra.name not in esperados[t]:
                extra.unlink()
        rutas = sorted(carpeta.glob("*.parquet"))
        periodos = [f"{r.stem}-12" for r in rutas]
        man = {"tabla": f"ffmm_{t}", "files": [f"outputs/ffmm/{carpeta.name}/{r.name}" for r in rutas],
               "total_records": sum(pq.ParquetFile(r).metadata.num_rows for r in rutas), "periodos": periodos,
               "fondos_por_periodo": {f"{a}-12": len(rs) for a, rs in sorted(por_anio.items())},
               "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        estable.escribir_json(carpeta / "manifest.json", man)
        resumen[t] = man
    return resumen


def construir_control(estado: dict, cand: list[tuple[str, int]], hoy: date, reediciones: list[dict]) -> dict:
    claves = set(cand) | set(estado)
    cierres: dict[str, dict] = {}
    sin_info: dict[str, list[str]] = defaultdict(list)
    for k in sorted(claves, key=lambda k: (k[1], int(k[0]))):
        est = estado.get(k, {}).get("estado", "pendiente")
        c = cierres.setdefault(str(k[1]), {"candidatos": 0, "con_estados": 0, "sin_informacion": 0, "ilegibles": 0,
                                           "pendientes": 0, "cerrado": cerrado(k[1], hoy)})
        c["candidatos"] += 1
        if est == "ok":
            c["con_estados"] += 1
        elif est == "sin_informacion":
            c["sin_informacion"] += 1
            sin_info[str(k[1])].append(k[0])
        elif est == "ilegible":
            c["ilegibles"] += 1
        else:
            c["pendientes"] += 1
    previo = cargar_control()
    ilegibles = [{"run": r["run"], "anio": r["anio"], "motivo": r.get("motivo", ""), "intentos": r.get("intentos", 0),
                  "archivo": r.get("archivo")}
                 for r in sorted(estado.values(), key=lambda r: (r["anio"], int(r["run"]))) if r["estado"] == "ilegible"]
    avisos = [{"run": r["run"], "anio": r["anio"], "aviso": a}
              for r in sorted(estado.values(), key=lambda r: (r["anio"], int(r["run"])))
              if r["estado"] == "ok" for a in r.get("avisos", [])][:MAX_AVISOS]
    return {"tabla": "ffmm_eeff", "desde": DESDE, "cierres": cierres, "sin_informacion": dict(sin_info),
            "ilegibles": ilegibles, "avisos": avisos,
            "reediciones": ((previo.get("reediciones") or []) + reediciones)[-MAX_REEDICIONES:],
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


ORIGEN = ("CMF — Estados financieros IFRS de fondos mutuos (XML «FMEF», Circular 1997 de 2010), enlazado en la ficha de "
          "cada fondo: https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&tipoentidad=RGFMU")
DESCRIPCION = {
    "balance": ("Estado de situación financiera de cada fondo mutuo —vigente o extinto— al 31 de diciembre de cada año, "
                "línea por línea (16 líneas), con el comparativo del año anterior. Miles de la moneda del fondo "
                "(pesos, dólares o euros)."),
    "resultados": ("Estado de resultados integrales de cada fondo mutuo —vigente o extinto— del ejercicio completo, "
                   "línea por línea (19 líneas), con el comparativo del año anterior. Miles de la moneda del fondo "
                   "(pesos, dólares o euros)."),
}


def actualizar_data_manifest() -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    hoy = _hoy().isoformat()
    nuevas = []
    for t in TABLAS:
        m = SALIDA / f"ffmm_{t}" / "manifest.json"
        if not m.exists():
            continue
        mm = json.loads(m.read_text())
        per = mm["periodos"]
        nuevas.append({
            "id": f"ffmm_{t}", "name": f"ffmm.{t}", "view_name": f"ffmm_{t}", "sector": "ffmm",
            "sector_label": "Fondos Mutuos", "norma": "IFRS · XML CMF (Circular 1997)",
            "corte": f"{per[0]} a {per[-1]}" if per else "sin cierres",
            "frescura": f"Último cierre publicado: {per[-1]}" if per else "",
            "modo": "Automático · 3 veces al mes, incremental", "ultima_actualizacion": hoy,
            "file_parquet": f"outputs/ffmm/ffmm_{t}/manifest.json", "registros_reales": mm["total_records"],
            "descripcion": DESCRIPCION[t], "origen": ORIGEN,
        })
    quitar = {e["id"] for e in nuevas}
    man["tables"] = [t for t in man["tables"] if t["id"] not in quitar] + nuevas
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    estable.escribir_json(ruta, man)


# ---------------------------------------------------------------------------
# Corrida
# ---------------------------------------------------------------------------

def procesar(pedir: list[tuple[str, int]], estado: dict, hoy: date, minutos: float, hilos: int,
             contar: bool = True) -> dict:
    """Resuelve los pendientes con `hilos` hilos y un tope de tiempo; devuelve contadores y reediciones."""
    inicio = time.monotonic()
    cuenta: Counter = Counter()
    reediciones: list[dict] = []
    detenido_por_tiempo = False

    def tarea(k):
        if FRENO.detener.is_set() or time.monotonic() - inicio > minutos * 60:
            return k, None, "omitido"
        r, ev = resolver(k[0], k[1], estado.get(k), hoy, contar)
        return k, r, ev

    hechos = 0
    with ThreadPoolExecutor(max_workers=max(1, hilos)) as ex:
        futuros = [ex.submit(tarea, k) for k in pedir]
        for fut in as_completed(futuros):
            k, r, ev = fut.result()
            if ev == "omitido":
                cuenta["omitidos"] += 1
                detenido_por_tiempo = detenido_por_tiempo or not FRENO.detener.is_set()
                continue
            estado[k] = r
            cuenta[r["estado"]] += 1
            if ev:
                cuenta[ev] += 1
            if ev == "reedicion":
                reediciones.append({"run": k[0], "anio": k[1], "archivo_anterior": r.get("reedicion_de"),
                                    "archivo_nuevo": r.get("archivo"), "detectado": hoy.isoformat()})
            hechos += 1
            if hechos % 500 == 0:
                guardar_progreso(estado)
                print(f"… {hechos}/{len(pedir)} fondos y cierres resueltos", flush=True)
    return {"cuenta": dict(cuenta), "reediciones": reediciones, "por_tiempo": detenido_por_tiempo,
            "freno": FRENO.detener.is_set()}


def correr(minutos: float = 270, hilos: int = 4, desde: int = DESDE, hasta: int | None = None,
           limite: int = 0, forzar: bool = False, publicar: bool = True) -> dict:
    hoy = _hoy()
    inicio = time.monotonic()
    FRENO.__init__()
    LOCAL.mkdir(parents=True, exist_ok=True)
    estado = cargar_estado()
    cand = candidatos(hoy, desde, hasta)
    pedir = planificar(cand, estado, hoy, forzar)
    if limite:
        pedir = pedir[:limite]
    nuevos = sum(1 for k in pedir if estado.get(k) is None)
    print(f"Cierres {desde}..{ultimo_cierre(hoy) if hasta is None else hasta}: {len(cand)} candidatos · "
          f"ya resueltos {len(estado)} · a pedir {len(pedir)} ({nuevos} nuevos)", flush=True)
    res = procesar(pedir, estado, hoy, minutos, hilos) if pedir else {"cuenta": {}, "reediciones": [], "por_tiempo": False,
                                                                       "freno": False}
    # Rondas lentas para los que siguen pendientes (desafíos de la CMF que aguantaron los reintentos): un hilo y espera
    # previa. No cuentan como una corrida más para marcar un XML como ilegible.
    for ronda in range(RONDAS_REZAGADOS):
        rezagados = sorted((k for k, r in estado.items() if r["estado"] == "pendiente"), key=lambda k: (-k[1], int(k[0])))
        restante = minutos - (time.monotonic() - inicio) / 60
        if not rezagados or res["freno"] or restante <= ESPERA_REZAGADOS / 60 + 1:
            break
        print(f"Ronda lenta {ronda + 1}/{RONDAS_REZAGADOS}: {len(rezagados)} pendientes tras la pasada principal", flush=True)
        time.sleep(ESPERA_REZAGADOS)
        extra = procesar(rezagados, estado, hoy, restante, 1, contar=False)
        res["reediciones"] += extra["reediciones"]
        res["freno"] = res["freno"] or extra["freno"]
        res["cuenta"]["rezagados_resueltos"] = res["cuenta"].get("rezagados_resueltos", 0) + sum(
            1 for k in rezagados if estado[k]["estado"] != "pendiente")
    guardar_progreso(estado)
    ev = evaluar(estado, cand, hoy)
    out = {**res, **ev, "candidatos": len(cand), "publicado": False}
    if res["freno"]:
        print("::warning::La CMF dejó de responder bien (desafíos o cortes seguidos): se guarda el progreso y se reanuda "
              "en la próxima corrida")
    if ev["motivo_error"]:
        print(f"::error title=Fondos mutuos EEFF::{ev['motivo_error']}; no se publica")
    elif ev["pendientes_cerrados"]:
        print(f"Serie incompleta: faltan {len(ev['pendientes_cerrados'])} fondos y cierres cerrados; no se publica todavía.")
    elif publicar and ev["puede_publicar"]:
        escribir_tablas(estado)
        estable.escribir_json(CONTROL, construir_control(estado, cand, hoy, res["reediciones"]))
        actualizar_data_manifest()
        out["publicado"] = True
    ilegibles = sorted((r for r in estado.values() if r["estado"] == "ilegible"), key=lambda r: (r["anio"], int(r["run"])))
    pend = sorted((r for r in estado.values() if r["estado"] == "pendiente"), key=lambda r: (r["anio"], int(r["run"])))
    # Los logs de Actions no se pueden bajar desde fuera: el diagnóstico va agrupado en una sola anotación (≤ 4.000 caracteres).
    out["motivos_ilegibles"] = dict(Counter((r.get("motivo") or "")[:70] for r in ilegibles).most_common(8))
    out["motivos_pendientes"] = dict(Counter((r.get("motivo") or "")[:70] for r in pend).most_common(4))
    if ilegibles:
        print("::warning title=FFMM EEFF ilegibles::" + json.dumps(out["motivos_ilegibles"], ensure_ascii=False))
    for r in ilegibles[:3]:
        print(f"::notice::ilegible: fondo {r['run']} cierre {r['anio']}: {r.get('motivo', '')[:140]}")
    for r in pend[:4]:                                   # una muestra para diagnosticar desde las anotaciones
        print(f"::notice::pendiente: fondo {r['run']} cierre {r['anio']} ({r.get('fase')}): {r.get('motivo', '')[:160]}")
    for r in res["reediciones"]:
        print(f"::notice::reedición del fondo {r['run']} cierre {r['anio']}: {r['archivo_nuevo']}")
    (LOCAL / "resumen.json").write_text(json.dumps(
        {k: v for k, v in out.items() if k not in ("pendientes_cerrados", "reediciones")}
        | {"pendientes_cerrados": len(out["pendientes_cerrados"]), "reediciones": len(out["reediciones"])},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--minutos", type=float, default=270, help="tope de tiempo de la corrida (el progreso se conserva)")
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--desde", type=int, default=DESDE)
    ap.add_argument("--hasta", type=int, default=None, help="último cierre a considerar (por defecto, el año pasado)")
    ap.add_argument("--limite", type=int, default=0, help="máximo de fondos y cierres a pedir (pruebas)")
    ap.add_argument("--refrescar-todo", action="store_true", help="revisa la ficha de toda la historia")
    ap.add_argument("--solo-data-manifest", action="store_true")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest()
        return 0
    out = correr(a.minutos, a.hilos, a.desde, a.hasta, a.limite, a.refrescar_todo)
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"publicado={'true' if out['publicado'] else 'false'}\n")
            f.write(f"completo={'true' if not out['pendientes_cerrados'] else 'false'}\n")
    c = out["cuenta"]
    print(f"Resuelto en esta corrida: {c} · fondos con estados {out['ok']} · ilegibles {out['ilegibles']} · "
          f"publicado: {out['publicado']}")
    resumen = {"candidatos": out["candidatos"], "ok": out["ok"], "ilegibles": out["ilegibles"],
               "pendientes_cerrados": len(out["pendientes_cerrados"]), "publicado": out["publicado"],
               "cuenta": c, "balances_verificados": out["balances_verificados"],
               "balances_descuadrados": out["balances_descuadrados"], "por_tiempo": out["por_tiempo"],
               "freno": out["freno"], "motivos_ilegibles": out["motivos_ilegibles"],
               "motivos_pendientes": out["motivos_pendientes"]}
    print("::notice title=FFMM EEFF::FFMM_EEFF_PROGRESS=" + json.dumps(resumen, ensure_ascii=False))
    return 1 if out["motivo_error"] else 0


if __name__ == "__main__":
    sys.exit(main())

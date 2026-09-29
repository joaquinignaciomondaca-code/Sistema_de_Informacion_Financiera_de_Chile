#!/usr/bin/env python3
"""Estados financieros IFRS de AGF, securitizadoras y cajas de compensación (CMF).

Fuente única: el archivo TXT trimestral de la CMF «Estados financieros bajo estándar
IFRS» (estadisticas_ifrs.php → ver_archivo.php?inicio=AAAAMM&termino=AAAAMM). Cada
archivo trae, para todas las sociedades que envían sus estados financieros IFRS
(XBRL, columna «taxonomía»), las cuentas del estado de situación (ESF) y del estado
de resultados (ER) por RUT. Un solo archivo por trimestre alimenta los tres sectores.

Incremental:
  * docs/outputs/ifrs_sectores/manifest.json guarda los trimestres ya procesados.
  * Un trimestre «cerrado» (más de DIAS_CIERRE días desde el fin del trimestre) no se
    vuelve a descargar nunca.
  * Los trimestres recientes se vuelven a leer en cada corrida hasta que se cierran,
    para recoger a las sociedades que presentan tarde. Solo se reescribe el archivo
    anual de ese año.

Selección de entidades por sector: RUT de la lista de entidades del sector, o nombre
reportado que calza con el patrón del sector (así aparecen solas las entidades nuevas,
que quedan marcadas en_lista_entidades = false y se informan en el manifiesto).

Altas automáticas en listas sin registro CMF propio: una sociedad que en el último trimestre
reporta con nombre de caja de compensación (CCAF) o de factoring/leasing y no está en la
lista respectiva se agrega a esa lista (docs/outputs/entidades/novedades_ifrs.json deja el
evento). Solo el último trimestre: una sociedad que dejó de existir no reaparece. Para
factoring/leasing el archivo solo se usa para detectar; sus tablas las publica
factoring_leasing/scripts/backfill_ifrs.py con esa misma lista.

Montos: el entero literal del archivo, en unidades de la moneda informada (moneda =
CLP o USD). No se convierte, no se suma ni se redondea. Si un valor no es entero se
deja nulo y el texto original queda en valor_no_numerico.

Salidas por sector y tabla (balance, resultados):
  docs/outputs/<carpeta>/<prefijo>_<tabla>/<AAAA>.parquet  +  manifest.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import cuadratura  # noqa: E402
DOCS = RAIZ / "docs" / "outputs"
CONTROL = DOCS / "ifrs_sectores" / "manifest.json"
INDICE = "https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php"
ARCHIVO = "https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={0}&termino={1}"
UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)", "Accept": "text/plain,text/html,*/*"}
DIAS_CIERRE = 150

SECTORES = {
    "agf": {
        "carpeta": "agf", "prefijo": "agf", "etiqueta": "Administradoras Generales de Fondos",
        "lista": "agf/agf_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"ADMINISTRADORA\s+GENERAL\s+DE\s+FONDOS|\bA\.?\s?G\.?\s?F\.?(\s|$)"),
    },
    "securitizadoras": {
        "carpeta": "securitizadoras", "prefijo": "securitizadoras", "etiqueta": "Securitizadoras",
        "lista": "securitizadoras/securitizadoras_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"SECURITIZADORA"),
    },
    "cajas_compensacion": {
        "carpeta": "cajas_compensacion", "prefijo": "ccaf", "etiqueta": "Cajas de Compensación",
        "lista": "cajas_compensacion/ccaf_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"CAJA\s+DE\s+COMPENSACI"),
        "alta": lambda c, d, nombre: {
            "rut": int(c), "dv": d, "rut_completo": f"{int(c):,}".replace(",", ".") + f"-{d}", "razon_social": nombre,
            "nombre_fantasia": nombre, "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833", "regulador_primario": "SUSESO", "emisor_valores_cmf": False,
            "estado_vigencia": "Vigente", "lineas_deuda_registradas": False,
            "observaciones": "Agregada automáticamente: reporta estados financieros IFRS a la CMF."},
    },
}
# Listas que solo se completan con este archivo (sin tablas propias aquí).
SOLO_LISTA = {
    "factoring_leasing": {
        "lista": "factoring_leasing/factoring_leasing_maestro.json", "clave_rut": "rut",
        "patron": re.compile(r"\bFACTORING\b|\bLEASING\b"), "excluir": re.compile(r"^BANCO\b|SEGUROS"),
        "alta": lambda c, d, nombre: {
            "rut": f"{c}-{d}", "rut_formateado": f"{int(c):,}".replace(",", ".") + f"-{d}", "razon_social": nombre,
            "nombre_fantasia": nombre, "tipo_sociedad": "Factoring" if "FACTORING" in nombre.upper() else "Leasing",
            "segmento": "Factoring" if "FACTORING" in nombre.upper() else "Leasing",
            "registro_cmf": "Estados financieros IFRS (CMF)", "vigencia_cmf": "Vigente", "vigente": 1, "estado": "Activo",
            "es_factoring": int("FACTORING" in nombre.upper()),
            # El nombre no dice si el leasing es financiero u habitacional: solo se marca lo explícito.
            "es_leasing_habitacional": 1 if "HABITACIONAL" in nombre.upper() else None,
            "eeff_ifrs_en_cmf": "Sí (IFRS)", "fuente_eeff": "CMF > Estados financieros IFRS (TXT)",
            "observaciones": "Agregada automáticamente: reporta estados financieros IFRS a la CMF con giro factoring/leasing."},
    },
}
NOVEDADES = DOCS / "entidades" / "novedades_ifrs.json"
MAX_ALTAS = 10
TABLAS = {"balance": "ESF", "resultados": "ER"}
TIPO_BALANCE = {"I": "individual", "C": "consolidado"}

ESQUEMA = pa.schema([
    ("periodo", pa.string()), ("rut", pa.string()), ("rut_dv", pa.string()),
    ("razon_social", pa.string()), ("tipo_balance", pa.string()), ("moneda", pa.string()),
    ("estado_financiero", pa.string()), ("orden", pa.int32()), ("cuenta", pa.string()),
    ("valor", pa.int64()), ("valor_no_numerico", pa.string()), ("repeticion", pa.int16()),
    ("taxonomia", pa.string()), ("en_lista_entidades", pa.bool_()),
])


class ErrorFuente(Exception):
    pass


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs).get("href") or "")


def _get(url: str, timeout: int = 180) -> bytes:
    ultimo = None
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:  # red inestable de la CMF
            ultimo = e
            time.sleep(5 * (intento + 1))
    raise ErrorFuente(f"{url}: {ultimo}")


def dv(cuerpo: str) -> str:
    s, m = 0, 2
    for c in reversed(cuerpo):
        s += int(c) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def periodos_indice(raw: bytes) -> tuple[list[str], dict[str, str]]:
    """Trimestres del índice y, para cada uno, el enlace anual que lo contiene (respaldo)."""
    if b"<html" not in raw[:2000].lower():
        raise ErrorFuente("el índice CMF no es HTML")
    p = _Links()
    p.feed(raw.decode("utf-8", errors="replace"))
    periodos, anual = set(), {}
    for link in p.links:
        m = re.search(r"inicio=(\d{6})&(?:amp;)?termino=(\d{6})", link)
        if not m or "ver_archivo" not in link:
            continue
        a, b = m.groups()
        if a > b or a[4:] not in ("03", "06", "09", "12") or b[4:] not in ("03", "06", "09", "12"):
            continue
        y, mm = int(a[:4]), int(a[4:])
        while f"{y:04d}{mm:02d}" <= b:
            per = f"{y:04d}{mm:02d}"
            periodos.add(per)
            if a != b:
                anual[per] = (a, b)
            mm += 3
            if mm > 12:
                y, mm = y + 1, 3
    if not periodos:
        raise ErrorFuente("índice CMF sin trimestres")
    return sorted(periodos), anual


def cerrado(periodo: str, hoy: date) -> bool:
    y, m = int(periodo[:4]), int(periodo[4:])
    fin = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (hoy - fin).days > DIAS_CIERRE


def es_txt(raw: bytes) -> bool:
    cab = raw[:2000].lower()
    return bool(raw) and b"<html" not in cab and b"<!doctype" not in cab and b"accion no permitida" not in cab


def decodificar(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _norm(s: str) -> str:
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s.upper()) if not unicodedata.combining(c))
    return " ".join(s.split())


def cargar_listas() -> dict[str, dict[str, str]]:
    listas = {}
    for sec, cfg in {**SECTORES, **SOLO_LISTA}.items():
        filas = json.loads((DOCS / cfg["lista"]).read_text(encoding="utf-8"))
        ruts = {}
        for f in filas:
            cuerpo = str(f[cfg["clave_rut"]]).replace(".", "").split("-")[0].strip()
            if cuerpo.isdigit():
                ruts[cuerpo] = str(f.get("razon_social") or f.get("nombre_empresa") or "")
        if not ruts:
            raise ErrorFuente(f"lista de entidades vacía: {cfg['lista']}")
        listas[sec] = ruts
    return listas


def leer_archivo(raw: bytes, periodo: str, listas: dict[str, dict[str, str]]):
    """Devuelve {sector: {tabla: [filas]}}, estadísticas y avisos."""
    if not es_txt(raw):
        raise ErrorFuente("la descarga no es el TXT de la CMF")
    datos = {s: {t: [] for t in TABLAS} for s in SECTORES}
    avisos: list[str] = []
    entidades_archivo = set()
    lineas_periodo = 0
    orden: dict[tuple, int] = {}
    repet: dict[tuple, int] = {}
    asignacion: dict[str, str | None] = {}
    candidatos: dict[str, dict[str, str]] = {s: {} for s in SOLO_LISTA}
    for n, c in enumerate(csv.reader(io.StringIO(decodificar(raw)), delimiter=";"), start=1):
        if not c or all(not x.strip() for x in c):
            continue
        c = [x.strip() for x in c]
        if len(c) < 9:
            if len(c) > 2 and c[0] == periodo:
                avisos.append(f"línea {n}: {len(c)} campos")
            continue
        per, cuerpo, nombre, tipo, moneda, cuenta, valor, tax, estado = c[:9]
        if per != periodo:
            continue  # el archivo anual trae otros trimestres
        lineas_periodo += 1
        entidades_archivo.add(cuerpo)
        if cuerpo not in asignacion:
            nn = _norm(nombre)
            asignacion[cuerpo] = next((s for s in SECTORES if cuerpo in listas[s]), None) or \
                next((s for s, cfg in SECTORES.items() if cfg["patron"].search(nn)), None)
        sec = asignacion[cuerpo]
        if sec is None:
            for s, cfg in SOLO_LISTA.items():
                nn = _norm(nombre)
                if cuerpo.isdigit() and cuerpo not in listas[s] and cfg["patron"].search(nn) and not cfg["excluir"].search(nn):
                    candidatos[s][f"{cuerpo}-{dv(cuerpo)}"] = nombre
            continue
        tabla = next((t for t, pref in TABLAS.items() if estado.startswith(pref)), None)
        if tabla is None:
            continue  # flujos de efectivo y otros estados: no se publican
        if len(c) != 9 or tipo not in TIPO_BALANCE or not cuenta:
            avisos.append(f"línea {n}: esquema inesperado ({cuerpo})")
            continue
        clave = (cuerpo, tipo, moneda, estado)
        orden[clave] = orden.get(clave, 0) + 1
        k2 = clave + (tax, cuenta)
        repet[k2] = repet.get(k2, 0) + 1
        entero = re.fullmatch(r"-?\d+", valor) is not None
        datos[sec][tabla].append({
            "periodo": f"{per[:4]}-{per[4:]}", "rut": cuerpo, "rut_dv": f"{cuerpo}-{dv(cuerpo)}" if cuerpo.isdigit() else cuerpo,
            "razon_social": nombre, "tipo_balance": TIPO_BALANCE[tipo], "moneda": moneda,
            "estado_financiero": estado, "orden": orden[clave], "cuenta": cuenta,
            "valor": int(valor) if entero else None, "valor_no_numerico": None if entero else valor[:200],
            "repeticion": repet[k2], "taxonomia": tax, "en_lista_entidades": cuerpo in listas[sec],
        })
    if lineas_periodo == 0:
        raise ErrorFuente(f"el archivo no trae filas de {periodo}")
    if len(entidades_archivo) < 50:
        raise ErrorFuente(f"el archivo trae solo {len(entidades_archivo)} sociedades")
    return datos, {"lineas": lineas_periodo, "sociedades": len(entidades_archivo),
                   "solo_lista_fuera": {s: [{"rut": r, "razon_social": n} for r, n in sorted(v.items())]
                                        for s, v in candidatos.items()}}, avisos


def ruta_tabla(sec: str, tabla: str) -> Path:
    cfg = SECTORES[sec]
    return DOCS / cfg["carpeta"] / f"{cfg['prefijo']}_{tabla}"


def escribir(sec: str, tabla: str, periodo: str, filas: list[dict]) -> None:
    carpeta = ruta_tabla(sec, tabla)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{periodo[:4]}.parquet"
    per = f"{periodo[:4]}-{periodo[4:]}"
    partes = []
    if ruta.exists():
        viejo = pq.read_table(ruta).to_pandas()
        partes.append(viejo[viejo["periodo"] != per])
    partes.append(pd.DataFrame(filas, columns=ESQUEMA.names))
    partes = [p for p in partes if len(p)]
    if not partes:
        ruta.unlink(missing_ok=True)
        return
    df = pd.concat(partes, ignore_index=True)
    df = df.sort_values(["periodo", "rut", "tipo_balance", "estado_financiero", "orden"], kind="stable")
    for col, tipo in (("orden", "int32"), ("repeticion", "int16")):
        df[col] = df[col].astype(tipo)
    df["valor"] = df["valor"].astype("Int64")
    tmp = ruta.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pandas(df, schema=ESQUEMA, preserve_index=False), tmp,
                   compression="zstd", compression_level=9)
    os.replace(tmp, ruta)


def refrescar_marcas(listas: dict[str, dict[str, str]], control: dict) -> int:
    """Recalcula en_lista_entidades de todo lo publicado contra la lista vigente (la lista crece
    con pipelines/entidades); reescribe solo los años que cambian. Devuelve archivos reescritos."""
    cambios = 0
    for sec in SECTORES:
        for tabla in TABLAS:
            for ruta in sorted(ruta_tabla(sec, tabla).glob("*.parquet")):
                t = pq.read_table(ruta)
                ruts = t.column("rut").to_pylist()
                nueva = [r in listas[sec] for r in ruts]
                if nueva == t.column("en_lista_entidades").to_pylist():
                    continue
                t = t.set_column(t.schema.get_field_index("en_lista_entidades"), "en_lista_entidades",
                                 pa.array(nueva, pa.bool_()))
                tmp = ruta.with_suffix(".tmp")
                pq.write_table(t, tmp, compression="zstd", compression_level=9)
                os.replace(tmp, ruta)
                cambios += 1
    for per in control["periodos"].values():
        for sec, r in per.get("sectores", {}).items():
            if "fuera_de_lista" in r:
                r["fuera_de_lista"] = [e for e in r["fuera_de_lista"] if e["rut"].split("-")[0] not in listas[sec]]
        for sec, lst in per.get("solo_lista_fuera", {}).items():
            per["solo_lista_fuera"][sec] = [e for e in lst if e["rut"].split("-")[0] not in listas.get(sec, {})]
    if cambios:
        print(f"Marca en_lista_entidades actualizada en {cambios} archivos")
    return cambios


def escribir_manifiestos(control: dict) -> None:
    periodos = sorted(control["periodos"])
    for sec, cfg in SECTORES.items():
        for tabla in TABLAS:
            carpeta = ruta_tabla(sec, tabla)
            carpeta.mkdir(parents=True, exist_ok=True)
            rutas = sorted(carpeta.glob("*.parquet"))
            con = [p for p in periodos if control["periodos"][p]["sectores"][sec]["entidades"]]
            man = {"tabla": f"{cfg['prefijo']}_{tabla}",
                   "files": [f"outputs/{cfg['carpeta']}/{carpeta.name}/{r.name}" for r in rutas],
                   "total_records": sum(pq.ParquetFile(r).metadata.num_rows for r in rutas),
                   "periodos": [f"{p[:4]}-{p[4:]}" for p in con],
                   "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            (carpeta / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")


def cargar_control() -> dict:
    return json.loads(CONTROL.read_text()) if CONTROL.exists() else {"periodos": {}}


def guardar_control(control: dict) -> None:
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    control["periodos"] = dict(sorted(control["periodos"].items()))
    control["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    CONTROL.write_text(json.dumps(control, ensure_ascii=False, indent=2) + "\n")


ORIGEN = ("CMF — Estados financieros bajo estándar IFRS (TXT trimestral con todas las sociedades que envían "
          "estados financieros XBRL): https://www.cmfchile.cl/institucional/estadisticas/estadisticas_ifrs.php")
DESCRIPCION = {
    "balance": "Estado de situación financiera (ESF) de cada {q}, cuenta por cuenta, tal como lo publica la CMF. "
               "Montos en unidades de la moneda informada (CLP o USD), sin conversión.",
    "resultados": "Estado de resultados (ER, por función o naturaleza e integral) de cada {q}, cuenta por cuenta. "
                  "Montos acumulados del ejercicio a la fecha del trimestre, en unidades de la moneda informada.",
}
QUIEN = {"agf": "administradora general de fondos", "securitizadoras": "sociedad securitizadora",
         "cajas_compensacion": "caja de compensación de asignación familiar"}


def actualizar_data_manifest(control: dict) -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    hoy = date.today().isoformat()
    nuevas = []
    for sec, cfg in SECTORES.items():
        for tabla in TABLAS:
            carpeta = ruta_tabla(sec, tabla)
            m = carpeta / "manifest.json"
            if not m.exists():
                continue
            mm = json.loads(m.read_text())
            per = mm["periodos"]
            vista = f"{cfg['prefijo']}_{tabla}"
            nuevas.append({
                "id": vista, "name": f"{cfg['prefijo']}.{tabla}", "view_name": vista, "sector": sec,
                "sector_label": cfg["etiqueta"], "norma": "IFRS · archivo TXT de estados financieros CMF",
                "corte": f"{per[0]} a {per[-1]}" if per else "sin trimestres",
                "frescura": f"Último trimestre publicado: {per[-1]}" if per else "",
                "modo": "Automático · 3 veces al mes, incremental", "ultima_actualizacion": hoy,
                "file_parquet": f"outputs/{cfg['carpeta']}/{carpeta.name}/manifest.json",
                "registros_reales": mm["total_records"],
                "descripcion": DESCRIPCION[tabla].format(q=QUIEN[sec]), "origen": ORIGEN,
            })
    ids = {e["id"] for e in nuevas} | {"securitizadoras_balance_resumen", "ccaf_caratula_totales"}
    man["tables"] = [t for t in man["tables"] if t["id"] not in ids] + nuevas
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    ruta.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")


def guardar_lista(rel: str, filas: list[dict]) -> None:
    js = DOCS / rel
    js.write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pqt = js.with_suffix(".parquet")
    if pqt.exists():
        esquema = pq.read_schema(pqt)
        df = pd.DataFrame(filas).reindex(columns=esquema.names)
        for campo in esquema:
            if pa.types.is_integer(campo.type):
                df[campo.name] = pd.to_numeric(df[campo.name], errors="coerce").astype("Int64")
            elif pa.types.is_boolean(campo.type):
                df[campo.name] = df[campo.name].fillna(False).astype(bool)
        pq.write_table(pa.Table.from_pandas(df, schema=esquema.remove_metadata(), preserve_index=False), pqt)


def agregar_altas(fuera: dict[str, list[dict]], periodo: str) -> int:
    """Agrega a la lista las sociedades del último trimestre que calzan con el giro y no están."""
    eventos = []
    for s, lst in fuera.items():
        cfg = SECTORES.get(s) or SOLO_LISTA.get(s)
        if not cfg or "alta" not in cfg or not lst:
            continue
        filas = json.loads((DOCS / cfg["lista"]).read_text(encoding="utf-8"))
        ya = {str(f[cfg["clave_rut"]]).replace(".", "").split("-")[0] for f in filas}
        columnas = list(filas[0].keys())
        pendientes = [e for e in lst if e["rut"].split("-")[0] not in ya]
        if len(pendientes) > MAX_ALTAS:
            print(f"::warning::{s}: {len(pendientes)} sociedades calzan con el giro y no están en la lista; "
                  f"más de {MAX_ALTAS} en una corrida sugiere un patrón demasiado amplio: no se agrega ninguna")
            continue
        for e in lst:
            c, d = e["rut"].split("-")
            if c in ya or not c.isdigit():
                continue
            alta = cfg["alta"](c, d, e["razon_social"])
            filas.append({k: alta.get(k) for k in columnas})
            ya.add(c)
            eventos.append({"fecha": date.today().isoformat(), "sector": s, "lista": cfg["lista"].removesuffix(".json"),
                            "rut": e["rut"], "razon_social": e["razon_social"], "evento": "alta",
                            "antes": None, "ahora": f"reporta IFRS en {periodo}"})
            print(f"::notice::{s}: alta {e['rut']} {e['razon_social']} (reporta IFRS en {periodo})")
        if any(ev["sector"] == s for ev in eventos):
            guardar_lista(cfg["lista"], filas)
    if eventos:
        NOVEDADES.parent.mkdir(parents=True, exist_ok=True)
        hist = json.loads(NOVEDADES.read_text()) if NOVEDADES.exists() else {"eventos": []}
        hist["eventos"] = hist["eventos"] + eventos
        NOVEDADES.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n")
    return len(eventos)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--minutos", type=float, default=40)
    ap.add_argument("--max-periodos", type=int, default=200)
    ap.add_argument("--solo-data-manifest", action="store_true")
    a = ap.parse_args(argv)
    control = cargar_control()
    if a.solo_data_manifest:
        actualizar_data_manifest(control)
        return 0
    inicio = time.monotonic()
    hoy = date.today()
    listas = cargar_listas()
    indice = _get(INDICE)
    periodos, anual = periodos_indice(indice)
    pendientes = [p for p in periodos if p not in control["periodos"] or not control["periodos"][p].get("cerrado")]
    print(f"Índice CMF: {len(periodos)} trimestres ({periodos[0]}..{periodos[-1]}). "
          f"Procesados y cerrados: {len(periodos) - len(pendientes)}. A leer ahora: {len(pendientes)}")
    cache_anual: dict[tuple, bytes] = {}
    hechos, errores = 0, []
    for periodo in pendientes[:a.max_periodos]:
        if time.monotonic() - inicio > a.minutos * 60:
            print(f"Tiempo agotado ({a.minutos:.0f} min); el resto sigue en la próxima corrida.")
            break
        url = ARCHIVO.format(periodo, periodo)
        try:
            try:
                raw = _get(url)
                datos, est, avisos = leer_archivo(raw, periodo, listas)
            except ErrorFuente as e:
                if periodo not in anual:
                    raise
                par = anual[periodo]
                url = ARCHIVO.format(*par)
                if par not in cache_anual:
                    cache_anual[par] = _get(url)
                raw = cache_anual[par]
                datos, est, avisos = leer_archivo(raw, periodo, listas)
                avisos.insert(0, f"trimestre leído del archivo anual ({e})")
        except ErrorFuente as e:
            errores.append(f"{periodo}: {e}")
            print(f"::warning::{periodo}: {e}")
            continue
        # Cuadratura contable (README §4): activos = pasivos + patrimonio. Un balance aislado que
        # no cuadra queda como aviso; si la lectura falla en bloque (≥3 y más del 5 %), el trimestre no se publica.
        verificados, descuadres = 0, []
        for sec in SECTORES:
            v, malos = cuadratura.verificar_ifrs(datos[sec]["balance"])
            verificados += v
            descuadres += [f"{sec} {m}" for m in malos]
        if cuadratura.debe_detener(verificados, descuadres):
            errores.append(f"{periodo}: {len(descuadres)} de {verificados} balances no cuadran")
            print(f"::warning::{periodo}: {len(descuadres)} de {verificados} balances no cuadran "
                  f"(activos ≠ pasivos + patrimonio); no se publica. Ej.: {descuadres[0]}")
            continue
        avisos += [f"balance no cuadra: {m}" for m in descuadres]
        est["balances_verificados"], est["balances_descuadrados"] = verificados, len(descuadres)
        previo = control["periodos"].get(periodo, {}).get("sectores", {})
        resumen = {}
        for sec in SECTORES:
            ents = sorted({f["rut"] for t in TABLAS for f in datos[sec][t]})
            antes = previo.get(sec, {}).get("entidades", 0)
            if len(ents) < antes:
                # Una relectura nunca debe perder entidades: se conserva lo ya publicado.
                avisos.append(f"{sec}: la relectura trae {len(ents)} entidades (antes {antes}); se mantiene lo anterior")
                resumen[sec] = previo[sec]
                continue
            for tabla in TABLAS:
                escribir(sec, tabla, periodo, datos[sec][tabla])
            fuera = sorted({(f["rut_dv"], f["razon_social"]) for t in TABLAS for f in datos[sec][t]
                            if not f["en_lista_entidades"]})
            resumen[sec] = {"entidades": len(ents),
                            "filas": {t: len(datos[sec][t]) for t in TABLAS},
                            "fuera_de_lista": [{"rut": r, "razon_social": n} for r, n in fuera]}
        control["periodos"][periodo] = {
            "cerrado": cerrado(periodo, hoy), "leido_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fuente": url, "sha256": hashlib.sha256(raw).hexdigest(), **est,
            "sectores": resumen, "avisos": avisos[:20],
        }
        guardar_control(control)
        hechos += 1
        print(f"{periodo}: {est['sociedades']} sociedades · " +
              " · ".join(f"{s} {r['entidades']} ent. ({r['filas']['balance']}+{r['filas']['resultados']} filas)"
                         for s, r in resumen.items()) + (f" · {len(avisos)} avisos" if avisos else ""))
    hechos += refrescar_marcas(listas, control)
    # Entidades del giro presentes en el último trimestre que no están en la lista: las CCAF y
    # factoring/leasing se agregan solas; AGF y securitizadoras entran por el registro CMF
    # (pipelines/entidades), aquí solo se avisan.
    if control["periodos"]:
        ult = max(control["periodos"])
        fuera = {s: r.get("fuera_de_lista", []) for s, r in control["periodos"][ult]["sectores"].items()}
        fuera.update(control["periodos"][ult].get("solo_lista_fuera", {}))
        if agregar_altas(fuera, ult):
            listas = cargar_listas()
            hechos += 1 + refrescar_marcas(listas, control)
        nuevas = {s: r.get("fuera_de_lista", []) for s, r in control["periodos"][ult]["sectores"].items()}
        control["entidades_fuera_de_lista_ultimo_trimestre"] = {"periodo": ult, **nuevas}
        for s, lst in nuevas.items():
            for e in lst:
                print(f"::notice::{s}: {e['rut']} {e['razon_social']} reporta en {ult} y no está en la lista de entidades")
        guardar_control(control)
    escribir_manifiestos(control)
    actualizar_data_manifest(control)
    print(f"Trimestres leídos en esta corrida: {hechos}. Errores: {len(errores)}")
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"publicados={hechos}\n")
    return 1 if errores and not hechos else 0


if __name__ == "__main__":
    sys.exit(main())

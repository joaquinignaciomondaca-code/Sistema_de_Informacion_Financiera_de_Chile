"""Actualiza la cartera de inversiones de los fondos mutuos (CMF, Circular 1333).

La CMF entrega por mes un archivo CSV (separador ";") por tipo de cartera:
  NACI  inversiones en emisores nacionales        -> cartera_nacional
  EXTR  inversiones en emisores extranjeros       -> cartera_extranjera
  FUTU  contratos de futuro y forward             -> futuros_forwards
  OPCI  contratos de opciones                     -> opciones
(OPLA, opciones en que el fondo es lanzador, viene vacía en todos los meses revisados.)

Incremental: solo procesa los meses que faltan en docs/outputs/ffmm/manifest.json.
Antes de escribir un mes se valida (fail-closed):
  - el encabezado es exactamente el de la Circular 1333 (códigos FFM_...),
  - números y fechas se pueden leer (si más del 1 % de las filas tiene campos ilegibles,
    el mes no se publica),
  - el mes está completo: la cartera nacional trae al menos el 90 % de los fondos del mes
    anterior publicado (si no, se espera a la próxima corrida).

Los montos van en miles de la moneda funcional de cada fondo (sufijo _miles_mf), como
exige la circular: no siempre son pesos.

Salida:
  docs/outputs/ffmm/cartera_nacional/<AAAA-MM>.parquet    (un archivo por mes)
  docs/outputs/ffmm/<tabla>/<AAAA>.parquet                (resto: un archivo por año)
  docs/outputs/ffmm/<tabla>/manifest.json
  docs/outputs/ffmm/maestro_fondos_mutuos.parquet  (lista de fondos que reportan cartera:
                                                    primer y último mes; detecta fondos nuevos)
  docs/outputs/ffmm/manifest.json            (control de meses publicados)
"""
from __future__ import annotations

import argparse
import io
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipelines.auto import estable  # noqa: E402
from pipelines.auto.rut import normalizar_dataframe  # noqa: E402

SALIDA = RAIZ / "docs" / "outputs" / "ffmm"
URL = "https://www.cmfchile.cl/institucional/estadisticas/ffm_download.php"
REFERER = "https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php"

# (columna, código CMF, tipo) · t texto, n número, f fecha DD/MM/AAAA
_COMUNES = [("run_fondo", "RUN FONDO", "t"), ("nombre_fondo", "NOMBRE FONDO", "t")]
CARTERAS = {
    "NACI": ("cartera_nacional", _COMUNES + [
        ("nemotecnico", "FFM_6010100", "t"), ("rut_emisor", "FFM_6010211", "t"), ("dv_emisor", "FFM_6010212", "t"),
        ("pais_emisor", "FFM_6010300", "t"), ("tipo_instrumento", "FFM_6010400", "t"),
        ("fecha_vencimiento", "FFM_6010500", "f"), ("situacion_instrumento", "FFM_6010600", "t"),
        ("clasificacion_riesgo", "FFM_6010700", "t"), ("codigo_grupo_empresarial", "FFM_6010800", "t"),
        ("cantidad_unidades", "FFM_6010900", "n"), ("tipo_unidades", "FFM_6011000", "t"),
        ("tir_pct", "FFM_TIR_6011111", "n"), ("valor_par_pct", "FFM_PAR_6011111", "n"),
        ("valor_relevante", "FFM_REL_6011111", "n"), ("codigo_valorizacion", "FFM_6011112", "t"),
        ("base_tasa_dias", "FFM_6011113", "n"), ("tipo_interes", "FFM_6011114", "t"),
        ("valorizacion_miles_mf", "FFM_6011200", "n"), ("moneda_liquidacion", "FFM_6011300", "t"),
        ("pais_transaccion", "FFM_6011400", "t"), ("pct_capital_emisor", "FFM_6011511", "n"),
        ("pct_activo_emisor", "FFM_6011512", "n"), ("pct_activo_fondo", "FFM_6011513", "n")]),
    "EXTR": ("cartera_extranjera", _COMUNES + [
        ("nemotecnico", "FFM_6020100", "t"), ("nombre_emisor", "FFM_6020200", "t"),
        ("pais_emisor", "FFM_6020300", "t"), ("tipo_instrumento", "FFM_6020400", "t"),
        ("fecha_vencimiento", "FFM_6020500", "f"), ("situacion_instrumento", "FFM_6020600", "t"),
        ("clasificacion_riesgo", "FFM_6020700", "t"), ("grupo_empresarial", "FFM_6020800", "t"),
        ("cantidad_unidades", "FFM_6020900", "n"), ("tipo_unidades", "FFM_6021000", "t"),
        ("tir_pct", "FFM_TIR_6021111", "n"), ("valor_par_pct", "FFM_PAR_6021111", "n"),
        ("valor_relevante", "FFM_REL_6021111", "n"), ("codigo_valorizacion", "FFM_6021112", "t"),
        ("base_tasa_dias", "FFM_6021113", "n"), ("tipo_interes", "FFM_6021114", "t"),
        ("valorizacion_miles_mf", "FFM_6021200", "n"), ("moneda_liquidacion", "FFM_6021300", "t"),
        ("pais_transaccion", "FFM_6021400", "t"), ("pct_capital_emisor", "FFM_6021511", "n"),
        ("pct_activo_emisor", "FFM_6021512", "n"), ("pct_activo_fondo", "FFM_6021513", "n")]),
    "FUTU": ("futuros_forwards", _COMUNES + [
        ("activo_objeto", "FFM_6040111", "t"), ("nemotecnico", "FFM_6040112", "t"),
        ("unidad_cotizacion", "FFM_6040113", "t"), ("fecha_vencimiento", "FFM_6040114", "f"),
        ("moneda_liquidacion", "FFM_6040115", "t"), ("pais", "FFM_6040116", "t"),
        ("posicion", "FFM_6040200", "t"), ("unidades_nominales", "FFM_6040300", "n"),
        ("precio_futuro", "FFM_6040400", "n"), ("monto_comprometido_miles_mf", "FFM_6040500", "n"),
        ("valorizacion_mercado_miles_mf", "FFM_6040600", "n")]),
    "OPCI": ("opciones", _COMUNES + [
        ("activo_objeto", "FFM_6030111", "t"), ("nemotecnico", "FFM_6030112", "t"),
        ("forma_ejercicio", "FFM_6030113", "t"), ("fecha_expiracion", "FFM_6030114", "f"),
        ("moneda_liquidacion", "FFM_6030115", "t"), ("pais", "FFM_6030116", "t"),
        ("tipo_opcion", "FFM_6030200", "t"), ("valor_mercado_unitario_prima", "FFM_6030300", "n"),
        ("numero_contratos", "FFM_6030400", "n"), ("precio_ejercicio", "FFM_6030500", "n"),
        ("valor_mercado_activo_objeto", "FFM_6030600", "n"), ("unidades_activo_objeto", "FFM_6030700", "n"),
        ("inversion_primas_miles_mf", "FFM_6030800", "n"),
        ("valorizacion_precio_ejercicio_miles_mf", "FFM_6030900", "n"),
        ("valorizacion_mercado_miles_mf", "FFM_6031000", "n"), ("pct_primas_activo_fondo", "FFM_6031100", "n")]),
}
TABLAS = [v[0] for v in CARTERAS.values()]
DESDE = "2001-01"
# La cartera nacional pesa ~0,5 MB por mes: parte más tarde. Para extenderla basta con cambiar
# la fecha; la próxima corrida completa solo lo que falta de esa tabla.
DESDE_TABLA = {"cartera_nacional": "2022-01"}
POR_MES = {"cartera_nacional"}
ORDEN = {"cartera_nacional": ["tipo_instrumento", "nemotecnico"], "cartera_extranjera": ["nemotecnico"],
         "futuros_forwards": ["activo_objeto", "fecha_vencimiento"], "opciones": ["nemotecnico"]}
ORIGEN = ("CMF — Cartera de inversiones de fondos mutuos (Circular 1333), archivo mensual de "
          "https://www.cmfchile.cl/institucional/estadisticas/ffm_cartera.php")
# id de vista -> (tabla o None para la lista de fondos, nombre, descripción)
WEB = {
    "ffmm_maestro": (None, "ffmm.lista_entidades", "Fondos mutuos que reportan cartera a la CMF: RUN, nombre vigente, "
                     "primer y último mes informado y si reportó el último mes publicado (un fondo nuevo aparece aquí "
                     "el mes en que informa por primera vez)."),
    "ffmm_cartera_nacional": ("cartera_nacional", "ffmm.cartera_nacional", "Inversiones de cada fondo en instrumentos "
                              "de emisores nacionales, instrumento por instrumento, al cierre de cada mes. Montos en "
                              "miles de la moneda funcional del fondo."),
    "ffmm_cartera_extranjera": ("cartera_extranjera", "ffmm.cartera_extranjera", "Inversiones de cada fondo en "
                                "instrumentos de emisores extranjeros al cierre de cada mes. Montos en miles de la "
                                "moneda funcional del fondo."),
    "ffmm_futuros": ("futuros_forwards", "ffmm.futuros_forwards", "Contratos de futuro y forward vigentes de cada "
                     "fondo al cierre de cada mes. Montos en miles de la moneda funcional del fondo."),
    "ffmm_opciones": ("opciones", "ffmm.opciones", "Contratos de opciones vigentes de cada fondo al cierre de cada "
                      "mes. Montos en miles de la moneda funcional del fondo."),
}
DIAS_ESPERA = 12        # la circular da 5 días hábiles para informar
COBERTURA_MINIMA = 0.90  # fondos en la cartera nacional respecto del mes anterior


class NoPublicado(Exception):
    pass


class ErrorValidacion(Exception):
    pass


def esquema(tabla: str) -> pa.Schema:
    cod = next(k for k, v in CARTERAS.items() if v[0] == tabla)
    cols = [("periodo", pa.string())]
    for c, _, t in CARTERAS[cod][1]:
        if c == "dv_emisor":
            continue
        cols.append((c, pa.float64() if t == "n" else pa.string()))
    return pa.schema(cols)


# ---------------------------------------------------------------------------
def _post(cartera: str, periodo: str, timeout: int = 120) -> bytes:
    data = urllib.parse.urlencode({"aa": periodo[:4], "mm": periodo[5:], "cartera": cartera,
                                   "btnConsulta": "GENERAR ARCHIVO"}).encode()
    req = urllib.request.Request(URL, data=data, headers={
        "User-Agent": "Mozilla/5.0 (monitor-financiero-chile)", "Referer": REFERER,
        "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def descargar(cartera: str, periodo: str, cache: Path | None) -> bytes:
    nombre = f"{cartera}_{periodo.replace('-', '')}.txt"
    if cache is not None and (cache / nombre).exists():
        return (cache / nombre).read_bytes()
    for intento in range(1, 4):
        try:
            data = _post(cartera, periodo)
            break
        except Exception as e:
            if intento == 3:
                raise
            print(f"  reintento {intento} {nombre}: {e}")
            time.sleep(10 * intento)
    if cache is not None:
        cache.mkdir(parents=True, exist_ok=True)
        (cache / nombre).write_bytes(data)
    return data


def _num(txt: str):
    s = txt.strip()
    if s in ("", "NA", "-"):
        return None
    if not re.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)", s):
        raise ValueError(f"número {txt!r}")
    return float(s)


def _fecha(txt: str):
    s = txt.strip()
    if s in ("", "99999999", "NA", "-") or s.endswith("9999"):
        return None
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        raise ValueError(f"fecha {txt!r}")
    d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    datetime(y, mth, d)  # valida día y mes
    return f"{y:04d}-{mth:02d}-{d:02d}"


def leer(cartera: str, raw: bytes, periodo: str) -> tuple[pd.DataFrame, list[str]]:
    """Devuelve las filas del mes (vacío si la CMF no trae datos) y los avisos."""
    tabla, cols = CARTERAS[cartera]
    try:
        texto = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = raw.decode("latin-1")
    lineas = [ln for ln in texto.replace("\r", "").split("\n") if ln.strip()]
    if not lineas or not lineas[0].upper().startswith("RUN FONDO"):
        if len(texto.strip()) < 200:  # "Sin información": mes sin datos para esta cartera
            return pd.DataFrame(columns=esquema(tabla).names), []
        raise ErrorValidacion(f"{cartera} {periodo}: respuesta sin encabezado ({texto[:80]!r})")
    encabezado = [h.strip().upper() for h in lineas[0].split(";")]
    esperado = [c[1] for c in cols]
    if encabezado != esperado:
        raise ErrorValidacion(f"{cartera} {periodo}: encabezado distinto al de la Circular 1333: {encabezado}")
    filas, malas, avisos = [], [], []
    for n, ln in enumerate(lineas[1:], start=2):
        partes = ln.split(";")
        if len(partes) != len(esperado):
            malas.append(f"línea {n}: {len(partes)} campos en vez de {len(esperado)}")
            continue
        fila, malo = {"periodo": periodo}, None
        for (c, _, t), v in zip(cols, partes):
            try:
                fila[c] = _num(v) if t == "n" else _fecha(v) if t == "f" else (v.strip() or None)
            except ValueError as e:
                fila[c] = None
                malo = malo or f"{c} ({e})"
        if malo:
            malas.append(f"línea {n}: {malo}")
        if "dv_emisor" in fila:
            dv = fila.pop("dv_emisor")
            if fila.get("rut_emisor"):
                fila["rut_emisor"] = f"{fila['rut_emisor']}-{dv}" if dv else fila["rut_emisor"]
        filas.append(fila)
    if len(malas) > 0.01 * max(len(filas), 1):
        raise ErrorValidacion(f"{cartera} {periodo}: {len(malas)} de {len(filas)} filas con problemas "
                              f"(más del 1 %):\n  - " + "\n  - ".join(malas[:15]))
    avisos += [f"{cartera}: {m}" for m in malas]
    return pd.DataFrame(filas).reindex(columns=esquema(tabla).names), avisos


# ---------------------------------------------------------------------------
def ruta_particion(tabla: str, periodo: str) -> Path:
    return SALIDA / tabla / (f"{periodo}.parquet" if tabla in POR_MES else f"{periodo[:4]}.parquet")


def escribir(tabla: str, periodo: str, nuevo: pd.DataFrame) -> int:
    ruta = ruta_particion(tabla, periodo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    partes = []
    if ruta.exists():
        viejo = pq.read_table(ruta).to_pandas()
        partes.append(viejo[viejo["periodo"] != periodo])
    partes.append(nuevo)
    partes = [p for p in partes if len(p)]
    if not partes:
        return 0
    df = pd.concat(partes, ignore_index=True).reindex(columns=esquema(tabla).names)
    df = df.sort_values(["periodo", "run_fondo"] + ORDEN.get(tabla, []), kind="stable", na_position="first")
    df = normalizar_dataframe(df)  # convención de RUT (pipelines/auto/rut.py)
    tmp = ruta.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pandas(df, schema=esquema(tabla), preserve_index=False), tmp,
                   compression="zstd", compression_level=9)
    os.replace(tmp, ruta)
    return len(nuevo)


def escribir_manifiestos(control: dict) -> None:
    for tabla in TABLAS:
        (SALIDA / tabla).mkdir(parents=True, exist_ok=True)
        rutas = sorted((SALIDA / tabla).glob("*.parquet"))
        periodos = sorted(p for p, v in control["periodos"].items() if tabla in v["registros"])
        man = {"tabla": tabla, "files": [f"outputs/ffmm/{tabla}/{r.name}" for r in rutas],
               "total_records": sum(pq.ParquetFile(r).metadata.num_rows for r in rutas), "periodos": periodos,
               "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        estable.escribir_json((SALIDA / tabla / "manifest.json"), man)
    filas = [{"run_fondo": run, "nombre_fondo": i["nombre"], "primer_periodo": i["primer"],
              "ultimo_periodo": i["ultimo"], "meses_reportados": i["meses"]}
             for run, i in sorted(control["fondos"].items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)]
    if filas:
        df = pd.DataFrame(filas)
        df["reporta_ultimo_mes"] = df["ultimo_periodo"] == max(control["periodos"])
        pq.write_table(pa.Table.from_pandas(df, preserve_index=False), SALIDA / "maestro_fondos_mutuos.parquet",
                       compression="zstd")


def actualizar_data_manifest(control: dict) -> None:
    """Mantiene al día las entradas de fondos mutuos en data_manifest.json."""
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    hoy = date.today().isoformat()
    entradas = []
    for vista, (tabla, nombre, descripcion) in WEB.items():
        if tabla is None:
            archivo = "outputs/ffmm/maestro_fondos_mutuos.parquet"
            registros = pq.ParquetFile(SALIDA / "maestro_fondos_mutuos.parquet").metadata.num_rows
            periodos = sorted(control["periodos"])
        else:
            archivo = f"outputs/ffmm/{tabla}/manifest.json"
            m = json.loads((SALIDA / tabla / "manifest.json").read_text())
            registros, periodos = m["total_records"], m["periodos"]
        entradas.append({
            "id": vista, "name": nombre, "view_name": vista, "sector": "ffmm", "sector_label": "Fondos Mutuos",
            "norma": "Circular CMF 1333",
            "corte": f"{periodos[0]} a {periodos[-1]}" if periodos else "sin meses publicados",
            "frescura": f"Último mes publicado: {periodos[-1]}" if periodos else "",
            "modo": "Automático · 3 veces al mes, incremental", "ultima_actualizacion": hoy,
            "file_parquet": archivo, "registros_reales": registros, "descripcion": descripcion, "origen": ORIGEN,
        })
    ids = {e["id"] for e in entradas}
    resto = [t for t in man["tables"] if t["id"] not in ids]
    man["tables"] = entradas + resto
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    estable.escribir_json(ruta, man)


def cargar_control() -> dict:
    ruta = SALIDA / "manifest.json"
    if ruta.exists():
        return json.loads(ruta.read_text())
    return {"periodos": {}, "fondos": {}}


def guardar_control(control: dict) -> None:
    control["periodos"] = dict(sorted(control["periodos"].items()))
    control["desde"] = {t: DESDE_TABLA.get(t, DESDE) for t in TABLAS}
    control["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    estable.escribir_json((SALIDA / "manifest.json"), control)


def meses(desde: str, hasta: str) -> list[str]:
    y, m = map(int, desde.split("-"))
    out = []
    while f"{y}-{m:02d}" <= hasta:
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def ultimo_mes_disponible(hoy: date | None = None) -> str:
    """Último mes cuyo plazo de envío ya pasó (fin de mes + DIAS_ESPERA)."""
    hoy = hoy or date.today()
    d = hoy - timedelta(days=DIAS_ESPERA)
    y, m = (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)
    return f"{y}-{m:02d}"


def procesar_mes(periodo: str, tablas: list[str], control: dict, cache: Path | None, escribir_datos: bool,
                 reciente: bool = True):
    datos, avisos = {}, []
    cods = [c for c, (t, _) in CARTERAS.items() if t in tablas or c == "NACI"]
    with ThreadPoolExecutor(max_workers=len(cods)) as ex:
        crudos = dict(zip(cods, ex.map(lambda c: descargar(c, periodo, cache), cods)))
    for cod in cods:
        df, av = leer(cod, crudos[cod], periodo)
        datos[CARTERAS[cod][0]], avisos = df, avisos + av
    nac = datos["cartera_nacional"]
    # En los meses recientes la falta de datos significa "aún no publicado" (se espera); en los
    # antiguos es una anomalía y se detiene con error para revisarla.
    Falta = NoPublicado if reciente else ErrorValidacion
    if nac.empty:
        raise Falta(f"{periodo}: la CMF no tiene la cartera nacional")
    fondos = nac["run_fondo"].nunique()
    previos = [v.get("fondos_nacional") for p, v in control["periodos"].items() if p < periodo]
    previo = next((x for x in reversed(previos) if x), None)
    if previo and fondos < COBERTURA_MINIMA * previo:
        raise Falta(f"{periodo}: solo {fondos} fondos en la cartera nacional (mes anterior {previo}); "
                          "se espera a que la CMF complete el mes")
    if not escribir_datos:
        return {t: len(d) for t, d in datos.items()}, avisos, fondos
    conteo = {t: escribir(t, periodo, datos[t]) for t in tablas}
    if periodo not in control["periodos"]:
        for df in (nac, datos.get("cartera_extranjera", pd.DataFrame())):
            for run, nombre in df[["run_fondo", "nombre_fondo"]].drop_duplicates("run_fondo").itertuples(index=False):
                i = control["fondos"].setdefault(run, {"nombre": nombre, "primer": periodo, "ultimo": periodo, "meses": 0})
                if i.get("_ultimo_contado") != periodo:
                    i["meses"] += 1
                    i["_ultimo_contado"] = periodo
                i["primer"] = min(i["primer"], periodo)
                if periodo >= i["ultimo"]:
                    i["ultimo"], i["nombre"] = periodo, nombre
    # SHA-256 de cada archivo tal como lo devolvió la CMF: deja en el manifiesto el rastro de
    # dónde sale lo publicado. Solo los meses publicados desde que se agregó tienen este campo.
    control["periodos"].setdefault(periodo, {"registros": {}, "avisos": 0}).setdefault(
        "sha256_origen", {}).update({c: hashlib.sha256(crudos[c]).hexdigest() for c in cods})
    return conteo, avisos, fondos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hasta", default=None)
    ap.add_argument("--max-periodos", type=int, default=400)
    ap.add_argument("--cache", type=Path, default=None, help="guardar/reusar las descargas en esta carpeta")
    ap.add_argument("--diagnostico", action="store_true", help="revisar los meses pendientes sin escribir")
    ap.add_argument("--solo-data-manifest", action="store_true",
                    help="solo recalcular las entradas de este sector en data_manifest.json")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest(cargar_control())
        return 0
    gha = bool(os.environ.get("GITHUB_ACTIONS"))
    SALIDA.mkdir(parents=True, exist_ok=True)
    control = cargar_control()
    pendientes = []
    for p in meses(min([DESDE] + list(DESDE_TABLA.values())), a.hasta or ultimo_mes_disponible()):
        hechas = set(control["periodos"].get(p, {}).get("registros", {}))
        faltan = [t for t in TABLAS if p >= DESDE_TABLA.get(t, DESDE) and t not in hechas]
        if faltan:
            pendientes.append((p, faltan))
    print(f"Meses publicados: {len(control['periodos'])}. Meses con tablas pendientes: {len(pendientes)}")
    hechos, malos = [], 0
    limite_reciente = meses("2000-01", a.hasta or ultimo_mes_disponible())[-3]
    for periodo, faltan in pendientes[:a.max_periodos]:
        try:
            conteo, avisos, fondos = procesar_mes(periodo, faltan, control, a.cache, not a.diagnostico,
                                                   reciente=periodo >= limite_reciente)
        except NoPublicado as e:
            print(f"{e}. Se retoma en la próxima corrida.")
            break
        except ErrorValidacion as e:
            if not a.diagnostico:
                raise
            malos += 1
            print(f"{periodo}: PROBLEMA · {e}")
            if gha:
                print(f"::warning title=Diagnóstico FFMM {periodo}::" + str(e).replace("\n", "%0A")[:1500])
            continue
        if a.diagnostico:
            print(f"{periodo}: OK · {fondos} fondos · " + ", ".join(f"{t} {n}" for t, n in conteo.items()))
            continue
        info = control["periodos"].setdefault(periodo, {"registros": {}, "avisos": 0})
        info["registros"].update(conteo)
        info["fondos_nacional"] = fondos
        info["avisos"] = len(avisos)
        info["detalle_avisos"] = avisos[:20]
        guardar_control(control)
        hechos.append(periodo)
        print(f"{periodo}: {fondos} fondos · " + ", ".join(f"{t} {n}" for t, n in conteo.items())
              + (f" · {len(avisos)} avisos" if avisos else ""))
    if a.diagnostico:
        msg = f"{len(pendientes[:a.max_periodos])} meses revisados, {malos} con problemas"
        print(msg)
        if gha:
            print(f"::notice title=Diagnóstico FFMM::{msg}")
        return 0
    if hechos:
        for i in control["fondos"].values():
            i.pop("_ultimo_contado", None)
        guardar_control(control)
        escribir_manifiestos(control)
        actualizar_data_manifest(control)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            fh.write(f"publicados={len(hechos)}\n")
    print(f"Listo: {len(hechos)} meses nuevos.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErrorValidacion as e:
        print(f"ERROR DE VALIDACIÓN (no se publicó el mes): {e}", file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS"):
            print("::error title=FFMM 1333::" + str(e).replace("\n", "%0A")[:3000])
        sys.exit(2)

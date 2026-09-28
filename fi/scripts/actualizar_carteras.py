"""Actualiza la cartera de inversiones de los fondos de inversión (CMF, informes IFRS trimestrales).

La CMF no publica un archivo masivo para fondos de inversión: cada fondo tiene, por trimestre,
una página por tipo de cartera (ifrs_cartera_*.php) y otra de pactos (ifrs_informe_vrc_crv.php).
Este script consulta todas las páginas de los fondos del registro CMF, trimestre a trimestre.

Incremental: solo procesa los trimestres que faltan en docs/outputs/fi/manifest.json.
Un trimestre se publica completo o no se publica (fail-closed):
  - cada página debe traer exactamente el encabezado esperado; números con formato chileno
    (1.234.567,89) y fechas DD/MM/AAAA; nada se rellena con ceros,
  - la suma de cada columna de montos debe cuadrar con la fila TOTAL que publica la CMF para
    ese fondo y cartera (si descuadra más del 2 % de los fondos con datos, el trimestre no se
    publica; los descuadres menores quedan como avisos),
  - más del 1 % de filas ilegibles o páginas inesperadas detiene el trimestre,
  - completitud: fondos con cartera >= 90 % de los del trimestre anterior (si no, se espera).

Montos en miles de la moneda funcional de cada fondo (sufijo _miles_mf); la moneda funcional
se lee del informe de pactos ("Cifras expresadas en miles de: ...") y va en la lista de fondos.

Salida (docs/outputs/fi/):
  cartera_nacional/<AAAA-MM>.parquet     un archivo por trimestre
  <tabla>/<AAAA>.parquet                 cartera_extranjera, metodo_participacion, bienes_raices,
                                         futuros_forwards, opciones, pactos: un archivo por año
  <tabla>/manifest.json, manifest.json (control)
  maestro_fondos_inversion.parquet       registro CMF (vigentes y no vigentes) + primer/último
                                         trimestre con cartera + moneda funcional
  fi_registro_fondos_universo.json       el mismo registro, formato que usa pipelines/xml_eeff
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "docs" / "outputs" / "fi"
UA = "Mozilla/5.0 (monitor-financiero-chile)"
BASE_CARTERA = "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/"
URL_PACTOS = "https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_informe_vrc_crv.php"
URL_LISTA = "https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado={estado}&entidad={tipo}"
TIPOS_FONDO = {"FINRE": "Fondo de Inversión No Rescatable", "FIRES": "Fondo de Inversión Rescatable"}

# código -> (tabla, página, [(encabezado CMF, columna, tipo)]) · t texto, n número, f fecha, r rut
CARTERAS = {
    "N": ("cartera_nacional", "ifrs_cartera_nac.php", [
        ("Clasif. del Instr. en ESF", "clasificacion_esf", "t"), ("Nemotécnico", "nemotecnico", "t"),
        ("Rut Emisor", "rut_emisor", "r"), ("Cod. País", "pais_emisor", "t"),
        ("Tipo Instrumento", "tipo_instrumento", "t"), ("Fecha Vencimiento", "fecha_vencimiento", "f"),
        ("Situación del Instr.", "situacion_instrumento", "t"), ("Clasif. De Riesgo", "clasificacion_riesgo", "t"),
        ("Grupo Empresarial", "codigo_grupo_empresarial", "t"), ("Cant Unidades", "cantidad_unidades", "n"),
        ("Tipo Unidades", "tipo_unidades", "t"), ("TIR, Valor par o Precio", "tir_valor_par_precio", "n"),
        ("Código Valolización", "codigo_valorizacion", "t"), ("Base tasa", "base_tasa_dias", "n"),
        ("Tipo de interés", "tipo_interes", "t"), ("Valolización al Cierre", "valorizacion_miles_mf", "n"),
        ("Cód. Moneda Liquidación", "moneda_liquidacion", "t"), ("Cód. Pais Transacción", "pais_transaccion", "t"),
        ("% Capital del Emisor", "pct_capital_emisor", "n"), ("% Tot. Activo del Emisor", "pct_activo_emisor", "n"),
        ("% Tot. Activo del Fondo", "pct_activo_fondo", "n")]),
    "E": ("cartera_extranjera", "ifrs_cartera_ext.php", [
        ("Clasif del Instrumento en ESF", "clasificacion_esf", "t"), ("Código ISIN o CUSIP", "isin", "t"),
        ("Nemotecnico", "nemotecnico", "t"), ("Nombre del emisor", "nombre_emisor", "t"),
        ("Cod. País", "pais_emisor", "t"), ("Tipo Instrumento", "tipo_instrumento", "t"),
        ("Fecha Vencimiento", "fecha_vencimiento", "f"), ("Situación del Instr.", "situacion_instrumento", "t"),
        ("Clasif. De Riesgo", "clasificacion_riesgo", "t"), ("Nombre Grupo Empr.", "grupo_empresarial", "t"),
        ("Cant Unidades", "cantidad_unidades", "n"), ("Tipo Unidades", "tipo_unidades", "t"),
        ("TIR, Valor par o Precio", "tir_valor_par_precio", "n"), ("Código Valolización", "codigo_valorizacion", "t"),
        ("Base tasa", "base_tasa_dias", "n"), ("Tipo de interés", "tipo_interes", "t"),
        ("Valolización al Cierre", "valorizacion_miles_mf", "n"), ("Cód. Moneda Liquidación", "moneda_liquidacion", "t"),
        ("Cód. Pais Transacción", "pais_transaccion", "t"), ("% Capital del Emisor", "pct_capital_emisor", "n"),
        ("% Tot. Activo del Emisor", "pct_activo_emisor", "n"), ("% Tot. Activo del Fondo", "pct_activo_fondo", "n")]),
    "M": ("metodo_participacion", "ifrs_cartera_met_part.php", [
        ("Código ISIN o CUSIP", "isin", "t"), ("Nombre del emisor", "nombre_emisor", "t"),
        ("Rut Emisor", "rut_emisor", "r"), ("Cod. País", "pais_emisor", "t"), ("Tipo Inst.", "tipo_instrumento", "t"),
        ("Sit. del Instr.", "situacion_instrumento", "t"), ("Cant. Uni.", "cantidad_unidades", "n"),
        ("% Cap. del Emi", "pct_capital_emisor", "n"), ("Patrimonio del Emi.", "patrimonio_emisor_miles_mf", "n"),
        ("Val. al Cierre", "valor_cierre_miles_mf", "n"), ("Prov. por Deterioro", "provision_deterioro_miles_mf", "n"),
        ("Plusvalías de la Inv.", "plusvalia_miles_mf", "n"), ("Cód. Mon. Liq.", "moneda_liquidacion", "t"),
        ("Cod Pais T", "pais_transaccion", "t"), ("% Act del Fondo", "pct_activo_fondo", "n")]),
    "B": ("bienes_raices", "ifrs_cartera_bie_rai.php", [
        ("Domicilio", "domicilio", "t"), ("Comuna", "comuna", "t"), ("Ciudad", "ciudad", "t"), ("Region", "region", "t"),
        ("Cod. País", "pais", "t"), ("Tipo BR", "tipo_bien_raiz", "t"), ("%. en Comunidades", "pct_comunidad", "n"),
        ("Destino", "destino", "t"), ("Tipo Renta", "tipo_renta", "t"),
        ("Prohibiciones o Garantías", "prohibiciones_garantias", "t"), ("Val. al cierre", "valor_cierre_miles_mf", "n"),
        ("Ajustes y Prohibiciones", "ajustes_prohibiciones_miles_mf", "n"), ("% act del fondo", "pct_activo_fondo", "n")]),
    "F": ("futuros_forwards", "ifrs_cartera_fut_fw.php", [
        ("Clasif del Instrumento en ESF", "clasificacion_esf", "t"), ("Activo Objeto", "activo_objeto", "t"),
        ("Nemotecnico", "nemotecnico", "t"), ("Unidad de Cotización", "unidad_cotizacion", "t"),
        ("Fecha Ini. Contr.", "fecha_inicio", "f"), ("Fecha Venc.", "fecha_vencimiento", "f"),
        ("Nombre Contraparte", "contraparte", "t"), ("Cód. Mon. Liq.", "moneda_liquidacion", "t"),
        ("Cod. País", "pais", "t"), ("Pos. Compra Venta", "posicion", "t"),
        ("Uni. Nominales Totales", "unidades_nominales", "n"), ("Precio Futuro Contrato", "precio_futuro", "n"),
        ("Monto Comprometido", "monto_comprometido_miles_mf", "n"), ("Val. Merc. Contrato", "valor_mercado_miles_mf", "n")]),
    "O": ("opciones", "ifrs_cartera_op.php", [
        ("Clasif del Instrumento en ESF", "clasificacion_esf", "t"), ("Activo Objeto", "activo_objeto", "t"),
        ("Nemotécnico", "nemotecnico", "t"), ("Forma de Ejercicio", "forma_ejercicio", "t"),
        ("Fecha Inicio Contr.", "fecha_inicio", "f"), ("Fecha Vencimiento", "fecha_vencimiento", "f"),
        ("Nombre Contraparte", "contraparte", "t"), ("Cód. Mon. Liq.", "moneda_liquidacion", "t"),
        ("Cod. País", "pais", "t"), ("Tipo Opción", "tipo_opcion", "t"),
        ("Val. Merc. Uni. Prima", "valor_mercado_unitario_prima", "n"), ("Num. Contratos", "numero_contratos", "n"),
        ("Precio Ejercicio", "precio_ejercicio", "n"), ("Val. Merc. Act. Obj.", "valor_mercado_activo_objeto", "n"),
        ("Num. Uni. Act. Obj.", "unidades_activo_objeto", "n"), ("Inversion Primas", "inversion_primas_miles_mf", "n"),
        ("Valorizacion Prec. Ejerc.", "valorizacion_precio_ejercicio_miles_mf", "n"),
        ("Valorizacion Mercado", "valorizacion_mercado_miles_mf", "n"),
        ("Porc. Inv. Prim. Act. Tot.Fondo", "pct_primas_activo_fondo", "n")]),
}
# Pactos: 12 encabezados, "Instrumento en compromiso" abarca 4 celdas (sub-encabezados).
PACTOS_TH = ["Código de Operación", "Fecha de Inicio", "Fecha de Término", "Nombre contraparte", "RUT contraparte",
             "Valor Inicial (1)", "Moneda de origen", "Tasa de Pacto (2)", "Valor final (1)",
             "Valorización al cierre (1)", "Instrumento en compromiso", "Valor de mercado (3)"]
PACTOS_SUB = ["Código ISIN o CUSIP", "Nemotécnico del instrumento", "Nombre del emisor", "Tipo de instrumento"]
PACTOS = [("tipo_operacion", "t"), ("fecha_inicio", "f"), ("fecha_termino", "f"), ("contraparte", "t"),
          ("rut_contraparte", "r"), ("valor_inicial_miles_mf", "n"), ("moneda_origen", "t"), ("tasa_pacto_pct", "n"),
          ("valor_final_miles_mf", "n"), ("valorizacion_cierre_miles_mf", "n"), ("isin", "t"), ("nemotecnico", "t"),
          ("nombre_emisor", "t"), ("tipo_instrumento", "t"), ("valor_mercado_miles_moneda", "n")]
TABLAS = [v[0] for v in CARTERAS.values()] + ["pactos"]
DESDE = "2020-03"
POR_PERIODO = {"cartera_nacional"}
DIAS_ESPERA = {3: 75, 6: 75, 9: 75, 12: 100}  # EEFF trimestrales: 60 días; anuales: 90 días
COBERTURA_MINIMA = 0.90
MAX_DESCUADRE = 0.02
TRABAJADORES = 12


class NoPublicado(Exception):
    pass


class ErrorValidacion(Exception):
    pass


def columnas(tabla: str) -> list[tuple[str, str]]:
    if tabla == "pactos":
        return PACTOS
    return [(c, t) for _, c, t in next(v[2] for v in CARTERAS.values() if v[0] == tabla)]


def esquema(tabla: str) -> pa.Schema:
    cols = [("periodo", pa.string()), ("run_fondo", pa.string())]
    cols += [(c, pa.float64() if t == "n" else pa.string()) for c, t in columnas(tabla)]
    return pa.schema(cols)


# --- lectura de HTML ---------------------------------------------------------
class _Tablas(HTMLParser):
    """Extrae cada <table> como {th: [filas de encabezado], filas: [filas de datos]}."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tablas, self._fila, self._celda, self._tipo = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tablas.append({"th": [], "filas": []})
        elif tag == "tr":
            self._fila = []
        elif tag in ("td", "th"):
            self._celda, self._tipo = [], tag

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._celda is not None and self._fila is not None:
            self._fila.append((self._tipo, " ".join("".join(self._celda).split())))
            self._celda = None
        elif tag == "tr" and self._fila is not None:
            if self._fila and self.tablas:
                destino = "th" if all(k == "th" for k, _ in self._fila) else "filas"
                self.tablas[-1][destino].append([v for _, v in self._fila])
            self._fila = None

    def handle_data(self, data):
        if self._celda is not None:
            self._celda.append(data)


def tablas_html(raw: bytes) -> list[dict]:
    try:
        texto = raw.decode("utf-8")
    except UnicodeDecodeError:
        texto = raw.decode("latin-1")
    p = _Tablas()
    p.feed(texto)
    return p.tablas


def _norm(s: str) -> str:
    return " ".join(s.split()).strip()


_NUM = re.compile(r"-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?")


def num(txt: str):
    s = txt.strip()
    if s in ("", "NA", "-"):
        return None
    if not _NUM.fullmatch(s):
        raise ValueError(f"número {txt!r}")
    return float(s.replace(".", "").replace(",", "."))


def fecha(txt: str):
    s = txt.strip()
    if s in ("", "NA", "-", "99999999") or s.endswith("9999"):
        return None
    # Desde 2024-06 algunas páginas traen la hora ("24/01/2019 00:00:00"); se descarta.
    hora = r"(?:\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp]\.?\s*[Mm]\.?)?)?"
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})" + hora, s)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})" + hora, s)
        if not m:
            raise ValueError(f"fecha {txt!r}")
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    datetime(y, mth, d)
    return f"{y:04d}-{mth:02d}-{d:02d}"


def rut(txt: str):
    s = txt.strip().replace(".", "")
    if s in ("", "NA", "0"):
        return None if s != "0" else "0"
    if not re.fullmatch(r"\d+(-[\dkK])?", s):
        raise ValueError(f"rut {txt!r}")
    return s.upper()


def convertir(valor: str, tipo: str):
    if tipo == "n":
        return num(valor)
    if tipo == "f":
        return fecha(valor)
    if tipo == "r":
        return rut(valor)
    return valor.strip() or None


def _cuadrar(detalle: list[list[str]], total: list[str], cols: list[tuple[str, str]]) -> list[str]:
    """Compara cada celda numérica de la fila TOTAL con la suma de su columna."""
    difs = []
    for j, celda in enumerate(total):
        if j >= len(cols) or cols[j][1] != "n" or not celda.strip() or celda.strip().upper().startswith("TOTAL"):
            continue
        try:
            t = num(celda)
            s = sum(num(f[j]) or 0.0 for f in detalle)
        except ValueError:
            continue
        if t is None:
            continue
        n = max(len(detalle), 1)
        # porcentajes con 4 decimales; montos enteros en miles: se tolera el redondeo de cada fila
        tol = 0.0001 * n + 0.01 if cols[j][0].startswith("pct_") else 0.5 * n + 1e-7 * abs(t)
        if abs(s - t) > tol:
            difs.append(f"{cols[j][0]}: suma {s:,.4f} vs TOTAL {t:,.4f}")
    return difs


def leer_cartera(cod: str, raw: bytes) -> tuple[list[dict], list[str], list[str]]:
    """Filas de una página de cartera, filas ilegibles y descuadres contra el TOTAL."""
    _, _, spec = CARTERAS[cod]
    esperado = [h for h, _, _ in spec]
    tablas = [t for t in tablas_html(raw) if t["th"] and [_norm(h) for h in t["th"][0]] == esperado]
    if len(tablas) != 1:
        encontrados = [t["th"][0] for t in tablas_html(raw) if t["th"]]
        raise ErrorValidacion(f"cartera {cod}: encabezado inesperado {encontrados[:1]}")
    cols = [(c, t) for _, c, t in spec]
    detalle, totales, filas, malas = [], [], [], []
    for f in tablas[0]["filas"]:
        if len(f) <= 1:
            continue  # título, línea en blanco o nota
        if any(c.upper().startswith("TOTAL") for c in f):
            totales.append(f)
            continue
        if len(f) != len(spec):
            malas.append(f"{len(f)} celdas en vez de {len(spec)}")
            continue
        fila, malo = {}, None
        for (_, col, tipo), v in zip(spec, f):
            try:
                fila[col] = convertir(v, tipo)
            except ValueError as e:
                fila[col], malo = None, malo or f"{col} ({e})"
        if malo:
            malas.append(malo)
        detalle.append(f)
        filas.append(fila)
    descuadres = []
    for t in totales:
        descuadres += _cuadrar(detalle, t, cols)
    return filas, malas, descuadres


def leer_pactos(raw: bytes) -> tuple[list[dict], list[str], list[str], str | None]:
    tablas = [t for t in tablas_html(raw) if t["th"] and [_norm(h) for h in t["th"][0]] == PACTOS_TH]
    if not tablas or any(len(t["th"]) < 2 or [_norm(h) for h in t["th"][1]] != PACTOS_SUB for t in tablas):
        raise ErrorValidacion("pactos: encabezado inesperado")
    filas, malas, descuadres, moneda = [], [], [], None
    for t in tablas:
        detalle = []
        for f in t["filas"]:
            if len(f) == 1:
                m = re.search(r"miles de:\s*([^.\s]+(?:\s[^.\s]+)*)\s*\.?$", f[0])
                if m and f[0].startswith("Período"):
                    moneda = moneda or m.group(1).strip()
                continue
            if any(c.upper().startswith("TOTAL") for c in f):
                descuadres += _cuadrar(detalle, f, PACTOS)
                continue
            if len(f) != len(PACTOS):
                malas.append(f"pactos: {len(f)} celdas en vez de {len(PACTOS)}")
                continue
            fila, malo = {}, None
            for (col, tipo), v in zip(PACTOS, f):
                try:
                    fila[col] = convertir(v, tipo)
                except ValueError as e:
                    fila[col], malo = None, malo or f"{col} ({e})"
            if malo:
                malas.append(malo)
            detalle.append(f)
            filas.append(fila)
    return filas, malas, descuadres, moneda


# --- descargas ---------------------------------------------------------------
def _get(url: str, timeout: int = 90) -> bytes:
    for intento in range(1, 5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if intento == 4:
                raise
            time.sleep(5 * intento)


def url_pagina(cod: str, run: str, periodo: str) -> str:
    q = {"rut": run, "periodo": periodo.replace("-", "")}
    if cod == "V":
        return URL_PACTOS + "?" + urllib.parse.urlencode(q)
    q.update({"tipo": "fi", "cartera": cod})
    return BASE_CARTERA + CARTERAS[cod][1] + "?" + urllib.parse.urlencode(q)


def descargar_lista() -> list[dict]:
    fondos, vistos = [], set()
    for tipo, desc in TIPOS_FONDO.items():
        for estado in ("VI", "NV"):
            raw = _get(URL_LISTA.format(estado=estado, tipo=tipo))
            tablas = [t for t in tablas_html(raw) if t["th"] and _norm(t["th"][0][0]) == "R.U.T."]
            if len(tablas) != 1:
                raise ErrorValidacion(f"lista {tipo} {estado}: no se encontró la tabla de fondos")
            for f in tablas[0]["filas"]:
                if len(f) < 3 or not re.fullmatch(r"\d+-[\dkK]", f[0].strip()):
                    continue
                run = f[0].split("-")[0]
                if (run, tipo) in vistos:
                    continue
                vistos.add((run, tipo))
                fondos.append({"run_fondo": run, "rut_fondo_dv": f[0].strip().upper(), "nombre_fondo": f[1],
                               "administradora": f[2], "estado_vigencia": "Vigente" if estado == "VI" else "No Vigente",
                               "tipo_entidad": tipo, "tipo_entidad_desc": desc})
    return fondos


# --- control y escritura -----------------------------------------------------
def trimestres(desde: str, hasta: str) -> list[str]:
    y, m = int(desde[:4]), int(desde[5:])
    out = []
    while f"{y}-{m:02d}" <= hasta:
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 3) if m == 12 else (y, m + 3)
    return out


def ultimo_trimestre_disponible(hoy: date | None = None) -> str:
    hoy = hoy or date.today()
    y, m = hoy.year, (hoy.month - 1) // 3 * 3  # trimestre anterior al actual
    if m == 0:
        y, m = y - 1, 12
    while True:
        fin = date(y, m, {3: 31, 6: 30, 9: 30, 12: 31}[m])
        if fin + timedelta(days=DIAS_ESPERA[m]) <= hoy:
            return f"{y}-{m:02d}"
        y, m = (y - 1, 12) if m == 3 else (y, m - 3)


def cargar_control() -> dict:
    ruta = SALIDA / "manifest.json"
    return json.loads(ruta.read_text()) if ruta.exists() else {"periodos": {}, "fondos": {}}


def guardar_control(control: dict) -> None:
    control["periodos"] = dict(sorted(control["periodos"].items()))
    control["desde"] = DESDE
    control["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (SALIDA / "manifest.json").write_text(json.dumps(control, ensure_ascii=False, indent=2) + "\n")


def ruta_particion(tabla: str, periodo: str) -> Path:
    return SALIDA / tabla / (f"{periodo}.parquet" if tabla in POR_PERIODO else f"{periodo[:4]}.parquet")


def escribir(tabla: str, periodo: str, filas: list[dict]) -> int:
    ruta = ruta_particion(tabla, periodo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    nuevo = pd.DataFrame(filas).reindex(columns=esquema(tabla).names)
    partes = []
    if ruta.exists():
        viejo = pq.read_table(ruta).to_pandas()
        partes.append(viejo[viejo["periodo"] != periodo])
    partes.append(nuevo)
    partes = [p for p in partes if len(p)]
    if not partes:
        return 0
    df = pd.concat(partes, ignore_index=True).reindex(columns=esquema(tabla).names)
    df["_run"] = pd.to_numeric(df["run_fondo"], errors="coerce")
    df = df.sort_values(["periodo", "_run"], kind="stable").drop(columns="_run")
    tmp = ruta.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pandas(df, schema=esquema(tabla), preserve_index=False), tmp,
                   compression="zstd", compression_level=9)
    os.replace(tmp, ruta)
    return len(nuevo)


def fondos_a_consultar(periodo: str, registro: list[dict], control: dict, reciente: bool) -> list[str]:
    """Trimestres recientes: vigentes + los que reportaron el trimestre anterior. Antiguos: todo el registro."""
    if not reciente:
        return sorted({f["run_fondo"] for f in registro}, key=int)
    previos = [p for p in control["periodos"] if p < periodo]
    anteriores = set(control["periodos"][max(previos)].get("fondos_con_cartera", [])) if previos else set()
    vig = {f["run_fondo"] for f in registro if f["estado_vigencia"] == "Vigente"}
    if not previos:
        vig |= {f["run_fondo"] for f in registro}
    return sorted(vig | anteriores, key=int)


def procesar_trimestre(periodo: str, fondos: list[str], control: dict, reciente: bool):
    tareas = [(run, cod) for run in fondos for cod in list(CARTERAS) + ["V"]]
    def bajar(t):
        run, cod = t
        return t, _get(url_pagina(cod, run, periodo))
    datos = {t: [] for t in TABLAS}
    malas, descuadres, inesperadas, monedas, con_cartera, fondos_con_datos = [], [], [], {}, set(), 0
    fondos_descuadre = set()
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as ex:
        for (run, cod), raw in ex.map(bajar, tareas):
            try:
                if cod == "V":
                    filas, m, d, moneda = leer_pactos(raw)
                    if moneda:
                        monedas[run] = moneda
                    tabla = "pactos"
                else:
                    filas, m, d = leer_cartera(cod, raw)
                    tabla = CARTERAS[cod][0]
            except ErrorValidacion as e:
                inesperadas.append(f"fondo {run} {cod}: {e}")
                continue
            for f in filas:
                f["periodo"], f["run_fondo"] = periodo, run
            datos[tabla] += filas
            if filas:
                con_cartera.add(run)
            malas += [f"fondo {run} {cod}: {x}" for x in m]
            if d:
                fondos_descuadre.add(run)
                descuadres += [f"fondo {run} {cod}: {x}" for x in d]
    total_filas = sum(len(v) for v in datos.values())
    if len(inesperadas) > 0.01 * len(tareas):
        raise ErrorValidacion(f"{periodo}: {len(inesperadas)} de {len(tareas)} páginas inesperadas:\n  - "
                              + "\n  - ".join(inesperadas[:15]))
    if len(malas) > 0.01 * max(total_filas, 1):
        raise ErrorValidacion(f"{periodo}: {len(malas)} de {total_filas} filas ilegibles:\n  - " + "\n  - ".join(malas[:15]))
    if len(fondos_descuadre) > MAX_DESCUADRE * max(len(con_cartera), 1):
        raise ErrorValidacion(f"{periodo}: {len(fondos_descuadre)} de {len(con_cartera)} fondos no cuadran con el "
                              "TOTAL de la CMF:\n  - " + "\n  - ".join(descuadres[:15]))
    previos = [v.get("n_fondos_con_cartera") for p, v in control["periodos"].items() if p < periodo]
    previo = next((x for x in reversed(previos) if x), None)
    Falta = NoPublicado if reciente else ErrorValidacion
    if not con_cartera:
        raise Falta(f"{periodo}: ningún fondo con cartera publicada")
    if previo and len(con_cartera) < COBERTURA_MINIMA * previo:
        raise Falta(f"{periodo}: {len(con_cartera)} fondos con cartera (trimestre anterior {previo}); "
                    "se espera a que la CMF complete el trimestre")
    avisos = inesperadas + malas + descuadres
    return datos, avisos, con_cartera, monedas, len(tareas)


def escribir_salidas(control: dict, registro: list[dict]) -> None:
    for tabla in TABLAS:
        (SALIDA / tabla).mkdir(parents=True, exist_ok=True)
        vacio = SALIDA / tabla / "_vacio.parquet"
        rutas = sorted(r for r in (SALIDA / tabla).glob("*.parquet") if r.name != vacio.name)
        if rutas:
            vacio.unlink(missing_ok=True)
        else:
            # Ningún fondo informó esta cartera todavía (p. ej. bienes raíces directos): se publica
            # un archivo sin filas con el esquema, para que la vista web exista y responda vacía.
            pq.write_table(esquema(tabla).empty_table(), vacio)
            rutas = [vacio]
        man = {"tabla": tabla, "files": [f"outputs/fi/{tabla}/{r.name}" for r in rutas],
               "total_records": sum(pq.ParquetFile(r).metadata.num_rows for r in rutas),
               "periodos": sorted(control["periodos"]),
               "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (SALIDA / tabla / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")
    ultimo = max(control["periodos"]) if control["periodos"] else None
    filas = []
    for f in sorted(registro, key=lambda f: (int(f["run_fondo"]), f["tipo_entidad"])):
        info = control["fondos"].get(f["run_fondo"], {})
        filas.append({**{k: f[k] for k in ("run_fondo", "rut_fondo_dv", "nombre_fondo", "administradora",
                                           "tipo_entidad", "estado_vigencia")},
                      "moneda_funcional": info.get("moneda"), "primer_periodo_cartera": info.get("primer"),
                      "ultimo_periodo_cartera": info.get("ultimo"), "trimestres_con_cartera": info.get("trimestres", 0),
                      "reporta_ultimo_periodo": bool(ultimo and info.get("ultimo") == ultimo)})
    df = pd.DataFrame(filas)
    df["trimestres_con_cartera"] = df["trimestres_con_cartera"].astype("int64")
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), SALIDA / "maestro_fondos_inversion.parquet",
                   compression="zstd")
    universo = [{"id": f"FI_{f['run_fondo']}", **f} for f in registro]
    (SALIDA / "fi_registro_fondos_universo.json").write_text(json.dumps(universo, ensure_ascii=False, indent=1) + "\n")


ORIGEN = ("CMF — Informes IFRS de cartera de inversiones y de pactos (VRC/CRV) de cada fondo de inversión, "
          "https://www.cmfchile.cl (ifrs_cartera_*.php, ifrs_informe_vrc_crv.php), y registro de fondos "
          "(consulta.php, FINRE y FIRES).")
WEB = {
    "fi_maestro": (None, "fi.lista_entidades", "Registro CMF de fondos de inversión (rescatables y no rescatables, "
                   "vigentes y no vigentes) con administradora, moneda funcional y primer y último trimestre con "
                   "cartera publicada."),
    "fi_cartera_nacional": ("cartera_nacional", "fi.cartera_nacional", "Inversiones en instrumentos de emisores "
                            "nacionales, instrumento por instrumento, al cierre de cada trimestre. Montos en miles de "
                            "la moneda funcional del fondo."),
    "fi_cartera_extranjera": ("cartera_extranjera", "fi.cartera_extranjera", "Inversiones en instrumentos de "
                              "emisores extranjeros al cierre de cada trimestre."),
    "fi_metodo_participacion": ("metodo_participacion", "fi.metodo_participacion", "Inversiones valorizadas por "
                                "el método de la participación (sociedades filiales y coligadas)."),
    "fi_bienes_raices": ("bienes_raices", "fi.bienes_raices", "Bienes raíces nacionales y extranjeros de los "
                         "fondos."),
    "fi_futuros": ("futuros_forwards", "fi.futuros_forwards", "Contratos de futuro, forward y swap vigentes al "
                   "cierre de cada trimestre."),
    "fi_opciones": ("opciones", "fi.opciones", "Contratos de opciones vigentes al cierre de cada trimestre."),
    "fi_pactos": ("pactos", "fi.pactos", "Operaciones de venta con compromiso de retrocompra (VRC) y de compra con "
                  "compromiso de retroventa (CRV) vigentes al cierre de cada trimestre."),
}


def actualizar_data_manifest(control: dict) -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists() or not (SALIDA / "maestro_fondos_inversion.parquet").exists():
        return
    man = json.loads(ruta.read_text())
    hoy = date.today().isoformat()
    periodos = sorted(control["periodos"])
    entradas = []
    for vista, (tabla, nombre, descripcion) in WEB.items():
        if tabla is None:
            archivo = "outputs/fi/maestro_fondos_inversion.parquet"
            registros = pq.ParquetFile(SALIDA / "maestro_fondos_inversion.parquet").metadata.num_rows
        else:
            archivo = f"outputs/fi/{tabla}/manifest.json"
            registros = json.loads((SALIDA / tabla / "manifest.json").read_text())["total_records"]
        entradas.append({
            "id": vista, "name": nombre, "view_name": vista, "sector": "fi", "sector_label": "Fondos de Inversión",
            "norma": "IFRS · informes de cartera CMF",
            "corte": f"{periodos[0]} a {periodos[-1]}" if periodos else "sin trimestres publicados",
            "frescura": f"Último trimestre publicado: {periodos[-1]}" if periodos else "",
            "modo": "Automático · 3 veces al mes, incremental", "ultima_actualizacion": hoy,
            "file_parquet": archivo, "registros_reales": registros, "descripcion": descripcion, "origen": ORIGEN,
        })
    ids = {e["id"] for e in entradas}
    man["tables"] = entradas + [t for t in man["tables"] if t["id"] not in ids]
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    ruta.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hasta", default=None)
    ap.add_argument("--max-periodos", type=int, default=100)
    ap.add_argument("--minutos", type=float, default=240, help="no empezar trimestres nuevos pasado este tiempo")
    ap.add_argument("--fondos", nargs="*", help="solo estos RUN (pruebas; no escribe)")
    ap.add_argument("--solo-data-manifest", action="store_true")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest(cargar_control())
        return 0
    inicio = time.monotonic()
    gha = bool(os.environ.get("GITHUB_ACTIONS"))
    SALIDA.mkdir(parents=True, exist_ok=True)
    control = cargar_control()
    registro = descargar_lista()
    previo = control.get("fondos_registro")
    if previo and len(registro) < 0.9 * previo:
        raise ErrorValidacion(f"el registro CMF trae {len(registro)} fondos (antes {previo})")
    print(f"Registro CMF: {len(registro)} fondos "
          f"({sum(f['estado_vigencia'] == 'Vigente' for f in registro)} vigentes)")
    hasta = a.hasta or ultimo_trimestre_disponible()
    pendientes = [p for p in trimestres(DESDE, hasta) if p not in control["periodos"]]
    recientes = set(trimestres(DESDE, hasta)[-2:])
    print(f"Trimestres publicados: {len(control['periodos'])}. Pendientes: {len(pendientes)}")
    hechos = []
    for periodo in pendientes[:a.max_periodos]:
        if time.monotonic() - inicio > a.minutos * 60:
            print(f"Tiempo agotado ({a.minutos:.0f} min); el resto sigue en la próxima corrida.")
            break
        reciente = periodo in recientes
        fondos = a.fondos or fondos_a_consultar(periodo, registro, control, reciente)
        t0 = time.monotonic()
        try:
            datos, avisos, con_cartera, monedas, n = procesar_trimestre(periodo, fondos, control, reciente and not a.fondos)
        except NoPublicado as e:
            print(f"{e}. Se retoma en la próxima corrida.")
            break
        resumen = ", ".join(f"{t} {len(v)}" for t, v in datos.items())
        print(f"{periodo}: {len(fondos)} fondos consultados ({n} páginas, {time.monotonic() - t0:.0f} s), "
              f"{len(con_cartera)} con cartera · {resumen}" + (f" · {len(avisos)} avisos" if avisos else ""))
        for x in avisos[:10]:
            print(f"   aviso: {x}")
        if a.fondos:
            continue
        conteo = {t: escribir(t, periodo, v) for t, v in datos.items()}
        control["periodos"][periodo] = {"registros": conteo, "n_fondos_con_cartera": len(con_cartera),
                                        "fondos_con_cartera": sorted(con_cartera, key=int),
                                        "avisos": len(avisos), "detalle_avisos": avisos[:20]}
        for run in con_cartera:
            i = control["fondos"].setdefault(run, {"primer": None, "ultimo": None, "trimestres": 0})
            i["primer"] = min(i["primer"] or periodo, periodo)
            i["trimestres"] += 1
            if periodo >= (i["ultimo"] or ""):
                i["ultimo"] = periodo
        for run, moneda in monedas.items():
            i = control["fondos"].setdefault(run, {"primer": None, "ultimo": None, "trimestres": 0})
            if periodo >= (i.get("moneda_periodo") or ""):
                i["moneda"], i["moneda_periodo"] = moneda, periodo
        control["fondos_registro"] = len(registro)
        guardar_control(control)
        escribir_salidas(control, registro)
        hechos.append(periodo)
    if not a.fondos and (hechos or not (SALIDA / "maestro_fondos_inversion.parquet").exists()) and control["periodos"]:
        escribir_salidas(control, registro)
        actualizar_data_manifest(control)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            fh.write(f"publicados={len(hechos)}\n")
    msg = f"{len(hechos)} trimestres nuevos" + (f" ({hechos[0]} a {hechos[-1]})" if hechos else "")
    print("Listo: " + msg)
    if gha:
        print(f"::notice title=FI carteras::{msg}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErrorValidacion as e:
        print(f"ERROR DE VALIDACIÓN (no se publicó el trimestre): {e}", file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS"):
            print("::error title=FI carteras::" + str(e).replace("\n", "%0A")[:3000])
        sys.exit(2)

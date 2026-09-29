#!/usr/bin/env python3
"""Detección automática de entidades nuevas y cambios de vigencia (registros públicos CMF).

Para cada sector con registro en https://www.cmfchile.cl/institucional/mercados/consulta.php
(listas de vigentes «VI» y no vigentes «NV»):
  * RUT vigente que no está en la lista de entidades del sector → se agrega (alta), con los
    campos que da el registro (RUT, razón social, vigencia, enlace a la ficha CMF); los campos
    descriptivos que se completaban a mano quedan vacíos.
  * RUT de la lista que la CMF muestra en la lista de no vigentes (y no en la de vigentes)
    → se marca no vigente. Nunca se da de baja por simple ausencia.
  * RUT marcado no vigente que vuelve a la lista de vigentes → se marca vigente.
Cada cambio queda en docs/outputs/entidades/novedades.json y como aviso en Actions.

Un sector puede combinar varios registros (sistemas de pago: operadores de tarjetas, cámaras,
contrapartes centrales y depósito de valores); en algunos solo se revisa la vigencia porque el
registro incluye entidades que no son del sector.

Cooperativas de ahorro y crédito fiscalizadas: registro BCCOO (mercado B).

Bancos: registro BANCO (mercado B). Solo se agregan bancos nuevos y se marca «No vigente» a un
banco «Activo» que la CMF muestre como no vigente; los fusionados, cerrados y totales del
sistema no se tocan (varios comparten RUT con el banco que los absorbió).

Patrimonios separados: la CMF publica todas las inscripciones de títulos de deuda por registro
automático (listado_titulos_deuda.php: número, fecha, emisor, tipo, RUT, monto, moneda,
vencimiento). Cada inscripción de una securitizadora que no está en la lista se agrega; la
clase de colateral no está en esa página y queda vacía.

AFP: la Superintendencia de Pensiones publica a diario el valor cuota de cada AFP; una AFP que
aparece ahí y no está en la lista se agrega, con el RUT del Registro de Valores CMF (RVEMI).

Resguardo: si el registro vigente trae menos de la mitad de las entidades vigentes que ya
estaban en la lista (página caída o formato nuevo), ese sector no se modifica.

Otros sectores detectan sus entidades en su propio actualizador: FI (registro completo en cada
corrida de fi_carteras), FFMM y seguros (la lista sale de los archivos de cartera), CCAF y
factoring/leasing (el actualizador IFRS agrega a quien reporta con ese giro), AGF y
securitizadoras (además del registro, el IFRS avisa quién reporta sin estar en la lista).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from pipelines.auto.rut import normalizar_registros  # noqa: E402

DOCS = RAIZ / "docs" / "outputs"
NOVEDADES = DOCS / "entidades" / "novedades.json"
URL = "https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado={mercado}&Estado={estado}&entidad={codigo}"
FICHA = ("https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado={mercado}&rut={rut}"
         "&tipoentidad={codigo}&vig={estado}&control=svs&pestania=1")
UA = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/1.0)"}


def rut_int(c, d): return int(c)
def rut_str(c, d): return c
def rut_dv(c, d): return f"{c}-{d}"
def puntos(c, d): return f"{int(c):,}".replace(",", ".") + f"-{d}"


SECTORES = {
    "agf": {
        "archivos": ["agf/agf_maestro"], "codigo": "RGAGF", "mercado": "V",
        "rut": rut_int, "clave": "rut", "vig": ("Vigente", "No Vigente / Cancelada"),
        "alta": lambda c, d, nombre, url, cod=None: {
            "rut": int(c), "dv": d, "rut_completo": puntos(c, d), "razon_social": nombre, "nombre_fantasia": nombre,
            "tipo_entidad": "Administradora General de Fondos", "marco_legal": "Ley N° 20.712 (Ley Única de Fondos - LUF)",
            "regulador": "CMF", "cmf_url": url, "fondos_inversion_administrados": 0},
    },
    "securitizadoras": {
        "archivos": ["securitizadoras/securitizadoras_maestro"], "codigo": "RGSEC", "mercado": "V",
        "rut": rut_str, "clave": "rut", "vig": ("VIGENTE", "NO VIGENTE / EN LIQUIDACION"),
        "alta": lambda c, d, nombre, url, cod=None: {
            "rut": c, "dv": d, "rut_completo": f"{c}-{d}", "razon_social": nombre, "tipo_entidad_cmf": "RGSEC",
            "lineas_deuda_registradas": 0, "cmf_url": url},
    },
    "corredoras_bolsa": {
        # La lista de entidades no tiene vigencia; el registro único sí.
        "archivos": ["corredoras_bolsa/corredoras_bolsa_maestro", "corredoras_bolsa/corredoras_bolsa_registro_universo"],
        "codigo": "COBOL", "mercado": "V", "rut": rut_dv, "clave": "rut", "vig": ("Vigente", "No Vigente"),
        "alta": lambda c, d, nombre, url, cod=None: {
            "rut": f"{c}-{d}", "rut_cuerpo": c, "dv": d, "nombre_empresa": nombre, "nombre_fantasia": nombre,
            "tipo_intermediario": "CORREDOR DE BOLSA", "tipo_entidad": "COBOL", "url_ficha_cmf": url},
    },
    "fintech": {
        "archivos": ["fintech/fintech_rpsf_maestro"], "codigo": "RGPSF", "mercado": "O",
        "rut": rut_int, "clave": "rut", "vig": ("Vigente", "No Vigente"),
        "alta": lambda c, d, nombre, url, cod=None: {
            "rut": int(c), "dv": d, "rut_completo": puntos(c, d), "razon_social": nombre, "nombre_fantasia": nombre,
            "cmf_url": url, "servicios_acreditados_total": 0},
    },
    "cooperativas": {
        "archivos": ["cooperativas/cooperativas_maestro"], "codigo": "BCCOO", "mercado": "B",
        "rut": rut_dv, "clave": "rut", "vig": ("Vigente", "No Vigente"),
        "alta": lambda c, d, nombre, url, cod=None: {
            "rut": f"{c}-{d}", "rut_cuerpo": c, "dv": d, "nombre_empresa": nombre, "nombre_fantasia": nombre,
            "tipo_institucion": "COOPERATIVA DE AHORRO Y CREDITO", "regulador_principal": "CMF Chile"},
    },
    "bancos": {
        "archivos": ["bancos/bancos_maestro"], "codigo": "BANCO", "mercado": "B",
        "rut": puntos, "clave": "rut", "campo_vig": "estado", "vig": ("Activo", "No vigente"),
        # Solo pasa Activo → No vigente; fusionados/cerrados/agregados comparten RUT con bancos vigentes.
        "solo_baja": True,
        "alta": lambda c, d, nombre, url, cod=None: {
            "codigo_institucion": f"sin_codigo_{c}", "rut": puntos(c, d), "razon_social": nombre, "nombre_fantasia": nombre,
            "tipo_licencia": "Banca Comercial"},
    },
    "sistemas_pago": {
        "archivos": ["sistemas_pago/sistemas_pago_maestro"],
        # (mercado, código, ¿agrega entidades nuevas?). BCSAG (sociedades de apoyo al giro bancario)
        # y DCVAL incluyen entidades que no son sistemas de pago: ahí solo se revisa la vigencia.
        "registros": [("B", "TPOPE", True), ("V", "RGCCO", True), ("B", "BCSAG", False), ("V", "DCVAL", False)],
        "rut": rut_int, "clave": "rut", "vig": ("Vigente", "No Vigente"),
        "alta": lambda c, d, nombre, url, cod=None: {
            "rut": int(c), "dv": d, "rut_completo": puntos(c, d), "codigo_sistema": "", "razon_social": nombre,
            "nombre_comercial": nombre,
            "tipo_sistema": {"TPOPE": "Operador de Tarjetas de Pago", "RGCCO": "Entidad de Contraparte Central"}.get(cod, cod),
            "marco_legal": {"TPOPE": "Ley N° 20.950 / Compendio Normas Financieras BCCh Cap. III.J.2",
                            "RGCCO": "Ley N° 20.345"}.get(cod, ""),
            "supervisor": "CMF", "cmf_url": url},
    },
}

AFP_SP = "https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFP.php?tf=A"
AFP_BASE = "pensiones/afp_maestro_administradoras"
SECTORES["afp"] = {"archivos": [AFP_BASE], "fuente": "afp"}
PS_URL = "https://www.cmfchile.cl/institucional/estadisticas/listado_titulos_deuda.php"
PS_BASE = "securitizadoras/patrimonios_separados_maestro"
SECTORES["patrimonios_separados"] = {"archivos": [PS_BASE], "fuente": "registro_automatico"}


class _Tablas(HTMLParser):
    """Tablas HTML (admite tablas anidadas): th = filas solo de <th>, filas = el resto, todas = en orden."""

    def __init__(self):
        super().__init__()
        self.tablas, self._pila = [], []  # pila de [tabla, fila, celda]

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._pila.append([{"th": [], "filas": [], "todas": []}, None, None])
        elif not self._pila:
            return
        elif tag == "tr":
            self._pila[-1][1] = []
        elif tag in ("td", "th") and self._pila[-1][1] is not None:
            self._pila[-1][2] = [tag, ""]

    def handle_endtag(self, tag):
        if not self._pila:
            return
        t, f, c = self._pila[-1]
        if tag in ("td", "th") and c is not None and f is not None:
            f.append((c[0], " ".join(c[1].split())))
            self._pila[-1][2] = None
        elif tag == "tr" and f is not None:
            if f:
                t["todas"].append([v for _, v in f])
                (t["th"] if all(x == "th" for x, _ in f) else t["filas"]).append([v for _, v in f])
            self._pila[-1][1] = None
        elif tag == "table":
            self.tablas.append(self._pila.pop()[0])

    def handle_data(self, data):
        for nivel in self._pila[-1:]:
            if nivel[2] is not None:
                nivel[2][1] += data


def _get(url: str) -> bytes:
    ultimo = None
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception as e:
            ultimo = e
            time.sleep(5 * (intento + 1))
    raise RuntimeError(f"{url}: {ultimo}")


def registros(cfg: dict) -> list[tuple[str, str, bool]]:
    return cfg.get("registros") or [(cfg["mercado"], cfg["codigo"], True)]


def registro(mercado: str, codigo: str, estado: str) -> dict[str, tuple[str, str]]:
    """{cuerpo_rut: (dv, nombre)} de la lista CMF."""
    raw = _get(URL.format(mercado=mercado, estado=estado, codigo=codigo))
    p = _Tablas()
    p.feed(raw.decode("utf-8", errors="replace"))
    out = {}
    for t in p.tablas:
        if not t["th"] or not t["th"][0] or "R.U.T" not in t["th"][0][0].upper():
            continue
        for f in t["filas"]:
            m = re.fullmatch(r"([\d.]+)-([\dkK])", f[0].strip()) if f else None
            if m and len(f) >= 2:
                out[m.group(1).replace(".", "")] = (m.group(2).upper(), f[1].strip())
    return out


def cuerpo(v) -> str:
    return str(v).replace(".", "").split("-")[0].strip()


def guardar(base: str, filas: list[dict]) -> None:
    # Convención de RUT: `rut` = cuerpo, `rut_dv` = con DV, sin `rut_cuerpo`
    # (ver pipelines/auto/rut.py). Único punto de escritura de todas las listas.
    filas = normalizar_registros(filas)[0]
    js, pqt = DOCS / f"{base}.json", DOCS / f"{base}.parquet"
    js.write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if pqt.exists():
        esquema = pq.read_schema(pqt)
        df = pd.DataFrame(filas).reindex(columns=esquema.names)
        for campo in esquema:
            if pa.types.is_integer(campo.type):
                df[campo.name] = pd.to_numeric(df[campo.name], errors="coerce").astype("Int64")
        pq.write_table(pa.Table.from_pandas(df, schema=esquema.remove_metadata(), preserve_index=False), pqt)


def procesar(sector: str, cfg: dict, hoy: str) -> list[dict]:
    if cfg.get("fuente") == "afp":
        return procesar_afp(hoy)
    if cfg.get("fuente") == "registro_automatico":
        return procesar_ps(hoy)
    vi, nv, origen = {}, {}, {}
    for mercado, codigo, altas in registros(cfg):
        v = registro(mercado, codigo, "VI")
        for c, x in v.items():
            vi.setdefault(c, x)
            if altas and c not in origen:
                origen[c] = (mercado, codigo)
        for c, x in registro(mercado, codigo, "NV").items():
            nv.setdefault(c, x)
    campo = cfg.get("campo_vig", "estado_vigencia")
    eventos = []
    for base in cfg["archivos"]:
        ruta = DOCS / f"{base}.json"
        filas = json.loads(ruta.read_text(encoding="utf-8"))
        tiene_vig = any(campo in f for f in filas)
        en_lista = {cuerpo(f[cfg["clave"]]) for f in filas}
        vigentes_antes = {cuerpo(f[cfg["clave"]]) for f in filas
                          if not tiene_vig or f.get(campo) == cfg["vig"][0]}
        coinciden = len(vigentes_antes & set(vi))
        if tiene_vig and vigentes_antes and coinciden < len(vigentes_antes) / 2:
            print(f"::warning::{sector}: el registro CMF vigente trae {len(vi)} entidades y solo {coinciden} de "
                  f"{len(vigentes_antes)} vigentes de {base}; no se modifica")
            continue
        if not tiene_vig and len(vi) < 5:
            print(f"::warning::{sector}: registro CMF vigente con {len(vi)} entidades; no se modifica {base}")
            continue
        cambio = False
        for f in filas:
            c = cuerpo(f[cfg["clave"]])
            if not tiene_vig:
                break
            nuevo = cfg["vig"][0] if c in vi else cfg["vig"][1] if c in nv else None
            if cfg.get("solo_baja") and (f.get(campo) != cfg["vig"][0] or nuevo != cfg["vig"][1]):
                continue
            if nuevo and f.get(campo) != nuevo:
                eventos.append({"fecha": hoy, "sector": sector, "lista": base, "rut": f"{c}-{(vi.get(c) or nv.get(c))[0]}",
                                "razon_social": (vi.get(c) or nv.get(c))[1], "evento": "cambio_vigencia",
                                "antes": f.get(campo), "ahora": nuevo})
                f[campo] = nuevo
                cambio = True
        columnas = list(filas[0].keys()) if filas else []
        for c, (d, nombre) in sorted(vi.items()):
            if c in en_lista or c not in origen:
                continue
            mercado, codigo = origen[c]
            url = FICHA.format(mercado=mercado, rut=c, codigo=codigo, estado="VI")
            alta = cfg["alta"](c, d, nombre, url, codigo)
            if tiene_vig:
                alta[campo] = cfg["vig"][0]
            fila = {k: alta.get(k) for k in columnas}
            filas.append(fila)
            eventos.append({"fecha": hoy, "sector": sector, "lista": base, "rut": f"{c}-{d}", "razon_social": nombre,
                            "evento": "alta", "antes": None, "ahora": cfg["vig"][0]})
            cambio = True
        if cambio:
            guardar(base, filas)
        print(f"{sector} · {base}: registro CMF {len(vi)} vigentes / {len(nv)} no vigentes; lista {len(filas)} "
              f"filas; cambios {sum(e['lista'] == base for e in eventos)}")
    return eventos


def _norm(s: str) -> str:
    import unicodedata
    s = "".join(ch for ch in unicodedata.normalize("NFKD", str(s).upper()) if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", s).split())


def afp_publicadas(raw: bytes | None = None) -> list[str]:
    """Nombres cortos de las AFP con valor cuota publicado por la Superintendencia de Pensiones.

    La página es una tabla de diseño: las AFP son las filas entre «A.F.P. | Valor Cuota | …» y «TOTAL».
    """
    p = _Tablas()
    p.feed((raw if raw is not None else _get(AFP_SP)).decode("latin-1", errors="replace"))
    nombres = []
    for t in p.tablas:
        dentro = False
        for f in t["todas"]:
            n = _norm(f[0]) if f else ""
            if n in ("A F P", "AFP") and len(f) >= 2 and "CUOTA" in _norm(f[1]):
                dentro = True
                continue
            if not dentro:
                continue
            if n == "TOTAL" or len(f) < 2:
                break
            if n and re.search(r"\d", f[1]):
                nombres.append(n)
    return nombres


def procesar_afp(hoy: str) -> list[dict]:
    nombres = afp_publicadas()
    ruta = DOCS / f"{AFP_BASE}.json"
    filas = json.loads(ruta.read_text(encoding="utf-8"))
    if len(nombres) < max(3, len(filas) // 2):
        print(f"::warning::afp: la Superintendencia muestra {len(nombres)} AFP; no se modifica {AFP_BASE}")
        return []
    conocidas = {_norm(f["nombre_fantasia"]).removeprefix("AFP ").strip() for f in filas} | \
                {_norm(f["nombre_administradora"]).removeprefix("ADMINISTRADORA DE FONDOS DE PENSIONES ").removesuffix(" S A").strip()
                 for f in filas}
    nuevas = [n for n in nombres if n not in conocidas]
    for f in filas:
        n = _norm(f["nombre_fantasia"]).removeprefix("AFP ").strip()
        if n not in nombres:
            print(f"::notice::afp: {n} está en la lista pero hoy no tiene valor cuota publicado (no se modifica)")
    if not nuevas:
        print(f"afp · {AFP_BASE}: Superintendencia {len(nombres)} AFP; lista {len(filas)} filas; cambios 0")
        return []
    emisores = registro("V", "RVEMI", "VI")
    eventos = []
    for n in nuevas:
        rut = next(((c, d, nom) for c, (d, nom) in emisores.items()
                    if _norm(nom).startswith(f"ADMINISTRADORA DE FONDOS DE PENSIONES {n}")), None)
        c, d, razon = rut if rut else ("", "", f"ADMINISTRADORA DE FONDOS DE PENSIONES {n}")
        fila = {"id": f"afp_{c}_{d}" if c else f"afp_{n.lower().replace(' ', '_')}",
                "rut_administradora": puntos(c, d) if c else "", "nombre_administradora": razon,
                "nombre_fantasia": "AFP " + n.title()}
        filas.append(fila)
        eventos.append({"fecha": hoy, "sector": "afp", "lista": AFP_BASE, "rut": fila["rut_administradora"],
                        "razon_social": razon, "evento": "alta", "antes": None, "ahora": "Vigente"})
        if not c:
            print(f"::warning::afp: {n} sin RUT en el Registro de Valores; se agrega sin RUT")
    guardar(AFP_BASE, filas)
    print(f"afp · {AFP_BASE}: Superintendencia {len(nombres)} AFP; lista {len(filas)} filas; cambios {len(eventos)}")
    return eventos


def inscripciones_registro_automatico(raw: bytes) -> list[dict]:
    p = _Tablas()
    p.feed(raw.decode("utf-8", errors="replace"))
    out = []
    for t in p.tablas:
        cab = [_norm(x) for x in (t["th"][0] if t["th"] else [])]
        if not cab or "NUMERO DE INSCRIPCION" not in cab[0]:
            continue
        for f in t["filas"]:
            if len(f) < 8 or not f[0].strip().isdigit():
                continue
            fecha = lambda x: "-".join(reversed(x.strip().split("-"))) if re.fullmatch(r"\d{2}-\d{2}-\d{4}", x.strip()) else None
            monto = f[5].replace(",", "").strip()
            out.append({"numero_inscripcion": f[0].strip(), "fecha_inscripcion": fecha(f[1]), "razon_social": f[2].strip(),
                        "tipo_emision": f[3].strip(), "rut": cuerpo(f[4]),
                        "monto_inscrito": float(monto) if re.fullmatch(r"\d+(\.\d+)?", monto) else None,
                        "moneda": f[6].strip(), "fecha_vencimiento": fecha(f[7])})
    return out


def procesar_ps(hoy: str) -> list[dict]:
    todas = inscripciones_registro_automatico(_get(PS_URL))
    filas = json.loads((DOCS / f"{PS_BASE}.json").read_text(encoding="utf-8"))
    secs = {cuerpo(f["rut"]) for f in json.loads((DOCS / "securitizadoras/securitizadoras_maestro.json").read_text(encoding="utf-8"))}
    ps = [x for x in todas if x["rut"] in secs or "SECURITIZADORA" in _norm(x["razon_social"])]
    ya = {str(f["numero_inscripcion"]) for f in filas}
    if len(todas) < 100 or len(ya & {x["numero_inscripcion"] for x in ps}) < len(ya) / 2:
        print(f"::warning::patrimonios_separados: el listado CMF trae {len(todas)} inscripciones y "
              f"{len(ya & {x['numero_inscripcion'] for x in ps})} de las {len(ya)} de la lista; no se modifica")
        return []
    eventos = []
    for x in sorted(ps, key=lambda x: int(x["numero_inscripcion"])):
        if x["numero_inscripcion"] in ya:
            continue
        filas.append({"numero_inscripcion": x["numero_inscripcion"], "fecha_inscripcion": x["fecha_inscripcion"],
                      "rut_administradora": x["rut"], "razon_social_administradora": x["razon_social"],
                      "denominacion_emision": f"Línea N° {x['numero_inscripcion']} - {x['razon_social']}",
                      "tipo_emision": x["tipo_emision"], "moneda": x["moneda"], "monto_inscrito": x["monto_inscrito"],
                      "fecha_vencimiento": x["fecha_vencimiento"], "clase_colateral_subyacente": None})
        eventos.append({"fecha": hoy, "sector": "patrimonios_separados", "lista": PS_BASE,
                        "rut": x["rut"], "razon_social": f"N° {x['numero_inscripcion']} {x['razon_social']}",
                        "evento": "alta", "antes": None, "ahora": f"inscrita {x['fecha_inscripcion']}"})
    if eventos:
        filas.sort(key=lambda f: int(f["numero_inscripcion"]), reverse=True)
        guardar(PS_BASE, filas)
    print(f"patrimonios_separados · {PS_BASE}: listado CMF {len(todas)} inscripciones ({len(ps)} de securitizadoras); "
          f"lista {len(filas)} filas; cambios {len(eventos)}")
    return eventos


FI_MAESTRO = "fi/maestro_fondos_inversion"


def _norm_nombre(s) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"\bS\.A\.?\b", " ", s)
    s = re.sub(r"\bADMINISTRADORA GENERAL DE FONDOS\b", " ", s)
    return " ".join(s.upper().split())


def actualizar_fondos_agf() -> None:
    """AGF: cuántos fondos de inversión vigentes administra cada una.

    El registro CMF de AGF no publica ese número: se cuenta con el registro de
    fondos (FI), que anota la `administradora` de cada fondo. El cruce se hace
    por nombre normalizado (mayúsculas, sin «S.A.» ni «ADMINISTRADORA GENERAL
    DE FONDOS»); una AGF que no aparece administra 0 fondos de inversión. Sin
    esta pasada el campo queda en 0 para todas, como estaba.
    """
    ruta = DOCS / "agf/agf_maestro.json"
    fi = DOCS / f"{FI_MAESTRO}.parquet"
    if not ruta.exists() or not fi.exists():
        return
    tabla = pq.read_table(fi, columns=["administradora", "run_fondo", "estado_vigencia"]).to_pandas()
    vigentes = tabla[tabla["estado_vigencia"] == "Vigente"]
    conteo: dict[str, int] = {}
    for nombre, n in vigentes.groupby("administradora")["run_fondo"].nunique().items():
        conteo[_norm_nombre(nombre)] = max(conteo.get(_norm_nombre(nombre), 0), int(n))
    filas = json.loads(ruta.read_text(encoding="utf-8"))
    cambio = 0
    for f in filas:
        n = conteo.get(_norm_nombre(f.get("razon_social")))
        if n is None:
            n = conteo.get(_norm_nombre(f.get("nombre_fantasia")), 0)
        if f.get("fondos_inversion_administrados") != n:
            f["fondos_inversion_administrados"] = n
            cambio += 1
    if cambio:
        guardar("agf/agf_maestro", filas)
    print(f"agf · fondos_inversion_administrados: {cambio} AGF actualizadas "
          f"({vigentes['run_fondo'].nunique()} fondos vigentes en el registro FI)")


def actualizar_conteos_web() -> None:
    """Conteo «N entidades» del menú lateral (por archivo) y del diccionario (por id) de cada lista."""
    vistas = {AFP_BASE: "afp_maestro"}
    for nombre in ("sidebar.js", "data_dictionary.js"):
        ruta = RAIZ / "docs" / "js" / nombre
        s = ruta.read_text(encoding="utf-8")
        for base in bases():
            n = pq.ParquetFile(DOCS / f"{base}.parquet").metadata.num_rows
            if nombre == "sidebar.js":
                patron = rf'(rows: ")\d+( [^"]*", file: "outputs/{re.escape(base)}\.parquet")'
            else:
                vid = re.escape(vistas.get(base, base.split("/")[-1]))
                patron = rf'(id: "{vid}",(?:(?!\n  \}}).)*?registros: ")\d+( [^"]*")'
            s = re.sub(patron, rf"\g<1>{n}\g<2>", s, count=1, flags=re.S)
        ruta.write_text(s, encoding="utf-8")


# Listas que completa pipelines/ifrs_sectores/actualizar.py; aquí solo se cuentan.
BASES_IFRS = ["cajas_compensacion/ccaf_maestro", "factoring_leasing/factoring_leasing_maestro"]


def bases() -> list[str]:
    return [b for cfg in SECTORES.values() for b in cfg["archivos"]] + BASES_IFRS


def actualizar_data_manifest() -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    for t in man["tables"]:
        f = t.get("file_parquet") or ""
        if any(f == f"outputs/{b}.parquet" for b in bases()):
            t["registros_reales"] = pq.ParquetFile(DOCS / f[len("outputs/"):]).metadata.num_rows
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    ruta.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo-data-manifest", action="store_true")
    ap.add_argument("--solo-conteos", action="store_true", help="conteos del sitio y data_manifest, sin consultar la CMF")
    ap.add_argument("--sectores", nargs="*", default=list(SECTORES))
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest()
        return 0
    if a.solo_conteos:
        actualizar_data_manifest()
        actualizar_fondos_agf()
        actualizar_conteos_web()
        return 0
    hoy = date.today().isoformat()
    eventos, fallas = [], 0
    for s in a.sectores:
        try:
            eventos += procesar(s, SECTORES[s], hoy)
        except Exception as e:  # un registro caído no detiene a los demás
            fallas += 1
            print(f"::warning::{s}: {e}")
    for e in eventos:
        print(f"::notice::{e['sector']}: {e['evento']} {e['rut']} {e['razon_social']} ({e['antes']} → {e['ahora']})")
    NOVEDADES.parent.mkdir(parents=True, exist_ok=True)
    hist = json.loads(NOVEDADES.read_text()) if NOVEDADES.exists() else {"eventos": []}
    hist["eventos"] = hist["eventos"] + eventos
    hist["ultima_revision_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hist["sectores_revisados"] = a.sectores
    NOVEDADES.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n")
    actualizar_data_manifest()
    actualizar_fondos_agf()
    actualizar_conteos_web()
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"cambios={len(eventos)}\n")
    print(f"Cambios: {len(eventos)}. Registros con error: {fallas}")
    return 1 if fallas == len(a.sectores) else 0


if __name__ == "__main__":
    sys.exit(main())

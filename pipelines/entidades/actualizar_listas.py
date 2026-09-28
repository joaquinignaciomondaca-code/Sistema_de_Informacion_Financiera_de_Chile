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

Resguardo: si el registro vigente trae menos de la mitad de las entidades vigentes que ya
estaban en la lista (página caída o formato nuevo), ese sector no se modifica.

Otros sectores ya detectan solos sus entidades: FI (registro completo en cada corrida de
fi_carteras), FFMM y seguros (la lista sale de los archivos de cartera), AGF / securitizadoras
/ CCAF (el actualizador IFRS avisa quién reporta sin estar en la lista), corredores (idem).
"""
from __future__ import annotations

import argparse
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
        "alta": lambda c, d, nombre, url: {
            "rut": int(c), "dv": d, "rut_completo": puntos(c, d), "razon_social": nombre, "nombre_fantasia": nombre,
            "tipo_entidad": "Administradora General de Fondos", "marco_legal": "Ley N° 20.712 (Ley Única de Fondos - LUF)",
            "regulador": "CMF", "cmf_url": url, "fondos_inversion_administrados": 0},
    },
    "securitizadoras": {
        "archivos": ["securitizadoras/securitizadoras_maestro"], "codigo": "RGSEC", "mercado": "V",
        "rut": rut_str, "clave": "rut", "vig": ("VIGENTE", "NO VIGENTE / EN LIQUIDACION"),
        "alta": lambda c, d, nombre, url: {
            "rut": c, "dv": d, "rut_completo": f"{c}-{d}", "razon_social": nombre, "tipo_entidad_cmf": "RGSEC",
            "lineas_deuda_registradas": 0, "cmf_url": url},
    },
    "corredoras_bolsa": {
        # La lista de entidades no tiene vigencia; el registro único sí.
        "archivos": ["corredoras_bolsa/corredoras_bolsa_maestro", "corredoras_bolsa/corredoras_bolsa_registro_universo"],
        "codigo": "COBOL", "mercado": "V", "rut": rut_dv, "clave": "rut", "vig": ("Vigente", "No Vigente"),
        "alta": lambda c, d, nombre, url: {
            "rut": f"{c}-{d}", "rut_cuerpo": c, "dv": d, "nombre_empresa": nombre, "nombre_fantasia": nombre,
            "tipo_intermediario": "CORREDOR DE BOLSA", "tipo_entidad": "COBOL", "url_ficha_cmf": url},
    },
    "fintech": {
        "archivos": ["fintech/fintech_rpsf_maestro"], "codigo": "RGPSF", "mercado": "O",
        "rut": rut_int, "clave": "rut", "vig": ("Vigente", "No Vigente"),
        "alta": lambda c, d, nombre, url: {
            "rut": int(c), "dv": d, "rut_completo": puntos(c, d), "razon_social": nombre, "nombre_fantasia": nombre,
            "cmf_url": url, "servicios_acreditados_total": 0},
    },
}


class _Tablas(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tablas, self._t, self._f, self._c = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._t = {"th": [], "filas": []}
        elif tag == "tr" and self._t is not None:
            self._f = []
        elif tag in ("td", "th") and self._f is not None:
            self._c = [tag, ""]

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._c is not None and self._f is not None:
            self._f.append((self._c[0], " ".join(self._c[1].split())))
            self._c = None
        elif tag == "tr" and self._f is not None and self._t is not None:
            if self._f and all(t == "th" for t, _ in self._f):
                self._t["th"].append([v for _, v in self._f])
            elif self._f:
                self._t["filas"].append([v for _, v in self._f])
            self._f = None
        elif tag == "table" and self._t is not None:
            self.tablas.append(self._t)
            self._t = None

    def handle_data(self, data):
        if self._c is not None:
            self._c[1] += data


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


def registro(cfg: dict, estado: str) -> dict[str, tuple[str, str]]:
    """{cuerpo_rut: (dv, nombre)} de la lista CMF."""
    raw = _get(URL.format(mercado=cfg["mercado"], estado=estado, codigo=cfg["codigo"]))
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
    js, pqt = DOCS / f"{base}.json", DOCS / f"{base}.parquet"
    js.write_text(json.dumps(filas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if pqt.exists():
        esquema = pq.read_schema(pqt)
        df = pd.DataFrame(filas).reindex(columns=esquema.names)
        for campo in esquema:
            if pa.types.is_integer(campo.type):
                df[campo.name] = pd.to_numeric(df[campo.name], errors="coerce").fillna(0).astype("int64")
        pq.write_table(pa.Table.from_pandas(df, schema=esquema.remove_metadata(), preserve_index=False), pqt)


def procesar(sector: str, cfg: dict, hoy: str) -> list[dict]:
    vi, nv = registro(cfg, "VI"), registro(cfg, "NV")
    eventos = []
    for base in cfg["archivos"]:
        ruta = DOCS / f"{base}.json"
        filas = json.loads(ruta.read_text(encoding="utf-8"))
        tiene_vig = any("estado_vigencia" in f for f in filas)
        en_lista = {cuerpo(f[cfg["clave"]]) for f in filas}
        vigentes_antes = {cuerpo(f[cfg["clave"]]) for f in filas
                          if not tiene_vig or f.get("estado_vigencia") == cfg["vig"][0]}
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
            if nuevo and f.get("estado_vigencia") != nuevo:
                eventos.append({"fecha": hoy, "sector": sector, "lista": base, "rut": f"{c}-{(vi.get(c) or nv.get(c))[0]}",
                                "razon_social": (vi.get(c) or nv.get(c))[1], "evento": "cambio_vigencia",
                                "antes": f.get("estado_vigencia"), "ahora": nuevo})
                f["estado_vigencia"] = nuevo
                cambio = True
        columnas = list(filas[0].keys()) if filas else []
        for c, (d, nombre) in sorted(vi.items()):
            if c in en_lista:
                continue
            url = FICHA.format(mercado=cfg["mercado"], rut=c, codigo=cfg["codigo"], estado="VI")
            alta = cfg["alta"](c, d, nombre, url)
            if tiene_vig:
                alta["estado_vigencia"] = cfg["vig"][0]
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


def actualizar_data_manifest() -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists():
        return
    man = json.loads(ruta.read_text())
    for t in man["tables"]:
        f = t.get("file_parquet") or ""
        if any(f == f"outputs/{b}.parquet" for cfg in SECTORES.values() for b in cfg["archivos"]):
            t["registros_reales"] = pq.ParquetFile(DOCS / f[len("outputs/"):]).metadata.num_rows
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    ruta.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo-data-manifest", action="store_true")
    ap.add_argument("--sectores", nargs="*", default=list(SECTORES))
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest()
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
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"cambios={len(eventos)}\n")
    print(f"Cambios: {len(eventos)}. Registros con error: {fallas}")
    return 1 if fallas == len(a.sectores) else 0


if __name__ == "__main__":
    sys.exit(main())

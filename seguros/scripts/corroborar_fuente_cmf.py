"""Corrobora contra la fuente: descarga los ZIP reales de la CMF y compara con lo publicado.

La auditoría de 2026-10-07 atribuyó los hallazgos de calidad (duplicados exactos, doble
reporte de control en fusiones, fechas imposibles) a la fuente, por consistencia interna.
Este script comprueba esa atribución con evidencia directa: descarga el ZIP del mes pedido,
mira el archivo crudo y responde:

  1. duplicados: ¿el archivo crudo trae las mismas líneas repetidas que se publicaron?
  2. doble reporte: ¿el ZIP trae dos archivos de control (C) para la misma compañía, o un
     archivo con el mismo tipo_inversion dos veces con valores distintos?
  3. fechas imposibles: ¿la fecha (p. ej. vencimiento 2173) aparece en la línea cruda?
  4. fidelidad: ¿releer el ZIP con el lector del repo reproduce exactamente lo publicado
     (filas y duplicados por tabla)?

Uso:
  python -m seguros.scripts.corroborar_fuente_cmf 2025-03:vida 2024-06:generales ...

Escribe un JSON por mes en /tmp/corroboracion/ (en Actions se sube como artifact).
"""
from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from seguros.scripts.actualizar_carteras import SALIDA, SECTORES, TABLAS, descargar, leer_zip

SALIDA_CORRO = Path("/tmp/corroboracion")
# Años imposibles como vencimiento (2170-2199 en AAAAMMDD).
RE_FECHA_RARA = re.compile(rb"21[7-9]\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])")
POR_MES = {"renta_fija", "bienes_raices"}


def leer_publicado(tabla: str, periodo: str) -> pd.DataFrame:
    nombre = f"{periodo}.parquet" if tabla in POR_MES else f"{periodo[:4]}.parquet"
    ruta = SALIDA / tabla / nombre
    if not ruta.exists():
        return pd.DataFrame()
    return pq.read_table(ruta).to_pandas().query("periodo == @periodo")


def analizar(sector: str, periodo: str) -> dict:
    data = descargar(sector, periodo, None)
    z = zipfile.ZipFile(io.BytesIO(data))
    rep = {"sector": sector, "periodo": periodo, "duplicados": [], "dobles_c": [],
           "fechas_raras": [], "fidelidad": {}, "exclusiones": []}
    c_por_rut: dict[str, list] = {}
    for nombre in sorted(z.namelist()):
        if nombre.endswith("/"):
            continue
        raw = z.read(nombre)
        lineas = [ln for ln in raw.split(b"\n") if ln.strip(b"\r\n\x1a ")]
        cnt = Counter(lineas)
        dups = {k: v for k, v in cnt.items() if v > 1}
        if dups:
            _archivo, veces = max(dups.items(), key=lambda kv: kv[1])
            rep["duplicados"].append({
                "archivo": nombre, "lineas": len(lineas),
                "filas_de_mas": sum(v - 1 for v in dups.values()),
                "max_multiplicidad": max(dups.values()),
                "ejemplo": _archivo[:140].decode("latin-1"), "veces_ejemplo": veces})
        if nombre.split(".")[0][:1].lower() == "c":
            m = re.search(r"(\d{7,9})", nombre)
            c_por_rut.setdefault(m.group(1) if m else "?", []).append(nombre)
        for ln in lineas:
            mm = RE_FECHA_RARA.search(ln)
            if mm:
                rep["fechas_raras"].append({
                    "archivo": nombre, "fecha": mm.group(0).decode(),
                    "contexto": ln[max(0, mm.start() - 12):mm.end() + 4].decode("latin-1")})
    rep["dobles_c_zip"] = {r: ns for r, ns in c_por_rut.items() if len(ns) > 1}
    # Releer con el lector del repo y comparar con lo publicado.
    filas, _comp, avisos, exc = leer_zip(data, periodo, sector)
    rep["exclusiones"] = exc
    # Doble reporte dentro de las filas leídas: mismo (rut, tipo_inversion), valores distintos.
    vals: dict[tuple, set] = {}
    for f in filas["control_inversiones"]:
        vals.setdefault((f["rut_aseguradora"], f["tipo_inversion"]), set()).add(f["valor_final_m_clp"])
    rep["dobles_c"] = [f"{r} tipo {t}: {len(v)} valores" for (r, t), v in sorted(vals.items()) if len(v) > 1]
    for t in TABLAS:
        pub = leer_publicado(t, periodo)
        nuevo = pd.DataFrame(filas[t])
        rep["fidelidad"][t] = {
            "publicado": int(len(pub)), "releido": int(len(nuevo)),
            "duplicados_publicados": int(pub.duplicated().sum()),
            "duplicados_releidos": int(nuevo.duplicated().sum())}
    rep["avisos_relectura"] = len(avisos)
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("meses", nargs="+", help="meses a corroborar, con formato AAAA-MM:vida|generales")
    a = ap.parse_args()
    SALIDA_CORRO.mkdir(parents=True, exist_ok=True)
    for arg in a.meses:
        periodo, sector = arg.rsplit(":", 1)
        if sector not in SECTORES or not re.fullmatch(r"\d{4}-\d{2}", periodo):
            ap.error(f"mes inválido: {arg} (use AAAA-MM:vida|generales)")
        rep = analizar(sector, periodo)
        (SALIDA_CORRO / f"{sector}_{periodo}.json").write_text(json.dumps(rep, indent=1, default=str))
        print(f"\n{sector} {periodo}: {len(rep['duplicados'])} archivos con duplicados en crudo · "
              f"dobles C en ZIP: {rep['dobles_c_zip']} · dobles C releídos: {len(rep['dobles_c'])} · "
              f"fechas raras en crudo: {len(rep['fechas_raras'])}")
        for d in rep["duplicados"][:4]:
            print(f"   dup: {d['archivo']}: {d['filas_de_mas']} filas de más (máx x{d['max_multiplicidad']})")
        for t, v in rep["fidelidad"].items():
            igual = v["publicado"] == v["releido"] and v["duplicados_publicados"] == v["duplicados_releidos"]
            print(f"   {t}: publicado {v['publicado']} / releído {v['releido']} · "
                  f"duplicados {v['duplicados_publicados']}/{v['duplicados_releidos']} "
                  f"{'OK' if igual else 'DIFiere'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Prueba el lector de la Circular 1835 con líneas reales de la CMF (seguros/fuentes/muestras_1835).

Cada muestra trae hasta 3 líneas por tipo de registro y compañía, en ambos formatos
(v2016 hasta 2024-11, v2024 desde 2024-12). Se arma un ZIP por sector y mes y se lee
con el mismo código que usa la actualización mensual.

  python -m seguros.tests.test_formato_1835
"""
import io
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

from seguros.scripts.actualizar_carteras import SECTORES, leer_zip

MUESTRAS = Path(__file__).resolve().parents[1] / "fuentes" / "muestras_1835"
SECTOR = {v: k for k, v in SECTORES.items()}


def zips():
    grupos = defaultdict(lambda: defaultdict(list))
    for f in sorted(MUESTRAS.glob("*.txt")):
        ent, yyyymm, _ = f.stem.split("_")
        for raw in f.read_bytes().split(b"\n"):
            if b"|" in raw:
                nombre, linea = raw.split(b"|", 1)
                grupos[(ent, yyyymm)][nombre.decode()].append(linea.rstrip(b"\r"))
    for (ent, yyyymm), archivos in sorted(grupos.items()):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for nombre, lineas in archivos.items():
                z.writestr(nombre, b"\r\n".join(lineas) + b"\r\n")
        yield SECTOR[ent], f"{yyyymm[:4]}-{yyyymm[4:]}", buf.getvalue()


def main():
    fallas = 0
    for sector, periodo, data in zips():
        filas, comp, avisos = leer_zip(data, periodo, sector)
        n = {t: len(v) for t, v in filas.items() if v}
        print(f"{sector:9} {periodo}: {len(comp)} compañías · " + ", ".join(f"{t} {k}" for t, k in n.items()))
        rf = pd.DataFrame(filas["renta_fija"])
        if len(rf):  # cuadratura de bonos: costo amortizado - deterioro = valor final (M$) x 1000
            ok = rf.dropna(subset=["costo_amortizado_clp", "valor_final_m_clp"])
            dif = (ok["costo_amortizado_clp"] - ok["deterioro_clp"].fillna(0) - ok["valor_final_m_clp"] * 1000).abs()
            cuadra = ((dif <= 1000) | (ok["valor_razonable_clp"].fillna(0) > 0)).mean()
            fechas = rf["fecha_vencimiento"].dropna()
            validas = fechas.map(lambda s: bool(re.fullmatch(r"(19|20|21)\d\d-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])", s))).mean()
            print(f"          bonos: cuadratura {cuadra:.1%}, vencimientos válidos {validas:.1%}")
            if cuadra < 0.95 or validas < 0.99:
                fallas += 1
        for t in ("acciones", "fondos_mutuos", "bienes_raices", "extranjeros", "derivados", "pactos"):
            df = pd.DataFrame(filas[t])
            for c in [c for c in df.columns if c.startswith("fecha")]:
                f = df[c].dropna()
                if len(f) and not f.str.match(r"(19|20|21)\d\d-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$").all():
                    print(f"          FALLA {t}.{c}: {f[~f.str.match(r'(19|20|21)').fillna(False)].head(3).tolist()}")
                    fallas += 1
    assert fallas == 0, f"{fallas} fallas"
    print("OK")


if __name__ == "__main__":
    main()

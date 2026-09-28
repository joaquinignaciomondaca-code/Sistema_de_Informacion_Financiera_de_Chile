#!/usr/bin/env python3
"""Series del Banco Central (API REST SIETE) en formato largo: una fila por serie y fecha.

Complementa las tres tablas mensuales de macro con un catálogo amplio de series (tasas, tipo de
cambio, precios, actividad, empleo, commodities, bolsa, sector externo, fiscal y expectativas),
cada una con su frecuencia original (diaria, mensual o trimestral). Agregar una serie = sumar una
línea a CATALOGO.

Incremental: por serie, solo se consulta desde la última fecha guardada menos una ventana de
revisión (10 días en diarias, 6 meses en mensuales, 13 meses en trimestrales). Fail-closed:
  - una observación ya publicada nunca se borra (si la API no la trae, se conserva),
  - una serie que falla o no existe en el BCCh no bloquea a las demás: queda con su estado en el
    catálogo y se avisa en Actions; si fallan todas (credenciales o API caída) no se escribe nada,
  - solo valores numéricos; fechas futuras se descartan.

Salida (docs/outputs/macro/):
  series/<AAAA>.parquet + series/manifest.json   observaciones (fecha, periodo, clave, valor)
  macro_series_catalogo.parquet                  una fila por serie: código, nombre, grupo,
                                                 frecuencia, unidad, título oficial BCCh,
                                                 primera/última fecha, observaciones, estado
Credenciales: BCCH_EMAIL y BCCH_PASSWORD (secrets USER_BCCH / PASSWORD_BCCH en Actions).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "docs" / "outputs" / "macro"
CARPETA = SALIDA / "series"
CATALOGO_PQ = SALIDA / "macro_series_catalogo.parquet"
API = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
DESDE = "2014-01-01"
VENTANA = {"D": 10, "M": 183, "T": 400}  # días de relectura para capturar revisiones
MENSUALES = ("macro_tasas_rendimientos", "macro_divisas_mercado", "macro_precios_actividad")
FRECUENCIA = {"D": "Diaria", "M": "Mensual", "T": "Trimestral"}

# clave, código SIETE, grupo, unidad, nombre corto
_C = [
    # Tasas y renta fija
    ("tpm", "F022.TPM.TIN.D001.NO.Z.D", "Tasas", "%", "Tasa de política monetaria (diaria)"),
    ("tib", "F022.TIB.TIP.D001.NO.Z.D", "Tasas", "%", "Tasa interbancaria promedio (diaria)"),
    ("spc_clp_90d", "F022.SPC.TPR.D090.NO.Z.D", "Tasas", "%", "Swap promedio cámara pesos 90 días"),
    ("spc_clp_180d", "F022.SPC.TPR.D180.NO.Z.D", "Tasas", "%", "Swap promedio cámara pesos 180 días"),
    ("spc_clp_360d", "F022.SPC.TPR.D360.NO.Z.D", "Tasas", "%", "Swap promedio cámara pesos 360 días"),
    ("spc_clp_2y", "F022.SPC.TIN.AN02.NO.Z.D", "Tasas", "%", "Swap promedio cámara pesos 2 años"),
    ("spc_uf_1y", "F022.SPC.TIN.AN01.UF.Z.D", "Tasas", "%", "Swap promedio cámara UF 1 año"),
    ("bcp_2y", "F022.BCLP.TIS.AN02.NO.Z.D", "Tasas", "%", "Bonos en pesos 2 años (BCP/BTP)"),
    ("bcp_5y", "F022.BCLP.TIS.AN05.NO.Z.D", "Tasas", "%", "Bonos en pesos 5 años (BCP/BTP)"),
    ("bcp_10y", "F022.BCLP.TIS.AN10.NO.Z.D", "Tasas", "%", "Bonos en pesos 10 años (BCP/BTP)"),
    ("bcu_1y", "F022.BUF.TIS.AN01.UF.Z.D", "Tasas", "%", "Bonos en UF 1 año (BCU/BTU)"),
    ("bcu_2y", "F022.BUF.TIS.AN02.UF.Z.D", "Tasas", "%", "Bonos en UF 2 años (BCU/BTU)"),
    ("bcu_5y", "F022.BUF.TIS.AN05.UF.Z.D", "Tasas", "%", "Bonos en UF 5 años (BCU/BTU)"),
    ("bcu_10y", "F022.BUF.TIS.AN10.UF.Z.D", "Tasas", "%", "Bonos en UF 10 años (BCU/BTU)"),
    ("bcu_20y", "F022.BUF.TIS.AN20.UF.Z.D", "Tasas", "%", "Bonos en UF 20 años (BCU/BTU)"),
    ("bcu_30y", "F022.BUF.TIS.AN30.UF.Z.D", "Tasas", "%", "Bonos en UF 30 años (BCU/BTU)"),
    # Tipo de cambio
    ("usd_clp", "F073.TCO.PRE.Z.D", "Tipo de cambio", "CLP por USD", "Dólar observado"),
    ("eur_clp", "F072.CLP.EUR.N.O.D", "Tipo de cambio", "CLP por EUR", "Euro observado"),
    ("tcm", "F073.TCM.IND.199502.D", "Tipo de cambio", "Índice", "Tipo de cambio multilateral (TCM)"),
    ("tcm_5", "F073.TM5.IND.199001.D", "Tipo de cambio", "Índice", "Tipo de cambio multilateral 5 monedas (TCM-5)"),
    ("tcm_x", "G073.TCMX.IND.199801.D", "Tipo de cambio", "Índice", "Tipo de cambio multilateral sin EE.UU. (TCM-X)"),
    ("tcr", "F073.TCR.IND.199101.M", "Tipo de cambio", "Índice", "Tipo de cambio real"),
    ("tcr_5", "F073.TR5.IND.198601.M", "Tipo de cambio", "Índice", "Tipo de cambio real 5 monedas"),
    # Precios y reajustes
    ("uf", "F073.UFF.PRE.Z.D", "Precios y reajustes", "CLP", "Unidad de fomento"),
    ("utm", "F073.UTR.PRE.Z.M", "Precios y reajustes", "CLP", "Unidad tributaria mensual"),
    ("ipc_indice", "G073.IPC.IND.2023.M", "Precios y reajustes", "Índice 2023=100", "IPC general"),
    ("ipc_var_mensual", "G073.IPC.VAR.2023.M", "Precios y reajustes", "%", "IPC, variación mensual"),
    ("ipc_var_anual", "G073.IPC.V12.2023.M", "Precios y reajustes", "%", "IPC, variación en 12 meses"),
    # Actividad
    ("imacec", "F032.ICF.IND.Z.Z.EP18.Z.Z.0.M", "Actividad", "Índice 2018=100", "Imacec empalmado"),
    ("imacec_no_minero", "F032.IMC.IND.Z.Z.EP18.N03.Z.0.M", "Actividad", "Índice 2018=100", "Imacec no minero"),
    ("imacec_mineria", "F032.IMC.IND.Z.Z.EP18.03.Z.0.M", "Actividad", "Índice 2018=100", "Imacec minería"),
    ("imacec_comercio", "F032.IMC.IND.Z.Z.EP18.COM.Z.0.M", "Actividad", "Índice 2018=100", "Imacec comercio"),
    ("imacec_servicios", "F032.IMC.IND.Z.Z.EP18.SERV.Z.0.M", "Actividad", "Índice 2018=100", "Imacec servicios"),
    ("pib", "F032.PIB.FLU.R.CLP.EP18.Z.Z.0.T", "Actividad", "Miles de millones CLP encadenados", "PIB trimestral (volumen)"),
    # Mercado laboral
    ("desocupacion", "F049.DES.TAS.INE9.10.M", "Mercado laboral", "%", "Tasa de desocupación nacional"),
    ("ocupados", "F049.OCU.PMT.INE9.01.M", "Mercado laboral", "Miles de personas", "Ocupados"),
    ("asalariados", "F049.OCU.PMT.INE9.87.M", "Mercado laboral", "Miles de personas", "Asalariados"),
    ("fuerza_trabajo", "F049.FTR.PMT.INE9.01.M", "Mercado laboral", "Miles de personas", "Fuerza de trabajo"),
    # Commodities
    ("cobre_diario", "F019.PPB.PRE.100.D", "Commodities", "USD por libra", "Cobre refinado BML (diario)"),
    ("cobre_mensual", "F019.PPB.PRE.40.M", "Commodities", "USD por libra", "Cobre refinado BML (mensual)"),
    ("oro", "F019.PPB.PRE.44.D", "Commodities", "USD por onza troy", "Oro"),
    ("plata", "F019.PPB.PRE.45.D", "Commodities", "USD por onza troy", "Plata"),
    # Bolsa
    ("ipsa", "F013.IBC.IND.N.7.LAC.CL.CLP.BLO.D", "Bolsa", "Índice", "IPSA"),
    # Sector externo
    ("reservas", "F062.A5.STO.PF.USD.M", "Sector externo", "Millones de USD", "Reservas internacionales"),
    ("treasury_10y", "F019.TBG.TAS.10.D", "Sector externo", "%", "Bono del Tesoro de EE.UU. 10 años"),
    ("fed_funds", "F019.TPM.TIN.10.D", "Sector externo", "%", "Tasa de política monetaria de EE.UU."),
    # Fiscal
    ("deuda_publica_pib", "F051.D7.PPB.C.Z.Z.T", "Fiscal", "% del PIB", "Deuda bruta del Gobierno Central"),
    # Expectativas
    ("eee_ipc_11m", "F089.IPC.V12.14.M", "Expectativas", "%", "Encuesta de expectativas (EEE): inflación a 11 meses"),
    ("eee_ipc_23m", "F089.IPC.V12.15.M", "Expectativas", "%", "Encuesta de expectativas (EEE): inflación a 23 meses"),
    ("eee_tpm_11m", "F089.TPM.TAS.14.M", "Expectativas", "%", "Encuesta de expectativas (EEE): TPM a 11 meses"),
    ("eee_tpm_23m", "F089.TPM.TAS.15.M", "Expectativas", "%", "Encuesta de expectativas (EEE): TPM a 23 meses"),
    ("eof_ipc_12m", "F089.EOF.VII.12MS.D", "Expectativas", "%", "Encuesta de operadores financieros (EOF): inflación a 12 meses"),
    ("eof_tpm_12m", "F089.EOF.TPM.12MS.D", "Expectativas", "%", "Encuesta de operadores financieros (EOF): TPM a 12 meses"),
]
CATALOGO = [{"clave": c, "serie_id": s, "grupo": g, "unidad": u, "nombre": n, "frecuencia": s.rsplit(".", 1)[1]}
            for c, s, g, u, n in _C]
assert len({c["clave"] for c in CATALOGO}) == len(CATALOGO), "claves repetidas"

ESQUEMA = pa.schema([("fecha", pa.string()), ("periodo", pa.string()), ("clave", pa.string()),
                     ("serie_id", pa.string()), ("valor", pa.float64())])


class ErrorApi(Exception):
    pass


def consultar(serie_id: str, desde: str, hasta: str, usuario: str, clave: str) -> tuple[str, list[tuple[str, float]]]:
    """(título oficial, [(AAAA-MM-DD, valor)]) de GetSeries. No incluye credenciales en los errores."""
    q = urllib.parse.urlencode({"user": usuario, "pass": clave, "function": "GetSeries", "timeseries": serie_id,
                                "firstdate": desde, "lastdate": hasta})
    ultimo = "sin respuesta"
    for intento in range(3):
        try:
            with urllib.request.urlopen(f"{API}?{q}", timeout=120) as r:
                crudo = r.read()
            break
        except Exception as e:  # red: reintentar
            ultimo = type(e).__name__
            time.sleep(3 * (intento + 1))
    else:
        raise ErrorApi(f"sin conexión ({ultimo})")
    # La API responde en UTF-8 o en Windows-1252 según la serie (títulos con tildes).
    try:
        texto = crudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = crudo.decode("cp1252", errors="replace")
    try:
        d = json.loads(texto)
    except ValueError:
        raise ErrorApi("respuesta no es JSON")
    if d.get("Codigo") != 0:
        raise ErrorApi(f"BCCh código {d.get('Codigo')}: {d.get('Descripcion')}")
    serie = d.get("Series") or {}
    obs = []
    for o in serie.get("Obs") or []:
        if str(o.get("statusCode", "OK")).upper() != "OK":
            continue
        try:
            v = float(str(o["value"]).replace(",", "."))
        except (TypeError, ValueError):
            continue
        if v != v:  # NaN
            continue
        f = datetime.strptime(o["indexDateString"], "%d-%m-%Y").date().isoformat()
        obs.append((f, v))
    return serie.get("descripEsp") or "", obs


def cargar() -> pd.DataFrame:
    rutas = sorted(CARPETA.glob("*.parquet"))
    if not rutas:
        return pd.DataFrame(columns=ESQUEMA.names)
    return pd.concat([pq.read_table(r).to_pandas() for r in rutas], ignore_index=True)


def cargar_control() -> dict:
    ruta = CARPETA / "manifest.json"
    if ruta.exists():
        c = json.loads(ruta.read_text())
        c.setdefault("series", {})
        return c
    return {"series": {}}


def inicio_consulta(cat: dict, previo: pd.DataFrame) -> str:
    fechas = previo.loc[previo["clave"] == cat["clave"], "fecha"]
    if fechas.empty:
        return DESDE
    ultima = date.fromisoformat(fechas.max())
    return max(DESDE, (ultima - timedelta(days=VENTANA[cat["frecuencia"]])).isoformat())


def combinar(previo: pd.DataFrame, clave: str, serie_id: str, nuevas: list[tuple[str, float]]) -> pd.DataFrame:
    """Las observaciones nuevas reemplazan a las de la misma fecha; ninguna previa se borra."""
    hoy = date.today().isoformat()
    nuevas = [(f, v) for f, v in nuevas if DESDE <= f <= hoy]
    if not nuevas:
        return previo
    df = pd.DataFrame(nuevas, columns=["fecha", "valor"])
    df["periodo"], df["clave"], df["serie_id"] = df["fecha"].str[:7], clave, serie_id
    otras = previo[~((previo["clave"] == clave) & previo["fecha"].isin(df["fecha"]))]
    return pd.concat([otras, df[ESQUEMA.names]], ignore_index=True)


def escribir(df: pd.DataFrame, previo: pd.DataFrame) -> list[str]:
    """Escribe solo los años que cambian. Devuelve los años escritos."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    df = df.sort_values(["clave", "fecha"], kind="stable").reset_index(drop=True)
    escritos = []
    for anio, parte in df.groupby(df["fecha"].str[:4]):
        viejo = previo[previo["fecha"].str[:4] == anio].sort_values(["clave", "fecha"], kind="stable")
        parte = parte.reset_index(drop=True)
        if len(viejo) == len(parte) and viejo.reset_index(drop=True)[ESQUEMA.names].equals(parte[ESQUEMA.names]):
            continue
        tmp = CARPETA / f"{anio}.tmp"
        pq.write_table(pa.Table.from_pandas(parte[ESQUEMA.names], schema=ESQUEMA, preserve_index=False), tmp,
                       compression="zstd", compression_level=9)
        os.replace(tmp, CARPETA / f"{anio}.parquet")
        escritos.append(anio)
    return escritos


def escribir_catalogo(df: pd.DataFrame, control: dict) -> None:
    filas = []
    for c in CATALOGO:
        sub = df.loc[df["clave"] == c["clave"], "fecha"]
        info = control["series"].get(c["clave"], {})
        filas.append({**{k: c[k] for k in ("clave", "serie_id", "nombre", "grupo", "unidad")},
                      "frecuencia": FRECUENCIA[c["frecuencia"]], "titulo_bcch": info.get("titulo_bcch"),
                      "primera_fecha": sub.min() if len(sub) else None, "ultima_fecha": sub.max() if len(sub) else None,
                      "observaciones": int(len(sub)), "estado": info.get("estado", "pendiente"),
                      "ultima_consulta_utc": info.get("ultima_consulta_utc")})
    t = pd.DataFrame(filas)
    t["observaciones"] = t["observaciones"].astype("int64")
    pq.write_table(pa.Table.from_pandas(t, preserve_index=False), CATALOGO_PQ, compression="zstd")


def actualizar_data_manifest() -> None:
    ruta = RAIZ / "data_manifest.json"
    if not ruta.exists() or not CATALOGO_PQ.exists():
        return
    man = json.loads(ruta.read_text())
    man_series = json.loads((CARPETA / "manifest.json").read_text())
    cat = pq.read_table(CATALOGO_PQ).to_pandas()
    corte = f"{cat['primera_fecha'].dropna().min()} a {cat['ultima_fecha'].dropna().max()}"
    hoy = date.today().isoformat()
    origen = "Banco Central de Chile — Base de Datos Estadísticos (API REST SIETE, https://si3.bcentral.cl/SieteRestWS)."
    base = {"sector": "macro", "sector_label": "Macroeconomía (BCCh)", "norma": "Estadísticas oficiales BCCh",
            "corte": corte, "frescura": "Se actualiza sola a diario", "modo": "Automático · diario, incremental",
            "ultima_actualizacion": hoy, "origen": origen}
    entradas = [
        {"id": "macro_series", "name": "macro.series", "view_name": "macro_series", **base,
         "file_parquet": "outputs/macro/series/manifest.json", "registros_reales": man_series["total_records"],
         "descripcion": "Observaciones de todas las series del catálogo, una fila por serie y fecha, en su "
                        "frecuencia original (diaria, mensual o trimestral)."},
        {"id": "macro_series_catalogo", "name": "macro.series_catalogo", "view_name": "macro_series_catalogo", **base,
         "file_parquet": "outputs/macro/macro_series_catalogo.parquet", "registros_reales": len(cat),
         "descripcion": "Catálogo de series del Banco Central publicadas: código SIETE, nombre, grupo, frecuencia, "
                        "unidad, título oficial, cobertura y estado."},
    ]
    # Tablas mensuales: corte y filas desde los Parquet publicados (el reintento del commit
    # rehace data_manifest sobre la versión remota y no debe perder su actualización).
    for t in man["tables"]:
        pqt = SALIDA / f"{t['id']}.parquet"
        if t["id"] in MENSUALES and pqt.exists():
            per = pq.read_table(pqt, columns=["periodo"]).column(0).to_pylist()
            nuevo = {"corte": f"{per[0]} a {per[-1]}", "registros_reales": len(per)}
            if any(t.get(k) != v for k, v in nuevo.items()):
                t.update(nuevo, ultima_actualizacion=hoy)
    ids = {e["id"] for e in entradas}
    man["tables"] = [t for t in man["tables"] if t["id"] not in ids] + entradas
    man["total_tables"] = len(man["tables"])
    man["total_records"] = sum(int(t.get("registros_reales") or 0) for t in man["tables"])
    man["updated_at"] = hoy
    ruta.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo-data-manifest", action="store_true")
    ap.add_argument("--claves", nargs="*", help="solo estas series (pruebas)")
    a = ap.parse_args(argv)
    if a.solo_data_manifest:
        actualizar_data_manifest()
        return 0
    usuario, clave = os.environ.get("BCCH_EMAIL", ""), os.environ.get("BCCH_PASSWORD", "")
    if not usuario or not clave:
        print("::error::Faltan BCCH_EMAIL / BCCH_PASSWORD")
        return 1
    control = cargar_control()
    previo = cargar()
    hoy = date.today().isoformat()
    cats = [c for c in CATALOGO if not a.claves or c["clave"] in a.claves]

    def bajar(c):
        desde = inicio_consulta(c, previo)
        try:
            return c, desde, consultar(c["serie_id"], desde, hoy, usuario, clave), None
        except ErrorApi as e:
            return c, desde, None, str(e)

    df, fallas, nuevas_obs = previo.copy(), [], 0
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with ThreadPoolExecutor(max_workers=6) as ex:
        for c, desde, res, err in ex.map(bajar, cats):
            info = control["series"].setdefault(c["clave"], {})
            info["serie_id"], info["ultima_consulta_utc"] = c["serie_id"], ahora
            if err:
                fallas.append(c["clave"])
                info["estado"] = f"error: {err}"[:200]
                print(f"::warning::{c['clave']} ({c['serie_id']}): {err}")
                continue
            titulo, obs = res
            if titulo:
                info["titulo_bcch"] = titulo
            antes = int((df["clave"] == c["clave"]).sum())
            df = combinar(df, c["clave"], c["serie_id"], obs)
            despues = int((df["clave"] == c["clave"]).sum())
            nuevas_obs += despues - antes
            if despues == 0:
                info["estado"] = "sin datos en el BCCh"
                print(f"::warning::{c['clave']} ({c['serie_id']}): el BCCh no entrega observaciones desde {desde}")
            else:
                info["estado"] = "ok"
            print(f"{c['clave']:20} {c['serie_id']:38} desde {desde}: {len(obs):5d} obs. · total {despues}")
    if fallas and len(fallas) == len(cats):
        print("::error::Fallaron todas las series (credenciales o API); no se escribe nada")
        return 1
    # Anti-regresión: ninguna serie puede quedar con menos observaciones que antes.
    for c in cats:
        if (df["clave"] == c["clave"]).sum() < (previo["clave"] == c["clave"]).sum():
            raise SystemExit(f"regresión de observaciones en {c['clave']}; no se escribe nada")
    anios = escribir(df, previo)
    rutas = sorted(CARPETA.glob("*.parquet"))
    control.update({"files": [f"outputs/macro/series/{r.name}" for r in rutas],
                    "total_records": int(sum(pq.ParquetFile(r).metadata.num_rows for r in rutas)),
                    "series_en_catalogo": len(CATALOGO), "updated_at": ahora})
    (CARPETA / "manifest.json").write_text(json.dumps(control, ensure_ascii=False, indent=2) + "\n")
    escribir_catalogo(df, control)
    actualizar_data_manifest()
    print(f"Observaciones nuevas: {nuevas_obs}. Años reescritos: {anios or 'ninguno'}. Series con error: {len(fallas)}")
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"series_cambios={len(anios)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

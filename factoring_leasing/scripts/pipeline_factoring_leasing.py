"""
Pipeline único del sector Factoring & Leasing (CMF) — v2.0

Fuente: Estados Financieros IFRS en texto plano publicados por la CMF
        https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio=YYYYMM&termino=YYYYMM
Formato de cada línea: periodo;rut;nombre;ind_cons;moneda;cuenta;valor;taxonomia;estado_financiero

Salidas (docs/outputs/factoring_leasing/):
  factoring_leasing_maestro.parquet/.json         catálogo (desde data/catalogo_factoring_leasing.json)
  factoring_leasing_eeff_cuentas.parquet          TODAS las cuentas CMF de las entidades objetivo, formato largo
  factoring_leasing_balance_resumen.parquet/.json resumen derivado del formato largo con data/mapeo_cuentas.json
  factoring_leasing_cobertura.parquet/.json       entidad x trimestre: ok | sin_archivo | sin_entidad | sin_total_activos

Trazabilidad: cada fila lleva fuente_url, metodo, fecha_extraccion y script_version.
Sin secretos, sin rutas locales, sin fallbacks silenciosos de tipo de cambio.

Uso:
  python factoring_leasing/scripts/pipeline_factoring_leasing.py --step todo               # maestro + descarga incremental + resumen
  python factoring_leasing/scripts/pipeline_factoring_leasing.py --step descargar --desde 202503
  python factoring_leasing/scripts/pipeline_factoring_leasing.py --step descargar --solo-faltantes
  python factoring_leasing/scripts/pipeline_factoring_leasing.py --step resumen
  python factoring_leasing/scripts/pipeline_factoring_leasing.py --step descargar --fixture tests/fixture_cmf_202503.txt  # prueba offline

Dependencias: pandas, pyarrow (ver requirements.txt). Sin bcchapi: el TC sale de docs/outputs/macro/macro_divisas_mercado.parquet.
"""
import os
import re
import sys
import json
import ssl
import time
import argparse
import calendar
import unicodedata
import urllib.request
from datetime import datetime, date

import pandas as pd

SCRIPT_VERSION = "2.0.0"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SECTOR_DIR = os.path.join(BASE_DIR, "factoring_leasing")
DATA_DIR = os.path.join(SECTOR_DIR, "data")
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "factoring_leasing")
CATALOGO = os.path.join(DATA_DIR, "catalogo_factoring_leasing.json")
MAPEO = os.path.join(DATA_DIR, "mapeo_cuentas.json")
NO_MAPEADAS = os.path.join(DATA_DIR, "cuentas_no_mapeadas.json")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")

P_MAESTRO = os.path.join(OUT_DIR, "factoring_leasing_maestro.parquet")
P_CUENTAS = os.path.join(OUT_DIR, "factoring_leasing_eeff_cuentas.parquet")
P_RESUMEN = os.path.join(OUT_DIR, "factoring_leasing_balance_resumen.parquet")
P_COBERTURA = os.path.join(OUT_DIR, "factoring_leasing_cobertura.parquet")

CMF_URL = "https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php?inicio={q}&termino={q}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MonitorFinancieroChile/2.0; +https://github.com/joaquinignaciomondaca-code/monitor-financiero-chile)"}
PRIMER_TRIMESTRE = "201403"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


# --------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------
def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def dv_m11(body):
    s, mult = 0, 2
    for c in reversed(str(body)):
        s += int(c) * mult
        mult = mult + 1 if mult < 7 else 2
    r = 11 - (s % 11)
    return {11: "0", 10: "K"}.get(r, str(r))


def normalizar(texto):
    """minúsculas, sin acentos, espacios colapsados."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()


def trimestres(desde, hasta):
    y0, m0 = int(desde[:4]), int(desde[4:])
    y1, m1 = int(hasta[:4]), int(hasta[4:])
    out = []
    for y in range(y0, y1 + 1):
        for m in (3, 6, 9, 12):
            if (y, m) < (y0, m0) or (y, m) > (y1, m1):
                continue
            out.append(f"{y}{m:02d}")
    return out


def ultimo_trimestre_publicable(hoy=None):
    """CMF publica ~60-90 días después del cierre; el último trimestre cerrado hace >= 2 meses."""
    hoy = hoy or date.today()
    y, m = hoy.year, hoy.month - 2
    if m <= 0:
        y, m = y - 1, m + 12
    mq = (m // 3) * 3
    if mq == 0:
        y, mq = y - 1, 12
    return f"{y}{mq:02d}"


def guardar(df, path_parquet, con_json=True):
    df.to_parquet(path_parquet, index=False, engine="pyarrow")
    if con_json:
        df.to_json(path_parquet.replace(".parquet", ".json"), orient="records", indent=1, force_ascii=False)
    log(f"  guardado {os.path.relpath(path_parquet, BASE_DIR)} ({len(df)} filas)")


def tc_map():
    """periodo YYYY-MM -> dólar observado de cierre. Sin fallbacks: si falta, queda None."""
    if not os.path.exists(MACRO_PARQUET):
        log("  AVISO: no existe macro_divisas_mercado.parquet; los montos en USD quedarán nulos.")
        return {}
    df = pd.read_parquet(MACRO_PARQUET, columns=["periodo", "usd_clp_cierre"]).dropna()
    return dict(zip(df["periodo"], df["usd_clp_cierre"].astype(float)))


# --------------------------------------------------------------------------------------
# Paso 1: maestro
# --------------------------------------------------------------------------------------
def cargar_catalogo():
    with open(CATALOGO, encoding="utf-8") as fh:
        cat = json.load(fh)
    ents = cat["entidades"]
    for e in ents:
        cuerpo, dv = e["rut"].split("-")
        if dv_m11(cuerpo) != dv.upper():
            raise ValueError(f"RUT inválido en catálogo: {e['rut']} ({e['razon_social']})")
    ruts = [e["rut"] for e in ents]
    if len(ruts) != len(set(ruts)):
        raise ValueError("RUT duplicado en catálogo")
    return cat


def step_maestro():
    log("Paso 1: maestro desde catálogo versionado")
    cat = cargar_catalogo()
    df = pd.DataFrame(cat["entidades"]).sort_values("razon_social").reset_index(drop=True)
    df["catalogo_version"] = cat["_meta"]["version"]
    df["fecha_extraccion"] = datetime.now().strftime("%Y-%m-%d")
    df["script_version"] = SCRIPT_VERSION
    guardar(df, P_MAESTRO)
    return df


# --------------------------------------------------------------------------------------
# Paso 2: descarga -> formato largo
# --------------------------------------------------------------------------------------
def descargar_trimestre(q, inseguro=False, reintentos=3):
    url = CMF_URL.format(q=q)
    ctx = ssl.create_default_context()
    if inseguro:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    ultimo_error = None
    for intento in range(1, reintentos + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=90) as resp:
                raw = resp.read()
            if len(raw) < 100:
                return url, ""
            try:
                return url, raw.decode("utf-8")
            except UnicodeDecodeError:
                return url, raw.decode("latin-1", errors="ignore")
        except Exception as e:  # noqa
            ultimo_error = e
            time.sleep(3 * intento)
    raise RuntimeError(f"{q}: fallo descarga tras {reintentos} intentos: {ultimo_error}")


def parsear_cmf(texto, q, url, objetivo):
    """texto CMF -> lista de dicts (formato largo) sólo para RUT objetivo (cuerpo sin DV)."""
    y, m = q[:4], q[4:6]
    fecha_corte = f"{y}-{m}-{calendar.monthrange(int(y), int(m))[1]:02d}"
    hoy = datetime.now().strftime("%Y-%m-%d")
    filas = []
    for linea in texto.splitlines():
        p = linea.rstrip("\r\n").split(";")
        if len(p) < 7:
            continue
        cuerpo = p[1].strip().split("-")[0].replace(".", "")
        if cuerpo not in objetivo:
            continue
        try:
            valor = float(p[6].strip().replace(",", "."))
        except ValueError:
            continue
        filas.append({
            "periodo": f"{y}-{m}",
            "fecha_corte": fecha_corte,
            "rut": objetivo[cuerpo]["rut"],
            "razon_social": objetivo[cuerpo]["razon_social"],
            "nombre_en_archivo": p[2].strip(),
            "ind_cons": p[3].strip().upper()[:1],
            "moneda": p[4].strip().upper(),
            "cuenta": p[5].strip(),
            "valor": valor,
            "taxonomia": p[7].strip() if len(p) > 7 else None,
            "estado_financiero": p[8].strip() if len(p) > 8 else None,
            "fuente_url": url,
            "metodo": "cmf_ver_archivo",
            "fecha_extraccion": hoy,
            "script_version": SCRIPT_VERSION,
        })
    return filas


def step_descargar(desde=None, hasta=None, solo_faltantes=False, fixture=None, inseguro=False):
    log("Paso 2: descarga CMF -> formato largo (todas las cuentas)")
    cat = cargar_catalogo()
    objetivo = {e["rut"].split("-")[0]: e for e in cat["entidades"] if e.get("fuente_eeff_pipeline") == "cmf_ver_archivo"}
    log(f"  {len(objetivo)} entidades objetivo (fuente_eeff_pipeline = cmf_ver_archivo)")

    existente = pd.read_parquet(P_CUENTAS) if os.path.exists(P_CUENTAS) else pd.DataFrame()
    cobertura_prev = pd.read_parquet(P_COBERTURA) if os.path.exists(P_COBERTURA) else pd.DataFrame()

    if fixture:
        q = re.search(r"(\d{6})", os.path.basename(fixture)).group(1)
        lista = [q]
    else:
        hasta = hasta or ultimo_trimestre_publicable()
        desde = desde or PRIMER_TRIMESTRE
        lista = trimestres(desde, hasta)
        if solo_faltantes and not existente.empty:
            ya = set(existente["periodo"].str.replace("-", "").unique())
            lista = [q for q in lista if q not in ya]
    log(f"  trimestres a procesar: {len(lista)} ({lista[0] if lista else '-'} → {lista[-1] if lista else '-'})")

    nuevas, cobert = [], []
    for q in lista:
        try:
            if fixture:
                url, texto = f"fixture://{os.path.basename(fixture)}", open(fixture, encoding="utf-8").read()
            else:
                url, texto = descargar_trimestre(q, inseguro=inseguro)
        except Exception as e:
            log(f"  [{q}] ERROR {e}")
            for e_ in objetivo.values():
                cobert.append({"periodo": f"{q[:4]}-{q[4:]}", "rut": e_["rut"], "estado": "error_descarga", "detalle": str(e)[:200]})
            continue
        if not texto:
            log(f"  [{q}] sin archivo publicado")
            for e_ in objetivo.values():
                cobert.append({"periodo": f"{q[:4]}-{q[4:]}", "rut": e_["rut"], "estado": "sin_archivo", "detalle": None})
            continue
        filas = parsear_cmf(texto, q, url, objetivo)
        presentes = {f["rut"] for f in filas}
        for e_ in objetivo.values():
            cobert.append({"periodo": f"{q[:4]}-{q[4:]}", "rut": e_["rut"],
                           "estado": "ok" if e_["rut"] in presentes else "sin_entidad", "detalle": None})
        nuevas.extend(filas)
        log(f"  [{q}] {len(filas)} cuentas de {len(presentes)} entidades")
        if not fixture:
            time.sleep(1.0)  # cortesía con el servidor CMF

    df_new = pd.DataFrame(nuevas)
    if not df_new.empty:
        if not existente.empty:
            per = set(df_new["periodo"].unique())
            existente = existente[~existente["periodo"].isin(per)]  # reemplazo por período completo
            df_all = pd.concat([existente, df_new], ignore_index=True)
        else:
            df_all = df_new
        df_all = df_all.sort_values(["periodo", "rut", "ind_cons", "cuenta"]).reset_index(drop=True)
        guardar(df_all, P_CUENTAS, con_json=False)  # largo: sólo parquet (JSON sería enorme)
    else:
        log("  no se obtuvieron cuentas nuevas")

    df_cob = pd.DataFrame(cobert)
    if not df_cob.empty:
        if not cobertura_prev.empty:
            per = set(df_cob["periodo"].unique())
            cobertura_prev = cobertura_prev[~cobertura_prev["periodo"].isin(per)]
            df_cob = pd.concat([cobertura_prev, df_cob], ignore_index=True)
        df_cob["fecha_extraccion"] = datetime.now().strftime("%Y-%m-%d")
        df_cob["script_version"] = SCRIPT_VERSION
        guardar(df_cob.sort_values(["periodo", "rut"]), P_COBERTURA)


# --------------------------------------------------------------------------------------
# Paso 3: resumen desde formato largo con mapeo explícito
# --------------------------------------------------------------------------------------
class Mapeo:
    def __init__(self, path=MAPEO):
        with open(path, encoding="utf-8") as fh:
            self.cfg = json.load(fh)
        self.metricas = {}
        for nombre, m in self.cfg["metricas"].items():
            self.metricas[nombre] = {
                "exactas": {normalizar(x) for x in m.get("exactas", [])},
                "patrones": [re.compile(p) for p in m.get("patrones", [])],
                "excluir": [re.compile(p) for p in m.get("excluir", [])],
            }
        self.componentes_cartera = self.cfg["cartera_credito_componentes"]
        self.relevantes = [re.compile(p) for p in self.cfg["cuentas_relevantes_para_reporte_no_mapeadas"]["patrones"]]

    def clasificar(self, cuenta):
        n = normalizar(cuenta)
        hits = []
        for nombre, m in self.metricas.items():
            if any(p.search(n) for p in m["excluir"]):
                continue
            if n in m["exactas"] or any(p.search(n) for p in m["patrones"]):
                hits.append(nombre)
        return hits

    def es_relevante(self, cuenta):
        n = normalizar(cuenta)
        return any(p.search(n) for p in self.relevantes)


def step_resumen():
    log("Paso 3: resumen de balance desde formato largo")
    if not os.path.exists(P_CUENTAS):
        raise SystemExit("No existe factoring_leasing_eeff_cuentas.parquet: ejecuta --step descargar primero.")
    mp = Mapeo()
    df = pd.read_parquet(P_CUENTAS)
    df = df[df["moneda"] == "CLP"].copy()

    # Preferir Consolidado sobre Individual por (rut, periodo)
    pref = df.groupby(["rut", "periodo"])["ind_cons"].agg(lambda s: "C" if "C" in set(s) else sorted(set(s))[0]).rename("ind_pref")
    df = df.merge(pref, on=["rut", "periodo"])
    df = df[df["ind_cons"] == df["ind_pref"]].drop(columns="ind_pref")

    # Clasificación de cuentas (cacheada por nombre)
    nombres = df["cuenta"].unique()
    clas = {c: mp.clasificar(c) for c in nombres}
    df["metricas"] = df["cuenta"].map(clas)

    # Suma por métrica: una cuenta puede aparecer repetida (subtotales) -> tomar el máximo abs por nombre, luego sumar nombres
    filas, no_map = [], {}
    tcs = tc_map()
    for (rut, periodo), g in df.groupby(["rut", "periodo"]):
        por_cuenta = g.groupby("cuenta")["valor"].agg(lambda s: s.iloc[0])
        vals = {}
        for cuenta, v in por_cuenta.items():
            for m in clas[cuenta]:
                vals.setdefault(m, 0.0)
                vals[m] += v
        tot_act = vals.get("total_activos", 0.0)
        if tot_act <= 0:
            continue
        pc, pnc = vals.get("pasivos_corrientes", 0.0), vals.get("pasivos_no_corrientes", 0.0)
        tot_pas = vals.get("total_pasivos") or (pc + pnc)
        pat, pat_origen = vals.get("patrimonio_neto"), "cmf"
        if not pat:
            pat, pat_origen = tot_act - tot_pas, "derivado_A_menos_P"
        cartera = sum(vals.get(c, 0.0) for c in mp.componentes_cartera)
        liq = vals.get("activos_liquidos", 0.0)
        tc = tcs.get(periodo)
        usd = (lambda x: round(x / 1e6 / tc, 2) if tc else None)
        mm = (lambda x: round(x / 1e6, 2))
        filas.append({
            "id_balance": f"{rut}_{periodo.replace('-', '')}",
            "periodo": periodo,
            "fecha_corte": g["fecha_corte"].iloc[0],
            "rut": rut,
            "nombre_empresa": g["razon_social"].iloc[0],
            "ind_cons": g["ind_cons"].iloc[0],
            "total_activos_m_clp": mm(tot_act),
            "total_activos_m_usd": usd(tot_act),
            "pasivos_corrientes_m_clp": mm(pc),
            "pasivos_no_corrientes_m_clp": mm(pnc),
            "total_pasivos_m_clp": mm(tot_pas),
            "total_pasivos_m_usd": usd(tot_pas),
            "patrimonio_neto_m_clp": mm(pat),
            "patrimonio_m_usd": usd(pat),
            "patrimonio_origen": pat_origen,
            "cartera_credito_m_clp": mm(cartera),
            "cartera_credito_m_usd": usd(cartera),
            "cartera_deudores_comerciales_m_clp": mm(vals.get("cartera_deudores_comerciales", 0.0)),
            "cartera_arrendamiento_financiero_m_clp": mm(vals.get("cartera_arrendamiento_financiero", 0.0)),
            "cartera_colocaciones_m_clp": mm(vals.get("cartera_colocaciones", 0.0)),
            "otros_activos_financieros_m_clp": mm(vals.get("otros_activos_financieros", 0.0)),
            "activos_liquidos_m_clp": mm(liq),
            "activos_liquidos_m_usd": usd(liq),
            "ingresos_actividades_ordinarias_m_clp": mm(vals.get("ingresos_actividades_ordinarias", 0.0)),
            "ganancia_perdida_m_clp": mm(vals.get("ganancia_perdida", 0.0)),
            "tc_usd_clp": tc,
            "tc_fuente": "bcch_dolar_observado_cierre(macro_divisas_mercado)" if tc else "faltante",
            "cuadre_ok": abs(tot_act - tot_pas - pat) <= 0.005 * tot_act,
            "cartera_definicion": mp.cfg["_meta"]["version"],
            "fuente_url": g["fuente_url"].iloc[0],
            "metodo": "cmf_ver_archivo",
            "fecha_extraccion": g["fecha_extraccion"].iloc[0],
            "script_version": SCRIPT_VERSION,
        })
        # Cuentas relevantes no mapeadas (> 5 % activos)
        for cuenta, v in por_cuenta.items():
            if not clas[cuenta] and mp.es_relevante(cuenta) and abs(v) > 0.05 * tot_act:
                k = cuenta
                no_map.setdefault(k, {"cuenta": cuenta, "apariciones": 0, "max_pct_activos": 0.0, "ejemplo": None})
                no_map[k]["apariciones"] += 1
                pct = round(abs(v) / tot_act * 100, 1)
                if pct > no_map[k]["max_pct_activos"]:
                    no_map[k]["max_pct_activos"] = pct
                    no_map[k]["ejemplo"] = f"{g['razon_social'].iloc[0]} {periodo}"

    res = pd.DataFrame(filas).sort_values(["periodo", "nombre_empresa"]).reset_index(drop=True)
    guardar(res, P_RESUMEN)

    with open(NO_MAPEADAS, "w", encoding="utf-8") as fh:
        json.dump({"_meta": {"generado": datetime.now().strftime("%Y-%m-%d"),
                             "instruccion": "Cuentas con patrón de cartera/crédito y monto > 5 % de activos que NO calzan con mapeo_cuentas.json. Revisar y agregar a 'exactas' o 'patrones'."},
                   "cuentas": sorted(no_map.values(), key=lambda x: -x["max_pct_activos"])}, fh, ensure_ascii=False, indent=1)
    log(f"  cuentas relevantes no mapeadas: {len(no_map)} -> {os.path.relpath(NO_MAPEADAS, BASE_DIR)}")

    # Resumen de calidad en consola
    bajo = res[res["periodo"] == res["periodo"].max()]
    bajo = bajo[bajo["cartera_credito_m_clp"] / bajo["total_activos_m_clp"] < 0.5]
    if len(bajo):
        log(f"  AVISO: {len(bajo)} entidades con cartera/activos < 0,5 en {res['periodo'].max()} → revisar cuentas_no_mapeadas.json")
    log(f"  patrimonio derivado (A-P) en {(res['patrimonio_origen'] != 'cmf').sum()} de {len(res)} filas; TC faltante en {(res['tc_fuente'] == 'faltante').sum()}")


# --------------------------------------------------------------------------------------
# Migración única: añadir trazabilidad al resumen v1 (mientras no se regenere desde CMF)
# --------------------------------------------------------------------------------------
def step_migrar_legacy():
    log("Migración: añadir columnas de trazabilidad al balance_resumen v1 existente")
    df = pd.read_parquet(P_RESUMEN)
    if "script_version" in df.columns:
        log("  ya migrado; nada que hacer")
        return
    tcs = tc_map()
    df["patrimonio_origen"] = "desconocido_v1"
    df["tc_usd_clp"] = df["periodo"].map(tcs)
    df["tc_fuente"] = df["tc_usd_clp"].apply(lambda x: "bcch_dolar_observado_cierre(macro_divisas_mercado)" if pd.notna(x) else "faltante")
    df["cuadre_ok"] = (df["total_activos_m_clp"] - df["total_pasivos_m_clp"] - df["patrimonio_neto_m_clp"]).abs() <= 0.005 * df["total_activos_m_clp"]
    df["cartera_definicion"] = "v1_solo_deudores_comerciales (subestima leasing/automotriz; regenerar con --step descargar + resumen)"
    df["fuente_url"] = df["periodo"].apply(lambda p: CMF_URL.format(q=p.replace("-", "")))
    df["metodo"] = "cmf_ver_archivo"
    df["fecha_extraccion"] = "2026-09-23"
    df["script_version"] = "1.x-legacy(stream_cmf_eeff_series)"
    guardar(df, P_RESUMEN)


# --------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", choices=["maestro", "descargar", "resumen", "todo", "migrar-legacy"], default="todo")
    ap.add_argument("--desde", help="YYYYMM (default 201403)")
    ap.add_argument("--hasta", help="YYYYMM (default: último trimestre publicable)")
    ap.add_argument("--solo-faltantes", action="store_true", help="descargar sólo trimestres que no estén en el formato largo")
    ap.add_argument("--fixture", help="archivo local con formato CMF para pruebas offline (nombre debe incluir YYYYMM)")
    ap.add_argument("--inseguro", action="store_true", help="desactiva verificación TLS (sólo si CMF tiene cadena rota; queda registrado en log)")
    a = ap.parse_args()

    log(f"Pipeline Factoring & Leasing v{SCRIPT_VERSION} — step={a.step}")
    if a.inseguro:
        log("  AVISO: verificación TLS desactivada por --inseguro")
    if a.step in ("maestro", "todo"):
        step_maestro()
    if a.step in ("descargar", "todo"):
        step_descargar(a.desde, a.hasta, a.solo_faltantes or a.step == "todo", a.fixture, a.inseguro)
    if a.step in ("resumen", "todo"):
        step_resumen()
    if a.step == "migrar-legacy":
        step_migrar_legacy()
    log("fin")


if __name__ == "__main__":
    main()

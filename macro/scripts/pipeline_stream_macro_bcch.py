"""
Pipeline de Macroeconomía y Tasas de Interés - Banco Central de Chile (BCCh SIETE).
Descarga streaming concurrente y consolidación de 23 series canónicas (2020 a 2026):
1. macro_tasas_rendimientos: TPM, TIB/ICP, Curva BCP (2y, 5y, 10y), Curva BCU (5y, 10y, 20y), SPC (CLP 2y, UF 1y), Slopes y Breakeven Inflation.
2. macro_divisas_mercado: USD/CLP (promedio, cierre, min, max, volatilidad), EUR/CLP (promedio, cierre), TCR Multilateral, TCR-5 y variaciones.
3. macro_precios_actividad: UF (cierre, promedio), IPC (índice, mensual, anual), IMACEC (total, no minero), Cobre BML (USD/lb), Expectativas EEE (11m, 23m).
"""

import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

try:
    import bcchapi
except ImportError:
    raise ImportError("La librería 'bcchapi' es obligatoria. Instalar con 'pip install bcchapi'.")

import sys as _sys
_sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from mfc_common.credentials import bcch_credentials

# Credenciales desde variables de entorno / .env (ver mfc_common/credentials.py). Se resuelven al usarlas.
def _bcch_session():
    email, password = bcch_credentials()
    return bcchapi.Siete(email, password)

FETCH_START_DATE = "2013-01-01"
SERIES_START_PERIOD = "2014-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

SERIES_CATALOG = {
    # Tasas
    "tpm_m": {"sid": "F022.TPM.TIN.D001.NO.Z.M", "freq": "M", "desc": "TPM Mensual"},
    "tib_m": {"sid": "F022.TIB.TIP.D001.NO.Z.M", "freq": "M", "desc": "Tasa Interbancaria ICP Promedio"},
    "bcp_2y_d": {"sid": "F022.BCLP.TIS.AN02.NO.Z.D", "freq": "D", "desc": "Bonos Central Pesos 2Y"},
    "bcp_5y_d": {"sid": "F022.BCLP.TIS.AN05.NO.Z.D", "freq": "D", "desc": "Bonos Central Pesos 5Y"},
    "bcp_10y_d": {"sid": "F022.BCLP.TIS.AN10.NO.Z.D", "freq": "D", "desc": "Bonos Central Pesos 10Y"},
    "bcu_5y_d": {"sid": "F022.BUF.TIS.AN05.UF.Z.D", "freq": "D", "desc": "Bonos Central UF 5Y"},
    "bcu_10y_d": {"sid": "F022.BUF.TIS.AN10.UF.Z.D", "freq": "D", "desc": "Bonos Central UF 10Y"},
    "bcu_20y_d": {"sid": "F022.BUF.TIS.AN20.UF.Z.D", "freq": "D", "desc": "Bonos Central UF 20Y"},
    "spc_clp_2y_d": {"sid": "F022.SPC.TIN.AN02.NO.Z.D", "freq": "D", "desc": "Swap Promedio Camara CLP 2Y"},
    "spc_uf_1y_d": {"sid": "F022.SPC.TIN.AN01.UF.Z.D", "freq": "D", "desc": "Swap Promedio Camara UF 1Y"},
    # Divisas
    "usd_clp_d": {"sid": "F073.TCO.PRE.Z.D", "freq": "D", "desc": "Dólar Observado Diario"},
    "eur_clp_d": {"sid": "F072.CLP.EUR.N.O.D", "freq": "D", "desc": "Euro Observado Diario"},
    "tcr_m": {"sid": "F073.TCR.IND.199101.M", "freq": "M", "desc": "TCR General 1986=100"},
    "tcr_5_m": {"sid": "F073.TR5.IND.198601.M", "freq": "M", "desc": "TCR 5 Monedas 1986=100"},
    # Precios / Actividad
    "uf_d": {"sid": "F073.UFF.PRE.Z.D", "freq": "D", "desc": "Unidad de Fomento Diaria"},
    "ipc_idx_m": {"sid": "G073.IPC.IND.2023.M", "freq": "M", "desc": "IPC General Base 2023=100"},
    "ipc_var_m": {"sid": "G073.IPC.VAR.2023.M", "freq": "M", "desc": "IPC Variación Mensual %"},
    "ipc_v12_m": {"sid": "G073.IPC.V12.2023.M", "freq": "M", "desc": "IPC Variación Interanual %"},
    "imacec_m": {"sid": "F032.ICF.IND.Z.Z.EP18.Z.Z.0.M", "freq": "M", "desc": "IMACEC Total Empalmado"},
    "imacec_nm_m": {"sid": "F032.IMC.IND.Z.Z.EP18.N03.Z.0.M", "freq": "M", "desc": "IMACEC No Minero Empalmado"},
    "cobre_m": {"sid": "F019.PPB.PRE.40.M", "freq": "M", "desc": "Cobre Refinado BML USD/lb"},
    "eee_11m": {"sid": "F089.IPC.V12.14.M", "freq": "M", "desc": "Expectativa IPC EEE 11M %"},
    "eee_23m": {"sid": "F089.IPC.V12.15.M", "freq": "M", "desc": "Expectativa IPC EEE 23M %"}
}

def fetch_single_series(item):
    """Descarga una serie creando su propia instancia de bcchapi (Thread-safe)."""
    key, meta = item
    sid = meta["sid"]
    for attempt in range(1, 4):
        try:
            siete = _bcch_session()
            df = siete.cuadro(series=[sid], desde=FETCH_START_DATE, hasta=END_DATE)
            if df is not None and not df.empty:
                df.columns = ["valor"]
                df.index = pd.to_datetime(df.index)
                df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
                df = df.dropna()
                return key, df
            else:
                return key, pd.DataFrame()
        except Exception as e:
            if attempt == 3:
                print(f"Error persistente en {key} ({sid}): {e}")
                return key, pd.DataFrame()
            time.sleep(1.0)
    return key, pd.DataFrame()

def run_macro_pipeline():
    print("=" * 70)
    print("Iniciando Pipeline de Macroeconomía y Tasas (BCCh SIETE)")
    print(f"Rango temporal: {FETCH_START_DATE} a {END_DATE} (Series finales desde {SERIES_START_PERIOD})")
    print(f"Descargando {len(SERIES_CATALOG)} series con 8 workers concurrentes...")
    print("=" * 70)

    t0 = time.time()
    raw_series = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(fetch_single_series, SERIES_CATALOG.items())
        for key, df in results:
            raw_series[key] = df
            print(f"  OK: {key:15s} [{SERIES_CATALOG[key]['sid']}] -> {len(df):4d} observaciones")

    elapsed = time.time() - t0
    print(f"Descarga completada en {elapsed:.2f} segundos.")
    print("-" * 70)

    # Creamos un índice maestro de periodos mensuales (YYYY-MM)
    all_months = pd.date_range(start=FETCH_START_DATE, end=END_DATE, freq="MS").strftime("%Y-%m").tolist()
    # Limitar hasta el mes actual
    curr_month = datetime.today().strftime("%Y-%m")
    periods = [p for p in all_months if p <= curr_month]

    # =========================================================================
    # TABLA 1: macro_tasas_rendimientos
    # =========================================================================
    print("Construyendo tabla: macro_tasas_rendimientos...")
    t_rows = []
    for p in periods:
        p_dt = pd.to_datetime(p)
        # Helper para series mensuales directas
        def get_m_val(df_key):
            df = raw_series.get(df_key)
            if df is not None and not df.empty:
                sub = df[df.index.strftime("%Y-%m") == p]
                if not sub.empty:
                    return round(float(sub.iloc[0]["valor"]), 4)
            return None

        # Helper para series diarias: promedio y cierre
        def get_d_stats(df_key):
            df = raw_series.get(df_key)
            if df is not None and not df.empty:
                sub = df[df.index.strftime("%Y-%m") == p]
                if not sub.empty:
                    mean_val = round(float(sub["valor"].mean()), 4)
                    close_val = round(float(sub.iloc[-1]["valor"]), 4)
                    return mean_val, close_val
            return None, None

        tpm = get_m_val("tpm_m")
        tib = get_m_val("tib_m")
        bcp_2y, bcp_2y_c = get_d_stats("bcp_2y_d")
        bcp_5y, bcp_5y_c = get_d_stats("bcp_5y_d")
        bcp_10y, bcp_10y_c = get_d_stats("bcp_10y_d")
        bcu_5y, bcu_5y_c = get_d_stats("bcu_5y_d")
        bcu_10y, bcu_10y_c = get_d_stats("bcu_10y_d")
        bcu_20y, bcu_20y_c = get_d_stats("bcu_20y_d")
        spc_clp_2y, _ = get_d_stats("spc_clp_2y_d")
        spc_uf_1y, _ = get_d_stats("spc_uf_1y_d")

        # Métricas analíticas derivadas
        spread_10y_2y = round((bcp_10y - bcp_2y) * 100.0, 1) if (bcp_10y is not None and bcp_2y is not None) else None
        spread_5y_2y = round((bcp_5y - bcp_2y) * 100.0, 1) if (bcp_5y is not None and bcp_2y is not None) else None
        breakeven_5y = round(bcp_5y - bcu_5y, 4) if (bcp_5y is not None and bcu_5y is not None) else None
        breakeven_10y = round(bcp_10y - bcu_10y, 4) if (bcp_10y is not None and bcu_10y is not None) else None

        t_rows.append({
            "periodo": p,
            "tpm": tpm,
            "tib_promedio": tib,
            "bcp_2y": bcp_2y,
            "bcp_5y": bcp_5y,
            "bcp_10y": bcp_10y,
            "bcu_5y": bcu_5y,
            "bcu_10y": bcu_10y,
            "bcu_20y": bcu_20y,
            "spc_clp_2y": spc_clp_2y,
            "spc_uf_1y": spc_uf_1y,
            "spread_bcp_10y_2y_bps": spread_10y_2y,
            "spread_bcp_5y_2y_bps": spread_5y_2y,
            "inflacion_implicita_5y_breakeven": breakeven_5y,
            "inflacion_implicita_10y_breakeven": breakeven_10y
        })

    df_tasas = pd.DataFrame(t_rows).sort_values("periodo").reset_index(drop=True)
    df_tasas = df_tasas[df_tasas["periodo"] >= SERIES_START_PERIOD].reset_index(drop=True)

    # =========================================================================
    # TABLA 2: macro_divisas_mercado
    # =========================================================================
    print("Construyendo tabla: macro_divisas_mercado...")
    d_rows = []
    for p in periods:
        def get_m_val(df_key):
            df = raw_series.get(df_key)
            if df is not None and not df.empty:
                sub = df[df.index.strftime("%Y-%m") == p]
                if not sub.empty:
                    return round(float(sub.iloc[0]["valor"]), 4)
            return None

        # Stats USD
        df_usd = raw_series.get("usd_clp_d")
        usd_prom, usd_cierre, usd_min, usd_max, usd_vol = None, None, None, None, None
        if df_usd is not None and not df_usd.empty:
            sub = df_usd[df_usd.index.strftime("%Y-%m") == p]
            if not sub.empty:
                usd_prom = round(float(sub["valor"].mean()), 2)
                usd_cierre = round(float(sub.iloc[-1]["valor"]), 2)
                usd_min = round(float(sub["valor"].min()), 2)
                usd_max = round(float(sub["valor"].max()), 2)
                # Volatilidad mensual anualizada: std(retornos diarios) * sqrt(252)
                if len(sub) > 2:
                    rets = sub["valor"].pct_change().dropna()
                    usd_vol = round(float(rets.std() * np.sqrt(252) * 100.0), 2)

        # Stats EUR
        df_eur = raw_series.get("eur_clp_d")
        eur_prom, eur_cierre = None, None
        if df_eur is not None and not df_eur.empty:
            sub = df_eur[df_eur.index.strftime("%Y-%m") == p]
            if not sub.empty:
                eur_prom = round(float(sub["valor"].mean()), 2)
                eur_cierre = round(float(sub.iloc[-1]["valor"]), 2)

        tcr = get_m_val("tcr_m")
        tcr_5 = get_m_val("tcr_5_m")

        d_rows.append({
            "periodo": p,
            "usd_clp_promedio": usd_prom,
            "usd_clp_cierre": usd_cierre,
            "usd_clp_min": usd_min,
            "usd_clp_max": usd_max,
            "usd_clp_volatilidad_anualizada_pct": usd_vol,
            "eur_clp_promedio": eur_prom,
            "eur_clp_cierre": eur_cierre,
            "tcr_general": tcr,
            "tcr_5monedas": tcr_5
        })

    df_divisas = pd.DataFrame(d_rows).sort_values("periodo").reset_index(drop=True)
    # Calcular variaciones porcentuales mensuales e interanuales
    df_divisas["var_mensual_usd_pct"] = round(df_divisas["usd_clp_cierre"].pct_change() * 100.0, 2)
    df_divisas["var_anual_usd_pct"] = round(df_divisas["usd_clp_cierre"].pct_change(12) * 100.0, 2)
    df_divisas["var_mensual_eur_pct"] = round(df_divisas["eur_clp_cierre"].pct_change() * 100.0, 2)

    # Filtrar desde el periodo de referencia maestro
    df_divisas = df_divisas[df_divisas["periodo"] >= SERIES_START_PERIOD].reset_index(drop=True)

    # Reordenar columnas limpias
    divisas_cols = [
        "periodo", "usd_clp_promedio", "usd_clp_cierre", "usd_clp_min", "usd_clp_max",
        "var_mensual_usd_pct", "var_anual_usd_pct", "usd_clp_volatilidad_anualizada_pct",
        "eur_clp_promedio", "eur_clp_cierre", "var_mensual_eur_pct",
        "tcr_general", "tcr_5monedas"
    ]
    df_divisas = df_divisas[divisas_cols]

    # =========================================================================
    # TABLA 3: macro_precios_actividad
    # =========================================================================
    print("Construyendo tabla: macro_precios_actividad...")
    p_rows = []
    for p in periods:
        def get_m_val(df_key):
            df = raw_series.get(df_key)
            if df is not None and not df.empty:
                sub = df[df.index.strftime("%Y-%m") == p]
                if not sub.empty:
                    return round(float(sub.iloc[0]["valor"]), 4)
            return None

        # Stats UF
        df_uf = raw_series.get("uf_d")
        uf_prom, uf_cierre = None, None
        if df_uf is not None and not df_uf.empty:
            sub = df_uf[df_uf.index.strftime("%Y-%m") == p]
            if not sub.empty:
                uf_prom = round(float(sub["valor"].mean()), 2)
                uf_cierre = round(float(sub.iloc[-1]["valor"]), 2)

        ipc_idx = get_m_val("ipc_idx_m")
        ipc_var = get_m_val("ipc_var_m")
        ipc_v12 = get_m_val("ipc_v12_m")
        imacec = get_m_val("imacec_m")
        imacec_nm = get_m_val("imacec_nm_m")
        cobre = get_m_val("cobre_m")
        eee_11m = get_m_val("eee_11m")
        eee_23m = get_m_val("eee_23m")

        p_rows.append({
            "periodo": p,
            "uf_cierre": uf_cierre,
            "uf_promedio": uf_prom,
            "ipc_indice": ipc_idx,
            "ipc_var_mensual": ipc_var,
            "ipc_var_anual": ipc_v12,
            "imacec_empalmado": imacec,
            "imacec_no_minero": imacec_nm,
            "cobre_spot_usd_lb": cobre,
            "eee_ipc_11m": eee_11m,
            "eee_ipc_23m": eee_23m
        })

    df_precios = pd.DataFrame(p_rows).sort_values("periodo").reset_index(drop=True)
    # Variaciones de UF e IMACEC
    df_precios["uf_var_mensual_pct"] = round(df_precios["uf_cierre"].pct_change() * 100.0, 2)
    df_precios["imacec_var_anual_pct"] = round(df_precios["imacec_empalmado"].pct_change(12) * 100.0, 2)
    df_precios["cobre_var_anual_pct"] = round(df_precios["cobre_spot_usd_lb"].pct_change(12) * 100.0, 2)
    df_precios["desvio_eee_11m_meta_bps"] = round((df_precios["eee_ipc_11m"] - 3.0) * 100.0, 1)

    # Filtrar desde el periodo de referencia maestro
    df_precios = df_precios[df_precios["periodo"] >= SERIES_START_PERIOD].reset_index(drop=True)

    precios_cols = [
        "periodo", "uf_cierre", "uf_promedio", "uf_var_mensual_pct",
        "ipc_indice", "ipc_var_mensual", "ipc_var_anual",
        "imacec_empalmado", "imacec_no_minero", "imacec_var_anual_pct",
        "cobre_spot_usd_lb", "cobre_var_anual_pct",
        "eee_ipc_11m", "eee_ipc_23m", "desvio_eee_11m_meta_bps"
    ]
    df_precios = df_precios[precios_cols]

    # =========================================================================
    # EXPORTACIÓN PARQUET Y JSON
    # =========================================================================
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "outputs", "macro"))
    os.makedirs(out_dir, exist_ok=True)

    tables = {
        "macro_tasas_rendimientos": df_tasas,
        "macro_divisas_mercado": df_divisas,
        "macro_precios_actividad": df_precios
    }

    print("-" * 70)
    for name, df in tables.items():
        pq_path = os.path.join(out_dir, f"{name}.parquet")
        js_path = os.path.join(out_dir, f"{name}.json")

        df.to_parquet(pq_path, index=False, engine="pyarrow")
        df.to_json(js_path, orient="records", date_format="iso", indent=2)

        pq_size = os.path.getsize(pq_path) / 1024.0
        js_size = os.path.getsize(js_path) / 1024.0
        print(f"Exportado: {name:28s} | {len(df):3d} filas x {len(df.columns):2d} cols | Parquet: {pq_size:6.1f} KB | JSON: {js_size:6.1f} KB")

    print("=" * 70)
    print("Pipeline de Macroeconomía finalizado con éxito.")
    print("=" * 70)

if __name__ == "__main__":
    run_macro_pipeline()

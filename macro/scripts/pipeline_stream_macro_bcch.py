"""
Pipeline de Macroeconomía y Tasas de Interés - Banco Central de Chile (BCCh SIETE).
Descarga streaming concurrente y consolidación de 23 series canónicas (2020 a 2026):
1. macro_tasas_rendimientos: TPM, TIB/ICP, Curva BCP (2y, 5y, 10y), Curva BCU (5y, 10y, 20y), SPC (CLP 2y, UF 1y), Slopes y Breakeven Inflation.
2. macro_divisas_mercado: USD/CLP (promedio, cierre, min, max, volatilidad), EUR/CLP (promedio, cierre), TCR Multilateral, TCR-5 y variaciones.
3. macro_precios_actividad: UF (cierre, promedio), IPC (índice, mensual, anual), IMACEC (total, no minero), Cobre BML (USD/lb), Expectativas EEE (11m, 23m).
"""

import os
import shutil
import time
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import date
from concurrent.futures import ThreadPoolExecutor

try:
    import bcchapi
except ImportError:
    raise ImportError("La librería 'bcchapi' es obligatoria. Instalar con 'pip install bcchapi'.")

EMAIL_BCCH = os.environ.get("BCCH_EMAIL", "")
PASS_BCCH = os.environ.get("BCCH_PASSWORD", "")

FETCH_START_DATE = "2013-01-01"
SERIES_START_PERIOD = "2014-01"
ROOT = Path(__file__).resolve().parents[2]
TABLES = ("macro_tasas_rendimientos", "macro_divisas_mercado", "macro_precios_actividad")

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

def fetch_single_series(item, start_date, end_date):
    """Descarga una serie creando su propia instancia de bcchapi (Thread-safe)."""
    key, meta = item
    sid = meta["sid"]
    for attempt in range(1, 4):
        try:
            siete = bcchapi.Siete(EMAIL_BCCH, PASS_BCCH)
            df = siete.cuadro(series=[sid], desde=start_date, hasta=end_date)
            if df is not None and not df.empty:
                df.columns = ["valor"]
                df.index = pd.to_datetime(df.index)
                df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
                df = df.dropna()
                return key, df
            else:
                return key, pd.DataFrame()
        except Exception:
            if attempt == 3:
                # La excepción de la API podría incluir parámetros sensibles.
                print(f"Error persistente en {key} ({sid}); se omiten detalles de autenticación.")
                raise RuntimeError(f"Falló la consulta de {key} ({sid}); no se publicará nada") from None
            time.sleep(1.0)
    raise RuntimeError(f"Falló la consulta de {key} ({sid})")

def load_baseline(directory):
    """La última extracción validada es el punto de partida; sin ella, backfill completo."""
    directory = Path(directory)
    if not directory.exists():
        return {}
    existing = [directory / f"{name}.parquet" for name in TABLES]
    if not any(path.exists() for path in existing):
        return {}
    if not all(path.exists() for path in existing):
        raise ValueError("Baseline macro incompleto; faltan tablas Parquet")
    tables = {name: pd.read_parquet(directory / f"{name}.parquet") for name in TABLES}
    periods = [table["periodo"].tolist() for table in tables.values()]
    if not periods[0] or any(p != periods[0] for p in periods[1:]):
        raise ValueError("Baseline macro con períodos inconsistentes")
    if periods[0] != sorted(set(periods[0])) or periods[0][-1] > date.today().strftime("%Y-%m"):
        raise ValueError("Baseline macro con períodos duplicados, desordenados o futuros")
    return tables


def merge_incremental(fresh, baseline, start_period):
    """Valores nuevos no nulos prevalecen; se preservan historia y métricas antiguas."""
    if not baseline:
        return fresh
    merged = {}
    for name in TABLES:
        old = baseline[name].set_index("periodo")
        new = fresh[name].set_index("periodo")
        if list(old.columns) != list(new.columns):
            raise ValueError(f"Cambio de esquema de {name}; requiere revisión manual")
        result = new.combine_first(old).sort_index().reset_index()
        merged[name] = result[baseline[name].columns]

    # Recalcular retornos usando el histórico completo (12 meses previos),
    # sin cambiar los meses anteriores al rango consultado.
    changes = {
        "macro_divisas_mercado": [
            ("var_mensual_usd_pct", "usd_clp_cierre", 1),
            ("var_anual_usd_pct", "usd_clp_cierre", 12),
            ("var_mensual_eur_pct", "eur_clp_cierre", 1),
        ],
        "macro_precios_actividad": [
            ("uf_var_mensual_pct", "uf_cierre", 1),
            ("imacec_var_anual_pct", "imacec_empalmado", 12),
            ("cobre_var_anual_pct", "cobre_spot_usd_lb", 12),
        ],
    }
    for name, metrics in changes.items():
        frame = merged[name]
        mask = frame["periodo"] >= start_period
        old_sources = baseline[name].set_index("periodo")
        for target, source, lag in metrics:
            values = pd.to_numeric(frame[source], errors="coerce")
            calculated = (values.pct_change(lag, fill_method=None) * 100).round(2)
            before = frame["periodo"].map(old_sources[source])
            same = frame[source].eq(before) | (frame[source].isna() & before.isna())
            changed_source = mask & (~same | ~frame["periodo"].isin(old_sources.index))
            frame.loc[changed_source, target] = calculated.loc[changed_source].combine_first(frame.loc[changed_source, target])
    return merged


def run_macro_pipeline(output_dir=None, baseline_dir=None):
    """Consulta desde el primer día del último mes disponible, nunca todo el histórico."""
    if not EMAIL_BCCH or not PASS_BCCH:
        raise RuntimeError("Faltan BCCH_EMAIL y BCCH_PASSWORD en el entorno; no se ejecutó la descarga.")
    published = ROOT / "docs" / "outputs" / "macro"
    baseline = load_baseline(baseline_dir or published)
    # En un primer arranque sin Parquets previos se hace un backfill completo.
    # Consultar el mes inclusivo permite completar datos diarios y publicaciones
    # mensuales con retraso; el histórico anterior se lee solo del baseline.
    start_date = f"{next(iter(baseline.values()))['periodo'].iloc[-1]}-01" if baseline else FETCH_START_DATE
    end_date = date.today().isoformat()
    if start_date > end_date:
        raise ValueError("Baseline macro posterior a la fecha actual")
    print("=" * 70)
    print(f"BCCh SIETE: consultando {len(SERIES_CATALOG)} series desde {start_date} hasta {end_date}")
    print("=" * 70)
    t0 = time.time()
    raw_series = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(lambda item: fetch_single_series(item, start_date, end_date), SERIES_CATALOG.items())
        for key, df in results:
            raw_series[key] = df
            print(f"  {key:15s}: {len(df):4d} observaciones")
    print(f"Descarga completada en {time.time() - t0:.2f} segundos.")
    # Si faltan las dos fuentes diarias básicas, lo más probable es un fallo
    # de API/autenticación. Una serie mensual puede estar vacía legítimamente.
    if all(frame.empty for frame in raw_series.values()):
        raise RuntimeError("BCCh no entregó ninguna serie; revisar autenticación/API; no se escribieron salidas")
    if not baseline and any(frame.empty for frame in raw_series.values()):
        raise RuntimeError("Backfill incompleto: algunas series llegaron vacías; no se escribieron salidas")
    # Una respuesta vacía NO borra el histórico. Los fallos de red/autenticación
    # abortan arriba; series sin nuevas observaciones son normales (IPC/IMACEC).
    periods = pd.date_range(start=start_date, end=end_date, freq="MS").strftime("%Y-%m").tolist()
    if not periods:
        periods = [start_date[:7]]

    # =========================================================================
    # TABLA 1: macro_tasas_rendimientos
    # =========================================================================
    print("Construyendo tabla: macro_tasas_rendimientos...")
    t_rows = []
    for p in periods:
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
    df_divisas["var_mensual_usd_pct"] = round(df_divisas["usd_clp_cierre"].pct_change(fill_method=None) * 100.0, 2)
    df_divisas["var_anual_usd_pct"] = round(df_divisas["usd_clp_cierre"].pct_change(12, fill_method=None) * 100.0, 2)
    df_divisas["var_mensual_eur_pct"] = round(df_divisas["eur_clp_cierre"].pct_change(fill_method=None) * 100.0, 2)

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
    df_precios["uf_var_mensual_pct"] = round(df_precios["uf_cierre"].pct_change(fill_method=None) * 100.0, 2)
    df_precios["imacec_var_anual_pct"] = round(df_precios["imacec_empalmado"].pct_change(12, fill_method=None) * 100.0, 2)
    df_precios["cobre_var_anual_pct"] = round(df_precios["cobre_spot_usd_lb"].pct_change(12, fill_method=None) * 100.0, 2)
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

    # No abrir períodos posteriores si alguna tabla carece de su indicador base.
    # Las series mensuales con rezago permanecen NULL hasta que las publique BCCh;
    # nunca se sustituyen valores válidos anteriores por respuestas vacías.
    fresh = {"macro_tasas_rendimientos": df_tasas,
             "macro_divisas_mercado": df_divisas,
             "macro_precios_actividad": df_precios}
    last = next(iter(baseline.values()))["periodo"].iloc[-1] if baseline else None
    core = {"macro_divisas_mercado": "usd_clp_cierre", "macro_precios_actividad": "uf_cierre"}
    accepted = last
    for period in [p for p in periods if last is None or p > last]:
        if any(fresh[name].loc[fresh[name]["periodo"] == period, column].isna().all()
               for name, column in core.items()):
            print(f"Periodo {period} pendiente de datos esenciales; se reintentará mañana.")
            break
        accepted = period
    if accepted is None:
        raise RuntimeError("BCCh no entregó un primer período completo; no se escribieron salidas")
    fresh = {name: table[table["periodo"] <= accepted].copy() for name, table in fresh.items()}
    tables = merge_incremental(fresh, baseline, start_date[:7])

    out_dir = Path(output_dir or ROOT / ".local-data" / "macro").resolve()
    source = Path(baseline_dir or published).resolve()
    if out_dir == source:
        raise ValueError("Staging y baseline deben estar en directorios distintos")
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        pq_path, js_path = out_dir / f"{name}.parquet", out_dir / f"{name}.json"
        if baseline and df.equals(baseline[name]) and (source / js_path.name).exists():
            if pq_path != source / pq_path.name:
                shutil.copyfile(source / pq_path.name, pq_path)
            if js_path != source / js_path.name:
                shutil.copyfile(source / js_path.name, js_path)
            print(f"Sin cambios: {name}")
            continue
        df.to_parquet(pq_path, index=False, engine="pyarrow")
        df.to_json(js_path, orient="records", date_format="iso", indent=2)
        print(f"Actualizado: {name}: {len(df)} períodos hasta {df['periodo'].iloc[-1]}")
    print("Pipeline macro incremental finalizado; salidas en staging.")

if __name__ == "__main__":
    run_macro_pipeline()

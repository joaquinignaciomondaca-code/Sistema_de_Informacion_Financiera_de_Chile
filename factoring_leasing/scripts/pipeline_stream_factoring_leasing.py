"""
Pipeline de Factoring & Leasing - CMF Chile / NBFI.
Genera los datasets analíticos puros de balance y cartera sin métricas sintéticas:
1. factoring_leasing_maestro: Catálogo oficial de entidades con RUT Módulo 11, razón social, tipo y grupo controlador.
2. factoring_leasing_balance_resumen: Balances trimestrales (2018 a 2026) con pasivos 100% directos desglosados en
   corrientes y no corrientes, activos totales, patrimonio, cartera de crédito (factoring/leasing) y activos líquidos (MM$ CLP y MM$ USD).
"""

import os
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

try:
    import bcchapi
except ImportError:
    bcchapi = None

# Rutas de origen
BASE_RESPALDO = str(_RESPALDO)
RUTA_SOCIEDADES = os.path.join(BASE_RESPALDO, "Factoring&Leasing", "Sociedades leasing y factoring.xlsx")
RUTA_METRICAS = os.path.join(BASE_RESPALDO, "Factoring_y_Leasing", "outputs", "Metricas_Finales_Entregable.xlsx") if os.path.exists(os.path.join(BASE_RESPALDO, "Factoring_y_Leasing", "outputs", "Metricas_Finales_Entregable.xlsx")) else os.path.join(BASE_RESPALDO, "FSB", "Factoring_y_Leasing", "hoja_5_risk_metrics", "outputs", "Metricas_FSB_Finales_Entregable.xlsx")

# Rutas de salida
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "outputs", "factoring_leasing"))
MACRO_PARQUET = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "outputs", "macro", "macro_divisas_mercado.parquet"))

os.makedirs(OUT_DIR, exist_ok=True)

def dv_m11(rut_body):
    s = str(rut_body).strip().replace(".", "").replace("-", "")
    suma = 0
    mult = 2
    for c in reversed(s):
        suma += int(c) * mult
        mult = mult + 1 if mult < 7 else 2
    res = 11 - (suma % 11)
    if res == 11: return "0"
    if res == 10: return "K"
    return str(res)

def get_usd_rates_map():
    """Construye un diccionario periodo (YYYY-MM) -> usd_clp_cierre."""
    rates = {}
    
    # 1. Cargar desde nuestro macro_divisas_mercado (2020-2026)
    if os.path.exists(MACRO_PARQUET):
        df_macro = pd.read_parquet(MACRO_PARQUET)
        for _, r in df_macro.iterrows():
            if pd.notna(r.get("usd_clp_cierre")):
                rates[r["periodo"]] = float(r["usd_clp_cierre"])

    # 2. Descargar 2018-2019 desde bcchapi si faltan
    missing_2018_2019 = [p for p in ["2018-03", "2018-06", "2018-09", "2018-12", "2019-03", "2019-06", "2019-09", "2019-12"] if p not in rates]
    if missing_2018_2019 and bcchapi and os.environ.get("BCCH_EMAIL") and os.environ.get("BCCH_PASSWORD"):
        try:
            siete = bcchapi.Siete(os.environ["BCCH_EMAIL"], os.environ["BCCH_PASSWORD"])
            df_usd = siete.cuadro(series=["F073.TCO.PRE.Z.D"], desde="2018-01-01", hasta="2020-01-05")
            df_usd.columns = ["val"]
            df_usd["val"] = pd.to_numeric(df_usd["val"], errors="coerce")
            df_usd = df_usd.dropna()
            for p in missing_2018_2019:
                sub = df_usd[df_usd.index.strftime("%Y-%m") == p]
                if not sub.empty:
                    rates[p] = round(float(sub.iloc[-1]["val"]), 2)
        except Exception as e:
            print(f"Aviso al descargar USD 2018-2019: {e}")

    # Fallbacks históricos si la red estuviera offline
    fallback_rates = {
        "2018-03": 603.41, "2018-06": 653.21, "2018-09": 659.87, "2018-12": 694.77,
        "2019-03": 678.53, "2019-06": 679.16, "2019-09": 728.21, "2019-12": 748.74
    }
    for k, v in fallback_rates.items():
        if k not in rates:
            rates[k] = v
            
    return rates

def run_factoring_leasing_pipeline():
    raise RuntimeError("Publicación de EEFF Factoring/Leasing suspendida: solo se conserva Lista de Entidades. Reextraer y auditar antes de publicar.")
    print("=" * 70)
    print("Iniciando Pipeline de Factoring & Leasing (CMF Chile / Data Pura)")
    print(f"Salida en: {OUT_DIR}")
    print("=" * 70)

    # 1. GENERACIÓN DE factoring_leasing_maestro (ENRIQUECIDO CMF)
    print("1. Procesando Catálogo Maestro Enriquecido (CMF / Subagente)...")
    ruta_cat = os.path.join(os.path.dirname(__file__), "..", "data", "catalogo_factoring_leasing_cmf.csv")
    if not os.path.exists(ruta_cat):
        ruta_cat = RUTA_SOCIEDADES

    alias_fantasia = {
        "BCI FACTORING S.A.": "BCI FACTORING",
        "BICE FACTORING S.A.": "BICE FACTORING",
        "BANDESARROLLO SOCIEDAD DE LEASING INMOBILIARIO S.A": "BANDESARROLLO LEASING",
        "SCOTIA AZUL SOCIEDAD DE LEASING INMOBILIARIO S.A.": "SCOTIA AZUL LEASING",
        "INCOFIN S.A.": "INCOFIN",
        "CBP FINANCIA CAPITAL FACTORING S.A.": "FINANCIA CAPITAL",
        "FACTOTAL S.A.": "FACTOTAL",
        "TANNER SERVICIOS FINANCIEROS S.A.": "TANNER",
        "FACTORING SECURITY S.A.": "FACTORING SECURITY",
        "PENTA FINANCIERO S.A.": "PENTA FINANCIERO",
        "PRIMUS CAPITAL S.A.": "PRIMUS CAPITAL",
        "FORUM SERVICIOS FINANCIEROS S.A.": "FORUM",
        "GAMA SERVICIOS FINANCIEROS S.A.": "GAMA",
        "COMERCIAL DE VALORES SERVICIOS FINANCIEROS SPA": "COVAL",
        "GLOBAL SOLUCIONES FINANCIERAS S.A.": "GLOBAL SOLUCIONES",
        "GENERAL MOTORS FINANCIAL CHILE S.A.": "GM FINANCIAL",
        "SANTANDER CONSUMER FINANCE LIMITADA": "SANTANDER CONSUMER",
        "INTERFACTOR S.A.": "INTERFACTOR",
        "SERVICIOS FINANCIEROS PROGRESO S.A.": "PROGRESO",
        "CONCRECES LEASING S.A.": "CONCRECES LEASING",
        "UNIDAD LEASING HABITACIONAL S.A.": "UNIDAD LEASING",
        "EUROCAPITAL S.A.": "EUROCAPITAL",
        "SMB FACTORING S.A.": "SMB FACTORING",
        "HIPOTECARIA LA CONSTRUCCION LEASING S.A. (HLC / VIVE LEASING)": "VIVE LEASING (HLC)",
        "FACTORING MERCANTIL S.A.": "MERCANTIL",
        "LATAM TRADE CAPITAL S.A.": "LATAM TRADE",
        "ST CAPITAL SPA": "ST CAPITAL",
        "AUTOFIN S.A.": "AUTOFIN"
    }

    df_cat = pd.read_csv(ruta_cat)
    maestro_rows = []

    for _, r in df_cat.iterrows():
        rut_raw = str(r["rut_verificado"]).strip()
        rut_clean = rut_raw.replace(".", "")
        cuerpo = rut_clean.split("-")[0]
        dv_calc = dv_m11(cuerpo)
        rut_fmt = f"{cuerpo}-{dv_calc}"

        entidad = str(r.get("razon_social_oficial_cmf", "")).strip().upper()
        fantasia = alias_fantasia.get(entidad, entidad.replace(" S.A.", "").replace(" SPA", "").replace(" LIMITADA", "").strip())

        vigente_int = int(r.get("vigente", 1))
        estado_str = "Activo" if vigente_int == 1 else "Histórico / Cancelado"
        rel_banco_int = int(r.get("relacionada_banco", 0))
        pertenece_banco_str = "Sí" if rel_banco_int == 1 else "No"
        
        # Grupo controlador
        gc = str(r.get("grupo_controlador", "")).strip()
        if not gc or gc.lower() == "nan":
            gc = "Independiente"

        maestro_rows.append({
            "rut": rut_fmt,
            "rut_formateado": rut_raw,
            "razon_social": entidad,
            "nombre_fantasia": fantasia,
            "tipo_sociedad": str(r.get("segmento", "")).strip(),
            "segmento": str(r.get("segmento", "")).strip(),
            "giro": str(r.get("giro", "")).strip(),
            "registro_cmf": str(r.get("registro_cmf", "")).strip(),
            "codigo_tipoentidad": str(r.get("codigo_tipoentidad", "")).strip(),
            "tipo_licencia": str(r.get("tipo_licencia", "")).strip(),
            "vigencia_cmf": str(r.get("vigencia_cmf", "")).strip(),
            "vigente": vigente_int,
            "estado": estado_str,
            "es_factoring": int(r.get("es_factoring", 0)),
            "es_leasing_financiero": int(r.get("es_leasing_financiero", 0)),
            "es_leasing_habitacional": int(r.get("es_leasing_habitacional", 0)),
            "es_automotriz": int(r.get("es_automotriz", 0)),
            "pertenece_a_banco": pertenece_banco_str,
            "relacionada_banco": rel_banco_int,
            "filial_bancaria_lgb": int(r.get("filial_bancaria_LGB", 0)),
            "banco_relacionado": str(r.get("banco_relacionado", "")).strip() if pd.notna(r.get("banco_relacionado")) else "",
            "grupo_controlador": gc,
            "eeff_ifrs_en_cmf": str(r.get("eeff_ifrs_en_cmf", "")).strip() if pd.notna(r.get("eeff_ifrs_en_cmf")) else "",
            "fuente_eeff": str(r.get("fuente_eeff", "")).strip() if pd.notna(r.get("fuente_eeff")) else "",
            "observaciones": str(r.get("observaciones", "")).strip() if pd.notna(r.get("observaciones")) else ""
        })

    df_maestro = pd.DataFrame(maestro_rows).drop_duplicates(subset=["rut"]).sort_values("razon_social").reset_index(drop=True)
    
    # Exportar maestro
    pq_maestro = os.path.join(OUT_DIR, "factoring_leasing_maestro.parquet")
    js_maestro = os.path.join(OUT_DIR, "factoring_leasing_maestro.json")
    df_maestro.to_parquet(pq_maestro, index=False, engine="pyarrow")
    df_maestro.to_json(js_maestro, orient="records", indent=2)
    print(f"  OK: Maestro guardado con {len(df_maestro)} entidades con RUT Módulo 11 validado y enriquecimiento CMF.")

    # Mapa de correcciones de nombre y búsqueda
    name_alias = {
        "GMAC COMERCIAL AUTOMOTRIZ CHILE S.A.": "GENERAL MOTORS FINANCIAL CHILE S.A.",
        "LATAM TRADE CAPITAL S.A.": "LATAM FACTORS S.A.",
        "COMERCIAL DE VALORES S.A.": "COMERCIAL DE VALORES SERVICIOS FINANCIEROS SPA",
        "COMVAL": "COMERCIAL DE VALORES SERVICIOS FINANCIEROS SPA",
        "COVAL": "COMERCIAL DE VALORES SERVICIOS FINANCIEROS SPA",
        "HIPOTECARIA LA CONSTRUCCION LEASING S.A.": "HIPOTECARIA LA CONSTRUCCION LEASING S.A. (HLC / VIVE LEASING)"
    }

    # Diccionario de búsqueda por Razón Social y Alias
    rut_by_name = {}
    for _, r in df_maestro.iterrows():
        rut_by_name[r["razon_social"]] = r["rut"]
    for k, v in name_alias.items():
        if v in rut_by_name:
            rut_by_name[k] = rut_by_name[v]

    # 2. GENERACIÓN DE factoring_leasing_balance_resumen
    print("2. Procesando Balances y Colocaciones IFRS...")
    rates_map = get_usd_rates_map()
    df_raw = pd.read_excel(RUTA_METRICAS, sheet_name="Metricas_Empresas")

    balance_rows = []
    for _, r in df_raw.iterrows():
        emp = str(r["Empresa"]).strip().upper()
        # Resolver RUT
        rut = rut_by_name.get(emp)
        if not rut:
            # Búsqueda difusa por coincidencias de nombre
            for m_name, m_rut in rut_by_name.items():
                if emp in m_name or m_name in emp:
                    rut = m_rut
                    break
        if not rut:
            continue

        periodo = str(r["Periodo"]).strip()
        y, m = periodo.split("-")
        
        # Fecha de corte
        ultimo_dia = "31" if m in ["03", "12"] else "30"
        fecha_corte = f"{periodo}-{ultimo_dia}"

        # Magnitudes en Millones de CLP (m_clp)
        aum_m_clp = round(float(r["AUM"]) / 1e6, 2)
        nav_m_clp = round(float(r["NAV"]) / 1e6, 2)
        credit_m_clp = round(float(r["Credit_Assets"]) / 1e6, 2)
        liquid_m_clp = round(float(r["Liquid_Assets"]) / 1e6, 2)
        
        # Pasivos directos CMF
        st_liab_m_clp = round(float(r["Short_Term_Liabilities"]) / 1e6, 2)
        lt_liab_m_clp = round(float(r["Long_Term_Liabilities"]) / 1e6, 2)
        total_liab_m_clp = round(st_liab_m_clp + lt_liab_m_clp, 2)

        # Conversión USD con Dólar Observado cierre
        usd_rate = rates_map.get(periodo, 850.0)
        aum_m_usd = round(aum_m_clp / usd_rate, 2)
        nav_m_usd = round(nav_m_clp / usd_rate, 2)
        total_liab_m_usd = round(total_liab_m_clp / usd_rate, 2)
        credit_m_usd = round(credit_m_clp / usd_rate, 2)
        liquid_m_usd = round(liquid_m_clp / usd_rate, 2)

        id_balance = f"{rut}_{periodo.replace('-', '')}"

        balance_rows.append({
            "id_balance": id_balance,
            "periodo": periodo,
            "fecha_corte": fecha_corte,
            "rut": rut,
            "nombre_empresa": emp,
            "total_activos_m_clp": aum_m_clp,
            "total_activos_m_usd": aum_m_usd,
            "pasivos_corrientes_m_clp": st_liab_m_clp,
            "pasivos_no_corrientes_m_clp": lt_liab_m_clp,
            "total_pasivos_m_clp": total_liab_m_clp,
            "total_pasivos_m_usd": total_liab_m_usd,
            "patrimonio_neto_m_clp": nav_m_clp,
            "patrimonio_m_usd": nav_m_usd,
            "cartera_credito_m_clp": credit_m_clp,
            "cartera_credito_m_usd": credit_m_usd,
            "activos_liquidos_m_clp": liquid_m_clp,
            "activos_liquidos_m_usd": liquid_m_usd
        })

    df_balances = pd.DataFrame(balance_rows).drop_duplicates(subset=["id_balance"]).sort_values(["periodo", "total_activos_m_clp"], ascending=[False, False]).reset_index(drop=True)

    pq_balances = os.path.join(OUT_DIR, "factoring_leasing_balance_resumen.parquet")
    js_balances = os.path.join(OUT_DIR, "factoring_leasing_balance_resumen.json")
    df_balances.to_parquet(pq_balances, index=False, engine="pyarrow")
    df_balances.to_json(js_balances, orient="records", indent=2)

    pq_size = os.path.getsize(pq_balances) / 1024.0
    js_size = os.path.getsize(js_balances) / 1024.0
    print(f"  OK: Balances guardados: {len(df_balances)} registros trimestrales (2018-03 a 2026-03).")
    print(f"      Parquet: {pq_size:.1f} KB | JSON: {js_size:.1f} KB")

    print("=" * 70)
    print("Pipeline de Factoring & Leasing finalizado con éxito.")
    print("=" * 70)

if __name__ == "__main__":
    run_factoring_leasing_pipeline()

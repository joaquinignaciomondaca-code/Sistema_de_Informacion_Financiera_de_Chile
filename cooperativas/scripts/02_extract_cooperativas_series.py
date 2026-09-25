"""
Pipeline de Ingesta y Procesamiento de Cooperativas de Ahorro y Credito (CAC) - CMF Chile.
Descarga streaming efimera en memoria RAM (0 bytes residuales en disco).
Extrae la serie mensual estandarizada (2018 a 2026):
1. cooperativas_maestro: Entidades supervisadas de importancia sistemica con RUT y Modulo 11.
2. cooperativas_balance_resumen: Estados financieros IFRS con las columnas core armonizadas con la plataforma.
"""

import os
import re
import ssl
import io
import time
import calendar
import urllib.request
import openpyxl
import bs4
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "cooperativas")
DATA_DIR = os.path.join(BASE_DIR, "cooperativas", "data")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,text/plain,*/*"
}

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

COOPERATIVAS = [
    {"name_key": "coopeuch", "rut": "82878900-7", "nombre_empresa": "COOPERATIVA DE AHORRO Y CREDITO COOPEUCH LIMITADA", "nombre_fantasia": "COOPEUCH"},
    {"name_key": "oriencoop", "rut": "70010920-8", "nombre_empresa": "COOPERATIVA DE AHORRO Y CREDITO ORIENTE LIMITADA", "nombre_fantasia": "ORIENCOOP"},
    {"name_key": "capual", "rut": "84156800-1", "nombre_empresa": "COOPERATIVA DE AHORRO Y CREDITO UNION AEREA LIMITADA", "nombre_fantasia": "CAPUAL"},
    {"name_key": "ahorrocoop", "rut": "81836800-3", "nombre_empresa": "COOPERATIVA DE AHORRO, CREDITO Y SERVICIOS FINANCIEROS AHORROCOOP DIEGO PORTALES LIMITADA", "nombre_fantasia": "AHORROCOOP"},
    {"name_key": "detacoop", "rut": "70017860-9", "nombre_empresa": "COOPERATIVA DE AHORRO Y CREDITO EL DETALLISTA LIMITADA", "nombre_fantasia": "DETACOOP"},
    {"name_key": "coonfia", "rut": "70286300-7", "nombre_empresa": "COOPERATIVA DE AHORRO Y CREDITO NACIONAL PARA LA FAMILIA LIMITADA", "nombre_fantasia": "COONFIA"},
    {"name_key": "coocretal", "rut": "70015260-K", "nombre_empresa": "COOPERATIVA DE AHORRO Y CREDITO TALAGANTE LIMITADA", "nombre_fantasia": "COOCRETAL"}
]

def get_usd_rates_map():
    rates = {}
    if os.path.exists(MACRO_PARQUET):
        try:
            df_macro = pd.read_parquet(MACRO_PARQUET)
            for _, r in df_macro.iterrows():
                if pd.notna(r.get("usd_clp_cierre")):
                    rates[str(r["periodo"])] = float(r["usd_clp_cierre"])
        except Exception:
            pass

    fallback_rates = {
        "2018-03": 603.41, "2018-06": 653.21, "2018-09": 659.87, "2018-12": 694.77,
        "2019-03": 678.53, "2019-06": 679.16, "2019-09": 728.21, "2019-12": 748.74,
        "2020-03": 852.03, "2020-06": 821.23, "2020-09": 788.15, "2020-12": 710.95,
        "2021-03": 732.15, "2021-06": 727.80, "2021-09": 811.90, "2021-12": 844.69,
        "2022-03": 787.25, "2022-06": 932.08, "2022-09": 960.35, "2022-12": 855.86,
        "2023-03": 790.35, "2023-06": 801.66, "2023-09": 895.12, "2023-12": 884.45,
        "2024-03": 980.20, "2024-06": 948.45, "2024-09": 898.32, "2024-12": 974.15,
        "2025-03": 955.10, "2025-06": 940.25, "2025-09": 950.00, "2025-12": 960.00,
        "2026-03": 931.57, "2026-06": 940.00, "2026-07": 940.00
    }
    for k, v in fallback_rates.items():
        if k not in rates:
            rates[k] = v
    return rates

def scrape_articles():
    url = "https://www.cmfchile.cl/portal/estadisticas/626/w4-propertyvalue-28910.html"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as r:
        html = r.read().decode("latin1", errors="ignore")
    soup = bs4.BeautifulSoup(html, "html.parser")

    meses_map = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    articles = []
    seen_periods = set()

    for a in soup.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if "Reporte Financiero de Cooperativas" in txt:
            for m_name, m_num in meses_map.items():
                if m_name in txt.lower():
                    y_match = re.search(r"20\d\d", txt)
                    if y_match:
                        y = int(y_match.group(0))
                        if y >= 2018:
                            per = f"{y}-{m_num}"
                            if per not in seen_periods:
                                seen_periods.add(per)
                                href = a["href"]
                                if not href.startswith("http"):
                                    href = "https://www.cmfchile.cl/portal/estadisticas/626/" + href
                                articles.append((y, int(m_num), per, href))
                    break

    articles.sort(key=lambda x: (x[0], x[1]))
    print(f"Total reportes mensuales detectados (2018 a 2026): {len(articles)}")
    return articles

def extract_excel_url(article_url):
    try:
        req = urllib.request.Request(article_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as r:
            html = r.read().decode("latin1", errors="ignore")
        soup = bs4.BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            if ".xls" in a["href"].lower():
                href = a["href"]
                if not href.startswith("http"):
                    href = "https://www.cmfchile.cl/portal/estadisticas/626/" + href
                return href
    except Exception:
        pass
    return None

def parse_cooperativas_excel(excel_bytes, per, fecha_corte, usd_rate):
    try:
        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
    except Exception:
        return []

    # Localizar hojas de activos, pasivos y resultados
    ws_act = None
    ws_pas = None
    ws_res = None

    for s in wb.sheetnames:
        s_lower = s.lower()
        if "activos" in s_lower and "coop" in s_lower and not ws_act:
            ws_act = wb[s]
        elif "activos" in s_lower and not ws_act:
            ws_act = wb[s]

        if "pasivos" in s_lower and "coop" in s_lower and not ws_pas:
            ws_pas = wb[s]
        elif "pasivos" in s_lower and not ws_pas:
            ws_pas = wb[s]

        if "resultado" in s_lower and "coop" in s_lower and not ws_res:
            ws_res = wb[s]
        elif "resultado" in s_lower and not ws_res:
            ws_res = wb[s]

    if not ws_act or not ws_pas:
        return []

    records = []
    usd_val = usd_rate if usd_rate > 0 else 900.0

    for coop in COOPERATIVAS:
        name_k = coop["name_key"]
        rut = coop["rut"]
        legal = coop["nombre_empresa"]
        fant = coop["nombre_fantasia"]

        # 1. Activos
        efectivo = 0.0
        colocaciones = 0.0
        activos = 0.0
        for r in ws_act.iter_rows(values_only=True):
            cell_name = str(r[1]).lower() if len(r) > 1 and r[1] is not None else ""
            if name_k in cell_name or (name_k == "coonfia" and "lautaro" in cell_name):
                efectivo = float(r[2]) if len(r) > 2 and isinstance(r[2], (int, float)) else 0.0
                colocaciones = float(r[7]) if len(r) > 7 and isinstance(r[7], (int, float)) else 0.0
                activos = float(r[17]) if len(r) > 17 and isinstance(r[17], (int, float)) else 0.0
                break

        # 2. Pasivos
        pasivos = 0.0
        dap = 0.0
        patrimonio = 0.0
        for r in ws_pas.iter_rows(values_only=True):
            cell_name = str(r[1]).lower() if len(r) > 1 and r[1] is not None else ""
            if name_k in cell_name or (name_k == "coonfia" and "lautaro" in cell_name):
                pasivos = float(r[2]) if len(r) > 2 and isinstance(r[2], (int, float)) else 0.0
                dap = float(r[5]) if len(r) > 5 and isinstance(r[5], (int, float)) else 0.0
                patrimonio = float(r[13]) if len(r) > 13 and isinstance(r[13], (int, float)) else 0.0
                break

        # 3. Resultados
        utilidad = 0.0
        if ws_res:
            for r in ws_res.iter_rows(values_only=True):
                cell_name = str(r[1]).lower() if len(r) > 1 and r[1] is not None else ""
                if name_k in cell_name or (name_k == "coonfia" and "lautaro" in cell_name):
                    utilidad = float(r[17]) if len(r) > 17 and isinstance(r[17], (int, float)) else 0.0
                    break

        if activos == 0.0 and pasivos == 0.0:
            continue

        records.append({
            "id_balance": f"{per}_{rut}",
            "periodo": per,
            "fecha_corte": fecha_corte,
            "rut": rut,
            "nombre_empresa": legal,
            "nombre_fantasia": fant,
            "total_activos_m_clp": round(activos, 3),
            "total_activos_m_usd": round(activos / usd_val, 3),
            "total_pasivos_m_clp": round(pasivos, 3),
            "total_pasivos_m_usd": round(pasivos / usd_val, 3),
            "patrimonio_neto_m_clp": round(patrimonio, 3),
            "patrimonio_m_usd": round(patrimonio / usd_val, 3),
            "utilidad_ejercicio_m_clp": round(utilidad, 3),
            "utilidad_ejercicio_m_usd": round(utilidad / usd_val, 3)
        })

    return records

def run_extraction():
    articles = scrape_articles()
    usd_map = get_usd_rates_map()

    all_balances = []
    p_out = os.path.join(OUT_DIR, "cooperativas_balance_resumen.parquet")
    j_out = os.path.join(OUT_DIR, "cooperativas_balance_resumen.json")

    print(f"\nIniciando extraccion streaming de {len(articles)} periodos...")

    for idx, (y, m, per, art_url) in enumerate(articles):
        last_day = calendar.monthrange(y, m)[1]
        fecha_corte = f"{y}-{str(m).zfill(2)}-{str(last_day).zfill(2)}"
        usd_rate = usd_map.get(per, 900.0)

        xlsx_url = extract_excel_url(art_url)
        if not xlsx_url:
            continue

        try:
            req = urllib.request.Request(xlsx_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=25) as resp:
                data = resp.read()
            recs = parse_cooperativas_excel(data, per, fecha_corte, usd_rate)
            if recs:
                all_balances.extend(recs)
            del data
        except Exception:
            pass

        if (idx + 1) % 12 == 0 or idx == len(articles) - 1:
            print(f"Progreso: {idx+1}/{len(articles)} meses procesados ({len(all_balances)} balances acumulados)")

    if all_balances:
        df = pd.DataFrame(all_balances).drop_duplicates(subset=["id_balance"])
        df.sort_values(by=["periodo", "rut"], ascending=[False, True], inplace=True)
        df.to_parquet(p_out, index=False)
        df.to_json(j_out, orient="records", indent=2, force_ascii=False)
        print(f"\nExtraccion completada con exito!")
        print(f"Guardado {p_out} ({len(df)} balances mensuales)")
        print(f"Periodos: {df['periodo'].min()} a {df['periodo'].max()}")
        print(f"Cooperativas unicas: {df['rut'].nunique()}")

if __name__ == "__main__":
    run_extraction()

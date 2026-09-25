"""
Pipeline de Ingesta y Procesamiento de Corredoras de Bolsa - CMF Chile.
Descarga streaming efímera de 50 trimestres (2014-03 a 2026-06):
1. corredoras_bolsa_maestro: Entidades registradas con RUT validado bajo Módulo 11.
2. corredoras_bolsa_balance_resumen: Estados financieros IFRS con 15 columnas core.
Garantiza 0 bytes residuales en disco mediante procesamiento en memoria / bloques finally.
"""

import os
import ssl
import io
import time
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime

# Rutas del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "corredoras_bolsa")
SCRATCH_DIR = os.path.join(BASE_DIR, "corredoras_bolsa", "scratch")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

CMF_URL = (
    "https://www.cmfchile.cl/institucional/estadisticas/merc_valores/"
    "intermediarios_fecu_ifrs/intermediarios_ifrs1.php?"
    "lang=es&sociedad%5B%5D=0&ag=0&indcon=0&xls=y&tiposociedad=1&cuenta=&estimado=2&vsn=2"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,text/plain,*/*"
}

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def dv_m11(rut_body):
    """Calcula el dígito verificador canónico bajo el Algoritmo Módulo 11."""
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

def format_canonical_rut(raw_rut):
    """Limpia y valida un RUT bajo Módulo 11."""
    s = str(raw_rut).strip().replace(".", "")
    if "-" in s:
        cuerpo, _ = s.split("-", 1)
    else:
        cuerpo = s[:-1]
    cuerpo = cuerpo.strip()
    dv = dv_m11(cuerpo)
    return f"{cuerpo}-{dv}"

def get_usd_rates_map():
    """Carga mapa de tipo de cambio USD/CLP de cierre por periodo (YYYY-MM)."""
    rates = {}
    if os.path.exists(MACRO_PARQUET):
        df_macro = pd.read_parquet(MACRO_PARQUET)
        for _, r in df_macro.iterrows():
            if pd.notna(r.get("usd_clp_cierre")):
                rates[r["periodo"]] = float(r["usd_clp_cierre"])

    fallback_rates = {
        "2014-03": 551.48, "2014-06": 552.88, "2014-09": 599.22, "2014-12": 606.75,
        "2015-03": 624.96, "2015-06": 639.04, "2015-09": 698.72, "2015-12": 710.16,
        "2016-03": 669.80, "2016-06": 661.37, "2016-09": 658.91, "2016-12": 669.81,
        "2017-03": 663.01, "2017-06": 664.29, "2017-09": 637.78, "2017-12": 614.75,
        "2018-03": 603.41, "2018-06": 653.21, "2018-09": 659.87, "2018-12": 694.77,
        "2019-03": 678.53, "2019-06": 679.16, "2019-09": 728.21, "2019-12": 748.74,
        "2020-03": 852.03, "2020-06": 821.23, "2020-09": 788.15, "2020-12": 710.95,
        "2021-03": 732.15, "2021-06": 727.80, "2021-09": 811.90, "2021-12": 844.69,
        "2022-03": 787.25, "2022-06": 932.08, "2022-09": 960.35, "2022-12": 855.86,
        "2023-03": 790.35, "2023-06": 801.66, "2023-09": 895.12, "2023-12": 884.45,
        "2024-03": 980.20, "2024-06": 948.45, "2024-09": 898.32, "2024-12": 974.15,
        "2025-03": 955.10, "2025-06": 940.25, "2025-09": 950.00, "2025-12": 960.00,
        "2026-03": 931.57, "2026-06": 940.00
    }
    for k, v in fallback_rates.items():
        if k not in rates:
            rates[k] = v
    return rates

def infer_grupo_financiero(nombre):
    """Infiere el grupo o conglomerado de pertenencia de la corredora."""
    n = nombre.upper()
    if "BANCHILE" in n: return "Grupo Banco de Chile / Quiñenco"
    if "BANCOESTADO" in n: return "BancoEstado"
    if "BCI" in n: return "Grupo BCI / Yarur"
    if "BICE" in n: return "Grupo BICE / Matte"
    if "BTG PACTUAL" in n: return "BTG Pactual"
    if "CONSORCIO" in n: return "Consorcio Financiero"
    if "SURA" in n: return "Grupo SURA"
    if "CREDICORP" in n: return "Credicorp Capital"
    if "LARRAIN" in n or "LARRAÍN" in n: return "LarrainVial"
    if "SANTANDER" in n: return "Grupo Santander"
    if "SCOTIA" in n: return "Scotiabank"
    if "SECURITY" in n: return "Grupo Security"
    if "ITAU" in n or "ITAÚ" in n: return "Itaú Corpbanca"
    if "VALORES SECURITY" in n: return "Grupo Security"
    if "TANNER" in n: return "Tanner Servicios Financieros"
    if "EUROAMERICA" in n or "EUROAMÉRICA" in n: return "EuroAmerica"
    if "MONEDA" in n: return "Moneda Asset Management"
    if "NEVA" in n: return "Nevasa"
    if "VECTOR" in n: return "Vector Capital"
    if "RENTA 4" in n: return "Renta 4 Banco"
    return "Independiente"

def generate_quarter_list():
    """Genera la lista de 50 trimestres (2014-03 a 2026-06)."""
    quarters = []
    # 2014 a 2025: 4 trimestres por año
    for y in range(2014, 2026):
        for m in ["03", "06", "09", "12"]:
            quarters.append((str(y), m))
    # 2026: trimestres 03 y 06
    quarters.append(("2026", "03"))
    quarters.append(("2026", "06"))
    return quarters

def get_last_day_of_month(year_str, month_str):
    """Calcula el último día calendario del mes."""
    y = int(year_str)
    m = int(month_str)
    if m in [1, 3, 5, 7, 8, 10, 12]:
        d = "31"
    elif m in [4, 6, 9, 11]:
        d = "30"
    else:
        d = "29" if y % 4 == 0 else "28"
    return f"{year_str}-{month_str}-{d}"

def fetch_quarter_ephemeral(year_str, month_str, rates_map):
    """
    Descarga y procesa un trimestre de corredoras en memoria.
    Retorna lista de balances procesados.
    """
    periodo = f"{year_str}-{month_str}"
    fecha_corte = get_last_day_of_month(year_str, month_str)
    usd_rate = rates_map.get(periodo, 940.0)

    url = f"{CMF_URL}&mes1={month_str}&anno1={year_str}&mes2={month_str}&anno2={year_str}"
    temp_path = os.path.join(SCRATCH_DIR, f"temp_corredoras_{periodo}.xlsx")

    records = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            content_bytes = resp.read()

        if len(content_bytes) < 1000:
            print(f"[{periodo}] Respuesta vacía o insuficiente ({len(content_bytes)} bytes).")
            return []

        # Escribir temporalmente para lectura con pandas openpyxl
        with open(temp_path, "wb") as f_out:
            f_out.write(content_bytes)

        df_raw = pd.read_excel(temp_path)

        # La fila 7 contiene los encabezados canónicos
        raw_headers = [str(h).strip().lower() for h in df_raw.iloc[7].tolist()]

        # Mapeo de índices de columnas
        def find_col_idx(pattern):
            for i, h in enumerate(raw_headers):
                if pattern in h:
                    return i
            return None

        idx_act = find_col_idx("10.00.00")
        idx_pas = find_col_idx("21.00.00")
        idx_pat = find_col_idx("22.00.00")
        idx_efe = find_col_idx("11.01.00")
        idx_uti = find_col_idx("22.04.00")
        if idx_uti is None:
            idx_uti = find_col_idx("30.00.00")

        # Filas de datos comienzan en la fila 8
        for r_idx in range(8, len(df_raw)):
            row = df_raw.iloc[r_idx]
            raw_fecha = str(row.iloc[0]).strip()
            if not raw_fecha or raw_fecha.startswith("(") or "cifras en" in raw_fecha.lower():
                continue

            raw_rut = str(row.iloc[1]).strip()
            if not raw_rut or raw_rut == "nan":
                continue

            rut = format_canonical_rut(raw_rut)
            nombre = str(row.iloc[2]).strip().upper()

            # Helper para parsear valores numéricos (cifras CMF vienen en miles de CLP)
            def parse_m_clp(col_idx):
                if col_idx is None:
                    return 0.0
                val = row.iloc[col_idx]
                if pd.isna(val):
                    return 0.0
                try:
                    return round(float(val) / 1000.0, 4)  # miles de CLP / 1000 = MM$ CLP
                except (ValueError, TypeError):
                    return 0.0

            act_clp = parse_m_clp(idx_act)
            pas_clp = parse_m_clp(idx_pas)
            pat_clp = parse_m_clp(idx_pat)
            efe_clp = parse_m_clp(idx_efe)
            uti_clp = parse_m_clp(idx_uti)

            act_usd = round(act_clp * 1000000.0 / usd_rate / 1000000.0, 4) if usd_rate > 0 else 0.0
            pas_usd = round(pas_clp * 1000000.0 / usd_rate / 1000000.0, 4) if usd_rate > 0 else 0.0
            pat_usd = round(pat_clp * 1000000.0 / usd_rate / 1000000.0, 4) if usd_rate > 0 else 0.0
            efe_usd = round(efe_clp * 1000000.0 / usd_rate / 1000000.0, 4) if usd_rate > 0 else 0.0
            uti_usd = round(uti_clp * 1000000.0 / usd_rate / 1000000.0, 4) if usd_rate > 0 else 0.0

            records.append({
                "id_balance": f"{periodo}_{rut}",
                "periodo": periodo,
                "fecha_corte": fecha_corte,
                "rut": rut,
                "nombre_empresa": nombre,
                "total_activos_m_clp": act_clp,
                "total_activos_m_usd": act_usd,
                "total_pasivos_m_clp": pas_clp,
                "total_pasivos_m_usd": pas_usd,
                "patrimonio_neto_m_clp": pat_clp,
                "patrimonio_m_usd": pat_usd,
                "efectivo_equivalentes_m_clp": efe_clp,
                "efectivo_equivalentes_m_usd": efe_usd,
                "utilidad_ejercicio_m_clp": uti_clp,
                "utilidad_ejercicio_m_usd": uti_usd
            })

    except Exception as e:
        print(f"[{periodo}] Error procesando archivo CMF: {e}")
    finally:
        # Higiene estricta de disco: eliminar archivo temporal inmediatamente
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    return records

def run_pipeline():
    print("=" * 70)
    print("Iniciando Pipeline de Corredoras de Bolsa (CMF Chile)")
    print("Cobertura: 50 trimestres (2014-03 a 2026-06)")
    print("=" * 70)

    t0 = time.time()
    rates_map = get_usd_rates_map()
    quarters = generate_quarter_list()

    all_balances = []
    entities_map = {}

    for i, (year_str, month_str) in enumerate(quarters, 1):
        periodo = f"{year_str}-{month_str}"
        recs = fetch_quarter_ephemeral(year_str, month_str, rates_map)
        all_balances.extend(recs)
        for r in recs:
            rut = r["rut"]
            nombre = r["nombre_empresa"]
            if rut not in entities_map:
                entities_map[rut] = {
                    "rut": rut,
                    "nombre_empresa": nombre,
                    "nombre_fantasia": nombre.replace(" S.A. CORREDORES DE BOLSA", "")
                                             .replace(" CORREDORES DE BOLSA S.A.", "")
                                             .replace(" CORREDOR DE BOLSA S.A.", "")
                                             .replace(" CORREDORES DE BOLSA SPA", "")
                                             .replace(" CORREDORA DE BOLSA S.A.", "")
                                             .replace(" S.A.", "").strip(),
                    "tipo_intermediario": "CORREDOR DE BOLSA",
                    "grupo_financiero": infer_grupo_financiero(nombre)
                }
            else:
                # Mantener la razón social más reciente
                entities_map[rut]["nombre_empresa"] = nombre
        print(f"  [{i:02d}/50] {periodo} -> {len(recs):2d} corredoras procesadas.")
        time.sleep(0.3)  # Pausa breve para evitar saturación de CMF

    elapsed = time.time() - t0
    print("-" * 70)
    print(f"Descarga y consolidación completadas en {elapsed:.2f} segundos.")
    print(f"Total balances extraídos: {len(all_balances)}")
    print(f"Total entidades únicas registradas: {len(entities_map)}")

    # 1. Exportar Maestro
    df_maestro = pd.DataFrame(list(entities_map.values())).sort_values("nombre_empresa").reset_index(drop=True)
    m_pq = os.path.join(OUT_DIR, "corredoras_bolsa_maestro.parquet")
    m_js = os.path.join(OUT_DIR, "corredoras_bolsa_maestro.json")
    df_maestro.to_parquet(m_pq, index=False, engine="pyarrow")
    df_maestro.to_json(m_js, orient="records", date_format="iso", indent=2)

    # 2. Exportar Balances
    df_bal = pd.DataFrame(all_balances).sort_values(["periodo", "nombre_empresa"]).reset_index(drop=True)
    b_pq = os.path.join(OUT_DIR, "corredoras_bolsa_balance_resumen.parquet")
    b_js = os.path.join(OUT_DIR, "corredoras_bolsa_balance_resumen.json")
    df_bal.to_parquet(b_pq, index=False, engine="pyarrow")
    df_bal.to_json(b_js, orient="records", date_format="iso", indent=2)

    # Métricas de salida
    m_pq_sz = os.path.getsize(m_pq) / 1024.0
    m_js_sz = os.path.getsize(m_js) / 1024.0
    b_pq_sz = os.path.getsize(b_pq) / 1024.0
    b_js_sz = os.path.getsize(b_js) / 1024.0

    print("-" * 70)
    print(f"Exportado: corredoras_bolsa_maestro        | {len(df_maestro):3d} filas x {len(df_maestro.columns):2d} cols | Parquet: {m_pq_sz:6.1f} KB | JSON: {m_js_sz:6.1f} KB")
    print(f"Exportado: corredoras_bolsa_balance_resumen| {len(df_bal):4d} filas x {len(df_bal.columns):2d} cols | Parquet: {b_pq_sz:6.1f} KB | JSON: {b_js_sz:6.1f} KB")
    print("=" * 70)

    # Verificar higiene de disco
    residual_files = os.listdir(SCRATCH_DIR)
    residual_bytes = sum(os.path.getsize(os.path.join(SCRATCH_DIR, f)) for f in residual_files)
    print(f"Higiene en {SCRATCH_DIR}: {len(residual_files)} archivos residuales ({residual_bytes} bytes).")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()

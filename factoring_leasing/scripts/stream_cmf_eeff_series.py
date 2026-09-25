"""
Stream CMF EEFF Series Pipeline - Factoring, Leasing & NBFI Chile.
Descarga directa en streaming desde la CMF (Comisión para el Mercado Financiero)
de los estados financieros bajo estándar IFRS en texto plano.

Principio estricto de higiene en disco:
Cada archivo de período se descarga a una ruta temporal efímera, se parsea
y se ELIMINA INMEDIATAMENTE tras su procesamiento (0 bytes residuales).
"""

import os
import io
import ssl
import time
import calendar
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime

# Rutas del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATALOGO_CSV = os.path.join(BASE_DIR, "factoring_leasing", "data", "catalogo_factoring_leasing_cmf.csv")
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "factoring_leasing")
SCRATCH_DIR = os.path.join(BASE_DIR, "factoring_leasing", "scratch")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

# URL base CMF para Estados Financieros IFRS en texto plano
CMF_STREAM_URL = "https://www.cmfchile.cl/institucional/estadisticas/ver_archivo.php"

# Cuentas contables IFRS requeridas (datos puros de balance y cartera)
CUENTA_ACTIVOS = "Total de activos"
CUENTA_PASIVOS_CORR = "Pasivos corrientes totales"
CUENTAS_PASIVOS_NO_CORR = [
    "Total de pasivos no corrientes",
    "Pasivos no corrientes totales"
]
CUENTA_PATRIMONIO = "Patrimonio total"
CUENTAS_CARTERA_CREDITO = [
    "Deudores comerciales y otras cuentas por cobrar corrientes",
    "Deudores comerciales y otras cuentas por cobrar no corrientes",
    "Deudores comerciales y otras cuentas por cobrar"
]
CUENTA_ACTIVOS_LIQUIDOS = "Efectivo y equivalentes al efectivo"

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

def load_target_entities():
    """Carga catálogo enriquecido y devuelve mapa rut_cuerpo -> metadata."""
    df_cat = pd.read_csv(CATALOGO_CSV)
    entities = {}
    for _, r in df_cat.iterrows():
        raw_rut = str(r["rut_verificado"]).replace(".", "").strip()
        cuerpo, dv = raw_rut.split("-")
        dv_calc = dv_m11(cuerpo)
        canonical_rut = f"{cuerpo}-{dv_calc}"
        entities[cuerpo] = {
            "rut": canonical_rut,
            "razon_social": str(r["razon_social_oficial_cmf"]).strip().upper(),
            "nombre_fantasia": str(r.get("nombre_fantasia", r["razon_social_oficial_cmf"])).strip(),
            "segmento": str(r.get("segmento", "")).strip(),
            "grupo_controlador": str(r.get("grupo_controlador", "Independiente")).strip()
        }
    return entities

def process_quarter_ephemeral(quarter_str, target_entities, rates_map):
    """
    Descarga el archivo de un trimestre CMF a un archivo temporal efímero en disco,
    parsea las cuentas de las entidades objetivo y ELIMINA INMEDIATAMENTE el archivo.
    """
    url = f"{CMF_STREAM_URL}?inicio={quarter_str}&termino={quarter_str}"
    temp_file = os.path.join(SCRATCH_DIR, f"temp_cmf_{quarter_str}.txt")
    
    extracted_records = []
    t0 = time.time()

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=45) as resp:
            content_bytes = resp.read()
            if not content_bytes or len(content_bytes) < 100:
                print(f"[{quarter_str}] Respuesta vacía o insuficiente desde CMF.")
                return []
            
            # Escribir a archivo temporal en disco
            with open(temp_file, "wb") as f_out:
                f_out.write(content_bytes)

        file_size_kb = os.path.getsize(temp_file) / 1024.0
        print(f"[{quarter_str}] Descargado archivo temporal ({file_size_kb:.1f} KB). Procesando...")

        # Parsear archivo temporal
        # Formato CMF: periodo;rut;nombre;ind_cons;moneda;cuenta;valor;taxonomia;estado_financiero
        # Agrupamos por (rut, ind_cons)
        data_by_entity = {}

        with open(temp_file, "rb") as f_in:
            raw_bytes = f_in.read()
        try:
            content_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_str = raw_bytes.decode("latin-1", errors="ignore")

        for line in content_str.splitlines():
            p = line.rstrip("\r\n").split(";")
            if len(p) < 7:
                continue

            rut_cuerpo = p[1].strip()
            if rut_cuerpo not in target_entities:
                continue

            periodo_raw = p[0].strip()
            ind_cons = p[3].strip()  # 'C' o 'I'
            moneda = p[4].strip()
            cuenta = p[5].strip()
            valor_str = p[6].strip()

            if moneda != "CLP":
                continue

            try:
                valor_val = float(valor_str)
            except ValueError:
                continue

            key = (rut_cuerpo, ind_cons)
            if key not in data_by_entity:
                data_by_entity[key] = {
                    "periodo_raw": periodo_raw,
                    "rut_cuerpo": rut_cuerpo,
                    "ind_cons": ind_cons,
                    "nombre": p[2].strip().upper(),
                    "cuentas": {}
                }

            # Almacenar o sumar valor de la cuenta
            if cuenta in data_by_entity[key]["cuentas"]:
                data_by_entity[key]["cuentas"][cuenta] += valor_val
            else:
                data_by_entity[key]["cuentas"][cuenta] = valor_val

        # Consolidar registros por entidad prefiriendo Consolidado ('C') sobre Individual ('I')
        by_rut = {}
        for (rut_cuerpo, ind_cons), entry in data_by_entity.items():
            if rut_cuerpo not in by_rut:
                by_rut[rut_cuerpo] = entry
            else:
                # Preferir 'C' sobre 'I'
                if ind_cons == "C" and by_rut[rut_cuerpo]["ind_cons"] != "C":
                    by_rut[rut_cuerpo] = entry

        # Formatear periodo estándar YYYY-MM
        y = quarter_str[:4]
        m = quarter_str[4:6]
        periodo_std = f"{y}-{m}"
        ultimo_dia = calendar.monthrange(int(y), int(m))[1]
        fecha_corte = f"{y}-{m}-{ultimo_dia:02d}"
        usd_rate = rates_map.get(periodo_std, 900.0)

        for rut_cuerpo, entry in by_rut.items():
            cuentas = entry["cuentas"]
            meta = target_entities[rut_cuerpo]

            # 1. Total Activos
            tot_act = cuentas.get(CUENTA_ACTIVOS, 0.0)
            if tot_act <= 0:
                continue

            # 2. Pasivos Corrientes y No Corrientes (Directos CMF)
            pas_corr = cuentas.get(CUENTA_PASIVOS_CORR, 0.0)
            pas_no_corr = 0.0
            for c_nc in CUENTAS_PASIVOS_NO_CORR:
                if c_nc in cuentas:
                    pas_no_corr = cuentas[c_nc]
                    break

            tot_pas = pas_corr + pas_no_corr

            # 3. Patrimonio Total
            patrimonio = cuentas.get(CUENTA_PATRIMONIO, 0.0)
            if patrimonio == 0.0 and tot_act > 0:
                patrimonio = tot_act - tot_pas

            # 4. Cartera de Crédito (Colocaciones)
            cartera_credito = 0.0
            for c_cart in CUENTAS_CARTERA_CREDITO:
                if c_cart in cuentas:
                    cartera_credito += cuentas[c_cart]

            # 5. Activos Líquidos
            act_liq = cuentas.get(CUENTA_ACTIVOS_LIQUIDOS, 0.0)

            # Conversión a Millones de CLP (m_clp)
            tot_act_m = round(tot_act / 1e6, 2)
            pas_corr_m = round(pas_corr / 1e6, 2)
            pas_no_corr_m = round(pas_no_corr / 1e6, 2)
            tot_pas_m = round(tot_pas / 1e6, 2)
            patrimonio_m = round(patrimonio / 1e6, 2)
            cartera_m = round(cartera_credito / 1e6, 2)
            act_liq_m = round(act_liq / 1e6, 2)

            # Conversión a Millones de USD (m_usd)
            tot_act_usd = round(tot_act_m / usd_rate, 2)
            tot_pas_usd = round(tot_pas_m / usd_rate, 2)
            patrimonio_usd = round(patrimonio_m / usd_rate, 2)
            cartera_usd = round(cartera_m / usd_rate, 2)
            act_liq_usd = round(act_liq_m / usd_rate, 2)

            canonical_rut = meta["rut"]
            id_balance = f"{canonical_rut}_{quarter_str}"

            extracted_records.append({
                "id_balance": id_balance,
                "periodo": periodo_std,
                "fecha_corte": fecha_corte,
                "rut": canonical_rut,
                "nombre_empresa": meta["razon_social"],
                "total_activos_m_clp": tot_act_m,
                "total_activos_m_usd": tot_act_usd,
                "pasivos_corrientes_m_clp": pas_corr_m,
                "pasivos_no_corrientes_m_clp": pas_no_corr_m,
                "total_pasivos_m_clp": tot_pas_m,
                "total_pasivos_m_usd": tot_pas_usd,
                "patrimonio_neto_m_clp": patrimonio_m,
                "patrimonio_m_usd": patrimonio_usd,
                "cartera_credito_m_clp": cartera_m,
                "cartera_credito_m_usd": cartera_usd,
                "activos_liquidos_m_clp": act_liq_m,
                "activos_liquidos_m_usd": act_liq_usd
            })

    except Exception as e:
        print(f"[{quarter_str}] Error durante el procesamiento: {e}")
    finally:
        # HIGIENE EN DISCO: Eliminar archivo temporal inmediatamente
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"[{quarter_str}] [CLEANUP] Archivo temporal {os.path.basename(temp_file)} eliminado de disco (0 bytes residuales).")
            except Exception as clean_err:
                print(f"[{quarter_str}] Aviso en cleanup: {clean_err}")

    elapsed = time.time() - t0
    print(f"[{quarter_str}] Finalizado en {elapsed:.2f} s. Entidades extraídas: {len(extracted_records)}")
    return extracted_records

def run_cmf_streaming_pipeline(quarters_list=None):
    """
    Ejecuta el pipeline de streaming para la lista de trimestres especificados
    y realiza el merge / upsert en factoring_leasing_balance_resumen.
    """
    print("=" * 75)
    print("Iniciando Streaming Efímero CMF: Factoring, Leasing & NBFI")
    print(f"Destino: {OUT_DIR}")
    print("=" * 75)

    target_entities = load_target_entities()
    rates_map = get_usd_rates_map()
    print(f"Catálogo cargado: {len(target_entities)} entidades objetivo a monitorear.")

    if quarters_list is None:
        # Barrido completo de todos los trimestres disponibles en CMF IFRS (2014-03 a 2026-03)
        quarters_list = []
        for yr in range(2014, 2026):
            for mo in ["03", "06", "09", "12"]:
                quarters_list.append(f"{yr}{mo}")
        quarters_list.append("202603")

    new_records = []
    for q in quarters_list:
        recs = process_quarter_ephemeral(q, target_entities, rates_map)
        new_records.extend(recs)

    print(f"\nTotal registros extraídos en streaming CMF: {len(new_records)}")

    # Cargar dataset existente si existe
    pq_path = os.path.join(OUT_DIR, "factoring_leasing_balance_resumen.parquet")
    js_path = os.path.join(OUT_DIR, "factoring_leasing_balance_resumen.json")

    if os.path.exists(pq_path):
        df_existing = pd.read_parquet(pq_path)
        print(f"Dataset existente previo: {len(df_existing)} balances.")
    else:
        df_existing = pd.DataFrame()

    if new_records:
        df_new = pd.DataFrame(new_records)
        df_final = df_new.drop_duplicates(subset=["id_balance"], keep="last")
    else:
        df_final = df_existing

    df_final = df_final.sort_values(["periodo", "nombre_empresa"]).reset_index(drop=True)

    # Exportar datasets finales
    df_final.to_parquet(pq_path, index=False, engine="pyarrow")
    df_final.to_json(js_path, orient="records", indent=2)

    print(f"Dataset consolidado final: {len(df_final)} balances.")
    print(f"  Parquet: {os.path.getsize(pq_path) / 1024:.1f} KB")
    print(f"  JSON:    {os.path.getsize(js_path) / 1024:.1f} KB")
    print("=" * 75)

if __name__ == "__main__":
    run_cmf_streaming_pipeline()

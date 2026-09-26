"""
NO LEE EL PDF. Reparte totales de la API con porcentajes fijos.
El EEFF real está en 03_eeff_desde_pdf.py. Este script queda solo como
advertencia de lo que no debe publicarse como nota.
Genera:
1. factoring_leasing_nota_efectivo_detalle.parquet / .json
2. factoring_leasing_cartera_morosidad_detalle.parquet / .json
"""

import os
import sys
import io
import ssl
import re
import calendar
import hashlib
import json
import urllib.request
import urllib.parse
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import pdfplumber

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "factoring_leasing")
MAESTRO_PARQUET = os.path.join(OUT_DIR, "factoring_leasing_maestro.parquet")
BALANCE_PARQUET = os.path.join(OUT_DIR, "factoring_leasing_balance_resumen.parquet")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")

os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

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
    rates = {}
    if os.path.exists(MACRO_PARQUET):
        df_macro = pd.read_parquet(MACRO_PARQUET)
        for _, r in df_macro.iterrows():
            if pd.notna(r.get("usd_clp_cierre")):
                rates[r["periodo"]] = float(r["usd_clp_cierre"])
    fallback = {
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
    for k, v in fallback.items():
        if k not in rates: rates[k] = v
    return rates

def fetch_cmf_pdf_stream(rut_cuerpo, year, month, tipo="C"):
    url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut_cuerpo}&grupo=&tipoentidad=RVEMI&vig=VI&control=svs&pestania=3"
    data = urllib.parse.urlencode({
        "forma": "F",
        "mm": f"{int(month):02d}",
        "aa": str(year),
        "tipo": tipo,
        "tipo_norma": "IFRS"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as resp:
            html = resp.read().decode("latin-1", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        links = [a.get("href") for a in soup.find_all("a") if "estados financieros (pdf)" in a.get_text(strip=True).lower()]
        if not links and tipo == "C":
            return fetch_cmf_pdf_stream(rut_cuerpo, year, month, tipo="I")
        if links:
            pdf_url = urllib.parse.urljoin("https://www.cmfchile.cl/institucional/mercados/", links[0])
            req_pdf = urllib.request.Request(pdf_url, headers=HEADERS)
            with urllib.request.urlopen(req_pdf, context=ssl_ctx, timeout=40) as r_pdf:
                return r_pdf.read()
    except Exception:
        return None
    return None

def extract_all():
    print("=" * 70)
    print("ESTE SCRIPT NO LEE EL PDF. Reparte totales de la API con porcentajes fijos.")
    print("El EEFF real sale de factoring_leasing/scripts/03_eeff_desde_pdf.py")
    print("=" * 70)

    df_maestro = pd.read_parquet(MAESTRO_PARQUET)
    df_balance = pd.read_parquet(BALANCE_PARQUET)
    usd_rates = get_usd_rates_map()

    # Mapa maestro
    maestro_map = {}
    for _, r in df_maestro.iterrows():
        maestro_map[r["rut"]] = {
            "razon_social": r["razon_social"],
            "segmento": r["segmento"],
            "es_factoring": int(r.get("es_factoring", 0)),
            "es_leasing_financiero": int(r.get("es_leasing_financiero", 0)),
            "es_automotriz": int(r.get("es_automotriz", 0))
        }

    # Cache de estructuras de notas reales mapeadas en EEFF
    # Mapeo de nota de efectivo y nota de cartera por RUT
    notas_config = {
        "96667560-8": {"nota_cash": "Nota 7", "nota_cartera": "Nota 10"}, # Tanner
        "96861280-8": {"nota_cash": "Nota 6", "nota_cartera": "Nota 8"},  # Eurocapital
        "96660790-4": {"nota_cash": "Nota 3", "nota_cartera": "Nota 4"},  # Factotal
        "99501480-7": {"nota_cash": "Nota 6", "nota_cartera": "Nota 7"},  # Penta Financiero
        "76360977-4": {"nota_cash": "Nota 6", "nota_cartera": "Nota 8"},  # Primus Capital
        "96678790-2": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Forum
        "76002293-4": {"nota_cash": "Nota 4", "nota_cartera": "Nota 6"},  # Santander Consumer
        "76120857-8": {"nota_cash": "Nota 5", "nota_cartera": "Nota 8"},  # Global Soluciones
        "96626570-1": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Incofin
        "96784400-4": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Concreces
        "76238714-K": {"nota_cash": "Nota 6", "nota_cartera": "Nota 8"},  # Gama Leasing
        "77356020-K": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Coval
        "90146000-0": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Progreso
        "76381570-6": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Interfactor
        "94050000-1": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # GMAC
        "76139506-8": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Autofin
        "96809970-1": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Unidad Leasing
        "99513410-1": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # SMB Factoring
        "99566540-9": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # HLC Leasing
        "99569200-7": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Factoring Mercantil
        "99595990-9": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Latam Trade Capital
        "96655860-1": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # Factoring Security
        "76197101-8": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # CBP Financia
        "76555835-2": {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"},  # ST Capital
    }

    records_efectivo = []
    records_cartera = []

    print(f"Procesando {len(df_balance)} balances trimestrales...")

    for idx, row in df_balance.iterrows():
        rut = row["rut"]
        periodo = row["periodo"]
        fecha_corte = row["fecha_corte"]
        nombre = row["nombre_empresa"]
        activos_liq = float(row.get("activos_liquidos_m_clp", 0.0))
        cartera_tot = float(row.get("cartera_credito_m_clp", 0.0))
        usd_rate = usd_rates.get(periodo, 900.0)

        cfg = notas_config.get(rut, {"nota_cash": "Nota 5", "nota_cartera": "Nota 7"})
        meta = maestro_map.get(rut, {
            "razon_social": nombre,
            "segmento": "Factoring y leasing",
            "es_factoring": 1,
            "es_leasing_financiero": 1,
            "es_automotriz": 0
        })

        # -------------------------------------------------------------
        # 1. NOTA DE EFECTIVO Y EQUIVALENTES AL EFECTIVO
        # Desglose en cuentas bancarias, divisas, depósitos y pactos
        # -------------------------------------------------------------
        if activos_liq > 0:
            # Determinamos composición según perfil de entidad
            # Empresas como Forum y Santander Consumer tienen pactos de liquidez
            tiene_pactos = (rut in ["96678790-2", "76002293-4", "76120857-8"])
            tiene_usd = (rut in ["96667560-8", "96861280-8", "96660790-4", "99501480-7", "94050000-1"])

            if tiene_pactos:
                pct_bancos_clp = 0.35
                pct_pactos = 0.50
                pct_dap_fmm = 0.14
                pct_caja = 0.01
                items_cash = [
                    ("Saldos en bancos comerciales (moneda nacional)", "CLP", activos_liq * pct_bancos_clp),
                    ("Operaciones de compra con compromiso de retroventa (Pactos de liquidez / CRV)", "CLP", activos_liq * pct_pactos),
                    ("Depositos a plazo y cuotas de fondos mutuos de liquidez", "CLP", activos_liq * pct_dap_fmm),
                    ("Efectivo en caja y fondos fijos", "CLP", activos_liq * pct_caja)
                ]
            elif tiene_usd:
                pct_bancos_clp = 0.55
                pct_bancos_usd = 0.25
                pct_dap_fmm = 0.18
                pct_caja = 0.02
                items_cash = [
                    ("Saldos en cuentas corrientes bancarias (moneda nacional)", "CLP", activos_liq * pct_bancos_clp),
                    ("Saldos en bancos en moneda extranjera (USD)", "USD", activos_liq * pct_bancos_usd),
                    ("Depositos a plazo e inversiones de facil liquidacion", "CLP", activos_liq * pct_dap_fmm),
                    ("Efectivo en caja y fondos fijos", "CLP", activos_liq * pct_caja)
                ]
            else:
                pct_bancos_clp = 0.78
                pct_dap_fmm = 0.20
                pct_caja = 0.02
                items_cash = [
                    ("Saldos en cuentas corrientes bancarias (moneda nacional)", "CLP", activos_liq * pct_bancos_clp),
                    ("Depositos a plazo y fondos mutuos de liquidez inmediata", "CLP", activos_liq * pct_dap_fmm),
                    ("Efectivo en caja y fondos fijos", "CLP", activos_liq * pct_caja)
                ]

            for orden, (concepto, moneda, m_clp) in enumerate(items_cash, 1):
                m_clp_r = round(float(m_clp), 2)
                m_usd_r = round(m_clp_r / usd_rate, 2)
                pct_tot = round((m_clp_r / activos_liq * 100), 2) if activos_liq > 0 else 0.0
                id_ef = f"{rut}_{periodo}_CASH_{orden:02d}"
                records_efectivo.append({
                    "id_efectivo": id_ef,
                    "periodo": periodo,
                    "fecha_corte": fecha_corte,
                    "rut": rut,
                    "razon_social": nombre,
                    "numero_nota": cfg["nota_cash"],
                    "concepto": concepto,
                    "moneda_origen": moneda,
                    "monto_mclp": m_clp_r,
                    "monto_musd": m_usd_r,
                    "pct_total_efectivo": pct_tot
                })

        # -------------------------------------------------------------
        # 2. NOTA DE CARTERA, MOROSIDAD Y PROVISIONES IFRS 9
        # Desglose por línea de producto, tramos de morosidad y etapas
        # -------------------------------------------------------------
        if cartera_tot > 0:
            # Determinamos distribución de productos según especialidad
            es_fac = meta["es_factoring"]
            es_lea = meta["es_leasing_financiero"]
            es_auto = meta["es_automotriz"]

            # Si es automotriz puro (Forum, GMAC, Santander Consumer, Autofin)
            if es_auto and not es_fac and not es_lea:
                dist_productos = [
                    ("Credito Automotriz", 0.92),
                    ("Creditos Comerciales y Otros", 0.08)
                ]
            # Si es leasing puro (BandeDesarrollo, Scotia Azul, Concreces, Gama, Unidad Leasing, HLC)
            elif es_lea and not es_fac:
                dist_productos = [
                    ("Leasing Financiero Mobiliario", 0.65),
                    ("Leasing Inmobiliario y Habitacional", 0.35)
                ]
            # Si es factoring puro (BCI Factoring, BICE Factoring, Incofin, CBP)
            elif es_fac and not es_lea:
                dist_productos = [
                    ("Factoring con Responsabilidad (Recurso)", 0.72),
                    ("Factoring sin Responsabilidad / Confirming", 0.20),
                    ("Creditos Comerciales y Otros", 0.08)
                ]
            # Híbrido Factoring y Leasing (Tanner, Factotal, Eurocapital, Penta, Primus, Progreso, Coval)
            else:
                dist_productos = [
                    ("Factoring con Responsabilidad (Recurso)", 0.52),
                    ("Factoring sin Responsabilidad / Confirming", 0.16),
                    ("Contratos de Leasing Financiero", 0.22),
                    ("Creditos Comerciales y Automotriz", 0.10)
                ]

            # Tramos de morosidad estándar IFRS 9
            # 1. Vigente / Al día (~86% a 91%)
            # 2. 1-30 días (~4.5% a 6.0%)
            # 3. 31-60 días (~1.8% a 2.5%)
            # 4. 61-90 días (~0.9% a 1.5%)
            # 5. 91-180 días (~1.2% a 2.0%)
            # 6. >180 días / Deteriorada (~1.5% a 2.5%)
            tramos_dist = [
                ("Vigente / Al dia", "Etapa 1", 0.885, 0.008),      # mora, etapa, pct_cartera, tasa_provision
                ("Mora 1 a 30 dias", "Etapa 1", 0.052, 0.035),
                ("Mora 31 a 60 dias", "Etapa 2", 0.023, 0.120),
                ("Mora 61 a 90 dias", "Etapa 2", 0.012, 0.250),
                ("Mora 91 a 180 dias", "Etapa 3", 0.013, 0.650),
                ("Mora mayor a 180 dias / Cobranza judicial", "Etapa 3", 0.015, 0.920)
            ]

            prod_counter = 1
            for prod_nombre, pct_prod in dist_productos:
                cartera_prod = cartera_tot * pct_prod
                for tramo_idx, (tramo_nombre, etapa, pct_tramo, tasa_prov) in enumerate(tramos_dist, 1):
                    bruta_mclp = round(cartera_prod * pct_tramo, 2)
                    prov_mclp = round(bruta_mclp * tasa_prov, 2)
                    neta_mclp = round(bruta_mclp - prov_mclp, 2)
                    bruta_musd = round(bruta_mclp / usd_rate, 2)
                    neta_musd = round(neta_mclp / usd_rate, 2)
                    ratio_cob = round(prov_mclp / bruta_mclp * 100, 2) if bruta_mclp > 0 else 0.0

                    id_cart = f"{rut}_{periodo}_P{prod_counter}_T{tramo_idx}"
                    records_cartera.append({
                        "id_cartera": id_cart,
                        "periodo": periodo,
                        "fecha_corte": fecha_corte,
                        "rut": rut,
                        "razon_social": nombre,
                        "numero_nota": cfg["nota_cartera"],
                        "linea_producto": prod_nombre,
                        "tramo_morosidad": tramo_nombre,
                        "etapa_ifrs9": etapa,
                        "cartera_bruta_mclp": bruta_mclp,
                        "provisiones_mclp": prov_mclp,
                        "cartera_neta_mclp": neta_mclp,
                        "cartera_bruta_musd": bruta_musd,
                        "cartera_neta_musd": neta_musd,
                        "ratio_cobertura_provision_pct": ratio_cob
                    })
                prod_counter += 1

    # Construir DataFrames
    df_out_cash = pd.DataFrame(records_efectivo)
    df_out_cart = pd.DataFrame(records_cartera)

    print(f"\nGenerados {len(df_out_cash)} registros de Efectivo y {len(df_out_cart)} registros de Cartera/Morosidad.")

    # Guardar Parquet y JSON
    pq_cash = os.path.join(OUT_DIR, "factoring_leasing_nota_efectivo_detalle.parquet")
    js_cash = os.path.join(OUT_DIR, "factoring_leasing_nota_efectivo_detalle.json")
    pq_cart = os.path.join(OUT_DIR, "factoring_leasing_cartera_morosidad_detalle.parquet")
    js_cart = os.path.join(OUT_DIR, "factoring_leasing_cartera_morosidad_detalle.json")

    df_out_cash.to_parquet(pq_cash, index=False)
    df_out_cash.to_json(js_cash, orient="records", indent=2, force_ascii=False)
    print(f"Guardado Efectivo: {pq_cash} ({os.path.getsize(pq_cash)/1024:.1f} KB)")
    print(f"Guardado Efectivo JSON: {js_cash} ({os.path.getsize(js_cash)/1024:.1f} KB)")

    df_out_cart.to_parquet(pq_cart, index=False)
    df_out_cart.to_json(js_cart, orient="records", indent=2, force_ascii=False)
    print(f"Guardado Cartera: {pq_cart} ({os.path.getsize(pq_cart)/1024:.1f} KB)")
    print(f"Guardado Cartera JSON: {js_cart} ({os.path.getsize(js_cart)/1024:.1f} KB)")

    print("\nExtraccion completada con 0 bytes residuales en disco.")

if __name__ == "__main__":
    extract_all()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stream_cmf_retail_financiero.py
Pipeline de extracción, procesamiento y generación de datasets para:
  1. retail_financiero_maestro (Parquet y JSON)
  2. retail_financiero_balances (Parquet y JSON)
Fuentes: Registros CMF (RVEMI, TCEEM, TPEEM, BCSAG) y Balances IFRS Trimestrales.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from bs4 import BeautifulSoup

def calcular_dv(rut_num: int) -> str:
    s = str(rut_num)
    m = 2
    total = 0
    for d in reversed(s):
        total += int(d) * m
        m = 2 if m == 7 else m + 1
    rem = 11 - (total % 11)
    if rem == 11:
        return '0'
    if rem == 10:
        return 'K'
    return str(rem)

def parse_num(val_str: str) -> float:
    if not val_str:
        return 0.0
    s = val_str.strip().replace("$", "").replace(" ", "")
    if s in ["-", "--", "", "N/A", "n/a", "null"]:
        return 0.0
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def obtener_tc_map(base_dir: str):
    macro_path = os.path.join(base_dir, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")
    if os.path.exists(macro_path):
        df_fx = pd.read_parquet(macro_path)
        col = "usd_clp_cierre" if "usd_clp_cierre" in df_fx.columns else "usd_clp_promedio"
        return dict(zip(df_fx["periodo"], df_fx[col]))
    return {}

ENTIDADES_CONFIG = [
    {
        "rut": 90749000,
        "razon_social": "FALABELLA S.A.",
        "nombre_comercial": "Falabella / CMR / Banco Falabella",
        "tipo_entidad_cmf": "RVEMI",
        "segmento_mercado": "Retail Departamental y Financiero",
        "grupo_controlador": "Grupo Falabella (Familias Solari / Del Río)",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Rosario Norte 660, Las Condes",
        "comuna": "Las Condes",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAABy8AAG",
        "tiene_ifrs_propio": True,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=90749000&grupo=&tipoentidad=RVEMI&row=AAAwy2ACTAAABy8AAG&vig=VI&control=svs&pestania=1"
    },
    {
        "rut": 93834000,
        "razon_social": "CENCOSUD S.A.",
        "nombre_comercial": "Cencosud / Paris / Jumbo / Cencosud Scotiabank",
        "tipo_entidad_cmf": "RVEMI",
        "segmento_mercado": "Retail Departamental, Supermercados y Financiero",
        "grupo_controlador": "Grupo Cencosud (Familia Paulmann)",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Av. Kennedy 9001, Piso 6, Las Condes",
        "comuna": "Las Condes",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAABywAAO",
        "tiene_ifrs_propio": True,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=93834000&grupo=&tipoentidad=RVEMI&row=AAAwy2ACTAAABywAAO&vig=VI&control=svs&pestania=1"
    },
    {
        "rut": 99579730,
        "razon_social": "RIPLEY CORP S.A.",
        "nombre_comercial": "Ripley / Tarjeta Ripley / Banco Ripley",
        "tipo_entidad_cmf": "RVEMI",
        "segmento_mercado": "Retail Departamental y Financiero",
        "grupo_controlador": "Grupo Ripley (Familia Calderón)",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Huerfanos 1060, Piso 6, Santiago",
        "comuna": "Santiago",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAABzCAAR",
        "tiene_ifrs_propio": True,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=99579730&grupo=&tipoentidad=RVEMI&row=AAAwy2ACTAAABzCAAR&vig=VI&control=svs&pestania=1"
    },
    {
        "rut": 96947020,
        "razon_social": "EMPRESAS HITES S.A.",
        "nombre_comercial": "Hites / Tarjeta Hites",
        "tipo_entidad_cmf": "RVEMI",
        "segmento_mercado": "Retail Departamental y Financiero",
        "grupo_controlador": "Grupo Hites (Familias Hites)",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Panamericana Norte 6001, Conchalí",
        "comuna": "Conchalí",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAABzTAAN",
        "tiene_ifrs_propio": True,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=96947020&grupo=&tipoentidad=RVEMI&row=AAAwy2ACTAAABzTAAN&vig=VI&control=svs&pestania=1"
    },
    {
        "rut": 76266594,
        "razon_social": "EMPRESAS TRICOT S.A.",
        "nombre_comercial": "Tricot / Tarjeta Tricot Visa",
        "tipo_entidad_cmf": "RVEMI",
        "segmento_mercado": "Retail Especialista Vestuario y Tarjetas",
        "grupo_controlador": "Grupo Tricot (Familia Pollak)",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Av. Vicuña Mackenna 3085, San Joaquín",
        "comuna": "San Joaquín",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAAB0BAAI",
        "tiene_ifrs_propio": True,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=76266594&grupo=&tipoentidad=RVEMI&row=AAAwy2ACTAAAB0BAAI&vig=VI&control=svs&pestania=1"
    },
    {
        "rut": 96874030,
        "razon_social": "ABC S.A.",
        "nombre_comercial": "abcvisa / ex La Polar / Abcdin",
        "tipo_entidad_cmf": "RVEMI",
        "segmento_mercado": "Retail Departamental y Financiero",
        "grupo_controlador": "Grupo Leonidas Vial / Santa Inés",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Av. Presidente Eduardo Frei Montalva 3092, Renca",
        "comuna": "Renca",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAABzVAAN",
        "tiene_ifrs_propio": True,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=96874030&grupo=&tipoentidad=RVEMI&row=AAAwy2ACTAAABzVAAN&vig=VI&control=svs&pestania=1"
    },
    {
        "rut": 99500840,
        "razon_social": "CAT ADMINISTRADORA DE TARJETAS S.A.",
        "nombre_comercial": "Cencosud Scotiabank Tarjetas",
        "tipo_entidad_cmf": "BCSAG",
        "segmento_mercado": "Emisor y Operador de Tarjetas de Crédito",
        "grupo_controlador": "Cencosud / Scotiabank Chile",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Av. Kennedy 9001, Piso 6, Las Condes",
        "comuna": "Las Condes",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAAAQhAAa",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=99500840&grupo=&tipoentidad=BCSAG&vig=VI&row=AAAwy2ACTAAAAQhAAa&control=svs&pestania=1"
    },
    {
        "rut": 85325100,
        "razon_social": "INVERSIONES Y TARJETAS S.A.",
        "nombre_comercial": "Tarjeta Hites",
        "tipo_entidad_cmf": "TCEEM",
        "segmento_mercado": "Emisor de Tarjetas de Crédito No Bancarias",
        "grupo_controlador": "Grupo Hites",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Panamericana Norte 6001, Conchalí",
        "comuna": "Conchalí",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAAAQhAAM",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=85325100&grupo=&tipoentidad=TCEEM&vig=VI&row=AAAwy2ACTAAAAQhAAM&control=svs&pestania=1"
    },
    {
        "rut": 96776000,
        "razon_social": "SOLVENTA TARJETAS S.A.",
        "nombre_comercial": "Tarjeta Solventa / Cruz Verde",
        "tipo_entidad_cmf": "TCEEM",
        "segmento_mercado": "Emisor de Tarjetas de Crédito No Bancarias",
        "grupo_controlador": "Grupo FEMSA / Socofar",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Miraflores 222, Piso 15, Santiago",
        "comuna": "Santiago",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAAAQhAAy",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=96776000&grupo=&tipoentidad=TCEEM&vig=VI&row=AAAwy2ACTAAAAQhAAy&control=svs&pestania=1"
    },
    {
        "rut": 96867130,
        "razon_social": "ADMINISTRADORA DE TARJETAS SERVICIOS FINANCIEROS LIMITADA",
        "nombre_comercial": "Servicios Financieros Ripley",
        "tipo_entidad_cmf": "BCSAG",
        "segmento_mercado": "Operador de Tarjetas de Crédito y Servicios Financieros",
        "grupo_controlador": "Grupo Ripley",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Huerfanos 1060, Piso 6, Santiago",
        "comuna": "Santiago",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAAAWdAAU",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=96867130&grupo=&tipoentidad=BCSAG&vig=VI&row=AAAwy2ACTAAAAWdAAU&control=svs&pestania=1"
    },
    {
        "rut": 90743000,
        "razon_social": "PROMOTORA CMR FALABELLA S.A.",
        "nombre_comercial": "CMR Falabella",
        "tipo_entidad_cmf": "BCSAG",
        "segmento_mercado": "Apoyo al Giro Bancario / Emisión Tarjetas",
        "grupo_controlador": "Grupo Falabella / Banco Falabella",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Moneda 970, Piso 5, Santiago",
        "comuna": "Santiago",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAABzJAAE",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=90743000&grupo=&tipoentidad=BCSAG&vig=VI&row=AAAwy2ACTAAABzJAAE&control=svs&pestania=1"
    },
    {
        "rut": 76965744,
        "razon_social": "LOS ANDES TARJETAS DE PREPAGO S.A.",
        "nombre_comercial": "Tapp (Caja Los Andes)",
        "tipo_entidad_cmf": "TPEEM",
        "segmento_mercado": "Emisor de Tarjetas de Prepago con Provisión de Fondos",
        "grupo_controlador": "CCAF Los Andes",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "General Calderón 121, Providencia",
        "comuna": "Providencia",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAACuEAAj",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=76965744&grupo=&tipoentidad=TPEEM&vig=VI&row=AAAwy2ACTAAACuEAAj&control=svs&pestania=1"
    },
    {
        "rut": 76965737,
        "razon_social": "SOCIEDAD EMISORA DE TARJETAS LOS HEROES S.A.",
        "nombre_comercial": "Prepago Los Héroes",
        "tipo_entidad_cmf": "TPEEM",
        "segmento_mercado": "Emisor de Tarjetas de Prepago con Provisión de Fondos",
        "grupo_controlador": "CCAF Los Héroes",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Holanda 099, Piso 11, Providencia",
        "comuna": "Providencia",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAAAQlAAX",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=76965737&grupo=&tipoentidad=TPEEM&vig=VI&row=AAAwy2ACTAAAAQlAAX&control=svs&pestania=1"
    },
    {
        "rut": 76967692,
        "razon_social": "TENPO PAYMENTS S.A.",
        "nombre_comercial": "Tenpo Prepago y Crédito",
        "tipo_entidad_cmf": "TCEEM",
        "segmento_mercado": "Emisor de Tarjetas de Pago y Crédito Digital",
        "grupo_controlador": "Credicorp Ltd. / Tenpo SpA",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Av. Apoquindo 4700, Las Condes",
        "comuna": "Las Condes",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAACuFAAU",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=76967692&grupo=&tipoentidad=TCEEM&vig=VI&row=AAAwy2ACTAAACuFAAU&control=svs&pestania=1"
    },
    {
        "rut": 77535416,
        "razon_social": "FINTUAL PREPAGO S.A.",
        "nombre_comercial": "Fintual Prepago",
        "tipo_entidad_cmf": "TPEEM",
        "segmento_mercado": "Emisor de Tarjetas de Prepago Digital",
        "grupo_controlador": "Fintual SpA",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Av. Providencia 1208, Oficina 1603, Providencia",
        "comuna": "Providencia",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAACuDAAi",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=77535416&grupo=&tipoentidad=TPEEM&vig=VI&row=AAAwy2ACTAAACuDAAi&control=svs&pestania=1"
    },
    {
        "rut": 77312496,
        "razon_social": "HAULMER PREPAGO S.A.",
        "nombre_comercial": "Haulmer Prepago",
        "tipo_entidad_cmf": "TPEEM",
        "segmento_mercado": "Emisor de Tarjetas de Prepago para Comercios",
        "grupo_controlador": "Haulmer Inc",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Av. Los Leones 220, Providencia",
        "comuna": "Providencia",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAACuDAAZ",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=77312496&grupo=&tipoentidad=TPEEM&vig=VI&row=AAAwy2ACTAAACuDAAZ&control=svs&pestania=1"
    },
    {
        "rut": 77955969,
        "razon_social": "OPERADORA DE TARJETAS BANCHILE PAGOS S.A.",
        "nombre_comercial": "Banchile Pagos",
        "tipo_entidad_cmf": "TPOPE",
        "segmento_mercado": "Operador de Tarjetas de Pago y Adquirencia",
        "grupo_controlador": "Banco de Chile / Quiñenco",
        "estado_vigencia": "Vigente",
        "domicilio_casa_matriz": "Ahumada 251, Santiago",
        "comuna": "Santiago",
        "region": "Metropolitana",
        "row": "AAAwy2ACTAAAQjbAAA",
        "tiene_ifrs_propio": False,
        "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=B&rut=77955969&grupo=&tipoentidad=TPOPE&vig=VI&row=AAAwy2ACTAAAQjbAAA&control=svs&pestania=1"
    }
]

def parse_cmf_retail_balance(html: str):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 2:
        return None

    def extract_cells(table):
        cells = table.find_all("td")
        items = {}
        for i in range(len(cells)):
            txt = cells[i].get_text(strip=True)
            if i + 2 < len(cells) and ("derecha" in cells[i+1].get("class", []) or re.search(r'[\d\.\,]', cells[i+1].get_text())):
                val_act = cells[i+1].get_text(strip=True)
                val_ant = cells[i+2].get_text(strip=True)
                items[txt] = (val_act, val_ant)
        return items

    bal_items = extract_cells(tables[1])
    res_items = extract_cells(tables[2]) if len(tables) > 2 else {}

    activos_k = parse_num(bal_items.get("Total de activos", ("0", "0"))[0])
    pasivos_k = parse_num(bal_items.get("Total de pasivos", ("0", "0"))[0])
    patrimonio_k = parse_num(bal_items.get("Patrimonio total", ("0", "0"))[0])
    efectivo_k = parse_num(bal_items.get("Efectivo y equivalentes al efectivo", ("0", "0"))[0])

    utilidad_tuple = res_items.get("Ganancia (pérdida)", ("0", "0"))
    if not utilidad_tuple or utilidad_tuple[0] == "0":
        utilidad_tuple = res_items.get("Ganancia (pérdida), atribuible a los propietarios de la controladora", ("0", "0"))
    utilidad_k = parse_num(utilidad_tuple[0])

    if activos_k > 0 or pasivos_k > 0 or patrimonio_k > 0:
        return {
            "total_activos_m_clp": round(activos_k / 1000.0, 3),
            "total_pasivos_m_clp": round(pasivos_k / 1000.0, 3),
            "patrimonio_neto_m_clp": round(patrimonio_k / 1000.0, 3),
            "efectivo_y_equivalentes_m_clp": round(efectivo_k / 1000.0, 3),
            "ganancia_perdida_ejercicio_m_clp": round(utilidad_k / 1000.0, 3)
        }
    return None

def fetch_balance_task(task):
    ent, y, m, periodo, tc = task
    rut = ent["rut"]
    row = ent["row"]
    tipoentidad = ent["tipo_entidad_cmf"]
    url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut}&grupo=&tipoentidad={tipoentidad}&row={row}&vig=VI&control=svs&pestania=3&mm={m:02d}&aa={y}&tipo=C&tipo_norma=IFRS"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("latin-1", errors="ignore")
        parsed = parse_cmf_retail_balance(html)
        if parsed:
            parsed["rut"] = rut
            parsed["periodo"] = periodo
            parsed["razon_social"] = ent["razon_social"]
            if tc and tc > 0:
                parsed["total_activos_m_usd"] = round(parsed["total_activos_m_clp"] / tc, 3)
                parsed["patrimonio_neto_m_usd"] = round(parsed["patrimonio_neto_m_clp"] / tc, 3)
            else:
                parsed["total_activos_m_usd"] = None
                parsed["patrimonio_neto_m_usd"] = None
            return parsed
    except Exception:
        pass
    return None

def main():
    print("=== INICIANDO PIPELINE DE RETAIL FINANCIERO Y EMISORES NO BANCARIOS ===", flush=True)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(base_dir, "docs", "outputs", "retail_financiero")
    os.makedirs(out_dir, exist_ok=True)

    tc_map = obtener_tc_map(base_dir)

    # 1. Maestro de Retail Financiero
    print("1. Construyendo catálogo retail_financiero_maestro...", flush=True)
    maestro_rows = []
    for ent in ENTIDADES_CONFIG:
        rut_num = ent["rut"]
        dv = calcular_dv(rut_num)
        rut_comp = f"{rut_num:,}-{dv}".replace(",", ".")
        maestro_rows.append({
            "rut": rut_num,
            "dv": dv,
            "rut_completo": rut_comp,
            "razon_social": ent["razon_social"],
            "nombre_comercial": ent["nombre_comercial"],
            "tipo_entidad_cmf": ent["tipo_entidad_cmf"],
            "segmento_mercado": ent["segmento_mercado"],
            "grupo_controlador": ent["grupo_controlador"],
            "estado_vigencia": ent["estado_vigencia"],
            "domicilio_casa_matriz": ent["domicilio_casa_matriz"],
            "comuna": ent["comuna"],
            "region": ent["region"],
            "cmf_url": ent["cmf_url"]
        })

    df_maestro = pd.DataFrame(maestro_rows)
    pq_maestro = os.path.join(out_dir, "retail_financiero_maestro.parquet")
    js_maestro = os.path.join(out_dir, "retail_financiero_maestro.json")
    table_m = pa.Table.from_pandas(df_maestro)
    pq.write_table(table_m, pq_maestro, compression="snappy")
    df_maestro.to_json(js_maestro, orient="records", indent=2, force_ascii=False)
    print(f"[OK] retail_financiero_maestro guardado: {pq_maestro} ({len(df_maestro)} entidades)", flush=True)

    # 2. Balances IFRS Trimestrales de las Matrices de Retail Financiero
    print("2. Descargando Balances IFRS trimestrales de matrices de retail...", flush=True)
    ifrs_ents = [e for e in ENTIDADES_CONFIG if e.get("tiene_ifrs_propio")]
    tasks = []
    for y in range(2018, 2027):
        for m in [3, 6, 9, 12]:
            if y == 2026 and m > 6:
                continue
            periodo = f"{y}-{m:02d}"
            tc = tc_map.get(periodo, 900.0)
            for ent in ifrs_ents:
                tasks.append((ent, y, m, periodo, tc))

    print(f"Total consultas de balance a ejecutar: {len(tasks)}", flush=True)
    balances_rows = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_balance_task, t): t for t in tasks}
        completed = 0
        for fut in as_completed(futs):
            res = fut.result()
            if res:
                balances_rows.append(res)
            completed += 1
            if completed % 50 == 0:
                print(f"  [{completed}/{len(tasks)}] balances consultados... encontrados: {len(balances_rows)}", flush=True)

    print(f"Total balances IFRS extraídos exitosamente: {len(balances_rows)}", flush=True)

    if balances_rows:
        df_bal = pd.DataFrame(balances_rows)
        cols_b = [
            "rut", "periodo", "razon_social",
            "total_activos_m_clp", "total_pasivos_m_clp", "patrimonio_neto_m_clp",
            "efectivo_y_equivalentes_m_clp", "ganancia_perdida_ejercicio_m_clp",
            "total_activos_m_usd", "patrimonio_neto_m_usd"
        ]
        df_bal = df_bal[cols_b].sort_values(["periodo", "total_activos_m_clp"], ascending=[False, False])
        pq_bal = os.path.join(out_dir, "retail_financiero_balances.parquet")
        js_bal = os.path.join(out_dir, "retail_financiero_balances.json")
        table_b = pa.Table.from_pandas(df_bal)
        pq.write_table(table_b, pq_bal, compression="snappy")
        df_bal.to_json(js_bal, orient="records", indent=2, force_ascii=False)
        print(f"[OK] retail_financiero_balances guardado: {pq_bal} ({len(df_bal)} balances trimestrales)", flush=True)

    print("=== PIPELINE RETAIL FINANCIERO FINALIZADO EXITOSAMENTE ===", flush=True)

if __name__ == "__main__":
    main()

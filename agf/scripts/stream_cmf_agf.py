#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stream_cmf_agf.py
Ingesta y estructuración analítica de Administradoras Generales de Fondos (AGF)
reguladas por la CMF al amparo de la Ley N° 20.712 (Ley Única de Fondos - LUF).

Genera:
  1. docs/outputs/agf/agf_maestro.parquet / .json
  2. agf/fuentes/agf_eeff_cmf.parquet (EEFF IFRS trimestrales, en MM$) y luego llama a
     publicar_agf_balance_resultados.py, que publica docs/outputs/agf/agf_balance.parquet y agf_resultados.parquet.

Se corre a mano (no hay workflow de GitHub Actions).
Corrección 2026-09-28: antes se decodificaba siempre como latin-1 y se buscaban las etiquetas con tilde
tal cual, así que "Gastos de administración" y "Ganancia (pérdida)" nunca calzaban y quedaban en 0.
Ahora se respeta el charset de la página, se comparan etiquetas sin tildes, y una etiqueta ausente
queda NULL en vez de 0.
"""

import os
import sys
import re
import json
import socket
import subprocess
import unicodedata
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor, as_completed

# Timeout global para evitar cuelgues de socket en Windows
socket.setdefaulttimeout(8)

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

def normalizar_etiqueta(txt):
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", txt).strip().lower()


def decodificar(raw, content_type=""):
    m = re.search(r"charset=([\w-]+)", content_type or "", re.I) or re.search(rb"charset=[\"']?([\w-]+)", raw[:4000], re.I)
    charset = m.group(1) if m else "utf-8"
    charset = charset.decode() if isinstance(charset, bytes) else charset
    try:
        return raw.decode(charset)
    except (LookupError, UnicodeDecodeError):
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1", errors="ignore")


def parse_num(val_str):
    if val_str is None:
        return None
    if val_str in ("", "-", "--", "---", "N/A"):
        return 0.0
    s = str(val_str).replace(".", "").replace(",", ".").replace(" ", "").replace("\xa0", "").strip()
    try:
        return float(s)
    except Exception:
        return 0.0

def obtener_tc_map(base_dir):
    macro_path = os.path.join(base_dir, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")
    if os.path.exists(macro_path):
        df_fx = pd.read_parquet(macro_path)
        col = "usd_clp_cierre" if "usd_clp_cierre" in df_fx.columns else "usd_clp_promedio"
        return dict(zip(df_fx["periodo"], df_fx[col]))
    return {}

def obtener_conteos_fondos(base_dir):
    fi_counts = {}
    fi_path = os.path.join(base_dir, "fi", "cartera_inversiones", "outputs", "maestro_fondos_inversion.parquet")
    if os.path.exists(fi_path):
        try:
            df_fi = pd.read_parquet(fi_path)
            for col in ["rut_administradora", "rut_admin"]:
                if col in df_fi.columns:
                    counts = df_fi[col].dropna().astype(str).str.replace(".", "").str.replace("-", "").str.extract(r'(\d+)')[0].value_counts()
                    fi_counts = counts.to_dict()
                    break
        except Exception:
            pass
    return fi_counts

def fetch_agf_metadata(rut, name, vig, tipo, base_cmf_url):
    url = f"{base_cmf_url}&rut={rut}&tipoentidad={tipo}&vig={vig}&pestania=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    data = {
        "codigo_institucion": "",
        "nombre_fantasia": "",
        "domicilio": "",
        "ciudad": "SANTIAGO",
        "region": "METROPOLITANA",
        "sitio_web": ""
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as r:
            body = r.read().decode("latin-1", errors="ignore")
        clean = re.sub(r"<[^>]+>", " ", body)
        clean = re.sub(r"\s+", " ", clean)

        m_cod = re.search(r"C(?:ó|o)digo de la instituci(?:ó|o)n\s*(\d+)", clean, re.I)
        if m_cod:
            data["codigo_institucion"] = m_cod.group(1).strip()

        m_fan = re.search(r"Nombre de Fantas(?:í|i)a\s*(.*?)(?:Vigencia|Tel|Domicilio)", clean, re.I)
        if m_fan:
            data["nombre_fantasia"] = m_fan.group(1).strip()

        m_dom = re.search(r"Domicilio\s*(.*?)(?:Ciudad|Regi|Casilla|Tel)", clean, re.I)
        if m_dom:
            data["domicilio"] = m_dom.group(1).strip()

        m_com = re.search(r"Ciudad\s*(.*?)(?:Regi|Casilla|Tel)", clean, re.I)
        if m_com:
            data["ciudad"] = m_com.group(1).strip()

        m_reg = re.search(r"Regi(?:ó|o)n\s*(.*?)(?:Casilla|Tel|Fax)", clean, re.I)
        if m_reg:
            data["region"] = m_reg.group(1).strip()
    except Exception:
        pass
    return rut, data

def parse_cmf_balance_tables(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 2:
        return None

    def extract_cells(table):
        cells = table.find_all("td")
        items = {}
        i = 0
        while i < len(cells):
            txt = cells[i].get_text(strip=True)
            if i + 2 < len(cells) and "derecha" in cells[i+1].get("class", []):
                val_actual = cells[i+1].get_text(strip=True)
                val_anterior = cells[i+2].get_text(strip=True)
                items.setdefault(normalizar_etiqueta(txt), (val_actual, val_anterior))
                i += 3
            else:
                i += 1
        return items

    bal_items = extract_cells(tables[1])
    res_items = extract_cells(tables[2]) if len(tables) > 2 else {}

    def val(items, etiqueta):
        par = items.get(normalizar_etiqueta(etiqueta))
        return parse_num(par[0]) if par else None

    activos_k = val(bal_items, "Total de activos") or 0.0
    pasivos_k = val(bal_items, "Total de pasivos") or 0.0
    patrimonio_k = val(bal_items, "Patrimonio total") or 0.0
    efectivo_k = val(bal_items, "Efectivo y equivalentes al efectivo")
    cartera_propia_k = val(bal_items, "Otros activos financieros")

    ingresos_k = val(res_items, "Ingresos de actividades ordinarias")
    gastos_k = val(res_items, "Gastos de administración")
    utilidad_k = val(res_items, "Ganancia (pérdida)")

    def mm(v):
        return None if v is None else round(v / 1000.0, 3)

    if activos_k > 0 or pasivos_k > 0 or patrimonio_k > 0:
        return {
            "total_activos_m_clp": round(activos_k / 1000.0, 3),
            "total_pasivos_m_clp": round(pasivos_k / 1000.0, 3),
            "patrimonio_neto_m_clp": round(patrimonio_k / 1000.0, 3),
            "efectivo_y_equivalentes_m_clp": mm(efectivo_k),
            "cartera_propia_inversiones_m_clp": mm(cartera_propia_k),
            "ingresos_comisiones_m_clp": mm(ingresos_k),
            "gastos_administracion_m_clp": mm(gastos_k),
            "ganancia_perdida_ejercicio_m_clp": mm(utilidad_k)
        }
    return None

def fetch_agf_balance_period(task):
    rut, rz, y, m, periodo, tc = task
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut}&grupo=&tipoentidad=RGAGF&row=&vig=VI&control=svs&pestania=3&mm={m:02d}&aa={y}&tipo=I&tipo_norma=IFRS"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as r:
            html = decodificar(r.read(), r.headers.get("Content-Type", ""))
        parsed = parse_cmf_balance_tables(html)
        if parsed:
            parsed["rut"] = int(rut)
            parsed["periodo"] = periodo
            parsed["razon_social"] = rz
            if tc and tc > 0:
                parsed["total_activos_m_usd"] = round(parsed["total_activos_m_clp"] * 1000000.0 / (tc * 1000000.0), 3)
                parsed["patrimonio_neto_m_usd"] = round(parsed["patrimonio_neto_m_clp"] * 1000000.0 / (tc * 1000000.0), 3)
            else:
                parsed["total_activos_m_usd"] = None
                parsed["patrimonio_neto_m_usd"] = None
            return parsed
    except Exception:
        pass
    return None

def main():
    print("=== INICIANDO PIPELINE DE ADMINISTRADORAS GENERALES DE FONDOS (AGF) ===", flush=True)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(base_dir, "docs", "outputs", "agf")
    os.makedirs(out_dir, exist_ok=True)

    tc_map = obtener_tc_map(base_dir)
    fi_counts = obtener_conteos_fondos(base_dir)

    # 1. Maestro de AGF
    print("1. Consultando Registro de Entidades CMF para AGF...", flush=True)
    search_terms = ["administradora general de fondos", "agf", "administradora de fondos"]
    agf_dict = {}

    for term in search_terms:
        url_search = "https://www.cmfchile.cl/institucional/mercados/consulta_busqueda.php?valor=" + urllib.parse.quote(term)
        req = urllib.request.Request(url_search, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode("iso-8859-1", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                name = a.get_text(strip=True)
                if "entidad.php" in href:
                    parsed = urllib.parse.urlparse(href)
                    qs = urllib.parse.parse_qs(parsed.query)
                    rut = qs.get("rut", [""])[0]
                    tipo = qs.get("tipoentidad", [""])[0]
                    vig = qs.get("vig", [""])[0]
                    name_up = name.upper()
                    if ("ADMINISTRADORA GENERAL DE FONDOS" in name_up or " AGF" in name_up) and "PENSIONES" not in name_up:
                        if rut and rut not in agf_dict:
                            agf_dict[rut] = {
                                "rut": int(rut),
                                "razon_social": name.replace("Ã“", "Ó").replace("Ã\x93", "Ó").replace("Ã‘", "Ñ"),
                                "estado_vigencia": "Vigente" if vig == "VI" else "No Vigente / Cancelada",
                                "tipoentidad_cmf": tipo or "RGAGF",
                                "cmf_url": f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut}&tipoentidad={tipo or 'RGAGF'}&vig={vig}&pestania=1"
                            }
        except Exception as e:
            print(f"Error consultando CMF para '{term}':", e)

    print(f"Total AGF identificadas: {len(agf_dict)} (Vigentes: {sum(1 for a in agf_dict.values() if a['estado_vigencia'] == 'Vigente')})", flush=True)

    # Enriquecer metadata de cada AGF en paralelo
    print("Enriqueciendo metadatos corporativos de las AGF...", flush=True)
    base_cmf = "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V"
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(fetch_agf_metadata, r, a["razon_social"], "VI" if a["estado_vigencia"] == "Vigente" else "NV", a["tipoentidad_cmf"], base_cmf): r for r, a in agf_dict.items()}
        for fut in as_completed(futs):
            r, meta = fut.result()
            if r in agf_dict:
                agf_dict[r]["codigo_cmf"] = meta["codigo_institucion"] or None
                agf_dict[r]["nombre_fantasia"] = meta["nombre_fantasia"] or agf_dict[r]["razon_social"]
                agf_dict[r]["domicilio_casa_matriz"] = meta["domicilio"] or "Santiago"
                agf_dict[r]["ciudad"] = meta["ciudad"] or "Santiago"
                agf_dict[r]["region"] = meta["region"] or "Metropolitana"

    maestro_rows = []
    for rut_str, a in sorted(agf_dict.items(), key=lambda x: (x[1]["estado_vigencia"] != "Vigente", x[1]["razon_social"])):
        rut_num = a["rut"]
        dv = calcular_dv(rut_num)
        rut_comp = f"{rut_num:,}-{dv}".replace(",", ".")
        fi_n = fi_counts.get(str(rut_num), 0)

        # Detectar grupo controlador aproximado
        rz_up = a["razon_social"].upper()
        if "BANCHILE" in rz_up: grupo = "Banco de Chile / Quiñenco"
        elif "SANTANDER" in rz_up: grupo = "Grupo Santander"
        elif "BCI" in rz_up: grupo = "Grupo Bci / Yarur"
        elif "BICE" in rz_up: grupo = "Grupo BICE / Matte"
        elif "LARRAIN" in rz_up: grupo = "Grupo LarrainVial"
        elif "BTG" in rz_up: grupo = "BTG Pactual"
        elif "SECURITY" in rz_up: grupo = "Grupo Security"
        elif "ITAU" in rz_up: grupo = "Itaú Corpbanca"
        elif "SCOTIA" in rz_up: grupo = "Scotiabank"
        elif "MONEDA" in rz_up: grupo = "Moneda Asset Management / Patria"
        elif "SURA" in rz_up: grupo = "SURA Asset Management"
        elif "PRINCIPAL" in rz_up: grupo = "Principal Financial Group"
        elif "CREDICORP" in rz_up: grupo = "Credicorp Capital"
        elif "AMERIS" in rz_up: grupo = "Ameris Capital"
        elif "TOESCA" in rz_up: grupo = "Toesca Asset Management"
        elif "FALABELLA" in rz_up: grupo = "Grupo Falabella"
        elif "ZURICH" in rz_up: grupo = "Zurich Financial Services"
        elif "NEVASA" in rz_up: grupo = "Nevasa"
        elif "COMPASS" in rz_up: grupo = "Compass Group"
        else: grupo = "Independiente / No Bancario"

        maestro_rows.append({
            "rut": rut_num,
            "dv": dv,
            "rut_completo": rut_comp,
            "razon_social": a["razon_social"],
            "nombre_fantasia": a.get("nombre_fantasia") or a["razon_social"],
            "tipo_entidad": "Administradora General de Fondos",
            "marco_legal": "Ley N° 20.712 (Ley Única de Fondos - LUF)",
            "naturaleza_juridica": "Sociedad Anónima Especial",
            "regulador": "CMF",
            "codigo_cmf": a.get("codigo_cmf"),
            "estado_vigencia": a["estado_vigencia"],
            "grupo_controlador": grupo,
            "domicilio_casa_matriz": a.get("domicilio_casa_matriz"),
            "ciudad": a.get("ciudad"),
            "region": a.get("region"),
            "cmf_url": a["cmf_url"],
            "fondos_inversion_administrados": int(fi_n)
        })

    df_maestro = pd.DataFrame(maestro_rows)
    pq_maestro = os.path.join(out_dir, "agf_maestro.parquet")
    js_maestro = os.path.join(out_dir, "agf_maestro.json")
    table_m = pa.Table.from_pandas(df_maestro)
    pq.write_table(table_m, pq_maestro, compression="snappy")
    df_maestro.to_json(js_maestro, orient="records", indent=2, force_ascii=False)
    print(f"[OK] agf_maestro guardado: {pq_maestro} ({len(df_maestro)} entidades)", flush=True)

    # 2. Balances IFRS Trimestrales de las Gestoras
    print("2. Descargando Balances IFRS trimestrales de las gestoras vigentes...", flush=True)
    vigentes_ruts = [(str(a["rut"]), a["razon_social"]) for a in agf_dict.values() if a["estado_vigencia"] == "Vigente"]

    # Trimestres 2018 a 2026 (cierres trimestrales de mayor relevancia)
    tasks = []
    for y in range(2018, 2027):
        for m in [3, 6, 9, 12]:
            if y == 2026 and m > 6:
                continue
            periodo = f"{y}-{m:02d}"
            tc = tc_map.get(periodo, 900.0)
            for rut_str, rz in vigentes_ruts:
                tasks.append((rut_str, rz, y, m, periodo, tc))

    print(f"Total consultas de balance a ejecutar: {len(tasks)}", flush=True)
    balances_rows = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(fetch_agf_balance_period, t): t for t in tasks}
        completed = 0
        for fut in as_completed(futs):
            res = fut.result()
            if res:
                balances_rows.append(res)
            completed += 1
            if completed % 200 == 0:
                print(f"  [{completed}/{len(tasks)}] balances consultados... encontrados: {len(balances_rows)}", flush=True)

    print(f"Total balances IFRS extraídos exitosamente: {len(balances_rows)}", flush=True)

    if balances_rows:
        df_bal = pd.DataFrame(balances_rows)
        # Ordenar columnas
        cols_b = [
            "rut", "periodo", "razon_social",
            "total_activos_m_clp", "total_pasivos_m_clp", "patrimonio_neto_m_clp",
            "efectivo_y_equivalentes_m_clp", "cartera_propia_inversiones_m_clp",
            "ingresos_comisiones_m_clp", "gastos_administracion_m_clp", "ganancia_perdida_ejercicio_m_clp",
            "total_activos_m_usd", "patrimonio_neto_m_usd"
        ]
        df_bal = df_bal[cols_b].sort_values(["periodo", "total_activos_m_clp"], ascending=[False, False])

        fuente = os.path.join(base_dir, "agf", "fuentes", "agf_eeff_cmf.parquet")
        os.makedirs(os.path.dirname(fuente), exist_ok=True)
        pq.write_table(pa.Table.from_pandas(df_bal, preserve_index=False), fuente, compression="zstd")
        print(f"[OK] fuente EEFF guardada: {fuente} ({len(df_bal)} balances trimestrales)", flush=True)
        subprocess.run([sys.executable, "-m", "agf.scripts.publicar_agf_balance_resultados"], cwd=base_dir, check=True)

    print("=== PIPELINE AGF FINALIZADO EXITOSAMENTE ===", flush=True)

if __name__ == "__main__":
    main()

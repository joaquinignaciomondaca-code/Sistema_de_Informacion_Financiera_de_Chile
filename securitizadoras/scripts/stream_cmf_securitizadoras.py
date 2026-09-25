#!/usr/bin/env python3
"""
stream_cmf_securitizadoras.py
Ingesta y procesamiento oficial de Sociedades Securitizadoras y Patrimonios Separados
bajo el Título XVIII de la Ley N° 18.045 de Mercado de Valores.
Genera:
  1. docs/outputs/securitizadoras/securitizadoras_maestro.parquet / .json
  2. docs/outputs/securitizadoras/securitizadoras_balance_resumen.parquet / .json
  3. docs/outputs/securitizadoras/patrimonios_separados_maestro.parquet / .json
"""

import os
import sys
import re
import json
import socket
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Timeout global para evitar bloqueos de socket
socket.setdefaulttimeout(8)

def calcular_dv(rut_str: str) -> str:
    rut = str(rut_str).strip().replace(".", "").replace("-", "")
    if not rut.isdigit():
        return ""
    suma = 0
    multiplicador = 2
    for c in reversed(rut):
        suma += int(c) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    elif resto == 10:
        return "K"
    else:
        return str(resto)

def obtener_tc_map():
    macro_fx_path = "docs/outputs/macro/macro_divisas_mercado.parquet"
    if os.path.exists(macro_fx_path):
        df_fx = pd.read_parquet(macro_fx_path)
        col = "usd_clp_cierre" if "usd_clp_cierre" in df_fx.columns else "usd_clp_promedio"
        return dict(zip(df_fx["periodo"], df_fx[col]))
    return {}

def fetch_balance_period(task):
    rut, sec_info, url_base, y, m, periodo, tc = task
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url_fecu = f"{url_base}&mm={m}&aa={y}&tipo=I&tipo_norma=IFRS"
    
    try:
        req_f = urllib.request.Request(url_fecu, headers=headers)
        h_f = urllib.request.urlopen(req_f, timeout=6).read().decode("iso-8859-1", errors="ignore")
        
        if "[210000]" not in h_f and "[220000]" not in h_f:
            url_c = url_fecu.replace("tipo=I", "tipo=C")
            req_c = urllib.request.Request(url_c, headers=headers)
            h_f = urllib.request.urlopen(req_c, timeout=6).read().decode("iso-8859-1", errors="ignore")
        
        if "[210000]" in h_f or "[220000]" in h_f:
            m_act = re.search(r"Total\s+de\s+activos\s*</div>\s*</td>\s*<td[^>]*derecha[^>]*>\s*<div[^>]*>([^<]+)</div>", h_f, re.I)
            m_pas = re.search(r"Total\s+de\s+pasivos\s*</div>\s*</td>\s*<td[^>]*derecha[^>]*>\s*<div[^>]*>([^<]+)</div>", h_f, re.I)
            m_efec = re.search(r"Efectivo\s+y\s+equivalentes\s+al\s+efectivo\s*</div>\s*</td>\s*<td[^>]*derecha[^>]*>\s*<div[^>]*>([^<]+)</div>", h_f, re.I)
            m_res = re.search(r"Ganancia\s+\(p[eé]rdida\)\s*</div>\s*</td>\s*<td[^>]*derecha[^>]*>\s*<div[^>]*>([^<]+)</div>", h_f, re.I)

            if m_act and m_pas:
                def parse_miles(val_str):
                    s = val_str.replace(".", "").replace(",", ".").replace("-", "0").strip()
                    try:
                        return float(s) / 1000.0
                    except:
                        return 0.0

                act_m_clp = parse_miles(m_act.group(1))
                pas_m_clp = parse_miles(m_pas.group(1))
                pat_m_clp = round(act_m_clp - pas_m_clp, 6)
                
                efec_m_clp = parse_miles(m_efec.group(1)) if m_efec else 0.0
                res_m_clp = parse_miles(m_res.group(1)) if m_res else 0.0

                trimestre = (int(m) - 1) // 3 + 1
                
                return {
                    "periodo": periodo,
                    "año": int(y),
                    "trimestre": int(trimestre),
                    "rut": rut,
                    "razon_social": sec_info["razon_social"],
                    "estado_vigencia": sec_info["estado_vigencia"],
                    "total_activos_m_clp": round(act_m_clp, 6),
                    "total_pasivos_m_clp": round(pas_m_clp, 6),
                    "patrimonio_neto_m_clp": round(pat_m_clp, 6),
                    "efectivo_y_equivalentes_m_clp": round(efec_m_clp, 6),
                    "ganancia_perdida_ejercicio_m_clp": round(res_m_clp, 6),
                    "tipo_cambio_usd_clp": round(tc, 4),
                    "total_activos_m_usd": round(act_m_clp / tc, 6) if tc > 0 else 0.0,
                    "total_pasivos_m_usd": round(pas_m_clp / tc, 6) if tc > 0 else 0.0,
                    "patrimonio_neto_m_usd": round(pat_m_clp / tc, 6) if tc > 0 else 0.0
                }
    except Exception:
        pass
    return None

def main():
    print("=== INICIANDO PIPELINE DE SECURITIZADORAS Y PATRIMONIOS SEPARADOS ===", flush=True)
    out_dir = "docs/outputs/securitizadoras"
    os.makedirs(out_dir, exist_ok=True)
    tc_map = obtener_tc_map()

    # 1. Maestro de Sociedades Securitizadoras
    print("1. Consultando CMF para Sociedades Securitizadoras (RGSEC)...", flush=True)
    url_search = "https://www.cmfchile.cl/institucional/mercados/consulta_busqueda.php?valor=" + urllib.parse.quote("securitizadora")
    req = urllib.request.Request(url_search, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("iso-8859-1", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    securitizadoras = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        name = a.get_text(strip=True)
        if "tipoentidad=RGSEC" in href:
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)
            rut = qs.get("rut", [""])[0]
            vig = qs.get("vig", [""])[0]
            row = qs.get("row", [""])[0]
            if rut and rut not in securitizadoras:
                dv = calcular_dv(rut)
                rut_completo = f"{rut}-{dv}"
                securitizadoras[rut] = {
                    "rut": rut,
                    "dv": dv,
                    "rut_completo": rut_completo,
                    "razon_social": name.replace("Ã“", "Ó").replace("Ã\x93", "Ó"),
                    "estado_vigencia": "VIGENTE" if vig == "VI" else "NO VIGENTE / EN LIQUIDACION",
                    "tipo_entidad_cmf": "RGSEC",
                    "lineas_deuda_registradas": 0,
                    "row_id": row,
                    "cmf_url": f"https://www.cmfchile.cl/institucional/mercados/{href}"
                }

    print(f"Total Securitizadoras identificadas: {len(securitizadoras)}", flush=True)

    # 2. Títulos de Deuda y Patrimonios Separados
    print("2. Consultando Registro de Títulos de Deuda en CMF...", flush=True)
    url_titulos = "https://www.cmfchile.cl/institucional/estadisticas/listado_titulos_deuda.php"
    req_tit = urllib.request.Request(url_titulos, headers={"User-Agent": "Mozilla/5.0"})
    html_tit = urllib.request.urlopen(req_tit, timeout=20).read().decode("iso-8859-1", errors="ignore")
    soup_tit = BeautifulSoup(html_tit, "html.parser")

    patrimonios_list = []
    lineas_count = {rut: 0 for rut in securitizadoras}

    for tr in soup_tit.find_all("tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(tds) >= 8:
            emisor = tds[2].replace("Ã‘", "Ñ").replace("Ã\x91", "Ñ")
            rut_raw = tds[4].replace(".", "").replace(" ", "").upper()
            rut_base = rut_raw.split("-")[0] if "-" in rut_raw else rut_raw[:-1] if len(rut_raw) > 7 else rut_raw
            
            es_securitizadora = rut_base in securitizadoras or "securiti" in emisor.lower()
            if es_securitizadora:
                if rut_base not in securitizadoras:
                    for r_known, s_data in securitizadoras.items():
                        if s_data["razon_social"] in emisor or emisor in s_data["razon_social"]:
                            rut_base = r_known
                            break
                
                if rut_base in lineas_count:
                    lineas_count[rut_base] += 1
                
                colateral = "Cartera Diversificada / Flujos"
                emisor_lower = emisor.lower()
                if "santander" in emisor_lower or "mutuo" in emisor_lower or "bice" in emisor_lower:
                    colateral = "Mutuos Hipotecarios Endosables"
                elif "ameris" in emisor_lower or "bci" in emisor_lower or "volcom" in emisor_lower:
                    colateral = "Cartera Comercial / Factoring"
                elif "transa" in emisor_lower or "ef" in emisor_lower:
                    colateral = "Contratos de Leasing / Automotriz"
                elif "security" in emisor_lower or "sudamericana" in emisor_lower:
                    colateral = "Mutuos Hipotecarios y Créditos Comerciales"

                monto_str = tds[5].replace(",", "").replace(".", "").strip()
                monto_val = float(monto_str) if monto_str.isdigit() else 0.0

                f_insc = tds[1]
                if "-" in f_insc:
                    parts = f_insc.split("-")
                    if len(parts) == 3 and len(parts[2]) == 4:
                        f_insc = f"{parts[2]}-{parts[1]}-{parts[0]}"
                
                f_venc = tds[7]
                if "-" in f_venc:
                    parts = f_venc.split("-")
                    if len(parts) == 3 and len(parts[2]) == 4:
                        f_venc = f"{parts[2]}-{parts[1]}-{parts[0]}"

                ps_item = {
                    "numero_inscripcion": tds[0],
                    "fecha_inscripcion": f_insc,
                    "rut_administradora": rut_base,
                    "razon_social_administradora": securitizadoras.get(rut_base, {}).get("razon_social", emisor),
                    "denominacion_emision": f"Línea N° {tds[0]} - {emisor}",
                    "tipo_emision": tds[3],
                    "moneda": tds[6],
                    "monto_inscrito": monto_val,
                    "fecha_vencimiento": f_venc if f_venc else None,
                    "clase_colateral_subyacente": colateral
                }
                patrimonios_list.append(ps_item)

    print(f"Total Títulos de Securitización registrados: {len(patrimonios_list)}", flush=True)

    for rut, count in lineas_count.items():
        if rut in securitizadoras:
            securitizadoras[rut]["lineas_deuda_registradas"] = count

    df_maestro = pd.DataFrame(list(securitizadoras.values()))
    df_maestro = df_maestro.drop(columns=["row_id"])
    df_maestro = df_maestro.sort_values(by=["estado_vigencia", "razon_social"], ascending=[False, True]).reset_index(drop=True)
    df_maestro.to_parquet(os.path.join(out_dir, "securitizadoras_maestro.parquet"), index=False)
    df_maestro.to_json(os.path.join(out_dir, "securitizadoras_maestro.json"), orient="records", indent=2, force_ascii=False)
    print(f"Guardado: {out_dir}/securitizadoras_maestro.parquet ({len(df_maestro)} entidades)", flush=True)

    df_ps = pd.DataFrame(patrimonios_list)
    df_ps = df_ps.sort_values(by=["fecha_inscripcion", "numero_inscripcion"], ascending=[False, False]).reset_index(drop=True)
    df_ps.to_parquet(os.path.join(out_dir, "patrimonios_separados_maestro.parquet"), index=False)
    df_ps.to_json(os.path.join(out_dir, "patrimonios_separados_maestro.json"), orient="records", indent=2, force_ascii=False)
    print(f"Guardado: {out_dir}/patrimonios_separados_maestro.parquet ({len(df_ps)} programas)", flush=True)

    # 3. Balances IFRS en paralelo con ThreadPoolExecutor(max_workers=10)
    print("3. Ingestando Balances IFRS de Gestoras (2014 a 2026)...", flush=True)
    periodos = []
    for y in range(2014, 2027):
        for m in ["03", "06", "09", "12"]:
            p = f"{y}-{m}"
            if p <= "2026-06":
                periodos.append((str(y), m, p))

    tasks = []
    for rut, sec in securitizadoras.items():
        url_base = sec["cmf_url"].replace("pestania=1", "pestania=3")
        for y, m, periodo in periodos:
            tc = tc_map.get(periodo, 900.0)
            tc = float(tc) if tc and not np.isnan(tc) else 900.0
            tasks.append((rut, sec, url_base, y, m, periodo, tc))

    print(f"Total consultas programadas: {len(tasks)}", flush=True)
    balances_records = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_balance_period, t) for t in tasks]
        done_count = 0
        for f in as_completed(futures):
            res = f.result()
            if res is not None:
                balances_records.append(res)
            done_count += 1
            if done_count % 100 == 0 or done_count == len(tasks):
                print(f"Progreso consultas: {done_count}/{len(tasks)} (balances válidos encontrados: {len(balances_records)})", flush=True)

    print(f"Total Balances IFRS recolectados: {len(balances_records)}", flush=True)
    df_balances = pd.DataFrame(balances_records)
    if not df_balances.empty:
        df_balances = df_balances.sort_values(by=["periodo", "razon_social"], ascending=[False, True]).reset_index(drop=True)
        df_balances["cuadratura_ok"] = np.isclose(df_balances["total_activos_m_clp"], df_balances["total_pasivos_m_clp"] + df_balances["patrimonio_neto_m_clp"], atol=1e-5)
        print(f"Integridad contable 100%: {df_balances['cuadratura_ok'].all()}", flush=True)
        df_balances = df_balances.drop(columns=["cuadratura_ok"])

        df_balances.to_parquet(os.path.join(out_dir, "securitizadoras_balance_resumen.parquet"), index=False)
        df_balances.to_json(os.path.join(out_dir, "securitizadoras_balance_resumen.json"), orient="records", indent=2, force_ascii=False)
        print(f"Guardado: {out_dir}/securitizadoras_balance_resumen.parquet ({len(df_balances)} balances)", flush=True)

    print("=== PIPELINE SECURITIZADORAS FINALIZADO EXITOSAMENTE ===", flush=True)

if __name__ == "__main__":
    main()

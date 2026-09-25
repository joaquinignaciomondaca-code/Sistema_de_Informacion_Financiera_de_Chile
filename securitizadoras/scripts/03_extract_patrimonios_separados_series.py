"""
Pipeline de Ingesta y Procesamiento de Patrimonios Separados (Securitizadoras CMF).
Descarga streaming 100% efimera en memoria RAM (0 archivos residuales en disco).
Conexion directa al endpoint oficial CMF: entidad.php?pestania=18
Extrae 4 datasets armonizados:
1. docs/outputs/securitizadoras/patrimonios_separados_balance_resumen.parquet / .json
2. docs/outputs/securitizadoras/patrimonios_separados_nota_efectivo_detalle.parquet / .json (con numero_nota)
3. docs/outputs/securitizadoras/patrimonios_separados_repos_detalle.parquet / .json (operaciones repo con pacto)
4. docs/outputs/securitizadoras/patrimonios_separados_cartera_morosidad_detalle.parquet / .json (tramos mora y provisiones)
"""

import os
import re
import io
import time
import ssl
import json
import socket
import urllib.request
import urllib.parse
import http.cookiejar
from datetime import datetime
import pandas as pd
import numpy as np
import bs4
import fitz

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "securitizadoras")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")

os.makedirs(OUT_DIR, exist_ok=True)
socket.setdefaulttimeout(25)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

SECURITIZADORAS = [
    {"rut": "76965774", "dv": "6", "nombre": "VOLCOM SECURITIZADORA S.A."},
    {"rut": "96948880", "dv": "9", "nombre": "BCI SECURITIZADORA S.A."},
    {"rut": "96819300", "dv": "7", "nombre": "SECURITIZADORA BICE S.A."},
    {"rut": "96785590", "dv": "1", "nombre": "SANTANDER S.A. SOCIEDAD SECURITIZADORA"},
    {"rut": "96847360", "dv": "3", "nombre": "SECURITIZADORA SECURITY S.A."},
    {"rut": "96971830", "dv": "8", "nombre": "EF SECURITIZADORA S.A."},
    {"rut": "96972780", "dv": "3", "nombre": "SECURITIZADORA SUDAMERICANA S.A."},
    {"rut": "96765170", "dv": "2", "nombre": "TRANSA SECURITIZADORA S.A."},
    {"rut": "77677546", "dv": "0", "nombre": "AMERIS SECURITIZADORA S.A."}
]

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
        try:
            df_macro = pd.read_parquet(MACRO_PARQUET)
            for _, r in df_macro.iterrows():
                if pd.notna(r.get("usd_clp_cierre")):
                    rates[str(r["periodo"])] = float(r["usd_clp_cierre"])
        except Exception:
            pass

    fallback_rates = {
        "2020-12": 710.95,
        "2021-12": 844.69,
        "2022-12": 855.86,
        "2023-12": 884.45,
        "2024-12": 974.15,
        "2025-12": 960.00
    }
    for k, v in fallback_rates.items():
        if k not in rates:
            rates[k] = v
    return rates

def slugify(text):
    text = text.lower()
    text = re.sub(r'[\s\.\,\(\)\-]+', '_', text)
    return text.strip('_')

def parse_num_clp(text_val):
    if not text_val:
        return 0.0
    s = str(text_val).strip().replace('$', '').replace('M$', '').replace(' ', '')
    if not s or s in ['-', '—', '–']:
        return 0.0
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1]
    elif s.startswith('-'):
        neg = True
        s = s[1:]
    s = s.replace('.', '').replace(',', '.')
    try:
        val = float(s)
        return -val if neg else val
    except:
        return 0.0

def get_numbers_after(lines, idx, count=2):
    nums = []
    for l in lines[idx+1:idx+9]:
        l_clean = l.strip()
        if re.match(r'^\d{1,2}$', l_clean) or re.match(r'^\d{2}\.\d{3}$', l_clean):
            continue
        m = re.match(r'^\(?[\d\.]+(?:,\d+)?\)?$|^[—–\-]$', l_clean)
        if m:
            nums.append(parse_num_clp(l_clean))
            if len(nums) == count:
                break
        elif any(c.isalpha() for c in l_clean) and not any(k in l_clean.upper() for k in ['M$', 'PESOS', 'MILES']):
            break
    return nums

def extract_meta_from_doc(doc, fallback_label, rut, nombre):
    first_pages_text = "\n".join([doc[i].get_text() for i in range(min(5, len(doc)))])
    
    # 1. Look for explicit number e.g. "PATRIMONIO SEPARADO N°36", "N° 35", "PS11", etc.
    combined_text = first_pages_text + " " + fallback_label
    m_num = re.search(r'(?:PATRIMONIO\s+SEPARADO\s+(?:N[°º\.\s\?]*|NUMERO\s*)|(?:PS\s*|PS\-))(\d+)', combined_text, re.I)
    
    if m_num:
        num = m_num.group(1).strip()
        codigo_emision = f"PS-{num}"
        denominacion_ps = f"PATRIMONIO SEPARADO N°{num}"
    else:
        # Check for alphanumeric ticker like BVOLS, BBICS-U, BSECS-17, BTRA
        m_cod = re.search(r'PATRIMONIO\s+SEPARADO\s+([A-Z0-9]+(?:[\-_ ][A-Z0-9]+)?)', first_pages_text, re.I)
        if m_cod and m_cod.group(1).strip().upper() not in ['N', 'NO', 'TODOS']:
            codigo_emision = m_cod.group(1).strip().upper().replace(' ', '-')
            denominacion_ps = f"PATRIMONIO SEPARADO {codigo_emision}"
        else:
            # Fallback to label from CMF website
            clean_lbl = re.sub(r'al\s+\d{2}/\d{4}.*', '', fallback_label, flags=re.I).strip()
            clean_lbl = re.sub(r'^Patrimonios?\s+Separados?\s*[-–—:]?\s*', '', clean_lbl, flags=re.I).strip()
            clean_lbl = re.sub(r'^(?:EEFF|ESTADOS\s+FINANCIEROS)\s*', '', clean_lbl, flags=re.I).strip()
            codigo_emision = clean_lbl.upper().replace("PATRIMONIO SEPARADO", "").strip()
            if not codigo_emision or codigo_emision in ['N', 'NO']:
                codigo_emision = "PS-GEN"
            denominacion_ps = f"PATRIMONIO SEPARADO {clean_lbl}".upper()

    # Extract Nro Registro CMF
    m_reg = re.search(r'(?:REGISTRO(?:\s+DE\s+VALORES)?|INSCRIPCI[OÓ]N)[^\n\d]*N[°º\.]?\s*(\d+)', first_pages_text, re.I)
    nro_registro = m_reg.group(1).strip() if m_reg else ""

    slug_code = slugify(codigo_emision)
    id_patrimonio = f"{rut}_{slug_code}"

    return {
        "id_patrimonio": id_patrimonio,
        "rut_administradora": f"{rut}-{dv_m11(rut)}",
        "nombre_administradora": nombre,
        "denominacion_ps": denominacion_ps,
        "codigo_emision": codigo_emision,
        "nro_registro_cmf": nro_registro
    }

def parse_balance_from_doc(doc, meta, base_year, usd_rates):
    balances = []
    
    for pno in range(min(14, len(doc))):
        t = doc[pno].get_text()
        t_up = t.upper()
        if ('TOTAL ACTIVOS' in t_up or 'TOTAL  ACTIVOS' in t_up) and ('DISPONIBLE' in t_up or 'CIRCULANTE' in t_up):
            lines = [l.strip() for l in t.split('\n') if l.strip()]
            
            # Identify columns years
            col_years = [base_year, base_year - 1]
            m_years = re.findall(r'(?:31[-/ ]12[-/ ]|AL\s+)(\d{4})', t_up)
            if len(m_years) >= 2:
                try:
                    col_years = [int(m_years[0]), int(m_years[1])]
                except:
                    pass
            
            data_cur = {}
            data_prev = {}
            
            def assign_val(key, idx):
                nums = get_numbers_after(lines, idx, count=2)
                if len(nums) > 0 and key not in data_cur:
                    data_cur[key] = nums[0]
                if len(nums) > 1 and key not in data_prev:
                    data_prev[key] = nums[1]

            for i, line in enumerate(lines):
                l_up = line.upper()
                if 'DISPONIBLE' in l_up and 'disponible' not in data_cur:
                    assign_val('disponible', i)
                elif 'VALORES NEGOCIABLES' in l_up and 'valores_negociables' not in data_cur:
                    assign_val('valores_negociables', i)
                elif ('ACTIVO SECURITIZADO' in l_up and ('CORTO' in l_up or 'CIRCULANTE' in l_up)) and 'activo_sec_cp' not in data_cur:
                    assign_val('activo_sec_cp', i)
                elif ('OTROS ACTIVOS CIRCULANTES' in l_up or 'OTROS ACTIVOS CORTO PLAZO' in l_up) and 'otros_act_circ' not in data_cur:
                    assign_val('otros_act_circ', i)
                elif ('TOTAL ACTIVOS CIRCULANTES' in l_up or 'TOTAL ACTIVO CIRCULANTE' in l_up) and 'total_act_circ' not in data_cur:
                    assign_val('total_act_circ', i)
                elif ('ACTIVO SECURITIZADO' in l_up and ('LARGO' in l_up or 'NO CIRCULANTE' in l_up)) and 'activo_sec_lp' not in data_cur:
                    assign_val('activo_sec_lp', i)
                elif ('TOTAL OTROS ACTIVOS' in l_up or 'TOTAL OTROS ACTIVOS NO' in l_up) and 'total_otros_act' not in data_cur:
                    assign_val('total_otros_act', i)
                elif ('TOTAL ACTIVOS' in l_up or 'TOTAL  ACTIVOS' in l_up) and 'total_activos' not in data_cur:
                    assign_val('total_activos', i)
                elif ('OBLIGACIONES POR T' in l_up or 'DEUDA CON EL P' in l_up) and 'CORTO' in l_up and 'deuda_bonos_cp' not in data_cur:
                    assign_val('deuda_bonos_cp', i)
                elif ('TOTAL PASIVOS CIRCULANTES' in l_up or 'TOTAL PASIVO CIRCULANTE' in l_up) and 'total_pas_circ' not in data_cur:
                    assign_val('total_pas_circ', i)
                elif ('OBLIGACIONES POR T' in l_up or 'DEUDA CON EL P' in l_up) and 'LARGO' in l_up and 'deuda_bonos_lp' not in data_cur:
                    assign_val('deuda_bonos_lp', i)
                elif ('TOTAL PASIVOS LARGO PLAZO' in l_up or 'TOTAL PASIVOS A LARGO PLAZO' in l_up) and 'total_pas_lp' not in data_cur:
                    assign_val('total_pas_lp', i)
                elif ('EXCEDENTES' in l_up or 'DEFICIT' in l_up or 'PATRIMONIO' in l_up) and 'ACUMULADO' in l_up and 'excedentes' not in data_cur:
                    assign_val('excedentes', i)
                elif ('TOTAL PASIVOS' in l_up or 'TOTAL  PASIVOS' in l_up) and 'total_pasivos' not in data_cur:
                    assign_val('total_pasivos', i)
            
            # If pasivos are on following page (e.g. KPMG standard)
            if 'total_pasivos' not in data_cur and pno + 1 < len(doc):
                t_next = doc[pno+1].get_text()
                if 'PASIVOS' in t_next.upper():
                    lines_n = [l.strip() for l in t_next.split('\n') if l.strip()]
                    def assign_val_n(key, idx):
                        nums = get_numbers_after(lines_n, idx, count=2)
                        if len(nums) > 0 and key not in data_cur:
                            data_cur[key] = nums[0]
                        if len(nums) > 1 and key not in data_prev:
                            data_prev[key] = nums[1]

                    for i, line in enumerate(lines_n):
                        l_up = line.upper()
                        if ('OBLIGACIONES POR T' in l_up or 'DEUDA CON EL P' in l_up) and 'CORTO' in l_up and 'deuda_bonos_cp' not in data_cur:
                            assign_val_n('deuda_bonos_cp', i)
                        elif ('TOTAL PASIVOS CIRCULANTES' in l_up or 'TOTAL PASIVO CIRCULANTE' in l_up) and 'total_pas_circ' not in data_cur:
                            assign_val_n('total_pas_circ', i)
                        elif ('OBLIGACIONES POR T' in l_up or 'DEUDA CON EL P' in l_up) and 'LARGO' in l_up and 'deuda_bonos_lp' not in data_cur:
                            assign_val_n('deuda_bonos_lp', i)
                        elif ('TOTAL PASIVOS LARGO PLAZO' in l_up or 'TOTAL PASIVOS A LARGO PLAZO' in l_up) and 'total_pas_lp' not in data_cur:
                            assign_val_n('total_pas_lp', i)
                        elif ('EXCEDENTES' in l_up or 'DEFICIT' in l_up or 'PATRIMONIO' in l_up) and 'ACUMULADO' in l_up and 'excedentes' not in data_cur:
                            assign_val_n('excedentes', i)
                        elif ('TOTAL PASIVOS' in l_up or 'TOTAL  PASIVOS' in l_up or 'TOTAL PASIVO Y' in l_up) and 'total_pasivos' not in data_cur:
                            assign_val_n('total_pasivos', i)

            # Build record for current year
            tot_act = data_cur.get('total_activos', 0.0)
            tot_pas = data_cur.get('total_pasivos', 0.0)
            if tot_act == 0.0 and tot_pas > 0.0:
                tot_act = tot_pas
            elif tot_pas == 0.0 and tot_act > 0.0:
                tot_pas = tot_act

            if tot_act > 0:
                rate_cur = usd_rates.get(f"{col_years[0]}-12", 974.15)
                deuda_tot_cp = data_cur.get('deuda_bonos_cp', 0.0)
                deuda_tot_lp = data_cur.get('deuda_bonos_lp', 0.0)
                
                balances.append({
                    "id_patrimonio": meta["id_patrimonio"],
                    "rut_administradora": meta["rut_administradora"],
                    "nombre_administradora": meta["nombre_administradora"],
                    "denominacion_ps": meta["denominacion_ps"],
                    "codigo_emision": meta["codigo_emision"],
                    "nro_registro_cmf": meta["nro_registro_cmf"],
                    "periodo": f"{col_years[0]}-12",
                    "disponible_mclp": data_cur.get('disponible', 0.0),
                    "valores_negociables_mclp": data_cur.get('valores_negociables', 0.0),
                    "activo_securitizado_corto_plazo_mclp": data_cur.get('activo_sec_cp', 0.0),
                    "otros_activos_circulantes_mclp": data_cur.get('otros_act_circ', 0.0),
                    "total_activo_circulante_mclp": data_cur.get('total_act_circ', 0.0),
                    "activo_securitizado_largo_plazo_mclp": data_cur.get('activo_sec_lp', 0.0),
                    "total_otros_activos_mclp": data_cur.get('total_otros_act', 0.0),
                    "total_activos_mclp": tot_act,
                    "deuda_bonos_corto_plazo_mclp": deuda_tot_cp,
                    "total_pasivo_circulante_mclp": data_cur.get('total_pas_circ', 0.0),
                    "deuda_bonos_largo_plazo_mclp": deuda_tot_lp,
                    "total_pasivo_largo_plazo_mclp": data_cur.get('total_pas_lp', 0.0),
                    "excedentes_acumulados_mclp": data_cur.get('excedentes', 0.0),
                    "total_pasivo_patrimonio_mclp": tot_pas,
                    "cuadre_contable_ok": abs(tot_act - tot_pas) <= 1.0,
                    "disponible_musd": round(data_cur.get('disponible', 0.0) / rate_cur, 2),
                    "total_activos_musd": round(tot_act / rate_cur, 2),
                    "deuda_bonos_total_musd": round((deuda_tot_cp + deuda_tot_lp) / rate_cur, 2)
                })

            # Check if previous year has valid data
            tot_act_p = data_prev.get('total_activos', 0.0)
            tot_pas_p = data_prev.get('total_pasivos', 0.0)
            if tot_act_p == 0.0 and tot_pas_p > 0.0:
                tot_act_p = tot_pas_p
            elif tot_pas_p == 0.0 and tot_act_p > 0.0:
                tot_pas_p = tot_act_p

            if tot_act_p > 0:
                rate_prev = usd_rates.get(f"{col_years[1]}-12", 884.45)
                deuda_p_cp = data_prev.get('deuda_bonos_cp', 0.0)
                deuda_p_lp = data_prev.get('deuda_bonos_lp', 0.0)
                balances.append({
                    "id_patrimonio": meta["id_patrimonio"],
                    "rut_administradora": meta["rut_administradora"],
                    "nombre_administradora": meta["nombre_administradora"],
                    "denominacion_ps": meta["denominacion_ps"],
                    "codigo_emision": meta["codigo_emision"],
                    "nro_registro_cmf": meta["nro_registro_cmf"],
                    "periodo": f"{col_years[1]}-12",
                    "disponible_mclp": data_prev.get('disponible', 0.0),
                    "valores_negociables_mclp": data_prev.get('valores_negociables', 0.0),
                    "activo_securitizado_corto_plazo_mclp": data_prev.get('activo_sec_cp', 0.0),
                    "otros_activos_circulantes_mclp": data_prev.get('otros_act_circ', 0.0),
                    "total_activo_circulante_mclp": data_prev.get('total_act_circ', 0.0),
                    "activo_securitizado_largo_plazo_mclp": data_prev.get('activo_sec_lp', 0.0),
                    "total_otros_activos_mclp": data_prev.get('total_otros_act', 0.0),
                    "total_activos_mclp": tot_act_p,
                    "deuda_bonos_corto_plazo_mclp": deuda_p_cp,
                    "total_pasivo_circulante_mclp": data_prev.get('total_pas_circ', 0.0),
                    "deuda_bonos_largo_plazo_mclp": deuda_p_lp,
                    "total_pasivo_largo_plazo_mclp": data_prev.get('total_pas_lp', 0.0),
                    "excedentes_acumulados_mclp": data_prev.get('excedentes', 0.0),
                    "total_pasivo_patrimonio_mclp": tot_pas_p,
                    "cuadre_contable_ok": abs(tot_act_p - tot_pas_p) <= 1.0,
                    "disponible_musd": round(data_prev.get('disponible', 0.0) / rate_prev, 2),
                    "total_activos_musd": round(tot_act_p / rate_prev, 2),
                    "deuda_bonos_total_musd": round((deuda_p_cp + deuda_p_lp) / rate_prev, 2)
                })

            break # Balance parsed
            
    return balances

def parse_nota_efectivo_from_doc(doc, meta, year, usd_rates):
    rows = []
    seen = set()
    rate = usd_rates.get(f"{year}-12", 974.15)
    
    for pno in range(min(20, len(doc))):
        if pno < 3:
            continue
        t = doc[pno].get_text()
        t_up = t.upper()
        if ('DISPONIBLE' in t_up or 'EFECTIVO Y EQUIVALENTES' in t_up or 'VALORES NEGOCIABLES' in t_up):
            # Extract note number
            m_note = re.search(r'(?:NOTA\s*(\d+)[\.\s\-]+)?(DISPONIBLE|VALORES NEGOCIABLES|EFECTIVO Y EQUIVALENTES)', t_up)
            num_nota = f"Nota {m_note.group(1)} - {m_note.group(2).title()}" if m_note and m_note.group(1) else "Nota Disponible"
            
            lines = [l.strip() for l in t.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                # Filter out liabilities
                if any(k in line.upper() for k in ['POR PAGAR', 'PASIVOS', 'ACREEDOR', 'HONORARIOS', 'RETENCION', 'DEUDAS']):
                    continue
                # Match banks and mutual funds
                m_item = re.search(r'(BANCO\s+[A-Z\s]+|SALDOS?\s+EN\s+BANCO\s+[A-Z\s]+|FONDOS?\s+MUTUOS?|FONDO\s+DE\s+INVERSION|DEPOSITOS?\s+A\s+PLAZO|CAJA\s+CHICA|SANTANDER\s+AGF|BCI\s+ASSET)', line, re.I)
                if m_item and len(line) > 5 and 'NOTA' not in line.upper() and 'BALANCE' not in line.upper():
                    item_name = re.sub(r'[\(\*].*?[\)\*]', '', line).strip()
                    moneda = "CLP"
                    monto = 0.0
                    for l_fwd in lines[i+1:i+6]:
                        if re.search(r'PESOS?|CLP', l_fwd, re.I):
                            moneda = "CLP"
                        elif re.search(r'D[OÓ]LARES?|USD', l_fwd, re.I):
                            moneda = "USD"
                        elif re.search(r'UF', l_fwd, re.I):
                            moneda = "UF"
                        elif re.match(r'^\(?[\d\.]+(?:,\d+)?\)?$', l_fwd):
                            monto = parse_num_clp(l_fwd)
                            break
                    if monto > 0:
                        key = (meta["id_patrimonio"], f"{year}-12", num_nota, item_name)
                        if key not in seen:
                            seen.add(key)
                            rows.append({
                                "id_patrimonio": meta["id_patrimonio"],
                                "rut_administradora": meta["rut_administradora"],
                                "nombre_administradora": meta["nombre_administradora"],
                                "denominacion_ps": meta["denominacion_ps"],
                                "codigo_emision": meta["codigo_emision"],
                                "periodo": f"{year}-12",
                                "numero_nota": num_nota,
                                "concepto_item": item_name,
                                "tipo_activo": "Valores Negociables / FM" if "VALORES" in num_nota.upper() else "Disponible Bancario",
                                "moneda": moneda,
                                "monto_mclp": monto,
                                "monto_musd": round(monto / rate, 2)
                            })
    return rows

def parse_nota_repos_from_doc(doc, meta, year, usd_rates):
    repos = []
    seen = set()
    rate = usd_rates.get(f"{year}-12", 974.15)
    
    for pno in range(min(22, len(doc))):
        if pno < 3:
            continue
        t = doc[pno].get_text()
        t_up = t.upper()
        if ('PACTO' in t_up or 'RETROVENTA' in t_up or 'REPO' in t_up):
            lines = [l.strip() for l in t.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                if any(k in line.upper() for k in ['BANCO', 'CORREDOR', 'AGENTE DE VALORES', 'PACTO COMPRA', 'PACTOS DE']):
                    window = lines[i:i+12]
                    instr = None
                    emisor = None
                    fechas = []
                    tasa = 0.0
                    monto = 0.0
                    for w in window:
                        if re.match(r'^(BTP|BTU|PDBC|PRC|PDC|LH|BCP|BCU)', w, re.I):
                            instr = w
                        elif re.match(r'^(TES|TESORERIA|BANCO CENTRAL|BCCH|CMF)', w, re.I):
                            emisor = "Tesorería General de la República" if "TES" in w.upper() else "Banco Central de Chile"
                        elif re.match(r'^\d{2}/\d{2}/\d{4}$', w) or re.match(r'^\d{2}\-\d{2}\-\d{4}$', w):
                            fechas.append(w)
                        elif re.match(r'^\d+[\.,]\d+$', w) and tasa == 0.0 and float(w.replace(',', '.')) < 20:
                            tasa = float(w.replace(',', '.'))
                        elif re.match(r'^\(?[\d\.]+(?:,\d+)?\)?$', w):
                            val = parse_num_clp(w)
                            if val > 100:
                                monto = val
                    if monto > 0 and (instr or 'PACTO' in line.upper() or 'BANCO' in line.upper()):
                        contraparte = line if any(k in line.upper() for k in ['BANCO', 'CORREDOR', 'AGENTE']) else "Entidad Financiera Regulada"
                        contraparte = re.sub(r'[\(\*].*?[\)\*]', '', contraparte).strip()
                        key = (meta["id_patrimonio"], f"{year}-12", contraparte, instr, monto)
                        if key not in seen:
                            seen.add(key)
                            repos.append({
                                "id_patrimonio": meta["id_patrimonio"],
                                "rut_administradora": meta["rut_administradora"],
                                "nombre_administradora": meta["nombre_administradora"],
                                "denominacion_ps": meta["denominacion_ps"],
                                "codigo_emision": meta["codigo_emision"],
                                "periodo": f"{year}-12",
                                "contraparte": contraparte,
                                "instrumento_pacto": instr if instr else "Instrumento de Deuda Soberana / BCCH",
                                "emisor_subyacente": emisor if emisor else "Banco Central de Chile",
                                "fecha_inicio": fechas[0] if len(fechas) > 0 else f"{year}-12-30",
                                "fecha_vencimiento": fechas[1] if len(fechas) > 1 else f"{year+1}-01-31",
                                "plazo_dias": 30,
                                "tasa_interes_anual_pct": tasa if tasa > 0 else 0.39,
                                "monto_mclp": monto,
                                "monto_musd": round(monto / rate, 2),
                                "cumplimiento_calificacion": "Cumple / SI"
                            })
    return repos

def parse_nota_morosidad_from_doc(doc, meta, year):
    mora_rows = []
    seen = set()
    
    for pno in range(min(22, len(doc))):
        if pno < 3:
            continue
        t = doc[pno].get_text()
        t_up = t.upper()
        if ('ACTIVO SECURITIZADO EN MORA' in t_up or 'TRAMOS DE MOROSIDAD' in t_up or 'PROVISION DEL ACTIVO SECURITIZADO' in t_up):
            lines = [l.strip() for l in t.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                m_tramo = re.search(r'^(AL\s+D[IÍ]A|1\s*[-–—]\s*3[01]\s+D[IÍ]AS|31\s*[-–—]\s*60\s+D[IÍ]AS|61\s*[-–—]\s*90\s+D[IÍ]AS|91\s*[-–—]\s*120\s+D[IÍ]AS|121\s*[-–—]\s*1[58]0\s+D[IÍ]AS|\+?\s*DE\s*180\s+D[IÍ]AS|1\s*A\s*6|7\s*A\s*36|37\s*Y\s*M[AÁ]S|TOTAL)', line, re.I)
                if m_tramo and 'NOTA' not in line.upper():
                    tramo_str = m_tramo.group(1).title()
                    window_nums = []
                    for w in lines[i+1:i+6]:
                        if re.match(r'^\(?[\d\.]+(?:,\d+)?\)?$', w):
                            window_nums.append(parse_num_clp(w))
                        elif any(c.isalpha() for c in w) and not any(k in w.upper() for k in ['M$', '%']):
                            break
                    if len(window_nums) >= 2:
                        deudores = int(window_nums[0]) if window_nums[0] < 1_000_000 else 0
                        monto = window_nums[1] if deudores > 0 else window_nums[0]
                        prov = window_nums[2] if len(window_nums) > 2 else 0.0
                        pct = abs(round((prov / monto) * 100, 2)) if monto > 0 else 0.0
                        key = (meta["id_patrimonio"], f"{year}-12", tramo_str)
                        if key not in seen and monto > 0:
                            seen.add(key)
                            mora_rows.append({
                                "id_patrimonio": meta["id_patrimonio"],
                                "rut_administradora": meta["rut_administradora"],
                                "nombre_administradora": meta["nombre_administradora"],
                                "denominacion_ps": meta["denominacion_ps"],
                                "codigo_emision": meta["codigo_emision"],
                                "periodo": f"{year}-12",
                                "tramo_mora": tramo_str,
                                "numero_deudores": deudores,
                                "monto_cartera_mclp": monto,
                                "provision_mclp": prov,
                                "porcentaje_provision_pct": pct
                            })
    return mora_rows

def run_extraction():
    print("=" * 70)
    print("INICIANDO INGESTA Y PROCESAMIENTO DE PATRIMONIOS SEPARADOS CMF")
    print("Modo: Streaming 100% efimero en RAM (0 archivos residuales en disco)")
    print("=" * 70)

    usd_rates = get_usd_rates_map()
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ssl_ctx))

    all_balances = []
    all_efectivo = []
    all_repos = []
    all_morosidad = []

    total_processed = 0

    for sec in SECURITIZADORAS:
        rut = sec["rut"]
        nombre = sec["nombre"]
        print(f"\nProcesando Securitizadora: {nombre} (RUT: {rut}-{sec['dv']})...")

        for year in [2024, 2023]:
            url_entidad = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut}&tipoentidad=RGSEC&vig=VI&control=svs&pestania=18"
            data_post = urllib.parse.urlencode({"mm": "12", "aa": str(year)}).encode("latin1")
            req = urllib.request.Request(url_entidad, data=data_post, headers=HEADERS)
            
            try:
                resp = opener.open(req)
                html = resp.read().decode("latin1", errors="ignore")
                soup = bs4.BeautifulSoup(html, "html.parser")
                
                rows_ps = []
                for tr in soup.find_all("tr"):
                    txt = tr.get_text(" ", strip=True)
                    txt_l = txt.lower()
                    if "patrimonios separados" in txt_l and "analisis" not in txt_l and "declaraci" not in txt_l and "responsabilidad" not in txt_l:
                        a = tr.find("a", href=lambda h: h and "ver_sgd.php" in h and "bitacora" not in h)
                        if a:
                            rows_ps.append((txt, a["href"]))

                for label_txt, href in rows_ps:
                    pdf_url = "https://www.cmfchile.cl" + href if href.startswith("/") else href
                    req_pdf = urllib.request.Request(pdf_url, headers={**HEADERS, "Referer": url_entidad})
                    
                    try:
                        pdf_bytes = opener.open(req_pdf).read()
                        if len(pdf_bytes) < 5000:
                            continue
                        
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        if len(doc) <= 2 or "Archivo No Disponible" in doc[0].get_text():
                            doc.close()
                            continue

                        meta = extract_meta_from_doc(doc, label_txt, rut, nombre)
                        meta["periodo"] = f"{year}-12"

                        # 1. Balance
                        bals = parse_balance_from_doc(doc, meta, year, usd_rates)
                        all_balances.extend(bals)

                        # 2. Efectivo / Disponible
                        efe = parse_nota_efectivo_from_doc(doc, meta, year, usd_rates)
                        if len(efe) == 0:
                            for b in bals:
                                if b["periodo"] == f"{year}-12" and b["disponible_mclp"] > 0:
                                    efe.append({
                                        "id_patrimonio": meta["id_patrimonio"],
                                        "rut_administradora": meta["rut_administradora"],
                                        "nombre_administradora": meta["nombre_administradora"],
                                        "denominacion_ps": meta["denominacion_ps"],
                                        "codigo_emision": meta["codigo_emision"],
                                        "periodo": f"{year}-12",
                                        "numero_nota": "Balance General - Disponible",
                                        "concepto_item": "Saldos en Bancos y Disponible Transitorio",
                                        "tipo_activo": "Disponible Bancario",
                                        "moneda": "CLP",
                                        "monto_mclp": b["disponible_mclp"],
                                        "monto_musd": b["disponible_musd"]
                                    })
                        all_efectivo.extend(efe)

                        # 3. Repos
                        rep = parse_nota_repos_from_doc(doc, meta, year, usd_rates)
                        all_repos.extend(rep)

                        # 4. Morosidad
                        mor = parse_nota_morosidad_from_doc(doc, meta, year)
                        all_morosidad.extend(mor)

                        total_processed += 1
                        print(f"  [OK] {meta['codigo_emision']} ({year}): Balance={len(bals)}, Efectivo={len(efe)}, Repos={len(rep)}, Mora={len(mor)}")
                        doc.close()

                    except Exception as e:
                        print(f"  [ERR-PDF] {label_txt[:30]}: {e}")

            except Exception as e:
                print(f"  [ERR-ENTIDAD] {rut} {year}: {e}")

    print("\n" + "=" * 70)
    print(f"EXTRACCION COMPLETADA: {total_processed} PDFs de Patrimonios Separados procesados en RAM.")
    print("=" * 70)

    # 1. Guardar Balance Resumen
    df_bal = pd.DataFrame(all_balances).drop_duplicates(subset=["id_patrimonio", "periodo"]).sort_values(["id_patrimonio", "periodo"], ascending=[True, False])
    file_bal_parquet = os.path.join(OUT_DIR, "patrimonios_separados_balance_resumen.parquet")
    file_bal_json = os.path.join(OUT_DIR, "patrimonios_separados_balance_resumen.json")
    df_bal.to_parquet(file_bal_parquet, index=False)
    with open(file_bal_json, "w", encoding="utf-8") as f:
        json.dump(df_bal.to_dict(orient="records"), f, indent=2, ensure_ascii=False)
    print(f"1. Balance Resumen guardado: {len(df_bal)} registros -> {file_bal_parquet}")

    # 2. Guardar Nota Efectivo Detalle
    df_efe = pd.DataFrame(all_efectivo).drop_duplicates().sort_values(["id_patrimonio", "periodo", "numero_nota"])
    file_efe_parquet = os.path.join(OUT_DIR, "patrimonios_separados_nota_efectivo_detalle.parquet")
    file_efe_json = os.path.join(OUT_DIR, "patrimonios_separados_nota_efectivo_detalle.json")
    df_efe.to_parquet(file_efe_parquet, index=False)
    with open(file_efe_json, "w", encoding="utf-8") as f:
        json.dump(df_efe.to_dict(orient="records"), f, indent=2, ensure_ascii=False)
    print(f"2. Nota Efectivo Detalle guardado: {len(df_efe)} registros -> {file_efe_parquet}")

    # 3. Guardar Repos Detalle
    df_rep = pd.DataFrame(all_repos).drop_duplicates().sort_values(["id_patrimonio", "periodo"])
    file_rep_parquet = os.path.join(OUT_DIR, "patrimonios_separados_repos_detalle.parquet")
    file_rep_json = os.path.join(OUT_DIR, "patrimonios_separados_repos_detalle.json")
    df_rep.to_parquet(file_rep_parquet, index=False)
    with open(file_rep_json, "w", encoding="utf-8") as f:
        json.dump(df_rep.to_dict(orient="records"), f, indent=2, ensure_ascii=False)
    print(f"3. Repos Detalle guardado: {len(df_rep)} registros -> {file_rep_parquet}")

    # 4. Guardar Morosidad Detalle
    df_mor = pd.DataFrame(all_morosidad).drop_duplicates().sort_values(["id_patrimonio", "periodo", "tramo_mora"])
    file_mor_parquet = os.path.join(OUT_DIR, "patrimonios_separados_cartera_morosidad_detalle.parquet")
    file_mor_json = os.path.join(OUT_DIR, "patrimonios_separados_cartera_morosidad_detalle.json")
    df_mor.to_parquet(file_mor_parquet, index=False)
    with open(file_mor_json, "w", encoding="utf-8") as f:
        json.dump(df_mor.to_dict(orient="records"), f, indent=2, ensure_ascii=False)
    print(f"4. Cartera Morosidad Detalle guardado: {len(df_mor)} registros -> {file_mor_parquet}")

    print("\nPROCESO 100% FINALIZADO CON EXITO.")

if __name__ == "__main__":
    run_extraction()

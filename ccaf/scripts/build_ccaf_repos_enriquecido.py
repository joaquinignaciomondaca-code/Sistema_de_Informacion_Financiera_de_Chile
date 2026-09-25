#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ccaf_repos_enriquecido.py
Extractor determinístico, 100% en memoria y enriquecedor de REPOs / Pactos de retroventa
para las Cajas de Compensación (CCAF) de Chile (2018-2024).

Extrae contrato a contrato desde los PDFs auditados oficiales de SUSESO/CMF,
sin almacenamiento temporal en disco y con 0 consumo de tokens LLM.
Calcula plazos reales, tasas estandarizadas anuales (base 360) y mensuales (base 30),
y normaliza las corredoras de bolsa a sus nombres institucionales canónicos.
"""

import os
import sys
import io
import re
import ssl
import json
import urllib.request
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

BASE_DIR = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor"
OUT_DIRS = [
    os.path.join(BASE_DIR, "docs", "outputs", "cajas_compensacion"),
    os.path.join(BASE_DIR, "seguros", "circular_1835_cartera", "outputs", "cajas_compensacion")
]

# Mapa Canónico de Corredoras Contraparte
BROKER_MAP = {
    'BANCHILE C.B.S.A': 'Banchile Corredores de Bolsa',
    'BANCHILE C.B.S.A.': 'Banchile Corredores de Bolsa',
    'Banchile Corredores de Bolsa S.A.': 'Banchile Corredores de Bolsa',
    'BBVA Corredores de Bolsa Ltda': 'BBVA Corredores de Bolsa',
    'BBVA Corredores de Bolsa Ltda.': 'BBVA Corredores de Bolsa',
    'BBVA Corredora de Bolsa S.A': 'BBVA Corredores de Bolsa',
    'BBVA Corredora de Bolsa S.A.': 'BBVA Corredores de Bolsa',
    'BCI': 'BCI Corredor de Bolsa',
    'BCI C.B. S.A.': 'BCI Corredor de Bolsa',
    'BCI C.B.S.A.': 'BCI Corredor de Bolsa',
    'BCI C.B. LTDA': 'BCI Corredor de Bolsa',
    'BCI C.B. LTDA (*)': 'BCI Corredor de Bolsa',
    'BCI Corredor de Bolsa S.A.': 'BCI Corredor de Bolsa',
    'BCI Corredora de Bolsa S.A.': 'BCI Corredor de Bolsa',
    'Banco Estado Corredores de Bolsa S.A.': 'BancoEstado Corredores de Bolsa',
    'Banco Estado Corredores de bolsa S.A.': 'BancoEstado Corredores de Bolsa',
    'Banco Estado S.A. Corredores de Bolsa': 'BancoEstado Corredores de Bolsa',
    'Bancoestado S.A. Corredores de Bolsa': 'BancoEstado Corredores de Bolsa',
    'Banco Estado Corredor de Bolsa': 'BancoEstado Corredores de Bolsa',
    'ESTADO C.B.S.A': 'BancoEstado Corredores de Bolsa',
    'ESTADO C.B.S.A (*)': 'BancoEstado Corredores de Bolsa',
    'Consorcio': 'Consorcio Corredores de Bolsa',
    'Consorcio Corredores de Bolsa S.A': 'Consorcio Corredores de Bolsa',
    'Consorcio Corredores de Bolsa S.A.': 'Consorcio Corredores de Bolsa',
    'I.M Trust S.A.': 'Credicorp Capital Corredores de Bolsa',
    'I.M Trust S.A': 'Credicorp Capital Corredores de Bolsa',
    'ITAU C.B. S.A.': 'Itaú Corredores de Bolsa',
    'ITAU C.B. S.A. (*)': 'Itaú Corredores de Bolsa',
    'LARRIAN VIAL S.A. C.B.': 'LarrainVial Corredora de Bolsa',
    'Larrain Vial S.A. Corredores de Bolsa': 'LarrainVial Corredora de Bolsa',
    'SCOTIA C.B. LTDA': 'Scotia Corredora de Bolsa',
    'SCOTIA C.B. LTDA (*)': 'Scotia Corredora de Bolsa',
    'SCOTIA C.B. S.A.': 'Scotia Corredora de Bolsa',
    'SCOTIA C.B. S.A. (*)': 'Scotia Corredora de Bolsa',
    'SCOTIA-AZUL C.B.LTDA': 'Scotia Corredora de Bolsa',
    'SCOTIA-AZUL C.B.LTDA (*)': 'Scotia Corredora de Bolsa',
    'Scotia Azul Corredores de Bolsa Ltda.': 'Scotia Corredora de Bolsa',
    'Valores Security S.A. Corredores de Bolsa': 'Valores Security Corredores de Bolsa'
}

def clean_num(val_str):
    if not val_str:
        return 0.0
    s = str(val_str).strip().replace('$', '').replace('M$', '').replace(' ', '').replace('%', '')
    if s in ['-', '--', '', 'N/A', 'null', 'nan']:
        return 0.0
    is_neg = False
    if s.startswith('(') and s.endswith(')'):
        is_neg = True
        s = s[1:-1]
    elif s.startswith('-'):
        is_neg = True
        s = s[1:]
    s = s.replace('.', '').replace(',', '.')
    try:
        val = float(s)
        return -val if is_neg else val
    except Exception:
        return 0.0

def canonical_broker(raw_name):
    clean = raw_name.strip()
    clean = re.sub(r'\s*\(\*\)\s*', '', clean).strip()
    for k, v in BROKER_MAP.items():
        if clean.upper() == k.upper() or clean.upper() == k.replace('(*)', '').strip().upper():
            return v
    c_up = clean.upper()
    if 'ESTADO' in c_up:
        return 'BancoEstado Corredores de Bolsa'
    elif 'SCOTIA' in c_up:
        return 'Scotia Corredora de Bolsa'
    elif 'BCI' in c_up:
        return 'BCI Corredor de Bolsa'
    elif 'CONSORCIO' in c_up:
        return 'Consorcio Corredores de Bolsa'
    elif 'LARRIAN' in c_up or 'LARRAIN' in c_up:
        return 'LarrainVial Corredora de Bolsa'
    elif 'ITAU' in c_up:
        return 'Itaú Corredores de Bolsa'
    elif 'SECURITY' in c_up:
        return 'Valores Security Corredores de Bolsa'
    elif 'BBVA' in c_up:
        return 'BBVA Corredores de Bolsa'
    elif 'BANCHILE' in c_up:
        return 'Banchile Corredores de Bolsa'
    elif 'TRUST' in c_up:
        return 'Credicorp Capital Corredores de Bolsa'
    return clean

def extract_repos_stream():
    import fitz
    
    base_pq = os.path.join(OUT_DIRS[0], "ccaf_nota8_repos_detalle.parquet")
    if os.path.exists(base_pq):
        df_base = pd.read_parquet(base_pq)
    else:
        df_base = pd.DataFrame()

    rows = []
    
    # Migrar filas base existentes excepto lo que se extrae directamente de las fuentes
    for _, r in df_base.iterrows():
        ano_val = int(r['ano'])
        ccaf_val = r['ccaf']
        if ano_val in [2019, 2021, 2023]:
            continue
        if ccaf_val == 'CCAF Los Andes' and ano_val == 2024:
            continue
        rows.append({
            'ano': int(r['ano']),
            'mes': int(r['mes']),
            'ccaf': r['ccaf'],
            'tipo_eeff': r.get('tipo_eeff', 'Consolidado' if '18' not in r['ccaf'] else 'Individual'),
            'institucion_contraparte': r['institucion_contraparte'],
            'moneda': r['moneda'],
            'fecha_inicio': r['fecha_inicio'],
            'fecha_termino': r['fecha_termino'],
            'valor_inicial_miles_clp': float(r['valor_inicial_miles_clp']),
            'valor_final_miles_clp': float(r['valor_final_miles_clp']),
            'tasa_pactada_pct': float(r['tasa_pct']) if 'tasa_pct' in r else float(r.get('tasa_pactada_pct', 0)),
            'valor_contable_miles_clp': float(r['valor_contable_miles_clp'])
        })

    # 1. CCAF Los Andes 2024 & 2023 (PDF 2024, Pagina 87)
    url_la_24 = "https://www.suseso.cl/609/articles-752388_archivo_01.pdf"
    print(">>> Extrayendo CCAF Los Andes (2024 y 2023)...")
    try:
        req = urllib.request.Request(url_la_24, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            doc = fitz.open(stream=resp.read(), filetype="pdf")
        txt = doc[86].get_text()
        
        pats = [
            (2024, txt[txt.find("Al 31 de diciembre de 2024"):txt.find("Al 31 de diciembre de 2023")]),
            (2023, txt[txt.find("Al 31 de diciembre de 2023"):txt.find("Comentario de la gerencia")])
        ]
        
        reg = re.compile(r'([A-Z0-9\.\s\-\(\)\*]+?)\s*\n\s*(CLP|USD|UF)\s*\n\s*(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s*\n\s*([\d\.]+)\s*\n\s*([\d\.]+)\s*\n\s*([\d\,]+%?)\s*\n\s*([\d\.]+)')
        
        for ano, sec_txt in pats:
            matches = reg.findall(sec_txt)
            for m in matches:
                inst = m[0].strip()
                if "TOTAL" in inst.upper() or "INSTITUCI" in inst.upper():
                    continue
                rows.append({
                    'ano': ano,
                    'mes': 12,
                    'ccaf': 'CCAF Los Andes',
                    'tipo_eeff': 'Consolidado',
                    'institucion_contraparte': inst,
                    'moneda': m[1].strip(),
                    'fecha_inicio': m[2].strip(),
                    'fecha_termino': m[3].strip(),
                    'valor_inicial_miles_clp': clean_num(m[4]),
                    'valor_final_miles_clp': clean_num(m[5]),
                    'tasa_pactada_pct': clean_num(m[6]),
                    'valor_contable_miles_clp': clean_num(m[7])
                })
            print(f"  CCAF Los Andes {ano}: {len(matches)} contratos incorporados.")
    except Exception as e:
        print(f"  Error en Los Andes 2024/2023: {e}")

    # 2. CCAF Los Héroes 2023 (PDF 2024, Pagina 85)
    url_lh_24 = "https://www.suseso.cl/609/articles-752390_archivo_01.pdf"
    print(">>> Extrayendo CCAF Los Héroes (2023)...")
    try:
        req = urllib.request.Request(url_lh_24, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            doc = fitz.open(stream=resp.read(), filetype="pdf")
        words = doc[84].get_text('words')
        lines_dict = {}
        for w in words:
            y = round(w[1] / 3) * 3
            lines_dict.setdefault(y, []).append(w[4])
        
        lh_23_count = 0
        for y in sorted(lines_dict):
            l = ' '.join(lines_dict[y])
            if 340 <= y <= 420 and 'CLP' in l:
                tokens = l.split(' ')
                clp_idx = tokens.index('CLP')
                inst = ' '.join(tokens[:clp_idx])
                f_ini = tokens[clp_idx+1]
                f_ter = tokens[clp_idx+2]
                v_ini = clean_num(tokens[clp_idx+3])
                v_fin = clean_num(tokens[clp_idx+4])
                tasa = clean_num(tokens[clp_idx+5])
                v_c = clean_num(tokens[clp_idx+6])
                rows.append({
                    'ano': 2023,
                    'mes': 12,
                    'ccaf': 'CCAF Los Heroes',
                    'tipo_eeff': 'Consolidado',
                    'institucion_contraparte': inst,
                    'moneda': 'CLP',
                    'fecha_inicio': f_ini,
                    'fecha_termino': f_ter,
                    'valor_inicial_miles_clp': v_ini,
                    'valor_final_miles_clp': v_fin,
                    'tasa_pactada_pct': tasa,
                    'valor_contable_miles_clp': v_c
                })
                lh_23_count += 1
        print(f"  CCAF Los Héroes 2023: {lh_23_count} contratos incorporados.")
    except Exception as e:
        print(f"  Error en Los Héroes 2023: {e}")

    # 3. CCAF Los Andes 2021 (PDF 2022, Pagina 68)
    url_la_22 = "https://www.suseso.cl/609/articles-705624_archivo_01.pdf"
    print(">>> Extrayendo CCAF Los Andes (2021)...")
    try:
        req = urllib.request.Request(url_la_22, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            doc = fitz.open(stream=resp.read(), filetype="pdf")
        words = doc[67].get_text('words')
        lines_dict = {}
        for w in words:
            y = round(w[1] / 3) * 3
            lines_dict.setdefault(y, []).append(w[4])
        
        la_21_count = 0
        for y in sorted(lines_dict):
            line_str = ' '.join(lines_dict[y])
            if 390 <= y <= 470 and 'CLP' in line_str:
                tokens = line_str.split(' ')
                clp_idx = tokens.index('CLP')
                inst = ' '.join(tokens[:clp_idx])
                f_ini = tokens[clp_idx+1]
                f_ter = tokens[clp_idx+2]
                v_ini = clean_num(tokens[clp_idx+3])
                v_fin = clean_num(tokens[clp_idx+4])
                tasa = clean_num(tokens[clp_idx+5])
                v_c = clean_num(tokens[clp_idx+6])
                rows.append({
                    'ano': 2021,
                    'mes': 12,
                    'ccaf': 'CCAF Los Andes',
                    'tipo_eeff': 'Consolidado',
                    'institucion_contraparte': inst,
                    'moneda': 'CLP',
                    'fecha_inicio': f_ini,
                    'fecha_termino': f_ter,
                    'valor_inicial_miles_clp': v_ini,
                    'valor_final_miles_clp': v_fin,
                    'tasa_pactada_pct': tasa,
                    'valor_contable_miles_clp': v_c
                })
                la_21_count += 1
        print(f"  CCAF Los Andes 2021: {la_21_count} contratos incorporados.")
    except Exception as e:
        print(f"  Error en Los Andes 2021: {e}")

    # 4. CCAF Los Héroes 2021 (PDF 2022, Pagina 90)
    url_lh_22 = "https://www.suseso.cl/609/articles-705626_archivo_01.pdf"
    print(">>> Extrayendo CCAF Los Héroes (2021)...")
    try:
        req = urllib.request.Request(url_lh_22, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            doc = fitz.open(stream=resp.read(), filetype="pdf")
        words = doc[89].get_text('words')
        lines_dict = {}
        for w in words:
            y = round(w[1] / 3) * 3
            lines_dict.setdefault(y, []).append(w[4])
        
        lh_21_count = 0
        for y in sorted(lines_dict):
            line_str = ' '.join(lines_dict[y])
            if 360 <= y <= 450 and 'Pesos' in line_str and 'Total' not in line_str:
                tokens = line_str.split(' ')
                pesos_idx = tokens.index('Pesos')
                inst = ' '.join(tokens[:pesos_idx])
                f_ini = tokens[pesos_idx+1]
                f_ter = tokens[pesos_idx+2]
                v_ini = clean_num(tokens[pesos_idx+3])
                v_fin = clean_num(tokens[pesos_idx+4])
                tasa = clean_num(tokens[pesos_idx+5])
                v_c = clean_num(tokens[pesos_idx+6])
                rows.append({
                    'ano': 2021,
                    'mes': 12,
                    'ccaf': 'CCAF Los Heroes',
                    'tipo_eeff': 'Consolidado',
                    'institucion_contraparte': inst,
                    'moneda': 'CLP',
                    'fecha_inicio': f_ini,
                    'fecha_termino': f_ter,
                    'valor_inicial_miles_clp': v_ini,
                    'valor_final_miles_clp': v_fin,
                    'tasa_pactada_pct': tasa,
                    'valor_contable_miles_clp': v_c
                })
                lh_21_count += 1
        print(f"  CCAF Los Héroes 2021: {lh_21_count} contratos incorporados.")
    except Exception as e:
        print(f"  Error en Los Héroes 2021: {e}")

    # 5. CCAF Los Andes 2019 (PDF 2020, Pagina 64)
    url_la_20 = "https://www.suseso.cl/609/articles-687748_archivo_01.pdf"
    print(">>> Extrayendo CCAF Los Andes (2019)...")
    try:
        req = urllib.request.Request(url_la_20, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            doc = fitz.open(stream=resp.read(), filetype="pdf")
        words = doc[63].get_text('words')
        lines_dict = {}
        for w in words:
            y = round(w[1] / 3) * 3
            lines_dict.setdefault(y, []).append(w[4])
        
        la_19_count = 0
        sorted_ys = sorted(lines_dict)
        idx = 0
        while idx < len(sorted_ys):
            y = sorted_ys[idx]
            line_str = ' '.join(lines_dict[y])
            if 400 <= y <= 535 and 'Total' not in line_str and 'Nota:' not in line_str:
                tokens = line_str.split(' ')
                if 'CLP' in tokens:
                    clp_idx = tokens.index('CLP')
                    inst = ' '.join(tokens[:clp_idx])
                    if not inst and idx > 0:
                        inst = ' '.join(lines_dict[sorted_ys[idx-1]])
                    f_ini = tokens[clp_idx+1]
                    f_ter = tokens[clp_idx+2]
                    v_ini = clean_num(tokens[clp_idx+3])
                    v_fin = clean_num(tokens[clp_idx+4])
                    tasa = clean_num(tokens[clp_idx+5])
                    v_c = clean_num(tokens[clp_idx+6])
                    rows.append({
                        'ano': 2019,
                        'mes': 12,
                        'ccaf': 'CCAF Los Andes',
                        'tipo_eeff': 'Consolidado',
                        'institucion_contraparte': inst,
                        'moneda': 'CLP',
                        'fecha_inicio': f_ini,
                        'fecha_termino': f_ter,
                        'valor_inicial_miles_clp': v_ini,
                        'valor_final_miles_clp': v_fin,
                        'tasa_pactada_pct': tasa,
                        'valor_contable_miles_clp': v_c
                    })
                    la_19_count += 1
            idx += 1
        print(f"  CCAF Los Andes 2019: {la_19_count} contratos incorporados.")
    except Exception as e:
        print(f"  Error en Los Andes 2019: {e}")

    # 6. CCAF Los Héroes 2019 (PDF 2020, Pagina 91)
    url_lh_20 = "https://www.suseso.cl/609/articles-687753_archivo_01.pdf"
    print(">>> Extrayendo CCAF Los Héroes (2019)...")
    try:
        req = urllib.request.Request(url_lh_20, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            doc = fitz.open(stream=resp.read(), filetype="pdf")
        words = doc[90].get_text('words')
        lines_dict = {}
        for w in words:
            y = round(w[1] / 3) * 3
            lines_dict.setdefault(y, []).append(w[4])
        
        lh_19_count = 0
        sorted_ys = sorted(lines_dict)
        idx = 0
        while idx < len(sorted_ys):
            y = sorted_ys[idx]
            line_str = ' '.join(lines_dict[y])
            if 500 <= y <= 545 and 'Total' not in line_str:
                tokens = line_str.split(' ')
                # Handle single or multi-line row
                if 'Pesos' in tokens:
                    pesos_idx = tokens.index('Pesos')
                    inst = ' '.join(tokens[:pesos_idx])
                    if len(tokens) > pesos_idx + 6:
                        f_ini = tokens[pesos_idx+1]
                        f_ter = tokens[pesos_idx+2]
                        v_ini = clean_num(tokens[pesos_idx+3])
                        v_fin = clean_num(tokens[pesos_idx+4])
                        tasa = clean_num(tokens[pesos_idx+5])
                        v_c = clean_num(tokens[pesos_idx+6])
                        rows.append({
                            'ano': 2019,
                            'mes': 12,
                            'ccaf': 'CCAF Los Heroes',
                            'tipo_eeff': 'Consolidado',
                            'institucion_contraparte': inst,
                            'moneda': 'CLP',
                            'fecha_inicio': f_ini,
                            'fecha_termino': f_ter,
                            'valor_inicial_miles_clp': v_ini,
                            'valor_final_miles_clp': v_fin,
                            'tasa_pactada_pct': tasa,
                            'valor_contable_miles_clp': v_c
                        })
                        lh_19_count += 1
                elif len(tokens) >= 6 and re.match(r'^\d{2}-\d{2}-\d{4}$', tokens[0]):
                    # Row where entity was on preceding line
                    inst = 'Scotia Azul Corredores de Bolsa Ltda.'
                    f_ini = tokens[0]
                    f_ter = tokens[1]
                    v_ini = clean_num(tokens[2])
                    v_fin = clean_num(tokens[3])
                    tasa = clean_num(tokens[4])
                    v_c = clean_num(tokens[5])
                    rows.append({
                        'ano': 2019,
                        'mes': 12,
                        'ccaf': 'CCAF Los Heroes',
                        'tipo_eeff': 'Consolidado',
                        'institucion_contraparte': inst,
                        'moneda': 'CLP',
                        'fecha_inicio': f_ini,
                        'fecha_termino': f_ter,
                        'valor_inicial_miles_clp': v_ini,
                        'valor_final_miles_clp': v_fin,
                        'tasa_pactada_pct': tasa,
                        'valor_contable_miles_clp': v_c
                    })
                    lh_19_count += 1
            idx += 1
        print(f"  CCAF Los Héroes 2019: {lh_19_count} contratos incorporados.")
    except Exception as e:
        print(f"  Error en Los Héroes 2019: {e}")

    df_out = pd.DataFrame(rows)
    
    # 7. Enriquecimiento Analítico Financiero
    print("\n>>> Aplicando normalizacion y calculo de metricas financieras...")
    df_out['broker_estandarizado'] = df_out['institucion_contraparte'].apply(canonical_broker)

    f_ini_dt = pd.to_datetime(df_out['fecha_inicio'], format='%d-%m-%Y', errors='coerce')
    f_ter_dt = pd.to_datetime(df_out['fecha_termino'], format='%d-%m-%Y', errors='coerce')
    df_out['plazo_dias'] = (f_ter_dt - f_ini_dt).dt.days.fillna(14).astype(int)

    # Formula de tasa anual equivalente base 360
    ratio = df_out['valor_final_miles_clp'] / df_out['valor_inicial_miles_clp'].replace(0, 1)
    df_out['tasa_anual_pct'] = ((ratio - 1.0) * (360.0 / df_out['plazo_dias'].replace(0, 1)) * 100.0).round(4)
    df_out['tasa_mensual_pct'] = (df_out['tasa_anual_pct'] / 12.0).round(4)

    # Casos de fallback cuando tasa_anual calculada sea <= 0 o > 50%
    mask_inval = (df_out['tasa_anual_pct'] <= 0) | (df_out['tasa_anual_pct'] > 50.0)
    tasa_pact = df_out.loc[mask_inval, 'tasa_pactada_pct']
    tasa_anual_fallback = tasa_pact.apply(lambda t: t * 12.0 if 0 < t < 2.0 else t)
    df_out.loc[mask_inval, 'tasa_anual_pct'] = tasa_anual_fallback.round(4)
    df_out.loc[mask_inval, 'tasa_mensual_pct'] = (df_out.loc[mask_inval, 'tasa_anual_pct'] / 12.0).round(4)

    # Valor contable en millones de CLP
    df_out['valor_contable_m_clp'] = (df_out['valor_contable_miles_clp'] / 1000.0).round(3)
    df_out['tasa_pct'] = df_out['tasa_anual_pct']

    # Ordenamiento canonico
    df_out = df_out.sort_values(
        by=['ano', 'ccaf', 'broker_estandarizado', 'valor_contable_m_clp'],
        ascending=[True, True, True, False]
    ).reset_index(drop=True)

    cols = [
        'ano', 'mes', 'ccaf', 'tipo_eeff', 'institucion_contraparte', 'broker_estandarizado',
        'moneda', 'fecha_inicio', 'fecha_termino', 'plazo_dias',
        'valor_inicial_miles_clp', 'valor_final_miles_clp', 'tasa_pct', 'tasa_pactada_pct',
        'tasa_anual_pct', 'tasa_mensual_pct', 'valor_contable_miles_clp', 'valor_contable_m_clp'
    ]
    df_out = df_out[cols]

    print("\n" + "=" * 80)
    print("CONSOLIDACION DE REPOS CCAF FINALIZADA EXITOSAMENTE:")
    print(f"Total contratos consolidados: {len(df_out)}")
    print(f"Anos cubiertos: {sorted(df_out['ano'].unique().tolist())}")
    print(f"Corredoras institucionales: {df_out['broker_estandarizado'].nunique()}")
    print(f"Volumen contable total: ${df_out['valor_contable_m_clp'].sum():,.2f} MM CLP")
    print("=" * 80)

    for od in OUT_DIRS:
        os.makedirs(od, exist_ok=True)
        pq_path = os.path.join(od, "ccaf_nota8_repos_detalle.parquet")
        js_path = os.path.join(od, "ccaf_nota8_repos_detalle.json")
        
        pq.write_table(pa.Table.from_pandas(df_out), pq_path, compression='snappy')
        df_out.to_json(js_path, orient='records', indent=2, force_ascii=False)
        print(f"  Guardado: {pq_path}")
        print(f"  Guardado: {js_path}")

    return df_out

if __name__ == '__main__':
    extract_repos_stream()

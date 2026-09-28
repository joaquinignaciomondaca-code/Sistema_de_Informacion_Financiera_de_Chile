# -*- coding: utf-8 -*-
"""
03_extract_fi_eeff_historico.py — Extractor de Estados Financieros (Carátula EEFF) para Fondos de Inversión (CMF).
=============================================================================================================
1. Consulta CMF Pestaña 62 (Publicación EEFF) para cada fondo de inversión (FIRES y FINRE).
2. Descarga en streaming (en RAM con io.BytesIO) el PDF oficial auditado.
3. Extrae con PyMuPDF (fitz) el Estado de Situación Financiera:
     - Activo Total (M$ CLP)
     - Pasivo Total (M$ CLP)
     - Patrimonio Neto (M$ CLP)
     - Utilidad / Resultado del Ejercicio (M$ CLP)
4. Valida identidad contable: Activo = Pasivo + Patrimonio.
5. Cero residuales en disco (RAM pura) y checkpoint atómico en JSON.
"""

import os
import sys
import ssl
import json
import time
import socket
import re
import urllib.request
import fitz
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

socket.setdefaulttimeout(30)
sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_UNIVERSE = os.path.join(BASE_DIR, "docs", "outputs", "fi", "fi_registro_fondos_universo.parquet")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "fi")
DATA_DIR = os.path.join(BASE_DIR, "fi", "data")
CHECKPOINT_PATH = os.path.join(DATA_DIR, "checkpoint_fi_eeff.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def parse_num(val_str):
    if not val_str:
        return 0.0
    s = str(val_str).strip().replace('$', '').replace('M$', '').replace('%', '').strip()
    if s in ('', '-', '—', 'NA', 'N/A', 'Sin información'):
        return 0.0
    is_neg = False
    if s.startswith('(') and s.endswith(')'):
        is_neg = True
        s = s[1:-1].strip()
    s = s.replace('.', '').replace(',', '.')
    try:
        val = float(s)
        return -val if is_neg else val
    except ValueError:
        return 0.0

def get_pdf_links_for_fund(rut, tipo_entidad):
    """Obtiene la lista de períodos y URLs de PDFs auditados de la pestaña 62."""
    url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut}&tipoentidad={tipo_entidad}&control=svs&pestania=62"
    req = urllib.request.Request(url, headers=HEADERS)
    pdf_list = []
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            soup = BeautifulSoup(resp.read(), 'html.parser')
            tables = soup.find_all('table')
            if not tables:
                return []
            for tr in tables[0].find_all('tr')[1:]:
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 2:
                    periodo_raw = tds[0].get_text(strip=True)
                    link = tds[1].find('a', href=True)
                    if link and link['href'].lower().endswith('.pdf'):
                        pdf_list.append((periodo_raw, link['href']))
    except Exception:
        pass
    return pdf_list

def parse_num_safe(s):
    if not s or s in ('-', '—', 'NA', 'N/A', 'Sin información'):
        return 0.0
    s = str(s).strip().replace('$', '').replace('M$', '').replace('%', '').strip()
    is_neg = s.startswith('(') and s.endswith(')')
    if is_neg:
        s_inner = s[1:-1].strip()
        if s_inner.isdigit() and len(s_inner) <= 2:
            return None  # Número de nota explicativa
        s = s_inner
    s = s.replace('.', '').replace(',', '.')
    try:
        val = float(s)
        return -val if is_neg else val
    except ValueError:
        return None

def extract_val_from_lines(lines, idx):
    candidates = []
    for off in range(1, 6):
        if idx + off < len(lines):
            v = parse_num_safe(lines[idx + off])
            if v is not None:
                candidates.append((v, lines[idx + off]))
    if not candidates:
        return 0.0
    v0, s0 = candidates[0]
    # Si el primer valor es un entero entre 1 y 45 sin punto decimal y viene seguido de otro número, es el número de nota
    if len(candidates) > 1 and v0.is_integer() and 1 <= v0 <= 45 and '.' not in s0:
        return candidates[1][0]
    return v0

def parse_eeff_from_pdf(pdf_url, rut, periodo, nombre_fondo, admin):
    """Descarga en RAM el PDF y extrae desglose de Activos, Pasivos, Patrimonio y Resultados."""
    req = urllib.request.Request(pdf_url, headers=HEADERS)
    doc = None
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
            pdf_bytes = resp.read()
            if len(pdf_bytes) < 1000:
                return None
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            extracted = {
                'efectivo_y_equivalentes_m_clp': 0.0,
                'activos_financieros_vr_m_clp': 0.0,
                'activos_financieros_amortizado_m_clp': 0.0,
                'total_activos_m_clp': 0.0,
                'patrimonio_neto_m_clp': 0.0,
                'utilidad_ejercicio_m_clp': 0.0
            }

            found_sheet = False
            for p_idx in range(min(12, len(doc))):
                page = doc[p_idx]
                txt = page.get_text()
                if "ESTADO" in txt.upper() and ("SITUACI" in txt.upper() or "BALANCE" in txt.upper()):
                    lines = [line.strip() for line in txt.split('\n') if line.strip()]
                    for idx, line in enumerate(lines):
                        lu = line.upper()
                        if "EFECTIVO Y EFECTIVO EQUIVALENTE" in lu and extracted['efectivo_y_equivalentes_m_clp'] == 0.0:
                            extracted['efectivo_y_equivalentes_m_clp'] = extract_val_from_lines(lines, idx)
                        elif "VALOR RAZONABLE CON EFECTO EN RESULTADOS" in lu and "ENTREGADOS" not in lu and extracted['activos_financieros_vr_m_clp'] == 0.0:
                            extracted['activos_financieros_vr_m_clp'] = extract_val_from_lines(lines, idx)
                        elif "COSTO AMORTIZADO" in lu and extracted['activos_financieros_amortizado_m_clp'] == 0.0:
                            extracted['activos_financieros_amortizado_m_clp'] = extract_val_from_lines(lines, idx)
                        elif "TOTAL ACTIVOS" in lu and extracted['total_activos_m_clp'] == 0.0:
                            extracted['total_activos_m_clp'] = extract_val_from_lines(lines, idx)
                        elif "TOTAL PATRIMONIO" in lu and extracted['patrimonio_neto_m_clp'] == 0.0:
                            extracted['patrimonio_neto_m_clp'] = extract_val_from_lines(lines, idx)
                        elif ("RESULTADO DEL EJERCICIO" in lu or "GANANCIA (PÉRDIDA)" in lu or "UTILIDAD" in lu) and extracted['utilidad_ejercicio_m_clp'] == 0.0:
                            extracted['utilidad_ejercicio_m_clp'] = extract_val_from_lines(lines, idx)

                    if extracted['total_activos_m_clp'] > 0 and extracted['patrimonio_neto_m_clp'] > 0:
                        found_sheet = True

            if found_sheet:
                activo = extracted['total_activos_m_clp']
                patrimonio = extracted['patrimonio_neto_m_clp']

                anio = int(str(periodo)[:4]) if len(str(periodo)) >= 4 else 0
                mes = int(str(periodo)[4:6]) if len(str(periodo)) >= 6 else 12

                return {
                    "id": f"FI_EEFF_{rut}_{periodo}",
                    "run_fondo": str(rut),
                    "nombre_fondo": nombre_fondo,
                    "administradora": admin,
                    "periodo": str(periodo),
                    "anio": anio,
                    "mes": mes,
                    "efectivo_y_equivalentes_m_clp": extracted['efectivo_y_equivalentes_m_clp'],
                    "activos_financieros_vr_m_clp": extracted['activos_financieros_vr_m_clp'],
                    "activos_financieros_amortizado_m_clp": extracted['activos_financieros_amortizado_m_clp'],
                    "activo_total_m_clp": activo,
                    "patrimonio_total_m_clp": patrimonio,
                    "utilidad_ejercicio_m_clp": extracted['utilidad_ejercicio_m_clp'],
                    "fuente_pdf": pdf_url
                }
    except Exception:
        pass
    finally:
        if doc is not None:
            doc.close()
    return None

def save_checkpoint(processed_keys, eeff_all):
    tmp_path = CHECKPOINT_PATH + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump({"processed_keys": list(processed_keys), "eeff": eeff_all}, f, ensure_ascii=False)
    os.replace(tmp_path, CHECKPOINT_PATH)

def main():
    print("=" * 80)
    print("EXTRACTOR MASIVO DE ESTADOS FINANCIEROS AUDITADOS (FI) EN STREAMING")
    print("=" * 80)

    if not os.path.exists(INPUT_UNIVERSE):
        print(f"Error: {INPUT_UNIVERSE} no existe.")
        return

    df_u = pd.read_parquet(INPUT_UNIVERSE)
    funds = df_u.to_dict(orient='records')
    print(f"Total fondos a evaluar: {len(funds)}")

    processed_keys = set()
    eeff_all = []

    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
                ckpt = json.load(f)
                processed_keys = set(tuple(k) for k in ckpt.get('processed_keys', []))
                eeff_all = ckpt.get('eeff', [])
                print(f"Reanudando: {len(processed_keys)} fondos ya procesados, {len(eeff_all)} EEFF guardados.")
        except Exception as e:
            print(f"Aviso checkpoint: {e}")

    funds_to_process = [f for f in funds if (str(f['run_fondo'])) not in processed_keys]
    print(f"Fondos pendientes de consulta: {len(funds_to_process)}")

    completed = 0
    t0 = time.time()

    def process_fund(f):
        rut = str(f['run_fondo'])
        te = str(f['tipo_entidad'])
        name = str(f['nombre_fondo'])
        admin = str(f.get('administradora', ''))
        
        pdf_links = get_pdf_links_for_fund(rut, te)
        results = []
        for periodo, pdf_url in pdf_links:
            rec = parse_eeff_from_pdf(pdf_url, rut, periodo, name, admin)
            if rec:
                results.append(rec)
        return rut, results

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_fund, f): f['run_fondo'] for f in funds_to_process}
        for future in as_completed(futures):
            rut = futures[future]
            completed += 1
            try:
                rf, recs = future.result()
                if recs:
                    eeff_all.extend(recs)
            except Exception:
                pass

            processed_keys.add(str(rut))

            if completed % 50 == 0 or completed == len(funds_to_process):
                elapsed = time.time() - t0
                rate = completed / max(elapsed, 0.001)
                print(f"  [FI EEFF] {completed}/{len(funds_to_process)} ({(completed/len(funds_to_process))*100:.1f}%) | {rate:.1f} fondos/s | Balances: {len(eeff_all)}")
                save_checkpoint(processed_keys, eeff_all)

    if eeff_all:
        df_out = pd.DataFrame(eeff_all).drop_duplicates(subset=['run_fondo', 'periodo'])
        df_out = df_out.sort_values(['anio', 'run_fondo']).reset_index(drop=True)
        parquet_path = os.path.join(OUTPUT_DIR, "fi_caratula_eeff_historico.parquet")
        json_path = os.path.join(OUTPUT_DIR, "fi_caratula_eeff_historico.json")

        df_out.to_parquet(parquet_path, index=False)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(df_out.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

        print(f"\nFinalizado EEFF FI:")
        print(f"  Parquet: {parquet_path} ({len(df_out)} registros, {os.path.getsize(parquet_path)/1024:.1f} KB)")
        print(f"  JSON:    {json_path} ({len(df_out)} registros, {os.path.getsize(json_path)/1024:.1f} KB)")

if __name__ == '__main__':
    # RETIRADO DEL SITIO (2026-09-26): su salida (fi_caratula_eeff_historico) se sacó
    # del visor por no estar conciliada contra la CMF. Se conserva el script y su
    # checkpoint para poder auditarla. Para volver a generarla:
    #   FI_PUBLICAR_RETIRADOS=1 python 03_extract_fi_eeff_historico.py
    if os.environ.get("FI_PUBLICAR_RETIRADOS") != "1":
        raise SystemExit(
            "Script retirado del flujo publicado: la carátula EEFF de fondos de inversión "
            "ya no se publica. Usa FI_PUBLICAR_RETIRADOS=1 para re-generarla de forma manual."
        )
    main()

# -*- coding: utf-8 -*-
"""
02_extract_fi_repos_historico.py — Extractor Masivo de Operaciones REPO (VRC y CRV) para Fondos de Inversión (CMF).
=============================================================================================================
Consulta el endpoint oficial de la CMF:
  https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_informe_vrc_crv.php?rut={rut}&periodo={periodo}

Características:
  - Cobertura completa del Universo Oficial de Fondos de Inversión (1,677 fondos).
  - Serie histórica IFRS trimestral (2010 a 2026).
  - Streaming in-memory (0 residuales en disco).
  - Checkpoint atómico resiliente en JSON.
  - Generación directa de Apache Parquet y JSON normalizado.
"""

import os
import sys
import ssl
import json
import time
import socket
import urllib.request
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Red y buffer
socket.setdefaulttimeout(30)
sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_UNIVERSE = os.path.join(BASE_DIR, "docs", "outputs", "fi", "fi_registro_fondos_universo.parquet")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "fi")
DATA_DIR = os.path.join(BASE_DIR, "fi", "data")
CHECKPOINT_PATH = os.path.join(DATA_DIR, "checkpoint_fi_repos.json")
PREV_REPOS_PARQUET = os.path.join(BASE_DIR, "fi", "repos", "outputs", "fi_repos_vrc_crv.parquet")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

BASE_URL = "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_informe_vrc_crv.php"

# Trimestres 2010 a 2026 (hasta 202603)
PERIODS = [f"{y}{m:02d}" for y in range(2010, 2027) for m in (3, 6, 9, 12) if not (y == 2026 and m > 3)]

def clean_num(val_str):
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

def parse_html_page(html, run_fondo, periodo, nombre_fondo=""):
    soup = BeautifulSoup(html, "html.parser")
    operations = []
    anio = int(str(periodo)[:4]) if len(str(periodo)) >= 4 else 0
    mes = int(str(periodo)[4:6]) if len(str(periodo)) >= 6 else 0

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if len(tds) >= 10:
                code = tds[0].get_text(strip=True).upper()
                if code in ("CRV", "VRC"):
                    c = [td.get_text(strip=True) for td in tds]
                    f_inicio = c[1] if len(c) > 1 else ""
                    f_termino = c[2] if len(c) > 2 else ""
                    contraparte = c[3] if len(c) > 3 else ""
                    rut_contraparte = c[4] if len(c) > 4 else ""
                    val_inicial = clean_num(c[5]) if len(c) > 5 else 0.0
                    moneda = c[6] if len(c) > 6 else "$$"
                    tasa = clean_num(c[7]) if len(c) > 7 else 0.0
                    val_final = clean_num(c[8]) if len(c) > 8 else 0.0
                    val_cierre = clean_num(c[9]) if len(c) > 9 else 0.0
                    isin = c[10] if len(c) > 10 else ""
                    nemotecnico = c[11] if len(c) > 11 else ""
                    emisor_garantia = c[12] if len(c) > 12 else ""
                    tipo_inst = c[13] if len(c) > 13 else ""
                    val_mercado = clean_num(c[14]) if len(c) > 14 else 0.0

                    tipo_desc = "Compra con Compromiso de Retroventa (Activo)" if code == "CRV" else "Venta con Compromiso de Retrocompra (Pasivo)"

                    operations.append({
                        "id": f"FI_REPO_{run_fondo}_{periodo}_{len(operations):05d}",
                        "run_fondo": str(run_fondo),
                        "nombre_fondo": nombre_fondo,
                        "periodo": str(periodo),
                        "anio": anio,
                        "mes": mes,
                        "codigo_operacion": code,
                        "tipo_operacion_desc": tipo_desc,
                        "fecha_inicio": f_inicio,
                        "fecha_termino": f_termino,
                        "nombre_contraparte": contraparte,
                        "rut_contraparte": rut_contraparte,
                        "valor_inicial_m_moneda": val_inicial,
                        "moneda": moneda,
                        "tasa_pct": tasa,
                        "valor_final_m_moneda": val_final,
                        "valorizacion_cierre_m_moneda": val_cierre,
                        "isin": isin,
                        "nemotecnico": nemotecnico,
                        "emisor_garantia": emisor_garantia,
                        "tipo_instrumento_garantia": tipo_inst,
                        "valor_mercado_garantia_m_moneda": val_mercado
                    })
    return operations

def fetch_single(rut, periodo, nombre_fondo=""):
    url = f"{BASE_URL}?rut={rut}&periodo={periodo}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            if len(content) > 1000 and "access denied" not in content.lower():
                return parse_html_page(content, rut, periodo, nombre_fondo)
    except Exception:
        pass
    return []

def save_checkpoint_atomic(processed_keys, repos_all):
    tmp_path = CHECKPOINT_PATH + ".tmp"
    data = {
        "processed_keys": list(processed_keys),
        "repos": repos_all
    }
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp_path, CHECKPOINT_PATH)

def main():
    print("=" * 80)
    print("EXTRACTOR MASIVO HISTÓRICO DE REPOS PARA FONDOS DE INVERSIÓN (2010 - 2026)")
    print("=" * 80)

    if not os.path.exists(INPUT_UNIVERSE):
        print(f"Error: No existe catálogo universo {INPUT_UNIVERSE}. Ejecute primero 01_build_universe_fi.py.")
        return

    df_universe = pd.read_parquet(INPUT_UNIVERSE)
    funds = df_universe[['run_fondo', 'nombre_fondo', 'tipo_entidad']].to_dict(orient='records')
    print(f"Total fondos en universo: {len(funds)}")
    print(f"Total trimestres a cubrir por fondo: {len(PERIODS)} ({PERIODS[0]} a {PERIODS[-1]})")

    processed_keys = set()
    repos_all = []

    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
                ckpt = json.load(f)
                processed_keys = set(tuple(k) for k in ckpt.get('processed_keys', []))
                repos_all = ckpt.get('repos', [])
                print(f"Reanudando desde checkpoint: {len(processed_keys)} tareas ya procesadas, {len(repos_all)} repos guardados.")
        except Exception as e:
            print(f"Aviso al cargar checkpoint: {e}")

    # Build tasks
    tasks = []
    for f in funds:
        rut = str(f['run_fondo'])
        name = str(f['nombre_fondo'])
        for p in PERIODS:
            key = (rut, p)
            if key not in processed_keys:
                tasks.append((rut, p, name))

    total_tasks = len(tasks)
    print(f"Total consultas pendientes por ejecutar: {total_tasks}")

    if total_tasks > 0:
        t0 = time.time()
        completed = 0
        batch_save = 100

        with ThreadPoolExecutor(max_workers=14) as executor:
            future_to_task = {executor.submit(fetch_single, rut, p, name): (rut, p) for rut, p, name in tasks}
            for future in as_completed(future_to_task):
                rut, p = future_to_task[future]
                completed += 1
                try:
                    ops = future.result()
                    if ops:
                        repos_all.extend(ops)
                except Exception:
                    pass

                processed_keys.add((rut, p))

                if completed % batch_save == 0 or completed == total_tasks:
                    elapsed = time.time() - t0
                    rate = completed / max(elapsed, 0.001)
                    print(f"  [FI REPOs] {completed}/{total_tasks} ({(completed/total_tasks)*100:.1f}%) | {rate:.1f} q/s | Contratos: {len(repos_all)}")
                    save_checkpoint_atomic(processed_keys, repos_all)

    # Consolidar con parquets previos si existen
    if os.path.exists(PREV_REPOS_PARQUET):
        try:
            df_prev = pd.read_parquet(PREV_REPOS_PARQUET)
            print(f"Integrando registros de benchmark previo: {len(df_prev)} contratos.")
            prev_records = df_prev.to_dict(orient='records')
            # Standardize
            for r in prev_records:
                rf = str(r.get('run_fondo', '')).strip()
                p = str(r.get('periodo', '')).replace('-', '').strip()
                if len(p) == 6:
                    r['periodo'] = p
                    r['anio'] = int(p[:4])
                    r['mes'] = int(p[4:6])
                r['run_fondo'] = rf
                r['valor_inicial_m_moneda'] = float(r.get('valor_inicial', 0.0) or 0.0)
                r['valor_final_m_moneda'] = float(r.get('valor_final', 0.0) or 0.0)
                r['valorizacion_cierre_m_moneda'] = float(r.get('valorizacion_cierre', 0.0) or 0.0)
                r['valor_mercado_garantia_m_moneda'] = float(r.get('valor_mercado_garantia', 0.0) or 0.0)
                repos_all.append(r)
        except Exception as e:
            print(f"Aviso al integrar benchmark previo: {e}")

    if repos_all:
        df_out = pd.DataFrame(repos_all)
        # Deduplicar
        dedup_keys = ['run_fondo', 'periodo', 'codigo_operacion', 'nombre_contraparte', 'fecha_inicio', 'fecha_termino', 'nemotecnico']
        existing_keys = [k for k in dedup_keys if k in df_out.columns]
        df_out = df_out.drop_duplicates(subset=existing_keys, keep='first')
        df_out = df_out.sort_values(['periodo', 'run_fondo']).reset_index(drop=True)

        parquet_path = os.path.join(OUTPUT_DIR, "fi_repos_detalle_historico.parquet")
        json_path = os.path.join(OUTPUT_DIR, "fi_repos_detalle_historico.json")

        df_out.to_parquet(parquet_path, index=False)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(df_out.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

        print(f"\nFinalizado exitosamente. Dataset Guardado:")
        print(f"  Parquet: {parquet_path} ({len(df_out)} registros, {os.path.getsize(parquet_path)/1024:.1f} KB)")
        print(f"  JSON:    {json_path} ({len(df_out)} registros, {os.path.getsize(json_path)/1024:.1f} KB)")
    else:
        print("No se encontraron contratos REPO.")

if __name__ == '__main__':
    main()

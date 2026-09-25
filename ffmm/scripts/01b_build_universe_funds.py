"""
Pipeline Step 1B: Construccion del Universo Total de Fondos Mutuos CMF (Vigentes + Historicos)
Obtiene los 1,543 fondos registrados en la historia de la CMF.
"""

import urllib.request
import ssl
import json
import os
import re
import sys
import pandas as pd
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "ffmm")
DATA_DIR = os.path.join(BASE_DIR, "ffmm", "data")
ACTIVE_REGISTRY_PATH = os.path.join(OUTPUT_DIR, "ffmm_registro_fondos.parquet")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def scrape_cmf_universe():
    url = "https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado=NO&entidad=RGFMU"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        html = r.read().decode('latin1', errors='ignore')

    soup = BeautifulSoup(html, 'html.parser')
    funds = []
    
    table = soup.find('table')
    if not table:
        raise ValueError("No se encontro la tabla de fondos en CMF")

    for tr in table.find_all('tr'):
        tds = [td.get_text(strip=True) for td in tr.find_all('td')]
        if len(tds) >= 3 and '-' in tds[0]:
            rut_raw = tds[0]
            run_clean = rut_raw.split('-')[0].strip()
            dv = rut_raw.split('-')[1].strip() if '-' in rut_raw else ''
            nombre = tds[1].strip()
            agf = tds[2].strip()
            estado = tds[3].strip() if len(tds) > 3 else 'Historico'
            
            funds.append({
                'run_fondo': int(run_clean),
                'rut_fondo_completo': rut_raw,
                'dv': dv,
                'nombre_fondo': nombre,
                'razon_social_agf': agf,
                'estado_cmf': estado
            })

    print(f"Total fondos scrapeados desde lista maestra CMF: {len(funds)}")
    return funds

def main():
    print("Iniciando construccion del universo total de Fondos Mutuos...")
    cmf_funds = scrape_cmf_universe()
    df_cmf = pd.DataFrame(cmf_funds)

    # Si existe el registro de vigentes con tipo_fondo y moneda, hacer merge
    if os.path.exists(ACTIVE_REGISTRY_PATH):
        df_active = pd.read_parquet(ACTIVE_REGISTRY_PATH)
        df_active['run_fondo'] = df_active['run_fondo'].astype(int)
        merge_cols = ['run_fondo', 'rut_agf', 'tipo_fondo', 'moneda']
        existing_cols = [c for c in merge_cols if c in df_active.columns]
        df_merged = pd.merge(df_cmf, df_active[existing_cols], on='run_fondo', how='left')
        df_merged['tipo_fondo'] = df_merged['tipo_fondo'].fillna('No especificado')
        df_merged['moneda'] = df_merged['moneda'].fillna('CLP')
        df_merged['rut_agf'] = df_merged['rut_agf'].fillna('')
    else:
        df_merged = df_cmf
        df_merged['tipo_fondo'] = 'No especificado'
        df_merged['moneda'] = 'CLP'
        df_merged['rut_agf'] = ''

    df_merged = df_merged.sort_values('run_fondo').reset_index(drop=True)

    parquet_path = os.path.join(OUTPUT_DIR, "ffmm_registro_fondos_universo.parquet")
    df_merged.to_parquet(parquet_path, index=False)
    print(f"Guardado Parquet Universo: {parquet_path} ({os.path.getsize(parquet_path)/1024:.1f} KB)")

    json_path = os.path.join(OUTPUT_DIR, "ffmm_registro_fondos_universo.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(df_merged.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
    print(f"Guardado JSON Universo: {json_path} ({os.path.getsize(json_path)/1024:.1f} KB)")
    print(f"Universo consolidado: {len(df_merged)} fondos.")

if __name__ == '__main__':
    main()

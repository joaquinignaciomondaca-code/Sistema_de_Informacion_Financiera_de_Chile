# -*- coding: utf-8 -*-
"""
01_build_universe_fi.py - Construye el Censo Oficial y Completo de Fondos de Inversión (FI) en Chile.
Consulta la Comisión para el Mercado Financiero (CMF) para:
  - FIRES (Fondos de Inversión Rescatables): Vigentes y No Vigentes
  - FINRE (Fondos de Inversión No Rescatables): Vigentes y No Vigentes

Genera:
  - docs/outputs/fi/fi_registro_fondos_universo.parquet
  - docs/outputs/fi/fi_registro_fondos_universo.json
"""

import os
import sys
import ssl
import json
import urllib.request
from bs4 import BeautifulSoup
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "fi")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

ENTIDADES = [
    ('FIRES', 'Fondo de Inversión Rescatable'),
    ('FINRE', 'Fondo de Inversión No Rescatable')
]

ESTADOS = ['VI', 'NV']

all_funds = []
seen_keys = set()

for ent_code, ent_desc in ENTIDADES:
    for estado in ESTADOS:
        url = f"https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado={estado}&entidad={ent_code}"
        print(f"Consultando CMF: {ent_code} ({estado})...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                soup = BeautifulSoup(resp.read(), 'html.parser')
                tables = soup.find_all('table')
                if not tables:
                    continue
                rows = tables[0].find_all('tr')[1:]
                for tr in rows:
                    tds = tr.find_all(['td', 'th'])
                    if len(tds) < 3:
                        continue
                    rut_dv = tds[0].get_text(strip=True)
                    rut_num = rut_dv.split('-')[0].strip().replace('.', '')
                    nombre = tds[1].get_text(strip=True)
                    admin = tds[2].get_text(strip=True) if len(tds) > 2 else ''
                    vigencia_text = tds[3].get_text(strip=True) if len(tds) > 3 else ('Vigente' if estado == 'VI' else 'No Vigente')
                    
                    link = tr.find('a', href=True)
                    href = link['href'] if link else ''
                    row_id = ''
                    if 'row=' in href:
                        try:
                            row_id = href.split('row=')[1].split('&')[0]
                        except:
                            row_id = ''
                    
                    key = (rut_num, ent_code)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_funds.append({
                            'id': f'FI_{rut_num}',
                            'run_fondo': rut_num,
                            'rut_fondo_dv': rut_dv,
                            'nombre_fondo': nombre,
                            'administradora': admin,
                            'estado_vigencia': vigencia_text,
                            'tipo_entidad': ent_code,
                            'tipo_entidad_desc': ent_desc,
                            'cmf_row_id': row_id,
                            'url_ficha_cmf': f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut_num}&tipoentidad={ent_code}&control=svs&pestania=1"
                        })
        except Exception as e:
            print(f"Error consultando {ent_code} {estado}: {e}")

df = pd.DataFrame(all_funds)
df = df.sort_values(['tipo_entidad', 'run_fondo']).reset_index(drop=True)

parquet_path = os.path.join(OUTPUT_DIR, 'fi_registro_fondos_universo.parquet')
json_path = os.path.join(OUTPUT_DIR, 'fi_registro_fondos_universo.json')

df.to_parquet(parquet_path, index=False)
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(df.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

print(f"\nUniverso Total Fondos de Inversión: {len(df)} fondos.")
print(f"  Por tipo entidad:\n{df['tipo_entidad_desc'].value_counts().to_string()}")
print(f"  Por vigencia:\n{df['estado_vigencia'].value_counts().to_string()}")
print(f"Archivo Parquet: {parquet_path} ({os.path.getsize(parquet_path)/1024:.1f} KB)")
print(f"Archivo JSON: {json_path} ({os.path.getsize(json_path)/1024:.1f} KB)")

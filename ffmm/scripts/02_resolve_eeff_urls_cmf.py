"""
Pipeline Step 2: Resolucion Masiva de URLs de EEFF desde CMF (pestania 62)
Mapeo especial:
  - Santander: convierte URLs con '?id=XXX' a 'https://sam.santanderassetmanagement.cl/.../EF{id}.pdf'
"""

import urllib.request
import ssl
import json
import os
import re
import sys
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "ffmm", "ffmm_registro_fondos.parquet")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "ffmm")
DATA_DIR = os.path.join(BASE_DIR, "ffmm", "data")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_fund_eeff_urls(fund_info):
    run = fund_info['run_fondo']
    agf_name = fund_info['razon_social_agf']
    url_p62 = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={run}&grupo=&tipoentidad=RGFMU&row=&vig=VI&control=svs&pestania=62"
    
    result = {
        'run_fondo': run,
        'nombre_fondo': fund_info['nombre_fondo'],
        'rut_agf': fund_info['rut_agf'],
        'razon_social_agf': agf_name,
        'tipo_fondo': fund_info.get('tipo_fondo', ''),
        'moneda': fund_info.get('moneda', 'CLP'),
        'url_eeff_2024': '',
        'url_auditores_2024': '',
        'periodo_seleccionado': '',
        'todos_periodos': [],
        'estado_cmf': 'SIN_REGISTROS',
        'error': ''
    }

    retries = 3
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url_p62, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                html = r.read().decode('latin1', errors='ignore')

            m = re.search(r'<table id=[\'"]Tabla[\'"].*?</table>', html, re.DOTALL)
            if not m:
                result['estado_cmf'] = 'TABLA_NO_ENCONTRADA'
                return result

            table_html = m.group(0)
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
            
            periodos_encontrados = []
            for r_text in rows[1:]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', r_text, re.DOTALL)
                if not cells or 'No existen registros' in cells[0]:
                    continue

                periodo = re.sub(r'<[^>]+>', ' ', cells[0]).strip()
                eeff_link = ''
                if len(cells) > 1:
                    m_href = re.search(r'href=[\'"]([^\'"]+)[\'"]', cells[1])
                    if m_href:
                        eeff_link = m_href.group(1).strip()

                auditor_link = ''
                if len(cells) > 2:
                    m_href_aud = re.search(r'href=[\'"]([^\'"]+)[\'"]', cells[2])
                    if m_href_aud:
                        auditor_link = m_href_aud.group(1).strip()

                periodos_encontrados.append({
                    'periodo': periodo,
                    'url_eeff': eeff_link,
                    'url_auditores': auditor_link
                })

            result['todos_periodos'] = periodos_encontrados

            chosen = None
            for p in periodos_encontrados:
                per_str = p['periodo']
                u_eeff = p['url_eeff']
                if any(k in per_str for k in ['2025', '2024']):
                    if u_eeff:
                        if 'cloudfront' in u_eeff:
                            continue
                        chosen = p
                        break
            
            if not chosen:
                for p in periodos_encontrados:
                    if any(k in p['periodo'] for k in ['2025', '2024']) and p['url_eeff']:
                        chosen = p
                        break

            if chosen:
                url_final = chosen['url_eeff']
                # Si es Santander y tiene id=..., convertir al enlace directo de SAM files
                if 'SANTANDER' in agf_name.upper() and 'id=' in url_final:
                    m_id = re.search(r'id=(\d+)', url_final)
                    if m_id:
                        url_final = f"https://sam.santanderassetmanagement.cl/samfiles/archivos/documentacion_legal/informes_auditores_historicos/fondos/2025/EF{m_id.group(1)}.pdf"

                result['url_eeff_2024'] = url_final
                result['url_auditores_2024'] = chosen['url_auditores']
                result['periodo_seleccionado'] = chosen['periodo']
                result['estado_cmf'] = 'DISPONIBLE_2024'
            elif periodos_encontrados:
                result['estado_cmf'] = 'DISPONIBLE_OTROS_PERIODOS'
            else:
                result['estado_cmf'] = 'VACIO_EN_CMF'

            return result

        except Exception as e:
            if attempt == retries - 1:
                result['error'] = str(e)
                result['estado_cmf'] = 'ERROR_RED'
                return result
            time.sleep(0.5 * (attempt + 1))

    return result

def main():
    if not os.path.exists(INPUT_PARQUET):
        raise FileNotFoundError(f"No se encuentra el registro {INPUT_PARQUET}. Ejecute step 01 primero.")

    df_registry = pd.read_parquet(INPUT_PARQUET)
    funds_list = df_registry.to_dict(orient='records')
    total_funds = len(funds_list)
    print(f"Iniciando resolucion de URLs (con Santander fix) para {total_funds} fondos mutuos...")

    results = []
    t0 = time.time()
    batch_size = 30
    processed_count = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_fund = {executor.submit(fetch_fund_eeff_urls, f): f for f in funds_list}
        for future in as_completed(future_to_fund):
            res = future.result()
            results.append(res)
            processed_count += 1
            if processed_count % batch_size == 0 or processed_count == total_funds:
                elapsed = time.time() - t0
                rate = processed_count / max(elapsed, 0.001)
                print(f"  Progreso: {processed_count}/{total_funds} ({(processed_count/total_funds)*100:.1f}%) | {rate:.1f} fondos/s")

    df_results = pd.DataFrame(results)
    parquet_path = os.path.join(OUTPUT_DIR, "ffmm_eeff_urls_2024.parquet")
    df_save = df_results.copy()
    df_save['todos_periodos'] = df_save['todos_periodos'].apply(lambda x: json.dumps(x, ensure_ascii=False))
    df_save.to_parquet(parquet_path, index=False)
    print(f"\nGuardado Parquet URLs: {parquet_path} ({os.path.getsize(parquet_path)/1024:.1f} KB)")

    json_path = os.path.join(OUTPUT_DIR, "ffmm_eeff_urls_2024.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Guardado JSON URLs: {json_path} ({os.path.getsize(json_path)/1024:.1f} KB)")

    print("\nResumen de Disponibilidad de EEFF en CMF:")
    print(df_results['estado_cmf'].value_counts())

if __name__ == '__main__':
    main()

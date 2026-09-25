"""
Pipeline Step 1: Descarga y construccion del Registro de Fondos Mutuos Activos en 2024
Fuente: CMF Chile (fm_ident2.php)
Salidas:
  - docs/outputs/ffmm/ffmm_registro_fondos.parquet
  - docs/outputs/ffmm/ffmm_registro_fondos.json
"""

import urllib.request
import ssl
import json
import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

URL_REGISTRO = 'https://www.cmfchile.cl/institucional/estadisticas/fm_ident2.php'
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'outputs', 'ffmm'))
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_registry():
    print(f"Descargando catalogo de Fondos Mutuos desde CMF: {URL_REGISTRO}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(URL_REGISTRO, data=b'', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        raw_text = r.read().decode('latin1', errors='ignore')

    lines = raw_text.splitlines()
    if not lines:
        raise ValueError("Respuesta vacia desde CMF")

    headers = [h.strip() for h in lines[0].split(';')]
    print(f"Encabezados CMF: {headers}")

    records = []
    seen_runs = {}

    for line in lines[1:]:
        parts = [p.strip() for p in line.split(';')]
        if len(parts) < 4:
            continue

        rut_agf = parts[0]
        razon_social_agf = parts[1]
        run_fondo = parts[2]
        nombre_fondo = parts[3]
        nombre_corto = parts[4] if len(parts) > 4 else ''
        fecha_res = parts[5] if len(parts) > 5 else ''
        nro_res = parts[6] if len(parts) > 6 else ''
        tipo_fondo = parts[7] if len(parts) > 7 else ''
        fecha_inicio = parts[8] if len(parts) > 8 else ''
        fecha_termino = parts[9] if len(parts) > 9 else ''
        moneda = parts[10] if len(parts) > 10 else 'CLP'

        if not run_fondo or not run_fondo.isdigit():
            continue

        es_activo_2024 = False
        if not fecha_termino:
            es_activo_2024 = True
        else:
            try:
                parts_date = fecha_termino.split('/')
                if len(parts_date) == 3 and parts_date[2].isdigit():
                    yr = int(parts_date[2])
                    if yr >= 2024:
                        es_activo_2024 = True
            except Exception:
                pass

        if not es_activo_2024:
            continue

        if run_fondo not in seen_runs:
            item = {
                'run_fondo': run_fondo,
                'nombre_fondo': nombre_fondo,
                'nombre_corto': nombre_corto,
                'rut_agf': rut_agf,
                'razon_social_agf': razon_social_agf,
                'tipo_fondo': tipo_fondo,
                'moneda': moneda,
                'fecha_inicio': fecha_inicio,
                'fecha_termino': fecha_termino,
                'estado': 'VIGENTE' if not fecha_termino else 'TERMINO_2024+'
            }
            seen_runs[run_fondo] = item

    all_funds = list(seen_runs.values())
    print(f"Total fondos activos en 2024 identificados: {len(all_funds)}")
    return all_funds

def main():
    funds = fetch_registry()
    df = pd.DataFrame(funds)
    
    parquet_path = os.path.join(OUTPUT_DIR, 'ffmm_registro_fondos.parquet')
    df.to_parquet(parquet_path, index=False)
    print(f"Guardado Parquet: {parquet_path} ({os.path.getsize(parquet_path)/1024:.1f} KB)")

    json_path = os.path.join(OUTPUT_DIR, 'ffmm_registro_fondos.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(funds, f, ensure_ascii=False, indent=2)
    print(f"Guardado JSON: {json_path} ({os.path.getsize(json_path)/1024:.1f} KB)")

    print("\nDistribucion de Fondos Activos por AGF (Top 10):")
    agf_dist = df['razon_social_agf'].value_counts()
    for agf, count in agf_dist.head(10).items():
        print(f"  - {agf[:50]}: {count} fondos")

if __name__ == '__main__':
    main()

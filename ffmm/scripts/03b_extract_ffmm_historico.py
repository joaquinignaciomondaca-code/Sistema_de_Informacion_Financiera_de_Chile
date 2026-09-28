"""
Pipeline Step 3B: Extractor Masivo Streaming en RAM de EEFF y Notas REPO de Fondos Mutuos (2015-2025)
======================================================================================================
Arquitectura:
1. Consulta CMF Pestaña 3 (Información Financiera) para cada fondo y año.
2. Extrae carátula completa EEFF directamente del HTML (Activos, Pasivos, Patrimonio/AUM, Utilidad, Efectivo, Cartera).
3. Si existe PDF de notas ('FMNO...pdf'):
   - Descarga en RAM con reintentos y socket timeout (io.BytesIO, cero archivos en disco).
   - PyMuPDF analiza tablas de Nota 25 (Pactos / Retroventas).
   - Extrae tabla literal de 11 columnas con soporte multilínea (unidades, total transado, tasa, saldo al cierre).
   - Libera memoria (doc.close(), buffer descartado).
4. Persistencia atómica en checkpoints JSON y Parquet final.
"""

import urllib.request
import ssl
import json
import os
import re
import sys
import time
import socket
import fitz
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración de red y buffer de salida
socket.setdefaulttimeout(30)
sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_UNIVERSE = os.path.join(BASE_DIR, "docs", "outputs", "ffmm", "ffmm_registro_fondos_universo.parquet")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "ffmm")
DATA_DIR = os.path.join(BASE_DIR, "ffmm", "data")
CHECKPOINT_PATH = os.path.join(DATA_DIR, "checkpoint_historico_eeff.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

YEARS_TO_PROCESS = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010]

def parse_num(val_str):
    if not val_str:
        return 0.0
    s = str(val_str).strip()
    s = s.replace('$', '').replace('M$', '').replace('%', '').strip()
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

def unpack_multiline_table(raw_rows):
    """
    Desempaqueta tablas donde celdas colapsadas contienen múltiples filas separadas por salto de línea.
    """
    unpacked = []
    for row in raw_rows:
        col_splits = [[line.strip() for line in str(c or '').split('\n') if line.strip()] for c in row]
        max_lines = max((len(lines) for lines in col_splits), default=1)
        if max_lines > 1 and any(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line) for col in col_splits for line in col):
            for i in range(max_lines):
                new_row = [col[i] if i < len(col) else '' for col in col_splits]
                unpacked.append(new_row)
        else:
            unpacked.append([' '.join(str(c or '').split()) for c in row])
    return unpacked

def extract_eeff_html(html, fund_info, yr):
    soup = BeautifulSoup(html, 'html.parser')
    res = {
        'run_fondo': fund_info['run_fondo'],
        'nombre_fondo': fund_info['nombre_fondo'],
        'rut_agf': fund_info.get('rut_agf', ''),
        'razon_social_agf': fund_info['razon_social_agf'],
        'periodo': f"{yr}12",
        'anio': yr,
        'mes': 12,
        'fecha_cierre': f"31/12/{yr}",
        'moneda': 'CLP',
        'efectivo_y_equivalentes_m_clp': 0.0,
        'activos_financieros_vr_m_clp': 0.0,
        'activos_financieros_amortizado_m_clp': 0.0,
        'cuentas_por_cobrar_m_clp': 0.0,
        'otros_activos_m_clp': 0.0,
        'total_activos_m_clp': 0.0,
        'pasivos_financieros_vr_m_clp': 0.0,
        'cuentas_por_pagar_m_clp': 0.0,
        'rescates_por_pagar_m_clp': 0.0,
        'remuneracion_agf_por_pagar_m_clp': 0.0,
        'otros_pasivos_m_clp': 0.0,
        'total_pasivos_m_clp': 0.0,
        'patrimonio_activo_neto_m_clp': 0.0,
        'ingresos_operacionales_m_clp': 0.0,
        'comision_administracion_m_clp': 0.0,
        'utilidad_neta_ejercicio_m_clp': 0.0,
        'cuadre_activo_pasivo_patrimonio': False,
        'diferencia_cuadre_m_clp': 0.0,
        'tiene_notas_pdf': False,
        'url_notas_cmf': ''
    }

    escala = 1.0
    if 'expresado en pesos' in html.lower() and 'miles de pesos' not in html.lower():
        escala = 0.001

    for table in soup.find_all('table'):
        txt = table.get_text()
        if 'ESTADO DE SITUACION FINANCIERA' in txt:
            for tr in table.find_all('tr'):
                tds = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if len(tds) >= 3:
                    label = tds[1].upper() if len(tds) >= 4 and not tds[0] else tds[0].upper()
                    val_str = tds[-2] if len(tds) >= 4 else tds[-1]
                    val = parse_num(val_str) * escala
                    if 'EFECTIVO Y EFECTIVO EQUIVALENTE' in label: res['efectivo_y_equivalentes_m_clp'] = val
                    elif 'VALOR RAZONABLE CON EFECTO EN RESULTADOS' in label and 'ENTREGADOS' not in label and 'PASIVOS' not in label: res['activos_financieros_vr_m_clp'] = val
                    elif 'COSTO AMORTIZADO' in label and 'PASIVOS' not in label: res['activos_financieros_amortizado_m_clp'] = val
                    elif 'CUENTAS POR COBRAR A INTERMEDIARIOS' in label or 'OTRAS CUENTAS POR COBRAR' in label: res['cuentas_por_cobrar_m_clp'] += val
                    elif 'OTROS ACTIVOS' in label: res['otros_activos_m_clp'] = val
                    elif 'TOTAL ACTIVO' in label: res['total_activos_m_clp'] = val
                    elif 'PASIVOS FINANCIEROS A VALOR RAZONABLE' in label: res['pasivos_financieros_vr_m_clp'] = val
                    elif 'CUENTAS POR PAGAR A INTERMEDIARIOS' in label or 'OTROS DOCUMENTOS Y CUENTAS POR PAGAR' in label: res['cuentas_por_pagar_m_clp'] += val
                    elif 'RESCATES POR PAGAR' in label: res['rescates_por_pagar_m_clp'] = val
                    elif 'REMUNERACIONES SOCIEDAD' in label or 'REMUNERACION SOCIEDAD' in label: res['remuneracion_agf_por_pagar_m_clp'] = val
                    elif 'OTROS PASIVOS' in label: res['otros_pasivos_m_clp'] = val
                    elif 'TOTAL PASIVO' in label and 'EXCLUIDO' in label: res['total_pasivos_m_clp'] = val
                    elif 'ACTIVO NETO ATRIBUIBLE' in label: res['patrimonio_activo_neto_m_clp'] = val

        elif 'ESTADO DE RESULTADOS' in txt:
            for tr in table.find_all('tr'):
                tds = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if len(tds) >= 3:
                    label = tds[1].upper() if len(tds) >= 4 and not tds[0] else tds[0].upper()
                    val_str = tds[-2] if len(tds) >= 4 else tds[-1]
                    val = parse_num(val_str) * escala
                    if 'TOTAL INGRESOS' in label or 'TOTAL INGRESOS/(PÉRDIDAS)' in label: res['ingresos_operacionales_m_clp'] = val
                    elif 'COMISIÓN DE ADMINISTRACIÓN' in label or 'COMISION DE ADMINISTRACION' in label: res['comision_administracion_m_clp'] = val
                    elif 'UTILIDAD/(PÉRDIDA) DE LA OPERACIÓN DESPUÉS DE IMPUESTO' in label or 'UTILIDAD/(PERDIDA) DE LA OPERACION DESPUES DE IMPUESTO' in label:
                        res['utilidad_neta_ejercicio_m_clp'] = val

    # Verificar cuadre contable
    diff = abs(res['total_activos_m_clp'] - (res['total_pasivos_m_clp'] + res['patrimonio_activo_neto_m_clp']))
    res['diferencia_cuadre_m_clp'] = round(diff, 2)
    res['cuadre_activo_pasivo_patrimonio'] = (diff < 1.0)

    # Link de notas
    base_url = "https://www.cmfchile.cl/institucional/mercados/"
    for a in soup.find_all('a', href=True):
        txt_a = a.get_text(strip=True)
        href_a = a['href']
        if (txt_a == 'Notas' or 'FMNO' in href_a) and 'pdf' in href_a.lower():
            res['tiene_notas_pdf'] = True
            res['url_notas_cmf'] = urllib.parse.urljoin(base_url, href_a)
            break

    return res

def extract_repos_from_pdf_stream(pdf_bytes, fund_info, yr):
    repos = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    except Exception:
        return repos

    repo_pages = []
    for pno in range(len(doc)):
        try:
            txt_u = doc[pno].get_text().upper()
            if any(k in txt_u for k in ['COMPRA CON RETROVENTA', 'OPERACIONES CON RETROVENTA', 'OPERACIONES CON PACTO']):
                repo_pages.append(pno)
        except Exception:
            continue

    if not repo_pages:
        doc.close()
        return repos

    for pno in repo_pages:
        try:
            page = doc[pno]
            tabs = page.find_tables()
            for tab in tabs.tables:
                raw_rows = tab.extract()
                if not raw_rows or len(raw_rows) < 2:
                    continue

                raw_header = ' '.join([str(c) for r in raw_rows[:3] for c in r if c])
                norm_header = re.sub(r'\s+', ' ', raw_header).upper()

                if any(k in norm_header for k in ['BOLETA BANCARIA', 'PÓLIZA DE SEGURO', 'POLIZA DE SEGURO', 'CUSTODIA NACIONAL', 'VALOR CUOTA']):
                    continue

                is_repo = any(k in norm_header for k in ['FECHA COMPRA', 'FECHA DE COMPRA', 'TOTAL TRANSADO', 'PRECIO PACTADO', 'SALDO AL CIERRE', 'PROMESA DE VENTA'])
                if not is_repo:
                    continue

                unpacked_rows = unpack_multiline_table(raw_rows)

                for r in unpacked_rows:
                    cells = [str(c).strip() for c in r if c is not None]
                    row_str = ' '.join(cells).upper()

                    if 'TOTAL' in cells[0].upper() or (len(cells) > 1 and 'TOTAL' in cells[1].upper()):
                        continue
                    if any(h in row_str for h in ['FECHA COMPRA', 'CONTRAPARTE', 'NEMOTÉCNICO', 'NEMOTECNICO', 'UNIDADES NOMINALES', 'TOTAL TRANSADO', 'PRECIO PACTADO', 'SALDO AL CIERRE', 'CLASIFICACIÓN', 'PROMESA DE VENTA']):
                        continue
                    if 'SIN INFORMACI' in row_str:
                        continue

                    has_date = any(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', c) for c in cells)
                    has_rut = any(re.search(r'\d{7,8}[-0-9kK]', c.replace('.', '')) for c in cells)
                    if not (has_date or has_rut):
                        continue

                    clean_cells = [c for c in cells if c != '']
                    if len(clean_cells) < 4:
                        continue

                    f_compra = ''
                    f_venc = ''
                    dates = [c for c in clean_cells if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', c)]
                    if len(dates) >= 2:
                        f_compra = dates[0]
                        f_venc = dates[1]
                    elif dates:
                        f_compra = dates[0]

                    rut_cp = ''
                    ruts = [c for c in clean_cells if re.search(r'\d{7,8}[-0-9kK]', c.replace('.', ''))]
                    if ruts:
                        rut_cp = ruts[0]

                    nom_cp = ''
                    for c in clean_cells:
                        c_u = c.upper()
                        if any(b in c_u for b in ['BANCO', 'BCI', 'CHILE', 'SANTANDER', 'ITAÚ', 'ITAU', 'SCOTIA', 'BICE', 'SECURITY', 'ESTADO', 'CORREDOR', 'BILBAO', 'BBVA']):
                            nom_cp = c
                            break
                    if not nom_cp and rut_cp and rut_cp in clean_cells:
                        idx = clean_cells.index(rut_cp)
                        if idx + 1 < len(clean_cells):
                            nom_cp = clean_cells[idx + 1]

                    nums = []
                    for c in clean_cells:
                        val = parse_num(c)
                        if val != 0.0:
                            nums.append(val)

                    saldo_cierre = 0.0
                    tot_trans = 0.0
                    unid_nom = 0.0
                    if nums:
                        saldo_cierre = nums[-1]
                        if len(nums) >= 3:
                            unid_nom = nums[0]
                            tot_trans = nums[1]
                        elif len(nums) == 2:
                            tot_trans = nums[0]

                    tipo_inst = ''
                    nemo = ''
                    for c in clean_cells:
                        c_u = c.upper()
                        if any(t in c_u for t in ['BTP', 'BTU', 'PDBC', 'PRC', 'BCP', 'BCU', 'DP', 'TGR']):
                            nemo = c
                            if 'BTP' in c_u: tipo_inst = 'BTP'
                            elif 'BTU' in c_u: tipo_inst = 'BTU'
                            elif 'PDBC' in c_u: tipo_inst = 'PDBC'
                            elif 'BCP' in c_u: tipo_inst = 'BCP'
                            elif 'BCU' in c_u: tipo_inst = 'BCU'
                            elif 'DP' in c_u: tipo_inst = 'DP'
                            break

                    tasa_pactada = ''
                    for c in clean_cells:
                        if '%' in c or (re.search(r'^\d+[\.,]\d+$', c) and parse_num(c) < 30.0 and parse_num(c) > 0.01):
                            tasa_pactada = c
                            break

                    repos.append({
                        'run_fondo': fund_info['run_fondo'],
                        'nombre_fondo': fund_info['nombre_fondo'],
                        'rut_agf': fund_info.get('rut_agf', ''),
                        'razon_social_agf': fund_info['razon_social_agf'],
                        'periodo': f"{yr}12",
                        'anio': yr,
                        'fecha_compra': f_compra,
                        'rut_contraparte': rut_cp,
                        'nombre_contraparte': nom_cp,
                        'clasificacion_riesgo': 'NA',
                        'nemotecnico': nemo,
                        'tipo_instrumento': tipo_inst,
                        'unidades_nominales': unid_nom,
                        'total_transado_m_clp': tot_trans,
                        'fecha_vencimiento': f_venc,
                        'precio_pactado_tasa': tasa_pactada,
                        'saldo_al_cierre_m_clp': saldo_cierre,
                        'pagina_pdf': pno + 1
                    })
        except Exception:
            continue

    doc.close()
    return repos

def process_fund_year(fund_info, yr):
    rut = fund_info['run_fondo']
    url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut}&tipoentidad=RGFMU&vig=VI&control=svs&pestania=3&aa={yr}&mm=12"
    
    html = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=12) as r:
                html = r.read().decode('latin1', errors='ignore')
            break
        except Exception:
            time.sleep(0.3)

    if not html or 'ESTADO DE SITUACION FINANCIERA' not in html:
        return None, []

    eeff_res = extract_eeff_html(html, fund_info, yr)
    repos_res = []

    # Si hay link de notas, descargar y procesar en RAM con reintentos
    if eeff_res['tiene_notas_pdf'] and eeff_res['url_notas_cmf']:
        pdf_url = eeff_res['url_notas_cmf']
        pdf_bytes = None
        for attempt in range(3):
            try:
                req_pdf = urllib.request.Request(pdf_url, headers=HEADERS)
                with urllib.request.urlopen(req_pdf, context=ctx, timeout=20) as r_pdf:
                    pdf_bytes = r_pdf.read()
                if pdf_bytes:
                    break
            except Exception:
                time.sleep(0.5 * (attempt + 1))

        if pdf_bytes:
            repos_res = extract_repos_from_pdf_stream(pdf_bytes, fund_info, yr)
            del pdf_bytes

    return eeff_res, repos_res

def save_checkpoint_atomic(processed_keys, eeff_all, repos_all):
    tmp_path = CHECKPOINT_PATH + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump({
            'processed_keys': list(processed_keys),
            'eeff': eeff_all,
            'repos': repos_all
        }, f, ensure_ascii=False)
    os.replace(tmp_path, CHECKPOINT_PATH)

def main():
    print(f"Iniciando pipeline masivo historico de FFMM (Años: {min(YEARS_TO_PROCESS)} a {max(YEARS_TO_PROCESS)})...")
    if not os.path.exists(INPUT_UNIVERSE):
        raise FileNotFoundError(f"No existe {INPUT_UNIVERSE}. Ejecute step 01b primero.")

    df_universe = pd.read_parquet(INPUT_UNIVERSE)
    funds = df_universe.to_dict(orient='records')
    print(f"Total fondos en universo: {len(funds)}")

    processed_keys = set()
    eeff_all = []
    repos_all = []

    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
                ckpt = json.load(f)
                processed_keys = set(tuple(k) for k in ckpt.get('processed_keys', []))
                eeff_all = ckpt.get('eeff', [])
                repos_all = ckpt.get('repos', [])
                print(f"Reanudando desde checkpoint: {len(processed_keys)} combinaciones ya procesadas.")
        except Exception as e:
            print(f"No se pudo cargar checkpoint: {e}")

    tasks = []
    for yr in YEARS_TO_PROCESS:
        for f in funds:
            key = (f['run_fondo'], yr)
            if key not in processed_keys:
                tasks.append((f, yr))

    total_tasks = len(tasks)
    print(f"Total consultas pendientes por ejecutar: {total_tasks}")
    if total_tasks == 0:
        print("Todas las tareas ya fueron completadas segun el checkpoint.")
    else:
        t0 = time.time()
        completed_count = 0
        batch_save = 100

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_task = {executor.submit(process_fund_year, f, yr): (f['run_fondo'], yr) for f, yr in tasks}
            for future in as_completed(future_to_task):
                rut, yr = future_to_task[future]
                completed_count += 1
                try:
                    eeff_item, repo_items = future.result()
                    if eeff_item:
                        eeff_all.append(eeff_item)
                    if repo_items:
                        repos_all.extend(repo_items)
                except Exception as e:
                    pass

                processed_keys.add((rut, yr))

                if completed_count % batch_save == 0 or completed_count == total_tasks:
                    elapsed = time.time() - t0
                    rate = completed_count / max(elapsed, 0.001)
                    print(f"  Progreso: {completed_count}/{total_tasks} ({(completed_count/total_tasks)*100:.1f}%) | {rate:.1f} queries/s | EEFF: {len(eeff_all)} | REPOs: {len(repos_all)}")
                    save_checkpoint_atomic(processed_keys, eeff_all, repos_all)

    print("\nProcesamiento masivo finalizado. Generando Parquets y JSONs finales...")

    # La carátula histórica se retiró del sitio el 2026-09-26 (no se reconcilió
    # contra la fuente y discrepaba con la extracción 2024). Se sigue calculando
    # para el resumen en pantalla, pero no se publica. Para volver a exportarla:
    #   FFMM_PUBLICAR_CARATULA_HISTORICO=1 python 03b_extract_ffmm_historico.py
    publicar_caratula = os.environ.get("FFMM_PUBLICAR_CARATULA_HISTORICO") == "1"

    df_eeff = None
    if eeff_all:
        df_eeff = pd.DataFrame(eeff_all).drop_duplicates(subset=['run_fondo', 'periodo'])
        df_eeff = df_eeff.sort_values(['anio', 'run_fondo']).reset_index(drop=True)
        if publicar_caratula:
            eeff_parquet = os.path.join(OUTPUT_DIR, "ffmm_caratula_eeff_historico.parquet")
            df_eeff.to_parquet(eeff_parquet, index=False)
            print(f"Guardado Parquet EEFF Historico: {eeff_parquet} ({len(df_eeff)} registros, {os.path.getsize(eeff_parquet)/1024:.1f} KB)")
            eeff_json = os.path.join(OUTPUT_DIR, "ffmm_caratula_eeff_historico.json")
            with open(eeff_json, 'w', encoding='utf-8') as f:
                json.dump(df_eeff.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
            print(f"Guardado JSON EEFF Historico: {eeff_json} ({os.path.getsize(eeff_json)/1024:.1f} KB)")
        else:
            print("Carátula histórica calculada pero NO publicada (retirada del sitio; ver comentario arriba).")

    if repos_all:
        df_repos = pd.DataFrame(repos_all).drop_duplicates(subset=['run_fondo', 'periodo', 'nemotecnico', 'saldo_al_cierre_m_clp', 'fecha_compra'])
        df_repos = df_repos.sort_values(['anio', 'run_fondo']).reset_index(drop=True)
        repos_parquet = os.path.join(OUTPUT_DIR, "ffmm_repos_detalle_historico.parquet")
        df_repos.to_parquet(repos_parquet, index=False)
        print(f"Guardado Parquet REPOs Historico: {repos_parquet} ({len(df_repos)} contratos, {os.path.getsize(repos_parquet)/1024:.1f} KB)")
        repos_json = os.path.join(OUTPUT_DIR, "ffmm_repos_detalle_historico.json")
        with open(repos_json, 'w', encoding='utf-8') as f:
            json.dump(df_repos.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
        print(f"Guardado JSON REPOs Historico: {repos_json} ({os.path.getsize(repos_json)/1024:.1f} KB)")

    print("\nResumen Global por Anio:")
    if eeff_all:
        df_summary = df_eeff.groupby('anio').agg(
            fondos_con_eeff=('run_fondo', 'count'),
            aum_total_m_clp=('patrimonio_activo_neto_m_clp', 'sum'),
            activos_totales_m_clp=('total_activos_m_clp', 'sum')
        ).reset_index()
        print(df_summary.to_string(index=False))

if __name__ == '__main__':
    main()

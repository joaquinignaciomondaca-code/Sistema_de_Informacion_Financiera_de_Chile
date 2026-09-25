"""
Pipeline Step 3: Extractor Masivo Determinista de EEFF de Fondos Mutuos (2024)
Metodo: Descarga en memoria (0 archivos residuales, 0 tokens LLM) via PyMuPDF.
Caracteristicas:
  - Carátula: Solver multi-columna exacto (Activos, AUM / Patrimonio, Utilidad del Ejercicio).
  - Repos: Extracción literal de la tabla CMF completa (11 columnas oficiales).
Entrada:
  - docs/outputs/ffmm/ffmm_eeff_urls_2024.parquet
Salidas:
  - docs/outputs/ffmm/ffmm_caratula_eeff_2024.parquet
  - docs/outputs/ffmm/ffmm_caratula_eeff_2024.json
  - docs/outputs/ffmm/ffmm_repos_detalle_2024.parquet (TABLA LITERAL COMPLETA)
  - docs/outputs/ffmm/ffmm_repos_detalle_2024.json
"""

import os
import re
import sys
import json
import time
import requests
import fitz  # PyMuPDF
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "ffmm", "ffmm_eeff_urls_2024.parquet")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "ffmm")
DATA_DIR = os.path.join(BASE_DIR, "ffmm", "data")
CHECKPOINT_PATH = os.path.join(DATA_DIR, "checkpoint_extracted.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

TC_USD_CLP_2024 = 973.85

def parse_num(val_str):
    if not val_str:
        return 0.0
    val_str = str(val_str).strip().replace('$', '').replace('M$', '').replace('US$', '').replace('M(USD)', '').replace('M($)', '').strip()
    if val_str in ['-', '—', '–', '', 'None']:
        return 0.0
    es_negativo = False
    if val_str.startswith('(') and val_str.endswith(')'):
        es_negativo = True
        val_str = val_str[1:-1].strip()
    elif val_str.startswith('-'):
        es_negativo = True
        val_str = val_str[1:].strip()
    
    val_str = val_str.replace('.', '').replace(',', '.')
    try:
        n = float(val_str)
        return -n if es_negativo else n
    except ValueError:
        return 0.0

def parse_line_numbers(s):
    tokens = s.strip().split()
    results = []
    for tok in tokens:
        clean = tok.replace('$', '').replace('M$', '').replace('US$', '').replace('M(USD)', '').replace('M($)', '').strip()
        if clean in ['-', '—', '–']:
            results.append(0.0)
            continue
        neg = False
        if clean.startswith('(') and clean.endswith(')'):
            neg = True
            clean = clean[1:-1].strip()
        elif clean.startswith('-'):
            neg = True
            clean = clean[1:].strip()
        clean = clean.replace('.', '').replace(',', '.')
        try:
            val = float(clean)
            results.append(-val if neg else val)
        except ValueError:
            pass
    return results

def get_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.cmfchile.cl/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
    })
    return s

def extract_caratula(doc):
    balance_data = {
        'total_activos': 0.0,
        'total_pasivos': 0.0,
        'patrimonio_neto': 0.0,
        'efectivo_caratula': 0.0,
        'fvtpl_caratula': 0.0,
        'costo_amortizado_caratula': 0.0,
        'total_ingresos_netos': 0.0,
        'comision_administracion': 0.0,
        'total_gastos_operacion': 0.0,
        'utilidad_ejercicio': 0.0,
        'moneda_informada': 'CLP',
        'caratula_encontrada': False
    }

    # Localizar Balance Real
    b_page_idx = -1
    for p_idx in range(min(15, len(doc))):
        txt_u = doc[p_idx].get_text().upper()
        if ('TOTAL ACTIVOS' in txt_u or 'TOTAL ACTIVO' in txt_u) and ('TOTAL PASIVOS' in txt_u or 'TOTAL PASIVO' in txt_u):
            if 'CONTENIDO' not in txt_u and 'INFORME DEL AUDITOR' not in txt_u and 'DICTAMEN' not in txt_u:
                b_page_idx = p_idx
                break

    if b_page_idx != -1:
        balance_data['caratula_encontrada'] = True
        txt = doc[b_page_idx].get_text()
        txt_u = txt.upper()
        if "MILES DE DÓLARES" in txt_u or "MILES DE DOLARES" in txt_u or "M(USD)" in txt_u or "MUSD" in txt_u:
            balance_data['moneda_informada'] = 'USD'

        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        act_cols, pas_cols, pat_cols = [], [], []
        efec_cols, fvtpl_cols, amort_cols = [], [], []

        for i, line in enumerate(lines):
            line_u = line.upper()
            nums_in_line = parse_line_numbers(line)
            def get_f_nums():
                if nums_in_line: return nums_in_line
                for k in range(i+1, min(i+4, len(lines))):
                    fn = parse_line_numbers(lines[k])
                    if fn: return fn
                return []

            if re.match(r'^TOTAL\s+ACTIVOS?\b', line_u) and not act_cols:
                act_cols = get_f_nums()
            elif re.match(r'^TOTAL\s+PASIVOS?\b', line_u) and "EXCLUIDO" in line_u and not pas_cols:
                pas_cols = get_f_nums()
            elif "ACTIVO NETO ATRIBUIBLE" in line_u and not pat_cols:
                pat_cols = get_f_nums()
            elif "EFECTIVO Y EFECTIVO EQUIVALENTE" in line_u and not efec_cols:
                efec_cols = get_f_nums()
            elif "VALOR RAZONABLE CON EFECTO EN RESULTADOS" in line_u and "ENTREGADO" not in line_u and not fvtpl_cols:
                fvtpl_cols = get_f_nums()
            elif "COSTO AMORTIZADO" in line_u and not amort_cols:
                amort_cols = get_f_nums()

        chosen_col = -1
        max_cols = max(len(act_cols), len(pas_cols), len(pat_cols))
        for col_idx in range(max_cols):
            a = act_cols[col_idx] if col_idx < len(act_cols) else 0.0
            p = pas_cols[col_idx] if col_idx < len(pas_cols) else 0.0
            pt = pat_cols[col_idx] if col_idx < len(pat_cols) else 0.0
            if a > 0 and abs(a - (p + pt)) <= 5.0:
                chosen_col = col_idx
                balance_data['total_activos'] = a
                balance_data['total_pasivos'] = p
                balance_data['patrimonio_neto'] = pt
                break

        if chosen_col == -1:
            balance_data['total_activos'] = act_cols[0] if act_cols else 0.0
            balance_data['total_pasivos'] = pas_cols[0] if pas_cols else 0.0
            balance_data['patrimonio_neto'] = pat_cols[0] if pat_cols else 0.0
            chosen_col = 0

        balance_data['efectivo_caratula'] = efec_cols[chosen_col] if chosen_col < len(efec_cols) else (efec_cols[0] if efec_cols else 0.0)
        balance_data['fvtpl_caratula'] = fvtpl_cols[chosen_col] if chosen_col < len(fvtpl_cols) else (fvtpl_cols[0] if fvtpl_cols else 0.0)
        balance_data['costo_amortizado_caratula'] = amort_cols[chosen_col] if chosen_col < len(amort_cols) else (amort_cols[0] if amort_cols else 0.0)

    # Localizar Estado de Resultados Real
    r_page_idx = -1
    for p_idx in range(min(15, len(doc))):
        txt_u = doc[p_idx].get_text().upper()
        if ('TOTAL INGRESOS' in txt_u or 'TOTAL RESULTADO' in txt_u) and ('TOTAL GASTOS' in txt_u or 'COMISIÓN' in txt_u or 'COMISION' in txt_u):
            if 'CONTENIDO' not in txt_u and 'INFORME DEL AUDITOR' not in txt_u and 'DICTAMEN' not in txt_u:
                r_page_idx = p_idx
                break

    if r_page_idx != -1:
        lines = [l.strip() for l in doc[r_page_idx].get_text().splitlines() if l.strip()]
        for i, line in enumerate(lines):
            line_u = line.upper()
            nums = parse_line_numbers(line)
            def get_f_nums_r():
                if nums: return nums
                for k in range(i+1, min(i+4, len(lines))):
                    fn = parse_line_numbers(lines[k])
                    if fn: return fn
                return []

            if ("TOTAL INGRESOS" in line_u or "TOTAL RESULTADO DE LA OPERACION" in line_u) and balance_data['total_ingresos_netos'] == 0.0:
                fn = get_f_nums_r()
                if fn: balance_data['total_ingresos_netos'] = fn[0]
            elif ("COMISIÓN DE ADMINISTRACIÓN" in line_u or "COMISION DE ADMINISTRACION" in line_u) and balance_data['comision_administracion'] == 0.0:
                fn = get_f_nums_r()
                if fn: balance_data['comision_administracion'] = fn[0]
            elif ("TOTAL GASTOS DE OPERACIÓN" in line_u or "TOTAL GASTOS DE OPERACION" in line_u) and balance_data['total_gastos_operacion'] == 0.0:
                fn = get_f_nums_r()
                if fn: balance_data['total_gastos_operacion'] = fn[0]
            elif ("AUMENTO/(DISMINUCIÓN) DE ACTIVO NETO" in line_u or "AUMENTO/(DISMINUCION) DE ACTIVO NETO" in line_u) and balance_data['utilidad_ejercicio'] == 0.0:
                fn = get_f_nums_r()
                if fn: balance_data['utilidad_ejercicio'] = fn[0]

    return balance_data

def extract_literal_repo_table(doc, run_fondo, nombre_fondo, agf_nombre, total_activos_fondo, factor_tc):
    """Extrae la tabla literal completa de 11 columnas de Operaciones de Compra con Retroventa."""
    repo_result = {
        'tiene_repos': False,
        'saldo_repos_total_m_clp': 0.0,
        'contratos_detalle': []
    }

    repo_pages = []
    for p_idx in range(len(doc)):
        txt_u = doc[p_idx].get_text().upper()
        if 'COMPRA CON RETROVENTA' in txt_u or 'OPERACIONES CON RETROVENTA' in txt_u:
            repo_pages.append(p_idx)

    if not repo_pages:
        return repo_result

    for p_idx in repo_pages:
        page = doc[p_idx]
        txt = page.get_text()

        # 1. Intentar con find_tables() (Tablas CMF estructuradas de 11 columnas)
        finder = page.find_tables()
        found_structured_table = False

        for tab in finder.tables:
            raw_rows = tab.extract()
            if not raw_rows or len(raw_rows) < 2:
                continue

            raw_str = ' '.join([str(c) for r in raw_rows[:3] for c in r if c])
            norm_str = re.sub(r'\s+', ' ', raw_str).upper()

            # Descartar tablas de Garantías o Custodia
            if any(k in norm_str for k in ['BOLETA BANCARIA', 'PÓLIZA DE SEGURO', 'POLIZA DE SEGURO', 'CUSTODIA NACIONAL', 'VALOR CUOTA']):
                continue

            is_repo = any(k in norm_str for k in ['FECHA COMPRA', 'FECHA DE COMPRA', 'TOTAL TRANSADO', 'PRECIO PACTADO', 'SALDO AL CIERRE', 'PROMESA DE VENTA'])
            if not is_repo:
                continue

            found_structured_table = True

            for row in raw_rows:
                cells = [str(c).strip() if c is not None else '' for c in row]
                row_str = ' '.join(cells).upper()

                # Ignorar encabezados y fila total
                if 'TOTAL' in cells[0].upper() or (len(cells) > 1 and 'TOTAL' in cells[1].upper()):
                    continue
                if any(h in row_str for h in ['FECHA COMPRA', 'CONTRAPARTE', 'NEMOTÉCNICO', 'NEMOTECNICO', 'UNIDADES NOMINALES', 'TOTAL TRANSADO', 'PRECIO PACTADO', 'SALDO AL CIERRE', 'CLASIFICACIÓN', 'PROMESA DE VENTA']):
                    continue

                has_date = any(re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', c) for c in cells)
                has_rut = any(re.search(r'\d{1,2}\.\d{3}\.\d{3}-[\dkK]', c) for c in cells)
                if not (has_date or has_rut):
                    continue

                clean_cells = [c for c in cells if c != '']
                if len(clean_cells) < 4:
                    continue

                f_compra = ''
                f_venc = ''
                dates_found = [c for c in clean_cells if re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', c)]
                if len(dates_found) >= 2:
                    f_compra = dates_found[0]
                    f_venc = dates_found[1]
                elif dates_found:
                    f_compra = dates_found[0]

                rut_cp = ''
                ruts_found = [c for c in clean_cells if re.search(r'\d{1,2}\.\d{3}\.\d{3}-[\dkK]', c)]
                if ruts_found:
                    rut_cp = ruts_found[0]

                nom_cp = ''
                for c in clean_cells:
                    c_u = c.upper()
                    if any(b in c_u for b in ['BANCO', 'BCI', 'CHILE', 'SANTANDER', 'ITAÚ', 'ITAU', 'SCOTIA', 'BICE', 'SECURITY', 'ESTADO', 'CORREDOR']):
                        nom_cp = c
                        break

                if not nom_cp and rut_cp and rut_cp in clean_cells:
                    idx_r = clean_cells.index(rut_cp)
                    if idx_r + 1 < len(clean_cells):
                        nom_cp = clean_cells[idx_r + 1]

                nums_found = []
                for c in clean_cells:
                    val = parse_num(c)
                    if val != 0.0:
                        nums_found.append(val)

                saldo_cierre = 0.0
                tot_trans = 0.0
                unid_nom = 0.0
                if nums_found:
                    saldo_cierre = nums_found[-1]
                    if len(nums_found) >= 3:
                        unid_nom = nums_found[0]
                        tot_trans = nums_found[1]
                    elif len(nums_found) == 2:
                        tot_trans = nums_found[0]

                tipo_inst = ''
                nemo = ''
                for c in clean_cells:
                    c_u = c.upper()
                    if any(t in c_u for t in ['BTP', 'BTU', 'PDBC', 'PRC', 'BCP', 'BCU', 'DP', 'TGR']):
                        if len(c) <= 6:
                            tipo_inst = c
                        else:
                            nemo = c

                tasa = ''
                for c in clean_cells:
                    if re.match(r'^\d+,\d{1,4}$', c):
                        tasa = c

                saldo_cierre_clp = saldo_cierre * factor_tc
                tot_trans_clp = tot_trans * factor_tc

                if saldo_cierre_clp > 0:
                    repo_result['tiene_repos'] = True
                    repo_result['contratos_detalle'].append({
                        'run_fondo': run_fondo,
                        'nombre_fondo': nombre_fondo,
                        'rut_agf': '',
                        'razon_social_agf': agf_nombre,
                        'fecha_compra': f_compra,
                        'rut_contraparte': rut_cp,
                        'nombre_contraparte': nom_cp if nom_cp else 'NO_INFORMADO',
                        'clasificacion_riesgo': 'NA',
                        'nemotecnico': nemo,
                        'tipo_instrumento': tipo_inst,
                        'unidades_nominales': unid_nom,
                        'total_transado_m_clp': tot_trans_clp,
                        'fecha_vencimiento': f_venc,
                        'precio_pactado_tasa': tasa,
                        'saldo_al_cierre_m_clp': saldo_cierre_clp,
                        'pagina_pdf': p_idx + 1
                    })
                    repo_result['saldo_repos_total_m_clp'] += saldo_cierre_clp

        # 2. Si no habia tabla estructurada con lineas en la pagina, extraer lineas de texto (formato BICE)
        if not found_structured_table:
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            in_repo_note = False
            for i, line in enumerate(lines):
                line_u = line.upper()
                if 'OPERACIONES DE COMPRA CON RETROVENTA' in line_u or 'OPERACIONES CON RETROVENTA' in line_u:
                    in_repo_note = True
                    continue
                if in_repo_note and any(k in line_u for k in ['INFORMACIÓN ESTADÍSTICA', 'INFORMACION ESTADISTICA', 'CUSTODIA', 'GARANTÍA', 'GARANTIA', 'NOTA ']):
                    in_repo_note = False
                    continue

                if in_repo_note:
                    # Descartar polizas de garantia de Nota 24
                    if any(g in line_u for g in ['POLIZA', 'PÓLIZA', 'GARANTIA', 'GARANTÍA', 'BENEFICIARIOS', 'BOLETA BANCARIA', 'CONTINENTAL', 'SEGUROS']):
                        continue

                    if 'RETROVENTA' in line_u and any(b in line_u for b in ['BANCO', 'BCI', 'CHILE', 'SANTANDER', 'ITAÚ', 'ITAU', 'SCOTIA', 'BICE', 'SECURITY', 'ESTADO', 'CORREDOR']):
                        vals = []
                        for k in range(i+1, min(i+4, len(lines))):
                            cand = lines[k].strip()
                            if cand in ['-', '—', '–'] or re.match(r'^[\d\.\,\-]+$', cand):
                                vals.append(parse_num(cand))
                        if vals:
                            s_val = vals[1] if len(vals) >= 2 and vals[1] > 0 else vals[0]
                            cp_clean = re.sub(r'[\d\.\,\$\-\–\—]', '', line).strip()
                            cp_clean = re.sub(r'^(?:SALDO|OPERACIONES|RETROVENTA|DE|CON)+', '', cp_clean, flags=re.I).strip()
                            s_clp = s_val * factor_tc
                            if s_clp > 0:
                                repo_result['tiene_repos'] = True
                                repo_result['contratos_detalle'].append({
                                    'run_fondo': run_fondo,
                                    'nombre_fondo': nombre_fondo,
                                    'rut_agf': '',
                                    'razon_social_agf': agf_nombre,
                                    'fecha_compra': '31/12/2024',
                                    'rut_contraparte': '',
                                    'nombre_contraparte': cp_clean,
                                    'clasificacion_riesgo': 'NA',
                                    'nemotecnico': '',
                                    'tipo_instrumento': 'PACTO_RETROVENTA',
                                    'unidades_nominales': 0.0,
                                    'total_transado_m_clp': s_clp,
                                    'fecha_vencimiento': '',
                                    'precio_pactado_tasa': '',
                                    'saldo_al_cierre_m_clp': s_clp,
                                    'pagina_pdf': p_idx + 1
                                })
                                repo_result['saldo_repos_total_m_clp'] += s_clp

    return repo_result

def process_single_fund(session, fund_row):
    run = fund_row['run_fondo']
    url = fund_row.get('url_eeff_2024', '')
    name = fund_row.get('nombre_fondo', '')
    agf = fund_row.get('razon_social_agf', '')
    rut_agf = fund_row.get('rut_agf', '')

    result = {
        'run_fondo': run,
        'nombre_fondo': name,
        'rut_agf': rut_agf,
        'razon_social_agf': agf,
        'moneda': fund_row.get('moneda', 'CLP'),
        'url_procesada': url,
        'status': 'PENDIENTE',
        'caratula': {},
        'repos': {},
        'error': ''
    }

    if not url:
        result['status'] = 'SIN_URL_2024'
        return result

    try:
        resp = session.get(url, timeout=25)
        if resp.status_code != 200 or resp.content[:4] != b'%PDF':
            result['status'] = f'HTTP_{resp.status_code}' if resp.status_code != 200 else 'NO_ES_PDF_DIRECTO'
            return result

        doc = fitz.open(stream=resp.content, filetype='pdf')
        caratula = extract_caratula(doc)
        total_activos = caratula.get('total_activos', 0.0)
        moneda_rep = caratula.get('moneda_informada', 'CLP')
        factor_tc = TC_USD_CLP_2024 if moneda_rep == 'USD' else 1.0

        repos = extract_literal_repo_table(doc, run, name, agf, total_activos, factor_tc)
        doc.close()

        result['caratula'] = caratula
        result['repos'] = repos
        result['status'] = 'EXITO'
        return result

    except Exception as e:
        result['status'] = 'ERROR_EXTRACCION'
        result['error'] = str(e)
        return result

def main():
    if not os.path.exists(INPUT_PARQUET):
        raise FileNotFoundError(f"No existe {INPUT_PARQUET}. Ejecute Step 02 primero.")

    df_urls = pd.read_parquet(INPUT_PARQUET)
    funds = df_urls[df_urls['url_eeff_2024'] != ''].to_dict(orient='records')
    total = len(funds)
    print(f"Iniciando extraccion masiva y literal de EEFF para {total} fondos mutuos...", flush=True)

    results = []
    t0 = time.time()
    batch_size = 30
    processed_count = 0

    session = get_session()

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_fund = {executor.submit(process_single_fund, session, f): f for f in funds}
        for future in as_completed(future_to_fund):
            res = future.result()
            results.append(res)
            processed_count += 1

            if processed_count % batch_size == 0 or processed_count == total:
                elapsed = time.time() - t0
                rate = processed_count / max(elapsed, 0.001)
                print(f"  Progreso: {processed_count}/{total} ({(processed_count/total)*100:.1f}%) | {rate:.1f} fondos/s", flush=True)

    checkpoint_map = {r['run_fondo']: r for r in results}
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_map, f, ensure_ascii=False)

    caratula_rows = []
    repo_rows = []

    for r in results:
        if r.get('status') == 'EXITO' and r.get('caratula'):
            c = r['caratula']
            moneda_rep = c.get('moneda_informada', 'CLP')
            factor_tc = TC_USD_CLP_2024 if moneda_rep == 'USD' else 1.0

            activos_clp = c.get('total_activos', 0.0) * factor_tc
            pasivos_clp = c.get('total_pasivos', 0.0) * factor_tc
            patrimonio_clp = c.get('patrimonio_neto', 0.0) * factor_tc
            utilidad_clp = c.get('utilidad_ejercicio', 0.0) * factor_tc
            efectivo_clp = c.get('efectivo_caratula', 0.0) * factor_tc
            fvtpl_clp = c.get('fvtpl_caratula', 0.0) * factor_tc
            amortizado_clp = c.get('costo_amortizado_caratula', 0.0) * factor_tc
            saldo_repos_clp = r.get('repos', {}).get('saldo_repos_total_m_clp', 0.0)

            caratula_rows.append({
                'run_fondo': r['run_fondo'],
                'nombre_fondo': r['nombre_fondo'],
                'rut_agf': r['rut_agf'],
                'razon_social_agf': r['razon_social_agf'],
                'moneda_fondo': r['moneda'],
                'moneda_eeff': moneda_rep,
                'factor_tc_usd_clp': factor_tc,
                'total_activos_m_clp': activos_clp,
                'total_pasivos_m_clp': pasivos_clp,
                'patrimonio_aum_m_clp': patrimonio_clp,
                'utilidad_ejercicio_m_clp': utilidad_clp,
                'saldo_repos_m_clp': saldo_repos_clp,
                'costo_amortizado_m_clp': amortizado_clp,
                'fvtpl_m_clp': fvtpl_clp,
                'efectivo_m_clp': efectivo_clp,
                'tiene_repos': r.get('repos', {}).get('tiene_repos', False)
            })

            for cr in r.get('repos', {}).get('contratos_detalle', []):
                cr['rut_agf'] = r['rut_agf']
                repo_rows.append(cr)

    df_caratula = pd.DataFrame(caratula_rows)
    p_caratula = os.path.join(OUTPUT_DIR, "ffmm_caratula_eeff_2024.parquet")
    df_caratula.to_parquet(p_caratula, index=False)
    j_caratula = os.path.join(OUTPUT_DIR, "ffmm_caratula_eeff_2024.json")
    with open(j_caratula, 'w', encoding='utf-8') as f:
        json.dump(caratula_rows, f, ensure_ascii=False, indent=2)

    df_repos = pd.DataFrame(repo_rows)
    p_repos = os.path.join(OUTPUT_DIR, "ffmm_repos_detalle_2024.parquet")
    df_repos.to_parquet(p_repos, index=False)
    j_repos = os.path.join(OUTPUT_DIR, "ffmm_repos_detalle_2024.json")
    with open(j_repos, 'w', encoding='utf-8') as f:
        json.dump(repo_rows, f, ensure_ascii=False, indent=2)

    print(f"\nExtraccion completada con exito:")
    print(f"  Caratulas extraidas: {len(df_caratula)} fondos | Archivo: {p_caratula}")
    print(f"  Contratos REPO literales extraidos: {len(df_repos)} contratos | Archivo: {p_repos}")
    if not df_caratula.empty:
        total_aum = df_caratula['patrimonio_aum_m_clp'].sum()
        total_repo = df_caratula['saldo_repos_m_clp'].sum()
        print(f"  Total Patrimonio Administrado (AUM): ${total_aum:,.0f} M CLP")
        print(f"  Total REPOs detectados: ${total_repo:,.0f} M CLP")

if __name__ == '__main__':
    main()

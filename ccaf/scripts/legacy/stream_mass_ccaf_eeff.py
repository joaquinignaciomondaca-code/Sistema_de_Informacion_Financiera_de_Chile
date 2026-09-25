import fitz
import re
import os
import json
import ssl
import time
import urllib.request
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "pipelines", "manual", "raw_inputs", "ccaf")
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "cajas_compensacion")
SCRATCH_DIR = os.path.join(BASE_DIR, "scratch")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

CCAF_RUTS = {
    "CCAF Los Andes": "81.826.800-9",
    "CCAF La Araucana": "70.016.160-5",
    "CCAF Los Heroes": "70.016.330-1",
    "CCAF 18 de Septiembre": "82.606.800-K"
}

REPORTS_QUEUE = [
    # 2024 (cubre 2024 y 2023)
    {"ccaf": "CCAF Los Andes", "ano": 2024, "url": "https://www.suseso.cl/609/articles-752388_archivo_01.pdf"},
    {"ccaf": "CCAF La Araucana", "ano": 2024, "url": "https://www.suseso.cl/609/articles-752387_archivo_01.pdf"},
    {"ccaf": "CCAF Los Heroes", "ano": 2024, "url": "https://www.suseso.cl/609/articles-752390_archivo_01.pdf"},
    {"ccaf": "CCAF 18 de Septiembre", "ano": 2024, "url": "https://www.suseso.cl/609/articles-752385_archivo_01.pdf"},

    # 2022 (cubre 2022 y 2021)
    {"ccaf": "CCAF Los Andes", "ano": 2022, "url": "https://www.suseso.cl/609/articles-705624_archivo_01.pdf"},
    {"ccaf": "CCAF La Araucana", "ano": 2022, "url": "https://www.suseso.cl/609/articles-705625_archivo_01.pdf"},
    {"ccaf": "CCAF Los Heroes", "ano": 2022, "url": "https://www.suseso.cl/609/articles-705626_archivo_01.pdf"},
    {"ccaf": "CCAF 18 de Septiembre", "ano": 2022, "url": "https://www.suseso.cl/609/articles-705627_archivo_01.pdf"},

    # 2020 (cubre 2020 y 2019)
    {"ccaf": "CCAF Los Andes", "ano": 2020, "url": "https://www.suseso.cl/609/articles-687748_archivo_01.pdf"},
    {"ccaf": "CCAF La Araucana", "ano": 2020, "url": "https://www.suseso.cl/609/articles-687750_archivo_01.pdf"},
    {"ccaf": "CCAF Los Heroes", "ano": 2020, "url": "https://www.suseso.cl/609/articles-687753_archivo_01.pdf"},
    {"ccaf": "CCAF 18 de Septiembre", "ano": 2020, "url": "https://www.suseso.cl/609/articles-687755_archivo_01.pdf"},

    # 2018 (cubre 2018 y 2017)
    {"ccaf": "CCAF Los Andes", "ano": 2018, "url": "https://www.suseso.cl/609/articles-623937_archivo_01.pdf"},
    {"ccaf": "CCAF La Araucana", "ano": 2018, "url": "https://www.suseso.cl/609/articles-623962_archivo_01.pdf"},
    {"ccaf": "CCAF Los Heroes", "ano": 2018, "url": "https://www.suseso.cl/609/articles-623965_archivo_01.pdf"},
    {"ccaf": "CCAF 18 de Septiembre", "ano": 2018, "url": "https://www.suseso.cl/609/articles-623933_archivo_01.pdf"}
]

def clean_num(val_str):
    if not val_str: return 0.0
    s = str(val_str).strip().replace("$", "").replace("M$", "").replace(" ", "")
    if s in ["-", "--", "", "N/A", "null"]: return 0.0
    is_neg = False
    if s.startswith("(") and s.endswith(")"):
        is_neg = True
        s = s[1:-1]
    elif s.startswith("-"):
        is_neg = True
        s = s[1:]
    s = s.replace(".", "").replace(",", ".")
    try:
        val = float(s)
        return -val if is_neg else val
    except Exception:
        return 0.0

def query_deepseek_with_retry(prompt, max_retries=3):
    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request("http://127.0.0.1:9655/v1/chat/completions", data=data, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer free-deepseek"
    })

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    [Reintento {attempt+1}/{max_retries}] Error en DeepSeek: {e}. Esperando 4s...")
                time.sleep(4)
            else:
                print(f"    [Error final] DeepSeek fallo tras {max_retries} intentos: {e}")
                return ""

def extract_caratula(doc, ccaf_name, rep_year):
    rut = CCAF_RUTS.get(ccaf_name, "")
    activos_page = None
    for pno in range(min(25, len(doc))):
        txt = doc[pno].get_text().upper()
        if ("TOTAL DE ACTIVOS" in txt or "TOTAL ACTIVOS" in txt or "10000" in txt) and "INDICE" not in txt[:30]:
            activos_page = pno
            break
            
    if activos_page is None:
        return []

    lines = []
    for pno in range(activos_page, min(activos_page + 3, len(doc))):
        for l in doc[pno].get_text().splitlines():
            l_str = l.strip()
            if l_str:
                lines.append(l_str)

    results = {
        "Total de activos": [0, 0],
        "Total de pasivos": [0, 0],
        "Patrimonio total": [0, 0],
        "Utilidad neta": [0, 0]
    }

    for i, l in enumerate(lines):
        l_up = l.upper()
        if ("10000" in l_up and "ACTIVO" in l_up) or l_up == "10000" or l_up == "TOTAL DE ACTIVOS" or l_up == "TOTAL ACTIVOS":
            vals = []
            for j in range(1, 5):
                if i + j < len(lines):
                    cand = lines[i+j]
                    if re.match(r"^[\(\-]?\d{1,3}(\.\d{3})*(\,\d+)?\)?$", cand):
                        vals.append(clean_num(cand))
                        if len(vals) == 2: break
            if len(vals) >= 2: results["Total de activos"] = vals[:2]

        elif ("20000" in l_up and "PASIVO" in l_up) or l_up == "20000" or l_up == "TOTAL DE PASIVOS" or l_up == "TOTAL PASIVO" or l_up == "TOTAL PASIVOS":
            vals = []
            for j in range(1, 5):
                if i + j < len(lines):
                    cand = lines[i+j]
                    if re.match(r"^[\(\-]?\d{1,3}(\.\d{3})*(\,\d+)?\)?$", cand):
                        vals.append(clean_num(cand))
                        if len(vals) == 2: break
            if len(vals) >= 2: results["Total de pasivos"] = vals[:2]

        elif ("23000" in l_up and "PATRIMONIO" in l_up) or l_up == "23000" or l_up == "PATRIMONIO TOTAL" or l_up == "TOTAL PATRIMONIO":
            vals = []
            for j in range(1, 5):
                if i + j < len(lines):
                    cand = lines[i+j]
                    if re.match(r"^[\(\-]?\d{1,3}(\.\d{3})*(\,\d+)?\)?$", cand):
                        vals.append(clean_num(cand))
                        if len(vals) == 2: break
            if len(vals) >= 2: results["Patrimonio total"] = vals[:2]

        elif ("23050" in l_up and "GANANCIA" in l_up) or l_up == "23050" or l_up.startswith("GANANCIA (P") or l_up == "GANANCIA (PERDIDA) DEL EJERCICIO" or l_up == "GANANCIA DEL EJERCICIO":
            vals = []
            for j in range(1, 5):
                if i + j < len(lines):
                    cand = lines[i+j]
                    if re.match(r"^[\(\-]?\d{1,3}(\.\d{3})*(\,\d+)?\)?$", cand):
                        vals.append(clean_num(cand))
                        if len(vals) == 2: break
            if len(vals) >= 2: results["Utilidad neta"] = vals[:2]

    y_curr = rep_year
    y_prev = rep_year - 1
    
    rows = []
    for concept, vals in results.items():
        if vals[0] != 0 or vals[1] != 0:
            rows.append({"ano": y_curr, "mes": 12, "ccaf": ccaf_name, "rut": rut, "asiento_contable": concept, "monto_m_clp": round(vals[0] / 1000.0, 3), "monto_miles_clp": vals[0], "moneda": "CLP", "escala": "Miles"})
            rows.append({"ano": y_prev, "mes": 12, "ccaf": ccaf_name, "rut": rut, "asiento_contable": concept, "monto_m_clp": round(vals[1] / 1000.0, 3), "monto_miles_clp": vals[1], "moneda": "CLP", "escala": "Miles"})
    return rows

def locate_nota8_pages(doc):
    pages = []
    for pno in range(15, len(doc)):
        txt = doc[pno].get_text().upper()
        if "NOTA 8" in txt and any(k in txt for k in ["EFECTIVO", "EQUIVALENTE"]):
            pages.append(pno)
        elif pages and ("NOTA 9" in txt or "COLOCACIONES DE CR" in txt):
            break
    if not pages:
        return []
    p_start = pages[0]
    p_end = min(p_start + 4, len(doc))
    return list(range(p_start, p_end))

def extract_nota8_with_deepseek(doc, ccaf_name, rep_year):
    p_indices = locate_nota8_pages(doc)
    if not p_indices:
        return ""
    slice_text = ""
    for p in p_indices:
        slice_text += f"=== PAGINA {p+1} ===\n" + doc[p].get_text() + "\n"
        
    y_curr = rep_year
    y_prev = rep_year - 1

    prompt = f"""Eres un analista financiero experto. A continuacion tienes las paginas de la NOTA 8 (Efectivo y Equivalentes al Efectivo) de {ccaf_name} para los ejercicios {y_curr} y {y_prev}:

{slice_text}

Extrae las siguientes 3 tablas en formato de texto plano con separador "|":

### TABLA_RESUMEN_NOTA8
Columnas: ano|mes|ccaf|concepto|monto|moneda|escala
Extrae los conceptos de: Caja, Bancos, Depositos a plazo, Otro efectivo y equivalentes (o Pactos), Total efectivo y equivalentes para los ejercicios {y_curr} y {y_prev}.
Montos como enteros limpios sin puntos de miles.

### TABLA_DAP_NOTA8
Columnas: ano|mes|ccaf|tipo_inversion|moneda|plazo_dias|tasa_anual_pct|capital_monto|intereses_devengados|valor_contable|escala
Extrae cada fila del cuadro de depositos a plazo vigentes al 31-12-{y_curr}. Si la tabla no reporta depositos o esta vacia, no generes filas de datos.

### TABLA_REPOS_NOTA8
Columnas: ano|mes|ccaf|institucion_contraparte|moneda|fecha_inicio|fecha_termino|valor_inicial|valor_final|tasa_pct|valor_contable|escala
Extrae cada operacion de pactos de retroventa / repos al 31-12-{y_curr}. Si no tiene pactos vigentes, no generes filas de datos.

Reglas:
- Entrega unicamente las tablas con sus encabezados de seccion (### TABLA_...).
- Sin introducciones, conclusiones ni explicaciones.
"""
    return query_deepseek_with_retry(prompt)

def process_single_report_ephemeral(rep):
    ccaf_name = rep["ccaf"]
    rep_year = rep["ano"]
    url = rep["url"]
    
    clean_tag = ccaf_name.replace(" ", "_").lower()
    temp_pdf = os.path.join(SCRATCH_DIR, f"temp_{clean_tag}_{rep_year}.pdf")
    raw_path = os.path.join(RAW_DIR, f"raw_nota8_{clean_tag}_{rep_year}.txt")
    
    # Check if raw text already extracted
    existing_raw = ""
    if os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as rf:
            existing_raw = rf.read()

    print(f"\n>>> Procesando: {ccaf_name} ({rep_year})")
    t0 = time.time()
    
    caratula_rows = []
    raw_nota8_text = existing_raw
    doc = None
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=40) as r, open(temp_pdf, "wb") as f:
            f.write(r.read())
            
        pdf_size_kb = os.path.getsize(temp_pdf) / 1024.0
        print(f"  [OK] Descargado efimeramente ({pdf_size_kb:.1f} KB).")
        
        doc = fitz.open(temp_pdf)
        caratula_rows = extract_caratula(doc, ccaf_name, rep_year)
        print(f"  [OK] Caratula extraida: {len(caratula_rows)} filas.")
        
        if not raw_nota8_text:
            print(f"  Consultando Nota 8 a DeepSeek local...")
            raw_nota8_text = extract_nota8_with_deepseek(doc, ccaf_name, rep_year)
            if raw_nota8_text:
                with open(raw_path, "w", encoding="utf-8") as rf:
                    rf.write(raw_nota8_text)
                print(f"  [OK] Raw text guardado: {os.path.basename(raw_path)}")
            # Pausa suave de 3 segundos para el servidor DeepSeek
            time.sleep(3)
        else:
            print(f"  [CACHE RAW] Nota 8 ya existente en {os.path.basename(raw_path)}.")
            
    except Exception as e:
        print(f"  [ERROR] Procesando {ccaf_name} {rep_year}: {e}")
    finally:
        # Cerrar siempre el documento antes de eliminar
        if doc is not None:
            try: doc.close()
            except Exception: pass
            
        # HIGIENE ESTRICTA EN DISCO: Eliminar archivo PDF inmediatamente
        if os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
                print(f"  [CLEANUP] Archivo {os.path.basename(temp_pdf)} ELIMINADO (0 bytes residuales).")
            except Exception as ce:
                print(f"  [AVISO] No se pudo borrar {temp_pdf}: {ce}")
                
    elapsed = time.time() - t0
    print(f"  Tiempo reporte: {elapsed:.2f} s.")
    return caratula_rows, raw_nota8_text, ccaf_name

def run_mass_pipeline():
    print("=" * 80)
    print("INICIANDO PIPELINE MASIVO EFIMERO: CCAF HISTORICO 2017-2024")
    print(f"Total reportes en cola: {len(REPORTS_QUEUE)}")
    print("Principio estricto: Descarga -> Procesa -> Elimina PDF (0 bytes en disco)")
    print("=" * 80)

    all_caratula = []
    all_nota8_blocks = []

    for rep in REPORTS_QUEUE:
        c_rows, n8_raw, ccaf_name = process_single_report_ephemeral(rep)
        all_caratula.extend(c_rows)
        if n8_raw:
            all_nota8_blocks.append({"ccaf": ccaf_name, "raw": n8_raw})

    # Consolidar Caratula
    df_caratula = pd.DataFrame(all_caratula)
    df_caratula = df_caratula.drop_duplicates(subset=["ano", "mes", "ccaf", "asiento_contable"], keep="first")
    df_caratula = df_caratula.sort_values(["ano", "ccaf", "asiento_contable"], ascending=[False, True, True]).reset_index(drop=True)
    
    pq_caratula = os.path.join(OUT_DIR, "ccaf_caratula_totales.parquet")
    js_caratula = os.path.join(OUT_DIR, "ccaf_caratula_totales.json")
    pq.write_table(pa.Table.from_pandas(df_caratula), pq_caratula, compression="snappy")
    df_caratula.to_json(js_caratula, orient="records", indent=2, force_ascii=False)

    # Parsear y compilar tablas de Nota 8
    resumen_rows = []
    dap_rows = []
    repos_rows = []

    for block in all_nota8_blocks:
        ccaf_name = block["ccaf"]
        text = block["raw"]
        current_section = None
        
        for line in text.splitlines():
            l = line.strip()
            if not l: continue
            if "### TABLA_RESUMEN_NOTA8" in l:
                current_section = "RESUMEN"
                continue
            elif "### TABLA_DAP_NOTA8" in l:
                current_section = "DAP"
                continue
            elif "### TABLA_REPOS_NOTA8" in l:
                current_section = "REPOS"
                continue
            elif l.startswith("ano|") or l.startswith("año|"):
                continue

            parts = [p.strip() for p in l.split("|")]
            
            if current_section == "RESUMEN" and len(parts) >= 5:
                ano = int(parts[0]) if parts[0].isdigit() else 2024
                mes = int(parts[1]) if parts[1].isdigit() else 12
                conc = parts[3]
                monto = clean_num(parts[4])
                mon = parts[5] if len(parts) > 5 else "CLP"
                resumen_rows.append({
                    "ano": ano, "mes": mes, "ccaf": ccaf_name, "concepto": conc,
                    "monto_miles_clp": monto, "monto_m_clp": round(monto / 1000.0, 3), "moneda": mon
                })
            elif current_section == "DAP" and len(parts) >= 8:
                ano = int(parts[0]) if parts[0].isdigit() else 2024
                mes = int(parts[1]) if parts[1].isdigit() else 12
                tipo_inv = parts[3]
                mon = parts[4]
                dias = clean_num(parts[5])
                tasa = clean_num(parts[6])
                cap = clean_num(parts[7])
                inte = clean_num(parts[8]) if len(parts) > 8 else 0
                vc = clean_num(parts[9]) if len(parts) > 9 else cap + inte
                dap_rows.append({
                    "ano": ano, "mes": mes, "ccaf": ccaf_name, "tipo_inversion": tipo_inv,
                    "moneda": mon, "plazo_dias": int(dias), "tasa_pct": tasa,
                    "capital_miles_clp": cap, "intereses_miles_clp": inte, "valor_contable_miles_clp": vc,
                    "valor_contable_m_clp": round(vc / 1000.0, 3)
                })
            elif current_section == "REPOS" and len(parts) >= 8:
                ano = int(parts[0]) if parts[0].isdigit() else 2024
                mes = int(parts[1]) if parts[1].isdigit() else 12
                inst = parts[3]
                mon = parts[4]
                f_ini = parts[5]
                f_ter = parts[6]
                v_ini = clean_num(parts[7])
                v_fin = clean_num(parts[8])
                tasa = clean_num(parts[9]) if len(parts) > 9 else 0
                vc = clean_num(parts[10]) if len(parts) > 10 else v_fin
                repos_rows.append({
                    "ano": ano, "mes": mes, "ccaf": ccaf_name, "institucion_contraparte": inst,
                    "moneda": mon, "fecha_inicio": f_ini, "fecha_termino": f_ter,
                    "valor_inicial_miles_clp": v_ini, "valor_final_miles_clp": v_fin, "tasa_pct": tasa,
                    "valor_contable_miles_clp": vc, "valor_contable_m_clp": round(vc / 1000.0, 3)
                })

    df_res = pd.DataFrame(resumen_rows).drop_duplicates().sort_values(["ano", "ccaf"]).reset_index(drop=True)
    df_dap = pd.DataFrame(dap_rows).drop_duplicates().sort_values(["ano", "ccaf"]).reset_index(drop=True)
    df_rep = pd.DataFrame(repos_rows).drop_duplicates().sort_values(["ano", "ccaf"]).reset_index(drop=True)

    pq_res = os.path.join(OUT_DIR, "ccaf_nota8_efectivo_resumen.parquet")
    pq_dap = os.path.join(OUT_DIR, "ccaf_nota8_dap_detalle.parquet")
    pq_rep = os.path.join(OUT_DIR, "ccaf_nota8_repos_detalle.parquet")

    pq.write_table(pa.Table.from_pandas(df_res), pq_res, compression="snappy")
    df_res.to_json(os.path.join(OUT_DIR, "ccaf_nota8_efectivo_resumen.json"), orient="records", indent=2, force_ascii=False)

    pq.write_table(pa.Table.from_pandas(df_dap), pq_dap, compression="snappy")
    df_dap.to_json(os.path.join(OUT_DIR, "ccaf_nota8_dap_detalle.json"), orient="records", indent=2, force_ascii=False)

    pq.write_table(pa.Table.from_pandas(df_rep), pq_rep, compression="snappy")
    df_rep.to_json(os.path.join(OUT_DIR, "ccaf_nota8_repos_detalle.json"), orient="records", indent=2, force_ascii=False)

    print("\n" + "=" * 80)
    print("PIPELINE MASIVO EFIMERO FINALIZADO CON EXITO:")
    print(f"  1. ccaf_caratula_totales.parquet        -> {len(df_caratula)} filas (Historico 2017-2024)")
    print(f"  2. ccaf_nota8_efectivo_resumen.parquet -> {len(df_res)} filas")
    print(f"  3. ccaf_nota8_dap_detalle.parquet      -> {len(df_dap)} filas")
    print(f"  4. ccaf_nota8_repos_detalle.parquet    -> {len(df_rep)} filas")
    print("=" * 80)

if __name__ == "__main__":
    run_mass_pipeline()

import fitz
import re
import os
import json
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

CCAF_CATALOG = [
    {
        "name": "CCAF Los Andes",
        "rut": "81.826.800-9",
        "rut_num": 81826800,
        "pdf_name": "eeff_los_andes_2024.pdf"
    },
    {
        "name": "CCAF La Araucana",
        "rut": "70.016.160-5",
        "rut_num": 70016160,
        "pdf_name": "eeff_la_araucana_2024.pdf"
    },
    {
        "name": "CCAF Los Heroes",
        "rut": "70.016.330-1",
        "rut_num": 70016330,
        "pdf_name": "eeff_los_heroes_2024.pdf"
    },
    {
        "name": "CCAF 18 de Septiembre",
        "rut": "82.606.800-K",
        "rut_num": 82606800,
        "pdf_name": "eeff_caja18_2024.pdf"
    }
]

def clean_num(val_str):
    if not val_str:
        return 0.0
    s = str(val_str).strip().replace("$", "").replace("M$", "").replace(" ", "")
    if s in ["-", "--", "", "N/A", "null"]:
        return 0.0
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

def query_deepseek(prompt):
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
    with urllib.request.urlopen(req, timeout=90) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["choices"][0]["message"]["content"]

def extract_caratula_totales(doc, ent):
    # Locate balance sheet page
    activos_page = None
    for pno in range(min(25, len(doc))):
        txt = doc[pno].get_text()
        if ("TOTAL DE ACTIVOS" in txt.upper() or "TOTAL ACTIVOS" in txt.upper()) and "INDICE" not in txt.upper()[:30]:
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

        elif ("23050" in l_up and "GANANCIA" in l_up) or l_up == "23050" or l_up.startswith("GANANCIA (P") or l_up == "GANANCIA (PERDIDA) DEL EJERCICIO":
            vals = []
            for j in range(1, 5):
                if i + j < len(lines):
                    cand = lines[i+j]
                    if re.match(r"^[\(\-]?\d{1,3}(\.\d{3})*(\,\d+)?\)?$", cand):
                        vals.append(clean_num(cand))
                        if len(vals) == 2: break
            if len(vals) >= 2: results["Utilidad neta"] = vals[:2]

    rows = []
    for concept, vals in results.items():
        rows.append({"ano": 2024, "mes": 12, "ccaf": ent["name"], "rut": ent["rut"], "asiento_contable": concept, "monto_m_clp": round(vals[0] / 1000.0, 3), "monto_miles_clp": vals[0], "moneda": "CLP", "escala": "Miles"})
        rows.append({"ano": 2023, "mes": 12, "ccaf": ent["name"], "rut": ent["rut"], "asiento_contable": concept, "monto_m_clp": round(vals[1] / 1000.0, 3), "monto_miles_clp": vals[1], "moneda": "CLP", "escala": "Miles"})
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
    # Include up to 4 pages from first match
    p_start = pages[0]
    p_end = min(p_start + 4, len(doc))
    return list(range(p_start, p_end))

def extract_nota8_tables(doc, ent):
    p_indices = locate_nota8_pages(doc)
    if not p_indices:
        print(f"  [AVISO] No se ubicaron paginas de Nota 8 para {ent['name']}")
        return "", "", ""
        
    slice_text = ""
    for p in p_indices:
        slice_text += f"=== PAGINA {p+1} ===\n" + doc[p].get_text() + "\n"
        
    prompt = f"""Eres un analista financiero experto. A continuacion tienes las paginas de la NOTA 8 (Efectivo y Equivalentes al Efectivo) de {ent['name']}:

{slice_text}

Extrae las siguientes 3 tablas en formato de texto plano con separador "|":

### TABLA_RESUMEN_NOTA8
Columnas: ano|mes|ccaf|concepto|monto|moneda|escala
Extrae los conceptos de: Caja, Bancos, Depositos a plazo, Otro efectivo y equivalentes (o Pactos), Total efectivo y equivalentes para los ejercicios 2024 y 2023.
Montos como enteros limpios sin puntos de miles.

### TABLA_DAP_NOTA8
Columnas: ano|mes|ccaf|tipo_inversion|moneda|plazo_dias|tasa_anual_pct|capital_monto|intereses_devengados|valor_contable|escala
Extrae cada fila del cuadro de depositos a plazo vigentes al 31-12-2024. Si la tabla no reporta depositos o esta vacia, no generes filas de datos.

### TABLA_REPOS_NOTA8
Columnas: ano|mes|ccaf|institucion_contraparte|moneda|fecha_inicio|fecha_termino|valor_inicial|valor_final|tasa_pct|valor_contable|escala
Extrae cada operacion de pactos de retroventa / repos al 31-12-2024. Si no tiene pactos vigentes, no generes filas de datos.

Reglas:
- Entrega unicamente las tablas con sus encabezados de seccion (### TABLA_...).
- Sin introducciones, conclusiones ni explicaciones.
"""
    response_text = query_deepseek(prompt)
    return response_text

def run_phase1_batch():
    print("=" * 80)
    print("INICIANDO EXTRACCION MASIVA CCAF - FASE 1 (TOTALES Y NOTA 8)")
    print("=" * 80)

    all_caratula = []
    raw_nota8_blocks = []

    for ent in CCAF_CATALOG:
        pdf_path = os.path.join(SCRATCH_DIR, ent["pdf_name"])
        if not os.path.exists(pdf_path):
            print(f"[ERROR] Archivo no encontrado: {pdf_path}")
            continue
            
        print(f"\nProcesando {ent['name']} ({ent['pdf_name']})...")
        doc = fitz.open(pdf_path)
        print(f"  Total paginas: {len(doc)}")
        
        # 1. Caratula Totales
        rows_caratula = extract_caratula_totales(doc, ent)
        print(f"  [OK] Totales extraidos: {len(rows_caratula)} filas.")
        all_caratula.extend(rows_caratula)
        
        # 2. Nota 8 con DeepSeek
        print(f"  Consultando Nota 8 via DeepSeek local...")
        nota8_raw = extract_nota8_tables(doc, ent)
        raw_nota8_blocks.append({"ccaf": ent["name"], "raw": nota8_raw})
        
        # Guardar raw text por entidad
        raw_ent_path = os.path.join(RAW_DIR, f"raw_nota8_{ent['rut_num']}.txt")
        with open(raw_ent_path, "w", encoding="utf-8") as f:
            f.write(nota8_raw)
        print(f"  [OK] Raw text guardado: {raw_ent_path}")

    # Guardar Caratula Parquet y JSON
    df_caratula = pd.DataFrame(all_caratula)
    pq_caratula = os.path.join(OUT_DIR, "ccaf_caratula_totales.parquet")
    js_caratula = os.path.join(OUT_DIR, "ccaf_caratula_totales.json")
    table_c = pa.Table.from_pandas(df_caratula)
    pq.write_table(table_c, pq_caratula, compression="snappy")
    df_caratula.to_json(js_caratula, orient="records", indent=2, force_ascii=False)
    print(f"\n[OK] ccaf_caratula_totales generado con exito: {len(df_caratula)} filas.")

    # Parsear y compilar tablas de Nota 8 de todas las CCAF
    resumen_rows = []
    dap_rows = []
    repos_rows = []

    for block in raw_nota8_blocks:
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
                continue # header
                
            parts = [p.strip() for p in l.split("|")]
            
            if current_section == "RESUMEN" and len(parts) >= 5:
                # ano|mes|ccaf|concepto|monto|moneda|escala
                ano = int(parts[0]) if parts[0].isdigit() else 2024
                mes = int(parts[1]) if parts[1].isdigit() else 12
                c_nom = parts[2]
                conc = parts[3]
                monto = clean_num(parts[4])
                mon = parts[5] if len(parts) > 5 else "CLP"
                resumen_rows.append({
                    "ano": ano, "mes": mes, "ccaf": ccaf_name, "concepto": conc,
                    "monto_miles_clp": monto, "monto_m_clp": round(monto / 1000.0, 3), "moneda": mon
                })
            elif current_section == "DAP" and len(parts) >= 8:
                # ano|mes|ccaf|tipo_inversion|moneda|plazo_dias|tasa_anual_pct|capital_monto|intereses_devengados|valor_contable|escala
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
                # ano|mes|ccaf|institucion_contraparte|moneda|fecha_inicio|fecha_termino|valor_inicial|valor_final|tasa_pct|valor_contable|escala
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

    # Guardar Parquet y JSON de Nota 8
    df_res = pd.DataFrame(resumen_rows)
    df_dap = pd.DataFrame(dap_rows)
    df_rep = pd.DataFrame(repos_rows)

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
    print("EXTRACCION Y COMPILACION MASIVA FASE 1 FINALIZADA:")
    print(f"  1. ccaf_caratula_totales.parquet        -> {len(df_caratula)} filas")
    print(f"  2. ccaf_nota8_efectivo_resumen.parquet -> {len(df_res)} filas")
    print(f"  3. ccaf_nota8_dap_detalle.parquet      -> {len(df_dap)} filas")
    print(f"  4. ccaf_nota8_repos_detalle.parquet    -> {len(df_rep)} filas")
    print("=" * 80)

if __name__ == "__main__":
    run_phase1_batch()

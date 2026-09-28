"""
Pipeline de Extraccion Streaming de EEFF y Mercado REPO para Corredoras de Bolsa - CMF Chile.
Descarga efimera en memoria RAM (0 bytes residuales en disco):
1. Nivel 1: Caratula EEFF y Balance General IFRS (desde XML).
2. Nivel 2: Segmentacion de Contrapartes, Tasas Ponderadas y Plazos REPO (desde PDF Notas).
3. Nivel 3: Detalle de Colaterales e Instrumentos Subyacentes bajo Pacto (desde PDF Notas).

Guarda en docs/outputs/corredoras_bolsa/:
- corredoras_bolsa_caratula_eeff_historico.parquet / .json
- corredoras_repos_contrapartes_tasas.parquet / .json
- corredoras_repos_colaterales_detalle.parquet / .json
- corredoras_bolsa_balance_resumen.parquet / .json
"""

import os
import re
import ssl
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import fitz

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "corredoras_bolsa")
DATA_DIR = os.path.join(BASE_DIR, "corredoras_bolsa", "data")
MACRO_PARQUET = os.path.join(BASE_DIR, "docs", "outputs", "macro", "macro_divisas_mercado.parquet")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint_corredoras_repos.json")

# Pactos/colaterales de notas PDF retirados de publicación (auditoría pendiente).
# Con False el pipeline solo extrae y publica las carátulas XML (Nivel 1).
PUBLICAR_PACTOS_REPOS = False

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,text/plain,*/*"
}

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def get_usd_rates_map():
    rates = {}
    if os.path.exists(MACRO_PARQUET):
        try:
            df_macro = pd.read_parquet(MACRO_PARQUET)
            for _, r in df_macro.iterrows():
                if pd.notna(r.get("usd_clp_cierre")):
                    rates[str(r["periodo"])] = float(r["usd_clp_cierre"])
        except Exception:
            pass

    fallback_rates = {
        "2018-03": 603.41, "2018-06": 653.21, "2018-09": 659.87, "2018-12": 694.77,
        "2019-03": 678.53, "2019-06": 679.16, "2019-09": 728.21, "2019-12": 748.74,
        "2020-03": 852.03, "2020-06": 821.23, "2020-09": 788.15, "2020-12": 710.95,
        "2021-03": 732.15, "2021-06": 727.80, "2021-09": 811.90, "2021-12": 844.69,
        "2022-03": 787.25, "2022-06": 932.08, "2022-09": 960.35, "2022-12": 855.86,
        "2023-03": 790.35, "2023-06": 801.66, "2023-09": 895.12, "2023-12": 884.45,
        "2024-03": 980.20, "2024-06": 948.45, "2024-09": 898.32, "2024-12": 974.15,
        "2025-03": 955.10, "2025-06": 940.25, "2025-09": 950.00, "2025-12": 960.00,
        "2026-03": 931.57, "2026-06": 940.00
    }
    for k, v in fallback_rates.items():
        if k not in rates:
            rates[k] = v
    return rates

def parse_num(s):
    if not s: return 0.0
    s = s.strip().replace("$", "").replace("%", "").strip()
    if s in ("-", "—", "NA", "N/A", ""): return 0.0
    is_neg = s.startswith("(") and s.endswith(")")
    if is_neg: s = s[1:-1].strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
        return -v if is_neg else v
    except ValueError:
        return 0.0

def fetch_links(rut_clean, row_id, year, month):
    url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut={rut_clean}&tipoentidad=COBOL&row={row_id}&control=svs&pestania=3"
    data = urllib.parse.urlencode({"aa": str(year), "mm": str(month).zfill(2)}).encode("latin1")
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=12) as r:
            html = r.read().decode("latin1", errors="ignore")
    except Exception:
        return None, None

    xml_url, pdf_url = None, None
    for a in re.finditer(r'href="([^"]*ifrs_xml_verarchivo\.php[^"]*)"', html):
        href = a.group(1)
        if "archivo=IVEF" in href and not xml_url:
            xml_url = "https://www.cmfchile.cl/institucional/" + href.replace("../", "")
        elif "archivo=IVNO" in href and not pdf_url:
            pdf_url = "https://www.cmfchile.cl/institucional/" + href.replace("../", "")
    return xml_url, pdf_url

def parse_xml_balance(xml_bytes, rut, nombre, periodo, fecha_corte, usd_rate):
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return None

    cuentas = {}
    for c in root.findall(".//Cuenta"):
        if c.attrib.get("Context") == "PeriodoActual":
            code = c.attrib.get("CodigoCuenta")
            try:
                cuentas[code] = float(c.text.strip()) if c.text and c.text.strip() else 0.0
            except ValueError:
                pass

    activos = cuentas.get("TotalActivos", 0.0)
    pasivos = cuentas.get("TotalPasivos", 0.0)
    patrimonio = cuentas.get("TotalPatrimonio", 0.0)
    utilidad = cuentas.get("UtilidadPerdidaDelEjercicio", cuentas.get("ResultadoDelEjercicioPatrimonio", cuentas.get("ResultadoAntesDeImpuestoALaRenta", 0.0)))
    efectivo = cuentas.get("EfectivoYEfectivoEquivalente", 0.0)
    vr_disp = cuentas.get("AValorRazonableCarteraPropiaDisponible", 0.0)
    vr_comp = cuentas.get("AValorRazonableCarteraPropiaComprometida", 0.0)
    crv_activos = cuentas.get("ACostoAmortizadoOperacionesDeFinanciamientoActivos", 
                              cuentas.get("ACostoAmortizadoOperacionesDeFinanciamientoOperacionesDeCompraConRetroventaSobreIRV", 0.0))
    vrc_pasivos = cuentas.get("OperacionesDeVentaConRetrocompraSobreIRFeIIF",
                              cuentas.get("ObligacionesPorFinanciamiento", 0.0))

    cuadre = abs(activos - (pasivos + patrimonio)) < 5.0
    usd_val = usd_rate if usd_rate > 0 else 900.0

    return {
        "id_balance": f"{periodo}_{rut}",
        "periodo": periodo,
        "fecha_corte": fecha_corte,
        "rut": rut,
        "nombre_empresa": nombre,
        "total_activos_m_clp": round(activos, 3),
        "total_activos_m_usd": round(activos / usd_val, 3),
        "total_pasivos_m_clp": round(pasivos, 3),
        "total_pasivos_m_usd": round(pasivos / usd_val, 3),
        "patrimonio_neto_m_clp": round(patrimonio, 3),
        "patrimonio_m_usd": round(patrimonio / usd_val, 3),
        "utilidad_ejercicio_m_clp": round(utilidad, 3),
        "utilidad_ejercicio_m_usd": round(utilidad / usd_val, 3),
        "efectivo_equivalentes_m_clp": round(efectivo, 3),
        "efectivo_equivalentes_m_usd": round(efectivo / usd_val, 3),
        "cartera_vr_disponible_m_clp": round(vr_disp, 3),
        "cartera_vr_comprometida_m_clp": round(vr_comp, 3),
        "operaciones_financiamiento_crv_m_clp": round(crv_activos, 3),
        "operaciones_financiamiento_crv_m_usd": round(crv_activos / usd_val, 3),
        "obligaciones_retrocompra_vrc_m_clp": round(vrc_pasivos, 3),
        "obligaciones_retrocompra_vrc_m_usd": round(vrc_pasivos / usd_val, 3),
        "cuadre_balance": cuadre
    }

def parse_pdf_repos(pdf_bytes, rut, nombre, periodo, fecha_corte, usd_rate):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return [], []

    nivel2_records = []
    nivel3_records = []
    usd_val = usd_rate if usd_rate > 0 else 900.0

    # 1. Nivel 2: Contrapartes y Tasas
    for p_idx in range(len(doc)):
        page_txt = doc[p_idx].get_text()
        txt_upper = page_txt.upper()
        if any(h in txt_upper for h in [
            "OPERACIONES DE COMPRA CON RETROVENTA SOBRE INSTRUMENTOS",
            "OPERACIONES DE VENTA CON RETROCOMPRA SOBRE INSTRUMENTOS",
            "OBLIGACIONES POR OPERACIONES DE VENTA CON RETROCOMPRA",
            "COMPRAS CON RETROVENTA SOBRE INSTRUMENTOS DE RENTA VARIABLE"
        ]):
            lines = [l.strip() for l in page_txt.split("\n") if l.strip()]
            tipo_op = "Simultánea / Retroventa (CRV)" if "COMPRA" in txt_upper else "Retrocompra (VRC)"
            
            for seg in ["Personas naturales", "Personas jurídicas", "Intermediarios de valores", "Inversionistas institucionales", "Inversionistas Institucionales", "Partes relacionadas", "Entidades Relacionadas", "Totales", "Total"]:
                for i, line in enumerate(lines):
                    if seg.lower() == line.lower() or (seg.lower() in line.lower() and len(line) < 35):
                        cand_nums = []
                        for off in range(1, 8):
                            if i + off < len(lines):
                                nxt = lines[i+off]
                                if any(s_check.lower() in nxt.lower() for s_check in ["personas", "intermediarios", "inversionistas", "partes", "entidades", "total", "al 31", "nota"]):
                                    break
                                val = parse_num(nxt)
                                cand_nums.append(val)
                        
                        if len(cand_nums) >= 4:
                            tasa = cand_nums[0] if cand_nums[0] < 20.0 else 0.0
                            h7 = cand_nums[1] if tasa > 0 else cand_nums[0]
                            m7 = cand_nums[2] if tasa > 0 else cand_nums[1]
                            tot = cand_nums[3] if tasa > 0 else cand_nums[2]
                            suby = cand_nums[4] if len(cand_nums) > 4 and (tasa > 0) else (cand_nums[3] if len(cand_nums) > 3 else 0.0)
                            
                            seg_norm = seg.replace("Institucionales", "institucionales").replace("Entidades Relacionadas", "Partes relacionadas").replace("Total", "Totales")
                            
                            nivel2_records.append({
                                "id_pacto": f"{periodo}_{rut}_{seg_norm}_{tipo_op[:3]}",
                                "periodo": periodo,
                                "fecha_corte": fecha_corte,
                                "rut": rut,
                                "nombre_empresa": nombre,
                                "tipo_operacion": tipo_op,
                                "segmento_contraparte": seg_norm,
                                "tasa_promedio_pct": round(tasa, 4),
                                "monto_hasta_7d_m_clp": round(h7, 3),
                                "monto_mas_7d_m_clp": round(m7, 3),
                                "monto_total_m_clp": round(tot, 3),
                                "monto_total_m_usd": round(tot / usd_val, 3),
                                "valor_razonable_garantia_m_clp": round(suby, 3),
                                "valor_razonable_garantia_m_usd": round(suby / usd_val, 3)
                            })

    # 2. Nivel 3: Detalle de Colaterales por Nemotecnico
    for p_idx in range(len(doc)):
        page_txt = doc[p_idx].get_text()
        txt_upper = page_txt.upper()
        if any(h in txt_upper for h in [
            "INSTRUMENTOS DE RENTA VARIABLE RECIBIDOS Y UTILIZADOS",
            "COMPRAS CON RETROVENTA SOBRE IRV",
            "GARANTÍAS POR OPERACIONES A PLAZO CUBIERTAS"
        ]):
            lines = [l.strip() for l in page_txt.split("\n") if l.strip()]
            for i, l in enumerate(lines):
                clean_nem = l.replace(" ", "").upper()
                if re.match(r"^[A-Z0-9\-]{2,12}$", clean_nem) and not any(k in clean_nem for k in ["NOTA", "TOTAL", "M$", "PAGINA", "BCS", "BEC", "ENERO", "MARZO", "JUNIO", "SEPTIEMBRE", "DICIEMBRE", "CHILE", "ACTIVOS", "PASIVOS"]):
                    cand_nums = []
                    for off in range(1, 6):
                        if i + off < len(lines):
                            nxt = lines[i+off]
                            if re.match(r"^[A-Z0-9\-]{2,12}$", nxt.replace(" ", "").upper()) and not re.match(r"^[\d\.\,\-\s\(\)]+$", nxt):
                                break
                            val = parse_num(nxt)
                            if val != 0.0:
                                cand_nums.append(val)
                    if cand_nums:
                        unidades = cand_nums[0] if len(cand_nums) >= 2 else 0.0
                        monto = cand_nums[1] if len(cand_nums) >= 2 else cand_nums[0]
                        tipo_inst = "Acción Nacional (IRV)" if not "CFI" in clean_nem else "Cuota de Fondo de Inversión (CFI)"
                        nivel3_records.append({
                            "id_colateral": f"{periodo}_{rut}_{clean_nem}_{len(nivel3_records)}",
                            "periodo": periodo,
                            "fecha_corte": fecha_corte,
                            "rut": rut,
                            "nombre_empresa": nombre,
                            "nemotecnico": clean_nem,
                            "tipo_instrumento": tipo_inst,
                            "unidades_pactadas": round(unidades, 2),
                            "monto_pactado_m_clp": round(monto, 3),
                            "monto_pactado_m_usd": round(monto / usd_val, 3),
                            "valor_mercado_m_clp": round(monto, 3),
                            "valor_mercado_m_usd": round(monto / usd_val, 3)
                        })

    return nivel2_records, nivel3_records

def run_extraction():
    universo_path = os.path.join(OUT_DIR, "corredoras_bolsa_registro_universo.parquet")
    if not os.path.exists(universo_path):
        print("No se encontro el universo de corredoras. Ejecutar 01 primero.")
        return

    df_univ = pd.read_parquet(universo_path)
    # Filtrar activas con row_id valido
    df_active = df_univ[(df_univ["estado_vigencia"] == "Vigente") & (df_univ["row_id"] != "")].copy()
    print(f"Iniciando extraccion para {len(df_active)} corredoras vigentes...")

    usd_map = get_usd_rates_map()

    # Cargar checkpoints si existen
    eeff_list = []
    nivel2_list = []
    nivel3_list = []

    p_eeff = os.path.join(OUT_DIR, "corredoras_bolsa_caratula_eeff_historico.parquet")
    p_n2 = os.path.join(OUT_DIR, "corredoras_repos_contrapartes_tasas.parquet")
    p_n3 = os.path.join(OUT_DIR, "corredoras_repos_colaterales_detalle.parquet")

    if os.path.exists(p_eeff):
        try:
            eeff_list = pd.read_parquet(p_eeff).to_dict(orient="records")
        except Exception:
            pass
    if os.path.exists(p_n2):
        try:
            nivel2_list = pd.read_parquet(p_n2).to_dict(orient="records")
        except Exception:
            pass
    if os.path.exists(p_n3):
        try:
            nivel3_list = pd.read_parquet(p_n3).to_dict(orient="records")
        except Exception:
            pass

    processed_keys = set(f"{r['periodo']}_{r['rut']}" for r in eeff_list)

    # Anios y meses a procesar (trimestres 2018 a 2026)
    quarters = [
        (2026, 6, "2026-06", "2026-06-30"),
        (2026, 3, "2026-03", "2026-03-31"),
        (2025, 12, "2025-12", "2025-12-31"),
        (2025, 9, "2025-09", "2025-09-30"),
        (2025, 6, "2025-06", "2025-06-30"),
        (2025, 3, "2025-03", "2025-03-31"),
        (2024, 12, "2024-12", "2024-12-31"),
        (2024, 9, "2024-09", "2024-09-30"),
        (2024, 6, "2024-06", "2024-06-30"),
        (2024, 3, "2024-03", "2024-03-31"),
        (2023, 12, "2023-12", "2023-12-31"),
        (2023, 9, "2023-09", "2023-09-30"),
        (2023, 6, "2023-06", "2023-06-30"),
        (2023, 3, "2023-03", "2023-03-31"),
        (2022, 12, "2022-12", "2022-12-31"),
        (2022, 9, "2022-09", "2022-09-30"),
        (2022, 6, "2022-06", "2022-06-30"),
        (2022, 3, "2022-03", "2022-03-31"),
        (2021, 12, "2021-12", "2021-12-31"),
        (2021, 9, "2021-09", "2021-09-30"),
        (2021, 6, "2021-06", "2021-06-30"),
        (2021, 3, "2021-03", "2021-03-31"),
        (2020, 12, "2020-12", "2020-12-31"),
        (2020, 6, "2020-06", "2020-06-30"),
        (2019, 12, "2019-12", "2019-12-31"),
        (2018, 12, "2018-12", "2018-12-31")
    ]

    total_ops = len(df_active) * len(quarters)
    count = 0
    extracted_eeff = 0
    extracted_n2 = 0
    extracted_n3 = 0

    print(f"Total combinaciones corredora-periodo a evaluar: {total_ops}")

    for _, row in df_active.iterrows():
        rut = row["rut"]
        cuerpo = row["rut_cuerpo"]
        nombre = row["nombre_empresa"]
        row_id = row["row_id"]

        print(f"\nProcesando {nombre} (RUT: {rut})...")

        for yr, mm, per, f_corte in quarters:
            count += 1
            key = f"{per}_{rut}"
            if key in processed_keys:
                continue

            usd_rate = usd_map.get(per, 900.0)

            # Buscar links en pestania 3
            xml_url, pdf_url = fetch_links(cuerpo, row_id, yr, mm)
            if not xml_url and not pdf_url:
                continue

            # Nivel 1: Descargar XML en RAM y parsear
            if xml_url:
                try:
                    req_x = urllib.request.Request(xml_url, headers=HEADERS)
                    with urllib.request.urlopen(req_x, context=ssl_ctx, timeout=20) as resp:
                        xml_bytes = resp.read()
                    eeff_rec = parse_xml_balance(xml_bytes, rut, nombre, per, f_corte, usd_rate)
                    if eeff_rec:
                        eeff_list.append(eeff_rec)
                        extracted_eeff += 1
                    del xml_bytes
                except Exception as e:
                    pass

            # Nivel 2 y 3: Descargar PDF en RAM y parsear (desactivado: PUBLICAR_PACTOS_REPOS)
            if pdf_url and PUBLICAR_PACTOS_REPOS:
                try:
                    req_p = urllib.request.Request(pdf_url, headers=HEADERS)
                    with urllib.request.urlopen(req_p, context=ssl_ctx, timeout=30) as resp:
                        pdf_bytes = resp.read()
                    n2_recs, n3_recs = parse_pdf_repos(pdf_bytes, rut, nombre, per, f_corte, usd_rate)
                    if n2_recs:
                        nivel2_list.extend(n2_recs)
                        extracted_n2 += len(n2_recs)
                    if n3_recs:
                        nivel3_list.extend(n3_recs)
                        extracted_n3 += len(n3_recs)
                    del pdf_bytes
                except Exception as e:
                    pass

            processed_keys.add(key)
            time.sleep(0.05)

        # Guardar checkpoint intermedio cada corredora
        if eeff_list:
            df_e = pd.DataFrame(eeff_list).drop_duplicates(subset=["periodo", "rut"])
            df_e.to_parquet(p_eeff, index=False)
            df_e.to_json(p_eeff.replace(".parquet", ".json"), orient="records", indent=2, force_ascii=False)

            # Sincronizar balance resumen
            p_res = os.path.join(OUT_DIR, "corredoras_bolsa_balance_resumen.parquet")
            cols_res = ["id_balance", "periodo", "fecha_corte", "rut", "nombre_empresa",
                        "total_activos_m_clp", "total_activos_m_usd", "total_pasivos_m_clp", "total_pasivos_m_usd",
                        "patrimonio_neto_m_clp", "patrimonio_m_usd", "efectivo_equivalentes_m_clp", "efectivo_equivalentes_m_usd",
                        "utilidad_ejercicio_m_clp", "utilidad_ejercicio_m_usd"]
            df_res = df_e[[c for c in cols_res if c in df_e.columns]].copy()
            df_res.to_parquet(p_res, index=False)
            df_res.to_json(p_res.replace(".parquet", ".json"), orient="records", indent=2, force_ascii=False)

        if nivel2_list:
            df_n2 = pd.DataFrame(nivel2_list).drop_duplicates(subset=["id_pacto"])
            df_n2.to_parquet(p_n2, index=False)
            df_n2.to_json(p_n2.replace(".parquet", ".json"), orient="records", indent=2, force_ascii=False)

        if nivel3_list:
            df_n3 = pd.DataFrame(nivel3_list).drop_duplicates(subset=["id_colateral"])
            df_n3.to_parquet(p_n3, index=False)
            df_n3.to_json(p_n3.replace(".parquet", ".json"), orient="records", indent=2, force_ascii=False)

        print(f"Checkpoint: EEFF={len(eeff_list)}, Nivel 2 Pactos={len(nivel2_list)}, Nivel 3 Colaterales={len(nivel3_list)}")

    print("\nExtraccion completada exitosamente!")
    print(f"Total Balances EEFF (Nivel 1): {len(eeff_list)}")
    print(f"Total Contratos REPO por Contraparte (Nivel 2): {len(nivel2_list)}")
    print(f"Total Tickers / Instrumentos en Colateral (Nivel 3): {len(nivel3_list)}")

if __name__ == "__main__":
    run_extraction()

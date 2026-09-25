"""
Pipeline Especializado de Derivados y Pactos - Circular 1835 (Compañías de Seguros)
===================================================================================
Módulo: seguros / circular_1835_cartera
Procesa todos los archivos p*.txt de los ZIPs de Seguros Generales y de Vida.
Genera 4 datasets normalizados e independientes:
  - b7_forwards.parquet  (Tipo 3: Forwards Cambiarios y de Inflación)
  - b7_swaps.parquet     (Tipo 5: Swaps de Moneda y Tasa)
  - b7_repos.parquet     (Tipo 6: Pactos y Repos de Liquidez)
  - b7_opciones.parquet  (Tipo 2: Opciones Financieras)

Soporta tanto el layout histórico (489 caracteres) como el moderno (587 caracteres).
Exporta en Parquet y en CSV con UTF-8 BOM para apertura nativa en Excel.
"""

import os
import sys
import glob
import zipfile
import re
import pandas as pd
from datetime import datetime

# Rutas del módulo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
INPUTS_DIR = os.path.join(MODULE_DIR, "inputs")
OUTPUTS_DIR = os.path.join(MODULE_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)


# =============================================================================
# FUNCIONES AUXILIARES DE CONVERSIÓN
# =============================================================================
def _to_float(s, scale=1.0):
    if not s:
        return 0.0
    s_clean = s.strip().replace("+", "")
    try:
        return float(s_clean) / scale
    except ValueError:
        return 0.0


def _parse_signed_float(s, scale=1.0):
    """Extrae un float numérico con signo de un substring de forma resiliente."""
    if not s:
        return 0.0
    s_clean = s.strip()
    m = re.search(r'([+-]?\d+(?:\.\d+)?)', s_clean)
    if m:
        try:
            return float(m.group(1)) / scale
        except ValueError:
            return 0.0
    return 0.0


def _format_date(s):
    s_clean = s.strip()
    if len(s_clean) == 8 and s_clean.isdigit():
        return f"{s_clean[:4]}-{s_clean[4:6]}-{s_clean[6:]}"
    return s_clean


# =============================================================================
# PARSERS POR TIPO DE INSTRUMENTO
# =============================================================================

def parse_forward_row(line, meta):
    """
    Parsea una fila de Forward (Tipo 3) usando anclaje dinámico sobre bloques de signos.
    Inmune a variaciones de longitud de línea (460, 489, 585, 587 caracteres).
    """
    is_587 = len(line) >= 550

    # 1. Metadatos generales y contraparte
    row = {
        **meta,
        "instrumento": "FORWARD",
        "objetivo": line[1:6].strip(),
        "tipo_operacion": line[6:16].strip(),
        "folio_operacion": line[16:28].strip() if is_587 else line[16:26].strip(),
        "item_operacion": line[28:31].strip() if is_587 else line[26:29].strip(),
        "fecha_operacion": _format_date(line[31:39] if is_587 else line[29:37]),
        "fecha_vencimiento": _format_date(line[39:47] if is_587 else line[37:45]),
        "rut_contraparte": line[47:77].strip() if is_587 else "",
        "nombre_contraparte": line[77:137].strip() if is_587 else line[45:105].strip(),
        "pais_contraparte": line[137:139].strip() if is_587 else line[105:107].strip(),
        "relacionado": line[139:141].strip() if is_587 else line[107:109].strip(),
        "clasificacion_riesgo": line[141:156].strip() if is_587 else line[109:124].strip(),
        "reserva_fondo": line[163:168].strip() if is_587 else line[124:129].strip(),
        "nombre_fondo": line[168:198].strip() if is_587 else line[129:159].strip(),
        "nombre_cartera": line[198:228].strip() if is_587 else line[159:189].strip(),
        "subyacente_pata_larga": line[228:258].strip() if is_587 else line[189:219].strip(),
        "subyacente_pata_corta": line[258:288].strip() if is_587 else line[219:249].strip(),
        "nocional_pata_larga": _to_float(line[288:304] if is_587 else line[249:265], 10000.0),
        "nocional_pata_corta": _to_float(line[304:320] if is_587 else line[265:281], 10000.0),
        "monto_larga_m_clp": _to_float(line[320:334], 1.0) if is_587 else 0.0,
        "monto_corta_m_clp": _to_float(line[334:344], 1.0) if is_587 else 0.0,
        "moneda": "",
        "precio_forward_pactado": 0.0,
        "valor_mercado_activo_m_clp": 0.0,
        "precio_spot_mercado": 0.0,
        "precio_forward_mercado": 0.0,
        "tasa_descuento_flujos": 0.0,
        "valor_razonable_mtm_m_clp": 0.0,
        "fuente_valorizacion": "",
        "monto_activos_en_margen": 0.0,
        "monto_activo": 0.0,
        "monto_pasivo": 0.0,
        "efecto_resultados_m_clp": 0.0,
        "tsa": "",
        "clasificacion_eeff": "",
        "layout_version": "587_CHARS" if is_587 else "489_CHARS"
    }

    # 2. Anclaje dinámico por patrones con signo ([+-]\d{12,14})
    signs = list(re.finditer(r'([+-]\d{11,14})', line))
    if len(signs) >= 3:
        # signs[0]: tasa de descuento
        tasa = _parse_signed_float(signs[0].group(1), 1000.0)
        if abs(tasa) > 100.0:
            tasa /= 10.0
        row["tasa_descuento_flujos"] = tasa

        # signs[1]: valor razonable MTM
        row["valor_razonable_mtm_m_clp"] = _parse_signed_float(signs[1].group(1), 1.0)

        # signs[2]: efecto en resultados
        row["efecto_resultados_m_clp"] = _parse_signed_float(signs[2].group(1), 1.0)

        # Bloque de precios (59 dígitos justo antes del primer signo)
        s0 = signs[0].start()
        p_block = line[max(0, s0 - 61):s0].strip()
        if len(p_block) >= 50:
            # 15 digitos: forward pactado
            fwd_pact = _to_float(p_block[-59:-44], 100000.0)
            val_act = _to_float(p_block[-44:-29], 1.0)
            spot = _to_float(p_block[-29:-15], 10000.0)
            fwd_merc = _to_float(p_block[-15:], 100000.0)

            # Si el precio pactado es en CLP pero excede rango razonable (ej. > 50000), ajustar escala
            if fwd_pact > 50000.0:
                fwd_pact /= 10.0
            if fwd_merc > 50000.0:
                fwd_merc /= 10.0

            row["precio_forward_pactado"] = fwd_pact
            row["valor_mercado_activo_m_clp"] = val_act
            row["precio_spot_mercado"] = spot
            row["precio_forward_mercado"] = fwd_merc

        # Moneda: buscar en los caracteres anteriores al bloque de precios
        moneda_sub = line[max(0, s0 - 75):max(0, s0 - 55)]
        m_curr = re.findall(r'(PROM|UF|\$\$|EUR|USD|GBP|CLP)', moneda_sub)
        if m_curr:
            row["moneda"] = m_curr[-1]

        # Bloque intermedio entre signs[1] y signs[2]
        s1_end = signs[1].end()
        s2_start = signs[2].start()
        mid_chunk = line[s1_end:s2_start]
        if len(mid_chunk) >= 30:
            row["fuente_valorizacion"] = mid_chunk[:30].strip()
            # Montos restantes
            post_fuente = mid_chunk[30:]
            digits = re.findall(r'\d+', post_fuente)
            if len(digits) >= 3:
                row["monto_activos_en_margen"] = _to_float(digits[0], 1.0)
                row["monto_activo"] = _to_float(digits[1], 1.0)
                row["monto_pasivo"] = _to_float(digits[2], 1.0)
            elif len(digits) == 2:
                row["monto_activo"] = _to_float(digits[0], 1.0)
                row["monto_pasivo"] = _to_float(digits[1], 1.0)

        # Sufijo tras signs[2]
        s2_end = signs[2].end()
        tail = line[s2_end:].strip()
        if len(tail) >= 2:
            row["tsa"] = tail[:2].strip()
            row["clasificacion_eeff"] = tail[2:].strip()

    elif len(signs) == 2:
        row["valor_razonable_mtm_m_clp"] = _parse_signed_float(signs[0].group(1), 1.0)
        row["efecto_resultados_m_clp"] = _parse_signed_float(signs[1].group(1), 1.0)
    else:
        # Fallback posicional
        if is_587:
            row["moneda"] = line[344:350].strip()
            row["precio_forward_pactado"] = _to_float(line[350:365], 100000.0)
            row["valor_mercado_activo_m_clp"] = _to_float(line[365:381], 1.0)
            row["precio_spot_mercado"] = _to_float(line[381:395], 10000.0)
            row["precio_forward_mercado"] = _to_float(line[395:410], 100000.0)
            row["tasa_descuento_flujos"] = _to_float(line[410:424], 1000.0)
            row["valor_razonable_mtm_m_clp"] = _to_float(line[424:438], 1.0)
            row["fuente_valorizacion"] = line[452:482].strip()
            row["efecto_resultados_m_clp"] = _to_float(line[523:537], 1.0)
        else:
            row["moneda"] = line[279:285].strip()
            row["precio_forward_pactado"] = _to_float(line[285:300], 100000.0)
            row["valor_mercado_activo_m_clp"] = _to_float(line[300:314], 1.0)
            row["precio_spot_mercado"] = _to_float(line[314:326], 10000.0)
            row["precio_forward_mercado"] = _to_float(line[326:340], 100000.0)
            row["tasa_descuento_flujos"] = _to_float(line[340:354], 1000.0)
            row["valor_razonable_mtm_m_clp"] = _to_float(line[354:368], 1.0)
            row["fuente_valorizacion"] = line[368:398].strip()
            row["efecto_resultados_m_clp"] = _to_float(line[437:451], 1.0)

    return row


def parse_swap_row(line, meta):
    """Parsea una fila de Swap (Tipo 5) con anclaje dinámico."""
    is_587 = len(line) >= 550

    row = {
        **meta,
        "instrumento": "SWAP",
        "objetivo": line[1:6].strip(),
        "tipo_operacion": line[6:16].strip(),
        "folio_operacion": line[16:28].strip() if is_587 else line[16:26].strip(),
        "item_operacion": line[28:31].strip() if is_587 else line[26:29].strip(),
        "fecha_operacion": _format_date(line[31:39] if is_587 else line[29:37]),
        "fecha_vencimiento": _format_date(line[39:47] if is_587 else line[37:45]),
        "rut_contraparte": line[47:77].strip() if is_587 else "",
        "nombre_contraparte": line[77:137].strip() if is_587 else line[45:105].strip(),
        "pais_contraparte": line[137:139].strip() if is_587 else line[105:107].strip(),
        "relacionado": line[139:141].strip() if is_587 else line[107:109].strip(),
        "clasificacion_riesgo": line[141:156].strip() if is_587 else line[109:124].strip(),
        "moneda_pata_larga": line[222:228].strip() if is_587 else line[156:162].strip(),
        "moneda_pata_corta": line[228:234].strip() if is_587 else line[162:168].strip(),
        "tasa_contrato_larga": line[234:264].strip() if is_587 else line[168:198].strip(),
        "tasa_contrato_corta": line[264:294].strip() if is_587 else line[198:228].strip(),
        "valor_razonable_mtm_m_clp": 0.0,
        "fuente_valorizacion": "",
        "reserva_fondo": "",
        "nombre_fondo": "",
        "nombre_cartera": "",
        "monto_activos_en_margen": 0.0,
        "monto_activo": 0.0,
        "monto_pasivo": 0.0,
        "efecto_resultados_m_clp": 0.0,
        "tsa": "",
        "clasificacion_eeff": "",
        "layout_version": "587_CHARS" if is_587 else "489_CHARS"
    }

    signs = list(re.finditer(r'([+-]\d{11,14})', line))
    if len(signs) >= 2:
        row["valor_razonable_mtm_m_clp"] = _parse_signed_float(signs[0].group(1), 1.0)
        row["efecto_resultados_m_clp"] = _parse_signed_float(signs[-1].group(1), 1.0)

        # Entre signs[0] y signs[-1]
        mid = line[signs[0].end():signs[-1].start()]
        if len(mid) >= 30:
            row["fuente_valorizacion"] = mid[:30].strip()

        # Montos activo y pasivo antes del último signo
        pre_last = line[max(0, signs[-1].start() - 30):signs[-1].start()]
        d = re.findall(r'\d{8,14}', pre_last)
        if len(d) >= 2:
            row["monto_activo"] = _to_float(d[-2], 1.0)
            row["monto_pasivo"] = _to_float(d[-1], 1.0)
        elif len(d) == 1:
            row["monto_activo"] = _to_float(d[-1], 1.0)
    else:
        # Fallback posicional
        if is_587:
            row["valor_razonable_mtm_m_clp"] = _to_float(line[389:403], 1.0)
            row["fuente_valorizacion"] = line[417:447].strip()
            row["monto_activo"] = _to_float(line[539:552], 1.0)
            row["monto_pasivo"] = _to_float(line[552:565], 1.0)
            row["efecto_resultados_m_clp"] = _to_float(line[565:579], 1.0)
        else:
            row["valor_razonable_mtm_m_clp"] = _to_float(line[319:333], 1.0)
            row["fuente_valorizacion"] = line[333:363].strip()
            row["monto_activo"] = _to_float(line[441:454], 1.0)
            row["monto_pasivo"] = _to_float(line[454:467], 1.0)
            row["efecto_resultados_m_clp"] = _to_float(line[467:481], 1.0)

    return row


def parse_repo_row(line, meta):
    """Parsea una fila de Repos / Pactos de Retrocompra (Tipo 6) con calibración exacta."""
    is_587 = len(line) >= 550

    row = {
        **meta,
        "instrumento": "REPO_PACTO",
        "tipo_operacion": line[1:11].strip(),
        "folio_operacion": line[11:21].strip(),
        "item_operacion": line[21:24].strip(),
        "fecha_operacion": _format_date(line[24:32]),
        "fecha_vencimiento": _format_date(line[32:40]),
        "codigo_contraparte": line[40:53].strip(),
        "nombre_contraparte": line[53:113].strip(),
        "pais_contraparte": line[113:115].strip(),
        "relacionado": line[115:117].strip(),
        "activo_objeto_nemotecnico": line[117:147].strip(),
        "serie_activo_objeto": line[147:177].strip(),
        "rut_activo_objeto": line[177:187].strip(),
        "valor_nominal": _to_float(line[187:203], 10000.0),
        "tasa_pacto": 0.0,
        "tasa_mercado": 0.0,
        "moneda": "",
        "tasa_efectiva": 0.0,
        "valor_inicial_um": 0.0,
        "valor_pactado_um": 0.0,
        "interes_devengado_m_clp": 0.0,
        "layout_version": "587_CHARS" if is_587 else "489_CHARS"
    }

    # Búsqueda dinámica de la moneda en la zona de pactos (pos 235-255)
    m_curr = re.search(r'(UF|\$\$|PROM|CLP|USD|EUR)', line[235:255])
    if m_curr:
        cp = 235 + m_curr.start()
        row["moneda"] = m_curr.group(1)

        # Tasas antes de la moneda
        tp = _parse_signed_float(line[cp-39:cp-25], 10000.0)
        if tp > 100.0:
            tp /= 10.0
        row["tasa_pacto"] = tp

        tm = _parse_signed_float(line[cp-25:cp-11], 10000.0)
        if tm > 100.0:
            tm /= 10.0
        row["tasa_mercado"] = tm

        # Tras la moneda
        te = _parse_signed_float(line[cp+6:cp+20], 10000.0)
        if te > 100.0:
            te /= 10.0
        row["tasa_efectiva"] = te

        row["valor_inicial_um"] = _parse_signed_float(line[cp+20:cp+36], 100000.0)
        row["valor_pactado_um"] = _parse_signed_float(line[cp+36:cp+52], 100000.0)
        row["interes_devengado_m_clp"] = _parse_signed_float(line[cp+68:cp+84], 10000.0)
    else:
        # Fallback tradicional
        row["tasa_pacto"] = _to_float(line[203:217], 10000.0)
        row["tasa_mercado"] = _to_float(line[217:231], 10000.0)
        row["moneda"] = line[244:250].strip()
        row["tasa_efectiva"] = _to_float(line[250:264], 10000.0)
        row["valor_inicial_um"] = _to_float(line[264:280], 10000.0)
        row["valor_pactado_um"] = _to_float(line[280:296], 10000.0)
        row["interes_devengado_m_clp"] = _to_float(line[296:312], 10000.0)

    return row


def parse_opcion_row(line, meta):
    """Parsea una fila de Opciones Financieras (Tipo 2) con anclaje dinámico."""
    row = {
        **meta,
        "instrumento": "OPCION",
        "objetivo": line[1:4].strip(),
        "tipo_operacion": line[4:14].strip(),
        "folio_operacion": line[14:24].strip(),
        "item_operacion": line[24:27].strip(),
        "fecha_operacion": _format_date(line[27:35]),
        "fecha_vencimiento": _format_date(line[35:43]),
        "nombre_contraparte": line[43:103].strip(),
        "nacionalidad": line[103:105].strip(),
        "relacionado": line[105:107].strip(),
        "clasificacion_riesgo": line[107:122].strip(),
        "activo_subyacente_larga": line[122:152].strip(),
        "activo_subyacente_corta": line[152:182].strip(),
        "moneda": line[198:204].strip(),
        "precio_ejercicio_strike": _to_float(line[204:217], 1000.0),
        "precio_spot_subyacente": _to_float(line[217:230], 1000.0),
        "prima_opcion_monto": _to_float(line[230:246], 1000.0),
        "numero_contratos": _to_float(line[265:271], 1.0),
        "valor_razonable_mtm_m_clp": 0.0,
        "fuente_valorizacion": "",
        "efecto_resultados_m_clp": 0.0,
        "layout_version": "VIGENTE"
    }

    signs = list(re.finditer(r'([+-]\d{11,14})', line))
    if len(signs) >= 2:
        row["valor_razonable_mtm_m_clp"] = _parse_signed_float(signs[0].group(1), 1.0)
        row["efecto_resultados_m_clp"] = _parse_signed_float(signs[-1].group(1), 1.0)
        mid = line[signs[0].end():signs[-1].start()]
        if len(mid) >= 20:
            row["fuente_valorizacion"] = mid[:30].strip()
    elif len(signs) == 1:
        row["valor_razonable_mtm_m_clp"] = _parse_signed_float(signs[0].group(1), 1.0)
        row["fuente_valorizacion"] = line[signs[0].end():signs[0].end()+30].strip()
    else:
        row["valor_razonable_mtm_m_clp"] = _to_float(line[271:284], 1.0)
        row["fuente_valorizacion"] = line[284:314].strip()

    return row


# =============================================================================
# PIPELINE PRINCIPAL DE PROCESAMIENTO
# =============================================================================

def extract_contracts_from_zip(zip_source, filename_hint=""):
    """
    Extrae todos los contratos forwards, swaps, repos, opciones de un único ZIP.
    zip_source puede ser una ruta (str) o un buffer en memoria (io.BytesIO).
    """
    if isinstance(zip_source, str):
        zname = os.path.basename(zip_source)
        zf_target = zip_source
    else:
        zname = filename_hint or "in_memory.zip"
        zf_target = zip_source

    sector = "GENERALES" if any(k in zname.lower() for k in ["generales", "g.zip", "csgen"]) else "VIDA"

    forwards = []
    swaps = []
    repos = []
    opciones = []

    with zipfile.ZipFile(zf_target, "r") as z:
        target_files = [f for f in z.namelist() if os.path.basename(f).lower().startswith("p")]

        for fn in target_files:
            try:
                lines = z.open(fn).read().decode("latin-1").splitlines()
            except Exception:
                continue

            if not lines:
                continue

            h = lines[0]
            if not h.startswith("1") or len(h) < 20:
                continue

            # Extraer período de forma robusta soportando todos los formatos CMF:
            # - pYYYYMMDD (8 dígitos)
            # - pYYYYMM   (6 dígitos empezando en 20)
            # - pYYMMDD   (6 dígitos históricos)
            fn_base = os.path.basename(fn).lower()
            m8 = re.search(r'p(20\d{2})(\d{2})\d{2}', fn_base)
            if m8:
                periodo = f"{m8.group(1)}-{m8.group(2)}"
            else:
                m6_4 = re.search(r'p(20\d{2})(\d{2})', fn_base)
                if m6_4:
                    periodo = f"{m6_4.group(1)}-{m6_4.group(2)}"
                else:
                    m6_2 = re.search(r'p(\d{2})(\d{2})\d{2}', fn_base)
                    if m6_2:
                        periodo = f"20{m6_2.group(1)}-{m6_2.group(2)}"
                    else:
                        periodo_raw = h[71:77].strip() if len(h) >= 77 else ""
                        periodo = f"{periodo_raw[:4]}-{periodo_raw[4:6]}" if len(periodo_raw) == 6 else periodo_raw

            rut_entidad = f"{h[1:10].strip()}-{h[10:11].strip()}"
            nombre_entidad = h[11:71].strip()

            meta = {
                "periodo": periodo,
                "sector_seguro": sector,
                "rut_aseguradora": rut_entidad,
                "nombre_aseguradora": nombre_entidad,
                "origen_zip": zname,
                "archivo_interno": fn
            }

            for line in lines[1:]:
                if not line or len(line) < 50 or line.startswith(("3000", "5000", "6000", "7000", "9000")):
                    continue

                tipo_op = line[6:16].strip()
                if not tipo_op:
                    continue

                t = line[0]
                if t == "3":
                    forwards.append(parse_forward_row(line, meta))
                elif t == "5":
                    swaps.append(parse_swap_row(line, meta))
                elif t == "6":
                    repos.append(parse_repo_row(line, meta))
                elif t == "2":
                    opciones.append(parse_opcion_row(line, meta))

    return {
        "forwards": forwards,
        "swaps": swaps,
        "repos": repos,
        "opciones": opciones
    }


def consolidate_contracts(contracts_dict):
    """Consolida y deduplica un diccionario de contratos en los 4 archivos Parquet y CSV."""
    results = {}
    for name, data_list in contracts_dict.items():
        parquet_path = os.path.join(OUTPUTS_DIR, f"b7_{name}.parquet")
        csv_path = os.path.join(OUTPUTS_DIR, f"b7_{name}.csv")

        if data_list:
            df = pd.DataFrame(data_list)
            if os.path.exists(parquet_path):
                try:
                    df_old = pd.read_parquet(parquet_path)
                    df = pd.concat([df_old, df], ignore_index=True)
                    dedup_subset = [c for c in ["periodo", "rut_aseguradora", "folio_operacion", "item_operacion", "tipo_operacion"] if c in df.columns]
                    if dedup_subset:
                        df = df.drop_duplicates(subset=dedup_subset, keep="last")
                except Exception:
                    pass

            df.to_parquet(parquet_path, index=False, engine="pyarrow")
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            results[name] = len(data_list)
        else:
            if not os.path.exists(parquet_path):
                pd.DataFrame().to_parquet(parquet_path, index=False, engine="pyarrow")
                pd.DataFrame().to_csv(csv_path, index=False, encoding="utf-8-sig")
            results[name] = 0

    return results


def process_single_zip(zip_source, filename_hint="", delete_zip=True):
    """Procesa un archivo ZIP (en disco o en memoria BytesIO), lo consolida y lo elimina si está en disco."""
    contracts = extract_contracts_from_zip(zip_source, filename_hint=filename_hint)
    counts = consolidate_contracts(contracts)
    if delete_zip and isinstance(zip_source, str) and os.path.exists(zip_source):
        try:
            size_kb = os.path.getsize(zip_source) / 1024
            os.remove(zip_source)
            print(f"  [ELIMINADO] {os.path.basename(zip_source)} ({size_kb:.1f} KB liberados)")
        except Exception as e:
            print(f"  [WARN] No se pudo eliminar {zip_source}: {e}")
    return counts


def process_all_zip_derivatives(delete_zips=False):
    print("=" * 80)
    print("PIPELINE B.7: DERIVADOS Y PACTOS - CIRCULAR 1835 CMF (SEGUROS)")
    print(f"Fecha de Ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if delete_zips:
        print("[MODO EFICIENTE] Se eliminarán los archivos ZIP tras su procesamiento exitoso.")
    print("=" * 80)

    zip_files = sorted(glob.glob(os.path.join(INPUTS_DIR, "**", "*.zip"), recursive=True))
    if not zip_files:
        print(f"[AVISO] No se encontraron archivos .zip en {INPUTS_DIR}")
        return

    print(f"Archivos ZIP encontrados ({len(zip_files)}):")
    for zf in zip_files:
        print(f"  -> {os.path.relpath(zf, MODULE_DIR)} ({os.path.getsize(zf) / 1024:.1f} KB)")

    combined = {"forwards": [], "swaps": [], "repos": [], "opciones": []}
    zips_to_delete = []

    for zpath in zip_files:
        try:
            c = extract_contracts_from_zip(zpath)
            for k in combined:
                combined[k].extend(c[k])
            if delete_zips:
                zips_to_delete.append(zpath)
        except Exception as e:
            print(f"[ERROR] No se pudo leer {os.path.basename(zpath)}: {e}")

    consolidate_contracts(combined)

    if delete_zips and zips_to_delete:
        print("\n" + "-" * 80)
        print(f"LIMPIEZA DE ESPACIO EN DISCO ({len(zips_to_delete)} archivos ZIP eliminados):")
        for zp in zips_to_delete:
            try:
                size_kb = os.path.getsize(zp) / 1024
                os.remove(zp)
                print(f"  [ELIMINADO] {os.path.basename(zp)} ({size_kb:.1f} KB liberados)")
            except Exception as e:
                print(f"  [WARN] No se pudo eliminar {os.path.basename(zp)}: {e}")

    print("\nProcesamiento de derivados completado exitosamente.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline B.7 Derivados y Pactos Seguros")
    parser.add_argument("--delete-zips", action="store_true", help="Eliminar archivos ZIP tras consolidar para ahorrar espacio en disco")
    args = parser.parse_args()

    process_all_zip_derivatives(delete_zips=args.delete_zips)

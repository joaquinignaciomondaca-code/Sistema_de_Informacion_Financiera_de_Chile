#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_extract_ccaf_xbrl.py
Extractor unificado, determinístico y 100% en memoria de Estados Financieros XBRL 
para Cajas de Compensación (CCAF) desde la Comisión para el Mercado Financiero (CMF Chile).

Genera (Parquet + JSON):
1. ccaf_caratula_totales (Balance General y Estado de Resultados: Activos, Pasivos, Patrimonio, Utilidad)
(2026-09-28: se retiraron de la web Nota 8 y colocaciones de crédito social; solo queda el balance
desde el XBRL oficial, junto con la lista de entidades.)
"""

import os
import sys
import io
import re
import json
import urllib.request
import zipfile
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

BASE_DIR = str(_ROOT)
OUT_DIRS = [
    os.path.join(BASE_DIR, "docs", "outputs", "cajas_compensacion"),
]

CCAF_ENTITIES = {
    '81826800': {
        'nombre': 'CCAF Los Andes',
        'rut_formato': '81.826.800-9',
        'tipo_eeff': 'Consolidado'
    },
    '70016160': {
        'nombre': 'CCAF La Araucana',
        'rut_formato': '70.016.160-5',
        'tipo_eeff': 'Consolidado'
    },
    '70016330': {
        'nombre': 'CCAF Los Heroes',
        'rut_formato': '70.016.330-1',
        'tipo_eeff': 'Consolidado'
    },
    '82606800': {
        'nombre': 'CCAF 18 de Septiembre',
        'rut_formato': '82.606.800-K',
        'tipo_eeff': 'Individual'
    }
}

# Períodos objetivo (anuales e intermedios 2019-2026)
TARGET_PERIODS = [
    (2026, 6), (2026, 3),
    (2025, 12), (2025, 9), (2025, 6), (2025, 3),
    (2024, 12), (2024, 9), (2024, 6), (2024, 3),
    (2023, 12), (2023, 9), (2023, 6), (2023, 3),
    (2022, 12), (2021, 12), (2020, 12), (2019, 12)
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_xbrl_zip_url(rut: str, ano: int, mes: int):
    """Obtiene la URL de descarga del archivo XBRL desde novedades_envio_sa_ifrs y entidad.php"""
    nov_url = f"https://www.cmfchile.cl/institucional/mercados/novedades_envio_sa_ifrs.php?mm_ifrs={mes:02d}&aa_ifrs={ano}"
    req = urllib.request.Request(nov_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('latin1')
    except Exception as e:
        return None, None

    match = re.search(rf'<a href=[\'\"](entidad\.php\?[^\'\"]*rut={rut}[^\'\"]*)[\'\"]', html)
    if not match:
        return None, None

    ent_url = 'https://www.cmfchile.cl/institucional/mercados/' + match.group(1).replace('&amp;', '&')
    
    req_ent = urllib.request.Request(ent_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req_ent, timeout=30) as resp:
            ent_html = resp.read().decode('latin1')
    except Exception as e:
        return None, None

    xbrl_match = re.search(r'href=[\"\']([^\"\']*safec_ifrs_verarchivo\.php[^\"\']*)[\"\'][^>]*>Estados financieros \(XBRL\)', ent_html)
    if not xbrl_match:
        return None, None

    xbrl_href = xbrl_match.group(1).replace('&amp;', '&')
    if xbrl_href.startswith('../'):
        xbrl_url = 'https://www.cmfchile.cl/institucional/' + xbrl_href[3:]
    else:
        xbrl_url = xbrl_href

    return xbrl_url, ent_url

def download_and_extract_xbrl_in_memory(xbrl_url: str, referer_url: str):
    """Descarga en stream y extrae el contenido de la instancia XBRL sin tocar el disco"""
    req = urllib.request.Request(xbrl_url, headers={**HEADERS, 'Referer': referer_url})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read()
    except Exception as e:
        return None

    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        for fname in z.namelist():
            if fname.lower().endswith('.xbrl'):
                return z.read(fname).decode('latin1', errors='replace')
    except Exception as e:
        return None

    return None

def parse_xbrl_facts(xbrl_text: str):
    """Extrae todos los tags y contextos numéricos de la instancia XBRL"""
    facts = {}
    pattern = re.compile(r'<((?:ifrs-full|cl-cc|cl-ci):[a-zA-Z0-9_\-]+)\s+[^>]*contextRef=[\'\"]([^\'\"]+)[\'\"][^>]*>([^<]+)</\1>', re.DOTALL)
    for tag, ctx, val_str in pattern.findall(xbrl_text):
        val_clean = val_str.strip()
        try:
            val_num = float(val_clean)
            if tag not in facts:
                facts[tag] = {}
            facts[tag][ctx] = val_num
        except ValueError:
            pass
    return facts

def get_fact(facts, tag, preferred_contexts):
    if tag not in facts:
        return None
    for ctx in preferred_contexts:
        if ctx in facts[tag]:
            return facts[tag][ctx]
    # Buscar contexto parcial
    for c, v in facts[tag].items():
        if any(p.lower() in c.lower() for p in preferred_contexts):
            return v
    return None

def extract_all():
    print("=" * 80)
    print("INICIANDO EXTRACCION AUTOMATIZADA XBRL CCAF DESDE CMF CHILE")
    print("=" * 80)

    caratula_rows = []

    success_count = 0
    fail_count = 0

    for ano, mes in TARGET_PERIODS:
        for rut, info in CCAF_ENTITIES.items():
            ccaf_nombre = info['nombre']
            rut_fmt = info['rut_formato']
            tipo_eeff = info['tipo_eeff']

            sys.stdout.write(f"[*] Consultando {ccaf_nombre} ({rut}) | Periodo {ano}-{mes:02d}... ")
            sys.stdout.flush()

            xbrl_url, ref_url = get_xbrl_zip_url(rut, ano, mes)
            if not xbrl_url:
                print("No disponible en CMF.")
                continue

            xbrl_text = download_and_extract_xbrl_in_memory(xbrl_url, ref_url)
            if not xbrl_text:
                print("Error en descarga/stream.")
                fail_count += 1
                continue

            facts = parse_xbrl_facts(xbrl_text)
            success_count += 1
            print("OK.")

            # Contextos de cierre para balance y resultados
            instant_ctx = ['CierreTrimestreActual', 'CierreAnoActual', 'SaldoActualFinal', 'AcumuladoActual', 'AcumuladoAnoActual']
            duration_ctx = ['TrimestreAcumuladoActual', 'PeriodoActual', 'AnoActual', 'AcumuladoActual', 'AcumuladoAnoActual']

            # -------------------------------------------------------------
            # 1. CARATULA TOTALES
            # -------------------------------------------------------------
            activos_val = get_fact(facts, 'ifrs-full:Assets', instant_ctx)
            pasivos_val = get_fact(facts, 'ifrs-full:Liabilities', instant_ctx)
            patrimonio_val = get_fact(facts, 'ifrs-full:Equity', instant_ctx)
            utilidad_val = get_fact(facts, 'ifrs-full:ProfitLoss', duration_ctx)

            if activos_val is not None:
                caratula_rows.append({
                    'ano': ano, 'mes': mes, 'ccaf': ccaf_nombre, 'rut': rut_fmt,
                    'tipo_eeff': tipo_eeff, 'asiento_contable': 'Total de activos',
                    'monto_m_clp': round(activos_val / 1e9, 3),
                    'monto_miles_clp': round(activos_val / 1e3, 0),
                    'codigo_fecu': '10000', 'moneda': 'CLP', 'escala': 'Miles de pesos'
                })
            if pasivos_val is not None:
                caratula_rows.append({
                    'ano': ano, 'mes': mes, 'ccaf': ccaf_nombre, 'rut': rut_fmt,
                    'tipo_eeff': tipo_eeff, 'asiento_contable': 'Total de pasivos',
                    'monto_m_clp': round(pasivos_val / 1e9, 3),
                    'monto_miles_clp': round(pasivos_val / 1e3, 0),
                    'codigo_fecu': '20000', 'moneda': 'CLP', 'escala': 'Miles de pesos'
                })
            if patrimonio_val is not None:
                caratula_rows.append({
                    'ano': ano, 'mes': mes, 'ccaf': ccaf_nombre, 'rut': rut_fmt,
                    'tipo_eeff': tipo_eeff, 'asiento_contable': 'Patrimonio total',
                    'monto_m_clp': round(patrimonio_val / 1e9, 3),
                    'monto_miles_clp': round(patrimonio_val / 1e3, 0),
                    'codigo_fecu': '23000', 'moneda': 'CLP', 'escala': 'Miles de pesos'
                })
            if utilidad_val is not None:
                caratula_rows.append({
                    'ano': ano, 'mes': mes, 'ccaf': ccaf_nombre, 'rut': rut_fmt,
                    'tipo_eeff': tipo_eeff, 'asiento_contable': 'Utilidad neta',
                    'monto_m_clp': round(utilidad_val / 1e9, 3),
                    'monto_miles_clp': round(utilidad_val / 1e3, 0),
                    'codigo_fecu': '23050', 'moneda': 'CLP', 'escala': 'Miles de pesos'
                })

    print("\n" + "=" * 80)
    print(f"RESUMEN DE EXTRACCION: {success_count} reportes procesados con éxito.")
    print("=" * 80)

    # Convertir a DataFrames y ordenar
    df_caratula = pd.DataFrame(caratula_rows).sort_values(['ano', 'mes', 'ccaf', 'codigo_fecu'])

    # Guardar en ambas carpetas
    for od in OUT_DIRS:
        os.makedirs(od, exist_ok=True)

        # 1. Carátula
        df_caratula.to_parquet(os.path.join(od, "ccaf_caratula_totales.parquet"), index=False)
        with open(os.path.join(od, "ccaf_caratula_totales.json"), "w", encoding="utf-8") as f:
            json.dump(df_caratula.to_dict(orient="records"), f, indent=2, ensure_ascii=False)

    print(f"[+] ccaf_caratula_totales: {len(df_caratula)} filas guardadas.")
    print("[*] Proceso completado con cero residuos en disco.")

if __name__ == '__main__':
    extract_all()

# -*- coding: utf-8 -*-
"""
extract_cartera_fi.py — Extractor de Carteras IFRS para Fondos de Inversión (CMF)
================================================================================
Módulo: fi / cartera_inversiones / scripts / extract_cartera_fi.py

Descarga y procesa las 6 carteras normativas IFRS desde la CMF:
  - N: Cartera Nacional (Renta Fija, Acciones, Pagarés, Depósitos)
  - E: Cartera Extranjera (ETFs globales, Acciones y Bonos Internacionales)
  - M: Método de Participación (Sociedades Coligadas / Relacionadas)
  - B: Bienes Raíces (Activos Inmobiliarios)
  - O: Opciones Financieras
  - F: Futuros y Forwards (Derivados OTC y Bursátiles)

Características:
  - Multithreading configurable (ThreadPoolExecutor).
  - Soporte de reintentos con backoff exponencial.
  - Guarda directamente en Apache Parquet comprimido con Snappy.
  - Cero residuo en disco intermedio (streaming in-memory).
"""

import os
import sys
import io
import re
import time
import argparse
import logging
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Rutas del módulo
SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
OUTPUTS_DIR = MODULE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

MAESTRO_PARQUET = OUTPUTS_DIR / "maestro_fondos_inversion.parquet"

# Endpoints oficiales CMF IFRS
CMF_ENDPOINTS = {
    'N': "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_nac.php",
    'E': "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_ext.php",
    'M': "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_met_part.php",
    'B': "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_bie_rai.php",
    'O': "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_op.php",
    'F': "https://www.cmfchile.cl/sitio/inc/inf_financiera/ifrs_xml/ifrs_cartera_fut_fw.php"
}

TABLE_NAMES = {
    'N': "fi_cartera_nacional.parquet",
    'E': "fi_cartera_extranjera.parquet",
    'M': "fi_metodo_participacion.parquet",
    'B': "fi_bienes_raices.parquet",
    'O': "fi_opciones.parquet",
    'F': "fi_futuros_forward.parquet"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("ExtractorFFII")


class FIIExtractor:
    def __init__(self, max_workers=6):
        self.max_workers = max_workers
        self.lock = threading.Lock()
        
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=16, pool_maxsize=16)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })

    def fetch_fund_cartera(self, rut, periodo, tipo_cartera):
        url = CMF_ENDPOINTS.get(tipo_cartera)
        params = {"rut": rut, "periodo": periodo, "tipo": "fi", "cartera": tipo_cartera}
        try:
            resp = self.session.get(url, params=params, verify=False, timeout=20)
            if resp.status_code != 200 or len(resp.text) < 500:
                return None

            dfs = pd.read_html(io.BytesIO(resp.content), decimal=',', thousands='.')
            if not dfs:
                return None

            valid_dfs = [df.dropna(how='all', axis=1).dropna(how='all') for df in dfs if len(df.columns) >= 4]
            if not valid_dfs:
                return None

            df = pd.concat(valid_dfs, ignore_index=True, sort=False)
            
            # Detectar cabecera real
            header_idx = None
            for i in range(min(5, len(df))):
                vals = [str(v).strip() for v in df.iloc[i].values if str(v).strip() not in ('', 'nan', 'None')]
                if len(set(vals)) > 1:
                    header_idx = i
                    break
            
            if header_idx is not None:
                new_cols = [str(v).strip() if str(v).strip() not in ('nan', '', 'None') else f'col_{c}' for c, v in enumerate(df.iloc[header_idx])]
                df.columns = new_cols
                df = df.iloc[header_idx + 1:].reset_index(drop=True)

            df = df.dropna(how='all').reset_index(drop=True)
            if df.empty:
                return None

            # Estandarizar nombres de columnas de forma limpia
            clean_names = []
            for col in df.columns:
                c_str = str(col).strip().lower()
                c_str = re.sub(r'[^a-z0-9_]+', '_', c_str).strip('_')
                clean_names.append(c_str if c_str else "col")
            df.columns = clean_names
            
            df["rut_fondo"] = str(rut)
            df["periodo"] = str(periodo)
            df["tipo_cartera"] = tipo_cartera
            df["fecha_proceso"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return df
        except Exception:
            return None

    def process_period(self, periodos, ruts=None, carteras=None):
        carteras = carteras or ['N', 'E', 'F', 'O', 'M']
        
        if not ruts:
            if MAESTRO_PARQUET.exists():
                df_m = pd.read_parquet(MAESTRO_PARQUET)
                ruts = [str(r).lstrip('0') for r in df_m["rut_fondo"].tolist()]
            else:
                log.error("No se encontró maestro_fondos_inversion.parquet.")
                return

        tasks = [(r, p, t) for p in periodos for r in ruts for t in carteras]
        log.info(f"Iniciando extracción para {len(ruts)} fondos, {len(periodos)} períodos. Total tareas: {len(tasks):,}")

        accumulated = {t: [] for t in carteras}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {executor.submit(self.fetch_fund_cartera, r, p, t): (r, p, t) for r, p, t in tasks}
            
            done_count = 0
            found_count = 0
            for future in as_completed(future_to_task):
                done_count += 1
                r, p, t = future_to_task[future]
                df = future.result()
                if df is not None and not df.empty:
                    found_count += 1
                    with self.lock:
                        accumulated[t].append(df)
                
                if done_count % 500 == 0 or done_count == len(tasks):
                    log.info(f"Progreso: {done_count:,}/{len(tasks):,} tareas completadas ({found_count:,} carteras encontradas)")

        # Consolidar a Parquet
        for t, df_list in accumulated.items():
            if df_list:
                df_cat = pd.concat(df_list, ignore_index=True)
                tgt_file = OUTPUTS_DIR / TABLE_NAMES[t]
                
                if tgt_file.exists():
                    df_old = pd.read_parquet(tgt_file)
                    df_cat = pd.concat([df_old, df_cat], ignore_index=True).drop_duplicates()
                
                df_cat.to_parquet(tgt_file, index=False)
                log.info(f"Guardado {tgt_file.name}: {len(df_cat):,} filas totales")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extractor de Carteras IFRS para Fondos de Inversión")
    parser.add_argument("--periodos", nargs="+", default=["202406"], help="Lista de períodos YYYYMM (ej: 202406 202403)")
    parser.add_argument("--workers", type=int, default=6, help="Hilos concurrentes")
    args = parser.parse_args()

    extractor = FIIExtractor(max_workers=args.workers)
    extractor.process_period(periodos=args.periodos)

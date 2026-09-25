"""
Scraper y Consolidador Oficial de Operaciones Repo / Pactos (VRC y CRV) para Fondos de Inversion.
Consulta el endpoint institucional de la CMF:
  https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_informe_vrc_crv.php?rut={run_fondo}&periodo={periodo}

Genera un dataset Parquet de alta velocidad con:
  - id (Surrogate Key deterministica: FI_REPO_{run_fondo}_{periodo}_{idx})
  - run_fondo (FK canonica hacia fi.lista_entidades)
  - Cobertura historica completa (2014-03 a 2026-03)
"""

import sys
import re
import time
import random
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import requests
import pandas as pd
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("RepoScraperFI")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

BASE_URL = "https://www.cmfchile.cl/institucional/inc/inf_financiera/ifrs_xml/ifrs_informe_vrc_crv.php"

def clean_num(val_str):
    if not val_str:
        return 0.0
    v = str(val_str).strip().replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return 0.0

def parse_html_page(html, run_fondo, periodo):
    soup = BeautifulSoup(html, "html.parser")
    operations = []

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if len(tds) >= 10:
                code = tds[0].get_text(strip=True).upper()
                if code in ("CRV", "VRC"):
                    raw_cols = [td.get_text(strip=True) for td in tds]
                    
                    f_inicio = raw_cols[1] if len(raw_cols) > 1 else ""
                    f_termino = raw_cols[2] if len(raw_cols) > 2 else ""
                    contraparte = raw_cols[3] if len(raw_cols) > 3 else ""
                    rut_contraparte = raw_cols[4] if len(raw_cols) > 4 else ""
                    val_inicial = clean_num(raw_cols[5]) if len(raw_cols) > 5 else 0.0
                    moneda = raw_cols[6] if len(raw_cols) > 6 else "$$"
                    tasa = clean_num(raw_cols[7]) if len(raw_cols) > 7 else 0.0
                    val_final = clean_num(raw_cols[8]) if len(raw_cols) > 8 else 0.0
                    val_cierre = clean_num(raw_cols[9]) if len(raw_cols) > 9 else 0.0
                    isin = raw_cols[10] if len(raw_cols) > 10 else ""
                    nemotecnico = raw_cols[11] if len(raw_cols) > 11 else ""
                    emisor_garantia = raw_cols[12] if len(raw_cols) > 12 else ""
                    tipo_inst = raw_cols[13] if len(raw_cols) > 13 else ""
                    val_mercado = clean_num(raw_cols[14]) if len(raw_cols) > 14 else 0.0

                    operations.append({
                        "run_fondo": str(run_fondo),
                        "periodo": str(periodo),
                        "codigo_operacion": code,
                        "tipo_operacion_desc": "Compra con Compromiso de Retroventa (Activo)" if code == "CRV" else "Venta con Compromiso de Retrocompra (Pasivo)",
                        "fecha_inicio": f_inicio,
                        "fecha_termino": f_termino,
                        "nombre_contraparte": contraparte,
                        "rut_contraparte": rut_contraparte,
                        "valor_inicial": val_inicial,
                        "moneda": moneda,
                        "tasa_pct": tasa,
                        "valor_final": val_final,
                        "valorizacion_cierre": val_cierre,
                        "isin": isin,
                        "nemotecnico": nemotecnico,
                        "emisor_garantia": emisor_garantia,
                        "tipo_instrumento_garantia": tipo_inst,
                        "valor_mercado_garantia": val_mercado
                    })

    return operations

def fetch_single(session, run_fondo, periodo):
    params = {"rut": run_fondo, "periodo": periodo}
    try:
        r = session.get(BASE_URL, params=params, headers=HEADERS, verify=False, timeout=12)
        if r.status_code == 200 and len(r.text) > 1000 and "access denied" not in r.text.lower():
            return parse_html_page(r.text, run_fondo, periodo)
    except Exception as e:
        logger.debug(f"Error {run_fondo} {periodo}: {e}")
    return []

def main():
    logger.info("=== INICIO INGESTA REPOS FONDOS DE INVERSION CMF (2014 - 2026) ===")
    
    # 1. Cargar catálogo de fondos
    maestro_path = Path("fi/cartera_inversiones/outputs/maestro_fondos_inversion.parquet")
    if maestro_path.exists():
        df_m = pd.read_parquet(maestro_path)
        col_rut = "run_fondo" if "run_fondo" in df_m.columns else "rut_fondo"
        all_ruts = df_m[col_rut].dropna().astype(str).unique().tolist()
    else:
        all_ruts = []
    
    logger.info(f"Fondos en maestro: {len(all_ruts)}")

    # 2. Cargar fondos que ya tenían repos históricamente
    hist_parquet = Path("fi/repos/outputs/fi_repos_vrc_crv.parquet")
    # 2. Cargar fondos que ya tenían repos históricamente + los descubiertos en sondeo
    hist_parquet = Path("fi/repos/outputs/fi_repos_vrc_crv.parquet")
    known_repo_ruts = {"9280", "7099", "7010", "9077", "9219", "9530", "9082", "9202", "9212", "9514", 
                       "10167", "10344", "9351", "7182", "9635", "10110", "9559", "10574", "9203", "7219", 
                       "9581", "10656", "10705", "9480", "9799", "10639", "10485", "10651", "10162", "10631", 
                       "10630", "10103", "9091", "7210", "10575", "10252", "10405"}
    logger.info(f"Fondos confirmados con operaciones repo: {len(known_repo_ruts)}")

    all_periods = [f"{y}{m:02d}" for y in range(2014, 2027) for m in (3, 6, 9, 12) if not (y == 2026 and m > 3)]
    logger.info(f"Total trimestres a cubrir: {len(all_periods)} (desde {all_periods[0]} hasta {all_periods[-1]})")

    active_repo_ruts = known_repo_ruts

    # 4. FASE 2: Extracción exhaustiva de todos los trimestres para fondos activos
    logger.info("[FASE 2] Descarga exhaustiva de todos los trimestres (37 fondos x 49 trimestres)...")
    all_operations = []
    
    tasks = []
    for rut in sorted(active_repo_ruts, key=int):
        for p in all_periods:
            tasks.append((rut, p))

    logger.info(f"Total tareas de consulta: {len(tasks)}")

    def crawl_worker(task):
        rut, p = task
        s = requests.Session()
        s.headers.update(HEADERS)
        return fetch_single(s, rut, p)

    done_count = 0
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(crawl_worker, t) for t in tasks]
        for future in as_completed(futures):
            ops = future.result()
            if ops:
                all_operations.extend(ops)
            done_count += 1
            if done_count % 300 == 0 or done_count == len(tasks):
                logger.info(f"Progreso: {done_count}/{len(tasks)} consultas ({len(all_operations)} operaciones encontradas)")

    logger.info(f"Descarga finalizada. Total operaciones crudas extraídas: {len(all_operations)}")

    # 5. Consolidar con histórico previo
    df_new = pd.DataFrame(all_operations)
    if not df_new.empty:
        df_new["run_fondo"] = df_new["run_fondo"].astype(str).str.strip()
        df_new["periodo"] = df_new["periodo"].astype(str).str.strip()
        for c in df_new.columns:
            if df_new[c].dtype == "object":
                df_new[c] = df_new[c].fillna("").astype(str).str.strip()

    if hist_parquet.exists():
        df_prev = pd.read_parquet(hist_parquet)
        df_prev["run_fondo"] = df_prev["run_fondo"].astype(str).str.strip()
        df_prev["periodo"] = df_prev["periodo"].astype(str).str.strip()
        for c in df_prev.columns:
            if df_prev[c].dtype == "object":
                df_prev[c] = df_prev[c].fillna("").astype(str).str.strip()
        logger.info(f"Registros previos en Parquet: {len(df_prev)}")
        common_cols = [c for c in df_new.columns if c in df_prev.columns]
        if not df_new.empty:
            df_combined = pd.concat([df_new, df_prev[common_cols]], ignore_index=True)
            dedup_keys = ["run_fondo", "periodo", "codigo_operacion", "nombre_contraparte", "fecha_inicio", "fecha_termino", "valor_inicial"]
            existing_keys = [k for k in dedup_keys if k in df_combined.columns]
            df_combined = df_combined.drop_duplicates(subset=existing_keys, keep="first")
        else:
            df_combined = df_prev
    else:
        df_combined = df_new

    # 6. Normalización integral y auditoría institucional canónica
    logger.info("Aplicando normalización integral canónica (ISIN, RUTs, fechas, tipos, monedas)...")
    try:
        from normalize_repos_fi import normalize_repos_dataframe, export_clean_outputs
    except ImportError:
        from fi.repos.scripts.normalize_repos_fi import normalize_repos_dataframe, export_clean_outputs

    df_clean = normalize_repos_dataframe(df_combined)

    # 7. Guardar Parquet maestro, Parquet docs, JSON y bundle web
    export_clean_outputs(df_clean)

    logger.info(f"Total registros normalizados finales: {len(df_clean):,}")
    logger.info(f"ISINs válidos normalizados: {df_clean['isin'].notna().sum()}")
    logger.info(f"Rango temporal ISO: {df_clean['periodo'].min()} a {df_clean['periodo'].max()}")
    logger.info(f"Fondos con operaciones: {df_clean['run_fondo'].nunique()}")
    logger.info("=== PROCESO DE SCRAPING Y NORMALIZACION COMPLETADO EXITOSAMENTE ===")

if __name__ == "__main__":
    main()

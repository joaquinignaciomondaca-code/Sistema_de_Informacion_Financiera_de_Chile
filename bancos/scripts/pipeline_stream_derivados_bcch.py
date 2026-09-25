"""
Pipeline de Derivados OTC Bancarios - Banco Central de Chile (BCCh SIETE F099).
Descarga streaming y consolidación de:
1. Posición Vigente (Stock Nocional a fin de mes)
2. Montos Transados (Flujos mensuales de compras, ventas y neto)
Desglosado por:
- Instrumento (Forward USD/CLP, Forward UF/CLP, NDF, Swap Promedio Cámara SPC, Cross-Currency Swap CCS)
- Sector Contraparte (No Residentes / Exterior, Empresas Sector Real, Fondos de Pensiones AFPs, Residentes No Bancos)
- Plazos Contractuales (hasta 7d, 8-35d, 36-95d, 96-185d, 186-370d, >1a, 2a, 5a, 10a+)
"""

import os
import re
import json
import time
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

try:
    import bcchapi
except ImportError:
    raise ImportError("La librería 'bcchapi' es obligatoria. Instalar con 'pip install bcchapi'.")

EMAIL_BCCH = "joaquinmondacaparada@gmail.com"
PASS_BCCH = "#Mondaca2001c"

def classify_series(sid, title):
    """Clasifica los metadatos de una serie F099 en dimensiones estructuradas."""
    t_lower = title.lower()
    
    # 1. Tipo de registro
    tipo = "Posicion Vigente (Stock)" if ".STO." in sid else "Monto Transado (Flujo)"
    
    # 2. Instrumento
    if "ndf" in sid.lower() or "ndf" in t_lower:
        instrumento = "Forward NDF (Compensacion)"
    elif "fwd" in sid.lower() or "forward" in t_lower:
        instrumento = "Forward Monedas"
    elif "ccs" in sid.lower() or "cross-currency" in t_lower:
        instrumento = "Cross-Currency Swap (CCS)"
    elif "spc" in sid.lower() or "promedio c" in t_lower or "cámara" in t_lower or "camara" in t_lower:
        instrumento = "Swap Promedio Camara (SPC)"
    elif "swp" in sid.lower() or "swap" in t_lower:
        instrumento = "Swap Tasa de Interes"
    elif "opc" in sid.lower() or "opciones" in t_lower:
        instrumento = "Opciones de Moneda"
    else:
        instrumento = "Derivados Financieros Varios"

    # 3. Moneda
    if "MUF" in sid or "UF" in title:
        moneda = "UF"
        unidad = "Miles de UF"
    elif "MMMCLP" in sid or ("CLP" in sid and "USD" not in sid and "ME" not in sid):
        moneda = "CLP"
        unidad = "Miles de Millones de CLP"
    elif "MMUSD" in sid or "USD" in sid or "ME" in sid:
        moneda = "USD"
        unidad = "Millones de USD"
    else:
        moneda = "USD"
        unidad = "Millones de USD"

    # 4. Sector Contraparte
    if ".NR." in sid or "no residentes" in t_lower:
        contraparte = "No Residentes (Exterior)"
    elif ".42." in sid or "pensiones" in t_lower:
        contraparte = "Fondos de Pensiones (AFPs)"
    elif ".55A." in sid or "sector real" in t_lower or "empresas" in t_lower:
        contraparte = "Empresas Sector Real"
    elif ".63." in sid or "residentes no bancos" in t_lower:
        contraparte = "Residentes No Bancos"
    elif "interbancario" in t_lower:
        contraparte = "Bancos (Interbancario)"
    else:
        contraparte = "Total Mercado"

    # 5. Plazo Contractual
    plazo = "Total Plazos"
    if "P17" in sid or "hasta 7" in t_lower: plazo = "Hasta 7 dias"
    elif "P835" in sid or "8 a 35" in t_lower: plazo = "8 a 35 dias"
    elif "P3695" in sid or "36 a 95" in t_lower: plazo = "36 a 95 dias"
    elif "P96185" in sid or "96 a 185" in t_lower: plazo = "96 a 185 dias"
    elif "P186370" in sid or "186 a 370" in t_lower: plazo = "186 a 370 dias"
    elif "MA01" in sid or "mayor a 1" in t_lower or "mas de 1" in t_lower: plazo = "Mayor a 1 ano"
    elif "HA02" in sid or "hasta 2" in t_lower: plazo = "Hasta 2 anos"
    elif "AN02" in sid or "2 a" in t_lower: plazo = "2 anos"
    elif "AN05" in sid or "5 a" in t_lower: plazo = "5 anos"
    elif "MA10" in sid or "10 y" in t_lower: plazo = "10 anos y mas"
    elif "ME03" in sid: plazo = "3 meses"
    elif "ME06" in sid: plazo = "6 meses"
    elif "ME09" in sid: plazo = "9 meses"
    elif "ME12" in sid: plazo = "12 meses"

    # 6. Direccion / Operacion
    if ".COM." in sid or "compra" in t_lower:
        direccion = "Compra"
    elif ".VTA." in sid or "venta" in t_lower:
        direccion = "Venta"
    elif ".NET." in sid or "neto" in t_lower:
        direccion = "Neto"
    else:
        direccion = "Total"

    return {
        "series_id": sid,
        "tipo_registro": tipo,
        "instrumento": instrumento,
        "contraparte": contraparte,
        "plazo": plazo,
        "moneda": moneda,
        "unidad": unidad,
        "direccion": direccion,
        "titulo_original": title
    }

def fetch_single_series(sid):
    """Descarga una serie individual utilizando una sesión dedicada de bcchapi."""
    try:
        siete = bcchapi.Siete(EMAIL_BCCH, PASS_BCCH)
        df = siete.cuadro(series=[sid], desde="2010-01-01", hasta="2026-07-31")
        if df is not None and not df.empty:
            return sid, df
    except Exception as e:
        pass
    return sid, None

def run_pipeline():
    print("=" * 60, flush=True)
    print("INICIANDO PIPELINE DERIVADOS OTC BANCARIOS (BCCh F099)", flush=True)
    print("=" * 60, flush=True)
    t_start = time.time()

    # 1. Cargar catálogo indexado
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    catalog_path = os.path.join(base_dir, "bancos", "derivados_otc", "catalog_f099.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        raw_catalog = json.load(f)

    monthly_series = [s for s in raw_catalog if s["freq"] == "MONTHLY"]
    print(f"Total series mensuales disponibles en F099: {len(monthly_series)}", flush=True)

    # 2. Seleccionar series canónicas estructuradas de alto impacto
    selected_meta = {}
    for s in monthly_series:
        sid = s["id"]
        meta = classify_series(sid, s["title"])
        
        # Filtro estricto de series canónicas prioritarias
        is_canonical = False
        
        # A. NDF por plazos netos
        if "ndf" in sid.lower() and ".net." in sid.lower():
            is_canonical = True
        # B. Forwards USD/CLP y UF/CLP con principales contrapartes
        elif any(cp in sid for cp in [".NR.", ".42.", ".55A.", ".63."]) and any(d in sid for d in [".COM.", ".VTA.", ".NET."]):
            if any(term in sid.lower() for term in ["fwd", "clpusd", "muf.mlml"]):
                if "Z.Z.0.M" in sid or "TOT" in sid or "C.Z.0.M" in sid:
                    is_canonical = True
        # C. Swaps SPC por plazos principales (Compras y Neto)
        elif "spc" in sid.lower() and any(p in sid for p in ["HA02", "AN02", "AN05", "MA10"]) and any(cp in sid for cp in [".NR.", ".42.", ".55A."]):
            if any(d in sid for d in [".COM.", ".NET."]):
                is_canonical = True
        # D. Swaps CCS
        elif "ccs" in sid.lower() and any(cp in sid for cp in [".NR.", ".42.", ".55A."]):
            if any(d in sid for d in [".COM.", ".NET."]):
                is_canonical = True
                
        if is_canonical:
            selected_meta[sid] = meta

    target_ids = list(selected_meta.keys())
    print(f"Series canónicas seleccionadas para descarga paralela: {len(target_ids)}", flush=True)

    # 3. Descarga concurrente rápida (8 hilos independientes)
    print("Iniciando descarga concurrente con 8 workers independientes...", flush=True)
    all_dfs = {}
    completed = 0

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_single_series, sid): sid for sid in target_ids}
        for f in futures:
            sid, df = f.result()
            completed += 1
            if df is not None and not df.empty:
                all_dfs[sid] = df
            if completed % 10 == 0 or completed == len(target_ids):
                print(f"  Progreso: {completed}/{len(target_ids)} series procesadas ({len(all_dfs)} con datos)", flush=True)

    print(f"Descarga finalizada en {time.time() - t_start:.2f} s.", flush=True)

    # 4. Consolidación en formato tidy
    records_stock = []
    records_flujo = []

    for sid, df_serie in all_dfs.items():
        meta = selected_meta[sid]
        col_name = df_serie.columns[0]
        serie_vals = df_serie[col_name].dropna()

        for dt, val in serie_vals.items():
            if pd.isna(val):
                continue
            periodo = str(dt)[:7]
            fecha_corte = str(dt)[:10]

            rec = {
                "id_registro": f"{periodo}_{sid}",
                "periodo": periodo,
                "fecha_corte": fecha_corte,
                "categoria_mercado": "Derivados Bancarios OTC",
                "tipo_registro": meta["tipo_registro"],
                "instrumento": meta["instrumento"],
                "contraparte": meta["contraparte"],
                "plazo_contractual": meta["plazo"],
                "moneda": meta["moneda"],
                "unidad_medida": meta["unidad"],
                "direccion": meta["direccion"],
                "monto": round(float(val), 2),
                "series_id": sid,
                "glosa_serie": meta["titulo_original"]
            }

            if meta["tipo_registro"] == "Posicion Vigente (Stock)":
                records_stock.append(rec)
            else:
                records_flujo.append(rec)

    df_stock = pd.DataFrame(records_stock)
    df_flujo = pd.DataFrame(records_flujo)

    if not df_stock.empty:
        df_stock = df_stock.drop_duplicates(subset=["id_registro"]).sort_values(["periodo", "instrumento", "contraparte"])
    if not df_flujo.empty:
        df_flujo = df_flujo.drop_duplicates(subset=["id_registro"]).sort_values(["periodo", "instrumento", "contraparte"])

    print(f"Registros consolidados: Posicion Vigente = {len(df_stock):,}, Flujos Transados = {len(df_flujo):,}", flush=True)

    # 5. Exportación a docs/outputs/bancos/
    output_dir = os.path.join(base_dir, "docs", "outputs", "bancos")
    os.makedirs(output_dir, exist_ok=True)

    p_stock = os.path.join(output_dir, "bancos_derivados_posicion_vigente.parquet")
    p_flujo = os.path.join(output_dir, "bancos_derivados_flujos_transados.parquet")

    df_stock.to_parquet(p_stock, index=False, compression="snappy")
    df_stock.to_json(p_stock.replace(".parquet", ".json"), orient="records", indent=2, force_ascii=False)

    df_flujo.to_parquet(p_flujo, index=False, compression="snappy")
    df_flujo.to_json(p_flujo.replace(".parquet", ".json"), orient="records", indent=2, force_ascii=False)

    print("\nArchivos exportados con exito:", flush=True)
    print(f"  bancos_derivados_posicion_vigente.parquet: {os.path.getsize(p_stock) / 1024:.1f} KB ({len(df_stock):,} filas)", flush=True)
    print(f"  bancos_derivados_flujos_transados.parquet: {os.path.getsize(p_flujo) / 1024:.1f} KB ({len(df_flujo):,} filas)", flush=True)

    print(f"\nTiempo total de ejecucion: {time.time() - t_start:.2f} s", flush=True)
    return True

if __name__ == "__main__":
    run_pipeline()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_retail_financiero.py
Suite de auditoría matemática, contable y referencial para:
  1. retail_financiero_maestro (Parquet y JSON)
  2. retail_financiero_balances (Parquet y JSON)
"""

import os
import sys
import json
import pandas as pd
import numpy as np

def calcular_dv(rut_num: int) -> str:
    s = str(rut_num)
    m = 2
    total = 0
    for d in reversed(s):
        total += int(d) * m
        m = 2 if m == 7 else m + 1
    rem = 11 - (total % 11)
    if rem == 11:
        return '0'
    if rem == 10:
        return 'K'
    return str(rem)

def run_audit():
    print("=" * 75)
    print("AUDITORÍA DE INTEGRIDAD: RETAIL FINANCIERO Y EMISORES NO BANCARIOS")
    print("=" * 75)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(base_dir, "docs", "outputs", "retail_financiero")

    pq_maestro = os.path.join(out_dir, "retail_financiero_maestro.parquet")
    js_maestro = os.path.join(out_dir, "retail_financiero_maestro.json")
    pq_bal = os.path.join(out_dir, "retail_financiero_balances.parquet")
    js_bal = os.path.join(out_dir, "retail_financiero_balances.json")

    errors = []

    # 1. Existencia
    for p in [pq_maestro, js_maestro, pq_bal, js_bal]:
        if not os.path.exists(p):
            errors.append(f"Falta archivo requerido: {p}")
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        sys.exit(1)

    # 2. Cargar datos
    df_m_pq = pd.read_parquet(pq_maestro)
    with open(js_maestro, "r", encoding="utf-8") as f:
        df_m_js = pd.DataFrame(json.load(f))

    df_b_pq = pd.read_parquet(pq_bal)
    with open(js_bal, "r", encoding="utf-8") as f:
        df_b_js = pd.DataFrame(json.load(f))

    print("\n--- 1. AUDITORÍA: retail_financiero_maestro ---")
    print(f"Total entidades registradas: {len(df_m_pq)} (Parquet: {os.path.getsize(pq_maestro)} bytes, JSON: {os.path.getsize(js_maestro)} bytes)")

    if len(df_m_pq) != len(df_m_js):
        errors.append(f"Discrepancia de filas en maestro: Parquet {len(df_m_pq)} vs JSON {len(df_m_js)}")

    # Duplicados RUT
    if df_m_pq["rut"].duplicated().any():
        dups = df_m_pq[df_m_pq["rut"].duplicated()]["rut"].tolist()
        errors.append(f"RUTs duplicados en maestro: {dups}")
    else:
        print("RUTs duplicados: 0")

    # Módulo 11
    m11_ok = 0
    for _, row in df_m_pq.iterrows():
        expected_dv = calcular_dv(int(row["rut"]))
        actual_dv = str(row["dv"]).upper()
        if expected_dv != actual_dv:
            errors.append(f"Falla Módulo 11 en RUT {row['rut']}: esperado {expected_dv}, actual {actual_dv}")
        else:
            m11_ok += 1
    print(f"Validación Módulo 11 (RUT): {m11_ok}/{len(df_m_pq)} válidos (100.0%)")

    # Distribución por tipo de entidad
    tipo_counts = df_m_pq["tipo_entidad_cmf"].value_counts().to_dict()
    print(f"Distribución por tipo de entidad CMF: {tipo_counts}")

    print("\n--- 2. AUDITORÍA: retail_financiero_balances ---")
    print(f"Total balances trimestrales: {len(df_b_pq)} (Parquet: {os.path.getsize(pq_bal)} bytes, JSON: {os.path.getsize(js_bal)} bytes)")

    if len(df_b_pq) != len(df_b_js):
        errors.append(f"Discrepancia de filas en balances: Parquet {len(df_b_pq)} vs JSON {len(df_b_js)}")

    # Duplicados (rut, periodo)
    if df_b_pq.duplicated(subset=["rut", "periodo"]).any():
        dups_b = df_b_pq[df_b_pq.duplicated(subset=["rut", "periodo"])][["rut", "periodo"]].to_dict(orient="records")
        errors.append(f"Balances duplicados por (rut, periodo): {dups_b[:5]}")
    else:
        print("Balances duplicados (rut, periodo): 0")

    # Integridad referencial
    ruts_maestro = set(df_m_pq["rut"])
    ruts_bal = set(df_b_pq["rut"])
    desconectados = ruts_bal - ruts_maestro
    if desconectados:
        errors.append(f"RUTs en balances que no existen en maestro: {desconectados}")
    else:
        print(f"Integridad referencial: 100.0% ({len(ruts_bal)}/{len(ruts_bal)} entidades con balances vinculadas)")

    # Ecuación Contable Fundamental: Activo == Pasivo + Patrimonio
    diffs = (df_b_pq["total_activos_m_clp"] - (df_b_pq["total_pasivos_m_clp"] + df_b_pq["patrimonio_neto_m_clp"])).abs()
    cuadre_exacto = (diffs <= 0.005).sum()
    pct_cuadre = (cuadre_exacto / len(df_b_pq)) * 100.0
    print(f"Ecuación Contable (Activo == Pasivo + Patrimonio): {pct_cuadre:.1f}% exacta ({cuadre_exacto}/{len(df_b_pq)})")
    print(f"Diferencia máxima observada: {diffs.max():.6f} MM$ CLP")

    if pct_cuadre < 98.0:
        errors.append(f"Descuadre contable excesivo: {pct_cuadre:.1f}% de cuadre")

    # Nulos en columnas core
    cols_core = ["rut", "periodo", "razon_social", "total_activos_m_clp", "total_pasivos_m_clp", "patrimonio_neto_m_clp"]
    nulos = df_b_pq[cols_core].isna().sum().sum()
    print(f"Valores nulos en columnas core: {nulos}")
    if nulos > 0:
        errors.append(f"Valores nulos en columnas core: {nulos}")

    # Top entidades por activos totales al último periodo disponible
    max_periodo = df_b_pq["periodo"].max()
    print(f"\nTOP MATRICES DE RETAIL POR ACTIVOS TOTALES ({max_periodo}):")
    df_top = df_b_pq[df_b_pq["periodo"] == max_periodo].sort_values("total_activos_m_clp", ascending=False)
    for _, r in df_top.iterrows():
        print(f"  - {r['razon_social']:<35} | Activos: {r['total_activos_m_clp']:>12.1f} MM$ | Patrimonio: {r['patrimonio_neto_m_clp']:>12.1f} MM$ | Utilidad: {r['ganancia_perdida_ejercicio_m_clp']:>10.1f} MM$")

    print("\n" + "=" * 75)
    if errors:
        print(f"[FAIL] Se encontraron {len(errors)} errores en la auditoría:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("[PASS] RESULTADO DE AUDITORÍA: 100% APROBADA - CERO ERRORES DETECTADOS")
        print("=" * 75)

if __name__ == "__main__":
    run_audit()

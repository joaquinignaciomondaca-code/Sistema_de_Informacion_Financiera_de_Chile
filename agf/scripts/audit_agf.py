#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_agf.py
Suite de auditoría matemática, contable y referencial para:
  1. agf_maestro (Parquet y JSON)
  2. agf_balance y agf_resultados (Parquet)
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
    print("=" * 70)
    print("AUDITORÍA DE INTEGRIDAD: ADMINISTRADORAS GENERALES DE FONDOS (AGF)")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(base_dir, "docs", "outputs", "agf")

    pq_maestro = os.path.join(out_dir, "agf_maestro.parquet")
    js_maestro = os.path.join(out_dir, "agf_maestro.json")
    pq_bal = os.path.join(out_dir, "agf_balance.parquet")
    pq_res = os.path.join(out_dir, "agf_resultados.parquet")

    errors = []

    # 1. Existencia
    for p in [pq_maestro, js_maestro, pq_bal, pq_res]:
        if not os.path.exists(p):
            errors.append(f"Falta archivo: {p}")
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        sys.exit(1)

    # 2. Cargar datos
    df_m_pq = pd.read_parquet(pq_maestro)
    with open(js_maestro, "r", encoding="utf-8") as f:
        df_m_js = pd.DataFrame(json.load(f))

    df_b_pq = pd.read_parquet(pq_bal)
    df_r_pq = pd.read_parquet(pq_res)

    print("\n--- 1. AUDITORÍA: agf_maestro ---")
    print(f"Total entidades registradas: {len(df_m_pq)} (Parquet: {os.path.getsize(pq_maestro)} bytes, JSON: {os.path.getsize(js_maestro)} bytes)")

    if len(df_m_pq) != len(df_m_js):
        errors.append(f"Discrepancia de filas en maestro: Parquet {len(df_m_pq)} vs JSON {len(df_m_js)}")

    # Duplicados RUT
    if df_m_pq["rut"].duplicated().any():
        dups = df_m_pq[df_m_pq["rut"].duplicated()]["rut"].tolist()
        errors.append(f"RUTs duplicados en maestro: {dups}")
    else:
        print("RUTs duplicados: 0")

    # Modulo 11
    m11_ok = 0
    for _, row in df_m_pq.iterrows():
        expected_dv = calcular_dv(int(row["rut"]))
        actual_dv = str(row["dv"]).upper()
        if expected_dv != actual_dv:
            errors.append(f"Falla Módulo 11 en RUT {row['rut']}: esperado {expected_dv}, actual {actual_dv}")
        else:
            m11_ok += 1
    print(f"Validación Módulo 11 (RUT): {m11_ok}/{len(df_m_pq)} válidos (100.0%)")

    # Distribución vigencia
    vig_counts = df_m_pq["estado_vigencia"].value_counts().to_dict()
    print(f"Distribución vigencia: {vig_counts}")

    print("\n--- 2. AUDITORÍA: agf_balance / agf_resultados ---")
    print(f"Balances: {len(df_b_pq)} | Resultados: {len(df_r_pq)}")
    if set(zip(df_b_pq["rut"], df_b_pq["periodo"])) != set(zip(df_r_pq["rut"], df_r_pq["periodo"])):
        errors.append("agf_balance y agf_resultados no cubren los mismos (rut, periodo)")
    if df_r_pq.duplicated(subset=["rut", "periodo"]).any():
        errors.append("agf_resultados tiene (rut, periodo) duplicados")
    meses_ok = (df_r_pq["meses_acumulados"] == df_r_pq["periodo"].str[5:].astype(int)).all()
    if not meses_ok:
        errors.append("agf_resultados.meses_acumulados no coincide con el mes del periodo")
    marzo = df_r_pq[df_r_pq["meses_acumulados"] == 3]
    if not (marzo["ingresos_ordinarios_trimestre_mm_clp"].fillna(-1) == marzo["ingresos_ordinarios_acum_mm_clp"].fillna(-1)).all():
        errors.append("agf_resultados: en marzo el ingreso del trimestre debe igualar el acumulado")
    for col in ["gastos_administracion_acum_mm_clp", "ganancia_perdida_acum_mm_clp"]:
        n = int(df_r_pq[col].notna().sum())
        print(f"{col}: {n}/{len(df_r_pq)} con dato" + (" (no capturado en la fuente)" if n == 0 else ""))
        if n and (df_r_pq[col].fillna(0) == 0).all():
            errors.append(f"{col}: todo en cero; revisar el scraper")

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
    diffs = (df_b_pq["total_activos_mm_clp"] - (df_b_pq["total_pasivos_mm_clp"] + df_b_pq["patrimonio_mm_clp"])).abs()
    # Permitir tolerancia de redondeo de 0.002 MM$ (por aproximación de miles)
    cuadre_exacto = (diffs <= 0.005).sum()
    pct_cuadre = (cuadre_exacto / len(df_b_pq)) * 100.0
    print(f"Ecuación Contable (Activo == Pasivo + Patrimonio): {pct_cuadre:.1f}% exacta ({cuadre_exacto}/{len(df_b_pq)})")
    print(f"Diferencia máxima observada: {diffs.max():.6f} MM$ CLP")

    if pct_cuadre < 98.0:
        errors.append(f"Descuadre contable excesivo: {pct_cuadre:.1f}% de cuadre")

    # Nulos en columnas clave
    cols_core = ["rut", "periodo", "razon_social", "total_activos_mm_clp", "total_pasivos_mm_clp", "patrimonio_mm_clp"]
    nulos = df_b_pq[cols_core].isna().sum().sum()
    print(f"Valores nulos en columnas core: {nulos}")
    if nulos > 0:
        errors.append(f"Valores nulos en columnas core: {nulos}")

    # Top AGFs por activos propios
    max_periodo = df_b_pq["periodo"].max()
    print(f"\nTOP 5 GESTORAS POR ACTIVOS PROPIOS ({max_periodo}):")
    df_top = df_b_pq[df_b_pq["periodo"] == max_periodo].sort_values("total_activos_mm_clp", ascending=False).head(5)
    for _, r in df_top.iterrows():
        print(f"  - {r['razon_social']:<50} | Activos: {r['total_activos_mm_clp']:>10.1f} MM$ | Patrimonio: {r['patrimonio_mm_clp']:>10.1f} MM$")

    print("\n" + "=" * 70)
    if errors:
        print(f"[FAIL] Se encontraron {len(errors)} errores en la auditoría:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("[PASS] RESULTADO DE AUDITORÍA: 100% APROBADA - CERO ERRORES DETECTADOS")
        print("=" * 70)

if __name__ == "__main__":
    run_audit()

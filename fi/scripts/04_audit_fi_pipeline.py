# -*- coding: utf-8 -*-
"""
04_audit_fi_pipeline.py — Auditoría Contable y de Operaciones REPO para Fondos de Inversión (FI).
==============================================================================================
"""

import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FI_OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "fi")

EEFF_PARQUET = os.path.join(FI_OUTPUT_DIR, "fi_caratula_eeff_historico.parquet")
REPOS_PARQUET = os.path.join(FI_OUTPUT_DIR, "fi_repos_detalle_historico.parquet")
UNIVERSE_PARQUET = os.path.join(FI_OUTPUT_DIR, "fi_registro_fondos_universo.parquet")

def main():
    print("=" * 80)
    print("AUDITORÍA INTEGRAL DE FONDOS DE INVERSIÓN (FI)")
    print("=" * 80)

    # 1. Universo
    if os.path.exists(UNIVERSE_PARQUET):
        df_u = pd.read_parquet(UNIVERSE_PARQUET)
        print(f"\n1. UNIVERSO DE FONDOS DE INVERSIÓN: {len(df_u)} fondos registrados")
        print(f"   - Por Tipo: {df_u['tipo_entidad_desc'].value_counts().to_dict()}")
        print(f"   - Por Vigencia: {df_u['estado_vigencia'].value_counts().to_dict()}")

    # 2. Caratula EEFF
    if os.path.exists(EEFF_PARQUET):
        df_e = pd.read_parquet(EEFF_PARQUET)
        print(f"\n2. AUDITORÍA CONTABLE EEFF: {len(df_e)} registros contables")
        if not df_e.empty:
            print(f"   - Fondos únicos con EEFF: {df_e['run_fondo'].nunique()}")
            if 'efectivo_y_equivalentes_m_clp' in df_e.columns:
                print(f"   - Efectivo y Equivalentes total: {df_e['efectivo_y_equivalentes_m_clp'].sum()/1e6:,.2f} Billones CLP")
            if 'activos_financieros_vr_m_clp' in df_e.columns:
                print(f"   - Activos Financieros a Valor Razonable: {df_e['activos_financieros_vr_m_clp'].sum()/1e6:,.2f} Billones CLP")
            if 'activos_financieros_amortizado_m_clp' in df_e.columns:
                print(f"   - Activos Financieros Costo Amortizado: {df_e['activos_financieros_amortizado_m_clp'].sum()/1e6:,.2f} Billones CLP")
            if 'anio' in df_e.columns:
                print("   - Evolución anual EEFF:")
                g = df_e.groupby('anio').agg(
                    fondos=('run_fondo', 'nunique'),
                    patrimonio_billones=('patrimonio_total_m_clp', lambda x: x.sum() / 1e6),
                    activos_billones=('activo_total_m_clp', lambda x: x.sum() / 1e6),
                    utilidad_billones=('utilidad_ejercicio_m_clp', lambda x: x.sum() / 1e6)
                ).reset_index()
                print(g.to_string(index=False))
    else:
        print(f"\n2. AUDITORÍA CONTABLE EEFF: No existe archivo {EEFF_PARQUET} aún.")

    # 3. Operaciones REPO
    if os.path.exists(REPOS_PARQUET):
        df_r = pd.read_parquet(REPOS_PARQUET)
        print(f"\n3. AUDITORÍA DE OPERACIONES REPO (VRC / CRV): {len(df_r)} contratos")
        if not df_r.empty:
            print(f"   - Fondos operando REPO: {df_r['run_fondo'].nunique()}")
            if 'codigo_operacion' in df_r.columns:
                print(f"   - Desglose Tipo Operación:\n{df_r['codigo_operacion'].value_counts().to_string()}")
            if 'nombre_contraparte' in df_r.columns:
                print("\n   - Top 5 Contrapartes:")
                print(df_r['nombre_contraparte'].value_counts().head(5).to_string())
            if 'anio' in df_r.columns:
                print("\n   - Evolución Anual Contratos REPO:")
                g_r = df_r.groupby('anio').agg(
                    contratos=('id', 'count'),
                    fondos=('run_fondo', 'nunique'),
                    saldo_cierre_m=('valorizacion_cierre_m_moneda', 'sum')
                ).reset_index()
                print(g_r.to_string(index=False))
    else:
        print(f"\n3. AUDITORÍA DE OPERACIONES REPO: No existe archivo {REPOS_PARQUET} aún.")

if __name__ == '__main__':
    main()

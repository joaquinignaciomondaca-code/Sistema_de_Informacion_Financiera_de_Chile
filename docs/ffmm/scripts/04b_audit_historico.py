"""
Pipeline Step 4B: Auditoria Contable y Validacion Cruzada Historica de EEFF y REPOs FFMM (2015-2025)
====================================================================================================
1. Verifica la ecuacion fundamental: Activo = Pasivo + Patrimonio para cada fondo y año.
2. Compara los contratos REPO contra el benchmark historico del Banco Central (repo_transacciones.csv).
3. Genera metricas macrofinancieras anuales (AUM total, Activos totales, REPO total M CLP, fondos activos).
"""

import os
import sys
import json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "ffmm")
EEFF_PARQUET = os.path.join(OUTPUT_DIR, "ffmm_caratula_eeff_historico.parquet")
REPOS_PARQUET = os.path.join(OUTPUT_DIR, "ffmm_repos_detalle_historico.parquet")
BENCHMARK_CSV = r"C:\Users\joaqu\Desktop\Respaldo_BCCH\Fondos_Mutuos\05_REPO\outputs\repo_transacciones.csv"

def audit_eeff():
    print("=" * 80)
    print("1. AUDITORIA CONTABLE DE ESTADOS FINANCIEROS (CARATULA)")
    print("=" * 80)
    if not os.path.exists(EEFF_PARQUET):
        print(f"Aviso: Aun no se genera {EEFF_PARQUET}. Esperando finalizacion del extractor.")
        return False

    df = pd.read_parquet(EEFF_PARQUET)
    total_records = len(df)
    print(f"Total registros EEFF historicos: {total_records}")
    print(f"Rango de años: {df['anio'].min()} a {df['anio'].max()}")
    print(f"Fondos unicos con EEFF: {df['run_fondo'].nunique()}")

    # Validacion ecuacion contable
    df['diff_contable'] = np.abs(df['total_activos_m_clp'] - (df['total_pasivos_m_clp'] + df['patrimonio_activo_neto_m_clp']))
    df['cuadre_ok'] = df['diff_contable'] < 1.0

    cuadres_validos = df['cuadre_ok'].sum()
    pct_cuadre = (cuadres_validos / total_records) * 100
    print(f"\nVerificacion de Identidad Contable (Activo = Pasivo + Patrimonio):")
    print(f"  Cumplimiento exacto: {cuadres_validos}/{total_records} ({pct_cuadre:.2f}%)")

    # Resumen anual macro
    print("\nEvolucion Anual del Mercado de Fondos Mutuos Chilenos:")
    summary = df.groupby('anio').agg(
        fondos_con_eeff=('run_fondo', 'count'),
        aum_total_billones_clp=('patrimonio_activo_neto_m_clp', lambda x: round(x.sum() / 1e6, 2)),
        activos_totales_billones_clp=('total_activos_m_clp', lambda x: round(x.sum() / 1e6, 2)),
        pct_cuadre_ok=('cuadre_ok', lambda x: round((x.sum() / len(x)) * 100, 1))
    ).reset_index()
    print(summary.to_string(index=False))

    return True

def audit_repos():
    print("\n" + "=" * 80)
    print("2. AUDITORIA DE CONTRATOS REPO (RETROVENTAS LITERAL 11 COLUMNAS)")
    print("=" * 80)
    if not os.path.exists(REPOS_PARQUET):
        print(f"Aviso: Aun no se genera {REPOS_PARQUET}.")
        return False

    df_repos = pd.read_parquet(REPOS_PARQUET)
    print(f"Total contratos REPO extraidos: {len(df_repos)}")
    print(f"Fondos con contratos REPO: {df_repos['run_fondo'].nunique()}")
    print(f"Saldo total REPO en cartera: ${df_repos['saldo_al_cierre_m_clp'].sum():,.0f} M CLP")

    # Resumen anual repos
    repo_summary = df_repos.groupby('anio').agg(
        contratos=('run_fondo', 'count'),
        fondos_operando=('run_fondo', 'nunique'),
        saldo_cierre_m_clp=('saldo_al_cierre_m_clp', 'sum'),
        total_transado_m_clp=('total_transado_m_clp', 'sum')
    ).reset_index()
    print("\nEvolucion Anual de Contratos REPO:")
    print(repo_summary.to_string(index=False))

    # Comparacion con Benchmark historico
    if os.path.exists(BENCHMARK_CSV):
        print(f"\nComparacion con Benchmark Historico ({BENCHMARK_CSV}):")
        try:
            df_bench = pd.read_csv(BENCHMARK_CSV, sep=';', encoding='utf-8-sig')
            print(f"  Contratos en benchmark: {len(df_bench)}")
            bench_by_year = df_bench['Año'].value_counts().sort_index().to_dict()
            our_by_year = df_repos['anio'].value_counts().sort_index().to_dict()
            comp_rows = []
            all_years = sorted(set(list(bench_by_year.keys()) + list(our_by_year.keys())))
            for y in all_years:
                b_cnt = bench_by_year.get(y, 0)
                o_cnt = our_by_year.get(int(y) if str(y).isdigit() else y, 0)
                comp_rows.append({'Año': y, 'Benchmark_BCCH': b_cnt, 'Extraccion_CMF': o_cnt, 'Diferencia': o_cnt - b_cnt})
            print(pd.DataFrame(comp_rows).to_string(index=False))
        except Exception as e:
            print(f"  No se pudo leer benchmark: {e}")

    return True

def main():
    audit_eeff()
    audit_repos()

if __name__ == '__main__':
    main()

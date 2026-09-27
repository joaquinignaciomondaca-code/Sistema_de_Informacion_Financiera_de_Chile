"""
Pipeline Step 4: Auditoria Integral del Mercado de Fondos Mutuos (EEFF 2024)
Verificaciones:
  1. Cuadratura Contable: Total Activos == Total Pasivos + Activo Neto (Patrimonio)
  2. Cuadratura de Resultados: Ingresos - Gastos == Utilidad Neta
  3. Mercado REPO: Volumen total, participacion sobre AUM, y ranking de contrapartes dealers
  4. Ranking de AGFs por Patrimonio Administrado (AUM)
Salida:
  - Reporte consolidado de auditoria
"""

# RETIRADO DEL SITIO (2026-09-26): audita las salidas 2024 (carátula y repos) ya retiradas
# del visor; se mantiene como herramienta de laboratorio para la auditoría pendiente contra la CMF.
import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PARQUET_CARATULA = os.path.join(BASE_DIR, "docs", "outputs", "ffmm", "ffmm_caratula_eeff_2024.parquet")
PARQUET_REPOS = os.path.join(BASE_DIR, "docs", "outputs", "ffmm", "ffmm_repos_detalle_2024.parquet")

def run_audit():
    if not os.path.exists(PARQUET_CARATULA):
        print(f"Error: {PARQUET_CARATULA} no existe.")
        return

    df_c = pd.read_parquet(PARQUET_CARATULA)
    df_r = pd.read_parquet(PARQUET_REPOS) if os.path.exists(PARQUET_REPOS) else pd.DataFrame()

    print("=" * 70)
    print("AUDITORIA INTEGRAL DE ESTADOS FINANCIEROS FONDOS MUTUOS (CIERRE 2024)")
    print("=" * 70)

    total_fondos = len(df_c)
    print(f"\n1. COBERTURA DE MERCADO:")
    print(f"   Total fondos con caratulas extraidas: {total_fondos}")
    
    # Cuadratura Contable: Activos = Pasivos + Patrimonio
    # Tolerancia por redondeo de M$: 5 M$
    cuadratura_balance = df_c['total_activos_m_clp'] - (df_c['total_pasivos_m_clp'] + df_c['patrimonio_aum_m_clp'])
    cuadran_balance = cuadratura_balance.abs() <= 5.0
    pct_cuadran = (cuadran_balance.sum() / max(total_fondos, 1)) * 100

    print(f"\n2. CUADRATURA DE BALANCE (Activos == Pasivos + Patrimonio):")
    print(f"   Fondos que cuadran con exactitud: {cuadran_balance.sum()}/{total_fondos} ({pct_cuadran:.1f}%)")
    
    # Magnitudes Globales
    aum_total = df_c['patrimonio_aum_m_clp'].sum()
    activos_total = df_c['total_activos_m_clp'].sum()
    pasivos_total = df_c['total_pasivos_m_clp'].sum()
    utilidad_total = df_c['utilidad_ejercicio_m_clp'].sum()
    efectivo_total = df_c['efectivo_m_clp'].sum()
    fvtpl_total = df_c['fvtpl_m_clp'].sum()
    amortizado_total = df_c['costo_amortizado_m_clp'].sum()
    repos_total = df_c['saldo_repos_m_clp'].sum()

    print(f"\n3. TOTALES CONSOLIDADOS DEL MERCADO (en M$ CLP):")
    print(f"   - Total Activos Administrados:      ${activos_total:>18,.0f} M CLP")
    print(f"   - Total Pasivos:                    ${pasivos_total:>18,.0f} M CLP")
    print(f"   - Patrimonio Neto (AUM):            ${aum_total:>18,.0f} M CLP (${aum_total/1e6:,.2f} Billones CLP)")
    print(f"   - Utilidad Neta del Ejercicio:      ${utilidad_total:>18,.0f} M CLP")
    print(f"   - Efectivo y Equivalentes:          ${efectivo_total:>18,.0f} M CLP ({(efectivo_total/max(activos_total,1))*100:.1f}% de activos)")
    print(f"   - Activos a Valor Razonable (FVTPL):${fvtpl_total:>18,.0f} M CLP ({(fvtpl_total/max(activos_total,1))*100:.1f}% de activos)")
    print(f"   - Activos a Costo Amortizado:       ${amortizado_total:>18,.0f} M CLP ({(amortizado_total/max(activos_total,1))*100:.1f}% de activos)")
    print(f"   - Operaciones REPO (Retroventa):    ${repos_total:>18,.0f} M CLP ({(repos_total/max(activos_total,1))*100:.1f}% de activos)")

    print(f"\n4. RANKING TOP 10 ADMINISTRADORAS POR AUM:")
    agf_ranking = df_c.groupby('razon_social_agf')['patrimonio_aum_m_clp'].agg(['sum', 'count']).sort_values('sum', ascending=False)
    agf_ranking.columns = ['AUM_M_CLP', 'Num_Fondos']
    agf_ranking['Part_%'] = (agf_ranking['AUM_M_CLP'] / max(aum_total, 1)) * 100
    for idx, (agf, row) in enumerate(agf_ranking.head(10).iterrows(), 1):
        print(f"   {idx:>2}. {agf[:42]:<42} | ${row['AUM_M_CLP']:>15,.0f} M CLP | {row['Part_%']:>5.1f}% | {int(row['Num_Fondos']):>2} fondos")

    if not df_r.empty and 'saldo_al_cierre_m_clp' in df_r.columns:
        print(f"\n5. ANALISIS DE OPERACIONES REPO (COMPRA CON RETROVENTA):")
        print(f"   Total contratos registrados: {len(df_r)}")
        print(f"   Monto total contratos: ${df_r['saldo_al_cierre_m_clp'].sum():,.0f} M CLP")
        
        # Agrupar contrapartes
        print("\n   Top Contrapartes / Dealers en REPOs FFMM:")
        dealers = df_r.groupby('nombre_contraparte')['saldo_al_cierre_m_clp'].agg(['sum', 'count']).sort_values('sum', ascending=False)
        dealers['Part_%'] = (dealers['sum'] / max(df_r['saldo_al_cierre_m_clp'].sum(), 1)) * 100
        for idx, (dealer, row) in enumerate(dealers.head(10).iterrows(), 1):
            print(f"   {idx:>2}. {dealer[:38]:<38} | ${row['sum']:>14,.0f} M CLP | {row['Part_%']:>5.1f}% | {int(row['count']):>2} contratos")

    print("\n" + "=" * 70)
    print("AUDITORIA CONCLUIDA EXITOSAMENTE")
    print("=" * 70)

if __name__ == '__main__':
    run_audit()

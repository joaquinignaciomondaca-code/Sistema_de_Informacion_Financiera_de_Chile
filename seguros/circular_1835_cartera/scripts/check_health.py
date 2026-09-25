import os
import pandas as pd

for sector in ['vida', 'generales']:
    print('=' * 80)
    print(f'AUDITORIA DE INTEGRIDAD: SECTOR {sector.upper()}')
    print('=' * 80)
    base = os.path.join(r'seguros/circular_1835_cartera/outputs', sector)
    
    # 1. Acciones
    df_acc = pd.read_parquet(os.path.join(base, 'cartera_acciones.parquet'))
    p_min, p_max = df_acc['periodo'].min(), df_acc['periodo'].max()
    print(f'Acciones: {len(df_acc):,} filas | Periodos: {p_min} a {p_max}')
    sample = df_acc[df_acc['nemotecnico'].isin(['CHILE', 'BCI', 'BSANTANDER', 'SQM-B', 'CMPC'])].groupby('nemotecnico')['precio_cierre_clp'].median().round(2)
    print('  Precios representativos:', sample.to_dict())
    
    # 2. Bonos
    df_bon = pd.read_parquet(os.path.join(base, 'cartera_bonos.parquet'))
    p_min, p_max = df_bon['periodo'].min(), df_bon['periodo'].max()
    print(f'Bonos: {len(df_bon):,} filas | Periodos: {p_min} a {p_max}')
    print(f'  TIR Compra Media: {df_bon["tir_compra_pct"].mean():.2f}% | Mediana: {df_bon["tir_compra_pct"].median():.2f}%')
    print(f'  TIR Mercado Media: {df_bon["tir_mercado_pct"].mean():.2f}% | Mediana: {df_bon["tir_mercado_pct"].median():.2f}%')
    print(f'  Tasa Emision Media: {df_bon["tasa_emision_pct"].mean():.2f}% | Mediana: {df_bon["tasa_emision_pct"].median():.2f}%')
    
    # 3. Fondos
    df_fnd = pd.read_parquet(os.path.join(base, 'cartera_fondos.parquet'))
    print(f'Fondos: {len(df_fnd):,} filas | Cuotas median: {df_fnd["cuotas_cartera"].median():,.1f} | VCuota median: {df_fnd["valor_cuota"].median():,.2f}')
    
    # 4. Bienes Raices
    df_br = pd.read_parquet(os.path.join(base, 'cartera_bienes_raices.parquet'))
    print(f'Bienes Raices: {len(df_br):,} filas | Avaluo SII median: {df_br["avaluo_fiscal_m_clp"].median():,.1f} M$ | Tasacion median: {df_br["tasacion_comercial_m_clp"].median():,.1f} M$')
    print('  Top 3 comunas:', df_br['comuna'].value_counts().head(3).to_dict())
    print()

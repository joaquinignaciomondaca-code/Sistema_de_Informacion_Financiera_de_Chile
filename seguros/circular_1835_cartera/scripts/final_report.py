from pathlib import Path
import os
import shutil
import pandas as pd

ctrl = pd.read_csv(r'seguros/circular_1835_cartera/control_descargas_activos.csv')
total, used, free = shutil.disk_usage(Path(__file__).resolve().anchor)

print('=' * 85)
print('BALANCE FINAL: HISTORIA COMPLETA CIRCULAR 1835 CMF (2007 - PRESENTE)')
print('=' * 85)
print(f'Total periodos evaluados: {len(ctrl):,}')
print(ctrl['estado'].value_counts())
print(f'\nEspacio libre en Disco C: {free / (1024**3):.2f} GB')

print('\n' + '-' * 85)
print('CARTERAS SEGREGADAS: SEGUROS DE VIDA (outputs/vida/)')
print('-' * 85)
v_path = r'seguros/circular_1835_cartera/outputs/vida'
total_rows_vida = 0
for f in sorted(os.listdir(v_path)):
    if f.endswith('.parquet'):
        p = os.path.join(v_path, f)
        df = pd.read_parquet(p)
        sz = os.path.getsize(p) / (1024*1024)
        p_min = df['periodo'].min() if 'periodo' in df.columns else '-'
        p_max = df['periodo'].max() if 'periodo' in df.columns else '-'
        total_rows_vida += len(df)
        print(f'  - {f:30}: {len(df):>11,} filas | {sz:>6.2f} MB | {p_min} a {p_max}')
print(f'TOTAL REGISTROS VIDA: {total_rows_vida:,}')

print('\n' + '-' * 85)
print('CARTERAS SEGREGADAS: SEGUROS GENERALES (outputs/generales/)')
print('-' * 85)
g_path = r'seguros/circular_1835_cartera/outputs/generales'
total_rows_gen = 0
for f in sorted(os.listdir(g_path)):
    if f.endswith('.parquet'):
        p = os.path.join(g_path, f)
        df = pd.read_parquet(p)
        sz = os.path.getsize(p) / (1024*1024)
        p_min = df['periodo'].min() if 'periodo' in df.columns else '-'
        p_max = df['periodo'].max() if 'periodo' in df.columns else '-'
        total_rows_gen += len(df)
        print(f'  - {f:30}: {len(df):>11,} filas | {sz:>6.2f} MB | {p_min} a {p_max}')
print(f'TOTAL REGISTROS GENERALES: {total_rows_gen:,}')

print('\n' + '=' * 85)
print(f'TOTAL GENERAL DE REGISTROS DE INVERSION CONSOLIDADOS: {total_rows_vida + total_rows_gen:,}')
print('=' * 85)

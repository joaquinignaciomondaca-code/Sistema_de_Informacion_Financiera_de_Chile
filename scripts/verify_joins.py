import pandas as pd

print("--- Test 1: fi.lista_entidades schema ---")
df_m = pd.read_parquet('fi/cartera_inversiones/outputs/maestro_fondos_inversion.parquet')
print(df_m[['id', 'run_fondo', 'nombre_fondo', 'categoria_fondo']].head(3))

print("\n--- Test 2: fi.cartera_nacional schema ---")
df_c = pd.read_parquet('fi/cartera_inversiones/outputs/fi_cartera_nacional.parquet', columns=['id', 'periodo', 'run_fondo', 'nemotecnico', 'rut_emisor'])
print(df_c.head(3))

print("\n--- Test 3: Join fi.cartera_nacional with fi.lista_entidades on run_fondo ---")
merged = df_c.merge(df_m, on='run_fondo', how='inner')
top_fondos = merged.groupby(['nombre_fondo', 'categoria_fondo']).size().reset_index(name='total_activos').sort_values(by='total_activos', ascending=False).head(5)
print(top_fondos)

print("\n--- Test 4: Check Foreign Key Coverage ---")
fondos_en_cartera = df_c['run_fondo'].nunique()
fondos_en_maestro = df_m['run_fondo'].nunique()
fondos_con_match = df_c['run_fondo'].isin(df_m['run_fondo']).sum()
pct_match = (fondos_con_match / len(df_c)) * 100
print(f"Fondos únicos en cartera: {fondos_en_cartera}")
print(f"Fondos únicos en maestro: {fondos_en_maestro}")
print(f"Filas con match FK en maestro: {fondos_con_match:,} / {len(df_c):,} ({pct_match:.2f}%)")


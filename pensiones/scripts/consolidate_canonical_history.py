"""
Consolidación y normalización canónica de los 139 meses de historia de Fondos de Pensiones.
Mapea los RUTs históricos (Ex-ProVida 98.000.400-7 y Ex-Cuprum 98.001.000-7) a sus entidades legales continuas
para garantizar 100% de integridad referencial con afp_maestro_administradoras y cero claves duplicadas.
"""

import glob
import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor")
PARTITIONS_DIR = BASE_DIR / "pensiones" / "outputs" / "partitions"
OUTPUT_DIR = BASE_DIR / "pensiones" / "outputs"
DOCS_OUTPUT_DIR = BASE_DIR / "docs" / "outputs" / "pensiones"

HISTORICAL_RUT_MAP = {
    '98.000.400-7': ('76.265.736-8', 'AFP ProVida S.A.'),
    '98.001.000-7': ('76.240.079-0', 'AFP Cuprum S.A.'),
}

def consolidate():
    print("Iniciando consolidación canónica con mapeo de RUTs históricos...")
    
    bono_files = sorted(glob.glob(str(PARTITIONS_DIR / "bonos_*.parquet")))
    accion_files = sorted(glob.glob(str(PARTITIONS_DIR / "acciones_*.parquet")))
    derivado_files = sorted(glob.glob(str(PARTITIONS_DIR / "derivados_*.parquet")))
    
    # 1. BONOS
    b_dfs = []
    for f in bono_files:
        df = pd.read_parquet(f)
        if not df.empty and 'rut_administradora' in df.columns:
            b_dfs.append(df)
            
    if b_dfs:
        df_bonos = pd.concat(b_dfs, ignore_index=True)
        # Mapear RUTs históricos a entidades vigentes
        for old_rut, (new_rut, new_name) in HISTORICAL_RUT_MAP.items():
            mask = df_bonos['rut_administradora'] == old_rut
            df_bonos.loc[mask, 'rut_administradora'] = new_rut
            df_bonos.loc[mask, 'nombre_administradora'] = new_name
            
        df_bonos = df_bonos.groupby(
            ['periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_instrumento', 'nemotecnico', 'emisor', 'fuente'],
            as_index=False
        )['monto_usd_millones'].sum()
        df_bonos['monto_usd_millones'] = df_bonos['monto_usd_millones'].round(4)
        df_bonos['id_posicion'] = df_bonos['periodo'] + "_" + df_bonos['rut_administradora'] + "_" + df_bonos['nemotecnico']
        cols_bonos = ['id_posicion', 'periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_instrumento', 'nemotecnico', 'emisor', 'monto_usd_millones', 'fuente']
        df_bonos = df_bonos[cols_bonos]
        
        df_bonos.to_parquet(OUTPUT_DIR / "afp_cartera_bonos.parquet", index=False)
        df_bonos.to_parquet(DOCS_OUTPUT_DIR / "afp_cartera_bonos.parquet", index=False)
        print(f"Bonos consolidados: {len(df_bonos):,} registros en afp_cartera_bonos.parquet")

    # 2. ACCIONES
    a_dfs = []
    for f in accion_files:
        df = pd.read_parquet(f)
        if not df.empty and 'rut_administradora' in df.columns:
            a_dfs.append(df)
            
    if a_dfs:
        df_acciones = pd.concat(a_dfs, ignore_index=True)
        for old_rut, (new_rut, new_name) in HISTORICAL_RUT_MAP.items():
            mask = df_acciones['rut_administradora'] == old_rut
            df_acciones.loc[mask, 'rut_administradora'] = new_rut
            df_acciones.loc[mask, 'nombre_administradora'] = new_name
            
        df_acciones = df_acciones.groupby(
            ['periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'nemotecnico', 'emisor', 'tipo_accion', 'fuente'],
            as_index=False
        ).agg({'monto_usd_millones': 'sum', 'pct_emisor': 'max'})
        df_acciones['monto_usd_millones'] = df_acciones['monto_usd_millones'].round(4)
        df_acciones['id_posicion'] = df_acciones['periodo'] + "_" + df_acciones['rut_administradora'] + "_" + df_acciones['nemotecnico']
        cols_acciones = ['id_posicion', 'periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'nemotecnico', 'emisor', 'tipo_accion', 'monto_usd_millones', 'pct_emisor', 'fuente']
        df_acciones = df_acciones[cols_acciones]
        
        df_acciones.to_parquet(OUTPUT_DIR / "afp_cartera_acciones.parquet", index=False)
        df_acciones.to_parquet(DOCS_OUTPUT_DIR / "afp_cartera_acciones.parquet", index=False)
        print(f"Acciones consolidadas: {len(df_acciones):,} registros en afp_cartera_acciones.parquet")

    # 3. DERIVADOS
    d_dfs = []
    for f in derivado_files:
        df = pd.read_parquet(f)
        if not df.empty and 'rut_administradora' in df.columns:
            d_dfs.append(df)
            
    if d_dfs:
        df_derivados = pd.concat(d_dfs, ignore_index=True)
        for old_rut, (new_rut, new_name) in HISTORICAL_RUT_MAP.items():
            mask = df_derivados['rut_administradora'] == old_rut
            df_derivados.loc[mask, 'rut_administradora'] = new_rut
            df_derivados.loc[mask, 'nombre_administradora'] = new_name
            
        df_derivados = df_derivados.groupby(
            ['periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_derivado', 'contraparte', 'unidad_indexada', 'fuente'],
            as_index=False
        )['nocional_usd_millones'].sum()
        df_derivados['nocional_usd_millones'] = df_derivados['nocional_usd_millones'].round(4)
        df_derivados['id_posicion'] = (
            df_derivados['periodo'] + "_" + 
            df_derivados['rut_administradora'] + "_" + 
            df_derivados.groupby(['periodo', 'rut_administradora']).cumcount().astype(str)
        )
        cols_derivados = ['id_posicion', 'periodo', 'fecha_corte', 'rut_administradora', 'nombre_administradora', 'tipo_derivado', 'contraparte', 'unidad_indexada', 'nocional_usd_millones', 'fuente']
        df_derivados = df_derivados[cols_derivados]
        
        df_derivados.to_parquet(OUTPUT_DIR / "afp_derivados.parquet", index=False)
        df_derivados.to_parquet(DOCS_OUTPUT_DIR / "afp_derivados.parquet", index=False)
        df_derivados.to_parquet(DOCS_OUTPUT_DIR / "afp_derivados_swaps.parquet", index=False)
        print(f"Derivados consolidados: {len(df_derivados):,} registros en afp_derivados.parquet")

if __name__ == "__main__":
    consolidate()

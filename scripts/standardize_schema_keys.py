"""
Estandarizador de Claves Relacionales: Primary Keys (PKs), Foreign Keys (FKs) y Surrogate IDs.
Aplica las mejores practicas de modelado para Data Warehousing analitico en DuckDB:
  1. Clave natural canonica de Fondos: run_fondo (homogeneizando rut_fondo -> run_fondo).
  2. Clave natural canonica de Aseguradoras: rut_aseguradora.
  3. Surrogate Primary Key 'id' deterministica como primera columna en cada tabla.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

def process_file(file_path, id_prefix, entity_col_rename=None, entity_col="run_fondo", period_col="periodo"):
    p = Path(file_path)
    if not p.exists():
        print(f"[-] No existe: {p}")
        return

    print(f"[+] Procesando {p.name} ({p})...")
    df = pd.read_parquet(p)
    initial_len = len(df)

    # 1. Renombrar columna de entidad si corresponde
    if entity_col_rename:
        for old_col, new_col in entity_col_rename.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
                print(f"    Renombrada {old_col} -> {new_col}")

    # 2. Generar Surrogate Key 'id'
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # Para maestros
    if id_prefix in ("VIDA", "GEN", "FFMM", "FI") and not period_col in df.columns:
        df.insert(0, "id", [f"{id_prefix}_{str(val).strip()}" for val in df[entity_col]])
    else:
        # Para tablas transaccionales/cartera
        ent_vals = df[entity_col].astype(str) if entity_col in df.columns else ""
        per_vals = df[period_col].astype(str) if period_col in df.columns else ""
        indices = np.arange(len(df))
        ids = [f"{id_prefix}_{e}_{p}_{i:06d}" for e, p, i in zip(ent_vals, per_vals, indices)]
        df.insert(0, "id", ids)

    # 3. Guardar Parquet
    df.to_parquet(p, index=False)
    print(f"    Completado: {len(df):,} filas guardadas con PK 'id'.")

def main():
    print("=== ESTANDARIZACION DE ESQUEMA RELACIONAL (PKS, FKS, IDS) ===")

    # --- FONDOS DE INVERSION (FFII) ---
    ffii_rename = {"rut_fondo": "run_fondo"}
    process_file("fi/cartera_inversiones/outputs/maestro_fondos_inversion.parquet", "FI", ffii_rename, entity_col="run_fondo")
    process_file("fi/cartera_inversiones/outputs/fi_cartera_nacional.parquet", "FI_NAC", ffii_rename, entity_col="run_fondo")
    process_file("fi/cartera_inversiones/outputs/fi_cartera_extranjera.parquet", "FI_EXT", ffii_rename, entity_col="run_fondo")
    process_file("fi/cartera_inversiones/outputs/fi_futuros_forward.parquet", "FI_FWD", ffii_rename, entity_col="run_fondo")
    process_file("fi/cartera_inversiones/outputs/fi_metodo_participacion.parquet", "FI_PART", ffii_rename, entity_col="run_fondo")
    process_file("fi/cartera_inversiones/outputs/fi_opciones.parquet", "FI_OPC", ffii_rename, entity_col="run_fondo")

    # --- FONDOS MUTUOS (FFMM) ---
    process_file("ffmm/circular_1333_cartera/outputs/maestro_fondos_mutuos.parquet", "FFMM", entity_col="run_fondo")
    process_file("ffmm/circular_1333_cartera/outputs/ffmm_futu_normalizado.parquet", "FFMM_FUTU", entity_col="run_fondo")
    process_file("ffmm/circular_1333_cartera/outputs/ffmm_opci_normalizado.parquet", "FFMM_OPCI", entity_col="run_fondo")

    # --- SEGUROS (VIDA Y GENERALES) MAESTROS ---
    process_file("docs/outputs/vida/maestro_aseguradoras_vida.parquet", "VIDA", entity_col="rut_aseguradora")
    process_file("docs/outputs/generales/maestro_aseguradoras_generales.parquet", "GEN", entity_col="rut_aseguradora")
    
    # También en carpeta origen seguros
    process_file("seguros/circular_1835_cartera/outputs/vida/maestro_aseguradoras_vida.parquet", "VIDA", entity_col="rut_aseguradora")
    process_file("seguros/circular_1835_cartera/outputs/generales/maestro_aseguradoras_generales.parquet", "GEN", entity_col="rut_aseguradora")

    print("\n=== TODAS LAS TABLAS HAN SIDO ESTANDARIZADAS CON EXITO ===")

if __name__ == "__main__":
    main()

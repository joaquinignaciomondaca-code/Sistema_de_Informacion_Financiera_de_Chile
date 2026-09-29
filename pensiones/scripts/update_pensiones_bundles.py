import json
import re
from pathlib import Path
import pandas as pd

def update_bundles():
    print("Exportando JSONs y actualizando data_bundles.js...")
    
    docs_out = Path("docs/outputs/pensiones")
    docs_out.mkdir(parents=True, exist_ok=True)
    
    # 1. Leer parquets
    df_bonos = pd.read_parquet(docs_out / "afp_cartera_bonos.parquet")
    df_acciones = pd.read_parquet(docs_out / "afp_cartera_acciones.parquet")
    df_derivados = pd.read_parquet(docs_out / "afp_derivados.parquet")
    
    # También guardar copia como afp_derivados_swaps.parquet para compatibilidad DuckDB
    df_derivados.to_parquet(docs_out / "afp_derivados_swaps.parquet", index=False)
    
    # 2. Exportar JSONs completos para descarga o fallback
    bonos_records = df_bonos.to_dict(orient="records")
    acciones_records = df_acciones.to_dict(orient="records")
    derivados_records = df_derivados.to_dict(orient="records")
    
    with open(docs_out / "afp_cartera_bonos.json", "w", encoding="utf-8") as f:
        json.dump(bonos_records, f, ensure_ascii=False)
    with open(docs_out / "afp_cartera_acciones.json", "w", encoding="utf-8") as f:
        json.dump(acciones_records, f, ensure_ascii=False)
    with open(docs_out / "afp_derivados_swaps.json", "w", encoding="utf-8") as f:
        json.dump(derivados_records, f, ensure_ascii=False)
        
    print(f"JSONs exportados: {len(bonos_records):,} bonos, {len(acciones_records):,} acciones, {len(derivados_records):,} swaps")
    
    # Sin precarga en data_bundles.js: la web ya no expone estas tablas (ver pensiones/README.md)
    # y scripts/audit_navigation.py exige que el bundle solo tenga afp_lista_entidades y bancos_*.

if __name__ == "__main__":
    update_bundles()

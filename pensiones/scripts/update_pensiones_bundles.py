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
    
    # 3. Muestra para precarga en data_bundles.js (primeros 250 registros de los datos reales para no saturar memoria)
    sample_bonos = bonos_records[:250]
    sample_acciones = acciones_records[:250]
    sample_swaps = derivados_records[:250]
    
    bundle_file = Path("docs/js/data_bundles.js")
    if bundle_file.exists():
        js_text = bundle_file.read_text(encoding="utf-8")
        
        # Reemplazar o insertar afp_cartera_bonos
        if "window.DATA_BUNDLES.afp_cartera_bonos" in js_text:
            js_text = re.sub(r'window\.DATA_BUNDLES\.afp_cartera_bonos\s*=\s*\[[\s\S]*?\];', f"window.DATA_BUNDLES.afp_cartera_bonos = {json.dumps(sample_bonos, ensure_ascii=False)};", js_text)
        else:
            js_text += f"\nwindow.DATA_BUNDLES.afp_cartera_bonos = {json.dumps(sample_bonos, ensure_ascii=False)};\n"

        # Reemplazar o insertar afp_cartera_acciones
        if "window.DATA_BUNDLES.afp_cartera_acciones" in js_text:
            js_text = re.sub(r'window\.DATA_BUNDLES\.afp_cartera_acciones\s*=\s*\[[\s\S]*?\];', f"window.DATA_BUNDLES.afp_cartera_acciones = {json.dumps(sample_acciones, ensure_ascii=False)};", js_text)
        else:
            js_text += f"\nwindow.DATA_BUNDLES.afp_cartera_acciones = {json.dumps(sample_acciones, ensure_ascii=False)};\n"

        # Reemplazar o insertar afp_derivados_swaps
        if "window.DATA_BUNDLES.afp_derivados_swaps" in js_text:
            js_text = re.sub(r'window\.DATA_BUNDLES\.afp_derivados_swaps\s*=\s*\[[\s\S]*?\];', f"window.DATA_BUNDLES.afp_derivados_swaps = {json.dumps(sample_swaps, ensure_ascii=False)};", js_text)
        else:
            js_text += f"\nwindow.DATA_BUNDLES.afp_derivados_swaps = {json.dumps(sample_swaps, ensure_ascii=False)};\n"

        bundle_file.write_text(js_text, encoding="utf-8")
        print("data_bundles.js actualizado exitosamente con datos históricos reales.")

if __name__ == "__main__":
    update_bundles()

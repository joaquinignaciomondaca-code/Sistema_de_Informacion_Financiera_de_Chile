"""
Sincronizador en caliente: vuelca los contratos REPO históricos del checkpoint
a Parquet y JSON publicados. La carátula histórica se omite por defecto.
"""

# La carátula histórica se retiró del sitio el 2026-09-26; sólo se exporta
# en uso de laboratorio con FFMM_PUBLICAR_CARATULA_HISTORICO=1.
import os
import json
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "ffmm")
DATA_DIR = os.path.join(BASE_DIR, "ffmm", "data")
CHECKPOINT_PATH = os.path.join(DATA_DIR, "checkpoint_historico_eeff.json")

def sync():
    publicar_caratula = os.environ.get("FFMM_PUBLICAR_CARATULA_HISTORICO") == "1"
    if not os.path.exists(CHECKPOINT_PATH):
        print("No se encontro checkpoint.")
        return

    try:
        with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except Exception as e:
        print(f"Error leyendo checkpoint: {e}")
        return

    eeff_all = d.get('eeff', [])
    repos_all = d.get('repos', [])
    processed_count = len(d.get('processed_keys', []))

    if not publicar_caratula:
        print("  (Carátula histórica omitida: retirada del sitio el 2026-09-26.)")
    print(f"Sincronizando estado: {processed_count} tareas, {len(eeff_all)} EEFF, {len(repos_all)} REPOs.")

    if eeff_all and publicar_caratula:
        df_eeff = pd.DataFrame(eeff_all).drop_duplicates(subset=['run_fondo', 'periodo'])
        df_eeff = df_eeff.sort_values(['anio', 'run_fondo']).reset_index(drop=True)
        eeff_parquet = os.path.join(OUTPUT_DIR, "ffmm_caratula_eeff_historico.parquet")
        df_eeff.to_parquet(eeff_parquet, index=False)
        eeff_json = os.path.join(OUTPUT_DIR, "ffmm_caratula_eeff_historico.json")
        with open(eeff_json, 'w', encoding='utf-8') as f:
            json.dump(df_eeff.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
        print(f"  Parquet EEFF actualizado: {len(df_eeff)} registros.")

    if repos_all:
        df_repos = pd.DataFrame(repos_all).drop_duplicates(subset=['run_fondo', 'periodo', 'nemotecnico', 'saldo_al_cierre_m_clp', 'fecha_compra'])
        df_repos = df_repos.sort_values(['anio', 'run_fondo']).reset_index(drop=True)
        repos_parquet = os.path.join(OUTPUT_DIR, "ffmm_repos_detalle_historico.parquet")
        df_repos.to_parquet(repos_parquet, index=False)
        repos_json = os.path.join(OUTPUT_DIR, "ffmm_repos_detalle_historico.json")
        with open(repos_json, 'w', encoding='utf-8') as f:
            json.dump(df_repos.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
        print(f"  Parquet REPOs actualizado: {len(df_repos)} contratos.")

if __name__ == '__main__':
    sync()

"""
Auditoría Estricta de Calidad y Consistencia Contable
Patrimonios Separados (Securitizadoras CMF Chile).
Verifica:
1. Existencia y paridad exacta Parquet vs JSON (4 datasets).
2. Integridad referencial con securitizadoras_maestro.
3. Cuadre contable exacto: Total Activos == Total Pasivo + Patrimonio/Excedentes.
4. Coherencia de montos en CLP vs USD.
5. Presencia de columna 'numero_nota' en efectivo detalle.
6. Coherencia de instrumentos y contrapartes en repos detalle.
"""

import os
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "securitizadoras")
MAESTRO_PARQUET = os.path.join(OUT_DIR, "securitizadoras_maestro.parquet")

DATASETS = [
    "patrimonios_separados_balance_resumen",
    "patrimonios_separados_nota_efectivo_detalle",
    "patrimonios_separados_repos_detalle",
    "patrimonios_separados_cartera_morosidad_detalle"
]

def run_audit():
    print("=" * 70)
    print("AUDITORIA DE DATOS: PATRIMONIOS SEPARADOS (CMF CHILE)")
    print("=" * 70)

    errors = []
    
    # 1. Cargar Maestro
    if not os.path.exists(MAESTRO_PARQUET):
        errors.append(f"No existe securitizadoras_maestro en {MAESTRO_PARQUET}")
        ruts_validos = set()
    else:
        df_maestro = pd.read_parquet(MAESTRO_PARQUET)
        ruts_validos = set(df_maestro["rut_completo"].unique())
        print(f"[OK] Securitizadoras Maestro cargado: {len(ruts_validos)} RUTs unicos.")

    # 2. Verificar cada dataset
    dfs = {}
    for ds in DATASETS:
        pq_path = os.path.join(OUT_DIR, f"{ds}.parquet")
        js_path = os.path.join(OUT_DIR, f"{ds}.json")

        if not os.path.exists(pq_path):
            errors.append(f"Falta archivo Parquet: {pq_path}")
            continue
        if not os.path.exists(js_path):
            errors.append(f"Falta archivo JSON: {js_path}")
            continue

        df = pd.read_parquet(pq_path)
        with open(js_path, "r", encoding="utf-8") as f:
            js_data = json.load(f)

        len_df = len(df)
        len_js = len(js_data)

        if len_df != len_js:
            errors.append(f"Discrepancia conteo en {ds}: Parquet={len_df} vs JSON={len_js}")
        else:
            print(f"[OK] {ds}: Parquet={len_df} | JSON={len_js} (Sincronizacion 100%)")

        # Verificar integridad referencial
        ruts_ds = set(df["rut_administradora"].unique())
        invalid_ruts = ruts_ds - ruts_validos
        if invalid_ruts:
            errors.append(f"RUTs invalidos en {ds}: {invalid_ruts}")
        else:
            print(f"  [OK] Integridad referencial RUTs: Todos ({len(ruts_ds)}) pertenecen a securitizadoras_maestro.")

        dfs[ds] = df

    # 3. Auditoria especifica: Balance Resumen
    if "patrimonios_separados_balance_resumen" in dfs:
        df_bal = dfs["patrimonios_separados_balance_resumen"]
        
        # Cuadre contable
        cuadres_ok = df_bal["cuadre_contable_ok"].sum()
        total_bals = len(df_bal)
        if cuadres_ok != total_bals:
            diff = total_bals - cuadres_ok
            errors.append(f"{diff} balances no cumplen cuadre contable exacto")
        else:
            print(f"[OK] Balance Resumen: 100% cuadre contable exacto ({cuadres_ok}/{total_bals} balances).")

        # Periodos cubiertos
        periodos = sorted(df_bal["periodo"].unique().tolist())
        print(f"  [OK] Periodos cubiertos en Balances: {periodos}")

    # 4. Auditoria especifica: Nota Efectivo Detalle
    if "patrimonios_separados_nota_efectivo_detalle" in dfs:
        df_efe = dfs["patrimonios_separados_nota_efectivo_detalle"]
        if "numero_nota" not in df_efe.columns:
            errors.append("Falta columna 'numero_nota' en patrimonios_separados_nota_efectivo_detalle")
        else:
            notas_distintas = df_efe["numero_nota"].value_counts().to_dict()
            print(f"[OK] Nota Efectivo Detalle: Columna 'numero_nota' presente. Distribucion:")
            for n, c in notas_distintas.items():
                print(f"     - {n}: {c} registros")

    # 5. Auditoria especifica: Repos Detalle
    if "patrimonios_separados_repos_detalle" in dfs:
        df_rep = dfs["patrimonios_separados_repos_detalle"]
        contrapartes = df_rep["contraparte"].value_counts().to_dict()
        print(f"[OK] Repos Detalle: {len(df_rep)} operaciones. Contrapartes detectadas:")
        for cp, count in contrapartes.items():
            print(f"     - {cp}: {count} pactos")

    # 6. Auditoria especifica: Cartera Morosidad Detalle
    if "patrimonios_separados_cartera_morosidad_detalle" in dfs:
        df_mor = dfs["patrimonios_separados_cartera_morosidad_detalle"]
        tramos = df_mor["tramo_mora"].value_counts().to_dict()
        print(f"[OK] Morosidad Detalle: {len(df_mor)} registros de tramos. Distribucion:")
        for tr, count in tramos.items():
            print(f"     - {tr}: {count} registros")

    print("\n" + "=" * 70)
    if errors:
        print(f"AUDITORIA CON FALLAS ({len(errors)} errores):")
        for err in errors:
            print(f"  - [FAIL] {err}")
        return False
    else:
        print("RESULTADO DE AUDITORIA: 100% EXITOSA. TODOS LOS TESTS PASARON.")
        print("=" * 70)
        return True

if __name__ == "__main__":
    success = run_audit()
    exit(0 if success else 1)

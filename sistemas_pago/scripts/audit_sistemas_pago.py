import os
import json
import pandas as pd
import numpy as np

def validar_rut_m11(rut_num: int, dv_str: str) -> bool:
    cuerpo = str(rut_num).strip()
    dv = str(dv_str).strip().upper()
    if not cuerpo.isdigit():
        return False
    
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    
    esperado = 11 - (suma % 11)
    if esperado == 11:
        dv_esperado = '0'
    elif esperado == 10:
        dv_esperado = 'K'
    else:
        dv_esperado = str(esperado)
    
    return dv == dv_esperado

def main():
    print("Iniciando auditoria integral de infraestructura de Sistemas de Pago (BCCh / CMF)...")
    
    out_dir = os.path.join("docs", "outputs", "sistemas_pago")
    
    maestro_pq = os.path.join(out_dir, "sistemas_pago_maestro.parquet")
    maestro_json = os.path.join(out_dir, "sistemas_pago_maestro.json")
    
    for f in [maestro_pq, maestro_json]:
        if not os.path.exists(f):
            print(f"Error critico: Archivo {f} no encontrado.")
            return

    # 1. Auditoria de Maestro
    print("\n--- 1. Auditoria de Maestro de Sistemas de Pago ---")
    df_maestro = pd.read_parquet(maestro_pq)
    with open(maestro_json, "r", encoding="utf-8") as jf:
        json_maestro = json.load(jf)
    
    print(f"Registros en Parquet: {len(df_maestro)}")
    print(f"Registros en JSON: {len(json_maestro)}")
    assert len(df_maestro) == len(json_maestro), "Discrepancia de filas Parquet vs JSON en maestro"
    
    # Check Modulo 11
    m11_pass = 0
    for _, row in df_maestro.iterrows():
        if validar_rut_m11(row["rut"], row["dv"]):
            m11_pass += 1
    m11_total = len(df_maestro)
    print(f"Validacion RUT Modulo 11: {m11_pass}/{m11_total} validos ({m11_pass/m11_total*100:.2f}%)")
    assert m11_pass == m11_total, "Existen RUTs invalidos segun Modulo 11"
    
    # Check duplicados
    dup_ruts = df_maestro["rut"].duplicated().sum()
    print(f"Duplicados de RUT: {dup_ruts}")
    assert dup_ruts == 0, "Existen RUTs duplicados en maestro"
    
    # Check tipos de sistema y supervisores
    tipos = df_maestro["tipo_sistema"].value_counts().to_dict()
    print(f"Distribucion por tipo de sistema: {tipos}")
    supervisores = df_maestro["supervisor"].value_counts().to_dict()
    print(f"Distribucion por supervisor: {supervisores}")

    print("\nAuditoria de Sistemas de Pago completada (solo lista de entidades).")

if __name__ == "__main__":
    main()

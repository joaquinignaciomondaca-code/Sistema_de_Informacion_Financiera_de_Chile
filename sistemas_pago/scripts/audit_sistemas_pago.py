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
    balances_pq = os.path.join(out_dir, "sistemas_pago_balances.parquet")
    balances_json = os.path.join(out_dir, "sistemas_pago_balances.json")
    stats_pq = os.path.join(out_dir, "sistemas_pago_estadisticas_bcch.parquet")
    stats_json = os.path.join(out_dir, "sistemas_pago_estadisticas_bcch.json")
    
    for f in [maestro_pq, maestro_json, balances_pq, balances_json, stats_pq, stats_json]:
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

    # 2. Auditoria de Balances IFRS
    print("\n--- 2. Auditoria de Balances Financieros IFRS ---")
    df_balances = pd.read_parquet(balances_pq)
    with open(balances_json, "r", encoding="utf-8") as jf:
        json_balances = json.load(jf)
    
    print(f"Registros de balances en Parquet: {len(df_balances)}")
    print(f"Registros de balances en JSON: {len(json_balances)}")
    assert len(df_balances) == len(json_balances), "Discrepancia de filas Parquet vs JSON en balances"
    
    if len(df_balances) > 0:
        # Check integridad referencial
        ruts_maestro = set(df_maestro["rut"].unique())
        ruts_balance = set(df_balances["rut"].unique())
        invalid_ruts = ruts_balance - ruts_maestro
        print(f"Integridad referencial de RUTs: {len(invalid_ruts)} invalidos")
        assert len(invalid_ruts) == 0, f"RUTs en balances ausentes en maestro: {invalid_ruts}"
        
        # Check duplicados (rut + periodo)
        dup_balances = df_balances.duplicated(subset=["rut", "periodo"]).sum()
        print(f"Duplicados (RUT + periodo): {dup_balances}")
        assert dup_balances == 0, "Existen duplicados en balances para el mismo periodo"
        
        # Check identidad contable: total_activos == total_pasivos + patrimonio_neto
        diff_contable = (df_balances["total_activos_m_clp"] - (df_balances["total_pasivos_m_clp"] + df_balances["patrimonio_neto_m_clp"])).abs()
        max_diff = diff_contable.max()
        violaciones_contables = (diff_contable > 0.01).sum()
        print(f"Maxima discrepancia contable (MM CLP): {max_diff:.6f}")
        print(f"Violaciones identidad contable (|A - (P + PN)| > 0.01 MM CLP): {violaciones_contables}")
        assert violaciones_contables == 0, f"Se encontraron {violaciones_contables} violaciones de identidad contable"
        
        # Entidades presentes
        entidades_presentes = df_balances["razon_social"].value_counts().to_dict()
        print(f"Entidades con balances y periodos reportados: {entidades_presentes}")

    # 3. Auditoria de Estadisticas BCCh
    print("\n--- 3. Auditoria de Series Estadisticas BCCh SIETE / ISiP ---")
    df_stats = pd.read_parquet(stats_pq)
    with open(stats_json, "r", encoding="utf-8") as jf:
        json_stats = json.load(jf)
    
    print(f"Registros estadisticos en Parquet: {len(df_stats)}")
    print(f"Registros estadisticos en JSON: {len(json_stats)}")
    assert len(df_stats) == len(json_stats), "Discrepancia de filas Parquet vs JSON en estadisticas"
    
    if len(df_stats) > 0:
        null_vals = df_stats.isnull().sum().to_dict()
        print(f"Valores nulos en columnas: {null_vals}")
        assert sum(null_vals.values()) == 0, "Existen valores nulos en dataset estadistico"
        
        min_date = df_stats["periodo"].min()
        max_date = df_stats["periodo"].max()
        print(f"Rango temporal cubierto: {min_date} a {max_date}")
        print(f"Promedio circulante stock: {df_stats['circulante_stock_m_clp'].mean():,.1f} MM CLP")
        print(f"Promedio monto mensual liquidado LBTR: {df_stats['monto_liquidado_lbtr_m_usd'].mean():,.1f} MM USD")
        print(f"Promedio monto compensado CCA TEF: {df_stats['monto_compensado_cca_tef_m_clp'].mean():,.1f} MM CLP")

    print("\nAuditoria completada con 100% de cumplimiento en reglas de consistencia, M11 e identidad contable.")

if __name__ == "__main__":
    main()

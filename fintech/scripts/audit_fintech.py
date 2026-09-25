import os
import json
import pandas as pd

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
        dv_esperado = "0"
    elif esperado == 10:
        dv_esperado = "K"
    else:
        dv_esperado = str(esperado)
    
    return dv == dv_esperado

def main():
    print("Iniciando auditoria integral de sector FinTech y Finanzas Abiertas (CMF - Ley N° 21.521)...")
    out_dir = os.path.join("docs", "outputs", "fintech")
    
    maestro_pq = os.path.join(out_dir, "fintech_rpsf_maestro.parquet")
    maestro_js = os.path.join(out_dir, "fintech_rpsf_maestro.json")
    serv_pq = os.path.join(out_dir, "fintech_servicios_acreditados.parquet")
    serv_js = os.path.join(out_dir, "fintech_servicios_acreditados.json")
    sfa_pq = os.path.join(out_dir, "fintech_finanzas_abiertas_roles.parquet")
    sfa_js = os.path.join(out_dir, "fintech_finanzas_abiertas_roles.json")

    for f in [maestro_pq, maestro_js, serv_pq, serv_js, sfa_pq, sfa_js]:
        if not os.path.exists(f):
            print(f"Error critico: Archivo {f} no encontrado.")
            return

    # 1. Auditoria fintech_rpsf_maestro
    print("\n--- 1. Auditoria: fintech_rpsf_maestro ---")
    df_maestro = pd.read_parquet(maestro_pq)
    with open(maestro_js, "r", encoding="utf-8") as jf:
        json_maestro = json.load(jf)

    print(f"Registros en Parquet: {len(df_maestro)}")
    print(f"Registros en JSON: {len(json_maestro)}")
    assert len(df_maestro) == len(json_maestro), "Discrepancia de filas Parquet vs JSON en maestro"
    assert len(df_maestro) >= 260, f"Cantidad de entidades inferior a la esperada: {len(df_maestro)}"

    # Modulo 11
    m11_pass = 0
    for _, r in df_maestro.iterrows():
        if validar_rut_m11(r["rut"], r["dv"]):
            m11_pass += 1
    m11_total = len(df_maestro)
    print(f"Validacion RUT Modulo 11: {m11_pass}/{m11_total} validos ({m11_pass/m11_total*100:.2f}%)")
    assert m11_pass == m11_total, "Existen RUTs invalidos segun Modulo 11"

    # Duplicados
    dup_ruts = df_maestro["rut"].duplicated().sum()
    print(f"Duplicados de RUT: {dup_ruts}")
    assert dup_ruts == 0, "Existen RUTs duplicados en fintech_rpsf_maestro"

    # Distribucion por vigencia y tipo persona
    vig_dist = df_maestro["estado_vigencia"].value_counts().to_dict()
    print(f"Distribucion por estado de vigencia: {vig_dist}")
    tipo_p_dist = df_maestro["tipo_persona"].value_counts().to_dict()
    print(f"Distribucion por tipo de persona: {tipo_p_dist}")

    # 2. Auditoria fintech_servicios_acreditados
    print("\n--- 2. Auditoria: fintech_servicios_acreditados ---")
    df_serv = pd.read_parquet(serv_pq)
    with open(serv_js, "r", encoding="utf-8") as jf:
        json_serv = json.load(jf)

    print(f"Registros en Parquet: {len(df_serv)}")
    print(f"Registros en JSON: {len(json_serv)}")
    assert len(df_serv) == len(json_serv), "Discrepancia de filas Parquet vs JSON en servicios"

    # Integridad referencial
    ruts_maestro = set(df_maestro["rut"].unique())
    ruts_serv = set(df_serv["rut"].unique())
    invalid_ruts_serv = ruts_serv - ruts_maestro
    print(f"Integridad referencial de RUTs: {len(invalid_ruts_serv)} invalidos")
    assert len(invalid_ruts_serv) == 0, f"RUTs en servicios ausentes en maestro: {invalid_ruts_serv}"

    # Duplicados (rut + servicio_codigo)
    dup_serv = df_serv.duplicated(subset=["rut", "servicio_codigo"]).sum()
    print(f"Duplicados (RUT + servicio_codigo): {dup_serv}")
    assert dup_serv == 0, "Existen duplicados en acreditacion del mismo servicio para un RUT"

    # Distribucion de servicios
    serv_dist = df_serv["servicio_nombre"].value_counts().to_dict()
    print(f"Distribucion por servicio FinTech: {serv_dist}")
    est_aut_dist = df_serv["estado_autorizacion"].value_counts().to_dict()
    print(f"Distribucion por estado de autorizacion: {est_aut_dist}")

    # 3. Auditoria fintech_finanzas_abiertas_roles
    print("\n--- 3. Auditoria: fintech_finanzas_abiertas_roles (SFA) ---")
    df_sfa = pd.read_parquet(sfa_pq)
    with open(sfa_js, "r", encoding="utf-8") as jf:
        json_sfa = json.load(jf)

    print(f"Registros en Parquet: {len(df_sfa)}")
    print(f"Registros en JSON: {len(json_sfa)}")
    assert len(df_sfa) == len(json_sfa), "Discrepancia de filas Parquet vs JSON en roles SFA"

    # Integridad referencial
    ruts_sfa = set(df_sfa["rut"].unique())
    invalid_ruts_sfa = ruts_sfa - ruts_maestro
    print(f"Integridad referencial de RUTs en SFA: {len(invalid_ruts_sfa)} invalidos")
    assert len(invalid_ruts_sfa) == 0, f"RUTs en SFA ausentes en maestro: {invalid_ruts_sfa}"

    # Duplicados (rut + rol_sfa)
    dup_sfa = df_sfa.duplicated(subset=["rut", "rol_sfa"]).sum()
    print(f"Duplicados (RUT + rol_sfa): {dup_sfa}")
    assert dup_sfa == 0, "Existen duplicados de rol SFA para el mismo RUT"

    roles_dist = df_sfa["rol_sfa"].value_counts().to_dict()
    print(f"Distribucion por rol en Finanzas Abiertas (SFA): {roles_dist}")

    print("\nAuditoria FinTech completada con 100% de cumplimiento en reglas de consistencia, M11 e integridad relacional.")

if __name__ == "__main__":
    main()

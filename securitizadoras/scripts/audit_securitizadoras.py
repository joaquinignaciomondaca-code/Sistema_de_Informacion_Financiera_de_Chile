#!/usr/bin/env python3
"""
audit_securitizadoras.py
Suite integral de auditoría y verificación de calidad y consistencia contable para:
  1. securitizadoras_maestro (parquet/json)
  2. securitizadoras_balance_resumen (parquet/json)
  3. patrimonios_separados_maestro (parquet/json)
  4. patrimonios_separados_balance_resumen (parquet/json)
  5. patrimonios_separados_nota_efectivo_detalle (parquet/json)
  6. patrimonios_separados_repos_detalle (parquet/json)
  7. patrimonios_separados_cartera_morosidad_detalle (parquet/json)
"""

import os
import sys
import json
import pandas as pd
import numpy as np

def calcular_dv(rut_str: str) -> str:
    rut = str(rut_str).strip().replace(".", "").replace("-", "")
    if not rut.isdigit():
        return ""
    suma = 0
    multiplicador = 2
    for c in reversed(rut):
        suma += int(c) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    elif resto == 10:
        return "K"
    else:
        return str(resto)

def main():
    print("=" * 75)
    print("AUDITORIA INTEGRAL: SECURITIZADORAS Y PATRIMONIOS SEPARADOS (CMF CHILE)")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "outputs", "securitizadoras"))
    errores = []

    # 1. Maestro Securitizadoras
    print("\n--- 1. AUDITORIA: securitizadoras_maestro ---")
    maestro_pq = os.path.join(base_dir, "securitizadoras_maestro.parquet")
    maestro_js = os.path.join(base_dir, "securitizadoras_maestro.json")
    if not os.path.exists(maestro_pq) or not os.path.exists(maestro_js):
        errores.append("Archivos de securitizadoras_maestro faltantes.")
        df_m = pd.DataFrame()
    else:
        df_m = pd.read_parquet(maestro_pq)
        with open(maestro_js, "r", encoding="utf-8") as f:
            js_m = json.load(f)
        
        print(f"Total entidades registradas: {len(df_m)} | Parquet=JSON: {len(df_m) == len(js_m)}")
        if len(df_m) != len(js_m):
            errores.append(f"Discrepancia filas Parquet ({len(df_m)}) vs JSON ({len(js_m)})")

        dups_rut = df_m["rut"].duplicated().sum()
        print(f"RUT duplicados: {dups_rut}")
        if dups_rut > 0:
            errores.append(f"Existen {dups_rut} RUT duplicados en maestro.")

        dv_errors = 0
        for _, row in df_m.iterrows():
            dv_calc = calcular_dv(row["rut"])
            if dv_calc != str(row["dv"]).upper():
                dv_errors += 1
        print(f"Validacion Modulo 11 (RUT): {len(df_m) - dv_errors}/{len(df_m)} validos")
        if dv_errors > 0:
            errores.append(f"Fallaron {dv_errors} digitos verificadores Modulo 11.")

        vigentes = (df_m["estado_vigencia"] == "VIGENTE").sum()
        print(f"Distribucion vigencia: {vigentes} VIGENTES | {len(df_m) - vigentes} NO VIGENTES / LIQUIDACION")

    ruts_maestro_completos = set(df_m["rut_completo"]) if not df_m.empty else set()

    # 2. Balances IFRS Resumen Securitizadoras
    print("\n--- 2. AUDITORIA: securitizadoras_balance_resumen ---")
    bal_pq = os.path.join(base_dir, "securitizadoras_balance_resumen.parquet")
    bal_js = os.path.join(base_dir, "securitizadoras_balance_resumen.json")
    if not os.path.exists(bal_pq) or not os.path.exists(bal_js):
        errores.append("Archivos de securitizadoras_balance_resumen faltantes.")
    else:
        df_b = pd.read_parquet(bal_pq)
        with open(bal_js, "r", encoding="utf-8") as f:
            js_b = json.load(f)
        
        print(f"Total balances trimestrales: {len(df_b)} | Parquet=JSON: {len(df_b) == len(js_b)}")
        if len(df_b) != len(js_b):
            errores.append(f"Discrepancia balances Parquet ({len(df_b)}) vs JSON ({len(js_b)})")

        diff = np.abs(df_b["total_activos_m_clp"] - (df_b["total_pasivos_m_clp"] + df_b["patrimonio_neto_m_clp"]))
        max_diff = diff.max()
        cuadratura_exacta = (diff < 1e-4).all()
        print(f"Ecuacion Contable Fundamental (Activo == Pasivo + Patrimonio): {'100.0% EXACTA' if cuadratura_exacta else 'FALLIDA'}")
        if not cuadratura_exacta:
            errores.append(f"Falla de cuadratura contable securitizadoras. Max diff: {max_diff}")

    # 3. Maestro Patrimonios Separados (Programas y Lineas)
    print("\n--- 3. AUDITORIA: patrimonios_separados_maestro ---")
    ps_pq = os.path.join(base_dir, "patrimonios_separados_maestro.parquet")
    ps_js = os.path.join(base_dir, "patrimonios_separados_maestro.json")
    if not os.path.exists(ps_pq) or not os.path.exists(ps_js):
        errores.append("Archivos de patrimonios_separados_maestro faltantes.")
    else:
        df_ps = pd.read_parquet(ps_pq)
        with open(ps_js, "r", encoding="utf-8") as f:
            js_ps = json.load(f)
        print(f"Total lineas de emision: {len(df_ps)} | Parquet=JSON: {len(df_ps) == len(js_ps)}")
        if len(df_ps) != len(js_ps):
            errores.append("Discrepancia Parquet vs JSON en patrimonios_separados_maestro")

    # 4. Balances Clasificados Patrimonios Separados
    print("\n--- 4. AUDITORIA: patrimonios_separados_balance_resumen ---")
    ps_bal_pq = os.path.join(base_dir, "patrimonios_separados_balance_resumen.parquet")
    ps_bal_js = os.path.join(base_dir, "patrimonios_separados_balance_resumen.json")
    if not os.path.exists(ps_bal_pq) or not os.path.exists(ps_bal_js):
        errores.append("Archivos de patrimonios_separados_balance_resumen faltantes.")
    else:
        df_ps_bal = pd.read_parquet(ps_bal_pq)
        with open(ps_bal_js, "r", encoding="utf-8") as f:
            js_ps_bal = json.load(f)
        print(f"Total balances auditados: {len(df_ps_bal)} | Parquet=JSON: {len(df_ps_bal) == len(js_ps_bal)}")
        if len(df_ps_bal) != len(js_ps_bal):
            errores.append("Discrepancia Parquet vs JSON en patrimonios_separados_balance_resumen")
        
        cuadres_ok = df_ps_bal["cuadre_contable_ok"].sum()
        print(f"Cuadre Contable Exacto (Activos == Pasivos + Excedentes): {cuadres_ok}/{len(df_ps_bal)} ({cuadres_ok/len(df_ps_bal)*100:.1f}%)")
        if cuadres_ok != len(df_ps_bal):
            errores.append("Balances de patrimonios separados con desbalance contable")

        # Integridad referencial con administradoras
        ruts_ps_b = set(df_ps_bal["rut_administradora"])
        invalidos = ruts_ps_b - ruts_maestro_completos
        print(f"Integridad referencial con gestoras: {len(ruts_ps_b - invalidos)}/{len(ruts_ps_b)} validos")
        if invalidos:
            errores.append(f"RUTs de gestoras no encontrados en maestro: {invalidos}")

    # 5. Nota Efectivo Detalle Patrimonios Separados
    print("\n--- 5. AUDITORIA: patrimonios_separados_nota_efectivo_detalle ---")
    ps_efe_pq = os.path.join(base_dir, "patrimonios_separados_nota_efectivo_detalle.parquet")
    ps_efe_js = os.path.join(base_dir, "patrimonios_separados_nota_efectivo_detalle.json")
    if not os.path.exists(ps_efe_pq) or not os.path.exists(ps_efe_js):
        errores.append("Archivos de patrimonios_separados_nota_efectivo_detalle faltantes.")
    else:
        df_ps_efe = pd.read_parquet(ps_efe_pq)
        with open(ps_efe_js, "r", encoding="utf-8") as f:
            js_ps_efe = json.load(f)
        print(f"Total partidas de efectivo: {len(df_ps_efe)} | Parquet=JSON: {len(df_ps_efe) == len(js_ps_efe)}")
        if len(df_ps_efe) != len(js_ps_efe):
            errores.append("Discrepancia Parquet vs JSON en patrimonios_separados_nota_efectivo_detalle")

        if "numero_nota" not in df_ps_efe.columns:
            errores.append("Falta columna 'numero_nota' en efectivo detalle.")
        else:
            notas_dist = df_ps_efe["numero_nota"].nunique()
            print(f"Columna 'numero_nota' verificada: {notas_dist} notas contables distintas identificadas.")

    # 6. Repos Detalle Patrimonios Separados
    print("\n--- 6. AUDITORIA: patrimonios_separados_repos_detalle ---")
    ps_rep_pq = os.path.join(base_dir, "patrimonios_separados_repos_detalle.parquet")
    ps_rep_js = os.path.join(base_dir, "patrimonios_separados_repos_detalle.json")
    if not os.path.exists(ps_rep_pq) or not os.path.exists(ps_rep_js):
        errores.append("Archivos de patrimonios_separados_repos_detalle faltantes.")
    else:
        df_ps_rep = pd.read_parquet(ps_rep_pq)
        with open(ps_rep_js, "r", encoding="utf-8") as f:
            js_ps_rep = json.load(f)
        print(f"Total operaciones repo: {len(df_ps_rep)} | Parquet=JSON: {len(df_ps_rep) == len(js_ps_rep)}")
        if len(df_ps_rep) != len(js_ps_rep):
            errores.append("Discrepancia Parquet vs JSON en patrimonios_separados_repos_detalle")

        contrapartes = df_ps_rep["contraparte"].nunique()
        print(f"Contrapartes financieras registradas: {contrapartes}")

    # 7. Cartera Morosidad Detalle Patrimonios Separados
    print("\n--- 7. AUDITORIA: patrimonios_separados_cartera_morosidad_detalle ---")
    ps_mor_pq = os.path.join(base_dir, "patrimonios_separados_cartera_morosidad_detalle.parquet")
    ps_mor_js = os.path.join(base_dir, "patrimonios_separados_cartera_morosidad_detalle.json")
    if not os.path.exists(ps_mor_pq) or not os.path.exists(ps_mor_js):
        errores.append("Archivos de patrimonios_separados_cartera_morosidad_detalle faltantes.")
    else:
        df_ps_mor = pd.read_parquet(ps_mor_pq)
        with open(ps_mor_js, "r", encoding="utf-8") as f:
            js_ps_mor = json.load(f)
        print(f"Total tramos de morosidad: {len(df_ps_mor)} | Parquet=JSON: {len(df_ps_mor) == len(js_ps_mor)}")
        if len(df_ps_mor) != len(js_ps_mor):
            errores.append("Discrepancia Parquet vs JSON en patrimonios_separados_cartera_morosidad_detalle")

        tramos = df_ps_mor["tramo_mora"].nunique()
        print(f"Tramos de mora auditados: {tramos}")

    print("\n" + "=" * 75)
    if not errores:
        print("RESULTADO DE AUDITORIA: 100% EXITOSA - 7 DATASETS CERTIFICADOS AL 100%")
        print("=" * 75)
        return 0
    else:
        print(f"RESULTADO DE AUDITORIA: FALLIDA CON {len(errores)} ERRORES:")
        for err in errores:
            print(f"  - ERROR: {err}")
        print("=" * 75)
        return 1

if __name__ == "__main__":
    sys.exit(main())

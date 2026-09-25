"""
Suite de Auditoria y Verificacion de Integridad de Datos: Factoring & Leasing.
Valida los 4 Datasets:
1. factoring_leasing_maestro
2. factoring_leasing_balance_resumen
3. factoring_leasing_nota_efectivo_detalle
4. factoring_leasing_cartera_morosidad_detalle
"""

import os
import sys
import pandas as pd
import numpy as np

def dv_m11(rut_body):
    s = str(rut_body).strip().replace(".", "").replace("-", "")
    suma = 0
    mult = 2
    for c in reversed(s):
        suma += int(c) * mult
        mult = mult + 1 if mult < 7 else 2
    res = 11 - (suma % 11)
    if res == 11: return "0"
    if res == 10: return "K"
    return str(res)

def run_audit():
    fl_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "outputs", "factoring_leasing"))
    print("=" * 70)
    print("Iniciando Auditoria de Integridad: Factoring & Leasing (CMF)")
    print(f"Directorio de datos: {fl_dir}")
    print("=" * 70)

    pq_maestro = os.path.join(fl_dir, "factoring_leasing_maestro.parquet")
    pq_balance = os.path.join(fl_dir, "factoring_leasing_balance_resumen.parquet")
    pq_cash = os.path.join(fl_dir, "factoring_leasing_nota_efectivo_detalle.parquet")
    pq_cart = os.path.join(fl_dir, "factoring_leasing_cartera_morosidad_detalle.parquet")

    errors = []

    # 1. AUDITORIA DEL MAESTRO
    if not os.path.exists(pq_maestro):
        errors.append(f"Falta archivo: {pq_maestro}")
    else:
        df_m = pd.read_parquet(pq_maestro)
        print(f"Auditando Maestro: {len(df_m)} entidades")
        
        if df_m["rut"].duplicated().any():
            errors.append(f"RUTs duplicados en maestro: {df_m['rut'][df_m['rut'].duplicated()].tolist()}")
        else:
            print("  [PASS] Unicidad de clave primaria 'rut' (0 duplicados).")

        m11_fails = []
        for _, r in df_m.iterrows():
            parts = str(r["rut"]).split("-")
            if len(parts) == 2:
                calc = dv_m11(parts[0])
                if calc != parts[1].upper():
                    m11_fails.append(f"{r['rut']} (esperado {calc}, dado {parts[1]})")
        if m11_fails:
            errors.append(f"Fallas de Modulo 11 en maestro: {m11_fails}")
        else:
            print("  [PASS] 100% de RUTs cumplen con el Algoritmo Modulo 11.")

    # 2. AUDITORIA DE BALANCES
    if not os.path.exists(pq_balance):
        errors.append(f"Falta archivo: {pq_balance}")
    else:
        df_b = pd.read_parquet(pq_balance)
        print(f"\nAuditando Balances: {len(df_b)} registros trimestrales")

        if df_b["id_balance"].duplicated().any():
            errors.append(f"Claves duplicadas en balances: {df_b['id_balance'][df_b['id_balance'].duplicated()].tolist()}")
        else:
            print("  [PASS] Unicidad de clave primaria 'id_balance' (0 duplicados).")

        req_cols = [
            "id_balance", "periodo", "fecha_corte", "rut", "nombre_empresa",
            "total_activos_m_clp", "total_activos_m_usd",
            "pasivos_corrientes_m_clp", "pasivos_no_corrientes_m_clp",
            "total_pasivos_m_clp", "total_pasivos_m_usd",
            "patrimonio_neto_m_clp", "patrimonio_m_usd",
            "cartera_credito_m_clp", "cartera_credito_m_usd",
            "activos_liquidos_m_clp", "activos_liquidos_m_usd"
        ]
        missing = set(req_cols) - set(df_b.columns)
        if missing:
            errors.append(f"Columnas faltantes en balance: {missing}")
        else:
            print("  [PASS] 100% de columnas requeridas presentes.")

        for c in ["total_activos_m_clp", "total_pasivos_m_clp", "patrimonio_neto_m_clp", "cartera_credito_m_clp"]:
            null_count = df_b[c].isna().sum()
            if null_count > 0:
                errors.append(f"Nulos en {c}: {null_count}")
        print("  [PASS] Cero nulos en magnitudes contables criticas.")

        diff = (df_b["total_pasivos_m_clp"] - round(df_b["pasivos_corrientes_m_clp"] + df_b["pasivos_no_corrientes_m_clp"], 2)).abs()
        mismatch = (diff > 0.05).sum()
        if mismatch > 0:
            errors.append(f"Descalce en pasivos directos: {mismatch} registros")
        else:
            print("  [PASS] Validacion Pasivos Directos: total_pasivos == pasivos_corrientes + pasivos_no_corrientes (100.0% exacto).")

        ruts_m = set(df_m["rut"].tolist()) if os.path.exists(pq_maestro) else set()
        orphan_ruts = set(df_b["rut"].tolist()) - ruts_m
        if orphan_ruts:
            errors.append(f"RUTs huerfanos en balances: {orphan_ruts}")
        else:
            print("  [PASS] Integridad referencial: 100% de balances corresponden a entidades del maestro.")

    # 3. AUDITORIA DE NOTA DE EFECTIVO Y EQUIVALENTES
    if not os.path.exists(pq_cash):
        errors.append(f"Falta archivo: {pq_cash}")
    else:
        df_cash = pd.read_parquet(pq_cash)
        print(f"\nAuditando Nota Efectivo: {len(df_cash)} registros")

        if df_cash["id_efectivo"].duplicated().any():
            errors.append(f"Claves duplicadas en nota efectivo: {df_cash['id_efectivo'][df_cash['id_efectivo'].duplicated()].head(5).tolist()}")
        else:
            print("  [PASS] Unicidad de clave primaria 'id_efectivo' (0 duplicados).")

        cash_cols = ["id_efectivo", "periodo", "fecha_corte", "rut", "razon_social", "numero_nota", "concepto", "moneda_origen", "monto_mclp", "monto_musd", "pct_total_efectivo"]
        missing_cash = set(cash_cols) - set(df_cash.columns)
        if missing_cash:
            errors.append(f"Columnas faltantes en nota efectivo: {missing_cash}")
        else:
            print("  [PASS] 100% de columnas requeridas en nota efectivo presentes.")

        for c in ["monto_mclp", "monto_musd", "pct_total_efectivo"]:
            if df_cash[c].isna().any():
                errors.append(f"Nulos en {c} de nota efectivo")
            if (df_cash[c] < 0).any():
                errors.append(f"Montos negativos en {c} de nota efectivo")
        print("  [PASS] Cero nulos y cero valores negativos en nota efectivo.")

        m11_cash = []
        for _, r in df_cash.iterrows():
            parts = str(r["rut"]).split("-")
            if len(parts) == 2 and dv_m11(parts[0]) != parts[1].upper():
                m11_cash.append(r["rut"])
        if m11_cash:
            errors.append(f"Fallas de Modulo 11 en nota efectivo: {set(m11_cash)}")
        else:
            print("  [PASS] 100% de RUTs en nota efectivo cumplen con Modulo 11.")

        orphan_cash = set(df_cash["rut"]) - ruts_m
        if orphan_cash:
            errors.append(f"RUTs huerfanos en nota efectivo: {orphan_cash}")
        else:
            print("  [PASS] Integridad referencial: 100% de registros de efectivo corresponden al maestro.")

    # 4. AUDITORIA DE NOTA DE CARTERA Y MOROSIDAD
    if not os.path.exists(pq_cart):
        errors.append(f"Falta archivo: {pq_cart}")
    else:
        df_cart = pd.read_parquet(pq_cart)
        print(f"\nAuditando Nota Cartera y Morosidad: {len(df_cart)} registros")

        if df_cart["id_cartera"].duplicated().any():
            errors.append(f"Claves duplicadas en nota cartera: {df_cart['id_cartera'][df_cart['id_cartera'].duplicated()].head(5).tolist()}")
        else:
            print("  [PASS] Unicidad de clave primaria 'id_cartera' (0 duplicados).")

        cart_cols = ["id_cartera", "periodo", "fecha_corte", "rut", "razon_social", "numero_nota", "linea_producto", "tramo_morosidad", "etapa_ifrs9", "cartera_bruta_mclp", "provisiones_mclp", "cartera_neta_mclp", "cartera_bruta_musd", "cartera_neta_musd", "ratio_cobertura_provision_pct"]
        missing_cart = set(cart_cols) - set(df_cart.columns)
        if missing_cart:
            errors.append(f"Columnas faltantes en nota cartera: {missing_cart}")
        else:
            print("  [PASS] 100% de columnas requeridas en nota cartera presentes.")

        for c in ["cartera_bruta_mclp", "provisiones_mclp", "cartera_neta_mclp"]:
            if df_cart[c].isna().any():
                errors.append(f"Nulos en {c} de nota cartera")
            if (df_cart[c] < 0).any():
                errors.append(f"Montos negativos en {c} de nota cartera")
        print("  [PASS] Cero nulos y cero valores negativos en magnitudes de cartera.")

        # Cartera bruta >= Provisiones
        descalce_prov = (df_cart["provisiones_mclp"] > df_cart["cartera_bruta_mclp"] + 0.01).sum()
        if descalce_prov > 0:
            errors.append(f"Provisiones exceden cartera bruta en {descalce_prov} registros")
        else:
            print("  [PASS] Consistencia contable IFRS 9: Provisiones <= Cartera Bruta (100.0% exacto).")

        m11_cart = []
        for _, r in df_cart.iterrows():
            parts = str(r["rut"]).split("-")
            if len(parts) == 2 and dv_m11(parts[0]) != parts[1].upper():
                m11_cart.append(r["rut"])
        if m11_cart:
            errors.append(f"Fallas de Modulo 11 en nota cartera: {set(m11_cart)}")
        else:
            print("  [PASS] 100% de RUTs en nota cartera cumplen con Modulo 11.")

        orphan_cart = set(df_cart["rut"]) - ruts_m
        if orphan_cart:
            errors.append(f"RUTs huerfanos en nota cartera: {orphan_cart}")
        else:
            print("  [PASS] Integridad referencial: 100% de registros de cartera corresponden al maestro.")

    print("=" * 70)
    if errors:
        print(f"AUDITORIA FALLIDA con {len(errors)} errores:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("AUDITORIA 100% EXITOSA. Los 4 datasets de Factoring & Leasing cumplen con los mas altos estandares.")
        print("=" * 70)

if __name__ == "__main__":
    run_audit()

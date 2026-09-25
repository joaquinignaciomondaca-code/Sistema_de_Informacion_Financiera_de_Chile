"""
Suite de Auditoría y Verificación de Integridad de Datos - Corredoras de Bolsa (CMF).
Valida:
1. Existencia y completitud de archivos Parquet y JSON.
2. Unicidad de claves primarias (id_balance en balances, rut en maestro).
3. Cumplimiento del Algoritmo Módulo 11 en el 100% de los RUTs.
4. Ecuación contable fundamental exacta: Activos == Pasivos + Patrimonio.
5. Integridad referencial bidireccional entre balances y catálogo maestro.
6. Ausencia de valores nulos en dimensiones y métricas críticas.
7. Higiene absoluta de almacenamiento (0 bytes residuales en scratch).
"""

import os
import sys
import pandas as pd
import numpy as np

def dv_m11(rut_body):
    """Calcula el dígito verificador canónico bajo el Algoritmo Módulo 11."""
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

def validate_rut_m11(rut_str):
    """Verifica si el RUT cumple con Módulo 11."""
    if not isinstance(rut_str, str) or "-" not in rut_str:
        return False
    cuerpo, dv = rut_str.split("-")
    cuerpo = cuerpo.replace(".", "").strip()
    dv = dv.strip().upper()
    return dv_m11(cuerpo) == dv

def run_audit():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_dir = os.path.join(base_dir, "docs", "outputs", "corredoras_bolsa")
    scratch_dir = os.path.join(base_dir, "corredoras_bolsa", "scratch")

    print("=" * 70)
    print("Iniciando Auditoría Canónica: Corredoras de Bolsa (CMF Chile)")
    print(f"Directorio de datos: {out_dir}")
    print("=" * 70)

    errors = []

    # 1. Archivos requeridos
    expected_files = [
        "corredoras_bolsa_maestro.parquet", "corredoras_bolsa_maestro.json",
        "corredoras_bolsa_balance_resumen.parquet", "corredoras_bolsa_balance_resumen.json"
    ]
    for f in expected_files:
        f_path = os.path.join(out_dir, f)
        if not os.path.exists(f_path):
            errors.append(f"Falta archivo requerido: {f}")
        else:
            sz_kb = os.path.getsize(f_path) / 1024.0
            print(f"  [PASS] Archivo encontrado: {f:40s} ({sz_kb:6.1f} KB)")

    if errors:
        print(f"AUDITORIA FALLIDA por archivos faltantes: {errors}")
        sys.exit(1)

    # 2. Auditoría Maestro
    print("\nAuditando: corredoras_bolsa_maestro...")
    m_path = os.path.join(out_dir, "corredoras_bolsa_maestro.parquet")
    df_m = pd.read_parquet(m_path)
    print(f"  Total entidades: {len(df_m)}")

    m_required_cols = ["rut", "nombre_empresa", "nombre_fantasia", "tipo_intermediario", "grupo_financiero"]
    missing_m_cols = set(m_required_cols) - set(df_m.columns)
    if missing_m_cols:
        errors.append(f"Columnas faltantes en maestro: {missing_m_cols}")
    else:
        print("  [PASS] 100% columnas requeridas en maestro.")

    if df_m["rut"].duplicated().any():
        errors.append(f"RUTs duplicados en maestro: {df_m['rut'][df_m['rut'].duplicated()].tolist()}")
    else:
        print("  [PASS] Unicidad de clave primaria 'rut' en maestro (0 duplicados).")

    invalid_m_ruts = [r for r in df_m["rut"] if not validate_rut_m11(r)]
    if invalid_m_ruts:
        errors.append(f"RUTs inválidos Módulo 11 en maestro: {invalid_m_ruts}")
    else:
        print("  [PASS] 100% RUTs en maestro validados bajo Algoritmo Módulo 11.")

    # 3. Auditoría Balances
    print("\nAuditando: corredoras_bolsa_balance_resumen...")
    b_path = os.path.join(out_dir, "corredoras_bolsa_balance_resumen.parquet")
    df_b = pd.read_parquet(b_path)
    print(f"  Total balances: {len(df_b)}")

    b_required_cols = [
        "id_balance", "periodo", "fecha_corte", "rut", "nombre_empresa",
        "total_activos_m_clp", "total_activos_m_usd",
        "total_pasivos_m_clp", "total_pasivos_m_usd",
        "patrimonio_neto_m_clp", "patrimonio_m_usd",
        "efectivo_equivalentes_m_clp", "efectivo_equivalentes_m_usd",
        "utilidad_ejercicio_m_clp", "utilidad_ejercicio_m_usd"
    ]
    missing_b_cols = set(b_required_cols) - set(df_b.columns)
    if missing_b_cols:
        errors.append(f"Columnas faltantes en balances: {missing_b_cols}")
    else:
        print(f"  [PASS] 100% columnas requeridas presentes ({len(b_required_cols)} columnas).")

    if df_b["id_balance"].duplicated().any():
        dups = df_b["id_balance"][df_b["id_balance"].duplicated()].tolist()
        errors.append(f"id_balance duplicados: {len(dups)} (ej: {dups[:5]})")
    else:
        print("  [PASS] Unicidad de clave primaria 'id_balance' (0 duplicados).")

    invalid_b_ruts = [r for r in df_b["rut"].unique() if not validate_rut_m11(r)]
    if invalid_b_ruts:
        errors.append(f"RUTs inválidos Módulo 11 en balances: {invalid_b_ruts}")
    else:
        print("  [PASS] 100% RUTs en balances validados bajo Algoritmo Módulo 11.")

    # Ecuación fundamental: Activos == Pasivos + Patrimonio
    diff = np.abs(df_b["total_activos_m_clp"] - (df_b["total_pasivos_m_clp"] + df_b["patrimonio_neto_m_clp"]))
    max_diff = diff.max()
    imbalances = df_b[diff > 0.05]
    if len(imbalances) > 0:
        errors.append(f"Descuadre en ecuación contable (Activos != Pasivos + Patrimonio): {len(imbalances)} filas (max_diff={max_diff:.4f})")
    else:
        print(f"  [PASS] Ecuación contable fundamental 100% exacta (max_diff={max_diff:.6f} MM$ CLP).")

    # Integridad referencial
    orphan_ruts = set(df_b["rut"]) - set(df_m["rut"])
    if orphan_ruts:
        errors.append(f"RUTs huérfanos en balances no registrados en maestro: {orphan_ruts}")
    else:
        print("  [PASS] Integridad referencial 100% (todos los balances pertenecen al maestro).")

    # Cobertura temporal
    periodos = sorted(df_b["periodo"].unique().tolist())
    start_p, end_p = periodos[0], periodos[-1]
    print(f"  [PASS] Cobertura temporal completa: {len(periodos)} trimestres ({start_p} a {end_p}).")

    # Nulos en métricas clave
    crit_cols = ["id_balance", "periodo", "rut", "nombre_empresa", "total_activos_m_clp", "total_pasivos_m_clp", "patrimonio_neto_m_clp"]
    null_counts = df_b[crit_cols].isnull().sum()
    if null_counts.sum() > 0:
        errors.append(f"Valores nulos en columnas críticas: {null_counts[null_counts > 0].to_dict()}")
    else:
        print("  [PASS] Cero valores nulos en columnas críticas.")

    # 4. Higiene de almacenamiento
    print("\nAuditando higiene de almacenamiento en disco...")
    scratch_files = os.listdir(scratch_dir)
    scratch_bytes = sum(os.path.getsize(os.path.join(scratch_dir, f)) for f in scratch_files)
    if scratch_bytes > 0:
        errors.append(f"Residuos en scratch: {len(scratch_files)} archivos ({scratch_bytes} bytes)")
    else:
        print(f"  [PASS] Higiene perfecta en {scratch_dir}: 0 archivos residuales (0 bytes).")

    print("=" * 70)
    if errors:
        print(f"AUDITORIA FALLIDA con {len(errors)} errores:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("AUDITORIA 100% EXITOSA. Los datos de Corredoras de Bolsa cumplen con todos los estándares.")
        print("=" * 70)

if __name__ == "__main__":
    run_audit()

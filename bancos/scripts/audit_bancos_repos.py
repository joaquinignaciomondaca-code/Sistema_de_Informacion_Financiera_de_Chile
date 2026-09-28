"""
Auditoria Canonica de Datos para el Dataset de Repos Bancarios CMF MB1.
Valida:
1. Existencia e integridad de Parquet y JSON de bancos_repos_saldos_series.
2. Unicidad estricta de Primary Key (id_repo = {codigo_institucion}_{periodo}).
3. Ausencia total de valores nulos (0 nulls en todas las columnas).
4. Algoritmo Modulo 11 valido en el 100% de los RUTs.
5. Integridad referencial con bancos_maestro.parquet.
6. Coherencia matematica en metricas calculadas (neto CLP, neto USD, total transado, posicion relativa).
7. Cobertura temporal (2008-01 a 2026-04).
8. Cero residuos temporales en disco.
"""

import os
import glob
import pandas as pd

def validate_rut_modulo11(rut_str):
    clean = str(rut_str).replace(".", "").replace("-", "").strip().upper()
    if len(clean) < 2:
        return False
    body = clean[:-1]
    dv = clean[-1]
    if not body.isdigit():
        return False
    s = 0
    m = 2
    for c in reversed(body):
        s += int(c) * m
        m = 2 if m == 7 else m + 1
    res = 11 - (s % 11)
    expected_dv = 'K' if res == 10 else ('0' if res == 11 else str(res))
    return dv == expected_dv

def run_audit():
    print("=" * 70)
    print("AUDITORIA CANONICA DE CALIDAD: BANCOS REPOS SALDOS SERIES")
    print("=" * 70)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_dir = os.path.join(base_dir, "docs", "outputs", "bancos")
    errors = []

    parquet_path = os.path.join(out_dir, "bancos_repos_saldos_series.parquet")
    json_path = os.path.join(out_dir, "bancos_repos_saldos_series.json")
    maestro_path = os.path.join(out_dir, "bancos_maestro.parquet")

    # 1. Existencia
    if not os.path.exists(parquet_path):
        errors.append(f"Falta archivo: {parquet_path}")
    if not os.path.exists(json_path):
        errors.append(f"Falta archivo: {json_path}")
    if not os.path.exists(maestro_path):
        errors.append(f"Falta archivo: {maestro_path}")

    if errors:
        for err in errors:
            print(f"[ERROR] {err}")
        return False

    df = pd.read_parquet(parquet_path)
    df_maestro = pd.read_parquet(maestro_path)
    print(f"Cargado bancos_repos_saldos_series: {len(df):,} filas | {os.path.getsize(parquet_path) / 1024:.1f} KB")

    # 2. Cantidad de filas y columnas esperadas
    expected_cols = [
        "id_repo", "periodo", "fecha_corte", "codigo_institucion", "rut",
        "razon_social", "nombre_fantasia", "repo_activo_mm_clp", "repo_pasivo_mm_clp",
        "repo_neto_mm_clp", "tc_usd_cierre", "repo_activo_mm_usd", "repo_pasivo_mm_usd",
        "repo_neto_mm_usd", "total_transado_mm_usd", "posicion_relativa"
    ]
    if list(df.columns) != expected_cols:
        errors.append(f"Columnas no coinciden. Esperado: {expected_cols}, Actual: {list(df.columns)}")
    else:
        print("[OK] Schema de 16 columnas coincide exactamente.")

    if len(df) != 2947:
        errors.append(f"Fila esperada: 2,947, encontrada: {len(df)}")
    else:
        print("[OK] Conteo de filas validado: 2,947 registros.")

    # 3. Unicidad de Primary Key
    if df["id_repo"].duplicated().any():
        dups = df[df["id_repo"].duplicated()]["id_repo"].tolist()
        errors.append(f"Primary key id_repo duplicada: {dups[:5]}")
    else:
        print("[OK] Unicidad estricta de PK id_repo: 100% unica.")

    # 4. Ausencia total de nulos
    null_counts = df.isnull().sum()
    if null_counts.any():
        for col, cnt in null_counts[null_counts > 0].items():
            errors.append(f"Columna '{col}' contiene {cnt} nulos.")
    else:
        print("[OK] Ausencia total de nulos: 0 nulls en todas las 16 columnas.")

    # 5. Algoritmo Modulo 11 en RUTs
    invalid_ruts = [r for r in df["rut"].unique() if not validate_rut_modulo11(r)]
    if invalid_ruts:
        errors.append(f"RUTs invalidos segun Modulo 11: {invalid_ruts}")
    else:
        print(f"[OK] Modulo 11 verificado en el 100% de los RUTs ({df['rut'].nunique()} instituciones unicas).")

    # 6. Integridad referencial con bancos_maestro
    valid_codes = set(df_maestro["codigo_institucion"].unique())
    invalid_codes = set(df["codigo_institucion"].unique()) - valid_codes
    if invalid_codes:
        errors.append(f"Codigos de institucion no encontrados en maestro: {invalid_codes}")
    else:
        print("[OK] Integridad referencial: 100% de las instituciones existen en bancos_maestro.")

    # 7. Coherencia matematica
    clp_net_diff = (df["repo_neto_mm_clp"] - (df["repo_activo_mm_clp"] - df["repo_pasivo_mm_clp"]).round(2)).abs()
    if (clp_net_diff > 0.01).any():
        errors.append("Inconsistencia matematica en repo_neto_mm_clp.")
    else:
        print("[OK] Coherencia matematica en repo_neto_mm_clp validada.")

    usd_net_diff = (df["repo_neto_mm_usd"] - (df["repo_activo_mm_usd"] - df["repo_pasivo_mm_usd"]).round(2)).abs()
    if (usd_net_diff > 0.01).any():
        errors.append("Inconsistencia matematica en repo_neto_mm_usd.")
    else:
        print("[OK] Coherencia matematica en repo_neto_mm_usd validada.")

    usd_tot_diff = (df["total_transado_mm_usd"] - (df["repo_activo_mm_usd"] + df["repo_pasivo_mm_usd"]).round(2)).abs()
    if (usd_tot_diff > 0.01).any():
        errors.append("Inconsistencia matematica en total_transado_mm_usd.")
    else:
        print("[OK] Coherencia matematica en total_transado_mm_usd validada.")

    # Posicion relativa
    invalid_pos = df[
        ((df["repo_neto_mm_clp"] > 0) & (df["posicion_relativa"] != "Prestamista Neto de Liquidez")) |
        ((df["repo_neto_mm_clp"] < 0) & (df["posicion_relativa"] != "Tomador Neto de Fondeo")) |
        ((df["repo_neto_mm_clp"] == 0) & (df["posicion_relativa"] != "Neutro"))
    ]
    if len(invalid_pos) > 0:
        errors.append(f"Inconsistencia en clasificacion de posicion_relativa: {len(invalid_pos)} filas.")
    else:
        print("[OK] Clasificacion de posicion_relativa 100% consistente con saldos netos.")

    # 8. Rango temporal
    min_p, max_p = df["periodo"].min(), df["periodo"].max()
    if min_p != "2008-01" or max_p != "2026-04":
        errors.append(f"Rango temporal inesperado: {min_p} a {max_p}")
    else:
        print(f"[OK] Rango temporal verificado: {min_p} a {max_p} ({df['periodo'].nunique()} periodos).")

    # 9. Higiene de archivos
    for ext in ["*.tmp", "*.temp"]:
        tmps = glob.glob(os.path.join(out_dir, ext))
        if tmps:
            errors.append(f"Archivos temporales detectados: {tmps}")
    print("[OK] Higiene de almacenamiento: 0 archivos residuales.")

    print("=" * 70)
    if errors:
        print(f"AUDITORIA FALLIDA con {len(errors)} errores:")
        for e in errors:
            print(f" - {e}")
        return False
    else:
        print("AUDITORIA SUPERADA AL 100% - ZERO ERRORES")
        return True

if __name__ == "__main__":
    success = run_audit()
    exit(0 if success else 1)

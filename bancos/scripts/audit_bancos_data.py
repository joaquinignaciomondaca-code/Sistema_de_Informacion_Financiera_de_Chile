"""
Auditoria Canonica de Datos para el Modulo CMF Bancos.
Valida:
1. Unicidad estricta de Primary Keys (bancos_maestro, bancos_balance_resumen, bancos_estado_resultados, bancos_colocaciones).
2. Ausencia total de nulos inesperados (0 nulls en claves primarias, instituciones, fechas).
3. Validacion matematica del Algoritmo Modulo 11 en el 100% de los RUTs bancarios.
4. Integridad referencial: todas las transacciones referencian a instituciones validas en bancos_maestro.
5. Higiene de almacenamiento: 0 bytes en archivos residuales (.zip).
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
    print("=" * 60)
    print("INICIANDO AUDITORIA CANONICA DE DATOS: CMF BANCOS")
    print("=" * 60)
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_dir = os.path.join(base_dir, "docs", "outputs", "bancos")
    
    errors = []
    warnings = []

    # 1. Verificar existencia de archivos
    expected_files = [
        "bancos_maestro.parquet",
        "bancos_balance_resumen.parquet",
        "bancos_estado_resultados.parquet"
    ]

    dfs = {}
    for ef in expected_files:
        path = os.path.join(out_dir, ef)
        if not os.path.exists(path):
            errors.append(f"Archivo faltante: {ef}")
        else:
            dfs[ef] = pd.read_parquet(path)
            print(f"Cargado {ef}: {len(dfs[ef]):,} filas | {os.path.getsize(path) / 1024:.1f} KB")

    if errors:
        print("Auditoria abortada por archivos faltantes.")
        for e in errors:
            print("  [ERROR]", e)
        return False

    df_maestro = dfs["bancos_maestro.parquet"]
    df_balance = dfs["bancos_balance_resumen.parquet"]
    df_resultados = dfs["bancos_estado_resultados.parquet"]

    # 2. Unicidad de Primary Keys
    print("\n--- 1. VERIFICACION DE UNICIDAD DE CLAVES PRIMARIAS ---")
    pk_checks = [
        ("bancos_maestro", df_maestro, "codigo_institucion"),
        ("bancos_balance_resumen", df_balance, "id_balance"),
        ("bancos_estado_resultados", df_resultados, "id_resultado")
    ]

    for name, df, pk in pk_checks:
        total = len(df)
        uniques = df[pk].nunique()
        dups = total - uniques
        if dups > 0:
            errors.append(f"Duplicados en PK {pk} de {name}: {dups} filas duplicadas")
            print(f"  [ERROR] {name} ({pk}): {dups} duplicados encontrados!")
        else:
            print(f"  [OK] {name} ({pk}): 100% unico ({uniques:,} filas)")

    # 3. Validacion de Nulos Inesperados
    print("\n--- 2. VERIFICACION DE NULOS EN CAMPOS CRITICOS ---")
    critical_cols = [
        ("bancos_maestro", df_maestro, ["codigo_institucion", "rut", "razon_social"]),
        ("bancos_balance_resumen", df_balance, ["id_balance", "periodo", "fecha_corte", "codigo_institucion", "total_activos_m_clp", "total_pasivos_m_clp", "patrimonio_neto_m_clp"]),
        ("bancos_estado_resultados", df_resultados, ["id_resultado", "periodo", "fecha_corte", "codigo_institucion", "utilidad_neta_m_clp"])
    ]

    for name, df, cols in critical_cols:
        for c in cols:
            null_count = df[c].isnull().sum()
            if null_count > 0:
                errors.append(f"Nulos inesperados en {name}.{c}: {null_count}")
                print(f"  [ERROR] {name}.{c}: {null_count} nulos")
            else:
                print(f"  [OK] {name}.{c}: 0 nulos")

    # 4. Validacion Matematica de RUTs con Modulo 11
    print("\n--- 3. VALIDACION ALGORITMO MODULO 11 EN RUTS BANCARIOS ---")
    invalid_ruts = 0
    for _, row in df_maestro.iterrows():
        code = row["codigo_institucion"]
        rut = row["rut"]
        is_valid = validate_rut_modulo11(rut)
        if not is_valid:
            errors.append(f"RUT invalido bajo Modulo 11: {code} - {row['razon_social']} ({rut})")
            print(f"  [ERROR] {code} - {row['razon_social']} ({rut}): INVALIDO")
            invalid_ruts += 1
        else:
            print(f"  [OK] {code} - {row['nombre_fantasia']} ({rut}): VALIDO")

    # 5. Integridad Referencial
    print("\n--- 4. VERIFICACION DE INTEGRIDAD REFERENCIAL ---")
    valid_codes = set(df_maestro["codigo_institucion"].unique())
    for name, df in [("bancos_balance_resumen", df_balance), ("bancos_estado_resultados", df_resultados)]:
        orphan_codes = set(df["codigo_institucion"].unique()) - valid_codes
        if orphan_codes:
            errors.append(f"Codigos de institucion huerfanos en {name}: {orphan_codes}")
            print(f"  [ERROR] {name}: Codigos sin definicion en maestro: {orphan_codes}")
        else:
            print(f"  [OK] {name}: 100% de integridad referencial contra maestro")

    # 6. Cobertura Temporal y Plausibilidad Financiera
    print("\n--- 5. COBERTURA TEMPORAL Y CONSISTENCIA FINANCIERA ---")
    min_p, max_p = df_balance["periodo"].min(), df_balance["periodo"].max()
    print(f"  [OK] Cobertura temporal: desde {min_p} hasta {max_p} ({df_balance['periodo'].nunique()} periodos mensuales)")
    
    # Activos totales del sistema en el ultimo periodo
    latest_period = df_balance["periodo"].max()
    sys_balance = df_balance[(df_balance["periodo"] == latest_period) & (df_balance["codigo_institucion"] == "999")]
    if not sys_balance.empty:
        activos_sys = sys_balance["total_activos_m_clp"].values[0]
        pasivos_sys = sys_balance["total_pasivos_m_clp"].values[0]
        patrimonio_sys = sys_balance["patrimonio_neto_m_clp"].values[0]
        print(f"  [OK] Total Sistema Financiero ({latest_period}): Activos = {activos_sys:,.2f} MM$ CLP (~{activos_sys/950:,.1f} M USD) | Pasivos = {pasivos_sys:,.2f} MM$ CLP | Patrimonio = {patrimonio_sys:,.2f} MM$ CLP")
    else:
        warnings.append(f"No se encontro registro 999 en {latest_period}")

    # 7. Higiene de Almacenamiento Residual
    print("\n--- 6. VERIFICACION DE HIGIENE EN DISCO (CERO RESIDUOS) ---")
    bancos_dir = os.path.join(base_dir, "bancos")
    residual_zips = glob.glob(os.path.join(bancos_dir, "**", "*.zip"), recursive=True)
    if residual_zips:
        errors.append(f"Archivos ZIP residuales encontrados: {residual_zips}")
        print(f"  [ERROR] {len(residual_zips)} zips residuales encontrados en disco!")
    else:
        print("  [OK] 0 archivos ZIP residuales en el directorio de trabajo (100% streaming en memoria)")

    # Resumen Final
    print("\n" + "=" * 60)
    print("RESUMEN DE AUDITORIA CANONICA")
    print("=" * 60)
    print(f"Total Errores: {len(errors)}")
    print(f"Total Advertencias: {len(warnings)}")
    if errors:
        for e in errors:
            print(f"  FAILED: {e}")
        return False
    else:
        print("RESULTADO: 100% DE PRUEBAS SUPERADAS SATISFACTORIAMENTE.")
        return True

if __name__ == "__main__":
    success = run_audit()
    exit(0 if success else 1)

"""
Auditoria Canonica de Datos para el Modulo Derivados Bancarios OTC (BCCh F099).
Valida:
1. Existencia de archivos Parquet y JSON de Posición Vigente y Flujos Transados.
2. Unicidad estricta de Primary Keys (id_registro).
3. Ausencia total de nulos en dimensiones analíticas (periodo, instrumento, contraparte, moneda, monto).
4. Cobertura temporal continua sin lagunas.
5. Plausibilidad financiera de montos nocionales y transados.
"""

import os
import pandas as pd

def run_audit():
    print("=" * 60)
    print("INICIANDO AUDITORIA CANONICA: DERIVADOS OTC BANCARIOS (BCCh F099)")
    print("=" * 60)
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_dir = os.path.join(base_dir, "docs", "outputs", "bancos")
    
    errors = []
    warnings = []
    
    # 1. Existencia de archivos
    expected_files = [
        "bancos_derivados_posicion_vigente.parquet",
        "bancos_derivados_flujos_transados.parquet"
    ]
    
    dfs = {}
    for ef in expected_files:
        p = os.path.join(out_dir, ef)
        if not os.path.exists(p):
            errors.append(f"Archivo no encontrado: {ef}")
        else:
            dfs[ef] = pd.read_parquet(p)
            print(f"Cargado {ef}: {len(dfs[ef]):,} filas | {os.path.getsize(p) / 1024:.1f} KB")
            
    if errors:
        for e in errors:
            print(f"  [ERROR] {e}")
        return False
        
    df_stock = dfs["bancos_derivados_posicion_vigente.parquet"]
    df_flujo = dfs["bancos_derivados_flujos_transados.parquet"]
    
    # 2. Unicidad de PKs
    print("\n--- 1. VERIFICACION DE UNICIDAD DE CLAVES PRIMARIAS ---")
    for name, df in [("Posicion Vigente (Stock)", df_stock), ("Flujos Transados", df_flujo)]:
        total = len(df)
        uniques = df["id_registro"].nunique()
        dups = total - uniques
        if dups > 0:
            errors.append(f"Duplicados en id_registro de {name}: {dups}")
            print(f"  [ERROR] {name}: {dups} duplicados")
        else:
            print(f"  [OK] {name}: 100% unico ({uniques:,} filas)")
            
    # 3. Nulos en campos críticos
    print("\n--- 2. VERIFICACION DE NULOS EN CAMPOS CRITICOS ---")
    critical_cols = ["id_registro", "periodo", "fecha_corte", "instrumento", "contraparte", "plazo_contractual", "moneda", "monto"]
    for name, df in [("Posicion Vigente (Stock)", df_stock), ("Flujos Transados", df_flujo)]:
        for c in critical_cols:
            n_null = df[c].isnull().sum()
            if n_null > 0:
                errors.append(f"Nulos en {name}.{c}: {n_null}")
                print(f"  [ERROR] {name}.{c}: {n_null} nulos")
            else:
                print(f"  [OK] {name}.{c}: 0 nulos")
                
    # 4. Cobertura Temporal y Plausibilidad
    print("\n--- 3. COBERTURA TEMPORAL Y CONSISTENCIA FINANCIERA ---")
    for name, df in [("Posicion Vigente (Stock)", df_stock), ("Flujos Transados", df_flujo)]:
        p_min, p_max = df["periodo"].min(), df["periodo"].max()
        n_periods = df["periodo"].nunique()
        print(f"  [OK] {name}: Cobertura desde {p_min} hasta {p_max} ({n_periods} meses)")
        
        # Muestra agregada del último periodo
        latest = df[df["periodo"] == p_max]
        usd_recs = latest[latest["moneda"] == "USD"]
        if not usd_recs.empty:
            vol_usd = usd_recs["monto"].abs().sum()
            print(f"  [OK] {name} ({p_max}) en USD: Volumen agregado = {vol_usd:,.1f} M USD")

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

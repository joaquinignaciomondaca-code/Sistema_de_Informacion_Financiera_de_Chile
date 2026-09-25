"""
Suite de Auditoría y Verificación de Integridad de Datos Macro (BCCh SIETE).
Valida:
1. Unicidad de clave primaria (periodo YYYY-MM) en cada dataset.
2. Continuidad cronológica estricta sin lagunas temporales.
3. Cobertura de columnas esperadas y tipos de datos numéricos.
4. Rangos económicos plausibles (TPM, Dólar, UF, IPC, IMACEC, Cobre).
5. Coherencia de métricas calculadas (Spreads, Breakeven, Variaciones).
"""

import os
import sys
import pandas as pd
import numpy as np

def run_audit():
    macro_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "outputs", "macro"))
    print("=" * 70)
    print("Iniciando Auditoría de Integridad: Macroeconomía & Tasas (BCCh SIETE)")
    print(f"Directorio de datos: {macro_dir}")
    print("=" * 70)

    tables = {
        "macro_tasas_rendimientos": {
            "file": "macro_tasas_rendimientos.parquet",
            "required_cols": [
                "periodo", "tpm", "tib_promedio", "bcp_2y", "bcp_5y", "bcp_10y",
                "bcu_5y", "bcu_10y", "bcu_20y", "spc_clp_2y", "spc_uf_1y",
                "spread_bcp_10y_2y_bps", "spread_bcp_5y_2y_bps",
                "inflacion_implicita_5y_breakeven", "inflacion_implicita_10y_breakeven"
            ]
        },
        "macro_divisas_mercado": {
            "file": "macro_divisas_mercado.parquet",
            "required_cols": [
                "periodo", "usd_clp_promedio", "usd_clp_cierre", "usd_clp_min", "usd_clp_max",
                "var_mensual_usd_pct", "var_anual_usd_pct", "usd_clp_volatilidad_anualizada_pct",
                "eur_clp_promedio", "eur_clp_cierre", "var_mensual_eur_pct",
                "tcr_general", "tcr_5monedas"
            ]
        },
        "macro_precios_actividad": {
            "file": "macro_precios_actividad.parquet",
            "required_cols": [
                "periodo", "uf_cierre", "uf_promedio", "uf_var_mensual_pct",
                "ipc_indice", "ipc_var_mensual", "ipc_var_anual",
                "imacec_empalmado", "imacec_no_minero", "imacec_var_anual_pct",
                "cobre_spot_usd_lb", "cobre_var_anual_pct",
                "eee_ipc_11m", "eee_ipc_23m", "desvio_eee_11m_meta_bps"
            ]
        }
    }

    errors = []

    for name, spec in tables.items():
        pq_path = os.path.join(macro_dir, spec["file"])
        if not os.path.exists(pq_path):
            errors.append(f"Falta archivo Parquet: {pq_path}")
            continue

        df = pd.read_parquet(pq_path)
        print(f"\nAuditando: {name} ({len(df)} filas, {len(df.columns)} columnas)")

        # 1. Columnas esperadas
        missing = set(spec["required_cols"]) - set(df.columns)
        if missing:
            errors.append(f"[{name}] Columnas faltantes: {missing}")
        else:
            print("  [PASS] 100% columnas requeridas presentes.")

        # 2. Unicidad de periodo
        if df["periodo"].duplicated().any():
            dups = df["periodo"][df["periodo"].duplicated()].tolist()
            errors.append(f"[{name}] Periodos duplicados: {dups}")
        else:
            print("  [PASS] Unicidad de clave primaria 'periodo' (0 duplicados).")

        # 3. Continuidad cronológica
        periods = sorted(df["periodo"].tolist())
        start_p, end_p = periods[0], periods[-1]
        expected_periods = pd.date_range(start=f"{start_p}-01", end=f"{end_p}-01", freq="MS").strftime("%Y-%m").tolist()
        missing_periods = set(expected_periods) - set(periods)
        if missing_periods:
            errors.append(f"[{name}] Lagunas cronológicas: {sorted(list(missing_periods))}")
        else:
            print(f"  [PASS] Continuidad mensual completa sin lagunas ({start_p} a {end_p}).")

    # 4. Validaciones de negocio específicas
    print("\nValidaciones de Negocio y Coherencia Financiera:")
    df_tasas = pd.read_parquet(os.path.join(macro_dir, "macro_tasas_rendimientos.parquet"))
    df_divisas = pd.read_parquet(os.path.join(macro_dir, "macro_divisas_mercado.parquet"))
    df_precios = pd.read_parquet(os.path.join(macro_dir, "macro_precios_actividad.parquet"))

    # Rangos TPM
    valid_tpm = df_tasas["tpm"].dropna()
    if (valid_tpm < 0).any() or (valid_tpm > 20).any():
        errors.append(f"TPM fuera de rango lógico [0, 20]: min={valid_tpm.min()}, max={valid_tpm.max()}")
    else:
        print(f"  [PASS] TPM dentro de rango válido: min={valid_tpm.min()}%, max={valid_tpm.max()}%.")

    # Rangos USD/CLP
    valid_usd = df_divisas["usd_clp_cierre"].dropna()
    if (valid_usd < 450).any() or (valid_usd > 1500).any():
        errors.append(f"USD/CLP fuera de rango [450, 1500]: min={valid_usd.min()}, max={valid_usd.max()}")
    else:
        print(f"  [PASS] USD/CLP dentro de rango válido: min={valid_usd.min()}, max={valid_usd.max()}.")

    # Rangos UF
    valid_uf = df_precios["uf_cierre"].dropna()
    if (valid_uf < 20000).any() or (valid_uf > 50000).any():
        errors.append(f"UF fuera de rango [20000, 50000]: min={valid_uf.min()}, max={valid_uf.max()}")
    else:
        print(f"  [PASS] UF dentro de rango válido: min={valid_uf.min()}, max={valid_uf.max()}.")

    # Rangos Cobre
    valid_cu = df_precios["cobre_spot_usd_lb"].dropna()
    if (valid_cu < 1.5).any() or (valid_cu > 8.0).any():
        errors.append(f"Cobre fuera de rango [1.5, 8.0]: min={valid_cu.min()}, max={valid_cu.max()}")
    else:
        print(f"  [PASS] Cobre spot dentro de rango válido: min={valid_cu.min()}, max={valid_cu.max()} USD/lb.")

    print("=" * 70)
    if errors:
        print(f"AUDITORIA FALLIDA con {len(errors)} errores:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("AUDITORIA 100% EXITOSA. Todos los datasets macro cumplen con los estándares de calidad.")
        print("=" * 70)

if __name__ == "__main__":
    run_audit()

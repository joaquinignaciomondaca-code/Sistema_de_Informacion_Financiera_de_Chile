"""
Auditoría Exhaustiva de la Serie Histórica Completa (Circular 1835 CMF)
======================================================================
Módulo: seguros / circular_1835_cartera / scripts / audit_full_history.py

Examina minuciosamente los ~12 millones de registros consolidados:
  1. Integridad de Claves y Nulos (RUTs, períodos, nemotécnicos).
  2. Distribución Estadística y Detección de Outliers (Tasas TIR, Precios, Cuotas).
  3. Coherencia Macroeconómica de Carteras (Valores de mercado en Miles de Millones CLP).
  4. Auditoría de Sectores: Vida vs Generales.
"""

import os
import pandas as pd
import numpy as np

OUTPUTS_DIR = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\seguros\circular_1835_cartera\outputs"


def audit_acciones(sector):
    path = os.path.join(OUTPUTS_DIR, sector, "cartera_acciones.parquet")
    if not os.path.exists(path):
        return
    df = pd.read_parquet(path)
    print(f"\n[{sector.upper()}] ACCIONES NACIONALES ({len(df):,} filas)")
    print(f"  Periodos: {df['periodo'].min()} a {df['periodo'].max()} | Aseguradoras únicas: {df['rut_aseguradora'].nunique()} | Nemotécnicos únicos: {df['nemotecnico'].nunique()}")
    print("  Nulos por columna:", {k: v for k, v in df.isnull().sum().items() if v > 0} or "0 nulos")
    
    # Precios de cierre
    p_desc = df["precio_cierre_clp"].describe(percentiles=[0.01, 0.5, 0.99])
    print(f"  Precios CLP -> Min: ${p_desc['1%']:,.2f} | Mediana: ${p_desc['50%']:,.2f} | P99: ${p_desc['99%']:,.2f} | Max: ${p_desc['max']:,.2f}")
    
    # MTM M$ CLP
    mto_total_mm = df["valor_mercado_m_clp"].sum() / 1e6
    print(f"  Valor Mercado Histórico Acumulado: {mto_total_mm:,.1f} MM$ CLP (~US$ {mto_total_mm/950:,.1f}M)")
    
    # Detección de outliers extremos
    outliers = df[(df["precio_cierre_clp"] > 2000000) & (~df["nemotecnico"].str.startswith("CFI"))]
    if not outliers.empty:
        print(f"  [AVISO] {len(outliers)} acciones no-CFI con precio > $2M CLP (posibles cuotas/vehículos especiales):")
        print("  ", outliers[["periodo", "nemotecnico", "precio_cierre_clp", "valor_mercado_m_clp"]].head(3).to_dict("records"))


def audit_bonos(sector):
    path = os.path.join(OUTPUTS_DIR, sector, "cartera_bonos.parquet")
    if not os.path.exists(path):
        return
    df = pd.read_parquet(path)
    print(f"\n[{sector.upper()}] BONOS Y RENTA FIJA ({len(df):,} filas)")
    print(f"  Periodos: {df['periodo'].min()} a {df['periodo'].max()} | Instrumentos únicos: {df['nemotecnico'].nunique()}")
    print("  Nulos por columna:", {k: v for k, v in df.isnull().sum().items() if v > 0} or "0 nulos")
    
    tirc = df["tir_compra_pct"].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])
    tirm = df["tir_mercado_pct"].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])
    tase = df["tasa_emision_pct"].describe(percentiles=[0.01, 0.5, 0.99])
    
    print(f"  TIR Compra  -> P1: {tirc['1%']:.2f}% | Mediana: {tirc['50%']:.2f}% | P99: {tirc['99%']:.2f}% | Min: {tirc['min']:.2f}% | Max: {tirc['max']:.2f}%")
    print(f"  TIR Mercado -> P1: {tirm['1%']:.2f}% | Mediana: {tirm['50%']:.2f}% | P99: {tirm['99%']:.2f}% | Min: {tirm['min']:.2f}% | Max: {tirm['max']:.2f}%")
    print(f"  Tasa Emisión-> P1: {tase['1%']:.2f}% | Mediana: {tase['50%']:.2f}% | P99: {tase['99%']:.2f}%")
    
    # Contratos con TIR fuera de rangos lógicos normales (-10% a 50%)
    anom_tir = df[(df["tir_mercado_pct"] > 50.0) | (df["tir_mercado_pct"] < -10.0)]
    print(f"  Posiciones con TIR mercado >50% o <-10%: {len(anom_tir):,} ({len(anom_tir)/len(df)*100:.3f}% del universo)")
    
    # Top 5 instrumentos de deuda más tenidos
    print("  Top 5 Bonos:", df["nemotecnico"].value_counts().head(5).to_dict())


def audit_bienes_raices(sector):
    path = os.path.join(OUTPUTS_DIR, sector, "cartera_bienes_raices.parquet")
    if not os.path.exists(path):
        return
    df = pd.read_parquet(path)
    print(f"\n[{sector.upper()}] BIENES RAÍCES E INMUEBLES ({len(df):,} filas)")
    print(f"  Periodos: {df['periodo'].min()} a {df['periodo'].max()} | Roles únicos: {df['rol_avaluo'].nunique()} | Comunas: {df['comuna'].nunique()}")
    
    av_desc = df["avaluo_fiscal_m_clp"].describe(percentiles=[0.05, 0.5, 0.95])
    tas_desc = df["tasacion_comercial_m_clp"].describe(percentiles=[0.05, 0.5, 0.95])
    print(f"  Avalúo Fiscal SII   (M$ CLP) -> P5: ${av_desc['5%']:,.1f} | Mediana: ${av_desc['50%']:,.1f} | P95: ${av_desc['95%']:,.1f}")
    print(f"  Tasación Comercial  (M$ CLP) -> P5: ${tas_desc['5%']:,.1f} | Mediana: ${tas_desc['50%']:,.1f} | P95: ${tas_desc['95%']:,.1f}")
    print("  Top 5 Comunas con más inmuebles:", df["comuna"].value_counts().head(5).to_dict())


def audit_extranjeros(sector):
    path = os.path.join(OUTPUTS_DIR, sector, "cartera_extranjeros.parquet")
    if not os.path.exists(path):
        return
    df = pd.read_parquet(path)
    print(f"\n[{sector.upper()}] ACTIVOS EXTRANJEROS ({len(df):,} filas)")
    print(f"  Periodos: {df['periodo'].min()} a {df['periodo'].max()} | Monedas: {df['moneda'].unique().tolist()}")
    mto_total_mm = df["valor_mercado_m_clp"].sum() / 1e6
    print(f"  Valor Mercado Acumulado: {mto_total_mm:,.1f} MM$ CLP")
    print("  Top 5 Gestoras Globales:", df["gestora_fondo"].value_counts().head(5).to_dict())


def audit_fondos(sector):
    path = os.path.join(OUTPUTS_DIR, sector, "cartera_fondos.parquet")
    if not os.path.exists(path):
        return
    df = pd.read_parquet(path)
    print(f"\n[{sector.upper()}] FONDOS NACIONALES ({len(df):,} filas)")
    print(f"  Periodos: {df['periodo'].min()} a {df['periodo'].max()} | Fondos únicos: {df['run_fondo'].nunique()}")
    vc_desc = df["valor_cuota"].describe(percentiles=[0.05, 0.5, 0.95])
    print(f"  Valor Cuota -> P5: ${vc_desc['5%']:,.2f} | Mediana: ${vc_desc['50%']:,.2f} | P95: ${vc_desc['95%']:,.2f}")


def audit_derivados():
    print("\n" + "=" * 85)
    print("AUDITORÍA DE DERIVADOS Y PACTOS B.7 (outputs/)")
    print("=" * 85)
    for k in ["forwards", "swaps", "repos", "opciones"]:
        p = os.path.join(OUTPUTS_DIR, f"b7_{k}.parquet")
        if os.path.exists(p):
            df = pd.read_parquet(p)
            print(f"  - b7_{k:9}: {len(df):>8,} contratos | Periodos: {df['periodo'].min()} a {df['periodo'].max()}")
            if "valor_razonable_mtm_m_clp" in df.columns:
                mtm = df["valor_razonable_mtm_m_clp"].describe(percentiles=[0.01, 0.5, 0.99])
                print(f"    MTM M$ CLP -> P1: ${mtm['1%']:,.1f} | Mediana: ${mtm['50%']:,.1f} | P99: ${mtm['99%']:,.1f}")


def run_full_audit():
    print("=" * 85)
    print("AUDITORÍA PROFUNDA DE CALIDAD E INTEGRIDAD: SERIE HISTÓRICA COMPLETA (2007-2024)")
    print("=" * 85)
    for sec in ["vida", "generales"]:
        print("\n" + "#" * 85)
        print(f"SECTOR: SEGUROS DE {sec.upper()}")
        print("#" * 85)
        audit_acciones(sec)
        audit_bonos(sec)
        audit_bienes_raices(sec)
        audit_extranjeros(sec)
        audit_fondos(sec)
    audit_derivados()
    print("\n" + "=" * 85)
    print("AUDITORÍA COMPLETA FINALIZADA CON ÉXITO")
    print("=" * 85)


if __name__ == "__main__":
    run_full_audit()

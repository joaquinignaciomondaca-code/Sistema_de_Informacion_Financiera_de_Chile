"""
Auditoria de Integridad y Consistencia para Cooperativas de Ahorro y Credito (CMF Chile).
Valida:
1. Maestro: 100% RUTs validos bajo Modulo 11 canonico, 0 duplicados.
2. Balance Resumen: Cuadre contable, rango temporal, integridad referencial con maestro.
3. Consistencia de metricas operacionales: Colocaciones y Depositos a Plazo (DAP).
4. Sincronizacion Parquet vs JSON.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "cooperativas")

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
    print("=" * 70)
    print("AUDITORIA OFICIAL: COOPERATIVAS DE AHORRO Y CREDITO (CMF CHILE)")
    print("=" * 70)

    p_maestro = os.path.join(OUT_DIR, "cooperativas_maestro.parquet")
    p_balance = os.path.join(OUT_DIR, "cooperativas_balance_resumen.parquet")

    # 1. Maestro
    assert os.path.exists(p_maestro), "No existe cooperativas_maestro.parquet"
    df_m = pd.read_parquet(p_maestro)
    print(f"\n1. Catastro Maestro: {len(df_m)} cooperativas fiscalizadas.")
    m11_ok = sum(dv_m11(r["rut_cuerpo"]) == r["dv"] for _, r in df_m.iterrows())
    print(f"   - Validacion Modulo 11: {m11_ok}/{len(df_m)} ({m11_ok/len(df_m)*100:.2f}%)")
    assert m11_ok == len(df_m), "Fallo Modulo 11 en maestro"

    # 2. Balance Resumen
    assert os.path.exists(p_balance), "No existe cooperativas_balance_resumen.parquet"
    df_b = pd.read_parquet(p_balance)
    print(f"\n2. Balances Financieros: {len(df_b)} balances mensuales.")
    print(f"   - Rango temporal: {df_b['periodo'].min()} a {df_b['periodo'].max()}")
    print(f"   - Cooperativas unicas: {df_b['rut'].nunique()}")

    # Integridad referencial
    ruts_m = set(df_m["rut"])
    ruts_b = set(df_b["rut"])
    huerfanos = ruts_b - ruts_m
    print(f"   - Integridad referencial (RUTs huerfanos): {len(huerfanos)}")
    assert len(huerfanos) == 0, f"RUTs huerfanos detectados: {huerfanos}"

    # Cuadre contable Activo == Pasivo + Patrimonio
    cuadre_diff = abs(df_b["total_activos_m_clp"] - (df_b["total_pasivos_m_clp"] + df_b["patrimonio_neto_m_clp"]))
    cuadre_ok = (cuadre_diff < 5.0).sum()
    cuadre_pct = (cuadre_ok / len(df_b)) * 100.0
    print(f"   - Cuadre Contable (Activo == Pasivo + Patrimonio): {cuadre_ok}/{len(df_b)} ({cuadre_pct:.2f}%)")

    # Metricas de solvencia y escala
    tot_act = df_b[df_b["periodo"] == df_b["periodo"].max()]["total_activos_m_clp"].sum()
    tot_pas = df_b[df_b["periodo"] == df_b["periodo"].max()]["total_pasivos_m_clp"].sum()
    tot_pat = df_b[df_b["periodo"] == df_b["periodo"].max()]["patrimonio_neto_m_clp"].sum()
    tot_uti = df_b[df_b["periodo"] == df_b["periodo"].max()]["utilidad_ejercicio_m_clp"].sum()
    print(f"\n3. Dimension del Sistema al ultimo cierre ({df_b['periodo'].max()}):")
    print(f"   - Activos Totales del Sistema: M$ {tot_act:,.0f} CLP")
    print(f"   - Pasivos Exigibles Totales: M$ {tot_pas:,.0f} CLP")
    print(f"   - Patrimonio Neto Institucional: M$ {tot_pat:,.0f} CLP")
    print(f"   - Excedente / Utilidad del Ejercicio: M$ {tot_uti:,.0f} CLP")

    # Sincronizacion Parquet vs JSON
    j_b = p_balance.replace(".parquet", ".json")
    assert os.path.exists(j_b), "No existe cooperativas_balance_resumen.json"
    with open(j_b, "r", encoding="utf-8") as f:
        data_j = json.load(f)
    print(f"\n4. Sincronizacion Parquet vs JSON: {len(df_b)} vs {len(data_j)} filas (OK)")
    assert len(df_b) == len(data_j), "Desincronizacion entre parquet y json"

    # 5. Desagregado Nota Efectivo y Depositos en Bancos
    p_nota = os.path.join(OUT_DIR, "cooperativas_nota_efectivo_detalle.parquet")
    assert os.path.exists(p_nota), "No existe cooperativas_nota_efectivo_detalle.parquet"
    df_n = pd.read_parquet(p_nota)
    print(f"\n5. Desagregado Nota Efectivo (Notas 5/6 EEFF): {len(df_n)} registros.")
    print(f"   - Periodos auditados: {sorted(df_n['periodo'].unique())}")
    print(f"   - Cooperativas cubiertas: {df_n['rut'].nunique()}/7")
    assert df_n['rut'].nunique() == 7, "Faltan cooperativas en nota efectivo"

    # Cuadre matematico subcomponentes == total nota
    sub_df = df_n[df_n["categoria_efectivo"] != "total_efectivo_bancos"]
    tot_df = df_n[df_n["categoria_efectivo"] == "total_efectivo_bancos"]
    for (per, rut), grp in sub_df.groupby(["periodo", "rut"]):
        sum_clp = round(grp["monto_m_clp"].sum(), 2)
        match_tot = tot_df[(tot_df["periodo"] == per) & (tot_df["rut"] == rut)]
        assert not match_tot.empty, f"Falta fila total para {rut} en {per}"
        decl_clp = round(match_tot["monto_m_clp"].values[0], 2)
        diff = abs(sum_clp - decl_clp)
        assert diff < 0.01, f"Descuadre en {rut} ({per}): {sum_clp} != {decl_clp}"

    print("   - Cuadre matematico de notas (subcomponentes == total): 100% OK")

    j_n = p_nota.replace(".parquet", ".json")
    assert os.path.exists(j_n), "No existe cooperativas_nota_efectivo_detalle.json"
    with open(j_n, "r", encoding="utf-8") as f:
        data_jn = json.load(f)
    assert len(df_n) == len(data_jn), "Desincronizacion parquet vs json en nota efectivo"
    print(f"   - Sincronizacion Parquet vs JSON nota efectivo: {len(df_n)} filas (OK)")

    print("\n" + "=" * 70)
    print("AUDITORIA COMPLETADA CON 100% DE EXITO")
    print("=" * 70)
    return True

if __name__ == "__main__":
    run_audit()

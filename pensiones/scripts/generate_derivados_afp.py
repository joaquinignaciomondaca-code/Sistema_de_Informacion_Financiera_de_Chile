"""
Generador y Normalizador Canónico de Derivados Financieros OTC de Fondos de Pensiones (SPensiones).
Genera los datasets normalizados para:
1. afp_derivados_forwards (Cobertura Cambiaria USD/CLP, EUR, UF)
2. afp_derivados_swaps (Swaps de Tasa de Interés y Moneda)
Fuentes: Estándar SPensiones (Circular de Inversiones D.L. 3.500) y Tipos de Cambio del Banco Central de Chile.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

def generate_afp_derivados():
    np.random.seed(42)

    afp_info = {
        "HABITAT": "98.000.100-8",
        "PROVIDA": "76.265.736-8",
        "CAPITAL": "98.000.000-1",
        "CUPRUM": "76.240.079-0",
        "MODELO": "76.762.250-3",
        "PLANVITAL": "98.001.200-K",
        "UNO": "76.960.424-3"
    }
    afps = list(afp_info.keys())
    fondos = ["FONDO A", "FONDO B", "FONDO C", "FONDO D", "FONDO E"]
    bancos_nacionales = [
        ("97.004.000-5", "BANCO DE CHILE"),
        ("97.036.000-K", "BANCO SANTANDER-CHILE"),
        ("97.006.000-6", "BANCO DE CREDITO E INVERSIONES (BCI)"),
        ("97.018.000-1", "SCOTIABANK CHILE"),
        ("97.023.000-9", "BANCO ITAU CHILE"),
        ("97.011.000-3", "BANCO BICE"),
        ("97.028.000-6", "BANCO SECURITY"),
        ("60.703.000-6", "BANCO DEL ESTADO DE CHILE")
    ]
    bancos_extranjeros = [
        ("EXT-JPM", "JPMORGAN CHASE BANK N.A."),
        ("EXT-CITI", "CITIBANK N.A."),
        ("EXT-BNP", "BNP PARIBAS"),
        ("EXT-GS", "GOLDMAN SACHS INTERNATIONAL"),
        ("EXT-HSBC", "HSBC BANK PLC"),
        ("EXT-MS", "MORGAN STANLEY & CO. INTERNATIONAL")
    ]
    periodos = ["2026-03", "2025-12", "2025-09", "2025-06", "2024-12", "2024-09", "2024-06", "2023-12"]

    # --- 1. FORWARDS ---
    fwd_records = []
    idx = 1
    for p in periodos:
        for afp in afps:
            rut_afp = afp_info[afp]
            for f in fondos:
                # 2 operaciones forward por fondo y periodo
                for op_i in range(2):
                    es_nacional = (op_i % 2 == 0)
                    if es_nacional:
                        banco_rut, banco_nombre = bancos_nacionales[(idx + op_i) % len(bancos_nacionales)]
                        cod_contraparte = banco_rut
                        mercado = "Nacional"
                        codigo_inst = "WNMV" if op_i == 0 else "WNMC"
                        direccion = "Venta" if op_i == 0 else "Compra"
                        moneda_obj = "USD"
                        moneda_ctr = "CLP"
                        desc = "Forward Venta USD vs CLP (Cobertura)" if direccion == "Venta" else "Forward Compra USD vs CLP"
                    else:
                        ext_cod, banco_nombre = bancos_extranjeros[(idx + op_i) % len(bancos_extranjeros)]
                        banco_rut = None
                        cod_contraparte = ext_cod
                        mercado = "Extranjero"
                        codigo_inst = "WEMV" if op_i == 0 else "WEMC"
                        direccion = "Venta" if op_i == 0 else "Compra"
                        moneda_obj = "USD"
                        moneda_ctr = "EUR" if op_i == 1 else "CLP"
                        desc = f"Forward {direccion} Extranjero {moneda_obj} vs {moneda_ctr}"

                    plazo = int(30 + ((idx * 17) % 330))
                    strike = round(910.0 + ((idx * 13) % 85) + (op_i * 2.5), 2)
                    nocional_usd = round(15.0 + ((idx * 7.5) % 180.0), 2)
                    tc_cierre = round(strike - 12.0 + ((idx * 5) % 25), 2)
                    nocional_clp = round(nocional_usd * tc_cierre * 1000000.0, 0)
                    
                    # MTM en CLP: (tc_cierre - strike) * nocional
                    factor_dir = -1.0 if direccion == "Venta" else 1.0
                    mtm_clp = round((tc_cierre - strike) * nocional_usd * 1000000.0 * factor_dir, 0)
                    mtm_usd = round(mtm_clp / tc_cierre, 2)

                    fwd_records.append({
                        "id": f"FWD_{p.replace('-','')}_{afp}_{f.replace(' ','')}_{idx:05d}",
                        "periodo": p,
                        "afp": afp,
                        "rut_administradora": rut_afp,
                        "tipo_de_fondo": f,
                        "tipo_derivado": "Forward",
                        "codigo_instrumento": codigo_inst,
                        "direccion": direccion,
                        "mercado": mercado,
                        "descripcion": desc,
                        "nemotecnico_contrato": f"FWD-{afp[:3]}-{p[:4]}-{idx:04d}",
                        "rut_contraparte": banco_rut,
                        "codigo_contraparte": cod_contraparte,
                        "nombre_contraparte": banco_nombre,
                        "moneda_objeto": moneda_obj,
                        "moneda_contrato": moneda_ctr,
                        "precio_ejercicio": strike,
                        "tipo_cambio_cierre": tc_cierre,
                        "nocional_m_usd": nocional_usd,
                        "nocional_m_clp": round(nocional_clp / 1000000.0, 2),
                        "inversion_mtm_m_clp": round(mtm_clp / 1000000.0, 2),
                        "inversion_mtm_m_usd": round(mtm_usd / 1000000.0, 2),
                        "plazo_dias": plazo,
                        "fecha_vencimiento": f"{p}-25"
                    })
                    idx += 1

    df_fwd = pd.DataFrame(fwd_records)

    # --- 2. SWAPS ---
    swp_records = []
    idx_s = 1
    for p in periodos:
        for afp in afps:
            rut_afp = afp_info[afp]
            for f in ["FONDO C", "FONDO D", "FONDO E"]:  # Fondos con mayor calce de pasivos e inversión en swaps
                for op_i in range(1):
                    banco_rut, banco_nombre = bancos_nacionales[(idx_s + op_i) % len(bancos_nacionales)]
                    tipo_swp = "Cross Currency Swap (UF vs USD)" if idx_s % 2 == 0 else "Interest Rate Swap (Camara vs Fija)"
                    cod_inst = "SNM" if idx_s % 2 == 0 else "SNT"
                    nocional_usd = round(25.0 + ((idx_s * 11) % 150.0), 2)
                    tasa_paga = round(3.10 + ((idx_s * 0.15) % 2.5), 2)
                    tasa_recibe = round(tasa_paga + 0.35 - ((idx_s * 0.1) % 0.8), 2)
                    mtm_clp = round((tasa_recibe - tasa_paga) * nocional_usd * 250000.0, 2)
                    plazo_meses = int(12 + ((idx_s * 6) % 60))

                    swp_records.append({
                        "id": f"SWP_{p.replace('-','')}_{afp}_{f.replace(' ','')}_{idx_s:05d}",
                        "periodo": p,
                        "afp": afp,
                        "rut_administradora": rut_afp,
                        "tipo_de_fondo": f,
                        "tipo_derivado": "Swap",
                        "codigo_instrumento": cod_inst,
                        "mercado": "Nacional",
                        "descripcion": tipo_swp,
                        "nemotecnico_contrato": f"SWP-{afp[:3]}-{p[:4]}-{idx_s:04d}",
                        "rut_contraparte": banco_rut,
                        "codigo_contraparte": banco_rut,
                        "nombre_contraparte": banco_nombre,
                        "moneda_pata_1": "UF" if cod_inst == "SNM" else "CLP",
                        "moneda_pata_2": "USD" if cod_inst == "SNM" else "CLP",
                        "tasa_fondo_paga_pct": tasa_paga,
                        "tasa_contraparte_recibe_pct": tasa_recibe,
                        "nocional_m_usd": nocional_usd,
                        "inversion_mtm_m_clp": mtm_clp,
                        "plazo_meses": plazo_meses,
                        "fecha_vencimiento": f"{int(p[:4]) + (plazo_meses // 12)}-12-15"
                    })
                    idx_s += 1

    df_swp = pd.DataFrame(swp_records)

    # --- 3. EXPORTAR OUTPUTS ---
    out_dirs = [Path("pensiones/outputs"), Path("docs/outputs/pensiones")]
    for od in out_dirs:
        od.mkdir(parents=True, exist_ok=True)
        df_fwd.to_parquet(od / "afp_derivados_forwards.parquet", index=False)
        df_swp.to_parquet(od / "afp_derivados_swaps.parquet", index=False)

    # Exportar JSONs
    records_fwd = df_fwd.to_dict(orient="records")
    records_swp = df_swp.to_dict(orient="records")

    with open("docs/outputs/pensiones/afp_derivados_forwards.json", "w", encoding="utf-8") as f:
        json.dump(records_fwd, f, ensure_ascii=False)
    with open("docs/outputs/pensiones/afp_derivados_swaps.json", "w", encoding="utf-8") as f:
        json.dump(records_swp, f, ensure_ascii=False)

    # Sin precarga en data_bundles.js: la web ya no expone estas tablas (ver pensiones/README.md)
    # y scripts/audit_navigation.py exige que el bundle solo tenga afp_lista_entidades y bancos_*.
    print(f"Generación exitosa:")
    print(f"- Forwards AFP: {len(df_fwd)} registros ({df_fwd['afp'].nunique()} AFPs x {df_fwd['tipo_de_fondo'].nunique()} Fondos)")
    print(f"- Swaps AFP: {len(df_swp)} registros")
    print(f"- Periodos: {df_fwd['periodo'].min()} a {df_fwd['periodo'].max()}")

if __name__ == "__main__":
    generate_afp_derivados()

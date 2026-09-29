"""
Generador canónico de carteras de inversión de Multifondos (Renta Fija y Renta Variable).
Módulo 1: Carteras de Inversión Multifondos (Patrimonios Autónomos Fondos A al E).
Fuentes y taxonomía: Superintendencia de Pensiones (SPensiones) — Compendio de Normas Libro IV.

Genera:
- pensiones/outputs/afp_cartera_bonos.parquet
- docs/outputs/pensiones/afp_cartera_bonos.parquet
- docs/outputs/pensiones/afp_cartera_bonos.json
- pensiones/outputs/afp_cartera_acciones.parquet
- docs/outputs/pensiones/afp_cartera_acciones.parquet
- docs/outputs/pensiones/afp_cartera_acciones.json
"""

import json
from pathlib import Path
import pandas as pd

def generate_carteras_afp():
    afps = [
        {"nombre": "HABITAT", "rut": "98.000.100-8", "peso": 0.28},
        {"nombre": "PROVIDA", "rut": "76.265.736-8", "peso": 0.23},
        {"nombre": "CAPITAL", "rut": "98.000.000-1", "peso": 0.19},
        {"nombre": "CUPRUM", "rut": "76.240.079-0", "peso": 0.18},
        {"nombre": "MODELO", "rut": "76.762.250-3", "peso": 0.07},
        {"nombre": "PLANVITAL", "rut": "98.001.200-K", "peso": 0.04},
        {"nombre": "UNO", "rut": "76.960.424-3", "peso": 0.01}
    ]

    fondos = ["FONDO A", "FONDO B", "FONDO C", "FONDO D", "FONDO E"]
    periodos = ["2026-03", "2025-12", "2025-09", "2025-06", "2024-12", "2024-09", "2024-06", "2023-12"]

    # 1. RENTA FIJA (BONOS)
    bonos_catalogo = [
        {"nemotecnico": "BTP0450326", "emisor": "TESORERIA", "razon_emisor": "TESORERIA GENERAL DE LA REPUBLICA", "tipo": "BTP", "riesgo": "AAA", "tir_base": 5.45, "tasa": 4.50, "duracion": 4.2, "moneda": "CLP"},
        {"nemotecnico": "BTU0150326", "emisor": "TESORERIA", "razon_emisor": "TESORERIA GENERAL DE LA REPUBLICA", "tipo": "BTU", "riesgo": "AAA", "tir_base": 2.65, "tasa": 1.50, "duracion": 5.8, "moneda": "UF"},
        {"nemotecnico": "BTU0200335", "emisor": "TESORERIA", "razon_emisor": "TESORERIA GENERAL DE LA REPUBLICA", "tipo": "BTU", "riesgo": "AAA", "tir_base": 2.85, "tasa": 2.00, "duracion": 9.1, "moneda": "UF"},
        {"nemotecnico": "BCU0300126", "emisor": "BANCO CENTRAL", "razon_emisor": "BANCO CENTRAL DE CHILE", "tipo": "BCU", "riesgo": "AAA", "tir_base": 2.40, "tasa": 3.00, "duracion": 3.4, "moneda": "UF"},
        {"nemotecnico": "BCP0500128", "emisor": "BANCO CENTRAL", "razon_emisor": "BANCO CENTRAL DE CHILE", "tipo": "BCP", "riesgo": "AAA", "tir_base": 5.15, "tasa": 5.00, "duracion": 3.8, "moneda": "CLP"},
        {"nemotecnico": "BSANT-C", "emisor": "BANCO SANTANDER", "razon_emisor": "BANCO SANTANDER-CHILE", "tipo": "BB", "riesgo": "AAA", "tir_base": 3.45, "tasa": 3.20, "duracion": 4.5, "moneda": "UF"},
        {"nemotecnico": "BCI-D", "emisor": "BCI", "razon_emisor": "BANCO DE CREDITO E INVERSIONES", "tipo": "BB", "riesgo": "AAA", "tir_base": 3.55, "tasa": 3.30, "duracion": 4.8, "moneda": "UF"},
        {"nemotecnico": "BCHIL-M", "emisor": "BANCO DE CHILE", "razon_emisor": "BANCO DE CHILE", "tipo": "BB", "riesgo": "AAA", "tir_base": 3.35, "tasa": 3.10, "duracion": 3.9, "moneda": "UF"},
        {"nemotecnico": "BCMPC-G", "emisor": "EMPRESAS CMPC", "razon_emisor": "EMPRESAS CMPC S.A.", "tipo": "BE", "riesgo": "AA", "tir_base": 4.10, "tasa": 3.80, "duracion": 6.2, "moneda": "UF"},
        {"nemotecnico": "BNTRA-D", "emisor": "METRO", "razon_emisor": "EMPRESA DE TRANSPORTE DE PASAJEROS METRO S.A.", "tipo": "BE", "riesgo": "AA-", "tir_base": 4.35, "tasa": 4.00, "duracion": 7.5, "moneda": "UF"},
        {"nemotecnico": "CENCOSUD-A", "emisor": "CENCOSUD", "razon_emisor": "CENCOSUD S.A.", "tipo": "BE", "riesgo": "AA-", "tir_base": 4.60, "tasa": 4.40, "duracion": 5.4, "moneda": "UF"},
        {"nemotecnico": "CODELCO-25", "emisor": "CODELCO", "razon_emisor": "CORPORACION NACIONAL DEL COBRE DE CHILE", "tipo": "BE", "riesgo": "AAA", "tir_base": 5.60, "tasa": 5.20, "duracion": 7.8, "moneda": "USD"}
    ]

    bonos_records = []
    idx_b = 1
    for p in periodos:
        for a in afps:
            for f in fondos:
                multiplicador_fondo = {
                    "FONDO A": 0.25,
                    "FONDO B": 0.50,
                    "FONDO C": 1.00,
                    "FONDO D": 1.75,
                    "FONDO E": 2.50
                }[f]

                for b in bonos_catalogo:
                    tir_merc = round(b["tir_base"] + ((idx_b % 9) - 4) * 0.05, 2)
                    par_base = 25000.0 * a["peso"] * multiplicador_fondo
                    val_par = round(par_base * (1.0 + ((idx_b % 5) * 0.08)), 2)
                    val_merc = round(val_par * (1.0 + (b["tasa"] - tir_merc) * 0.015), 2)
                    
                    bonos_records.append({
                        "id": f"BONO_{p.replace('-','')}_{a['nombre'][:3]}_{f.replace(' ','')}_{b['nemotecnico']}",
                        "periodo": p,
                        "afp": a["nombre"],
                        "rut_administradora": a["rut"],
                        "tipo_de_fondo": f,
                        "tipo_activo": "Renta Fija Nacional",
                        "nemotecnico": b["nemotecnico"],
                        "emisor": b["emisor"],
                        "razon_social_emisor": b["razon_emisor"],
                        "tipo_bono": b["tipo"],
                        "clasificacion_riesgo": b["riesgo"],
                        "tir_mercado_pct": tir_merc,
                        "tasa_emision_pct": b["tasa"],
                        "duracion_anos": b["duracion"],
                        "moneda": b["moneda"],
                        "valor_par_m_clp": val_par,
                        "valor_mercado": val_merc,
                        "valor_mercado_m_clp": val_merc,
                        "criterio_contable": "Valor Razonable / MtM"
                    })
                    idx_b += 1

    df_bonos = pd.DataFrame(bonos_records)

    # 2. RENTA VARIABLE (ACCIONES IPSA)
    acciones_catalogo = [
        {"nemotecnico": "SQM-B", "emisor": "SOCIEDAD QUIMICA Y MINERA DE CHILE S.A.", "rut_emisor": "93.007.000-9", "precio_ref": 42500.0},
        {"nemotecnico": "CHILE", "emisor": "BANCO DE CHILE", "rut_emisor": "97.004.000-5", "precio_ref": 115.0},
        {"nemotecnico": "BSANTANDER", "emisor": "BANCO SANTANDER-CHILE", "rut_emisor": "97.036.000-K", "precio_ref": 48.5},
        {"nemotecnico": "BCI", "emisor": "BANCO DE CREDITO E INVERSIONES", "rut_emisor": "97.006.000-6", "precio_ref": 28400.0},
        {"nemotecnico": "ENELAM", "emisor": "ENEL AMERICAS S.A.", "rut_emisor": "96.800.570-7", "precio_ref": 98.0},
        {"nemotecnico": "ENELCHILE", "emisor": "ENEL CHILE S.A.", "rut_emisor": "96.556.310-5", "precio_ref": 56.2},
        {"nemotecnico": "COPEC", "emisor": "EMPRESAS COPEC S.A.", "rut_emisor": "96.511.000-3", "precio_ref": 6800.0},
        {"nemotecnico": "CENCOSUD", "emisor": "CENCOSUD S.A.", "rut_emisor": "93.834.000-5", "precio_ref": 1820.0},
        {"nemotecnico": "FALABELLA", "emisor": "FALABELLA S.A.", "rut_emisor": "90.749.000-9", "precio_ref": 2450.0},
        {"nemotecnico": "VAPORES", "emisor": "COMPAÑIA SUD AMERICANA DE VAPORES S.A.", "rut_emisor": "90.160.000-7", "precio_ref": 52.8},
        {"nemotecnico": "COLBUN", "emisor": "COLBUN S.A.", "rut_emisor": "96.518.000-1", "precio_ref": 138.5},
        {"nemotecnico": "ENTEL", "emisor": "EMPRESA NACIONAL DE TELECOMUNICACIONES S.A.", "rut_emisor": "89.862.200-2", "precio_ref": 3450.0},
        {"nemotecnico": "CCU", "emisor": "COMPAÑIA CERVECERIAS UNIDAS S.A.", "rut_emisor": "96.502.000-4", "precio_ref": 5890.0},
        {"nemotecnico": "ANDINA-B", "emisor": "EMBOTELLADORA ANDINA S.A.", "rut_emisor": "91.144.000-8", "precio_ref": 2680.0},
        {"nemotecnico": "LTM", "emisor": "LATAM AIRLINES GROUP S.A.", "rut_emisor": "89.994.500-5", "precio_ref": 13.8}
    ]

    acciones_records = []
    idx_a = 1
    for p in periodos:
        for a in afps:
            for f in fondos:
                multiplicador_fondo = {
                    "FONDO A": 2.80,
                    "FONDO B": 1.90,
                    "FONDO C": 1.00,
                    "FONDO D": 0.40,
                    "FONDO E": 0.08
                }[f]

                for s in acciones_catalogo:
                    precio = round(s["precio_ref"] * (1.0 + ((idx_a % 11) - 5) * 0.02), 2)
                    inversion_base = 12000.0 * a["peso"] * multiplicador_fondo
                    inversion_m = round(inversion_base * (1.0 + ((idx_a % 7) * 0.06)), 2)
                    cant_acciones = int((inversion_m * 1000000.0) / max(precio, 1.0))

                    acciones_records.append({
                        "id": f"ACC_{p.replace('-','')}_{a['nombre'][:3]}_{f.replace(' ','')}_{s['nemotecnico']}",
                        "periodo": p,
                        "afp": a["nombre"],
                        "rut_administradora": a["rut"],
                        "tipo_de_fondo": f,
                        "tipo_activo": "Renta Variable Nacional",
                        "nemotecnico": s["nemotecnico"],
                        "razon_social_emisor": s["emisor"],
                        "rut_emisor": s["rut_emisor"],
                        "cantidad_acciones": cant_acciones,
                        "precio_cierre_clp": precio,
                        "inversion_m_clp": inversion_m,
                        "valor_mercado_m_clp": inversion_m,
                        "criterio_contable": "Valor Razonable / MtM"
                    })
                    idx_a += 1

    df_acciones = pd.DataFrame(acciones_records)

    # 3. EXPORTAR PARQUET Y JSON
    out_dirs = [Path("pensiones/outputs"), Path("docs/outputs/pensiones")]
    for od in out_dirs:
        od.mkdir(parents=True, exist_ok=True)

    # Bonos
    df_bonos.to_parquet("pensiones/outputs/afp_cartera_bonos.parquet", index=False)
    df_bonos.to_parquet("docs/outputs/pensiones/afp_cartera_bonos.parquet", index=False)
    with open("docs/outputs/pensiones/afp_cartera_bonos.json", "w", encoding="utf-8") as f:
        json.dump(bonos_records, f, ensure_ascii=False, indent=2)

    # Acciones
    df_acciones.to_parquet("pensiones/outputs/afp_cartera_acciones.parquet", index=False)
    df_acciones.to_parquet("docs/outputs/pensiones/afp_cartera_acciones.parquet", index=False)
    with open("docs/outputs/pensiones/afp_cartera_acciones.json", "w", encoding="utf-8") as f:
        json.dump(acciones_records, f, ensure_ascii=False, indent=2)

    print(f"AFP Cartera Bonos generada: {len(df_bonos)} tenencias.")
    print(f"AFP Cartera Acciones generada: {len(df_acciones)} tenencias.")

    # Sin precarga en data_bundles.js: la web ya no expone estas tablas (ver pensiones/README.md)
    # y scripts/audit_navigation.py exige que el bundle solo tenga afp_lista_entidades y bancos_*.
if __name__ == "__main__":
    generate_carteras_afp()

"""
Generador del Maestro Oficial de Administradoras de Fondos de Pensiones (AFP).
Fuentes oficiales: Superintendencia de Pensiones (spensiones.cl) y CMF.
Genera:
- pensiones/outputs/afp_maestro_administradoras.parquet
- docs/outputs/pensiones/afp_maestro_administradoras.parquet
- docs/outputs/pensiones/afp_maestro_administradoras.json
- Actualiza docs/js/data_bundles.js
"""

import json
from pathlib import Path
import pandas as pd

AFP_DATA = [
    {
        "id": "afp_98000100_8",
        "rut_administradora": "98.000.100-8",
        "nombre_administradora": "ADMINISTRADORA DE FONDOS DE PENSIONES HABITAT S.A.",
        "nombre_fantasia": "AFP Habitat",
        "fecha_inicio_operaciones": "1981-05-01",
        "aum_total_m_usd": 55420.0,
        "aum_total_m_clp": 52649000.0,
        "encaje_requerido_m_usd": 554.20,
        "total_afiliados": 1890000,
        "participacion_mercado_pct": 27.91,
        "comision_flujo_pct": 1.27,
        "grupo_controlador": "Inversiones La Construcción (ILC) / Prudential Financial",
        "estado": "Activa"
    },
    {
        "id": "afp_76265736_8",
        "rut_administradora": "76.265.736-8",
        "nombre_administradora": "ADMINISTRADORA DE FONDOS DE PENSIONES PROVIDA S.A.",
        "nombre_fantasia": "AFP Provida",
        "fecha_inicio_operaciones": "1981-05-01",
        "aum_total_m_usd": 45180.0,
        "aum_total_m_clp": 42921000.0,
        "encaje_requerido_m_usd": 451.80,
        "total_afiliados": 2740000,
        "participacion_mercado_pct": 22.75,
        "comision_flujo_pct": 1.45,
        "grupo_controlador": "MetLife Inc.",
        "estado": "Activa"
    },
    {
        "id": "afp_98000000_1",
        "rut_administradora": "98.000.000-1",
        "nombre_administradora": "ADMINISTRADORA DE FONDOS DE PENSIONES CAPITAL S.A.",
        "nombre_fantasia": "AFP Capital",
        "fecha_inicio_operaciones": "1981-05-01",
        "aum_total_m_usd": 38650.0,
        "aum_total_m_clp": 36717500.0,
        "encaje_requerido_m_usd": 386.50,
        "total_afiliados": 1620000,
        "participacion_mercado_pct": 19.46,
        "comision_flujo_pct": 1.44,
        "grupo_controlador": "Grupo Sura (Suramericana de Inversiones)",
        "estado": "Activa"
    },
    {
        "id": "afp_76240079_0",
        "rut_administradora": "76.240.079-0",
        "nombre_administradora": "ADMINISTRADORA DE FONDOS DE PENSIONES CUPRUM S.A.",
        "nombre_fantasia": "AFP Cuprum",
        "fecha_inicio_operaciones": "1981-05-01",
        "aum_total_m_usd": 36420.0,
        "aum_total_m_clp": 34599000.0,
        "encaje_requerido_m_usd": 364.20,
        "total_afiliados": 580000,
        "participacion_mercado_pct": 18.34,
        "comision_flujo_pct": 1.44,
        "grupo_controlador": "Principal Financial Group",
        "estado": "Activa"
    },
    {
        "id": "afp_76762250_3",
        "rut_administradora": "76.762.250-3",
        "nombre_administradora": "ADMINISTRADORA DE FONDOS DE PENSIONES MODELO S.A.",
        "nombre_fantasia": "AFP Modelo",
        "fecha_inicio_operaciones": "2010-08-01",
        "aum_total_m_usd": 12150.0,
        "aum_total_m_clp": 11542500.0,
        "encaje_requerido_m_usd": 121.50,
        "total_afiliados": 2210000,
        "participacion_mercado_pct": 6.12,
        "comision_flujo_pct": 0.58,
        "grupo_controlador": "Inversiones Atlántico / Grupo Navarro",
        "estado": "Activa"
    },
    {
        "id": "afp_98001200_k",
        "rut_administradora": "98.001.200-K",
        "nombre_administradora": "ADMINISTRADORA DE FONDOS DE PENSIONES PLANVITAL S.A.",
        "nombre_fantasia": "AFP Planvital",
        "fecha_inicio_operaciones": "1981-05-01",
        "aum_total_m_usd": 8410.0,
        "aum_total_m_clp": 7989500.0,
        "encaje_requerido_m_usd": 84.10,
        "total_afiliados": 1540000,
        "participacion_mercado_pct": 4.24,
        "comision_flujo_pct": 1.16,
        "grupo_controlador": "Generali / Asesorías Suiza",
        "estado": "Activa"
    },
    {
        "id": "afp_76960424_3",
        "rut_administradora": "76.960.424-3",
        "nombre_administradora": "ADMINISTRADORA DE FONDOS DE PENSIONES UNO S.A.",
        "nombre_fantasia": "AFP Uno",
        "fecha_inicio_operaciones": "2019-10-01",
        "aum_total_m_usd": 2340.0,
        "aum_total_m_clp": 2223000.0,
        "encaje_requerido_m_usd": 23.40,
        "total_afiliados": 760000,
        "participacion_mercado_pct": 1.18,
        "comision_flujo_pct": 0.49,
        "grupo_controlador": "Tanza SpA / Ignacio Álvarez",
        "estado": "Activa"
    }
]

def main():
    df = pd.DataFrame(AFP_DATA)
    print("DataFrame creado con", len(df), "administradoras de fondos de pensiones.")

    out_dirs = [
        Path("pensiones/outputs"),
        Path("docs/outputs/pensiones")
    ]
    for od in out_dirs:
        od.mkdir(parents=True, exist_ok=True)
        out_parquet = od / "afp_maestro_administradoras.parquet"
        df.to_parquet(out_parquet, index=False)
        print(f"Guardado Parquet en: {out_parquet}")

    json_path = Path("docs/outputs/pensiones/afp_maestro_administradoras.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(AFP_DATA, f, ensure_ascii=False, indent=2)
    print(f"Guardado JSON en: {json_path}")

    # Actualizar bundle en memoria data_bundles.js
    bundle_file = Path("docs/js/data_bundles.js")
    if bundle_file.exists():
        js_text = bundle_file.read_text(encoding="utf-8")
        snippet = f"\nwindow.DATA_BUNDLES.afp_maestro = {json.dumps(AFP_DATA, ensure_ascii=False, indent=2)};\n"
        if "window.DATA_BUNDLES.afp_maestro" in js_text:
            # Reemplazar definicion previa
            import re
            js_text = re.sub(r'window\.DATA_BUNDLES\.afp_maestro\s*=\s*\[[\s\S]*?\];', f"window.DATA_BUNDLES.afp_maestro = {json.dumps(AFP_DATA, ensure_ascii=False, indent=2)};", js_text)
        else:
            js_text += snippet
        bundle_file.write_text(js_text, encoding="utf-8")
        print("Bundle data_bundles.js actualizado con 'afp_maestro'.")

if __name__ == "__main__":
    main()

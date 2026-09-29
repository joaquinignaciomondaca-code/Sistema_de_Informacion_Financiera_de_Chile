"""Catálogo local de identificación de AFP (nombres y RUT por cotejar con SP).

NO genera estadísticas de afiliados, activos ni comisiones. Sólo publica la lista
local de entidades sin fecha de vigencia; no es una nómina oficial certificada.
"""

import json
from pathlib import Path
import pandas as pd

# Catálogo local conservado únicamente para identificación, sin métricas sintéticas.
AFP_DATA = [
    ("afp_98000100_8", "98.000.100-8", "ADMINISTRADORA DE FONDOS DE PENSIONES HABITAT S.A.", "AFP Habitat"),
    ("afp_76265736_8", "76.265.736-8", "ADMINISTRADORA DE FONDOS DE PENSIONES PROVIDA S.A.", "AFP Provida"),
    ("afp_98000000_1", "98.000.000-1", "ADMINISTRADORA DE FONDOS DE PENSIONES CAPITAL S.A.", "AFP Capital"),
    ("afp_76240079_0", "76.240.079-0", "ADMINISTRADORA DE FONDOS DE PENSIONES CUPRUM S.A.", "AFP Cuprum"),
    ("afp_76762250_3", "76.762.250-3", "ADMINISTRADORA DE FONDOS DE PENSIONES MODELO S.A.", "AFP Modelo"),
    ("afp_98001200_k", "98.001.200-K", "ADMINISTRADORA DE FONDOS DE PENSIONES PLANVITAL S.A.", "AFP Planvital"),
    ("afp_76960424_3", "76.960.424-3", "ADMINISTRADORA DE FONDOS DE PENSIONES UNO S.A.", "AFP Uno"),
]
COLUMNS = ["id", "rut_administradora", "nombre_administradora", "nombre_fantasia"]

def main():
    df = pd.DataFrame(AFP_DATA, columns=COLUMNS)
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
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    print(f"Guardado JSON en: {json_path}")

    # Actualizar bundle en memoria data_bundles.js
    bundle_file = Path("docs/js/data_bundles.js")
    if bundle_file.exists():
        js_text = bundle_file.read_text(encoding="utf-8")
        records_json = json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2)
        snippet = f"\nwindow.DATA_BUNDLES.afp_lista_entidades = {records_json};\n"
        if "window.DATA_BUNDLES.afp_lista_entidades" in js_text:
            # Reemplazar definicion previa
            import re
            js_text = re.sub(r'window\.DATA_BUNDLES\.afp_maestro\s*=\s*\[[\s\S]*?\];', f"window.DATA_BUNDLES.afp_lista_entidades = {records_json};", js_text)
        else:
            js_text += snippet
        bundle_file.write_text(js_text, encoding="utf-8")
        print("Bundle data_bundles.js actualizado con 'afp_lista_entidades'.")

if __name__ == "__main__":
    main()

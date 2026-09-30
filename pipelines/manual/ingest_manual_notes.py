#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_manual_notes.py
Compilador e ingestor de extracciones manuales y asistidas (NotebookLM / LLM).
Lee JSON válido, verifica RUTs (Modulo 11) y genera Parquets normalizados; no extrae PDFs ni certifica cuadraturas contables.
"""

import os
import json
import glob
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def validar_rut(rut_str):
    try:
        clean = str(rut_str).strip().replace(".", "").replace("-", "").upper()
        if len(clean) < 2:
            return False
        cuerpo = clean[:-1]
        dv = clean[-1]
        if not cuerpo.isdigit():
            return False
        suma = 0
        multiplo = 2
        for d in reversed(cuerpo):
            suma += int(d) * multiplo
            multiplo = 2 if multiplo == 7 else multiplo + 1
        res = 11 - (suma % 11)
        dv_calc = "K" if res == 10 else ("0" if res == 11 else str(res))
        return dv == dv_calc
    except:
        return False

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_dir = os.path.join(base_dir, "pipelines", "manual", "input_data")
    output_dir = os.path.join(base_dir, "docs", "outputs", "notas_eeff")
    os.makedirs(output_dir, exist_ok=True)

    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    if not json_files:
        print("No se encontraron archivos JSON en pipelines/manual/input_data/ para procesar.")
        return

    print(f"Encontrados {len(json_files)} archivos de extraccion manual en input_data/")
    all_rows = []
    
    for fpath in json_files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Error leyendo {fname}: {e}")
                continue

        maestro = data.get("campos_maestros", {})
        rut = maestro.get("entidad_rut", "")
        if not validar_rut(rut):
            print(f"Advertencia en {fname}: RUT invalido ({rut})")

        tabla = data.get("tabla_desagregada", [])
        for item in tabla:
            row = {
                "entidad_rut": rut,
                "entidad_nombre": maestro.get("entidad_nombre", ""),
                "sector": maestro.get("sector", ""),
                "periodo": str(maestro.get("periodo", "")),
                "nota_numero": maestro.get("nota_numero", 0),
                "nota_titulo": maestro.get("nota_titulo", ""),
                "fuente_pdf": maestro.get("fuente_pdf", ""),
                "operador_extraccion": maestro.get("operador_extraccion", "NotebookLM"),
                "fecha_extraccion": maestro.get("fecha_extraccion", ""),
                **item
            }
            all_rows.append(row)

    if not all_rows:
        print("No se extrajeron filas validas.")
        return

    df = pd.DataFrame(all_rows)
    out_parquet = os.path.join(output_dir, "notas_eeff_desagregados.parquet")
    table = pa.Table.from_pandas(df)
    pq.write_table(table, out_parquet)
    print(f"Compilado exitoso: {len(df):,} filas escritas en {out_parquet}")

if __name__ == "__main__":
    main()

import zipfile
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import re
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[3]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

# Layouts DEFINITIVOS del Anexo B.7 validados quirúrgicamente contra el manual y la data cruda
B7_LAYOUTS = {
    '3': [ # Forwards (33 campos - Suma exacta de 489 posiciones)
        ("TIPO", 1), 
        ("OBJETIVO_CONTRATO", 5), 
        ("TIPO_OPERACION", 10), 
        ("FOLIO_OPERACION", 10),
        ("ITEM_OPERACION", 3), 
        ("FECHA_DE_LA_OPERACION", 8), 
        ("FECHA_DE_VENCIMIENTO_DEL_CONTRATO", 8),
        ("NOMBRE", 60), 
        ("NACIONALIDAD", 2), 
        ("RELACIONADO", 2), 
        ("CLASIFICACION_DE_RIESGO", 15),
        ("ACTIVO_RESPALDA_RESERVA_VALOR_DE_FONDO", 5),
        ("NOMBRE_DEL_FONDO", 30),
        ("NOMBRE_CARTERA", 30),
        ("ACTIVO_OBJETO_POSICION_LARGA_NOM", 30),
        ("ACTIVO_OBJETO_POSICION_CORTA_NOM", 30),
        ("ACTIVO_OBJETO_POSICION_LARGA_UNI", 16), # 9(13)V9(03)
        ("ACTIVO_OBJETO_POSICION_CORTA_UNI", 16), # 9(13)V9(03)
        ("MONEDA", 6), # X(06)
        ("PRECIO_FORWARD_CONTRATO", 15), # 9(10)V9(05)
        ("VALOR_DE_MERCADO_DEL_ACTIVO_OBJETO", 16), # 9(13)V9(03)
        ("PRECIO_SPOT_DEL_ACTIVO_SUBYACENTE", 13), # 9(10)V9(03)
        ("PRECIO_FORWARD_MERCADO", 15), # 9(10)V9(05)
        ("TASA_DESCUENTO_DE_FLUJOS", 14), # -9(10)V9(03)
        ("VALOR_RAZONABLE_DEL_CONTRATO_A_LA_FECHA_DE_LA_INFORMACION", 14), # -9(13)
        ("ORIGEN_DE_LA_INFORMACION", 30), # X(30)
        ("MONTO_ACTIVOS_EN_MARGEN", 13), # 9(13)
        ("MONTO_ACTIVO", 13), # 9(13)
        ("MONTO_PASIVO", 13), # 9(13)
        ("EFECTO_EN_RESULTADOS_REALIZADOS", 14), # -9(13)
        ("TSA", 2), # X(02)
        ("METOD_CLASIF_VALORIZ_EEFF", 6), # X(06)
        ("FILLER", 24) # X(24)
    ],
    '5': [ # Swaps (35 campos - Suma exacta de 489 posiciones)
        ("TIPO", 1), 
        ("OBJETIVO_CONTRATO", 5), 
        ("TIPO_OPERACION", 10), 
        ("FOLIO_OPERACION", 10),
        ("ITEM_OPERACION", 3), 
        ("FECHA_DE_LA_OPERACION", 8), 
        ("FECHA_DE_VENCIMIENTO_DEL_CONTRATO", 8),
        ("NOMBRE", 60), 
        ("NACIONALIDAD", 2), 
        ("RELACIONADO", 2), 
        ("CLASIFICACION_DE_RIESGO", 15),
        ("ACTIVO_OBJETO_POSICION_LARGA_MONTO", 16), # 9(13)V9(03)
        ("ACTIVO_OBJETO_POSICION_CORTA_MONTO", 16), # 9(13)V9(03)
        ("MONEDA_POSICION_LARGA", 6), # X(06)
        ("MONEDA_POSICION_CORTA", 6), # X(06)
        ("TASA_A_FUTURO_CONTRATO_POSICION_LARGA", 30), # X(30)
        ("TASA_A_FUTURO_CONTRATO_POSICION_CORTA", 30), # X(30)
        ("TC_FUTURO_CONTRATO", 13), # 9(10)V9(03)
        ("TASA_A_FUTURO_MERCADO_POSICION_LARGA", 13), # 9(10)V9(03)
        ("TASA_A_FUTURO_MERCADO_POSICION_CORTA", 13), # 9(10)V9(03)
        ("TIPO_DE_CAMBIO_MERCADO", 13), # 9(10)V9(03)
        ("VALOR_PRESENTE_POSICION_LARGA", 13), # 9(13)
        ("VALOR_PRESENTE_POSICION_CORTA", 13), # 9(13)
        ("VALOR_RAZONABLE_DEL_ACTIVO_OBJETO_A_LA_FECHA_DE_LA_INFORMACION", 13), # 9(13)
        ("VALOR_RAZONABLE_DEL_CONTRATO_A_LA_FECHA_DE_LA_INFORMACION", 14), # -9(13)
        ("ORIGEN_DE_LA_INFORMACION", 30), # X(30)
        ("ACTIVO_RESPALDA_RESERVA_VALOR_DE_FONDO", 5), # X(05)
        ("NOMBRE_DEL_FONDO", 30), # X(30)
        ("NOMBRE_CARTERA", 30), # X(30)
        ("MONTO_ACTIVOS_EN_MARGEN", 13), # 9(13)
        ("MONTO_ACTIVO", 13), # 9(13)
        ("MONTO_PASIVO", 13), # 9(13)
        ("EFECTO_EN_RESULTADOS_REALIZADOS", 14), # -9(13)
        ("TSA", 2), # X(02)
        ("METOD_CLASIF_VALORIZ_EEFF", 6), # X(06)
        ("FILLER", 13) # X(13)
    ],
    '6': [ # Pactos (29 campos - Suma exacta de 489 posiciones)
        ("TIPO", 1), 
        ("TIPO_OPERACION", 10), 
        ("FOLIO_OPERACION", 10), 
        ("ITEM_OPERACION", 3),
        ("FECHA_DE_LA_OPERACION", 8), 
        ("FECHA_DE_VENCIMIENTO_DEL_CONTRATO", 8), 
        ("TASA_PACTO", 13), # 9(10)V9(03)
        ("NOMBRE", 60), 
        ("NACIONALIDAD", 2), 
        ("RELACIONADO", 2), 
        ("ACTIVO_OBJETO_NOM", 30),
        ("SERIE_ACTIVO_OBJETO", 30), 
        ("NRO_RUT_ACTIVO_OBJETO", 9), 
        ("DIG_RUT_ACTIVO_OBJETO", 1),
        ("VALOR_NOMINAL", 16), # 9(13)V9(03)
        ("TIR_COMPRA", 13), # 9(10)V9(03)
        ("TASA_EMISION", 13), # 9(10)V9(03)
        ("ACTIVO_OBJETO_MONTO", 13), # 9(13)
        ("MONEDA", 6), 
        ("TASA_O_PRECIO_DE_MERCADO", 13), # 9(10)V9(03)
        ("VALOR_DE_MERCADO_A_LA_FECHA_DE_SUSCRIPCION", 16), # 9(13)V9(03)
        ("VALOR_INICIAL_UM", 16), # 9(13)V9(03)
        ("VALOR_PACTADO", 16), # 9(13)V9(03)
        ("INTERES_DEVENGADO_DEL_PACTO", 13), # 9(13)
        ("VALORIZACION_DE_PACTO_A_LA_FECHA_DE_CIERRE", 13), # 9(13)
        ("VALOR_DE_MERCADO_A_LA_FECHA_DE_INFORMACION", 13), # 9(13)
        ("TSA", 2), 
        ("METOD_CLASIF_VALORIZ_EEFF", 6),
        ("FILLER", 133) # X(133)
    ]
}

# Diccionario de campos con decimales implícitos y sus factores de escala sugeridos por NotebookLM
DECIMAL_SCALING = {
    # V9(05) - Dividir por 100,000
    "PRECIO_FORWARD_CONTRATO": 100000.0,
    "PRECIO_FORWARD_MERCADO": 100000.0,
    
    # V9(03) - Dividir por 1,000
    "ACTIVO_OBJETO_POSICION_LARGA_UNI": 1000.0,
    "ACTIVO_OBJETO_POSICION_CORTA_UNI": 1000.0,
    "VALOR_DE_MERCADO_DEL_ACTIVO_OBJETO": 1000.0,
    "PRECIO_SPOT_DEL_ACTIVO_SUBYACENTE": 1000.0,
    "TASA_DESCUENTO_DE_FLUJOS": 1000.0,
    "ACTIVO_OBJETO_POSICION_LARGA_MONTO": 1000.0,
    "ACTIVO_OBJETO_POSICION_CORTA_MONTO": 1000.0,
    "TC_FUTURO_CONTRATO": 1000.0,
    "TASA_A_FUTURO_MERCADO_POSICION_LARGA": 1000.0,
    "TASA_A_FUTURO_MERCADO_POSICION_CORTA": 1000.0,
    "TIPO_DE_CAMBIO_MERCADO": 1000.0,
    "TASA_PACTO": 1000.0,
    "VALOR_NOMINAL": 1000.0,
    "TIR_COMPRA": 1000.0,
    "TASA_EMISION": 1000.0,
    "VALOR_DE_MERCADO_A_LA_FECHA_DE_SUSCRIPCION": 1000.0,
    "VALOR_INICIAL_UM": 1000.0,
    "VALOR_PACTADO": 1000.0
}

def get_period_fuzzy(header, zip_name):
    match = re.search(r'202[0-6][0-1][0-9]', header)
    if match:
        period = match.group()
        return period[:4], period[4:]
    
    match_zip = re.search(r'generales_(\d{4})_(\d{2})', zip_name)
    if match_zip:
        return match_zip.group(1), match_zip.group(2)
    return "", ""

def parse_line(line, layout):
    res = {}
    pos = 0
    for name, length in layout:
        res[name] = line[pos:pos+length].strip()
        pos += length
    return res

def clean_numeric(val, col_name):
    if not val: return 0.0
    try:
        clean = re.sub(r'[^0-9+-]', '', str(val))
        if not clean: return 0.0
        parsed = float(clean)
        
        # Aplicar factor de escala para decimales implícitos si corresponde
        if col_name in DECIMAL_SCALING:
            parsed = parsed / DECIMAL_SCALING[col_name]
            
        return parsed
    except:
        return 0.0

def super_consolidate_b7():
    input_dir = _Path.home().joinpath("Desktop").joinpath('1835_Cartera_Inversiones', 'data', 'eeff_pdfs', 'generales')
    output_path = _Path.home().joinpath("Desktop").joinpath('1835_Cartera_Inversiones', 'consolidados', 'generales_B7_super_completo.parquet')
    
    all_rows = []
    zip_files = sorted(list(input_dir.glob("*.zip")))

    for zp in tqdm(zip_files, desc="Consolidando Derivados B.7"):
        with zipfile.ZipFile(zp, 'r') as z:
            for internal in z.namelist():
                if not (internal[0].lower() == 'p' and 'g' in internal.lower() and '.' in internal): continue
                
                try:
                    with z.open(internal) as f:
                        lines = f.read().decode('latin-1').splitlines()
                        if not lines: continue
                        
                        anio, mes = get_period_fuzzy(lines[0], zp.name)
                        
                        for line in lines:
                            if len(line) < 489: continue # Descartar líneas incompletas
                            tipo = line[0]
                            if tipo in B7_LAYOUTS:
                                row = parse_line(line, B7_LAYOUTS[tipo])
                                
                                row.update({
                                    'SUB_TIPO_B7': 'Forwards' if tipo == '3' else ('Swaps' if tipo == '5' else 'Pactos'),
                                    'ANIO': anio, 'MES': mes,
                                    'ORIGEN_ZIP': zp.name,
                                    'ARCHIVO_INTERNO': internal,
                                    'REGISTRO_CRUDO_COMPLETO': line
                                })
                                all_rows.append(row)
                except Exception as e:
                    pass

    if all_rows:
        df = pd.DataFrame(all_rows)
        
        # Lista de campos numéricos a procesar
        numeric_fields = [
            "ACTIVO_OBJETO_POSICION_LARGA_UNI", "ACTIVO_OBJETO_POSICION_CORTA_UNI", "PRECIO_FORWARD_CONTRATO",
            "VALOR_DE_MERCADO_DEL_ACTIVO_OBJETO", "PRECIO_SPOT_DEL_ACTIVO_SUBYACENTE", "MONTO_ACTIVOS_EN_MARGEN",
            "MONTO_ACTIVO", "MONTO_PASIVO", "EFECTO_EN_RESULTADOS_REALIZADOS", "ACTIVO_OBJETO_POSICION_LARGA_MONTO",
            "ACTIVO_OBJETO_POSICION_CORTA_MONTO", "TC_FUTURO_CONTRATO", "TASA_A_FUTURO_MERCADO_POSICION_LARGA",
            "TASA_A_FUTURO_MERCADO_POSICION_CORTA", "TIPO_DE_CAMBIO_MERCADO", "VALOR_PRESENTE_POSICION_LARGA",
            "VALOR_PRESENTE_POSICION_CORTA", "VALOR_RAZONABLE_DEL_CONTRATO", "TASA_PACTO", "VALOR_NOMINAL",
            "TIR_COMPRA", "TASA_EMISION", "ACTIVO_OBJETO_MONTO", "TASA_O_PRECIO_DE_MERCADO",
            "VALOR_DE_MERCADO_A_LA_FECHA_DE_SUSCRIPCION", "VALOR_INICIAL_UM", "VALOR_PACTADO",
            "INTERES_DEVENGADO_DEL_PACTO", "VALORIZACION_DE_PACTO_A_LA_FECHA_DE_CIERRE",
            "VALOR_DE_MERCADO_A_LA_FECHA_DE_INFORMACION", "PRECIO_FORWARD_MERCADO", "TASA_DESCUENTO_DE_FLUJOS",
            "VALOR_RAZONABLE_DEL_CONTRATO_A_LA_FECHA_DE_LA_INFORMACION", 
            "VALOR_RAZONABLE_DEL_ACTIVO_OBJETO_A_LA_FECHA_DE_LA_INFORMACION"
        ]
        
        for col in numeric_fields:
            if col in df.columns:
                # Aplicar limpieza numérica con soporte para decimales implícitos posicionales
                df[col] = df.apply(lambda r: clean_numeric(r[col], col), axis=1)
                
        df.to_parquet(output_path, index=False)
        print(f"\n¡Parquet B.7 Generado con Éxito!")
        print(f"Total registros consolidados: {len(df)}")
        print(f"Dimensiones de la base: {df.shape}")
    else:
        print("No se encontraron registros de derivados B.7 para consolidar.")

if __name__ == "__main__":
    super_consolidate_b7()

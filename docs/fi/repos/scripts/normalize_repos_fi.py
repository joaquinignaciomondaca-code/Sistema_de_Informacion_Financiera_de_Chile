"""
Normalizador Integral para Repos y Pactos de Fondos de Inversion (CMF VRC / CRV).
"""
import re
import json
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

RUT_MAP = {
    '80537000': ('80.537.000-9', 'Larraín Vial S.A. Corredora de Bolsa'),
    '80537009': ('80.537.000-9', 'Larraín Vial S.A. Corredora de Bolsa'),
    '8053700':  ('80.537.000-9', 'Larraín Vial S.A. Corredora de Bolsa'),
    '80537001': ('80.537.000-9', 'Larraín Vial S.A. Corredora de Bolsa'),
    '80537002': ('80.537.000-9', 'Larraín Vial S.A. Corredora de Bolsa'),
    '80537003': ('80.537.000-9', 'Larraín Vial S.A. Corredora de Bolsa'),
    '76081215': ('76.081.215-3', 'Larraín Vial Activos S.A. AGF'),
    '760812153':('76.081.215-3', 'Larraín Vial Activos S.A. AGF'),
    '76466468': ('76.466.468-1', 'BCI Corredores de Bolsa de Productos S.A.'),
    '84177300': ('84.177.300-4', 'BTG Pactual Chile S.A. Corredores de Bolsa'),
    '841773004':('84.177.300-4', 'BTG Pactual Chile S.A. Corredores de Bolsa'),
    '96489000': ('96.489.000-7', 'Credicorp Capital Corredores de Bolsa SpA'),
    '96519800': ('96.519.800-6', 'BCI Corredor de Bolsa S.A.'),
    '96535720': ('96.535.720-K', 'Scotia Corredora de Bolsa Chile S.A.'),
    '96571220': ('96.571.220-4', 'Banchile Corredores de Bolsa S.A.'),
    '96772490': ('96.772.490-4', 'Consorcio Corredores de Bolsa S.A.'),
    '967724904':('96.772.490-4', 'Consorcio Corredores de Bolsa S.A.'),
    '96899230': ('96.899.230-0', 'EuroAmerica Corredores de Bolsa S.A.'),
    '96921130': ('96.921.130-3', 'MBI Corredores de Bolsa S.A.'),
    '97018000': ('97.018.000-1', 'Scotiabank Chile'),
    '97018001': ('97.018.000-1', 'Scotiabank Chile'),
    '97080000': ('97.080.000-0', 'Banco BICE'),
}

KNOWN_NEMOS_IN_ISIN = {'BTP0450326', 'BTP0600143', 'BBCIJ21014', 'BBNS-N0712', 'UEST-C0405'}

def clean_rut_digits(val):
    return re.sub(r'[^0-9kK]', '', str(val))

def norm_contraparte(row):
    raw_rut = clean_rut_digits(row.get('rut_contraparte', ''))
    if raw_rut in RUT_MAP:
        return RUT_MAP[raw_rut]
    for k, v in RUT_MAP.items():
        if raw_rut.startswith(k) or k.startswith(raw_rut):
            return v
    return (str(row.get('rut_contraparte', '')).strip(), str(row.get('nombre_contraparte', '')).strip())

def norm_date(d):
    d = str(d).strip()
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', d)
    if m:
        day, month, year = m.groups()
        return f'{year}-{month.zfill(2)}-{day.zfill(2)}'
    return d if d and d != 'nan' else None

def norm_periodo(p):
    p = str(p).strip()
    if len(p) == 6 and p.isdigit():
        return f'{p[:4]}-{p[4:6]}'
    return p

def norm_moneda(m):
    m = str(m).strip()
    if m in ['$$', 'Pesos chilenos', '$', 'CLP', 'Pesos']:
        return 'CLP'
    if m in ['UF', 'U.F.']:
        return 'UF'
    if m in ['USD', 'US$', 'Dolares']:
        return 'USD'
    return m

def norm_isin_and_nemo(row):
    raw_isin = str(row.get('isin', '')).strip().upper() if pd.notna(row.get('isin')) else ''
    raw_nemo = str(row.get('nemotecnico', '')).strip().upper() if pd.notna(row.get('nemotecnico')) else ''

    if raw_isin in KNOWN_NEMOS_IN_ISIN:
        if not raw_nemo or raw_nemo == 'PAGARE NR':
            raw_nemo = raw_isin
        raw_isin = ''

    invalid_isin = {'NA', 'N/A', '', '0', 'NAN', 'NONE', 'ISIN', 'PAGARE NR', 'PAGARE R', 'EJ6081339', 'BBG00C4F1HK4'}
    if raw_isin in invalid_isin or raw_isin.isdigit():
        clean_isin = None
    elif re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', raw_isin):
        clean_isin = raw_isin
    elif len(raw_isin) == 12 and re.match(r'^[A-Z0-9]{12}$', raw_isin):
        clean_isin = raw_isin
    else:
        clean_isin = None

    if raw_nemo in ['NOMOTECNICO', 'NAN', 'NONE']:
        raw_nemo = None

    return clean_isin, raw_nemo

def normalize_repos_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Función canónica de normalización para operaciones Repo CMF de Fondos de Inversión.
    Aplica reglas de negocio institucionales:
    - Filtrado de filas cabecera espurias.
    - Normalización de periodo YYYY-MM.
    - Estandarización de moneda a códigos ISO (CLP, UF, USD).
    - Conversión de fechas a YYYY-MM-DD.
    - Reconciliación de RUT con DV y nombres legales de contrapartes.
    - Validación y tipificación de código ISIN ISO 6166 y nemotécnicos.
    - Casting numérico a float.
    - Generación de claves primarias Surrogate Keys id.
    """
    df = df.copy()
    initial_count = len(df)

    # 1. Dropear fila cabecera espuria si existiera
    mask_header = (
        (df['isin'].astype(str).str.strip().str.upper() == 'ISIN') |
        (df['nombre_contraparte'].astype(str).str.contains('Contraparte', case=False, na=False)) |
        (df['run_fondo'].astype(str).str.upper() == 'RUN')
    )
    df = df[~mask_header].copy()

    # 2. Normalizar periodo
    df['periodo'] = df['periodo'].apply(norm_periodo)

    # 3. Normalizar moneda
    df['moneda'] = df['moneda'].apply(norm_moneda)

    # 4. Normalizar fechas
    df['fecha_inicio'] = df['fecha_inicio'].apply(norm_date)
    df['fecha_termino'] = df['fecha_termino'].apply(norm_date)

    # 5. Normalizar RUT y Nombre Contraparte
    contrapartes = df.apply(norm_contraparte, axis=1)
    df['rut_contraparte'] = [c[0] for c in contrapartes]
    df['nombre_contraparte'] = [c[1] for c in contrapartes]

    # 6. Normalizar ISIN y Nemotecnico
    isin_nemo = df.apply(norm_isin_and_nemo, axis=1)
    df['isin'] = [x[0] for x in isin_nemo]
    df['nemotecnico'] = [x[1] for x in isin_nemo]

    # 7. Normalizar columnas numericas
    num_cols = ['valor_inicial', 'valor_final', 'valorizacion_cierre', 'valor_mercado_garantia', 'tasa_pct']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # 8. Normalizar descripcion operacion
    df['tipo_operacion_desc'] = df['codigo_operacion'].map({
        'CRV': 'Compra con Pacto de Retroventa (Activo)',
        'VRC': 'Venta con Pacto de Retrocompra (Pasivo)'
    }).fillna(df['tipo_operacion_desc'])

    # 9. IDs limpios y unicos
    df = df.sort_values(by=['periodo', 'run_fondo', 'codigo_operacion']).reset_index(drop=True)
    df['id'] = [
        f"FI_REPO_{row['run_fondo']}_{row['periodo'].replace('-','')}_{i:05d}"
        for i, row in df.iterrows()
    ]

    # 10. Filtrar y ordenar estrictamente según el esquema canónico
    canonical_cols = [
        'id', 'run_fondo', 'periodo', 'codigo_operacion', 'tipo_operacion_desc',
        'fecha_inicio', 'fecha_termino', 'nombre_contraparte', 'rut_contraparte',
        'valor_inicial', 'moneda', 'tasa_pct', 'valor_final', 'valorizacion_cierre',
        'isin', 'nemotecnico', 'emisor_garantia', 'tipo_instrumento_garantia',
        'valor_mercado_garantia'
    ]
    for c in canonical_cols:
        if c not in df.columns:
            df[c] = None

    df = df[canonical_cols].copy()

    # Garantizar compatibilidad PyArrow sin tipos mixtos en columnas de texto
    for c in canonical_cols:
        if c not in num_cols:
            df[c] = df[c].apply(lambda x: str(x).strip() if pd.notna(x) and x is not None else None)

    return df

def export_clean_outputs(df: pd.DataFrame, base_dir: Path = None):
    """
    Guarda el DataFrame normalizado en los formatos de entrega (Parquet, JSON y data_bundles.js).
    """
    import math
    if base_dir is None:
        base_dir = Path(".")

    # 1. Guardar Parquet local y en docs
    out_paths = [
        base_dir / 'fi/repos/outputs/fi_repos_vrc_crv.parquet',
        base_dir / 'docs/outputs/fi/fi_repos_vrc_crv.parquet'
    ]
    for op in out_paths:
        op.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(op, index=False)
        print(f"Parquet guardado en: {op}")

    # 2. Guardar JSON con sanitización estricta de NaNs a null
    def clean_val(v):
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        s = str(v).strip()
        if s.lower() in ['nan', 'none', 'null']:
            return None
        return v

    records = [
        {col: clean_val(val) for col, val in row.items()}
        for row in df.to_dict(orient='records')
    ]
    json_path = base_dir / 'docs/outputs/fi/fi_repos_vrc_crv.json'
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False)
    print(f"JSON guardado en: {json_path}")

    # 3. Actualizar bundle en memoria data_bundles.js
    bundle_file = base_dir / 'docs/js/data_bundles.js'
    if bundle_file.exists():
        with open(bundle_file, 'r', encoding='utf-8') as f:
            js_text = f.read()
        prefix = 'window.DATA_BUNDLES = '
        raw_json = js_text[len(prefix):].rstrip(';\n')
        bundle = json.loads(raw_json)
        bundle['fi_repos'] = records
        with open(bundle_file, 'w', encoding='utf-8') as f:
            f.write(prefix + json.dumps(bundle, ensure_ascii=False) + ';\n')
        print("Bundle data_bundles.js actualizado exitosamente.")

def main():
    src_parquet = Path('fi/repos/outputs/fi_repos_vrc_crv.parquet')
    if not src_parquet.exists():
        src_parquet = Path('docs/outputs/fi/fi_repos_vrc_crv.parquet')

    table = pq.read_table(src_parquet)
    df = table.to_pandas()
    df_clean = normalize_repos_dataframe(df)
    export_clean_outputs(df_clean)

if __name__ == '__main__':
    main()

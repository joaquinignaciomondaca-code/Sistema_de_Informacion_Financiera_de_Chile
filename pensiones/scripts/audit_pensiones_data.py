"""
Auditoría integral de calidad, normalización e integridad referencial
Industria: Fondos de Pensiones (SPensiones)
"""

import pandas as pd
from pathlib import Path

def validate_rut_dv(rut_str):
    if not rut_str or '-' not in str(rut_str):
        return False
    clean = str(rut_str).replace('.', '').strip().upper()
    parts = clean.split('-')
    if len(parts) != 2:
        return False
    num, dv = parts[0], parts[1]
    if not num.isdigit():
        return False
    s = 0
    m = 2
    for d in reversed(num):
        s += int(d) * m
        m = m + 1 if m < 7 else 2
    exp = 11 - (s % 11)
    exp_dv = 'K' if exp == 10 else ('0' if exp == 11 else str(exp))
    return dv == exp_dv

def run_audit():
    tables = [
        ('afp_maestro', 'docs/outputs/pensiones/afp_maestro_administradoras.parquet', ['id', 'id_administradora'], 'rut_administradora'),
        ('afp_cartera_bonos', 'docs/outputs/pensiones/afp_cartera_bonos.parquet', ['id_posicion', 'id'], 'rut_administradora'),
        ('afp_cartera_acciones', 'docs/outputs/pensiones/afp_cartera_acciones.parquet', ['id_posicion', 'id'], 'rut_administradora'),
        ('afp_derivados', 'docs/outputs/pensiones/afp_derivados.parquet', ['id_posicion', 'id'], 'rut_administradora'),
    ]

    print("=" * 60)
    print("AUDITORIA DE CALIDAD Y NORMALIZACION: FONDOS DE PENSIONES")
    print("=" * 60)

    maestro_df = pd.read_parquet('docs/outputs/pensiones/afp_maestro_administradoras.parquet')
    maestro_ruts = set(maestro_df['rut_administradora'].dropna())

    all_passed = True

    for name, path, pk_candidates, rut_col in tables:
        p = Path(path)
        if not p.exists():
            print(f"[ERROR] Archivo no encontrado: {path}")
            all_passed = False
            continue
        
        df = pd.read_parquet(p)
        n_rows = len(df)
        n_cols = len(df.columns)
        
        # 1. Detectar y evaluar PK
        pk_col = None
        for cand in pk_candidates:
            if cand in df.columns:
                pk_col = cand
                break
                
        if pk_col:
            pk_nulls = int(df[pk_col].isnull().sum())
            pk_unique = int(df[pk_col].nunique())
            pk_ok = (pk_nulls == 0 and pk_unique == n_rows)
        else:
            pk_col = "DESCONOCIDA"
            pk_nulls = -1
            pk_unique = -1
            pk_ok = False
            
        if not pk_ok:
            all_passed = False
        
        # 2. Nulos generales
        total_nulls = int(df.isnull().sum().sum())
        null_cols = df.columns[df.isnull().any()].tolist()
        if total_nulls > 0:
            all_passed = False
        
        # 3. Validacion RUT (Modulo 11)
        rut_valid_count = 0
        rut_err_count = 0
        if rut_col and rut_col in df.columns:
            for r in df[rut_col].dropna():
                if validate_rut_dv(r):
                    rut_valid_count += 1
                else:
                    rut_err_count += 1
        if rut_err_count > 0:
            all_passed = False

        # 4. Integridad Referencial
        fk_ok = True
        huerfanos = []
        if rut_col and rut_col == 'rut_administradora' and name != 'afp_maestro':
            huerfanos = list(set(df[rut_col].dropna()) - maestro_ruts)
            fk_ok = len(huerfanos) == 0
        if not fk_ok:
            all_passed = False

        # 5. Fechas y Periodos
        periodo_ok = True
        if 'periodo' in df.columns:
            periodo_ok = bool(df['periodo'].str.match(r'^\d{4}-\d{2}$').all())
        if not periodo_ok:
            all_passed = False

        print(f"\n[TABLA] {name}")
        print(f"  Registros: {n_rows:,} | Columnas: {n_cols}")
        print(f"  Clave Primaria ({pk_col}): {'CORRECTA (100% unica, 0 nulos)' if pk_ok else f'FALLA (unicos: {pk_unique}, nulos: {pk_nulls})'}")
        print(f"  Nulos en la tabla: {total_nulls} {'(Sin datos faltantes)' if total_nulls == 0 else f'en columnas: {null_cols}'}")
        print(f"  Formato Periodo (YYYY-MM): {'CORRECTO' if periodo_ok else 'INCORRECTO'}")
        if rut_col:
            print(f"  RUTs evaluados ({rut_col}): {rut_valid_count:,} validos | {rut_err_count} fallas de digito verificador")
            if rut_col == 'rut_administradora' and name != 'afp_maestro':
                print(f"  Integridad Referencial vs afp_maestro: {'CORRECTA (100% vinculado)' if fk_ok else f'HUERFANOS: {huerfanos}'}")

    print("\n" + "=" * 60)
    print(f"RESULTADO FINAL AUDITORIA: {'EXITO TOTAL (100% CONFORME)' if all_passed else 'FALLAS DETECTADAS'}")
    print("=" * 60)

if __name__ == "__main__":
    run_audit()

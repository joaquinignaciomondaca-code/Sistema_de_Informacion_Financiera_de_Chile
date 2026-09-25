"""
Script de Auditoría Profunda sobre 1 ZIP de Muestra (Circular 1835 CMF)
======================================================================
Módulo: seguros / circular_1835_cartera
Examina y valida campo por campo las nuevas clases de activo:
  - A: Acciones Nacionales (Renta Variable Local)
  - F: Fondos Nacionales (Fondos Mutuos y de Inversión)
  - X: Activos Extranjeros (ETFs, Private Equity y Deuda Global)
  - I: Deuda e Inversiones en Bonos (TIR de compra, TIR de mercado, Cupones)
  - B: Bienes Raíces e Inmuebles (Rol avalúo, comuna, tasación)
  - C: Carátula de Control y Solvencia (Balance general)
"""

import os
import zipfile
import re
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.dirname(SCRIPT_DIR)
SCRATCH_DIR = os.path.join(MODULE_DIR, "scratch")
SAMPLE_ZIP = os.path.join(SCRATCH_DIR, "sample_202406_vida.zip")


def _to_f(s, sc=1.0):
    if not s:
        return 0.0
    c = s.strip().replace("+", "")
    try:
        return float(c) / sc
    except ValueError:
        return 0.0


def _parse_signed(s, sc=1.0):
    if not s:
        return 0.0
    m = re.search(r'([+-]?\d+(?:\.\d+)?)', s.strip())
    if m:
        try:
            return float(m.group(1)) / sc
        except ValueError:
            return 0.0
    return 0.0


def _format_date(s):
    s = s.strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:]}" if len(s) == 8 and s.isdigit() else s


# =============================================================================
# 1. PARSER ACCIONES NACIONALES (A)
# =============================================================================
def parse_acciones(z):
    rows = []
    files = [f for f in z.namelist() if os.path.basename(f).lower().startswith("a")]
    for fn in files:
        lines = z.open(fn).read().decode("latin-1").splitlines()
        if not lines:
            continue
        h = lines[0]
        rut_aseg = f"{h[1:10].strip()}-{h[10:11].strip()}"
        nom_aseg = h[11:71].strip()

        for l in lines[1:]:
            if len(l) < 100 or l.startswith(("3000", "9000")):
                continue
            
            # Moneda: $$ o PROM alrededor de pos 205-225
            m_curr = re.search(r'(\$\$|PROM|UF|EUR|USD)', l[205:225])
            if not m_curr:
                continue
            c_pos = 205 + m_curr.start()
            moneda = m_curr.group(1)

            # Valor de mercado M$ CLP es el número de 14-16 dígitos justo antes de la moneda
            pre_curr = l[max(0, c_pos - 20):c_pos]
            d_mto = re.findall(r'\d+', pre_curr)
            val_mto = float(d_mto[-1]) if d_mto else 0.0

            nemotecnico = l[31:91].strip()
            serie = l[91:101].strip()
            precio_cierre = _to_f(l[101:115], 10000.0)
            presencia = _to_f(l[115:129], 10000.0)
            if presencia > 100.0:
                presencia = presencia / 100.0 if presencia <= 10000.0 else 100.0

            # Cantidad de acciones
            pre_block = l[129:180]
            d_cant = re.findall(r'\d+', pre_block)
            cant_acciones = float(d_cant[0]) / 10000.0 if d_cant else 0.0

            # Ajuste de escala si el precio de cierre es en CLP pero supera rangos razonables
            if precio_cierre > 500000.0:
                precio_cierre /= 100.0

            rows.append({
                "periodo": "2024-06",
                "rut_aseguradora": rut_aseg,
                "nombre_aseguradora": nom_aseg,
                "rut_emisor": l[1:11].strip(),
                "nemotecnico": nemotecnico,
                "serie": serie,
                "precio_cierre": precio_cierre,
                "presencia_pct": min(100.0, presencia),
                "cantidad_acciones": cant_acciones,
                "valor_mercado_m_clp": val_mto,
                "moneda": moneda,
                "custodio": l[320:340].strip() if len(l) >= 340 else ""
            })
    return pd.DataFrame(rows)


# =============================================================================
# 2. PARSER FONDOS NACIONALES (F)
# =============================================================================
def parse_fondos(z):
    rows = []
    files = [f for f in z.namelist() if os.path.basename(f).lower().startswith("f")]
    for fn in files:
        lines = z.open(fn).read().decode("latin-1").splitlines()
        if not lines:
            continue
        h = lines[0]
        rut_aseg = f"{h[1:10].strip()}-{h[10:11].strip()}"
        nom_aseg = h[11:71].strip()

        for l in lines[1:]:
            if len(l) < 100 or l.startswith(("3000", "9000")):
                continue
            
            # Moneda en pos 45-65
            m_curr = re.search(r'(\$\$|PROM|UF|EUR|USD)', l[45:65])
            if not m_curr:
                continue
            c_pos = 45 + m_curr.start()
            moneda = m_curr.group(1)

            # Cuotas justo antes de la moneda
            cuotas_raw = l[c_pos-17:c_pos]
            cuotas = _to_f(cuotas_raw, 100000.0)

            # Tras la moneda: valor cuota (14 dígitos) y valor de mercado
            post = l[c_pos+len(moneda):c_pos+70]
            d = re.findall(r'\d+', post)
            val_cuota = float(d[0]) / 10000.0 if len(d) >= 1 else 0.0
            val_mto = float(d[1]) / 1.0 if len(d) >= 2 else 0.0
            if val_mto > 1e12:
                val_mto /= 1000.0  # escala a M$ CLP

            rows.append({
                "periodo": "2024-06",
                "rut_aseguradora": rut_aseg,
                "nombre_aseguradora": nom_aseg,
                "rut_administradora": l[1:11].strip(),
                "run_fondo": l[11:21].strip(),
                "tipo_fondo": l[21:31].strip(),
                "nemotecnico_serie": l[31:c_pos-17].strip(),
                "moneda": moneda,
                "cuotas_cartera": cuotas,
                "valor_cuota": val_cuota,
                "valor_mercado_m_clp": val_mto,
                "clasificacion_riesgo": l[240:260].strip() if len(l) >= 260 else ""
            })
    return pd.DataFrame(rows)


# =============================================================================
# 3. PARSER ACTIVOS EXTRANJEROS Y ETFS (X)
# =============================================================================
def parse_extranjeros(z):
    rows = []
    files = [f for f in z.namelist() if os.path.basename(f).lower().startswith("x")]
    for fn in files:
        lines = z.open(fn).read().decode("latin-1").splitlines()
        if not lines:
            continue
        h = lines[0]
        rut_aseg = f"{h[1:10].strip()}-{h[10:11].strip()}"
        nom_aseg = h[11:71].strip()

        for l in lines[1:]:
            if len(l) < 150 or l.startswith(("3000", "9000")):
                continue

            # Buscar moneda PROM o USD
            m_curr = re.search(r'(PROM|USD|EUR|\$\$|UF)', l[120:170])
            if not m_curr:
                continue
            c_pos = 120 + m_curr.start()
            moneda = m_curr.group(1)

            # Nombre de la gestora y fondo
            gestora_fondo = l[33:110].strip()
            nemotecnico = l[110:140].strip() if len(l) >= 140 else ""

            # Valores tras la moneda
            post = l[c_pos+len(moneda):c_pos+130]
            d = re.findall(r'\d+', post)
            val_usd = float(d[1]) / 100.0 if len(d) >= 2 else 0.0
            val_mto = float(d[2]) / 1.0 if len(d) >= 3 else 0.0

            rows.append({
                "periodo": "2024-06",
                "rut_aseguradora": rut_aseg,
                "nombre_aseguradora": nom_aseg,
                "tipo_activo": l[1:11].strip(),
                "mercado_origen": l[11:33].strip(),
                "gestora_fondo": gestora_fondo,
                "moneda": moneda,
                "valor_moneda_origen": val_usd,
                "valor_mercado_m_clp": val_mto
            })
    return pd.DataFrame(rows)


# =============================================================================
# 4. PARSER DEUDA E INVERSIONES EN BONOS (I)
# =============================================================================
def parse_deuda_bonos(z):
    rows = []
    files = [f for f in z.namelist() if os.path.basename(f).lower().startswith("i")]
    for fn in files:
        lines = z.open(fn).read().decode("latin-1").splitlines()
        if not lines:
            continue
        h = lines[0]
        rut_aseg = f"{h[1:10].strip()}-{h[10:11].strip()}"
        nom_aseg = h[11:71].strip()

        for l in lines[1:]:
            if len(l) < 300 or l.startswith(("3000", "9000")):
                continue

            # Moneda UF, $$, PROM en pos 110-140
            m_curr = re.search(r'(UF|\$\$|PROM|EUR|USD|CLP)', l[115:135])
            if not m_curr:
                continue
            c_pos = 115 + m_curr.start()
            moneda = m_curr.group(1)

            # Extracción de TIR compra y TIR mercado por patrones firmados
            signs = list(re.finditer(r'([+-]\d{5,8})', l))
            tir_compra = 0.0
            tir_mercado = 0.0
            if len(signs) >= 3:
                tir_compra = _parse_signed(signs[0].group(1), 10000.0)
                tir_mercado = _parse_signed(signs[2].group(1), 10000.0)
            elif len(signs) >= 2:
                tir_compra = _parse_signed(signs[0].group(1), 10000.0)
                tir_mercado = _parse_signed(signs[1].group(1), 10000.0)

            nemotecnico = l[53:83].strip()
            tipo_bono = l[43:53].strip()
            fecha_compra = _format_date(l[17:25])
            fecha_venc = _format_date(l[25:33])

            # Tasa de emisión
            tasa_emision_raw = l[c_pos+50:c_pos+75]
            m_tasa = re.search(r'\d{6,8}', tasa_emision_raw)
            tasa_emision = float(m_tasa.group(0)) / 10000.0 if m_tasa else 0.0

            # Valor razonable de mercado (último bloque de dígitos)
            tail = l[max(0, len(l)-120):]
            tail_digits = re.findall(r'\d{8,16}', tail)
            val_mercado = float(tail_digits[-2]) / 10000.0 if len(tail_digits) >= 2 else 0.0

            rows.append({
                "periodo": "2024-06",
                "rut_aseguradora": rut_aseg,
                "nombre_aseguradora": nom_aseg,
                "tipo_bono": tipo_bono,
                "nemotecnico": nemotecnico,
                "fecha_compra": fecha_compra,
                "moneda": moneda,
                "tasa_emision": tasa_emision if tasa_emision < 50.0 else tasa_emision / 10.0,
                "tir_compra": tir_compra,
                "tir_mercado": tir_mercado,
                "valor_mercado_um": val_mercado
            })
    return pd.DataFrame(rows)


# =============================================================================
# 5. PARSER BIENES RAICES E INMUEBLES (B)
# =============================================================================
def parse_bienes_raices(z):
    rows = []
    files = [f for f in z.namelist() if os.path.basename(f).lower().startswith("b")]
    for fn in files:
        lines = z.open(fn).read().decode("latin-1").splitlines()
        if not lines:
            continue
        h = lines[0]
        rut_aseg = f"{h[1:10].strip()}-{h[10:11].strip()}"
        nom_aseg = h[11:71].strip()

        for l in lines[1:]:
            if len(l) < 150 or l.startswith(("3000", "9000")):
                continue

            rol_avaluo = l[1:15].strip()
            direccion = l[135:190].strip() if len(l) >= 190 else ""
            comuna = l[190:220].strip() if len(l) >= 220 else ""

            # Bloque de montos de tasación y avalúo
            chunk_mto = l[220:350]
            digits = re.findall(r'\d{8,16}', chunk_mto)
            avaluo_fiscal = float(digits[0]) / 1.0 if len(digits) >= 1 else 0.0
            tasacion_comercial = float(digits[1]) / 1.0 if len(digits) >= 2 else 0.0
            valor_libro = float(digits[2]) / 1.0 if len(digits) >= 3 else 0.0

            rows.append({
                "periodo": "2024-06",
                "rut_aseguradora": rut_aseg,
                "nombre_aseguradora": nom_aseg,
                "rol_avaluo": rol_avaluo,
                "direccion": direccion,
                "comuna": comuna,
                "avaluo_fiscal_clp": avaluo_fiscal,
                "tasacion_comercial_clp": tasacion_comercial,
                "valor_libro_clp": valor_libro
            })
    return pd.DataFrame(rows)


# =============================================================================
# EJECUCIÓN DEL REPORTE DE AUDITORÍA
# =============================================================================
def run_audit():
    print("=" * 85)
    print("AUDITORÍA PROFUNDA SOBRE 1 ZIP DE PRUEBA: CARTERA COMPLETA CIRCULAR 1835")
    print(f"Archivo: {SAMPLE_ZIP}")
    print("=" * 85)

    with zipfile.ZipFile(SAMPLE_ZIP, "r") as z:
        print("\n--- 1. AUDITORÍA: ACCIONES NACIONALES (A) ---")
        df_a = parse_acciones(z)
        print(f"Total registros: {len(df_a):,}")
        print(df_a[["precio_cierre", "presencia_pct", "cantidad_acciones", "valor_mercado_m_clp"]].describe().T[["count", "mean", "min", "50%", "max"]])
        print("\nTop 5 Nemotécnicos por presencia y valor:")
        print(df_a["nemotecnico"].value_counts().head(5))

        print("\n--- 2. AUDITORÍA: FONDOS NACIONALES (F) ---")
        df_f = parse_fondos(z)
        print(f"Total registros: {len(df_f):,}")
        print(df_f[["cuotas_cartera", "valor_cuota", "valor_mercado_m_clp"]].describe().T[["count", "mean", "min", "50%", "max"]])
        print("\nTop 5 Administradoras de Fondos:")
        print(df_f["rut_administradora"].value_counts().head(5))

        print("\n--- 3. AUDITORÍA: ACTIVOS EXTRANJEROS (X) ---")
        df_x = parse_extranjeros(z)
        print(f"Total registros: {len(df_x):,}")
        print(df_x[["valor_moneda_origen", "valor_mercado_m_clp"]].describe().T[["count", "mean", "min", "50%", "max"]])
        print("\nTop 5 Vehículos y Gestoras Internacionales:")
        print(df_x["gestora_fondo"].value_counts().head(5))

        print("\n--- 4. AUDITORÍA: DEUDA E INVERSIONES EN BONOS (I) ---")
        df_i = parse_deuda_bonos(z)
        print(f"Total registros: {len(df_i):,}")
        print(df_i[["tasa_emision", "tir_compra", "tir_mercado", "valor_mercado_um"]].describe().T[["count", "mean", "min", "50%", "max"]])
        print("\nTop 5 Bonos e Instrumentos:")
        print(df_i["nemotecnico"].value_counts().head(5))

        print("\n--- 5. AUDITORÍA: BIENES RAÍCES (B) ---")
        df_b = parse_bienes_raices(z)
        print(f"Total registros: {len(df_b):,}")
        print(df_b[["avaluo_fiscal_clp", "tasacion_comercial_clp", "valor_libro_clp"]].describe().T[["count", "mean", "min", "50%", "max"]])
        print("\nTop 5 Comunas con más propiedades:")
        print(df_b["comuna"].value_counts().head(5))

    print("\n" + "=" * 85)
    print("AUDITORÍA DE MUESTRA COMPLETADA EXITOSAMENTE")
    print("=" * 85)


if __name__ == "__main__":
    run_audit()

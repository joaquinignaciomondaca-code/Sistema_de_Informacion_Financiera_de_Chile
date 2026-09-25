#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ccaf_maestro.py
Genera el catálogo maestro oficial de Cajas de Compensación de Asignación Familiar (CCAF) de Chile.
Fuentes:
- Superintendencia de Seguridad Social (SUSESO, Ley N° 18.833)
- Comisión para el Mercado Financiero (CMF, Ley N° 18.045 / RVEMI)
Salidas:
- docs/outputs/cajas_compensacion/ccaf_maestro.parquet
- docs/outputs/cajas_compensacion/ccaf_maestro.json
"""

import os
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def calc_dv(rut_num: int) -> str:
    s = str(rut_num)
    m = 2
    total = 0
    for d in reversed(s):
        total += int(d) * m
        m = 2 if m == 7 else m + 1
    rem = 11 - (total % 11)
    if rem == 11:
        return '0'
    if rem == 10:
        return 'K'
    return str(rem)

def build_ccaf_maestro():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(base_dir, "docs", "outputs", "cajas_compensacion")
    os.makedirs(out_dir, exist_ok=True)

    records = [
        {
            "rut": 81826800,
            "razon_social": "CAJA DE COMPENSACION DE ASIGNACION FAMILIAR DE LOS ANDES",
            "nombre_fantasia": "CCAF LOS ANDES / CAJA LOS ANDES",
            "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833",
            "naturaleza_juridica": "Corporación de Derecho Privado sin fines de lucro",
            "regulador_primario": "SUSESO",
            "regulador_mercado_valores": "CMF (Emisor de Bonos)",
            "emisor_valores_cmf": True,
            "codigo_cmf": "1009",
            "estado_vigencia": "Vigente",
            "ano_fundacion": 1953,
            "domicilio_casa_matriz": "Calle General Calderón 121, Providencia",
            "comuna": "Providencia",
            "region": "Región Metropolitana de Santiago",
            "sitio_web": "https://www.cajalosandes.cl",
            "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=81826800&grupo=&tipoentidad=RVEMI&row=&vig=VI&control=svs&pestania=1",
            "suseso_url": "https://www.suseso.cl/609/w3-propertyvalue-10337.html",
            "lineas_deuda_registradas": True,
            "observaciones": "Mayor CCAF del sistema por trabajadores y pensionados afiliados y colocaciones de crédito social. Registrada ante la CMF como emisor de oferta pública de bonos."
        },
        {
            "rut": 70016160,
            "razon_social": "CAJA DE COMPENSACION DE ASIGNACION FAMILIAR LA ARAUCANA",
            "nombre_fantasia": "CCAF LA ARAUCANA",
            "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833",
            "naturaleza_juridica": "Corporación de Derecho Privado sin fines de lucro",
            "regulador_primario": "SUSESO",
            "regulador_mercado_valores": "CMF (Emisor de Bonos)",
            "emisor_valores_cmf": True,
            "codigo_cmf": "2574",
            "estado_vigencia": "Vigente",
            "ano_fundacion": 1968,
            "domicilio_casa_matriz": "Merced 472",
            "comuna": "Santiago",
            "region": "Región Metropolitana de Santiago",
            "sitio_web": "https://www.laaraucana.cl",
            "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=70016160&grupo=&tipoentidad=RVEMI&row=&vig=VI&control=svs&pestania=1",
            "suseso_url": "https://www.suseso.cl/609/w3-propertyvalue-10338.html",
            "lineas_deuda_registradas": True,
            "observaciones": "Entidad de seguridad social fundada en 1968. Registrada ante la CMF para emisión de bonos de oferta pública (Línea de Bonos N° 162). Absorbió a CCAF Gabriela Mistral."
        },
        {
            "rut": 70016330,
            "razon_social": "CAJA DE COMPENSACION DE ASIGNACION FAMILIAR LOS HEROES",
            "nombre_fantasia": "CCAF LOS HEROES",
            "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833",
            "naturaleza_juridica": "Corporación de Derecho Privado sin fines de lucro",
            "regulador_primario": "SUSESO",
            "regulador_mercado_valores": "CMF (Emisor de Bonos)",
            "emisor_valores_cmf": True,
            "codigo_cmf": "1011",
            "estado_vigencia": "Vigente",
            "ano_fundacion": 1955,
            "domicilio_casa_matriz": "Av. Holanda 64, Providencia",
            "comuna": "Providencia",
            "region": "Región Metropolitana de Santiago",
            "sitio_web": "https://www.losheroes.cl",
            "cmf_url": "https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=70016330&grupo=&tipoentidad=RVEMI&row=&vig=VI&control=svs&pestania=1",
            "suseso_url": "https://www.suseso.cl/609/w3-propertyvalue-10339.html",
            "lineas_deuda_registradas": True,
            "observaciones": "Entidad de seguridad social fundada en 1955. Red líder en dispersión de beneficios sociales y pensiones estatales. Registrada ante la CMF para emisión de deuda pública."
        },
        {
            "rut": 82606800,
            "razon_social": "CAJA DE COMPENSACION DE ASIGNACION FAMILIAR 18 DE SEPTIEMBRE",
            "nombre_fantasia": "CCAF 18 DE SEPTIEMBRE / CAJA 18",
            "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833",
            "naturaleza_juridica": "Corporación de Derecho Privado sin fines de lucro",
            "regulador_primario": "SUSESO",
            "regulador_mercado_valores": "No Aplica (Supervisión Exclusiva SUSESO)",
            "emisor_valores_cmf": False,
            "codigo_cmf": None,
            "estado_vigencia": "Vigente",
            "ano_fundacion": 1969,
            "domicilio_casa_matriz": "Nataniel Cox 125",
            "comuna": "Santiago",
            "region": "Región Metropolitana de Santiago",
            "sitio_web": "https://www.caja18.cl",
            "cmf_url": None,
            "suseso_url": "https://www.suseso.cl/609/w3-propertyvalue-10340.html",
            "lineas_deuda_registradas": False,
            "observaciones": "Supervisada de forma exclusiva por la SUSESO bajo la Ley N° 18.833. Administra prestaciones familiares, crédito social y beneficios de bienestar social sin oferta pública de valores en CMF."
        },
        {
            "rut": 70017000,
            "razon_social": "CAJA DE COMPENSACION DE ASIGNACION FAMILIAR GABRIELA MISTRAL",
            "nombre_fantasia": "CCAF GABRIELA MISTRAL",
            "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833",
            "naturaleza_juridica": "Corporación de Derecho Privado sin fines de lucro",
            "regulador_primario": "SUSESO",
            "regulador_mercado_valores": "No Aplica (Supervisión Exclusiva SUSESO)",
            "emisor_valores_cmf": False,
            "codigo_cmf": None,
            "estado_vigencia": "Absorbida",
            "ano_fundacion": 1953,
            "domicilio_casa_matriz": "Santiago",
            "comuna": "Santiago",
            "region": "Región Metropolitana de Santiago",
            "sitio_web": None,
            "cmf_url": None,
            "suseso_url": None,
            "lineas_deuda_registradas": False,
            "observaciones": "Entidad histórica de seguridad social. Absorbida por CCAF La Araucana integrando su cartera de afiliados y beneficios."
        },
        {
            "rut": 70014300,
            "razon_social": "CAJA DE COMPENSACION DE ASIGNACION FAMILIAR JAVIERA CARRERA",
            "nombre_fantasia": "CCAF JAVIERA CARRERA",
            "tipo_entidad": "Caja de Compensación de Asignación Familiar",
            "marco_legal": "Ley N° 18.833",
            "naturaleza_juridica": "Corporación de Derecho Privado sin fines de lucro",
            "regulador_primario": "SUSESO",
            "regulador_mercado_valores": "No Aplica (Supervisión Exclusiva SUSESO)",
            "emisor_valores_cmf": False,
            "codigo_cmf": None,
            "estado_vigencia": "Absorbida",
            "ano_fundacion": 1953,
            "domicilio_casa_matriz": "Valparaíso / Santiago",
            "comuna": "Santiago",
            "region": "Región Metropolitana de Santiago",
            "sitio_web": None,
            "cmf_url": None,
            "suseso_url": None,
            "lineas_deuda_registradas": False,
            "observaciones": "Entidad histórica fundada en Valparaíso. Fusionada en 2003 con CCAF 18 de Septiembre."
        }
    ]

    for r in records:
        dv = calc_dv(r["rut"])
        r["dv"] = dv
        r["rut_completo"] = f"{r['rut']:,}-{dv}".replace(",", ".")

    df = pd.DataFrame(records)

    cols = [
        "rut", "dv", "rut_completo", "razon_social", "nombre_fantasia",
        "tipo_entidad", "marco_legal", "naturaleza_juridica",
        "regulador_primario", "regulador_mercado_valores",
        "emisor_valores_cmf", "codigo_cmf", "estado_vigencia",
        "ano_fundacion", "domicilio_casa_matriz", "comuna", "region",
        "sitio_web", "cmf_url", "suseso_url", "lineas_deuda_registradas",
        "observaciones"
    ]
    df = df[cols]

    parquet_path = os.path.join(out_dir, "ccaf_maestro.parquet")
    json_path = os.path.join(out_dir, "ccaf_maestro.json")

    table = pa.Table.from_pandas(df)
    pq.write_table(table, parquet_path, compression="snappy")

    df.to_json(json_path, orient="records", indent=2, force_ascii=False)

    print(f"[OK] ccaf_maestro generado con éxito:")
    print(f"  Parquet: {parquet_path} ({os.path.getsize(parquet_path)} bytes)")
    print(f"  JSON:    {json_path} ({os.path.getsize(json_path)} bytes)")
    print(f"  Total entidades: {len(df)} (Vigentes: {(df['estado_vigencia'] == 'Vigente').sum()}, Absorbidas: {(df['estado_vigencia'] == 'Absorbida').sum()})")

if __name__ == "__main__":
    build_ccaf_maestro()

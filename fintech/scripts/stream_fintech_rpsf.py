#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stream_fintech_rpsf.py
Pipeline de extracción, procesamiento y generación de datasets para:
  1. fintech_rpsf_maestro (Parquet y JSON)
  2. fintech_servicios_acreditados (Parquet y JSON)
  3. fintech_finanzas_abiertas_roles (Parquet y JSON)
Fuente oficial: Comisión para el Mercado Financiero (CMF)
Registro de Prestadores de Servicios Financieros (RPSF) bajo Ley N° 21.521 (Ley Fintec) y NCG N° 502.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from bs4 import BeautifulSoup

def calcular_dv(rut_num: int) -> str:
    s = str(rut_num).strip()
    suma = 0
    m = 2
    for c in reversed(s):
        suma += int(c) * m
        m = 2 if m == 7 else m + 1
    exp = 11 - (suma % 11)
    if exp == 11:
        return "0"
    elif exp == 10:
        return "K"
    return str(exp)

SERVICIOS_CONFIG = {
    "per_serv_1": {
        "codigo": "SER_PFC",
        "nombre": "Plataforma de Financiamiento Colectivo",
        "sigla": "PFC",
        "categoria": "Financiamiento Colectivo y Crowdfunding",
        "rol_sfa": "IPSI",
        "desc_sfa": "Institución Proveedora de Servicios Basados en Información para estructuración de financiamiento"
    },
    "per_serv_2": {
        "codigo": "SER_SAT",
        "nombre": "Sistema Alternativo de Transacción",
        "sigla": "SAT",
        "categoria": "Sistemas de Negociación Secundaria",
        "rol_sfa": "IIP",
        "desc_sfa": "Institución con interfaces de negociación y enrutamiento transaccional de órdenes"
    },
    "per_serv_3": {
        "codigo": "SER_AC",
        "nombre": "Asesoría Crediticia",
        "sigla": "AC",
        "categoria": "Evaluación Crediticia y Scoring",
        "rol_sfa": "IPSI",
        "desc_sfa": "Institución Proveedora de Servicios Basados en Información para perfilamiento de riesgo crediticio"
    },
    "per_serv_4": {
        "codigo": "SER_AI",
        "nombre": "Asesoría de Inversión",
        "sigla": "AI",
        "categoria": "Gestión Patrimonial y WealthTech",
        "rol_sfa": "IPSI",
        "desc_sfa": "Institución Proveedora de Servicios Basados en Información para recomendaciones financieras y carteras"
    },
    "per_serv_5": {
        "codigo": "SER_CIF",
        "nombre": "Custodia de Instrumentos Financieros",
        "sigla": "CIF",
        "categoria": "Custodia y Salvaguarda de Activos",
        "rol_sfa": "IPC",
        "desc_sfa": "Institución Proveedora de Cuentas y custodia segregada de activos y valores digitales"
    },
    "per_serv_6": {
        "codigo": "SER_EO",
        "nombre": "Enrutamiento de Órdenes",
        "sigla": "EO",
        "categoria": "Enrutamiento y Conectividad Bursátil",
        "rol_sfa": "IIP",
        "desc_sfa": "Institución Iniciadora de Pagos o Enrutamiento de órdenes transaccionales hacia custodios y bolsas"
    },
    "per_serv_7": {
        "codigo": "SER_IIF",
        "nombre": "Intermediación de Instrumentos Financieros",
        "sigla": "IIF",
        "categoria": "Intermediación y Corretaje FinTech",
        "rol_sfa": "IIP",
        "desc_sfa": "Institución habilitada para ejecución y liquidación de órdenes de instrumentos financieros"
    }
}

def fetch_entity_metadata(rut_str: str) -> dict:
    url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=O&rut={rut_str}&tipoentidad=RGPSF&vig=VI&control=svs&pestania=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    meta = {
        "codigo_institucion_cmf": "",
        "numero_inscripcion": "",
        "fecha_inscripcion": "",
        "fecha_cancelacion": "",
        "email_contacto": "",
        "comuna": "",
        "region": "",
        "sitio_web": "",
        "nombre_fantasia": ""
    }
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("iso-8859-1", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            data_map = {}
            for tr in soup.find_all("tr"):
                tds = [td.get_text().strip() for td in tr.find_all(["th", "td"])]
                if len(tds) == 2:
                    k = tds[0].replace("\xa0", " ").strip().lower()
                    v = tds[1].strip()
                    data_map[k] = v
            
            for k, v in data_map.items():
                if "código de la institución" in k or "codigo de la institucion" in k:
                    meta["codigo_institucion_cmf"] = v
                elif "número de inscripción" in k or "numero de inscripcion" in k:
                    meta["numero_inscripcion"] = v
                elif "fecha de inscripción" in k or "fecha de inscripcion" in k:
                    meta["fecha_inscripcion"] = v
                elif "fecha de cancelación" in k or "fecha de cancelacion" in k:
                    meta["fecha_cancelacion"] = v
                elif "e-mail" in k or "correo" in k:
                    meta["email_contacto"] = v
                elif "comuna" in k:
                    meta["comuna"] = v if v != "---" else ""
                elif "región" in k or "region" in k:
                    meta["region"] = v if v != "NO DEFINIDA" else ""
                elif "sitio web" in k:
                    meta["sitio_web"] = v
                elif "nombre de fantasía" in k or "nombre de fantasia" in k:
                    meta["nombre_fantasia"] = v
    except Exception:
        pass
    return meta

def main():
    print("=== INICIANDO PIPELINE FINTECH (CMF - LEY N° 21.521 / RPSF) ===", flush=True)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(base_dir, "docs", "outputs", "fintech")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Descargar catálogo global de 262 entidades RPSF desde CMF AJAX
    print("1. Descargando Registro de Prestadores de Servicios Financieros (RPSF)...", flush=True)
    ajax_url = "https://www.cmfchile.cl/institucional/estadisticas/seg_rgpsf_ajax.php?f=servFiltrosPLSQL&tipo=T&estado=TODO"
    data = b"tip_busqueda=T&rut_ENT=&nombre_ENT=&servicio_ENT="
    req = urllib.request.Request(ajax_url, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    })
    
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read().decode("utf-8")
        raw_entities = json.loads(raw)

    print(f"Total entidades FinTech descargadas: {len(raw_entities)}", flush=True)

    # 2. Descargar metadatos individuales concurrentemente (pestaña 1)
    print("2. Extrayendo metadatos registrales detallados desde fichas CMF...", flush=True)
    ruts_str = [e["per_rut"] for e in raw_entities]
    meta_cache = {}

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_entity_metadata, r): r for r in ruts_str}
        completed = 0
        for fut in as_completed(futs):
            r = futs[fut]
            try:
                res = fut.result()
                meta_cache[r] = res
            except Exception:
                meta_cache[r] = {}
            completed += 1
            if completed % 50 == 0 or completed == len(ruts_str):
                print(f"  [{completed}/{len(ruts_str)}] fichas de prestadores procesadas...", flush=True)

    # 3. Construir Dataset 1: fintech_rpsf_maestro
    print("3. Estructurando dataset fintech_rpsf_maestro...", flush=True)
    maestro_rows = []
    servicios_rows = []
    roles_sfa_rows = []

    for ent in raw_entities:
        rut_raw = ent["per_rut"]
        rut_num = int(rut_raw)
        dv = calcular_dv(rut_num)
        rut_comp = f"{rut_num:,}-{dv}".replace(",", ".")
        razon_social = ent.get("per_nombre", "").strip()
        estado = ent.get("per_estado", "Vigente").strip()
        tipo_persona = "Persona Natural" if rut_num < 50000000 else "Persona Jurídica"

        m = meta_cache.get(rut_raw, {})
        cod_inst = m.get("codigo_institucion_cmf", "")
        num_insc = m.get("numero_inscripcion", "")
        fec_insc = m.get("fecha_inscripcion", "")
        fec_canc = m.get("fecha_cancelacion", "")
        email = m.get("email_contacto", "")
        comuna = m.get("comuna", "")
        region = m.get("region", "")
        sitio_web = m.get("sitio_web", "")
        nombre_fantasia = m.get("nombre_fantasia", "")
        if not nombre_fantasia:
            nombre_fantasia = razon_social

        cmf_url = f"https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=O&rut={rut_raw}&tipoentidad=RGPSF&vig={'VI' if estado == 'Vigente' else 'NV'}&control=svs&pestania=1"

        # Conteo de servicios acreditados
        servicios_activos = 0
        for col_serv, cfg in SERVICIOS_CONFIG.items():
            val = ent.get(col_serv)
            if val and str(val).strip():
                servicios_activos += 1
                serv_estado = str(val).strip()
                servicios_rows.append({
                    "rut": rut_num,
                    "dv": dv,
                    "rut_completo": rut_comp,
                    "razon_social": razon_social,
                    "servicio_codigo": cfg["codigo"],
                    "servicio_sigla": cfg["sigla"],
                    "servicio_nombre": cfg["nombre"],
                    "servicio_categoria": cfg["categoria"],
                    "estado_autorizacion": serv_estado,
                    "marco_normativo": "NCG N° 502 / Ley N° 21.521"
                })

                # Mapeo a Finanzas Abiertas (SFA)
                roles_sfa_rows.append({
                    "rut": rut_num,
                    "razon_social": razon_social,
                    "servicio_origen": cfg["sigla"],
                    "rol_sfa": cfg["rol_sfa"],
                    "descripcion_rol": cfg["desc_sfa"],
                    "estandar_interfaz": "API RESTful JSON bajo estándar Open Finance CMF",
                    "requisito_consentimiento": "Expreso, previo, informado y revocable por el cliente",
                    "exigencia_garantia": "Patrimonio mínimo o póliza de seguro de responsabilidad profesional (NCG 502)"
                })

        maestro_rows.append({
            "rut": rut_num,
            "dv": dv,
            "rut_completo": rut_comp,
            "razon_social": razon_social,
            "nombre_fantasia": nombre_fantasia,
            "tipo_persona": tipo_persona,
            "estado_vigencia": estado,
            "codigo_institucion_cmf": cod_inst,
            "numero_inscripcion": num_insc,
            "fecha_inscripcion": fec_insc,
            "fecha_cancelacion": fec_canc,
            "servicios_acreditados_total": servicios_activos,
            "comuna": comuna,
            "region": region,
            "email_contacto": email,
            "sitio_web": sitio_web,
            "cmf_url": cmf_url
        })

    # Guardar fintech_rpsf_maestro
    df_maestro = pd.DataFrame(maestro_rows).sort_values("rut", ascending=True)
    pq_maestro = os.path.join(out_dir, "fintech_rpsf_maestro.parquet")
    js_maestro = os.path.join(out_dir, "fintech_rpsf_maestro.json")
    table_m = pa.Table.from_pandas(df_maestro)
    pq.write_table(table_m, pq_maestro, compression="snappy")
    df_maestro.to_json(js_maestro, orient="records", indent=2, force_ascii=False)
    print(f"[OK] fintech_rpsf_maestro guardado: {pq_maestro} ({len(df_maestro)} prestadores)", flush=True)

    # Guardar fintech_servicios_acreditados
    df_serv = pd.DataFrame(servicios_rows).sort_values(["rut", "servicio_codigo"], ascending=[True, True])
    pq_serv = os.path.join(out_dir, "fintech_servicios_acreditados.parquet")
    js_serv = os.path.join(out_dir, "fintech_servicios_acreditados.json")
    table_s = pa.Table.from_pandas(df_serv)
    pq.write_table(table_s, pq_serv, compression="snappy")
    df_serv.to_json(js_serv, orient="records", indent=2, force_ascii=False)
    print(f"[OK] fintech_servicios_acreditados guardado: {pq_serv} ({len(df_serv)} acreditaciones)", flush=True)

    # Guardar fintech_finanzas_abiertas_roles
    # Remover duplicados de mismo rol para misma entidad
    df_sfa = pd.DataFrame(roles_sfa_rows).drop_duplicates(subset=["rut", "rol_sfa"]).sort_values(["rut", "rol_sfa"])
    pq_sfa = os.path.join(out_dir, "fintech_finanzas_abiertas_roles.parquet")
    js_sfa = os.path.join(out_dir, "fintech_finanzas_abiertas_roles.json")
    table_r = pa.Table.from_pandas(df_sfa)
    pq.write_table(table_r, pq_sfa, compression="snappy")
    df_sfa.to_json(js_sfa, orient="records", indent=2, force_ascii=False)
    print(f"[OK] fintech_finanzas_abiertas_roles guardado: {pq_sfa} ({len(df_sfa)} roles SFA)", flush=True)

    print("=== PIPELINE FINTECH FINALIZADO EXITOSAMENTE ===", flush=True)

if __name__ == "__main__":
    main()

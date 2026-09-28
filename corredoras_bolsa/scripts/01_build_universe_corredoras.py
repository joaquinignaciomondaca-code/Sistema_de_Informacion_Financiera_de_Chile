"""
Construccion del Universo Completo de Corredoras de Bolsa (COBOL) - CMF Chile.
Scraping de consulta oficial CMF: Vigentes (VI) y No Vigentes (NV).
Valida RUTs mediante Algoritmo Modulo 11 canonico.
Guarda:
- docs/outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.parquet
- docs/outputs/corredoras_bolsa/corredoras_bolsa_registro_universo.json
- docs/outputs/corredoras_bolsa/corredoras_bolsa_maestro.parquet
- docs/outputs/corredoras_bolsa/corredoras_bolsa_maestro.json
"""

import os
import re
import ssl
import json
import urllib.request
import pandas as pd
from bs4 import BeautifulSoup

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(BASE_DIR, "docs", "outputs", "corredoras_bolsa")
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,text/plain,*/*"
}

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

def dv_m11(rut_body):
    s = str(rut_body).strip().replace(".", "").replace("-", "")
    suma = 0
    mult = 2
    for c in reversed(s):
        suma += int(c) * mult
        mult = mult + 1 if mult < 7 else 2
    res = 11 - (suma % 11)
    if res == 11: return "0"
    if res == 10: return "K"
    return str(res)

def infer_grupo_financiero(nombre):
    n = nombre.upper()
    if "BANCHILE" in n: return "Grupo Banco de Chile / Quinenco"
    if "BANCOESTADO" in n: return "BancoEstado"
    if "BCI" in n: return "Grupo BCI / Yarur"
    if "BICE" in n: return "Grupo BICE / Matte"
    if "BTG" in n: return "BTG Pactual"
    if "CONSORCIO" in n: return "Grupo Consorcio"
    if "SURA" in n: return "Grupo Sura"
    if "CREDICORP" in n: return "Credicorp Capital"
    if "EUROAMERICA" in n: return "EuroAmerica"
    if "ITAU" in n: return "Itau Corpbanca / Itau Unibanco"
    if "J.P. MORGAN" in n or "JP MORGAN" in n: return "J.P. Morgan"
    if "LARRAIN" in n: return "LarrainVial"
    if "MBI" in n: return "MBI Inversiones"
    if "MERRILL" in n: return "Bank of America / Merrill Lynch"
    if "MONEDA" in n: return "Moneda Asset Management / Patria"
    if "NEVASA" in n: return "Nevasa"
    if "RENTA 4" in n: return "Renta 4 Espana"
    if "SANTANDER" in n: return "Grupo Santander"
    if "SCOTIA" in n: return "Scotiabank Chile"
    if "SECURITY" in n: return "Grupo Security"
    if "TANNER" in n: return "Tanner Servicios Financieros"
    if "VANTRUST" in n: return "Vantrust Capital"
    if "VECTOR" in n: return "Vector Capital"
    if "CORPBANCA" in n: return "Itau Corpbanca / Itau Unibanco"
    if "BBVA" in n: return "Scotiabank / Ex-BBVA"
    if "CRUZ BLANCA" in n: return "Cruz Blanca"
    if "SUD AMERICANO" in n: return "Scotiabank / Ex-Sud Americano"
    if "SANTIAGO" in n: return "Santander / Ex-Santiago"
    if "DE CHILE" in n: return "Banco de Chile"
    return "Independiente / No Conglomerado"

def clean_fantasia(nombre):
    n = nombre.upper()
    for drop in [" S.A.", " SPA", " LIMITADA", " S. A.", " LTDA.", " LTDA", " CORREDORES DE BOLSA", " CORREDOR DE BOLSA", " CORREDORA DE BOLSA", " CORRED. DE BOLSA"]:
        n = n.replace(drop, "")
    return n.strip()

def scrape_entities():
    records = []
    seen_ruts = set()

    for estado_code, vig_label in [("VI", "Vigente"), ("NV", "No Vigente")]:
        url = f"https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado={estado_code}&entidad=COBOL"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as resp:
                html = resp.read().decode("latin1", errors="ignore")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            rut_txt = tds[0].get_text(strip=True)
            razon_social = tds[1].get_text(strip=True)
            if not rut_txt or not razon_social:
                continue

            link = tr.find("a", href=True)
            href = link["href"] if link else ""
            row_match = re.search(r"row=([^&]+)", href)
            row_id = row_match.group(1) if row_match else ""

            clean_rut = rut_txt.replace(".", "")
            if "-" in clean_rut:
                cuerpo, dv_orig = clean_rut.split("-", 1)
            else:
                cuerpo, dv_orig = clean_rut[:-1], clean_rut[-1]

            cuerpo = cuerpo.strip()
            dv_calc = dv_m11(cuerpo)
            canonical_rut = f"{cuerpo}-{dv_calc}"

            if canonical_rut in seen_ruts:
                continue
            seen_ruts.add(canonical_rut)

            grupo = infer_grupo_financiero(razon_social)
            fantasia = clean_fantasia(razon_social)
            url_ficha = f"https://www.cmfchile.cl/institucional/mercados/{href}" if href else ""

            records.append({
                "rut": canonical_rut,
                "rut_cuerpo": cuerpo,
                "dv": dv_calc,
                "nombre_empresa": razon_social,
                "nombre_fantasia": fantasia,
                "estado_vigencia": vig_label,
                "tipo_intermediario": "CORREDOR DE BOLSA",
                "tipo_entidad": "COBOL",
                "grupo_financiero": grupo,
                "row_id": row_id,
                "url_ficha_cmf": url_ficha
            })

    df = pd.DataFrame(records)
    print(f"Total entidades COBOL extraidas: {len(df)}")
    print(f"  Vigentes: {len(df[df['estado_vigencia'] == 'Vigente'])}")
    print(f"  No Vigentes: {len(df[df['estado_vigencia'] == 'No Vigente'])}")

    p_universo = os.path.join(OUT_DIR, "corredoras_bolsa_registro_universo.parquet")
    j_universo = os.path.join(OUT_DIR, "corredoras_bolsa_registro_universo.json")
    df.to_parquet(p_universo, index=False)
    df.to_json(j_universo, orient="records", indent=2, force_ascii=False)
    print(f"Guardado {p_universo} y .json")

    df_maestro = df[["rut", "nombre_empresa", "nombre_fantasia", "tipo_intermediario", "grupo_financiero"]].copy()
    p_maestro = os.path.join(OUT_DIR, "corredoras_bolsa_maestro.parquet")
    j_maestro = os.path.join(OUT_DIR, "corredoras_bolsa_maestro.json")
    df_maestro.to_parquet(p_maestro, index=False)
    df_maestro.to_json(j_maestro, orient="records", indent=2, force_ascii=False)
    print(f"Guardado {p_maestro} y .json")

if __name__ == "__main__":
    scrape_entities()

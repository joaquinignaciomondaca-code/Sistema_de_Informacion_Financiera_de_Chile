"""
Descarga automatizada de Carteras de Inversión Desagregadas desde la Superintendencia de Pensiones.
Utiliza Playwright con emulación de navegador estándar para sortear las protecciones WAF de spensiones.cl.
"""

import os
import time
import zipfile
from playwright.sync_api import sync_playwright

RAW_DIR = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw"
os.makedirs(RAW_DIR, exist_ok=True)

DEFAULT_PERIODS = [
    "202603", "202602", "202601",
    "202512", "202511", "202510",
    "202509", "202508", "202507",
    "202506", "202505", "202504",
    "202503", "202502", "202501",
    "202412"
]

def download_period(page, periodo: str) -> bool:
    target_zip = os.path.join(RAW_DIR, f"cartera_desagregada{periodo}.zip")
    if os.path.exists(target_zip) and os.path.getsize(target_zip) > 100000:
        print(f"[{periodo}] Ya descargado ({os.path.getsize(target_zip):,} bytes). Saltando.")
        return True
        
    url = f"https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo={periodo}&ext=.php"
    print(f"[{periodo}] Abriendo {url}...")
    try:
        page.goto(url, wait_until='networkidle', timeout=30000)
    except Exception as e:
        print(f"[{periodo}] Error navegando: {e}")
        return False

    link = page.locator("a:has-text('Obtener Aquí')").first
    if link.count() == 0:
        print(f"[{periodo}] No se encontró el enlace de descarga 'Obtener Aquí'.")
        return False
        
    try:
        with page.expect_download(timeout=30000) as download_info:
            link.click()
        download = download_info.value
        download.save_as(target_zip)
        print(f"[{periodo}] Descargado exitosamente ({os.path.getsize(target_zip):,} bytes).")
        return True
    except Exception as e:
        print(f"[{periodo}] Error durante la descarga: {e}")
        return False

def run_downloader(periods=None):
    if periods is None:
        periods = DEFAULT_PERIODS
        
    print(f"Iniciando descarga de {len(periods)} periodos históricos...")
    t0 = time.time()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        success_count = 0
        for p_code in periods:
            ok = download_period(page, p_code)
            if ok:
                success_count += 1
            time.sleep(1.0) # Respeto a los servidores de SPensiones
            
        browser.close()
        
    print(f"\nDescarga finalizada: {success_count}/{len(periods)} periodos listos en {time.time()-t0:.1f} s")

if __name__ == "__main__":
    run_downloader()

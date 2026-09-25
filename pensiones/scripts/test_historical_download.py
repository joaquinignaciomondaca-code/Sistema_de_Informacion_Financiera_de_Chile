import os
import zipfile
from playwright.sync_api import sync_playwright

output_dir = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw"
os.makedirs(output_dir, exist_ok=True)

test_periods = ["202512", "202506"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    
    for periodo in test_periods:
        url = f"https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo={periodo}&ext=.php"
        print(f"\n--- Periodo {periodo}: Abriendo {url} ---")
        page.goto(url, wait_until='networkidle')
        
        zip_link = page.locator("a:has-text('Obtener Aquí')").first
        if zip_link.count() > 0:
            with page.expect_download() as download_info:
                zip_link.click()
            download = download_info.value
            fname = download.suggested_filename
            dest = os.path.join(output_dir, fname)
            download.save_as(dest)
            print(f"Descargado: {fname} ({os.path.getsize(dest):,} bytes)")
            
            with zipfile.ZipFile(dest, 'r') as z:
                print(f"Contenido: {z.namelist()}")
        else:
            print(f"No se encontró enlace 'Obtener Aquí' para {periodo}")
            
    browser.close()

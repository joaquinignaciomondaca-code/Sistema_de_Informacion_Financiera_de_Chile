from playwright.sync_api import sync_playwright
import os, zipfile

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo=200506&ext=.php', wait_until='networkidle')
    link = page.locator('a[href$=".zip"]').first
    print("Enlace encontrado:", link.inner_text(), link.get_attribute("href"))
    with page.expect_download(timeout=15000) as download_info:
        link.click()
    download = download_info.value
    dest = r'C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\test_legacy.zip'
    download.save_as(dest)
    print('Descargado legacy zip:', os.path.getsize(dest), 'bytes')
    with zipfile.ZipFile(dest, 'r') as z:
        print('Archivos dentro de legacy zip:', z.namelist()[:10])
    os.remove(dest)
    print('Eliminado zip de prueba.')
    browser.close()

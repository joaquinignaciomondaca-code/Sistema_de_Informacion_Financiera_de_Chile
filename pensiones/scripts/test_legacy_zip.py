from playwright.sync_api import sync_playwright
import os, zipfile
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo=200506&ext=.php', wait_until='networkidle')
    link = page.locator('a[href$=".zip"]').first
    print("Enlace encontrado:", link.inner_text(), link.get_attribute("href"))
    with page.expect_download(timeout=15000) as download_info:
        link.click()
    download = download_info.value
    dest = str(_ROOT.joinpath('pensiones', 'raw', 'test_legacy.zip'))
    download.save_as(dest)
    print('Descargado legacy zip:', os.path.getsize(dest), 'bytes')
    with zipfile.ZipFile(dest, 'r') as z:
        print('Archivos dentro de legacy zip:', z.namelist()[:10])
    os.remove(dest)
    print('Eliminado zip de prueba.')
    browser.close()

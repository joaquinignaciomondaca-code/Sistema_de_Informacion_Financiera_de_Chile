from playwright.sync_api import sync_playwright
import os
import zipfile
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

test_periods = ['202006', '201506', '201006', '200506', '200210']
raw_dir = str(_ROOT.joinpath('pensiones', 'raw', 'test'))
os.makedirs(raw_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    
    for periodo in test_periods:
        url = f"https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo={periodo}&ext=.php"
        print(f"\n--- Probando periodo {periodo} ---")
        page.goto(url, wait_until='networkidle')
        
        # Buscar enlace de descarga general
        zip_link = page.locator("a:has-text('Obtener Aquí')").first
        if zip_link.count() > 0:
            with page.expect_download(timeout=15000) as download_info:
                zip_link.click()
            download = download_info.value
            fname = download.suggested_filename
            dest = os.path.join(raw_dir, fname)
            download.save_as(dest)
            print(f"Descargado: {fname} ({os.path.getsize(dest):,} bytes)")
            if zipfile.is_zipfile(dest):
                with zipfile.ZipFile(dest, 'r') as z:
                    print(f"Contenido ZIP: {z.namelist()[:5]}")
            # Eliminar inmediatamente como pidió el usuario
            os.remove(dest)
            print("Archivo ZIP eliminado tras prueba.")
        else:
            print("No se encontró 'Obtener Aquí'. Inspeccionando enlaces disponibles:")
            links = page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a')).map(a => ({
                    text: a.innerText.trim(),
                    href: a.href
                })).filter(a => a.href && (a.href.includes('.zip') || a.href.includes('GetFile') || a.href.includes('genera')));
            }''')
            for l in links[:5]:
                print(f"  {l['text']} -> {l['href']}")
                
    browser.close()

import os
import zipfile
from playwright.sync_api import sync_playwright
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

output_dir = str(_ROOT.joinpath('pensiones', 'raw'))
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # Enable downloads
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    
    url = "https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo=202603&ext=.php"
    print(f"Abriendo {url}...")
    page.goto(url, wait_until='networkidle')
    
    # Encontrar el enlace del zip
    zip_link_handle = page.locator("a:has-text('Obtener Aquí')").first
    print("Enlace encontrado. Iniciando descarga...")
    
    with page.expect_download() as download_info:
        zip_link_handle.click()
    
    download = download_info.value
    suggested_filename = download.suggested_filename
    print(f"Descarga iniciada: {suggested_filename}")
    
    dest_path = os.path.join(output_dir, suggested_filename)
    download.save_as(dest_path)
    print(f"Guardado exitosamente en: {dest_path}, tamano: {os.path.getsize(dest_path)} bytes")
    
    if zipfile.is_zipfile(dest_path):
        with zipfile.ZipFile(dest_path, 'r') as z:
            namelist = z.namelist()
            print(f"Archivos dentro del ZIP ({len(namelist)}):")
            for name in namelist[:20]:
                print(f"  - {name}")
    else:
        print("El archivo descargado no es un zip estándar. Inspeccionando primeros 200 bytes:")
        with open(dest_path, 'rb') as f:
            print(f.read(200))
            
    browser.close()

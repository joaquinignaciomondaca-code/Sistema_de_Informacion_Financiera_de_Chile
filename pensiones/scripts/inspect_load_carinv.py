"""
Inspección de /apps/loadCarteras/loadCarInv.php
"""

from playwright.sync_api import sync_playwright

def inspect_load_carinv():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Probar en la página interactiva seleccionando un periodo
        url = "https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=estfinfp&menuN2=NOID"
        print(f"Cargando {url}...")
        page.goto(url, timeout=30000, wait_until='networkidle')
        
        # Inspeccionar el script de cambio de select
        scripts = page.evaluate('''() => {
            const select = document.querySelector('select[name="aaaamm0"]');
            return {
                onchange: select ? select.getAttribute('onchange') : null,
                id: select ? select.id : null,
                formAction: select && select.form ? select.form.action : null
            };
        }''')
        print("Select aaaamm0 atributos:", scripts)
        
        # Probar cambiar el select a 202603 y ver qué peticiones de red o elementos se cargan
        requests = []
        page.on("request", lambda req: requests.append((req.method, req.url, req.post_data)))
        
        print("\nSeleccionando 202603 en aaaamm0...")
        page.select_option('select[name="aaaamm0"]', '202603#/apps/loadCarteras/loadCarInv.php')
        page.wait_for_timeout(4000)
        
        print(f"Peticiones de red capturadas ({len(requests)}):")
        for r in requests[-10:]:
            print(f"  {r[0]} {r[1]} | post={r[2]}")
            
        print("\nNuevos elementos en la página:")
        links = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            })).filter(a => a.href && (a.href.endsWith('.zip') || a.href.endsWith('.xml') || a.href.endsWith('.xls') || a.href.endsWith('.csv') || a.href.includes('descarga')));
        }''')
        for l in links:
            print(f"  [DESCARGA] {l['text']} -> {l['href']}")
            
        browser.close()

if __name__ == "__main__":
    inspect_load_carinv()

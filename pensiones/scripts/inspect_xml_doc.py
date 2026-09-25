from playwright.sync_api import sync_playwright
import sys
sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    url = 'https://www.spensiones.cl/xml/doc/apps/finmes/ultima_version_cartera_desagregada/'
    print(f"Cargando {url}...")
    page.goto(url, wait_until='networkidle')
    
    body_text = page.inner_text('body')
    print("DOCUMENTACION XML CONTENIDO:")
    print(body_text[:2000])
    
    links = page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a')).map(a => ({
            text: a.innerText.trim(),
            href: a.href
        }));
    }''')
    print("\nEnlaces en doc:")
    for l in links:
        print(f"  {l['text']} -> {l['href']}")
        
    browser.close()

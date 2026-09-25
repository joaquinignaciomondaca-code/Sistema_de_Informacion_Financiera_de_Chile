"""
Inspección de .sc.php?_cid=41 (Series Estadísticas del Sistema de Pensiones)
"""

from playwright.sync_api import sync_playwright

def inspect_cid_41():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://www.spensiones.cl/safpstats/stats/.sc.php?_cid=41"
        print(f"=== NAVEGANDO A: {url} ===")
        page.goto(url, timeout=30000, wait_until='networkidle')
        
        print(f"Final URL: {page.url}")
        print(f"Title: {page.title()}")
        
        links = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            })).filter(a => a.href && a.text.length > 2);
        }''')
        
        print(f"\nEnlaces en _cid=41: {len(links)}")
        for l in links:
            if not any(x in l['href'] for x in ['channel', 'propertyname-5', 'propertyname-6']):
                print(f"  - {l['text']} -> {l['href']}")
                
        browser.close()

if __name__ == "__main__":
    inspect_cid_41()

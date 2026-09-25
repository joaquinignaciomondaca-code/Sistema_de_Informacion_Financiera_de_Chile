"""
Buscador interno en spensiones.cl mediante Playwright
"""

from playwright.sync_api import sync_playwright

def search_internal():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Búsqueda en el buscador institucional de spensiones
        query = "cartera de inversiones desagregada"
        search_url = f"https://www.spensiones.cl/portal/institucional/594/w3-search.html?q={query.replace(' ', '+')}"
        print(f"Buscando en: {search_url}")
        
        page.goto(search_url, timeout=20000)
        
        results = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            })).filter(a => a.href && a.text.length > 5 && a.href.includes('w3-article'));
        }''')
        
        print(f"Resultados encontrados: {len(results)}")
        for r in results[:15]:
            print(f"  - {r['text']} -> {r['href']}")
            
        browser.close()

if __name__ == "__main__":
    search_internal()

"""
Inspección de Estadísticas Financieras de Fondos de Pensiones
"""

from playwright.sync_api import sync_playwright

def inspect_financial_stats():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        targets = [
            ("Estadísticas Financieras Fondos", "https://www.spensiones.cl/portal/institucional/594/w3-propertyvalue-9876.html"),
            ("Series Estadísticas Sistema", "https://www.spensiones.cl/portal/institucional/594/w3-propertyvalue-9605.html"),
            ("Estadísticas Financieras AFP", "https://www.spensiones.cl/portal/institucional/594/w3-propertyvalue-9875.html")
        ]
        
        for label, u in targets:
            print(f"\n=== {label}: {u} ===")
            page.goto(u, timeout=20000)
            print(f"Title: {page.title()}")
            
            links = page.evaluate('''() => {
                return Array.from(document.querySelectorAll('#content a, main a, article a, .texto a, a')).map(a => ({
                    text: a.innerText.trim(),
                    href: a.href
                })).filter(a => a.href && a.text.length > 2 && !a.href.includes('w3-channel') && !a.href.includes('miportal'));
            }''')
            
            print(f"Enlaces encontrados: {len(links)}")
            for l in links[:20]:
                print(f"  - {l['text']} -> {l['href']}")
                
        browser.close()

if __name__ == "__main__":
    inspect_financial_stats()

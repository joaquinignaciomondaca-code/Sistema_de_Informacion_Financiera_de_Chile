"""
Inspección del Centro de Estadísticas de la SPensiones (paginaCuadrosCCEE.php)
"""

from playwright.sync_api import sync_playwright

def inspect_ccee():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=estfinfp&menuN2=NOID"
        print(f"=== NAVEGANDO A: {url} ===")
        page.goto(url, timeout=30000, wait_until='networkidle')
        
        print(f"Final URL: {page.url}")
        print(f"Title: {page.title()}")
        
        items = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a, button, select, table')).map(el => {
                if (el.tagName === 'A') {
                    return { tag: 'A', text: el.innerText.trim(), href: el.href };
                } else if (el.tagName === 'SELECT') {
                    return { tag: 'SELECT', name: el.name, options: Array.from(el.options).map(o => o.text.trim()) };
                }
                return null;
            }).filter(x => x !== null);
        }''')
        
        print(f"Total elementos interactivos detectados: {len(items)}")
        for it in items[:30]:
            if it['tag'] == 'A' and it['text']:
                print(f"  [LINK] {it['text']} -> {it['href']}")
            elif it['tag'] == 'SELECT':
                print(f"  [SELECT] {it['name']}: {it['options'][:5]}...")
                
        browser.close()

if __name__ == "__main__":
    inspect_ccee()

"""
Inspección detallada de cuadros estadísticos financieros de Fondos de Pensiones
"""

from playwright.sync_api import sync_playwright

def inspect_cuadros():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=estfinfp&menuN2=NOID"
        print(f"Navegando a: {url}")
        page.goto(url, timeout=30000, wait_until='networkidle')
        
        data = page.evaluate('''() => {
            const menuN2Links = Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            })).filter(a => a.href && a.href.includes('estfinfp'));
            
            const selects = Array.from(document.querySelectorAll('select')).map(s => ({
                name: s.name,
                id: s.id,
                options: Array.from(s.options).map(o => ({ value: o.value, text: o.text.trim() }))
            }));
            
            const tables = Array.from(document.querySelectorAll('table')).map(t => ({
                id: t.id,
                className: t.className,
                rows: t.rows.length
            }));

            return { menuN2Links, selects, tables };
        }''')
        
        print(f"\nEnlaces de submódulos financieros de Fondos: {len(data['menuN2Links'])}")
        for l in data['menuN2Links']:
            print(f"  - {l['text']} -> {l['href']}")
            
        print(f"\nSelects encontrados: {len(data['selects'])}")
        for s in data['selects']:
            print(f"  - {s.get('name') or s.get('id')}: {s['options'][:5]}")
            
        print(f"\nTablas encontradas: {len(data['tables'])}")
        for t in data['tables']:
            print(f"  - Table id={t['id']} class={t['className']} rows={t['rows']}")

        browser.close()

if __name__ == "__main__":
    inspect_cuadros()

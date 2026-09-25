from playwright.sync_api import sync_playwright
import sys
sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo=202603&ext=.php', wait_until='networkidle')
    
    sections = page.evaluate('''() => {
        let results = [];
        // Buscar encabezados o tablas que listan los nombres de los cuadros
        let tables = document.querySelectorAll('table');
        tables.forEach((t, i) => {
            let text = t.innerText.replace(/\\s+/g, ' ').trim();
            if (text.includes('Listado') || text.includes('Cuadro') || text.includes('CARTERA')) {
                results.push({tableIdx: i, text: text.substring(0, 500)});
            }
        });
        
        // También buscar todos los elementos tr que contengan enlaces a genera_desagregada
        let rows = [];
        document.querySelectorAll('tr').forEach(tr => {
            let links = tr.querySelectorAll('a');
            if (links.length > 0) {
                let txt = tr.innerText.replace(/\\s+/g, ' ').trim();
                let hrefs = Array.from(links).map(a => a.href);
                rows.push({text: txt, hrefs: hrefs});
            }
        });
        return {sections: results, rows: rows.slice(0, 40)};
    }''')
    
    print(f"Tablas encontradas: {len(sections['sections'])}")
    for s in sections['sections'][:5]:
        print("TABLE:", s)
        
    print("\nFilas con enlaces (primeras 30):")
    for r in sections['rows'][:30]:
        print("ROW:", r['text'])
        
    browser.close()

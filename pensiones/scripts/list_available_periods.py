from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=estfinfp&menuN2=NOID', wait_until='networkidle')
    
    options = page.evaluate('''() => {
        let sel = document.querySelector('select[name="aaaamm0"]');
        if (!sel) return [];
        return Array.from(sel.options).map(opt => ({
            value: opt.value,
            text: opt.innerText.trim()
        }));
    }''')
    
    print(f"Total periodos disponibles: {len(options)}")
    print("Primeros 15 (mas recientes):")
    for o in options[:15]:
        print(f"  {o['text']} -> {o['value']}")
    print("Ultimos 10 (mas antiguos):")
    for o in options[-10:]:
        print(f"  {o['text']} -> {o['value']}")
    browser.close()

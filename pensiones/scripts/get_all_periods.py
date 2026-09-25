from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=estfinfp&menuN2=NOID', wait_until='networkidle')
    
    periods = page.evaluate("""() => {
        const sel = document.querySelector('select[name="aaaamm0"]');
        if (!sel) return [];
        return Array.from(sel.options).map(opt => {
            return opt.value.split('#')[0].trim();
        }).filter(v => v.length === 6);
    }""")
    
    print(f"Total period codes: {len(periods)}")
    print(f"Sample: {periods[:10]} ... {periods[-5:]}")
    
    with open('pensiones/scripts/all_periods.json', 'w') as f:
        json.dump(periods, f, indent=2)
        
    browser.close()

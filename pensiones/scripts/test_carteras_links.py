from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.spensiones.cl/apps/loadCarteras/loadCarInv.php?menu=sci&menuN1=estfinfp&menuN2=NOID&orden=10&periodo=202603&ext=.php', wait_until='networkidle')
    
    links = page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a')).map(a => {
            let row = a.closest('tr');
            return {
                text: a.innerText.trim(),
                href: a.href,
                title: a.getAttribute('title') || '',
                rowText: row ? row.innerText.replace(/\\s+/g, ' ').trim() : ''
            };
        }).filter(x => x.href && (x.href.includes('genera_desagregada') || x.href.includes('GetFile') || x.href.includes('.zip') || x.href.includes('.xls')));
    }''')
    print(f'Cartera links found: {len(links)}')
    for idx, l in enumerate(links[:35]):
        print(f"[{idx}] {l['rowText']} ---> {l['href']}")
    browser.close()

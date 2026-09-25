from playwright.sync_api import sync_playwright

def get_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.spensiones.cl/apps/centroEstadisticas/paginaCuadrosCCEE.php?menu=sci&menuN1=estfinfp&menuN2=NOID', wait_until='networkidle')
        
        table_html = page.evaluate("""() => {
            const table = document.querySelector('table');
            return table ? table.outerHTML : 'No table';
        }""")
        print("TABLE HTML:")
        print(table_html)
        browser.close()

if __name__ == '__main__':
    get_html()

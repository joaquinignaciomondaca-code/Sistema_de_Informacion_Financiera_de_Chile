"""
Buscar iframes, scripts y enlaces de descarga en el HTML del artículo
"""

import re
from playwright.sync_api import sync_playwright

def inspect_article_files():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for art_id in ['17132', '17058', '16957']:
            url = f"https://www.spensiones.cl/portal/institucional/594/w3-article-{art_id}.html"
            print(f"\n=== INSPECCIONANDO: {url} ===")
            page.goto(url, timeout=20000)
            html = page.content()
            
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html)
            files = [l for l in links if any(ext in l.lower() for ext in ['.pdf', '.xls', '.xlsx', '.zip', '.csv', '.xml', 'download', 'archivo', 'getfile'])]
            print(f"Archivos encontrados ({len(files)}):")
            for f in set(files):
                print(f"  - {f}")
                
            iframes = re.findall(r'<iframe[^>]+src=[\'"]([^\'"]+)[\'"]', html)
            if iframes:
                print(f"Iframes: {iframes}")
                
        browser.close()

if __name__ == "__main__":
    inspect_article_files()

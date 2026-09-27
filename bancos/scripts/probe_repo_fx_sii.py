"""Inspecciona HTML público del SII para validar una auditoría independiente de FX.

No extrae ni publica una serie; imprime solamente un extracto estructural de
filas de tabla de 2008 y 2013 en una anotación Actions (no requiere credenciales).
"""
from __future__ import annotations
import json
import re
import urllib.request
from html.parser import HTMLParser

URL = 'https://www.sii.cl/pagina/valores/dolar/dolar{}.htm'


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def main():
    for year in (2022, 2025, 2026):
        with urllib.request.urlopen(urllib.request.Request(f'https://www.sii.cl/valores_y_fechas/dolar/dolar{year}.htm', headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response:
            url = response.url
            data = response.read(1_000_000).decode('utf-8', errors='replace')
        if year == 2013 and re.search(r'window.location.replace\(', data):
            redirect = 'https://www.sii.cl/valores_y_fechas/dolar/dolar2013.htm'
            with urllib.request.urlopen(redirect, timeout=25) as response:
                data = response.read(1_000_000).decode('utf-8', errors='replace')
                url = response.url
        parser = Tables()
        parser.feed(data)
        tables = sorted(parser.tables, key=len, reverse=True)
        print('::notice title=SII-FX-HTML::' + json.dumps({
            'year': year, 'url': url, 'tables': len(tables),
            'samples': [{'rows': len(t), 'first': t[:2], 'last': t[-3:]}
                        for t in tables[:2]],
            'sections': [re.sub(r'<[^>]+>', ' ', x)[:120] for x in re.findall(r'(?is)<h[1-5][^>]*>.*?(?:Diciembre|Noviembre|Enero).*?</h[1-5]>', data)[:3]],
            'html_start': re.sub(r'\s+', ' ', data[:700])[:400],
            'table_2013': [{'rows': len(t), 'first': t[:3], 'last': t[-4:],
                            'suspect_cells': {str(m): [t[d][m] for d in (27, 28, 29, 30, 31)]
                                              for m in ([1, 7, 10] if year != 2022 else [1, 7, 8])}}
                           for t in tables if len(t) >= 33 and len(t[0]) == 13][:1],
            'section_ids': re.findall(r"id=['\"](mes_[a-z]+)['\"]", data)[:14],
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()

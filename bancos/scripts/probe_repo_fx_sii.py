"""Inspecciona HTML público del SII para validar una auditoría independiente de FX.

No extrae ni publica una serie; imprime solamente un extracto estructural de
filas de tabla de 2008 y 2013 en una anotación Actions (no requiere credenciales).
"""
from __future__ import annotations
import json
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
    for year in (2008, 2013):
        with urllib.request.urlopen(urllib.request.Request(URL.format(year), headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response:
            url = response.url
            data = response.read(1_000_000).decode('utf-8', errors='replace')
        parser = Tables()
        parser.feed(data)
        tables = sorted(parser.tables, key=len, reverse=True)
        print('::notice title=SII-FX-HTML::' + json.dumps({
            'year': year, 'url': url, 'tables': len(tables),
            'samples': [{'rows': len(t), 'first': t[:2], 'last': t[-3:]}
                        for t in tables[:2]],
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()

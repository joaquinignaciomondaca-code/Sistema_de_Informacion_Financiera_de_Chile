import xml.etree.ElementTree as ET
import sys
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))
sys.stdout.reconfigure(encoding='utf-8')

xml_file = str(_ROOT.joinpath('pensiones', 'raw', 'extracted', 'cartera_desagregada202603.xml'))

# Muestreo por listado para ver qué columnas contiene cada uno
context = ET.iterparse(xml_file, events=('start', 'end'))
_, root = next(context)

listado_columns = {}
current_listado = None

for event, elem in context:
    tag = elem.tag.split('}')[-1]
    if event == 'start' and tag == 'listado':
        current_listado = elem.attrib.get('numero')
    elif event == 'end' and tag == 'fila' and current_listado and current_listado not in listado_columns:
        # Encontrar todas las etiquetas hijas dentro de columnas
        cols = elem.find('{http://www.spensiones.cl/xml}columnas')
        if cols is not None:
            child_tags = set()
            for child in cols:
                ctag = child.tag.split('}')[-1]
                sub_tags = [sc.tag.split('}')[-1] for sc in child]
                child_tags.add(f"{ctag}[{','.join(sub_tags)}]")
            glosa = elem.find('{http://www.spensiones.cl/xml}glosa')
            listado_columns[current_listado] = {
                'glosa_ejemplo': glosa.text if glosa is not None else '',
                'child_tags': list(child_tags)
            }
    elif event == 'end' and tag == 'listado':
        elem.clear()
        root.clear()

print("ESTRUCTURA DE COLUMNAS POR LISTADO:")
for k in sorted(listado_columns.keys(), key=lambda x: int(x)):
    info = listado_columns[k]
    print(f"\n--- Listado {k} (ejemplo: {info['glosa_ejemplo']}) ---")
    for ct in info['child_tags']:
        print(f"    {ct}")


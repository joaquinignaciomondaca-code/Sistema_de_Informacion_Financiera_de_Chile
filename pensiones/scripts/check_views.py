import xml.etree.ElementTree as ET
import sys
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))
sys.stdout.reconfigure(encoding='utf-8')

xml_file = str(_ROOT.joinpath('pensiones', 'raw', 'extracted', 'cartera_desagregada202603.xml'))

context = ET.iterparse(xml_file, events=('start', 'end'))
path_stack = []

found = {}
for event, elem in context:
    tag = elem.tag.split('}')[-1]
    if event == 'start':
        path_stack.append(tag)
    elif event == 'end':
        if tag == 'fila':
            # Ver qué tipo de listado_por_* es
            parent_view = None
            for p in path_stack:
                if p.startswith('listado_por_'):
                    parent_view = p
            if parent_view and parent_view not in found:
                xml_str = ET.tostring(elem, encoding='utf-8').decode('utf-8')
                found[parent_view] = xml_str
                print(f"\n================ VIEW: {parent_view} ================")
                print(xml_str[:1200])
        path_stack.pop()
        if len(found) >= 3:
            break

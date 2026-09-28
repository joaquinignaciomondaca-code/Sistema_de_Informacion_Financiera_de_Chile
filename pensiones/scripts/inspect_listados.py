import xml.etree.ElementTree as ET
import sys
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

sys.stdout.reconfigure(encoding='utf-8')
xml_file = str(_ROOT.joinpath('pensiones', 'raw', 'extracted', 'cartera_desagregada202603.xml'))

context = ET.iterparse(xml_file, events=('start',))
listados_info = {}

for event, elem in context:
    tag = elem.tag.split('}')[-1]
    if tag == 'listado':
        num = elem.attrib.get('numero')
        nombre = elem.attrib.get('nombre') or elem.attrib.get('titulo') or elem.attrib.get('glosa')
        listados_info[num] = nombre
    # también ver si hay un elemento titulo o nombre hijo inmediato de listado
    elif tag in ('titulo', 'nombre_listado', 'glosa_listado'):
        # ver último listado
        pass

print("Listados y sus atributos:")
for k, v in sorted(listados_info.items(), key=lambda x: int(x[0])):
    print(f"Listado {k}: {v}")

# También ver cómo se titulan en la web o en las primeras etiquetas de listado
context2 = ET.iterparse(xml_file, events=('start', 'end'))
current_num = None
first_glosas = {}
for event, elem in context2:
    tag = elem.tag.split('}')[-1]
    if event == 'start' and tag == 'listado':
        current_num = elem.attrib.get('numero')
    elif event == 'start' and tag == 'fila' and current_num and current_num not in first_glosas:
        pass
    elif event == 'end' and tag == 'glosa' and current_num and current_num not in first_glosas:
        first_glosas[current_num] = elem.text
        if len(first_glosas) >= 29:
            break
    if event == 'end' and tag == 'listado':
        elem.clear()

print("\nPrimeras glosas por listado:")
for k, v in sorted(first_glosas.items(), key=lambda x: int(x[0])):
    print(f"Listado {k} -> Primer activo/glosa: {v}")

import xml.etree.ElementTree as ET
import sys
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))
sys.stdout.reconfigure(encoding='utf-8')

xml_file = str(_ROOT.joinpath('pensiones', 'raw', 'extracted', 'cartera_desagregada202603.xml'))

# Tomar el primer listado_por_afp completo del listado 1
context = ET.iterparse(xml_file, events=('start', 'end'))
_, root = next(context)

found = False
for event, elem in context:
    tag = elem.tag.split('}')[-1]
    if event == 'end' and tag == 'fila':
        xml_str = ET.tostring(elem, encoding='utf-8').decode('utf-8')
        print("SAMPLE FILA COMPLETA:")
        print(xml_str)
        break


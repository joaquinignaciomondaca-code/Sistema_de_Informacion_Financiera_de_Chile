import xml.etree.ElementTree as ET
import sys
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parents[2]  # raíz del repo
_RESPALDO = _Path(_os.environ.get('MFC_RESPALDO_DIR', _Path.home().joinpath('Desktop', 'Respaldo_BCCH')))

sys.stdout.reconfigure(encoding='utf-8')

xml_file = str(_ROOT.joinpath('pensiones', 'raw', 'extracted', 'cartera_desagregada202603.xml'))

print("Inspeccionando agrupaciones y listados...")

listados = set()
agrupaciones = set()
instrumentos = set()
afps = set()
tipofondos = set()

context = ET.iterparse(xml_file, events=('start',))

for event, elem in context:
    tag = elem.tag.split('}')[-1]
    if tag == 'listado':
        listados.add(elem.attrib.get('numero'))
    elif tag == 'agrupacion':
        nombre = elem.attrib.get('nombre') or elem.attrib.get('codigo') or elem.text
        if nombre:
            agrupaciones.add(str(nombre))
        if elem.attrib:
            agrupaciones.add(str(elem.attrib))
    elif tag == 'afp':
        cod = elem.attrib.get('codigo') or elem.attrib.get('nombre')
        if cod:
            afps.add(str(elem.attrib))
    elif tag == 'tipofondo':
        cod = elem.attrib.get('codigo')
        if cod:
            tipofondos.add(cod)

print("Listados encontrados:", listados)
print("Tipofondos encontrados:", sorted(list(tipofondos)))
print("Agrupaciones encontradas (primeras 30):", list(agrupaciones)[:30])

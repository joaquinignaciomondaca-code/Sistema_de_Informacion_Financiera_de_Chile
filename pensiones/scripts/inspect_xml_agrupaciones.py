import xml.etree.ElementTree as ET
import sys

sys.stdout.reconfigure(encoding='utf-8')

xml_file = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\extracted\cartera_desagregada202603.xml"

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

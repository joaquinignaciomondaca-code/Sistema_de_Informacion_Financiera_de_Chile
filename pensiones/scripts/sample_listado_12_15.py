import xml.etree.ElementTree as ET
import sys
sys.stdout.reconfigure(encoding='utf-8')

xml_file = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\extracted\cartera_desagregada202603.xml"

context = ET.iterparse(xml_file, events=('start', 'end'))
_, root = next(context)

current_listado = None
l12_samples = []
l15_samples = []

for event, elem in context:
    tag = elem.tag.split('}')[-1]
    if event == 'start' and tag == 'listado':
        current_listado = elem.attrib.get('numero')
    elif event == 'end':
        if tag == 'fila' and current_listado == '12' and len(l12_samples) < 2:
            l12_samples.append(ET.tostring(elem, encoding='utf-8').decode('utf-8'))
        elif tag == 'fila' and current_listado == '15' and len(l15_samples) < 2:
            l15_samples.append(ET.tostring(elem, encoding='utf-8').decode('utf-8'))
        elif tag == 'listado':
            elem.clear()
            root.clear()
            if len(l12_samples) >= 2 and len(l15_samples) >= 2:
                break

print("=== LISTADO 12 (ACCIONES) ===")
for s in l12_samples:
    print(s)
    print("---------------------------------")

print("=== LISTADO 15 (BONOS CORPORATIVOS) ===")
for s in l15_samples:
    print(s)
    print("---------------------------------")

import xml.etree.ElementTree as ET
import sys
sys.stdout.reconfigure(encoding='utf-8')

xml_file = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\extracted\cartera_desagregada202603.xml"

target_listados = {'1', '11', '26'}
samples = {k: [] for k in target_listados}

context = ET.iterparse(xml_file, events=('start', 'end'))
_, root = next(context)

current_listado = None
recording = False

for event, elem in context:
    tag = elem.tag.split('}')[-1]
    
    if event == 'start':
        if tag == 'listado':
            current_listado = elem.attrib.get('numero')
    elif event == 'end':
        if tag == 'fila' and current_listado in target_listados:
            if len(samples[current_listado]) < 2:
                # Serializar este elemento fila a string
                xml_str = ET.tostring(elem, encoding='utf-8').decode('utf-8')
                samples[current_listado].append(xml_str)
        elif tag == 'listado':
            elem.clear()
            root.clear()
            current_listado = None
            if all(len(v) >= 2 for v in samples.values()):
                break

for list_num, rows in samples.items():
    print(f"\n==================== MUESTRA LISTADO {list_num} ====================")
    for r in rows:
        print(r[:1000]) # primeros 1000 caracteres
        print("--------------------------------------------------")

import xml.etree.ElementTree as ET
import sys
sys.stdout.reconfigure(encoding='utf-8')

xml_file = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\extracted\cartera_desagregada202603.xml"

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


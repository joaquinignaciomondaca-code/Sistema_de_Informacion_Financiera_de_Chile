import xml.etree.ElementTree as ET
import sys
sys.stdout.reconfigure(encoding='utf-8')

xml_file = r"C:\Users\joaqu\.gemini\antigravity\scratch\bcch_market_monitor\pensiones\raw\extracted\cartera_desagregada202603.xml"

context = ET.iterparse(xml_file, events=('start', 'end'))
path_stack = []

count = 0
for event, elem in context:
    tag = elem.tag.split('}')[-1]
    if event == 'start':
        path_stack.append((tag, elem.attrib))
    elif event == 'end':
        if tag == 'fila':
            count += 1
            if count <= 5:
                glosa = elem.find('{http://www.spensiones.cl/xml}glosa')
                glosa_text = glosa.text if glosa is not None else ''
                print("--- FILA ---")
                print("Ancestros:", [(p[0], p[1]) for p in path_stack[:-1]])
                print("Glosa:", glosa_text)
                total = elem.find('.//{http://www.spensiones.cl/xml}total')
                if total is not None:
                    mp = total.find('{http://www.spensiones.cl/xml}monto_pesos')
                    md = total.find('{http://www.spensiones.cl/xml}monto_dolares')
                    print(f"Total: monto_pesos={mp.text if mp is not None else None}, monto_dolares={md.text if md is not None else None}")
            else:
                break
        path_stack.pop()

